import json
import os
import time

import requests
from pydantic import ValidationError

from services.context_builder import build_context
from services.intelligence_validator import (
    IntelligenceOutput,
    validate_intelligence_output
)
from services.prompts import (
    PROMPT_VERSION,
    SYSTEM_INSTRUCTIONS,
    build_user_prompt
)


DEFAULT_MODEL = "gemini-3.6-flash"

MAX_ATTEMPTS = 3


INTELLIGENCE_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {
            "type": "string"
        },
        "recommendation": {
            "type": "string",
            "enum": [
                "KEEP",
                "UPGRADE",
                "REPLACE",
                "INVESTIGATE"
            ]
        },
        "confidence": {
            "type": "string",
            "enum": [
                "high",
                "medium",
                "low"
            ]
        },
        "rationale": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },
        "supporting_items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "record_id": {
                        "type": "integer"
                    },
                    "product": {
                        "type": "string"
                    },
                    "version": {
                        "type": "string"
                    },
                    "source": {
                        "type": "string"
                    },
                    "evidence": {
                        "type": "string"
                    }
                },
                "required": [
                    "record_id",
                    "product",
                    "version",
                    "source",
                    "evidence"
                ]
            }
        },
        "limitations": {
            "type": "array",
            "items": {
                "type": "string"
            }
        }
    },
    "required": [
        "summary",
        "recommendation",
        "confidence",
        "rationale",
        "supporting_items",
        "limitations"
    ]
}


def get_model_name():
    """
    Return the configured Gemini model.

    The model can be changed through .env
    without modifying the application.
    """

    return os.getenv(
        "GEMINI_MODEL",
        DEFAULT_MODEL
    )


def extract_response_text(data):
    """
    Safely extract generated text from a
    Gemini generateContent response.
    """

    candidates = data.get(
        "candidates",
        []
    )

    if not candidates:
        return {
            "success": False,
            "error": (
                "Gemini returned no response "
                "candidates."
            ),
            "text": None,
            "finish_reason": None
        }

    candidate = candidates[0]

    finish_reason = candidate.get(
        "finishReason"
    )

    content = candidate.get(
        "content",
        {}
    )

    parts = content.get(
        "parts",
        []
    )

    text_parts = []

    for part in parts:

        if part.get("thought"):
            continue

        text_value = part.get(
            "text"
        )

        if text_value:
            text_parts.append(
                text_value
            )

    output_text = "".join(
        text_parts
    ).strip()

    if not output_text:
        return {
            "success": False,
            "error": (
                "Gemini completed the request "
                "but returned no visible "
                "structured output."
            ),
            "text": None,
            "finish_reason": finish_reason
        }

    return {
        "success": True,
        "error": None,
        "text": output_text,
        "finish_reason": finish_reason
    }


