"""Support for Join notifications."""

from __future__ import annotations

import logging
from typing import Any, override

from pyjoin import get_devices, send_notification

from homeassistant.components.notify import (
    ATTR_DATA,
    ATTR_TITLE,
    ATTR_TITLE_DEFAULT,
    PLATFORM_SCHEMA as NOTIFY_PLATFORM_SCHEMA,
    BaseNotificationService,
)
from homeassistant.const import CONF_API_KEY, CONF_DEVICE_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import CONF_DEVICE_IDS, CONF_DEVICE_NAMES, vol

_LOGGER = logging.getLogger(__name__)

# Kept so existing `notify: - platform: joaoapps_join` YAML keeps working.
PLATFORM_SCHEMA = NOTIFY_PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_API_KEY): cv.string,
        vol.Optional(CONF_DEVICE_ID): cv.string,
        vol.Optional(CONF_DEVICE_IDS): cv.string,
        vol.Optional(CONF_DEVICE_NAMES): cv.string,
    }
)


def get_service(
    hass: HomeAssistant,
    config: ConfigType,
    discovery_info: DiscoveryInfoType | None = None,
) -> JoinNotificationService | None:
    """Get the Join notification service."""
    if discovery_info and (entry_id := discovery_info.get("entry_id")):
        # Created from a config entry
        entry = hass.config_entries.async_get_entry(entry_id)
        if entry is None:
            return None
        conf = entry.data
        return JoinNotificationService(
            conf[CONF_API_KEY],
            conf.get(CONF_DEVICE_ID),
            conf.get(CONF_DEVICE_IDS),
            conf.get(CONF_DEVICE_NAMES),
        )

    # Legacy YAML path
    api_key = config.get(CONF_API_KEY)
    device_id = config.get(CONF_DEVICE_ID)
    device_ids = config.get(CONF_DEVICE_IDS)
    device_names = config.get(CONF_DEVICE_NAMES)
    if api_key and not get_devices(api_key):
        _LOGGER.error("Error connecting to Join. Check the API key")
        return None
    if device_id is None and device_ids is None and device_names is None:
        _LOGGER.error(
            "No device was provided. Please specify device_id"
            ", device_ids, or device_names"
        )
        return None
    return JoinNotificationService(api_key, device_id, device_ids, device_names)


class JoinNotificationService(BaseNotificationService):
    """Implement the notification service for Join."""

    def __init__(self, api_key, device_id, device_ids, device_names):
        """Initialize the service."""
        self._api_key = api_key
        self._device_id = device_id
        self._device_ids = device_ids
        self._device_names = device_names

    @override
    def send_message(self, message: str = "", **kwargs: Any) -> None:
        """Send a message to a user."""
        title = kwargs.get(ATTR_TITLE, ATTR_TITLE_DEFAULT)
        data = kwargs.get(ATTR_DATA) or {}
        send_notification(
            device_id=self._device_id,
            device_ids=self._device_ids,
            device_names=self._device_names,
            text=message,
            title=title,
            icon=data.get("icon"),
            smallicon=data.get("smallicon"),
            image=data.get("image"),
            sound=data.get("sound"),
            notification_id=data.get("notification_id"),
            category=data.get("category"),
            url=data.get("url"),
            tts=data.get("tts"),
            tts_language=data.get("tts_language"),
            vibration=data.get("vibration"),
            actions=data.get("actions"),
            api_key=self._api_key,
        )
