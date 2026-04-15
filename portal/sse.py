import json
import time
import logging
from django.http import StreamingHttpResponse, JsonResponse
from django.utils import timezone
from .publishers import get_redis

logger = logging.getLogger(__name__)

HEARTBEAT_INTERVAL = 15  # seconds


def _format_sse(event, data):
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _stream_events(tenant_id, ticket_id=None):
    """
    Subscribe to Redis pub/sub channels and yield SSE messages as they arrive.

    Subscribed channels:
      - portal:events:<tenant_id>                       (all tenant events)
      - portal:events:<tenant_id>:ticket:<ticket_id>   (only if ticket_id given)
    """
    r = get_redis()
    pubsub = r.pubsub(ignore_subscribe_messages=True)

    channels = [f"portal:events:{tenant_id}"]
    if ticket_id:
        channels.append(f"portal:events:{tenant_id}:ticket:{ticket_id}")

    pubsub.subscribe(*channels)
    logger.info(f"SSE client subscribed to: {channels}")

    last_heartbeat = time.time()

    try:
        while True:
            message = pubsub.get_message()

            if message and message.get("type") == "message":
                try:
                    payload = json.loads(message["data"])
                    yield _format_sse(payload["event"], payload["data"])
                except (json.JSONDecodeError, KeyError) as e:
                    logger.error(f"Malformed Redis message: {e}")

            # Heartbeat to keep the HTTP connection alive
            if time.time() - last_heartbeat >= HEARTBEAT_INTERVAL:
                yield _format_sse("heartbeat", {"timestamp": timezone.now().isoformat()})
                last_heartbeat = time.time()

            time.sleep(0.05)  # 50ms poll — keeps CPU low without blocking

    except GeneratorExit:
        logger.info(f"SSE client disconnected from: {channels}")
    except Exception as e:
        logger.error(f"SSE stream error: {e}")
        yield _format_sse("error", {"message": "Internal stream error."})
    finally:
        pubsub.unsubscribe()
        pubsub.close()


def TicketStreamView(request):
    """
    GET /portal/stream?tenant_id=<tenant_id>
    GET /portal/stream?tenant_id=<tenant_id>&ticket_id=<ticket_id>

    Streams real-time events over SSE (Server-Sent Events) backed by Redis pub/sub.

    Events:
      ticket_created  : new ticket opened
      ticket_status   : ticket status changed
      new_comment     : comment posted on a ticket
      sla_breach      : SLA deadline breached
      heartbeat       : keep-alive ping every 15s
      error           : stream error
    """
    tenant_id = getattr(request, "tenant_id", None)
    if not tenant_id:
        return JsonResponse({"error": "tenant_id is required."}, status=400)

    ticket_id_param = request.GET.get("ticket_id")
    ticket_id = int(ticket_id_param) if ticket_id_param and ticket_id_param.isdigit() else None

    response = StreamingHttpResponse(
        _stream_events(tenant_id, ticket_id),
        content_type="text/event-stream",
    )
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"   # Disable Nginx buffering
    return response
    