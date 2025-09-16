from fastapi import FastAPI, Request
import fcm_client

app = FastAPI()

@app.post("/_matrix/push/v1/notify")
async def notify(request: Request):
    """
    Accept Matrix homeserver/Sygnal-style payloads,
    extract relevant fields, and forward to FCM.
    """

    payload = await request.json()
    notif = payload.get("notification", {})

    devices = notif.get("devices", [])
    if not devices:
        return {"status": 400, "error": "No devices in payload"}

    device_token = devices[0].get("pushkey")

    room_name = notif.get("room_name", "Matrix Room")
    body = notif.get("content", {}).get("body", "New message")

    data = {
        "room_id": notif.get("room_id", ""),
        "room_alias": notif.get("room_alias", ""),
        "event_id": notif.get("event_id", ""),
        "sender": notif.get("sender", ""),
        "sender_display_name": notif.get("sender_display_name", ""),
        "msgtype": notif.get("content", {}).get("msgtype", ""),
        "unread": str(notif.get("counts", {}).get("unread", 0)),
        "missed_calls": str(notif.get("counts", {}).get("missed_calls", 0)),
        "prio": notif.get("prio", "normal"),
        "type": notif.get("type", ""),
    }

    if(notif.get("type") == "m.text" and notif.get("content", {}).get("body", "") != ""):
        data["body"] = notif.get("content", {}).get("body", "")

    status, resp_text = fcm_client.send_push(
        device_token=device_token,
        title=room_name,
        body=body,
        data=data,
    )

    return {"status": status, "response": resp_text}

@app.post("/gmail/push/v1/notify")
async def gmail_notify(request: Request):
    """
    Accept Gmail webhook payloads, forward to FCM.
    """
    payload = await request.json()

    notif = payload.get("notification", {})
    data = payload.get("data", {})

    # You should include the Gmail user's device token in data
    device_token = data.get("device_token")
    if not device_token:
        return {"status": 400, "error": "Missing device_token in payload"}

    title = notif.get("title", "New Email")
    body = notif.get("body", "You have a new email")

    status, resp_text = fcm_client.send_push(
        device_token=device_token,
        title=title,
        body=body,
        data=data,
    )

    return {"status": status, "response": resp_text}