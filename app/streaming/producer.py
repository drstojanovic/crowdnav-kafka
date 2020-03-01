import json
import sys

from colorama import Fore
from kafka import KafkaProducer

from app import config


class Producer(object):
    producer = None

    @classmethod
    def init(cls):
        print("Initiating producer...")
        try:
            cls.producer = KafkaProducer(bootstrap_servers=config.kafka_host,
                                         value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                                         request_timeout_ms=5000)
        except RuntimeError:
            sys.exit(Fore.RED + "Connection to Kafka failed!" + Fore.RESET)

    @classmethod
    def publish(cls, message, topic):
        try:
            cls.producer.send(topic, message)
        except Exception as e:
            print("Error sending kafka status: " + str(e))
