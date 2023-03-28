/*
 * CAPLogger.h
 *
 *  Created on: 2015. 8. 20.
 *      Author: chjej202
 */

#ifndef CAPLOGGER_H_
#define CAPLOGGER_H_


#include <cap_common.h>
#include <CAPString.h>


#ifdef __cplusplus
extern "C"
{
#endif

/** 
 * @brief Log level used as an argument of @ref CAPLogger_Create.
 *  
 * Basd on this emumerator, user can decide to print short or detailed logs.
 */
typedef enum _ELogLevel
{
    LOG_NONE   = 0, //!< Print log with message level @ref MSG_NONE
    LOG_INFO   = 1, //!< Print log with message level @ref MSG_INFO and @ref MSG_ERROR
    LOG_ERROR  = 1, //!< Same to @ref LOG_INFO
    LOG_WARN   = 2, //!< Print log with message level @ref MSG_INFO, @ref MSG_ERROR, and @ref MSG_WARN
    LOG_DETAIL = 3, //!< Print all the log except message level @ref MSG_DEBUG
    LOG_DEBUG  = 4, //!< Print all the log
} ELogLevel;


/** 
 * @brief Log message level used as an argument of @ref CAPLogger_Write.
 *  
 * Developers can decide each log's importance. \n
 * Log tags can be changed on each log line depending on this message level.
 *
 */
typedef enum _ELogMsgLevel
{
    MSG_NONE   = 0, //!< The log needs to be printed even though user does not want to print any logs.
    MSG_INFO   = 1, //!< Information log message.
    MSG_ERROR  = 2, //!< Error log message.
    MSG_WARN   = 3, //!< warning log message.
    MSG_DETAIL = 4, //!< detailed log message.
    MSG_DEBUG  = 5, //!< debug log message.
} ELogMsgLevel;


/** 
 * @brief Create a logger.
 *  
 * This function creates a logger which gives a method to write logs. \n
 * Logger writes a log to the file thread-safely, but not file-safely. \n
 * If two processes are writing to a same file simultaneously, \n
 * contents of logged data may be corrupted.
 * 
 * @param strLogPath a log file path.
 * @param strPrefix a prefix for each log line.
 * @param enLogLevel a log level.
 * @param phLog [out] a logger handle to be created.
 * @param nMaxLogSize a log file max size.
					  defualt value is 2MB when you set nMaxLogSize to -1.
 * @param nMaxBackupNum the number of log files
					    defualt value is 1 when you set nMaxBackupNum to -1.
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_PARAM, @ref ERR_CAP_OUT_OF_MEMORY, \n
 *         @ref ERR_CAP_OPEN_FAIL.
 */
cap_result CAPLogger_Create(IN cap_string strLogPath, IN cap_string strPrefix, IN ELogLevel enLogLevel, IN int nMaxLogSize, IN int nMaxBackupNum, OUT cap_handle *phLog);


/** 
 * @brief Destroy a logger.
 *  
 * This function destroys a logger.
 * 
 * @param phLog a logger handle to be destroyed.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_INVALID_PARAM.
 */
cap_result CAPLogger_Destroy(IN OUT cap_handle *phLog);


/** 
 * @brief Write a single-line log.
 *  
 * This function prints a single-line log.
 * Format of each log is "[YYYY/MM/DD hh:mm:ss][process id][thread id][log tag][log prefix] log contents". \n
 * For example:
 *
 *     @code
 *     [2015/11/23 00:28:46][24219][0x36858740][LOG_INFO][fi_manager] Fault injection manager is started
 *     @endcode
 *
 * Log tag is determined by @a enLogLevel
 *
 * @param hLog a logger handle.
 * @param enLogLevel a log message level.
 * @param pszFormat printf-style contents to write a log.
 * @param ... arguments used in @a pszFormat.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_INVALID_PARAM.
 */
cap_result CAPLogger_Write(IN cap_handle hLog, ELogMsgLevel enLogLevel, const char *pszFormat, ...);

#ifdef __cplusplus
}
#endif


#endif /* CAPLOGGER_H_ */
