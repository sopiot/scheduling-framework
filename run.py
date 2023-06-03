from simulation_framework.simulation_framework import *
import argparse


START_LOGGER()


def arg_parse() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', '-c', type=str, dest='config_path',
                        required=False, help='Config file path, or directory path containing environment config files.')
    parser.add_argument('--policy', '-po', type=str, dest='policy_path', default='./scheduling_algorithm/samples',
                        required=False, help='Policy file path, or directory path containing policy files.')
    parser.add_argument('--simulation-data', '-i', type=str, dest='simulation_data_path',
                        required=False, help='Simulation data file path.')
    parser.add_argument('--service-parallel', '-sp', action='store_true', dest='service_parallel',
                        required=False, help='Enable Sub Service to execute in parallel.')
    parser.add_argument('--result-filename', '-o', dest='result_filename', action='store', default='sim_result',
                        required=False, help=('Output simulation result filename, without extension.\n'
                                              'if filename is not given, "sim_result" will be default filename.'))
    parser.add_argument('--mqtt-debug', '-mqtt-d', action='store_true', dest='mqtt_debug',
                        required=False, help='Enable MQTT debug mode.')
    parser.add_argument('--middleware-debug', '-mid-d', action='store_true', dest='middleware_debug',
                        required=False, help='Enable middleware debug mode.')
    parser.add_argument('--download-logs', '-dl', action='store_true', dest='download_logs',
                        required=False, help='Download simulation log files after each simulation end.')
    parser.add_argument('--profile', '-pf', action='store_true', dest='profile',
                        required=False, help='Profile detailed simulation overhead after whole simulation end.')
    parser.add_argument('--only-profile', '-only-pf', action='store_true', dest='only_profile',
                        required=False, help='Enable only profile mode. If this mode is enable, log path should be given.')
    parser.add_argument('--profile-type', '-pt', type=lambda x: ProfileType(x.lower()), default=ProfileType.EXECUTE, dest='profile_type', choices=list(ProfileType),
                        required=False, help=('Profile type\n'
                                              'You can choose from the following:\n'
                                              '  schedule: Profile the scheduling part of simulation\n'
                                              '  execute: Profile the execution part of simulation\n'))
    parser.add_argument('--log', '-lg', type=str, dest='log_path',
                        required=False, help=('Path containing simulation logs\n'
                                              'If there are multiple simulation logs in a folder, profile them all.'
                                              'If the given log path is for a single log, profile for only one log'))
    args = parser.parse_args()

    if not args.only_profile:
        if not args.config_path and not args.simulation_data_path:
            parser.error('config or simulation_file must be provided.')
        elif args.config_path and args.simulation_data_path:
            parser.error('config and simulation_file cannot be provided at the same time.')

        if not args.policy_path:
            parser.error('policy must be provided.')
    else:
        if not args.log_path:
            parser.error('log_path must be provided.')

    return args


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


def print_code_session_label(text: str = ''):
    from art import text2art
    result = text2art(text, font='big')
    f = [a for a in result.split('\n') if len(a.strip()) > 0]
    maxlen = max([len(a) for a in f])

    padding = '=' * (maxlen + 2)
    result = '\n'.join([padding] + f + [padding])
    print(result)


if __name__ == '__main__':
    # print_code_session_label('component generator')
    # print_code_session_label('service generator')
    # print_code_session_label('thing generator')
    # print_code_session_label('scenario generator')
    args = arg_parse()

    simulation_framework = SoPSimulationFramework(service_parallel=args.service_parallel, result_filename=args.result_filename, download_logs=args.download_logs,
                                                  profile=args.profile, profile_type=args.profile_type,
                                                  mqtt_debug=args.mqtt_debug, middleware_debug=args.middleware_debug)
    simulation_framework.load(config_path=args.config_path, simulation_data_path=args.simulation_data_path, policy_path=args.policy_path)
    simulation_framework.start()
