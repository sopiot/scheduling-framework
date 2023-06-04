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

        self._simulation_env_list: List[SoPSimulationEnv] = []
        self._policy_path_list: List[str] = []

    def load(self, config_path: str = '', simulation_data_path: str = '', policy_path: str = '') -> None:
        if (config_path and simulation_data_path) or (not config_path and not simulation_data_path):
            raise Exception('Only one of config_path and simulation_data_path must be given.')

        if config_path:
            config_list = self.load_config(config_path=config_path)
            simulation_env_list: List[SoPSimulationEnv] = []
            for config in config_list:
                simulation_env = SoPSimulationEnv(config=config)
                simulation_env_list.append(simulation_env)
            self._simulation_env_list = simulation_env_list
        elif simulation_data_path:
            self._simulation_env_list = self.load_simulation_data(simulation_data_path=simulation_data_path)
        else:
            raise Exception('[SoPSimulationFramework.load] Unknown error')

        self._policy_path_list = self.load_policy(policy_path=policy_path)

    def load_config(self, config_path: str) -> List[SoPSimulationConfig]:
        if os.path.isdir(config_path):
            config_list = [SoPSimulationConfig(config_path=os.path.join(config_path, config_file_path)) for config_file_path in os.listdir(config_path)
                           if config_file_path.startswith('config') and config_file_path.endswith('.yml')]
        else:
            config_list = [SoPSimulationConfig(config_path=config_path)] \
                if (os.path.basename(config_path).startswith('config') and os.path.basename(config_path).endswith('.yml')) else []
        return config_list

    def load_service_thing_pool(self, service_thing_pool_path: str) -> Tuple[List[SoPService], List[SoPThing]]:
        service_thing_pool = load_json(service_thing_pool_path)
        service_pool = [SoPService.load(service_info) for service_info in service_thing_pool['service_pool']]
        thing_pool = [SoPService.load(thing_info=thing_info) for thing_info in service_thing_pool['thing_pool']]
        return service_pool, thing_pool

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
        if any([not simulation_env.root_middleware for simulation_env in self._simulation_env_list]):
            self._simulation_env_list = self.generate_simulation_env()

        simulation_result_list: List[SoPSimulationResult] = []
        for simulation_data in self._simulation_env_list:
            for policy_path in self._policy_path_list:
                simulation_result = self.run_simulation(simulation=simulation_data, policy_path=policy_path)
                simulation_result_list.append(simulation_result)

        self.print_ranking(simulation_result_list=simulation_result_list)

    def update_middleware_thing(self, simulator: SoPSimulator, middleware_path: str = '~/middleware', policy_file_path: str = ''):

        def get_os_version(ssh_client: SoPSSHClient) -> str:
            lsb_release_install_check = ssh_client.send_command_with_check_success('command -v lsb_release', get_pty=True)
            if not lsb_release_install_check:
                install_result = ssh_client.send_command_with_check_success('sudo apt install lsb-release -y;', get_pty=True)
                if not install_result:
                    raise Exception(f'Install lsb-release failed to {ssh_client.device.name}')

            remote_device_os = ssh_client.send_command('lsb_release -a')[1].split('\t')[1].strip()
            return remote_device_os

        def install_remote_middleware(ssh_client: SoPSSHClient, user: str):
            # result = ssh_client.send_command(
            #     f'rm -rf {home_dir_append(middleware_path, user)}')
            remote_device_os = get_os_version(ssh_client)
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
            middleware_update_result = ssh_client.send_command_with_check_success(f'cd {home_dir_append(middleware_path, user)};'
                                                                                  'chmod +x sopiot_middleware;'
                                                                                  'cmake .;'
                                                                                  'make -j')
            if not middleware_update_result:
                raise Exception(f'Install middleware to {ssh_client.device.name} failed')

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
                raise Exception(f'Install big-thing-py failed to {ssh_client.device.name}')

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
                        raise Exception(f'Generate ramdisk failed to {ssh_client.device.name}')

            return True

        def set_cpu_clock_remote(ssh_client: SoPSSHClient) -> None:
            set_clock_command = '''function check_cpu_clock_setting() {
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

        middleware_list: List[SoPMiddleware] = get_middleware_list_recursive(simulator.simulation_env)

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

    def export_service_thing_pool(self, service_thing_pool_path: str, service_pool: List[SoPService], thing_pool: List[SoPThing]):
        service_thing_pool = {'service_pool': service_pool, 'thing_pool': thing_pool}
        save_json(service_thing_pool, service_thing_pool_path)

    def generate_simulation_env(self) -> List[SoPSimulationEnv]:
        self.env_generator = SoPEnvGenerator(service_parallel=self._service_parallel)
        service_pool: List[SoPService] = []
        thing_pool: List[SoPThing] = []

        for simulation_env in self._simulation_env_list:
            simulation_config = simulation_env.config
            service_thing_pool_path = simulation_config.service_thing_pool_path.abs_path()

            # if service_thing_pool is given in config, load it
            if os.path.exists(service_thing_pool_path):
                service_pool, thing_pool = self.load_service_thing_pool(service_thing_pool_path=service_thing_pool_path)
                self.env_generator.load(config=simulation_env.config)
            # else generate service_thing_pool
            else:
                self.env_generator.load(config=simulation_env.config)
                tag_name_pool, service_name_pool = self.env_generator.generate_name_pool()
                service_pool = self.env_generator.generate_service_pool(tag_name_pool=tag_name_pool, service_name_pool=service_name_pool)
                thing_pool = self.env_generator.generate_thing_pool(service_pool=service_pool)

            root_middleware = self.env_generator.generate_middleware_tree(thing_pool=thing_pool)
            self.env_generator.map_thing_to_middleware(root_middleware=root_middleware, thing_pool=thing_pool)

            # TODO: generate_scenario and mapping to middleware tree
            # TODO: generate super thing, scenario, and mapping to middleware tree

            simulation_info = dict(simulation_file_path=simulation_file_path,
                                   config_path=config_path,
                                   policy_file_path=[],
                                   label=[])
            for policy_file_path in policy_file_path_list:
                simulation_info['policy_file_path'].append(policy_file_path)
                simulation_info['label'].append(f'{self.env_generator.simulation_config.name}_policy_{os.path.basename(policy_file_path).split(".")[0]}')
            simulation_info_list.append(simulation_info)

        save_json(path=config.service_thing_pool_path.abs_path(), data={'service_pool': [], 'thing_pool': []})
        return simulation_info_list

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
