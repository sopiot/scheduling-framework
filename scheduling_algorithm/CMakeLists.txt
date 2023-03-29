file(GLOB scheduling_policies_SRC "*.c" "*.cc")
message("scheduling policies source list: " ${scheduling_policies_SRC})

add_library(scheduling-policies SHARED ${scheduling_policies_SRC})
target_include_directories(scheduling-policies PUBLIC ./capcommon/include ./middleware .)
