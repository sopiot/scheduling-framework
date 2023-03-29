#include "scheduling_policies_wrapper.h"

#include "my_scheduling_policies.h"
#include "scheduler.h"

void* SchedulingPolicies_Create(void* scheduler) {
  SScheduler* pstScheduler = (SScheduler*)scheduler;

  return new MySchedulingPolicies(
      pstScheduler->strMiddlewareName, pstScheduler->hServiceTable, pstScheduler->hScenarioTable,
      pstScheduler->hScheduleTable, pstScheduler->hTempScenarioTable, pstScheduler->hTempScheduleTable,
      pstScheduler->hSuperThingRequestHash, pstScheduler->hRunQueue, pstScheduler->hWaitQueue,
      pstScheduler->hEventQueue, pstScheduler->hScheduleQueue, pstScheduler->hCompleteQueue,
      pstScheduler->hParentMQTTHandler, pstScheduler->hChildMQTTHandler);
}
void SchedulingPolicies_Destroy(void* policies) { delete static_cast<MySchedulingPolicies*>(policies); }

//----------------------------------------
// Mapping Algorithm
//----------------------------------------

cap_result SchedulingPolicies_OnMapService(void* policies, cap_string strServiceName, cap_handle hCandidateList,
                                           OUT cap_string* pstrMappedThingName) {
  return static_cast<MySchedulingPolicies*>(policies)->OnMapService(strServiceName, hCandidateList,
                                                                    pstrMappedThingName);
}

//----------------------------------------
// Scheduling Request
//----------------------------------------

cap_result SchedulingPolicies_OnScheduleScenarioCheck(void* policies, cap_string strScenarioName,
                                                      cap_bool* pbScheduled) {
  return static_cast<MySchedulingPolicies*>(policies)->OnScheduleScenarioCheck(strScenarioName, pbScheduled);
}
cap_result SchedulingPolicies_OnScheduleScenarioConfirm(void* policies, cap_string strScenarioName) {
  return static_cast<MySchedulingPolicies*>(policies)->OnScheduleScenarioConfirm(strScenarioName);
}
cap_result SchedulingPolicies_OnUpdateScenario(void* policies, cap_string strScenarioName, cap_bool* pbScheduled) {
  return static_cast<MySchedulingPolicies*>(policies)->OnUpdateScenario(strScenarioName, pbScheduled);
}
cap_result SchedulingPolicies_OnCancelScenario(void* policies, cap_string strScenarioName) {
  return static_cast<MySchedulingPolicies*>(policies)->OnCancelScenario(strScenarioName);
}
cap_result SchedulingPolicies_OnGlobalUpdate(void* policies, int i) {
  return static_cast<MySchedulingPolicies*>(policies)->OnGlobalUpdate(i);
}
cap_result SchedulingPolicies_OnSuperScheduleRequest(void* policies, SScheduleTask* pstScheduleTask,
                                                     cap_bool* pbScheduled) {
  return static_cast<MySchedulingPolicies*>(policies)->OnSuperScheduleRequest(pstScheduleTask, pbScheduled);
}
cap_result SchedulingPolicies_OnSuperCancelRequest(void* policies, cap_string strRequestKey) {
  return static_cast<MySchedulingPolicies*>(policies)->OnSuperCancelRequest(strRequestKey);
}

//----------------------------------------
// Device Status Change
//----------------------------------------

cap_result SchedulingPolicies_OnThingRegister(void* policies, cap_string strThingName) {
  return static_cast<MySchedulingPolicies*>(policies)->OnThingRegister(strThingName);
}
cap_result SchedulingPolicies_OnThingUnregister(void* policies, cap_string strThingName) {
  return static_cast<MySchedulingPolicies*>(policies)->OnThingUnregister(strThingName);
}
cap_result SchedulingPolicies_OnMiddlewareRegister(void* policies, cap_string strMiddlewareName) {
  return static_cast<MySchedulingPolicies*>(policies)->OnMiddlewareRegister(strMiddlewareName);
}
cap_result SchedulingPolicies_OnMiddlewareUnregister(void* policies, cap_string strMiddlewareName) {
  return static_cast<MySchedulingPolicies*>(policies)->OnMiddlewareUnregister(strMiddlewareName);
}

