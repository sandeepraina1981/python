# -*- coding: utf-8 -*-
#
# © 2007-2008 Lenze Drive Systems GmbH. All rights reserved.
# © 2008-2020 Lenze Automation GmbH. All rights reserved.
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
# Test module docstring (must be first definition in file)
#-----------------------------------------------------------------------------------------------------------------------
"""Test file for Offline User Management
"""
#-----------------------------------------------------------------------------------------------------------------------
# Test module imports (must be defined before code)
#-----------------------------------------------------------------------------------------------------------------------
from pytef.namespace.testcase import (Version, RevisionVersion, FwTestCase, FwTestObject, TestBench, Result)
from tests.cysec.cysec_testsuites.offline_user_management.lib.Lib_UserManagement import Lib_UserManagement

#-----------------------------------------------------------------------------------------------------------------------
# PyTeF file header end
#-----------------------------------------------------------------------------------------------------------------------
class Test_OfflineUserManagement(FwTestCase):
    """
    Class for Offline User Management test
    """
    prefixCls = 'Test_OfflineUserManagement'
    prefixCls = 'Test_OfflineUserManagement'

    #-------------------------------------------------------------------------------------------------------------------
    # SVN keyword section
    #-------------------------------------------------------------------------------------------------------------------
    TEST_URL = "$HeadURL: $"[10:-2]
    TEST_REV = "$Revision: 9134 $"[11:-2]
    TEST_DATE = "$LastChangedDate: 2022-06-01 12:36:27 +0530 (Wed, 01 Jun 2022) $"[18:-2]
    TEST_AUTHOR = "$LastChangedBy: kolten $"[16:-2]
    TEST_VERSION = RevisionVersion(1, 2, 0, TEST_REV)

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
    TEST_KEYS = ["offline.user.management"]

    # : TestReview-Instanz, created by a test manager after a review.
    TESTMGR_REVIEW = None

    #-------------------------------------------------------------------------------------------------------------------
    # Pytef manager section
    #-------------------------------------------------------------------------------------------------------------------
    # : This test class is runnable with this PyTeF version.
    PYTEF_VERSION = Version(2, 0, 0)

    #-------------------------------------------------------------------------------------------------------------------
    def __init__(self, **kwargs) -> None:
        """
        Constructor of a testcase in this class.

        .. warning:: This Constructor is called by the framework while creating the test suite
                     for EVERY singe testcase in this class.
                     It's NOR called once NEITHER directly before every testcase!!!
        """
        super().__init__(**kwargs)

        initArgs = ()
        self.libUserManagement = self.resource.testLib(relModName = r"..\lib\Lib_UserManagement",
                                                       libName = "Lib_UserManagement",
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
        Lib_UserManagement.createTests(cls)

    #-------------------------------------------------------------------------------------------------------------------
    def setUpClass(self) -> Result:
        """
        Setup precondition for all testcases of this class
        """
        self.logger.info(f"[{type(self).prefixCls}] Preparing a single testcase ...")
        self.libUserManagement.setUpClass()

    #-------------------------------------------------------------------------------------------------------------------
    def tearDownClass(self) -> Result:
        """
        tearDownClass for offline user management test runner: calls setUpClass from Lib_UserManagement
        """

        self.logger.info(f"[{type(self).prefixCls}] Preparing a single testcase ...")
        self.libUserManagement.tearDownClass()

    #-------------------------------------------------------------------------------------------------------------------
    def setUp(self) -> Result:
        """
        setUp for offline user management test runner: calls setUpClass from Lib_UserManagement
        """

        self.logger.info(f"[{type(self).prefixCls}] Preparing a single testcase ...")
        self.libUserManagement.setUp()

    #-------------------------------------------------------------------------------------------------------------------
    def tearDown(self) -> None:
        """
        Cleanup the last testcase.
        """
        self.logger.info(f"[{type(self).prefixCls}] Post processing a single testcase ...")

    #-------------------------------------------------------------------------------------------------------------------
    def abortHandler(self) -> None:
        """
        Method abortHandler
        """

        self.logger.info(f"[{type(self).prefixCls}] Executing the abort handler of the class ...")

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Req_01_Grp_01_test_01(self) -> None:
        """
        TC1.0 Create 2 user and 2 groups
        """

        self.libUserManagement.req_01_Grp_01_test_01()

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Req_01_Grp_02_test_01(self) -> None:
        """
        TC1.1 Verify User login / logoff to offline project
        """

        self.libUserManagement.req_01_Grp_02_test_01()

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Req_01_Grp_03_test_01(self) -> None:
        """
        TC11.1 Verify authentical trial settings for user authentication
        """

        self.libUserManagement.req_01_Grp_03_test_01()

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Req_01_Grp_04_test_01(self) -> None:
        """
        TC11.0 Verify authentically logout time settings when inactive for logged in user
        """

        self.libUserManagement.req_01_Grp_04_test_01()

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Req_02_Pre(self) -> None:
        """
        Pre Verifying access to create, add or remove children, modify, remove, view
        """

        self.libUserManagement.req_02_pre()

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Req_02_Test(self) -> None:
        """
        Verifying access to create, add or remove children, modify, remove, view
        """

        self.libUserManagement.req_02_test()

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Req_02_Post(self) -> None:
        """
        Post Verifying access to create, add or remove children, modify, remove, view
        """

        self.libUserManagement.req_02_post()

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Req_03_Pre(self) -> None:
        """
        Pre Verify access rights to execute command type
        """
        self.libUserManagement.req_03_pre()

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Req_03_Test(self) -> None:
        """
        Verify access rights to execute command type
        """
        self.libUserManagement.req_03_test()

    #-------------------------------------------------------------------------------------------------------------------
    def tc_Req_03_Post(self) -> None:
        """
        Post verify access rights to execute command type
        """
        self.libUserManagement.req_03_post()

#-----------------------------------------------------------------------------------------------------------------------
#    MAIN Program
#-----------------------------------------------------------------------------------------------------------------------
# Note: The following code is executed if you start this file directly!


if __name__ == "__main__":
    TestBench.main(testFileName = __file__)

