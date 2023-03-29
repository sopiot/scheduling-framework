#ifndef MIDDLEWARE_GENRATE_JSON_
#define MIDDLEWARE_GENRATE_JSON_

#include <sqlite3.h>

#include "jsonc_utils.h"

cap_result GenerateJson_Thing(sqlite3 *pDBconn, int nThingId, const unsigned char *pszThingName, int bIsAlive,
                              int bIsSuper, int bIsParallel, int nAliveCycle, int bIncludePrivate,
                              OUT json_object *pThingObject);

#endif  // MIDDLEWARE_GENRATE_JSON_