from simulation_framework.utils import *
from simulation_framework.logger import *

from string import Template
from queue import Queue
from abc import ABCMeta


def get_whole_middleware_list(middleware: 'SoPMiddleware') -> List['SoPMiddleware']:
    # middleware_list = [middleware]

    # for child_middleware in middleware.children:
    #     middleware_list.extend(get_middleware_list(child_middleware))

    # middleware_list = sorted(middleware_list, key=lambda x: x.level, reverse=True)
    # return middleware_list
    root_middleware = middleware.root

    middleware_list = [root_middleware] + list(root_middleware.descendants)
    return middleware_list


def get_whole_thing_list(middleware: 'SoPMiddleware' = None) -> List['SoPThing']:
    # return [middleware] + list(middleware.descendants)
    # thing_list = [thing for thing in middleware.thing_list]

    # for child_middleware in middleware.children:
    #     thing_list.extend(get_thing_list(child_middleware))

    # thing_list = sorted(thing_list, key=lambda x: x.level, reverse=True)
    # return thing_list
    root_middleware = middleware.root

    middleware_list = get_whole_middleware_list(root_middleware)
    thing_list = flatten_list([middleware.thing_list for middleware in middleware_list])
    return thing_list


def get_whole_scenario_list(middleware: 'SoPMiddleware' = None) -> List['SoPScenario']:
    # scenario_list = [scenario for scenario in middleware.scenario_list]

    # for child_middleware in middleware.children:
    #     scenario_list.extend(get_scenario_list(child_middleware))

    # scenario_list = sorted(scenario_list, key=lambda x: x.level, reverse=True)
    # return scenario_list
    root_middleware = middleware.root

    middleware_list = get_whole_middleware_list(root_middleware)
    scenario_list = flatten_list([middleware.scenario_list for middleware in middleware_list])
    return scenario_list


def find_component(middleware: 'SoPMiddleware', component: 'SoPComponent', key: Callable = lambda x: x) -> Tuple[object, object]:

    def find_component_recursive(middleware: 'SoPMiddleware', component: 'SoPComponent'):
        if key(middleware) == key(component):
            return middleware, None

        for thing in middleware.thing_list:
            if key(thing) == key(component):
                return thing, middleware
        for scenario in middleware.scenario_list:
            if key(scenario) == key(component):
                return scenario, middleware
        for child_middleware in middleware.children:
            if key(child_middleware) == key(component):
                return child_middleware, middleware

        for child_middleware in middleware.children:
            result = find_component_recursive(
                child_middleware, component)
            if result:
                return result[0], result[1]
            else:
                find_component_recursive(
                    child_middleware, component)

    result = find_component_recursive(middleware, component)
    if result:
        return result[0], result[1]
    else:
        return None, None


def find_component_by_name(middleware: 'SoPMiddleware', component_name: str):

    def find_component_by_name_recursive(middleware: 'SoPMiddleware', component_name: str):
        if middleware.name == component_name:
            return middleware, None

        for thing in middleware.thing_list:
            if thing.name == component_name:
                return thing, middleware
        for scenario in middleware.scenario_list:
            if scenario.name == component_name:
                return scenario, middleware
        for child_middleware in middleware.children:
            if child_middleware.name == component_name:
                return child_middleware, middleware

        for child_middleware in middleware.children:
            result = find_component_by_name_recursive(child_middleware, component_name)
            if result:
                return result[0], result[1]
            else:
                find_component_by_name_recursive(child_middleware, component_name)

    result = find_component_by_name_recursive(middleware, component_name)
    if result:
        return result[0], result[1]
    else:
        return None, None


class SoPComponentType(Enum):
    DEVICE = 'DEVICE'
    MIDDLEWARE = 'MIDDLEWARE'
    THING = 'THING'
    SERVICE = 'SERVICE'
    SCENARIO = 'SCENARIO'

    UNDEFINED = 'UNDEFINED'

    def __str__(self):
        return self.value

    @classmethod
    def get(cls, name: str):
        try:
            return cls[name.upper()]
        except Exception:
            return cls.UNDEFINED


