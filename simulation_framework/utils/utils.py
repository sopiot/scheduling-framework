from simulation_framework.common import *
from big_thing_py.utils.log_util import *
from string import Template


from pathlib import Path
import yaml
import toml
import datetime
import random
import requests
import string
import shutil
import subprocess

from tabulate import tabulate


class MXTestLogLevel(Enum):
    PASS = 'PASS'
    WARN = 'WARN'
    INFO = 'INFO'
    FAIL = 'FAIL'


def MXTEST_LOG_DEBUG(msg: str, error: MXTestLogLevel = MXTestLogLevel.PASS, color: str = None, e: Exception = None, progress: float = None):
    # error = 0  : PASS ✅
    # error = 1  : WARN ⚠ -> use b'\xe2\x9a\xa0\xef\xb8\x8f'.decode()
    # error = -1 : FAIL ❌
    log_msg = ''
    WARN_emoji = b'\xe2\x9a\xa0\xef\xb8\x8f'.decode()
    progress_status = ''
    if progress:
        progress_status = f'[{progress*100:.3f}%]'

    if error == MXTestLogLevel.PASS:
        log_msg = f'{progress_status} [PASS✅] {msg} --> {str(e)}'
        MXLOG_DEBUG(log_msg, 'green' if not color else color)
    elif error == MXTestLogLevel.WARN:
        log_msg = f'{progress_status} [WARN{WARN_emoji} ] {msg} --> {str(e)}'
        MXLOG_DEBUG(log_msg, 'yellow' if not color else color)
    elif error == MXTestLogLevel.INFO:
        log_msg = f'{progress_status} [INFOℹ️ ] {msg} --> {str(e)}'
        MXLOG_DEBUG(log_msg, 'cyan' if not color else color)
    elif error == MXTestLogLevel.FAIL:
        log_msg = f'{progress_status} [FAIL❌] {msg} --> {str(e)}'
        MXLOG_DEBUG(log_msg, 'red' if not color else color)
        return e


def topic_seperator(topic: MXProtocolType, back_num: int):
    topic_slice = topic.value.split('/')
    for _ in range(back_num):
        topic_slice.pop()

    result = '/'.join(topic_slice)
    return result


def get_mapped_thing_list(schedule_info: dict, function_name: str = None, all_prefix: bool = False):
    if function_name:
        for mapping_info in schedule_info:
            if not all_prefix:
                if mapping_info['service'].split('.')[1] == function_name:
                    return mapping_info['things']
            elif mapping_info['service'].split('.')[1] == function_name and '*' in mapping_info['service']:
                return mapping_info['things']
    else:
        return [
            {
                'function_name': mapping_info['service'].split('.')[1],
                'thing_list': [thing['id'] for thing in mapping_info['things']]
            } for mapping_info in schedule_info
        ]


def len_no_ansi(string):
    import re
    return len(re.sub(
        r'[\u001B\u009B][\[\]()#;?]*((([a-zA-Z\d]*(;[-a-zA-Z\d\/#&.:=?%@~_]*)*)?\u0007)|((\d{1,4}(?:;\d{0,4})*)?[\dA-PR-TZcf-ntqry=><~]))', '', string))


def len_ansi(string):
    import re
    return len(string) - len(re.sub(
        r'[\u001B\u009B][\[\]()#;?]*((([a-zA-Z\d]*(;[-a-zA-Z\d\/#&.:=?%@~_]*)*)?\u0007)|((\d{1,4}(?:;\d{0,4})*)?[\dA-PR-TZcf-ntqry=><~]))', '', string))


def home_dir_append(path: str, user: str = None) -> str:
    if '~' in path:
        if user:
            return path.replace('~', f'/home/{user}')
        else:
            return path.replace('~', os.path.expanduser('~'))
    else:
        return path


def get_upper_path(path: str):
    path = Path(path)
    return path.parent.absolute()


def unixtime_to_date(unixtime: float = None):
    return datetime.datetime.fromtimestamp(unixtime)


def exception_wrapper(func: Callable = None,
                      empty_case_func: Callable = None,
                      key_error_case_func: Callable = None,
                      else_case_func: Callable = None,
                      final_case_func: Callable = None,):
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Empty as e:
            print_error(e)
            if empty_case_func:
                return empty_case_func()
        except KeyError as e:
            print_error(e)
            if key_error_case_func:
                return key_error_case_func()
        except KeyboardInterrupt as e:
            print('KeyboardInterrupt')
            if self.__class__.__name__ == 'MXSimulatorExecutor':
                self.event_handler.kill_all_simulation_instance()
                user_input = input(
                    'Select exit mode[1].\n1. Just exit\n2. Download remote logs\n') or '1'
                if user_input == '1':
                    cprint(f'Exit whole simulation...', 'red')
                    exit(0)
                elif user_input == '2':
                    cprint(f'Download remote logs...', 'yellow')
                    self.event_handler.download_log_file()
                    exit(0)
                else:
                    pass
        except Exception as e:
            if e is Empty:
                print_error(e)
                if empty_case_func:
                    return empty_case_func()
            elif e in [ValueError, IndexError, TypeError, KeyError]:
                print_error(e)
            else:
                print_error(e)
                self.event_handler.kill_all_simulation_instance()
                # if self.__class__.__name__ == 'MXSimulator':
                #     user_input = input(
                #         'kill_all_simulation_instance before exit? (y/n)[Y]: ') or 'y'
                #     if user_input == 'y':
                #         self.event_handler.kill_all_simulation_instance()
                #     else:
                #         pass
            print_error(e)
            raise e
        finally:
            if final_case_func:
                final_case_func()
    return wrapper


