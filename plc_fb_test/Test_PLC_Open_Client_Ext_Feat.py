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
"""This is test runner file for OPC UA PLC Open Client Extended Feature Test
"""
#-----------------------------------------------------------------------------------------------------------------------
# Test Script imports (must be defined before code)
#-----------------------------------------------------------------------------------------------------------------------
from pytef.namespace.testcase import FwTestCase, FwTestObject, Version, TestBench
from tests.testlib.utils.CommonLib import clsLogger
from tests.opc_ua.plc_fb_test.utils.excelReader import ConfigExlParser as ConfigOpenClientExtFeat
from tests.opc_ua.plc_fb_test.utils import constants_plc_fb as constants
from tests.opc_ua.plc_fb_test.lib.Lib_PLC_Open_Client_Ext_Feat import Lib_PLC_Open_Client_Ext_Feat

#-----------------------------------------------------------------------------------------------------------------------
# PyTeF file header end
#-----------------------------------------------------------------------------------------------------------------------
class Test_PLC_Open_Client_Ext_Feat(FwTestCase):
    """
    class for OPC UA PLC Open Client Extended Feature Test Runner
    """
    prefixCls = 'Test_PLC_Open_Client_Ext_Feat'

    #-------------------------------------------------------------------------------------------------------------------
    # SVN keyword section
    #-------------------------------------------------------------------------------------------------------------------
    TEST_URL = "$HeadURL: $"[10:-2]  # noqa: E501
    TEST_REV = "$Revision: $"[11:-2]
    TEST_DATE = "$LastChangedDate: $"[18:-2]
    TEST_AUTHOR = "$LastChangedBy: raina $"[16:-2]
    # TEST_VERSION = RevisionVersion(1, 0, 0, TEST_REV)

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

        initArgs = {"fbTestModeList": [
            constants.FBMode.BROWSE,
            constants.FBMode.TRANSLATE_PATH,
            constants.FBMode.B_T_PASSING],
            "fbTestImpementation": constants.FBImplementation.VARIABLE_RW_METHOD_CONNECT
            }

        self.libPLCOpenClientExtFeat = self.resource.testLib(relModName = r"lib\Lib_PLC_Open_Client_Ext_Feat",
                                                             libName = "Lib_PLC_Open_Client_Ext_Feat",
                                                             relToFile = __file__,
                                                             initKwargs = initArgs)

    @classmethod
    def autoCreateTestCases(cls) -> None:
        """Example to create test cases by parameters - here 900 test cases!!

        An implementation by typing all tc_* methods in this class in not needed any more.
        The test case specific parameters you get in the test code by self.testself.resultDict.get(myAttr)

        Actual it's not possible to hand
        """
        Lib_PLC_Open_Client_Ext_Feat.createTests(cls)

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
        self.libPLCOpenClientExtFeat.setUpClass()

    #-------------------------------------------------------------------------------------------------------------------
    def tearDownClass(self) -> None:
        """
        tearDownClass for Opc Ua test runner
        """
        self.logger.info("[%s] Post processing the test class ...", type(self).prefixCls)
        self.libPLCOpenClientExtFeat.tearDownClass()

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Group1(self) -> None:
        """
        TC01: Verify Reading of Variable data from Internal Server
        Execute Test case 01 from Group 01

        TC02: Verify Writing of Variable data to Internal Server
        Execute Test case 02 from Group 01

        TC03: Verify Simultaneous Read / Write operation for variable data for Internal Server
        Execute Test case 03 from Group 01
        """
        self.libPLCOpenClientExtFeat.executeGroup1()

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Group2(self) -> None:
        """
        TC04: Verify Reading of Variable data from c550 External Server
        Execute Test case 01 from Group 02

        TC05: Verify Writing of Variable data to c550 External Server
        Execute Test case 02 from Group 02

        TC06: Verify Simultaneous Read / Write operation for variable data for c550 External Server
        Execute Test case 03 from Group 02
        """
        self.libPLCOpenClientExtFeat.executeGroup2()


#-----------------------------------------------------------------------------------------------------------------------
#    MAIN Program
#-----------------------------------------------------------------------------------------------------------------------
# Note: The following code is executed if you start this file directly!
if __name__ == "__main__":
    logger = clsLogger()
    xlsReaderObj = ConfigOpenClientExtFeat(configFile = constants.CONFIG_FILE_FB_EXT_PATH, logger = logger)
    TestBench.main(testFileName = __file__)
