# -*- coding: utf-8 -*-
#
# © 2007-2008 Lenze Drive Systems GmbH. All rights reserved.
# © 2008-2021 Lenze Automation GmbH. All rights reserved.
#
#-----------------------------------------------------------------------------------------------------------------------
# PyTeF file header (for PyTeF Internal Code) V1.4-01
#-----------------------------------------------------------------------------------------------------------------------
# Disable linter warnings -> ONLY for PyTeF internal code!
#-----------------------------------------------------------------------------------------------------------------------
# PyTeF Internal Code docstring (must be first definition in file)
#-----------------------------------------------------------------------------------------------------------------------
"""
    Device Config XLSX reader which will read the test setting and save for later use in test. This is a singleton class
"""
#-----------------------------------------------------------------------------------------------------------------------
# PyTeF Internal Code imports (must be defined before code)
#-----------------------------------------------------------------------------------------------------------------------
import os
from xlrd import open_workbook
from tests.testlib.interface.patterns.Singleton import Singleton
from tests.testlib.utils.TestEnvInfo import TestEnvInfo
from tests.testlib.utils.CommonLib import clsLogger


#-----------------------------------------------------------------------------------------------------------------------
# SVN keyword section
#-----------------------------------------------------------------------------------------------------------------------
FILE_URL = "$HeadURL: $"[10:-2]  # noqa: E501
FILE_REV = "$Revision: $"[11:-2]
FILE_DATE = "$LastChangedDate: $"[18:-2]
FILE_AUTHOR = "$LastChangedBy: raina $"[16:-2]

