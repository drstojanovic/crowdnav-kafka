import json
import sys

from colorama import Fore
from kafka import KafkaConsumer

from app import Config

updater = None


# Try to connect to Kafka, else exits the process
def connect():
    if Config.kafkaUpdates:
        try:
            global updater
            updater = KafkaConsumer(bootstrap_servers=Config.kafkaHost,
                                    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                                    group_id=None,
                                    consumer_timeout_ms=100)
            updater.subscribe([Config.kafkaTlActionsTopic])
            print(Fore.GREEN + '# KafkaConnector OK!' + Fore.RESET)
        except RuntimeError:
            sys.exit(Fore.RED + "Connection to Kafka failed!" + Fore.RESET)


def read_new_tls_actions():
    return [msg.value for msg in updater]
