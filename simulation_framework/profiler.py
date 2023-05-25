from simulation_framework.core.elements import *
from abc import ABCMeta, abstractmethod

from big_thing_py.common.soptype import SoPProtocolType
from big_thing_py.common.common import Direction

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


class ProfileErrorCode(Enum):
    INVALID_REQUEST = auto()
    INVALID_LOG = auto()
    TOO_HIGH_OVERHEAD = auto()


class OverheadType(Enum):
    SUPER_THING_INNER = auto()
    TARGET_THING_INNER = auto()
    MIDDLEWARE_INNER = auto()
    SUPER_THING__MIDDLEWARE_COMM = auto()
    TARGET_THING__MIDDLEWARE_COMM = auto()
    MIDDLEWARE__MIDDLEWARE_COMM = auto()
    INNER = auto()
    COMM = auto()
    ALL = auto()


class ProfileType(Enum):
    SCHEDULE = auto()
    EXECUTE = auto()


class ScheduleStatus(Enum):
    CHECK = 'check'
    CONFIRM = 'confirm'


########################################################################################################################


def find_json_pattern(payload: str) -> str:
    # 만약 payload가 json 형식이라면 json 형식으로 변환
    pattern = re.compile(r'{[\s\S]*}')
    match = pattern.search(payload)
    if not match:
        return False

    payload = match.group()
    return payload.replace('\n', '').replace(' ', '').strip()

########################################################################################################################


class ProfileResult:

    def __init__(self) -> None:
        self.request_overhead_list: List[RequestOverhead] = []

    def add(self, request_overhead: 'RequestOverhead'):
        self.request_overhead_list.append(request_overhead)

    def avg_overhead(self, filter: dict) -> timedelta:
        target_overhead_list: List[Overhead] = []
        for request_overhead in self.request_overhead_list:
            target_overhead_list.extend(request_overhead.collect_overhead(filter))

        result = avg_timedelta([overhead.duration for overhead in target_overhead_list])
        return result

    def avg_total_duration(self) -> timedelta:
        avg_duration = timedelta()
        for request_overhead in self.request_overhead_list:
            target_overhead_list = request_overhead.overhead_list
            request_duration = sum([overhead.duration for overhead in target_overhead_list], timedelta())
            avg_duration += request_duration
        avg_duration = avg_duration / len(self.request_overhead_list)
        return avg_duration

    def avg_total_overhead(self) -> timedelta:
        return self.avg_total_inner_overhead() + self.avg_total_comm_overhead()

    def avg_total_inner_overhead(self) -> timedelta:
        avg_overhead = timedelta()
        for request_overhead in self.request_overhead_list:
            target_overhead_list = request_overhead.collect_overhead(filter=dict(type=OverheadType.INNER))
            inner_duration_sum = sum([overhead.duration for overhead in target_overhead_list], timedelta())
            avg_overhead += inner_duration_sum
        avg_overhead = avg_overhead / len(self.request_overhead_list)
        return avg_overhead

    def avg_total_comm_overhead(self) -> timedelta:
        avg_overhead = timedelta()
        for request_overhead in self.request_overhead_list:
            target_overhead_list = request_overhead.collect_overhead(filter=dict(type=OverheadType.COMM))
            comm_duration_sum = sum([overhead.duration for overhead in target_overhead_list], timedelta())
            avg_overhead += comm_duration_sum
        avg_overhead = avg_overhead / len(self.request_overhead_list)
        return avg_overhead

    def avg_total_middleware_inner_overhead(self) -> timedelta:
        avg_overhead = timedelta()
        for request_overhead in self.request_overhead_list:
            target_overhead_list = request_overhead.collect_overhead(filter=dict(type=OverheadType.MIDDLEWARE_INNER))
            inner_duration_sum = sum([overhead.duration for overhead in target_overhead_list], timedelta())
            avg_overhead += inner_duration_sum
        avg_overhead = avg_overhead / len(self.request_overhead_list)
        return avg_overhead

    def avg_total_super_thing_inner_overhead(self) -> timedelta:
        avg_overhead = timedelta()
        for request_overhead in self.request_overhead_list:
            target_overhead_list = request_overhead.collect_overhead(filter=dict(type=OverheadType.SUPER_THING_INNER))
            inner_duration_sum = sum([overhead.duration for overhead in target_overhead_list], timedelta())
            avg_overhead += inner_duration_sum
        avg_overhead = avg_overhead / len(self.request_overhead_list)
        return avg_overhead

    def avg_total_target_thing_inner_overhead(self) -> timedelta:
        avg_overhead = timedelta()
        for request_overhead in self.request_overhead_list:
            target_overhead_list = request_overhead.collect_overhead(filter=dict(type=OverheadType.TARGET_THING_INNER))
            inner_duration_sum = sum([overhead.duration for overhead in target_overhead_list], timedelta())
            avg_overhead += inner_duration_sum
        avg_overhead = avg_overhead / len(self.request_overhead_list)
        return avg_overhead

    def avg_total_middleware__middleware_comm_overhead(self) -> timedelta:
        avg_overhead = timedelta()
        for request_overhead in self.request_overhead_list:
            target_overhead_list = request_overhead.collect_overhead(filter=dict(type=OverheadType.MIDDLEWARE__MIDDLEWARE_COMM))
            inner_duration_sum = sum([overhead.duration for overhead in target_overhead_list], timedelta())
            avg_overhead += inner_duration_sum
        avg_overhead = avg_overhead / len(self.request_overhead_list)
        return avg_overhead

    def avg_total_super_thing__middleware_comm_overhead(self) -> timedelta:
        avg_overhead = timedelta()
        for request_overhead in self.request_overhead_list:
            target_overhead_list = request_overhead.collect_overhead(filter=dict(type=OverheadType.SUPER_THING__MIDDLEWARE_COMM))
            inner_duration_sum = sum([overhead.duration for overhead in target_overhead_list], timedelta())
            avg_overhead += inner_duration_sum
        avg_overhead = avg_overhead / len(self.request_overhead_list)
        return avg_overhead

    def avg_total_target_thing__middleware_comm_overhead(self) -> timedelta:
        avg_overhead = timedelta()
        for request_overhead in self.request_overhead_list:
            target_overhead_list = request_overhead.collect_overhead(filter=dict(type=OverheadType.TARGET_THING__MIDDLEWARE_COMM))
            inner_duration_sum = sum([overhead.duration for overhead in target_overhead_list], timedelta())
            avg_overhead += inner_duration_sum
        avg_overhead = avg_overhead / len(self.request_overhead_list)
        return avg_overhead


