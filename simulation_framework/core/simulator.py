from simulation_framework.core.event_handler import *

PREDEFINED_POLICY_FILE_NAME = 'my_scheduling_policies.cc'
SCHEDULING_ALGORITHM_PATH = f'{get_project_root()}/scheduling_algorithm'


def exception_wrapper(func: Callable = None,
                      empty_case_func: Callable = None,
                      key_error_case_func: Callable = None,
                      else_case_func: Callable = None,
                      final_case_func: Callable = None,):
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Empty as e:
            print_error()
            if empty_case_func:
                return empty_case_func()
        except KeyError as e:
            print_error()
            if key_error_case_func:
                return key_error_case_func()
        except KeyboardInterrupt as e:
            print('KeyboardInterrupt')
            if hasattr(self._simulator, 'event_handler'):
                event_handler: SoPEventHandler = self._simulator.event_handler
                event_handler.wrapup()
                user_input = input(
                    'Select exit mode[1].\n1. Just exit\n2. Download remote logs\n') or '1'
                if user_input == '1':
                    cprint(f'Exit whole simulation...', 'red')
                elif user_input == '2':
                    cprint(f'Download remote logs...', 'yellow')
                    event_handler.download_log_file()
                else:
                    cprint(f'Unknown input. Exit whole simulation...', 'red')
                exit(0)
        except Exception as e:
            if e is Empty:
                print_error()
                if empty_case_func:
                    return empty_case_func()
            elif e in [ValueError, IndexError, TypeError, KeyError]:
                print_error()
            else:
                print_error()
                event_handler: SoPEventHandler = self._simulator.event_handler
                event_handler.wrapup()
            print_error()
            raise e
        finally:
            if final_case_func:
                final_case_func()
    return wrapper


