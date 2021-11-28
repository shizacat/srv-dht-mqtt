#!/usr/bin/env python3

import os
import time
import random
import logging
import argparse
from dataclasses import dataclass

import paho.mqtt.client as mqtt
import dht


@dataclass
class Topics:
    current: str
    status_active: str
    status_fault: str


class Service:

    def __init__(self, **kwargs):
        self.mqtt_host = kwargs["mqtt_host"]
        self.mqtt_port = kwargs["mqtt_port"]
        self.mqtt_user = kwargs["mqtt_user"]
        self.mqtt_pass = kwargs["mqtt_pass"]
        self.pin = kwargs["dht_pin"]
        self.client_id = f'srv-dht-mqtt-{random.randint(0, 1000):03d}'

        # Config topics
        self.topic_temperature = Topics(
            current="srv-dht/temperature",
            status_active="srv-dht/temperature-status-active",
            status_fault="srv-dht/temperature-status-fault",
        )
        self.topic_humidity = Topics(
            current="srv-dht/humidity",
            status_active="srv-dht/humidity-status-active",
            status_fault="srv-dht/humidity-status-fault",
        )
        self.interval = 1.0  # second
        # If the current value is not received within the interval then error
        self.interval_fault = 60 * 5  # second

        self.dht = dht.DHT22(self.pin)
        self.dht.delay_between_readings = 0.5

        self.client = mqtt.Client(self.client_id)
        if self.mqtt_user:
            self.client.username_pw_set(self.mqtt_user, self.mqtt_pass)
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.connected_flag = False

        self.logger = logging.getLogger(__name__)

    def start(self):
        self.logger.info("Start service")
        self.client.connect(self.mqtt_host, self.mqtt_port, 60)
        self.client.enable_logger()
        self.client.loop_start()
        
        ts_last_good = time.monotonic()
        is_fault = False
        while True:
            try:
                temperature, humidity = self.dht.measure()
                self.client.publish(self.topic_temperature.current, temperature)
                self.client.publish(self.topic_humidity.current, humidity)
                if is_fault:
                    self._update_fault(False)
                    is_fault = False
                ts_last_good = time.monotonic()
                self.logger.info("Temperature/humidity was sent")
            except RuntimeError as e:
                self.logger.info("DHT return error: %s", e)
                if (
                    not is_fault 
                    and (time.monotonic() - ts_last_good) > self.interval_fault
                ):
                    is_fault = True
                    self._update_fault(True)
            time.sleep(self.interval)
    
    def _on_connect(self, client, userdata, flags, rc):
        """The callback for when the client receives a CONNACK response
        from the server.
        Subscribing in on_connect() means that if we lose the connection and
        reconnect then subscriptions will be renewed.
        """
        if rc == 0:
            self.logger.info("Connected to MQTT broker [rc=%s]", rc)
            self.client.connected_flag = True
            self._update_status(True)
            self._update_fault(False)
        else:
            self.logger.error("Failed to connect, return code [rc=%s]", rc)
    
    def on_disconnect(self, client, userdata, rc):
        self._update_status(False)
        self.client.connected_flag = False

    def stop(self):
        if self.client.connected_flag:
            self._update_status(False)
        self.logger.info("Stop service")
    
    def _update_status(self, value: bool):
        self.client.publish(self.topic_temperature.status_active, value)
        self.client.publish(self.topic_humidity.status_active, value)
    
    def _update_fault(self, value: bool):
        self.logger.info("Update fault status: %s", value)
        self.client.publish(self.topic_temperature.status_fault, value)
        self.client.publish(self.topic_humidity.status_fault, value)


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