class RequestOverhead:

    def __init__(self, request_key: str) -> None:
        self.overhead_list: List[Overhead] = []
        self.request_key = request_key

    def add(self, overhead: 'Overhead'):
        self.overhead_list.append(overhead)

    def collect_overhead(self, filter: dict) -> List['Overhead']:
        overhead_type_filter = filter.get('type')
        element_name_from_filter = filter.get('element_name_from')
        element_type_from_filter = filter.get('element_type_from')
        protocol_from_filter = filter.get('protocol_from')
        level_from_filter = filter.get('level_from')
        element_name_to_filter = filter.get('element_name_to')
        element_type_to_filter = filter.get('element_type_to')
        protocol_to_filter = filter.get('protocol_to')
        level_to_filter = filter.get('level_to')

        if overhead_type_filter == OverheadType.ALL:
            overhead_type_filter = list(OverheadType)
        elif overhead_type_filter == OverheadType.INNER:
            overhead_type_filter = [OverheadType.MIDDLEWARE_INNER, OverheadType.SUPER_THING_INNER]
        elif overhead_type_filter == OverheadType.COMM:
            overhead_type_filter = [OverheadType.MIDDLEWARE__MIDDLEWARE_COMM, OverheadType.SUPER_THING__MIDDLEWARE_COMM, OverheadType.TARGET_THING__MIDDLEWARE_COMM]
        else:
            overhead_type_filter = [overhead_type_filter]

        target_overhead_list: List[Overhead] = []
        for overhead in self.overhead_list:
            if overhead_type_filter and not overhead.type in overhead_type_filter:
                continue
            if element_name_from_filter and overhead.element_name_from != element_name_from_filter:
                continue
            if element_type_from_filter and overhead.element_type_from != element_type_from_filter:
                continue
            if protocol_from_filter and overhead.protocol_from != protocol_from_filter:
                continue
            if level_from_filter and overhead.level_from != level_from_filter:
                continue
            if element_name_to_filter and overhead.element_name_to != element_name_to_filter:
                continue
            if element_type_to_filter and overhead.element_type_to != element_type_to_filter:
                continue
            if protocol_to_filter and overhead.protocol_to != protocol_to_filter:
                continue
            if level_to_filter and overhead.level_to != level_to_filter:
                continue
            target_overhead_list.append(overhead)

        return target_overhead_list


class Overhead:

    def __init__(self, duration: timedelta = timedelta(), overhead_type: OverheadType = None,
                 element_name_from: str = None, element_type_from: SoPElementType = None, level_from: int = None, protocol_from: SoPProtocolType = None,
                 element_name_to: str = None, element_type_to: SoPElementType = None, level_to: int = None, protocol_to: SoPProtocolType = None) -> None:
        self.duration = duration
        self.type = overhead_type
        self.element_name_from: str = element_name_from
        self.element_type_from: SoPElementType = element_type_from
        self.protocol_from: SoPElementType = protocol_from
        self.level_from: int = level_from
        self.element_name_to: str = element_name_to
        self.element_type_to: SoPElementType = element_type_to
        self.protocol_to: SoPElementType = protocol_to
        self.level_to: int = level_to


