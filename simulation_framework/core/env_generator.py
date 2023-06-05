from simulation_framework.core.simulator import *

import random
import copy
import requests
from abc import ABCMeta, abstractmethod
from getpass import getpass
import platform


def print_middleware_tree(root_middleware: SoPMiddleware, show: Callable = lambda node: None):
    pre: str
    fill: str
    node: SoPMiddleware
    cprint(f'==== Middleware Tree Structure ====', 'green')
    for pre, fill, node in RenderTree(root_middleware):
        cprint(f'{pre}{node.name} - {show(node)}', 'cyan')


class SoPComponentGenerateMode(Enum):
    ALL_RANDOM = 'all_random'
    APPEND = 'append'
    APPEND_WITH_REMAPPING = 'append_with_remapping'

    UNDEFINED = 'UNDEFINED'

    def __str__(self):
        return self.value

    @classmethod
    def get(cls, name: str):
        try:
            return cls[name.upper()]
        except Exception:
            return cls.UNDEFINED


class SoPEnvGenerator:
    _PREDEFINED_KEYWORD_LIST = ['if', 'else', 'and', 'or', 'loop', 'wait_until', 'msec', 'list', 'normal', 'super',
                                'sec', 'min', 'hour', 'day', 'month', 'all', 'single', 'random']

    def __init__(self, service_parallel: bool) -> None:
        self._service_parallel = service_parallel

        self._service_pool: List[SoPService] = []
        self._thing_pool: List[SoPThing] = []
        self._config: SoPSimulationConfig = None

        self._tag_name_pool: List[str] = []
        self._service_name_pool: List[str] = []
        self._super_service_name_pool: List[str] = []

        self._generate_start_time: str = datetime.now().strftime('%Y%m%d_%H%M%S')

        # self._middleware_generator: SoPMiddlewareGenerator = None
        # self._thing_generator: SoPThingGenerator = None
        # self._scenario_generator: SoPServiceGenerator = None

    def load(self, config: SoPSimulationConfig):
        """A method to load SoPEvnGenerator for generate simulation environment

        Args:
            service_pool (List[SoPService]): Generated service pool
            thing_pool (List[SoPThing]): Generated thing pool
            config (SoPSimulationConfig): simulation environment config

        Raises:
            Exception: _description_
        """
        self._config = config

        self._middleware_device_pool: List[SoPDevice] = []
        self._thing_device_pool: List[SoPDevice] = []

        device_pool_path = self._config.device_pool_path.abs_path()
        if not os.path.exists(device_pool_path):
            save_yaml(device_pool_path, {})

        device_pool_dict = load_yaml(device_pool_path)
        if not 'localhost' in device_pool_dict:
            SOPTEST_LOG_DEBUG(f'localhost device config is not exist in device pool...', SoPTestLogLevel.WARN)
            device_pool_dict = self._add_localhost_info(device_pool_dict)
            save_yaml(device_pool_path, device_pool_dict)

        device_pool = self._load_device_pool(device_pool_path)

        # If local_mode is True, the program terminates if device_pool is defined or if localhost
        # does not exist in device_pool.
        if self._config.local_mode:
            SOPTEST_LOG_DEBUG(f'local_mode is True, below config will be ignored. \n'
                              'device pool                    (simulation.device_pool) \n'
                              'manual middleware config path  (middleware.manual)', SoPTestLogLevel.WARN)
            self._middleware_device_pool = [device for device in device_pool if device.name == 'localhost']
            self._thing_device_pool = [device for device in device_pool if device.name == 'localhost']
        else:
            if not self._config.middleware_config.device_pool:
                self._middleware_device_pool = [device for device in device_pool if device.name != 'localhost']
            else:
                self._middleware_device_pool = [device for device in device_pool if device.name in self._config.middleware_config.device_pool]

            # In the case of things, it defaults to running on a simulator device with relatively
            # high performance rather than running on an embedded device with low performance.
            if not self._config.thing_config.device_pool:
                self._thing_device_pool = [device for device in device_pool if device.name == 'localhost']
            else:
                self._thing_device_pool = [device for device in device_pool if device.name in self._config.thing_config.device_pool]

        manual_middleware_tree = self._config.middleware_config.manual_middleware_tree
        if manual_middleware_tree:
            if self._config.middleware_config.random:
                SOPTEST_LOG_DEBUG('random is defined in middleware config, but manual_middleware_tree is defined. '
                                  'random config will be ignored.', SoPTestLogLevel.WARN)
                self._config.middleware_config.random = None
            middleware_num = len(manual_middleware_tree.descendants) + 1
        elif self._config.middleware_config.random:
            self._middleware_device_pool = [device for device in device_pool if device.name != 'localhost']
            self._thing_device_pool = [device for device in device_pool if device.name == 'localhost']
            self._config.middleware_config.manual = None
            middleware_num = calculate_tree_node_num(self._config.middleware_config.random.height[1], self._config.middleware_config.random.width[1])
        else:
            raise Exception('If manual_middleware_tree is not defined, random config must be defined.')

        remote_device_list = [device for device in device_pool if device.name != 'localhost']
        if not self._config.local_mode and len(remote_device_list) < middleware_num:
            raise Exception(f'device pool is not enough for {os.path.basename(os.path.dirname(self._config.config_path))} simulation. (Requires at least {middleware_num} devices)')

        # self._service_generator = SoPServiceGenerator(self._config)
        # self._thing_generator = SoPThingGenerator(self._config, thing_device_pool)
        # self._middleware_generator = SoPMiddlewareGenerator(self._config, middleware_device_pool)
        # self._scenario_generator = SoPScenarioGenerator(self._config)

    def _generate_random_words(self, num_word: int = None, user_word_dictionary_file: List[str] = [], ban_word_list: List[str] = []) -> List[str]:
        selected_words: List[str] = []
        words_pool: List[str] = []

        # If user word dictionary file is provided, load it and use it as words pool
        if user_word_dictionary_file:
            if os.path.exists(user_word_dictionary_file):
                words_pool = read_file(user_word_dictionary_file)
            else:
                raise Exception(f'Invalid word dictionary file path! - {user_word_dictionary_file}')
        # Else, use default word pool. If default word pool file is not found, load it from online
        else:
            default_words_pool_path = f'{get_project_root()}/data/words_pool.txt'
            if os.path.exists(default_words_pool_path):
                words_pool = read_file(default_words_pool_path)
            else:
                response = requests.get("https://www.mit.edu/~ecprice/wordlist.10000")
                words_pool = [f'{word.decode()}\n' for word in response.content.splitlines()]
                write_file(default_words_pool_path, words_pool)

        # Remove duplicated words
        words_pool = list(set(words_pool))

        # Remove ban words
        for ban_word in ban_word_list:
            if ban_word not in words_pool:
                continue
            words_pool.remove(ban_word)

        # Select words from word pool
        while num_word:
            picked_word = random.choice(words_pool)
            if picked_word in selected_words:
                continue
            selected_words.append(picked_word)
            num_word -= 1

        return selected_words

    def generate_name_pool(self, ban_name_list: List[str] = []) -> Tuple[List[str], List[str]]:
        tag_type_num = self._config.service_config.tag_type_num
        service_type_num = self._config.service_config.normal.service_type_num
        # super_service_type_num = self._config.service_config.super.service_type_num

        ban_name_list = ban_name_list + self._PREDEFINED_KEYWORD_LIST

        tag_name_pool = random.sample(self._generate_random_words(num_word=tag_type_num * 10,
                                                                  ban_word_list=ban_name_list), tag_type_num)
        service_name_pool = random.sample(self._generate_random_words(num_word=service_type_num * 10,
                                                                      ban_word_list=ban_name_list), service_type_num)
        # super_service_name_pool = random.sample(self._generate_random_words(num_word=super_service_type_num * 10,
        #                                                                     ban_word_list=ban_name_list), super_service_type_num)
        return tag_name_pool, service_name_pool

    def generate_service_pool(self, tag_name_pool: List[str], service_name_pool: List[str]) -> List[SoPService]:
        service_pool = []
        for service_name in service_name_pool:
            tag_per_service_range = self._config.service_config.tag_per_service
            energy_range = self._config.service_config.normal.energy
            execute_time_range = self._config.service_config.normal.execute_time
            return_value_range = (0, 1000)

            service_name = f'function_{service_name}'
            level = -1
            tag_per_service = random.randint(*tag_per_service_range)
            tag_list = random.sample(tag_name_pool, tag_per_service)
            energy = random.randint(*energy_range)
            execute_time = random.uniform(*execute_time_range)
            return_value = random.randint(*return_value_range)

            service = SoPService(name=service_name,
                                 level=level,
                                 tag_list=tag_list,
                                 is_super=False,
                                 energy=energy,
                                 execute_time=execute_time,
                                 return_value=return_value)
            service_pool.append(service)
        SOPTEST_LOG_DEBUG(f'Generated service pool size of {len(service_pool)}', SoPTestLogLevel.INFO)
        return service_pool

    def generate_thing_pool(self, service_pool: List[SoPService]) -> List[SoPThing]:
        manual_middleware_tree = self._config.middleware_config.manual_middleware_tree
        if manual_middleware_tree:
            middleware_config_list = [manual_middleware_tree] + list(manual_middleware_tree.descendants)
            max_thing_num = sum([middleware_config.thing_num[1] for middleware_config in middleware_config_list])
        else:
            max_middleware_num = calculate_tree_node_num(self._config.middleware_config.random.height[1], self._config.middleware_config.random.width[1])
            max_thing_num = max_middleware_num * self._config.middleware_config.random.normal.thing_per_middleware[1]

        thing_pool = []
        for _ in range(max_thing_num):
            device = random.choice(self._thing_device_pool)
            thing_name = ''
            level = -1
            is_super = False
            fail_rate = self._config.thing_config.normal.fail_error_rate
            # broken_rate = self._config.thing_config.normal.broken_rate
            # unregister_rate = self._config.thing_config.normal.unregister_rate

            service_per_thing_range = self._config.thing_config.normal.service_per_thing
            service_per_thing = random.randint(*service_per_thing_range)
            selected_service_list = random.sample(service_pool, service_per_thing)

            # set trade off between energy and execute time
            # if energy is getting high, execute time will be getting low
            selected_service_list_copy = copy.deepcopy(selected_service_list)
            for service in selected_service_list_copy:
                thing_w = random.uniform(0, 0.5)
                service.execute_time = service.execute_time * (1 - thing_w)
                service.energy = service.energy * (1 + thing_w)

            config_dir = os.path.dirname(self._config.config_path)
            simulation_folder_path = f'{config_dir}/simulation_{self._config.name}_{self._generate_start_time}'
            thing = SoPThing(name=thing_name,
                             level=level,
                             service_list=selected_service_list_copy,
                             is_super=is_super,
                             is_parallel=self._service_parallel,
                             alive_cycle=60 * 5,
                             device=device,
                             thing_file_path=f'{simulation_folder_path}/thing/base_thing/{thing_name}.py',
                             remote_thing_file_path=f'{self._config.thing_config.remote_thing_folder_path}/base_thing/{thing_name}.py',
                             fail_rate=fail_rate)
            for service in thing.service_list:
                service.thing = thing

            thing_pool.append(thing)

        SOPTEST_LOG_DEBUG(f'Generated thing pool size of {max_thing_num}', SoPTestLogLevel.INFO)
        return thing_pool

    def generate_middleware_tree(self, thing_pool: List[SoPThing]) -> SoPMiddleware:
        device_pool = copy.deepcopy(self._middleware_device_pool)
        manual_middleware_tree = self._config.middleware_config.manual_middleware_tree

        if manual_middleware_tree:
            def manual_inner(node: SoPMiddleware, config_node: AnyNode, index: int) -> SoPMiddleware:
                height = config_node.height + 1
                if config_node.is_root:
                    middleware_name = f'middleware_level{height}_0'
                else:
                    middleware_name = f'{node.name}__middleware_level{height}_{index}'
                device = random.choice(device_pool)
                device_pool.remove(device)

                middleware = SoPMiddleware(name=middleware_name,
                                           level=height,
                                           thing_list=[],
                                           scenario_list=[],
                                           children=[],
                                           device=device,
                                           remote_middleware_path=self._config.middleware_config.remote_middleware_path,
                                           remote_middleware_config_path=self._config.middleware_config.remote_middleware_config_path,
                                           mqtt_port=device.mqtt_port)
                if height == 1:
                    return middleware

                for index, child_middleware_config in enumerate(config_node.children):
                    child_middleware = manual_inner(node=middleware, config_node=child_middleware_config, index=index)
                    child_middleware.parent = middleware

                return middleware

            root_middleware = manual_inner(node=None, config_node=manual_middleware_tree, index=0)
        elif self._config.middleware_config.random:
            def random_inner(node: SoPMiddleware, height: int, width_range: ConfigRandomIntRange, index: int) -> SoPMiddleware:
                if node == None:
                    middleware_name = f'middleware_level{height}_0'
                else:
                    middleware_name = f'{node.name}__middleware_level{height}_{index}'
                device = random.choice(device_pool)
                device_pool.remove(device)

                middleware = SoPMiddleware(name=middleware_name,
                                           level=height,
                                           thing_list=[],
                                           scenario_list=[],
                                           children=[],
                                           device=device,
                                           remote_middleware_path=self._config.middleware_config.remote_middleware_path,
                                           remote_middleware_config_path=self._config.middleware_config.remote_middleware_config_path,
                                           mqtt_port=device.mqtt_port)

                if height == 1:
                    return middleware

                width = random.randint(*width_range)
                for index in range(width):
                    child_middleware = random_inner(middleware, height - 1, width_range=width_range, index=index)
                    child_middleware.parent = middleware
                return middleware

            height_range = self._config.middleware_config.random.height
            width_range = self._config.middleware_config.random.width
            height = random.randint(*height_range)
            root_middleware = random_inner(node=None, height=height, width_range=width_range, index=0)
        else:
            raise Exception('Unknown error')

        print_middleware_tree(root_middleware)
        return root_middleware

    def map_thing_to_middleware(self, root_middleware: SoPMiddleware, thing_pool: List[SoPThing]) -> None:
        manual_middleware_tree = self._config.middleware_config.manual_middleware_tree

        if manual_middleware_tree:
            def manual_inner(node: SoPMiddleware, config_node: AnyNode) -> None:
                thing_per_middleware_range = config_node.thing_num
                thing_per_middleware = random.randint(*thing_per_middleware_range)
                selected_thing_list = random.sample(thing_pool, thing_per_middleware)
                node.thing_list = selected_thing_list

                for index, thing in enumerate(node.thing_list):
                    thing.middleware = node
                    thing.level = node.level + 1
                    thing.name = f'normal_thing_{index}__{node.name}'

                if not node.children:
                    return
                for child_middleware, child_middleware_config in zip(node.children, config_node.children):
                    manual_inner(node=child_middleware, config_node=child_middleware_config)

            manual_inner(node=root_middleware, config_node=manual_middleware_tree)
        elif self._config.middleware_config.random:
            thing_per_middleware_range = self._config.middleware_config.random.normal.thing_per_middleware

            def random_inner(node: SoPMiddleware) -> SoPMiddleware:
                thing_per_middleware = random.randint(*thing_per_middleware_range)
                selected_thing_list = random.sample(thing_pool, thing_per_middleware)
                node.thing_list = selected_thing_list

                for index, thing in enumerate(node.thing_list):
                    thing.middleware = node
                    thing.level = node.level + 1
                    thing.name = f'normal_thing_{index}__{node.name}'

                if not node.children:
                    return
                for child_middleware in node.children:
                    random_inner(child_middleware)

            random_inner(node=root_middleware)
        else:
            raise Exception('Unknown error')

        print_middleware_tree(root_middleware=root_middleware, show=lambda node: '\n'.join([f'{thing.name} level: {thing.level} service_num: {len(thing.service_list)}' for thing in node.thing_list]))

    def generate_super_thing_pool(self, root_middleware: SoPMiddleware, service_pool: List[SoPService]) -> List[SoPThing]:
        pass

    def generate(self):
        simulation_folder_path = f'{os.path.dirname(self._config.config_path)}/simulation_{self._config.name}_{get_current_time(TimeFormat.DATETIME2)}'
        SOPTEST_LOG_DEBUG(f'Generate simulation: {simulation_folder_path}', SoPTestLogLevel.INFO)

        if not self._service_pool:
            self._service_generator.generate(simulation_folder_path)

        if simulation_ID:
            simulation_env = self.simulation_env_pool[simulation_ID]['simulation_env']
            base_service_pool = self.simulation_env_pool[simulation_ID]['base_service_pool']
            simulation_config = self.simulation_env_pool[simulation_ID]['simulation_config']

            simulation_env = self._middleware_generator.generate(simulation_env=simulation_env)

            simulation_env = self._thing_generator.generate(simulation_env, base_service_pool, simulation_folder_path, is_parallel=service_parallel)
            simulation_env = self._thing_generator.generate_super(simulation_env, self._service_generator, simulation_folder_path)

            self._scenario_generator.generate(simulation_env, simulation_folder_path)
            self._scenario_generator.generate_super(simulation_env, simulation_folder_path)

            self.simulation_env = simulation_env

            simulation_data = self.generate_data(simulation_env)
            simulation_file_path = self.export_simulation_data_file(simulation_data, simulation_folder_path)
        else:
            simulation_env = self._middleware_generator.generate()

            base_service_pool = self._service_generator.generate()

            simulation_env = self._thing_generator.generate(simulation_env, base_service_pool, simulation_folder_path, is_parallel=service_parallel)
            simulation_env = self._thing_generator.generate_super(simulation_env, self._service_generator, simulation_folder_path)

            self._scenario_generator.generate(simulation_env, simulation_folder_path)
            self._scenario_generator.generate_super(simulation_env, simulation_folder_path)

            self.simulation_env = simulation_env

            simulation_data = self.generate_data(simulation_env)
            simulation_file_path = self.export_simulation_data_file(simulation_data, simulation_folder_path)

            simulation_ID = generate_random_string(16)
            self.simulation_env_pool[simulation_ID] = dict(simulation_env=simulation_env, base_service_pool=base_service_pool, simulation_config=self.simulation_config)

        return simulation_file_path, simulation_ID

    def _generate_event(self, component: SoPComponent, event_type: SoPEventType, timestamp: float = 0.0, **kwargs) -> SoPEvent:
        event_kwargs = dict(component=component, event_type=event_type, timestamp=timestamp)
        event_kwargs.update(kwargs)
        event = SoPEvent(**event_kwargs)
        return event

    def _generate_event_timeline(self, middleware_list: List[SoPMiddleware], thing_list: List[SoPThing], scenario_list: List[SoPScenario],
                                 running_time: float, event_timeout: float):
        event_timeline: List[SoPEvent] = []

        def make_dynamic_thing_event(local_thing_list: List[SoPThing], super_thing_list: List[SoPThing],
                                     normal_thing_select_rate: float, super_thing_select_rate: float,
                                     start_time_weight: float, end_time_weight: float, event_type: SoPEventType, delay: float):
            if event_type == SoPEventType.THING_UNREGISTER:
                event_type_1 = SoPEventType.THING_UNREGISTER
                event_type_2 = SoPEventType.THING_RUN
            elif event_type == SoPEventType.THING_KILL:
                event_type_1 = SoPEventType.THING_KILL
                event_type_2 = SoPEventType.THING_RUN
            else:
                raise Exception('invalid event type')

            selected_local_thing_list = random.sample(local_thing_list, int(len(local_thing_list) * normal_thing_select_rate))
            selected_super_thing_list = random.sample(super_thing_list, int(len(super_thing_list) * super_thing_select_rate))
            local_thing_unregister_timeline = [self._generate_event(component=thing, event_type=event_type_1, timestamp=self.simulation_config.running_time * start_time_weight).dict()
                                               for thing in selected_local_thing_list]
            super_thing_unregister_timeline = [self._generate_event(component=thing, event_type=event_type_1, timestamp=self.simulation_config.running_time * start_time_weight).dict()
                                               for thing in selected_super_thing_list]
            local_thing_register_timeline = [self._generate_event(component=thing, event_type=event_type_2, timestamp=self.simulation_config.running_time * end_time_weight).dict()
                                             for thing in selected_local_thing_list]
            super_thing_register_timeline = [self._generate_event(component=thing, event_type=event_type_2, timestamp=self.simulation_config.running_time * end_time_weight).dict()
                                             for thing in selected_super_thing_list]

            tmp_timeline = local_thing_unregister_timeline + super_thing_unregister_timeline + local_thing_register_timeline + super_thing_register_timeline
            if delay:
                tmp_timeline += [SoPEvent(delay=delay, event_type=SoPEventType.DELAY).dict()]
            return tmp_timeline

        # def make_scenario_event(local_scenario_list: List[SoPScenarioComponent], super_scenario_list: List[SoPScenarioComponent],
        #                         start_time_weight: float, end_time_weight: float, event_type: SoPEventType, delay: float):
        #     if event_type == SoPEventType.SCENARIO_STOP:
        #         event_type_1 = SoPEventType.SCENARIO_STOP
        #         event_type_2 = SoPEventType.SCENARIO_RUN
        #     elif event_type == SoPEventType.SCENARIO_DELETE:
        #         event_type_1 = SoPEventType.SCENARIO_DELETE
        #         event_type_2 = SoPEventType.SCENARIO_ADD
        #         # event_type_3 = SoPEventType.SCENARIO_RUN
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
        #         tmp_timeline += [SoPEvent(delay=delay,
        #                                   event_type=SoPEventType.DELAY).dict()]
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
        build_simulation_env_timeline.extend([self._generate_event(component=middleware, event_type=SoPEventType.MIDDLEWARE_RUN).dict()
                                              for middleware in middleware_list])
        build_simulation_env_timeline.extend([self._generate_event(component=thing, event_type=SoPEventType.THING_RUN).dict()
                                              for thing in sorted(thing_list, key=lambda x: x.is_super, reverse=False)])
        event_timeline.extend(build_simulation_env_timeline)

        # wait until all thing register
        event_timeline.append(
            SoPEvent(event_type=SoPEventType.THING_REGISTER_WAIT).dict())

        event_timeline.append(
            SoPEvent(delay=5, event_type=SoPEventType.DELAY).dict())

        # scenario add start
        scenario_add_timeline = [self._generate_event(component=scenario, event_type=SoPEventType.SCENARIO_ADD, middleware_component=find_component_recursive(self.simulation_env, scenario)[1]).dict()
                                 for scenario in scenario_list]
        event_timeline.extend(
            sorted(scenario_add_timeline, key=lambda x: x['timestamp']))

        event_timeline.append(
            SoPEvent(event_type=SoPEventType.SCENARIO_ADD_CHECK).dict())

        event_timeline.append(
            SoPEvent(delay=5, event_type=SoPEventType.DELAY).dict())

        event_timeline.append(
            SoPEvent(event_type=SoPEventType.REFRESH).dict())

        # simulation start
        event_timeline.append(
            SoPEvent(event_type=SoPEventType.START).dict())

        # scenario run start
        scenario_run_timeline = [self._generate_event(component=scenario, event_type=SoPEventType.SCENARIO_RUN).dict()
                                 for scenario in scenario_list]
        event_timeline.extend(
            sorted(scenario_run_timeline, key=lambda x: x['timestamp']))

        # thing unregister stage
        thing_unregister_timeline = make_dynamic_thing_event(local_thing_list=local_thing_list, super_thing_list=super_thing_list,
                                                             normal_thing_select_rate=self.simulation_config.thing_config.normal.unregister_rate,
                                                             super_thing_select_rate=self.simulation_config.thing_config.super.unregister_rate,
                                                             start_time_weight=0.2, end_time_weight=0.7, event_type=SoPEventType.THING_UNREGISTER, delay=0)
        event_timeline.extend(thing_unregister_timeline)

        # thing kill stage
        thing_kill_timeline = make_dynamic_thing_event(local_thing_list=local_thing_list, super_thing_list=super_thing_list,
                                                       normal_thing_select_rate=self.simulation_config.thing_config.normal.broken_rate,
                                                       super_thing_select_rate=self.simulation_config.thing_config.super.broken_rate,
                                                       start_time_weight=0.5, end_time_weight=10, event_type=SoPEventType.THING_KILL, delay=0)
        event_timeline.extend(thing_kill_timeline)

        # scenario stop stage
        # scenario_stop_timeline = make_scenario_event(local_scenario_list=non_super_scenario_list, super_scenario_list=super_scenario_list,
        #                                              start_time_weight=0.3, end_time_weight=0.8, event_type=SoPEventType.SCENARIO_STOP, delay=0)
        # event_timeline.extend(scenario_stop_timeline)

        # simulation end
        event_timeline.append(
            SoPEvent(event_type=SoPEventType.END, timestamp=running_time).dict())
        event_timeline = sorted(event_timeline, key=lambda x: x['timestamp'])
        end_index = 0
        for i, event in enumerate(event_timeline):
            if event['event_type'] == 'END':
                end_index = i
                break

        return event_timeline[:end_index+1]

    def generate_data(self, simulation_env: SoPMiddleware):
        # generate simulation env
        middleware_list: List[SoPMiddleware] = get_middleware_list_recursive(simulation_env)
        thing_list: List[SoPThing] = get_thing_list_recursive(simulation_env)
        scenario_list: List[SoPScenario] = get_scenario_list_recursive(simulation_env)

        longest_scenario = max(scenario_list, key=lambda x: x.period)
        if longest_scenario.period * 1.2 > self.simulation_config.running_time:
            running_time = longest_scenario.period * 1.2
            SOPTEST_LOG_DEBUG(
                f'Longest scenario period is {longest_scenario.period} but simulation time is {self.simulation_config.running_time}. Set simulation time to {running_time}', SoPTestLogLevel.WARN)
        else:
            running_time = self.simulation_config.running_time

        config = dict(name=self.simulation_config.name,
                      running_time=running_time,
                      event_timeout=self.simulation_config.event_timeout)
        component = simulation_env.dict()
        event_timeline = self._generate_event_timeline(middleware_list=middleware_list,
                                                       thing_list=thing_list,
                                                       scenario_list=scenario_list,
                                                       running_time=running_time,
                                                       event_timeout=self.simulation_config.event_timeout)
        simulation_dump = dict(config=config,
                               component=component,
                               event_timeline=event_timeline)
        return simulation_dump

    def export_simulation_data_file(self, simulation_dump: dict, simulation_folder_path: str):
        os.makedirs(simulation_folder_path, exist_ok=True)
        write_file(f'{simulation_folder_path}/simulation_data.json', dict_to_json_string(simulation_dump))
        return f'{simulation_folder_path}/simulation_data.json'

    def _load_device_pool(self, device_pool_path: str) -> List[SoPDevice]:
        device_list = load_yaml(device_pool_path)

        whole_device_pool = []
        for device_name, device_info in device_list.items():
            device = SoPDevice(
                name=device_name,
                component_type=SoPComponentType.DEVICE,
                host=device_info['host'],
                ssh_port=device_info['ssh_port'],
                user=device_info['user'],
                password=device_info['password'],
                mqtt_port=device_info.get('mqtt_port', None),
                mqtt_ssl_port=device_info.get('mqtt_ssl_port', 'Not used'),
                websocket_port=device_info.get('websocket_port', 'Not used'),
                websocket_ssl_port=device_info.get('websocket_ssl_port', 'Not used'),
                localserver_port=device_info.get('localserver_port', 58132))
            whole_device_pool.append(device)
        return whole_device_pool

    # =========================
    #         _    _  _
    #        | |  (_)| |
    #  _   _ | |_  _ | | ___
    # | | | || __|| || |/ __|
    # | |_| || |_ | || |\__ \
    #  \__,_| \__||_||_||___/
    # =========================

    def _read_ssh_config(self) -> dict:
        """A method that reads sshd_config and returns it as a dict

        Raises:
            Exception: raise if the OS platform is not Linux or MacOS

        Returns:
            dict: device pool data
        """
        if not platform.system() in ['Linux', 'Darwin']:
            raise Exception(f'{platform.system()} platform is not supported')

        with open('/etc/ssh/sshd_config', 'r') as file:
            ssh_config = {}
            for line in file:
                line = line.strip()
                if line.startswith('#'):
                    continue
                if not line:
                    continue

                line = line.split()
                ssh_config[line[0]] = line[1:]
        return ssh_config

    def _add_localhost_info(self, device_pool: dict) -> dict:
        """A method that add localhost device connection information to device_pool

        Args:
            device_pool (dict): device pool data

        Raises:
            Exception: _description_

        Returns:
            dict: _description_
        """

        ssh_config = self._read_ssh_config()
        if 'Port' in ssh_config:
            ssh_port = int(ssh_config['Port'][0])
        else:
            ssh_port = 22
        user = os.path.basename(os.path.expanduser('~'))
        password = getpass(f'Enter password of user [{user}]: ')
        localhost_info = dict(localhost=dict(host='localhost',
                                             ssh_port=ssh_port,
                                             user=user,
                                             password=password))

        test_ssh_client = SoPSSHClient(device=SoPDevice(name='test_localhost',
                                                        host='localhost',
                                                        ssh_port=ssh_port,
                                                        user=user,
                                                        password=password))
        try:
            test_ssh_client.connect()
        except Exception as e:
            raise Exception(f'Failed to connect to localhost. Please check ssh config. {e}')
        else:
            test_ssh_client.disconnect()

        updated_device_pool = {}
        updated_device_pool.update(localhost_info)
        updated_device_pool.update(device_pool)
        return updated_device_pool

    def _make_thing_name(self, index: int, is_super: bool):
        # normal_thing_level3_0__middleware_level2_0__middleware_level1_1_0
        prefix_name = 'super' if is_super else 'normal'
        name = f'{prefix_name}_thing_{middleware_index}_{index}'.replace(' ', '_')
        return name


