#ifndef JSONC_UTILS_H_
#define JSONC_UTILS_H_

#include "json-c/json_object.h"
#include "json-c/json_tokener.h"
#include "sop_common.h"

cap_result Jsonc_GetObjectOptional(json_object *pSrcJsonObject,
                                   IN const char *pszKey,
                                   json_object **ppDstJsonObject);
cap_result Jsonc_GetObject(json_object *pSrcJsonObject, IN const char *pszKey,
                           json_object **ppDstJsonObject);

cap_result Jsonc_GetIntOptional(json_object *pJsonObject, IN const char *pszKey,
                                IN OUT int *pnValue, IN int nDefault);
cap_result Jsonc_GetInt(json_object *pJsonObject, IN const char *pszKey,
                        IN OUT int *pnValue);
cap_result Jsonc_GetDouble(json_object *pJsonObject, IN const char *pszKey,
                           IN OUT double *pdbValue);
cap_result Jsonc_GetStringOptional(json_object *pJsonObject,
                                   IN const char *pszKey,
                                   IN OUT cap_string strValue,
                                   IN const char *pszDefault);
cap_result Jsonc_GetString(json_object *pJsonObject, IN const char *pszKey,
                           IN OUT cap_string strValue);

cap_result Jsonc_AddInt(json_object *pJsonObject, IN const char *pszKey,
                        IN int nValue);
cap_result Jsonc_AddDouble(json_object *pJsonObject, IN const char *pszKey,
                           IN double dbValue);
cap_result Jsonc_AddString(json_object *pJsonObject, IN const char *pszKey,
                           IN char *pszValue);

cap_result Jsonc_ToString(json_object *pJsonObject,
                          IN OUT cap_string strString);

/**
 * @brief Parse a json string \n
 * [Notice] ppJsonObject should be freed after use.
 *
 * @param ppJsonObject [out] a json_object that contains parsed result.
 * @param pszJsonString char pointer of the json string.
 * @param nJsonStringLen length of the json string.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned -
 *          @ref ERR_CAP_INVALID_PARAM,
 *          @ref ERR_CAP_OUT_OF_MEMORY.
 */
cap_result Jsonc_Parse(OUT json_object **ppJsonObject, IN char *pszJsonString,
                       IN int nJsonStringLen);

#endif