LOG_ORDER_MAP = {
    ProfileType.SCHEDULE: {
        SoPProtocolType.Super.CP_SCHEDULE: {
            Direction.RECEIVED: [
                {'direction': Direction.PUBLISH, 'element_type': SoPElementType.THING, 'protocol': SoPProtocolType.Super.MS_SCHEDULE, 'overhead_type': OverheadType.SUPER_THING__MIDDLEWARE_COMM},
                {'direction': Direction.PUBLISH, 'element_type': SoPElementType.MIDDLEWARE, 'protocol': SoPProtocolType.Super.CP_SCHEDULE, 'overhead_type': OverheadType.MIDDLEWARE_INNER},
            ],
            Direction.PUBLISH: [
                {'direction': Direction.RECEIVED, 'element_type': SoPElementType.MIDDLEWARE, 'protocol': SoPProtocolType.Super.CP_SCHEDULE, 'overhead_type': OverheadType.MIDDLEWARE__MIDDLEWARE_COMM},
            ],
        },
        SoPProtocolType.Super.MS_SCHEDULE: {
            Direction.RECEIVED: [
                {'direction': Direction.PUBLISH, 'element_type': SoPElementType.THING, 'protocol': SoPProtocolType.Super.SM_SCHEDULE, 'overhead_type': OverheadType.SUPER_THING_INNER},
            ],
            Direction.PUBLISH: [
                {'direction': Direction.RECEIVED, 'element_type': SoPElementType.THING, 'protocol': SoPProtocolType.Super.MS_SCHEDULE, 'overhead_type': OverheadType.SUPER_THING__MIDDLEWARE_COMM},
            ],
        },
        SoPProtocolType.Super.SM_SCHEDULE: {
            Direction.RECEIVED: [
                {'direction': Direction.PUBLISH, 'element_type': SoPElementType.MIDDLEWARE, 'protocol': SoPProtocolType.Super.PC_SCHEDULE, 'overhead_type': OverheadType.MIDDLEWARE_INNER},
            ],
            Direction.PUBLISH: [
                {'direction': Direction.RECEIVED, 'element_type': SoPElementType.MIDDLEWARE, 'protocol': SoPProtocolType.Super.SM_SCHEDULE, 'overhead_type': OverheadType.SUPER_THING__MIDDLEWARE_COMM},
            ],
        },
        SoPProtocolType.Super.CP_RESULT_SCHEDULE: {
            Direction.RECEIVED: [
                {'direction': Direction.PUBLISH, 'element_type': SoPElementType.MIDDLEWARE, 'protocol': SoPProtocolType.Super.CP_RESULT_SCHEDULE, 'overhead_type': OverheadType.MIDDLEWARE_INNER},
                {'direction': Direction.PUBLISH, 'element_type': SoPElementType.MIDDLEWARE, 'protocol': SoPProtocolType.Super.CP_RESULT_SCHEDULE, 'overhead_type': OverheadType.MIDDLEWARE_INNER},
            ],
            Direction.PUBLISH: [
                {'direction': Direction.RECEIVED, 'element_type': SoPElementType.MIDDLEWARE, 'protocol': SoPProtocolType.Super.CP_RESULT_SCHEDULE, 'overhead_type': OverheadType.TARGET_THING__MIDDLEWARE_COMM},
            ],
        },
        SoPProtocolType.Super.MS_RESULT_SCHEDULE: {
            Direction.RECEIVED: [
                {'direction': Direction.PUBLISH, 'element_type': SoPElementType.THING, 'protocol': SoPProtocolType.Super.SM_SCHEDULE, 'overhead_type': OverheadType.SUPER_THING_INNER},
                {'direction': Direction.PUBLISH, 'element_type': SoPElementType.THING, 'protocol': SoPProtocolType.Super.SM_RESULT_SCHEDULE, 'overhead_type': OverheadType.SUPER_THING_INNER},
            ],
            Direction.PUBLISH: [
                {'direction': Direction.RECEIVED, 'element_type': SoPElementType.THING, 'protocol': SoPProtocolType.Super.MS_RESULT_SCHEDULE, 'overhead_type': OverheadType.SUPER_THING__MIDDLEWARE_COMM},
            ],
        },
        SoPProtocolType.Super.SM_RESULT_SCHEDULE: {
            Direction.RECEIVED: [
                {'direction': Direction.PUBLISH, 'element_type': SoPElementType.MIDDLEWARE, 'protocol': SoPProtocolType.Super.PC_RESULT_SCHEDULE, 'overhead_type': OverheadType.MIDDLEWARE_INNER},
            ],
            Direction.PUBLISH: [
                {'direction': Direction.RECEIVED, 'element_type': SoPElementType.MIDDLEWARE, 'protocol': SoPProtocolType.Super.SM_RESULT_SCHEDULE, 'overhead_type': OverheadType.SUPER_THING__MIDDLEWARE_COMM},
            ],
        },
        SoPProtocolType.Super.PC_RESULT_SCHEDULE: {
            Direction.RECEIVED: [
                {'direction': Direction.PUBLISH, 'element_type': SoPElementType.MIDDLEWARE, 'protocol': SoPProtocolType.Super.PC_RESULT_SCHEDULE, 'overhead_type': OverheadType.MIDDLEWARE_INNER},
            ],
            Direction.PUBLISH: [
                {'direction': Direction.RECEIVED, 'element_type': SoPElementType.MIDDLEWARE, 'protocol': SoPProtocolType.Super.PC_RESULT_SCHEDULE, 'overhead_type': OverheadType.MIDDLEWARE__MIDDLEWARE_COMM},
            ],
        }
    },
    ProfileType.EXECUTE: {
        SoPProtocolType.Super.CP_EXECUTE: {
            Direction.RECEIVED: [
                {'direction': Direction.PUBLISH, 'element_type': SoPElementType.MIDDLEWARE, 'protocol': SoPProtocolType.Super.CP_EXECUTE,
                 'level_change': None, 'element_change': None, 'overhead_type': OverheadType.MIDDLEWARE_INNER},
                {'direction': Direction.PUBLISH, 'element_type': SoPElementType.MIDDLEWARE, 'protocol': SoPProtocolType.Super.MS_EXECUTE,
                 'level_change': None, 'element_change': None, 'overhead_type': OverheadType.MIDDLEWARE_INNER},
            ],
            Direction.PUBLISH: [
                {'direction': Direction.RECEIVED, 'element_type': SoPElementType.MIDDLEWARE, 'protocol': SoPProtocolType.Super.CP_EXECUTE,
                 'level_change': 'up', 'element_change': None, 'overhead_type': OverheadType.MIDDLEWARE__MIDDLEWARE_COMM},
            ],
        },
        SoPProtocolType.Super.MS_EXECUTE: {
            Direction.RECEIVED: [
                {'direction': Direction.PUBLISH, 'element_type': SoPElementType.THING, 'protocol': SoPProtocolType.Super.SM_EXECUTE,
                 'level_change': None, 'element_change': None, 'overhead_type': OverheadType.SUPER_THING_INNER},
            ],
            Direction.PUBLISH: [
                {'direction': Direction.RECEIVED, 'element_type': SoPElementType.THING, 'protocol': SoPProtocolType.Super.MS_EXECUTE,
                 'level_change': None, 'element_change': (SoPElementType.MIDDLEWARE, SoPElementType.THING), 'overhead_type': OverheadType.SUPER_THING__MIDDLEWARE_COMM},
            ]
        },
        SoPProtocolType.Super.SM_EXECUTE: {
            Direction.RECEIVED: [
                {'direction': Direction.PUBLISH, 'element_type': SoPElementType.MIDDLEWARE, 'protocol': SoPProtocolType.Super.PC_EXECUTE,
                 'level_change': None, 'element_change': None, 'overhead_type': OverheadType.MIDDLEWARE_INNER},
            ],
            Direction.PUBLISH: [
                {'direction': Direction.RECEIVED, 'element_type': SoPElementType.MIDDLEWARE, 'protocol': SoPProtocolType.Super.SM_EXECUTE,
                 'level_change': None, 'element_change': (SoPElementType.THING, SoPElementType.MIDDLEWARE), 'overhead_type': OverheadType.SUPER_THING__MIDDLEWARE_COMM},
            ]
        },
        SoPProtocolType.Super.PC_EXECUTE: {
            Direction.RECEIVED: [
                {'direction': Direction.PUBLISH, 'element_type': SoPElementType.MIDDLEWARE, 'protocol': SoPProtocolType.Super.PC_EXECUTE,
                 'level_change': None, 'element_change': None, 'overhead_type': OverheadType.MIDDLEWARE_INNER},
                {'direction': Direction.PUBLISH, 'element_type': SoPElementType.MIDDLEWARE, 'protocol': SoPProtocolType.Base.MT_EXECUTE,
                 'level_change': None, 'element_change': None, 'overhead_type': OverheadType.MIDDLEWARE_INNER},
            ],
            Direction.PUBLISH: [
                {'direction': Direction.RECEIVED, 'element_type': SoPElementType.MIDDLEWARE, 'protocol': SoPProtocolType.Super.PC_EXECUTE,
                 'level_change': 'down', 'element_change': None, 'overhead_type': OverheadType.MIDDLEWARE__MIDDLEWARE_COMM},
            ]
        },
        SoPProtocolType.Base.MT_EXECUTE: {
            Direction.RECEIVED: [
                {'direction': Direction.PUBLISH, 'element_type': SoPElementType.THING, 'protocol': SoPProtocolType.Base.TM_RESULT_EXECUTE,
                 'level_change': None, 'element_change': None, 'overhead_type': OverheadType.TARGET_THING_INNER},
            ],
            Direction.PUBLISH: [
                {'direction': Direction.RECEIVED, 'element_type': SoPElementType.THING, 'protocol': SoPProtocolType.Base.MT_EXECUTE,
                 'level_change': None, 'element_change': (SoPElementType.MIDDLEWARE, SoPElementType.THING), 'overhead_type': OverheadType.TARGET_THING__MIDDLEWARE_COMM},
            ]
        },
        SoPProtocolType.Base.TM_RESULT_EXECUTE: {
            Direction.RECEIVED: [
                {'direction': Direction.PUBLISH, 'element_type': SoPElementType.MIDDLEWARE, 'protocol': SoPProtocolType.Super.CP_RESULT_EXECUTE,
                 'level_change': None, 'element_change': None, 'overhead_type': OverheadType.MIDDLEWARE_INNER},
            ],
            Direction.PUBLISH: [
                {'direction': Direction.RECEIVED, 'element_type': SoPElementType.MIDDLEWARE, 'protocol': SoPProtocolType.Base.TM_RESULT_EXECUTE,
                 'level_change': None, 'element_change': (SoPElementType.THING, SoPElementType.MIDDLEWARE), 'overhead_type': OverheadType.TARGET_THING__MIDDLEWARE_COMM},
            ]
        },
        SoPProtocolType.Super.CP_RESULT_EXECUTE: {
            Direction.RECEIVED: [
                {'direction': Direction.PUBLISH, 'element_type': SoPElementType.MIDDLEWARE, 'protocol': SoPProtocolType.Super.CP_RESULT_EXECUTE,
                 'level_change': None, 'element_change': None, 'overhead_type': OverheadType.MIDDLEWARE_INNER},
                {'direction': Direction.PUBLISH, 'element_type': SoPElementType.MIDDLEWARE, 'protocol': SoPProtocolType.Super.MS_RESULT_EXECUTE,
                    'level_change': None, 'element_change': None, 'overhead_type': OverheadType.MIDDLEWARE_INNER},
            ],
            Direction.PUBLISH: [
                {'direction': Direction.RECEIVED, 'element_type': SoPElementType.MIDDLEWARE, 'protocol': SoPProtocolType.Super.CP_RESULT_EXECUTE,
                 'level_change': 'up', 'element_change': None, 'overhead_type': OverheadType.MIDDLEWARE__MIDDLEWARE_COMM},
            ]
        },
        SoPProtocolType.Super.MS_RESULT_EXECUTE: {
            Direction.RECEIVED: [
                {'direction': Direction.PUBLISH, 'element_type': SoPElementType.THING, 'protocol': SoPProtocolType.Super.SM_EXECUTE,
                 'level_change': None, 'element_change': None, 'overhead_type': OverheadType.SUPER_THING_INNER},
                {'direction': Direction.PUBLISH, 'element_type': SoPElementType.THING, 'protocol': SoPProtocolType.Super.SM_RESULT_EXECUTE,
                    'level_change': None, 'element_change': None, 'overhead_type': OverheadType.SUPER_THING_INNER},
            ],
            Direction.PUBLISH: [
                {'direction': Direction.RECEIVED, 'element_type': SoPElementType.THING, 'protocol': SoPProtocolType.Super.MS_RESULT_EXECUTE,
                 'level_change': None, 'element_change': (SoPElementType.MIDDLEWARE, SoPElementType.THING), 'overhead_type': OverheadType.SUPER_THING__MIDDLEWARE_COMM},
            ]
        },
        SoPProtocolType.Super.SM_RESULT_EXECUTE: {
            Direction.RECEIVED: [
                {'direction': Direction.PUBLISH, 'element_type': SoPElementType.MIDDLEWARE, 'protocol': SoPProtocolType.Super.PC_RESULT_EXECUTE,
                 'level_change': None, 'element_change': None, 'overhead_type': OverheadType.MIDDLEWARE_INNER},
            ],
            Direction.PUBLISH: [
                {'direction': Direction.RECEIVED, 'element_type': SoPElementType.MIDDLEWARE, 'protocol': SoPProtocolType.Super.SM_RESULT_EXECUTE,
                 'level_change': None, 'element_change': (SoPElementType.THING, SoPElementType.MIDDLEWARE), 'overhead_type': OverheadType.SUPER_THING__MIDDLEWARE_COMM},
            ]
        },
        SoPProtocolType.Super.PC_RESULT_EXECUTE: {
            Direction.RECEIVED: [
                {'direction': Direction.PUBLISH, 'element_type': SoPElementType.MIDDLEWARE, 'protocol': SoPProtocolType.Super.PC_RESULT_EXECUTE,
                 'level_change': None, 'element_change': None, 'overhead_type': OverheadType.MIDDLEWARE_INNER},
            ],
            Direction.PUBLISH: [
                {'direction': Direction.RECEIVED, 'element_type': SoPElementType.MIDDLEWARE, 'protocol': SoPProtocolType.Super.PC_RESULT_EXECUTE,
                 'level_change': 'down', 'element_change': None, 'overhead_type': OverheadType.MIDDLEWARE__MIDDLEWARE_COMM},
            ]
        }
    }
}


