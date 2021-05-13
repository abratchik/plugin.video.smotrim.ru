# -*- coding: utf-8 -*-
# Module: kodiplayer
# Created on: 03.04.2021
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import xbmc


class KodiPlayer(xbmc.Player):
    """ A custom Player object to check if Playback has started """

    def __init__(self):
        """ Initialises a custom Player object
        """
        xbmc.Player.__init__(self)

        self.__monitor = xbmc.Monitor()
        self.__playBackEventsTriggered = False  # pylint: disable=invalid-name
        self.__playPlayBackStoppedEventsTriggered = False  # pylint: disable=invalid-name
        self.__pollInterval = 1  # pylint: disable=invalid-name

    def waitForPlayBack(self, url=None, time_out=30):  # pylint: disable=invalid-name

        xbmc.log("Player: Waiting for playback", xbmc.LOGDEBUG)
        if self.__is_url_playing(url):
            self.__playBackEventsTriggered = True
            xbmc.log("Player: Already Playing", xbmc.LOGDEBUG)
            return True

        for i in range(0, int(time_out / self.__pollInterval)):
            if self.__monitor.abortRequested():
                xbmc.log("Player: Abort requested (%s)" % i * self.__pollInterval, xbmc.LOGDEBUG)
                return False

            if self.__is_url_playing(url):
                xbmc.log("Player: PlayBack started (%s)" % i * self.__pollInterval, xbmc.LOGDEBUG)
                return True

            if self.__playPlayBackStoppedEventsTriggered:
                xbmc.log("Player: PlayBackStopped triggered while waiting for start.", xbmc.LOGWARNING)
                return False

            self.__monitor.waitForAbort(self.__pollInterval)
            xbmc.log("Player: Waiting for an abort (%s)" % i * self.__pollInterval, xbmc.LOGDEBUG)

        xbmc.log("Player: time-out occurred waiting for playback (%s)" % time_out, xbmc.LOGWARNING)
        return False

    def onAVStarted(self):  # pylint: disable=invalid-name
        """ Will be called when Kodi has a video or audiostream """
        xbmc.log("Player: [onAVStarted] called", xbmc.LOGDEBUG)
        self.__playback_started()

    def onPlayBackStopped(self):  # pylint: disable=invalid-name
        """ Will be called when [user] stops Kodi playing a file """
        xbmc.log("Player: [onPlayBackStopped] called", xbmc.LOGDEBUG)
        self.__playback_stopped()

    def onPlayBackError(self):  # pylint: disable=invalid-name
        """ Will be called when playback stops due to an error. """
        xbmc.log("Player: [onPlayBackError] called", xbmc.LOGDEBUG)
        self.__playback_stopped()

    def __playback_stopped(self):
        """ Sets the correct flags after playback stopped """
        self.__playBackEventsTriggered = False
        self.__playPlayBackStoppedEventsTriggered = True

    def __playback_started(self):
        """ Sets the correct flags after playback started """
        self.__playBackEventsTriggered = True
        self.__playPlayBackStoppedEventsTriggered = False

    def __is_url_playing(self, url):
        """ Checks whether the given url is playing
        :param str url: The url to check for playback.
        :return: Indication if the url is actively playing or not.
        :rtype: bool
        """
        if not self.isPlaying():
            xbmc.log("Player: Not playing", xbmc.LOGDEBUG)
            return False

        if not self.__playBackEventsTriggered:
            xbmc.log("Player: Playing but the Kodi events did not yet trigger", xbmc.LOGDEBUG)
            return False

        # We are playing
        if url is None or url.startswith("plugin://"):
            xbmc.log("Player: No valid URL to check playback against: %s" % url, xbmc.LOGDEBUG)
            return True

        playing_file = self.getPlayingFile()
        xbmc.log("Player: Checking \n'%s' vs \n'%s'" % (url, playing_file), xbmc.LOGDEBUG)
        return url == playing_file
