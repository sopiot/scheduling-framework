from simulation_framework.core.profiler import *
import argparse


def arg_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root_log_path", '-s', type=str,
                        required=True, help="root log dir path")
    arg_list, unknown = parser.parse_known_args()

    return arg_list


def main():
    START_LOGGER()
    args = arg_parse()

    profiler = Profiler(root_log_folder_path=args.root_log_path)
    profiler.profile(ProfileType.EXECUTE)
    print(profiler)


if __name__ == '__main__':
    main()
