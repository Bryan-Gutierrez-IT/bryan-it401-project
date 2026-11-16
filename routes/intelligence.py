import json

from flask import render_template, request

from extensions import db
from models import IntelligenceResult
from services.intelligence_persistence import (
    save_intelligence_result
)
from services.intelligence_service import (
    generate_lifecycle_intelligence
)
from services.search_service import (
    search_lifecycle_records
)


MAX_INTELLIGENCE_RECORDS = 5


def extract_lifecycle_records(search_result):
    """
    Extract LifecycleRecord objects from the
    existing A4 search-service response.

    The intelligence component only receives
    the top retrieved records.
    """

    if not search_result:
        return []

    if isinstance(search_result, dict):
        candidates = search_result.get(
            "results",
            []
        )

    elif isinstance(search_result, list):
        candidates = search_result

    else:
        return []

    records = []

    for item in candidates:

        # The search service may already return
        # the LifecycleRecord object.
        if (
            hasattr(item, "id")
            and hasattr(item, "product")
        ):
            records.append(
                item
            )

        # A4 ranked results may wrap the model
        # inside a result dictionary.
        elif isinstance(item, dict):

            record = (
                item.get("record")
                or item.get(
                    "lifecycle_record"
                )
            )

            if record is not None:
                records.append(
                    record
                )

        if (
            len(records)
            >= MAX_INTELLIGENCE_RECORDS
        ):
            break

    return records


def parse_json_list(value):
    """
    Safely convert stored JSON text back
    into a Python list for the history page.
    """

    if not value:
        return []

    try:

        parsed = json.loads(
            value
        )

        if isinstance(parsed, list):
            return parsed

    except (
        json.JSONDecodeError,
        TypeError
    ):
        pass

    return []


def register_intelligence_routes(app):

    @app.route(
        "/intelligence",
        methods=[
            "GET",
            "POST"
        ]
    )
    def intelligence():

        search_query = ""
        user_request = ""

        retrieved_records = []

        generation = None

        error = None
        storage_error = None

        stored_result_id = None

        if request.method == "POST":

            search_query = (
                request.form.get(
                    "search_query",
                    ""
                )
                .strip()
            )

            user_request = (
                request.form.get(
                    "user_request",
                    ""
                )
                .strip()
            )

            # ---------------------------------
            # Validate user input
            # ---------------------------------

            if not search_query:

                error = (
                    "Enter a lifecycle search "
                    "such as Chrome 154 or "
                    "macOS Ventura."
                )

            elif not user_request:

                error = (
                    "Enter a question or "
                    "request for the "
                    "intelligence component."
                )

            elif len(search_query) > 200:

                error = (
                    "The lifecycle search "
                    "must be 200 characters "
                    "or fewer."
                )

            elif len(user_request) > 500:

                error = (
                    "The intelligence request "
                    "must be 500 characters "
                    "or fewer."
                )

            else:

                # -----------------------------
                # A4 retrieval
                # -----------------------------

                try:

                    search_result = (
                        search_lifecycle_records(
                            query_text=(
                                search_query
                            ),
                            product_filter="",
                            status_filter="",
                            sort_option=(
                                "relevance"
                            ),
                            page=1,
                            search_requested=True
                        )
                    )

                    retrieved_records = (
                        extract_lifecycle_records(
                            search_result
                        )
                    )

                except Exception as exc:

                    print(
                        "Intelligence retrieval "
                        f"error: {exc}"
                    )

                    retrieved_records = []

                    error = (
                        "BryghtCentral could "
                        "not retrieve lifecycle "
                        "records for this "
                        "request."
                    )

                # -----------------------------
                # Empty-context handling
                # -----------------------------

                if (
                    not error
                    and not retrieved_records
                ):

                    error = (
                        "No lifecycle records "
                        "matched that search. "
                        "Intelligence was not "
                        "generated because "
                        "there was no retrieved "
                        "context."
                    )

                # -----------------------------
                # Intelligence generation
                # -----------------------------

                if (
                    not error
                    and retrieved_records
                ):

                    generation_result = (
                        generate_lifecycle_intelligence(
                            user_request=(
                                user_request
                            ),
                            records=(
                                retrieved_records
                            )
                        )
                    )

                    if generation_result[
                        "success"
                    ]:

                        generation = (
                            generation_result
                        )

                        # ---------------------
                        # Persist only valid
                        # successful output
                        # ---------------------

                        save_result = (
                            save_intelligence_result(
                                generation_result
                            )
                        )

                        if save_result[
                            "success"
                        ]:

                            stored_result_id = (
                                save_result[
                                    "record"
                                ].id
                            )

                        else:

                            storage_error = (
                                save_result[
                                    "error"
                                ]
                            )

                    else:

                        error = (
                            generation_result[
                                "error"
                            ]
                        )

        return render_template(
            "intelligence.html",
            search_query=search_query,
            user_request=user_request,
            retrieved_records=(
                retrieved_records
            ),
            generation=generation,
            error=error,
            storage_error=storage_error,
            stored_result_id=(
                stored_result_id
            )
        )

    @app.route(
        "/intelligence-history"
    )
    def intelligence_history():

        try:

            stored_results = (
                db.session.execute(
                    db.select(
                        IntelligenceResult
                    )
                    .order_by(
                        IntelligenceResult
                        .generated_at
                        .desc(),
                        IntelligenceResult
                        .id
                        .desc()
                    )
                )
                .scalars()
                .all()
            )

        except Exception as exc:

            print(
                "Intelligence history "
                f"database error: {exc}"
            )

            stored_results = []

        history_items = []

        for result in stored_results:

            history_items.append(
                {
                    "record": result,
                    "rationale": (
                        parse_json_list(
                            result.rationale_json
                        )
                    ),
                    "supporting_items": (
                        parse_json_list(
                            result
                            .supporting_items_json
                        )
                    ),
                    "limitations": (
                        parse_json_list(
                            result
                            .limitations_json
                        )
                    ),
                    "source_record_ids": (
                        parse_json_list(
                            result
                            .source_record_ids_json
                        )
                    )
                }
            )

        return render_template(
            "intelligence_history.html",
            history_items=history_items
        )