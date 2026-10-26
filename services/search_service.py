from sqlalchemy import (
    and_,
    case,
    func,
    or_
)

from extensions import db
from models import (
    LifecycleRecord,
    SearchEvent
)


PER_PAGE = 15
MAX_QUERY_LENGTH = 200

VALID_STATUS_FILTERS = {
    "",
    "active",
    "ended",
    "unknown"
}

VALID_SORT_OPTIONS = {
    "relevance",
    "newest",
    "oldest",
    "alphabetical"
}


def normalize_query(query):
    """
    Normalize user search text.

    The original query is preserved separately
    for display.

    Normalization:
    - removes leading/trailing whitespace
    - collapses repeated internal whitespace
    - converts text to lowercase
    """

    if query is None:
        return ""

    cleaned = " ".join(
        str(query).strip().split()
    )

    return cleaned.lower()


def tokenize_query(normalized_query):
    """
    Break the normalized query into simple
    whitespace-separated search terms.
    """

    if not normalized_query:
        return []

    return [
        token
        for token
        in normalized_query.split()
        if token
    ]


def get_product_options():
    """
    Return distinct products currently stored
    in the lifecycle_records table.
    """

    rows = (
        db.session.query(
            LifecycleRecord.product
        )
        .distinct()
        .order_by(
            LifecycleRecord.product
        )
        .all()
    )

    return [
        row[0]
        for row in rows
        if row[0]
    ]


def _searchable_field_expressions():
    """
    Return normalized SQL expressions for
    searchable model fields.
    """

    return {
        "title": func.lower(
            func.coalesce(
                LifecycleRecord.title,
                ""
            )
        ),
        "description": func.lower(
            func.coalesce(
                LifecycleRecord.description,
                ""
            )
        ),
        "product": func.lower(
            func.coalesce(
                LifecycleRecord.product,
                ""
            )
        ),
        "version": func.lower(
            func.coalesce(
                LifecycleRecord.version,
                ""
            )
        ),
        "codename": func.lower(
            func.coalesce(
                LifecycleRecord.codename,
                ""
            )
        )
    }


def build_relevance_score(
    normalized_query,
    tokens
):
    """
    Build a simple relevance score.

    Weighting strategy:

    Exact title match       +10
    Exact product match      +9
    Exact codename match     +8
    Exact version match      +7

    Partial title match      +5
    Partial product match    +4
    Partial codename match   +4
    Partial version match    +4
    Description match        +1

    Each individual token may also contribute
    to the score.

    This is intentionally rule-based so the
    ranking is understandable and easy to
    explain for A4.
    """

    fields = (
        _searchable_field_expressions()
    )

    score_parts = []

    # Exact full-query matches.
    score_parts.extend([
        case(
            (
                fields["title"]
                == normalized_query,
                10
            ),
            else_=0
        ),
        case(
            (
                fields["product"]
                == normalized_query,
                9
            ),
            else_=0
        ),
        case(
            (
                fields["codename"]
                == normalized_query,
                8
            ),
            else_=0
        ),
        case(
            (
                fields["version"]
                == normalized_query,
                7
            ),
            else_=0
        )
    ])

    query_pattern = (
        f"%{normalized_query}%"
    )

    # Partial full-query matches.
    score_parts.extend([
        case(
            (
                fields["title"].like(
                    query_pattern
                ),
                5
            ),
            else_=0
        ),
        case(
            (
                fields["product"].like(
                    query_pattern
                ),
                4
            ),
            else_=0
        ),
        case(
            (
                fields["codename"].like(
                    query_pattern
                ),
                4
            ),
            else_=0
        ),
        case(
            (
                fields["version"].like(
                    query_pattern
                ),
                4
            ),
            else_=0
        ),
        case(
            (
                fields["description"].like(
                    query_pattern
                ),
                1
            ),
            else_=0
        )
    ])

    # Individual-token matches.
    for token in tokens:

        token_pattern = (
            f"%{token}%"
        )

        score_parts.extend([
            case(
                (
                    fields["title"].like(
                        token_pattern
                    ),
                    3
                ),
                else_=0
            ),
            case(
                (
                    fields["product"].like(
                        token_pattern
                    ),
                    2
                ),
                else_=0
            ),
            case(
                (
                    fields["codename"].like(
                        token_pattern
                    ),
                    2
                ),
                else_=0
            ),
            case(
                (
                    fields["version"].like(
                        token_pattern
                    ),
                    2
                ),
                else_=0
            ),
            case(
                (
                    fields["description"].like(
                        token_pattern
                    ),
                    1
                ),
                else_=0
            )
        ])

    # Small lifecycle usefulness boost.
    score_parts.append(
        case(
            (
                LifecycleRecord
                .is_maintained
                .is_(True),
                1
            ),
            else_=0
        )
    )

    score = score_parts[0]

    for part in score_parts[1:]:
        score = score + part

    return score.label(
        "relevance_score"
    )


