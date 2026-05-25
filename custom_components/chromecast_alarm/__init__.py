"""Chromecast Alarm integration: setup, services, runner registry."""
from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import (
    CONF_DAYS,
    CONF_TIME,
    DAY_CODES,
    DATA_RUNNERS,
    DOMAIN,
    PLATFORMS,
    SERVICE_FIRE,
    SERVICE_SET_DAYS,
    SERVICE_SET_TIME,
    SERVICE_SNOOZE,
    SERVICE_STOP,
)
from .coordinator import AlarmRunner

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config) -> bool:
    """Register module-wide services once."""
    hass.data.setdefault(DOMAIN, {DATA_RUNNERS: {}})
    _register_services(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a Chromecast Alarm config entry."""
    hass.data.setdefault(DOMAIN, {DATA_RUNNERS: {}})
    runners: dict[str, AlarmRunner] = hass.data[DOMAIN][DATA_RUNNERS]

    runner = AlarmRunner(hass, entry)
    await runner.async_start()
    runners[entry.entry_id] = runner

    entry.async_on_unload(entry.add_update_listener(_async_options_updated))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Tear down a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        runners: dict[str, AlarmRunner] = hass.data.get(DOMAIN, {}).get(DATA_RUNNERS, {})
        runner = runners.pop(entry.entry_id, None)
        if runner is not None:
            await runner.async_stop()
    return unload_ok


async def _async_options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Re-arm the runner when options change."""
    runners: dict[str, AlarmRunner] = hass.data.get(DOMAIN, {}).get(DATA_RUNNERS, {})
    runner = runners.get(entry.entry_id)
    if runner:
        await runner.async_handle_options_updated()


# ----------------------------------------------------------------------
# Services
# ----------------------------------------------------------------------

_FIRE_STOP_SCHEMA = vol.Schema(
    {vol.Required(ATTR_ENTITY_ID): cv.entity_ids}
)

_SNOOZE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
        vol.Optional("minutes"): vol.All(vol.Coerce(int), vol.Range(min=1, max=120)),
    }
)

_SET_TIME_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
        vol.Required("time"): cv.string,
    }
)

_SET_DAYS_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
        vol.Required("days"): vol.All(
            cv.ensure_list,
            [vol.In(DAY_CODES)],
        ),
    }
)


def _runners_for_entity_ids(hass: HomeAssistant, entity_ids: list[str]) -> list[AlarmRunner]:
    """Resolve entity_ids to runners. Accepts switch.<slug> entities owned by this domain."""
    runners: dict[str, AlarmRunner] = hass.data.get(DOMAIN, {}).get(DATA_RUNNERS, {})
    # Resolve via entity_registry to find config_entry_id behind each entity.
    from homeassistant.helpers import entity_registry as er

    registry = er.async_get(hass)
    result: list[AlarmRunner] = []
    for eid in entity_ids:
        entry = registry.async_get(eid)
        if entry is None or entry.platform != DOMAIN:
            _LOGGER.warning("Entity %s is not a Chromecast Alarm entity", eid)
            continue
        runner = runners.get(entry.config_entry_id) if entry.config_entry_id else None
        if runner is not None and runner not in result:
            result.append(runner)
    return result


def _register_services(hass: HomeAssistant) -> None:
    if hass.services.has_service(DOMAIN, SERVICE_FIRE):
        return

    async def _fire(call: ServiceCall) -> None:
        for runner in _runners_for_entity_ids(hass, call.data[ATTR_ENTITY_ID]):
            await runner.async_fire_now()

    async def _stop(call: ServiceCall) -> None:
        for runner in _runners_for_entity_ids(hass, call.data[ATTR_ENTITY_ID]):
            await runner.async_stop_playback()

    async def _snooze(call: ServiceCall) -> None:
        minutes = call.data.get("minutes")
        for runner in _runners_for_entity_ids(hass, call.data[ATTR_ENTITY_ID]):
            await runner.async_snooze(minutes)

    async def _set_time(call: ServiceCall) -> None:
        new_time = call.data["time"]
        for runner in _runners_for_entity_ids(hass, call.data[ATTR_ENTITY_ID]):
            updated = {**runner.entry.options, CONF_TIME: new_time}
            hass.config_entries.async_update_entry(runner.entry, options=updated)

    async def _set_days(call: ServiceCall) -> None:
        new_days = call.data["days"]
        for runner in _runners_for_entity_ids(hass, call.data[ATTR_ENTITY_ID]):
            updated = {**runner.entry.options, CONF_DAYS: new_days}
            hass.config_entries.async_update_entry(runner.entry, options=updated)

    hass.services.async_register(DOMAIN, SERVICE_FIRE, _fire, schema=_FIRE_STOP_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_STOP, _stop, schema=_FIRE_STOP_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SNOOZE, _snooze, schema=_SNOOZE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SET_TIME, _set_time, schema=_SET_TIME_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SET_DAYS, _set_days, schema=_SET_DAYS_SCHEMA)
