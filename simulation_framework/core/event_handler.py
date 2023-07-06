
from simulation_framework.core.components import *
from simulation_framework.config import *
from simulation_framework.ssh_client import *
from simulation_framework.mqtt_client import *
from tqdm import tqdm
from rich.progress import track, Progress, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn, TaskID

from big_thing_py.common.mxtype import MXProtocolType, MXType
from big_thing_py.common.error import MXErrorCode
from big_thing_py.common.thread import MXThread, Event, Empty


class MXSimulationEnv:
    def __init__(self, config: MXSimulationConfig, root_middleware: MXMiddleware = None,
                 static_event_timeline: List['MXEvent'] = [], dynamic_event_timeline: List['MXEvent'] = [],
                 service_pool: List[MXService] = [], thing_pool: List[MXThing] = [],
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


class MXEventType(Enum):
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

    MIDDLEWARE_CHECK = 'MIDDLEWARE_CHECK'                               # 모든 Middleware가 online 상태일 때까지 기다리는 이벤트.
    THING_CHECK = 'THING_CHECK'                                         # 모든 Thing이 online 상태일 때까지 기다리는 이벤트.
    SCENARIO_ADD_CHECK = 'SCENARIO_ADD_CHECK'                           # 모든 Scenario가 추가 완료될 때까지 기다리는 이벤트.
    SCENARIO_STATE_CHECK = 'SCENARIO_STATE_CHECK'                       # 모든 Scenario의 상태가 타겟 state가 될 때까지 기다리는 이벤트.

    UNDEFINED = 'UNDEFINED'

    def __str__(self):
        return self.value

    @classmethod
    def get(cls, name: str):
        try:
            return cls[name.upper()]
        except Exception:
            return cls.UNDEFINED


class MXEvent:

    def __init__(self, event_type: MXEventType, component: 'MXComponent' = None, middleware_component: 'MXMiddleware' = None, thing_component: 'MXThing' = None, service_component: 'MXService' = None, scenario_component: 'MXScenario' = None,
                 timestamp: float = 0, duration: float = None, delay: float = None,
                 error: MXErrorCode = None, return_type: MXType = None, return_value: ReturnType = None,
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
        self.event_type = MXEventType.get(data['event_type']) if data['event_type'] is str else data['event_type']
        self.component = MXComponent.load(data['component'])
        self.middleware_component = MXComponent.load(data['middleware_component'])
        self.thing_component = MXComponent.load(data['thing_component'])
        self.service_component = MXComponent.load(data['service_component'])
        self.scenario_component = MXComponent.load(data['scenario_component'])
        self.timestamp = data['timestamp']
        self.duration = data['duration']
        self.delay = data['delay']
        self.error = MXErrorCode.get(data['error']) if data['error'] is str else data['error']
        self.return_type = MXType.get(data['return_type']) if data['return_type'] is str else data['return_type']
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


class MXEventHandler:

    def __init__(self, root_middleware: MXMiddleware = None, timeout: float = 5.0, running_time: float = None, download_logs: bool = False,
                 mqtt_debug: bool = False, middleware_debug: bool = False) -> None:
        self.root_middleware = root_middleware
        self.middleware_list: List[MXMiddleware] = get_whole_middleware_list(self.root_middleware)
        self.thing_list: List[MXThing] = get_whole_thing_list(self.root_middleware)
        self.scenario_list: List[MXScenario] = get_whole_scenario_list(self.root_middleware)

        self.mqtt_client_list: List[MXMQTTClient] = []
        self.ssh_client_list: List[MXSSHClient] = []

        self.event_listener_event = Event()
        # self.event_listener_lock = Lock()
        self.event_listener_thread = MXThread(name='event_listener', target=self._event_listener, args=(self.event_listener_event, ))

        # simulator와 같은 인스턴스를 공유한다.
        self.simulation_start_time = 0
        # self.simulation_duration = 0
        self.event_log: List[MXEvent] = []
        self.timeout = timeout
        self.running_time = running_time

        self.mqtt_debug = mqtt_debug
        self.middleware_debug = middleware_debug

        self.download_logs = download_logs

        self.download_log_file_thread_queue = Queue()

        # progress bar
        self.simulation_progress = Progress()
        self.static_event_running_task: TaskID = None
        self.middleware_run_task: TaskID = None
        self.thing_run_task: TaskID = None
        self.scenario_add_task: TaskID = None
        self.scenario_init_check_task: TaskID = None

        self.schedule_running_task: TaskID = None
        self.execute_running_task: TaskID = None

    def _add_mqtt_client(self, mqtt_client: MXMQTTClient):
        self.mqtt_client_list.append(mqtt_client)

    def _add_ssh_client(self, ssh_client: MXSSHClient):
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
        # When middleware has the same device, shares the MXDeviceComponent instance.
        device_list = self._get_device_list()
        for middleware in self.middleware_list:
            for device in device_list:
                if device == middleware.device:
                    middleware.device = device

    def init_ssh_client_list(self) -> bool:
        with Progress() as progress:
            def task(device: MXDevice):
                ssh_client = MXSSHClient(device)
                ssh_client.connect(use_ssh_config=False)

                # 따로 명세되어있지 않고 local network에 있는 경우 사용 가능한 port를 찾는다.
                if device.mqtt_port:
                    device.available_port_list = []
                else:
                    if '192.168' in device.host or device.host == 'localhost':
                        device.available_port_list = ssh_client.available_port()
                    else:
                        raise Exception(f'mqtt_port of {device.name} is not specified.')

                self._add_ssh_client(ssh_client)
                progress.update(task1, advance=1)

            device_list = self._get_device_list()
            task1 = progress.add_task(description='Init SSH client', total=len(device_list))
            pool_map(task, device_list)

        return True

    # 로컬 네트워크에 있으면 기본적으로 사용 가능한 포트를 검색한다.
    # TODO: 만약 로컬 네트워크이고 mqtt 포트가 명세되어있는 경우 사용 가능한 포트에 명세한 mqtt 포트가 있는지 확인만하고 해당 포트를 mqtt 포트로 사용한다.
    # 로컬 서버 포트는 어떻게 할 것인지 고민해야한다. -> 같은 로컬 서버 포트를 사용하면 반복해서 미들웨어를 구동할 때 bind 에러가 발생한다...
    def init_mqtt_client_list(self):
        with Progress() as progress:
            def task(middleware: MXMiddleware):
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

                mqtt_client = MXMQTTClient(middleware, debug=self.mqtt_debug)
                self._add_mqtt_client(mqtt_client)
                progress.update(task1, advance=1)

            task1 = progress.add_task(description='Init MQTT client', total=len(self.middleware_list))
            pool_map(task, self.middleware_list)

        return True

    def download_log_file(self) -> str:

        def task(middleware: MXMiddleware):
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

    def event_trigger(self, event: MXEvent):
        # wait until timestamp is reached
        if event.timestamp == None:
            raise Exception('timestamp is not defined')
        while get_current_time() - self.simulation_start_time < event.timestamp:
            time.sleep(BUSY_WAIT_TIMEOUT)

        if event.event_type == MXEventType.DELAY:
            # MXTEST_LOG_DEBUG(f'Delay {event.delay} Sec start...', MXTestLogLevel.INFO, 'yellow')
            self.simulation_progress
            self.event_log.append(event)
            time.sleep(event.delay)
        elif event.event_type == MXEventType.START:
            cur_time = get_current_time()
            event.timestamp = cur_time
            self.simulation_start_time = cur_time

            MXTEST_LOG_DEBUG(f'Simulation Start', MXTestLogLevel.PASS, 'yellow')
        elif event.event_type == MXEventType.END:
            event.timestamp = get_current_time() - self.simulation_start_time
            MXTEST_LOG_DEBUG(f'Simulation End. duration: {event.timestamp:8.3f} sec', MXTestLogLevel.PASS, 'yellow')

            # check which scenario is stucked
            self.scenario_state_check(target_state=[MXScenarioState.INITIALIZED,
                                                    MXScenarioState.RUNNING,
                                                    MXScenarioState.EXECUTING], check_interval=3, retry=5, timeout=self.timeout)
            self.stop_event_listener()
            self.kill_every_process()

            return True
        else:
            target_component = event.component
            # async event
            if event.event_type == MXEventType.MIDDLEWARE_RUN:
                MXThread(name=f'{event.event_type.value}_{event.component.name}', target=self.run_middleware, args=(target_component, 10, )).start()
            elif event.event_type == MXEventType.MIDDLEWARE_KILL:
                MXThread(name=f'{event.event_type.value}_{event.component.name}', target=self.kill_middleware, args=(target_component, )).start()
            elif event.event_type == MXEventType.THING_RUN:
                MXThread(name=f'{event.event_type.value}_{event.component.name}', target=self.run_thing, args=(target_component, 30, )).start()
            elif event.event_type == MXEventType.THING_KILL:
                MXThread(name=f'{event.event_type.value}_{event.component.name}', target=self.kill_thing, args=(target_component, )).start()
            elif event.event_type == MXEventType.THING_UNREGISTER:
                MXThread(name=f'{event.event_type.value}_{event.component.name}', target=self.unregister_thing, args=(target_component, )).start()
            elif event.event_type == MXEventType.SCENARIO_VERIFY:
                MXThread(name=f'{event.event_type.value}_{event.component.name}', target=self.verify_scenario, args=(target_component, self.timeout, )).start()
            elif event.event_type == MXEventType.SCENARIO_ADD:
                MXThread(name=f'{event.event_type.value}_{event.component.name}', target=self.add_scenario, args=(target_component, self.timeout, )).start()
            elif event.event_type == MXEventType.SCENARIO_RUN:
                MXThread(name=f'{event.event_type.value}_{event.component.name}', target=self.run_scenario, args=(target_component, self.timeout, )).start()
            elif event.event_type == MXEventType.SCENARIO_STOP:
                MXThread(name=f'{event.event_type.value}_{event.component.name}', target=self.stop_scenario, args=(target_component, self.timeout, )).start()
            elif event.event_type == MXEventType.SCENARIO_UPDATE:
                MXThread(name=f'{event.event_type.value}_{event.component.name}', target=self.update_scenario, args=(target_component, self.timeout, )).start()
            elif event.event_type == MXEventType.SCENARIO_DELETE:
                MXThread(name=f'{event.event_type.value}_{event.component.name}', target=self.delete_scenario, args=(target_component, self.timeout, )).start()

            # sync event
            elif event.event_type == MXEventType.MIDDLEWARE_CHECK:
                self.check_middleware(timeout=self.timeout)
            elif event.event_type == MXEventType.THING_CHECK:
                self.check_thing(timeout=self.timeout)
            elif event.event_type == MXEventType.SCENARIO_ADD_CHECK:
                self.scenario_add_check(timeout=self.timeout)
            elif event.event_type == MXEventType.SCENARIO_STATE_CHECK:
                self.scenario_state_check(timeout=self.timeout, **event.kwargs)
            else:
                raise MXTEST_LOG_DEBUG(f'Event type is {event.event_type}, but not implemented yet', MXTestLogLevel.FAIL)

    ####  middleware   #############################################################################################################

    def run_mosquitto(self, middleware: MXMiddleware, ssh_client: MXSSHClient, remote_home_dir: str):
        remote_mosquitto_conf_file_path = f'{middleware.remote_middleware_config_path}/{middleware.name}_mosquitto.conf'
        ssh_client.send_command(f'/sbin/mosquitto -c {remote_mosquitto_conf_file_path.replace("~", remote_home_dir)} '
                                f'-v 2> {middleware.remote_middleware_config_path.replace("~", remote_home_dir)}/{middleware.name}_mosquitto.log &', ignore_result=True)
        target_mosquitto_pid_list = ssh_client.send_command(f'netstat -lpn | grep :{middleware.mqtt_port}')
        if len(target_mosquitto_pid_list) > 0:
            return True

    def init_middleware(self, middleware: MXMiddleware, ssh_client: MXSSHClient, remote_home_dir: str):
        remote_init_script_file_path = f'{middleware.remote_middleware_config_path}/{middleware.name}_init.sh'
        ssh_client.send_command(f'chmod +x {remote_init_script_file_path.replace("~",remote_home_dir)}; '
                                f'bash {remote_init_script_file_path.replace("~",remote_home_dir)}')

    def subscribe_scenario_finish_topic(self, middleware: MXMiddleware):
        mqtt_client = self.find_mqtt_client(middleware)
        while not mqtt_client.is_run:
            time.sleep(BUSY_WAIT_TIMEOUT * 100)
        mqtt_client.subscribe('SIM/FINISH')

    def run_middleware(self, middleware: MXMiddleware, timeout: float = 5) -> bool:

        def wait_parent_middleware_online(middleware: MXMiddleware) -> bool:
            # MXTEST_LOG_DEBUG(f'Wait for middleware: {middleware.name}, device: {middleware.device.name} online', MXTestLogLevel.INFO, 'yellow')
            parent_middleware = middleware.parent
            if not parent_middleware:
                return True
            else:
                while not parent_middleware.online:
                    time.sleep(BUSY_WAIT_TIMEOUT * 100)
                else:
                    return True

        def middleware_run_command(middleware: MXMiddleware, remote_home_dir: str) -> str:
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

        def check_online(mqtt_client: MXMQTTClient, timeout: float) -> bool:
            expect_msg = self.publish_and_expect(
                middleware,
                encode_MQTT_message(MXProtocolType.WebClient.EM_REFRESH.value % f'{mqtt_client.get_client_id()}@{middleware.name}', '{}'),
                MXProtocolType.WebClient.ME_RESULT_SERVICE_LIST.value % (f'{mqtt_client.get_client_id()}@{middleware.name}'),
                auto_subscribe=True,
                auto_unsubscribe=False,
                timeout=timeout)

            if expect_msg == MXErrorCode.TIMEOUT:
                return False

            middleware.online = True
            return True

        def check_online_cyclic(mqtt_client: MXMQTTClient, timeout: int, check_interval: float) -> Union[bool, MXErrorCode]:
            cur_time = get_current_time()
            while get_current_time() - cur_time < timeout:
                if check_online(mqtt_client=mqtt_client, timeout=check_interval):
                    # MXTEST_LOG_DEBUG(f'Middleware: {middleware.name}, device: {middleware.device.name} on {middleware.device.host}:{middleware.mqtt_port} '
                    #                  f'- websocket: {middleware.websocket_port} is online!', MXTestLogLevel.PASS)
                    return True
                else:
                    time.sleep(BUSY_WAIT_TIMEOUT)
            else:
                MXTEST_LOG_DEBUG(f'[TIMEOUT] Running middleware: {middleware.name}, device: {middleware.device.name} is failed...', MXTestLogLevel.FAIL)
                return MXErrorCode.TIMEOUT

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

        if check_online_cyclic(mqtt_client, timeout=timeout, check_interval=0.5) == MXErrorCode.TIMEOUT:
            MXTEST_LOG_DEBUG(f'Retry to run middleware: {middleware.name}, device: {middleware.device.name}...', MXTestLogLevel.WARN)
            if not self.kill_middleware(middleware):
                raise SimulationFrameworkError(f'Send middleware kill command failed! - middleware: {middleware.name}, device: {middleware.device.name} failed!')
            return self.run_middleware(middleware, timeout=timeout)

        self.subscribe_scenario_finish_topic(middleware=middleware)
        self.simulation_progress.update(self.middleware_run_task, advance=1)
        return True

    def kill_middleware(self, middleware: MXMiddleware) -> bool:
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

    def check_middleware(self, timeout: float) -> bool:
        remain_timeout = timeout
        while not all(middleware.online for middleware in self.middleware_list):
            time.sleep(BUSY_WAIT_TIMEOUT * 100)
            remain_timeout -= BUSY_WAIT_TIMEOUT * 100
            if remain_timeout <= 0:
                return False
        else:
            return True

    ####  thing   #############################################################################################################

    def subscribe_thing_topic(self, thing: MXThing, mqtt_client: MXMQTTClient):
        for service in thing.service_list:
            mqtt_client.subscribe([MXProtocolType.Base.MT_EXECUTE.value % (service.name, thing.name, thing.middleware_client_name, '#'),
                                   (MXProtocolType.Base.MT_EXECUTE.value % (service.name, thing.name, '', '')).rstrip('/'),
                                   MXProtocolType.Base.TM_RESULT_EXECUTE.value % (service.name, thing.name, '+', '#'),
                                   (MXProtocolType.Base.TM_RESULT_EXECUTE.value % (service.name, thing.name, '', '')).rstrip('/')])
            if thing.is_super:
                mqtt_client.subscribe([
                    MXProtocolType.Super.MS_EXECUTE.value % (service.name, thing.name, thing.middleware_client_name, '#'),
                    MXProtocolType.Super.SM_EXECUTE.value % ('+', '+', '#'),
                    MXProtocolType.Super.MS_RESULT_EXECUTE.value % ('+', '+', '#'),
                    MXProtocolType.Super.SM_RESULT_EXECUTE.value % (service.name, thing.name, thing.middleware_client_name, '#'),
                    MXProtocolType.Super.MS_SCHEDULE.value % (service.name, thing.name, thing.middleware_client_name, '#'),
                    MXProtocolType.Super.SM_SCHEDULE.value % ('+', '+', '#'),
                    MXProtocolType.Super.MS_RESULT_SCHEDULE.value % ('+', '+', '#'),
                    MXProtocolType.Super.SM_RESULT_SCHEDULE.value % (service.name, thing.name, thing.middleware_client_name, '#')])
        # for value in self._value_list:
        #     mqtt_client.subscribe([MXProtocolType.Default.TM_VALUE_PUBLISH.value % (thing.name, value['name']), MXProtocolType.Default.TM_VALUE_PUBLISH_OLD.value % (thing.name, value['name'])])

    def run_thing(self, thing: MXThing, timeout: float = 5):
        middleware = self.find_parent_middleware(thing)
        ssh_client = self.find_ssh_client(thing)
        mqtt_client = self.find_mqtt_client(middleware)

        while not middleware.online:
            time.sleep(BUSY_WAIT_TIMEOUT * 100)

        if thing.is_super:
            while not all(thing.registered for thing in self.thing_list if not thing.is_super):
                time.sleep(BUSY_WAIT_TIMEOUT * 100)
            time.sleep(0.5)

        target_topic_list = [MXProtocolType.Base.TM_REGISTER.value % thing.name,
                             MXProtocolType.Base.TM_UNREGISTER.value % thing.name,
                             MXProtocolType.Base.MT_RESULT_REGISTER.value % thing.name,
                             MXProtocolType.Base.MT_RESULT_UNREGISTER.value % thing.name]
        mqtt_client.subscribe(target_topic_list)

        user = middleware.device.user
        thing_cd_command = f'cd {os.path.dirname(thing.remote_thing_file_path)}'
        thing_run_command = (f'{thing_cd_command}; python {home_dir_append(thing.remote_thing_file_path, user)} -n {thing.name} -ip '
                             f'{mqtt_client.host if not thing.is_super else "localhost"} -p {mqtt_client.port} -ac {thing.alive_cycle} > /dev/null 2>&1 & echo $!')
        # print(thing_run_command.split('>')[0].strip())
        thing_run_result = ssh_client.send_command(thing_run_command)
        thing.pid = thing_run_result[0]

        # mqtt_ret, ssh_rets = self.command_and_expect(thing,
        #                                              thing_run_command,
        #                                              MXProtocolType.Base.TM_REGISTER.value % (thing.name),)
        # thing.pid = ssh_rets[0]

        # reg_start_time = get_current_time()
        recv_msg = self.expect(thing,
                               MXProtocolType.Base.MT_RESULT_REGISTER.value % (thing.name),)
        # reg_end_time = get_current_time()

        topic, payload, _ = decode_MQTT_message(recv_msg)
        if recv_msg == MXErrorCode.TIMEOUT:
            self.kill_thing(thing)
            self.run_thing(thing, timeout=timeout)
        elif self._check_result_payload(payload):
            thing.registered = True
            thing.middleware_client_name = payload['middleware_name']
            self.subscribe_thing_topic(thing, mqtt_client)

            # progress = [thing.registered for thing in self.thing_list].count(True) / len(self.thing_list)
            # MXTEST_LOG_DEBUG(f'[REGISTER] thing: {thing.name} duration: {(reg_end_time - reg_start_time):0.4f}', MXTestLogLevel.INFO, progress=progress, color='green')
            self.simulation_progress.update(self.thing_run_task, advance=1)
            return True

    def unregister_thing(self, thing: MXThing):
        # MXTEST_LOG_DEBUG(f'Unregister Thing {thing.name}...', MXTestLogLevel.INFO, color='yellow')
        ssh_client = self.find_ssh_client(thing)
        ssh_client.send_command(f'kill -2 {thing.pid}')

    def kill_thing(self, thing: MXThing):
        # MXTEST_LOG_DEBUG(f'Kill Thing {thing.name}...', MXTestLogLevel.INFO, color='yellow')
        ssh_client = self.find_ssh_client(thing)
        ssh_client.send_command(f'kill -9 {thing.pid}')

    def check_thing(self, timeout: float) -> bool:
        remain_timeout = timeout
        while not all(thing.registered for thing in self.thing_list):
            time.sleep(BUSY_WAIT_TIMEOUT * 100)
            remain_timeout -= BUSY_WAIT_TIMEOUT * 100
            if remain_timeout <= 0:
                return False
        else:
            return True

    ####  scenario   #############################################################################################################

    def scenario_add_check(self, timeout: float):
        remain_timeout = timeout
        while not all([scenario.add_result_arrived for scenario in self.scenario_list]):
            time.sleep(BUSY_WAIT_TIMEOUT * 100)
            remain_timeout -= BUSY_WAIT_TIMEOUT * 100
            if remain_timeout <= 0:
                return False
        else:
            # MXTEST_LOG_DEBUG(f'All scenario Add is complete!...', MXTestLogLevel.INFO)
            return True

    def scenario_state_check(self, target_state: List[MXScenarioState], check_interval: float, retry: int, timeout: float):

        def task(middleware: MXMiddleware, timeout: float):
            scenario_check_list: List[bool] = []
            whole_scenario_info_list = self.get_whole_scenario_info(middleware, timeout=timeout)

            # Update scenario state
            for scenario_info in whole_scenario_info_list:
                scenario = self.find_scenario(scenario_info.name)
                scenario.state = scenario_info.state

            # Check scenario state
            for scenario in middleware.scenario_list:
                if scenario.state == MXScenarioState.INITIALIZED:
                    scenario.schedule_success = True

                if scenario.state in target_state:
                    scenario_check_list.append(True)
                else:
                    scenario_check_list.append(False)

            if all(scenario_check_list):
                self.simulation_progress.update(self.scenario_init_check_task, advance=len(middleware.scenario_list))
                return True

            return False

        if isinstance(target_state, MXScenarioState):
            target_state = [target_state]

        while retry:
            if all([scenario.schedule_success for scenario in self.scenario_list]):
                break
            # Skip task run for middleware that only have schedule finished scenarios.
            pool_map(task, [(middleware, timeout, ) for middleware in self.middleware_list if not all(scenario.schedule_success for scenario in middleware.scenario_list)])
            time.sleep(check_interval)
            retry -= 1

        return True

    def verify_scenario(self, scenario: MXScenario, timeout: float = 5):
        middleware = self.find_parent_middleware(scenario)
        mqtt_client = self.find_mqtt_client(middleware)

        trigger_topic = MXProtocolType.WebClient.EM_VERIFY_SCENARIO.value % mqtt_client.get_client_id()
        trigger_payload = json_string_to_dict(dict(name=scenario.name, text=scenario.scenario_code()))
        trigger_message = encode_MQTT_message(trigger_topic, trigger_payload)
        target_topic = MXProtocolType.WebClient.ME_RESULT_VERIFY_SCENARIO.value % mqtt_client.get_client_id()

        mqtt_client.subscribe(trigger_topic)
        recv_msg = self.publish_and_expect(
            scenario,
            trigger_message,
            target_topic,
            auto_unsubscribe=False,
            timeout=timeout)

        topic, payload, _ = decode_MQTT_message(recv_msg)
        if recv_msg == MXErrorCode.TIMEOUT:
            MXTEST_LOG_DEBUG(f'{MXComponentType.SCENARIO.value} of scenario: {scenario.name}, device: {scenario.middleware.device.name} {MXComponentActionType.SCENARIO_VERIFY.value} failed...', MXTestLogLevel.FAIL)
        return self

    def add_scenario(self, scenario: MXScenario, timeout: float = 5, check_interval: float = 3):
        middleware = self.find_parent_middleware(scenario)
        mqtt_client = self.find_mqtt_client(middleware)

        trigger_topic = MXProtocolType.WebClient.EM_ADD_SCENARIO.value % mqtt_client.get_client_id()
        trigger_payload = json_string_to_dict(dict(name=scenario.name, text=scenario.scenario_code(), priority=scenario.priority))
        trigger_message = encode_MQTT_message(trigger_topic, trigger_payload)
        target_topic = MXProtocolType.WebClient.ME_RESULT_ADD_SCENARIO.value % mqtt_client.get_client_id()

        mqtt_client.subscribe(trigger_topic)
        scenario.add_result_arrived = False
        scenario.schedule_timeout = False
        scenario.schedule_success = False

        mqtt_client.subscribe(trigger_topic)
        recv_msg = self.publish_and_expect(
            scenario,
            trigger_message,
            target_topic,
            auto_subscribe=True,
            auto_unsubscribe=False,
            timeout=timeout)

        topic, payload, _ = decode_MQTT_message(recv_msg)
        if recv_msg == MXErrorCode.TIMEOUT:
            MXTEST_LOG_DEBUG(f'{MXComponentType.SCENARIO.value} scenario: {scenario.name}, device: {scenario.middleware.device.name} {MXComponentActionType.SCENARIO_ADD.value} failed...', MXTestLogLevel.FAIL)
            MXTEST_LOG_DEBUG(f'==== Fault Scenario ====', MXTestLogLevel.FAIL)
            MXTEST_LOG_DEBUG(f'name: {scenario.name}', MXTestLogLevel.FAIL)
            MXTEST_LOG_DEBUG(f'code: \n{scenario.scenario_code()}', MXTestLogLevel.FAIL)
            scenario.schedule_timeout = True
            return False
        elif self._check_result_payload(payload):
            scenario.add_result_arrived = True
            self.simulation_progress.update(self.scenario_add_task, advance=1)
            return True

        # MXTEST_LOG_DEBUG(f'middleware: {middleware.name} scenario: {scenario.name}, device: {scenario.middleware.device.name} {MXComponentActionType.SCENARIO_ADD.value} success...', MXTestLogLevel.WARN)

    def run_scenario(self, scenario: MXScenario, timeout: float = 5):
        # NOTE: 이미 add_scenario를 통해 시나리오가 정상적으로 init되어있는 것이 확인되어있는 상태이므로 다시 시나리오상태를 확인할 필요는 없다.

        if scenario.schedule_timeout:
            # MXTEST_LOG_DEBUG(f'Scenario {scenario.name} is timeout. Skip scenario run...', MXTestLogLevel.WARN)
            return False
        if not scenario.schedule_success:
            # MXTEST_LOG_DEBUG(f'Scenario {scenario.name} is not initialized. Skip scenario run...', MXTestLogLevel.WARN)
            return False

        middleware = self.find_parent_middleware(scenario)
        mqtt_client = self.find_mqtt_client(middleware)

        trigger_topic = MXProtocolType.WebClient.EM_RUN_SCENARIO.value % mqtt_client.get_client_id()
        trigger_payload = json_string_to_dict(dict(name=scenario.name))
        trigger_message = encode_MQTT_message(trigger_topic, trigger_payload)
        target_topic = MXProtocolType.WebClient.ME_RESULT_RUN_SCENARIO.value % mqtt_client.get_client_id()

        mqtt_client.subscribe(trigger_topic)
        recv_msg = self.publish_and_expect(
            scenario,
            trigger_message,
            target_topic,
            auto_subscribe=True,
            auto_unsubscribe=False,
            timeout=timeout)

        topic, payload, _ = decode_MQTT_message(recv_msg)
        if recv_msg == MXErrorCode.TIMEOUT:
            # MXTEST_LOG_DEBUG(f'{MXComponentType.SCENARIO.value} scenario: {scenario.name}, device: {scenario.middleware.device.name} {MXComponentActionType.SCENARIO_RUN.value} failed...', MXTestLogLevel.FAIL)
            return False
        elif self._check_result_payload(payload):
            # MXTEST_LOG_DEBUG(f'[SCENE_RUN] scenario: {scenario.name} duration: {(recv_time - pub_time):0.4f}', MXTestLogLevel.INFO, progress=progress, color='green')
            return True

    def stop_scenario(self, scenario: MXScenario, timeout: float = 5):
        middleware = self.find_parent_middleware(scenario)
        mqtt_client = self.find_mqtt_client(middleware)

        trigger_topic = MXProtocolType.WebClient.EM_STOP_SCENARIO.value % mqtt_client.get_client_id()
        trigger_payload = json_string_to_dict(dict(name=scenario.name))
        trigger_message = encode_MQTT_message(trigger_topic, trigger_payload)
        target_topic = MXProtocolType.WebClient.ME_RESULT_STOP_SCENARIO.value % mqtt_client.get_client_id()

        # NOTE: 시나리오의 상태를 확인할 필요 없이 바로 stop을 해도 먹히는지 확인이 필요
        # if not self.get_scenario_state(scenario, timeout=timeout) in [MXScenarioState.RUNNING, MXScenarioState.EXECUTING]:
        #     MXTEST_LOG_DEBUG(f'Fail to stop scenario {scenario.name} - state: {scenario.state.value}', MXTestLogLevel.FAIL)
        #     return False

        mqtt_client.subscribe(trigger_topic)
        recv_msg = self.publish_and_expect(
            scenario,
            trigger_message,
            target_topic,
            auto_subscribe=True,
            auto_unsubscribe=False,
            timeout=timeout)

        if recv_msg == MXErrorCode.TIMEOUT:
            MXTEST_LOG_DEBUG(f'{MXComponentType.SCENARIO.value} scenario: {scenario.name}, device: {scenario.middleware.device.name} {MXComponentActionType.SCENARIO_STOP.value} failed...', MXTestLogLevel.FAIL)
        return self

    def update_scenario(self, scenario: MXScenario, timeout: float = 5):
        middleware = self.find_parent_middleware(scenario)
        mqtt_client = self.find_mqtt_client(middleware)

        trigger_topic = MXProtocolType.WebClient.EM_UPDATE_SCENARIO.value % mqtt_client.get_client_id()
        trigger_payload = json_string_to_dict(dict(name=scenario.name))
        trigger_message = encode_MQTT_message(trigger_topic, trigger_payload)
        target_topic = MXProtocolType.WebClient.ME_RESULT_UPDATE_SCENARIO.value % mqtt_client.get_client_id()

        # NOTE: 시나리오의 상태를 확인할 필요 없이 바로 update을 해도 먹히는지 확인이 필요
        # if not self.get_scenario_state(scenario, timeout=timeout) in [MXScenarioState.STUCKED]:
        #     MXTEST_LOG_DEBUG(f'Fail to stop scenario {scenario.name} - state: {scenario.state.value}', MXTestLogLevel.FAIL)
        #     return False

        mqtt_client.subscribe(trigger_topic)
        recv_msg = self.publish_and_expect(
            scenario,
            trigger_message,
            target_topic,
            auto_subscribe=True,
            auto_unsubscribe=False,
            timeout=timeout)

        if recv_msg == MXErrorCode.TIMEOUT:
            MXTEST_LOG_DEBUG(f'{MXComponentType.SCENARIO.value} scenario: {scenario.name}, device: {scenario.middleware.device.name} {MXComponentActionType.SCENARIO_UPDATE.value} failed...', MXTestLogLevel.FAIL)
        return self

    def delete_scenario(self, scenario: MXScenario, timeout: float = 5):
        middleware = self.find_parent_middleware(scenario)
        mqtt_client = self.find_mqtt_client(middleware)

        trigger_topic = MXProtocolType.WebClient.EM_DELETE_SCENARIO.value % mqtt_client.get_client_id()
        trigger_payload = json_string_to_dict(dict(name=scenario.name))
        trigger_message = encode_MQTT_message(trigger_topic, trigger_payload)
        target_topic = MXProtocolType.WebClient.ME_RESULT_DELETE_SCENARIO.value % mqtt_client.get_client_id()

        # NOTE: 시나리오의 상태를 확인할 필요 없이 바로 delete를 해도 먹히는지 확인이 필요
        # if not self.get_scenario_state(scenario, timeout=timeout) in [MXScenarioState.RUNNING, MXScenarioState.EXECUTING]:
        #     MXTEST_LOG_DEBUG(
        #         f'Fail to stop scenario {scenario.name} - state: {scenario.state.value}', MXTestLogLevel.FAIL)
        #     return False
        mqtt_client.subscribe(trigger_topic)
        recv_msg = self.publish_and_expect(
            scenario,
            trigger_message,
            target_topic,
            auto_subscribe=True,
            auto_unsubscribe=False,
            timeout=timeout)

        if recv_msg == MXErrorCode.TIMEOUT:
            MXTEST_LOG_DEBUG(f'{MXComponentType.SCENARIO.value} scenario: {scenario.name}, device: {scenario.middleware.device.name} {MXComponentActionType.SCENARIO_DELETE.value} failed...', MXTestLogLevel.FAIL)
        return self

    def get_whole_scenario_info(self, middleware: MXMiddleware, timeout: float) -> List[MXScenarioInfo]:
        mqtt_client = self.find_mqtt_client(middleware)

        recv_msg = self.publish_and_expect(
            middleware,
            encode_MQTT_message(MXProtocolType.WebClient.EM_REFRESH.value % f'{mqtt_client.get_client_id()}@{middleware.name}', '{}'),
            MXProtocolType.WebClient.ME_RESULT_SCENARIO_LIST.value % f'{mqtt_client.get_client_id()}@{middleware.name}',
            auto_subscribe=True,
            auto_unsubscribe=False,
            timeout=timeout)

        if recv_msg in [MXErrorCode.TIMEOUT, MXErrorCode.FAIL]:
            return []

        topic, payload, _ = decode_MQTT_message(recv_msg)
        scenario_info_list = [MXScenarioInfo(id=scenario_info['id'],
                                             name=scenario_info['name'],
                                             state=MXScenarioState.get(scenario_info['state']),
                                             code=scenario_info['contents'],
                                             schedule_info=scenario_info['scheduleInfo']) for scenario_info in payload['scenarios']]
        return scenario_info_list

    def get_whole_service_list_info(self, middleware: MXMiddleware, timeout: float) -> List[MXService]:
        mqtt_client = self.find_mqtt_client(middleware)
        recv_msg = self.publish_and_expect(
            middleware,
            encode_MQTT_message(MXProtocolType.WebClient.EM_REFRESH.value % f'{mqtt_client.get_client_id()}@{middleware.name}', '{}'),
            MXProtocolType.WebClient.ME_RESULT_SERVICE_LIST.value % f'{mqtt_client.get_client_id()}@{middleware.name}',
            auto_subscribe=True,
            auto_unsubscribe=False,
            timeout=timeout)

        topic, payload, _ = decode_MQTT_message(recv_msg)
        if recv_msg == MXErrorCode.TIMEOUT:
            MXTEST_LOG_DEBUG(f'Get whole service list info of {middleware.name} failed -> MQTT timeout...', MXTestLogLevel.FAIL)
            return []

        whole_service_info: List[MXService] = []
        for service in payload['services']:
            if service['hierarchy'] == 'local' or service['hierarchy'] == 'parent':
                for thing in service['things']:
                    for service in thing['functions']:
                        service = MXService(name=service['name'],
                                            is_super=thing['is_super'],
                                            tag_list=[tag['name'] for tag in service['tags']])
                        whole_service_info.append(service)
        return whole_service_info

    #### kill ##########################################################################################################################

    def get_proc_pid(self, ssh_client: MXSSHClient, proc_name: str, port: int = None) -> Union[List[int], bool]:
        result: List[str] = ssh_client.send_command(f"lsof -i :{port} | grep {proc_name[:9]}")
        pid_list = list(set([line.split()[1] for line in result]))
        if len(pid_list) == 0:
            return False
        elif len(pid_list) == 1:
            return pid_list

    def get_component_proc_pid(self, ssh_client: MXSSHClient, component: MXComponent) -> List[int]:
        if isinstance(component, MXMiddleware):
            middleware_pid_list = self.get_proc_pid(ssh_client, 'sopiot_middleware', component.mqtt_port)
            mosquitto_pid_list = self.get_proc_pid(ssh_client, 'mosquitto', component.mqtt_port)
            return dict(middleware_pid_list=middleware_pid_list, mosquitto_pid_list=mosquitto_pid_list)
        elif isinstance(component, MXThing):
            middleware = self.find_parent_middleware(component)
            thing_pid_list = self.get_proc_pid(ssh_client, 'python', middleware.mqtt_port)
            return dict(thing_pid_list=thing_pid_list)

    def kill_all_middleware(self):
        MXTEST_LOG_DEBUG(f'Kill all middleware...', MXTestLogLevel.INFO, 'red')
        for middleware in self.middleware_list:
            ssh_client = self.find_ssh_client(middleware)
            ssh_client.send_command('pidof sopiot_middleware | xargs kill -9')
            ssh_client.send_command('pidof mosquitto | xargs kill -9')

    def kill_all_thing(self):
        MXTEST_LOG_DEBUG(f'Kill all python instance...', MXTestLogLevel.INFO, 'red')

        self_pid = os.getpid()
        for ssh_client in self.ssh_client_list:
            result = ssh_client.send_command(f"ps -ef | grep python | grep _thing_ | grep -v grep | awk '{{print $2}}'")

            for pid in result:
                if pid == self_pid:
                    continue
                result = ssh_client.send_command(f'kill -9 {pid}')

    def _kill_every_ssh_client(self):
        MXTEST_LOG_DEBUG(f'Kill all ssh client', MXTestLogLevel.INFO, 'red')
        for ssh_client in self.ssh_client_list:
            ssh_client.disconnect()
            del ssh_client

    def _kill_every_mqtt_client(self):
        MXTEST_LOG_DEBUG(f'Kill all mqtt client', MXTestLogLevel.INFO, 'red')
        for mqtt_client in self.mqtt_client_list:
            mqtt_client.stop()
            del mqtt_client

    def kill_every_process(self) -> bool:
        with Progress() as progress:
            task1 = progress.add_task("Clean up simulation processes", total=len(self.middleware_list) + len(self.ssh_client_list))
            task2 = progress.add_task("Kill middleware processes", total=len(self.middleware_list))
            if not self.middleware_debug:
                for middleware in self.middleware_list:
                    ssh_client = self.find_ssh_client(middleware)
                    ssh_client.send_command('pidof sopiot_middleware | xargs kill -9')
                    ssh_client.send_command('pidof mosquitto | xargs kill -9')
                    progress.update(task1, advance=1)
                    progress.update(task2, advance=1)

            self_pid = os.getpid()
            task3 = progress.add_task("Kill thing processes", total=len(self.ssh_client_list))
            for ssh_client in self.ssh_client_list:
                result = ssh_client.send_command(f"ps -ef | grep python | grep _thing_ | grep -v grep | awk '{{print $2}}'")

                for pid in result:
                    if pid == self_pid:
                        continue
                    result = ssh_client.send_command(f'kill -9 {pid}')
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

    def expect(self, component: Union[MXMiddleware, MXThing, MXScenario], target_topic: str, timeout: int = 5) -> Union[mqtt.MQTTMessage, MXErrorCode]:
        if not self.event_listener_thread.is_alive():
            raise RuntimeError('Event listener thread is not alive')

        cur_time = get_current_time()
        target_protocol = MXProtocolType.get(target_topic)

        while get_current_time() - cur_time < timeout:
            if not target_protocol in component.recv_msg_table:
                time.sleep(BUSY_WAIT_TIMEOUT)
                continue

            recv_msg = hash_pop(component.recv_msg_table, key=target_protocol)
            if recv_msg == None:
                return MXErrorCode.FAIL

            topic, _, _ = decode_MQTT_message(recv_msg)
            if mqtt.topic_matches_sub(target_topic, topic):
                return recv_msg
            else:
                MXTEST_LOG_DEBUG(f'Topic match failed... Expect {target_topic} but receive {topic}', MXTestLogLevel.WARN)
                return MXErrorCode.FAIL
        else:
            return MXErrorCode.TIMEOUT

    def publish_and_expect(self, component: MXComponent, trigger_msg: mqtt.MQTTMessage = None, target_topic: str = None,
                           auto_subscribe: bool = True, auto_unsubscribe: bool = False, timeout: int = 5) -> Union[mqtt.MQTTMessage, MXErrorCode]:
        if isinstance(component, MXMiddleware):
            target_middleware = component
        elif isinstance(component, (MXThing, MXScenario)):
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

    def command_and_expect(self, component: MXComponent, trigger_command: Union[List[str], str] = None, target_topic: str = None,
                           auto_subscribe: bool = True, auto_unsubscribe: bool = False, timeout: int = 5) -> Union[mqtt.MQTTMessage, MXErrorCode]:
        if isinstance(component, MXMiddleware):
            target_middleware = component
        elif isinstance(component, (MXThing, MXScenario)):
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

        ssh_rets = []
        if isinstance(trigger_command, list):
            for command in trigger_command:
                ssh_ret = ssh_client.send_command(command)
                ssh_rets.append(ssh_ret)
        else:
            ssh_ret = ssh_client.send_command(trigger_command)
            ssh_rets.append(ssh_ret)
        mqtt_ret = self.expect(component, target_topic, timeout)

        if auto_unsubscribe:
            mqtt_client.unsubscribe(target_topic)

        return mqtt_ret, ssh_rets

    #### on_recv_message ##########################################################################################################################

    def _on_recv_message(self, msg: mqtt.MQTTMessage):
        topic, payload, _ = decode_MQTT_message(msg)
        timestamp = get_current_time() - self.simulation_start_time

        protocol = MXProtocolType.get(topic)
        return_type = MXType.get(payload.get('return_type', None))
        return_value = payload.get('return_value', None)
        error = MXErrorCode.get(payload.get('error', None))
        scenario_name = payload.get('name', None) if payload.get('name', None) != None else payload.get('scenario', None)
        topic_slice = topic.split('/')

        if protocol in [MXProtocolType.WebClient.ME_RESULT_SCENARIO_LIST, MXProtocolType.WebClient.ME_RESULT_SERVICE_LIST]:
            client_id = topic_slice[3]
            middleware_name = client_id.split('@')[1]
            middleware = self.find_middleware(middleware_name)
            hash_insert(middleware.recv_msg_table, data=(protocol, msg))
        elif protocol == MXProtocolType.Base.TM_REGISTER:
            thing_name = topic_slice[2]
            thing = self.find_thing(thing_name)
            hash_insert(thing.recv_msg_table, data=(protocol, msg))
            self.event_log.append(MXEvent(event_type=MXEventType.THING_REGISTER, middleware_component=thing.middleware, thing_component=thing, timestamp=timestamp, duration=0))
        elif protocol == MXProtocolType.Base.MT_RESULT_REGISTER:
            thing_name = topic_slice[3]
            thing = self.find_thing(thing_name)
            hash_insert(thing.recv_msg_table, data=(protocol, msg))
            for event in list(reversed(self.event_log)):
                if not (event.middleware_component == thing.middleware and event.thing_component == thing and event.event_type == MXEventType.THING_REGISTER):
                    continue
                event.duration = timestamp - event.timestamp
                event.error = error
                break
        elif protocol == MXProtocolType.Base.TM_UNREGISTER:
            thing_name = topic_slice[2]
            thing = self.find_thing(thing_name)
            hash_insert(thing.recv_msg_table, data=(protocol, msg))
            self.event_log.append(MXEvent(event_type=MXEventType.THING_UNREGISTER, middleware_component=thing.middleware, thing_component=thing, timestamp=timestamp, duration=0))
        elif protocol == MXProtocolType.Base.MT_RESULT_UNREGISTER:
            thing_name = topic_slice[3]
            thing = self.find_thing(thing_name)
            hash_insert(thing.recv_msg_table, data=(protocol, msg))
            for event in list(reversed(self.event_log)):
                if not (event.middleware_component == thing.middleware and event.thing_component == thing and event.event_type == MXEventType.THING_UNREGISTER):
                    continue
                event.duration = timestamp - event.timestamp
                event.error = error
                # MXTEST_LOG_DEBUG(f'[UNREGISTER] thing: {thing_name} duration: {event.duration:0.4f}', MXTestLogLevel.INFO)
                break
        elif protocol == MXProtocolType.Base.MT_EXECUTE:
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
                event_type = MXEventType.SUB_FUNCTION_EXECUTE
            else:
                event_type = MXEventType.FUNCTION_EXECUTE

            self.event_log.append(MXEvent(event_type=event_type, middleware_component=thing.middleware, thing_component=thing, service_component=service,
                                          scenario_component=scenario, timestamp=timestamp, duration=0, requester_middleware_name=requester_middleware_name,
                                          super_thing_name=super_thing_name, super_function_name=super_function_name))
        elif protocol == MXProtocolType.Base.TM_RESULT_EXECUTE:
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
                if event.middleware_component == thing.middleware and event.thing_component == thing and event.service_component == service and event.scenario_component == scenario and event.requester_middleware_name == requester_middleware_name and event.event_type in [MXEventType.FUNCTION_EXECUTE, MXEventType.SUB_FUNCTION_EXECUTE]:
                    event.duration = timestamp - event.timestamp
                    event.error = error
                    event.return_type = return_type
                    event.return_value = return_value
                    event.requester_middleware_name = requester_middleware_name

                    passed_time = get_current_time() - self.simulation_start_time
                    progress = passed_time / self.running_time

                    if event.event_type == MXEventType.SUB_FUNCTION_EXECUTE:
                        color = 'light_magenta' if event.error == MXErrorCode.FAIL else 'light_cyan'
                        # MXTEST_LOG_DEBUG(f'[EXECUTE_SUB] thing: {thing_name} function: {function_name} scenario: {scenario_name} '
                        #                  f'requester_middleware_name: {requester_middleware_name} duration: {event.duration:0.4f} '
                        #                  f'return value: {return_value} - {return_type.value} error:{event.error.value}', MXTestLogLevel.PASS, progress=progress, color=color)
                    elif event.event_type == MXEventType.FUNCTION_EXECUTE:
                        color = 'red' if event.error == MXErrorCode.FAIL else 'green'
                        # MXTEST_LOG_DEBUG(f'[EXECUTE] thing: {thing_name} function: {function_name} scenario: {scenario_name} '
                        #                  f'requester_middleware_name: {requester_middleware_name} duration: {event.duration:0.4f} '
                        #                  f'return value: {return_value} - {return_type.value} error:{event.error.value}', MXTestLogLevel.PASS, progress=progress, color=color)
                    break
        elif protocol == MXProtocolType.WebClient.EM_VERIFY_SCENARIO:
            scenario = self.find_scenario(scenario_name)
            self.event_log.append(MXEvent(event_type=MXEventType.SCENARIO_VERIFY, middleware_component=scenario.middleware, scenario_component=scenario, timestamp=timestamp, duration=0))
        elif protocol == MXProtocolType.WebClient.ME_RESULT_VERIFY_SCENARIO:
            scenario = self.find_scenario(scenario_name)
            hash_insert(scenario.recv_msg_table, data=(protocol, msg))
            for event in list(reversed(self.event_log)):
                if not (event.middleware_component == scenario.middleware and event.scenario_component == scenario and event.event_type == MXEventType.SCENARIO_VERIFY):
                    continue
                event.duration = timestamp - event.timestamp
                event.error = error
                # MXTEST_LOG_DEBUG(f'[SCENE_VERIFY] scenario: {scenario_name} duration: {event.duration:0.4f}', MXTestLogLevel.INFO)
                break
        elif protocol == MXProtocolType.WebClient.EM_ADD_SCENARIO:
            scenario = self.find_scenario(scenario_name)
            self.event_log.append(MXEvent(event_type=MXEventType.SCENARIO_ADD, middleware_component=scenario.middleware, scenario_component=scenario, timestamp=timestamp, duration=0))
        elif protocol == MXProtocolType.WebClient.ME_RESULT_ADD_SCENARIO:
            scenario = self.find_scenario(scenario_name)
            hash_insert(scenario.recv_msg_table, data=(protocol, msg))
            for event in list(reversed(self.event_log)):
                if not (event.middleware_component == scenario.middleware and event.scenario_component == scenario and event.event_type == MXEventType.SCENARIO_ADD):
                    continue
                event.duration = timestamp - event.timestamp
                event.error = error
                break
        elif protocol == MXProtocolType.WebClient.EM_RUN_SCENARIO:
            scenario = self.find_scenario(scenario_name)
            self.event_log.append(MXEvent(event_type=MXEventType.SCENARIO_RUN, middleware_component=scenario.middleware, scenario_component=scenario, timestamp=timestamp, duration=0))
        elif protocol == MXProtocolType.WebClient.ME_RESULT_RUN_SCENARIO:
            scenario = self.find_scenario(scenario_name)
            hash_insert(scenario.recv_msg_table, data=(protocol, msg))
            for event in list(reversed(self.event_log)):
                if not (event.middleware_component == scenario.middleware and event.scenario_component == scenario and event.event_type == MXEventType.SCENARIO_RUN):
                    continue
                event.duration = timestamp - event.timestamp
                event.error = error
                # MXTEST_LOG_DEBUG(f'[SCENE_RUN] scenario: {scenario_name} duration: {event.duration:0.4f}', MXTestLogLevel.INFO)
                break
        elif protocol == MXProtocolType.WebClient.EM_STOP_SCENARIO:
            scenario = self.find_scenario(scenario_name)
            self.event_log.append(MXEvent(event_type=MXEventType.SCENARIO_STOP, middleware_component=scenario.middleware, scenario_component=scenario, timestamp=timestamp, duration=0))
        elif protocol == MXProtocolType.WebClient.ME_RESULT_STOP_SCENARIO:
            scenario = self.find_scenario(scenario_name)
            hash_insert(scenario.recv_msg_table, data=(protocol, msg))
            for event in list(reversed(self.event_log)):
                if not (event.middleware_component == scenario.middleware and event.scenario_component == scenario and event.event_type == MXEventType.SCENARIO_STOP):
                    continue
                event.duration = timestamp - event.timestamp
                event.error = error
                # MXTEST_LOG_DEBUG(f'[SCENE_STOP] scenario: {scenario_name} duration: {event.duration:0.4f}', MXTestLogLevel.INFO)
                break
        elif protocol == MXProtocolType.WebClient.EM_UPDATE_SCENARIO:
            scenario = self.find_scenario(scenario_name)
            self.event_log.append(MXEvent(event_type=MXEventType.SCENARIO_UPDATE, middleware_component=scenario.middleware, scenario_component=scenario, timestamp=timestamp, duration=0))
        elif protocol == MXProtocolType.WebClient.ME_RESULT_UPDATE_SCENARIO:
            scenario = self.find_scenario(scenario_name)
            hash_insert(scenario.recv_msg_table, data=(protocol, msg))
            for event in list(reversed(self.event_log)):
                if not (event.middleware_component == scenario.middleware and event.scenario_component == scenario and event.event_type == MXEventType.SCENARIO_UPDATE):
                    continue
                event.duration = timestamp - event.timestamp
                event.error = error
                # MXTEST_LOG_DEBUG(f'[SCENE_UPDATE] scenario: {scenario_name} duration: {event.duration:0.4f}', MXTestLogLevel.INFO)
                break
        elif protocol == MXProtocolType.WebClient.EM_DELETE_SCENARIO:
            scenario = self.find_scenario(scenario_name)
            self.event_log.append(MXEvent(event_type=MXEventType.SCENARIO_DELETE, middleware_component=scenario.middleware, scenario_component=scenario, timestamp=timestamp, duration=0))
        elif protocol == MXProtocolType.WebClient.ME_RESULT_DELETE_SCENARIO:
            scenario = self.find_scenario(scenario_name)
            hash_insert(scenario.recv_msg_table, data=(protocol, msg))
            for event in list(reversed(self.event_log)):
                if not (event.middleware_component == scenario.middleware and event.scenario_component == scenario and event.event_type == MXEventType.SCENARIO_DELETE):
                    continue
                event.duration = timestamp - event.timestamp
                event.error = error
                # MXTEST_LOG_DEBUG(f'[SCENE_DELETE] scenario: {scenario_name} duration: {event.duration:0.4f}', MXTestLogLevel.INFO)
                break

        ####################################################################################################################################################

        elif protocol == MXProtocolType.Super.MS_SCHEDULE:
            requester_middleware_name = topic_slice[5]
            super_middleware_name = topic_slice[4]
            super_thing_name = topic_slice[3]
            super_function_name = topic_slice[2]

            super_thing = self.find_thing(super_thing_name)
            scenario = self.find_scenario(scenario_name)
            super_service = super_thing.find_service_by_name(super_function_name)

            self.event_log.append(MXEvent(event_type=MXEventType.SUPER_SCHEDULE, middleware_component=super_thing.middleware, thing_component=super_thing,
                                          service_component=super_service, scenario_component=scenario, timestamp=timestamp, duration=0))
            # MXTEST_LOG_DEBUG(f'[SUPER_SCHEDULE_START] super_middleware: {super_middleware_name} requester_middleware: {requester_middleware_name} '
            #                  f'super_thing: {super_thing_name} super_function: {super_function_name} scenario: {scenario_name}', MXTestLogLevel.INFO)
        elif protocol == MXProtocolType.Super.SM_SCHEDULE:
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
            # MXTEST_LOG_DEBUG(f'[SUB_SCHEDULE_START] super_middleware: {""} requester_middleware: {requester_middleware_name} super_thing: {super_thing_name} '
            #                  f'super_function: {super_function_name} target_middleware: {target_middleware_name} target_thing: {target_thing_name} '
            #                  f'target_function: {target_function_name} scenario: {scenario_name}', MXTestLogLevel.INFO, progress=progress, color=color)
        elif protocol == MXProtocolType.Super.MS_RESULT_SCHEDULE:
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
            # MXTEST_LOG_DEBUG(f'[SUB_SCHEDULE_END] super_middleware: {""} requester_middleware: {requester_middleware_name} super_thing: {super_thing_name} '
            #                  f'super_function: {super_function_name} target_middleware: {target_middleware_name} target_thing: {target_thing_name} '
            #                  f'target_function: {target_function_name} scenario: {scenario_name}', MXTestLogLevel.INFO, progress=progress, color=color)
        elif protocol == MXProtocolType.Super.SM_RESULT_SCHEDULE:
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
                        and event.scenario_component == scenario and event.event_type == MXEventType.SUPER_SCHEDULE):
                    continue
                event.duration = timestamp - event.timestamp
                event.error = error
                event.return_type = return_type
                event.return_value = return_value

                progress = [scenario.add_result_arrived for scenario in self.scenario_list].count(True) / len(self.scenario_list)
                # MXTEST_LOG_DEBUG(f'[SUPER_SCHEDULE_END] super_middleware: {super_middleware_name} requester_middleware: {requester_middleware_name} '
                #                  f'super_thing: {super_thing_name} super_function: {super_function_name} scenario: {scenario_name} duration: {event.duration:0.4f} '
                #                  f'result: {event.error.value}', MXTestLogLevel.INFO, progress=progress)
                break
        elif protocol == MXProtocolType.Super.MS_EXECUTE:
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

            self.event_log.append(MXEvent(event_type=MXEventType.SUPER_FUNCTION_EXECUTE, middleware_component=super_thing.middleware, thing_component=super_thing,
                                          service_component=super_service, scenario_component=scenario, timestamp=timestamp, duration=0))
            passed_time = get_current_time() - self.simulation_start_time
            progress = passed_time / self.running_time
            # MXTEST_LOG_DEBUG(f'[SUPER_EXECUTE_START] super_middleware: {super_middleware_name} requester_middleware: {requester_middleware_name} super_thing: {super_thing_name} '
            #                  f'super_function: {super_function_name} scenario: {scenario_name}', MXTestLogLevel.INFO, progress=progress)
        elif protocol == MXProtocolType.Super.SM_EXECUTE:
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
            # MXTEST_LOG_DEBUG(f'[SUB_EXECUTE_START] super_middleware: {""} requester_middleware: {requester_middleware_name} super_thing: {super_thing_name} '
            #                  f'super_function: {super_function_name} target_middleware: {target_middleware_name} target_thing: {target_thing_name} '
            #                  f'target_function: {target_function_name} scenario: {scenario_name}', MXTestLogLevel.INFO, progress=progress, color=color)
        elif protocol == MXProtocolType.Super.MS_RESULT_EXECUTE:
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
            # MXTEST_LOG_DEBUG(f'[SUB_EXECUTE_END] super_middleware: {""} requester_middleware: {requester_middleware_name} super_thing: {super_thing_name} '
            #                  f'super_function: {super_function_name} target_middleware: {target_middleware_name} target_thing: {target_thing_name} '
            #                  f'target_function: {target_function_name} scenario: {scenario_name}', MXTestLogLevel.INFO, progress=progress, color=color)
        elif protocol == MXProtocolType.Super.SM_RESULT_EXECUTE:
            requester_middleware_name = topic_slice[6]
            super_middleware_name = topic_slice[5]
            super_thing_name = topic_slice[4]
            super_function_name = topic_slice[3]

            super_thing = self.find_thing(super_thing_name)
            scenario = self.find_scenario(scenario_name)
            super_service = super_thing.find_service_by_name(super_function_name)

            for event in list(reversed(self.event_log)):
                if not (event.event_type == MXEventType.SUPER_FUNCTION_EXECUTE and event.middleware_component == super_thing.middleware and event.thing_component == super_thing
                        and event.service_component == super_service and event.scenario_component == scenario):
                    continue
                event.duration = timestamp - event.timestamp
                event.error = error
                event.return_type = return_type
                event.return_value = return_value

                passed_time = get_current_time() - self.simulation_start_time
                progress = passed_time / self.running_time
                # MXTEST_LOG_DEBUG(f'[SUPER_EXECUTE_END] super_middleware: {super_middleware_name} requester_middleware: {requester_middleware_name} '
                #                  f'super_thing: {super_thing_name} super_function: {super_function_name} scenario: {scenario_name} duration: {event.duration:0.4f} '
                #                  f'return value: {return_value} - {return_type.value} error:{event.error.value}', MXTestLogLevel.INFO, progress=progress)
                break
        elif 'SIM/FINISH' in topic:
            scenario = self.find_scenario(scenario_name)
            scenario.cycle_count += 1
            # MXTEST_LOG_DEBUG(f'[SIM_FINISH] scenario: {scenario.name}, cycle_count: {scenario.cycle_count}', MXTestLogLevel.WARN)
            return True
        else:
            print(MXProtocolType.Super.SM_SCHEDULE.get_prefix())
            print(protocol)
            raise Exception(f'Unknown topic: {topic}')

        # elif topic_type == MXProtocolType.Default.TM_VALUE_PUBLISH:
        #     pass
        # elif MXProtocolType.Default.TM_VALUE_PUBLISH_OLD.get_prefix() in topic:
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
            MXTEST_LOG_DEBUG(f'Payload is None (timeout)!!!', MXTestLogLevel.FAIL)
            return None

        error_code = payload['error']
        error_string = payload.get('error_string', None)

        if error_code in [0, -4]:
            return True
        else:
            MXTEST_LOG_DEBUG(f'error_code: {error_code}, error_string : {error_string if error_string else "(No error string)"}', MXTestLogLevel.FAIL)
            return False

    def _get_device_list(self) -> List[MXDevice]:
        duplicated_device_list: List[MXDevice] = [middleware.device for middleware in self.middleware_list] + [thing.device for thing in self.thing_list]
        device_list: List[MXDevice] = []

        for device in duplicated_device_list:
            if device in device_list:
                continue
            device_list.append(device)

        return device_list

    def find_ssh_client(self, component: Union[MXMiddleware, MXThing]) -> MXSSHClient:
        for ssh_client in self.ssh_client_list:
            if ssh_client.device == component.device:
                return ssh_client
        else:
            return None

    def find_mqtt_client(self, middleware: MXMiddleware) -> MXMQTTClient:
        for mqtt_client in self.mqtt_client_list:
            if mqtt_client.middleware == middleware:
                return mqtt_client
        else:
            return None

    def find_middleware(self, target_middleware_name: str) -> MXMiddleware:
        for middleware in self.middleware_list:
            if middleware.name == target_middleware_name:
                return middleware
        else:
            return None

    def find_scenario(self, target_scenario_name: str) -> MXScenario:
        for scenario in self.scenario_list:
            if scenario.name == target_scenario_name:
                return scenario
        else:
            return None

    def find_thing(self, target_thing_name: str) -> MXThing:
        for thing in self.thing_list:
            if thing.name == target_thing_name:
                return thing
        else:
            return None

    def find_service(self, target_service_name: str) -> MXService:
        for thing in self.thing_list:
            for service in thing.service_list:
                if service.name == target_service_name:
                    return service
        else:
            return None

    def find_parent_middleware(self, component: Union[MXMiddleware, MXScenario, MXThing, MXService]) -> MXMiddleware:
        if isinstance(component, MXMiddleware):
            return component.parent
        elif isinstance(component, MXScenario):
            return component.middleware
        elif isinstance(component, MXThing):
            return component.middleware
        elif isinstance(component, MXService):
            return component.thing.middleware
        else:
            return None
