#ifndef SCHEDULING_POLICIES_H_
#define SCHEDULING_POLICIES_H_

#include <CAPQueue.h>
#include <CAPString.h>

#include "sop_common.h"
#include "task.h"

class SchedulingPolicies {
 public:
  //----------------------------------------
  // Mapping Algorithm
  //----------------------------------------

  virtual cap_result OnMapService(cap_string strServiceName, cap_handle hCandidateList,
                                  OUT cap_string *pstrMappedThingName) = 0;

  //----------------------------------------
  // Scheduling Request
  //----------------------------------------

  virtual cap_result OnScheduleScenarioCheck(cap_string strScenarioName, cap_bool *pbScheduled) = 0;
  virtual cap_result OnScheduleScenarioConfirm(cap_string strScenarioName) = 0;
  virtual cap_result OnUpdateScenario(cap_string strScenarioName, cap_bool *pbScheduled) = 0;
  virtual cap_result OnCancelScenario(cap_string strScenarioName) = 0;
  virtual cap_result OnGlobalUpdate(int i) = 0;
  virtual cap_result OnSuperScheduleRequest(SScheduleTask *pstScheduleTask, cap_bool *pbScheduled) = 0;
  virtual cap_result OnSuperCancelRequest(cap_string strRequestKey) = 0;

  //----------------------------------------
  // Device Status Change
  //----------------------------------------

  virtual cap_result OnThingRegister(cap_string strThingName) = 0;
  virtual cap_result OnThingUnregister(cap_string strThingName) = 0;
  virtual cap_result OnMiddlewareRegister(cap_string strMiddlewareName) = 0;
  virtual cap_result OnMiddlewareUnregister(cap_string strMiddlewareName) = 0;

  //----------------------------------------
  // Execution Request
  //----------------------------------------

  virtual cap_result OnServiceReady(SRunTask *pstRunTask) = 0;
  virtual cap_result OnServiceBusy(SRunTask *pstRunTask) = 0;

  virtual cap_result OnSuperServiceReady(SRunTask *pstRunTask) = 0;
  virtual cap_result OnSuperServiceBusy(SRunTask *pstRunTask) = 0;

  virtual cap_result OnSubServiceReady(SRunTask *pstRunTask) = 0;
  virtual cap_result OnSubServiceBusy(SRunTask *pstRunTask) = 0;

  //----------------------------------------
  // Execution Result
  //----------------------------------------

  virtual cap_result OnServiceSuccess(SExecutionResult *pstExecutionResult) = 0;
  virtual cap_result OnSuperServiceSuccess(SExecutionResult *pstExecutionResult) = 0;
  virtual cap_result OnSubServiceSuccess(SExecutionResult *pstExecutionResult) = 0;

  virtual cap_result OnServiceError(SExecutionResult *pstExecutionResult) = 0;
  virtual cap_result OnSuperServiceError(SExecutionResult *pstExecutionResult) = 0;
  virtual cap_result OnSubServiceError(SExecutionResult *pstExecutionResult) = 0;

  virtual cap_result OnServiceTimeout(cap_string strScenarioName, int nTry) = 0;
  virtual cap_result OnSuperServiceTimeout(cap_string strRequestKey, int nTry) = 0;
  virtual cap_result OnSubServiceTimeout(cap_string strRequestKey, int nTry) = 0;
};

#endif /* SCHEDULING_POLICIES_H_ */