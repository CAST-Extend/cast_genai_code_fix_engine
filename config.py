class Config:
    MODEL_NAME = ""
    MODEL_VERSION = ""
    MODEL_URL = ""
    MODEL_API_KEY = ""
    MODEL_MAX_INPUT_TOKENS = 
    MODEL_MAX_OUTPUT_TOKENS = 
    MODEL_INVOCATION_DELAY_IN_SECONDS = 

    IMAGING_URL = ""
    IMAGING_API_KEY = ""

    MONGODB_CONNECTION_STRING = ""
    MONGODB_NAME = ""

    # Use queue mechanism
    MQ_VENDOR = "mongodb"  # or "kafka" or "rabbitmq"

    # RabbitMQ configs (if used)
    RABBITMQ_HOST = "localhost"
    RABBITMQ_PORT = 5672
    RABBITMQ_VHOST = "/"
    RABBITMQ_USER = ""
    RABBITMQ_PASSWORD = ""

    # Kafka configs (if used)
    KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
    KAFKA_GROUP_ID = ""
    KAFKA_AUTO_OFFSET_RESET = ""

    MAX_THREADS = 2
    PORT = 8081
