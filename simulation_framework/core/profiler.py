from simulation_framework.core.elements import *
from datetime import datetime, timedelta
from enum import Enum, auto

TIMESTAMP_FORMAT = '%Y/%m/%d %H:%M:%S.%f'
TIMESTAMP_REGEX = r'\[(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}\.\d{6})\]'

SUPER_PROTOCOL = [SoPProtocolType.Super.MS_SCHEDULE,
                  SoPProtocolType.Super.MS_EXECUTE,
                  SoPProtocolType.Super.CP_SCHEDULE,
                  SoPProtocolType.Super.CP_EXECUTE]
SUPER_RESULT_PROTOCOL = [SoPProtocolType.Super.SM_RESULT_SCHEDULE,
                         SoPProtocolType.Super.SM_RESULT_EXECUTE,
                         SoPProtocolType.Super.PC_RESULT_SCHEDULE,
                         SoPProtocolType.Super.PC_RESULT_EXECUTE]
SUB_PROTOCOL = [SoPProtocolType.Super.SM_SCHEDULE,
                SoPProtocolType.Super.SM_EXECUTE,
                SoPProtocolType.Super.PC_SCHEDULE,
                SoPProtocolType.Super.PC_EXECUTE]
SUB_RESULT_PROTOCOL = [SoPProtocolType.Super.MS_RESULT_SCHEDULE,
                       SoPProtocolType.Super.MS_RESULT_EXECUTE,
                       SoPProtocolType.Super.CP_RESULT_SCHEDULE,
                       SoPProtocolType.Super.CP_RESULT_EXECUTE]

EXECUTE_PROTOCOL = [SoPProtocolType.Super.MS_EXECUTE,
                    SoPProtocolType.Super.CP_EXECUTE,
                    SoPProtocolType.Super.SM_RESULT_EXECUTE,
                    SoPProtocolType.Super.PC_RESULT_EXECUTE,
                    SoPProtocolType.Super.SM_EXECUTE,
                    SoPProtocolType.Super.PC_EXECUTE,
                    SoPProtocolType.Super.MS_RESULT_EXECUTE,
                    SoPProtocolType.Super.CP_RESULT_EXECUTE,
                    SoPProtocolType.Base.MT_EXECUTE,
                    SoPProtocolType.Base.TM_RESULT_EXECUTE]
SCHEDULE_PROTOCOL = [SoPProtocolType.Super.MS_SCHEDULE,
                     SoPProtocolType.Super.CP_SCHEDULE,
                     SoPProtocolType.Super.SM_RESULT_SCHEDULE,
                     SoPProtocolType.Super.PC_RESULT_SCHEDULE,
                     SoPProtocolType.Super.SM_SCHEDULE,
                     SoPProtocolType.Super.PC_SCHEDULE,
                     SoPProtocolType.Super.MS_RESULT_SCHEDULE,
                     SoPProtocolType.Super.CP_RESULT_SCHEDULE]

MS_PROTOCOL = [SoPProtocolType.Super.MS_SCHEDULE, SoPProtocolType.Super.MS_EXECUTE]
MS_RESULT_PROTOCOL = [SoPProtocolType.Super.MS_RESULT_SCHEDULE, SoPProtocolType.Super.MS_RESULT_EXECUTE]
SM_PROTOCOL = [SoPProtocolType.Super.SM_SCHEDULE, SoPProtocolType.Super.SM_EXECUTE]
SM_RESULT_PROTOCOL = [SoPProtocolType.Super.SM_RESULT_SCHEDULE, SoPProtocolType.Super.SM_RESULT_EXECUTE]
CP_PROTOCOL = [SoPProtocolType.Super.CP_SCHEDULE, SoPProtocolType.Super.CP_EXECUTE]
CP_RESULT_PROTOCOL = [SoPProtocolType.Super.CP_RESULT_SCHEDULE, SoPProtocolType.Super.CP_RESULT_EXECUTE]
PC_PROTOCOL = [SoPProtocolType.Super.PC_SCHEDULE, SoPProtocolType.Super.PC_EXECUTE]
PC_RESULT_PROTOCOL = [SoPProtocolType.Super.PC_RESULT_SCHEDULE, SoPProtocolType.Super.PC_RESULT_EXECUTE]

SUB_EXECUTE_PROTOCOL = [SoPProtocolType.Base.MT_EXECUTE]
SUB_EXECUTE_RESULT_PROTOCOL = [SoPProtocolType.Base.TM_RESULT_EXECUTE]


class OverheadType(Enum):
    SUPER_THING_INNER = auto()
    TARGET_THING_INNER = auto()
    MIDDLEWARE_INNER = auto()
    SUPER_THING__MIDDLEWARE_COMM = auto()
    TARGET_THING__MIDDLEWARE_COMM = auto()
    MIDDLEWARE__MIDDLEWARE_COMM = auto()
    INNER = auto()
    COMM = auto()


class ProfileType(Enum):
    SCHEDULE = auto()
    EXECUTE = auto()


class ScheduleStatus(Enum):
    CHECK = 'check'
    CONFIRM = 'confirm'


