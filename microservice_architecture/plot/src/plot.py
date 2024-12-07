import pandas as pd
import matplotlib.pyplot as plt
import time
import os
from datetime import datetime

class PlotGenerator:
    def __init__(self, log_path='/logs/metric_log.csv', plot_path='/logs/error_distribution.png'):
        self.log_path = log_path
        self.plot_path = plot_path
        self.last_modified = None

    def check_and_update_plot(self):
        #Проверяет изменения в файле логов и обновляет график при необходимости
        if not os.path.exists(self.log_path):
            print("Файл логов не найден")
            return False

        current_modified = os.path.getmtime(self.log_path)
        
        # Проверяем, изменился ли файл с логами
        if self.last_modified is None or current_modified > self.last_modified:
            try:
                # Чтение данных
                df = pd.read_csv(self.log_path)
                if len(df) == 0:
                    return False

                # Создание графика
                plt.figure(figsize=(10, 6))
                plt.hist(df['absolute_error'], bins=30, edgecolor='black')
                plt.title('Distribution of Absolute Errors')
                plt.xlabel('Absolute Error')
                plt.ylabel('Frequency')
                
                # Добавление информации о времени обновления
                plt.text(0.95, 0.95, 
                        f'Last update: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
                        transform=plt.gca().transAxes,
                        verticalalignment='top',
                        horizontalalignment='right')

                # Сохранение графика
                plt.savefig(self.plot_path)
                plt.close()

                self.last_modified = current_modified
                print(f"График обновлен: {datetime.now()}")
                return True

            except Exception as e:
                print(f"Ошибка при обновлении графика: {str(e)}")
                return False
        
        return False

def main():
    plot_generator = PlotGenerator()
    
    print("Сервис построения графиков запущен")
    while True:
        plot_generator.check_and_update_plot()
        time.sleep(5)  # Проверка обновлений каждые 5 секунд

if __name__ == '__main__':    main()