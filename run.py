from simulation_framework.simulation_framework import *
import argparse


START_LOGGER()


def arg_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config_path_list', '-e', type=str, nargs='+',
                        required=False, help='simulation config path list')
    parser.add_argument('--policy_file_path_list', '-p', type=str, nargs='+',
                        required=False, help='policy_file_path_list')
    parser.add_argument('--simulation_file_path', '-s', type=str, default='',
                        required=False, help='simulation data file path')
    parser.add_argument('--is_parallel', '-pl', action='store_true',
                        required=False, help='is_parallel')
    parser.add_argument('--filename', '-o',
                        required=False, help='output result filename')
    parser.add_argument('--mqtt_debug', '-mqtt_d', action='store_true',
                        required=False, help='mqtt debug mode')
    parser.add_argument('--middleware_debug', '-mid_d', action='store_true',
                        required=False, help='middleware debug mode')
    parser.add_argument('--download_logs', '-dl', action='store_true',
                        required=False, help='download simulation log files')
    parser.add_argument('--profile', '-pf', action='store_true',
                        required=False, help='profile detailed overhead')
    parser.add_argument('--only_profile', action='store_true',
                        required=False, help='profile detailed overhead')
    parser.add_argument('--profile_type', '-pt', type=str, default='Execute',
                        required=False, help=('Profile type\n'
                                              'You can choose from the following:\n'
                                              '  Schedule: Profile the scheduling part of simulation\n'
                                              '  Execute: Profile the execution part of simulation\n'))
    parser.add_argument('--root_log_path', '-logs', type=str,
                        help=('Path containing simulation logs\n'
                              'If there are multiple simulation logs in a folder, profile them all.'))
    parser.add_argument('--log_path', '-log', type=str,
                        help=('Specific simulation log path'))
    args, unknown = parser.parse_known_args()

    if not args.only_profile:
        if not args.config_path_list and not args.simulation_file_path:
            parser.error('config_path_list 또는 simulation_file_path 중 하나는 제공해야 합니다.')
        if not args.policy_file_path_list:
            parser.error('policy_file_path_list는 제공해야 합니다.')
    else:
        if not args.log_path and not args.root_log_path:
            parser.error('log_path 또는 root_log_path 중 하나는 제공해야 합니다.')

    return args


def simulation_main(args: argparse.Namespace):
    simulation_framework = SoPSimulationFramework(config_path_list=args.config_path_list,
                                                  simulation_file_path=args.simulation_file_path,
                                                  mqtt_debug=args.mqtt_debug,
                                                  middleware_debug=args.middleware_debug)

    simulation_framework.start(policy_file_path_list=args.policy_file_path_list,
                               args=args)


def profile_main(args: argparse.Namespace):
    profiler = Profiler()
    if args.log_path:
        profiler.load(log_root_path=args.log_path)
        profile_result = profiler.profile(args.profile_type, export=True)
        print_result(simulation_overhead=profile_result)
        customized_print(profile_result=profile_result)
    elif args.root_log_path:
        log_path_list = os.listdir(args.root_log_path)
        for log_path in log_path_list:
            profiler.load(log_root_path=log_path)
            profile_result = profiler.profile(args.profile_type, export=True)
            print_result(simulation_overhead=profile_result)
            customized_print(profile_result=profile_result)


