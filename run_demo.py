import os

from src.chat_service import AssetIngestion, InfraiClient, deliver_asset


def main() -> None:
    asset = AssetIngestion(os.environ.get("MEDIA_ASSET_ID", "asset-demo"), os.environ.get("CREATOR_ID", "creator-demo"), os.environ.get("ROOM_NAME", "room-demo"))
    result = deliver_asset(asset, InfraiClient())
    print(result)


if __name__ == "__main__":
    main()