class LogLine:
    def __init__(self, timestamp: datetime, raw_log_data: str, topic: str, payload: str, direction: Direction, protocol: SoPProtocolType,
                 element_name: str, element_type: SoPElementType, level: int) -> None:
        self.raw_log_data = raw_log_data
        self.element_name = element_name
        self.element_type = element_type
        self.level = level
        self.topic = topic
        self.payload = payload

        self.timestamp = timestamp
        self.direction = direction
        self.protocol = protocol

        self.scenario = ''
        self.super_service = ''
        self.super_thing = ''
        self.super_middleware = ''
        self.target_service = ''
        self.target_thing = ''
        self.target_middleware = ''
        self.requester_middleware = ''

        self.request_key = ''    # request_key = scenario@super_service@super_thing@requester_middleware
        self.target_key = ''     # target_key = target_service@target_thing@target_middleware

    def topic_slice(self, index: int):
        if not self.topic:
            return False

        topic_slice_list = self.topic.split('/')
        if len(topic_slice_list) <= index:
            raise IndexError('topic_slice_list index out of range')

        return self.topic.split('/')[index]

    def timestamp_str(self) -> str:
        return self.timestamp.strftime(TIMESTAMP_FORMAT)

    def update_info(self) -> dict:
        if not self.topic or not self.payload:
            return self

        topic_slice = self.topic.split('/')
        payload_dict = json_string_to_dict(self.payload)

        if self.protocol in SUPER_PROTOCOL:
            self.super_service = topic_slice[2]
            self.super_thing = topic_slice[3]
            self.requester_middleware = topic_slice[5]
            self.super_middleware = topic_slice[4]
        elif self.protocol in SUPER_RESULT_PROTOCOL:
            self.super_service = topic_slice[3]
            self.super_thing = topic_slice[4]
            self.requester_middleware = topic_slice[6]
            self.super_middleware = topic_slice[5]
        elif self.protocol in SUB_PROTOCOL:
            self.requester_middleware = topic_slice[5].split('@')[0]
            self.super_thing = topic_slice[5].split('@')[1]
            self.super_service = topic_slice[5].split('@')[2]
            self.target_middleware = topic_slice[4]
            self.target_service = topic_slice[2]
            # request_order = topic_slice[5].split('@')[3]
        elif self.protocol in SUB_RESULT_PROTOCOL:
            self.requester_middleware = topic_slice[6].split('@')[0]
            self.super_thing = topic_slice[6].split('@')[1]
            self.super_service = topic_slice[6].split('@')[2]
            self.target_middleware = topic_slice[5]
            self.target_service = topic_slice[3]
            # request_order = topic_slice[6].split('@')[3]
        elif self.protocol in SUB_EXECUTE_PROTOCOL:
            if len(topic_slice) <= 5:
                self.request_key = ''
            else:
                self.requester_middleware = topic_slice[5].split('@')[0]
                self.super_thing = topic_slice[5].split('@')[1]
                self.super_service = topic_slice[5].split('@')[2]
                self.target_middleware = topic_slice[4]
                self.target_service = topic_slice[2]
                self.target_thing = topic_slice[3]
                # request_order = topic_slice[5].split('@')[3]
        elif self.protocol in SUB_EXECUTE_RESULT_PROTOCOL:
            if len(topic_slice) <= 5:
                self.request_key = ''
            else:
                self.requester_middleware = topic_slice[6].split('@')[0]
                self.super_thing = topic_slice[6].split('@')[1]
                self.super_service = topic_slice[6].split('@')[2]
                self.target_middleware = topic_slice[5]
                self.target_service = topic_slice[3]
                self.target_thing = topic_slice[4]
                # request_order = topic_slice[6].split('@')[3]
        else:
            return self

        self.scenario = payload_dict.get('scenario', '')
        self.requester_middleware = '_'.join(self.requester_middleware.split('_')[:-1])
        self.request_key = '@'.join([self.scenario, self.super_service, self.super_thing, self.requester_middleware]) if self.requester_middleware else ''
        self.target_key = '@'.join([self.target_service, self.target_thing, self.target_middleware]) if self.target_middleware else ''

        return self


