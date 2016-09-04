from os.path import join
from time import sleep

import xbmcaddon
import xbmcgui
import xbmc


_A_ = xbmcaddon.Addon("service.bbclivefootballscores")
pluginPath = _A_.getAddonInfo("path")
skinpath = join(pluginPath, "resources", "skins", "Default", "720p")

class FootballNotification(xbmcgui.WindowXMLDialog):

    pass
