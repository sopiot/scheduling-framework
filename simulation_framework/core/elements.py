from simulation_framework.utils import *
from simulation_framework.logger import *

from string import Template
from queue import Queue
from abc import ABCMeta


def get_middleware_list_recursive(middleware: 'SoPMiddlewareElement' = None) -> List[object]:
    middleware_list = [middleware]

    for child_middleware in middleware.child_middleware_list:
        middleware_list.extend(get_middleware_list_recursive(child_middleware))

    middleware_list = sorted(middleware_list, key=lambda x: x.level, reverse=True)
    return middleware_list


def get_thing_list_recursive(middleware: 'SoPMiddlewareElement' = None) -> List[object]:
    thing_list = [thing for thing in middleware.thing_list]

    for child_middleware in middleware.child_middleware_list:
        thing_list.extend(get_thing_list_recursive(child_middleware))

    thing_list = sorted(thing_list, key=lambda x: x.level, reverse=True)
    return thing_list


def get_scenario_list_recursive(middleware: 'SoPMiddlewareElement' = None) -> List[object]:
    scenario_list = [scenario for scenario in middleware.scenario_list]

    for child_middleware in middleware.child_middleware_list:
        scenario_list.extend(get_scenario_list_recursive(child_middleware))

    scenario_list = sorted(scenario_list, key=lambda x: x.level, reverse=True)
    return scenario_list


def find_element_recursive(middleware: 'SoPMiddlewareElement', element: 'SoPElement', key: Callable = lambda x: x) -> Tuple[object, object]:

    def inner(middleware: 'SoPMiddlewareElement', element: 'SoPElement'):
        if key(middleware) == key(element):
            return middleware, None

        for thing in middleware.thing_list:
            if key(thing) == key(element):
                return thing, middleware
        for scenario in middleware.scenario_list:
            if key(scenario) == key(element):
                return scenario, middleware
        for child_middleware in middleware.child_middleware_list:
            if key(child_middleware) == key(element):
                return child_middleware, middleware

        for child_middleware in middleware.child_middleware_list:
            result = inner(
                child_middleware, element)
            if result:
                return result[0], result[1]
            else:
                inner(
                    child_middleware, element)

    result = inner(middleware, element)
    if result:
        return result[0], result[1]
    else:
        return None, None


def find_element_by_name_recursive(middleware: 'SoPMiddlewareElement', element_name: str):

    def inner(middleware: 'SoPMiddlewareElement', element_name: str):
        if middleware.name == element_name:
            return middleware, None

        for thing in middleware.thing_list:
            if thing.name == element_name:
                return thing, middleware
        for scenario in middleware.scenario_list:
            if scenario.name == element_name:
                return scenario, middleware
        for child_middleware in middleware.child_middleware_list:
            if child_middleware.name == element_name:
                return child_middleware, middleware

        for child_middleware in middleware.child_middleware_list:
            result = inner(child_middleware, element_name)
            if result:
                return result[0], result[1]
            else:
                inner(child_middleware, element_name)

    result = inner(middleware, element_name)
    if result:
        return result[0], result[1]
    else:
        return None, None


class SoPElementType(Enum):
    UNDEFINED = 'UNDEFINED'
    DEVICE = 'DEVICE'
    MIDDLEWARE = 'MIDDLEWARE'
    THING = 'THING'
    SERVICE = 'SERVICE'
    SCENARIO = 'SCENARIO'

    @classmethod
    def get(cls, name: str):
        try:
            return cls[name.upper()]
        except Exception:
            return cls.UNDEFINED


class SoPElementActionType(Enum):
    UNDEFINED = 'UNDEFINED'

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

    @classmethod
    def get(cls, name: str):
        try:
            return cls[name.upper()]
        except Exception:
            return cls.UNDEFINED


