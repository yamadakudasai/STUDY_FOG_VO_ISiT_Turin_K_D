"""
viz_cloud_fog_edge_pipeline_custom.py

Визуализация конвейера для эталонной архитектуры: Край → Туман → Облако
с возможностью настройки всех параметров системы

Показываем / We show:
  • Сквозная задержка "от краевого устройства до облака" для каждой задачи
  • Задержки на каждом уровне вычислений
  • Динамика очередей на Fog-узлах
  • Метрики производительности распределённой системы
"""
import random, statistics
import matplotlib.pyplot as plt
import numpy as np

class DistributedSystemSimulator:
    def __init__(self, n_edge_devices=100, n_fog_nodes=10, n_cloud_servers=3):
        self.n_edge_devices = n_edge_devices
        self.n_fog_nodes = n_fog_nodes
        self.n_cloud_servers = n_cloud_servers

        # Инициализация устройств
        self.edge_devices = self._init_edge_devices()
        self.fog_nodes = self._init_fog_nodes()
        self.cloud_servers = self._init_cloud_servers()

    def _init_edge_devices(self):
        """Инициализация краевых устройств (стационарные и мобильные)"""
        devices = []
        for i in range(self.n_edge_devices):
            device_type = "стационарный" if i % 2 == 0 else "мобильный"
            # Мобильные устройства имеют немного другие характеристики
            if device_type == "мобильный":
                processing_range = (8, 20)  # Немного выше задержка
                network_range = (8, 20)      # Менее стабильное соединение
            else:
                processing_range = (5, 15)  # Стабильная задержка
                network_range = (5, 15)      # Стабильное соединение

            devices.append({
                'id': f"Edge_{i}",
                'type': device_type,
                'processing_delay': random.randint(*processing_range),  # мс
                'network_delay': random.randint(*network_range),        # мс
                'assigned_fog': random.randint(0, self.n_fog_nodes-1)
            })
        return devices

    def _init_fog_nodes(self):
        """Инициализация Fog-узлов"""
        nodes = []
        for i in range(self.n_fog_nodes):
            # Разные Fog-узлы могут иметь разную производительность
            capacity_factor = random.uniform(0.8, 1.2)
            nodes.append({
                'id': f"Fog_{i}",
                'processing_delay_range': (int(30 * capacity_factor), int(80 * capacity_factor)),
                'queue_capacity': 400,
                'current_queue': 0,
                'assigned_cloud': random.randint(0, self.n_cloud_servers-1),
                'processed_tasks': 0
            })
        return nodes

    def _init_cloud_servers(self):
        """Инициализация облачных серверов"""
        servers = []
        for i in range(self.n_cloud_servers):
            # Облачные серверы обычно более производительные
            servers.append({
                'id': f"Cloud_{i}",
                'processing_delay_range': (10, 30),  # мс
                'storage_capacity': 1000,
                'processed_tasks': 0
            })
        return servers

def simulate_ethernet_architecture_custom(n_tasks=100, simulator=None, seed=42):
    """
    Симуляция эталонной архитектуры с кастомным симулятором
    """
    if simulator is None:
        simulator = DistributedSystemSimulator()

    random.seed(seed)
    tasks = []

    for task_id in range(n_tasks):
        # Случайное краевое устройство генерирует задачу
        edge_device = random.choice(simulator.edge_devices)
        fog_node = simulator.fog_nodes[edge_device['assigned_fog']]
        cloud_server = simulator.cloud_servers[fog_node['assigned_cloud']]

        # Задержки на каждом этапе
        edge_processing = edge_device['processing_delay']
        edge_to_fog_network = edge_device['network_delay']

        fog_processing = random.randint(*fog_node['processing_delay_range'])
        fog_queue_delay = fog_node['current_queue'] * 2  # 2 мс на задачу в очереди

        fog_to_cloud_network = random.randint(20, 50)  # Более высокая задержка до облака
        cloud_processing = random.randint(*cloud_server['processing_delay_range'])

        # Обновление очереди Fog-узла
        if fog_node['current_queue'] < fog_node['queue_capacity']:
            fog_node['current_queue'] += 1
        else:
            fog_queue_delay += 10  # Штраф за переполнение очереди

        # Общая сквозная задержка
        end_to_end_latency = (edge_processing + edge_to_fog_network +
                             fog_processing + fog_queue_delay +
                             fog_to_cloud_network + cloud_processing)

        tasks.append({
            'task_id': task_id,
            'edge_device': edge_device['id'],
            'edge_type': edge_device['type'],
            'fog_node': fog_node['id'],
            'cloud_server': cloud_server['id'],
            'edge_processing': edge_processing,
            'edge_to_fog_network': edge_to_fog_network,
            'fog_processing': fog_processing,
            'fog_queue_delay': fog_queue_delay,
            'fog_to_cloud_network': fog_to_cloud_network,
            'cloud_processing': cloud_processing,
            'end_to_end_latency': end_to_end_latency
        })

        # Уменьшение очереди Fog-узла (обработка задач)
        if random.random() < 0.3:  # 30% chance to process a task from queue
            if fog_node['current_queue'] > 0:
                fog_node['current_queue'] -= 1
                fog_node['processed_tasks'] += 1

        # Обновление статистики облачного сервера
        cloud_server['processed_tasks'] += 1

    return tasks

