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
    This module provides a class object to handle multiple notifications while
    honouring the timeout set by the user.
'''
import os
import Queue

try:
    from threading import Thread
    CAN_THREAD = True
except ImportError:
    from dummy_threading import Thread
    CAN_THREAD = False

import xbmcgui, xbmc, xbmcaddon

from .advanced_notification import createAdvancedNotification
from .utils import debug, localise

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


NOTIFY_STANDARD_DISPLAY = 0
NOTIFY_ADVANCED_PREPARE = 1
NOTIFY_ADVANCED_DISPLAY = 2

# Constants for identifying which notifications to display
NFY_GOALSCORER = 1
NFY_YELLOW = 2
NFY_RED = 4

# Event types for advanced notifications
EVENT_GOAL = 0
EVENT_YELLOW = 1
EVENT_RED = 2
EVENT_STATUS = 3

# STATUS_DICT object
# Format is {status: [status text, image path]}
STATUS_DICT = {"FT": ["Full Time", IMG_FT],
              "HT": ["Half Time", IMG_HT],
              "L": ["Latest", IMG_LATEST],
              "Fixture": ["Fixture", IMG_FIXTURE]}


class NotificationQueue(object):

    def __init__(self, timeout=2000, num_workers=5,
                 detailed=False, advanced=False):

        self.timeout = timeout
        self.num_workers = num_workers
        self.workers = []
        self.level = 0
        self.detailed = detailed
        self.advanced = advanced
        self.monitor = xbmc.Monitor()

        self.can_thread = CAN_THREAD
        # try:
        #     from threading import Thread
        #     self.can_thread = True
        # except ImportError:
        #     from dummy_threading import Thread
        #     self.can_thread = False

        ct = "can" if self.can_thread else "cannot"
        debug("Notifications {} thread.".format(ct))

        self.queue = Queue.Queue()
        self.worker_queue = Queue.Queue()
        self.dialog = xbmcgui.Dialog()
        self.process = Thread(target=self.__process)
        self.process.daemon = True
        self.process.start()

        if self.advanced:
            self.start_advanced_workers()

    def start_advanced_workers(self):

        if not self.workers:

            for _ in range(self.num_workers):
                worker = Thread(target=self._advancedNotificationWorker)
                worker.daemon = True
                worker.start()
                self.workers.append(worker)

    def set_advanced(self, advanced):

        self.advanced = advanced
        if self.advanced:
            self.start_advanced_workers()

    def set_level(self, level):
        self.level = level
        debug("Queue: Notification level: {0}".format(self.level))

    def Notify(self, title, message, icon=None, timeout=2000):

        self.dialog.notification(title, message, icon, timeout)

    # def add(self, match):
    #
    #     # if self.can_thread:
    #     #     self.queue.put((title, message, icon, timeout))
    #     # else:
    #     #     self.Notify(title, message, icon, timeout)
    #
    #     if self.advanced:
    #         pass
    #
    #     else:
    #         self.process_standard(match)

    def add(self, match):

        if match.booking:

            # Should we show notification?
            if self.level & NFY_YELLOW:

                try:
                    yellow = u"{0}: {1[1]} ({1[0]})".format(localise(32201),
                                                            match.LastYellowCard)
                except (TypeError, AttributeError):
                    yellow = u"{0}!".format(localise(32201))

                if self.advanced:
                    payload = (EVENT_YELLOW, yellow, match)
                    self.advanced_notification(*payload)

                else:
                    payload = (yellow,
                               unicode(match),
                               IMG_YELLOW,
                               self.timeout)
                    self.standard_notification(*payload)

                debug(u"Yellow Card: {}, {}".format(match, yellow))

        if match.redcard:

            # Should we show notification?
            if self.level & NFY_RED:

                try:
                    red = u"{0}: {1[1]} ({1[0]})".format(localise(32202),
                                                         match.LastRedCard)
                except (TypeError, AttributeError):
                    red = u"{0}!".format(localise(32202))

                if self.advanced:
                    payload = (EVENT_RED, red, match)
                    self.advanced_notification(*payload)

                else:
                    payload = (red,
                               unicode(match),
                               IMG_RED,
                               self.timeout)
                    self.standard_notification(*payload)

                debug(u"Red Card: {}, {}".format(match, red))

        # Has there been a goal?
        if match.Goal:

            # Gooooooooooooooooooooooooooooollllllllllllllll!

            # Should we show goalscorer?
            if self.level & NFY_GOALSCORER:

                simple = False

                try:
                    scorer = u"{0}: {1}".format(localise(32200),
                                                match.LastGoalScorer[1])
                except (TypeError, AttributeError):
                    simple = True
                    scorer = u"{0}!".format(localise(32200))
            else:
                simple = True
                scorer = u"{0}!".format(localise(32200))

            if self.advanced:
                payload = (EVENT_GOAL, scorer, match, simple)
                self.advanced_notification(*payload)

            else:
                payload = (scorer,
                           unicode(match),
                           IMG_GOAL,
                           self.timeout)
                self.standard_notification(*payload)

            debug(u"GOAL: {}, {}".format(match, scorer))

        # Has the status changed? e.g. kick-off, half-time, full-time?
        if match.StatusChanged:

            # Get the relevant status info
            info = STATUS_DICT.get(match.status, STATUS_DICT["Fixture"])

            if self.advanced:
                payload = (EVENT_STATUS, info[0], match)
                self.advanced_notification(*payload)

            else:
                # Send the notification
                payload = (info[0], unicode(match), info[1],
                           self.timeout)
                self.standard_notification(*payload)

            debug(u"STATUS: {0}".format(unicode(match)))

    def standard_notification(self, title, message, icon=None, timeout=2000):
        if self.can_thread:
            self.queue.put((NOTIFY_STANDARD_DISPLAY,
                            (title, message, icon, timeout)))
        else:
            self.Notify(title, message, icon, timeout)

    def advanced_notification(self, event_type, title, match, simple=False):
        if self.can_thread and self.workers:
            self.worker_queue.put((NOTIFY_ADVANCED_PREPARE,
                                   (event_type, title, match, simple)))
        else:
            self.AdvancedNotify(event_type, title, match, simple)

    def showAdvanced(self, filename):
        xbmc.executebuiltin("Skin.SetString(bbcscoresnotification, "
                            "{})".format(filename))
        xbmc.executebuiltin("Skin.SetBool(showscoredialog)")
        xbmc.sleep(self.timeout + 250)
        xbmc.executebuiltin("Skin.Reset(showscoredialog)")
        xbmc.sleep(250)
        #os.remove(filename)

    def __process(self):

        while not self.monitor.abortRequested():
            while not (self.queue.empty() or self.monitor.abortRequested()):
                self.busy = True
                mode, payload = self.queue.get()
                if mode == NOTIFY_STANDARD_DISPLAY:
                    t,m,i,d = payload
                    self.Notify(t, m, i, d)
                    xbmc.sleep(d)

                elif mode == NOTIFY_ADVANCED_DISPLAY:
                    self.showAdvanced(payload)

            if self.monitor.waitForAbort(0.5):
                break

    def _advancedNotificationWorker(self):

        while not self.monitor.abortRequested():
            while not (self.worker_queue.empty() or self.monitor.abortRequested()):
                action, payload = self.worker_queue.get()
                if action == NOTIFY_ADVANCED_PREPARE:
                    advanced_notification = createAdvancedNotification(*payload)
                    self.queue.put((NOTIFY_ADVANCED_DISPLAY,
                                    advanced_notification))
                self.worker_queue.task_done()

            if self.monitor.waitForAbort(0.5):
                break
