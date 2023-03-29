from simulation_framework.core.elements import *

import paho.mqtt.client as mqtt
from queue import Queue, Empty


class SoPMQTTClient:
    def __init__(self, middleware: SoPMiddlewareElement, debug: bool = False):
        self.client: mqtt.Client = mqtt.Client(
            client_id=middleware.name, clean_session=True)

        self.middleware = middleware
        self.host = middleware.device.host
        self.port = middleware.mqtt_port

        self.pub_message = None
        self.recv_message = None
        self.pub_message_queue: Queue = Queue()
        self.recv_message_queue: Queue = Queue()

        self.subscribe_list = set()
        self.is_run = False
        self.debug = debug

        self.set_callback()

    def connect(self):
        try:
            self.client.connect(self.middleware.device.host,
                                self.middleware.mqtt_port)
        except Exception as e:
            SOPLOG_DEBUG(f'Connect to broker failed...', 'red')
            return False

    def set_debug(self, debug: bool):
        self.debug = debug

    def get_client_id(self):
        return self.client._client_id.decode()

    def set_callback(self):
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_publish = self._on_publish
        self.client.on_subscribe = self._on_subscribe
        self.client.on_unsubscribe = self._on_unsubscribe
        self.client.on_message = self._on_message

    def publish(self, topic, payload, qos=0, retain=False):
        self.pub_message = encode_MQTT_message(
            topic, payload, get_current_time())
        ret = self.client.publish(topic, payload, qos, retain)
        if self.debug:
            if ret.rc == 0:
                pass
                SOPLOG_DEBUG(
                    f'{f"✅ Published by {self.get_client_id()}":>16}(qos={qos}): {topic:<80}, {payload} on {self.middleware.device.host}:{self.middleware.mqtt_port}', 'yellow')
            else:
                pass
                SOPLOG_DEBUG(f'Publish failed...', 'red')

    def subscribe(self, topic: Union[List, str], qos=0):
        if type(topic) is not list:
            self.client.subscribe(topic, qos)
            self.subscribe_list.add(topic)
            if self.debug:
                SOPLOG_DEBUG(
                    f'{f"✅ Subscribed by {self.get_client_id()}":>16}(qos={qos}): {topic:<80}, on {self.middleware.device.host}:{self.middleware.mqtt_port}', 'yellow')
        else:
            for item in topic:
                self.client.subscribe(item, qos)
                self.subscribe_list.add(item)
                if self.debug:
                    SOPLOG_DEBUG(
                        f'{f"✅ Subscribed by {self.get_client_id()}":>16}(qos={qos}): {item:<80}, on {self.middleware.device.host}:{self.middleware.mqtt_port}', 'yellow')

    def unsubscribe(self, topic, properties=None):
        if type(topic) is not list:
            self.client.unsubscribe(topic, properties)
            if topic in self.subscribe_list:
                self.subscribe_list.remove(topic)
            if self.debug:
                SOPLOG_DEBUG(
                    f'{f"❌ Unsubscribed by {self.get_client_id()}":>16}: {topic:<80}, on {self.middleware.device.host}:{self.middleware.mqtt_port}', 'yellow')
        else:
            for item in topic:
                self.client.unsubscribe(item, properties)
                if item in self.subscribe_list:
                    self.subscribe_list.remove(item)
                if self.debug:
                    SOPLOG_DEBUG(
                        f'{f"❌ Unsubscribed by {self.get_client_id()}":>16}: {item:<80}, on {self.middleware.device.host}:{self.middleware.mqtt_port}', 'yellow')

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
        self.client.loop_start()

    def loop_stop(self):
        self.client.loop_stop()

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
        self.recv_message_queue.put(message)
        topic, payload, _ = decode_MQTT_message(message)

        if self.debug:
            SOPLOG_DEBUG(
                f'{f"✅ Received by {self.get_client_id()}":>16}(qos={message.qos}): {topic:<80}, {payload} on {self.middleware.device.host}:{self.middleware.mqtt_port}', 'yellow')


def main():
    client = SoPMQTTClient('mid1', '147.46.114.165', 21283)
    client.run()

    input('Press Enter to continue...')
    client.publish(
        'mid1',
        'MS/SCHEDULE/on_all/SuperThingTest_D45D64A628DB/SoPIoT-MW-thsvkd1_E45F01615B50/SoPIoT-MW-thsvkd1_E45F01615B50',
        '{ "scenario": "test1", "period": 0 }')

    input('Press Enter to continue...')
    client.publish(
        'mid1',
        'MS/SCHEDULE/on_all/SuperThingTest_D45D64A628DB/SoPIoT-MW-thsvkd1_E45F01615B50/SoPIoT-MW-thsvkd1_E45F01615B50',
        '{ "scenario": "test1", "period": 0 }')

    input('Press Enter to continue...')
    client.publish(
        'mid1',
        'MS/RESULT/SCHEDULE/on/BigThingTest_D45D64A628DB/SoPIoT-MW-thsvkd0_E45F016E0066/SuperThingTest_D45D64A628DB',
        '{ "error": 0, "scenario": "test1" }')


if __name__ == '__main__':
    main()
