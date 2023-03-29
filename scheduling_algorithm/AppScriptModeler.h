#ifndef APP_SCRIPTMODELER_H_
#define APP_SCRIPTMODELER_H_

#include <CAPHash.h>
#include <CAPKeyValue.h>
#include <CAPStack.h>
#include <CAPString.h>
#include <cap_common.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef enum _EServiceType {
  SERVICE_TYPE_UNKNOWN,
  SERVICE_TYPE_FUNCTION,
  SERVICE_TYPE_VALUE,
} EServiceType;

typedef enum _ECalleeLocation {
  CALLEE_NONE,      // Not a statement calling a function
  CALLEE_EXTERNAL,  // calling a function outside script
  CALLEE_INTERNAL,  // calling a function inside a team
} ECalleeLocation;

typedef enum _ERangeType {
  RANGE_TYPE_NONE,
  RANGE_TYPE_ALL,
  RANGE_TYPE_OR,
} ERangeType;

typedef enum _EStatementType {
  IF_STATEMENT,
  LOOP_STATEMENT,
  ACTION_STATEMENT,
  FINISH_STATEMENT,
  WAIT_UNTIL_STATEMENT,
  IF_END_STATEMENT,
  LOOP_END_STATEMENT,
} EStatementType;

typedef enum _ETimeUnit {
  TIME_UNIT_MSEC,
  TIME_UNIT_SEC,
  TIME_UNIT_MINUTE,
  TIME_UNIT_HOUR,
  TIME_UNIT_DAY,
} ETimeUnit;

typedef enum _EOperator {
  OPERATOR_NONE,
  OPERATOR_EQUAL,
  OPERATOR_GREATER,
  OPERATOR_LESS,
  OPERATOR_GREATER_EQUAL,
  OPERATOR_LESS_EQUAL,
  OPERATOR_NOT_EQUAL,
  OPERATOR_AND,
  OPERATOR_OR,
  OPERATOR_NOT,
  OPERATOR_LEFT_PARENTHESIS,
  OPERATOR_RIGHT_PARENTHESIS,
} EOperator;

typedef enum _EExpressionType {
  EXP_TYPE_VARIABLE,
  EXP_TYPE_STRING,
  EXP_TYPE_INTEGER,
  EXP_TYPE_DOUBLE,
  EXP_TYPE_BINARY,
  EXP_TYPE_VOID,
  EXP_TYPE_MEMBER_VARIABLE,
} EExpressionType;

typedef struct _SExpression {
  EExpressionType enType;
  cap_string strPrimaryIdentifier;
  cap_string strSubIdentifier;
  double dbValue;
  cap_string strStringValue;
} SExpression;

typedef struct _SCondition {
  SExpression *pstLeftOperand;
  EOperator enOperator;
  SExpression *pstRightOperand;
  cap_bool bConditionTrue;  // initially set to zero
  cap_bool bInit;  // this is for checking the condition data is dirty or not
} SCondition;

typedef struct _SPeriod {
  ETimeUnit enTimeUnit;
  double dbTimeVal;
} SPeriod;

// use this from loop, wait until, if
typedef struct _SConditionalStatement {
  SPeriod stPeriod;
  long long llNextTimeMs;  // Time to go to next statement
  cap_handle hConditionList;
} SConditionalStatement;

typedef struct _SExecutionStatement {
  SPeriod stPeriod;
  long long llProceedTimeMs;  // Time to go to next statement
  cap_handle hInputList;
  cap_handle hOutputList;
  cap_string strPrimaryIdentifier;  // General/First IDENTIFIER
  cap_string strSubIdentifier;      // Second part of IDENTIFIER.IDENTIFIER
  ECalleeLocation enCalleeType;
  int nWaitingResultNum;
} SExecutionStatement;

typedef struct _SExecutionNode SExecutionNode;

typedef struct _SExecutionNode {
  EStatementType enType;
  void *pstStatementData;  // SExecutionStatement or SConditionalStatement
  SExecutionNode *pstNextTrue;
  SExecutionNode *pstNextFalse;
  int nLineNo;
} SExecutionNode;

typedef struct _SExecutionGraph {
  void *pGraphHash;
  SExecutionNode *pstRoot;
} SExecutionGraph;

// typedef struct _SServiceScheduleInfo {
//   EServiceType enType;              // Function or Value
//   cap_handle hMappedThingNameList;  // schedule result will be kept here.
//   int nPeriodMs;                    // in milli seconds.
//   cap_bool bScheduled;              // scheduled or not yet.
//   SServiceInfo *pstServiceInfo;     // ref to a service info.
// } SServiceScheduleInfo;

