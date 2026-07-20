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
import re
import os
import time
from itertools import zip_longest
from typing import Callable, List, Self, Tuple
from pytef.namespace.testlib import (Version, Result, autobehavior, tyOptBehavior)

from tests.testlib.utils.CommonLib import clsLogger, deleteUserManagementFiles
from tests.testlib.lib_pywinauto.plcd.PLC import PLC
from tests.opc_ua.plc_fb_test.lib.Lib_Base import Lib_Base
from tests.opc_ua.plc_fb_test.utils.excelReader import ConfigExlParserOpenClientAuthToken
from tests.opc_ua.plc_fb_test.utils.excelReportUpdater import ReportExlParser as ReportExlParserClientAuthToken
from tests.opc_ua.plc_fb_test.utils import constants_plc_fb as constants
from tests.opc_ua.plc_fb_test.utils.constants_plc_fb import FBTokenType
#-----------------------------------------------------------------------------------------------------------------------
# SVN keyword section
#-----------------------------------------------------------------------------------------------------------------------
FILE_URL = "$HeadURL: $"[10:-2]  # noqa:E501
FILE_REV = "$Revision: $"[11:-2]
FILE_DATE = "$LastChangedDate: $"[18:-2]
FILE_AUTHOR = "$LastChangedBy: $"[16:-2]

#-----------------------------------------------------------------------------------------------------------------------
# PyTeF file header end
#-----------------------------------------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------------------------------------
def logTestDetails() -> Callable:
    """
    Decorator to log test details and save test results for a given test case.

    Args:
        jiraIndex (int): The index of the test case in Jira.

    Returns:
        function: A decorator that wraps the test function to log and save its results.

    The decorator performs the following actions:
    1. Logs the test description at the start of the test.
    2. Executes the test function.
    3. Logs the test description with the result at the end of the test.
    4. Saves the test result.

    Example:
        @logTestDetails(testIndexList = [1,2,3])
        def test_example(self):
            # Test implementation
            pass
    """
    #-------------------------------------------------------------------------------------------------------------------
    def decorator(func : Callable) -> Callable:
        # flake8: noqa: ANN001
        def wrapper(self: Self, *args, **kwargs) -> List[bool]:
            self.logTestDescription(result = [])

            testResults, testRemarks = func(self, *args, **kwargs)

            self.saveTestResult(results = testResults, remarks = testRemarks)
            self.logTestDescription(result = testResults, isEnd = True)

            return testResults
        return wrapper
    return decorator

