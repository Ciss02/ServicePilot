"""Controlli browser centralizzati per tutte le pagine e le API."""

import time
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable
from threading import Lock
from urllib.parse import urlsplit

from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import PlainTextResponse

SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})
LOGIN_PATHS = frozenset({"/login", "/auth/login"})
SENSITIVE_PATH_PREFIXES = ("/app", "/auth", "/tickets", "/login", "/logout")
CONTENT_SECURITY_POLICY = "; ".join(
    (
        "default-src 'self'",
        "base-uri 'self'",
        "form-action 'self'",
        "frame-ancestors 'none'",
        "object-src 'none'",
        "script-src 'none'",
        "style-src 'self'",
        "img-src 'self' data:",
        "font-src 'self'",
        "connect-src 'self'",
    )
)


def _normalized_origin(value: str) -> tuple[str, str, int | None] | None:
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        return None
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return None
    default_port = 443 if parsed.scheme == "https" else 80
    return parsed.scheme, parsed.hostname.casefold(), port or default_port


def _request_origin(request: Request) -> tuple[str, str, int | None] | None:
    return _normalized_origin(str(request.base_url))


def request_has_valid_origin(request: Request) -> bool:
    """Accetta invii browser solo quando Origin o Referer coincidono con il portale."""

    supplied_origin = request.headers.get("origin")
    if supplied_origin is not None:
        return _normalized_origin(supplied_origin) == _request_origin(request)

    supplied_referer = request.headers.get("referer")
    if supplied_referer is not None:
        return _normalized_origin(supplied_referer) == _request_origin(request)

    # Client REST e test automatici possono non inviare entrambi gli header. Un form
    # ostile eseguito da un browser moderno invia invece Origin e viene controllato.
    return True


class LoginAttemptLimiter:
    """Limita il lavoro costoso di verifica password per singolo client."""

    def __init__(
        self,
        attempts_per_minute: int,
        *,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if attempts_per_minute < 1:
            raise ValueError("attempts_per_minute deve essere almeno 1")
        self._attempts_per_minute = attempts_per_minute
        self._clock = clock
        self._attempts: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def allow(self, client_key: str) -> bool:
        """Registra il tentativo e indica se pu\u00f2 proseguire."""

        now = self._clock()
        boundary = now - 60
        with self._lock:
            attempts = self._attempts[client_key]
            while attempts and attempts[0] <= boundary:
                attempts.popleft()
            if len(attempts) >= self._attempts_per_minute:
                return False
            attempts.append(now)
            return True


class BrowserSecurityMiddleware(BaseHTTPMiddleware):
    """Blocca invii cross-site e aggiunge protezioni uniformi alle risposte."""

    def __init__(
        self,
        app,
        *,
        enable_hsts: bool = False,
        login_attempts_per_minute: int = 10,
    ) -> None:
        super().__init__(app)
        self._enable_hsts = enable_hsts
        self._login_limiter = LoginAttemptLimiter(login_attempts_per_minute)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if request.method not in SAFE_METHODS and not request_has_valid_origin(request):
            response: Response = PlainTextResponse(
                "Origine della richiesta non consentita.",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        elif (
            request.method == "POST"
            and request.url.path in LOGIN_PATHS
            and not self._login_limiter.allow(
                request.client.host if request.client is not None else "unknown"
            )
        ):
            response = PlainTextResponse(
                "Troppi tentativi di accesso. Riprova tra un minuto.",
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                headers={"Retry-After": "60"},
            )
        else:
            response = await call_next(request)

        response.headers.setdefault("Content-Security-Policy", CONTENT_SECURITY_POLICY)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Permissions-Policy", "camera=(), microphone=(), geolocation=()"
        )
        response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        if request.url.path.startswith(SENSITIVE_PATH_PREFIXES):
            response.headers.setdefault("Cache-Control", "no-store")
        if self._enable_hsts:
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000")
        return response
