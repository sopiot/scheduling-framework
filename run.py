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


def print_code_session_label(text: str = ''):
    from art import text2art
    result = text2art(text, font='big')
    f = [a for a in result.split('\n') if len(a.strip()) > 0]
    maxlen = max([len(a) for a in f])

    padding = '=' * (maxlen + 2)
    result = '\n'.join([padding] + f + [padding])
    print(result)


if __name__ == '__main__':
    args = arg_parse()

    simulation_framework = SoPSimulationFramework(service_parallel=args.service_parallel, result_filename=args.result_filename, download_logs=args.download_logs,
                                                  profile=args.profile, profile_type=args.profile_type,
                                                  mqtt_debug=args.mqtt_debug, middleware_debug=args.middleware_debug)
    simulation_framework.load(config_path=args.config_path, simulation_data_path=args.simulation_data_path, policy_path=args.policy_path)
    simulation_framework.start()
