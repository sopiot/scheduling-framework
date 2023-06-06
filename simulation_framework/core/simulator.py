from simulation_framework.core.event_handler import *


def exception_wrapper(func: Callable = None,
                      empty_case_func: Callable = None,
                      key_error_case_func: Callable = None,
                      else_case_func: Callable = None,
                      final_case_func: Callable = None,):
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Empty as e:
            print_error(e)
            if empty_case_func:
                return empty_case_func()
        except KeyError as e:
            print_error(e)
            if key_error_case_func:
                return key_error_case_func()
        except KeyboardInterrupt as e:
            print('KeyboardInterrupt')
            if self.__class__.__name__ == 'SoPSimulatorExecutor':
                event_handler: SoPEventHandler = self.event_handler
                event_handler.kill_every_process()
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
                print_error(e)
                if empty_case_func:
                    return empty_case_func()
            elif e in [ValueError, IndexError, TypeError, KeyError]:
                print_error(e)
            else:
                print_error(e)
                event_handler: SoPEventHandler = self.event_handler
                event_handler.kill_every_process()
            print_error(e)
            raise e
        finally:
            if final_case_func:
                final_case_func()
    return wrapper


class SoPSimulator:

    def __init__(self, simulation_env: SoPSimulationEnv, mqtt_debug: bool = False, middleware_debug: bool = False, download_logs: bool = False) -> None:
        self.simulation_config: SoPSimulationConfig
        self.simulation_data: SoPSimulationEnv
        self.simulation_env: SoPMiddleware
        self.simulation_event_timeline: List[SoPEvent]

        self.event_handler: SoPEventHandler = None
        self.event_log: List[SoPEvent] = []

        self.mqtt_debug = mqtt_debug
        self.middleware_debug = middleware_debug
        self.download_logs = download_logs

        self.send_thing_file_thread_queue = Queue()
        self.send_middleware_file_thread_queue = Queue()

    def setup(self, config: SoPSimulationConfig, simulation_env: SoPSimulationEnv):
        self.simulation_config = config
        self.root_middleware = simulation_env.root_middleware
        self.event_timeline = [SoPEvent(event_type=SoPEventType.get(event['event_type']),
                                        component=find_component_by_name(self.simulation_env, event['component'])[0],
                                        timestamp=event['timestamp'],
                                        duration=event['duration'],
                                        delay=event['delay'],
                                        middleware_component=event['middleware_component'])
                               for event in simulation_env.event_timeline]
        self.event_handler = SoPEventHandler(root_middleware=self.root_middleware,
                                             event_log=self.event_log,
                                             timeout=self.simulation_config['event_timeout'],
                                             running_time=self.simulation_config['running_time'],
                                             download_logs=self.download_logs,
                                             mqtt_debug=self.mqtt_debug,
                                             middleware_debug=self.middleware_debug)
        self.event_handler.update_middleware_thing_device_list()
        self.event_handler.init_ssh_client_list()
        self.event_handler.init_mqtt_client_list()
        self.event_handler.start_event_listener()

        self.generate_middleware_configs(self.simulation_env)
        self.generate_thing_codes(self.simulation_env)
        self.generate_scenario_codes(self.simulation_env)

        # add send component file

    def trigger_static_events(self):
        """Trigger events that are triggered before the simulation starts
        """
        simulation_env_build_timeline = [event for event in self.simulation_event_timeline if event.event_type in [
            SoPEventType.MIDDLEWARE_RUN, SoPEventType.THING_RUN, SoPEventType.THING_REGISTER_WAIT, SoPEventType.DELAY]]
        last_index = [event.event_type for event in simulation_env_build_timeline].index(
            SoPEventType.DELAY)
        simulation_env_build_timeline = simulation_env_build_timeline[:last_index+1]

        for event in simulation_env_build_timeline:
            self.event_handler.event_trigger(event)

        self.trigger_scenario_addition_events()

    def trigger_scenario_addition_events(self):

        def task(middleware_scenario_add_timeline: List[SoPEvent]):
            for event in middleware_scenario_add_timeline:
                self.event_handler.event_trigger(event)

        whole_scenario_add_timeline = [
            event for event in self.simulation_event_timeline if event.event_type in [SoPEventType.SCENARIO_ADD, SoPEventType.SCENARIO_ADD_CHECK, SoPEventType.REFRESH, SoPEventType.DELAY]][1:]
        middleware_list: List[SoPMiddleware] = get_whole_middleware_list(self.simulation_env)

        middleware_scenario_add_timeline_list = []
        for middleware in middleware_list:
            scenario_add_timeline = [
                event for event in [event for event in whole_scenario_add_timeline if event.event_type == SoPEventType.SCENARIO_ADD] if find_component(self.simulation_env, event.component)[1].name == middleware.name]
            middleware_scenario_add_timeline_list.append(scenario_add_timeline)

        scenario_check_timeline_list = [event for event in whole_scenario_add_timeline if event.event_type in [
            SoPEventType.SCENARIO_ADD_CHECK, SoPEventType.REFRESH, SoPEventType.DELAY]]

        pool_map(task, middleware_scenario_add_timeline_list)

        for event in scenario_check_timeline_list:
            self.event_handler.event_trigger(event)

        return True

    def trigger_dynamic_events(self):
        """Trigger events that are triggered in the simulation
        """
        start_index = [event.event_type for event in self.simulation_event_timeline].index(SoPEventType.START)
        end_index = [event.event_type for event in self.simulation_event_timeline].index(SoPEventType.END)
        whole_simulation_timeline = self.simulation_event_timeline[start_index:end_index+1]
        for event in whole_simulation_timeline:
            self.event_handler.event_trigger(event)

    @exception_wrapper
    def start(self):
        # self.cleanup
        self.event_handler.remove_all_remote_simulation_file()
        self.event_handler.kill_every_process()

        # self.build_iot_system
        self.send_middleware_configs(self.simulation_env)
        self.send_thing_codes(self.simulation_env)

        self.trigger_static_events()
        self.trigger_dynamic_events()

        return self.simulation_env, self.event_log, self.event_handler.simulation_duration, self.event_handler.simulation_start_time

    def generate_middleware_configs(self, simulation_env: SoPSimulationEnv):
        """middleware init files consist of three files: 
            middleware.cfg: fgf
            mosquitto.conf: fgf
            init.sh: fg 

        Args:
            simulation_env (SoPMiddlewareComponent): _description_
        """
        middleware_list: List[SoPMiddleware] = get_whole_middleware_list(simulation_env)
        for middleware in middleware_list:
            ssh_client = self.event_handler.find_ssh_client(middleware)
            remote_home_dir = ssh_client.send_command('cd ~ && pwd')[0]
            middleware.middleware_cfg_file(
                self.simulation_env, remote_home_dir)
            middleware.mosquitto_conf_file()
            middleware.init_script_file(remote_home_dir)

            middleware.middleware_cfg_file_path = f'{os.path.dirname(self.simulation_file_path)}/middleware_config/{middleware.name}_middleware.cfg'
            middleware.mosquitto_conf_file_path = f'{os.path.dirname(self.simulation_file_path)}/middleware_config/{middleware.name}_mosquitto.conf'
            middleware.init_script_file_path = f'{os.path.dirname(self.simulation_file_path)}/middleware_config/{middleware.name}_init.sh'
            middleware.remote_middleware_cfg_file_path = f'{middleware.remote_middleware_config_path}/{middleware.name}_middleware.cfg'
            middleware.remote_mosquitto_conf_file_path = f'{middleware.remote_middleware_config_path}/{middleware.name}_mosquitto.conf'
            middleware.remote_init_script_file_path = f'{middleware.remote_middleware_config_path}/{middleware.name}_init.sh'
            write_file(middleware.middleware_cfg_file_path,
                       middleware.middleware_cfg)
            write_file(middleware.mosquitto_conf_file_path,
                       middleware.mosquitto_conf)
            write_file(middleware.init_script_file_path,
                       middleware.init_script)

    def generate_thing_codes(self, simulation_env: SoPMiddleware):
        thing_list: List[SoPThing] = get_whole_thing_list(simulation_env)

        for thing in thing_list:
            write_file(thing.thing_file_path, thing.thing_code())

    def generate_scenario_codes(self, simulation_env: SoPMiddleware):
        scenario_list: List[SoPScenario] = get_whole_scenario_list(
            simulation_env)
        for scenario in scenario_list:
            write_file(scenario.scenario_file_path,
                       scenario.scenario_code())

    def send_middleware_configs(self, simulation_env: SoPMiddleware):

        def ssh_task(middleware: SoPMiddleware):
            ssh_client = self.event_handler.find_ssh_client(middleware)
            user = middleware.device.user
            ssh_client.send_command(
                f'mkdir -p {home_dir_append(middleware.remote_middleware_config_path, user)}')

            return True

        def send_task(middleware: SoPMiddleware):
            ssh_client = self.event_handler.find_ssh_client(middleware)
            user = middleware.device.user
            ssh_client.send_command(
                f'mkdir -p {home_dir_append(middleware.remote_middleware_config_path, user)}')
            ssh_client.send_file(
                os.path.abspath(middleware.middleware_cfg_file_path), home_dir_append(middleware.remote_middleware_cfg_file_path, user))
            ssh_client.send_file(
                os.path.abspath(middleware.mosquitto_conf_file_path), home_dir_append(middleware.remote_mosquitto_conf_file_path, user))
            ssh_client.send_file(
                os.path.abspath(middleware.init_script_file_path), home_dir_append(middleware.remote_init_script_file_path, user))
            SOPTEST_LOG_DEBUG(
                f'Send middleware config folder {middleware.name}', SoPTestLogLevel.PASS)

            return True

        middleware_list: List[SoPMiddleware] = get_whole_middleware_list(
            simulation_env)

        pool_map(ssh_task, middleware_list)
        pool_map(send_task, middleware_list, proc=1)

        return True

    def send_thing_codes(self, simulation_env: SoPMiddleware):

        def ssh_task(thing: SoPThing):
            ssh_client = self.event_handler.find_ssh_client(thing)
            user = thing.device.user
            ssh_client.send_command(
                f'mkdir -p {home_dir_append(os.path.dirname(thing.remote_thing_file_path), user)}')

            return True

        def send_task(thing: SoPThing):
            ssh_client = self.event_handler.find_ssh_client(thing)
            user = thing.device.user
            ssh_client.send_command(
                f'mkdir -p {home_dir_append(os.path.dirname(thing.remote_thing_file_path), user)}')
            try:
                ssh_client.send_file(
                    os.path.abspath(thing.thing_file_path), home_dir_append(thing.remote_thing_file_path, thing.device.user))
            except OSError:
                os.system(
                    f'sshpass -p "{ssh_client.device.password}" scp -o StrictHostKeyChecking=no -P {ssh_client.device.ssh_port} {os.path.abspath(thing.thing_file_path)} {ssh_client.device.user}@{ssh_client.device.host}:{thing.remote_thing_file_path} > /dev/null 2>&1 &')

            SOPTEST_LOG_DEBUG(
                f'Send thing file {os.path.basename(thing.thing_file_path)}', SoPTestLogLevel.PASS)

            return True

        thing_list: List[SoPThing] = get_whole_thing_list(
            simulation_env)

        pool_map(ssh_task, thing_list)
        pool_map(send_task, thing_list, proc=1)

        return True


if __name__ == '__main__':
    pass