def analyze_performance(tasks):
    """Анализ производительности системы"""
    latencies = [task['end_to_end_latency'] for task in tasks]
    edge_latencies = [task['edge_processing'] for task in tasks]
    fog_latencies = [task['fog_processing'] + task['fog_queue_delay'] for task in tasks]
    cloud_latencies = [task['cloud_processing'] for task in tasks]
    network_latencies = [task['edge_to_fog_network'] + task['fog_to_cloud_network'] for task in tasks]

    # Статистика
    stats = {
        'avg_end_to_end': statistics.mean(latencies),
        'p95_end_to_end': statistics.quantiles(latencies, n=20)[18],
        'p99_end_to_end': statistics.quantiles(latencies, n=100)[98],
        'avg_edge': statistics.mean(edge_latencies),
        'avg_fog': statistics.mean(fog_latencies),
        'avg_cloud': statistics.mean(cloud_latencies),
        'avg_network': statistics.mean(network_latencies),
        'max_latency': max(latencies),
        'min_latency': min(latencies),
        'std_latency': statistics.stdev(latencies) if len(latencies) > 1 else 0
    }

    return stats

def plot_comprehensive_results(tasks, stats, config):
    """Построение комплексных графиков результатов"""

    plt.figure(figsize=(15, 10))

    # График 1: Сквозная задержка по задачам
    plt.subplot(2, 3, 1)
    task_ids = [task['task_id'] for task in tasks]
    latencies = [task['end_to_end_latency'] for task in tasks]
    plt.plot(task_ids, latencies, 'b-', alpha=0.7, linewidth=1)
    plt.axhline(y=stats['avg_end_to_end'], color='r', linestyle='--', label=f'Средняя: {stats["avg_end_to_end"]:.1f}мс')
    plt.xlabel('Номер задачи / Task #')
    plt.ylabel('Сквозная задержка, мс / End-to-End Latency, ms')
    plt.title('Сквозная задержка по задачам\nEnd-to-End Latency per Task')
    plt.grid(True, alpha=0.3)
    plt.legend()

    # График 2: Распределение задержек по уровням
    plt.subplot(2, 3, 2)
    components = ['Край/Edge', 'Туман/Fog', 'Облако/Cloud', 'Сеть/Network']
    avg_latencies = [stats['avg_edge'], stats['avg_fog'], stats['avg_cloud'], stats['avg_network']]
    colors = ['green', 'gray', 'blue', 'orange']
    bars = plt.bar(components, avg_latencies, color=colors, alpha=0.7)
    plt.ylabel('Средняя задержка, мс / Average Latency, ms')
    plt.title('Распределение задержек по уровням\nLatency Distribution by Level')

    # Добавление значений на столбцы
    for bar, value in zip(bars, avg_latencies):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5,
                f'{value:.1f}', ha='center', va='bottom')

    # График 3: Сравнение стационарных и мобильных устройств
    plt.subplot(2, 3, 3)
    stationary_latencies = [task['end_to_end_latency'] for task in tasks if task['edge_type'] == 'стационарный']
    mobile_latencies = [task['end_to_end_latency'] for task in tasks if task['edge_type'] == 'мобильный']

    box_data = [stationary_latencies, mobile_latencies]
    box_labels = ['Стационарные\nStationary', 'Мобильные\nMobile']
    box_plot = plt.boxplot(box_data, labels=box_labels, patch_artist=True)

    # Цвета для boxplot
    colors = ['lightgreen', 'lightblue']
    for patch, color in zip(box_plot['boxes'], colors):
        patch.set_facecolor(color)

    plt.ylabel('Задержка, мс / Latency, ms')
    plt.title('Сравнение типов устройств\nDevice Type Comparison')

    # График 4: Накопительная задержка
    plt.subplot(2, 3, 4)
    cumulative_latency = np.cumsum([task['end_to_end_latency'] for task in tasks])
    plt.plot(task_ids, cumulative_latency, 'purple', linewidth=2)
    plt.xlabel('Номер задачи / Task #')
    plt.ylabel('Накопительная задержка, мс / Cumulative Latency, ms')
    plt.title('Накопительная задержка\nCumulative Latency')
    plt.grid(True, alpha=0.3)

    # График 5: Гистограмма распределения задержек
    plt.subplot(2, 3, 5)
    plt.hist(latencies, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
    plt.axvline(stats['avg_end_to_end'], color='red', linestyle='--', label=f'Средняя: {stats["avg_end_to_end"]:.1f}мс')
    plt.axvline(stats['p95_end_to_end'], color='orange', linestyle='--', label=f'95%: {stats["p95_end_to_end"]:.1f}мс')
    plt.xlabel('Задержка, мс / Latency, ms')
    plt.ylabel('Частота / Frequency')
    plt.title('Распределение задержек\nLatency Distribution')
    plt.legend()

    # График 6: Информация о конфигурации
    plt.subplot(2, 3, 6)
    plt.axis('off')
    config_text = (
        f"КОНФИГУРАЦИЯ СИСТЕМЫ\n"
        f"Краевые устройства: {config['edge_devices']}\n"
        f"Fog-узлы: {config['fog_nodes']}\n"
        f"Облачные серверы: {config['cloud_servers']}\n"
        f"Задачи: {config['tasks']}\n\n"
        f"МЕТРИКИ ПРОИЗВОДИТЕЛЬНОСТИ\n"
        f"Средняя задержка: {stats['avg_end_to_end']:.1f} мс\n"
        f"95-й перцентиль: {stats['p95_end_to_end']:.1f} мс\n"
        f"Стандартное отклонение: {stats['std_latency']:.1f} мс"
    )
    plt.text(0.1, 0.9, config_text, transform=plt.gca().transAxes, fontsize=10,
             verticalalignment='top', bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray"))

    plt.tight_layout()
    plt.show()

def print_detailed_metrics(tasks, stats, config):
    """Вывод детализированных метрик"""
    print("=" * 70)
    print("МЕТРИКИ ЭТАЛОННОЙ АРХИТЕКТУРЫ / REFERENCE ARCHITECTURE METRICS")
    print("=" * 70)

    print(f"\nКОНФИГУРАЦИЯ СИСТЕМЫ / SYSTEM CONFIGURATION:")
    print(f"  Краевые устройства: {config['edge_devices']}")
    print(f"  Fog-узлы: {config['fog_nodes']}")
    print(f"  Облачные серверы: {config['cloud_servers']}")
    print(f"  Всего задач: {config['tasks']}")

    print(f"\nОБЩАЯ ПРОИЗВОДИТЕЛЬНОСТЬ / OVERALL PERFORMANCE:")
    print(f"  Средняя сквозная задержка: {stats['avg_end_to_end']:.2f} мс")
    print(f"  95-й перцентиль задержки: {stats['p95_end_to_end']:.2f} мс")
    print(f"  99-й перцентиль задержки: {stats['p99_end_to_end']:.2f} мс")
    print(f"  Стандартное отклонение: {stats['std_latency']:.2f} мс")
    print(f"  Минимальная задержка: {stats['min_latency']:.2f} мс")
    print(f"  Максимальная задержка: {stats['max_latency']:.2f} мс")

    print(f"\nРАСПРЕДЕЛЕНИЕ ЗАДЕРЖЕК / LATENCY DISTRIBUTION:")
    print(f"  Краевой уровень (Edge): {stats['avg_edge']:.2f} мс ({stats['avg_edge']/stats['avg_end_to_end']*100:.1f}%)")
    print(f"  Туманный уровень (Fog): {stats['avg_fog']:.2f} мс ({stats['avg_fog']/stats['avg_end_to_end']*100:.1f}%)")
    print(f"  Облачный уровень (Cloud): {stats['avg_cloud']:.2f} мс ({stats['avg_cloud']/stats['avg_end_to_end']*100:.1f}%)")
    print(f"  Сетевые задержки: {stats['avg_network']:.2f} мс ({stats['avg_network']/stats['avg_end_to_end']*100:.1f}%)")

    # Анализ по типам устройств
    stationary_tasks = [t for t in tasks if t['edge_type'] == 'стационарный']
    mobile_tasks = [t for t in tasks if t['edge_type'] == 'мобильный']

    if stationary_tasks:
        avg_stationary = statistics.mean([t['end_to_end_latency'] for t in stationary_tasks])
        print(f"\nСТАЦИОНАРНЫЕ УСТРОЙСТВА / STATIONARY DEVICES:")
        print(f"  Количество задач: {len(stationary_tasks)} ({len(stationary_tasks)/len(tasks)*100:.1f}%)")
        print(f"  Средняя задержка: {avg_stationary:.2f} мс")

    if mobile_tasks:
        avg_mobile = statistics.mean([t['end_to_end_latency'] for t in mobile_tasks])
        print(f"\nМОБИЛЬНЫЕ УСТРОЙСТВА / MOBILE DEVICES:")
        print(f"  Количество задач: {len(mobile_tasks)} ({len(mobile_tasks)/len(tasks)*100:.1f}%)")
        print(f"  Средняя задержка: {avg_mobile:.2f} мс")

def simulate_custom_config():
    """Функция для быстрой настройки конфигурации системы"""

    # 🎛️ НАСТРОЙКА ПАРАМЕТРОВ СИСТЕМЫ - МЕНЯЙТЕ ЭТИ ЧИСЛА 🎛️
    CONFIG = {
        'edge_devices': 5000,      # ↦ Количество краевых устройств (100-10000)
        'fog_nodes': 80,          # ↦ Количество Fog-узлов (100-10000)
        'cloud_servers': 25,       # ↦ Количество облачных серверов (1-100)
        'tasks': 200,             # ↦ Количество задач для симуляции
        'seed': 42               # ↦ Seed для воспроизводимости результатов
    }

    print(f"⚙️  Загружена конфигурация:")
    print(f"   Краевые устройства: {CONFIG['edge_devices']}")
    print(f"   Fog-узлы: {CONFIG['fog_nodes']}")
    print(f"   Облачные серверы: {CONFIG['cloud_servers']}")
    print(f"   Задачи: {CONFIG['tasks']}")

    # Проверка корректности конфигурации
    if CONFIG['edge_devices'] < CONFIG['fog_nodes']:
        print("⚠️  Предупреждение: Fog-узлов больше чем краевых устройств")

    if CONFIG['fog_nodes'] < CONFIG['cloud_servers']:
        print("⚠️  Предупреждение: Облачных серверов больше чем Fog-узлов")

    # Инициализация симулятора
    simulator = DistributedSystemSimulator(
        n_edge_devices=CONFIG['edge_devices'],
        n_fog_nodes=CONFIG['fog_nodes'],
        n_cloud_servers=CONFIG['cloud_servers']
    )

    # Запуск симуляции
    tasks = simulate_ethernet_architecture_custom(
        n_tasks=CONFIG['tasks'],
        simulator=simulator,
        seed=CONFIG['seed']
    )

    return tasks, simulator, CONFIG

def main():
    """Основная функция с настраиваемыми параметрами"""

    print("🚀 СИМУЛЯЦИЯ ЭТАЛОННОЙ АРХИТЕКТУРЫ: КРАЙ → ТУМАН → ОБЛАКО")
    print("🚀 REFERENCE ARCHITECTURE SIMULATION: EDGE → FOG → CLOUD")
    print("-" * 70)

    # Запуск симуляции с кастомной конфигурацией
    tasks, simulator, config = simulate_custom_config()

    # Анализ производительности
    stats = analyze_performance(tasks)

    # Вывод результатов
    print_detailed_metrics(tasks, stats, config)

    # Построение графиков
    plot_comprehensive_results(tasks, stats, config)

    print(f"\n✅ СИМУЛЯЦИЯ ЗАВЕРШЕНА УСПЕШНО!")
    print(f"📊 Для изменения конфигурации отредактируйте словарь CONFIG в функции simulate_custom_config()")

if __name__ == '__main__':
    main()