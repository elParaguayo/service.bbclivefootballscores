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
'''

import os
import sys

if sys.version_info >=  (2, 7):
    import json as json
else:
    import simplejson as json

import xbmc
import xbmcaddon
import xbmcgui

from resources.lib.footballscores import League
from resources.lib.notificationqueue import NotificationQueue

# Set the addon environment
_A_ = xbmcaddon.Addon("service.bbclivefootballscores")
_GET_ = _A_.getSetting
_SET_ = _A_.setSetting
pluginPath = _A_.getAddonInfo("path")

# Set some constants

# Define our images
IMG_GOAL = os.path.join(pluginPath, "resources", "media", "goal.png")
IMG_FT = os.path.join(pluginPath, "resources", "media", "whistle.png")
IMG_LATEST = os.path.join(pluginPath, "resources", "media" ,"football.png")
IMG_HT = os.path.join(pluginPath, "resources", "media", "ht.png")
IMG_FIXTURE = os.path.join(pluginPath, "resources", "media" , "fixture.png")
IMG_YELLOW = os.path.join(pluginPath, "resources", "media", "yellow-card.png")
IMG_RED = os.path.join(pluginPath, "resources", "media", "red-card.png")

# Notification display time
n = int(_GET_("DisplayTime"))
NOTIFY_TIME = n * 1000

# Additional detail
d = _GET_("AdditionalDetail") == "true"
SHOW_GOALSCORER = _GET_("ShowGoalscorer") == "true"
SHOW_BOOKINGS = int(_GET_("ShowBookings"))
SHOW_YELLOW = bool(SHOW_BOOKINGS == 2)
SHOW_RED = bool(SHOW_BOOKINGS != 0)
DETAILED = all([d, any([SHOW_GOALSCORER, SHOW_BOOKINGS])])

# STATUS_DICT object
# Format is {status: [status text, image path]}
STATUS_DICT = {"FT": ["Full Time", IMG_FT],
              "HT": ["Half Time", IMG_HT],
              "L": ["Latest", IMG_LATEST],
              "Fixture": ["Fixture", IMG_FIXTURE]}

def localise(id):
    '''Gets localised string.

    Shamelessly copied from service.xbmc.versioncheck
    '''
    string = _A_.getLocalizedString(id).encode( 'utf-8', 'ignore' )
    return string

def debug(msg):
    '''Script for adding debug messages.

    Takes one argument:
    msg:    debug message to send to XBMC log
    '''

    msg = u"bbclivefootballscores: {0}".format(msg).encode("ascii", "ignore")
    xbmc.log(msg,xbmc.LOGDEBUG)

def getSelectedLeagues():
    '''Returns list of leagues selected by user in settings file.'''

    # Try to get list of selected leagues from settings file
    try:

        # Get the settings value and convert to a list
        watchedleagues = json.loads(str(_GET_("watchedleagues")))

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

    return _GET_("Alerts") != "true"

def checkNotificationDetailLevel():
    '''Sets certain constants to determine how much detail is required for
       notifications.

       Returns a tuple which should set the following variables:
       SHOW_GOALSCORER
       SHOW_BOOKINGS
       SHOW_YELLOW
       SHOW_RED
       DETAILED
    '''
    d = _GET_("AdditionalDetail") == "true"
    SHOW_GOALSCORER = _GET_("ShowGoalscorer") == "true"
    SHOW_BOOKINGS = int(_GET_("ShowBookings"))
    SHOW_YELLOW = bool(SHOW_BOOKINGS == 2)
    SHOW_RED = bool(SHOW_BOOKINGS != 0)
    DETAILED = all([d, any([SHOW_GOALSCORER, SHOW_BOOKINGS])])

    return SHOW_GOALSCORER, SHOW_BOOKINGS, SHOW_YELLOW, SHOW_RED, DETAILED

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
        try:
            matchdict[l] = League(l, detailed=DETAILED)
        except TypeError:
            pass

    # Loop through leaues to be removed
    for l in removedleagues:

        # Remove league from the dictionary
        matchdict.pop(l)

    # Return the dictionary
    return matchdict

def Notify(subject, message, image=None, timeout=2000):
    '''Displays match notification.

    Take 4 arguments:
    subject:    subject line
    message:    message line
    image:      path to icon
    timeoute:   display time in milliseconds
    '''
    queue.add(subject, message, image, timeout)

def checkMatch(match):
    '''Look at the match and work out what notification we want to show.

    Takes one argument:
    match:  footballscores.FootballMatch object
    '''

    if match.booking:

        # Should we show notification?
        if (SHOW_YELLOW and DETAILED):
            yellow = u" {1} ({0})".format(*match.LastYellowCard)
        else:
            yellow = None

        Notify(u"YELLOW!{0}".format(yellow if yellow else u""),
               str(match),
               IMG_YELLOW,
               timeout=NOTIFY_TIME)
        debug(u"Yellow Card: %s" % (unicode(match)))

    if match.redcard:

        # Should we show notification?
        if (SHOW_RED and DETAILED):
            red = u" {1} ({0})".format(*match.LastRedCard)
        else:
            red = None

        Notify(u"RED!{0}".format(red if red else u""),
               str(match),
               IMG_RED,
               timeout=NOTIFY_TIME)
        debug(u"Red Card: %s" % (unicode(match)))

    # Has there been a goal?
    if match.Goal:

        # Gooooooooooooooooooooooooooooollllllllllllllll!

        # Should we show goalscorer?
        if (SHOW_GOALSCORER and DETAILED):
            scorer = u" {0}".format(match.LastGoalScorer[1])
        else:
            scorer = None

        Notify(u"GOAL!{0}".format(scorer if scorer else u""),
               str(match),
               IMG_GOAL,
               timeout=NOTIFY_TIME)
        debug(u"GOAL: %s" % (unicode(match)))


    # Has the status changed? e.g. kick-off, half-time, full-time?
    if match.StatusChanged:

        # Get the relevant status info
        info = STATUS_DICT.get(match.status, STATUS_DICT["Fixture"])

        # Send the notification
        Notify(info[0], unicode(match), info[1], timeout=NOTIFY_TIME)
        debug(u"STATUS: {0}".format(unicode(match)))

def checkTickers():

    try:
        tickers = json.loads(_GET_("currenttickers"))
    except ValueError:
        tickers = {}

    d = []

    for k in tickers:

        w = xbmcgui.Window(int(k))
        try:
            c = w.getControl(tickers[k])
        except RuntimeError:
            d.append(k)

    for k in d:
        tickers.pop(k)

    _SET_("currenttickers", json.dumps(tickers))


def updateTickers(text):

    try:
        tickers = json.loads(_GET_("currenttickers"))
    except ValueError:
        tickers = {}

    for k in tickers:

        w = xbmcgui.Window(int(k))
        c = w.getControl(tickers[k])
        c.reset()
        c.addLabel(text)


    _SET_("ticker", text)


def doUpdates(matchdict):
    '''Main function to updated leagues and check matches for updates.

    Takes one argument:
    matchdict:  dictionary of leagues being watchedleagues

    Returns updated dictionary
    '''

    ticker = u""

    # Loop through each league that we're following
    for league in matchdict:

        # Make sure we only get additional information if we need it.
        for m in matchdict[league].LeagueMatches:
            m.detailed = DETAILED

        # Get the league to update each match
        matchdict[league].Update()

        if matchdict[league]:
            if ticker:
                ticker += "  "
            ticker += u"[B]{0}[/B]: ".format(matchdict[league].LeagueName)
            ticker += u", ".join(unicode(m) for m in matchdict[league].LeagueMatches)

        # Loop through the matches
        for match in matchdict[league].LeagueMatches:

            # and check it for updates
            checkMatch(match)

    debug(ticker)
    updateTickers(ticker)
    # xbmc.executebuiltin(u"skin.setstring(tickertext,{0})".format(ticker))

    # Return the updated dicitonary object
    return matchdict


# Script starts here.
# Let's get some initial data before we enter main service loop

# Build dictionary of leagues we want to follow
matchdict = updateWatchedLeagues({}, getSelectedLeagues())
debug(u"LeagueList - {0}".format(matchdict))

# Check if we need to show alerts or not.
alerts = checkAlerts()

# Clear old tickers
checkTickers()

# Variable for counting loop iterations
i = 0

# Create a notification queue object
queue = NotificationQueue()

# Main service loop - need to exit script cleanly if XBMC is shutting down
debug("Entering main loop...")
while not xbmc.abortRequested:

    # 5 seconds before we do main update, let's check and see if there are any
    # new leagues that we need to follow.
    # Also, check whether the user has enabled/disabled alerts
    if i == 11:
        matchdict = updateWatchedLeagues(matchdict, getSelectedLeagues())
        alerts = checkAlerts()
        (SHOW_GOALSCORER,
         SHOW_BOOKINGS,
         SHOW_YELLOW,
         SHOW_RED,
         DETAILED) = checkNotificationDetailLevel()

    # If user wants alerts and we've reached ou desired loop number...
    if alerts and not i:

        # Update our match dictionary and check for updates.
        debug("Checking scores...")
        matchdict = doUpdates(matchdict)

    # Sleep for 5 seconds (if this is longer, XBMC may not shut down cleanly.)
    xbmc.sleep(5000)

    # Increment our counter
    # 12 x 5000 = 60,000 i.e. scores update every 1 minute
    # Currently hard-coded - may look to change this.
    i = (i + 1) % 12
