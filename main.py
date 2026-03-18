# filepath: main.py
import os
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-web-security --ignore-certificate-errors --autoplay-policy=no-user-gesture-required"

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings

from ui.main_window import MyToolApp

if __name__ == "__main__":
    app = QApplication(sys.argv)

    profile = QWebEngineProfile("XXT_Auto_Profile", app)

    project_dir = os.path.dirname(os.path.abspath(__file__))
    profile_dir = os.path.join(project_dir, "web_profile")
    cache_dir = os.path.join(profile_dir, "cache")
    os.makedirs(cache_dir, exist_ok=True)

    profile.setPersistentStoragePath(profile_dir)
    profile.setCachePath(cache_dir)
    profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.DiskHttpCache)
    profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies)

    settings = profile.settings()
    settings.setAttribute(QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, False)
    settings.setAttribute(QWebEngineSettings.WebAttribute.AllowRunningInsecureContent, True)
    settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)

    window = MyToolApp(web_profile=profile)
    window.show()
    sys.exit(app.exec())