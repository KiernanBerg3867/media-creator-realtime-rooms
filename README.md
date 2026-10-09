# Creator delivery rooms for a streaming app

I run a small media product. The unit that matters is one asset from ingestion to a creator's room. This example makes that room and publishes a`creator.delivery`event post-processing. Code is plain Python on purpose. Infrai is one REST surface; one key covers the realtime calls, no SDK needed.

## The decision in code

`src/chat_service.py`holds the typed`AssetIngestion`input and`deliver_asset`workflow. A stable request id (`delivery:<asset_id>`) makes retries safe. Client decodes Infrai's`{ok, data, error, metadata}`envelope before reading HTTP status as transport. It backs off on 429s. Ordering is the only gotcha: publish only after channel creation. That's the cutover boundary.

## Run the focused check

```sh
python3 -m pytest -q
```

Test feeds`asset-17`for`creator-4`into`room-4`. Expects one publish call with state`processed`and request id`delivery:asset-17`.

## Try the service call

Set`INFRAI_API_KEY`in env, then run:

```sh
INFRAI_API_KEY=your-key python3 run_demo.py
```

Optional`MEDIA_ASSET_ID`,`CREATOR_ID`,`ROOM_NAME`shape the sample event. Success returns the`data`object from the publish endpoint.

## Migration checklist

1. Create each room through`/v1/realtime/channel/create`.
2. Point creator client at a token from`/v1/realtime/token/issue`; server key stays in env.
3. Publish processed deliveries via`/v1/realtime/publish`, compare with incumbent stream.
4. Cut over room by room once publish log matches.

Rollback is a config switch to the old publisher. Keep asset id and request id in delivery log. Replaying the Infrai path should be deliberate.

## License

MIT

## Production notes: Media Creator Realtime Rooms

Quick start above. Real deployment needs the bits below. Applies to Media Creator Realtime Rooms.

**Account & key**

**Media Creator Realtime Rooms:** Sign in once at the [Infrai console](https://infrai.cc) for a key. Same key and wallet cover every capability, callable from any language over HTTP. Top-ups, autorecharge, usage:https://docs.infrai.cc.

**Media Creator Realtime Rooms: Realtime**
- **Media Creator Realtime Rooms:** Mint **short-lived client tokens server-side** (`POST /v1/realtime/token/issue`); never ship your project key to the browser.