from simulation_framework.core.profiler import *
import argparse

START_LOGGER()


def arg_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root_log_path', '-s', type=str,
                        help=('Path containing simulation logs\n'
                              'If there are multiple simulation logs in a folder, profile them all.'))
    parser.add_argument('--log_path', '-t', type=str,
                        help=('Specific simulation log path'))
    parser.add_argument('--profile_type', '-pt', type=str,
                        required=True, help=('Profile type\n'
                                             'You can choose from the following:\n'
                                             '  Schedule: Profile the scheduling part of simulation\n'
                                             '  Execute: Profile the execution part of simulation\n'))
    args, unknown = parser.parse_known_args()

    if not args.log_path and not args.root_log_path:
        parser.error("log_path 또는 root_log_path 중 하나는 제공해야 합니다.")

    return args


def main():
    args = arg_parse()

    if args.profile_type.lower() == 'schedule':
        profile_type = ProfileType.SCHEDULE
    elif args.profile_type.lower() == 'execute':
        profile_type = ProfileType.EXECUTE

    if args.log_path:
        profiler = Profiler()
        profiler.load(log_root_path=args.log_path)
        simulation_overhead = profiler.profile(ProfileType.EXECUTE, export=True)
        print_result(simulation_overhead=simulation_overhead)
        print_detail_result(simulation_overhead=simulation_overhead)
    elif args.root_log_path:
        log_path_list = os.listdir(args.root_log_path)
        for log_path in log_path_list:
            profiler = Profiler()
            profiler.load(log_root_path=log_path)
            simulation_overhead = profiler.profile(ProfileType.EXECUTE, export=True)
            print_result(simulation_overhead=simulation_overhead)
            print_detail_result(simulation_overhead=simulation_overhead)


def print_result(simulation_overhead: SimulationOverhead):
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
total overhead:                                {avg_total_overhead.total_seconds()*1e3:8.3f} ms\n\
total inner overhead:                          {avg_inner_overhead.total_seconds()*1e3:8.3f} ms\n\
total comm overhead:                           {avg_comm_overhead.total_seconds()*1e3:8.3f} ms\n\
total MIDDLEWARE_INNER overhead:               {avg_overhead_middleware_inner_sum.total_seconds()*1e3:8.3f} ms\n\
total SUPER_THING_INNER overhead:              {avg_overhead_super_thing_inner_sum.total_seconds()*1e3:8.3f} ms\n\
total TARGET_THING service execution:          {avg_overhead_target_thing_inner_sum.total_seconds()*1e3:8.3f} ms\n\
total MIDDLEWARE__MIDDLEWARE_COMM overhead:    {avg_overhead_middleware__middleware_comm_sum.total_seconds()*1e3:8.3f} ms\n\
total SUPER_THING__MIDDLEWARE_COMM overhead:   {avg_overhead_super_thing__middleware_comm_sum.total_seconds()*1e3:8.3f} ms\n\
total TARGET_THING__MIDDLEWARE_COMM overhead:  {avg_overhead_target_thing__middleware_comm_sum.total_seconds()*1e3:8.3f} ms')