typedef struct _SExecutionCall {
  cap_string strExecutionName;
  SExecutionNode *pstCurrent;
  SExecutionNode *pstRoot;
  cap_bool bUsed;
} SExecutionCall;

typedef struct _SExecutionPlan {
  cap_handle hCompositeServiceHash;
  cap_handle hCallStack;  // (Data: SExecutionCall)
} SExecutionPlan;

typedef struct _SScenario {
  cap_string strScenarioText;
  cap_string strScenarioName;
  SExecutionPlan *pstGlobalPlan;
  cap_handle hVariableHash;
  cap_bool bNotLoaded;  // initialize to FALSE
  cap_handle hExecutionNodeList;
  SExecutionNode *pstFinish;
  cap_handle hLock;
  cap_string strErrorString;
  cap_handle hScheduleKeyHash;
  cap_handle hCompositeServiceHash;  // (key: composite service name, Data:
                                     // execution node)
  cap_string strTempBuf;             // temporary buffer used internally
  int nPeriodMs;  // global period of this scenario in milli seconds
} SScenario;

typedef cap_result (*CbFnExecutionNodeTraverse)(int nIndex,
                                                SExecutionNode *pstNode,
                                                IN void *pUserData);
typedef cap_result (*CbFnTwoExecutionNodesTraverse)(
    int nIndex, SExecutionNode *pstFirstNode, SExecutionNode *pstSecondNode,
    IN void *pUserData);
typedef cap_result (*CbFnTeamTraverse)(int nIndex, cap_string strTeamName,
                                       IN void *pUserData);
typedef cap_result (*CbFnPlanTraverse)(int nIndex, cap_string strPlanName,
                                       IN void *pUserData);
typedef cap_result (*CbFnCompositeServiceTraverse)(
    int nIndex, cap_string strCompositeServiceName, IN void *pUserData);
typedef cap_result (*CbFnThingTraverse)(int nIndex, cap_string strClassName,
                                        cap_string strThingName, int nThingNum,
                                        IN void *pUserData);
typedef cap_result (*CbFnModeNodeTraverse)(int nIndex, cap_string strTeamName,
                                           cap_string strModeName,
                                           SExecutionNode *pstNode,
                                           IN void *pUserData);
typedef cap_result (*CbFnModeTraverse)(int nIndex, cap_string strTeamName,
                                       cap_string strModeName,
                                       IN void *pUserData);
typedef cap_result (*CbFnEventTraverse)(int nIndex, cap_string strTeamName,
                                        cap_string strModeName,
                                        cap_string strEventName,
                                        cap_string strDstModeName,
                                        IN void *pUserData);
typedef cap_result (*CbFnCompositeServiceNodeTraverse)(
    SExecutionNode *pstPrevNode, cap_bool bDirection,
    SExecutionNode *pstCurNode, int nDepth, cap_bool bShownBefore,
    IN void *pUserData);

/**
 * @brief Initialize AppScriptModeler.
 *
 * This function initializes AppScriptModeler. \n
 * To use AppScriptModeler with multiple threads with different handles, this
 * function must be called \n to resolve synchronization problem among threads.
 *
 * @warning This function must be called once when the program is started (such
 * as main function). \n Please call @ref AppScriptModeler_Finalize at the end
 * of program to free internal data.
 *
 * @return This function returns ERR_CAP_NOERROR if there is no error. \n
 *         If this function is called twice, ERR_CAP_ALREADY_DONE is returned.
 */
cap_result AppScriptModeler_Initialize();

/**
 * @brief Finalize AppScriptModeler.
 *
 * This function Finalizes AppScriptModeler.
 *
 * @warning This function must be called once when the program is going to be
 * terminated. \n This function is a pair of @ref AppScriptModeler_Initialize,
 * \n so you don't need to call this function when @ref
 * AppScriptModeler_Initialize is not used before.
 *
 * @return This function returns ERR_CAP_NOERROR if there is no error. \n
 *         If this function is called twice, ERR_CAP_ALREADY_DONE is returned.
 */
cap_result AppScriptModeler_Finalize();

