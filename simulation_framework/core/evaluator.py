from simulation_framework.core.event_handler import *
from simulation_framework.profiler import *

import csv
from itertools import zip_longest


class MXExecuteCycleErrorType(Enum):
    SUCCESS = 'SUCCESS'
    PERIOD_FAIL = 'PERIOD_FAIL'
    RERUN_FAIL = 'RERUN_FAIL'
    SERVICE_ORDER_FAIL = 'SERVICE_ORDER_FAIL'
    OVERTIME = 'OVERTIME'

    UNDEFINED = 'UNDEFINED'

    def __str__(self):
        return self.value

    @classmethod
    def get(cls, name: str):
        try:
            return cls[name.upper()]
        except Exception:
            return cls.UNDEFINED


class MXScenarioErrorType(Enum):
    SUCCESS = 'SUCCESS'
    FAIL = 'FAIL'
    SCHEDULE_FAIL = 'SCHEDULE_FAIL'
    SCHEDULE_TIMEOUT = 'SCHEDULE_TIMEOUT'

    UNDEFINED = 'UNDEFINED'

    def __str__(self):
        return self.value

    @classmethod
    def get(cls, name: str):
        try:
            return cls[name.upper()]
        except Exception:
            return cls.UNDEFINED


class MXExecuteCycleResult:
    def __init__(self, execute_cycle: List[MXEvent] = [], cycle_latency: int = 0, cycle_energy: int = 0, avg_execute_time: int = 0, overhead: float = 0, error: MXExecuteCycleErrorType = None) -> None:
        self.execute_event_cycle: List[MXEvent] = execute_cycle

        self.cycle_latency = cycle_latency
        self.cycle_energy = cycle_energy
        self.avg_execute_time = avg_execute_time
        self.overhead = overhead
        self.error = error


class MXScenarioResult:
    def __init__(self, scenario_component: MXScenario = None,
                 execute_cycle_result_list: List[MXExecuteCycleResult] = [],
                 schedule_event_list: List[MXEvent] = [],
                 avg_schedule_latency: int = 0,
                 avg_latency: int = 0,
                 avg_energy: int = 0,
                 avg_execute_time: int = 0,
                 avg_overhead: int = 0,
                 total_scenario_cycle_num: int = 0,
                 error: MXScenarioErrorType = None) -> None:
        self.scenario_component: MXScenario = scenario_component

        self.execute_cycle_result_list = execute_cycle_result_list
        self.schedule_event_list = schedule_event_list

        self.avg_schedule_latency = avg_schedule_latency
        self.avg_latency = avg_latency
        self.avg_energy = avg_energy
        self.avg_execute_time = avg_execute_time
        self.avg_overhead = avg_overhead
        self.total_scenario_cycle_num = total_scenario_cycle_num
        self.error: MXScenarioErrorType = error


class MXMiddlewareResult:
    def __init__(self, middleware_component: MXMiddleware,
                 scenario_result_list: List[MXScenarioResult] = [], local_scenario_result_list: List[MXScenarioResult] = [], super_scenario_result_list: List[MXScenarioResult] = [],
                 total_scenario_num: List[int] = [0, 0, 0], timeout_scenario_num: List[int] = [0, 0, 0], denied_scenario_num: List[int] = [0, 0, 0], failed_scenario_num: List[int] = [0, 0, 0],
                 avg_latency: List[int] = [0, 0, 0], avg_execute_time: List[int] = [0, 0, 0], avg_schedule_latency: List[int] = [0, 0, 0], avg_energy: List[int] = [0, 0, 0], avg_overhead: List[int] = [0, 0, 0]) -> None:
        self.middleware_component = middleware_component
        self.scenario_result_list = scenario_result_list
        self.local_scenario_result_list = local_scenario_result_list
        self.super_scenario_result_list = super_scenario_result_list

        self.total_scenario_num = total_scenario_num
        self.timeout_scenario_num = timeout_scenario_num
        self.denied_scenario_num = denied_scenario_num
        self.failed_scenario_num = failed_scenario_num

        self.avg_latency = avg_latency
        self.avg_execute_time = avg_execute_time
        self.avg_schedule_latency = avg_schedule_latency
        self.avg_energy = avg_energy
        self.avg_overhead = avg_overhead

        self.total_scenario_cycle_num = sum([scenario.cycle_count for scenario in self.middleware_component.scenario_list])
        self.total_execute_count = len([event for event in self.middleware_component.event_log
                                        if event.event_type in [MXEventType.FUNCTION_EXECUTE, MXEventType.SUB_FUNCTION_EXECUTE]])
        self.total_execute_time = sum([event.duration for event in self.middleware_component.event_log
                                       if event.event_type in [MXEventType.FUNCTION_EXECUTE, MXEventType.SUB_FUNCTION_EXECUTE]])


