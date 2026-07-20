# -*- coding: utf-8 -*-
#
# � 2007-2020 Lenze Drive Systems GmbH, Lenze Automation GmbH. All rights reserved.
# � 2020-     Lenze SE. All rights reserved.
#
#-----------------------------------------------------------------------------------------------------------------------
# PyTeF file header (for Test Library) V1.4-01
#-----------------------------------------------------------------------------------------------------------------------
# Disable linter warnings -> OTHER DISABLES ARE NOT RECOMMENDED, CHANGES ARE AT YOUR OWN RISK!
#
#-----------------------------------------------------------------------------------------------------------------------
# Test Library docstring (must be first definition in file)
#-----------------------------------------------------------------------------------------------------------------------
"""
    Library for Target Device Manager Test. This include all the grouped test cases which will be called from test
    script. This include common function which will be used by all the tools while running the test
"""
#-----------------------------------------------------------------------------------------------------------------------
# Test Library imports (must be defined before code)
#-----------------------------------------------------------------------------------------------------------------------
import os
import traceback
from datetime import datetime
import typing as ty

#audit log utilites
from tests.cysec.auditlog_testsuites.audit_log_test.lib.Lib_Base import Lib_Base
# from tests.cysec.auditlog_testsuites.audit_log_test.utils.constants_audit_log import
from tests.cysec.auditlog_testsuites.audit_log_test.utils.constants_audit_log import Constants_i950
from tests.cysec.auditlog_testsuites.audit_log_test.lib.parser.Log_Parser_Factory import Factory_Log_Parser
# from tests.cysec.auditlog_testsuites.audit_log_test.utils.excelReader import CmdParamConfigExlParser
# from tests.cysec.auditlog_testsuites.audit_log_test.utils.excelReportUpdater import ReportExlParser
# from tests.cysec.auditlog_testsuites.audit_log_test.core.ssh_client_lib import SSHClient

#testlib utilites
from tests.testlib.utils.CommonLib import userSleep
#-----------------------------------------------------------------------------------------------------------------------
# SVN keyword section
#-----------------------------------------------------------------------------------------------------------------------
FILE_URL = "$HeadURL: http://repository.lenze.com/ssv/TestRepository/branches/sdc/tests/common/opc_ua/lib/Lib_OpcUa.py $"[10:-2]  # noqa:E501
FILE_REV = "$Revision: 8942 $"[11:-2]
FILE_DATE = "$LastChangedDate: 2022-03-15 09:39:23 +0530 (Tue, 15 Mar 2022) $"[18:-2]
FILE_AUTHOR = "$LastChangedBy: patole@lenze.com $"[16:-2]