def generate_lifecycle_intelligence(
    user_request,
    records
):
    """
    Generate lifecycle intelligence using
    retrieved BryghtCentral records only.

    Workflow:

    Retrieved records
        ↓
    Build bounded context
        ↓
    Construct prompt
        ↓
    Gemini structured generation
        ↓
    Pydantic validation
        ↓
    BryghtCentral record validation
        ↓
    Validated intelligence result
    """

    api_key = os.getenv(
        "GEMINI_API_KEY"
    )

    if not api_key:

        return {
            "success": False,
            "error_type": (
                "missing_api_key"
            ),
            "error": (
                "Intelligence generation is "
                "unavailable because the "
                "Gemini API key is not "
                "configured."
            ),
            "data": None,
            "metadata": None
        }

    user_request = str(
        user_request or ""
    ).strip()

    if not user_request:

        return {
            "success": False,
            "error_type": (
                "invalid_request"
            ),
            "error": (
                "Enter a lifecycle question "
                "or request before generating "
                "intelligence."
            ),
            "data": None,
            "metadata": None
        }

    if len(user_request) > 500:

        return {
            "success": False,
            "error_type": (
                "invalid_request"
            ),
            "error": (
                "The intelligence request "
                "must be 500 characters "
                "or fewer."
            ),
            "data": None,
            "metadata": None
        }

    # -----------------------------------------
    # Build bounded context
    # -----------------------------------------

    context_result = build_context(
        records
    )

    if not context_result[
        "success"
    ]:

        return {
            "success": False,
            "error_type": (
                "empty_context"
            ),
            "error": (
                context_result[
                    "error"
                ]
            ),
            "data": None,
            "metadata": None
        }

    # -----------------------------------------
    # Construct user prompt
    # -----------------------------------------

    user_prompt = (
        build_user_prompt(
            user_request=(
                user_request
            ),
            context_text=(
                context_result[
                    "context_text"
                ]
            )
        )
    )

    model_name = get_model_name()

    url = (
        "https://"
        "generativelanguage.googleapis.com/"
        f"v1beta/models/"
        f"{model_name}:generateContent"
    )

    headers = {
        "x-goog-api-key": api_key,
        "Content-Type": (
            "application/json"
        )
    }

    payload = {
        "systemInstruction": {
            "parts": [
                {
                    "text": (
                        SYSTEM_INSTRUCTIONS
                    )
                }
            ]
        },
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": (
                            user_prompt
                        )
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0,
            "maxOutputTokens": 2048,
            "responseMimeType": (
                "application/json"
            ),
            "responseJsonSchema": (
                INTELLIGENCE_JSON_SCHEMA
            )
        }
    }

    last_error = None

    # -----------------------------------------
    # Gemini request with limited retries
    # -----------------------------------------

    for attempt in range(
        1,
        MAX_ATTEMPTS + 1
    ):

        try:

            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=(10, 90)
            )

        except requests.Timeout:

            last_error = {
                "success": False,
                "error_type": "timeout",
                "error": (
                    "The intelligence service "
                    "timed out."
                ),
                "data": None,
                "metadata": None
            }

            if attempt < MAX_ATTEMPTS:

                time.sleep(
                    3 * attempt
                )

                continue

            return last_error

        except requests.ConnectionError:

            return {
                "success": False,
                "error_type": (
                    "connection_error"
                ),
                "error": (
                    "BryghtCentral could not "
                    "connect to the Gemini "
                    "intelligence service."
                ),
                "data": None,
                "metadata": None
            }

        # -------------------------------------
        # Successful HTTP request
        # -------------------------------------

        if response.status_code == 200:

            try:

                response_data = (
                    response.json()
                )

            except ValueError:

                return {
                    "success": False,
                    "error_type": (
                        "invalid_output"
                    ),
                    "error": (
                        "Gemini returned an "
                        "invalid response format."
                    ),
                    "data": None,
                    "metadata": None
                }

            extracted = (
                extract_response_text(
                    response_data
                )
            )

            if not extracted[
                "success"
            ]:

                return {
                    "success": False,
                    "error_type": (
                        "invalid_output"
                    ),
                    "error": (
                        extracted[
                            "error"
                        ]
                    ),
                    "data": None,
                    "metadata": {
                        "model_name": (
                            model_name
                        ),
                        "prompt_version": (
                            PROMPT_VERSION
                        ),
                        "finish_reason": (
                            extracted[
                                "finish_reason"
                            ]
                        )
                    }
                }

            output_text = (
                extracted["text"]
            )

            # ---------------------------------
            # Pydantic structured validation
            # ---------------------------------

            try:

                parsed_output = (
                    IntelligenceOutput
                    .model_validate_json(
                        output_text
                    )
                )

            except ValidationError as exc:

                print(
                    "Gemini structured "
                    "validation error:",
                    exc
                )

                return {
                    "success": False,
                    "error_type": (
                        "invalid_output"
                    ),
                    "error": (
                        "The generated result "
                        "did not match the "
                        "required intelligence "
                        "structure."
                    ),
                    "data": None,
                    "metadata": {
                        "model_name": (
                            model_name
                        ),
                        "prompt_version": (
                            PROMPT_VERSION
                        )
                    }
                }

            # ---------------------------------
            # Application-level validation
            # ---------------------------------

            validation_result = (
                validate_intelligence_output(
                    output=(
                        parsed_output
                    ),
                    allowed_record_ids=(
                        context_result[
                            "record_ids"
                        ]
                    )
                )
            )

            if not validation_result[
                "success"
            ]:

                return {
                    "success": False,
                    "error_type": (
                        "validation_failed"
                    ),
                    "error": (
                        validation_result[
                            "error"
                        ]
                    ),
                    "data": None,
                    "metadata": {
                        "model_name": (
                            model_name
                        ),
                        "prompt_version": (
                            PROMPT_VERSION
                        ),
                        "source_record_ids": (
                            context_result[
                                "record_ids"
                            ]
                        )
                    }
                }

            usage_metadata = (
                response_data.get(
                    "usageMetadata",
                    {}
                )
            )

            # ---------------------------------
            # Fully validated result
            # ---------------------------------

            return {
                "success": True,
                "error_type": None,
                "error": None,
                "data": (
                    validation_result[
                        "data"
                    ]
                ),
                "metadata": {
                    "model_name": (
                        response_data.get(
                            "modelVersion"
                        )
                        or model_name
                    ),
                    "configured_model": (
                        model_name
                    ),
                    "prompt_version": (
                        PROMPT_VERSION
                    ),
                    "source_record_ids": (
                        context_result[
                            "record_ids"
                        ]
                    ),
                    "context_record_count": (
                        context_result[
                            "record_count"
                        ]
                    ),
                    "user_request": (
                        user_request
                    ),
                    "finish_reason": (
                        extracted[
                            "finish_reason"
                        ]
                    ),
                    "response_id": (
                        response_data.get(
                            "responseId"
                        )
                    ),
                    "prompt_tokens": (
                        usage_metadata.get(
                            "promptTokenCount"
                        )
                    ),
                    "output_tokens": (
                        usage_metadata.get(
                            "candidatesTokenCount"
                        )
                    ),
                    "total_tokens": (
                        usage_metadata.get(
                            "totalTokenCount"
                        )
                    )
                }
            }

        # -------------------------------------
        # Retry temporary provider failures
        # -------------------------------------

        if response.status_code in (
            429,
            500,
            502,
            503,
            504
        ):

            if (
                response.status_code
                == 429
            ):

                error_type = (
                    "rate_limit"
                )

                message = (
                    "The Gemini service is "
                    "temporarily rate limited."
                )

            else:

                error_type = (
                    "service_unavailable"
                )

                message = (
                    "The Gemini service is "
                    "temporarily unavailable."
                )

            last_error = {
                "success": False,
                "error_type": (
                    error_type
                ),
                "error": message,
                "data": None,
                "metadata": None
            }

            if attempt < MAX_ATTEMPTS:

                time.sleep(
                    3 * attempt
                )

                continue

            return last_error

        # -------------------------------------
        # Authentication / permission errors
        # -------------------------------------

        if response.status_code in (
            401,
            403
        ):

            return {
                "success": False,
                "error_type": (
                    "authentication_error"
                ),
                "error": (
                    "The Gemini API key was "
                    "rejected or does not have "
                    "permission to use the "
                    "configured model."
                ),
                "data": None,
                "metadata": None
            }

        # -------------------------------------
        # Other provider errors
        # -------------------------------------

        try:

            error_data = (
                response.json()
            )

            provider_message = (
                error_data
                .get("error", {})
                .get("message")
            )

        except ValueError:

            provider_message = None

        print(
            "Gemini API error:",
            response.status_code,
            provider_message
        )

        return {
            "success": False,
            "error_type": "api_error",
            "error": (
                "The Gemini intelligence "
                "service returned an error."
            ),
            "data": None,
            "metadata": None
        }

    return (
        last_error
        or {
            "success": False,
            "error_type": (
                "generation_failed"
            ),
            "error": (
                "Intelligence generation "
                "failed unexpectedly."
            ),
            "data": None,
            "metadata": None
        }
    )