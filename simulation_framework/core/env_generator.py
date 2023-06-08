from simulation_framework.core.simulator import *

import random
import copy
import requests
from abc import ABCMeta, abstractmethod
from getpass import getpass
import platform


def print_middleware_tree(root_middleware: SoPMiddleware, show: Callable = lambda middleware: None):
    pre: str
    fill: str
    middleware: SoPMiddleware
    cprint(f'==== Middleware Tree Structure ====', 'green')
    for pre, fill, middleware in RenderTree(root_middleware):
        cprint(f'{pre}{middleware.name} - {show(middleware)}', 'cyan')


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
        self._config: SoPSimulationConfig

        self._generate_start_time: str = datetime.now().strftime('%Y%m%d_%H%M%S')
        self._simulation_folder_path: str = ''

        self._middleware_device_pool: List[SoPDevice] = []
        self._thing_device_pool: List[SoPDevice] = []

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
        self._simulation_folder_path = f'{os.path.dirname(self._config.config_path)}/simulation_{self._config.name}_{self._generate_start_time}'
        manual_middleware_tree = self._config.middleware_config.manual_middleware_tree
        random_middleware_config = self._config.middleware_config.random

        device_pool_path = self._config.device_pool_path.abs_path()
        self._check_device_pool(device_pool_path)
        global_device_pool = self._load_device_pool(device_pool_path)

        # If local_mode is True, the program terminates if device_pool is defined or if localhost
        # does not exist in device_pool.
        if self._config.local_mode:
            SOPTEST_LOG_DEBUG(f'local_mode is True, below config will be ignored. \n'
                              'device pool                    (middleware.device_pool) \n'
                              'manual middleware config path  (middleware.manual)', SoPTestLogLevel.WARN)
            self._middleware_device_pool = [device for device in global_device_pool if device.name == 'localhost']
            self._thing_device_pool = [device for device in global_device_pool if device.name == 'localhost']
        else:
            if manual_middleware_tree:
                SOPTEST_LOG_DEBUG('middleware.manual config is defined. middleware.random & middleware.device config will be ignored.', SoPTestLogLevel.WARN)
                self._middleware_device_pool = global_device_pool
                self._config.middleware_config.random = None
                middleware_num = len(manual_middleware_tree.descendants) + 1
            elif random_middleware_config:
                if self._config.middleware_config.device_pool:
                    self._middleware_device_pool = [self._find_device(device, global_device_pool) for device in self._config.middleware_config.device_pool]
                else:
                    self._middleware_device_pool = [device for device in global_device_pool if device.name != 'localhost']
                middleware_num = calculate_tree_node_num(random_middleware_config.height[1], random_middleware_config.width[1])
            else:
                raise SimulationFailError('If manual_middleware_tree is not defined, random config must be defined.')

            # In the case of things, it defaults to running on a simulator device with relatively
            # high performance rather than running on an embedded device with low performance.
            if self._config.thing_config.device_pool:
                self._thing_device_pool = [self._find_device(device, global_device_pool) for device in self._config.thing_config.device_pool]
            else:
                self._thing_device_pool = [device for device in global_device_pool if device.name == 'localhost']

            if len(self._middleware_device_pool) < middleware_num:
                raise SimulationFailError(f'Device pool is not enough for {os.path.basename(os.path.dirname(self._config.config_path))} simulation. '
                                          f'(Requires at least {middleware_num} devices)')

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

    def generate_name_pool(self, num_tag_name_generate: int, num_service_name_generate: int, num_super_service_name_generate: int,
                           ban_name_list: List[str] = []) -> Tuple[List[str], List[str], List[str]]:
        ban_name_list = ban_name_list + self._PREDEFINED_KEYWORD_LIST

        tag_name_pool = self._generate_random_words(num_word=num_tag_name_generate, ban_word_list=ban_name_list)
        service_name_pool = self._generate_random_words(num_word=num_service_name_generate, ban_word_list=ban_name_list)
        super_service_name_pool = self._generate_random_words(num_word=num_super_service_name_generate, ban_word_list=ban_name_list)
        return tag_name_pool, service_name_pool, super_service_name_pool

    def generate_service_pool(self, tag_name_pool: List[str], service_name_pool: List[str], num_service_generate: int) -> List[SoPService]:
        service_name_pool_copy = copy.deepcopy(service_name_pool)
        service_pool: List[SoPService] = []
        for _ in range(num_service_generate):
            tag_per_service_range = self._config.service_config.tag_per_service
            energy_range = self._config.service_config.normal.energy
            execute_time_range = self._config.service_config.normal.execute_time
            return_value_range = (0, 1000)

            selected_service_name = random.choice(service_name_pool_copy)
            service_name_pool_copy.remove(selected_service_name)
            service_name = f'function_{selected_service_name}'
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

        SOPTEST_LOG_DEBUG(f'Generate service pool size of {len(service_pool)}', SoPTestLogLevel.INFO)
        return service_pool

    def generate_thing_pool(self, service_pool: List[SoPService], num_thing_generate: int) -> List[SoPThing]:
        thing_pool = []
        for _ in range(num_thing_generate):
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

            thing = SoPThing(name=thing_name,
                             level=level,
                             service_list=selected_service_list_copy,
                             is_super=is_super,
                             is_parallel=self._service_parallel,
                             alive_cycle=60 * 5,
                             device=device,
                             thing_file_path=f'{self._simulation_folder_path}/thing/base_thing/{thing_name}.py',
                             remote_thing_file_path=f'{self._config.thing_config.remote_thing_folder_path}/base_thing/{thing_name}.py',
                             fail_rate=fail_rate)
            for service in thing.service_list:
                service.thing = thing

            thing_pool.append(thing)

        SOPTEST_LOG_DEBUG(f'Generate thing pool size of {num_thing_generate}', SoPTestLogLevel.INFO)
        return thing_pool

    def generate_middleware_tree(self) -> SoPMiddleware:
        manual_middleware_tree = self._config.middleware_config.manual_middleware_tree
        random_middleware_config = self._config.middleware_config.random
        device_pool = copy.deepcopy(self._middleware_device_pool)

        if manual_middleware_tree:
            def generate_middleware_tree_manual(middleware: SoPMiddleware, middleware_config: AnyNode, index: int) -> SoPMiddleware:
                height = middleware_config.height + 1
                if middleware_config.is_root:
                    middleware_name = f'middleware_level{height}_0'
                else:
                    middleware_name = f'{middleware.name}__middleware_level{height}_{index}'
                if not middleware_config.device:
                    device = random.choice(device_pool)
                else:
                    selected_device = random.choice(middleware_config.device)
                    for d in device_pool:
                        if d.name == selected_device:
                            device = d
                            break

                # Do not remove localhost device
                if device.name != 'localhost':
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

                for index, child_middleware_config in enumerate(middleware_config.children):
                    child_middleware = generate_middleware_tree_manual(middleware=middleware, middleware_config=child_middleware_config, index=index)
                    child_middleware.parent = middleware

                return middleware

            root_middleware = generate_middleware_tree_manual(middleware=None, middleware_config=manual_middleware_tree, index=0)
        elif random_middleware_config:
            def generate_middleware_tree_random(middleware: SoPMiddleware, height: int, width_range: ConfigRandomIntRange, index: int) -> SoPMiddleware:
                if middleware == None:
                    middleware_name = f'middleware_level{height}_0'
                else:
                    middleware_name = f'{middleware.name}__middleware_level{height}_{index}'

                device = random.choice(device_pool)

                # Do not remove localhost device
                if device.name != 'localhost':
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
                    child_middleware = generate_middleware_tree_random(middleware, height - 1, width_range=width_range, index=index)
                    child_middleware.parent = middleware
                return middleware

            height_range = random_middleware_config.height
            width_range = random_middleware_config.width
            height = random.randint(*height_range)
            root_middleware = generate_middleware_tree_random(middleware=None, height=height, width_range=width_range, index=0)
        else:
            raise Exception('Unknown simulation generator error')

        print_middleware_tree(root_middleware)
        return root_middleware

    def map_thing_to_middleware(self, root_middleware: SoPMiddleware, thing_pool: List[SoPThing]) -> None:
        manual_middleware_tree = self._config.middleware_config.manual_middleware_tree
        random_config = self._config.middleware_config.random

        if manual_middleware_tree:
            def map_thing_to_middleware_manual(middleware: SoPMiddleware, middleware_config: AnyNode) -> None:
                thing_per_middleware_range = middleware_config.thing_num
                thing_per_middleware = random.randint(*thing_per_middleware_range)
                selected_thing_list = random.sample(thing_pool, thing_per_middleware)
                middleware.thing_list = selected_thing_list

                for index, thing in enumerate(middleware.thing_list):
                    middleware.thing_list[index].middleware = middleware
                    middleware.thing_list[index].level = middleware.level + 1
                    middleware.thing_list[index].name = f'normal_thing_{index}__{middleware.name}'
                    middleware.thing_list[index].remote_thing_file_path = f'{self._config.thing_config.remote_thing_folder_path}/base_thing/{middleware.thing_list[index].name}.py'
                    middleware.thing_list[index].thing_file_path = f'{self._simulation_folder_path}/thing/base_thing/{middleware.thing_list[index].name}.py'

                if not middleware.children:
                    return
                for child_middleware, child_middleware_config in zip(middleware.children, middleware_config.children):
                    map_thing_to_middleware_manual(middleware=child_middleware, middleware_config=child_middleware_config)

            map_thing_to_middleware_manual(middleware=root_middleware, middleware_config=manual_middleware_tree)
        elif random_config:
            thing_per_middleware_range = random_config.normal.thing_per_middleware

            def map_thing_to_middleware_random(middleware: SoPMiddleware) -> None:
                thing_per_middleware = random.randint(*thing_per_middleware_range)
                selected_thing_list = random.sample(thing_pool, thing_per_middleware)
                middleware.thing_list = selected_thing_list

                for index, thing in enumerate(middleware.thing_list):
                    middleware.thing_list[index].middleware = middleware
                    middleware.thing_list[index].level = middleware.level + 1
                    middleware.thing_list[index].name = f'normal_thing_{index}__{middleware.name}'
                    middleware.thing_list[index].remote_thing_file_path = f'{self._config.thing_config.remote_thing_folder_path}/base_thing/{middleware.thing_list[index].name}.py'
                    middleware.thing_list[index].thing_file_path = f'{self._simulation_folder_path}/thing/base_thing/{middleware.thing_list[index].name}.py'

                if not middleware.children:
                    return
                for child_middleware in middleware.children:
                    map_thing_to_middleware_random(child_middleware)

            map_thing_to_middleware_random(middleware=root_middleware)
        else:
            raise Exception('Unknown simulation generator error')

        SOPTEST_LOG_DEBUG(f'Map thing to middleware tree', SoPTestLogLevel.INFO)
        # print_middleware_tree(root_middleware=root_middleware, show=lambda middleware: '\n'.join([f'{thing.name} level: {thing.level} service_num: {len(thing.service_list)}' for thing in node.thing_list]))

    def generate_scenario(self, root_middleware: SoPMiddleware):
        manual_middleware_tree = self._config.middleware_config.manual_middleware_tree
        random_config = self._config.middleware_config.random
        service_per_scenario_range = self._config.application_config.normal.service_per_application

        if manual_middleware_tree:
            def generate_scenario_manual(middleware: SoPMiddleware, middleware_config: AnyNode) -> None:
                scenario_per_middleware_range = middleware_config.scenario_num
                scenario_per_middleware = random.randint(*scenario_per_middleware_range)
                available_service_list = flatten_list([thing.service_list for thing in middleware.thing_list])

                for index in range(scenario_per_middleware):
                    scenario_name = f'normal_scenario_{index}__{middleware.name}'
                    level = middleware.level
                    period_range = self._config.application_config.normal.period
                    period = random.uniform(*period_range)
                    priority = -1
                    service_per_scenario = random.randint(*service_per_scenario_range)
                    selected_service_list: List[SoPService] = random.sample(available_service_list, service_per_scenario)

                    scenario = SoPScenario(name=scenario_name,
                                           level=level,
                                           service_list=selected_service_list,
                                           period=period,
                                           priority=priority,
                                           scenario_file_path=f'{self._simulation_folder_path}/application/base_application/{scenario_name}.txt',
                                           middleware=middleware)
                    middleware.scenario_list.append(scenario)

                if not middleware.children:
                    return
                for child_middleware, child_middleware_config in zip(middleware.children, middleware_config.children):
                    generate_scenario_manual(middleware=child_middleware, middleware_config=child_middleware_config)

            generate_scenario_manual(middleware=root_middleware, middleware_config=manual_middleware_tree)
        elif random_config:
            scenario_per_middleware_range = random_config.normal.scenario_per_middleware
            service_per_scenario_range = self._config.application_config.normal.service_per_application

            def generate_scenario_random(middleware: SoPMiddleware) -> None:
                scenario_per_middleware = random.randint(*scenario_per_middleware_range)
                available_service_list = flatten_list([thing.service_list for thing in middleware.thing_list])

                for index in range(scenario_per_middleware):
                    scenario_name = f'normal_scenario_{index}__{middleware.name}'
                    level = middleware.level
                    period_range = self._config.application_config.normal.period
                    period = random.uniform(*period_range)
                    priority = -1
                    service_per_scenario = random.randint(*service_per_scenario_range)

                    if len(available_service_list) < service_per_scenario:
                        raise SimulationFailError('Not enough service for scenario')
                    selected_service_list: List[SoPService] = random.sample(available_service_list, service_per_scenario)

                    scenario = SoPScenario(name=scenario_name,
                                           level=level,
                                           service_list=selected_service_list,
                                           period=period,
                                           priority=priority,
                                           scenario_file_path=f'{self._simulation_folder_path}/application/base_application/{scenario_name}.txt',
                                           middleware=middleware)
                    middleware.scenario_list.append(scenario)

                # for index, thing in enumerate(middleware.thing_list):
                #     thing.middleware = middleware
                #     thing.level = middleware.level + 1
                #     thing.name = f'normal_thing_{index}__{middleware.name}'

                if not middleware.children:
                    return
                for child_middleware in middleware.children:
                    generate_scenario_random(child_middleware)

            generate_scenario_random(middleware=root_middleware)
        else:
            raise Exception('Unknown simulation generator error')

        SOPTEST_LOG_DEBUG(f'Generate application to middleware tree', SoPTestLogLevel.INFO)

    def generate_super(self, root_middleware: SoPMiddleware, tag_name_pool: List[str], super_service_name_pool: List[str]) -> List[SoPThing]:
        super_service_name_pool_copy = copy.deepcopy(super_service_name_pool)
        manual_middleware_tree = self._config.middleware_config.manual_middleware_tree
        random_config = self._config.middleware_config.random
        generated_super_service_num = 0

        sub_service_per_super_service_range = self._config.service_config.super.service_per_super_service
        super_service_per_thing_range = self._config.thing_config.super.service_per_thing
        super_service_per_scenario_range = self._config.application_config.super.service_per_application

        def generate_super_service_common(middleware: SoPMiddleware) -> List[SoPService]:
            super_service_per_thing = random.randint(*super_service_per_thing_range)
            super_service_list: List[SoPService] = []
            for _ in range(super_service_per_thing):
                sub_service_list = self._get_accessible_sub_service_list(middleware=middleware, sub_service_per_super_service_range=sub_service_per_super_service_range)

                # Define other super service's properties
                tag_per_service_range = self._config.service_config.tag_per_service
                # energy_range = None
                # execute_time_range = None
                # return_value_range = None

                selected_super_service_name = random.choice(super_service_name_pool_copy)
                super_service_name_pool_copy.remove(selected_super_service_name)
                super_service_name = f'super_function_{selected_super_service_name}'
                level = middleware.level
                tag_per_service = random.randint(*tag_per_service_range)
                tag_list = random.sample(tag_name_pool, tag_per_service)
                # For super service, energy, execute time, return value is calculated by sub services
                energy = 0
                execute_time = 0
                return_value = 0

                super_service = SoPService(name=super_service_name,
                                           level=level,
                                           tag_list=tag_list,
                                           is_super=True,
                                           energy=energy,
                                           execute_time=execute_time,
                                           return_value=return_value,
                                           sub_service_list=sub_service_list)
                super_service_list.append(super_service)

            return super_service_list

        def generate_super_thing_common(middleware: SoPMiddleware, super_thing_per_middleware: int) -> List[SoPThing]:
            nonlocal generated_super_service_num
            super_thing_list: List[SoPThing] = []
            for index in range(super_thing_per_middleware):
                device = middleware.device
                super_thing_name = f'super_thing_{index}__{middleware.name}'
                level = middleware.level
                is_super = True
                fail_rate = self._config.thing_config.super.fail_error_rate

                super_service_list = generate_super_service_common(middleware=middleware)
                generated_super_service_num += len(super_service_list)
                if generated_super_service_num > self._config.service_config.super.service_type_num:
                    SOPTEST_LOG_DEBUG(f'generated_super_service_num is exceed super.service_type_num: {self._config.service_config.super.service_type_num}.', SoPTestLogLevel.WARN)
                # broken_rate = self._config.thing_config.normal.broken_rate
                # unregister_rate = self._config.thing_config.normal.unregister_rate

                super_thing = SoPThing(name=super_thing_name,
                                       level=level,
                                       service_list=super_service_list,
                                       is_super=is_super,
                                       is_parallel=self._service_parallel,
                                       alive_cycle=60 * 5,
                                       device=device,
                                       thing_file_path=f'{self._simulation_folder_path}/thing/super_thing/{super_thing_name}.py',
                                       remote_thing_file_path=f'{self._config.thing_config.remote_thing_folder_path}/super_thing/{super_thing_name}.py',
                                       fail_rate=fail_rate)
                for super_service in super_thing.service_list:
                    super_service.thing = super_thing

                super_thing_list.append(super_thing)

            return super_thing_list

        def generate_super_scenario_common(middleware: SoPMiddleware, super_scenario_per_middleware: int) -> List[SoPScenario]:
            parent_middleware_list: List[SoPMiddleware] = middleware.path
            super_thing_list = [thing for thing in flatten_list([middleware.thing_list for middleware in parent_middleware_list]) if thing.is_super]
            available_super_service_list = flatten_list([thing.service_list for thing in super_thing_list])

            super_scenario_list: List[SoPScenario] = []
            for index in range(super_scenario_per_middleware):
                super_scenario_name = f'super_scenario_{index}__{middleware.name}'
                level = middleware.level
                period_range = self._config.application_config.super.period
                period = random.uniform(*period_range)
                priority = -1
                super_service_per_scenario = random.randint(*super_service_per_scenario_range)

                if len(available_super_service_list) < super_service_per_scenario:
                    raise SimulationFailError('Not enough super service for super scenario')
                selected_super_service_list: List[SoPService] = random.sample(available_super_service_list, super_service_per_scenario)

                super_scenario = SoPScenario(name=super_scenario_name,
                                             level=level,
                                             service_list=selected_super_service_list,
                                             period=period,
                                             priority=priority,
                                             scenario_file_path=f'{self._simulation_folder_path}/application/super_application/{super_scenario_name}.txt',
                                             middleware=middleware)
                super_scenario_list.append(super_scenario)

            return super_scenario_list

        if manual_middleware_tree:
            def generate_super_thing_manual(middleware: SoPMiddleware, middleware_config: AnyNode) -> None:
                super_thing_per_middleware_range = middleware_config.super_thing_num
                super_thing_per_middleware = random.randint(*super_thing_per_middleware_range)
                super_thing_list: List[SoPThing] = generate_super_thing_common(middleware=middleware, super_thing_per_middleware=super_thing_per_middleware)
                for super_thing in super_thing_list:
                    super_thing.middleware = middleware
                middleware.thing_list.extend(super_thing_list)

            def generate_super_scenario_manual(middleware: SoPMiddleware, middleware_config: AnyNode) -> List[SoPThing]:
                super_scenario_per_middleware_range = middleware_config.super_scenario_num
                super_scenario_per_middleware = random.randint(*super_scenario_per_middleware_range)
                super_scenario_list: List[SoPScenario] = generate_super_scenario_common(middleware=middleware, super_scenario_per_middleware=super_scenario_per_middleware)
                middleware.scenario_list.extend(super_scenario_list)

            def generate_super_manual(middleware: SoPMiddleware, middleware_config: AnyNode) -> None:
                generate_super_thing_manual(middleware=middleware, middleware_config=middleware_config)
                generate_super_scenario_manual(middleware=middleware, middleware_config=middleware_config)

                for child_middleware, child_middleware_config in zip(middleware.children, middleware_config.children):
                    generate_super_manual(middleware=child_middleware, middleware_config=child_middleware_config)

            generate_super_manual(middleware=root_middleware, middleware_config=manual_middleware_tree)
        elif random_config:
            super_thing_per_middleware_range = random_config.super.thing_per_middleware
            super_scenario_per_middleware_range = random_config.super.scenario_per_middleware

            def generate_super_thing_random(middleware: SoPMiddleware) -> List[SoPThing]:
                super_thing_per_middleware = random.randint(*super_thing_per_middleware_range)
                super_thing_list: List[SoPThing] = generate_super_thing_common(middleware=middleware, super_thing_per_middleware=super_thing_per_middleware)
                for super_thing in super_thing_list:
                    super_thing.middleware = middleware
                middleware.thing_list.extend(super_thing_list)

            def generate_super_scenario_random(middleware: SoPMiddleware) -> List[SoPThing]:
                super_scenario_per_middleware = random.randint(*super_scenario_per_middleware_range)
                super_scenario_list = generate_super_scenario_common(middleware=middleware, super_scenario_per_middleware=super_scenario_per_middleware)
                middleware.scenario_list.extend(super_scenario_list)

            def generate_super_random(middleware: SoPMiddleware):
                generate_super_thing_random(middleware=middleware)
                generate_super_scenario_random(middleware=middleware)

                for child_middleware in middleware.children:
                    generate_super_random(middleware=child_middleware)

            generate_super_random(middleware=root_middleware)
        else:
            raise Exception('Unknown simulation generator error')

    def validate_simulation_env(self, middleware: SoPMiddleware):
        thing_list = middleware.thing_list
        scenario_list = middleware.scenario_list

    def _generate_event_timeline(self, root_middleware: SoPMiddleware) -> Tuple[List[SoPEvent], List[SoPEvent]]:

        def generate_dynamic_thing_event_timeline(local_thing_list: List[SoPThing], super_thing_list: List[SoPThing],
                                                  normal_thing_select_rate: float, super_thing_select_rate: float,
                                                  start_time_weight: float, end_time_weight: float, event_type: SoPEventType,
                                                  delay: float) -> List[SoPEvent]:
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
            local_thing_unregister_timeline = [self._generate_event(component=thing, event_type=event_type_1, timestamp=self._config.running_time * start_time_weight)
                                               for thing in selected_local_thing_list]
            super_thing_unregister_timeline = [self._generate_event(component=thing, event_type=event_type_1, timestamp=self._config.running_time * start_time_weight)
                                               for thing in selected_super_thing_list]
            local_thing_register_timeline = [self._generate_event(component=thing, event_type=event_type_2, timestamp=self._config.running_time * end_time_weight)
                                             for thing in selected_local_thing_list]
            super_thing_register_timeline = [self._generate_event(component=thing, event_type=event_type_2, timestamp=self._config.running_time * end_time_weight)
                                             for thing in selected_super_thing_list]

            tmp_timeline = local_thing_unregister_timeline + super_thing_unregister_timeline + local_thing_register_timeline + super_thing_register_timeline
            if delay:
                tmp_timeline += [SoPEvent(delay=delay, event_type=SoPEventType.DELAY)]
            return tmp_timeline

        static_event_timeline: List[SoPEvent] = []
        dynamic_event_timeline: List[SoPEvent] = []
        middleware_list = get_whole_middleware_list(root_middleware)
        thing_list = get_whole_thing_list(root_middleware)
        scenario_list = get_whole_scenario_list(root_middleware)

        normal_thing_list = [thing for thing in thing_list if thing.is_super == False]
        super_thing_list = [thing for thing in thing_list if thing.is_super == True]

        # Build IoT system
        build_simulation_env_timeline = []
        build_simulation_env_timeline.extend([self._generate_event(component=middleware, event_type=SoPEventType.MIDDLEWARE_RUN)
                                              for middleware in middleware_list])
        build_simulation_env_timeline.extend([self._generate_event(component=thing, event_type=SoPEventType.THING_RUN)
                                              for thing in sorted(thing_list, key=lambda x: x.is_super, reverse=False)])
        static_event_timeline.extend(build_simulation_env_timeline)

        # Wait until all thing register
        static_event_timeline.append(SoPEvent(event_type=SoPEventType.THING_REGISTER_WAIT))
        static_event_timeline.append(SoPEvent(delay=5, event_type=SoPEventType.DELAY))

        # Scenario add start
        scenario_add_timeline = [self._generate_event(component=scenario, event_type=SoPEventType.SCENARIO_ADD, middleware_component=find_component(root_middleware, scenario)[1])
                                 for scenario in scenario_list]
        static_event_timeline.extend(sorted(scenario_add_timeline, key=lambda x: x.timestamp))
        static_event_timeline.append(SoPEvent(event_type=SoPEventType.SCENARIO_ADD_CHECK))
        static_event_timeline.append(SoPEvent(delay=5, event_type=SoPEventType.DELAY))
        static_event_timeline.append(SoPEvent(event_type=SoPEventType.REFRESH))

        # Simulation start
        dynamic_event_timeline.append(SoPEvent(event_type=SoPEventType.START))

        # Scenario run start
        scenario_run_timeline = [self._generate_event(component=scenario, event_type=SoPEventType.SCENARIO_RUN)
                                 for scenario in scenario_list]
        dynamic_event_timeline.extend(sorted(scenario_run_timeline, key=lambda x: x.timestamp))

        # Thing unregister event
        # if unregister_rate is 0, then no event will be generated
        thing_unregister_timeline = generate_dynamic_thing_event_timeline(local_thing_list=normal_thing_list, super_thing_list=super_thing_list,
                                                                          normal_thing_select_rate=self._config.thing_config.normal.unregister_rate,
                                                                          super_thing_select_rate=self._config.thing_config.super.unregister_rate,
                                                                          start_time_weight=0.2, end_time_weight=0.7, event_type=SoPEventType.THING_UNREGISTER,
                                                                          delay=0)
        dynamic_event_timeline.extend(thing_unregister_timeline)

        # Thing kill event
        # if kill_rate is 0, then no event will be generated
        thing_kill_timeline = generate_dynamic_thing_event_timeline(local_thing_list=normal_thing_list, super_thing_list=super_thing_list,
                                                                    normal_thing_select_rate=self._config.thing_config.normal.broken_rate,
                                                                    super_thing_select_rate=self._config.thing_config.super.broken_rate,
                                                                    start_time_weight=0.5, end_time_weight=10, event_type=SoPEventType.THING_KILL,
                                                                    delay=0)
        dynamic_event_timeline.extend(thing_kill_timeline)

        # Simulation end event
        dynamic_event_timeline.append(SoPEvent(event_type=SoPEventType.END, timestamp=self._config.running_time))

        # Sort event timeline
        static_event_timeline = sorted(static_event_timeline, key=lambda x: x.timestamp)
        dynamic_event_timeline = sorted(dynamic_event_timeline, key=lambda x: x.timestamp)

        return static_event_timeline, dynamic_event_timeline

    # =========================
    #         _    _  _
    #        | |  (_)| |
    #  _   _ | |_  _ | | ___
    # | | | || __|| || |/ __|
    # | |_| || |_ | || |\__ \
    #  \__,_| \__||_||_||___/
    # =========================

    def _find_device(self, device_name: str, device_pool: List[SoPDevice]) -> SoPDevice:
        for device in device_pool:
            if device.name == device_name:
                return device
        raise ValueError(f'Cannot find device {device_name} in device pool')

    def _check_device_pool(self, device_pool_path: str) -> None:
        device_pool_path = self._config.device_pool_path.abs_path()
        device_pool_dict = load_yaml(device_pool_path)
        if not 'localhost' in device_pool_dict:
            SOPTEST_LOG_DEBUG(f'Localhost device config is not exist in device pool...', SoPTestLogLevel.WARN)
            device_pool_dict = self._add_localhost_info(device_pool_dict)
            save_yaml(device_pool_path, device_pool_dict)

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

    def _get_accessible_sub_service_list(self, middleware: SoPMiddleware, sub_service_per_super_service_range: ConfigRandomIntRange) -> List[SoPService]:
        descendants_middleware_list: List[SoPMiddleware] = [middleware] + list(middleware.descendants)
        thing_list: List[SoPThing] = flatten_list([middleware.thing_list for middleware in descendants_middleware_list])
        candidate_sub_service_list = flatten_list([thing.service_list for thing in thing_list])

        sub_service_per_super_service = random.randint(*sub_service_per_super_service_range)
        if len(candidate_sub_service_list) < sub_service_per_super_service:
            raise SOPTEST_LOG_DEBUG(f'Not enough candidate sub service for super service', SoPTestLogLevel.FAIL)
        sub_service_list = random.sample(candidate_sub_service_list, sub_service_per_super_service)
        return sub_service_list

    def _generate_event(self, component: SoPComponent, event_type: SoPEventType, timestamp: float = 0.0, **kwargs) -> SoPEvent:
        event_kwargs = dict(component=component, event_type=event_type, timestamp=timestamp)
        event_kwargs.update(kwargs)
        event = SoPEvent(**event_kwargs)
        return event

    def generate_data(self, simulation_env: SoPMiddleware):
        middleware_list: List[SoPMiddleware] = get_whole_middleware_list(simulation_env)
        thing_list: List[SoPThing] = get_whole_thing_list(simulation_env)
        scenario_list: List[SoPScenario] = get_whole_scenario_list(simulation_env)

        longest_scenario = max(scenario_list, key=lambda x: x.period)
        if longest_scenario.period * 1.2 > self._config.running_time:
            running_time = longest_scenario.period * 1.2
            SOPTEST_LOG_DEBUG(
                f'Longest scenario period is {longest_scenario.period} but simulation time is {self._config.running_time}. Set simulation time to {running_time}', SoPTestLogLevel.WARN)
        else:
            running_time = self._config.running_time

        config = dict(name=self._config.name,
                      running_time=running_time,
                      event_timeout=self._config.event_timeout)
        component = simulation_env.dict()
        event_timeline = self._generate_event_timeline(middleware_list=middleware_list,
                                                       thing_list=thing_list,
                                                       scenario_list=scenario_list,
                                                       running_time=running_time,
                                                       event_timeout=self._config.event_timeout)
        simulation_dump = dict(config=config,
                               component=component,
                               event_timeline=event_timeline)
        return simulation_dump

    def _export_simulation_data_file(self, simulation_env_list: List[SoPSimulationEnv], simulation_data_file_path: str) -> None:
        os.makedirs(os.path.dirname(simulation_data_file_path), exist_ok=True)
        simulation_env_dict_list = {'simulation_list': []}
        for simulation_env in simulation_env_list:
            simulation_env_dict = simulation_env.dict()
            simulation_env_dict_list['simulation_list'].append(simulation_env_dict)
        save_json(simulation_data_file_path, simulation_env_dict_list)
