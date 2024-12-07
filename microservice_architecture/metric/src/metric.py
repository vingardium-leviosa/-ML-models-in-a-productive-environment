import pika
import json
import pandas as pd
import os
import time
from collections import defaultdict

class MetricCalculator:
    def __init__(self, log_path='/logs/metric_log.csv'):
        self.log_path = log_path
        self.pending_data = defaultdict(dict)
        
        # Создаем директорию logs, если она не существует
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        
        # Создаем файл с заголовками, если он не существует
        if not os.path.exists(self.log_path):
            with open(self.log_path, 'w') as f:
                f.write('id,y_true,y_pred,absolute_error\n')
            print(f"Создан новый файл логов: {self.log_path}")

    def process_message(self, message, queue_type):
        """Обработка входящего сообщения"""
        try:
            msg_id = message['id']
            value = float(message['body'])  # Преобразуем в float для надежности
            
            print(f"Получено сообщение: type={queue_type}, id={msg_id}, value={value}")
            
            # Сохраняем значение
            self.pending_data[msg_id][queue_type] = value
            
            # Проверяем наличие обоих значений
            if 'y_true' in self.pending_data[msg_id] and 'y_pred' in self.pending_data[msg_id]:
                self.calculate_and_save_metric(msg_id)
                
        except Exception as e:
            print(f"Ошибка при обработке сообщения: {str(e)}")

    def calculate_and_save_metric(self, msg_id):
        """Расчет и сохранение метрики"""
        try:
            data = self.pending_data[msg_id]
            y_true = data['y_true']
            y_pred = data['y_pred']
            
            absolute_error = abs(y_true - y_pred)
            
            # Записываем метрику в файл
            with open(self.log_path, 'a') as f:
                f.write(f"{msg_id},{y_true},{y_pred},{absolute_error}\n")
                f.flush()  # Принудительная запись буфера
                os.fsync(f.fileno())  # Убеждаемся, что данные записаны на диск
            
            print(f"Записана метрика: id={msg_id}, y_true={y_true}, y_pred={y_pred}, error={absolute_error}")
            
            # Удаляем обработанные данные
            del self.pending_data[msg_id]
            
        except Exception as e:
            print(f"Ошибка при сохранении метрики: {str(e)}")

def main():
    calculator = MetricCalculator()
    
    # Ожидание готовности RabbitMQ
    def wait_for_rabbitmq():
        while True:
            try:
                connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
                connection.close()
                print("Успешное подключение к RabbitMQ")
                return
            except Exception as e:
                print(f"RabbitMQ не готов: {str(e)}")
                time.sleep(5)

    wait_for_rabbitmq()

    while True:
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
            channel = connection.channel()

            # Объявление очередей
            channel.queue_declare(queue='y_true')
            channel.queue_declare(queue='y_pred')

            def callback(ch, method, properties, body):
                try:
                    message = json.loads(body)
                    queue_type = 'y_true' if method.routing_key == 'y_true' else 'y_pred'
                    calculator.process_message(message, queue_type)
                except Exception as e:
                    print(f"Ошибка в callback: {str(e)}")

            # Подписка на очереди
            channel.basic_consume(queue='y_true', on_message_callback=callback, auto_ack=True)
            channel.basic_consume(queue='y_pred', on_message_callback=callback, auto_ack=True)

            print('Ожидание сообщений. Для выхода нажмите CTRL+C')
            channel.start_consuming()

        except Exception as e:
            print(f"Ошибка подключения: {str(e)}")
            time.sleep(5)
            continue

if __name__ == '__main__':    main()