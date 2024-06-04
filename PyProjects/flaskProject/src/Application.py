import os
import shutil
import threading
import matplotlib
import schedule
from flet import *
from matplotlib import pyplot as plt
matplotlib.use('Agg')
from pymongo import MongoClient
from datetime import datetime, timedelta
import time


# Подключение к MongoDB
client = MongoClient("mongodb://localhost:27017")
db = client["diplom_DB"]
collection = db["diplom_collection"]
alerts = db["alerts_collection"]


def clear_directory(directory_path):
    try:
        shutil.rmtree(directory_path)  # Удаление директории и всех ее содержимого
        os.makedirs(directory_path)  # Повторное создание директории
        print(f"Directory {directory_path} cleared.")
    except Exception as e:
        print(f"Error clearing directory {directory_path}: {str(e)}")


def delete_alert(alert_id):
    try:
        result = alerts.delete_one({'_id': alert_id})
        if result.deleted_count > 0:
            print("Alert deleted from MongoDB")
        else:
            print("Alert not found in MongoDB")
    except Exception as e:
        print("Error deleting alert from MongoDB:", str(e))


def get_all_alerts_from_mongo():
    try:
        all_alerts = list(alerts.find())
        return all_alerts
    except Exception as e:
        print("Error retrieving alerts from MongoDB:", str(e))
        return []


def get_latest_record(ard_id):
    # Получение последней записи, отсортированной по времени
    latest_record = collection.find_one(
        {"ardID": ard_id},
        sort=[("timestamp", -1)]
    )
    print(latest_record)
    if latest_record:
        return latest_record
    else:
        return None


def get_records_by_time(ard_id, time_range="hour"):

    # Определение временного интервала
    end_time = datetime.now()
    if time_range == 'hour':
        start_time = end_time - timedelta(hours=1)
    elif time_range == 'day':
        start_time = end_time - timedelta(days=1)
    elif time_range == 'week':
        start_time = end_time - timedelta(weeks=1)
    elif time_range == 'month':
        start_time = end_time - timedelta(days=30)

    # Формирование запроса к MongoDB
    query = {'ardID': ard_id, 'timestamp': {'$gte': start_time, '$lte': end_time}}
    result = collection.find(query)

    # Возвращение найденных записей
    return list(result)


def plot_records(records, timestamp):
    timestamps = [record['timestamp'] for record in records]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(30, 16))

    fields1 = ['temperature', 'humidity', 'luminosity']
    fields2 = ['correctedPPM']

    for field in fields1:
        values = [record.get(field) for record in records]
        ax1.plot(timestamps, values, label=field)

    for field in fields2:
        values = [record.get(field) for record in records]
        ax2.plot(timestamps, values, label=field, color='red')

    # Настройка для первого графика
    ax1.set_xlabel('Timestamp', fontsize=18)
    ax1.set_ylabel('Value', fontsize=18)
    ax1.tick_params(axis='both', labelsize=18)
    ax1.grid(True)
    ax1.legend()

    # Настройка для второго графика
    ax2.set_xlabel('Timestamp', fontsize=18)
    ax2.set_ylabel('PPM', fontsize=18)
    ax2.tick_params(axis='both', labelsize=18)
    ax2.grid(True)
    ax2.legend()

    plt.tight_layout()
    plt.savefig(f"../assets/plots/plot_{records[0]['ardID']}_{timestamp}.png")
    plt.close(fig)



def get_unique_ard_ids():
    unique_ids = collection.distinct("ardID")
    return list(unique_ids)