class SoPSimulator:

    def __init__(self, simulation_env: SoPSimulationEnv, policy_path: str, mqtt_debug: bool = False, middleware_debug: bool = False, download_logs: bool = False) -> None:
        self.simulation_env = simulation_env
        self.policy_path = policy_path
        self.static_event_timeline: List[SoPEvent] = simulation_env.static_event_timeline
        self.dynamic_event_timeline: List[SoPEvent] = simulation_env.dynamic_event_timeline

        self.event_handler: SoPEventHandler = None

        self.mqtt_debug = mqtt_debug
        self.middleware_debug = middleware_debug
        self.download_logs = download_logs

        self.send_thing_file_thread_queue = Queue()
        self.send_middleware_file_thread_queue = Queue()

    def setup(self):
        self.event_handler = SoPEventHandler(root_middleware=self.simulation_env.root_middleware,
                                             timeout=self.simulation_env.config.event_timeout,
                                             running_time=self.simulation_env.config.running_time,
                                             download_logs=self.download_logs,
                                             mqtt_debug=self.mqtt_debug,
                                             middleware_debug=self.middleware_debug)
        self.event_handler.remove_duplicated_device_instance()
        self.event_handler.init_ssh_client_list()
        self.event_handler.init_mqtt_client_list()
        self.event_handler.start_event_listener()

        # self._generate_middleware_configs(self.simulation_env.root_middleware, simulation_data_file_path=self.simulation_env.simulation_data_file_path)
        # self._generate_thing_codes(self.simulation_env.root_middleware)
        # self._generate_scenario_codes(self.simulation_env.root_middleware)

    def cleanup(self):
        self.event_handler.remove_all_remote_simulation_file()
        self.event_handler.kill_every_process()

    def build_iot_system(self):
        self._send_middleware_configs()
        self._send_thing_codes()
        self._update_middleware_thing()

    def _update_middleware_thing(self):

        def get_remote_device_OS(ssh_client: SoPSSHClient) -> str:
            if not ssh_client.send_command_with_check_success('command -v lsb_release', get_pty=True):
                command = 'sudo apt install lsb-release -y;'
                if not ssh_client.send_command_with_check_success(command, get_pty=True):
                    raise SSHCommandFailError(command=command, reason=f'Install lsb-release failed to {ssh_client.device.name}')

            remote_device_os = ssh_client.send_command('lsb_release -a')[1].split('\t')[1].strip()
            return remote_device_os

        def install_remote_middleware(ssh_client: SoPSSHClient, user: str):
            remote_device_os = get_remote_device_OS(ssh_client)
            ssh_client.send_command('pidof sopiot_middleware | xargs kill -9')
            remote_middleware_path = self.simulation_env.config.middleware_config.remote_middleware_path
            # zip_file_path = zip_directory(remote_middleware_path, './middleware.zip')
            ssh_client.send_dir(SCHEDULING_ALGORITHM_PATH, home_dir_append(remote_middleware_path, user))
            if 'Ubuntu 20.04' in remote_device_os:
                # add_files_to_zip(zip_file_path, [f'{get_project_root()}/bin/sopiot_middleware_ubuntu2004_x64'])
                ssh_client.send_file(f'{get_project_root()}/bin/sopiot_middleware_ubuntu2004_x64',
                                     f'{home_dir_append(remote_middleware_path, user)}/sopiot_middleware')
            elif 'Ubuntu 22.04' in remote_device_os:
                ssh_client.send_file(f'{get_project_root()}/bin/sopiot_middleware_ubuntu2204_x64',
                                     f'{home_dir_append(remote_middleware_path, user)}/sopiot_middleware')
            elif 'Raspbian' in remote_device_os:
                ssh_client.send_file(f'{get_project_root()}/bin/sopiot_middleware_pi_x86',
                                     f'{home_dir_append(remote_middleware_path, user)}/sopiot_middleware')
            ssh_client.send_file(self.policy_path, f'{home_dir_append(remote_middleware_path, user)}/{PREDEFINED_POLICY_FILE_NAME}')
            middleware_update_command = (f'cd {home_dir_append(remote_middleware_path, user)};'
                                         'chmod +x sopiot_middleware;'
                                         'cmake .;'
                                         'make -j')
            if not ssh_client.send_command_with_check_success(middleware_update_command):
                raise SSHCommandFailError(command=middleware_update_command, reason=f'Install middleware to {ssh_client.device.name} failed')

            return True

        def install_remote_thing(ssh_client: SoPSSHClient, force_install: bool = True):
            thing_install_command = f'pip install big-thing-py'

            if force_install:
                thing_install_command += ' --force-reinstall'
                if not ssh_client.send_command_with_check_success(thing_install_command):
                    raise SSHCommandFailError(command=thing_install_command, reason=f'Install big-thing-py failed to {ssh_client.device.name}')
            elif not ssh_client.send_command_with_check_success('pip list | grep big-thing-py'):
                if not ssh_client.send_command_with_check_success(thing_install_command):
                    raise SSHCommandFailError(command=thing_install_command, reason=f'Install big-thing-py failed to {ssh_client.device.name}')

            return True

        def init_ramdisk(ssh_client: SoPSSHClient) -> None:
            ramdisk_generate_command_list = [f'sudo mkdir -p /mnt/ramdisk',
                                             f'sudo mount -t tmpfs -o size=500M tmpfs /mnt/ramdisk',
                                             f'echo "none /mnt/ramdisk tmpfs defaults,size=200M 0 0" | sudo tee -a /etc/fstab > /dev/null',
                                             f'sudo chmod 777 /mnt/ramdisk']
            if not ssh_client.send_command_with_check_success('ls /mnt/ramdisk'):
                for ramdisk_generate_command in ramdisk_generate_command_list:
                    if not ssh_client.send_command_with_check_success(ramdisk_generate_command):
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
            if not ssh_client.send_command_with_check_success(set_clock_command):
                SOPTEST_LOG_DEBUG(f'Set cpu clock {ssh_client.device.name} failed!', SoPTestLogLevel.FAIL)

        with Progress() as progress:
            def task(ssh_client: SoPSSHClient):
                user = ssh_client.device.user
                install_remote_middleware(ssh_client=ssh_client, user=user)
                install_remote_thing(ssh_client=ssh_client, force_install=True)
                init_ramdisk(ssh_client=ssh_client)

                remote_device_os = get_remote_device_OS(ssh_client=ssh_client)
                if 'Raspbian' in remote_device_os and ssh_client.device.name != 'localhost':
                    set_cpu_clock_remote(ssh_client=ssh_client)

                progress.update(task1, advance=1)

            middleware_list: List[SoPMiddleware] = get_whole_middleware_list(self.simulation_env.root_middleware)
            middleware_ssh_client_list = list(set([self.event_handler.find_ssh_client(middleware) for middleware in middleware_list]))
            thing_ssh_client_list = list(set([self.event_handler.find_ssh_client(thing) for middleware in middleware_list for thing in middleware.thing_list]))

            ssh_client_list = list(set(middleware_ssh_client_list + thing_ssh_client_list))
            task1 = progress.add_task("Install middleware & thing", total=len(ssh_client_list))
            pool_map(task, ssh_client_list)

        return True

    def _trigger_static_events(self) -> None:
        for event in self.static_event_timeline:
            self.event_handler.event_trigger(event)

    def _trigger_dynamic_events(self) -> None:
        for event in self.dynamic_event_timeline:
            self.event_handler.event_trigger(event)

    def start(self) -> None:
        self._trigger_static_events()
        self._trigger_dynamic_events()

    def _generate_middleware_configs(self, root_middleware: SoPMiddleware, simulation_data_file_path: str):
        middleware_list: List[SoPMiddleware] = get_whole_middleware_list(root_middleware)
        for middleware in middleware_list:
            remote_home_dir = f'/home/{middleware.device.user}'

            middleware_cfg = middleware.generate_middleware_cfg_file(remote_home_dir)
            mosquitto_conf = middleware.generate_mosquitto_conf_file()
            init_script = middleware.generate_init_script_file(remote_home_dir)

            middleware_cfg_file_path = f'{os.path.dirname(simulation_data_file_path)}/middleware_config/{middleware.name}_middleware.cfg'
            mosquitto_conf_file_path = f'{os.path.dirname(simulation_data_file_path)}/middleware_config/{middleware.name}_mosquitto.conf'
            init_script_file_path = f'{os.path.dirname(simulation_data_file_path)}/middleware_config/{middleware.name}_init.sh'

            write_file(middleware_cfg_file_path, middleware_cfg)
            write_file(mosquitto_conf_file_path, mosquitto_conf)
            write_file(init_script_file_path, init_script)

    def _generate_thing_codes(self, root_middleware: SoPMiddleware):
        thing_list: List[SoPThing] = get_whole_thing_list(root_middleware)

        for thing in thing_list:
            write_file(thing.thing_file_path, thing.thing_code())

    def _generate_scenario_codes(self, root_middleware: SoPMiddleware):
        scenario_list: List[SoPScenario] = get_whole_scenario_list(root_middleware)
        for scenario in scenario_list:
            write_file(scenario.scenario_file_path, scenario.scenario_code())

    def _send_middleware_configs(self):

        with Progress() as progress:
            def task(middleware: SoPMiddleware):
                ssh_client = self.event_handler.find_ssh_client(middleware)
                user = middleware.device.user
                simulation_data_file_path = self.simulation_env.simulation_data_file_path

                middleware_cfg = middleware.generate_middleware_cfg_file(user)
                mosquitto_conf = middleware.generate_mosquitto_conf_file()
                init_script = middleware.generate_init_script_file(user)

                middleware_cfg_file_path = f'{os.path.dirname(simulation_data_file_path)}/middleware_config/{middleware.name}_middleware.cfg'
                mosquitto_conf_file_path = f'{os.path.dirname(simulation_data_file_path)}/middleware_config/{middleware.name}_mosquitto.conf'
                init_script_file_path = f'{os.path.dirname(simulation_data_file_path)}/middleware_config/{middleware.name}_init.sh'
                remote_middleware_cfg_file_path = f'{middleware.remote_middleware_config_path}/{middleware.name}_middleware.cfg'
                remote_mosquitto_conf_file_path = f'{middleware.remote_middleware_config_path}/{middleware.name}_mosquitto.conf'
                remote_init_script_file_path = f'{middleware.remote_middleware_config_path}/{middleware.name}_init.sh'
                write_file(middleware_cfg_file_path, middleware_cfg)
                write_file(mosquitto_conf_file_path, mosquitto_conf)
                write_file(init_script_file_path, init_script)

                middleware.middleware_cfg = middleware_cfg

                ssh_client.send_command(f'mkdir -p {home_dir_append(middleware.remote_middleware_config_path, user)}')
                ssh_client.send_file(os.path.abspath(middleware_cfg_file_path), home_dir_append(remote_middleware_cfg_file_path, user))
                ssh_client.send_file(os.path.abspath(mosquitto_conf_file_path), home_dir_append(remote_mosquitto_conf_file_path, user))
                ssh_client.send_file(os.path.abspath(init_script_file_path), home_dir_append(remote_init_script_file_path, user))
                # SOPTEST_LOG_DEBUG(f'Send middleware config folder {middleware.name}', SoPTestLogLevel.PASS)

                progress.update(task1, advance=1)
                return True

            middleware_list: List[SoPMiddleware] = get_whole_middleware_list(self.simulation_env.root_middleware)
            task1 = progress.add_task("Send middleware configs...", total=len(middleware_list))
            pool_map(task, middleware_list, proc=1)

        return True

    def _send_thing_codes(self):

        with Progress() as progress:
            def send_task(thing: SoPThing):
                ssh_client = self.event_handler.find_ssh_client(thing)
                user = thing.device.user
                try:
                    write_file(thing.thing_file_path, thing.thing_code())
                    ssh_client.send_file(os.path.abspath(thing.thing_file_path), home_dir_append(thing.remote_thing_file_path, user))
                except OSError:
                    os.system(f'sshpass -p "{ssh_client.device.password}" scp -o StrictHostKeyChecking=no -P {ssh_client.device.ssh_port} '
                              f'{os.path.abspath(thing.thing_file_path)} {ssh_client.device.user}@{ssh_client.device.host}:{thing.remote_thing_file_path} > /dev/null 2>&1 &')

                # SOPTEST_LOG_DEBUG(f'Send thing file {os.path.basename(thing.thing_file_path)}', SoPTestLogLevel.PASS)

                progress.update(task1, advance=1)
                return True

            thing_list: List[SoPThing] = get_whole_thing_list(self.simulation_env.root_middleware)
            task1 = progress.add_task("Send thing codes...", total=len(thing_list))
            pool_map(send_task, thing_list, proc=1)

        return True

    # =========================
    #         _    _  _
    #        | |  (_)| |
    #  _   _ | |_  _ | | ___
    # | | | || __|| || |/ __|
    # | |_| || |_ | || |\__ \
    #  \__,_| \__||_||_||___/
    # =========================

    # for load event_timeline from simulation data file
    def _load_event_timeline(simulation_env: SoPSimulationEnv, event_timeline: List[dict]) -> List[SoPEvent]:
        event_timeline: List[SoPEvent] = [SoPEvent(event_type=SoPEventType.get(event['event_type']),
                                                   component=find_component_by_name(simulation_env.root_middleware, event['component'])[0],
                                                   timestamp=event['timestamp'],
                                                   duration=event['duration'],
                                                   delay=event['delay'],
                                                   middleware_component=event['middleware_component'])
                                          for event in event_timeline]

        return event_timeline

    def get_event_log(self) -> List[SoPEvent]:
        return self.event_handler.event_log


if __name__ == '__main__':
    pass
