# -*- coding: utf-8 -*-
#
# © 2007-2008 Lenze Drive Systems GmbH. All rights reserved.
# © 2008-2021 Lenze Automation GmbH. All rights reserved.
#
#-----------------------------------------------------------------------------------------------------------------------
# PyTeF file header (for Test Script) V1.4-01
#-----------------------------------------------------------------------------------------------------------------------
# Disable linter warnings -> OTHER DISABLES ARE NOT RECOMMENDED, CHANGES ARE AT YOUR OWN RISK!
# pylint: disable=wildcard-import,unused-wildcard-import
#
#-----------------------------------------------------------------------------------------------------------------------
# Test Script docstring (must be first definition in file)
#-----------------------------------------------------------------------------------------------------------------------
"""This is test runner file for OPC UA PLC Open Client FB Test
"""
#-----------------------------------------------------------------------------------------------------------------------
# Test Script imports (must be defined before code)
#-----------------------------------------------------------------------------------------------------------------------
from pytef.namespace.testcase import FwTestCase, FwTestObject, Version, TestBench, RevisionVersion
from tests.testlib.utils.CommonLib import clsLogger
from tests.opc_ua.plc_fb_test.utils.excelReader import ConfigExlParser as ConfigOpenClientFB
from tests.opc_ua.plc_fb_test.utils import constants_plc_fb as constants
from tests.opc_ua.plc_fb_test.lib.Lib_PLC_Open_Client_FB import Lib_PLC_Open_Client_FB

