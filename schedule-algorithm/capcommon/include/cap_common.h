#ifndef CAP_COMMON_H_
#define CAP_COMMON_H_

/** 
 * @mainpage CAP Common Library manual
 *
 * Supported Features:
 *     - Data structures
 *         - Hash, Queue, Key-value (Dictionary), Linked List
 *     - Library wrappers
 *         - socket, file, process, thread, event, lock, time
 *     - String Handling routines
 *     - Application-assist features
 *         - logger
 *
 * Modules:
 *     - CAPHash.c        - Hash implementation
 *     - CAPQueue.c       - Queue implementation
 *     - CAPLinkedList.c  - Llinked list implmentation
 *     - CAPThread.c      - Thread creation
 *     - CAPThreadLock.c  - Thread lock/unlock
 *     - CAPThreadEvent.c - Thread event handling
 *     - CAPSocket.c      - Socket support (currently, only Unix domain socket is supported)
 *     - CAPProcess.c     - Process creation
 *     - CAPKeyValue.c    - Dictionary-type data structure implementation
 *     - CAPFile.c        - File read/write
 *     - CAPTime.c        - Time measurement/sleep
 *     - CAPLogger.c      - File Logger
 */

#include <errno.h>
#include <limits.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifndef CHAR_MAX
#define CHAR_MAX 127
#endif

#ifndef SHRT_MAX
#define SHRT_MAX 0x7FFF
#endif

#ifndef INT_MAX
#define INT_MAX 0x7FFFFFFF
#endif

#ifndef LONG_MAX
#define LONG_MAX 0x7FFFFFFFL
#endif

#ifndef LONG_LONG_MAX
#define LONG_LONG_MAX 0x7FFFFFFFFFFFFFFFLL
#endif

#ifndef IN
#define IN
#endif

#ifndef OUT
#define OUT
#endif

#ifndef TRUE
#define TRUE (1)
#endif

#ifndef FALSE
#define FALSE (0)
#endif

#ifndef NULL
#define NULL (void *)(0)
#endif

#ifndef CALLBACK
#define CALLBACK
#endif

#ifndef MIN
#define MIN(a, b) ((a) < (b) ? (a) : (b))
#endif

#ifndef MAX
#define MAX(a, b) ((a) > (b) ? (a) : (b))
#endif

