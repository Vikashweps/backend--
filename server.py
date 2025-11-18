import zmq
import json
import psycopg2
import matplotlib.pyplot as plt
from datetime import datetime
import time

DB_CONFIG = {"host":"localhost","port":5433,"database":"test_psql","user":"postgres","password":"vika"}

# График
plt.ion()
fig, ax = plt.subplots()
ax.set_xlabel('Долгота'), ax.set_ylabel('Широта'), ax.set_title('Траектория движения')

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://*:5557")
socket.setsockopt(zmq.RCVTIMEO, 1000)
print("Сервер запущен")

while True:
    # Обновляем график только если окно существует
    if plt.fignum_exists(fig.number):
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            cursor.execute("SELECT Lat, Lon FROM user_equipment")
            results = cursor.fetchall()
            conn.close()

            lats = [float(lat) for lat, lon in results]
            lons = [float(lon) for lat, lon in results]

            ax.clear()
            ax.plot(lons, lats, 'ro', markersize=3)
            ax.set_xlabel('Долгота')
            ax.set_ylabel('Широта')
            ax.set_title(f'Траектория движения ({len(lats)} точек)')
            ax.grid(True)
            plt.draw()
            plt.pause(0.1)

        except Exception as e:
            print(f"Ошибка графика: {e}")
    else:
        # Окно закрыто - ждем немного
        time.sleep(1)

    # Проверяем данные от клиента
    try:
        message = socket.recv_string()
        data = json.loads(message)
        records = data if isinstance(data, list) else [data]

        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        for record in records:
            lat = float(record['location']['latitude'].replace(',', '.'))
            lon = float(record['location']['longitude'].replace(',', '.'))
            mcc, mnc = record['network']['operator'].split('/')

            cursor.execute("INSERT INTO user_equipment VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", (
                int(datetime.now().timestamp()), lat, lon, 4, int(mcc), int(mnc),
                int(record['network']['tac_lac']), int(record['network']['pci']),
                int(record['network']['ci']), int(record['network']['RSRP'].split()[0]),
                datetime.now()
            ))

        conn.commit()
        conn.close()
        socket.send_string(f"OK: {len(records)}")
        print(f"[{datetime.now()}] OK: {len(records)}")

    except zmq.Again:
        pass
    except Exception as e:
        print(f"Ошибка клиента: {e}")