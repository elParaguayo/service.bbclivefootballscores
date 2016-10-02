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
from threading import Lock

if sys.version_info >=  (2, 7):
    import json as json
else:
    import simplejson as json

import xbmc
import xbmcaddon
import xbmcgui

from resources.lib.footballscores import League
from resources.lib.notificationqueue import NotificationQueue
from resources.lib.service_settings import ServiceSettings
from resources.lib.utils import debug, localise

# Set the addon environment
_A_ = xbmcaddon.Addon("service.bbclivefootballscores")
_GET_ = _A_.getSetting
_SET_ = _A_.setSetting
pluginPath = _A_.getAddonInfo("path")
ADDON_PROFILE = xbmc.translatePath(_A_.getAddonInfo('profile')).decode('utf-8')

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

# Constants for identifying which notifications to display
NFY_GOALSCORER = 1
NFY_YELLOW = 2
NFY_RED = 4

SETTINGS_ALERTS = ("Alerts", )
SETTINGS_NOTIFICATIONS = ("AdditionalDetail", "AdvancedNotifications",
                          "ShowBookings", "ShowGoalscorer")
SETTINGS_NOTIFICATION_TIME = ("DisplayTime", )
SETTINGS_LEAGUES = ("watchedleagues", )
SETTING_REFRESH = ("RefreshTime", )

REFRESH_INTERVALS = (60, 90, 120, 150, 180, 300, 600, 900)

