import json
import os

from flask import render_template, request


def register_routes(app):

    @app.route("/")
    def index():
        return render_template("index.html")


    @app.route("/assets")
    def assets():

        data_path = os.path.join(
            app.root_path,
            "data",
            "assets.json"
        )

        with open(data_path, "r") as file:
            asset_data = json.load(file)

        search_query = request.args.get("q", "").strip().lower()

        if search_query:
            filtered_assets = []

            for asset in asset_data:
                searchable_text = " ".join(
                    str(value).lower()
                    for value in asset.values()
                )

                if search_query in searchable_text:
                    filtered_assets.append(asset)

            asset_data = filtered_assets

        return render_template(
            "assets.html",
            assets=asset_data,
            search_query=search_query
        )
