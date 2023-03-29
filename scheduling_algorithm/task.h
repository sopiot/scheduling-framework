#ifndef TASK_H_
#define TASK_H_

#include "CAPString.h"
#include "sop_common.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef enum _EScheduleEventType {
  SCHEDULE_EVENT_REGISTER,
  SCHEDULE_EVENT_UNREGISTER,
  SCHEDULE_EVENT_TIMEOUT_1,
  SCHEDULE_EVENT_TIMEOUT_2,
  SCHEDULE_EVENT_TIMEOUT_3,
  SCHEDULE_EVENT_RESULT_FAIL,
  SCHEDULE_EVENT_ADD_TAG,
  SCHEDULE_EVENT_DEL_TAG,
  SCHEDULE_EVENT_SET_ACCESS,
} EScheduleEventType;

typedef struct _SRunTask {
  ERequestType enType;
  cap_string strRunTopic;
  cap_string strResultTopic;
  cap_string strPayload;
} SRunTask;

typedef struct _SScheduleTask {
  ERequestType enType;
  EScheduleStatusType enScheduleStatus;
  int nPeriodMs;
  cap_string strScenarioName;
  cap_string strScenarioText;
  int nPriority;
  cap_string strFunctionName;
  cap_string strThingName;
  cap_string strRequestKey;
  cap_handle hResultHandler;
  cap_string strResultTopic;
  cap_handle hReplyHandler;
  cap_string strReplyTopic;
  cap_handle hTagList;
} SScheduleTask;

typedef struct _SRequestResult {
  ERequestResultType enType;
  cap_string strResultTopic;
  cap_string strReplyTopic;
  cap_string strPayload;
} SRequestResult;

typedef struct _SScheduleResult {
  cap_string strScenarioName;
  cap_string strThingName;
  cap_string strServiceName;
  int nErrorCode;
} SScheduleResult;

typedef struct _SExecutionResult {
  int nErrorCode;
  cap_string strStringValue;
  double dbValue;
  EValueType enType;
  cap_string strScenarioName;
  cap_string strThingName;
  cap_string strServiceName;
} SExecutionResult;

typedef struct _SScheduleEvent {
  EScheduleEventType enType;
  cap_string strTriggerName;
  cap_string strCategory;
  cap_string strPayload;
  cap_string strThingName;
  cap_string strServiceName;
  // cap_string strPrimaryIdentifier;
  // cap_string strSubIdentifier;
} SScheduleEvent;

// RunTask
cap_result RunTask_Create(IN ERequestType enType, OUT SRunTask **ppRequest);
cap_result RunTask_Destroy(OUT SRunTask **ppstRequest);

// ScheduleTask

cap_result ScheduleTask_Copy(IN SScheduleTask *pstSrc,
                             OUT SScheduleTask **pstDst);
// FIXME: refactor schedule task (at least separate the super schedule)
cap_result ScheduleTask_Create(
    IN ERequestType enType, IN EScheduleStatusType enScheduleStatus,
    IN cap_string strScenarioName, IN cap_string strScenarioText,
    IN int nPriority, IN cap_string strFunctionName, IN cap_string strThingName,
    IN cap_string strRequestKey, IN cap_handle hResultHandler,
    IN cap_string strResultTopic, IN cap_handle hReplyHandler,
    IN cap_string strReplyTopic, IN cap_handle hTagList,
    OUT SScheduleTask **ppScheduleTask);
cap_result ScheduleTask_Destroy(OUT SScheduleTask **ppstScheduleTask);

// RequestResult
cap_result RequestResult_Create(OUT SRequestResult **ppstRequestResult);
cap_result RequestResult_Destroy(OUT SRequestResult **ppstRequestResult);

// ScheduleEvent
cap_result ScheduleEvent_Create(IN EScheduleEventType enType,
                                IN cap_string strTriggerName,
                                OUT SScheduleEvent **ppstScheduleEvent);
cap_result ScheduleEvent_Destroy(OUT SScheduleEvent **ppstScheduleEvent);

// ScheduleResult
cap_result ScheduleResult_Create(IN SRequestResult *pstRequestResult,
                                 OUT SScheduleResult **ppScheduleResult);
cap_result ScheduleResult_Destroy(OUT SScheduleResult **ppstScheduleResult);

// ExecutionResult
cap_result ExecutionResult_Create(IN SRequestResult *pstRequestResult,
                                  OUT SExecutionResult **ppstExecutionResult);
cap_result ExecutionResult_Destroy(OUT SExecutionResult **ppstExecutionResult);

#ifdef __cplusplus
}
#endif

#endif /* TASK_H_ */