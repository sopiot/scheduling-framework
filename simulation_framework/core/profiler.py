from simulation_framework.core.elements import *
from datetime import datetime

# timestamp format: [2023/05/06 00:55:17.881]

# TODO 1: 로그 파일을 계층적으로 구성하기


class LogLine:
    def __init__(self, timestamp: str, raw_log_data: str, get_topic_func: Callable, get_payload_func: Callable, element_type: MXElementType) -> None:
        self._raw_log_data = raw_log_data
        self._get_topic_func = get_topic_func
        self._get_payload_func = get_payload_func
        self.element_type = element_type

        self._timestamp = datetime.strptime(timestamp, '%Y/%m/%d %H:%M:%S.%f')
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
    def raw_log_data(self) -> dict:
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
        self._timestamp = datetime.strptime(timestamp, '%Y/%m/%d %H:%M:%S.%f')

    def timestamp_str(self) -> str:
        return self._timestamp.strftime('%Y/%m/%d %H:%M:%S.%f')


class LogData:
    def __init__(self, log_path: str, timestamp_pattern: str, get_topic_func: Callable, get_payload_func: Callable, element_type: MXElementType) -> None:
        self._log_path = log_path
        self._log_line_list: List[LogLine] = []
        self._element_type = element_type

        self.load(self._log_path, timestamp_pattern=timestamp_pattern, get_topic_func=get_topic_func, get_payload_func=get_payload_func)

    def load(self, log_path: str, timestamp_pattern: str, get_topic_func: Callable, get_payload_func: Callable):
        with open(log_path, 'r') as f:
            raw_log_string = f.read()

        log_line_strings = re.split(timestamp_pattern, raw_log_string)[1:]
        for i in range(0, len(log_line_strings), 2):
            timestamp = log_line_strings[i]
            message = log_line_strings[i+1]
            log_line = LogLine(timestamp=timestamp, raw_log_data=message, get_topic_func=get_topic_func, get_payload_func=get_payload_func, element_type=self._element_type)
            self._log_line_list.append(log_line)


class MiddlewareLog:
    def __init__(self, log_path: str, level: int, name: str) -> None:
        self._level = level
        self._name = name

        self._log_data = LogData(log_path, timestamp_pattern=r'\[(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}\.\d{3})\]',
                                 get_topic_func=self.get_topic_func,
                                 get_payload_func=self.get_payload_func,
                                 element_type=MXElementType.MIDDLEWARE)

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
        self._level = level
        self._name = name
        self._is_super = is_super

        self._log_data = LogData(log_path, timestamp_pattern=r'\[(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}\.\d{3})\]',
                                 get_topic_func=self.get_topic_func,
                                 get_payload_func=self.get_payload_func,
                                 element_type=MXElementType.THING)

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
        self._root_log_folder_path = root_log_folder_path
        self._middleware_log_list: List[MiddlewareLog] = []
        self._thing_log_list: List[ThingLog] = []

        self.load(self._root_log_folder_path)

    def get_middleware_log(self, path: str) -> MiddlewareLog:
        file_list = os.listdir(path)
        for file in file_list:
            if not '.log' in file:
                continue
            middleware_name = file.split('.')[0]
            middleware_level = int(path.split(os.sep)[-2].split('.')[1].split('level')[1])
            middleware_log_path = os.path.join(path, file)
            middleware_log = MiddlewareLog(log_path=middleware_log_path, level=middleware_level, name=middleware_name)

            return middleware_log

    def get_thing_log_list(self, path: str) -> List[ThingLog]:
        try:
            file_list = os.listdir(path)
        except Exception as e:
            return []

        thing_log_list = []
        for file in file_list:
            if not '.log' in file:
                continue
            thing_name = file.split('.')[0]
            thing_level = int(path.split(os.sep)[-2].split('.')[1].split('level')[1])
            thing_log_path = os.path.join(path, file)
            is_super = True if 'super' in thing_name else False
            thing_log = ThingLog(log_path=thing_log_path, level=thing_level, name=thing_name, is_super=is_super)
            thing_log_list.append(thing_log)

        return thing_log_list

    def load(self, root_log_folder_path: str):
        for root, dirs, files in os.walk(root_log_folder_path):

            for dir in dirs:
                if not len(dir.split('.')) == 3:
                    continue

                middleware_log = self.get_middleware_log(os.path.join(root, dir, 'middleware'))
                thing_log_list = self.get_thing_log_list(os.path.join(root, dir, 'thing'))
                self._middleware_log_list.append(middleware_log)
                self._thing_log_list.extend(thing_log_list)

    def export_to_one_file(self) -> List[LogLine]:
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

        whole_log_data: List[LogLine] = []
        for middleware_log in self._middleware_log_list:
            whole_log_data.extend([log_line for log_line in middleware_log._log_data._log_line_list
                                   if isinstance(log_line.topic, str) and MXProtocolType.get(log_line.topic) in topic_filter])
        for thing_log in self._thing_log_list:
            whole_log_data.extend([log_line for log_line in thing_log._log_data._log_line_list
                                   if isinstance(log_line.topic, str) and MXProtocolType.get(log_line.topic) in topic_filter])

        whole_log_data.sort(key=lambda x: x.timestamp)

        with open('whole_log_file.txt', 'w') as f:
            for log_line in whole_log_data:
                f.write(f'[{log_line.timestamp}][{"T" if log_line.element_type == MXElementType.THING else "M"}] {log_line.topic} {log_line.payload}\n')

        return whole_log_data
