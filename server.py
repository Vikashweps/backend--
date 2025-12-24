import zmq
import json
import psycopg2
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "database": "test_psql",
    "user": "postgres",
    "password": "vika"
}

# Создаём фигуру
fig, ax = plt.subplots(figsize=(10, 8))
ax.set(xlabel='Долгота', ylabel='Широта', title='Траектория движения с уровнем сигнала')
ax.grid(True, alpha=0.3)
scatter = None
colorbar = None

# Загружаем начальные данные
lats, lons, rsrps = [], [], []
last_count = 0

try:
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("SELECT Lat, Lon, RSRP FROM user_equipment")
    results = cursor.fetchall()
    conn.close()

    if results:
        lats = [float(r[0]) for r in results]
        lons = [float(r[1]) for r in results]
        rsrps = [int(r[2]) if r[2] is not None else -100 for r in results]
        last_count = len(lats)
        print(f"Загружено {last_count} точек из БД")
    else:
        print("Нет данных в базе")

except Exception as e:
    print(f"Ошибка загрузки данных: {e}")

# Функция обновления графика
def update_plot():
    global scatter, colorbar, lats, lons, rsrps

    # Очищаем ось
    ax.clear()
    ax.set(xlabel='Долгота', ylabel='Широта', title=f'Траектория: {len(lats)} точек')
    ax.grid(True, alpha=0.3)

    if not lats:
        return

    rsrp_np = np.array(rsrps)
    lons_np = np.array(lons)
    lats_np = np.array(lats)
    valid_mask = (rsrp_np > -140) & (rsrp_np < 0)
    valid_rsrp = rsrp_np[valid_mask]
    valid_lons = lons_np[valid_mask]
    valid_lats = lats_np[valid_mask]

    if len(valid_rsrp) > 0:
        rsrp_min = valid_rsrp.min()
        rsrp_max = valid_rsrp.max()

        if rsrp_max == rsrp_min:
            colors = np.full_like(valid_rsrp, 0.5)
        else:
            colors = (valid_rsrp - rsrp_min) / (rsrp_max - rsrp_min)

        scatter = ax.scatter(valid_lons, valid_lats, c=colors, cmap='RdYlGn', s=30, alpha=0.7)

        # Удаляем старую цветовую шкалу
        if colorbar:
            colorbar.remove()

        # Добавляем новую
        colorbar = plt.colorbar(scatter, ax=ax)
        colorbar.set_label('RSRP (дБм)')
        colorbar.set_ticks([0, 1])
        colorbar.set_ticklabels([f'{rsrp_min:.0f} (слабый)', f'{rsrp_max:.0f} (сильный)'])

    # Точки без RSRP — серые
    invalid_mask = ~valid_mask
    if np.any(invalid_mask):
        ax.scatter(lons_np[invalid_mask], lats_np[invalid_mask], c='gray', s=20, alpha=0.5)

    fig.canvas.draw_idle()
    fig.canvas.flush_events()

# Первичное отображение
update_plot()
plt.show(block=False)

# Запуск ZeroMQ сервера
context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://*:5557")
socket.setsockopt(zmq.RCVTIMEO, 100)
print("Сервер запущен на tcp://*:5557")

try:
    while plt.fignum_exists(fig.number):
        try:
            message = socket.recv_string()
            data = json.loads(message)
            records = data if isinstance(data, list) else [data]

            new_points = 0
            for record in records:
                try:
                    # Извлекаем данные
                    lat = float(record['location']['latitude'].replace(',', '.'))
                    lon = float(record['location']['longitude'].replace(',', '.'))
                    mcc, mnc = record['network']['operator'].split('/')
                    rsrp_str = record['network']['RSRP']
                    rsrp_value = int(rsrp_str.split()[0]) if rsrp_str != "-" else -100

                    # Сохраняем в БД
                    conn = psycopg2.connect(**DB_CONFIG)
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO user_equipment 
                        (Time, Lat, Lon, Network_Type, MCC, MNC, Lac, PCI, CI, RSRP, server_time)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        datetime.now(), lat, lon, 4,
                        int(mcc) if mcc != "-" else 0,
                        int(mnc) if mnc != "-" else 0,
                        int(record['network']['tac_lac']) if record['network']['tac_lac'] != "-" else 0,
                        int(record['network']['pci']) if record['network']['pci'] != "-" else 0,
                        int(record['network']['ci']) if record['network']['ci'] != "-" else 0,
                        rsrp_value,
                        datetime.now()
                    ))
                    conn.commit()
                    conn.close()
                    new_points += 1

                except Exception as e:
                    print(f"Ошибка записи точки: {e}")
                    try:
                        conn.close()
                    except:
                        pass

            if new_points > 0:
                conn = psycopg2.connect(**DB_CONFIG)
                cursor = conn.cursor()
                cursor.execute("SELECT Lat, Lon, RSRP FROM user_equipment")
                results = cursor.fetchall()
                conn.close()

                lats = [float(r[0]) for r in results]
                lons = [float(r[1]) for r in results]
                rsrps = [int(r[2]) if r[2] is not None else -100 for r in results]

                update_plot()

                # Статистика
                valid_rsrps = [r for r in rsrps if -140 < r < 0]
                if valid_rsrps:
                    avg = np.mean(valid_rsrps)
                    print(f"[{datetime.now()}] +{new_points} записей. RSRP: {min(valid_rsrps)}..{max(valid_rsrps)} (ср. {avg:.1f})")

            socket.send_string(f"OK: {len(records)} записей получено")
            print(f"[{datetime.now()}] Принято: {len(records)} записей")

        except zmq.Again:
            plt.pause(0.01)
        except json.JSONDecodeError:
            socket.send_string("Ошибка: неверный JSON")
        except Exception as e:
            print(f"Ошибка обработки: {e}")
            socket.send_string(f"Ошибка: {str(e)}")

finally:
    print("Сервер остановлен")
    socket.close()
    context.term()