class MXSimulationResult:
    def __init__(self, middleware_result_list: List[MXMiddlewareResult] = [],
                 total_scenario_num: List[int] = [0, 0, 0], timeout_scenario_num: List[int] = [0, 0, 0], denied_scenario_num: List[int] = [0, 0, 0], failed_scenario_num: List[int] = [0, 0, 0],
                 avg_latency: List[int] = [0, 0, 0], avg_execute_time: List[int] = [0, 0, 0], avg_schedule_latency: List[int] = [0, 0, 0], avg_energy: List[int] = [0, 0, 0], avg_overhead: List[int] = [0, 0, 0],
                 avg_success_ratio: List[float] = [0, 0, 0],
                 config_path: str = '', policy_path: str = '') -> None:
        self.config_path = config_path
        self.policy_path = policy_path

        self.middleware_result_list = middleware_result_list

        self.total_scenario_num = total_scenario_num
        self.timeout_scenario_num = timeout_scenario_num
        self.denied_scenario_num = denied_scenario_num
        self.failed_scenario_num = failed_scenario_num

        self.avg_latency = avg_latency
        self.avg_execute_time = avg_execute_time
        self.avg_schedule_latency = avg_schedule_latency
        self.avg_energy = avg_energy
        self.avg_overhead = avg_overhead

        self.avg_success_ratio = avg_success_ratio

        self.total_scenario_cycle_num = sum([result.total_scenario_cycle_num for result in self.middleware_result_list])
        self.total_execute_count = sum([result.total_execute_count for result in self.middleware_result_list])
        self.total_execute_time = sum([result.total_execute_time for result in self.middleware_result_list])

    def get_total_scenario_num(self):
        return self.total_scenario_num

    def get_timeout_scenario_num(self):
        return self.timeout_scenario_num

    def get_non_timeout_scenario_num(self):
        return [self.total_scenario_num[0] - self.timeout_scenario_num[0],
                self.total_scenario_num[1] - self.timeout_scenario_num[1],
                self.total_scenario_num[2] - self.timeout_scenario_num[2]]

    def get_denied_scenario_num(self):
        return self.denied_scenario_num

    def get_accepted_scenario_num(self):
        return [self.total_scenario_num[0] - self.timeout_scenario_num[0] - self.denied_scenario_num[0],
                self.total_scenario_num[1] -
                self.timeout_scenario_num[1] - self.denied_scenario_num[1],
                self.total_scenario_num[2] - self.timeout_scenario_num[2] - self.denied_scenario_num[2]]

    def get_failed_scenario_num(self):
        return self.failed_scenario_num

    def get_success_scenario_num(self):
        return [self.total_scenario_num[0] - self.timeout_scenario_num[0] - self.denied_scenario_num[0] - self.failed_scenario_num[0],
                self.total_scenario_num[1] - self.timeout_scenario_num[1] -
                self.denied_scenario_num[1] - self.failed_scenario_num[1],
                self.total_scenario_num[2] - self.timeout_scenario_num[2] - self.denied_scenario_num[2] - self.failed_scenario_num[2]]

    def get_avg_acceptance_ratio(self):
        return [
            self.get_accepted_scenario_num()[0] / self.get_non_timeout_scenario_num()[0] if self.get_non_timeout_scenario_num()[0] != 0 else 0,
            self.get_accepted_scenario_num()[1] / self.get_non_timeout_scenario_num()[1] if self.get_non_timeout_scenario_num()[1] != 0 else 0,
            self.get_accepted_scenario_num()[2] / self.get_non_timeout_scenario_num()[2] if self.get_non_timeout_scenario_num()[2] != 0 else 0]

    def get_avg_success_ratio(self):
        self.avg_success_ratio = [
            self.get_success_scenario_num()[0] / self.get_non_timeout_scenario_num()[0] if self.get_non_timeout_scenario_num()[0] != 0 else 0,
            self.get_success_scenario_num()[1] / self.get_non_timeout_scenario_num()[1] if self.get_non_timeout_scenario_num()[1] != 0 else 0,
            self.get_success_scenario_num()[2] / self.get_non_timeout_scenario_num()[2] if self.get_non_timeout_scenario_num()[2] != 0 else 0]
        return self.avg_success_ratio

    def get_avg_latency(self):
        return self.avg_latency

    def get_avg_energy(self):
        return self.avg_energy

    def get_avg_execute_time(self):
        return self.avg_execute_time

    def get_avg_schedule_time(self):
        return self.avg_schedule_latency

    def get_avg_overhead(self):
        return self.avg_overhead


