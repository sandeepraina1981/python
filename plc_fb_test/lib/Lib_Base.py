# -*- coding: utf-8 -*-
#
# © 2007-2008 Lenze Drive Systems GmbH. All rights reserved.
# © 2008-2021 Lenze Automation GmbH. All rights reserved.
#
#-----------------------------------------------------------------------------------------------------------------------
# PyTeF file header (for Test Library) V1.4-01
#-----------------------------------------------------------------------------------------------------------------------
# Disable linter warnings -> OTHER DISABLES ARE NOT RECOMMENDED, CHANGES ARE AT YOUR OWN RISK!
# pylint: disable=wildcard-import,unused-wildcard-import
# pylint: disable=broad-exception-raised
#
#-----------------------------------------------------------------------------------------------------------------------
# Test Library docstring (must be first definition in file)
#-----------------------------------------------------------------------------------------------------------------------
""" Library for OPC UA Automation Test. This include all the grouped test cases which will be called from test script
    This include common function which will be used by all the tools while running the test
"""
#-----------------------------------------------------------------------------------------------------------------------
# Test Library imports (must be defined before code)
#-----------------------------------------------------------------------------------------------------------------------
import time
from datetime import datetime
from itertools import zip_longest
from typing import Any, List, Tuple
from pytef.namespace.testlib import (FwTestLib, Version, autobehavior, Result, IpcFilter, IpcLenzeC520, IpcLenzeC550,
                                     tyOptBehavior, Boolean, VisibleString)
from pytef.resource.device.ipc.alpharelease import IpcLenzeC430
from pytef.namespace.testlib import (Signed16, ByteArray, Signed32, Unsigned32)
from tests.opc_ua.plc_fb_test.utils import constants_plc_fb as constants
from tests.opc_ua.plc_fb_test.utils.constants_plc_fb import FBTokenType
from tests.testlib.utils.CommonLib import (getDecodedPassword, userSleep)
from tests.opc_ua.plc_fb_test.utils.excelReader import ConfigExlParser
from tests.opc_ua.plc_fb_test.utils.excelReportUpdater import ReportExlParser

#-----------------------------------------------------------------------------------------------------------------------
# SVN keyword section
#-----------------------------------------------------------------------------------------------------------------------
FILE_URL = "$HeadURL: $"[10:-2]  # noqa:E501
FILE_REV = "$Revision: $"[11:-2]
FILE_DATE = "$LastChangedDate: $"[18:-2]
FILE_AUTHOR = "$LastChangedBy: raina $"[16:-2]

