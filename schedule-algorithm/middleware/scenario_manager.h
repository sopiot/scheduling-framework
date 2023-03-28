#ifndef SCENARIOMANAGER_H_
#define SCENARIOMANAGER_H_

/**
 * @mainpage SoPIoT Scenario Manager
 *
 * Supported Features:
 *     - Interaction with Clients Regarding Scenario Management Via MQTT
 *         - Verify, Add, Delete, Run, Stop, Update
 *
 **/

#include "CAPString.h"
#include "CAPThread.h"
#include "mqtt_utils.h"
#include "sop_common.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct _SScenarioManagerCallbackData {
  cap_string strPayload;
  cap_string strScenarioName;
  cap_string strScenarioText;
  cap_string strError;
} SScenarioManagerCallbackData;

typedef struct _SScenarioManager {
  ESoPHandleId enID;
  cap_bool bCreated;
  cap_handle hMQTTHandler;
  SScenarioManagerCallbackData* pstCallback;
  cap_handle hScheduler;         // ref
  cap_string strMiddlewareName;  // ref
} SScenarioManager;

cap_result ScenarioManager_Create(OUT cap_handle* phScenarioManager,
                                  IN cap_string strBrokerURI,
                                  IN cap_string strMiddlewareName);
cap_result ScenarioManager_Run(cap_handle hScenarioManager,
                               IN cap_handle hScheduler);
cap_result ScenarioManager_Join(cap_handle hScenarioManager);
cap_result ScenarioManager_Destroy(OUT cap_handle* phScenarioManager);

#ifdef __cplusplus
}
#endif

#endif