#-----------------------------------------------------------------------------------------------------------------------
# PyTeF file header end
#-----------------------------------------------------------------------------------------------------------------------
class Test_PLC_Open_Client_FB(FwTestCase):
    """
    class for OPC UA PLC Open Client FB Test Runner
    """
    prefixCls = 'Test_PLC_Open_Client_FB'

    #-------------------------------------------------------------------------------------------------------------------
    # SVN keyword section
    #-------------------------------------------------------------------------------------------------------------------
    TEST_URL = "$HeadURL: $"[10:-2]  # noqa: E501
    TEST_REV = "$Revision: $"[11:-2]
    TEST_DATE = "$LastChangedDate: $"[18:-2]
    TEST_AUTHOR = "$LastChangedBy: raina $"[16:-2]
    TEST_VERSION = RevisionVersion(1, 0, 0, TEST_REV)

    #-------------------------------------------------------------------------------------------------------------------
    # Test manager section
    #-------------------------------------------------------------------------------------------------------------------
    # : Define the test object(s) of the testcases here.
    TEST_OBJS = [FwTestObject.NOT_DEFINED]

    # : While developing / debugging a test, you can set the valid (more detailed) test object here.
    #  It's only used, if this test script is directly started and is not part of a test suite.
    #  This object (if defined) is added as first element in TEST_OBJS.
    #  That way is easier as creating a test run configuration or to modify the TEST_OBJS.
    TEST_OBJ_DEVEL = FwTestObject.NOT_DEFINED

    # : Specify the test keys for the testcases in the class here.
    TEST_KEYS = ["opcua.plcopenclientfb"]

    # : TestReview-Instanz, created by a test manager after a review.
    TESTMGR_REVIEW = None

    #-------------------------------------------------------------------------------------------------------------------
    # Pytef manager section
    #-------------------------------------------------------------------------------------------------------------------
    # : This test class is runnable with this PyTeF version.
    PYTEF_VERSION = Version(2, 0, 0)

    #: TestReview-Instanz, created by a PyTeF developer after a review.
    PYTEF_REVIEW = None

    #-------------------------------------------------------------------------------------------------------------------
    def __init__(self, **kwargs) -> None:
        """
        Constructor of a testcase in this class.

        Describe all needed resources in Sphinx-Syntax.

        .. warning:: This Constructor is called by the framework while creating the test suite
                     for EVERY singe testcase in this class.
                     It's NOR called once NEITHER directly before every testcase!!!
        """

        super().__init__(**kwargs)

        # Here you can request your resources and define your attributes.
        # Note: You can use and create Templates, which are defined in
        #       -> Preferences -> PyDev -> Editor -> Templates
        #       The newest Templates you can import are here:
        #       <pytef>/templates/eclipse/pydev/templates

        initArgs = {"fbTestModeList": [constants.FBMode.FIXED_NODE],
                    "fbTestImpementation": constants.FBImplementation.VARIABLE_RW_CONNECT}

        self.libPLCOpenClientFB = self.resource.testLib(relModName = r"lib\Lib_PLC_Open_Client_FB",
                                                        libName = "Lib_PLC_Open_Client_FB",
                                                        relToFile = __file__,
                                                        initKwargs= initArgs)

    @classmethod
    def autoCreateTestCases(cls) -> None:
        """Example to create test cases by parameters - here 900 test cases!!

        An implementation by typing all tc_* methods in this class in not needed any more.
        The test case specific parameters you get in the test code by self.testself.resultDict.get(myAttr)

        Actual it's not possible to hand
        """
        Lib_PLC_Open_Client_FB.createTests(cls)

    #-------------------------------------------------------------------------------------------------------------------
    def autoTestFunc(self) -> None:
        """
        Auto Test Function
        """
        funcName = self.testParamDict.get('funcName')

        self.logger.info("[%s] funcName = %s", type(self).prefixCls, funcName)

        func = getattr(self, funcName)
        func()

    #-------------------------------------------------------------------------------------------------------------------
    def setUpClass(self) -> None:
        """
        setUpClass for Opc Ua test runner: calls setUpClass from Lib_OpcUa_LLM
        """

        self.logger.info("[%s] Preparing things for all testcases in this class ...", type(self).prefixCls)

        self.logger.info("[%s] Description of this class:", type(self).prefixCls)
        self.logger.info("[%s] %s", type(self).prefixCls, self.testClsDoc)
        self.libPLCOpenClientFB.setUpClass()

    #-------------------------------------------------------------------------------------------------------------------
    def tearDownClass(self) -> None:
        """
        tearDownClass for Opc Ua test runner
        """
        self.logger.info("[%s] Post processing the test class ...", type(self).prefixCls)
        self.libPLCOpenClientFB.tearDownClass()

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Group1(self) -> None:
        """
        Executes Group 01 test cases for internal server variable data operations.

        This group includes:
        - TC01: Verifies reading of variable data from the internal server.
        - TC02: Verifies writing of variable data to the internal server.
        - TC03: Verifies simultaneous read/write operations on variable data for the internal server.

        Returns:
            None
        """

        self.libPLCOpenClientFB.executeGroup1()

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Group2(self) -> None:
        """
        Executes Group 02 test cases for c550 external server variable data operations.

        This group includes:
        - TC04: Verifies reading of variable data from the c550 external server.
        - TC05: Verifies writing of variable data to the c550 external server.
        - TC06: Verifies simultaneous read/write operations on variable data for the c550 external server.

        Returns:
            None
        """

        self.libPLCOpenClientFB.executeGroup2()

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Group3(self) -> None:
        """
        Executes Group 03 test cases for c520 external server variable data operations.

        This group includes:
        - TC07: Verifies reading of variable data from the c520 external server.
        - TC08: Verifies writing of variable data to the c520 external server.
        - TC09: Verifies simultaneous read/write operations on variable data for the c520 external server.

        Returns:
            None
        """

        self.libPLCOpenClientFB.executeGroup3()

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Group4(self) -> None:
        """
        Executes Group 04 test cases for 3rd-party controller external server operations.

        This group includes:
        - TC10: Verifies reading of variable data from a 3rd-party controller external server.
        - TC11: Verifies writing of variable data to a 3rd-party controller external server.
        - TC12: Verifies simultaneous read/write operations on variable data for a 3rd-party controller external server.

        Returns:
            None
        """

        self.libPLCOpenClientFB.executeGroup4()

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Group5(self) -> None:
        """
        Executes Group 05 test cases for multiple external server variable data operations.

        This group includes:
        - TC13: Verifies reading of variable data from multiple external servers.
        - TC14: Verifies writing of variable data to multiple external servers.
        - TC15: Verifies simultaneous read/write operations on variable data for multiple external servers.

        Returns:
            None
        """

        self.libPLCOpenClientFB.executeGroup5()


#-----------------------------------------------------------------------------------------------------------------------
#    MAIN Program
#-----------------------------------------------------------------------------------------------------------------------
# Note: The following code is executed if you start this file directly!
if __name__ == "__main__":
    logger = clsLogger()
    xlsReaderObj = ConfigOpenClientFB(configFile = constants.CONFIG_FILE_FB_PATH, logger = logger)
    TestBench.main(testFileName = __file__)