class Overhead:

    def __init__(self) -> None:
        self.super_thing_inner_overhead_list: List[timedelta] = []
        self.target_thing_inner_overhead_list: List[timedelta] = []
        self.middleware_inner_overhead_list: List[timedelta] = []
        self.super_thing__middleware_comm_overhead_list: List[timedelta] = []
        self.target_thing__middleware_comm_overhead_list: List[timedelta] = []
        self.middleware__middleware_comm_overhead_list: List[timedelta] = []

    def __str__(self):
        super_thing_inner_overhead_total, super_thing_inner_overhead_avg = self.sum(OverheadType.SUPER_THING_INNER) * 1e3, self.avg(OverheadType.SUPER_THING_INNER) * 1e3
        target_thing_inner_overhead_total, target_thing_inner_overhead_avg = self.sum(OverheadType.TARGET_THING_INNER) * 1e3, self.avg(OverheadType.TARGET_THING_INNER) * 1e3
        middleware_inner_overhead_total, middleware_inner_overhead_avg = self.sum(OverheadType.MIDDLEWARE_INNER) * 1e3, self.avg(OverheadType.MIDDLEWARE_INNER) * 1e3
        super_thing_middleware_comm_overhead_total, super_thing_middleware_comm_overhead_avg = self.sum(
            OverheadType.SUPER_THING__MIDDLEWARE_COMM) * 1e3, self.avg(OverheadType.SUPER_THING__MIDDLEWARE_COMM) * 1e3
        target_thing_middleware_comm_overhead_total, target_thing_middleware_comm_overhead_avg = self.sum(
            OverheadType.TARGET_THING__MIDDLEWARE_COMM) * 1e3, self.avg(OverheadType.TARGET_THING__MIDDLEWARE_COMM) * 1e3
        middleware_middleware_comm_overhead_total, middleware_middleware_comm_overhead_avg = self.sum(
            OverheadType.MIDDLEWARE__MIDDLEWARE_COMM) * 1e3, self.avg(OverheadType.MIDDLEWARE__MIDDLEWARE_COMM) * 1e3

        return (f'Super Thing                 Inner Overhead         - '
                f'total: {super_thing_inner_overhead_total:8.3f} ms, average: {super_thing_inner_overhead_avg:8.3f} ms\n'
                f'Target Thing                Target Service Execute - '
                f'total: {target_thing_inner_overhead_total:8.3f} ms, average: {target_thing_inner_overhead_avg:8.3f} ms\n'
                f'Middleware                  Inner Overhead         - '
                f'total: {middleware_inner_overhead_total:8.3f} ms, average: {middleware_inner_overhead_avg:8.3f} ms\n'
                f'Super Thing <-> Middleware  Communication Overhead - '
                f'total: {super_thing_middleware_comm_overhead_total:8.3f} ms, average: {super_thing_middleware_comm_overhead_avg:8.3f} ms\n'
                f'Target Thing <-> Middleware Communication Overhead - '
                f'total: {target_thing_middleware_comm_overhead_total:8.3f} ms, average: {target_thing_middleware_comm_overhead_avg:8.3f} ms\n'
                f'Middleware <-> Middleware   Communication Overhead - '
                f'total: {middleware_middleware_comm_overhead_total:8.3f} ms, average: {middleware_middleware_comm_overhead_avg:8.3f} ms\n'
                ''
                f'                            Total Inner Overhead         - '
                f'{self.inner_overhead_total() * 1e3:8.3f} ms\n'
                f'                            Total Communication Overhead - '
                f'{self.comm_overhead_total() * 1e3:8.3f} ms\n'
                f'                            Total Overhead - '
                f'{self.overhead_total() * 1e3:8.3f} ms')

    def __add__(self, o: 'Overhead') -> 'Overhead':
        self.super_thing_inner_overhead_list += o.super_thing_inner_overhead_list
        self.target_thing_inner_overhead_list += o.target_thing_inner_overhead_list
        self.middleware_inner_overhead_list += o.middleware_inner_overhead_list
        self.super_thing__middleware_comm_overhead_list += o.super_thing__middleware_comm_overhead_list
        self.target_thing__middleware_comm_overhead_list += o.target_thing__middleware_comm_overhead_list
        self.middleware__middleware_comm_overhead_list += o.middleware__middleware_comm_overhead_list

        return self

    def add(self, overhead: float, overhead_type: OverheadType):
        if overhead_type == OverheadType.SUPER_THING_INNER:
            self.super_thing_inner_overhead_list.append(overhead)
        elif overhead_type == OverheadType.TARGET_THING_INNER:
            self.target_thing_inner_overhead_list.append(overhead)
        elif overhead_type == OverheadType.MIDDLEWARE_INNER:
            self.middleware_inner_overhead_list.append(overhead)
        elif overhead_type == OverheadType.SUPER_THING__MIDDLEWARE_COMM:
            self.super_thing__middleware_comm_overhead_list.append(overhead)
        elif overhead_type == OverheadType.TARGET_THING__MIDDLEWARE_COMM:
            self.target_thing__middleware_comm_overhead_list.append(overhead)
        elif overhead_type == OverheadType.MIDDLEWARE__MIDDLEWARE_COMM:
            self.middleware__middleware_comm_overhead_list.append(overhead)

    def sum(self, overhead_type: OverheadType) -> float:
        if overhead_type == OverheadType.SUPER_THING_INNER:
            return sum([overhead.total_seconds() for overhead in self.super_thing_inner_overhead_list])
        elif overhead_type == OverheadType.TARGET_THING_INNER:
            return sum([overhead.total_seconds() for overhead in self.target_thing_inner_overhead_list])
        elif overhead_type == OverheadType.MIDDLEWARE_INNER:
            return sum([overhead.total_seconds() for overhead in self.middleware_inner_overhead_list])
        elif overhead_type == OverheadType.SUPER_THING__MIDDLEWARE_COMM:
            return sum([overhead.total_seconds() for overhead in self.super_thing__middleware_comm_overhead_list])
        elif overhead_type == OverheadType.TARGET_THING__MIDDLEWARE_COMM:
            return sum([overhead.total_seconds() for overhead in self.target_thing__middleware_comm_overhead_list])
        elif overhead_type == OverheadType.MIDDLEWARE__MIDDLEWARE_COMM:
            return sum([overhead.total_seconds() for overhead in self.middleware__middleware_comm_overhead_list])

    def avg(self, overhead_type: OverheadType) -> float:
        if overhead_type == OverheadType.SUPER_THING_INNER:
            return avg([overhead.total_seconds() for overhead in self.super_thing_inner_overhead_list])
        elif overhead_type == OverheadType.TARGET_THING_INNER:
            return avg([overhead.total_seconds() for overhead in self.target_thing_inner_overhead_list])
        elif overhead_type == OverheadType.MIDDLEWARE_INNER:
            return avg([overhead.total_seconds() for overhead in self.middleware_inner_overhead_list])
        elif overhead_type == OverheadType.SUPER_THING__MIDDLEWARE_COMM:
            return avg([overhead.total_seconds() for overhead in self.super_thing__middleware_comm_overhead_list])
        elif overhead_type == OverheadType.TARGET_THING__MIDDLEWARE_COMM:
            return avg([overhead.total_seconds() for overhead in self.target_thing__middleware_comm_overhead_list])
        elif overhead_type == OverheadType.MIDDLEWARE__MIDDLEWARE_COMM:
            return avg([overhead.total_seconds() for overhead in self.middleware__middleware_comm_overhead_list])

    def inner_overhead_total(self) -> float:
        return sum([overhead.total_seconds() for overhead in self.super_thing_inner_overhead_list]) + \
            sum([overhead.total_seconds() for overhead in self.middleware_inner_overhead_list])

    def comm_overhead_total(self) -> float:
        return sum([overhead.total_seconds() for overhead in self.super_thing__middleware_comm_overhead_list]) + \
            sum([overhead.total_seconds() for overhead in self.target_thing__middleware_comm_overhead_list]) + \
            sum([overhead.total_seconds() for overhead in self.middleware__middleware_comm_overhead_list])

    def overhead_total(self) -> float:
        return self.inner_overhead_total() + self.comm_overhead_total()


