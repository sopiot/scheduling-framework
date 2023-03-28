#include "schedule_policy_wrapper.h"

#include "my_schedule_policy.h"
#include "scheduler.h"

void* SchedulePolicy_Create(void* scheduler) {
  SScheduler* pstScheduler = (SScheduler*)scheduler;

  return new MySchedulePolicy(pstScheduler->strMiddlewareName, pstScheduler->hServiceTable,
                              pstScheduler->hScenarioTable, pstScheduler->hScheduleTable,
                              pstScheduler->hTempScenarioTable, pstScheduler->hTempScheduleTable,
                              pstScheduler->hSuperThingRequestHash, pstScheduler->hRunQueue, pstScheduler->hWaitQueue,
                              pstScheduler->hEventQueue, pstScheduler->hScheduleQueue, pstScheduler->hCompleteQueue,
                              pstScheduler->hParentMQTTHandler, pstScheduler->hChildMQTTHandler);
}
void SchedulePolicy_Destroy(void* policy) { delete static_cast<MySchedulePolicy*>(policy); }

cap_result SchedulePolicy_OnScheduleScenarioCheck(void* policy, cap_string strScenarioName, cap_bool* pbScheduled) {
  return static_cast<MySchedulePolicy*>(policy)->OnScheduleScenarioCheck(strScenarioName, pbScheduled);
}
cap_result SchedulePolicy_OnScheduleScenarioConfirm(void* policy, cap_string strScenarioName) {
  return static_cast<MySchedulePolicy*>(policy)->OnScheduleScenarioConfirm(strScenarioName);
}

cap_result SchedulePolicy_OnUpdateScenario(void* policy, cap_string strScenarioName, cap_bool* pbScheduled) {
  return static_cast<MySchedulePolicy*>(policy)->OnUpdateScenario(strScenarioName, pbScheduled);
}

cap_result SchedulePolicy_OnCancelScenario(void* policy, cap_string strScenarioName) {
  return static_cast<MySchedulePolicy*>(policy)->OnCancelScenario(strScenarioName);
}

cap_result SchedulePolicy_OnGlobalUpdate(void* policy, int i) {
  return static_cast<MySchedulePolicy*>(policy)->OnGlobalUpdate(i);
}

cap_result SchedulePolicy_OnScheduleSuperRequest(void* policy, SScheduleTask* pstScheduleTask, cap_bool* pbScheduled) {
  return static_cast<MySchedulePolicy*>(policy)->OnScheduleSuperRequest(pstScheduleTask, pbScheduled);
}

cap_result SchedulePolicy_OnThingRegister(void* policy, cap_string strThingName) {
  return static_cast<MySchedulePolicy*>(policy)->OnThingRegister(strThingName);
}
cap_result SchedulePolicy_OnThingUnregister(void* policy, cap_string strThingName) {
  return static_cast<MySchedulePolicy*>(policy)->OnThingUnregister(strThingName);
}
cap_result SchedulePolicy_OnMiddlewareRegister(void* policy, int i) {
  return static_cast<MySchedulePolicy*>(policy)->OnMiddlewareRegister(i);
}
cap_result SchedulePolicy_OnMiddlewareUnregister(void* policy, int i) {
  return static_cast<MySchedulePolicy*>(policy)->OnMiddlewareUnregister(i);
}

cap_result SchedulePolicy_OnSuperScheduleResult(void* policy, SScheduleResult* pstScheduleResult) {
  return static_cast<MySchedulePolicy*>(policy)->OnSuperScheduleResult(pstScheduleResult);
}

cap_result SchedulePolicy_OnServiceReady(void* policy, int i) {
  return static_cast<MySchedulePolicy*>(policy)->OnServiceReady(i);
}
cap_result SchedulePolicy_OnServiceBusy(void* policy, int i) {
  return static_cast<MySchedulePolicy*>(policy)->OnServiceBusy(i);
}
cap_result SchedulePolicy_OnServiceSuccess(void* policy, SExecutionResult* pstExecutionResult) {
  return static_cast<MySchedulePolicy*>(policy)->OnServiceSuccess(pstExecutionResult);
}
cap_result SchedulePolicy_OnServiceError(void* policy, SExecutionResult* pstExecutionResult) {
  return static_cast<MySchedulePolicy*>(policy)->OnServiceError(pstExecutionResult);
}
cap_result SchedulePolicy_OnServiceTimeout(void* policy, cap_string strScenarioName, int nTry) {
  return static_cast<MySchedulePolicy*>(policy)->OnServiceTimeout(strScenarioName, nTry);
}

cap_result SchedulePolicy_OnSuperServiceReady(void* policy, int i) {
  return static_cast<MySchedulePolicy*>(policy)->OnSuperServiceReady(i);
}
cap_result SchedulePolicy_OnSuperServiceBusy(void* policy, int i) {
  return static_cast<MySchedulePolicy*>(policy)->OnSuperServiceBusy(i);
}
cap_result SchedulePolicy_OnSuperServiceSuccess(void* policy, int i) {
  return static_cast<MySchedulePolicy*>(policy)->OnSuperServiceSuccess(i);
}
cap_result SchedulePolicy_OnSuperServiceError(void* policy, int i) {
  return static_cast<MySchedulePolicy*>(policy)->OnSuperServiceError(i);
}
cap_result SchedulePolicy_OnSuperServiceTimeout(void* policy, int i) {
  return static_cast<MySchedulePolicy*>(policy)->OnSuperServiceTimeout(i);
}

cap_result SchedulePolicy_OnSubServiceReady(void* policy, int i) {
  return static_cast<MySchedulePolicy*>(policy)->OnSubServiceReady(i);
}
cap_result SchedulePolicy_OnSubServiceBusy(void* policy, int i) {
  return static_cast<MySchedulePolicy*>(policy)->OnSubServiceBusy(i);
}
cap_result SchedulePolicy_OnSubServiceSuccess(void* policy, int i) {
  return static_cast<MySchedulePolicy*>(policy)->OnSubServiceSuccess(i);
}
cap_result SchedulePolicy_OnSubServiceError(void* policy, int i) {
  return static_cast<MySchedulePolicy*>(policy)->OnSubServiceError(i);
}
cap_result SchedulePolicy_OnSubServiceTimeout(void* policy, int i) {
  return static_cast<MySchedulePolicy*>(policy)->OnSubServiceTimeout(i);
}