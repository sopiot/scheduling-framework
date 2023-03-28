file(GLOB common_SRC "*.c")
message("common source list: " ${common_SRC})

add_library(common STATIC ${common_SRC})
target_include_directories(common PUBLIC include ../capcommon/include)
target_link_libraries(common ${CMAKE_THREAD_LIBS_INIT})
