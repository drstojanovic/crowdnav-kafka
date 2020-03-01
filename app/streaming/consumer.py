import json
import sys

from colorama import Fore
from kafka import KafkaConsumer

from app import config


class Consumer(object):

    consumer = None

    @classmethod
    def init(cls):
        print("Initiating consumer...")
        try:
            cls.consumer = KafkaConsumer(bootstrap_servers=config.kafka_host,
                                         value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                                         group_id=None,
                                         consumer_timeout_ms=100)
            cls.consumer.subscribe([config.kafka_tl_actions_topic])
        except RuntimeError:
            sys.exit(Fore.RED + "Connection to Kafka failed!" + Fore.RESET)

    @classmethod
    def read_new_tls_actions(cls):
        return [msg.value for msg in cls.consumer]
