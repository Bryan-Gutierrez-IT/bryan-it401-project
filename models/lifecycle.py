from datetime import datetime

from extensions import db


class LifecycleRecord(db.Model):
    __tablename__ = "lifecycle_records"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    title = db.Column(
        db.String(255),
        nullable=False
    )

    description = db.Column(
        db.Text,
        nullable=False
    )

    source = db.Column(
        db.String(100),
        nullable=False
    )

    source_url = db.Column(
        db.String(500),
        nullable=False
    )

    retrieved_date = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    created_date = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    product = db.Column(
        db.String(100),
        nullable=False
    )

    version = db.Column(
        db.String(100),
        nullable=False
    )

    codename = db.Column(
        db.String(100),
        nullable=True
    )

    release_date = db.Column(
        db.Date,
        nullable=True
    )

    is_maintained = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    is_eol = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    eol_date = db.Column(
        db.Date,
        nullable=True
    )

    latest_version = db.Column(
        db.String(100),
        nullable=True
    )

    latest_release_date = db.Column(
        db.Date,
        nullable=True
    )

    external_id = db.Column(
        db.String(255),
        nullable=False
    )

    __table_args__ = (
        db.UniqueConstraint(
            "source",
            "external_id",
            name="uq_lifecycle_source_external_id"
        ),
    )

    def __repr__(self):
        return (
            f"<LifecycleRecord "
            f"{self.product} {self.version}>"
        )