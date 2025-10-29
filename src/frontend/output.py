"""
HTTP output abstraction layer.

Translates geneweb/lib/output.ml
Provides a clean interface for generating HTTP responses.
"""

from typing import Protocol, Optional
from enum import Enum
import sys


class HttpStatus(Enum):
    """HTTP status codes"""
    OK = 200
    MOVED_PERMANENTLY = 301
    FOUND = 302
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    CONFLICT = 409
    INTERNAL_SERVER_ERROR = 500
    SERVICE_UNAVAILABLE = 503


class OutputHandler(Protocol):
    """
    Protocol for HTTP output handling.
    Implementations can write to files, sockets, or buffers.
    """

    def status(self, http_status: HttpStatus) -> None:
        """Set HTTP status code"""
        ...

    def header(self, content: str) -> None:
        """Write HTTP header line"""
        ...

    def body(self, content: str) -> None:
        """Write HTTP response body content"""
        ...

    def flush(self) -> None:
        """Flush output buffer"""
        ...


class StandardOutputHandler:
    """
    Standard implementation writing to stdout.
    Used for CGI-style responses.
    """

    def __init__(self):
        self._status_sent = False
        self._headers_sent = False
        self._buffer = []

    def status(self, http_status: HttpStatus) -> None:
        """Set HTTP status code"""
        if self._status_sent:
            return
        status_line = f"Status: {http_status.value}\r\n"
        sys.stdout.write(status_line)
        self._status_sent = True

    def header(self, content: str) -> None:
        """Write HTTP header line"""
        if not content.endswith('\r\n'):
            content += '\r\n'
        sys.stdout.write(content)

    def body(self, content: str) -> None:
        """Write HTTP response body content"""
        if not self._headers_sent:
            # Blank line separates headers from body
            sys.stdout.write('\r\n')
            self._headers_sent = True
        sys.stdout.write(content)

    def flush(self) -> None:
        """Flush output buffer"""
        sys.stdout.flush()


class BufferedOutputHandler:
    """
    Buffered output handler for testing or memory operations.
    """

    def __init__(self):
        self.status_code: Optional[HttpStatus] = None
        self.headers: list[str] = []
        self.body_content: list[str] = []

    def status(self, http_status: HttpStatus) -> None:
        """Set HTTP status code"""
        self.status_code = http_status

    def header(self, content: str) -> None:
        """Write HTTP header line"""
        self.headers.append(content)

    def body(self, content: str) -> None:
        """Write HTTP response body content"""
        self.body_content.append(content)

    def flush(self) -> None:
        """No-op for buffered handler"""
        pass

    def get_response(self) -> str:
        """Get complete HTTP response as string"""
        lines = []
        if self.status_code:
            lines.append(f"HTTP/1.1 {self.status_code.value} {self.status_code.name}")
        lines.extend(self.headers)
        lines.append("")  # Blank line
        lines.extend(self.body_content)
        return "\n".join(lines)


class Output:
    """
    Main output interface for templates.
    Wraps OutputHandler and provides convenience methods.

    Translates the output functions from geneweb/lib/output.ml
    """

    def __init__(self, handler: OutputHandler):
        self.handler = handler

    def set_status(self, status: HttpStatus) -> None:
        """Set HTTP status code"""
        self.handler.status(status)

    def write_header(self, fmt: str, *args) -> None:
        """Write formatted header"""
        content = fmt % args if args else fmt
        self.handler.header(content)

    def write(self, content: str) -> None:
        """Write body content (safe, no escaping)"""
        self.handler.body(content)

    def write_escaped(self, content: str) -> None:
        """Write HTML-escaped body content"""
        escaped = (content
                   .replace('&', '&amp;')
                   .replace('<', '&lt;')
                   .replace('>', '&gt;')
                   .replace('"', '&quot;')
                   .replace("'", '&#39;'))
        self.handler.body(escaped)

    def printf(self, fmt: str, *args) -> None:
        """Write formatted body content"""
        content = fmt % args if args else fmt
        self.handler.body(content)

    def flush(self) -> None:
        """Flush output - MUST be called at end of response"""
        self.handler.flush()
