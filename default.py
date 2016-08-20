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

# What bookings to show
BOOKINGS = {0: "OFF",
            1: "RED ONLY",
            2: "ALL"}

# STATUS_DICT object
# Format is {status: [status text, image path]}
STATUS_DICT = {"FT": ["Full Time", IMG_FT],
              "HT": ["Half Time", IMG_HT],
              "L": ["Latest", IMG_LATEST],
              "Fixture": ["Fixture", IMG_FIXTURE]}


# Define core generic funcitons

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
    xbmc.log(msg)  # ,xbmc.LOGDEBUG


class SettingsMonitor(xbmc.Monitor):
    '''Handler to checking when settings are updated and triggering an
       appropriate callback.
    '''

    def __init__(self, *args, **kwargs):
        xbmc.Monitor.__init__(self)
        self.action = kwargs['action']

    def onSettingsChanged(self):
        debug("Detected change in settings (NB may not be this addon)")
        self.action()


class FootballScoresService(object):
    '''Class definition for the football scoress service.

       Service will run on starting Kodi and will stop on exit.

       Settings are read on starting the service. A separate monitor instance is
       needed to update settings if a user changes them while the script is
       running.
    '''

    def __init__(self):
        '''Initialises the service object but does not start it.

           Reads settings and defines the necessary variables and objects.
        '''
        debug("Initialisings service...")

        # Define required constants and objects
        self.matchdict = {}
        self.ticker = ""
        self.SHOW_ALERTS = -1
        self.SHOW_GOALSCORER = -1
        self.SHOW_BOOKINGS = -1
        self.SHOW_YELLOW = -1
        self.SHOW_RED = -1
        self.DETAILED = -1
        self.NOTIFY_TIME = -1

        # Read the addon settings
        self.getSettings()

        # Create a notification queue object for handling notifications
        debug("Creating queue")
        self.queue = NotificationQueue()

        # Create a settings monitor
        debug("Starting settings monitor...")
        self.monitor = SettingsMonitor(action=self.getSettings)

        # Clear old tickers
        debug("Clearing tickers")
        self.checkTickers()

    def Notify(self, subject, message, image=None, timeout=2000):
        '''Displays match notification.

        Take 4 arguments:
        subject:    subject line
        message:    message line
        image:      path to icon
        timeoute:   display time in milliseconds
        '''
        self.queue.add(subject, message, image, timeout)

    def getSettings(self):
        '''Reads the addon settings and updates the scipt settings accordingly.

           This method should be handled by a monitor instance so that any
           changes made to settings while the service is running are also
           updated.
        '''
        debug("Checking settings...")
        self.updateWatchedLeagues()
        self.checkAlerts()
        self.checkNotificationDetailLevel()
        self.checkNotificationTime()

    def checkNotificationTime(self):
        '''Sets the length of time for which notifications should be
           displayed.
        '''
        try:
            n = int(_GET_("DisplayTime"))
        except ValueError:
            # Default is 2 seconds
            n = 2

        if n != (self.NOTIFY_TIME / 1000):
            debug("Notification time now {} seconds".format(n))
            self.NOTIFY_TIME = n * 1000

    def checkAlerts(self):
        '''Setting is "True" when alerts are disabled.
        '''
        alerts = _GET_("Alerts") != "true"

        if alerts != self.SHOW_ALERTS:
            debug("Alerts now {}.".format("ON" if alerts else "OFF"))
            self.SHOW_ALERTS = alerts

    def checkNotificationDetailLevel(self):
        '''Sets certain constants to determine how much detail is required for
           notifications.
        '''
        d = _GET_("AdditionalDetail") == "true"

        gs = _GET_("ShowGoalscorer") == "true"
        if gs != self.SHOW_GOALSCORER:
            debug("Goal scorer alerts now {}.".format("ON" if gs else "OFF"))
            self.SHOW_GOALSCORER = gs

        try:
            bk = int(_GET_("ShowBookings"))
        except ValueError:
            bk = 0

        if bk != self.SHOW_BOOKINGS:
            debug("Bookings are now {}.".format(BOOKINGS[bk]))
            self.SHOW_YELLOW = bool(self.SHOW_BOOKINGS == 2)
            self.SHOW_RED = bool(self.SHOW_BOOKINGS != 0)
            self.SHOW_BOOKINGS = bk

        dt = all([d, any([self.SHOW_GOALSCORER, self.SHOW_BOOKINGS])])

        if dt != self.DETAILED:
            level = "ON" if dt else "OFF"
            debug("Showing additional detail is now {}.".format(level))
            self.DETAILED = dt

    def updateWatchedLeagues(self):
        '''Updates our active leagues to make sure that we're just looking at
        the leagues that the user wants.
        '''
        selectedleagues = self.getSelectedLeagues()

        # Build a list of leagues selected by user that are not in
        # our current dictionary
        newleagues = [l for l in selectedleagues if l not in self.matchdict]

        # Build a list of leagues in our dictionary that are no longer in
        # list of leagues selected by users
        removedleagues = [l for l in self.matchdict if l not in selectedleagues]

        # Loop through new leagues
        for l in newleagues:

            # Add a League object to the dictioanary
            try:
                self.matchdict[l] = League(l, detailed=self.DETAILED)
            except TypeError:
                pass

        # Loop through leaues to be removed
        for l in removedleagues:

            # Remove league from the dictionary
            self.matchdict.pop(l)

        if newleagues:
            debug("Added new leagues: {}".format(newleagues))

        if removedleagues:
            debug("Removed leagues: {}".format(removedleagues))

        if newleagues or removedleagues:
            debug(u"LeagueList - {0}".format(self.matchdict))

    def getSelectedLeagues(self):
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

    def checkMatch(self, match):
        '''Look at the match and work out what notification we want to show.

        Takes one argument:
        match:  footballscores.FootballMatch object
        '''

        if match.booking:

            # Should we show notification?
            if (self.SHOW_YELLOW and self.DETAILED):
                try:
                    yellow = u" {1} ({0})".format(*match.LastYellowCard)
                except AttributeError:
                    yellow = None
            else:
                yellow = None

            self.Notify(u"YELLOW!{0}".format(yellow if yellow else u""),
                        unicode(match),
                        IMG_YELLOW,
                        timeout=self.NOTIFY_TIME)
            debug(u"Yellow Card: %s" % (unicode(match)))

        if match.redcard:

            # Should we show notification?
            if (self.SHOW_RED and self.DETAILED):
                try:
                    red = u" {1} ({0})".format(*match.LastRedCard)
                except AttributeError:
                    red = None
            else:
                red = None

            self.Notify(u"RED!{0}".format(red if red else u""),
                        unicode(match),
                        IMG_RED,
                        timeout=self.NOTIFY_TIME)
            debug(u"Red Card: %s" % (unicode(match)))

        # Has there been a goal?
        if match.Goal:

            # Gooooooooooooooooooooooooooooollllllllllllllll!

            # Should we show goalscorer?
            if (self.SHOW_GOALSCORER and self.DETAILED):
                try:
                    scorer = u" {0}".format(match.LastGoalScorer[1])
                except AttributeError:
                    scorer = None
            else:
                scorer = None

            self.Notify(u"GOAL!{0}".format(scorer if scorer else u""),
                        unicode(match),
                        IMG_GOAL,
                        timeout=self.NOTIFY_TIME)
            debug(u"GOAL: %s" % (unicode(match)))

        # Has the status changed? e.g. kick-off, half-time, full-time?
        if match.StatusChanged:

            # Get the relevant status info
            info = STATUS_DICT.get(match.status, STATUS_DICT["Fixture"])

            # Send the notification
            self.Notify(info[0], unicode(match), info[1],
                        timeout=self.NOTIFY_TIME)
            debug(u"STATUS: {0}".format(unicode(match)))

    def checkTickers(self):
        '''Tickers are not a class property because they are implemented by a
           separate script.

           We therefore need to manually maintain a list of which windows have
           tickers and check to see it's correct.

           If a ticker cannot be found (i.e. it was implemented in a separate
           Kodi session) then it needs to be removed from the list.
        '''
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

    def updateTickers(self):
        '''Updates the ticker text on all known tickers.'''

        try:
            tickers = json.loads(_GET_("currenttickers"))
        except ValueError:
            tickers = {}

        for k in tickers:

            w = xbmcgui.Window(int(k))
            c = w.getControl(tickers[k])
            c.reset()
            c.addLabel(self.ticker)

    def doUpdates(self):
        '''Main function to updated leagues and check matches for updates.

        Takes one argument:
        self.matchdict:  dictionary of leagues being watchedleagues

        Returns updated dictionary
        '''

        ticker = u""

        # Loop through each league that we're following
        for league in self.matchdict:

            # Make sure we only get additional information if we need it.
            for m in self.matchdict[league].LeagueMatches:
                m.detailed = self.DETAILED

            # Get the league to update each match
            self.matchdict[league].Update()

            if self.matchdict[league]:
                if ticker:
                    ticker += "  "
                lgn = u"[B]{0}[/B]: ".format(self.matchdict[league].LeagueName)
                mtc = u", ".join(unicode(m) for m
                                 in self.matchdict[league].LeagueMatches)
                ticker += lgn
                ticker += mtc

            # If we're showing alerts then let's check each match for updates
            if self.SHOW_ALERTS:

                # Loop through the matches
                for match in self.matchdict[league].LeagueMatches:

                    # and check it for updates
                    self.checkMatch(match)

        # If there have been any changes then we need to update the tickers
        if ticker != self.ticker:
            debug(u"Ticker: {}".format(ticker))
            self.ticker = ticker
            xbmc.executebuiltin("Skin.SetString(bbcscorestickertext, {})".format(self.ticker.replace(",", "|")))
            self.updateTickers()

    def run(self):
        '''Method to start the service.

           Service runs in a loop which is terminated when the user exits Kodi.
        '''

        # Variable for counting loop iterations
        i = 0

        # Main service loop - need to exit script cleanly if XBMC is shutting
        # down
        debug("Entering main loop...")
        while not xbmc.abortRequested:

            # If user wants alerts and we've reached our desired loop number...
            if self.SHOW_ALERTS and not i:

                # Update our match dictionary and check for updates.
                debug("Checking scores...")
                self.doUpdates()

            # Sleep for 5 seconds
            # (if this is longer, XBMC may not shut down cleanly.)
            xbmc.sleep(5000)

            # Increment our counter
            # 12 x 5000 = 60,000 i.e. scores update every 1 minute
            # Currently hard-coded - may look to change this.
            i = (i + 1) % 12


if __name__ == "__main__":
    scores_service = FootballScoresService()
    scores_service.run()
