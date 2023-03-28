#ifndef MIDDLEWARE_SCENARIO_RUNNER_RUN_H_
#define MIDDLEWARE_SCENARIO_RUNNER_RUN_H_

#include "AppScriptModeler.h"
#include "cap_common.h"
#include "scheduler.h"
#include "sop_common.h"
#include "thing_info_handler.h"

cap_result ScheduleUtils_AssignExecutionResult(
    cap_handle hVariableHash, cap_handle hOutputList,
    SExecutionResult *pstExecutionResult);
cap_result RunLoopStatement(SProceedData *pstData,
                            SConditionalStatement *pstCondStmt,
                            cap_bool *pbNextDirection);
cap_result RunIfStatement(SProceedData *pstData,
                          SConditionalStatement *pstCondStmt,
                          cap_bool *pbNextDirection);
cap_result RunWaitUntilStatement(SProceedData *pstData,
                                 SConditionalStatement *pstCondStmt,
                                 cap_bool *pbNextDirection);
cap_result RunActionStatement(SProceedData *pstData,
                              SExecutionStatement *pstExecStmt,
                              cap_bool *pbNextDirection);

// Utils
cap_result GetValueOfScheduledExpression_String(SProceedData *pstProceedData,
                                                cap_handle hVariableHash,
                                                SExpression *pstExpression,
                                                EValueType enType,
                                                cap_string strValue);
cap_result GetValueOfScheduledExpression_Double(SProceedData *pstProceedData,
                                                cap_handle hVariableHash,
                                                SExpression *pstExpression,
                                                double *pdbValue);
#endif  // MIDDLEWARE_SCENARIO_RUNNER_RUN_H_