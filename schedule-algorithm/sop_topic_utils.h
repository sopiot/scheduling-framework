#ifndef SOP_TOPIC_UTILS_H_
#define SOP_TOPIC_UTILS_H_

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @mainpage SoPIoT Topic Formats
 *
 * SoPIoT Topic List
 *  - MT
 *    - MT/REGACK/[ThingName] ⇒ MT/RESULT/REGISTER/[ThingName]
 *    - MT/[FunctionName]/[ThingName] ⇒
 *      MT/EXECUTE/[MiddlewareName]/[ThingName]/[FunctionName]/[RequesterMWName]
 *    - MT/SCHEDULE/[MiddlewareName]/[SuperThingName]
 *      /[SuperFunctionName]/[RequesterMWName]
 *    - MT/RESULT/SCHEDULE/[MiddlewareName]/[ThingName]
 *      /[FunctionName]/[SuperThingName]
 *  - TM
 *    - TM/REGISTER/[ThingMame]
 *    - TM/UNREGISTER/[ThingName]
 *    - TM/ALIVE/[ThingName]
 *    - TM/RESULT/FUNCTION/[FunctionName]/[ThingName] ⇒
 *      MT/RESULT/SCHEDULE/[MiddlewareName]/[ThingName]/[FunctionName]/[SuperThingName]
 *    - TM/SCHEDULE/[MiddlewareName]/[ThingName]/[FunctionName]/[SuperThingName]
 *    - TM/RESULT/SCHEDULE/[MiddlewareName]/[SuperThingName]
 *      /[SuperFunctionName]/[RequesterMWName]
 *    - [ThingName]/[ValueName] ⇒ TM/VALUE_PUBLISH/[ValueName][ThingName]
 *    + TM/SN
 *      - TM/SN/REGISTER/VALUE/[ThingName]
 *      - TM/SN/REGISTER/VALUETAG/[ThingName]
 *      - TM/SN/REGISTER/FUNCTION/[ThingName]
 *      - TM/SN/REGISTER/FUNCTIONTAG/[ThingName]
 *      - TM/SN/REGISTER/ARGUMENT/[ThingName]
 *      - TM/SN/REGISTER/ALIVECYCLE/[ThingName]
 *      - TM/SN/REGISTER/FINISH/[ThingName]
 *  - EM
 *      - EM/ADD_SCENARIO/[ClientID]
 *      - EM/VERIFY_SCENARIO/[ClientID]
 *      - EM/DELETE_SCENARIO/[ClientID]
 *      - EM/RUN_SCENARIO/[ClientID]
 *      - EM/STOP_SCENARIO/[ClientID]
 *      - EM/UPDATE_SCENARIO/[ClientID]
 *      - EM/ADD_TAG/[ClientID]
 *      - EM/DELETE_TAG/[ClientID]
 *      - EM/SET_ACCESS/[ClientID]
 *      - EM/GET_TREE/[ClientID]
 *      - EM/REFRESH/[ClientID]
 *  - ME
 *      - ME/RESULT/ADD_SCENARIO/[ClientID]
 *      - ME/RESULT/VERIFY_SCENARIO/[ClientID]
 *      - ME/RESULT/DELETE_SCENARIO/[ClientID]
 *      - ME/RESULT/RUN_SCENARIO/[ClientID]
 *      - ME/RESULT/STOP_SCENARIO/[ClientID]
 *      - ME/RESULT/UPDATE_SCENARIO/[ClientID]
 *      - ME/RESULT/ADD_TAG/[ClientID]
 *      - ME/RESULT/DELETE_TAG/[ClientID]
 *      - ME/RESULT/SET_ACCESS/[ClientID]
 *      - ME/RESULT/GET_TREE/# ⇒ ME/RESULT/GET_TREE/[ClientID]
 *      - ME/RESULT/SERVICE_LIST/[ClientID] ⇒
 * ME/RESULT/SERVICE_LIST/[ClientID]
 *      - ME/RESULT/SCENARIO_LIST/[ClientID]
 *      - ME/NOTIFY/# ⇒ ME/NOTIFY_CHANGE/#
 *  - CP
 *      - CP/EXECUTE/[RequesterMWName] ⇒
 *        CP/EXECUTE/[MiddlewareName]/[ThingName]/[FunctionName]/[RequesterMWName]
 *      - CP/RESULT/FUNCTION/[RequesterMWId] ⇒
 *        CP/RESULT/EXECUTE/[MiddlewareName]/[ThingName]/[FunctionName]/[RequesterMWName]
 *      - CP/SERVICE_LIST/# ⇒ CP/SERVICE_LIST/#
 *      - CP/TRAVERSE/#
 *  - PC
 *      - PC/EXECUTE/[RequesterMWName] ⇒
 *        PC/EXECUTE/[MiddlewareName]/[ThingName]/[FunctionName]/[RequesterMWName]
 *      - PC/RESULT/FUNCTION/[RequesterMWName] ⇒
 *        PC/RESULT/EXECUTE/[MiddlewareName]/[SuperThingName]/[SuperFunctionName]/[RequesterMWName]
 *      - PC/SERVICE_LIST/# ⇒ PC/SERVICE_LIST/#
 *      - PC/TRAVERSE/#
 *  - MS
 *      - MS/RESULT/FUNCTION/[SuperThingName] ⇒
 *        MS/RESULT/EXECUTE/[MiddlewareName]/[ThingName]/[FunctionName]/[SuperThingName]
 *      - MS/RESULT/SERVICE_LIST/[SuperThingName] ⇒
 *        MS/RESULT/SERVICE_LIST/[SuperThingName]
 *  - SM
 *      - SM/EXECUTE/[SuperThingName] ⇒
 *        SM/EXECUTE/[MiddlewareName]/[ThingName]/[FunctionName][RequesterMWName]
 *      - SM/AVAILABILITY/[SuperThingName]
 *      - SM/REFRESH/[SuperThingName]
 *
 *
 * EM Topic: EM/[Category]/[ClientId]
 * Value Publish Topic: [ThingName]/[ValueName]
 * Execution Result Topic: TM/RESULT/FUNCTION/[FunctionName]/[ThingName]
 * Execution Request Topic: MT/[FunctionName]/[ThingName]
 * Service List Topic:
 *  - LOCAL
 *    - ME/RESULT/SERVICE_LIST/[RequesterId]
 *  - PARENT
 *    - CP/SERVICE_LIST
 *  - CHILD
 *    - PC/SERVICE_LIST
 */

