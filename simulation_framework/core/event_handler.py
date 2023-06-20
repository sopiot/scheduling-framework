
from simulation_framework.core.components import *
from simulation_framework.config import *
from simulation_framework.ssh_client import *
from simulation_framework.mqtt_client import *
from tqdm import tqdm
from rich.progress import track, Progress

from big_thing_py.common.soptype import SoPProtocolType, SoPErrorType, SoPType
from big_thing_py.common.thread import SoPThread, Event, Empty


class SoPSimulationEnv:
    def __init__(self, config: SoPSimulationConfig, root_middleware: SoPMiddleware = None,
                 static_event_timeline: List['SoPEvent'] = [], dynamic_event_timeline: List['SoPEvent'] = [],
                 service_pool: List[SoPService] = [], thing_pool: List[SoPThing] = [],
                 simulation_data_file_path: str = '') -> None:
        self.config = config
        self.root_middleware = root_middleware
        self.static_event_timeline = static_event_timeline
        self.dynamic_event_timeline = dynamic_event_timeline
        self.service_pool = service_pool
        self.thing_pool = thing_pool
        self.simulation_data_file_path = simulation_data_file_path

    def dict(self):
        return dict(config_path=self.config.config_path,
                    root_middleware=self.root_middleware.dict(),
                    static_event_timeline=[event.dict() for event in self.static_event_timeline],
                    dynamic_event_timeline=[event.dict() for event in self.dynamic_event_timeline],
                    service_pool=[service.dict() for service in self.service_pool],
                    thing_pool=[thing.dict() for thing in self.thing_pool])


class SoPEventType(Enum):
    START = 'START'                                                     # Simulation 시작 이벤트. 해당 이벤트가 발생하면 Simulation duration 타이머가 시작된다.
    END = 'END'                                                         # Simulation 종료 이벤트. 해당 이벤트가 발생하면 Simulation duration 타이머가 종료된다.
    DELAY = 'DELAY'                                                     # Delay 이벤트. 명세된 시간만큼 딜레이를 발생시킨다.

    MIDDLEWARE_RUN = 'MIDDLEWARE_RUN'                                   # Middleware 실행 이벤트. 원격 디바이스에 Middleware 프로그램을 실행시킨다.
    MIDDLEWARE_KILL = 'MIDDLEWARE_KILL'                                 # Middleware 종료 이벤트. 원격 디바이스의 Middleware 프로그램을 종료시킨다.

    THING_RUN = 'THING_RUN'                                             # Thing 실행 이벤트. 원격 디바이스에 Thing 프로그램을 실행시킨다.
    THING_KILL = 'THING_KILL'                                           # Thing 종료 이벤트. 원격 디바이스의 Thing 프로그램에 SIGINT를 보내 강제 종료시킨다.
    THING_REGISTER = 'THING_REGISTER'                                   # Thing Register 이벤트. Thing이 Register 패킷을 보내는 경우의 이벤트이다.
    THING_UNREGISTER = 'THING_UNREGISTER'                               # Thing Unregister 이벤트. Thing이 Unregister 패킷을 보내는 경우의 이벤트이다.

    THING_REGISTER_RESULT = 'THING_REGISTER_RESULT'                     # Thing Register 결과 이벤트. Middleware가 Register 결과 패킷을 보내는 경우의 이벤트이다.
    THING_UNREGISTER_RESULT = 'THING_UNREGISTER_RESULT'                 # Thing Unregister 결과 이벤트. Middleware가 Unregister 결과 패킷을 보내는 경우의 이벤트이다.

    FUNCTION_EXECUTE = 'FUNCTION_EXECUTE'                               # Function Service Execute 이벤트. Middleware가 Thing 프로그램에 Function Service Execute 패킷을 보내는 경우의 이벤트이다.
    FUNCTION_EXECUTE_RESULT = 'FUNCTION_EXECUTE_RESULT'                 # Function Service Execute 결과 이벤트. Thing이 Function Service Execute를 수행한 결과 패킷을 보내는 경우의 이벤트이다.

    VALUE_PUBLISH = 'VALUE_PUBLISH'                                     # Value Service Publish 이벤트. Thing이 Value Service 값 패킷을 보내는 경우의 이벤트이다.

    SCENARIO_VERIFY = 'SCENARIO_VERIFY'                                 # Scenario 검증 이벤트. 시뮬레이터가 EM/VERIFY_SCENARIO 패킷을 전송한다.
    SCENARIO_ADD = 'SCENARIO_ADD'                                       # Scenario 추가 이벤트. 시뮬레이터가 EM/ADD_SCENARIO 패킷을 전송한다.
    SCENARIO_RUN = 'SCENARIO_RUN'                                       # Scenario 실행 이벤트. 시뮬레이터가 EM/RUN_SCENARIO 패킷을 전송한다.
    SCENARIO_STOP = 'SCENARIO_STOP'                                     # Scenario 중지 이벤트. 시뮬레이터가 EM/STOP_SCENARIO 패킷을 전송한다.
    SCENARIO_UPDATE = 'SCENARIO_UPDATE'                                 # Scenario 업데이트 이벤트. 시뮬레이터가 EM/UPDATE_SCENARIO 패킷을 전송한다.
    SCENARIO_DELETE = 'SCENARIO_DELETE'                                 # Scenario 삭제 이벤트. 시뮬레이터가 EM/DELETE_SCENARIO 패킷을 전송한다.

    SCENARIO_VERIFY_RESULT = 'SCENARIO_VERIFY_RESULT'                   # Scenario 검증 결과 이벤트. 시뮬레이터가 EM/VERIFY_SCENARIO 패킷을 전송한다.
    SCENARIO_ADD_RESULT = 'SCENARIO_ADD_RESULT'                         # Scenario 추가 결과 이벤트. 시뮬레이터가 EM/ADD_SCENARIO 패킷을 전송한다.
    SCENARIO_RUN_RESULT = 'SCENARIO_RUN_RESULT'                         # Scenario 실행 결과 이벤트. 시뮬레이터가 EM/RUN_SCENARIO 패킷을 전송한다.
    SCENARIO_STOP_RESULT = 'SCENARIO_STOP_RESULT'                       # Scenario 중지 결과 이벤트. 시뮬레이터가 EM/STOP_SCENARIO 패킷을 전송한다.
    SCENARIO_UPDATE_RESULT = 'SCENARIO_UPDATE_RESULT'                   # Scenario 업데이트 결과 이벤트. 시뮬레이터가 EM/UPDATE_SCENARIO 패킷을 전송한다.
    SCENARIO_DELETE_RESULT = 'SCENARIO_DELETE_RESULT'                   # Scenario 삭제 결과 이벤트. 시뮬레이터가 EM/DELETE_SCENARIO 패킷을 전송한다.

    SUPER_FUNCTION_EXECUTE = 'SUPER_FUNCTION_EXECUTE'                   # Super Function Service Execute 이벤트. Middleware가 Super Thing 프로그램에 Super Function Service Execute 패킷을 보내는 경우의 이벤트이다.
    SUPER_FUNCTION_EXECUTE_RESULT = 'SUPER_FUNCTION_EXECUTE_RESULT'     # Super Function Service Execute 결과 이벤트. Super Thing이 Super Function Service Execute를 수행한 결과 패킷을 보내는 경우의 이벤트이다.
    SUB_FUNCTION_EXECUTE = 'SUB_FUNCTION_EXECUTE'                       # Sub Function Service Execute 이벤트. Super Thing이 Middleware에게 Sub Function Service Execute 패킷을 보내는 경우의 이벤트이다.
    SUB_FUNCTION_EXECUTE_RESULT = 'SUB_FUNCTION_EXECUTE_RESULT'         # Sub Function Service Execute 결과 이벤트. Middleware가 Super Thing에게 Sub Function Service Execute를 수행한 결과 패킷을 보내는 경우의 이벤트이다.
    SUPER_SCHEDULE = 'SUPER_SCHEDULE'                                   # Super Schedule 이벤트. Middleware가 Super Thing 프로그램에 Super Schedule 패킷을 보내는 경우의 이벤트이다.
    SUPER_SCHEDULE_RESULT = 'SUPER_SCHEDULE_RESULT'                     # Super Schedule 결과 이벤트. Super Thing이 Super Schedule를 수행한 결과 패킷을 보내는 경우의 이벤트이다.
    SUB_SCHEDULE = 'SUB_SCHEDULE'                                       # Sub Schedule 이벤트. Super Thing이 Middleware에게 Sub Schedule 패킷을 보내는 경우의 이벤트이다.
    SUB_SCHEDULE_RESULT = 'SUB_SCHEDULE_RESULT'                         # Sub Schedule 결과 이벤트. Middleware가 Super Thing에게 Sub Schedule를 수행한 결과 패킷을 보내는 경우의 이벤트이다.

    REFRESH = 'REFRESH'                                                 # Refresh 이벤트. 시뮬레이터가 EM/REFRESH 패킷을 전송한다.
    SCENARIO_ADD_CHECK = 'SCENARIO_ADD_CHECK'                           # 모든 Scenario가 추가 완료될 때까지 기다리는 이벤트.
    SCENARIO_RUN_CHECK = 'SCENARIO_RUN_CHECK'                           # 모든 Scenario가 실행 완료될 때까지 기다리는 이벤트.

    UNDEFINED = 'UNDEFINED'

    def __str__(self):
        return self.value

    @classmethod
    def get(cls, name: str):
        try:
            return cls[name.upper()]
        except Exception:
            return cls.UNDEFINED


class SoPEvent:

    def __init__(self, event_type: SoPEventType, component: 'SoPComponent' = None, middleware_component: 'SoPMiddleware' = None, thing_component: 'SoPThing' = None, service_component: 'SoPService' = None, scenario_component: 'SoPScenario' = None,
                 timestamp: float = 0, duration: float = None, delay: float = None,
                 error: SoPErrorType = None, return_type: SoPType = None, return_value: ReturnType = None,
                 requester_middleware_name: str = None, super_thing_name: str = None, super_function_name: str = None,
                 *args, **kwargs) -> None:
        self.event_type = event_type

        self.component = component
        self.middleware_component = middleware_component
        self.thing_component = thing_component
        self.service_component = service_component
        self.scenario_component = scenario_component

        self.timestamp = timestamp
        self.duration = duration

        self.delay = delay

        self.error = error
        self.return_type = return_type
        self.return_value = return_value
        self.requester_middleware_name = requester_middleware_name
        self.super_thing_name = super_thing_name
        self.super_function_name = super_function_name

        self.args = args
        self.kwargs = kwargs

    def load(self, data: dict):
        self.event_type = SoPEventType.get(data['event_type']) if data['event_type'] is str else data['event_type']
        self.component = SoPComponent.load(data['component'])
        self.middleware_component = SoPComponent.load(data['middleware_component'])
        self.thing_component = SoPComponent.load(data['thing_component'])
        self.service_component = SoPComponent.load(data['service_component'])
        self.scenario_component = SoPComponent.load(data['scenario_component'])
        self.timestamp = data['timestamp']
        self.duration = data['duration']
        self.delay = data['delay']
        self.error = SoPErrorType.get(data['error']) if data['error'] is str else data['error']
        self.return_type = SoPType.get(data['return_type']) if data['return_type'] is str else data['return_type']
        self.return_value = data['return_value']
        self.requester_middleware_name = data['requester_middleware_name']

    def dict(self) -> dict:
        return dict(event_type=self.event_type.value,
                    component=self.component.name if self.component else None,
                    middleware_component=self.middleware_component.name if self.middleware_component else None,
                    thing_component=self.thing_component.name if self.thing_component else None,
                    service_component=self.service_component.name if self.service_component else None,
                    scenario_component=self.scenario_component.name if self.scenario_component else None,
                    timestamp=self.timestamp,
                    duration=self.duration,
                    delay=self.delay,
                    error=self.error,
                    return_type=self.return_type,
                    return_value=self.return_value,
                    requester_middleware_name=self.requester_middleware_name)


