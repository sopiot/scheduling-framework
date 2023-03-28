/*
 * CAPProcess.h
 *
 *  Created on: 2015. 8. 31.
 *      Author: chjej202
 */

#ifndef CAPPROCESS_H_
#define CAPPROCESS_H_

#include <cap_common.h>
#include <CAPString.h>

#ifdef __cplusplus
extern "C"
{
#endif

/** 
 * @brief Create a new process.
 *  
 * This function creates a new process.
 * To execute a process, @a strArgs needs to be set, \n
 * and the first argument should be executable file path.
 *
 * @param strArgs executable file path and arguments.
 * @param nArgNum the number of arguments including executable file path.
 * @param phProcess [out] a process handle.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_PARAM, @ref ERR_CAP_OUT_OF_MEMORY, \n
 *         @ref ERR_CAP_INTERNAL_FAIL.
 */
cap_result CAPProcess_Create(cap_string *strArgs, int nArgNum, OUT cap_handle *phProcess);


/** 
 * @brief Wait or check a child process is terminated.
 *  
 * This function waits or checks the child process termination depending on @a bBlocked. \n
 * If @a bBlocked is TRUE, the function is blocked inside until the child process is terminated. \n
 * Otherwise, the function only checks the child process is terminated or not. \n
 * If the child process is not terminated yet, the function will return @ref ERR_CAP_NO_CHANGE.
 *
 * @param hProcess a process handle.
 * @param bBlocked wait until child process termination or not.
 * @param pnExitCode [out] a process return code or signal number.
 *
 * @return @ref ERR_CAP_NOERROR is returned if the child process is terminated. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE,  @ref ERR_CAP_INVALID_PARAM, \n
 *         @ref ERR_CAP_INTERNAL_FAIL. \n
 *         @ref ERR_CAP_NO_CHANGE can be returned when @a bBlocked is FALSE and \n
 *         the child process is not terminated yet.
 */
cap_result CAPProcess_Wait(cap_handle hProcess, IN cap_bool bBlocked, OUT int *pnExitCode);


/** 
 * @brief Kill process.
 *  
 * This function forcely kills the process which is not termianted yet. \n
 * @ref CAPProcess_Wait is also need to be called after @ref CAPProcess_Kill.
 *
 * @param hProcess a process handle.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE,  @ref ERR_CAP_INTERNAL_FAIL.
 */
cap_result CAPProcess_Kill(cap_handle hProcess);


/** 
 * @brief Get process ID.
 *  
 * This function forcely retrieves child process ID.
 *
 * @param hProcess a process handle.
 * @param pnPid [out] a retrieved child process ID.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE,  @ref ERR_CAP_INVALID_PARAM.
 */
cap_result CAPProcess_GetProcessId(cap_handle hProcess, int *pnPid);


/** 
 * @brief Destroy process handle.
 *  
 * This function destroys process handle.
 * 
 * @warning Please call @ref CAPProcess_Wait, before calling this function.
 *
 * @param phProcess a process handle to be destroyed.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE,  @ref ERR_CAP_INVALID_PARAM.
 */
cap_result CAPProcess_Destroy(cap_handle *phProcess);


/** 
 * @brief Get current running process ID.
 *  
 * This function retrieves current running process ID.
 * 
 * @param pnPid [out] a retrieved current process ID.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_PARAM.
 */
cap_result CAPProcess_GetCurProcId(OUT int *pnPid);

#ifdef __cplusplus
}
#endif

#endif /* CAPPROCESS_H_ */
