# filepath: ui/settings_dialog.py
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QMessageBox)
from utils.config_manager import load_config, save_config

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(" API 与模型设置")
        self.resize(400, 200)
        
        # 读取当前配置
        self.current_config = load_config()

        layout = QVBoxLayout(self)

        # API Key 输入框
        layout.addWidget(QLabel("API Key :"))
        self.input_api_key = QLineEdit()
        self.input_api_key.setText(self.current_config.get("api_key", ""))
        self.input_api_key.setEchoMode(QLineEdit.EchoMode.PasswordEchoOnEdit) # 密码模式
        layout.addWidget(self.input_api_key)

        # 模型名称输入框
        layout.addWidget(QLabel("模型名称 :"))
        self.input_model = QLineEdit()
        self.input_model.setText(self.current_config.get("model", ""))
        layout.addWidget(self.input_model)

        # 接口地址
        layout.addWidget(QLabel("接口地址 (Base URL):"))
        self.input_base_url = QLineEdit()
        self.input_base_url.setText(self.current_config.get("base_url", ""))
        layout.addWidget(self.input_base_url)

        layout.addStretch()

        # 底部按钮
        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("保存配置")
        self.btn_cancel = QPushButton("取消")
        
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save)
        layout.addLayout(btn_layout)

        # 绑定事件
        self.btn_save.clicked.connect(self.save_and_close)
        self.btn_cancel.clicked.connect(self.reject)

    def save_and_close(self):
        # 更新配置字典
        self.current_config["api_key"] = self.input_api_key.text().strip()
        self.current_config["model"] = self.input_model.text().strip()
        self.current_config["base_url"] = self.input_base_url.text().strip()
        
        # 保存到本地 json
        save_config(self.current_config)
        
        QMessageBox.information(self, "成功", "配置已保存！下次答题将使用新配置。")
        self.accept() # 关闭弹窗