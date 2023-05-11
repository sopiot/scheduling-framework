
from simulation_framework.core.ssh_client import *
from simulation_framework.core.mqtt_client import *


class SoPEventHandler:

    def __init__(self, simulation_env: SoPMiddlewareElement = None, event_log: List[SoPEvent] = [], timeout: float = 5.0, mqtt_debug: bool = False, middleware_debug: bool = False, running_time: float = None,
                 download_logs: bool = False) -> None:
        self.simulation_env = simulation_env
        self.middleware_list: List[SoPMiddlewareElement] = get_middleware_list_recursive(
            self.simulation_env)
        self.thing_list: List[SoPThingElement] = get_thing_list_recursive(
            self.simulation_env)
        self.scenario_list: List[SoPScenarioElement] = get_scenario_list_recursive(
            self.simulation_env)
        self.device_list: List[SoPDeviceElement] = []

        self.mqtt_client_list: List[SoPMQTTClient] = []
        self.ssh_client_list: List[SoPSSHClient] = []

        self.event_listener_event = Event()
        # self.event_listener_lock = Lock()
        self.event_listener_thread: SoPThread = SoPThread(
            name='event_listener', target=self.event_listener, args=(self.event_listener_event, ))

        # simulator와 같은 인스턴스를 공유한다.
        self.simulation_start_time = 0
        self.simulation_duration = 0
        self.event_log: List[SoPEvent] = event_log
        self.timeout = timeout
        self.running_time = running_time

        self.mqtt_debug = mqtt_debug
        self.middleware_debug = middleware_debug

        self.download_logs = download_logs

        self.download_log_file_thread_queue = Queue()

    def add_mqtt_client(self, mqtt_client: SoPMQTTClient):
        self.mqtt_client_list.append(mqtt_client)

    def add_ssh_client(self, ssh_client: SoPSSHClient):
        self.ssh_client_list.append(ssh_client)

    def update_middleware_thing_device_list(self):
        device_list: List[SoPDeviceElement] = [
            middleware.device for middleware in self.middleware_list] + [thing.device for thing in self.thing_list]

        for device in device_list:
            if device in self.device_list:
                continue
            self.device_list.append(device)

        # 미들웨어가 같은 디바이스를 가지는 경우 같은 SoPDeviceElement인스턴스를 공유한다.
        for middleware in self.middleware_list:
            for device in self.device_list:
                if device == middleware.device:
                    middleware.device = device

    def init_ssh_client_list(self):

        def task(device: SoPDeviceElement):
            ssh_client = SoPSSHClient(device)
            ssh_client.connect(use_ssh_config=False)

            # 따로 명세되어있지 않고 local network에 있는 경우 사용 가능한 port를 찾는다.
            if device.mqtt_port:
                device.available_port_list = []
            else:
                if '192.168' in device.host or device.host == 'localhost':
                    device.available_port_list = ssh_client.available_port()
                    SOPTEST_LOG_DEBUG(
                        f'Found available port of {device.name}', SoPTestLogLevel.INFO)
                else:
                    raise Exception(
                        f'mqtt_port of {device.name} is not specified.')

            self.add_ssh_client(ssh_client)

        pool_map(task, self.device_list)

        return True

    def init_mqtt_client_list(self):
        for middleware in self.middleware_list:
            if not self.middleware_debug:
                if '192.168' in middleware.device.host or middleware.device.host == 'localhost':
                    picked_port_list = random.sample(
                        middleware.device.available_port_list, 2)
                    middleware.localserver_port = picked_port_list[0]
                    if not middleware.mqtt_port:
                        middleware.mqtt_port = picked_port_list[1]
                else:
                    picked_port_list = []
                # middleware.set_port(*tuple(picked_port_list))
                for picked_port in picked_port_list:
                    middleware.device.available_port_list.remove(picked_port)

            mqtt_client = SoPMQTTClient(middleware, debug=self.mqtt_debug)
            self.add_mqtt_client(mqtt_client)

    def find_ssh_client(self, element: Union[SoPMiddlewareElement, SoPThingElement]) -> SoPSSHClient:
        for ssh_client in self.ssh_client_list:
            if ssh_client.device == element.device:
                return ssh_client
        else:
            return None

    def find_mqtt_client(self, middleware: SoPMiddlewareElement) -> SoPMQTTClient:
        for mqtt_client in self.mqtt_client_list:
            if mqtt_client.middleware == middleware:
                return mqtt_client
        else:
            return None

    def find_mqtt_client_by_client_id(self, client_id: str) -> SoPMQTTClient:
        for mqtt_client in self.mqtt_client_list:
            if mqtt_client.get_client_id() == client_id:
                return mqtt_client
        else:
            return None

    def find_middleware(self, target_middleware_name: str) -> SoPMiddlewareElement:
        for middleware in self.middleware_list:
            if middleware.name == target_middleware_name:
                return middleware
        else:
            return None

    def find_scenario(self, target_scenario_name: str) -> SoPScenarioElement:
        for scenario in self.scenario_list:
            if scenario.name == target_scenario_name:
                return scenario
        else:
            return None

    def find_thing(self, target_thing_name: str) -> SoPThingElement:
        for thing in self.thing_list:
            if thing.name == target_thing_name:
                return thing
        else:
            return None

    def find_service(self, target_service_name: str) -> SoPServiceElement:
        for thing in self.thing_list:
            for service in thing.service_list:
                if service.name == target_service_name:
                    return service
        else:
            return None

    def find_element_middleware(self, element: Union[SoPMiddlewareElement, SoPScenarioElement, SoPThingElement, SoPServiceElement, str]) -> SoPMiddlewareElement:
        if not element:
            raise ValueError('element is None')

        if not isinstance(element, str):
            element_name = element.name
        else:
            element_name = element

        for middleware in self.middleware_list:
            if isinstance(element, SoPMiddlewareElement):
                for child_middleware in middleware.child_middleware_list:
                    if child_middleware.name == element_name:
                        return middleware
            elif isinstance(element, SoPScenarioElement):
                for scenario in middleware.scenario_list:
                    if scenario.name == element_name:
                        return middleware
            elif isinstance(element, SoPThingElement):
                for thing in middleware.thing_list:
                    if thing.name == element_name:
                        return middleware
            elif isinstance(element, SoPServiceElement):
                for thing in middleware.thing_list:
                    for service in thing.service_list:
                        if service.name == element_name:
                            return middleware
        else:
            return None

    def event_listener_start(self):
        self.event_listener_thread.start()

    def event_listener_stop(self):
        self.event_listener_event.set()

    def download_log_file(self):

        def task(middleware: SoPMiddlewareElement):
            ssh_client = self.find_ssh_client(middleware)
            ssh_client.open_sftp()

            remote_home_dir = ssh_client.send_command('cd ~ && pwd')[0]
            target_middleware_log_path = os.path.join(target_simulation_log_path, f'middleware.level{middleware.level}.{middleware.name}')

            file_attr_list = ssh_client._sftp_client.listdir_attr(
                middleware.remote_middleware_config_path)
            for file_attr in file_attr_list:
                ssh_client.get_file(remote_path=os.path.join(middleware.remote_middleware_config_path, file_attr.filename),
                                    local_path=os.path.join(target_middleware_log_path, 'middleware', f'{middleware.name}.cfg'), ext_filter='cfg')
                ssh_client.get_file(remote_path=os.path.join(middleware.remote_middleware_config_path, file_attr.filename),
                                    local_path=os.path.join(target_middleware_log_path, 'middleware', f'{middleware.name}.mosquitto.conf'), ext_filter='conf')

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

        return True

    def event_trigger(self, event: SoPEvent):
        # wait until timestamp is reached
        if event.timestamp == None:
            raise Exception('timestamp is not defined')
        while get_current_time() - self.simulation_start_time < event.timestamp:
            time.sleep(THREAD_TIME_OUT)

        if event.event_type == SoPEventType.DELAY:
            SOPTEST_LOG_DEBUG(
                f'Delay {event.delay} Sec start...', SoPTestLogLevel.INFO, 'yellow')
            self.event_log.append(event)
            time.sleep(event.delay)
        elif event.event_type == SoPEventType.START:
            self.simulation_start_time = get_current_time()
            SOPTEST_LOG_DEBUG(
                f'Simulation Start', SoPTestLogLevel.PASS, 'yellow')
        elif event.event_type == SoPEventType.END:
            self.simulation_duration = get_current_time() - self.simulation_start_time
            SOPTEST_LOG_DEBUG(
                f'Simulation End. duration: {self.simulation_duration:.3f} sec', SoPTestLogLevel.PASS, 'yellow')

            # NOTE: 시뮬레이션이 끝날 때 시나리오를 stop하면 안된다. 끝나는 시점에서 그대로의 시나리오 state를 알아야 한다.
            # for middleware in self.middleware_list:
            #     for scenario in middleware.scenario_list:
            #         SoPThread(name=f'{event.event_type.value}_end',
            #                   target=self.stop_scenario, args=(scenario, self.timeout, )).start()

            self.refresh(timeout=self.timeout,
                         service_check=True, scenario_check=True)

            self.event_listener_stop()
            self.kill_all_simulation_instance()
            # if self.download_logs:
            #     self.download_log_file(
            #         self.middleware_commit_id, self.mosquitto_conf_trim)
            # self.wrapup()
            return True
        else:
            target_element = event.element
            if event.event_type == SoPEventType.MIDDLEWARE_RUN:
                parent_middleware = self.find_element_middleware(
                    target_element)
                if parent_middleware:
                    while not parent_middleware.online:
                        time.sleep(THREAD_TIME_OUT)
                SoPThread(name=f'{event.event_type.value}_{event.element.name}',
                          target=self.run_middleware, args=(target_element, 10, )).start()
                self.subscribe_scenario_finish_topic(middleware=target_element)
            elif event.event_type == SoPEventType.MIDDLEWARE_KILL:
                SoPThread(name=f'{event.event_type.value}_{event.element.name}',
                          target=self.kill_middleware, args=(target_element, )).start()
            elif event.event_type == SoPEventType.THING_RUN:
                while not self.check_middleware_online(target_element):
                    time.sleep(THREAD_TIME_OUT)
                SoPThread(name=f'{event.event_type.value}_{event.element.name}',
                          target=self.run_thing, args=(target_element, 30, )).start()
            elif event.event_type == SoPEventType.THING_KILL:
                SoPThread(name=f'{event.event_type.value}_{event.element.name}',
                          target=self.kill_thing, args=(target_element, )).start()
            elif event.event_type == SoPEventType.THING_UNREGISTER:
                SoPThread(name=f'{event.event_type.value}_{event.element.name}',
                          target=self.unregister_thing, args=(target_element, )).start()
            elif event.event_type == SoPEventType.SCENARIO_VERIFY:
                SoPThread(name=f'{event.event_type.value}_{event.element.name}',
                          target=self.verify_scenario, args=(target_element, self.timeout, )).start()
            elif event.event_type == SoPEventType.SCENARIO_ADD:
                SoPThread(name=f'{event.event_type.value}_{event.element.name}',
                          target=self.add_scenario, args=(target_element, self.timeout, )).start()
            elif event.event_type == SoPEventType.SCENARIO_RUN:
                SoPThread(name=f'{event.event_type.value}_{event.element.name}',
                          target=self.run_scenario, args=(target_element, self.timeout, )).start()
            elif event.event_type == SoPEventType.SCENARIO_STOP:
                SoPThread(name=f'{event.event_type.value}_{event.element.name}',
                          target=self.stop_scenario, args=(target_element, self.timeout, )).start()
            elif event.event_type == SoPEventType.SCENARIO_UPDATE:
                SoPThread(name=f'{event.event_type.value}_{event.element.name}',
                          target=self.update_scenario, args=(target_element, self.timeout, )).start()
            elif event.event_type == SoPEventType.SCENARIO_DELETE:
                SoPThread(name=f'{event.event_type.value}_{event.element.name}',
                          target=self.delete_scenario, args=(target_element, self.timeout, )).start()
            elif event.event_type == SoPEventType.REFRESH:
                self.refresh(timeout=self.timeout,
                             service_check=True, scenario_check=True)
            elif event.event_type == SoPEventType.THING_REGISTER_WAIT:
                self.thing_register_wait()
            elif event.event_type == SoPEventType.SCENARIO_ADD_CHECK:
                self.scenario_add_check(timeout=self.timeout)
            elif event.event_type == SoPEventType.SCENARIO_RUN_CHECK:
                self.scenario_run_check(timeout=self.timeout)
            else:
                raise SOPTEST_LOG_DEBUG(
                    f'Event type is {event.event_type}, but not implemented yet', SoPTestLogLevel.FAIL)

            # if event.event_type in [SoPEventType.MIDDLEWARE_RUN,
            #                         SoPEventType.MIDDLEWARE_KILL,
            #                         SoPEventType.THING_RUN,
            #                         SoPEventType.THING_KILL,
            #                         SoPEventType.THING_UNREGISTER]:
            #     time.sleep(0.1)

    def event_listener(self, stop_event: Event):
        recv_msg = None

        try:
            while not stop_event.wait(THREAD_TIME_OUT / 100):
                for mqtt_client in self.mqtt_client_list:
                    try:
                        recv_msg = mqtt_client.recv_message_queue.get(
                            timeout=THREAD_TIME_OUT / 100)
                        self.on_recv_message(recv_msg)
                    except Empty:
                        recv_msg = None

        except Exception as e:
            stop_event.set()
            print_error(e)
            return False

    ####  middleware   #############################################################################################################

    def run_mosquitto(self, middleware: SoPMiddlewareElement, ssh_client: SoPSSHClient, remote_home_dir: str):
        ssh_client.send_command(
            f'/sbin/mosquitto -c {middleware.remote_mosquitto_conf_file_path.replace("~", remote_home_dir)} -v 2> {middleware.remote_middleware_config_path.replace("~", remote_home_dir)}/{middleware.name}_mosquitto.log &', ignore_result=True)
        target_mosquitto_pid_list = ssh_client.send_command(
            f'netstat -lpn | grep :{middleware.mqtt_port}')
        if len(target_mosquitto_pid_list) > 0:
            return True

    def init_middleware(self, middleware: SoPMiddlewareElement, ssh_client: SoPSSHClient, remote_home_dir: str):
        ssh_client.send_command(
            f'chmod +x {middleware.remote_init_script_file_path.replace("~",remote_home_dir)}; bash {middleware.remote_init_script_file_path.replace("~",remote_home_dir)}')

    def subscribe_scenario_finish_topic(self, middleware: SoPMiddlewareElement):
        mqtt_client = self.find_mqtt_client(middleware)
        while not mqtt_client.is_run:
            time.sleep(THREAD_TIME_OUT)
        mqtt_client.subscribe('SIM/FINISH')

    def run_middleware(self, middleware: SoPMiddlewareElement, timeout: float = 5):

        def check_parent_middleware_online(parent_middleware: SoPMiddlewareElement):
            if parent_middleware:
                while not parent_middleware.online:
                    time.sleep(THREAD_TIME_OUT)

        def middleware_run_command(middleware: SoPMiddlewareElement, remote_home_dir: str):
            log_file_path = ''
            for line in middleware.middleware_cfg.split('\n'):
                if 'log_file_path = ' in line:
                    log_file_path = line.split('"')[1].strip('"')
                    log_file_path = os.path.dirname(log_file_path)
                    break

            user = os.path.basename(remote_home_dir)
            home_dir_append(middleware.remote_middleware_path, user)
            cd_to_config_dir_command = f'cd {os.path.dirname(middleware.remote_middleware_config_path).replace("~", remote_home_dir)}'
            run_command = f'mkdir -p {log_file_path}; cd {home_dir_append(middleware.remote_middleware_path, user)}; ./sopiot_middleware -f {middleware.remote_middleware_cfg_file_path.replace("~", remote_home_dir)} > {log_file_path}/{middleware.name}.stdout 2>&1 &'
            return f'{cd_to_config_dir_command}; {run_command}'

        def check_online(mqtt_client: SoPMQTTClient, timeout: float):
            _, payload, _ = self.publish_and_expect(
                middleware,
                encode_MQTT_message(SoPProtocolType.WebClient.EM_REFRESH.value %
                                    f'{mqtt_client.get_client_id()}_check_online@{middleware.name}', '{}'),
                SoPProtocolType.WebClient.ME_RESULT_SERVICE_LIST.value % (
                    f'{mqtt_client.get_client_id()}_check_online@{middleware.name}'),
                auto_subscribe=True,
                auto_unsubscribe=False,
                timeout=timeout)
            if payload is not None:
                SOPTEST_LOG_DEBUG(
                    f'Middleware {middleware.name} on {middleware.device.host}:{middleware.mqtt_port} - websocket: {middleware.websocket_port} was online!', SoPTestLogLevel.PASS)
                middleware.online = True
                return True
            else:
                # SOPTEST_LOG_DEBUG(
                #     f'Middleware {middleware.name} on {middleware.device.host}:{middleware.mqtt_port} was not online!', 1)
                return False

        def check_online_with_timeout(mqtt_client: SoPMQTTClient, timeout: int, check_interval: float):
            while timeout > 0:
                if check_online(mqtt_client=mqtt_client, timeout=check_interval):
                    return True
                else:
                    timeout -= check_interval
                    time.sleep(check_interval)
            else:
                SOPTEST_LOG_DEBUG(
                    f'[TIMEOUT] Running middleware {middleware.name} was failed...', SoPTestLogLevel.FAIL)
                return False

        ssh_client = self.find_ssh_client(middleware)
        mqtt_client = self.find_mqtt_client(middleware)
        parent_middleware = self.find_element_middleware(middleware)

        SOPTEST_LOG_DEBUG(
            f'Wait for middleware {middleware.name} online', SoPTestLogLevel.INFO, 'yellow')
        check_parent_middleware_online(parent_middleware)

        remote_home_dir = ssh_client.send_command('cd ~ && pwd')[0]
        self.run_mosquitto(middleware, ssh_client, remote_home_dir)
        self.init_middleware(middleware, ssh_client, remote_home_dir)
        mqtt_client.run()
        ssh_client.send_command(middleware_run_command(
            middleware=middleware, remote_home_dir=remote_home_dir), ignore_result=True)

        if not check_online_with_timeout(mqtt_client, timeout=timeout, check_interval=0.5):
            self.kill_middleware(middleware)
            self.run_middleware(middleware, timeout=timeout)

    def kill_middleware(self, middleware: SoPMiddlewareElement):
        ssh_client = self.find_ssh_client(middleware)
        pid_list = self.get_element_proc_pid(ssh_client, middleware)

        if pid_list['middleware_pid_list']:
            for middleware_pid in pid_list['middleware_pid_list']:
                if middleware_pid:
                    ssh_client.send_command(f'kill -9 {middleware_pid}')
        if pid_list['mosquitto_pid_list']:
            for mosquitto_pid in pid_list['mosquitto_pid_list']:
                if mosquitto_pid:
                    ssh_client.send_command(f'kill -9 {mosquitto_pid}')

    ####  thing   #############################################################################################################

    def check_thing_register(self, thing: SoPThingElement, timeout: float = 5):
        _, payload, _ = self.expect(
            thing,
            target_topic=SoPProtocolType.Base.TM_REGISTER.value % thing.name,
            auto_subscribe=True,
            auto_unsubscribe=False,
            timeout=timeout)
        if payload is None:
            SOPTEST_LOG_DEBUG(
                f'TM_REGISTER of thing {thing.name} was not detected (timeout)...', SoPTestLogLevel.FAIL)
            return False

        _, payload, _ = self.expect(
            thing,
            target_topic=SoPProtocolType.Base.MT_RESULT_REGISTER.value % thing.name,
            auto_subscribe=True,
            auto_unsubscribe=False,
            timeout=timeout)
        if payload is None:
            SOPTEST_LOG_DEBUG(
                f'MT_RESULT_REGISTER thing {thing.name} was not detected (timeout)...', SoPTestLogLevel.FAIL)
            return False

        error = int(payload['error'])
        if error in [0, -4]:
            thing.middleware_client_name = payload['middleware_name']
            return True
        elif error == -1:
            SOPTEST_LOG_DEBUG(
                f'Register fail of thing {thing.name} with register packet error... error code: {payload["error"]}', SoPTestLogLevel.FAIL)
            return False

    def subscribe_thing_topic(self, thing: SoPThingElement, mqtt_client: SoPMQTTClient):
        for service in thing.service_list:
            mqtt_client.subscribe([SoPProtocolType.Base.MT_EXECUTE.value % (service.name, thing.name, thing.middleware_client_name, '#'),
                                   (SoPProtocolType.Base.MT_EXECUTE.value % (
                                       service.name, thing.name, '', '')).rstrip('/'),
                                   SoPProtocolType.Base.TM_RESULT_EXECUTE.value % (
                service.name, thing.name, '+', '#'),
                (SoPProtocolType.Base.TM_RESULT_EXECUTE.value % (service.name, thing.name, '', '')).rstrip('/')])
            if thing.is_super:
                mqtt_client.subscribe([
                    SoPProtocolType.Super.MS_EXECUTE.value % (
                        service.name, thing.name, thing.middleware_client_name, '#'),
                    SoPProtocolType.Super.SM_EXECUTE.value % (
                        '+', '+', '+', '#'),
                    SoPProtocolType.Super.MS_RESULT_EXECUTE.value % (
                        '+', '+', '+', '#'),
                    SoPProtocolType.Super.SM_RESULT_EXECUTE.value % (
                        service.name, thing.name, thing.middleware_client_name, '#'),
                    SoPProtocolType.Super.MS_SCHEDULE.value % (
                        service.name, thing.name, thing.middleware_client_name, '#'),
                    SoPProtocolType.Super.SM_SCHEDULE.value % (
                        '+', '+', '+', '#'),
                    SoPProtocolType.Super.MS_RESULT_SCHEDULE.value % (
                        '+', '+', '+', '#'),
                    SoPProtocolType.Super.SM_RESULT_SCHEDULE.value % (
                        service.name, thing.name, thing.middleware_client_name, '#')])
        # for value in self._value_list:
        #     mqtt_client.subscribe([SoPProtocolType.Default.TM_VALUE_PUBLISH.value % (thing.name, value['name']),
        #                                         SoPProtocolType.Default.TM_VALUE_PUBLISH_OLD.value % (thing.name, value['name'])])

    def run_thing(self, thing: SoPThingElement, timeout: float = 5):
        # SOPTEST_LOG_DEBUG(
        #     f'Thing {thing.name} run start...', SoPTestLogLevel.PASS)
        middleware = self.find_element_middleware(thing)
        ssh_client = self.find_ssh_client(thing)
        mqtt_client = self.find_mqtt_client(middleware)

        target_topic_list = [SoPProtocolType.Base.TM_REGISTER.value % thing.name,
                             SoPProtocolType.Base.TM_UNREGISTER.value % thing.name,
                             SoPProtocolType.Base.MT_RESULT_REGISTER.value % thing.name,
                             SoPProtocolType.Base.MT_RESULT_UNREGISTER.value % thing.name]
        mqtt_client.subscribe(target_topic_list)

        result = ssh_client.send_command('cd ~ && pwd')
        thing_cd_command = f'cd {os.path.dirname(thing.remote_thing_file_path)}'
        thing_run_command = f'{thing_cd_command}; python {thing.remote_thing_file_path.replace("~", result[0])} -n {thing.name} -ip {mqtt_client.host if not thing.is_super else "localhost"} -p {mqtt_client.port} -ac {thing.alive_cycle} --retry_register > /dev/null 2>&1 & echo $!'
        # print(thing_run_command.split('>')[0].strip())
        result = ssh_client.send_command(thing_run_command)
        thing.pid = result[0]

        if self.check_thing_register(thing, timeout=timeout):
            # SOPTEST_LOG_DEBUG(
            #     f' Thing Register is complete. Thing: {thing.name}, Middleware: {middelware.name}', SoPTestLogLevel.PASS)
            self.subscribe_thing_topic(thing, mqtt_client)
            thing.registered = True
            return True
        else:
            thing.registered = False
            self.kill_thing(thing)
            self.run_thing(thing, timeout=timeout)

    def unregister_thing(self, thing: SoPThingElement):
        SOPTEST_LOG_DEBUG(
            f'Unregister Thing {thing.name}...', SoPTestLogLevel.INFO, color='yellow')
        ssh_client = self.find_ssh_client(thing)
        ssh_client.send_command(f'kill -2 {thing.pid}')

    def kill_thing(self, thing: SoPThingElement):
        SOPTEST_LOG_DEBUG(
            f'Kill Thing {thing.name}...', SoPTestLogLevel.INFO, color='yellow')
        ssh_client = self.find_ssh_client(thing)
        ssh_client.send_command(f'kill -9 {thing.pid}')

    ####  scenario   #############################################################################################################

    def refresh(self, timeout: float, service_check: bool = False, scenario_check: bool = False):

        def task(middleware: SoPMiddlewareElement):
            SOPTEST_LOG_DEBUG(
                f'Refresh Start... middleware: {middleware.name}', SoPTestLogLevel.INFO)

            if service_check:
                whole_service_info = self.get_whole_service_list_info(
                    middleware, timeout=timeout)
                if whole_service_info is False:
                    return False
            if scenario_check:
                whole_scenario_info_list: List[SoPScenarioInfo] = self.get_whole_scenario_info(
                    middleware, timeout=timeout)
                if whole_scenario_info_list is False:
                    return False

            # scenario service validation check
            whole_service_name_info = [service['name']
                                       for service in whole_service_info]
            for scenario in middleware.scenario_list:
                target_scenario_service_name_list = [
                    service.name for service in scenario.service_list]

                if set(target_scenario_service_name_list).issubset(set(whole_service_name_info)):
                    for thing in middleware.thing_list:
                        thing: SoPThingElement
                        mqtt_client = self.find_mqtt_client(middleware)
                        self.subscribe_thing_topic(thing, mqtt_client)
                        thing.registered = True

                    scenario.service_check = True
                else:
                    SOPTEST_LOG_DEBUG(
                        f'Service check Fail... level: {middleware.level}, middleware: {middleware.name}, scenario: {scenario.name}', SoPTestLogLevel.WARN)
                    # scenario.service_check = False

            # scenario add check
            for scenario in middleware.scenario_list:
                for scenario_info in whole_scenario_info_list:
                    scenario_info: SoPScenarioInfo
                    if scenario.name == scenario_info.name:
                        scenario.schedule_success = True
                        scenario.schedule_timeout = False
                        scenario.state = scenario_info.state
                        break
                else:
                    SOPTEST_LOG_DEBUG(
                        f'Scenario {scenario.name} is not in scenario list of {middleware.name}...', SoPTestLogLevel.WARN)

            SOPTEST_LOG_DEBUG(
                f'Refresh Success! middleware: {middleware.name}', SoPTestLogLevel.INFO)

        pool_map(task, self.middleware_list)

        return True

    def thing_register_wait(self):
        while not all([thing.registered for thing in self.thing_list]):
            time.sleep(THREAD_TIME_OUT)
        SOPTEST_LOG_DEBUG(
            f'All thing register is complete!...', SoPTestLogLevel.INFO)

        return True

    def scenario_add_check(self, timeout: float):
        while not all([scenario.schedule_success for scenario in self.scenario_list]):
            time.sleep(THREAD_TIME_OUT)
        SOPTEST_LOG_DEBUG(
            f'All scenario Add is complete!...', SoPTestLogLevel.INFO)

        return True

    def scenario_run_check(self, timeout: float):
        for middleware in self.middleware_list:
            whole_scenario_info_list: List[SoPScenarioInfo] = self.get_whole_scenario_info(
                middleware, timeout=timeout)
            if whole_scenario_info_list is False:
                return False

            # scenario run check
            for scenario in middleware.scenario_list:
                for scenario_info in whole_scenario_info_list:
                    scenario_info: SoPScenarioInfo
                    if scenario.name == scenario_info.name:
                        if scenario.state in [SoPScenarioState.RUNNING, SoPScenarioState.EXECUTING]:
                            scenario.schedule_success = True
                            scenario.state = scenario_info.state
                            break
                        else:
                            SOPTEST_LOG_DEBUG(
                                f'Scenario {scenario.name} is not in RUN state...', SoPTestLogLevel.WARN)
                else:
                    SOPTEST_LOG_DEBUG(
                        f'[SCENARIO RUN CHECK] Scenario {scenario.name} is not in scenario list of {middleware.name}...', SoPTestLogLevel.WARN)

            SOPTEST_LOG_DEBUG(
                f'Scenario Run Check Success! middleware: {middleware.name}', SoPTestLogLevel.PASS)

        return True

    def verify_scenario(self, scenario: SoPScenarioElement, timeout: float = 5):
        middleware = self.find_element_middleware(scenario)
        mqtt_client = self.find_mqtt_client(middleware)

        trigger_topic = SoPProtocolType.WebClient.EM_VERIFY_SCENARIO.value % mqtt_client.get_client_id()
        trigger_payload = json_string_to_dict(
            dict(name=scenario.name, text=scenario.scenario_code()))
        trigger_message = encode_MQTT_message(trigger_topic, trigger_payload)
        target_topic = SoPProtocolType.WebClient.ME_RESULT_VERIFY_SCENARIO.value % mqtt_client.get_client_id()

        mqtt_client.subscribe(trigger_topic)
        _, payload, _ = self.publish_and_expect(
            scenario,
            trigger_message,
            target_topic,
            auto_unsubscribe=False,
            timeout=timeout)

        if check_result_payload(payload) == None:
            SOPTEST_LOG_DEBUG(
                f'{SoPElementType.SCENARIO.value} {scenario.name} {SoPElementActionType.SCENARIO_VERIFY.value} failed...', SoPTestLogLevel.FAIL)
        return self

    def add_scenario(self, scenario: SoPScenarioElement, timeout: float = 5, check_interval: float = 1.0):
        middleware = self.find_element_middleware(scenario)
        mqtt_client = self.find_mqtt_client(middleware)

        trigger_topic = SoPProtocolType.WebClient.EM_ADD_SCENARIO.value % mqtt_client.get_client_id()
        trigger_payload = json_string_to_dict(
            dict(name=scenario.name, text=scenario.scenario_code()))
        trigger_message = encode_MQTT_message(trigger_topic, trigger_payload)
        target_topic = SoPProtocolType.WebClient.ME_RESULT_ADD_SCENARIO.value % mqtt_client.get_client_id()

        mqtt_client.subscribe(trigger_topic)
        _, payload, _ = self.publish_and_expect(
            scenario,
            trigger_message,
            target_topic,
            auto_subscribe=True,
            auto_unsubscribe=False,
            timeout=timeout)

        if check_result_payload(payload) == None:
            SOPTEST_LOG_DEBUG(
                f'{SoPElementType.SCENARIO.value} {scenario.name} {SoPElementActionType.SCENARIO_ADD.value} failed...', SoPTestLogLevel.FAIL)
            SOPTEST_LOG_DEBUG(
                f'==== Fault Scenario ====', SoPTestLogLevel.FAIL)
            SOPTEST_LOG_DEBUG(
                f'name: {scenario.name}', SoPTestLogLevel.FAIL)
            SOPTEST_LOG_DEBUG(
                f'code: \n{scenario.scenario_code()}', SoPTestLogLevel.FAIL)
            scenario.schedule_timeout = True
            return True

    def run_scenario(self, scenario: SoPScenarioElement, timeout: float = 5):
        # NOTE: 이미 add_scenario를 통해 시나리오가 정상적으로 init되어있는 것이 확인되어있는 상태이므로 다시 시나리오상태를 확인할 필요는 없다.

        if not scenario.state:
            SOPTEST_LOG_DEBUG(
                f'Scenario {scenario.name} state is None... Check it to TIMEOUT. Skip scenario run...', SoPTestLogLevel.WARN)
            scenario.schedule_timeout = True
            return False
        if not scenario.schedule_success:
            SOPTEST_LOG_DEBUG(
                f'Scenario {scenario.name} is not initialized. Skip scenario run...', SoPTestLogLevel.WARN)
            return False
        if not scenario.service_check:
            SOPTEST_LOG_DEBUG(
                f'Scenario {scenario.name} is not service validated. Skip scenario run...', SoPTestLogLevel.FAIL)
            scenario.schedule_timeout = True
            return False

        middleware = self.find_element_middleware(scenario)
        mqtt_client = self.find_mqtt_client(middleware)

        trigger_topic = SoPProtocolType.WebClient.EM_RUN_SCENARIO.value % mqtt_client.get_client_id()
        trigger_payload = json_string_to_dict(
            dict(name=scenario.name, text=scenario.scenario_code()))
        trigger_message = encode_MQTT_message(trigger_topic, trigger_payload)
        target_topic = SoPProtocolType.WebClient.ME_RESULT_RUN_SCENARIO.value % mqtt_client.get_client_id()

        mqtt_client.subscribe(trigger_topic)
        _, payload, _ = self.publish_and_expect(
            scenario,
            trigger_message,
            target_topic,
            auto_subscribe=True,
            auto_unsubscribe=False,
            timeout=timeout)

        if check_result_payload(payload) == None:
            SOPTEST_LOG_DEBUG(
                f'{SoPElementType.SCENARIO.value} {scenario.name} {SoPElementActionType.SCENARIO_RUN.value} failed...', SoPTestLogLevel.FAIL)
        return self

    def stop_scenario(self, scenario: SoPScenarioElement, timeout: float = 5):
        middleware = self.find_element_middleware(scenario)
        mqtt_client = self.find_mqtt_client(middleware)

        trigger_topic = SoPProtocolType.WebClient.EM_STOP_SCENARIO.value % mqtt_client.get_client_id()
        trigger_payload = json_string_to_dict(
            dict(name=scenario.name, text=scenario.scenario_code()))
        trigger_message = encode_MQTT_message(trigger_topic, trigger_payload)
        target_topic = SoPProtocolType.WebClient.ME_RESULT_STOP_SCENARIO.value % mqtt_client.get_client_id()

        # NOTE: 시나리오의 상태를 확인할 필요 없이 바로 stop을 해도 먹히는지 확인이 필요
        # if not self.get_scenario_state(scenario, timeout=timeout) in [SoPScenarioState.RUNNING, SoPScenarioState.EXECUTING]:
        #     SOPTEST_LOG_DEBUG(
        #         f'Fail to stop scenario {scenario.name} - state: {scenario.state.value}', SoPTestLogLevel.FAIL)
        #     return False

        mqtt_client.subscribe(trigger_topic)
        _, payload, _ = self.publish_and_expect(
            scenario,
            trigger_message,
            target_topic,
            auto_subscribe=True,
            auto_unsubscribe=False,
            timeout=timeout)

        if check_result_payload(payload) == None:
            SOPTEST_LOG_DEBUG(
                f'{SoPElementType.SCENARIO.value} {scenario.name} {SoPElementActionType.SCENARIO_STOP.value} failed...', SoPTestLogLevel.FAIL)
        return self

    def update_scenario(self, scenario: SoPScenarioElement, timeout: float = 5):
        middleware = self.find_element_middleware(scenario)
        mqtt_client = self.find_mqtt_client(middleware)

        trigger_topic = SoPProtocolType.WebClient.EM_UPDATE_SCENARIO.value % mqtt_client.get_client_id()
        trigger_payload = json_string_to_dict(
            dict(name=scenario.name, text=scenario.scenario_code()))
        trigger_message = encode_MQTT_message(trigger_topic, trigger_payload)
        target_topic = SoPProtocolType.WebClient.ME_RESULT_UPDATE_SCENARIO.value % mqtt_client.get_client_id()

        # NOTE: 시나리오의 상태를 확인할 필요 없이 바로 update을 해도 먹히는지 확인이 필요
        # if not self.get_scenario_state(scenario, timeout=timeout) in [SoPScenarioState.STUCKED]:
        #     SOPTEST_LOG_DEBUG(
        #         f'Fail to stop scenario {scenario.name} - state: {scenario.state.value}', SoPTestLogLevel.FAIL)
        #     return False

        mqtt_client.subscribe(trigger_topic)
        _, payload, _ = self.publish_and_expect(
            scenario,
            trigger_message,
            target_topic,
            auto_subscribe=True,
            auto_unsubscribe=False,
            timeout=timeout)

        if check_result_payload(payload) == None:
            SOPTEST_LOG_DEBUG(
                f'{SoPElementType.SCENARIO.value} {scenario.name} {SoPElementActionType.SCENARIO_UPDATE.value} failed...', SoPTestLogLevel.FAIL)
        return self

    def delete_scenario(self, scenario: SoPScenarioElement, timeout: float = 5):
        middleware = self.find_element_middleware(scenario)
        mqtt_client = self.find_mqtt_client(middleware)

        trigger_topic = SoPProtocolType.WebClient.EM_DELETE_SCENARIO.value % mqtt_client.get_client_id()
        trigger_payload = json_string_to_dict(
            dict(name=scenario.name, text=scenario.scenario_code()))
        trigger_message = encode_MQTT_message(trigger_topic, trigger_payload)
        target_topic = SoPProtocolType.WebClient.ME_RESULT_DELETE_SCENARIO.value % mqtt_client.get_client_id()

        # NOTE: 시나리오의 상태를 확인할 필요 없이 바로 delete를 해도 먹히는지 확인이 필요
        # if not self.get_scenario_state(scenario, timeout=timeout) in [SoPScenarioState.RUNNING, SoPScenarioState.EXECUTING]:
        #     SOPTEST_LOG_DEBUG(
        #         f'Fail to stop scenario {scenario.name} - state: {scenario.state.value}', SoPTestLogLevel.FAIL)
        #     return False
        mqtt_client.subscribe(trigger_topic)
        _, payload, _ = self.publish_and_expect(
            scenario,
            trigger_message,
            target_topic,
            auto_subscribe=True,
            auto_unsubscribe=False,
            timeout=timeout)

        if check_result_payload(payload) == None:
            SOPTEST_LOG_DEBUG(
                f'{SoPElementType.SCENARIO.value} {scenario.name} {SoPElementActionType.SCENARIO_DELETE.value} failed...', SoPTestLogLevel.FAIL)
        return self

    def get_whole_scenario_info(self, middleware: SoPMiddlewareElement, timeout: float) -> Union[List[SoPScenarioInfo], bool]:
        mqtt_client = self.find_mqtt_client(middleware)

        _, payload, _ = self.publish_and_expect(
            middleware,
            encode_MQTT_message(
                SoPProtocolType.WebClient.EM_REFRESH.value % f'{mqtt_client.get_client_id()}_get_whole_scenario_info@{middleware.name}', '{}'),
            SoPProtocolType.WebClient.ME_RESULT_SCENARIO_LIST.value % f'{mqtt_client.get_client_id()}_get_whole_scenario_info@{middleware.name}',
            auto_subscribe=True,
            auto_unsubscribe=False,
            timeout=timeout)

        if payload is not None:
            return [SoPScenarioInfo(id=scenario_info['id'],
                                    name=scenario_info['name'],
                                    state=SoPScenarioState.get(
                                        scenario_info['state']),
                                    code=scenario_info['contents'],
                                    schedule_info=scenario_info['scheduleInfo']) for scenario_info in payload['scenarios']]
        else:
            SOPTEST_LOG_DEBUG(
                f'Get whole scenario info of {middleware.name} failed -> MQTT timeout...', SoPTestLogLevel.FAIL)
            return False

    def get_whole_service_list_info(self, middleware: SoPMiddlewareElement, timeout: float) -> List[dict]:
        mqtt_client = self.find_mqtt_client(middleware)

        _, payload, _ = self.publish_and_expect(
            middleware,
            encode_MQTT_message(
                SoPProtocolType.WebClient.EM_REFRESH.value % f'{mqtt_client.get_client_id()}_get_whole_service_list_info@{middleware.name}', '{}'),
            SoPProtocolType.WebClient.ME_RESULT_SERVICE_LIST.value % f'{mqtt_client.get_client_id()}_get_whole_service_list_info@{middleware.name}',
            auto_subscribe=True,
            auto_unsubscribe=False,
            timeout=timeout)

        if payload is not None:
            whole_service_info = []
            for service in payload['services']:
                if service['hierarchy'] == 'local' or service['hierarchy'] == 'parent':
                    for thing in service['things']:
                        for service in thing['functions']:
                            whole_service_info.append(service)
            return whole_service_info
        else:
            SOPTEST_LOG_DEBUG(
                f'Get whole service list info of {middleware.name} failed -> MQTT timeout...', SoPTestLogLevel.FAIL)
            return False

    #### kill ##########################################################################################################################

    def get_proc_pid(self, ssh_client: SoPSSHClient, proc_name: str, port: int = None) -> Union[List[int], bool]:
        result: List[str] = ssh_client.send_command(
            f"lsof -i :{port} | grep {proc_name[:9]}")
        pid_list = list(set([line.split()[1] for line in result]))
        if len(pid_list) == 0:
            return False
        elif len(pid_list) == 1:
            return pid_list

    def get_element_proc_pid(self, ssh_client: SoPSSHClient, element: SoPElement) -> List[int]:
        if isinstance(element, SoPMiddlewareElement):
            middleware_pid_list = self.get_proc_pid(
                ssh_client, 'sopiot_middleware', element.mqtt_port)
            mosquitto_pid_list = self.get_proc_pid(
                ssh_client, 'mosquitto', element.mqtt_port)
            return dict(middleware_pid_list=middleware_pid_list, mosquitto_pid_list=mosquitto_pid_list)
        elif isinstance(element, SoPThingElement):
            middleware = self.find_element_middleware(element)
            thing_pid_list = self.get_proc_pid(
                ssh_client, 'python', middleware.mqtt_port)
            return dict(thing_pid_list=thing_pid_list)

    def kill_all_middleware(self):
        SOPTEST_LOG_DEBUG(f'Kill all middleware...',
                          SoPTestLogLevel.INFO, 'red')
        for middleware in self.middleware_list:
            ssh_client = self.find_ssh_client(middleware)
            ssh_client.send_command('pidof sopiot_middleware | xargs kill -9')
            ssh_client.send_command('pidof mosquitto | xargs kill -9')

    def kill_all_thing(self):
        SOPTEST_LOG_DEBUG(f'Kill all python instance...',
                          SoPTestLogLevel.INFO, 'red')

        self_pid = os.getpid()

        for ssh_client in self.ssh_client_list:
            result = ssh_client.send_command(
                f"ps -ef | grep python | grep _thing_ | grep -v grep | awk '{{print $2}}'")

            for pid in result:
                if pid == self_pid:
                    continue
                result = ssh_client.send_command(f'kill -9 {pid}')

    def kill_all_ssh_client(self):
        SOPTEST_LOG_DEBUG(f'Kill all ssh client...',
                          SoPTestLogLevel.INFO, 'red')
        for ssh_client in self.ssh_client_list:
            ssh_client.disconnect()
            del ssh_client

    def kill_all_mqtt_client(self):
        SOPTEST_LOG_DEBUG(f'Kill all mqtt client...',
                          SoPTestLogLevel.INFO, 'red')
        for mqtt_client in self.mqtt_client_list:
            mqtt_client.stop()
            del mqtt_client

    def kill_all_simulation_instance(self):
        SOPTEST_LOG_DEBUG(f'Kill simulation instance...',
                          SoPTestLogLevel.INFO, 'red')

        if not self.middleware_debug:
            self.kill_all_middleware()
        self.kill_all_thing()

    def wrapup(self):
        self.kill_all_ssh_client()
        self.kill_all_mqtt_client()

    def handler(self, signum, frame):
        pass  # 아무 작업도 하지 않음

    def remove_all_remote_simulation_file(self):
        finished_ssh_client_list = []
        for middleware in self.middleware_list:
            ssh_client = self.find_ssh_client(middleware)
            remote_home_dir = ssh_client.send_command('cd ~ && pwd')[0]
            if ssh_client in finished_ssh_client_list:
                continue
            ssh_client.send_command(
                f'rm -r {middleware.remote_middleware_config_path}')
            ssh_client.send_command(
                f'rm -r {middleware.remote_middleware_config_path}')
            ssh_client.send_command(
                f'rm -r {remote_home_dir}/simulation_log')
            finished_ssh_client_list.append(ssh_client)

        finished_ssh_client_list = []
        for thing in self.thing_list:
            ssh_client = self.find_ssh_client(thing)
            if ssh_client in finished_ssh_client_list:
                continue
            ssh_client.send_command(
                f'rm -r {os.path.dirname(thing.remote_thing_file_path)}')
            ssh_client.send_command(
                f'rm -r {os.path.dirname(os.path.dirname(thing.remote_thing_file_path))}')
            finished_ssh_client_list.append(ssh_client)

    #### expect ##########################################################################################################################

    def expect(self, element: SoPElement, target_topic: str = None, auto_subscribe: bool = True, auto_unsubscribe: bool = False, timeout: int = 5) -> Union[Tuple[str, dict], str]:
        cur_time = get_current_time()
        if isinstance(element, SoPMiddlewareElement):
            target_middleware = element
        else:
            target_middleware = self.find_element_middleware(element)

        target_middleware: SoPMiddlewareElement
        mqtt_client = self.find_mqtt_client(target_middleware)

        if not mqtt_client.is_run:
            raise Exception(
                f'{target_middleware.name} mqtt_client is not running...')

        try:
            if auto_subscribe:
                mqtt_client.subscribe(target_topic)

            while True:
                if get_current_time() - cur_time > timeout:
                    raise Empty('Timeout')

                topic, payload, timestamp = decode_MQTT_message(
                    element.recv_queue.get(timeout=timeout))

                if target_topic:
                    topic_slice = topic.split('/')
                    target_topic_slice = target_topic.split('/')
                    for i in range(len(target_topic_slice)):
                        if target_topic_slice[i] not in ['#', '+'] and target_topic_slice[i] != topic_slice[i]:
                            break
                    else:
                        return topic, payload, timestamp
                else:
                    element.recv_queue.put(
                        encode_MQTT_message(topic, payload, timestamp))
        except Empty as e:
            # SOPLOG_DEBUG(f'SoPMQTTClient Timeout for {target_topic}', 'red')
            return None, None, None
        except Exception as e:
            raise e
        finally:
            if auto_unsubscribe:
                if target_topic:
                    mqtt_client.unsubscribe(target_topic)

    def publish_and_expect(self, element: SoPElement, trigger_msg: mqtt.MQTTMessage = None, target_topic: str = None, auto_subscribe: bool = True, auto_unsubscribe: bool = False, timeout: int = 5):
        if isinstance(element, SoPMiddlewareElement):
            target_middleware = element
        else:
            target_middleware = self.find_element_middleware(element)

        target_middleware: SoPMiddlewareElement
        mqtt_client = self.find_mqtt_client(target_middleware)

        if not mqtt_client.is_run:
            mqtt_client.run()

        if auto_subscribe:
            mqtt_client.subscribe(target_topic)
        trigger_topic, trigger_payload, timestamp = decode_MQTT_message(
            trigger_msg, mode=str)
        mqtt_client.publish(trigger_topic, trigger_payload, retain=False)

        ret = self.expect(element, target_topic,
                          auto_subscribe, auto_unsubscribe, timeout)
        return ret

    def command_and_expect(self, element: SoPElement, trigger_command: Union[List[str], str] = None, target_topic: str = None,
                           auto_subscribe: bool = True, auto_unsubscribe: bool = False, timeout: int = 5):
        if isinstance(element, SoPMiddlewareElement):
            target_middleware = element
        else:
            target_middleware = self.find_element_middleware(element)

        target_middleware: SoPMiddlewareElement
        mqtt_client = self.find_mqtt_client(target_middleware)
        ssh_client = self.find_ssh_client(target_middleware)

        if not mqtt_client.is_run:
            mqtt_client.run()

        if auto_subscribe:
            mqtt_client.subscribe(target_topic)
        if isinstance(trigger_command, list):
            for command in trigger_command:
                ssh_client.send_command(command)
        else:
            ssh_client.send_command(trigger_command)
        ret = self.expect(element, target_topic,
                          auto_subscribe, auto_unsubscribe, timeout)
        return ret

    def check_middleware_online(self, thing: SoPThingElement):
        middleware = self.find_element_middleware(thing)
        return middleware.online

    #### on_recv_message ##########################################################################################################################

    def on_recv_message(self, msg: mqtt.MQTTMessage):
        topic, payload, timestamp = decode_MQTT_message(msg)
        timestamp = get_current_time() - self.simulation_start_time

        return_type = SoPType.get(payload.get('return_type', None))
        return_value = payload.get('return_value', None)
        error_type = SoPErrorType.get(payload.get('error', None))

        # FIXME: change it to 'scenario' after middleware updated
        scenario_name = payload.get('name', None)
        scenario_name = payload.get(
            'scenario', None) if not scenario_name else scenario_name

        if SoPProtocolType.WebClient.ME_RESULT_SCENARIO_LIST.get_prefix() in topic:
            client_id = topic.split('/')[3]

            if 'get_whole_scenario_info' in client_id:
                middleware_name = client_id.split('@')[1]

                middleware = self.find_middleware(middleware_name)
                middleware.recv_queue.put(msg)
        elif SoPProtocolType.WebClient.ME_RESULT_SERVICE_LIST.get_prefix() in topic:
            client_id = topic.split('/')[3]

            if 'get_whole_service_list_info' in client_id:
                middleware_name = client_id.split('@')[1]

                middleware = self.find_middleware(middleware_name)
                middleware.recv_queue.put(msg)
            elif 'check_online' in client_id:
                middleware_name = client_id.split('@')[1]

                middleware = self.find_middleware(middleware_name)
                middleware.recv_queue.put(msg)
        elif SoPProtocolType.Base.TM_REGISTER.get_prefix() in topic:
            thing_name = topic.split('/')[2]

            thing = self.find_thing(thing_name)
            middleware = self.find_element_middleware(thing)
            thing.recv_queue.put(msg)
            self.event_log.append(SoPEvent(
                event_type=SoPEventType.THING_REGISTER, middleware_element=middleware, thing_element=thing, timestamp=timestamp, duration=0))
        elif SoPProtocolType.Base.MT_RESULT_REGISTER.get_prefix() in topic:
            thing_name = topic.split('/')[3]

            thing = self.find_thing(thing_name)
            middleware = self.find_element_middleware(thing)
            thing.registered = True
            thing.recv_queue.put(msg)
            for event in list(reversed(self.event_log)):
                if event.middleware_element == middleware and event.thing_element == thing and event.event_type == SoPEventType.THING_REGISTER:
                    event.duration = timestamp - event.timestamp
                    event.error = error_type

                    progress = [thing.registered for thing in self.thing_list].count(
                        True) / len(self.thing_list)
                    color = 'red' if event.error == SoPErrorType.FAIL else 'green'
                    SOPTEST_LOG_DEBUG(
                        f'[REGISTER] thing: {thing_name} duration: {event.duration:0.4f}', SoPTestLogLevel.INFO, progress=progress, color=color)
                    break
        elif SoPProtocolType.Base.TM_UNREGISTER.get_prefix() in topic:
            thing_name = topic.split('/')[2]

            thing = self.find_thing(thing_name)
            middleware = self.find_element_middleware(thing)
            thing.recv_queue.put(msg)
            self.event_log.append(SoPEvent(
                event_type=SoPEventType.THING_UNREGISTER, middleware_element=middleware, thing_element=thing, timestamp=timestamp, duration=0))
        elif SoPProtocolType.Base.MT_RESULT_UNREGISTER.get_prefix() in topic:
            thing_name = topic.split('/')[3]

            thing = self.find_thing(thing_name)
            middleware = self.find_element_middleware(thing)
            thing.recv_queue.put(msg)
            for event in list(reversed(self.event_log)):
                if event.middleware_element == middleware and event.thing_element == thing and event.event_type == SoPEventType.THING_UNREGISTER:
                    event.duration = timestamp - event.timestamp
                    event.error = error_type
                    SOPTEST_LOG_DEBUG(
                        f'[UNREGISTER] thing: {thing_name} duration: {event.duration:0.4f}', SoPTestLogLevel.INFO)
                    break
        elif SoPProtocolType.Base.MT_EXECUTE.get_prefix() in topic:
            function_name = topic.split('/')[2]
            thing_name = topic.split('/')[3]

            thing = self.find_thing(thing_name)
            middleware = self.find_element_middleware(thing)
            scenario = self.find_scenario(scenario_name)
            service = thing.find_service_by_name(function_name)

            if len(topic.split('/')) > 4:
                # middleware_name = topic.split('/')[4]
                # Request_ID = RequesterMiddlewareName_SuperThing@SuperFunction@SubrequestOrder
                request_ID = topic.split('/')[5]

                requester_middleware_name = request_ID.split('@')[0]
                super_thing_name = request_ID.split('@')[1]
                super_function_name = request_ID.split('@')[2]
                # subrequest_order = request_ID.split('@')[3]
            else:
                super_thing_name = None
                super_function_name = None
                requester_middleware_name = None

            if requester_middleware_name is not None:
                event_type = SoPEventType.SUB_FUNCTION_EXECUTE
            else:
                event_type = SoPEventType.FUNCTION_EXECUTE
            self.event_log.append(SoPEvent(
                event_type=event_type, middleware_element=middleware, thing_element=thing, service_element=service, scenario_element=scenario,
                timestamp=timestamp, duration=0, requester_middleware_name=requester_middleware_name, super_thing_name=super_thing_name, super_function_name=super_function_name))
        elif SoPProtocolType.Base.TM_RESULT_EXECUTE.get_prefix() in topic:
            function_name = topic.split('/')[3]
            thing_name = topic.split('/')[4]

            thing = self.find_thing(thing_name)
            middleware = self.find_element_middleware(thing)
            scenario = self.find_scenario(scenario_name)
            service = thing.find_service_by_name(function_name)

            if len(topic.split('/')) > 5:
                # middleware_name = topic.split('/')[5]
                request_ID = topic.split('/')[6]

                requester_middleware_name = request_ID.split('@')[0]
                super_thing_name = request_ID.split('@')[1]
                super_function_name = request_ID.split('@')[2]
                # subrequest_order = request_ID.split('@')[3]
            else:
                super_thing_name = None
                super_function_name = None
                requester_middleware_name = None

            for event in list(reversed(self.event_log)):
                if event.middleware_element == middleware and event.thing_element == thing and event.service_element == service and event.scenario_element == scenario and event.requester_middleware_name == requester_middleware_name and event.event_type in [SoPEventType.FUNCTION_EXECUTE, SoPEventType.SUB_FUNCTION_EXECUTE]:
                    event.duration = timestamp - event.timestamp
                    event.error = error_type
                    event.return_type = return_type
                    event.return_value = return_value
                    event.requester_middleware_name = requester_middleware_name

                    passed_time = get_current_time() - self.simulation_start_time
                    progress = passed_time / self.running_time

                    if event.event_type == SoPEventType.SUB_FUNCTION_EXECUTE:
                        color = 'light_magenta' if event.error == SoPErrorType.FAIL else 'light_cyan'
                        SOPTEST_LOG_DEBUG(
                            f'[EXECUTE_SUB] thing: {thing_name} function: {function_name} scenario: {scenario_name} requester_middleware_name: {requester_middleware_name} duration: {event.duration:0.4f} return value: {return_value} - {return_type.value} error:{event.error.value}', SoPTestLogLevel.PASS, progress=progress, color=color)
                    elif event.event_type == SoPEventType.FUNCTION_EXECUTE:
                        color = 'red' if event.error == SoPErrorType.FAIL else 'green'
                        SOPTEST_LOG_DEBUG(
                            f'[EXECUTE] thing: {thing_name} function: {function_name} scenario: {scenario_name} requester_middleware_name: {requester_middleware_name} duration: {event.duration:0.4f} return value: {return_value} - {return_type.value} error:{event.error.value}', SoPTestLogLevel.PASS, progress=progress, color=color)
                    break
        elif SoPProtocolType.WebClient.EM_VERIFY_SCENARIO.get_prefix() in topic:
            scenario = self.find_scenario(scenario_name)
            middleware = self.find_element_middleware(scenario)

            self.event_log.append(SoPEvent(
                event_type=SoPEventType.SCENARIO_VERIFY, middleware_element=middleware, scenario_element=scenario, timestamp=timestamp, duration=0))
        elif SoPProtocolType.WebClient.ME_RESULT_VERIFY_SCENARIO.get_prefix() in topic:
            scenario = self.find_scenario(scenario_name)
            middleware = self.find_element_middleware(scenario)

            scenario.recv_queue.put(msg)
            for event in list(reversed(self.event_log)):
                if event.middleware_element == middleware and event.scenario_element == scenario and event.event_type == SoPEventType.SCENARIO_VERIFY:
                    event.duration = timestamp - event.timestamp
                    event.error = error_type
                    SOPTEST_LOG_DEBUG(
                        f'[SCENE_VERIFY] scenario: {scenario_name} duration: {event.duration:0.4f}', SoPTestLogLevel.INFO)
                    break
        elif SoPProtocolType.WebClient.EM_ADD_SCENARIO.get_prefix() in topic:
            scenario = self.find_scenario(scenario_name)
            middleware = self.find_element_middleware(scenario)

            self.event_log.append(SoPEvent(
                event_type=SoPEventType.SCENARIO_ADD, middleware_element=middleware, scenario_element=scenario, timestamp=timestamp, duration=0))
        elif SoPProtocolType.WebClient.ME_RESULT_ADD_SCENARIO.get_prefix() in topic:
            scenario = self.find_scenario(scenario_name)
            middleware = self.find_element_middleware(scenario)

            if not scenario.is_super():
                scenario.schedule_success = True
                scenario.service_check = True

            scenario.schedule_timeout = False
            scenario.recv_queue.put(msg)
            for event in list(reversed(self.event_log)):
                if event.middleware_element == middleware and event.scenario_element == scenario and event.event_type == SoPEventType.SCENARIO_ADD:
                    event.duration = timestamp - event.timestamp
                    event.error = error_type

                    progress = [scenario.schedule_success for scenario in self.scenario_list].count(
                        True) / len(self.scenario_list)
                    color = 'red' if event.error == SoPErrorType.FAIL else 'green'
                    SOPTEST_LOG_DEBUG(
                        f'[SCENE_ADD] scenario: {scenario_name} duration: {event.duration:0.4f}', SoPTestLogLevel.INFO, progress=progress, color=color)
                    break
        elif SoPProtocolType.WebClient.EM_RUN_SCENARIO.get_prefix() in topic:
            scenario = self.find_scenario(scenario_name)
            middleware = self.find_element_middleware(scenario)

            self.event_log.append(SoPEvent(
                event_type=SoPEventType.SCENARIO_RUN, middleware_element=middleware, scenario_element=scenario, timestamp=timestamp, duration=0))
        elif SoPProtocolType.WebClient.ME_RESULT_RUN_SCENARIO.get_prefix() in topic:
            scenario = self.find_scenario(scenario_name)
            middleware = self.find_element_middleware(scenario)

            scenario.recv_queue.put(msg)
            for event in list(reversed(self.event_log)):
                if event.middleware_element == middleware and event.scenario_element == scenario and event.event_type == SoPEventType.SCENARIO_RUN:
                    event.duration = timestamp - event.timestamp
                    event.error = error_type
                    SOPTEST_LOG_DEBUG(
                        f'[SCENE_RUN] scenario: {scenario_name} duration: {event.duration:0.4f}', SoPTestLogLevel.INFO)
                    break
        elif SoPProtocolType.WebClient.EM_STOP_SCENARIO.get_prefix() in topic:
            scenario = self.find_scenario(scenario_name)
            middleware = self.find_element_middleware(scenario)

            self.event_log.append(SoPEvent(
                event_type=SoPEventType.SCENARIO_STOP, middleware_element=middleware, scenario_element=scenario, timestamp=timestamp, duration=0))
        elif SoPProtocolType.WebClient.ME_RESULT_STOP_SCENARIO.get_prefix() in topic:
            scenario = self.find_scenario(scenario_name)
            middleware = self.find_element_middleware(scenario)

            scenario.recv_queue.put(msg)
            for event in list(reversed(self.event_log)):
                if event.middleware_element == middleware and event.scenario_element == scenario and event.event_type == SoPEventType.SCENARIO_STOP:
                    event.duration = timestamp - event.timestamp
                    event.error = error_type
                    SOPTEST_LOG_DEBUG(
                        f'[SCENE_STOP] scenario: {scenario_name} duration: {event.duration:0.4f}', SoPTestLogLevel.INFO)
                    break
        elif SoPProtocolType.WebClient.EM_UPDATE_SCENARIO.get_prefix() in topic:
            scenario = self.find_scenario(scenario_name)
            middleware = self.find_element_middleware(scenario)

            self.event_log.append(SoPEvent(
                event_type=SoPEventType.SCENARIO_UPDATE, middleware_element=middleware, scenario_element=scenario, timestamp=timestamp, duration=0))
        elif SoPProtocolType.WebClient.ME_RESULT_UPDATE_SCENARIO.get_prefix() in topic:
            scenario = self.find_scenario(scenario_name)
            middleware = self.find_element_middleware(scenario)

            scenario.recv_queue.put(msg)
            for event in list(reversed(self.event_log)):
                if event.middleware_element == middleware and event.scenario_element == scenario and event.event_type == SoPEventType.SCENARIO_UPDATE:
                    event.duration = timestamp - event.timestamp
                    event.error = error_type
                    SOPTEST_LOG_DEBUG(
                        f'[SCENE_UPDATE] scenario: {scenario_name} duration: {event.duration:0.4f}', SoPTestLogLevel.INFO)
                    break
        elif SoPProtocolType.WebClient.EM_DELETE_SCENARIO.get_prefix() in topic:
            scenario = self.find_scenario(scenario_name)
            middleware = self.find_element_middleware(scenario)

            self.event_log.append(SoPEvent(
                event_type=SoPEventType.SCENARIO_DELETE, middleware_element=middleware, scenario_element=scenario, timestamp=timestamp, duration=0))
        elif SoPProtocolType.WebClient.ME_RESULT_DELETE_SCENARIO.get_prefix() in topic:
            scenario = self.find_scenario(scenario_name)
            middleware = self.find_element_middleware(scenario)

            scenario.recv_queue.put(msg)
            for event in list(reversed(self.event_log)):
                if event.middleware_element == middleware and event.scenario_element == scenario and event.event_type == SoPEventType.SCENARIO_DELETE:
                    event.duration = timestamp - event.timestamp
                    event.error = error_type
                    SOPTEST_LOG_DEBUG(
                        f'[SCENE_DELETE] scenario: {scenario_name} duration: {event.duration:0.4f}', SoPTestLogLevel.INFO)
                    break

        ####################################################################################################################################################

        elif SoPProtocolType.Super.MS_SCHEDULE.get_prefix() in topic:
            requester_middleware_name = topic.split('/')[5]
            super_middleware_name = topic.split('/')[4]
            super_thing_name = topic.split('/')[3]
            super_function_name = topic.split('/')[2]

            super_thing = self.find_thing(super_thing_name)
            middleware = self.find_element_middleware(super_thing)
            scenario = self.find_scenario(scenario_name)
            super_service = super_thing.find_service_by_name(
                super_function_name)

            self.event_log.append(SoPEvent(
                event_type=SoPEventType.SUPER_SCHEDULE, middleware_element=middleware, thing_element=super_thing, service_element=super_service, scenario_element=scenario, timestamp=timestamp, duration=0))
            SOPTEST_LOG_DEBUG(
                f'[SUPER_SCHEDULE_START] super_middleware: {super_middleware_name} requester_middleware: {requester_middleware_name} super_thing: {super_thing_name} super_function: {super_function_name} scenario: {scenario_name}', SoPTestLogLevel.INFO)
        elif SoPProtocolType.Super.SM_SCHEDULE.get_prefix() in topic:
            target_middleware_name = topic.split('/')[4]
            target_thing_name = topic.split('/')[3]
            target_function_name = topic.split('/')[2]

            request_ID = topic.split('/')[5]
            requester_middleware_name = request_ID.split('@')[0]
            super_thing_name = request_ID.split('@')[1]
            super_function_name = request_ID.split('@')[2]

            scenario = self.find_scenario(scenario_name)

            progress = [scenario.schedule_success for scenario in self.scenario_list].count(
                True) / len(self.scenario_list)
            color = 'light_magenta'
            SOPTEST_LOG_DEBUG(
                f'[SUB_SCHEDULE_START] super_middleware: {""} requester_middleware: {requester_middleware_name} super_thing: {super_thing_name} super_function: {super_function_name} target_middleware: {target_middleware_name} target_thing: {target_thing_name} target_function: {target_function_name} scenario: {scenario_name}', SoPTestLogLevel.INFO, progress=progress, color=color)
        elif SoPProtocolType.Super.MS_RESULT_SCHEDULE.get_prefix() in topic:
            target_middleware_name = topic.split('/')[5]
            target_thing_name = topic.split('/')[4]
            target_function_name = topic.split('/')[3]

            request_ID = topic.split('/')[6]
            requester_middleware_name = request_ID.split('@')[0]
            super_thing_name = request_ID.split('@')[1]
            super_function_name = request_ID.split('@')[2]

            scenario = self.find_scenario(scenario_name)

            progress = [scenario.schedule_success for scenario in self.scenario_list].count(
                True) / len(self.scenario_list)
            color = 'light_magenta'
            SOPTEST_LOG_DEBUG(
                f'[SUB_SCHEDULE_END] super_middleware: {""} requester_middleware: {requester_middleware_name} super_thing: {super_thing_name} super_function: {super_function_name} target_middleware: {target_middleware_name} target_thing: {target_thing_name} target_function: {target_function_name} scenario: {scenario_name}', SoPTestLogLevel.INFO, progress=progress, color=color)
        elif SoPProtocolType.Super.SM_RESULT_SCHEDULE.get_prefix() in topic:
            requester_middleware_name = topic.split('/')[6]
            super_middleware_name = topic.split('/')[5]
            super_thing_name = topic.split('/')[4]
            super_function_name = topic.split('/')[3]

            super_thing = self.find_thing(super_thing_name)
            middleware = self.find_element_middleware(super_thing)
            scenario = self.find_scenario(scenario_name)
            super_service = super_thing.find_service_by_name(
                super_function_name)

            if scenario.is_super():
                scenario.schedule_success = True
                scenario.service_check = True

            for event in list(reversed(self.event_log)):
                if event.middleware_element == middleware and event.thing_element == super_thing and event.service_element == super_service and event.scenario_element == scenario and event.event_type == SoPEventType.SUPER_SCHEDULE:
                    event.duration = timestamp - event.timestamp
                    event.error = error_type
                    event.return_type = return_type
                    event.return_value = return_value

                    progress = [scenario.schedule_success for scenario in self.scenario_list].count(
                        True) / len(self.scenario_list)

                    SOPTEST_LOG_DEBUG(
                        f'[SUPER_SCHEDULE_END] super_middleware: {super_middleware_name} requester_middleware: {requester_middleware_name} super_thing: {super_thing_name} super_function: {super_function_name} scenario: {scenario_name} duration: {event.duration:0.4f} result: {event.error.value}', SoPTestLogLevel.INFO, progress=progress)
                    break
        elif SoPProtocolType.Super.MS_EXECUTE.get_prefix() in topic:
            super_function_name = topic.split('/')[2]
            super_thing_name = topic.split('/')[3]
            super_middleware_name = topic.split('/')[4]
            requester_middleware_name = topic.split('/')[5]

            super_thing = self.find_thing(super_thing_name)
            middleware = self.find_element_middleware(super_thing)
            scenario = self.find_scenario(scenario_name)
            super_service = super_thing.find_service_by_name(
                super_function_name)

            # NOTE: Super service가 감지되면 각 subfunction의 energy를 0으로 초기화한다.
            # 이렇게 하는 이유는 super service가 실행될 때 마다 다른 subfunction이 실행될 수 있고
            # 이에 따라 다른 eneryg 소모량을 가질 수 있다.
            # for subfunction in super_service.subfunction_list:
            #     subfunction.energy = 0

            self.event_log.append(SoPEvent(
                event_type=SoPEventType.SUPER_FUNCTION_EXECUTE, middleware_element=middleware, thing_element=super_thing, service_element=super_service, scenario_element=scenario, timestamp=timestamp, duration=0))
            passed_time = get_current_time() - self.simulation_start_time
            progress = passed_time / self.running_time
            SOPTEST_LOG_DEBUG(
                f'[SUPER_EXECUTE_START] super_middleware: {super_middleware_name} requester_middleware: {requester_middleware_name} super_thing: {super_thing_name} super_function: {super_function_name} scenario: {scenario_name}', SoPTestLogLevel.INFO, progress=progress)
        elif SoPProtocolType.Super.SM_EXECUTE.get_prefix() in topic:
            target_middleware_name = topic.split('/')[4]
            target_thing_name = topic.split('/')[3]
            target_function_name = topic.split('/')[2]

            request_ID = topic.split('/')[5]
            requester_middleware_name = request_ID.split('@')[0]
            super_thing_name = request_ID.split('@')[1]
            super_function_name = request_ID.split('@')[2]

            scenario = self.find_scenario(scenario_name)

            passed_time = get_current_time() - self.simulation_start_time
            progress = passed_time / self.running_time
            color = 'light_magenta'
            SOPTEST_LOG_DEBUG(
                f'[SUB_EXECUTE_START] super_middleware: {""} requester_middleware: {requester_middleware_name} super_thing: {super_thing_name} super_function: {super_function_name} target_middleware: {target_middleware_name} target_thing: {target_thing_name} target_function: {target_function_name} scenario: {scenario_name}', SoPTestLogLevel.INFO, progress=progress, color=color)
        elif SoPProtocolType.Super.MS_RESULT_EXECUTE.get_prefix() in topic:
            target_middleware_name = topic.split('/')[5]
            target_thing_name = topic.split('/')[4]
            target_function_name = topic.split('/')[3]

            request_ID = topic.split('/')[6]
            requester_middleware_name = request_ID.split('@')[0]
            super_thing_name = request_ID.split('@')[1]
            super_function_name = request_ID.split('@')[2]

            scenario = self.find_scenario(scenario_name)

            passed_time = get_current_time() - self.simulation_start_time
            progress = passed_time / self.running_time
            color = 'light_magenta'
            SOPTEST_LOG_DEBUG(
                f'[SUB_EXECUTE_END] super_middleware: {""} requester_middleware: {requester_middleware_name} super_thing: {super_thing_name} super_function: {super_function_name} target_middleware: {target_middleware_name} target_thing: {target_thing_name} target_function: {target_function_name} scenario: {scenario_name}', SoPTestLogLevel.INFO, progress=progress, color=color)
        elif SoPProtocolType.Super.SM_RESULT_EXECUTE.get_prefix() in topic:
            requester_middleware_name = topic.split('/')[6]
            super_middleware_name = topic.split('/')[5]
            super_thing_name = topic.split('/')[4]
            super_function_name = topic.split('/')[3]

            super_thing = self.find_thing(super_thing_name)
            middleware = self.find_element_middleware(super_thing)
            scenario = self.find_scenario(scenario_name)
            super_service = super_thing.find_service_by_name(
                super_function_name)

            for event in list(reversed(self.event_log)):
                if event.middleware_element == middleware and event.thing_element == super_thing and event.service_element == super_service and event.scenario_element == scenario and event.event_type == SoPEventType.SUPER_FUNCTION_EXECUTE:
                    event.duration = timestamp - event.timestamp
                    event.error = error_type
                    event.return_type = return_type
                    event.return_value = return_value

                    passed_time = get_current_time() - self.simulation_start_time
                    progress = passed_time / self.running_time
                    SOPTEST_LOG_DEBUG(
                        f'[SUPER_EXECUTE_END] super_middleware: {super_middleware_name} requester_middleware: {requester_middleware_name} super_thing: {super_thing_name} super_function: {super_function_name} scenario: {scenario_name} duration: {event.duration:0.4f} return value: {return_value} - {return_type.value} error:{event.error.value}', SoPTestLogLevel.INFO, progress=progress)
                    break
        elif 'SIM/FINISH' in topic:
            scenario = self.find_scenario(scenario_name)
            scenario.cycle_count += 1
            # SOPTEST_LOG_DEBUG(
            #     f'[SIM_FINISH] scenario: {scenario.name}, cycle_count: {scenario.cycle_count}', SoPTestLogLevel.WARN)
            return True
        else:
            raise Exception(f'Unknown topic: {topic}')

        # elif SoPProtocolType.Default.TM_VALUE_PUBLISH.get_prefix() in topic:
        #     pass
        # elif SoPProtocolType.Default.TM_VALUE_PUBLISH_OLD.get_prefix() in topic:
        #     pass
