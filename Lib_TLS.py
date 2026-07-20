# -*- coding: utf-8 -*-
#
# © 2007-2020 Lenze Drive Systems GmbH, Lenze Automation GmbH. All rights reserved.
# © 2020-     Lenze SE. All rights reserved.
#
#-----------------------------------------------------------------------------------------------------------------------
# PyTeF file header (for Test Library) V1.4-01
#-----------------------------------------------------------------------------------------------------------------------
# Disable linter warnings -> OTHER DISABLES ARE NOT RECOMMENDED, CHANGES ARE AT YOUR OWN RISK!
# pylint: disable=invalid-name
#
#-----------------------------------------------------------------------------------------------------------------------
# Test Library docstring (must be first definition in file)
#-----------------------------------------------------------------------------------------------------------------------
"""
    Library for Audit Log TLS and IEC. This include all the grouped test cases which will be called from test
    script. This include common function which will be used by all the tools while running the test
"""
#-----------------------------------------------------------------------------------------------------------------------
# Test Library imports (must be defined before code)
#-----------------------------------------------------------------------------------------------------------------------
import traceback
from datetime import datetime
import random
import string
from collections import Counter
from typing import List, Optional
import re
from pytef.namespace.testlib import Version, Result, autobehavior, os
from pytef.namespace.testcase import IpcFilter, IpcLenzeC550, IpcLenzeC520, ConverterFilter
from lenze.namespace.config.ipc.alpharelease import IpcLenzeC430
from pytef.namespace.config.converter import I950
from tests.cysec.auditlog_testsuites.audit_log_test.core.AuditLog_PLC import AuditLog_PLC
from tests.cysec.auditlog_testsuites.audit_log_test.utils.excelReader import ConfigExlParser
from tests.cysec.auditlog_testsuites.audit_log_test.utils.constants_audit_log import Constants_Base
from tests.testlib.ssh.ssh_client_lib import SSHClient, SSHConfig
from tests.cysec.auditlog_testsuites.audit_log_test.core.ssh_client_lib import SSHClient as SSHClientController
from tests.cysec.auditlog_testsuites.audit_log_test.lib.parser.Log_Parser import Validate_Data
from pytef.util import (Boolean, Signed16, Signed32, VisibleString)
from tests.cysec.auditlog_testsuites.audit_log_test.lib.parser.Log_Parser_Factory import (Factory_Log_Parser)
from tests.testlib.lib_pywinauto.easystarter_firmware.EasyStarterFirmware import EasyStarterFirmware
from tests.testlib.utils.CommonLib import (userSleep, clsLogger, deleteUserManagementFiles,
                                           switchOffController, switchOnController, isPytefPC)

from tests.cysec.auditlog_testsuites.audit_log_test.lib.Lib_Base import Lib_Base
from typing import Callable

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

def logTestDetails() -> Callable:
    """
    Decorator to log test details and save test results for a given test case.

    Returns:
        function: A decorator that wraps the test function to log and save its results.

    The decorator performs the following actions:
    1. Logs the test description at the start of the test.
    2. Executes the test function.
    3. Logs the test description with the result at the end of the test.
    4. Saves the test result.

    Example::

        @logTestDetails()
        def test_example(self):
            # Test implementation
            pass
    """
    #-------------------------------------------------------------------------------------------------------------------
    def decorator(func : Callable) -> Callable:
        def wrapper(self, *args, **kwargs) -> bool:
            self.logTestDescription()

            if Lib_TLS.skipTestCases:
                self.testCase.skip()

            grpName = self.configXlsObj.getGroupName(testCaseName = self.testCase.testCaseName)

            if grpName in ['Grp_05']:
                self.ipcObjs[0].cmd.appResetCold()
                userSleep(2)
                self.ipcObjs[0].cmd.appStart()

            elif grpName in ['Grp_01', 'Grp_02', 'Grp_03']:
                userSleep(2)
                self.ipcObjs[0].cmd.appStart()

            self.emptyOldLogs()

            result = func(self, *args, **kwargs)
            # Logging and Saving test result
            self.logTestDescription(endFlag = True, result = result)
            self.saveTestResult(testResult = result)
            return result
        return wrapper
    return decorator

