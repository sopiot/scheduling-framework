#ifndef SCHEDULE_UTILS_H_
#define SCHEDULE_UTILS_H_

#include "my_schedule_policy.h"
#include "scenario_table.h"
#include "schedule_table.h"
#include "service_table.h"
#include "utils.h"

#ifdef __cplusplus
extern "C" {
#endif

//----------------------------------------
// Structures
//----------------------------------------

typedef struct _SScheduleServiceUserData {
  cap_string strScenarioName;
  MySchedulePolicy *pstContext;
  cap_handle hCurScenarioTable;
} SScheduleServiceUserData;

typedef struct _SGetAffectedScenarioOnUnregUserData {
  cap_string strThingName;        // thing name to be found
  cap_string strScenarioNameRef;  // hash key on traversing (scenario name)
  cap_handle hScenarioNameList;   // [out] found scenario list
  cap_bool bFound;
  MySchedulePolicy *pstContext;
} SGetAffectedScenarioOnUnregUserData;

cap_result ScheduleUtils_AssignExecutionResult(IN cap_handle hVariableHash, IN cap_handle hOutputList,
                                               IN SExecutionResult *pstExecutionResult);
cap_result ScheduleUtils_ApplySuperScheduleResult(cap_handle hScheduleTable, cap_string strScenarioName,
                                                  SScheduleResult *pstScheduleResult);
cap_result ScheduleUtils_IntializeScenario(cap_handle hScheduleTable, cap_string strScenarioName,
                                           MySchedulePolicy *pstContext);
cap_result ScheduleUtils_CheckScenarioScheduled(cap_handle hScheduleTable, cap_string strScenarioName,
                                                cap_bool *pbAllScheduled);
cap_result ScheduleUtils_GetAffectedScenarioOnUnreg(MySchedulePolicy *pstContext, cap_string strThingName,
                                                    cap_handle *phScenarioNameList);
cap_result ScheduleUtils_GetAffectedScenarioOnReg(MySchedulePolicy *pstContext, cap_string strThingName,
                                                  cap_handle *phScenarioNameList);
cap_result ScheduleUtils_ScheduleScenario(MySchedulePolicy *pstContext, cap_string strScenarioName);
cap_result ScheduleUtils_UpdateScenario(MySchedulePolicy *pstContext, cap_string strScenarioName,
                                        cap_bool *pbScheduled);

cap_result ScheduleUtils_CheckSchedulability(IN cap_handle hScheduleTable, IN cap_handle hScenarioTable,
                                             IN cap_handle hServiceTable, IN cap_string strThingName,
                                             IN cap_string strFunctionName, IN long long llExecTimeMs, IN int nPeriodMs,
                                             OUT cap_bool *pbSchedulable);

cap_result ScheduleUtils_GetWaitingScenarioList(cap_handle hWaitQueue, cap_string strTargetThingName,
                                                cap_string strTargetServiceName, cap_handle *phScenarioList);

#ifdef __cplusplus
}
#endif

#endif  // SCHEDULE_UTILS_H_
