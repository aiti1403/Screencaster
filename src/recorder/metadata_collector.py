import time
import json
import uuid
from pynput import mouse, keyboard
import threading

class MetadataCollector:
    """
    Класс для сбора метаданных о действиях пользователя во время записи экрана.
    Отслеживает клики мышью, перетаскивание, прокрутку, нажатия клавиш и ввод текста.
    """
    
    def __init__(self):
        """Инициализирует сборщик метаданных"""
        self.collecting = False
        self.paused = False
        self.events = []
        self.metadata_file = None

        # Размер экрана
        self.screen_width = 1920  # Значение по умолчанию
        self.screen_height = 1080  # Значение по умолчанию

        self.fps = 30  # Значение по умолчанию

        # Для отслеживания длительных нажатий
        self.long_press_timers = {}  # Словарь таймеров для длительных нажатий
        self.long_press_threshold = 0.5  # Порог в секундах для длительного нажатия
            
        # Время начала и паузы записи
        self.start_time = None
        self.pause_time = None
        self.total_pause_time = 0
        self.recording_start = None
        
        # Состояние клавиш и мыши
        self.pressed_keys = set()
        self.key_press_times = {}
        
        # Состояние перетаскивания
        self.is_dragging = False
        self.drag_start_pos = None
        self.drag_start_time = None
        self.drag_keys = None
        self.drag_codes = None
        self.drag_key_codes = None
        
        # Состояние прокрутки
        self.is_scrolling = False
        self.scroll_start_pos = None
        self.scroll_start_time = None
        self.scroll_amount = 0
        self.last_scroll_time = 0
        
        # Состояние ввода текста
        self.in_input_field = False
        self.input_start_time = None
        self.input_codes = []
        self.input_keys = []
        self.input_key_codes = []
        
        # Инициализация маппингов клавиш
        self._init_key_mappings()
        
        # Инициализация слушателей событий
        self.mouse_listener = None
        self.keyboard_listener = None
        
        # Таймер для периодического сохранения метаданных
        self.save_timer = None
        
    def _init_key_mappings(self):
        """Инициализирует маппинги кодов клавиш согласно стандартным кодам JavaScript"""
        # Маппинг специальных клавиш (code)
        self.special_keys = {
            keyboard.Key.enter: "Enter",
            keyboard.Key.tab: "Tab",
            keyboard.Key.space: "Space",
            keyboard.Key.backspace: "Backspace",
            keyboard.Key.esc: "Escape",
            keyboard.Key.caps_lock: "CapsLock",
            keyboard.Key.delete: "Delete",
            keyboard.Key.insert: "Insert",
            keyboard.Key.home: "Home",
            keyboard.Key.end: "End",
            keyboard.Key.page_up: "PageUp",
            keyboard.Key.page_down: "PageDown",
            keyboard.Key.up: "ArrowUp",
            keyboard.Key.down: "ArrowDown",
            keyboard.Key.left: "ArrowLeft",
            keyboard.Key.right: "ArrowRight",
            keyboard.Key.f1: "F1",
            keyboard.Key.f2: "F2",
            keyboard.Key.f3: "F3",
            keyboard.Key.f4: "F4",
            keyboard.Key.f5: "F5",
            keyboard.Key.f6: "F6",
            keyboard.Key.f7: "F7",
            keyboard.Key.f8: "F8",
            keyboard.Key.f9: "F9",
            keyboard.Key.f10: "F10",
            keyboard.Key.f11: "F11",
            keyboard.Key.f12: "F12",
            keyboard.Key.shift: "ShiftLeft",
            keyboard.Key.shift_r: "ShiftRight",
            keyboard.Key.ctrl: "ControlLeft",
            keyboard.Key.ctrl_r: "ControlRight",
            keyboard.Key.alt: "AltLeft",
            keyboard.Key.alt_r: "AltRight",
            keyboard.Key.cmd: "MetaLeft",
            keyboard.Key.cmd_r: "MetaRight",
            keyboard.Key.num_lock: "NumLock",
            # Mac-специфичные клавиши
            keyboard.Key.alt_gr: "AltGraph",
        }
        
        # Маппинг символов согласно стандартным кодам (code)
        self.symbol_codes = {
            '!': "Digit1",
            '@': "Digit2",
            '#': "Digit3",
            '$': "Digit4",
            '%': "Digit5",
            '^': "Digit6",
            '&': "Digit7",
            '*': "Digit8",
            '(': "Digit9",
            ')': "Digit0",
            '_': "Minus",
            '+': "Equal",
            '-': "Minus",
            '=': "Equal",
            '"': "Quote",
            "'": "Quote",
            ':': "Semicolon",
            ';': "Semicolon",
            '?': "Slash",
            '/': "Slash",
            '>': "Period",
            '.': "Period",
            '<': "Comma",
            ',': "Comma",
            '~': "Backquote",
            '`': "Backquote",
            '|': "Backslash",
            '\\': "Backslash",
            '{': "BracketLeft",
            '[': "BracketLeft",
            '}': "BracketRight",
            ']': "BracketRight",
            '№': "Digit3"
        }
        
        # Маппинг букв и цифр согласно стандартным кодам (code)
        self.letter_codes = {}
        for i in range(26):
            char = chr(97 + i)  # a-z
            self.letter_codes[char] = f"Key{char.upper()}"
            self.letter_codes[char.upper()] = f"Key{char.upper()}"
            
        for i in range(10):
            self.letter_codes[str(i)] = f"Digit{i}"
            
        # Маппинг кодов клавиш в числовые коды (keyCode)
        self.key_code_map = {
            "ControlLeft": 17, "ControlRight": 17,
            "ShiftLeft": 16, "ShiftRight": 16,
            "AltLeft": 18, "AltRight": 18,
            "MetaLeft": 224, "MetaRight": 224,  # Обновлено для Mac
            "AltGraph": 225,  # Добавлено для Mac
            "Enter": 13, "Tab": 9, "Space": 32,
            "Backspace": 8, "Escape": 27, "CapsLock": 20,
            "Delete": 46, "Insert": 45,
            "Home": 36, "End": 35, "PageUp": 33, "PageDown": 34,
            "ArrowUp": 38, "ArrowDown": 40, "ArrowLeft": 37, "ArrowRight": 39,
            "F1": 112, "F2": 113, "F3": 114, "F4": 115, "F5": 116, "F6": 117,
            "F7": 118, "F8": 119, "F9": 120, "F10": 121, "F11": 122, "F12": 123,
            "Minus": 189, "Equal": 187, "BracketLeft": 219, "BracketRight": 221,
            "Semicolon": 186, "Quote": 222, "Backquote": 192, "Backslash": 220,
            "Comma": 188, "Period": 190, "Slash": 191,
            "NumLock": 144,
            
            # Добавляем коды для Numpad клавиш
            "Numpad0": 96, "Numpad1": 97, "Numpad2": 98, "Numpad3": 99, "Numpad4": 100,
            "Numpad5": 101, "Numpad6": 102, "Numpad7": 103, "Numpad8": 104, "Numpad9": 105,
            "NumpadMultiply": 106, "NumpadAdd": 107, "NumpadSubtract": 109,
            "NumpadDecimal": 110, "NumpadDivide": 111, "NumpadEnter": 13
        }
        
        # Добавляем коды для букв A-Z (65-90)
        for i in range(26):
            char = chr(65 + i)  # A-Z
            self.key_code_map[f"Key{char}"] = 65 + i
            
        # Добавляем коды для цифр 0-9 (48-57)
        for i in range(10):
            self.key_code_map[f"Digit{i}"] = 48 + i
        
        # Маппинг для key (символьное представление)
        self.key_map = {
            "ControlLeft": "Control", "ControlRight": "Control",
            "ShiftLeft": "Shift", "ShiftRight": "Shift",
            "AltLeft": "Alt", "AltRight": "Alt",
            "MetaLeft": "Meta", "MetaRight": "Meta",
            "AltGraph": "AltGraph",  # Добавлено для Mac
            "Enter": "Enter", "Tab": "Tab", "Space": " ",
            "Backspace": "Backspace", "Escape": "Escape", "CapsLock": "CapsLock",
            "Delete": "Delete", "Insert": "Insert",
            "Home": "Home", "End": "End", "PageUp": "PageUp", "PageDown": "PageDown",
            "ArrowUp": "ArrowUp", "ArrowDown": "ArrowDown", "ArrowLeft": "ArrowLeft", "ArrowRight": "ArrowRight",
            "F1": "F1", "F2": "F2", "F3": "F3", "F4": "F4", "F5": "F5", "F6": "F6",
            "F7": "F7", "F8": "F8", "F9": "F9", "F10": "F10", "F11": "F11", "F12": "F12",
            "Minus": "-", "Equal": "=", "BracketLeft": "[", "BracketRight": "]",
            "Semicolon": ";", "Quote": "'", "Backquote": "`", "Backslash": "\\",
            "Comma": ",", "Period": ".", "Slash": "/",
            "NumLock": "NumLock",
            
            # Добавляем символы для Numpad клавиш
            "Numpad0": "0", "Numpad1": "1", "Numpad2": "2", "Numpad3": "3", "Numpad4": "4",
            "Numpad5": "5", "Numpad6": "6", "Numpad7": "7", "Numpad8": "8", "Numpad9": "9",
            "NumpadMultiply": "*", "NumpadAdd": "+", "NumpadSubtract": "-",
            "NumpadDecimal": ".", "NumpadDivide": "/", "NumpadEnter": "Enter"
        }
        
        # Добавляем символы для букв A-Z
        for i in range(26):
            char = chr(65 + i)  # A-Z
            self.key_map[f"Key{char}"] = char
            
        # Добавляем символы для цифр 0-9
        for i in range(10):
            self.key_map[f"Digit{i}"] = str(i)
            
        # Обратный маппинг для старых кодов клавиш
        self.old_to_new_code = {
            "enter": "Enter",
            "tab": "Tab",
            "space": "Space",
            "backspace": "Backspace",
            "esc": "Escape",
            "caps_lock": "CapsLock",
            "delete": "Delete",
            "insert": "Insert",
            "home": "Home",
            "end": "End",
            "page_up": "PageUp",
            "page_down": "PageDown",
            "up": "ArrowUp",
            "down": "ArrowDown",
            "left": "ArrowLeft",
            "right": "ArrowRight",
            "f1": "F1", "f2": "F2", "f3": "F3", "f4": "F4", "f5": "F5", "f6": "F6",
            "f7": "F7", "f8": "F8", "f9": "F9", "f10": "F10", "f11": "F11", "f12": "F12",
            "shift": "ShiftLeft", "shift_r": "ShiftRight",
            "ctrl": "ControlLeft", "ctrl_r": "ControlRight",
            "ctrl_l": "ControlLeft",  # Добавлено для обратной совместимости
            "alt_l": "AltLeft", "alt_r": "AltRight",
            "alt_gr": "AltGraph",  # Добавлено для Mac
            "cmd": "MetaLeft", "cmd_r": "MetaRight",
            "cmd_l": "MetaLeft",  # Добавлено для обратной совместимости
            "option": "AltLeft",  # Добавлено для Mac (альтернативное название для Alt)
            "option_r": "AltRight",  # Добавлено для Mac
            "num_lock": "NumLock"
        }
        
        # Добавляем маппинг для Key1-Key26 (A-Z)
        for i in range(1, 27):
            char = chr(64 + i)  # A-Z (ASCII 65-90)
            self.old_to_new_code[f"Key{i}"] = f"Key{char}"

    def set_fps(self, fps):
        """Устанавливает значение FPS (кадров в секунду)"""
        self.fps = fps


    
    def start_collection(self, metadata_file):
        """Начинает сбор метаданных"""
        if self.collecting:
            return
            
        self.collecting = True
        self.paused = False
        self.events = []
        self.metadata_file = metadata_file
        
        # Устанавливаем время начала записи
        self.start_time = time.time()
        self.recording_start = time.strftime("%Y-%m-%d %H:%M:%S")
        self.total_pause_time = 0
        
        # Сбрасываем состояние клавиш и мыши
        self.pressed_keys = set()
        self.key_press_times = {}
        
        # Запускаем слушателей событий
        self.mouse_listener = mouse.Listener(
            on_click=self._on_mouse_click,
            on_scroll=self._on_scroll
        )
        self.mouse_listener.start()
        
        self.keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )
        self.keyboard_listener.start()
        
        # Запускаем таймер для периодического сохранения метаданных
        self.save_timer = threading.Timer(5.0, self._save_metadata_periodically)
        self.save_timer.daemon = True
        self.save_timer.start()
    
    def pause_collection(self):
        """Приостанавливает сбор метаданных"""
        if not self.collecting or self.paused:
            return
            
        self.paused = True
        self.pause_time = time.time()
        
        # Завершаем текущие события
        if self.is_dragging:
            # Получаем текущую позицию мыши
            current_pos = mouse.Controller().position
            self._on_mouse_click(current_pos[0], current_pos[1], mouse.Button.left, False)
            
        if self.is_scrolling:
            current_pos = mouse.Controller().position
            self._finish_scroll(current_pos[0], current_pos[1])
            
        if self.in_input_field:
            self._finish_input("Escape")
    
    def resume_collection(self):
        """Возобновляет сбор метаданных после паузы"""
        if not self.collecting or not self.paused:
            return
            
        # Вычисляем время паузы
        pause_duration = time.time() - self.pause_time
        self.total_pause_time += pause_duration
        
        self.paused = False
    
    def set_screen_size(self, width, height):
        self.screen_width = width
        self.screen_height = height

    def stop_collection(self):
        """Останавливает сбор метаданных и сохраняет результаты"""
        if not self.collecting:
            return
            
        # Если запись на паузе, учитываем это
        if self.paused:
            self.resume_collection()
            
        # Останавливаем слушателей событий
        if self.mouse_listener:
            self.mouse_listener.stop()
            self.mouse_listener = None
            
        if self.keyboard_listener:
            self.keyboard_listener.stop()
            self.keyboard_listener = None
            
        # Останавливаем таймер сохранения
        if self.save_timer:
            self.save_timer.cancel()
            self.save_timer = None
            
        # Завершаем текущие события
        if self.is_dragging:
            # Получаем текущую позицию мыши
            current_pos = mouse.Controller().position
            self._on_mouse_click(current_pos[0], current_pos[1], mouse.Button.left, False)
            
        if self.is_scrolling:
            current_pos = mouse.Controller().position
            self._finish_scroll(current_pos[0], current_pos[1])
            
        if self.in_input_field:
            self._finish_input("Escape")
            
        # Сохраняем метаданные
        self._save_metadata()

        # В методе stop_collection перед self.collecting = False:
