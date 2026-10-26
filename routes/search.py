from flask import (
    render_template,
    request
)

from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

from extensions import db
from models import SearchEvent
from services.search_service import (
    record_search_event,
    search_lifecycle_records
)


def register_search_routes(app):

    @app.route("/search")
    def search():

        search_requested = (
            "q" in request.args
        )

        query_text = request.args.get(
            "q",
            ""
        )

        product_filter = request.args.get(
            "product",
            ""
        )

        status_filter = request.args.get(
            "status",
            ""
        )

        sort_option = request.args.get(
            "sort",
            "relevance"
        )

        requested_page = request.args.get(
            "page",
            "1"
        )

        telemetry_warning = None

        try:

            search_result = (
                search_lifecycle_records(
                    query_text=query_text,
                    product_filter=product_filter,
                    status_filter=status_filter,
                    sort_option=sort_option,
                    page=requested_page,
                    search_requested=(
                        search_requested
                    )
                )
            )

        except SQLAlchemyError:

            db.session.rollback()

            search_result = {
                "success": False,
                "searched": search_requested,
                "error": (
                    "Search is temporarily "
                    "unavailable because the "
                    "database could not be reached."
                ),
                "notice": None,
                "original_query": (
                    query_text.strip()
                ),
                "normalized_query": "",
                "tokens": [],
                "product_filter": (
                    product_filter
                ),
                "status_filter": (
                    status_filter
                ),
                "sort_option": (
                    sort_option
                ),
                "products": [],
                "results": [],
                "total": 0,
                "page": 1,
                "pages": 0,
                "per_page": 15,
                "has_prev": False,
                "has_next": False,
                "prev_num": None,
                "next_num": None,
                "first_result": 0,
                "last_result": 0
            }

        # Record telemetry only for the first
        # page of a completed search.
        #
        # Moving between pagination pages does
        # not create duplicate telemetry events.
        page_parameter = request.args.get(
            "page"
        )

        initial_search_page = (
            page_parameter is None
            or page_parameter == ""
            or page_parameter == "1"
        )

        if (
            search_result["searched"]
            and search_result["success"]
            and initial_search_page
        ):

            telemetry_saved = (
                record_search_event(
                    original_query=(
                        search_result[
                            "original_query"
                        ]
                    ),
                    normalized_query=(
                        search_result[
                            "normalized_query"
                        ]
                    ),
                    product_filter=(
                        search_result[
                            "product_filter"
                        ]
                    ),
                    status_filter=(
                        search_result[
                            "status_filter"
                        ]
                    ),
                    sort_option=(
                        search_result[
                            "sort_option"
                        ]
                    ),
                    result_count=(
                        search_result[
                            "total"
                        ]
                    )
                )
            )

            if not telemetry_saved:

                telemetry_warning = (
                    "Search results loaded, "
                    "but search telemetry could "
                    "not be recorded."
                )

        return render_template(
            "search.html",
            search_result=search_result,
            telemetry_warning=(
                telemetry_warning
            )
        )


    @app.route("/search-history")
    def search_history():

        history_error = None
        events = []
        total_events = 0

        try:

            statement = (
                db.select(SearchEvent)
                .order_by(
                    SearchEvent
                    .searched_at
                    .desc()
                )
                .limit(50)
            )

            events = (
                db.session
                .execute(statement)
                .scalars()
                .all()
            )

            total_statement = (
                db.select(
                    func.count()
                )
                .select_from(
                    SearchEvent
                )
            )

            total_events = (
                db.session.scalar(
                    total_statement
                )
                or 0
            )

        except SQLAlchemyError:

            db.session.rollback()

            history_error = (
                "Search history is temporarily "
                "unavailable because the "
                "database could not be reached."
            )

        return render_template(
            "search_history.html",
            events=events,
            total_events=total_events,
            history_error=history_error
        )