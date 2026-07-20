# -*- coding: utf-8 -*-
#
# © 2007-2008 Lenze Drive Systems GmbH. All rights reserved.
# © 2008-2021 Lenze Automation GmbH. All rights reserved.
#
#-----------------------------------------------------------------------------------------------------------------------
# PyTeF file header (for Test Library) V1.4-01
#-----------------------------------------------------------------------------------------------------------------------
# Disable linter warnings -> OTHER DISABLES ARE NOT RECOMMENDED, CHANGES ARE AT YOUR OWN RISK!
#
#-----------------------------------------------------------------------------------------------------------------------
# Test Library docstring (must be first definition in file)
#-----------------------------------------------------------------------------------------------------------------------
""" Library for Offline User Management Automation Test. This include all the grouped test cases which will be called
    from test script
    This include common function which will be used by all the tools while running the test
"""
#-----------------------------------------------------------------------------------------------------------------------
# Test Library imports (must be defined before code)
#-----------------------------------------------------------------------------------------------------------------------
import os
from typing import Any, Callable
from time import sleep
from pytef.namespace.testlib import FwTestLib, Version, autobehavior, Result
from tests.testlib.utils.CommonLib import userSleep, clsLogger
from tests.cysec.cysec_testsuites.offline_user_management.core.ProjectObjFactory import ProjectObjFactory
from tests.cysec.cysec_testsuites.offline_user_management.core.UserManagement_PLC import UserManagement_PLC
from tests.cysec.cysec_testsuites.offline_user_management.core.ExecuteCommand import ExecuteCommand
from tests.cysec.cysec_testsuites.offline_user_management.utils.excelReader import ConfigExlParser
from tests.cysec.cysec_testsuites.offline_user_management.utils.excelReportUpdater import ReportExlParser
from tests.cysec.cysec_testsuites.offline_user_management.utils import constants_offline_usermanagement
from tests.testlib.utils.CommonConstant import EnumFunctionSelectionInsertionBehaviour

import win32com.client

