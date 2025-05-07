"""
Kafka utilities for publishing supplier events from the Auth Service
"""

import json
import logging
import time
from kafka import KafkaProducer
from django.conf import settings

logger = logging.getLogger(__name__)


class KafkaSupplierProducer:
    """Producer for supplier events"""
    
    def __init__(self):
        """Initialize Kafka producer"""
        self.bootstrap_servers = settings.KAFKA_BOOTSTRAP_SERVERS
        self.supplier_topic = settings.KAFKA_SUPPLIER_EVENTS_TOPIC
        self._producer = None
        
    @property
    def producer(self):
        """Lazy initialization of Kafka producer"""
        if self._producer is None:
            try:
                self._producer = KafkaProducer(
                    bootstrap_servers=self.bootstrap_servers,
                    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                    key_serializer=lambda k: str(k).encode('utf-8') if k else None,
                    acks='all'  # Wait for all replicas to acknowledge
                )
            except Exception as e:
                logger.error(f"Failed to create Kafka producer: {str(e)}")
                self._producer = None
        return self._producer
    
    def publish_event(self, topic, event_type, payload, key=None):
        """Publish an event to a Kafka topic"""
        if self.producer is None:
            logger.error("Kafka producer not initialized")
            return False
            
        message = {
            'event_type': event_type,
            'timestamp': int(time.time() * 1000),
            'payload': payload
        }
        
        try:
            future = self.producer.send(topic, key=key, value=message)
            future.get(timeout=10)  # Wait for the send to complete
            logger.info(f"Published event {event_type} to topic {topic}")
            return True
        except Exception as e:
            logger.error(f"Failed to publish event to Kafka: {str(e)}")
            return False
    
    def publish_supplier_created(self, supplier_id, data):
        """Publish a supplier created event"""
        return self.publish_event(
            self.supplier_topic,
            'supplier_created',
            data,
            key=str(supplier_id)
        )
    
    def publish_supplier_updated(self, supplier_id, data):
        """Publish a supplier updated event"""
        return self.publish_event(
            self.supplier_topic,
            'supplier_updated',
            data,
            key=str(supplier_id)
        )
    
    def publish_supplier_deleted(self, supplier_id):
        """Publish a supplier deleted event"""
        return self.publish_event(
            self.supplier_topic,
            'supplier_deleted',
            {'id': supplier_id},
            key=str(supplier_id)
        )


# Create a singleton instance
supplier_producer = KafkaSupplierProducer()