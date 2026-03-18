# filepath: ui/main_window.py
import json
import os
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QTextEdit, QLabel, QTabWidget)
from PySide6.QtCore import QUrl, QTimer, Slot
from PySide6.QtGui import QTextCursor,QIcon


from core.answer_worker import AnswerWorker
from ui.browser_view import AutoFitWebView
from ui.settings_dialog import SettingsDialog

class MyToolApp(QMainWindow):
    def __init__(self, web_profile=None):
        super().__init__()
        self.web_profile = web_profile
        self.setWindowTitle("学习通小助手")
        icon_path = os.path.join(os.path.dirname(__file__), "z_icon.ico")
        self.setWindowIcon(QIcon(icon_path))
        self.resize(1200, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0) 
        main_layout.setSpacing(1) 

        # 左侧：浏览器
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True) # 让标签页看起来更像真正的浏览器
        self.tabs.setTabsClosable(True) # 允许关闭标签页 (显示 X 按钮)
        self.tabs.tabCloseRequested.connect(self.close_tab) # 绑定关闭事件
        
        main_layout.addWidget(self.tabs, stretch=7) 

        # 右侧：控制台面板
        right_panel = QWidget()
        right_panel.setMinimumWidth(300) 
        
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 10, 10, 10)
        
        controls_layout = QVBoxLayout()

        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("智能答题操作控制台"))

        self.btn_settings = QPushButton("设置")
        self.btn_settings.setFixedWidth(80)
        header_layout.addWidget(self.btn_settings)
        
        controls_layout.addLayout(header_layout)
        
        nav_layout = QHBoxLayout()
        self.btn_back = QPushButton("◀ 后退")
        self.btn_forward = QPushButton("前进 ▶")
        
        self.btn_back.setStyleSheet("padding: 5px;")
        self.btn_forward.setStyleSheet("padding: 5px;")
        
        nav_layout.addWidget(self.btn_back)
        nav_layout.addWidget(self.btn_forward)
        controls_layout.addLayout(nav_layout)
        
        self.btn_auto_answer = QPushButton("▶ 一键全自动答题")
        self.set_button_style(self.btn_auto_answer, "#4CAF50", "#45a049", "#3e8e41")
        controls_layout.addWidget(self.btn_auto_answer)

        self.btn_auto_video = QPushButton("▶ 一键全自动刷课")
        self.set_button_style(self.btn_auto_video, "#2196F3", "#1E88E5", "#1976D2")
        controls_layout.addWidget(self.btn_auto_video)
        
        controls_layout.addStretch() 
        
        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setStyleSheet("background-color: #2b2b2b; color: #a9b7c6;")
        self.console_output.setPlaceholderText("Ciallo～(∠・ω＜ )⌒☆​")
        
        right_layout.addLayout(controls_layout, stretch=1)
        right_layout.addWidget(self.console_output, stretch=3)
        
        main_layout.addWidget(right_panel, stretch=2)

        self.btn_auto_answer.clicked.connect(self.toggle_answering)
        self.btn_back.clicked.connect(lambda: self.tabs.currentWidget().back())
        self.btn_forward.clicked.connect(lambda: self.tabs.currentWidget().forward())
        self.btn_settings.clicked.connect(self.open_settings)
        self.btn_auto_video.clicked.connect(self.toggle_watching)

        self.is_watching = False
        self.answer_thread = None
        self.is_running = False  # 记录当前系统是否在运行中

        self.add_new_tab(url="https://i.chaoxing.com/base", label="主页")

    def start_scraping_and_answering(self):
        self.console_output.append("\n>>> -> 开始注入深层答题雷达...")
        
        extract_js = r"""
        (function() {
            const sysLog = window.console.info.bind(window.console) || window.console.log.bind(window.console);
            let results = [];
            let globalIndex = 0;

            function scanFrames(win) {
                try {
                    let doc = win.document;
                    if (!doc) return;

                    let qNodes = doc.querySelectorAll('.singleQuesId, .questionLi, .Zy_Title, .subject_item');

                    if (qNodes.length > 0) {
                        qNodes.forEach((q) => {
                            let titleEl = q.querySelector('h3, .mark_name, .question-title');
                            let titleText = titleEl ? titleEl.innerText : q.innerText.split('\n')[0];
                            titleText = titleText.replace(/\s+/g, ' ').trim();

                            let optionsEl = q.querySelectorAll('li, .answerBg');
                            let choices = {};

                            if (optionsEl.length > 0) {
                                optionsEl.forEach((opt, idx) => {
                                    let letterEl = opt.querySelector('i.fl, .sort'); 
                                    let letter = letterEl ? letterEl.innerText.replace(/[^A-Z]/g, '') : String.fromCharCode(65 + idx);
                                    if (!letter) letter = String.fromCharCode(65 + idx);

                                    let text = opt.innerText.replace(/^[A-Z][、. ]/, '').trim(); 
                                    
                                    // 【绝对兜底法则】：如果没抓到字，强制翻译为对错！
                                    if (!text || text === "") {
                                        text = (idx === 0) ? "正确" : "错误";
                                    }
                                    
                                    choices[letter] = text;
                                });
                            }

                            results.push({ index: globalIndex++, question: titleText, hasOptions: Object.keys(choices).length > 0, choices: choices, type: 'mixed' });
                            q.style.borderLeft = "4px solid #FF5722";
                        });
                    }
                } catch(e) { } 

                try { for (let i = 0; i < win.frames.length; i++) scanFrames(win.frames[i]); } catch(e) {}
            }

            scanFrames(window);
            let finalStatus = results.length > 0 ? "success" : "empty";
            return JSON.stringify({ status: finalStatus, data: results });
        })();
        """
        current_browser = self.tabs.currentWidget()
        if current_browser:
            current_browser.page().runJavaScript(extract_js, self.on_data_scraped)
    
    @Slot()
    def toggle_answering(self):
        try:
            if not getattr(self, 'is_running', False):
                api_key = ""
                import json, os
                if os.path.exists("config.json"):
                    with open("config.json", "r", encoding="utf-8") as f:
                        api_key = json.load(f).get("api_key", "")

                if not api_key or str(api_key).strip() == "":
                    self.console_output.append("\n>>>  拦截警告：检测到未配置大模型 API Key！")
                    self.console_output.append(">>>  请先在弹出的设置窗口中填入信息，否则将默认全选 A。")
                    
                    self.open_settings() 
                    
                    if getattr(self, 'is_watching', False):
                        self.console_output.append(">>> -> 无人值守保护触发：5秒后将强行跳过本页测验，继续刷课...")
                        from PySide6.QtCore import QTimer
                        QTimer.singleShot(5000, self.force_jump_next)
                        
                    return # 拦截成功，直接终止后续的答题注入逻辑！
                self.is_running = True
                self.btn_auto_answer.setText("⏹ 停止答题")
                self.set_button_style(self.btn_auto_answer, "#FF0000", "#da3232", "#a72222")
                self.start_scraping_and_answering()
            else:
                self.btn_auto_answer.setText("正在停止...")
                self.btn_auto_answer.setEnabled(False)

                if self.answer_thread and self.answer_thread.isRunning():
                    self.answer_thread.stop()
                else:
                    self.reset_button_state()

        except Exception as e:
            import traceback
            print("-> toggle_answering 崩了：")
            traceback.print_exc()

    def reset_button_state(self):
        """将按钮恢复为初始的【开始】状态"""
        self.is_running = False
        self.btn_auto_answer.setText("▶ 一键全自动答题")
        self.set_button_style(self.btn_auto_answer, "#4CAF50", "#45a049", "#3e8e41")
        self.btn_auto_answer.setEnabled(True)

        if getattr(self, 'is_watching', False):
            self.console_output.append("\n>>> -> AI 答题执行完毕！")
            self.console_output.append(">>> -> 3秒后将强行跳过当前测验前往下一节...\n")
            from PySide6.QtCore import QTimer
            QTimer.singleShot(3000, self.force_jump_next)
    
    def force_jump_next(self):
        if not getattr(self, 'is_watching', False):
            return
            
        jump_js = """
            (function() {
                let clickedSubmit = false;

                function findAndClickSubmit(win) {
                    if (clickedSubmit) return;
                    try {
                        let doc = win.document;
                        if (doc) {
                            let submitBtn = Array.from(doc.querySelectorAll('a, button, span, div.btn'))
                                                 .find(b => b.innerText && b.innerText.trim() === '提交' && b.offsetHeight > 0);
                            if (submitBtn) {
                                submitBtn.click();
                                clickedSubmit = true;
                                
                                setTimeout(() => {
                                    function clickConfirm(w) {
                                        try {
                                            let confirmBtn = Array.from(w.document.querySelectorAll('.bluebtn, .ui-dialog-buttonpane button, .layui-layer-btn0, .jb_btn, a.sure'))
                                                                  .find(b => b.innerText && (b.innerText.includes('确定') || b.innerText.includes('确认')));
                                            if (confirmBtn && confirmBtn.offsetHeight > 0) confirmBtn.click();
                                        } catch(e) {}
                                        try { for (let i = 0; i < w.frames.length; i++) clickConfirm(w.frames[i]); } catch(e) {}
                                    }
                                    clickConfirm(window); // 绝对安全的作用域扫描
                                }, 1000);
                            }
                        }
                    } catch(e) {}
                    try { for (let i = 0; i < win.frames.length; i++) findAndClickSubmit(win.frames[i]); } catch(e) {}
                }

                findAndClickSubmit(window);

                setTimeout(() => {
                    try {
                        // 寻找弹窗和下一节按钮
                        let dialogBtn = Array.from(document.querySelectorAll('.bluebtn, .ui-dialog-buttonpane button, .layui-layer-btn0, .jb_btn'))
                                             .find(b => b.innerText && (b.innerText.includes('确定') || b.innerText.includes('下一节')));
                        if (dialogBtn && dialogBtn.offsetHeight > 0) { dialogBtn.click(); return; }
                        
                        let nextBtn = document.querySelector('.orientationright') || document.querySelector('#nextBtn') || Array.from(document.querySelectorAll('a, button, span')).find(el => el.innerText && el.innerText.trim() === '下一节');
                        if (nextBtn) { nextBtn.click(); }
                    } catch(e) {}
                }, 2500);
            })();
            """
        current_browser = self.tabs.currentWidget()
        if current_browser:
            current_browser.page().runJavaScript(jump_js)
            self.console_output.append("-> 正在尝试交卷并跳转新页面 (8秒后重启刷课雷达)...\n")
            from PySide6.QtCore import QTimer
            # Python 端独立计时器，8 秒后强制在下一个页面重启雷达
            QTimer.singleShot(8000, self.execute_watch_script)

    def reset_video_button_state(self):
        """将刷课按钮恢复为初始的【开始】状态"""
        self.is_watching = False
        self.btn_auto_video.setText("▶ 一键全自动刷课")
        self.set_button_style(self.btn_auto_video, "#2196F3", "#1E88E5", "#1976D2")
        self.btn_auto_video.setEnabled(True)
    
    def on_data_scraped(self, js_result_str):
        try:
            import json
            # 1. 检查返回值是否为空
            if not js_result_str:
                self.console_output.append(">>> -> JS 脚本返回为空，可能遭到跨域安全拦截。")
                self.reset_button_state()
                return

            # 2. 安全解析 JSON 字符串
            js_result = json.loads(js_result_str)

            # 3. 处理结果
            if js_result.get('status') == 'empty':
                self.console_output.append(">>> -> 页面中未找到任何题目！请确认左侧是否显示了具体题目，或超星又换了新页面结构。")
                self.reset_button_state()
                return

            questions_data = js_result.get('data', [])
            self.console_output.append(f">>> -> 成功提取到 {len(questions_data)} 道题目，启动后台多线程答题...")

            # 启动多线程
            self.answer_thread = AnswerWorker(questions_data)
            self.answer_thread.finished_question.connect(self.on_question_answered)
            self.answer_thread.log_signal.connect(lambda msg: self.console_output.append(msg + "\n"))
            self.answer_thread.finished.connect(self.reset_button_state)
            
            self.answer_thread.start()

        except Exception as e:
            import traceback
            self.console_output.append(f">>> -> 解析题目数据时崩溃: {str(e)}")
            print(traceback.format_exc()) # 在终端里打出详细报错
            self.reset_button_state()

    def on_question_answered(self, q_index, final_answers_list):
        import json
        js_array_str = json.dumps(final_answers_list)
        
        click_js = f"""
        (function() {{
            let targetAnswers = {js_array_str}; 
            let targetIndex = {q_index};
            let currentIndex = 0;
            let clicked = []; 

            function clickFrames(win) {{
                if (clicked.length > 0) return;

                try {{
                    let doc = win.document;
                    if (doc) {{
                        let qNodes = doc.querySelectorAll('.singleQuesId, .questionLi, .Zy_Title, .subject_item');
                        if (qNodes.length > 0) {{
                            qNodes.forEach((q) => {{
                                if (currentIndex === targetIndex) {{
                                    let optionsEl = q.querySelectorAll('li, .answerBg');
                                    optionsEl.forEach((opt, idx) => {{
                                        let letterEl = opt.querySelector('i.fl, .sort');
                                        let letter = letterEl ? letterEl.innerText.replace(/[^A-Z]/g, '') : String.fromCharCode(65 + idx);
                                        if (!letter) letter = String.fromCharCode(65 + idx);

                                        let text = opt.innerText.replace(/^[A-Z][、. ]/, '').trim();
                                        
                                        // 【点击器绝对兜底法则】
                                        if (!text || text === "") {{
                                            text = (idx === 0) ? "正确" : "错误";
                                        }}

                                        // 双重匹配：大模型返回字母或者中文，全都能识别
                                        let isMatch = targetAnswers.includes(letter) || 
                                                      targetAnswers.includes(text) ||
                                                      (text === "正确" && (targetAnswers.includes("对") || targetAnswers.includes("T") || targetAnswers.includes("True"))) ||
                                                      (text === "错误" && (targetAnswers.includes("错") || targetAnswers.includes("F") || targetAnswers.includes("False")));

                                        if (isMatch) {{
                                            let clickTargets = opt.querySelectorAll('input, a, label, .radio, .check');
                                            if (clickTargets.length > 0) {{
                                                clickTargets.forEach(t => t.click());
                                            }} else {{
                                                opt.click();
                                            }}
                                            clicked.push(letter);
                                            opt.style.border = "2px dashed #4CAF50";
                                        }}
                                    }});
                                }}
                                currentIndex++;
                            }});
                        }}
                    }}
                }} catch(e) {{}}

                try {{ for (let i = 0; i < win.frames.length; i++) if (clicked.length === 0) clickFrames(win.frames[i]); }} catch(e) {{}}
            }}

            clickFrames(window);
            
            if (clicked.length > 0) return ">>> 第 " + (targetIndex + 1) + " 题已自动点击: " + clicked.join(', ');
            return ">>> 第 " + (targetIndex + 1) + " 题未能触发点击。目标: " + targetAnswers.join(', ');
        }})();
        """
        current_browser = self.tabs.currentWidget()
        if current_browser:
            current_browser.page().runJavaScript(click_js, lambda res: self.console_output.append(str(res)))

    def add_new_tab(self, url=None, label="新标签页"):
        """创建一个新标签页并加入 QTabWidget"""
        browser = AutoFitWebView(
            profile=self.web_profile,
            base_width=1280, 
            new_tab_callback=self.create_tab_from_link,
            log_callback=self.handle_sys_log
        )
        
        if url:
            browser.setUrl(QUrl(url))

        index = self.tabs.addTab(browser, label)
        self.tabs.setCurrentIndex(index) # 自动切换到新弹出的标签页
        
        # 动态更新标签页标题
        browser.titleChanged.connect(lambda title, b=browser: self.tabs.setTabText(self.tabs.indexOf(b), title[:8] + "..."))
        
        return browser

    def create_tab_from_link(self):
        """当网页代码要求弹出新窗口时，会被 CustomWebPage 调用"""
        return self.add_new_tab(label="加载中...")

    def close_tab(self, index):
        """关闭标签页"""
        # 如果只剩最后一个标签了，为了防止左侧空掉，不允许关闭
        if self.tabs.count() < 2:
            return 
        self.tabs.widget(index).deleteLater() # 释放内存
        self.tabs.removeTab(index)
    
    def open_settings(self):
        dialog = SettingsDialog(self)
        dialog.exec()

    def get_video_js(self):
        return r"""
        (function() {
            if(window.__watchInterval) clearInterval(window.__watchInterval);

            const sysLog = window.console.warn.bind(window.console) || window.console.log.bind(window.console);

            sysLog("[SYS_PROGRESS] -> 看片，冲刺！");

            let noTaskCount = 0;

            window.__watchInterval = setInterval(() => {
                try {
                    let foundVideos = [];
                    let foundPPT = null;
                    let foundTest = false;

                    function scanWindow(win) {
                        let doc;
                        try { doc = win.document; } catch(e) {}
                        if (!doc) return;

                        // 1. 安全扫描视频
                        try { doc.querySelectorAll('video').forEach(v => { foundVideos.push({ video: v, win: win }); }); } catch(e) {}
                        
                        // 2. 安全扫描 PPT
                        try { if (doc.getElementById('panView') || doc.querySelector('.fileBox')) foundPPT = doc; } catch(e) {}
                        
                        // 3. 安全扫描测验
                        try {
                            if (doc.querySelector('.TiMu, .Zy_Title, .singleQuesId, .questionLi, .subject_item') ||
                                doc.querySelector('iframe[src*="work"]')) {
                                foundTest = true;
                            }
                        } catch(e) {}
                        try {
                            if (win.location && win.location.href && win.location.href.includes('work')) {
                                foundTest = true;
                            }
                        } catch(e) {}

                        try { for (let i = 0; i < win.frames.length; i++) scanWindow(win.frames[i]); } catch(e) {}
                    }

                    scanWindow(window);

                    let nextBtn = document.querySelector('.orientationright') || 
                                  document.querySelector('#nextBtn') || 
                                  Array.from(document.querySelectorAll('a, button, span')).find(el => el.innerText && el.innerText.trim() === '下一节');

                    if (foundVideos.length > 0) {
                        noTaskCount = 0; 
                        
                        let targetObj = null;
                        let allFinished = true;
                        let currentIndex = 1;

                        for (let i = 0; i < foundVideos.length; i++) {
                            let v = foundVideos[i].video;
                            let win = foundVideos[i].win;
                            
                            let isFinished = v.__xxt_finished;
                            try { if (win.document.querySelector('.ans-job-finished')) isFinished = true; } catch(e){}

                            if (!isFinished) {
                                targetObj = foundVideos[i]; 
                                allFinished = false;
                                currentIndex = i + 1;       
                                break; 
                            } else {
                                if (!v.__xxt_finished) {
                                    v.__xxt_finished = true;
                                    sysLog(`[SYS_PROGRESS] -> 第 ${i+1} 个视频已有绿钩，跳过！`);
                                }
                            }
                        }

                        if (targetObj) {
                            let v = targetObj.video;
                            let win = targetObj.win;

                            if (!v.muted) v.muted = true;
                            if (v.playbackRate !== 1.0) v.playbackRate = 1.0;
                            
                            if (v.paused && !v.ended) {
                                v.play().catch(e => {
                                    try { win.document.querySelector('.vjs-big-play-button').click(); } catch(err) {}
                                });
                            }

                            let current = Math.floor(v.currentTime) || 0;
                            let total = Math.floor(v.duration) || 0;

                            if (total > 0) {
                                let percent = Math.floor((current / total) * 100);
                                
                                sysLog(`[SYS_PROGRESS] -> [第${currentIndex}/${foundVideos.length}个视频] 播放进度: ${current}s / ${total}s (${percent}%)`);

                                if (!v.__xxt_finished && (percent >= 99 || v.ended || (total - current <= 1))) {
                                    v.__xxt_finished = true;
                                    sysLog(`[SYS_PROGRESS] -> 第 ${currentIndex} 个视频播放完毕！寻找下一个...`);
                                }
                            } else {
                                sysLog(`[SYS_PROGRESS] -> [第${currentIndex}/${foundVideos.length}个视频] 正在缓冲真实视频流...`);
                            }
                        } else if (allFinished) {
                            if (!window.__page_finished_handled) {
                                window.__page_finished_handled = true;
                                sysLog("[SYS_PROGRESS] -> 本页所有视频已全部播放完毕，任务点安全入账！");
                                
                                if (foundTest) {
                                    sysLog("[SYS_PROGRESS] -> 发现【章节测验】，开始答题！");
                                    clearInterval(window.__watchInterval);
                                } else {
                                    setTimeout(() => { if (nextBtn) { sysLog("[SYS_PROGRESS] -> 准备跳转至下一节..."); nextBtn.click(); } }, 3000);
                                }
                            }
                        }
                    } 
                    else if (foundPPT) {
                        noTaskCount = 0; 
                        if (!window.__ppt_handled) {
                            window.__ppt_handled = true;
                            sysLog("[SYS_PROGRESS] -> 检测到 PPT，安全模拟认真阅读中 (等待 8 秒)...");
                            setTimeout(() => {
                                sysLog("[SYS_PROGRESS] -> PPT 阅读完毕！");

                                if (foundTest) {
                                    sysLog("[SYS_PROGRESS] -> 发现【章节测验】，开始答题！");
                                    clearInterval(window.__watchInterval);
                                } else {
                                    if(nextBtn) { sysLog("[SYS_PROGRESS] -> 准备跳转至下一节..."); nextBtn.click(); }
                                }
                            }, 8000);
                        }
                    }
                    else if (foundTest) {
                        noTaskCount = 0;
                        if (!window.__test_handled) {
                            window.__test_handled = true;
                            sysLog("[SYS_PROGRESS] -> 发现纯【章节测验】页面，开始答题！");
                            clearInterval(window.__watchInterval);
                        }
                    }
                    else {
                        noTaskCount++;
                        if (nextBtn && noTaskCount > 3) {
                            if (!window.__empty_handled) {
                                window.__empty_handled = true;
                                sysLog("[SYS_PROGRESS] -> 当前章节无视频或文档任务，自动跳过...");
                                setTimeout(() => { 
                                    sysLog("[SYS_PROGRESS] -> 准备跳转至下一节..."); 
                                    nextBtn.click(); 
                                }, 2000);
                            }
                        } else if (!nextBtn && noTaskCount > 5) {
                            sysLog("[SYS_PROGRESS] -> 未发现学习任务和跳转按钮，自动停止刷课。");
                            clearInterval(window.__watchInterval);
                        } else {
                            sysLog("[SYS_PROGRESS] -> 正在深度扫描页面任务点...");
                        }
                    }
                } catch (err) {
                    sysLog("[SYS_PROGRESS] -> JS底层错误: " + err.message);
                }
            }, 4000); 
        })();
        """
    
    @Slot()
    def toggle_watching(self):
        """控制自动刷课的启动与停止"""
        if not self.is_watching:
            # 启动挂机
            self.is_watching = True
            self.btn_auto_video.setText("⏹ 停止全自动刷课")
            self.set_button_style(self.btn_auto_video, "#FF0000", "#da3232", "#a72222")
            self.execute_watch_script()
        else:
            # 停止挂机
            self.console_output.append("\n>>>  已向系统发送停止指令，当前任务结束后不再跳转。")
            self.reset_video_button_state() # <--- 直接调用新函数
            
            current_browser = self.tabs.currentWidget()
            if current_browser:
                current_browser.page().runJavaScript("if(window.__watchInterval) clearInterval(window.__watchInterval);")

    def handle_sys_log(self, msg):
        """基于 Emoji 识别的极简版日志接收器"""
        try:
            from PySide6.QtCore import QTimer
            msg_str = str(msg).strip()
            
            my_markers = ["->"]
            
            if any(marker in msg_str for marker in my_markers):
                
                clean_msg = msg_str.replace("[SYS_PROGRESS]", "").replace("[UPDATE_PROGRESS]", "").strip()
                self.console_output.append(clean_msg)
                
                if "开始答题" in clean_msg:
                    if not self.is_running:
                        self.console_output.append("\n>>> -> 正在将控制权移交给 AI 答题模块...")
                        self.toggle_answering()

                # 遇到走错房间的提示，自动弹回按钮
                if "自动停止" in clean_msg:
                    self.reset_video_button_state()

                # 遇到连播提示，启动 8 秒倒计时复活
                if "准备跳转至下一节" in clean_msg and getattr(self, 'is_watching', True):
                    self.console_output.append(">>> 正在等待新页面加载 (8秒后自动启动探测)...\n")
                    QTimer.singleShot(8000, self.execute_watch_script)

                # 强行让滚动条自动滚到底部
                self.console_output.verticalScrollBar().setValue(
                    self.console_output.verticalScrollBar().maximum()
                )

        except Exception as e:
            print(f"-> [UI接收器报错]: {e}")
    
    def execute_watch_script(self):
        """实际执行注入的地方"""
        if not self.is_watching:
            return
        current_browser = self.tabs.currentWidget()
        if not current_browser:
            self.console_output.append("请先打开一个网页！\n")
            self.toggle_watching() # 自动停止
            return
        self.console_output.append(">>> Ciallo～(∠・ω＜ )⌒☆​")
        current_browser.page().runJavaScript(self.get_video_js())
    
    def set_button_style(self, button, color_hex, hover_hex, pressed_hex):
        style = f"""
            QPushButton {{
                padding: 10px;
                font-weight: bold;
                background-color: {color_hex};
                color: white;
                border-radius: 4px;
                border: none;
                outline: none; /* 去除某些系统下的焦点虚线框 */
            }}
            QPushButton:hover {{
                background-color: {hover_hex};
            }}
            QPushButton:pressed {{
                background-color: {pressed_hex};
            }}
            QPushButton:focus {{
                background-color: {color_hex}; /* 保持原色，防止变白 */
                border: 1px solid white;  
            }}
        """
        button.setStyleSheet(style)