# profiler의 메소드로 만들어야 할 것 같음
def print_result(simulation_overhead: ProfileResult):
    avg_total_overhead = simulation_overhead.avg_total_overhead()
    avg_inner_overhead = simulation_overhead.avg_total_inner_overhead()
    avg_comm_overhead = simulation_overhead.avg_total_comm_overhead()
    avg_overhead_middleware_inner_sum = simulation_overhead.avg_total_middleware_inner_overhead()
    avg_overhead_super_thing_inner_sum = simulation_overhead.avg_total_super_thing_inner_overhead()
    avg_overhead_target_thing_inner_sum = simulation_overhead.avg_total_target_thing_inner_overhead()
    avg_overhead_middleware__middleware_comm_sum = simulation_overhead.avg_total_middleware__middleware_comm_overhead()
    avg_overhead_super_thing__middleware_comm_sum = simulation_overhead.avg_total_super_thing__middleware_comm_overhead()
    avg_overhead_target_thing__middleware_comm_sum = simulation_overhead.avg_total_target_thing__middleware_comm_overhead()

    SOPTEST_LOG_DEBUG(
        f'\n\
==== Request Avg Result =========\n\
total overhead:                                             {avg_total_overhead.total_seconds()*1e3:8.3f} ms\n\
total inner overhead:                                       {avg_inner_overhead.total_seconds()*1e3:8.3f} ms\n\
total comm overhead:                                        {avg_comm_overhead.total_seconds()*1e3:8.3f} ms\n\
total MIDDLEWARE_INNER overhead:                            {avg_overhead_middleware_inner_sum.total_seconds()*1e3:8.3f} ms\n\
total SUPER_THING_INNER overhead:                           {avg_overhead_super_thing_inner_sum.total_seconds()*1e3:8.3f} ms\n\
total TARGET_THING service execution:                       {avg_overhead_target_thing_inner_sum.total_seconds()*1e3:8.3f} ms\n\
total MIDDLEWARE__MIDDLEWARE_COMM overhead:                 {avg_overhead_middleware__middleware_comm_sum.total_seconds()*1e3:8.3f} ms\n\
total SUPER_THING__MIDDLEWARE_COMM overhead:                {avg_overhead_super_thing__middleware_comm_sum.total_seconds()*1e3:8.3f} ms\n\
total TARGET_THING__MIDDLEWARE_COMM overhead:               {avg_overhead_target_thing__middleware_comm_sum.total_seconds()*1e3:8.3f} ms')


