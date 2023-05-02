from simulation_framework.core.simulation_executor import *
from simulation_framework.core.config import *

import random
import copy


class MXElementGenerateMode(Enum):
    ALL_RANDOM = 'all_random'
    APPEND = 'append'
    APPEND_WITH_REMAPPING = 'append_with_remapping'


class MXSimulationGenerator:

    def __init__(self, config_path: str) -> None:
        if not config_path:
            return None

        self.simulation_env: MXMiddlewareElement = None
        self.simulation_env_pool = {}
        self.load_config(config_path)

    def load_config(self, config_path: str):
        self.simulation_config = MXSimulationConfig(config_path)

        self.check_device_pool()
        self.whole_device_pool = self.get_whole_device_pool(
            self.simulation_config.device_pool_path.abs_path())

        if not self.simulation_config.middleware_config.device_pool:
            middleware_device_pool = [
                device for device in self.whole_device_pool if device.name != 'localhost']
        else:
            middleware_device_pool = [
                device for device in self.whole_device_pool if device.name in self.simulation_config.middleware_config.device_pool]
        if not self.simulation_config.thing_config.device_pool:
            if not 'localhost' in [device.name for device in self.whole_device_pool]:
                raise Exception(
                    f'localhost must be defined in {self.simulation_config.device_pool_path}')
            thing_device_pool = [
                device for device in self.whole_device_pool if device.name == 'localhost']
        else:
            thing_device_pool = [
                device for device in self.whole_device_pool if device.name in self.simulation_config.thing_config.device_pool]

        manual_middleware_config_path = self.simulation_config.middleware_config.manual.abs_path()
        if manual_middleware_config_path:
            self.simulation_config.middleware_config.manual = load_yaml(
                self.simulation_config.middleware_config.manual.abs_path())
        elif self.simulation_config.middleware_config.random:
            middleware_device_pool = [
                device for device in self.whole_device_pool if device.name == 'localhost']
            self.simulation_config.middleware_config.manual = None

        self.middleware_generator = MXMiddlewareGenerator(
            self.simulation_config, middleware_device_pool)
        self.service_generator = MXServiceGenerator(self.simulation_config)
        self.thing_generator = MXThingGenerator(
            self.simulation_config, thing_device_pool)
        self.scenario_generator = MXScenarioGenerator(self.simulation_config)

    def check_device_pool(self):
        device_pool_path = self.simulation_config.device_pool_path.abs_path()

        # device_pool_path에 파일이 있는 지 확인하고 없으면 생성
        if not os.path.exists(device_pool_path):
            os.makedirs(os.path.dirname(device_pool_path), exist_ok=True)
            f = open(device_pool_path, 'w')
            f.close()

        # devcie_pool에 localhost에 대한 정보가 있는지 확인하고 없으면 생성
        device_pool = load_yaml(device_pool_path)
        if not 'localhost' in device_pool:
            with open('/etc/ssh/sshd_config', 'r') as f:
                lines = f.readlines()
                for line in lines:
                    if re.match('^#Port', line):
                        ssh_port = 22
                    else:
                        ssh_port = re.findall(
                            '^ *Port +([0-9]+)', line, re.M)
                        if len(ssh_port) == 0:
                            continue
                        else:
                            ssh_port = int(ssh_port[0])
                    user = os.path.basename(os.path.expanduser('~'))
                    break
            password = input(
                f'localhost config is not exist in [{os.path.basename(device_pool_path)}]... Enter password of user [{user}]: ')

            data = dict(
                localhost=dict(
                    host='localhost',
                    ssh_port=ssh_port,
                    user=user,
                    password=password
                )
            )

            test_ssh_client = MXSSHClient(device=MXDeviceElement(
                name='test_localhost', host='localhost', ssh_port=ssh_port, user=user, password=password))
            try:
                test_ssh_client.connect()
            except Exception as e:
                raise Exception(
                    f'Failed to connect to localhost. Please check your ssh config. {e}')
            test_ssh_client.disconnect()

            data.update(load_yaml(device_pool_path))
            save_yaml(device_pool_path, data)

    def generate_simulation(self, simulation_ID: str = None, config_path: str = None, is_parallel: bool = False):
        self.load_config(config_path)

        simulation_folder_path = f'{os.path.dirname(self.simulation_config.path)}/simulation_{self.simulation_config.name}_{get_current_time(TimeFormat.DATETIME2)}'
        MXTEST_LOG_DEBUG(
            f'Generate simulation: {simulation_folder_path}', MXTestLogLevel.INFO)

        if simulation_ID:
            simulation_env = self.simulation_env_pool[simulation_ID]['simulation_env']
            base_service_pool = self.simulation_env_pool[simulation_ID]['base_service_pool']
            simulation_config = self.simulation_env_pool[simulation_ID]['simulation_config']

            simulation_env = self.middleware_generator.generate(
                simulation_env=simulation_env)

            simulation_env = self.thing_generator.generate(
                simulation_env, base_service_pool, simulation_folder_path, is_parallel=is_parallel)
            simulation_env = self.thing_generator.generate_super(
                simulation_env, self.service_generator, simulation_folder_path)

            self.scenario_generator.generate(
                simulation_env, simulation_folder_path)
            self.scenario_generator.generate_super(
                simulation_env, simulation_folder_path)

            self.simulation_env = simulation_env

            simulation_data = self.generate_data(simulation_env)
            simulation_file_path = self.dump_file(
                simulation_data, simulation_folder_path)
        else:
            simulation_env = self.middleware_generator.generate()

            base_service_pool = self.service_generator.generate()

            simulation_env = self.thing_generator.generate(
                simulation_env, base_service_pool, simulation_folder_path, is_parallel=is_parallel)
            simulation_env = self.thing_generator.generate_super(
                simulation_env, self.service_generator, simulation_folder_path)

            self.scenario_generator.generate(
                simulation_env, simulation_folder_path)
            self.scenario_generator.generate_super(
                simulation_env, simulation_folder_path)

            self.simulation_env = simulation_env

            simulation_data = self.generate_data(simulation_env)
            simulation_file_path = self.dump_file(
                simulation_data, simulation_folder_path)

            simulation_ID = generate_random_string(16)
            self.simulation_env_pool[simulation_ID] = dict(
                simulation_env=simulation_env, base_service_pool=base_service_pool, simulation_config=self.simulation_config)

        return simulation_file_path, simulation_ID

    def generate_timeline(self, middleware_list: List[MXMiddlewareElement], thing_list: List[MXThingElement], scenario_list: List[MXScenarioElement],
                          running_time: float, event_timeout: float):
        event_timeline: List[MXEvent] = []

        def make_dynamic_thing_event(local_thing_list: List[MXThingElement], super_thing_list: List[MXThingElement],
                                     normal_thing_select_rate: float, super_thing_select_rate: float,
                                     start_time_weight: float, end_time_weight: float, event_type: MXEventType, delay: float):
            if event_type == MXEventType.THING_UNREGISTER:
                event_type_1 = MXEventType.THING_UNREGISTER
                event_type_2 = MXEventType.THING_RUN
            elif event_type == MXEventType.THING_KILL:
                event_type_1 = MXEventType.THING_KILL
                event_type_2 = MXEventType.THING_RUN
            else:
                raise Exception('invalid event type')

            selected_local_thing_list = random.sample(
                local_thing_list, int(len(local_thing_list) * normal_thing_select_rate))
            selected_super_thing_list = random.sample(
                super_thing_list, int(len(super_thing_list) * super_thing_select_rate))
            local_thing_unregister_timeline = [thing.event(
                event_type=event_type_1, timestamp=self.simulation_config.running_time * start_time_weight).dict() for thing in selected_local_thing_list]
            super_thing_unregister_timeline = [thing.event(
                event_type=event_type_1, timestamp=self.simulation_config.running_time * start_time_weight).dict() for thing in selected_super_thing_list]
            local_thing_register_timeline = [thing.event(
                event_type=event_type_2, timestamp=self.simulation_config.running_time * end_time_weight).dict() for thing in selected_local_thing_list]
            super_thing_register_timeline = [thing.event(
                event_type=event_type_2, timestamp=self.simulation_config.running_time * end_time_weight).dict() for thing in selected_super_thing_list]

            tmp_timeline = local_thing_unregister_timeline + super_thing_unregister_timeline + \
                local_thing_register_timeline + super_thing_register_timeline
            if delay:
                tmp_timeline += [MXEvent(delay=delay,
                                         event_type=MXEventType.DELAY).dict()]
            return tmp_timeline

        # def make_scenario_event(local_scenario_list: List[MXScenarioElement], super_scenario_list: List[MXScenarioElement],
        #                         start_time_weight: float, end_time_weight: float, event_type: MXEventType, delay: float):
        #     if event_type == MXEventType.SCENARIO_STOP:
        #         event_type_1 = MXEventType.SCENARIO_STOP
        #         event_type_2 = MXEventType.SCENARIO_RUN
        #     elif event_type == MXEventType.SCENARIO_DELETE:
        #         event_type_1 = MXEventType.SCENARIO_DELETE
        #         event_type_2 = MXEventType.SCENARIO_ADD
        #         # event_type_3 = MXEventType.SCENARIO_RUN
        #     else:
        #         raise Exception('invalid event type')

        #     selected_local_scenario_list = random.sample(
        #         local_scenario_list, int(len(local_scenario_list) * self.simulation_config.application_config.normal.stop_rate))
        #     selected_super_scenario_list = random.sample(
        #         super_scenario_list, int(len(super_scenario_list) * self.simulation_config.application_config.super.stop_rate))
        #     local_scenario_stop_timeline = [thing.event(
        #         event_type=event_type_1, timestamp=self.simulation_config.running_time * start_time_weight).dict() for thing in selected_local_scenario_list]
        #     super_scenario_stop_timeline = [thing.event(
        #         event_type=event_type_1, timestamp=self.simulation_config.running_time * start_time_weight).dict() for thing in selected_super_scenario_list]
        #     local_scenario_run_timeline = [thing.event(
        #         event_type=event_type_2, timestamp=self.simulation_config.running_time * end_time_weight).dict() for thing in selected_local_scenario_list]
        #     super_scenario_run_timeline = [thing.event(
        #         event_type=event_type_2, timestamp=self.simulation_config.running_time * end_time_weight).dict() for thing in selected_super_scenario_list]

        #     tmp_timeline = local_scenario_stop_timeline + super_scenario_stop_timeline + \
        #         local_scenario_run_timeline + super_scenario_run_timeline
        #     if delay:
        #         tmp_timeline += [MXEvent(delay=delay,
        #                                   event_type=MXEventType.DELAY).dict()]
        #     return tmp_timeline

        local_thing_list = [
            thing for thing in thing_list if thing.is_super == False]
        super_thing_list = [
            thing for thing in thing_list if thing.is_super == True]
        # non_super_scenario_list = [scenario for scenario in scenario_list if all(
        #     [not service.is_super for service in scenario.service_list])]
        # super_scenario_list = [scenario for scenario in scenario_list if all(
        #     [service.is_super for service in scenario.service_list])]

        # build simulation env
        build_simulation_env_timeline = []
        build_simulation_env_timeline.extend([middleware.event(
            MXEventType.MIDDLEWARE_RUN).dict() for middleware in middleware_list])
        build_simulation_env_timeline.extend(
            [thing.event(MXEventType.THING_RUN).dict() for thing in sorted(thing_list, key=lambda x: x.is_super, reverse=False)])
        event_timeline.extend(build_simulation_env_timeline)

        # wait until all thing register
        event_timeline.append(
            MXEvent(event_type=MXEventType.THING_REGISTER_WAIT).dict())

        event_timeline.append(
            MXEvent(delay=5, event_type=MXEventType.DELAY).dict())

        # scenario add start
        scenario_add_timeline = [scenario.event(event_type=MXEventType.SCENARIO_ADD,
                                                middleware_element=find_element_recursive(self.simulation_env, scenario)[1]).dict() for scenario in scenario_list]
        event_timeline.extend(
            sorted(scenario_add_timeline, key=lambda x: x['timestamp']))

        event_timeline.append(
            MXEvent(event_type=MXEventType.SCENARIO_ADD_CHECK).dict())

        event_timeline.append(
            MXEvent(delay=5, event_type=MXEventType.DELAY).dict())

        event_timeline.append(
            MXEvent(event_type=MXEventType.REFRESH).dict())

        # simualtion start
        event_timeline.append(
            MXEvent(event_type=MXEventType.START).dict())

        # scenario run start
        scenario_run_timeline = [scenario.event(
            event_type=MXEventType.SCENARIO_RUN).dict() for scenario in scenario_list]
        event_timeline.extend(
            sorted(scenario_run_timeline, key=lambda x: x['timestamp']))

        # thing unregister stage
        thing_unregister_timeline = make_dynamic_thing_event(local_thing_list=local_thing_list, super_thing_list=super_thing_list,
                                                             normal_thing_select_rate=self.simulation_config.thing_config.normal.unregister_rate,
                                                             super_thing_select_rate=self.simulation_config.thing_config.super.unregister_rate,
                                                             start_time_weight=0.2, end_time_weight=0.7, event_type=MXEventType.THING_UNREGISTER, delay=0)
        event_timeline.extend(thing_unregister_timeline)

        # thing kill stage
        thing_kill_timeline = make_dynamic_thing_event(local_thing_list=local_thing_list, super_thing_list=super_thing_list,
                                                       normal_thing_select_rate=self.simulation_config.thing_config.normal.broken_rate,
                                                       super_thing_select_rate=self.simulation_config.thing_config.super.broken_rate,
                                                       start_time_weight=0.5, end_time_weight=10, event_type=MXEventType.THING_KILL, delay=0)
        event_timeline.extend(thing_kill_timeline)

        # scenario stop stage
        # scenario_stop_timeline = make_scenario_event(local_scenario_list=non_super_scenario_list, super_scenario_list=super_scenario_list,
        #                                              start_time_weight=0.3, end_time_weight=0.8, event_type=MXEventType.SCENARIO_STOP, delay=0)
        # event_timeline.extend(scenario_stop_timeline)

        # simulation end
        event_timeline.append(
            MXEvent(event_type=MXEventType.END, timestamp=running_time).dict())
        event_timeline = sorted(event_timeline, key=lambda x: x['timestamp'])
        end_index = 0
        for i, event in enumerate(event_timeline):
            if event['event_type'] == 'END':
                end_index = i
                break

        return event_timeline[:end_index+1]

    def generate_data(self, simulation_env: MXMiddlewareElement):
        # generate simulation env
        middleware_list: List[MXMiddlewareElement] = get_middleware_list_recursive(
            simulation_env)
        thing_list: List[MXThingElement] = get_thing_list_recursive(
            simulation_env)
        scenario_list: List[MXScenarioElement] = get_scenario_list_recursive(
            simulation_env)

        longest_scneario = max(scenario_list, key=lambda x: x.period)
        if longest_scneario.period * 1.2 > self.simulation_config.running_time:
            running_time = longest_scneario.period * 1.2
            MXTEST_LOG_DEBUG(
                f'Longest scenario period is {longest_scneario.period} but simulation time is {self.simulation_config.running_time}. Set simulation time to {running_time}', MXTestLogLevel.WARN)
        else:
            running_time = self.simulation_config.running_time

        config = dict(name=self.simulation_config.name,
                      running_time=running_time,
                      event_timeout=self.simulation_config.event_timeout)
        component = simulation_env.dict()
        event_timeline = self.generate_timeline(middleware_list=middleware_list,
                                                thing_list=thing_list,
                                                scenario_list=scenario_list,
                                                running_time=running_time,
                                                event_timeout=self.simulation_config.event_timeout)
        simulation_dump = dict(config=config,
                               component=component,
                               event_timeline=event_timeline)
        return simulation_dump

    def dump_file(self, simulation_dump: dict, simulation_folder_path: str):
        os.makedirs(simulation_folder_path, exist_ok=True)
        write_file(f'{simulation_folder_path}/simulation_data.json',
                   dict_to_json_string(simulation_dump))
        return f'{simulation_folder_path}/simulation_data.json'

    def get_whole_device_pool(self, device_pool_path: str) -> List[MXDeviceElement]:
        device_list = load_yaml(device_pool_path)

        whole_device_pool = []
        for device_name, device_info in device_list.items():
            device = MXDeviceElement(
                name=device_name,
                element_type=MXElementType.DEVICE,
                host=device_info['host'],
                ssh_port=device_info['ssh_port'],
                user=device_info['user'],
                password=device_info['password'],
                mqtt_port=device_info.get('mqtt_port', None),
                mqtt_ssl_port=device_info.get('mqtt_ssl_port', 'Not used'),
                websocket_port=device_info.get('websocket_port', 'Not used'),
                websocket_ssl_port=device_info.get(
                    'websocket_ssl_port', 'Not used'),
                localserver_port=device_info.get('localserver_port', 58132))
            whole_device_pool.append(device)
        return whole_device_pool