#-----------------------------------------------------------------------------------------------------------------------
# PyTeF file header end
#-----------------------------------------------------------------------------------------------------------------------
class Lib_Base(FwTestLib):
    """
        OPC UA FB Test Lib
    """
    prefixCls = 'Lib_Base'
    __LIB_DICT = {}

    LIB_NAME = "Lib_Base"
    LIB_VERSION = Version(1, 0, 0)

    #-------------------------------------------------------------------------------------------------------------------
    def __init__(self, xlsReaderObj: ConfigExlParser, reportUpdaterObj: ReportExlParser, fbTestModeList: [],
                 fbTestImpementation: str) -> None:
        """
        Constructor
        """
        self.logger.info(f"[{type(self).prefixCls}] in Lib_Base::__init__()")
        super().__init__()

        self.fbTestModeList = fbTestModeList
        self.fbTestImplementation = fbTestImpementation
        self.fbCurrentMode = None
        self.remarks = []
        self.fbverificationsresults = {}
        self.runningTestSessions = []

        # Initialize dictionaries for storing various OPC UA and Pytef-related server parameters.
        # These include external IP addresses, authentication details, user identity tokens,
        # method call URLs, error lists for read/write operations, and cycle counters.
        # Each dictionary will hold key-value pairs relevant to its respective configuration or runtime data.
        self.externalIpAddresses = {}
        self.sOutOpcUaMethodCallUrl_Server = {}
        self.xOutPytefExecuteServer = {}
        self.iAuth_ImplimentationServer = {}
        self.iAuthUserIdentityTokenType = {}
        self.sUserIdentityTokenParamUser = {}
        self.sUserIdentityTokenParamPassword = {}
        self.iInPytefStepNoServer = {}
        self.dwErrorId_StepServer = {}
        self.dwErrorIdServer = {}
        self.xInPytefConnectDoneServer = {}
        self.adwInPytefWriteNodeErrorListServer = {}
        self.adwInPytefReadNodeErrorListServer = {}
        self.aiInPytefWriteReadNodeErrorListServer = {}
        self.adwInPytefMethodErrorListServer = {}
        self.diInPytefCountCyclesServer = {}

        # Initialize the function block mode as an empty string.
        # This will later store the mode as any one of the following
        # (BROWSE, TRANSLATE PATH, FIXED NODE, B+T PASSING, B+T+F PASSING).
        self.iOutPytefMode = ""

        # Creating IPC obj
        try:
            ipcFilter = IpcFilter(ipcClass = [IpcLenzeC520, IpcLenzeC550, IpcLenzeC430])
            self.ipcObjs = self.testCase.resource.ipc(ipcFilter = ipcFilter, number = constants.MAX_CONTROLLERS)

            self.logger.info(f"[{type(self).prefixCls}] List of ipc {self.ipcObjs} ")

            # Log controller details
            self.logger.newStep("Controller Details")

            self.ipcHostController = next(iter(self.ipcObjs), None)
            self.logger.info(f"{[type(self).prefixCls]} Host Controller Ip :- "
                             f"{self.ipcHostController.channelList[0].address}")

            sessionIndex = constants.SESSION_START_INDEX

            for ipcObj in self.ipcObjs[1:]:
                # self.ipcObjs[1:] skips the first element and starts from the second
                # as the first element is the host controller and we are skipping it from the loop

                # 2 IP Address entries per controller to be mapped
                # Create entry for Session 1
                self.externalIpAddresses[sessionIndex] = ipcObj.channelList[0].address
                sessionIndex += sessionIndex

                # Create entry for Session 2
                self.externalIpAddresses[sessionIndex] = ipcObj.channelList[0].address
                sessionIndex += sessionIndex

                self.logger.info(f"{[type(self).prefixCls]} "
                                 f"External Server Controller Ip :- {ipcObj.channelList[0].address}")

                self.logger.info(f"{[type(self).prefixCls]} "
                                 f"Controller Type :- {self.findCtrlType(ipcObj)}")

        except Exception:  # pylint: disable=broad-exception-caught
            self.testCase.skipTest("Failed to create ipc object")

        self.logger.info(f"[{[type(self).prefixCls]}] in Lib_Base::__init__()")

        self.xlsReaderObj = xlsReaderObj
        self.reportUpdaterObj = reportUpdaterObj

        self._initiateSymbolicVariables()
        self.connect()

    #-------------------------------------------------------------------------------------------------------------------
    def setParamsUsingHostIpc(self, param, valueToBeSet):
        """
            This method is used to write parameter values using IPC
        """
        try:
            idx, subIdx = param.split(":")

            indexObj = self.ipcHostController.objByIdx(index = int(idx, 16), subIndex = int(subIdx))
            indexObj.value = valueToBeSet
            userSleep(2)

            self.ipcHostController.cmd.paramSave()
        except Exception as ex:
            print(ex)

    #-------------------------------------------------------------------------------------------------------------------
    def updateHostControllerTime(self, updateTimeInSeconds: int) -> None:
        """
        Update the host controller's clock relative to a fixed epoch using IPC parameters.

        This method:
          1. Sets a time base/selector via IPC parameter `"0x245c:1"` (value `194`),
             then waits briefly to let the controller apply the setting.
          2. Computes the elapsed time in **nanoseconds** from the fixed epoch
             `2000-01-01 00:00:00` to the current host time, plus an additional
             user-provided offset in seconds (`updateTimeInSeconds`).
          3. Writes the computed nanoseconds value to IPC parameter `"0x245c:2"`,
             then waits briefly again.

        Args:
            updateTimeInSeconds (int):
                Additional offset **in seconds** to add to the current host time
                when computing the controller's time. Use positive values to advance
                the controller time and negative values to set it slightly earlier.
        """

        self.setParamsUsingHostIpc(param = "0x245c:1", valueToBeSet = 194)
        userSleep(1)

        initial_date = datetime(2000, 1, 1, 0, 0, 0)
        current_time = datetime.now()
        time_difference = current_time - initial_date
        elapsed_nanoseconds = int(time_difference.total_seconds() + updateTimeInSeconds) * 1_000_000_000

        self.setParamsUsingHostIpc(param = "0x245c:2", valueToBeSet = elapsed_nanoseconds)
        userSleep(1)

        self.rebootController(device = self.ipcHostController)

    #-------------------------------------------------------------------------------------------------------------------
    def findCtrlType(self, ipcObj : List[Any]) -> str:
        """
        This method is used to map controller Type using IPC object
        """
        # map to hold controller name and type
        ctrlDict = {"c550" : ipcObj.isC550,
                    "c520" : ipcObj.isC520,
                    "c430" : ipcObj.isC430}

        for ctrlName, isPresent in ctrlDict.items():
            if isPresent:
                return ctrlName
        return ''

    #-------------------------------------------------------------------------------------------------------------------
    def __getSessionNumbers(self) -> range:
        """
        Generate a range of session numbers based on predefined constants.

        The range starts from `constants.SESSION_START_INDEX` and ends at
        `constants.SESSION_MAX[self.ipcHostController] + constants.SESSION_START_INDEX`.

        Returns:
            range: A Python range object representing the session numbers.

        Example:
            >>> self.__getSessionNumbers()
            range(1, 5)  # if SESSION_START_INDEX = 1 and SESSION_MAX[...] = 4
        """

        controllerType = self.findCtrlType(ipcObj = self.ipcHostController)

        return range(constants.SESSION_START_INDEX,
                     constants.SESSION_MAX[controllerType] + constants.SESSION_START_INDEX)

    #-------------------------------------------------------------------------------------------------------------------
    def rebootController(self, device: Any) -> bool:
        """
        Summary of the rebootController function.

        Args:
            device: IPC object of the device.

        Returns:
            TYPE: Description of return value.
        """

        self.logger.newStep(f"Reboot of the controller with IP {device.channelList[0].address} started")
        rebootStatus = True

        try:
            device.disconnect()
        except Exception as ex:
            self.logger.warn(f"Error in disconnect() due to {ex}")

        try:
            device.connect()
        except Exception as ex:
            self.logger.warn(f"Error in connect() due to {ex}")

        try:
            device.cmd.appStop()
        except Exception as ex:
            self.logger.warn(f"Error in appStop() due to {ex}")

        try:
            device.cmd.devReboot()
        except Exception as ex:
            self.logger.warn(f"Error in devReboot() due to {ex}")
            rebootStatus = False

        time.sleep(10)

        try:
            device.disconnect()
        except Exception as ex:
            self.logger.warn(f"Error in disconnect() due to {ex}")

        try:
            device.connect()
        except Exception as ex:
            self.logger.warn(f"Error in connect() due to {ex}")

        if rebootStatus:
            self.logger.info("Controller Rebooted")
        else:
            self.logger.warn("Controller Reboot failed due to an error")

        self.logger.newStep(f"Reboot of the controller with IP {device.channelList[0].address} completed")

        return rebootStatus

    #-------------------------------------------------------------------------------------------------------------------
    def __getMemoryObject(self, symbolName, dataType):
        """
        Summary of the __getMemoryObject function.

        Args:
            symbolName: Provide the symbol name.
            dataType: Provide the dataType of the symbol name.
        """

        self.logger.info(f"[{type(self).prefixCls}] Creating memory object for symbol name {symbolName}")

        memObj = self.ipcHostController.plc.memObj(symbolName = symbolName, dataType = dataType)
        return memObj

    #-------------------------------------------------------------------------------------------------------------------
    def downloadPlcdProjects(self) -> bool:
        """
        This method is used to download PLCD project to the controllers
        """

        currControllerType = ""
        currIpAddr = ""

        try:
            for index, ipcObj in enumerate(self.ipcObjs):
                currControllerType = self.findCtrlType(ipcObj)
                currIpAddr = ipcObj.channelList[0].address

                if index == 0:
                    relBootProjectPath = "..\\projects\\plcd\\client\\" + f"{currControllerType}" + "\\boot"
                    self.logger.newStep(f"Download Boot Project in host controller {currControllerType} with "
                                        f"IP Address  {currIpAddr} from path {relBootProjectPath}")
                else:
                    relBootProjectPath = "..\\projects\\plcd\\server\\" + f"{currControllerType}" + "\\boot"
                    self.logger.newStep(f"Download Boot Project in client controller {currControllerType} with "
                                        f"IP Address {currIpAddr} from path {relBootProjectPath}")

                plcProject = ipcObj.project(relPath = relBootProjectPath, relToFile = __file__)
                plcProject.download(startAppl = True, log = True, reboot = True)

                self.logger.newStep(f"Boot Project downloaded in {currControllerType} with IP Address {currIpAddr}")
        except Exception:
            return False

        return True

    #-------------------------------------------------------------------------------------------------------------------
    def restartControllers(self) -> None:
        """
        This method is used to restart the controllers
        """

        for ipcObj in self.ipcObjs:
            currControllerType = self.findCtrlType(ipcObj)
            currIpAddr = ipcObj.channelList[0].address

            self.logger.newStep(f"Restart Controller {currControllerType} with IP Address {currIpAddr}")
            self.rebootController(ipcObj)
            self.logger.newStep(f"{currControllerType} restarted with IP Address {currIpAddr}")

    #-------------------------------------------------------------------------------------------------------------------
    def connect(self) -> None:
        """
        This method is used to connect with the controllers
        """

        self.logger.newStep("Initiate connect for ipc objects - Started")
        for ipcObj in self.ipcObjs:
            ipcObj.connect()
        self.logger.newStep("Initiate connect for ipc objects - Completed")

    #-------------------------------------------------------------------------------------------------------------------
    def disConnect(self) -> None:
        """
        This method is used to disconnect with the controllers
        """

        self.logger.newStep("Initiate disconnect for ipc objects - Started")
        for ipcObj in self.ipcObjs:
            ipcObj.disconnect()
        self.logger.newStep("Initiate disconnect for ipc objects - Completed")

    #-------------------------------------------------------------------------------------------------------------------
    def _executeGroup(self, testType: str) -> Tuple[List[bool], List[List[str]]]:
        """
        Execute a group of Function Block (FB) tests for a given test type.

        This method iterates through all configured FB test modes, sets up sessions,
        applies configurations, executes tests, and aggregates results and remarks.

        Workflow:
            1. For each FB mode in `self.fbTestModeList`:
                - Set the current mode.
                - Map session IP addresses based on the test type.
                - Configure session URLs, mode, and implementations.
                - Enable sessions and execute tests.
                - Verify OpenPLC client function block behavior.
                - Disable sessions and restart controllers.
            2. Aggregate results and remarks across all modes using logical AND for results
               and concatenation for remarks.

        Args:
            testType (str): The type of test to execute (e.g., "Internal", "External", "Multiple").

        Returns:
            tuple[list[bool], list[list[str]]]:
                - returnResult: A list of boolean values indicating pass/fail for each session.
                - returnRemarks: A list of lists containing remarks for each session.
        """

        returnResult = []
        returnRemarks = []

        for fbCurrentMode in self.fbTestModeList:
            self.fbCurrentMode = fbCurrentMode

            # Disable the sessions
            self.executeSessions(False)
            self.restartControllers()

            self.mapSessionIPAddresses(testType = testType)
            self.setSessionURLs(isSessionURLEmpty = True)
            self.setSessionURLs()
            self.setMode()
            self.setImplementations()

            # Enable the sessions
            self.executeSessions(executeValue = True)
            result = self.verifyOpenPlcClientFunctionBlock(testType = testType)

            returnResult = [currResult and previousResult
                            for currResult, previousResult in zip_longest(returnResult, result, fillvalue = True)]

            returnRemarks = [currRemarks + previousRemarks
                             for currRemarks, previousRemarks in zip_longest(returnRemarks,
                                                                             self.remarks, fillvalue = [])]

        return returnResult, returnRemarks

    #-------------------------------------------------------------------------------------------------------------------
    def mapSessionIPAddresses(self, testType: str) -> None:
        """
        Summary of the mapSessionIPAddresses function.

        Args:
            testType: Provide the type of test (INTERNAL/MULTIPLE/EXTERNAL).
        """

        if testType is not constants.TestType.INTERNAL.value:
            if len(self.externalIpAddresses) == 1:
                self.testCase.skipTest("Cannot proceed with multiple or external server tests as only host configured")

        self.runningTestSessions = []

        for sessionNumber in self.__getSessionNumbers():
            if self.xlsReaderObj.sessionConnectFlags[sessionNumber]:

                if testType is constants.TestType.INTERNAL.value:
                    self.runningTestSessions.append(
                        {"sessionNumber": sessionNumber,
                         "ipaddress": self.ipcHostController.channelList[0].address})
                else:
                    if sessionNumber <= len(self.externalIpAddresses):
                        self.runningTestSessions.append({"sessionNumber": sessionNumber,
                                                         "ipaddress": self.externalIpAddresses[sessionNumber]})

    #-------------------------------------------------------------------------------------------------------------------
    def setSessionURLs(self, isSessionURLEmpty = False):
        """
        This method is used to set FB client urls for Open PLC connections
        """

        self.logger.newStep("Create Sessions - Started")
        sessionURL = ""

        try:
            for activeSession in self.runningTestSessions:
                sessionIp = activeSession["ipaddress"]
                sessionNumber = activeSession["sessionNumber"]

                if isSessionURLEmpty is False:
                    sessionURL = constants.PLC_OPEN_CLIENT_SERVER_URL.format(sessionIp)

                result = self.sOutOpcUaMethodCallUrl_Server[sessionNumber].setValue(sessionURL)

                if not result.isOK:
                    self.testCase.skipTest(f"Create session failed while adding url with ipaddress {sessionIp} "
                                           f"for session {sessionNumber}")
                    return False

                time.sleep(1)

        except Exception:  # pylint: disable=broad-exception-caught
            self.testCase.skipTest(f"Create session failed while adding url with ipaddress {sessionIp} for session "
                                   f"{sessionNumber}")
            return False

        self.logger.newStep("Create Sessions - Completed")
        return True

    #-------------------------------------------------------------------------------------------------------------------
    def executeSessions(self, executeValue: bool) -> bool:
        """
        This method is used to set FB client urls for Open PLC connections
        """

        self.logger.newStep(f"Set execute as {executeValue} for the sessions")

        try:
            for activeSession in self.runningTestSessions:
                sessionNumber = activeSession["sessionNumber"]
                result = self.xOutPytefExecuteServer[sessionNumber].setValue(executeValue)

                if not result.isOK:
                    self.testCase.skipTest(f"Execute session failed while setting execute value as {executeValue} "
                                           f"for session {sessionNumber}")
                    return False

                time.sleep(1)

        except Exception:  # pylint: disable=broad-exception-caught
            self.testCase.skipTest(f"Execute session failed while setting execute value as {executeValue} for session "
                                   f"{sessionNumber}")
            return False

        self.logger.newStep(f"Set execute as {executeValue} for the sessions - Successfull")
        return True

    #-------------------------------------------------------------------------------------------------------------------
    def setImplementations(self) -> bool:
        """
        This method is used to set Implementations for Open PLC FB Tests
        """

        self.logger.newStep(f"Start to set the Implementation as {self.fbTestImplementation.name} for the sessions")

        try:
            for activeSession in self.runningTestSessions:
                sessionNumber = activeSession["sessionNumber"]
                result = self.iAuth_ImplimentationServer[sessionNumber].setValue(self.fbTestImplementation.value)

                if not result.isOK:
                    self.testCase.skipTest(f"Setting implementation as {self.fbTestImplementation.name} for session "
                                           f"{sessionNumber} failed")
                    return False

                time.sleep(1)

        except Exception:  # pylint: disable=broad-exception-caught
            self.testCase.skipTest(f"Setting implementation as {self.fbTestImplementation.name} for session "
                                   f"{sessionNumber} failed")
            return False

        self.logger.newStep("Completed setting the Implementation for the sessions")
        return True

    #-------------------------------------------------------------------------------------------------------------------
    def setMode(self) -> bool:
        """
        This method is used to set the Mode
        """

        self.logger.newStep("Start to set the Mode")

        result = self.iOutPytefMode.setValue(self.fbCurrentMode.value)

        if not result.isOK:
            self.testCase.skipTest(f"Failed to set {constants.PLC_OPEN_CLIENT_MODE_SYMBOL_NAME} to mode value "
                                   f"{self.fbCurrentMode.name}")
            return False

        self.logger.info(f"[{type(self).prefixCls}] Successfully set mode value {self.fbCurrentMode.name}")

        time.sleep(1)

        self.logger.newStep("Successfully set the Mode")
        return True

    #-------------------------------------------------------------------------------------------------------------------
    def setTokenType(self, tokenType: FBTokenType) -> bool:
        """
        This method is used to set User Identity Token Type for Open PLC FB Tests
        """

        self.logger.newStep(f"Start to set the Token Type as {tokenType.name} for the sessions")

        try:
            for activeSession in self.runningTestSessions:
                sessionNumber = activeSession["sessionNumber"]
                result = self.iAuthUserIdentityTokenType[sessionNumber].setValue(tokenType.value)

                if not result.isOK:
                    self.testCase.skipTest(f"Setting Token Type as {tokenType.value} for session "
                                           f"{sessionNumber} failed")
                    return False

                time.sleep(1)

        except Exception:  # pylint: disable=broad-exception-caught
            self.testCase.skipTest(f"Setting Token Type as {tokenType.name} for session "
                                   f"{sessionNumber} failed")
            return False

        self.logger.newStep("Completed setting the Token Type for the sessions")
        return True

    #-------------------------------------------------------------------------------------------------------------------
    def setUserIdentityTokenCredentials(self, tokenType: FBTokenType) -> bool:
        """
        This method is used to set User Identity Token with Credentials for Open PLC FB Tests
        """

        self.logger.newStep("Start to set User Identity Token with Credentials for the sessions")

        userName = ""
        userPassword = ""

        try:
            for activeSession in self.runningTestSessions:
                sessionNumber = activeSession["sessionNumber"]

                if tokenType == FBTokenType.USERNAME:
                    userName = constants.USERS_DETAILS_DICT["administratorUser"]["userName"]
                    userPassword = getDecodedPassword(
                        base64EncryptedPassword = constants.USERS_DETAILS_DICT["administratorUser"]["password"],
                        logger = self.logger)

                if tokenType == FBTokenType.USERTOKENID:
                    userName = constants.PLC_OPEN_CLIENT_UA_CLIENT_UI.format(sessionNumber)

                result = self.sUserIdentityTokenParamUser[sessionNumber].setValue(userName)

                if not result.isOK:
                    self.testCase.skipTest(f"Setting User Identity Token User for session {sessionNumber} failed")
                    return False

                time.sleep(1)

                result = self.sUserIdentityTokenParamPassword[sessionNumber].setValue(userPassword)

                if not result.isOK:
                    self.testCase.skipTest(f"Setting User Identity Token Password for session "
                                           f"{sessionNumber} failed")
                    return False

                time.sleep(1)

        except Exception:  # pylint: disable=broad-exception-caught
            self.testCase.skipTest(f"Setting User Identity Token with Credentials for the session "
                                   f"{sessionNumber} failed")
            return False

        self.logger.newStep("Completed setting the User Identity Token with Credentials for the sessions")
        return True

    #-------------------------------------------------------------------------------------------------------------------
    def setParameterUsers(self, authType: FBTokenType) -> bool:
        """
        Set OPC UA client username/password parameters for up to six clients on the host IPC.

        When `isCredentialsRequired` is `True`, the method pulls administrator credentials
        from `constants.USERS_DETAILS_DICT["administratorUser"]`, decoding the stored
        (base64-encrypted) password via `getDecodedPassword`. When `False`, it writes empty
        credentials, effectively clearing any configured usernames/passwords for all six clients.

        For each client (1 through 6), the following parameter indices are written:
            - Username: 0x2477:100 .. 0x2477:110 (even indices)
            - Password: 0x2477:101 .. 0x2477:111 (odd indices)

        Args:
            isCredentialsRequired (bool, optional):
                If True, writes the administrator username and decoded password.
                If False, writes empty strings for both username and password.
                Defaults to False.
        """

        userName = ""
        passWord = ""

        if authType == FBTokenType.USERTOKENID:
            userName = constants.USERS_DETAILS_DICT["administratorUser"]["userName"]
            passWord = getDecodedPassword(
                            base64EncryptedPassword = constants.USERS_DETAILS_DICT["administratorUser"]["password"],
                            logger = self.logger)

        # Update username and password Client 1
        self.setParamsUsingHostIpc(param = "0x2477:100", valueToBeSet = userName)
        self.setParamsUsingHostIpc(param = "0x2477:101", valueToBeSet = passWord)

        # Update username and password Client 2
        self.setParamsUsingHostIpc(param = "0x2477:102", valueToBeSet = userName)
        self.setParamsUsingHostIpc(param = "0x2477:103", valueToBeSet = passWord)

        # Update username and password Client 3
        self.setParamsUsingHostIpc(param = "0x2477:104", valueToBeSet = userName)
        self.setParamsUsingHostIpc(param = "0x2477:105", valueToBeSet = passWord)

        # Update username and password Client 4
        self.setParamsUsingHostIpc(param = "0x2477:106", valueToBeSet = userName)
        self.setParamsUsingHostIpc(param = "0x2477:107", valueToBeSet = passWord)

        # Update username and password Client 5
        self.setParamsUsingHostIpc(param = "0x2477:108", valueToBeSet = userName)
        self.setParamsUsingHostIpc(param = "0x2477:109", valueToBeSet = passWord)

        # Update username and password Client 6
        self.setParamsUsingHostIpc(param = "0x2477:110", valueToBeSet = userName)
        self.setParamsUsingHostIpc(param = "0x2477:111", valueToBeSet = passWord)

    #-------------------------------------------------------------------------------------------------------------------
    def logTestDescription(self, result: [], isEnd: bool = False) -> None:
        """
        log Test Description
        """
        try:
            grpName = self.xlsReaderObj.getGroupName(testCaseName = self.testCase.testCaseName)
            jiraIdList = self.xlsReaderObj.getJiraIdListByGroup(testGroupName = grpName)

            if not isEnd:
                self.logger.newStep(f"START : Verification of Test Group {grpName}")

            for jiraId, testResult in zip_longest(jiraIdList, result, fillvalue = True):
                # read test case description from the report file

                testDesc = self.reportUpdaterObj.getTestDescription(jiraId = jiraId)
                testCaseNumber = self.reportUpdaterObj.getTestCaseNumber(jiraId = jiraId)

                if not isEnd:
                    self.logger.newStep(f"START : TC Jira: {jiraId}, TC {testCaseNumber} {testDesc}",
                                        level = 1)

                if isEnd:
                    if testResult:
                        self.logger.newStep(f"END : TC Jira: {jiraId}, TC {testCaseNumber} {testDesc} "
                                            f"- PASSED", level = 1)
                    else:
                        self.logger.error("#" * 160)
                        self.logger.error(f"END : TC Jira: {jiraId}, TC {testCaseNumber} {testDesc} - FAILED")
                        self.logger.error("#" * 160)

        except IndexError:
            self.logger.warning(f"[{[type(self).prefixCls]}] Could not get test description from Report")
            self.logger.warning(f"[{[type(self).prefixCls]}] No jira id found in device config")

        finally:
            if isEnd:
                if all(result):
                    self.logger.newStep(f"END : Verification of Test Group {grpName} - SUCCESSFULL", level = 1)
                else:
                    self.testCase.fail(f"END : Verification of Test Group {grpName} - UNSUCCESSFULL")

    #-------------------------------------------------------------------------------------------------------------------
    def saveTestResult(self, results: [], remarks: []) -> None:
        """
        This method is used to get the current testcase jira and then update the result against that jira in report
        """
        try:
            grpName = self.xlsReaderObj.getGroupName(testCaseName = self.testCase.testCaseName)
            jiraIdList = self.xlsReaderObj.getJiraIdListByGroup(testGroupName = grpName)
            testSession = "\n".join("Session " + str(activeSession["sessionNumber"])
                                    for activeSession in self.runningTestSessions)

            for jiraId, testResult, testRemark in zip(jiraIdList, results, remarks):
                # Updating result in report
                if testResult is not None:
                    self.reportUpdaterObj.updateResult(jiraId = jiraId, result = testResult,
                                                       remark = "\n".join(testRemark),
                                                       mode = self.fbCurrentMode.name,
                                                       implementation = self.fbTestImplementation.name,
                                                       session = testSession)

        except Exception:  # pylint: disable=broad-exception-caught
            self.logger.exception(f"[{type(self).prefixCls}] Exception occurred in saveTestResult()")

    #-------------------------------------------------------------------------------------------------------------------
    def resetPreviousTestReportResult(self) -> None:
        """
        This method is used to reset the result id in the test report
        """
        try:
            testCaseGroups = self.xlsReaderObj.testCaseSelectionDict

            for currentTestCaseGroup, testCaseNames in testCaseGroups.items():
                for testCaseName in testCaseNames.keys():
                    test_case = self.xlsReaderObj.testCaseSelectionDict.get(currentTestCaseGroup).get(testCaseName)
                    jiraId = test_case.get("jira")

                    # Updating result in report
                    self.reportUpdaterObj.updateResult(jiraId = jiraId, result = "Not Executed", remark = "",
                                                       mode = "", implementation = "",
                                                       session = "")

        except Exception:  # pylint: disable=broad-exception-caught
            self.logger.exception(f"[{type(self).prefixCls}] Exception occurred in saveTestResult()")

    #-------------------------------------------------------------------------------------------------------------------
    def _validateStepNumbersUpdating(self) -> None:
        """
        Validate that step numbers for all active sessions are updating correctly.

        This method performs a two-phase check:
            1. Captures the current step number for each active session.
            2. Waits for a short interval and verifies that the step number has incremented.

        If any session's step number does not update or remains zero, the test is skipped
        with an appropriate message.

        Workflow:
            - Iterate through all running test sessions.
            - Fetch the current step number using `iInPytefStepNoServer[sessionNumber].getValue()`.
            - Ensure the value is greater than zero; otherwise, skip the test.
            - Sleep for 1 second.
            - Re-check the step number and compare with the previous value.
            - If unchanged, skip the test.
        """

        sessionResult = [None]

        for activeSession in self.runningTestSessions:
            sessionNumber = activeSession["sessionNumber"]
            result = self.iInPytefStepNoServer[sessionNumber].getValue()

            if result.isOK:
                if not result.value > 0:
                    self.testCase.skipTest(f"[Pre-check]: Step numbers not updating for {sessionNumber}: "
                                           f"as value displayed is {result.value}")

                sessionResult.append(result.value)
            time.sleep(1)

        time.sleep(10)

        for activeSession in self.runningTestSessions:
            sessionNumber = activeSession["sessionNumber"]
            result = self.iInPytefStepNoServer[sessionNumber].getValue()

            if result.isOK:
                if not result.value > 0:
                    self.testCase.skipTest(f"[Pre-check]: Step numbers not updating for Server {sessionNumber}: "
                                           f"as value displayed is {result.value}")

                if result.value == sessionResult[sessionNumber]:
                    time.sleep(1)
                    result = self.iInPytefStepNoServer[sessionNumber].getValue()
                    if result.isOK:
                        if result.value == sessionResult[sessionNumber]:
                            self.testCase.skipTest(f"[Pre-check]: Step numbers not updating for {sessionNumber}: "
                                                   f"as value displayed is {result.value}")
            time.sleep(1)

    #-------------------------------------------------------------------------------------------------------------------
    def _validateCycleCountUpdating(self) -> None:
        """
        Validate that the cycle count for each active session is updating over time.

        This method performs a pre-check to ensure that the cycle count values for
        all running test sessions are incrementing as expected. It works in two phases:

        1. Capture initial cycle count values for all active sessions.
           - If any session reports a non-positive value (<= 0), the test is skipped.
        2. Wait for 60 seconds and re-check the cycle count values.
           - If any session still reports a non-positive value or the value has not changed
             since the initial check, the test is skipped.
        """

        sessionResult = [None]

        for activeSession in self.runningTestSessions:
            sessionNumber = activeSession["sessionNumber"]
            result = self.diInPytefCountCyclesServer[sessionNumber].getValue()

            if result.isOK:
                if not result.value > 0:
                    self.testCase.skipTest(f"[Pre-check]: Count cycles not updating for {sessionNumber}: "
                                           f"as value displayed is {result.value}")

                sessionResult.append(result.value)

        time.sleep(60)

        for activeSession in self.runningTestSessions:
            sessionNumber = activeSession["sessionNumber"]
            result = self.diInPytefCountCyclesServer[sessionNumber].getValue()

            if result.isOK:
                if not result.value > 0:
                    self.testCase.skipTest(f"[Pre-check]: Count cycles not updating for {sessionNumber}: "
                                           f"as value displayed is {result.value}")

                if result.value == sessionResult[sessionNumber]:
                    self.testCase.skipTest(f"[Pre-check]: Count cycles not updating for {sessionNumber}: "
                                           f"as value displayed is {result.value}")

    #-------------------------------------------------------------------------------------------------------------------
    def _validateConnectStatus(self) -> None:
        """
        Validates the connection status for all active test sessions.

        This method continuously checks whether all running test sessions have completed
        their "Connect Done" status within a specified wait period. It polls the status
        from `self.xInPytefConnectDoneServer` for each session and aggregates the results.
        If any session fails to reach the expected state within the timeout, the test case
        is marked as skipped for those sessions.

        Workflow:
            1. Initialize a wait counter and a flag for connection completion.
            2. Loop until either all sessions report success or the timeout is reached:
                - For each active session, retrieve its connection status.
                - Append the status to `sessionResult`.
                - Check if all sessions are connected.
                - Sleep for 1 second between checks.
            3. If not all sessions are connected after the timeout:
                - Identify sessions that failed.
                - Skip the test case for those sessions with an appropriate message.

        Attributes Used:
            - self.runningTestSessions (List[Dict]): Active test sessions with session numbers.
            - self.xInPytefConnectDoneServer (Dict): Mapping of session numbers to status objects.
            - self.testCase.skipTest (Callable): Method to skip the test case when pre-check fails.
        """

        waitIndex = 60
        connectDone = False

        sessionResult = []

        while connectDone is False:
            for activeSession in self.runningTestSessions:
                sessionNumber = activeSession["sessionNumber"]
                result = self.xInPytefConnectDoneServer[sessionNumber].getValue()

                if result.isOK:
                    sessionResult.append(result.value)

            connectDone = all(sessionResult)

            time.sleep(1)
            waitIndex -= 1

            if waitIndex == 0:
                break

        if connectDone is False:
            for index, value in enumerate(sessionResult):
                if value is False:
                    currSessionNumber = self.runningTestSessions[index]["sessionNumber"]
                    self.testCase.skipTest(f"[Pre-check]: Connect Done {value} for {currSessionNumber}")

    #-------------------------------------------------------------------------------------------------------------------
    def _verifyFailedStepAfterConnect(self) -> bool:
        """
        Verifies if any function block execution step failed after the connection phase and logs remarks.

        This method checks all active test sessions for non-zero error IDs after the connection
        process. If any session reports a failed step, it logs an error and adds a remark entry
        for multiple test categories (READ, WRITE, READ-WRITE, and optionally METHOD EXECUTION).

        Workflow:
            1. Initialize a remark list with the current mode and implementation details.
            2. For each active session:
                - Retrieve the error ID from `dwErrorId_StepServer`.
                - If the error ID is non-zero, log the failure and append a remark.
            3. Append the collected remarks to `self.remarks` for:
                - READ VARIABLES FB Test
                - WRITE VARIABLES FB Test
                - READ-WRITE VARIABLES FB Test
                - METHOD EXECUTION FB Test (if supported by implementation type).

        Attributes Used:
            - self.fbCurrentMode (str): Current function block mode under test.
            - self.fbTestImplementation (Enum): Implementation type for the test.
            - self.runningTestSessions (List[Dict]): Active test sessions with session numbers.
            - self.dwErrorId_StepServer (Dict): Mapping of session numbers to error ID objects.
            - self.logger (Logger): Logger instance for error reporting.
            - self.remarks (List[List[str]]): Aggregated remarks for reporting.
            - constants.FBImplementation.VARIABLE_RW_METHOD_CONNECT: Enum value for method execution support.
        """

        testResult = True
        createRemarks = []

        createRemarks.append(f"For Mode: {self.fbCurrentMode.name} and "
                             f"Implementation: {self.fbTestImplementation.name}")

        for activeSession in self.runningTestSessions:
            sessionNumber = activeSession["sessionNumber"]
            result = self.dwErrorId_StepServer[sessionNumber].getValue()

            if result.isOK:
                if not result.value == 0:
                    testResult = testResult and False
                    createRemarks.append(f"Server {sessionNumber} returned failed step number {result} - FAILED")
                    self.logger.error(f"Server {sessionNumber} returned failed step number {result} - FAILED")
                else:
                    testResult = testResult and True
                    createRemarks.append(f"Server {sessionNumber} returned no failed step number - SUCCESSFULL")
                    self.logger.info(f"Server {sessionNumber} returned no failed step number - SUCCESSFULL")

        # Create Remark Entry for READ VARIABLES FB Test
        self.remarks.append(createRemarks)

        # Create Remark Entry for WRITE VARIABLES FB Test
        self.remarks.append(createRemarks)

        # Create Remark Entry for READ-WRITE VARIABLES FB Test
        self.remarks.append(createRemarks)

        # If Implementation type supports METHOD then Create Remark Entry for METHOD EXECUTION FB Test
        if self.fbTestImplementation == constants.FBImplementation.VARIABLE_RW_METHOD_CONNECT:
            self.remarks.append(createRemarks)

        return testResult

    #-------------------------------------------------------------------------------------------------------------------
    def _checkFailedStepErrorId(self) -> []:
        """
        Checks for failed execution steps based on error IDs and aggregates results for multiple FB tests.

        This method iterates through all active test sessions and verifies if any session reports
        a non-zero error ID after execution. If an error is detected, it logs the failure and adds
        remarks. It then creates result entries for different function block (FB) test categories:
        READ, WRITE, READ-WRITE, and optionally METHOD EXECUTION.

        Workflow:
            1. Initialize `testResult` as True and empty lists for remarks and results.
            2. For each active session:
                - Retrieve the error ID from `dwErrorId_StepServer`.
                - If non-zero, mark `testResult` as False, log the error, and add a remark.
            3. Append remarks and corresponding boolean results for:
                - READ VARIABLES FB Test
                - WRITE VARIABLES FB Test
                - READ-WRITE VARIABLES FB Test
                - METHOD EXECUTION FB Test (if supported by implementation type).
            4. Return the aggregated list of boolean results.

        Attributes Used:
            - self.runningTestSessions (List[Dict]): Active test sessions with session numbers.
            - self.dwErrorId_StepServer (Dict): Mapping of session numbers to error ID objects.
            - self.logger (Logger): Logger instance for error reporting.
            - self.remarks (List[List[str]]): Aggregated remarks for reporting.
            - self.fbTestImplementation (Enum): Implementation type for the test.
            - constants.FBImplementation.VARIABLE_RW_METHOD_CONNECT: Enum value for method execution support.
        """

        testResult = True
        createRemarks = []
        retResult = []

        for activeSession in self.runningTestSessions:
            sessionNumber = activeSession["sessionNumber"]
            result = self.dwErrorId_StepServer[sessionNumber].getValue()

            if result.isOK:
                if not result.value == 0:
                    testResult = testResult and False
                    createRemarks.append(f"Server {sessionNumber} returned error id {result} - FAILED")
                    self.logger.error(f"Server {sessionNumber} returned error id {result} - FAILED")

        # Create Remark Entry and Result for READ VARIABLES FB Test
        self.remarks.append(createRemarks)
        if testResult:
            retResult.append(True)
        else:
            retResult.append(False)

        # Create Remark Entry and Result for WRITE VARIABLES FB Test
        self.remarks.append(createRemarks)
        if testResult:
            retResult.append(True)
        else:
            retResult.append(False)

        # Create Remark Entry and Result for READ-WRITE VARIABLES FB Test
        self.remarks.append(createRemarks)
        if testResult:
            retResult.append(True)
        else:
            retResult.append(False)

        # If Implementation type supports METHOD then Create Remark Entry and Result for METHOD EXECUTION FB Test
        if self.fbTestImplementation == constants.FBImplementation.VARIABLE_RW_METHOD_CONNECT:
            self.remarks.append(createRemarks)
            if testResult:
                retResult.append(True)
            else:
                retResult.append(False)

        return retResult

    #-------------------------------------------------------------------------------------------------------------------
    def _verifyReadVariables(self) -> bool:
        """
        Verifies that all active sessions successfully read variables without errors.

        This method checks each active test session for errors in reading variables by
        querying `adwInPytefReadNodeErrorListServer`. If all sessions return no errors,
        the test passes; otherwise, it fails. It also logs the results and stores verification
        details for reporting.

        Workflow:
            1. Initialize remarks and set `testResult` to True.
            2. For each active session:
                - Retrieve the error list for READ variables.
                - If all values indicate no error, log success and keep `testResult` True.
                - Otherwise, log failure and set `testResult` to False.
                - Update `fbverificationsresults` with session-specific details.
            3. Append remarks for the READ VARIABLES FB Test.
            4. Return the overall test result.

        Attributes Used:
            - self.fbCurrentMode (str): Current function block mode under test.
            - self.fbTestImplementation (Enum): Implementation type for the test.
            - self.runningTestSessions (List[Dict]): Active test sessions with session numbers.
            - self.adwInPytefReadNodeErrorListServer (Dict): Mapping of session numbers to error list objects.
            - self.logger (Logger): Logger instance for info/error reporting.
            - self.fbverificationsresults (Dict): Stores verification details for each session.
            - self.remarks (List[List[str]]): Aggregated remarks for reporting.
        """

        createRemarks = []
        testResult = True

        createRemarks.append(f"For Mode: {self.fbCurrentMode.name} and "
                             f"Implementation: {self.fbTestImplementation.name}")

        for activeSession in self.runningTestSessions:
            sessionNumber = activeSession["sessionNumber"]
            result = self.adwInPytefReadNodeErrorListServer[sessionNumber].getValue()

            if result.isOK:
                if not all(result.value):
                    testResult = testResult and True
                    createRemarks.append(f"Server {sessionNumber} returned no error for READ variables - SUCCESSFULL")
                    self.logger.info(f"Server {sessionNumber} returned no error for READ variables - SUCCESSFULL")
                else:
                    testResult = testResult and False
                    createRemarks.append(f"Server {sessionNumber} returned with error id for READ variables - "
                                         f"UNSUCCESSFULL")

                    self.logger.error(f"Server {sessionNumber} returned with error id for READ variables - "
                                      f"UNSUCCESSFULL")

                if str(sessionNumber) not in self.fbverificationsresults:
                    self.fbverificationsresults[str(sessionNumber)] = []

                self.fbverificationsresults[str(sessionNumber)].append(
                    {"test case": "Read variable", "variable": result.value})

        # Create Remark Entry for READ VARIABLES FB Test
        self.remarks.append(createRemarks)

        return testResult

    #-------------------------------------------------------------------------------------------------------------------
    def _verifyWriteVariables(self, isAuthTestRemarks: bool = False) -> bool:
        """
        Verifies that all active sessions successfully write variables without errors.

        This method checks each active test session for errors in writing variables by
        querying `adwInPytefWriteNodeErrorListServer`. If all sessions return no errors,
        the test passes; otherwise, it fails. It also logs the results and stores verification
        details for reporting.

        Workflow:
            1. Initialize remarks and set `testResult` to True.
            2. For each active session:
                - Retrieve the error list for WRITE variables.
                - If all values indicate no error, log success and keep `testResult` True.
                - Otherwise, log failure and set `testResult` to False.
                - Update `fbverificationsresults` with session-specific details.
            3. Append remarks for the WRITE VARIABLES FB Test.
            4. Return the overall test result.

        Attributes Used:
            - self.fbCurrentMode (str): Current function block mode under test.
            - self.fbTestImplementation (Enum): Implementation type for the test.
            - self.runningTestSessions (List[Dict]): Active test sessions with session numbers.
            - self.adwInPytefWriteNodeErrorListServer (Dict): Mapping of session numbers to error list objects.
            - self.logger (Logger): Logger instance for info/error reporting.
            - self.fbverificationsresults (Dict): Stores verification details for each session.
            - self.remarks (List[List[str]]): Aggregated remarks for reporting.
        """

        createRemarks = []
        testResult = True

        createRemarks.append(f"For Mode: {self.fbCurrentMode.name} and "
                             f"Implementation: {self.fbTestImplementation.name}")

        for activeSession in self.runningTestSessions:
            sessionNumber = activeSession["sessionNumber"]
            result = self.adwInPytefWriteNodeErrorListServer[sessionNumber].getValue()

            if result.isOK:
                if not all(result.value):
                    testResult = testResult and True
                    createRemarks.append(f"Server {sessionNumber} returned no error for WRITE variables - "
                                         f"SUCCESSFULL")

                    self.logger.info(f"Server {sessionNumber} returned no error for WRITE variables - SUCCESSFULL")
                else:
                    testResult = testResult and False
                    createRemarks.append(f"Server {sessionNumber} returned with error id for WRITE variables - "
                                         f"UNSUCCESSFULL")

                    self.logger.error(f"Server {sessionNumber} returned with error id for WRITE variables - "
                                      f"UNSUCCESSFULL")

                if str(sessionNumber) not in self.fbverificationsresults:
                    self.fbverificationsresults[str(sessionNumber)] = []

                self.fbverificationsresults[str(sessionNumber)].append(
                    {"test case": "Write variable", "variable": result.value})

        # Create Remark Entry for WRITE VARIABLES FB Test
        if isAuthTestRemarks is not True:
            self.remarks.append(createRemarks)
        else:
            # Create Remark for last list item Entry for WRITE VARIABLES FB Test
            self.remarks[-1] = self.remarks[-1] + createRemarks

        return testResult

    #-------------------------------------------------------------------------------------------------------------------
    def _verifyReadWriteVariables(self, isAuthTestRemarks: bool = False) -> bool:
        """
        Verifies that all active sessions successfully perform WRITE-READ operations without errors.

        This method checks each active test session for errors during combined WRITE-READ operations
        by querying `aiInPytefWriteReadNodeErrorListServer`. If all sessions return no errors, the test
        passes; otherwise, it fails. It also logs the results and stores verification details for reporting.

        Workflow:
            1. Initialize remarks and set `testResult` to True.
            2. For each active session:
                - Retrieve the error list for WRITE-READ operations.
                - If all values indicate no error, log success and keep `testResult` True.
                - Otherwise, log failure and set `testResult` to False.
                - Update `fbverificationsresults` with session-specific details.
            3. Append remarks for the WRITE-READ VARIABLES FB Test.
            4. Return the overall test result.

        Attributes Used:
            - self.fbCurrentMode (str): Current function block mode under test.
            - self.fbTestImplementation (Enum): Implementation type for the test.
            - self.runningTestSessions (List[Dict]): Active test sessions with session numbers.
            - self.aiInPytefWriteReadNodeErrorListServer (Dict): Mapping of session numbers to error list objects.
            - self.logger (Logger): Logger instance for info/error reporting.
            - self.fbverificationsresults (Dict): Stores verification details for each session.
            - self.remarks (List[List[str]]): Aggregated remarks for reporting.

        Returns:
            bool: True if all sessions successfully performed WRITE-READ operations without errors, False otherwise.

        Raises:
            None explicitly, but logs errors for failed sessions.

        Notes:
            - `result.isOK` and `result.value` are expected properties of the error list object.
            - Each session's verification details are stored for later reporting.
        """

        createRemarks = []
        testResult = True

        createRemarks.append(f"For Mode: {self.fbCurrentMode.name} and "
                             f"Implementation: {self.fbTestImplementation.name}")

        for activeSession in self.runningTestSessions:
            sessionNumber = activeSession["sessionNumber"]
            result = self.aiInPytefWriteReadNodeErrorListServer[sessionNumber].getValue()

            if result.isOK:
                if not all(result.value):
                    testResult = testResult and True
                    createRemarks.append(f"Server {sessionNumber} returned no error for WRITE-READ variables - "
                                         f"SUCCESSFULL")

                    self.logger.info(f"Server {sessionNumber} returned no error for WRITE-READ variables - "
                                     f"SUCCESSFULL")
                else:
                    testResult = testResult and False
                    createRemarks.append(f"Server {sessionNumber} returned with error id for WRITE-READ variables - "
                                         f"UNSUCCESSFULL")
                    self.logger.error(f"Server {sessionNumber} returned with error id for WRITE-READ variables - "
                                      f"UNSUCCESSFULL")

                if str(sessionNumber) not in self.fbverificationsresults:
                    self.fbverificationsresults[str(sessionNumber)] = []

                self.fbverificationsresults[str(sessionNumber)].append(
                    {"test case": "Read-Write variable", "variable": result.value})

        # Create Remark Entry for WRITE-READ VARIABLES FB Test
        if isAuthTestRemarks is not True:
            self.remarks.append(createRemarks)
        else:
            # Create Remark for last list item Entry for WRITE-READ VARIABLES FB Test
            self.remarks[-1] = self.remarks[-1] + createRemarks

        return testResult

    #-------------------------------------------------------------------------------------------------------------------
    def _verifyMethodExecution(self) -> bool:
        """
        Verifies that all active sessions successfully execute methods without errors.

        This method checks each active test session for errors during method execution by
        querying `adwInPytefMethodErrorListServer`. If all sessions return no errors, the test
        passes; otherwise, it fails. It also logs the results and stores verification details
        for reporting.

        Workflow:
            1. Initialize remarks and set `testResult` to True.
            2. For each active session:
                - Retrieve the error list for method execution.
                - If all values indicate no error, log success and keep `testResult` True.
                - Otherwise, log failure and set `testResult` to False.
                - Update `fbverificationsresults` with session-specific details.
            3. Append remarks for the Method Execution FB Test.
            4. Return the overall test result.

        Attributes Used:
            - self.fbCurrentMode (str): Current function block mode under test.
            - self.fbTestImplementation (Enum): Implementation type for the test.
            - self.runningTestSessions (List[Dict]): Active test sessions with session numbers.
            - self.adwInPytefMethodErrorListServer (Dict): Mapping of session numbers to error list objects.
            - self.logger (Logger): Logger instance for info/error reporting.
            - self.fbverificationsresults (Dict): Stores verification details for each session.
            - self.remarks (List[List[str]]): Aggregated remarks for reporting.
        """

        createRemarks = []
        testResult = True

        createRemarks.append(f"For Mode: {self.fbCurrentMode.name} and "
                             f"Implementation: {self.fbTestImplementation.name}")

        for activeSession in self.runningTestSessions:
            sessionNumber = activeSession["sessionNumber"]
            result = self.adwInPytefMethodErrorListServer[sessionNumber].getValue()

            if result.isOK:
                if not all(result.value):
                    testResult = testResult and True
                    createRemarks.append(f"Server {sessionNumber} returned no error for Method execution - "
                                         f"SUCCESSFULL")

                    self.logger.info(f"Server {sessionNumber} returned no error for Method execution - SUCCESSFULL")
                else:
                    testResult = testResult and False
                    createRemarks.append(f"Server {sessionNumber} returned with error id for Method execution - "
                                         f"UNSUCCESSFULL")
                    self.logger.error(f"Server {sessionNumber} returned with error id for Method execution - "
                                      f"UNSUCCESSFULL")

                if str(sessionNumber) not in self.fbverificationsresults:
                    self.fbverificationsresults[str(sessionNumber)] = []

                self.fbverificationsresults[str(sessionNumber)].append(
                    {"test case": "Trigger Method", "variable": result.value})

        # Create Remark Entry for Method execution FB Test
        self.remarks.append(createRemarks)

        return testResult

    #-------------------------------------------------------------------------------------------------------------------
    def verifyOpenPlcClientFunctionBlock(self, testType: str) -> []:
        """
        This method verify the Function blocks for the operation types Read, Write,
        Asynchronous Write & Read and Method call

        Args:
            testType: Provide the type of test (INTERNAL/MULTIPLE/EXTERNAL).
        """

        self.logger.newStep("Function Block test result verification Pre-check check started")

        self.logger.info("---------- [Pre-check]: Step1 - Check Step numbers are updating ----------")
        self._validateStepNumbersUpdating()

        self.logger.info("---------- [Pre-check]: Step2 - Check Count cycles are updating ----------")
        self._validateCycleCountUpdating()

        self.logger.info("---------- [Pre-check]: Step3 - Check for Connect DONE status ----------")
        self._validateConnectStatus()

        self.logger.newStep("Function Block test result verification Pre-check check completed")

        self.logger.newStep("Function Block test result Verification started")

        waitIndex = 1
        waitLoop = constants.SESSION_WAIT[testType]

        while waitIndex <= waitLoop:
            time.sleep(60)
            self.logger.newStep(f"Function Block test result verification Verification status after {waitIndex} minute")

            self.remarks = []

            self.logger.info("------ [Verification]: Step1 - Check for failed step for every connected session ------")
            self._verifyFailedStepAfterConnect()

            self.logger.info("------ [Verification]: Step2 - Check for error id for failed Step "
                             "for every connected session ------")
            returnResult = self._checkFailedStepErrorId()

            if not all(returnResult):
                return returnResult

            self.remarks = []
            returnResult = []
            self.fbverificationsresults = {}

            self.logger.info("---------- [Verification]: Step3 - Check for error id while reading the values "
                             "from variables for every connected session ----------")
            returnResult.append(self._verifyReadVariables())

            self.logger.info("---------- [Verification]: Step4 - Check for error id while writing the values to "
                             "variables for every connected session ----------")
            returnResult.append(self._verifyWriteVariables())

            self.logger.info("---------- [Verification]: Step5 - Check for error id while writing & reading the "
                             "values to & from variables for every connected session ----------")
            returnResult.append(self._verifyReadWriteVariables())

            if self.fbTestImplementation == constants.FBImplementation.VARIABLE_RW_METHOD_CONNECT:
                returnResult.append(self._verifyMethodExecution())

            self.createTabularData()

            if all(returnResult) is False:
                return returnResult

            waitIndex += 1

        self.logger.newStep("Function Block test result Verification completed")

        return returnResult

    #-------------------------------------------------------------------------------------------------------------------
    def _initiateSymbolicVariables(self):
        """
        Initialize per-session PLC Open Client/Server symbolic variables by resolving memory objects.

        This method iterates over all session numbers returned by `self.__getSessionNumbers()`
        and populates a set of dictionaries/arrays on `self` with memory objects retrieved via
        `self.__getMemoryObject(...)`. Each memory object is addressed by a symbol name derived
        from `constants` and typed using the appropriate data type (e.g., `VisibleString`,
        `Boolean`, `Signed16`, `Unsigned32`, `ByteArray`, `Signed32`). After the per-session
        initialization, it also initializes the global `iOutPytefMode`.

        For each `sessionNo`, the following symbols and types are resolved:

            Server/connect & status:
                - `self.sOutOpcUaMethodCallUrl_Server[sessionNo]`:
                    symbol = `constants.PLC_OPEN_CLIENT_SERVER_URL_SYMBOL_NAME.format(sessionNo)`,
                    type = `VisibleString()`
                - `self.xOutPytefExecuteServer[sessionNo]`:
                    symbol = `constants.PLC_OPEN_CLIENT_EXECUTE_CONNECT_SYMBOL_NAME.format(sessionNo)`,
                    type = `Boolean`
                - `self.iAuth_ImplimentationServer[sessionNo]`:
                    symbol = `constants.PLC_OPEN_CLIENT_IMPLEMENTATION_SYMBOL_NAME.format(sessionNo)`,
                    type = `Signed16`
                - `self.iInPytefStepNoServer[sessionNo]`:
                    symbol = `constants.PLC_OPEN_CLIENT_CONNECT_STEPNO_SYMBOL_NAME.format(sessionNo)`,
                    type = `Signed16`
                - `self.dwErrorId_StepServer[sessionNo]`:
                    symbol = `constants.PLC_OPEN_CLIENT_CONNECT_STEPFAILED_SYMBOL_NAME.format(sessionNo)`,
                    type = `Signed16`
                - `self.dwErrorIdServer[sessionNo]`:
                    symbol = `constants.PLC_OPEN_CLIENT_CONNECT_STEPERRORID_SYMBOL_NAME.format(sessionNo)`,
                    type = `Unsigned32`
                - `self.xInPytefConnectDoneServer[sessionNo]`:
                    symbol = `constants.PLC_OPEN_CLIENT_CONNECT_CONNECTDONE_SYMBOL_NAME.format(sessionNo)`,
                    type = `Boolean`
                - `self.adwInPytefWriteNodeErrorListServer[sessionNo]`:
                    symbol = `constants.PLC_OPEN_CLIENT_CONNECT_WRITE_ERRORLIST_SYMBOL_NAME.format(sessionNo)`,
                    type = `ByteArray`
                - `self.adwInPytefReadNodeErrorListServer[sessionNo]`:
                    symbol = `constants.PLC_OPEN_CLIENT_CONNECT_READ_ERRORLIST_SYMBOL_NAME.format(sessionNo)`,
                    type = `ByteArray`
                - `self.aiInPytefWriteReadNodeErrorListServer[sessionNo]`:
                    symbol = `constants.PLC_OPEN_CLIENT_CONNECT_WRITEREAD_ERRORLIST_SYMBOL_NAME.format(sessionNo)`,
                    type = `ByteArray`
                - `self.adwInPytefMethodErrorListServer[sessionNo]`:
                    symbol = `constants.PLC_OPEN_CLIENT_CONNECT_METHOD_ERRORLIST_SYMBOL_NAME.format(sessionNo)`,
                    type = `ByteArray`
                - `self.diInPytefCountCyclesServer[sessionNo]`:
                    symbol = `constants.PLC_OPEN_CLIENT_CONNECT_COUNTCYCLES_SYMBOL_NAME.format(sessionNo)`,
                    type = `Signed32`

            Authentication (User Identity Token):
                - `self.iAuthUserIdentityTokenType[sessionNo]`:
                    symbol = `constants.PLC_OPEN_CLIENT_CONNECT_TOKEN_TYPE_SERVER.format(sessionNo)`,
                    type = `Signed16`
                - `self.sUserIdentityTokenParamUser[sessionNo]`:
                    symbol = `constants.PLC_OPEN_CLIENT_CONNECT_TOKEN_PRAM_USERNAME_SERVER.format(sessionNo)`,
                    type = `VisibleString()`
                - `self.sUserIdentityTokenParamPassword[sessionNo]`:
                    symbol = `constants.PLC_OPEN_CLIENT_CONNECT_TOKEN_PRAM_PASSWORD_SERVER.format(sessionNo)`,
                    type = `VisibleString()
        """

        # -----------------------------------------------------------------------------
        # Read per-session OPC UA / Pytef parameters from PLC memory into dictionaries.
        # For each session number returned by __getSessionNumbers():
        #   - We build the symbol name using sessionNo and constants.*
        #   - We read the PLC variable via __getMemoryObject with the expected data type.
        #   - We store the value in a per-session dictionary keyed by sessionNo.
        #
        # Key groups:
        #   Connectivity/control:
        #     sOutOpcUaMethodCallUrl_Server        -> Server URL or endpoint for OPC UA method calls (VisibleString)
        #     xOutPytefExecuteServer               -> Command/flag to trigger a connect/execute operation (Boolean)
        #     iInPytefStepNoServer                 -> Current step number within connection/operation (Signed16)
        #     xInPytefConnectDoneServer            -> Connect/operation completion flag (Boolean)
        #     diInPytefCountCyclesServer           -> Cycle/count metric for diagnostics (Signed32)
        #
        #   Authentication/user identity:
        #     iAuth_ImplimentationServer           -> Auth implementation/mode selector (Signed16)
        #     iAuthUserIdentityTokenType           -> OPC UA user token type (e.g., Anonymous/UserName/Certificate)
        #                                             (Signed16)
        #     sUserIdentityTokenParamUser          -> Username for UserName token type (VisibleString)
        #     sUserIdentityTokenParamPassword      -> Password for UserName token type (VisibleString)
        #
        #   Errors/diagnostics:
        #     dwErrorId_StepServer                 -> Error flag/ID indicating step failure (Signed16)
        #     dwErrorIdServer                      -> Detailed error code for the last error (Unsigned32)
        #     adwInPytefWriteNodeErrorListServer   -> Error list for write-node operations (ByteArray)
        #     adwInPytefReadNodeErrorListServer    -> Error list for read-node operations (ByteArray)
        #     aiInPytefWriteReadNodeErrorListServer-> Combined write+read error list (ByteArray)
        #     adwInPytefMethodErrorListServer      -> Error list for method invocations (ByteArray)
        #
        # Global:
        #   iOutPytefMode                          -> Pytef client mode (Signed16), stores any one of the following
        #                                             BROWSE, TRANSLATE PATH, FIXED NODE, B+T PASSING, B+T+F PASSING
        # -----------------------------------------------------------------------------

        for sessionNo in self.__getSessionNumbers():
            self.sOutOpcUaMethodCallUrl_Server[sessionNo] = self.__getMemoryObject(
                symbolName = constants.PLC_OPEN_CLIENT_SERVER_URL_SYMBOL_NAME.format(sessionNo),
                dataType = VisibleString())

            self.xOutPytefExecuteServer[sessionNo] = self.__getMemoryObject(
                symbolName = constants.PLC_OPEN_CLIENT_EXECUTE_CONNECT_SYMBOL_NAME.format(sessionNo),
                dataType = Boolean)

            self.iAuth_ImplimentationServer[sessionNo] = self.__getMemoryObject(
                symbolName = constants.PLC_OPEN_CLIENT_IMPLEMENTATION_SYMBOL_NAME.format(sessionNo),
                dataType = Signed16)

            self.iInPytefStepNoServer[sessionNo] = self.__getMemoryObject(
                symbolName = constants.PLC_OPEN_CLIENT_CONNECT_STEPNO_SYMBOL_NAME.format(sessionNo),
                dataType = Signed16)

            self.dwErrorId_StepServer[sessionNo] = self.__getMemoryObject(
                symbolName = constants.PLC_OPEN_CLIENT_CONNECT_STEPFAILED_SYMBOL_NAME.format(sessionNo),
                dataType = Signed16)

            self.dwErrorIdServer[sessionNo] = self.__getMemoryObject(
                symbolName = constants.PLC_OPEN_CLIENT_CONNECT_STEPERRORID_SYMBOL_NAME.format(sessionNo),
                dataType = Unsigned32)

            self.xInPytefConnectDoneServer[sessionNo] = self.__getMemoryObject(
                symbolName = constants.PLC_OPEN_CLIENT_CONNECT_CONNECTDONE_SYMBOL_NAME.format(sessionNo),
                dataType = Boolean)

            self.adwInPytefWriteNodeErrorListServer[sessionNo] = self.__getMemoryObject(
                symbolName = constants.PLC_OPEN_CLIENT_CONNECT_WRITE_ERRORLIST_SYMBOL_NAME.format(sessionNo),
                dataType = ByteArray)

            self.adwInPytefReadNodeErrorListServer[sessionNo] = self.__getMemoryObject(
                symbolName = constants.PLC_OPEN_CLIENT_CONNECT_READ_ERRORLIST_SYMBOL_NAME.format(sessionNo),
                dataType = ByteArray)

            self.aiInPytefWriteReadNodeErrorListServer[sessionNo] = self.__getMemoryObject(
                symbolName = constants.PLC_OPEN_CLIENT_CONNECT_WRITEREAD_ERRORLIST_SYMBOL_NAME.format(sessionNo),
                dataType = ByteArray)

            self.adwInPytefMethodErrorListServer[sessionNo] = self.__getMemoryObject(
                symbolName = constants.PLC_OPEN_CLIENT_CONNECT_METHOD_ERRORLIST_SYMBOL_NAME.format(sessionNo),
                dataType = ByteArray)

            self.diInPytefCountCyclesServer[sessionNo] = self.__getMemoryObject(
                symbolName = constants.PLC_OPEN_CLIENT_CONNECT_COUNTCYCLES_SYMBOL_NAME.format(sessionNo),
                dataType = Signed32)

            self.iAuthUserIdentityTokenType[sessionNo] = self.__getMemoryObject(
                symbolName = constants.PLC_OPEN_CLIENT_CONNECT_TOKEN_TYPE_SERVER.format(sessionNo),
                dataType = Signed16)

            self.sUserIdentityTokenParamUser[sessionNo] = self.__getMemoryObject(
                symbolName = constants.PLC_OPEN_CLIENT_CONNECT_TOKEN_PRAM_USERNAME_SERVER.format(sessionNo),
                dataType = VisibleString())

            self.sUserIdentityTokenParamPassword[sessionNo] = self.__getMemoryObject(
                symbolName = constants.PLC_OPEN_CLIENT_CONNECT_TOKEN_PRAM_PASSWORD_SERVER.format(sessionNo),
                dataType = VisibleString())

        self.iOutPytefMode = self.__getMemoryObject(symbolName = constants.PLC_OPEN_CLIENT_MODE_SYMBOL_NAME,
                                                    dataType = Signed16)

    #-------------------------------------------------------------------------------------------------------------------
    def createTabularData(self) -> None:
        """
        This method is used to display the data in tabular format
        """

        headers = ["Session", "Test Case"] + [f"Var{i}" for i in range(1, 51)]

        format_str = " ".join(["| {:<25} "] * len(headers))

        self.logger.newStep("Perform data analysis for the FB Scenarios to verify for any error - Started")
        self.logger.info("-" * len(headers) * 30)
        self.logger.info(format_str.format(*headers))
        self.logger.info("-" * len(headers) * 30)

        for session, tests in self.fbverificationsresults.items():
            for test in tests:
                row = ["Session" + session, test["test case"]] + [test["variable"][i]
                                                                  for i in range(len(test["variable"]))]
                format_row = " ".join(["| {:<25} "] * len(row))

                self.logger.info(format_row.format(*row))
                self.logger.info("-" * len(headers) * 30)

        self.logger.newStep("Perform data analysis for the FB Scenarios to verify for any error - Completed")

    #-------------------------------------------------------------------------------------------------------------------
    @autobehavior
    def setUpClass(self, behavior: tyOptBehavior = None, **kwargs) -> Result:
        """
        Method to setup the library content (allocated resources).

        The method can be called form the <testcase>.setUpClass() to setup all allocated resources.

        :param behavior:  Auto behavior of this method.
        :returns: Result
        """

        self.resetPreviousTestReportResult()
        return Result(errorCode = Result.NO_ERROR, errorMessage = "Success")

    #-------------------------------------------------------------------------------------------------------------------
    @autobehavior
    def tearDownClass(self, behavior: tyOptBehavior = None, **kwargs) -> Result:
        """
        Method to cleanup the library content (used resources).

        The method can be called form the <testcase>.tearDownClass() to cleanup all used resources.

        :param behavior:  Auto behavior of this method.
        :returns: Result
        """

        self.executeSessions(False)
        self.restartControllers()
        self.disConnect()
        return Result(errorCode = Result.NO_ERROR, errorMessage = "Success")