# ===========================================================================================================================
#                                                            _                                            _
#                                                           | |                                          | |
#   ___   ___   _ __ ___   _ __    ___   _ __    ___  _ __  | |_    __ _   ___  _ __    ___  _ __   __ _ | |_   ___   _ __
#  / __| / _ \ | '_ ` _ \ | '_ \  / _ \ | '_ \  / _ \| '_ \ | __|  / _` | / _ \| '_ \  / _ \| '__| / _` || __| / _ \ | '__|
# | (__ | (_) || | | | | || |_) || (_) || | | ||  __/| | | || |_  | (_| ||  __/| | | ||  __/| |   | (_| || |_ | (_) || |
#  \___| \___/ |_| |_| |_|| .__/  \___/ |_| |_| \___||_| |_| \__|  \__, | \___||_| |_| \___||_|    \__,_| \__| \___/ |_|
#                         | |                                       __/ |
#                         |_|                                      |___/
# ===========================================================================================================================

class SoPComponentGenerator(metaclass=ABCMeta):

    def __init__(self, config: SoPSimulationConfig = None) -> None:
        self._config: SoPSimulationConfig = config

    @abstractmethod
    def generate(self):
        pass


# ===================================================================================================
#                          _                                                      _
#                         (_)                                                    | |
#  ___   ___  _ __ __   __ _   ___   ___    __ _   ___  _ __    ___  _ __   __ _ | |_   ___   _ __
# / __| / _ \| '__|\ \ / /| | / __| / _ \  / _` | / _ \| '_ \  / _ \| '__| / _` || __| / _ \ | '__|
# \__ \|  __/| |    \ V / | || (__ |  __/ | (_| ||  __/| | | ||  __/| |   | (_| || |_ | (_) || |
# |___/ \___||_|     \_/  |_| \___| \___|  \__, | \___||_| |_| \___||_|    \__,_| \__| \___/ |_|
#                                           __/ |
#                                          |___/
# ===================================================================================================