class MXElementGenerator(metaclass=ABCMeta):

    def __init__(self, config: MXSimulationConfig = None) -> None:
        self.config: MXSimulationConfig = config

    @abstractmethod
    def generate(self):
        pass


class MXMiddlewareGenerator(MXElementGenerator):
    def __init__(self, config: MXSimulationConfig = None, device_pool: List[MXDeviceElement] = []) -> None:
        super().__init__(config)

        self.device_pool = device_pool
        self.used_device_list: List[MXDeviceElement] = []

    def find_device(self, device_name: str) -> MXDeviceElement:
        for device in self.device_pool:
            if device.name == device_name:
                return device
        else:
            raise Exception(
                f'Cannot find device {device_name} in device pool')

    def generate_middleware(self, height: int, index: int, name: str = 'middleware', upper_middleware: MXMiddlewareElement = None, target_device_pool: Union[str, List[str]] = None,
                            thing_num: List[int] = None, super_thing_num: List[int] = None, scenario_num: List[int] = None, super_scenario_num: List[int] = None,
                            mqtt_port: int = None) -> dict:

        def get_unselected_device(target_device_pool: List[MXDeviceElement]) -> MXDeviceElement:
            while True:
                device: MXDeviceElement = random.choice(target_device_pool)
                if device not in self.used_device_list:
                    self.used_device_list.append(device)
                    return device
                elif len(self.used_device_list) == len(target_device_pool):
                    MXTEST_LOG_DEBUG(
                        f'All device in device pool is used. Use device duplicate mode on middleware: {name}', MXTestLogLevel.WARN)
                    return device
                else:
                    continue

        # 미들웨어의 이름을 생성한다
        if upper_middleware:
            name = f'{upper_middleware.name}__{name}_level{height}_{index}'
        else:
            name = f'{name}_level{height}_{index}'

        # 최대한 디바이스가 겹치지 않게 미들웨어에 디바이스를 할당한다
        # 만약 디바이스 수가 모자라는 경우 경고를 출력하고 중복해서 할당한다
        if not target_device_pool:
            device = get_unselected_device(self.device_pool)
        elif isinstance(target_device_pool, list):
            target_device_pool: List[MXDeviceElement] = [
                self.find_device(device) for device in target_device_pool]
            device = get_unselected_device(target_device_pool)
        elif isinstance(target_device_pool, str):
            target_device_pool: List[MXDeviceElement] = [
                self.find_device(target_device_pool)]
            device = get_unselected_device(target_device_pool)
        else:
            raise Exception(
                f'Invalid target_device_pool type: {type(target_device_pool)}')

        name = 'middleware' if not name else name
        middleware = MXMiddlewareElement(name=name,
                                         level=height,
                                         element_type=MXElementType.MIDDLEWARE,
                                         thing_list=[],
                                         scenario_list=[],
                                         child_middleware_list=[],
                                         device=device,
                                         remote_middleware_path=self.config.middleware_config.remote_middleware_path,
                                         remote_middleware_config_path=self.config.middleware_config.remote_middleware_config_path,
                                         mqtt_port=mqtt_port if mqtt_port else device.mqtt_port,
                                         thing_num=thing_num,
                                         super_thing_num=super_thing_num,
                                         scenario_num=scenario_num,
                                         super_scenario_num=super_scenario_num)
        MXTEST_LOG_DEBUG(
            f'generate middleware: {middleware.name}({middleware.level})', MXTestLogLevel.PASS)
        return middleware

    def generate(self, simulation_env: MXMiddlewareElement = None, manual_height: int = None, manual_child_per_node: int = None):

        def get_middleware_tree_height(middleware_tree: List[dict]):
            if not middleware_tree:
                return 0
            return max(get_middleware_tree_height(middleware['child']) for middleware in middleware_tree) + 1

        def generate_random_middleware_tree_recursive(height: int, width: Tuple[int], upper_middleware: MXMiddlewareElement):
            upper_middleware.child_middleware_list.extend([self.generate_middleware(
                height=height - 1,
                index=i,
                upper_middleware=upper_middleware) for i in range(random.randint(width[0], width[1]))])
            if height - 1 > 1:
                for child_middleware in upper_middleware.child_middleware_list:
                    generate_random_middleware_tree_recursive(height - 1, width,
                                                              child_middleware)

            return upper_middleware

        def generate_manual_middleware_tree_recursive(height: int, upper_middleware: MXMiddlewareElement, middleware_tree: list):
            if not middleware_tree:
                return upper_middleware

            width = len(middleware_tree)
            # NOTE: middleware debug mode only available in manual middleware tree mode
            if upper_middleware.child_middleware_list:
                for child_middleware, child_middleware_tree in zip(upper_middleware.child_middleware_list, middleware_tree):
                    child_middleware.thing_num = child_middleware_tree['thing_num']
                    child_middleware.super_thing_num = child_middleware_tree['super_thing_num']
                    child_middleware.scenario_num = child_middleware_tree['scenario_num']
                    child_middleware.super_scenario_num = child_middleware_tree['super_scenario_num']
            else:
                tmp_child_middleware_list = []
                for i in range(width):
                    target_device_pool = middleware_tree[i].get(
                        'device', None)
                    if not target_device_pool:
                        target_device_pool = [
                            device.name for device in self.device_pool]

                    tmp_child_middleware_list.append(self.generate_middleware(
                        height=height - 1,
                        index=i,
                        name=middleware_tree[i]['name'],
                        upper_middleware=upper_middleware,
                        target_device_pool=target_device_pool,
                        thing_num=middleware_tree[i]['thing_num'],
                        super_thing_num=middleware_tree[i]['super_thing_num'],
                        scenario_num=middleware_tree[i]['scenario_num'],
                        super_scenario_num=middleware_tree[i]['super_scenario_num'],
                        mqtt_port=middleware_tree[i].get('mqtt_port', None)))
                upper_middleware.child_middleware_list.extend(
                    tmp_child_middleware_list)

            if height - 1 > 1:
                for child_middleware, child_middleware_tree in zip(upper_middleware.child_middleware_list, middleware_tree):
                    generate_manual_middleware_tree_recursive(
                        height - 1, child_middleware, child_middleware_tree['child'])

            return upper_middleware

        if manual_height is not None:
            new_simulation_env: MXMiddlewareElement = self.generate_middleware(
                height=manual_height,
                index=0)
            if manual_height > 1:
                generate_random_middleware_tree_recursive(
                    manual_height, [1, 1], new_simulation_env)

            if simulation_env:
                top_level = simulation_env.level
                middleware_list: List[MXMiddlewareElement] = get_middleware_list_recursive(
                    new_simulation_env)
                for middleware in middleware_list:
                    if middleware.level == top_level + 1:
                        middleware.child_middleware_list = [simulation_env]

            return new_simulation_env
        elif manual_child_per_node is not None:
            if not simulation_env:
                simulation_env: MXMiddlewareElement = self.generate_middleware(
                    height=2,
                    index=0)
            for _ in range(1, manual_child_per_node - len(simulation_env.child_middleware_list) + 1):
                index = len(simulation_env.child_middleware_list)
                middleware_env: MXMiddlewareElement = self.generate_middleware(
                    height=1,
                    index=index)
                simulation_env.child_middleware_list.append(middleware_env)
            return simulation_env
        elif self.config.middleware_config.manual:
            max_height = get_middleware_tree_height(
                self.config.middleware_config.manual)

            if not simulation_env:
                target_device_pool = self.config.middleware_config.manual[0].get(
                    'device', None)
                if not target_device_pool:
                    target_device_pool = [
                        device.name for device in self.device_pool]

                middleware_env: MXMiddlewareElement = self.generate_middleware(
                    height=max_height,
                    index=0,
                    name=self.config.middleware_config.manual[0]['name'],
                    target_device_pool=target_device_pool,
                    thing_num=self.config.middleware_config.manual[
                        0]['thing_num'],
                    super_thing_num=self.config.middleware_config.manual[
                        0]['super_thing_num'],
                    scenario_num=self.config.middleware_config.manual[
                        0]['scenario_num'],
                    super_scenario_num=self.config.middleware_config.manual[
                        0]['super_scenario_num'],
                    mqtt_port=self.config.middleware_config.manual[0].get(
                        'mqtt_port', None)
                )
            else:
                middleware_env = simulation_env
            return generate_manual_middleware_tree_recursive(max_height, middleware_env, self.config.middleware_config.manual[0]['child'])
        elif self.config.middleware_config.random:
            height = random.randint(self.config.middleware_config.random.height[0],
                                    self.config.middleware_config.random.height[1])
            middleware_env: MXMiddlewareElement = self.generate_middleware(
                height=height, index=0)
            if height == 1:
                return middleware_env
            return generate_random_middleware_tree_recursive(height, self.config.middleware_config.random.width, middleware_env)
        else:
            raise Exception('No middleware config found')


