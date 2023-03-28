#ifndef MIDDLEWARE_REQUESTING_THREAD_H_
#define MIDDLEWARE_REQUESTING_THREAD_H_

#include "CAPString.h"
#include "CAPThread.h"
#include "sop_common.h"

#ifdef __cplusplus
extern "C" {
#endif

// FIXME Refactor to unify with MQTTData
typedef struct _SMQTTMessage {
  cap_handle hTopicItemList;
  char *pszPayload;
  int nPayloadLen;
} SMQTTMessage;

// data used by the requesting thread
typedef struct _SRequestingThreadData {
  cap_string strRunTopic;
  cap_string strResultTopic;
  cap_string strReplyTopic;
  cap_string strRunPayload;
  cap_handle hRunMQTTHandler;
  cap_handle hReplyMQTTHandler;
} SRequestingThreadData;

cap_result MQTTMessage_Create(IN cap_handle hTopicItemList, IN char *pszPayload,
                              IN int nPayloadLen,
                              OUT SMQTTMessage **ppstMQTTMessage);
cap_result MQTTMessage_Destory(IN SMQTTMessage **ppstMQTTMessage);

cap_result RequestingThreadData_Create(
    OUT SRequestingThreadData **ppstRequestingThreadData);

cap_result RequestingThreadData_Destory(
    IN SRequestingThreadData **ppstRequestingThreadData);

cap_result HierarchyManager_RequestingThread_HandleResult(
    cap_handle hHierarchyManager, SMQTTMessage *pstMQTTMessage);

cap_result HierarchyManager_RequestingThread_Add(
    cap_handle hHierarchyManager, IN cap_string strKey,
    IN SRequestingThreadData *pstData);

cap_result HierarchyManager_RequestingThread_Delete(
    cap_handle hHierarchyManager, IN cap_string strKey);

cap_result HierarchyManager_RequestingThread_Run(
    cap_handle hHierarchyManager,
    IN SRequestingThreadData *pstRequestingThreadData);

#ifdef __cplusplus
}
#endif

#endif  // MIDDLEWARE_REQUESTING_THREAD_H_