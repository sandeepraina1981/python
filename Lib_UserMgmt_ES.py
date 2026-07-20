# -*- coding: utf-8 -*-
#
# © 2007-2008 Lenze Drive Systems GmbH. All rights reserved.
# © 2008-2021 Lenze Automation GmbH. All rights reserved.
#
#-----------------------------------------------------------------------------------------------------------------------
# PyTeF file header (for Test Library) V1.4-01
#-----------------------------------------------------------------------------------------------------------------------
# Disable linter warnings -> OTHER DISABLES ARE NOT RECOMMENDED, CHANGES ARE AT YOUR OWN RISK!
# pylint: disable=relative-import,wildcard-import,unused-wildcard-import
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
import os
import socket
import xml.etree.ElementTree as ET
from typing import Callable, Any

from pytef.namespace.testlib import Version, autobehavior, Result
from tests.opc_ua.opcua_cysec.core.Plcd import OpcUa_PLC
from tests.opc_ua.opcua_cysec.test_suites.lib.Lib_OpcUa_Base import Lib_OpcUa_Base
from tests.opc_ua.opcua_cysec.resources.utils.excelReportUpdater import ReportExlParser
from tests.opc_ua.opcua_cysec.resources.utils import constants_opc_ua as commonConstants, constants_opc_ua
from tests.opc_ua.opcua_cysec.test_suites.test_opc_ua.usermangement_and_es_auth.utils import constants
from tests.testlib.utils.CommonLib import userSleep, deleteUserManagementFiles, clsLogger
from tests.opc_ua.opcua_cysec.test_suites.test_opc_ua.usermangement_and_es_auth.utils.excelReader import ConfigExlParser
#-----------------------------------------------------------------------------------------------------------------------
# SVN keyword section
#-----------------------------------------------------------------------------------------------------------------------
FILE_URL = "$HeadURL: http://repository.lenze.com/ssv/TestRepository/branches/sdc/tests/common/opc_ua/lib/Lib_OpcUa.py $"[10:-2]  # noqa:E501
FILE_REV = "$Revision: 9126 $"[11:-2]
FILE_DATE = "$LastChangedDate: 2022-05-23 10:16:31 +0530 (Mon, 23 May 2022) $"[18:-2]
FILE_AUTHOR = "$LastChangedBy: saklechas $"[16:-2]

#-----------------------------------------------------------------------------------------------------------------------
# PyTeF file header end
#-----------------------------------------------------------------------------------------------------------------------
def logTestDetails() -> Callable:
    """
    Decorator to log test details, capture execution metadata, and update results to Jira.

    Args:
        jiraIndex (int): The index of the test case in Spira/Jira mapping.

    Returns:
        Callable: A decorator that wraps the test function to handle logging,
        result saving, and Jira integration.

    Behavior:
        1. Logs the test description at the start of the test.
        2. Executes the test function and captures its result (True/False).
        3. Logs the test description again with the result at the end of the test.
        4. Saves the test result locally.
    """
    #-------------------------------------------------------------------------------------------------------------------
    def decorator(func : Callable) -> Callable:

        def wrapper(self, *args, **kwargs) -> bool:

            jiraIndex = None

            self.logTestDescription(jiraIndex = jiraIndex)

            try:
                result = func(self, *args, **kwargs)

            except Exception:
                self.logger.exception(f"[{type(self).prefixCls}] Exception occurred while executing the test case.")
                result = False

            finally:
                self.logTestDescription(jiraIndex = jiraIndex, endFlag = True, result = result)
                self.saveTestResult(testResult = result)

            return result
        return wrapper
    return decorator

