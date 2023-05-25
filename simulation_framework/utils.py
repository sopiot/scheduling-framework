from simulation_framework.typing import *
from termcolor import cprint, colored
from enum import Enum, auto

from tabulate import tabulate
from pathlib import Path
import os
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


def json_file_read(path: str) -> Union[dict, bool]:
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return False


def json_file_write(path: str, data: Union[str, dict], indent: int = 4) -> None:
    with open(path, 'w') as f:
        if isinstance(data, (dict, str)):
            json.dump(data, f, indent=indent)
        else:
            raise Exception(
                f'common_util.json_file_write: data type error - {type(data)}')


def get_current_time(mode: TimeFormat = TimeFormat.UNIXTIME):
    if mode == TimeFormat.DATETIME1:
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    elif mode == TimeFormat.DATETIME2:
        return time.strftime("%Y%m%d_%H%M%S", time.localtime())
    elif mode == TimeFormat.DATE:
        return time.strftime("%Y-%m-%d", time.localtime())
    elif mode == TimeFormat.TIME:
        return time.strftime("%H:%M:%S", time.localtime())
    elif mode == TimeFormat.UNIXTIME:
        return time.time()
    return time.time()


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


def write_file(path: str, content: Union[str, List[str]]) -> None:
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            if isinstance(content, str):
                f.write(content)
            elif isinstance(content, list):
                f.writelines(content)
        return path
    except FileNotFoundError as e:
        print(f'Path not found: {path}')
        raise e


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


def load_toml(path: str) -> dict:
    config = toml.load(path)
    return config


def load_yaml(path: str) -> dict:
    with open(path, 'r') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    if not config == None:
        return config
    else:
        return {}


def save_yaml(path: str, data: dict):
    with open(path, 'w') as f:
        yaml.dump(data, f, sort_keys=False)


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
