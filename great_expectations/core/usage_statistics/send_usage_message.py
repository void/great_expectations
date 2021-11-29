from typing import Optional


def send_usage_message_with_handler(
    handler,
    event: str,
    event_payload: Optional[dict] = None,
    success: Optional[bool] = None,
):
    # helper method used to send a message when we have the handler directly
    print("HELLO WORLD")
    try:
        message: dict = {
            "event": event,
            "event_payload": event_payload,
            "success": success,
        }
        if handler is not None:
            handler.emit(message)
    except Exception:
        pass


def send_usage_message(
    data_context,
    event: str,
    event_payload: Optional[dict] = None,
    success: Optional[bool] = None,
):
    """send a usage statistics message."""
    # noinspection PyBroadException
    try:
        # DataContext level object
        # this is all possible at the DataContext level.
        handler = getattr(data_context, "_usage_statistics_handler", None)
        message: dict = {
            "event": event,
            "event_payload": event_payload,
            "success": success,
        }
        if handler is not None:
            handler.emit(message)
    except Exception:
        pass