#-----------------------------------------------------------------------------------------------------------------------
class Lib_UserMgmt_ES(Lib_OpcUa_Base):
    """
        OPC UA User Management and ES Auth Test Lib
    """
    prefixCls = 'Lib_UserMgmt_ES'
    __LIB_DICT = {}

    LIB_NAME = "Lib_UserMgmt_ES"
    LIB_VERSION = Version(1, 0, 0)
    PLCD_OBJECT = None
    THIRD_PARTYCLIENT_OBJECT = None

    lastTestPassed = True
    downloadPLCDProjectFlag = True

    #-------------------------------------------------------------------------------------------------------------------
    def __init__(self):
        """
        Constructor
        """
        self.logger.info(f"[{type(self).prefixCls}] in Lib_OpcUa::__init__()")
        type(self).CONFIG_FILE_OBJ = ConfigExlParser(
            logger = self.logger,
            config_file = constants.CONFIG_FILE_PATH + r"\DeviceConfig_UserMangement_and_ES_Auth.xls")
        super().__init__()

        self.reportXlsObj = ReportExlParser(
            logger = self.logger,
            reportFile = commonConstants.REPORT_FILE_PATH.format(self.configXlsObj.controllerType),
            reportSheetName = constants.REPORT_SHEET_NAME,
            controllerType = self.configXlsObj.controllerType,
            releaseName = self.configXlsObj.releaseName)

    #-------------------------------------------------------------------------------------------------------------------
    @classmethod
    def createTests(cls, testcls):
        """
        Calling base class method
        """
        Lib_OpcUa_Base.CONFIG_FILE_OBJ = ConfigExlParser(
            logger = clsLogger(),
            config_file = constants.CONFIG_FILE_PATH + r"\DeviceConfig_UserMangement_and_ES_Auth.xls")
        super().createTests(testcls = testcls)

    #-------------------------------------------------------------------------------------------------------------------
    @autobehavior
    def setUpClass(self, behavior = None, **kwargs) -> Result:
        """
        Steps -
            • Disable user management
            • Calling base class method
            • Open PLCD project, clean all and build the project, and select the controller
        """

        # Deleting user management files from the controller
        self.logger.newStep("Step 1: Deleting user managment files from controller if any")
        deleteUserManagementFiles(logger = self.logger,
                                  ipAddress = self.configXlsObj.controllerIP)

        self.logger.newStep("Step 2: Rebooting controller")
        if not self.restartController():
            self.testCase.fail("Failed to reboot controller after deleting user management")

        self.logger.info("Waiting for 30 secs, for OPC Ua Server to restart before connection with Pytef Client")
        userSleep(60)

        super().setUpClass(behavior = behavior, checkEcatFlag = False)

        projName = kwargs.get("projName", commonConstants.PLC_PROJ_NAME)

        # PLC object
        Lib_UserMgmt_ES.PLCD_OBJECT = OpcUa_PLC(logger = self.logger)

        # Start PLCD tool and open OPC UA project in it
        self.logger.newStep("Step 3: Starting PLC Designer and open project")
        if not Lib_UserMgmt_ES.PLCD_OBJECT.startPlcAndOpenProj(version = self.configXlsObj.plcVersion,
                                                               projPath  = self.projectPath,
                                                               projName = projName):
            self.testCase.skip("Failed to start PLC and open project")

        # Checking and logging watch dog status of project
        self.logger.info(f"[{type(self).prefixCls}] checking if watchdog is enabled or not")
        if not Lib_UserMgmt_ES.PLCD_OBJECT.checkIfWatchDogEnabled(projName = projName):
            self.logger.warning(f"[{type(self).prefixCls}] Watchdog is disable")
        else:
            self.logger.info(f"[{type(self).prefixCls}] Watchdog is enable")

        # Performing clean all and build operation on the project
        self.logger.newStep("Step 4: Clean All and Building project: ")
        if not Lib_UserMgmt_ES.PLCD_OBJECT.cleanAllBuild(projName = projName):
            self.testCase.skip("Step clean all failed...")

        self.logger.info(f"[{type(self).prefixCls}] Building Project....")
        if not Lib_UserMgmt_ES.PLCD_OBJECT.buildProject(projName = projName):
            self.testCase.skip(" Build project failed...")

        # Selecting controller
        self.logger.newStep("Step 5: Select controller")
        if not Lib_UserMgmt_ES.PLCD_OBJECT.selectController(ipAddress = self.configXlsObj.controllerIP,
                                                            gatewayIp = self.configXlsObj.controllerIP,
                                                            projName = projName):
            self.testCase.skip("Failed to select the controller")

        return Result(errorCode = Result.NO_ERROR, errorMessage = "Success")

    #-------------------------------------------------------------------------------------------------------------------
    @autobehavior
    def tearDownClass(self, behavior = None, **kwargs) -> Result:
        """
        Steps -
            • Close PLCD tool
            • Disable user management
        """
        projName = kwargs.get("projName", commonConstants.PLC_PROJ_NAME)

        # Closing PLC tool after test completion
        self.logger.newStep("Close PLCD tool", level = 3)
        if not Lib_UserMgmt_ES.PLCD_OBJECT.closePLC(projName = projName,
                                                    header = self.configXlsObj.plcheader,
                                                    saveFlag = False):
            self.logger.warning(f"[{type(self).prefixCls}] Close Failed...")

        # Deleting User management is not activated
        self.logger.newStep("Deleting user managment files from controller if any", level = 3)
        if not deleteUserManagementFiles(logger = self.logger,
                                         ipAddress = self.configXlsObj.controllerIP):
            self.logger.warning("Failed to delete user management from controller")

        # Rebooting controller after deleting user management files from it
        self.logger.newStep("Rebooting controller", level = 3)
        if not self.restartController():
            self.logger.warning(f"[{type(self).prefixCls}] Failed to reboot controller after deleting user management")

        return Result(errorCode = Result.NO_ERROR, errorMessage = "Success")

    #-------------------------------------------------------------------------------------------------------------------
    def pre_setUp(self, **kwargs) -> Any:
        """
        Method to setup the library content (internal structures).

        The method can be called form the <testcase>.setUp() to setup all library internal structures.

        :param behavior:  Auto behavior of this method.
        :returns: Result
        """
        projName = kwargs.get("projName", commonConstants.PLC_PROJ_NAME)

        # Handle No connection to the device popup if appeared
        Lib_UserMgmt_ES.PLCD_OBJECT.handlePLCConnectionLost(header = self.configXlsObj.plcheader)

        # Selecting controller
        self.logger.newStep(f"[{type(self).prefixCls}] Select controller", level = 3)
        self.logger.info(f"[{type(self).prefixCls}] Closing all open editors to fix issue of window pane freezing")
        Lib_UserMgmt_ES.PLCD_OBJECT.close_All_Editors(projName = projName)
        if not Lib_UserMgmt_ES.PLCD_OBJECT.selectController(
                ipAddress = self.configXlsObj.controllerIP, projName = projName,
                gatewayIp = self.configXlsObj.controllerIP,
                userName = commonConstants.USERS_DETAILS_DICT_SECURITY_TEST["administratorUser"]["userName"],
                base64Password = commonConstants.USERS_DETAILS_DICT_SECURITY_TEST["administratorUser"]["password"]):
            self.testCase.skip("Failed to select the controller")

        # Going Online so as to handle CR and handle usermanagement popup
        self.logger.newStep(f"[{type(self).prefixCls}] Logging in to the controller", level = 3)
        Lib_UserMgmt_ES.PLCD_OBJECT.goOnline(
            userName = commonConstants.USERS_DETAILS_DICT_SECURITY_TEST["administratorUser"]["userName"],
            base64EncryptedPassword = commonConstants.USERS_DETAILS_DICT_SECURITY_TEST["administratorUser"]["password"],
            projName = projName)
        Lib_UserMgmt_ES.PLCD_OBJECT.goOffline(projName = projName,
                                              header = self.configXlsObj.plcheader)

        # Enable Anonymous user login
        self.logger.newStep(f"[{type(self).prefixCls}] Enabling 'Anonymous user login'", level = 3)
        if not Lib_UserMgmt_ES.PLCD_OBJECT.enableOrDisableAnonymousUserLogin(
                projName = projName):
            self.testCase.skip("Failed to enable 'Anonymous user login")
        userSleep(5)

        result = super().setUp()
        Lib_OpcUa_Base.dummy3rdPrtyPyClientObj.closeSession()

        Lib_UserMgmt_ES.PLCD_OBJECT.goOnline(projName = projName)
        Lib_UserMgmt_ES.PLCD_OBJECT.createBootProject(projName = projName)

        Lib_UserMgmt_ES.PLCD_OBJECT.goOffline(projName = projName,
                                              header = self.configXlsObj.plcheader)

        return result

    #-------------------------------------------------------------------------------------------------------------------
    @autobehavior
    def tearDown(self, behavior = None, **kwargs) -> Result:
        """
        tearDown method Return noErr result
        """
        return Result(errorCode = Result.NO_ERROR, errorMessage = "Success")

    #-------------------------------------------------------------------------------------------------------------------
    def waitForFWLoaderSessionToClose(self, firmwareLoaderObj, userName = None, base64EncryptedPassword = None) -> bool:
        """
        This method is used to wait for firmware loading session to get closed after Firmware loading
        """
        try:
            # Waiting for firmware loading to complete if firmware loader tool is open
            flWin = firmwareLoaderObj.getMainWindow(header = firmwareLoaderObj.header)
            if flWin and flWin.exists():

                firmwareLoaderObj.checkIfFirmwareLoadingDone(
                    deviceDict = Lib_OpcUa_Base.clientArgs[commonConstants.FIRMWARE_LOADER_NAME].get("deviceDict"))
                # Updating numeric id of dummy third party client firmware loading causes controller to reboot
                self.logger.info(f'[{type(self).prefixCls}] Wating for 20 seconds')
                userSleep(20)
                self.updateNumericIds(userName = userName,
                                      base64EncryptedPassword = base64EncryptedPassword)
                timeout = 90
                self.logger.info(f"[{type(self).prefixCls}] Waiting for firmwareloader session to close.. timeout = "
                                 f"{timeout} seconds")
                while timeout:
                    # Get Session details of all active
                    objSessionDetails = self.getSessionDetails()
                    if objSessionDetails.sessionCount != 1:
                        self.logger.error(f"[{type(self).prefixCls}] Session count ({objSessionDetails.sessionCount}) "
                                          "is not equal to Excepted Session Count 1")
                        userSleep(5)
                        timeout -= 5
                        self.logger.info(f"[{type(self).prefixCls}] Waiting 5 seconds and retrying to check if "
                                         f"firmware loader session is closed timeout = {timeout} seconds")
                    else:
                        self.logger.info(f"[{type(self).prefixCls}] Firmware loader session closed")
                        return True
                self.logger.error(f"[{type(self).prefixCls}] Timeout error: Firmware loader is still occupying "
                                  "session after 90 seconds")
                return False
            self.logger.info(f"[{type(self).prefixCls}] FirmwareLoader tool is closed")
            return True
        except Exception:
            self.logger.exception(f"[{type(self).prefixCls}] Failure in Firmware Loading")
            return False

    #-------------------------------------------------------------------------------------------------------------------
    def getSymbolSetsAssignToGroups(self, dsmFilePath, dsmFileName) -> {}:
        """
        This function is used to return symbolSets assign to group from dsm file
        """
        dsmFile = dsmFilePath + '\\' + dsmFileName
        tree = ET.parse(dsmFile)
        root = tree.getroot()
        groupsSymbolRightsDict = {}
        for symbolRightsObject in root:
            if symbolRightsObject.tag != "SymbolRightsObject":
                continue
            symbolSetName = [child.text for child in symbolRightsObject if child.tag == "SymbolSetName"][0]
            for devicePermissionses in symbolRightsObject:
                if devicePermissionses.tag != 'DevicePermissionses':
                    continue
                for group in devicePermissionses:
                    groupName = group.text
                    if groupName in groupsSymbolRightsDict:
                        groupsSymbolRightsDict[groupName].append(symbolSetName)
                    else:
                        groupsSymbolRightsDict[groupName] = [symbolSetName]
        return groupsSymbolRightsDict

    #-------------------------------------------------------------------------------------------------------------------
    def verifySymbolAccessUsingPytef(self, thirdPrtyClientObj, plcObj) -> bool:
        """
        This function is used to verify Symbol access to group via pytef
        Step -
        1. Getting all symbolSets access assign to each groups
        2. Occupying PyTef with each users (AdministratorUser, ServiceUser, Developr=erUser)
        3. Get all the Symbols and subSymbols accessible to that user via Pytef
        4. Compere this accessible symbol and subSymbols from xml file data
               (Return True if both mathces for all users else False)
        """
        atleastOneFail = False
        try:
            # Getting all symbol sets access assign to each group in dictionary
            self.logger.newStep("Step 1: Getting all symbolSets access assign to each groups")
            groupsSymbolSetDict = self.getSymbolSetsAssignToGroups(
                dsmFilePath = constants.SECURITY_TEST_INPUT_FILES,
                dsmFileName = commonConstants.DEVICE_SYMBOL_MANAGEMENT_FILE_NAME)
            self.logger.info(f"[{type(self).prefixCls}] SymbolSets assign to groups - {groupsSymbolSetDict}")

            step = 1

            #Creating new userDetails dict and removing admin user from it to skip admin user
            #because admin is getting access to all symbols even if access is denied - CR
            #The below code will be removed once the CR is fixed
            userDetails = dict(commonConstants.USERS_DETAILS_DICT)
            userDetails.pop('administratorUser')

            # Validating access assign to each group via PyTeF client
            for userData in userDetails.values():
                step += 1
                self.logger.newStep(f"Step {step}: Occupying pytef session with {userData['userName']} user of "
                                    f"{userData['group']} group")
                atleaseOneMisMatch = False

                # Defining dictionary of arguments to occupy third party Python client session
                thirdPartyClientArgs = {
                    commonConstants.USER_NAME_KEY: userData["userName"],
                    commonConstants.BASE64_ENC_PASS_KEY: userData["password"],
                }

                # Occupying PyTeF Session with username and password
                if not thirdPrtyClientObj.occupySession(**thirdPartyClientArgs):
                    raise Exception(f"Unable to occupy pytef session with {userData['userName']} user of "
                                    f"{userData['group']} group")

                self.logger.info(f"[{type(self).prefixCls}] Pytef session with {userData['userName']} user of "
                                 f"{userData['group']} group is occupied successfully")

                # Getting symbols and syb-symbols data which is accessible from Pytef client
                step += 1
                self.logger.newStep(f"Step {step}: Get all the Symbols and subSymbols accessible to the "
                                    f"{userData['userName']} via Pytef")

                controllerFamily = self.getControllerFamily()

                userSymbolDetails = thirdPrtyClientObj.getAllSymbolDict(controllerFamily)
                self.logger.info(f"[{type(self).prefixCls}] Symbols and subSymbols read by {userData['userName']} "
                                 f"user from pytef (3rdPartyClient) are - {userSymbolDetails}")
                if not userSymbolDetails:
                    raise Exception("Unable to get symbols dictionary from pytef3rdPartyClient")

                # Validating above read data with data which is assign to the respective user
                step += 1
                self.logger.newStep(f"Step {step}: Compere this accessible symbol and subSymbols from xml file data")

                self.logger.info(f"[{type(self).prefixCls}] SymbolSets assign to {userData['group']} group are - "
                                 f"{groupsSymbolSetDict[userData['group']]}")

                usersSymbolSetsSymbolDict = {}
                for symbolSet in groupsSymbolSetDict[userData["group"]]:

                    symbolsFromXMLEile = plcObj.getSymbolsFromXMLFile(
                        xmlFilePath = self.projectPath,
                        symbolSet = symbolSet,
                        projName = commonConstants.PLC_PROJ_NAME,
                        controllerType = self.configXlsObj.controllerType)

                    for symbol, subSymbols in symbolsFromXMLEile.items():
                        usersSymbolSetsSymbolDict[symbol] = [subSymbol for subSymbol in subSymbols
                                                             if subSymbol != "name"]

                # Logging if Symbols are accessible or not... or any other symbols are accessible
                for symbol, subSymbols in userSymbolDetails.items():
                    if symbol in usersSymbolSetsSymbolDict:
                        self.logger.info(f"[{type(self).prefixCls}] {symbol} Symbol is available in SymbolSet... "
                                         "checking its subSymbols")
                        subSymbolMisMatch = False
                        for subSymbol in subSymbols:
                            if subSymbol not in usersSymbolSetsSymbolDict[symbol]:
                                self.logger.error(f"[{type(self).prefixCls}] {subSymbol} subSymbol is not available "
                                                  "in SymbolSet")
                                subSymbolMisMatch = True

                        if not subSymbolMisMatch:
                            self.logger.info(f"[{type(self).prefixCls}] All subSymbol of {symbol} symbol are also "
                                             "available in SymbolSet")
                        else:
                            atleaseOneMisMatch = True

                    else:
                        self.logger.error(f"[{type(self).prefixCls}] {symbol} - {subSymbols} symbol is not available "
                                          "in SymbolSet")
                        atleaseOneMisMatch = True
                if not atleaseOneMisMatch:
                    self.logger.newStep(f"All symbols and subSymbols for {userData['userName']} user are available "
                                        "in SymbolSet", level = 3)
                else:
                    self.logger.error(f"[{type(self).prefixCls}] Some symbols or subSymbols mis-match "
                                      f"(might not available in SymbolSet) for {userData['userName']} user")
                    atleastOneFail = True
                self.logger.info(f"[{type(self).prefixCls}] Closing Third Party Pytef Session")
                thirdPrtyClientObj.closeSession()
                self.logger.info(f"[{type(self).prefixCls}] Pytef Third Party Session closed successfully")
            return not atleastOneFail

        except Exception:
            self.logger.exception(f"[{type(self).prefixCls}] Exception occurred in verifySymbolAccessUsingPytef()")
        finally:
            self.logger.info(f"[{type(self).prefixCls}] Closing Third Party Pytef Session")
            thirdPrtyClientObj.closeSession()
            self.logger.info(f"[{type(self).prefixCls}] Pytef Third Party Session closed successfully")
        return False

    #-------------------------------------------------------------------------------------------------------------------
    def connectPytefUserWithCertificate(self, plcObj, thirdPrtyClientObj, policy, mode,
                                        userName = None, base64EncryptedPassword = None) -> Any:
        """
        This method is used to check connection from pytef to opc_ua server using certificate
        """
        try:
            # Defining dictionary of arguments to occupy third party Python client session
            thirdPartyClientArgs = {
                commonConstants.USER_NAME_KEY: userName,
                commonConstants.BASE64_ENC_PASS_KEY: base64EncryptedPassword,
                commonConstants.POLICY_KEY: policy,
                commonConstants.MODE_KEY: mode
            }

            # Checking if we are getting 'BadSecurityChecksFailed' error or not
            status = thirdPrtyClientObj.occupySession(**thirdPartyClientArgs)
            badSecurityChecksFailed = thirdPrtyClientObj.badSecurityChecksFailed

            if badSecurityChecksFailed:
                # Got BadSecurityChecksFailed error...
                self.logger.info(f"[{type(self).prefixCls}] Got 'BadSecurityChecksFailed' error...")
                self.logger.info(f"[{type(self).prefixCls}] Moving Pytef certificate from Quarantined certificate "
                                 "to Trused certificate")

                # Moving Pytef certificate from Quarantined certificate to Trused certificate

                certificateName = "PyTeF@" + socket.gethostname()
                plcObj.moveCertificateFromOneFolderToAnotherInPLCD(
                    projName = commonConstants.PLC_PROJ_NAME,
                    moveCertificateFrom = commonConstants.QUARANTINED_CERTIFICATES,
                    moveCertificateTo = commonConstants.TRUSTED_CERTIFICATES,
                    nameOfCertificate = certificateName)

                # Checking if we are able to connect to third party client successfully or not
                status = thirdPrtyClientObj.occupySession(**thirdPartyClientArgs)

                self.logger.info(f"[{type(self).prefixCls}] Closing Pytef session")
                thirdPrtyClientObj.closeSession()
                self.logger.info(f"[{type(self).prefixCls}] Pytef Session closed successfully")
            return status
        finally:
            thirdPrtyClientObj.closeSession()

    #-------------------------------------------------------------------------------------------------------------------
    def getControllerFamily(self) -> str:
        """
        This method is used to get the family of the controller used in the test
        """
        if self.configXlsObj.controllerType.startswith('c5'):
            return 'c500'
        if self.configXlsObj.controllerType.startswith('c4'):
            return 'c400'
        return ''

    #-------------------------------------------------------------------------------------------------------------------
    def isProjectOpen(self) -> str:
        """
        This method is used to check if project is opened
        """

        self.logger.info(f"[{type(self).prefixCls}] Check if project is opened..")

        if not Lib_UserMgmt_ES.PLCD_OBJECT.getMainWindow(header = commonConstants.PLC_PROJ_NAME):
            self.logger.info(f"[{type(self).prefixCls}] Project is not opened.. opening project")
            Lib_UserMgmt_ES.PLCD_OBJECT.OpenPlcProjDoCleanAllAndBuildProject(
                header = self.configXlsObj.plcheader,
                projPath = self.projectPath,
                projName = commonConstants.PLC_PROJ_NAME)

    #-------------------------------------------------------------------------------------------------------------------
    def req_19_Grp_01_test_00_pre(self) -> Any:
        """
        Pre verify access of symbol set group to the users via third party client and validate certificate Handling
        """

        self.pre_setUp()

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def req_19_Grp_01_test_01(self) -> bool:
        """
        - TC1.0 Verify creation of symbol configuration in PLCDesigner

        • Open Symbol configuration tab from devices window (If not found in devices create new one from project)
        • Activate "Support OPC UA Features" and "Enable Symbol Sets"
        • Delete Already available symbolsSets if any (Other than default)
        • Adding 5 symbolSets
        • Building the project
        • Saving and closing PLC project
        • Opening PLC Designer Project, Do Clean all and Build the project
        • Select Controller and Going online
        • Verify all selected symbols in each symbolSets inside the xml files  --> **TC1.0 TestResult**
        """

        testResult = Lib_UserMgmt_ES.PLCD_OBJECT.createAndValidateSymbolSets(
            header = self.configXlsObj.plcheader,
            projPath = self.projectPath,
            projName = commonConstants.PLC_PROJ_NAME,
            ipAddress = self.configXlsObj.controllerIP,
            controllerType = self.configXlsObj.controllerType)

        return testResult

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def req_19_Grp_01_test_02(self) -> bool:
        """
        - TC1.1 Verify creation of user groups and assignment of variables in PLCDesigner

        • Open 'Users and Groups' tab
        • Change mode to synchronize mode
        • Add users
        • Build the project
        • Save and close PLC project
        • Open PLC Designer Project, Do Clean all and Build the project
        • Select Controller and Go online with admin user
        • Verify Successful login --> **TC1.1 TestResult**
        """

        testResult = Lib_UserMgmt_ES.PLCD_OBJECT.createUsers(
            header = self.configXlsObj.plcheader,
            projName = commonConstants.PLC_PROJ_NAME,
            projPath = self.projectPath,
            ipAddress = self.configXlsObj.controllerIP)

        return testResult

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def req_19_Grp_01_test_03(self) -> bool:
        """
        - TC1.2 Verify download of symbol configuration and user groups to controller

        •  Open Users and Groups
        •  Change mode to synchronize mode
        •  Open symbol Rights tab
        •  Change mode to non-synchronize
        •  Load .dsm file from disk
        •  Change mode to synchronize mode and Download editor content to device
        •  Save PLC Project
        •  Go offline
        •  Go online with admin user
        •  Verify Successful login  --> **TC1.2 TestResult**
        """

        testResult = Lib_UserMgmt_ES.PLCD_OBJECT.grantSymbolRightsFromFile(
            dsmFilePath = os.path.join(os.getcwd(), constants.SECURITY_TEST_INPUT_FILES),
            dsmFileName = commonConstants.DEVICE_SYMBOL_MANAGEMENT_FILE_NAME,
            projname = commonConstants.PLC_PROJ_NAME,
            header = self.configXlsObj.plcheader)

        return testResult

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def req_19_Grp_01_test_04(self) -> bool:
        """
        - TC1.3 Verify access of symbol groups and associated variables with the UaExpert client.

        • Get all symbolSets access assign to each groups
        • For each users (AdministratorUser, ServiceUser, DeveloperUser)
        --> 1. Occupy PyTef session \n
        --> 2. Get all the Symbols and subSymbols accessible to that user via Pytef \n
        --> 3. Compare this accessible symbol and subSymbols from xml file data  --> **TC1.3 TestResult**
        """

        Lib_UserMgmt_ES.THIRD_PARTYCLIENT_OBJECT = self.getClientObject(clientType = commonConstants.PYTEF_CLIENT_NAME)

        testResult = self.verifySymbolAccessUsingPytef(thirdPrtyClientObj = Lib_UserMgmt_ES.THIRD_PARTYCLIENT_OBJECT,
                                                       plcObj = Lib_UserMgmt_ES.PLCD_OBJECT)
        return testResult

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def req_19_Grp_01_test_05(self) -> bool:
        """
        - TC1.4 Verify creation of new certificate for encrypted communication on controller

        • Open Security Screen and Select Devices tab on it
        • Click on refresh button to load the data
        • Select controller type in left view and OPC UA Server in the right view
        • Create new certificate
        • Verify if Certificate created or not
        • Save and close PLC Project and restart the controller
        • Open PLC Designer Project, Do Clean all and Build the project
        • Select Controller and Go online and Verify go online PLCD project downloaded successful \
          --> **TC1.4 TestResult**
        """

        plcObj = Lib_UserMgmt_ES.PLCD_OBJECT
        testResult = plcObj.createOpcUaCertificate(projName = commonConstants.PLC_PROJ_NAME,
                                                   header = self.configXlsObj.plcheader,
                                                   controllerType = self.configXlsObj.controllerType)

        if testResult:
            testResult = self.restartController()

        if testResult:
            try:
                self.logger.newStep("Step 7: Opening PLC Designer Project, Doing Clean all and Building the "
                                    "project")
                plcObj.OpenPlcProjDoCleanAllAndBuildProject(header = self.configXlsObj.plcheader,
                                                            projPath = self.projectPath,
                                                            projName = commonConstants.PLC_PROJ_NAME)

                self.logger.newStep("Step 8: Selecting Controller and Going online")
                self.logger.newStep("Selecting Controller", level = 3)
                if not plcObj.selectController(
                        ipAddress = self.configXlsObj.controllerIP,
                        projName = commonConstants.PLC_PROJ_NAME,
                        gatewayIp = self.configXlsObj.controllerIP,
                        userName = commonConstants.USERS_DETAILS_DICT['administratorUser']['userName'],
                        base64Password = commonConstants.USERS_DETAILS_DICT['administratorUser']['password']):
                    raise Exception("Error while selecting controller")

                self.logger.newStep("Going Online", level = 3)
                self.logger.info(f"[{type(self).prefixCls}] Going online with controller : "
                                 f"{self.configXlsObj.controllerIP}")

                if not plcObj.goOnline(
                    userName = commonConstants.USERS_DETAILS_DICT['administratorUser']['userName'],
                    base64EncryptedPassword = commonConstants.USERS_DETAILS_DICT['administratorUser']['password'],
                    projName = constants_opc_ua.PLC_PROJ_NAME
                ):
                    raise Exception("Unable to go online with controller")

            except Exception:
                self.logger.exception(f"[{type(self).prefixCls}] Exception occurred during Opening PLC "
                                      "Designer Project")
                testResult = False

        self.logger.info(f"[{type(self).prefixCls}] Opening Security Screen")
        plcObj.openSecurityScreen()

        self.logger.info(f"[{type(self).prefixCls}] Selecting devices on security screen")
        plcObj.gotoTabInSecurityScreenWindow(tabName = "Devices", mainWindow = None)

        self.logger.info(f"[{type(self).prefixCls}] Clicking refresh button")
        refreshButton = plcObj.getMainWindow(header = commonConstants.PLC_PROJ_NAME)[u'Button']
        refreshButton.set_focus()
        refreshButton.click()

        return testResult

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def req_19_Grp_01_test_06(self) -> bool:
        """
        - TC1.5 Verify encrypted connection to OPC-UA server in c5xx/c4xx via UaExpert for connection type
        "Basic256Sha256 - Sign & Encrypt"

        • Delete Trusted and quarantined certificates
        • Occupy Anonymous Pytef session with certificate having connection type Basic256Sha256 - Sign & Encrypt...
        • Verify rejection of pytef session with BadSecurityChecksFailed error
        • Download PYTEF Certificate to trusted certificate in device
        • Occupy anonymous Pytef connection with certificate having connection type Basic256Sha256 - Sign & Encrypt
        • Verify Successful connection from pytef to opc_ua server using certificate  --> **TC1.5 TestResult**
        """

        self.logger.newStep("Step 1: Deleting Trusted and quarantined certificates")

        plcObj = Lib_UserMgmt_ES.PLCD_OBJECT
        plcObj.deleteCertificatesFromPLCSecurity(projName = commonConstants.PLC_PROJ_NAME,
                                                 listOfTypeOfCertificates = [commonConstants.TRUSTED_CERTIFICATES,
                                                                             commonConstants.QUARANTINED_CERTIFICATES])

        self.logger.newStep("Step 2: Connecting Annonymous Pytef user by downloading PYTEF Certificate "
                            "to trusted certificate in device")
        self.logger.info(f"[{type(self).prefixCls}] Certificate Details: Policy = 'POLICY_BASIC_256_SHA_256', "
                         "mode = 'MODE_SIGN_AND_ENCRYPT'")

        testResult = self.connectPytefUserWithCertificate(
            plcObj = plcObj,
            thirdPrtyClientObj = Lib_UserMgmt_ES.THIRD_PARTYCLIENT_OBJECT,
            policy = Lib_UserMgmt_ES.THIRD_PARTYCLIENT_OBJECT.client.POLICY_BASIC_256_SHA_256,
            mode = Lib_UserMgmt_ES.THIRD_PARTYCLIENT_OBJECT.client.MODE_SIGN_AND_ENCRYPT)

        return testResult

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def req_19_Grp_01_test_07(self) -> bool:
        """
        - TC1.6 Verify encrypted connection to OPC-UA server in c5xx/c4xx via UaExpert for connection type
        "Basic256Sha256 - Sign"

        • Delete Trusted and quarantined certificates
        • Occupy Anonymous Pytef session with certificate having connection type Basic256Sha256 - Sign...
        • Verify rejection of pytef session with BadSecurityChecksFailed error
        • Download PYTEF Certificate to trusted certificate in device
        • Occupy anonymous Pytef connection with certificate having connection type Basic256Sha256 - Sign
        • Verify Successful connection from pytef to opc_ua server using certificate  --> **TC1.6 TestResult**
        """

        self.logger.newStep("Step 1: Deleting Trusted and quarantined certificates")

        plcObj = Lib_UserMgmt_ES.PLCD_OBJECT
        plcObj.deleteCertificatesFromPLCSecurity(projName = commonConstants.PLC_PROJ_NAME,
                                                 listOfTypeOfCertificates = [commonConstants.TRUSTED_CERTIFICATES,
                                                                             commonConstants.QUARANTINED_CERTIFICATES])

        self.logger.newStep("Step 2: Connecting Annonymous Pytef user by downloading PYTEF Certificate "
                            "to trusted certificate in device")
        self.logger.info(f"[{type(self).prefixCls}] Certificate Details: Policy = 'POLICY_BASIC_256_SHA_256', "
                         "mode = 'MODE_SIGN'")

        testResult = self.connectPytefUserWithCertificate(
            plcObj = plcObj,
            thirdPrtyClientObj = Lib_UserMgmt_ES.THIRD_PARTYCLIENT_OBJECT,
            policy = Lib_UserMgmt_ES.THIRD_PARTYCLIENT_OBJECT.client.POLICY_BASIC_256_SHA_256,
            mode = Lib_UserMgmt_ES.THIRD_PARTYCLIENT_OBJECT.client.MODE_SIGN)

        return testResult

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def req_19_Grp_01_test_08(self) -> bool:
        """
        - TC1.7 Verify encrypted connection to OPC-UA server in c5xx/c4xx via UaExpert for each user

        • For each user
        --> 1. Delete Trusted and quarantined certificates \n
        --> 2. Occupy Pytef session (with correct username and password) with certificate having connection type \
            Basic256Sha256 - Sign & Encrypt... \n
        --> 3. Verify rejection of pytef session with BadSecurityChecksFailed error \n
        --> 4. Download PYTEF Certificate to trusted certificate in device \n
        --> 5. Occupy Pytef session (with correct username and password) with certificate having connection type \
            Basic256Sha256 - Sign & Encrypt \n
        --> 6. Verify Successful connection from pytef to opc_ua server using certificate  --> \
            **TC1.7 TestResult** \n
        --> 7. Delete Trusted and quarantined certificates \n
        --> 8. Occupy Pytef session (with correct username and password) with certificate having connection type \
            Basic256Sha256 - Sign... \n
        --> 9. Verify rejection of pytef session with BadSecurityChecksFailed error \n
        --> 10. Download PYTEF Certificate to trusted certificate in device \n
        --> 11. Occupy Pytef session (with correct username and password) with certificate having connection type \
            Basic256Sha256 - Sign \n
        --> 12. Verify Successful connection from pytef to opc_ua server using certificate  --> **TC1.7 TestResult**
        """

        testResult = True
        plcObj = Lib_UserMgmt_ES.PLCD_OBJECT
        Lib_UserMgmt_ES.THIRD_PARTYCLIENT_OBJECT = self.getClientObject(clientType = commonConstants.PYTEF_CLIENT_NAME)

        step = 0
        for users in commonConstants.USERS_DETAILS_DICT.values():
            step += 1
            self.logger.newStep(f"Step {step}: Validating Pytef session with certificates for user - "
                                f"{users['userName']}")

            self.logger.newStep("Deleting Trusted and quarantined certificates", level = 3)
            plcObj.deleteCertificatesFromPLCSecurity(
                projName = commonConstants.PLC_PROJ_NAME,
                listOfTypeOfCertificates = [commonConstants.TRUSTED_CERTIFICATES,
                                            commonConstants.QUARANTINED_CERTIFICATES])

            self.logger.newStep("Certificate Details: Policy = 'POLICY_BASIC_256_SHA_256', mode = "
                                "'MODE_SIGN_AND_ENCRYPT'", level = 3)

            result = self.connectPytefUserWithCertificate(
                plcObj = plcObj,
                thirdPrtyClientObj = Lib_UserMgmt_ES.THIRD_PARTYCLIENT_OBJECT,
                userName = users["userName"],
                base64EncryptedPassword = users["password"],
                policy = Lib_UserMgmt_ES.THIRD_PARTYCLIENT_OBJECT.client.POLICY_BASIC_256_SHA_256,
                mode = Lib_UserMgmt_ES.THIRD_PARTYCLIENT_OBJECT.client.MODE_SIGN_AND_ENCRYPT)
            if not result:
                self.logger.error(f"[{type(self).prefixCls}] Failed to occupy pytef session with certificate "
                                  f"(Policy = 'POLICY_BASIC_256_SHA_256', mode = 'MODE_SIGN_AND_ENCRYPT') for user "
                                  f"{users['userName']} of {users['group']} group")
            testResult = testResult and result

            self.logger.newStep("Deleting Trusted and quarantined certificates", level = 3)
            plcObj.deleteCertificatesFromPLCSecurity(
                projName = commonConstants.PLC_PROJ_NAME,
                listOfTypeOfCertificates = [commonConstants.TRUSTED_CERTIFICATES,
                                            commonConstants.QUARANTINED_CERTIFICATES])

            self.logger.newStep("Certificate Details: Policy = 'POLICY_BASIC_256_SHA_256', mode = 'MODE_SIGN'",
                                level = 3)
            result = self.connectPytefUserWithCertificate(
                plcObj = plcObj,
                thirdPrtyClientObj = Lib_UserMgmt_ES.THIRD_PARTYCLIENT_OBJECT,
                userName = users["userName"],
                base64EncryptedPassword = users["password"],
                policy = Lib_UserMgmt_ES.THIRD_PARTYCLIENT_OBJECT.client.POLICY_BASIC_256_SHA_256,
                mode = Lib_UserMgmt_ES.THIRD_PARTYCLIENT_OBJECT.client.MODE_SIGN)

            if not result:
                self.logger.error(f"[{type(self).prefixCls}] Failed to occupy pytef session with certificate "
                                  f"(Policy = 'POLICY_BASIC_256_SHA_256', mode = 'MODE_SIGN') for user "
                                  f"{users['userName']} of {users['group']} group")
            testResult = testResult and result

        return testResult

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def req_19_Grp_01_test_09(self) -> bool:
        """
        - TC1.8 Verify creation of user administration files on the SD card in the path

        • Delete user management files from controller using paramiko
        • restart controller
        • verify user login disabled  --> **TC1.8 TestResult**
        """

        self.logger.newStep("1. Deleting User management files", level = 3)
        testResult = deleteUserManagementFiles(logger = self.logger,
                                               ipAddress = self.configXlsObj.controllerIP)

        self.logger.newStep("2. Restarting controller", level = 3)
        self.restartController()

        # Handle No connection to the device popup if appeared
        plcObj = Lib_UserMgmt_ES.PLCD_OBJECT
        plcObj.handlePLCConnectionLost(header = self.configXlsObj.plcheader)

        if testResult:
            self.logger.newStep("3. Check if user management is enabled")
            if plcObj.checkIfUserManagementEnabled(projName = commonConstants.PLC_PROJ_NAME):
                self.logger.error(f"[{type(self).prefixCls}] User management is still enabled")
                testResult = False

        Lib_UserMgmt_ES.lastTestPassed = testResult

        return testResult

    #-------------------------------------------------------------------------------------------------------------------
    def req_19_Grp_01_test_99_post(self) -> Any:
        """
        Post verify access of symbol set group to the usrs via third party client and validate certificate Handling
        """

        self.isProjectOpen()

        if Lib_UserMgmt_ES.lastTestPassed:
            self.logger.info(f"[{type(self).prefixCls}] Skipping deletion of user management files as it is "
                             "deleted successfully in the previous testcase")
        else:
            self.logger.info(f"[{type(self).prefixCls}] Deleting User management files")
            if not deleteUserManagementFiles(logger = self.logger,
                                             ipAddress = self.configXlsObj.controllerIP):
                self.logger.warning(f"[{type(self).prefixCls}] Failed to delete user management files")
            else:
                self.logger.info(f"[{type(self).prefixCls}] Restarting controller")
                if not self.restartController():
                    self.logger.warning(f"[{type(self).prefixCls}] Failed to restart controller")
                else:
                    # Handle No connection to the device popup if appeared
                    Lib_UserMgmt_ES.PLCD_OBJECT.handlePLCConnectionLost(header = self.configXlsObj.plcheader)

    #-------------------------------------------------------------------------------------------------------------------
    def req_23_Grp_01_test_00_pre(self) -> Any:
        """
        Pre verify connection to controller with Anonymous user enabled and user management Deactivated
        """

        self.pre_setUp()

        self.logger.newStep(f"[{type(self).prefixCls}] PREREQUISITE Steps")
        # Ensuring that User management is not activated
        self.logger.newStep(f"[{type(self).prefixCls}] Step 1. Ensuring that user management is not activated",
                            level = 3)
        if Lib_UserMgmt_ES.PLCD_OBJECT.checkIfUserManagementEnabled(
                projName = commonConstants.PLC_PROJ_NAME):
            # Failing the test as user management is activated
            raise Exception("User Management is activated")

        # Third party client 1 object
        self.logger.newStep(f"[{type(self).prefixCls}] Step 2. Occupy dummy 3rd party session", level = 3)
        Lib_OpcUa_Base.dummy3rdPrtyPyClientObj = self.getClientObject(
            clientType = commonConstants.PYTEF_CLIENT_NAME)
        if not self.occupySession(clientObj = Lib_OpcUa_Base.dummy3rdPrtyPyClientObj):
            raise Exception("Failed to occupy dummy 3rd party session")

        self.logger.newStep(f"[{type(self).prefixCls}] PREREQUISITE Completed")

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def req_23_Grp_01_test_01(self) -> bool:

        easyStarterObj = None

        try:
            # Easy Starter Object
            easyStarterObj = self.getClientObject(clientType = commonConstants.EASY_STARTER_NAME)
            # Occupy EasyStarter Session
            self.logger.newStep("Verifying Easy Starter Anonymous connection")
            self.occupySession(clientObj = easyStarterObj)

            testResult = self.validateSessionDetails(lstOfActiveClientObjs = [easyStarterObj])

            # Closing EasyStarter session
            self.closeSessionAndValidate(clientObj = easyStarterObj)

            return testResult
        except Exception:
            if easyStarterObj:
                easyStarterObj.closeSession()

            return False

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def req_23_Grp_01_test_02(self) -> bool:

        appLoaderObj = None

        try:
            # App Loader Object
            appLoaderObj = self.getClientObject(clientType = commonConstants.APPLICATION_LOADER_NAME)
            # Occupy Application Loader Session
            self.logger.newStep("Verifying Application Loader Anonymous connection")
            self.occupySession(clientObj = appLoaderObj)

            testResult = self.validateSessionDetails(lstOfActiveClientObjs = [appLoaderObj])

            # Closing App Loader session
            self.closeSessionAndValidate(clientObj = appLoaderObj)

            return testResult
        except Exception:
            if appLoaderObj:
                appLoaderObj.closeSession()

            return False

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def req_23_Grp_01_test_03(self) -> bool:

        firmwareLoaderObj = None

        try:
            # Firmware Loader Object
            firmwareLoaderObj = self.getClientObject(clientType = commonConstants.FIRMWARE_LOADER_NAME)

            # Firmware loader session
            self.logger.newStep("Verifying Firmware Loader Anonymous connection")
            self.occupySession(clientObj = firmwareLoaderObj)
            testResult = self.validateSessionDetails(lstOfActiveClientObjs = [firmwareLoaderObj])

            if not self.waitForFWLoaderSessionToClose(firmwareLoaderObj = firmwareLoaderObj):
                testResult = False

            return testResult
        except Exception:
            if firmwareLoaderObj:
                firmwareLoaderObj.closeSession()

            return False

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def req_23_Grp_01_test_04(self) -> bool:

        easyUiDesignerObj = None

        try:
            # Easy Ui Designer Object
            easyUiDesignerObj = self.getClientObject(clientType = commonConstants.EASY_UI_DESIGNER_NAME)

            self.logger.newStep("Verifying Easy Ui Designer Anonymous connection")
            # EUD sessions
            self.occupySession(clientObj = easyUiDesignerObj)
            testResult = self.validateSessionDetails(lstOfActiveClientObjs = [easyUiDesignerObj])

            # Close EUD session
            self.closeSessionAndValidate(clientObj = easyUiDesignerObj)

            return testResult
        except Exception:
            if easyUiDesignerObj:
                easyUiDesignerObj.closeSession()

            return False

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def req_23_Grp_01_test_05(self) -> bool:

        thirdPrtyClientObj2 = None

        try:
            # Third party client object
            thirdPrtyClientObj2 = self.getClientObject(clientType = commonConstants.PYTEF_CLIENT_NAME)

            # Occupy third party session
            self.logger.newStep("Verifying Third Party Pytef Anonymous connection")
            self.occupySession(clientObj = thirdPrtyClientObj2)

            testResult = self.validateSessionDetails(lstOfActiveClientObjs = [thirdPrtyClientObj2])

            # Close Third party client session
            self.closeSessionAndValidate(clientObj = thirdPrtyClientObj2)

            return testResult
        except Exception:
            if thirdPrtyClientObj2:
                thirdPrtyClientObj2.closeSession()

            return False

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def req_23_Grp_01_test_06(self) -> bool:
        try:
            # x510 object
            x510Obj = self.getClientObject(clientType = commonConstants.X510_NAME)

            # Occupying x510 Session
            self.occupySession(clientObj = x510Obj)
            self.logger.newStep("Verifying x510 Anonymous connection")
            testResult = self.validateSessionDetails(lstOfActiveClientObjs = [x510Obj])
            # Setting numeric id of x510 session again back to 0 if session was not occupied
            if not testResult:
                x510Obj.numericId = 0

            # Close Third party client session
            self.closeSessionAndValidate(clientObj = x510Obj)

            return testResult
        except Exception:
            if x510Obj:
                x510Obj.closeSession()

            return False

    #-------------------------------------------------------------------------------------------------------------------
    def req_23_Grp_01_test_99_post(self) -> Any:
        if Lib_OpcUa_Base.dummy3rdPrtyPyClientObj:
            Lib_OpcUa_Base.dummy3rdPrtyPyClientObj.closeSession()

    #-------------------------------------------------------------------------------------------------------------------
    def req_23_Grp_02_test_00_pre(self) -> Any:
        """
        Pre verify connection to controller with Anonymous user enabled and user management activated
        """

        self.pre_setUp()

        self.logger.info(f"[{type(self).prefixCls}] PREREQUISITE Steps".format())

        # Activating user management
        self.logger.newStep(f"[{type(self).prefixCls}] Step 1. Activate user management and add users", level = 3)
        if not Lib_UserMgmt_ES.PLCD_OBJECT.activateUsrMgmtAndAddAdminUsr(
                projName = commonConstants.PLC_PROJ_NAME,
                adminData = commonConstants.USERS_DETAILS_DICT_SECURITY_TEST['administratorUser']):
            raise Exception("User Management is not activated")

        # Add users
        usersAddedStatus = Lib_UserMgmt_ES.PLCD_OBJECT.addUsersInUserAndGroups(
            userData = commonConstants.USERS_DETAILS_DICT_SECURITY_TEST, projName = commonConstants.PLC_PROJ_NAME)
        if not usersAddedStatus:
            raise Exception("Failed to add users in user management")

        # Stopping sync mode in Users and Groups
        self.logger.newStep(f"[{type(self).prefixCls}] Step 2. Stop Synchronization mode", level = 3)
        if not Lib_UserMgmt_ES.PLCD_OBJECT.stopSyncModeInUsersAndGroups():
            raise Exception("Failed to stop sync mode in Users and Groups Tab")

        # Setting Modify, View, Execute Access to EasyUi Interface
        self.logger.newStep(f"[{type(self).prefixCls}] Step 3. Set Modify, View, Execute Access Rights to "
                            "EasyUi Interface", level = 3)
        if not Lib_UserMgmt_ES.PLCD_OBJECT.grantAccessRightsFromFile(
                drmFileName = constants.DEVICE_RIGHT_MANAGEMENT_FILE_NAME,
                drmFilePath = constants.SECURITY_TEST_INPUT_FILES,
                projname = commonConstants.PLC_PROJ_NAME):
            raise Exception("Access Rights not set for EasyUi Interface")

        # Stop sync mode
        self.logger.newStep(f"[{type(self).prefixCls}] Step 4. Stop sync mode in Access Rights tab", level = 3)
        if not Lib_UserMgmt_ES.PLCD_OBJECT.stopSyncModeInAccessRights():
            raise Exception("Failed to stop sync mode")

        # Reboot controller
        self.logger.newStep(f"[{type(self).prefixCls}] Step 5. Reboot Controller", level = 3)
        if not self.restartController():
            raise Exception("Failed to reboot the controller")

        self.logger.info(f"[{type(self).prefixCls}] Waiting for OPC UA Server to restart")
        userSleep(60)

        # Third party client 1 object
        self.logger.newStep(f"[{type(self).prefixCls}] Step 6. Occupy dummy 3rd party session", level = 3)
        Lib_OpcUa_Base.dummy3rdPrtyPyClientObj = self.getClientObject(clientType = commonConstants.PYTEF_CLIENT_NAME)
        if not self.occupySession(clientObj = Lib_OpcUa_Base.dummy3rdPrtyPyClientObj):
            raise Exception("Failed to occupy dummy 3rd party session")

        self.logger.info(f"[{type(self).prefixCls}] PREREQUISITE Completed".format())

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def req_23_Grp_02_test_01(self) -> bool:

        uaExpertClientObj = None

        try:
            # Ua Expert Object
            uaExpertClientObj = self.getClientObject(clientType = commonConstants.UA_EXPERT_NAME)

            # Ua Expert sessions
            self.logger.newStep("1. Verifying Connection of Ua Expert Anonymous Session")
            self.occupySession(clientObj = uaExpertClientObj)
            testResult = self.validateSessionDetails(lstOfActiveClientObjs = [uaExpertClientObj])
            if testResult:
                self.logger.newStep("Successfully verified Ua Expert connection for Anonymous session")
            else:
                self.logger.error(f"[{type(self).prefixCls}] Ua Expert connection for Anonymous session failed")

            # Verifying Ua Expert session with valid users of different groups
            self.logger.newStep("2. Verifying Ua Expert session with valid users of different groups")

            # Defining list of groups for which the connection is expected
            connExpectedForGrpsLi = ["Administrator", "Engineering", "EasyUi", "Watch", "Service", "Developer"]

            # Iterating and verifying connection for every user data (stored in commonConstants)
            for _ , userData in commonConstants.USERS_DETAILS_DICT_SECURITY_TEST.items():
                self.logger.newStep(f"[{type(self).prefixCls}] Verifying Ua Expert connection for user of "
                                    f"{userData['group']} group", level = 3)

                connectionExpectedFlag = False
                if userData['group'] in connExpectedForGrpsLi:
                    connectionExpectedFlag = True

                verificationResult = self.swtchUsrAndValConnection(
                    clientObj = uaExpertClientObj, userName = userData['userName'],
                    baseEncPassword = userData['password'],
                    connectionExpectedFlag = connectionExpectedFlag)
                testResult = testResult and verificationResult

            # Closing Ua Expert tool session
            self.closeSessionAndValidate(clientObj = uaExpertClientObj)

            return testResult
        except Exception:
            if uaExpertClientObj:
                uaExpertClientObj.closeSession()

            return False

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def req_23_Grp_02_test_02(self) -> bool:

        easyStarterObj = None

        try:
            # EasyStarter object
            easyStarterObj = self.getClientObject(clientType = commonConstants.EASY_STARTER_NAME)

            # Easy Starter sessions
            self.logger.newStep("1. Verifying Easy Starter Anonymous Session")
            self.occupySession(clientObj = easyStarterObj)
            testResult = self.validateSessionDetails(lstOfActiveClientObjs = [easyStarterObj])
            if testResult:
                self.logger.newStep("Successfully verified Easy Starter connection for Anonymous session")
            else:
                self.logger.error(f"[{type(self).prefixCls}] Easy Starter connection for Anonymous session failed")

            # Verifying EasyStarter session with valid users of different groups
            self.logger.newStep("2. Verifying EasyStarter session with valid users of different groups")

            # Defining list of groups for which the connection is expected
            connExpectedForGrpsLi = ["Administrator", "Engineering"]

            # Iterating and verifying connection for every user data (stored in commonConstants)
            for _ , userData in commonConstants.USERS_DETAILS_DICT_SECURITY_TEST.items():
                self.logger.newStep(f"[{type(self).prefixCls}] Verifying Easy Starter connection for user of "
                                    f"{userData['group']} group", level = 3)

                connectionExpectedFlag = False
                if userData['group'] in connExpectedForGrpsLi:
                    connectionExpectedFlag = True

                verificationResult = self.swtchUsrAndValConnection(
                    clientObj = easyStarterObj, userName = userData['userName'],
                    baseEncPassword = userData['password'], connectionExpectedFlag = connectionExpectedFlag)

                testResult = testResult and verificationResult

            # Closing Easy Starter session
            self.closeSessionAndValidate(clientObj = easyStarterObj)

            return testResult
        except Exception:
            if easyStarterObj:
                easyStarterObj.closeSession()

            return False

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def req_23_Grp_02_test_03(self) -> bool:

        appLoaderObj = None

        try:
            # Application Loader object
            appLoaderObj = self.getClientObject(clientType = commonConstants.APPLICATION_LOADER_NAME)

            # Verifying Application Loader session as anonymous user
            self.logger.newStep("1. Verifying Application Loader session as anonymous user")
            self.occupySession(clientObj = appLoaderObj)
            testResult = self.validateSessionDetails(lstOfActiveClientObjs = [appLoaderObj])
            if testResult:
                self.logger.newStep("Successfully verified Application Loader connection for Anonymous session")
            else:
                self.logger.error(f"[{type(self).prefixCls}] Application Loader connection for Anonymous session "
                                  "failed")

            # Verifying Application Loader session with valid users of different groups
            self.logger.newStep("2. Verifying Application Loader session with valid users of different groups")

            # Defining list of groups for which the connection is expected
            connExpectedForGrpsLi = ["Administrator", "Engineering"]

            # Iterating and verifying connection for every user data (stored in commonConstants)
            for _ , userData in commonConstants.USERS_DETAILS_DICT_SECURITY_TEST.items():
                self.logger.newStep(f"[{type(self).prefixCls}] Verifying Application Loader connection for user of "
                                    f"{userData['group']} group", level = 3)

                connectionExpectedFlag = False
                if userData['group'] in connExpectedForGrpsLi:
                    connectionExpectedFlag = True

                verificationResult = self.swtchUsrAndValConnection(
                    clientObj = appLoaderObj, userName = userData['userName'],
                    baseEncPassword = userData['password'], connectionExpectedFlag = connectionExpectedFlag)

                testResult = testResult and verificationResult

            # Closing Application Loader session
            self.closeSessionAndValidate(clientObj = appLoaderObj)

            return testResult
        except Exception:
            if appLoaderObj:
                appLoaderObj.closeSession()

            return False

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def req_23_Grp_02_test_04(self) -> bool:

        firmwareLoaderObj = None

        try:
            # Firmware Loader object
            firmwareLoaderObj = self.getClientObject(clientType = commonConstants.FIRMWARE_LOADER_NAME)

            # Verifying Firmware Loader session as anonymous user
            self.logger.newStep("1. Verifying Firmware Loader session as anonymous user")
            self.occupySession(clientObj = firmwareLoaderObj)
            testResult = self.validateSessionDetails(lstOfActiveClientObjs = [firmwareLoaderObj])
            if testResult:
                self.logger.newStep("Successfully verified Firmware Loader connection for Anonymous session")
            else:
                self.logger.error(f"[{type(self).prefixCls}] Firmware Loader connection for Anonymous session failed")

            if not self.waitForFWLoaderSessionToClose(firmwareLoaderObj = firmwareLoaderObj):
                testResult = False

            # Verifying Firmware Loader session with valid users of different groups
            self.logger.newStep("2. Verifying Firmware Loader session with valid users of different groups")

            # Defining list of groups for which the connection is expected
            connExpectedForGrpsLi = ["Administrator", "Engineering"]

            # Iterating and verifying connection for every user data (stored in commonConstants)
            for _ , userData in commonConstants.USERS_DETAILS_DICT_SECURITY_TEST.items():
                self.logger.newStep(f"[{type(self).prefixCls}] Verifying FirmwareLoader connection for user of "
                                    f"{userData['group']} group", level = 3)

                connectionExpectedFlag = False
                if userData['group'] in connExpectedForGrpsLi:
                    connectionExpectedFlag = True

                verificationResult = self.swtchUsrAndValConnection(
                    clientObj = firmwareLoaderObj, userName = userData['userName'],
                    baseEncPassword = userData['password'], connectionExpectedFlag = connectionExpectedFlag)

                if not self.waitForFWLoaderSessionToClose(firmwareLoaderObj = firmwareLoaderObj):
                    testResult = False

                testResult = testResult and verificationResult

                return testResult
        except Exception:
            if firmwareLoaderObj:
                firmwareLoaderObj.closeSession()

            return False

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def req_23_Grp_02_test_05(self) -> bool:

        easyUiDesignerObj = None

        try:
            # EasyUiDesigner object
            easyUiDesignerObj = self.getClientObject(clientType = commonConstants.EASY_UI_DESIGNER_NAME)

            # Occupying Easy Ui Session
            self.occupySession(clientObj = easyUiDesignerObj)

            # Easy ui Designer sessions
            self.logger.newStep("1. Verifying Easy ui Designer Session as Anonymous user")
            # switchUserArgs
            swtchUserArgs = {commonConstants.USER_NAME_KEY: None,
                             commonConstants.BASE64_ENC_PASS_KEY: None}
            if easyUiDesignerObj.switchUser(**swtchUserArgs):
                # Updating numeric id for easy ui designer if switch user is successfull
                easyUiDesignerObj.numericId = Lib_OpcUa_Base.dummy3rdPrtyPyClientObj.getNumericId(index = -1)
            testResult = self.validateSessionDetails(lstOfActiveClientObjs = [easyUiDesignerObj])
            if testResult:
                self.logger.newStep("Successfully verified Easy ui Designer connection for Anonymous session")
            else:
                self.logger.error(f"[{type(self).prefixCls}] Easy ui Designer connection for Anonymous session failed")

            # Defining list of groups for which the connection is expected
            connExpectedForGrpsLi = ["Administrator", "EasyUi", "Watch", "Service", "Developer"]

            # Verifying EasyUiDesigner session with valid users of different groups
            self.logger.newStep("2. Verifying EasyUiDesigner session with valid users of different groups")

            # Iterating and verifying connection for every user data (stored in commonConstants)
            for _ , userData in commonConstants.USERS_DETAILS_DICT_SECURITY_TEST.items():
                connectionExpectedFlag = False
                self.logger.newStep(f"[{type(self).prefixCls}] Verifying connection Easy Ui Desginer connection "
                                    f"for user of {userData['group']} group", level = 3)

                if userData['group'] in connExpectedForGrpsLi:
                    connectionExpectedFlag = True

                verificationResult = self.swtchUsrAndValConnection(
                    clientObj = easyUiDesignerObj, userName = userData['userName'],
                    baseEncPassword = userData['password'], connectionExpectedFlag = connectionExpectedFlag)

                testResult = testResult and verificationResult

            # Closing Easy Ui Designer session
            self.closeSessionAndValidate(clientObj = easyUiDesignerObj)

            return testResult
        except Exception:
            if easyUiDesignerObj:
                easyUiDesignerObj.closeSession()

            return False

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def req_23_Grp_02_test_06(self) -> bool:

        thirdPrtyClientObj = None

        try:
            # Third party client object
            thirdPrtyClientObj = self.getClientObject(clientType = commonConstants.PYTEF_CLIENT_NAME)

            # Verifying Third party client session as anonymous user
            self.logger.newStep("1.  Verifying Third party python client session as anonymous user")
            self.occupySession(clientObj = thirdPrtyClientObj)
            testResult = self.validateSessionDetails(lstOfActiveClientObjs = [thirdPrtyClientObj])
            if testResult:
                self.logger.newStep("Successfully verified Third party python client connection for Anonymous session")
            else:
                self.logger.error(f"[{type(self).prefixCls}] Third party python client connection for Anonymous "
                                  "session failed")

            # Defining list of groups for which the connection is expected
            connExpectedForGrpsLi = ["Administrator", "Engineering", "EasyUi", "Watch", "Service", "Developer"]

            # Verifying Third party client session with valid users of different groups
            self.logger.newStep("2. Verifying thirdPrtyClientObj session with valid users of different groups")

            # Iterating and verifying connection for every user data (stored in commonConstants)
            for _ , userData in commonConstants.USERS_DETAILS_DICT_SECURITY_TEST.items():
                self.logger.newStep(f"[{type(self).prefixCls}] Verifying third party python connection for user of "
                                    f"{userData['group']} group", level = 3)

                connectionExpectedFlag = False
                if userData['group'] in connExpectedForGrpsLi:
                    connectionExpectedFlag = True

                verificationResult = self.swtchUsrAndValConnection(
                    clientObj = thirdPrtyClientObj, userName = userData['userName'],
                    baseEncPassword = userData['password'], connectionExpectedFlag = connectionExpectedFlag)

                testResult = testResult and verificationResult

            # Closing Third party python session
            self.closeSessionAndValidate(clientObj = thirdPrtyClientObj)

            return testResult
        except Exception:
            if thirdPrtyClientObj:
                thirdPrtyClientObj.closeSession()

            return False

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def req_23_Grp_02_test_07(self) -> bool:

        self.testCase.skip("The testcase for x510 is skipped as a issue is observed with x510 session due to a reason "
                           "where connection is expected to be rejected when x510 occupies about 8 sessions")

        x510Obj = None

        try:
            #
            # This testcase for x510 is commented as a issue is observed with x510 session
            # i.e In the cases where connection is expected to be rejected.. x510 occupies about 8 sessions
            #
            #
            # x510 object
            x510Obj = self.getClientObject(clientType = commonConstants.X510_NAME)

            # Verifying X510 session as anonymous user
            self.logger.newStep("1.  Verifying x510 session as anonymous user")
            self.occupySession(clientObj = x510Obj)
            testResult = self.validateSessionDetails(lstOfActiveClientObjs = [x510Obj])
            if testResult:
                self.logger.newStep("Successfully verified x510 connection for Anonymous session")
            else:
                self.logger.error(f"[{type(self).prefixCls}] x510 connection for Anonymous session failed")

            # Defining list of groups for which the connection is expected
            connExpectedForGrpsLi = ["Administrator", "Developer", "Engineering", "EasyUi", "Watch", "Service"]

            # Verifying Third party client session with valid users of different groups
            self.logger.newStep("2. Verifying x510 session with valid users of different groups")

            # Iterating and verifying connection for every user data (stored in commonConstants)
            for _ , userData in commonConstants.USERS_DETAILS_DICT_SECURITY_TEST.items():
                connectionExpectedFlag = False
                self.logger.newStep(f"[{type(self).prefixCls}] Verifying x510 connection for user of "
                                    f"{userData['group']} group", level = 3)

                if userData['group'] in connExpectedForGrpsLi:
                    connectionExpectedFlag = True

                verificationResult = self.swtchUsrAndValConnection(
                    clientObj = x510Obj, userName = userData['userName'],
                    baseEncPassword = userData['password'], connectionExpectedFlag = connectionExpectedFlag)
                if not verificationResult:
                    x510Obj.closeSession()
                    # Waiting for 2 min for x510Obj to close session
                    userSleep(120)

                testResult = testResult and verificationResult

            # Closing x510 session
            self.closeSessionAndValidate(clientObj = x510Obj)

            return testResult
        except Exception:
            if x510Obj:
                x510Obj.closeSession()

            return False

    #-------------------------------------------------------------------------------------------------------------------
    def req_23_Grp_02_test_99_post(self) -> Any:
        if Lib_OpcUa_Base.dummy3rdPrtyPyClientObj:
            Lib_OpcUa_Base.dummy3rdPrtyPyClientObj.closeSession()

    #-------------------------------------------------------------------------------------------------------------------
    def req_23_Grp_03_test_00_pre(self) -> Any:
        """
        Pre verify connection to controller with Anonymous user disabled and user management activated
        """

        self.pre_setUp()

        self.logger.info(f"[{type(self).prefixCls}] PREREQUISITE Steps")

        # Activating user management
        self.logger.newStep(f"[{type(self).prefixCls}] Step 1. Activating user management and adding users",
                            level = 3)
        if not Lib_UserMgmt_ES.PLCD_OBJECT.activateUsrMgmtAndAddAdminUsr(
                projName = commonConstants.PLC_PROJ_NAME,
                adminData = commonConstants.USERS_DETAILS_DICT_SECURITY_TEST['administratorUser']):
            raise Exception("User Management is not activated")

        # Add users
        usersAddedStatus = Lib_UserMgmt_ES.PLCD_OBJECT.addUsersInUserAndGroups(
            userData = commonConstants.USERS_DETAILS_DICT_SECURITY_TEST, projName = commonConstants.PLC_PROJ_NAME)
        if not usersAddedStatus:
            raise Exception("Failed to add users in user management")

        # Stopping sync mode in Users and Groups
        self.logger.newStep(f"[{type(self).prefixCls}] Step 2. Stop Synchronization mode", level = 3)
        if not Lib_UserMgmt_ES.PLCD_OBJECT.stopSyncModeInUsersAndGroups():
            raise Exception("Failed to stop sync mode in Users and Groups Tab")

        # Setting Modify, View, Execute Access to EasyUi Interface
        self.logger.newStep(f"[{type(self).prefixCls}] Step 3. Setting Modify, View, Execute Access to EasyUi "
                            "Interface", level = 3)
        if not Lib_UserMgmt_ES.PLCD_OBJECT.grantAccessRightsFromFile(
                drmFileName = constants.DEVICE_RIGHT_MANAGEMENT_FILE_NAME,
                drmFilePath = constants.SECURITY_TEST_INPUT_FILES,
                projname = commonConstants.PLC_PROJ_NAME):
            raise Exception("Access Rights not set for EasyUi Interface")

        # Stop sync mode
        self.logger.newStep(f"[{type(self).prefixCls}] Step 4. Stop Synchronization mode in Access Rights tab",
                            level = 3)
        if not Lib_UserMgmt_ES.PLCD_OBJECT.stopSyncModeInAccessRights():
            raise Exception("Failed to stop sync mode")

        self.logger.newStep(f"[{type(self).prefixCls}] Step 5. Disabling 'Anonymous user login'", level = 3)
        if not Lib_UserMgmt_ES.PLCD_OBJECT.enableOrDisableAnonymousUserLogin(
                projName = commonConstants.PLC_PROJ_NAME, disableFlag = True):
            raise Exception("Failed to disable 'Anonymous user login")

        # Reboot controller
        self.logger.newStep(f"[{type(self).prefixCls}] Step 6. Reboot Controller", level = 3)
        if not self.restartController():
            raise Exception("Failed to reboot the controller")

        self.logger.info("Waiting for 30 secs, for OPC Ua Server to restart before connection with Pytef Client")
        userSleep(60)

        # Third party client 1 object
        self.logger.newStep(f"[{type(self).prefixCls}] Step 7. Occupying dummy 3rd party session", level = 3)
        Lib_OpcUa_Base.dummy3rdPrtyPyClientObj = self.getClientObject(clientType = commonConstants.PYTEF_CLIENT_NAME)

        # Connecting dummy 3rd party client using username
        if not self.occupySession(
                clientObj = Lib_OpcUa_Base.dummy3rdPrtyPyClientObj,
                userName = commonConstants.USERS_DETAILS_DICT_SECURITY_TEST['administratorUser']['userName'],
                base64EncryptedPassword= commonConstants.USERS_DETAILS_DICT_SECURITY_TEST[
                    'administratorUser']['password']):
            self.logger.info("Waiting 5 sec and trying again")
            userSleep(5)
            if not self.occupySession(
                    clientObj = Lib_OpcUa_Base.dummy3rdPrtyPyClientObj,
                    userName = commonConstants.USERS_DETAILS_DICT_SECURITY_TEST['administratorUser']['userName'],
                    base64EncryptedPassword= commonConstants.USERS_DETAILS_DICT_SECURITY_TEST[
                        'administratorUser']['password']):

                raise Exception("Failed to occupy dummy 3rd party client as Admin user")

        self.logger.info(f"[{type(self).prefixCls}] PREREQUISITE Completed".format())

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def req_23_Grp_03_test_01(self) -> bool:

        uaExpertClientObj = None

        try:
            # Ua Expert Object
            uaExpertClientObj = self.getClientObject(clientType = commonConstants.UA_EXPERT_NAME)

            # Ua Expert sessions
            self.logger.newStep("1.  Verifying Rejection of Ua Expert Anonymous Session")
            self.occupySession(clientObj = uaExpertClientObj)
            testResult = self.validateSessionDetails(lstOfActiveClientObjs = [])
            if testResult:
                self.logger.newStep("Successfully verified rejection of Ua Expert session for Anonymous user")
            else:
                self.logger.error(f"[{type(self).prefixCls}] Rejection for Ua Expert session failed ")

            # Verifying Ua Expert session with valid users of different groups
            self.logger.newStep("2. Verifying Ua Expert session with valid users of different groups")

            # Defining list of groups for which the connection is expected
            connExpectedForGrpsLi = ["Administrator", "Engineering", "Service", "EasyUi", "Developer", "Watch"]

            # Iterating and verifying connection for every user data (stored in commonConstants)
            for _ , userData in commonConstants.USERS_DETAILS_DICT_SECURITY_TEST.items():
                self.logger.newStep(f"[{type(self).prefixCls}] Verifying Ua Expert connection for user of "
                                    f"{userData['group']} group", level = 3)

                connectionExpectedFlag = False
                if userData['group'] in connExpectedForGrpsLi:
                    connectionExpectedFlag = True

                verificationResult = self.swtchUsrAndValConnection(
                    clientObj = uaExpertClientObj, userName = userData['userName'],
                    baseEncPassword = userData['password'],
                    connectionExpectedFlag = connectionExpectedFlag)
                testResult = testResult and verificationResult

            # Verifying Ua Expert session with invalid users of different groups
            self.logger.newStep("3. Verifying Ua Expert session with invalid users (wrong user name and correct "
                                "password) of different groups")
            for user, userData in commonConstants.USERS_DETAILS_DICT_SECURITY_TEST.items():
                self.logger.newStep(f"[{type(self).prefixCls}] Verifying Ua Expert connection for {user} "
                                    "with wrong user name", level = 3)

                verificationResult = self.swtchUsrAndValConnection(
                    clientObj = uaExpertClientObj, userName = constants.SECURITY_TEST_INVALID_USERNAME,
                    baseEncPassword = userData['password'], connectionExpectedFlag = False)

                testResult = testResult and verificationResult

            # Verifying Ua Expert session with invalid users of different groups
            self.logger.newStep("4. Verifying Ua Expert session with invalid users (correct user name and wrong "
                                "password) of different groups")
            for user, userData in commonConstants.USERS_DETAILS_DICT_SECURITY_TEST.items():
                self.logger.newStep(f"[{type(self).prefixCls}] Verifying Ua Expert connection for {user} "
                                    "with wrong password", level = 3)

                verificationResult = self.swtchUsrAndValConnection(
                    clientObj = uaExpertClientObj, userName = userData['userName'],
                    baseEncPassword = constants.SECURITY_TEST_INVALID_PASSWORD,
                    connectionExpectedFlag = False)

                testResult = testResult and verificationResult

            # Verifying Ua Expert session with invalid user (wrong username and wrong password)
            self.logger.newStep("5. Verifying Ua Expert session with invalid user (wrong user name and wrong password) "
                                "of different groups")

            verificationResult = self.swtchUsrAndValConnection(
                clientObj = uaExpertClientObj, userName = constants.SECURITY_TEST_INVALID_USERNAME,
                baseEncPassword = constants.SECURITY_TEST_INVALID_PASSWORD,
                connectionExpectedFlag = False)

            testResult = testResult and verificationResult

            # Closing Ua Expert tool session
            self.closeSessionAndValidate(clientObj = uaExpertClientObj)

            return testResult
        except Exception:
            if uaExpertClientObj:
                uaExpertClientObj.closeSession()

            return False

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def req_23_Grp_03_test_02(self) -> bool:

        easyStarterObj = None

        try:
            # EasyStarter object
            easyStarterObj = self.getClientObject(clientType = commonConstants.EASY_STARTER_NAME)

            # Easy Starter sessions
            self.logger.newStep("1.  Verifying Easy Starter Anonymous Session")
            self.occupySession(clientObj = easyStarterObj)
            testResult = self.validateSessionDetails(lstOfActiveClientObjs = [easyStarterObj])
            if testResult:
                self.logger.newStep("Successfully verified Easy Starter connection for Anonymous session")
            else:
                self.logger.error(f"[{type(self).prefixCls}] Easy Starter connection for Anonymous session failed")

            # Verifying EasyStarter session with valid users of different groups
            self.logger.newStep("2. Verifying EasyStarter session with valid users of different groups")

            # Defining list of groups for which the connection is expected
            connExpectedForGrpsLi = ["Administrator", "Engineering"]

            # Iterating and verifying connection for every user data (stored in commonConstants)
            for _ , userData in commonConstants.USERS_DETAILS_DICT_SECURITY_TEST.items():
                self.logger.newStep(f"[{type(self).prefixCls}] Verifying Easy Starter connection for user of "
                                    f"{userData['group']} group", level = 3)

                connectionExpectedFlag = False
                if userData['group'] in connExpectedForGrpsLi:
                    connectionExpectedFlag = True

                verificationResult = self.swtchUsrAndValConnection(
                    clientObj = easyStarterObj, userName = userData['userName'],
                    baseEncPassword = userData['password'], connectionExpectedFlag = connectionExpectedFlag)

                testResult = testResult and verificationResult

            # Verifying Easy Starter session with invalid username and correct password for all users
            self.logger.newStep("3. Verifying EasyStarter session with invalid users (wrong user name and correct "
                                "password) of different groups")
            for user, userData in commonConstants.USERS_DETAILS_DICT_SECURITY_TEST.items():
                self.logger.newStep(f"[{type(self).prefixCls}] Verifying Easy Starter connection for {user} "
                                    "with wrong user name", level = 3)

                verificationResult = self.swtchUsrAndValConnection(
                    clientObj = easyStarterObj, userName = constants.SECURITY_TEST_INVALID_USERNAME,
                    baseEncPassword = userData['password'], connectionExpectedFlag = False)

                testResult = testResult and verificationResult

            # Verifying Easy Starter session with correct username and invalid password for all users
            self.logger.newStep("4. Verifying EasyStarter session with invalid users (correct user name and "
                                "wrong password) of different groups")
            for user, userData in commonConstants.USERS_DETAILS_DICT_SECURITY_TEST.items():
                self.logger.newStep(f"[{type(self).prefixCls}] Verifying Easy Starter connection for {user} "
                                    "with wrong password", level = 3)

                verificationResult = self.swtchUsrAndValConnection(
                    clientObj = easyStarterObj, userName = userData['userName'],
                    baseEncPassword = constants.SECURITY_TEST_INVALID_PASSWORD,
                    connectionExpectedFlag = False)

                testResult = testResult and verificationResult

            # Verifying Easy Starter session with wrong username and wrong password
            self.logger.newStep("5. Verifying EasyStarter session with wrong username and wrong password")
            verificationResult = self.swtchUsrAndValConnection(
                clientObj = easyStarterObj, userName = constants.SECURITY_TEST_INVALID_USERNAME,
                baseEncPassword = constants.SECURITY_TEST_INVALID_PASSWORD,
                connectionExpectedFlag = False)

            testResult = testResult and verificationResult

            # Closing Easy Starter session
            self.closeSessionAndValidate(clientObj = easyStarterObj)
            return testResult
        except Exception:
            if easyStarterObj:
                easyStarterObj.closeSession()

            return False

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def req_23_Grp_03_test_03(self) -> bool:

        appLoaderObj = None

        try:
            # Application Loader object
            appLoaderObj = self.getClientObject(clientType = commonConstants.APPLICATION_LOADER_NAME)

            # Verifying Application Loader session as anonymous user
            self.logger.newStep("1. Verifying Application Loader session as anonymous user")
            self.occupySession(clientObj = appLoaderObj)
            testResult = self.validateSessionDetails(lstOfActiveClientObjs = [appLoaderObj])
            if testResult:
                self.logger.newStep("Successfully verified Application Loader connection for Anonymous session")
            else:
                self.logger.error(f"[{type(self).prefixCls}] Application Loader connection for Anonymous session "
                                  "failed")

            # Verifying Application Loader session with valid users of different groups
            self.logger.newStep("2. Verifying Application Loader session with valid users of different groups")

            # Defining list of groups for which the connection is expected
            connExpectedForGrpsLi = ["Administrator", "Engineering"]

            # Iterating and verifying connection for every user data (stored in commonConstants)
            for user, userData in commonConstants.USERS_DETAILS_DICT_SECURITY_TEST.items():
                self.logger.newStep(f"[{type(self).prefixCls}] Verifying connection Application Loader connection for "
                                    f"user of {userData['group']} group", level = 3)

                connectionExpectedFlag = False
                if userData['group'] in connExpectedForGrpsLi:
                    connectionExpectedFlag = True

                verificationResult = self.swtchUsrAndValConnection(
                    clientObj = appLoaderObj, userName = userData['userName'],
                    baseEncPassword = userData['password'], connectionExpectedFlag = connectionExpectedFlag)

                testResult = testResult and verificationResult

            # Verifying ApplicationLoader session with invalid username and correct password for all users
            self.logger.newStep("3. Verifying ApplicationLoader session with invalid users"
                                "(wrong user name and correct password) of different groups")
            for user, userData in commonConstants.USERS_DETAILS_DICT_SECURITY_TEST.items():
                connectionExpectedFlag = False
                self.logger.newStep(f"[{type(self).prefixCls}] Verifying ApplicationLoader connection for {user} "
                                    "with wrong user name", level = 3)

                verificationResult = self.swtchUsrAndValConnection(
                    clientObj = appLoaderObj, userName = constants.SECURITY_TEST_INVALID_USERNAME,
                    baseEncPassword = userData['password'], connectionExpectedFlag = False)

                testResult = testResult and verificationResult

            # Verifying ApplicationLoader session with correct username and invalid password for all users
            self.logger.newStep("4. Verifying ApplicationLoader session with invalid users"
                                "(correct user name and wrong password) of different groups")
            for user, userData in commonConstants.USERS_DETAILS_DICT_SECURITY_TEST.items():
                self.logger.newStep(f"[{type(self).prefixCls}] Verifying ApplicationLoader connection for {user} "
                                    "with wrong password", level = 3)

                verificationResult = self.swtchUsrAndValConnection(
                    clientObj = appLoaderObj, userName = userData['userName'],
                    baseEncPassword = constants.SECURITY_TEST_INVALID_PASSWORD,
                    connectionExpectedFlag = False)

                testResult = testResult and verificationResult

            # Verifying ApplicationLoader session with wrong username and wrong password
            self.logger.newStep("5. Verifying ApplicationLoader session with wrong username and wrong password")
            verificationResult = self.swtchUsrAndValConnection(
                clientObj = appLoaderObj, userName = constants.SECURITY_TEST_INVALID_USERNAME,
                baseEncPassword = constants.SECURITY_TEST_INVALID_PASSWORD,
                connectionExpectedFlag = False)

            testResult = testResult and verificationResult

            # Closing ApplicationLoader session
            self.closeSessionAndValidate(clientObj = appLoaderObj)

            return testResult
        except Exception:
            if appLoaderObj:
                appLoaderObj.closeSession()

            return False

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def req_23_Grp_03_test_04(self) -> bool:

        firmwareLoaderObj = None

        try:
            # Firmware Loader object
            firmwareLoaderObj = self.getClientObject(clientType = commonConstants.FIRMWARE_LOADER_NAME)

            # Verifying FirmwareLoader as anonymous user
            self.logger.newStep("1. Verifying Firmware Loader session as anonymous user")
            self.occupySession(clientObj = firmwareLoaderObj)
            testResult = self.validateSessionDetails(lstOfActiveClientObjs = [firmwareLoaderObj])
            if testResult:
                self.logger.newStep("Successfully verified Firmware Loader connection for Anonymous session")
            else:
                self.logger.error(f"[{type(self).prefixCls}] Firmware Loader connection for Anonymous session failed")

            if not self.waitForFWLoaderSessionToClose(
                    firmwareLoaderObj = firmwareLoaderObj,
                    userName = commonConstants.USERS_DETAILS_DICT_SECURITY_TEST['administratorUser']['userName'],
                    base64EncryptedPassword= commonConstants.USERS_DETAILS_DICT_SECURITY_TEST[
                        'administratorUser']['password']):
                testResult = False

            # Verifying Firmware Loader session with valid users of different groups
            self.logger.newStep("2. Verifying Firmware Loader session with valid users of different groups")

            # Defining list of groups for which the connection is expected
            connExpectedForGrpsLi = ["Administrator", "Engineering"]

            # Iterating and verifying connection for every user data (stored in commonConstants)
            for _ , userData in commonConstants.USERS_DETAILS_DICT_SECURITY_TEST.items():
                self.logger.newStep(f"[{type(self).prefixCls}] Verifying connection FirmwareLoader connection for "
                                    f"user of {userData['group']} group", level = 3)

                connectionExpectedFlag = False
                if userData['group'] in connExpectedForGrpsLi:
                    connectionExpectedFlag = True

                verificationResult = self.swtchUsrAndValConnection(
                    clientObj = firmwareLoaderObj, userName = userData['userName'],
                    baseEncPassword = userData['password'], connectionExpectedFlag = connectionExpectedFlag)

                # Waiting for firmware loader session to close
                # Added this code because it is observed that firmwareloader takes around 65 seconds to leave session
                # after successfull fw download
                if not self.waitForFWLoaderSessionToClose(
                        firmwareLoaderObj = firmwareLoaderObj,
                        userName = commonConstants.USERS_DETAILS_DICT_SECURITY_TEST['administratorUser']['userName'],
                        base64EncryptedPassword= commonConstants.USERS_DETAILS_DICT_SECURITY_TEST[
                            'administratorUser']['password']):
                    testResult = False

                testResult = testResult and verificationResult

            # Verifying Firmware Loader session with invalid username and correct password for all users
            self.logger.newStep("3. Verifying Firmware Loader session with invalid users"
                                "(wrong user name and correct password) of different groups")
            for user, userData in commonConstants.USERS_DETAILS_DICT_SECURITY_TEST.items():
                self.logger.newStep(f"[{type(self).prefixCls}] Verifying Firmware Loader connection for {user} "
                                    "with wrong user name", level = 3)

                verificationResult = self.swtchUsrAndValConnection(
                    clientObj = firmwareLoaderObj, userName = constants.SECURITY_TEST_INVALID_USERNAME,
                    baseEncPassword = userData['password'], connectionExpectedFlag = False)

                testResult = testResult and verificationResult

            # Verifying Firmware Loader session with correct username and invalid password for all users
            self.logger.newStep("4. Verifying Firmware Loader session with invalid users"
                                "(correct user name and wrong password) of different groups")
            for user, userData in commonConstants.USERS_DETAILS_DICT_SECURITY_TEST.items():
                self.logger.newStep(f"[{type(self).prefixCls}] Verifying Firmware Loader connection for {user} "
                                    "with wrong password", level = 3)

                verificationResult = self.swtchUsrAndValConnection(
                    clientObj = firmwareLoaderObj, userName = userData['userName'],
                    baseEncPassword = constants.SECURITY_TEST_INVALID_PASSWORD,
                    connectionExpectedFlag = False)

                testResult = testResult and verificationResult

            # Verifying Firmware Loader session with wrong username and wrong password
            self.logger.newStep("5. Verifying Firmware Loader session with wrong username and wrong password")
            verificationResult = self.swtchUsrAndValConnection(
                clientObj = firmwareLoaderObj, userName = constants.SECURITY_TEST_INVALID_USERNAME,
                baseEncPassword = constants.SECURITY_TEST_INVALID_PASSWORD,
                connectionExpectedFlag = False)

            testResult = testResult and verificationResult
            return testResult

        except Exception:
            if firmwareLoaderObj:
                firmwareLoaderObj.closeSession()

            return False

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def req_23_Grp_03_test_05(self) -> bool:

        easyUiDesignerObj = None

        try:
            # EasyUiDesigner object
            easyUiDesignerObj = self.getClientObject(clientType = commonConstants.EASY_UI_DESIGNER_NAME)

            # Occupying Easy Ui Session
            self.occupySession(clientObj = easyUiDesignerObj)

            # Easy ui Designer sessions
            self.logger.newStep("1. Verifying Rejection of Easy ui Designer Session as Anonymous user")
            # switchUserArgs
            swtchUserArgs = {commonConstants.USER_NAME_KEY: None,
                             commonConstants.BASE64_ENC_PASS_KEY: None}
            if easyUiDesignerObj.switchUser(**swtchUserArgs):
                # Updating numeric id for easy ui designer if switch user is successfull
                easyUiDesignerObj.numericId = Lib_OpcUa_Base.dummy3rdPrtyPyClientObj.getNumericId(index = -1)
            testResult = self.validateSessionDetails(lstOfActiveClientObjs = [])
            if testResult:
                self.logger.newStep("Successfully verified rejection of Easy ui Designer session for Anonymous user")
            else:
                self.logger.error(f"[{type(self).prefixCls}] Rejection for Easy ui Designer session failed ")

            # Defining list of groups for which the connection is expected
            connExpectedForGrpsLi = ["Administrator", "EasyUi", "Watch", "Service", "Developer"]

            # Verifying EasyUiDesigner session with valid users of different groups
            self.logger.newStep("2. Verifying EasyUiDesigner session with valid users of different groups")

            # Iterating and verifying connection for every user data (stored in commonConstants)
            for _ , userData in commonConstants.USERS_DETAILS_DICT_SECURITY_TEST.items():
                connectionExpectedFlag = False
                self.logger.newStep(f"[{type(self).prefixCls}] Verifying connection Easy Ui Designer connection for "
                                    f"user of {userData['group']} group", level = 3)

                if userData['group'] in connExpectedForGrpsLi:
                    connectionExpectedFlag = True

                verificationResult = self.swtchUsrAndValConnection(
                    clientObj = easyUiDesignerObj, userName = userData['userName'],
                    baseEncPassword = userData['password'], connectionExpectedFlag = connectionExpectedFlag)

                testResult = testResult and verificationResult

            # Verifying Easy ui Designer session with invalid username and correct password for all users
            self.logger.newStep("3. Verifying Easy ui Designer session with invalid users"
                                "(wrong user name and correct password) of different groups")
            for user, userData in commonConstants.USERS_DETAILS_DICT_SECURITY_TEST.items():
                self.logger.newStep(f"[{type(self).prefixCls}] Verifying Easy ui Designer connection for {user} "
                                    "with wrong user name", level = 3)

                verificationResult = self.swtchUsrAndValConnection(
                    clientObj = easyUiDesignerObj, userName = constants.SECURITY_TEST_INVALID_USERNAME,
                    baseEncPassword = userData['password'], connectionExpectedFlag = False)

                testResult = testResult and verificationResult

            # Verifying Easy ui Designer session with correct username and invalid password for all users
            self.logger.newStep("4. Verifying Easy ui Designer session with invalid users"
                                "(correct user name and wrong password) of different groups")
            for user, userData in commonConstants.USERS_DETAILS_DICT_SECURITY_TEST.items():
                self.logger.newStep(f"[{type(self).prefixCls}] Verifying Easy ui Designer connection for {user} "
                                    "with wrong password", level = 3)

                verificationResult = self.swtchUsrAndValConnection(
                    clientObj = easyUiDesignerObj, userName = userData['userName'],
                    baseEncPassword = constants.SECURITY_TEST_INVALID_PASSWORD,
                    connectionExpectedFlag = False)

                testResult = testResult and verificationResult

            # Verifying Easy ui Designer session with wrong username and wrong password
            self.logger.newStep("5. Verifying Easy ui Designer session with wrong username and wrong password")
            verificationResult = self.swtchUsrAndValConnection(
                clientObj = easyUiDesignerObj, userName = constants.SECURITY_TEST_INVALID_USERNAME,
                baseEncPassword = constants.SECURITY_TEST_INVALID_PASSWORD,
                connectionExpectedFlag = False)

            testResult = testResult and verificationResult

            # Closing Easy ui Designer session
            self.closeSessionAndValidate(clientObj = easyUiDesignerObj)
            return testResult
        except Exception:
            if easyUiDesignerObj:
                easyUiDesignerObj.closeSession()

            return False

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def req_23_Grp_03_test_06(self) -> bool:

        thirdPrtyClientObj = None

        try:
            # Third party client object
            thirdPrtyClientObj = self.getClientObject(clientType = commonConstants.PYTEF_CLIENT_NAME)

            # Verifying Rejection of Third party client session as anonymous user
            self.logger.newStep("1.  Verifying Rejection of Third party client  session as anonymous user")
            self.occupySession(clientObj = thirdPrtyClientObj)
            testResult = self.validateSessionDetails(lstOfActiveClientObjs = [])
            if testResult:
                self.logger.newStep("Successfully verified rejection of Third party client  session for Anonymous user")
            else:
                self.logger.error(f"[{type(self).prefixCls}] Rejection for Third party client  session failed ")

            # Verifying Third party client session with valid users of different groups
            self.logger.newStep("2. Verifying thirdPrtyClientObj session with valid users of different groups")

            # Iterating and verifying connection for every user data (stored in commonConstants)
            for _ , userData in commonConstants.USERS_DETAILS_DICT_SECURITY_TEST.items():
                self.logger.newStep(f"[{type(self).prefixCls}] Verifying third party python connection for user of "
                                    f"{userData['group']} group", level = 3)

                verificationResult = self.swtchUsrAndValConnection(
                    clientObj = thirdPrtyClientObj, userName = userData['userName'],
                    baseEncPassword = userData['password'], connectionExpectedFlag = True)

                testResult = testResult and verificationResult

            # Verifying Third party python session with invalid username and correct password for all users
            self.logger.newStep("3. Verifying Third party python session with invalid users"
                                "(wrong user name and correct password) of different groups")
            for user, userData in commonConstants.USERS_DETAILS_DICT_SECURITY_TEST.items():
                self.logger.newStep(f"[{type(self).prefixCls}] Verifying Third party python connection for {user} with "
                                    "wrong user name", level = 3)

                verificationResult = self.swtchUsrAndValConnection(
                    clientObj = thirdPrtyClientObj, userName = constants.SECURITY_TEST_INVALID_USERNAME,
                    baseEncPassword = userData['password'], connectionExpectedFlag = False)

                testResult = testResult and verificationResult

            # Verifying Third party python session with correct username and invalid password for all users
            self.logger.newStep("4. Verifying Third party python session with invalid users"
                                "(correct user name and wrong password) of different groups")
            for user, userData in commonConstants.USERS_DETAILS_DICT_SECURITY_TEST.items():
                self.logger.newStep(
                    f"[{type(self).prefixCls}] Verifying Third party python connection for {user} "
                    "with wrong password", level = 3)

                verificationResult = self.swtchUsrAndValConnection(
                    clientObj = thirdPrtyClientObj, userName = userData['userName'],
                    baseEncPassword = constants.SECURITY_TEST_INVALID_PASSWORD,
                    connectionExpectedFlag = False)

                testResult = testResult and verificationResult

            # Verifying Third party python session with wrong username and wrong password
            self.logger.newStep("5. Verifying Third party python session with wrong username and wrong password")
            verificationResult = self.swtchUsrAndValConnection(
                clientObj = thirdPrtyClientObj, userName = constants.SECURITY_TEST_INVALID_USERNAME,
                baseEncPassword = constants.SECURITY_TEST_INVALID_PASSWORD,
                connectionExpectedFlag = False)

            testResult = testResult and verificationResult

            # Closing Third party python session
            self.closeSessionAndValidate(clientObj = thirdPrtyClientObj)
            return testResult
        except Exception:
            if thirdPrtyClientObj:
                thirdPrtyClientObj.closeSession()

            return False

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def req_23_Grp_03_test_07(self) -> bool:

        self.testCase.skip("The testcase for x510 is skipped as a issue is observed with x510 session due to a reason "
                           "where connection is expected to be rejected when x510 occupies about 8 sessions")

        x510Obj = None

        try:
            # This testcase for x510 is commented as a issue is observed with x510 session
            # i.e In the cases where connection is expected to be rejected.. x510 occupies about 8 sessions
            #
            # x510 object
            x510Obj = self.getClientObject(clientType = commonConstants.X510_NAME)

            # x510 session
            self.logger.newStep("1. Verifying Rejection of x510 Anonymous Session")
            self.occupySession(clientObj = x510Obj)
            testResult = self.validateSessionDetails(lstOfActiveClientObjs = [x510Obj])
            if testResult:
                self.logger.newStep("Successfully verified rejection of x510 session for Anonymous user")
            else:
                self.logger.error(f"[{type(self).prefixCls}] Rejection for x510 session failed ")

            # Defining list of groups for which the connection is expected
            connExpectedForGrpsLi = ["Administrator", "Engineering", "EasyUi", "Developer", "Service", "Watch"]

            # Verifying x510 session with valid users of different groups
            self.logger.newStep("2. Verifying x510 session with valid users of different groups")
            # Iterating and verifying connection for every user data (stored in commonConstants)
            for _ , userData in commonConstants.USERS_DETAILS_DICT_SECURITY_TEST.items():
                connectionExpectedFlag = False
                self.logger.newStep(f"[{type(self).prefixCls}] Verifying x510 connection for user of "
                                    f"{userData['group']} group", level = 3)

                if userData['group'] in connExpectedForGrpsLi:
                    connectionExpectedFlag = True

                verificationResult = self.swtchUsrAndValConnection(
                    clientObj = x510Obj, userName = userData['userName'],
                    baseEncPassword = userData['password'], connectionExpectedFlag = connectionExpectedFlag)

                testResult = testResult and verificationResult

            # Verifying x510 session with invalid username and correct password for all users
            self.logger.newStep("3. Verifying x510 session with invalid users "
                                "(wrong user name and correct password) of different groups")
            for user, userData in commonConstants.USERS_DETAILS_DICT_SECURITY_TEST.items():
                self.logger.newStep(f"[{type(self).prefixCls}] Verifying x510 connection for {user} with wrong "
                                    "user name", level = 3)

                verificationResult = self.swtchUsrAndValConnection(
                    clientObj = x510Obj, userName = constants.SECURITY_TEST_INVALID_USERNAME,
                    baseEncPassword = userData['password'], connectionExpectedFlag = False)

                testResult = testResult and verificationResult

            # Verifying x510 session with correct username and invalid password for all users
            self.logger.newStep("4. Verifying x510 session with invalid users "
                                "(correct user name and wrong password) of different groups")
            for user, userData in commonConstants.USERS_DETAILS_DICT_SECURITY_TEST.items():
                self.logger.newStep(f"[{type(self).prefixCls}] Verifying x510 connection for {user} "
                                    "with wrong password", level = 3)

                verificationResult = self.swtchUsrAndValConnection(
                    clientObj = x510Obj, userName = userData['userName'],
                    baseEncPassword = constants.SECURITY_TEST_INVALID_PASSWORD,
                    connectionExpectedFlag = False)

                testResult = testResult and verificationResult

            # Verifying x510 session with wrong username and wrong password
            self.logger.newStep("5. Verifying x510 session with wrong username and wrong password")
            verificationResult = self.swtchUsrAndValConnection(
                clientObj = x510Obj, userName = constants.SECURITY_TEST_INVALID_USERNAME,
                baseEncPassword = constants.SECURITY_TEST_INVALID_PASSWORD,
                connectionExpectedFlag = False)

            testResult = testResult and verificationResult

            # Closing x510 session
            self.closeSessionAndValidate(clientObj = x510Obj)
            return testResult

        except Exception:
            if x510Obj:
                x510Obj.closeSession()

            return False

    #-------------------------------------------------------------------------------------------------------------------
    def req_23_Grp_03_test_99_post(self) -> Any:
        if Lib_OpcUa_Base.dummy3rdPrtyPyClientObj:
            Lib_OpcUa_Base.dummy3rdPrtyPyClientObj.closeSession()

    #-------------------------------------------------------------------------------------------------------------------
    def req_23_Grp_04_test_00_pre(self) -> Any:
        """
        Pre verify connection to controller with Anonymous user deleted and user management activated
        """

        self.pre_setUp()

        self.logger.info(f"[{type(self).prefixCls}] PREREQUISITE Steps".format())

        # Activating user management
        self.logger.newStep(f"[{type(self).prefixCls}] Step 1. Activating user management and adding users",
                            level = 3)
        if not Lib_UserMgmt_ES.PLCD_OBJECT.activateUsrMgmtAndAddAdminUsr(
                projName = commonConstants.PLC_PROJ_NAME,
                adminData = commonConstants.USERS_DETAILS_DICT_SECURITY_TEST['administratorUser']):
            raise Exception("User Management is not activated")

        # Add users
        usersAddedStatus = Lib_UserMgmt_ES.PLCD_OBJECT.addUsersInUserAndGroups(
            userData = commonConstants.USERS_DETAILS_DICT_SECURITY_TEST, projName = commonConstants.PLC_PROJ_NAME)
        if not usersAddedStatus:
            raise Exception("Failed to add users in user management")

        # Stopping sync mode in Users and Groups
        self.logger.newStep(f"[{type(self).prefixCls}] Step 2. Stop Synchronization mode", level = 3)
        if not Lib_UserMgmt_ES.PLCD_OBJECT.stopSyncModeInUsersAndGroups():
            raise Exception("Failed to stop sync mode in Users and Groups Tab")

        # Setting Modify, View, Execute Access to EasyUi Interface
        self.logger.newStep(f"[{type(self).prefixCls}] Step 3. Setting Modify, View, Execute Access to EasyUi "
                            "Interface", level = 3)
        if not Lib_UserMgmt_ES.PLCD_OBJECT.grantAccessRightsFromFile(
                drmFileName = constants.DEVICE_RIGHT_MANAGEMENT_FILE_NAME,
                drmFilePath = constants.SECURITY_TEST_INPUT_FILES,
                projname = commonConstants.PLC_PROJ_NAME):
            raise Exception("Access Rights not set for EasyUi Interface")

        # Stop sync mode
        self.logger.newStep(f"[{type(self).prefixCls}] Step 4. Stop Synchronization mode in Access Rights tab",
                            level = 3)
        if not Lib_UserMgmt_ES.PLCD_OBJECT.stopSyncModeInAccessRights():
            raise Exception("Failed to stop sync mode")

        # Deleting anonymous user
        self.logger.newStep(f"[{type(self).prefixCls}] Step 5. Delete 'Anonymous_OPCUAServer' user from user "
                            "management", level = 3)
        usersDelStatus = Lib_UserMgmt_ES.PLCD_OBJECT.deleteUserInUserAndGroups(
            projName = commonConstants.PLC_PROJ_NAME, userName = "Anonymous_OPCUAServer",
            adminData = commonConstants.USERS_DETAILS_DICT_SECURITY_TEST["administratorUser"])
        if not usersDelStatus:
            raise Exception("Failed to anonymous user from user management")

        Lib_UserMgmt_ES.PLCD_OBJECT.createBootProject(projName = commonConstants.PLC_PROJ_NAME)

        # Reboot controller
        self.logger.newStep(f"[{type(self).prefixCls}] Step 6. Reboot Controller", level = 3)
        if not self.restartController():
            raise Exception("Failed to reboot the controller")

        self.logger.info("Waiting for 30 secs, for OPC Ua Server to restart before connection with Pytef Client")
        userSleep(60)

        # Third party client 1 object
        self.logger.newStep(f"[{type(self).prefixCls}] Step 7. Occupying dummy 3rd party session as admin user",
                            level = 3)
        Lib_OpcUa_Base.dummy3rdPrtyPyClientObj = self.getClientObject(clientType = commonConstants.PYTEF_CLIENT_NAME)

        # Connecting dummy 3rd party client using username
        if not self.occupySession(
                clientObj = Lib_OpcUa_Base.dummy3rdPrtyPyClientObj,
                userName = commonConstants.USERS_DETAILS_DICT_SECURITY_TEST['administratorUser']['userName'],
                base64EncryptedPassword= commonConstants.USERS_DETAILS_DICT_SECURITY_TEST[
                    'administratorUser']['password']):
            self.logger.info("Waiting 5 sec and trying again")
            userSleep(5)
            if not self.occupySession(
                    clientObj = Lib_OpcUa_Base.dummy3rdPrtyPyClientObj,
                    userName = commonConstants.USERS_DETAILS_DICT_SECURITY_TEST['administratorUser']['userName'],
                    base64EncryptedPassword= commonConstants.USERS_DETAILS_DICT_SECURITY_TEST[
                        'administratorUser']['password']):
                raise Exception("Failed to connect dummy third party connection")

        self.logger.info(f"[{type(self).prefixCls}] PREREQUISITE Completed".format())

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def req_23_Grp_04_test_01(self) -> bool:

        uaExpertClientObj = None

        try:
            # Ua Expert Object
            uaExpertClientObj = self.getClientObject(clientType = commonConstants.UA_EXPERT_NAME)

            # Ua Expert sessions
            self.logger.newStep("1.  Verifying Rejection of Ua Expert Anonymous Session")
            self.occupySession(clientObj = uaExpertClientObj)
            testResult = self.validateSessionDetails(lstOfActiveClientObjs = [])
            if testResult:
                self.logger.newStep("Successfully verified rejection of Ua Expert session for Anonymous user")
            else:
                self.logger.error(f"[{type(self).prefixCls}] Rejection for Ua Expert session failed ")

            # Verifying Ua Expert session with valid users of different groups
            self.logger.newStep("2. Verifying Ua Expert session with valid users of different groups")

            # Defining list of groups for which the connection is expected
            connExpectedForGrpsLi = ["Administrator", "Engineering", "Service", "EasyUi", "Developer", "Watch"]

            # Iterating and verifying connection for every user data (stored in commonConstants)
            for _ , userData in commonConstants.USERS_DETAILS_DICT_SECURITY_TEST.items():
                self.logger.newStep(f"[{type(self).prefixCls}] Verifying Ua Expert connection for user of "
                                    f"{userData['group']} group", level = 3)

                connectionExpectedFlag = False
                if userData['group'] in connExpectedForGrpsLi:
                    connectionExpectedFlag = True

                verificationResult = self.swtchUsrAndValConnection(
                    clientObj = uaExpertClientObj, userName = userData['userName'],
                    baseEncPassword = userData['password'],
                    connectionExpectedFlag = connectionExpectedFlag)
                testResult = testResult and verificationResult

            # Verifying Ua Expert session with invalid users of different groups
            self.logger.newStep("3. Verifying Ua Expert session with invalid users (wrong user name and correct "
                                "password) of different groups")
            for user, userData in commonConstants.USERS_DETAILS_DICT_SECURITY_TEST.items():
                self.logger.newStep(f"[{type(self).prefixCls}] Verifying Ua Expert connection for {user} "
                                    "with wrong user name", level = 3)

                verificationResult = self.swtchUsrAndValConnection(
                    clientObj = uaExpertClientObj, userName = constants.SECURITY_TEST_INVALID_USERNAME,
                    baseEncPassword = userData['password'], connectionExpectedFlag = False)

                testResult = testResult and verificationResult

            # Verifying Ua Expert session with invalid users of different groups
            self.logger.newStep("4. Verifying Ua Expert session with invalid users (correct user name and "
                                "wrong password) of different groups")
            for user, userData in commonConstants.USERS_DETAILS_DICT_SECURITY_TEST.items():
                self.logger.newStep(f"[{type(self).prefixCls}] Verifying Ua Expert connection for {user} "
                                    "with wrong password", level = 3)

                verificationResult = self.swtchUsrAndValConnection(
                    clientObj = uaExpertClientObj, userName = userData['userName'],
                    baseEncPassword = constants.SECURITY_TEST_INVALID_PASSWORD,
                    connectionExpectedFlag = False)

                testResult = testResult and verificationResult

            # Verifying Ua Expert session with invalid user (wrong username and wrong password)
            self.logger.newStep("5. Verifying Ua Expert session with invalid user (wrong user name and wrong password) "
                                "of different groups")

            verificationResult = self.swtchUsrAndValConnection(
                clientObj = uaExpertClientObj, userName = constants.SECURITY_TEST_INVALID_USERNAME,
                baseEncPassword = constants.SECURITY_TEST_INVALID_PASSWORD,
                connectionExpectedFlag = False)

            testResult = testResult and verificationResult

            # Closing Ua Expert tool session
            self.closeSessionAndValidate(clientObj = uaExpertClientObj)
            return testResult
        except Exception:
            if uaExpertClientObj:
                uaExpertClientObj.closeSession()

            return False

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def req_23_Grp_04_test_02(self) -> bool:

        easyStarterObj = None

        try:
            # EasyStarter object
            easyStarterObj = self.getClientObject(clientType = commonConstants.EASY_STARTER_NAME)

            # Easy Starter sessions
            self.logger.newStep("1.  Verifying Easy Starter Anonymous Session")
            self.occupySession(clientObj = easyStarterObj)
            testResult = self.validateSessionDetails(lstOfActiveClientObjs = [easyStarterObj])
            if testResult:
                self.logger.newStep("Successfully verified Easy Starter connection for Anonymous session")
            else:
                self.logger.error(f"[{type(self).prefixCls}] Easy Starter connection for Anonymous session failed")

            # Verifying EasyStarter session with valid users of different groups
            self.logger.newStep("2. Verifying EasyStarter session with valid users of different groups")

            # Defining list of groups for which the connection is expected
            connExpectedForGrpsLi = ["Administrator", "Engineering"]

            # Iterating and verifying connection for every user data (stored in commonConstants)
            for _ , userData in commonConstants.USERS_DETAILS_DICT_SECURITY_TEST.items():
                self.logger.newStep(f"[{type(self).prefixCls}] Verifying Easy Starter connection for user of "
                                    f"{userData['group']} group", level = 3)

                connectionExpectedFlag = False
                if userData['group'] in connExpectedForGrpsLi:
                    connectionExpectedFlag = True

                verificationResult = self.swtchUsrAndValConnection(
                    clientObj = easyStarterObj, userName = userData['userName'],
                    baseEncPassword = userData['password'], connectionExpectedFlag = connectionExpectedFlag)

                testResult = testResult and verificationResult

            # Verifying Easy Starter session with invalid username and correct password for all users
            self.logger.newStep("3. Verifying EasyStarter session with invalid users (wrong user name and correct "
                                "password) of different groups")
            for user, userData in commonConstants.USERS_DETAILS_DICT_SECURITY_TEST.items():
                self.logger.newStep(f"[{type(self).prefixCls}] Verifying Easy Starter connection for {user} "
                                    "with wrong user name", level = 3)

                verificationResult = self.swtchUsrAndValConnection(
                    clientObj = easyStarterObj, userName = constants.SECURITY_TEST_INVALID_USERNAME,
                    baseEncPassword = userData['password'], connectionExpectedFlag = False)

                testResult = testResult and verificationResult

            # Verifying Easy Starter session with correct username and invalid password for all users
            self.logger.newStep("4. Verifying EasyStarter session with invalid users (correct user name and wrong "
                                "password) of different groups")
            for user, userData in commonConstants.USERS_DETAILS_DICT_SECURITY_TEST.items():
                self.logger.newStep(f"[{type(self).prefixCls}] Verifying Easy Starter connection for {user} "
                                    "with wrong password", level = 3)

                verificationResult = self.swtchUsrAndValConnection(
                    clientObj = easyStarterObj, userName = userData['userName'],
                    baseEncPassword = constants.SECURITY_TEST_INVALID_PASSWORD,
                    connectionExpectedFlag = False)

                testResult = testResult and verificationResult

            # Verifying Easy Starter session with wrong username and wrong password
            self.logger.newStep("5. Verifying EasyStarter session with wrong username and wrong password")
            verificationResult = self.swtchUsrAndValConnection(
                clientObj = easyStarterObj, userName = constants.SECURITY_TEST_INVALID_USERNAME,
                baseEncPassword = constants.SECURITY_TEST_INVALID_PASSWORD,
                connectionExpectedFlag = False)

            testResult = testResult and verificationResult

            # Closing Easy Starter session
            self.closeSessionAndValidate(clientObj = easyStarterObj)
            return testResult
        except Exception:
            if easyStarterObj:
                easyStarterObj.closeSession()

            return False

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def req_23_Grp_04_test_03(self) -> bool:

        appLoaderObj = None

        try:
            # Application Loader object
            appLoaderObj = self.getClientObject(clientType = commonConstants.APPLICATION_LOADER_NAME)

            # Verifying Application Loader session as anonymous user
            self.logger.newStep("1.  Verifying Application Loader session as anonymous user")
            self.occupySession(clientObj = appLoaderObj)
            testResult = self.validateSessionDetails(lstOfActiveClientObjs = [appLoaderObj])
            if testResult:
                self.logger.newStep("Successfully verified Application Loader connection for Anonymous session")
            else:
                self.logger.error(f"[{type(self).prefixCls}] Application Loader connection for Anonymous session "
                                  "failed")

            # Verifying Application Loader session with valid users of different groups
            self.logger.newStep("2. Verifying Application Loader session with valid users of different groups")

            # Defining list of groups for which the connection is expected
            connExpectedForGrpsLi = ["Administrator", "Engineering"]

            # Iterating and verifying connection for every user data (stored in commonConstants)
            for _ , userData in commonConstants.USERS_DETAILS_DICT_SECURITY_TEST.items():
                self.logger.newStep(f"[{type(self).prefixCls}] Verifying connection of Application Loader for user of "
                                    f"{userData['group']} group", level = 3)

                connectionExpectedFlag = False
                if userData['group'] in connExpectedForGrpsLi:
                    connectionExpectedFlag = True

                verificationResult = self.swtchUsrAndValConnection(
                    clientObj = appLoaderObj, userName = userData['userName'],
                    baseEncPassword = userData['password'], connectionExpectedFlag = connectionExpectedFlag)

                testResult = testResult and verificationResult

            # Verifying ApplicationLoader session with invalid username and correct password for all users
            self.logger.newStep("3. Verifying ApplicationLoader session with invalid users"
                                "(wrong user name and correct password) of different groups")
            for user, userData in commonConstants.USERS_DETAILS_DICT_SECURITY_TEST.items():
                connectionExpectedFlag = False
                self.logger.newStep(f"[{type(self).prefixCls}] Verifying ApplicationLoader connection for {user} "
                                    "with wrong user name", level = 3)

                verificationResult = self.swtchUsrAndValConnection(
                    clientObj = appLoaderObj, userName = constants.SECURITY_TEST_INVALID_USERNAME,
                    baseEncPassword = userData['password'], connectionExpectedFlag = False)

                testResult = testResult and verificationResult

            # Verifying ApplicationLoader session with correct username and invalid password for all users
            self.logger.newStep("4. Verifying ApplicationLoader session with invalid users"
                                "(correct user name and wrong password) of different groups")
            for user, userData in commonConstants.USERS_DETAILS_DICT_SECURITY_TEST.items():
                self.logger.newStep(f"[{type(self).prefixCls}] Verifying ApplicationLoader connection for {user} "
                                    "with wrong password", level = 3)

                verificationResult = self.swtchUsrAndValConnection(
                    clientObj = appLoaderObj, userName = userData['userName'],
                    baseEncPassword = constants.SECURITY_TEST_INVALID_PASSWORD,
                    connectionExpectedFlag = False)

                testResult = testResult and verificationResult

            # Verifying ApplicationLoader session with wrong username and wrong password
            self.logger.newStep("5. Verifying ApplicationLoader session with wrong username and wrong password")
            verificationResult = self.swtchUsrAndValConnection(
                clientObj = appLoaderObj, userName = constants.SECURITY_TEST_INVALID_USERNAME,
                baseEncPassword = constants.SECURITY_TEST_INVALID_PASSWORD,
                connectionExpectedFlag = False)

            testResult = testResult and verificationResult

            # Closing ApplicationLoader session
            self.closeSessionAndValidate(clientObj = appLoaderObj)
            return testResult

        except Exception:
            if appLoaderObj:
                appLoaderObj.closeSession()

            return False

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def req_23_Grp_04_test_04(self) -> bool:

        firmwareLoaderObj = None

        try:
            # Firmware Loader object
            firmwareLoaderObj = self.getClientObject(clientType = commonConstants.FIRMWARE_LOADER_NAME)

            # Verifying FirmwareLoader as anonymous user
            self.logger.newStep("1. Verifying Firmware Loader session as anonymous user")
            self.occupySession(clientObj = firmwareLoaderObj)
            testResult = self.validateSessionDetails(lstOfActiveClientObjs = [firmwareLoaderObj])
            if testResult:
                self.logger.newStep("Successfully verified Firmware Loader connection for Anonymous session")
            else:
                self.logger.error(f"[{type(self).prefixCls}] Firmware Loader connection for Anonymous session failed")

            if not self.waitForFWLoaderSessionToClose(
                    firmwareLoaderObj = firmwareLoaderObj,
                    userName = commonConstants.USERS_DETAILS_DICT_SECURITY_TEST['administratorUser']['userName'],
                    base64EncryptedPassword= commonConstants.USERS_DETAILS_DICT_SECURITY_TEST[
                        'administratorUser']['password']):
                testResult = False

            # Verifying Firmware Loader session with valid users of different groups
            self.logger.newStep("2. Verifying Firmware Loader session with valid users of different groups")

            # Defining list of groups for which the connection is expected
            connExpectedForGrpsLi = ["Administrator", "Engineering"]

            # Iterating and verifying connection for every user data (stored in commonConstants)
            for _ , userData in commonConstants.USERS_DETAILS_DICT_SECURITY_TEST.items():
                self.logger.newStep(f"[{type(self).prefixCls}] Verifying connection of Firmware Loader for user of "
                                    f"{userData['group']} group", level = 3)

                connectionExpectedFlag = False
                if userData['group'] in connExpectedForGrpsLi:
                    connectionExpectedFlag = True

                verificationResult = self.swtchUsrAndValConnection(
                    clientObj = firmwareLoaderObj, userName = userData['userName'],
                    baseEncPassword = userData['password'], connectionExpectedFlag = connectionExpectedFlag)

                # Waiting for firmware loader session to close
                # Added this code because it is observed that firmware loader takes around 65 seconds to leave session
                # after successfully fw download
                if not self.waitForFWLoaderSessionToClose(
                        firmwareLoaderObj = firmwareLoaderObj,
                        userName = commonConstants.USERS_DETAILS_DICT_SECURITY_TEST['administratorUser']['userName'],
                        base64EncryptedPassword= commonConstants.USERS_DETAILS_DICT_SECURITY_TEST[
                            'administratorUser']['password']):
                    testResult = False

                testResult = testResult and verificationResult

            # Verifying Firmware Loader session with invalid username and correct password for all users
            self.logger.newStep("3. Verifying Firmware Loader session with invalid users"
                                "(wrong user name and correct password) of different groups")
            for user, userData in commonConstants.USERS_DETAILS_DICT_SECURITY_TEST.items():
                self.logger.newStep(f"[{type(self).prefixCls}] Verifying Firmware Loader connection for {user} "
                                    "with wrong user name", level = 3)

                verificationResult = self.swtchUsrAndValConnection(
                    clientObj = firmwareLoaderObj, userName = constants.SECURITY_TEST_INVALID_USERNAME,
                    baseEncPassword = userData['password'], connectionExpectedFlag = False)

                testResult = testResult and verificationResult

            # Verifying Firmware Loader session with correct username and invalid password for all users
            self.logger.newStep("4. Verifying Firmware Loader session with invalid users"
                                "(correct user name and wrong password) of different groups")
            for user, userData in commonConstants.USERS_DETAILS_DICT_SECURITY_TEST.items():
                self.logger.newStep(f"[{type(self).prefixCls}] Verifying Firmware Loader connection for {user} "
                                    "with wrong password", level = 3)

                verificationResult = self.swtchUsrAndValConnection(
                    clientObj = firmwareLoaderObj, userName = userData['userName'],
                    baseEncPassword = constants.SECURITY_TEST_INVALID_PASSWORD,
                    connectionExpectedFlag = False)

                testResult = testResult and verificationResult

            # Verifying Firmware Loader session with wrong username and wrong password
            self.logger.newStep("5. Verifying Firmware Loader session with wrong username and wrong password")
            verificationResult = self.swtchUsrAndValConnection(
                clientObj = firmwareLoaderObj, userName = constants.SECURITY_TEST_INVALID_USERNAME,
                baseEncPassword = constants.SECURITY_TEST_INVALID_PASSWORD,
                connectionExpectedFlag = False)

            testResult = testResult and verificationResult
            return testResult

        except Exception:
            if firmwareLoaderObj:
                firmwareLoaderObj.closeSession()

            return False

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def req_23_Grp_04_test_05(self) -> bool:

        easyUiDesignerObj = None

        try:
            # EasyUiDesigner object
            easyUiDesignerObj = self.getClientObject(clientType = commonConstants.EASY_UI_DESIGNER_NAME)

            # Occupying Easy Ui Session
            self.occupySession(clientObj = easyUiDesignerObj)

            # Easy ui Designer sessions
            self.logger.newStep("1. Verifying Rejection of Easy ui Designer Session as Anonymous user")
            # switchUserArgs
            swtchUserArgs = {commonConstants.USER_NAME_KEY: None,
                             commonConstants.BASE64_ENC_PASS_KEY: None}
            if easyUiDesignerObj.switchUser(**swtchUserArgs):
                # Updating numeric id for easy ui designer if switch user is successfull
                easyUiDesignerObj.numericId = Lib_OpcUa_Base.dummy3rdPrtyPyClientObj.getNumericId(index = -1)
            testResult = self.validateSessionDetails(lstOfActiveClientObjs = [])
            if testResult:
                self.logger.newStep("Successfully verified rejection of Easy ui Designer session for Anonymous user")
            else:
                self.logger.error(f"[{type(self).prefixCls}] Rejection for Easy ui Designer session failed ")

            # Defining list of groups for which the connection is expected
            connExpectedForGrpsLi = ["Administrator", "EasyUi", "Watch", "Service", "Developer"]

            # Verifying EasyUiDesigner session with valid users of different groups
            self.logger.newStep("2. Verifying EasyUiDesigner session with valid users of different groups")

            # Iterating and verifying connection for every user data (stored in commonConstants)
            for _ , userData in commonConstants.USERS_DETAILS_DICT_SECURITY_TEST.items():
                connectionExpectedFlag = False
                self.logger.newStep(f"[{type(self).prefixCls}] Verifying connection of Easy Ui Designer for user of "
                                    f"{userData['group']} group", level = 3)

                if userData['group'] in connExpectedForGrpsLi:
                    connectionExpectedFlag = True

                verificationResult = self.swtchUsrAndValConnection(
                    clientObj = easyUiDesignerObj, userName = userData['userName'],
                    baseEncPassword = userData['password'], connectionExpectedFlag = connectionExpectedFlag)

                testResult = testResult and verificationResult

            # Verifying Easy ui Designer session with invalid username and correct password for all users
            self.logger.newStep("3. Verifying Easy ui Designer session with invalid users"
                                "(wrong user name and correct password) of different groups")
            for user, userData in commonConstants.USERS_DETAILS_DICT_SECURITY_TEST.items():
                self.logger.newStep(f"[{type(self).prefixCls}] Verifying Easy ui Designer connection for {user} "
                                    "with wrong user name", level = 3)

                verificationResult = self.swtchUsrAndValConnection(
                    clientObj = easyUiDesignerObj, userName = constants.SECURITY_TEST_INVALID_USERNAME,
                    baseEncPassword = userData['password'], connectionExpectedFlag = False)

                testResult = testResult and verificationResult

            # Verifying Easy ui Designer session with correct username and invalid password for all users
            self.logger.newStep("4. Verifying Easy ui Designer session with invalid users"
                                "(correct user name and wrong password) of different groups")
            for user, userData in commonConstants.USERS_DETAILS_DICT_SECURITY_TEST.items():
                self.logger.newStep(f"[{type(self).prefixCls}] Verifying Easy ui Designer connection for {user} "
                                    "with wrong password", level = 3)

                verificationResult = self.swtchUsrAndValConnection(
                    clientObj = easyUiDesignerObj, userName = userData['userName'],
                    baseEncPassword = constants.SECURITY_TEST_INVALID_PASSWORD,
                    connectionExpectedFlag = False)

                testResult = testResult and verificationResult

            # Verifying Easy ui Designer session with wrong username and wrong password
            self.logger.newStep("5. Verifying Easy ui Designer session with wrong username and wrong password")
            verificationResult = self.swtchUsrAndValConnection(
                clientObj = easyUiDesignerObj, userName = constants.SECURITY_TEST_INVALID_USERNAME,
                baseEncPassword = constants.SECURITY_TEST_INVALID_PASSWORD,
                connectionExpectedFlag = False)

            testResult = testResult and verificationResult

            # Closing Easy ui Designer session
            self.closeSessionAndValidate(clientObj = easyUiDesignerObj)
            return testResult

        except Exception:
            if easyUiDesignerObj:
                easyUiDesignerObj.closeSession()

            return False

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def req_23_Grp_04_test_06(self) -> bool:

        thirdPrtyClientObj = None

        try:
            # Third party client object
            thirdPrtyClientObj = self.getClientObject(clientType = commonConstants.PYTEF_CLIENT_NAME)

            # Verifying Rejection of Third party client session as anonymous user
            self.logger.newStep("1. Verifying Rejection of Third party client session as anonymous user")
            self.occupySession(clientObj = thirdPrtyClientObj)
            testResult = self.validateSessionDetails(lstOfActiveClientObjs = [])
            if testResult:
                self.logger.newStep("Successfully verified rejection of Third party client session for Anonymous user")
            else:
                self.logger.error(f"[{type(self).prefixCls}] Rejection for Third party client session failed ")

            # Verifying Third party client session with valid users of different groups
            self.logger.newStep("2. Verifying thirdPrtyClientObj session with valid users of different groups")

            # Iterating and verifying connection for every user data (stored in commonConstants)
            for _ , userData in commonConstants.USERS_DETAILS_DICT_SECURITY_TEST.items():
                self.logger.newStep(f"[{type(self).prefixCls}] Verifying third party python connection for user of "
                                    f"{userData['group']} group", level = 3)

                verificationResult = self.swtchUsrAndValConnection(
                    clientObj = thirdPrtyClientObj, userName = userData['userName'],
                    baseEncPassword = userData['password'], connectionExpectedFlag = True)

                testResult = testResult and verificationResult

            # Verifying Third party python session with invalid username and correct password for all users
            self.logger.newStep("3. Verifying Third party python session with invalid users"
                                "(wrong user name and correct password) of different groups")
            for user, userData in commonConstants.USERS_DETAILS_DICT_SECURITY_TEST.items():
                self.logger.newStep(f"[{type(self).prefixCls}] Verifying Third party python connection for {user} "
                                    "with wrong user name", level = 3)

                verificationResult = self.swtchUsrAndValConnection(
                    clientObj = thirdPrtyClientObj, userName = constants.SECURITY_TEST_INVALID_USERNAME,
                    baseEncPassword = userData['password'], connectionExpectedFlag = False)

                testResult = testResult and verificationResult

            # Verifying Third party python session with correct username and invalid password for all users
            self.logger.newStep("4. Verifying Third party python session with invalid users"
                                "(correct user name and wrong password) of different groups")
            for user, userData in commonConstants.USERS_DETAILS_DICT_SECURITY_TEST.items():
                self.logger.newStep(f"[{type(self).prefixCls}] Verifying Third party python connection for {user} "
                                    "with wrong password", level = 3)

                verificationResult = self.swtchUsrAndValConnection(
                    clientObj = thirdPrtyClientObj, userName = userData['userName'],
                    baseEncPassword = constants.SECURITY_TEST_INVALID_PASSWORD,
                    connectionExpectedFlag = False)

                testResult = testResult and verificationResult

            # Verifying Third party python session with wrong username and wrong password
            self.logger.newStep("5. Verifying Third party python session with wrong username and wrong password")
            verificationResult = self.swtchUsrAndValConnection(
                clientObj = thirdPrtyClientObj, userName = constants.SECURITY_TEST_INVALID_USERNAME,
                baseEncPassword = constants.SECURITY_TEST_INVALID_PASSWORD,
                connectionExpectedFlag = False)

            testResult = testResult and verificationResult

            # Closing Third party python session
            self.closeSessionAndValidate(clientObj = thirdPrtyClientObj)
            return testResult

        except Exception:
            if thirdPrtyClientObj:
                thirdPrtyClientObj.closeSession()

            return False

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def req_23_Grp_04_test_07(self) -> bool:

        self.testCase.skip("The testcase for x510 is skipped as a issue is observed with x510 session due to a reason "
                           "where connection is expected to be rejected when x510 occupies about 8 sessions")

        x510Obj = None

        try:
            # This testcase for x510 is commented as a issue is observed with x510 session
            # i.e In the cases where connection is expected to be rejected.. x510 occupies about 8 sessions
            #
            # x510 object
            x510Obj = self.getClientObject(clientType = commonConstants.X510_NAME)

            # x510 session
            self.logger.newStep("1. Verifying Rejection of x510 Anonymous Session")
            self.occupySession(clientObj = x510Obj)
            testResult = self.validateSessionDetails(lstOfActiveClientObjs = [x510Obj])
            if testResult:
                self.logger.newStep("Successfully verified rejection of x510 session for Anonymous user")
            else:
                self.logger.error(f"[{type(self).prefixCls}] Rejection for x510 session failed ")

            # Defining list of groups for which the connection is expected
            connExpectedForGrpsLi = ["Administrator", "Engineering"]

            # Verifying x510 session with valid users of different groups
            self.logger.newStep("2. Verifying x510 session with valid users of different groups")
            # Iterating and verifying connection for every user data (stored in commonConstants)
            for _ , userData in commonConstants.USERS_DETAILS_DICT_SECURITY_TEST.items():
                connectionExpectedFlag = False
                self.logger.newStep(f"[{type(self).prefixCls}] Verifying x510 connection for user of"
                                    f"{userData['group']} group", level = 3)

                if userData['group'] in connExpectedForGrpsLi:
                    connectionExpectedFlag = True

                verificationResult = self.swtchUsrAndValConnection(
                    clientObj = x510Obj, userName = userData['userName'],
                    baseEncPassword = userData['password'], connectionExpectedFlag = connectionExpectedFlag)

                testResult = testResult and verificationResult

            # Verifying x510 session with invalid username and correct password for all users
            self.logger.newStep("3. Verifying x510 session with invalid users "
                                "(wrong user name and correct password) of different groups")
            for user, userData in commonConstants.USERS_DETAILS_DICT_SECURITY_TEST.items():
                self.logger.newStep(f"[{type(self).prefixCls}] Verifying x510 connection for {user} with wrong user "
                                    "name", level = 3)

                verificationResult = self.swtchUsrAndValConnection(
                    clientObj = x510Obj, userName = constants.SECURITY_TEST_INVALID_USERNAME,
                    baseEncPassword = userData['password'], connectionExpectedFlag = False)

                testResult = testResult and verificationResult

            # Verifying x510 session with correct username and invalid password for all users
            self.logger.newStep("4. Verifying x510 session with invalid users "
                                "(correct user name and wrong password) of different groups")
            for user, userData in commonConstants.USERS_DETAILS_DICT_SECURITY_TEST.items():
                self.logger.newStep(f"[{type(self).prefixCls}] Verifying x510 connection for {user} "
                                    "with wrong password", level = 3)

                verificationResult = self.swtchUsrAndValConnection(
                    clientObj = x510Obj, userName = userData['userName'],
                    baseEncPassword = constants.SECURITY_TEST_INVALID_PASSWORD,
                    connectionExpectedFlag = False)

                testResult = testResult and verificationResult

            # Verifying x510 session with wrong username and wrong password
            self.logger.newStep("5. Verifying x510 session with wrong username and wrong password")
            verificationResult = self.swtchUsrAndValConnection(
                clientObj = x510Obj, userName = constants.SECURITY_TEST_INVALID_USERNAME,
                baseEncPassword = constants.SECURITY_TEST_INVALID_PASSWORD,
                connectionExpectedFlag = False)

            testResult = testResult and verificationResult

            # Closing x510 session
            self.closeSessionAndValidate(clientObj = x510Obj)
            return testResult

        except Exception:
            if x510Obj:
                x510Obj.closeSession()

            return False

    #-------------------------------------------------------------------------------------------------------------------
    def req_23_Grp_04_test_99_post(self) -> Any:
        # Handle No connection to the device popup if appeared
        Lib_UserMgmt_ES.PLCD_OBJECT.handlePLCConnectionLost(header = self.configXlsObj.plcheader)

        # Disabling Anonymous User login
        Lib_UserMgmt_ES.PLCD_OBJECT.enableOrDisableAnonymousUserLogin(
            projName = commonConstants.PLC_PROJ_NAME, disableFlag = True,
            userName = commonConstants.USERS_DETAILS_DICT_SECURITY_TEST['administratorUser']['userName'],
            base64EncryptedPassword = commonConstants.USERS_DETAILS_DICT_SECURITY_TEST['administratorUser']['password'])

        # Refreshing users and group
        Lib_UserMgmt_ES.PLCD_OBJECT.checkIfUserManagementEnabled(projName = commonConstants.PLC_PROJ_NAME)

        # ENabling Anonymous User login
        Lib_UserMgmt_ES.PLCD_OBJECT.enableOrDisableAnonymousUserLogin(
            projName = commonConstants.PLC_PROJ_NAME,
            userName = commonConstants.USERS_DETAILS_DICT_SECURITY_TEST['administratorUser']['userName'],
            base64EncryptedPassword = commonConstants.USERS_DETAILS_DICT_SECURITY_TEST['administratorUser']['password'])

        # Refreshing users and group
        Lib_UserMgmt_ES.PLCD_OBJECT.checkIfUserManagementEnabled(projName = commonConstants.PLC_PROJ_NAME)

        if Lib_OpcUa_Base.dummy3rdPrtyPyClientObj:
            Lib_OpcUa_Base.dummy3rdPrtyPyClientObj.closeSession()

    #-------------------------------------------------------------------------------------------------------------------
    def req_23_Grp_05_test_00_pre(self) -> Any:
        """
        Pre verify connection to controller with Anonymous user diasabled, user management activated and changed
        EngineeringItf credential
        """

        self.pre_setUp()

        self.logger.info(f"[{type(self).prefixCls}] PREREQUISITE Steps".format())

        # Activating user management
        self.logger.newStep(f"[{type(self).prefixCls}] Step 1. Activating user management and adding users",
                            level = 3)
        if not Lib_UserMgmt_ES.PLCD_OBJECT.activateUsrMgmtAndAddAdminUsr(
                projName = commonConstants.PLC_PROJ_NAME,
                adminData = commonConstants.USERS_DETAILS_DICT_SECURITY_TEST['administratorUser']):
            raise Exception("User Management is not activated")

        # Add users
        usersAddedStatus = Lib_UserMgmt_ES.PLCD_OBJECT.addUsersInUserAndGroups(
            userData = commonConstants.USERS_DETAILS_DICT_SECURITY_TEST, projName = commonConstants.PLC_PROJ_NAME)
        if not usersAddedStatus:
            raise Exception("Failed to add users in user management")

        # Change EngineeringItf default credentials
        self.logger.newStep(f"[{type(self).prefixCls}] Step 2. Change EngineeringItf default credentials",
                            level = 3)
        editUserStatus = Lib_UserMgmt_ES.PLCD_OBJECT.changeUserPassword(
            projName = commonConstants.PLC_PROJ_NAME, userName = "EngineeringItf",
            newBase64EncPwd = constants.SECURITY_TEST_CHANGED_ENG_ITF_PWD)
        if not editUserStatus:
            raise Exception("Failed to change Engineering Itf credentials")

        # Stopping sync mode in Users and Groups
        self.logger.newStep(f"[{type(self).prefixCls}] Step 3. Stop Synchronization mode", level = 3)
        if not Lib_UserMgmt_ES.PLCD_OBJECT.stopSyncModeInUsersAndGroups():
            raise Exception("Failed to stop sync mode in Users and Groups Tab")

        # Setting Modify, View, Execute Access to EasyUi Interface
        self.logger.newStep(f"[{type(self).prefixCls}] Step 4. Setting Modify, View, Execute Access to EasyUi "
                            "Interface", level = 3)
        if not Lib_UserMgmt_ES.PLCD_OBJECT.grantAccessRightsFromFile(
                drmFileName = constants.DEVICE_RIGHT_MANAGEMENT_FILE_NAME,
                drmFilePath = constants.SECURITY_TEST_INPUT_FILES,
                projname = commonConstants.PLC_PROJ_NAME):
            raise Exception("Access Rights not set for EasyUi Interface")

        # Stop sync mode
        self.logger.newStep(f"[{type(self).prefixCls}] Step 5. Stop Synchronization mode in Access Rights tab",
                            level = 3)
        if not Lib_UserMgmt_ES.PLCD_OBJECT.stopSyncModeInAccessRights():
            raise Exception("Failed to stop sync mode")

        # Reboot controller
        self.logger.newStep(f"[{type(self).prefixCls}] Step 5. Reboot Controller", level = 3)
        if not self.restartController():
            raise Exception("Failed to reboot the controller")

        self.logger.info("Waiting for 60 secs, for OPC Ua Server to restart before connection with Pytef Client")
        userSleep(60)

        # Third party client 1 object
        self.logger.newStep(f"[{type(self).prefixCls}] Step 8. Occupying dummy 3rd party session", level = 3)
        Lib_OpcUa_Base.dummy3rdPrtyPyClientObj = self.getClientObject(clientType = commonConstants.PYTEF_CLIENT_NAME)

        # Connecting dummy 3rd party client
        if not self.occupySession(clientObj = Lib_OpcUa_Base.dummy3rdPrtyPyClientObj):
            self.logger.info(f"[{type(self).prefixCls}] Waiting 5 sec and trying again")
            userSleep(5)
            if not self.occupySession(clientObj = Lib_OpcUa_Base.dummy3rdPrtyPyClientObj):
                raise Exception("Failed to connect dummy third party connection")

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def req_23_Grp_05_test_01(self) -> bool:

        easyStarterObj = None

        try:
            # EasyStarter object
            easyStarterObj = self.getClientObject(clientType = commonConstants.EASY_STARTER_NAME)

            # Easy Starter sessions
            self.logger.newStep("1. Verifying Rejection of Easy Starter Anonymous Session")
            self.occupySession(clientObj = easyStarterObj)
            testResult = self.validateSessionDetails(lstOfActiveClientObjs = [])
            if testResult:
                self.logger.newStep("Successfully verified rejection of Easy Starter session for Anonymous user")
            else:
                self.logger.error(f"[{type(self).prefixCls}] Rejection for Easy Starter session failed ")

            # Defining list of groups for which the connection is expected
            connExpectedForGrpsLi = ["Administrator", "Engineering"]

            # Verifying Easy Starter session with valid users of different groups
            self.logger.newStep("2. Verifying Easy Starter session with valid users of different groups")
            # Iterating and verifying connection for every user data (stored in commonConstants)
            for _ , userData in commonConstants.USERS_DETAILS_DICT_SECURITY_TEST.items():
                connectionExpectedFlag = False
                self.logger.newStep(f"[{type(self).prefixCls}] Verifying Easy Starter connection for user of "
                                    f"{userData['group']} group", level = 3)

                if userData['group'] in connExpectedForGrpsLi:
                    connectionExpectedFlag = True

                verificationResult = self.swtchUsrAndValConnection(
                    clientObj = easyStarterObj, userName = userData['userName'],
                    baseEncPassword = userData['password'], connectionExpectedFlag = connectionExpectedFlag)

                testResult = testResult and verificationResult

            # Verifying Easy Starter session with invalid username and correct password for all users
            self.logger.newStep("3. Verifying EasyStarter session with invalid users (wrong user name and correct "
                                "password) of different groups")
            for user, userData in commonConstants.USERS_DETAILS_DICT_SECURITY_TEST.items():
                connectionExpectedFlag = False
                self.logger.newStep(f"[{type(self).prefixCls}] Verifying Easy Starter connection for {user} "
                                    "with wrong user name", level = 3)

                verificationResult = self.swtchUsrAndValConnection(
                    clientObj = easyStarterObj, userName = constants.SECURITY_TEST_INVALID_USERNAME,
                    baseEncPassword = userData['password'], connectionExpectedFlag = False)

                testResult = testResult and verificationResult

            # Verifying Easy Starter session with correct username and invalid password for all users
            self.logger.newStep("4. Verifying EasyStarter session with invalid users (correct user name and "
                                "wrong password) of different groups")
            for user, userData in commonConstants.USERS_DETAILS_DICT_SECURITY_TEST.items():
                connectionExpectedFlag = False
                self.logger.newStep(f"[{type(self).prefixCls}] Verifying Easy Starter connection for {user} "
                                    "with wrong password", level = 3)

                verificationResult = self.swtchUsrAndValConnection(
                    clientObj = easyStarterObj, userName = userData['userName'],
                    baseEncPassword = constants.SECURITY_TEST_INVALID_PASSWORD,
                    connectionExpectedFlag = False)

                testResult = testResult and verificationResult

            # Verifying Easy Starter session with wrong username and wrong password
            self.logger.newStep("5. Verifying EasyStarter session with wrong username and wrong password")
            verificationResult = self.swtchUsrAndValConnection(
                clientObj = easyStarterObj, userName = constants.SECURITY_TEST_INVALID_USERNAME,
                baseEncPassword = constants.SECURITY_TEST_INVALID_PASSWORD,
                connectionExpectedFlag = False)

            testResult = testResult and verificationResult

            # Closing Easy Starter session
            self.closeSessionAndValidate(clientObj = easyStarterObj)
            return testResult

        except Exception:
            if easyStarterObj:
                easyStarterObj.closeSession()

            return False

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def req_23_Grp_05_test_02(self) -> bool:

        appLoaderObj = None

        try:
            # ApplicationLoader object
            appLoaderObj = self.getClientObject(clientType = commonConstants.APPLICATION_LOADER_NAME)

            # ApplicationLoader sessions
            self.logger.newStep("1. Verifying Rejection of ApplicationLoader Anonymous Session")
            self.occupySession(clientObj = appLoaderObj)
            testResult = self.validateSessionDetails(lstOfActiveClientObjs = [])
            if testResult:
                self.logger.newStep("Successfully verified rejection of ApplicationLoader session for Anonymous user")
            else:
                self.logger.error(f"[{type(self).prefixCls}] Rejection for ApplicationLoader session failed ")

            # Defining list of groups for which the connection is expected
            connExpectedForGrpsLi = ["Administrator", "Engineering"]

            # Verifying ApplicationLoader session with valid users of different groups
            self.logger.newStep("2. Verifying ApplicationLoader session with valid users of different groups")
            # Iterating and verifying connection for every user data (stored in commonConstants)
            for _ , userData in commonConstants.USERS_DETAILS_DICT_SECURITY_TEST.items():
                connectionExpectedFlag = False
                self.logger.newStep(f"[{type(self).prefixCls}] Verifying ApplicationLoader connection for user of "
                                    f"{userData['group']} group", level = 3)

                if userData['group'] in connExpectedForGrpsLi:
                    connectionExpectedFlag = True

                verificationResult = self.swtchUsrAndValConnection(
                    clientObj = appLoaderObj, userName = userData['userName'],
                    baseEncPassword = userData['password'], connectionExpectedFlag = connectionExpectedFlag)

                testResult = testResult and verificationResult

            # Verifying ApplicationLoader session with invalid username and correct password for all users
            self.logger.newStep("3. Verifying ApplicationLoader session with invalid users (wrong user name and "
                                "correct password) of different groups")
            for user, userData in commonConstants.USERS_DETAILS_DICT_SECURITY_TEST.items():
                self.logger.newStep(f"[{type(self).prefixCls}] Verifying ApplicationLoader connection for {user} "
                                    "with wrong user name", level = 3)

                verificationResult = self.swtchUsrAndValConnection(
                    clientObj = appLoaderObj, userName = constants.SECURITY_TEST_INVALID_USERNAME,
                    baseEncPassword = userData['password'], connectionExpectedFlag = False)

                testResult = testResult and verificationResult

            # Verifying ApplicationLoader session with correct username and invalid password for all users
            self.logger.newStep("4. Verifying ApplicationLoader session with invalid users"
                                " (correct user name and wrong password) of different groups")
            for user, userData in commonConstants.USERS_DETAILS_DICT_SECURITY_TEST.items():
                self.logger.newStep(f"[{type(self).prefixCls}] Verifying ApplicationLoader connection for {user} "
                                    "with wrong password", level = 3)

                verificationResult = self.swtchUsrAndValConnection(
                    clientObj = appLoaderObj, userName = userData['userName'],
                    baseEncPassword = constants.SECURITY_TEST_INVALID_PASSWORD,
                    connectionExpectedFlag = False)

                testResult = testResult and verificationResult

            # Verifying ApplicationLoader session with wrong username and wrong password
            self.logger.newStep("5. Verifying ApplicationLoader session with wrong username and wrong password")
            verificationResult = self.swtchUsrAndValConnection(
                clientObj = appLoaderObj, userName = constants.SECURITY_TEST_INVALID_USERNAME,
                baseEncPassword = constants.SECURITY_TEST_INVALID_PASSWORD,
                connectionExpectedFlag = False)

            testResult = testResult and verificationResult

            # Closing ApplicationLoader session
            self.closeSessionAndValidate(clientObj = appLoaderObj)
            return testResult

        except Exception:
            if appLoaderObj:
                appLoaderObj.closeSession()

            return False

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def req_23_Grp_05_test_03(self) -> bool:

        firmwareLoaderObj = None

        try:
            # Firmware Loader object
            firmwareLoaderObj = self.getClientObject(clientType = commonConstants.FIRMWARE_LOADER_NAME)

            # Firmware Loader session
            self.logger.newStep("1. Verifying Rejection of Firmware Loader Anonymous Session")
            self.occupySession(clientObj = firmwareLoaderObj)
            testResult = self.validateSessionDetails(lstOfActiveClientObjs = [])
            if testResult:
                self.logger.newStep("Successfully verified rejection of Firmware Loader session for Anonymous user")
            else:
                self.logger.error(f"[{type(self).prefixCls}] Rejection for Firmware Loader session failed ")

            # Defining list of groups for which the connection is expected
            connExpectedForGrpsLi = ["Administrator", "Engineering"]

            # Verifying Firmware Loader session with valid users of different groups
            self.logger.newStep("2. Verifying Firmware Loader session with valid users of different groups")
            # Iterating and verifying connection for every user data (stored in commonConstants)
            for _ , userData in commonConstants.USERS_DETAILS_DICT_SECURITY_TEST.items():
                connectionExpectedFlag = False
                self.logger.newStep(f"[{type(self).prefixCls}] Verifying Firmware Loader connection for user of "
                                    f"{userData['group']} group", level = 3)

                if userData['group'] in connExpectedForGrpsLi:
                    connectionExpectedFlag = True

                verificationResult = self.swtchUsrAndValConnection(
                    clientObj = firmwareLoaderObj, userName = userData['userName'],
                    baseEncPassword = userData['password'], connectionExpectedFlag = connectionExpectedFlag)

                if not self.waitForFWLoaderSessionToClose(firmwareLoaderObj = firmwareLoaderObj):
                    testResult = False

                testResult = testResult and verificationResult

            # Verifying Firmware Loader session with invalid username and correct password for all users
            self.logger.newStep("3. Verifying Firmware Loader session with invalid users"
                                "(wrong user name and correct password) of different groups")
            for user, userData in commonConstants.USERS_DETAILS_DICT_SECURITY_TEST.items():
                self.logger.newStep(f"[{type(self).prefixCls}] Verifying Firmware Loader connection for {user} with "
                                    "wrong user name", level = 3)

                verificationResult = self.swtchUsrAndValConnection(
                    clientObj = firmwareLoaderObj, userName = constants.SECURITY_TEST_INVALID_USERNAME,
                    baseEncPassword = userData['password'], connectionExpectedFlag = False)

                testResult = testResult and verificationResult

            # Verifying Firmware Loader session with correct username and invalid password for all users
            self.logger.newStep("4. Verifying Firmware Loader session with invalid users"
                                "(correct user name and wrong password) of different groups")
            for user, userData in commonConstants.USERS_DETAILS_DICT_SECURITY_TEST.items():
                self.logger.newStep(f"[{type(self).prefixCls}] Verifying Firmware Loader connection for {user} with "
                                    "wrong password", level = 3)

                verificationResult = self.swtchUsrAndValConnection(
                    clientObj = firmwareLoaderObj, userName = userData['userName'],
                    baseEncPassword = constants.SECURITY_TEST_INVALID_PASSWORD,
                    connectionExpectedFlag = False)

                testResult = testResult and verificationResult

            # Verifying Firmware Loader session with wrong username and wrong password
            self.logger.newStep("5. Verifying Firmware Loader session with wrong username and wrong password")
            verificationResult = self.swtchUsrAndValConnection(
                clientObj = firmwareLoaderObj, userName = constants.SECURITY_TEST_INVALID_USERNAME,
                baseEncPassword = constants.SECURITY_TEST_INVALID_PASSWORD,
                connectionExpectedFlag = False)

            testResult = testResult and verificationResult
            return testResult

        except Exception:
            if firmwareLoaderObj:
                firmwareLoaderObj.closeSession()

            return False

    #-------------------------------------------------------------------------------------------------------------------
    def req_23_Grp_05_test_99_post(self) -> Any:
        if Lib_OpcUa_Base.dummy3rdPrtyPyClientObj:
            Lib_OpcUa_Base.dummy3rdPrtyPyClientObj.closeSession()