class ElementLog(metaclass=ABCMeta):
    def __init__(self, log_path: str, level: int, element_name: str, device: str) -> None:
        self.log_path = log_path
        self.level = level
        self.element_name = element_name
        self.device = device

        self.element_type: SoPElementType = None

        self.timestamp_regex = TIMESTAMP_REGEX
        self.log_line_list: List[LogLine] = []

    def load(self) -> 'ElementLog':
        with open(self.log_path, 'r') as f:
            raw_log_string = f.read()

        log_line_strings = re.split(self.timestamp_regex, raw_log_string)[1:]
        for i in range(0, len(log_line_strings), 2):
            timestamp = datetime.strptime(log_line_strings[i], TIMESTAMP_FORMAT)
            message = log_line_strings[i+1]

            topic = self.get_topic_func(message)
            payload = self.get_payload_func(message)
            direction = self.get_direction(message)
            protocol = self.get_protocol(message)

            log_line = LogLine(timestamp=timestamp, raw_log_data=message,
                               topic=topic, payload=payload, direction=direction, protocol=protocol,
                               element_name=self.element_name, element_type=self.element_type,
                               level=self.level).update_info()
            self.log_line_list.append(log_line)

        return self

    @abstractmethod
    def get_topic_func(self, log_data: str) -> str:
        pass

    @abstractmethod
    def get_payload_func(self, log_data: str) -> str:
        pass

    def get_direction(self, log_data: str) -> Direction:
        if Direction.PUBLISH.value in log_data:
            direction = Direction.PUBLISH
        elif Direction.RECEIVED.value in log_data:
            direction = Direction.RECEIVED
        else:
            direction = None

        return direction

    def get_protocol(self, topic: str) -> SoPProtocolType:
        protocol = SoPProtocolType.get(topic)
        if not protocol:
            return None

        return protocol