def search_lifecycle_records(
    query_text,
    product_filter="",
    status_filter="",
    sort_option="relevance",
    page=1,
    search_requested=True
):
    """
    Search stored LifecycleRecord information.

    Retrieval sequence:

    Query processing
        ↓
    Multi-field retrieval
        ↓
    Boolean filtering
        ↓
    Relevance ranking / sorting
        ↓
    Pagination
        ↓
    Results
    """

    original_query = (
        str(query_text or "")
    )

    normalized_query = (
        normalize_query(
            original_query
        )
    )

    product_filter = (
        str(
            product_filter or ""
        ).strip()
    )

    status_filter = (
        str(
            status_filter or ""
        ).strip().lower()
    )

    sort_option = (
        str(
            sort_option or "relevance"
        ).strip().lower()
    )

    products = (
        get_product_options()
    )

    result = {
        "success": True,
        "searched": False,
        "error": None,
        "notice": None,
        "original_query": (
            original_query.strip()
        ),
        "normalized_query": (
            normalized_query
        ),
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
        "products": products,
        "results": [],
        "total": 0,
        "page": 1,
        "pages": 0,
        "per_page": PER_PAGE,
        "has_prev": False,
        "has_next": False,
        "prev_num": None,
        "next_num": None,
        "first_result": 0,
        "last_result": 0
    }

    # Initial page load:
    # do not treat it as an error.
    if not search_requested:

        return result

    result["searched"] = True

    # Empty query handling.
    if not normalized_query:

        result["success"] = False

        result["error"] = (
            "Enter a keyword or phrase "
            "to begin searching."
        )

        return result

    # Very long query handling.
    if (
        len(normalized_query)
        > MAX_QUERY_LENGTH
    ):

        result["success"] = False

        result["error"] = (
            "Search queries must be "
            f"{MAX_QUERY_LENGTH} characters "
            "or fewer."
        )

        return result

    # Validate status filter.
    if (
        status_filter
        not in VALID_STATUS_FILTERS
    ):

        result["success"] = False

        result["error"] = (
            "The selected status filter "
            "is not valid."
        )

        return result

    # Validate sort option.
    if (
        sort_option
        not in VALID_SORT_OPTIONS
    ):

        result["success"] = False

        result["error"] = (
            "The selected sorting option "
            "is not valid."
        )

        return result

    # Validate product filter.
    if (
        product_filter
        and product_filter
        not in products
    ):

        result["success"] = False

        result["error"] = (
            "The selected product filter "
            "is not valid."
        )

        return result

    # Validate page number.
    try:

        page = int(page)

    except (
        TypeError,
        ValueError
    ):

        page = 1

        result["notice"] = (
            "The requested page number "
            "was invalid. Showing page 1."
        )

    if page < 1:

        page = 1

        result["notice"] = (
            "The requested page number "
            "was invalid. Showing page 1."
        )

    tokens = tokenize_query(
        normalized_query
    )

    result["tokens"] = tokens

    fields = (
        _searchable_field_expressions()
    )

    # -------------------------------------------------
    # Multi-field keyword retrieval
    # -------------------------------------------------

    token_conditions = []

    for token in tokens:

        pattern = f"%{token}%"

        token_conditions.append(
            or_(
                fields["title"].like(
                    pattern
                ),
                fields[
                    "description"
                ].like(
                    pattern
                ),
                fields["product"].like(
                    pattern
                ),
                fields["version"].like(
                    pattern
                ),
                fields["codename"].like(
                    pattern
                )
            )
        )

    relevance_score = (
        build_relevance_score(
            normalized_query,
            tokens
        )
    )

    query = (
        LifecycleRecord.query
        .add_columns(
            relevance_score
        )
    )

    # All query terms must appear somewhere
    # across the searchable fields.
    if token_conditions:

        query = query.filter(
            and_(
                *token_conditions
            )
        )

    # -------------------------------------------------
    # Boolean filters
    # -------------------------------------------------

    if product_filter:

        query = query.filter(
            LifecycleRecord.product
            == product_filter
        )

    if status_filter == "active":

        query = query.filter(
            LifecycleRecord
            .is_maintained
            .is_(True),
            LifecycleRecord
            .is_eol
            .is_(False)
        )

    elif status_filter == "ended":

        query = query.filter(
            LifecycleRecord
            .is_eol
            .is_(True)
        )

    elif status_filter == "unknown":

        query = query.filter(
            LifecycleRecord
            .is_maintained
            .is_(False),
            LifecycleRecord
            .is_eol
            .is_(False)
        )

    # -------------------------------------------------
    # Sorting / ranking
    # -------------------------------------------------

    if sort_option == "newest":

        query = query.order_by(
            LifecycleRecord
            .release_date
            .is_(None),
            LifecycleRecord
            .release_date
            .desc(),
            relevance_score.desc()
        )

    elif sort_option == "oldest":

        query = query.order_by(
            LifecycleRecord
            .release_date
            .is_(None),
            LifecycleRecord
            .release_date
            .asc(),
            relevance_score.desc()
        )

    elif sort_option == "alphabetical":

        query = query.order_by(
            LifecycleRecord
            .product
            .asc(),
            LifecycleRecord
            .version
            .asc()
        )

    else:

        # Default: relevance ranking.
        query = query.order_by(
            relevance_score.desc(),
            LifecycleRecord
            .is_maintained
            .desc(),
            LifecycleRecord
            .release_date
            .is_(None),
            LifecycleRecord
            .release_date
            .desc(),
            LifecycleRecord
            .product
            .asc()
        )

    # -------------------------------------------------
    # Pagination
    # -------------------------------------------------

    pagination = query.paginate(
        page=page,
        per_page=PER_PAGE,
        error_out=False
    )

    # Handle page numbers beyond the
    # available result set.
    if (
        pagination.total > 0
        and pagination.pages > 0
        and page > pagination.pages
    ):

        page = pagination.pages

        pagination = query.paginate(
            page=page,
            per_page=PER_PAGE,
            error_out=False
        )

        result["notice"] = (
            "The requested page did not "
            "exist. Showing the last "
            "available page."
        )

    formatted_results = []

    for row in pagination.items:

        record = row[0]
        score = row[1]

        formatted_results.append({
            "record": record,
            "score": int(
                score or 0
            )
        })

    total = pagination.total

    if total > 0:

        first_result = (
            (pagination.page - 1)
            * PER_PAGE
            + 1
        )

        last_result = min(
            pagination.page
            * PER_PAGE,
            total
        )

    else:

        first_result = 0
        last_result = 0

    result.update({
        "results": formatted_results,
        "total": total,
        "page": pagination.page,
        "pages": pagination.pages,
        "has_prev": pagination.has_prev,
        "has_next": pagination.has_next,
        "prev_num": pagination.prev_num,
        "next_num": pagination.next_num,
        "first_result": first_result,
        "last_result": last_result
    })

    return result


def record_search_event(
    original_query,
    normalized_query,
    product_filter,
    status_filter,
    sort_option,
    result_count
):
    """
    Store basic search telemetry.

    Telemetry failures are contained here
    so they do not prevent users from
    receiving search results.
    """

    try:

        event = SearchEvent(
            query=original_query,
            normalized_query=(
                normalized_query
            ),
            product_filter=(
                product_filter
                or None
            ),
            status_filter=(
                status_filter
                or None
            ),
            sort_option=(
                sort_option
                or "relevance"
            ),
            result_count=(
                result_count
            ),
            no_results=(
                result_count == 0
            )
        )

        db.session.add(event)
        db.session.commit()

        return True

    except Exception:

        db.session.rollback()

        return False