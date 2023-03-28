from scheduling_framework.core.schedule_framework import *
from scheduling_framework.core.simulation_generator import *
import argparse


def arg_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config_path_list", '-e', type=str, nargs='+',
                        required=False, help="simulation config path list")
    parser.add_argument("--policy_file_path_list", '-p', type=str, nargs='+',
                        required=False, help="policy_file_path_list")
    parser.add_argument("--simulation_file_path", '-s', type=str, default='',
                        required=False, help="simulation data file path")
    parser.add_argument("--is_parallel", '-pl', action='store_true',
                        required=False, help="is_parallel")
    parser.add_argument("--filename", '-o',
                        required=False, help="output result filename")
    parser.add_argument("--mqtt_debug", '-mqtt_d', action='store_true',
                        required=False, help="mqtt debug mode")
    parser.add_argument("--middleware_debug", '-mid_d', action='store_true',
                        required=False, help="middleware debug mode")
    parser.add_argument("--download_logs", '-dl', action='store_true',
                        required=False, help="download simulation log files")
    arg_list, unknown = parser.parse_known_args()

    return arg_list


def main():
    START_LOGGER()
    args = arg_parse()

    scheduling_framework = SoPSchedulingFramework(config_path_list=args.config_path_list,
                                                  simulation_file_path=args.simulation_file_path,
                                                  mqtt_debug=args.mqtt_debug,
                                                  middleware_debug=args.middleware_debug)

    scheduling_framework.start(policy_file_path_list=args.policy_file_path_list,
                               args=args)


if __name__ == '__main__':
    main()