class SoPScenarioState(Enum):
    UNDEFINED = -1
    CREATED = 'CREATED'
    SCHEDULING = 'SCHEDULING'
    INITIALIZED = 'INITIALIZED'
    RUNNING = 'RUNNING'
    EXECUTING = 'EXECUTING'
    STUCKED = 'STUCKED'
    COMPLETED = 'COMPLETED'

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
    UNDEFINED = 'UNDEFINED'
    NORMAL = 'NORMAL'
    FAIL = 'FAIL'
    TIMEOUT = 'TIMEOUT'
    SHUTDOWN = 'SHUTDOWN'

    @classmethod
    def get(cls, name: str):
        try:
            return cls[name.upper()]
        except Exception:
            return cls.UNDEFINED


class SoPElementScopeType(Enum):
    LOCAL = 'LOCAL'
    SUPER = 'SUPER'


class SoPElement(metaclass=ABCMeta):

    def __init__(self, name: str, level: int, element_type: SoPElementType) -> None:
        # basic info
        self.name = name
        self.level = level
        self.element_type = element_type

    def load(self, data: dict) -> None:
        self.name = data['name']
        self.level = data['level']
        self.element_type = SoPElementType.get(data['element_type'])

        return self

    def dict(self) -> dict:
        return dict(name=self.name,
                    level=self.level,
                    element_type=self.element_type.value)


class SoPDeviceElement(SoPElement):
    def __init__(self, name: str = '', level: int = -1, element_type: SoPElementType = SoPElementType.DEVICE,
                 host: str = '', ssh_port: int = None, user: str = '', password: str = '',
                 mqtt_port: int = None,
                 mqtt_ssl_port: int = None,
                 websocket_port: int = None,
                 websocket_ssl_port: int = None,
                 localserver_port: int = 58132) -> None:
        super().__init__(name, level, element_type)

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

    def load(self, data: dict) -> 'SoPDeviceElement':
        self.name = data['name']
        self.element_type = SoPElementType.get(data['element_type'])

        self.host = data['host']
        self.ssh_port = data['ssh_port']
        self.user = data['user']
        self.password = data['password']

        self.mqtt_port = data['mqtt_port']
        self.mqtt_ssl_port = data['mqtt_ssl_port']
        self.websocket_port = data['websocket_port']
        self.websocket_ssl_port = data['websocket_ssl_port']
        self.localserver_port = data['localserver_port']

        return self

    def dict(self):
        return dict(name=self.name,
                    element_type=self.element_type.value,
                    host=self.host,
                    user=self.user,
                    ssh_port=self.ssh_port,
                    password=self.password,
                    mqtt_port=self.mqtt_port,
                    mqtt_ssl_port=self.mqtt_ssl_port,
                    websocket_port=self.websocket_port,
                    websocket_ssl_port=self.websocket_ssl_port,
                    localserver_port=self.localserver_port)


class SoPMiddlewareElement(SoPElement):

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

    MOSQUITTO_CONF_TEMPLATE = Template('''set_tcp_nodelay true
log_timestamp true
log_timestamp_format %Y/%m/%d %H:%M:%S

listener $port 0.0.0.0
protocol mqtt
allow_anonymous true''')

#     MOSQUITTO_CONF_TEMPLATE = '''set_tcp_nodelay true

# listener %d 0.0.0.0
# protocol mqtt
# allow_anonymous true

# listener %d 0.0.0.0
# protocol websockets
# allow_anonymous true'''

#     MOSQUITTO_CONF_TEMPLATE_OLD = '''persistence true
# persistence_location /var/lib/mosquitto/

# include_dir /etc/mosquitto/conf.d

# listener %d 0.0.0.0
# protocol mqtt
# allow_anonymous true

# listener %d 0.0.0.0
# protocol websockets
# allow_anonymous true

# listener %d 0.0.0.0
# protocol mqtt
# allow_anonymous true
# cafile /etc/mosquitto/ca_certificates/ca.crt
# certfile /etc/mosquitto/certs/host.crt
# keyfile /etc/mosquitto/certs/host.key
# require_certificate true

