#ifndef SCHEDULING_POLICIES_WRAPPER_H_
#define SCHEDULING_POLICIES_WRAPPER_H_

#include "CAPString.h"
#include "task.h"

#ifdef __cplusplus
extern "C" {
#endif

void* SchedulingPolicies_Create(void* scheduler);
void SchedulingPolicies_Destroy(void* policies);

//----------------------------------------
// Scheduling Request
//----------------------------------------

cap_result SchedulingPolicies_OnScheduleScenarioCheck(void* policies, cap_string strScenarioName, cap_bool* pbScheduled);
cap_result SchedulingPolicies_OnScheduleScenarioConfirm(void* policies, cap_string strScenarioName);
cap_result SchedulingPolicies_OnUpdateScenario(void* policies, cap_string strScenarioName, cap_bool* pbScheduled);
cap_result SchedulingPolicies_OnCancelScenario(void* policies, cap_string strScenarioName);
cap_result SchedulingPolicies_OnGlobalUpdate(void* policies,
                                           int i);  // not used
cap_result SchedulingPolicies_OnSuperScheduleRequest(void* policies, SScheduleTask* pstScheduleTask,
                                                   cap_bool* pbScheduled);
cap_result SchedulingPolicies_OnSuperCancelRequest(cap_string strRequestKey);

//----------------------------------------
// Device Status Change
//----------------------------------------

cap_result SchedulingPolicies_OnThingRegister(void* policies, cap_string strThingName);
cap_result SchedulingPolicies_OnThingUnregister(void* policies, cap_string strThingName);
cap_result SchedulingPolicies_OnMiddlewareRegister(void* policies, int i);
cap_result SchedulingPolicies_OnMiddlewareUnregister(void* policies, int i);

//----------------------------------------
// Device Status Change
//----------------------------------------

cap_result SchedulingPolicies_OnServiceReady(void* policies, SRunTask* pstRunTask);
cap_result SchedulingPolicies_OnServiceBusy(void* policies, SRunTask* pstRunTask);

cap_result SchedulingPolicies_OnSuperServiceReady(void* policies, SRunTask* pstRunTask);
cap_result SchedulingPolicies_OnSuperServiceBusy(void* policies, SRunTask* pstRunTask);

cap_result SchedulingPolicies_OnSubServiceReady(void* policies, SRunTask* pstRunTask);
cap_result SchedulingPolicies_OnSubServiceBusy(void* policies, SRunTask* pstRunTask);

//----------------------------------------
// Device Status Change
//----------------------------------------

cap_result SchedulingPolicies_OnServiceSuccess(void* policies, SExecutionResult* pstExecutionResult);
cap_result SchedulingPolicies_OnServiceError(void* policies, SExecutionResult* pstExecutionResult);
cap_result SchedulingPolicies_OnServiceTimeout(void* policies, cap_string strScenarioName, int nTry);

cap_result SchedulingPolicies_OnSuperServiceSuccess(void* policies, SExecutionResult* pstExecutionResult);
cap_result SchedulingPolicies_OnSuperServiceError(void* policies, SExecutionResult* pstExecutionResult);
cap_result SchedulingPolicies_OnSuperServiceTimeout(void* policies, cap_string strRequestKey, int nTry);

cap_result SchedulingPolicies_OnSubServiceSuccess(void* policies, SExecutionResult* pstExecutionResult);
cap_result SchedulingPolicies_OnSubServiceError(void* policies, SExecutionResult* pstExecutionResult);
cap_result SchedulingPolicies_OnSubServiceTimeout(void* policies, cap_string strRequestKey, int nTry);

// Additional...

cap_result SchedulingPolicies_OnSuperScheduleResult(void* policies, SScheduleResult* pstScheduleResult);

#ifdef __cplusplus
}
#endif

#endif /* SCHEDULING_POLICIES_WRAPPER_H_ */