class SoPComponentActionType(Enum):
    RUN = 'RUN'
    KILL = 'KILL'
    UNREGISTER = 'UNREGISTER'
    SCENARIO_VERIFY = 'SCENARIO_VERIFY'
    SCENARIO_ADD = 'SCENARIO_ADD'
    SCENARIO_RUN = 'SCENARIO_RUN'
    SCENARIO_STOP = 'SCENARIO_STOP'
    SCENARIO_UPDATE = 'SCENARIO_UPDATE'
    SCENARIO_DELETE = 'SCENARIO_DELETE'
    DELAY = 'DELAY'

    UNDEFINED = 'UNDEFINED'

    def __str__(self):
        return self.value

    @classmethod
    def get(cls, name: str):
        try:
            return cls[name.upper()]
        except Exception:
            return cls.UNDEFINED


class SoPScenarioState(Enum):
    CREATED = 'CREATED'
    SCHEDULING = 'SCHEDULING'
    INITIALIZED = 'INITIALIZED'
    RUNNING = 'RUNNING'
    EXECUTING = 'EXECUTING'
    STUCKED = 'STUCKED'
    COMPLETED = 'COMPLETED'

    UNDEFINED = 'UNDEFINED'

    def __str__(self):
        return self.value

    @classmethod
    def get(cls, name: str):
        try:
            return cls[name.upper()]
        except Exception:
            return cls.UNDEFINED


class SoPScenarioInfo:
    '''
        return dict(id=scenario_info['id'], 
        name=scenario_info['name'], 
        code=scenario_info['contents'],
        state=SoPScenarioStateType.get(scenario_info['state']), 
        schedule_info=scenario_info['scheduleInfo'])
    '''

    def __init__(self, id: int, name: str, code: str, state: SoPScenarioState, schedule_info: List[dict]) -> None:
        self.id = id
        self.name = name
        self.code = code
        self.state = state
        self.schedule_info = schedule_info


class SoPThingFaultType(Enum):
    NORMAL = 'NORMAL'
    FAIL = 'FAIL'
    TIMEOUT = 'TIMEOUT'
    SHUTDOWN = 'SHUTDOWN'

    UNDEFINED = 'UNDEFINED'

    def __str__(self):
        return self.value

    @classmethod
    def get(cls, name: str):
        try:
            return cls[name.upper()]
        except Exception:
            return cls.UNDEFINED


class SoPComponentScopeType(Enum):
    LOCAL = 'LOCAL'
    SUPER = 'SUPER'

    UNDEFINED = 'UNDEFINED'

    def __str__(self):
        return self.value

    @classmethod
    def get(cls, name: str):
        try:
            return cls[name.upper()]
        except Exception:
            return cls.UNDEFINED


class SoPComponent(metaclass=ABCMeta):

    def __init__(self, name: str, level: int, component_type: SoPComponentType) -> None:
        # basic info
        self.name = name
        self.level = level
        self.component_type = component_type

    def __getstate__(self):
        state = self.__dict__.copy()

        state['name'] = self.name
        state['level'] = self.level
        state['component_type'] = self.component_type

        return state

    def __setstate__(self, state):
        self.__dict__.update(state)

        self.name = state['name']
        self.level = state['level']
        self.component_type = state['component_type']

    @classmethod
    def load(cls, data: dict) -> 'SoPComponent':
        component = cls()
        component.name = data['name']
        component.level = data['level']
        component.component_type = SoPComponentType.get(data['component_type'])

        return component

    def dict(self) -> dict:
        return dict(name=self.name,
                    level=self.level,
                    component_type=self.component_type.value)