class SoPServiceGenerator(SoPComponentGenerator):

    def generate_super(self, middleware: SoPMiddleware, thing_config: SoPThingConfig = None) -> List[SoPService]:

        def get_candidate_sub_service_list(super_middleware: SoPMiddleware):
            candidate_sub_service_list: List[SoPService] = []
            for thing in super_middleware.thing_list:
                candidate_sub_service_list.extend(
                    [service for service in thing.service_list if not service.is_super])
            for middleware in super_middleware.child_middleware_list:
                candidate_sub_service_list.extend(
                    get_candidate_sub_service_list(middleware))

            return candidate_sub_service_list

        # TODO: 다시 재작성할 것
        def generate_super_service_property(candidate_sub_service_list: List[SoPService],
                                            selected_sub_service_list: List[SoPService],
                                            super_service_list: List[SoPService]):
            while True:
                super_service_name = f'super_function_{random.choice(self.super_service_name_pool)}'
                if super_service_name not in [super_service.name for super_service in super_service_list]:
                    break
            tag_list = random.sample(self.tag_name_pool, random.randint(self._config.service_config.tag_per_service[0],
                                                                        self._config.service_config.tag_per_service[1]))

            # NOTE: super service의 energy, execute_time은 sub_service들의 합으로 계산된다. super service의 sub_service들의 매핑상태는
            # 미들웨어에 등록되기 전까지 알 수 없으므로 원칙적으로 energy, execute_time은 계산할 수 없다. 그러나 super service가 미들웨어에
            # 붙을 때 예상 execute time을 제공하고 있으므로, execute_time은 super service가 고른 sub_service들의중 가장 execute time이
            # 긴 조합으로 execute time을 계산하여 초기값으로 둔다.
            energy = 0
            execute_time = 0

            for sub_service in selected_sub_service_list:
                same_name_sub_service_list = [
                    candidate_service for candidate_service in candidate_sub_service_list if sub_service.name == candidate_service.name]
                execute_time += max(
                    [sub_service.execute_time for sub_service in same_name_sub_service_list])

            return super_service_name, tag_list, energy, execute_time

        self.thing_config = thing_config
        super_service_num = random.randint(self.thing_config.super.service_per_thing[0],
                                           self.thing_config.super.service_per_thing[1])
        candidate_service_list = get_candidate_sub_service_list(middleware)
        super_service_list = []
        for _ in range(super_service_num):
            # TODO: sup_service를 누적하는 기능 완료하기
            prev_sub_service_num = 0
            sub_service_num = random.randint(self._config.service_config.super.service_per_super_service[0],
                                             self._config.service_config.super.service_per_super_service[1])
            selected_service_list: List[SoPService] = random.sample(
                candidate_service_list, sub_service_num)
            super_service_name, tag_list, energy, execute_time = generate_super_service_property(
                candidate_sub_service_list=candidate_service_list, selected_sub_service_list=selected_service_list, super_service_list=super_service_list)

            super_service = SoPService(name=super_service_name,
                                       tag_list=tag_list,
                                       is_super=True,
                                       energy=energy,
                                       execute_time=execute_time,
                                       sub_service_list=selected_service_list)

            super_service_list.append(super_service)
        return super_service_list


