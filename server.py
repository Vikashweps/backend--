import zmq
import json
import socket
from datetime import datetime
class ZeroMQServer:
    def __init__(self, host='*', port=5555):
        self.host = host
        self.port = port
        self.counter = 0
        self.received_data = []
        self.filename = 'received_data.json'

        # Инициализация ZMQ
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)

    def is_port_available(self, port):
        """Проверяет доступность порта"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            return result != 0  # 0 means port is in use
        except:
            return False

    def find_available_port(self, start_port=5555, max_attempts=50):
        """Находит свободный порт"""
        for port in range(start_port, start_port + max_attempts):
            if self.is_port_available(port):
                return port
        return None

    def save_to_file(self, data):
        """Сохраняет данные в файл"""
        try:
            try:
                with open(self.filename, 'r') as f:
                    existing_data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                existing_data = []

            existing_data.append(data)

            with open(self.filename, 'w') as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            print(f"Ошибка сохранения в файл: {e}")

    def print_all_data(self):
        """Выводит все сохраненные данные на экран"""
        try:
            with open(self.filename, 'r') as f:
                data = json.load(f)
                print(f"\n === ВСЕ СОХРАНЁННЫЕ ДАННЫЕ ({len(data)} записей) ===")
                for i, item in enumerate(data, 1):
                    print(f"   {i}. [{item['timestamp']}] \"{item['message']}\" (от: {item['source']})")
                print("=" * 60 + "\n")
        except FileNotFoundError:
            print("Файл данных не найден.")
        except Exception as e:
            print(f"Ошибка чтения данных: {e}")

    def run(self):
        try:
            # Проверяем доступность порта
            available_port = self.find_available_port(self.port)
            if available_port is None:
                print("Не найдено свободных портов!")
                return

            if available_port != self.port:
                print(f"  Порт {self.port} занят → использую порт {available_port}")
                self.port = available_port

            # Привязываем сокет
            bind_address = f"tcp://{self.host}:{self.port}"
            self.socket.bind(bind_address)
            print(f"\n СЕРВЕР ЗАПУЩЕН и ожидает подключений")
            print(f" Адрес: {bind_address}")
            print(f"Ожидание первого сообщения от клиента...")
            print(f"(Android-клиент должен подключиться к этому адресу)")
            print(f" Нажмите Ctrl+C для остановки сервера\n")

            # Сохраняем порт в файл для клиента
            with open('server_port.txt', 'w') as f:
                f.write(str(self.port))

            while True:
                try:
                    # Ждем сообщение — это БЛОКИРУЮЩИЙ вызов!
                    print("⏳ Ожидаю сообщение от клиента...")
                    message = self.socket.recv_string()
                    self.counter += 1
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    # Создаем объект данных
                    data = {
                        'timestamp': timestamp,
                        'message': message,
                        'counter': self.counter,
                        'source': 'Android'
                    }

                    # Сообщение получено — выводим красиво
                    print(f"\n [СООБЩЕНИЕ #{self.counter} ПОЛУЧЕНО]")
                    print(f"От: Android-клиент")
                    print(f"Время: {timestamp}")
                    print(f"Текст: \"{message}\"")
                    print(f"Сохраняю в {self.filename}...")

                    # Сохраняем в файл
                    self.save_to_file(data)

                    # Отправляем ответ
                    response = f" Сервер получил сообщение #{self.counter}!"
                    self.socket.send_string(response)

                    print(f" Ответ отправлен: \"{response}\"")
                    print("   " + "-" * 50)

                    # Показываем статистику каждые 5 сообщений
                    if self.counter % 5 == 0:
                        self.print_all_data()

                except zmq.ZMQError as e:
                    print(f"  Ошибка ZeroMQ: {e}")
                    continue
                except Exception as e:
                    print(f" Неожиданная ошибка при обработке сообщения: {e}")
                    continue

        except KeyboardInterrupt:
            print("\n Сервер остановлен пользователем (Ctrl+C)")
        except Exception as e:
            print(f" Критическая ошибка сервера: {e}")
        finally:
            print("🔌 Закрываю сокет и контекст ZeroMQ...")
            self.socket.close()
            self.context.term()
            print(" Сервер полностью остановлен.")


if __name__ == "__main__":
    server = ZeroMQServer(host='*', port=5555)
    server.run()