class SoPDevice(SoPComponent):
    def __init__(self, name: str = '', level: int = -1, component_type: SoPComponentType = SoPComponentType.DEVICE,
                 host: str = '', ssh_port: int = None, user: str = '', password: str = '',
                 mqtt_port: int = None,
                 mqtt_ssl_port: int = None,
                 websocket_port: int = None,
                 websocket_ssl_port: int = None,
                 localserver_port: int = 58132) -> None:
        super().__init__(name, level, component_type)

        self.host = host
        self.ssh_port = ssh_port
        self.user = user
        self.password = password

        self.mqtt_port = mqtt_port
        self.mqtt_ssl_port = mqtt_ssl_port
        self.websocket_port = websocket_port
        self.websocket_ssl_port = websocket_ssl_port
        self.localserver_port = localserver_port

        self.available_port_list: List[int] = []

    def __eq__(self, __o: object) -> bool:
        return self.host == __o.host and self.user == __o.user and self.ssh_port == __o.ssh_port and self.password == __o.password

    @classmethod
    def load(cls, data: dict) -> 'SoPDevice':
        device: SoPDevice = super().load(data=data)

        device.host = data['host']
        device.ssh_port = data['ssh_port']
        device.user = data['user']
        device.password = data['password']

        device.mqtt_port = data['mqtt_port']
        device.mqtt_ssl_port = data['mqtt_ssl_port']
        device.websocket_port = data['websocket_port']
        device.websocket_ssl_port = data['websocket_ssl_port']
        device.localserver_port = data['localserver_port']

        return device

    def dict(self):
        return dict(name=self.name,
                    level=self.level,
                    component_type=self.component_type.value,
                    host=self.host,
                    user=self.user,
                    ssh_port=self.ssh_port,
                    password=self.password,
                    mqtt_port=self.mqtt_port,
                    mqtt_ssl_port=self.mqtt_ssl_port,
                    websocket_port=self.websocket_port,
                    websocket_ssl_port=self.websocket_ssl_port,
                    localserver_port=self.localserver_port)


