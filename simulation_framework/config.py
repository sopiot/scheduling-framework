from simulation_framework.utils import *
from simulation_framework.logger import *
from anytree.importer import DictImporter
import os


class SoPPath:
    def __init__(self, config_path: str, path: str) -> None:
        self.config_path = config_path
        self.path = path

    def __str__(self) -> str:
        return self.abs_path()

    def abs_path(self):
        path = ''
        if not self.path:
            return None
        elif '${ROOT}' in self.path:
            path = self.path.replace('${ROOT}', str(get_project_root()))
        elif './' in self.path:
            path = self.path.replace('./', f'{os.path.dirname(self.config_path)}/')
        elif '~' in self.path:
            path = home_dir_append(path=self.path)
        else:
            path = os.path.join(os.path.dirname(self.config_path), self.path)

        return path


class SoPSimulationConfig:
    """_summary_

    name: str
    running_time: float
    event_timeout: float
    device_pool_path: str
    service_pool_path: str

    middleware_config: SoPMiddlewareConfig

    service_config: SoPServiceConfig

    thing_config: SoPThingConfig

    application_config: SoPApplicationConfig

    """

    def __init__(self, config_path: str = None) -> None:
        self.config_path = config_path
        config = load_yaml(config_path)
        if not config:
            raise ValueError(f'config_path is not valid. config_path: {config_path}')

        self.name: str = config['simulation'].get('name', os.path.basename(config_path).split('.')[0])
        self.running_time: float = config['simulation'].get('running_time', 120.0)
        self.event_timeout: float = config['simulation'].get('event_timeout', 15.0)

        self.device_pool_path = SoPPath(config_path=os.path.abspath(config_path),
                                        path=config['simulation'].get('device_pool_path', 'device_pool.yml'))
        self.service_thing_pool_path = SoPPath(config_path=os.path.abspath(config_path),
                                               path=config['simulation'].get('service_thing_pool_path', 'service_thing_pool.json'))
        self.local_mode = config['simulation'].get('local_mode', False)
        self.middleware_config = SoPMiddlewareConfig(config['middleware'], config_path)
        self.service_config = SoPServiceConfig(config['service'])
        self.thing_config = SoPThingConfig(config['thing'])
        self.application_config = SoPApplicationConfig(config['application'])


class SoPMiddlewareConfig:
    """_summary_

    device_pool: List[str]
    remote_middleware_path: str
    remote_middleware_config_path: str

    manual: str

    random: 
        height: ConfigRandomIntRange
        width: ConfigRandomIntRange
        normal:
            thing_per_middleware: ConfigRandomIntRange
            application_per_middleware: ConfigRandomIntRange
        super:
            thing_per_middleware: ConfigRandomIntRange
            application_per_middleware: ConfigRandomIntRange

    Raises:
        SOPTEST_LOG_DEBUG: _description_
    """

    class RandomConfig:

        class DetailConfig:
            def __init__(self, data: dict) -> None:
                self.thing_per_middleware: ConfigRandomIntRange = data['thing_per_middleware']
                self.scenario_per_middleware: ConfigRandomIntRange = data['application_per_middleware']

        def __init__(self, data: dict) -> None:
            self.height: ConfigRandomIntRange = data['height']
            self.width: ConfigRandomIntRange = data['width']

            self.normal = SoPMiddlewareConfig.RandomConfig.DetailConfig(data['normal'])
            self.super = SoPMiddlewareConfig.RandomConfig.DetailConfig(data['super'])

    def __init__(self, data: dict, config_path: str) -> None:
        self.device_pool: List[str] = data.get('device', None)
        self.remote_middleware_path: str = data.get('remote_middleware_path', '~/middleware')
        self.remote_middleware_config_path: str = data.get('remote_middleware_config_path', '/mnt/ramdisk/middleware_config')

        self.manual = SoPPath(config_path=os.path.abspath(config_path),
                              path=data.get('manual', ''))
        self.manual_middleware_tree: AnyNode = None

        if self.manual.abs_path():
            importer = DictImporter()
            manual_middleware_tree_dict = load_yaml(self.manual.abs_path())
            self.manual_middleware_tree = importer.import_(manual_middleware_tree_dict)
        self.random = SoPMiddlewareConfig.RandomConfig(data['random']) if 'random' in data else None
        if not 'manual' in data and not 'random' in data:
            raise SOPTEST_LOG_DEBUG(f'random: and manual: are not set...', SoPTestLogLevel.FAIL)


class SoPServiceConfig:
    """_summary_

    tag_type_num: int
    tag_per_service: ConfigRandomIntRange

    normal:
        service_type_num: int
        energy: ConfigRandomIntRange
        execute_time: ConfigRandomIntRange
    super:
        service_type_num: int
        service_per_super_service: ConfigRandomIntRange

    """

    class NormalConfig:
        def __init__(self, data: dict) -> None:
            self.service_type_num: int = data['service_type_num']
            self.energy: ConfigRandomIntRange = data['energy']
            self.execute_time: ConfigRandomIntRange = data['execute_time']

    class SuperConfig:
        def __init__(self, data: dict) -> None:
            self.service_type_num: int = data['service_type_num']
            self.service_per_super_service: ConfigRandomIntRange = data['service_per_super_service']

    def __init__(self, data: dict) -> None:
        self.tag_type_num: int = data.get('tag_type_num', 1)
        self.tag_per_service: ConfigRandomIntRange = data.get('tag_per_service', [1, 1])

        self.normal = SoPServiceConfig.NormalConfig(data['normal'])
        self.super = SoPServiceConfig.SuperConfig(data['super'])


class SoPThingConfig:
    """_summary_

    remote_thing_folder_path: str
    device_pool: List[str]

    normal:
        service_per_thing: ConfigRandomIntRange
        fail_error_rate: int
        broken_rate: int
    super:
        service_per_thing: ConfigRandomIntRange
        fail_error_rate: int
        broken_rate: int

    """

    class DetailConfig:
        def __init__(self, data: dict) -> None:
            self.service_per_thing: ConfigRandomIntRange = data['service_per_thing']

            self.fail_error_rate: int = data['fail_error_rate']
            self.broken_rate: int = data['broken_rate']
            self.unregister_rate: int = data['unregister_rate']

    def __init__(self, data: dict) -> None:
        self.remote_thing_folder_path: str = data.get('remote_thing_folder_path', '/mnt/ramdisk/thing')
        self.device_pool: List[str] = data.get('device', None)

        self.normal = SoPThingConfig.DetailConfig(data['normal'])
        self.super = SoPThingConfig.DetailConfig(data['super'])


class SoPApplicationConfig:
    """_summary_

    normal:
        service_per_application: ConfigRandomIntRange
        period: ConfigRandomFloatRange
    super:
        service_per_application: ConfigRandomIntRange
        period: ConfigRandomFloatRange

    """

    class DetailConfig:
        def __init__(self, data: dict) -> None:
            self.service_per_application: ConfigRandomIntRange = data['service_per_application']
            self.period: ConfigRandomFloatRange = data['period']

    def __init__(self, data: dict) -> None:
        self.normal = SoPApplicationConfig.DetailConfig(data['normal'])
        self.super = SoPApplicationConfig.DetailConfig(data['super'])
