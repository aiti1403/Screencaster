import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QLineEdit, QPushButton, QCheckBox, QComboBox,
                            QFileDialog, QGroupBox, QFormLayout, QTabWidget,
                            QWidget, QSlider, QSpinBox, QRadioButton)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon

class SettingsWindow(QDialog):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.setWindowTitle("Settings")
        self.setMinimumSize(550, 450)
        
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("QTabBar::tab { height: 25px; min-width: 100px; }")
        
        # ===== GENERAL TAB =====
        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)
        general_layout.setSpacing(15)
        
        # Save settings group
        save_group = QGroupBox("Saving")
        save_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        save_layout = QFormLayout()
        save_layout.setVerticalSpacing(10)
        save_layout.setLabelAlignment(Qt.AlignRight)
        
        # Save path
        save_path_layout = QHBoxLayout()
        save_path_layout.setSpacing(5)
        self.save_path_edit = QLineEdit()
        browse_button = QPushButton("Browse...")
        browse_button.setFixedWidth(80)
        browse_button.clicked.connect(self.browse_save_path)
        save_path_layout.addWidget(self.save_path_edit)
        save_path_layout.addWidget(browse_button)
        save_layout.addRow("Save path:", save_path_layout)
        
        # File name template
        self.filename_template = QLineEdit()
        self.filename_template.setText("Recording_%Y-%m-%d_%H-%M-%S")
        save_layout.addRow("Filename template:", self.filename_template)
        
        # Video format
        self.format_combo = QComboBox()
        self.format_combo.addItems(["mp4", "avi", "mov", "wmv", "mkv"])
        save_layout.addRow("Video format:", self.format_combo)
        
        save_group.setLayout(save_layout)
        general_layout.addWidget(save_group)
        
        # Recording settings group
        record_group = QGroupBox("Recording")
        record_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        record_layout = QFormLayout()
        record_layout.setVerticalSpacing(10)
        record_layout.setLabelAlignment(Qt.AlignRight)
        
        # FPS
        self.fps_combo = QComboBox()
        self.fps_combo.addItems(["15", "24", "25", "30", "60"])
        record_layout.addRow("Frames per second:", self.fps_combo)
        
        # Show cursor
        self.show_cursor_check = QCheckBox()
        record_layout.addRow("Show cursor:", self.show_cursor_check)
        
        # Record audio
        self.record_audio_check = QCheckBox()
        self.record_audio_check.setChecked(True)
        record_layout.addRow("Record audio:", self.record_audio_check)
        
        # Audio source
        audio_source_layout = QHBoxLayout()
        self.mic_radio = QRadioButton("Microphone")
        self.system_radio = QRadioButton("System sounds")
        self.both_radio = QRadioButton("Both")
        self.mic_radio.setChecked(True)
        audio_source_layout.addWidget(self.mic_radio)
        audio_source_layout.addWidget(self.system_radio)
        audio_source_layout.addWidget(self.both_radio)
        audio_source_layout.addStretch()
        record_layout.addRow("Audio source:", audio_source_layout)
        
        record_group.setLayout(record_layout)
        general_layout.addWidget(record_group)
        
        general_layout.addStretch()
        
        # Add general tab
        self.tab_widget.addTab(general_tab, "General")
        
        # ===== VIDEO TAB =====
        video_tab = QWidget()
        video_layout = QVBoxLayout(video_tab)
        video_layout.setSpacing(15)
        
        # Video quality group
        video_quality_group = QGroupBox("Video Quality")
        video_quality_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        video_quality_layout = QFormLayout()
        video_quality_layout.setVerticalSpacing(10)
        video_quality_layout.setLabelAlignment(Qt.AlignRight)
        
        # Quality slider
        quality_layout = QHBoxLayout()
        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setMinimum(1)
        self.quality_slider.setMaximum(100)
        self.quality_slider.setValue(80)
        self.quality_slider.setFixedWidth(300)
        self.quality_value = QLabel("80%")
        self.quality_slider.valueChanged.connect(
            lambda value: self.quality_value.setText(f"{value}%")
        )
        quality_layout.addWidget(self.quality_slider)
        quality_layout.addWidget(self.quality_value)
        quality_layout.addStretch()
        video_quality_layout.addRow("Quality:", quality_layout)
        
        # Resolution option removed as requested
        
        # Codec
        self.codec_combo = QComboBox()
        self.codec_combo.addItems(["H.264", "H.265", "VP9", "AV1"])
        video_quality_layout.addRow("Codec:", self.codec_combo)
        
        video_quality_group.setLayout(video_quality_layout)
        video_layout.addWidget(video_quality_group)
        
        # Watermark group
        watermark_group = QGroupBox("Watermark")
        watermark_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        watermark_layout = QFormLayout()
        watermark_layout.setVerticalSpacing(10)
        watermark_layout.setLabelAlignment(Qt.AlignRight)
        
        # Enable watermark
        self.watermark_check = QCheckBox()
        watermark_layout.addRow("Enable watermark:", self.watermark_check)
        
        # Watermark image
        watermark_path_layout = QHBoxLayout()
        self.watermark_path_edit = QLineEdit()
        watermark_browse_button = QPushButton("Browse...")
        watermark_browse_button.setFixedWidth(80)
        watermark_browse_button.clicked.connect(self.browse_watermark)
        watermark_path_layout.addWidget(self.watermark_path_edit)
        watermark_path_layout.addWidget(watermark_browse_button)
        watermark_layout.addRow("Image:", watermark_path_layout)
        
        # Watermark position
        self.watermark_position = QComboBox()
        self.watermark_position.addItems(["Top Left", "Top Right", "Bottom Left", "Bottom Right"])
        watermark_layout.addRow("Position:", self.watermark_position)
        
        watermark_group.setLayout(watermark_layout)
        video_layout.addWidget(watermark_group)
        
        video_layout.addStretch()
        
        # Add video tab
        self.tab_widget.addTab(video_tab, "Video")
        
        # ===== HOTKEYS TAB =====
        hotkeys_tab = QWidget()
        hotkeys_layout = QVBoxLayout(hotkeys_tab)
        
        hotkeys_group = QGroupBox("Hotkeys")
        hotkeys_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        hotkeys_form = QFormLayout()
        hotkeys_form.setVerticalSpacing(10)
        hotkeys_form.setLabelAlignment(Qt.AlignRight)
        
        self.start_hotkey_edit = QLineEdit()
        self.start_hotkey_edit.setText("F8")
        self.pause_hotkey_edit = QLineEdit()
        self.pause_hotkey_edit.setText("F9")
        self.stop_hotkey_edit = QLineEdit()
        self.stop_hotkey_edit.setText("F10")
        self.screenshot_hotkey_edit = QLineEdit()
        self.screenshot_hotkey_edit.setText("F11")
        
        hotkeys_form.addRow("Start recording:", self.start_hotkey_edit)
        hotkeys_form.addRow("Pause:", self.pause_hotkey_edit)
        hotkeys_form.addRow("Stop:", self.stop_hotkey_edit)
        hotkeys_form.addRow("Screenshot:", self.screenshot_hotkey_edit)
        
        hotkeys_group.setLayout(hotkeys_form)
        hotkeys_layout.addWidget(hotkeys_group)
        hotkeys_layout.addStretch()
        
        # Add hotkeys tab
        self.tab_widget.addTab(hotkeys_tab, "Hotkeys")
        
        # Add tab widget to main layout
        main_layout.addWidget(self.tab_widget)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_settings)
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_settings)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        
        buttons_layout.addWidget(self.reset_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(cancel_button)
        main_layout.addLayout(buttons_layout)
    
    def load_settings(self):
        settings = self.config.settings
        
        # Load existing settings
        self.save_path_edit.setText(settings.get("save_path", ""))
        self.format_combo.setCurrentText(settings.get("video_format", "mp4"))
        self.fps_combo.setCurrentText(str(settings.get("fps", 30)))
        self.show_cursor_check.setChecked(settings.get("show_cursor", True))
        
        # Load hotkeys
        hotkeys = settings.get("hotkeys", {})
        self.start_hotkey_edit.setText(hotkeys.get("start_recording", "F8"))
        self.pause_hotkey_edit.setText(hotkeys.get("pause_recording", "F9"))
        self.stop_hotkey_edit.setText(hotkeys.get("stop_recording", "F10"))
        self.screenshot_hotkey_edit.setText(hotkeys.get("screenshot", "F11"))
        
        # Load new settings with defaults
        self.filename_template.setText(settings.get("filename_template", "Recording_%Y-%m-%d_%H-%M-%S"))
        self.record_audio_check.setChecked(settings.get("record_audio", True))
        
        # Audio source
        audio_source = settings.get("audio_source", "Microphone")
        if audio_source == "Microphone":
            self.mic_radio.setChecked(True)
        elif audio_source == "System sounds":
            self.system_radio.setChecked(True)
        else:
            self.both_radio.setChecked(True)
        
        # Video quality settings
        self.quality_slider.setValue(settings.get("video_quality", 80))
        # Resolution setting removed
        self.codec_combo.setCurrentText(settings.get("codec", "H.264"))
        
        # Watermark settings
        self.watermark_check.setChecked(settings.get("watermark_enabled", False))
        self.watermark_path_edit.setText(settings.get("watermark_path", ""))
        self.watermark_position.setCurrentText(settings.get("watermark_position", "Bottom Right"))
    
    def save_settings(self):
        settings = self.config.settings
        
        # Save basic settings
        settings["save_path"] = self.save_path_edit.text()
        settings["video_format"] = self.format_combo.currentText()
        settings["fps"] = int(self.fps_combo.currentText())
        settings["show_cursor"] = self.show_cursor_check.isChecked()
        
        # Save hotkeys
        if "hotkeys" not in settings:
            settings["hotkeys"] = {}
        settings["hotkeys"]["start_recording"] = self.start_hotkey_edit.text()
        settings["hotkeys"]["pause_recording"] = self.pause_hotkey_edit.text()
        settings["hotkeys"]["stop_recording"] = self.stop_hotkey_edit.text()
        settings["hotkeys"]["screenshot"] = self.screenshot_hotkey_edit.text()
        
        # Save new settings
        settings["filename_template"] = self.filename_template.text()
        settings["record_audio"] = self.record_audio_check.isChecked()
        
        # Audio source
        if self.mic_radio.isChecked():
            settings["audio_source"] = "Microphone"
        elif self.system_radio.isChecked():
            settings["audio_source"] = "System sounds"
        else:
            settings["audio_source"] = "Both"
        
        # Video quality settings
        settings["video_quality"] = self.quality_slider.value()
        # Resolution setting removed
        settings["codec"] = self.codec_combo.currentText()
        
        # Watermark settings
        settings["watermark_enabled"] = self.watermark_check.isChecked()
        settings["watermark_path"] = self.watermark_path_edit.text()
        settings["watermark_position"] = self.watermark_position.currentText()
        
        self.config.save_config()
        self.accept()
    
    def reset_settings(self):
        # Reset to default values
        self.save_path_edit.setText(os.path.join(os.path.expanduser("~"), "Videos"))
        self.filename_template.setText("Recording_%Y-%m-%d_%H-%M-%S")
        self.format_combo.setCurrentText("mp4")
        self.fps_combo.setCurrentText("30")
        self.show_cursor_check.setChecked(True)
        self.record_audio_check.setChecked(True)
        self.mic_radio.setChecked(True)
        
        # Reset hotkeys
        self.start_hotkey_edit.setText("F8")
        self.pause_hotkey_edit.setText("F9")
        self.stop_hotkey_edit.setText("F10")
        self.screenshot_hotkey_edit.setText("F11")
        
        # Reset video settings
        # Reset video settings
        self.quality_slider.setValue(80)
        self.quality_value.setText("80%")
        # Resolution reset removed
        self.codec_combo.setCurrentText("H.264")
        
        # Reset watermark
        self.watermark_check.setChecked(False)
        self.watermark_path_edit.setText("")
        self.watermark_position.setCurrentText("Bottom Right")
    
    def browse_save_path(self):
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Save Directory",
            self.save_path_edit.text() or os.path.expanduser("~")
        )
        
        if directory:
            self.save_path_edit.setText(directory)
    
    def browse_watermark(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Watermark Image",
            self.watermark_path_edit.text() or os.path.expanduser("~"),
            "Images (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        
        if file_path:
            self.watermark_path_edit.setText(file_path)

