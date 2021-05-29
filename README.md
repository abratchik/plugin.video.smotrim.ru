# KODI addon for Smotrim.ru

This is Kodi video addon for viewing video from the site
[Smotrim.ru](https://Smotrim.ru). 

If you have any questions of feedback please post in on the 
forum XBMC.ru [here](http://xbmc.ru/forum/showthread.php?t=23431).

## Compatibility
The addon as been tested on 
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

## Disclaimer
This is a non-commercial community-supported addon for the Smotrim.ru web site.
It has been created for watching Russian programs on the TV screen, just for fun and has no relation
to the VGTRK company.

License: [GPL v.3](http://www.gnu.org/copyleft/gpl.html)
