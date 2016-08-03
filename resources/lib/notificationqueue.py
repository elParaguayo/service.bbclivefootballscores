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

import Queue

import xbmcgui, xbmc

class NotificationQueue(object):

    def __init__(self):

        try:
            from threading import Thread
            self.can_thread = True
        except ImportError:
            from dummy_threading import Thread
            self.can_thread = False

        self.queue = Queue.Queue()
        self.dialog = xbmcgui.Dialog()
        self.process = Thread(target=self.__process)
        self.process.daemon = True
        self.process.start()

    def Notify(self, title, message, icon=None, timeout=2000):

        self.dialog.notification(title, message, icon, timeout)

    def add(self, title, message, icon=None, timeout=2000):

        if self.can_thread:
            self.queue.put((title, message, icon, timeout))
        else:
            self.Notify(title, message, icon, timeout)

    def __process(self):

        while not xbmc.abortRequested:
            while not self.queue.empty():
                self.busy = True
                t,m,i,d = self.queue.get()
                self.Notify(t, m, i, d)
                xbmc.sleep(d)

            xbmc.sleep(500)
