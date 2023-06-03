from simulation_framework.typing import *
from termcolor import cprint, colored
from dataclasses import *
from anytree import *

from tabulate import tabulate
from pathlib import Path
import os
import re
import random
import string
import yaml
import toml
import time
import json

from big_thing_py.common.thread import SoPThread


BUSY_WAIT_TIMEOUT = 0.0001


class TimeFormat(Enum):
    DATETIME1 = '%Y-%m-%d %H:%M:%S'
    DATETIME2 = '%Y%m%d_%H%M%S'
    DATE = '%Y-%m-%d'
    TIME = '%H:%M:%S'
    UNIXTIME = 'unixtime'

    UNDEFINED = 'UNDEFINED'

    def __str__(self):
        return self.value

    @classmethod
    def get(cls, name: str):
        try:
            return cls[name.upper()]
        except Exception:
            return cls.UNDEFINED


class Direction(Enum):
    PUBLISH = 'PUBLISH'
    RECEIVED = 'RECEIVED'

    UNDEFINED = 'UNDEFINED'

    def __str__(self):
        return self.value

    @classmethod
    def get(cls, name: str):
        try:
            return cls[name.upper()]
        except Exception:
            return cls.UNDEFINED


def get_tree_node(root: object, get_children: Callable, get_target: Callable) -> Union[object, None]:
    if get_target(root):
        return root
    children_list = get_children(root)
    if not children_list:
        return None

    for children_node in get_children(root):
        found_node = get_tree_node(children_node, get_children, get_target)
        if found_node:
            return found_node

    return None


def get_tree_node_list(root, get_children: Callable):
    node_list = [root]
    children_list = get_children(root)
    if not children_list:
        return node_list

    for children_node in get_children(root):
        node_list.extend(get_tree_node_list(children_node, get_children))

    return node_list


def count_tree_node_num(root: object, get_children: Callable, filter: Callable):
    count = 0
    if filter(root):
        count += 1
    children_list = get_children(root)
    if not children_list:
        return count

    for children_node in get_children(root):
        count += count_tree_node_num(children_node, get_children, filter)

    return count


def calculate_tree_node_num(height, num_children):
    if height == 1:
        return 1

    node_count = 1
    for _ in range(num_children):
        node_count += calculate_tree_node_num(height - 1, num_children)

    return node_count


def get_tree_height(root: object, get_children: Callable):
    height = 1
    children_list = get_children(root)
    if not children_list:
        return height

    for children_node in get_children(root):
        height = max(height, get_tree_height(children_node, get_children))

    return height + 1


def find_json_pattern(payload: str) -> str:
    # 만약 payload가 json 형식이라면 json 형식으로 변환
    pattern = re.compile(r'{[\s\S]*}')
    match = pattern.search(payload)
    if not match:
        return False

    payload = match.group()
    return payload.replace('\n', '').replace(' ', '').strip()


def get_current_time(mode: TimeFormat = TimeFormat.UNIXTIME):
    if mode == TimeFormat.DATETIME1:
        cur_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    elif mode == TimeFormat.DATETIME2:
        cur_time = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    elif mode == TimeFormat.DATE:
        cur_time = time.strftime("%Y-%m-%d", time.localtime())
    elif mode == TimeFormat.TIME:
        cur_time = time.strftime("%H:%M:%S", time.localtime())
    elif mode == TimeFormat.UNIXTIME:
        cur_time = time.time()
    else:
        cur_time = time.time()

    return cur_time


def json_string_to_dict(json_string: str) -> Union[str, dict]:
    try:
        if type(json_string) in [str, bytes]:
            return json.loads(json_string)
        else:
            return json_string

    except json.JSONDecodeError as e:
        cprint(f'[json_string_to_dict] input string must be json format string... return raw string...', 'red')
        return json_string


