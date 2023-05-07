from simulation_framework.core.elements import *
from datetime import datetime, timedelta

TIMESTAMP_FORMAT = '%Y/%m/%d %H:%M:%S.%f'
TIMESTAMP_REGEX = r'\[(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}\.\d{3})\]'


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
        topic_filter = [MXProtocolType.Super.MS_SCHEDULE,
                        MXProtocolType.Super.SM_SCHEDULE,
                        MXProtocolType.Super.MS_RESULT_SCHEDULE,
                        MXProtocolType.Super.SM_RESULT_SCHEDULE,
                        MXProtocolType.Super.MS_EXECUTE,
                        MXProtocolType.Super.SM_EXECUTE,
                        MXProtocolType.Super.MS_RESULT_EXECUTE,
                        MXProtocolType.Super.SM_RESULT_EXECUTE,
                        MXProtocolType.Super.PC_SCHEDULE,
                        MXProtocolType.Super.CP_SCHEDULE,
                        MXProtocolType.Super.PC_RESULT_SCHEDULE,
                        MXProtocolType.Super.CP_RESULT_SCHEDULE,
                        MXProtocolType.Super.PC_EXECUTE,
                        MXProtocolType.Super.CP_EXECUTE,
                        MXProtocolType.Super.PC_RESULT_EXECUTE,
                        MXProtocolType.Super.CP_RESULT_EXECUTE,
                        ]

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

        if protocol in [MXProtocolType.Super.MS_SCHEDULE, MXProtocolType.Super.MS_EXECUTE,
                        MXProtocolType.Super.CP_SCHEDULE, MXProtocolType.Super.CP_EXECUTE]:
            scenario = payload['scenario']
            super_service = topic.split('/')[2]
            super_thing = topic.split('/')[3]
            super_middleware = topic.split('/')[4]
            requester_middleware = topic.split('/')[5]
            key = '@'.join([scenario, super_service, requester_middleware])
        elif protocol in [MXProtocolType.Super.SM_RESULT_SCHEDULE, MXProtocolType.Super.SM_RESULT_EXECUTE,
                          MXProtocolType.Super.PC_RESULT_SCHEDULE, MXProtocolType.Super.PC_RESULT_EXECUTE]:
            scenario = payload['scenario']
            super_service = topic.split('/')[3]
            super_thing = topic.split('/')[4]
            super_middleware = topic.split('/')[5]
            requester_middleware = topic.split('/')[6]
            key = '@'.join([scenario, super_service, requester_middleware])
        elif protocol in [MXProtocolType.Super.SM_SCHEDULE, MXProtocolType.Super.SM_EXECUTE,
                          MXProtocolType.Super.PC_SCHEDULE, MXProtocolType.Super.PC_EXECUTE]:
            scenario = payload['scenario']
            target_service = topic.split('/')[2]
            target_middleware = topic.split('/')[4]
            requester_middleware = topic.split('/')[5].split('@')[0]
            super_thing = topic.split('/')[5].split('@')[1]
            super_service = topic.split('/')[5].split('@')[2]
            request_order = topic.split('/')[5].split('@')[3]
            key = '@'.join([scenario, super_service, requester_middleware])
        elif protocol in [MXProtocolType.Super.MS_RESULT_SCHEDULE, MXProtocolType.Super.MS_RESULT_EXECUTE,
                          MXProtocolType.Super.CP_RESULT_SCHEDULE, MXProtocolType.Super.CP_RESULT_EXECUTE]:
            scenario = payload['scenario']
            target_service = topic.split('/')[3]
            target_middleware = topic.split('/')[5]
            requester_middleware = topic.split('/')[6].split('@')[0]
            super_thing = topic.split('/')[6].split('@')[1]
            super_service = topic.split('/')[6].split('@')[2]
            request_order = topic.split('/')[6].split('@')[3]

        key = '@'.join([scenario, super_service, requester_middleware])

        return key

    def get_super_service_start_log_list(self, super_service: str, start_protocol: MXProtocolType) -> List[LogLine]:
        log_list = []
        for log_line in self.integrated_log_list:
            if MXProtocolType.get(log_line.topic) == start_protocol and super_service == log_line.topic.split('/')[2]:
                log_list.append(log_line)

        if len(log_list) == 0:
            raise Exception(f"Cannot find super service start log for {super_service}")

        return log_list

    def profile(self, type: ProfileType):
        if not type in [ProfileType.SCHEDULE, ProfileType.EXECUTE]:
            raise Exception(f"Invalid profile type: {type}")

        for super_service in self.super_service_table:
            result = self.profile_super_service(super_service, type)

    def profile_super_service(self, super_service: str, type: ProfileType):
        overhead = Overhead()

        if type == ProfileType.SCHEDULE:
            start_protocol = MXProtocolType.Super.MS_SCHEDULE
        elif type == ProfileType.EXECUTE:
            start_protocol = MXProtocolType.Super.MS_EXECUTE

        super_service_start_log_list = self.get_super_service_start_log_list(super_service, start_protocol)

        for super_service_start_log in super_service_start_log_list:
            super_service_log_list: List[LogLine] = []
            log_line_pool = self.get_logs_in_time_range(self.integrated_log_list,
                                                        start_time=super_service_start_log.timestamp - timedelta(milliseconds=3),
                                                        end_time=None)
            for log_line in log_line_pool:
                if log_line.log_key == super_service_start_log.log_key:
                    super_service_log_list.append(log_line)

            for log_line in self.integrated_log_list:
                if log_line.topic == MXProtocolType.Super.MS_SCHEDULE and super_service in log_line.payload:
                    super_service_start_time = log_line.timestamp
                    break