#-----------------------------------------------------------------------------------------------------------------------
# SVN keyword section
#-----------------------------------------------------------------------------------------------------------------------
FILE_URL = "$HeadURL: $"[10:-2]
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

    Example:
        @logTestDetails()
        def test_example(self):
            # Test implementation
            pass
    """
    #-------------------------------------------------------------------------------------------------------------------
    def decorator(func : Callable) -> Callable:
        # flake8: noqa: ANN001
        def wrapper(self, *args, **kwargs) -> Any:
            grpName = self.configXlsObj.getGroupName(testCaseName = self.testCase.testCaseName)
            testCaseNumber = self.configXlsObj.getTestCaseName(testCaseName = self.testCase.testCaseName).capitalize()
            jiraId = self.configXlsObj.getJiraIdByTestCase(testGroupName = grpName, testCaseNumber = testCaseNumber)

            self.logTestDescription(jiraId = jiraId)
            testResult = func(self, *args, **kwargs)

            self.logTestDescription(jiraId = jiraId, result = testResult, endFlag = True)
            self.saveTestResult(testResult = testResult, jiraId = jiraId)

            return testResult
        return wrapper
    return decorator

#-----------------------------------------------------------------------------------------------------------------------

class Lib_UserManagement(FwTestLib):
    """
        Offline User Management Lib
    """
    TC1_FAILED_FLAG = False
    PRE_REQ_FAILED = False

    prefixCls = 'Lib_UserManagement'
    __LIB_DICT = dict()

    LIB_VERSION = Version(1, 0, 0)
    LIB_NAME = "Lib_UserManagement"

    #-------------------------------------------------------------------------------------------------------------------
    def __init__(self) -> None:
        """
        Constructor
        """
        super().__init__()
        # ...
        self.logger.info(f"[{type(self).prefixCls}] in Lib_UserManagement::__init__()")
        self.plcObj = UserManagement_PLC(logger = self.logger)
        self.exeCmdObj = ExecuteCommand(logger = self.logger)

        self.configXlsObj = ConfigExlParser(config_file = constants_offline_usermanagement.CONFIG_FILE_PATH,
                                            logger = self.logger)

        self.reportXlsObj = ReportExlParser(logger = self.logger,
                                            controllerType = self.configXlsObj.controllerType,
                                            releaseName = self.configXlsObj.releaseName)

        self.currentJiraList = []

    #-------------------------------------------------------------------------------------------------------------------
    @classmethod
    def createTests(cls, testcls) -> None:
        """
        Auto create tests at runtime.

        1. For every testcase selected for execution a test is created.
        The name of each runtime testcase is in the format : *test_<testname>*

        2. Creates a test Set ( collection of testcases to be run)

        """
        logger = clsLogger(cls)

        configXlsObj = ConfigExlParser(constants_offline_usermanagement.CONFIG_FILE_PATH,
                                       logger = logger)

        try:
            for reqGrp, tcInfo in list(configXlsObj.testCaseSelectionDict.items()):
                reqGrpList = reqGrp.split("_")

                if configXlsObj.testCaseSelectionDict.get(reqGrp).get("runTestFlag"):
                    testCaseNamePre = f"test_{reqGrp}_test_00_pre"
                    testCaseNamePost = f"test_{reqGrp}_test_99_post"

                    funNameInTestPre = f"tc_{reqGrpList[0]}_{reqGrpList[1]}_Pre"
                    funNameInTestPost = f"tc_{reqGrpList[0]}_{reqGrpList[1]}_Post"

                    if 'Req_01' not in reqGrp:
                        testcls.addTestCase(name = testCaseNamePre,
                                            func = getattr(testcls, funNameInTestPre),
                                            tcParam = {})

                    for tcName, tcNamesDict in tcInfo.items():
                        if not tcName.startswith("Test_"):
                            continue

                        tcParam = {}

                        jiraInfo = configXlsObj.getJiraIdByTestCase(testGroupName = reqGrp, testCaseNumber = tcName)

                        jiraID = constants_offline_usermanagement.JIRA_TESTKEY.format(jiraInfo)
                        tcParam['@jiratest_tcIdList'] = [(None, [jiraID])]

                        testCaseName = f"test_{reqGrp}_{tcName.lower()}_{jiraID}"

                        logger.info(f"[{cls.prefixCls}] {testCaseName} is selected for execution")

                        if 'Req_01' in reqGrp:
                            funNameInTest = f"tc_{reqGrp}_{tcName.lower()}"
                        else:
                            funNameInTest = f"tc_{reqGrpList[0]}_{reqGrpList[1]}_Test"

                        testcls.addTestCase(name = testCaseName,
                                            func = getattr(testcls, funNameInTest),
                                            tcParam = tcParam)

                    if 'Req_01' not in reqGrp:
                        testcls.addTestCase(name = testCaseNamePost,
                                            func = getattr(testcls, funNameInTestPost),
                                            tcParam = {})
                else:
                    logger.info(f"[{cls.prefixCls}] tc_{reqGrp} is not selected for execution")

        except Exception:  # pylint: disable=broad-exception-caught
            logger.exception(f"[{cls.prefixCls}] Exception occurred in createTests ")

    #-------------------------------------------------------------------------------------------------------------------
    @autobehavior
    def setUpClass(self, behavior = None, **kwargs) -> Result:
        """
        Method to setup the library content (allocated resources).

        The method can be called form the <testcase>.setUpClass() to setup all allocated resources.

        :param behavior:  Auto behavior of this method.
        :returns: Result
        """
        projName = constants_offline_usermanagement.OFFLINE_USR_MGMT_PLC_PROJ_NAME
        projPath = os.getcwd() + constants_offline_usermanagement.OFFLINE_USR_MGMT_PROJ_PATH.format(
            self.configXlsObj.controllerType)
        try:
            self.logger.info(f"[{type(self).prefixCls}] Pre test setup validation successful")

            self.logger.info(f"[{type(self).prefixCls}] {self.configXlsObj}")

            self.logger.newStep("Step 1. Open PLC Designer tool")
            self.plcObj.openPLC(version = self.configXlsObj.plcVersion)

            self.logger.newStep("Step 2. Open existing project")
            projOpenStatus = self.plcObj.openProjAndHandleEnvWin(
                projPath = projPath, projName = projName, ignoreUpdatesFlag = True)
            if projOpenStatus:
                self.logger.info(f"[{type(self).prefixCls}] Project opened successfully")
            else:
                raise Exception("Some error occurred while opening project")  # pylint: disable=broad-exception-raised

            # self.plcObj.connectToRunningPLC(version = self.configXlsObj.plcVersion)
            # self.plcObj.projName = projName

            self.logger.newStep("Step 3. Set behaviour of Function node selection to "
                                "'Function nodes below EtherCAT'")
            setFunctionNodeInsertionStatus = self.plcObj.setBehaviourOfFunctionsNodeInsertion(
                projName = projName,
                eFuncNodeInsertionBehavior = EnumFunctionSelectionInsertionBehaviour.FUNCTION_NODES_BELOW_ETHERCAT)
            if setFunctionNodeInsertionStatus:
                self.logger.info(
                    f"[{type(self).prefixCls}] Successful set behaviour of Function node selection to "
                    "'Function nodes below EtherCAT'")
            else:
                self.logger.error(f"[{type(self).prefixCls}] Failed to set behaviour of Function node selection "
                                  "to 'Function nodes below EtherCAT'")
            #
            self.logger.newStep("Step 4. Logging in as Owner")
            # Logging in with Owner
            self.plcObj.loginUser(projName = constants_offline_usermanagement.OFFLINE_USR_MGMT_PLC_PROJ_NAME,
                                  userName = constants_offline_usermanagement.OWNER_USERNAME)

            self.logger.newStep("Step 5. Delete existing groups and users")
            if not self.plcObj.deleteAllUsersAndGroups(
                projName = constants_offline_usermanagement.OFFLINE_USR_MGMT_PLC_PROJ_NAME
            ):
                raise Exception("Failed to delete existing Users and Grourps")  # pylint: disable=broad-exception-raised

            self.logger.newStep("Step 6. Create Groups")
            # Creating two Groups: Group1 and Group2
            createGroup1Status = self.plcObj.createGroup(
                groupName = "Group1",
                projName = constants_offline_usermanagement.OFFLINE_USR_MGMT_PLC_PROJ_NAME)
            createGroup2Status = self.plcObj.createGroup(
                groupName = "Group2",
                projName = constants_offline_usermanagement.OFFLINE_USR_MGMT_PLC_PROJ_NAME)

            if createGroup1Status and createGroup2Status:
                self.logger.newStep("Groups created successfully")
            else:
                raise Exception("Error occurred while creating groups in PLCD project")

            self.logger.newStep("Step 7. Create Users")
            # Creating User: user1 with
            createUser1Status = self.plcObj.createUser(
                projName = constants_offline_usermanagement.OFFLINE_USR_MGMT_PLC_PROJ_NAME,
                userName = constants_offline_usermanagement.USER1_USERNAME,
                password = constants_offline_usermanagement.USER1_PASSWORD,
                memberShipList = ['Group1'])

            createUser2Status = self.plcObj.createUser(
                projName = constants_offline_usermanagement.OFFLINE_USR_MGMT_PLC_PROJ_NAME,
                userName = constants_offline_usermanagement.USER2_USERNAME,
                password = constants_offline_usermanagement.USER2_PASSWORD,
                memberShipList = ['Group2'])

            if createUser1Status and createUser2Status:
                self.logger.newStep("Users created successfully")
            else:
                raise Exception("Error occurred while creating users in PLCD project")

            self.logger.newStep("Pre-requisite step completed")
            return Result(errorCode = Result.NO_ERROR, errorMessage = "Success")
        except Exception as ex:  # pylint: disable=broad-exception-caught
            self.testCase.skip(ex)

    #-------------------------------------------------------------------------------------------------------------------
    @autobehavior
    def tearDownClass(self, behavior = None, **kwargs) -> Result:
        """
        Method to cleanup the library content (used resources).

        The method can be called form the <testcase>.tearDownClass() to cleanup all used resources.

        :param behavior:  Auto behavior of this method.
        :returns: Result

        """
        self.logger.info(f"[{type(self).prefixCls}] Closing PLC Designer tool")
        self.plcObj.closePLC(projName = constants_offline_usermanagement.OFFLINE_USR_MGMT_PLC_PROJ_NAME,
                             header = self.plcObj.header,
                             saveFlag = False)

        return Result(errorCode = Result.NO_ERROR,
                      errorMessage = "Success")

    #-------------------------------------------------------------------------------------------------------------------
    @autobehavior
    def setUp(self, behavior = None, **kwargs) -> Result:
        """
        Method to setup the library content (internal structures).

        The method can be called form the <testcase>.setUp() to setup all library internal structures.

        :param behavior:  Auto behavior of this method.
        :returns: Result
        """
        if Lib_UserManagement.TC1_FAILED_FLAG:
            self.testCase.skip("Skip test, Users and Groups not created..")

        return Result(errorCode = Result.NO_ERROR,
                      errorMessage = "Success")

    #-------------------------------------------------------------------------------------------------------------------
    @autobehavior
    def tearDown(self, behavior = None, **kwargs) -> Result:
        """
        Method to cleanup the library content (internal structures).

        The method can be called form the <testcase>.tearDown() to cleanup all internal structures.

        :param behavior:  Auto behavior of this method.
        :returns:         Result

        """
        return Result(errorCode = Result.NO_ERROR,
                      errorMessage = "Success")

    #-------------------------------------------------------------------------------------------------------------------
    def logTestDescription(self, jiraId: str, endFlag: bool = False, result: bool = None) -> None:
        """
        log Test Description

        """
        try:
            testDesc = self.reportXlsObj.getTestDescription(jiraId = jiraId)

            if not endFlag:
                self.logger.newStep(f"START : TC JIRA: {jiraId} - {testDesc}", level = 1)
            else:
                if result:
                    self.logger.newStep(f"END : TC JIRA: {jiraId} - {testDesc} - PASSED", level = 1)
                else:
                    self.logger.error("#" * 160)
                    self.logger.error(f"END : TC JIRA: {jiraId} - {testDesc} - FAILED")
                    self.logger.error("#" * 160)

        except IndexError:
            self.logger.warning(f"[{type(self).prefixCls}] Could not get test description from Report")
            self.logger.warning(f"[{type(self).prefixCls}] No jira found in device config")
        except Exception:  # pylint: disable=broad-exception-caught
            self.logger.exception(f"[{type(self).prefixCls}] Exception occurred in logTestDescription() ")

    #-------------------------------------------------------------------------------------------------------------------
    def saveTestResult(self, testResult: bool, jiraId: str) -> None:
        '''
        This method is used to save test result in report file
        '''
        self.reportXlsObj.updateResult(jiraId = jiraId, result = testResult)
        if not testResult:
            self.testCase.fail("TEST FAILED")

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def req_01_Grp_01_test_01(self) -> Any:
        """
        TC1.0 Create 2 user and 2 groups
        """
        try:
            # Go to Project Settings -> Users and Groups -> Groups tab and check if Group1 and Group2 is present
            self.logger.newStep("Verifying if Groups: Group1 and Group2 are created...", level = 3)
            grpCreateResult = self.plcObj.checkIfGroupsAreCreated(
                projName = constants_offline_usermanagement.OFFLINE_USR_MGMT_PLC_PROJ_NAME,
                groupNameList = ['Group1', 'Group2'])

            if grpCreateResult:
                self.logger.newStep("Verification of creation of Group1 and Group2 successful", level = 3)
            else:
                self.logger.error(f"[{type(self).prefixCls}] Verification of creation of Group1 and Group2 failed")

            # Go to Users tab and check if user1 is present with Group1's membership
            self.logger.newStep(f"Verifying if user: {constants_offline_usermanagement.USER1_USERNAME} is "
                                "properly created with membership to Group1", level = 3)
            usr1CreateResult = self.plcObj.checkIfUserIsCreated(
                projName = constants_offline_usermanagement.OFFLINE_USR_MGMT_PLC_PROJ_NAME,
                userName = constants_offline_usermanagement.USER1_USERNAME, memberShipList = ['Group1'])

            if usr1CreateResult:
                self.logger.newStep("user1 is properly created with membership of Group1", level = 3)
            else:
                self.logger.error(f"[{type(self).prefixCls}] user: user1 with membership of Group1 is not created..")

            # Go to Users tab and check if user2 is present with Group2's membership
            self.logger.newStep(f"Verifying if user: {constants_offline_usermanagement.USER2_USERNAME} "
                                "is properly created with membership to Group2", level = 3)
            usr2CreateResult = self.plcObj.checkIfUserIsCreated(
                projName = constants_offline_usermanagement.OFFLINE_USR_MGMT_PLC_PROJ_NAME,
                userName = constants_offline_usermanagement.USER2_USERNAME, memberShipList = ['Group2'])

            if usr2CreateResult:
                self.logger.newStep("user2 is properly created with membership of Group2", level = 3)
            else:
                self.logger.error(f"[{type(self).prefixCls}] user: user1 with membership of Group2 is not created..")

            self.logger.newStep("All Groups and users are properly created...")

            result = grpCreateResult and usr1CreateResult and usr2CreateResult

            return result
        except Exception:  # pylint: disable=broad-exception-caught
            self.logger.exception(f"[{type(self).prefixCls}] Exception occurred in  req_01_TcGrp_01() ")
            Lib_UserManagement.TC1_FAILED_FLAG = True
            return False

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def req_01_Grp_02_test_01(self) -> Any:
        """
        TC1.1 Verify User login / logoff to offline project
        """
        try:
            # Verifying login with user1
            self.logger.newStep(
                f"Verifying user login for {constants_offline_usermanagement.USER1_USERNAME}", level = 3)
            usr1LoginResult = self.plcObj.loginUser(
                projName = constants_offline_usermanagement.OFFLINE_USR_MGMT_PLC_PROJ_NAME,
                userName = constants_offline_usermanagement.USER1_USERNAME,
                base64Password = constants_offline_usermanagement.USER1_PASSWORD)

            if usr1LoginResult:
                self.logger.newStep(f"Login for user : {constants_offline_usermanagement.USER1_USERNAME} "
                                    "verified successfully", level = 3)
            else:
                self.logger.error(f"[{type(self).prefixCls}] Verification of user : "
                                  f"{constants_offline_usermanagement.USER1_USERNAME} login failed")

            # Verifying login with user2
            self.logger.newStep(
                f"Verifying user login for {constants_offline_usermanagement.USER2_USERNAME}", level = 3)
            usr2LoginResult = self.plcObj.loginUser(
                projName = constants_offline_usermanagement.OFFLINE_USR_MGMT_PLC_PROJ_NAME,
                userName = constants_offline_usermanagement.USER2_USERNAME,
                base64Password = constants_offline_usermanagement.USER2_PASSWORD)

            if usr2LoginResult:
                self.logger.newStep(f"Login for user : {constants_offline_usermanagement.USER2_USERNAME} "
                                    "verified successfully", level = 3)
            else:
                self.logger.error(f"[{type(self).prefixCls}] Verification of user : "
                                  f"{constants_offline_usermanagement.USER2_USERNAME} login failed")

            # Verifying login with Owner
            self.logger.newStep(
                f"Verifying user login for {constants_offline_usermanagement.OWNER_USERNAME}", level = 3)
            ownerLoginResult = self.plcObj.loginUser(
                projName = constants_offline_usermanagement.OFFLINE_USR_MGMT_PLC_PROJ_NAME,
                userName = constants_offline_usermanagement.OWNER_USERNAME)

            if ownerLoginResult:
                self.logger.newStep(
                    f"Login for user :{constants_offline_usermanagement.OWNER_USERNAME} "
                    "verified successfully", level = 3)
            else:
                self.logger.error(f"[{type(self).prefixCls}] Verification of "
                                  f"{constants_offline_usermanagement.OWNER_USERNAME} login failed")

            # Verifying login out
            self.logger.newStep("Verifying user logout", level = 3)
            logoutUserStatus = self.plcObj.logoutCurrentUser(
                projName = constants_offline_usermanagement.OFFLINE_USR_MGMT_PLC_PROJ_NAME)

            self.logger.info(f"[{type(self).prefixCls}] Verifying that no user is currently logged in")
            usrLogoutResult = logoutUserStatus and self.plcObj.checkNobodyIsLoggedIn(
                projName = constants_offline_usermanagement.OFFLINE_USR_MGMT_PLC_PROJ_NAME)

            if usrLogoutResult:
                self.logger.newStep("Successfully verified user logout", level = 3)
            else:
                self.logger.error(f"[{type(self).prefixCls}] Verification for user logout failed..")

            result = usr1LoginResult and usr2LoginResult and ownerLoginResult and usrLogoutResult

            return result
        except Exception:  # pylint: disable=broad-exception-caught
            self.logger.exception(f"[{type(self).prefixCls}] Exception occurred in  req_01_TcGrp_02() ")
            return False

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def req_01_Grp_03_test_01(self) -> Any:
        """
        TC11.1 Verify authentical trial settings for user authentication
        """
        try:
            authenticationTrialValue = 10
            testResult = False

            # Login as Owner and set maximum authentication trials value
            self.logger.newStep(f"Logging in as {constants_offline_usermanagement.OWNER_USERNAME}", level = 3)
            self.plcObj.loginUser(projName = constants_offline_usermanagement.OFFLINE_USR_MGMT_PLC_PROJ_NAME,
                                  userName = constants_offline_usermanagement.OWNER_USERNAME)
            self.logger.newStep(
                f"Setting Maximum number of authentication trials to {authenticationTrialValue}", level = 3)

            if self.plcObj.setMaxAuthenticationTrials(
                    projName = constants_offline_usermanagement.OFFLINE_USR_MGMT_PLC_PROJ_NAME,
                    authenticationTrialValue = authenticationTrialValue):
                # Verify that user becomes inactive after maximum authentication trials without password
                self.logger.newStep("Verifying maximum authentication trials setting", level = 3)
                maxAuthTrailVerifyStatus = self.plcObj.checkUserInactiveAfterMaxTrail(
                    projName = constants_offline_usermanagement.OFFLINE_USR_MGMT_PLC_PROJ_NAME,
                    userName = constants_offline_usermanagement.USER1_USERNAME,
                    maxAuthenticationTrailValue = authenticationTrialValue)

                if maxAuthTrailVerifyStatus:
                    self.logger.newStep("Max authentication trials settings successfully verified", level = 3)
                    testResult = True
                else:
                    self.logger.error(
                        f"[{type(self).prefixCls}] Max authentication trials settings verification failed")
            else:
                self.logger.error(f"[{type(self).prefixCls}] Failed to set Maximum Authentication trials")

            return testResult
        except Exception:  # pylint: disable=broad-exception-caught
            self.logger.exception(f"[{type(self).prefixCls}] Exception occurred in  req_01_TcGrp_03() ")
            return False

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def req_01_Grp_04_test_01(self) -> Any:
        """
        TC11.0 Verify authentically logout time settings when inactive for logged in user
        """
        try:
            inactivityLogoutTimeInMins = 1
            testResult = False

            self.plcObj.loginUser(projName = constants_offline_usermanagement.OFFLINE_USR_MGMT_PLC_PROJ_NAME,
                                  userName = constants_offline_usermanagement.OWNER_USERNAME)

            self.logger.newStep(f"Setting Inactivity logout time to {inactivityLogoutTimeInMins} min", level = 3)
            if self.plcObj.setInactivityLogoutTime(
                    projName = constants_offline_usermanagement.OFFLINE_USR_MGMT_PLC_PROJ_NAME,
                    inactivityLogoutTimeInMins = inactivityLogoutTimeInMins):
                self.logger.newStep("Logging in with user1")
                self.plcObj.loginUser(projName = constants_offline_usermanagement.OFFLINE_USR_MGMT_PLC_PROJ_NAME,
                                      userName = constants_offline_usermanagement.USER1_USERNAME,
                                      base64Password = constants_offline_usermanagement.USER1_PASSWORD)

                self.logger.newStep(f"Waiting for {inactivityLogoutTimeInMins} min ", level = 3)
                sleep(inactivityLogoutTimeInMins * 60)

                logoutStatus = self.plcObj.checkNobodyIsLoggedIn(
                    projName = constants_offline_usermanagement.OFFLINE_USR_MGMT_PLC_PROJ_NAME)
                if logoutStatus:
                    self.logger.newStep(f"User successfully got logged out after {inactivityLogoutTimeInMins} "
                                        "min of activity")
                    testResult = True
                else:
                    self.logger.error(f"[{type(self).prefixCls}] User did not got logged out after "
                                      f"{inactivityLogoutTimeInMins} min of activity")

            else:
                self.logger.error(f"[{type(self).prefixCls}] Failed to set Inactivity logout time")

            return testResult
        except Exception:  # pylint: disable=broad-exception-caught
            self.logger.exception(f"[{type(self).prefixCls}] Exception occurred in  req_01_TcGrp_04() ")
            return False

    #-------------------------------------------------------------------------------------------------------------------
    def req_02_pre(self) -> bool:
        """
        Pre Verify access to create, add or remove children, modify, remove, view
        """

        testObjectInfo = self.configXlsObj.getTestObjectInfo(testCaseName = self.testCase.testCaseName)

        projObjFactory = ProjectObjFactory()
        projObjArgs = {'plcObj' : self.plcObj,
                       'objType' : testObjectInfo["objectType"],
                       'Logger' : self.logger}

        # Create object from objectName
        projObj = projObjFactory.getProjectObject(projectObjName = testObjectInfo["objectName"],
                                                  projObjArgs = projObjArgs)

        # Performing pre-required steps for current project object
        self.logger.newStep("Performing pre-required operations", level = 3)
        preReqStatus = projObj.preReq()

        if not preReqStatus:
            Lib_UserManagement.PRE_REQ_FAILED = True
            raise Exception("Test failed while performing pre-req operation")

        self.logger.newStep("Pre-required operations completed", level = 3)
        return preReqStatus

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def req_02_test(self) -> Any:
        """
        Verify access to create, add or remove children, modify, remove, view
        """

        testObjectInfo = self.configXlsObj.getTestObjectInfo(testCaseName = self.testCase.testCaseName)

        if Lib_UserManagement.PRE_REQ_FAILED:
            self.testCase.skip(f'Test skipped as pre-required operations for {testObjectInfo["objectName"]} failed')

        testResult = None
        self.logger.newStep(f'PLCD PROJECT OBJECT UNDER TEST = {testObjectInfo["objectName"]}', level = 1)

        testID = int(self.testCase.testCaseName.split('_')[-2])
        actionIndex = constants_offline_usermanagement.SequenceIndex.from_index(testID).value

        try:
            projObjFactory = ProjectObjFactory()
            projObjArgs = {'plcObj' : self.plcObj,
                           'objType' : testObjectInfo["objectType"],
                           'Logger' : self.logger}

            # Create object from objectName
            projObj = projObjFactory.getProjectObject(projectObjName = testObjectInfo["objectName"],
                                                      projObjArgs = projObjArgs)

            # Execute testcases for requiredProjObj
            actionSequence = list(type(projObj).ACTION_SEQ.items())
            accessType, accessTypeData = actionSequence[actionIndex]

            self.plcObj.moveMousePtrToTitleBar(
                    projName = constants_offline_usermanagement.OFFLINE_USR_MGMT_PLC_PROJ_NAME)

            # Logging in as Owner
            self.logger.newStep(f"Logging in as {constants_offline_usermanagement.OWNER_USERNAME}", level = 3)
            loginStatus = self.plcObj.loginUser(
                projName = constants_offline_usermanagement.OFFLINE_USR_MGMT_PLC_PROJ_NAME,
                userName = constants_offline_usermanagement.OWNER_USERNAME)

            if not loginStatus:
                raise Exception(f"[{type(self).prefixCls}] {constants_offline_usermanagement.OWNER_USERNAME} "
                                "not logged in...")

            # Setting following permissions for project object
            # Everyone => Deny
            # Group 1 => Deny
            # Group 2 => Grant
            self.logger.newStep(
                "Setting Permissions : Everyone -> Deny, Group1 -> Deny, Group2 -> Grant", level = 3)

            permSetStatus = self.plcObj.setPermission(
                projName = constants_offline_usermanagement.OFFLINE_USR_MGMT_PLC_PROJ_NAME,
                permissionPath = constants_offline_usermanagement.PERMISSION_PATH_DICT[accessType],
                objectName = accessTypeData['nameInPermissionWin'],
                groupPermissionsDict = {"Everyone" : "Deny", "Group1" : "Deny", "Group2" : "Grant"}
                )

            if not permSetStatus:
                raise Exception(f"[{type(self).prefixCls}] Permission not set properly")

            # If accessType is add or remove children then access for add children operation
            # and remove children operation are verified separately
            if accessType == 'addOrRemoveChildren':
                # Logging in as user 1 and verifying addChildren access
                self.logger.newStep("Logging in as user1 and verifying addChildren access", level = 3)
                loginStatus = self.plcObj.loginUser(
                    projName = constants_offline_usermanagement.OFFLINE_USR_MGMT_PLC_PROJ_NAME,
                    userName = constants_offline_usermanagement.USER1_USERNAME,
                    base64Password = constants_offline_usermanagement.USER1_PASSWORD)

                if not loginStatus:
                    raise Exception(f"[{type(self).prefixCls}] {constants_offline_usermanagement.USER1_USERNAME}"
                                    " not logged in...")

                u1AddChildAccessResult = self.plcObj.verifyAccess(projObj = projObj,
                                                                  accessStr = 'addChildren',
                                                                  accessExpectedFlag = False)
                if not u1AddChildAccessResult:
                    self.logger.error(
                        f"[{type(self).prefixCls}] KNOWN ISSUE: action to addChildren is getting Granted even "
                        "if permission is set to Deny for Motion Objects, Hence ignoring this failure for now")

                # Logging in as user 2 and verifying addChildren access
                self.logger.newStep("Logging in as user2 and verifying addChildren access", level = 3)
                loginStatus = self.plcObj.loginUser(
                    projName = constants_offline_usermanagement.OFFLINE_USR_MGMT_PLC_PROJ_NAME,
                    userName = constants_offline_usermanagement.USER2_USERNAME,
                    base64Password = constants_offline_usermanagement.USER2_PASSWORD)

                if not loginStatus:
                    raise Exception(f"[{type(self).prefixCls}] {constants_offline_usermanagement.USER2_USERNAME} "
                                    "not logged in...")

                u2AddChildAccessResult = self.plcObj.verifyAccess(projObj = projObj,
                                                                  accessStr = 'addChildren',
                                                                  accessExpectedFlag = True)
                if not u2AddChildAccessResult:
                    self.logger.error(f"[{type(self).prefixCls}] Verification of "
                                      f"{constants_offline_usermanagement.USER2_USERNAME} "
                                      "access to addChildren failed...")

                # Logging in as user 1 and verifying addChildren access
                self.logger.newStep("Logging in as user1 and verifying removeChildren access", level = 3)
                loginStatus = self.plcObj.loginUser(
                    projName = constants_offline_usermanagement.OFFLINE_USR_MGMT_PLC_PROJ_NAME,
                    userName = constants_offline_usermanagement.USER1_USERNAME,
                    base64Password = constants_offline_usermanagement.USER1_PASSWORD)

                if not loginStatus:
                    raise Exception(f"[{type(self).prefixCls}] {constants_offline_usermanagement.USER1_USERNAME}"
                                    " not logged in...")

                u1RemChildAccessResult = self.plcObj.verifyAccess(projObj = projObj,
                                                                  accessStr = 'removeChildren',
                                                                  accessExpectedFlag = False)
                if not u1RemChildAccessResult:
                    self.logger.error(f"[{type(self).prefixCls}] Verification of "
                                      f"{constants_offline_usermanagement.USER1_USERNAME} "
                                      "access to removeChildren failed...")

                # Logging in as user 2 and verifying addChildren access
                self.logger.newStep("Logging in as user2 and verifying removeChildren access", level = 3)
                loginStatus = self.plcObj.loginUser(
                    projName = constants_offline_usermanagement.OFFLINE_USR_MGMT_PLC_PROJ_NAME,
                    userName = constants_offline_usermanagement.USER2_USERNAME,
                    base64Password = constants_offline_usermanagement.USER2_PASSWORD)

                if not loginStatus:
                    raise Exception(f"[{type(self).prefixCls}] {constants_offline_usermanagement.USER2_USERNAME} "
                                    "not logged in...")

                u2RemChildAccessResult = self.plcObj.verifyAccess(projObj = projObj,
                                                                  accessStr = 'removeChildren',
                                                                  accessExpectedFlag = True)
                if not u2RemChildAccessResult:
                    self.logger.error(f"[{type(self).prefixCls}] Verification of "
                                      f"{constants_offline_usermanagement.USER2_USERNAME} "
                                      "access to removeChildren failed...")

                u1AccessResult = u1AddChildAccessResult and u1RemChildAccessResult
                u2AccessResult = u2AddChildAccessResult and u2RemChildAccessResult
            else:
                # Logging in as user 1 and verifying access
                self.logger.newStep(f"Logging in as user1 and verifying {accessType} access", level = 3)
                loginStatus = self.plcObj.loginUser(
                    projName = constants_offline_usermanagement.OFFLINE_USR_MGMT_PLC_PROJ_NAME,
                    userName = constants_offline_usermanagement.USER1_USERNAME,
                    base64Password = constants_offline_usermanagement.USER1_PASSWORD)

                if not loginStatus:
                    raise Exception(f"[{type(self).prefixCls}] {constants_offline_usermanagement.USER1_USERNAME} "
                                    "not logged in...")

                u1AccessResult = self.plcObj.verifyAccess(projObj = projObj,
                                                          accessStr = accessType,
                                                          accessExpectedFlag = False)
                if not u1AccessResult:
                    self.logger.error(f"[{type(self).prefixCls}] Verification of "
                                      f"{constants_offline_usermanagement.USER1_USERNAME} access to "
                                      f"{accessType} failed...")

                self.plcObj.moveMousePtrToTitleBar(
                    projName = constants_offline_usermanagement.OFFLINE_USR_MGMT_PLC_PROJ_NAME)

                # Logging in as user 2 and verifying access
                self.logger.newStep(f"Logging in as user2 and verifying {accessType} access", level = 3)
                loginStatus = self.plcObj.loginUser(
                    projName = constants_offline_usermanagement.OFFLINE_USR_MGMT_PLC_PROJ_NAME,
                    userName = constants_offline_usermanagement.USER2_USERNAME,
                    base64Password = constants_offline_usermanagement.USER2_PASSWORD)

                if not loginStatus:
                    raise Exception(f"[{type(self).prefixCls}] {constants_offline_usermanagement.USER2_USERNAME} "
                                    "not logged in...")

                u2AccessResult = self.plcObj.verifyAccess(projObj = projObj,
                                                          accessStr = accessType,
                                                          accessExpectedFlag = True,
                                                          addorDeleteAfterFlag = True)
                if not u2AccessResult:
                    self.logger.error(f"[{type(self).prefixCls}] Verification of "
                                      f"{constants_offline_usermanagement.USER2_USERNAME} access to "
                                      f"{accessType} failed...")

            userSleep(2)
            self.plcObj.moveMousePtrToTitleBar(
                projName = constants_offline_usermanagement.OFFLINE_USR_MGMT_PLC_PROJ_NAME)
            userSleep(2)

            # Logging in as Owner
            self.logger.newStep(f"Logging in as {constants_offline_usermanagement.OWNER_USERNAME}", level = 3)
            loginStatus = self.plcObj.loginUser(
                projName = constants_offline_usermanagement.OFFLINE_USR_MGMT_PLC_PROJ_NAME,
                userName = constants_offline_usermanagement.OWNER_USERNAME)

            if not loginStatus:
                raise Exception(f"[{type(self).prefixCls}] {constants_offline_usermanagement.OWNER_USERNAME} "
                                "not logged in...")

            # Clearing permissions from all Groups for current accessType for current project object
            self.logger.newStep(f"Clearing Permission for {accessType} command", level = 3)
            permClearStatus = self.plcObj.setPermission(
                projName = constants_offline_usermanagement.OFFLINE_USR_MGMT_PLC_PROJ_NAME,
                permissionPath = constants_offline_usermanagement.PERMISSION_PATH_DICT[accessType],
                objectName = accessTypeData['nameInPermissionWin'],
                groupPermissionsDict = {"Everyone" : "Clear", "Group1" : "Clear", "Group2" : "Clear"})

            if not permClearStatus:
                raise Exception(f"[{type(self).prefixCls}] Permissions not cleared properly")

            # Logging out from Owner .. so that nobody is logged in..
            self.logger.newStep("Logging out from Owner.. so that nobody is logged in", level = 3)
            logoutStatus = self.plcObj.logoutCurrentUser(
                projName = constants_offline_usermanagement.OFFLINE_USR_MGMT_PLC_PROJ_NAME)

            if not logoutStatus:
                raise Exception(f"[{type(self).prefixCls}] Owner not logged out..")

            # Verifying access with no user logged in ( after clearing permisions)
            self.logger.newStep(f"Verifying {accessType} access", level = 3)
            if accessType == 'addOrRemoveChildren':
                nobodyAddChildAcessResult = self.plcObj.verifyAccess(projObj = projObj,
                                                                     accessStr = 'addChildren',
                                                                     accessExpectedFlag = True)
                if not nobodyAddChildAcessResult:
                    self.logger.error(f"[{type(self).prefixCls}] Verification of nobody access to "
                                      "addChildren failed...")

                nobodyRemChildAcessResult = self.plcObj.verifyAccess(projObj = projObj,
                                                                     accessStr = 'removeChildren',
                                                                     accessExpectedFlag = True)
                if not nobodyRemChildAcessResult:
                    self.logger.error(f"[{type(self).prefixCls}] Verification of nobody access to "
                                      "removeChildren failed...")

                nobodyAccessResult = nobodyAddChildAcessResult and nobodyRemChildAcessResult
            else:
                nobodyAccessResult = self.plcObj.verifyAccess(projObj = projObj,
                                                              accessStr = accessType,
                                                              accessExpectedFlag = True)
                if not nobodyAccessResult:
                    self.logger.error(f"[{type(self).prefixCls}] Verification of nobody access to "
                                      f"{accessType} failed...")

            testResult = u1AccessResult and u2AccessResult and nobodyAccessResult
            return testResult

        except Exception:  # pylint: disable=broad-exception-caught
            self.logger.exception(f"[{type(self).prefixCls}] Exception occurred in Requirement 2 for "
                                  f'{testObjectInfo["objectName"]} object')

            if testResult is None:
                self.testCase.skip(f"[{type(self).prefixCls}] Exception occurred in prerequisite for "
                                   f'{testObjectInfo["objectName"]} object')

            return False

    #-------------------------------------------------------------------------------------------------------------------
    def req_02_post(self) -> bool:
        """
        Post Verify access to create, add or remove children, modify, remove, view
        """

        testObjectInfo = self.configXlsObj.getTestObjectInfo(testCaseName = self.testCase.testCaseName)

        if Lib_UserManagement.PRE_REQ_FAILED:
            Lib_UserManagement.PRE_REQ_FAILED = False
            self.testCase.skip(f'Post operations skipped as pre-required operations for '
                               f'{testObjectInfo["objectName"]} failed')

        projObjFactory = ProjectObjFactory()
        projObjArgs = {'plcObj' : self.plcObj,
                       'objType' : testObjectInfo["objectType"],
                       'Logger' : self.logger}

        # Create object from objectName
        projObj = projObjFactory.getProjectObject(projectObjName = testObjectInfo["objectName"],
                                                  projObjArgs = projObjArgs)

        # Performing post-required steps for current project object
        self.logger.newStep("Performing cleanup operation", level = 3)
        Lib_UserManagement.PRE_REQ_FAILED = False
        projObj.cleanUp()
        self.logger.newStep("Cleanup operation completed", level = 3)

        return True

    #-------------------------------------------------------------------------------------------------------------------
    def req_03_pre(self) -> Any:
        """
        Pre Verify access rights to execute command type
        """

        testObjectInfo = self.configXlsObj.getTestObjectInfo(testCaseName = self.testCase.testCaseName)

        if testObjectInfo["objectName"] in constants_offline_usermanagement.TESTS_WITH_CR:
            self.testCase.skip(f'Pre Test {testObjectInfo["objectName"]} cannot be executed due to a CR L-17578')

        self.exeCmdObj.connectToRunningPLC(version = self.configXlsObj.plcVersion)

        self.logger.newStep(f'Performing pre-required steps for {testObjectInfo["objectName"]} command')
        preReqStatus = True

        try:
            if testObjectInfo["preReqArgs"]:
                preReqStatus = getattr(
                    self.exeCmdObj, "preReq" + testObjectInfo["objectName"])(**testObjectInfo["preReqArgs"])
            else:
                preReqStatus = getattr(self.exeCmdObj, "preReq" + testObjectInfo["objectName"])()
        except Exception:  # pylint: disable=broad-exception-caught
            self.logger.newStep(f'Pre-requisite steps are not needed for {testObjectInfo["objectName"]} command')

        if not preReqStatus:
            Lib_UserManagement.PRE_REQ_FAILED = True
            raise Exception(f'Some error occurred in pre-required steps for {testObjectInfo["objectName"]} command')

        self.logger.newStep(f'Pre-required steps for {testObjectInfo["objectName"]} command completed')

        return True

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def req_03_test(self) -> Any:
        """
        Verify access rights to execute command type
        """

        testObjectInfo = self.configXlsObj.getTestObjectInfo(testCaseName = self.testCase.testCaseName)

        if testObjectInfo["objectName"] in constants_offline_usermanagement.TESTS_WITH_CR:
            self.testCase.fail(f'Test {testObjectInfo["objectName"]} cannot be executed due to a CR L-17578')

        if Lib_UserManagement.PRE_REQ_FAILED:
            self.testCase.skip(f'Test skipped as pre-required operations for {testObjectInfo["objectName"]} failed')

        testResult = None
        try:
            self.exeCmdObj.connectToRunningPLC(version = self.configXlsObj.plcVersion)

            # Logging in as Owner
            self.exeCmdObj.moveMousePtrToTitleBar(
                projName = constants_offline_usermanagement.OFFLINE_USR_MGMT_PLC_PROJ_NAME)
            self.logger.newStep(f"Logging in as {constants_offline_usermanagement.OWNER_USERNAME}", level = 3)

            loginStatus = self.exeCmdObj.loginUser(
                projName = constants_offline_usermanagement.OFFLINE_USR_MGMT_PLC_PROJ_NAME,
                userName = constants_offline_usermanagement.OWNER_USERNAME)

            if not loginStatus:
                raise Exception(f"[{type(self).prefixCls}] {constants_offline_usermanagement.OWNER_USERNAME} "
                                "not logged in...")

            # Setting following permissions for project object
            # Everyone => Deny
            # Group 1 => Deny
            # Group 2 => Grant
            self.logger.newStep("Setting Permissions : Everyone -> Deny, Group1 -> Deny, Group2 -> Grant", level = 3)
            permSetStatus = self.exeCmdObj.setPermission(
                projName = constants_offline_usermanagement.OFFLINE_USR_MGMT_PLC_PROJ_NAME,
                permissionPath = constants_offline_usermanagement.PERMISSION_PATH_DICT['execute'],
                objectName = constants_offline_usermanagement.NAMES_IN_PERMISSION_WIN_DICT.get(
                    testObjectInfo["objectName"]),
                groupPermissionsDict = {"Everyone" : "Deny", "Group1" : "Deny", "Group2" : "Grant"}
                )

            if not permSetStatus:
                raise Exception(f"[{type(self).prefixCls}] Permissions not set properly")

            self.exeCmdObj.moveMousePtrToTitleBar(
                projName = constants_offline_usermanagement.OFFLINE_USR_MGMT_PLC_PROJ_NAME)

            # Logging in as user 1 and verifying access
            self.logger.newStep(f'Logging in as user1 and verifying {testObjectInfo["objectName"]} access', level = 3)
            loginStatus = self.exeCmdObj.loginUser(
                projName = constants_offline_usermanagement.OFFLINE_USR_MGMT_PLC_PROJ_NAME,
                userName = constants_offline_usermanagement.USER1_USERNAME,
                base64Password = constants_offline_usermanagement.USER1_PASSWORD)

            if not loginStatus:
                raise Exception(f"[{type(self).prefixCls}] {constants_offline_usermanagement.USER1_USERNAME} "
                                "not logged in...")

            u1AccessResult = self.exeCmdObj.verifyExecuteCmdAccess(objName = testObjectInfo["objectName"],
                                                                   accessExpectedFlag = False)
            if not u1AccessResult:
                self.logger.error(f"[{type(self).prefixCls}] Verification of "
                                  f"{constants_offline_usermanagement.USER1_USERNAME} access to execute "
                                  f'{testObjectInfo["objectName"]} command failed')

            self.exeCmdObj.moveMousePtrToTitleBar(
                projName = constants_offline_usermanagement.OFFLINE_USR_MGMT_PLC_PROJ_NAME)

            # Logging in as user 2 and verifying access
            self.logger.newStep(f'Logging in as user2 and verifying {testObjectInfo["objectName"]} access', level = 3)
            loginStatus = self.exeCmdObj.loginUser(
                projName = constants_offline_usermanagement.OFFLINE_USR_MGMT_PLC_PROJ_NAME,
                userName = constants_offline_usermanagement.USER2_USERNAME,
                base64Password = constants_offline_usermanagement.USER2_PASSWORD)

            if not loginStatus:
                raise Exception(f"[{type(self).prefixCls}] {constants_offline_usermanagement.USER2_USERNAME} "
                                "not logged in...")

            u2AccessResult = self.exeCmdObj.verifyExecuteCmdAccess(objName = testObjectInfo["objectName"],
                                                                   accessExpectedFlag = True)
            if not u2AccessResult:
                self.logger.error(f"[{type(self).prefixCls}] Verification of "
                                  f"{constants_offline_usermanagement.USER2_USERNAME} access to execute "
                                  f'{testObjectInfo["objectName"]} command failed')

            userSleep(2)
            self.exeCmdObj.moveMousePtrToTitleBar(
                projName = constants_offline_usermanagement.OFFLINE_USR_MGMT_PLC_PROJ_NAME)

            # Logging in as Owner
            self.logger.newStep(f"Logging in as {constants_offline_usermanagement.OWNER_USERNAME}", level = 3)
            loginStatus = self.exeCmdObj.loginUser(
                projName = constants_offline_usermanagement.OFFLINE_USR_MGMT_PLC_PROJ_NAME,
                userName = constants_offline_usermanagement.OWNER_USERNAME)

            if not loginStatus:
                raise Exception(f"[{type(self).prefixCls}] {constants_offline_usermanagement.OWNER_USERNAME} "
                                "not logged in...")

            # Clearing permissions from all Groups for current accessType for current project object
            self.logger.newStep(f'Clearing Permission for execute {testObjectInfo["objectName"]} command', level = 3)
            permClearStataus = self.exeCmdObj.setPermission(
                projName = constants_offline_usermanagement.OFFLINE_USR_MGMT_PLC_PROJ_NAME,
                permissionPath = constants_offline_usermanagement.PERMISSION_PATH_DICT['execute'],
                objectName = constants_offline_usermanagement.NAMES_IN_PERMISSION_WIN_DICT.get(
                    testObjectInfo["objectName"]),
                groupPermissionsDict = {"Everyone" : "Clear", "Group1" : "Clear", "Group2" : "Clear"}
                )

            if not permClearStataus:
                raise Exception(f"[{type(self).prefixCls}] Permissions not cleared properly")

            # Logging out from Owner .. so that nobody is logged in..
            self.logger.newStep("Logging out from Owner.. so that nobody is logged in", level = 3)
            logoutStatus = self.exeCmdObj.logoutCurrentUser(
                projName = constants_offline_usermanagement.OFFLINE_USR_MGMT_PLC_PROJ_NAME)

            if not logoutStatus:
                raise Exception(f"[{type(self).prefixCls}] Owner is not logged out")

            # Verifying access with no user logged in ( after clearing permisions)
            self.logger.newStep(f'Verifying execute {testObjectInfo["objectName"]} command access', level = 3)

            self.exeCmdObj.moveMousePtrToTitleBar(
                projName = constants_offline_usermanagement.OFFLINE_USR_MGMT_PLC_PROJ_NAME)

            nobodyAccessResult = self.exeCmdObj.verifyExecuteCmdAccess(objName = testObjectInfo["objectName"],
                                                                       accessExpectedFlag = True)
            if not nobodyAccessResult:
                self.logger.error(f"[{type(self).prefixCls}] Verification of nobody access to execute "
                                  f'{testObjectInfo["objectName"]} command failed')

            testResult = u1AccessResult and u2AccessResult and nobodyAccessResult
            return testResult

        except Exception:  # pylint: disable=broad-exception-caught
            self.logger.exception(f"[{type(self).prefixCls}] Exception occurred in Requirement 3 for "
                                  f'{testObjectInfo["objectName"]} command')

            if testResult is None:
                self.testCase.skip("Exception occurred in prerequisite")

            return False

    #-------------------------------------------------------------------------------------------------------------------
    def req_03_post(self) -> Any:
        """
        Post verify access rights to execute command type
        """

        cleanUpStatus = True
        testObjectInfo = self.configXlsObj.getTestObjectInfo(testCaseName = self.testCase.testCaseName)

        if testObjectInfo["objectName"] in constants_offline_usermanagement.TESTS_WITH_CR:
            self.testCase.skip(f'Post Test {testObjectInfo["objectName"]} cannot be executed due to a CR L-17578')

        if Lib_UserManagement.PRE_REQ_FAILED:
            Lib_UserManagement.PRE_REQ_FAILED = False
            self.testCase.skip(f'Post operations skipped as pre-required operations for '
                               f'{testObjectInfo["objectName"]} failed')

        self.logger.newStep(f'Performing clean up steps for {testObjectInfo["objectName"]} command')

        try:
            cleanUpStatus = getattr(self.exeCmdObj, "cleanUp" + testObjectInfo["objectName"])()
            if not cleanUpStatus:
                self.logger.error(f"[{type(self).prefixCls}] Some error occurred in pre-required steps for "
                                  f'{testObjectInfo["objectName"]} command')

            else:
                self.logger.newStep(f'Cleanup steps for {testObjectInfo["objectName"]} command completed')
        except Exception:  # pylint: disable=broad-exception-caught
            self.logger.newStep(f'Cleanup steps are not needed for {testObjectInfo["objectName"]} command')

        if not cleanUpStatus:
            self.logger.error(f"[{type(self).prefixCls}] Some error occurred in clean-up steps for "
                              f'{testObjectInfo["objectName"]} command')
        else:
            self.logger.newStep(f'Cleanup steps for {testObjectInfo["objectName"]} command completed')

        Lib_UserManagement.PRE_REQ_FAILED = False

        return True