#ifdef __cplusplus
extern "C" {
#endif

#ifndef WIN32
#define DIR_SEPARATOR '/'
#define LINE_SEPARATOR '\n'
#else
#define DIR_SEPARATOR '\\'
#define LINE_SEPARATOR '\r\n'
#endif

typedef void *cap_handle;
typedef int cap_bool;

typedef enum _EHandleId {
    HANDLEID_CAP_THREAD = 6,
    HANDLEID_CAP_THREAD_LOCK = 7,
    HANDLEID_CAP_THREAD_EVENT = 8,
    HANDLEID_CAP_LINKED_LIST = 9,
    HANDLEID_CAP_SOCKET = 14,
    HANDLEID_CAP_HASH = 15,
    HANDLEID_CAP_THREAD_QUEUE = 16,
    HANDLEID_CAP_FILE = 17,
    HANDLEID_CAP_KEYVALUE = 18,
    HANDLEID_CAP_PROCESS = 22,
    HANDLEID_CAP_LOGGER = 23,
    HANDLEID_CAP_STACK = 24,
} EHandleId;

typedef enum _ECapResult {
    ERR_CAP_NOERROR = 0,
    ERR_CAP_UNKNOWN = 1,
    ERR_CAP_OUT_OF_MEMORY = 2,
    ERR_CAP_INVALID_HANDLE = 3,
    ERR_CAP_FILE_IO_ERROR = 4,
    ERR_CAP_READ_FILE_LACK = 5,
    ERR_CAP_INVALID_PARAM = 6,
    ERR_CAP_NO_CHANGE = 7,
    ERR_CAP_CRITICAL = 8,
    ERR_CAP_TIME_EXPIRED = 9,
    ERR_CAP_ALREADY_DONE = 10,
    ERR_CAP_NO_DATA = 11,
    ERR_CAP_INDEX_OUT_OF_BOUND = 12,
    ERR_CAP_INTERNAL_FAIL = 13,
    ERR_CAP_MUTEX_ERROR = 14,
    ERR_CAP_DB_ERROR = 15,
    ERR_CAP_USER_CANCELED = 16,
    ERR_CAP_CONNECT_ERROR = 17,
    ERR_CAP_DISCONNECT_ERROR = 18,
    ERR_CAP_SUBSCRIBE_ERROR = 19,
    ERR_CAP_UNSUBSCRIBE_ERROR = 20,
    ERR_CAP_SUSPEND = 21,
    ERR_CAP_INVALID_DATA = 22,
    ERR_CAP_NOT_FOUND = 23,
    ERR_CAP_NOT_SUPPORTED = 24,
    ERR_CAP_CONVERSION_ERROR = 25,
    ERR_CAP_DUPLICATED = 26,
    ERR_CAP_CALLBACK_ERROR = 27,
    ERR_CAP_FOUND_DATA = 28,
    ERR_CAP_SOCKET_ERROR = 29,
    ERR_CAP_SERVER_ERROR = 30,
    ERR_CAP_BIND_ERROR = 31,
    ERR_CAP_NET_ERROR = 32,
    ERR_CAP_LISTEN_ERROR = 33,
    ERR_CAP_SELECT_ERROR = 34,
    ERR_CAP_NET_TIMEOUT = 35,
    ERR_CAP_ACCEPT_ERROR = 36,
    ERR_CAP_CLIENT_ERROR = 37,
    ERR_CAP_INVALID_SOCKET = 38,
    ERR_CAP_NET_SEND_ERROR = 39,
    ERR_CAP_NET_RECEIVE_ERROR = 40,
    ERR_CAP_OPEN_FAIL = 41,
    ERR_CAP_FILE_NOT_OPENED = 42,
    ERR_CAP_SEEK_FAIL = 43,
    ERR_CAP_FLUSH_FAIL = 44,
    ERR_CAP_NOT_EMTPY = 45,
    ERR_CAP_CONFIG_ERROR = 46,
    ERR_CAP_INVALID_ACCESS = 47,
    ERR_CAP_INITIALIZE_FAIL = 48,
    ERR_CAP_NOT_FINISHED = 49,
    ERR_CAP_INVALID_ARGUMENT = 50,
    ERR_CAP_INVALID_REQUEST = 51,
    ERR_CAP_READ_DATA_LACK = 52,
    ERR_CAP_NOT_CONNECTED = 53,
    ERR_CAP_REACH_TO_MAXIMUM = 54,
    ERR_CAP_NOT_INITIALIZED = 55,
    ERR_CAP_END_OF_DATA = 56,
    ERR_CAP_NULL_FROM_LIST = 57,
} cap_result;

#ifdef _DEBUG

#include <unistd.h>

#define dp(fmt, args...) fprintf(stderr, fmt, ##args)
#define dlp(fmt, args...) fprintf(stderr, "[%s %s %d]" fmt, __FILE__, __FUNCTION__, __LINE__, ##args)
#define print_id(comment) fprintf(stderr, "sid: %5d, pgid: %5d, pid: %5d, ppid: %5d	 # %s\n", (int)getsid(0), (int)getpgid(0), (int)getpid(), (int)getppid(), comment)

#define ERRIFGOTO(res, label)                                                                                              \
    if ((res) != ERR_CAP_NOERROR) {                                                                                        \
        fprintf(stderr, "error! %d (%s:%d, strerror: %s, pid: %d)\n", res, __FILE__, __LINE__, strerror(errno), getpid()); \
        goto label;                                                                                                        \
    }
#define ERRASSIGNGOTO(res, err, label)                                                                                     \
    {                                                                                                                      \
        res = err;                                                                                                         \
        fprintf(stderr, "error! %d (%s:%d, strerror: %s, pid: %d)\n", res, __FILE__, __LINE__, strerror(errno), getpid()); \
        goto label;                                                                                                        \
    }
#define IFVARERRASSIGNGOTO(var, val, res, err, label)                                           \
    if ((var) == (val)) {                                                                       \
        res = err;                                                                              \
        fprintf(stderr, "error! (%s:%d, strerror: %s)\n", __FILE__, __LINE__, strerror(errno)); \
        goto label;                                                                             \
    }
#define ERRREADGOTO(read, read_full, res, label)                                                     \
    if ((read) < (read_full)) {                                                                      \
        res = ERR_CAP_READ_DATA_LACK;                                                                \
        fprintf(stderr, "read error! (%s:%d, strerror: %s)\n", __FILE__, __LINE__, strerror(errno)); \
        goto label;                                                                                  \
    }
#else
#define dp(fmt, args...)
#define dlp(fmt, args...)
#define print_id(comment)
#define ERRIFGOTO(res, label)       \
    if ((res) != ERR_CAP_NOERROR) { \
        goto label;                 \
    }
#define ERRASSIGNGOTO(res, err, label) \
    {                                  \
        res = err;                     \
        goto label;                    \
    }
#define IFVARERRASSIGNGOTO(var, val, res, err, label) \
    if ((var) == (val)) {                             \
        res = err;                                    \
        goto label;                                   \
    }
#define ERRREADGOTO(read, read_full, res, label) \
    if ((read) < (read_full)) {                  \
        res = ERR_CAP_READ_DATA_LACK;            \
        goto label;                              \
    }
#endif

#define CAPASSIGNGOTO(res, err, label) \
    {                                  \
        res = err;                     \
        goto label;                    \
    }

#define ERRMEMGOTO(var, res, label)  \
    if ((var) == NULL) {             \
        res = ERR_CAP_OUT_OF_MEMORY; \
        goto label;                  \
    }

#define SAFEMEMFREE(mem) \
    if ((mem) != NULL) { \
        free((mem));     \
        mem = NULL;      \
    }

#define IS_VALID_HANDLE(handle, id) (handle != NULL && (*((int *)(handle))) == id)

#define CONST_STRLEN(str) (sizeof(str) - 1)

#define DOUBLE_EPSILON (0.0000001)

#define DOUBLE_IS_APPROX_EQUAL(a, b) (fabs((a) - (b)) <= DOUBLE_EPSILON)

#define DOUBLE_IS_GREATER(a, b) (((a) - (b)) > DOUBLE_EPSILON)

#define DOUBLE_IS_LESS(a, b) (((b) - (a)) > DOUBLE_EPSILON)
#ifdef __cplusplus
}
#endif

#endif /* CAP_COMMON_H_ */
