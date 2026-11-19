"""HTTP requests shared by the Tkinter window and the report helper."""

import json
import socket
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen


BASE_URL = "http://127.0.0.1:5050"


class RequestError(Exception):
    """An error message that can be displayed to the user."""


def request_json(path, fields=None):
    # urlopen uses GET without a body. Even an empty byte body selects POST.
    body = None if fields is None else urlencode(fields).encode("utf-8")
    try:
        with urlopen(BASE_URL + path, data=body, timeout=5) as reply:
            return json.loads(reply.read().decode("utf-8"))
    except HTTPError as error:
        with error:
            try:
                message = json.loads(error.read().decode("utf-8"))["error"]
            except (ValueError, KeyError, TypeError):
                message = f"The server returned HTTP {error.code}."
        raise RequestError(message) from error
    except (URLError, socket.timeout, ConnectionError) as error:
        if isinstance(getattr(error, "reason", error), socket.timeout):
            raise RequestError("The server timed out. Refresh the list and try again.") from error
        raise RequestError("Cannot reach Flask. Start server.py, then try again.") from error
    except ValueError as error:
        raise RequestError("Flask returned an unreadable reply. Try refreshing.") from error