#-----------------------------------------------------------------------------------------------------------------------
class Lib_PLC_Open_Client_Auth_Tokens(Lib_Base):
    """
        OPC UA PLC Open Client Authorization Tokens
    """
    prefixCls = 'Lib_PLC_Open_Client_Auth_Tokens'
    __LIB_DICT = {}

    LIB_NAME = "Lib_PLC_Open_Client_Auth_Tokens"
    LIB_VERSION = Version(1, 0, 0)
    PLC_OBJ = None

    #-------------------------------------------------------------------------------------------------------------------
    def __init__(self, fbTestModeList, fbTestImpementation) -> None:
        """
        Constructor
        """

        self.logger.info(f"[{type(self).prefixCls}] in Lib_PLC_Open_Client_Auth_Tokens::__init__()")
        self.xlsReaderObj = ConfigExlParserOpenClientAuthToken(configFile = constants.CONFIG_FILE_FB_AUTH_TOKENS_PATH,
                                                               logger = self.logger)

        self.reportUpdaterObj = ReportExlParserClientAuthToken(reportFile = constants.REPORT_FILE_FB_AUTH_TOKENS_PATH,
                                                             sheetName = constants.REPORT_SHEET_FB_AUTH_TOKENS_NAME,
                                                             logger = self.logger)

        super().__init__(xlsReaderObj = self.xlsReaderObj, reportUpdaterObj = self.reportUpdaterObj,
                         fbTestModeList = fbTestModeList, fbTestImpementation = fbTestImpementation)

    #-------------------------------------------------------------------------------------------------------------------
    @classmethod
    def createTests(cls, testcls: str) -> None:
        """
        Auto create tests at runtime.

        Let the base class do the job
        """

        logger = clsLogger()
        xlsReaderObj = ConfigExlParserOpenClientAuthToken(configFile = constants.CONFIG_FILE_FB_AUTH_TOKENS_PATH,
                                                          logger = logger)

        tests = [tcName for tcName in dir(testcls) if 'tc_' in tcName]

        for testMethodName in tests:
            tcParam = {}
            tcParam['funcName'] = testMethodName

            try:
                _regextcmatch = re.match("tc_(.*)", testMethodName)
                testName = _regextcmatch.group(1)
                grpName = testName.split("_")[0]

                tcName = next(iter(xlsReaderObj.testCaseSelectionDict.get(grpName)))
                executeFlag = xlsReaderObj.testCaseSelectionDict.get(grpName).get(tcName).get("execute")

                if executeFlag:
                    jiraIdList = xlsReaderObj.getJiraIdListByGroup(testGroupName = grpName)
                    tcParam['@spiratest_tcIdList'] = [(None, jiraIdList)]
                    testCaseName = f"test_plc_ext_feat_{testName}"

                    testcls.addTestCase(name = testCaseName,
                                        func = getattr(testcls, testMethodName),
                                        tcParam = tcParam)
                else:
                    logger.info(f"[{cls.prefixCls}] Test group {testMethodName} not selected for test")
            except Exception:  # pylint: disable=broad-exception-caught

                logger.exception(f"[{cls.prefixCls}] Test case {testMethodName} is not selected for execution...")

    #-------------------------------------------------------------------------------------------------------------------
    def deactivateUserManagement(self):

        """
        Deactivate user management on all IPC controllers managed by this instance.

        This method iterates over `self.ipcObjs` and performs the following steps
        for each device (IPC controller):
          1. Deletes user management files from the controller.
          2. Reboots the controller to ensure the changes take effect.
          3. Fails the current test case if the reboot does not succeed.

        The method expects the following attributes and external functions to be available:
          - `self.ipcObjs` (Iterable): A collection of IPC device objects. Each object must
            expose `channelList` where the first element contains an `address` attribute.
          - `self.logger` (Logger-like): Provides a `newStep(str)` method used to log test steps.
          - `self.rebootController(device)` (Callable): Reboots the given IPC device and returns
            `True` on success, `False` otherwise.
          - `self.testCase.fail(str)` (Callable): Marks the test case as failed with the given message.
          - `deleteUserManagementFiles(logger, ipAddress)` (Callable): Deletes user management files
            from the controller at the given IP address.
        """

        for ipcObj in self.ipcObjs:
            currIpAddr = ipcObj.channelList[0].address

            # Deleting user management files from the controller
            self.logger.newStep("Step 1: Deleting user management files from controller if any")
            deleteUserManagementFiles(logger = self.logger,
                                      ipAddress = currIpAddr)

            self.logger.newStep("Step 2: Rebooting controller")
            if not self.rebootController(device = ipcObj):
                self.testCase.fail("Failed to reboot controller after deleting user management")

    #-------------------------------------------------------------------------------------------------------------------
    def __moveCertificateInPLCD(self):
        """
        Move the controller's certificate from **Quarantined** to **Trusted** in the PLCD tool.

        This method:
          1. Selects the first controller (by IP) in `self.ipcObjs` within the PLCD project.
          2. Brings the PLCD session online (without downloading).
          3. Performs a drag-and-drop move of the controller certificate from the
             **Quarantined** folder to the **Trusted** folder in PLCD.
          4. Takes the PLCD session offline.

        The controller type and project name are derived from the first `ipcObj` using
        `self.findCtrlType(...)` and `constants.PLC_PROJ_NAME.format(controllerType)`.
        """

        currControllerType = self.findCtrlType(next(iter(self.ipcObjs)))
        currIpAddr = next(iter(self.ipcObjs)).channelList[0].address

        # Selecting the required controller from the gateway
        self.logger.newStep("Step 1: Selecting required controller")
        if not Lib_PLC_Open_Client_Auth_Tokens.PLC_OBJ.selectController(ipAddress = currIpAddr,
                                       projName = constants.PLC_PROJ_NAME.format(currControllerType)):
            self.testCase.skip(f"Failed to select required controller with IP address : {currIpAddr}")

        # Downloading application to the controller
        self.logger.newStep("Step 2:  Controller Going Online")
        if not Lib_PLC_Open_Client_Auth_Tokens.PLC_OBJ.goOnline(download = False):
            self.testCase.skip("Failed to Go online in plcd project")

        self.logger.newStep("Step 3: Drag and Drop Controller Certificate from Quarantined to Trusted Certificate")
        Lib_PLC_Open_Client_Auth_Tokens.plcObj.moveCertificateFromOneFolderToAnotherInPLCD(
            projName = constants.PLC_PROJ_NAME.format(currControllerType),
            moveCertificateFrom = constants.TYPE_OF_CERTIFICATES[1],
            moveCertificateTo = constants.TYPE_OF_CERTIFICATES[0],
            nameOfCertificate = '')

        self.logger.newStep("Step 4: Controller Going Offline")
        if not Lib_PLC_Open_Client_Auth_Tokens.PLC_OBJ.goOffline(
            projName = constants.PLC_PROJ_NAME.format(currControllerType),
            header = constants.PLC_HEADER):
            self.testCase.skip("Failed to Go offline in plcd project")

    #-------------------------------------------------------------------------------------------------------------------
    def configureWithPLCD(self):
        """
        Configure one or more controllers using the PLCD tool and an OPC UA PLCopen FB project.

        Workflow Overview:
            0. Start the PLCD tool (using the PLC version from `self.xlsReaderObj`).
            1. Open the PLCopen FB project corresponding to each controller type.
            2. Clean All.
            3. Build the project.
            4. Expand project devices.
            5. Select the target controller by IP from the gateway.
            6. Update communication/encryption policy to "optional encryption".
            7. Activate user management and add the admin user.
            8. Go online (download the application) with certificate installation.
            9. (Host controller only) Delete certificates from Trusted and Quarantine.
           10. Create a boot project.
           11. Go offline.
           12. Reboot the controller.
           13. (Server controllers) Save and close the project.

        Behavior:
            - Calls :`deactivateUserManagement` up front to remove any existing user
              management on all IPCs.
            - Initializes a global PLCD session `Lib_PLC_Open_Client_Auth_Tokens.PLC_OBJ`.
            - Iterates over `self.ipcObjs` in reverse, but treats the *first* element of the
              original list (`next(iter(self.ipcObjs))`) as the **client** and all others as
              **server** when resolving project paths.
            - Uses `self.findCtrlType(ipcObj)` to determine the controller type used to format
              project names/paths.

        """

        self.deactivateUserManagement()

        # Creating PLCD object
        Lib_PLC_Open_Client_Auth_Tokens.PLC_OBJ = PLC(logger = self.logger)

        # Starting the PLCD tool
        self.logger.newStep("Step 0: Starting the PLCD tool")
        if not Lib_PLC_Open_Client_Auth_Tokens.PLC_OBJ.openPLC(version = self.xlsReaderObj.plcVersion):
            self.testCase.skip("Failed to start PLC tool")

        for ipcObj in self.ipcObjs[::-1]:
            currControllerType = self.findCtrlType(ipcObj)
            currIpAddr = ipcObj.channelList[0].address

            if next(iter(self.ipcObjs)) == ipcObj:
                relBootProjectPath = os.getcwd() + constants.PLC_PROJ_PATH.format("client", currControllerType)

            else:
                relBootProjectPath = os.getcwd() + constants.PLC_PROJ_PATH.format("server", currControllerType)

            # Opening OPC UA PLC Open FB project in it
            self.logger.newStep("Step 1: Open OPC UA PLC Open FB project")
            if not Lib_PLC_Open_Client_Auth_Tokens.PLC_OBJ.openProjAndHandleEnvWin(projPath = relBootProjectPath,
                                                       projName = constants.PLC_PROJ_NAME.format(currControllerType)):
                self.testCase.skip("Failed to open OPC UA PLC Open FB project")

            # Performing 'Clean all' operation on the project
            self.logger.newStep("Step 2: Performing Clean All")
            if not Lib_PLC_Open_Client_Auth_Tokens.PLC_OBJ.cleanAllBuild(
                projName = constants.PLC_PROJ_NAME.format(currControllerType)):
                self.testCase.skip("Failed to perform clean all operation")

            # Performing 'Build' operation on the project
            self.logger.newStep("Step 3: Building the project")
            if not Lib_PLC_Open_Client_Auth_Tokens.PLC_OBJ.buildProject(
                projName = constants.PLC_PROJ_NAME.format(currControllerType)):
                self.testCase.skip("Failed to build the project", self.controllerIP)

            # Going offline with the controller
            self.logger.newStep("Step 4: Expanding project devices")
            if not Lib_PLC_Open_Client_Auth_Tokens.PLC_OBJ.expandPLCDProjectDevices(
                projName = constants.PLC_PROJ_NAME.format(currControllerType)):
                self.testCase.skip("Failed to expand PLC project devices")

            # Selecting the required controller from the gateway
            self.logger.newStep("Step 5: Selecting required controller")
            if not Lib_PLC_Open_Client_Auth_Tokens.PLC_OBJ.selectController(ipAddress = currIpAddr,
                                           projName = constants.PLC_PROJ_NAME.format(currControllerType)):
                self.testCase.skip(f"Failed to select required controller with IP address : {currIpAddr}")

            # Updating encryption policy
            self.logger.newStep("Step 6: Updating Encryption Policy")
            if not Lib_PLC_Open_Client_Auth_Tokens.PLC_OBJ.changeCommPolicy(
                projName = constants.PLC_PROJ_NAME.format(currControllerType),
                policyName = constants.PolicyNames.OPTIONAL_ENCRYPTION.value):
                self.testCase.skip("Failed to update encryption policy")

            if next(iter(self.ipcObjs)) is not ipcObj:
                self.logger.newStep("Step 7: Activate user management and add user")
                if not Lib_PLC_Open_Client_Auth_Tokens.PLC_OBJ.activateUsrMgmtAndAddAdminUsr(
                    projName = constants.PLC_PROJ_NAME.format(currControllerType),
                    adminData = constants.USERS_DETAILS_DICT["administratorUser"]):
                    self.testCase.skip("Failed to activate user management and add user")

            # Downloading application to the controller
            self.logger.newStep("Step 8: Downloading application to the controller")
            if not Lib_PLC_Open_Client_Auth_Tokens.PLC_OBJ.goOnline():
                self.testCase.skip("Failed to download application to the controller")

            if next(iter(self.ipcObjs)) is ipcObj:
                self.logger.newStep("Step 9: Delete certificates from Trusted and Quarantine")
                if not Lib_PLC_Open_Client_Auth_Tokens.PLC_OBJ.deleteCertificatesFromPLCSecurity(
                    projName = constants.PLC_PROJ_NAME.format(currControllerType),
                    listOfTypeOfCertificates = constants.TYPE_OF_CERTIFICATES):
                    self.testCase.skip("Failed to delete certificates from Trusted and Quarantine")

            self.logger.newStep("Step 10: Create boot project")
            if not Lib_PLC_Open_Client_Auth_Tokens.PLC_OBJ.createBootProject(
                projName = constants.PLC_PROJ_NAME.format(currControllerType)):
                self.testCase.skip("Failed to create boot project")

            self.logger.newStep("Step 11: Controller Going Offline")
            if not Lib_PLC_Open_Client_Auth_Tokens.PLC_OBJ.goOffline(
                projName = constants.PLC_PROJ_NAME.format(currControllerType),
                header = constants.PLC_HEADER):
                self.testCase.skip("Failed to Go offline in plcd project ")

            # Rebooting the controller
            self.logger.newStep("Step 12: Rebooting controller")
            if not self.rebootController(device = ipcObj):
                self.testCase.fail("Failed to reboot controller after creating boot project")

            Lib_PLC_Open_Client_Auth_Tokens.PLC_OBJ.handlePLCConnectionLost(header = constants.PLC_HEADER)

            if next(iter(self.ipcObjs)) is not ipcObj:
                self.logger.info("Step 13: Saving & Closing Project")
                if not Lib_PLC_Open_Client_Auth_Tokens.PLC_OBJ.closeAndSaveProject(
                    projName = constants.PLC_PROJ_NAME.format(currControllerType),
                    header = constants.PLC_HEADER):
                    self.testCase.skip("Failed to save and close Project")

    #-------------------------------------------------------------------------------------------------------------------
    def __checkFailedStepAuthTokenErrorId(self) -> bool:
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

        createRemarks.append(f"Connect Status For Mode: {self.fbCurrentMode.name} and "
                             f"Implementation: {self.fbTestImplementation.name}")

        for activeSession in self.runningTestSessions:
            sessionNumber = activeSession["sessionNumber"]
            result = self.dwErrorId_StepServer[sessionNumber].getValue()

            if result.isOK:
                if not result.value == 0:
                    testResult = testResult and False
                    createRemarks.append(f"Server {sessionNumber} returned error id {result} - FAILED")
                    self.logger.error(f"Server {sessionNumber} returned error id {result} - FAILED")
                else:
                    testResult = testResult and True
                    createRemarks.append(f"Server {sessionNumber} returned with no error id  - SUCCESSFULL")
                    self.logger.info(f"Server {sessionNumber} returned with no error id SUCCESSFULL")

        # Create Remark Entry and Result for CONNECT STATUS for FB Test
        self.remarks.append(createRemarks)
        return testResult

    #-------------------------------------------------------------------------------------------------------------------
    def _executeAuthGrp(self, testType: str, authType: FBTokenType) -> Tuple[List[bool], List[List[str]]]:
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

        self.setParameterUsers(authType = authType)

        for fbCurrentMode in self.fbTestModeList:
            self.fbCurrentMode = fbCurrentMode

            # Disable the sessions
            self.executeSessions(False)
            self.restartControllers()

            self.mapSessionIPAddresses(testType = testType)
            self.setSessionURLs(isSessionURLEmpty = True)
            self.setSessionURLs()

            self.setTokenType(tokenType = authType)
            self.setUserIdentityTokenCredentials(tokenType = authType)

            self.setMode()
            self.setImplementations()

            # Enable the sessions
            self.executeSessions(executeValue = True)
            result = self.__verifyOpenPlcClientAuthTokenFunctionBlock(testType = testType)

            returnResult = [currResult and previousResult
                            for currResult, previousResult in zip_longest(returnResult, result, fillvalue = True)]

            returnRemarks = [currRemarks + previousRemarks
                             for currRemarks, previousRemarks in zip_longest(returnRemarks,
                                                                             self.remarks, fillvalue = [])]

        return returnResult, returnRemarks

    #-------------------------------------------------------------------------------------------------------------------
    def __verifyOpenPlcClientAuthTokenFunctionBlock(self, testType: str) -> []:
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
            returnResult = []
            self.fbverificationsresults = {}

            self.logger.info("------ [Verification]: Step1 - Check for failed step for every connected session ------")

            if not self._verifyFailedStepAfterConnect():
                # This check is for Auth Token Type 100 where Certificate Generation needs to be syncronized
                # This failure indicates certificate needs to be copied from Quarantine to Trusted
                self.remarks = []
                self.__moveCertificateInPLCD()
                self._verifyFailedStepAfterConnect()

            self.logger.info("------ [Verification]: Step2 - Check for error id for failed Step "
                             "for every connected session ------")
            self.remarks = []
            returnResult.append(self.__checkFailedStepAuthTokenErrorId())

            self.logger.info("---------- [Verification]: Step3 - Check for error id while reading the values "
                             "from variables for every connected session ----------")
            testResult = self._verifyReadVariables()

            self.logger.info("---------- [Verification]: Step4 - Check for error id while writing the values to "
                             "variables for every connected session ----------")
            testResult = testResult and self._verifyWriteVariables(isAuthTestRemarks = True)

            self.logger.info("---------- [Verification]: Step5 - Check for error id while writing & reading the "
                             "values to & from variables for every connected session ----------")
            testResult = testResult and self._verifyReadWriteVariables(isAuthTestRemarks = True)
            returnResult.append(testResult)

            self.logger.info("---------- [Verification]: Step6 - Check for error id while executing the method "
                             "for every connected session ----------")
            returnResult.append(self._verifyMethodExecution())

            self.createTabularData()

            if all(returnResult) is False:
                return returnResult

            waitIndex += 1

        self.logger.newStep("Function Block test result Verification completed")

        return returnResult

    #-------------------------------------------------------------------------------------------------------------------
    @autobehavior
    def setUpClass(self, behavior: tyOptBehavior = None, **kwargs) -> Result:
        """
        Method to setup the library content (allocated resources).

        The method can be called form the <testcase>.setUpClass() to setup all allocated resources.

        :param behavior:  Auto behavior of this method.
        :returns: Result
        """

        super().setUpClass(behavior = behavior)
        self.configureWithPLCD()

        self.logger.info("Update controller time stamp by 5 minutes")
        self.update_host_controller_time(updateTimeInSeconds = 200)

        self.reportUpdaterObj.updateReportHeader(
            header = constants.REPORT_FB_AUTH_TOKENS_HEADER.format(self.findCtrlType(self.ipcHostController),
                                                                   self.xlsReaderObj.releaseName))

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

        currControllerType = self.findCtrlType(next(iter(self.ipcObjs)))
        self.update_host_controller_time(updateTimeInSeconds = 0)

        if not Lib_PLC_Open_Client_Auth_Tokens.PLC_OBJ.closePLC(
            projName = constants.PLC_PROJ_NAME.format(currControllerType),
            header = constants.PLC_HEADER, saveFlag = False):
            self.logger.warn("Failed to close PLC Designer tool")

        super().tearDownClass(behavior = behavior)
        return Result(errorCode = Result.NO_ERROR, errorMessage = "Success")

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def executeGroup1(self):
        """
        TC01: Verify connection to Ext OPC-UA servers c5xx/c4xx with UAUITT_Anonymous(0) using Security Policy
        "SignEncrypt" with user Auth active
        Execute Test case 01 from Group 01

        TC02: Verify Read/Write data to Ext OPC-UA servers c5xx/c4xx with UAUITT_Anonymous(0) using Security Policy
        "SignEncrypt" with user Auth active with "Fixed Node" &
        "Node Info get from UA Browse and UA TranslatePathList FB"
        Execute Test case 02 from Group 01

        TC03: Verify Read/Write data & MethodCall to Ext OPC-UA servers c5xx/c4xx with UAUITT_Anonymous(0) using
        Security Policy "SignEncrypt" with user Auth active with "Fixed Node" &
        "Node Info get from UA Browse and UA TranslatePathList FB"
        Execute Test case 03 from Group 01
        """


        testResult, testRemarks = self._executeAuthGrp(testType = constants.TestType.MULTIPLE.value,
                                                        authType = FBTokenType.ANONYMOUS)
        return testResult, testRemarks

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def executeGroup2(self):
        """
        TC04: Verify connection to Ext OPC-UA servers c5xx/c4xx with UAUITT_Username(1) using Security Policy
        "SignEncrypt" with user Auth active
        Execute Test case 01 from Group 02

        TC05: Verify Read/Write Data to Ext OPC-UA servers c5xx/c4xx with  UAUITT_Username(1) using Security Policy
        "SignEncrypt" with user Auth active with "Fixed Node" and "Node Info get from UA Browse
        Execute Test case 02 from Group 02

        TC06: Verify Read/Write Data & Method Call  to Ext OPC-UA servers c5xx/c4xx with UAUITT_Username(1) using
        Security Policy "SignEncrypt" with user Auth active with "Fixed Node" &
        "Node Info get from UA Browse and UA TranslatePathList FB"
        Execute Test case 03 from Group 02
        """

        testResult, testRemarks = self._executeAuthGrp(testType = constants.TestType.MULTIPLE.value,
                                                        authType = FBTokenType.USERNAME)
        return testResult, testRemarks

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def executeGroup3(self):
        """
        TC07: Verify connection to Ext OPC-UA servers c5xx/c4xx with UAUITT_UserTokenID(100) using Security Policy
        "SignEncrypt" with user Auth active.
        Execute Test case 01 from Group 02

        TC08: Verify Read/Write Data to Ext OPC-UA servers c5xx/c4xx with UAUITT_UserTokenID(100) using
        Security Policy "SignEncrypt" with user Auth active with "Fixed Node" &
        "Node Info get from UA Browse & UA TranslatePathList FB"
        Execute Test case 02 from Group 02

        TC09: Verify Read/Write Data &Method Call to Ext OPC-UA servers c5xx/c4xx withUAUITT_UserTokenID(100) using
        SecurityPolicy"SignEncrypt" with user Auth active with "Fixed Node" &
        "Node Info get from UA Browse and UA TranslatePathList FB"
        Execute Test case 03 from Group 02
        """

        testResult, testRemarks = self._executeAuthGrp(testType = constants.TestType.MULTIPLE.value,
                                                        authType = FBTokenType.USERTOKENID)
        return testResult, testRemarks
