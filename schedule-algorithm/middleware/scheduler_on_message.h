#include "CAPString.h"
#include "cap_common.h"

CALLBACK cap_result on_scheduler_parent_mqtt_message(cap_string strTopic,
                                                     cap_handle hTopicItemList,
                                                     char *pszPayload,
                                                     int nPayloadLen,
                                                     IN void *pUserData);

CALLBACK cap_result on_scheduler_child_mqtt_message(cap_string strTopic,
                                                    cap_handle hTopicItemList,
                                                    char *pszPayload,
                                                    int nPayloadLen,
                                                    IN void *pUserData);