class MXServiceGenerator(MXElementGenerator):

    BAN_WORD_LIST = ['if', 'else', 'and', 'or', 'loop', 'wait_until', 'msec', 'list', 'normal', 'super',
                     'sec', 'min', 'hour', 'day', 'month', 'all', 'single', 'random']

    def __init__(self, config: MXSimulationConfig = None) -> None:
        super().__init__(config)

        self.tag_name_pool = generate_random_words(
            word_num=self.config.service_config.tag_type_num, ban_word_list=MXServiceGenerator.BAN_WORD_LIST)
        self.service_name_pool = random.sample(generate_random_words(
            word_num=self.config.service_config.normal.service_type_num * 10, ban_word_list=MXServiceGenerator.BAN_WORD_LIST), self.config.service_config.normal.service_type_num)
        self.super_service_name_pool = random.sample(generate_random_words(
            word_num=self.config.service_config.super.service_type_num * 10, ban_word_list=MXServiceGenerator.BAN_WORD_LIST), self.config.service_config.super.service_type_num)

    def generate(self):

        def generate_service_property(service_name: str):
            service_name = f'function_{service_name}'
            tag_list = random.sample(self.tag_name_pool, random.randint(
                self.config.service_config.tag_per_service[0], self.config.service_config.tag_per_service[1]))
            if len(tag_list) != len(set(tag_list)):
                MXTEST_LOG_DEBUG(
                    f'service {service_name}\'s tag_list has duplicated words! check this out...', MXTestLogLevel.FAIL)
                tag_list = list(set(tag_list))

            energy = random.randint(
                self.config.service_config.normal.energy[0], self.config.service_config.normal.energy[1])
            execute_time = random.uniform(
                self.config.service_config.normal.execute_time[0], self.config.service_config.normal.execute_time[1])
            return_value = random.randint(0, 1000)

            return service_name, tag_list, energy, execute_time, return_value

        service_pool = []
        for service_name in self.service_name_pool:
            # is_trade_off가 True이면 execute_time, energy가 서로 반비례하게 생성된다.
            service_name, tag_list, energy, execute_time, return_value = generate_service_property(
                service_name=service_name)
            service = MXServiceElement(name=service_name,
                                       level=None,
                                       element_type=MXElementType.SERVICE,
                                       tag_list=tag_list,
                                       is_super=False,
                                       energy=energy,
                                       execute_time=execute_time,
                                       return_value=return_value)
            service_pool.append(service)
        MXTEST_LOG_DEBUG(
            f'generated {len(service_pool)} normal services', MXTestLogLevel.PASS)
        return service_pool

    def generate_super(self, middleware: MXMiddlewareElement, thing_config: MXThingConfig = None) -> List[MXServiceElement]:

        def get_candidate_subservice_list(super_middleware: MXMiddlewareElement):
            candidate_subservice_list: List[MXServiceElement] = []
            for thing in super_middleware.thing_list:
                candidate_subservice_list.extend(
                    [service for service in thing.service_list if not service.is_super])
            for middleware in super_middleware.child_middleware_list:
                candidate_subservice_list.extend(
                    get_candidate_subservice_list(middleware))

            return candidate_subservice_list

        # TODO: 다시 재작성할 것
        def generate_super_service_property(candidate_subservice_list: List[MXServiceElement],
                                            selected_subservice_list: List[MXServiceElement],
                                            super_service_list: List[MXServiceElement]):
            while True:
                super_service_name = f'super_function_{random.choice(self.super_service_name_pool)}'
                if super_service_name not in [super_service.name for super_service in super_service_list]:
                    break
            tag_list = random.sample(self.tag_name_pool, random.randint(self.config.service_config.tag_per_service[0],
                                                                        self.config.service_config.tag_per_service[1]))

            # NOTE: super service의 energy, execute_time은 subservice들의 합으로 계산된다. super service의 subservice 매핑상태는
            # 미들웨어에 등록되기 전까지 알 수 없으므로 원칙적으로 energy, execute_time은 계산할 수 없다. 그러나 super service가 미들웨어에
            # 붙을 때 예상 execute time을 제공하고 있으므로, execute_time은 super service가 고른 subservice중 가장 execute time이
            # 긴 조합으로 execute time을 계산하여 초기값으로 둔다.
            energy = 0
            execute_time = 0

            for subservice in selected_subservice_list:
                same_name_subservice_list = [
                    candidate_service for candidate_service in candidate_subservice_list if subservice.name == candidate_service.name]
                execute_time += max(
                    [subservice.execute_time for subservice in same_name_subservice_list])

            return super_service_name, tag_list, energy, execute_time

        self.thing_config = thing_config
        super_service_num = random.randint(self.thing_config.super.service_per_thing[0],
                                           self.thing_config.super.service_per_thing[1])
        candidate_service_list = get_candidate_subservice_list(middleware)
        super_service_list = []
        for _ in range(super_service_num):
            # TODO: supservice를 누적하는 기능 완료하기
            prev_subservice_num = 0
            subservice_num = random.randint(self.config.service_config.super.service_per_super_service[0],
                                            self.config.service_config.super.service_per_super_service[1])
            selected_service_list: List[MXServiceElement] = random.sample(
                candidate_service_list, subservice_num)
            super_service_name, tag_list, energy, execute_time = generate_super_service_property(
                candidate_subservice_list=candidate_service_list, selected_subservice_list=selected_service_list, super_service_list=super_service_list)

            super_service = MXServiceElement(name=super_service_name,
                                             element_type=MXElementType.SERVICE,
                                             tag_list=tag_list,
                                             is_super=True,
                                             energy=energy,
                                             execute_time=execute_time,
                                             subservice_list=selected_service_list)

            super_service_list.append(super_service)
        return super_service_list


