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

if sys.version_info >=  (2, 7):
    import json as json
else:
    import simplejson as json

import xbmc
import xbmcgui
import xbmcaddon

class LiveScoresAPI(object):

    def __init__(self):

        self.__addon = xbmcaddon.Addon("service.bbclivefootballscores")
        self._getS = self.__addon.getSetting

    def __loadLeagues(self):
        '''See if there are any previously selected leagues.

        Returns list of league IDs.
        '''

        try:
            watchedleagues = json.loads(str(self._getS("watchedleagues")))
        except:
            watchedleagues = []

        return watchedleagues

    def __saveLeagues(self, leagues):
        '''Converts list to JSON compatible string and saves it to our
        user's settings.
        '''

        rawdata = json.dumps(leagues)
        self.__addon.setSetting(id="watchedleagues",value=rawdata)

    def isFollowing(self, leagueID):

        return leagueID in self.__loadLeagues()

    def addLeague(self, leagueID):

        all = self.__loadLeagues()

        if not leagueID in all:
            all.append(leagueID)
            self.__saveLeagues(all)
            return True

        else:
            return False

    def removeLeague(self, leagueID):

        all = self.__loadLeagues()

        if leagueID in all:
            all.remove(leagueID)
            self.__saveLeagues(all)
            return True

        else:
            return False
