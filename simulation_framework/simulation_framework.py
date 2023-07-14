from simulation_framework.core.simulator import *
from simulation_framework.core.env_generator import *
from simulation_framework.core.evaluator import *
from simulation_framework.profiler import *


class MXSimulationFramework:

    def __init__(self, service_parallel: bool = True, result_filename: str = '', download_logs: bool = False,
                 profile: bool = False, profile_type: ProfileType = ProfileType.EXECUTE,
                 mqtt_debug: bool = False, middleware_debug: bool = False) -> None:
        self._simulator: MXSimulator = None
        self._service_parallel = service_parallel
        self._result_filename = result_filename
        self._download_logs = download_logs
        self._profile = profile
        self._profile_type = profile_type
        self._mqtt_debug = mqtt_debug
        self._middleware_debug = middleware_debug

        self._config_list: List[MXSimulationConfig] = []
        self._policy_path_list: List[str] = []
        self._simulation_env_list: List[MXSimulationEnv] = []

    def load(self, config_path: str = '', simulation_data_path: str = '', policy_path: str = '') -> None:
        if config_path:
            self._config_list = self.load_config(config_path=config_path)
        elif simulation_data_path:
            self._simulation_env_list = self.load_simulation_data(simulation_data_path=simulation_data_path)
        else:
            raise ConfigPathError('Only one of config_path and simulation_data_path must be given.', path='not given')

        self._policy_path_list = self.load_policy(policy_path=policy_path)

    def load_config(self, config_path: str) -> List[MXSimulationConfig]:
        if os.path.isdir(config_path):
            config_list = [MXSimulationConfig(config_path=os.path.join(config_path, config_file_path)) for config_file_path in os.listdir(config_path)
                           if config_file_path.startswith('config') and config_file_path.endswith('.yml')]
        else:
            config_list = ([MXSimulationConfig(config_path=config_path)]
                           if (os.path.basename(config_path).startswith('config') and os.path.basename(config_path).endswith('.yml')) else [])
        return config_list

    def load_service_thing_pool(self, service_thing_pool_path: str) -> Tuple[List[str], List[str], List[str], List[MXService], List[MXThing]]:
        if not os.path.exists(service_thing_pool_path):
            return [], [], [], [], []

        service_thing_pool = load_json(service_thing_pool_path)
        tag_name_pool = service_thing_pool['tag_name_pool']
        service_name_pool = service_thing_pool['service_name_pool']
        super_service_name_pool = service_thing_pool['super_service_name_pool']
        service_pool = [MXService.load(service_info) for service_info in service_thing_pool['service_pool']]
        thing_pool = [MXThing.load(thing_info) for thing_info in service_thing_pool['thing_pool']]
        for thing in thing_pool:
            for service in thing.service_list:
                service.thing = thing

        MXTEST_LOG_DEBUG(f'Load service_thing_pool from ./{os.path.relpath(service_thing_pool_path, get_project_root())}', MXTestLogLevel.INFO)
        return tag_name_pool, service_name_pool, super_service_name_pool, service_pool, thing_pool

    def load_simulation_data(self, simulation_data_path: str) -> Tuple[MXSimulationConfig, List[MXSimulationEnv]]:
        simulation_data_file = load_json(simulation_data_path)
        simulation_env_list: List[MXSimulationEnv] = []
        for simulation_env_info in simulation_data_file['simulation_env_list']:
            config = simulation_env_info['config']
            root_middleware = MXMiddleware.load(simulation_env_info['root_middleware'])
            event_timing_list = simulation_env_info['event_timing_list']
            simulation_env = MXSimulationEnv(config=config, root_middleware=root_middleware, event_timing_list=event_timing_list)
            simulation_env_list.append(simulation_env)

        return simulation_env_list

    def load_policy(self, policy_path: str) -> List[str]:
        if os.path.isdir(policy_path):
            policy_path_list = [os.path.join(policy_path, file) for file in os.listdir(policy_path) if file.startswith('policy') and file.endswith('.cc')]
        else:
            policy_path_list = [policy_path] if (os.path.basename(policy_path).startswith('policy') and os.path.basename(policy_path).endswith('.cc')) else []
        return policy_path_list

    def start(self):
        # Generate simulation if any root_middleware in self._simulation_env_list is None.
        if self._config_list:
            self._simulation_env_list = self.generate_simulation_env(self._config_list)

        # Run simulation with simulation_env_list and policy_path_list.
        # Simulation will run with count of len(simulation_env_list) * len(policy_path_list).
        simulation_result_list: List[MXSimulationResult] = []
        for index, simulation_env in enumerate(self._simulation_env_list):
            for policy_path in self._policy_path_list:
                simulation_result = self.run_simulation(simulation_env=simulation_env, policy_path=policy_path, index=index)
                simulation_result_list.append(simulation_result)

        self.print_ranking(simulation_result_list=simulation_result_list)

    def print_ranking(self, simulation_result_list: List[MXSimulationResult]):
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
        self.env_generator = MXEnvGenerator(service_parallel=self._service_parallel)

        simulation_env_list: List[MXSimulationEnv] = []
        for config in config_list:
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
            generated_tag_name_pool, generated_service_name_pool, generated_super_service_name_pool = self.env_generator.generate_name_pool(
                num_tag_name_generate=num_tag_name_generate,
                num_service_name_generate=num_service_name_generate,
                num_super_service_name_generate=num_super_service_name_generate
            )
            tag_name_pool = loaded_tag_name_pool + generated_tag_name_pool
            service_name_pool = loaded_service_name_pool + generated_service_name_pool
            super_service_name_pool = loaded_super_service_name_pool + generated_super_service_name_pool

            generated_service_pool = self.env_generator.generate_service_pool(tag_name_pool=tag_name_pool, service_name_pool=service_name_pool, num_service_generate=num_service_generate)
            service_pool = loaded_service_pool + generated_service_pool
            generated_thing_pool = self.env_generator.generate_thing_pool(service_pool=service_pool, num_thing_generate=num_thing_generate)
            thing_pool = loaded_thing_pool + generated_thing_pool

            # Export service_thing_pool
            self._export_service_thing_pool(service_thing_pool_path=service_thing_pool_path,
                                            tag_name_pool=tag_name_pool, service_name_pool=service_name_pool, super_service_name_pool=super_service_name_pool,
                                            service_pool=service_pool, thing_pool=thing_pool)

            # Generate middleware tree
            root_middleware = self.env_generator.generate_middleware_tree()

            # Map services and things to middleware
            self.env_generator.map_thing_to_middleware(root_middleware=root_middleware, thing_pool=thing_pool)

            # Generate application
            self.env_generator.generate_scenario(root_middleware=root_middleware)

            # Generate super service, super thing and super scenario
            self.env_generator.generate_super(root_middleware=root_middleware, tag_name_pool=tag_name_pool, super_service_name_pool=super_service_name_pool)

            # Generate event timing_list
            static_event_timing_list, dynamic_event_timing_list = self.env_generator._generate_event_timing_list(root_middleware=root_middleware)

            # Update simulation env
            simulation_env.root_middleware = root_middleware
            simulation_env.service_pool = service_pool
            simulation_env.thing_pool = thing_pool
            simulation_env.static_event_timing_list = static_event_timing_list
            simulation_env.dynamic_event_timing_list = dynamic_event_timing_list
            simulation_env_list.append(simulation_env)

        simulation_data_file_path = f'{self.env_generator._simulation_folder_path}/simulation_data.json'
        for simulation_env in simulation_env_list:
            simulation_env.simulation_data_file_path = simulation_data_file_path

        self.env_generator._export_simulation_data_file(simulation_env_list=simulation_env_list, simulation_data_file_path=simulation_data_file_path)
        return simulation_env_list

    @exception_wrapper
    def run_simulation(self, simulation_env: MXSimulationEnv, policy_path: str, index: int):
        MXTEST_LOG_DEBUG(f'==== Start simulation {simulation_env.config.name}, iter: {index}, policy: {os.path.basename(policy_path)} ====', MXTestLogLevel.INFO)
        self._simulator = MXSimulator(simulation_env=simulation_env, policy_path=policy_path, mqtt_debug=self._mqtt_debug, middleware_debug=self._middleware_debug, download_logs=self._download_logs)
        self._simulator.setup()
        self._simulator.cleanup()
        self._simulator.build_iot_system()
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

    # =========================
    #         _    _  _
    #        | |  (_)| |
    #  _   _ | |_  _ | | ___
    # | | | || __|| || |/ __|
    # | |_| || |_ | || |\__ \
    #  \__,_| \__||_||_||___/
    # =========================

    def _export_service_thing_pool(self, service_thing_pool_path: str, tag_name_pool: List[str], service_name_pool: List[str], super_service_name_pool: List[str], service_pool: List[MXService], thing_pool: List[MXThing]):
        service_pool_dict = [service.dict() for service in service_pool]
        thing_pool_dict = [thing.dict() for thing in thing_pool]
        service_thing_pool = {'tag_name_pool': tag_name_pool,
                              'service_name_pool': service_name_pool,
                              'super_service_name_pool': super_service_name_pool,
                              'service_pool': service_pool_dict,
                              'thing_pool': thing_pool_dict}
        save_json(service_thing_pool_path, service_thing_pool)
