# filepath: ui/browser_view.py
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage
from PySide6.QtCore import QUrl
import os

class CustomWebPage(QWebEnginePage):
    def __init__(self, profile, parent_browser):
        super().__init__(profile, parent_browser)
        self.parent_browser = parent_browser # 保存对 AutoFitWebView 的引用

    def acceptNavigationRequest(self, url, _type, isMainFrame):
        print(f"尝试导航至: {url.toString()}")
        return super().acceptNavigationRequest(url, _type, isMainFrame)

    def createWindow(self, _type):
        if hasattr(self.parent_browser, 'new_tab_callback') and self.parent_browser.new_tab_callback:
            new_browser = self.parent_browser.new_tab_callback()
            return new_browser.page()
        return super().createWindow(_type)
    
    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        # 屏蔽无用警告
        if "size detected as NaN" in message or "Element.addUnits" in message:
            return 
            
        # 拦截 JS 发来的进度报告，转交给 Python 控制台
        if "[SYS_PROGRESS]" in message:
            clean_msg = message.replace("[SYS_PROGRESS]", "").strip()
            # 如果有绑定的控制台打印函数，就调它
            if hasattr(self.parent_browser, 'log_callback') and self.parent_browser.log_callback:
                self.parent_browser.log_callback(clean_msg + "\n")
            return

class AutoFitWebView(QWebEngineView):
    def __init__(self, base_width=1280, new_tab_callback=None, log_callback=None, profile=None):
        super().__init__()
        self.base_width = base_width
        self.new_tab_callback = new_tab_callback
        self.log_callback = log_callback 
        
        if profile is None:
            profile = QWebEngineProfile.defaultProfile()

        user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        profile.setHttpUserAgent(user_agent)
        
        self.setPage(CustomWebPage(profile, self))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        current_width = self.width()
        zoom_factor = max(0.3, current_width / self.base_width)
        self.setZoomFactor(zoom_factor)