def check_result_payload(payload: dict = None):
    if not payload:
        MXTEST_LOG_DEBUG(f'Payload is None (timeout)!!!',
                         MXTestLogLevel.FAIL)
        return None

    error_code = payload['error']
    error_string = payload.get('error_string', None)

    if error_code in [0, -4]:
        return True
    else:
        MXTEST_LOG_DEBUG(
            f'error_code: {error_code}, error_string : {error_string if error_string else "(No error string)"}', MXTestLogLevel.FAIL)
        return False


def generate_random_words(word_num: int = None, custom_words_file: List[str] = [], ban_word_list: List[str] = []) -> List[str]:
    picked_words = []
    whole_words = []

    if not custom_words_file:

        # 만약 service_names.txt파일이 존재한다면 해당 파일을 읽어온다.
        res_path = f'{get_project_root()}/res'
        if os.path.exists(f'{res_path}/service_names.txt'):
            whole_words: List[str] = read_file(
                f'{res_path}/service_names.txt')
        else:
            response = requests.get(
                "https://www.mit.edu/~ecprice/wordlist.10000")
            whole_words = [word.decode() + '\n'
                           for word in response.content.splitlines()]
            os.makedirs(
                f'{res_path}', exist_ok=True)
            with open(f'{res_path}/service_names.txt', 'w') as f:
                f.writelines(whole_words)
        for ban_word in ban_word_list:
            if ban_word not in whole_words:
                continue
            whole_words.remove(ban_word)
    else:
        file: List[str] = read_file(custom_words_file)
        whole_words = [line.strip() for line in file]

    while len(picked_words) < word_num:
        picked_word = random.choice(whole_words)
        if picked_word in picked_words:
            continue
        picked_words.append(picked_word)

    if not len(picked_words) == word_num:
        raise Exception(
            f'word_num is not matched. word_num: {word_num}, picked_words: {picked_words}')
    return list(set(picked_words))


def get_middleware_list_recursive(middleware: object = None) -> List[object]:
    middleware_list = [middleware]

    for child_middleware in middleware.child_middleware_list:
        middleware_list.extend(
            get_middleware_list_recursive(child_middleware))

    middleware_list = sorted(
        middleware_list, key=lambda x: x.level, reverse=True)
    return middleware_list


def get_thing_list_recursive(middleware: object = None) -> List[object]:
    thing_list = [thing for thing in middleware.thing_list]

    for child_middleware in middleware.child_middleware_list:
        thing_list.extend(get_thing_list_recursive(child_middleware))

    thing_list = sorted(
        thing_list, key=lambda x: x.level, reverse=True)
    return thing_list


def get_scenario_list_recursive(middleware: object = None) -> List[object]:
    scenario_list = [scenario for scenario in middleware.scenario_list]

    for child_middleware in middleware.child_middleware_list:
        scenario_list.extend(get_scenario_list_recursive(child_middleware))

    scenario_list = sorted(
        scenario_list, key=lambda x: x.level, reverse=True)
    return scenario_list


def find_element_recursive(middleware: object, element: object, key: Callable = lambda x: x) -> Tuple[object, object]:

    def inner(middleware: object, element: object):
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


def find_element_by_name_recursive(middleware: object, element_name: str):

    def inner(middleware: object, element_name: str):
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


def append_indent(code: str, indent: int = 1, remove_tab: bool = True):
    code_lines = code.split('\n')
    tabs = '    ' * indent
    for i, code_line in enumerate(code_lines):
        code_lines[i] = tabs + code_line
    if remove_tab:
        return '\n'.join(code_lines).replace('\t', '    ')
    else:
        return '\n'.join(code_lines)


def generate_random_string(len: int):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=len))


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


def pool_map(func: Callable, args: List[Tuple], proc: int = 10) -> List[Any]:
    thread_list: List[MXThread] = []
    for arg_chuck in [args[i:i+proc] for i in range(0, len(args), proc)]:
        for arg in arg_chuck:
            if not isinstance(arg, tuple):
                arg = (arg,)
            thread = MXThread(target=func, args=arg)
            thread_list.append(thread)
            thread.start()

        for thread in thread_list:
            thread.join()


def move_file(src_path, dest_path):
    shutil.move(src_path, dest_path)


def copy_file(src_path, dest_path):
    shutil.copy(src_path, dest_path)


def get_project_root(project_name: str = 'simulation-framework') -> Path:
    start_path = Path(__file__)
    while True:
        if str(start_path).split('/')[-1] == project_name:
            return str(start_path)
        else:
            start_path = start_path.parent


def execute_command(command: str, print_output: bool = True) -> subprocess.CompletedProcess:
    result = subprocess.run(command,
                            stdout=subprocess.STDOUT if print_output else subprocess.DEVNULL,
                            stderr=subprocess.STDOUT if print_output else subprocess.DEVNULL,
                            shell=True)
    return result


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
        print_error(e)
        MXLOG_DEBUG(f'File not found: {path}')
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
        print_error(e)
        MXLOG_DEBUG(f'Path not found: {path}')
        raise e


def print_table(table, header, scenario_name: str = None):
    title_filler = '-'
    table = tabulate(table, headers=header,
                     tablefmt='fancy_grid', numalign='left')

    if scenario_name:
        print(
            f"{f' scenario {scenario_name} ':{title_filler}^{len(table.split()[0])}}")
    print(table)
    return table


# def randint(min: int, max: int) -> int:
#     return random.randint(min, max)


# def randfloat(min: float, max: float) -> float:
#     return random.uniform(min, max)


# def randbool(weight: Tuple[float, float] = (1, 1)) -> bool:
#     return random.choices([True, False], weights=[weight[0], 1 - weight[1]])
