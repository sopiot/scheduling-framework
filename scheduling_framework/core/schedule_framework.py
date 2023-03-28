from scheduling_framework.core.simulation_executor import *
from scheduling_framework.core.simulation_generator import *
from scheduling_framework.core.simulation_evaluator import *


class SoPSchedulingFramework:

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
            self.simulation_generator = SoPSimulationGenerator(
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

    def update_middleware_thing(self, simulation_executor: SoPSimulatorExecutor,
                                middleware_path: str = '~/middleware',
                                policy_file_path: str = ''):

        def task(middleware: SoPMiddlewareElement):
            ssh_client = simulation_executor.event_handler.find_ssh_client(
                middleware)
            remote_home_dir = ssh_client.send_command('cd ~ && pwd')[0]
            user = os.path.basename(remote_home_dir)
            ssh_client.send_command('sudo apt install lsb-release -y')
            result = ssh_client.send_command('echo $?')
            if int(result[0]):
                raise Exception(
                    f'Install lsb-release failed to {middleware.name}')
            remote_device_os = ssh_client.send_command(
                'lsb_release -a')[1].split('\t')[1].strip()

            ssh_client.send_command('pidof sopiot_middleware | xargs kill -9')
            if not middleware.binary_sended:
                result = ssh_client.send_command(
                    f'rm -rf {home_dir_append(middleware_path, user)}')
                result = ssh_client.send_dir(
                    f'{get_project_root()}/schedule_algorithm', home_dir_append(middleware_path, user))
                if 'Ubuntu 20.04' in remote_device_os:
                    result = ssh_client.send_file(
                        f'{get_project_root()}/bin/sopiot_middleware_ubuntu2004_x64', f'{home_dir_append(middleware_path, user)}/sopiot_middleware')
                elif 'Ubuntu 22.04' in remote_device_os:
                    result = ssh_client.send_file(
                        f'{get_project_root()}/bin/sopiot_middleware_ubuntu2204_x64', f'{home_dir_append(middleware_path, user)}/sopiot_middleware')
                elif 'Raspbian' in remote_device_os:
                    result = ssh_client.send_file(
                        f'{get_project_root()}/bin/sopiot_middleware_pi_x86', f'{home_dir_append(middleware_path, user)}/sopiot_middleware')
                middleware.binary_sended = True

            ssh_client.send_file(
                policy_file_path, f'{home_dir_append(middleware_path, user)}/my_schedule_policy.cc')
            middleware_update_result = ssh_client.send_command(
                f'cd {home_dir_append(middleware_path, user)}; chmod +x sopiot_middleware;cmake .; make -j; echo $?')[-1]

            if not int(middleware_update_result[0]):
                SOPTEST_LOG_DEBUG(
                    f'device {middleware.device.name} middleware {middleware.name} update result: True', SoPTestLogLevel.INFO)
            else:
                raise Exception(
                    f'device {middleware.device.name} middleware {middleware.name} update result: False')

            # TODO: not tested yet
            randisk_check_command = f'ls /mnt/ramdisk'
            ssh_client.send_command(randisk_check_command)
            randisk_check_result = ssh_client.send_command('echo $?')
            if int(randisk_check_result[0]):
                ramdisk_generate_command_list = [f'sudo mkdir -p /mnt/ramdisk',
                                                 f'sudo mount -t tmpfs -o size=200M tmpfs /mnt/ramdisk',
                                                 f'echo "none /mnt/ramdisk tmpfs defaults,size=200M 0 0" | sudo tee -a /etc/fstab > /dev/null',
                                                 f'sudo chmod 777 /mnt/ramdisk']
                for ramdisk_generate_command in ramdisk_generate_command_list:
                    ssh_client.send_command(ramdisk_generate_command)

            if any([thing.is_super for thing in middleware.thing_list]):
                remote_home_dir = ssh_client.send_command('cd ~ && pwd')[0]
                thing_install_command = f'pip install big-thing-py'
                ssh_client.send_command(thing_install_command)

        middleware_list: List[SoPMiddlewareElement] = get_middleware_list_recursive(
            simulation_executor.simulation_env)

        pool_map(task, middleware_list, proc=1)

        return True

    def print_ranking(self, raw_simulation_result_list: List[SoPSimulationResult]):
        if not raw_simulation_result_list:
            SOPTEST_LOG_DEBUG(f'No simulation result', SoPTestLogLevel.WARN)
            return False

        simulation_result_list_sort_by_policy: Dict[str, List[SoPSimulationResult]] = {
        }
        for simualtion_result in raw_simulation_result_list:
            if simualtion_result.policy in simulation_result_list_sort_by_policy:
                simulation_result_list_sort_by_policy[simualtion_result.policy].append(
                    simualtion_result)
            else:
                simulation_result_list_sort_by_policy[simualtion_result.policy] = [
                    simualtion_result]
        simulation_result_list: List[SoPSimulationResult] = []
        for policy, result_list in simulation_result_list_sort_by_policy.items():
            simulation_result_avg = SoPSimulationResult(policy=policy,
                                                        avg_latency=avg(
                                                            [result.total_execute_time / result.total_scenario_cycle_num for result in result_list]),
                                                        avg_energy=avg(
                                                            [result.get_avg_energy()[0] for result in result_list]),
                                                        avg_success_ratio=avg([result.get_avg_success_ratio()[0] for result in result_list]))
            simulation_result_list.append(simulation_result_avg)

        simulation_result_list_sort_by_application_latency = sorted(
            simulation_result_list, key=lambda x: x.avg_latency)
        simulation_result_list_sort_by_application_energy = sorted(
            simulation_result_list, key=lambda x: x.avg_energy)
        simulation_result_list_sort_by_success_ratio = sorted(
            simulation_result_list, key=lambda x: x.avg_success_ratio, reverse=True)

        # TODO: policy에 대한 랭킹으로만 나와야한다. 같은 config결과는 평균을 내든지 해야한다.
        rank_header = ['Rank', 'QoS', 'Energy Saving', 'Stablity']
        print_table([[i+1,
                      f'''latency: {simulation_result_list_sort_by_application_latency[i].avg_latency}
policy: {simulation_result_list_sort_by_application_latency[i].policy}''',
                      f'''energy: {simulation_result_list_sort_by_application_energy[i].avg_energy}
policy: {simulation_result_list_sort_by_application_latency[i].policy}''',
                      f'''success_ratio: {f'{simulation_result_list_sort_by_success_ratio[i].avg_success_ratio * 100:.2f}'}
policy: {simulation_result_list_sort_by_application_latency[i].policy}'''] for i in range(len(simulation_result_list))], rank_header)

        return True

    def generate_simulation(self, policy_file_path_list: List[str] = [], args=None):
        simulation_ID = None
        simulation_info_list = []

        for config_path in self.config_path_list:
            if 'paper_experiments' in config_path:
                device_pool_path = SoPPath(root_path=get_project_root(),
                                           config_path=config_path,
                                           path=load_yaml(config_path)['device_pool_path'])
                device_list = load_yaml(device_pool_path.abs_path())
                if len(device_list) < 11:
                    raise Exception(
                        f'device pool is not enough for paper experiments. (more than 11 devices required)')

            simulation_file_path, simulation_ID = self.simulation_generator.generate_simulation(simulation_ID=simulation_ID,
                                                                                                config_path=config_path,
                                                                                                is_parallel=args.is_parallel)
            simulation_info = dict(simulation_file_path=simulation_file_path,
                                   config_path=config_path,
                                   policy_file_path=[],
                                   label=[])
            for policy_file_path in policy_file_path_list:
                simulation_info['policy_file_path'].append(
                    policy_file_path)
                simulation_info['label'].append(
                    f'{self.simulation_generator.simulation_config.name}_policy_{os.path.basename(policy_file_path).split(".")[0]}')
            simulation_info_list.append(simulation_info)
        return simulation_info_list

    def run_simulation(self, simulation_info_list: List[dict], policy_file_path_list: List[str] = [], args=None):
        # FIXME: simulation file을 직접 명세하여 시뮬레이션을 진행하는 경우 config 파일 위치를 알 수 없어 에러 발생.
        # 이 부분 수정할 것
        simulation_result_list: List[SoPSimulationResult] = []

        if self.simulation_file_path:
            simulation_executor = SoPSimulatorExecutor(simulation_file_path=self.simulation_file_path,
                                                       mqtt_debug=self.mqtt_debug,
                                                       middleware_debug=self.middleware_debug,
                                                       args=args)

            for policy_file_path in policy_file_path_list:
                label = f'simulation_file_{self.simulation_file_path}_policy_{os.path.basename(policy_file_path).split(".")[0]}'
                SOPTEST_LOG_DEBUG(
                    f'==== Start simulation {label} ====', SoPTestLogLevel.INFO)

                self.update_middleware_thing(
                    simulation_executor=simulation_executor,
                    middleware_path='~/middleware',
                    policy_file_path=policy_file_path)

                try:
                    simulation_env, event_log, simulation_duration, simulation_start_time = simulation_executor.start()
                except Exception as e:
                    print_error(e)
                    continue

                simulation_evaluator = SoPSimulationEvaluator(
                    simulation_env, event_log, simulation_duration, simulation_start_time)
                simulation_result = simulation_evaluator.evaluate_simulation()
                simulation_result.config = self.simulation_generator.simulation_config.name
                simulation_result.policy = os.path.basename(
                    policy_file_path).split(".")[0]
                simulation_result_list.append(simulation_result)

                simulation_evaluator.export_txt(
                    simulation_result=simulation_result, label=label, args=args)
                simulation_evaluator.export_csv(
                    simulation_result=simulation_result, label=label, args=args)

                if args.download_logs:
                    simulation_executor.event_handler.download_log_file()
                simulation_executor.event_handler.wrapup()

                del simulation_executor
                del simulation_evaluator
        else:
            for simulation_info in simulation_info_list:
                for label, policy_file_path in zip(simulation_info['label'], simulation_info['policy_file_path']):
                    SOPTEST_LOG_DEBUG(
                        f'==== Start simulation {label} ====', SoPTestLogLevel.INFO)

                    simulation_file_path = simulation_info['simulation_file_path']
                    args.config_path = simulation_info['config_path']

                    simulation_executor = SoPSimulatorExecutor(
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
                        SOPTEST_LOG_DEBUG(
                            f'==== Simulation {label} Canceled by user ====', SoPTestLogLevel.WARN)
                        continue

                    simulation_evaluator = SoPSimulationEvaluator(
                        simulation_env, event_log, simulation_duration, simulation_start_time)
                    simulation_result = simulation_evaluator.evaluate_simulation()
                    simulation_result.config = os.path.basename(
                        self.simulation_generator.simulation_config.config_path).split('.')[0]
                    simulation_result.policy = os.path.basename(
                        policy_file_path).split('.')[0]
                    simulation_result_list.append(simulation_result)

                    simulation_evaluator.export_txt(
                        simulation_result=simulation_result, label=label, args=args)
                    simulation_evaluator.export_csv(
                        simulation_result=simulation_result, label=label, args=args)

                    if args.download_logs:
                        simulation_executor.event_handler.download_log_file()
                    simulation_executor.event_handler.wrapup()

                    del simulation_executor
                    del simulation_evaluator

        return simulation_result_list
