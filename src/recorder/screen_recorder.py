import os
import time
import cv2
import numpy as np
import pyautogui
import threading
from datetime import datetime
from src.recorder.metadata_collector import MetadataCollector

class ScreenRecorder:
    def __init__(self, config):
        self.config = config
        self.recording = False
        self.paused = False
        self.is_paused = False
        self.thread = None
        self.metadata_collector = MetadataCollector()
        self.output_file = None
        self.start_time = None
        self.pause_time = None
        self.total_pause_time = 0
        
    def start_recording(self):
        if self.recording:
            return
            
        # Создаем имя файла на основе текущей даты и времени
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        video_format = self.config.settings["video_format"]
        filename = f"screencaster_{timestamp}.{video_format}"
        
        # Полный путь к файлу
        save_path = self.config.settings["save_path"]
        if not os.path.exists(save_path):
            os.makedirs(save_path)
            
        self.output_file = os.path.join(save_path, filename)
        
        # Метаданные будут сохраняться в файл с тем же именем, но с расширением .json
        metadata_file = os.path.join(save_path, f"screencaster_{timestamp}.json")
        
        # Инициализация сборщика метаданных
        self.metadata_collector.start_collection(metadata_file)
        
        # Запуск записи в отдельном потоке
        self.recording = True
        self.is_paused = False
        self.start_time = time.time()
        self.total_pause_time = 0
        self.thread = threading.Thread(target=self._record_screen)
        self.thread.daemon = True
        self.thread.start()
        
    def pause_recording(self):
        if not self.recording or self.is_paused:
            return
            
        self.is_paused = True
        self.pause_time = time.time()
        self.metadata_collector.pause_collection()
        
    def resume_recording(self):
        if not self.recording or not self.is_paused:
            return
            
        self.is_paused = False
        # Учитываем время паузы
        self.total_pause_time += time.time() - self.pause_time
        self.metadata_collector.resume_collection()
        
    def stop_recording(self):
        if not self.recording:
            return
            
        self.recording = False
        if self.thread:
            self.thread.join()
            
        self.metadata_collector.stop_collection()
        
    def _record_screen(self):
        # Получаем настройки записи
        fps = self.config.settings["fps"]
        show_cursor = self.config.settings["show_cursor"]
        
        # Получаем разрешение экрана
        screen_width, screen_height = pyautogui.size()
        
        # Настраиваем кодек и writer для видео
        fourcc = cv2.VideoWriter_fourcc(*'mp4v') if self.config.settings["video_format"] == "mp4" else cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter(self.output_file, fourcc, fps, (screen_width, screen_height))
        
        # Расчет задержки между кадрами
        frame_delay = 1.0 / fps
        
        try:
            last_frame_time = time.time()
            
            while self.recording:
                if not self.is_paused:
                    current_time = time.time()
                    
                    # Проверяем, прошло ли достаточно времени для следующего кадра
                    if current_time - last_frame_time >= frame_delay:
                        # Захват скриншота
                        screenshot = pyautogui.screenshot()
                        frame = np.array(screenshot)
                        
                        # Конвертируем из RGB в BGR (OpenCV использует BGR)
                        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                        
                        # Если нужно показать курсор, добавляем его на кадр
                        if show_cursor:
                            cursor_x, cursor_y = pyautogui.position()
                            cv2.circle(frame, (cursor_x, cursor_y), 5, (0, 0, 255), -1)
                        
                        # Записываем кадр
                        out.write(frame)
                        
                        # Обновляем время последнего кадра
                        last_frame_time = current_time
                    
                    # Небольшая задержка, чтобы не нагружать CPU
                    time.sleep(0.001)
                else:
                    # Если запись на паузе, просто ждем
                    time.sleep(0.1)
                    
        finally:
            # Закрываем writer
            out.release()
            
            # Если запись была остановлена до завершения, конвертируем в нужный формат
            if self.config.settings["video_format"] == "mov" and os.path.exists(self.output_file):
                # Для конвертации в .mov можно использовать ffmpeg
                # Это потребует дополнительной реализации
                pass