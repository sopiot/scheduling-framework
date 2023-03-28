from typing import *
from termcolor import *

from enum import Enum
import os
import time
import re
from abc import ABCMeta, abstractmethod
from big_thing_py.common import *
from big_thing_py.utils import *
from dataclasses import dataclass, field


class SoPEventType(Enum):
    UNDEFINED = 'UNDEFINED'

    START = 'START'
    END = 'END'
    DELAY = 'DELAY'

    MIDDLEWARE_RUN = 'MIDDLEWARE_RUN'
    MIDDLEWARE_KILL = 'MIDDLEWARE_KILL'

    THING_RUN = 'THING_RUN'
    THING_KILL = 'THING_KILL'
    THING_REGISTER = 'THING_REGISTER'
    THING_UNREGISTER = 'THING_UNREGISTER'

    THING_REGISTER_RESULT = 'THING_REGISTER_RESULT'
    THING_UNREGISTER_RESULT = 'THING_UNREGISTER_RESULT'

    FUNCTION_EXECUTE = 'FUNCTION_EXECUTE'
    FUNCTION_EXECUTE_RESULT = 'FUNCTION_EXECUTE_RESULT'

    VALUE_PUBLISH = 'VALUE_PUBLISH'

    SCENARIO_VERIFY = 'SCENARIO_VERIFY'
    SCENARIO_ADD = 'SCENARIO_ADD'
    SCENARIO_RUN = 'SCENARIO_RUN'
    SCENARIO_STOP = 'SCENARIO_STOP'
    SCENARIO_UPDATE = 'SCENARIO_UPDATE'
    SCENARIO_DELETE = 'SCENARIO_DELETE'

    SCENARIO_VERIFY_RESULT = 'SCENARIO_VERIFY_RESULT'
    SCENARIO_ADD_RESULT = 'SCENARIO_ADD_RESULT'
    SCENARIO_RUN_RESULT = 'SCENARIO_RUN_RESULT'
    SCENARIO_STOP_RESULT = 'SCENARIO_STOP_RESULT'
    SCENARIO_UPDATE_RESULT = 'SCENARIO_UPDATE_RESULT'
    SCENARIO_DELETE_RESULT = 'SCENARIO_DELETE_RESULT'

    SUPER_FUNCTION_EXECUTE = 'SUPER_FUNCTION_EXECUTE'
    SUPER_FUNCTION_EXECUTE_RESULT = 'SUPER_FUNCTION_EXECUTE_RESULT'
    SUB_FUNCTION_EXECUTE = 'SUB_FUNCTION_EXECUTE'
    SUB_FUNCTION_EXECUTE_RESULT = 'SUB_FUNCTION_EXECUTE_RESULT'
    SUB_SCHEDULE = 'SUB_SCHEDULE'
    SUB_SCHEDULE_RESULT = 'SUB_SCHEDULE_RESULT'
    SUPER_SCHEDULE = 'SUPER_SCHEDULE'
    SUPER_SCHEDULE_RESULT = 'SUPER_SCHEDULE_RESULT'

    REFRESH = 'REFRESH'
    THING_REGISTER_WAIT = 'THING_REGISTER_WAIT'
    SCENARIO_ADD_CHECK = 'SCENARIO_ADD_CHECK'
    SCENARIO_RUN_CHECK = 'SCENARIO_RUN_CHECK'

    @classmethod
    def get(cls, name: str):
        try:
            return cls[name.upper()]
        except Exception:
            return cls.UNDEFINED