class SettingsMonitor(xbmc.Monitor):
    '''Handler to checking when settings are updated and triggering an
       appropriate callback.
    '''

    def __init__(self, *args, **kwargs):
        xbmc.Monitor.__init__(self)
        self.action = kwargs['action']
        self.lock = kwargs['lock']
        debug("Binding settings action to {0}".format(repr(self.action)))

    def onSettingsChanged(self):
        debug("Detected change in settings (NB may not be this addon)")
        try:
            self.lock.acquire()
            self.action()
        finally:
            self.lock.release()


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
        self.ADVANCED_NOTIFICATIONS = -1
        self.REFRESH_TIME = 12

        self.updated_needed = False

        # Create a notification queue object for handling notifications
        debug("Creating queue")
        self.queue = NotificationQueue()

        # Read the addon settings
        self.config = ServiceSettings("service.bbclivefootballscores")
        self.getSettings()

        self.lock = Lock()

        # Create a settings monitor
        debug("Starting settings monitor...")
        self.monitor = SettingsMonitor(action=self.queue_update,
                                       lock=self.lock)

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
        if any(x in SETTINGS_ALERTS for x in self.config._updated):
            self.checkAlerts()

        if any(x in SETTINGS_NOTIFICATIONS for x in self.config._updated):
            self.checkNotificationDetailLevel()

        if any(x in SETTINGS_LEAGUES for x in self.config._updated):
            self.updateWatchedLeagues()

        if any(x in SETTINGS_NOTIFICATION_TIME for x in self.config._updated):
            self.checkNotificationTime()

        if any(x in SETTING_REFRESH for x in self.config._updated):
            self.checkRefreshTime()

    def checkNotificationTime(self):
        '''Sets the length of time for which notifications should be
           displayed.
        '''
        try:
            #n = int(_GET_("DisplayTime"))
            n = int(self.config.DisplayTime)
        except ValueError:
            # Default is 2 seconds
            n = 2

        if n != (self.NOTIFY_TIME / 1000):
            debug("Notification time now {} seconds".format(n))
            self.NOTIFY_TIME = n * 1000
            self.queue.timeout = self.NOTIFY_TIME

    def checkRefreshTime(self):
        '''Sets the time required between updates'''
        try:
            idx = int(self.config.RefreshTime)
        except ValueError:
            idx = 0

        interval = REFRESH_INTERVALS[idx]

        debug("Update interval is now {} seconds.".format(interval))

        self.REFRESH_TIME = interval / 5

    def checkAlerts(self):
        '''Setting is "True" when alerts are disabled.
        '''
        #alerts = _GET_("Alerts") != "true"
        alerts = self.config.Alerts != "true"

        if alerts != self.SHOW_ALERTS:
            debug("Alerts now {}.".format("ON" if alerts else "OFF"))
            self.SHOW_ALERTS = alerts

    def queue_update(self):
        debug("Queuing settings update...")
        self.updated_needed = True

    def checkNotificationDetailLevel(self):
        '''Sets certain constants to determine how much detail is required for
           notifications.
        '''
        nfy_level = 0

        # d = _GET_("AdditionalDetail") == "true"
        # adv = _GET_("AdvancedNotifications") == "true"
        d = self.config.AdditionalDetail == "true"
        adv = self.config.AdvancedNotifications == "true"

        #gs = _GET_("ShowGoalscorer") == "true"
        gs = self.config.ShowGoalscorer == "true"
        if gs != self.SHOW_GOALSCORER:
            debug("Goal scorer alerts now {}.".format("ON" if gs else "OFF"))
            self.SHOW_GOALSCORER = gs
        if self.SHOW_GOALSCORER:
            nfy_level += NFY_GOALSCORER

        try:
            #bk = int(_A_.getSetting("ShowBookings"))
            bk = int(self.config.ShowBookings)
        except ValueError:
            bk = 0

        if bk != self.SHOW_BOOKINGS:
            debug("Bookings are now {}.".format(BOOKINGS[bk]))
            self.SHOW_YELLOW = bool(bk == 2)
            self.SHOW_RED = bool(bk != 0)
            self.SHOW_BOOKINGS = bk

        if self.SHOW_YELLOW:
            nfy_level += NFY_YELLOW

        if self.SHOW_RED:
            nfy_level += NFY_RED

        self.queue.set_level(nfy_level)

        dt = all([d, any([self.SHOW_GOALSCORER, self.SHOW_BOOKINGS])])

        if dt != self.DETAILED:
            level = "ON" if dt else "OFF"
            debug("Showing additional detail is now {}.".format(level))
            self.DETAILED = dt

        advanced = d and adv
        if advanced != self.ADVANCED_NOTIFICATIONS:
            level = "ON" if advanced else "OFF"
            debug("Advanced notifications are now {0}".format(level))
            self.queue.set_advanced(advanced)
            self.ADVANCED_NOTIFICATIONS = advanced

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
            #watchedleagues = json.loads(str(_GET_("watchedleagues")))
            watchedleagues = json.loads(self.config.watchedleagues)

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
        #match.goal = True
        if any([match.booking, match.redcard, match.goal, match.StatusChanged]):
            debug(u"Match needs processing... {}".format(repr(match)))
            self.queue.add(match)

    def checkTickers(self):
        '''Tickers are not a class property because they are implemented by a
           separate script.

           We therefore need to manually maintain a list of which windows have
           tickers and check to see it's correct.

           If a ticker cannot be found (i.e. it was implemented in a separate
           Kodi session) then it needs to be removed from the list.
        '''
        try:
            #tickers = json.loads(_GET_("currenttickers"))
            tickers = json.loads(self.config.currenttickers)
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

        #_SET_("currenttickers", json.dumps(tickers))
        self.config.currenttickers = json.dumps(tickers)

    def updateTickers(self):
        '''Updates the ticker text on all known tickers.'''

        try:
            #tickers = json.loads(_GET_("currenttickers"))
            tickers = json.loads(self.config.currenttickers)
        except ValueError:
            tickers = {}

        for k in tickers:

            w = xbmcgui.Window(int(k))
            c = w.getControl(tickers[k])
            c.reset()
            c.addLabel(self.ticker.decode("utf-8").replace("|", ","))

    def doUpdates(self):
        '''Main function to updated leagues and check matches for updates.

        Takes one argument:
        self.matchdict:  dictionary of leagues being watchedleagues
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
                    ticker += u"  "
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
            self.ticker = ticker.replace(",", "|").encode("utf-8")
            xbmc.executebuiltin("Skin.SetString(bbcscorestickertext, {})".format(self.ticker))
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
        while not self.monitor.abortRequested():

            if self.monitor.waitForAbort(5):
                break

            if self.updated_needed:
                try:
                    self.config._reload()
                    self.getSettings()
                finally:
                    self.updated_needed = False

            # If user wants alerts and we've reached our desired loop number...
            if not i:

                # Update our match dictionary and check for updates.
                debug("Checking scores...")

                try:
                    self.lock.acquire()
                    self.doUpdates()
                finally:
                    self.lock.release()

            # Sleep for 5 seconds
            # (if this is longer, XBMC may not shut down cleanly.)
            #xbmc.sleep(5000)

            # Increment our counter
            # will equal 0 when we hit our desired refresh time.
            i = (i + 1) % self.REFRESH_TIME


if __name__ == "__main__":
    scores_service = FootballScoresService()
    scores_service.run()

    # Clean exit
    scores_service = None
