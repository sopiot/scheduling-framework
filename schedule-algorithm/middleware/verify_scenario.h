#ifndef MIDDLEWARE_VERIFY_SCENARIO_H_
#define MIDDLEWARE_VERIFY_SCENARIO_H_

/**
 * @mainpage SoPIoT Scenario Verification
 *
 * Things to verify
 *  - Duplicated scenario name
 *  - VerifyConditionalStatement
 *    - Unsupported type is used on an operand
 *    - Boolean type and double type cannot be compared
 *    - String type only matches to string type
 *    - Irregular input is inserted
 *  - VerifyActionStatement
 *    - Function name is required for execution
 *    - Matched Function Not Found
 *    - Unknown thing.function
 *    - %s.%s does not support any argument
 *    - %s.%s has %d arguments
 *    - Unsupported type is used on the function param
 *    - Function %s's Argument %d type mismatch: expression type is
 *      '%s' but argument type is '%s'
 *    - %s.%s Multiple Return Type is not supported
 */

#include "CAPString.h"
#include "cap_common.h"

/**
 * @brief Verify a scenario text . \n
 *
 * @param strScenarioName string that will contain the scenario name.
 * @param strScenarioText string that will contain the scenario.
 * @param strError [out] error code of the verification.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_PARAM, @ref
 * ERR_CAP_OUT_OF_MEMORY.
 */
cap_result VerifyScenario(IN cap_string strScenarioName, IN cap_string strScenarioText,
                          IN OUT cap_string strError);

#endif  // MIDDLEWARE_VERIFY_SCENARIO_H_