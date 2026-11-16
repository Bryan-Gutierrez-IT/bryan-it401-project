from typing import List, Literal

from pydantic import BaseModel


VALID_RECOMMENDATIONS = {
    "KEEP",
    "UPGRADE",
    "REPLACE",
    "INVESTIGATE"
}

VALID_CONFIDENCE_LEVELS = {
    "high",
    "medium",
    "low"
}


class SupportingItem(BaseModel):
    record_id: int
    product: str
    version: str
    source: str
    evidence: str


class IntelligenceOutput(BaseModel):
    summary: str

    recommendation: Literal[
        "KEEP",
        "UPGRADE",
        "REPLACE",
        "INVESTIGATE"
    ]

    confidence: Literal[
        "high",
        "medium",
        "low"
    ]

    rationale: List[str]

    supporting_items: List[
        SupportingItem
    ]

    limitations: List[str]


def validate_intelligence_output(
    output,
    allowed_record_ids
):
    """
    Perform application-level validation
    after structured parsing.

    This protects BryghtCentral from:
    - empty required fields
    - unsupported recommendation values
    - unsupported confidence values
    - missing rationale
    - fabricated supporting record IDs
    - empty evidence
    """

    if output is None:
        return {
            "success": False,
            "error": (
                "The intelligence service "
                "returned no structured output."
            ),
            "data": None
        }

    if isinstance(
        output,
        IntelligenceOutput
    ):
        data = output.model_dump()

    elif isinstance(output, dict):
        data = output

    else:
        return {
            "success": False,
            "error": (
                "The intelligence output "
                "was not in the expected format."
            ),
            "data": None
        }

    required_text_fields = [
        "summary",
        "recommendation",
        "confidence"
    ]

    for field_name in required_text_fields:

        value = data.get(
            field_name
        )

        if (
            not isinstance(value, str)
            or not value.strip()
        ):
            return {
                "success": False,
                "error": (
                    f"Required field "
                    f"'{field_name}' "
                    "was missing or empty."
                ),
                "data": None
            }

    recommendation = (
        data["recommendation"]
        .strip()
        .upper()
    )

    if (
        recommendation
        not in VALID_RECOMMENDATIONS
    ):
        return {
            "success": False,
            "error": (
                "The generated recommendation "
                "was not an allowed value."
            ),
            "data": None
        }

    confidence = (
        data["confidence"]
        .strip()
        .lower()
    )

    if (
        confidence
        not in VALID_CONFIDENCE_LEVELS
    ):
        return {
            "success": False,
            "error": (
                "The generated confidence "
                "level was not valid."
            ),
            "data": None
        }

    rationale = data.get(
        "rationale"
    )

    if (
        not isinstance(
            rationale,
            list
        )
        or len(rationale) == 0
    ):
        return {
            "success": False,
            "error": (
                "The generated result did "
                "not include rationale."
            ),
            "data": None
        }

    cleaned_rationale = []

    for reason in rationale:

        if (
            not isinstance(reason, str)
            or not reason.strip()
        ):
            return {
                "success": False,
                "error": (
                    "One of the rationale "
                    "items was empty."
                ),
                "data": None
            }

        cleaned_rationale.append(
            reason.strip()
        )

    supporting_items = data.get(
        "supporting_items"
    )

    if (
        not isinstance(
            supporting_items,
            list
        )
        or len(supporting_items) == 0
    ):
        return {
            "success": False,
            "error": (
                "The recommendation did "
                "not identify supporting "
                "lifecycle records."
            ),
            "data": None
        }

    allowed_ids = {
        int(record_id)
        for record_id
        in allowed_record_ids
    }

    cleaned_items = []

    for item in supporting_items:

        if hasattr(
            item,
            "model_dump"
        ):
            item = item.model_dump()

        if not isinstance(
            item,
            dict
        ):
            return {
                "success": False,
                "error": (
                    "A supporting item had "
                    "an invalid format."
                ),
                "data": None
            }

        record_id = item.get(
            "record_id"
        )

        try:
            record_id = int(
                record_id
            )

        except (
            TypeError,
            ValueError
        ):
            return {
                "success": False,
                "error": (
                    "A supporting item "
                    "contained an invalid "
                    "record ID."
                ),
                "data": None
            }

        if record_id not in allowed_ids:

            return {
                "success": False,
                "error": (
                    "The model referenced "
                    "a lifecycle record that "
                    "was not supplied in the "
                    "retrieved context."
                ),
                "data": None
            }

        required_item_fields = [
            "product",
            "version",
            "source",
            "evidence"
        ]

        for field_name in (
            required_item_fields
        ):

            value = item.get(
                field_name
            )

            if (
                not isinstance(value, str)
                or not value.strip()
            ):
                return {
                    "success": False,
                    "error": (
                        "A supporting item "
                        f"was missing "
                        f"'{field_name}'."
                    ),
                    "data": None
                }

        cleaned_items.append({
            "record_id": record_id,
            "product": (
                item["product"].strip()
            ),
            "version": (
                item["version"].strip()
            ),
            "source": (
                item["source"].strip()
            ),
            "evidence": (
                item["evidence"].strip()
            )
        })

    limitations = data.get(
        "limitations",
        []
    )

    if not isinstance(
        limitations,
        list
    ):
        return {
            "success": False,
            "error": (
                "The limitations field "
                "was not in the expected "
                "format."
            ),
            "data": None
        }

    cleaned_limitations = [
        str(item).strip()
        for item in limitations
        if str(item).strip()
    ]

    if not cleaned_limitations:

        cleaned_limitations = [
            (
                "This recommendation is "
                "limited to the lifecycle "
                "information supplied by "
                "BryghtCentral."
            )
        ]

    cleaned_data = {
        "summary": (
            data["summary"].strip()
        ),
        "recommendation": (
            recommendation
        ),
        "confidence": (
            confidence
        ),
        "rationale": (
            cleaned_rationale
        ),
        "supporting_items": (
            cleaned_items
        ),
        "limitations": (
            cleaned_limitations
        )
    }

    return {
        "success": True,
        "error": None,
        "data": cleaned_data
    }