//----------------------------------------
// Execution Request
//----------------------------------------

cap_result SchedulingPolicies_OnServiceReady(void* policies, SRunTask* pstRunTask) {
  return static_cast<MySchedulingPolicies*>(policies)->OnServiceReady(pstRunTask);
}
cap_result SchedulingPolicies_OnServiceBusy(void* policies, SRunTask* pstRunTask) {
  return static_cast<MySchedulingPolicies*>(policies)->OnServiceBusy(pstRunTask);
}

cap_result SchedulingPolicies_OnSuperServiceReady(void* policies, SRunTask* pstRunTask) {
  return static_cast<MySchedulingPolicies*>(policies)->OnSuperServiceReady(pstRunTask);
}
cap_result SchedulingPolicies_OnSuperServiceBusy(void* policies, SRunTask* pstRunTask) {
  return static_cast<MySchedulingPolicies*>(policies)->OnSuperServiceBusy(pstRunTask);
}

cap_result SchedulingPolicies_OnSubServiceReady(void* policies, SRunTask* pstRunTask) {
  return static_cast<MySchedulingPolicies*>(policies)->OnSubServiceReady(pstRunTask);
}
cap_result SchedulingPolicies_OnSubServiceBusy(void* policies, SRunTask* pstRunTask) {
  return static_cast<MySchedulingPolicies*>(policies)->OnSubServiceBusy(pstRunTask);
}

//----------------------------------------
// Execution Result
//----------------------------------------

cap_result SchedulingPolicies_OnServiceSuccess(void* policies, SExecutionResult* pstExecutionResult) {
  return static_cast<MySchedulingPolicies*>(policies)->OnServiceSuccess(pstExecutionResult);
}
cap_result SchedulingPolicies_OnSuperServiceSuccess(void* policies, SExecutionResult* pstExecutionResult) {
  return static_cast<MySchedulingPolicies*>(policies)->OnSuperServiceSuccess(pstExecutionResult);
}
cap_result SchedulingPolicies_OnSubServiceSuccess(void* policies, SExecutionResult* pstExecutionResult) {
  return static_cast<MySchedulingPolicies*>(policies)->OnSubServiceSuccess(pstExecutionResult);
}

cap_result SchedulingPolicies_OnServiceError(void* policies, SExecutionResult* pstExecutionResult) {
  return static_cast<MySchedulingPolicies*>(policies)->OnServiceError(pstExecutionResult);
}
cap_result SchedulingPolicies_OnSuperServiceError(void* policies, SExecutionResult* pstExecutionResult) {
  return static_cast<MySchedulingPolicies*>(policies)->OnSuperServiceError(pstExecutionResult);
}
cap_result SchedulingPolicies_OnSubServiceError(void* policies, SExecutionResult* pstExecutionResult) {
  return static_cast<MySchedulingPolicies*>(policies)->OnSubServiceError(pstExecutionResult);
}

cap_result SchedulingPolicies_OnServiceTimeout(void* policies, cap_string strScenarioName, int nTry) {
  return static_cast<MySchedulingPolicies*>(policies)->OnServiceTimeout(strScenarioName, nTry);
}
cap_result SchedulingPolicies_OnSuperServiceTimeout(void* policies, cap_string strRequestKey, int nTry) {
  return static_cast<MySchedulingPolicies*>(policies)->OnSuperServiceTimeout(strRequestKey, nTry);
}
cap_result SchedulingPolicies_OnSubServiceTimeout(void* policies, cap_string strRequestKey, int nTry) {
  return static_cast<MySchedulingPolicies*>(policies)->OnSubServiceTimeout(strRequestKey, nTry);
}

//----------------------------------------
// Additional...
//----------------------------------------

cap_result SchedulingPolicies_OnSuperScheduleResult(void* policies, SScheduleResult* pstScheduleResult) {
  return static_cast<MySchedulingPolicies*>(policies)->OnSuperScheduleResult(pstScheduleResult);
}