class SoPMiddleware(SoPComponent, NodeMixin):

    CFG_TEMPLATE = '''%s
broker_uri = "tcp://%s:%d"

middleware_identifier = "%s"
socket_listening_port = %d
alive_checking_period = 60

main_db_file_path = "%s/%s_Main.db"
value_log_db_file_path = "%s/%s_ValueLog.db"

log_level = 5
log_file_path = "%s/simulation_log/%s_middleware.log"
log_max_size = 300
log_backup_num = 100'''

    # port: int
    MOSQUITTO_CONF_TEMPLATE = Template('''set_tcp_nodelay true
log_timestamp true
log_timestamp_format %Y/%m/%d %H:%M:%S

listener $port 0.0.0.0
protocol mqtt
allow_anonymous true''')

    INIT_SCRIPT_TEMPLATE = '''MAIN_DB=%s/%s_Main.db
VALUE_LOG_DB=%s/%s_ValueLog.db

if [ -f "$MAIN_DB" ]; then
    rm -f $MAIN_DB
fi
if [ -f "$VALUE_LOG_DB" ]; then
    rm -f $VALUE_LOG_DB
fi

sqlite3 $MAIN_DB < %s/MainDBCreate
sqlite3 $VALUE_LOG_DB < %s/ValueLogDBCreate'''

    def __init__(self, name: str = '', level: int = -1,
                 thing_list: List['SoPThing'] = [], scenario_list: List['SoPScenario'] = [], parent: 'SoPMiddleware' = None, children: List['SoPMiddleware'] = [],
                 device: SoPDevice = None,
                 remote_middleware_path: str = None, remote_middleware_config_path: str = None,
                 mqtt_port: int = None, mqtt_ssl_port: int = None, websocket_port: int = None, websocket_ssl_port: int = None, localserver_port: int = 58132) -> None:
        super().__init__(name, level, component_type=SoPComponentType.MIDDLEWARE)

        self.thing_list = thing_list
        self.scenario_list = scenario_list
        self.parent: SoPMiddleware = parent
        self.children: List[SoPMiddleware] = children

        self.device = device

        self.remote_middleware_path = remote_middleware_path
        self.remote_middleware_config_path = remote_middleware_config_path
        self.remote_middleware_cfg_file_path = ''
        self.remote_mosquitto_conf_file_path = ''
        self.remote_init_script_file_path = ''

        self.middleware_cfg_file_path = ''
        self.mosquitto_conf_file_path = ''
        self.init_script_file_path = ''

        self.middleware_cfg = ''
        self.mosquitto_conf = ''
        self.init_script = ''

        self.mqtt_port = mqtt_port
        self.mqtt_ssl_port = mqtt_ssl_port
        self.websocket_port = websocket_port
        self.websocket_ssl_port = websocket_ssl_port
        self.localserver_port = localserver_port

        self.online = False

        self.recv_queue: Queue = Queue()

    @classmethod
    def load(cls, data: dict) -> 'SoPMiddleware':
        middleware: SoPMiddleware = super().load(data=data)

        middleware.thing_list = [SoPThing.load(thing_info) for thing_info in data['thing_list']]
        middleware.scenario_list = [SoPScenario.load(scenario_info) for scenario_info in data['scenario_list']]
        middleware.children = [SoPMiddleware.load(child_middleware_info) for child_middleware_info in data['child_middleware_list']]

        middleware.device = SoPDevice.load(data['device'])

        middleware.remote_middleware_path = data['remote_middleware_path']
        middleware.remote_middleware_config_path = data['remote_middleware_config_path']

        # middleware_tree가 지정되어있는 경우 하나로 정해진다.
        middleware.mqtt_port = data['mqtt_port']
        middleware.mqtt_ssl_port = data['mqtt_ssl_port']
        middleware.websocket_port = data['websocket_port']
        middleware.websocket_ssl_port = data['websocket_ssl_port']
        middleware.localserver_port = data['localserver_port']

        return middleware

    def dict(self):
        self.children: List[SoPMiddleware]
        return dict(**super().dict(),
                    thing_list=[thing.dict() for thing in self.thing_list],
                    scenario_list=[scenario.dict() for scenario in self.scenario_list],
                    child_middleware_list=[child_middleware.dict() for child_middleware in self.children],
                    device=self.device.dict(),
                    remote_middleware_path=self.remote_middleware_path,
                    remote_middleware_config_path=self.remote_middleware_config_path,
                    mqtt_port=self.mqtt_port,
                    mqtt_ssl_port=self.mqtt_ssl_port,
                    websocket_port=self.websocket_port,
                    websocket_ssl_port=self.websocket_ssl_port,
                    localserver_port=self.localserver_port)

    def set_port(self, mqtt_port: int, mqtt_ssl_port: int, websocket_port: int, websocket_ssl_port: int, localserver_port: int):
        self.mqtt_port = mqtt_port
        self.mqtt_ssl_port = mqtt_ssl_port
        self.websocket_port = websocket_port
        self.websocket_ssl_port = websocket_ssl_port
        self.localserver_port = localserver_port

    def middleware_cfg_file(self, simulation_env: 'SoPMiddleware', remote_home_dir: str):
        _, parent_middleware = find_component(simulation_env, self)
        parent_middleware: SoPMiddleware
        if parent_middleware is None:
            parent_middleware_line = ''
        else:
            parent_middleware_line = f'parent_broker_uri = "tcp://{parent_middleware.device.host}:{parent_middleware.mqtt_port}"'

        user = os.path.basename(remote_home_dir)
        self.middleware_cfg = SoPMiddleware.CFG_TEMPLATE % (parent_middleware_line,
                                                            '127.0.0.1',
                                                            self.mqtt_port if self.mqtt_port else self.device.mqtt_port,
                                                            self.name,
                                                            self.localserver_port,
                                                            home_dir_append(
                                                                path=self.remote_middleware_config_path, user=user),
                                                            self.name,
                                                            home_dir_append(
                                                                path=self.remote_middleware_config_path, user=user),
                                                            self.name,
                                                            remote_home_dir,
                                                            self.name)
        return self.middleware_cfg

    def mosquitto_conf_file(self):
        mosquitto_port = self.mqtt_port if self.mqtt_port else self.device.mqtt_port
        self.mosquitto_conf = SoPMiddleware.MOSQUITTO_CONF_TEMPLATE.substitute(port=mosquitto_port)

        return self.mosquitto_conf

    def init_script_file(self, remote_home_dir: str):
        user = os.path.basename(remote_home_dir)
        self.init_script = SoPMiddleware.INIT_SCRIPT_TEMPLATE % (home_dir_append(path=self.remote_middleware_config_path, user=user),
                                                                 self.name,
                                                                 home_dir_append(
            path=self.remote_middleware_config_path, user=user),
            self.name,
            home_dir_append(
            path=self.remote_middleware_path, user=user),
            home_dir_append(path=self.remote_middleware_path, user=user))
        return self.init_script


