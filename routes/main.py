import json
import os

from flask import render_template, request

from services.lifecycle_api import get_lifecycle_data
from services.apple_scraper import get_apple_security_updates


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

        search_query = request.args.get(
            "q",
            ""
        ).strip().lower()

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


    @app.route("/support-intelligence")
    def support_intelligence():

        # Get the selected product from the URL.
        product = request.args.get(
            "product",
            "macOS"
        ).strip()

        # Get the selected version from the URL.
        requested_version = request.args.get(
            "version",
            ""
        ).strip()

        lifecycle_data = None
        apple_data = None

        selected_release = None
        selected_version = ""

        recommendation = None

        apple_updates_for_release = []

        if product:

            # -----------------------------------------
            # API DATA
            # -----------------------------------------

            lifecycle_data = get_lifecycle_data(
                product
            )


            # -----------------------------------------
            # SCRAPED APPLE DATA
            # Only relevant for macOS
            # -----------------------------------------

            if product.lower() in [
                "macos",
                "mac",
                "mac os"
            ]:

                apple_data = (
                    get_apple_security_updates()
                )


            # -----------------------------------------
            # FIND THE VERSION SELECTED BY THE USER
            # -----------------------------------------

            if (
                lifecycle_data
                and lifecycle_data.get("success")
                and lifecycle_data.get("results")
            ):

                releases = lifecycle_data["results"]


                # Try to find the version selected
                # by the user.
                if requested_version:

                    selected_release = next(
                        (
                            release
                            for release in releases
                            if str(
                                release.get(
                                    "version",
                                    ""
                                )
                            ).lower()
                            ==
                            requested_version.lower()
                        ),
                        None
                    )
                if requested_version and selected_release is None:

                    return render_template(
                        "support_intelligence.html",
                        product=product,
                        lifecycle_data=lifecycle_data,
                        apple_data=apple_data,
                        selected_release=None,
                        selected_version="",
                        recommendation=None,
                        apple_updates_for_release=[],
                        input_error=(
                            f"Version '{requested_version}' "
                            f"was not found for {product}."
                        )
                    )

                # If no version was selected,
                # or the version is invalid,
                # use the newest release.
                if selected_release is None:

                    selected_release = releases[0]


                selected_version = str(
                    selected_release.get(
                        "version",
                        ""
                    )
                )


                # -----------------------------------------
                # FIND NEWEST SUPPORTED RELEASE
                # -----------------------------------------

                latest_supported = next(
                    (
                        release
                        for release in releases
                        if release.get(
                            "is_maintained"
                        )
                        and not release.get(
                            "is_eol"
                        )
                    ),
                    None
                )


                # -----------------------------------------
                # CREATE BRYGHTCENTRAL RECOMMENDATION
                # -----------------------------------------

                selected_label = (
                    selected_release.get(
                        "label"
                    )
                    or selected_version
                )


                # Release is no longer supported
                if (
                    selected_release.get("is_eol")
                    or not selected_release.get(
                        "is_maintained"
                    )
                ):

                    if latest_supported:

                        upgrade_target = (
                            latest_supported.get(
                                "label"
                            )
                        )

                        message = (
                            f"{selected_label} is no longer "
                            f"receiving active support. "
                            f"Upgrade to {upgrade_target} "
                            f"if the device or application "
                            f"is compatible."
                        )

                    else:

                        message = (
                            f"{selected_label} is no longer "
                            f"receiving active support. "
                            f"Upgrade to a currently "
                            f"supported release."
                        )


                    recommendation = {
                        "level": "Upgrade Recommended",
                        "message": message
                    }


                # Release is still supported
                else:

                    if (
                        latest_supported
                        and selected_version
                        != str(
                            latest_supported.get(
                                "version",
                                ""
                            )
                        )
                    ):

                        newest_label = (
                            latest_supported.get(
                                "label"
                            )
                        )

                        message = (
                            f"{selected_label} is still "
                            f"maintained and receiving "
                            f"support. The newest supported "
                            f"release currently tracked is "
                            f"{newest_label}."
                        )

                    else:

                        message = (
                            f"{selected_label} is currently "
                            f"maintained and is the newest "
                            f"supported release tracked by "
                            f"BryghtCentral."
                        )


                    recommendation = {
                        "level": "Supported",
                        "message": message
                    }


                # -----------------------------------------
                # FILTER APPLE SCRAPED DATA
                #
                # Example:
                # macOS 13 -> Ventura updates
                # macOS 14 -> Sonoma updates
                # macOS 15 -> Sequoia updates
                # -----------------------------------------

                if (
                    apple_data
                    and apple_data.get("success")
                    and apple_data.get("results")
                    and selected_release
                ):

                    codename = (
                        selected_release.get(
                            "codename"
                        )
                        or ""
                    ).lower()

                    if codename:

                        for update in apple_data[
                            "results"
                        ]:

                            update_text = (
                                (
                                    update.get(
                                        "update_name",
                                        ""
                                    )
                                    + " "
                                    + update.get(
                                        "available_for",
                                        ""
                                    )
                                )
                                .lower()
                            )

                            if codename in update_text:

                                apple_updates_for_release.append(
                                    update
                                )


        return render_template(
            "support_intelligence.html",
            product=product,
            lifecycle_data=lifecycle_data,
            apple_data=apple_data,
            selected_release=selected_release,
            selected_version=selected_version,
            recommendation=recommendation,
            apple_updates_for_release=(
                apple_updates_for_release
            ),
            input_error=None
        )