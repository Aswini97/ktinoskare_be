# telemetry/middleware.py
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
import jwt
from django.conf import settings

class JWTAuthMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        query_string = scope.get("query_string", b"").decode()
        token = dict(x.split("=") for x in query_string.split("&") if "=" in x).get("token")
        
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            scope["user"] = await get_user(payload["user_id"])
        except Exception:
            scope["user"] = AnonymousUser()
            
        return await self.app(scope, receive, send)