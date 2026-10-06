import os
import sys

# Ensure root directory is in sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from main import app as fastapi_app


class VercelPathMiddleware:
    """
    ASGI middleware that restores original request path on Vercel deployments.
    When Vercel rewrites requests to /api/index.py, this middleware inspects
    Vercel routing headers (x-matched-path, x-forwarded-uri, etc.) to set
    scope['path'] to the originally requested endpoint.
    """
    def __init__(self, asgi_app):
        self.asgi_app = asgi_app

    async def __call__(self, scope, receive, send):
        if scope.get("type") == "http":
            headers = dict(scope.get("headers", []))
            for hdr in [b"x-matched-path", b"x-forwarded-uri", b"x-vercel-matched-path", b"x-original-uri"]:
                raw = headers.get(hdr)
                if raw:
                    path_str = raw.decode("utf-8", errors="ignore").split("?")[0]
                    if path_str and not path_str.endswith(".py"):
                        scope["path"] = path_str
                        break
        await self.asgi_app(scope, receive, send)


app = VercelPathMiddleware(fastapi_app)
