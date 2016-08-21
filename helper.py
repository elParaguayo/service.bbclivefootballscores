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
import os
import json

# Import standard xbmc/kodi modules
import xbmc
import xbmcgui
import xbmcaddon

# Import service specific objects
from resources.lib.settings import selectLeagues, toggleNotification
from resources.lib.league_tables import XBMCLeagueTable
from resources.lib.live_scores_detail import XBMCLiveScoresDetail
from resources.lib.results import XBMCResults
from resources.lib.fixtures import XBMCFixtures
from resources.lib.utils import closeAddonSettings
from resources.lib.menu import FootballHelperMenu
from resources.lib.ticker import TickerOverlay

# Import PyXBMCt module.
from pyxbmct.addonwindow import *

_A_ = xbmcaddon.Addon("service.bbclivefootballscores")
_GET_ = _A_.getSetting
_SET_ = _A_.setSetting

getwin = {"jsonrpc":"2.0",
          "id":1,
          "method":"GUI.GetProperties",
          "params":
            {"properties":["currentwindow"]}
         }

def ToggleTicker():

    try:
        tickers = json.loads(_GET_("currenttickers"))
    except ValueError:
        tickers = {}

    if not tickers:
        tickers = {}

    # Get the current window ID
    current_window = xbmc.executeJSONRPC(json.dumps(getwin))
    window_id = json.loads(current_window)["result"]["currentwindow"]["id"]

    # json doesn't like integer keys so we need to look for a unicode object
    key = unicode(window_id)

    if key in tickers:

        # There's already a ticker on this window
        # Remove it from our list but get the ID of the ticker first
        tickerid = tickers.pop(key)

        # Get the window
        w = xbmcgui.Window(window_id)

        # Find the ticker
        t = w.getControl(tickerid)

        # and remove it
        w.removeControl(t)

    else:

        # No ticker, so create one
        ScoreTicker = TickerOverlay(window_id)

        # Show it
        ScoreTicker.show()

        # Give it current text
        tickertext = xbmc.getInfoLabel("Skin.String(bbcscorestickertext)")
        tickertext = tickertext.decode("utf-8").replace("|", ",")
        ScoreTicker.update(unicode(tickertext))

        # Add to our list of current active tickers
        tickers[ScoreTicker.windowid] = ScoreTicker.id

    # Save our list
    _SET_("currenttickers", json.dumps(tickers))

try:
    params = dict((x.split("=") for x in sys.argv[1].lower().split(";")))
except (ValueError, AttributeError, IndexError):
    params = {}

# If no parameters are passed then we show default menu
if not params:

    menu = FootballHelperMenu()
    menu.show()
    menu = None


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

    # Get rid of it when we're finished
    xlt = None

elif params.get("mode") == "matchdetail":

    # Close addon setting window (if open)
    closeAddonSettings()

    # Create an instance of the XBMC League Table
    xlsd = XBMCLiveScoresDetail()

    # and display it!
    xlsd.start()

    # Get rid of it when we're finished
    xlsd = None

elif params.get("mode") == "results":
    # Close addon setting window (if open)
    closeAddonSettings()

    # Create an instance of the XBMC Results
    xr = XBMCResults()

    # and display it!
    xr.start()

    # Get rid of it when we're finished
    xr = None

elif params.get("mode") == "fixtures":
    # Close addon setting window (if open)
    closeAddonSettings()

    # Create an instance of the XBMC Fixtures
    xf = XBMCFixtures()

    # and display it!
    xf.start()

    # Get rid of it when we're finished
    xf = None

elif params.get("mode") == "toggleticker":

    ToggleTicker()
