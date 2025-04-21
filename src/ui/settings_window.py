import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QLineEdit, QPushButton, QCheckBox, QComboBox,
                            QFileDialog, QGroupBox, QFormLayout)

class SettingsWindow(QDialog):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.setWindowTitle("Настройки")
        self.setFixedSize(400, 300)
        
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Группа настроек сохранения
        save_group = QGroupBox("Сохранение")
        save_layout = QFormLayout()
        
        # Путь сохранения
        save_path_layout = QHBoxLayout()
        self.save_path_edit = QLineEdit()
        browse_button = QPushButton("Обзор")
        browse_button.clicked.connect(self.browse_save_path)
        save_path_layout.addWidget(self.save_path_edit)
        save_path_layout.addWidget(browse_button)
        save_layout.addRow("Путь сохранения:", save_path_layout)
        
        # Формат видео
        self.format_combo = QComboBox()
        self.format_combo.addItems(["mov", "mp4"])
        save_layout.addRow("Формат видео:", self.format_combo)
        
        save_group.setLayout(save_layout)
        layout.addWidget(save_group)
        
        # Группа настроек записи
        record_group = QGroupBox("Запись")
        record_layout = QFormLayout()
        
        # FPS
        self.fps_combo = QComboBox()
        self.fps_combo.addItems(["15", "25", "30", "60"])
        record_layout.addRow("Кадров в секунду:", self.fps_combo)
        
        # Показывать курсор
        self.show_cursor_check = QCheckBox()
        record_layout.addRow("Показывать курсор:", self.show_cursor_check)
        
        record_group.setLayout(record_layout)
        layout.addWidget(record_group)
        
        # Группа горячих клавиш
        hotkeys_group = QGroupBox("Горячие клавиши")
        hotkeys_layout = QFormLayout()
        
        self.start_hotkey_edit = QLineEdit()
        self.pause_hotkey_edit = QLineEdit()
        self.stop_hotkey_edit = QLineEdit()
        
        hotkeys_layout.addRow("Начать запись:", self.start_hotkey_edit)
        hotkeys_layout.addRow("Пауза:", self.pause_hotkey_edit)
        hotkeys_layout.addRow("Остановить:", self.stop_hotkey_edit)
        
        hotkeys_group.setLayout(hotkeys_layout)
        layout.addWidget(hotkeys_group)
        
        # Кнопки сохранения/отмены
        buttons_layout = QHBoxLayout()
        save_button = QPushButton("Сохранить")
        save_button.clicked.connect(self.save_settings)
        cancel_button = QPushButton("Отмена")
        cancel_button.clicked.connect(self.reject)
        
        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(cancel_button)
        layout.addLayout(buttons_layout)
    
    def load_settings(self):
        settings = self.config.settings
        
        self.save_path_edit.setText(settings["save_path"])
        self.format_combo.setCurrentText(settings["video_format"])
        self.fps_combo.setCurrentText(str(settings["fps"]))
        self.show_cursor_check.setChecked(settings["show_cursor"])
        
        self.start_hotkey_edit.setText(settings["hotkeys"]["start_recording"])
        self.pause_hotkey_edit.setText(settings["hotkeys"]["pause_recording"])
        self.stop_hotkey_edit.setText(settings["hotkeys"]["stop_recording"])
    
    def save_settings(self):
        settings = self.config.settings
        
        settings["save_path"] = self.save_path_edit.text()
        settings["video_format"] = self.format_combo.currentText()
        settings["fps"] = int(self.fps_combo.currentText())
        settings["show_cursor"] = self.show_cursor_check.isChecked()
        
        settings["hotkeys"]["start_recording"] = self.start_hotkey_edit.text()
        settings["hotkeys"]["pause_recording"] = self.pause_hotkey_edit.text()
        settings["hotkeys"]["stop_recording"] = self.stop_hotkey_edit.text()
        
        self.config.save_config()
        self.accept()
    
    def browse_save_path(self):
        directory = QFileDialog.getExistingDirectory(
            self, 
            "Выберите папку для сохранения", 
            self.save_path_edit.text()
        )
        
        if directory:
            self.save_path_edit.setText(directory)