#include "sop_common.h"

CALLBACK cap_result DestroyTopicList(IN int nOffset, IN void *pData,
                                     IN void *pUserData);

/** Converters **/

/**
 * @brief Convert a topic list to a topic string. \n
 * [Notice] strTopic should be allocated before calling this function.
 *
 * @param hTopicItemList a linked list that contains topic strings.
 * @param strTopic [out] converted string.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned -
 *          @ref ERR_CAP_INVALID_PARAM,
 *          @ref ERR_CAP_OUT_OF_MEMORY.
 */
cap_result TopicListToString(IN cap_handle hTopicItemList,
                             IN OUT cap_string strTopic);

/**
 * @brief Convert a topic string to a topic list. \n
 * [Notice] hTopicItemList should be allocated before calling this function.
 *
 * @param strTopic string to be converted.
 * @param hTopicItemList [out] a linked list that contains topic strings.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned -
 *          @ref ERR_CAP_INVALID_PARAM,
 *          @ref ERR_CAP_OUT_OF_MEMORY.
 */
cap_result TopicStringToList(IN cap_string strTopic,
                             IN OUT cap_handle hTopicItemList);

/** Topic Parsers **/

/**
 * @brief Retrieve a protocol from a topic. \n
 * [Notice] strProtocol not be freed because it just points the topic
 * list.
 *
 * @param hTopicItemList a linked list that contains topic strings.
 * @param pstrProtocol [out] string pointer that will contain the protocol.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_PARAM, @ref
 * ERR_CAP_OUT_OF_MEMORY.
 */