# 더 세부적으로 오버헤드를 출력할 수 있다 만 예시로 보여준다.
# Profiler를 인자로 넘겨주는 것으로 변경
def customized_print(profile_result: ProfileResult):
    # [ST(3) <- MW(3)    MW(2)    MW(1)         ]
    # [ST(↓)    MW(3)    MW(2)    MW(1)         ]
    #############################################
    # [ST(3) -> MW(3)    MW(2)    MW(1)    LT(1)]
    # [ST(3)    MW(↓)    MW(2)    MW(1)    LT(1)]
    # [ST(3)    MW(3) -> MW(2)    MW(1)    LT(1)]
    # [ST(3)    MW(3)    MW(↓)    MW(1)    LT(1)]
    # [ST(3)    MW(3)    MW(2) -> MW(1)    LT(1)]
    # [ST(3)    MW(3)    MW(2)    MW(↓)    LT(1)]
    # [ST(3)    MW(3)    MW(2)    MW(1) -> LT(1)]
    # [ST(3)    MW(3)    MW(2)    MW(1)    LT(↓)]
    # [ST(3)    MW(3)    MW(2)    MW(1) <- LT(1)]
    # [ST(3)    MW(3)    MW(2)    MW(↓)    LT(1)]
    # [ST(3)    MW(3)    MW(2) <- MW(1)    LT(1)]
    # [ST(3)    MW(3)    MW(↓)    MW(1)    LT(1)]
    # [ST(3)    MW(3) <- MW(2)    MW(1)    LT(1)]
    # [ST(3)    MW(↓)    MW(2)    MW(1)    LT(1)]
    # [ST(3) <- MW(3)    MW(2)    MW(1)    LT(1)]
    # [ST(↓)    MW(3)    MW(2)    MW(1)    LT(1)]
    #############################################
    # [ST(3) -> MW(3)    MW(2)    LT(2)         ]

    # [ST(3) <- MW(3)    MW(2)    MW(1)         ]
    avg_MS_EXECUTE_comm_overhead = profile_result.avg_overhead(dict(type=OverheadType.SUPER_THING__MIDDLEWARE_COMM,
                                                                    element_type_from=SoPElementType.MIDDLEWARE,
                                                                    protocol_from=SoPProtocolType.Super.MS_EXECUTE,
                                                                    level_from=3,
                                                                    element_type_to=SoPElementType.THING,
                                                                    protocol_to=SoPProtocolType.Super.MS_EXECUTE,
                                                                    level_to=3))
    # [ST(↓)    MW(3)    MW(2)    MW(1)         ]
    avg_MS_EXECUTE_inner_overhead = profile_result.avg_overhead(dict(type=OverheadType.SUPER_THING_INNER,
                                                                     element_type_from=SoPElementType.THING,
                                                                     protocol_from=SoPProtocolType.Super.MS_EXECUTE,
                                                                     level_from=3,
                                                                     element_type_to=SoPElementType.THING,
                                                                     protocol_to=SoPProtocolType.Super.SM_EXECUTE,
                                                                     level_to=3))
    # [ST(3) -> MW(3)    MW(2)    MW(1)    LT(1)]
    avg_SM_EXECUTE_comm_overhead_3_3 = profile_result.avg_overhead(dict(type=OverheadType.SUPER_THING__MIDDLEWARE_COMM,
                                                                        element_type_from=SoPElementType.THING,
                                                                        protocol_from=SoPProtocolType.Super.SM_EXECUTE,
                                                                        level_from=3,
                                                                        element_type_to=SoPElementType.MIDDLEWARE,
                                                                        protocol_to=SoPProtocolType.Super.SM_EXECUTE,
                                                                        level_to=3))
    # [ST(3)    MW(↓)    MW(2)    MW(1)    LT(1)]
    avg_PC_EXECUTE_inner_overhead_3 = profile_result.avg_overhead(dict(type=OverheadType.MIDDLEWARE_INNER,
                                                                       element_type_from=SoPElementType.MIDDLEWARE,
                                                                       protocol_from=SoPProtocolType.Super.SM_EXECUTE,
                                                                       level_from=3,
                                                                       element_type_to=SoPElementType.MIDDLEWARE,
                                                                       protocol_to=SoPProtocolType.Super.PC_EXECUTE,
                                                                       level_to=3))
    # [ST(3)    MW(3) -> MW(2)    MW(1)    LT(1)]
    avg_PC_EXECUTE_comm_overhead_3_2 = profile_result.avg_overhead(dict(type=OverheadType.MIDDLEWARE__MIDDLEWARE_COMM,
                                                                        element_type_from=SoPElementType.MIDDLEWARE,
                                                                        protocol_from=SoPProtocolType.Super.PC_EXECUTE,
                                                                        level_from=3,
                                                                        element_type_to=SoPElementType.MIDDLEWARE,
                                                                        protocol_to=SoPProtocolType.Super.PC_EXECUTE,
                                                                        level_to=2))
    # [ST(3)    MW(3)    MW(↓)    MW(1)    LT(1)]
    avg_PC_EXECUTE_inner_overhead_2 = profile_result.avg_overhead(dict(type=OverheadType.MIDDLEWARE_INNER,
                                                                       element_type_from=SoPElementType.MIDDLEWARE,
                                                                       protocol_from=SoPProtocolType.Super.PC_EXECUTE,
                                                                       level_from=2,
                                                                       element_type_to=SoPElementType.MIDDLEWARE,
                                                                       protocol_to=SoPProtocolType.Super.PC_EXECUTE,
                                                                       level_to=2))
    # [ST(3)    MW(3)    MW(2) -> MW(1)    LT(1)]
    avg_PC_EXECUTE_comm_overhead_2_1 = profile_result.avg_overhead(dict(type=OverheadType.MIDDLEWARE__MIDDLEWARE_COMM,
                                                                        element_type_from=SoPElementType.MIDDLEWARE,
                                                                        protocol_from=SoPProtocolType.Super.PC_EXECUTE,
                                                                        level_from=2,
                                                                        element_type_to=SoPElementType.MIDDLEWARE,
                                                                        protocol_to=SoPProtocolType.Super.PC_EXECUTE,
                                                                        level_to=1))
    # [ST(3)    MW(3)    MW(2)    MW(↓)    LT(1)]
    avg_PC_EXECUTE_inner_overhead_1 = profile_result.avg_overhead(dict(type=OverheadType.MIDDLEWARE_INNER,
                                                                       element_type_from=SoPElementType.MIDDLEWARE,
                                                                       protocol_from=SoPProtocolType.Super.PC_EXECUTE,
                                                                       level_from=1,
                                                                       element_type_to=SoPElementType.MIDDLEWARE,
                                                                       protocol_to=SoPProtocolType.Base.MT_EXECUTE,
                                                                       level_to=1))
    # [ST(3)    MW(3)    MW(2)    MW(1) -> LT(1)]
    avg_MT_EXECUTE_comm_overhead_1_1 = profile_result.avg_overhead(dict(type=OverheadType.TARGET_THING__MIDDLEWARE_COMM,
                                                                        element_type_from=SoPElementType.MIDDLEWARE,
                                                                        protocol_from=SoPProtocolType.Base.MT_EXECUTE,
                                                                        level_from=1,
                                                                        element_type_to=SoPElementType.THING,
                                                                        protocol_to=SoPProtocolType.Base.MT_EXECUTE,
                                                                        level_to=1))
    # [ST(3)    MW(3)    MW(2)    MW(1)    LT(↓)]
    avg_MT_EXECUTE_inner_overhead_1 = profile_result.avg_overhead(dict(type=OverheadType.TARGET_THING_INNER,
                                                                       element_type_from=SoPElementType.THING,
                                                                       protocol_from=SoPProtocolType.Base.MT_EXECUTE,
                                                                       level_from=1,
                                                                       element_type_to=SoPElementType.THING,
                                                                       protocol_to=SoPProtocolType.Base.TM_RESULT_EXECUTE,
                                                                       level_to=1))
    # [ST(3)    MW(3)    MW(2)    MW(1) <- LT(1)]
    avg_MT_RESULT_EXECUTE_comm_overhead_1 = profile_result.avg_overhead(dict(type=OverheadType.TARGET_THING__MIDDLEWARE_COMM,
                                                                             element_type_from=SoPElementType.THING,
                                                                             protocol_from=SoPProtocolType.Base.TM_RESULT_EXECUTE,
                                                                             level_from=1,
                                                                             element_type_to=SoPElementType.MIDDLEWARE,
                                                                             protocol_to=SoPProtocolType.Base.TM_RESULT_EXECUTE,
                                                                             level_to=1))
    # [ST(3)    MW(3)    MW(2)    MW(↓)    LT(1)]
    avg_CP_RESULT_EXECUTE_inner_overhead_1 = profile_result.avg_overhead(dict(type=OverheadType.MIDDLEWARE_INNER,
                                                                              element_type_from=SoPElementType.MIDDLEWARE,
                                                                              protocol_from=SoPProtocolType.Base.TM_RESULT_EXECUTE,
                                                                              level_from=1,
                                                                              element_type_to=SoPElementType.MIDDLEWARE,
                                                                              protocol_to=SoPProtocolType.Super.CP_RESULT_EXECUTE,
                                                                              level_to=1))
    # [ST(3)    MW(3)    MW(2) <- MW(1)    LT(1)]
    avg_CP_RESULT_EXECUTE_comm_overhead_1_2 = profile_result.avg_overhead(dict(type=OverheadType.MIDDLEWARE__MIDDLEWARE_COMM,
                                                                               element_type_from=SoPElementType.MIDDLEWARE,
                                                                               protocol_from=SoPProtocolType.Super.CP_RESULT_EXECUTE,
                                                                               level_from=1,
                                                                               element_type_to=SoPElementType.MIDDLEWARE,
                                                                               protocol_to=SoPProtocolType.Super.CP_RESULT_EXECUTE,
                                                                               level_to=2))
    # [ST(3)    MW(3)    MW(↓)    MW(1)    LT(1)]
    avg_CP_RESULT_EXECUTE_inner_overhead_2 = profile_result.avg_overhead(dict(type=OverheadType.MIDDLEWARE_INNER,
                                                                              element_type_from=SoPElementType.MIDDLEWARE,
                                                                              protocol_from=SoPProtocolType.Super.CP_RESULT_EXECUTE,
                                                                              level_from=2,
                                                                              element_type_to=SoPElementType.MIDDLEWARE,
                                                                              protocol_to=SoPProtocolType.Super.CP_RESULT_EXECUTE,
                                                                              level_to=2))
    # [ST(3)    MW(3) <- MW(2)    MW(1)    LT(1)]
    avg_CP_RESULT_EXECUTE_comm_overhead_2_3 = profile_result.avg_overhead(dict(type=OverheadType.MIDDLEWARE__MIDDLEWARE_COMM,
                                                                               element_type_from=SoPElementType.MIDDLEWARE,
                                                                               protocol_from=SoPProtocolType.Super.CP_RESULT_EXECUTE,
                                                                               level_from=2,
                                                                               element_type_to=SoPElementType.MIDDLEWARE,
                                                                               protocol_to=SoPProtocolType.Super.CP_RESULT_EXECUTE,
                                                                               level_to=3))
    # [ST(3)    MW(↓)    MW(2)    MW(1)    LT(1)]
    avg_CP_RESULT_EXECUTE_inner_overhead_3 = profile_result.avg_overhead(dict(type=OverheadType.MIDDLEWARE_INNER,
                                                                              element_type_from=SoPElementType.MIDDLEWARE,
                                                                              protocol_from=SoPProtocolType.Super.CP_RESULT_EXECUTE,
                                                                              level_from=3,
                                                                              element_type_to=SoPElementType.MIDDLEWARE,
                                                                              protocol_to=SoPProtocolType.Super.MS_RESULT_EXECUTE,
                                                                              level_to=3))
    # [ST(3) <- MW(3)    MW(2)    MW(1)    LT(1)]
    avg_MS_RESULT_EXECUTE_comm_overhead_3_3 = profile_result.avg_overhead(dict(type=OverheadType.SUPER_THING__MIDDLEWARE_COMM,
                                                                               element_type_from=SoPElementType.MIDDLEWARE,
                                                                               protocol_from=SoPProtocolType.Super.MS_RESULT_EXECUTE,
                                                                               level_from=3,
                                                                               element_type_to=SoPElementType.THING,
                                                                               protocol_to=SoPProtocolType.Super.MS_RESULT_EXECUTE,
                                                                               level_to=3))
    # [ST(↓)    MW(3)    MW(2)    MW(1)    LT(1)]
    avg_MS_RESULT_EXECUTE_inner_overhead_3 = profile_result.avg_overhead(dict(type=OverheadType.SUPER_THING_INNER,
                                                                              element_type_from=SoPElementType.THING,
                                                                              protocol_from=SoPProtocolType.Super.MS_RESULT_EXECUTE,
                                                                              level_from=3,
                                                                              element_type_to=SoPElementType.THING,
                                                                              protocol_to=SoPProtocolType.Super.SM_EXECUTE,
                                                                              level_to=3))
    # [ST(↓)    MW(3)    MW(2)    MW(1)    LT(1)]
    avg_MS_RESULT_EXECUTE_inner_overhead_final = profile_result.avg_overhead(dict(type=OverheadType.SUPER_THING_INNER,
                                                                                  element_type_from=SoPElementType.THING,
                                                                                  protocol_from=SoPProtocolType.Super.MS_RESULT_EXECUTE,
                                                                                  level_from=3,
                                                                                  element_type_to=SoPElementType.THING,
                                                                                  protocol_to=SoPProtocolType.Super.SM_RESULT_EXECUTE,
                                                                                  level_to=3))
    # [ST(3) -> MW(3)    MW(2)    LT(2)         ]
    avg_SM_RESULT_EXECUTE_comm_overhead = profile_result.avg_overhead(dict(type=OverheadType.SUPER_THING__MIDDLEWARE_COMM,
                                                                           element_type_from=SoPElementType.THING,
                                                                           protocol_from=SoPProtocolType.Super.SM_RESULT_EXECUTE,
                                                                           level_from=3,
                                                                           element_type_to=SoPElementType.MIDDLEWARE,
                                                                           protocol_to=SoPProtocolType.Super.SM_RESULT_EXECUTE,
                                                                           level_to=3))
    SOPTEST_LOG_DEBUG(
        f'\n\
==== Request Detail Result =========\n\
total avg_MS_EXECUTE_comm_overhead overhead:                {avg_MS_EXECUTE_comm_overhead.total_seconds()*1e3:8.3f} ms\n\
total avg_MS_EXECUTE_inner_overhead overhead:               {avg_MS_EXECUTE_inner_overhead.total_seconds()*1e3:8.3f} ms\n\
total avg_SM_EXECUTE_comm_overhead_3_3 overhead:            {avg_SM_EXECUTE_comm_overhead_3_3.total_seconds()*1e3:8.3f} ms\n\
total avg_PC_EXECUTE_inner_overhead_3 overhead:             {avg_PC_EXECUTE_inner_overhead_3.total_seconds()*1e3:8.3f} ms\n\
total avg_PC_EXECUTE_comm_overhead_3_2 overhead:            {avg_PC_EXECUTE_comm_overhead_3_2.total_seconds()*1e3:8.3f} ms\n\
total avg_PC_EXECUTE_inner_overhead_2 overhead:             {avg_PC_EXECUTE_inner_overhead_2.total_seconds()*1e3:8.3f} ms\n\
total avg_PC_EXECUTE_comm_overhead_2_1 overhead:            {avg_PC_EXECUTE_comm_overhead_2_1.total_seconds()*1e3:8.3f} ms\n\
total avg_PC_EXECUTE_inner_overhead_1 overhead:             {avg_PC_EXECUTE_inner_overhead_1.total_seconds()*1e3:8.3f} ms\n\
total avg_MT_EXECUTE_comm_overhead_1_1 overhead:            {avg_MT_EXECUTE_comm_overhead_1_1.total_seconds()*1e3:8.3f} ms\n\
total avg_MT_EXECUTE_inner_overhead_1 overhead:             {avg_MT_EXECUTE_inner_overhead_1.total_seconds()*1e3:8.3f} ms\n\
total avg_MT_RESULT_EXECUTE_comm_overhead_1 overhead:       {avg_MT_RESULT_EXECUTE_comm_overhead_1.total_seconds()*1e3:8.3f} ms\n\
total avg_CP_RESULT_EXECUTE_inner_overhead_1 overhead:      {avg_CP_RESULT_EXECUTE_inner_overhead_1.total_seconds()*1e3:8.3f} ms\n\
total avg_CP_RESULT_EXECUTE_comm_overhead_1_2 overhead:     {avg_CP_RESULT_EXECUTE_comm_overhead_1_2.total_seconds()*1e3:8.3f} ms\n\
total avg_CP_RESULT_EXECUTE_inner_overhead_2 overhead:      {avg_CP_RESULT_EXECUTE_inner_overhead_2.total_seconds()*1e3:8.3f} ms\n\
total avg_CP_RESULT_EXECUTE_comm_overhead_2_3 overhead:     {avg_CP_RESULT_EXECUTE_comm_overhead_2_3.total_seconds()*1e3:8.3f} ms\n\
total avg_CP_RESULT_EXECUTE_inner_overhead_3 overhead:      {avg_CP_RESULT_EXECUTE_inner_overhead_3.total_seconds()*1e3:8.3f} ms\n\
total avg_MS_RESULT_EXECUTE_comm_overhead_3_3 overhead:     {avg_MS_RESULT_EXECUTE_comm_overhead_3_3.total_seconds()*1e3:8.3f} ms\n\
total avg_MS_RESULT_EXECUTE_inner_overhead_3 overhead:      {avg_MS_RESULT_EXECUTE_inner_overhead_3.total_seconds()*1e3:8.3f} ms\n\
total avg_MS_RESULT_EXECUTE_inner_overhead_final overhead:  {avg_MS_RESULT_EXECUTE_inner_overhead_final.total_seconds()*1e3:8.3f} ms\n\
total avg_SM_RESULT_EXECUTE_comm_overhead overhead:         {avg_SM_RESULT_EXECUTE_comm_overhead.total_seconds()*1e3:8.3f} ms\n\
')


if __name__ == '__main__':
    args = arg_parse()

    if args.profile_type.lower() == 'schedule':
        args.profile_type = ProfileType.SCHEDULE
    elif args.profile_type.lower() == 'execute':
        args.profile_type = ProfileType.EXECUTE

    if args.only_profile:
        profile_main(args)
    else:
        simulation_main(args)
