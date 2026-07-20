# -*- coding: utf-8 -*-
#
# © 2007-2020 Lenze Drive Systems GmbH, Lenze Automation GmbH. All rights reserved.
# © 2020-     Lenze SE. All rights reserved.
#
#-----------------------------------------------------------------------------------------------------------------------
# PyTeF file header (for Test Script) V2.0-00
#-----------------------------------------------------------------------------------------------------------------------
# Disable linter warnings -> OTHER DISABLES ARE NOT RECOMMENDED, CHANGES ARE AT YOUR OWN RISK!
# pylint: disable=wildcard-import,unused-wildcard-import
#
#-----------------------------------------------------------------------------------------------------------------------
# Test Script docstring (must be first definition in file)
#-----------------------------------------------------------------------------------------------------------------------
"""This is Test Script Runner for Audit log TLS and IEC
"""
#-----------------------------------------------------------------------------------------------------------------------
# Test Script imports (must be defined before code)
#-----------------------------------------------------------------------------------------------------------------------

from pytef.namespace.testcase import FwTestCase, RevisionVersion, FwTestObject, Version, TestBench

from pytef.namespace.testlib import Result

from tests.cysec.auditlog_testsuites.audit_log_test.lib.Lib_TLS import Lib_TLS

from tests.testlib.utils.CommonLib import clsLogger

from tests.cysec.auditlog_testsuites.audit_log_test.utils.constants_audit_log import Constants_Base as constants
from tests.cysec.auditlog_testsuites.audit_log_test.utils.excelReader import ConfigExlParser

