import time
import json
import sys
from abc import ABC, abstractmethod

from json.decoder import JSONDecodeError
from paho.mqtt.client import Client, MQTTMessage, MQTT_LOG_ERR, MQTT_LOG_WARNING, MQTT_LOG_INFO, MQTT_LOG_NOTICE, MQTT_LOG_DEBUG, MQTT_ERR_SUCCESS, MQTT_ERR_QUEUE_SIZE, error_string



TAG = "PahoIoTClient"
TAG_PAHO_CLIENT = "Paho-Internal"

class IotClientConfig:
    """
    Contains config data used by the PahoIoTClient.
    """

    DISCONNECT_TIMEOUT_S_DEFAULT = 10
    OPERATION_TIMEOUT_S_DEFAULT = 5

    KEY_ENDPOINT = "endpoint"
    KEY_PORT = "port"
    KEY_CLIENT_ID = "client_id"
    KEY_CA_PATH = "ca_path"
    KEY_CERTIFICATE_PATH = "certificate_path"
    KEY_PRIVATE_KEY_PATH = "private_key_path"
    KEY_USERNAME = "username"
    KEY_PASSWORD = "password"
    KEY_DISCONNECT_TIMEOUT_S = "disconnect_timeout_s"
    KEY_OPERATION_TIMEOUT_S = "operation_timeout_s"

    endpoint: str
    port: int
    client_id: str
    ca_path: str
    certificate_path: str
    private_key_path: str
    username: str
    password: str
    disconnect_timeout_s: int
    operation_timeout_s: int

    def __init__(self, config_file_path: str):
        config_json = json.load(open(config_file_path, "r"))
        self.endpoint = config_json[self.KEY_ENDPOINT]
        self.port = config_json[self.KEY_PORT]
        self.client_id = config_json[self.KEY_CLIENT_ID]
        self.ca_path = config_json[self.KEY_CA_PATH]
        self.certificate_path = config_json[self.KEY_CERTIFICATE_PATH]
        self.private_key_path = config_json[self.KEY_PRIVATE_KEY_PATH]
        self.username = config_json[self.KEY_USERNAME]
        self.password = config_json[self.KEY_PASSWORD]
        self.disconnect_timeout_s = config_json[self.KEY_DISCONNECT_TIMEOUT_S]
        self.operation_timeout_s = config_json[self.KEY_OPERATION_TIMEOUT_S]


class IoTEventListener(ABC):
    """
    Callback used to notify when IoT connection lifecycle event occur.
    """

    @abstractmethod
    def on_iot_connected(self, iot_client):
        """
        Called when the IoTClient has connected to the broker.
        """

    @abstractmethod
    def on_iot_disconnected(self, iot_client):
        """
        Called when the IoTClient has disconnected from the broker.
        """

    @abstractmethod
    def on_iot_message_published(self, iot_client, message_id, payload_size: int):
        """
        Called when a message has been succesfully published on the broker.
        """

    @abstractmethod
    def on_iot_message_received(self, iot_client, topic, payload):
        """
        Called when a message has been received.
        """

class PahoIoTClient:
    """
    Responsible for connecting to AWS IoT. Handles all connection lifecycle events and attempts to reconnect whenever possible if disconnected. Data is sent to IoT via the method .send_telemetry(TelemetryMessage).
    """

    MQTT_QOS_RETRY_INTERVAL_S = 60
    KEEP_ALIVE_TIMEOUT_S = 2 * 60

    config: IotClientConfig
    mqtt_client: Client()
    event_listener: IoTEventListener
    topic_subscriptions: list

    important_paho_messages = ["Sending PUBLISH (d1", "Connection failed, retrying"]

    def __init__(self, config: IotClientConfig, event_listener: IoTEventListener):
        self.set_config(config = config)
        self.event_listener = event_listener
        self.mqtt_client = Client(config.client_id)
        self.mqtt_client.message_retry_set(self.MQTT_QOS_RETRY_INTERVAL_S)
        # self.mqtt_client.tls_set(ca_certs = config.ca_path, certfile = config.certificate_path, keyfile = config.private_key_path)
        self.mqtt_client.username_pw_set(username = config.username, password = config.password)
        self.mqtt_client.on_connect = self.on_connected
        self.mqtt_client.on_disconnect = self.on_disconnected
        self.mqtt_client.on_publish = self.on_message_published
        self.mqtt_client.on_message = self.on_message_received

    def set_config(self, config: IotClientConfig):
        self.config = config

    def is_connected(self) -> bool:
        return self.mqtt_client.is_connected()
        
    def connect(self):
        self.mqtt_client.connect_async(host = self.config.endpoint, port = self.config.port, keepalive = self.KEEP_ALIVE_TIMEOUT_S)
        self.mqtt_client.loop_start()

    def disconnect(self):
        self.mqtt_client.disconnect()
        self.mqtt_client.loop_stop()

    # async def reconnect(self, delay_in_s: int = 5):
    #     await asyncio.sleep(delay_in_s)
    #     self.disconnect()
    #     await asyncio.sleep(delay_in_s)
    #     self.connect()

    def publish(self, topic: str, data: str, qos: int = 1, reconnect_after_fail: bool = False) -> (int, int):
        message_info = self.mqtt_client.publish(topic = topic, payload = data, qos = qos)
        if message_info.rc is not MQTT_ERR_SUCCESS:
            pass
        else:
            pass
        return (message_info.rc, message_info.mid)
        
    def is_response_code_success(self, response_code: int) -> bool:
        return response_code is MQTT_ERR_SUCCESS
    
    def initialise_subscriptions_list(self):
        self.topic_subscriptions = []

    def subscribe(self, subscriptions: list):
        for subscription in subscriptions:
            if not self.is_topic_subscribed(subscription):
                self.topic_subscriptions.append(subscription)
        
        self.mqtt_client.subscribe(topic = self.topic_subscriptions)
    
    def is_topic_subscribed(self, subscription):
        for existing_subscription in self.topic_subscriptions:
            if subscription[0] == existing_subscription[0]:
                return True
        return False

    def on_connected(self, client, userdata, flags, rc):
        self.initialise_subscriptions_list()        

        if self.event_listener is not None:
            self.event_listener.on_iot_connected(iot_client=self)

    def on_disconnected(self, client, userdata, rc):
        # Clear the list of subscriptions
        if self.event_listener is not None:
            self.event_listener.on_iot_disconnected(iot_client=self)

    def on_message_published(self, client, userdata, mid):
        if self.event_listener is not None:
            self.event_listener.on_iot_message_published(self, message_id = mid, payload_size = self.payload_sizes.pop("{0}".format(mid), None))

    def on_message_received(self, client, userdata, message):
        if self.event_listener is not None:
            self.event_listener.on_iot_message_received(iot_client = self, topic = message.topic, payload = message.payload)
    