# Отменяем все таймеры длительных нажатий
        for code, timer in self.long_press_timers.items():
            timer.cancel()
        self.long_press_timers.clear()

        
        self.collecting = False
    
    def _save_metadata_periodically(self):
        """Периодически сохраняет метаданные"""
        if not self.collecting:
            return
            
        self._save_metadata()
        
        # Перезапускаем таймер
        self.save_timer = threading.Timer(5.0, self._save_metadata_periodically)
        self.save_timer.daemon = True
        self.save_timer.start()
    
    def _generate_id(self):
        """Генерирует короткий идентификатор для события"""
        # Создаем UUID и берем только первые 8 символов
        return str(uuid.uuid4())[:4]
   
    
    def _get_current_timestamp(self):
        """Возвращает текущее время относительно начала записи с учетом пауз"""
        if self.paused:
            return round(self.pause_time - self.start_time - self.total_pause_time, 3)
        return round(time.time() - self.start_time - self.total_pause_time, 3)


    
    def _save_metadata(self):
        """Сохраняет собранные метаданные в файл"""
        if not self.metadata_file:
            return
            
        # Создаем структуру метаданных
        metadata = {
            "version": "1.0",
            "recordingDuration": round(self._get_current_timestamp(), 3),
            "screen": {
                "width": self.screen_width,
                "height": self.screen_height
            },
            "fps": self.fps,
            "events": self.events
        }
            
        # Сохраняем в файл
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)



    
    def _adjust_coordinates(self, x, y):
        """Корректирует координаты мыши при необходимости"""
        # Здесь можно добавить логику для корректировки координат,
        # например, для учета масштабирования экрана
        return x, y
    
    def _map_key_to_code(self, key):
        """Преобразует клавишу в код клавиши согласно стандартным кодам JavaScript"""
        try:
            # Для специальных клавиш
            if key in self.special_keys:
                return self.special_keys[key]
            
            # Для обычных клавиш
            if hasattr(key, 'char') and key.char:
                char = key.char
                
                # Проверяем, есть ли символ в маппинге символов
                if char in self.symbol_codes:
                    return self.symbol_codes[char]
                    
                # Проверяем, есть ли символ в маппинге букв и цифр
                if char in self.letter_codes:
                    return self.letter_codes[char]
                
                # Если символ не найден в маппингах, используем ASCII код
                return f"Key{ord(char)}"
            
            # Проверка на Mac-специфичные клавиши по vk-коду
            if hasattr(key, 'vk'):
                # Command key на Mac часто имеет vk=55 или vk=54
                if key.vk == 55 or key.vk == 54:
                    return "MetaLeft"
                # Option key на Mac часто имеет vk=58
                elif key.vk == 58:
                    return "AltLeft"
                # Правый Option key на Mac
                elif key.vk == 61:
                    return "AltRight"
                # AltGraph key
                elif key.vk == 225:
                    return "AltGraph"
                
                # Проверка на Numpad клавиши
                if 96 <= key.vk <= 105:  # Numpad 0-9
                    return f"Numpad{key.vk - 96}"
                elif key.vk == 106:
                    return "NumpadMultiply"
                elif key.vk == 107:
                    return "NumpadAdd"
                elif key.vk == 109:
                    return "NumpadSubtract"
                elif key.vk == 110:
                    return "NumpadDecimal"
                elif key.vk == 111:
                    return "NumpadDivide"
                elif key.vk == 144:
                    return "NumLock"
            
            # Если ничего не подошло, возвращаем строковое представление
            key_str = str(key).replace('Key.', '')
            
            # Проверка на key26
            if key_str.lower() == 'key26':
                return "KeyZ"  # Z - 26-я буква английского алфавита
            
            # Проверяем, есть ли в обратном маппинге
            if key_str in self.old_to_new_code:
                return self.old_to_new_code[key_str]
            
            # Проверка на специальные клавиши Mac
            if key_str == 'cmd' or key_str == 'cmd_l':
                return "MetaLeft"
            elif key_str == 'cmd_r':
                return "MetaRight"
            elif key_str == 'option' or key_str == 'alt':
                return "AltLeft"
            elif key_str == 'option_r' or key_str == 'alt_r':
                return "AltRight"
            elif key_str == 'alt_gr':
                return "AltGraph"
            
            # Проверка на нестандартные коды типа "Key26"
            if key_str.startswith('Key') and key_str[3:].isdigit():
                num = int(key_str[3:])
                if 1 <= num <= 26:  # Если это число от 1 до 26
                    # Преобразуем в стандартный код клавиши (A-Z)
                    char = chr(64 + num)  # A=65, поэтому начинаем с 64+1
                    return f"Key{char}"
            
            # Если ключ не найден в маппинге, возвращаем стандартный код
            # вместо строкового представления
            return key_str
        
        except Exception as e:
            # Добавляем логирование ошибки для отладки
            print(f"Error mapping key {key}: {e}")
            return str(key)

    
    def _get_key_code_number(self, code):
        """Возвращает числовой код клавиши"""
        return self.key_code_map.get(code, 0)
    
    def _on_key_press(self, key):
        """Обрабатывает нажатие клавиши"""
        if not self.collecting or self.paused:
            return
            
        timestamp = self._get_current_timestamp()
        code = self._map_key_to_code(key)  # code (DOM standard)
        
        # Нормализуем код клавиши для Key1-Key26
        if code.startswith('Key') and code[3:].isdigit():
            num = int(code[3:])
            if 1 <= num <= 26:
                code = f"Key{chr(64 + num)}"
        
        # Если клавиша уже нажата, игнорируем повторное нажатие
        if code in self.pressed_keys:
            return
            
        # Добавляем клавишу в список нажатых
        self.pressed_keys.add(code)
        self.key_press_times[code] = timestamp
        
        # Создаем таймер для длительного нажатия, если его еще нет
        if code not in self.long_press_timers:
            timer = threading.Timer(self.long_press_threshold, self._handle_long_press, args=[code])
            timer.daemon = True
            timer.start()
            self.long_press_timers[code] = timer
        
        # Получаем keyCode (устаревший, но все еще используемый)
        key_code = self.key_code_map.get(code, 0)
        
        # Получаем key (символьное представление)
        key_char = self.key_map.get(code, code)
        
        # Проверяем на горячую клавишу
        hotkey = self._check_for_hotkey(code)
        if hotkey:
            # Создаем событие hotkey с полной информацией о клавишах
            keys_list = list(self.pressed_keys)
            key_codes_list = [self.key_code_map.get(k, 0) for k in keys_list]
            key_chars_list = [self.key_map.get(k, k) for k in keys_list]
            
            self.events.append({
                "id": self._generate_id(),
                "type": "hotkey",
                "time": timestamp,
                "hotkey": hotkey,
                "keys": key_chars_list,  # Символьные представления
                "codes": keys_list,      # DOM стандартные коды
                "keyCodes": key_codes_list  # Числовые коды
            })
        else:
            # Создаем событие keyPress с полной информацией о клавише
            self.events.append({
                "id": self._generate_id(),
                "type": "keyPress",
                "time": timestamp,
                "key": key_char,      # Символьное представление
                "code": code,         # DOM стандартный код
                "keyCode": key_code   # Числовой код
            })
            
        # Список клавиш, которые не должны начинать ввод текста
        non_input_keys = {
            "ControlLeft", "ControlRight", "ShiftLeft", "ShiftRight",
            "AltLeft", "AltRight", "MetaLeft", "MetaRight", "CapsLock",
            "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12",
            "Escape", "Tab", "Enter", "Backspace", "Delete", "Insert",
            "Home", "End", "PageUp", "PageDown",
            "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight",
            "NumLock"
        }
        
        # Если уже идет ввод текста, добавляем код клавиши
        if self.in_input_field:
            # Проверяем на клавиши, которые завершают ввод
            if code in {"Enter", "Tab", "Escape"}:
                # Завершаем ввод текста
                self._finish_input(code)
            # Добавляем все клавиши к вводу, включая модификаторы и Backspace
            else:
                # Добавляем информацию о клавише к вводу
                self.input_codes.append(code)
                self.input_keys.append(key_char)
                self.input_key_codes.append(key_code)
        # Если это начало ввода текста (только если это не первое нажатие и не служебная клавиша)
        elif code not in non_input_keys and len(self.events) >= 2:
            # Проверяем предыдущее событие
            prev_event = self.events[-2] if len(self.events) > 1 else None
            
            # Начинаем ввод текста только если предыдущее событие было нажатием клавиши
            # и прошло не более 1 секунды
            if (prev_event and prev_event.get("type") == "keyPress" and 
                timestamp - prev_event.get("time", 0) < 1.0 and
                prev_event.get("code") not in non_input_keys):
                
                # Удаляем предыдущее событие keyPress, так как оно станет частью ввода
                prev_key_event = self.events.pop()
                self.events.pop()  # Удаляем текущее событие keyPress, которое мы только что добавили
                
                self.in_input_field = True
                self.input_start_time = prev_event.get("time")  # Используем время предыдущего события
                
                # Добавляем предыдущую клавишу как начало ввода
                self.input_codes = [prev_event.get("code"), code]
                self.input_keys = [prev_event.get("key"), key_char]
                self.input_key_codes = [prev_event.get("keyCode", 0), key_code]

    
    
    def _on_key_release(self, key):
        """Обрабатывает отпускание клавиши"""
        if not self.collecting or self.paused:
            return
            
        code = self._map_key_to_code(key)
        
        # Если клавиша не была нажата, игнорируем
        if code not in self.pressed_keys:
            return
            
        # Удаляем клавишу из списка нажатых
        self.pressed_keys.remove(code)
        
        # Отменяем таймер длительного нажатия, если он существует
        if code in self.long_press_timers:
            self.long_press_timers[code].cancel()
            del self.long_press_timers[code]
        
        # Если идет ввод текста и отпущена клавиша Enter, Tab или Escape, завершаем ввод
        if self.in_input_field and code in {"Enter", "Tab", "Escape"}:
            self._finish_input(code)


    
    def _check_for_hotkey(self, key_code):
        """Проверяет, является ли текущая комбинация клавиш горячей клавишей"""
        # Если нажата только одна клавиша, это не горячая клавиша
        if len(self.pressed_keys) <= 1:
            return False
            
        # Преобразуем Key1-Key26 в стандартные коды DOM
        normalized_keys = set()
        for k in self.pressed_keys:
            if k.startswith('Key') and k[3:].isdigit():
                num = int(k[3:])
                if 1 <= num <= 26:
                    normalized_keys.add(f"Key{chr(64 + num)}")
                else:
                    normalized_keys.add(k)
            else:
                normalized_keys.add(k)
        
        # Проверяем известные комбинации горячих клавиш
        modifiers = {"ControlLeft", "ControlRight", "ShiftLeft", "ShiftRight", 
                    "AltLeft", "AltRight", "MetaLeft", "MetaRight"}
        
        # Должен быть хотя бы один модификатор
        has_modifier = any(k in modifiers for k in normalized_keys)
        if not has_modifier:
            return False
            
        # Известные комбинации
        known_hotkeys = {
            frozenset(["ControlLeft", "KeyC"]): "Ctrl+C",
            frozenset(["ControlRight", "KeyC"]): "Ctrl+C",
            frozenset(["ControlLeft", "KeyV"]): "Ctrl+V",
            frozenset(["ControlRight", "KeyV"]): "Ctrl+V",
            frozenset(["ControlLeft", "KeyX"]): "Ctrl+X",
            frozenset(["ControlRight", "KeyX"]): "Ctrl+X",
            frozenset(["ControlLeft", "KeyZ"]): "Ctrl+Z",
            frozenset(["ControlRight", "KeyZ"]): "Ctrl+Z",
            frozenset(["ControlLeft", "KeyY"]): "Ctrl+Y",
            frozenset(["ControlRight", "KeyY"]): "Ctrl+Y",
            frozenset(["ControlLeft", "KeyA"]): "Ctrl+A",
            frozenset(["ControlRight", "KeyA"]): "Ctrl+A",
            frozenset(["ControlLeft", "KeyS"]): "Ctrl+S",
            frozenset(["ControlRight", "KeyS"]): "Ctrl+S",
            frozenset(["ControlLeft", "KeyF"]): "Ctrl+F",
            frozenset(["ControlRight", "KeyF"]): "Ctrl+F",
            frozenset(["ControlLeft", "KeyP"]): "Ctrl+P",
            frozenset(["ControlRight", "KeyP"]): "Ctrl+P",
            frozenset(["ControlLeft", "KeyO"]): "Ctrl+O",
            frozenset(["ControlRight", "KeyO"]): "Ctrl+O",
            frozenset(["ControlLeft", "KeyN"]): "Ctrl+N",
            frozenset(["ControlRight", "KeyN"]): "Ctrl+N",
            frozenset(["AltLeft", "F4"]): "Alt+F4",
            frozenset(["AltRight", "F4"]): "Alt+F4",
            frozenset(["ControlLeft", "ShiftLeft", "KeyZ"]): "Ctrl+Shift+Z",
            frozenset(["ControlRight", "ShiftLeft", "KeyZ"]): "Ctrl+Shift+Z",
            frozenset(["ControlLeft", "ShiftRight", "KeyZ"]): "Ctrl+Shift+Z",
            frozenset(["ControlRight", "ShiftRight", "KeyZ"]): "Ctrl+Shift+Z",
        }
        
        # Проверяем, соответствует ли текущий набор клавиш известной горячей клавише
        current_keys = frozenset(normalized_keys)
        for hotkey_keys, hotkey_name in known_hotkeys.items():
            # Преобразуем key_code, если это Key1-Key26
            normalized_key_code = key_code
            if key_code.startswith('Key') and key_code[3:].isdigit():
                num = int(key_code[3:])
                if 1 <= num <= 26:
                    normalized_key_code = f"Key{chr(64 + num)}"
            
            if hotkey_keys.issubset(current_keys) and normalized_key_code in hotkey_keys:
                return hotkey_name
                
        # Если не нашли известную комбинацию, но есть модификатор и другая клавиша,
        # создаем пользовательскую горячую клавишу
        non_modifiers = [k for k in normalized_keys if k not in modifiers]
        
        # Преобразуем key_code, если это Key1-Key26
        normalized_key_code = key_code
        if key_code.startswith('Key') and key_code[3:].isdigit():
            num = int(key_code[3:])
            if 1 <= num <= 26:
                normalized_key_code = f"Key{chr(64 + num)}"
        
        if non_modifiers and normalized_key_code in non_modifiers:
            # Формируем имя горячей клавиши
            modifier_parts = []
            if "ControlLeft" in normalized_keys or "ControlRight" in normalized_keys:
                modifier_parts.append("Ctrl")
            if "ShiftLeft" in normalized_keys or "ShiftRight" in normalized_keys:
                modifier_parts.append("Shift")
            if "AltLeft" in normalized_keys or "AltRight" in normalized_keys:
                modifier_parts.append("Alt")
            if "MetaLeft" in normalized_keys or "MetaRight" in normalized_keys:
                modifier_parts.append("Win")
                
            # Используем нормализованный код клавиши для отображения
            key_part = self.key_map.get(normalized_key_code, normalized_key_code)
            return "+".join(modifier_parts + [key_part])
            
        return False


    
    def _finish_input(self, reason_code):
        """Завершает событие ввода текста"""
        if not self.in_input_field:
            return
            
        timestamp = self._get_current_timestamp()
        reason_key = self.key_map.get(reason_code, reason_code)

        # Формируем текстовое значение из введенных символов
        input_value = ""
        for i in range(len(self.input_codes)):
            code = self.input_codes[i]
            key = self.input_keys[i]
            
            # Обрабатываем Backspace (удаляем последний символ)
            if code == "Backspace":
                if input_value:  # Если есть что удалять
                    input_value = input_value[:-1]
            # Пропускаем другие специальные клавиши, которые не добавляют символы
            elif code in ["Delete", "ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown",
                        "Home", "End", "PageUp", "PageDown"]:
                pass
            # Пропускаем модификаторы
            elif code in ["ControlLeft", "ControlRight", "ShiftLeft", "ShiftRight", 
                        "AltLeft", "AltRight", "MetaLeft", "MetaRight"]:
                pass
            # Обрабатываем Enter как перевод строки
            elif code == "Enter":
                input_value += "\n"
            # Обрабатываем Tab как табуляцию
            elif code == "Tab":
                input_value += "\t"
            # Обрабатываем пробел
            elif code == "Space":
                input_value += " "
            # Для букв (KeyA-KeyZ)
            elif code.startswith("Key"):
                char = code[3:]  # Извлекаем букву из кода (например, "A" из "KeyA")
                # Учитываем регистр
                if "ShiftLeft" in self.pressed_keys or "ShiftRight" in self.pressed_keys:
                    input_value += char
                else:
                    input_value += char.lower()
            # Для цифр (Digit0-Digit9)
            elif code.startswith("Digit"):
                digit = code[5:]  # Извлекаем цифру из кода (например, "1" из "Digit1")
                # Учитываем Shift для символов над цифрами
                if "ShiftLeft" in self.pressed_keys or "ShiftRight" in self.pressed_keys:
                    shift_symbols = {
                        "1": "!", "2": "@", "3": "#", "4": "$", "5": "%",
                        "6": "^", "7": "&", "8": "*", "9": "(", "0": ")"
                    }
                    input_value += shift_symbols.get(digit, digit)
                else:
                    input_value += digit
            # Для других символов используем символьное представление
            elif len(key) == 1:
                input_value += key
        
        # Создаем событие input с полной информацией о клавишах
        self.events.append({
            "id": self._generate_id(),
            "type": "input",
            "time": self.input_start_time,
            "duration": round(timestamp - self.input_start_time, 3),
            "keys": self.input_keys,    # Символьные представления
            "codes": self.input_codes,      # DOM стандартные коды
            "keyCodes": self.input_key_codes,  # Числовые коды
            "length": len(self.input_codes),
            "value": input_value,           # Добавляем текстовое значение
            "reason": reason_key
        })
        
        # Сбрасываем состояние ввода
        self.in_input_field = False
        self.input_start_time = None
        self.input_codes = []
        self.input_keys = []
        self.input_key_codes = []


    def _on_mouse_click(self, x, y, button, pressed):
        """Обрабатывает клики мышью"""
        if not self.collecting or self.paused:
            return
            
        # Завершаем ввод текста при любом клике мыши (нажатии кнопки)
        if pressed and self.in_input_field:
            self._finish_input("Click")
            
        # Корректируем координаты
        x, y = self._adjust_coordinates(x, y)
        timestamp = self._get_current_timestamp()
        
        # Подготовка информации о нажатых клавишах
        if self.pressed_keys:
            keys = [self.key_map.get(code, code) for code in self.pressed_keys]
            codes = list(self.pressed_keys)
            key_codes = [self.key_code_map.get(code, 0) for code in self.pressed_keys]
        else:
            keys = None
            codes = None
            key_codes = None
            
        if pressed:
            # Обработка нажатия кнопки мыши
            if button == mouse.Button.left:
                # Начало потенциального drag and drop
                self.drag_start_pos = (x, y)
                self.drag_start_time = timestamp
                self.is_dragging = True
                
                # Сохраняем информацию о нажатых клавишах для потенциального клика
                self.drag_keys = keys
                self.drag_codes = codes
                self.drag_key_codes = key_codes
                
                # НЕ создаем событие leftClick сразу - подождем, чтобы определить, 
                # является ли это кликом или началом перетаскивания
                    
            elif button == mouse.Button.right:
                self.events.append({
                    "id": self._generate_id(),
                    "type": "rightClick",
                    "time": timestamp,
                    "x": x,
                    "y": y,
                    "keys": keys,
                    "codes": codes,
                    "keyCodes": key_codes
                })
        else:
            # Обработка отпускания кнопки мыши
            if button == mouse.Button.left and self.is_dragging:
                # Завершение drag and drop
                end_pos = (x, y)
                end_time = timestamp
                
                # Проверяем, было ли реальное перетаскивание
                if (abs(self.drag_start_pos[0] - end_pos[0]) > 5 or
                    abs(self.drag_start_pos[1] - end_pos[1]) > 5):
                    
                    # Создаем событие drag
                    self.events.append({
                        "id": self._generate_id(),
                        "type": "drag",
                        "time": self.drag_start_time,
                        "startTime": self.drag_start_time,
                        "endTime": end_time,
                        "x": self.drag_start_pos[0],
                        "y": self.drag_start_pos[1],
                        "start": {
                            "x": self.drag_start_pos[0],
                            "y": self.drag_start_pos[1],
                            "time": self.drag_start_time
                        },
                        "end": {
                            "x": end_pos[0],
                            "y": end_pos[1],
                            "time": end_time
                        },
                        "duration": round(end_time - self.drag_start_time, 3),
                        "keys": self.drag_keys,
                        "codes": self.drag_codes,
                        "keyCodes": self.drag_key_codes
                    })
                else:
                    # Если не было реального перетаскивания, то это был клик
                    # Проверка на двойной клик
                    if len(self.events) > 0 and self.events[-1].get("type") == "leftClick":
                        last_click_time = self.events[-1].get("time", 0)
                        if timestamp - last_click_time < 0.5:  # Если прошло менее 0.5 секунд
                            # Удаляем предыдущий клик
                            self.events.pop()
                            # Добавляем двойной клик
                            self.events.append({
                                "id": self._generate_id(),
                                "type": "doubleClick",
                                "time": timestamp,
                                "x": self.drag_start_pos[0],
                                "y": self.drag_start_pos[1],
                                "keys": self.drag_keys,
                                "codes": self.drag_codes,
                                "keyCodes": self.drag_key_codes
                            })
                        else:
                            # Обычный клик левой кнопкой
                            self.events.append({
                                "id": self._generate_id(),
                                "type": "leftClick",
                                "time": self.drag_start_time,  # Используем время начала нажатия
                                "x": self.drag_start_pos[0],
                                "y": self.drag_start_pos[1],
                                "keys": self.drag_keys,
                                "codes": self.drag_codes,
                                "keyCodes": self.drag_key_codes
                            })
                    else:
                        # Обычный клик левой кнопкой
                        self.events.append({
                            "id": self._generate_id(),
                            "type": "leftClick",
                            "time": self.drag_start_time,  # Используем время начала нажатия
                            "x": self.drag_start_pos[0],
                            "y": self.drag_start_pos[1],
                            "keys": self.drag_keys,
                            "codes": self.drag_codes,
                            "keyCodes": self.drag_key_codes
                        })
                    
                # Сбрасываем состояние перетаскивания
                self.is_dragging = False
                self.drag_start_pos = None
                self.drag_start_time = None
                self.drag_keys = None
                self.drag_codes = None
                self.drag_key_codes = None




    def _handle_long_press(self, code):
        """Обрабатывает длительное нажатие клавиши"""
        if not self.collecting or self.paused or code not in self.pressed_keys:
            return
            
        timestamp = self._get_current_timestamp()
        press_time = self.key_press_times.get(code)
        
        if press_time and (timestamp - press_time) >= self.long_press_threshold:
            # Получаем информацию о клавише
            key_char = self.key_map.get(code, code)
            key_code = self.key_code_map.get(code, 0)
            
            # Создаем событие keyLongPress
            self.events.append({
                "id": self._generate_id(),
                "type": "keyLongPress",
                "time": press_time,  # Время начала нажатия
                "duration": round(timestamp - press_time, 3),
                "key": key_char,      # Символьное представление
                "code": code,         # DOM стандартный код
                "keyCode": key_code   # Числовой код
            })
            
            # Удаляем таймер из словаря, так как он уже выполнился
            if code in self.long_press_timers:
                del self.long_press_timers[code]


    
    def _on_scroll(self, x, y, dx, dy):
        """Обрабатывает прокрутку колесиком мыши"""
        if not self.collecting or self.paused:
            return
            
        # Завершаем ввод текста при прокрутке
        if self.in_input_field:
            self._finish_input("Scroll")
            
        # Корректируем координаты
        x, y = self._adjust_coordinates(x, y)
        timestamp = self._get_current_timestamp()
        
        # Определяем направление прокрутки
        # В pynput: положительное dy означает прокрутку вверх, отрицательное - вниз
        # Для единообразия с веб-стандартами: положительное значение = вниз, отрицательное = вверх
        # Определяем направление прокрутки