#-----------------------------------------------------------------------------------------------------------------------
# PyTeF file header end
#-----------------------------------------------------------------------------------------------------------------------
class Test_Audit_Log_TLS_IEC(FwTestCase):
    """
    Class for Error Handling
    """
    prefixCls = 'Test_Audit_Log_Sys_Log'

    #-------------------------------------------------------------------------------------------------------------------
    # SVN keyword section
    #-------------------------------------------------------------------------------------------------------------------
    TEST_URL     = "$HeadURL: http://repository.lenze.com/ssv/TestRepository/branches/sdc//tests/common/target_device_manager_test/Test_Error_Handling.py $"[10:-2]  # noqa:E501
    TEST_REV     = "$Revision: 8821 $"[11:-2]
    TEST_DATE    = "$LastChangedDate: 2022-02-09 17:40:58 +0530 (Wed, 09 Feb 2022) $"[18:-2]
    TEST_AUTHOR  = "$LastChangedBy: patole@lenze.com $"[16:-2]
    TEST_VERSION = RevisionVersion(1, 0, 0, TEST_REV)

    #-------------------------------------------------------------------------------------------------------------------
    # Test manager section
    #-------------------------------------------------------------------------------------------------------------------
    #: Define the test object(s) of the testcases here.
    TEST_OBJS = [FwTestObject.NOT_DEFINED]

    #: While developing / debugging a test, you can set the va lid (more detailed) test object here.
    #  It's only used, if this test script is directly started and is not part of a test suite.
    #  This object (if defined) is added as first element in TEST_OBJS.
    #  That way is easier as creating a test run configuration or to modify the TEST_OBJS.
    TEST_OBJ_DEVEL = FwTestObject.NOT_DEFINED

    #: Specify the test keys for the testcases in the class here.
    TEST_KEYS = ["auditLog.TLS"]

    #: TestReview-Instanz, created by a test manager after a review.
    TESTMGR_REVIEW = None

    #-------------------------------------------------------------------------------------------------------------------
    # Pytef manager section
    #-------------------------------------------------------------------------------------------------------------------
    #: This test class is runnable with this PyTeF version.
    PYTEF_VERSION = Version(2, 0, 0)

    #: TestReview-Instanz, created by a PyTeF developer after a review.
    PYTEF_REVIEW = None

    #-------------------------------------------------------------------------------------------------------------------
    def __init__(self, **kwargs) -> None:
        """
        Constructor of a testcase in this class.
        """
        super().__init__(**kwargs)

        initArgs = ()

        xlReaderObj = ConfigExlParser(configFile = constants.CONGIF_FILE_PATH_TLS,
                                      logger = self.logger)

        if xlReaderObj.controllerType == "i950 (BS-STO)":
            self.libTLS = self.resource.testLib(relModName = r"lib\Lib_TLS_i950",
                                                libName = "Lib_TLS_i950",
                                                relToFile = __file__,
                                                initArgs = initArgs)
        else:
            self.libTLS = self.resource.testLib(relModName = r"lib\Lib_TLS",
                                                libName = "Lib_TLS",
                                                relToFile = __file__,
                                                initArgs = initArgs)

    #-------------------------------------------------------------------------------------------------------------------
    def autoTestFunc(self) -> None:
        """
        Auto Test Function
        """
        funcName = self.testParamDict.get('funcName')

        self.logger.info(f"[{type(self).prefixCls}] funcName = {funcName}")

        func = getattr(self, funcName)
        func()

    #-------------------------------------------------------------------------------------------------------------------
    def setUpClass(self) -> None:
        """
        SetUp class for Auditlog TLS Test test
        """
        self.logger.info(f"[{type(self).prefixCls}] Preparing things for all testcases in this class ...")
        self.libTLS.setUpClass()

    #-------------------------------------------------------------------------------------------------------------------
    def setUp(self) -> None:
        """
        SetUp class for Auditlog TLS Test test
        """
        return Result(errorCode = Result.NO_ERROR, errorMessage = "Success")

    #-------------------------------------------------------------------------------------------------------------------
    def tearDown(self) -> None:
        """
        SetUp class for Auditlog TLS Test test
        """
        return Result(errorCode = Result.NO_ERROR, errorMessage = "Success")

    #-------------------------------------------------------------------------------------------------------------------
    def tearDownClass(self) -> None:
        """
        Teardown class for Auditlog TLS Test test to generate report after test execution
        """
        self.logger.info(f"[{type(self).prefixCls}] Post processing the test class ...")
        self.libTLS.tearDownClass()

    #-------------------------------------------------------------------------------------------------------------------
    def abortHandler(self) -> None:
        """
        Auditlog TLS Test test abortHandler()
        """
        self.logger.info(f"[{type(self).prefixCls}] Executing the abort handler of the class ...")

    #-------------------------------------------------------------------------------------------------------------------
    @classmethod
    def autoCreateTestCases(cls) -> None:
        """Example to create test cases by parameters - here 900 test cases!!

        An implementation by typing all tc_* methods in this class in not needed any more.
        The test case specific parameters you get in the test code by self.testself.resultDict.get(myAttr)

        Actual it's not possible to hand
        """
        Lib_TLS.createTests(cls)

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp_01_test_00_pre(self) -> None:
        """
        Pre-Requisite for Test Group 1
        """
        self.libTLS.grp_01_00_pre()

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp_01_test_01(self):
        """
        TC2.0: Verify activation of SyslogClient with UDP connection to communicate with Syslog server.
        """
        if not self.libTLS.common_testCase_01(protocol = constants.PROTOCOL_TYPES[0],
                                              encryption = constants.SERVER_ENCRYPTION["NOT_ENCRYPTED"],
                                              port = constants.PORT["UDP"]):
            self.fail(f"{self.testCaseName} Failed")

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp_01_test_02(self):
        """
        TC3.0: Verify that the timestamp of log messages received by the external server matches those sent by
        SyslogClient with UDP connection.
        """
        if not self.libTLS.common_testCase_02():
            self.fail(f"{self.testCaseName} Failed")

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp_01_test_03(self):
        """
        TC4.0: Verify that the number of logs received by the external server matches the number sent by
        SyslogClient within a specific time period using UDP connection.
        """
        if not self.libTLS.common_testCase_03():
            self.fail(f"{self.testCaseName} Failed")

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp_01_test_04(self):
        """
        TC5.0: Verify that Codesys Audit logs received by the external server match those sent by
        SyslogClient with UDP connection.
        """
        if not self.libTLS.common_testCase_04():
            self.fail(f"{self.testCaseName} Failed")

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp_01_test_05(self):
        """
        TC6.0: Verify that IEC addsys logs received by the external server match those sent by
        SyslogClient with UDP connection.
        """
        if not self.libTLS.common_testCase_05():
            self.fail(f"{self.testCaseName} Failed")

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp_01_test_06(self):
        """
        TC7.0: Verify that Syslog firmservices logs received by the external server match those sent by
        SyslogClient with UDP connection.
        """
        if not self.libTLS.common_testCase_06():
            self.fail(f"{self.testCaseName} Failed")

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp_01_test_07(self):
        """
        TC8.0: Verify that OPCUA logs received by the external server match those sent by
        SyslogClient with UDP connection.
        """
        if not self.libTLS.common_testCase_07():
            self.fail(f"{self.testCaseName} Failed")

    # #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp_01_test_08(self):
        """
        TC9.0: Verify that logs are updated at the external server from
        SyslogClient after disconnection using UDP connection.
        """
        if not self.libTLS.common_testCase_08():
            self.fail(f"{self.testCaseName} Failed")

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp_01_test_09(self):
        """
        TC10.0: Verify that logs are updated at the external server from
        SyslogClient after reconnection using UDP connection.
        """
        if not self.libTLS.common_testCase_09():
            self.fail(f"{self.testCaseName} Failed")

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp_01_test_99_post(self) -> None:
        """
        Post Actions for Test Group 1
        """
        self.libTLS.grp_01_99_post()

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp_02_test_00_pre(self) -> None:
        """
        Pre-Requisite for Test Group 2
        """
        self.libTLS.grp_02_00_pre()

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp_02_test_01(self):
        """
        TC11.0: Verify activation of SyslogClient with TCP connection and without encryption.
        """
        if not self.libTLS.common_testCase_01(protocol = constants.PROTOCOL_TYPES[1],
                                              encryption = constants.SERVER_ENCRYPTION["NOT_ENCRYPTED"],
                                              port = constants.PORT["TCP"]):
            self.fail(f"{self.testCaseName} Failed")

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp_02_test_02(self):
        """
        TC12.0: Verify that the timestamp of log messages received by the external server matches those sent by
        SyslogClient with TCP connection and without encryption.
        """
        if not self.libTLS.common_testCase_02():
            self.fail(f"{self.testCaseName} Failed")

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp_02_test_03(self):
        """
        TC13.0: Verify that the number of logs received by the external server matches the number sent by
        SyslogClient within a specific time period using TCP connection and without encryption.
        """
        if not self.libTLS.common_testCase_03():
            self.fail(f"{self.testCaseName} Failed")

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp_02_test_04(self):
        """
        TC14.0: Verify that Codesys Audit logs received by the external server match those sent by
        SyslogClient with TCP connection and without encryption.
        """
        if not self.libTLS.common_testCase_04():
            self.fail(f"{self.testCaseName} Failed")

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp_02_test_05(self):
        """
        TC15.0: Verify that IEC addsys logs received by the external server match those sent by
        SyslogClient with TCP connection and without encryption.
        """
        if not self.libTLS.common_testCase_05():
            self.fail(f"{self.testCaseName} Failed")

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp_02_test_06(self):
        """
        TC16.0: Verify that Syslog firmservices logs received by the external server match those sent by
        SyslogClient with TCP connection and without encryption.
        """
        if not self.libTLS.common_testCase_06():
            self.fail(f"{self.testCaseName} Failed")

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp_02_test_07(self):
        """
        TC17.0: Verify that OPCUA logs received by the external server match those sent by
        SyslogClient with TCP connection and without encryption.
        """
        if not self.libTLS.common_testCase_07():
            self.fail(f"{self.testCaseName} Failed")

    # #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp_02_test_08(self):
        """
        TC18.0: Verify that logs are updated at the external server from
        SyslogClient after disconnection using TCP connection and without encryption.
        """
        if not self.libTLS.common_testCase_08():
            self.fail(f"{self.testCaseName} Failed")

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp_02_test_09(self):
        """
        TC19.0: Verify that logs are updated at the external server from
        SyslogClient after reconnection using TCP connection and without encryption.
        """
        if not self.libTLS.common_testCase_09():
            self.fail(f"{self.testCaseName} Failed")

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp_02_test_99_post(self) -> None:
        """
        Post Actions for Test Group 2
        """
        self.libTLS.grp_02_99_post()

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp_03_test_00_pre(self) -> None:
        """
        Pre-Requisite for Test Group 3
        """
        self.libTLS.grp_03_00_pre()

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp_03_test_01(self):
        """
        TC20.0: Verify activation of SyslogClient with TCP connection and encryption.
        """
        if not self.libTLS.common_testCase_01(protocol = constants.PROTOCOL_TYPES[1],
                                              encryption = constants.SERVER_ENCRYPTION["ENCRYPTED"],
                                              port = constants.PORT["TCP_TLS"]):
            self.fail(f"{self.testCaseName} Failed")

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp_03_test_02(self):
        """
        TC21.0: Verify that the timestamp of log messages received by the external server matches those sent by
        SyslogClient with TCP connection and encryption.
        """
        if not self.libTLS.common_testCase_02():
            self.fail(f"{self.testCaseName} Failed")

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp_03_test_03(self):
        """
        TC22.0: Verify that the number of logs received by the external server matches the number sent by
        SyslogClient within a specific time period using TCP connection and encryption.
        """
        if not self.libTLS.common_testCase_03():
            self.fail(f"{self.testCaseName} Failed")

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp_03_test_04(self):
        """
        TC23.0: Verify that Codesys Audit logs received by the external server match those sent by
        SyslogClient with TCP connection and encryption.
        """
        if not self.libTLS.common_testCase_04():
            self.fail(f"{self.testCaseName} Failed")

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp_03_test_05(self):
        """
        TC24.0: Verify that IEC addsys logs received by the external server match those sent by
        SyslogClient with TCP connection and encryption.
        """
        if not self.libTLS.common_testCase_05():
            self.fail(f"{self.testCaseName} Failed")

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp_03_test_06(self):
        """
        TC25.0: Verify that Syslog firmservices logs received by the external server match those sent by
        SyslogClient with TCP connection and encryption.
        """
        if not self.libTLS.common_testCase_06():
            self.fail(f"{self.testCaseName} Failed")

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp_03_test_07(self):
        """
        TC26.0: Verify that OPCUA logs received by the external server match those sent by
        SyslogClient with TCP connection and encryption.
        """
        if not self.libTLS.common_testCase_07():
            self.fail(f"{self.testCaseName} Failed")

    # #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp_03_test_08(self):
        """
        TC27.0: Verify that logs are updated at the external server from SyslogClient after
        disconnection using TCP connection and encryption.
        """
        if not self.libTLS.common_testCase_08():
            self.fail(f"{self.testCaseName} Failed")

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp_03_test_09(self):
        """
        TC28.0: Verify that logs are updated at the external server from SyslogClient after
        reconnection using TCP connection and encryption.
        """
        if not self.libTLS.common_testCase_09():
            self.fail(f"{self.testCaseName} Failed")

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp_03_test_99_post(self) -> None:
        """
        Post Actions for Test Group 3
        """
        self.libTLS.grp_03_99_post()

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp_04_test_00_pre(self) -> None:
        """
        Pre-Requisite for Test Group 4
        """
        self.libTLS.grp_04_00_pre()

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp_04_test_01(self):
        """
        TC1.0: Verify activation of SyslogClient with UDP and TLS encryption to communicate with Syslog server.
        """
        if not self.libTLS.grp_04_test_01():
            self.fail(f"{self.testCaseName} Failed")

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp_04_test_02(self):
        """
        TC34.0: Verify the functioning of the Message Severity Filter for TCP connection with encryption.
        """
        if not self.libTLS.grp_04_test_02():
            self.fail(f"{self.testCaseName} Failed")

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp_04_test_03(self):
        """
        TC35.0: Verify the functioning of the Message Severity Filter for TCP connection without encryption.
        """
        if not self.libTLS.grp_04_test_03():
            self.fail(f"{self.testCaseName} Failed")

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp_04_test_04(self):
        """
        TC36.0: Verify the functioning of the Message Severity Filter for UDP connection.
        """
        if not self.libTLS.grp_04_test_04():
            self.fail(f"{self.testCaseName} Failed")

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp_04_test_99_post(self) -> None:
        """
        Post Actions for Test Group 4
        """
        self.libTLS.grp_04_99_post()

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp_05_test_00_pre(self) -> None:
        """
        TC Group for IEC Function Block Testing

        Executing Pre-requisite for Test Group 5
        """
        self.libTLS.grp_05_00_pre()

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp_05_test_01(self):
        """
        TC1.1 Verify whether the logs for the user are being generated in the User (user.log) file with setting
        "L_IS1P_eFacility":=user(1) by using "Audit log IEC FB "
        """
        if not self.libTLS.grp_05_test_01():
            self.fail(f"{self.testCaseName} Failed")

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp_05_test_02(self):
        """
        TC1.2 Verify whether the logs for Authentication are getting generated in Authentication(auth.log) file
        with setting "L_IS1P_eFacility":=Auth(4) by using "Audit log IEC FB "
        """
        if not self.libTLS.grp_05_test_02():
            self.fail(f"{self.testCaseName} Failed")

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp_05_test_03(self):
        """
        TC1.3 Verify whether the logs for user are getting generated in User(auth.log) file with Successful
        authentication of user with Setting "L_IS1P_eAuthentication" :=successful(1) by using "Audit log IEC FB"
        """
        if not self.libTLS.grp_05_test_03():
            self.fail(f"{self.testCaseName} Failed")

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp_05_test_04(self):
        """
        TC1.4 Verify whether the logs for user are getting generated in User(auth.log) file with Failed
        authentication of user with Setting "L_IS1P_eAuthentication" :=failed(2) by using "Audit log IEC FB"
        """
        if not self.libTLS.grp_05_test_04():
            self.fail(f"{self.testCaseName} Failed")

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp_05_test_05(self):
        """
        TC1.5 Verify whether the logs for user are getting generated in User(auth.log) file with
        None authentication of user with Setting "L_IS1P_eAuthentication" :=none(0) by using "Audit log IEC FB"
        """
        if not self.libTLS.grp_05_test_05():
            self.fail(f"{self.testCaseName} Failed")

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp_05_test_06(self):
        """
        TC1.6 Verify whether Name of the user is 64 characters in User(user.log) file with
        Setting "sUser" by using "Audit log IEC FB"
        """
        if not self.libTLS.grp_05_test_06():
            self.fail(f"{self.testCaseName} Failed")

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp_05_test_07(self):
        """
        TC1.7 Verify whether Name of the user is not exceed 64 characters in User(user.log) file with
        Setting "sUser" by using "Audit log IEC FB "
        """
        if not self.libTLS.grp_05_test_07():
            self.fail(f"{self.testCaseName} Failed")

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp_05_test_08(self):
        """
        TC1.8 Verify log message is 255 characters in User(user.log) file with setting "sMessage"
        by using "Audit log IEC FB "
        """
        if not self.libTLS.grp_05_test_08():
            self.fail(f"{self.testCaseName} Failed")

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp_05_test_09(self):
        """
        TC1.9 Verify log message is not exceed 255 characters in User(user.log) file with setting
        "sMessage" by using "Audit log IEC FB "
        """
        if not self.libTLS.grp_05_test_09():
            self.fail(f"{self.testCaseName} Failed")

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp_05_test_10(self):
        """
        TC2.0 Verify the "Auditlog IEC FB" generates correct number of logs with same messages
        as defined by user
        """
        if not self.libTLS.grp_05_test_10():
            self.fail(f"{self.testCaseName} Failed")

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp_05_test_11(self):
        """
        TC2.1 Verify the "Auditlog IEC FB" generates correct number logs with different messages
        as defined by user
        """
        if not self.libTLS.grp_05_test_11():
            self.fail(f"{self.testCaseName} Failed")

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp_05_test_12(self):
        """
        TC2.2 Verify the "Auditlog IEC FB" generate logs after calling IEC FB multiple times within a
        task and also from any task within the application.
        """
        if not self.libTLS.grp_05_test_12():
            self.fail(f"{self.testCaseName} Failed")

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp_05_test_13(self):
        """
        TC2.3 Verify the "Auditlog IEC FB" transmission of messages within the buffer size limit.
        """
        if not self.libTLS.grp_05_test_13():
            self.fail(f"{self.testCaseName} Failed")

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp_05_test_14(self):
        """
        TC2.4 Verify that after an event of a network failure, the messages that have not yet been
        transferred from the buffer are lost by using "Auditlog IEC FB"
        """
        if not self.libTLS.grp_05_test_14():
            self.fail(f"{self.testCaseName} Failed")

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp_05_test_99_post(self) -> None:
        """
        Post Actions for Test Group 5
        """
        self.libTLS.grp_05_99_post()

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp_06_test_00_pre(self) -> None:
        """
        Pre-Requisite for Test Group 6
        """
        self.libTLS.grp_06_00_pre()

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp_06_test_01(self):
        """
        TC29.0: Verify that if the logs are updated at external server from syslog client after
        Deleted certificate them With TCP Connection and with Encryption.
        """
        if not self.libTLS.grp_06_test_01():
            self.fail(f"{self.testCaseName} Failed")