class SoPService(SoPComponent):

    ERROR_TEMPLATE = '''\
global thing_start_time
global service_fail_flag

%s

if random.uniform(0, 1) < %f or service_fail_flag[f'{get_current_function_name()}']:
    service_fail_flag[f'{get_current_function_name()}'] = True
    raise Exception('fail error')
'''

    SUBFUNCTION_TEMPLATE = '''\
results += [self.req(key, subfunction_name='%s', tag_list=%s, arg_list=(), service_type=SoPServiceType.FUNCTION, policy=SoPPolicy.%s)]'''

    SERVICE_INSTANCE_TEMPLATE = '''\
SoPFunction(func=%s, return_type=SoPType.STRING, tag_list=[%s], arg_list=[], exec_time=%8.3f, timeout=%8.3f, energy=%d)'''

    SUPER_SERVICE_INSTANCE_TEMPLATE = '''\
SoPSuperFunction(func=self.%s, return_type=SoPType.STRING, tag_list=[%s], arg_list=[], exec_time=%8.3f, timeout=%8.3f, energy=%d)'''

    FUNCTION_TEMPLATE = '''\
def %s() -> str:
    SOPLOG_DEBUG(f'function {get_current_function_name()} run... return %d')
    
%s
    
    time.sleep(%8.3f)
    return "execute_time: %8.3f, energy: %d"
'''

    SUPER_FUNCTION_TEMPLATE = '''\
def %s(self, key) -> str:
    SOPLOG_DEBUG(f'super function {get_current_function_name()} run...')
    results = []

%s

    execute_time_sum = 0
    energy_sum = 0
    if results:
        for result in results:
            for sub_service_result in result:
                if sub_service_result['return_value'] is None:
                    continue
                execute_time = float(sub_service_result['return_value'].split(",")[0].split(": ")[1])
                energy = int(sub_service_result['return_value'].split(",")[1].split(": ")[1])
                execute_time_sum += execute_time
                energy_sum += energy

        return f"execute_time: {execute_time_sum}, energy: {energy_sum}"
    else:
        raise Exception('super execute fail...')
'''

    def __init__(self, name: str = '', level: int = -1,
                 tag_list: List[str] = [], is_super: bool = False, energy: float = 0, execute_time: float = 0, return_value: int = 0,
                 sub_service_list: List['SoPService'] = [], thing: 'SoPThing' = None) -> None:
        super().__init__(name, level, component_type=SoPComponentType.SERVICE)

        self.tag_list = tag_list
        self.is_super = is_super
        self.energy = energy
        self.execute_time = execute_time
        self.return_value = return_value

        self.sub_service_list = sub_service_list
        self.thing = thing

    def tag_code(self) -> str:
        tag_code = ', '.join([f'SoPTag("{tag}")' for tag in self.tag_list])
        return tag_code

    def error_code(self, fail_rate: float, is_super: bool) -> str:
        error_code = self.ERROR_TEMPLATE % ('''\
if thing_start_time == 0:
    thing_start_time = get_current_time()''' if not is_super else '''\
if thing_start_time == 0:
    thing_start_time += 1
elif thing_start_time == 1:
    thing_start_time = get_current_time()''', fail_rate)

        return error_code.rstrip()

    def sub_service_request_code(self) -> str:
        sub_service_request_code_list = []
        for subfunction in self.sub_service_list:
            picked_tag_list = random.sample(subfunction.tag_list, random.randint(1, len(subfunction.tag_list)))
            if len(picked_tag_list) != len(set(picked_tag_list)):
                SOPTEST_LOG_DEBUG(f'request line of {self.name}:{subfunction.name}\'s tag_list has duplicated words! check this out...', SoPTestLogLevel.FAIL)
                picked_tag_list = list(set(picked_tag_list))

            # TODO: policy(ALL, SINGLE) 비율을 조정할 수 있도록 수정하면 좋을 것 같다. (현재는 1:1로 고정)
            policy = random.choice(['SINGLE'])

            sub_service_request_code_list.append(self.SUBFUNCTION_TEMPLATE % (subfunction.name,
                                                                              picked_tag_list,
                                                                              policy))
        return '\n'.join(sub_service_request_code_list).rstrip()

    def service_instance_code(self) -> str:
        tag_code = self.tag_code()
        if not self.is_super:
            service_instance_code = self.SERVICE_INSTANCE_TEMPLATE % (self.name,
                                                                      tag_code,
                                                                      self.execute_time,
                                                                      600,
                                                                      self.energy)
        else:
            service_instance_code = self.SUPER_SERVICE_INSTANCE_TEMPLATE % (self.name,
                                                                            self.tag_code(),
                                                                            self.execute_time,
                                                                            600,
                                                                            self.energy)
        return service_instance_code

    def service_code(self, fail_rate: float, is_super: bool) -> str:
        error_code = append_indent(self.error_code(fail_rate, is_super))
        if not self.is_super:
            service_code = self.FUNCTION_TEMPLATE % (self.name,
                                                     self.return_value,
                                                     error_code,
                                                     self.execute_time,
                                                     self.execute_time,
                                                     self.energy)
        else:
            # in case of super service, error_code is not used.
            sub_service_request_code = append_indent(self.sub_service_request_code())
            service_code = self.SUPER_FUNCTION_TEMPLATE % (self.name, sub_service_request_code)
        return service_code

    @classmethod
    def load(cls, data: dict) -> 'SoPService':
        service: SoPService = super().load(data=data)

        service.tag_list = data['tag_list']
        service.is_super = data['is_super']
        service.energy = data['energy']
        service.execute_time = data['execute_time']
        service.return_value = data['return_value']

        service.sub_service_list = [SoPService.load(service_info) for service_info in data['subfunction_list']]

        return service

    def dict(self) -> dict:
        return dict(**super().dict(),
                    tag_list=self.tag_list,
                    is_super=self.is_super,
                    energy=self.energy,
                    execute_time=self.execute_time,
                    return_value=self.return_value,
                    subfunction_list=[subfunction.dict() for subfunction in self.sub_service_list])


