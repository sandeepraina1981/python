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
"""This is test runner file for OPC UA LLM Test
"""
#-----------------------------------------------------------------------------------------------------------------------
# Test Script imports (must be defined before code)
#-----------------------------------------------------------------------------------------------------------------------
import sys
from pytef.namespace.testcase import FwTestCase, RevisionVersion, FwTestObject, Version, TestBench
from tests.testlib.utils.CommonLib import isEclipseRunningAsAdmin, clsLogger
from tests.testlib.seleniumLib.SeleniumLib import SeleniumLib
from tests.opc_ua.opc_ua_llm_test.lib.Lib_OpcUa_LLM import Lib_OpcUa_LLM
from tests.testlib.utils.InterpreterValidation import ValidateInterpreter
from tests.opc_ua.opc_ua_llm_test.utils.excelReader import ConfigExlParser
from tests.opc_ua.opc_ua_llm_test.utils import constants_llm as constants

#-----------------------------------------------------------------------------------------------------------------------
# PyTeF file header end
#-----------------------------------------------------------------------------------------------------------------------
class Test_OpcUa_LLM(FwTestCase):
    """
    class for OPC UA LLM Test Runner
    """
    prefixCls = 'Test_OpcUa_LLM'

    #-------------------------------------------------------------------------------------------------------------------
    # SVN keyword section
    #-------------------------------------------------------------------------------------------------------------------
    TEST_URL = "$HeadURL: http://repository.lenze.com/ssv/TestRepository/branches/sdc/tests/common/opc_ua/Test_OpcUa.py $"[10:-2]  # noqa: E501
    TEST_REV = "$Revision: 9122 $"[11:-2]
    TEST_DATE = "$LastChangedDate: 2022-05-19 18:21:47 +0530 (Thu, 19 May 2022) $"[18:-2]
    TEST_AUTHOR = "$LastChangedBy: kolten $"[16:-2]
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
    TEST_KEYS = ["opc.test"]

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

        initArgs = ()
        self.libOpcUaLLM = self.resource.testLib(relModName = r"lib\Lib_OpcUa_LLM",
                                                 libName = "Lib_OpcUa_LLM",
                                                 relToFile = __file__,
                                                 initArgs = initArgs)

    #-------------------------------------------------------------------------------------------------------------------
    @classmethod
    def autoCreateTestCases(cls) -> None:
        """Example to create test cases by parameters - here 900 test cases!!

        An implementation by typing all tc_* methods in this class in not needed any more.
        The test case specific parameters you get in the test code by self.testself.resultDict.get(myAttr)

        Actual it's not possible to hand
        """
        Lib_OpcUa_LLM.createTests(cls)

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
        self.libOpcUaLLM.setUpClass()

    #-------------------------------------------------------------------------------------------------------------------
    def tearDownClass(self) -> None:
        """
        tearDownClass for Opc Ua test runner
        """
        self.logger.info("[%s] Post processing the test class ...", type(self).prefixCls)
        self.libOpcUaLLM.tearDownClass()

    #-------------------------------------------------------------------------------------------------------------------
    def setUp(self) -> None:
        """
        setUp for Opc Ua test runner: calls setUpClass from Lib_OpcUa_LLM
        """

        self.logger.info("[%s] Preparing a single testcase ...", type(self).prefixCls)
        self.libOpcUaLLM.setUp()

    #-------------------------------------------------------------------------------------------------------------------
    def tearDown(self) -> None:
        """
        tearDown for Opc Ua test runner: calls setUpClass from Lib_OpcUa_LLM
        """

        self.logger.info("[%s] Post processing a single testcase ...", type(self).prefixCls)
        self.libOpcUaLLM.tearDown()

    #-------------------------------------------------------------------------------------------------------------------
    def abortHandler(self) -> None:
        """
        abortHandler for Opc Ua test runner
        """

        self.logger.info("[%s] Executing the abort handler of the class ...", type(self).prefixCls)

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp1_TC1(self) -> None:
        """
        Download the project in the controller using PLC Designer tool

        """
        self.libOpcUaLLM.grp_01_tc_01()

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp2_TC1(self) -> None:
        """
        Verify External Client session connections with "Static AC Configuration" mode and AC OPC UA = 0 for different\
         Max Server Settings (Parameter-0x2472 (103))

            .. image:: images/sequenceDiagrams/1_1.png

        """
        self.libOpcUaLLM.grp_02_tc_01()

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp2_TC2(self) -> None:
        """
        Verify External Client session connections with "Static AC Configuration" mode and AC OPC UA = 100 for \
         different Max Server Settings (Parameter-0x2472 (103))

            .. image:: images/sequenceDiagrams/1_2.png

        """
        self.libOpcUaLLM.grp_02_tc_02()

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp2_TC3(self) -> None:
        """
        Verify External Client session connections with "Static AC Configuration" mode and AC OPC UA = 150 for \
        different Max Server Settings (Parameter-0x2472 (103))

            .. image:: images/sequenceDiagrams/1_3.png

        """
        self.libOpcUaLLM.grp_02_tc_03()

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp3_TC1(self) -> None:
        """
        Verify External Client session connections for different settings for AC OPC UA with mode set as \
        "ALL AC to FAST Toolbox"  with Max Server Setting as 1 (Parameter-0x2472 (103)) and AC OPC UA set as 0 & 150

            .. image:: images/sequenceDiagrams/2_1.png

        """
        self.libOpcUaLLM.grp_03_tc_01()

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp3_TC2(self) -> None:
        """
        Verify External Client session connections for different settings for AC OPC UA with mode set as \
        "ALL AC to FAST Toolbox"  with Max Server Setting as 6 (Parameter-0x2472 (103)) and AC OPC UA set as 0 & 150

            .. image:: images/sequenceDiagrams/2_2.png

        """
        self.libOpcUaLLM.grp_03_tc_02()

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp4_TC1(self) -> None:
        """
        Verify sequential login of Client 7 after logout of client 6 with Max Server Setting 6 (Parameter-0x2472 \
        (103)) and AC to OPC UA 150

            .. image:: images/sequenceDiagrams/3_1.png

        """
        self.libOpcUaLLM.grp_04_tc_01()

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp5_TC1(self) -> None:
        """
        Verify Connection of One or More then External Client with mode set as "Static AC Configuration"  with Max \
        Server Setting 6 ( Parameter-0x2472 (103)) and Total AC is  500 , credit assigned to FAST toolbox 500 and \
         credit assigner to OPC UA 150

            .. image:: images/sequenceDiagrams/4_1.png

        """
        self.libOpcUaLLM.grp_05_tc_01()

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp6_TC1(self) -> None:
        """
        Verify updatation of Application credit in Diagnosis License Manager without connection of Third party client \
        with assigned Credit being set as different values (0, 100 & 150)

        """
        self.libOpcUaLLM.grp_06_tc_01()

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp7_TC1(self) -> None:
        """
        TC4.1 Verify connection of Multiple PLC open client to OPC UA server when required Application credit are not
        available on SD card

        """
        self.libOpcUaLLM.grp_07_tc_01()

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp7_TC2(self) -> None:
        """
        TC4.2 Verify connection of Multiple PLC Open client to OPC UA server when required Application credit are
        available on SD card

        """
        self.libOpcUaLLM.grp_07_tc_02()

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp7_TC3(self) -> None:
        """
        TC 4.3 Verify disconnecting one of the six already connected OPC UA server session, with PLC open client and
        connecting a new OPC UA server session

        """
        self.libOpcUaLLM.grp_07_tc_03()

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp8_TC1(self) -> None:
        """
        TC4.4 Verify reading the PLC Designer variable PubSub data using the same c5xx controller as publisher and\
        subscriber fot AC OPC UA = 150 credits

        """
        self.libOpcUaLLM.grp_08_tc_01()

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp8_TC2(self) -> None:
        """
        TC4.5 Verify reading the PLC Designer variable PubSub data using the same c5xx controller as publisher and\
        subscriber for AC OPC UA =0 credits

        """
        self.libOpcUaLLM.grp_08_tc_02()

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp8_TC3(self) -> None:
        """
        TC4.6 Verify reading the PLC Designer variable PubSub data using the same c5xx controller as publisher and\
        subscriber with mode set as "ALL AC to FAST Toolbox" .

        """
        self.libOpcUaLLM.grp_08_tc_03()

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp9_TC1(self) -> None:
        """
        TC4.7 Verify External Client session connections with "Static AC Configuration" mode and AC OPC UA = 100 with\
        Parameter 0x247B PUB Sub --Enabled and PUB Sub configuration not downloaded

        """
        self.libOpcUaLLM.grp_09_tc_01()


#-----------------------------------------------------------------------------------------------------------------------
#    MAIN Program
#-----------------------------------------------------------------------------------------------------------------------
# Note: The following code is executed if you start this file directly!
if __name__ == "__main__":
    logger = clsLogger()
    xlsReaderObj = ConfigExlParser(configFile = constants.CONFIG_FILE_PATH, logger = logger)
    testEnvData = xlsReaderObj.getTestEnvData
    ValidateInterpreter(testEnvData = testEnvData)

    # Checking if test is running in admin mode or not
    if not isEclipseRunningAsAdmin():
        sys.exit()

    # Checking if edge driver is installed in current file path
    if not SeleniumLib.edgeDriverValidation():
        sys.exit()

    TestBench.main(testFileName = __file__)