# listener %d 0.0.0.0
# protocol websockets
# allow_anonymous true
# cafile /etc/mosquitto/ca_certificates/ca.crt
# certfile /etc/mosquitto/certs/host.crt
# keyfile /etc/mosquitto/certs/host.key
# require_certificate true'''

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

    def __init__(self, name: str = '', level: int = -1, element_type: SoPElementType = None,
                 thing_list: List['SoPThingElement'] = [], scenario_list: List['SoPScenarioElement'] = [], child_middleware_list: List['SoPMiddlewareElement'] = [],
                 device: SoPDeviceElement = None,
                 remote_middleware_path: str = None, remote_middleware_config_path: str = None,
                 mqtt_port: int = None, mqtt_ssl_port: int = None, websocket_port: int = None, websocket_ssl_port: int = None, localserver_port: int = 58132,
                 thing_num: List[int] = None, scenario_num: List[int] = None, super_thing_num: List[int] = None, super_scenario_num: List[int] = None) -> None:
        super().__init__(name, level, element_type)

        self.thing_list = thing_list
        self.scenario_list = scenario_list
        self.child_middleware_list = child_middleware_list

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

        # for middleware_tree config option
        self.thing_num = thing_num
        self.super_thing_num = super_thing_num
        self.scenario_num = scenario_num
        self.super_scenario_num = super_scenario_num

        self.online = False

        self.event_log: List[SoPEvent] = []
        self.recv_queue: Queue = Queue()

    def load(self, data: dict):
        super().load(data)

        self.thing_list = [SoPThingElement().load(thing_info)
                           for thing_info in data['thing_list']]
        self.scenario_list = [SoPScenarioElement().load(
            scenario_info) for scenario_info in data['scenario_list']]
        self.child_middleware_list = [SoPMiddlewareElement().load(
            child_middleware_info) for child_middleware_info in data['child_middleware_list']]

        self.device = SoPDeviceElement().load(data['device'])

        self.remote_middleware_path = data['remote_middleware_path']
        self.remote_middleware_config_path = data['remote_middleware_config_path']

        # middleware_tree가 지정되어있는 경우 하나로 정해진다.
        self.mqtt_port = data['mqtt_port']
        self.mqtt_ssl_port = data['mqtt_ssl_port']
        self.websocket_port = data['websocket_port']
        self.websocket_ssl_port = data['websocket_ssl_port']
        self.localserver_port = data['localserver_port']

        self.thing_num = data['thing_num']
        self.super_thing_num = data['super_thing_num']
        self.scenario_num = data['scenario_num']
        self.super_scenario_num = data['super_scenario_num']

        return self

    def dict(self):
        return dict(
            **super().dict(),
            thing_list=[thing.dict() for thing in self.thing_list],
            scenario_list=[scenario.dict()
                           for scenario in self.scenario_list],
            child_middleware_list=[child_middleware.dict(
            ) for child_middleware in self.child_middleware_list],
            device=self.device.dict(),
            remote_middleware_path=self.remote_middleware_path,
            remote_middleware_config_path=self.remote_middleware_config_path,
            mqtt_port=self.mqtt_port,
            mqtt_ssl_port=self.mqtt_ssl_port,
            websocket_port=self.websocket_port,
            websocket_ssl_port=self.websocket_ssl_port,
            localserver_port=self.localserver_port,
            thing_num=self.thing_num,
            super_thing_num=self.super_thing_num,
            scenario_num=self.scenario_num,
            super_scenario_num=self.super_scenario_num)

    def set_port(self, mqtt_port: int, mqtt_ssl_port: int, websocket_port: int, websocket_ssl_port: int, localserver_port: int):
        self.mqtt_port = mqtt_port
        self.mqtt_ssl_port = mqtt_ssl_port
        self.websocket_port = websocket_port
        self.websocket_ssl_port = websocket_ssl_port
        self.localserver_port = localserver_port

    def middleware_cfg_file(self, simulation_env: 'SoPMiddlewareElement', remote_home_dir: str):
        _, parent_middleware = find_element_recursive(simulation_env, self)
        parent_middleware: SoPMiddlewareElement
        if parent_middleware is None:
            parent_middleware_line = ''
        else:
            parent_middleware_line = f'parent_broker_uri = "tcp://{parent_middleware.device.host}:{parent_middleware.mqtt_port}"'

        user = os.path.basename(remote_home_dir)
        self.middleware_cfg = SoPMiddlewareElement.CFG_TEMPLATE % (parent_middleware_line,
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
        # if mosquitto_conf_trim:
        #     self.mosquitto_conf = SoPMiddlewareElement.MOSQUITTO_CONF_TEMPLATE % (self.mqtt_port,
        #                                                                           self.websocket_port,)
        # else:
        #     self.mosquitto_conf = SoPMiddlewareElement.MOSQUITTO_CONF_TEMPLATE_OLD % (self.mqtt_port,
        #                                                                               self.mqtt_ssl_port,
        #                                                                               self.websocket_port,
        #                                                                               self.websocket_ssl_port)

        # self.mosquitto_conf = SoPMiddlewareElement.MOSQUITTO_CONF_TEMPLATE % (self.mqtt_port,
        #                                                                       self.websocket_port,)

        mosquitto_port = self.mqtt_port if self.mqtt_port else self.device.mqtt_port
        self.mosquitto_conf = SoPMiddlewareElement.MOSQUITTO_CONF_TEMPLATE.substitute(port=mosquitto_port)

        return self.mosquitto_conf

    def init_script_file(self, remote_home_dir: str):
        user = os.path.basename(remote_home_dir)
        self.init_script = SoPMiddlewareElement.INIT_SCRIPT_TEMPLATE % (home_dir_append(path=self.remote_middleware_config_path, user=user),
                                                                        self.name,
                                                                        home_dir_append(
                                                                            path=self.remote_middleware_config_path, user=user),
                                                                        self.name,
                                                                        home_dir_append(
                                                                            path=self.remote_middleware_path, user=user),
                                                                        home_dir_append(path=self.remote_middleware_path, user=user))
        return self.init_script


class SoPServiceElement(SoPElement):

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
            for subresult in result:
                if subresult['return_value'] is None:
                    continue
                execute_time = float(subresult['return_value'].split(",")[0].split(": ")[1])
                energy = int(subresult['return_value'].split(",")[1].split(": ")[1])
                execute_time_sum += execute_time
                energy_sum += energy

        return f"execute_time: {execute_time_sum}, energy: {energy_sum}"
    else:
        raise Exception('super execute fail...')
'''

    def __init__(self, name: str = '', level: int = -1, element_type: SoPElementType = None,
                 tag_list: List[str] = [], is_super: bool = False, energy: float = 0, execute_time: float = 0, return_value: int = 0,
                 sub_service_list: List['SoPServiceElement'] = []) -> None:
        super().__init__(name, level, element_type)

        self.tag_list = tag_list
        self.is_super = is_super
        self.energy = energy
        self.execute_time = execute_time
        self.return_value = return_value

        self.sub_service_list = sub_service_list

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

    def reqline_code(self) -> str:
        reqline_code_list = []
        for subfunction in self.sub_service_list:
            picked_tag_list = random.sample(subfunction.tag_list, random.randint(
                1, len(subfunction.tag_list)))
            if len(picked_tag_list) != len(set(picked_tag_list)):
                SOPTEST_LOG_DEBUG(
                    f'request line of {self.name}:{subfunction.name}\'s tag_list has duplicated words! check this out...', SoPTestLogLevel.FAIL)
                picked_tag_list = list(set(picked_tag_list))

            # TODO: policy(ALL, SINGLE) 비율을 조정할 수 있도록 수정하면 좋을 것 같다. (현재는 1:1로 고정)
            policy = random.choice(['SINGLE'])

            reqline_code_list.append(self.SUBFUNCTION_TEMPLATE % (subfunction.name,
                                                                  picked_tag_list,
                                                                  policy))
        return '\n'.join(reqline_code_list).rstrip()

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
        error_code = append_indent(self.error_code(
            fail_rate, is_super))
        if not self.is_super:
            service_code = self.FUNCTION_TEMPLATE % (self.name,
                                                     self.return_value,
                                                     error_code,
                                                     self.execute_time,
                                                     self.execute_time,
                                                     self.energy)
        else:
            # NOTE: in case of super service, error_code is not used.
            reqline_code = append_indent(self.reqline_code())
            service_code = self.SUPER_FUNCTION_TEMPLATE % (self.name,
                                                           reqline_code)
        return service_code

    def load(self, data: dict) -> 'SoPServiceElement':
        super().load(data)

        self.tag_list = data['tag_list']
        self.is_super = data['is_super']
        self.energy = data['energy']
        self.execute_time = data['execute_time']
        self.return_value = data['return_value']

        self.sub_service_list = [SoPServiceElement().load(
            service_info) for service_info in data['subfunction_list']]

        return self

    def dict(self) -> dict:
        return dict(**super().dict(),
                    tag_list=self.tag_list,
                    is_super=self.is_super,
                    energy=self.energy,
                    execute_time=self.execute_time,
                    return_value=self.return_value,
                    subfunction_list=[subfunction.dict() for subfunction in self.sub_service_list])


class SoPThingElement(SoPElement):

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
    args, unknown = parser.parse_known_args()
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
    args, unknown = parser.parse_known_args()

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

    def __init__(self, name: str = '', level: int = -1, element_type: SoPElementType = None,
                 service_list: List['SoPServiceElement'] = [], is_super: bool = False, is_parallel: bool = False, alive_cycle: float = 0,
                 device: SoPDeviceElement = None,
                 thing_file_path: str = '', remote_thing_file_path: str = '',
                 fail_rate: float = None) -> None:
        super().__init__(name, level, element_type)

        self.service_list = service_list
        self.is_super = is_super
        self.is_parallel = is_parallel
        self.alive_cycle = alive_cycle

        self.device = device

        self.thing_file_path = thing_file_path
        self.remote_thing_file_path = remote_thing_file_path
        self.fail_rate = fail_rate

        self.middleware_client_name: str = ''
        self.registered: bool = False
        self.pid: int = 0

        self.event_log: List[SoPEvent] = []
        self.recv_queue: Queue = Queue()

    def load(self, data: dict):
        super().load(data)

        self.service_list = [SoPServiceElement().load(service_info)
                             for service_info in data['service_list']]
        self.is_super = data['is_super']
        self.is_parallel = data['is_parallel']
        self.alive_cycle = data['alive_cycle']

        self.device = SoPDeviceElement().load(data['device'])

        self.thing_file_path = data['thing_file_path']
        self.remote_thing_file_path = data['remote_thing_file_path']

        self.fail_rate = data['fail_rate']

        return self

    def dict(self):
        return dict(**super().dict(),
                    service_list=[service.dict()
                                  for service in self.service_list],
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

    def find_service_by_name(self, service_name: str) -> SoPServiceElement:
        for service in self.service_list:
            if service.name == service_name:
                return service


class SoPScenarioElement(SoPElement):

    SCENARIO_TEMPLATE = '''loop(%s) {
%s
}
'''

    def __init__(self, name: str = '', level: int = -1, element_type: SoPElementType = None,
                 service_list: List[SoPServiceElement] = [], period: float = None,
                 scenario_file_path: str = '') -> None:
        super().__init__(name, level, element_type)

        self.service_list = service_list
        self.period = period
        self.scenario_file_path = scenario_file_path

        self.state: SoPScenarioState = None
        self.schedule_success = False
        self.schedule_timeout = False
        self.service_check = False

        self.event_log: List[SoPEvent] = []
        self.recv_queue: Queue = Queue()

        # FIXME: 제대로 구현하기
        self.cycle_count = 0

    def load(self, data: dict) -> None:
        super().load(data)

        self.service_list = [SoPServiceElement().load(service_info)
                             for service_info in data['service_list']]
        self.period = data['period']
        self.scenario_file_path = data['scenario_file_path']

        return self

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