class SoPThing(SoPComponent):

    THING_TEMPLATE = '''\
from big_thing_py.big_thing import *

import time
import random
import argparse

thing_start_time = 0
service_fail_flag = %s

%s

def arg_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", '-n', action='store', type=str,
                        required=False, default='%s', help="thing name")
    parser.add_argument("--host", '-ip', action='store', type=str,
                        required=False, default='%s', help="host name")
    parser.add_argument("--port", '-p', action='store', type=int,
                        required=False, default=%d, help="port")
    parser.add_argument("--alive_cycle", '-ac', action='store', type=int,
                        required=False, default=%8.3f, help="refresh_cycle")
    parser.add_argument("--refresh_cycle", '-rc', action='store', type=int,
                        required=False, default=%8.3f, help="refresh_cycle")
    parser.add_argument("--append_mac", '-am', action='%s',                         # store_true, store_false
                        required=False, help="append mac address to thing name")
    parser.add_argument("--retry_register", action='store_true',
                        required=False, help="retry register feature enable")
    args = parser.parse_args()
    return args


def main():
    args = arg_parse()
    function_list = \\
        [%s]
    value_list = []
    thing = SoPBigThing(name=args.name, service_list=function_list + value_list,
                        alive_cycle=args.alive_cycle, is_super=False, is_parallel=%s, ip=args.host, port=args.port,
                        ssl_ca_path=None, ssl_enable=None, append_mac_address=False, log_name='%s', log_mode=SoPPrintMode.FULL,
                        retry_register=args.retry_register)
    thing.setup(avahi_enable=False)
    thing.run()


if __name__ == '__main__':
    main()
'''
    SUPER_THING_TEMPLATE = '''\
from big_thing_py.super_thing import *

import argparse

thing_start_time = 0


class SoPBasicSuperThing(SoPSuperThing):

    def __init__(self, name: str, service_list: List[SoPService] = ..., alive_cycle: float = 600, is_super: bool = False, is_parallel: bool = True,
                 ip: str = None, port: int = None, ssl_ca_path: str = None, ssl_enable: bool = False, log_name: str = None, log_enable: bool = True, log_mode: SoPPrintMode = SoPPrintMode.FULL, append_mac_address: bool = True,
                 refresh_cycle: float = 10, retry_register: bool = False):
        value_list = []
        function_list = \\
            [%s]

        service_list = value_list + function_list
        super().__init__(name, service_list, alive_cycle, is_super, is_parallel, ip, port,
                         ssl_ca_path, ssl_enable, log_name, log_enable, log_mode, append_mac_address, refresh_cycle, retry_register)

%s

def arg_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", '-n', action='store', type=str,
                        required=False, default='%s', help="thing name")
    parser.add_argument("--host", '-ip', action='store', type=str,
                        required=False, default='%s', help="host name")
    parser.add_argument("--port", '-p', action='store', type=int,
                        required=False, default=%d, help="port")
    parser.add_argument("--alive_cycle", '-ac', action='store', type=int,
                        required=False, default=%8.3f, help="alive cycle")
    parser.add_argument("--refresh_cycle", '-rc', action='store', type=int,
                        required=False, default=%8.3f, help="refresh cycle")
    parser.add_argument("--auto_scan", '-as', action='%s',
                        required=False, help="middleware auto scan enable")
    parser.add_argument("--log", action='store_true',
                        required=False, help="log enable")
    parser.add_argument("--log_mode", action='store',
                        required=False, default=SoPPrintMode.FULL, help="log mode")
    parser.add_argument("--append_mac", '-am', action='store_true',                         # store_true, store_false
                        required=False, help="append mac address to thing name")
    parser.add_argument("--retry_register", action='store_true',
                        required=False, help="retry register feature enable")
    args = parser.parse_args()

    return args


def generate_thing(args):
    super_thing = SoPBasicSuperThing(name=args.name, ip=args.host, port=args.port, is_super=True, is_parallel=%s, ssl_ca_path=None, ssl_enable=None,
                                     alive_cycle=args.alive_cycle, refresh_cycle=args.refresh_cycle, append_mac_address=False, log_name='%s', log_mode=SoPPrintMode.FULL,
                                     retry_register=args.retry_register)
    return super_thing


if __name__ == '__main__':
    args = arg_parse()
    thing = generate_thing(args)
    thing.setup(avahi_enable=args.auto_scan)
    thing.run()
'''

    def __init__(self, name: str = '', level: int = -1,
                 service_list: List['SoPService'] = [], is_super: bool = False, is_parallel: bool = False, alive_cycle: float = 0,
                 device: SoPDevice = None, middleware: SoPMiddleware = None,
                 thing_file_path: str = '', remote_thing_file_path: str = '',
                 fail_rate: float = None) -> None:
        super().__init__(name, level, component_type=SoPComponentType.THING)

        self.service_list = service_list
        self.is_super = is_super
        self.is_parallel = is_parallel
        self.alive_cycle = alive_cycle

        self.device = device
        self.middleware = middleware

        self.thing_file_path = thing_file_path
        self.remote_thing_file_path = remote_thing_file_path
        self.fail_rate = fail_rate

        # for middleware mqtt client name (middleware.name + mac address)
        self.middleware_client_name: str = ''
        self.registered: bool = False
        self.pid: int = 0

        self.recv_queue: Queue = Queue()

    def __getstate__(self):
        state = super().__getstate__()

        state['service_list'] = self.service_list
        state['is_super'] = self.is_super
        state['is_parallel'] = self.is_parallel
        state['alive_cycle'] = self.alive_cycle
        state['device'] = self.device
        state['thing_file_path'] = self.thing_file_path
        state['remote_thing_file_path'] = self.remote_thing_file_path
        state['fail_rate'] = self.fail_rate
        state['middleware_client_name'] = self.middleware_client_name
        state['registered'] = self.registered
        state['pid'] = self.pid

        del state['recv_queue']
        del state['middleware']

        return state

    def __setstate__(self, state):
        super().__setstate__(state)

        self.service_list = state['service_list']
        self.is_super = state['is_super']
        self.is_parallel = state['is_parallel']
        self.alive_cycle = state['alive_cycle']
        self.device = state['device']
        self.thing_file_path = state['thing_file_path']
        self.remote_thing_file_path = state['remote_thing_file_path']
        self.fail_rate = state['fail_rate']
        self.middleware_client_name = state['middleware_client_name']
        self.registered = state['registered']
        self.pid = state['pid']

        self.middleware = None
        self.recv_queue: Queue = Queue()

    @classmethod
    def load(cls, data: dict):
        thing: SoPThing = super().load(data=data)

        thing.service_list = [SoPService.load(service_info)
                              for service_info in data['service_list']]
        thing.is_super = data['is_super']
        thing.is_parallel = data['is_parallel']
        thing.alive_cycle = data['alive_cycle']

        thing.device = SoPDevice.load(data['device'])

        thing.thing_file_path = data['thing_file_path']
        thing.remote_thing_file_path = data['remote_thing_file_path']

        thing.fail_rate = data['fail_rate']

        return thing

    def dict(self):
        return dict(**super().dict(),
                    service_list=[service.dict() for service in self.service_list],
                    is_super=self.is_super,
                    is_parallel=self.is_parallel,
                    alive_cycle=self.alive_cycle,
                    device=self.device.dict(),
                    thing_file_path=self.thing_file_path,
                    remote_thing_file_path=self.remote_thing_file_path,
                    fail_rate=self.fail_rate)

    def thing_code(self):

        if not self.is_super:
            whole_service_code = ''.join(
                [service.service_code(self.fail_rate, self.is_super) + '\n' for service in self.service_list])
            whole_service_instance_code = ', \n\t\t'.join(
                [service.service_instance_code() for service in self.service_list])
            thing_code = self.THING_TEMPLATE % ({service.name: False for service in self.service_list},
                                                whole_service_code,
                                                self.name,
                                                'localhost',
                                                1883,
                                                60,
                                                60,
                                                'store_true',
                                                whole_service_instance_code,
                                                self.is_parallel,
                                                f'./log/{self.name}.log')
        else:
            whole_service_code = append_indent(''.join(
                [service.service_code(self.fail_rate, self.is_super) + '\n' for service in self.service_list]))
            whole_service_instance_code = ', \n\t\t'.join(
                [service.service_instance_code() for service in self.service_list])
            thing_code = self.SUPER_THING_TEMPLATE % (whole_service_instance_code,
                                                      whole_service_code,
                                                      self.name,
                                                      'localhost',
                                                      1883,
                                                      60,
                                                      60,
                                                      'store_true',
                                                      self.is_parallel,
                                                      f'./log/{self.name}.log')
        return thing_code

    def find_service_by_name(self, service_name: str) -> SoPService:
        for service in self.service_list:
            if service.name == service_name:
                return service