class MiddlewareLog(ElementLog):
    def __init__(self, log_path: str, level: int, element_name: str, device: str) -> None:
        super().__init__(log_path, level, element_name, device)
        self.element_type = SoPElementType.MIDDLEWARE

    def get_topic_func(self, log_data: str) -> str:
        if not ('[RECEIVED]' in log_data or '[PUBLISH]' in log_data):
            return None

        match = re.search(r'(?<=Topic: ).*', log_data)
        if match:
            topic = match.group(0)
        else:
            return None

        return topic

    def get_payload_func(self, log_data: str) -> str:
        match = re.search(r'(?<=Payload: )[\s\S]*', log_data)
        if match:
            payload = match.group(0)
        else:
            return None

        # 만약 payload가 json 형식이라면 json 형식으로 변환
        payload = find_json_pattern(payload)
        return payload


class ThingLog(ElementLog):
    def __init__(self, log_path: str, level: int, element_name: str, device: str, is_super: bool) -> None:
        super().__init__(log_path, level, element_name, device)
        self.element_type = SoPElementType.THING

        self.is_super = is_super

    def get_topic_func(self, log_data: str) -> str:
        match = re.search(r'topic: (.+?) payload: ([\s\S]*)', log_data)
        if match:
            topic = match.group(1)
        else:
            return None

        return topic

    def get_payload_func(self, log_data: str) -> str:
        match = re.search(r'topic: (.+?) payload: ([\s\S]*)', log_data)
        if match:
            payload = match.group(2)
        else:
            return None

        # 만약 payload가 json 형식이라면 json 형식으로 변환
        payload = find_json_pattern(payload)
        return payload


