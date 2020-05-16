import os


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Config(object):
    __metaclass__ = Singleton

    def __init__(self):
        self.kafka_endpoint = os.getenv('KAFKA_ENDPOINT', '127.0.0.1:9092')
        self.kafka_topic_trips = os.getenv('KAFKA_TOPIC_TRIPS', 'trips')
        self.kafka_topic_performance = os.getenv('KAFKA_TOPIC_PERFORMANCE', 'performance')
        self.kafka_topic_traffic = os.getenv('KAFKA_TOPIC_TRAFFIC', 'traffic')
        self.kafka_topic_tl_status = os.getenv('KAFKA_TOPIC_TL_STATUS', 'tl-status')
        self.kafka_topic_tl_lights = os.getenv('KAFKA_TOPIC_TL_LIGHTS', 'tl-lights')
        self.kafka_topic_tl_times = os.getenv('KAFKA_TOPIC_TL_TIMES', 'tl-times')

        self.sumo_config_file = os.getenv('SUMO_CONFIG_FILE', './app/map/map.sumo.cfg')
        self.sumo_map_file = os.getenv('SUMO_MAP_FILE', './app/map/map.net.xml')
        self.sumo_total_cars = int(os.getenv('SUMO_TOTAL_CARS', 1000))
        self.sumo_random_seed = int(os.getenv('SUMO_RANDOM_SEED', -1))

        self.multipliers_none = float(os.getenv('MULTIPLIERS_NONE', 0.00))
        self.multipliers_few = float(os.getenv('MULTIPLIERS_FEW', 0.50))
        self.multipliers_many = float(os.getenv('MULTIPLIERS_MANY', 1.30))