LOG_ORDER_MAP = {
    ProfileType.SCHEDULE: {
        SoPProtocolType.Super.CP_SCHEDULE: [
            {'direction': Direction.RECEIVED, 'element_type': SoPElementType.MIDDLEWARE, 'protocol': SoPProtocolType.Super.CP_SCHEDULE, 'overhead_type': OverheadType.MIDDLEWARE__MIDDLEWARE_COMM},
            {'direction': Direction.PUBLISH, 'element_type': SoPElementType.THING, 'protocol': SoPProtocolType.Super.MS_SCHEDULE, 'overhead_type': OverheadType.SUPER_THING__MIDDLEWARE_COMM},
            {'direction': Direction.PUBLISH, 'element_type': SoPElementType.MIDDLEWARE, 'protocol': SoPProtocolType.Super.CP_SCHEDULE, 'overhead_type': OverheadType.MIDDLEWARE_INNER},
        ],
        SoPProtocolType.Super.MS_SCHEDULE: [
            {'direction': Direction.RECEIVED, 'element_type': SoPElementType.THING, 'protocol': SoPProtocolType.Super.MS_SCHEDULE, 'overhead_type': OverheadType.SUPER_THING__MIDDLEWARE_COMM},
            {'direction': Direction.PUBLISH, 'element_type': SoPElementType.THING, 'protocol': SoPProtocolType.Super.SM_SCHEDULE, 'overhead_type': OverheadType.SUPER_THING_INNER},
        ],
        SoPProtocolType.Super.SM_SCHEDULE: [
            {'direction': Direction.RECEIVED, 'element_type': SoPElementType.MIDDLEWARE, 'protocol': SoPProtocolType.Super.SM_SCHEDULE, 'overhead_type': OverheadType.SUPER_THING__MIDDLEWARE_COMM},
            {'direction': Direction.PUBLISH, 'element_type': SoPElementType.MIDDLEWARE, 'protocol': SoPProtocolType.Super.PC_SCHEDULE, 'overhead_type': OverheadType.MIDDLEWARE_INNER},
        ],
        'fill it': [],
        SoPProtocolType.Super.CP_RESULT_SCHEDULE: [
            {'direction': Direction.RECEIVED, 'element_type': SoPElementType.MIDDLEWARE, 'protocol': SoPProtocolType.Super.CP_RESULT_SCHEDULE, 'overhead_type': OverheadType.TARGET_THING__MIDDLEWARE_COMM},
            {'direction': Direction.PUBLISH, 'element_type': SoPElementType.MIDDLEWARE, 'protocol': SoPProtocolType.Super.CP_RESULT_SCHEDULE, 'overhead_type': OverheadType.MIDDLEWARE_INNER},
            {'direction': Direction.PUBLISH, 'element_type': SoPElementType.MIDDLEWARE, 'protocol': SoPProtocolType.Super.CP_RESULT_SCHEDULE, 'overhead_type': OverheadType.MIDDLEWARE_INNER},
        ],
        SoPProtocolType.Super.MS_RESULT_SCHEDULE: [
            {'direction': Direction.RECEIVED, 'element_type': SoPElementType.THING, 'protocol': SoPProtocolType.Super.MS_RESULT_SCHEDULE, 'overhead_type': OverheadType.SUPER_THING__MIDDLEWARE_COMM},
            {'direction': Direction.PUBLISH, 'element_type': SoPElementType.THING, 'protocol': SoPProtocolType.Super.SM_SCHEDULE, 'overhead_type': OverheadType.SUPER_THING_INNER},
            {'direction': Direction.PUBLISH, 'element_type': SoPElementType.THING, 'protocol': SoPProtocolType.Super.SM_RESULT_SCHEDULE, 'overhead_type': OverheadType.SUPER_THING_INNER},
        ],
        SoPProtocolType.Super.SM_RESULT_SCHEDULE: [
            {'direction': Direction.RECEIVED, 'element_type': SoPElementType.MIDDLEWARE, 'protocol': SoPProtocolType.Super.SM_RESULT_SCHEDULE, 'overhead_type': OverheadType.SUPER_THING__MIDDLEWARE_COMM},
            {'direction': Direction.PUBLISH, 'element_type': SoPElementType.MIDDLEWARE, 'protocol': SoPProtocolType.Super.PC_RESULT_SCHEDULE, 'overhead_type': OverheadType.MIDDLEWARE_INNER},
        ],
        SoPProtocolType.Super.PC_RESULT_SCHEDULE: [
            {'direction': Direction.RECEIVED, 'element_type': SoPElementType.MIDDLEWARE, 'protocol': SoPProtocolType.Super.PC_RESULT_SCHEDULE, 'overhead_type': OverheadType.MIDDLEWARE__MIDDLEWARE_COMM},
            {'direction': Direction.PUBLISH, 'element_type': SoPElementType.MIDDLEWARE, 'protocol': SoPProtocolType.Super.PC_RESULT_SCHEDULE, 'overhead_type': OverheadType.MIDDLEWARE_INNER},
        ],
    },
    ProfileType.EXECUTE: {
        SoPProtocolType.Super.CP_EXECUTE: [
            {'direction': Direction.RECEIVED, 'element_type': SoPElementType.MIDDLEWARE, 'protocol': SoPProtocolType.Super.CP_EXECUTE, 'overhead_type': OverheadType.MIDDLEWARE__MIDDLEWARE_COMM},
            {'direction': Direction.PUBLISH, 'element_type': SoPElementType.MIDDLEWARE, 'protocol': SoPProtocolType.Super.CP_EXECUTE, 'overhead_type': OverheadType.MIDDLEWARE_INNER},
            {'direction': Direction.PUBLISH, 'element_type': SoPElementType.MIDDLEWARE, 'protocol': SoPProtocolType.Super.MS_EXECUTE, 'overhead_type': OverheadType.MIDDLEWARE_INNER},
        ],
        SoPProtocolType.Super.MS_EXECUTE: [
            {'direction': Direction.RECEIVED, 'element_type': SoPElementType.THING, 'protocol': SoPProtocolType.Super.MS_EXECUTE, 'overhead_type': OverheadType.SUPER_THING__MIDDLEWARE_COMM},
            {'direction': Direction.PUBLISH, 'element_type': SoPElementType.THING, 'protocol': SoPProtocolType.Super.SM_EXECUTE, 'overhead_type': OverheadType.SUPER_THING_INNER},
        ],
        SoPProtocolType.Super.SM_EXECUTE: [
            {'direction': Direction.RECEIVED, 'element_type': SoPElementType.MIDDLEWARE, 'protocol': SoPProtocolType.Super.SM_EXECUTE, 'overhead_type': OverheadType.SUPER_THING__MIDDLEWARE_COMM},
            {'direction': Direction.PUBLISH, 'element_type': SoPElementType.MIDDLEWARE, 'protocol': SoPProtocolType.Super.PC_EXECUTE, 'overhead_type': OverheadType.MIDDLEWARE_INNER},
        ],
        SoPProtocolType.Super.PC_EXECUTE: [
            {'direction': Direction.RECEIVED, 'element_type': SoPElementType.MIDDLEWARE, 'protocol': SoPProtocolType.Super.PC_EXECUTE, 'overhead_type': OverheadType.MIDDLEWARE__MIDDLEWARE_COMM},
            {'direction': Direction.PUBLISH, 'element_type': SoPElementType.MIDDLEWARE, 'protocol': SoPProtocolType.Super.PC_EXECUTE, 'overhead_type': OverheadType.MIDDLEWARE_INNER},
            {'direction': Direction.PUBLISH, 'element_type': SoPElementType.MIDDLEWARE, 'protocol': SoPProtocolType.Base.MT_EXECUTE, 'overhead_type': OverheadType.MIDDLEWARE_INNER},
        ],
        SoPProtocolType.Base.MT_EXECUTE: [
            {'direction': Direction.RECEIVED, 'element_type': SoPElementType.THING, 'protocol': SoPProtocolType.Base.MT_EXECUTE, 'overhead_type': OverheadType.TARGET_THING__MIDDLEWARE_COMM},
            {'direction': Direction.PUBLISH, 'element_type': SoPElementType.THING, 'protocol': SoPProtocolType.Base.TM_RESULT_EXECUTE, 'overhead_type': OverheadType.TARGET_THING_INNER},
        ],
        SoPProtocolType.Base.TM_RESULT_EXECUTE: [
            {'direction': Direction.RECEIVED, 'element_type': SoPElementType.MIDDLEWARE, 'protocol': SoPProtocolType.Base.TM_RESULT_EXECUTE, 'overhead_type': OverheadType.TARGET_THING__MIDDLEWARE_COMM},
            {'direction': Direction.PUBLISH, 'element_type': SoPElementType.MIDDLEWARE, 'protocol': SoPProtocolType.Super.CP_RESULT_EXECUTE, 'overhead_type': OverheadType.MIDDLEWARE_INNER},
        ],
        SoPProtocolType.Super.CP_RESULT_EXECUTE: [
            {'direction': Direction.RECEIVED, 'element_type': SoPElementType.MIDDLEWARE, 'protocol': SoPProtocolType.Super.CP_RESULT_EXECUTE, 'overhead_type': OverheadType.MIDDLEWARE__MIDDLEWARE_COMM},
            {'direction': Direction.PUBLISH, 'element_type': SoPElementType.MIDDLEWARE, 'protocol': SoPProtocolType.Super.CP_RESULT_EXECUTE, 'overhead_type': OverheadType.MIDDLEWARE_INNER},
            {'direction': Direction.PUBLISH, 'element_type': SoPElementType.MIDDLEWARE, 'protocol': SoPProtocolType.Super.MS_RESULT_EXECUTE, 'overhead_type': OverheadType.MIDDLEWARE_INNER},
        ],
        SoPProtocolType.Super.MS_RESULT_EXECUTE: [
            {'direction': Direction.RECEIVED, 'element_type': SoPElementType.THING, 'protocol': SoPProtocolType.Super.MS_RESULT_EXECUTE, 'overhead_type': OverheadType.SUPER_THING__MIDDLEWARE_COMM},
            {'direction': Direction.PUBLISH, 'element_type': SoPElementType.THING, 'protocol': SoPProtocolType.Super.SM_EXECUTE, 'overhead_type': OverheadType.SUPER_THING_INNER},
            {'direction': Direction.PUBLISH, 'element_type': SoPElementType.THING, 'protocol': SoPProtocolType.Super.SM_RESULT_EXECUTE, 'overhead_type': OverheadType.SUPER_THING_INNER},
        ],
        SoPProtocolType.Super.SM_RESULT_EXECUTE: [
            {'direction': Direction.RECEIVED, 'element_type': SoPElementType.MIDDLEWARE, 'protocol': SoPProtocolType.Super.SM_RESULT_EXECUTE, 'overhead_type': OverheadType.SUPER_THING__MIDDLEWARE_COMM},
            {'direction': Direction.PUBLISH, 'element_type': SoPElementType.MIDDLEWARE, 'protocol': SoPProtocolType.Super.PC_RESULT_EXECUTE, 'overhead_type': OverheadType.MIDDLEWARE_INNER},
        ],
        SoPProtocolType.Super.PC_RESULT_EXECUTE: [
            {'direction': Direction.RECEIVED, 'element_type': SoPElementType.MIDDLEWARE, 'protocol': SoPProtocolType.Super.PC_RESULT_EXECUTE, 'overhead_type': OverheadType.MIDDLEWARE__MIDDLEWARE_COMM},
            {'direction': Direction.PUBLISH, 'element_type': SoPElementType.MIDDLEWARE, 'protocol': SoPProtocolType.Super.PC_RESULT_EXECUTE, 'overhead_type': OverheadType.MIDDLEWARE_INNER},
        ],
    }
}


