from simulation_framework.core.elements import *
from datetime import datetime, timedelta

TIMESTAMP_FORMAT = '%Y/%m/%d %H:%M:%S.%f'
TIMESTAMP_REGEX = r'\[(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}\.\d{3})\]'

SUPER_PROTOCOL = [MXProtocolType.Super.MS_SCHEDULE, MXProtocolType.Super.MS_EXECUTE,
                  MXProtocolType.Super.CP_SCHEDULE, MXProtocolType.Super.CP_EXECUTE]
SUPER_RESULT_PROTOCOL = [MXProtocolType.Super.SM_RESULT_SCHEDULE, MXProtocolType.Super.SM_RESULT_EXECUTE,
                         MXProtocolType.Super.PC_RESULT_SCHEDULE, MXProtocolType.Super.PC_RESULT_EXECUTE]
SUB_PROTOCOL = [MXProtocolType.Super.SM_SCHEDULE, MXProtocolType.Super.SM_EXECUTE,
                MXProtocolType.Super.PC_SCHEDULE, MXProtocolType.Super.PC_EXECUTE]
SUB_RESULT_PROTOCOL = [MXProtocolType.Super.MS_RESULT_SCHEDULE, MXProtocolType.Super.MS_RESULT_EXECUTE,
                       MXProtocolType.Super.CP_RESULT_SCHEDULE, MXProtocolType.Super.CP_RESULT_EXECUTE]
SUB_EXECUTE_PROTOCOL = [MXProtocolType.Base.MT_EXECUTE]
SUB_EXECUTE_RESULT_PROTOCOL = [MXProtocolType.Base.TM_RESULT_EXECUTE]


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
    def __init__(self, timestamp: str, raw_log_data: str, get_topic_func: Callable, get_payload_func: Callable, element_type: MXElementType, element_name: str) -> None:
        self._raw_log_data = raw_log_data
        self._get_topic_func = get_topic_func
        self._get_payload_func = get_payload_func
        self.element_type = element_type
        self.element_name = element_name
        self.log_key = ''

        self._timestamp = datetime.strptime(timestamp, TIMESTAMP_FORMAT)
        self.topic = self.get_topic(self.raw_log_data)
        self.payload = self.get_payload(self.raw_log_data)

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

    @property
    def raw_log_data(self) -> str:
        return self._raw_log_data

    @raw_log_data.setter
    def raw_log_data(self, raw_log_data: str):
        self._raw_log_data = raw_log_data
        self.topic = self.get_topic(self._raw_log_data)
        self.payload = self.get_payload(self._raw_log_data)

    @property
    def timestamp(self) -> dict:
        return self._timestamp

    @timestamp.setter
    def timestamp(self, timestamp: str):
        self._timestamp = datetime.strptime(timestamp, TIMESTAMP_FORMAT)

    def timestamp_str(self) -> str:
        return self._timestamp.strftime(TIMESTAMP_FORMAT)


