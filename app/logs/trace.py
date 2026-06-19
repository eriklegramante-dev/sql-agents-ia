from contextvars import ContextVar

trace_id_ctx: ContextVar[str] = ContextVar("trace_id_ctx", default=None)


def set_trace_id(trace_id: str):
    """
    Store the current trace identifier in context.

    Args:
        trace_id (str): Unique trace identifier for the request.
    """
    trace_id_ctx.set(trace_id)


def get_trace_id() -> str:
    """
    Retrieve the current trace identifier from context.

    Returns:
        str: Current trace identifier.
    """
    return trace_id_ctx.get()