class LogLine:
    def __init__(self, timestamp: str, raw_log_data: str, get_topic_func: Callable, get_payload_func: Callable, element_type: SoPElementType, element_name: str) -> None:
        self._raw_log_data = raw_log_data
        self._get_topic_func = get_topic_func
        self._get_payload_func = get_payload_func
        self.element_type = element_type
        self.element_name = element_name

        self._timestamp = datetime.strptime(timestamp, TIMESTAMP_FORMAT)
        self.topic = self.get_topic(self.raw_log_data)
        self.payload = self.get_payload(self.raw_log_data)
        self.direction = self.get_direction(self.raw_log_data)
        self.protocol = SoPProtocolType.get(self.topic) if self.topic else None

        self.scenario = ''
        self.super_service = ''
        self.super_thing = ''
        self.super_middleware = ''
        self.target_service = ''
        self.target_thing = ''
        self.target_middleware = ''
        self.requester_middleware = ''

        # request_key = scenario@super_service@super_thing@requester_middleware
        self.request_key = ''
        # target_key = target_service@target_thing@target_middleware
        self.target_key = ''

    def topic_slice(self, order: int):
        if not self.topic:
            return False

        topic_slice_list = self.topic.split('/')
        if len(topic_slice_list) <= order:
            raise IndexError('topic_slice_list index out of range')

        return self.topic.split('/')[order]

    def get_topic(self, log_data: str) -> str:
        topic: str = self._get_topic_func(log_data)
        if not topic:
            return False

        return topic.strip()

    def get_payload(self, log_data: str) -> str:
        payload = self._get_payload_func(log_data)

        if not payload:
            return False

        # 만약 payload가 json 형식이라면 json 형식으로 변환
        pattern = re.compile(r'{[\s\S]*}')
        match = pattern.search(payload)
        if not match:
            return None

        payload = match.group()
        return payload.replace('\n', '').replace(' ', '').strip()

    def get_direction(self, log_data: str) -> Direction:
        if Direction.PUBLISH.value in log_data:
            direction = Direction.PUBLISH
        elif Direction.RECEIVED.value in log_data:
            direction = Direction.RECEIVED
        else:
            direction = None

        return direction

    @property
    def raw_log_data(self) -> str:
        return self._raw_log_data

    @raw_log_data.setter
    def raw_log_data(self, raw_log_data: str):
        self._raw_log_data = raw_log_data
        self.topic = self.get_topic(self._raw_log_data)
        self.payload = self.get_payload(self._raw_log_data)
        self.direction = self.get_direction(self._raw_log_data)

    @property
    def timestamp(self) -> dict:
        return self._timestamp

    @timestamp.setter
    def timestamp(self, timestamp: Union[str, datetime]):
        if isinstance(timestamp, str):
            self._timestamp = datetime.strptime(timestamp, TIMESTAMP_FORMAT)
        elif isinstance(timestamp, datetime):
            self._timestamp = timestamp
        else:
            raise TypeError('timestamp type must be str or datetime')

    def timestamp_str(self) -> str:
        return self._timestamp.strftime(TIMESTAMP_FORMAT)


