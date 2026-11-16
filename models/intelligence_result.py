from datetime import datetime

from extensions import db


class IntelligenceResult(db.Model):
    __tablename__ = "intelligence_results"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_request = db.Column(
        db.Text,
        nullable=False
    )

    capability = db.Column(
        db.String(50),
        nullable=False,
        default="recommendation"
    )

    summary = db.Column(
        db.Text,
        nullable=False
    )

    recommendation = db.Column(
        db.String(50),
        nullable=False
    )

    confidence = db.Column(
        db.String(20),
        nullable=False
    )

    rationale_json = db.Column(
        db.Text,
        nullable=False
    )

    supporting_items_json = db.Column(
        db.Text,
        nullable=False
    )

    limitations_json = db.Column(
        db.Text,
        nullable=False
    )

    source_record_ids_json = db.Column(
        db.Text,
        nullable=False
    )

    prompt_version = db.Column(
        db.String(50),
        nullable=False
    )

    model_name = db.Column(
        db.String(100),
        nullable=False
    )

    generated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    def __repr__(self):
        return (
            f"<IntelligenceResult "
            f"id={self.id} "
            f"recommendation={self.recommendation}>"
        )