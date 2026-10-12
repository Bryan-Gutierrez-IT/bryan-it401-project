from app import app
from services.lifecycle_persistence import (
    sync_lifecycle_records
)


with app.app_context():

    print("Syncing macOS...")
    mac_result = sync_lifecycle_records(
        "macOS"
    )
    print(mac_result)

    print()

    print("Syncing Chrome...")
    chrome_result = sync_lifecycle_records(
        "Chrome"
    )
    print(chrome_result)