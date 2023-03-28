/*
 * CAPMath.h
 *
 *  Created on: 2017. 5. 31.
 *      Author: chjej202
 */

#ifndef CAPMATH_H_
#define CAPMATH_H_

#include <cap_common.h>

#ifdef __cplusplus
extern "C"
{
#endif

/**
 * @brief Find a prime number from @a nStartPoint to @a nStartPoint + @a nLength - 1.
 *
 * Find a prime number from @a nStartPoint to @a nStartPoint + @a nLength - 1. \n
 * The function returns the smallest prime number inside the range. \n
 * If the function cannot find a prime number, it returns @a nStartPoint + @a nLength .
 *
 * @param nStartPoint a start point to find a prime number
 * @param nLength a range to find search a prime number.
 *
 * @return This function returns the smallest prime number inside the range. \n
 *         If the prime number is not found, it returns @a nStartPoint + @a nLength .
 *
 */
int CAPMath_FindPrimeFromRange(int nStartPoint, int nLength);

#ifdef __cplusplus
}
#endif

#endif /* CAPMATH_H_ */
