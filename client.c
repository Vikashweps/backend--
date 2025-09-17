#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>

#define PORT 2000

int main()
{
    int sock;
    struct sockaddr_in server;
    char message[] = "Hello from C client!";
    
    // Создаем сокет
    sock = socket(AF_INET, SOCK_STREAM, 0);
    if(sock == -1) {
        printf("Ошибка создания сокета\n");
        return 1;
    }
    
    // Настраиваем адрес сервера - используем localhost
    server.sin_addr.s_addr = inet_addr("127.0.0.1"); // localhost
    server.sin_family = AF_INET;
    server.sin_port = htons(PORT);
    
    // Подключаемся к серверу
    if(connect(sock, (struct sockaddr*)&server, sizeof(server)) < 0) {
        perror("Ошибка подключения");
        printf("Убедитесь, что сервер запущен: python3 server.py\n");
        close(sock);
        return 1;
    }
    
    printf("Подключено к серверу\n");
    
    // Отправляем сообщение
    if(send(sock, message, strlen(message), 0) < 0) {
        printf("Ошибка отправки\n");
        close(sock);
        return 1;
    }
    
    printf("Сообщение отправлено: %s\n", message);
    
    // Закрываем соединение
    close(sock);
    printf("Соединение закрыто\n");
    
    return 0;
}