import zmq
import json
from datetime import datetime

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://*:5557")

print("Сервер запущен на tcp://*:5557")
print("Ожидаю данные...")

try:
    while True:
        # Получаем данные
        message = socket.recv_string()
        time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print(f"[{time}] Получено сообщение")

        try:
            # Парсим JSON
            data = json.loads(message)
            records_count = len(data) if isinstance(data, list) else 1

            # Сохраняем в файл
            with open("received_data.json", "a", encoding="utf-8") as f:
                for record in data if isinstance(data, list) else [data]:
                    record["server_time"] = time
                    json.dump(record, f, ensure_ascii=False)
                    f.write("\n")

            print(f"Сохранено {records_count} записей")
            response = f"OK: получено {records_count} записей"

        except json.JSONDecodeError as e:
            print(f"Ошибка JSON: {e}")
            response = f"ERROR: {e}"

        # Отправляем ответ
        socket.send_string(response)
        print(f"Ответ: {response}\n")

except KeyboardInterrupt:
    print("\nСервер остановлен")
finally:
    socket.close()
    context.term()