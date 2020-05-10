import json
import sys

from colorama import Fore
from kafka import KafkaConsumer

from app.config import Config


class Consumer(object):

    consumer = None

    @classmethod
    def init(cls):
        print("Initiating consumer...")
        try:
            cls.consumer = KafkaConsumer(bootstrap_servers=Config().kafka_endpoint,
                                         value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                                         group_id=None,
                                         consumer_timeout_ms=100)
            cls.consumer.subscribe([Config().kafka_topic_tl_status])
        except RuntimeError:
            sys.exit(Fore.RED + "Connection to Kafka failed!" + Fore.RESET)

    @classmethod
    def read_new_tl_status(cls):
        return [msg.value for msg in cls.consumer]
