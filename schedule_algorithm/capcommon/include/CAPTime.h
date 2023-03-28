/*
 * CAPTime.h
 *
 *  Created on: 2015. 8. 31.
 *      Author: chjej202
 */

#ifndef CAPTIME_H_
#define CAPTIME_H_

#include <cap_common.h>

#include <CAPString.h>

#ifdef __cplusplus
extern "C"
{
#endif

/**
 * @brief Get current linux time in milliseconds.
 *  
 * This function retrieves a current linux time in millisecond time unit.
 * This function can be used for time measurement.
 *
 * @param pllTime [out] current linux in milliseconds.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_PARAM, @ref ERR_CAP_INTERNAL_FAIL.
 */
cap_result CAPTime_GetCurTimeInMilliSeconds(long long *pllTime);

/**
 * @brief Get current tick value in milliseconds.
 *  
 * This function retrieves a current tick (uptime of a device) in millisecond time unit.
 * This function can be used for time measurement.
 *
 * @param pllTime [out] current tick in milliseconds.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_PARAM, @ref ERR_CAP_INTERNAL_FAIL.
 */
cap_result CAPTime_GetCurTickInMilliSeconds(long long *pllTime);


/**
 * @brief Sleep the current thread.
 *  
 * This function sleeps a current thread for a specific amount of time.
 *
 * @param nMillisec the amount of time to sleep in milliseconds.
 */
void CAPTime_Sleep(int nMillisec);


/** 
 * @brief Not implemented yet
 *  
 */
cap_result CAPTime_GetCurDateAndTimeInString(cap_string strDateAndTime);


/** 
 * @brief Not implemented yet
 *  
 */
cap_result CAPTime_GetCurDateInString(cap_string strDate);

#ifdef __cplusplus
}
#endif

#endif /* CAPTIME_H_ */
