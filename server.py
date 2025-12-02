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

# Создаем график
fig, ax = plt.subplots(figsize=(10, 8))
ax.set(xlabel='Долгота', ylabel='Широта', title='Траектория движения с уровнем сигнала')
scatter_plot = None

# Загружаем начальные данные
try:
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("SELECT Lat, Lon, RSRP FROM user_equipment")
    results = cursor.fetchall()
    conn.close()

    if results:
        lats = [float(lat) for lat, lon, rsrp in results]
        lons = [float(lon) for lat, lon, rsrp in results]
        rsrps = [int(rsrp) if rsrp is not None else -100 for lat, lon, rsrp in results]

        # Нормализация: лучший -70, худший -125
        if rsrps:
            rsrp_np = np.array(rsrps)
            # RSRP от -125 (плохо) до -70 (отлично)
            rsrp_norm = (rsrp_np - (-125)) / (-70 - (-125))
            rsrp_norm = np.clip(rsrp_norm, 0, 1)

            # Рисуем точки цветом по уровню сигнала
            scatter_plot = ax.scatter(lons, lats, c=rsrp_norm,
                                      cmap='RdYlGn', s=30, alpha=0.7)
        else:
            # Если нет данных RSRP, рисуем красные точки
            ax.scatter(lons, lats, c='red', s=30, alpha=0.7)

        ax.grid(True, alpha=0.3)

        # Добавляем цветовую шкалу если есть данные RSRP
        if rsrps and scatter_plot:
            cbar = plt.colorbar(scatter_plot, ax=ax)
            cbar.set_label('RSRP (дБм)')
            cbar.set_ticks([0, 0.5, 1])
            cbar.set_ticklabels(['-125 (плохо)', '-97.5', '-70 (отлично)'])

        print(f"График создан: {len(lats)} точек")
        last_count = len(lats)

    else:
        print("Нет данных в базе")
        last_count = 0
        lats, lons, rsrps = [], [], []

except Exception as e:
    print(f"Ошибка начального графика: {e}")
    last_count = 0
    lats, lons, rsrps = [], [], []

plt.tight_layout()
plt.show(block=False)

# Запускаем сервер
context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://*:5557")
socket.setsockopt(zmq.RCVTIMEO, 1000)
print("Сервер запущен")

while True:
    if not plt.fignum_exists(fig.number):
        print("График закрыт")
        break

    try:
        message = socket.recv_string()
        data = json.loads(message)
        records = data if isinstance(data, list) else [data]

        new_points = 0
        for record in records:
            try:
                conn = psycopg2.connect(**DB_CONFIG)
                cursor = conn.cursor()

                lat = float(record['location']['latitude'].replace(',', '.'))
                lon = float(record['location']['longitude'].replace(',', '.'))
                mcc, mnc = record['network']['operator'].split('/')
                rsrp_value = int(record['network']['RSRP'].split()[0])

                cursor.execute("""
                    INSERT INTO user_equipment 
                    (Time, Lat, Lon, Network_Type, MCC, MNC, Lac, PCI, CI, RSRP, server_time)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    datetime.now(), lat, lon, 4, int(mcc), int(mnc),
                    int(record['network']['tac_lac']), int(record['network']['pci']),
                    int(record['network']['ci']), rsrp_value,
                    datetime.now()
                ))
                conn.commit()
                conn.close()
                new_points += 1

            except Exception as e:
                print(f"Ошибка записи: {e}")
                try:
                    conn.close()
                except:
                    pass

        # Обновляем график если есть новые данные
        if new_points > 0:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            cursor.execute("SELECT Lat, Lon, RSRP FROM user_equipment")
            results = cursor.fetchall()
            conn.close()

            if results:
                lats = [float(lat) for lat, lon, rsrp in results]
                lons = [float(lon) for lat, lon, rsrp in results]
                rsrps = [int(rsrp) if rsrp is not None else -100 for lat, lon, rsrp in results]

                if len(lats) > last_count:
                    # Очищаем график
                    ax.clear()

                    # Нормализация: лучший -70, худший -125
                    if rsrps:
                        rsrp_np = np.array(rsrps)
                        rsrp_norm = (rsrp_np - (-125)) / (-70 - (-125))
                        rsrp_norm = np.clip(rsrp_norm, 0, 1)

                        scatter_plot = ax.scatter(lons, lats, c=rsrp_norm,
                                                  cmap='RdYlGn', s=30, alpha=0.7)
                    else:
                        ax.scatter(lons, lats, c='red', s=30, alpha=0.7)

                    ax.set(xlabel='Долгота', ylabel='Широта',
                           title=f'Траектория: {len(lats)} точек')
                    ax.grid(True, alpha=0.3)

                    # Добавляем цветовую шкалу
                    if rsrps and scatter_plot:
                        cbar = plt.colorbar(scatter_plot, ax=ax)
                        cbar.set_label('RSRP (дБм)')
                        cbar.set_ticks([0, 0.5, 1])
                        cbar.set_ticklabels(['-125 (плохо)', '-97.5', '-70 (отлично)'])

                    fig.canvas.draw_idle()
                    fig.canvas.flush_events()
                    last_count = len(lats)

                    # Статистика RSRP
                    if rsrps:
                        valid_rsrps = [r for r in rsrps if r > -140]
                        if valid_rsrps:
                            avg_rsrp = np.mean(valid_rsrps)
                            min_rsrp = np.min(valid_rsrps)
                            max_rsrp = np.max(valid_rsrps)
                            print(f"График обновлен: {len(lats)} точек")
                            print(f"  RSRP: средний={avg_rsrp:.1f}, мин={min_rsrp}, макс={max_rsrp} дБм")

                            # Категории сигнала (по новому диапазону)
                            excellent = sum(1 for r in valid_rsrps if r >= -70)
                            good = sum(1 for r in valid_rsrps if -85 <= r < -70)
                            moderate = sum(1 for r in valid_rsrps if -100 <= r < -85)
                            poor = sum(1 for r in valid_rsrps if r < -100)
                            print(f"  Отлично (≥-70): {excellent}")
                            print(f"  Хорошо (-85...-70): {good}")
                            print(f"  Средне (-100...-85): {moderate}")
                            print(f"  Плохо (<-100): {poor}")
                        else:
                            print(f"График обновлен: {len(lats)} точек")

        socket.send_string(f"OK: {len(records)}")
        print(f"[{datetime.now()}] Принято: {len(records)} записей")

    except zmq.Again:
        plt.pause(0.01)
    except Exception as e:
        print(f"Ошибка: {e}")

print("Сервер остановлен")
socket.close()