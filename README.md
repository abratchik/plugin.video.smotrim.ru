# KODI addon for Smotrim.ru
[![en](https://img.shields.io/badge/lang-en-red.svg)](https://github.com/abratchik/plugin.video.smotrim.ru/blob/Leia/README.md)
[![ru-ru](https://img.shields.io/badge/lang-ru--ru-green.svg)](https://github.com/abratchik/plugin.video.smotrim.ru/blob/Leia/README.ru-ru.md)


This is Kodi video addon for viewing video from the site
[Smotrim.ru](https://Smotrim.ru). 

If you have any questions of feedback please post in on the 
forum XBMC.ru [here](http://xbmc.ru/forum/showthread.php?t=23431).

## Compatibility
The addon has been tested on 
- Kodi Leia under Ubuntu 18.04 LTS.
- Kodi Matrix under Ubuntu 20.04 LTS
- Kodi Matrix on Android v9 Pie
- Kodi Matrix on macOS BigSur 11.1
- Kodi Matrix on Windows 10 

## Installation 
1. Download  [this file](https://abratchik.github.io/kodi.repository/matrix/repository.abratchik/repository.abratchik-1.0.2.zip)
2. Navigate to **System/Add-ons/Install from the zip file** and 
   specify the file downloaded on the previous step. 
3. Navigate to **System/Add-ons/Alex Bratchik Kodi repository/
   Video add-ons**, click on "Smotrim.ru" and install it.
   
That's all. Enjoy :)

## User registration
Starting from the release 1.0.18, the addon supports user registration with
the mobile number. Registration is triggered whenever a valid mobile number is
specified in the addon settings.

At this point, mostly Russian mobile numbers accepted by the web site Smitrim.ru,
any other mobile may not work, unfortunately. In case if you don't have such
number, please leave the Phone number in the addon settings blank.

## Watching Live TV
Starting version 1.1.11, the addon supports Live TV streaming. Live TV streams
are available only for some channels and may be not accessible outside Russia.

Navigation to the live TV: Channels > [ChannelName] > Live TV. 

### Integration with IPTV Manager
Starting version 1.1.15, the addon supports ITPV Manager integration. Enabling 
integration is done as follows:

1. Open the addon Settings, open Interface tab. If the IPTV Manager is not 
   installed, select the option **Install IPTV Manager** and install it along with 
   dependencies.
2. Turn the integration with IPTV manager ON.
3. Open IPTV manager Settings. Go to IPTV Simple tab and ensure that IPTV Simple
   is managed automatically by the IPTV Manager
4. In the TV Channles tab, run the update of TV playlist and EPG. This may take
   2-3 min, depending on your hardware and network speed

After this you should see the list of channels with EPG under Live TV main menu of
Kodi.

## Resolution of video playback issues
The site smotrim.ru is streaming HD content, which may require additional
configuration of the Kodi system. If you are experiencing unstable 
video, skipping fragments or slow start of the video, it is recommended to 
modify the cache parameters as follows:

````
memorysize = 41943040
readfactor = 10
````

You can set these parameters by manually editing [advancedsettings.xml](https://kodi.wiki/view/Advancedsettings.xml#cache)
file. Most conveniently it can be done with help of another plugin,
[Unlock Advanced Settings](https://github.com/abratchik/script.unlock.advancedsettings),
which you can install from the [same repository](https://abratchik.github.io/kodi.repository/matrix/repository.abratchik/repository.abratchik-1.0.2.zip)
Once installed, please go to **Cache** section, change the parameters, save
and restart Kodi. After that the video playback shall be smoother.

Some videos may not play correctly in the "auto" mode of video quality selection. In this
case it is recommended to set the video quality explicitly, corresponding to the resolution
of your monitor, and the Internet connection speed:

- fhd-wide (1920x1080)
- hd-wide (1280x720)
- high-wide (960x540)
- medium-wide (640x360)
- low-wide (416x243)


## Disclaimer
This is a non-commercial community-supported addon for the Smotrim.ru web site.
It has been created for watching Russian programs on the TV screen, just for fun and has no relation
to the VGTRK company.

License: [GPL v.3](http://www.gnu.org/copyleft/gpl.html)
