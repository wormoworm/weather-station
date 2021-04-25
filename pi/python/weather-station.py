import json
import time
from bme280pi import Sensor
from time import sleep
from paho_iot_client import PahoIoTClient, IotClientConfig

SAMPLING_INTERVAL_S = 30

def get_current_time_ms():
    return int(round(time.time() * 1000))

# Initialise the BME280 sensor, using I2C address 0x77
sensor = Sensor(address=0x77)

paho_config = IotClientConfig("/home/pi/paho/paho_config.json")
paho_client = PahoIoTClient(config = paho_config, event_listener = None)

paho_client.connect()

# Sample the sensor once per second in a loop
while True:
    data = {
        "temperature": round(sensor.get_temperature(), 1),
        "pressure": round(sensor.get_pressure(), 3),
        "humidity": round(sensor.get_humidity(), 1)
    }
    message = {
        "timestamp": get_current_time_ms(),
        "data": data
    }
    print("Publishing message: {0}".format(message))
    paho_client.publish(topic = "sensors/freyr", data = json.dumps(message), qos = 1)
    sleep(SAMPLING_INTERVAL_S)