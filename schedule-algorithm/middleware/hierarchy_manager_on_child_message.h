#ifndef HIERARCHYMANAGER_ON_CHILD_MESSAGE_H_
#define HIERARCHYMANAGER_ON_CHILD_MESSAGE_H_

#include "sop_common.h"

#ifdef __cplusplus
extern "C" {
#endif

CALLBACK cap_result on_hierarchy_manager_child_mqtt_message(cap_string strTopic,
                                          cap_handle hTopicItemList,
                                          char *pszPayload, int nPayloadLen,
                                          IN void *pUserData);

#ifdef __cplusplus
}
#endif

#endif  // HIERARCHYMANAGER_ON_CHILD_MESSAGE_H_