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
import xbmc
import xbmcaddon

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

class FootballHelperMenu(object):

    def __init__(self):

        pass

    def show(self):

        # Set the title and menu size
        self.window = AddonDialogWindow("Menu")
        self.window.setGeometry(450,300,5,2)

        # ITEM 1 - LEAGUE TABLES
        self.ltbutton = Button("Show League Tables")
        self.window.placeControl(self.ltbutton, 0, 0, columnspan = 2)

        # ITEM 2 - MATCH DETAIL
        self.mdbutton = Button("Show Match Detail")
        self.window.placeControl(self.mdbutton, 1, 0, columnspan = 2)

        # ITEM 3 - MATCH DETAIL
        self.resbutton = Button("Show Results")
        self.window.placeControl(self.resbutton, 2, 0, columnspan = 2)

        # CLOSE BUTTON

        self.clbutton = Button("Close")
        self.window.placeControl(self.clbutton, 4, 0, columnspan = 2)

        # Bind actions
        self.window.connect(ACTION_PREVIOUS_MENU, lambda: self.window.close())
        self.window.connect(ACTION_NAV_BACK, lambda: self.window.close())
        self.window.connect(self.clbutton, lambda: self.window.close())
        self.window.connect(self.ltbutton, lambda: self.open("leaguetable"))
        self.window.connect(self.mdbutton, lambda: self.open("matchdetail"))
        self.window.connect(self.resbutton, lambda: self.open("results"))

        self.window.setFocus(self.ltbutton)

        # Handle navigation to make user experience better
        self.ltbutton.controlDown(self.mdbutton)
        self.mdbutton.controlUp(self.ltbutton)
        self.mdbutton.controlDown(self.resbutton)
        self.resbutton.controlDown(self.clbutton)
        self.resbutton.controlUp(self.mdbutton)
        self.clbutton.controlUp(self.resbutton)
        # self.leaguelist.controlLeft(self.leaguebutton)
        # self.leaguelist.controlRight(self.closebutton)
        # self.closebutton.controlUp(self.leaguelist)
        # self.closebutton.controlLeft(self.leaguebutton)
        # self.leaguebutton.controlRight(self.closebutton)
        # self.leaguebutton.controlUp(self.leaguelist)

        # Ready to go...
        self.window.doModal()

    def open(self, mode):

        self.window.close()
        xbmc.executebuiltin("RunScript(service.bbclivefootballscores, mode={0})".format(mode))
