from simulation_framework.core.elements import *
from simulation_framework.core.event_handler import *
from simulation_framework.core.config import *


class SoPSimulatorExecutor:

    def __init__(self, simulation_file_path: str = None, mqtt_debug: bool = False, middleware_debug: bool = False, args: dict = None) -> None:
        self.simulation_file_path = simulation_file_path

        self.simulation_event_timeline: List[SoPEvent] = []
        self.simulation_env: SoPMiddlewareElement = None

        self.event_handler: SoPEventHandler = None

        self.event_log: List[SoPEvent] = []
        self.mqtt_debug = mqtt_debug
        self.middleware_debug = middleware_debug
        self.args = args

        self.send_thing_file_thread_queue = Queue()
        self.send_middleware_file_thread_queue = Queue()

        self.load_simulation(self.simulation_file_path)

    def load_simulation(self, simulation_folder_path: str):
        simulation_data = json_file_read(simulation_folder_path)
        self.simulation_config = simulation_data['config']
        self.simulation_env = SoPMiddlewareElement().load(
            simulation_data['component'])

        self.event_handler = SoPEventHandler(simulation_env=self.simulation_env,
                                             event_log=self.event_log,
                                             timeout=self.simulation_config['event_timeout'],
                                             mqtt_debug=self.mqtt_debug,
                                             middleware_debug=self.middleware_debug,
                                             running_time=self.simulation_config['running_time'],
                                             download_logs=self.args.download_logs)
        self.event_handler.update_middleware_thing_device_list()
        self.event_handler.init_ssh_client_list()
        self.event_handler.init_mqtt_client_list()
        self.event_handler.event_listener_start()

        self.generate_middleware_file(
            self.simulation_env)
        self.generate_thing_file(self.simulation_env)
        self.generate_scenario_file(self.simulation_env)

        self.simulation_event_timeline = [SoPEvent(event_type=SoPEventType.get(event['event_type']),
                                                   element=find_element_by_name_recursive(
            self.simulation_env, event['element'])[0],
            timestamp=event['timestamp'],
            duration=event['duration'],
            delay=event['delay'],
            middleware_element=event['middleware_element']) for event in simulation_data['event_timeline']]

    def build_middleware_thing_env(self):
        simulation_env_build_timeline = [event for event in self.simulation_event_timeline if event.event_type in [
            SoPEventType.MIDDLEWARE_RUN, SoPEventType.THING_RUN, SoPEventType.THING_REGISTER_WAIT, SoPEventType.DELAY]]
        last_index = [event.event_type for event in simulation_env_build_timeline].index(
            SoPEventType.DELAY)
        simulation_env_build_timeline = simulation_env_build_timeline[:last_index+1]

        for event in simulation_env_build_timeline:
            self.event_handler.event_trigger(event)

    def build_scenario_env(self):

        def task(middleware_scenario_add_timeline: List[SoPEvent]):
            for event in middleware_scenario_add_timeline:
                self.event_handler.event_trigger(event)

        whole_scenario_add_timeline = [
            event for event in self.simulation_event_timeline if event.event_type in [SoPEventType.SCENARIO_ADD, SoPEventType.SCENARIO_ADD_CHECK, SoPEventType.REFRESH, SoPEventType.DELAY]][1:]
        middleware_list: List[SoPMiddlewareElement] = get_middleware_list_recursive(
            self.simulation_env)

        middleware_scenario_add_timeline_list = []
        for middleware in middleware_list:
            scenario_add_timeline = [
                event for event in [event for event in whole_scenario_add_timeline if event.event_type == SoPEventType.SCENARIO_ADD] if find_element_recursive(self.simulation_env, event.element)[1].name == middleware.name]
            middleware_scenario_add_timeline_list.append(scenario_add_timeline)

        scenario_check_timeline_list = [event for event in whole_scenario_add_timeline if event.event_type in [
            SoPEventType.SCENARIO_ADD_CHECK, SoPEventType.REFRESH, SoPEventType.DELAY]]

        pool_map(task, middleware_scenario_add_timeline_list)

        for event in scenario_check_timeline_list:
            self.event_handler.event_trigger(event)

        return True

    def simulation_event_trigger_start(self):
        start_index = [event.event_type for event in self.simulation_event_timeline].index(
            SoPEventType.START)
        end_index = [event.event_type for event in self.simulation_event_timeline].index(
            SoPEventType.END)
        whole_simulation_timeline = self.simulation_event_timeline[start_index:end_index+1]
        for event in whole_simulation_timeline:
            self.event_handler.event_trigger(event)

    @exception_wrapper
    def start(self):
        self.event_handler.remove_all_remote_simulation_file()
        self.send_middleware_file(self.simulation_env)
        self.send_thing_file(self.simulation_env)
        self.event_handler.kill_all_simulation_instance()

        self.build_middleware_thing_env()
        self.build_scenario_env()
        self.simulation_event_trigger_start()

        return self.simulation_env, self.event_log, self.event_handler.simulation_duration, self.event_handler.simulation_start_time

    def generate_middleware_file(self, simulation_env: SoPMiddlewareElement):
        middleware_list: List[SoPMiddlewareElement] = get_middleware_list_recursive(
            simulation_env)
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

    def generate_thing_file(self, simulation_env: SoPMiddlewareElement):
        thing_list: List[SoPThingElement] = get_thing_list_recursive(
            simulation_env)

        for thing in thing_list:
            write_file(
                thing.thing_file_path, thing.thing_code())

    def generate_scenario_file(self, simulation_env: SoPMiddlewareElement):
        scenario_list: List[SoPScenarioElement] = get_scenario_list_recursive(
            simulation_env)
        for scenario in scenario_list:
            write_file(scenario.scenario_file_path,
                       scenario.scenario_code())

    def send_middleware_file(self, simulation_env: SoPMiddlewareElement):

        def ssh_task(middleware: SoPMiddlewareElement):
            ssh_client = self.event_handler.find_ssh_client(middleware)
            user = middleware.device.user
            ssh_client.send_command(
                f'mkdir -p {home_dir_append(middleware.remote_middleware_config_path, user)}')

            return True

        def send_task(middleware: SoPMiddlewareElement):
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

        middleware_list: List[SoPMiddlewareElement] = get_middleware_list_recursive(
            simulation_env)

        pool_map(ssh_task, middleware_list)
        pool_map(send_task, middleware_list, proc=1)

        return True

    def send_thing_file(self, simulation_env: SoPMiddlewareElement):

        def ssh_task(thing: SoPThingElement):
            ssh_client = self.event_handler.find_ssh_client(thing)
            user = thing.device.user
            ssh_client.send_command(
                f'mkdir -p {home_dir_append(os.path.dirname(thing.remote_thing_file_path), user)}')

            return True

        def send_task(thing: SoPThingElement):
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

        thing_list: List[SoPThingElement] = get_thing_list_recursive(
            simulation_env)

        pool_map(ssh_task, thing_list)
        pool_map(send_task, thing_list, proc=1)

        return True


if __name__ == '__main__':
    pass
