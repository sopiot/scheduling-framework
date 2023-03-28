#ifndef _MqttMessageHandler_H_
#define _MqttMessageHandler_H_

#include "CAPString.h"
#include "MQTTClient.h"
#include "sop_common.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef cap_result (*CbFnMQTTHandler)(cap_string strTopic,
                                      cap_handle hTopicItemList,
                                      char *pszPayload, int nPayloadLen,
                                      IN void *pUserData);

typedef struct _SMqttMessageHandler {
  ESoPHandleId enID;
  MQTTClient hClient;
  cap_handle hMQTTMessageQueue;
  cap_handle hMQTTMessageHandlingThread;
  volatile MQTTClient_deliveryToken nDeliveredToken;
  CbFnMQTTHandler fnCallback;
  void *pUserData;
  cap_handle hSubscriptionList;
  cap_bool bConnected;
  cap_handle hLock;
  int nPublishWaitTime;
} SMqttMessageHandler;

cap_result MqttMessageHandler_Create(cap_string strBrokerURI,
                                     cap_string strClientID,
                                     int nPublishWaitTime,
                                     OUT cap_handle *phHandler);
cap_result MqttMessageHandler_SetReceiveCallback(
    cap_handle hHandler, CbFnMQTTHandler fnCbMessageArrive, void *pUserData);
cap_result MqttMessageHandler_Connect(cap_handle hHandler);
cap_result MqttMessageHandler_Disconnect(cap_handle hHandler);
cap_result MqttMessageHandler_Publish(cap_handle hHandler, cap_string strTopic,
                                      char *pszPayload, int nPayloadLen);
cap_result MqttMessageHandler_Subscribe(cap_handle hHandler,
                                        cap_string strTopic);
cap_result MqttMessageHandler_SubscribeMany(cap_handle hHandler,
                                            char *const *paszTopicArray,
                                            int nTopicNum);
cap_result MqttMessageHandler_Unsubscribe(cap_handle hHandler,
                                          cap_string strTopic);
cap_result MqttMessageHandler_Destroy(IN OUT cap_handle *phHandler);

#ifdef __cplusplus
}
#endif

#endif /* _MqttMessageHandler_H_ */