cap_result GetProtocolFromTopic(IN cap_handle hTopicItemList,
                                OUT cap_string *pstrProtocol);

cap_result GetProtocolFromTopicString(IN cap_string strTopic,
                                      OUT cap_string *pstrProtocol);

/**
 * @brief Retrieve a category from a topic. \n
 * [Notice] strCategory not be freed because it just points the topic
 * list.
 *
 * @param hTopicItemList a linked list that contains topic strings.
 * @param pstrCategory [out] string pointer that will contain the category.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_PARAM, @ref
 * ERR_CAP_OUT_OF_MEMORY.
 */
cap_result GetCategoryFromTopic(IN cap_handle hTopicItemList,
                                OUT cap_string *pstrCategory);

/**
 * @brief Retrieve a sub category from a topic. \n
 * [Notice] pstrSubCategory not be freed because it just points the topic
 * list.
 *
 * @param hTopicItemList a linked list that contains topic strings.
 * @param pstrSubCategory [out] string pointer that will contain the client id.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_PARAM, @ref
 * ERR_CAP_OUT_OF_MEMORY.
 */
cap_result GetSubCategoryFromTopic(IN cap_handle hTopicItemList,
                                   OUT cap_string *pstrSubCategory);

/**
 * @brief Retrieve a client id from a EM topic. \n
 * [Notice] strClientId should not be freed because it just points the topic
 * list.
 *
 * @param hTopicItemList a linked list that contains topic strings.
 * @param pstrClientId [out] string pointer that will contain the client id.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_PARAM, @ref
 * ERR_CAP_OUT_OF_MEMORY.
 */
cap_result GetClientIdFromEMTopic(IN cap_handle hTopicItemList,
                                  OUT cap_string *pstrClientId);

/**
 * @brief Parse a schedule request topic. \n
 *
 * @param hTopicItemList a linked list that contains topic strings.
 * @param pstrFunctionName [out] string pointer that will contain a function
 * name.
 * @param pstrThingName [out] string pointer that will contain a thing name.
 * @param pstrTargetMiddlewareName [out] string pointer that will contain a
 * target middleware name.
 * @param pstrRequesterName [out] string pointer that will contain a
 * requester super thing name.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_PARAM, @ref
 * ERR_CAP_OUT_OF_MEMORY.
 */
cap_result ParseScheduleRequestTopic(IN cap_handle hTopicItemList,
                                     OUT cap_string *pstrFunctionName,
                                     OUT cap_string *pstrThingName,
                                     OUT cap_string *pstrTargetMiddlewareName,
                                     OUT cap_string *pstrRequesterName);

/**
 * @brief Parse a request result topic. \n
 *
 * @param hTopicItemList a linked list that contains topic strings.
 * @param pstrFunctionName [out] string pointer that will contain a function
 * name.
 * @param pstrThingName [out] string pointer that will contain a thing name.
 * @param pstrTargetMiddlewareName [out] string pointer that will contain a
 * target middleware name.
 * @param pstrRequesterName [out] string pointer that will contain a
 * requester name.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_PARAM, @ref
 * ERR_CAP_OUT_OF_MEMORY.
 */
cap_result ParseRequestResultTopic(IN cap_handle hTopicItemList,
                                   OUT cap_string *pstrFunctionName,
                                   OUT cap_string *pstrThingName,
                                   OUT cap_string *pstrTargetMiddlewareName,
                                   OUT cap_string *pstrRequesterName);