class App(UserControl):
    def __init__(self, pg):
        super().__init__()
        self.pg = pg
        self.animation_style = animation.Animation(500, AnimationCurve.DECELERATE)
        self.init_helper()
        # Запуск планировщика в отдельном потоке
        self.start_scheduler()

    def start_scheduler(self):
        schedule.every(5).seconds.do(self.update_pages)

        def run_schedule():
            while True:
                schedule.run_pending()
                time.sleep(1)

        threading.Thread(target=run_schedule, daemon=True).start()

    def update_pages(self):
        self.refresh_page2()
        self.update_container()

    def delete_alert_and_refresh(self, alert_id):
        self.delete_alert(alert_id)
        self.refresh_page2()

    def delete_alert(self, alert_id):
        delete_alert(alert_id)
        self.page2.content.controls = self.get_list_of_warning_containers()  # Обновление контейнера page2
        self.page2.content.update()  # Обновление содержимого контейнера
        self.pg.update()  # Обновление пользовательского интерфейса

    def refresh_page2(self):
        # Проверяем, есть ли кнопка обновления в контролах, и если нет, добавляем ее
        if not any(isinstance(ctrl, IconButton) and ctrl.icon == icons.UPDATE for ctrl in self.page2.content.controls):
            self.page2.content.controls.insert(0, IconButton(
                icon=icons.UPDATE,
                icon_color="black",
                icon_size=50,
                tooltip="update page",
                on_click=lambda e: self.refresh_page2()
            ))
        # Обновляем содержимое контейнера с предупреждениями
        self.page2.content.controls[1:] = self.get_list_of_warning_containers()
        self.page2.content.update()  # Обновление содержимого контейнера
        self.pg.update()  # Обновление пользовательского интерфейса


    def get_warning_cont(self, warning_data):
        return Container(
            height=200,
            border_radius=border_radius.all(10),
            border=border.all(width=3, color="grey"),
            margin=margin.only(top=10, bottom=10, left=10, right=10),
            alignment=alignment.center,
            content=Row(
                [
                    Text("ID : " + str(warning_data.get("ardID")), size=16),
                    Text(f"Timestamp: {warning_data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}", size=16),
                    Text(warning_data.get("message"), size=16),
                    IconButton(
                        icons.DELETE_FOREVER,
                        on_click=lambda e:self.delete_alert_and_refresh(warning_data.get("_id"))
                    )
                ]
            )
        )


    def get_list_of_warning_containers(self):
        lst = []
        for i in get_all_alerts_from_mongo():
            lst.append(self.get_warning_cont(i))
        return lst


    def init_page2(self):
        # Инициализация page2
        self.page2 = Container(
            alignment=alignment.center,
            offset=transform.Offset(0, 0),
            bgcolor='green',
            content=Column(
                [
                    IconButton(
                        icon=icons.UPDATE,
                        icon_color="black",
                        icon_size=50,
                        tooltip="update page",
                    )
                ] + self.get_list_of_warning_containers(),
                scroll=ScrollMode.ADAPTIVE
            )
        )


    def init_page1(self):
        # Инициализация page1
        self.page1 = Container(
            alignment=alignment.top_left,
            offset=transform.Offset(0, 0),
            bgcolor='blue',
            content=Column(
                [IconButton(
                    icon=icons.UPDATE,
                    icon_color="black",
                    icon_size=50,
                    tooltip="update page",
                    on_click=lambda e: self.update_container()
                )
                ] + self.get_list_of_ard_containers(),
                scroll=ScrollMode.ADAPTIVE
            )
        )

    def update_container(self):
        self.page1.content.controls = [
                                          IconButton(
                                              icon=icons.UPDATE,
                                              icon_color="black",
                                              icon_size=50,
                                              tooltip="update page",
                                              on_click=lambda e: self.update_container()
                                          )
                                      ] + self.get_list_of_ard_containers()
        self.page1.content.update()

    def get_ard_cont(self, sensor_data, timestamp):
        image_pass = f"../assets/plots/plot_{sensor_data['ardID']}_{timestamp}.png"
        return Container(
            height=500,
            border_radius=border_radius.all(10),
            border=border.all(width=3, color="grey"),
            margin=margin.only(top=10, bottom=10, left=10, right=10),
            alignment=alignment.center,
            content=Row(
                [
                    Column(
                        [
                            Text(f"ArdID: {sensor_data['ardID']}", size=16),
                            Text(f"Temperature: {sensor_data['temperature']:.1f}", size=16),
                            Text(f"Humidity: {sensor_data['humidity']:.1f}", size=16),
                            Text(f"PPM: {sensor_data['correctedPPM']:.2f}", size=16),
                            Text(f"Luminosity: {sensor_data['luminosity']}", size=16),
                            Text(f"Timestamp: {sensor_data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}", size=16),
                        ]
                    ),
                    Image(
                        src=image_pass,
                        expand=True
                    ),
                ]
            )
        )

    def get_list_of_ard_containers(self):
        directory_path = "../assets/plots"
        clear_directory(directory_path)

        for rec in get_unique_ard_ids():
            timestamp = str(time.time())
            plot_records(get_records_by_time(rec, "day"), timestamp)
        return [self.get_ard_cont(get_latest_record(i), timestamp) for i in get_unique_ard_ids()]


    def init_helper(self):
        self.side_bar_column = Column(
            spacing=0,
            controls=[
                Row(
                    controls=[
                        Container(
                            data=0,
                            on_click=lambda e: self.switch_page(e, 'page1'),
                            expand=True,
                            height=40,
                            content=Icon(
                                icons.CHAT_BUBBLE,
                                color='blue'
                            ),
                        ),
                    ]
                ),

                Row(
                    controls=[
                        Container(
                            on_click=lambda e: self.switch_page(e, 'page2'),
                            data=1,
                            expand=True,
                            height=40,
                            content=Icon(
                                icons.BADGE,
                                color='blue'
                            ),
                        ),
                    ]
                ),
            ]
        )

        self.indicator = Container(
            height=40,
            bgcolor='red',
            offset=transform.Offset(0, 0),
            animate_offset=animation.Animation(500, AnimationCurve.DECELERATE)
        )

        self.init_page1()
        self.init_page2()


        self.switch_control = {
            'page1': self.page1,
            'page2': self.page2
        }

        self.pg.add(
            Container(
                bgcolor='white',
                expand=True,
                content=Row(
                    spacing=0,
                    controls=[
                        Container(
                            width=80,
                            border=border.only(right=border.BorderSide(width=1, color='#22888888'), ),
                            content=Column(
                                alignment='spaceBetween',
                                controls=[

                                    Container(
                                        height=100,
                                        # bgcolor='blue'
                                    ),

                                    Container(
                                        height=500,
                                        content=Row(
                                            spacing=0,
                                            controls=[
                                                Container(
                                                    expand=True,
                                                    content=self.side_bar_column,

                                                ),
                                                Container(
                                                    width=3,
                                                    content=Column(
                                                        controls=[
                                                            self.indicator,
                                                        ]
                                                    ),

                                                ),
                                            ]
                                        )
                                    ),

                                    Container(
                                        height=50,
                                    ),
                                ]
                            )
                        ),

                        Container(
                            expand=True,
                            content=Stack(
                                controls=[
                                    self.page2,
                                    self.page1,
                                ]
                            )
                        ),
                    ]
                )

            )
        )

    def switch_page(self, e, point):
        print(point)
        for page in self.switch_control:
            self.switch_control[page].offset.x = 2
            self.switch_control[page].update()

        self.switch_control[point].offset.x = 0
        self.switch_control[point].update()

        self.indicator.offset.y = e.control.data
        self.indicator.update()


app(target=App, assets_dir='assets')