class MXThingGenerator(MXElementGenerator):

    def __init__(self, config: MXSimulationConfig = None, thing_device_pool: List[MXDeviceElement] = []) -> None:
        super().__init__(config)

        self.thing_deivce_pool: List[MXDeviceElement] = thing_device_pool

    def make_thing_name(self, index: int, is_super: bool, middleware: MXMiddlewareElement):
        middleware_index = '_'.join(middleware.name.split('_')[1:])  # levelN_M
        prefix_name = 'super' if is_super else 'normal'
        name = f'{prefix_name}_thing_{middleware_index}_{index}'

        return name.replace(' ', '_')

    def generate_error_property(self, is_super: bool):
        if is_super:
            config = self.config.thing_config.super
        else:
            config = self.config.thing_config.normal

        fail_rate = config.fail_error_rate

        return fail_rate

    def generate_thing_property(self, middleware: MXMiddlewareElement, index: int, is_super: bool, service_list: List[MXServiceElement] = []):
        fail_rate = self.generate_error_property(
            is_super=is_super)
        thing_name = self.make_thing_name(
            index=index, is_super=is_super, middleware=middleware)

        # NOTE: super thing은 미들웨어와 같은 device를 사용한다.
        if is_super:
            device = middleware.device
        else:
            device = random.choice(self.thing_deivce_pool)

        if service_list:
            picked_service_list = random.sample(service_list, k=random.randint(self.config.thing_config.normal.service_per_thing[0],
                                                                               self.config.thing_config.normal.service_per_thing[1]))
        else:
            picked_service_list = []
        return thing_name, device, fail_rate, copy.deepcopy(picked_service_list)

    def generate(self, simulation_env: MXMiddlewareElement, service_list: List[MXServiceElement], simulation_folder_path: str, is_parallel: bool):

        def generate_recursive(middleware: MXMiddlewareElement, service_list: List[MXServiceElement]) -> MXMiddlewareElement:
            if not self.config.middleware_config.manual:
                base_thing_num = random.randint(self.config.middleware_config.random.normal.thing_per_middleware[0],
                                                self.config.middleware_config.random.normal.thing_per_middleware[1])
            else:
                base_thing_num = random.randint(middleware.thing_num[0],
                                                middleware.thing_num[1])

            # 이미 생성된 thing이 있으면, 기존 thing에 누적해서 추가분을 더 생성
            prev_thing_num = len(
                [thing for thing in middleware.thing_list if not thing.is_super])
            for index in range(base_thing_num - prev_thing_num):
                thing_name, device, fail_rate, picked_service_list = self.generate_thing_property(middleware=middleware,
                                                                                                  index=index + prev_thing_num,
                                                                                                  is_super=False,
                                                                                                  service_list=service_list)
                for service in picked_service_list:
                    thing_w = random.uniform(0, 0.5)
                    service.execute_time = service.execute_time * (1 - thing_w)
                    service.energy = service.energy * (1 + thing_w)

                thing = MXThingElement(name=thing_name,
                                       level=middleware.level,
                                       element_type=MXElementType.THING,
                                       service_list=picked_service_list,
                                       is_super=False,
                                       is_parallel=is_parallel,
                                       alive_cycle=300,
                                       device=device,
                                       thing_file_path=f'{simulation_folder_path}/thing/base_thing/{thing_name}.py',
                                       remote_thing_file_path=f'{self.config.thing_config.remote_thing_folder_path}/base_thing/{thing_name}.py',
                                       fail_rate=fail_rate)
                MXTEST_LOG_DEBUG(
                    f'generate thing: {thing.name} (level: {thing.level})', MXTestLogLevel.PASS)

                for service in thing.service_list:
                    service.level = middleware.level
                middleware.thing_list.append(thing)

            for child_middleware in middleware.child_middleware_list:
                generate_recursive(child_middleware, service_list)

        generate_recursive(simulation_env, service_list)
        return simulation_env

    def generate_super(self, simulation_env: MXMiddlewareElement, service_generator: MXServiceGenerator, simulation_folder_path: str) -> MXMiddlewareElement:

        def generate_super_recursive(middleware: MXMiddlewareElement, service_generator: MXServiceGenerator) -> MXMiddlewareElement:
            middleware_list: List[MXMiddlewareElement] = get_middleware_list_recursive(
                self.simulation_env)
            if middleware_list[0].level == middleware.level:
                # 미들웨어 레벨이 최상위 인 경우에만 super thing을 생성한다.
                MXTEST_LOG_DEBUG(
                    f'Super thing is created only in top middleware', MXTestLogLevel.WARN)

                if not self.config.middleware_config.manual:
                    super_thing_num = random.randint(self.config.middleware_config.random.super.thing_per_middleware[0],
                                                     self.config.middleware_config.random.super.thing_per_middleware[1])
                else:
                    super_thing_num = random.randint(middleware.super_thing_num[0],
                                                     middleware.super_thing_num[1])
            else:
                super_thing_num = 0
                super_thing_list = [
                    thing for thing in middleware.thing_list if thing.is_super]
                for super_thing in super_thing_list:
                    middleware.thing_list.remove(super_thing)

            # 이미 생성된 super thing이 있으면, 기존 thing에 누적해서 추가분을 더 생성
            prev_super_thing_num = len(
                [thing for thing in middleware.thing_list if thing.is_super])
            for index in range(super_thing_num - prev_super_thing_num):
                thing_name, device, fail_rate, _ = self.generate_thing_property(middleware=middleware,
                                                                                index=index + prev_super_thing_num,
                                                                                is_super=True,
                                                                                service_list=[])
                super_service_list = service_generator.generate_super(
                    middleware=middleware, thing_config=self.config.thing_config)

                # NOTE: super thing은 항상 is_parallel=True 이다.
                super_thing = MXThingElement(name=thing_name,
                                             level=middleware.level,
                                             element_type=MXElementType.THING,
                                             service_list=super_service_list,
                                             is_super=True,
                                             is_parallel=True,
                                             alive_cycle=300,
                                             device=device,
                                             thing_file_path=f'{simulation_folder_path}/thing/super_thing/{thing_name}.py',
                                             remote_thing_file_path=f'{self.config.thing_config.remote_thing_folder_path}/super_thing/{thing_name}.py',
                                             fail_rate=fail_rate)
                MXTEST_LOG_DEBUG(
                    f'generate super thing: {super_thing.name} (level: {super_thing.level})', MXTestLogLevel.PASS)
                for service in super_thing.service_list:
                    service.level = middleware.level
                middleware.thing_list.append(super_thing)

            for child_middleware in middleware.child_middleware_list:
                generate_super_recursive(child_middleware, service_generator)

        self.simulation_env = simulation_env

        generate_super_recursive(simulation_env, service_generator)
        return simulation_env