class SoPEventHandler:

    def __init__(self, root_middleware: SoPMiddleware = None, timeout: float = 5.0, running_time: float = None, download_logs: bool = False,
                 mqtt_debug: bool = False, middleware_debug: bool = False) -> None:
        self.root_middleware = root_middleware
        self.middleware_list: List[SoPMiddleware] = get_whole_middleware_list(self.root_middleware)
        self.thing_list: List[SoPThing] = get_whole_thing_list(self.root_middleware)
        self.scenario_list: List[SoPScenario] = get_whole_scenario_list(self.root_middleware)

        self.mqtt_client_list: List[SoPMQTTClient] = []
        self.ssh_client_list: List[SoPSSHClient] = []

        self.event_listener_event = Event()
        # self.event_listener_lock = Lock()
        self.event_listener_thread = SoPThread(name='event_listener', target=self._event_listener, args=(self.event_listener_event, ))

        # simulator와 같은 인스턴스를 공유한다.
        self.simulation_start_time = 0
        # self.simulation_duration = 0
        self.event_log: List[SoPEvent] = []
        self.timeout = timeout
        self.running_time = running_time

        self.mqtt_debug = mqtt_debug
        self.middleware_debug = middleware_debug

        self.download_logs = download_logs

        self.download_log_file_thread_queue = Queue()

    def _add_mqtt_client(self, mqtt_client: SoPMQTTClient):
        self.mqtt_client_list.append(mqtt_client)

    def _add_ssh_client(self, ssh_client: SoPSSHClient):
        self.ssh_client_list.append(ssh_client)

    def _event_listener(self, stop_event: Event):
        recv_msg: mqtt.MQTTMessage = None

        try:
            while not stop_event.wait(BUSY_WAIT_TIMEOUT / 100):
                for mqtt_client in self.mqtt_client_list:
                    try:
                        recv_msg = mqtt_client._recv_message_queue.get(timeout=BUSY_WAIT_TIMEOUT / 100)
                        self._on_recv_message(recv_msg)
                    except Empty:
                        recv_msg = None

        except Exception as e:
            stop_event.set()
            print_error()
            return False

    def start_event_listener(self):
        self.event_listener_thread.start()

    def stop_event_listener(self):
        self.event_listener_event.set()

    def remove_duplicated_device_instance(self) -> None:
        # When middleware has the same device, shares the SoPDeviceComponent instance.
        device_list = self._get_device_list()
        for middleware in self.middleware_list:
            for device in device_list:
                if device == middleware.device:
                    middleware.device = device

    def init_ssh_client_list(self) -> bool:
        with Progress() as progress:
            def task(device: SoPDevice):
                ssh_client = SoPSSHClient(device)
                ssh_client.connect(use_ssh_config=False)

                # 따로 명세되어있지 않고 local network에 있는 경우 사용 가능한 port를 찾는다.
                if device.mqtt_port:
                    device.available_port_list = []
                else:
                    if '192.168' in device.host or device.host == 'localhost':
                        device.available_port_list = ssh_client.available_port()
                        # SOPTEST_LOG_DEBUG(f'Found available port of {device.name}', SoPTestLogLevel.INFO)
                    else:
                        raise Exception(f'mqtt_port of {device.name} is not specified.')

                self._add_ssh_client(ssh_client)
                progress.update(task1, advance=1)

            device_list = self._get_device_list()
            task1 = progress.add_task(description='Init SSH client', total=len(device_list))
            pool_map(task, device_list)

        return True

    def init_mqtt_client_list(self):
        with Progress() as progress:
            def task(middleware: SoPMiddleware):
                if not self.middleware_debug:
                    if '192.168' in middleware.device.host or middleware.device.host == 'localhost':
                        picked_port_list = random.sample(middleware.device.available_port_list, 2)
                        middleware.localserver_port = picked_port_list[0]
                        if not middleware.mqtt_port:
                            middleware.mqtt_port = picked_port_list[1]
                    else:
                        picked_port_list = []

                    for picked_port in picked_port_list:
                        middleware.device.available_port_list.remove(picked_port)

                mqtt_client = SoPMQTTClient(middleware, debug=self.mqtt_debug)
                self._add_mqtt_client(mqtt_client)
                progress.update(task1, advance=1)

            task1 = progress.add_task(description='Init MQTT client', total=len(self.middleware_list))
            pool_map(task, self.middleware_list)

        return True

    def download_log_file(self) -> str:

        def task(middleware: SoPMiddleware):
            user = middleware.device.user
            ssh_client = self.find_ssh_client(middleware)
            ssh_client.open_sftp()

            remote_home_dir = f'/home/{user}'
            target_middleware_log_path = os.path.join(target_simulation_log_path, f'middleware.{ssh_client.device.name}.level{middleware.level}.{middleware.name}')

            file_attr_list = ssh_client._sftp_client.listdir_attr(
                middleware.remote_middleware_config_path)
            for file_attr in file_attr_list:
                ssh_client.get_file(remote_path=os.path.join(middleware.remote_middleware_config_path, file_attr.filename),
                                    local_path=os.path.join(target_middleware_log_path, 'middleware', f'{middleware.name}.cfg'), ext_filter='cfg')
                ssh_client.get_file(remote_path=os.path.join(middleware.remote_middleware_config_path, file_attr.filename),
                                    local_path=os.path.join(target_middleware_log_path, 'middleware', f'{middleware.name}.mosquitto.conf'), ext_filter='conf')
                ssh_client.get_file(remote_path=os.path.join(middleware.remote_middleware_config_path, file_attr.filename),
                                    local_path=os.path.join(target_middleware_log_path, 'middleware', f'{middleware.name}_mosquitto.log'), ext_filter='log')

            remote_middleware_log_path = os.path.join(remote_home_dir, 'simulation_log')
            file_attr_list = ssh_client._sftp_client.listdir_attr(remote_middleware_log_path)
            for file_attr in file_attr_list:
                file_base_name = file_attr.filename.split(".")[0]
                if not (f'{file_base_name}' == f"{middleware.name}_middleware" or f'{file_base_name}' == middleware.name):
                    continue
                ssh_client.get_file(remote_path=os.path.join(remote_middleware_log_path, file_attr.filename),
                                    local_path=os.path.join(target_middleware_log_path, 'middleware', f'{middleware.name}.log'), ext_filter='log')
                ssh_client.get_file(remote_path=os.path.join(remote_middleware_log_path, file_attr.filename),
                                    local_path=os.path.join(target_middleware_log_path, 'middleware', f'{middleware.name}.stdout'), ext_filter='stdout')

            for thing in middleware.thing_list:
                thing_ssh_client = self.find_ssh_client(thing)
                thing_ssh_client.open_sftp()

                target_thing_log_file_name = f'base_thing.{thing.name}.log' if not thing.is_super else f'super_thing.{thing.name}.log'

                thing_log_path = os.path.join(os.path.dirname(thing.remote_thing_file_path), 'log')

                file_attr_list = thing_ssh_client._sftp_client.listdir_attr(thing_log_path)
                for file_attr in file_attr_list:
                    if not thing.name in file_attr.filename:
                        continue
                    thing_ssh_client.get_file(remote_path=os.path.join(thing_log_path, file_attr.filename),
                                              local_path=os.path.join(target_middleware_log_path, 'thing', target_thing_log_file_name), ext_filter='log')

            return True

        target_simulation_log_path = home_dir_append(f'remote_logs/simulation_log_{get_current_time(mode=TimeFormat.DATETIME2)}')

        pool_map(task, self.middleware_list, proc=1)

        return target_simulation_log_path

    def event_trigger(self, event: SoPEvent):
        # wait until timestamp is reached
        if event.timestamp == None:
            raise Exception('timestamp is not defined')
        while get_current_time() - self.simulation_start_time < event.timestamp:
            time.sleep(BUSY_WAIT_TIMEOUT)

        if event.event_type == SoPEventType.DELAY:
            SOPTEST_LOG_DEBUG(f'Delay {event.delay} Sec start...', SoPTestLogLevel.INFO, 'yellow')
            self.event_log.append(event)
            time.sleep(event.delay)
        elif event.event_type == SoPEventType.START:
            cur_time = get_current_time()
            event.timestamp = cur_time
            self.simulation_start_time = cur_time
            SOPTEST_LOG_DEBUG(f'Simulation Start', SoPTestLogLevel.PASS, 'yellow')
        elif event.event_type == SoPEventType.END:
            event.timestamp = get_current_time() - self.simulation_start_time
            SOPTEST_LOG_DEBUG(f'Simulation End. duration: {event.timestamp:8.3f} sec', SoPTestLogLevel.PASS, 'yellow')

            # for check scenario state
            self.refresh(timeout=self.timeout, scenario_check=True, check_interval=3.0)
            self.stop_event_listener()
            self.kill_every_process()

            return True
        else:
            target_component = event.component
            if event.event_type == SoPEventType.MIDDLEWARE_RUN:
                # parent_middleware = self.find_parent_middleware(target_component)
                # if parent_middleware:
                #     while not parent_middleware.online:
                #         time.sleep(BUSY_WAIT_TIMEOUT)
                while not self.check_middleware_online(target_component):
                    time.sleep(BUSY_WAIT_TIMEOUT)
                SoPThread(name=f'{event.event_type.value}_{event.component.name}',
                          target=self.run_middleware, args=(target_component, 10, )).start()
                self.subscribe_scenario_finish_topic(middleware=target_component)
            elif event.event_type == SoPEventType.MIDDLEWARE_KILL:
                SoPThread(name=f'{event.event_type.value}_{event.component.name}',
                          target=self.kill_middleware, args=(target_component, )).start()
            elif event.event_type == SoPEventType.THING_RUN:
                while not self.check_middleware_online(target_component):
                    time.sleep(BUSY_WAIT_TIMEOUT)
                SoPThread(name=f'{event.event_type.value}_{event.component.name}',
                          target=self.run_thing, args=(target_component, 30, )).start()
            elif event.event_type == SoPEventType.THING_KILL:
                SoPThread(name=f'{event.event_type.value}_{event.component.name}',
                          target=self.kill_thing, args=(target_component, )).start()
            elif event.event_type == SoPEventType.THING_UNREGISTER:
                SoPThread(name=f'{event.event_type.value}_{event.component.name}',
                          target=self.unregister_thing, args=(target_component, )).start()
            elif event.event_type == SoPEventType.SCENARIO_VERIFY:
                SoPThread(name=f'{event.event_type.value}_{event.component.name}',
                          target=self.verify_scenario, args=(target_component, self.timeout, )).start()
            elif event.event_type == SoPEventType.SCENARIO_ADD:
                SoPThread(name=f'{event.event_type.value}_{event.component.name}',
                          target=self.add_scenario, args=(target_component, self.timeout, )).start()
            elif event.event_type == SoPEventType.SCENARIO_RUN:
                SoPThread(name=f'{event.event_type.value}_{event.component.name}',
                          target=self.run_scenario, args=(target_component, self.timeout, )).start()
            elif event.event_type == SoPEventType.SCENARIO_STOP:
                SoPThread(name=f'{event.event_type.value}_{event.component.name}',
                          target=self.stop_scenario, args=(target_component, self.timeout, )).start()
            elif event.event_type == SoPEventType.SCENARIO_UPDATE:
                SoPThread(name=f'{event.event_type.value}_{event.component.name}',
                          target=self.update_scenario, args=(target_component, self.timeout, )).start()
            elif event.event_type == SoPEventType.SCENARIO_DELETE:
                SoPThread(name=f'{event.event_type.value}_{event.component.name}',
                          target=self.delete_scenario, args=(target_component, self.timeout, )).start()
            elif event.event_type == SoPEventType.REFRESH:
                self.refresh(timeout=self.timeout, check_interval=3.0, **event.kwargs)
            elif event.event_type == SoPEventType.SCENARIO_ADD_CHECK:
                self.scenario_add_check(timeout=self.timeout)
            elif event.event_type == SoPEventType.SCENARIO_RUN_CHECK:
                self.scenario_run_check(timeout=self.timeout)
            else:
                raise SOPTEST_LOG_DEBUG(f'Event type is {event.event_type}, but not implemented yet', SoPTestLogLevel.FAIL)

    ####  middleware   #############################################################################################################

    def run_mosquitto(self, middleware: SoPMiddleware, ssh_client: SoPSSHClient, remote_home_dir: str):
        remote_mosquitto_conf_file_path = f'{middleware.remote_middleware_config_path}/{middleware.name}_mosquitto.conf'
        ssh_client.send_command(f'/sbin/mosquitto -c {remote_mosquitto_conf_file_path.replace("~", remote_home_dir)} '
                                f'-v 2> {middleware.remote_middleware_config_path.replace("~", remote_home_dir)}/{middleware.name}_mosquitto.log &', ignore_result=True)
        target_mosquitto_pid_list = ssh_client.send_command(f'netstat -lpn | grep :{middleware.mqtt_port}')
        if len(target_mosquitto_pid_list) > 0:
            return True

    def init_middleware(self, middleware: SoPMiddleware, ssh_client: SoPSSHClient, remote_home_dir: str):
        remote_init_script_file_path = f'{middleware.remote_middleware_config_path}/{middleware.name}_init.sh'
        ssh_client.send_command(f'chmod +x {remote_init_script_file_path.replace("~",remote_home_dir)}; '
                                f'bash {remote_init_script_file_path.replace("~",remote_home_dir)}')

    def subscribe_scenario_finish_topic(self, middleware: SoPMiddleware):
        mqtt_client = self.find_mqtt_client(middleware)
        while not mqtt_client.is_run:
            time.sleep(BUSY_WAIT_TIMEOUT)
        mqtt_client.subscribe('SIM/FINISH')

    def run_middleware(self, middleware: SoPMiddleware, timeout: float = 5) -> bool:

        def wait_parent_middleware_online(middleware: SoPMiddleware) -> bool:
            SOPTEST_LOG_DEBUG(f'Wait for middleware: {middleware.name}, device: {middleware.device.name} online', SoPTestLogLevel.INFO, 'yellow')
            parent_middleware = middleware.parent
            if not parent_middleware:
                return True
            else:
                while not parent_middleware.online:
                    time.sleep(BUSY_WAIT_TIMEOUT)
                else:
                    return True

        def middleware_run_command(middleware: SoPMiddleware, remote_home_dir: str) -> str:
            log_file_path = ''
            for line in middleware.middleware_cfg.split('\n'):
                if 'log_file_path = ' in line:
                    log_file_path = line.split('"')[1].strip('"')
                    log_file_path = os.path.dirname(log_file_path)
                    break

            user = os.path.basename(remote_home_dir)
            home_dir_append(middleware.remote_middleware_path, user)
            cd_to_config_dir_command = f'cd {os.path.dirname(middleware.remote_middleware_config_path).replace("~", remote_home_dir)}'
            remote_middleware_cfg_file_path = f'{middleware.remote_middleware_config_path}/{middleware.name}_middleware.cfg'
            run_command = (f'mkdir -p {log_file_path}; cd {home_dir_append(middleware.remote_middleware_path, user)}; '
                           f'./sopiot_middleware -f {remote_middleware_cfg_file_path.replace("~", remote_home_dir)} > {log_file_path}/{middleware.name}.stdout 2>&1 &')
            return f'{cd_to_config_dir_command}; {run_command}'

        def check_online(mqtt_client: SoPMQTTClient, timeout: float) -> bool:
            expect_msg = self.publish_and_expect(
                middleware,
                encode_MQTT_message(SoPProtocolType.WebClient.EM_REFRESH.value % f'{mqtt_client.get_client_id()}@{middleware.name}', '{}'),
                SoPProtocolType.WebClient.ME_RESULT_SERVICE_LIST.value % (f'{mqtt_client.get_client_id()}@{middleware.name}'),
                auto_subscribe=True,
                auto_unsubscribe=False,
                timeout=timeout)

            if expect_msg == SoPErrorType.TIMEOUT:
                return False

            middleware.online = True
            return True

        def check_online_cyclic(mqtt_client: SoPMQTTClient, timeout: int, check_interval: float) -> Union[bool, SoPErrorType]:
            cur_time = get_current_time()
            while get_current_time() - cur_time < timeout:
                if check_online(mqtt_client=mqtt_client, timeout=check_interval):
                    SOPTEST_LOG_DEBUG(f'Middleware: {middleware.name}, device: {middleware.device.name} on {middleware.device.host}:{middleware.mqtt_port} '
                                      f'- websocket: {middleware.websocket_port} is online!', SoPTestLogLevel.PASS)
                    return True
                else:
                    time.sleep(BUSY_WAIT_TIMEOUT)
            else:
                SOPTEST_LOG_DEBUG(f'[TIMEOUT] Running middleware: {middleware.name}, device: {middleware.device.name} is failed...', SoPTestLogLevel.FAIL)
                return SoPErrorType.TIMEOUT

        ssh_client = self.find_ssh_client(middleware)
        mqtt_client = self.find_mqtt_client(middleware)
        wait_parent_middleware_online(middleware)

        user = middleware.device.user
        remote_home_dir = f'/home/{user}'
        self.run_mosquitto(middleware, ssh_client, remote_home_dir)
        self.init_middleware(middleware, ssh_client, remote_home_dir)
        mqtt_client.run()
        if not ssh_client.send_command_with_check_success(middleware_run_command(middleware=middleware, remote_home_dir=remote_home_dir)):
            raise SimulationFrameworkError(f'Send middleware run command failed! - middleware: {middleware.name}, device: {middleware.device.name}')

        if check_online_cyclic(mqtt_client, timeout=timeout, check_interval=0.5) == SoPErrorType.TIMEOUT:
            SOPTEST_LOG_DEBUG(f'Retry to run middleware: {middleware.name}, device: {middleware.device.name}...', SoPTestLogLevel.WARN)
            if not self.kill_middleware(middleware):
                raise SimulationFrameworkError(f'Send middleware kill command failed! - middleware: {middleware.name}, device: {middleware.device.name} failed!')
            return self.run_middleware(middleware, timeout=timeout)

        return True

    def kill_middleware(self, middleware: SoPMiddleware) -> bool:
        ssh_client = self.find_ssh_client(middleware)
        pid_list = self.get_component_proc_pid(ssh_client, middleware)

        if pid_list['middleware_pid_list']:
            for middleware_pid in pid_list['middleware_pid_list']:
                if middleware_pid:
                    return ssh_client.send_command_with_check_success(f'kill -9 {middleware_pid}')
        if pid_list['mosquitto_pid_list']:
            for mosquitto_pid in pid_list['mosquitto_pid_list']:
                if mosquitto_pid:
                    return ssh_client.send_command_with_check_success(f'kill -9 {mosquitto_pid}')

    ####  thing   #############################################################################################################

    def subscribe_thing_topic(self, thing: SoPThing, mqtt_client: SoPMQTTClient):
        for service in thing.service_list:
            mqtt_client.subscribe([SoPProtocolType.Base.MT_EXECUTE.value % (service.name, thing.name, thing.middleware_client_name, '#'),
                                   (SoPProtocolType.Base.MT_EXECUTE.value % (service.name, thing.name, '', '')).rstrip('/'),
                                   SoPProtocolType.Base.TM_RESULT_EXECUTE.value % (service.name, thing.name, '+', '#'),
                                   (SoPProtocolType.Base.TM_RESULT_EXECUTE.value % (service.name, thing.name, '', '')).rstrip('/')])
            if thing.is_super:
                mqtt_client.subscribe([
                    SoPProtocolType.Super.MS_EXECUTE.value % (service.name, thing.name, thing.middleware_client_name, '#'),
                    SoPProtocolType.Super.SM_EXECUTE.value % ('+', '+', '+', '#'),
                    SoPProtocolType.Super.MS_RESULT_EXECUTE.value % ('+', '+', '+', '#'),
                    SoPProtocolType.Super.SM_RESULT_EXECUTE.value % (service.name, thing.name, thing.middleware_client_name, '#'),
                    SoPProtocolType.Super.MS_SCHEDULE.value % (service.name, thing.name, thing.middleware_client_name, '#'),
                    SoPProtocolType.Super.SM_SCHEDULE.value % ('+', '+', '+', '#'),
                    SoPProtocolType.Super.MS_RESULT_SCHEDULE.value % ('+', '+', '+', '#'),
                    SoPProtocolType.Super.SM_RESULT_SCHEDULE.value % (service.name, thing.name, thing.middleware_client_name, '#')])
        # for value in self._value_list:
        #     mqtt_client.subscribe([SoPProtocolType.Default.TM_VALUE_PUBLISH.value % (thing.name, value['name']), SoPProtocolType.Default.TM_VALUE_PUBLISH_OLD.value % (thing.name, value['name'])])

    def run_thing(self, thing: SoPThing, timeout: float = 5):
        middleware = self.find_parent_middleware(thing)
        ssh_client = self.find_ssh_client(thing)
        mqtt_client = self.find_mqtt_client(middleware)

        target_topic_list = [SoPProtocolType.Base.TM_REGISTER.value % thing.name,
                             SoPProtocolType.Base.TM_UNREGISTER.value % thing.name,
                             SoPProtocolType.Base.MT_RESULT_REGISTER.value % thing.name,
                             SoPProtocolType.Base.MT_RESULT_UNREGISTER.value % thing.name]
        mqtt_client.subscribe(target_topic_list)

        user = middleware.device.user
        thing_cd_command = f'cd {os.path.dirname(thing.remote_thing_file_path)}'
        thing_run_command = (f'{thing_cd_command}; python {home_dir_append(thing.remote_thing_file_path, user)} -n {thing.name} -ip '
                             f'{mqtt_client.host if not thing.is_super else "localhost"} -p {mqtt_client.port} -ac {thing.alive_cycle} --retry_register > /dev/null 2>&1 & echo $!')
        # print(thing_run_command.split('>')[0].strip())
        thing_run_result = ssh_client.send_command(thing_run_command)
        thing.pid = thing_run_result[0]

        self.command_and_expect(
            thing,
            thing_run_command,
            SoPProtocolType.Base.TM_REGISTER.value % (thing.name),
        )
        reg_start_time = get_current_time()
        recv_msg = self.expect(
            thing,
            SoPProtocolType.Base.MT_RESULT_REGISTER.value % (thing.name),
        )
        reg_end_time = get_current_time()

        topic, payload, _ = decode_MQTT_message(recv_msg)
        if recv_msg == SoPErrorType.TIMEOUT:
            self.kill_thing(thing)
            self.run_thing(thing, timeout=timeout)
        elif self._check_result_payload(payload):
            thing.registered = True
            thing.middleware_client_name = payload['middleware_name']
            self.subscribe_thing_topic(thing, mqtt_client)

            progress = [thing.registered for thing in self.thing_list].count(True) / len(self.thing_list)
            SOPTEST_LOG_DEBUG(f'[REGISTER] thing: {thing.name} duration: {(reg_end_time - reg_start_time):0.4f}', SoPTestLogLevel.INFO, progress=progress, color='green')
            return True

    def unregister_thing(self, thing: SoPThing):
        SOPTEST_LOG_DEBUG(f'Unregister Thing {thing.name}...', SoPTestLogLevel.INFO, color='yellow')
        ssh_client = self.find_ssh_client(thing)
        ssh_client.send_command(f'kill -2 {thing.pid}')

    def kill_thing(self, thing: SoPThing):
        SOPTEST_LOG_DEBUG(f'Kill Thing {thing.name}...', SoPTestLogLevel.INFO, color='yellow')
        ssh_client = self.find_ssh_client(thing)
        ssh_client.send_command(f'kill -9 {thing.pid}')

    ####  scenario   #############################################################################################################

    def refresh(self, timeout: float, check_interval: float = 3.0, scenario_check: bool = True, service_check: bool = False, thing_register_check: bool = False):
        refresh_result: List[bool] = []

        def get_init_failed_scenario(middleware: SoPMiddleware, scenario_info_list: List[SoPScenarioInfo]) -> List[SoPScenario]:
            if not scenario_info_list:
                return []

            init_failed_scenario_list = []
            for scenario in middleware.scenario_list:
                for scenario_info in scenario_info_list:
                    scenario.state = scenario_info.state
                    if scenario.name != scenario_info.name:
                        continue
                    if scenario.state == SoPScenarioState.INITIALIZED:
                        scenario.schedule_success = True
                        break
                    else:
                        SOPTEST_LOG_DEBUG(f'Scenario {scenario.name} is in {scenario.state.value} state...', SoPTestLogLevel.WARN)
                        init_failed_scenario_list.append(scenario)
                else:
                    SOPTEST_LOG_DEBUG(f'Scenario {scenario.name} is not in scenario list of {middleware.name}...', SoPTestLogLevel.WARN)
                    init_failed_scenario_list.append(scenario)

            return init_failed_scenario_list

        def check_service_list_valid(scenario: SoPScenario, service_info_list: List[SoPService]) -> bool:
            if not service_info_list:
                return False

            for service in scenario.service_list:
                if not service.name in [service_info.name for service_info in service_info_list]:
                    SOPTEST_LOG_DEBUG(f'service {service.name} is not in Scenario {scenario.name}', SoPTestLogLevel.WARN)
                    return False
            else:
                return True

        def get_register_failed_thing(middleware: SoPMiddleware):
            thing_list = get_whole_thing_list(middleware)

            register_failed_thing_list = []
            for thing in thing_list:
                if not thing.registered:
                    SOPTEST_LOG_DEBUG(f'Thing {thing.name} is not registered...', SoPTestLogLevel.WARN)
                    register_failed_thing_list.append(thing)

            return register_failed_thing_list

        def task(middleware: SoPMiddleware, timeout: float):
            SOPTEST_LOG_DEBUG(f'Refresh Start... middleware: {middleware.name}, device: {middleware.device.name}', SoPTestLogLevel.INFO)
            whole_service_info_list: List[SoPService] = []
            whole_scenario_info_list: List[SoPScenarioInfo] = []

            if scenario_check:
                whole_scenario_info_list = self.get_whole_scenario_info(middleware, timeout=timeout)
                init_failed_scenario_list = get_init_failed_scenario(middleware, whole_scenario_info_list)
                if len(init_failed_scenario_list) > 0:
                    for scenario in init_failed_scenario_list:
                        refresh_result.append(False)
                        SOPTEST_LOG_DEBUG(f'Scenario {scenario.name} in {middleware.name} init failed...', SoPTestLogLevel.FAIL)
            if service_check:
                whole_service_info_list = self.get_whole_service_list_info(middleware, timeout=timeout)
                scenario_list = get_whole_scenario_list(middleware)
                for scenario in scenario_list:
                    if not check_service_list_valid(scenario=scenario, service_info_list=whole_service_info_list):
                        refresh_result.append(False)
                        SOPTEST_LOG_DEBUG(f'Scenario {scenario.name} in {middleware.name} service check failed...', SoPTestLogLevel.FAIL)
            if thing_register_check:
                register_failed_thing_list = get_register_failed_thing(middleware)
                if len(register_failed_thing_list) > 0:
                    refresh_result.append(False)
                    SOPTEST_LOG_DEBUG(f'Thing register failed...', SoPTestLogLevel.FAIL)

            refresh_result.append(True)
            SOPTEST_LOG_DEBUG(f'Refresh Success! middleware: {middleware.name}', SoPTestLogLevel.INFO)

        cur_time1 = get_current_time()
        while get_current_time() - cur_time1 < timeout:
            cur_time2 = get_current_time()
            pool_map(task, [(middleware, check_interval) for middleware in self.middleware_list])

            if all(refresh_result):
                break
            else:
                refresh_result = []

            while get_current_time() - cur_time2 < check_interval:
                time.sleep(BUSY_WAIT_TIMEOUT * 10)

        return True

    def scenario_add_check(self, timeout: float):
        while not all([scenario.add_result_arrived for scenario in self.scenario_list]):
            time.sleep(BUSY_WAIT_TIMEOUT)
        SOPTEST_LOG_DEBUG(f'All scenario Add is complete!...', SoPTestLogLevel.INFO)

        return True

    def scenario_run_check(self, timeout: float):
        for middleware in self.middleware_list:
            whole_scenario_info_list: List[SoPScenarioInfo] = self.get_whole_scenario_info(middleware, timeout=timeout)
            if whole_scenario_info_list is False:
                return False

            # scenario run check
            for scenario in middleware.scenario_list:
                for scenario_info in whole_scenario_info_list:
                    scenario_info: SoPScenarioInfo
                    scenario.state = scenario_info.state
                    if scenario.name != scenario_info.name:
                        continue
                    if scenario.state in [SoPScenarioState.RUNNING, SoPScenarioState.EXECUTING]:
                        break
                    else:
                        SOPTEST_LOG_DEBUG(f'Scenario {scenario.name} is not in RUN state...', SoPTestLogLevel.WARN)
                else:
                    SOPTEST_LOG_DEBUG(f'[SCENARIO RUN CHECK] Scenario {scenario.name} is not in scenario list of {middleware.name}...', SoPTestLogLevel.WARN)

            SOPTEST_LOG_DEBUG(f'Scenario Run Check Success! middleware: {middleware.name}', SoPTestLogLevel.PASS)

        return True

    def verify_scenario(self, scenario: SoPScenario, timeout: float = 5):
        middleware = self.find_parent_middleware(scenario)
        mqtt_client = self.find_mqtt_client(middleware)

        trigger_topic = SoPProtocolType.WebClient.EM_VERIFY_SCENARIO.value % mqtt_client.get_client_id()
        trigger_payload = json_string_to_dict(dict(name=scenario.name, text=scenario.scenario_code()))
        trigger_message = encode_MQTT_message(trigger_topic, trigger_payload)
        target_topic = SoPProtocolType.WebClient.ME_RESULT_VERIFY_SCENARIO.value % mqtt_client.get_client_id()

        mqtt_client.subscribe(trigger_topic)
        recv_msg = self.publish_and_expect(
            scenario,
            trigger_message,
            target_topic,
            auto_unsubscribe=False,
            timeout=timeout)

        topic, payload, _ = decode_MQTT_message(recv_msg)
        if recv_msg == SoPErrorType.TIMEOUT:
            SOPTEST_LOG_DEBUG(f'{SoPComponentType.SCENARIO.value} of scenario: {scenario.name}, device: {scenario.middleware.device.name} {SoPComponentActionType.SCENARIO_VERIFY.value} failed...', SoPTestLogLevel.FAIL)
        return self

    def add_scenario(self, scenario: SoPScenario, timeout: float = 5, check_interval: float = 1.0):
        middleware = self.find_parent_middleware(scenario)
        mqtt_client = self.find_mqtt_client(middleware)

        trigger_topic = SoPProtocolType.WebClient.EM_ADD_SCENARIO.value % mqtt_client.get_client_id()
        trigger_payload = json_string_to_dict(dict(name=scenario.name, text=scenario.scenario_code(), priority=scenario.priority))
        trigger_message = encode_MQTT_message(trigger_topic, trigger_payload)
        target_topic = SoPProtocolType.WebClient.ME_RESULT_ADD_SCENARIO.value % mqtt_client.get_client_id()

        mqtt_client.subscribe(trigger_topic)
        scenario.add_result_arrived = False
        scenario.schedule_timeout = False
        scenario.schedule_success = False

        mqtt_client.subscribe(trigger_topic)
        pub_time = get_current_time()
        recv_msg = self.publish_and_expect(
            scenario,
            trigger_message,
            target_topic,
            auto_subscribe=True,
            auto_unsubscribe=False,
            timeout=timeout)
        recv_time = get_current_time()

        topic, payload, _ = decode_MQTT_message(recv_msg)
        if recv_msg == SoPErrorType.TIMEOUT:
            SOPTEST_LOG_DEBUG(f'{SoPComponentType.SCENARIO.value} scenario: {scenario.name}, device: {scenario.middleware.device.name} {SoPComponentActionType.SCENARIO_ADD.value} failed...', SoPTestLogLevel.FAIL)
            SOPTEST_LOG_DEBUG(f'==== Fault Scenario ====', SoPTestLogLevel.FAIL)
            SOPTEST_LOG_DEBUG(f'name: {scenario.name}', SoPTestLogLevel.FAIL)
            SOPTEST_LOG_DEBUG(f'code: \n{scenario.scenario_code()}', SoPTestLogLevel.FAIL)
            scenario.schedule_timeout = True
            return False
        elif self._check_result_payload(payload):
            scenario.add_result_arrived = True

            progress = [scenario.add_result_arrived for scenario in self.scenario_list].count(True) / len(self.scenario_list)
            SOPTEST_LOG_DEBUG(f'[SCENE_ADD] scenario: {scenario.name} duration: {(recv_time - pub_time):0.4f}', SoPTestLogLevel.INFO, progress=progress, color='green')
            return True

        SOPTEST_LOG_DEBUG(f'middleware: {middleware.name} scenario: {scenario.name}, device: {scenario.middleware.device.name} {SoPComponentActionType.SCENARIO_ADD.value} success...', SoPTestLogLevel.WARN)

    def run_scenario(self, scenario: SoPScenario, timeout: float = 5):
        # NOTE: 이미 add_scenario를 통해 시나리오가 정상적으로 init되어있는 것이 확인되어있는 상태이므로 다시 시나리오상태를 확인할 필요는 없다.

        if scenario.schedule_timeout:
            SOPTEST_LOG_DEBUG(f'Scenario {scenario.name} is timeout. Skip scenario run...', SoPTestLogLevel.WARN)
            return False
        if not scenario.schedule_success:
            SOPTEST_LOG_DEBUG(f'Scenario {scenario.name} is not initialized. Skip scenario run...', SoPTestLogLevel.WARN)
            return False

        middleware = self.find_parent_middleware(scenario)
        mqtt_client = self.find_mqtt_client(middleware)

        trigger_topic = SoPProtocolType.WebClient.EM_RUN_SCENARIO.value % mqtt_client.get_client_id()
        trigger_payload = json_string_to_dict(dict(name=scenario.name))
        trigger_message = encode_MQTT_message(trigger_topic, trigger_payload)
        target_topic = SoPProtocolType.WebClient.ME_RESULT_RUN_SCENARIO.value % mqtt_client.get_client_id()

        mqtt_client.subscribe(trigger_topic)
        pub_time = get_current_time()
        recv_msg = self.publish_and_expect(
            scenario,
            trigger_message,
            target_topic,
            auto_subscribe=True,
            auto_unsubscribe=False,
            timeout=timeout)
        recv_time = get_current_time()

        topic, payload, _ = decode_MQTT_message(recv_msg)
        if recv_msg == SoPErrorType.TIMEOUT:
            SOPTEST_LOG_DEBUG(f'{SoPComponentType.SCENARIO.value} scenario: {scenario.name}, device: {scenario.middleware.device.name} {SoPComponentActionType.SCENARIO_RUN.value} failed...', SoPTestLogLevel.FAIL)
            return False
        elif self._check_result_payload(payload):
            progress = [scenario.add_result_arrived for scenario in self.scenario_list].count(True) / len(self.scenario_list)
            SOPTEST_LOG_DEBUG(f'[SCENE_RUN] scenario: {scenario.name} duration: {(recv_time - pub_time):0.4f}', SoPTestLogLevel.INFO, progress=progress, color='green')
            return True

    def stop_scenario(self, scenario: SoPScenario, timeout: float = 5):
        middleware = self.find_parent_middleware(scenario)
        mqtt_client = self.find_mqtt_client(middleware)

        trigger_topic = SoPProtocolType.WebClient.EM_STOP_SCENARIO.value % mqtt_client.get_client_id()
        trigger_payload = json_string_to_dict(dict(name=scenario.name))
        trigger_message = encode_MQTT_message(trigger_topic, trigger_payload)
        target_topic = SoPProtocolType.WebClient.ME_RESULT_STOP_SCENARIO.value % mqtt_client.get_client_id()

        # NOTE: 시나리오의 상태를 확인할 필요 없이 바로 stop을 해도 먹히는지 확인이 필요
        # if not self.get_scenario_state(scenario, timeout=timeout) in [SoPScenarioState.RUNNING, SoPScenarioState.EXECUTING]:
        #     SOPTEST_LOG_DEBUG(
        #         f'Fail to stop scenario {scenario.name} - state: {scenario.state.value}', SoPTestLogLevel.FAIL)
        #     return False

        mqtt_client.subscribe(trigger_topic)
        recv_msg = self.publish_and_expect(
            scenario,
            trigger_message,
            target_topic,
            auto_subscribe=True,
            auto_unsubscribe=False,
            timeout=timeout)

        if recv_msg == SoPErrorType.TIMEOUT:
            SOPTEST_LOG_DEBUG(f'{SoPComponentType.SCENARIO.value} scenario: {scenario.name}, device: {scenario.middleware.device.name} {SoPComponentActionType.SCENARIO_STOP.value} failed...', SoPTestLogLevel.FAIL)
        return self

    def update_scenario(self, scenario: SoPScenario, timeout: float = 5):
        middleware = self.find_parent_middleware(scenario)
        mqtt_client = self.find_mqtt_client(middleware)

        trigger_topic = SoPProtocolType.WebClient.EM_UPDATE_SCENARIO.value % mqtt_client.get_client_id()
        trigger_payload = json_string_to_dict(dict(name=scenario.name))
        trigger_message = encode_MQTT_message(trigger_topic, trigger_payload)
        target_topic = SoPProtocolType.WebClient.ME_RESULT_UPDATE_SCENARIO.value % mqtt_client.get_client_id()

        # NOTE: 시나리오의 상태를 확인할 필요 없이 바로 update을 해도 먹히는지 확인이 필요
        # if not self.get_scenario_state(scenario, timeout=timeout) in [SoPScenarioState.STUCKED]:
        #     SOPTEST_LOG_DEBUG(
        #         f'Fail to stop scenario {scenario.name} - state: {scenario.state.value}', SoPTestLogLevel.FAIL)
        #     return False

        mqtt_client.subscribe(trigger_topic)
        recv_msg = self.publish_and_expect(
            scenario,
            trigger_message,
            target_topic,
            auto_subscribe=True,
            auto_unsubscribe=False,
            timeout=timeout)

        if recv_msg == SoPErrorType.TIMEOUT:
            SOPTEST_LOG_DEBUG(f'{SoPComponentType.SCENARIO.value} scenario: {scenario.name}, device: {scenario.middleware.device.name} {SoPComponentActionType.SCENARIO_UPDATE.value} failed...', SoPTestLogLevel.FAIL)
        return self

    def delete_scenario(self, scenario: SoPScenario, timeout: float = 5):
        middleware = self.find_parent_middleware(scenario)
        mqtt_client = self.find_mqtt_client(middleware)

        trigger_topic = SoPProtocolType.WebClient.EM_DELETE_SCENARIO.value % mqtt_client.get_client_id()
        trigger_payload = json_string_to_dict(dict(name=scenario.name))
        trigger_message = encode_MQTT_message(trigger_topic, trigger_payload)
        target_topic = SoPProtocolType.WebClient.ME_RESULT_DELETE_SCENARIO.value % mqtt_client.get_client_id()

        # NOTE: 시나리오의 상태를 확인할 필요 없이 바로 delete를 해도 먹히는지 확인이 필요
        # if not self.get_scenario_state(scenario, timeout=timeout) in [SoPScenarioState.RUNNING, SoPScenarioState.EXECUTING]:
        #     SOPTEST_LOG_DEBUG(
        #         f'Fail to stop scenario {scenario.name} - state: {scenario.state.value}', SoPTestLogLevel.FAIL)
        #     return False
        mqtt_client.subscribe(trigger_topic)
        recv_msg = self.publish_and_expect(
            scenario,
            trigger_message,
            target_topic,
            auto_subscribe=True,
            auto_unsubscribe=False,
            timeout=timeout)

        if recv_msg == SoPErrorType.TIMEOUT:
            SOPTEST_LOG_DEBUG(f'{SoPComponentType.SCENARIO.value} scenario: {scenario.name}, device: {scenario.middleware.device.name} {SoPComponentActionType.SCENARIO_DELETE.value} failed...', SoPTestLogLevel.FAIL)
        return self

    def get_whole_scenario_info(self, middleware: SoPMiddleware, timeout: float) -> List[SoPScenarioInfo]:
        mqtt_client = self.find_mqtt_client(middleware)

        recv_msg = self.publish_and_expect(
            middleware,
            encode_MQTT_message(SoPProtocolType.WebClient.EM_REFRESH.value % f'{mqtt_client.get_client_id()}@{middleware.name}', '{}'),
            SoPProtocolType.WebClient.ME_RESULT_SCENARIO_LIST.value % f'{mqtt_client.get_client_id()}@{middleware.name}',
            auto_subscribe=True,
            auto_unsubscribe=False,
            timeout=timeout)

        topic, payload, _ = decode_MQTT_message(recv_msg)
        if recv_msg == SoPErrorType.TIMEOUT:
            SOPTEST_LOG_DEBUG(f'Get whole scenario info of {middleware.name} failed -> MQTT timeout...', SoPTestLogLevel.FAIL)
            return []

        scenario_info_list = [SoPScenarioInfo(id=scenario_info['id'],
                                              name=scenario_info['name'],
                                              state=SoPScenarioState.get(scenario_info['state']),
                                              code=scenario_info['contents'],
                                              schedule_info=scenario_info['scheduleInfo']) for scenario_info in payload['scenarios']]
        return scenario_info_list

    def get_whole_service_list_info(self, middleware: SoPMiddleware, timeout: float) -> List[SoPService]:
        mqtt_client = self.find_mqtt_client(middleware)
        recv_msg = self.publish_and_expect(
            middleware,
            encode_MQTT_message(SoPProtocolType.WebClient.EM_REFRESH.value % f'{mqtt_client.get_client_id()}@{middleware.name}', '{}'),
            SoPProtocolType.WebClient.ME_RESULT_SERVICE_LIST.value % f'{mqtt_client.get_client_id()}@{middleware.name}',
            auto_subscribe=True,
            auto_unsubscribe=False,
            timeout=timeout)

        topic, payload, _ = decode_MQTT_message(recv_msg)
        if recv_msg == SoPErrorType.TIMEOUT:
            SOPTEST_LOG_DEBUG(f'Get whole service list info of {middleware.name} failed -> MQTT timeout...', SoPTestLogLevel.FAIL)
            return []

        whole_service_info: List[SoPService] = []
        for service in payload['services']:
            if service['hierarchy'] == 'local' or service['hierarchy'] == 'parent':
                for thing in service['things']:
                    for service in thing['functions']:
                        service = SoPService(name=service['name'],
                                             is_super=thing['is_super'],
                                             tag_list=[tag['name'] for tag in service['tags']])
                        whole_service_info.append(service)
        return whole_service_info

    #### kill ##########################################################################################################################

    def get_proc_pid(self, ssh_client: SoPSSHClient, proc_name: str, port: int = None) -> Union[List[int], bool]:
        result: List[str] = ssh_client.send_command(f"lsof -i :{port} | grep {proc_name[:9]}")
        pid_list = list(set([line.split()[1] for line in result]))
        if len(pid_list) == 0:
            return False
        elif len(pid_list) == 1:
            return pid_list

    def get_component_proc_pid(self, ssh_client: SoPSSHClient, component: SoPComponent) -> List[int]:
        if isinstance(component, SoPMiddleware):
            middleware_pid_list = self.get_proc_pid(ssh_client, 'sopiot_middleware', component.mqtt_port)
            mosquitto_pid_list = self.get_proc_pid(ssh_client, 'mosquitto', component.mqtt_port)
            return dict(middleware_pid_list=middleware_pid_list, mosquitto_pid_list=mosquitto_pid_list)
        elif isinstance(component, SoPThing):
            middleware = self.find_parent_middleware(component)
            thing_pid_list = self.get_proc_pid(ssh_client, 'python', middleware.mqtt_port)
            return dict(thing_pid_list=thing_pid_list)

    def kill_all_middleware(self):
        SOPTEST_LOG_DEBUG(f'Kill all middleware...', SoPTestLogLevel.INFO, 'red')
        for middleware in self.middleware_list:
            ssh_client = self.find_ssh_client(middleware)
            ssh_client.send_command('pidof sopiot_middleware | xargs kill -9', force=True)
            ssh_client.send_command('pidof mosquitto | xargs kill -9', force=True)

    def kill_all_thing(self):
        SOPTEST_LOG_DEBUG(f'Kill all python instance...', SoPTestLogLevel.INFO, 'red')

        self_pid = os.getpid()
        for ssh_client in self.ssh_client_list:
            result = ssh_client.send_command(f"ps -ef | grep python | grep _thing_ | grep -v grep | awk '{{print $2}}'")

            for pid in result:
                if pid == self_pid:
                    continue
                result = ssh_client.send_command(f'kill -9 {pid}')

    def _kill_every_ssh_client(self):
        SOPTEST_LOG_DEBUG(f'Kill all ssh client...', SoPTestLogLevel.INFO, 'red')
        for ssh_client in self.ssh_client_list:
            ssh_client.disconnect()
            del ssh_client

    def _kill_every_mqtt_client(self):
        SOPTEST_LOG_DEBUG(f'Kill all mqtt client...', SoPTestLogLevel.INFO, 'red')
        for mqtt_client in self.mqtt_client_list:
            mqtt_client.stop()
            del mqtt_client

    def kill_every_process(self) -> bool:
        with Progress() as progress:
            task1 = progress.add_task("Clean up simulation processes...", total=len(self.middleware_list) + len(self.ssh_client_list))
            task2 = progress.add_task("Kill middleware processes...", total=len(self.middleware_list))
            if not self.middleware_debug:
                for middleware in self.middleware_list:
                    ssh_client = self.find_ssh_client(middleware)
                    ssh_client.send_command('pidof sopiot_middleware | xargs kill -9', force=True)
                    ssh_client.send_command('pidof mosquitto | xargs kill -9', force=True)
                    progress.update(task1, advance=1)
                    progress.update(task2, advance=1)

            self_pid = os.getpid()
            task3 = progress.add_task("Kill thing processes...", total=len(self.ssh_client_list))
            for ssh_client in self.ssh_client_list:
                result = ssh_client.send_command(f"ps -ef | grep python | grep _thing_ | grep -v grep | awk '{{print $2}}'")

                for pid in result:
                    if pid == self_pid:
                        continue
                    result = ssh_client.send_command(f'kill -9 {pid}', force=True)
                progress.update(task1, advance=1)
                progress.update(task3, advance=1)

        return True

    def wrapup(self):
        self.kill_every_process()
        self._kill_every_ssh_client()
        self._kill_every_mqtt_client()

    def remove_all_remote_simulation_file(self):
        finished_ssh_client_list = []
        for middleware in self.middleware_list:
            ssh_client = self.find_ssh_client(middleware)
            remote_home_dir = f'/home/{middleware.device.user}'
            if ssh_client in finished_ssh_client_list:
                continue
            ssh_client.send_command(f'rm -r {middleware.remote_middleware_config_path}')
            ssh_client.send_command(f'rm -r {middleware.remote_middleware_config_path}')
            ssh_client.send_command(f'rm -r {remote_home_dir}/simulation_log')
            finished_ssh_client_list.append(ssh_client)

        finished_ssh_client_list = []
        for thing in self.thing_list:
            ssh_client = self.find_ssh_client(thing)
            if ssh_client in finished_ssh_client_list:
                continue
            ssh_client.send_command(f'rm -r {os.path.dirname(thing.remote_thing_file_path)}')
            ssh_client.send_command(f'rm -r {os.path.dirname(os.path.dirname(thing.remote_thing_file_path))}')
            finished_ssh_client_list.append(ssh_client)

    #### expect ##########################################################################################################################

    def expect(self, component: Union[SoPMiddleware, SoPThing, SoPScenario], target_topic: str, timeout: int = 5) -> Union[mqtt.MQTTMessage, SoPErrorType]:
        if not self.event_listener_thread.is_alive():
            raise RuntimeError('Event listener thread is not alive')

        cur_time = get_current_time()
        target_protocol = SoPProtocolType.get(target_topic)

        while get_current_time() - cur_time < timeout:
            if not target_protocol in component.recv_msg_table:
                time.sleep(BUSY_WAIT_TIMEOUT)
                continue

            recv_msg = hash_pop(component.recv_msg_table, key=target_protocol)
            topic, _, _ = decode_MQTT_message(recv_msg)
            if mqtt.topic_matches_sub(target_topic, topic):
                return recv_msg
            else:
                SOPTEST_LOG_DEBUG(f'Topic match failed... Expect {target_topic} but receive {topic}', SoPTestLogLevel.WARN)
                return None
        else:
            return SoPErrorType.TIMEOUT

    def publish_and_expect(self, component: SoPComponent, trigger_msg: mqtt.MQTTMessage = None, target_topic: str = None,
                           auto_subscribe: bool = True, auto_unsubscribe: bool = False, timeout: int = 5) -> Union[mqtt.MQTTMessage, SoPErrorType]:
        if isinstance(component, SoPMiddleware):
            target_middleware = component
        elif isinstance(component, (SoPThing, SoPScenario)):
            target_middleware = self.find_parent_middleware(component)
        else:
            raise TypeError(f'Invalid component type: {type(component)}')

        mqtt_client = self.find_mqtt_client(target_middleware)
        if not mqtt_client.is_run:
            raise RuntimeError(f'MQTT Client is not running')

        if auto_subscribe:
            mqtt_client.subscribe(target_topic)

        trigger_topic, trigger_payload, _ = decode_MQTT_message(trigger_msg, mode=str)
        mqtt_client.publish(trigger_topic, trigger_payload, retain=False)
        ret = self.expect(component, target_topic, timeout)

        if auto_unsubscribe:
            mqtt_client.unsubscribe(target_topic)

        return ret

    def command_and_expect(self, component: SoPComponent, trigger_command: Union[List[str], str] = None, target_topic: str = None,
                           auto_subscribe: bool = True, auto_unsubscribe: bool = False, timeout: int = 5) -> Union[mqtt.MQTTMessage, SoPErrorType]:
        if isinstance(component, SoPMiddleware):
            target_middleware = component
        elif isinstance(component, (SoPThing, SoPScenario)):
            target_middleware = self.find_parent_middleware(component)
        else:
            raise TypeError(f'Invalid component type: {type(component)}')

        mqtt_client = self.find_mqtt_client(target_middleware)
        ssh_client = self.find_ssh_client(target_middleware)
        if not mqtt_client.is_run:
            raise RuntimeError(f'MQTT Client is not running')
        if not ssh_client.connected:
            raise RuntimeError(f'SSH Client is not connected')

        if auto_subscribe:
            mqtt_client.subscribe(target_topic)

        if isinstance(trigger_command, list):
            for command in trigger_command:
                ssh_client.send_command(command)
        else:
            ssh_client.send_command(trigger_command)
        ret = self.expect(component, target_topic, timeout)

        if auto_unsubscribe:
            mqtt_client.unsubscribe(target_topic)

        return ret

    def check_middleware_online(self, thing: SoPThing) -> bool:
        middleware = self.find_parent_middleware(thing)
        if middleware:
            return middleware.online
        else:
            return True

    #### on_recv_message ##########################################################################################################################

    def _on_recv_message(self, msg: mqtt.MQTTMessage):
        topic, payload, _ = decode_MQTT_message(msg)
        timestamp = get_current_time() - self.simulation_start_time

        protocol = SoPProtocolType.get(topic)
        return_type = SoPType.get(payload.get('return_type', None))
        return_value = payload.get('return_value', None)
        error = SoPErrorType.get(payload.get('error', None))
        scenario_name = payload.get('name', None) if payload.get('name', None) != None else payload.get('scenario', None)
        topic_slice = topic.split('/')

        if protocol in [SoPProtocolType.WebClient.ME_RESULT_SCENARIO_LIST, SoPProtocolType.WebClient.ME_RESULT_SERVICE_LIST]:
            client_id = topic_slice[3]
            middleware_name = client_id.split('@')[1]
            middleware = self.find_middleware(middleware_name)
            hash_insert(middleware.recv_msg_table, data=(protocol, msg))
        elif protocol == SoPProtocolType.Base.TM_REGISTER:
            thing_name = topic_slice[2]
            thing = self.find_thing(thing_name)
            hash_insert(thing.recv_msg_table, data=(protocol, msg))
            self.event_log.append(SoPEvent(event_type=SoPEventType.THING_REGISTER, middleware_component=thing.middleware, thing_component=thing, timestamp=timestamp, duration=0))
        elif SoPProtocolType.Base.MT_RESULT_REGISTER.get_prefix() in topic:
            thing_name = topic_slice[3]
            thing = self.find_thing(thing_name)
            hash_insert(thing.recv_msg_table, data=(protocol, msg))
            for event in list(reversed(self.event_log)):
                if not (event.middleware_component == thing.middleware and event.thing_component == thing and event.event_type == SoPEventType.THING_REGISTER):
                    continue
                event.duration = timestamp - event.timestamp
                event.error = error
                break
        elif SoPProtocolType.Base.TM_UNREGISTER.get_prefix() in topic:
            thing_name = topic_slice[2]
            thing = self.find_thing(thing_name)
            hash_insert(thing.recv_msg_table, data=(protocol, msg))
            self.event_log.append(SoPEvent(event_type=SoPEventType.THING_UNREGISTER, middleware_component=thing.middleware, thing_component=thing, timestamp=timestamp, duration=0))
        elif SoPProtocolType.Base.MT_RESULT_UNREGISTER.get_prefix() in topic:
            thing_name = topic_slice[3]
            thing = self.find_thing(thing_name)
            hash_insert(thing.recv_msg_table, data=(protocol, msg))
            for event in list(reversed(self.event_log)):
                if not (event.middleware_component == thing.middleware and event.thing_component == thing and event.event_type == SoPEventType.THING_UNREGISTER):
                    continue
                event.duration = timestamp - event.timestamp
                event.error = error
                SOPTEST_LOG_DEBUG(f'[UNREGISTER] thing: {thing_name} duration: {event.duration:0.4f}', SoPTestLogLevel.INFO)
                break
        elif SoPProtocolType.Base.MT_EXECUTE.get_prefix() in topic:
            function_name = topic_slice[2]
            thing_name = topic_slice[3]
            thing = self.find_thing(thing_name)
            scenario = self.find_scenario(scenario_name)
            service = thing.find_service_by_name(function_name)

            if len(topic_slice) > 4:
                request_ID = topic_slice[5]
                requester_middleware_name = request_ID.split('@')[0]
                super_thing_name = request_ID.split('@')[1]
                super_function_name = request_ID.split('@')[2]
                # sub_service_request_order = request_ID.split('@')[3]
            else:
                super_thing_name = None
                super_function_name = None
                requester_middleware_name = None

            if requester_middleware_name is not None:
                event_type = SoPEventType.SUB_FUNCTION_EXECUTE
            else:
                event_type = SoPEventType.FUNCTION_EXECUTE

            self.event_log.append(SoPEvent(event_type=event_type, middleware_component=thing.middleware, thing_component=thing, service_component=service,
                                           scenario_component=scenario, timestamp=timestamp, duration=0, requester_middleware_name=requester_middleware_name,
                                           super_thing_name=super_thing_name, super_function_name=super_function_name))
        elif SoPProtocolType.Base.TM_RESULT_EXECUTE.get_prefix() in topic:
            function_name = topic_slice[3]
            thing_name = topic_slice[4]
            thing = self.find_thing(thing_name)
            scenario = self.find_scenario(scenario_name)
            service = thing.find_service_by_name(function_name)

            if len(topic_slice) > 5:
                # middleware_name = topic_slice[5]
                request_ID = topic_slice[6]

                requester_middleware_name = request_ID.split('@')[0]
                super_thing_name = request_ID.split('@')[1]
                super_function_name = request_ID.split('@')[2]
                # sub_service_request_order = request_ID.split('@')[3]
            else:
                super_thing_name = None
                super_function_name = None
                requester_middleware_name = None

            for event in list(reversed(self.event_log)):
                if event.middleware_component == thing.middleware and event.thing_component == thing and event.service_component == service and event.scenario_component == scenario and event.requester_middleware_name == requester_middleware_name and event.event_type in [SoPEventType.FUNCTION_EXECUTE, SoPEventType.SUB_FUNCTION_EXECUTE]:
                    event.duration = timestamp - event.timestamp
                    event.error = error
                    event.return_type = return_type
                    event.return_value = return_value
                    event.requester_middleware_name = requester_middleware_name

                    passed_time = get_current_time() - self.simulation_start_time
                    progress = passed_time / self.running_time

                    if event.event_type == SoPEventType.SUB_FUNCTION_EXECUTE:
                        color = 'light_magenta' if event.error == SoPErrorType.FAIL else 'light_cyan'
                        SOPTEST_LOG_DEBUG(f'[EXECUTE_SUB] thing: {thing_name} function: {function_name} scenario: {scenario_name} '
                                          f'requester_middleware_name: {requester_middleware_name} duration: {event.duration:0.4f} '
                                          f'return value: {return_value} - {return_type.value} error:{event.error.value}', SoPTestLogLevel.PASS, progress=progress, color=color)
                    elif event.event_type == SoPEventType.FUNCTION_EXECUTE:
                        color = 'red' if event.error == SoPErrorType.FAIL else 'green'
                        SOPTEST_LOG_DEBUG(f'[EXECUTE] thing: {thing_name} function: {function_name} scenario: {scenario_name} '
                                          f'requester_middleware_name: {requester_middleware_name} duration: {event.duration:0.4f} '
                                          f'return value: {return_value} - {return_type.value} error:{event.error.value}', SoPTestLogLevel.PASS, progress=progress, color=color)
                    break
        elif SoPProtocolType.WebClient.EM_VERIFY_SCENARIO.get_prefix() in topic:
            scenario = self.find_scenario(scenario_name)
            self.event_log.append(SoPEvent(event_type=SoPEventType.SCENARIO_VERIFY, middleware_component=scenario.middleware, scenario_component=scenario, timestamp=timestamp, duration=0))
        elif SoPProtocolType.WebClient.ME_RESULT_VERIFY_SCENARIO.get_prefix() in topic:
            scenario = self.find_scenario(scenario_name)
            hash_insert(scenario.recv_msg_table, data=(protocol, msg))
            for event in list(reversed(self.event_log)):
                if not (event.middleware_component == scenario.middleware and event.scenario_component == scenario and event.event_type == SoPEventType.SCENARIO_VERIFY):
                    continue
                event.duration = timestamp - event.timestamp
                event.error = error
                SOPTEST_LOG_DEBUG(f'[SCENE_VERIFY] scenario: {scenario_name} duration: {event.duration:0.4f}', SoPTestLogLevel.INFO)
                break
        elif SoPProtocolType.WebClient.EM_ADD_SCENARIO.get_prefix() in topic:
            scenario = self.find_scenario(scenario_name)
            self.event_log.append(SoPEvent(event_type=SoPEventType.SCENARIO_ADD, middleware_component=scenario.middleware, scenario_component=scenario, timestamp=timestamp, duration=0))
        elif SoPProtocolType.WebClient.ME_RESULT_ADD_SCENARIO.get_prefix() in topic:
            scenario = self.find_scenario(scenario_name)
            hash_insert(scenario.recv_msg_table, data=(protocol, msg))
            for event in list(reversed(self.event_log)):
                if not (event.middleware_component == scenario.middleware and event.scenario_component == scenario and event.event_type == SoPEventType.SCENARIO_ADD):
                    continue
                event.duration = timestamp - event.timestamp
                event.error = error
                break
        elif SoPProtocolType.WebClient.EM_RUN_SCENARIO.get_prefix() in topic:
            scenario = self.find_scenario(scenario_name)
            self.event_log.append(SoPEvent(event_type=SoPEventType.SCENARIO_RUN, middleware_component=scenario.middleware, scenario_component=scenario, timestamp=timestamp, duration=0))
        elif SoPProtocolType.WebClient.ME_RESULT_RUN_SCENARIO.get_prefix() in topic:
            scenario = self.find_scenario(scenario_name)
            hash_insert(scenario.recv_msg_table, data=(protocol, msg))
            for event in list(reversed(self.event_log)):
                if not (event.middleware_component == scenario.middleware and event.scenario_component == scenario and event.event_type == SoPEventType.SCENARIO_RUN):
                    continue
                event.duration = timestamp - event.timestamp
                event.error = error
                SOPTEST_LOG_DEBUG(f'[SCENE_RUN] scenario: {scenario_name} duration: {event.duration:0.4f}', SoPTestLogLevel.INFO)
                break
        elif SoPProtocolType.WebClient.EM_STOP_SCENARIO.get_prefix() in topic:
            scenario = self.find_scenario(scenario_name)
            self.event_log.append(SoPEvent(event_type=SoPEventType.SCENARIO_STOP, middleware_component=scenario.middleware, scenario_component=scenario, timestamp=timestamp, duration=0))
        elif SoPProtocolType.WebClient.ME_RESULT_STOP_SCENARIO.get_prefix() in topic:
            scenario = self.find_scenario(scenario_name)
            hash_insert(scenario.recv_msg_table, data=(protocol, msg))
            for event in list(reversed(self.event_log)):
                if not (event.middleware_component == scenario.middleware and event.scenario_component == scenario and event.event_type == SoPEventType.SCENARIO_STOP):
                    continue
                event.duration = timestamp - event.timestamp
                event.error = error
                SOPTEST_LOG_DEBUG(f'[SCENE_STOP] scenario: {scenario_name} duration: {event.duration:0.4f}', SoPTestLogLevel.INFO)
                break
        elif SoPProtocolType.WebClient.EM_UPDATE_SCENARIO.get_prefix() in topic:
            scenario = self.find_scenario(scenario_name)
            self.event_log.append(SoPEvent(event_type=SoPEventType.SCENARIO_UPDATE, middleware_component=scenario.middleware, scenario_component=scenario, timestamp=timestamp, duration=0))
        elif SoPProtocolType.WebClient.ME_RESULT_UPDATE_SCENARIO.get_prefix() in topic:
            scenario = self.find_scenario(scenario_name)
            hash_insert(scenario.recv_msg_table, data=(protocol, msg))
            for event in list(reversed(self.event_log)):
                if not (event.middleware_component == scenario.middleware and event.scenario_component == scenario and event.event_type == SoPEventType.SCENARIO_UPDATE):
                    continue
                event.duration = timestamp - event.timestamp
                event.error = error
                SOPTEST_LOG_DEBUG(f'[SCENE_UPDATE] scenario: {scenario_name} duration: {event.duration:0.4f}', SoPTestLogLevel.INFO)
                break
        elif SoPProtocolType.WebClient.EM_DELETE_SCENARIO.get_prefix() in topic:
            scenario = self.find_scenario(scenario_name)
            self.event_log.append(SoPEvent(event_type=SoPEventType.SCENARIO_DELETE, middleware_component=scenario.middleware, scenario_component=scenario, timestamp=timestamp, duration=0))
        elif SoPProtocolType.WebClient.ME_RESULT_DELETE_SCENARIO.get_prefix() in topic:
            scenario = self.find_scenario(scenario_name)
            hash_insert(scenario.recv_msg_table, data=(protocol, msg))
            for event in list(reversed(self.event_log)):
                if not (event.middleware_component == scenario.middleware and event.scenario_component == scenario and event.event_type == SoPEventType.SCENARIO_DELETE):
                    continue
                event.duration = timestamp - event.timestamp
                event.error = error
                SOPTEST_LOG_DEBUG(f'[SCENE_DELETE] scenario: {scenario_name} duration: {event.duration:0.4f}', SoPTestLogLevel.INFO)
                break

        ####################################################################################################################################################

        elif SoPProtocolType.Super.MS_SCHEDULE.get_prefix() in topic:
            requester_middleware_name = topic_slice[5]
            super_middleware_name = topic_slice[4]
            super_thing_name = topic_slice[3]
            super_function_name = topic_slice[2]

            super_thing = self.find_thing(super_thing_name)
            scenario = self.find_scenario(scenario_name)
            super_service = super_thing.find_service_by_name(super_function_name)

            self.event_log.append(SoPEvent(event_type=SoPEventType.SUPER_SCHEDULE, middleware_component=super_thing.middleware, thing_component=super_thing,
                                           service_component=super_service, scenario_component=scenario, timestamp=timestamp, duration=0))
            SOPTEST_LOG_DEBUG(f'[SUPER_SCHEDULE_START] super_middleware: {super_middleware_name} requester_middleware: {requester_middleware_name} '
                              f'super_thing: {super_thing_name} super_function: {super_function_name} scenario: {scenario_name}', SoPTestLogLevel.INFO)
        elif SoPProtocolType.Super.SM_SCHEDULE.get_prefix() in topic:
            target_middleware_name = topic_slice[4]
            target_thing_name = topic_slice[3]
            target_function_name = topic_slice[2]

            request_ID = topic_slice[5]
            requester_middleware_name = request_ID.split('@')[0]
            super_thing_name = request_ID.split('@')[1]
            super_function_name = request_ID.split('@')[2]

            scenario = self.find_scenario(scenario_name)

            progress = [scenario.add_result_arrived for scenario in self.scenario_list].count(True) / len(self.scenario_list)
            color = 'light_magenta'
            SOPTEST_LOG_DEBUG(f'[SUB_SCHEDULE_START] super_middleware: {""} requester_middleware: {requester_middleware_name} super_thing: {super_thing_name} '
                              f'super_function: {super_function_name} target_middleware: {target_middleware_name} target_thing: {target_thing_name} '
                              f'target_function: {target_function_name} scenario: {scenario_name}', SoPTestLogLevel.INFO, progress=progress, color=color)
        elif SoPProtocolType.Super.MS_RESULT_SCHEDULE.get_prefix() in topic:
            target_middleware_name = topic_slice[5]
            target_thing_name = topic_slice[4]
            target_function_name = topic_slice[3]

            request_ID = topic_slice[6]
            requester_middleware_name = request_ID.split('@')[0]
            super_thing_name = request_ID.split('@')[1]
            super_function_name = request_ID.split('@')[2]

            scenario = self.find_scenario(scenario_name)

            progress = [scenario.add_result_arrived for scenario in self.scenario_list].count(True) / len(self.scenario_list)
            color = 'light_magenta'
            SOPTEST_LOG_DEBUG(f'[SUB_SCHEDULE_END] super_middleware: {""} requester_middleware: {requester_middleware_name} super_thing: {super_thing_name} '
                              f'super_function: {super_function_name} target_middleware: {target_middleware_name} target_thing: {target_thing_name} '
                              f'target_function: {target_function_name} scenario: {scenario_name}', SoPTestLogLevel.INFO, progress=progress, color=color)
        elif SoPProtocolType.Super.SM_RESULT_SCHEDULE.get_prefix() in topic:
            requester_middleware_name = topic_slice[6]
            super_middleware_name = topic_slice[5]
            super_thing_name = topic_slice[4]
            super_function_name = topic_slice[3]

            super_thing = self.find_thing(super_thing_name)
            scenario = self.find_scenario(scenario_name)
            super_service = super_thing.find_service_by_name(super_function_name)
            hash_insert(scenario.recv_msg_table, data=(protocol, msg))

            for event in list(reversed(self.event_log)):
                if not (event.middleware_component == super_thing.middleware and event.thing_component == super_thing and event.service_component == super_service
                        and event.scenario_component == scenario and event.event_type == SoPEventType.SUPER_SCHEDULE):
                    continue
                event.duration = timestamp - event.timestamp
                event.error = error
                event.return_type = return_type
                event.return_value = return_value

                progress = [scenario.add_result_arrived for scenario in self.scenario_list].count(True) / len(self.scenario_list)
                SOPTEST_LOG_DEBUG(f'[SUPER_SCHEDULE_END] super_middleware: {super_middleware_name} requester_middleware: {requester_middleware_name} '
                                  f'super_thing: {super_thing_name} super_function: {super_function_name} scenario: {scenario_name} duration: {event.duration:0.4f} '
                                  f'result: {event.error.value}', SoPTestLogLevel.INFO, progress=progress)
                break
        elif SoPProtocolType.Super.MS_EXECUTE.get_prefix() in topic:
            super_function_name = topic_slice[2]
            super_thing_name = topic_slice[3]
            super_middleware_name = topic_slice[4]
            requester_middleware_name = topic_slice[5]

            super_thing = self.find_thing(super_thing_name)
            scenario = self.find_scenario(scenario_name)
            super_service = super_thing.find_service_by_name(super_function_name)

            # NOTE: Super service가 감지되면 각 subfunction의 energy를 0으로 초기화한다.
            # 이렇게 하는 이유는 super service가 실행될 때 마다 다른 subfunction이 실행될 수 있고
            # 이에 따라 다른 energy 소모량을 가질 수 있다.
            # for subfunction in super_service.subfunction_list:
            #     subfunction.energy = 0

            self.event_log.append(SoPEvent(event_type=SoPEventType.SUPER_FUNCTION_EXECUTE, middleware_component=super_thing.middleware, thing_component=super_thing,
                                           service_component=super_service, scenario_component=scenario, timestamp=timestamp, duration=0))
            passed_time = get_current_time() - self.simulation_start_time
            progress = passed_time / self.running_time
            SOPTEST_LOG_DEBUG(f'[SUPER_EXECUTE_START] super_middleware: {super_middleware_name} requester_middleware: {requester_middleware_name} super_thing: {super_thing_name} '
                              f'super_function: {super_function_name} scenario: {scenario_name}', SoPTestLogLevel.INFO, progress=progress)
        elif SoPProtocolType.Super.SM_EXECUTE.get_prefix() in topic:
            target_middleware_name = topic_slice[4]
            target_thing_name = topic_slice[3]
            target_function_name = topic_slice[2]

            request_ID = topic_slice[5]
            requester_middleware_name = request_ID.split('@')[0]
            super_thing_name = request_ID.split('@')[1]
            super_function_name = request_ID.split('@')[2]

            scenario = self.find_scenario(scenario_name)

            passed_time = get_current_time() - self.simulation_start_time
            progress = passed_time / self.running_time
            color = 'light_magenta'
            SOPTEST_LOG_DEBUG(f'[SUB_EXECUTE_START] super_middleware: {""} requester_middleware: {requester_middleware_name} super_thing: {super_thing_name} '
                              f'super_function: {super_function_name} target_middleware: {target_middleware_name} target_thing: {target_thing_name} '
                              f'target_function: {target_function_name} scenario: {scenario_name}', SoPTestLogLevel.INFO, progress=progress, color=color)
        elif SoPProtocolType.Super.MS_RESULT_EXECUTE.get_prefix() in topic:
            target_middleware_name = topic_slice[5]
            target_thing_name = topic_slice[4]
            target_function_name = topic_slice[3]

            request_ID = topic_slice[6]
            requester_middleware_name = request_ID.split('@')[0]
            super_thing_name = request_ID.split('@')[1]
            super_function_name = request_ID.split('@')[2]

            scenario = self.find_scenario(scenario_name)

            passed_time = get_current_time() - self.simulation_start_time
            progress = passed_time / self.running_time
            color = 'light_magenta'
            SOPTEST_LOG_DEBUG(f'[SUB_EXECUTE_END] super_middleware: {""} requester_middleware: {requester_middleware_name} super_thing: {super_thing_name} '
                              f'super_function: {super_function_name} target_middleware: {target_middleware_name} target_thing: {target_thing_name} '
                              f'target_function: {target_function_name} scenario: {scenario_name}', SoPTestLogLevel.INFO, progress=progress, color=color)
        elif SoPProtocolType.Super.SM_RESULT_EXECUTE.get_prefix() in topic:
            requester_middleware_name = topic_slice[6]
            super_middleware_name = topic_slice[5]
            super_thing_name = topic_slice[4]
            super_function_name = topic_slice[3]

            super_thing = self.find_thing(super_thing_name)
            scenario = self.find_scenario(scenario_name)
            super_service = super_thing.find_service_by_name(super_function_name)

            for event in list(reversed(self.event_log)):
                if not (event.event_type == SoPEventType.SUPER_FUNCTION_EXECUTE and event.middleware_component == super_thing.middleware and event.thing_component == super_thing
                        and event.service_component == super_service and event.scenario_component == scenario):
                    continue
                event.duration = timestamp - event.timestamp
                event.error = error
                event.return_type = return_type
                event.return_value = return_value

                passed_time = get_current_time() - self.simulation_start_time
                progress = passed_time / self.running_time
                SOPTEST_LOG_DEBUG(f'[SUPER_EXECUTE_END] super_middleware: {super_middleware_name} requester_middleware: {requester_middleware_name} '
                                  f'super_thing: {super_thing_name} super_function: {super_function_name} scenario: {scenario_name} duration: {event.duration:0.4f} '
                                  f'return value: {return_value} - {return_type.value} error:{event.error.value}', SoPTestLogLevel.INFO, progress=progress)
                break
        elif 'SIM/FINISH' in topic:
            scenario = self.find_scenario(scenario_name)
            scenario.cycle_count += 1
            # SOPTEST_LOG_DEBUG(f'[SIM_FINISH] scenario: {scenario.name}, cycle_count: {scenario.cycle_count}', SoPTestLogLevel.WARN)
            return True
        else:
            raise Exception(f'Unknown topic: {topic}')

        # elif SoPProtocolType.Default.TM_VALUE_PUBLISH.get_prefix() in topic:
        #     pass
        # elif SoPProtocolType.Default.TM_VALUE_PUBLISH_OLD.get_prefix() in topic:
        #     pass

    # =========================
    #         _    _  _
    #        | |  (_)| |
    #  _   _ | |_  _ | | ___
    # | | | || __|| || |/ __|
    # | |_| || |_ | || |\__ \
    #  \__,_| \__||_||_||___/
    # =========================

    def _check_result_payload(self, payload: dict = None):
        if not payload:
            SOPTEST_LOG_DEBUG(f'Payload is None (timeout)!!!', SoPTestLogLevel.FAIL)
            return None

        error_code = payload['error']
        error_string = payload.get('error_string', None)

        if error_code in [0, -4]:
            return True
        else:
            SOPTEST_LOG_DEBUG(f'error_code: {error_code}, error_string : {error_string if error_string else "(No error string)"}', SoPTestLogLevel.FAIL)
            return False

    def _get_device_list(self) -> List[SoPDevice]:
        duplicated_device_list: List[SoPDevice] = [middleware.device for middleware in self.middleware_list] + [thing.device for thing in self.thing_list]
        device_list: List[SoPDevice] = []

        for device in duplicated_device_list:
            if device in device_list:
                continue
            device_list.append(device)

        return device_list

    def find_ssh_client(self, component: Union[SoPMiddleware, SoPThing]) -> SoPSSHClient:
        for ssh_client in self.ssh_client_list:
            if ssh_client.device == component.device:
                return ssh_client
        else:
            return None

    def find_mqtt_client(self, middleware: SoPMiddleware) -> SoPMQTTClient:
        for mqtt_client in self.mqtt_client_list:
            if mqtt_client.middleware == middleware:
                return mqtt_client
        else:
            return None

    def find_middleware(self, target_middleware_name: str) -> SoPMiddleware:
        for middleware in self.middleware_list:
            if middleware.name == target_middleware_name:
                return middleware
        else:
            return None

    def find_scenario(self, target_scenario_name: str) -> SoPScenario:
        for scenario in self.scenario_list:
            if scenario.name == target_scenario_name:
                return scenario
        else:
            return None

    def find_thing(self, target_thing_name: str) -> SoPThing:
        for thing in self.thing_list:
            if thing.name == target_thing_name:
                return thing
        else:
            return None

    def find_service(self, target_service_name: str) -> SoPService:
        for thing in self.thing_list:
            for service in thing.service_list:
                if service.name == target_service_name:
                    return service
        else:
            return None

    def find_parent_middleware(self, component: Union[SoPMiddleware, SoPScenario, SoPThing, SoPService]) -> SoPMiddleware:
        if isinstance(component, SoPMiddleware):
            return component.parent
        elif isinstance(component, SoPScenario):
            return component.middleware
        elif isinstance(component, SoPThing):
            return component.middleware
        elif isinstance(component, SoPService):
            return component.thing.middleware
        else:
            return None
