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

'''
    BBC Football Scores service for XBMC
    by elParaguayo

    Provides notifications for live matches from a large number of leagues.

    Version: 0.1.0
'''

import os
import sys

if sys.version_info >=  (2, 7):
    import json as json
else:
    import simplejson as json

import xbmc
import xbmcaddon

from footballscores import League

# Set the addon environment
_A_ = xbmcaddon.Addon()
_S_ = _A_.getSetting
pluginPath = _A_.getAddonInfo("path")

# Set some constants

# Define our images
IMG_GOAL = os.path.join(pluginPath, "images", "goal.jpg")
IMG_FT = os.path.join(pluginPath, "images", "ft.jpg")
IMG_LATEST = os.path.join(pluginPath, "images" ,"latest.jpg")
IMG_HT = os.path.join(pluginPath, "images", "ht.jpg")
IMG_FIXTURE = os.path.join(pluginPath, "images" , "notstarted.jpg")

# STATUS_DICT object
# Format is {status: [status text, image path]}
STATUS_DICT = {"FT": ["Full Time", IMG_FT],
              "HT": ["Half Time", IMG_HT],
              "L": ["Latest", IMG_LATEST],
              "Fixture": ["Fixture", IMG_FIXTURE]}

def debug(msg):
    '''Script for adding debug messages.

    Takes one argument:
    msg:    debug message to send to XBMC log
    '''

    xbmc.log(msg,xbmc.LOGDEBUG)

def getSelectedLeagues():
    '''Returns list of leagues selected by user in settings file.'''

    # Try to get list of selected leagues from settings file
    try: 
        
        # Get the settings value and convert to a list
        watchedleagues = json.loads(str(_S_("watchedleagues")))

    # if there's a problem
    except: 

        # Create an empty list (stops service from crashing)
        watchedleagues = []

    # Return this list
    return watchedleagues

def checkAlerts():
    '''Setting is "True" when alerts are disabled.

    Returns boolean:
    True:   Service should display alerts
    False:  Alerts are disabled
    '''

    return _S_("Alerts") != "true"

def serviceRunning():
    '''User should be able to deactivate alerts (rather than deactivating
        the service) via setting.

    Returns a boolean as to whether we should provide alerts or not.
    '''

    return True

def updateWatchedLeagues(matchdict, selectedleagues):
    '''Updates our active leagues to make sure that we're just looking at the
    leagues that the user wants.

    Takes 2 arguments:
    matchdict:          dictionary of leagues being watched
    selectedleagues:    list of league IDs chosen by user

    Returns updated dictionary object.
    '''

    # Build a list of leagues selected by user that are not in
    # our current dictionary
    newleagues = [l for l in selectedleagues if l not in matchdict]
    
    # Build a list of leagues in our dictionary that are no longer in
    # list of leagues selected by users
    removedleagues = [l for l in matchdict if l not in selectedleagues]

    # Loop through new leagues
    for l in newleagues:

        # Add a League object to the dictioanary
        matchdict[l] = League(l)

    # Loop through leaues to be removed
    for l in removedleagues:

        # Remove league from the dictionary
        matchdict.pop(l)

    # Return the dictionary
    return matchdict

def Notify(subject, message, image=None):
    '''Displays match notification.

    Take 3 arguments:
    subject:    subject line
    message:    message line
    image:      path to icon
    '''
    xbmc.executebuiltin('Notification(%s,%s,2000,%s)' % (subject,
                                                         message, 
                                                         image))

def checkMatch(match):
    '''Look at the match and work out what notification we want to show.

    Takes one argument:
    match:  footballscores.FootballMatch object
    '''

    # Has there been a goal?
    if match.Goal:

        # Gooooooooooooooooooooooooooooollllllllllllllll!
        Notify("GOAL!", str(match), IMG_GOAL)

    # Has the status changed? e.g. kick-off, half-time, full-time?
    if match.StatusChanged:

        # Get the relevant status info
        info = STATUS_DICT.get(match.status, STATUS_DICT["Fixture"])

        # Send the notification
        Notify(info[0], str(match), info[1])

def doUpdates(matchdict):
    '''Main function to updated leagues and check matches for updates.

    Takes one argument:
    matchdict:  dictionary of leagues being watchedleagues

    Returns updated dictionary
    '''

    # Loop through each league that we're following
    for league in matchdict:

        # Get the league to update each match
        matchdict[league].Update()

        # Loop through the matches
        for match in matchdict[league].LeagueMatches:

            # and check it for updates
            checkMatch(match)

    # Return the updated dicitonary object
    return matchdict


# Script starts here.
# Let's get some initial data before we enter main service loop

# Build dictionary of leagues we want to follow
matchdict = updateWatchedLeagues({}, getSelectedLeagues())

# Check if we need to show alerts or not.
alerts = checkAlerts()

# Variable for counting loop iterations
i = 0

# Main service loop - need to exit script cleanly if XBMC is shutting down
while not xbmc.abortRequested:

    # 5 seconds before we do main update, let's check and see if there are any
    # new leagues that we need to follow.
    # Also, check whether the user has enabled/disabled alerts
    if i == 11:
        matchdict = updateWatchedLeagues(matchdict, getSelectedLeagues())
        alerts = checkAlerts()

    # If user wants alerts and we've reached ou desired loop number...
    if alerts and not i:

        # Update our match dictionary and check for updates.
        matchdict = doUpdates(matchdict)
        
    # Sleep for 5 seconds (if this is longer, XBMC may not shut down cleanly.)
    xbmc.sleep(5000)

    # Increment our counter
    # 12 x 5000 = 60,000 i.e. scores update every 1 minute
    # Currently hard-coded - may look to change this.
    i = (i + 1) % 12
