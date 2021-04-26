import json
import time
import board
import digitalio
import adafruit_bme280
from time import sleep
from paho_iot_client import PahoIoTClient, IotClientConfig

SAMPLING_INTERVAL_S = 30

def get_current_time_s():
    return int(round(time.time()))

# NOTE: Pin numbers correspond to the GPIO_xx numbers on pinout.xyz

# Create sensor object, using the board's default SPI bus.
spi = board.SPI()
bme_cs = digitalio.DigitalInOut(board.D5)
bme280 = adafruit_bme280.Adafruit_BME280_SPI(spi, bme_cs)

paho_config = IotClientConfig("/home/pi/paho/paho_config.json")
paho_client = PahoIoTClient(config = paho_config, event_listener = None)

paho_client.connect()

# Sample the sensor once per second in a loop
while True:
    data = {
        "temperature": round(bme280.temperature, 1),
        "pressure": round(bme280.pressure, 3),
        "humidity": round(bme280.relative_humidity, 1)
    }
    message = {
        "timestamp": get_current_time_s(),
        "data": data
    }
    print("Publishing message: {0}".format(message))
    paho_client.publish(topic = "sensors/freyr", data = json.dumps(message), qos = 1)
    sleep(SAMPLING_INTERVAL_S)