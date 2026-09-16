"""Global configuration variables and environment settings for MT5Bridge."""

import os
import secrets

LOGLEVEL = os.environ.get("LOGLEVEL", "INFO").upper()

# Security config
SECURITY_ENABLED = os.environ.get("SECURITY_ENABLED", "true").lower() in (
    "true",
    "1",
    "t",
    "yes",
    "on",
)
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", secrets.token_urlsafe(32))
JWT_EXPIRE = int(os.environ.get("JWT_EXPIRE", 3600))
JWT_AUD = os.environ.get("JWT_AUD", "mt5bridge")

# API Key config
API_KEY = os.environ.get("API_KEY", None)