#-----------------------------------------------------------------------------------------------------------------------
# PyTeF file header end
#-----------------------------------------------------------------------------------------------------------------------
class Lib_i950(Lib_Base):
    """
        Audit Log Lib
    """
    prefixCls = 'Lib_Base_i950'

    #-------------------------------------------------------------------------------------------------------------------
    def __init__(self) -> None:
        """
        Constructor
        """
        #Do not change the execution sequence
        super().__init__()
        self.constants = Constants_i950()

    #-------------------------------------------------------------------------------------------------------------------
    def emptyOldLogs(self, extSSHClient = None) -> None:
        """
        This method is used to empty the contents of logs .
        """
        try:
            sshClient = self.sshMasterClient

            if extSSHClient:
                sshClient = extSSHClient

            # Log the start of the log deletion process
            self.logger.newStep("Emptying/Clearing Previous Logs")
            try:
                # Establish connection to the remote controller using SSH
                sshClient.connect()
                controllerStorage = sshClient.list_remote_directory(remote_path = self.constants.CONTROLLER_LOG_PATH)
                for flname in controllerStorage :
                    if flname in self.constants.LOG_FOLDERS.keys():
                        remote_path = self.constants.LOG_FILES[self.constants.LOG_FOLDERS[
                                                               flname]].split(self.constants.LOG_FILE_NAME)[0]

                        fileListController = sshClient.list_remote_directory(remote_path = remote_path)

                        if fileListController:
                            self.logger.info(f"Files in folder - {fileListController}")
                            try:
                                # Construct the full remote file path
                                remote_path = self.constants.LOG_FILES[self.constants.LOG_FOLDERS[flname]]
                                # remote_path = self.constants.CONTROLLER_LOG_PATH + logFile


                                self.logger.info(f"File to empty - {remote_path}")

                                if remote_path.split('.')[-1].isnumeric():
                                    self.logger.info(f"Delete the rotated log : - {remote_path}")
                                    sshClient.delete_remote_file(remote_path)
                                    continue

                                # empty remote file content
                                sshClient.change_remote_file_content(remote_path = remote_path,
                                                                     new_content = "",
                                                                     overWrite = True)
                            except Exception as e:
                                self.logger.error(e)
                        else:
                            self.logger.error(f"No files found in folder - {remote_path}")
                            continue
                    else:
                        self.logger.error(f"{flname} not found in LOG_FILES")
                        continue


                # Disconnect from the remote server after deletion
                sshClient.disconnect()

            except Exception as exc:
                # Log any exception that occurs while deleting log files
                self.logger.error(f"Exception Occurred in emptying old log files: {exc}")
        except Exception:
            # Log any unexpected exceptions in the outer try block
            self.logger.error("Exception Occurred in emptying old log files")

    #-------------------------------------------------------------------------------------------------------------------
    def verifyLogs(self, logType, validationType, detailsToCheck, extSSHClient = None) -> bool:
        """
        Verifies log files based on provided details to check.
        """

        # Initialize the verification result as True
        vertificationResult = True

        # localLog = self.constants.LOCAL_0

        sshClient = self.sshMasterClient

        if extSSHClient:
            sshClient = extSSHClient

        # Establish SSH connection
        sshClient.connect()

        timeOut = 300
        self.logger.newStep(f"Waiting for {timeOut} sec for {logType} to generated in controller...")
        timeCount = 0
        while timeCount < timeOut:
            if sshClient.check_remote_file_exists(
                    remote_path = self.constants.LOG_FILES[logType]):
                self.logger.info(f"{logType} is generated in controller...")
                break

            userSleep(10)
            timeCount += 10
            self.logger.info(f"Waiting for {timeOut - timeCount}sec {logType} to be generated in controller...")
        else:
            self.logger.error(f"{logType} NOT generated in controller...")

        # Get the current test case name from the stack trace
        stackList = traceback.extract_stack()
        currentTestCase = [stackObj for stackObj in stackList if "Lib_Sys_Log.py" in stackObj.filename or \
                           "Lib_cmdParam.py" in stackObj.filename][-1].name

        # Start logging the step for verifying logs
        self.logger.newStep("Verifying Logs", level = 1)

        # Check if the specific log file exists on the remote server
        remote_path = self.constants.LOG_FILES[logType]
        if sshClient.check_remote_file_exists(
                remote_path = remote_path):

            # Get the list of log files in the remote directory
            self.logger.info(f"{self.constants.LOG_FILES[logType]} is present in controllers log folder")
        else:
            # Log error if the specified log file does not exist
            self.logger.error(f"{self.constants.LOG_FILES[logType]} do not exist in log folder")
            return False

        # Check if the local folder for storing logs is created
        self.logger.newStep("Creating Directory For Storing Logs Locally")
        if Lib_Base.SYSTEM_LOGS_FOLDER_CREATED:
            # Folder is already created
            self.logger.info(f"{[type(self).prefixCls]} Local Log folder is already present")
        else:
            # Create a new folder for storing logs locally
            Lib_Base.SYSTEM_LOGS_FOLDER_CREATED = '_'.join(
                str(datetime.now()).split()).split('.')[0].replace(":", "_")

            Lib_Base.SYSTEM_LOGS_FOLDER_CREATED = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                self.constants.SYSTEM_LOG_PATH,
                Lib_Base.SYSTEM_LOGS_FOLDER_CREATED)

            self.logger.info(f"{[type(self).prefixCls]} Creating folder named :- "
                             f"{Lib_Base.SYSTEM_LOGS_FOLDER_CREATED}")
            os.makedirs(Lib_Base.SYSTEM_LOGS_FOLDER_CREATED)

        # Initialize a set to store details found during validation
        detailsFound = set()

        if sshClient.check_remote_file_exists(
                     remote_path = self.constants.LOG_FILES[logType]):

            logFilesToCheck = [self.constants.LOG_FILE_NAME]

        else:
            self.logger.error(f"{self.constants.LOG_FILES[logType]} do not exist in log folder")
            return False

        for logFile in logFilesToCheck:

            self.logger.newStep(f"Copying and Validating Logs :- {[logFile]}")

            # Create the local path for storing the copied log file
            self.logger.newStep("Copy controller log to Local:", level = 3)
            logPath = os.path.join(Lib_Base.SYSTEM_LOGS_FOLDER_CREATED,
                                   '_'.join([self.testCase.testCaseName, currentTestCase, logFile]))

            # Copy the remote log file to the local directory
            sshClient.copy_file_to_local(self.constants.LOG_FILES[logType], logPath)

            # Parse the log file using a suitable parser
            self.logger.newStep("Parsing Logs", level = 3)
            logObj = Factory_Log_Parser().create_parser(logType = self.constants.LOCAL_LOG_0, logPath = logPath)

            # Validate log structure for the given log type
            if logType not in Lib_Base.LOGS_FORMAT_VALIDATED or \
                    Lib_Base.LOGS_FORMAT_VALIDATED[logType] is False:

                # Check if the log structure is valid
                if logObj.validateLogStructure():
                    # Log a success message if the log structure is valid
                    self.logger.info(
                        f"{[type(self).prefixCls]} Successfully verified file structure of type - {logType}")
                    # Mark the log type as validated and valid
                    Lib_Base.LOGS_FORMAT_VALIDATED[logType] = True

                    self.logger.info(
                        f"Lib_Base.LOGS_FORMAT_VALIDATED = {Lib_Base.LOGS_FORMAT_VALIDATED}")

                # If the log structure is invalid
                else:
                    # Log an error message if the log structure is invalid
                    self.logger.error(
                        f"{[type(self).prefixCls]} Structure of type - {logType} is Invalid")
                    # Mark the log type as validated but invalid
                    Lib_Base.LOGS_FORMAT_VALIDATED[logType] = False

            # Validate the details in the log file
            self.logger.newStep(f"Validating details in {logPath}", level = 3)
            for detail in detailsToCheck:
                matchingLine = logObj.validateLogFileData(validationType = validationType, result = detail)
                if matchingLine:
                    # Log found details
                    detailsFound.add(matchingLine)
                    self.logger.info(f"{[type(self).prefixCls]} FOUND '{matchingLine}' in {logFile}")
                else:
                    # Log missing details
                    self.logger.error(f"{[type(self).prefixCls]} '{detail}' NOT FOUND in {logFile}")

            # Verify if all expected details are present
            self.logger.newStep(f"Checking If All Details are found in the logfile : {logFile}")
            if len(detailsFound) == len(set(detailsToCheck)):
                # All details found; verification successful
                vertificationResult = True
                self.logger.info(f"{[type(self).prefixCls]} All details are found in log files")
                for detail in detailsFound:
                    self.logger.info(f"{[type(self).prefixCls]} Detail Found :- '{detail}'")
            else:
                # Some details missing; log the discrepancy
                vertificationResult = False
                if len(detailsFound) == 0:
                    self.logger.error(f"No detail is found in :{logFile}")
                else:
                    self.logger.error(f"{[type(self).prefixCls]} Some Details Are Missing in the log : {logFile}")

        # Disconnect from SSH client
        sshClient.disconnect()

        # Return the verification result
        return vertificationResult

    #-------------------------------------------------------------------------------------------------------------------
    def findCtrlType(self, ipcObj : ty.List["_Ipc"]) -> str:
        """
        This method is used to map controller Type using IPC object
        """
        # map to hold controller name and type
        ctrlName = "i950 (BS-STO)"
        if ipcObj.isI950:
                return ctrlName
        return ''

    #-------------------------------------------------------------------------------------------------------------------
