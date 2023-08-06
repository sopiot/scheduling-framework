from simulation_framework.core.env_generator import *
from simulation_framework.core.evaluator import *
from simulation_framework.profiler import *


class MXSimulationFramework:

    def __init__(self, service_parallel: bool, result_filename: str, download_logs: bool,
                 profile: bool, profile_type: ProfileType, ram_disk: bool,
                 mqtt_debug: bool, middleware_debug: bool) -> None:
        self._simulator: MXSimulator = None
        self._service_parallel = service_parallel
        self._result_filename = result_filename
        self._download_logs = download_logs
        self._profile = profile
        self._profile_type = profile_type
        self._ram_disk = ram_disk
        self._mqtt_debug = mqtt_debug
        self._middleware_debug = middleware_debug
        self._config_list: List[MXSimulationConfig] = []
        self._policy_file_list: List[str] = []
        self._simulation_env_list: List[MXSimulationEnv] = []

    def load(self, config_path_list: List[str] = '', simulation_data_path: str = '', policy_path_list: List[str] = '') -> None:
        if config_path_list:
            self._config_list = self.load_config(config_path_list=config_path_list)
        elif simulation_data_path:
            self._simulation_env_list = self.load_simulation_data(simulation_data_path=simulation_data_path)
        else:
            raise ConfigPathError('Only one of config_path and simulation_data_path must be given.', path='not given')

        self._policy_file_list = self.load_policy(policy_path_list=policy_path_list)

    def load_config(self, config_path_list: List[str]) -> List[MXSimulationConfig]:
        config_list: List[MXSimulationConfig] = []
        for config_path in config_path_list:
            if os.path.isdir(config_path):
                config_file_path_list = os.listdir(config_path)
                for config_file_path in config_file_path_list:
                    if not (config_file_path.startswith('config') and config_file_path.endswith('.yml')):
                        continue
                    config = MXSimulationConfig(config_path=os.path.join(config_path, config_file_path))
                    config_list.append(config)
            else:
                if (os.path.basename(config_path).startswith('config') and os.path.basename(config_path).endswith('.yml')):
                    config_list.append(MXSimulationConfig(config_path=config_path))

        if not self._result_filename:
            self._result_filename = f'{config_list[0].name}_result'

        return config_list

    def load_service_thing_pool(self, service_thing_pool_path: str) -> Tuple[List[str], List[str], List[str], List[MXService], List[MXThing]]:
        if not os.path.exists(service_thing_pool_path):
            return [], [], [], [], []

        service_thing_pool = load_json(service_thing_pool_path)
        tag_name_pool = service_thing_pool['tag_name_pool']
        service_name_pool = service_thing_pool['service_name_pool']
        super_service_name_pool = service_thing_pool['super_service_name_pool']
        service_pool: List[MXService] = [MXService.load(service_info) for service_info in service_thing_pool['service_pool']]
        thing_pool: List[MXThing] = [MXThing.load(thing_info) for thing_info in service_thing_pool['thing_pool']]
        for thing in thing_pool:
            for service in thing.service_list:
                service.thing = thing

        MXTEST_LOG_DEBUG(f'Load service_thing_pool from ./{os.path.relpath(service_thing_pool_path, get_project_root())}', MXTestLogLevel.INFO)
        return tag_name_pool, service_name_pool, super_service_name_pool, service_pool, thing_pool

    def load_event_timing_list(self, simulation_env: MXSimulationEnv, event_timing_list: List[dict]) -> List[MXEvent]:
        event_list: List[MXEvent] = []
        for event in event_timing_list:
            event_type = MXEventType.get(event['event_type'])
            component = find_component_by_name(simulation_env.root_middleware, event['component'])
            middleware_component = find_component_by_name(simulation_env.root_middleware, event['middleware_component'])
            if component and component.component_type in [MXComponentType.MIDDLEWARE, MXComponentType.THING, MXComponentType.SCENARIO]:
                component.middleware = middleware_component

            event_obj = MXEvent(event_type=event_type,
                                component=find_component_by_name(simulation_env.root_middleware, event['component']),
                                timestamp=event['timestamp'],
                                duration=event['duration'],
                                delay=event['delay'],
                                middleware_component=find_component_by_name(simulation_env.root_middleware, event['middleware_component']),
                                args=event['args'],
                                kwargs=event['kwargs'])
            event_list.append(event_obj)

        return event_list

    def load_simulation_data(self, simulation_data_path: str) -> Tuple[MXSimulationConfig, List[MXSimulationEnv]]:
        simulation_data_file = load_json(simulation_data_path)
        simulation_env_list: List[MXSimulationEnv] = []
        for simulation_env_info in simulation_data_file['simulation_list']:
            config = MXSimulationConfig(config_path=simulation_env_info['config_path'])
            service_pool = simulation_env_info['service_pool']
            thing_pool = simulation_env_info['thing_pool']
            simulation_env = MXSimulationEnv(config=config,
                                             service_pool=service_pool,
                                             thing_pool=thing_pool,
                                             simulation_data_file_path=simulation_data_path)
            simulation_env.load_middleware_tree(simulation_env_info['root_middleware'])
            simulation_env.static_event_timing_list = self.load_event_timing_list(simulation_env, simulation_env_info['static_event_timing_list'])
            simulation_env.dynamic_event_timing_list = self.load_event_timing_list(simulation_env, simulation_env_info['dynamic_event_timing_list'])
            simulation_env_list.append(simulation_env)

        return simulation_env_list

    def load_policy(self, policy_path_list: List[str]) -> List[str]:
        policy_list: List[str] = []
        for policy_path in policy_path_list:
            if os.path.isdir(policy_path):
                policy_file_path_list = os.listdir(policy_path)
                for policy_file_path in policy_file_path_list:
                    if not (policy_file_path.startswith('policy') and policy_file_path.endswith('.cc')):
                        continue
                    policy_file_path = os.path.join(policy_path, policy_file_path)
                    policy_list.append(policy_file_path)
            else:
                policy_base_path = os.path.basename(policy_path)
                if policy_base_path.startswith('policy') and policy_base_path.endswith('.cc'):
                    policy_list.append(policy_path)

        return policy_list

    def start(self) -> None:
        # Generate simulation if any root_middleware in self._simulation_env_list is None.
        if self._config_list:
            self._simulation_env_list = self.generate_simulation_env(self._config_list)

        # Run simulation with simulation_env_list and policy_path_list.
        # Simulation will run with count of len(simulation_env_list) * len(policy_path_list).
        simulation_result_list: List[MXSimulationResult] = []
        for index, simulation_env in enumerate(self._simulation_env_list):
            for policy_file in self._policy_file_list:
                simulation_result = self.run_simulation(simulation_env=simulation_env, policy_path=policy_file, index=index)
                simulation_result_list.append(simulation_result)

        self.print_ranking(simulation_result_list=simulation_result_list)

    def print_ranking(self, simulation_result_list: List[MXSimulationResult]) -> bool:
        if not simulation_result_list:
            MXTEST_LOG_DEBUG(f'No simulation result', MXTestLogLevel.WARN)
            return False

        simulation_result_list_sort_by_policy: Dict[str, List[MXSimulationResult]] = {}
        for simulation_result in simulation_result_list:
            if simulation_result.policy_path in simulation_result_list_sort_by_policy:
                simulation_result_list_sort_by_policy[simulation_result.policy_path].append(simulation_result)
            else:
                simulation_result_list_sort_by_policy[simulation_result.policy_path] = [simulation_result]
        simulation_result_list: List[MXSimulationResult] = []
        for policy, result_list in simulation_result_list_sort_by_policy.items():
            simulation_result_avg = MXSimulationResult(policy_path=policy,
                                                       avg_latency=avg([result.get_avg_latency()[0] for result in result_list]),
                                                       avg_energy=avg([result.get_avg_energy()[0] for result in result_list]),
                                                       avg_success_ratio=avg([result.get_avg_success_ratio()[0] for result in result_list]))
            simulation_result_list.append(simulation_result_avg)

        simulation_result_list_sort_by_application_latency = sorted(simulation_result_list, key=lambda x: x.avg_latency)
        simulation_result_list_sort_by_application_energy = sorted(simulation_result_list, key=lambda x: x.avg_energy)
        simulation_result_list_sort_by_success_ratio = sorted(simulation_result_list, key=lambda x: x.avg_success_ratio, reverse=True)

        rank_header = ['Rank', 'QoS', 'Energy Saving', 'Stability']
        print_table([[i+1,
                      f'''latency: {f'{simulation_result_list_sort_by_application_latency[i].avg_latency:.2f}'}
policy: {simulation_result_list_sort_by_application_latency[i].policy_path}''',
                      f'''energy: {f'{simulation_result_list_sort_by_application_energy[i].avg_energy:.2f}'}
policy: {simulation_result_list_sort_by_application_energy[i].policy_path}''',
                      f'''success_ratio: {f'{simulation_result_list_sort_by_success_ratio[i].avg_success_ratio * 100:.2f}'}
policy: {simulation_result_list_sort_by_success_ratio[i].policy_path}'''] for i in range(len(simulation_result_list))], rank_header)

        return True

    def calculate_num_service_thing_generate(self, config: MXSimulationConfig) -> Tuple[int, int]:
        manual_middleware_tree = config.middleware_config.manual_middleware_tree
        random_middleware_config = config.middleware_config.random

        # Set service_num according to current config
        num_service_generate = config.service_config.normal.service_type_num
        num_thing_generate = 0

        # Calculate max_thing_num according to current config
        if manual_middleware_tree:
            middleware_config_list = [manual_middleware_tree] + list(manual_middleware_tree.descendants)
            num_thing_generate = sum([middleware_config.thing_num[1] for middleware_config in middleware_config_list])
        elif random_middleware_config:
            max_middleware_num = calculate_tree_node_num(random_middleware_config.height[1], random_middleware_config.width[1])
            num_thing_generate = max_middleware_num * random_middleware_config.normal.thing_per_middleware[1]
        else:
            raise SimulationFailError('manual_middleware_tree and random_middleware_config are both None')

        # If config.force_generate is True, generate service and thing pool according to current
        # Else, generate services and things as much as the difference between the number of
        # service thing pools to be created in the current setting and the number of service
        # thing pools already created.

        return num_service_generate, num_thing_generate

    def generate_simulation_env(self, config_list: List[MXSimulationConfig]) -> List[MXSimulationEnv]:
        if len(config_list) == 0:
            raise ConfigLoadError('No config file loaded. Check -c or -i option.')

        self.env_generator = MXEnvGenerator(service_parallel=self._service_parallel)

        simulation_env_list: List[MXSimulationEnv] = []
        for config in config_list:
            MXTEST_LOG_DEBUG(f'Generate simulation env with config: {config.name}', MXTestLogLevel.PASS)
            loaded_tag_name_pool, loaded_service_name_pool, loaded_super_service_name_pool, loaded_service_pool, loaded_thing_pool = [], [], [], [], []
            simulation_env = MXSimulationEnv(config=config)
            service_thing_pool_path = config.service_thing_pool_path.abs_path()

            self.env_generator.load(config=simulation_env.config)

            # If service_thing_pool path is given in config, load it
            num_tag_name_generate = config.service_config.tag_per_service[1]
            num_service_name_generate = config.service_config.normal.service_type_num
            num_super_service_name_generate = config.service_config.super.service_type_num
            num_service_generate, num_thing_generate = self.calculate_num_service_thing_generate(config=config)

            # Calculate the number of services and things to be generated
            if not config.force_generate:
                (loaded_tag_name_pool,
                 loaded_service_name_pool,
                 loaded_super_service_name_pool,
                 loaded_service_pool,
                 loaded_thing_pool) = self.load_service_thing_pool(service_thing_pool_path=service_thing_pool_path)

                num_tag_name_generate -= len(loaded_tag_name_pool)
                num_service_name_generate -= len(loaded_service_name_pool)
                num_super_service_name_generate -= len(loaded_super_service_name_pool)
                num_service_generate -= len(loaded_service_pool)
                num_thing_generate -= len(loaded_thing_pool)

                if num_tag_name_generate < 0:
                    num_tag_name_generate = 0
                if num_service_name_generate < 0:
                    num_service_name_generate = 0
                if num_super_service_name_generate < 0:
                    num_super_service_name_generate = 0
                if num_service_generate < 0:
                    num_service_generate = 0
                if num_thing_generate < 0:
                    num_thing_generate = 0

            # Generate services and things
            generated_tag_name_pool, generated_service_name_pool, generated_super_service_name_pool = self.env_generator._generate_name_pool(
                num_tag_name_generate=num_tag_name_generate,
                num_service_name_generate=num_service_name_generate,
                num_super_service_name_generate=num_super_service_name_generate
            )
            tag_name_pool = loaded_tag_name_pool + generated_tag_name_pool
            service_name_pool = loaded_service_name_pool + generated_service_name_pool
            super_service_name_pool = loaded_super_service_name_pool + generated_super_service_name_pool

            generated_service_pool = self.env_generator._generate_service_pool(tag_name_pool=tag_name_pool, service_name_pool=service_name_pool, num_service_generate=num_service_generate)
            service_pool = loaded_service_pool + generated_service_pool
            generated_thing_pool = self.env_generator._generate_thing_pool(service_pool=service_pool, num_thing_generate=num_thing_generate)
            thing_pool = loaded_thing_pool + generated_thing_pool

            # Export service_thing_pool
            self._export_service_thing_pool(service_thing_pool_path=service_thing_pool_path,
                                            tag_name_pool=tag_name_pool, service_name_pool=service_name_pool, super_service_name_pool=super_service_name_pool,
                                            service_pool=service_pool, thing_pool=thing_pool)

            # Generate middleware tree
            root_middleware = self.env_generator._generate_middleware_tree()

            # Map services and things to middleware
            self.env_generator._map_thing_to_middleware(root_middleware=root_middleware, thing_pool=thing_pool)

            # Generate scenario
            self.env_generator._generate_scenario(root_middleware=root_middleware)

            # Generate super service, super thing and super scenario
            self.env_generator._generate_super_component(root_middleware=root_middleware, tag_name_pool=tag_name_pool, super_service_name_pool=super_service_name_pool)

            # Generate event timing_list
            static_event_timing_list, dynamic_event_timing_list = self.env_generator._generate_event_timing_list(root_middleware=root_middleware)

            # Update simulation env
            simulation_env.root_middleware = root_middleware
            simulation_env.service_pool = service_pool
            simulation_env.thing_pool = thing_pool
            simulation_env.static_event_timing_list = static_event_timing_list
            simulation_env.dynamic_event_timing_list = dynamic_event_timing_list
            simulation_env.simulation_data_file_path = f'{self.env_generator._simulation_folder_path}/simulation_data.json'
            simulation_env_list.append(simulation_env)

        self.env_generator._export_simulation_data_file(simulation_env_list=simulation_env_list, simulation_data_file_path=simulation_env_list[0].simulation_data_file_path)
        return simulation_env_list

    def run_simulation(self, simulation_env: MXSimulationEnv, policy_path: str, index: int) -> MXSimulationResult:
        try:
            MXTEST_LOG_DEBUG(f'==== Start simulation {simulation_env.config.name}, iter: {index}, policy: {os.path.basename(policy_path)} ====', MXTestLogLevel.INFO)
            self._simulator = MXSimulator(simulation_env=simulation_env, policy_path=policy_path, mqtt_debug=self._mqtt_debug,
                                          middleware_debug=self._middleware_debug, download_logs=self._download_logs)
            self._simulator.setup()
            self._simulator.start()

            evaluator = MXEvaluator(simulation_env=simulation_env, event_log=self._simulator.get_event_log()).classify_event_log()
            simulation_result = evaluator.evaluate_simulation()

            simulation_result.config_path = simulation_env.config.config_path
            simulation_result.policy_path = policy_path

            profiler = None
            if self._download_logs:
                self._simulator.event_handler.download_log_file()
            if self._profile:
                log_root_path = self._simulator.event_handler.download_log_file()
                profiler = Profiler()
                profiler.load(log_root_path=log_root_path)
                simulation_overhead = profiler.profile(self._profile_type, export=True)
            else:
                simulation_overhead = None

            simulation_name = f'{simulation_env.config.name}_{index}'
            evaluator.export_txt(simulation_result=simulation_result, simulation_overhead=simulation_overhead, simulation_name=simulation_name, file_name=self._result_filename,
                                 config_path=simulation_env.config.config_path)
            evaluator.export_csv(simulation_result=simulation_result, simulation_overhead=simulation_overhead, simulation_name=simulation_name, file_name=self._result_filename,
                                 config_path=simulation_env.config.config_path)

            self._simulator.event_handler.wrapup()
            return simulation_result
        except KeyboardInterrupt:
            MXTEST_LOG_DEBUG('KeyboardInterrupt')
            event_handler: MXEventHandler = self._simulator.event_handler
            event_handler.wrapup()

            try:
                user_input = int(input('Select exit mode[default=1].\n1. Just exit\n2. Download remote logs\n') or 1)
            except KeyboardInterrupt:
                user_input = 1

            if user_input == 1:
                cprint(f'\rExit whole simulation...', 'red')
            elif user_input == 2:
                cprint(f'Download remote logs...', 'yellow')
                event_handler.download_log_file()
            else:
                cprint(f'Unknown input. Exit whole simulation...', 'red')

            exit(0)
        except Exception as e:
            print_error()
            event_handler: MXEventHandler = self._simulator.event_handler
            event_handler.wrapup()

    # =========================
    #         _    _  _
    #        | |  (_)| |
    #  _   _ | |_  _ | | ___
    # | | | || __|| || |/ __|
    # | |_| || |_ | || |\__ \
    #  \__,_| \__||_||_||___/
    # =========================

    def _export_service_thing_pool(self, service_thing_pool_path: str, tag_name_pool: List[str], service_name_pool: List[str], super_service_name_pool: List[str],
                                   service_pool: List[MXService], thing_pool: List[MXThing]) -> None:
        service_pool_dict = [service.dict() for service in service_pool]
        thing_pool_dict = [thing.dict() for thing in thing_pool]
        service_thing_pool = {'tag_name_pool': tag_name_pool,
                              'service_name_pool': service_name_pool,
                              'super_service_name_pool': super_service_name_pool,
                              'service_pool': service_pool_dict,
                              'thing_pool': thing_pool_dict}
        save_json(service_thing_pool_path, service_thing_pool)
