import os
from urllib.parse import quote_plus

from dotenv import load_dotenv
from flask import Flask

from extensions import db, migrate
from routes.main import register_routes
from routes.lifecycle_records import register_lifecycle_routes

load_dotenv()


def create_app():

    app = Flask(__name__)
    
    app.config["SECRET_KEY"] = os.getenv(
        "SECRET_KEY",
        "dev-secret-key"
    )

    db_username = os.getenv("DB_USERNAME")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv(
        "DB_HOST",
        "127.0.0.1"
    )
    db_port = os.getenv(
        "DB_PORT",
        "3307"
    )
    db_name = os.getenv("DB_NAME")

    required_values = {
        "DB_USERNAME": db_username,
        "DB_PASSWORD": db_password,
        "DB_NAME": db_name
    }

    missing_values = [
        key
        for key, value
        in required_values.items()
        if not value
    ]

    if missing_values:
        raise RuntimeError(
            "Missing required database "
            "environment variables: "
            + ", ".join(missing_values)
        )

    database_uri = (
        "mysql+pymysql://"
        f"{quote_plus(db_username)}:"
        f"{quote_plus(db_password)}@"
        f"{db_host}:"
        f"{db_port}/"
        f"{quote_plus(db_name)}"
    )

    app.config[
        "SQLALCHEMY_DATABASE_URI"
    ] = database_uri

    app.config[
        "SQLALCHEMY_TRACK_MODIFICATIONS"
    ] = False

    db.init_app(app)

    migrate.init_app(
        app,
        db
    )

    register_routes(app)
    register_lifecycle_routes(app)
    # Import models so SQLAlchemy and
    # Flask-Migrate can discover them.
    from models import LifecycleRecord

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)