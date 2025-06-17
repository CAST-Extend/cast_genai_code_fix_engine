class Config:
    MODEL_NAME = "gpt-4o-mini"
    MODEL_VERSION = ""
    MODEL_URL = ""
    MODEL_API_KEY = ""
    MODEL_MAX_INPUT_TOKENS = 128000
    MODEL_MAX_OUTPUT_TOKENS = 16384
    MODEL_INVOCATION_DELAY_IN_SECONDS = 10

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
    KAFKA_GROUP_ID = "cast_ai_group"
    KAFKA_AUTO_OFFSET_RESET = "earliest"

    MAX_THREADS = 2
    PORT = 8081
