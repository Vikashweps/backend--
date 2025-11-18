import json
import psycopg2

# Подключение к БД
conn = psycopg2.connect(
    host="localhost",
    port=5433,
    database="test_psql",
    user="postgres",
    password="vika"
)
cursor = conn.cursor()

# Чтение JSON файла
with open("received_data.json", "r", encoding="utf-8") as file:
    for line in file:
        data = json.loads(line.strip())

        # Просто вставляем данные
        cursor.execute("""
            INSERT INTO user_equipment 
            (Time, Lat, Lon, Network_Type, MCC, MNC, Lac, PCI, CI, RSRP, server_time)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            1234567890,  # Просто число вместо timestamp
            float(data['location']['latitude'].replace(',', '.')),
            float(data['location']['longitude'].replace(',', '.')),
            4,
            int(data['network']['operator'].split('/')[0]),
            int(data['network']['operator'].split('/')[1]),
            int(data['network']['tac_lac']),
            int(data['network']['pci']),
            int(data['network'].get('ci') or data['network'].get('cid')),
            int(data['network']['RSRP'].split()[0]),
            data['server_time']
        ))

# Сохраняем все изменения
conn.commit()
print(" Данные добавлены в БД")