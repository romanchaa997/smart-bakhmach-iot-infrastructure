import paho.mqtt.client as mqtt
from typing import Callable, Dict
import json
from shared.config import settings


class MQTTClient:
    """MQTT client for IoT device communication"""
    
    def __init__(self):
        self.client = mqtt.Client()
        self.handlers: Dict[str, Callable] = {}
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        
        if settings.mqtt_username and settings.mqtt_password:
            self.client.username_pw_set(settings.mqtt_username, settings.mqtt_password)
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback for when client connects to broker"""
        if rc == 0:
            print(f"Connected to MQTT Broker at {settings.mqtt_broker_host}")
            # Subscribe to all registered topics
            for topic in self.handlers.keys():
                client.subscribe(topic)
        else:
            print(f"Failed to connect to MQTT Broker, return code {rc}")
    
    def _on_message(self, client, userdata, msg):
        """Callback for when a message is received"""
        topic = msg.topic
        try:
            payload = json.loads(msg.payload.decode())
            if topic in self.handlers:
                self.handlers[topic](payload)
        except Exception as e:
            print(f"Error processing MQTT message: {e}")
    
    def connect(self):
        """Connect to MQTT broker"""
        self.client.connect(settings.mqtt_broker_host, settings.mqtt_broker_port, 60)
        self.client.loop_start()
    
    def disconnect(self):
        """Disconnect from MQTT broker"""
        self.client.loop_stop()
        self.client.disconnect()
    
    def publish(self, topic: str, message: dict):
        """Publish message to MQTT topic"""
        payload = json.dumps(message)
        self.client.publish(topic, payload)
    
    def subscribe(self, topic: str, handler: Callable):
        """Subscribe to MQTT topic with handler"""
        self.handlers[topic] = handler
        if self.client.is_connected():
            self.client.subscribe(topic)


mqtt_client = MQTTClient()