/**
 * @brief Create an AppScriptModeler handle.
 *
 * This function creates an AppScriptModeler handle which deals with one script
 * text.
 *
 * @param phModel [out] an AppScriptModeler handle to be created.
 *
 * @warning Please free the memory with @ref AppScriptModeler_Destroy after
 * finishing the use of a handle.
 *
 * @return This function returns ERR_CAP_NOERROR if there is no error. \n
 *         Errors to be returned - ERR_CAP_INVALID_PARAM, ERR_CAP_OUT_OF_MEMORY,
 * \n ERR_CAP_MUTEX_ERROR.
 */
cap_result AppScriptModeler_Create(OUT cap_handle *phModel);

/**
 * @brief Parse a script text.
 *
 * This function parses a script text @a strText with script name @a
 * strScenarioName. \n All other functions except @ref AppScriptModeler_Destroy
 * can be used after calling this function.
 *
 * @param hModel an AppScriptModeler handle.
 * @param strScenarioName The name of a script.
 * @param strText a script text content.
 *
 * @return This function returns ERR_CAP_NOERROR if there is no error. \n
 *         Errors to be returned - ERR_CAP_INVALID_PARAM, ERR_CAP_OUT_OF_MEMORY,
 * \n ERR_CAP_MUTEX_ERROR, ERR_CAP_INVALID_DATA, ERR_CAP_DUPLICATED, \n
 *         ERR_CAP_INTERNAL_FAIL, ERR_CAP_NOT_FOUND, ERR_CAP_NOT_SUPPORTED.
 */
cap_result AppScriptModeler_Load(cap_handle hModel, cap_string strScenarioName,
                                 cap_string strText);

/**
 * @brief Get a script name.
 *
 * This function retrieves a script name. \n
 * A user must pass a created cap_string argument at @a strScenarioName to store
 * the name.
 *
 * @param hModel an AppScriptModeler handle.
 * @param strScenarioName [in/out] a script name to be retrieved.
 *
 * @return This function returns ERR_CAP_NOERROR if there is no error. \n
 *         Errors to be returned - ERR_CAP_INVALID_PARAM, ERR_CAP_OUT_OF_MEMORY,
 * \n ERR_CAP_NOT_INITIALIZED.
 */
cap_result AppScriptModeler_GetScenarioName(cap_handle hModel,
                                            IN OUT cap_string strScenarioName);

cap_result AppScriptModeler_GetScenarioText(cap_handle hModel,
                                            IN OUT cap_string strScenarioText);

/**
 * @brief Retrieves the current execution node.
 *
 * This function retrieves the current execution node in global scope of the
 * script \n pointed in an AppScriptModeler.
 *
 * @param hModel an AppScriptModeler handle.
 * @param ppstExecNode [out] the current execution node.
 *
 * @return This function returns ERR_CAP_NOERROR if there is no error. \n
 *         Errors to be returned - ERR_CAP_INVALID_PARAM,
 * ERR_CAP_NOT_INITIALIZED, ERR_CAP_NO_DATA.
 */
cap_result AppScriptModeler_GetCurrent(cap_handle hModel,
                                       OUT SExecutionNode **ppstExecNode);

/**
 * @brief Move a current node pointer to the next node.
 *
 * This function moves a current node pointer to the next node in global scope.
 * \n Next node is decided by @a bDirection (TRUE/FALSE). \n If the current node
 * is a finish statement or throw statement, the function returns
 * ERR_CAP_END_OF_DATA.
 *
 * @param hModel an AppScriptModeler handle.
 * @param bDirection the next node direction to be moved.
 * @param ppstExecNode [out] The next execution node.
 *
 * @return This function returns ERR_CAP_NOERROR if there is no error. \n
 *         Errors to be returned - ERR_CAP_INVALID_PARAM,
 * ERR_CAP_NOT_INITIALIZED, ERR_CAP_INVALID_DATA, ERR_CAP_END_OF_DATA,
 * ERR_CAP_NO_DATA.
 */
cap_result AppScriptModeler_MoveToNext(cap_handle hModel, cap_bool bDirection,
                                       OUT SExecutionNode **ppstExecNode);

/**
 * @brief Set the current execution node to the initial node.
 *
 * This function resets the current node to the initial node in global scope.
 *
 * @param hModel an AppScriptModeler handle.
 *
 * @return This function returns ERR_CAP_NOERROR if there is no error. \n
 *         Errors to be returned - ERR_CAP_INVALID_PARAM,
 * ERR_CAP_NOT_INITIALIZED, ERR_CAP_NO_DATA.
 */
cap_result AppScriptModeler_ClearExecution(cap_handle hModel);

