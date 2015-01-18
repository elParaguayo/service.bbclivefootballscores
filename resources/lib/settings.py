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

from resources.lib.footballscores import getAllLeagues

_A_ = xbmcaddon.Addon("service.bbclivefootballscores")
_S_ = _A_.getSetting

# Define modes
STANDARD = 0
RESET = 1
TOGGLE_NOTIFICATIONS = 2

modes= {"standard": STANDARD,
        "reset": RESET,
        "toggle": TOGGLE_NOTIFICATIONS}

def localise(id):
    '''Gets localised string.

    Shamelessly copied from service.xbmc.versioncheck
    '''
    string = _A_.getLocalizedString(id).encode( 'utf-8', 'ignore' )
    return string

def Notify(subject, message, image=None):
    '''Displays match notification.

    Take 3 arguments:
    subject:    subject line
    message:    message line
    image:      path to icon
    '''
    xbmcgui.Dialog().notification(subject, message, image, 2000)

def selectLeagues():
    '''Get list of available leagues and allow user to select those
    leagues from which they want to receive updates.
    '''

    # Get list of leagues
    # Format is [{"name": "Name of League",
    #             "id": "competition-xxxxxxx"}]
    leagues = getMasterLeagueList()

    # Set a flag to keep displaying select dialog until flag changes
    finishedSelection = False

    # Load the list of leagues currently selected by user
    watchedleagues = loadLeagues()

    # Start loop - will be exited once user confirms selection or
    # cancels
    while not finishedSelection:

        # Empty list for select dialog
        userchoice = []

        # Loop through leagues
        for league in leagues:

            try:
                # Add league details to our list
                # leagues.append([league["name"],int(league["id"][12:])])

                # Check whether leagues is one we're following
                if int(league["id"]) in watchedleagues:

                    # Mark the league if it's one the user has previously
                    # selected and add it to the select dialog
                    userchoice.append("*" + league["name"])

                else:

                # If not previously selected, we still need to add to
                # select dialog
                    userchoice.append(league["name"])

            # Hopefully we don't end up here...
            except:

                # Tell the user there's a problem
                userchoice.append(localise(32020))

                # We only need to tell the user once!
                break

        # Add an option to say we've finished selecting leagues
        userchoice.append(localise(32022))


        # Display the list
        inputchoice = xbmcgui.Dialog().select(localise(32021),
                                              userchoice)


        # Check whether the user has clicked on a league...
        if (inputchoice >=0 and not userchoice[inputchoice] == localise(32022)
            and not userchoice[inputchoice] == localise(32021)):

            # If it's one that's already in our watched league list...
            if int(leagues[inputchoice]["id"]) in watchedleagues:

                # ...then we need to remove it
                watchedleagues.remove(int(leagues[inputchoice]["id"]))

            # if not...
            else:

                # ... then we need to add it
                watchedleagues.append(int(leagues[inputchoice]["id"]))

        # If we're done
        elif userchoice[inputchoice] == localise(32022):

            # Save our new list
            saveLeagues(watchedleagues)

            # Set the flag to leave the select dialog loop
            finishedSelection = True

        # If there's an error or we hit cancel
        elif (inputchoice == -1 or
              userchoice[inputchoice] == localise(32020)):


            # end the selection (but don't save new settings)
            finishedSelection = True

def getMasterLeagueList():
    '''Returns master list of leagues/competitions for which we
    can obtain data.

    Some competitions are only visible when matches are being
    played so any new competitions are added to the master list
    whenever this script is run.

    Returns: masterLeagueList - list of competitions in dict
                                format {"name": xx, "id", xx}
    '''

    currentleagues = getAllLeagues()

    try:
        masterLeagueList = json.loads(_S_("masterlist"))

    except:
        masterLeagueList = []

    masterLeagueList += [x for x in currentleagues
                         if x not in masterLeagueList]

    _A_.setSetting(id="masterlist",value=json.dumps(masterLeagueList))

    return masterLeagueList

def loadLeagues():
    '''See if there are any previously selected leagues.

    Returns list of league IDs.
    '''

    try:
        watchedleagues = json.loads(str(_S_("watchedleagues")))
    except:
        watchedleagues = []

    return watchedleagues

def saveLeagues(leagues):
    '''Converts list to JSON compatible string and saves it to our
    user's settings.
    '''

    rawdata = json.dumps(leagues)
    _A_.setSetting(id="watchedleagues",value=rawdata)

def resetLeagues():
    '''Clears all saved league IDs.

    Useful if IDs change leading to duplicate menu entries.
    '''
    _A_.setSetting(id="watchedleagues",value="[]")
    _A_.setSetting(id="masterlist",value="[]")
    ok = xbmcgui.Dialog().ok(localise(32023), localise(32027))

def toggleNotification():
    '''Toggles score notifications on or off.'''
    state = not (_S_("Alerts") == "true")
    Notify("BBC Football Scores", localise(32024) % (localise(32025) if state else localise(32026)))
    _A_.setSetting(id="Alerts", value=str(state).lower())