class Profiler:
    def __init__(self):
        self.middleware_log_list: List[MiddlewareLog] = []
        self.thing_log_list: List[ThingLog] = []
        self.simulation_overhead = ProfileResult()

        self.super_service_table: Dict[str, List[str]] = {}
        self.integrated_mqtt_log: List[LogLine] = []

    def load(self, log_root_path: str = '') -> 'Profiler':
        for root, dirs, files in os.walk(log_root_path):

            for dir in dirs:
                if not len(dir.split('.')) == 4:
                    continue

                middleware_log = self.make_middleware_log(os.path.join(root, dir, 'middleware'))
                thing_log_list = self.make_thing_log_list(os.path.join(root, dir, 'thing'))
                self.middleware_log_list.append(middleware_log)
                self.thing_log_list.extend(thing_log_list)

        self.super_service_table = self.make_super_service_table()
        self.integrated_mqtt_log: List[LogLine] = self.make_integrated_mqtt_log()

        SOPLOG_DEBUG(f'Load simulation log from {log_root_path} successfully', 'green')
        return self

    ##########################################################################################################################################

    def make_middleware_log(self, path: str) -> MiddlewareLog:
        dir_name = os.path.basename(os.path.dirname(path))
        device = dir_name.split('.')[1]
        middleware_level = int(dir_name.split('.')[2].split('level')[1])

        file_list = os.listdir(path)
        for file in file_list:
            if not '.log' in file or '_mosquitto' in file:
                continue
            middleware_name = file.split('.')[0]
            middleware_log = MiddlewareLog(log_path=os.path.join(path, file), level=middleware_level, element_name=middleware_name, device=device).load()
            SOPLOG_DEBUG(f'Generate MiddlewareLog of middleware {middleware_log.element_name} from {file}', 'green')

            return middleware_log

    def make_thing_log_list(self, path: str) -> List[ThingLog]:
        dir_name = os.path.basename(os.path.dirname(path))
        device = dir_name.split('.')[1]
        thing_level = int(dir_name.split('.')[2].split('level')[1])

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
            thing_log = ThingLog(log_path=os.path.join(path, file), level=thing_level, element_name=thing_name, device=device, is_super=is_super).load()
            SOPLOG_DEBUG(f'Generate ThingLog of thing {thing_log.element_name} from {file}', 'green')

            thing_log_list.append(thing_log)

        return thing_log_list

    def make_integrated_raw_log(self) -> List[LogLine]:
        whole_raw_log_line_list: List[LogLine] = []
        for element_log in self.middleware_log_list + self.thing_log_list:
            for log_line in element_log.log_line_list:
                whole_raw_log_line_list.append(log_line)

        whole_raw_log_line_list.sort(key=lambda x: x.timestamp)
        return whole_raw_log_line_list

    def make_integrated_mqtt_log(self) -> List[LogLine]:
        topic_filter = SCHEDULE_PROTOCOL + EXECUTE_PROTOCOL

        integrated_raw_log = self.make_integrated_raw_log()
        integrated_mqtt_log: List[LogLine] = []
        for log_line in integrated_raw_log:
            # if log line is not mqtt message, skip it
            if not log_line.topic:
                continue
            # if log line's topic is not in target protocol, skip it
            if not log_line.protocol in topic_filter:
                continue
            # If log line is not related to the super request, skip it
            if not log_line.request_key:
                continue
            integrated_mqtt_log.append(log_line)

        return integrated_mqtt_log

    def make_super_service_table(self) -> Dict[str, List[str]]:
        super_service_table = {}
        super_thing_log_list = [thing_log for thing_log in self.thing_log_list if thing_log.is_super]
        if len(super_thing_log_list) == 0:
            return False

        request_order = 0
        for super_thing_log in super_thing_log_list:
            for log_line in super_thing_log.log_line_list:
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

    def make_log_line_string(self, duration: timedelta, log_line: LogLine) -> str:
        timestamp = log_line.timestamp_str()
        direction = log_line.direction.value
        element_name = log_line.element_name
        topic = log_line.topic
        payload = log_line.payload

        log_line_string = f'({duration.total_seconds()*1e3:8.3f} ms)[{timestamp}][{direction:<8}] {element_name} {topic} {payload}\n'
        return log_line_string

    def make_log_string(self):
        for log_line in self.log_line_list:
            duration = (log_line.timestamp - self.log_line_list[0].timestamp) if log_line == self.log_line_list[0] else (log_line.timestamp -
                                                                                                                         self.log_line_list[self.log_line_list.index(log_line)-1].timestamp)
            log_line_string = self.make_log_line_string(duration, log_line)
            self.log_string += log_line_string

    def export_to_file(self, log_file_name: str, request_log_line_list: List[LogLine]):
        os.makedirs(os.path.dirname(log_file_name), exist_ok=True)
        with open(log_file_name, 'w') as f:
            for i, log_line in enumerate(request_log_line_list):
                duration = (request_log_line_list[i].timestamp - request_log_line_list[i-1].timestamp) if i > 0 else timedelta(seconds=0)
                log_string = self.make_log_line_string(duration, log_line)
                f.write(log_string)

        SOPLOG_DEBUG(f'Write {log_file_name}...', 'yellow')

    ##########################################################################################################################################

    def collect_request_start_log_line(self, profile_type: ProfileType) -> List[LogLine]:
        if profile_type == ProfileType.SCHEDULE:
            start_protocol = SoPProtocolType.Super.MS_SCHEDULE
        elif profile_type == ProfileType.EXECUTE:
            start_protocol = SoPProtocolType.Super.MS_EXECUTE
        else:
            raise Exception(f"Invalid profile type: {profile_type}")

        request_start_log_line_list: List[LogLine] = []
        for log_line in self.integrated_mqtt_log:
            if log_line.protocol != start_protocol:
                continue
            if log_line.element_type != SoPElementType.MIDDLEWARE:
                continue
            if log_line.direction != Direction.PUBLISH:
                continue

            request_start_log_line_list.append(log_line)

        if len(request_start_log_line_list) == 0:
            SOPLOG_DEBUG(f"Cannot find request start log!!!", 'red')
            return ProfileErrorCode.INVALID_LOG

        # Drop the first loop of request
        return request_start_log_line_list[1:]

    def collect_log_line_by_request(self, super_service_start_log: LogLine, profile_type: ProfileType) -> Union[List[LogLine], bool]:
        if profile_type == ProfileType.SCHEDULE:
            protocol_filter = SCHEDULE_PROTOCOL
        elif profile_type == ProfileType.EXECUTE:
            protocol_filter = EXECUTE_PROTOCOL
        else:
            raise Exception(f"Invalid profile type: {profile_type}")

        # target range: start ~ finish
        log_line_in_target_range = self.get_logs_time_range(log_data=self.integrated_mqtt_log,
                                                            start_time=super_service_start_log.timestamp, end_time=None)
        request_log_list: List[LogLine] = []
        for log_line in log_line_in_target_range:
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
            log_str = self.make_log_line_string(duration=timedelta(seconds=0), log_line=log_line)
            SOPTEST_LOG_DEBUG(f'[DEBUG] request_key_check: {log_line.request_key != super_service_start_log.request_key} {log_str}', 'yellow')

        log_line_for_this_req: List[LogLine] = []
        for log_line in request_log_list:
            log_line_for_this_req.append(log_line)
            if self.is_request_end(log_line):
                return log_line_for_this_req
        else:
            return False

    def collect_target_start_log_line(self, target_service: str, request_log_list: List[LogLine], profile_type: ProfileType) -> List[LogLine]:
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
            SOPLOG_DEBUG(f"Cannot find target start log for {target_service}", 'yellow')
            return []

        return target_start_log_list

    def is_request_end(self, log_line: LogLine) -> bool:
        return log_line.protocol in SM_RESULT_PROTOCOL and log_line.element_type == SoPElementType.MIDDLEWARE

    def is_sub_request_end(self, log_line: LogLine) -> bool:
        return log_line.protocol in MS_RESULT_PROTOCOL and log_line.element_type == SoPElementType.THING

    ##########################################################################################################################################

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
        if start_time > end_time:
            raise Exception(f"Invalid time range: {start_time} ~ {end_time}")

        log_range = [log_line for log_line in log_data if start_time <= log_line.timestamp <= end_time]
        return log_range

    def get_windowed_log_list(self, request_log_list: List[LogLine], target_log_line, before: int = 3, after: int = 3) -> List[LogLine]:
        target_log_index = request_log_list.index(target_log_line)
        index1 = target_log_index-before if target_log_index-before >= 0 else 0
        index2 = target_log_index+after+1 if target_log_index+after+1 <= len(request_log_list) else len(request_log_list)
        log_window = request_log_list[index1:index2]
        return log_window

    ##########################################################################################################################################

    def get_overhead_type_if_valid(self, curr_log_line: LogLine, next_log_line: LogLine, profile_type: ProfileType) -> OverheadType:
        if curr_log_line == next_log_line:
            SOPTEST_LOG_DEBUG(f'[DEBUG] Same log line: {curr_log_line}', 'yellow')
            return False

        filter_list = LOG_ORDER_MAP[profile_type][curr_log_line.protocol][curr_log_line.direction]
        for filter in filter_list:
            element_type_check = (filter['element_type'] == next_log_line.element_type)
            protocol_check = (filter['protocol'] == next_log_line.protocol)
            level_change_check = False
            element_change_check = False

            if filter['level_change'] == 'up':
                level_change_check = (curr_log_line.level < next_log_line.level) and abs(curr_log_line.level - next_log_line.level) == 1
            elif filter['level_change'] == 'down':
                level_change_check = (curr_log_line.level > next_log_line.level) and abs(curr_log_line.level - next_log_line.level) == 1
            elif curr_log_line.level == next_log_line.level:
                level_change_check = True

            if filter['element_change']:
                if curr_log_line.element_type == filter['element_change'][0] and next_log_line.element_type == filter['element_change'][1]:
                    element_change_check = True
            elif curr_log_line.element_type == next_log_line.element_type:
                element_change_check = True

            overhead_type = filter['overhead_type']
            if element_type_check and protocol_check and level_change_check and element_change_check:
                return overhead_type
        else:
            return False

    ##########################################################################################################################################

    def get_avg_overhead(self, overhead_type: OverheadType = None) -> float:
        if overhead_type == None:
            return sum([overhead.overhead_total() for overhead in self.whole_request_overhead_list]) / len(self.whole_request_overhead_list)
        elif overhead_type == OverheadType.INNER:
            return sum([overhead.inner_overhead_total() for overhead in self.whole_request_overhead_list]) / len(self.whole_request_overhead_list)
        elif overhead_type == OverheadType.COMM:
            return sum([overhead.comm_overhead_total() for overhead in self.whole_request_overhead_list]) / len(self.whole_request_overhead_list)
        else:
            whole_overhead = ProfileResult()
            for overhead in self.whole_request_overhead_list:
                whole_overhead += overhead
            return whole_overhead.avg(overhead_type)

    def profile(self, profile_type: ProfileType, export: bool = False) -> ProfileResult:
        if not profile_type in [ProfileType.SCHEDULE, ProfileType.EXECUTE]:
            raise Exception(f"Invalid profile type: {profile_type}")

        request_start_log_line_list = self.collect_request_start_log_line(profile_type=profile_type)
        if export:
            file_created_time = get_current_time(mode=TimeFormat.DATETIME2)
        super_service_index_lookup_table = {super_service: 0 for super_service in self.super_service_table}

        for i, request_start_log in enumerate(request_start_log_line_list):
            request_log_line_list: List[LogLine] = self.collect_log_line_by_request(request_start_log, profile_type=profile_type)
            if not request_log_line_list:
                continue
            super_service_request_index = super_service_index_lookup_table[request_start_log.super_service]

            if export:
                self.export_to_file(log_file_name=f'./profile_result_{file_created_time}/log_{request_start_log.super_service}_request_{super_service_request_index}.txt',
                                    request_log_line_list=request_log_line_list)
            request_overhead = self.profile_request(request_log_line_list=request_log_line_list, profile_type=profile_type)
            if request_overhead == ProfileErrorCode.INVALID_LOG:
                SOPLOG_DEBUG(f'log file is not valid... skip this log file', 'red')
                return ProfileErrorCode.INVALID_LOG
            elif request_overhead == ProfileErrorCode.INVALID_REQUEST:
                SOPLOG_DEBUG(f'request log is not valid... skip this request', 'red')
                continue
            elif request_overhead == ProfileErrorCode.TOO_HIGH_OVERHEAD:
                SOPLOG_DEBUG(f'log file overhead is too high... skip this request', 'red')
                continue

            SOPLOG_DEBUG(f'Profile request: {request_log_line_list[0].request_key}:{i} complete!', 'cyan')
            self.simulation_overhead.add(request_overhead)
            super_service_index_lookup_table[request_start_log.super_service] += 1

        return self.simulation_overhead

    def profile_request(self, request_log_line_list: List[LogLine], profile_type: ProfileType) -> ProfileResult:
        request_key = request_log_line_list[0].request_key
        request_overhead = RequestOverhead(request_key=request_key)

        for i, log_line in enumerate(request_log_line_list):
            curr_log_line = log_line
            if self.is_request_end(log_line=curr_log_line):
                break
            next_log_line = request_log_line_list[i+1]

            overhead_type = self.get_overhead_type_if_valid(curr_log_line=curr_log_line, next_log_line=next_log_line, profile_type=profile_type)
            if not overhead_type:
                # duration = timedelta(seconds=0)
                return ProfileErrorCode.INVALID_REQUEST
            else:
                duration = next_log_line.timestamp - curr_log_line.timestamp

            detail_overhead = Overhead(duration=duration, overhead_type=overhead_type,
                                       element_name_from=curr_log_line.element_name,
                                       element_type_from=curr_log_line.element_type,
                                       level_from=curr_log_line.level,
                                       protocol_from=curr_log_line.protocol,
                                       element_name_to=next_log_line.element_name,
                                       element_type_to=next_log_line.element_type,
                                       level_to=next_log_line.level,
                                       protocol_to=next_log_line.protocol)
            request_overhead.overhead_list.append(detail_overhead)

        return request_overhead

    # TODO: complete this
    def profile_target(self, target_log_list: List[LogLine], profile_type: ProfileType) -> ProfileResult:
        target_overhead = ProfileResult()

        return target_overhead


