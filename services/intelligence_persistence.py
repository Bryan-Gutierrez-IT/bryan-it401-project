import json

from sqlalchemy.exc import SQLAlchemyError

from extensions import db
from models import IntelligenceResult


def save_intelligence_result(
    generation_result
):
    """
    Persist a successfully validated
    intelligence-generation result.

    Only successful results should be stored.
    """

    if not generation_result:
        return {
            "success": False,
            "error": (
                "No intelligence result "
                "was provided."
            ),
            "record": None
        }

    if not generation_result.get(
        "success"
    ):
        return {
            "success": False,
            "error": (
                "Failed intelligence "
                "generations are not stored."
            ),
            "record": None
        }

    data = generation_result.get(
        "data"
    )

    metadata = generation_result.get(
        "metadata"
    ) or {}

    if not data:
        return {
            "success": False,
            "error": (
                "The intelligence result "
                "does not contain validated "
                "output data."
            ),
            "record": None
        }

    try:

        record = IntelligenceResult(
            user_request=(
                metadata.get(
                    "user_request",
                    ""
                )
            ),
            capability=(
                "recommendation"
            ),
            summary=(
                data["summary"]
            ),
            recommendation=(
                data["recommendation"]
            ),
            confidence=(
                data["confidence"]
            ),
            rationale_json=(
                json.dumps(
                    data["rationale"],
                    ensure_ascii=False
                )
            ),
            supporting_items_json=(
                json.dumps(
                    data[
                        "supporting_items"
                    ],
                    ensure_ascii=False
                )
            ),
            limitations_json=(
                json.dumps(
                    data["limitations"],
                    ensure_ascii=False
                )
            ),
            source_record_ids_json=(
                json.dumps(
                    metadata.get(
                        "source_record_ids",
                        []
                    )
                )
            ),
            prompt_version=(
                metadata.get(
                    "prompt_version",
                    "unknown"
                )
            ),
            model_name=(
                metadata.get(
                    "model_name",
                    "unknown"
                )
            )
        )

        db.session.add(
            record
        )

        db.session.commit()

        return {
            "success": True,
            "error": None,
            "record": record
        }

    except (
        KeyError,
        TypeError,
        ValueError
    ) as exc:

        db.session.rollback()

        print(
            "Invalid intelligence "
            f"persistence data: {exc}"
        )

        return {
            "success": False,
            "error": (
                "The generated intelligence "
                "could not be prepared for "
                "storage."
            ),
            "record": None
        }

    except SQLAlchemyError as exc:

        db.session.rollback()

        print(
            "Database error while saving "
            f"intelligence: {exc}"
        )

        return {
            "success": False,
            "error": (
                "The generated intelligence "
                "could not be saved to the "
                "database."
            ),
            "record": None
        }