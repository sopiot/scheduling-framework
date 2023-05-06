from simulation_framework.core.elements import *
from datetime import datetime

# timestamp format: [2023/05/06 00:55:17.881]

# TODO 1: 로그 파일을 계층적으로 구성하기


class LogLine:
    def __init__(self, timestamp: str, raw_log_data: str, get_topic_func: Callable, get_payload_func: Callable) -> None:
        self._raw_log_data = raw_log_data
        self._get_topic_func = get_topic_func
        self._get_payload_func = get_payload_func

        self.timestamp = timestamp
        self.topic: str = self.get_topic(self.raw_log_data)
        self.payload: str = self.get_payload(self.raw_log_data)

    @property
    def raw_log_data(self) -> dict:
        return self._raw_log_data

    @raw_log_data.setter
    def raw_log_data(self, raw_log_data: str):
        self._raw_log_data = raw_log_data
        self.topic = self.get_topic(self._raw_log_data)
        self.payload = self.get_payload(self._raw_log_data)

    def get_topic(self, log_data: str) -> str:
        topic = self._get_topic_func(log_data)
        if not topic:
            return False

        return topic

    def get_payload(self, log_data: str) -> Union[str, dict]:
        payload = self._get_payload_func(log_data)

        if not payload:
            return False

        # 만약 payload가 json 형식이라면 json 형식으로 변환
        try:
            payload = json.loads(payload)
        except:
            pass

        return payload


class LogData:
    def __init__(self, log_path: str, timestamp_pattern: str, get_topic_func: Callable, get_payload_func: Callable) -> None:
        self._log_path = log_path
        self._log_line_list: List[LogLine] = []

        self.load(self._log_path, timestamp_pattern=timestamp_pattern, get_topic_func=get_topic_func, get_payload_func=get_payload_func)

    def load(self, log_path: str, timestamp_pattern: str, get_topic_func: Callable, get_payload_func: Callable):
        with open(log_path, 'r') as f:
            raw_log_string = f.read()

        log_line_strings = re.split(timestamp_pattern, raw_log_string)[1:]
        for i in range(0, len(log_line_strings), 2):
            timestamp = log_line_strings[i]
            message = log_line_strings[i+1]
            log_line = LogLine(timestamp=timestamp, raw_log_data=message, get_topic_func=get_topic_func, get_payload_func=get_payload_func)
            self._log_line_list.append(log_line)


class MiddlewareLog:
    def __init__(self, log_path: str, level: int, name: str) -> None:
        self._level = level
        self._name = name

        self._log_data = LogData(log_path, timestamp_pattern=r'\[(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}\.\d{3})\]',
                                 get_topic_func=self.get_topic_func,
                                 get_payload_func=self.get_payload_func)

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
        match = re.search(r'(?<=Payload: ).*', log_data)
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
                                 get_payload_func=self.get_payload_func)

    def get_topic_func(self, log_data: str) -> str:
        match = re.search(r'(?<=topic : ).*', log_data)
        if match:
            topic = match.group(0)
        else:
            return False

        return topic

    def get_payload_func(self, log_data: str) -> str:
        match = re.search(r'(?<=payload : ).*', log_data)
        if match:
            payload = match.group(0)
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
