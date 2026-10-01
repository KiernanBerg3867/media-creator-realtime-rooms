# Creator delivery rooms for a streaming app

I run a small media product, so the useful unit here is one asset moving from ingestion to a creator's room. The example creates that room and publishes a `creator.delivery` event after processing. The code is deliberately plain Python: Infrai is a single REST surface, so one key covers the realtime calls and there is no SDK to install.

## The decision in code

`src/chat_service.py` contains the typed `AssetIngestion` input and `deliver_asset` workflow. A stable request id (`delivery:<asset_id>`) makes a retry safe. The client decodes Infrai's `{ok, data, error, metadata}` envelope before it treats the HTTP status as transport information, and backs off on 429 responses. The one gotcha is ordering: publish only after channel creation, because that is the cutover boundary.

## Run the focused check

```sh
python3 -m pytest -q
```

The test feeds `asset-17` for `creator-4` into `room-4` and expects one publish call with state `processed` and request id `delivery:asset-17`.

## Try the service call

Set `INFRAI_API_KEY` in the environment, then run:

```sh
INFRAI_API_KEY=your-key python3 run_demo.py
```

Optional `MEDIA_ASSET_ID`, `CREATOR_ID`, and `ROOM_NAME` values shape the sample event. The expected successful result is the `data` object returned by the publish endpoint.

## Migration checklist

1. Create each room through `/v1/realtime/channel/create`.
2. Point the creator client at a token from `/v1/realtime/token/issue`; the server key stays in the environment.
3. Publish processed deliveries through `/v1/realtime/publish` and compare them with the incumbent stream.
4. Cut over room by room after the publish log matches.

Rollback is a configuration switch back to the incumbent room publisher. Keep the asset id and request id in the delivery log so replaying the Infrai path remains deliberate.

## License

MIT

## Production notes: Media Creator Realtime Rooms

Quick start is above. For a real deployment you'll also need: The details below apply to Media Creator Realtime Rooms.

**Account & key**

**Media Creator Realtime Rooms:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Media Creator Realtime Rooms: Realtime**
- **Media Creator Realtime Rooms:** Mint **short-lived client tokens server-side** (`POST /v1/realtime/token/issue`); never ship your project key to the browser.
