#ifndef SCHEDULE_POLICY_WRAPPER_H_
#define SCHEDULE_POLICY_WRAPPER_H_

#include "CAPString.h"
#include "task.h"

#ifdef __cplusplus
extern "C" {
#endif

void* SchedulePolicy_Create(void* scheduler);
void SchedulePolicy_Destroy(void* thisSchedulePolicy);

cap_result SchedulePolicy_OnScheduleScenarioCheck(void* thisSchedulePolicy, cap_string strScenarioName,
                                                  cap_bool* pbScheduled);
cap_result SchedulePolicy_OnScheduleScenarioConfirm(void* thisSchedulePolicy, cap_string strScenarioName);
cap_result SchedulePolicy_OnUpdateScenario(void* thisSchedulePolicy, cap_string strScenarioName, cap_bool* pbScheduled);
cap_result SchedulePolicy_OnCancelScenario(void* thisSchedulePolicy, cap_string strScenarioName);
cap_result SchedulePolicy_OnGlobalUpdate(void* thisSchedulePolicy,
                                         int i);  // not used
cap_result SchedulePolicy_OnScheduleSuperRequest(void* thisSchedulePolicy, SScheduleTask* pstScheduleTask,
                                                 cap_bool* pbScheduled);

cap_result SchedulePolicy_OnThingRegister(void* thisSchedulePolicy, cap_string strThingName);
cap_result SchedulePolicy_OnThingUnregister(void* thisSchedulePolicy, cap_string strThingName);
cap_result SchedulePolicy_OnMiddlewareRegister(void* thisSchedulePolicy, int i);
cap_result SchedulePolicy_OnMiddlewareUnregister(void* thisSchedulePolicy, int i);

cap_result SchedulePolicy_OnSuperScheduleResult(void* policy, SScheduleResult* pstScheduleResult);

cap_result SchedulePolicy_OnServiceReady(void* thisSchedulePolicy, int i);
cap_result SchedulePolicy_OnServiceBusy(void* thisSchedulePolicy, int i);
cap_result SchedulePolicy_OnServiceSuccess(void* thisSchedulePolicy, SExecutionResult* pstExecutionResult);
cap_result SchedulePolicy_OnServiceError(void* thisSchedulePolicy, SExecutionResult* pstExecutionResult);
cap_result SchedulePolicy_OnServiceTimeout(void* thisSchedulePolicy, cap_string strScenarioName, int nTry);

cap_result SchedulePolicy_OnSuperServiceReady(void* thisSchedulePolicy, int i);
cap_result SchedulePolicy_OnSuperServiceBusy(void* thisSchedulePolicy, int i);
cap_result SchedulePolicy_OnSuperServiceSuccess(void* thisSchedulePolicy, int i);
cap_result SchedulePolicy_OnSuperServiceError(void* thisSchedulePolicy, int i);
cap_result SchedulePolicy_OnSuperServiceTimeout(void* thisSchedulePolicy, int i);

cap_result SchedulePolicy_OnSubServiceReady(void* thisSchedulePolicy, int i);
cap_result SchedulePolicy_OnSubServiceBusy(void* thisSchedulePolicy, int i);
cap_result SchedulePolicy_OnSubServiceSuccess(void* thisSchedulePolicy, int i);
cap_result SchedulePolicy_OnSubServiceError(void* thisSchedulePolicy, int i);
cap_result SchedulePolicy_OnSubServiceTimeout(void* thisSchedulePolicy, int i);

#ifdef __cplusplus
}
#endif

#endif /* SCHEDULE_POLICY_WRAPPER_H_ */