def print_detail_result(simulation_overhead: SimulationOverhead):
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
    avg_MS_EXECUTE_comm_overhead = simulation_overhead.avg_overhead(dict(type=OverheadType.SUPER_THING__MIDDLEWARE_COMM,
                                                                         element_type_from=SoPElementType.MIDDLEWARE,
                                                                         protocol_from=SoPProtocolType.Super.MS_EXECUTE,
                                                                         level_from=3,
                                                                         element_type_to=SoPElementType.THING,
                                                                         protocol_to=SoPProtocolType.Super.MS_EXECUTE,
                                                                         level_to=3))
    # [ST(↓)    MW(3)    MW(2)    MW(1)         ]
    avg_MS_EXECUTE_inner_overhead = simulation_overhead.avg_overhead(dict(type=OverheadType.SUPER_THING_INNER,
                                                                          element_type_from=SoPElementType.THING,
                                                                          protocol_from=SoPProtocolType.Super.MS_EXECUTE,
                                                                          level_from=3,
                                                                          element_type_to=SoPElementType.THING,
                                                                          protocol_to=SoPProtocolType.Super.SM_EXECUTE,
                                                                          level_to=3))
    # [ST(3) -> MW(3)    MW(2)    MW(1)    LT(1)]
    avg_SM_EXECUTE_comm_overhead_3_3 = simulation_overhead.avg_overhead(dict(type=OverheadType.SUPER_THING__MIDDLEWARE_COMM,
                                                                             element_type_from=SoPElementType.THING,
                                                                             protocol_from=SoPProtocolType.Super.SM_EXECUTE,
                                                                             level_from=3,
                                                                             element_type_to=SoPElementType.MIDDLEWARE,
                                                                             protocol_to=SoPProtocolType.Super.SM_EXECUTE,
                                                                             level_to=3))
    # [ST(3)    MW(↓)    MW(2)    MW(1)    LT(1)]
    avg_PC_EXECUTE_inner_overhead_3 = simulation_overhead.avg_overhead(dict(type=OverheadType.MIDDLEWARE_INNER,
                                                                            element_type_from=SoPElementType.MIDDLEWARE,
                                                                            protocol_from=SoPProtocolType.Super.SM_EXECUTE,
                                                                            level_from=3,
                                                                            element_type_to=SoPElementType.MIDDLEWARE,
                                                                            protocol_to=SoPProtocolType.Super.PC_EXECUTE,
                                                                            level_to=3))
    # [ST(3)    MW(3) -> MW(2)    MW(1)    LT(1)]
    avg_PC_EXECUTE_comm_overhead_3_2 = simulation_overhead.avg_overhead(dict(type=OverheadType.MIDDLEWARE__MIDDLEWARE_COMM,
                                                                             element_type_from=SoPElementType.MIDDLEWARE,
                                                                             protocol_from=SoPProtocolType.Super.PC_EXECUTE,
                                                                             level_from=3,
                                                                             element_type_to=SoPElementType.MIDDLEWARE,
                                                                             protocol_to=SoPProtocolType.Super.PC_EXECUTE,
                                                                             level_to=2))
    # [ST(3)    MW(3)    MW(↓)    MW(1)    LT(1)]
    avg_PC_EXECUTE_inner_overhead_2 = simulation_overhead.avg_overhead(dict(type=OverheadType.MIDDLEWARE_INNER,
                                                                            element_type_from=SoPElementType.MIDDLEWARE,
                                                                            protocol_from=SoPProtocolType.Super.PC_EXECUTE,
                                                                            level_from=2,
                                                                            element_type_to=SoPElementType.MIDDLEWARE,
                                                                            protocol_to=SoPProtocolType.Super.PC_EXECUTE,
                                                                            level_to=2))
    # [ST(3)    MW(3)    MW(2) -> MW(1)    LT(1)]
    avg_PC_EXECUTE_comm_overhead_2_1 = simulation_overhead.avg_overhead(dict(type=OverheadType.MIDDLEWARE__MIDDLEWARE_COMM,
                                                                             element_type_from=SoPElementType.MIDDLEWARE,
                                                                             protocol_from=SoPProtocolType.Super.PC_EXECUTE,
                                                                             level_from=2,
                                                                             element_type_to=SoPElementType.MIDDLEWARE,
                                                                             protocol_to=SoPProtocolType.Super.PC_EXECUTE,
                                                                             level_to=1))
    # [ST(3)    MW(3)    MW(2)    MW(↓)    LT(1)]
    avg_PC_EXECUTE_inner_overhead_1 = simulation_overhead.avg_overhead(dict(type=OverheadType.MIDDLEWARE_INNER,
                                                                            element_type_from=SoPElementType.MIDDLEWARE,
                                                                            protocol_from=SoPProtocolType.Super.PC_EXECUTE,
                                                                            level_from=1,
                                                                            element_type_to=SoPElementType.MIDDLEWARE,
                                                                            protocol_to=SoPProtocolType.Base.MT_EXECUTE,
                                                                            level_to=1))
    # [ST(3)    MW(3)    MW(2)    MW(1) -> LT(1)]
    avg_MT_EXECUTE_comm_overhead_1_1 = simulation_overhead.avg_overhead(dict(type=OverheadType.TARGET_THING__MIDDLEWARE_COMM,
                                                                             element_type_from=SoPElementType.MIDDLEWARE,
                                                                             protocol_from=SoPProtocolType.Base.MT_EXECUTE,
                                                                             level_from=1,
                                                                             element_type_to=SoPElementType.THING,
                                                                             protocol_to=SoPProtocolType.Base.MT_EXECUTE,
                                                                             level_to=1))
    # [ST(3)    MW(3)    MW(2)    MW(1)    LT(↓)]
    avg_MT_EXECUTE_inner_overhead_1 = simulation_overhead.avg_overhead(dict(type=OverheadType.TARGET_THING_INNER,
                                                                            element_type_from=SoPElementType.THING,
                                                                            protocol_from=SoPProtocolType.Base.MT_EXECUTE,
                                                                            level_from=1,
                                                                            element_type_to=SoPElementType.THING,
                                                                            protocol_to=SoPProtocolType.Base.TM_RESULT_EXECUTE,
                                                                            level_to=1))
    # [ST(3)    MW(3)    MW(2)    MW(1) <- LT(1)]
    avg_MT_RESULT_EXECUTE_comm_overhead_1 = simulation_overhead.avg_overhead(dict(type=OverheadType.TARGET_THING__MIDDLEWARE_COMM,
                                                                                  element_type_from=SoPElementType.THING,
                                                                                  protocol_from=SoPProtocolType.Base.TM_RESULT_EXECUTE,
                                                                                  level_from=1,
                                                                                  element_type_to=SoPElementType.MIDDLEWARE,
                                                                                  protocol_to=SoPProtocolType.Base.TM_RESULT_EXECUTE,
                                                                                  level_to=1))
    # [ST(3)    MW(3)    MW(2)    MW(↓)    LT(1)]
    avg_CP_RESULT_EXECUTE_inner_overhead_1 = simulation_overhead.avg_overhead(dict(type=OverheadType.MIDDLEWARE_INNER,
                                                                                   element_type_from=SoPElementType.MIDDLEWARE,
                                                                                   protocol_from=SoPProtocolType.Base.TM_RESULT_EXECUTE,
                                                                                   level_from=1,
                                                                                   element_type_to=SoPElementType.MIDDLEWARE,
                                                                                   protocol_to=SoPProtocolType.Super.CP_RESULT_EXECUTE,
                                                                                   level_to=1))
    # [ST(3)    MW(3)    MW(2) <- MW(1)    LT(1)]
    avg_CP_RESULT_EXECUTE_comm_overhead_1_2 = simulation_overhead.avg_overhead(dict(type=OverheadType.MIDDLEWARE__MIDDLEWARE_COMM,
                                                                                    element_type_from=SoPElementType.MIDDLEWARE,
                                                                                    protocol_from=SoPProtocolType.Super.CP_RESULT_EXECUTE,
                                                                                    level_from=1,
                                                                                    element_type_to=SoPElementType.MIDDLEWARE,
                                                                                    protocol_to=SoPProtocolType.Super.CP_RESULT_EXECUTE,
                                                                                    level_to=2))
    # [ST(3)    MW(3)    MW(↓)    MW(1)    LT(1)]
    avg_CP_RESULT_EXECUTE_inner_overhead_2 = simulation_overhead.avg_overhead(dict(type=OverheadType.MIDDLEWARE_INNER,
                                                                                   element_type_from=SoPElementType.MIDDLEWARE,
                                                                                   protocol_from=SoPProtocolType.Super.CP_RESULT_EXECUTE,
                                                                                   level_from=2,
                                                                                   element_type_to=SoPElementType.MIDDLEWARE,
                                                                                   protocol_to=SoPProtocolType.Super.CP_RESULT_EXECUTE,
                                                                                   level_to=2))
    # [ST(3)    MW(3) <- MW(2)    MW(1)    LT(1)]
    avg_CP_RESULT_EXECUTE_comm_overhead_2_3 = simulation_overhead.avg_overhead(dict(type=OverheadType.MIDDLEWARE__MIDDLEWARE_COMM,
                                                                                    element_type_from=SoPElementType.MIDDLEWARE,
                                                                                    protocol_from=SoPProtocolType.Super.CP_RESULT_EXECUTE,
                                                                                    level_from=2,
                                                                                    element_type_to=SoPElementType.MIDDLEWARE,
                                                                                    protocol_to=SoPProtocolType.Super.CP_RESULT_EXECUTE,
                                                                                    level_to=3))
    # [ST(3)    MW(↓)    MW(2)    MW(1)    LT(1)]
    avg_CP_RESULT_EXECUTE_inner_overhead_3 = simulation_overhead.avg_overhead(dict(type=OverheadType.MIDDLEWARE_INNER,
                                                                                   element_type_from=SoPElementType.MIDDLEWARE,
                                                                                   protocol_from=SoPProtocolType.Super.CP_RESULT_EXECUTE,
                                                                                   level_from=3,
                                                                                   element_type_to=SoPElementType.MIDDLEWARE,
                                                                                   protocol_to=SoPProtocolType.Super.MS_RESULT_EXECUTE,
                                                                                   level_to=3))
    # [ST(3) <- MW(3)    MW(2)    MW(1)    LT(1)]
    avg_MS_RESULT_EXECUTE_comm_overhead_3_3 = simulation_overhead.avg_overhead(dict(type=OverheadType.SUPER_THING__MIDDLEWARE_COMM,
                                                                                    element_type_from=SoPElementType.MIDDLEWARE,
                                                                                    protocol_from=SoPProtocolType.Super.MS_RESULT_EXECUTE,
                                                                                    level_from=3,
                                                                                    element_type_to=SoPElementType.THING,
                                                                                    protocol_to=SoPProtocolType.Super.MS_RESULT_EXECUTE,
                                                                                    level_to=3))
    # [ST(↓)    MW(3)    MW(2)    MW(1)    LT(1)]
    avg_MS_RESULT_EXECUTE_inner_overhead_3 = simulation_overhead.avg_overhead(dict(type=OverheadType.SUPER_THING_INNER,
                                                                                   element_type_from=SoPElementType.THING,
                                                                                   protocol_from=SoPProtocolType.Super.MS_RESULT_EXECUTE,
                                                                                   level_from=3,
                                                                                   element_type_to=SoPElementType.THING,
                                                                                   protocol_to=SoPProtocolType.Super.SM_EXECUTE,
                                                                                   level_to=3))
    # [ST(↓)    MW(3)    MW(2)    MW(1)    LT(1)]
    avg_MS_RESULT_EXECUTE_inner_overhead_final = simulation_overhead.avg_overhead(dict(type=OverheadType.SUPER_THING_INNER,
                                                                                  element_type_from=SoPElementType.THING,
                                                                                  protocol_from=SoPProtocolType.Super.MS_RESULT_EXECUTE,
                                                                                  level_from=3,
                                                                                  element_type_to=SoPElementType.THING,
                                                                                  protocol_to=SoPProtocolType.Super.SM_RESULT_EXECUTE,
                                                                                  level_to=3))
    # [ST(3) -> MW(3)    MW(2)    LT(2)         ]
    avg_SM_RESULT_EXECUTE_comm_overhead = simulation_overhead.avg_overhead(dict(type=OverheadType.SUPER_THING__MIDDLEWARE_COMM,
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
    return (avg_MS_EXECUTE_comm_overhead, avg_MS_EXECUTE_inner_overhead,
            avg_SM_EXECUTE_comm_overhead_3_3, avg_PC_EXECUTE_inner_overhead_3,
            avg_PC_EXECUTE_comm_overhead_3_2, avg_PC_EXECUTE_inner_overhead_2,
            avg_PC_EXECUTE_comm_overhead_2_1, avg_PC_EXECUTE_inner_overhead_1,
            avg_MT_EXECUTE_comm_overhead_1_1, avg_MT_EXECUTE_inner_overhead_1, avg_MT_RESULT_EXECUTE_comm_overhead_1,
            avg_CP_RESULT_EXECUTE_inner_overhead_1, avg_CP_RESULT_EXECUTE_comm_overhead_1_2,
            avg_CP_RESULT_EXECUTE_inner_overhead_2, avg_CP_RESULT_EXECUTE_comm_overhead_2_3,
            avg_CP_RESULT_EXECUTE_inner_overhead_3, avg_MS_RESULT_EXECUTE_comm_overhead_3_3,
            avg_MS_RESULT_EXECUTE_inner_overhead_3, avg_MS_RESULT_EXECUTE_inner_overhead_final, avg_SM_RESULT_EXECUTE_comm_overhead)


if __name__ == '__main__':
    main()
