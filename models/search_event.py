from datetime import datetime

from extensions import db


class SearchEvent(db.Model):
    __tablename__ = "search_events"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    query = db.Column(
        db.String(255),
        nullable=False
    )

    normalized_query = db.Column(
        db.String(255),
        nullable=False
    )

    product_filter = db.Column(
        db.String(100),
        nullable=True
    )

    status_filter = db.Column(
        db.String(50),
        nullable=True
    )

    sort_option = db.Column(
        db.String(50),
        nullable=False,
        default="relevance"
    )

    result_count = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    no_results = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    searched_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    def __repr__(self):
        return (
            f"<SearchEvent "
            f"query='{self.query}' "
            f"results={self.result_count}>"
        )