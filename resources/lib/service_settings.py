import xml.etree.ElementTree as ET
import os

import xbmc, xbmcaddon


class ServiceSettings(object):

    specials = ("_addon", "_pluginpath", "_profile", "_file",
                "_old", "_data", "_reload", "_updated", "_default")

    def __init__(self, service, default=None):
        self._addon = xbmcaddon.Addon(service)
        profile = self._addon.getAddonInfo('profile')
        self._pluginpath = self._addon.getAddonInfo("path")
        self._profile = xbmc.translatePath(profile).decode('utf-8')
        self._file = os.path.join(self._profile, "settings.xml")

        self._old = {"settings": {}}
        self._data = {"settings": {}}
        self._updated = []
        self._default = default

        self._reload()

    def __getattr__(self, attr):
        if attr in ServiceSettings.specials:
            return self.__dict__[attr]
        else:
            if attr in self._data["settings"]:
                return self._data["settings"][attr]
            else:
                return self._default

    def __setattr__(self, attr, value):
        if attr in ServiceSettings.specials:
            self.__dict__[attr] = value
        else:
            self._addon.setSetting(attr, value)
            self._data["settings"][attr] = value

    def _reload(self):
        try:
            raw = ET.parse(self._file)
            root = raw.getroot()

            config = {x.get("id"): x.get("value") for x in root}
            self._data["settings"] = config

            data = self._data["settings"]
            old = self._old["settings"]

            new_keys = [x for x in data if x not in old]
            updated = [x for x in data if data[x] != old.get(x)]
            self._updated = list(set(new_keys + updated))
        except:
            self._data = {"settings": {}}
            self._updated = []
        finally:
            self._old = self._data.copy()
