import socket

# Создаем TCP/IP сокет
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = ('localhost', 2000)

# Подключаемся к серверу - передаем ОДИН аргумент (кортеж)
client_socket.connect(server_address)
print("Подключение к серверу установлено")

# Отправляем данные серверу
client_socket.sendall(b'Hello, server!')
print("Сообщение отправлено серверу")

# Получаем ответ от сервера (если сервер отправляет)
data = client_socket.recv(1024)
print(f"Получено от сервера: {data.decode()}")

# Закрываем соединение
client_socket.close()
print("Соединение закрыто")