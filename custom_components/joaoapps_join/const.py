"""Constants for Joaoapps Join."""

DOMAIN = "joaoapps_join"

CONF_DEVICE_IDS = "device_ids"
CONF_DEVICE_NAMES = "device_names"

# Services are registered per config entry as "<name>_<suffix>" (same naming
# the YAML version used), e.g. joaoapps_join.kitchen_ring
SERVICE_SUFFIXES = (
    "ring",
    "set_wallpaper",
    "send_sms",
    "send_file",
    "send_url",
    "send_tasker",
)

# Core's dev branch moved from voluptuous to probatio; support either.
try:
    import voluptuous as vol
except ImportError:  # pragma: no cover
    import probatio as vol  # type: ignore[no-redef]

__all__ = [
    "CONF_DEVICE_IDS",
    "CONF_DEVICE_NAMES",
    "DOMAIN",
    "SERVICE_SUFFIXES",
    "vol",
]