/**
 * @brief Retrieves a ScheduleKey hash.
 *
 */
cap_result AppScriptModeler_GetScheduleKeyHash(
    cap_handle hModel, OUT cap_handle *phScheduleKeyHash);
/**
 * @brief Retrieves a variable hash.
 *
 * This function retrieves a hash which consists of a {variable name} as a key
 * and \n structure with Exrpession as a value. This function is used for
 * filling the internal thing data or verifying thing information.
 *
 * @param hModel an AppScriptModeler handle.
 * @param phVariableHash [out] a hash with a {variable name} as a key.
 *
 * @return This function returns ERR_CAP_NOERROR if there is no error. \n
 *         Errors to be returned - ERR_CAP_INVALID_PARAM,
 * ERR_CAP_NOT_INITIALIZED.
 */
cap_result AppScriptModeler_GetVariableHash(cap_handle hModel,
                                            OUT cap_handle *phVariableHash);

/**
 * @brief Retrieves the period value.
 *
 * @param hModel an AppScriptModeler handle.
 * @param pnPeriodMs [out] a number with a period value
 *
 * @return This function returns ERR_CAP_NOERROR if there is no error. \n
 *         Errors to be returned - ERR_CAP_INVALID_PARAM,
 * ERR_CAP_NOT_INITIALIZED.
 */
cap_result AppScriptModeler_GetPeriod(cap_handle hModel, OUT int *pnPeriodMs);

/**
 * @brief Traverse all execution nodes.
 *
 * This function traverses all execution node and provides a callback funtion
 * to check or verify each node.
 *
 * @param hModel an AppScriptModeler handle.
 * @param fnCallback a callback function.
 * @param pUserData user data which is passed to a callback function.
 *
 * @return This function returns ERR_CAP_NOERROR if there is no error. \n
 *         Errors to be returned - ERR_CAP_INVALID_PARAM,
 * ERR_CAP_NOT_INITIALIZED, ERR_CAP_INVALID_DATA.
 */
cap_result AppScriptModeler_TraverseExecutionNodeList(
    cap_handle hModel, IN CbFnExecutionNodeTraverse fnCallback,
    IN void *pUserData);

/**
 * @brief Traverse two execution node lists with same length.
 *
 * This function traverses all execution node and provides a callback funtion
 * to check or verify each node. This function access same index nodes in two
 * execution node list
 *
 * @param hFirstModel an AppScriptModeler handle.
 * @param hSecondModel an AppScriptModeler handle.
 * @param fnCallback a callback function.
 * @param pUserData user data which is passed to a callback function.
 *
 * @return This function returns ERR_CAP_NOERROR if there is no error. \n
 *         Errors to be returned - ERR_CAP_INVALID_PARAM,
 * ERR_CAP_NOT_INITIALIZED, ERR_CAP_INVALID_DATA.
 */
cap_result AppScriptModeler_TraverseTwoExecutionNodeLists(
    cap_handle hFirstModel, cap_handle hSecondModel,
    IN CbFnTwoExecutionNodesTraverse fnCallback, IN void *pUserData);

/**
 * @brief Get error string.
 *
 * This function retrieves an error string when the error is occurred during
 * parsing.
 *
 * @param hModel an AppScriptModeler handle.
 * @param strErrorInfo [in/out] an error string to be retrieved.
 *
 * @return This function returns ERR_CAP_NOERROR if there is no error. \n
 *         Errors to be returned - ERR_CAP_INVALID_PARAM,
 * ERR_CAP_OUT_OF_MEMORY.
 */
cap_result AppScriptModeler_GetErrorInfo(cap_handle hModel,
                                         IN OUT cap_string strErrorInfo);

/**
 * @brief Destroy an AppScriptModeler handle.
 *
 * This function destroys an AppScriptModeler handle.
 *
 * @param phModel an AppScriptModeler handle to be destroyed.
 *
 * @warning Please free the memory with @ref AppScriptModeler_Destroy after
 * finishing the use of a handle.
 *
 * @return This function returns ERR_CAP_NOERROR if there is no error. \n
 *         Errors to be returned - ERR_CAP_INVALID_PARAM.
 */
cap_result AppScriptModeler_Destroy(IN OUT cap_handle *phModel);

// get string of a statement type
const char *StatementTypeString(EStatementType type);

#ifdef __cplusplus
}
#endif

#endif /* APP_SCRIPTMODELER_H_ */
