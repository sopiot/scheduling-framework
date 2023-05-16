from simulation_framework.core.simulation_executor import *
from simulation_framework.core.simulation_generator import *
from simulation_framework.core.simulation_evaluator import *
from tqdm import tqdm, trange


PREDEFINED_POLICY_FILE_NAME = 'my_scheduling_policies.cc'
SCHEDULING_ALGORITHM_PATH = f'{get_project_root()}/scheduling_algorithm'


class MXSchedulingFramework:

    def __init__(self, config_path_list: List[str] = [], simulation_file_path: str = '', mqtt_debug: bool = False, middleware_debug: bool = False) -> None:
        tmp_config_path_list = []
        for config_file_path in config_path_list:
            if os.path.isdir(config_file_path):
                tmp_config_path_list.extend(
                    [os.path.join(config_file_path, file) for file in os.listdir(config_file_path) if os.path.basename(file).endswith('.yml') and os.path.basename(file).startswith('config')])
            elif os.path.isfile(config_file_path) and os.path.basename(config_file_path).endswith('.yml') and os.path.basename(config_file_path).startswith('config'):
                tmp_config_path_list.append(config_file_path)

        if not tmp_config_path_list:
            raise Exception('No config file provided.')

        simulation_name_list = [load_yaml(config_file_path)[
            'simulation']['name'] for config_file_path in tmp_config_path_list]

        visited = set()
        duplicated_simulation_name_list = list({x for x in simulation_name_list if x in visited or (
            visited.add(x) or False)})
        if len(simulation_name_list) != len(set(simulation_name_list)):
            raise Exception(
                f'Simulation name should be unique. - simulation name: {duplicated_simulation_name_list}')

        self.config_path_list = tmp_config_path_list
        self.simulation_file_path = simulation_file_path
        self.mqtt_debug = mqtt_debug
        self.middleware_debug = middleware_debug

        if not self.simulation_file_path and not self.config_path_list:
            raise Exception('No config file path provided.')
        elif self.config_path_list:
            self.simulation_generator = MXSimulationGenerator(
                config_path=self.config_path_list[0])

    def start(self, policy_file_path_list: Union[str, List[str]] = [], args=None):
        tmp_policy_file_path_list = []
        for policy_file_path in policy_file_path_list:
            if os.path.isdir(policy_file_path):
                tmp_policy_file_path_list.extend(
                    [os.path.join(policy_file_path, file) for file in sorted(os.listdir(policy_file_path)) if file.endswith('.cc')])
            elif os.path.isfile(policy_file_path) and policy_file_path.endswith('.cc'):
                tmp_policy_file_path_list.append(policy_file_path)

        if not tmp_policy_file_path_list:
            raise Exception('No policy file provided.')

        if not self.simulation_file_path:
            simulation_info_list = self.generate_simulation(
                policy_file_path_list=tmp_policy_file_path_list, args=args)
        else:
            simulation_info_list = [dict(simulation_file_path=self.simulation_file_path,
                                         config_path='',
                                         policy_file_path=tmp_policy_file_path_list,
                                         label=['test_simulation'])]
        simulation_result_list = self.run_simulation(simulation_info_list=simulation_info_list,
                                                     policy_file_path_list=tmp_policy_file_path_list, args=args)
        self.print_ranking(raw_simulation_result_list=simulation_result_list)

    def update_middleware_thing(self, simulation_executor: MXSimulatorExecutor,
                                middleware_path: str = '~/middleware',
                                policy_file_path: str = ''):

        simulator_ip = ''

        def get_os_version(ssh_client: MXSSHClient) -> str:
            lsb_release_install_check = ssh_client.send_command_with_check_success('command -v lsb_release', get_pty=True)
            if not lsb_release_install_check:
                install_result = ssh_client.send_command_with_check_success('sudo apt install lsb-release -y;', get_pty=True)
                if not install_result:
                    raise Exception(f'Install lsb-release failed to {ssh_client.device.name}')

            remote_device_os = ssh_client.send_command('lsb_release -a')[1].split('\t')[1].strip()
            return remote_device_os

        def install_remote_middleware(ssh_client: MXSSHClient, user: str):
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

            MXTEST_LOG_DEBUG(f'Install middleware to {ssh_client.device.name} success', MXTestLogLevel.INFO)
            return True

        def install_remote_thing(ssh_client: MXSSHClient, force_install: bool = True):
            # if not any([thing.is_super for thing in middleware.thing_list]):
            #     MXTEST_LOG_DEBUG(f'device {middleware.device.name} middleware {middleware.name} is not have Super Thing', MXTestLogLevel.INFO)
            #     return True
            thing_install_command = f'pip install big-thing-py {"--force-reinstall --no-deps" if force_install else ""}'
            MXTEST_LOG_DEBUG(f'{"[FORCE] " if force_install else ""}big-thing-py install to {ssh_client.device.name} start', MXTestLogLevel.INFO)
            pip_install_result = ssh_client.send_command_with_check_success(thing_install_command)
            if not pip_install_result:
                raise Exception(f'Install big-thing-py failed to {ssh_client.device.name}')

            MXTEST_LOG_DEBUG(f'{"[FORCE] " if force_install else ""}big-thing-py install to {ssh_client.device.name} end', MXTestLogLevel.INFO)
            return True

        def init_ramdisk(ssh_client: MXSSHClient) -> None:
            # TODO: not tested yet
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

        def time_sync(ssh_client: MXSSHClient) -> None:
            remote_home_dir = ssh_client.send_command('cd ~ && pwd')[0]
            remote_shell_path = ssh_client.send_command('echo $SHELL')
            remote_shell_name = remote_shell_path[0].split('/')[-1].strip()
            ntp_install_result = ssh_client.send_command_with_check_success(f'source {remote_home_dir}/.{remote_shell_name}rc; command -v ntpdate', get_pty=True)
            if not ntp_install_result:
                ntp_install_success_result = ssh_client.send_command_with_check_success('sudo apt install ntpdate -y')
                if not ntp_install_success_result:
                    raise Exception(f'Install ntpdate failed to {ssh_client.device.name}')

            # sudo sed -i -E 's/^pool 0\.(.*)\.pool\.ntp\.org iburst/pool time1.google.com iburst/g' /etc/ntp.conf
            # sudo sed -i -E 's/^pool 1\.(.*)\.pool\.ntp\.org iburst/pool time2.google.com iburst/g' /etc/ntp.conf
            # sudo sed -i -E 's/^pool 2\.(.*)\.pool\.ntp\.org iburst/pool time3.google.com iburst/g' /etc/ntp.conf
            # sudo sed -i -E 's/^pool 3\.(.*)\.pool\.ntp\.org iburst/pool time4.google.com iburst/g' /etc/ntp.conf
            # cat /etc/ntp.conf | grep "time1.google.com"
            # ntp_conf_check_command = ('cat /etc/ntp.conf | grep "time1.google.com"'
            #                           'cat /etc/ntp.conf | grep "time2.google.com"'
            #                           'cat /etc/ntp.conf | grep "time3.google.com"'
            #                           'cat /etc/ntp.conf | grep "time4.google.com"')
            # ntp_conf_check_command_result = ssh_client.send_command(ntp_conf_check_command, get_pty=True)
            # time_sync_command = ("sudo sed -i -E 's/^pool 0\.(.*)\.pool\.ntp\.org iburst/pool time1.google.com iburst/g' /etc/ntp.conf"
            #                      "sudo sed -i -E 's/^pool 1\.(.*)\.pool\.ntp\.org iburst/pool time2.google.com iburst/g' /etc/ntp.conf"
            #                      "sudo sed -i -E 's/^pool 2\.(.*)\.pool\.ntp\.org iburst/pool time3.google.com iburst/g' /etc/ntp.conf"
            #                      "sudo sed -i -E 's/^pool 3\.(.*)\.pool\.ntp\.org iburst/pool time4.google.com iburst/g' /etc/ntp.conf"
            #                      'sudo service ntp restart;'
            #                      'ntpq -p')

            # time_sync_command = (f'source {remote_home_dir}/.{remote_shell_name}rc;'
            #                      f'sudo service ntp stop;'
            #                      f'sudo ntpdate {simulator_ip}')
            time_sync_command = ('sudo service ntp restart;'
                                 'ntpq -p')
            MXTEST_LOG_DEBUG(f'Time sync {ssh_client.device.name} start', MXTestLogLevel.INFO)
            time_sync_result = ssh_client.send_command_with_check_success(time_sync_command, get_pty=True)
            if not time_sync_result:
                MXTEST_LOG_DEBUG(f'Time sync {ssh_client.device.name} failed!', MXTestLogLevel.FAIL)
                return False

            MXTEST_LOG_DEBUG(f'Time sync {ssh_client.device.name} end', MXTestLogLevel.INFO)
            return True

        def send_task(ssh_client: MXSSHClient):
            remote_home_dir = ssh_client.send_command('cd ~ && pwd')[0]
            user = os.path.basename(remote_home_dir)
            install_remote_middleware(ssh_client=ssh_client, user=user)

        def task(ssh_client: MXSSHClient):
            install_remote_thing(ssh_client=ssh_client, force_install=True)
            init_ramdisk(ssh_client=ssh_client)
            time_sync(ssh_client=ssh_client)

        middleware_list: List[MXMiddlewareElement] = get_middleware_list_recursive(simulation_executor.simulation_env)
        ssh_client_list = list(set([simulation_executor.event_handler.find_ssh_client(middleware) for middleware in middleware_list] +
                               [simulation_executor.event_handler.find_ssh_client(thing) for middleware in middleware_list for thing in middleware.thing_list]))
        local_ssh_client = None
        for ssh_client in ssh_client_list:
            if ssh_client.device.name == 'localhost':
                local_ssh_client = ssh_client
                break

        ip_list = local_ssh_client.send_command('hostname -I')[0].split(' ')
        for ip in ip_list:
            if not '192.168' in ip:
                continue
            simulator_ip = ip
            break
        pool_map(task, ssh_client_list)
        pool_map(send_task, ssh_client_list, proc=1)

        return True

    def print_ranking(self, raw_simulation_result_list: List[MXSimulationResult]):
        if not raw_simulation_result_list:
            MXTEST_LOG_DEBUG(f'No simulation result', MXTestLogLevel.WARN)
            return False

        simulation_result_list_sort_by_policy: Dict[str, List[MXSimulationResult]] = {}
        for simulation_result in raw_simulation_result_list:
            if simulation_result.policy in simulation_result_list_sort_by_policy:
                simulation_result_list_sort_by_policy[simulation_result.policy].append(simulation_result)
            else:
                simulation_result_list_sort_by_policy[simulation_result.policy] = [simulation_result]
        simulation_result_list: List[MXSimulationResult] = []
        for policy, result_list in simulation_result_list_sort_by_policy.items():
            simulation_result_avg = MXSimulationResult(policy=policy,
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

    def generate_simulation(self, policy_file_path_list: List[str] = [], args=None):
        simulation_ID = None
        simulation_info_list = []

        for config_path in self.config_path_list:
            device_pool_path = MXPath(project_root_path=get_project_root(),
                                       config_path=config_path,
                                       path=load_yaml(config_path)['device_pool_path'])
            device_list: List[dict] = load_yaml(device_pool_path.abs_path())
            valid_device_list = [device for device in device_list if device != 'localhost']

            if not 'sim_env_samples' in config_path:
                pass
            elif 'paper_experiments' in config_path:
                if len(valid_device_list) < 11:
                    raise Exception(f'device pool is not enough for {os.path.basename(os.path.dirname(config_path))} simulation. (Requires at least 11 devices)')
            elif 'remote' in config_path:
                if 'simple_home' in config_path:
                    if len(valid_device_list) < 1:
                        raise Exception(f'device pool is not enough for {os.path.basename(os.path.dirname(config_path))} simulation. (Requires at least 1 devices)')
                elif 'simple_building' in config_path:
                    if len(valid_device_list) < 5:
                        raise Exception(f'device pool is not enough for {os.path.basename(os.path.dirname(config_path))} simulation. (Requires at least 5 devices)')
                elif 'simple_campus' in config_path:
                    if len(valid_device_list) < 7:
                        raise Exception(f'device pool is not enough for {os.path.basename(os.path.dirname(config_path))} simulation. (Requires at least 7 devices)')

            simulation_file_path, simulation_ID = self.simulation_generator.generate_simulation(simulation_ID=simulation_ID,
                                                                                                config_path=config_path,
                                                                                                is_parallel=args.is_parallel)
            simulation_info = dict(simulation_file_path=simulation_file_path,
                                   config_path=config_path,
                                   policy_file_path=[],
                                   label=[])
            for policy_file_path in policy_file_path_list:
                simulation_info['policy_file_path'].append(policy_file_path)
                simulation_info['label'].append(f'{self.simulation_generator.simulation_config.name}_policy_{os.path.basename(policy_file_path).split(".")[0]}')
            simulation_info_list.append(simulation_info)
        return simulation_info_list

    def run_simulation(self, simulation_info_list: List[dict], policy_file_path_list: List[str] = [], args=None):
        # FIXME: simulation file을 직접 명세하여 시뮬레이션을 진행하는 경우 config 파일 위치를 알 수 없어 에러 발생.
        # 이 부분 수정할 것
        simulation_result_list: List[MXSimulationResult] = []

        if self.simulation_file_path:
            simulation_executor = MXSimulatorExecutor(simulation_file_path=self.simulation_file_path,
                                                       mqtt_debug=self.mqtt_debug,
                                                       middleware_debug=self.middleware_debug,
                                                       args=args)

            for policy_file_path in policy_file_path_list:
                label = f'simulation_file_{self.simulation_file_path}_policy_{os.path.basename(policy_file_path).split(".")[0]}'
                MXTEST_LOG_DEBUG(f'==== Start simulation {label} ====', MXTestLogLevel.INFO)

                self.update_middleware_thing(
                    simulation_executor=simulation_executor,
                    middleware_path='~/middleware',
                    policy_file_path=policy_file_path)

                try:
                    simulation_env, event_log, simulation_duration, simulation_start_time = simulation_executor.start()
                except Exception as e:
                    print_error(e)
                    continue

                simulation_evaluator = MXSimulationEvaluator(simulation_env, event_log, simulation_duration, simulation_start_time)
                simulation_result = simulation_evaluator.evaluate_simulation()
                simulation_result.config = self.simulation_generator.simulation_config.name
                simulation_result.policy = os.path.basename(policy_file_path).split(".")[0]
                simulation_result_list.append(simulation_result)

                profiler = None
                if args.download_logs:
                    simulation_executor.event_handler.download_log_file()
                if args.profile:
                    root_log_path = simulation_executor.event_handler.download_log_file()
                    profiler = Profiler(root_log_folder_path=root_log_path)
                    profiler.profile(ProfileType.EXECUTE, export=False)

                simulation_evaluator.export_txt(simulation_result=simulation_result, profiler=profiler, label=label, args=args)
                simulation_evaluator.export_csv(simulation_result=simulation_result, profiler=profiler, label=label, args=args)

                simulation_executor.event_handler.wrapup()

                del simulation_executor
                del simulation_evaluator
        else:
            for simulation_info in simulation_info_list:
                for label, policy_file_path in zip(simulation_info['label'], simulation_info['policy_file_path']):
                    MXTEST_LOG_DEBUG(f'==== Start simulation {label} ====', MXTestLogLevel.INFO)

                    simulation_file_path = simulation_info['simulation_file_path']
                    args.config_path = simulation_info['config_path']

                    simulation_executor = MXSimulatorExecutor(
                        simulation_file_path=simulation_file_path,
                        mqtt_debug=self.mqtt_debug,
                        middleware_debug=self.middleware_debug,
                        args=args)
                    self.update_middleware_thing(
                        simulation_executor=simulation_executor,
                        middleware_path='~/middleware',
                        policy_file_path=policy_file_path)

                    try:
                        simulation_env, event_log, simulation_duration, simulation_start_time = simulation_executor.start()
                    except Exception as e:
                        MXTEST_LOG_DEBUG(f'==== Simulation {label} Canceled by user ====', MXTestLogLevel.WARN)
                        continue

                    simulation_evaluator = MXSimulationEvaluator(simulation_env, event_log, simulation_duration, simulation_start_time)
                    simulation_result = simulation_evaluator.evaluate_simulation()
                    simulation_result.config = os.path.basename(self.simulation_generator.simulation_config.path).split('.')[0]
                    simulation_result.policy = os.path.basename(policy_file_path).split('.')[0]
                    simulation_result_list.append(simulation_result)

                    profiler = None
                    if args.download_logs:
                        simulation_executor.event_handler.download_log_file()
                    if args.profile:
                        root_log_path = simulation_executor.event_handler.download_log_file()
                        profiler = Profiler(root_log_folder_path=root_log_path)
                        profiler.profile(ProfileType.EXECUTE, export=False)

                    simulation_evaluator.export_txt(simulation_result=simulation_result, profiler=profiler, label=label, args=args)
                    simulation_evaluator.export_csv(simulation_result=simulation_result, profiler=profiler, label=label, args=args)

                    simulation_executor.event_handler.wrapup()

                    del simulation_executor
                    del simulation_evaluator

        return simulation_result_list
