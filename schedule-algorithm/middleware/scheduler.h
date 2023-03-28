#ifndef SCHEDULER_H_
#define SCHEDULER_H_

/**
 * @mainpage SoPIoT Scheduler
 *
 * Supported Features:
 *     - Manage Scenarios
 *         - Add, Delete, Run, Stop, Update(Re-schedule) Scenarios
 *     -
 *
 * Variables:
 *     - ESoPHandleId         enID
 *     - cap_string           strBrokerURI
 *     - cap_bool             bCreated
 *     - cap_handle           hMQTTHandler
 *     - SScenarioManagerCallbackData* pstCallback
 *     - cap_handle           hValueCache
 */

#include <CAPString.h>

#include "AppScriptModeler.h"
#include "scenario_table.h"
#include "schedule_table.h"
#include "service_table.h"
#include "sop_common.h"
#include "value_cache.h"

#ifdef __cplusplus
extern "C" {
#endif

#define ERROR_SEPARATOR "\t"

#define SCHEDULER_RUNNER_HASH_BUCKET_NUM (1017)

CAPSTRING_CONST(CAPSTR_CATEGORY_RESULT, "RESULT");
CAPSTRING_CONST(CAPSTR_CATEGORY_EXECUTE, "EXECUTE");
CAPSTRING_CONST(CAPSTR_CATEGORY_SCHEDULE, "SCHEDULE");

typedef struct _SExecutionTable {
  SScheduleTable *pstLocalScheduleTable;
  SScheduleTable *pstSuperScheduleTable;
  SServiceTable *pstServiceTable;
  SScenarioTable *pstScenarioTable;
} SExecutionTable;

typedef struct _SScheduler {
  ESoPHandleId enID;
  cap_bool bCreated;
  cap_string strMiddlewareName;
  cap_handle hParentMQTTHandler;
  cap_handle hChildMQTTHandler;
  cap_string strChildBrokerURI;
  cap_handle hValueCache;
  cap_handle hScenarioTable;  // strScenarioName->SScenarioInfo
  cap_handle hServiceTable;   // strServiceKey -> SServiceInfo
                              // strServiceKey: strThingName.strServiceName
  cap_handle hScheduleTable;  // strScheduleKey: strIdentifier.strServiceName
                              //        (SUPER): strRequestKey.strServiceName
  cap_handle hTempScenarioTable;
  cap_handle hTempScheduleTable;
  cap_handle hSuperThingRequestHash;
  cap_handle hEventQueue;
  cap_handle hScheduleQueue;
  cap_handle hRunQueue;
  cap_handle hWaitQueue;
  cap_handle hCompleteQueue;
  cap_handle hSchedulingThread;
  cap_handle hSchedulePolicy;
} SScheduler;

typedef struct _SProceedData {
  SScheduler *pstScheduler;
  SScenarioInfo *pstScenarioInfo;
  cap_string strScenarioNameRef;
} SProceedData;

cap_result Scheduler_RunScenario(IN SScheduler *pstScheduler,
                                 IN cap_string strScenarioName);
cap_result Scheduler_StopScenario(IN SScheduler *pstScheduler,
                                  IN cap_string strScenarioName);

cap_result Scheduler_Create(OUT cap_handle *phScheduler,
                            IN cap_string strParentBrokerURI,
                            IN cap_string strChildBrokerURI,
                            IN cap_string strMiddlewareName);
cap_result Scheduler_Run(cap_handle hScheduler);
cap_result Scheduler_Destroy(IN OUT cap_handle *phScheduler);
cap_result Scheduler_Join(cap_handle phScheduler);

#ifdef __cplusplus
}
#endif

#endif /* SCHEDULER_H_ */
