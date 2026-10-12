from datetime import datetime

from flask import (
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from extensions import db
from models import LifecycleRecord
from services.lifecycle_persistence import (
    sync_lifecycle_records
)


def parse_form_date(value):
    """
    Convert a YYYY-MM-DD form value into a Python date.

    Returns:
        (date_value, error_message)
    """

    if not value:
        return None, None

    try:
        parsed_date = datetime.strptime(
            value,
            "%Y-%m-%d"
        ).date()

        return parsed_date, None

    except ValueError:
        return (
            None,
            f"Invalid date: {value}"
        )


def register_lifecycle_routes(app):

    @app.route("/stored-releases")
    def stored_releases():

        search = request.args.get(
            "search",
            ""
        ).strip()

        product_filter = request.args.get(
            "product",
            ""
        ).strip()

        status_filter = request.args.get(
            "status",
            ""
        ).strip()

        query = LifecycleRecord.query

        if search:

            search_term = f"%{search}%"

            query = query.filter(
                or_(
                    LifecycleRecord.title.ilike(
                        search_term
                    ),
                    LifecycleRecord.product.ilike(
                        search_term
                    ),
                    LifecycleRecord.version.ilike(
                        search_term
                    ),
                    LifecycleRecord.codename.ilike(
                        search_term
                    ),
                    LifecycleRecord.source.ilike(
                        search_term
                    )
                )
            )

        if product_filter:

            query = query.filter(
                LifecycleRecord.product
                == product_filter
            )

        if status_filter == "active":

            query = query.filter(
                LifecycleRecord.is_maintained.is_(
                    True
                ),
                LifecycleRecord.is_eol.is_(
                    False
                )
            )

        elif status_filter == "ended":

            query = query.filter(
                LifecycleRecord.is_eol.is_(
                    True
                )
            )

        records = (
            query
            .order_by(
                LifecycleRecord.product,
                LifecycleRecord.id
            )
            .all()
        )

        products = [
            row[0]
            for row in (
                db.session.query(
                    LifecycleRecord.product
                )
                .distinct()
                .order_by(
                    LifecycleRecord.product
                )
                .all()
            )
        ]

        total_count = (
            LifecycleRecord.query.count()
        )

        return render_template(
            "stored_releases.html",
            records=records,
            products=products,
            total_count=total_count,
            search=search,
            product_filter=product_filter,
            status_filter=status_filter
        )


    @app.route(
        "/stored-releases/sync",
        methods=["POST"]
    )
    def sync_stored_releases():

        mac_result = (
            sync_lifecycle_records(
                "macOS"
            )
        )

        chrome_result = (
            sync_lifecycle_records(
                "Chrome"
            )
        )

        errors = []

        if not mac_result.get(
            "success"
        ):

            errors.append(
                "macOS: "
                + mac_result.get(
                    "error",
                    "Unknown error"
                )
            )

        if not chrome_result.get(
            "success"
        ):

            errors.append(
                "Chrome: "
                + chrome_result.get(
                    "error",
                    "Unknown error"
                )
            )

        if errors:

            flash(
                "Lifecycle sync completed "
                "with errors: "
                + " | ".join(errors),
                "error"
            )

        else:

            total_created = (
                mac_result.get(
                    "created",
                    0
                )
                + chrome_result.get(
                    "created",
                    0
                )
            )

            total_updated = (
                mac_result.get(
                    "updated",
                    0
                )
                + chrome_result.get(
                    "updated",
                    0
                )
            )

            flash(
                "Lifecycle data synchronized "
                "successfully. "
                f"Created {total_created} records "
                f"and updated {total_updated} records.",
                "success"
            )

        return redirect(
            url_for(
                "stored_releases"
            )
        )


    @app.route(
        "/stored-releases/create",
        methods=["GET", "POST"]
    )
    def create_stored_release():

        if request.method == "POST":

            title = request.form.get(
                "title",
                ""
            ).strip()

            description = request.form.get(
                "description",
                ""
            ).strip()

            source = request.form.get(
                "source",
                ""
            ).strip()

            source_url = request.form.get(
                "source_url",
                ""
            ).strip()

            product = request.form.get(
                "product",
                ""
            ).strip()

            version = request.form.get(
                "version",
                ""
            ).strip()

            external_id = request.form.get(
                "external_id",
                ""
            ).strip()

            required_fields = {
                "Title": title,
                "Description": description,
                "Source": source,
                "Source URL": source_url,
                "Product": product,
                "Version": version,
                "External ID": external_id
            }

            missing_fields = [
                field
                for field, value
                in required_fields.items()
                if not value
            ]

            if missing_fields:

                flash(
                    "Missing required fields: "
                    + ", ".join(
                        missing_fields
                    ),
                    "error"
                )

                return render_template(
                    "lifecycle_form.html",
                    record=None,
                    form_title=(
                        "Create Lifecycle Record"
                    )
                )

            if not (
                source_url.startswith(
                    "http://"
                )
                or source_url.startswith(
                    "https://"
                )
            ):

                flash(
                    "Source URL must begin with "
                    "http:// or https://.",
                    "error"
                )

                return render_template(
                    "lifecycle_form.html",
                    record=None,
                    form_title=(
                        "Create Lifecycle Record"
                    )
                )

            release_date, release_error = (
                parse_form_date(
                    request.form.get(
                        "release_date"
                    )
                )
            )

            eol_date, eol_error = (
                parse_form_date(
                    request.form.get(
                        "eol_date"
                    )
                )
            )

            (
                latest_release_date,
                latest_release_error
            ) = parse_form_date(
                request.form.get(
                    "latest_release_date"
                )
            )

            date_errors = [
                error
                for error in [
                    release_error,
                    eol_error,
                    latest_release_error
                ]
                if error
            ]

            if date_errors:

                flash(
                    " ".join(date_errors),
                    "error"
                )

                return render_template(
                    "lifecycle_form.html",
                    record=None,
                    form_title=(
                        "Create Lifecycle Record"
                    )
                )

            duplicate = (
                LifecycleRecord.query
                .filter_by(
                    source=source,
                    external_id=external_id
                )
                .first()
            )

            if duplicate:

                flash(
                    "A record with this source "
                    "and external ID already "
                    "exists.",
                    "error"
                )

                return render_template(
                    "lifecycle_form.html",
                    record=None,
                    form_title=(
                        "Create Lifecycle Record"
                    )
                )

            record = LifecycleRecord(
                title=title,
                description=description,
                source=source,
                source_url=source_url,
                retrieved_date=datetime.utcnow(),
                product=product,
                version=version,
                codename=(
                    request.form.get(
                        "codename",
                        ""
                    ).strip()
                    or None
                ),
                release_date=release_date,
                is_maintained=(
                    request.form.get(
                        "is_maintained"
                    )
                    == "on"
                ),
                is_eol=(
                    request.form.get(
                        "is_eol"
                    )
                    == "on"
                ),
                eol_date=eol_date,
                latest_version=(
                    request.form.get(
                        "latest_version",
                        ""
                    ).strip()
                    or None
                ),
                latest_release_date=(
                    latest_release_date
                ),
                external_id=external_id
            )

            try:

                db.session.add(record)
                db.session.commit()

                flash(
                    "Lifecycle record created "
                    "successfully.",
                    "success"
                )

                return redirect(
                    url_for(
                        "stored_releases"
                    )
                )

            except IntegrityError:

                db.session.rollback()

                flash(
                    "That record already exists.",
                    "error"
                )

            except Exception:

                db.session.rollback()

                flash(
                    "The record could not be "
                    "created.",
                    "error"
                )

        return render_template(
            "lifecycle_form.html",
            record=None,
            form_title=(
                "Create Lifecycle Record"
            )
        )


    @app.route(
        "/stored-releases/"
        "<int:record_id>/edit",
        methods=["GET", "POST"]
    )
    def edit_stored_release(
        record_id
    ):

        record = (
            LifecycleRecord.query
            .get_or_404(
                record_id
            )
        )

        if request.method == "POST":

            title = request.form.get(
                "title",
                ""
            ).strip()

            description = request.form.get(
                "description",
                ""
            ).strip()

            source = request.form.get(
                "source",
                ""
            ).strip()

            source_url = request.form.get(
                "source_url",
                ""
            ).strip()

            product = request.form.get(
                "product",
                ""
            ).strip()

            version = request.form.get(
                "version",
                ""
            ).strip()

            external_id = request.form.get(
                "external_id",
                ""
            ).strip()

            required_fields = {
                "Title": title,
                "Description": description,
                "Source": source,
                "Source URL": source_url,
                "Product": product,
                "Version": version,
                "External ID": external_id
            }

            missing_fields = [
                field
                for field, value
                in required_fields.items()
                if not value
            ]

            if missing_fields:

                flash(
                    "Missing required fields: "
                    + ", ".join(
                        missing_fields
                    ),
                    "error"
                )

                return render_template(
                    "lifecycle_form.html",
                    record=record,
                    form_title=(
                        "Edit Lifecycle Record"
                    )
                )

            if not (
                source_url.startswith(
                    "http://"
                )
                or source_url.startswith(
                    "https://"
                )
            ):

                flash(
                    "Source URL must begin with "
                    "http:// or https://.",
                    "error"
                )

                return render_template(
                    "lifecycle_form.html",
                    record=record,
                    form_title=(
                        "Edit Lifecycle Record"
                    )
                )

            release_date, release_error = (
                parse_form_date(
                    request.form.get(
                        "release_date"
                    )
                )
            )

            eol_date, eol_error = (
                parse_form_date(
                    request.form.get(
                        "eol_date"
                    )
                )
            )

            (
                latest_release_date,
                latest_release_error
            ) = parse_form_date(
                request.form.get(
                    "latest_release_date"
                )
            )

            date_errors = [
                error
                for error in [
                    release_error,
                    eol_error,
                    latest_release_error
                ]
                if error
            ]

            if date_errors:

                flash(
                    " ".join(date_errors),
                    "error"
                )

                return render_template(
                    "lifecycle_form.html",
                    record=record,
                    form_title=(
                        "Edit Lifecycle Record"
                    )
                )

            duplicate = (
                LifecycleRecord.query
                .filter(
                    LifecycleRecord.source
                    == source,
                    LifecycleRecord.external_id
                    == external_id,
                    LifecycleRecord.id
                    != record.id
                )
                .first()
            )

            if duplicate:

                flash(
                    "Another record already uses "
                    "this source and external ID.",
                    "error"
                )

                return render_template(
                    "lifecycle_form.html",
                    record=record,
                    form_title=(
                        "Edit Lifecycle Record"
                    )
                )

            record.title = title
            record.description = (
                description
            )
            record.source = source
            record.source_url = source_url
            record.product = product
            record.version = version

            record.codename = (
                request.form.get(
                    "codename",
                    ""
                ).strip()
                or None
            )

            record.release_date = (
                release_date
            )

            record.is_maintained = (
                request.form.get(
                    "is_maintained"
                )
                == "on"
            )

            record.is_eol = (
                request.form.get(
                    "is_eol"
                )
                == "on"
            )

            record.eol_date = (
                eol_date
            )

            record.latest_version = (
                request.form.get(
                    "latest_version",
                    ""
                ).strip()
                or None
            )

            record.latest_release_date = (
                latest_release_date
            )

            record.external_id = (
                external_id
            )

            try:

                db.session.commit()

                flash(
                    "Lifecycle record updated "
                    "successfully.",
                    "success"
                )

                return redirect(
                    url_for(
                        "stored_releases"
                    )
                )

            except IntegrityError:

                db.session.rollback()

                flash(
                    "That update would create "
                    "a duplicate record.",
                    "error"
                )

            except Exception:

                db.session.rollback()

                flash(
                    "The record could not be "
                    "updated.",
                    "error"
                )

        return render_template(
            "lifecycle_form.html",
            record=record,
            form_title=(
                "Edit Lifecycle Record"
            )
        )


    @app.route(
        "/stored-releases/"
        "<int:record_id>/delete",
        methods=["POST"]
    )
    def delete_stored_release(
        record_id
    ):

        record = (
            LifecycleRecord.query
            .get_or_404(
                record_id
            )
        )

        try:

            db.session.delete(record)
            db.session.commit()

            flash(
                "Lifecycle record deleted "
                "successfully.",
                "success"
            )

        except Exception:

            db.session.rollback()

            flash(
                "The record could not be "
                "deleted.",
                "error"
            )

        return redirect(
            url_for(
                "stored_releases"
            )
        )