#-----------------------------------------------------------------------------------------------------------------------
class Lib_TLS(Lib_Base):
    """
        Audit Log TLS Lib
    """
    prefixCls = 'Lib_TLS'
    __LIB_DICT = {}

    LIB_NAME = 'Lib_TLS'
    LIB_VERSION = Version(1, 0, 0)

    SERVER_LOG_PATH = None
    PLC_OBJ = None

    skipTestCases = False

    #-------------------------------------------------------------------------------------------------------------------
    def __init__(self) -> None:
        """
        Constructor
        """

        try:
            # self.constants = Constants_Base()
            super().__init__(reportSheetNames = Constants_Base.REPORT_SHEET_TLS,
                             configFileName = Constants_Base.CONGIF_FILE_PATH_TLS)

            self.logger.info(f"[{[type(self).prefixCls]}] in Lib_TLS::__init__()")

            # define members
            self.sshTlsServer = None

            self.plcProject = None

            try:
                ipcFilter = IpcFilter(ipcClass = [IpcLenzeC430, IpcLenzeC520, IpcLenzeC550])
                self.ipcObjs = self.testCase.resource.ipc(ipcFilter = ipcFilter, number = 1)
            except Exception:
                try:
                    convFilter = ConverterFilter(convClass = I950)
                    self.ipcObjs = self.testCase.resource.converter(convFilter = convFilter, number = 1)

                except Exception:
                    self.logger.error(f"[{type(self).prefixCls}] Unable to reach i950 controller")

            # Save controller IP address
            self.ipAddresses.append(self.ipcObjs[0].channelList[0].address)

            # Get controller type
            self.controllerTypes.append(self.findCtrlType(self.ipcObjs[0]))

            self.sshMasterClient = SSHClientController(ipcObject = self.ipcObjs[0], logger = self.logger)

            # Init SSH client object from IPC object
            configServer = SSHConfig(ipAddress = Constants_Base.SERVER_IP, port = 22, username='smart', password='123')
            self.sshTlsServer = SSHClient(configServer, self.logger)

            # IO pin filter for
            self.ioPinList = self.testCase.resource.ioPin(resException = False)

            # Log controller details
            self.logger.newStep("Controller Details")
            self.logger.info(f"{[type(self).prefixCls]} Controller Ip :- {self.ipAddresses[0]}")
            self.logger.info(f"{[type(self).prefixCls]} Controller Type :- {self.controllerTypes[0]}")
        except Exception as Ex:
            print(Ex)

    #-------------------------------------------------------------------------------------------------------------------
    @classmethod
    def createTests(cls, testcls):
        """
        Method to create tests
        """
        logger = clsLogger(cls)
        xlsReaderObj = ConfigExlParser(configFile = Constants_Base.CONGIF_FILE_PATH_TLS, logger = logger)

        super().createTests(testcls = testcls, xlsReaderObj = xlsReaderObj)

    #-------------------------------------------------------------------------------------------------------------------
    @autobehavior
    def setUpClass(self, behavior = None, **kwargs) -> Result:
        """
        Method to setup the library content (allocated resources).

        The method can be called form the <testcase>.setUpClass() to setup all allocated resources.

        :param behavior:  Auto behavior of this method.
        :returns: Result
        """
        try:
            self.logger.newStep("setUpClass()")

            # updating release name and controller type in report file
            self.logger.newStep("Update Release Name In Report File")
            self.reportXlsObj.updateRelease(currentReleaseName = self.configXlsObj.releaseName,
                                            typeOfController = self.controllerTypes[0],
                                            sheetName = self.constants.REPORT_SHEET_TLS)

            # # Asking user if the run is a fresh run
            # freshRun = showConfirmDialog(
            #     hwnd = None,
            #     text = "Reset the Report?\n\n"
            #     "Do you want to reset result column values in report to 'Not Executed' before starting the test ?\n"
            #     "  Click 'Yes' to reset result column values in report to 'Not Executed'.\n"
            #     "  Click 'No' to keep existing values in the Report\n",
            #     caption = 'Reset the report',
            #     utype = CommonConstant.MB_YESNO)
            #
            # if freshRun == CommonConstant.IDYES:
            #     resetReportStatus = self.reportXlsObj.resetReport(sheetName = self.constants.REPORT_SHEET_TLS)
            #     if resetReportStatus:
            #         self.logger.info(
            #             "[%s] Result values in report successfully set to 'Not Executed'", type(self).prefixCls)
            #     else:
            #         self.logger.error("[%s] Failed to reset the Report", type(self).prefixCls)

            self.logger.newStep("Download Boot Project")
            relBootProjectPath = "..\\project\\plcd\\" + f"{self.controllerTypes[0]}" + "\\boot"
            self.plcProject = self.ipcObjs[0].project(relPath = relBootProjectPath, relToFile = __file__)
            self.plcProject.download(startAppl = True, log = True, reboot = True)

            self.logger.newStep("Setting Syslog Parameter to Activated")
            syslogDict = self.constants.PARAM_DICT["SYSLOG_PARAMETER"]

            # Activate  Sys Logging
            isSyslogActivated = self.setParamsUsingIPC(param = syslogDict[0],
                                                       valueToBeSet = syslogDict[1], ipcObj = self.ipcObjs[0])
            if isSyslogActivated:
                self.logger.info(f"{[type(self).prefixCls]} Syslog Parameter Set to Activated")
            else:
                self.testCase.skip(f"{[type(self).prefixCls]} Failed to set Syslog Parameter To Activated")

            # Set Log Severity to full
            isSyslogSeveritySet = self.setParamsUsingIPC(param = "0x5914:6",
                                                         valueToBeSet = "255", ipcObj = self.ipcObjs[0])
            if isSyslogSeveritySet:
                self.logger.info(f"{[type(self).prefixCls]} Log Severity increased to full")
            else:
                self.testCase.skip(f"{[type(self).prefixCls]} Failed to Log Severity increased to full")

            try:
                index = self.constants.SYSLOG_PARAMS["SERVER_IP"][0].split(':')[0]
                subIndex = self.constants.SYSLOG_PARAMS["SERVER_IP"][0].split(':')[1]

                # changing ip address to required format(little endian)
                octets = self.constants.SERVER_IP.split('.')
                # Convert each octet to its hexadecimal equivalent and combine in reverse order (little-endian)
                littleEndianHex = ''.join(format(int(octet), '02X') for octet in octets[::-1])

                # Convert the little-endian hexadecimal string to an integer
                littleEndianInt = int(littleEndianHex, 16)

                serverIpObj = self.ipcObjs[0].objByIdx(index = int(index, 16), subIndex = int(subIndex, 16))
                serverIpObj.value = littleEndianInt
                self.ipcObjs[0].cmd.paramSave()
                userSleep(2)
            except Exception as ex:
                self.logger.warning(f"{[type(self).prefixCls]} {ex}")

            Lib_TLS.SERVER_LOG_PATH = self.constants.SERVER_LOGPATH.format(self.ipAddresses[0])

            self.logger.newStep("Changing Access To Log File")
            self.sshTlsServer.connect()
            self.sshTlsServer.execute_remote_command(command = self.constants.ACCESS_TO_LOG)

            Lib_TLS.PLC_OBJ = AuditLog_PLC(logger = self.logger)

            # return no error Result object
            return Result(errorCode = Result.NO_ERROR,
                          errorMessage = "Success")

        except Exception as err:  # pylint: disable = broad-except
            self.logger.error(f"[{[type(self).prefixCls]}] Exception occurred in setupclass(). Err - {err}")

            # return error Result object
            return Result(errorCode = Result.ERROR,
                          errorMessage = err)

    #-------------------------------------------------------------------------------------------------------------------
    @property
    def startSyslog(self):
        return Lib_TLS.startSyslog.value

    #-------------------------------------------------------------------------------------------------------------------
    @startSyslog.setter
    def startSyslog(self, value):
        Lib_TLS.startSyslog.value = value

    #-------------------------------------------------------------------------------------------------------------------
    @property
    def strMessage(self):
        return Lib_TLS.strMessage.value

    #-------------------------------------------------------------------------------------------------------------------
    @strMessage.setter
    def strMessage(self, value):
        Lib_TLS.strMessage.value = value

    #-------------------------------------------------------------------------------------------------------------------
    @property
    def strUser(self):
        return Lib_TLS.strUser.value

    #-------------------------------------------------------------------------------------------------------------------
    @strUser.setter
    def strUser(self, value):
        Lib_TLS.strUser.value = value

    #-------------------------------------------------------------------------------------------------------------------
    @property
    def iMessage_Count(self):
        return Lib_TLS.iMessage_Count.value

    #-------------------------------------------------------------------------------------------------------------------
    @iMessage_Count.setter
    def iMessage_Count(self, value):
        Lib_TLS.iMessage_Count.value = value

    #-------------------------------------------------------------------------------------------------------------------
    @property
    def iMessage_idx(self):
        return Lib_TLS.iMessage_idx.value

    #-------------------------------------------------------------------------------------------------------------------
    @iMessage_idx.setter
    def iMessage_idx(self, value):
        Lib_TLS.iMessage_idx.value = value

    #-------------------------------------------------------------------------------------------------------------------
    @property
    def iMessage_idy(self):
        return Lib_TLS.iMessage_idy.value

    #-------------------------------------------------------------------------------------------------------------------
    @iMessage_idy.setter
    def iMessage_idy(self, value):
        Lib_TLS.iMessage_idy.value = value

    #-------------------------------------------------------------------------------------------------------------------
    @property
    def iMessage_idz(self):
        return Lib_TLS.iMessage_idz.value

    #-------------------------------------------------------------------------------------------------------------------
    @iMessage_idz.setter
    def iMessage_idz(self, value):
        Lib_TLS.iMessage_idz.value = value

    #-------------------------------------------------------------------------------------------------------------------
    @property
    def ui_Log_Data_Transfer_Rate(self):
        return Lib_TLS.ui_Log_Data_Transfer_Rate.value

    #-------------------------------------------------------------------------------------------------------------------
    @ui_Log_Data_Transfer_Rate.setter
    def ui_Log_Data_Transfer_Rate(self, value):
        Lib_TLS.ui_Log_Data_Transfer_Rate.value = value

    #-------------------------------------------------------------------------------------------------------------------
    @property
    def iFacility(self):
        return Lib_TLS.iFacility.value

    #-------------------------------------------------------------------------------------------------------------------
    @iFacility.setter
    def iFacility(self, value):
        Lib_TLS.iFacility.value = value

    #-------------------------------------------------------------------------------------------------------------------
    @property
    def iAuthentication(self):
        return Lib_TLS.iAuthentication.value

    #-------------------------------------------------------------------------------------------------------------------
    @iAuthentication.setter
    def iAuthentication(self, value):
        Lib_TLS.iAuthentication.value = value

    #-------------------------------------------------------------------------------------------------------------------
    @property
    def iSeverity(self):
        return Lib_TLS.iSeverity.value

    #-------------------------------------------------------------------------------------------------------------------
    @iSeverity.setter
    def iSeverity(self, value):
        Lib_TLS.iSeverity.value = value

    #-------------------------------------------------------------------------------------------------------------------
    @property
    def bTrigger_Log_Msg(self):
        return Lib_TLS.bTrigger_Log_Msg.value

    #-------------------------------------------------------------------------------------------------------------------
    @bTrigger_Log_Msg.setter
    def bTrigger_Log_Msg(self, value):
        Lib_TLS.bTrigger_Log_Msg.value = value

    #-------------------------------------------------------------------------------------------------------------------
    @property
    def bTrigger_Log_MsgIdx_1(self):
        return Lib_TLS.bTrigger_Log_MsgIdx_1.value

    #-------------------------------------------------------------------------------------------------------------------
    @bTrigger_Log_MsgIdx_1.setter
    def bTrigger_Log_MsgIdx_1(self, value):
        Lib_TLS.bTrigger_Log_MsgIdx_1.value = value

    #-------------------------------------------------------------------------------------------------------------------
    @property
    def bTrigger_Log_MsgIdx_2(self):
        return Lib_TLS.bTrigger_Log_MsgIdx_2.value

    #-------------------------------------------------------------------------------------------------------------------
    @bTrigger_Log_MsgIdx_2.setter
    def bTrigger_Log_MsgIdx_2(self, value):
        Lib_TLS.bTrigger_Log_MsgIdx_2.value = value

    #-------------------------------------------------------------------------------------------------------------------
    @property
    def bTrigger_Interval(self):
        return Lib_TLS.bTrigger_Interval.value

    #-------------------------------------------------------------------------------------------------------------------
    @bTrigger_Interval.setter
    def bTrigger_Interval(self, value):
        Lib_TLS.bTrigger_Interval.value = value

    #-------------------------------------------------------------------------------------------------------------------
    @autobehavior
    def tearDownClass(self, behavior = None, **kwargs) -> Result:
        """
        Method to cleanup the library content (used resources).

        The method can be called form the <testcase>.tearDownClass() to cleanup all used resources.

        :param behavior:  Auto behavior of this method.
        :returns: Result
        """
        Lib_TLS.PLC_OBJ
        # return no error Result object
        return Result(errorCode = Result.NO_ERROR,
                      errorMessage = "Success")

    #-------------------------------------------------------------------------------------------------------------------
    def grpSetup(self, behavior = None, **kwargs) -> None:
        """
        Setup for group
        """
        try:
            self.logger.newStep("Setup for Test Group", level = 1)
            # connect ipc 1
            self.ipcObjs[0].connect()

            self.ipcObjs[0].cmd.appStart()

            Lib_TLS.startSyslog = self.ipcObjs[0].memObj(
                                                    signalName = "Application.GVL_Pytef.bSyslogTLS_StartLog",
                                                    dataType = Boolean(), channel = self.ipcObjs[0].getDefaultChannel())

            Lib_TLS.strMessage = self.ipcObjs[0].memObj(
                                                    signalName = "Application.GVL_Pytef.strMessage",
                                                    dataType = VisibleString(),
                                                    channel = self.ipcObjs[0].getDefaultChannel())

            Lib_TLS.strUser = self.ipcObjs[0].memObj(
                                                    signalName = "Application.GVL_Pytef.strUser",
                                                    dataType = VisibleString(),
                                                    channel = self.ipcObjs[0].getDefaultChannel())

            Lib_TLS.iMessage_Count = self.ipcObjs[0].memObj(
                                                        signalName = "Application.GVL_Pytef.iMessage_Count",
                                                        dataType = Signed16(),
                                                        channel = self.ipcObjs[0].getDefaultChannel())

            Lib_TLS.iMessage_idx = self.ipcObjs[0].memObj(signalName = "Application.GVL_Pytef.iMessage_idx",
                                                          dataType = Signed16(),
                                                          channel = self.ipcObjs[0].getDefaultChannel())

            Lib_TLS.iMessage_idy = self.ipcObjs[0].memObj(signalName = "Application.GVL_Pytef.iMessage_idy",
                                                          dataType = Signed16(),
                                                          channel = self.ipcObjs[0].getDefaultChannel())

            Lib_TLS.iMessage_idz = self.ipcObjs[0].memObj(signalName = "Application.GVL_Pytef.iMessage_idz",
                                                          dataType = Signed16(),
                                                          channel = self.ipcObjs[0].getDefaultChannel())

            Lib_TLS.ui_Log_Data_Transfer_Rate = self.ipcObjs[0].memObj(
                signalName = "Application.GVL_Pytef.ui_Log_Data_Transfer_Rate",
                dataType = Signed16(), channel = self.ipcObjs[0].getDefaultChannel())

            Lib_TLS.iFacility = self.ipcObjs[0].memObj(signalName = "Application.GVL_Pytef.iFacility",
                                                       dataType = Signed32(),
                                                       channel = self.ipcObjs[0].getDefaultChannel())

            Lib_TLS.iAuthentication = self.ipcObjs[0].memObj(
                signalName = "Application.GVL_Pytef.iAuthentication",
                dataType = Signed32(), channel = self.ipcObjs[0].getDefaultChannel())

            Lib_TLS.iSeverity = self.ipcObjs[0].memObj(signalName = "Application.GVL_Pytef.iSeverity",
                                                       dataType = Signed32(),
                                                       channel = self.ipcObjs[0].getDefaultChannel())

            Lib_TLS.bTrigger_Log_Msg = self.ipcObjs[0].memObj(
                signalName = "Application.GVL_Pytef.bTrigger_Log_Msg",
                dataType = Boolean(), channel = self.ipcObjs[0].getDefaultChannel())

            Lib_TLS.bTrigger_Log_MsgIdx_1 = self.ipcObjs[0].memObj(
                                                            signalName = "Application.GVL_Pytef.bTrigger_Log_MsgIdx_1",
                                                            dataType = Boolean(),
                                                            channel = self.ipcObjs[0].getDefaultChannel())

            Lib_TLS.bTrigger_Log_MsgIdx_2 = self.ipcObjs[0].memObj(
                                                            signalName = "Application.GVL_Pytef.bTrigger_Log_MsgIdx_2",
                                                            dataType = Boolean(),
                                                            channel = self.ipcObjs[0].getDefaultChannel())

            Lib_TLS.bTrigger_Interval = self.ipcObjs[0].memObj(
                signalName = "Application.GVL_Pytef.bTrigger_Interval",
                dataType = Boolean(), channel = self.ipcObjs[0].getDefaultChannel())

            # disconnect ipc 1
            self.ipcObjs[0].disconnect()

            self.logger.newStep("Group setup is successful", level = 1)
            return True

        except Exception as exc:
            self.logger.error(f"Exception occurred in group setup :- {exc}")
            return False

    #-------------------------------------------------------------------------------------------------------------------
    def emptyOldLogs(self) -> None:
        """
        This method is used to empty the contents of logs .
        """
        try:
            # Log the start of the log deletion process
            self.logger.newStep("Emptying/Clearing Previous Logs of Controller")
            try:
                # Establish connection to the remote controller using SSH
                self.sshMasterClient.connect()
                self.sshTlsServer.connect()

                # List all files in the specified remote directory
                fileListController = self.sshMasterClient.list_remote_directory(
                    remote_path = self.constants.CONTROLLER_LOG_PATH)
                self.logger.info(f"Files in folder - {fileListController}")

                logFiles = [flName for flName in fileListController if flName.endswith(".log")]
                # Iterate through the list of files and delete them one by one
                for flname in logFiles :
                    # Construct the full remote file path
                    remote_path = self.constants.CONTROLLER_LOG_PATH + flname
                    self.logger.info(f"File to empty - {remote_path}")

                    # Delete the file from the remote directory
                    self.sshMasterClient.change_remote_file_content(remote_path = remote_path,
                                                                    new_content = "",
                                                                    overWrite = True)

                # emptying linux server log
                self.logger.newStep("Emptying Server Logs")
                self.sshTlsServer.change_remote_file_content(remote_path = Lib_TLS.SERVER_LOG_PATH,
                                                             new_content = "",
                                                             overWrite = True)

                # Disconnect from the remote server after deletion
                self.sshMasterClient.disconnect()
                self.sshTlsServer.disconnect()
            except Exception as exc:
                # Log any exception that occurs while deleting log files
                self.logger.error(f"Exception Occurred in deleting old log files: {exc}")
        except Exception:
            # Log any unexpected exceptions in the outer try block
            self.logger.error("Exception Occurred in deleting old log files")

    #-------------------------------------------------------------------------------------------------------------------
    def verifyLogs(self, logType, validationType, detailsToCheck, logsNotPresent = None, extSSHClient = None) -> bool:
        """
        Verifies log files based on provided details to check.
        """

        # Initialize the verification result as True
        vertificationResult = True

        sshClient = self.sshMasterClient

        remote_path = self.constants.LOG_FILES[logType]

        if extSSHClient:
            sshClient = extSSHClient
            remote_path = Lib_TLS.SERVER_LOG_PATH

        # Establish SSH connection
        sshClient.connect()

        timeOut = 10
        self.logger.newStep(f"Waiting for {timeOut}sec for {logType} to generated in controller...")
        timeCount = 0
        while timeCount < timeOut:
            if sshClient.check_remote_file_exists(remote_path = remote_path):
                self.logger.info(f"{logType} is generated in controller...")
                break

            userSleep(1)
            timeCount += 1
            self.logger.info(f"Waiting for {timeOut - timeCount}sec {logType} to be generated in controller...")
        else:
            self.logger.error(f"{logType} NOT generated in controller...")

        # Get the current test case name from the stack trace
        stackList = traceback.extract_stack()
        testCase = re.match(r".*test_(Grp_\d+_.*)_\w+-\d+", self.testCase.testCaseName).group(1).lower()
        currentTestCase = [
            stackObj for stackObj in stackList if testCase in stackObj.name or 'testCase' in stackObj.name][0].name

        # Start logging the step for verifying logs
        self.logger.newStep("Verifying Logs", level = 1)
        # Check if the local folder for storing logs is created
        self.logger.newStep("Creating Directory For Storing Logs Locally")
        if Lib_TLS.SYSTEM_LOGS_FOLDER_CREATED:
            # Folder is already created
            self.logger.info(f"{[type(self).prefixCls]} Local Log folder is already present")
        else:
            # Create a new folder for storing logs locally
            Lib_TLS.SYSTEM_LOGS_FOLDER_CREATED = '_'.join(
                str(datetime.now()).split()).split('.')[0].replace(":", "_")
            Lib_TLS.SYSTEM_LOGS_FOLDER_CREATED = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                self.constants.SYSTEM_LOG_PATH,
                Lib_TLS.SYSTEM_LOGS_FOLDER_CREATED)
            self.logger.info(f"{[type(self).prefixCls]} Creating folder named :- "
                             f"{Lib_TLS.SYSTEM_LOGS_FOLDER_CREATED}")
            os.makedirs(Lib_TLS.SYSTEM_LOGS_FOLDER_CREATED)

        # Initialize a set to store details found during validation
        detailsFound = set()

        logFile = None
        if logType == self.constants.SERVER_LOG:
            logFile = self.constants.LOG_FILES[logType].format(self.ipAddresses[0])
        else:
            logFile = self.constants.LOG_FILES[logType].split(self.constants.CONTROLLER_LOG_PATH)[1]

        self.logger.newStep(f"Copying and Validating Logs :- {[logFile]}")

        # Create the local path for storing the copied log file
        self.logger.newStep("Copy controller log to Local:", level = 3)
        logPath = os.path.join(Lib_TLS.SYSTEM_LOGS_FOLDER_CREATED,
                               '_'.join([self.testCase.testCaseName, currentTestCase, logFile]))

        if logType == self.constants.SERVER_LOG:
            duplicateFile = 1
            while True:
                if os.path.exists(logPath):
                    logFile = logFile.split('.txt')[0].split('_')[0] + "_" + str(duplicateFile) + '.txt'
                    logPath = os.path.join(Lib_TLS.SYSTEM_LOGS_FOLDER_CREATED,
                                           '_'.join([self.testCase.testCaseName, currentTestCase, logFile]))
                else:
                    break
                duplicateFile = duplicateFile + 1

        # Copy the remote log file to the local directory
        sshClient.copy_file_to_local(remote_path, logPath)

        # Parse the log file using a suitable parser
        self.logger.newStep("Parsing Logs", level = 3)
        logObj = Factory_Log_Parser().create_parser(logType = logType, logPath = logPath)

        # Validate the details in the log file
        self.logger.newStep(f"Validating details in {logPath}", level = 3)
        for detail in detailsToCheck:
            matchingLine = logObj.validateLogFileData(validationType = validationType, result = detail)
            if matchingLine:
                # Log found details
                matchingLine = matchingLine.replace('\n', '')
                detailsFound.add(matchingLine)
                self.logger.info(f"{[type(self).prefixCls]} FOUND '{matchingLine}' in {logFile}")
            else:
                # Log missing details
                self.logger.error(f"{[type(self).prefixCls]} '{detail}' NOT FOUND in {logFile}")

        if logsNotPresent:
            for logMsg in logsNotPresent:
                matchingLine = logObj.validateLogFileData(validationType = validationType, result = logMsg)
                if matchingLine:
                    # Log found details
                    matchingLine = matchingLine.replace('\n', '')
                    detailsFound.add(matchingLine)
                    self.logger.error(f"{[type(self).prefixCls]} FOUND '{matchingLine}' in {logFile}")
                    return False
                else:
                    # Log missing details
                    self.logger.info(f"{[type(self).prefixCls]} '{logMsg}' NOT FOUND in {logFile}")

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
    def verifyLogsRepeatability(self, logType, detail) -> int:
        """
        Verifies log files based on provided details to check for repeatability.

        Args:
            logType (str): The type of log to verify (e.g., LOCAL_LOG).
            detail (dict): The details to check within the log files.

        Returns:
            int: The total count of log messages that match the provided details.

        The method performs the following actions:
        1. Connects to the remote server via SSH.
        2. Scans and collects log files based on the specified log type.
        3. Checks if the log folder is already created; if not, creates a new log folder.
        4. Copies the log files locally and validates the log messages for repeatability.
        5. Disconnects from the remote server.
        """

        # Wait for 5 mins to refresh the log service in the controller (As confirmed by System Team)
        timeOut = 10
        self.logger.newStep(f"Waiting for {timeOut}sec for {logType} to generated in controller...")
        timeCount = 0
        while timeCount < timeOut:
            if self.sshMasterClient.check_remote_file_exists(
                    remote_path = self.constants.LOG_FILES[logType]):
                self.logger.info(f"{logType} is generated in controller...")
                break

            userSleep(1)
            timeCount += 1
            self.logger.info(f"Waiting for {timeOut - timeCount}sec {logType} to be generated in controller...")
        else:
            self.logger.error(f"{logType} NOT generated in controller...")

        # Establish connection with the remote server via SSH
        self.sshMasterClient.connect()

        # Log the start of the process for verifying logs
        self.logger.newStep("Verifying Logs")

        logFile = self.constants.LOG_FILES[logType].split(self.constants.CONTROLLER_LOG_PATH)[1]

        # Get the current test case name from the stack trace
        stackList = traceback.extract_stack()
        testCase = re.match(r".*test_(Grp_\d+_.*)_\w+-\d+", self.testCase.testCaseName).group(1).lower()
        currentTestCase = [
            stackObj for stackObj in stackList if testCase in stackObj.name or 'testCase' in stackObj.name][0].name

        # Check if the log folder for storing logs locally has been created
        if Lib_TLS.SYSTEM_LOGS_FOLDER_CREATED:
            self.logger.info(f"{[type(self).prefixCls]} Log folder is already present")
        else:
            # Create a new folder for storing logs locally
            Lib_TLS.SYSTEM_LOGS_FOLDER_CREATED = '_'.join(
                str(datetime.now()).split()).split('.')[0].replace(":", "_")

            Lib_TLS.SYSTEM_LOGS_FOLDER_CREATED = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                self.constants.SYSTEM_LOG_PATH,
                Lib_TLS.SYSTEM_LOGS_FOLDER_CREATED)

            self.logger.info(f"{[type(self).prefixCls]} Creating folder named :- "
                             f"{Lib_TLS.SYSTEM_LOGS_FOLDER_CREATED}")

            os.makedirs(Lib_TLS.SYSTEM_LOGS_FOLDER_CREATED)

        # Construct the local path for storing the log file
        validFilePath = re.sub(self.constants.INVALID_FOLDER_SYMBOLS, self.constants.REPLACE_INVALID_SYMBOL, logFile)
        logPath = os.path.join(Lib_TLS.SYSTEM_LOGS_FOLDER_CREATED,
                               '_'.join([self.testCase.testCaseName, currentTestCase, validFilePath]))

        # Copy the log file from the remote server to the local machine
        self.sshMasterClient.copy_file_to_local(self.constants.LOG_FILES[logType], logPath)

        # Parse the copied log file using the appropriate parser
        logObj = Factory_Log_Parser().create_parser(logType = logType, logPath = logPath)

        # Log the validation process
        self.logger.info(f"{[type(self).prefixCls]} Validating log messages generated in files")

        # Validate the log messages for repeatability and accumulate the count
        logList = logObj.validateLogMessageRepitability(result = detail)
        totalCount = len(logList)

        # Log the total count of matching log messages found
        self.logger.info(f"{[type(self).prefixCls]} '{detail}' was found '{totalCount}' times in Log")

        # Disconnect from the remote server
        self.sshMasterClient.disconnect()

        # Return the total count of matching log messages
        return totalCount

    #-------------------------------------------------------------------------------------------------------------------
    def setSyslogParams(self, protocol : str, encryption : str, port : str) -> None:
        """
        This method is used to set the syslog parameters value
        """
        try:
            self.logger.newStep("Setting Syslog Parameters")

            # step 3 : setting encryption
            self.logger.newStep("Setting Encryption", level = 3)
            self.setParamsUsingIPC(param = self.constants.SYSLOG_PARAMS["ENCRYPTION"][0],
                                   valueToBeSet = encryption,
                                   ipcObj = self.ipcObjs[0])

            # step 1 : setting port
            self.logger.newStep("Setting Port", level = 3)
            self.setParamsUsingIPC(param = self.constants.SYSLOG_PARAMS["PORT"][0],
                                   valueToBeSet = port,
                                   ipcObj = self.ipcObjs[0])

            # step 2 : setting protocol
            self.logger.newStep("Setting Protocol", level = 3)
            self.setParamsUsingIPC(param = self.constants.SYSLOG_PARAMS["PROTOCOL"][0],
                                   valueToBeSet = protocol,
                                   ipcObj = self.ipcObjs[0])

        except Exception:
            # Log any unexpected exceptions in the outer try block
            self.logger.error("Exception Occurred in setSyslogParams")

    #-------------------------------------------------------------------------------------------------------------------
    def verifySyslogParams(self, expectedProtocol : str, expectedEncryption : str, expectedPort : str) -> bool:
        """
        This method is used to verify if the syslog parameter values are entered successfully
        """
        try:
            self.logger.newStep("Verifying Syslog Parameters")

            # step 1 : checking port
            self.logger.newStep("Verifying Port", level = 3)
            portReadValue = self.readParamUsingIPC(param = self.constants.SYSLOG_PARAMS["PORT"][0],
                                                   ipcObj = self.ipcObjs[0])
            portReadValue = portReadValue[self.constants.SYSLOG_PARAMS["PORT"][0]]['value']
            if portReadValue == expectedPort:
                self.logger.info(f"{[type(self).prefixCls]} Port Value is set successfully :- {expectedPort}")
            else:
                self.logger.error(f"{[type(self).prefixCls]} Port Value is NOT set successfully")
                self.logger.error(f"{[type(self).prefixCls]} Expected :- {expectedPort} Found :- {portReadValue}")
                return False

            # step 2 : checking protocol
            self.logger.newStep("Verifying Protocol", level = 3)
            protocolReadValue = self.readParamUsingIPC(param = self.constants.SYSLOG_PARAMS["PROTOCOL"][0],
                                                       ipcObj = self.ipcObjs[0])
            protocolReadValue = protocolReadValue[self.constants.SYSLOG_PARAMS["PROTOCOL"][0]]['message']
            if expectedProtocol in protocolReadValue:
                self.logger.info(f"{[type(self).prefixCls]} Protocol Value is set successfully :- {expectedProtocol}")
            else:
                self.logger.error(f"{[type(self).prefixCls]} Protocol Value is NOT set successfully")
                self.logger.error(
                    f"{[type(self).prefixCls]} Expected :- {expectedProtocol} Found :- {protocolReadValue}")
                return False

            # step 3 : checking encryption
            self.logger.newStep("Verifying Encryption", level = 3)
            encryptionReadValue = self.readParamUsingIPC(param = self.constants.SYSLOG_PARAMS["ENCRYPTION"][0],
                                                         ipcObj = self.ipcObjs[0])
            encryptionReadValue = encryptionReadValue[self.constants.SYSLOG_PARAMS["ENCRYPTION"][0]]['value']
            if str(encryptionReadValue) == expectedEncryption:
                self.logger.info(
                    f"{[type(self).prefixCls]} Encryption Value is set successfully :- {expectedEncryption}")
            else:
                self.logger.error(f"{[type(self).prefixCls]} Encryption Value is NOT set successfully")
                self.logger.error(
                    f"{[type(self).prefixCls]} Expected :- {expectedEncryption} Found :- {encryptionReadValue}")
                return False

            return True
        except Exception:
            # Log any unexpected exceptions in the outer try block
            self.logger.error("Exception Occurred in verifySyslogParams")
            return False

    #-------------------------------------------------------------------------------------------------------------------
    def compareMessagesInLogs(self, firstLogType: str, secondLogType: str, logMessage: str,
                              SSHClientFirst= None, SSHClientSecond= None) -> bool:
        """
        This method is used to verify if the syslog parameter values are entered successfully.

        Parameters:
        firstLogType (str): The type of the first log to check.
        secondLogType (str): The type of the second log to check.
        logMessage (str): The log message to verify.
        SSHClientFirst (Optional[SSHClient]): SSH client for the first log type, default is None.
        SSHClientSecond (Optional[SSHClient]): SSH client for the second log type, default is None.

        Returns:
        bool: True if the log message is present in both logs, False otherwise.
        """
        try:
            # Verify logs for the first log type
            presentOnFirst = self.verifyLogs(logType=firstLogType, validationType=Validate_Data.LOG_MESSAGE,
                                             detailsToCheck=logMessage, extSSHClient=SSHClientFirst)

            # Verify logs for the second log type
            presentOnSecond = self.verifyLogs(logType=secondLogType, validationType=Validate_Data.LOG_MESSAGE,
                                              detailsToCheck=logMessage, extSSHClient=SSHClientSecond)

            # Check if logs are present on both log types
            if presentOnFirst and presentOnSecond:
                self.logger.info(f"Logs are present on both {firstLogType} and {secondLogType}")
                return True

            # Check if logs are present only on the first log type
            if presentOnFirst and not presentOnSecond:
                self.logger.error(f"Logs are present on {firstLogType} but NOT on {secondLogType}")
                return False

            # Check if logs are present only on the second log type
            if presentOnSecond and not presentOnFirst:
                self.logger.error(f"Logs are present on {secondLogType} but NOT on {firstLogType}")
                return False

            # Logs are not present on both log types
            self.logger.error(f"Logs are NOT present on both {firstLogType} and {secondLogType}")
            return False
        except Exception:
            # Log any unexpected exceptions in the outer try block
            self.logger.error("Exception Occurred in compareMessagesInLogs()")
            return False

    #-------------------------------------------------------------------------------------------------------------------
    def compareLatestMessageTimestampInLogs(self, firstLogType, secondLogType, SSHClientFirst, SSHClientSecond) -> bool:
        """
        This method compares the timestamps of the latest log messages in two different log types.

        Parameters:
        firstLogType (str): The type of the first log to check.
        secondLogType (str): The type of the second log to check.
        SSHClientFirst (SSHClient): SSH client for the first log type.
        SSHClientSecond (SSHClient): SSH client for the second log type.

        Returns:
        bool: True if the latest log messages in both logs have the same timestamp, False otherwise.
        """
        try:
            # connecting second client
            SSHClientSecond.connect()

            self.ipcObjs[0].cmd.appStart()
            self.ipcObjs[0].cmd.appStop()

            # finding latest log time of linux server log
            self.logger.newStep(f"Finding time of the latest log generated in {secondLogType} logs")
            serverLogPath = os.path.join(
                Lib_TLS.SYSTEM_LOGS_FOLDER_CREATED,
                '_'.join([self.testCase.testCaseName, self.constants.LOG_FILES[secondLogType].format(
                    self.ipAddresses[0])])
            )
            SSHClientSecond.copy_file_to_local(Lib_TLS.SERVER_LOG_PATH, serverLogPath)

            serverLogObj = Factory_Log_Parser().create_parser(
                logType = secondLogType,
                logPath = serverLogPath
            )
            latestLogGeneratedTime = serverLogObj.latestLogTimestamp()
            serverLogtime = latestLogGeneratedTime
            serverLogtime = serverLogtime.rsplit('.', 1)[0]
            self.logger.info(f"[{type(self).prefixCls}] {secondLogType} Time found :- {serverLogtime}")

            # connecting first client
            SSHClientFirst.connect()

            # Copy the latest log file from the controller to the local machine
            self.logger.newStep(f"Finding time of the latest log generated in {firstLogType} logs")
            logPath = os.path.join(
                Lib_TLS.SYSTEM_LOGS_FOLDER_CREATED,
                '_'.join([self.testCase.testCaseName,
                          self.constants.LOG_FILES[firstLogType].split(self.constants.CONTROLLER_LOG_PATH)[1]])
            )

            SSHClientFirst.copy_file_to_local(self.constants.LOG_FILES[firstLogType], logPath)

            logObj = Factory_Log_Parser().create_parser(
                logType = firstLogType,
                logPath = logPath
            )
            # finding latest log time of linux server log
            latestLogGeneratedTime = logObj.latestLogTimestamp()
            firstLogTime = latestLogGeneratedTime
            firstLogTime = firstLogTime.rsplit('.', 1)[0]
            self.logger.newStep(f"[{type(self).prefixCls}] {firstLogType} Time found :- {firstLogTime}")

            if serverLogtime == firstLogTime:
                self.logger.info(f"[{type(self).prefixCls}] Both logs have SAME time stamp")
                return True
            else:
                self.logger.error(f"[{type(self).prefixCls}] Both logs have DIFFERENT time stamp")
                return False
        except Exception:
            # Log any unexpected exceptions in the outer try block
            self.logger.error("Exception Occurred in verifySyslogParams")
            return False

    #-------------------------------------------------------------------------------------------------------------------
    def checkLogsPostReconnect(self) -> bool:
        """
        This method checks the logs after reconnecting by setting parameters, starting and stopping the application,
        and comparing log messages between local and server logs.

        Returns:
        bool: True if the log messages are present in both logs, False otherwise.
        """
        try:
            # Retrieve syslog parameters from self.constants
            syslogDict = self.constants.PARAM_DICT["SYSLOG_PARAMETER"]

            # Set parameters using IPC
            self.setParamsUsingIPC(param=syslogDict[0], valueToBeSet=syslogDict[1], ipcObj=self.ipcObjs[0])

            # Start and stop the application to generate logs
            self.ipcObjs[0].cmd.appStart()
            self.ipcObjs[0].cmd.appStop()

            # Compare log messages between local and server logs
            return self.compareMessagesInLogs(
                firstLogType=self.constants.LOCAL_LOG_0,
                secondLogType=self.constants.SERVER_LOG,
                logMessage=self.constants.LOG_DICTIONARY[self.constants.LOCAL_LOG_0]["startStopApp"],
                SSHClientSecond=self.sshTlsServer
            )
        except Exception:
            # Log any unexpected exceptions in the outer try block
            self.logger.exception(f"{[type(self).prefixCls]} Exception Occurred in checkLogsPostReconnectUDP()")
            return False

    #-------------------------------------------------------------------------------------------------------------------
    def verifyLogCountSync(self, firstLogType: str, secondLogType: str,
                           SSHClientFirst: SSHClient, SSHClientSecond: SSHClient) -> bool:
        """
        This method verifies if the number of log messages in two different log types are synchronized.

        Parameters:
        firstLogType (str): The type of the first log to check.
        secondLogType (str): The type of the second log to check.
        SSHClientFirst (SSHClient): SSH client for the first log type.
        SSHClientSecond (SSHClient): SSH client for the second log type.

        Returns:
        bool: True if the number of log messages in both logs are the same, False otherwise.
        """
        try:
            # Connecting to the second client
            SSHClientSecond.connect()

            # Performing delete logbook to generate log and compare time stamp
            self.ipcObjs[0].cmd.logBookDelete()

            # Finding the number of logs in the Linux server log
            self.logger.newStep(f"Finding number of logs in {secondLogType} file")
            serverLogPath = os.path.join(
                Lib_TLS.SYSTEM_LOGS_FOLDER_CREATED,
                '_'.join([self.testCase.testCaseName, self.constants.LOG_FILES[secondLogType].format(
                    self.ipAddresses[0])])
            )
            SSHClientSecond.copy_file_to_local(Lib_TLS.SERVER_LOG_PATH, serverLogPath)

            serverLogObj = Factory_Log_Parser().create_parser(
                logType=secondLogType,
                logPath=serverLogPath
            )
            totalLogMessagesServer = serverLogObj.total_log_messages()
            self.logger.newStep(f"[{type(self).prefixCls}] number of logs in server logs :- {totalLogMessagesServer}")

            # Connecting to the first client
            SSHClientFirst.connect()

            # Finding the number of logs in the first log type
            self.logger.newStep(f"Finding number of logs in {firstLogType} file")
            logPath = os.path.join(
                Lib_TLS.SYSTEM_LOGS_FOLDER_CREATED,
                '_'.join([self.testCase.testCaseName,
                          self.constants.LOG_FILES[firstLogType].split(self.constants.CONTROLLER_LOG_PATH)[1]])
            )

            SSHClientFirst.copy_file_to_local(self.constants.LOG_FILES[firstLogType], logPath)

            logObj = Factory_Log_Parser().create_parser(
                logType=firstLogType,
                logPath=logPath
            )
            totalLogMessagesController = logObj.total_log_messages()
            self.logger.newStep(f"[{type(self).prefixCls}] number of logs in controller logs :- "
                                f"{totalLogMessagesController}")

            # Comparing the number of log messages
            if totalLogMessagesController == totalLogMessagesServer:
                self.logger.info(f"[{type(self).prefixCls}] Both logs have SAME number of logs")
                return True
            else:
                self.logger.error(f"[{type(self).prefixCls}] Both logs have DIFFERENT number of logs")
                return False
        except Exception:
            # Log any unexpected exceptions in the outer try block
            self.logger.exception(f"{[type(self).prefixCls]} Exception Occurred in checkLogsPostReconnectUDP()")
            return False

    #-------------------------------------------------------------------------------------------------------------------
    def verifySeverities(self, severities: List[str]) -> bool:
        """
        This method verifies if the log severities are correctly set and logs are generated accordingly.

        Parameters:
        severities (List[str]): A list of severities to verify.

        Returns:
        bool: True if the log severities are correctly set and logs are generated as expected, False otherwise.
        """
        try:
            for severity in severities:
                # Connecting to the TLS server
                self.sshTlsServer.connect()

                self.logger.newStep(f"Verifying For {severity} severity")

                # Clear the content of the server log
                self.logger.newStep("Clear content of server log file", level=3)
                self.sshTlsServer.change_remote_file_content(
                    remote_path=Lib_TLS.SERVER_LOG_PATH, new_content="", overWrite=True)

                # Set Syslog log severity to "None"
                self.logger.newStep("Set Syslog log severity to None", level=3)
                isSyslogActivated = self.setParamsUsingIPC(param="0x5914:6", valueToBeSet="00", ipcObj=self.ipcObjs[0])
                if isSyslogActivated:
                    self.logger.info(f"{[type(self).prefixCls]} Log Severity set to {severity}")
                else:
                    self.testCase.skip(f"{[type(self).prefixCls]} Failed to set Log Severity to {severity}")
                    self.sshTlsServer.disconnect()
                    return False

                self.logger.newStep("Setting Flag of 'bSyslogTLS_StartLog' to True")
                self.startSyslog = True

                userSleep(3)

                logsNotPresent = []
                for toBeAddedSeverity in self.constants.SYSLOG_SEVERITY_LIST:
                    if severity == toBeAddedSeverity:
                        continue
                    logsNotPresent.append(self.constants.LOG_DICTIONARY[self.constants.USER_LOG][
                        self.constants.SEVERITIES_MESSAGE_KEYS[toBeAddedSeverity]][0])

                # Verify logs when all severities are off
                if self.verifyLogs(logType=self.constants.SERVER_LOG, validationType = Validate_Data.LOG_MESSAGE,
                                   detailsToCheck = self.constants.LOG_DICTIONARY[self.constants.USER_LOG][
                                       self.constants.SEVERITIES_MESSAGE_KEYS[severity]],
                                   extSSHClient = self.sshTlsServer):
                    self.logger.error(
                        f"{[type(self).prefixCls]} {severity} Log Generated even when all severities are off")
                    self.sshTlsServer.disconnect()
                    return False

                # Set Syslog log severity to the current severity
                self.logger.newStep(f"Set Syslog log severity to {severity}", level=3)
                isSyslogActivated = self.setParamsUsingIPC(param="0x5914:6",
                                                           valueToBeSet=self.constants.SEVERITIES_VALUES[severity],
                                                           ipcObj=self.ipcObjs[0])
                if isSyslogActivated:
                    self.logger.info(f"{[type(self).prefixCls]} Log Severity set to {severity}")
                else:
                    self.testCase.skip(f"{[type(self).prefixCls]} Failed to set Log Severity to {severity}")
                    self.sshTlsServer.disconnect()
                    return False

                self.logger.newStep("Setting Flag of 'bSyslogTLS_StartLog' to True")
                self.startSyslog = True

                userSleep(3)

                # Verify logs for the current severity
                if not self.verifyLogs(logType=self.constants.SERVER_LOG, validationType=Validate_Data.LOG_MESSAGE,
                                       detailsToCheck=self.constants.LOG_DICTIONARY[self.constants.USER_LOG][
                                           self.constants.SEVERITIES_MESSAGE_KEYS[severity]],
                                       logsNotPresent = logsNotPresent,
                                       extSSHClient=self.sshTlsServer):
                    self.logger.error(f"{[type(self).prefixCls]} {severity} Log NOT generated in User Logs")
                    return False

            # emptying linux server log
            self.logger.newStep("Emptying Server Logs")
            self.sshTlsServer.connect()
            self.sshTlsServer.change_remote_file_content(remote_path = Lib_TLS.SERVER_LOG_PATH,
                                                         new_content = "", overWrite = True)

            return True
        except Exception:
            self.logger.exception(f"{[type(self).prefixCls]} Exception Occurred in verifySeverities()")
            return False

    #-------------------------------------------------------------------------------------------------------------------
    def verifyFirmwareServicesLog(self, firstLogType: str, secondLogType: str,
                                  SSHClientFirst: Optional[SSHClient] = None,
                                  SSHClientSecond: Optional[SSHClient] = None) -> bool:
        """
        This method verifies the firmware services log by using the Firmware Loader tool to connect to the device
        and then comparing log messages between two different log types.

        Parameters:
        firstLogType (str): The type of the first log to check.
        secondLogType (str): The type of the second log to check.
        SSHClientFirst (Optional[SSHClient]): SSH client for the first log type, default is None.
        SSHClientSecond (Optional[SSHClient]): SSH client for the second log type, default is None.

        Returns:
        bool: True if the log messages are present in both logs, False otherwise.
        """
        try:
            # Initialize the Firmware Loader
            firmwareLoader = EasyStarterFirmware(logger=self.logger)

            # Use Firmware Loader for device connection
            deviceDict = {self.constants.DEVICE[self.controllerTypes[0]]: (
                "Firmware", "Controller", self.constants.DEVICE[self.controllerTypes[0]],
                self.constants.DEVICE_AND_VERSION[self.controllerTypes[0]].format(self.configXlsObj.controllerFWVersion),
                self.constants.DEVICE_AND_VERSION[self.controllerTypes[0]].format(self.configXlsObj.controllerFWVersion),
                self.configXlsObj.controllerFWVersion)}

            self.logger.newStep("Starting Firmware Loader Tool")
            firmwareLoader.openEasyStarterFirmwareTool(esversion=self.configXlsObj.firmwareLoaderVersion)
            self.logger.newStep("Selecting Firmware and connecting firmware loader tool")
            firmwareLoader.connectDevice(deviceDict=deviceDict, ipAddress=self.ipAddresses[0])
            firmwareLoader.closeEasyStarterFirmwareTool()

            # Compare log messages between local and server logs
            return self.compareMessagesInLogs(
                firstLogType=firstLogType,
                secondLogType=secondLogType,
                logMessage=self.constants.LOG_DICTIONARY[self.constants.LOCAL_LOG_0]["easyStarterConnectDisconnect"],
                SSHClientFirst=SSHClientFirst,
                SSHClientSecond=SSHClientSecond
            )
        except Exception:
            # Log any unexpected exceptions in the outer try block
            self.logger.exception(f"{[type(self).prefixCls]} Exception Occurred in checkLogsPostReconnectUDP()")
            return False

    #-------------------------------------------------------------------------------------------------------------------
    def verifyThirdPartyClient(self, firstLogType: str, secondLogType: str,
                               SSHClientFirst: Optional[SSHClient] = None,
                               SSHClientSecond: Optional[SSHClient] = None) -> bool:
        """
        This method verifies the log messages related to a Python 3rd Party Client session by occupying the session
        and then comparing log messages between two different log types.

        Parameters:
        firstLogType (str): The type of the first log to check.
        secondLogType (str): The type of the second log to check.
        SSHClientFirst (Optional[SSHClient]): SSH client for the first log type, default is None.
        SSHClientSecond (Optional[SSHClient]): SSH client for the second log type, default is None.

        Returns:
        bool: True if the log messages are present in both logs, False otherwise.
        """
        try:
            # Step 1: Occupy a Python 3rd Party Client session
            self.logger.newStep("Occupying Python 3rd Party Client Session")
            self.occupyPython3rdPartySession(ipAddress=self.ipAddresses[0])

            # Compare log messages between local and server logs
            return self.compareMessagesInLogs(
                firstLogType=firstLogType,
                secondLogType=secondLogType,
                logMessage=self.constants.LOG_DICTIONARY[self.constants.LOCAL_LOG_0]["3rdPartyClientConnectDisconnect"],
                SSHClientFirst=SSHClientFirst,
                SSHClientSecond=SSHClientSecond
            )
        except Exception:
            # Log any unexpected exceptions in the outer try block
            self.logger.exception(f"{[type(self).prefixCls]} Exception Occurred in checkLogsPostReconnectUDP()")
            return False

    #---------------------------------------------------------------------------------------------------
    def generate_random_string(self, length=255):
        '''
        Generate Random String
        '''
        # Generate a random string of specified length
        random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=length))
        return random_string

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def common_testCase_01(self, protocol, encryption, port) -> bool:
        """
        TC2.0: Verify activation of SyslogClient with UDP connection to communicate with Syslog server.
        """
        try:
            self.logger.newStep(
                f"Executing test cases with protocol: {protocol}, encryption: {encryption}, port: {port}")
            # verifying syslog paramaeters
            if not self.verifySyslogParams(expectedProtocol = protocol,
                                           expectedEncryption = encryption,
                                           expectedPort = port):
                self.logger.error(f"[{type(self).prefixCls}] Verification Failed...Test Failed")
                return False

            # Deactivate Sys Log
            syslogDict = self.constants.PARAM_DICT["SYSLOG_PARAMETER"]
            self.setParamsUsingIPC(param = syslogDict[0],
                                   valueToBeSet = '0', ipcObj = self.ipcObjs[0])

            # Activate Sys Log
            self.setParamsUsingIPC(param = syslogDict[0],
                                   valueToBeSet = syslogDict[1], ipcObj = self.ipcObjs[0])

            # performing start application so as to generate proper logs
            self.ipcObjs[0].cmd.appStart()

            logGenerationResult = False
            retryTimer = self.constants.RETRY_TIMER
            while retryTimer:
                logGenerationResult = logGenerationResult or (self.verifyLogs(
                    logType = self.constants.SERVER_LOG, validationType = Validate_Data.LOG_MESSAGE,
                    detailsToCheck = self.constants.LOG_DICTIONARY[self.constants.SERVER_LOG]['startLogging'],
                    extSSHClient = self.sshTlsServer
                ) or self.verifyLogs(
                    logType = self.constants.SERVER_LOG, validationType = Validate_Data.LOG_MESSAGE,
                    detailsToCheck = self.constants.LOG_DICTIONARY[self.constants.SERVER_LOG]['restartSyslogging'],
                    extSSHClient = self.sshTlsServer
                ))
                if logGenerationResult:
                    break
                userSleep(30)
                retryTimer = retryTimer - 30

            return logGenerationResult
        except Exception:
            self.logger.exception("Exception Occurred in TestCase 2")
            return False

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def common_testCase_02(self) -> bool:
        """
        TC3.0: Verify that the timestamp of log messages received by the external server matches those sent by
        SyslogClient.
        """
        try:
            return self.compareLatestMessageTimestampInLogs(firstLogType = self.constants.LOCAL_LOG_0,
                                                            secondLogType = self.constants.SERVER_LOG,
                                                            SSHClientFirst = self.sshMasterClient,
                                                            SSHClientSecond = self.sshTlsServer)
        except Exception:
            self.logger.exception("Exception Occurred in TestCase 3")
            return False

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def common_testCase_03(self) -> bool:
        """
        TC4.0: Verify that the number of logs received by the external server matches the number sent by
        SyslogClient within a specific time period using.
        """
        try:
            # performing delete logbook to generate log and compare time stamp
            self.ipcObjs[0].cmd.logBookDelete()

            return self.verifyLogCountSync(firstLogType = self.constants.LOCAL_LOG_0,
                                           secondLogType = self.constants.SERVER_LOG,
                                           SSHClientFirst = self.sshMasterClient,
                                           SSHClientSecond = self.sshTlsServer)

        except Exception:
            # Log any exceptions during execution
            self.logger.exception("Exception Occurred in TestCase 4")
            return False

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def common_testCase_04(self) -> bool:
        """
        TC5.0: Verify that Codesys Audit logs received by the external server match those sent by SyslogClient.
        """
        try:
            # performing start stop application to generate log and compare time stamp
            self.ipcObjs[0].cmd.appStart()
            self.ipcObjs[0].cmd.appStop()

            return self.compareMessagesInLogs(
                firstLogType = self.constants.LOCAL_LOG_0,
                secondLogType = self.constants.SERVER_LOG,
                logMessage = self.constants.LOG_DICTIONARY[self.constants.LOCAL_LOG_0]["startStopApp"],
                SSHClientSecond = self.sshTlsServer)

        except Exception:
            # Log any exceptions during execution
            self.logger.exception("Exception Occurred in TestCase 5")
            return False

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def common_testCase_05(self) -> bool:
        """
        TC6.0: Verify that IEC Syslogs received by the external server match those sent by SyslogClient.
        """
        try:
            self.logger.newStep("Set Syslog log severity to Maximum", level = 3)
            isSyslogActivated = self.setParamsUsingIPC(param = "0x5914:6", valueToBeSet = "255",
                                                       ipcObj = self.ipcObjs[0])
            if isSyslogActivated:
                self.logger.info(f"{[type(self).prefixCls]} Log Severity set to MAX")
            else:
                self.testCase.skip(f"{[type(self).prefixCls]} Failed to set Log Severity to MAX")
                self.sshTlsServer.disconnect()
                return False

            self.logger.newStep("Setting Flag of 'bSyslogTLS_StartLog' to True")
            self.startSyslog = True

            userSleep(3)

            if self.verifyLogs(
                logType = self.constants.SERVER_LOG, validationType = Validate_Data.LOG_MESSAGE,
                detailsToCheck = self.constants.LOG_DICTIONARY[self.constants.USER_LOG]["maxLogs"],
                extSSHClient = self.sshTlsServer
            ):
                return True
            return False
        except Exception:
            # Log any exceptions during execution
            self.logger.exception("Exception Occurred in TestCase 6")
            return False

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def common_testCase_06(self) -> bool:
        """
        TC7.0: Verify that Syslog firmservices logs received by the external server match those sent by
        SyslogClient
        """
        try:
            isFirmwareServiceVerified = self.verifyFirmwareServicesLog(firstLogType = self.constants.LOCAL_LOG_0,
                                                                       secondLogType = self.constants.SERVER_LOG,
                                                                       SSHClientSecond = self.sshTlsServer)

            self.ipcObjs[0].disconnect()
            userSleep(1)
            self.ipcObjs[0].connect()
            userSleep(1)

            userSleep(60)
            self.ipcObjs[0].cmd.appStart()

            return isFirmwareServiceVerified
        except Exception:
            # Log any exceptions during execution
            self.logger.exception("Exception Occurred in TestCase 7")
            return False

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def common_testCase_07(self) -> bool:
        """
        TC8.0: Verify that OPCUA logs received by the external server match those sent by SyslogClient
        """
        try:
            return self.verifyThirdPartyClient(firstLogType = self.constants.LOCAL_LOG_0,
                                               secondLogType = self.constants.SERVER_LOG,
                                               SSHClientSecond = self.sshTlsServer)

        except Exception:
            # Log any exceptions encountered during execution
            self.logger.exception("Exception Occurred in TestCase 8")
            return False

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def common_testCase_08(self) -> bool:
        """
        TC9.0: Verify that logs are updated at the external server from SyslogClient after disconnection
        """
        try:
            self.logger.newStep("Setting Linux Lan Switch to Off")
            linuxSwitchPin = self.testCase.resource.ioPin(pinName = "TLS_Server_ETH_SWITCH")

            if isPytefPC():
                linuxSwitchPin.set()
            else:
                linuxSwitchPin.clear()
            userSleep(5)

            # performing delete logbook
            self.logger.newStep("Performing Command of Delete Log Book")
            self.ipcObjs[0].cmd.logBookDelete()
            userSleep(10)

            self.logger.newStep("Setting Linux Lan Switch to On")
            if isPytefPC():
                linuxSwitchPin.clear()
            else:
                linuxSwitchPin.set()
            userSleep(10)

            # Step 3: Verify logs for the external client actions
            return not self.compareMessagesInLogs(
                firstLogType = self.constants.LOCAL_LOG_0,
                secondLogType = self.constants.SERVER_LOG,
                logMessage = self.constants.LOG_DICTIONARY[self.constants.LOCAL_LOG_0]["deleteLogbookCmd"],
                SSHClientSecond = self.sshTlsServer)

        except Exception:
            # Log any exception that occurs during execution
            self.logger.exception(f"{[type(self).prefixCls]} Exception Occurred in TestCase 9")
            return False

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def common_testCase_09(self) -> bool:
        """
        TC10.0: Verify that logs are updated at the external server from SyslogClient after reconnection
        """
        try:
            return self.checkLogsPostReconnect()

        except Exception:
            # Log any exception that occurs during execution
            self.logger.exception(f"{[type(self).prefixCls]} Exception Occurred in TestCase 9")
            return False

    #-------------------------------------------------------------------------------------------------------------------
    def grp_01_00_pre(self):
        """
        TC1.0: Verify activation of SyslogClient with UDP and TLS encryption to communicate with Syslog server.
        TC2.0: Verify activation of SyslogClient with UDP connection to communicate with Syslog server.
        TC3.0: Verify that the timestamp of log messages received by the external server matches those sent by
        SyslogClient with UDP connection.
        TC4.0: Verify that the number of logs received by the external server matches the number sent by SyslogClient
        within a specific time period using UDP connection.
        TC5.0: Verify that Codesys Audit logs received by the external server match those sent by SyslogClient
        with UDP connection.
        TC6.0: Verify that IEC addsys logs received by the external server match those sent by SyslogClient
        with UDP connection.
        TC7.0: Verify that Syslog firmservices logs received by the external server match those sent by SyslogClient
        with UDP connection.
        TC8.0: Verify that OPCUA logs received by the external server match those sent by SyslogClient
        with UDP connection.
        TC9.0: Verify that logs are updated at the external server from SyslogClient after disconnection
        using UDP connection.
        TC10.0: Verify that logs are updated at the external server from SyslogClient after reconnection
        using UDP connection.

        """
        try:
            if not self.grpSetup():
                self.logger.error("Group Setup Failed...Skipping the Group")
                Lib_TLS.skipTestCases = True
                raise Exception("Group Setup Failed")

            # setting syslog parameters
            self.setSyslogParams(protocol = self.constants.PROTOCOL["UDP"],
                                 encryption = self.constants.SERVER_ENCRYPTION["NOT_ENCRYPTED"],
                                 port = self.constants.PORT["UDP"])

        except Exception as exc:
            self.logger.error(f"Failed to complete Pre-Requisite for Group 1 as {exc}")
            Lib_TLS.skipTestCases = True
            self.testCase.fail("Group Pre-Requisite Failed")

    #-------------------------------------------------------------------------------------------------------------------
    def grp_01_99_post(self):
        try:
            Lib_TLS.skipTestCases = False

        except Exception as exc:
            self.logger.error(f"Post Actions for Group 1 Failed: {exc}")
            Lib_TLS.skipTestCases = True

    #-------------------------------------------------------------------------------------------------------------------
    def grp_02_00_pre(self):
        """
        TC11.0: Verify activation of SyslogClient with TCP connection and without encryption.
        TC12.0: Verify that the timestamp of log messages received by the external server matches those sent by
        SyslogClient with TCP connection and without encryption.
        TC13.0: Verify that the number of logs received by the external server matches the number sent by
        SyslogClient within a specific time period using TCP connection and without encryption.
        TC14.0: Verify that Codesys Audit logs received by the external server match those sent by
        SyslogClient with TCP connection and without encryption.
        TC15.0: Verify that IEC addsys logs received by the external server match those sent by
        SyslogClient with TCP connection and without encryption.
        TC16.0: Verify that Syslog firmservices logs received by the external server match those sent by
        SyslogClient with TCP connection and without encryption.
        TC17.0: Verify that OPCUA logs received by the external server match those sent by
        SyslogClient with TCP connection and without encryption.
        TC18.0: Verify that logs are updated at the external server from
        SyslogClient after disconnection using TCP connection and without encryption.
        TC19.0: Verify that logs are updated at the external server from
        SyslogClient after reconnection using TCP connection and without encryption.

        """
        try:
            if not self.grpSetup():
                self.logger.error("Group Setup Failed...Skipping the Group")
                Lib_TLS.skipTestCases = True
                raise Exception("Group Setup Failed")

            # setting syslog parameters
            self.setSyslogParams(protocol = self.constants.PROTOCOL["TCP"],
                                 encryption = self.constants.SERVER_ENCRYPTION["NOT_ENCRYPTED"],
                                 port = self.constants.PORT["TCP"])

        except Exception as exc:
            self.logger.error(f"Failed to complete Pre-Requisite for Group 2 as {exc}")
            Lib_TLS.skipTestCases = True
            self.testCase.fail("Group Pre-Requisite Failed")

    #-------------------------------------------------------------------------------------------------------------------
    def grp_02_99_post(self):
        try:
            Lib_TLS.skipTestCases = False

        except Exception as exc:
            self.logger.error(f"Post Actions for Group 1 Failed: {exc}")
            Lib_TLS.skipTestCases = True

    #-------------------------------------------------------------------------------------------------------------------
    def grp_03_00_pre(self):
        """
        TC20.0: Verify activation of SyslogClient with TCP connection and encryption.
        TC21.0: Verify that the timestamp of log messages received by the external server matches those sent by
        SyslogClient with TCP connection and encryption.
        TC22.0: Verify that the number of logs received by the external server matches the number sent by
        SyslogClient within a specific time period using TCP connection and encryption.
        TC23.0: Verify that Codesys Audit logs received by the external server match those sent by
        SyslogClient with TCP connection and encryption.
        TC24.0: Verify that IEC addsys logs received by the external server match those sent by
        SyslogClient with TCP connection and encryption.
        TC25.0: Verify that Syslog firmservices logs received by the external server match those sent by
        SyslogClient with TCP connection and encryption.
        TC26.0: Verify that OPCUA logs received by the external server match those sent by
        SyslogClient with TCP connection and encryption.
        TC27.0: Verify that logs are updated at the external server from
        SyslogClient after disconnection using TCP connection and encryption.
        TC28.0: Verify that logs are updated at the external server from
        SyslogClient after reconnection using TCP connection and encryption.

        """
        try:
            if not self.grpSetup():
                self.logger.error("Group Setup Failed...Skipping the Group")
                Lib_TLS.skipTestCases = True
                raise Exception("Group Setup Failed")

            # setting syslog parameters
            self.setSyslogParams(protocol = self.constants.PROTOCOL["TCP"],
                                 encryption = self.constants.SERVER_ENCRYPTION["ENCRYPTED"],
                                 port = self.constants.PORT["TCP_TLS"])
        except Exception as exc:
            self.logger.error(f"Failed to complete Pre-Requisite for Group 3 as {exc}")
            Lib_TLS.skipTestCases = True
            self.testCase.fail("Group Pre-Requisite Failed")

    #-------------------------------------------------------------------------------------------------------------------
    def grp_03_99_post(self):
        try:
            Lib_TLS.skipTestCases = False

        except Exception as exc:
            self.logger.error(f"Post Actions for Group 1 Failed: {exc}")
            Lib_TLS.skipTestCases = True

    #-------------------------------------------------------------------------------------------------------------------
    def grp_04_00_pre(self):
        """
        TC1.0: Verify activation of SyslogClient with UDP and TLS encryption to communicate with Syslog server.
        TC34.0: Verify the functioning of the Message Severity Filter for TCP connection with encryption.
        TC35.0: Verify the functioning of the Message Severity Filter for TCP connection without encryption.
        TC36.0: Verify the functioning of the Message Severity Filter for UDP connection.
        """
        try:
            if not self.grpSetup():
                self.logger.error("Group Setup Failed...Skipping the Group")
                Lib_TLS.skipTestCases = True
                raise Exception("Group Setup Failed")

        except Exception as exc:
            Lib_TLS.skipTestCases = True
            self.testCase.fail(f"Group Pre-Requisite Failed: {exc}")

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def grp_04_test_01(self) -> bool:
        """
        TC1.0: Verify activation of SyslogClient with UDP and TLS encryption to communicate with Syslog server.
        """
        try:
            # setting syslog parameters
            self.setSyslogParams(protocol = self.constants.PROTOCOL["UDP"],
                                 encryption = self.constants.SERVER_ENCRYPTION["ENCRYPTED"],
                                 port = self.constants.PORT["UDP"])

            # verifying syslog paramaeters
            if self.verifySyslogParams(expectedProtocol = self.constants.PROTOCOL_TYPES[1],
                                       expectedEncryption = self.constants.SERVER_ENCRYPTION["ENCRYPTED"],
                                       expectedPort = self.constants.PORT["UDP"]):
                self.logger.info(f"[{type(self).prefixCls}] Verification Successful...Test Passed")
                return True
            return False

        except Exception:
            self.logger.exception("Exception Occurred in TestCase 1")
            return False

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def grp_04_test_02(self) -> bool:
        try:
            self.setSyslogParams(protocol = self.constants.PROTOCOL["TCP"],
                                 encryption = self.constants.SERVER_ENCRYPTION["ENCRYPTED"],
                                 port = self.constants.PORT["TCP_TLS"])

            # verifying syslog paramaeters
            if not self.verifySyslogParams(expectedProtocol = self.constants.PROTOCOL_TYPES[1],
                                           expectedEncryption = self.constants.SERVER_ENCRYPTION["ENCRYPTED"],
                                           expectedPort = self.constants.PORT["TCP_TLS"]):
                self.logger.error(f"[{type(self).prefixCls}] Failed to set TCP settings with Encryption")
                return False
            self.logger.info(f"[{type(self).prefixCls}] TCP settings with Encryption applied successfully")

            return self.verifySeverities(severities = self.constants.SYSLOG_SEVERITY_LIST)
        except Exception:
            self.logger.exception("Exception Occurred in TestCase 1")
            return False

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def grp_04_test_03(self) -> bool:
        try:
            self.setSyslogParams(protocol = self.constants.PROTOCOL["TCP"],
                                 encryption = self.constants.SERVER_ENCRYPTION["NOT_ENCRYPTED"],
                                 port = self.constants.PORT["TCP"])

            # verifying syslog paramaeters
            if not self.verifySyslogParams(expectedProtocol = self.constants.PROTOCOL_TYPES[1],
                                           expectedEncryption = self.constants.SERVER_ENCRYPTION["NOT_ENCRYPTED"],
                                           expectedPort = self.constants.PORT["TCP"]):
                self.logger.error(f"[{type(self).prefixCls}] Failed to set TCP settings without encryption")
                return False
            self.logger.info(f"[{type(self).prefixCls}] TCP settings without encryption applied successfully")

            return self.verifySeverities(severities = self.constants.SYSLOG_SEVERITY_LIST[:4])
        except Exception:
            self.logger.exception("Exception Occurred in TestCase 2")
            return False

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def grp_04_test_04(self) -> bool:
        try:
            self.setSyslogParams(protocol = self.constants.PROTOCOL["UDP"],
                                 encryption = self.constants.SERVER_ENCRYPTION["NOT_ENCRYPTED"],
                                 port = self.constants.PORT["UDP"])

            # verifying syslog paramaeters
            if not self.verifySyslogParams(expectedProtocol = self.constants.PROTOCOL_TYPES[0],
                                           expectedEncryption = self.constants.SERVER_ENCRYPTION["NOT_ENCRYPTED"],
                                           expectedPort = self.constants.PORT["UDP"]):
                self.logger.error(f"[{type(self).prefixCls}] Failed to set UDP settings")
                return False
            self.logger.info(f"[{type(self).prefixCls}] UDP Settings applied successfully")

            return self.verifySeverities(severities = self.constants.SYSLOG_SEVERITY_LIST[4:])
        except Exception:
            self.logger.exception("Exception Occurred in TestCase 3")
            return False

    #-------------------------------------------------------------------------------------------------------------------
        #     # List of test case methods to execute
        #     testCases = [testCase0, testCase1, testCase2, testCase3]
        #
        #     # Initialize flag to track the success of all test cases
        #     noTcFailed = True
        #
        #     # Iterate through each test case in the list
        #     for testCase in testCases:
        #         # Check if not developer mode
        #         self.emptyOldLogs()
        #
        #         # Check if the test case fails
        #         if not testCase(self):
        #             # If a test case fails, update the flag to False
        #             noTcFailed = False
        #
        # except Exception as err:  # Handle any unexpected exceptions during execution
        #     self.testCase.fail(err)
        #
        # finally:
        #     # If any test case failed, log the failure
        #     if not noTcFailed:
        #         self.testCase.fail("One Or More test cases failed")

    #-------------------------------------------------------------------------------------------------------------------
    def grp_04_99_post(self):
        try:
            Lib_TLS.skipTestCases = False

        except Exception as exc:
            self.logger.error(f"Post Actions for Group 4 Failed: {exc}")
            Lib_TLS.skipTestCases = True

    #-------------------------------------------------------------------------------------------------------------------
    def grp_05_00_pre(self) -> None:
        """
        TC Group for IEC Function Block Testing

        TC1.1 Verify whether the logs for the user are being generated in the User (user.log) file with
        setting "L_IS1P_eFacility":=user(1) by using "Audit log IEC FB "
        TC1.2 Verify whether the logs for the user are being generated in the User (user.log) file with setting
        "L_IS1P_eFacility":=user(1) by using "Audit log IEC FB "
        TC1.3 Verify whether the logs for user are getting generated in User(auth.log) file with Successful
        authentication of user with Setting "L_IS1P_eAuthentication" :=successful(1) by using "Audit log IEC FB"
        TC1.4 Verify whether the logs for user are getting generated in User(auth.log) file with Failed
        authentication of user with Setting "L_IS1P_eAuthentication" :=failed(2) by using "Audit log IEC FB"
        TC1.5 Verify whether the logs for user are getting generated in User(auth.log) file with None
        authentication of user with Setting "L_IS1P_eAuthentication" :=none(0) by using "Audit log IEC FB"
        TC1.6 Verify whether Name of the user is 64 characters in User(user.log) file with Setting
        "sUser" by using "Audit log IEC FB"
        TC1.7 Verify whether Name of the user is not exceed 64 characters in User(user.log) file with
        Setting "sUser" by using "Audit log IEC FB "
        TC1.8 Verify log message is 255 characters in User(user.log) file with setting "sMessage" by using
        "Audit log IEC FB "
        TC1.9 Verify log message is not exceed 255 characters in User(user.log) file with setting "sMessage"
        by using "Audit log IEC FB "
        TC2.0 Verify the "Auditlog IEC FB" generates correct number of logs with same messages as defined by user
        TC2.1 Verify the "Auditlog IEC FB" generates correct number logs with different messages as defined by user
        TC2.2 Verify the "Auditlog IEC FB" generate logs after calling IEC FB multiple times within a
        task and also from any task within the application.
        TC2.3 Verify the "Auditlog IEC FB" transmission of messages within the buffer size limit.
        TC2.4 Verify that after an event of a network failure, the messages that have not yet been
        transferred from the buffer are lost by using "Auditlog IEC FB"
        """
        try:
            if not self.grpSetup():
                self.logger.error("Group Setup Failed...Skipping the Group")
                Lib_TLS.skipTestCases = True
                raise Exception("Group Setup Failed")

            self.logger.newStep("Setting Syslog Parameter to Activated")
            syslogDict = self.constants.PARAM_DICT["SYSLOG_PARAMETER"]

            # Activate  Sys Logging
            isSyslogActivated = self.setParamsUsingIPC(param = syslogDict[0],
                                                       valueToBeSet = syslogDict[1], ipcObj = self.ipcObjs[0])
            if isSyslogActivated:
                self.logger.info(f"{[type(self).prefixCls]} Syslog Parameter Set to Activated")
            else:
                self.testCase.skip(f"{[type(self).prefixCls]} Failed to set Syslog Parameter To Activated")

            # Set Log Severity to full
            isSyslogSeveritySet = self.setParamsUsingIPC(param = "0x5914:6",
                                                         valueToBeSet = "255", ipcObj = self.ipcObjs[0])
            if isSyslogSeveritySet:
                self.logger.info(f"{[type(self).prefixCls]} Log Severity increased to full")
            else:
                self.testCase.skip(f"{[type(self).prefixCls]} Failed to Log Severity increased to full")

            self.logger.newStep("Setting Flag of 'bSyslogTLS_StartLog' to False")
            self.startSyslog = False

            # Ensure disable user management is done
            if deleteUserManagementFiles(logger = self.logger, ipAddress = self.ipAddresses[0]):
                # If user management was disabled, controller restart is must
                self.ipcObjs[0].waitUntilBooted(switchOff = True,
                                                switchOn  = True,
                                                channel   = self.ipcObjs[0].getDefaultChannel())

        except Exception as exc:
            Lib_TLS.skipTestCases = True
            self.testCase.fail(f"Group Pre-Requisite Failed: {exc}")

    #-----------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def grp_05_test_01(self) -> bool:
        """
        TC1.1 Verify whether the logs for the user are being generated in the User (user.log) file with setting
        "L_IS1P_eFacility":=user(1) by using "Audit log IEC FB "
        """
        try:
            # Initialize the test result
            testResult = True

            # Set the number of log messages to generate
            logMsgCount = 5
            # Set the facility identifier
            iFacility = 1
            # Define the log message
            logMsg = "This is TC1.1 of IEC Function Block Testing"

            # Assign values to the message and count attributes
            self.strMessage = logMsg
            self.iMessage_Count = logMsgCount
            self.iFacility = iFacility

            # Determine the log type based on the facility identifier
            logType = self.constants.USER_LOG if iFacility == 1 else self.constants.AUTH_LOG

            # Log the message and count information
            self.logger.info(f"Log '{logMsg}' in {logType} {logMsgCount} times")

            # Trigger the log message generation
            self.bTrigger_Log_Msg = True

            # Verify the repeatability of the logs
            readLogMsgCount = self.verifyLogsRepeatability(logType = logType, detail = logMsg)

            # Check if the read log message count matches the expected count
            if readLogMsgCount == logMsgCount:
                testResult = True
                self.logger.info(f"Successfully logged message '{logMsg}' in {logType} {readLogMsgCount} times")
            else:
                testResult = False
                self.logger.error(f"Failed Logging message '{logMsg}' in {logType} {logMsgCount} "
                                  f"times instead logger {readLogMsgCount} times")

            # Return the result of log format verification
            return testResult

        except Exception:
            # Log any exceptions that occur during test case execution
            self.logger.exception("Exception Occurred in TestCase1")
            return False

    #-----------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def grp_05_test_02(self) -> bool:
        """
        TC1.2 Verify whether the logs for Authentication are getting generated in Authentication(auth.log) file
        with setting "L_IS1P_eFacility":=Auth(4) by using "Audit log IEC FB "
        """
        try:
            # Initialize the test result
            testResult = True

            # Set the number of log messages to generate
            logMsgCount = 5
            # Set the facility identifier
            iFacility = 4
            # Define the log message
            logMsg = "This is TC1.2 of IEC Function Block Testing"

            # Assign values to the message and count attributes
            self.strMessage = logMsg
            self.iMessage_Count = logMsgCount
            self.iFacility = iFacility

            # Determine the log type based on the facility identifier
            logType = self.constants.USER_LOG if iFacility == 1 else self.constants.AUTH_LOG

            # Log the message and count information
            self.logger.info(f"Log '{logMsg}' in {logType} {logMsgCount} times")

            # Trigger the log message generation
            self.bTrigger_Log_Msg = True

            # Verify the repeatability of the logs
            readLogMsgCount = self.verifyLogsRepeatability(logType = logType, detail = logMsg)

            # Check if the read log message count matches the expected count
            if readLogMsgCount == logMsgCount:
                testResult = True
                self.logger.info(f"Successfully logged message '{logMsg}' in {logType} {readLogMsgCount} times")
            else:
                testResult = False
                self.logger.error(f"Failed Logging message '{logMsg}' in {logType} {logMsgCount} times"
                                  f", instead logged {readLogMsgCount} times")

            # Return the result of log format verification
            return testResult

        except Exception:
            # Log any exceptions that occur during test case execution
            self.logger.exception("Exception Occurred in TestCase2")
            return False

    #-----------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def grp_05_test_03(self) -> bool:
        """
        TC1.3 Verify whether the logs for user are getting generated in User(auth.log) file with Successful
        authentication of user with Setting "L_IS1P_eAuthentication" :=successful(1) by using "Audit log IEC FB"
        """
        try:
            # Initialize the test result
            testResult = True

            # Set the number of log messages to generate
            logMsgCount = 5
            # Set the facility identifier
            iFacility = 4
            # Set the authentication identifier
            iAuthetication = 1
            # Define the log message
            logMsg = "This is TC1.3 of IEC Function Block Testing"

            # Assign values to the message, count, and authentication attributes
            self.strMessage = logMsg
            self.iMessage_Count = logMsgCount
            self.iAuthentication = iAuthetication
            self.iFacility = iFacility

            # Determine the log type based on the facility identifier
            logType = self.constants.USER_LOG if iFacility == 1 else self.constants.AUTH_LOG

            # Log the message and count information
            self.logger.info(f"Log '{logMsg}' in {logType} {logMsgCount} times")

            # Trigger the log message generation
            self.bTrigger_Log_Msg = True

            userSleep(2)

            # Get the current test case name from the stack trace
            stackList = traceback.extract_stack()
            testCase = re.match(r".*test_(Grp_\d+_.*)_\w+-\d+", self.testCase.testCaseName).group(1).lower()
            currentTestCase = [stackObj for stackObj in stackList if testCase in stackObj.name][0].name

            # Copy the latest log file from the controller to the local machine
            logPath = os.path.join(Lib_TLS.SYSTEM_LOGS_FOLDER_CREATED,
                                   '_'.join([self.testCase.testCaseName, currentTestCase,
                                             self.constants.LOG_FILES[logType].split(
                                                 self.constants.CONTROLLER_LOG_PATH)[1]]))

            self.sshMasterClient.copy_file_to_local(
                remote_path = self.constants.LOG_FILES[logType],
                local_path = logPath)

            # Parse the log file and retrieve the timestamp of the latest log entry
            logObj = Factory_Log_Parser().create_parser(logType = logType, logPath = logPath)

            # Extract log messages from the log data, excluding those with "successful"
            logMsgLst = [logData.logmessage for logData in logObj.structured_Log_Data
                         if "successful" in logData.logmessage]

            # Check if there are log messages including "successful"
            if len(logMsgLst) == logMsgCount:
                testResult = True
                self.logger.info(
                    f"Successfully logged message with 'successful' in {logType} {len(logMsgLst)} times")
            else:
                testResult = False
                self.logger.error(
                    f"Failed to log message with 'successful' in {logType} {logMsgCount} times, "
                    f"instead logged {len(logMsgLst)} times")

            # Return the result of log format verification
            return testResult

        except Exception:
            # Log any exceptions that occur during test case execution
            self.logger.exception("Exception Occurred in TestCase3")
            return False

    #-----------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def grp_05_test_04(self) -> bool:
        """
        TC1.4 Verify whether the logs for user are getting generated in User(auth.log) file with Failed
        authentication of user with Setting "L_IS1P_eAuthentication" :=failed(2) by using "Audit log IEC FB"
        """
        try:
            # Initialize the test result
            testResult = True

            # Set the number of log messages to generate
            logMsgCount = 5

            # Set the facility identifier
            iFacility = 4

            # Set the authentication identifier
            iAuthetication = 2

            # Define the log message
            logMsg = "This is TC1.3 of IEC Function Block Testing"

            # Assign values to the message, count, and authentication attributes
            self.strMessage = logMsg
            self.iMessage_Count = logMsgCount
            self.iAuthentication = iAuthetication
            self.iFacility = iFacility

            # Determine the log type based on the facility identifier
            logType = self.constants.USER_LOG if iFacility == 1 else self.constants.AUTH_LOG

            # Log the message and count information
            self.logger.info(f"Log '{logMsg}' in {logType} {logMsgCount} times")

            # Trigger the log message generation
            self.bTrigger_Log_Msg = True

            userSleep(2)

            # Get the current test case name from the stack trace
            stackList = traceback.extract_stack()
            testCase = re.match(r".*test_(Grp_\d+_.*)_\w+-\d+", self.testCase.testCaseName).group(1).lower()
            currentTestCase = [stackObj for stackObj in stackList if testCase in stackObj.name][0].name

            # Copy the latest log file from the controller to the local machine
            logPath = os.path.join(Lib_TLS.SYSTEM_LOGS_FOLDER_CREATED,
                                   '_'.join([self.testCase.testCaseName, currentTestCase,
                                             self.constants.LOG_FILES[logType].split(
                                                 self.constants.CONTROLLER_LOG_PATH)[1]]))

            self.sshMasterClient.copy_file_to_local(
                remote_path = self.constants.LOG_FILES[logType],
                local_path = logPath)

            # Parse the log file and retrieve the timestamp of the latest log entry
            logObj = Factory_Log_Parser().create_parser(logType = logType, logPath = logPath)

            # Extract log messages from the log data, excluding those with "successful"
            logMsgLst = [logData.logmessage for logData in logObj.structured_Log_Data
                         if "failed" in logData.logmessage]

            # Check if there are log messages including "failed"
            if len(logMsgLst) == logMsgCount:
                testResult = True
                self.logger.info(
                    f"Successfully logged message with 'failed' in {logType} {len(logMsgLst)} times")
            else:
                testResult = False
                self.logger.error(
                    f"Failed to log message with 'failed' in {logType} {logMsgCount} times,"
                    f" instead logged {len(logMsgLst)} times")

            # Return the result of log format verification
            return testResult

        except Exception:
            # Log any exceptions that occur during test case execution
            self.logger.exception("Exception Occurred in TestCase4")
            return False

    #-----------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def grp_05_test_05(self) -> bool:
        """
        TC1.5 Verify whether the logs for user are getting generated in User(auth.log) file with
        None authentication of user with Setting "L_IS1P_eAuthentication" :=none(0) by using "Audit log IEC FB"
        """
        try:
            # Initialize the test result
            testResult = True

            # Set the number of log messages to generate
            logMsgCount = 5

            # Set the facility identifier
            iFacility = 4

            # Set the authentication identifier
            iAuthetication = 0

            # Define the log message
            logMsg = "This is TC1.3 of IEC Function Block Testing"

            # Assign values to the message, count, and authentication attributes
            self.strMessage = logMsg
            self.iMessage_Count = logMsgCount
            self.iAuthentication = iAuthetication
            self.iFacility = iFacility

            # Determine the log type based on the facility identifier
            logType = self.constants.USER_LOG if iFacility == 1 else self.constants.AUTH_LOG

            # Log the message and count information
            self.logger.info(f"Log '{logMsg}' in {logType} {logMsgCount} times")

            # Trigger the log message generation
            self.bTrigger_Log_Msg = True

            userSleep(2)

            # Get the current test case name from the stack trace
            stackList = traceback.extract_stack()
            testCase = re.match(r".*test_(Grp_\d+_.*)_\w+-\d+", self.testCase.testCaseName).group(1).lower()
            currentTestCase = [stackObj for stackObj in stackList if testCase in stackObj.name][0].name

            # Copy the latest log file from the controller to the local machine
            logPath = os.path.join(Lib_TLS.SYSTEM_LOGS_FOLDER_CREATED,
                                   '_'.join([self.testCase.testCaseName, currentTestCase,
                                             self.constants.LOG_FILES[logType].split(
                                                 self.constants.CONTROLLER_LOG_PATH)[1]]))
            self.sshMasterClient.copy_file_to_local(
                remote_path = self.constants.LOG_FILES[logType],
                local_path = logPath)

            # Parse the log file and retrieve the timestamp of the latest log entry
            logObj = Factory_Log_Parser().create_parser(logType = logType, logPath = logPath)

            # Extract log messages from the log data, excluding those with "successful"
            logMsgLst = [logData.logmessage for logData in logObj.structured_Log_Data
                         if "failed" in logData.logmessage or "successful" in logData.logmessage]

            # Check if there are no log messages excluding "successful"
            if len(logMsgLst) == 0:
                testResult = True
                self.logger.info(
                    f"Success - there are zero log messages with 'failed' in {logType} as expected")
            else:
                testResult = False
                self.logger.error(
                    f"Failed to log message with 'failed' in {logType} 0 "
                    f"times instead logged {len(logMsgLst)} times ")

            # Return the result of log format verification
            return testResult

        except Exception:
            # Log any exceptions that occur during test case execution
            self.logger.exception("Exception Occurred in TestCase5")
            return False

    #-----------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def grp_05_test_06(self) -> bool:
        """
        TC1.6 Verify whether Name of the user is 64 characters in User(user.log) file with
        Setting "sUser" by using "Audit log IEC FB"
        """
        try:
            # Initialize the test result
            testResult = True

            # Set the number of log messages to generate
            logMsgCount = 1

            # Set the facility identifier
            iFacility = 1

            # Set the authentication identifier
            iAuthetication = 0

            # Define the log message
            logMsg = "This is TC1.6 of IEC Function Block Testing"

            # Define the 64-character username
            userName64char = r"XzEPGZPwQTXUEnfCUBYPCOwfXgF18QOMJqpWoDPu9QuSxVwJYt2AnEGyicJqqJSL"

            # Assign values to the user, message, count, and authentication attributes
            self.strUser = userName64char
            self.strMessage = logMsg
            self.iMessage_Count = logMsgCount
            self.iAuthentication = iAuthetication
            self.iFacility = iFacility

            # Determine the log type based on the facility identifier
            logType = self.constants.USER_LOG if iFacility == 1 else self.constants.AUTH_LOG

            # Log the message and count information
            self.logger.info(f"Log '{logMsg}' in {logType} {logMsgCount} times")

            # Trigger the log message generation
            self.bTrigger_Log_Msg = True

            # Verify the log details based on the hostname
            testResult = self.verifyLogs(logType = logType, validationType = Validate_Data.LOG_MESSAGE,
                                         detailsToCheck = [userName64char])

            if testResult:
                self.logger.info(f"Successfully logged message with 64char user name '{logMsg}' in {logType} "
                                 f"Hostname  '{userName64char}'")

                # get logged msg count
                readLogMsgCount = self.verifyLogsRepeatability(logType = logType, detail = logMsg)

                # Check if the read log message count matches the expected count
                if readLogMsgCount == logMsgCount:
                    testResult = True
                    self.logger.info(
                        f"Successfully logged message '{logMsg}' in {logType} {readLogMsgCount} times")
                else:
                    testResult = False
                    self.logger.error(f"Failed Logging message '{logMsg}' in {logType} {logMsgCount} times,"
                                      f" instead logged {readLogMsgCount} times")
            else:
                self.logger.error(f"Failed Logging message '{logMsg}' in {logType}")

            # Return the result of log format verification
            return testResult

        except Exception:
            # Log any exceptions that occur during test case execution
            self.logger.exception("Exception Occurred in TestCase6")
            return False

    #-----------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def grp_05_test_07(self) -> bool:
        """
        TC1.7 Verify whether Name of the user is not exceed 64 characters in User(user.log) file with
        Setting "sUser" by using "Audit log IEC FB "
        """
        try:
            # Initialize the test result
            testResult = True

            # Set the number of log messages to generate
            logMsgCount = 1

            # Set the facility identifier
            iFacility = 1

            # Set the authentication identifier
            iAuthetication = 0

            # Define the log message
            logMsg = "This is TC1.7 of IEC Function Block Testing"

            # Define a username that exceeds 64 characters
            userName64charplus = r"XzEPGZPwQTXUEnfCUBYPCOwfXgF18QOMJqpWoDPu9QuSxVwJYt2AnEGyicJqqJSL1234"

            # Define a username that is exactly 64 characters
            userName64char = r"XzEPGZPwQTXUEnfCUBYPCOwfXgF18QOMJqpWoDPu9QuSxVwJYt2AnEGyicJqqJSL"

            # Assign values to the user, message, count, and authentication attributes
            self.strUser = userName64charplus
            self.strMessage = logMsg
            self.iMessage_Count = logMsgCount
            self.iAuthentication = iAuthetication
            self.iFacility = iFacility

            # Determine the log type based on the facility identifier
            logType = self.constants.USER_LOG if iFacility == 1 else self.constants.AUTH_LOG

            # Log the message and count information
            self.logger.info(f"Log '{logMsg}' in {logType} {logMsgCount} times")

            # Trigger the log message generation
            self.bTrigger_Log_Msg = True

            # Verify the log details based on the hostname
            testResult = self.verifyLogs(logType = logType, validationType = Validate_Data.LOG_MESSAGE,
                                         detailsToCheck = [userName64charplus])

            # If the log with the longer username is not found, check the truncated username
            if not testResult:
                testResult = self.verifyLogs(logType = logType, validationType = Validate_Data.LOG_MESSAGE,
                                             detailsToCheck = [userName64char])

            if testResult:
                self.logger.info(
                    f"Successfully logged message '{logMsg}' in {logType} Hostname {userName64char}")
            else:
                self.logger.error(f"Failed Log message '{logMsg}' in {logType} Hostname {userName64charplus} ")

            # Return the result of log format verification
            return testResult

        except Exception:
            # Log any exceptions that occur during test case execution
            self.logger.exception("Exception Occurred in TestCase7")
            return False

    #-----------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def grp_05_test_08(self) -> bool:
        """
        TC1.8 Verify log message is 255 characters in User(user.log) file with setting "sMessage"
        by using "Audit log IEC FB "
        """
        try:
            # Initialize the test result
            testResult = True

            # Set the number of log messages to generate
            logMsgCount = 1
            # Set the facility identifier
            iFacility = 1

            # Generate a random string of 255 characters
            logMsg255Char = self.generate_random_string()

            # Assign values to the message and count attributes
            self.strMessage = logMsg255Char
            self.iMessage_Count = logMsgCount
            self.iFacility = iFacility

            # Determine the log type based on the facility identifier
            logType = self.constants.USER_LOG if iFacility == 1 else self.constants.AUTH_LOG

            # Log the message and count information
            self.logger.info(f"Log {logMsg255Char} in {logType} {logMsgCount} times")

            # Trigger the log message generation
            self.bTrigger_Log_Msg = True

            # Verify the log details based on the log message
            testResult = self.verifyLogs(logType = logType, validationType = Validate_Data.LOG_MESSAGE,
                                         detailsToCheck = [logMsg255Char])

            if testResult:
                self.logger.info(f"Successfully logged message of length 255 char in {logType}")
            else:
                self.logger.error(f"Failed Logging message of length 255 char in {logType}")

            # Return the result of log format verification
            return testResult

        except Exception:
            # Log any exceptions that occur during test case execution
            self.logger.exception("Exception Occurred in TestCase8")
            return False

    #-----------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def grp_05_test_09(self) -> bool:
        """
        TC1.9 Verify log message is not exceed 255 characters in User(user.log) file with setting
        "sMessage" by using "Audit log IEC FB "
        """
        try:
            # Initialize the test result
            testResult = True

            # Set the number of log messages to generate
            logMsgCount = 1

            # Set the facility identifier
            iFacility = 1

            # Generate a random string of 255 characters
            logMsg255Char = self.generate_random_string()

            # Create a log message that exceeds 255 characters
            logMsg255PlusChar = logMsg255Char + "12345"

            # Assign values to the message and count attributes
            self.strMessage = logMsg255PlusChar
            self.iMessage_Count = logMsgCount
            self.iFacility = iFacility

            # Determine the log type based on the facility identifier
            logType = self.constants.USER_LOG if iFacility == 1 else self.constants.AUTH_LOG

            # Log the message and count information
            self.logger.info(f"Log {logMsg255PlusChar} in {logType} {logMsgCount} times")

            # Trigger the log message generation
            self.bTrigger_Log_Msg = True

            # Verify the log details based on the log message
            testResult = self.verifyLogs(logType = logType, validationType = Validate_Data.LOG_MESSAGE,
                                         detailsToCheck = [logMsg255PlusChar])

            # If the log with the longer message is not found, check the truncated message
            if not testResult:
                testResult = self.verifyLogs(logType = logType, validationType = Validate_Data.LOG_MESSAGE,
                                             detailsToCheck = [logMsg255Char])

            if testResult:
                self.logger.info(f"Successfully logged message of length 255+ char in {logType}")
            else:
                self.logger.error(f"Failed Logging message of length 255+ char in {logType}")

            # Return the result of log format verification
            return testResult

        except Exception:
            # Log any exceptions that occur during test case execution
            self.logger.exception("Exception Occurred in TestCase9")
            return False

    #-----------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def grp_05_test_10(self) -> bool:
        """
        TC2.0 Verify the "Auditlog IEC FB" generates correct number of logs with same messages
        as defined by user
        """
        try:
            # Initialize the test result
            testResult = True

            # Set the number of log messages to generate
            logMsgCount = 99

            # Set the facility identifier
            iFacility = 1

            # Set the authentication identifier
            iAuthetication = 0

            # Define the log message
            logMsg = "This is TC2.0 of IEC Function Block Testing"

            # Assign values to the message, count, and authentication attributes
            self.strMessage = logMsg
            self.iMessage_Count = logMsgCount
            self.iAuthentication = iAuthetication
            self.iFacility = iFacility

            # Determine the log type based on the facility identifier
            logType = self.constants.USER_LOG if iFacility == 1 else self.constants.AUTH_LOG

            # Log the message and count information
            self.logger.info(f"Log '{logMsg}' in {logType} {logMsgCount} times")

            # Trigger the log message generation
            self.bTrigger_Log_Msg = True

            # Get the current test case name from the stack trace
            stackList = traceback.extract_stack()
            testCase = re.match(r".*test_(Grp_\d+_.*)_\w+-\d+", self.testCase.testCaseName).group(1).lower()
            currentTestCase = [stackObj for stackObj in stackList if testCase in stackObj.name][0].name

            # Copy the latest log file from the controller to the local machine
            logPath = os.path.join(Lib_TLS.SYSTEM_LOGS_FOLDER_CREATED,
                                   '_'.join([self.testCase.testCaseName, currentTestCase,
                                             self.constants.LOG_FILES[logType].split(
                                                 self.constants.CONTROLLER_LOG_PATH)[1]]))

            self.sshMasterClient.copy_file_to_local(
                remote_path = self.constants.LOG_FILES[logType],
                local_path = logPath)

            # Parse the log file and retrieve the timestamp of the latest log entry
            logObj = Factory_Log_Parser().create_parser(logType = logType, logPath = logPath)

            # Extract timestamps from the log data
            timestampList = [logData.timestamp.split(".")[0] for logData in logObj.structured_Log_Data]

            # Count the occurrences of each timestamp
            count_dict = Counter(timestampList)

            # Determine the maximum rate of log entries
            rate = max(count_dict.values())
            controllerRate = self.ui_Log_Data_Transfer_Rate

            # Compare the rate with the expected log data transfer rate
            if rate < controllerRate:
                testResult = True
                self.logger.info(
                    f"Successfully logged message in {logType} at rate {rate} less than {controllerRate}")
            else:
                testResult = False
                self.logger.error(
                    f"Failed to log message in {logType} at {rate} less than {controllerRate} ctrl rate")

            # Return the result of log format verification
            return testResult

        except Exception:
            # Log any exceptions that occur during test case execution
            self.logger.exception("Exception Occurred in TestCase10")
            return False

    #-----------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def grp_05_test_11(self) -> bool:
        """
        TC2.1 Verify the "Auditlog IEC FB" generates correct number logs with different messages
        as defined by user
        """
        try:
            # Initialize the test result
            testResult = True

            # Set the number of log messages to generate
            logMsgCount = 99

            # Set the facility identifier
            iFacility = 1

            # Set the authentication identifier
            iAuthetication = 0

            # Define the log message
            logMsg = "This is TC2.1 of IEC Function Block Testing"

            # Assign values to the message, count, and authentication attributes
            self.strMessage = logMsg
            self.iMessage_Count = logMsgCount
            self.iAuthentication = iAuthetication
            self.iFacility = iFacility

            # Determine the log type based on the facility identifier
            logType = self.constants.USER_LOG if iFacility == 1 else self.constants.AUTH_LOG

            # Log the message and count information
            self.logger.info(f"Log '{logMsg}' in {logType} {logMsgCount} times")

            # Trigger the log message generation
            self.bTrigger_Log_MsgIdx_1 = True

            # Get the current test case name from the stack trace
            stackList = traceback.extract_stack()
            testCase = re.match(r".*test_(Grp_\d+_.*)_\w+-\d+", self.testCase.testCaseName).group(1).lower()
            currentTestCase = [stackObj for stackObj in stackList if testCase in stackObj.name][0].name

            # Copy the latest log file from the controller to the local machine
            logPath = os.path.join(Lib_TLS.SYSTEM_LOGS_FOLDER_CREATED,
                                   '_'.join([self.testCase.testCaseName, currentTestCase,
                                             self.constants.LOG_FILES[logType].split(
                                                 self.constants.CONTROLLER_LOG_PATH)[1]]))

            self.sshMasterClient.copy_file_to_local(
                remote_path = self.constants.LOG_FILES[logType],
                local_path = logPath)

            # Parse the log file and retrieve the timestamp of the latest log entry
            logObj = Factory_Log_Parser().create_parser(logType = logType, logPath = logPath)

            # Extract log messages from the log data
            logMsgLst = [logData.logmessage for logData in logObj.structured_Log_Data]

            # Count the occurrences of each log message
            count_dict = Counter(logMsgLst)

            # Determine the maximum count of any single log message
            max_count = max(count_dict.values())

            # Check if each log message appears only once
            if max_count == 1:
                testResult = True
                self.logger.info(f"Successfully logged Unique messages in {logType} {len(logMsgLst)} times")
            else:
                testResult = False
                self.logger.error(f"Failed Log Unique message in {logType}")

            # Return the result of log format verification
            return testResult

        except Exception:
            # Log any exceptions that occur during test case execution
            self.logger.exception("Exception Occurred in TestCase11")
            return False

    #-----------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def grp_05_test_12(self) -> bool:
        """
        TC2.2 Verify the "Auditlog IEC FB" generate logs after calling IEC FB multiple times within a
        task and also from any task within the application.
        """
        try:
            # Initialize the test result
            testResult = True

            # Set the number of log messages to generate
            logMsgCount = 5
            # Set the facility identifier
            iFacility = 1
            # Set the authentication identifier
            iAuthetication = 1
            # Define the log message
            logMsg = "This is TC2.2 of IEC Function Block Testing"

            # Assign values to the message, count, and authentication attributes
            self.strMessage = logMsg
            self.iMessage_Count = logMsgCount
            self.iAuthentication = iAuthetication
            self.iFacility = iFacility

            # Determine the log type based on the facility identifier
            logType = self.constants.USER_LOG if iFacility == 1 else self.constants.AUTH_LOG

            # Log the message and count information
            self.logger.info(f"Log '{logMsg}' in {logType} {logMsgCount} times")

            # Trigger the log message generation
            self.bTrigger_Log_Msg = True
            self.bTrigger_Log_MsgIdx_1 = True
            self.bTrigger_Log_MsgIdx_2 = True
            self.bTrigger_Interval = True

            # wait for all interval message to log in log files
            userSleep(logMsgCount + 2)

            # Verify the repeatability of the logs
            readLogMsgCount = self.verifyLogsRepeatability(logType = logType, detail = logMsg)

            # Check if the read log message count matches the expected count multiplied by 4
            if readLogMsgCount == logMsgCount * 4:
                testResult = True
                self.logger.info(f"Successfully logged message '{logMsg}' in {logType} {readLogMsgCount} times")
            else:
                testResult = False
                self.logger.error(f"Failed Logging message '{logMsg}' in {logType} {logMsgCount * 4} "
                                  f"times, instead logged {readLogMsgCount} times")

            # Return the result of log format verification
            return testResult

        except Exception:
            # Log any exceptions that occur during test case execution
            self.logger.exception("Exception Occurred in TestCase3")
            return False

    #-----------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def grp_05_test_13(self) -> bool:
        """
        TC2.3 Verify the "Auditlog IEC FB" transmission of messages within the buffer size limit.
        """
        try:
            # Initialize the test result
            testResult = True

            # Set the number of log messages to generate
            logMsgCount = 115
            # Set the facility identifier
            iFacility = 1
            # Set the authentication identifier
            iAuthetication = 0
            # Define the log message
            logMsg = "This is TC2.3 of IEC Function Block Testing"

            # Assign values to the message, count, and authentication attributes
            self.strMessage = logMsg
            self.iMessage_Count = logMsgCount
            self.iAuthentication = iAuthetication
            self.iFacility = iFacility

            # Determine the log type based on the facility identifier
            logType = self.constants.USER_LOG if iFacility == 1 else self.constants.AUTH_LOG

            # Log the message and count information
            self.logger.info(f"Log '{logMsg}' in {logType} {logMsgCount} times")

            # Trigger the log message generation
            self.bTrigger_Log_Msg = True

            userSleep(3)

            # Verify the repeatability of the logs
            readLogMsgCount = self.verifyLogsRepeatability(logType = logType, detail = logMsg)

            # Check if the read log message count matches the buffer size limit (99)
            if readLogMsgCount == 99:
                testResult = True
                self.logger.info(f"the read log message count matches the buffer size limit {readLogMsgCount}")
            else:
                testResult = False
                self.logger.error(
                    f"Read log message count {readLogMsgCount} DOES NOT matches the buffer size limit 99")

            # Return the result of log format verification
            return testResult

        except Exception:
            # Log any exceptions that occur during test case execution
            self.logger.exception("Exception Occurred in TestCase13")
            return False

    #-----------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def grp_05_test_14(self) -> bool:
        """
        TC2.4 Verify that after an event of a network failure, the messages that have not yet been
        transferred from the buffer are lost by using "Auditlog IEC FB"
        """
        try:
            # Initialize the test result
            testResult = True

            # Set the number of log messages to generate
            logMsgCount = 115
            # Set the facility identifier
            iFacility = 1
            # Set the authentication identifier
            iAuthetication = 0
            # Define the log message
            logMsg = "This is TC2.4 of IEC Function Block Testing"

            # Assign values to the message, count, and authentication attributes
            self.strMessage = logMsg
            self.iMessage_Count = logMsgCount
            self.iAuthentication = iAuthetication
            self.iFacility = iFacility

            # Determine the log type based on the facility identifier
            logType = self.constants.USER_LOG if iFacility == 1 else self.constants.AUTH_LOG

            # Log the message and count information
            self.logger.info(f"Log '{logMsg}' in {logType} {logMsgCount} times")

            # Trigger the log message generation
            self.bTrigger_Log_Msg = True

            # disconnect
            self.ipcObjs[0].disconnect()

            # Simulate a network failure by switching off the controller
            switchOffController(logger = self.logger, controllerIP = self.ipAddresses[0],
                                ioPinList = self.ioPinList, pinName = "IPC_CtrlPower")

            # Switch the controller back on
            switchOnController(logger = self.logger, controllerIP = self.ipAddresses[0],
                               ioPinList = self.ioPinList, pinName = "IPC_CtrlPower")

            # Wait for the controller to restart
            self.logger.info("Waiting for 60sec....")
            userSleep(60)

            # Reconnect to the controller
            self.ipcObjs[0].connect()

            # Verify the repeatability of the logs and get message count
            readLogMsgCount = self.verifyLogsRepeatability(logType = logType, detail = logMsg)

            # Check if the read log message count does not match the expected count, indicating message loss
            if readLogMsgCount != logMsgCount:
                testResult = True
                self.logger.info(
                    "the read log message count does not match the expected count, indicating message loss ")
            else:
                testResult = False
                self.logger.error(
                    "the read log message count does not match the expected count, indicating NOT message loss")

            self.ipcObjs[0].disconnect()
            # Return the result of log format verification
            return testResult

        except Exception:
            # Log any exceptions that occur during test case execution
            self.logger.exception("Exception Occurred in TestCase14")
            return False

    #-------------------------------------------------------------------------------------------------------------------
    def grp_05_99_post(self):
        try:
            Lib_TLS.skipTestCases = False

        except Exception as exc:
            self.logger.error(f"Post Actions for Group 5 Failed: {exc}")
            Lib_TLS.skipTestCases = True

    #-------------------------------------------------------------------------------------------------------------------
    def grp_06_00_pre(self):
        """
        TC29.0: Verify that if the logs are updated at external server from syslog client after
        Deleted certificate them With TCP Connection and with Encryption.
        TC32.0: Verify Creation of New Lenze Syslog proxy certificate with Controller
        Start, Stop, Reset Cold, Reset Warm, Reset Origin.
        TC33.0: Verify Creation of New certificate with Controller Restart.
        TC30.0: Verify that if the logs are updated at external server from syslog client after creation of
        New certificate With TCP Connection and with Encryption.
        """
        try:
            if not self.grpSetup():
                self.logger.error("Group Setup Failed...Skipping the Group")
                Lib_TLS.skipTestCases = True
                raise Exception("Group Setup Failed")

            self.logger.newStep("Setting Syslog Severity To Max")
            self.setParamsUsingIPC(param = "0x5914:6", valueToBeSet = "255", ipcObj = self.ipcObjs[0])

        except Exception as exc:
            Lib_TLS.skipTestCases = True
            self.testCase.fail(f"Group Pre-Requisite Failed: {exc}")

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def grp_06_test_01(self) -> bool:
        """
        TC29.0: Verify that if the logs are updated at external server from syslog client after
        Deleted certificate them With TCP Connection and with Encryption.
        """
        try:
            testResult = True

            # setting syslog parameters
            self.setSyslogParams(protocol = self.constants.PROTOCOL["TCP"],
                                 encryption = self.constants.SERVER_ENCRYPTION["ENCRYPTED"],
                                 port = self.constants.PORT["TCP_TLS"])

            testResult = testResult and self.verifySyslogParams(
                expectedProtocol = self.constants.PROTOCOL_TYPES[1],
                expectedEncryption = self.constants.SERVER_ENCRYPTION["ENCRYPTED"],
                expectedPort = self.constants.PORT["TCP_TLS"])

            self.logger.newStep("Start PLC and Open Project")
            testResult = testResult and Lib_TLS.PLC_OBJ.startPlcAndOpenProj(
                version = self.configXlsObj.plcVersion,
                projPath = os.path.join(os.getcwd(),
                                        self.constants.PLC_PROJ_PATH.format(self.controllerTypes[0])),
                projName = self.constants.PLC_PROJ_NAME.format(self.controllerTypes[0]))

            self.logger.info(
                f"{[type(self).prefixCls]} Go Online and Upload all to read all parameters set via backend")
            testResult = testResult and Lib_TLS.PLC_OBJ.goOnline(
                upload = True, projName = self.constants.PLC_PROJ_NAME.format(self.controllerTypes[0]))

            self.logger.newStep("Delete 'Syslog Proxy Certificate'")
            retry = 3
            while retry:
                Lib_TLS.PLC_OBJ.deleteEncCommCert(
                    projName = self.constants.PLC_PROJ_NAME.format(self.controllerTypes[0]),
                    certificateType = self.constants.TYPE_CERTIFICATE[0],
                    certName = self.constants.CERT_NAME)

                if not Lib_TLS.PLC_OBJ.checkIfCertificateAvailable(
                    projName = self.constants.PLC_PROJ_NAME.format(self.controllerTypes[0]),
                    folderName = self.constants.TYPE_CERTIFICATE[1],
                    certificateName = self.constants.CERT_NAME_DELETED
                ):
                    self.logger.error(f"{[type(self).prefixCls]} Failed to Delete 'Syslog Proxy Certificate'")
                    self.logger.info("Trying to Delete 'Syslog Proxy Certificate' Again")
                    retry = retry - 1
                else:
                    self.logger.info(
                        f"{[type(self).prefixCls]} Successfully Deleted 'Syslog Proxy Certificate'")
                    break

            self.logger.newStep("Verify Certificate is deleted log message on external srver")
            self.verifyLogs(logType= self.constants.SERVER_LOG, validationType=Validate_Data.LOG_MESSAGE,
                            detailsToCheck = self.constants.LOG_DICTIONARY[
                                self.constants.SERVER_LOG]["keyNotAccessible"], extSSHClient = self.sshTlsServer)

            # performing start stop application to generate log and compare time stamp
            self.logger.newStep("Verifying if logs are getting updated on external server or not")
            Lib_TLS.PLC_OBJ.stopApplication(projName = self.constants.PLC_PROJ_NAME.format(self.controllerTypes[0]))
            Lib_TLS.PLC_OBJ.startApplication(projName = self.constants.PLC_PROJ_NAME.format(self.controllerTypes[0]))
            Lib_TLS.PLC_OBJ.stopApplication(projName = self.constants.PLC_PROJ_NAME.format(self.controllerTypes[0]))

            return testResult and self.compareMessagesInLogs(
                firstLogType = self.constants.LOCAL_LOG_0, secondLogType = self.constants.SERVER_LOG,
                logMessage = self.constants.LOG_DICTIONARY[self.constants.LOCAL_LOG_0]["startStopApp"],
                SSHClientSecond = self.sshTlsServer)

        except Exception:
            self.logger.exception("Exception Occurred in TestCase 1")
            return False

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def grp_06_test_02(self) -> bool:
        """
        TC32.0: Verify Creation of New Lenze Syslog proxy certificate with Controller
        Start, Stop, Reset Cold, Reset Warm, Reset Origin.
        """
        try:
            # performing operations one by one and checking certificate is not resent
            self.logger.newStep(f"{[type(self).prefixCls]} Start Application")
            Lib_TLS.PLC_OBJ.startApplication(projName = self.constants.PLC_PROJ_NAME.format(self.controllerTypes[0]))

            self.logger.info(f"{[type(self).prefixCls]} Verify Certificate is not auto created")
            if not Lib_TLS.PLC_OBJ.checkIfCertificateAvailable(
                projName = self.constants.PLC_PROJ_NAME.format(self.controllerTypes[0]),
                folderName = self.constants.TYPE_CERTIFICATE[0], certificateName = self.constants.CERT_NAME
            ):
                self.logger.info(f"{[type(self).prefixCls]} Certificate not avaliable...lets continue")
            else:
                self.logger.error(f"{[type(self).prefixCls]} Certificate is avaliable...Test Failed")
                return False

            self.logger.newStep(f"{[type(self).prefixCls]} Stop Application")
            Lib_TLS.PLC_OBJ.stopApplication(projName = self.constants.PLC_PROJ_NAME.format(self.controllerTypes[0]))

            self.logger.info(f"{[type(self).prefixCls]} Verify Certificate is not auto created")
            if not Lib_TLS.PLC_OBJ.checkIfCertificateAvailable(
                projName = self.constants.PLC_PROJ_NAME.format(self.controllerTypes[0]),
                folderName = self.constants.TYPE_CERTIFICATE[0], certificateName = self.constants.CERT_NAME
            ):
                self.logger.info(f"{[type(self).prefixCls]} Certificate not avaliable...lets continue")
            else:
                self.logger.error(f"{[type(self).prefixCls]} Certificate is avaliable...Test Failed")
                return False

            self.logger.newStep(f"{[type(self).prefixCls]} Reset Cold")
            Lib_TLS.PLC_OBJ.resetCold(projName  = self.constants.PLC_PROJ_NAME,
                                      header = self.constants.PLC_HEADER)

            self.logger.info(f"{[type(self).prefixCls]} Verify Certificate is not auto created")
            if not Lib_TLS.PLC_OBJ.checkIfCertificateAvailable(
                projName = self.constants.PLC_PROJ_NAME.format(self.controllerTypes[0]),
                folderName = self.constants.TYPE_CERTIFICATE[0], certificateName = self.constants.CERT_NAME
            ):
                self.logger.info(f"{[type(self).prefixCls]} Certificate not avaliable...lets continue")
            else:
                self.logger.error(f"{[type(self).prefixCls]} Certificate is avaliable...Test Failed")
                return False

            self.logger.newStep(f"{[type(self).prefixCls]} Reset Warm")
            Lib_TLS.PLC_OBJ.resetWarm(projName  = self.constants.PLC_PROJ_NAME, header = self.constants.PLC_HEADER)

            self.logger.info(f"{[type(self).prefixCls]} Verify Certificate is not auto created")
            if not Lib_TLS.PLC_OBJ.checkIfCertificateAvailable(
                projName = self.constants.PLC_PROJ_NAME.format(self.controllerTypes[0]),
                folderName = self.constants.TYPE_CERTIFICATE[0], certificateName = self.constants.CERT_NAME
            ):
                self.logger.info(f"{[type(self).prefixCls]} Certificate not avaliable...lets continue")
            else:
                self.logger.error(f"{[type(self).prefixCls]} Certificate is avaliable...Test Failed")
                return False

            Lib_TLS.PLC_OBJ.goOffline(projName = self.constants.PLC_PROJ_NAME.format(self.controllerTypes[0]),
                                      header = self.constants.PLC_HEADER)

            self.logger.newStep(f"{[type(self).prefixCls]} Reset Origin")
            self.ipcObjs[0].connect()
            self.ipcObjs[0].cmd.appResetOrigin()

            self.logger.info(f"{[type(self).prefixCls]} Verify Certificate is not auto created")
            if not Lib_TLS.PLC_OBJ.checkIfCertificateAvailable(
                projName = self.constants.PLC_PROJ_NAME.format(self.controllerTypes[0]),
                folderName = self.constants.TYPE_CERTIFICATE[0], certificateName = self.constants.CERT_NAME
            ):
                self.logger.info(f"{[type(self).prefixCls]} Certificate not avaliable...lets continue")
            else:
                self.logger.error(f"{[type(self).prefixCls]} Certificate is avaliable...Test Failed")
                return False

            self.ipcObjs[0].disconnect()  # much needed

            return True

        except Exception:
            self.logger.exception("Exception Occurred in TestCase 1")
            return False

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def grp_06_test_03(self) -> bool:
        try:
            self.logger.newStep("Restart Controller")
            self.ipcObjs[0].waitUntilBooted(switchOff = True, switchOn  = True,
                                            channel   = self.ipcObjs[0].getDefaultChannel())

            self.logger.info(f"{[type(self).prefixCls]} Verify 'Syslog Proxy' Certificate is auto created")
            Lib_TLS.PLC_OBJ.handlePLCConnectionLost(header = self.constants.PLC_HEADER)
            if Lib_TLS.PLC_OBJ.checkIfCertificateAvailable(
                projName = self.constants.PLC_PROJ_NAME.format(self.controllerTypes[0]),
                folderName = self.constants.TYPE_CERTIFICATE[0], certificateName = self.constants.CERT_NAME
            ):
                self.logger.info(f"{[type(self).prefixCls]} Certificate is avaliable...Test Passed")
            else:
                self.logger.error(f"{[type(self).prefixCls]} Certificate is not avaliable...Test Failed")
                return False

            self.logger.newStep("Download Boot Project")
            relBootProjectPath = "..\\project\\plcd\\" + f"{self.controllerTypes[0]}" + "\\boot"
            self.plcProject = self.ipcObjs[0].project(relPath = relBootProjectPath, relToFile = __file__)
            self.plcProject.download(startAppl = True, log = True, reboot = True)

            # setting syslog parameters
            # Activate  Sys Logging
            syslogDict = self.constants.PARAM_DICT["SYSLOG_PARAMETER"]
            isSyslogActivated = self.setParamsUsingIPC(param = syslogDict[0],
                                                       valueToBeSet = syslogDict[1], ipcObj = self.ipcObjs[0])
            if isSyslogActivated:
                self.logger.info(f"{[type(self).prefixCls]} Syslog Parameter Set to Activated")
            else:
                self.testCase.skip(f"{[type(self).prefixCls]} Failed to set Syslog Parameter To Activated")

            # setting other syslog parameters needed for the test
            self.setSyslogParams(protocol = self.constants.PROTOCOL["TCP"],
                                 encryption = self.constants.SERVER_ENCRYPTION["ENCRYPTED"],
                                 port = self.constants.PORT["TCP_TLS"])

            self.verifySyslogParams(expectedProtocol = self.constants.PROTOCOL_TYPES[1],
                                    expectedEncryption = self.constants.SERVER_ENCRYPTION["ENCRYPTED"],
                                    expectedPort = self.constants.PORT["TCP_TLS"])

            self.logger.newStep("Setting Log Severity to Maximum")
            syslogDict = self.constants.PARAM_DICT["SYSLOG_PARAMETER"]

            # Set Log Severity to full
            isSyslogSeveritySet = self.setParamsUsingIPC(param = "0x5914:6",
                                                         valueToBeSet = "255", ipcObj = self.ipcObjs[0])
            if isSyslogSeveritySet:
                self.logger.info(f"{[type(self).prefixCls]} Log Severity increased to full")
            else:
                self.testCase.skip(f"{[type(self).prefixCls]} Failed to Log Severity increased to full")

            index = self.constants.SYSLOG_PARAMS["SERVER_IP"][0].split(':')[0]
            subIndex = self.constants.SYSLOG_PARAMS["SERVER_IP"][0].split(':')[1]

            # changing ip address to required format(little endian)
            octets = self.constants.SERVER_IP.split('.')
            # Convert each octet to its hexadecimal equivalent and combine in reverse order (little-endian)
            littleEndianHex = ''.join(format(int(octet), '02X') for octet in octets[::-1])

            # Convert the little-endian hexadecimal string to an integer
            littleEndianInt = int(littleEndianHex, 16)

            serverIpObj = self.ipcObjs[0].objByIdx(index = int(index, 16), subIndex = int(subIndex, 16))
            serverIpObj.value = littleEndianInt
            self.ipcObjs[0].cmd.paramSave()
            userSleep(2)

            self.logger.info(f"{[type(self).prefixCls]} Setting syslog severity to Max")
            self.setParamsUsingIPC(param = "0x5914:6", valueToBeSet = "255", ipcObj = self.ipcObjs[0])

            self.logger.info(
                f"{[type(self).prefixCls]} Go Online and Upload all to read all parameters set via backend")
            Lib_TLS.PLC_OBJ.handlePLCConnectionLost(header = self.constants.PLC_HEADER)
            Lib_TLS.PLC_OBJ.goOnline(
                upload = True, projName = self.constants.PLC_PROJ_NAME.format(self.controllerTypes[0]))

            return True

        except Exception:
            self.logger.exception("Exception Occurred in TestCase 2")
            return False

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def grp_06_test_04(self) -> bool:
        try:
            self.logger.newStep("Delete 'Syslog Proxy Certificate'")
            retry = 3
            while retry:
                Lib_TLS.PLC_OBJ.deleteEncCommCert(
                    projName = self.constants.PLC_PROJ_NAME.format(self.controllerTypes[0]),
                    certificateType = self.constants.TYPE_CERTIFICATE[0],
                    certName = self.constants.CERT_NAME)

                if not Lib_TLS.PLC_OBJ.checkIfCertificateAvailable(
                    projName = self.constants.PLC_PROJ_NAME.format(self.controllerTypes[0]),
                    folderName = self.constants.TYPE_CERTIFICATE[1],
                    certificateName = self.constants.CERT_NAME_DELETED
                ):
                    self.logger.error(f"{[type(self).prefixCls]} Failed to Delete 'Syslog Proxy Certificate'")
                    self.logger.info("Trying to Delete 'Syslog Proxy Certificate' Again")
                    retry = retry - 1
                else:
                    self.logger.info(
                        f"{[type(self).prefixCls]} Successfully Deleted 'Syslog Proxy Certificate'")
                    break

            testResult = Lib_TLS.PLC_OBJ.createNewEncCertificate(
                projName = self.constants.PLC_PROJ_NAME.format(self.controllerTypes[0]),
                certificateType = self.constants.TYPE_CERTIFICATE[1],
                certName = self.constants.CERT_NAME_DELETED, keyLength = self.constants.CERT_KEY_LENGTH,
                validity = self.constants.CERT_VALIDITY)

            self.logger.info(
                f"{[type(self).prefixCls]} Go Online and Upload all to read all parameters set via backend")
            Lib_TLS.PLC_OBJ.goOnline(upload = True,
                                     projName = self.constants.PLC_PROJ_NAME.format(self.controllerTypes[0]))

            # performing start stop application to generate log and compare time stamp
            self.logger.newStep("Verifying if logs are getting updated on external server or not")
            Lib_TLS.PLC_OBJ.stopApplication(projName = self.constants.PLC_PROJ_NAME.format(self.controllerTypes[0]))
            Lib_TLS.PLC_OBJ.startApplication(projName = self.constants.PLC_PROJ_NAME.format(self.controllerTypes[0]))
            Lib_TLS.PLC_OBJ.stopApplication(projName = self.constants.PLC_PROJ_NAME.format(self.controllerTypes[0]))

            return testResult and self.compareMessagesInLogs(
                firstLogType = self.constants.LOCAL_LOG_0, secondLogType = self.constants.SERVER_LOG,
                logMessage = self.constants.LOG_DICTIONARY[self.constants.LOCAL_LOG_0]["startStopApp"],
                SSHClientSecond = self.sshTlsServer)
        except Exception:
            self.logger.exception("Exception Occurred in TestCase 3")
            return False

    #-------------------------------------------------------------------------------------------------------------------
    def grp_06_99_post(self):
        try:
            Lib_TLS.PLC_OBJ.goOffline(projName = self.constants.PLC_PROJ_NAME.format(self.controllerTypes[0]),
                                      header = self.constants.PLC_PROJ_NAME.format(self.controllerTypes[0]))

            self.logger.newStep("Close PLCD tool")
            if not Lib_TLS.PLC_OBJ.closePLC(projName = self.constants.PLC_PROJ_NAME.format(self.controllerTypes[0]),
                                            header = self.constants.PLC_PROJ_NAME.format(self.controllerTypes[0]),
                                            saveFlag = False):
                self.logger.warning(f"[{type(self).prefixCls}] Close Failed...")

        except Exception as exc:
            self.testCase.fail(f"Group Post-Requisite Failed: {exc}")

    #-------------------------------------------------------------------------------------------------------------------
