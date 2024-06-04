import socket
from datetime import datetime
from pymongo import MongoClient

HOST = ''  # IP-адрес ESP8266
PORT = 8888  # Порт, на котором ESP8266 отправляет данные

try:
    client = MongoClient('localhost', 27017)
    db = client.diplom_DB
    todos = db.diplom_collection
    alerts = db.alerts_collection
    print("Connected successfully!!!")
except:
    print("Could not connect to MongoDB")

data_dict = {}

def main():
    # Создаем сокет и связываем его с хостом и портом
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PORT))
    s.listen(1)

    print(f"Listening for connections on {HOST}:{PORT}...")

    while True:
        # Принимаем входящее подключение
        conn, addr = s.accept()
        print(f"Connected by {addr[0]}:{addr[1]}")

        # Читаем данные из подключения
        data = conn.recv(1024).decode()
        if data:
            print("Received data:")
            print(data)
            if len(data) > 0:
                data_dict = parse_data_string(data)
                if data_dict is not None:
                    save_data_to_mongo(data_dict)
                    check_data_fields(data_dict)
                else:
                    print("Miss data")

        # Закрываем подключение
        conn.close()


def save_alert_to_mongo(alert_dict):
    try:
        alerts.insert_one(alert_dict)
        print("Alert saved to MongoDB")
    except Exception as e:
        print("Error saving alert to MongoDB:", str(e))


def check_data_fields(data_dict):
    temperature = data_dict.get('temperature')
    humidity = data_dict.get('humidity')
    correctedPPM = data_dict.get('correctedPPM')
    luminosity = data_dict.get('luminosity')
    answer_dict = {}

    if temperature is not None and (temperature < 18 or temperature > 30):
        answer_dict['ardID'] = data_dict.get('ardID')
        answer_dict['message'] = "Показатель температуры выходит за границы нормальных значений - " + str(temperature)
        answer_dict['timestamp'] = datetime.now()
        save_alert_to_mongo(answer_dict)

    if humidity is not None and (humidity < 30 or humidity > 60):
        answer_dict['ardID'] = data_dict.get('ardID')
        answer_dict['message'] = "Показатель влажности выходит за границы нормальных значений - " + str(humidity)
        answer_dict['timestamp'] = datetime.now()
        save_alert_to_mongo(answer_dict)

    if correctedPPM is not None and (correctedPPM > 1400):
        answer_dict['ardID'] = data_dict.get('ardID')
        answer_dict['message'] = "Показатель CO2 выходит за границы нормальных значений - " + str(correctedPPM)
        answer_dict['timestamp'] = datetime.now()
        save_alert_to_mongo(answer_dict)

    if luminosity is not None and (luminosity < 30):
        answer_dict['ardID'] = data_dict.get('ardID')
        answer_dict['message'] = "Показатель освещенности выходит за границы нормальных значений - " + str(luminosity)
        answer_dict['timestamp'] = datetime.now()
        save_alert_to_mongo(answer_dict)


def parse_data_string(data_str):
    # Разделяем строку по символу '/'
    data_parts = data_str.strip().split('/')

    # Проверяем, что в data_parts есть ожидаемое количество элементов
    if len(data_parts) != 9:
        return None

    # Создаем словарь для хранения данных
    data_dict = {}

    # Заполняем словарь данными из строки
    data_dict['ardID'] = int(data_parts[0])
    data_dict['temperature'] = float(data_parts[1])
    data_dict['humidity'] = float(data_parts[2])
    data_dict['rzero'] = float(data_parts[3])
    data_dict['correctedRZero'] = float(data_parts[4])
    data_dict['resistance'] = float(data_parts[5])
    data_dict['ppm'] = float(data_parts[6])
    data_dict['correctedPPM'] = float(data_parts[7])
    data_dict['luminosity'] = float(data_parts[8])

    return data_dict


def save_data_to_mongo(dict):
    # Добавляем текущую дату-время в словарь данных
    dict['timestamp'] = datetime.now()

    # Вставляем данные в коллекцию
    result = todos.insert_one(dict)
    print(f"Данные успешно сохранены в MongoDB. ID документа: {result.inserted_id}")


if __name__ == '__main__':
    main()