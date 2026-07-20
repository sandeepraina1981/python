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
from typing import Callable, List, Self
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
        xlsReaderObj = ConfigExlParserOpenClientAuthToken(configFile = constants.CONFIG_FILE_FB_EXT_PATH,
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
    def moveCertificateInPLCD(self):
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
                self.testCase.skip(f"Failed to update encryption policy")

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
        self.updateHostControllerTime(updateTimeInSeconds = 200)

        self.reportUpdaterObj.updateReportHeader(
            header = constants.REPORT_FB_EXT_HEADER.format(self.findCtrlType(self.ipcHostController),
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
        self.updateHostControllerTime(updateTimeInSeconds = 0)

        if not Lib_PLC_Open_Client_Auth_Tokens.PLC_OBJ.closePLC(
            projName = constants.PLC_PROJ_NAME.format(currControllerType),
            header = constants.PLC_HEADER, saveFlag = False):
            self.logger.warn("Failed to close PLC Designer tool")

        super().tearDownClass(behavior = behavior)
        return Result(errorCode = Result.NO_ERROR, errorMessage = "Success")

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def execute_Grp1(self):
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


        testResult, testRemarks = self._execute_AuthGrp(testType = constants.TestType.MULTIPLE.value,
                                                        authType = FBTokenType.ANONYMOUS)
        return testResult, testRemarks

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def execute_Grp2(self):
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

        testResult, testRemarks = self._execute_AuthGrp(testType = constants.TestType.MULTIPLE.value,
                                                        authType = FBTokenType.USERNAME)
        return testResult, testRemarks

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def execute_Grp3(self):
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

        testResult, testRemarks = self._execute_AuthGrp(testType = constants.TestType.MULTIPLE.value,
                                                        authType = FBTokenType.USERTOKENID)
        return testResult, testRemarks