class MXScenarioGenerator(MXElementGenerator):

    def __init__(self, config: MXSimulationConfig = None) -> None:
        super().__init__(config)

        self.scenario_config = self.config.application_config
        self.middleware_config = self.config.middleware_config

        self.scenario_pool: List[MXScenarioElement] = []
        self.super_scenario_pool: List[MXScenarioElement] = []

    def make_scenario_name(self, is_super: bool, index: int, middleware: MXMiddlewareElement):
        middleware_index = '_'.join(
            middleware.name.split('_')[1:])  # levelN_M
        prefix = 'super' if is_super else 'normal'
        name = f'{prefix}_scenario_{middleware_index}_{index}'.replace(
            ' ', '_')

        return name

    def generate(self, simulation_env: MXMiddlewareElement, simulation_folder_path: str):

        def generate_recursive(middleware: MXMiddlewareElement):
            whole_service_list: List[MXServiceElement] = []
            for thing in middleware.thing_list:
                if thing.is_super:
                    continue
                whole_service_list += thing.service_list

            if not self.middleware_config.manual:
                scenario_num = random.randint(self.middleware_config.random.normal.scenario_per_middleware[0],
                                              self.middleware_config.random.normal.scenario_per_middleware[1])
            else:
                scenario_num = random.randint(middleware.scenario_num[0],
                                              middleware.scenario_num[1])

            # 이미 생성된 scenario가 있으면, 기존 scenario에 누적해서 추가분을 더 생성
            prev_scenario_num = len([scenario for scenario in middleware.scenario_list if not all(
                [service.is_super for service in scenario.service_list])])
            for index in range(scenario_num - prev_scenario_num):
                # NOTE: 반드시 아래조건을 만족해야한다.
                # thing_num * service_per_thing > service_per_application
                service_per_application = random.randint(self.config.application_config.normal.service_per_application[0],
                                                         min(self.config.application_config.normal.service_per_application[1], len(whole_service_list)))
                picked_service_list: List[MXServiceElement] = random.sample(
                    whole_service_list, k=service_per_application)
                scenario_name = self.make_scenario_name(
                    False, index + prev_scenario_num, middleware)

                period = random.uniform(self.config.application_config.normal.period[0],
                                        self.config.application_config.normal.period[1])

                scenario = MXScenarioElement(name=scenario_name,
                                             level=middleware.level,
                                             element_type=MXElementType.SCENARIO,
                                             service_list=picked_service_list,
                                             period=period,
                                             scenario_file_path=f'{simulation_folder_path}/application/base_application/{scenario_name}.txt')
                MXTEST_LOG_DEBUG(
                    f'generate scenario: {scenario.name} (level: {scenario.level})', MXTestLogLevel.PASS)
                middleware.scenario_list.append(scenario)

            for child_middleware in middleware.child_middleware_list:
                generate_recursive(child_middleware)

        generate_recursive(simulation_env)

    def generate_super(self, simulation_env: MXMiddlewareElement, simulation_folder_path: str):

        def generate_super_recursive(middleware: MXMiddlewareElement, upper_middleware_list: List[MXMiddlewareElement]):
            whole_super_service_list: List[MXServiceElement] = []
            for middleware in upper_middleware_list:
                for thing in middleware.thing_list:
                    if not thing.is_super:
                        continue
                    whole_super_service_list += thing.service_list

            middleware_list: List[MXMiddlewareElement] = sorted(
                get_middleware_list_recursive(simulation_env), key=lambda x: x.level)
            if middleware.level == middleware_list[0].level or middleware.level == middleware_list[-1].level:
                # 미들웨어 레벨이 최상위, 최하위인 경우에만 super scenario를 생성한다.
                MXTEST_LOG_DEBUG(
                    f'Super scenario is created only in top, bottom middleware', MXTestLogLevel.WARN)
                if not self.middleware_config.manual:
                    super_scenario_num = random.randint(self.middleware_config.random.super.scenario_per_middleware[0],
                                                        self.middleware_config.random.super.scenario_per_middleware[1])
                else:
                    super_scenario_num = random.randint(middleware.super_scenario_num[0],
                                                        middleware.super_scenario_num[1])
            else:
                super_scenario_num = 0
                super_scenario_list = [
                    scenario for scenario in middleware.scenario_list if scenario.is_super()]
                for super_scenario in super_scenario_list:
                    middleware.scenario_list.remove(super_scenario)

            # 이미 생성된 super scenario가 있으면, 기존 super scenario에 누적해서 추가분을 더 생성
            prev_super_scenario_num = len([scenario for scenario in middleware.scenario_list if all(
                [service.is_super for service in scenario.service_list])])
            for index in range(super_scenario_num - len([scenario for scenario in middleware.scenario_list if all([service.is_super for service in scenario.service_list])])):
                service_per_application = random.randint(self.config.application_config.super.service_per_application[0],
                                                         min(self.config.application_config.super.service_per_application[1], len(whole_super_service_list)))
                picked_service_list: List[MXServiceElement] = random.sample(
                    whole_super_service_list, k=service_per_application)
                scenario_name = self.make_scenario_name(
                    True, index + prev_super_scenario_num, middleware)

                period = random.uniform(self.config.application_config.super.period[0],
                                        self.config.application_config.super.period[1])

                scenario = MXScenarioElement(name=scenario_name,
                                             level=middleware.level,
                                             element_type=MXElementType.SCENARIO,
                                             service_list=picked_service_list,
                                             period=period,
                                             scenario_file_path=f'{simulation_folder_path}/application/super_application/{scenario_name}.txt')
                MXTEST_LOG_DEBUG(
                    f'generate super scenario: {scenario.name} (level: {scenario.level})', MXTestLogLevel.PASS)
                middleware.scenario_list.append(scenario)

            for child_middleware in middleware.child_middleware_list:
                generate_super_recursive(
                    child_middleware, upper_middleware_list + [child_middleware])

        generate_super_recursive(simulation_env, [simulation_env])
