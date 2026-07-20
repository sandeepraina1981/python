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
import os
import math
import re
import random
import string
import socket
import time
from typing import Any, List, Optional, Union
from lenze.drivers import OpcUaClient
from opcua import ua
from pytef.namespace.testlib import (FwTestLib, Version, Result, autobehavior, IpcFilter, IpcLenzeC520, IpcLenzeC550,
                                     VisibleString, Boolean, Unsigned32, tyOptBehavior)
from pytef.resource.device.ipc.alpharelease import IpcLenzeC430
from tests.opc_ua.opc_ua_llm_test.core.LLM_PLCD import LLM_PLC
from tests.testlib.seleniumLib.lenze_diagnosis_tool.LenzeDiagnosisTool import LenzeDiagnosis
from tests.opc_ua.opc_ua_llm_test.utils import constants_llm as constants
from tests.opc_ua.opc_ua_llm_test.utils.excelReader import ConfigExlParser
from tests.opc_ua.opc_ua_llm_test.utils.excelReportUpdater import ReportExlParser
from tests.testlib.utils.CommonLib import clsLogger, takeScreenshot
from tests.testlib.lib_pywinauto.ua_expert.UaExpert import UaExpert
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
class Lib_OpcUa_LLM(FwTestLib):
    """
        OPC UA Security Test Lib
    """
    prefixCls = 'Lib_OpcUa_LLM'
    __LIB_DICT = {}

    LIB_NAME = "Lib_OpcUa_LLM"
    LIB_VERSION = Version(1, 0, 0)
    PLCD_OBJECT = None

    #-------------------------------------------------------------------------------------------------------------------
    def __init__(self) -> None:
        """
        Constructor
        """
        self.logger.info("[%s] in Lib_OpcUa_LLM::__init__()", type(self).prefixCls)
        super().__init__()
        self.ipc = None
        self.defaultChannel = None
        self.ioPins = []

        # Creating IPC obj
        try:
            ipcFilter = IpcFilter(ipcClass = [IpcLenzeC520, IpcLenzeC550, IpcLenzeC430])
            self.ipc = self.testCase.resource.ipc(ipcFilter = ipcFilter, number = 1)[0]

            self.logger.info(f"[{type(self).prefixCls}] List of ipc {self.ipc} ")
            self.defaultChannel = self.ipc.getDefaultChannel()
            # Save controller IP address
            self.controllerIP = self.ipc.channelList[0].address

            self.ioPins = self.testCase.resource.ioPin(resException = False)

        except Exception:  # pylint: disable=broad-exception-caught
            self.testCase.skipTest("Failed to create ipc object")

        self.xlsReaderObj = ConfigExlParser(configFile = constants.CONFIG_FILE_PATH, logger = self.logger)
        self.reportUpdaterObj = ReportExlParser(reportFile = constants.REPORT_FILE_PATH,
                                                sheetName = constants.REPORT_SHEET_NAME,
                                                logger = self.logger)

    #-------------------------------------------------------------------------------------------------------------------
    @classmethod
    def createTests(cls, testcls) -> None:
        """
        Auto create tests at runtime.

        Let the base class do the job
        """
        logger = clsLogger()
        xlsReaderObj = ConfigExlParser(configFile = constants.CONFIG_FILE_PATH, logger = logger)

        tests = [tcName for tcName in dir(testcls) if 'tc_' in tcName]

        for testMethodName in tests:
            tcParam = {}
            tcParam['funcName'] = testMethodName

            try:
                _regextcmatch = re.match("tc_(.*)", testMethodName)
                testName = _regextcmatch.group(1)
                grpName = testName.split("_")[0]
                tcName = testName.split("_")[1]
                spiraId = int(xlsReaderObj.testCaseSelectionDict.get(grpName).get(tcName).get("spira"))
                executeFlag = xlsReaderObj.testCaseSelectionDict.get(grpName).get(tcName).get("execute")
                if executeFlag:
                    tcParam['@spiratest_tcIdList'] = [(None, [spiraId])]

                    testCaseName = f"test_opc_llm_{xlsReaderObj.controllerType}_{testName}"

                    testcls.addTestCase(name = testCaseName,
                                        func = getattr(testcls, testMethodName),
                                        tcParam = tcParam)
                else:
                    logger.info("[%s] Test case %s with spira : %s not selected for test",
                                cls.prefixCls, testMethodName, spiraId)
            except Exception:  # pylint: disable=broad-exception-caught

                logger.exception("[%s] Test case %s is not selected for execution...", cls.prefixCls, testMethodName)

    #-------------------------------------------------------------------------------------------------------------------
    @autobehavior
    def setUpClass(self, behavior: tyOptBehavior = None, **kwargs) -> Result:
        """
        Method to setup the library content (allocated resources).

        The method can be called form the <testcase>.setUpClass() to setup all allocated resources.

        :param behavior:  Auto behavior of this method.
        :returns: Result
        """
        # Creating PLCD object
        plcObj = LLM_PLC(logger = self.logger)

        # Storing PLC object at class level
        Lib_OpcUa_LLM.PLCD_OBJECT = plcObj
        # plcObj.header = 'PLC Designer ' + self.xlsReaderObj.plcVersion
        # plcObj.connectToRunningPLC(version = self.xlsReaderObj.plcVersion)
        #
        # return Result(errorCode = Result.NO_ERROR,
        #               errorMessage = "Success")

        # Starting the PLCD tool and opening OPC UA LLM project in it
        self.logger.newStep("1. Start PLCD tool and open OPC UA LLM project")
        fullProjPath = os.path.join(os.getcwd(), constants.PLC_PROJ_PATH.format(self.xlsReaderObj.controllerType))
        if not plcObj.startPlcAndOpenProj(version = self.xlsReaderObj.plcVersion,
                                          projPath = fullProjPath,
                                          projName = constants.PLC_PROJ_NAME, ignoreUpdatesFlag = True):
            self.testCase.skip("Failed to start PLC tool and open OPC UA LLM project")

        # Performing 'Clean all' operation on the project
        self.logger.newStep("2. Performing Clean All")
        if not plcObj.cleanAllBuild(projName = constants.PLC_PROJ_NAME):
            self.testCase.skip("Failed to perform clean all operation")

        # Performing 'Build' operation on the project
        self.logger.newStep("3. Building the project")
        if not plcObj.buildProject(projName = constants.PLC_PROJ_NAME):
            self.testCase.skip("Failed to build the project", self.controllerIP)

        # Going offline with the controller
        self.logger.newStep("4. Expanding project devices")
        if not plcObj.expandPLCDProjectDevices(projName = constants.PLC_PROJ_NAME):
            self.testCase.skip("Failed to expand PLC project devices")

        # Selecting the required controller from the gateway
        self.logger.newStep("5. Selecting required controller")
        if not plcObj.selectController(ipAddress = self.controllerIP,
                                       projName = constants.PLC_PROJ_NAME):
            self.testCase.skip(f"Failed to select required controller with IP address : {self.controllerIP}")

        # Downloading application to the controller
        self.logger.newStep("6. Downloading application to the controller")
        if not plcObj.goOnline():
            self.testCase.skip("Failed to download application to the controller")

        if not plcObj.goOffline(projName = constants.PLC_PROJ_NAME, header = plcObj.header):
            raise Exception("Failed to Go offline in plcd porject ")

        # Disconnecting IPC before going online as Application credit assignment in the controller and in the PLCD
        # project might be different
        self.ipc.disconnect()

        # Setting pub sub activation to Disabled
        self.logger.newStep("7. Setting Pub Sub Activation value to Disabled")
        paramIdx, paramSubIdx = constants.PUB_SUB_ACTIVATION_PARAM_STR.split(':')
        param = self.ipc.objByIdx(index = int(paramIdx, 16), subIndex = int(paramSubIdx))
        result = param.setValue(constants.PUB_SUB_ACTIVATION_DISABLE_VALUE)
        if not result.isOK:
            raise Exception("Failed to set Pub Sub Activation to Disabled")

        try:
            self.ipc.cmd.paramSave()
        except Exception:  # pylint: disable=broad-exception-caught
            self.logger.newStep("Param save failed")

        # Downloading application to the controller
        self.logger.newStep("8. Downloading application to the controller")
        if not plcObj.goOnline(upload = True):
            self.testCase.skip("Failed to download application to the controller")

        # Creating online boot project
        self.logger.newStep("9. Create online boot project")
        if not plcObj.createBootProject(projName = constants.PLC_PROJ_NAME):
            self.testCase.skip("Failed to create online boot project")

        if not plcObj.goOffline(projName = constants.PLC_PROJ_NAME, header = plcObj.header):
            raise Exception("Failed to Go offline in plcd porject ")

        # Rebooting the controller
        self.logger.newStep("10. Reboot controller")
        if not self.restartController():
            self.testCase.skip("Failed to reboot the controller")

        # Selecting the controller after controller is rebooted the gateway
        self.logger.newStep("11. Selecting required controller after rebooting")
        if not plcObj.selectController(ipAddress = self.controllerIP,
                                       projName = constants.PLC_PROJ_NAME):
            self.testCase.skip(f"Failed to select required controller with IP address : {self.controllerIP}")

        # Deleting the Pub Sub configuration from Ua Expert
        self.logger.newStep("12. Deleting the exisiting pub sub config from controller using Ua Expert")
        self._dwnldOrDeletePubSubConfigToCtrl(downloadFlag = False)

        # Updating Report header with controller type and current release name
        newRprtHeader = constants.REPORT_HEADER.format(self.xlsReaderObj.controllerType, self.xlsReaderObj.releaseName)
        self.logger.info("[%s] Updating Report Header with '%s'", type(self).prefixCls, newRprtHeader)
        if not self.reportUpdaterObj.updateReportHeader(header = newRprtHeader):
            self.logger.warning("[%s] Failed to update report header..", type(self).prefixCls)

        # Below code is only added for fast testing.. Remove below code and uncomment the above code before committing
        # plcObj.connectToRunningPLC(version = self.xlsReaderObj.plcVersion)

        return Result(errorCode = Result.NO_ERROR,
                      errorMessage = "Success")

    #-------------------------------------------------------------------------------------------------------------------
    @autobehavior
    def tearDownClass(self, behavior: tyOptBehavior = None, **kwargs) -> Result:
        """
        Method to cleanup the library content (used resources).

        The method can be called form the <testcase>.tearDownClass() to cleanup all used resources.

        :param behavior:  Auto behavior of this method.
        :returns: Result

        """
        # Closing PLC tool after test completion
        self.logger.newStep("Close PLCD tool", level = 3)
        if not Lib_OpcUa_LLM.PLCD_OBJECT.closePLC(projName = constants.PLC_PROJ_NAME,
                                                  header = Lib_OpcUa_LLM.PLCD_OBJECT.header,
                                                  saveFlag = False):
            self.logger.warning("[%s] Close PLC Failed...", type(self).prefixCls)

        return Result(errorCode = Result.NO_ERROR,
                      errorMessage = "Success")

    #-------------------------------------------------------------------------------------------------------------------
    @autobehavior
    def setUp(self, behavior: tyOptBehavior = None, **kwargs) -> Result:
        """
        Method to setup the library content (internal structures).

        The method can be called form the <testcase>.setUp() to setup all library internal structures.

        :param behavior:  Auto behavior of this method.
        :returns: Result
        """
        return Result(errorCode = Result.NO_ERROR,
                      errorMessage = "Success")

    #-------------------------------------------------------------------------------------------------------------------
    @autobehavior
    def tearDown(self, behavior: tyOptBehavior = None, **kwargs) -> Result:
        """
        Method to cleanup the library content (internal structures).

        The method can be called form the <testcase>.tearDown() to cleanup all internal structures.

        :param behavior:  Auto behavior of this method.
        :returns:         Result

        """
        plcObj = Lib_OpcUa_LLM.PLCD_OBJECT
        if not plcObj.goOffline(projName = constants.PLC_PROJ_NAME, header = plcObj.header):
            self.logger.warning("[%s] Failed to go offline", type(self).prefixCls)
        return Result(errorCode = Result.NO_ERROR,
                      errorMessage = "Success")

    #-------------------------------------------------------------------------------------------------------------------
    def restartController(self) -> bool:
        """
        This method is used to restart the controller
        """
        self.logger.info("[%s] Restarting the controller",  type(self).prefixCls)
        result = self.ipc.waitUntilBooted(switchOff = True,
                                          switchOn  = True,
                                          channel   = self.ipc.getDefaultChannel())
        if not result.isOK:
            self.logger.error(
                "[%s] Failed to reboot the controller.. deleting cache from Pytef works and trying again",
                type(self).prefixCls)
            return False
        self.logger.info("[%s] Controller Restarted successfully", type(self).prefixCls)
        return True

    #-------------------------------------------------------------------------------------------------------------------
    def _validateExtPkg(self, extPkgExpectedFlag: bool) -> bool:
        """
        This method is used to check and validate if extended packages is activated or not using Diagnosis tool
        """
        diagTool = None
        try:
            self.logger.info("[%s] Checking if extended package is activated or not", type(self).prefixCls)
            if extPkgExpectedFlag:
                self.logger.info("[%s] Extended package is expected", type(self).prefixCls)
            else:
                self.logger.info("[%s] Extended package is not expected", type(self).prefixCls)

            # Object for Lenze Diagnosis Tool
            diagTool = LenzeDiagnosis(logger = self.logger)

            # Retry is added as it is observed that sometimes contents on License Manager do not load
            # Even after waiting for 60 seconds or after switching tabs
            retryCount = 5
            for retry in range(retryCount):
                # Starting Lenze Diagnosis tool
                if diagTool.startLenzeDiagnosisTool(ipAddress = self.controllerIP,
                                                    userName = constants.DIAGNOSIS_USERNAME,
                                                    base64EncryptedPassword = constants.DIAGNOSIS_BASE64_PWD):
                    # Opening License Manager
                    if diagTool.openLicenseManagerTab():
                        if diagTool.waitForLicenseManContentsToLoad():
                            self.logger.info("[%s] Reading extended packages message", type(self).prefixCls)
                            extPackMsg = diagTool.readExtendedPackagesMsg()
                            break

                self.logger.error(
                    "[%s] Reopening the tool and trying again to read ext packages message.. retry count: %s",
                    type(self).prefixCls, retry)
                diagTool.closeLenzeDiagnosisTool()
            else:
                self.logger.error(
                    "[%s] Failed to start Diagnosis tool and read extended messages", type(self).prefixCls)
                return False

            # Closing Lenze Diagnosis tool
            diagTool.closeLenzeDiagnosisTool()

            if extPackMsg is None:
                raise Exception("Failed to read Extended Package Status from Diagnosis tool")

            if constants.EXTENDED_PACKAGE_STR[self.xlsReaderObj.controllerType] in extPackMsg and extPkgExpectedFlag:
                self.logger.info("[%s] Extended package is activated", type(self).prefixCls)
                return True
            if extPkgExpectedFlag:
                self.logger.error("[%s] Extended package is not activated", type(self).prefixCls)
                return False
            if constants.EXTENDED_PACKAGE_STR[self.xlsReaderObj.controllerType] in extPackMsg:
                self.logger.error("[%s] Extended package is activated", type(self).prefixCls)
                return False
            self.logger.info("[%s] Extended package is not activated", type(self).prefixCls)
            return True
        except Exception:  # pylint: disable=broad-exception-caught
            self.logger.exception("[%s] Exception occurred in _validateExtPkg()", type(self).prefixCls)
            return False
        finally:
            if diagTool is not None:
                del diagTool

    #-------------------------------------------------------------------------------------------------------------------
    def _getThirdPartyClients(self, noOfReqObjs: int) -> List[OpcUaClient]:
        """
        This method is used to get required number of third party client objects in a list
        """
        try:
            # Declaring empty list variable
            objList = []
            for objNum in range(1, noOfReqObjs + 1):
                # Creating third party python client for every count and naming the object accordingly
                obj = OpcUaClient(name = constants.THIRD_PARTY_PYTHON_CLIENT_NAME.format(objNum))
                # Appending the newly created object in the list
                objList.append(obj)
        except Exception:  # pylint: disable=broad-exception-caught
            self.logger.exception("[%s] Exception occurred while creating third party python client objects",
                                  type(self).prefixCls)
        return objList

    #-------------------------------------------------------------------------------------------------------------------
    def _disconnectThirdPartyClients(self, clientObjsToDisconnectLi: List[OpcUaClient]) -> None:
        """
        This method is used to disconnect the third party clients
        """
        try:
            self.logger.newStep("Disconnecting all Third party clients", level = 3)
            for clientObj in clientObjsToDisconnectLi:
                self.logger.info("[%s] Disconnecting %s client", type(self).prefixCls, clientObj.name)
                res = clientObj.disconnect()
                if res.errorCode:
                    self.logger.error("[%s] Error occurred while disconnecting %s client : %s",
                                      type(self).prefixCls, clientObj.name, res.errorMessage)
                else:
                    self.logger.info("[%s] %s client disconnected", type(self).prefixCls, clientObj.name)
                self.logger.info("-"*120)
        except Exception:  # pylint: disable=broad-exception-caught
            self.logger.exception(
                "[%s] Exception occurred in _disconnectThirdPartyClients()", type(self).prefixCls)

    #-------------------------------------------------------------------------------------------------------------------
    def _dwnldMaxExtSessSettingInCntrl(self, maxExtSessionsToSet: int) -> bool:
        """
        This method is used to set maximum external session value in PLCD and download this setting to the controller
        """
        try:
            self.ipc.disconnect()
            self.ipc.cmd.appStart()

            # Setting max external value
            self.logger.info(
                f"[{type(self).prefixCls}] Setting max external session count param to {maxExtSessionsToSet}")
            maxExtParam = self.ipc.objByIdx(index = int("0x2471", 16), subIndex = 103)
            result = maxExtParam.setValue(maxExtSessionsToSet)
            if not result.isOK:
                self.logger.error(f"[{type(self).prefixCls}] Failed to set max ext session val parameter")
                return False

            # Restart with current vals
            self.logger.info(f"[{type(self).prefixCls}] Start UA Server Restart")
            resServerParam = self.ipc.objByIdx(index = int("0x2470", 16), subIndex = 1)
            result = resServerParam.setValue(1)
            if not result.isOK:
                self.logger.error(f"[{type(self).prefixCls}] Failed to start restart server using param")
                return False
            self.ipc.disconnect()
            time.sleep(60)
            timeout = 120
            while timeout:
                try:
                    res = resServerParam.getValue()
                    if res.value == 0:
                        self.logger.info(f"[{type(self).prefixCls}] UA Server Restart Complete")
                        break
                except Exception:  # pylint: disable=broad-exception-caught
                    pass
                timeout -= 1
            else:
                self.logger.error(f"[{type(self).prefixCls}] Timeout: Restart server failed")
                return False

            self.logger.info(
                f"[{type(self).prefixCls}] Checking if max external session value {maxExtSessionsToSet} is reflected "
                "in Active Max External session count param")
            actExtParam = self.ipc.objByIdx(index = int("0x2472", 16), subIndex = 103)
            result = actExtParam.getValue()
            if not result.isOK:
                self.logger.error(f"[{type(self).prefixCls}] Failed to read active ext session val parameter")
                return False

            if result.value == maxExtSessionsToSet:
                self.logger.info(
                    f"[{type(self).prefixCls}] {result.value} value is reflected in active max session parameter")
                return True
            self.logger.error(f"[{type(self).prefixCls}] {maxExtSessionsToSet} value not reflected in active "
                              f"external session count value ({result.value})")
            return False

        except Exception:  # pylint: disable=broad-exception-caught
            self.logger.exception(
                "[%s] Exception occurred in _dwnldMaxExtSessSettingInCntrl()", type(self).prefixCls)
            return False

    #-------------------------------------------------------------------------------------------------------------------
    def _disconnectAllPLCOpenClients(self) -> bool:
        """
        This method is used to disconnect all open client connections
        """
        self.logger.info(
                    f"[{type(self).prefixCls}] Setting symbol {constants.PLC_OPEN_CLIENT_EXECUTE_CONNECT_SYMBOL_NAME} "
                    "to False to disconnect all PLC Open Client connections")
        memObj = self.ipc.plc.memObj(
                symbolName = constants.PLC_OPEN_CLIENT_EXECUTE_CONNECT_SYMBOL_NAME,
                dataType= Boolean)
        result = memObj.setValue(False)
        if not result.isOK:
            self.logger.error(
                f"[{type(self).prefixCls}] Failed to set {constants.PLC_OPEN_CLIENT_EXECUTE_CONNECT_SYMBOL_NAME} "
                "to False... Could not disconnect PLC Open client connections")
            return False
        self.ipc.cmd.appStart()
        self.logger.info(
                    f"[{type(self).prefixCls}] Successfully disconnected all the PLC Open clients")
        return True

    #-------------------------------------------------------------------------------------------------------------------
    def _connectAndVerifyConnections(self, listOfClientObjToConnect: List[OpcUaClient], noOfExpectedConn: int) -> bool:
        """
        This method is used to connect Third Party Client sessions and verify number of proper connections against
        expected count
        :param listOfClientObjToConnect: List of third party clients, on whom connection is to be performed
        :param noOfExpectedConn: Number of clients that are expected to be connected successfully
        """
        try:
            # Initializing noOfClientsConnected variable to 0
            noOfClientsConnected = 0

            self.logger.newStep(
                f"Verifying Third party client connections for Max External Sessions set to {noOfExpectedConn}")
            self.logger.info("-"*120)
            for clientObj in listOfClientObjToConnect:
                self.logger.info("[%s] Establishing %s connection", type(self).prefixCls, clientObj.name)
                try:
                    connectionResult = clientObj.connect(
                        url = constants.THIRD_PARTY_PYTHON_SERVER_URL.format(self.controllerIP),
                        namespaceStr = constants.THIRD_PARTY_PYTHON_SERVER_NAMESPACE)

                    if connectionResult.errorCode:
                        self.logger.error("[%s] Connection of %s client failed %s", type(self).prefixCls,
                                          clientObj.name,
                                          connectionResult.errorMessage)
                    else:
                        self.logger.info(
                            "[%s] Connection of %s client successful", type(self).prefixCls, clientObj.name)
                        # Incrementing noOfClientsConnected variable if connection is successful
                        noOfClientsConnected += 1
                except Exception:  # pylint: disable=broad-exception-caught
                    self.logger.exception(
                        "[%s] Connection of %s client failed", type(self).prefixCls, clientObj.name)
                self.logger.info("-"*120)

            if noOfClientsConnected == noOfExpectedConn:
                self.logger.info(
                    "[%s] No. of third party clients connected : %s == No of expected connection : %s",
                    type(self).prefixCls, noOfClientsConnected, noOfExpectedConn)
                self.logger.newStep(
                    "Verification of Third party client connections for Max External Sessions"
                    f" set to {noOfExpectedConn} is successful")
                time.sleep(5)
                return True
            self.logger.error(
                "[%s] No. of third party clients connected : %s != No of expected connection : %s",
                type(self).prefixCls, noOfClientsConnected, noOfExpectedConn)
            self.logger.error("="*180)
            self.logger.error(
                "Verification of Third party client connections for Max External Sessions set to"
                " %s failed", noOfExpectedConn)
            self.logger.error("="*180)
        except Exception:  # pylint: disable=broad-exception-caught
            self.logger.exception(
                "[%s] Exception occurred in _connectAndVerifyConnections()", type(self).prefixCls)
        return False

    #-------------------------------------------------------------------------------------------------------------------
    def _verifyUpdationOfClientNames(self, clientObjsToCheckLi: List[OpcUaClient], noOfExpectedConn: int) -> bool:
        """
        This method is used to Verify updation of Third Party Client names via IPC using params
        :param listOfClientObjToConnect: List of third party clients, on whom connection is to be performed
        :param noOfExpectedConn: Number of clients that are expected to be connected successfully
        """
        try:
            # plcObj = Lib_OpcUa_LLM.PLCD_OBJECT
            self.logger.newStep("Verifying updation of Third party client connection names")

            # Verifying external client names of the expected connections in PLCD
            noOfExtClientNamesVerified = 0

            for clientNo in range(len(clientObjsToCheckLi) - 2, -1, -1):
                paramIdx = constants.EXTERNAL_CLIENT_NAME_PLC_PARAM_INDEX
                paramSubIdx = constants.EXTERNAL_CLIENT_NAME_PLC_PARAM_SUB_INDEX + clientNo

                extClientNameParam = self.ipc.objByIdx(index = int(paramIdx, 16), subIndex = paramSubIdx)
                self.logger.info(
                    f"[{type(self).prefixCls}] Reading param {paramIdx}:{paramSubIdx} to get name of External client "
                    f"no. {clientNo}")
                result = extClientNameParam.getValue()
                if not result.isOK:
                    self.logger.error(f"[{type(self).prefixCls}] Failed to read external client name parameter")
                    return False

                self.logger.info(f"[{type(self).prefixCls}] External client no. {clientNo} name : {result.value}")

                if constants.THIRD_PARTY_CLIENT_APP_URI.format(socket.gethostname().upper()) == result.value:
                    noOfExtClientNamesVerified += 1
                time.sleep(3)

            if noOfExtClientNamesVerified == noOfExpectedConn:
                self.logger.info(
                    "[%s] No. of updatation of third party clients names in parameters : %s == No of expected"
                    " connections : %s", type(self).prefixCls, noOfExtClientNamesVerified, noOfExpectedConn)
                self.logger.newStep(
                    "Verification of updation of Third party client connection names in parameters for Max "
                    f"External Sessions set to {noOfExpectedConn} is successful")
                return True
            self.logger.error(
                "[%s] No. of updatation of third party clients names in parameters: %s != No of expected "
                "connection : %s", type(self).prefixCls, noOfExtClientNamesVerified, noOfExpectedConn)
            self.logger.error("="*180)
            self.logger.error(
                "Verification of updatation of third party clients names in parameters for Max External"
                " Sessions set to %s failed", noOfExpectedConn)
            self.logger.error("="*180)
        except Exception:  # pylint: disable=broad-exception-caught
            self.logger.exception(
                "[%s] Exception occurred in _verifyUpdationOfClientNames()", type(self).prefixCls)
        return False

    #-------------------------------------------------------------------------------------------------------------------
    def _getAvlAppCredsFrmDiag(self) -> Optional[int]:
        """
        This method is used to start Lenze Diagnosis Web page, read available Application credits and then close the
        tool
        """
        try:
            self.logger.info("[%s] Reading available App credits from Diagnosis tool", type(self).prefixCls)
            # Creating Lenze Diagnosis tool object
            diagnosisObj = LenzeDiagnosis(logger = self.logger)
            if diagnosisObj.startLenzeDiagnosisTool(ipAddress = self.controllerIP,
                                                    userName = constants.DIAGNOSIS_USERNAME,
                                                    base64EncryptedPassword = constants.DIAGNOSIS_BASE64_PWD):
                return diagnosisObj.getAvailableAppCredits()
            self.logger.error("[%s] Lenze Diagnosis tool is not open", type(self).prefixCls)
            return None
        except Exception:  # pylint: disable=broad-exception-caught
            self.logger.exception("[%s] Exception occurred in _getAvlAppCredsFrmDiag()", type(self).prefixCls)
            return None
        finally:
            diagnosisObj.closeLenzeDiagnosisTool()

    #-------------------------------------------------------------------------------------------------------------------
    def _clearLogsFromDiagnosis(self) -> Union[bool, str]:
        """
        This method is used to start Lenze Diagnosis Web page, and read the logbook
        """
        logMsgs = None
        try:
            # Creating Lenze Diagnosis tool object
            diagnosisObj = LenzeDiagnosis(logger = self.logger)
            if diagnosisObj.startLenzeDiagnosisTool(ipAddress = self.controllerIP,
                                                    userName = constants.DIAGNOSIS_USERNAME,
                                                    base64EncryptedPassword = constants.DIAGNOSIS_BASE64_PWD):
                return diagnosisObj.clearLogbook()
            self.logger.error("[%s] Lenze Diagnosis tool is not open", type(self).prefixCls)
            return logMsgs
        except Exception:  # pylint: disable=broad-exception-caught
            self.logger.exception(
                "[%s] Exception occurred in _clearLogsFromDiagnosis()", type(self).prefixCls)
            return logMsgs
        finally:
            diagnosisObj.closeLenzeDiagnosisTool()

    #-------------------------------------------------------------------------------------------------------------------
    def _getLogsFromDiagnosis(self) -> Union[bool, str]:
        """
        This method is used to start Lenze Diagnosis Web page, and read the logbook
        """
        logMsgs = None
        try:
            # Creating Lenze Diagnosis tool object
            diagnosisObj = LenzeDiagnosis(logger = self.logger)
            if diagnosisObj.startLenzeDiagnosisTool(ipAddress = self.controllerIP,
                                                    userName = constants.DIAGNOSIS_USERNAME,
                                                    base64EncryptedPassword = constants.DIAGNOSIS_BASE64_PWD):
                return diagnosisObj.readLogbook()
            self.logger.error("[%s] Lenze Diagnosis tool is not open", type(self).prefixCls)
            return logMsgs
        except Exception:  # pylint: disable=broad-exception-caught
            self.logger.exception(
                "[%s] Exception occurred in _getLogsFromDiagnosis()", type(self).prefixCls)
            return logMsgs
        finally:
            diagnosisObj.closeLenzeDiagnosisTool()

    #-------------------------------------------------------------------------------------------------------------------
    def _checkAppCredExceedMsgInDiag(self, msgExpectedFlag: bool) -> bool:
        """
        This method is used to start Lenze Diagnosis Web page, check if 'Application credits exceeded' message
        is found in Alarms and then close the tool
        """
        try:
            # Creating Lenze Diagnosis tool object
            diagnosisObj = LenzeDiagnosis(logger = self.logger)
            if diagnosisObj.startLenzeDiagnosisTool(ipAddress = self.controllerIP,
                                                    userName = constants.DIAGNOSIS_USERNAME,
                                                    base64EncryptedPassword = constants.DIAGNOSIS_BASE64_PWD):
                msgFound = diagnosisObj.checkIfACExceededOccuredInAlarms()

                if msgExpectedFlag and msgFound:
                    self.logger.info(
                        "[%s] 'Application credits exceeded message' found", type(self).prefixCls)
                    return True
                if msgExpectedFlag:
                    self.logger.error(
                        "[%s] 'Application credits exceeded message' not found", type(self).prefixCls)
                    return False
                if msgFound:
                    self.logger.error(
                        "[%s] 'Application credits exceeded message' found", type(self).prefixCls)
                    return False
                self.logger.error(
                    "[%s] 'Application credits exceeded message' not found", type(self).prefixCls)
                return True
            self.logger.error("[%s] Lenze Diagnosis tool is not open", type(self).prefixCls)
            return False
        except Exception:  # pylint: disable=broad-exception-caught
            self.logger.exception(
                "[%s] Exception occurred in _checkAppCredExceedMsgInDiag()", type(self).prefixCls)
            return False
        finally:
            diagnosisObj.closeLenzeDiagnosisTool()

    #-------------------------------------------------------------------------------------------------------------------
    def _verifyAppCredsInDiagnosis(self, expACForOPCUA: Optional[int] = None, expACForFASTUI: Optional[int] = None,
                                   expACForFASTToolBox: Optional[int] = None,
                                   expACForFASTServices: Optional[int] = None) -> bool:
        """
        This method is used to verify the assigned application credits on License Manager page in Diagnosis tool
        """
        try:
            self.logger.info("[%s] Verifying Assigned app credits in Diagnosis tool", type(self).prefixCls)
            atLeastOneFailed = False
            # Creating Lenze Diagnosis tool object
            diagnosisObj = LenzeDiagnosis(logger = self.logger)
            retryCount = 3
            for retry in range(retryCount):
                # Start Lenze Diagnosis tool
                if diagnosisObj.startLenzeDiagnosisTool(ipAddress = self.controllerIP,
                                                        userName = constants.DIAGNOSIS_USERNAME,
                                                        base64EncryptedPassword = constants.DIAGNOSIS_BASE64_PWD):
                    # Opening License Manager
                    if diagnosisObj.openLicenseManagerTab():
                        # Waiting for contents on License manager to be loaded
                        if diagnosisObj.waitForLicenseManContentsToLoad():
                            self.logger.info("[%s] License manager page is open", type(self).prefixCls)
                            break

                self.logger.warning(
                    "[%s] Closing Diagnosis tool.. reopening it and trying again : retry count : %s",
                    type(self).prefixCls, retry)
                diagnosisObj.closeLenzeDiagnosisTool()
            else:
                self.logger.error(
                    "[%s] Failed to start Lenze Diagnosis tool and open License manager", type(self).prefixCls)
                return False

            #----------------------- Verification of Application Credits for OPC UA---------------------------------
            if expACForOPCUA is not None:
                self.logger.newStep("Verifying Assigned app credits for OPC UA in Diagnosis tool", level = 3)
                readAC = diagnosisObj.getAssignedCreditsForOPCUa()
                if readAC == expACForOPCUA:
                    self.logger.info(
                        "[%s] Verification of Assigned AC for OPC UA successfull", type(self).prefixCls)
                    self.logger.info(
                        "[%s] Expected AC : %s == AC found : %s", type(self).prefixCls, expACForOPCUA,
                        readAC)
                else:
                    self.logger.error(
                        "[%s] Verification of Assigned AC for OPC UA failed", type(self).prefixCls)
                    self.logger.error(
                        "[%s] Expected AC : %s != AC found : %s", type(self).prefixCls, expACForOPCUA,
                        readAC)
                    atLeastOneFailed = True

            #----------------------- Verification of Application Credits for FAST UI--------------------------------
            if expACForFASTUI is not None:
                self.logger.newStep("Verifying Assigned app credits for FAST UI in Diagnosis tool", level = 3)
                readAC = diagnosisObj.getAssignedCreditsForFastUi()
                if readAC == expACForFASTUI:
                    self.logger.info(
                        "[%s] Verification of Assigned AC for FAST UI successful", type(self).prefixCls)
                    self.logger.info(
                        "[%s] Expected AC : %s == AC found : %s", type(self).prefixCls, expACForFASTUI,
                        readAC)
                else:
                    self.logger.error(
                        "[%s] Verification of Assigned AC for FAST UI failed", type(self).prefixCls)
                    self.logger.error(
                        "[%s] Expected AC : %s != AC found : %s", type(self).prefixCls, expACForFASTUI,
                        readAC)
                    atLeastOneFailed = True

            #----------------------- Verification of Application Credits for FAST Toolbox---------------------------
            if expACForFASTToolBox is not None:
                self.logger.newStep(
                    "Verifying Assigned app credits for FAST Toolbox in Diagnosis tool", level = 3)
                readAC = diagnosisObj.getAssignedCreditsForFastToolbox()
                if readAC == expACForFASTToolBox:
                    self.logger.info("[%s] Verification of Assigned AC for FAST Toolbox successful",
                                     type(self).prefixCls)
                    self.logger.info("[%s] Expected AC : %s == AC found : %s", type(self).prefixCls,
                                     expACForFASTToolBox, readAC)
                else:
                    self.logger.error(
                        "[%s] Verification of Assigned AC for FAST Toolbox failed", type(self).prefixCls)
                    self.logger.error(
                        "[%s] Expected AC : %s != AC found : %s",
                        type(self).prefixCls, expACForFASTToolBox, readAC)
                    atLeastOneFailed = True

            #----------------------- Verification of Application Credits for FAST Services--------------------------
            if expACForFASTServices is not None:
                self.logger.newStep(
                    "Verifying Assigned app credits for FAST services in Diagnosis tool", level = 3)
                readAC = diagnosisObj.getAssignedCreditsForFASTService()
                if readAC == expACForFASTServices:
                    self.logger.info(
                        "[%s] Verification of Assigned AC for FAST services successful",
                        type(self).prefixCls)
                    self.logger.info(
                        "[%s] Expected AC : %s == AC found : %s", type(self).prefixCls,
                        expACForFASTServices, readAC)
                else:
                    self.logger.error(
                        "[%s] Verification of Assigned AC for FAST services failed", type(self).prefixCls)
                    self.logger.error(
                        "[%s] Expected AC : %s != AC found : %s", type(self).prefixCls,
                        expACForFASTServices, readAC)
                    atLeastOneFailed = True

            if atLeastOneFailed:
                self.logger.error("[%s] Verification of Assigned app credits in Diagnosis tool failed",
                                  type(self).prefixCls)
                return False

            self.logger.newStep("Verification of Assigned app credits in Diagnosis tool successful", level = 3)
            return True
        except Exception:  # pylint: disable=broad-exception-caught
            self.logger.exception(
                "[%s] Exception occurred in _verifyAppCredsInDiagnosis()", type(self).prefixCls)
            return False
        finally:
            diagnosisObj.closeLenzeDiagnosisTool()
            del diagnosisObj

    #-------------------------------------------------------------------------------------------------------------------
    def _logDescAndupdateResult(self, result: bool, remark: Optional[str] = None) -> None:
        """
        This method is used to get the current testcase spira and then update the result against that spira in report
        """
        try:
            # Getting current testcase's spira id
            currentSpira = self.xlsReaderObj.getSpiraId(testCaseName = self.testCase.testCaseName)

            # Updating result in report
            self.reportUpdaterObj.updateResult(spiraId = currentSpira, result = result, remark = remark)

            # Getting current testcase description from report to log
            testDesc = self.reportUpdaterObj.getTestDescription(spira = currentSpira)
            if result:
                self.logger.newStep(testDesc + " - PASSED", level = 1)
            else:
                self.logger.error("#"*160)
                self.logger.error(f"{testDesc} - FAILED")
                self.logger.error("#"*160)
        except Exception:  # pylint: disable=broad-exception-caught
            self.logger.exception("[%s] Exception occurred in _logDescAndupdateResult()", type(self).prefixCls)

    #-------------------------------------------------------------------------------------------------------------------
    def _generateRandomValForPubVar(self, currentValue: Any, variantType: ua.VariantType) -> Any:
        """
        This method is used to generate a random value for pub vars
        :param currentValue: Current value of the pub var
        """
        if variantType in [ua.VariantType.Int16, ua.VariantType.Int32, ua.VariantType.Int64]:
            newVal = random.choice([val for val in range(-32768, 32767 + 1) if val != currentValue])
        elif variantType in [ua.VariantType.UInt16, ua.VariantType.UInt32, ua.VariantType.UInt64]:
            newVal = random.choice([val for val in range(0, 65535 + 1) if val != currentValue])
        elif variantType in [ua.VariantType.Float, ua.VariantType.Double]:
            newVal = random.choice([val for val in [round(i * 0.1, 1) for i in range(10, 1000)] if val != currentValue])
        elif variantType == ua.VariantType.String:
            newVal = ''.join(random.choices(string.ascii_letters + string.digits,
                                            k=len(currentValue) if currentValue else 4))
        elif variantType == ua.VariantType.ByteString:
            newVal = bytes(random.choices(range(256), k=len(currentValue)))
        else:
            raise ValueError(f"Random value generator not implemented for this data type: {variantType}")
        return newVal

    #-------------------------------------------------------------------------------------------------------------------
    def _checkPubSubVarUpdate(self, pubNodeStr: str, subNodeStr: str) -> bool:
        """
        This method is used to check updation of sub variable on change to pub variable
        """
        thirdPartyConnectionStatus = False
        try:
            # Creating one extra client than expected max external session
            thirdPartyClientObjs = self._getThirdPartyClients(noOfReqObjs = 1)
            thirdPartyConnectionStatus = self._connectAndVerifyConnections(
                listOfClientObjToConnect = thirdPartyClientObjs, noOfExpectedConn = 1)
            if not thirdPartyConnectionStatus:
                self.logger.error(f'[{type(self).prefixCls}] Failed to occupy third party python session')
                return False
            thirdPartyClientObj = thirdPartyClientObjs[0]

            result = thirdPartyClientObj.getNodeFromNodeString(nodeString = pubNodeStr)
            if not result.isOK:
                self.logger.error(f'[{type(self).prefixCls}] Failed to get {pubNodeStr} node')
                return False
            pubNode = result.value

            result = thirdPartyClientObj.getNodeFromNodeString(nodeString = subNodeStr)
            if not result.isOK:
                self.logger.error(f'[{type(self).prefixCls}] Failed to get {subNodeStr} node')
                return False
            subNode = result.value

            self.logger.info(f"[{type(self).prefixCls}] Setting random value to the pub var : {pubNodeStr}")
            currentSubValue = subNode.get_value()
            variantType = subNode.get_data_type_as_variant_type()
            randomValToSet = self._generateRandomValForPubVar(currentValue = currentSubValue,
                                                              variantType = variantType)
            self.logger.info(f"[{type(self).prefixCls}] Setting value : {randomValToSet}")
            pubNode.set_value(value = randomValToSet, varianttype = variantType)

            time.sleep(1)
            pubNodeValue = pubNode.get_value()
            self.logger.info(
                f"[{type(self).prefixCls}] Checking if value set for pub var is reflected in the corresponding sub var "
                f":{subNodeStr}")
            subValue = subNode.get_value()
            self.logger.info(
                f"[{type(self).prefixCls}] Read value of sub var is : {subValue}")

            if variantType in [ua.VariantType.Float, ua.VariantType.Double]:
                if round(pubNode.value, 2) == round(subValue, 2):
                    self.logger.info(
                        f"[{type(self).prefixCls}] Value changed for Pub var : {pubNodeValue} == Sub var : {subValue}"
                        " after rounding off upto 2 decimal places")
                    return True
            else:
                if pubNodeValue == subValue:
                    self.logger.info(
                        f"[{type(self).prefixCls}] Value changed for Pub var : {pubNodeValue} == Sub var : "
                        f"{subValue}")
                    return True

            self.logger.error(
                f"[{type(self).prefixCls}] Value changed for Pub var : {pubNodeValue} != Sub var : {subValue}")
            return False
        except Exception:  # pylint: disable=broad-exception-caught
            self.logger.exception("Exception occured in _checkPubSubVarUpdate()")
            return False
        finally:
            if thirdPartyConnectionStatus:
                self._disconnectThirdPartyClients(clientObjsToDisconnectLi = thirdPartyClientObjs)

    #-------------------------------------------------------------------------------------------------------------------
    def _checkIfVarValsChanging(self, checkCycles: int = 20) -> bool:
        """
        This method is used to check that variables are auto updating or not
        """
        thirdPartyConnectionStatus = False
        try:
            # Creating one extra client than expected max external session
            thirdPartyClientObjs = self._getThirdPartyClients(noOfReqObjs = 1)
            thirdPartyConnectionStatus = self._connectAndVerifyConnections(
                listOfClientObjToConnect = thirdPartyClientObjs, noOfExpectedConn = 1)
            if not thirdPartyConnectionStatus:
                self.logger.error(f'[{type(self).prefixCls}] Failed to occupy third party python session')
                return False
            thirdPartyClientObj = thirdPartyClientObjs[0]
            controllerFam = constants.CONTROLLER_FAMILY_MAP[self.xlsReaderObj.controllerType]

            for nodeStr in constants.SUB_VAR_AUTO_CHANGE_NODESTRINGS:
                varNodeString = nodeStr.format(controllerFam)
                self.logger.info(
                    f'[{type(self).prefixCls}] Reading value of {varNodeString} for {checkCycles}'
                    ' times')
                readValues = set()
                for checkCycle in range(checkCycles):
                    randomPause = random.randint(1, 5)
                    self.logger.info(
                        f'[{type(self).prefixCls}] Reading value of {varNodeString} -> iteration - {checkCycle}')
                    result = thirdPartyClientObj.getNodeFromNodeString(nodeString = varNodeString)
                    if not result.isOK:
                        self.logger.error(f'[{type(self).prefixCls}] Failed to get {varNodeString} node')
                        return False
                    node = result.value
                    nodeValue = node.get_value()
                    self.logger.info(f"[{type(self).prefixCls}] Value read: '{nodeValue}'")
                    readValues.add(nodeValue)
                    self.logger.info(f'[{type(self).prefixCls}] Waiting for {randomPause} seconds')
                    time.sleep(randomPause)
                if len(readValues) == 1:
                    self.logger.error(f'[{type(self).prefixCls}] Value of {varNodeString} node is not changing')
                    return False
                self.logger.info(
                    f'[{type(self).prefixCls}] Successfully verified that value of {varNodeString} node is '
                    'automatically changing')
            self.logger.info(
                f"[{type(self).prefixCls}] All the variables are changing automatically")
            return True

        except Exception:  # pylint: disable=broad-exception-caught
            self.logger.exception("Exception occurred in _checkIfVarValsChanging()")
            return False
        finally:
            if thirdPartyConnectionStatus:
                self._disconnectThirdPartyClients(clientObjsToDisconnectLi = thirdPartyClientObjs)

    #-------------------------------------------------------------------------------------------------------------------
    def _dwnldOrDeletePubSubConfigToCtrl(self, downloadFlag: bool = True) -> bool:
        """
        This method is used to download or delete pub sub config to the controller via sftp
        :param downloadFlag: this flag decides whether to download the config (True) or to clear the config (False)
        """
        self.logger.newStep(
                        f"[{type(self).prefixCls}] Connect to controller via ssh: customer user", level = 3)

        ssh = self.ipc.ssh()
        try:
            result = ssh.login()
            if not result.isOK:
                self.logger.error(f"[{type(self).prefixCls}] SSH login via customer user failed")
                return False
            sftp = ssh.sftp()
            remoteFilePath = constants.UA_BIN_FILE_PATH_IN_CTRL + fr'/{constants.PUBSUB_CONFIG_BIN_FILE_NAME}'
            if downloadFlag:
                self.logger.info(
                    f"[{type(self).prefixCls}] Send {constants.PUBSUB_CONFIG_BIN_FILE_NAME} to "
                    f"controller ({constants.UA_BIN_FILE_PATH_IN_CTRL})")

                localFilePath = os.path.join(
                    os.getcwd(),
                    constants.PUB_SUB_CONFIG_FOLDER_PATH.format(self.xlsReaderObj.controllerType),
                    constants.PUBSUB_CONFIG_BIN_FILE_NAME)

                result = sftp.fileDownload(localFilePath = localFilePath,
                                           remoteFilePath = remoteFilePath)
                if result.isOK:
                    self.logger.info(
                        f"[{type(self).prefixCls}] {constants.PUBSUB_CONFIG_BIN_FILE_NAME} downloaded to controller "
                        "successfully.. restarting the controller")
                    return self.restartController()
                self.logger.info(
                    f"[{type(self).prefixCls}] Failed to download {constants.PUBSUB_CONFIG_BIN_FILE_NAME} to "
                    "controller")
                return False

            self.logger.info(f"[{type(self).prefixCls}] Deleting file {remoteFilePath} from the controller")
            result = sftp.listDir(constants.UA_BIN_FILE_PATH_IN_CTRL)
            matchedFileNames = [
                file.baseName for file in result.value if file.baseName == constants.PUBSUB_CONFIG_BIN_FILE_NAME]
            if not matchedFileNames:
                self.logger.info(f"[{type(self).prefixCls}] {constants.PUBSUB_CONFIG_BIN_FILE_NAME} file is already not"
                                 " present in the controller")
                return True

            result = sftp.fileDelete(remoteFilePath = remoteFilePath)
            if result.isOK:
                self.logger.info(
                    f"[{type(self).prefixCls}] {constants.PUBSUB_CONFIG_BIN_FILE_NAME} deleted from controller "
                    "successfully.. restarting the controller")
                return self.restartController()
            self.logger.info(
                f"[{type(self).prefixCls}] Failed to delete {constants.PUBSUB_CONFIG_BIN_FILE_NAME} from "
                "controller")
            return False
        except Exception:  # pylint: disable=broad-exception-caught
            self.logger.exception("Exception occurred in _dwnldOrDeletePubSubConfigToCtrl()")
            return False
        finally:
            ssh.logout()

    #-------------------------------------------------------------------------------------------------------------------
    def _setFBClientUrls(self) -> bool:
        """
        This method is used to set FB client urls for Open PLC connections
        """
        try:
            plcOpenClientServerUrl = constants.PLC_OPEN_CLIENT_SERVER_URL.format(self.controllerIP)
            countToConnect = constants.MAX_NUM_OF_EXT_SESSIONS_POSSIBLE[self.xlsReaderObj.controllerType] + 1

            byteLength = len(plcOpenClientServerUrl)
            # Convert the string to a byte array with the specified length
            byteArray = bytearray(plcOpenClientServerUrl, 'utf-8')
            if len(byteArray) < byteLength:
                byteArray.extend([0] * (byteLength - len(byteArray)))

            # Create the VisibleString with the byte array
            visibleString = VisibleString(byteArray)

            for clientNo in range(1, countToConnect + 1):
                self.logger.info(
                    f"[{type(self).prefixCls}] Setting server url {plcOpenClientServerUrl} for client number: "
                    f"{clientNo}")

                memObj = self.ipc.plc.memObj(
                    symbolName = constants.PLC_OPEN_CLIENT_SERVER_URL_SYMBOL_NAME.format(clientNo),
                    dataType = visibleString)
                result = memObj.setValue(plcOpenClientServerUrl)
                if not result.isOK:
                    self.logger.error(
                        f"[{type(self).prefixCls}] Failed to set server url {plcOpenClientServerUrl} for"
                        f" client number: {clientNo}")
                    return False
            time.sleep(5)
            return True
        except Exception:  # pylint: disable=broad-exception-caught
            self.logger.exception("Exception occurred in _setFBClientUrls()")
            return False

    #-------------------------------------------------------------------------------------------------------------------
    def _attemptPLCOpenConnection(self) -> bool:
        """
        This method is used to set symbol to connect all Open PLC connections
        """
        self.logger.info(
                f"[{type(self).prefixCls}] Setting symbol {constants.PLC_OPEN_CLIENT_EXECUTE_CONNECT_SYMBOL_NAME} "
                "to True to attempt connection of  PLC Open Clients")
        memObj = self.ipc.plc.memObj(
                symbolName = constants.PLC_OPEN_CLIENT_EXECUTE_CONNECT_SYMBOL_NAME,
                dataType= Boolean)
        result = memObj.setValue(True)
        if not result.isOK:
            self.logger.error(
                f"[{type(self).prefixCls}] Failed to set {constants.PLC_OPEN_CLIENT_EXECUTE_CONNECT_SYMBOL_NAME} "
                "to True")
            return False
        time.sleep(5)
        self.logger.info(
            f"[{type(self).prefixCls}] Successfully set {constants.PLC_OPEN_CLIENT_EXECUTE_CONNECT_SYMBOL_NAME} "
            "to True to connect PLC Open connections")
        return True

    #-------------------------------------------------------------------------------------------------------------------
    def _setMaxExternalSessions(self, maxExtSessionToSet: int) -> bool:
        """
        This method is used to set max external session parameter
        """
        paramIdx, paramSubIdx = constants.MAX_EXTERNAL_SESSION_COUNT_PARAM.split(':')
        maxExtSession = self.ipc.objByIdx(index = int(paramIdx, 16), subIndex = int(paramSubIdx))
        self.logger.info(
            f"[{type(self).prefixCls}] Setting max external session count to {maxExtSessionToSet}")
        result = maxExtSession.setValue(maxExtSessionToSet)
        if not result.isOK:
            self.logger.error(f"[{type(self).prefixCls}] Failed to set max external sessions")
            return False

        self.logger.info(f"[{type(self).prefixCls}] Successfully set max external session to {maxExtSessionToSet}")
        return True

    #-------------------------------------------------------------------------------------------------------------------
    def _getUsedExternalClientsCount(self) -> int:
        """
        This method is used to read parameter and get used external client session counts
        """
        paramIdx, paramSubIdx = constants.USED_EXTERNAL_SESSION_COUNT_PARAM.split(':')
        usedClientPar = self.ipc.objByIdx(index = int(paramIdx, 16), subIndex = int(paramSubIdx))
        self.logger.info(
            f"[{type(self).prefixCls}] Reading used external session count")
        result = usedClientPar.getValue()
        if not result.isOK:
            raise Exception(f"[{type(self).prefixCls}] Failed to read used external sessions")

        self.logger.info(f"[{type(self).prefixCls}] Used external session count read : {result.value}")
        return result.value

    #-------------------------------------------------------------------------------------------------------------------
    def grp_01_tc_01(self) -> None:
        """
        Download the project in the controller using PLC Designer tool
        """
        try:
            self.logger.info("Project already downloaded in above steps (Setup class)")
            self._logDescAndupdateResult(result = True)
        except Exception as ex:  # pylint: disable=broad-exception-caught
            self._logDescAndupdateResult(result = False, remark = str(ex))
            self.testCase.fail(ex)

    #-------------------------------------------------------------------------------------------------------------------
    def execute_Grp02(self, appCreditsToSet: int) -> None:
        """
        This method is used to execute testcases of group 01 i.e
        Verify External Client session connections with "Static AC Configuration" mode and different AC OPC UA for \
        different Max Server Settings
        """
        atleastOneFailedFlag = False
        plcObj = Lib_OpcUa_LLM.PLCD_OBJECT

        # Opening License Manager in PLC tool
        self.logger.newStep("1. Set configuration mode in License Manager to Static AC configuration")
        if not plcObj.openLicenseManager(projName = constants.PLC_PROJ_NAME):
            raise Exception("Failed to open license manager in PLCD tool")

        # Setting License Configuration mode to Static AC configuration
        if not plcObj.setConfigModeInLicenseManager(configModeName = constants.CONFIG_MODE_STATIC_AC_STR,
                                                    projName = constants.PLC_PROJ_NAME):
            raise Exception("Failed to set config mode in License Manager to Static AC configuration")

        # Setting Application credits for FAST Toolbox on License Manager window
        self.logger.newStep("2. Set FAST Toolbox Application credits to 0")
        if not plcObj.setFastToolboxAppCreds(appCreditsToSet = 0,
                                             projName = constants.PLC_PROJ_NAME):
            raise Exception("Failed to set Application credits for FAST Toolbox in License Manager")

        # Setting Application credits for FAST UI on License Manager window
        self.logger.newStep("3. Set FAST UI Application credits to 0")
        if not plcObj.setFastUiAppCreds(appCreditsToSet = 0,
                                        projName = constants.PLC_PROJ_NAME):
            raise Exception("Failed to set Application credits for FAST UI in License Manager")

        # Setting Application credits for Device Features on License Manager window
        self.logger.newStep("4. Set Device Features Application credits to 0")
        if not plcObj.setDeviceFeaturesAppCreds(appCreditsToSet = 0,
                                                projName = constants.PLC_PROJ_NAME):
            raise Exception("Failed to set Application credits for FAST Service in License Manager")

        # Setting Application credits for OPC UA on License Manager window
        self.logger.newStep(f"5. Set OPC UA Application credits to {appCreditsToSet}")
        if not plcObj.setOpcUaAppCreds(appCreditsToSet = appCreditsToSet, projName = constants.PLC_PROJ_NAME):
            raise Exception("Failed to set Application credits for OPC UA in License Manager")

        # Disconnecting IPC before going online as Application credit assignment in the controller and in the PLCD
        # project might be different
        self.ipc.disconnect()

        # Going online downloading changes to the controller
        self.logger.newStep("6. Downloading project to the controller")
        if not plcObj.goOnline():
            raise Exception("Failed to go online with the controller")

        # Creating online boot project
        self.logger.newStep("7. Create online boot project")
        if not plcObj.createBootProject(projName = constants.PLC_PROJ_NAME):
            raise Exception("Failed to create online boot project")

        if not plcObj.goOffline(projName = constants.PLC_PROJ_NAME, header = plcObj.header):
            raise Exception("Failed to Go offline in plcd porject ")

        # Rebooting the controller
        self.logger.newStep("8. Reboot controller")
        self.restartController()

        self.logger.newStep(
            f"7. Verifying Assigned Application credits for OPC UA = {appCreditsToSet} in Diagnosis tool")
        if not self._verifyAppCredsInDiagnosis(expACForOPCUA = appCreditsToSet):
            raise Exception("Verification of App Credits in Diagnosis failed")

        # Creating one extra client than expected max possible external session
        thirdPartyClientObjs = self._getThirdPartyClients(
            noOfReqObjs = constants.MAX_NUM_OF_EXT_SESSIONS_POSSIBLE[self.xlsReaderObj.controllerType] + 1)

        self.logger.newStep(
            "8. Incrementing max external session count setting and Verifying connection and updation of"
            " their names")
        # Incrementing Max external session value and checking connection till max possible connection
        for countOfSessionToTest in range(1, constants.MAX_NUM_OF_EXT_SESSIONS_POSSIBLE[
                self.xlsReaderObj.controllerType] + 1):

            # Setting max external session in dstVersionPlcd
            self.logger.newStep(f"Setting max external session to {countOfSessionToTest}", level = 3)
            if not self._dwnldMaxExtSessSettingInCntrl(maxExtSessionsToSet = countOfSessionToTest):
                raise Exception("Failed to set Max External Session settings")

            clientObjsToConnectLi = thirdPartyClientObjs[:countOfSessionToTest + 1]
            # Connecting client objects one more than expected number of proper connections
            self.logger.newStep(
                "Verifying connection and updation of their names for max external session "
                f"set to {countOfSessionToTest}")
            connectionResult = self._connectAndVerifyConnections(listOfClientObjToConnect = clientObjsToConnectLi,
                                                                 noOfExpectedConn = countOfSessionToTest)
            nameUpdationResult = self._verifyUpdationOfClientNames(clientObjsToCheckLi = clientObjsToConnectLi,
                                                                   noOfExpectedConn = countOfSessionToTest)

            testResult = connectionResult and nameUpdationResult
            if testResult:
                self.logger.newStep(
                    "Verifying connection and updation of their names for max external session "
                    f"set to {countOfSessionToTest} is successfull")
            else:
                self.logger.error(
                    "[%s] Verification of proper connection and updation of names of clients failed",
                    type(self).prefixCls)

            # Checking if Extended package activated or not
            self.logger.newStep(
                         "Validating activation of extended packages for Max External Sessions set "
                         f"to {countOfSessionToTest}")
            extPkgExpected = False
            if countOfSessionToTest >= constants.MIN_EXT_CLIENT_REQ_TO_ACTIVATE_EXT_PKG:
                extPkgExpected = True
            extPkgResult = self._validateExtPkg(extPkgExpectedFlag = extPkgExpected)
            # Disconnected all THird party clients
            self._disconnectThirdPartyClients(clientObjsToDisconnectLi = clientObjsToConnectLi)

            msgToLog = "Verification of External Client session connections with 'Static AC Configuration' mode "\
                f"and AC OPC UA = {appCreditsToSet} for Max Server Settings = {countOfSessionToTest} "

            # Restarting controller if Extended Pkg was activated...
            if extPkgExpected == extPkgResult:
                if not self.restartController():
                    self.logger.warning("[%s] Failed to restart the controller", type(self).prefixCls)

            if not (testResult and extPkgResult):
                self.logger.error("#"*180)
                self.logger.error("[%s] %s Failed", type(self).prefixCls, msgToLog)
                self.logger.error("#"*180)
                atleastOneFailedFlag = True
            else:
                self.logger.newStep(msgToLog + " Successful", level = 1)

        # Raising exception to fail the test if any one of the verification is failed
        if atleastOneFailedFlag:
            raise Exception("TEST FAILED")

    #-------------------------------------------------------------------------------------------------------------------
    def grp_02_tc_01(self) -> None:
        """
        TC1.1 Verify External Client session connections with "Static AC Configuration" mode and AC OPC UA = 0 for \
        different Max Server Settings (Parameter-0x2472 (103))
        """
        try:
            self.execute_Grp02(appCreditsToSet = 0)
            self._logDescAndupdateResult(result = True)
        except Exception as ex:  # pylint: disable=broad-exception-caught
            self._logDescAndupdateResult(result = False, remark = str(ex))
            self.testCase.fail(ex)

    #-------------------------------------------------------------------------------------------------------------------
    def grp_02_tc_02(self) -> None:
        """
        TC1.2 Verify External Client session connections with "Static AC Configuration" mode and AC OPC UA = 100 for \
        different Max Server Settings (Parameter-0x2472 (103))
        """
        try:
            self.execute_Grp02(appCreditsToSet = 100)
            self._logDescAndupdateResult(result = True)
        except Exception as ex:  # pylint: disable=broad-exception-caught
            self._logDescAndupdateResult(result = False, remark = str(ex))
            self.testCase.fail(ex)

    #-------------------------------------------------------------------------------------------------------------------
    def grp_02_tc_03(self) -> None:
        """
        TC1.3 Verify External Client session connections with "Static AC Configuration" mode and AC OPC UA = 150 for \
        different Max Server Settings (Parameter-0x2472 (103))
        """
        try:
            self.execute_Grp02(appCreditsToSet = 150)
            self._logDescAndupdateResult(result = True)
        except Exception as ex:  # pylint: disable=broad-exception-caught
            self._logDescAndupdateResult(result = False, remark = str(ex))
            self.testCase.fail(ex)

    #-------------------------------------------------------------------------------------------------------------------
    def execute_Grp03(self, maxExtSessionCount: int) -> None:
        """
        This method is used to execute testcases of group 02 i.e
        Verify External Client session connections for different settings for AC OPC UA with mode set as \
        "ALL AC to FAST Toolbox"  with Max Server Setting as 1 (Parameter-0x2472 (103)) and AC OPC UA set as 0 & 150
        """
        atleastOneFailedFlag = False
        plcObj = Lib_OpcUa_LLM.PLCD_OBJECT

        # In this test group we test External client connections for Application credits value 0 and 150
        # We can change the application credits value in below tuple if required
        for appCredits in (0, 150):
            # Opening License Manager in PLC tool
            self.logger.newStep("1. Set configuration mode in License Manager to Static AC configuration")
            if not plcObj.openLicenseManager(projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to open license manager in PLCD tool")

            # Setting License Configuration mode to Static AC configuration
            if not plcObj.setConfigModeInLicenseManager(configModeName = constants.CONFIG_MODE_STATIC_AC_STR,
                                                        projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to set config mode in License Manager to Static AC configuration")

            # Setting Application credits for FAST Toolbox on License Manager window
            self.logger.newStep("2. Set FAST Toolbox Application credits to 0")
            if not plcObj.setFastToolboxAppCreds(appCreditsToSet = 0,
                                                 projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to set Application credits for FAST Toolbox in License Manager")

            # Setting Application credits for FAST UI on License Manager window
            self.logger.newStep("3. Set FAST UI Application credits to 0")
            if not plcObj.setFastUiAppCreds(appCreditsToSet = 0,
                                            projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to set Application credits for FAST UI in License Manager")

            # Setting Application credits for Device Features on License Manager window
            self.logger.newStep("4. Set Device Features Application credits to 0")
            if not plcObj.setDeviceFeaturesAppCreds(appCreditsToSet = 0,
                                                    projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to set Application credits for FAST Service in License Manager")

            # Setting Application credits for OPC UA on License Manager window
            self.logger.newStep(f"5. Set OPC UA Application credits to {appCredits}")
            if not plcObj.setOpcUaAppCreds(appCreditsToSet = appCredits, projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to set Application credits for OPC UA in License Manager")

            # Setting License Configuration mode to Static AC configuration
            self.logger.newStep("6. Set configuration mode in License Manager to All AC to FAST Toolbox")
            if not plcObj.setConfigModeInLicenseManager(configModeName = constants.CONFIG_MODE_ALL_AC_TO_FAST_STR,
                                                        projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to set config mode in License Manager to All AC to FAST Toolbox")

            # Disconnecting IPC before going online as Application credit assignment in the controller and in the PLCD
            # project might be different
            self.ipc.disconnect()

            # Going online downloading changes to the controller
            self.logger.newStep("7. Downloading project to the controller")
            if not plcObj.goOnline():
                raise Exception("Failed to go online with the controller")

            # Creating online boot project
            self.logger.newStep("8. Create online boot project")
            if not plcObj.createBootProject(projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to create online boot project")

            if not plcObj.goOffline(projName = constants.PLC_PROJ_NAME, header = plcObj.header):
                raise Exception("Failed to Go offline in plcd porject ")

            # Rebooting the controller
            self.logger.newStep("9. Reboot controller")
            self.restartController()

            self.logger.newStep(
                "12. Verifying, All available credits are assigned to FAST Toolbox and for others "
                "is set to 0 in Diagnosis tool")
            availableCrds = self._getAvlAppCredsFrmDiag()
            if not self._verifyAppCredsInDiagnosis(expACForOPCUA = 0,
                                                   expACForFASTUI = 0,
                                                   expACForFASTToolBox = availableCrds,
                                                   expACForFASTServices = 0):
                raise Exception("Verification of App Credits in Diagnosis failed")

            # Creating one extra client than expected max external session
            thirdPartyClientObjs = self._getThirdPartyClients(
                noOfReqObjs = 2)

            self.logger.newStep(
                f"13. Setting max external session to {maxExtSessionCount}", level = 3)
            if not self._dwnldMaxExtSessSettingInCntrl(maxExtSessionsToSet = maxExtSessionCount):
                raise Exception("Failed to set Max External Session settings in PLCD tool")

            # Connecting client objects one more than expected number of proper connections
            self.logger.newStep(
                "14. Verifying connection and updation of their names for max external session "
                f"set to {maxExtSessionCount}")
            connectionResult = self._connectAndVerifyConnections(listOfClientObjToConnect = thirdPartyClientObjs,
                                                                 noOfExpectedConn = 1)
            nameUpdationResult = self._verifyUpdationOfClientNames(clientObjsToCheckLi = thirdPartyClientObjs,
                                                                   noOfExpectedConn = 1)

            testResult = connectionResult and nameUpdationResult
            if testResult:
                self.logger.newStep(
                    "Verifying connection and updation of their names for max external session "
                    f"set to {maxExtSessionCount} is successfull")
            else:
                self.logger.error(
                    "[%s] Verification of proper connection and updation of names of clients failed",
                    type(self).prefixCls)

            # Checking if Extended package activated or not
            self.logger.info("[%s] Validating activation of extended packages", type(self).prefixCls)
            extPkgResult = self._validateExtPkg(extPkgExpectedFlag = False)

            # Disconnected all THird party clients
            self._disconnectThirdPartyClients(clientObjsToDisconnectLi = thirdPartyClientObjs)

            # Restarting controller if Extended Pkg was activated...
            if not extPkgResult:
                if not self.restartController():
                    self.logger.warning("[%s] Failed to restart the controller", type(self).prefixCls)

            msgToLog = "Verification of External Client session connections with 'Static AC Configuration' mode" + \
                f"and AC OPC UA = {appCredits} for Max Server Settings = {maxExtSessionCount} "

            if not (testResult and extPkgResult):
                self.logger.error("[%s] %s Failed", type(self).prefixCls, msgToLog)
                atleastOneFailedFlag = True
            else:
                self.logger.info("[%s] %s Successful", type(self).prefixCls, msgToLog)

        # Raising exception to fail the test if any one of the verification is failed
        if atleastOneFailedFlag:
            raise Exception("TEST FAILED")

    #-------------------------------------------------------------------------------------------------------------------
    def grp_03_tc_01(self) -> None:
        """
        Verify External Client session connections for different settings for AC OPC UA with mode set as \
        "ALL AC to FAST Toolbox"  with Max Server Setting as 1 (Parameter-0x2472 (103)) and AC OPC UA set as 0 & 150
        """
        try:
            self.execute_Grp03(maxExtSessionCount = 1)
            self._logDescAndupdateResult(result = True)
        except Exception as ex:  # pylint: disable=broad-exception-caught
            self._logDescAndupdateResult(result = False, remark = str(ex))
            self.testCase.fail(ex)

    #-------------------------------------------------------------------------------------------------------------------
    def grp_03_tc_02(self) -> None:
        """
        Verify External Client session connections for different settings for AC OPC UA with mode set as \
        "ALL AC to FAST Toolbox"  with Max Server Setting as 6 (Parameter-0x2472 (103)) and AC OPC UA set as 0 & 150
        """
        try:
            self.execute_Grp03(
                maxExtSessionCount = constants.MAX_NUM_OF_EXT_SESSIONS_POSSIBLE[self.xlsReaderObj.controllerType])
            self._logDescAndupdateResult(result = True)
        except Exception as ex:  # pylint: disable=broad-exception-caught
            self._logDescAndupdateResult(result = False, remark = str(ex))
            self.testCase.fail(ex)

    #-------------------------------------------------------------------------------------------------------------------
    def grp_04_tc_01(self) -> None:
        """
        Verify sequential login of Client 7 after logout of client 6 with Max Server Setting 6 (Parameter-0x2472 (103))
         and AC to OPC UA 150
        """
        try:
            plcObj = Lib_OpcUa_LLM.PLCD_OBJECT
            # Declaring App credits to be set for OPC UA
            appCreditsToSet = 150

            # Opening License Manager in PLC tool
            self.logger.newStep("1. Set configuration mode in License Manager to Static AC configuration")
            if not plcObj.openLicenseManager(projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to open license manager in PLCD tool")

            # Setting License Configuration mode to Static AC configuration
            if not plcObj.setConfigModeInLicenseManager(configModeName = constants.CONFIG_MODE_STATIC_AC_STR,
                                                        projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to set config mode in License Manager to Static AC configuration")

            # Setting Application credits for FAST Toolbox on License Manager window
            self.logger.newStep("2. Set FAST Toolbox Application credits to 0")
            if not plcObj.setFastToolboxAppCreds(appCreditsToSet = 0,
                                                 projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to set Application credits for FAST Toolbox in License Manager")

            # Setting Application credits for FAST UI on License Manager window
            self.logger.newStep("3. Set FAST UI Application credits to 0")
            if not plcObj.setFastUiAppCreds(appCreditsToSet = 0,
                                            projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to set Application credits for FAST UI in License Manager")

            # Setting Application credits for Device Features on License Manager window
            self.logger.newStep("4. Set Device Features Application credits to 0")
            if not plcObj.setDeviceFeaturesAppCreds(appCreditsToSet = 0,
                                                    projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to set Application credits for FAST Service in License Manager")

            # Setting Application credits for OPC UA on License Manager window
            self.logger.newStep(f"5. Set OPC UA Application credits to {appCreditsToSet}")
            if not plcObj.setOpcUaAppCreds(appCreditsToSet = appCreditsToSet,
                                           projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to set Application credits for OPC UA in License Manager")

            # Disconnecting IPC before going online as Application credit assignment in the controller and in the PLCD
            # project might be different
            self.ipc.disconnect()

            # Going online downloading changes to the controller
            self.logger.newStep("6. Downloading project to the controller")
            if not plcObj.goOnline():
                raise Exception("Failed to go online with the controller")

            # Creating online boot project
            self.logger.newStep("7. Create online boot project")
            if not plcObj.createBootProject(projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to create online boot project")

            if not plcObj.goOffline(projName = constants.PLC_PROJ_NAME, header = plcObj.header):
                raise Exception("Failed to Go offline in plcd porject ")

            # Rebooting the controller
            self.logger.newStep("8. Reboot controller")
            self.restartController()

            # Creating Third party client objects
            thirdPartyClientObjs = self._getThirdPartyClients(
                noOfReqObjs = constants.MAX_NUM_OF_EXT_SESSIONS_POSSIBLE[self.xlsReaderObj.controllerType] + 1)

            # Setting max extenal session setting
            self.logger.newStep(
                f"7. Setting max external session to "
                f"{constants.MAX_NUM_OF_EXT_SESSIONS_POSSIBLE[self.xlsReaderObj.controllerType]}")
            if not self._dwnldMaxExtSessSettingInCntrl(
                    maxExtSessionsToSet = constants.MAX_NUM_OF_EXT_SESSIONS_POSSIBLE[self.xlsReaderObj.controllerType]):
                raise Exception("Failed to set Max External Session settings")

            # Connecting 6 clients
            self.logger.newStep(
                f"8. Connecting {constants.MAX_NUM_OF_EXT_SESSIONS_POSSIBLE[self.xlsReaderObj.controllerType]} Third "
                "party clients")
            self.logger.info("-"*120)
            for clientIndex in range(constants.MAX_NUM_OF_EXT_SESSIONS_POSSIBLE[self.xlsReaderObj.controllerType]):
                self.logger.info(
                    "[%s] Connecting %s client", type(self).prefixCls, thirdPartyClientObjs[clientIndex].name)
                res = thirdPartyClientObjs[clientIndex].connect(
                    url = constants.THIRD_PARTY_PYTHON_SERVER_URL.format(self.controllerIP),
                    namespaceStr = constants.THIRD_PARTY_PYTHON_SERVER_NAMESPACE)
                if res.errorCode:
                    self.logger.error("[%s] : %s", type(self).prefixCls, res.errorMessage)
                    raise Exception(f"Failed to connect {thirdPartyClientObjs[clientIndex].name} client")

                self.logger.info("[%s] %s client sucessfully connected", type(self).prefixCls,
                                 thirdPartyClientObjs[clientIndex].name)
                self.logger.info("-"*120)
            self.logger.newStep(
                f"Connection of {constants.MAX_NUM_OF_EXT_SESSIONS_POSSIBLE[self.xlsReaderObj.controllerType]} Third "
                "party clients successful")

            # Disconnecting the last client
            self.logger.newStep(
                "9. Disconnecting client no. "
                f"{constants.MAX_NUM_OF_EXT_SESSIONS_POSSIBLE[self.xlsReaderObj.controllerType]}")
            clientToDisc = thirdPartyClientObjs[
                constants.MAX_NUM_OF_EXT_SESSIONS_POSSIBLE[self.xlsReaderObj.controllerType] - 1]
            self.logger.info("[%s] Disconnecting %s client", type(self).prefixCls, clientToDisc.name)
            res = clientToDisc.disconnect()
            if res.errorCode:
                self.logger.error("[%s] : %s", type(self).prefixCls, res.errorMessage)
                raise Exception(
                    f"Failed to disconnect client no. "
                    f"{constants.MAX_NUM_OF_EXT_SESSIONS_POSSIBLE[self.xlsReaderObj.controllerType]}")
            self.logger.info(
                "[%s] Sucessfully disconnected %s client", type(self).prefixCls, clientToDisc.name)
            self.logger.newStep(
                f"Sucessfully disconnected client no. "
                f"{constants.MAX_NUM_OF_EXT_SESSIONS_POSSIBLE[self.xlsReaderObj.controllerType]}")

            # Connecting 7th client after disconnecting 6th client and verifying if connection is allowed or not
            clientNoConnToVerify = constants.MAX_NUM_OF_EXT_SESSIONS_POSSIBLE[self.xlsReaderObj.controllerType] + 1
            clientNoDisconnected = constants.MAX_NUM_OF_EXT_SESSIONS_POSSIBLE[self.xlsReaderObj.controllerType]
            self.logger.newStep(
                f"8. Verifying connection of client no. {clientNoConnToVerify}, after disconnecting client "
                f"no. {clientNoDisconnected}")
            clientToCon = thirdPartyClientObjs[
                constants.MAX_NUM_OF_EXT_SESSIONS_POSSIBLE[self.xlsReaderObj.controllerType]]
            self.logger.info("[%s] Connecting %s client", type(self).prefixCls, clientToCon.name)
            res = clientToCon.connect(
                url = constants.THIRD_PARTY_PYTHON_SERVER_URL.format(self.controllerIP),
                namespaceStr = constants.THIRD_PARTY_PYTHON_SERVER_NAMESPACE)
            if res.errorCode:
                self.logger.error("[%s] : %s", type(self).prefixCls, res.errorMessage)
                raise Exception(f"Failed to connect client no. "
                                f"{constants.MAX_NUM_OF_EXT_SESSIONS_POSSIBLE[self.xlsReaderObj.controllerType] + 1}")
            self.logger.info("[%s] %s client connected successfully", type(self).prefixCls, clientToCon.name)
            connectedClientCount = constants.MAX_NUM_OF_EXT_SESSIONS_POSSIBLE[self.xlsReaderObj.controllerType] + 1
            disconnectedClientNo = constants.MAX_NUM_OF_EXT_SESSIONS_POSSIBLE[self.xlsReaderObj.controllerType]
            self.logger.newStep(
                f"Third party client no. {connectedClientCount} connected successfully after disconnecting, client "
                f"no. {disconnectedClientNo}")

            # Checking that extended package is available
            self.logger.newStep("10. Verifying activation of Extended Packages")
            if not self._validateExtPkg(extPkgExpectedFlag = True):
                raise Exception("Extended package is not activated")
            self.logger.newStep("Successfully verified activation of extended packages")

            self._logDescAndupdateResult(result = True)

            # Rebooting the controller as Extended package was activated
            if not self.restartController():
                self.logger.warning("[%s] Failed to restart the controller", type(self).prefixCls)

        except Exception as ex:  # pylint: disable=broad-exception-caught
            self._logDescAndupdateResult(result = False, remark = str(ex))
            self.testCase.fail(ex)
        finally:
            if thirdPartyClientObjs:
                # Disconnecting third party clients
                self._disconnectThirdPartyClients(clientObjsToDisconnectLi = thirdPartyClientObjs)

    #-------------------------------------------------------------------------------------------------------------------
    def grp_05_tc_01(self) -> None:
        """
        Verify Connection of One or More then External Client with mode set as "Static AC Configuration"
        with Max Server Setting 6 ( Parameter-0x2472 (103)) and Total AC is  500 , credit assigned to FAST toolbox
        500 and credit assigner to OPC UA 150
        """
        try:
            # Getting Total available Application credits from the Lenze Diagnosis tool
            availableCrds = self._getAvlAppCredsFrmDiag()

            # Declaring Application Credits for OPC UA
            appCredsToSetForOpcUa = 150

            # Dividing total available Application Credits in 3 parts and assigning it to (FAST UI, FAST Services and
            # FAST Toolbox ), So That Sum of all Assigned Application credits > Total available Application credits
            appCredsForOthers = math.floor(availableCrds/3)

            plcObj = Lib_OpcUa_LLM.PLCD_OBJECT

            # Opening License Manager in PLC tool
            self.logger.newStep("1. Set configuration mode in License Manager to Static AC configuration")
            if not plcObj.openLicenseManager(projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to open license manager in PLCD tool")

            # Setting License Configuration mode to Static AC configuration
            if not plcObj.setConfigModeInLicenseManager(configModeName = constants.CONFIG_MODE_STATIC_AC_STR,
                                                        projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to set config mode in License Manager to Static AC configuration")

            # Setting Application credits for OPC UA on License Manager window
            self.logger.newStep(f"2. Set OPC UA Application credits to {appCredsToSetForOpcUa}")
            if not plcObj.setOpcUaAppCreds(appCreditsToSet = appCredsToSetForOpcUa,
                                           projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to set Application credits for OPC UA in License Manager")

            # Setting Application credits for FAST Toolbox on License Manager window
            self.logger.newStep(f"3. Set FAST Toolbox Application credits to {appCredsForOthers}")
            if not plcObj.setFastToolboxAppCreds(appCreditsToSet = appCredsForOthers,
                                                 projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to set Application credits for FAST Toolbox in License Manager")

            # Setting Application credits for FAST UI on License Manager window
            self.logger.newStep(f"4. Set FAST UI Application credits to {appCredsForOthers}")
            if not plcObj.setFastUiAppCreds(appCreditsToSet = appCredsForOthers,
                                            projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to set Application credits for FAST UI in License Manager")

            # Setting Application credits for Device Features on License Manager window
            self.logger.newStep(f"5. Set Device Features Application credits to {appCredsForOthers}")
            if not plcObj.setDeviceFeaturesAppCreds(appCreditsToSet = appCredsForOthers,
                                                    projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to set Application credits for FAST Service in License Manager")

            # Disconnecting IPC before going online as Application credit assignment in the controller and in the PLCD
            # project might be different
            self.ipc.disconnect()

            # Going online downloading changes to the controller
            self.logger.newStep("6. Downloading project to the controller")
            if not plcObj.goOnline():
                raise Exception("Failed to go online with the controller")

            # Creating online boot project
            self.logger.newStep("8. Create online boot project")
            if not plcObj.createBootProject(projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to create online boot project")

            if not plcObj.goOffline(projName = constants.PLC_PROJ_NAME, header = plcObj.header):
                raise Exception("Failed to Go offline in plcd porject ")

            # Rebooting the controller
            self.logger.newStep("9. Reboot controller")
            self.restartController()

            # Setting max extenal session on UA_Server page in PLCD
            self.logger.newStep(
                f"7. Setting max external session to "
                f"{constants.MAX_NUM_OF_EXT_SESSIONS_POSSIBLE[self.xlsReaderObj.controllerType]}")
            if not self._dwnldMaxExtSessSettingInCntrl(
                    maxExtSessionsToSet = constants.MAX_NUM_OF_EXT_SESSIONS_POSSIBLE[self.xlsReaderObj.controllerType]):
                raise Exception("Failed to set Max External Session settings tool")

            # Creating Third party client objects
            # Creating one extra object than the max possible connections
            thirdPartyClientObjs = self._getThirdPartyClients(
                noOfReqObjs = constants.MAX_NUM_OF_EXT_SESSIONS_POSSIBLE[self.xlsReaderObj.controllerType] + 1)

            # Connecting all third party clients
            self.logger.newStep(
                f"8. Connecting {constants.MAX_NUM_OF_EXT_SESSIONS_POSSIBLE[self.xlsReaderObj.controllerType] + 1} "
                "third party clients")
            connectionResult = self._connectAndVerifyConnections(
                listOfClientObjToConnect = thirdPartyClientObjs,
                noOfExpectedConn = constants.MAX_NUM_OF_EXT_SESSIONS_POSSIBLE[self.xlsReaderObj.controllerType])

            # Connecting all third party clients
            self.logger.newStep("9. Verifying Application credits exceed message in Alarms page in Diagnosis")
            alarmResult = self._checkAppCredExceedMsgInDiag(msgExpectedFlag = True)
            if alarmResult:
                self.logger.newStep("Verification of Application credits exceed message sucessful")
            else:
                self.logger.error("="*180)
                self.logger.error("Verification of Application credits exceed message failed")
                self.logger.error("="*180)

            # Connecting all third party clients
            self.logger.newStep("10. Verifying Assigned Application credits for in Diagnosis tool")
            acResult = self._verifyAppCredsInDiagnosis(expACForOPCUA = appCredsToSetForOpcUa,
                                                       expACForFASTUI = appCredsForOthers,
                                                       expACForFASTToolBox = appCredsForOthers,
                                                       expACForFASTServices = appCredsForOthers)
            if acResult:
                self.logger.newStep(
                    "Verification of Assigned Application credits in Diagnosis tool sucessful")
            else:
                self.logger.error("="*180)
                self.logger.error(
                    "Verification of Assigned Application credits in Diagnosis tool failed")
                self.logger.error("="*180)

            if connectionResult and alarmResult and acResult:
                self._logDescAndupdateResult(result = True)
            else:
                raise Exception("TEST FAILED : One or more validation failed")

        except Exception as ex:  # pylint: disable=broad-exception-caught
            self._logDescAndupdateResult(result = False, remark = str(ex))
            self.testCase.fail(ex)
        finally:
            if thirdPartyClientObjs:
                self._disconnectThirdPartyClients(clientObjsToDisconnectLi = thirdPartyClientObjs)
            if not self.restartController():
                self.logger.warning("[%s] Failed to reboot the controller..", type(self).prefixCls)

    #-------------------------------------------------------------------------------------------------------------------
    def grp_06_tc_01(self) -> None:
        """
        Verify updatation of Application credit in Diagnosis License Manager without connection of Third party client
        with assigned Credit being set as different values (0, 100 & 150)
        """
        try:
            plcObj = Lib_OpcUa_LLM.PLCD_OBJECT

            acOPCUaAppCredsToCheck = [0, 100, 150]

            for appCred in acOPCUaAppCredsToCheck:
                otherAppCreds = 0
                self.logger.newStep(f"Checking for app credits: {appCred}")

                # Opening License Manager in PLC tool
                self.logger.newStep("Set configuration mode in License Manager to Static AC configuration")
                if not plcObj.openLicenseManager(projName = constants.PLC_PROJ_NAME):
                    raise Exception("Failed to open license manager in PLCD tool")

                # Setting License Configuration mode to Static AC configuration
                if not plcObj.setConfigModeInLicenseManager(configModeName = constants.CONFIG_MODE_STATIC_AC_STR,
                                                            projName = constants.PLC_PROJ_NAME):
                    raise Exception("Failed to set config mode in License Manager to Static AC configuration")

                # Setting Application credits for OPC UA on License Manager window
                self.logger.newStep(f"Set OPC UA Application credits to {appCred}")
                if not plcObj.setOpcUaAppCreds(appCreditsToSet = appCred,
                                               projName = constants.PLC_PROJ_NAME):
                    raise Exception("Failed to set Application credits for OPC UA in License Manager")

                # Setting Application credits for FAST Toolbox on License Manager window
                self.logger.newStep(f"Set FAST Toolbox Application credits to {otherAppCreds}")
                if not plcObj.setFastToolboxAppCreds(appCreditsToSet = otherAppCreds,
                                                     projName = constants.PLC_PROJ_NAME):
                    raise Exception("Failed to set Application credits for FAST Toolbox in License Manager")

                # Setting Application credits for FAST UI on License Manager window
                self.logger.newStep(f"Set FAST UI Application credits to {otherAppCreds}")
                if not plcObj.setFastUiAppCreds(appCreditsToSet = otherAppCreds,
                                                projName = constants.PLC_PROJ_NAME):
                    raise Exception("Failed to set Application credits for FAST UI in License Manager")

                # Setting Application credits for Device Features on License Manager window
                self.logger.newStep(f"Set Device Features Application credits to {otherAppCreds}")
                if not plcObj.setDeviceFeaturesAppCreds(appCreditsToSet = otherAppCreds,
                                                        projName = constants.PLC_PROJ_NAME):
                    raise Exception("Failed to set Application credits for FAST Service in License Manager")

                # Disconnecting IPC before going online as Application credit assignment in the controller and in the
                #  PLCD project might be different
                self.ipc.disconnect()

                # Going online downloading changes to the controller
                self.logger.newStep("Downloading project to the controller")
                if not plcObj.goOnline():
                    raise Exception("Failed to go online with the controller")

                # Creating online boot project
                self.logger.newStep("Create online boot project")
                if not plcObj.createBootProject(projName = constants.PLC_PROJ_NAME):
                    raise Exception("Failed to create online boot project")

                if not plcObj.goOffline(projName = constants.PLC_PROJ_NAME, header = plcObj.header):
                    raise Exception("Failed to Go offline in plcd porject ")

                # Rebooting the controller
                self.logger.newStep("Reboot controller")
                self.restartController()

                self.logger.newStep(
                    f"Verifying Assigned AC OPC UA Application credits in Diagnosis tool is equal to {appCred}")
                acResult = self._verifyAppCredsInDiagnosis(expACForOPCUA = appCred)
                if acResult:
                    self.logger.newStep(
                        f"Successfully verified AC OPC UA Application credits in Diagnosis tool = {appCred}")
                else:
                    self.logger.error("="*180)
                    self.logger.error(
                        f"Assigned AC OPC UA Application credits in Diagnosis != {appCred}")
                    self.logger.error("="*180)
                    raise Exception(
                        f"TEST FAILED : AC OPC UA Application credits in Diagnosis tool != {appCred}.. after setting "
                        "it using PLCD")

            self._logDescAndupdateResult(result = True)

        except Exception as ex:  # pylint: disable=broad-exception-caught
            self._logDescAndupdateResult(result = False, remark = str(ex))
            self.testCase.fail(ex)

    #-------------------------------------------------------------------------------------------------------------------
    def grp_07_tc_01(self) -> None:
        """
        Verify connection of Multiple PLC open client to OPC UA server when required Application credit are not
        availble on SD card
        """
        noOfExpectedConn = 1
        try:
            plcObj = Lib_OpcUa_LLM.PLCD_OBJECT

            # Opening License Manager in PLC tool
            if not plcObj.openLicenseManager(projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to open license manager in PLCD tool")

            # Setting License Configuration mode to Static AC configuration
            self.logger.newStep("Set configuration mode in License Manager to All AC to FAST Toolbox")
            if not plcObj.setConfigModeInLicenseManager(configModeName = constants.CONFIG_MODE_ALL_AC_TO_FAST_STR,
                                                        projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to set config mode in License Manager to All AC to FAST Toolbox")

            # Disconnecting IPC before going online as Application credit assignment in the controller and in the PLCD
            # project might be different
            self.ipc.disconnect()

            # Going online downloading changes to the controller
            self.logger.newStep("Downloading project to the controller")
            if not plcObj.goOnline(upload = True):
                raise Exception("Failed to go online with the controller")

            # Creating online boot project
            self.logger.newStep("Create online boot project")
            if not plcObj.createBootProject(projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to create online boot project")

            if not plcObj.goOffline(projName = constants.PLC_PROJ_NAME, header = plcObj.header):
                raise Exception("Failed to Go offline in plcd porject ")

            # Rebooting the controller
            self.logger.newStep("Reboot controller")
            if not self.restartController():
                raise Exception("Failed to reboot the controller")

            # Handle no connection pop up
            plcObj.handlePLCConnectionLost(header = plcObj.header)

            self.logger.newStep("Starting application")
            # Starting application
            self.ipc.cmd.appStart()

            # Going online downloading changes to the controller
            self.logger.newStep("Downloading project to the controller")
            if not plcObj.goOnline(upload = True):
                raise Exception("Failed to go online with the controller")

            # Setting max external session in dstVersionPlcd
            maxExtSessionCount = constants.MAX_NUM_OF_EXT_SESSIONS_POSSIBLE[self.xlsReaderObj.controllerType]
            self.logger.newStep("Setting max external session in PLCD to {maxExtSessionCount}", level = 3)
            if not self._dwnldMaxExtSessSettingInCntrl(maxExtSessionsToSet = maxExtSessionCount):
                raise Exception("Failed to set Max External Session settings in PLCD tool")

            if not plcObj.deleteLogs(projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to delete the controller logbook")

            # Connect PLC Open clients and verify that only one connection is allowed and others are rejected
            self.logger.newStep(
                "Connect PLC Open clients and verify that only one connection is allowed and others are rejected")

            # Connecting PLC Open clients.. one extra than the max possible clients
            if not self._setFBClientUrls():
                raise Exception("Failed to set Fb client URLs for PLC Open connections")

            self.logger.info(
                    f"[{type(self).prefixCls}] Setting symbol {constants.PLC_OPEN_CLIENT_EXECUTE_CONNECT_SYMBOL_NAME} "
                    f"to True to attempt connections of PLC Open Clients")
            if not self._attemptPLCOpenConnection():
                raise Exception(f"Failed to set {constants.PLC_OPEN_CLIENT_EXECUTE_CONNECT_SYMBOL_NAME}  to True")

            self.logger.newStep(
                f"Check using (PLC Open client Error ids) that only {noOfExpectedConn} clients are successfully "
                "connected")
            connectionsVerified = 0
            for clientNo in range(1, noOfExpectedConn + 2):
                self.logger.info(
                    f"[{type(self).prefixCls}] Checking for connection error id for server number : {clientNo}")
                memObj = self.ipc.plc.memObj(
                   symbolName = constants.PLC_OPEN_CLIENT_CONNECT_ERROR_SYMBOL_NAME.format(clientNo),
                   dataType= Unsigned32)
                result = memObj.getValue()
                if not result.isOK:
                    raise Exception(
                        f"[{type(self).prefixCls}] Failed to read connection error id for client num: {clientNo}")
                self.logger.info(
                    f"[{type(self).prefixCls}] Error read for client number: {clientNo} -> {result.value}")
                if result.value == constants.PLC_OPEN_CLIENT_FAILED_CONNECT_ERROR_ID:
                    self.logger.info(
                        f"[{type(self).prefixCls}] PLC Open client connection for client number: {clientNo} failed..")
                else:
                    self.logger.info(
                        f"[{type(self).prefixCls}] PLC Open client connection for client number: {clientNo}"
                        " is successful")
                    connectionsVerified += 1

            if connectionsVerified == noOfExpectedConn:
                self.logger.info(
                    f"[{type(self).prefixCls}] PLC Open expected client connection count: {noOfExpectedConn} "
                    f" == Successful connection count : {connectionsVerified}")
            else:
                raise Exception(f"PLC Open expected client connection count: {noOfExpectedConn} "
                                f" != Successful connection count : {connectionsVerified}")

            self.logger.newStep("Checking that the number of used external clients (from parameter)"
                                f" should be {noOfExpectedConn}")
            connectedClientCount = self._getUsedExternalClientsCount()

            if connectedClientCount == noOfExpectedConn:
                self.logger.info(
                    f"[{type(self).prefixCls}] Verified that number of used external clients ({connectedClientCount})"
                    f" is  {noOfExpectedConn}")
            else:
                raise Exception(
                    f"Number of used external sessions ({connectedClientCount}) is not equal to {noOfExpectedConn}")

            # Checking for OPC UA AC Rejected failure in controller logbook
            self.logger.newStep(
                f"Checking for '{constants.OPC_AC_REJECTED_LOGBOOK_MSG}' msg in controller logbook")
            logMsgs = plcObj.readLogbookMsgs(projName = constants.PLC_PROJ_NAME)
            if constants.OPC_AC_REJECTED_LOGBOOK_MSG not in logMsgs:
                raise Exception(f"'{constants.OPC_AC_REJECTED_LOGBOOK_MSG}' not found in controller logbook")
            self.logger.info(f"'{constants.OPC_AC_REJECTED_LOGBOOK_MSG}' found in controller logbook")

            self._logDescAndupdateResult(result = True)

        except Exception as ex:  # pylint: disable=broad-exception-caught
            self._logDescAndupdateResult(result = False, remark = str(ex))
            self.testCase.fail(ex)

        finally:
            if not self._disconnectAllPLCOpenClients():
                self.logger.warning("Failed to disconnect all the PLC Open clients")

            if not plcObj.goOffline(projName = constants.PLC_PROJ_NAME, header = plcObj.header):
                self.logger.warning("Failed to go offline")

    #-------------------------------------------------------------------------------------------------------------------
    def grp_07_tc_02(self) -> None:
        """
        Verify connection of Multiple PLC Open client to OPC UA server when required Application credit are availble
        on SD card
        """
        try:
            plcObj = Lib_OpcUa_LLM.PLCD_OBJECT

            # Opening License Manager in PLC tool
            self.logger.newStep("Set configuration mode in License Manager to Static AC configuration")
            if not plcObj.openLicenseManager(projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to open license manager in PLCD tool")

            # Setting License Configuration mode to Static AC configuration
            if not plcObj.setConfigModeInLicenseManager(configModeName = constants.CONFIG_MODE_STATIC_AC_STR,
                                                        projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to set config mode in License Manager to Static AC configuration")

            # Setting Application credits for FAST Toolbox on License Manager window
            self.logger.newStep("Set FAST Toolbox Application credits to 0")
            if not plcObj.setFastToolboxAppCreds(appCreditsToSet = 0,
                                                 projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to set Application credits for FAST Toolbox in License Manager")

            # Setting Application credits for FAST UI on License Manager window
            self.logger.newStep("Set FAST UI Application credits to 0")
            if not plcObj.setFastUiAppCreds(appCreditsToSet = 0,
                                            projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to set Application credits for FAST UI in License Manager")

            # Setting Application credits for Device Features on License Manager window
            self.logger.newStep("Set Device Features Application credits to 0")
            if not plcObj.setDeviceFeaturesAppCreds(appCreditsToSet = 0,
                                                    projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to set Application credits for FAST Service in License Manager")

            # Setting Application credits for OPC UA on License Manager window
            self.logger.newStep("Set OPC UA Application credits to 150")
            if not plcObj.setOpcUaAppCreds(appCreditsToSet = 150, projName = constants.PLC_PROJ_NAME):
                raise Exception("ailed to set Application credits for OPC UA in License Manager")

            # Disconnecting IPC before going online as Application credit assignment in the controller and in the PLCD
            # project might be different
            self.ipc.disconnect()

            # Going online downloading changes to the controller
            self.logger.newStep("Downloading project to the controller")
            if not plcObj.goOnline(upload = True):
                raise Exception("Failed to go online with the controller")

            # Creating online boot project
            self.logger.newStep("Create online boot project")
            if not plcObj.createBootProject(projName = constants.PLC_PROJ_NAME):
                takeScreenshot()
                raise Exception("Failed to create online boot project")

            # Rebooting the controller
            self.logger.newStep("Reboot controller")
            if not self.restartController():
                raise Exception("Failed to reboot the controller")

            self.logger.newStep("Starting application")
            # Starting application
            self.ipc.cmd.appStart()

            # Handle no connection pop up
            plcObj.handlePLCConnectionLost(header = plcObj.header)

            # Going online downloading changes to the controller
            self.logger.newStep("Downloading project to the controller")
            if not plcObj.goOnline(upload = True):
                raise Exception("Failed to go online with the controller")

            # Setting max external session
            maxExtSessionCount = constants.MAX_NUM_OF_EXT_SESSIONS_POSSIBLE[self.xlsReaderObj.controllerType]
            self.logger.newStep(f"Setting max external session to {maxExtSessionCount}", level = 3)
            if not self._dwnldMaxExtSessSettingInCntrl(maxExtSessionsToSet = maxExtSessionCount):
                raise Exception("Failed to set Max External Session settings")

            if not plcObj.deleteLogs(projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to delete the controller logbook")

            # Connect PLC Open clients and verify that only one connection is allowed and others are rejected
            self.logger.newStep(
                "Connect PLC Open clients and verify that only one connection is allowed and others are rejected")

            # Connecting PLC Open clients.. one extra than the max possible clients
            if not self._setFBClientUrls():
                raise Exception("Failed to set Fb client URLs for PLC Open connections")

            self.logger.info(
                f"[{type(self).prefixCls}] Setting symbol {constants.PLC_OPEN_CLIENT_CONNECT_EXTRA_SYMBOL_NAME} "
                f"to True to attempt connection of the extra PLC Open Clients")
            memObj = self.ipc.plc.memObj(
                    symbolName = constants.PLC_OPEN_CLIENT_CONNECT_EXTRA_SYMBOL_NAME,
                    dataType= Boolean)
            result = memObj.setValue(True)
            if not result.isOK:
                raise Exception(
                    f"[{type(self).prefixCls}] Failed to set {constants.PLC_OPEN_CLIENT_CONNECT_EXTRA_SYMBOL_NAME} "
                    "to True")

            time.sleep(5)
            self.logger.info(
                    f"[{type(self).prefixCls}] Setting symbol {constants.PLC_OPEN_CLIENT_EXECUTE_CONNECT_SYMBOL_NAME} "
                    f"to True to attempt connections of PLC Open Clients")
            if not self._attemptPLCOpenConnection():
                raise Exception(f"Failed to set {constants.PLC_OPEN_CLIENT_EXECUTE_CONNECT_SYMBOL_NAME} to True")

            self.logger.info(f"[{type(self).prefixCls}] Starting application")
            self.ipc.cmd.appStart()

            self.logger.newStep(
                f"Check using using PLC Open client error ID that only {maxExtSessionCount} client is "
                "successfully connected")
            connectionsVerified = 0
            for clientNo in range(1, maxExtSessionCount + 2):
                self.logger.info(
                    f"[{type(self).prefixCls}] Checking for connection error id for server number : {clientNo}")
                memObj = self.ipc.plc.memObj(
                   symbolName = constants.PLC_OPEN_CLIENT_CONNECT_ERROR_SYMBOL_NAME.format(clientNo),
                   dataType= Unsigned32)
                result = memObj.getValue()
                if not result.isOK:
                    raise Exception(f"Failed to read connection error id for client num: {clientNo}")
                if result.value == constants.PLC_OPEN_CLIENT_FAILED_CONNECT_ERROR_ID:
                    self.logger.info(
                        f"[{type(self).prefixCls}] PLC Open client connection for client number: {clientNo} failed..")
                else:
                    self.logger.info(
                        f"[{type(self).prefixCls}] PLC Open client connection for client number: {clientNo}"
                        " is successful")
                    connectionsVerified += 1

            if connectionsVerified == maxExtSessionCount:
                self.logger.info(
                    f"[{type(self).prefixCls}] PLC Open expected client connection count: {maxExtSessionCount} "
                    f" == Successful connection count : {connectionsVerified}")
            else:
                raise Exception(f"PLC Open expected client connection count: {maxExtSessionCount} "
                                f" != Successful connection count : {connectionsVerified}")

            self.logger.newStep(
                f"Check using using Used external session parameter that only {maxExtSessionCount} client is"
                " successfully connected")
            self.logger.info(
                f"[{type(self).prefixCls}] Checking that the number of used external clients (using parameter)"
                f" should be {maxExtSessionCount}")
            connectedClientCount = self._getUsedExternalClientsCount()

            if connectedClientCount == maxExtSessionCount:
                self.logger.info(
                    f"[{type(self).prefixCls}] Verified that number of used external clients is "
                    f" {maxExtSessionCount}")
            else:
                raise Exception(f"Number of used external sessions is not equal to {maxExtSessionCount}")

            # Checking for OPC UA AC Rejected failure in controller logbook
            self.logger.newStep(
                f"Checking for '{constants.OPC_AC_REJECTED_LOGBOOK_MSG}' msg in controller logbook")
            logMsgs = plcObj.readLogbookMsgs(projName = constants.PLC_PROJ_NAME)
            if constants.OPC_AC_REJECTED_LOGBOOK_MSG not in logMsgs:
                raise Exception(f"'{constants.OPC_AC_REJECTED_LOGBOOK_MSG}' not found in controller logbook")
            self.logger.info(f"'{constants.OPC_AC_REJECTED_LOGBOOK_MSG}' found in controller logbook")

            self._logDescAndupdateResult(result = True)

        except Exception as ex:  # pylint: disable=broad-exception-caught
            self._logDescAndupdateResult(result = False, remark = str(ex))
            self.testCase.fail(ex)

        finally:
            # Disconnected all PLC open clients
            self._disconnectAllPLCOpenClients()

            if not plcObj.goOffline(projName = constants.PLC_PROJ_NAME, header = plcObj.header):
                self.logger.warning("Failed to go offline")

    #-------------------------------------------------------------------------------------------------------------------
    def grp_07_tc_03(self) -> None:
        """
        Verify disconnecting one of the six already connected OPC UA server session, with PLC open client and
        connecting a new OPC UA server session
        """
        try:
            plcObj = Lib_OpcUa_LLM.PLCD_OBJECT

            # Opening License Manager in PLC tool
            self.logger.newStep("Set configuration mode in License Manager to Static AC configuration")
            if not plcObj.openLicenseManager(projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to open license manager in PLCD tool")

            # Setting License Configuration mode to Static AC configuration
            if not plcObj.setConfigModeInLicenseManager(configModeName = constants.CONFIG_MODE_STATIC_AC_STR,
                                                        projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to set config mode in License Manager to Static AC configuration")

            # Setting Application credits for FAST Toolbox on License Manager window
            self.logger.newStep("Set FAST Toolbox Application credits to 0")
            if not plcObj.setFastToolboxAppCreds(appCreditsToSet = 0,
                                                 projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to set Application credits for FAST Toolbox in License Manager")

            # Setting Application credits for FAST UI on License Manager window
            self.logger.newStep("Set FAST UI Application credits to 0")
            if not plcObj.setFastUiAppCreds(appCreditsToSet = 0,
                                            projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to set Application credits for FAST UI in License Manager")

            # Setting Application credits for Device Features on License Manager window
            self.logger.newStep("Set Device Features Application credits to 0")
            if not plcObj.setDeviceFeaturesAppCreds(appCreditsToSet = 0,
                                                    projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to set Application credits for FAST Service in License Manager")

            # Setting Application credits for OPC UA on License Manager window
            self.logger.newStep("Set OPC UA Application credits to 150")
            if not plcObj.setOpcUaAppCreds(appCreditsToSet = 150, projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to set Application credits for OPC UA in License Manager")

            # Disconnecting IPC before going online as Application credit assignment in the controller and in the PLCD
            # project might be different
            self.ipc.disconnect()

            # Going online downloading changes to the controller
            self.logger.newStep("Downloading project to the controller")
            if not plcObj.goOnline(upload = True):
                raise Exception("Failed to go online with the controller")

            # Creating online boot project
            self.logger.newStep("Create online boot project")
            if not plcObj.createBootProject(projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to create online boot project")

            # Rebooting the controller
            self.logger.newStep("Reboot controller")
            if not self.restartController():
                raise Exception("Failed to reboot the controller")

            # Handle no connection pop up
            plcObj.handlePLCConnectionLost(header = plcObj.header)

            self.logger.newStep("Starting application")
            # Starting application
            self.ipc.cmd.appStart()

            # Going online downloading changes to the controller
            self.logger.newStep("Downloading project to the controller")
            if not plcObj.goOnline(upload = True):
                raise Exception("Failed to go online with the controller")

            # Setting max external session
            maxExtSessionCount = constants.MAX_NUM_OF_EXT_SESSIONS_POSSIBLE[self.xlsReaderObj.controllerType]
            self.logger.newStep(f"Setting max external session to {maxExtSessionCount}",
                                level = 3)
            if not self._dwnldMaxExtSessSettingInCntrl(maxExtSessionsToSet = maxExtSessionCount):
                raise Exception("Failed to set Max External Session settings")

            if not plcObj.deleteLogs(projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to delete the controller logbook")

            # Connect PLC Open clients and verify
            self.logger.newStep(
                f"Connect PLC Open clients and verify that {maxExtSessionCount} connections are allowed and others "
                "are rejected")

            # Connecting PLC Open clients.. one extra than the max possible clients
            if not self._setFBClientUrls():
                raise Exception("Failed to set Fb client URLs for PLC Open connections")

            self.logger.info(
                    f"[{type(self).prefixCls}] Setting symbol {constants.PLC_OPEN_CLIENT_EXECUTE_CONNECT_SYMBOL_NAME} "
                    f"to True to attempt connections of PLC Open Clients")
            if not self._attemptPLCOpenConnection():
                raise Exception(
                    f"[{type(self).prefixCls}] Failed to set {constants.PLC_OPEN_CLIENT_EXECUTE_CONNECT_SYMBOL_NAME} "
                    "to True")

            self.logger.info(f"[{type(self).prefixCls}] Starting application")
            self.ipc.cmd.appStart()

            self.logger.newStep(f"Checking now that number of used external clients should be: {maxExtSessionCount}")
            connectedClientCount = self._getUsedExternalClientsCount()

            if connectedClientCount == maxExtSessionCount:
                self.logger.info(
                    f"[{type(self).prefixCls}] Verified that number of used external clients is "
                    f" {maxExtSessionCount}")
            else:
                raise Exception(
                    f"[{type(self).prefixCls}] Number of used external sessions is not equal to "
                    f"{maxExtSessionCount}")

            self.logger.newStep(f"Setting symbol {constants.PLC_OPEN_CLIENT_DISABLE_ONE_CLIENT_SYMBOL_NAME} "
                                f"to True to disconnect one of 6 clients")
            memObj = self.ipc.plc.memObj(
                    symbolName = constants.PLC_OPEN_CLIENT_DISABLE_ONE_CLIENT_SYMBOL_NAME,
                    dataType= Boolean)
            result = memObj.setValue(True)
            if not result.isOK:
                raise Exception(
                    f"[{type(self).prefixCls}] Failed to set {constants.PLC_OPEN_CLIENT_DISABLE_ONE_CLIENT_SYMBOL_NAME}"
                    " to True")
            time.sleep(5)
            self.logger.newStep(f"Checking now that number of used external clients should be:"
                                f" {maxExtSessionCount - 1}")
            connectedClientCount = self._getUsedExternalClientsCount()

            if connectedClientCount == maxExtSessionCount - 1:
                self.logger.info(
                    f"[{type(self).prefixCls}] Verified that number of used external clients is "
                    f" {maxExtSessionCount - 1}")
            else:
                raise Exception(
                    f"[{type(self).prefixCls}] Number of used external sessions is not equal to "
                    f"{maxExtSessionCount - 1}")

            self.logger.newStep(f"Setting symbol {constants.PLC_OPEN_CLIENT_CONNECT_EXTRA_SYMBOL_NAME} "
                                f"to True to connect one extra client")
            memObj = self.ipc.plc.memObj(
                    symbolName = constants.PLC_OPEN_CLIENT_CONNECT_EXTRA_SYMBOL_NAME,
                    dataType= Boolean)
            result = memObj.setValue(True)
            if not result.isOK:
                raise Exception(
                    f"[{type(self).prefixCls}] Failed to set {constants.PLC_OPEN_CLIENT_CONNECT_EXTRA_SYMBOL_NAME} "
                    "to True")
            time.sleep(5)
            self.logger.newStep(f"Checking now that number of used external clients again should be"
                                f" {maxExtSessionCount}")
            connectedClientCount = self._getUsedExternalClientsCount()

            if connectedClientCount == maxExtSessionCount:
                self.logger.info(
                    f"[{type(self).prefixCls}] Verified that number of used external clients ({connectedClientCount})"
                    f" is {maxExtSessionCount}")
            else:
                raise Exception(
                    f"[{type(self).prefixCls}] Number of used external sessions clients ({connectedClientCount}) is not"
                    f" equal to {maxExtSessionCount}")

            # Checking for OPC UA AC Rejected failure in controller logbook
            self.logger.newStep(
                f"Checking for '{constants.OPC_AC_REJECTED_LOGBOOK_MSG}' msg in controller logbook")
            logMsgs = plcObj.readLogbookMsgs(projName = constants.PLC_PROJ_NAME)
            if constants.OPC_AC_REJECTED_LOGBOOK_MSG not in logMsgs:
                raise Exception(f"'{constants.OPC_AC_REJECTED_LOGBOOK_MSG}' not found in controller logbook")
            self.logger.info(f"'{constants.OPC_AC_REJECTED_LOGBOOK_MSG}' found in controller logbook")

            self._logDescAndupdateResult(result = True)

        except Exception as ex:  # pylint: disable=broad-exception-caught
            self._logDescAndupdateResult(result = False, remark = str(ex))
            self.testCase.fail(ex)

        finally:
            # Disconnected all PLC open clients
            self._disconnectAllPLCOpenClients()

            if not plcObj.goOffline(projName = constants.PLC_PROJ_NAME, header = plcObj.header):
                self.logger.warning("Failed to go offline")

    #-------------------------------------------------------------------------------------------------------------------
    def grp_08_tc_01(self) -> None:
        """
        TC4.4 Verify reading the PLC Designer variable PubSub data using the same c5xx controller as publisher and
        subscriber fot AC OPC UA = 150 credits
        """
        acOpcUaCreds = 150
        try:
            plcObj = Lib_OpcUa_LLM.PLCD_OBJECT

            # Deleting the Pub Sub configuration from Ua Expert
            self.logger.newStep("Deleting the pub sub config from controller using Ua Expert")
            if not self._dwnldOrDeletePubSubConfigToCtrl(downloadFlag = False):
                raise Exception("Failed to delete the pub sub config")

            # Deleting the controller logbook
            self.logger.newStep("Deleting the controller logbook")
            if not plcObj.goOnline():
                raise Exception("Failed to go online with the controller")

            if not plcObj.deleteLogs(projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to delete the controller logbook")

            if not plcObj.goOffline(projName = constants.PLC_PROJ_NAME, header = plcObj.header):
                raise Exception("Failed to go offline after clearing the logbook")

            # Opening License Manager in PLC tool
            if not plcObj.openLicenseManager(projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to open license manager in PLCD tool")

            # Setting License Configuration mode to Static AC configuration
            self.logger.newStep("Set configuration mode in License Manager to Static AC configuration")
            if not plcObj.setConfigModeInLicenseManager(configModeName = constants.CONFIG_MODE_STATIC_AC_STR,
                                                        projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to set config mode in License Manager to Static AC configuration")

            # Setting Application credits for FAST Toolbox on License Manager window
            self.logger.newStep("Set FAST Toolbox Application credits to 0")
            if not plcObj.setFastToolboxAppCreds(appCreditsToSet = 0,
                                                 projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to set Application credits for FAST Toolbox in License Manager")

            # Setting Application credits for FAST UI on License Manager window
            self.logger.newStep("Set FAST UI Application credits to 0")
            if not plcObj.setFastUiAppCreds(appCreditsToSet = 0,
                                            projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to set Application credits for FAST UI in License Manager")

            # Setting Application credits for Device Features on License Manager window
            self.logger.newStep("Set Device Features Application credits to 0")
            if not plcObj.setDeviceFeaturesAppCreds(appCreditsToSet = 0,
                                                    projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to set Application credits for FAST Service in License Manager")

            # Setting Application credits for OPC UA on License Manager window
            self.logger.newStep(f"Set OPC UA Application credits to {acOpcUaCreds}")
            if not plcObj.setOpcUaAppCreds(appCreditsToSet = acOpcUaCreds, projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to set Application credits for OPC UA in License Manager")

            # Disconnecting IPC before going online as Application credit assignment in the controller and in the PLCD
            # project might be different
            self.ipc.disconnect()

            # Going online downloading changes to the controller
            self.logger.newStep("Downloading project to the controller")
            if not plcObj.goOnline():
                raise Exception("Failed to go online with the controller")

            if not plcObj.goOffline(projName = constants.PLC_PROJ_NAME, header = plcObj.header):
                raise Exception("Failed to Go offline in plcd project ")

            # Setting pub sub activation to Disabled
            self.logger.info("Setting Pub Sub Activation value to Enabled")
            paramIdx, paramSubIdx = constants.PUB_SUB_ACTIVATION_PARAM_STR.split(':')
            param = self.ipc.objByIdx(index = int(paramIdx, 16), subIndex = int(paramSubIdx))
            result = param.setValue(constants.PUB_SUB_ACTIVATION_ENABLED_VALUE)
            if not result.isOK:
                raise Exception("Failed to set Pub Sub Activation to Enabled")

            # Saving the changed parameter
            try:
                self.ipc.cmd.paramSave()
            except Exception:  # pylint: disable=broad-exception-caught
                self.logger.newStep("Param save failed")

            # Going online downloading changes to the controller
            self.logger.newStep("Downloading project to the controller and upload values from controller")
            if not plcObj.goOnline(upload = True):
                raise Exception("Failed to go online with the controller")

            # Creating online boot project
            self.logger.newStep("Create online boot project")
            if not plcObj.createBootProject(projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to create online boot project")

            # Rebooting the controller
            self.logger.newStep("Reboot controller")
            if not self.restartController():
                raise Exception("Failed to reboot the controller")

            # Handle no connection pop up
            plcObj.handlePLCConnectionLost(header = plcObj.header)

            self.logger.newStep("Start application", level = 3)
            self.ipc.cmd.appStart()

            # Checking if pub sub diagnosis is in running state
            self.logger.info("Checking that Pub Sub diagnosis is not in Disabled state")
            paramIdx, paramSubIdx = constants.OPC_UA_PUB_SUB_STATE_PARAM_STR.split(':')
            param = self.ipc.objByIdx(index = int(paramIdx, 16), subIndex = int(paramSubIdx))
            result = param.getValue()
            if not result.isOK:
                raise Exception("Failed to read OPC UA Pub Sub Diagnosis: Pub Sub State parameter")

            readVal = result.value
            if readVal != constants.OPC_UA_PUB_SUB_STATE_DISABLE_VALUE:
                self.logger.info(
                    f"Successfully verified that OPC UA Pub Sub Diagnosis: Pub Sub State parameter value is not "
                    "Disabled")
            else:
                raise Exception(f"OPC UA Pub Sub Diagnosis: Pub Sub State parameter value ({readVal}) -> Disabled")

            # Downloading the Pub Sub configuration from Ua Expert
            self.logger.newStep("Downloading the pub sub config to controller using Ua Expert")
            pubSubDownloadStatus = self._dwnldOrDeletePubSubConfigToCtrl()

            if not pubSubDownloadStatus:
                raise Exception("Failed to download Pub Sub Configuration in Ua Expert")

            self.logger.newStep(
                "Checking if Sub variable's value is automatically changing",
                level = 3)
            self.ipc.cmd.appStart()
            if not self._checkIfVarValsChanging():
                raise Exception("Sub variable values are not automatically changing")

            self.logger.newStep(
                "Updating pub var 3 times Checking if sub var is receiving value from pub var for each iteration",
                level = 3)
            controllerFam = constants.CONTROLLER_FAMILY_MAP[self.xlsReaderObj.controllerType]

            res = []
            for _ in range(3):
                pubSubRes = self._checkPubSubVarUpdate(pubNodeStr = constants.PUB_VAR_NODESTRING.format(controllerFam),
                                                       subNodeStr = constants.SUB_VAR_NODESTRING.format(controllerFam))
                res.append(pubSubRes)

            if res and False not in res:
                self.logger.info(f"[{type(self).prefixCls}] Sub var successfully received values from Pub vars")
            else:
                raise Exception(f"[{type(self).prefixCls}] Sub var failed to receive values from Pub vars")
            self._logDescAndupdateResult(result = True)
        except Exception as ex:  # pylint: disable=broad-exception-caught
            self._logDescAndupdateResult(result = False, remark = str(ex))
            self.testCase.fail(ex)

    #-------------------------------------------------------------------------------------------------------------------
    def grp_08_tc_02(self) -> None:
        """
        TC4.5 Verify reading the PLC Designer variable PubSub data using the same c5xx controller as publisher and
        subscriber for AC OPC UA =0 credits
        """
        try:
            plcObj = Lib_OpcUa_LLM.PLCD_OBJECT

            # Opening License Manager in PLC tool
            if not plcObj.openLicenseManager(projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to open license manager in PLCD tool")

            # Setting License Configuration mode to Static AC configuration
            self.logger.newStep("Set configuration mode in License Manager to Static AC configuration")
            if not plcObj.setConfigModeInLicenseManager(configModeName = constants.CONFIG_MODE_STATIC_AC_STR,
                                                        projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to set config mode in License Manager to Static AC configuration")

            # Setting Application credits for FAST Toolbox on License Manager window
            self.logger.newStep("Set FAST Toolbox Application credits to 0")
            if not plcObj.setFastToolboxAppCreds(appCreditsToSet = 0,
                                                 projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to set Application credits for FAST Toolbox in License Manager")

            # Setting Application credits for FAST UI on License Manager window
            self.logger.newStep("Set FAST UI Application credits to 0")
            if not plcObj.setFastUiAppCreds(appCreditsToSet = 0,
                                            projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to set Application credits for FAST UI in License Manager")

            # Setting Application credits for Device Features on License Manager window
            self.logger.newStep("Set Device Features Application credits to 0")
            if not plcObj.setDeviceFeaturesAppCreds(appCreditsToSet = 0,
                                                    projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to set Application credits for FAST Service in License Manager")

            # Setting Application credits for OPC UA on License Manager window
            self.logger.newStep("Set OPC UA Application credits to 0")
            if not plcObj.setOpcUaAppCreds(appCreditsToSet = 0, projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to set Application credits for OPC UA in License Manager")

            # Disconnecting IPC before going online as Application credit assignment in the controller and in the PLCD
            # project might be different
            self.ipc.disconnect()

            # Going online downloading changes to the controller
            self.logger.newStep("Downloading project to the controller")
            if not plcObj.goOnline():
                raise Exception("Failed to go online with the controller")

            # Creating online boot project
            self.logger.newStep("Create online boot project")
            if not plcObj.createBootProject(projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to create online boot project")

            # Rebooting the controller
            self.logger.newStep("Reboot controller")
            if not self.restartController():
                raise Exception("Failed to reboot the controller")

            # Handle no connection pop up
            plcObj.handlePLCConnectionLost(header = plcObj.header)

            # Opening License Manager in PLC tool
            if not plcObj.openLicenseManager(projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to open license manager in PLCD tool")

            # Setting License Configuration mode to Static AC configuration
            self.logger.newStep("Set configuration mode in License Manager to Static AC configuration")
            if not plcObj.setConfigModeInLicenseManager(configModeName = constants.CONFIG_MODE_STATIC_AC_STR,
                                                        projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to set config mode in License Manager to Static AC configuration")

            # Setting Application credits for FAST Toolbox on License Manager window
            self.logger.newStep("Set FAST Toolbox Application credits to 0")
            if not plcObj.setFastToolboxAppCreds(appCreditsToSet = 1000,
                                                 projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to set Application credits for FAST Toolbox in License Manager")

            # Setting Application credits for FAST UI on License Manager window
            self.logger.newStep("Set FAST UI Application credits to 0")
            if not plcObj.setFastUiAppCreds(appCreditsToSet = 0,
                                            projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to set Application credits for FAST UI in License Manager")

            # Setting Application credits for Device Features on License Manager window
            self.logger.newStep("Set Device Features Application credits to 0")
            if not plcObj.setDeviceFeaturesAppCreds(appCreditsToSet = 0,
                                                    projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to set Application credits for FAST Service in License Manager")

            # Setting Application credits for OPC UA on License Manager window
            self.logger.newStep("Set OPC UA Application credits to 0")
            if not plcObj.setOpcUaAppCreds(appCreditsToSet = 0, projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to set Application credits for OPC UA in License Manager")

            # Disconnecting IPC before going online as Application credit assignment in the controller and in the PLCD
            # project might be different
            self.ipc.disconnect()

            # Going online downloading changes to the controller
            self.logger.newStep("Downloading project to the controller")
            if not plcObj.goOnline():
                raise Exception("Failed to go online with the controller")

            if not plcObj.goOffline(projName = constants.PLC_PROJ_NAME, header = plcObj.header):
                raise Exception("Failed to Go offline in plcd project ")

            # Setting pub sub activation to Enabled
            self.logger.info("Setting Pub Sub Activation value to Enabled")
            paramIdx, paramSubIdx = constants.PUB_SUB_ACTIVATION_PARAM_STR.split(':')
            param = self.ipc.objByIdx(index = int(paramIdx, 16), subIndex = int(paramSubIdx))
            result = param.setValue(constants.PUB_SUB_ACTIVATION_ENABLED_VALUE)
            if not result.isOK:
                raise Exception("Failed to set Pub Sub Activation to Enabled")

            # Saving the changed parameter
            try:
                self.ipc.cmd.paramSave()
            except Exception:  # pylint: disable=broad-exception-caught
                self.logger.newStep("Param save failed")

            # Going online downloading changes to the controller
            self.logger.newStep("Downloading project to the controller")
            if not plcObj.goOnline(upload = True):
                raise Exception("Failed to go online with the controller")

            # Creating online boot project
            self.logger.newStep("Create online boot project")
            if not plcObj.createBootProject(projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to create online boot project")

            self.logger.newStep("Deleting logs from PLC logbook")
            if not plcObj.deleteLogs(projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to delete the controller logbook")

            self.logger.newStep("Deleting logs from Lenze Diagnosis tool")
            if not self._clearLogsFromDiagnosis():
                raise Exception("Failed to delete the Lenze Diagnosis logbook")

            # Rebooting the controller
            self.logger.newStep("Reboot controller")
            if not self.restartController():
                raise Exception("Failed to reboot the controller")

            # Handle no connection pop up
            plcObj.handlePLCConnectionLost(header = plcObj.header)

            # Going online downloading changes to the controller
            self.logger.newStep("Downloading project to the controller")
            if not plcObj.goOnline(upload = True):
                raise Exception("Failed to go online with the controller")

            self.logger.newStep("Start application", level = 3)
            self.ipc.cmd.appStart()

            # Checking for pub sub config failure msg in controller logbook
            self.logger.newStep(
                f"Checking for '{constants.PUB_SUB_CONFIG_FAILED_LOGBOOK_MSG}' msg in controller logbook")
            logMsgs = plcObj.readLogbookMsgs(projName = constants.PLC_PROJ_NAME)
            if constants.PUB_SUB_CONFIG_FAILED_LOGBOOK_MSG not in logMsgs:
                self.logger.info(f"{logMsgs}")
                raise Exception(f"'{constants.PUB_SUB_CONFIG_FAILED_LOGBOOK_MSG}' not found in controller logbook")
            self.logger.info(f"'{constants.PUB_SUB_CONFIG_FAILED_LOGBOOK_MSG}' found in controller logbook")

            # Checking pub sub activation to Disabled
            self.logger.info("Checking that OPC UA Pub Sub Diagnosis: Pub Sub State parameter is Disabled")
            paramIdx, paramSubIdx = constants.OPC_UA_PUB_SUB_STATE_PARAM_STR.split(':')
            param = self.ipc.objByIdx(index = int(paramIdx, 16), subIndex = int(paramSubIdx))
            result = param.getValue()
            if not result.isOK:
                raise Exception("Failed to read OPC UA Pub Sub Diagnosis: Pub Sub State parameter")

            readVal = result.value
            if readVal == constants.OPC_UA_PUB_SUB_STATE_DISABLE_VALUE:
                self.logger.info(
                    "Successfully verified that OPC UA Pub Sub Diagnosis: Pub Sub State parameter value is Disabled")
            else:
                raise Exception(f"OPC UA Pub Sub Diagnosis: Pub Sub State parameter value ({readVal}) != Disabled")

            # Checking for pub sub config failure msg in diagnosis tool logbook
            self.logger.newStep(
                f"Checking for '{constants.PUB_SUB_CONFIG_FAILED_LOGBOOK_MSG}' msg in Lenze Diagnosis Tool logbook")
            logMsgs = self._getLogsFromDiagnosis()
            if constants.PUB_SUB_CONFIG_FAILED_LOGBOOK_MSG not in logMsgs:
                self.logger.info(f"{logMsgs}")
                raise Exception(f"'{constants.PUB_SUB_CONFIG_FAILED_LOGBOOK_MSG}' not found in Lenze Diagnosis logbook")
            self.logger.info(f"'{constants.PUB_SUB_CONFIG_FAILED_LOGBOOK_MSG}' found in Lenze Diagnosis logbook")
            self._logDescAndupdateResult(result = True)
        except Exception as ex:  # pylint: disable=broad-exception-caught
            self._logDescAndupdateResult(result = False, remark = str(ex))
            self.testCase.fail(ex)

    #-------------------------------------------------------------------------------------------------------------------
    def grp_08_tc_03(self) -> None:
        """
        TC4.6 Verify reading the PLC Designer variable PubSub data using the same c5xx controller as publisher and
        subscriber with mode set as "ALL AC to FAST Toolbox" .
        """
        try:
            plcObj = Lib_OpcUa_LLM.PLCD_OBJECT

            # Opening License Manager in PLC tool
            if not plcObj.openLicenseManager(projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to open license manager in PLCD tool")

            # Setting License Configuration mode to Static AC configuration
            self.logger.newStep("Set configuration mode in License Manager to All AC to FAST Toolbox")
            if not plcObj.setConfigModeInLicenseManager(configModeName = constants.CONFIG_MODE_ALL_AC_TO_FAST_STR,
                                                        projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to set config mode in License Manager to All AC to FAST Toolbox")

            # Disconnecting IPC before going online as Application credit assignment in the controller and in the PLCD
            # project might be different
            self.ipc.disconnect()

            # Going online downloading changes to the controller
            self.logger.newStep("Downloading project to the controller")
            if not plcObj.goOnline():
                raise Exception("Failed to go online with the controller")

            if not plcObj.goOffline(projName = constants.PLC_PROJ_NAME, header = plcObj.header):
                raise Exception("Failed to Go offline in plcd project ")

            # Setting pub sub activation to Enabled
            self.logger.info("Setting Pub Sub Activation value to Enabled")
            paramIdx, paramSubIdx = constants.PUB_SUB_ACTIVATION_PARAM_STR.split(':')
            param = self.ipc.objByIdx(index = int(paramIdx, 16), subIndex = int(paramSubIdx))
            result = param.setValue(constants.PUB_SUB_ACTIVATION_ENABLED_VALUE)
            if not result.isOK:
                raise Exception("Failed to set Pub Sub Activation to Enabled")

            # Saving the changed parameter
            try:
                self.ipc.cmd.paramSave()
            except Exception:  # pylint: disable=broad-exception-caught
                self.logger.newStep("Param save failed")

            # Going online downloading changes to the controller
            self.logger.newStep("Downloading project to the controller")
            if not plcObj.goOnline(upload = True):
                raise Exception("Failed to go online with the controller")

            self.logger.newStep("Deleting logs from PLC logbook")
            if not plcObj.deleteLogs(projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to delete the controller logbook")

            self.logger.newStep("Deleting logs from Lenze Diagnosis tool")
            if not self._clearLogsFromDiagnosis():
                raise Exception("Failed to delete the Lenze Diagnosis logbook")

            # Creating online boot project
            self.logger.newStep("Create online boot project")
            if not plcObj.createBootProject(projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to create online boot project")

            # Rebooting the controller
            self.logger.newStep("Reboot controller")
            if not self.restartController():
                raise Exception("Failed to reboot the controller")

            # Handle no connection pop up
            plcObj.handlePLCConnectionLost(header = plcObj.header)

            # Downloading the Pub Sub configuration from Ua Expert
            self.logger.newStep("Downloading the pub sub config to controller using Ua Expert")
            pubSubDownloadStatus = self._dwnldOrDeletePubSubConfigToCtrl()
            if pubSubDownloadStatus:
                raise Exception("Pub Sub configuration download successful but was expected to fail")
            self.logger.info("Download of Pub Sub Configuration failed as expected")

            self.logger.newStep("Start application", level = 3)
            self.ipc.cmd.appStart()

            # Going online downloading changes to the controller
            self.logger.newStep("Downloading project to the controller")
            if not plcObj.goOnline(upload = True):
                raise Exception("Failed to go online with the controller")

            # Checking for pub sub config failure msg in controller logbook
            self.logger.newStep(
                f"Checking for '{constants.PUB_SUB_CONFIG_FAILED_LOGBOOK_MSG}' msg in controller logbook")
            logMsgs = plcObj.readLogbookMsgs(projName = constants.PLC_PROJ_NAME)
            if constants.PUB_SUB_CONFIG_FAILED_LOGBOOK_MSG not in logMsgs:
                raise Exception(f"'{constants.PUB_SUB_CONFIG_FAILED_LOGBOOK_MSG}' not found in controller logbook")
            self.logger.info(f"'{constants.PUB_SUB_CONFIG_FAILED_LOGBOOK_MSG}' found in controller logbook")

            # Checking for pub sub config failure msg in diagnosis tool logbook
            self.logger.newStep(
                f"Checking for '{constants.PUB_SUB_CONFIG_FAILED_LOGBOOK_MSG}' msg in Lenze Diagnosis Tool logbook")
            logMsgs = self._getLogsFromDiagnosis()
            if constants.PUB_SUB_CONFIG_FAILED_LOGBOOK_MSG not in logMsgs:
                raise Exception(f"'{constants.PUB_SUB_CONFIG_FAILED_LOGBOOK_MSG}' not found in Lenze Diagnosis logbook")
            self.logger.info(f"'{constants.PUB_SUB_CONFIG_FAILED_LOGBOOK_MSG}' found in Lenze Diagnosis  logbook")

            self.logger.newStep(
                "Updating pub var 3 times Checking if sub var is not receiving value from pub var for each iteration",
                level = 3)
            controllerFam = constants.CONTROLLER_FAMILY_MAP[self.xlsReaderObj.controllerType]

            res = []
            for _ in range(3):
                pubSubRes = self._checkPubSubVarUpdate(pubNodeStr = constants.PUB_VAR_NODESTRING.format(controllerFam),
                                                       subNodeStr = constants.SUB_VAR_NODESTRING.format(controllerFam))
                res.append(pubSubRes)

            if res and True not in res:
                self.logger.info(
                   f"[{type(self).prefixCls}] Successfully verified that sub var is not receiving value from pub var")
            else:
                raise Exception("Sub vars are receiving values from pub var which is not expected")
            self._logDescAndupdateResult(result = True)
        except Exception as ex:  # pylint: disable=broad-exception-caught
            self._logDescAndupdateResult(result = False, remark = str(ex))
            self.testCase.fail(ex)

    #-------------------------------------------------------------------------------------------------------------------
    def grp_09_tc_01(self) -> None:
        """
        TC4.7 Verify External Client session connections with "Static AC Configuration" mode and AC OPC UA = 100 with
        Parameter 0x247B PUB Sub --Enabled and PUB Sub configuration not downloaded
        """
        thirdPartyClientObjs = []
        try:
            plcObj = Lib_OpcUa_LLM.PLCD_OBJECT
            acOpcUaAppCreds = 100

            # Deleting the Pub Sub configuration from Ua Expert
            self.logger.newStep("Deleting the pub sub config from controller using Ua Expert")
            if not self._dwnldOrDeletePubSubConfigToCtrl(downloadFlag = False):
                raise Exception("Failed to delete the pub sub config")

            # Opening License Manager in PLC tool
            self.logger.newStep("Set configuration mode in License Manager to Static AC configuration")
            if not plcObj.openLicenseManager(projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to open license manager in PLCD tool")

            # Setting License Configuration mode to Static AC configuration
            if not plcObj.setConfigModeInLicenseManager(configModeName = constants.CONFIG_MODE_STATIC_AC_STR,
                                                        projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to set config mode in License Manager to Static AC configuration")

            # Setting Application credits for OPC UA on License Manager window
            self.logger.newStep(f"Set OPC UA Application credits to {acOpcUaAppCreds}")
            if not plcObj.setOpcUaAppCreds(appCreditsToSet = acOpcUaAppCreds,
                                           projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to set Application credits for OPC UA in License Manager")

            # Setting Application credits for FAST Toolbox on License Manager window
            self.logger.newStep("Set FAST Toolbox Application credits to 0")
            if not plcObj.setFastToolboxAppCreds(appCreditsToSet = 0,
                                                 projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to set Application credits for FAST Toolbox in License Manager")

            # Setting Application credits for FAST UI on License Manager window
            self.logger.newStep("Set FAST UI Application credits to 0")
            if not plcObj.setFastUiAppCreds(appCreditsToSet = 0,
                                            projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to set Application credits for FAST UI in License Manager")

            # Setting Application credits for Device Features on License Manager window
            self.logger.newStep("Set Device Features Application credits to 0")
            if not plcObj.setDeviceFeaturesAppCreds(appCreditsToSet = 0,
                                                    projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to set Application credits for FAST Service in License Manager")

            # Setting pub sub activation to Enabled
            self.logger.info("Setting Pub Sub Activation value to Enabled")
            paramIdx, paramSubIdx = constants.PUB_SUB_ACTIVATION_PARAM_STR.split(':')
            param = self.ipc.objByIdx(index = int(paramIdx, 16), subIndex = int(paramSubIdx))
            result = param.setValue(constants.PUB_SUB_ACTIVATION_ENABLED_VALUE)
            if not result.isOK:
                raise Exception("Failed to set Pub Sub Activation to Enabled")

            # Saving the changed parameter
            try:
                self.ipc.cmd.paramSave()
            except Exception:  # pylint: disable=broad-exception-caught
                self.logger.newStep("Param save failed")

            # Disconnecting IPC before going online as Application credit assignment in the controller and in the PLCD
            # project might be different
            self.ipc.disconnect()

            # Going online downloading changes to the controller
            self.logger.newStep("Downloading project to the controller")
            if not plcObj.goOnline(upload = True):
                raise Exception("Failed to go online with the controller")

            # Creating online boot project
            self.logger.newStep("Create online boot project")
            if not plcObj.createBootProject(projName = constants.PLC_PROJ_NAME):
                raise Exception("Failed to create online boot project")

            # Rebooting the controller
            self.logger.newStep("Reboot controller")
            if not self.restartController():
                raise Exception("Failed to reboot the controller")

            # Handle no connection pop up
            plcObj.handlePLCConnectionLost(header = plcObj.header)

            # Going online downloading changes to the controller
            self.logger.newStep("Connecting more than one external client and checking if connection is successful")
            thirdPartyClientObjs = self._getThirdPartyClients(noOfReqObjs = 2)
            if not self._connectAndVerifyConnections(listOfClientObjToConnect = thirdPartyClientObjs,
                                                     noOfExpectedConn = 2):
                raise Exception("Failed to connect more than one external session")
            self.logger.info("[%s] External sessions more than one successfully connected", type(self).prefixCls)

            self._logDescAndupdateResult(result = True)
        except Exception as ex:  # pylint: disable=broad-exception-caught
            self._logDescAndupdateResult(result = False, remark = str(ex))
            self.testCase.fail(ex)
        finally:
            if thirdPartyClientObjs:
                # Disconnected all THird party clients
                self._disconnectThirdPartyClients(clientObjsToDisconnectLi = thirdPartyClientObjs)