def dict_to_json_string(dict_object: Union[dict, list, str], pretty: bool = True, indent: int = 4) -> str:
    try:
        if type(dict_object) == dict:
            if pretty:
                return json.dumps(dict_object, sort_keys=True, indent=indent)
            else:
                return json.dumps(dict_object)
        elif type(dict_object) == list:
            if pretty:
                return '\n'.join([json.dumps(item, sort_keys=True, indent=indent) for item in dict_object])
            else:
                return '\n'.join([json.dumps(item) for item in dict_object])
        else:
            if pretty:
                json.dumps(json.loads(dict_object), sort_keys=True, indent=indent)
            else:
                return str(dict_object)
    except Exception as e:
        cprint('[dict_to_json_string] ' + str(e), 'red')
        return False


def generate_random_string(len: int):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=len))


def home_dir_append(path: str, user: str = None) -> str:
    if '~' in path:
        if user:
            return path.replace('~', f'/home/{user}')
        else:
            return path.replace('~', os.path.expanduser('~'))
    else:
        return path


def unixtime_to_date(unixtime: float = None):
    return datetime.fromtimestamp(unixtime)


def get_project_root(project_name: str = 'simulation-framework') -> Path:
    start_path = Path(__file__)
    while True:
        if str(start_path).split('/')[-1] == project_name:
            return str(start_path)
        else:
            start_path = start_path.parent


def append_indent(code: str, indent: int = 1, remove_tab: bool = True):
    code_lines = code.split('\n')
    tabs = '    ' * indent
    for i, code_line in enumerate(code_lines):
        code_lines[i] = tabs + code_line
    if remove_tab:
        return '\n'.join(code_lines).replace('\t', '    ')
    else:
        return '\n'.join(code_lines)


def read_file(path: str, strip: bool = True, raw: bool = False) -> List[str]:
    try:
        with open(path, 'r') as f:
            if raw:
                return f.read()
            if strip:
                return [line.strip() for line in f.readlines()]
            else:
                return f.readlines()
    except FileNotFoundError as e:
        print(f'File not found: {path}')
        raise e


def write_file(path: str, data: Union[str, List[str]]) -> None:
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            if isinstance(data, str):
                f.write(data)
            elif isinstance(data, list):
                f.writelines(data)
        return path
    except FileNotFoundError as e:
        print(f'Path not found: {path}')
        raise e


def load_yaml(path: str) -> dict:
    with open(path, 'r') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    if not config == None:
        return config
    else:
        return None


def save_yaml(path: str, data: dict):
    with open(path, 'w') as f:
        yaml.dump(data, f, sort_keys=False)


def load_json(path: str) -> Union[dict, bool]:
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return False


def save_json(path: str, data: Union[str, dict], indent: int = 4) -> None:
    with open(path, 'w') as f:
        if isinstance(data, (dict, str)):
            json.dump(data, f, indent=indent)
        else:
            raise Exception(
                f'common_util.json_file_write: data type error - {type(data)}')


def avg(src: List[Union[int, float]]) -> float:
    non_zero_value_list = [value for value in src if value > 0]
    return sum(non_zero_value_list) / len(non_zero_value_list) if len(non_zero_value_list) > 0 else 0


def avg_timedelta(src: List[timedelta]) -> timedelta:
    non_zero_value_list = [value for value in src if value > timedelta()]
    return sum(non_zero_value_list, timedelta()) / len(non_zero_value_list) if len(non_zero_value_list) > 0 else timedelta()


def pool_map(func: Callable, args: List[Tuple], proc: int = 10) -> List[Any]:
    thread_list: List[SoPThread] = []
    for arg_chuck in [args[i:i+proc] for i in range(0, len(args), proc)]:
        for arg in arg_chuck:
            if not isinstance(arg, tuple):
                arg = (arg,)
            thread = SoPThread(target=func, args=arg)
            thread_list.append(thread)
            thread.start()

        for thread in thread_list:
            thread.join()


def print_table(table, header, scenario_name: str = None):
    title_filler = '-'
    table = tabulate(table, headers=header,
                     tablefmt='fancy_grid', numalign='left')

    if scenario_name:
        print(
            f"{f' scenario {scenario_name} ':{title_filler}^{len(table.split()[0])}}")
    print(table)
    return table
