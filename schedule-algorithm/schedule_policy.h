#ifndef SCHEDULE_POLICY_H_
#define SCHEDULE_POLICY_H_

#include <CAPQueue.h>
#include <CAPString.h>

#include "sop_common.h"
#include "task.h"

class SchedulePolicy {
 public:
  virtual cap_result OnMapService(cap_string strServiceName, cap_handle hCandidateList,
                                  OUT cap_string *pstrMappedThingName) = 0;
  virtual cap_result OnScheduleScenarioCheck(cap_string strScenarioName, cap_bool *pbScheduled) = 0;
  virtual cap_result OnScheduleScenarioConfirm(cap_string strScenarioName) = 0;
  virtual cap_result OnUpdateScenario(cap_string strScenarioName, cap_bool *pbScheduled) = 0;
  virtual cap_result OnCancelScenario(cap_string strScenarioName) = 0;
  virtual cap_result OnGlobalUpdate(int i) = 0;
  virtual cap_result OnScheduleSuperRequest(SScheduleTask *pstScheduleTask, cap_bool *pbScheduled) = 0;
  virtual cap_result OnThingRegister(cap_string strThingName) = 0;
  virtual cap_result OnThingUnregister(cap_string strThingName) = 0;
  virtual cap_result OnMiddlewareRegister(int i) = 0;
  virtual cap_result OnMiddlewareUnregister(int i) = 0;

  virtual cap_result OnServiceReady(int i) = 0;
  virtual cap_result OnServiceBusy(int i) = 0;
  virtual cap_result OnServiceSuccess(SExecutionResult *pstExecutionResult) = 0;
  virtual cap_result OnServiceError(SExecutionResult* pstExecutionResult) = 0;
  virtual cap_result OnServiceTimeout(cap_string strScenarioName, int nTry) = 0;

  virtual cap_result OnSuperServiceReady(int i) = 0;
  virtual cap_result OnSuperServiceBusy(int i) = 0;
  virtual cap_result OnSuperServiceSuccess(int i) = 0;
  virtual cap_result OnSuperServiceError(int i) = 0;
  virtual cap_result OnSuperServiceTimeout(int i) = 0;

  virtual cap_result OnSubServiceReady(int i) = 0;
  virtual cap_result OnSubServiceBusy(int i) = 0;
  virtual cap_result OnSubServiceSuccess(int i) = 0;
  virtual cap_result OnSubServiceError(int i) = 0;
  virtual cap_result OnSubServiceTimeout(int i) = 0;
};

#endif /* SCHEDULE_POLICY_H_ */