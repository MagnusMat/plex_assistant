"""
Plex Assistant is a component for Home Assistant to add control of Plex to
Google Assistant with a little help from IFTTT or DialogFlow.

Play to Google Cast devices or Plex Clients using fuzzy searches for media and
cast device names.

https://github.com/maykar/plex_assistant
"""

from homeassistant.helpers.network import get_url
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

DOMAIN = "plex_assistant"
CONF_URL = "url"
CONF_TOKEN = "token"
CONF_DEFAULT_CAST = "default_cast"
CONF_LANG = "language"
CONF_TTS_ERROR = "tts_errors"
CONF_ALIASES = "aliases"
CONF_CAST_DELAY = "cast_delay"

CONFIG_SCHEMA = vol.Schema({DOMAIN: {
    vol.Required(CONF_URL): cv.url,
    vol.Required(CONF_TOKEN): cv.string,
    vol.Optional(CONF_DEFAULT_CAST): cv.string,
    vol.Optional(CONF_CAST_DELAY, default={}): vol.Any(dict),
    vol.Optional(CONF_LANG, default='en'): cv.string,
    vol.Optional(CONF_TTS_ERROR, default=True): cv.boolean,
    vol.Optional(CONF_ALIASES, default={}): vol.Any(dict),
}}, extra=vol.ALLOW_EXTRA)


class PA:
    """ Hold our libraries, devices, etc. """
    plex = None
    server = None
    lib = {}
    devices = {}
    device_names = []
    clients = {}
    client_names = []
    client_sensor = []
    alias_names = []
    attr_update = True


def setup(hass, config):
    """Called when Home Assistant is loading our component."""
    import logging
    import os

    from gtts import gTTS
    from plexapi.server import PlexServer
    from pychromecast import get_chromecasts
    from pychromecast.controllers.plex import PlexController

    from .helpers import (cc_callback, find_media, fuzzy, get_libraries,
                          media_error, play_media, video_selection)
    from .localize import LOCALIZE
    from .process_speech import process_speech
    from datetime import datetime

    _LOGGER = logging.getLogger(__name__)

    conf = config[DOMAIN]
    base_url = conf.get(CONF_URL)
    token = conf.get(CONF_TOKEN)
    default_cast = conf.get(CONF_DEFAULT_CAST)
    lang = conf.get(CONF_LANG)
    tts_error = conf.get(CONF_TTS_ERROR)
    aliases = conf.get(CONF_ALIASES)
    cast_delay = conf.get(CONF_CAST_DELAY)

    localize = LOCALIZE[lang] if lang in LOCALIZE.keys() else LOCALIZE['en']

    directory = hass.config.path() + '/www/plex_assist_tts/'
    if tts_error and not os.path.exists(directory):
        os.makedirs(directory, mode=0o777)

    get_chromecasts(blocking=False, callback=cc_callback)
    PA.server = PlexServer(base_url, token)
    PA.plex = PA.server.library
    PA.lib = get_libraries(PA.plex)
    PA.alias_names = list(aliases.keys()) if aliases else []

    def update_sensor():
        clients = [{client.title: {"ID": client.machineIdentifier,
                                   "type": client.product}} for client in PA.clients]
        devicelist = list(PA.devices.keys())
        state = str(len(devicelist + clients)) + ' connected devices.'
        attributes = {
            "Connected Devices": {
                'Cast Devices': devicelist or 'None',
                'Plex Clients': clients or 'None'
            },
            "friendly_name": "Plex Assistant Devices",
        }
        sensor = "sensor.plex_assistant_devices"
        hass.states.async_set(sensor, state, attributes)

    def handle_input(call):
        command_string = call.data.get("command").strip().lower()

        if not command_string:
            _LOGGER.warning(localize["no_call"])
            return

        chromecasts = get_chromecasts()
        for chromecast in chromecasts:
            PA.devices[chromecast.device.friendly_name] = chromecast

        PA.clients = PA.server.clients()
        PA.client_names = [client.title for client in PA.clients]
        PA.client_ids = [client.machineIdentifier for client in PA.clients]

        if localize["controls"]["update_sensor"] in command_string:
            update_sensor()
            return

        cast = None
        alias = ["", 0]
        client = False
        speech_error = False

        command = process_speech(command_string, localize, default_cast, PA)

        if not command["control"]:
            _LOGGER.debug({i: command[i] for i in command if i != 'library'})

        if PA.lib["updated"] < PA.plex.search(sort="addedAt:desc", limit=1)[0].addedAt:
            PA.lib = get_libraries(PA.plex)

        PA.device_names = list(PA.devices.keys())
        devices = PA.device_names + PA.client_names + PA.client_ids
        device = fuzzy(command["device"] or default_cast, devices)
        if aliases:
            alias = fuzzy(command["device"] or default_cast, PA.alias_names)

        if alias[1] < 60 and device[1] < 60:
            _LOGGER.warning("{0} {1}: \"{2}\"".format(
                localize["cast_device"].capitalize(),
                localize["not_found"],
                command["device"].title()
            ))
            _LOGGER.debug("Device Score: %s", device[1])
            _LOGGER.debug("Devices: %s", str(devices))

            if aliases:
                _LOGGER.debug("Alias Score: %s", alias[1])
                _LOGGER.debug("Aliases: %s", str(PA.alias_names))
            return

        name = aliases[alias[0]] if alias[1] > device[1] else device[0]
        cast = PA.devices[name] if name in PA.device_names else name
        client = isinstance(cast, str)
        if client:
            client_device = next(
                c for c in PA.clients if c.title == cast or c.machineIdentifier == cast)
            cast = client_device

        if command["control"]:
            control = command["control"]
            if client:
                cast.proxyThroughServer()
                plex_c = PA.server.client(cast.title)
            else:
                plex_c = PlexController()
                cast.wait()
                cast.register_handler(plex_c)
            if control == "play":
                plex_c.play()
            elif control == "pause":
                plex_c.pause()
            elif control == "stop":
                plex_c.stop()
            elif control == "jump_forward":
                plex_c.stepForward()
            elif control == "jump_back":
                plex_c.stepBack()
            return

        try:
            result = find_media(command, command["media"], PA.lib)
            media = video_selection(command, result["media"],
                                    result["library"])
        except Exception:
            error = media_error(command, localize)
            if tts_error:
                tts = gTTS(error, lang=lang)
                tts.save(directory + 'error.mp3')
                speech_error = True
            _LOGGER.warning(error)

        if speech_error and not client:
            cast.wait()
            med_con = cast.media_controller
            mp3 = get_url(hass) + "/local/plex_assist_tts/error.mp3"
            med_con.play_media(mp3, 'audio/mpeg')
            med_con.block_until_active()
            return

        _LOGGER.debug("Media: %s", str(media))

        if client:
            _LOGGER.debug("Client: %s", cast)
            cast.proxyThroughServer()
            plex_c = cast
            plex_c.playMedia(media)
        else:
            _LOGGER.debug("Cast: %s", cast.name)
            delay = 6
            if call.data.get("cast_delay") or call.data.get("cast_delay") == 0:
                delay = call.data.get("cast_delay")
            elif cast.name in cast_delay.keys():
                delay = cast_delay[cast.name]
            plex_c = PlexController()
            plex_c.namespace = 'urn:x-cast:com.google.cast.media'
            cast.register_handler(plex_c)
            cast.wait()
            play_media(float(delay), cast, plex_c, media)

        update_sensor()

    hass.services.register(DOMAIN, "command", handle_input)
    return True
