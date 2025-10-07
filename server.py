import zmq
import json
import re
from datetime import datetime

HOST = "*"  # Слушать на всех интерфейсах
FILENAME = "received_data.json"

context = zmq.Context()
socket = context.socket(zmq.REP)
address = f"tcp://{HOST}:5557"
socket.bind(address)

print(f" Сервер запущен на {address}")
print(" Ожидаю сообщения ...\n")

counter = 0
LAT_PATTERN = r"lat=\s*([+-]?\d*\.\d+|\d+)" #регулярные выражения для извлечения координат из текста
LON_PATTERN = r"lon=\s*([+-]?\d*\.\d+|\d+)"
ALT_PATTERN = r"alt=\s*([+-]?\d*\.\d+|\d+)"

try:
    while True:
        message = socket.recv_string()
        counter += 1
        server_time = datetime.now().strftime("%Y:%m:%d %H:%M:%S")

        print(f"[{counter}] Получено: \"{message}\"")
        print(f"     Время на сервере: {server_time}")
        #  Парсинг координат из текста
        lat_match = re.search(LAT_PATTERN, message)
        lon_match = re.search(LON_PATTERN, message)
        alt_match = re.search(ALT_PATTERN, message)
        parsed_data = {
            "latitude": float(lat_match.group(1)) if lat_match else None,
            "longitude": float(lon_match.group(1)) if lon_match else None,
            "altitude": float(alt_match.group(1)) if alt_match else None
        }

        data = {
            "counter": counter,
            "server_timestamp": server_time,
            "raw_message": message,
            "source": "Android",
            "parsed": parsed_data
        }

        try:
            try:
                with open(FILENAME, "r", encoding="utf-8") as f:
                    records = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                records = []

            records.append(data)

            with open(FILENAME, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=2, ensure_ascii=False)

            print(f"    Сохранено в {FILENAME}")
        except Exception as e:
            print(f"   Ошибка записи: {e}")

        # Отправляем ответ
        response = f"{counter} - данные записаны "
        socket.send_string(response)
        print(f"     Ответ отправлен: \"{response}\"\n")

except Exception as e:
    print(f"\n Ошибка: {e}")
finally:
    socket.close()
    context.term()
    print("Сервер завершён.")