#-----------------------------------------------------------------------------------------------------------------------
# PyTeF file header end
#-----------------------------------------------------------------------------------------------------------------------
class ConfigExlParser(metaclass = Singleton):
    '''
    Class for reading and parsing config data from config file
    '''
    prefixCls = 'ConfigExlParser'

    COMMON_SETTINGS_SHEETNAME = "Common Settings"
    COMMON_SETTINGS_COL = 1
    COMMON_SETTINGS_RELEASE_NAME_ROW = 1
    COMMON_SETTINGS_SESSION_ROW = 2
    COMMON_SETTINGS_SESSION_INDEX = 1

    TESTCASE_SELECTION_SHEET = "Test Case Selection"
    TESTCASE_SELECTION_START_ROW = 3
    TESTCASE_SELECTION_GRP_NAME_COL = 0
    TESTCASE_SELECTION_TC_NAME_COLUMN = 1
    TESTCASE_SELECTION_JIRA_ID_COLUMN = 2
    TESTCASE_SELECTION_EXECUTE_FLAG_COLUMN = 3
    TESTCASE_SELECTION_TC_DESC_COLUMN = 4

    #-------------------------------------------------------------------------------------------------------------------
    def __init__(self, configFile: str, logger: clsLogger) -> None:
        '''
        Constructor for XLSReader
        '''
        # Opening workbook for reading xls file
        fullPath = os.getcwd() + configFile

        self.logger = logger
        self.workbook = open_workbook(fullPath)
        self.releaseName = None
        self.sessionConnectFlags = {}
        self.testCaseSelectionDict = {}
        self._loadConfigData()

    #-------------------------------------------------------------------------------------------------------------------
    @property
    def getTestEnvData(self) -> TestEnvInfo:
        """
            This method is used to get the test env and test cases info
        """
        return TestEnvInfo(controllerType = "", isPlcdUsed = False)

    def __str__(self) -> str:
        formatConfigData = \
            """
                **********  CONFIG.XLS DATA   **********
                            Release Name : {}
                            Connect External Session : {}
                            testCaseSelectionDict : {}
            """
        return formatConfigData.format(self.releaseName,
                                       self.sessionConnectFlags,
                                       self.testCaseSelectionDict)

    #-------------------------------------------------------------------------------------------------------------------
    def str_to_bool(self, convertValue: str) -> bool:
        """
        Convert a string to a boolean value.
        Accepts: 'true', 'false', 'yes', 'no', '1', '0', 'y', 'n' (case-insensitive).
        Raises ValueError for invalid input.
        """
        if not isinstance(convertValue, str):
            raise TypeError("Input must be a string")

        value = str(convertValue).strip().lower()

        if value in ("true", "1", "yes", "y"):
            return True

        if value in ("false", "0", "no", "n"):
            return False

        raise ValueError(f"Invalid boolean string: {value}")

    #-------------------------------------------------------------------------------------------------------------------
    def _readCommonSettings(self) -> None:
        '''
        This method reads the Common Setting sheet from Device Config and stores values in member Variables
        '''
        worksheet = self.workbook.sheet_by_name(ConfigExlParser.COMMON_SETTINGS_SHEETNAME)

        # read ReleaseName
        self.releaseName = worksheet.cell_value(
            ConfigExlParser.COMMON_SETTINGS_RELEASE_NAME_ROW, ConfigExlParser.COMMON_SETTINGS_COL)

        # read Connect External Session 1
        self.sessionConnectFlags[ConfigExlParser.COMMON_SETTINGS_SESSION_INDEX] = self.str_to_bool(
            worksheet.cell_value(ConfigExlParser.COMMON_SETTINGS_SESSION_ROW,
                                 ConfigExlParser.COMMON_SETTINGS_COL))

        # read Connect External Session 2
        self.sessionConnectFlags[ConfigExlParser.COMMON_SETTINGS_SESSION_INDEX + 1] = self.str_to_bool(
            worksheet.cell_value(ConfigExlParser.COMMON_SETTINGS_SESSION_ROW + 1,
                                 ConfigExlParser.COMMON_SETTINGS_COL))

        # read Connect External Session 3
        self.sessionConnectFlags[ConfigExlParser.COMMON_SETTINGS_SESSION_INDEX + 2] = self.str_to_bool(
            worksheet.cell_value(ConfigExlParser.COMMON_SETTINGS_SESSION_ROW + 2,
                                 ConfigExlParser.COMMON_SETTINGS_COL))

        # read Connect External Session 4
        self.sessionConnectFlags[ConfigExlParser.COMMON_SETTINGS_SESSION_INDEX + 3] =  self.str_to_bool(
            worksheet.cell_value(ConfigExlParser.COMMON_SETTINGS_SESSION_ROW + 3,
                                 ConfigExlParser.COMMON_SETTINGS_COL))

        # read Connect External Session 5
        self.sessionConnectFlags[ConfigExlParser.COMMON_SETTINGS_SESSION_INDEX + 4] = self.str_to_bool(
            worksheet.cell_value(ConfigExlParser.COMMON_SETTINGS_SESSION_ROW + 4,
                                 ConfigExlParser.COMMON_SETTINGS_COL))

        # read Connect External Session 6
        self.sessionConnectFlags[ConfigExlParser.COMMON_SETTINGS_SESSION_INDEX + 5] = self.str_to_bool(
            worksheet.cell_value(ConfigExlParser.COMMON_SETTINGS_SESSION_ROW + 5,
                                 ConfigExlParser.COMMON_SETTINGS_COL))

    #-------------------------------------------------------------------------------------------------------------------
    def getGroupName(self, testCaseName: str) -> str:
        """
        This method is used to get group number
        """

        grpNo = testCaseName.split('_')[-1]
        return grpNo

    #-------------------------------------------------------------------------------------------------------------------
    def getJiraIdListByGroup(self, testGroupName: str) -> []:
        """
        This method is used to get jira id based on the testcase name
        """
        try:
            jiraIdList = []
            tcList = self.testCaseSelectionDict.get(testGroupName)

            for tcItem in tcList.items():
                jiraIdList.append(int(str(tcItem[1]["jira"])))

            return jiraIdList
        except Exception:  # pylint: disable=broad-exception-caught
            self.logger.exception(f"[{type(self).prefixCls}] Exception occurred in getJiraIdListByGroup()")
            return []

    #-------------------------------------------------------------------------------------------------------------------
    def _loadConfigData(self) -> None:
        """
            Validate config file for empty values
        """
        self._readCommonSettings()
        self.testCaseSelectionDict = self._readTestCaseSelection()

    #-------------------------------------------------------------------------------------------------------------------
    def _readTestCaseSelection(self) -> None:
        '''
        This method reads the testcase selection data
        '''
        try:
            worksheet = self.workbook.sheet_by_name(ConfigExlParser.TESTCASE_SELECTION_SHEET)
            rowIndex = ConfigExlParser.TESTCASE_SELECTION_START_ROW
            testCaseSelectionDict = {}

            try:
                grpName = ''
                executeFlag = True

                while True:
                    grpCellVal = worksheet.cell_value(rowIndex, ConfigExlParser.TESTCASE_SELECTION_GRP_NAME_COL)

                    if grpCellVal.strip():
                        grpName = grpCellVal

                    tcName = worksheet.cell_value(rowIndex, ConfigExlParser.TESTCASE_SELECTION_TC_NAME_COLUMN)
                    jiraCellVal = worksheet.cell_value(rowIndex, ConfigExlParser.TESTCASE_SELECTION_JIRA_ID_COLUMN)
                    jiraId = str(int(jiraCellVal))

                    executeCellVal = worksheet.cell_value(rowIndex,
                                                          ConfigExlParser.TESTCASE_SELECTION_EXECUTE_FLAG_COLUMN)
                    if executeCellVal.strip():
                        executeFlag = bool(executeCellVal == 'Execute')

                    testDesc = worksheet.cell_value(rowIndex,
                                                    ConfigExlParser.TESTCASE_SELECTION_TC_DESC_COLUMN)
                    if testCaseSelectionDict.get(grpName, None) is None:
                        testCaseSelectionDict[grpName] = {}

                    testCaseSelectionDict[grpName][tcName] = {"jira" : jiraId,
                                                              "execute" : executeFlag,
                                                              "testDesc" : testDesc}

                    rowIndex += 1
            except IndexError:
                # Last row reached
                pass
            return testCaseSelectionDict
        except Exception:  # pylint: disable=broad-exception-caught
            self.logger.exception(f"[{type(self).prefixCls}] Exception occurred in _readTestCaseSelection()")
            return None

class ConfigExlParserOpenClientAuthToken(ConfigExlParser):
    COMMON_SETTINGS_PLCVER_ROW = 8

    def __init__(self, configFile, logger):
        super().__init__(configFile = configFile, logger = logger)
        self._readAuthTokenCommonSettings()

    #-------------------------------------------------------------------------------------------------------------------
    def _readAuthTokenCommonSettings(self) -> None:
        '''
        This method reads the Common Setting sheet from Device Config and stores values in member Variables
        '''
        worksheet = self.workbook.sheet_by_name(ConfigExlParser.COMMON_SETTINGS_SHEETNAME)

        # read PLC Designer Version
        self.plcVersion = worksheet.cell_value(
            ConfigExlParserOpenClientAuthToken.COMMON_SETTINGS_PLCVER_ROW,
            ConfigExlParser.COMMON_SETTINGS_COL)