# В pynput: положительное dy означает прокрутку вверх, отрицательное - вниз
# Мы сохраняем это соответствие: положительное значение = вверх, отрицательное = вниз
        scroll_direction = 1 if dy > 0 else -1  # Положительное = вверх, отрицательное = вниз
        scroll_direction_name = "up" if dy > 0 else "down"

        
        # Если уже идет прокрутка, обновляем ее
        if self.is_scrolling:
            # Если прошло более 0.5 секунд с последней прокрутки или изменилось направление,
            # завершаем предыдущую прокрутку
            current_direction = 1 if self.scroll_amount > 0 else -1
            if timestamp - self.last_scroll_time > 0.5 or current_direction != scroll_direction:
                self._finish_scroll(x, y)
                
                # Начинаем новую прокрутку
                self.is_scrolling = True
                self.scroll_start_pos = (x, y)
                self.scroll_start_time = timestamp
                self.scroll_amount = scroll_direction
                self.scroll_direction_name = scroll_direction_name
            else:
                # Продолжаем текущую прокрутку
                self.scroll_amount += scroll_direction
        else:
            # Начинаем новую прокрутку
            self.is_scrolling = True
            self.scroll_start_pos = (x, y)
            self.scroll_start_time = timestamp
            self.scroll_amount = scroll_direction
            self.scroll_direction_name = scroll_direction_name
            
        self.last_scroll_time = timestamp

    def _finish_scroll(self, end_x, end_y):
        """Завершает событие прокрутки после паузы"""
        if not self.is_scrolling:
            return
            
        timestamp = self._get_current_timestamp()
        
        # Подготовка информации о нажатых клавишах
        if self.pressed_keys:
            keys = [self.key_map.get(code, code) for code in self.pressed_keys]
            codes = list(self.pressed_keys)
            key_codes = [self.key_code_map.get(code, 0) for code in self.pressed_keys]
        else:
            keys = None
            codes = None
            key_codes = None
        
        # Определяем направление прокрутки на основе накопленного значения
        direction = "up" if self.scroll_amount > 0 else "down"

        
        # Создаем событие scroll
        self.events.append({
            "id": self._generate_id(),
            "type": "scroll",
            "time": self.scroll_start_time,
            "startTime": self.scroll_start_time,
            "endTime": timestamp,
            "start": {
                "x": self.scroll_start_pos[0],
                "y": self.scroll_start_pos[1],
                "time": self.scroll_start_time
            },
            "end": {
                "x": end_x,
                "y": end_y,
                "time": timestamp
            },
            "scrollAmount": self.scroll_amount,  # Абсолютное значение для количества "щелчков"
            "direction": direction,  # Явное указание направления
            "duration": round(timestamp - self.scroll_start_time, 3),
            "keys": keys,
            "codes": codes,
            "keyCodes": key_codes
        })
        
        # Сбрасываем состояние прокрутки
        self.is_scrolling = False
        self.scroll_start_pos = None
        self.scroll_start_time = None
        self.scroll_amount = 0
        self.scroll_direction_name = None
    
        
        
    

        
    def add_custom_event(self, event_type, data=None):
        """Добавляет пользовательское событие в метаданные"""
        if not self.collecting:
            return
            
        timestamp = self._get_current_timestamp()
        
        event = {
            "id": self._generate_id(),
            "type": event_type,
            "time": timestamp
        }
        
        if data:
            event.update(data)
            
        self.events.append(event)
        
        # Сохраняем метаданные после добавления пользовательского события
        self._save_metadata()
        
        return event["id"]
    
    def get_events(self):
        """Возвращает список всех собранных событий"""
        return self.events
    
    def get_recording_duration(self):
        """Возвращает текущую продолжительность записи в секундах"""
        return self._get_current_timestamp()
    
    def get_recording_start(self):
        """Возвращает время начала записи"""
        return self.recording_start
    
    def get_metadata_file(self):
        """Возвращает путь к файлу метаданных"""
        return self.metadata_file
    
    def is_collecting(self):
        """Возвращает True, если сбор метаданных активен"""
        return self.collecting
    
    def is_paused(self):
        """Возвращает True, если сбор метаданных приостановлен"""
        return self.paused
    
    def get_pressed_keys(self):
        """Возвращает список текущих нажатых клавиш"""
        return list(self.pressed_keys)
    
    def get_key_press_times(self):
        """Возвращает словарь времен нажатия клавиш"""
        return self.key_press_times.copy()
    
    def get_total_pause_time(self):
        """Возвращает общее время пауз в секундах"""
        return self.total_pause_time
    
    def clear_events(self):
        """Очищает список событий"""
        self.events = []
        
        # Сохраняем пустые метаданные
        self._save_metadata()
    
    def __del__(self):
        """Деструктор класса"""
        # Останавливаем сбор метаданных при удалении объекта
        self.stop_collection()
