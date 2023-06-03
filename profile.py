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
