import os
import sys
import shutil
import subprocess

def build_executable():
    print("Начало сборки приложения...")
    
    # Очистка предыдущих сборок
    if os.path.exists("build"):
        shutil.rmtree("build")
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    
    # Команда для PyInstaller
    cmd = [
        "pyinstaller",
        "--name=Screencaster",
        "--windowed",  # Без консольного окна
        "--onefile",   # Один исполняемый файл
        "main.py"
    ]
    
    # Запуск PyInstaller
    try:
        subprocess.run(cmd, check=True)
        print("Сборка успешно завершена!")
        print(f"Исполняемый файл находится в: {os.path.abspath('dist/Screencaster.exe')}")
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при сборке: {e}")
        return False
    
    return True

if __name__ == "__main__":
    build_executable()