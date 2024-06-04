import threading
import subprocess

def run_application():
    # Запуск файла Application.py
    subprocess.run(["python", "Application.py"])

def run_rs485_bd():
    # Запуск файла RS485_BD.py
    subprocess.run(["python", "RS485_BD.py"])

if __name__ == "__main__":
    # Создание потоков
    thread1 = threading.Thread(target=run_application)
    thread2 = threading.Thread(target=run_rs485_bd)

    # Запуск потоков
    thread1.start()
    thread2.start()

    # Ожидание завершения потоков
    thread1.join()
    thread2.join()

    print("Оба потока завершились.")