# [ST(3) <- MW(3)    MW(2)    MW(1)         ]
# [ST(3) -> MW(3)    MW(2)    MW(1)    LT(1)]
# [ST(3)    MW(3) -> MW(2)    MW(1)    LT(1)]
# [ST(3)    MW(3)    MW(2) -> MW(1)    LT(1)]
# [ST(3)    MW(3)    MW(2)    MW(1) -> LT(1)]
# [ST(3)    MW(3)    MW(2)    MW(1) <- LT(1)]
# [ST(3)    MW(3)    MW(2) <- MW(1)    LT(1)]
# [ST(3)    MW(3) <- MW(2)    MW(1)    LT(1)]
# [ST(3) <- MW(3)    MW(2)    MW(1)    LT(1)]
# [ST(3) -> MW(3)    MW(2)    LT(2)         ]
# [ST(3)    MW(3) -> MW(2)    LT(2)         ]
# [ST(3)    MW(3)    MW(2) -> LT(2)         ]
# [ST(3)    MW(3)    MW(2) <- LT(2)         ]
# [ST(3)    MW(3) <- MW(2)    LT(2)         ]
# [ST(3) <- MW(3)    MW(2)    LT(2)         ]
# [ST(3) -> MW(3)    LT(3)                  ]
# [ST(3)    MW(3) -> LT(3)                  ]
# [ST(3)    MW(3) <- LT(3)                  ]
# [ST(3) <- MW(3)    LT(3)                  ]
