import pika
import pickle
import numpy as np
import json
import os

model_path = os.path.join(os.path.dirname(__file__), 'myfile.pkl')
with open(model_path, 'rb') as pkl_file:
    regressor = pickle.load(pkl_file)

try:
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()

    channel.queue_declare(queue='features')
    channel.queue_declare(queue='y_pred')

    def callback(ch, method, properties, body):
        message = json.loads(body)
        features = message['body']
        message_id = message['id']
        
        pred = regressor.predict(np.array(features).reshape(1, -1))
        
        prediction_message = {
            'id': message_id,
            'body': float(pred[0])
        }
        
        channel.basic_publish(exchange='',
                            routing_key='y_pred',
                            body=json.dumps(prediction_message))
        print(f'Предсказание отправлено в очередь y_pred')

    channel.basic_consume(
        queue='features',
        on_message_callback=callback,
        auto_ack=True
    )
    print('Ожидание сообщений')

    channel.start_consuming()
except Exception as e:    
    print(f'Ошибка: {str(e)}')