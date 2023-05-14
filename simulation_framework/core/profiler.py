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
SUB_EXECUTE_PROTOCOL = [SoPProtocolType.Base.MT_EXECUTE]
SUB_EXECUTE_RESULT_PROTOCOL = [SoPProtocolType.Base.TM_RESULT_EXECUTE]

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


class OverheadType(Enum):
    SUPER_THING_INNER = auto()
    TARGET_THING_INNER = auto()
    MIDDLEWARE_INNER = auto()
    SUPER_THING__MIDDLEWARE_COMM = auto()
    TARGET_THING__MIDDLEWARE_COMM = auto()
    MIDDLEWARE__MIDDLEWARE_COMM = auto()


class ProfileType(Enum):
    SCHEDULE = auto()
    EXECUTE = auto()


class Overhead:

    def __init__(self) -> None:
        self.super_thing_inner_overhead_list = []
        self.middleware_inner_overhead_list = []
        self.target_thing_inner_overhead_list = []
        self.super_thing__middleware_comm_overhead_list = []
        self.target_thing__middleware_comm_overhead_list = []
        self.middleware__middleware_comm_overhead_list = []

    def __add__(self, o: 'Overhead') -> 'Overhead':
        self.super_thing_inner_overhead_list += o.super_thing_inner_overhead_list
        self.middleware_inner_overhead_list += o.middleware_inner_overhead_list
        self.target_thing_inner_overhead_list += o.target_thing_inner_overhead_list
        self.super_thing__middleware_comm_overhead_list += o.super_thing__middleware_comm_overhead_list
        self.target_thing__middleware_comm_overhead_list += o.target_thing__middleware_comm_overhead_list
        self.middleware__middleware_comm_overhead_list += o.middleware__middleware_comm_overhead_list

        return self

    def add(self, overhead: float, type: OverheadType):
        if type == OverheadType.SUPER_THING_INNER:
            self.super_thing_inner_overhead_list.append(overhead)
        elif type == OverheadType.TARGET_THING_INNER:
            self.target_thing_inner_overhead_list.append(overhead)
        elif type == OverheadType.MIDDLEWARE_INNER:
            self.middleware_inner_overhead_list.append(overhead)
        elif type == OverheadType.SUPER_THING__MIDDLEWARE_COMM:
            self.super_thing__middleware_comm_overhead_list.append(overhead)
        elif type == OverheadType.TARGET_THING__MIDDLEWARE_COMM:
            self.target_thing__middleware_comm_overhead_list.append(overhead)
        elif type == OverheadType.MIDDLEWARE__MIDDLEWARE_COMM:
            self.middleware__middleware_comm_overhead_list.append(overhead)

    def get(self, type: OverheadType) -> float:
        if type == OverheadType.SUPER_THING_INNER:
            return avg(self.super_thing_inner_overhead_list)
        elif type == OverheadType.TARGET_THING_INNER:
            return avg(self.target_thing_inner_overhead_list)
        elif type == OverheadType.MIDDLEWARE_INNER:
            return avg(self.middleware_inner_overhead_list)
        elif type == OverheadType.SUPER_THING__MIDDLEWARE_COMM:
            return avg(self.super_thing__middleware_comm_overhead_list)
        elif type == OverheadType.TARGET_THING__MIDDLEWARE_COMM:
            return avg(self.target_thing__middleware_comm_overhead_list)
        elif type == OverheadType.MIDDLEWARE__MIDDLEWARE_COMM:
            return avg(self.middleware__middleware_comm_overhead_list)


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
        self.requester_middleware = ''
        self.target_middleware = ''

        # request_key = scenario@super_service@super_thing@requester_middleware
        self.request_key = ''
        # target_key = target_service@target_thing
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
            request_key, target_key, scenario, requester_middleware, target_middleware = self.make_log_line_info(log_line)
            log_line.request_key = request_key
            log_line.target_key = target_key
            log_line.scenario = scenario
            log_line.requester_middleware = requester_middleware
            log_line.target_middleware = target_middleware

        return whole_mqtt_msg_log_line_list

    def make_super_service_table(self) -> Dict[str, List[str]]:
        '''
            Make Super Service info table from SuperThing's log
        '''
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

    def get_logs_in_time_range(self, log_data: List[LogLine], start_time: datetime = None, end_time: datetime = None) -> List[LogLine]:
        if start_time == None:
            start_time = datetime.min
        if end_time == None:
            end_time = datetime.max

        return [log_line for log_line in log_data if start_time <= log_line.timestamp <= end_time]

    def make_log_line_info(self, log_line: LogLine) -> Tuple[str, str, str, str, str]:
        topic = log_line.topic
        payload = json_string_to_dict(log_line.payload)
        target_middleware = ''
        target_thing = ''
        target_service = ''
        request_key = ''
        target_key = ''

        if log_line.protocol in SUPER_PROTOCOL:
            super_service = topic.split('/')[2]
            super_thing = topic.split('/')[3]
            requester_middleware = topic.split('/')[5]
            # super_middleware = topic.split('/')[4]
        elif log_line.protocol in SUPER_RESULT_PROTOCOL:
            super_service = topic.split('/')[3]
            super_thing = topic.split('/')[4]
            requester_middleware = topic.split('/')[6]
            # super_middleware = topic.split('/')[5]
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
        target_key = '@'.join([target_service, target_thing])

        return request_key, target_key, scenario, requester_middleware, target_middleware

    def get_request_start_log_list(self, super_service: str, profile_type: ProfileType) -> List[LogLine]:
        '''
            전체 로그에서 super service 요청 시작 로그 리스트를 가져온다 (CP/EXECUTE or CP/SCHEDULE)
        '''
        request_start_log_list = []
        profile_protocol = self.profile_type_to_protocol(profile_type)
        for log_line in self.integrated_mqtt_msg_log_list:
            if log_line.protocol != profile_protocol:
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

        return request_start_log_list

    def get_same_request_log_list(self, super_service_start_log: LogLine, profile_type: ProfileType) -> List[LogLine]:
        '''
            전체 로그에서 특정 super service 요청에 대한 로그 리스트를 가져온다
        '''
        if profile_type == ProfileType.SCHEDULE:
            protocol_filter = SCHEDULE_PROTOCOL
        elif profile_type == ProfileType.EXECUTE:
            protocol_filter = EXECUTE_PROTOCOL
        else:
            raise Exception(f"Invalid profile type: {profile_type}")

        request_log_list = []
        for log_line in self.integrated_mqtt_msg_log_list:
            if not log_line.protocol in protocol_filter:
                continue
            if log_line.request_key != super_service_start_log.request_key:
                continue

            if log_line.element_type == SoPElementType.MIDDLEWARE:
                if log_line.protocol in SUPER_PROTOCOL + SUPER_RESULT_PROTOCOL and not log_line.element_name in log_line.requester_middleware:
                    continue
                elif log_line.protocol in SUB_PROTOCOL + SUB_RESULT_PROTOCOL and not log_line.element_name in log_line.target_middleware:
                    continue

            request_log_list.append(log_line)

        same_request_log_list = self.check_log_line_sequence(request_log_list)
        # same_request_log_list = request_log_list
        return same_request_log_list

    def profile_type_to_protocol(self, profile_type: ProfileType) -> SoPProtocolType:
        if profile_type == ProfileType.SCHEDULE:
            return SoPProtocolType.Super.CP_SCHEDULE
        elif profile_type == ProfileType.EXECUTE:
            return SoPProtocolType.Super.CP_EXECUTE
        else:
            raise Exception(f"Invalid profile type: {profile_type}")

    def check_log_line_sequence(self, request_log_list: List[LogLine]) -> List[LogLine]:
        for i, log_line in enumerate(request_log_list[1:]):
            prev_element_type = request_log_list[i-1].element_type
            prev_protocol = request_log_list[i-1].protocol
            curr_element_type = request_log_list[i].element_type
            curr_protocol = request_log_list[i].protocol
            if (prev_element_type, curr_element_type) == (SoPElementType.THING, SoPElementType.MIDDLEWARE) \
                    and (prev_protocol, curr_protocol) == (SoPProtocolType.Super.MS_RESULT_EXECUTE, SoPProtocolType.Super.SM_EXECUTE):
                tmp_log_line = request_log_list[i-1]
                request_log_list[i-1] = request_log_list[i]
                request_log_list[i] = tmp_log_line

                request_log_list[i].timestamp = request_log_list[i-1].timestamp

        return request_log_list

    def profile(self, type: ProfileType) -> Overhead:
        whole_overhead = Overhead()
        if not type in [ProfileType.SCHEDULE, ProfileType.EXECUTE]:
            raise Exception(f"Invalid profile type: {type}")

        for super_service in self.super_service_table:
            overhead_result = self.profile_super_service(super_service, type)
            whole_overhead += overhead_result

        return whole_overhead

    def profile_super_service(self, super_service: str, profile_type: ProfileType) -> Overhead:
        super_service_overhead = Overhead()

        # 같은 super service에 대한 요청이 여러개가 존재한다. 각 요청에 대해서 오버헤드를 계산한다.
        request_start_log_list = self.get_request_start_log_list(super_service, profile_type=profile_type)
        for i, request_start_log in enumerate(request_start_log_list):
            same_request_log_list: List[LogLine] = self.get_same_request_log_list(request_start_log, profile_type=profile_type)

            log_file_name = f'log_{super_service}_request_{i}.txt'
            with open(log_file_name, 'w') as f:
                for i, log_line in enumerate(same_request_log_list):
                    duration = (same_request_log_list[i].timestamp - same_request_log_list[i-1].timestamp) if i > 0 else timedelta(seconds=0)
                    duration_ms = int(duration.total_seconds() * 1e3)
                    duration_us = int(duration.total_seconds() * 1e6)
                    f.write(
                        f'({f"{duration_ms:>4}.{int(duration_us - duration_ms * 1e3):0>3}"} ms)[{log_line.timestamp_str()}][{log_line.direction.value:<8}] {log_line.element_name} {log_line.topic} {log_line.payload}\n')
            SOPLOG_DEBUG(f'Write {log_file_name}...', 'yellow')

        return super_service_overhead

    def profile_target(self, target: str, profile_type: ProfileType) -> Overhead:
        target_overhead = Overhead()