class MXEvaluator:

    MIDDLEWARE_EVENT = [MXEventType.MIDDLEWARE_RUN,
                        MXEventType.MIDDLEWARE_KILL,
                        MXEventType.THING_REGISTER,
                        MXEventType.THING_UNREGISTER,
                        MXEventType.THING_KILL,
                        MXEventType.SCENARIO_VERIFY,
                        MXEventType.SCENARIO_ADD,
                        MXEventType.SCENARIO_RUN,
                        MXEventType.SCENARIO_STOP,
                        MXEventType.SCENARIO_UPDATE,
                        MXEventType.SCENARIO_DELETE,
                        MXEventType.FUNCTION_EXECUTE,
                        MXEventType.SUPER_FUNCTION_EXECUTE,
                        MXEventType.SUPER_SCHEDULE,
                        MXEventType.SUB_FUNCTION_EXECUTE,
                        MXEventType.SUB_SCHEDULE]
    THING_EVENT = [MXEventType.THING_REGISTER,
                   MXEventType.THING_UNREGISTER,
                   MXEventType.THING_KILL,
                   MXEventType.FUNCTION_EXECUTE,
                   MXEventType.SUPER_FUNCTION_EXECUTE,
                   MXEventType.SUPER_SCHEDULE,
                   MXEventType.SUB_FUNCTION_EXECUTE]
    SERVICE_EVENT = [MXEventType.FUNCTION_EXECUTE,
                     MXEventType.SUB_FUNCTION_EXECUTE,
                     MXEventType.SUPER_FUNCTION_EXECUTE,
                     MXEventType.SUPER_SCHEDULE]
    SCENARIO_EVENT = [MXEventType.FUNCTION_EXECUTE,
                      MXEventType.SUB_FUNCTION_EXECUTE,
                      MXEventType.SUPER_FUNCTION_EXECUTE,
                      MXEventType.SUPER_SCHEDULE,
                      MXEventType.SCENARIO_VERIFY,
                      MXEventType.SCENARIO_ADD,
                      MXEventType.SCENARIO_RUN,
                      MXEventType.SCENARIO_STOP,
                      MXEventType.SCENARIO_UPDATE,
                      MXEventType.SCENARIO_DELETE]

    def __init__(self, simulation_env: MXSimulationEnv, event_log: List[MXEvent]) -> None:
        self.simulation_env = simulation_env
        self.event_log = event_log

    def classify_event_log(self) -> 'MXEvaluator':
        middleware_list = get_whole_middleware_list(self.simulation_env.root_middleware)
        thing_list = get_whole_thing_list(self.simulation_env.root_middleware)
        scenario_list = get_whole_scenario_list(self.simulation_env.root_middleware)
        for component in middleware_list + thing_list + scenario_list:
            component.event_log: List[MXEvent] = []

        for event in self.event_log:
            if event.event_type in MXEvaluator.MIDDLEWARE_EVENT:
                middleware = find_component_by_name(self.simulation_env.root_middleware, event.middleware_component.name)
                middleware.event_log.append(event)
            if event.event_type in MXEvaluator.THING_EVENT:
                thing = find_component_by_name(self.simulation_env.root_middleware, event.thing_component.name)
                thing.event_log.append(event)
            if event.event_type in MXEvaluator.SCENARIO_EVENT:
                scenario = find_component_by_name(self.simulation_env.root_middleware, event.scenario_component.name)
                scenario.event_log.append(event)
        return self

    def evaluate_service(self, target_middleware: MXMiddleware, target_service: MXService) -> Tuple[str, str, int, float, float]:

        def count_service_call(target_service: MXService, event_log: List[MXEvent]):
            call_count = 0
            event_log = [event for event in event_log if event.event_type in MXEvaluator.SERVICE_EVENT]
            for event in event_log:
                if event.service_component.name == target_service.name:
                    call_count += 1
            return call_count

        def cal_service_whole_duration(target_service: MXService, event_log: List[MXEvent]):
            whole_duration = 0
            event_log = [event for event in event_log if event.event_type in MXEvaluator.SERVICE_EVENT]
            for event in event_log:
                if event.service_component.name == target_service.name:
                    whole_duration += event.duration
            return whole_duration

        thing_name = ''
        service_name = ''
        call_count = 0
        energy_consumption = .0
        utilization = .0

        for thing in target_middleware.thing_list:
            for service in thing.service_list:
                if service.name == target_service.name:
                    thing_name = thing.name
                    service_name = service.name
                    call_count = count_service_call(service, target_middleware.event_log)
                    energy_consumption = service.energy * call_count
                    utilization = cal_service_whole_duration(service, target_middleware.event_log) / self.simulation_env.config.running_time

        return thing_name, service_name, call_count, energy_consumption, utilization

    def evaluate_execute_cycle(self, scenario: MXScenario, execute_cycle: List[MXEvent]) -> MXExecuteCycleResult:
        if not scenario.is_super():
            first_service = scenario.service_list[0]
            last_service = scenario.service_list[-1]
            cycle_pattern_check = (execute_cycle[0].service_component.name == first_service.name and execute_cycle[-1].service_component.name == last_service.name)
        else:
            first_service = scenario.service_list[0]
            last_service = scenario.service_list[-1].sub_service_list[-1]

            scenario_service_pattern = sorted([service.name for service in scenario.service_list[0].sub_service_list] + [scenario.service_list[0].name])
            target_service_pattern = sorted([event.service_component.name for event in execute_cycle])

            cycle_pattern_check = (scenario_service_pattern == target_service_pattern)

        if not cycle_pattern_check:
            # 시나리오 안의 서비스가 순차적으로 실행되지 않는 경우. -> 이런 경우 미들웨어의 문제임
            if not execute_cycle[-1].error:
                if all([event.timestamp > self.simulation_env.config.running_time for event in execute_cycle]):
                    return MXExecuteCycleResult(error=MXExecuteCycleErrorType.OVERTIME)
                else:
                    return MXExecuteCycleResult(error=MXExecuteCycleErrorType.RERUN_FAIL)
            elif execute_cycle[-1].error == MXErrorCode.FAIL:
                return MXExecuteCycleResult(error=MXExecuteCycleErrorType.RERUN_FAIL)
            else:
                MXTEST_LOG_DEBUG(f'First or last index of scenario cycle service is not matched with super service\'s subfunction list', MXTestLogLevel.FAIL)
                MXTEST_LOG_DEBUG(f'[{execute_cycle[0].service_component.name} <-> {scenario.service_list[0].name}', MXTestLogLevel.FAIL)
                MXTEST_LOG_DEBUG(f'[{execute_cycle[-1].service_component.name} <-> {scenario.service_list[-1].name}', MXTestLogLevel.FAIL)
                return MXExecuteCycleResult(error=MXExecuteCycleErrorType.SERVICE_ORDER_FAIL)

        if not scenario.is_super():
            cycle_latency = execute_cycle[-1].timestamp - execute_cycle[0].timestamp + execute_cycle[-1].duration
            cycle_energy = sum([event.service_component.energy for event in execute_cycle])

            real_execute_time = True
            if real_execute_time:
                avg_execute_time = avg([event.duration for event in execute_cycle])
            else:
                # FIXME: 매핑이 잘 되는지만 보려고 추가한 코드임. 나중에 삭제해야함
                avg_execute_time = 0
                thing_list: List[MXThing] = get_whole_thing_list(self.simulation_env.root_middleware)
                service_list: List[MXService] = []
                for thing in thing_list:
                    service_list += thing.service_list

                for event in execute_cycle:
                    candidate_service_list = [service for service in service_list if event.service_component.name == service.name]
                    for service in event.thing_component.service_list:
                        if service.name == event.service_component.name:
                            avg_execute_time += service.execute_time
                            candidate_service_info_list = [(service.name, service.execute_time, service.energy) for service in candidate_service_list]
                            candidate_service_execute_time_list = sorted([service[1] for service in candidate_service_info_list])
                            candidate_service_energy_list = sorted([service[2] for service in candidate_service_info_list])

                            execute_time_index = candidate_service_execute_time_list.index(service.execute_time)
                            energy_index = candidate_service_energy_list.index(service.energy)

                            execute_time_opt = execute_time_index / len(candidate_service_execute_time_list) * 100
                            energy_opt = energy_index / len(candidate_service_energy_list) * 100
                            MXTEST_LOG_DEBUG(f'execute_time opt: {execute_time_opt:0.2f}%')
                            MXTEST_LOG_DEBUG(f'energy opt: {energy_opt:0.2f}%')
                            break
                avg_execute_time /= len(execute_cycle)
            overhead = 0
        elif scenario.is_super():
            super_execute_cycle = [event for event in execute_cycle if event.event_type == MXEventType.SUPER_FUNCTION_EXECUTE]
            sub_execute_cycle = [event for event in execute_cycle if event.event_type == MXEventType.SUB_FUNCTION_EXECUTE]
            cycle_latency = super_execute_cycle[-1].timestamp - super_execute_cycle[0].timestamp + super_execute_cycle[-1].duration
            cycle_energy = sum([event.service_component.energy for event in execute_cycle])
            overhead = cycle_latency - sum([sub_execute.duration for sub_execute in sub_execute_cycle])
            avg_execute_time = avg([event.duration for event in super_execute_cycle])

        execute_cycle_result = MXExecuteCycleResult(cycle_latency=cycle_latency,
                                                    cycle_energy=cycle_energy,
                                                    avg_execute_time=avg_execute_time,
                                                    execute_cycle=execute_cycle,
                                                    overhead=overhead,
                                                    error=MXExecuteCycleErrorType.SUCCESS)
        if execute_cycle_result.cycle_latency > scenario.period:
            # 시나리오 상태가 stucked는 아니지만 total service execute time이 period를 넘어서는 경우
            MXTEST_LOG_DEBUG(f'Current execute event cycle of scenario {scenario.name} is PERIOD_FAIL, Scenario will be checked to deadline meet fail', MXTestLogLevel.WARN)
            MXTEST_LOG_DEBUG(f'Scenario: {scenario.name}, Period: {scenario.period}ms, Cycle Latency: {execute_cycle_result.cycle_latency}, ', MXTestLogLevel.WARN)
            MXTEST_LOG_DEBUG(f'Scenario Code: \n{scenario.scenario_code()}', MXTestLogLevel.WARN)
            for event in execute_cycle:
                simulation_start_time = self.get_simulation_start_time()
                if not simulation_start_time:
                    simulation_start_time = 0
                MXTEST_LOG_DEBUG(f'timestamp: {unixtime_to_date(simulation_start_time + event.timestamp)}|{event.timestamp}, '
                                 f'event_type: {event.event_type}, service: {event.service_component.name}, duration: {event.duration}', MXTestLogLevel.WARN)

            # return MXExecuteCycleResult(error=MXExecuteCycleErrorType.PERIOD_FAIL)
            # return execute_cycle_result

        return execute_cycle_result

    def evaluate_scenario(self, scenario: MXScenario) -> MXScenarioResult:

        # 리스트 execute_event_list 안에 다른 리스트 execute_pattern의 패턴을 찾아 리스트로 반환하는 함수
        # 예를 들어 src_list가 [1, 2, 3, 1, 2, 1, 2, 3, 1]이고 execute_pattern가 [1, 2, 3]이면
        # [[1, 2, 3], [1,2], [1, 2, 3], [1]]을 반환한다.

        def find_execute_cycle(execute_event_list: List[MXEvent], service_pattern: List[MXService]) -> List[List[MXEvent]]:
            '''
            리스트 execute_event_list 안에 다른 리스트 execute_pattern의 패턴을 찾아 리스트로 반환하는 함수
            예를 들어 src_list가 [1, 2, 3, 1, 2, 1, 2, 3, 1]이고 execute_pattern가 [1, 2, 3]이면
            [[1, 2, 3], [1, 2, 3]]을 반환한다.
            첫번쨰 사이클과 마지막 사이클은 빼고 반환한다. 
            '''
            result = []

            for i in range(len(execute_event_list)):
                if any([event.error == MXErrorCode.FAIL for event in [event for event in execute_event_list[i:i+len(service_pattern)] if event.event_type in [MXEventType.SUPER_FUNCTION_EXECUTE, MXEventType.FUNCTION_EXECUTE]]]):
                    # 시나리오 cycle중 fail이 있는 경우 무시한다.
                    continue
                sliced_service_list = [event.service_component for event in execute_event_list[i:i+len(service_pattern)]]

                if any([service.is_super for service in service_pattern]):
                    super_service_pattern = [service for service in service_pattern if service.is_super]

                    check_list = []

                    super_service_num = len(super_service_pattern)
                    start_index = 0
                    for j in range(super_service_num):
                        super_service_slot = sliced_service_list[start_index:start_index + len(super_service_pattern[j].sub_service_list) + 1]
                        super_service_name_check = (super_service_slot[0].name == super_service_pattern[j].name)
                        sub_service_name_check = (sorted([service.name for service in super_service_slot[1:]]) == sorted([service.name for service in super_service_pattern[j].sub_service_list]))
                        super_service_slot_check = super_service_name_check and sub_service_name_check
                        check_list.append(super_service_slot_check)
                        start_index += len(super_service_pattern[j].sub_service_list) + 1

                    service_instance_name_check = all(check_list)
                else:
                    service_instance_name_check = ([service.name for service in sliced_service_list] == [service.name for service in service_pattern])

                if service_instance_name_check:
                    result.append(execute_event_list[i:i+len(service_pattern)])

            return result[1:-1]

        def get_service_pattern_from_scenario(scenario: MXScenario):
            service_pattern = []
            for service in scenario.service_list:
                service_pattern.append(service)
                for sub_service in service.sub_service_list:
                    service_pattern.append(sub_service)
            return service_pattern

        scenario_event_log: List[MXEvent] = scenario.event_log
        whole_execute_event_list: List[MXEvent] = [event for event in scenario_event_log
                                                   if event.event_type in [MXEventType.FUNCTION_EXECUTE,
                                                                           MXEventType.SUPER_FUNCTION_EXECUTE,
                                                                           MXEventType.SUB_FUNCTION_EXECUTE]]
        schedule_event_list: List[MXEvent] = [event for event in scenario_event_log if event.event_type == MXEventType.SUPER_SCHEDULE]

        if not scenario.is_super():
            event_type_list = [event.event_type for event in whole_execute_event_list]
            if len(schedule_event_list) > 0:
                raise Exception(f'scenario {scenario.name} is super, but super schedule event is found')
            if MXEventType.SUPER_FUNCTION_EXECUTE in event_type_list or MXEventType.SUB_FUNCTION_EXECUTE in event_type_list:
                raise Exception(f'scenario {scenario.name} is local, but sub_service event is not found')

        # if the state of the scenario remains initialized, it means scenario is timeout.
        if scenario.state == MXScenarioState.UNDEFINED:
            return MXScenarioResult(scenario_component=scenario, error=MXScenarioErrorType.SCHEDULE_TIMEOUT)
        # if the state of the scenario is STUCKED and there is no event related to Execution in the event_log, it means scenario schedule is failed.
        elif scenario.state == MXScenarioState.STUCKED and len([event for event in scenario_event_log if event.event_type in [MXEventType.FUNCTION_EXECUTE,
                                                                                                                              MXEventType.SUPER_FUNCTION_EXECUTE]]) == 0:
            return MXScenarioResult(scenario_component=scenario, error=MXScenarioErrorType.SCHEDULE_FAIL)
        elif scenario.state == MXScenarioState.STUCKED:
            return MXScenarioResult(scenario_component=scenario, error=MXScenarioErrorType.FAIL)
        else:
            pass

        service_pattern = get_service_pattern_from_scenario(scenario=scenario)
        execute_cycle_list = find_execute_cycle(execute_event_list=whole_execute_event_list, service_pattern=service_pattern)

        execute_cycle_result_list: List[MXExecuteCycleResult] = []
        for execute_cycle in execute_cycle_list[1:-1]:
            execute_cycle_result = self.evaluate_execute_cycle(scenario, execute_cycle)
            execute_cycle_result_list.append(execute_cycle_result)

        scenario_result = MXScenarioResult(scenario_component=scenario,
                                           execute_cycle_result_list=execute_cycle_result_list,
                                           schedule_event_list=schedule_event_list,
                                           avg_schedule_latency=avg([schedule_event.duration for schedule_event in schedule_event_list]),
                                           avg_latency=avg([execute_cycle_result.cycle_latency for execute_cycle_result in execute_cycle_result_list]),
                                           avg_energy=avg([execute_cycle_result.cycle_energy for execute_cycle_result in execute_cycle_result_list]),
                                           avg_execute_time=avg([execute_cycle_result.avg_execute_time for execute_cycle_result in execute_cycle_result_list]),
                                           avg_overhead=avg([execute_cycle_result.overhead for execute_cycle_result in execute_cycle_result_list]),
                                           error=MXScenarioErrorType.SUCCESS)
        return scenario_result

    def evaluate_middleware(self, middleware: MXMiddleware) -> MXMiddlewareResult:
        scenario_result_list: List[MXScenarioResult] = []
        for scenario in middleware.scenario_list:
            scenario_result = self.evaluate_scenario(scenario)
            scenario_result_list.append(scenario_result)

        local_scenario_result_list = [scenario_result for scenario_result in scenario_result_list if not scenario_result.scenario_component.is_super()]
        super_scenario_result_list = [scenario_result for scenario_result in scenario_result_list if scenario_result.scenario_component.is_super()]

        total_scenario_num = [len(scenario_result_list),
                              len(local_scenario_result_list),
                              len(super_scenario_result_list)]
        timeout_scenario_num = [len([scenario_result for scenario_result in scenario_result_list if scenario_result.error == MXScenarioErrorType.SCHEDULE_TIMEOUT]),
                                len([scenario_result for scenario_result in local_scenario_result_list if scenario_result.error == MXScenarioErrorType.SCHEDULE_TIMEOUT]),
                                len([scenario_result for scenario_result in super_scenario_result_list if scenario_result.error == MXScenarioErrorType.SCHEDULE_TIMEOUT])]
        denied_scenario_num = [len([scenario_result for scenario_result in scenario_result_list if scenario_result.error == MXScenarioErrorType.SCHEDULE_FAIL]),
                               len([scenario_result for scenario_result in local_scenario_result_list if scenario_result.error == MXScenarioErrorType.SCHEDULE_FAIL]),
                               len([scenario_result for scenario_result in super_scenario_result_list if scenario_result.error == MXScenarioErrorType.SCHEDULE_FAIL])]
        failed_scenario_num = [len([scenario_result for scenario_result in scenario_result_list if scenario_result.error == MXScenarioErrorType.FAIL]),
                               len([scenario_result for scenario_result in local_scenario_result_list if scenario_result.error == MXScenarioErrorType.FAIL]),
                               len([scenario_result for scenario_result in super_scenario_result_list if scenario_result.error == MXScenarioErrorType.FAIL])]
        avg_schedule_latency = [avg([scenario_result.avg_schedule_latency for scenario_result in scenario_result_list]),
                                avg([scenario_result.avg_schedule_latency for scenario_result in local_scenario_result_list]),
                                avg([scenario_result.avg_schedule_latency for scenario_result in super_scenario_result_list])]
        avg_execute_time = [avg([scenario_result.avg_execute_time for scenario_result in scenario_result_list]),
                            avg([scenario_result.avg_execute_time for scenario_result in local_scenario_result_list]),
                            avg([scenario_result.avg_execute_time for scenario_result in super_scenario_result_list])]
        avg_latency = [avg([scenario_result.avg_latency for scenario_result in scenario_result_list]),
                       avg([scenario_result.avg_latency for scenario_result in local_scenario_result_list]),
                       avg([scenario_result.avg_latency for scenario_result in super_scenario_result_list])]
        avg_energy = [avg([scenario_result.avg_energy for scenario_result in scenario_result_list]),
                      avg([scenario_result.avg_energy for scenario_result in local_scenario_result_list]),
                      avg([scenario_result.avg_energy for scenario_result in super_scenario_result_list])]
        avg_overhead = [
            avg([scenario_result.avg_overhead for scenario_result in scenario_result_list]),
            avg([scenario_result.avg_overhead for scenario_result in local_scenario_result_list]),
            avg([scenario_result.avg_overhead for scenario_result in super_scenario_result_list])]

        return MXMiddlewareResult(middleware_component=middleware,
                                  scenario_result_list=scenario_result_list,
                                  local_scenario_result_list=local_scenario_result_list,
                                  super_scenario_result_list=super_scenario_result_list,
                                  total_scenario_num=total_scenario_num,
                                  timeout_scenario_num=timeout_scenario_num,
                                  denied_scenario_num=denied_scenario_num,
                                  failed_scenario_num=failed_scenario_num,
                                  avg_schedule_latency=avg_schedule_latency,
                                  avg_execute_time=avg_execute_time,
                                  avg_latency=avg_latency,
                                  avg_energy=avg_energy,
                                  avg_overhead=avg_overhead)

    def evaluate_simulation(self) -> MXSimulationResult:

        def flatten_middleware_result_list(middleware_result_list: List[MXMiddlewareResult]) -> Tuple[List[MXScenarioResult], List[MXScenarioResult], List[MXScenarioResult]]:
            scenario_result_list = []
            local_scenario_result_list = []
            super_scenario_result_list = []
            for middleware_result in middleware_result_list:
                scenario_result_list += middleware_result.scenario_result_list
                local_scenario_result_list += middleware_result.local_scenario_result_list
                super_scenario_result_list += middleware_result.super_scenario_result_list
            return scenario_result_list, local_scenario_result_list, super_scenario_result_list

        middleware_result_list: List[MXMiddlewareResult] = []
        middleware_list = get_whole_middleware_list(self.simulation_env.root_middleware)
        for middleware in middleware_list:
            middleware_result = self.evaluate_middleware(middleware)
            middleware_result_list.append(middleware_result)

        # flatten middleware result list

        scenario_result_list, local_scenario_result_list, super_scenario_result_list = flatten_middleware_result_list(middleware_result_list)

        total_scenario_num = [len(scenario_result_list),
                              len(local_scenario_result_list),
                              len(super_scenario_result_list)]
        timeout_scenario_num = [len([scenario_result for scenario_result in scenario_result_list if scenario_result.error == MXScenarioErrorType.SCHEDULE_TIMEOUT]),
                                len([scenario_result for scenario_result in local_scenario_result_list if scenario_result.error == MXScenarioErrorType.SCHEDULE_TIMEOUT]),
                                len([scenario_result for scenario_result in super_scenario_result_list if scenario_result.error == MXScenarioErrorType.SCHEDULE_TIMEOUT])]
        denied_scenario_num = [len([scenario_result for scenario_result in scenario_result_list if scenario_result.error == MXScenarioErrorType.SCHEDULE_FAIL]),
                               len([scenario_result for scenario_result in local_scenario_result_list if scenario_result.error == MXScenarioErrorType.SCHEDULE_FAIL]),
                               len([scenario_result for scenario_result in super_scenario_result_list if scenario_result.error == MXScenarioErrorType.SCHEDULE_FAIL])]
        failed_scenario_num = [len([scenario_result for scenario_result in scenario_result_list if scenario_result.error == MXScenarioErrorType.FAIL]),
                               len([scenario_result for scenario_result in local_scenario_result_list if scenario_result.error == MXScenarioErrorType.FAIL]),
                               len([scenario_result for scenario_result in super_scenario_result_list if scenario_result.error == MXScenarioErrorType.FAIL])]
        avg_schedule_latency = [avg([scenario_result.avg_schedule_latency for scenario_result in scenario_result_list]),
                                avg([scenario_result.avg_schedule_latency for scenario_result in local_scenario_result_list]),
                                avg([scenario_result.avg_schedule_latency for scenario_result in super_scenario_result_list])]
        avg_execute_time = [avg([scenario_result.avg_execute_time for scenario_result in scenario_result_list]),
                            avg([scenario_result.avg_execute_time for scenario_result in local_scenario_result_list]),
                            avg([scenario_result.avg_execute_time for scenario_result in super_scenario_result_list])]
        avg_latency = [avg([scenario_result.avg_latency for scenario_result in scenario_result_list]),
                       avg([scenario_result.avg_latency for scenario_result in local_scenario_result_list]),
                       avg([scenario_result.avg_latency for scenario_result in super_scenario_result_list])]
        avg_energy = [avg([scenario_result.avg_energy for scenario_result in scenario_result_list]),
                      avg([scenario_result.avg_energy for scenario_result in local_scenario_result_list]),
                      avg([scenario_result.avg_energy for scenario_result in super_scenario_result_list])]
        avg_overhead = [avg([scenario_result.avg_overhead for scenario_result in scenario_result_list]),
                        avg([scenario_result.avg_overhead for scenario_result in local_scenario_result_list]),
                        avg([scenario_result.avg_overhead for scenario_result in super_scenario_result_list])]

        simulation_result = MXSimulationResult(middleware_result_list=middleware_result_list,
                                               total_scenario_num=total_scenario_num,
                                               timeout_scenario_num=timeout_scenario_num,
                                               denied_scenario_num=denied_scenario_num,
                                               failed_scenario_num=failed_scenario_num,
                                               avg_latency=avg_latency,
                                               avg_execute_time=avg_execute_time,
                                               avg_schedule_latency=avg_schedule_latency,
                                               avg_energy=avg_energy,
                                               avg_overhead=avg_overhead)
        return simulation_result

    # def make_service_utilization_table(self, target_middleware: MXMiddleware):
    #     header = ['thing', 'service(call count)', 'energy consumption', 'utilization']
    #     table = []
    #     for thing in target_middleware.thing_list:
    #         for service in thing.service_list:
    #             if service.name in [row[1].split('(')[0] for row in table]:
    #                 continue
    #             thing_name, service_name, call_count, energy_consumption, utilization = self.evaluate_service(
    #                 target_middleware, service)
    #             if utilization > 0:
    #                 table.append([f'{thing_name}', f"{service_name}({call_count})", energy_consumption, f'{utilization * 100:8.3f}%'])
    #     return table, header

    # def make_scenario_score_table(self, target_middleware: MXMiddleware):
    #     header = ['application', 'avg latency',
    #               'period', 'avg_energy', 'result']
    #     table = []
    #     deadline_meet_cnt = 0
    #     for scenario in target_middleware.scenario_list:
    #         (avg_scenario_latency,
    #          avg_scenario_energy,
    #          avg_scenario_execute_time,
    #          avg_scenario_schedule_latency,
    #          scenario_evaluate_result) = self.evaluate_scenario(scenario)
    #         table.append([scenario.name, f'{avg_scenario_latency:8.3f}s', f'{(scenario.period):8.3f}s', f'{avg_scenario_energy:8.3f}s', scenario_evaluate_result.value])
    #         if scenario_evaluate_result == MXScenarioErrorType.SUCCESS:
    #             deadline_meet_cnt += 1
    #     acceptance_ratio = [scenario.schedule_success for scenario in target_middleware.scenario_list].count(True) / len(target_middleware.scenario_list)
    #     deadline_meet_ratio = deadline_meet_cnt / len(target_middleware.scenario_list)
    #     table.append([f'Acceptance Ratio: {acceptance_ratio * 100:0.2f}%', '', '', '', ''])
    #     table.append([f'Deadline Meet Ratio: {deadline_meet_ratio * 100:0.2f}%', '', '', '', ''])
    #     return table, header

    # def make_whole_timing_list_table(self, target_middleware: MXMiddleware):
    #     header = ['time', 'duration', 'event_type', 'level', 'requester_middleware', 'thing',
    #               'service(delay)', 'application(period)', 'result', 'return_value', 'return_type']
    #     table = []
    #     for event in target_middleware.event_log:
    #         if event.event_type in [MXEventType.FUNCTION_EXECUTE, MXEventType.SUPER_FUNCTION_EXECUTE] and not event.duration:
    #             continue

    #         if event.middleware_component:
    #             middleware, _ = find_component(self.simulation_env.root_middleware, event.middleware_component)
    #         elif event.thing_component:
    #             _, middleware = find_component(self.simulation_env.root_middleware, event.thing_component)
    #         elif event.scenario_component:
    #             _, middleware = find_component(self.simulation_env.root_middleware, event.scenario_component)

    #         middleware: MXMiddleware
    #         requester_middleware = event.requester_middleware_name if event.service_component else None

    #         if not middleware:
    #             raise Exception('middleware is not found')

    #         table.append([event.timestamp,
    #                       event.duration,
    #                       event.event_type.value,
    #                       middleware.level,
    #                       requester_middleware,
    #                       event.thing_component.name if event.thing_component else '',
    #                       event.service_component.name if event.service_component else '',
    #                       event.scenario_component.name if event.scenario_component else '',
    #                       str(event.error) if event.error else '',
    #                       event.return_value,
    #                       str(event.return_type) if event.return_type else ''])
    #     return table, header

    def export_txt(self, simulation_result: MXSimulationResult, simulation_overhead: ProfileResult = None, simulation_name: str = '', file_name: str = '', config_path: str = '') -> None:
        middleware_list: List[MXMiddleware] = get_whole_middleware_list(self.simulation_env.root_middleware)

        scenario_result_header = ['', 'avg accept ratio(%)', 'avg success ratio(%)', 'avg latency', 'avg energy', 'avg execute time', 'avg schedule time', 'avg overhead']
        count_result_header = ['', 'total', 'success', 'fail', 'accept', 'accept fail', 'timeout num']
        policy_result_header = ['total execute count', 'total execute time', 'total application cycle num', 'total avg application latency']
        if simulation_overhead:
            profile_result_header = ['overhead type', 'overhead']

        scenario_result_table = []
        count_result_table = []

        scenario_result_table.append([f'total',
                                      f'{simulation_result.get_avg_acceptance_ratio()[0] * 100:8.3f}',
                                      f'{simulation_result.get_avg_success_ratio()[0] * 100:8.3f}',
                                      f'{simulation_result.get_avg_latency()[0]:8.3f}',
                                      f'{simulation_result.get_avg_energy()[0]:8.3f}',
                                      f'{simulation_result.get_avg_execute_time()[0]:8.3f}',
                                      f'{simulation_result.get_avg_schedule_time()[0]:8.3f}',
                                      f'{simulation_result.get_avg_overhead()[0]:8.3f}'])
        scenario_result_table.append([f'local',
                                      f'{simulation_result.get_avg_acceptance_ratio()[1] * 100:8.3f}',
                                      f'{simulation_result.get_avg_success_ratio()[1] * 100:8.3f}',
                                      f'{simulation_result.get_avg_latency()[1]:8.3f}',
                                      f'{simulation_result.get_avg_energy()[1]:8.3f}',
                                      f'{simulation_result.get_avg_execute_time()[1]:8.3f}',
                                      f'{simulation_result.get_avg_schedule_time()[1]:8.3f}',
                                      f'{simulation_result.get_avg_overhead()[1]:8.3f}'])
        scenario_result_table.append([f'super',
                                      f'{simulation_result.get_avg_acceptance_ratio()[2] * 100:8.3f}',
                                      f'{simulation_result.get_avg_success_ratio()[2] * 100:8.3f}',
                                      f'{simulation_result.get_avg_latency()[2]:8.3f}',
                                      f'{simulation_result.get_avg_energy()[2]:8.3f}',
                                      f'{simulation_result.get_avg_execute_time()[2]:8.3f}',
                                      f'{simulation_result.get_avg_schedule_time()[2]:8.3f}',
                                      f'{simulation_result.get_avg_overhead()[2]:8.3f}'])
        count_result_table.append([f'total',
                                   f'{simulation_result.get_total_scenario_num()[0]}',
                                   f'{simulation_result.get_success_scenario_num()[0]}',
                                   f'{simulation_result.get_failed_scenario_num()[0]}',
                                   f'{simulation_result.get_accepted_scenario_num()[0]}',
                                   f'{simulation_result.get_denied_scenario_num()[0]}',
                                   f'{simulation_result.get_timeout_scenario_num()[0]}'])
        count_result_table.append([f'local',
                                   f'{simulation_result.get_total_scenario_num()[1]}',
                                   f'{simulation_result.get_success_scenario_num()[1]}',
                                   f'{simulation_result.get_failed_scenario_num()[1]}',
                                   f'{simulation_result.get_accepted_scenario_num()[1]}',
                                   f'{simulation_result.get_denied_scenario_num()[1]}',
                                   f'{simulation_result.get_timeout_scenario_num()[1]}'])
        count_result_table.append([f'super',
                                   f'{simulation_result.get_total_scenario_num()[2]}',
                                   f'{simulation_result.get_success_scenario_num()[2]}',
                                   f'{simulation_result.get_failed_scenario_num()[2]}',
                                   f'{simulation_result.get_accepted_scenario_num()[2]}',
                                   f'{simulation_result.get_denied_scenario_num()[2]}',
                                   f'{simulation_result.get_timeout_scenario_num()[2]}'])
        policy_result_table = [[simulation_result.total_execute_count,
                                simulation_result.total_execute_time,
                                simulation_result.total_scenario_cycle_num,
                                f'{(simulation_result.total_execute_time / simulation_result.total_scenario_cycle_num if simulation_result.total_scenario_cycle_num != 0 else 0):0.2f}']]

        if simulation_overhead:
            profile_result_table = []
            profile_result_table.append(['total', f'{simulation_overhead.avg_total_overhead().total_seconds():8.3f}'])
            profile_result_table.append(['total inner', f'{simulation_overhead.avg_total_inner_overhead().total_seconds():8.3f}'])
            profile_result_table.append(['total comm', f'{simulation_overhead.avg_total_comm_overhead().total_seconds():8.3f}'])
            profile_result_table.append(['total middleware_inner', f'{simulation_overhead.avg_total_middleware_inner_overhead().total_seconds():8.3f}'])
            profile_result_table.append(['total super_thing_inner', f'{simulation_overhead.avg_total_super_thing_inner_overhead().total_seconds():8.3f}'])
            profile_result_table.append(['total middleware_middleware_comm', f'{simulation_overhead.avg_total_middleware__middleware_comm_overhead().total_seconds():8.3f}'])
            profile_result_table.append(['total super_thing_middleware_comm', f'{simulation_overhead.avg_total_super_thing__middleware_comm_overhead().total_seconds():8.3f}'])
            profile_result_table.append(['total target_thing_middleware_comm', f'{simulation_overhead.avg_total_target_thing__middleware_comm_overhead().total_seconds():8.3f}'])

        # print simulation score
        thing_list: List[MXThing] = get_whole_thing_list(self.simulation_env.root_middleware)
        thing_list = [thing for thing in thing_list if thing.is_super == False]
        main_title = (f'==== Simulation [{simulation_name}] result ===='
                      f'* is_parallel: {thing_list[0].is_parallel}'
                      f'* datetime: {get_current_time(mode=TimeFormat.DATETIME1)}')
        scenario_result_title = f'==== Scenario Result ===='
        count_result_title = f'==== Count Result ===='
        policy_result_title = f'==== Policy Result ===='
        if simulation_overhead:
            profile_result_title = f'==== Profile Overhead Result ===='

        print(main_title)
        print(scenario_result_title)
        scenario_result_table_str = print_table(scenario_result_table, scenario_result_header)
        print(count_result_title)
        count_result_table_str = print_table(count_result_table, count_result_header)
        print(policy_result_title)
        policy_result_table_str = print_table(policy_result_table, policy_result_header)
        if simulation_overhead:
            print(profile_result_title)
            profile_result_table_str = print_table(profile_result_table, profile_result_header)

        if not file_name:
            file_name = f'result_{os.path.basename(os.path.dirname(config_path))}'
        else:
            pass

        os.makedirs(f'{get_project_root()}/sim_result', exist_ok=True)
        with open(f'{get_project_root()}/sim_result/{file_name}.txt', 'a+') as f:
            f.write(main_title + '\n')
            f.write(scenario_result_title + '\n')
            f.write(scenario_result_table_str)
            f.write('\n')
            f.write(count_result_title + '\n')
            f.write(count_result_table_str)
            f.write('\n')
            f.write(policy_result_title + '\n')
            f.write(policy_result_table_str)
            f.write('\n')
            if simulation_overhead:
                f.write(profile_result_title + '\n')
                f.write(profile_result_table_str)
                f.write('\n')

    def export_csv(self, simulation_result: MXSimulationResult,  simulation_overhead: ProfileResult = None, simulation_name: str = '', file_name: str = '', config_path: str = '') -> None:
        if not file_name:
            file_name = f'result_{os.path.basename(os.path.dirname(config_path))}'
        else:
            pass

        os.makedirs(f'{get_project_root()}/sim_result', exist_ok=True)
        with open(f'{get_project_root()}/sim_result/{file_name}.csv', 'a+') as f:
            wr = csv.writer(f)
            header = (['simulation name'] +
                      ['avg accept ratio(%) (all)', 'avg success ratio(%) (all)', 'avg latency (all)', 'avg energy (all)', 'avg execute time (all)', 'avg schedule time (all)',  'avg overhead (all)', 'total (all)', 'success (all)', 'fail (all)', 'accept (all)', 'accept fail (all)', 'timeout num (all)'] +
                      ['avg accept ratio(%) (local)', 'avg success ratio(%) (local)', 'avg latency (local)', 'avg energy (local)', 'avg execute time (local)', 'avg schedule time (local)',  'avg overhead (local)', 'total (local)', 'success (local)', 'fail (local)', 'accept (local)', 'accept fail (local)', 'timeout num (local)'] +
                      ['avg accept ratio(%) (super)', 'avg success ratio(%) (super)', 'avg latency (super)', 'avg energy (super)', 'avg execute time (super)', 'avg schedule time (super)',  'avg overhead (super)', 'total (super)', 'success (super)', 'fail (super)', 'accept (super)', 'accept fail (super)', 'timeout num (super)'] +
                      ['total execute count', 'total execute time', 'total application cycle num', 'total avg application latency'])
            if simulation_overhead:
                header += ['avg overhead', 'inner overhead', 'comm overhead', 'middleware inner', 'super thing inner',
                           'middleware - middleware comm overhead', 'super thing - middleware comm overhead', 'target thing - middleware comm overhead']
            wr.writerow(header)
            data = ([f'{simulation_name}'] +
                    [f'{simulation_result.get_avg_acceptance_ratio()[0] * 100:8.3f}',
                     f'{simulation_result.get_avg_success_ratio()[0] * 100:8.3f}',
                     f'{simulation_result.get_avg_latency()[0]:8.3f}',
                     f'{simulation_result.get_avg_energy()[0]:8.3f}',
                     f'{simulation_result.get_avg_execute_time()[0]:8.3f}',
                     f'{simulation_result.get_avg_schedule_time()[0]:8.3f}',
                     f'{simulation_result.get_avg_overhead()[0]:8.3f}'] +
                    [f'{simulation_result.get_total_scenario_num()[0]}',
                     f'{simulation_result.get_success_scenario_num()[0]}',
                     f'{simulation_result.get_failed_scenario_num()[0]}',
                     f'{simulation_result.get_accepted_scenario_num()[0]}',
                     f'{simulation_result.get_denied_scenario_num()[0]}',
                     f'{simulation_result.get_timeout_scenario_num()[0]}'] +
                    [f'{simulation_result.get_avg_acceptance_ratio()[1] * 100:8.3f}',
                     f'{simulation_result.get_avg_success_ratio()[1] * 100:8.3f}',
                     f'{simulation_result.get_avg_latency()[1]:8.3f}',
                     f'{simulation_result.get_avg_energy()[1]:8.3f}',
                     f'{simulation_result.get_avg_execute_time()[1]:8.3f}',
                     f'{simulation_result.get_avg_schedule_time()[1]:8.3f}',
                     f'{simulation_result.get_avg_overhead()[1]:8.3f}'] +
                    [f'{simulation_result.get_total_scenario_num()[1]}',
                     f'{simulation_result.get_success_scenario_num()[1]}',
                     f'{simulation_result.get_failed_scenario_num()[1]}',
                     f'{simulation_result.get_accepted_scenario_num()[1]}',
                     f'{simulation_result.get_denied_scenario_num()[1]}',
                     f'{simulation_result.get_timeout_scenario_num()[1]}'] +
                    [f'{simulation_result.get_avg_acceptance_ratio()[2] * 100:8.3f}',
                     f'{simulation_result.get_avg_success_ratio()[2] * 100:8.3f}',
                     f'{simulation_result.get_avg_latency()[2]:8.3f}',
                     f'{simulation_result.get_avg_energy()[2]:8.3f}',
                     f'{simulation_result.get_avg_execute_time()[2]:8.3f}',
                     f'{simulation_result.get_avg_schedule_time()[2]:8.3f}',
                     f'{simulation_result.get_avg_overhead()[2]:8.3f}'] +
                    [f'{simulation_result.get_total_scenario_num()[2]}',
                     f'{simulation_result.get_success_scenario_num()[2]}',
                     f'{simulation_result.get_failed_scenario_num()[2]}',
                     f'{simulation_result.get_accepted_scenario_num()[2]}',
                     f'{simulation_result.get_denied_scenario_num()[2]}',
                     f'{simulation_result.get_timeout_scenario_num()[2]}'] +
                    [f'{simulation_result.total_execute_count}',
                     f'{simulation_result.total_execute_time}',
                     f'{simulation_result.total_scenario_cycle_num}',
                     f'{(simulation_result.total_execute_time / simulation_result.total_scenario_cycle_num if simulation_result.total_scenario_cycle_num != 0 else 0):0.2f}']
                    )
            if simulation_overhead:
                data += [f'{simulation_overhead.avg_total_overhead().total_seconds():8.3f}',
                         f'{simulation_overhead.avg_total_inner_overhead().total_seconds():8.3f}',
                         f'{simulation_overhead.avg_total_comm_overhead().total_seconds():8.3f}',
                         f'{simulation_overhead.avg_total_middleware_inner_overhead().total_seconds():8.3f}',
                         f'{simulation_overhead.avg_total_super_thing_inner_overhead().total_seconds():8.3f}',
                         f'{simulation_overhead.avg_total_middleware__middleware_comm_overhead().total_seconds():8.3f}',
                         f'{simulation_overhead.avg_total_super_thing__middleware_comm_overhead().total_seconds():8.3f}',
                         f'{simulation_overhead.avg_total_target_thing__middleware_comm_overhead().total_seconds():8.3f}']
            wr.writerow(data)

    # =========================
    #         _    _  _
    #        | |  (_)| |
    #  _   _ | |_  _ | | ___
    # | | | || __|| || |/ __|
    # | |_| || |_ | || |\__ \
    #  \__,_| \__||_||_||___/
    # =========================

    def get_simulation_start_time(self) -> float:
        for event in self.event_log:
            if event.event_type == MXEventType.START:
                return event.timestamp
