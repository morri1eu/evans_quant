import logging


class LoggerAdapter(logging.LoggerAdapter):
    """Add connection ID and client IP address to websockets logs."""

    def process(self, msg, kwargs):
        try:
            websocket = kwargs["extra"]["websocket"]
        except KeyError:
            return msg, kwargs
        kwargs["extra"]["event_data"] = {
            "connection_id": str(websocket.id),
            "remote_addr": websocket.request_headers.get("X-Forwarded-For"),
        }
        return msg, kwargs
