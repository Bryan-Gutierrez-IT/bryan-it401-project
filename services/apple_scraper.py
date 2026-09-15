import requests
from bs4 import BeautifulSoup


APPLE_SECURITY_URL = "https://support.apple.com/en-us/100100"


def get_apple_security_updates():
    """
    Scrape Apple's Security Releases page.

    Returns recent macOS security/update records containing:
    - update name
    - available-for information
    - release date
    - information link, when available
    """

    try:
        response = requests.get(
            APPLE_SECURITY_URL,
            timeout=15,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 "
                    "BryghtCentral-IT401-Student-Project"
                )
            }
        )

        if response.status_code != 200:
            return {
                "success": False,
                "error": (
                    "Apple security page request failed "
                    f"with status code {response.status_code}."
                ),
                "source_url": APPLE_SECURITY_URL,
                "results": []
            }

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        # Find tables on Apple's page
        tables = soup.find_all("table")

        if not tables:
            return {
                "success": False,
                "error": (
                    "No security update table could be found "
                    "on Apple's webpage."
                ),
                "source_url": APPLE_SECURITY_URL,
                "results": []
            }

        updates = []

        # Search every table so the scraper is not dependent
        # on the security table always being the first table.
        for table in tables:

            rows = table.find_all("tr")

            for row in rows:

                cells = row.find_all("td")

                # We expect:
                # column 1 = update name
                # column 2 = available for
                # column 3 = release date
                if len(cells) < 3:
                    continue

                update_name = cells[0].get_text(
                    " ",
                    strip=True
                )

                available_for = cells[1].get_text(
                    " ",
                    strip=True
                )

                release_date = cells[2].get_text(
                    " ",
                    strip=True
                )

                # We only want macOS-related records.
                if "macos" not in update_name.lower():
                    continue

                link_element = cells[0].find("a")

                information_link = None

                if link_element:
                    information_link = link_element.get(
                        "href"
                    )

                    # Apple's links may sometimes be relative.
                    if (
                        information_link
                        and information_link.startswith("/")
                    ):
                        information_link = (
                            "https://support.apple.com"
                            + information_link
                        )

                updates.append({
                    "update_name": update_name,
                    "available_for": available_for,
                    "release_date": release_date,
                    "information_link": information_link
                })

        if not updates:
            return {
                "success": True,
                "error": None,
                "source_url": APPLE_SECURITY_URL,
                "results": [],
                "message": (
                    "No recent macOS security releases "
                    "were found."
                )
            }

        return {
            "success": True,
            "error": None,
            "source_url": APPLE_SECURITY_URL,
            "results": updates,
            "message": None
        }

    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": (
                "The Apple security webpage request "
                "timed out."
            ),
            "source_url": APPLE_SECURITY_URL,
            "results": []
        }

    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "error": (
                "Could not connect to Apple's "
                "security webpage."
            ),
            "source_url": APPLE_SECURITY_URL,
            "results": []
        }

    except requests.exceptions.RequestException:
        return {
            "success": False,
            "error": (
                "An error occurred while retrieving "
                "Apple security information."
            ),
            "source_url": APPLE_SECURITY_URL,
            "results": []
        }