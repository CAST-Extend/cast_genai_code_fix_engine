# app_mq.py
from app_mq_rabbitmq import RabbitMQ
# from app_mq_kafka import KafkaMQ
from app_mq_mongodb import MongoDBMQ  # Using async MongoDB queue (Motor)
from config import Config

class AppMessageQueue:
    def __init__(self, logger, config: Config):
        """
        Initialize the message queue factory
        
        Args:
            logger: Logger instance
            config: Dictionary or config object with MQ_VENDOR
        """
        self.config = config
        self.logger = logger
        self.vendor = config.MQ_VENDOR

    def open(self):
        """
        Return the appropriate message queue instance.
        """
        if self.vendor == 'rabbitmq':
            return RabbitMQ(self.config)
        # elif self.vendor == 'kafka':
        #     return KafkaMQ(self.config)
        elif self.vendor == 'mongodb':
            return MongoDBMQ(self.config)
        else:
            raise NotImplementedError(f"Unsupported MQ vendor: {self.vendor}")
