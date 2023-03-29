#ifndef MY_SCHEDULING_POLICIES_H_
#define MY_SCHEDULING_POLICIES_H_

#include "scheduling_policies.h"
#include "task.h"

#ifdef __cplusplus
extern "C" {
#endif

class MySchedulingPolicies : public SchedulingPolicies {
 public:
  MySchedulingPolicies(void *middleware_name, void *service_table, void *scenario_table, void *schedule_table,
                       void *tmp_scenario_table, void *tmp_schedule_table, void *super_thing_request_hash,
                       void *run_queue, void *wait_queue, void *event_queue, void *schedule_queue, void *complete_queue,
                       void *parent_mqtt_handler, void *child_mqtt_handler);
  ~MySchedulingPolicies();

  //----------------------------------------
  // Mapping Algorithm
  //----------------------------------------

  virtual cap_result OnMapService(cap_string strServiceName, cap_handle hCandidateList,
                                  OUT cap_string *pstrMappedThingName);

  //----------------------------------------
  // Scheduling Request
  //----------------------------------------

  virtual cap_result OnScheduleScenarioCheck(cap_string strScenarioName, cap_bool *pbScheduled);
  virtual cap_result OnScheduleScenarioConfirm(cap_string strScenarioName);
  virtual cap_result OnUpdateScenario(cap_string strScenarioName, cap_bool *pbScheduled);
  virtual cap_result OnCancelScenario(cap_string strScenarioName);
  virtual cap_result OnGlobalUpdate(int i);
  virtual cap_result OnSuperScheduleRequest(SScheduleTask *pstScheduleTask, cap_bool *pbScheduled);
  virtual cap_result OnSuperCancelRequest(cap_string strRequestKey);

  //----------------------------------------
  // Device Status Change
  //----------------------------------------

  virtual cap_result OnThingRegister(cap_string strThingName);
  virtual cap_result OnThingUnregister(cap_string strThingName);
  virtual cap_result OnMiddlewareRegister(cap_string strMiddlewareName);
  virtual cap_result OnMiddlewareUnregister(cap_string strMiddlewareName);

  //----------------------------------------
  // Execution Request
  //----------------------------------------

  virtual cap_result OnServiceReady(SRunTask *pstRunTask);
  virtual cap_result OnServiceBusy(SRunTask *pstRunTask);

  virtual cap_result OnSuperServiceReady(SRunTask *pstRunTask);
  virtual cap_result OnSuperServiceBusy(SRunTask *pstRunTask);

  virtual cap_result OnSubServiceReady(SRunTask *pstRunTask);
  virtual cap_result OnSubServiceBusy(SRunTask *pstRunTask);

  //----------------------------------------
  // Execution Result
  //----------------------------------------

  virtual cap_result OnServiceSuccess(SExecutionResult *pstExecutionResult);
  virtual cap_result OnSuperServiceSuccess(SExecutionResult *pstExecutionResult);
  virtual cap_result OnSubServiceSuccess(SExecutionResult *pstExecutionResult);

  virtual cap_result OnServiceError(SExecutionResult *pstExecutionResult);
  virtual cap_result OnSuperServiceError(SExecutionResult *pstExecutionResult);
  virtual cap_result OnSubServiceError(SExecutionResult *pstExecutionResult);

  virtual cap_result OnServiceTimeout(cap_string strScenarioName, int nTry);
  virtual cap_result OnSuperServiceTimeout(cap_string strRequestKey, int nTry);
  virtual cap_result OnSubServiceTimeout(cap_string strRequestKey, int nTry);

  //----------------------------------------
  // Utils...
  //----------------------------------------

  cap_result OnSuperScheduleResult(SScheduleResult *pstScheduleResult);

  //----------------------------------------
  // Member Variables
  //----------------------------------------

  cap_string strMiddlewareName_;
  cap_handle hServiceTable_;
  cap_handle hScenarioTable_;
  cap_handle hScheduleTable_;
  cap_handle hTempScenarioTable_;
  cap_handle hTempScheduleTable_;
  cap_handle hSuperThingRequestHash_;
  cap_handle hRunQueue_;
  cap_handle hWaitQueue_;
  cap_handle hEventQueue_;
  cap_handle hScheduleQueue_;
  cap_handle hCompleteQueue_;
  cap_handle hParentMQTTHandler_;
  cap_handle hChildMQTTHandler_;
};

#ifdef __cplusplus
}
#endif

#endif /* MY_SCHEDULING_POLICIES_H_ */