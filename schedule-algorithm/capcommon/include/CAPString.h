/*
 * CAPString.h
 *
 *  Created on: 2015. 4. 2.
 *      Author: chjej202
 */

#ifndef CAPSTRING_H_
#define CAPSTRING_H_

#include <stdarg.h>
#include <cap_common.h>

//typedef signed char *cap_string;

#ifdef __cplusplus
extern "C"
{
#endif

typedef struct _SCAPString {
	char *pszStr;
	int nStringLen;
	int nBufferLen;
} *cap_string;


/** 
 * @brief Create cap_string.
 *  
 * This function creates cap_string which is an alternative to string-buffer
 * char * in C. \n
 * cap_string internally manages string length information to prevent string 
 * buffer overflow.
 *
 * @warning Please free the memory with @ref CAPString_Delete or @ref SAFE_CAPSTRING_DELETE \n
 *          after finishing the use of each cap_string.
 *
 * @return This function returns cap_string. \n
 *         If an error occurs, it will return NULL.
 */
cap_string CAPString_New();


/** 
 * @brief Destroy cap_string.
 *  
 * This function destroys cap_string which is created by @ref CAPString_New. \n
 * Instead of using this function, use @ref SAFE_CAPSTRING_DELETE \n
 * which also checks the pointer before delete and sets pointer to NULL after delete.
 *
 * @param pString a pointer to cap_string which is going to be freed.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - ERR_CAP_INVALID_HANDLE.
 * 
 */
cap_result CAPString_Delete(cap_string *pString);


/** 
 * @brief Set cap_string.
 *  
 * This function sets cap_string @a strSrc to cap_string @a strDst.
 *
 * @param strDst a destination string to be set.
 * @param strSrc a source string to be copied.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_OUT_OF_MEMORY.
 */
cap_result CAPString_Set(cap_string strDst, cap_string strSrc);


/** 
 * @brief Set cap_string from char *.
 *  
 * This function sets the string from char * to cap_string @a strDst. \n
 * The function can figure out NULL terminator in the buffer, and \n
 * only copies the characters before the NULL terminator. \n
 * If there is no NULL terminator in the string, this function will \n
 * copy the whole buffer.
 *
 * @param strDst a destination string to be set.
 * @param pszSrc a buffer which stores source string.
 * @param nSrcBufLen the size of source buffer.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_OUT_OF_MEMORY.
 */
cap_result CAPString_SetLow(cap_string strDst, const char *pszSrc, int nSrcBufLen);


/**
 * @brief Set cap_string from the part of cap_string.
 *  
 * This function copies the part of @a strSrc to @a strDst. \n
 * It copies the string from @a nSrcIndex and copied @a nSrcLen amount of string.
 *
 * @param strDst a destination string to be set.
 * @param strSrc a source string which contains the piece of string to be copied.
 * @param nSrcIndex a start index of the string to be copied.
 * @param nSrcLen the length of the string to be copied.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_OUT_OF_MEMORY.
 */
cap_result CAPString_SetSub(cap_string strDst, cap_string strSrc, int nSrcIndex, int nSrcLen);


/** 
 * @brief Remove whitespaces from the head and tail of the string.
 *  
 * This function trims a string. The function will remove whitespaces located before \n
 * the first character and after the last character of the string. \n
 * It uses isspace() function to check whitespace characters.
 * 
 * @param strTarget a string to be trimmed.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE.
 */
cap_result CAPString_Trim(cap_string strTarget);


/** 
 * @brief Set length of the string.
 *  
 * This function sets length of the string. \n
 * If the string length is less than @a nLength, the string will be shrunk. \n
 * If the string length is greater than @a nLength, the content \n
 * after the existed string will be filled with space (' ', 0x20 in hex value).
 * 
 * @param strTarget a target string to change the string length.
 * @param nLength string length to be set.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_OUT_OF_MEMORY.
 */
cap_result CAPString_SetLength(cap_string strTarget, int nLength);


/** 
 * @brief Append cap_string to cap_string.
 *  
 * This function appends @a strSrc cap_string to @a strDst cap_string.
 * 
 * @param strDst a destination string to be appended
 * @param strSrc a source string to append
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_OUT_OF_MEMORY.
 */
cap_result CAPString_AppendString(cap_string strDst, cap_string strSrc);


/** 
 * @brief Append cap_string to cap_string.
 *  
 * This function appends @a strSrc cap_string to @a strDst cap_string. \n
 * It appends the string from @a nSrcIndex and copied @a nSrcLen amount of string.
 * 
 * @param strDst a destination string to be appended
 * @param strSrc a source string to append
 * @param nSrcIndex a start index of the string to be copied.
 * @param nSrcLen the length of the string to be copied.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_OUT_OF_MEMORY.
 */
cap_result CAPString_AppendStringSub(cap_string strDst, cap_string strSrc, int nSrcIndex, int nSrcLen);


/**
 * @brief Append single char to cap_string. 
 *  
 * This function appends single character @a ch to @a strDst cap_string.
 * 
 * @param strDst a destination string to be appended
 * @param ch a single character to append
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_OUT_OF_MEMORY.
 */
cap_result CAPString_AppendChar(cap_string strDst, char ch);


/** 
 * @brief Append a pointer to char to cap_string.
 *  
 * This function appends the string from char * to cap_string @a strDst. \n
 * The function can figure out NULL terminator in the buffer, and \n
 * only appends the characters before the NULL terminator. \n
 * If there is no NULL terminator in the string, this function will \n
 * append the whole buffer.
 *
 * @param strDst a destination string to be appended.
 * @param pszSrc a buffer which stores source string.
 * @param nSrcBufLen the size of source buffer.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_OUT_OF_MEMORY.
 */
cap_result CAPString_AppendLow(cap_string strDst, char *pszSrc, int nSrcBufLen);


/** 
 * @brief Set string with format.
 *  
 * This function is similar to sprintf() function used in libc. \n
 * The function fills the string based on printf-style arguments which consist of \n
 * formatted string and arguments used in formatted string.
 *
 * @param strTarget a destination string to be set.
 * @param pszFormat formatted string which will be set to @a strTarget
 * @param ... arguments used in pszFormat
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_OUT_OF_MEMORY.
 */
cap_result CAPString_PrintFormat(cap_string strTarget, char *pszFormat, ...);


/**
 * @brief Set string with format via va_list.
 *  
 * This function is similar to vsprintf() function used in libc. \n
 * The function fills the string based on arguments provided by va_list.
 *
 * @param strTarget a destination string to be set.
 * @param pszFormat a formatted string which will be appended to @a strTarget.
 * @param argList the list of format and arguments.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_OUT_OF_MEMORY.
 */
cap_result CAPString_VPrintFormat(cap_string strTarget, char *pszFormat, va_list argList);


/** 
 * @brief Append string with format.
 *  
 * The function appends the string based on printf-style arguments which consist of \n
 * formatted string, and arguments used in formatted string.
 *
 * @param strTarget a destination string to be appended.
 * @param pszFormat a formatted string which will be appended to @a strTarget.
 * @param ... arguments used in pszFormat
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_OUT_OF_MEMORY.
 */
cap_result CAPString_AppendFormat(cap_string strTarget, char *pszFormat, ...);


/** 
 * @brief Replace string occurred in cap_string.
 *  
 *  The function replaces a string @a strFrom to @ strTo.
 *
 *  @param strTarget a target string to be changed.
 *  @param strFrom a string to be replaced.
 *  @param strTo a string to replace.
 *
 *  @return @ref ERR_CAP_NOERROR is return if there is no error. \n
 *  		Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_OUT_OF_MEMORY \n
 *  								@ref ERR_CAP_INVALID_PARAM.
 *  		if Error happens, strTarget would not be changed.
 */
cap_result CAPString_ReplaceString(cap_string strTarget, cap_string strFrom, cap_string strTo);


/** 
 * @brief Replace characters occurred in cap_string.
 *  
 * The function replaces a single character @a chFrom to @a chTo.
 *
 * @param strTarget a target string to be changed.
 * @param chFrom a character to be replaced.
 * @param chTo a character to replace
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_OUT_OF_MEMORY.
 */
cap_result CAPString_ReplaceChar(cap_string strTarget, char chFrom, char chTo);


/** 
 * @brief Retrieve a pointer to char of cap_string.
 *  
 * This function retrieves char * of cap_string.
 * This function used for printing out the variable \n
 * (such as printf function or @ref CAPString_PrintFormat). \n
 * @warning Do not store the pointer separatly, modify the data, or free the pointer. \n
 *          It will hurt the consistancy of cap_string data. \n
 *          Just use this function for instantly referencing/copying the internal data.
 *
 * @param strTarget a target string to retrieve a pointer to char.
 * @param pnStringLen [out] an output value which retrieves the string length. 
 *                    Put NULL if you don't need to retrive string length. \n
 *
 * @return  This function returns a pointer to actual string buffer. \n
 *          If an error occurs, it will return NULL.
 */
char *CAPString_LowPtr(cap_string strTarget, OUT int *pnStringLen);


/** 
 * @brief Retrieve the length of the string.
 *  
 * This function retrieves the length of the string.
 *
 * @param strTarget a target string to retrieve the string length.
 *
 * @return  This function returns the string length. \n
 *          If an error occurs or string is empty, it will return 0.
 */
int CAPString_Length(cap_string strTarget);


/** 
 * @brief Find a specific character from the string in order. 
 *  
 * This function searches a character @a ch from @a nIndex. \n
 * If the character is found, this function retrieves the index of the string \n 
 * where the character is located.
 *
 * @param strTarget a target string to find character
 * @param nIndex the start index to find character.
 * @param ch a character to find
 *
 * @return  This function returns the index of found character. \n
 *          If the character is not found, it returns -1 (@ref CAPSTR_INDEX_NOT_FOUND).
 */
int CAPString_FindChar(cap_string strTarget, int nIndex, char ch);


/** 
 * @brief Find a specific character from the string in reverse order. 
 *  
 * This function searches a character @a ch from @a nIndex. \n
 * Compared to @ref CAPString_FindChar, @a nIndex is a reverse-order index value \n
 * which means 0 is the last character of the string.
 * If the character is found, this function retrieves the index of the string. \n 
 * Retrieved index is not a reverse-order which means 0 is the first character of the string.
 *
 * @param strTarget a target string to find character
 * @param nIndex a start index to find character (reverse order).
 * @param ch a character to find
 *
 * @return  This function returns the index of found character (not reverse order). \n
 *          If the character is not found, it returns -1 (@ref CAPSTR_INDEX_NOT_FOUND).
 */
int CAPString_FindRChar(cap_string strTarget, int nIndex, char ch);


/** 
 * @brief Find a specific string from the string.
 *
 * This function searches cap_string @a strToFind from @a nIndex. \n
 * If @a strToFind is found in the @a strTarget, this function retrieves \n
 * the index of the string where the character is located.
 *
 * @param strTarget a target string to find @a strToFind
 * @param nIndex a start index to find charcater (reverse order).
 * @param strToFind a string with @a cap_string format to find
 *
 * @return  This function returns the index of found character. \n
 *          If the character is not found, it returns -1 (@ref CAPSTR_INDEX_NOT_FOUND).
 */
int CAPString_FindString(cap_string strTarget, IN int nIndex, IN cap_string strToFind);


/**
 * @brief Convert cap_string to double-type value. 
 *  
 * This function converts string to double value. Corresponding libc function is strtod(). \n
 * It converts the string started from @a nIndex to double value.
 *
 * @param strTarget a target string to perform double-value conversion.
 * @param nIndex a start index to convert a double value
 * @param pnEndIndex an end pointer which points to the last converted character. 
 *
 * @return This function returns a double value. \n
 *         If the value is not converted, return value and retrieved value of pnEndIndex both become 0.
 */
double CAPString_ToDouble(cap_string strTarget, int nIndex, OUT int *pnEndIndex);


/** 
 * @brief Convert cap_string to integer-type value. 
 *  
 * This function converts string to integer value. Corresponding libc function is strtol(). \n
 * It converts the string started from @a nIndex to an integer value.
 *
 * @param strTarget a target string to perform integer-value conversion.
 * @param nIndex a start index to convert an integer value
 * @param pnEndIndex an end pointer which points to the last converted character. 
 *
 * @return This function returns an integer value. \n
 *         If the value is not converted, return value and retrieved value of pnEndIndex both become 0.
 */
int CAPString_ToInteger(cap_string strTarget, int nIndex, OUT int *pnEndIndex);


/** 
 * @brief Convert cap_string to long-long-type value. 
 *  
 * This function converts string to long long value. Corresponding libc function is strtoll(). \n
 * It converts the string started from @a nIndex to an long long value.
 *
 * @param strTarget a target string to perform long-long-value conversion.
 * @param nIndex a start index to convert a long long value
 * @param pnEndIndex an end pointer which points to the last converted character. 
 *
 * @return This function returns a long long value. \n
 *         If the value is not converted, return value and retrieved value of pnEndIndex both become 0.
 */
long long CAPString_ToLongLong(cap_string strTarget, int nIndex, OUT int *pnEndIndex);


/** 
 * @brief Compare the prefix of the string value. 
 *  
 * This function checks @a strTarget has @a strPrefix as a prefix.
 *
 * @param strTarget a target string to check prefix.
 * @param strPrefix a prefix string to be compare.
 *
 * @return This function returns TRUE if the prefix is matched. Otherwise, returns FALSE.
 */
cap_bool CAPString_StartsWith(cap_string strTarget, cap_string strPrefix);


/** 
 * @brief Compare two strings
 *  
 * This function compare two strings are equal.
 *
 * @param strCompare1 a string to compare.
 * @param strCompare2 a string to compare.
 *
 * @return This function returns TRUE if two strings are same. Otherwise, returns FALSE.
 */
cap_bool CAPString_IsEqual(cap_string strCompare1, cap_string strCompare2);


/**
 * @brief Compare two strings ignoring cases
 *
 * This function compare two strings are equal ignoring cases.
 *
 * @param strCompare1 a string to compare.
 * @param strCompare2 a string to compare.
 *
 * @return This function returns TRUE if two case-ignored strings are same. Otherwise, returns FALSE.
 */
cap_bool CAPString_IsEqualIgnoreCase(cap_string strCompare1, cap_string strCompare2);


#define CAPSTRING_MAX (2147483647 - 1)

#define CAPSTR_INDEX_NOT_FOUND (-1)

#define SAFE_CAPSTRING_DELETE(str) if(str!=NULL){ CAPString_Delete(&str); str=NULL; }

#define CAPSTRING_CONST(strName, strVal) static struct _SCAPString st ## strName ## _const = { strVal, sizeof(strVal)-1, sizeof(strVal) }; \
static const cap_string strName = &st##strName ## _const;

#ifdef __cplusplus
}
#endif


#endif /* CAPSTRING_H_ */
