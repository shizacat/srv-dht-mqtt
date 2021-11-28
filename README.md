# Description

The 'srv-dht-mqtt' sends temperature and humidity to MQTT server
for homebridge-mqttthing plugin.


# Setting

MQTT topics:

Temperature:
- srv-dht/temperature - getCurrentTemperature
- srv-dht/temperature-status-active - getStatusActive
- srv-dht/temperature-status-fault - getStatusFault

Humidity:
- srv-dht/humidity - getCurrentRelativeHumidity
- srv-dht/humidity-status-active - getStatusActive
- srv-dht/humidity-status-fault - getStatusFault