/**
 * @brief Parse a request result topic string. \n
 * It will call @ref ParseRequestResultTopic internally.
 *
 * @param hTopicItemList a linked list that contains topic strings.
 * @param strSuperFunctionName [out] string that will contain a super
 * function name.
 * @param strSuperThingName [out] string that will contain a super
 * thing name.
 * @param strTargetMiddlewareName [out] pointer that will contain a
 * target middleware name.
 * @param strRequesterMiddlewareName [out] pointer that will contain a
 * requester middleware name.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_PARAM, @ref
 * ERR_CAP_OUT_OF_MEMORY.
 */
cap_result ParseRequestResultTopicString(
    IN cap_string strTopic, IN OUT cap_string strFunctionName,
    IN OUT cap_string strThingName, IN OUT cap_string strTargetMiddlewareName,
    IN OUT cap_string strRequesterName);

cap_result ParseExecutionRequestTopic(IN cap_handle hTopicItemList,
                                      OUT cap_string *pstrFunctionName,
                                      OUT cap_string *pstrThingName,
                                      OUT cap_string *pstrTargetMiddlewareName,
                                      OUT cap_string *pstrRequesterName);

cap_result ParseExecutionRequestTopicString(
    IN cap_string strTopic, IN OUT cap_string strFunctionName,
    IN OUT cap_string strThingName, IN OUT cap_string strTargetMiddlewareName,
    IN OUT cap_string strRequesterName);

/** Topic Generators **/

// Scenario Manager

cap_result GenerateVerifyScenarioResultTopic(IN cap_string strRequesterName,
                                             IN OUT cap_string strTopic);
cap_result GenerateAddScenarioResultTopic(IN cap_string strRequesterName,
                                          IN OUT cap_string strTopic);
cap_result GenerateDeleteScenarioResultTopic(IN cap_string strRequesterName,
                                             IN OUT cap_string strTopic);
cap_result GenerateRunScenarioResultTopic(IN cap_string strRequesterName,
                                          IN OUT cap_string strTopic);
cap_result GenerateStopScenarioResultTopic(IN cap_string strRequesterName,
                                           IN OUT cap_string strTopic);
cap_result GenerateScheduleScenarioResultTopic(IN cap_string strRequesterName,
                                               IN OUT cap_string strTopic);

// Thing Manager

cap_result GenerateRegisterResultTopic(IN cap_string strRequesterName,
                                       IN OUT cap_string strTopic);
cap_result GenerateUnregisterResultTopic(IN cap_string strRequesterName,
                                         IN OUT cap_string strTopic);
cap_result GenerateAddTagResultTopic(IN cap_string strRequesterName,
                                     IN OUT cap_string strTopic);
cap_result GenerateDeleteTagResultTopic(IN cap_string strRequesterName,
                                        IN OUT cap_string strTopic);
cap_result GenerateSetAccessResultTopic(IN cap_string strRequesterName,
                                        IN OUT cap_string strTopic);

/**
 * @brief Generate a value publish topic
 * \n Execution Result Topic:
 * TM/RESULT/FUNCTION/[FunctionName]/[ThingName]
 *
 * @param strThingName a string that contains thing name
 * @param strFunctionName a string that contains function name
 * @param strTopic [out] a string that contains the generated topic.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_PARAM, @ref
 * ERR_CAP_OUT_OF_MEMORY.
 */
cap_result GenerateValuePublishTopic(IN cap_string strThingName,
                                     IN cap_string FunctionName,
                                     IN OUT cap_string strTopic);

/**
 * @brief Generate a execution result topic \n
 *
 * @param strProtocol a string that contains protocol name
 * @param strFunctionName a string that contains function name
 * @param strThingName a string that contains thing name
 * @param strMiddlewareName a string that contains middleware name
 * @param strRequesterName a string that contains requester name
 * @param strTopic [out] a string that contains the generated topic.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_PARAM, @ref
 * ERR_CAP_OUT_OF_MEMORY.
 */
cap_result GenerateExecutionResultTopic(IN cap_string strProtocol,
                                        IN cap_string strFunctionName,
                                        IN cap_string strThingName,
                                        IN cap_string strMiddlewareName,
                                        IN cap_string strRequesterName,
                                        IN OUT cap_string strTopic);

