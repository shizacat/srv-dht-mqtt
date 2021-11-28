#!/usr/bin/env python3

import os
import time
import logging
import random
import argparse

import paho.mqtt.client as mqtt
import dht

class Service:

    def __init__(self, **kwargs):
        self.mqtt_host = kwargs["mqtt_host"]
        self.mqtt_port = kwargs["mqtt_port"]
        self.mqtt_user = kwargs["mqtt_user"]
        self.mqtt_pass = kwargs["mqtt_pass"]
        self.pin = kwargs["dht_pin"]
        self.client_id = f'srv-dht-mqtt-{random.randint(0, 1000):03d}'
        self.topic_temperature = "srv-dht/temperature"
        self.topic_humidity = "srv-dht/humidity"

        self.dht = dht.DHT22(self.pin)
        self.dht.delay_between_readings = 0.5

        self.client = mqtt.Client(self.client_id)
        if self.mqtt_user:
            self.client.username_pw_set(self.mqtt_user, self.mqtt_pass)
        self.client.on_connect = self._on_connect
        # self.client.on_message = self._on_message

        self.logger = logging.getLogger(__name__)

    def start(self):
        self.client.connect(self.mqtt_host, self.mqtt_port, 60)
        # self.client.loop_forever()
        self.client.enable_logger()
        self.client.loop_start()
        while True:
            try:
                temperature, humidity = self.dht.measure()
                self.client.publish(self.topic_temperature, temperature)
                self.client.publish(self.topic_humidity, humidity)
            except RuntimeError as e:
                self.logger.debug("RT Error: %s", e)
            time.sleep(1)
    
    def _on_connect(self, client, userdata, flags, rc):
        """The callback for when the client receives a CONNACK response
        from the server.
        Subscribing in on_connect() means that if we lose the connection and
        reconnect then subscriptions will be renewed.
        """
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)
        self.logger.debug("Connected with result code %s", rc)
        # self.client.subscribe("$SYS/#")
    
    def _on_message(self, client, userdata, msg):
        """The callback for when a PUBLISH message is received from the server.
        """
        self.logger.debug(msg.topic + " " + str(msg.payload))

    def stop(self):
        pass


def arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mqtt-host", type=str, default=os.environ.get("SRV_MQTT_HOST", "")
    )
    parser.add_argument(
        "--mqtt-port",
        type=int,
        default=int(os.environ.get("SRV_MQTT_PORT", 1883))
    )
    parser.add_argument(
        "--mqtt-user", type=str, default=os.environ.get("SRV_MQTT_USER", "")
    )
    parser.add_argument(
        "--mqtt-pass", type=str, default=os.environ.get("SRV_MQTT_PASS", "")
    )
    parser.add_argument(
        "--dht-pin",
        type=int,
        default=int(os.environ.get("SRV_MQTT_DHT_PIN", 0))
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = arguments()
    srv = Service(**vars(args))
    try:
        srv.start()
    except KeyboardInterrupt:
        srv.stop()
