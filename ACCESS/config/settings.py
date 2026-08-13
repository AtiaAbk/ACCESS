import os

from dotenv import load_dotenv


# Load environment variables from .env
load_dotenv()


# =========================
# ACCESS Application Config
# =========================

APP_NAME = "ACCESS"

APP_FULL_NAME = (
    "Adaptive Cognitive Companion for Efficient System Services"
)

VERSION = "1.0"

ENVIRONMENT = os.getenv(
    "ACCESS_ENV",
    "development"
)

DEBUG = os.getenv(
    "ACCESS_DEBUG",
    "false"
).lower() == "true"


# =========================
# System Configuration
# =========================

SUPPORTED_PLATFORMS = [
    "Windows",
    "macOS",
    "Linux",
]

DEFAULT_MODE = "offline-first"
