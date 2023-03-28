file(GLOB schedule_policy_SRC "*.c" "*.cc")
message("schedule policy source list: " ${schedule_policy_SRC})

add_library(schedule-policy SHARED ${schedule_policy_SRC})
target_include_directories(schedule-policy PUBLIC ./capcommon/include ./middleware .)
