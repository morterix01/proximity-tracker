[app]

# (str) Title of your application
title = Proximity Alert

# (str) Package name
package.name = proximityalert

# (str) Package domain (needed for android/ios packaging)
package.domain = org.proximity

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,json,mp3,pkl

# (str) Application versioning (method 1)
version = 4.4

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = python3,kivy,openssl,requests,urllib3,charset-normalizer,idna,locationsharinglib,cachetools,plyer,beautifulsoup4,pytz,six,pyjnius

# (str) Custom source folders for requirements
# packagelist.include_patterns = 

# (list) Garden requirements
#garden_requirements =

# (str) Presplash of the application
#presplash.filename = %(source.dir)s/data/presplash.png

# (str) Icon of the application
#icon.filename = %(source.dir)s/data/icon.png

# (list) Supported orientations
# Valid values are: landscape, portrait, portrait-upside-down, landscape-left, landscape-right
orientation = portrait

# (list) Permissions
android.permissions = INTERNET, ACCESS_FINE_LOCATION, ACCESS_COARSE_LOCATION, WAKE_LOCK, FOREGROUND_SERVICE, ACCESS_BACKGROUND_LOCATION

# (int) Target Android API, should be as high as possible.
android.api = 31

# (int) Minimum API your APK will support.
android.minapi = 21

# (str) Android NDK version to use
#android.ndk = 25b

# (str) Android SDK directory
#android.sdk = /path/to/android/sdk

# (str) Android NDK directory
#android.ndk_path = /path/to/android/ndk

# (bool) Use --private data storage (True) or --dir public storage (False)
android.private_storage = True

# (list) List of service to declare
#services = ProximityService:service.py

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = off, 1 = on)
warn_on_root = 1

# (str) Path to build work directory, if not set it defaults to .buildozer in the project directory.
#build_dir = ./.buildozer

# (str) Path to build output directory, if not set it defaults to bin in the project directory.
#bin_dir = ./bin
