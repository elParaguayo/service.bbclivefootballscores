'''
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program. If not, see <http://www.gnu.org/licenses/>.
'''

''' This script is part of the BBC Football Scores service by elParaguayo

    Its purpose is to handle all non-core elements of the service.

    If called directly it will (eventually) present a menu of different options.
    Alternatively it can be called passing any of the following parameters:

    mode:
      selectleague: run the Select Leagues dialogue
      leaguetable: display league tables
      matchdetail: display additional match detail
      fixtures: display upcoming fixturs (WIP)
      results: display historic results (WIP)
'''

import sys

# Import standard xbmc/kodi modules
import xbmc
import xbmcgui
import xbmcaddon

# Import service specific objects
from resources.lib.settings import selectLeagues, toggleNotification
from resources.lib.league_tables import XBMCLeagueTable
from resources.lib.live_scores_detail import XBMCLiveScoresDetail
from resources.lib.utils import closeAddonSettings
from resources.lib.menu import FootballHelperMenu

# Import PyXBMCt module.
from pyxbmct.addonwindow import *

try:
    params = dict((x.split("=") for x in sys.argv[1].lower().split(";")))
except (ValueError, AttributeError, IndexError):
    params = {}

# If no parameters are passed then we show default menu
if not params:

    menu = FootballHelperMenu()
    menu.show()


# If there are parameters, let's see what we want to do...
if params.get("mode") == "selectleague":

    selectLeagues()

elif params.get("mode") == "leaguetable":

    # Close addon setting window (if open)
    closeAddonSettings()

    # Create an instance of the XBMC League Table
    xlt = XBMCLeagueTable()

    # and display it!
    xlt.start()

elif params.get("mode") == "matchdetail":

    # Close addon setting window (if open)
    closeAddonSettings()

    # Create an instance of the XBMC League Table
    xlsd = XBMCLiveScoresDetail()

    # and display it!
    xlsd.start()
