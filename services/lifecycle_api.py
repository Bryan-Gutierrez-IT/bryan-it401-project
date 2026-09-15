import requests


BASE_URL = "https://endoflife.date/api/v1/products"


SUPPORTED_PRODUCTS = {
    "macos": "macos",
    "mac": "macos",
    "mac os": "macos",
    "chrome": "chrome",
    "google chrome": "chrome"
}


def get_lifecycle_data(product):
    """
    Retrieve lifecycle information from endoflife.date.

    Supported examples:
    macos
    chrome
    """

    product = product.strip().lower()

    if not product:
        return {
            "success": False,
            "error": "Please enter a product name.",
            "product": None,
            "results": []
        }

    api_product = SUPPORTED_PRODUCTS.get(product)

    if not api_product:
        return {
            "success": False,
            "error": (
                "That product is not currently supported. "
                "Try 'macOS' or 'Chrome'."
            ),
            "product": product,
            "results": []
        }

    url = f"{BASE_URL}/{api_product}/"

    try:
        response = requests.get(
            url,
            timeout=15,
            headers={
                "User-Agent": "BryghtCentral-IT401-Student-Project"
            }
        )

        if response.status_code == 404:
            return {
                "success": False,
                "error": "Lifecycle information was not found.",
                "product": product,
                "results": []
            }

        if response.status_code != 200:
            return {
                "success": False,
                "error": (
                    f"Lifecycle API request failed with "
                    f"status code {response.status_code}."
                ),
                "product": product,
                "results": []
            }

        data = response.json()

        result = data.get("result", {})

        releases = result.get("releases", [])

        lifecycle_results = []

        for release in releases:
            latest = release.get("latest", {}) or {}

            has_latest_details = bool(latest)

            lifecycle_results.append({
                "version": release.get("name", "Unknown"),
                "codename": release.get("codename"),
                "label": release.get("label"),
                "release_date": release.get("releaseDate"),
                "is_eol": release.get("isEol"),
                "eol_date": release.get("eolFrom"),
                "is_maintained": release.get("isMaintained"),

                # Some products, such as macOS, provide
                # a separate latest patch/version object.
                # Chrome does not track releases this way.
                "has_latest_details": has_latest_details,

                "latest_version": (
                    latest.get("name")
                    if has_latest_details
                    else None
                ),

                "latest_release_date": (
                    latest.get("date")
                    if has_latest_details
                    else None
                )
            })

        if not lifecycle_results:
            return {
                "success": True,
                "error": None,
                "product": result.get("label", product),
                "results": [],
                "message": "No lifecycle releases were found."
            }

        return {
            "success": True,
            "error": None,
            "product": result.get("label", product),
            "results": lifecycle_results,
            "message": None
        }

    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "The lifecycle API request timed out.",
            "product": product,
            "results": []
        }

    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "error": "Could not connect to the lifecycle API.",
            "product": product,
            "results": []
        }

    except requests.exceptions.RequestException:
        return {
            "success": False,
            "error": "An error occurred while requesting lifecycle data.",
            "product": product,
            "results": []
        }

    except ValueError:
        return {
            "success": False,
            "error": "The lifecycle API returned unreadable data.",
            "product": product,
            "results": []
        }