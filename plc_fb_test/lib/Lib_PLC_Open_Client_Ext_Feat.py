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
from typing import Callable, List, Self
from pytef.namespace.testlib import (Version, Result, autobehavior, tyOptBehavior)

from tests.testlib.utils.CommonLib import clsLogger
from tests.opc_ua.plc_fb_test.lib.Lib_Base import Lib_Base
from tests.opc_ua.plc_fb_test.utils.excelReader import ConfigExlParser as ConfigOpenClientExtFeat
from tests.opc_ua.plc_fb_test.utils.excelReportUpdater import ReportExlParser as ReportExlParserClientExtFeat
from tests.opc_ua.plc_fb_test.utils import constants_plc_fb as constants

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
        def wrapper(self: Self, *args, **kwargs) -> List[bool]:
            self.logTestDescription(result = [])

            testResults, testRemarks = func(self, *args, **kwargs)

            self.saveTestResult(results = testResults, remarks = testRemarks)
            self.logTestDescription(result = testResults, isEnd = True)

            return testResults
        return wrapper
    return decorator

#-----------------------------------------------------------------------------------------------------------------------
class Lib_PLC_Open_Client_Ext_Feat(Lib_Base):
    """
        OPC UA PLC Open Client Extended Feature
    """
    prefixCls = 'Lib_PLC_Open_Client_Ext_Feat'
    __LIB_DICT = {}

    LIB_NAME = "Lib_PLC_Open_Client_Ext_Feat"
    LIB_VERSION = Version(1, 0, 0)

    #-------------------------------------------------------------------------------------------------------------------
    def __init__(self, fbTestModeList, fbTestImpementation) -> None:
        """
        Constructor
        """

        self.logger.info(f"[{type(self).prefixCls}] in Lib_PLC_Open_Client_Ext_Feat::__init__()")
        self.xlsReaderObj = ConfigOpenClientExtFeat(
            configFile = constants.CONFIG_FILE_FB_EXT_PATH, logger = self.logger)

        self.reportUpdaterObj = ReportExlParserClientExtFeat(reportFile = constants.REPORT_FILE_FB_EXT_PATH,
                                                             sheetName = constants.REPORT_SHEET_FB_EXT_NAME,
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
        xlsReaderObj = ConfigOpenClientExtFeat(configFile = constants.CONFIG_FILE_FB_EXT_PATH, logger = logger)

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
    @autobehavior
    def setUpClass(self, behavior: tyOptBehavior = None, **kwargs) -> Result:
        """
        Method to setup the library content (allocated resources).

        The method can be called form the <testcase>.setUpClass() to setup all allocated resources.

        :param behavior:  Auto behavior of this method.
        :returns: Result
        """

        super().setUpClass(behavior = behavior)
        if not self.downloadPlcdProjects():
            self.testCase.skipTest("Failed to download project in the selected controller")

        self.reportUpdaterObj.updateReportHeader(
            header = constants.REPORT_FB_EXT_HEADER.format(self.findCtrlType(self.ipcHostController),
                                                           self.xlsReaderObj.releaseName))

        return Result(errorCode = Result.NO_ERROR, errorMessage = "Success")

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def executeGroup1(self):
        """
        TC01: Verify Read Data from External server using node information obtained from UA Browse and
        Translate Path Function
        Execute Test case 01 from Group 01

        TC02: Write varibles from External server using node information obtained from UA Browse and
        Translate Path Function
        Execute Test case 02 from Group 01

        TC03: Write and Read varibles from External server using node information obtained from UA Browse and
        Translate Path Function
        Execute Test case 03 from Group 01

        TC04: Call & Execute Method from External server using node information obtained from UA Browse and
        Translate Path Function
        Execute Test case 04 from Group 01
        """

        testResult, testRemarks = self._executeGroup(testType = constants.TestType.EXTERNAL.value)
        return testResult, testRemarks

    #-------------------------------------------------------------------------------------------------------------------
    @logTestDetails()
    def executeGroup2(self):
        """
        TC06: Read varibles from Multiple server using node information obtained from UA Browse and
        Translate Path Function
        Execute Test case 01 from Group 02

        TC07: Write varibles from Multiple server using node information obtained from UA Browse and
        Translate Path Function
        Execute Test case 02 from Group 02

        TC08: Write and Read varibles from Multiple server using node information obtained from UA Browse and
        Translate Path Function
        Execute Test case 03 from Group 02

        TC09: Call & Execute Method from Multiple server using node information obtained from UA Browse and
        Translate Path Function
        Execute Test case 04 from Group 02
        """

        testResult, testRemarks = self._executeGroup(testType = constants.TestType.MULTIPLE.value)
        return testResult, testRemarks
