#ifndef MY_SCHEDULE_POLICY_H_
#define MY_SCHEDULE_POLICY_H_

#include "schedule_policy.h"
#include "task.h"

#ifdef __cplusplus
extern "C" {
#endif

class MySchedulePolicy : public SchedulePolicy {
 public:
  MySchedulePolicy(void* middleware_name, void* service_table, void* scenario_table, void* schedule_table,
                   void* tmp_scenario_table, void* tmp_schedule_table, void* super_thing_request_hash, void* run_queue,
                   void* wait_queue, void* event_queue, void* schedule_queue, void* complete_queue,
                   void* parent_mqtt_handler, void* child_mqtt_handler);
  ~MySchedulePolicy();

  virtual cap_result OnMapService(cap_string strServiceName, cap_handle hCandidateList,
                                  OUT cap_string* pstrMappedThingName);

  virtual cap_result OnScheduleScenarioCheck(cap_string strScenarioName, cap_bool* pbScheduled);
  virtual cap_result OnScheduleScenarioConfirm(cap_string strScenarioName);
  virtual cap_result OnUpdateScenario(cap_string strScenarioName, cap_bool* pbScheduled);
  virtual cap_result OnCancelScenario(cap_string strScenarioName);
  virtual cap_result OnGlobalUpdate(int i);
  virtual cap_result OnScheduleSuperRequest(SScheduleTask* pstScheduleTask, cap_bool* pbScheduled);

  virtual cap_result OnThingRegister(cap_string strThingName);
  virtual cap_result OnThingUnregister(cap_string strThingName);
  virtual cap_result OnMiddlewareRegister(int i);
  virtual cap_result OnMiddlewareUnregister(int i);

  virtual cap_result OnSuperScheduleResult(SScheduleResult* pstScheduleResult);

  virtual cap_result OnServiceReady(int i);
  virtual cap_result OnServiceBusy(int i);
  virtual cap_result OnServiceSuccess(SExecutionResult* pstExecutionResult);
  virtual cap_result OnServiceError(SExecutionResult* pstExecutionResult);
  virtual cap_result OnServiceTimeout(cap_string strScenarioName, int nTry);

  virtual cap_result OnSuperServiceReady(int i);
  virtual cap_result OnSuperServiceBusy(int i);
  virtual cap_result OnSuperServiceSuccess(int i);
  virtual cap_result OnSuperServiceError(int i);
  virtual cap_result OnSuperServiceTimeout(int i);

  virtual cap_result OnSubServiceReady(int i);
  virtual cap_result OnSubServiceBusy(int i);
  virtual cap_result OnSubServiceSuccess(int i);
  virtual cap_result OnSubServiceError(int i);
  virtual cap_result OnSubServiceTimeout(int i);

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

#endif /* MY_SCHEDULE_POLICY_H_ */