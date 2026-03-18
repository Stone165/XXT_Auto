# filepath: utils/config_manager.py
import json
import os

CONFIG_FILE = "config.json"

def load_config():
    """读取本地配置文件，如果没有则自动生成一个模板"""
    if not os.path.exists(CONFIG_FILE):
        default_config = {
            "api_key": "",
            "base_url": "",
            "model": ""
        }
        save_config(default_config)
        return default_config
        
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_config(config_data):
    """将配置保存到本地 JSON 文件"""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config_data, f, ensure_ascii=False, indent=4)