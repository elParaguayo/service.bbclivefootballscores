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

    It allows users to select which leagues they wish to receive updates
    for.

    It is called via the script configuration screen or by passing
    parameters to trigger specific functions.

    The script accepts the following parameters:
      toggle:   Turns score notifications on and off
      reset:    Resets watched league data

    NB only one parameter should be passed at a time.
'''
import sys

if sys.version_info >=  (2, 7):
    import json as json
    from collections import OrderedDict
else:
    import simplejson as json
    from resources.lib.ordereddict import OrderedDict

import xbmc
import xbmcgui
import xbmcaddon

from resources.lib.footballscores import Results
from resources.lib.utils import closeAddonSettings

# Import PyXBMCt module.
from pyxbmct.addonwindow import *

_A_ = xbmcaddon.Addon("service.bbclivefootballscores")
_S_ = _A_.getSetting

def localise(id):
    '''Gets localised string.

    Shamelessly copied from service.xbmc.versioncheck
    '''
    string = _A_.getLocalizedString(id).encode( 'utf-8', 'ignore' )
    return string

class XBMCResults(object):

    def __init__(self):

        # It may take a bit of time to display menus/tables so let's
        # make sure the user knows what's going on
        self.prog = xbmcgui.DialogProgressBG()
        self.prog.create(localise(32112), localise(32107))

        # variables for league table display
        self.redraw = False
        self.offset = 0
        self.menu = True
        self.leagueid = 0

        # variables for root menu
        self.showall = True
        self.active = True

        # Get our favourite leagues
        self.watchedleagues = json.loads(str(_S_("watchedleagues")))

        # Create a Leaue Table instance
        self.results = Results()

        self.prog.update(25, localise(32108))

        allcomps = self.results.getCompetitions()

        allcomps = [x for x in allcomps if x["id"][:11] == "competition"]

        # Get all of the available leagues, store it in an Ordered Dict
        # key=League name
        # value=League ID
        self.allleagues = OrderedDict((x["name"],
                                       x["id"][-9:])
                                       for x in allcomps)

        self.prog.update(75, localise(32109))

        # Create a similar Ordered Dict for just those leagues that we're
        # currently followin
        lgid = x["id"][-9:]
        self.watchedleagues = OrderedDict((x["name"], x["id"][-9:])
                                          for x in allcomps
                                          if (unicode(lgid).isnumeric() and
                                              int(lgid) in self.watchedleagues))

        self.prog.close()


    def showMenu(self, all_leagues=False):



        # Setting this to False means that the menu won't display if
        # we hit escape
        self.active = False

        # Set the title and menu size
        window = AddonDialogWindow(localise(32100))
        window.setGeometry(450,300,5,4)

        # Create a List object
        self.leaguelist = List()

        # Get the appropriate list of leagues depending on what mode we're in
        displaylist = self.allleagues if self.showall else self.watchedleagues

        #self.prog.update(92)

        # Add the List to the menu
        window.placeControl(self.leaguelist, 0, 0, rowspan=4, columnspan=4)
        self.leaguelist.addItems(displaylist.keys())

        # Bind the list action
        p = self.leaguelist.getSelectedPosition
        window.connect(self.leaguelist,
                       lambda w = window:
                       self.setID(self.leaguelist.getListItem(p()).getLabel(),
                                  w))

        # Don't think these are needed, but what the hell...
        window.connect(ACTION_PREVIOUS_MENU, lambda w=window: self.finish(w))
        window.connect(ACTION_NAV_BACK, lambda w=window: self.finish(w))

        #self.prog.update(94)

        # Create the button to toggle mode
        leaguetext = localise(32101) if self.showall else localise(32102)
        self.leaguebutton = Button(leaguetext)
        window.placeControl(self.leaguebutton, 4, 0, columnspan=2)

        # Bind the button
        window.connect(self.leaguebutton, lambda w=window: self.toggleMode(w))

        #self.prog.update(96)

        # Add the close button
        self.closebutton = Button(localise(32103))
        window.placeControl(self.closebutton, 4, 2, columnspan=2)
        window.setFocus(self.leaguelist)
        # Connect the button to a function.
        window.connect(self.closebutton, lambda w=window:self.finish(w))

        #self.prog.update(98)

        # Handle navigation to make user experience better
        self.leaguelist.controlLeft(self.leaguebutton)
        self.leaguelist.controlRight(self.closebutton)
        self.closebutton.controlUp(self.leaguelist)
        self.closebutton.controlLeft(self.leaguebutton)
        self.leaguebutton.controlRight(self.closebutton)
        self.leaguebutton.controlUp(self.leaguelist)

        # Ready to go...
        window.doModal()

        # Clean up
        window = None

    def showResults(self):

        # Basic variables
        self.redraw = False

        # If there are multiple tables for a competition (e.g. World Cup)
        # Let's just get the required one
        table = self.rawdata[self.offset]

        #self.prog.update(92)

        # How many rows are in the table?
        # We'll need this to set the size of the display
        n = len(table["results"])

        # Create a window instance and size it
        window = AddonDialogWindow(table["date"])
        window.setGeometry(450, (n + 4) * 30, n + 3, 15)

        #self.prog.update(94)

        # Add the teams
        for i,r in enumerate(table["results"]):
            try:
                r["score"] = r["score"].replace("-", " - ")
            except:
                pass

            # result = Label(u"{hometeam} {score} {awayteam}".format(**r),
            #                alignment=2)
            home = Label(u"{hometeam}".format(**r), alignment=1)
            score = Label("{score}".format(**r), alignment=2)
            away = Label(u"{awayteam}".format(**r))

            window.placeControl(home, i+1, 0, columnspan=6)
            window.placeControl(score, i+1, 6, columnspan=3)
            window.placeControl(away, i+1, 9, columnspan=6)


        #self.prog.update(94)

        # Add the close button
        closebutton = Button(localise(32103))
        window.placeControl(closebutton, n+2, 5, columnspan=5)
        window.setFocus(closebutton)
        # Connect the button to a function.
        window.connect(closebutton, lambda w=window: self.finish(w))

        # Not sure we need these...
        window.connect(ACTION_PREVIOUS_MENU, lambda w=window: self.finish(w))
        window.connect(ACTION_NAV_BACK, lambda w=window: self.finish(w))

        #self.prog.update(96)

        # We may need some extra buttons (for multiple table competitions)
        nextbutton = Button(localise(32104))
        prevbutton = Button(localise(32105))

        # There are more leagues after the one we're showing
        if self.offset < (len(self.rawdata) - 1):
            window.placeControl(nextbutton, n+2, 10, columnspan=5)
            window.connect(nextbutton, lambda w=window: self.next(w))
            nextbutton.controlLeft(closebutton)
            closebutton.controlRight(nextbutton)

        # There are more leagues before the one we're showing
        if self.offset > 0:
            window.placeControl(prevbutton, n+2, 0, columnspan=5)
            window.connect(prevbutton, lambda w=window: self.previous(w))
            prevbutton.controlRight(closebutton)
            closebutton.controlLeft(prevbutton)

        #self.prog.close()

        # Ready to go...
        window.doModal()

        # Clean up
        window = None

    def getResultsData(self, ID):

        self.prog.create(localise(32112), localise(32113))
        try:
            raw = self.results.getResults("competition-%s"
                                                 % (self.leagueid))

        except:
            raw = None

        self.prog.close()

        return raw

    def setID(self, ID, w):
        # Gets the ID of the selected league
        ID = self.allleagues[ID]
        self.setleague(ID,w)

    def next(self,w):
        # Display the next table in the competion
        self.offset += 1
        self.redraw = True
        w.close()

    def previous(self,w):
        # Display the previous tablein the competition
        self.offset -= 1
        self.redraw = True
        w.close()

    def finish(self,w):
        # We're done. Gracefully close down menu.
        self.redraw = False
        self.menu = False
        self.active = False
        w.close()

    def setleague(self,lg, w):
        # Set up the variables to display the league table
        self.leagueid = lg
        self.offset = 0
        self.redraw = True
        w.close()
        self.rawdata = self.getResultsData(self.leagueid)
        self.prog.update(90)

    def toggleMode(self,w):
        # Toggle between showing all competitions and just our favourites
        self.showall = not self.showall
        self.active = True
        w.close()

    def start(self):

        # Let's begin
        while self.active:
            # Show the main menu
            self.showMenu()

            while self.redraw:

                # Show a league table
                self.showResults()

if __name__ == "__main__":

    # Close addon setting window (if open)
    closeAddonSettings()

    # Create an instance of the XBMC League Table
    xlr = XBMCResults()

    # and display it!
    xlr.start()
