from simulation_framework.core.simulator import *
from simulation_framework.core.env_generator import *
from simulation_framework.core.evaluator import *
from simulation_framework.profiler import *


PREDEFINED_POLICY_FILE_NAME = 'my_scheduling_policies.cc'
SCHEDULING_ALGORITHM_PATH = f'{get_project_root()}/scheduling_algorithm'


class SoPSimulationFramework:

    def __init__(self, service_parallel: bool = True, result_filename: str = '', download_logs: bool = False,
                 profile: bool = False, profile_type: ProfileType = ProfileType.EXECUTE,
                 mqtt_debug: bool = False, middleware_debug: bool = False) -> None:
        self._service_parallel = service_parallel
        self._result_filename = result_filename
        self._download_logs = download_logs
        self._profile = profile
        self._profile_type = profile_type
        self._mqtt_debug = mqtt_debug
        self._middleware_debug = middleware_debug

        self._config_list: List[SoPSimulationConfig] = []
        self._policy_path_list: List[str] = []
        self._simulation_env_list: List[SoPSimulationEnv] = []

    def load(self, config_path: str = '', simulation_data_path: str = '', policy_path: str = '') -> None:
        if config_path:
            self._config_list = self.load_config(config_path=config_path)
        elif simulation_data_path:
            self._simulation_env_list = self.load_simulation_data(simulation_data_path=simulation_data_path)
        else:
            raise ConfigPathError('Only one of config_path and simulation_data_path must be given.', path='not given')

        self._policy_path_list = self.load_policy(policy_path=policy_path)

    def load_config(self, config_path: str) -> List[SoPSimulationConfig]:
        if os.path.isdir(config_path):
            config_list = [SoPSimulationConfig(config_path=os.path.join(config_path, config_file_path)) for config_file_path in os.listdir(config_path)
                           if config_file_path.startswith('config') and config_file_path.endswith('.yml')]
        else:
            config_list = [SoPSimulationConfig(config_path=config_path)] \
                if (os.path.basename(config_path).startswith('config') and os.path.basename(config_path).endswith('.yml')) else []
        return config_list

    def load_service_thing_pool(self, service_thing_pool_path: str) -> Tuple[List[str], List[str], List[SoPService], List[SoPThing]]:
        if not os.path.exists(service_thing_pool_path):
            return [], [], [], []

        service_thing_pool = load_json(service_thing_pool_path)
        tag_name_pool = service_thing_pool['tag_name_pool']
        service_name_pool = service_thing_pool['service_name_pool']
        service_pool = [SoPService.load(service_info) for service_info in service_thing_pool['service_pool']]
        thing_pool = [SoPThing.load(thing_info) for thing_info in service_thing_pool['thing_pool']]
        for thing in thing_pool:
            for service in thing.service_list:
                service.thing = thing
        return tag_name_pool, service_name_pool, service_pool, thing_pool

    def load_simulation_data(self, simulation_data_path: str) -> Tuple[SoPSimulationConfig, List[SoPSimulationEnv]]:
        simulation_data_file = load_json(simulation_data_path)
        simulation_env_list: List[SoPSimulationEnv] = []
        for simulation_env_info in simulation_data_file['simulation_env_list']:
            config = simulation_env_info['config']
            root_middleware = SoPMiddleware.load(simulation_env_info['root_middleware'])
            event_timeline = simulation_env_info['event_timeline']
            simulation_env = SoPSimulationEnv(config=config, root_middleware=root_middleware, event_timeline=event_timeline)
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

        simulation_result_list: List[SoPSimulationResult] = []
        for simulation_data in self._simulation_env_list:
            for policy_path in self._policy_path_list:
                simulation_result = self.run_simulation(simulation=simulation_data, policy_path=policy_path)
                simulation_result_list.append(simulation_result)

        self.print_ranking(simulation_result_list=simulation_result_list)

    def update_middleware_thing(self, simulator: SoPSimulator, middleware_path: str = '~/middleware', policy_file_path: str = ''):

        def install_remote_middleware(ssh_client: SoPSSHClient, user: str):
            # result = ssh_client.send_command(
            #     f'rm -rf {home_dir_append(middleware_path, user)}')
            remote_device_os = self.get_remote_device_OS(ssh_client)
            ssh_client.send_command('pidof sopiot_middleware | xargs kill -9')
            ssh_client.send_dir(SCHEDULING_ALGORITHM_PATH, home_dir_append(middleware_path, user))
            if 'Ubuntu 20.04' in remote_device_os:
                ssh_client.send_file(f'{get_project_root()}/bin/sopiot_middleware_ubuntu2004_x64',
                                     f'{home_dir_append(middleware_path, user)}/sopiot_middleware')
            elif 'Ubuntu 22.04' in remote_device_os:
                ssh_client.send_file(f'{get_project_root()}/bin/sopiot_middleware_ubuntu2204_x64',
                                     f'{home_dir_append(middleware_path, user)}/sopiot_middleware')
            elif 'Raspbian' in remote_device_os:
                ssh_client.send_file(f'{get_project_root()}/bin/sopiot_middleware_pi_x86',
                                     f'{home_dir_append(middleware_path, user)}/sopiot_middleware')
            ssh_client.send_file(policy_file_path, f'{home_dir_append(middleware_path, user)}/{PREDEFINED_POLICY_FILE_NAME}')
            command = (f'cd {home_dir_append(middleware_path, user)};'
                       'chmod +x sopiot_middleware;'
                       'cmake .;'
                       'make -j')
            middleware_update_result = ssh_client.send_command_with_check_success(command)
            if not middleware_update_result:
                raise SSHCommandFailError(command=command, reason=f'Install middleware to {ssh_client.device.name} failed')

            SOPTEST_LOG_DEBUG(f'Install middleware to {ssh_client.device.name} success', SoPTestLogLevel.INFO)
            return True

        def install_remote_thing(ssh_client: SoPSSHClient, force_install: bool = True):
            # if not any([thing.is_super for thing in middleware.thing_list]):
            #     SOPTEST_LOG_DEBUG(f'device {middleware.device.name} middleware {middleware.name} is not have Super Thing', SoPTestLogLevel.INFO)
            #     return True
            thing_install_command = f'pip install big-thing-py {"--force-reinstall --no-deps" if force_install else ""}'
            SOPTEST_LOG_DEBUG(f'{"[FORCE] " if force_install else ""}big-thing-py install to {ssh_client.device.name} start', SoPTestLogLevel.INFO)
            pip_install_result = ssh_client.send_command_with_check_success(thing_install_command)
            if not pip_install_result:
                raise SSHCommandFailError(command=thing_install_command, reason=f'Install big-thing-py failed to {ssh_client.device.name}')

            SOPTEST_LOG_DEBUG(f'{"[FORCE] " if force_install else ""}big-thing-py install to {ssh_client.device.name} end', SoPTestLogLevel.INFO)
            return True

        def init_ramdisk(ssh_client: SoPSSHClient) -> None:
            ramdisk_check_command = 'ls /mnt/ramdisk'
            ramdisk_generate_command_list = [f'sudo mkdir -p /mnt/ramdisk',
                                             f'sudo mount -t tmpfs -o size=200M tmpfs /mnt/ramdisk',
                                             f'echo "none /mnt/ramdisk tmpfs defaults,size=200M 0 0" | sudo tee -a /etc/fstab > /dev/null',
                                             f'sudo chmod 777 /mnt/ramdisk']
            ramdisk_check_result = ssh_client.send_command_with_check_success(ramdisk_check_command)
            if not ramdisk_check_result:
                for ramdisk_generate_command in ramdisk_generate_command_list:
                    result = ssh_client.send_command_with_check_success(ramdisk_generate_command)
                    if not result:
                        raise SSHCommandFailError(command=ramdisk_generate_command, reason=f'Generate ramdisk failed to {ssh_client.device.name}')

            return True

        def set_cpu_clock_remote(ssh_client: SoPSSHClient) -> None:
            set_clock_command = '''\
function check_cpu_clock_setting() {
	sudo cat /sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_cur_freq
	sudo cat /sys/devices/system/cpu/cpu1/cpufreq/cpuinfo_cur_freq
	sudo cat /sys/devices/system/cpu/cpu2/cpufreq/cpuinfo_cur_freq
	sudo cat /sys/devices/system/cpu/cpu3/cpufreq/cpuinfo_cur_freq
}

function set_cpu_clock() {
	echo "performance" | sudo tee /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
	echo "performance" | sudo tee /sys/devices/system/cpu/cpu1/cpufreq/scaling_governor
	echo "performance" | sudo tee /sys/devices/system/cpu/cpu2/cpufreq/scaling_governor
	echo "performance" | sudo tee /sys/devices/system/cpu/cpu3/cpufreq/scaling_governor
	# Ondemand
	# Interactive
	# Schedutil
}

check_cpu_clock_setting
set_cpu_clock
check_cpu_clock_setting'''
            result = ssh_client.send_command_with_check_success(set_clock_command)
            if not result:
                SOPTEST_LOG_DEBUG(f'Set cpu clock {ssh_client.device.name} failed!', SoPTestLogLevel.FAIL)

        def send_task(ssh_client: SoPSSHClient):
            remote_home_dir = ssh_client.send_command('cd ~ && pwd')[0]
            user = os.path.basename(remote_home_dir)
            install_remote_middleware(ssh_client=ssh_client, user=user)

        def task(ssh_client: SoPSSHClient):
            install_remote_thing(ssh_client=ssh_client, force_install=True)
            init_ramdisk(ssh_client=ssh_client)

            if ssh_client.device.name != 'localhost':
                set_cpu_clock_remote(ssh_client=ssh_client)

        middleware_list: List[SoPMiddleware] = get_whole_middleware_list(simulator.simulation_env)

        middleware_ssh_client_list = list(set([simulator.event_handler.find_ssh_client(middleware) for middleware in middleware_list]))
        thing_ssh_client_list = list(set([simulator.event_handler.find_ssh_client(thing) for middleware in middleware_list for thing in middleware.thing_list]))

        pool_map(task, list(set(middleware_ssh_client_list + thing_ssh_client_list)))
        pool_map(send_task, middleware_ssh_client_list, proc=1)

        return True

    def print_ranking(self, simulation_result_list: List[SoPSimulationResult]):
        if not simulation_result_list:
            SOPTEST_LOG_DEBUG(f'No simulation result', SoPTestLogLevel.WARN)
            return False

        simulation_result_list_sort_by_policy: Dict[str, List[SoPSimulationResult]] = {}
        for simulation_result in simulation_result_list:
            if simulation_result.policy in simulation_result_list_sort_by_policy:
                simulation_result_list_sort_by_policy[simulation_result.policy].append(simulation_result)
            else:
                simulation_result_list_sort_by_policy[simulation_result.policy] = [simulation_result]
        simulation_result_list: List[SoPSimulationResult] = []
        for policy, result_list in simulation_result_list_sort_by_policy.items():
            simulation_result_avg = SoPSimulationResult(policy=policy,
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
policy: {simulation_result_list_sort_by_application_latency[i].policy}''',
                      f'''energy: {f'{simulation_result_list_sort_by_application_energy[i].avg_energy:.2f}'}
policy: {simulation_result_list_sort_by_application_energy[i].policy}''',
                      f'''success_ratio: {f'{simulation_result_list_sort_by_success_ratio[i].avg_success_ratio * 100:.2f}'}
policy: {simulation_result_list_sort_by_success_ratio[i].policy}'''] for i in range(len(simulation_result_list))], rank_header)

        return True

    def calculate_num_thing_service_generate(self, config: SoPSimulationConfig, loaded_tag_name_num: int, loaded_service_name_num: int,
                                             loaded_service_num: int, loaded_thing_num: int) -> Tuple[int, int, int, int]:
        manual_middleware_tree = config.middleware_config.manual_middleware_tree
        random_middleware_config = config.middleware_config.random

        # Set service_num according to current config
        tag_type_num = config.service_config.tag_type_num
        service_name_num = 0
        service_num = config.service_config.normal.service_type_num
        thing_num = 0

        # Calculate max_thing_num according to current config
        if manual_middleware_tree:
            middleware_config_list = [manual_middleware_tree] + list(manual_middleware_tree.descendants)
            max_thing_num = sum([middleware_config.thing_num[1] for middleware_config in middleware_config_list])
            max_super_thing_num = sum([middleware_config.super_thing_num[1] for middleware_config in middleware_config_list])
        elif random_middleware_config:
            max_middleware_num = calculate_tree_node_num(random_middleware_config.height[1], random_middleware_config.width[1])
            max_thing_num = max_middleware_num * random_middleware_config.normal.thing_per_middleware[1]
            max_super_thing_num = max_middleware_num * random_middleware_config.super.thing_per_middleware[1]
        else:
            raise SimulationFailError('manual_middleware_tree and random_middleware_config are both None')

        thing_num = max_thing_num
        service_name_num = max_thing_num * config.thing_config.normal.service_per_thing[1] + max_super_thing_num * config.thing_config.super.service_per_thing[1]

        # If config.force_generate is True, generate service and thing pool according to current
        # Else, generate services and things as much as the difference between the number of
        # service thing pools to be created in the current setting and the number of service
        # thing pools already created.
        if config.force_generate:
            pass
        else:
            tag_type_num -= loaded_tag_name_num
            service_name_num -= loaded_service_name_num
            service_num -= loaded_service_num
            thing_num -= loaded_thing_num

            if tag_type_num <= 0:
                tag_type_num = 0
            if service_name_num <= 0:
                service_name_num = 0
            if service_num <= 0:
                service_num = 0
            if thing_num <= 0:
                thing_num = 0

        return tag_type_num, service_name_num, service_num, thing_num

    def generate_simulation_env(self, config_list: List[SoPSimulationConfig]) -> List[SoPSimulationEnv]:
        self.env_generator = SoPEnvGenerator(service_parallel=self._service_parallel)

        simulation_env_list: List[SoPSimulationEnv] = []
        for config in config_list:
            loaded_tag_name_pool, loaded_service_name_pool, loaded_service_pool, loaded_thing_pool = [], [], [], []
            simulation_env = SoPSimulationEnv(config=config)
            service_thing_pool_path = config.service_thing_pool_path.abs_path()

            self.env_generator.load(config=simulation_env.config)

            # If service_thing_pool path is given in config, load it
            if not config.force_generate:
                loaded_tag_name_pool, loaded_service_name_pool, loaded_service_pool, loaded_thing_pool = self.load_service_thing_pool(service_thing_pool_path=service_thing_pool_path)

            # Calculate the number of services and things to be generated
            num_tag_name_generate, num_service_name_generate, num_service_generate, num_thing_generate = \
                self.calculate_num_thing_service_generate(config=config,
                                                          loaded_tag_name_num=len(loaded_tag_name_pool), loaded_service_name_num=len(loaded_service_name_pool),
                                                          loaded_service_num=len(loaded_service_pool), loaded_thing_num=len(loaded_thing_pool))

            # Generate services and things
            generated_tag_name_pool, generated_service_name_pool = self.env_generator.generate_name_pool(num_tag_name=num_tag_name_generate, num_service_name=num_service_name_generate)
            tag_name_pool = loaded_tag_name_pool + generated_tag_name_pool
            service_name_pool = loaded_service_name_pool + generated_service_name_pool
            raw_service_name_pool = copy.deepcopy(service_name_pool)
            generated_service_pool = self.env_generator.generate_service_pool(tag_name_pool=tag_name_pool, service_name_pool=service_name_pool, num_service_generate=num_service_generate)
            service_pool = loaded_service_pool + generated_service_pool
            generated_thing_pool = self.env_generator.generate_thing_pool(service_pool=service_pool, num_thing_generate=num_thing_generate)
            thing_pool = loaded_thing_pool + generated_thing_pool

            # Export service_thing_pool
            self.export_service_thing_pool(tag_name_pool=tag_name_pool, service_name_pool=raw_service_name_pool,
                                           service_thing_pool_path=service_thing_pool_path, service_pool=service_pool, thing_pool=thing_pool)

            # Generate middleware tree
            root_middleware = self.env_generator.generate_middleware_tree(thing_pool=thing_pool)

            # Map services and things to middleware
            self.env_generator.map_thing_to_middleware(root_middleware=root_middleware, thing_pool=thing_pool)

            # Generate application
            self.env_generator.generate_scenario(root_middleware=root_middleware)

            # Generate super service, super thing and super scenario
            self.env_generator.generate_super(root_middleware=root_middleware, tag_name_pool=tag_name_pool, super_service_name_pool=service_name_pool)

            # TODO: Generate event timeline
            static_event_timeline, dynamic_event_timeline = self.env_generator._generate_event_timeline(root_middleware=root_middleware)

            simulation_env.root_middleware = root_middleware
            simulation_env.service_pool = service_pool
            simulation_env.thing_pool = thing_pool
            simulation_env.static_event_timeline = static_event_timeline
            simulation_env.dynamic_event_timeline = dynamic_event_timeline
            simulation_env_list.append(simulation_env)

        simulation_data_file_path = self.env_generator._export_simulation_data_file(simulation_env_list=simulation_env_list, simulation_folder_path=self.env_generator._simulation_folder_path)
        return simulation_env_list

    def run_simulation(self, config: SoPSimulationConfig, simulation_data: SoPSimulationEnv, policy_file_path: str):
        """ Steps in a Simulation:
            1. setup
                1-1. generate simulation data files
            2. cleanup
                2-1. remove every remote simulation files
                2-2. kill every process
            3. build_iot_system
                3-1. send the generated data
            4. trigger_events
                4-1. trigger static events
                4-2. trigger dynamic events
            5. evaluate
                5-1. get simulation result
        """
        # SOPTEST_LOG_DEBUG(f'==== Start simulation {label} ====', SoPTestLogLevel.INFO)
        simulator = SoPSimulator(simulation_env=simulation_data, mqtt_debug=self._mqtt_debug, middleware_debug=self._middleware_debug)
        simulator.setup(config=config, simulation_file_path=self.simulation_file_path)
        # simulator.cleanup()
        # simulator.kill_every_process()
        # simulator.remove_every_files()
        # simulator.build_iot_system()
        # simulator.start()

        self.update_middleware_thing(simulator=simulator, middleware_path='~/middleware', policy_file_path=policy_file_path)

        try:
            # simulation_env, event_log, simulation_duration, simulation_start_time = simulator.start()
            simulator.start()
        except Exception as e:
            print_error(e)

        evaluator = SoPEvaluator(simulation_env, event_log, simulation_duration, simulation_start_time)
        # evaluator.eval(simulator.result)

        simulation_result = evaluator.evaluate_simulation()
        simulation_result.config = self.env_generator.simulation_config.name
        simulation_result.policy = os.path.basename(policy_file_path).split(".")[0]
        simulation_result_list.append(simulation_result)

        profiler = None
        if args.download_logs:
            simulator.event_handler.download_log_file()
        if args.profile:
            log_root_path = simulator.event_handler.download_log_file()
            profiler = Profiler()
            profiler.load(log_root_path=log_root_path)
            simulation_overhead = profiler.profile(args.profile_type, export=True)

        evaluator.export_txt(simulation_result=simulation_result, simulation_overhead=simulation_overhead, label=label, args=args)
        evaluator.export_csv(simulation_result=simulation_result, simulation_overhead=simulation_overhead, label=label, args=args)

        # TODO: Make wrapup_simulation method
        simulator.event_handler.wrapup()
        # del simulator
        # del evaluator

        return simulation_result_list

    # =========================
    #         _    _  _
    #        | |  (_)| |
    #  _   _ | |_  _ | | ___
    # | | | || __|| || |/ __|
    # | |_| || |_ | || |\__ \
    #  \__,_| \__||_||_||___/
    # =========================

    def export_service_thing_pool(self, service_thing_pool_path: str, tag_name_pool: List[str], service_name_pool: List[str], service_pool: List[SoPService], thing_pool: List[SoPThing]):
        service_pool_dict = [service.dict() for service in service_pool]
        thing_pool_dict = [thing.dict() for thing in thing_pool]
        service_thing_pool = {'tag_name_pool': tag_name_pool,
                              'service_name_pool': service_name_pool,
                              'service_pool': service_pool_dict,
                              'thing_pool': thing_pool_dict}
        save_json(service_thing_pool_path, service_thing_pool)

    def get_remote_device_OS(self, ssh_client: SoPSSHClient) -> str:
        lsb_release_install_check = ssh_client.send_command_with_check_success('command -v lsb_release', get_pty=True)
        if not lsb_release_install_check:
            command = 'sudo apt install lsb-release -y;'
            install_result = ssh_client.send_command_with_check_success(command, get_pty=True)
            if not install_result:
                raise SSHCommandFailError(command=command, reason=f'Install lsb-release failed to {ssh_client.device.name}')

        remote_device_os = ssh_client.send_command('lsb_release -a')[1].split('\t')[1].strip()
        return remote_device_os
