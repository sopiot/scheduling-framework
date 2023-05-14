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
    overhead1 = profiler.get_avg_overhead()
    overhead2 = profiler.get_avg_overhead(OverheadType.INNER)
    overhead3 = profiler.get_avg_overhead(OverheadType.COMM)
    overhead4 = profiler.get_avg_overhead(OverheadType.SUPER_THING_INNER)
    overhead5 = profiler.get_avg_overhead(OverheadType.TARGET_THING_INNER)
    overhead6 = profiler.get_avg_overhead(OverheadType.MIDDLEWARE_INNER)
    overhead7 = profiler.get_avg_overhead(OverheadType.SUPER_THING__MIDDLEWARE_COMM)
    overhead8 = profiler.get_avg_overhead(OverheadType.TARGET_THING__MIDDLEWARE_COMM)
    overhead9 = profiler.get_avg_overhead(OverheadType.MIDDLEWARE__MIDDLEWARE_COMM)


if __name__ == '__main__':
    main()
