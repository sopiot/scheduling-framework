/*
 * CAPFile.h
 *
 *  Created on: 2015. 8. 20.
 *      Author: chjej202
 */

#ifndef CAPFILE_H_
#define CAPFILE_H_


#include <cap_common.h>
#include <CAPString.h>

#ifdef __cplusplus
extern "C"
{
#endif

typedef enum _EFileSeek {
    FILE_SEEK_START,
    FILE_SEEK_CUR,
    FILE_SEEK_END,
} EFileSeek;

#define CAP_READ_MODE   (0x01)
#define CAP_WRITE_MODE  (0x02)
#define CAP_APPEND_MODE (0x03)
#define CAP_PLUS_MODE   (0x10)

typedef enum _EFileMode {
    FILE_MODE_READ = CAP_READ_MODE,
    FILE_MODE_READ_PLUS = CAP_READ_MODE | CAP_PLUS_MODE,
    FILE_MODE_WRITE = CAP_WRITE_MODE,
    FILE_MODE_WRITE_PLUS = CAP_WRITE_MODE | CAP_PLUS_MODE,
    FILE_MODE_APPEND = CAP_APPEND_MODE,
    FILE_MODE_APPEND_PLUS = CAP_APPEND_MODE | CAP_PLUS_MODE,
} EFileMode;


/** 
 * @brief Create a file access handle.
 *  
 * This function creates a file access handle. \n
 * It only creates a structure to be used. \n
 * It does not perform any file operations. \n
 *
 * @param phFile a file access handle to be created.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_PARAM, @ref ERR_CAP_OUT_OF_MEMORY.
 */
cap_result CAPFile_Create(OUT cap_handle *phFile);


/** 
 * @brief Destroy a file access handle.
 *  
 * This function destroys a file access handle. \n
 * It also close a file if a file is not closed yet.
 *
 * @param phFile a file access handle to be destroyed.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_PARAM, @ref ERR_CAP_INVALID_HANDLE.
 */
cap_result CAPFile_Destroy(IN OUT cap_handle *phFile);


/** 
 * @brief Open a file.
 *  
 * This function opens a file located at @a strPath. \n
 * Depending on the usage of file, appropriate @ref EFileMode \n
 * needs to be passed as an argument. \n
 * If a file is already opened, this function closes the previous file before opening the file.
 *
 * @param hFile a file access handle.
 * @param strPath a file path to open
 * @param enFileMode open mode. Refer @ref EFileMode for available file modes.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_PARAM, @ref ERR_CAP_INVALID_HANDLE, \n
 *         @ref ERR_CAP_INTERNAL_FAIL, @ref ERR_CAP_OUT_OF_MEMORY, @ref ERR_CAP_OPEN_FAIL.
 */
cap_result CAPFile_Open(cap_handle hFile, cap_string strPath, IN EFileMode enFileMode);


/** 
 * @brief Close a file.
 *  
 * This function closes a file. \n
 * If a file is not opened, the internal operation is ignored.
 *
 * @param hFile a file access handle.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE.
 */
cap_result CAPFile_Close(cap_handle hFile);


/** 
 * @brief Read a file.
 *  
 * This function reads data from a file. \n
 * This function reads and stores data into @a pBuffer. \n
 * Maximum data to be read is @a nDataToRead. \n
 * The amount of data actually read is retrieved at @a pnDataRead. \n
 * If a file is not opened, this function retrieves an error.
 *
 * @param hFile a file access handle.
 * @param pBuffer a buffer to store read data.
 * @param nDataToRead the size of data to read
 * @param pnDataRead [out] the size of data read
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_INVALID_PARAM, \n
 *         @ref ERR_CAP_FILE_NOT_OPENED
 */
cap_result CAPFile_Read(cap_handle hFile, IN OUT char *pBuffer, IN int nDataToRead, OUT int *pnDataRead);


/** 
 * @brief Write a file.
 *  
 * This function writes data to a file. \n
 * This function writes data in @a pBuffer. \n
 * Maximum data to be written is @a nDataLen. \n
 * The amount of data actually written is retrieved at @a pnDataWritten. \n
 * If a file is not opened, this function retrieves an error.
 *
 * @param hFile a file access handle.
 * @param pData a source buffer to write data.
 * @param nDataLen the size of data to write.
 * @param pnDataWritten [out] the size of data written.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_INVALID_PARAM, \n
 *         @ref ERR_CAP_FILE_NOT_OPENED.
 */
cap_result CAPFile_Write(cap_handle hFile, IN char *pData, IN int nDataLen, OUT int *pnDataWritten);


/** 
 * @brief Move a file offset.
 *  
 * This function moves a file offset of file. \n
 * Base offset is determined by @ref EFileSeek. To move backward, \n
 * set lOffset to a negative value.
 *
 * @param hFile a file access handle.
 * @param lOffset an offset to move from base offset.
 * @param enSeek base offset to move a file offset. @ref EFileSeek.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_INVALID_PARAM, \n
 *         @ref ERR_CAP_FILE_NOT_OPENED, @ref ERR_CAP_SEEK_FAIL.
 */
cap_result CAPFile_Seek(cap_handle hFile, long lOffset, EFileSeek enSeek);


/** 
 * @brief Flush a file.
 *  
 * This function updates the change of a file immediately.
 *
 * @param hFile a file access handle.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_FILE_NOT_OPENED. \n
 */
cap_result CAPFile_Flush(cap_handle hFile);


/** 
 * @brief return the size of a file.
 *
 * @param hFile a file access handle.
 * @parm sz [out] the size of a file.

 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_FILE_NOT_OPENED. \n
 */
cap_result CAPFile_GetFileSize(IN cap_handle hFile, OUT int *sz);

#ifdef __cplusplus
}
#endif


#endif /* CAPFILE_H_ */
