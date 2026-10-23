"""Config flow for Joaoapps Join."""

from __future__ import annotations

import hashlib
import logging
from typing import Any

from pyjoin import get_devices

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_API_KEY, CONF_DEVICE_ID, CONF_NAME
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
)

from .const import CONF_DEVICE_IDS, CONF_DEVICE_NAMES, DOMAIN, vol

_LOGGER = logging.getLogger(__name__)

TARGET_KEYS = (CONF_DEVICE_ID, CONF_DEVICE_IDS, CONF_DEVICE_NAMES)

STEP_USER_SCHEMA = vol.Schema({vol.Required(CONF_API_KEY): str})


def _targets(data: dict[str, Any]) -> dict[str, str]:
    return {key: data[key] for key in TARGET_KEYS if data.get(key)}


class JoinConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Join."""

    VERSION = 1

    def __init__(self) -> None:
        self._api_key: str | None = None
        self._devices: dict[str, str] = {}

    async def _validate(self, data: dict[str, Any]) -> str | None:
        """Return an error key, or None if the data is usable."""
        if len(_targets(data)) != 1:
            return "one_target_required"
        try:
            devices = await self.hass.async_add_executor_job(
                get_devices, data[CONF_API_KEY]
            )
        except Exception:  # noqa: BLE001
            _LOGGER.debug("Join API request failed", exc_info=True)
            return "cannot_connect"
        if not devices:
            return "invalid_auth"
        return None

    async def _create(self, data: dict[str, Any]) -> ConfigFlowResult:
        target = next(iter(_targets(data).values()))
        # Hash so the API key never shows up in the entry's unique_id.
        digest = hashlib.sha256(f"{data[CONF_API_KEY]}:{target}".encode()).hexdigest()
        await self.async_set_unique_id(digest[:16])
        self._abort_if_unique_id_configured()
        return self.async_create_entry(title=data.get(CONF_NAME) or "Join", data=data)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for the API key and list the devices under it."""
        errors: dict[str, str] = {}
        if user_input is not None:
            api_key = user_input[CONF_API_KEY].strip()
            try:
                devices = await self.hass.async_add_executor_job(get_devices, api_key)
            except Exception:  # noqa: BLE001
                _LOGGER.debug("Join API request failed", exc_info=True)
                errors["base"] = "cannot_connect"
            else:
                # pyjoin returns [(deviceName, deviceId), ...] (or False)
                found = {dev_id: name or dev_id for name, dev_id in devices or []}
                if found:
                    self._api_key = api_key
                    self._devices = found
                    return await self.async_step_devices()
                errors["base"] = "invalid_auth"
        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(
                STEP_USER_SCHEMA, user_input
            ),
            errors=errors,
        )

    async def async_step_devices(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Pick which of the account's devices to target."""
        errors: dict[str, str] = {}
        if user_input is not None:
            selected = user_input.get("devices") or []
            if not selected:
                errors["base"] = "no_devices_selected"
            else:
                data = {CONF_API_KEY: self._api_key}
                if name := user_input.get(CONF_NAME):
                    data[CONF_NAME] = name
                if len(selected) == 1:
                    data[CONF_DEVICE_ID] = selected[0]
                else:
                    data[CONF_DEVICE_IDS] = ",".join(selected)
                return await self._create(data)
        return self.async_show_form(
            step_id="devices",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_NAME): str,
                    vol.Required("devices"): SelectSelector(
                        SelectSelectorConfig(
                            options=[
                                SelectOptionDict(value=k, label=v)
                                for k, v in self._devices.items()
                            ],
                            multiple=True,
                        )
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_import(self, import_data: dict[str, Any]) -> ConfigFlowResult:
        """Import a `joaoapps_join:` YAML entry."""
        data = {k: v for k, v in import_data.items() if v}
        if (error := await self._validate(data)) is not None:
            return self.async_abort(reason=error)
        return await self._create(data)
