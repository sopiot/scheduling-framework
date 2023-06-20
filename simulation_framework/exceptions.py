class SimulationFrameworkError(Exception):
    """Base class for exceptions in this module."""

    def __init__(self, reason: str = '') -> None:
        self._reason = f'reason: {reason.strip()}' + '\n'

    @property
    def reason(self) -> str:
        return self._reason

    @reason.setter
    def reason(self, reason: str) -> None:
        self._reason = f'reason: {reason.strip()}' + '\n'


class UnsupportedError(SimulationFrameworkError):
    """Unsupported error"""

    def __init__(self, reason: str = '') -> None:
        super().__init__(reason)


class SimulationFailError(SimulationFrameworkError):
    """Simulation fail error"""

    def __init__(self, reason: str = '') -> None:
        super().__init__(reason)

    def __str__(self) -> str:
        return 'Simulation failed.' + '\n' + self._reason


class ConfigError(SimulationFrameworkError):
    """Config error"""

    def __init__(self, reason: str = '') -> None:
        super().__init__(reason)


class ConfigKeyError(ConfigError):
    """Config key error"""

    def __init__(self, key: str, reason: str = '') -> None:
        super().__init__(reason)
        self._key = key

    def __str__(self) -> str:
        return f'config_key is not valid. config_key: {self._key}' + '\n' + self._reason


class ConfigPathError(ConfigError):
    """Config path error"""

    def __init__(self, path: str, reason: str = '') -> None:
        super().__init__(reason)
        self._path = path

    def __str__(self) -> str:
        return f'config_path is not valid. config_path: {self._path}' + '\n' + self._reason


class MiddlewareTreePathError(ConfigError):
    """Middleware tree path error"""

    def __init__(self, path: str, reason: str = '') -> None:
        super().__init__(reason)
        self._path = path

    def __str__(self) -> str:
        return f'middleware_tree_path is not valid. middleware_tree_path: {self._path}' + '\n' + self._reason


class ConfigMissingError(ConfigError):
    """Config missing error"""

    def __init__(self, reason: str = '') -> None:
        super().__init__(reason)


class SSHCommandFailError(SimulationFrameworkError):
    """SSH command fail error"""

    def __init__(self, command: str, reason: str = '') -> None:
        super().__init__(reason)
        self._command = command

    def __str__(self) -> str:
        return f'SSH command failed: {self._command}' + '\n' + self._reason


class SSHConfigError(SimulationFailError):
    """SSH config error"""

    def __init__(self, reason: str = '') -> None:
        super().__init__(reason)

    def __str__(self) -> str:
        return 'SSH config error.' + '\n' + self._reason
