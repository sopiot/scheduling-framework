#ifndef SOPIOT_UTILS_H_
#define SOPIOT_UTILS_H_

#include "AppScriptModeler.h"
#include "CAPString.h"
#include "thing_info_handler.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @mainpage SoPIoT Scenario Manager
 *
 * Describes keys that are used in SoPIoT
 *
 * Service identifier key:
 *    - [PrimaryIdentifier].[ServiceName]
 *    - used as a hash key when retrieving a value from the service runtime info
 * hash of ScenarioModel
 *    - value of the hash:
 *      - ServiceTyhpe
 *      - MappedThingNameList
 *
 * ValueCache Key:
 *    - [ThingName].[ServiceName]
 *    - used as a hash key when retrieving a value from the value cache.
 *    - value of the hash:
 *      - latest sensor value.
 *
 * Request Key
 *    - [ScenarioName]_[MiddlewareName(Ommitable)]_[ThingName]_[FunctionName]
 *    - used as a hash key when receiving the request result.
 *    - value of the hash:
 *      - ThreadEvent
 */

CALLBACK cap_result DestroyStringList(IN int nOffset, IN void *pData,
                                      IN void *pUserData);

CALLBACK cap_result DuplicateStringList(IN int nOffset, IN void *pDataSrc,
                                        IN void *pUserData,
                                        OUT void **ppDataDst);

CALLBACK cap_result PrintHashKey(IN cap_string strKey, IN void *pData,
                                 IN void *pUserData);

cap_result GetMacAddress(IN OUT char *pszMacAddress);

// Type Conversion

const char *MapExpressionTypeToString(EExpressionType enType);

EValueType MapExpressionTypeToValueType(EExpressionType enExpType);

EExpressionType MapValueTypeToExpressionType(EValueType enValueType);

EValueType ValueTypeStringToValueType(const char *pszString);

const char *ValueTypeToValueTypeString(EValueType enValueType);

// ServiceKey

cap_result GenerateServiceKey(IN cap_string strThingName,
                              IN cap_string strServiceName,
                              IN OUT cap_string strKey);

cap_result ParseServiceKey(IN cap_string strKey, OUT cap_string strThingName,
                           OUT cap_string strValueName);

// ScheduleKey

cap_result GenerateScheduleKey(IN cap_string strPrimaryIdentifier,
                               IN cap_string strServiceName,
                               IN OUT cap_string strKey);
/**
 * @brief Parse a service identifier key into a primary identifier and a service
 * name. \n [Notice] strPrimaryIdentifier should be allocated before use.
 * [Notice] strServiceName should be allocated before use.
 *
 * @param strScheduleKey a service identifier key that indicates the
 * target service.
 * @param strIdentifier [out] primary identifier of the key
 * @param strServiceName [out] service name of the key
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned -
 *          @ref ERR_CAP_INVALID_PARAM,
 *          @ref ERR_CAP_OUT_OF_MEMORY.
 */
cap_result ParseScheduleKey(IN cap_string strScheduleKey,
                            OUT cap_string *pstrIdentifier,
                            OUT cap_string *pstrServiceName);

// RequestKey

cap_result RequestKey_Create_FromMQTTMessage(IN cap_handle hTopicItemList,
                                             char *pszPayload, int nPayloadLen,
                                             OUT cap_string *pstrKey);

cap_result RequestKey_Create(IN cap_string strScenarioName,
                             IN cap_string strMiddlewareName,
                             IN cap_string strThingName,
                             IN cap_string strFunctionName,
                             IN cap_string strRequesterName,
                             OUT cap_string *strKey);

/**
 * @brief Parse a primary identifier
 *
 * This function parses a primary identifier into a range type and a tag
 * list.
 *
 * @param strPrimaryIdentifier a primary identifier string to parse.
 * @param penRangeType [out] range type of the primary identifier
 * @param hTagList [out] a list that contains tags of the primary identifier
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned -
 *          @ref ERR_CAP_INVALID_PARAM,
 *          @ref ERR_CAP_OUT_OF_MEMORY,
 *          @ref ERR_CAP_NOT_SUPPORTED.
 */
cap_result ParsePrimaryIdentifier(IN cap_string strPrimaryIdentifier,
                                  OUT ERangeType *penRangeType,
                                  IN OUT cap_handle hTagList);

// MQTT Initialization

typedef cap_result (*CbFnOnMessage)(cap_string strTopic,
                                    cap_handle hTopicItemList, char *pszPayload,
                                    int nPayloadLen, void *pUserData);

cap_result InitMqttMessageHandler(cap_handle hHandler, CbFnOnMessage on_message,
                                  void *pUserData, char **paszTopicList,
                                  int TopicNum);

#ifdef __cplusplus
}
#endif

#endif  // SOPIOT_UTILS_