class LogData:
    def __init__(self, log_path: str, timestamp_pattern: str, get_topic_func: Callable, get_payload_func: Callable, element_type: SoPElementType, element_name: str) -> None:
        self.log_path = log_path
        self.log_line_list: List[LogLine] = []
        self.element_type = element_type
        self.element_name = element_name

        self.init(self.log_path, timestamp_pattern=timestamp_pattern, get_topic_func=get_topic_func, get_payload_func=get_payload_func)

    def init(self, log_path: str, timestamp_pattern: str, get_topic_func: Callable, get_payload_func: Callable):
        with open(log_path, 'r') as f:
            raw_log_string = f.read()

        log_line_strings = re.split(timestamp_pattern, raw_log_string)[1:]
        for i in range(0, len(log_line_strings), 2):
            timestamp = log_line_strings[i]
            message = log_line_strings[i+1]
            log_line = LogLine(timestamp=timestamp, raw_log_data=message,
                               get_topic_func=get_topic_func, get_payload_func=get_payload_func,
                               element_type=self.element_type, element_name=self.element_name)
            self.log_line_list.append(log_line)


class MiddlewareLog:
    def __init__(self, log_path: str, level: int, name: str) -> None:
        self.level = level
        self.name = name

        self.log_data = LogData(log_path, timestamp_pattern=TIMESTAMP_REGEX,
                                get_topic_func=self.get_topic_func,
                                get_payload_func=self.get_payload_func,
                                element_type=SoPElementType.MIDDLEWARE,
                                element_name=self.name)

    def get_topic_func(self, log_data: str) -> str:
        if not ('[RECEIVED]' in log_data or '[PUBLISH]' in log_data):
            return False

        match = re.search(r'(?<=Topic: ).*', log_data)
        if match:
            topic = match.group(0)
        else:
            return False

        return topic

    def get_payload_func(self, log_data: str) -> str:
        match = re.search(r'(?<=Payload: )[\s\S]*', log_data)
        if match:
            payload = match.group(0)
        else:
            return False

        return payload


class ThingLog:
    def __init__(self, log_path: str, level: int, name: str, is_super: bool) -> None:
        self.level = level
        self.name = name
        self.is_super = is_super

        self.log_data = LogData(log_path, timestamp_pattern=TIMESTAMP_REGEX,
                                get_topic_func=self.get_topic_func,
                                get_payload_func=self.get_payload_func,
                                element_type=SoPElementType.THING,
                                element_name=self.name)

    def get_topic_func(self, log_data: str) -> str:
        match = re.search(r'topic: (.+?) payload: ([\s\S]*)', log_data)
        if match:
            topic = match.group(1)
        else:
            return False

        return topic

    def get_payload_func(self, log_data: str) -> str:
        match = re.search(r'topic: (.+?) payload: ([\s\S]*)', log_data)
        if match:
            payload = match.group(2)
        else:
            return False

        return payload


