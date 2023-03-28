#ifndef SOPCOMMON_H_
#define SOPCOMMON_H_

#include <stdarg.h>

#include "CAPLogger.h"
#include "CAPString.h"
#include "cap_common.h"

#ifdef __cplusplus
extern "C" {
#endif

#ifndef NO_MOVE
#define NO_MOVE (-1)
#endif

typedef enum _ETopicLevel {
  TOPIC_LEVEL_FIRST,
  TOPIC_LEVEL_SECOND,
  TOPIC_LEVEL_THIRD,
  TOPIC_LEVEL_FOURTH,
  TOPIC_LEVEL_FIFTH,
  TOPIC_LEVEL_SIXTH,
  TOPIC_LEVEL_SEVENTH,
  TOPIC_LEVEL_EIGHTH,
} ETopicLevel;

#define HANDLID_GROUP_MIDDLEWARE (0x1000)
#define MIDDLEWARE_IDX_LOCAL (1)

typedef enum _ESoPHandleId {
  HANDLEID_SCENARIO = HANDLID_GROUP_MIDDLEWARE | 1,
  HANDLEID_CENTRAL_MANAGER,
  HANDLEID_SCHEDULER,

  HANDLEID_HIERARCHY_MANAGER,
  HANDLEID_THING_MANAGER,
  HANDLEID_INFO_MANAGER,
  HANDLEID_SCENARIO_RUNNER,
  HANDLEID_SCENARIO_MANAGER,

  HANDLEID_MQTT_MESSAGE_HANDLER,
  HANDLEID_VALUE_CACHE,
} ESoPHandleId;

typedef enum _ESource {
  FROM_PARENT,  // to parent mw
  FROM_LOCAL,   // to client or local server
  FROM_CHILD,   // to child mw
} ESource;

typedef enum _EDestination {
  DST_PARENT,  // to parent mw
  DST_LOCAL,   // to client or local server
  DST_CHILD,   // to child mw
  DST_SUPER,   // to super thing
} EDestination;

typedef enum _EScheduleStatusType {
  SCHEDULE_STATUS_NORMAL,
  SCHEDULE_STATUS_CHECK,
  SCHEDULE_STATUS_CONFIRM
} EScheduleStatusType;

typedef enum _EValueType {
  VALUE_TYPE_INT,
  VALUE_TYPE_DOUBLE,
  VALUE_TYPE_BOOL,
  VALUE_TYPE_STRING,
  VALUE_TYPE_BINARY,
  VALUE_TYPE_VOID,  // return type of a void function
  VALUE_TYPE_UNKNOWN,
} EValueType;

typedef enum _ERequestType {
  REQUEST_UNKNOWN = 0,
  ADD_SCENARIO,                // add schedule task in a local scenario
  CANCEL_SCENARIO,             // cancel schedule task in a local scenario
  UPDATE_SCENARIO,             // update schedule task in a local scenario
  SUPER_SCHEDULE_BY_SCENARIO,  // super schedule task in a local scenario
  SCHEDULE_BY_SUPER_SERVICE,   // super thing schedule request from a super
                               // service
  EXECUTION_BY_SCENARIO,       // execution task in a local scenario
  EXECUTION_BY_SUPER_SERVICE,  // super thing execution request from a super
                               // service
} ERequestType;

typedef enum _ERequestResultType {
  REQUEST_RESULT_UNKNOWN = 0,
  EXEC_RESULT_TO_SCENARIO = 1,
  LOCAL_EXEC_RESULT_TO_SUPER_SERVICE = 2,
  SUPER_SCHEDULE_RESULT_TO_SCENARIO = 3,
} ERequestResultType;

typedef enum _EMqttErrorCode {
  ERR_MQTT_NOERROR = 0,
  ERR_MQTT_FAIL = -1,
  ERR_MQTT_DUPLICATED = -4,
  ERR_MQTT_NOT_SUPPORTED = -5,
  ERR_MQTT_INVALID_REQUEST = -7,
} EMqttErrorCode;

typedef struct _SMQTTData {
  char *pszTopic;
  int nTopicLen;
  char *pszPayload;
  int nPayloadLen;
} SMQTTData;

CAPSTRING_CONST(CAPSTR_PROTOCOL_TM, "TM");
CAPSTRING_CONST(CAPSTR_PROTOCOL_MT, "MT");
CAPSTRING_CONST(CAPSTR_PROTOCOL_EM, "EM");
CAPSTRING_CONST(CAPSTR_PROTOCOL_ME, "ME");
CAPSTRING_CONST(CAPSTR_PROTOCOL_MS, "MS");
CAPSTRING_CONST(CAPSTR_PROTOCOL_SM, "SM");
CAPSTRING_CONST(CAPSTR_PROTOCOL_CP, "CP");
CAPSTRING_CONST(CAPSTR_PROTOCOL_PC, "PC");

CAPSTRING_CONST(CAPSTR_STATUS_CHECK, "check");
CAPSTRING_CONST(CAPSTR_STATUS_CONFIRM, "confirm");
CAPSTRING_CONST(CAPSTR_SUPER_THING_REQUEST, "SUPER_THING_REQUEST");
CAPSTRING_CONST(CAPSTR_SUPER, "SUPER");

#define ERROR_TYPE_INFORMATION 0x01000000
#define ERROR_TYPE_ERROR 0x02000000
#define ERROR_TYPE_CRITICAL 0x03000000

#define MODULE_COMMON 0x00000000
#define MODULE_THING_HANDLER 0x00100000
#define MODULE_SCENARIO_MANAGER 0x00200000
#define MODULE_THING_MANAGER 0x00300000

// TODO(hyunjae): should change level1 & leve2 to 1, 2.
// Set to 0 for testing purpose at the moment
#define QOS_LEVEL_0 (0)
#define QOS_LEVEL_1 (1)
#define QOS_LEVEL_2 (2)

#define SAFEJSONFREE(mem)   \
  if ((mem) != NULL) {      \
    json_object_put((mem)); \
    mem = NULL;             \
  }

extern cap_bool g_bExit;
extern cap_handle g_hLogger;

#define SOPLOG_ERROR(fmt, ...)            \
  dp("[ERROR] " fmt "\n", ##__VA_ARGS__); \
  CAPLogger_Write(g_hLogger, MSG_ERROR, fmt, ##__VA_ARGS__);

#define SOPLOG_WARN(fmt, ...)            \
  dp("[WARN] " fmt "\n", ##__VA_ARGS__); \
  CAPLogger_Write(g_hLogger, MSG_WARN, fmt, ##__VA_ARGS__);

#define SOPLOG_DETAIL(fmt, ...)            \
  dp("[DETAIL] " fmt "\n", ##__VA_ARGS__); \
  CAPLogger_Write(g_hLogger, MSG_DETAIL, fmt, ##__VA_ARGS__);

#define SOPLOG_INFO(fmt, ...)            \
  dp("[INFO] " fmt "\n", ##__VA_ARGS__); \
  CAPLogger_Write(g_hLogger, MSG_INFO, fmt, ##__VA_ARGS__);

#define SOPLOG_DEBUG(fmt, ...)            \
  dp("[DEBUG] " fmt "\n", ##__VA_ARGS__); \
  CAPLogger_Write(g_hLogger, MSG_DEBUG, fmt, ##__VA_ARGS__);

#ifdef __cplusplus
}
#endif

#endif /* SOPCOMMON_H_ */
