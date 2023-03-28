/*
 * CAPThreadEvent.h
 *
 *  Created on: 2015. 5. 19.
 *      Author: chjej202
 */

#ifndef CAPTHREADEVENT_H_
#define CAPTHREADEVENT_H_

#include "cap_common.h"


#ifdef __cplusplus
extern "C"
{
#endif


/** 
 * @brief Create an event handle.
 *  
 * This function creates an event handle which can performs a synchronization between threads. \n
 * This event handle is basically working as a one-to-many(single event setter-multiple event handler) \n
 * thread synchronization. \n
 * The behavior is similar to SetEvent() and WaitForSingleObject() used in Windows. \n
 * If SetEvent is triggered before WaitForSingleObject is called, the event handler \n
 * which calls WaitForSingleObject does not blocked and handle the event.
 * 
 * @param phEvent [out] an event handle to be created.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_PARAM, @ref ERR_CAP_OUT_OF_MEMORY, \n
 *         @ref ERR_CAP_INTERNAL_FAIL.
 */
cap_result CAPThreadEvent_Create(OUT cap_handle *phEvent);


/** 
 * @brief Set an event.
 *  
 * This function sets an event which wakes up one of threads waiting event.
 * 
 * @param hEvent an event handle.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_MUTEX_ERROR.
 */
cap_result CAPThreadEvent_SetEvent(cap_handle hEvent);


/** 
 * @brief Wait an event.
 *  
 * This function waits an event. \n
 * A thread is blocked inside this function until an event is set.
 * 
 * @param hEvent an event handle.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_MUTEX_ERROR.
 */
cap_result CAPThreadEvent_WaitEvent(cap_handle hEvent);


/** 
 * @brief Wait an event with timeout.
 *  
 * This function waits an event. \n
 * A thread is blocked inside this function until \n
 * either an event is set or @a llSleepTimeMs milliseconds time is exceeded. \n
 * If the time is exceeded, this function returns @ref ERR_CAP_TIME_EXPIRED.
 * 
 * @param hEvent an event handle.
 * @param nSleepTime maximum time to be blocked.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_MUTEX_ERROR, \n
 *         @ref ERR_CAP_TIME_EXPIRED.
 *
 */
cap_result CAPThreadEvent_WaitTimeEvent(cap_handle hEvent, long long llSleepTimeMs);

/** 
 * @brief Destroy an event handle.
 *  
 * This function destorys an event handle.
 * 
 * @param phEvent an event handle to be destroyed.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_INVALID_PARAM, \n
 *         @ref ERR_CAP_MUTEX_ERROR.
 */
cap_result CAPThreadEvent_Destroy(IN OUT cap_handle *phEvent);

#ifdef __cplusplus
}
#endif


#endif /* CAPTHREADEVENT_H_ */
