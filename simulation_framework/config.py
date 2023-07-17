from simulation_framework.utils import *
from simulation_framework.logger import *
from anytree.importer import DictImporter
import os


class MXPath:
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


class MXSimulationConfig:
    """_summary_

    name: str
    running_time: float
    event_timeout: float
    device_pool_path: str
    service_pool_path: str

    middleware_config: MXMiddlewareConfig

    service_config: MXServiceConfig

    thing_config: MXThingConfig

    application_config: MXApplicationConfig

    """

    def __init__(self, config_path: str = None) -> None:
        self.config_path = config_path
        config = load_yaml(config_path)
        if not config:
            raise ConfigPathError(config_path=config_path)

        self.name: str = config['simulation'].get('name', os.path.basename(config_path).split('.')[0])
        self.running_time: float = config['simulation'].get('running_time', 120.0)
        self.event_timeout: float = config['simulation'].get('event_timeout', 15.0)

        self.device_pool_path = MXPath(config_path=os.path.abspath(config_path),
                                       path=config['simulation'].get('device_pool_path', 'device_pool.yml'))
        self.service_thing_pool_path = MXPath(config_path=os.path.abspath(config_path),
                                              path=config['simulation'].get('service_thing_pool_path', 'service_thing_pool.json'))
        self.force_generate = config['simulation'].get('force_generate', False)
        self.local_mode = config['simulation'].get('local_mode', False)

        self.middleware_config = MXMiddlewareConfig(config['middleware'], config_path)
        self.service_config = MXServiceConfig(config['service'])
        self.thing_config = MXThingConfig(config['thing'])
        self.application_config = MXApplicationConfig(config['application'])

    # TODO: implement this
    def dict(self):
        raise NotImplementedError
        return dict(config_path=self.config_path,
                    name=self.name,
                    running_time=self.running_time,
                    event_timeout=self.event_timeout,
                    device_pool_path=self.device_pool_path,
                    service_thing_pool_path=self.service_thing_pool_path,
                    force_generate=self.force_generate,
                    local_mode=self.local_mode,
                    middleware_config=self.middleware_config.dict(),
                    service_config=self.service_config.dict(),
                    thing_config=self.thing_config.dict(),
                    application_config=self.application_config.dict())


class MXMiddlewareConfig:
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
        MZTEST_LOG_DEBUG: _description_
    """

    class RandomConfig:

        class DetailConfig:
            def __init__(self, data: dict) -> None:
                self.thing_per_middleware: ConfigRandomIntRange = data['thing_per_middleware']
                self.scenario_per_middleware: ConfigRandomIntRange = data['application_per_middleware']

        def __init__(self, data: dict) -> None:
            self.height: ConfigRandomIntRange = data['height']
            self.width: ConfigRandomIntRange = data['width']

            self.normal = MXMiddlewareConfig.RandomConfig.DetailConfig(data['normal'])
            self.super = MXMiddlewareConfig.RandomConfig.DetailConfig(data['super'])

    def __init__(self, data: dict, config_path: str) -> None:
        self.device_pool: List[str] = data.get('device', None)
        self.remote_middleware_path: str = data.get('remote_middleware_path', '/tmp/middleware')
        self.remote_middleware_config_path: str = data.get('remote_middleware_config_path', '/tmp/middleware_config')

        self.manual = MXPath(config_path=os.path.abspath(config_path),
                             path=data.get('manual', ''))
        self.manual_middleware_tree: AnyNode = None

        if self.manual.abs_path():
            importer = DictImporter()
            manual_middleware_tree_dict = load_yaml(self.manual.abs_path())
            if not manual_middleware_tree_dict:
                raise MiddlewareTreePathError(path=self.manual.abs_path())
            self.manual_middleware_tree = importer.import_(manual_middleware_tree_dict)
        self.random = MXMiddlewareConfig.RandomConfig(data['random']) if 'random' in data else None
        if not 'manual' in data and not 'random' in data:
            raise ConfigMissingError('Either "random" or "manual" must be specified in config. Please provide at least one of them.')


class MXServiceConfig:
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

        self.normal = MXServiceConfig.NormalConfig(data['normal'])
        self.super = MXServiceConfig.SuperConfig(data['super'])


class MXThingConfig:
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

            self.fail_error_rate: float = data['fail_error_rate']
            self.broken_rate: float = data['broken_rate']
            self.unregister_rate: float = data['unregister_rate']

    def __init__(self, data: dict) -> None:
        self.remote_thing_folder_path: str = data.get('remote_thing_folder_path', '/tmp/thing')
        self.device_pool: List[str] = data.get('device', None)

        self.normal = MXThingConfig.DetailConfig(data['normal'])
        self.super = MXThingConfig.DetailConfig(data['super'])


class MXApplicationConfig:
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
        self.normal = MXApplicationConfig.DetailConfig(data['normal'])
        self.super = MXApplicationConfig.DetailConfig(data['super'])