class Profiler:
    def __init__(self, root_log_folder_path: str):
        self.root_log_folder_path = root_log_folder_path
        self.middleware_log_list: List[MiddlewareLog] = []
        self.thing_log_list: List[ThingLog] = []
        self.super_service_table = {}
        self.overhead = Overhead()

        self.super_service_table: Dict[str, List[str]] = {}
        self.integrated_mqtt_msg_log_list: List[LogLine] = []

        self.whole_request_overhead_list: List[Overhead] = []

        self.init(self.root_log_folder_path)

    def init(self, root_log_folder_path: str):
        for root, dirs, files in os.walk(root_log_folder_path):

            for dir in dirs:
                if not len(dir.split('.')) == 3:
                    continue

                middleware_log = self.make_middleware_log(os.path.join(root, dir, 'middleware'))
                thing_log_list = self.make_thing_log_list(os.path.join(root, dir, 'thing'))
                self.middleware_log_list.append(middleware_log)
                self.thing_log_list.extend(thing_log_list)

        self.super_service_table = self.make_super_service_table()
        self.integrated_mqtt_msg_log_list: List[LogLine] = self.make_integrated_mqtt_msg_log_list()

        SOPLOG_DEBUG(f'Load simulation log from {root_log_folder_path} successfully', 'green')

    ##########################################################################################################################################

    def make_middleware_log(self, path: str) -> MiddlewareLog:
        file_list = os.listdir(path)
        for file in file_list:
            if not '.log' in file:
                continue
            middleware_name = file.split('.')[0]
            middleware_level = int(path.split(os.sep)[-2].split('.')[1].split('level')[1])
            middleware_log_path = os.path.join(path, file)
            middleware_log = MiddlewareLog(log_path=middleware_log_path, level=middleware_level, name=middleware_name)
            SOPLOG_DEBUG(f'Generate MiddlewareLog of middleware {middleware_log.log_data.element_name} from {file}', 'green')

            return middleware_log

    def make_thing_log_list(self, path: str) -> List[ThingLog]:
        try:
            file_list = os.listdir(path)
        except Exception as e:
            return []

        thing_log_list = []
        for file in file_list:
            if not '.log' in file:
                continue
            is_super = True if file.split('.')[0] == 'super_thing' else False
            thing_name = file.split('.')[1]
            thing_level = int(path.split(os.sep)[-2].split('.')[1].split('level')[1])
            thing_log_path = os.path.join(path, file)
            thing_log = ThingLog(log_path=thing_log_path, level=thing_level, name=thing_name, is_super=is_super)
            SOPLOG_DEBUG(f'Generate MiddlewareLog of middleware {thing_log.log_data.element_name} from {file}', 'green')

            thing_log_list.append(thing_log)

        return thing_log_list

    def make_integrated_raw_log_list(self) -> List[LogLine]:
        whole_raw_log_line_list: List[LogLine] = []
        for element_log in self.middleware_log_list + self.thing_log_list:
            for log_line in element_log.log_data.log_line_list:
                whole_raw_log_line_list.append(log_line)

        whole_raw_log_line_list.sort(key=lambda x: x.timestamp)
        return whole_raw_log_line_list

    def make_integrated_mqtt_msg_log_list(self) -> List[LogLine]:
        topic_filter = SUPER_PROTOCOL + SUPER_RESULT_PROTOCOL + SUB_PROTOCOL + SUB_RESULT_PROTOCOL + SUB_EXECUTE_PROTOCOL + SUB_EXECUTE_RESULT_PROTOCOL

        whole_raw_log_line_list = self.make_integrated_raw_log_list()

        whole_mqtt_msg_log_line_list: List[LogLine] = []
        for log_line in whole_raw_log_line_list:
            if not isinstance(log_line.topic, str):
                # if log line is not mqtt message, skip it
                continue
            if not log_line.protocol in topic_filter:
                # if log line's topic is not in target protocol, skip it
                continue
            if log_line.protocol in (SUB_EXECUTE_PROTOCOL + SUB_EXECUTE_RESULT_PROTOCOL) and len(log_line.topic.split('/')) <= 5:
                # if log line'protocol is execute, but not execute form super service(if execute is from local scenario), skip it
                continue
            whole_mqtt_msg_log_line_list.append(log_line)

        for log_line in whole_mqtt_msg_log_line_list:
            log_line_info = self.make_log_line_info(log_line)

            log_line.request_key = log_line_info['request_key']
            log_line.target_key = log_line_info['target_key']
            log_line.scenario = log_line_info['scenario']
            log_line.super_service = log_line_info['super_service']
            log_line.super_thing = log_line_info['super_thing']
            log_line.super_middleware = log_line_info['super_middleware']
            log_line.target_service = log_line_info['target_service']
            log_line.target_thing = log_line_info['target_thing']
            log_line.target_middleware = log_line_info['target_middleware']
            log_line.requester_middleware = log_line_info['requester_middleware']

        return whole_mqtt_msg_log_line_list

    def make_super_service_table(self) -> Dict[str, List[str]]:
        super_service_table = {}
        super_thing_log_list = [thing_log for thing_log in self.thing_log_list if thing_log.is_super]
        if len(super_thing_log_list) == 0:
            return False

        request_order = 0
        for super_thing_log in super_thing_log_list:
            for log_line in super_thing_log.log_data.log_line_list:
                if '✔✔✔' in log_line.raw_log_data:
                    break

                if "Detect super service" in log_line.raw_log_data:
                    request_order = 0
                    super_service = log_line.raw_log_data.split(":")[1].strip()
                    super_service_table[super_service] = []
                elif "sub_service" in log_line.raw_log_data:
                    sub_service = log_line.raw_log_data.split(":")[1].strip()
                    super_service_table[super_service].append((sub_service, request_order))
                    request_order += 1

        return super_service_table

    def make_log_line_info(self, log_line: LogLine) -> dict:
        topic = log_line.topic
        payload = json_string_to_dict(log_line.payload)

        super_service = ''
        super_thing = ''
        super_middleware = ''

        target_service = ''
        target_thing = ''
        target_middleware = ''

        request_key = ''
        target_key = ''

        if log_line.protocol in SUPER_PROTOCOL:
            super_service = topic.split('/')[2]
            super_thing = topic.split('/')[3]
            requester_middleware = topic.split('/')[5]
            super_middleware = topic.split('/')[4]
        elif log_line.protocol in SUPER_RESULT_PROTOCOL:
            super_service = topic.split('/')[3]
            super_thing = topic.split('/')[4]
            requester_middleware = topic.split('/')[6]
            super_middleware = topic.split('/')[5]
        elif log_line.protocol in SUB_PROTOCOL:
            requester_middleware = topic.split('/')[5].split('@')[0]
            super_thing = topic.split('/')[5].split('@')[1]
            super_service = topic.split('/')[5].split('@')[2]
            target_middleware = topic.split('/')[4]
            target_service = topic.split('/')[2]
            # request_order = topic.split('/')[5].split('@')[3]
        elif log_line.protocol in SUB_RESULT_PROTOCOL:
            requester_middleware = topic.split('/')[6].split('@')[0]
            super_thing = topic.split('/')[6].split('@')[1]
            super_service = topic.split('/')[6].split('@')[2]
            target_middleware = topic.split('/')[5]
            target_service = topic.split('/')[3]
            # request_order = topic.split('/')[6].split('@')[3]
        elif log_line.protocol in SUB_EXECUTE_PROTOCOL:
            if len(topic.split('/')) <= 5:
                request_key = ''
            else:
                requester_middleware = topic.split('/')[5].split('@')[0]
                super_thing = topic.split('/')[5].split('@')[1]
                super_service = topic.split('/')[5].split('@')[2]
                target_middleware = topic.split('/')[4]
                target_service = topic.split('/')[2]
                target_thing = topic.split('/')[3]
                # request_order = topic.split('/')[5].split('@')[3]
        elif log_line.protocol in SUB_EXECUTE_RESULT_PROTOCOL:
            if len(topic.split('/')) <= 5:
                request_key = ''
            else:
                requester_middleware = topic.split('/')[6].split('@')[0]
                super_thing = topic.split('/')[6].split('@')[1]
                super_service = topic.split('/')[6].split('@')[2]
                target_middleware = topic.split('/')[5]
                target_service = topic.split('/')[3]
                target_thing = topic.split('/')[4]
                # request_order = topic.split('/')[6].split('@')[3]

        scenario = payload['scenario']
        requester_middleware = '_'.join(requester_middleware.split('_')[:-1])
        request_key = '@'.join([scenario, super_service, super_thing, requester_middleware])
        target_key = '@'.join([target_service, target_thing, target_middleware])

        return dict(request_key=request_key, target_key=target_key,
                    scenario=scenario,
                    super_service=super_service, super_thing=super_thing, super_middleware=super_middleware,
                    target_service=target_service, target_thing=target_thing, target_middleware=target_middleware,
                    requester_middleware=requester_middleware)

    def make_log_string(self, duration: timedelta, log_line: LogLine) -> str:
        timestamp = log_line.timestamp_str()
        direction = log_line.direction.value
        element_name = log_line.element_name
        topic = log_line.topic
        payload = log_line.payload

        log_string = f'({duration.total_seconds()*1e3:8.3f} ms)[{timestamp}][{direction:<8}] {element_name} {topic} {payload}\n'
        return log_string

    def export_to_file(self, log_file_name: str, request_log_list: List[LogLine]):
        with open(log_file_name, 'w') as f:
            for i, log_line in enumerate(request_log_list):
                duration = (request_log_list[i].timestamp - request_log_list[i-1].timestamp) if i > 0 else timedelta(seconds=0)
                log_string = self.make_log_string(duration, log_line)
                f.write(log_string)

        SOPLOG_DEBUG(f'Write {log_file_name}...', 'yellow')

    ##########################################################################################################################################

    def collect_request_start_log_list(self, super_service: str, profile_type: ProfileType) -> List[LogLine]:
        if profile_type == ProfileType.SCHEDULE:
            start_protocol = SoPProtocolType.Super.CP_SCHEDULE
        elif profile_type == ProfileType.EXECUTE:
            start_protocol = SoPProtocolType.Super.CP_EXECUTE
        else:
            raise Exception(f"Invalid profile type: {profile_type}")

        request_start_log_list: List[LogLine] = []
        for log_line in self.integrated_mqtt_msg_log_list:
            if log_line.protocol != start_protocol:
                continue
            if log_line.element_type != SoPElementType.MIDDLEWARE:
                continue
            if log_line.element_name != log_line.requester_middleware:
                continue
            if super_service != log_line.topic_slice(2):
                continue

            request_start_log_list.append(log_line)

        if len(request_start_log_list) == 0:
            SOPLOG_DEBUG(f"Cannot find super service start log for {super_service}", 'yellow')
            return []

        # first & last loop of request is not valid
        return request_start_log_list[1:-1]

    def collect_target_start_log_list(self, target_service: str, request_log_list: List[LogLine], profile_type: ProfileType) -> List[LogLine]:
        if profile_type == ProfileType.SCHEDULE:
            start_protocol = SoPProtocolType.Super.SM_SCHEDULE
        elif profile_type == ProfileType.EXECUTE:
            start_protocol = SoPProtocolType.Super.SM_EXECUTE
        else:
            raise Exception(f"Invalid profile type: {profile_type}")

        target_start_log_list: List[LogLine] = []
        for log_line in request_log_list:
            if log_line.protocol != start_protocol:
                continue
            if log_line.element_type != SoPElementType.THING:
                continue
            # execute에 대해서도 target_log_list를 뽑아야하지만 현재 result list기능이 구현되지 않아 single에 대한 것에 대해서만 대응한다.
            # if profile_type == ProfileType.EXECUTE and '@'.join([target_service, target_thing]) != log_line.target_key:
            #     continue
            if profile_type == ProfileType.SCHEDULE and ScheduleStatus.CHECK.value != json_string_to_dict(log_line.payload)['status'].lower():
                continue

            target_start_log_list.append(log_line)

        if len(target_start_log_list) == 0:
            SOPLOG_DEBUG(f"Cannot find target start log for {target_key}", 'yellow')
            return []

        return target_start_log_list

    ##########################################################################################################################################

    def get_request_log_list(self, super_service_start_log: LogLine, profile_type: ProfileType) -> List[LogLine]:
        if profile_type == ProfileType.SCHEDULE:
            protocol_filter = SCHEDULE_PROTOCOL
        elif profile_type == ProfileType.EXECUTE:
            protocol_filter = EXECUTE_PROTOCOL
        else:
            raise Exception(f"Invalid profile type: {profile_type}")

        log_range = self.get_logs_time_range(self.integrated_mqtt_msg_log_list, super_service_start_log.timestamp - timedelta(milliseconds=3))
        request_log_list: List[LogLine] = []
        for log_line in log_range:
            if not log_line.protocol in protocol_filter:
                continue
            # get same request log list
            if log_line.request_key != super_service_start_log.request_key:
                continue
            # exclude irrelevant logs with this request
            if log_line.element_type == SoPElementType.MIDDLEWARE:
                if log_line.protocol in SUPER_PROTOCOL + SUPER_RESULT_PROTOCOL and not log_line.element_name in log_line.requester_middleware:
                    continue
                elif log_line.protocol in SUB_PROTOCOL + SUB_RESULT_PROTOCOL and not log_line.element_name in log_line.target_middleware:
                    continue

            request_log_list.append(log_line)

        cut_request_log_list: List[LogLine] = []
        for log_line in request_log_list:
            cut_request_log_list.append(log_line)
            if log_line.protocol in PC_RESULT_PROTOCOL and log_line.requester_middleware == log_line.element_name:
                break

        return cut_request_log_list

    def get_target_log_list(self, target_start_log: LogLine, request_log_list: List[LogLine], profile_type: ProfileType) -> List[LogLine]:
        if profile_type == ProfileType.SCHEDULE:
            protocol_filter = SCHEDULE_PROTOCOL
        elif profile_type == ProfileType.EXECUTE:
            protocol_filter = EXECUTE_PROTOCOL
        else:
            raise Exception(f"Invalid profile type: {profile_type}")

        log_range = self.get_logs_time_range(request_log_list, target_start_log.timestamp - timedelta(milliseconds=3))
        target_log_list: List[LogLine] = []
        for log_line in log_range:
            if not log_line.protocol in protocol_filter:
                continue

    def get_logs_time_range(self, log_data: List[LogLine], start_time: datetime = None, end_time: datetime = None) -> List[LogLine]:
        if start_time == None:
            start_time = datetime.min
        if end_time == None:
            end_time = datetime.max

        return [log_line for log_line in log_data if start_time <= log_line.timestamp <= end_time]

    def get_windowed_log_list(self, request_log_list: List[LogLine], target_log_line, before: int = 3, after: int = 3) -> List[LogLine]:
        target_log_index = request_log_list.index(target_log_line)
        index1 = target_log_index-before if target_log_index-before >= 0 else 0
        index2 = target_log_index+after+1 if target_log_index+after+1 <= len(request_log_list) else len(request_log_list)
        log_window = request_log_list[index1:index2]
        return log_window

    ##########################################################################################################################################

    def check_next_log_valid(self, curr_log_line: LogLine, next_log_line: LogLine, profile_type: ProfileType) -> Union[OverheadType, bool]:
        filter_list = LOG_ORDER_MAP[profile_type][curr_log_line.protocol]
        for filter in filter_list:
            direction_check = (filter['direction'] == next_log_line.direction)
            element_type_check = (filter['element_type'] == next_log_line.element_type)
            protocol_check = (filter['protocol'] == next_log_line.protocol)

            overhead_type = filter['overhead_type']
            if direction_check and element_type_check and protocol_check:
                return overhead_type

        return False

    def find_valid_next_log(self, curr_log_line: LogLine, request_log_list: List[LogLine], profile_type: ProfileType) -> LogLine:
        log_window = self.get_windowed_log_list(request_log_list=request_log_list, target_log_line=curr_log_line, before=3, after=3)
        for log_line in log_window:
            overhead_type = self.check_next_log_valid(curr_log_line=curr_log_line, next_log_line=log_line, profile_type=profile_type)
            if overhead_type:
                return log_line

    ##########################################################################################################################################

    def get_avg_overhead(self, overhead_type: OverheadType = None) -> float:
        if overhead_type == None:
            return sum([overhead.overhead_total() for overhead in self.whole_request_overhead_list]) / len(self.whole_request_overhead_list)
        elif overhead_type == OverheadType.INNER:
            return sum([overhead.inner_overhead_total() for overhead in self.whole_request_overhead_list]) / len(self.whole_request_overhead_list)
        elif overhead_type == OverheadType.COMM:
            return sum([overhead.comm_overhead_total() for overhead in self.whole_request_overhead_list]) / len(self.whole_request_overhead_list)
        else:
            whole_overhead = Overhead()
            for overhead in self.whole_request_overhead_list:
                whole_overhead += overhead
            return whole_overhead.avg(overhead_type)

    def profile(self, profile_type: ProfileType, export: bool = False) -> Tuple[Overhead, float]:
        if not profile_type in [ProfileType.SCHEDULE, ProfileType.EXECUTE]:
            raise Exception(f"Invalid profile type: {profile_type}")

        self.whole_request_overhead_list = []
        for super_service in self.super_service_table:
            request_overhead_list = self.profile_super_service(super_service, profile_type, export=export)
            self.whole_request_overhead_list.extend(request_overhead_list)

    def profile_super_service(self, super_service: str, profile_type: ProfileType, export: bool = False) -> List[Overhead]:
        # 같은 super service에 대한 request가 여러개가 존재한다. 각 요청에 대해서 오버헤드를 계산한다.
        request_start_log_list = self.collect_request_start_log_list(super_service, profile_type=profile_type)
        request_overhead_list: List[Overhead] = []
        for i, request_start_log in enumerate(request_start_log_list):
            request_log_list: List[LogLine] = self.get_request_log_list(request_start_log, profile_type=profile_type)
            request_overhead = self.profile_request(request_log_list=request_log_list, profile_type=profile_type)
            request_overhead_list.append(request_overhead)

            if export:
                self.export_to_file(log_file_name=f'log_{super_service}_request_{i}.txt', request_log_list=request_log_list)

        return request_overhead_list

    def profile_request(self, request_log_list: List[LogLine], profile_type: ProfileType) -> Overhead:
        request_overhead = Overhead()

        for i, log_line in enumerate(request_log_list[:-1]):
            curr_log_line = log_line
            next_log_line = request_log_list[i+1]

            if curr_log_line.protocol == SoPProtocolType.Super.SM_SCHEDULE:
                target_start_log_list = self.collect_target_start_log_list(target_service=curr_log_line.target_service, request_log_list=request_log_list, profile_type=profile_type)
                for target_start_log in target_start_log_list:
                    target_log_list = self.get_target_log_list(target_start_log=target_start_log, request_log_list=request_log_list, profile_type=profile_type)
                    self.profile_target(target_log_list=target_log_list, profile_type=profile_type)
            else:
                overhead_type = self.check_next_log_valid(curr_log_line=curr_log_line, next_log_line=next_log_line, profile_type=profile_type)
                if not overhead_type:
                    # 다음 인덱스의 로그가 올바르지 않은 로그인 경우(순서가 제대로 되어있지 않는 경우) 짝에 맞는 로그를 window 범위에서 찾는다.
                    next_log_line = self.find_valid_next_log(curr_log_line=curr_log_line, request_log_list=request_log_list, profile_type=profile_type)
                    overhead_type = self.check_next_log_valid(curr_log_line=curr_log_line, next_log_line=next_log_line, profile_type=profile_type)

                overhead = next_log_line.timestamp - curr_log_line.timestamp
                request_overhead.add(overhead=overhead, overhead_type=overhead_type)

        SOPLOG_DEBUG(f'Profile request: {request_log_list[0].request_key} complete!', 'yellow')
        SOPLOG_DEBUG(f'=== Result=== \n{str(request_overhead)}', 'green')
        return request_overhead

    def profile_target(self, target_log_list: List[LogLine], profile_type: ProfileType) -> Overhead:
        target_overhead = Overhead()

        # TODO

        return target_overhead
