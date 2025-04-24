import os
from PyQt5.QtWidgets import (QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout,
                            QWidget, QLabel, QFrame, QGraphicsDropShadowEffect, QDesktopWidget,
                            QApplication, QMenu, QAction)
from PyQt5.QtCore import Qt, QPoint, QTimer, QSize
from PyQt5.QtGui import QIcon, QColor, QFont, QPainter, QBrush, QPen, QPolygon
from src.ui.settings_window import SettingsWindow
from src.recorder.screen_recorder import ScreenRecorder
from src.utils.config import Config

class CircleButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(50, 50)
        self.setStyleSheet("""
            QPushButton {
                background-color: white;
                border-radius: 25px;
                border: 1px solid #E0E0E0;
            }
            QPushButton:hover {
                background-color: #F5F5F5;
            }
            QPushButton:disabled {
                background-color: #F8F8F8;
                border: 1px solid #EEEEEE;
            }
        """)
        
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Если это кнопка записи, рисуем красный круг
        if self.objectName() == "recordButton":
            if hasattr(self, "is_recording") and self.is_recording:
                # Рисуем квадрат для состояния записи
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(QColor("#FF4D4D")))
                painter.drawRect(17, 17, 16, 16)
            else:
                # Рисуем круг для состояния ожидания
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(QColor("#FF4D4D")))
                painter.drawEllipse(17, 17, 16, 16)
        
        # Если это кнопка паузы, рисуем две вертикальные линии
        elif self.objectName() == "pauseButton":
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor("#666666")))
            # Рисуем две вертикальные линии
            painter.drawRect(17, 17, 5, 16)
            painter.drawRect(28, 17, 5, 16)
        
        # Если это кнопка выбора области
        elif self.objectName() == "regionButton":
            # Рисуем иконку монитора
            painter.setPen(QPen(QColor("#666666"), 1))
            painter.setBrush(QBrush(QColor("#666666")))
            # Монитор
            painter.drawRect(15, 18, 20, 14)
            # Подставка
            painter.drawRect(22, 32, 6, 3)
            painter.drawRect(19, 35, 12, 1)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Инициализация конфигурации
        self.config = Config()
        
        # Инициализация рекордера
        self.recorder = ScreenRecorder(self.config)
        
        # Настройка окна
        self.setWindowTitle("Screen Recorder")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setFixedSize(80, 280)  # Уменьшаем высоту, так как убрали кнопку настроек
        
        # Переменные для перетаскивания окна
        self.dragging = False
        self.offset = QPoint()
        
        # Переменные для отслеживания состояния записи
        self.is_recording = False
        self.is_paused = False
        self.recording_time = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        
        # Создание UI
        self.init_ui()
        
        # Подключение горячих клавиш
        self.setup_hotkeys()
        
        # Позиционирование окна у левого края экрана
        self.position_window()
        
        # Создание всплывающего меню для выбора разрешения
        self.resolution_menu = QMenu(self)
        self.resolution_menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 1px solid #E0E0E0;
                border-radius: 5px;
                padding: 5px;
            }
            QMenu::item {
                padding: 5px 15px;
                border-radius: 3px;
            }
            QMenu::item:selected {
                background-color: #F0F0F0;
            }
        """)
        
        # Добавляем единственный пункт меню - 1920x1080
        resolution_action = QAction("1920 x 1080", self)
        resolution_action.triggered.connect(lambda: self.set_resolution(1920, 1080))
        self.resolution_menu.addAction(resolution_action)
        
        # Создание меню для кнопки закрытия
        self.close_menu = QMenu(self)
        self.close_menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 1px solid #E0E0E0;
                border-radius: 5px;
                padding: 5px;
            }
            QMenu::item {
                padding: 5px 15px;
                border-radius: 3px;
            }
            QMenu::item:selected {
                background-color: #F0F0F0;
            }
        """)
        
        # Добавляем пункты меню для кнопки закрытия
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.open_settings)
        self.close_menu.addAction(settings_action)
        
        minimize_action = QAction("Minimize", self)
        minimize_action.triggered.connect(self.showMinimized)
        self.close_menu.addAction(minimize_action)
        
        close_action = QAction("Close", self)
        close_action.triggered.connect(self.close)
        self.close_menu.addAction(close_action)

    def position_window(self):
        # Получаем размеры экрана
        desktop = QDesktopWidget().availableGeometry()
        
        # Вычисляем позицию окна (у левого края, по центру по вертикали)
        x = 20  # отступ от левого края
        y = (desktop.height() - self.height()) // 2
        
        # Устанавливаем позицию
        self.move(x, y)

    def init_ui(self):
        # Основной виджет и layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Установка стиля для основного виджета
        central_widget.setStyleSheet("""
            background-color: #FFFFFF;
            color: #333333;
            font-family: 'Segoe UI', Arial;
            border-radius: 10px;
            border: 1px solid #E0E0E0;
        """)
        
        # Добавляем тень для окна
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 2)
        central_widget.setGraphicsEffect(shadow)
        
        # Создаем основной вертикальный layout с увеличенным верхним отступом для кнопки закрытия
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 25, 10, 15)  # Увеличиваем верхний отступ
        main_layout.setSpacing(10)  # Уменьшаем расстояние между элементами
        
        # Кнопка закрытия (создаем отдельно от layout)
        self.close_button = QPushButton("×", central_widget)
        self.close_button.setFixedSize(18, 18)
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: #F0F0F0;
                color: #666666;
                border: none;
                border-radius: 9px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #E0E0E0;
                color: #333333;
            }
        """)
        self.close_button.clicked.connect(self.show_close_menu)
        
        # Кнопка записи
        self.record_button = CircleButton()
        self.record_button.setObjectName("recordButton")
        self.record_button.is_recording = False
        self.record_button.clicked.connect(self.toggle_recording)
        
        # Добавляем тень для кнопки
        button_shadow = QGraphicsDropShadowEffect()
        button_shadow.setBlurRadius(10)
        button_shadow.setColor(QColor(0, 0, 0, 30))
        button_shadow.setOffset(0, 2)
        self.record_button.setGraphicsEffect(button_shadow)
        
        main_layout.addWidget(self.record_button, alignment=Qt.AlignCenter)
        
        # Создаем контейнер для таймера с отступами
        timer_container = QWidget()
        timer_layout = QHBoxLayout(timer_container)
        timer_layout.setContentsMargins(0, 0, 0, 0)  # Убираем отступы внутри контейнера
        
        # Добавляем таймер записи под кнопкой записи
        self.timer_label = QLabel("00:00")
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setStyleSheet("""
            color: #333333;
            font-size: 16px;
            font-weight: bold;
        """)
        
        # Добавляем таймер в контейнер с центрированием
        timer_layout.addWidget(self.timer_label, alignment=Qt.AlignCenter)
        
        # Добавляем контейнер с таймером в основной layout
        main_layout.addWidget(timer_container)
        
        # Разделительная линия 1
        line1 = QFrame()
        line1.setFrameShape(QFrame.HLine)
        line1.setFrameShadow(QFrame.Plain)
        line1.setStyleSheet("background-color: #E5E5E5; max-height: 1px;")
        main_layout.addWidget(line1)
        
        # Кнопка паузы
        self.pause_button = CircleButton()
        self.pause_button.setObjectName("pauseButton")
        self.pause_button.clicked.connect(self.toggle_pause)
        self.pause_button.setEnabled(False)  # По умолчанию отключена
        main_layout.addWidget(self.pause_button, alignment=Qt.AlignCenter)
        
        # Разделительная линия 2
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setFrameShadow(QFrame.Plain)
        line2.setStyleSheet("background-color: #E5E5E5; max-height: 1px;")
        main_layout.addWidget(line2)
        
        # Кнопка выбора области записи
        self.region_button = CircleButton()
        self.region_button.setObjectName("regionButton")
        self.region_button.clicked.connect(self.select_region)
        main_layout.addWidget(self.region_button, alignment=Qt.AlignCenter)
        
        # Удалена кнопка настроек и разделительная линия перед ней
        
        # Добавляем растягивающийся элемент внизу для баланса
        main_layout.addStretch(1)

    def resizeEvent(self, event):
        """Переопределяем метод resizeEvent для обновления позиции кнопки закрытия при изменении размера окна"""
        super().resizeEvent(event)
        if hasattr(self, 'close_button'):
            self.close_button.move(self.width() - 25, 5)

    def show_close_menu(self):
        # Показываем всплывающее меню с опциями "Настройки", "Свернуть" и "Закрыть"
        # Позиционируем меню вплотную к правой стороне основного окна
        pos = self.mapToGlobal(QPoint(self.width(), 10))  # 10px от верха окна
        self.close_menu.popup(pos)


    def open_settings(self):
        settings_window = SettingsWindow(self.config)
        
        # Position the settings window next to the main window
        main_pos = self.mapToGlobal(QPoint(0, 0))
        settings_window.move(main_pos.x() + self.width() + 5, main_pos.y())
        
        settings_window.exec_()


    def select_region(self):
        # Показываем всплывающее меню с выбором разрешения
        pos = self.region_button.mapToGlobal(QPoint(self.region_button.width(), 0))
        self.resolution_menu.popup(pos)

    def set_resolution(self, width, height):
        # Устанавливаем выбранное разрешение в конфигурацию
        self.config.set('recording', 'width', str(width))
        self.config.set('recording', 'height', str(height))
        self.config.save()
        
        # Показываем уведомление о выбранном разрешении
        self.show_notification(f"Resolution set: {width} x {height}")

    def show_notification(self, message):
        # Создаем временную метку с уведомлением как дочерний виджет основного окна
        notification = QLabel(message, self)
        notification.setStyleSheet("""
            background-color: rgba(0, 0, 0, 0.7);
            color: white;
            border-radius: 5px;
            padding: 10px;
            font-size: 14px;
        """)
        notification.setAlignment(Qt.AlignCenter)
        notification.setFixedSize(200, 40)
        
        # Позиционируем уведомление рядом с окном
        # Позиционируем уведомление рядом с окном
        notification_x = self.width()
        notification_y = self.height() // 2 - notification.height() // 2
        notification.move(notification_x, notification_y)
        
        # Устанавливаем флаги окна для уведомления
        notification.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        
        # Показываем уведомление
        notification.show()
        
        # Скрываем и удаляем уведомление через 2 секунды
        def hide_and_delete():
            notification.hide()
            notification.deleteLater()
        
        QTimer.singleShot(2000, hide_and_delete)

    def toggle_recording(self):
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def toggle_pause(self):
        if self.is_recording:
            if not self.is_paused:
                self.pause_recording()
            else:
                self.resume_recording()

    def start_recording(self):
        self.recorder.start_recording()
        self.is_recording = True
        self.is_paused = False
        
        # Обновляем UI
        self.record_button.is_recording = True
        self.record_button.update()
        self.pause_button.setEnabled(True)
        self.region_button.setEnabled(False)
        
        # Запускаем таймер
        self.recording_time = 0
        self.timer.start(1000)  # Обновление каждую секунду

    def pause_recording(self):
        # Проверяем, есть ли метод pause_recording в recorder
        if hasattr(self.recorder, 'pause_recording') and callable(getattr(self.recorder, 'pause_recording')):
            self.recorder.pause_recording()
        
        self.is_paused = True
        
        # Останавливаем таймер
        self.timer.stop()
        
        # Показываем уведомление о паузе
        self.show_notification("Recording paused")

    def resume_recording(self):
        # Проверяем, есть ли метод resume_recording в recorder
        if hasattr(self.recorder, 'resume_recording') and callable(getattr(self.recorder, 'resume_recording')):
            self.recorder.resume_recording()
        
        self.is_paused = False
        
        # Возобновляем таймер
        self.timer.start(1000)
        
        # Показываем уведомление о возобновлении
        self.show_notification("Recording resumed")

    def stop_recording(self):
        # Вызываем метод stop_recording без попытки распаковки результата
        result = self.recorder.stop_recording()
        
        # Инициализируем переменные по умолчанию
        video_file = None
        
        # Проверяем тип возвращаемого значения
        if isinstance(result, tuple) and len(result) >= 1:
            video_file = result[0]
        elif isinstance(result, str):
            video_file = result
        
        self.is_recording = False
        self.is_paused = False
        
        # Обновляем UI
        self.record_button.is_recording = False
        self.record_button.update()
        self.pause_button.setEnabled(False)
        self.region_button.setEnabled(True)
        
        # Останавливаем таймер
        self.timer.stop()
        self.recording_time = 0
        self.update_timer()
        
        # Показываем уведомление о завершении записи
        if video_file:
            self.show_notification(f"Recording saved: {os.path.basename(video_file)}")
        else:
            self.show_notification("Recording completed")
   
    def update_timer(self):
        if self.is_recording:
            self.recording_time += 1
            
            minutes = self.recording_time // 60
            seconds = self.recording_time % 60
            
            time_str = f"{minutes:02d}:{seconds:02d}"
            self.timer_label.setText(time_str)
        else:
            self.timer_label.setText("00:00")

    def setup_hotkeys(self):
        # Настройка горячих клавиш будет реализована с использованием keyboard
        pass

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.offset = event.pos()

    def mouseMoveEvent(self, event):
        if self.dragging and event.buttons() == Qt.LeftButton:
            self.move(self.mapToGlobal(event.pos() - self.offset))

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False

    def showEvent(self, event):
        """Переопределяем метод showEvent для позиционирования окна и кнопки закрытия"""
        super().showEvent(event)
        self.position_window()
        
        # Позиционируем кнопку закрытия в правом верхнем углу
        if hasattr(self, 'close_button'):
            self.close_button.move(self.width() - 25, 5)

