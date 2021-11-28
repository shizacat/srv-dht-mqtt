from distutils.core import setup
from distutils.cmd import Command


setup(
    name="srv-dht-mqtt",
    version="1.0",
    url="https://github.com/shizacat/srv-dht-mqtt",
    author="Matveev Alexey",
    description="Service reads data from sensor DHT22/11 and one sends this to MQTT service",
    scripts=["srv-dht-mqtt.py"],
    install_requires=[
        "paho-mqtt",
        "git+https://github.com/shizacat/dht-pi-python@1.0"
    ],
)
