#!/usr/bin/env python3

import os
import time
import random
import logging
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
        self.interval = 1.0  # second

        self.dht = dht.DHT22(self.pin)
        self.dht.delay_between_readings = 0.5

        self.client = mqtt.Client(self.client_id)
        if self.mqtt_user:
            self.client.username_pw_set(self.mqtt_user, self.mqtt_pass)
        self.client.on_connect = self._on_connect

        self.logger = logging.getLogger(__name__)

    def start(self):
        self.logger.info("Start service")
        self.client.connect(self.mqtt_host, self.mqtt_port, 60)
        self.client.enable_logger()
        self.client.loop_start()
        while True:
            try:
                temperature, humidity = self.dht.measure()
                self.client.publish(self.topic_temperature, temperature)
                self.client.publish(self.topic_humidity, humidity)
                self.logger.info("Temperature/humidity was sent")
            except RuntimeError as e:
                self.logger.info("DHT return error: %s", e)
            time.sleep(self.interval)
    
    def _on_connect(self, client, userdata, flags, rc):
        """The callback for when the client receives a CONNACK response
        from the server.
        Subscribing in on_connect() means that if we lose the connection and
        reconnect then subscriptions will be renewed.
        """
        if rc == 0:
            self.logger.info("Connected to MQTT broker [rc=%s]", rc)
        else:
            self.logger.error("Failed to connect, return code [rc=%s]", rc)

    def stop(self):
        self.logger.info("Stop service")


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
    parser.add_argument(
        "--log-level",
        type=int,
        default=int(os.environ.get("SRV_LOG_LEVEL", 4)),
        choices=[1, 2, 3, 4, 5],
        help=(
            "Logging level, debug(1), info(2), warning(3), "
            "error(4, default), critical(5)"
        )
    )
    return parser.parse_args()


def config_logger(log_level: int):
    # format
    LOG_FORMAT = '%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s] %(message)s'
    logging.basicConfig(format=LOG_FORMAT)

    log_level = logging.getLevelName(log_level * 10)
    logger = logging.getLogger()  # default
    logger_service = logging.getLogger(__name__)
    logger.setLevel(log_level)
    logger_service.setLevel(log_level)


if __name__ == "__main__":
    args = arguments()
    config_logger(args.log_level)
    srv = Service(**vars(args))
    try:
        srv.start()
    except KeyboardInterrupt:
        srv.stop()