class SoPScenario(SoPComponent):

    SCENARIO_TEMPLATE = '''loop(%s) {
%s
}
'''

    def __init__(self, name: str = '', level: int = -1,
                 service_list: List[SoPService] = [], period: float = None, priority: int = None,
                 scenario_file_path: str = '', middleware: SoPMiddleware = None) -> None:
        super().__init__(name, level, component_type=SoPComponentType.SCENARIO)

        self.service_list = service_list
        self.period = period
        self.priority = priority
        self.scenario_file_path = scenario_file_path
        self.middleware = middleware

        self.state: SoPScenarioState = SoPScenarioState.UNDEFINED
        self.add_result_arrived = False
        self.schedule_success = False
        self.schedule_timeout = False

        self.recv_queue: Queue = Queue()

        # FIXME: 제대로 구현하기
        self.cycle_count = 0

    def __getstate__(self):
        state = super().__getstate__()

        state['service_list'] = self.service_list
        state['period'] = self.period
        state['priority'] = self.priority
        state['scenario_file_path'] = self.scenario_file_path
        state['state'] = self.state
        state['add_result_arrived'] = self.add_result_arrived
        state['schedule_success'] = self.schedule_success
        state['schedule_timeout'] = self.schedule_timeout

        del state['recv_queue']
        del state['middleware']

        return state

    def __setstate__(self, state):
        super().__setstate__(state)

        self.service_list = state['service_list']
        self.period = state['period']
        self.priority = state['priority']
        self.scenario_file_path = state['scenario_file_path']
        self.state = state['state']
        self.add_result_arrived = state['add_result_arrived']
        self.schedule_success = state['schedule_success']
        self.schedule_timeout = state['schedule_timeout']

        self.middleware = None
        self.recv_queue: Queue = Queue()

    @classmethod
    def load(cls, data: dict) -> None:
        scenario: SoPScenario = super().load(data=data)

        scenario.service_list = [SoPService.load(service_info)
                                 for service_info in data['service_list']]
        scenario.period = data['period']
        scenario.scenario_file_path = data['scenario_file_path']

        return scenario

    def dict(self) -> dict:
        return dict(**super().dict(),
                    service_list=[service.dict() for service in self.service_list],
                    period=self.period,
                    scenario_file_path=self.scenario_file_path)

    def scenario_code(self) -> str:
        service_line_code = ''
        for service in self.service_list:
            tag_code = f'(#{" #".join([tag for tag in random.sample(service.tag_list, k=random.randint(1, len(service.tag_list)))])})'
            service_line = f'{tag_code}.{service.name}()' + '\n'
            service_line_code += service_line
        service_line_code = service_line_code.rstrip()
        scenario_code = (self.SCENARIO_TEMPLATE % (f'{(self.period * 1000):.0f} MSEC',
                                                   append_indent(service_line_code)))
        return scenario_code

    def is_super(self) -> bool:
        return all([service.is_super for service in self.service_list])
