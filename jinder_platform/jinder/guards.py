"""Who is calling, and may they do this? Every check runs on the server (Feature 1 AC7)."""
import sqlite3

from . import store
from .http_server import Ctx
from .util import ApiError


def current_user(ctx: Ctx):
    """The signed-in user row, or None. The result is cached for the request."""
    if ctx.user_cache is None:
        ctx.user_cache = store.user_for_token(ctx.conn, ctx.token) or False
    return ctx.user_cache or None


def require_user(ctx: Ctx) -> sqlite3.Row:
    user = current_user(ctx)
    if not user:
        raise ApiError(401, "UNAUTHORIZED", "Your session has ended. Sign in again.")
    return user


def require_role(ctx: Ctx, role: str) -> sqlite3.Row:
    user = require_user(ctx)
    if user["role"] != role:
        raise ApiError(403, "FORBIDDEN", "You don't have access to this.")
    return user