#-------------------------------------------------------------------------------------------------------------------
    def tc_Grp_06_test_02(self):
        """
        TC32.0: Verify Creation of New Lenze Syslog proxy certificate with Controller
        Start, Stop, Reset Cold, Reset Warm, Reset Origin.
        """
        if not self.libTLS.grp_06_test_02():
            self.fail(f"{self.testCaseName} Failed")

#-------------------------------------------------------------------------------------------------------------------
    def tc_Grp_06_test_03(self):
        """
        TC30.0: Verify that if the logs are updated at external server from syslog client after creation of
        New certificate With TCP Connection and with Encryption.
        """
        if not self.libTLS.grp_06_test_03():
            self.fail(f"{self.testCaseName} Failed")

#-------------------------------------------------------------------------------------------------------------------
    def tc_Grp_06_test_04(self):
        """
        TC35.0: Verify the functioning of the Message Severity Filter for TCP connection without encryption.
        """
        if not self.libTLS.grp_06_test_04():
            self.fail(f"{self.testCaseName} Failed")

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Grp_06_test_99_post(self) -> None:
        """
        Post Actions for Test Group 6
        """
        self.libTLS.grp_06_99_post()

#-----------------------------------------------------------------------------------------------------------------------
#    MAIN Program
#-----------------------------------------------------------------------------------------------------------------------
# Note: The following code is executed if you start this file directly!
#


if __name__ == "__main__":

    # Validating Python interpreter
    logger = clsLogger()

    # Checking if test is running in admin mode or not
    # if not isEclipseRunningAsAdmin():
    #     sys.exit()

    TestBench.main(testFileName = __file__)