/**
 * @brief Generate a execution request topic \n
 *
 * @param strProtocol a string that contains protocol name
 * @param strFunctionName a string that contains function name
 * @param strThingName a string that contains thing name
 * @param strMiddlewareName a string that contains middleware name
 * @param strRequesterName a string that contains requester name
 * @param strTopic [out] a string that contains the generated topic.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_PARAM, @ref
 * ERR_CAP_OUT_OF_MEMORY.
 */
cap_result GenerateExecutionRequestTopic(IN cap_string strProtocol,
                                         IN cap_string strFunctionName,
                                         IN cap_string strThingName,
                                         IN cap_string strMiddlewareName,
                                         IN cap_string strRequesterName,
                                         IN OUT cap_string strTopic);

/**
 * @brief Generate a schedule request topic \n
 *
 * @param strProtocol a string that contains protocol name
 * @param strTargetMiddlewareName a string that contains the target
 * middleware name
 * @param strTargetThingName a string that contains the target thing name
 * @param strTargetServiceName a string that contains the target servoce name
 * @param strRequesterMiddlewareName a string that contains the requester
 * middleware name
 * @param strTopic [out] a string that contains the generated topic.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_PARAM, @ref
 * ERR_CAP_OUT_OF_MEMORY.
 */
cap_result GenerateScheduleRequestTopic(
    IN cap_string strProtocol, IN cap_string strTargetMiddlewareName,
    IN cap_string strTargetThingName, IN cap_string strTargetServiceName,
    IN cap_string strRequesterMiddlewareName, IN OUT cap_string strTopic);

/**
 * @brief Generate a schedule result topic \n
 *
 * @param strProtocol a string that contains protocol name
 * @param strTargetServiceName a string that contains the target servoce name
 * @param strTargetThingName a string that contains the target thing name
 * @param strTargetMiddlewareName a string that contains the target
 * middleware name
 * @param strRequesterMiddlewareName a string that contains the requester
 * middleware name
 * @param strTopic [out] a string that contains the generated topic.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_PARAM, @ref
 * ERR_CAP_OUT_OF_MEMORY.
 */
cap_result GenerateScheduleResultTopic(IN cap_string strProtocol,
                                       IN cap_string strTargetServiceName,
                                       IN cap_string strTargetThingName,
                                       IN cap_string strTargetMiddlewareName,
                                       IN cap_string strRequesterName,
                                       IN OUT cap_string strTopic);

/**
 * @brief Generate a service list topic \n
 *
 * @param eDst a direction that indicates where to publish
 * @param strTopic [out] a string that contains the generated topic.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_PARAM, @ref
 * ERR_CAP_OUT_OF_MEMORY.
 */
cap_result GenerateServiceListTopic(IN EDestination eDst,
                                    IN OUT cap_string strTopic);

/**
 * @brief Generate a service list result topic \n
 *
 * @param strProtocol a string that contains protocol
 * @param strRequesterName a string that contains requester name
 * @param strTopic [out] a string that contains the generated topic.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_PARAM, @ref
 * ERR_CAP_OUT_OF_MEMORY.
 */
cap_result GenerateServiceListResultTopic(IN cap_string strProtocol,
                                          IN cap_string strRequesterName,
                                          IN OUT cap_string strTopic);

/**
 * @brief Generate a scenario list result topic \n
 *
 * @param strProtocol a string that contains protocol
 * @param strRequesterName a string that contains requester name
 * @param strTopic [out] a string that contains the generated topic.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_PARAM, @ref
 * ERR_CAP_OUT_OF_MEMORY.
 */
cap_result GenerateScenarioListResultTopic(IN cap_string strProtocol,
                                           IN cap_string strRequesterName,
                                           IN OUT cap_string strTopic);

#ifdef __cplusplus
}
#endif

#endif
