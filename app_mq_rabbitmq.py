# rabbitmq_async.py
from aio_pika import connect_robust, Message, DeliveryMode
import asyncio
import json

class RabbitMQ():
    def __init__(self, config):
        self.config = config
        self.url = (
            f"amqp://{config['RABBITMQ_USER']}:{config['RABBITMQ_PASSWORD']}"
            f"@{config['RABBITMQ_HOST']}:{config['RABBITMQ_PORT']}{config['RABBITMQ_VHOST']}"
        )
        self.connection = None
        self.channel = None

    async def connect(self):
        self.connection = await connect_robust(self.url)
        self.channel = await self.connection.channel()

    async def close(self):
        if self.channel:
            await self.channel.close()
        if self.connection:
            await self.connection.close()

    async def publish(self, topic, message):
        if not self.channel:
            await self.connect()

        await self.channel.declare_queue(topic, durable=True)
        body = message.encode() if isinstance(message, str) else json.dumps(message).encode()
        await self.channel.default_exchange.publish(
            Message(
                body=body,
                delivery_mode=DeliveryMode.PERSISTENT
            ),
            routing_key=topic
        )

    async def get(self, topic, timeout=5):
        if not self.channel:
            await self.connect()

        queue = await self.channel.declare_queue(topic, durable=True)
        incoming_message = await queue.get(timeout=timeout, fail=False)
        if incoming_message:
            async with incoming_message.process():
                return incoming_message.body.decode()
        return None

    async def process(self, topic, callback):
        if not self.channel:
            await self.connect()

        queue = await self.channel.declare_queue(topic, durable=True)

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    try:
                        await callback(message.body.decode())
                    except Exception as e:
                        print(f"[!] Error processing message: {e}")
