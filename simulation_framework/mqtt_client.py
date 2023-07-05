from simulation_framework.core.components import *

import paho.mqtt.client as mqtt


def encode_MQTT_message(topic: str, payload: Union[str, dict], timestamp: float = None) -> mqtt.MQTTMessage:
    msg = mqtt.MQTTMessage()
    msg.topic = bytes(topic, encoding='utf-8')
    if isinstance(payload, str):
        msg.payload = bytes(payload, encoding='utf-8')
    elif isinstance(payload, dict):
        msg.payload = dict_to_json_string(payload)
    msg.timestamp = timestamp

    return msg


def decode_MQTT_message(msg: mqtt.MQTTMessage, mode=dict) -> Tuple[str, dict]:
    topic = msg.topic
    payload = msg.payload
    timestamp: float = msg.timestamp

    if isinstance(topic, bytes):
        topic = topic.decode()
    if isinstance(payload, bytes):
        payload = payload.decode()

    if isinstance(payload, str):
        if mode == str:
            return topic, payload, timestamp
        elif mode == dict:
            return topic, json_string_to_dict(payload), timestamp
        else:
            raise UnsupportedError(f'Unexpected mode!!! - {mode}')
    elif isinstance(payload, dict):
        if mode == str:
            return topic, dict_to_json_string(payload), timestamp
        elif mode == dict:
            return topic, payload, timestamp
        else:
            raise UnsupportedError(f'Unexpected mode!!! - {mode}')
    else:
        raise UnsupportedError(f'Unexpected type!!! - {type(payload)}')


class MXMQTTClient:
    def __init__(self, middleware: MXMiddleware, debug: bool = False):
        self._mqtt_client: mqtt.Client = mqtt.Client(client_id=middleware.name, clean_session=True)

        self.middleware = middleware
        self.host = middleware.device.host
        self.port = middleware.mqtt_port

        self._pub_message = None
        self._recv_message = None
        self._pub_message_queue: Queue = Queue()
        self._recv_message_queue: Queue = Queue()

        self._subscribe_list = set()
        self._debug = debug

        self.is_run = False

        self.set_callback()

    def connect(self):
        try:
            self._mqtt_client.connect(self.middleware.device.host, self.middleware.mqtt_port)
        except Exception as e:
            MXLOG_DEBUG(f'Connect to broker failed...', 'red')
            return False

    def set_debug(self, debug: bool):
        self._debug = debug

    def get_client_id(self):
        return self._mqtt_client._client_id.decode()

    def set_callback(self):
        self._mqtt_client.on_connect = self._on_connect
        self._mqtt_client.on_disconnect = self._on_disconnect
        self._mqtt_client.on_publish = self._on_publish
        self._mqtt_client.on_subscribe = self._on_subscribe
        self._mqtt_client.on_unsubscribe = self._on_unsubscribe
        self._mqtt_client.on_message = self._on_message

    def publish(self, topic, payload, qos=0, retain=False):
        self._pub_message = encode_MQTT_message(
            topic, payload, get_current_time())
        ret = self._mqtt_client.publish(topic, payload, qos, retain)
        if self._debug:
            if ret.rc == 0:
                pass
                MXLOG_DEBUG(
                    f'{f"✅ Published by {self.get_client_id()}":>16}(qos={qos}): {topic:<80}, {payload} '
                    f'on {self.middleware.device.name} - {self.middleware.device.host}:{self.middleware.mqtt_port}', 'yellow')
            else:
                pass
                MXLOG_DEBUG(f'Publish failed...', 'red')

    def subscribe(self, topic: Union[List, str], qos=0):
        if type(topic) is not list:
            self._mqtt_client.subscribe(topic, qos)
            self._subscribe_list.add(topic)
            if self._debug:
                MXLOG_DEBUG(
                    f'{f"✅ Subscribed by {self.get_client_id()}":>16}(qos={qos}): {topic:<80}, '
                    f'on {self.middleware.device.name} - {self.middleware.device.host}:{self.middleware.mqtt_port}', 'yellow')
        else:
            for item in topic:
                self._mqtt_client.subscribe(item, qos)
                self._subscribe_list.add(item)
                if self._debug:
                    MXLOG_DEBUG(
                        f'{f"✅ Subscribed by {self.get_client_id()}":>16}(qos={qos}): {item:<80}, '
                        f'on {self.middleware.device.name} - {self.middleware.device.host}:{self.middleware.mqtt_port}', 'yellow')

    def unsubscribe(self, topic, properties=None):
        if type(topic) is not list:
            self._mqtt_client.unsubscribe(topic, properties)
            if topic in self._subscribe_list:
                self._subscribe_list.remove(topic)
            if self._debug:
                MXLOG_DEBUG(
                    f'{f"❌ Unsubscribed by {self.get_client_id()}":>16}: {topic:<80}, '
                    f'on {self.middleware.device.name} - {self.middleware.device.host}:{self.middleware.mqtt_port}', 'yellow')
        else:
            for item in topic:
                self._mqtt_client.unsubscribe(item, properties)
                if item in self._subscribe_list:
                    self._subscribe_list.remove(item)
                if self._debug:
                    MXLOG_DEBUG(
                        f'{f"❌ Unsubscribed by {self.get_client_id()}":>16}: {item:<80}, '
                        f'on {self.middleware.device.name} - {self.middleware.device.host}:{self.middleware.mqtt_port}', 'yellow')

    def run(self):
        if self.is_run:
            return self
        else:
            self.connect()
            self.loop_start()
            self.is_run = True
            # self.subscribe_predefine_topics()
            return self

    def stop(self):
        self.loop_stop()

    def loop_start(self):
        self._mqtt_client.loop_start()

    def loop_stop(self):
        self._mqtt_client.loop_stop()

    ####################################################################################################

    def _on_connect(self, client: mqtt.Client, userdata, flags, rc):
        pass

    def _on_disconnect(self, client, userdata, rc):
        pass

    def _on_log(self, client, userdata, level, buf):
        pass

    def _on_subscribe(self, client, userdata, mid, granted_qos):
        pass

    def _on_unsubscribe(self, client, userdata, mid):
        pass

    def _on_publish(self, client, userdata, mid):
        pass

    def _on_message(self, client: mqtt.Client, userdata, message: mqtt.MQTTMessage):
        # self.recv_message = message
        self._recv_message_queue.put(message)
        topic, payload, _ = decode_MQTT_message(message)

        if self._debug:
            MXLOG_DEBUG(
                f'{f"✅ Received by {self.get_client_id()}":>16}(qos={message.qos}): {topic:<80}, {payload} '
                f'on {self.middleware.device.name} - {self.middleware.device.host}:{self.middleware.mqtt_port}', 'yellow')
