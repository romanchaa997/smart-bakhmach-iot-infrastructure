from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
import json
from typing import Callable
import asyncio
from shared.config import settings


class KafkaClient:
    """Kafka client for event-driven communication"""
    
    def __init__(self):
        self.producer = None
        self.consumers = {}
    
    async def start_producer(self):
        """Initialize Kafka producer"""
        self.producer = AIOKafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        await self.producer.start()
    
    async def stop_producer(self):
        """Stop Kafka producer"""
        if self.producer:
            await self.producer.stop()
    
    async def publish(self, topic: str, message: dict):
        """Publish message to Kafka topic"""
        if not self.producer:
            await self.start_producer()
        await self.producer.send_and_wait(topic, message)
    
    async def subscribe(self, topic: str, group_id: str, handler: Callable):
        """Subscribe to Kafka topic and handle messages"""
        consumer = AIOKafkaConsumer(
            topic,
            bootstrap_servers=settings.kafka_bootstrap_servers,
            group_id=group_id,
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )
        await consumer.start()
        self.consumers[topic] = consumer
        
        try:
            async for msg in consumer:
                await handler(msg.value)
        finally:
            await consumer.stop()


kafka_client = KafkaClient()
