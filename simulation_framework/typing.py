from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional, Tuple, List, Union, TypeVar
from enum import Enum, auto

ReturnType = Union[int, float, bool, str]
ConfigRandomFloatRange = Tuple[float, float]
ConfigRandomIntRange = Tuple[int, int]
