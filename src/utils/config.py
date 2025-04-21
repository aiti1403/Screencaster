import os
import json
from pathlib import Path

class Config:
    def __init__(self):
        self.home_dir = str(Path.home())
        self.default_save_path = os.path.join(self.home_dir, "Videos", "Screencaster")
        self.default_settings = {
            "save_path": self.default_save_path,
            "show_cursor": True,
            "fps": 25,
            "video_format": "mov",
            "hotkeys": {
                "start_recording": "F9",
                "pause_recording": "F10",
                "stop_recording": "F11"
            },
            "resolution": "1920x1080"
        }
        
        # Создаем директорию для сохранения, если она не существует
        if not os.path.exists(self.default_save_path):
            os.makedirs(self.default_save_path)
            
        self.config_path = os.path.join(self.home_dir, ".screencaster_config.json")
        self.load_config()
    
    def load_config(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    self.settings = json.load(f)
            except:
                self.settings = self.default_settings
        else:
            self.settings = self.default_settings
            self.save_config()
    
    def get_recordings_folder(self):
    # Возвращает путь к папке с записями
    # Это пример, замените на реальную логику из вашего класса Config
        return os.path.join(os.path.expanduser("~"), "Videos", "Screencaster")

    
    def save_config(self):
        with open(self.config_path, 'w') as f:
            json.dump(self.settings, f, indent=4)