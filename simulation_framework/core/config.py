from simulation_framework.utils import *


class SoPPath:
    def __init__(self, project_root_path: str, config_path: str, path: str) -> None:
        self.project_root_path = project_root_path
        self.config_path = config_path
        self.path = path

    def __str__(self) -> str:
        return self.abs_path()

    def abs_path(self):
        path = ''
        if not self.path:
            return None
        elif '${ROOT}' in self.path:
            path = self.path.replace(
                '${ROOT}', str(self.project_root_path))
        elif './' in self.path:
            path = self.path.replace(
                './', f'{os.path.dirname(self.config_path)}/')
        elif '~' in self.path:
            path = home_dir_append(path=self.path)
        else:
            path = os.path.join(os.path.dirname(self.config_path), self.path)

        return path


class SoPSimulationConfig:
    def __init__(self, config_path: str = None, config: dict = None) -> None:
        self.path = config_path
        if not config and self.path:
            data = load_yaml(self.path)
        elif config and not self.path:
            data = config
        else:
            raise Exception('config_path and config are both None.')

        self.name: str = data['simulation'].get(
            'name', os.path.basename(self.path).split('.')[0])
        self.running_time: float = data['simulation'].get(
            'running_time', 120.0)
        self.event_timeout: float = data['simulation'].get(
            'event_timeout', 15.0)

        self.device_pool_path = SoPPath(project_root_path=get_project_root(),
                                        config_path=os.path.abspath(
                                            self.path),
                                        path=data.get('device_pool_path', 'device_pool.yml'))
        self.middleware_config = SoPMiddlewareConfig(
            data['middleware'], self.path)
        self.service_config = SoPServiceConfig(data['service'])
        self.thing_config = SoPThingConfig(data['thing'])
        self.application_config = SoPApplicationConfig(data['application'])


class SoPMiddlewareConfig:

    class RandomConfig:

        class DetailConfig:
            def __init__(self, data: dict) -> None:
                self.thing_per_middleware: Tuple[int] = data['thing_per_middleware']
                self.scenario_per_middleware: Tuple[int] = data['application_per_middleware']

        def __init__(self, data: dict) -> None:
            self.height: Tuple[int] = data['height']
            self.width: Tuple[int] = data['width']

            self.normal = SoPMiddlewareConfig.RandomConfig.DetailConfig(
                data['normal'])
            self.super = SoPMiddlewareConfig.RandomConfig.DetailConfig(
                data['super'])

    def __init__(self, data: dict, config_path: str) -> None:
        self.device_pool: List[str] = data.get('device', None)
        self.remote_middleware_path: str = data.get(
            'remote_middleware_path', '~/middleware')
        self.remote_middleware_config_path: str = data.get(
            'remote_middleware_config_path', '/mnt/ramdisk/middleware_config')

        self.manual = SoPPath(project_root_path=get_project_root(),
                              config_path=os.path.abspath(config_path),
                              path=data.get('manual', ''))
        self.random = SoPMiddlewareConfig.RandomConfig(
            data['random']) if 'random' in data else None
        if not 'manual' in data and not 'random' in data:
            raise SOPTEST_LOG_DEBUG(
                f'random: and manual: are not set...', SoPTestLogLevel.FAIL)


class SoPServiceConfig:

    class NormalConfig:
        def __init__(self, data: dict) -> None:
            self.service_type_num: int = data['service_type_num']
            self.energy: Tuple[int] = data['energy']
            self.execute_time: Tuple[int] = data['execute_time']

    class SuperConfig:
        def __init__(self, data: dict) -> None:
            self.service_type_num: int = data['service_type_num']
            self.service_per_super_service: Tuple[int] = data['service_per_super_service']

    def __init__(self, data: dict) -> None:
        self.tag_type_num: int = data.get('tag_type_num', 1)
        self.tag_per_service: Tuple[int] = data.get('tag_per_service', [1, 1])

        self.normal = SoPServiceConfig.NormalConfig(data['normal'])
        self.super = SoPServiceConfig.SuperConfig(data['super'])


class SoPThingConfig:

    class DetailConfig:
        def __init__(self, data: dict) -> None:
            self.service_per_thing: Tuple[int] = data['service_per_thing']

            self.fail_error_rate: int = data['fail_error_rate']
            self.broken_rate: int = data['broken_rate']
            self.unregister_rate: int = data['unregister_rate']

    def __init__(self, data: dict) -> None:
        self.remote_thing_folder_path: str = data.get(
            'remote_thing_folder_path', '/mnt/ramdisk/thing')
        self.device_pool: List[str] = data.get('device', None)

        self.normal = SoPThingConfig.DetailConfig(data['normal'])
        self.super = SoPThingConfig.DetailConfig(data['super'])


class SoPApplicationConfig:

    class DetailConfig:
        def __init__(self, data: dict) -> None:
            self.service_per_application: List[int] = data['service_per_application']
            self.period: List[float] = data['period']

    def __init__(self, data: dict) -> None:
        self.normal = SoPApplicationConfig.DetailConfig(data['normal'])
        self.super = SoPApplicationConfig.DetailConfig(data['super'])