# =========================================================================================
#  _    _      _                                                        _
# | |  | |    (_)                                                      | |
# | |_ | |__   _  _ __    __ _    __ _   ___  _ __    ___  _ __   __ _ | |_   ___   _ __
# | __|| '_ \ | || '_ \  / _` |  / _` | / _ \| '_ \  / _ \| '__| / _` || __| / _ \ | '__|
# | |_ | | | || || | | || (_| | | (_| ||  __/| | | ||  __/| |   | (_| || |_ | (_) || |
#  \__||_| |_||_||_| |_| \__, |  \__, | \___||_| |_| \___||_|    \__,_| \__| \___/ |_|
#                         __/ |   __/ |
#                        |___/   |___/
# =========================================================================================

class SoPThingGenerator(SoPComponentGenerator):

    def generate_super(self, simulation_env: SoPMiddleware, service_generator: SoPServiceGenerator, simulation_folder_path: str) -> SoPMiddleware:

        def inner(middleware: SoPMiddleware, service_generator: SoPServiceGenerator) -> SoPMiddleware:
            middleware_list: List[SoPMiddleware] = get_middleware_list_recursive(
                self.simulation_env)
            if middleware_list[0].level == middleware.level:
                # 미들웨어 레벨이 최상위 인 경우에만 super thing을 생성한다.
                SOPTEST_LOG_DEBUG(
                    f'Super thing is created only in top middleware', SoPTestLogLevel.WARN)

                if not self._config.middleware_config.manual:
                    super_thing_num = random.randint(self._config.middleware_config.random.super.thing_per_middleware[0],
                                                     self._config.middleware_config.random.super.thing_per_middleware[1])
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
                    middleware=middleware, thing_config=self._config.thing_config)

                # NOTE: super thing은 항상 is_parallel=True 이다.
                super_thing = SoPThing(name=thing_name,
                                       level=middleware.level,
                                       service_list=super_service_list,
                                       is_super=True,
                                       is_parallel=True,
                                       alive_cycle=300,
                                       device=device,
                                       thing_file_path=f'{simulation_folder_path}/thing/super_thing/{thing_name}.py',
                                       remote_thing_file_path=f'{self._config.thing_config.remote_thing_folder_path}/super_thing/{thing_name}.py',
                                       fail_rate=fail_rate)
                SOPTEST_LOG_DEBUG(
                    f'generate super thing: {super_thing.name} (level: {super_thing.level})', SoPTestLogLevel.PASS)
                for service in super_thing.service_list:
                    service.level = middleware.level
                middleware.thing_list.append(super_thing)

            for child_middleware in middleware.child_middleware_list:
                inner(child_middleware, service_generator)

        self.simulation_env = simulation_env

        inner(simulation_env, service_generator)
        return simulation_env


