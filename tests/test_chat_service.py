from src.chat_service import AssetIngestion, InfraiClient, deliver_asset


class RecordingClient:
    def __init__(self):
        self.calls = []

    def create_channel(self, channel):
        self.calls.append(("create", channel))

    def publish(self, channel, event, data, account_id, request_id):
        self.calls.append(("publish", channel, event, data, account_id, request_id))
        return {"published": True}


def test_processed_asset_is_delivered_once_with_stable_request_id():
    client = RecordingClient()
    result = deliver_asset(AssetIngestion("asset-17", "creator-4", "room-4"), client)
    assert result == {"published": True}
    assert client.calls[0] == ("create", "room-4")
    assert client.calls[1][-1] == "delivery:asset-17"
    assert client.calls[1][3]["state"] == "processed"


def test_create_channel_omits_default_type_and_preserves_explicit_type():
    client = InfraiClient(api_key="test")
    requests = []
    client._post = lambda path, payload, request_id: requests.append((path, payload, request_id))

    client.create_channel("room-4")
    client.create_channel("room-5", channel_type="custom")

    assert requests[0] == ("/v1/realtime/channel/create", {"channel": "room-4", "vendor": "pusher"}, "channel:room-4")
    assert requests[1][1]["type"] == "custom"