class LogData:
    def __init__(self, log_path: str, timestamp_pattern: str, get_topic_func: Callable, get_payload_func: Callable, element_type: MXElementType, element_name: str) -> None:
        self.log_path = log_path
        self.log_line_list: List[LogLine] = []
        self.element_type = element_type
        self.element_name = element_name

        self.load(self.log_path, timestamp_pattern=timestamp_pattern, get_topic_func=get_topic_func, get_payload_func=get_payload_func)

    def load(self, log_path: str, timestamp_pattern: str, get_topic_func: Callable, get_payload_func: Callable):
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
                                element_type=MXElementType.MIDDLEWARE,
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
                                element_type=MXElementType.THING,
                                element_name=self.name)

    def get_topic_func(self, log_data: str) -> str:
        match = re.search(r'topic : (.+?) payload : (.+)', log_data)
        if match:
            topic = match.group(1)
        else:
            return False

        return topic

    def get_payload_func(self, log_data: str) -> str:
        match = re.search(r'topic : (.+?) payload : (.+)', log_data)
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

        self.load(self.root_log_folder_path)
        self.super_service_table = self.make_super_service_table()
        self.integrated_log_list: List[LogLine] = self.make_integrated_log_list()

    def make_middleware_log(self, path: str) -> MiddlewareLog:
        file_list = os.listdir(path)
        for file in file_list:
            if not '.log' in file:
                continue
            middleware_name = file.split('.')[0]
            middleware_level = int(path.split(os.sep)[-2].split('.')[1].split('level')[1])
            middleware_log_path = os.path.join(path, file)
            middleware_log = MiddlewareLog(log_path=middleware_log_path, level=middleware_level, name=middleware_name)

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
            thing_log_list.append(thing_log)

        return thing_log_list

    def load(self, root_log_folder_path: str):
        for root, dirs, files in os.walk(root_log_folder_path):

            for dir in dirs:
                if not len(dir.split('.')) == 3:
                    continue

                middleware_log = self.make_middleware_log(os.path.join(root, dir, 'middleware'))
                thing_log_list = self.make_thing_log_list(os.path.join(root, dir, 'thing'))
                self.middleware_log_list.append(middleware_log)
                self.thing_log_list.extend(thing_log_list)

    def make_integrated_log_list(self):
        topic_filter = SUPER_PROTOCOL + SUPER_RESULT_PROTOCOL + SUB_PROTOCOL + SUB_RESULT_PROTOCOL + SUB_EXECUTE_PROTOCOL + SUB_EXECUTE_RESULT_PROTOCOL

        whole_log_line_list: List[LogLine] = []
        for middleware_log in self.middleware_log_list:
            whole_log_line_list.extend([log_line for log_line in middleware_log.log_data.log_line_list
                                        if isinstance(log_line.topic, str) and MXProtocolType.get(log_line.topic) in topic_filter])
        for thing_log in self.thing_log_list:
            whole_log_line_list.extend([log_line for log_line in thing_log.log_data.log_line_list
                                        if isinstance(log_line.topic, str) and MXProtocolType.get(log_line.topic) in topic_filter])

        whole_log_line_list.sort(key=lambda x: x.timestamp)

        for log_line in whole_log_line_list:
            log_line.log_key = self.make_log_key(log_line)

        return whole_log_line_list

    def export_integrated_log_file(self, file_name: str = 'whole_log_file.txt') -> str:
        with open(file_name, 'w') as f:
            for log_line in self.integrated_log_list:
                f.write(f'[{log_line.timestamp_str()[:-3]}][{"THING     " if log_line.element_type == MXElementType.THING else "MIDDLEWARE"}]'
                        f'[{log_line.element_name}][{self.make_log_key(log_line)}] '
                        f'{log_line.topic} {log_line.payload}\n')
        return os.path.abspath(file_name)

    def make_super_service_table(self) -> Dict[str, List[str]]:
        super_service_table = {}
        super_thing_log_list = [thing_log for thing_log in self.thing_log_list if thing_log.is_super]
        if len(super_thing_log_list) == 0:
            return False

        for super_thing_log in super_thing_log_list:
            request_order = 0
            for log_line in super_thing_log.log_data.log_line_list:
                if '✔✔✔' in log_line.raw_log_data:
                    break

                if "Detect super service" in log_line.raw_log_data:
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

    def make_log_key(self, log_line: LogLine) -> str:
        topic = log_line.topic
        payload = json_string_to_dict(log_line.payload)
        protocol = MXProtocolType.get(topic)
        scenario = payload['scenario']

        if protocol in SUPER_PROTOCOL:
            super_service = topic.split('/')[2]
            super_thing = topic.split('/')[3]
            super_middleware = topic.split('/')[4]
            requester_middleware = topic.split('/')[5]
            key = '@'.join([scenario, super_service, super_thing, super_middleware, requester_middleware])
        elif protocol in SUPER_RESULT_PROTOCOL:
            super_service = topic.split('/')[3]
            super_thing = topic.split('/')[4]
            super_middleware = topic.split('/')[5]
            requester_middleware = topic.split('/')[6]
            key = '@'.join([scenario, super_service, super_thing, super_middleware, requester_middleware])
        elif protocol in SUB_PROTOCOL:
            target_service = topic.split('/')[2]
            target_middleware = topic.split('/')[4]
            requester_middleware = topic.split('/')[5].split('@')[0]
            super_thing = topic.split('/')[5].split('@')[1]
            super_service = topic.split('/')[5].split('@')[2]
            request_order = topic.split('/')[5].split('@')[3]
            key = '@'.join([scenario, target_service, requester_middleware, super_thing, super_service, str(request_order)])
        elif protocol in SUB_RESULT_PROTOCOL:
            target_service = topic.split('/')[3]
            target_middleware = topic.split('/')[5]
            requester_middleware = topic.split('/')[6].split('@')[0]
            super_thing = topic.split('/')[6].split('@')[1]
            super_service = topic.split('/')[6].split('@')[2]
            request_order = topic.split('/')[6].split('@')[3]
            key = '@'.join([scenario, target_service, requester_middleware, super_thing, super_service, str(request_order)])
        elif protocol in SUB_EXECUTE_PROTOCOL:
            try:
                target_service = topic.split('/')[2]
                target_thing = topic.split('/')[3]
                target_middleware = topic.split('/')[4]
                requester_middleware = topic.split('/')[5].split('@')[0]
                super_thing = topic.split('/')[5].split('@')[1]
                super_service = topic.split('/')[5].split('@')[2]
                request_order = topic.split('/')[5].split('@')[3]
                key = '@'.join([scenario, target_service, requester_middleware, super_thing, super_service, str(request_order)])
            except Exception as e:
                key = ''
        elif protocol in SUB_EXECUTE_RESULT_PROTOCOL:
            try:
                target_service = topic.split('/')[3]
                target_thing = topic.split('/')[4]
                target_middleware = topic.split('/')[5]
                requester_middleware = topic.split('/')[6].split('@')[0]
                super_thing = topic.split('/')[6].split('@')[1]
                super_service = topic.split('/')[6].split('@')[2]
                request_order = topic.split('/')[6].split('@')[3]
                key = '@'.join([scenario, target_service, requester_middleware, super_thing, super_service, str(request_order)])
            except Exception as e:
                key = ''

        return key

    def get_super_service_start_log_list(self, super_service: str, start_protocol: MXProtocolType) -> List[LogLine]:
        log_list = []
        for log_line in self.integrated_log_list:
            if MXProtocolType.get(log_line.topic) == start_protocol and super_service == log_line.topic.split('/')[2]:
                log_list.append(log_line)

        if len(log_list) == 0:
            raise Exception(f"Cannot find super service start log for {super_service}")

        return log_list

    def get_sub_log_key_from_super_service(self, super_service: str, super_service_start_log: LogLine) -> List[str]:
        super_log_key = super_service_start_log.log_key

        scenario = super_log_key.split('@')[0]
        super_service = super_log_key.split('@')[1]
        super_thing = super_log_key.split('@')[2]
        super_middleware = super_log_key.split('@')[3]
        requester_middleware = super_log_key.split('@')[4]

        sub_service_list = self.super_service_table[super_service]
        sub_log_key_list = []
        for target_service, request_order in sub_service_list:
            sub_log_key = '@'.join([scenario, target_service, requester_middleware, super_thing, super_service, str(request_order)])
            sub_log_key_list.append(sub_log_key)

        return sub_log_key_list

    def profile(self, type: ProfileType):
        if not type in [ProfileType.SCHEDULE, ProfileType.EXECUTE]:
            raise Exception(f"Invalid profile type: {type}")

        for super_service in self.super_service_table:
            result = self.profile_super_service(super_service, type)

    def profile_super_service(self, super_service: str, type: ProfileType):
        overhead = Overhead()

        if type == ProfileType.SCHEDULE:
            start_protocol = MXProtocolType.Super.CP_SCHEDULE
        elif type == ProfileType.EXECUTE:
            start_protocol = MXProtocolType.Super.CP_EXECUTE

        # 같은 super service에 대한 요청이 여러개가 존재한다. 각 요청에 대해서 오버헤드를 계산한다.
        super_service_start_log_list = self.get_super_service_start_log_list(super_service, start_protocol)
        super_service_start_log_list: List[LogLine] = sorted(super_service_start_log_list, key=lambda x: x.timestamp)
        for super_service_start_log in super_service_start_log_list:
            request_log_list: List[LogLine] = []
            log_line_pool = self.get_logs_in_time_range(self.integrated_log_list,
                                                        start_time=super_service_start_log.timestamp - timedelta(milliseconds=3),
                                                        end_time=None)
            sub_log_key_list = self.get_sub_log_key_from_super_service(super_service, super_service_start_log)
            for log_line in log_line_pool:
                if log_line.log_key == super_service_start_log.log_key or log_line.log_key in sub_log_key_list:
                    request_log_list.append(log_line)

            for sub_service, i in self.super_service_table[super_service]:
                with open(f'log_{super_service}_{sub_service}_{i}.txt', 'w') as f:
                    for i, log_line in enumerate(request_log_list[:-1]):
                        sub_service_check = (MXProtocolType.get(log_line.topic) in (SUB_PROTOCOL + SUB_RESULT_PROTOCOL +
                                             SUB_EXECUTE_PROTOCOL + SUB_EXECUTE_RESULT_PROTOCOL)) and (sub_service in log_line.topic)
                        super_service_check = (MXProtocolType.get(log_line.topic) in (SUPER_PROTOCOL + SUPER_RESULT_PROTOCOL)) and (super_service in log_line.topic)
                        if not (sub_service_check or super_service_check):
                            continue
                        duration = (request_log_list[i].timestamp - request_log_list[i-1].timestamp) if i > 0 else timedelta(milliseconds=0)
                        duration_ms = int(duration.total_seconds() * 1000)
                        f.write(f'({duration_ms:>4}ms)[{log_line.timestamp_str()[:-3]}] {log_line.element_name} {log_line.topic} {log_line.payload}\n')

            with open(f'log_{super_service}.txt', 'w') as f:
                for i, log_line in enumerate(request_log_list):
                    if not (sub_service_check or super_service_check):
                        continue
                    duration = (request_log_list[i].timestamp - request_log_list[i-1].timestamp) if i > 0 else timedelta(milliseconds=0)
                    duration_ms = int(duration.total_seconds() * 1000)
                    f.write(f'({duration_ms:>4}ms)[{log_line.timestamp_str()[:-3]}] {log_line.element_name} {log_line.topic} {log_line.payload}\n')

            for log_line in self.integrated_log_list:
                if log_line.topic == MXProtocolType.Super.MS_SCHEDULE and super_service in log_line.payload:
                    super_service_start_time = log_line.timestamp
                    break
