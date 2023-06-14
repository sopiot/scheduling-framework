profiler = Profiler()
if args.log_path:
    profiler.load(log_root_path=args.log_path)
    profile_result = profiler.profile(args.profile_type, export=True)
    profiler.print_result()
    customized_print(profile_result=profile_result)
elif args.root_log_path:
    log_path_list = os.listdir(args.root_log_path)
    profile_result_list = []
    for log_path in log_path_list:
        profiler.load(log_root_path=log_path)
        profiler.profile(args.profile_type, export=True)
        profile_result = profiler.print_result()
        profile_result_list.append(profile_result)
        customized_print(profile_result=profile_result)
    profiler.profile_result = sum(profile_result_list, ProfileResult())
    profiler.print_result()


def customized_print(profile_result: ProfileResult):
    """ A Function that prints the profile result in a customized way.

        Users can use the ProfileResult's avg_overhead method to average certain types of overhead.
        This function is an example of a custom profiling result output function that leverages that
        feature.

        This function was written assuming the simulation situation below.
        ===========================================
        [ST(3) <- MW(3)    MW(2)    MW(1)         ]
        [ST(↓)    MW(3)    MW(2)    MW(1)         ]
        ###########################################
        [ST(3) -> MW(3)    MW(2)    MW(1)    LT(1)]
        [ST(3)    MW(↓)    MW(2)    MW(1)    LT(1)]
        [ST(3)    MW(3) -> MW(2)    MW(1)    LT(1)]
        [ST(3)    MW(3)    MW(↓)    MW(1)    LT(1)]
        [ST(3)    MW(3)    MW(2) -> MW(1)    LT(1)]
        [ST(3)    MW(3)    MW(2)    MW(↓)    LT(1)]
        [ST(3)    MW(3)    MW(2)    MW(1) -> LT(1)]
        [ST(3)    MW(3)    MW(2)    MW(1)    LT(↓)]
        [ST(3)    MW(3)    MW(2)    MW(1) <- LT(1)]
        [ST(3)    MW(3)    MW(2)    MW(↓)    LT(1)]
        [ST(3)    MW(3)    MW(2) <- MW(1)    LT(1)]
        [ST(3)    MW(3)    MW(↓)    MW(1)    LT(1)]
        [ST(3)    MW(3) <- MW(2)    MW(1)    LT(1)]
        [ST(3)    MW(↓)    MW(2)    MW(1)    LT(1)]
        [ST(3) <- MW(3)    MW(2)    MW(1)    LT(1)]
        [ST(↓)    MW(3)    MW(2)    MW(1)    LT(1)]
        ###########################################
        [ST(3) -> MW(3)    MW(2)    LT(2)         ]
        ===========================================
        ST:  Super Thing
        MW:  Middleware
        LT:  Local Thing
        (N): Level
        ->, <-: Send packet
        ↓: Inner computation
        ===========================================

    Args:
        profile_result (ProfileResult): Result of profiling
    """
    avg_MS_EXECUTE_comm_overhead = profile_result.avg_overhead(dict(type=OverheadType.SUPER_THING__MIDDLEWARE_COMM,
                                                                    component_type_from=SoPComponentType.MIDDLEWARE,
                                                                    protocol_from=SoPProtocolType.Super.MS_EXECUTE,
                                                                    level_from=3,
                                                                    component_type_to=SoPComponentType.THING,
                                                                    protocol_to=SoPProtocolType.Super.MS_EXECUTE,
                                                                    level_to=3))
    # [ST(↓)    MW(3)    MW(2)    MW(1)         ]
    avg_MS_EXECUTE_inner_overhead = profile_result.avg_overhead(dict(type=OverheadType.SUPER_THING_INNER,
                                                                     component_type_from=SoPComponentType.THING,
                                                                     protocol_from=SoPProtocolType.Super.MS_EXECUTE,
                                                                     level_from=3,
                                                                     component_type_to=SoPComponentType.THING,
                                                                     protocol_to=SoPProtocolType.Super.SM_EXECUTE,
                                                                     level_to=3))
    # [ST(3) -> MW(3)    MW(2)    MW(1)    LT(1)]
    avg_SM_EXECUTE_comm_overhead_3_3 = profile_result.avg_overhead(dict(type=OverheadType.SUPER_THING__MIDDLEWARE_COMM,
                                                                        component_type_from=SoPComponentType.THING,
                                                                        protocol_from=SoPProtocolType.Super.SM_EXECUTE,
                                                                        level_from=3,
                                                                        component_type_to=SoPComponentType.MIDDLEWARE,
                                                                        protocol_to=SoPProtocolType.Super.SM_EXECUTE,
                                                                        level_to=3))
    # [ST(3)    MW(↓)    MW(2)    MW(1)    LT(1)]
    avg_PC_EXECUTE_inner_overhead_3 = profile_result.avg_overhead(dict(type=OverheadType.MIDDLEWARE_INNER,
                                                                       component_type_from=SoPComponentType.MIDDLEWARE,
                                                                       protocol_from=SoPProtocolType.Super.SM_EXECUTE,
                                                                       level_from=3,
                                                                       component_type_to=SoPComponentType.MIDDLEWARE,
                                                                       protocol_to=SoPProtocolType.Super.PC_EXECUTE,
                                                                       level_to=3))
    # [ST(3)    MW(3) -> MW(2)    MW(1)    LT(1)]
    avg_PC_EXECUTE_comm_overhead_3_2 = profile_result.avg_overhead(dict(type=OverheadType.MIDDLEWARE__MIDDLEWARE_COMM,
                                                                        component_type_from=SoPComponentType.MIDDLEWARE,
                                                                        protocol_from=SoPProtocolType.Super.PC_EXECUTE,
                                                                        level_from=3,
                                                                        component_type_to=SoPComponentType.MIDDLEWARE,
                                                                        protocol_to=SoPProtocolType.Super.PC_EXECUTE,
                                                                        level_to=2))
    # [ST(3)    MW(3)    MW(↓)    MW(1)    LT(1)]
    avg_PC_EXECUTE_inner_overhead_2 = profile_result.avg_overhead(dict(type=OverheadType.MIDDLEWARE_INNER,
                                                                       component_type_from=SoPComponentType.MIDDLEWARE,
                                                                       protocol_from=SoPProtocolType.Super.PC_EXECUTE,
                                                                       level_from=2,
                                                                       component_type_to=SoPComponentType.MIDDLEWARE,
                                                                       protocol_to=SoPProtocolType.Super.PC_EXECUTE,
                                                                       level_to=2))
    # [ST(3)    MW(3)    MW(2) -> MW(1)    LT(1)]
    avg_PC_EXECUTE_comm_overhead_2_1 = profile_result.avg_overhead(dict(type=OverheadType.MIDDLEWARE__MIDDLEWARE_COMM,
                                                                        component_type_from=SoPComponentType.MIDDLEWARE,
                                                                        protocol_from=SoPProtocolType.Super.PC_EXECUTE,
                                                                        level_from=2,
                                                                        component_type_to=SoPComponentType.MIDDLEWARE,
                                                                        protocol_to=SoPProtocolType.Super.PC_EXECUTE,
                                                                        level_to=1))
    # [ST(3)    MW(3)    MW(2)    MW(↓)    LT(1)]
    avg_PC_EXECUTE_inner_overhead_1 = profile_result.avg_overhead(dict(type=OverheadType.MIDDLEWARE_INNER,
                                                                       component_type_from=SoPComponentType.MIDDLEWARE,
                                                                       protocol_from=SoPProtocolType.Super.PC_EXECUTE,
                                                                       level_from=1,
                                                                       component_type_to=SoPComponentType.MIDDLEWARE,
                                                                       protocol_to=SoPProtocolType.Base.MT_EXECUTE,
                                                                       level_to=1))
    # [ST(3)    MW(3)    MW(2)    MW(1) -> LT(1)]
    avg_MT_EXECUTE_comm_overhead_1_1 = profile_result.avg_overhead(dict(type=OverheadType.TARGET_THING__MIDDLEWARE_COMM,
                                                                        component_type_from=SoPComponentType.MIDDLEWARE,
                                                                        protocol_from=SoPProtocolType.Base.MT_EXECUTE,
                                                                        level_from=1,
                                                                        component_type_to=SoPComponentType.THING,
                                                                        protocol_to=SoPProtocolType.Base.MT_EXECUTE,
                                                                        level_to=1))
    # [ST(3)    MW(3)    MW(2)    MW(1)    LT(↓)]
    avg_MT_EXECUTE_inner_overhead_1 = profile_result.avg_overhead(dict(type=OverheadType.TARGET_THING_INNER,
                                                                       component_type_from=SoPComponentType.THING,
                                                                       protocol_from=SoPProtocolType.Base.MT_EXECUTE,
                                                                       level_from=1,
                                                                       component_type_to=SoPComponentType.THING,
                                                                       protocol_to=SoPProtocolType.Base.TM_RESULT_EXECUTE,
                                                                       level_to=1))
    # [ST(3)    MW(3)    MW(2)    MW(1) <- LT(1)]
    avg_MT_RESULT_EXECUTE_comm_overhead_1 = profile_result.avg_overhead(dict(type=OverheadType.TARGET_THING__MIDDLEWARE_COMM,
                                                                             component_type_from=SoPComponentType.THING,
                                                                             protocol_from=SoPProtocolType.Base.TM_RESULT_EXECUTE,
                                                                             level_from=1,
                                                                             component_type_to=SoPComponentType.MIDDLEWARE,
                                                                             protocol_to=SoPProtocolType.Base.TM_RESULT_EXECUTE,
                                                                             level_to=1))
    # [ST(3)    MW(3)    MW(2)    MW(↓)    LT(1)]
    avg_CP_RESULT_EXECUTE_inner_overhead_1 = profile_result.avg_overhead(dict(type=OverheadType.MIDDLEWARE_INNER,
                                                                              component_type_from=SoPComponentType.MIDDLEWARE,
                                                                              protocol_from=SoPProtocolType.Base.TM_RESULT_EXECUTE,
                                                                              level_from=1,
                                                                              component_type_to=SoPComponentType.MIDDLEWARE,
                                                                              protocol_to=SoPProtocolType.Super.CP_RESULT_EXECUTE,
                                                                              level_to=1))
    # [ST(3)    MW(3)    MW(2) <- MW(1)    LT(1)]
    avg_CP_RESULT_EXECUTE_comm_overhead_1_2 = profile_result.avg_overhead(dict(type=OverheadType.MIDDLEWARE__MIDDLEWARE_COMM,
                                                                               component_type_from=SoPComponentType.MIDDLEWARE,
                                                                               protocol_from=SoPProtocolType.Super.CP_RESULT_EXECUTE,
                                                                               level_from=1,
                                                                               component_type_to=SoPComponentType.MIDDLEWARE,
                                                                               protocol_to=SoPProtocolType.Super.CP_RESULT_EXECUTE,
                                                                               level_to=2))
    # [ST(3)    MW(3)    MW(↓)    MW(1)    LT(1)]
    avg_CP_RESULT_EXECUTE_inner_overhead_2 = profile_result.avg_overhead(dict(type=OverheadType.MIDDLEWARE_INNER,
                                                                              component_type_from=SoPComponentType.MIDDLEWARE,
                                                                              protocol_from=SoPProtocolType.Super.CP_RESULT_EXECUTE,
                                                                              level_from=2,
                                                                              component_type_to=SoPComponentType.MIDDLEWARE,
                                                                              protocol_to=SoPProtocolType.Super.CP_RESULT_EXECUTE,
                                                                              level_to=2))
    # [ST(3)    MW(3) <- MW(2)    MW(1)    LT(1)]
    avg_CP_RESULT_EXECUTE_comm_overhead_2_3 = profile_result.avg_overhead(dict(type=OverheadType.MIDDLEWARE__MIDDLEWARE_COMM,
                                                                               component_type_from=SoPComponentType.MIDDLEWARE,
                                                                               protocol_from=SoPProtocolType.Super.CP_RESULT_EXECUTE,
                                                                               level_from=2,
                                                                               component_type_to=SoPComponentType.MIDDLEWARE,
                                                                               protocol_to=SoPProtocolType.Super.CP_RESULT_EXECUTE,
                                                                               level_to=3))
    # [ST(3)    MW(↓)    MW(2)    MW(1)    LT(1)]
    avg_CP_RESULT_EXECUTE_inner_overhead_3 = profile_result.avg_overhead(dict(type=OverheadType.MIDDLEWARE_INNER,
                                                                              component_type_from=SoPComponentType.MIDDLEWARE,
                                                                              protocol_from=SoPProtocolType.Super.CP_RESULT_EXECUTE,
                                                                              level_from=3,
                                                                              component_type_to=SoPComponentType.MIDDLEWARE,
                                                                              protocol_to=SoPProtocolType.Super.MS_RESULT_EXECUTE,
                                                                              level_to=3))
    # [ST(3) <- MW(3)    MW(2)    MW(1)    LT(1)]
    avg_MS_RESULT_EXECUTE_comm_overhead_3_3 = profile_result.avg_overhead(dict(type=OverheadType.SUPER_THING__MIDDLEWARE_COMM,
                                                                               component_type_from=SoPComponentType.MIDDLEWARE,
                                                                               protocol_from=SoPProtocolType.Super.MS_RESULT_EXECUTE,
                                                                               level_from=3,
                                                                               component_type_to=SoPComponentType.THING,
                                                                               protocol_to=SoPProtocolType.Super.MS_RESULT_EXECUTE,
                                                                               level_to=3))
    # [ST(↓)    MW(3)    MW(2)    MW(1)    LT(1)]
    avg_MS_RESULT_EXECUTE_inner_overhead_3 = profile_result.avg_overhead(dict(type=OverheadType.SUPER_THING_INNER,
                                                                              component_type_from=SoPComponentType.THING,
                                                                              protocol_from=SoPProtocolType.Super.MS_RESULT_EXECUTE,
                                                                              level_from=3,
                                                                              component_type_to=SoPComponentType.THING,
                                                                              protocol_to=SoPProtocolType.Super.SM_EXECUTE,
                                                                              level_to=3))
    # [ST(↓)    MW(3)    MW(2)    MW(1)    LT(1)]
    avg_MS_RESULT_EXECUTE_inner_overhead_final = profile_result.avg_overhead(dict(type=OverheadType.SUPER_THING_INNER,
                                                                                  component_type_from=SoPComponentType.THING,
                                                                                  protocol_from=SoPProtocolType.Super.MS_RESULT_EXECUTE,
                                                                                  level_from=3,
                                                                                  component_type_to=SoPComponentType.THING,
                                                                                  protocol_to=SoPProtocolType.Super.SM_RESULT_EXECUTE,
                                                                                  level_to=3))
    # [ST(3) -> MW(3)    MW(2)    LT(2)         ]
    avg_SM_RESULT_EXECUTE_comm_overhead = profile_result.avg_overhead(dict(type=OverheadType.SUPER_THING__MIDDLEWARE_COMM,
                                                                           component_type_from=SoPComponentType.THING,
                                                                           protocol_from=SoPProtocolType.Super.SM_RESULT_EXECUTE,
                                                                           level_from=3,
                                                                           component_type_to=SoPComponentType.MIDDLEWARE,
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
