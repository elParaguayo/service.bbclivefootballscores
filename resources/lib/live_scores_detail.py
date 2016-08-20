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

'''
import sys
import os

if sys.version_info >=  (2, 7):
    import json as json
    from collections import OrderedDict
else:
    import simplejson as json
    from resources.lib.ordereddict import OrderedDict

import xbmc
import xbmcgui
import xbmcaddon

from resources.lib.footballscores import League
from resources.lib.utils import closeAddonSettings

# Import PyXBMCt module.
from pyxbmct.addonwindow import *

_A_ = xbmcaddon.Addon("service.bbclivefootballscores")
_S_ = _A_.getSetting
pluginPath = _A_.getAddonInfo("path")

def imgloc(img):
    return os.path.join(pluginPath, "resources", "media" , img)

imagedict = {"goal": imgloc("ball-white.png"),
             "yellow": imgloc("yellow-card.png"),
             "red": imgloc("red-card.png")}

def localise(id):
    '''Gets localised string.

    Shamelessly copied from service.xbmc.versioncheck
    '''
    string = _A_.getLocalizedString(id).encode( 'utf-8', 'ignore' )
    return string

class XBMCLiveScoresDetail(object):

    def __init__(self):

        # It may take a bit of time to display menus/tables so let's
        # make sure the user knows what's going on
        self.prog = xbmcgui.DialogProgressBG()
        self.prog.create(localise(32106), localise(32107))

        # variables for league table display
        self.redraw = False
        self.menu = True
        self.leagueid = 0

        # variables for root menu
        self.showall = True
        self.active = True

        # Get our favourite leagues
        self.watchedleagues = json.loads(str(_S_("watchedleagues")))

        self.prog.update(25, localise(32108))
        self.activeleagues = League.getLeagues()
        self.favouriteleagues = [x for x in self.activeleagues if int(x["id"]) in self.watchedleagues]

        # Get all of the available leagues, store it in an Ordered Dict
        # key=League name
        # value=League ID
        self.allleagues = OrderedDict((x["name"],
                                       x["id"])
                                       for x in self.activeleagues)

        self.prog.update(75, localise(32109))

        # Create a similar Ordered Dict for just those leagues that we're
        # currently followin
        self.watchedleagues = OrderedDict((x["name"], x["id"])
                                          for x in self.favouriteleagues)

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

        # self.prog.close()

        # Ready to go...
        window.doModal()

        # Clean up
        window = None

    def showLiveMatches(self):

        # Basic variables
        self.redraw = False

        # If there are multiple tables for a competition (e.g. World Cup)
        # Let's just get the required one
        matches = self.rawdata.LeagueMatches

        #self.prog.update(92)

        # How many rows are in the table?
        # We'll need this to set the size of the display
        n = min(len(matches),8)

        # Create a window instance and size it
        window = AddonDialogWindow("Select Match")
        window.setGeometry(450, 450, 8, 4)

        #self.prog.update(94)

        self.matchlist = List()

        window.placeControl(self.matchlist, 0, 0, rowspan=7, columnspan=4)
        self.matchlist.addItems([unicode(x) for x in matches])

        # Bind the list action
        p = self.matchlist.getSelectedPosition
        window.connect(self.matchlist,
                       lambda w = window:
                       self.setMatch(p(),
                                  w))
        #self.matchlist.addItems(["2","3"])

        # Add the teams
        # for i, m in enumerate(matches):
        #     match = Button(unicode(m))
        #     window.placeControl(match,i+1,0, columnspan=4)

        #self.prog.update(94)

        # Add the close button
        closebutton = Button(localise(32103))
        window.placeControl(closebutton, 7, 1, columnspan=2)
        window.setFocus(self.matchlist)
        # Connect the button to a function.
        window.connect(closebutton, lambda w=window: self.finish(w))

        # Not sure we need these...
        window.connect(ACTION_PREVIOUS_MENU, lambda w=window: self.finish(w))
        window.connect(ACTION_NAV_BACK, lambda w=window: self.finish(w))

        #self.prog.update(96)

        self.matchlist.controlLeft(closebutton)
        self.matchlist.controlRight(closebutton)
        closebutton.controlUp(self.matchlist)

        # We may need some extra buttons (for multiple table competitions)
        nextbutton = Button(localise(32104))
        prevbutton = Button(localise(32105))

        # Ready to go...
        window.doModal()

        # Clean up
        window = None

    def showMatchDetail(self, match):

        # Basic variables
        self.redraw = False

        match.detailed = True
        match.Update()

        homeincidents = [x for x in match.rawincidents if x[0]=="home"]
        awayincidents = [x for x in match.rawincidents if x[0]=="away"]

        n = max(len(homeincidents), len(awayincidents))

        # Create a window instance and size it
        window = AddonDialogWindow("Match Detail")
        window.setGeometry(700, 190 + (n * 30), n + 4, 11)

        #self.prog.update(94)

        homelabel = Label(u"[B]{0}[/B]".format(match.HomeTeam), alignment=ALIGN_CENTER)
        awaylabel = Label(u"[B]{0}[/B]".format(match.AwayTeam), alignment=ALIGN_CENTER)
        scorelabel = Label("[B]{homescore} - {awayscore}[/B]".format(**match.matchdict), alignment=ALIGN_CENTER)

        window.placeControl(homelabel, 0, 0, columnspan=5)
        window.placeControl(awaylabel, 0, 6, columnspan=5)
        window.placeControl(scorelabel, 1, 4, columnspan=3)

        # Add the incidents
        for i, m in enumerate(homeincidents):
            #t = Label(m[1][0], alignment=ALIGN_CENTER_X)
            t = Image(imagedict[m[1]], aspectRatio=2)
            p = Label(m[2], alignment=ALIGN_RIGHT)
            c = Label(m[3], alignment=ALIGN_CENTER_X)

            window.placeControl(t,i+2,0)
            window.placeControl(p,i+2,1, columnspan=3)
            window.placeControl(c,i+2,4)

        for i, m in enumerate(awayincidents):
            t = Image(imagedict[m[1]], aspectRatio=2)
            p = Label(m[2], alignment=ALIGN_RIGHT)
            c = Label(m[3], alignment=ALIGN_CENTER_X)

            window.placeControl(t,i+2,6)
            window.placeControl(p,i+2,7, columnspan=3)
            window.placeControl(c,i+2,10)

        #self.prog.update(94)

        # Add the close button
        closebutton = Button(localise(32103))
        window.placeControl(closebutton, n+3, 6, columnspan=4)
        window.setFocus(closebutton)
        # Connect the button to a function.
        window.connect(closebutton, lambda w=window: self.finish(w))

        # Choose another competition
        compbutton = Button("Different Game")
        window.placeControl(compbutton, n+3, 1, columnspan=4)
        # Connect the button to a function.
        window.connect(compbutton, lambda w=window: self.back(w))

        # Not sure we need these...
        window.connect(ACTION_PREVIOUS_MENU, lambda w=window: self.finish(w))
        window.connect(ACTION_NAV_BACK, lambda w=window: self.finish(w))

        #self.prog.update(96)

        # We may need some extra buttons (for multiple table competitions)
        nextbutton = Button(localise(32104))
        prevbutton = Button(localise(32105))

        closebutton.controlLeft(compbutton)
        compbutton.controlRight(closebutton)

        # Ready to go...
        window.doModal()

        # Clean up
        window = None

    def getLiveMatches(self, ID):

        self.prog.create(localise(32106), localise(32111))
        try:
            raw = League(self.leagueid)

        except:
            raw = None

        self.prog.close()

        return raw

    def back(self, w):
        self.redraw = True
        w.close()

    def setID(self, ID, w):
        # Gets the ID of the selected league
        ID = self.allleagues[ID]
        self.setleague(ID,w)

    def setMatch(self, ID, w):
        m = self.rawdata.LeagueMatches[ID]
        w.close()
        self.showMatchDetail(m)

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
        self.rawdata = self.getLiveMatches(self.leagueid)
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
                self.showLiveMatches()
