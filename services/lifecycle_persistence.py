from datetime import datetime

from extensions import db
from models import LifecycleRecord
from services.lifecycle_api import (
    get_lifecycle_data,
    SUPPORTED_PRODUCTS
)


def parse_date(value):
    """
    Convert a YYYY-MM-DD string into a Python date.
    Returns None when the value is missing or invalid.
    """
    if not value:
        return None

    try:
        return datetime.strptime(
            value,
            "%Y-%m-%d"
        ).date()
    except (TypeError, ValueError):
        return None


def sync_lifecycle_records(product):
    """
    Retrieve lifecycle information from endoflife.date
    and persist it to MySQL.

    Existing records are updated instead of duplicated.
    """

    product_input = product.strip()
    product_key = product_input.lower()

    api_product = SUPPORTED_PRODUCTS.get(
        product_key
    )

    if not api_product:
        return {
            "success": False,
            "error": (
                "Unsupported product. "
                "Try macOS or Chrome."
            ),
            "created": 0,
            "updated": 0
        }

    lifecycle_data = get_lifecycle_data(
        product_input
    )

    if not lifecycle_data.get("success"):
        return {
            "success": False,
            "error": lifecycle_data.get(
                "error",
                "Lifecycle API request failed."
            ),
            "created": 0,
            "updated": 0
        }

    releases = lifecycle_data.get(
        "results",
        []
    )

    if not releases:
        return {
            "success": False,
            "error": (
                "No lifecycle releases "
                "were returned."
            ),
            "created": 0,
            "updated": 0
        }

    source = "endoflife.date"

    source_url = (
        "https://endoflife.date/"
        f"api/v1/products/{api_product}/"
    )

    product_name = lifecycle_data.get(
        "product",
        product_input
    )

    created_count = 0
    updated_count = 0

    try:
        for release in releases:

            version = str(
                release.get(
                    "version",
                    "Unknown"
                )
            )

            external_id = (
                f"{api_product}:{version}"
            )

            record = (
                LifecycleRecord.query
                .filter_by(
                    source=source,
                    external_id=external_id
                )
                .first()
            )

            title = (
                f"{product_name} {version}"
            )

            description = (
                f"Lifecycle information for "
                f"{product_name} {version} "
                f"retrieved from "
                f"endoflife.date."
            )

            if record is None:

                record = LifecycleRecord(
                    title=title,
                    description=description,
                    source=source,
                    source_url=source_url,
                    retrieved_date=datetime.utcnow(),
                    product=product_name,
                    version=version,
                    codename=release.get(
                        "codename"
                    ),
                    release_date=parse_date(
                        release.get(
                            "release_date"
                        )
                    ),
                    is_maintained=bool(
                        release.get(
                            "is_maintained"
                        )
                    ),
                    is_eol=bool(
                        release.get(
                            "is_eol"
                        )
                    ),
                    eol_date=parse_date(
                        release.get(
                            "eol_date"
                        )
                    ),
                    latest_version=release.get(
                        "latest_version"
                    ),
                    latest_release_date=parse_date(
                        release.get(
                            "latest_release_date"
                        )
                    ),
                    external_id=external_id
                )

                db.session.add(record)

                created_count += 1

            else:

                record.title = title
                record.description = description
                record.source_url = source_url
                record.retrieved_date = (
                    datetime.utcnow()
                )

                record.product = (
                    product_name
                )

                record.version = version

                record.codename = (
                    release.get(
                        "codename"
                    )
                )

                record.release_date = (
                    parse_date(
                        release.get(
                            "release_date"
                        )
                    )
                )

                record.is_maintained = bool(
                    release.get(
                        "is_maintained"
                    )
                )

                record.is_eol = bool(
                    release.get(
                        "is_eol"
                    )
                )

                record.eol_date = (
                    parse_date(
                        release.get(
                            "eol_date"
                        )
                    )
                )

                record.latest_version = (
                    release.get(
                        "latest_version"
                    )
                )

                record.latest_release_date = (
                    parse_date(
                        release.get(
                            "latest_release_date"
                        )
                    )
                )

                updated_count += 1

        db.session.commit()

        return {
            "success": True,
            "error": None,
            "created": created_count,
            "updated": updated_count
        }

    except Exception as error:

        db.session.rollback()

        return {
            "success": False,
            "error": str(error),
            "created": 0,
            "updated": 0
        }