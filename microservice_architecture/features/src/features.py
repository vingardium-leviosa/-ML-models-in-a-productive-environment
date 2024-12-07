import pika
import numpy as np
import json
from sklearn.datasets import load_diabetes
from datetime import datetime
import time

def wait_for_rabbitmq():
    while True:
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
            connection.close()
            print("Successfully connected to RabbitMQ")
            return
        except:
            print("RabbitMQ is not ready. Waiting...")
            time.sleep(5)

# Ждем, пока RabbitMQ будет готов
wait_for_rabbitmq()

while True:
    try:
        X, y = load_diabetes(return_X_y=True)
        random_row = np.random.randint(0, X.shape[0]-1)
        
        message_id = datetime.timestamp(datetime.now())

        connection = pika.BlockingConnection(pika.ConnectionParameters(
            host='rabbitmq',
            connection_attempts=10,
            retry_delay=5
        ))
        channel = connection.channel()

        channel.queue_declare(queue='y_true')
        channel.queue_declare(queue='features')

        message_y_true = {
            'id': message_id,
            'body': float(y[random_row])
        }

        message_features = {
            'id': message_id,
            'body': list(X[random_row])
        }

        channel.basic_publish(exchange='',
                            routing_key='y_true',
                            body=json.dumps(message_y_true))
        print('Сообщение с правильным ответом отправлено в очередь')

        channel.basic_publish(exchange='',
                            routing_key='features',
                            body=json.dumps(message_features))
        print('Сообщение с вектором признаков отправлено в очередь')

        connection.close()
        time.sleep(5)
        
    except Exception as e:
        print(f'Ошибка: {str(e)}')        
        time.sleep(5)  # Ждем перед повторной попыткой