# ===========================================================================================================
#                                       _                                                 _
#                                      (_)                                               | |
#  ___   ___   ___  _ __    __ _  _ __  _   ___     __ _   ___  _ __    ___  _ __   __ _ | |_   ___   _ __
# / __| / __| / _ \| '_ \  / _` || '__|| | / _ \   / _` | / _ \| '_ \  / _ \| '__| / _` || __| / _ \ | '__|
# \__ \| (__ |  __/| | | || (_| || |   | || (_) | | (_| ||  __/| | | ||  __/| |   | (_| || |_ | (_) || |
# |___/ \___| \___||_| |_| \__,_||_|   |_| \___/   \__, | \___||_| |_| \___||_|    \__,_| \__| \___/ |_|
#                                                   __/ |
#                                                  |___/
# ===========================================================================================================

class SoPScenarioGenerator(SoPComponentGenerator):

    def __init__(self, config: SoPSimulationConfig = None) -> None:
        super().__init__(config)

        self.scenario_config = self._config.application_config
        self.middleware_config = self._config.middleware_config

        self.scenario_pool: List[SoPScenario] = []
        self.super_scenario_pool: List[SoPScenario] = []

    def make_scenario_name(self, is_super: bool, index: int, middleware: SoPMiddleware):
        middleware_index = '_'.join(
            middleware.name.split('_')[1:])  # levelN_M
        prefix = 'super' if is_super else 'normal'
        name = f'{prefix}_scenario_{middleware_index}_{index}'.replace(
            ' ', '_')

        return name

    def generate(self, simulation_env: SoPMiddleware, simulation_folder_path: str):

        def inner(middleware: SoPMiddleware):
            whole_service_list: List[SoPService] = []
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
                service_per_application = random.randint(self._config.application_config.normal.service_per_application[0],
                                                         min(self._config.application_config.normal.service_per_application[1], len(whole_service_list)))
                picked_service_list: List[SoPService] = random.sample(
                    whole_service_list, k=service_per_application)
                scenario_name = self.make_scenario_name(
                    False, index + prev_scenario_num, middleware)

                period = random.uniform(self._config.application_config.normal.period[0],
                                        self._config.application_config.normal.period[1])

                scenario = SoPScenario(name=scenario_name,
                                       level=middleware.level,
                                       service_list=picked_service_list,
                                       period=period,
                                       scenario_file_path=f'{simulation_folder_path}/application/base_application/{scenario_name}.txt')
                SOPTEST_LOG_DEBUG(
                    f'generate scenario: {scenario.name} (level: {scenario.level})', SoPTestLogLevel.PASS)
                middleware.scenario_list.append(scenario)

            for child_middleware in middleware.child_middleware_list:
                inner(child_middleware)

        inner(simulation_env)

    def generate_super(self, simulation_env: SoPMiddleware, simulation_folder_path: str):

        def inner(middleware: SoPMiddleware, upper_middleware_list: List[SoPMiddleware]):
            whole_super_service_list: List[SoPService] = []
            for middleware in upper_middleware_list:
                for thing in middleware.thing_list:
                    if not thing.is_super:
                        continue
                    whole_super_service_list += thing.service_list

            middleware_list: List[SoPMiddleware] = sorted(
                get_middleware_list_recursive(simulation_env), key=lambda x: x.level)
            if middleware.level == middleware_list[0].level or middleware.level == middleware_list[-1].level:
                # 미들웨어 레벨이 최상위, 최하위인 경우에만 super scenario를 생성한다.
                SOPTEST_LOG_DEBUG(
                    f'Super scenario is created only in top, bottom middleware', SoPTestLogLevel.WARN)
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
                service_per_application = random.randint(self._config.application_config.super.service_per_application[0],
                                                         min(self._config.application_config.super.service_per_application[1], len(whole_super_service_list)))
                picked_service_list: List[SoPService] = random.sample(
                    whole_super_service_list, k=service_per_application)
                scenario_name = self.make_scenario_name(
                    True, index + prev_super_scenario_num, middleware)

                period = random.uniform(self._config.application_config.super.period[0],
                                        self._config.application_config.super.period[1])

                scenario = SoPScenario(name=scenario_name,
                                       level=middleware.level,
                                       service_list=picked_service_list,
                                       period=period,
                                       scenario_file_path=f'{simulation_folder_path}/application/super_application/{scenario_name}.txt')
                SOPTEST_LOG_DEBUG(
                    f'generate super scenario: {scenario.name} (level: {scenario.level})', SoPTestLogLevel.PASS)
                middleware.scenario_list.append(scenario)

            for child_middleware in middleware.child_middleware_list:
                inner(
                    child_middleware, upper_middleware_list + [child_middleware])

        inner(simulation_env, [simulation_env])
