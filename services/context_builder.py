from datetime import date, datetime


MAX_CONTEXT_RECORDS = 5


def format_date(value):
    """
    Convert date/datetime values into a clean
    ISO-style string for AI context.

    Missing values are represented as "Unknown".
    """

    if value is None:
        return "Unknown"

    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")

    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")

    return str(value)


def build_record_context(record):
    """
    Convert one LifecycleRecord into a limited,
    structured dictionary containing only fields
    useful for lifecycle intelligence.

    Sensitive configuration values, database
    credentials, internal application settings,
    and unrelated fields are intentionally
    excluded.
    """

    return {
        "record_id": record.id,
        "title": record.title,
        "product": record.product,
        "version": record.version,
        "codename": record.codename,
        "description": record.description,
        "release_date": format_date(
            record.release_date
        ),
        "is_maintained": bool(
            record.is_maintained
        ),
        "is_eol": bool(
            record.is_eol
        ),
        "eol_date": format_date(
            record.eol_date
        ),
        "latest_version": (
            record.latest_version
            or "Unknown"
        ),
        "latest_release_date": format_date(
            record.latest_release_date
        ),
        "source": record.source,
        "source_url": record.source_url,
        "retrieved_date": format_date(
            record.retrieved_date
        )
    }


def build_context(records):
    """
    Build a bounded context package from
    retrieved LifecycleRecord objects.

    Only the first MAX_CONTEXT_RECORDS records
    are included.

    Returns both:
    - structured_items: useful for validation
      and persistence
    - context_text: formatted text to send to
      the intelligent component
    """

    if not records:
        return {
            "success": False,
            "error": (
                "No lifecycle records were "
                "available to build context."
            ),
            "record_count": 0,
            "record_ids": [],
            "structured_items": [],
            "context_text": ""
        }

    limited_records = list(
        records[:MAX_CONTEXT_RECORDS]
    )

    structured_items = [
        build_record_context(record)
        for record in limited_records
    ]

    sections = []

    for index, item in enumerate(
        structured_items,
        start=1
    ):

        codename = (
            item["codename"]
            or "None"
        )

        section = (
            f"RECORD {index}\n"
            f"Record ID: {item['record_id']}\n"
            f"Title: {item['title']}\n"
            f"Product: {item['product']}\n"
            f"Version: {item['version']}\n"
            f"Codename: {codename}\n"
            f"Description: {item['description']}\n"
            f"Release Date: "
            f"{item['release_date']}\n"
            f"Maintained: "
            f"{item['is_maintained']}\n"
            f"End of Life: "
            f"{item['is_eol']}\n"
            f"EOL Date: "
            f"{item['eol_date']}\n"
            f"Latest Version: "
            f"{item['latest_version']}\n"
            f"Latest Release Date: "
            f"{item['latest_release_date']}\n"
            f"Source: {item['source']}\n"
            f"Source URL: "
            f"{item['source_url']}\n"
            f"Retrieved Date: "
            f"{item['retrieved_date']}"
        )

        sections.append(section)

    context_text = "\n\n".join(
        sections
    )

    return {
        "success": True,
        "error": None,
        "record_count": len(
            structured_items
        ),
        "record_ids": [
            item["record_id"]
            for item in structured_items
        ],
        "structured_items": (
            structured_items
        ),
        "context_text": context_text
    }