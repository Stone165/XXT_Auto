# filepath: main.py
import os
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-web-security --ignore-certificate-errors --autoplay-policy=no-user-gesture-required"

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings, QWebEngineScript

from ui.main_window import MyToolApp

if __name__ == "__main__":
    sys.argv.append("--autoplay-policy=no-user-gesture-required")
    sys.argv.append("--disable-web-security")
    sys.argv.append("--ignore-certificate-errors")

    app = QApplication(sys.argv)

    profile = QWebEngineProfile.defaultProfile()
    settings = profile.settings()
    
    settings.setAttribute(QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, False)
    settings.setAttribute(QWebEngineSettings.WebAttribute.AllowRunningInsecureContent, True)
    settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)

    window = MyToolApp()
    window.show()
    sys.exit(app.exec())