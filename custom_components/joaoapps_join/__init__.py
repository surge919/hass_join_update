"""Support for Joaoapps Join services (config-flow version)."""

from __future__ import annotations

import logging

from pyjoin import (
    ring_device,
    send_file,
    send_notification,
    send_sms,
    send_url,
    set_wallpaper,
)

from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_DEVICE_ID, CONF_NAME, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import discovery
from homeassistant.helpers.service import async_set_service_schema
from homeassistant.helpers.typing import ConfigType

from .const import CONF_DEVICE_IDS, CONF_DEVICE_NAMES, DOMAIN, SERVICE_SUFFIXES

_LOGGER = logging.getLogger(__name__)


SERVICE_FIELDS: dict[str, dict] = {
    "send_url": {
        "url": {
            "required": True,
            "example": "https://www.home-assistant.io",
            "selector": {"text": {}},
        }
    },
    "send_file": {
        "url": {"required": True, "selector": {"text": {}}},
    },
    "set_wallpaper": {
        "url": {"required": True, "selector": {"text": {}}},
    },
    "send_sms": {
        "number": {"required": True, "selector": {"text": {}}},
        "message": {"required": True, "selector": {"text": {"multiline": True}}},
    },
    "send_tasker": {
        "command": {"required": True, "selector": {"text": {}}},
    },
}


def _prefix(name: str | None) -> str:
    """Service name prefix, identical to the old YAML behaviour."""
    return f"{name.lower().replace(' ', '_')}_" if name else ""


def _notify_name(name: str | None) -> str:
    """Name of the legacy notify action (notify.<name>)."""
    return _prefix(name).rstrip("_") or DOMAIN


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Import any legacy `joaoapps_join:` YAML into config entries."""
    # Needed later so the notify platform is set up with the real config.
    hass.data[DOMAIN] = {"config": config}

    confs = config.get(DOMAIN) or []
    if isinstance(confs, dict):
        confs = [confs]
    for conf in confs:
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN, context={"source": SOURCE_IMPORT}, data=dict(conf)
            )
        )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Join from a config entry."""
    data = entry.data
    api_key = data[CONF_API_KEY]
    targets = {
        "device_id": data.get(CONF_DEVICE_ID),
        "device_ids": data.get(CONF_DEVICE_IDS),
        "device_names": data.get(CONF_DEVICE_NAMES),
    }
    name = data.get(CONF_NAME)
    prefix = _prefix(name)

    # Plain (non-async) handlers run in the executor, which is what we want
    # because pyjoin is blocking.
    def ring_service(call: ServiceCall) -> None:
        ring_device(api_key=api_key, **targets)

    def set_wallpaper_service(call: ServiceCall) -> None:
        set_wallpaper(api_key=api_key, url=call.data.get("url"), **targets)

    def send_file_service(call: ServiceCall) -> None:
        send_file(api_key=api_key, url=call.data.get("url"), **targets)

    def send_url_service(call: ServiceCall) -> None:
        send_url(api_key=api_key, url=call.data.get("url"), **targets)

    def send_tasker_service(call: ServiceCall) -> None:
        send_notification(api_key=api_key, text=call.data.get("command"), **targets)

    def send_sms_service(call: ServiceCall) -> None:
        send_sms(
            api_key=api_key,
            sms_number=call.data.get("number"),
            sms_text=call.data.get("message"),
            **targets,
        )

    handlers = {
        "ring": ring_service,
        "set_wallpaper": set_wallpaper_service,
        "send_sms": send_sms_service,
        "send_file": send_file_service,
        "send_url": send_url_service,
        "send_tasker": send_tasker_service,
    }
    for suffix, handler in handlers.items():
        hass.services.async_register(DOMAIN, f"{prefix}{suffix}", handler)
        # Names are per-entry, so services.yaml can't describe them; this
        # is what makes the fields show up in the UI.
        async_set_service_schema(
            hass,
            DOMAIN,
            f"{prefix}{suffix}",
            {"fields": SERVICE_FIELDS.get(suffix, {})},
        )

    # Legacy notify.<name> action, kept so `data:` (icon, sound, tts, ...)
    # and existing automations keep working.
    await discovery.async_load_platform(
        hass,
        Platform.NOTIFY,
        DOMAIN,
        {CONF_NAME: _notify_name(name), "entry_id": entry.entry_id},
        hass.data[DOMAIN]["config"],
    )

    entry.async_on_unload(entry.add_update_listener(_async_reload))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    name = entry.data.get(CONF_NAME)
    prefix = _prefix(name)
    for suffix in SERVICE_SUFFIXES:
        hass.services.async_remove(DOMAIN, f"{prefix}{suffix}")
    hass.services.async_remove("notify", _notify_name(name))
    return True


async def _async_reload(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
