# coding=utf-8
# Module: streamextractor
# Author: Alex Bratchik
# Created on: 03.04.2021
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import xbmc
import YDStreamExtractor as ydse
import YoutubeDLWrapper

from yd_private_libs import util

from urllib.parse import urlencode


def getVideoInfo(url, quality=None, resolve_redirects=False):
    """
    Returns a VideoInfo object or None.
    Quality is 0=SD, 1=720p, 2=1080p, 3=Highest Available
    and represents a maximum.
    """

    if resolve_redirects:
        try:
            url = ydse.resolve_http_redirect(url)
        except Exception:
            xbmc.log('_getYoutubeDLVideo(): Failed to resolve URL %s' % url, xbmc.LOGERROR)
            return None

    ytdl = YoutubeDLWrapper._getYTDL()
    ytdl.clearDownloadParams()
    try:
        r = ytdl.extract_info(url, download=False)
    except YoutubeDLWrapper.DownloadError:
        return None
    urls = _selectVideoQuality(r, quality)
    if not urls:
        return None
    info = YoutubeDLWrapper.VideoInfo(r.get('id', ''))
    info._streams = urls
    info.title = r.get('title', urls[0]['title'])
    info.description = r.get('description', '')
    info.thumbnail = r.get('thumbnail', urls[0]['thumbnail'])
    info.sourceName = r.get('extractor', '')
    info.info = r
    return info


def _selectVideoQuality(r, quality=None):

    if quality is None:
        quality = util.getSetting('video_quality', 1)

    disable_dash = util.getSetting('disable_dash_video', True)
    skip_no_audio = util.getSetting('skip_no_audio', True)

    entries = r.get('entries') or [r]

    minHeight, maxHeight = _getQualityLimits(quality)

    xbmc.log("minHeight=%s, maxHeight=%s" % (minHeight, maxHeight), xbmc.LOGDEBUG)

    xbmc.log('Quality: {0}'.format(quality), xbmc.LOGDEBUG)

    urls = []
    idx = 0
    for entry in entries:

        defFormat = None
        defMax = 0
        defPref = -1000
        prefFormat = None
        prefMax = 0
        prefPref = -1000

        index = {}
        formats = entry.get('formats') or [entry]

        for i in range(len(formats)):
            index[formats[i]['format_id']] = i

        keys = sorted(index.keys())
        fallback = formats[index[keys[0]]]
        for fmt in keys:
            fdata = formats[index[fmt]]
            print(fdata)

            if 'height' not in fdata:
                # trying to assume resoliution by bitrate
                if 'tbr' in fdata:
                    tbr = int(fdata['tbr'])
                    fdata['preference'] = 2  # preference to HLS
                    if tbr in range(800, 1199):
                        fdata['height'] = 480
                    elif tbr in range(1200, 1799):
                        fdata['height'] = 720
                    elif tbr in range(1800, 4500):
                        fdata['height'] = 1080
                    else:
                        continue
                else:
                    continue
            elif disable_dash and 'dash' in fdata.get('format_note', '').lower():
                continue
            elif skip_no_audio and fdata.get('acodec', '').lower() == 'none':
                continue

            h = fdata['height']
            if h is None:
                h = 1
            p = fdata.get('preference', 1)
            if p is None:
                p = 1
            if h >= minHeight and h <= maxHeight:
                if (h >= prefMax and p > prefPref) or (h > prefMax and p >= prefPref):
                    prefMax = h
                    prefPref = p
                    prefFormat = fdata
            elif (h >= defMax and h <= maxHeight and p > defPref) or (h > defMax and h <= maxHeight and p >= defPref):
                defMax = h
                defFormat = fdata
                defPref = p

        formatID = None
        if prefFormat:
            info = prefFormat
            logBase = '[{3}] Using Preferred Format: {0} ({1}x{2})'
        elif defFormat:
            info = defFormat
            logBase = '[{3}] Using Default Format: {0} ({1}x{2})'
        else:
            info = fallback
            logBase = '[{3}] Using Fallback Format: {0} ({1}x{2})'
        url = info['url']
        formatID = info['format_id']
        xbmc.log(logBase.format(formatID,
                                info.get('width', '?'),
                                info.get('height', '?'),
                                entry.get('title', '').encode('ascii', 'replace')),
                 xbmc.LOGDEBUG)
        if url.find("rtmp") == -1:
            url += '|' + urlencode(
                {'User-Agent': entry.get('user_agent') or YoutubeDLWrapper.std_headers['User-Agent']})
        else:
            url += ' playpath=' + fdata['play_path']
        new_info = dict(entry)
        new_info.update(info)
        urls.append(
            {
                'xbmc_url': url,
                'url': info['url'],
                'title': entry.get('title', ''),
                'thumbnail': entry.get('thumbnail', ''),
                'formatID': formatID,
                'idx': idx,
                'ytdl_format': new_info
            }
        )
        idx += 1
    return urls


def _getQualityLimits(quality):
    minHeight = 0
    maxHeight = 480
    if quality > 2:
        minHeight = 1081
        maxHeight = 999999
    elif quality > 1:
        minHeight = 721
        maxHeight = 1080
    elif quality > 0:
        minHeight = 481
        maxHeight = 720
    return minHeight, maxHeight
