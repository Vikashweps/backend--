import numpy as np
import matplotlib.pyplot as plt
import json

lats = []
lons = []
# Читаем файл построчно
with open('received_data.json', 'r') as file:
    for line in file:
        line = line.strip()
        if line:  # если строка не пустая
            try:
                item = json.loads(line)
                # Проверяем структуру данных
                if 'location' in item:
                    lat = item['location']['latitude']
                    lon = item['location']['longitude']
                elif 'parsed' in item:
                    lat = item['parsed']['latitude']
                    lon = item['parsed']['longitude']
                else:
                    continue

                if lat is not None and lon is not None:
                    # ЗАМЕНЯЕМ ЗАПЯТЫЕ НА ТОЧКИ
                    lat_clean = str(lat).replace(',', '.').strip()
                    lon_clean = str(lon).replace(',', '.').strip()

                    lats.append(float(lat_clean))
                    lons.append(float(lon_clean))

            except (json.JSONDecodeError, ValueError) as e:
                print(f"Ошибка в строке: {line}")
                print(f"Ошибка: {e}")
                continue

plt.figure(figsize=(10, 8))
plt.plot(lons, lats, 'bo-', markersize=4, linewidth=1)
plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.ylim(min(lats) - 0.001, max(lats) + 0.001)
plt.xlim(min(lons) - 0.001, max(lons) + 0.001)
plt.grid(True)
plt.title(f'Траектория движения ({len(lats)} точек)')
plt.tight_layout()
plt.show()