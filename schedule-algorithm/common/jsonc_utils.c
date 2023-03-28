#include "jsonc_utils.h"

#include "mqtt_utils.h"

cap_result Jsonc_GetObjectOptional(json_object *pSrcJsonObject,
                                   IN const char *pszKey,
                                   json_object **ppDstJsonObject) {
  cap_result result = ERR_CAP_UNKNOWN;
  json_object *pTempObject = NULL;

  if (!json_object_object_get_ex(pSrcJsonObject, pszKey, &pTempObject)) {
    *ppDstJsonObject = NULL;
  } else {
    *ppDstJsonObject = pTempObject;
  }

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

cap_result Jsonc_GetObject(json_object *pSrcJsonObject, IN const char *pszKey,
                           json_object **ppDstJsonObject) {
  cap_result result = ERR_CAP_UNKNOWN;
  json_object *pTempObject = NULL;

  if (!json_object_object_get_ex(pSrcJsonObject, pszKey, &pTempObject)) {
    ERRASSIGNGOTO(result, ERR_CAP_INVALID_DATA, _EXIT);
  }

  *ppDstJsonObject = pTempObject;

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

cap_result Jsonc_GetIntOptional(json_object *pJsonObject, IN const char *pszKey,
                                IN OUT int *pnValue, IN int nDefault) {
  cap_result result = ERR_CAP_UNKNOWN;
  json_object *pJsonValue = NULL;

  if (!json_object_object_get_ex(pJsonObject, pszKey, &pJsonValue)) {
    *pnValue = nDefault;
  } else {
    *pnValue = json_object_get_int(pJsonValue);
  }

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

cap_result Jsonc_GetInt(json_object *pJsonObject, IN const char *pszKey,
                        IN OUT int *pnValue) {
  cap_result result = ERR_CAP_UNKNOWN;
  json_object *pJsonValue = NULL;

  if (!json_object_object_get_ex(pJsonObject, pszKey, &pJsonValue)) {
    ERRASSIGNGOTO(result, ERR_CAP_INVALID_DATA, _EXIT);
  }

  *pnValue = json_object_get_int(pJsonValue);

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

cap_result Jsonc_GetDouble(json_object *pJsonObject, IN const char *pszKey,
                           IN OUT double *pdbValue) {
  cap_result result = ERR_CAP_UNKNOWN;
  json_object *pJsonValue = NULL;

  if (!json_object_object_get_ex(pJsonObject, pszKey, &pJsonValue)) {
    ERRASSIGNGOTO(result, ERR_CAP_INVALID_DATA, _EXIT);
  }

  *pdbValue = json_object_get_double(pJsonValue);

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

cap_result Jsonc_GetStringOptional(json_object *pJsonObject,
                                   IN const char *pszKey,
                                   IN OUT cap_string strValue,
                                   IN const char *pszDefault) {
  cap_result result = ERR_CAP_UNKNOWN;
  json_object *pJsonValue = NULL;

  if (!json_object_object_get_ex(pJsonObject, pszKey, &pJsonValue)) {
    result = CAPString_SetLow(strValue, pszDefault, CAPSTRING_MAX);

    ERRIFGOTO(result, _EXIT);
  } else {
    result = CAPString_SetLow(strValue, json_object_get_string(pJsonValue),
                              CAPSTRING_MAX);
    ERRIFGOTO(result, _EXIT);
  }

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

cap_result Jsonc_GetString(json_object *pJsonObject, IN const char *pszKey,
                           IN OUT cap_string strValue) {
  cap_result result = ERR_CAP_UNKNOWN;
  json_object *pJsonValue = NULL;

  if (!json_object_object_get_ex(pJsonObject, pszKey, &pJsonValue)) {
    ERRASSIGNGOTO(result, ERR_CAP_INVALID_DATA, _EXIT);
  }

  result = CAPString_SetLow(strValue, json_object_get_string(pJsonValue),
                            CAPSTRING_MAX);
  ERRIFGOTO(result, _EXIT);

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

cap_result Jsonc_AddInt(json_object *pJsonObject, IN const char *pszKey,
                        IN int nValue) {
  cap_result result = ERR_CAP_UNKNOWN;

  IFVARERRASSIGNGOTO(pJsonObject, NULL, result, ERR_CAP_INVALID_PARAM, _EXIT);

  json_object_object_add(pJsonObject, pszKey, json_object_new_int(nValue));

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

cap_result Jsonc_AddDouble(json_object *pJsonObject, IN const char *pszKey,
                           IN double dbValue) {
  cap_result result = ERR_CAP_UNKNOWN;

  IFVARERRASSIGNGOTO(pJsonObject, NULL, result, ERR_CAP_INVALID_PARAM, _EXIT);

  json_object_object_add(pJsonObject, pszKey, json_object_new_double(dbValue));

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

cap_result Jsonc_AddString(json_object *pJsonObject, IN const char *pszKey,
                           IN char *strValue) {
  cap_result result = ERR_CAP_UNKNOWN;

  IFVARERRASSIGNGOTO(pJsonObject, NULL, result, ERR_CAP_INVALID_PARAM, _EXIT);

  json_object_object_add(pJsonObject, pszKey, json_object_new_string(strValue));

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

cap_result Jsonc_ToString(json_object *pJsonObject,
                          IN OUT cap_string strString) {
  cap_result result = ERR_CAP_UNKNOWN;

  IFVARERRASSIGNGOTO(pJsonObject, NULL, result, ERR_CAP_INVALID_PARAM, _EXIT);
  IFVARERRASSIGNGOTO(strString, NULL, result, ERR_CAP_INVALID_PARAM, _EXIT);

  result = CAPString_SetLow(strString, json_object_to_json_string(pJsonObject),
                            CAPSTRING_MAX);
  ERRIFGOTO(result, _EXIT);

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

cap_result Jsonc_Parse(OUT json_object **ppJsonObject, IN char *pszJsonString,
                       IN int nJsonStringLen) {
  cap_result result = ERR_CAP_UNKNOWN;
  struct json_tokener *tok;
  struct json_object *obj = NULL;
  json_object *pJsonObject;

  IFVARERRASSIGNGOTO(pszJsonString, NULL, result, ERR_CAP_INVALID_PARAM, _EXIT);

  if (nJsonStringLen < 0) {
    ERRASSIGNGOTO(result, ERR_CAP_INVALID_PARAM, _EXIT);
  }

  tok = json_tokener_new();
  ERRMEMGOTO(tok, result, _EXIT);

  pJsonObject = json_tokener_parse_ex(tok, pszJsonString, nJsonStringLen);

  if (tok->err != json_tokener_success) {
    if (obj != NULL) json_object_put(obj);
    obj = NULL;

    ERRASSIGNGOTO(result, ERR_CAP_CONVERSION_ERROR, _EXIT);
  }

  json_tokener_free(tok);

  *ppJsonObject = pJsonObject;

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}