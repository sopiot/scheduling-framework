#ifndef SOP_PAYLOAD_UTILS_H_
#define SOP_PAYLOAD_UTILS_H_

#include "sop_common.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @mainpage SoPIoT Payload Formats
 *
 * Delete Scenario Payload:
 *  [ScenarioName#]
 *
 *
 */

/** Payload Parsers */

cap_result ParseSubScheduleRequestPayload(IN char *pszPayload,
                                          IN int nPayloadLen,
                                          OUT cap_string *pstrScenarioName,
                                          IN OUT EScheduleStatusType *penStatus,
                                          IN OUT int *pnPeriodMs,
                                          OUT cap_handle *phTagList);
cap_result ParseScheduleRequestPayload(IN char *pszPayload, IN int nPayloadLen,
                                       OUT cap_string *pstrScenarioName,
                                       IN OUT EScheduleStatusType *penStatus,
                                       IN OUT int *pnPeriodMs);

cap_result ParseScheduleRequestPayloadString(
    IN cap_string strPayload, OUT cap_string *pstrScenarioName,
    IN OUT EScheduleStatusType *penStatus, OUT int *pnPeriodMs);

cap_result ParseExecutionRequestPayload(IN char *pszPayload, IN int nPayloadLen,
                                        OUT cap_string *pstrScenarioName);

cap_result ParseExecutionRequestPayloadString(IN cap_string strPayload,
                                              OUT cap_string *pstrScenarioName);

cap_result GenerateScheduleRequestPayload(IN cap_string strScenarioName,
                                          IN int nPeriodMs,
                                          IN OUT cap_string strPayload);

#ifdef __cplusplus
}
#endif

#endif
