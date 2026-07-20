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
from tests.testlib.utils.Validation import isEmpty
from tests.testlib.utils.Validation import isValidControllerType
from tests.testlib.utils.Validation import isValidReleaseName
from tests.testlib.utils.TestEnvInfo import TestEnvInfo


#-----------------------------------------------------------------------------------------------------------------------
# SVN keyword section
#-----------------------------------------------------------------------------------------------------------------------
FILE_URL = "$HeadURL: http://repository.lenze.com/ssv/TestRepository/branches/sdc/tests/common/opc_ua/utils/excelReader.py $"[10:-2]  # noqa: E501
FILE_REV = "$Revision: 9362 $"[11:-2]
FILE_DATE = "$LastChangedDate: 2022-12-06 12:29:26 +0530 (Tue, 06 Dec 2022) $"[18:-2]
FILE_AUTHOR = "$LastChangedBy: saklechas $"[16:-2]

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
    COMMON_SETTINGS_START_ROW = 1

    TESTCASE_SELECTION_SHEET = "Test Case Selection"
    TESTCASE_SELECTION_START_ROW = 3
    TESTCASE_SELECTION_GRP_NAME_COL = 0
    TESTCASE_SELECTION_TC_NAME_COLUMN = 1
    TESTCASE_SELECTION_SPIRA_ID_COLUMN = 2
    TESTCASE_SELECTION_EXECUTE_FLAG_COLUMN = 3
    TESTCASE_SELECTION_TC_DESC_COLUMN = 4

    #-------------------------------------------------------------------------------------------------------------------
    def __init__(self, configFile: str, logger) -> None:
        '''
        Constructor for XLSReader
        '''
        # Opening workbook for reading xls file
        fullPath = os.getcwd() + configFile

        self.logger = logger
        self.workbook = open_workbook(fullPath)
        self.controllerType = None
        self.releaseName = None
        self.plcVersion = None
        self.testCaseSelectionDict = {}
        self._loadConfigData()

    #-------------------------------------------------------------------------------------------------------------------
    @property
    def getTestEnvData(self) -> TestEnvInfo:
        """
            This method is used to get the test env info which is further used to decide whether to run the test on
            32bit or 64bit python
        """
        return TestEnvInfo(controllerType = self.controllerType, isPlcdUsed = True)

    def __str__(self) -> str:
        formatConfigData = \
            """
                **********  CONFIG.XLS DATA   **********
                            Controller Type : {}
                               Release Name : {}
                       PLC Designer Version : {}
                      testCaseSelectionDict : {}
            """
        return formatConfigData.format(self.controllerType,
                                       self.releaseName,
                                       self.plcVersion,
                                       self.testCaseSelectionDict)

    #-------------------------------------------------------------------------------------------------------------------
    def _readCommonSettings(self) -> None:
        '''
        This method reads the Common Setting sheet from Device Config and stores values in member Variables
        '''
        worksheet = self.workbook.sheet_by_name(ConfigExlParser.COMMON_SETTINGS_SHEETNAME)

        curRow = ConfigExlParser.COMMON_SETTINGS_START_ROW

        # read controllerType
        self.controllerType = worksheet.cell_value(curRow + 0, ConfigExlParser.COMMON_SETTINGS_COL)

        # read releaseName
        self.releaseName = worksheet.cell_value(curRow + 1, ConfigExlParser.COMMON_SETTINGS_COL)

        # read plcVersion
        self.plcVersion = worksheet.cell_value(curRow + 2, ConfigExlParser.COMMON_SETTINGS_COL)

        # validateXLSData
        self._validateXLSData()

    #-------------------------------------------------------------------------------------------------------------------
    def getSpiraId(self, testCaseName: str) -> None:
        """
        This method is used to get spira id based on the testcase name
        """
        try:
            grpNo = testCaseName.split('_')[-2]
            tcNo = testCaseName.split('_')[-1]
            return self.testCaseSelectionDict.get(grpNo).get(tcNo).get("spira")
        except Exception:  # pylint: disable=broad-exception-caught
            self.logger.exception("[%s] Exception occurred in getSpiraId()", type(self).prefixCls)
            return None

    #-------------------------------------------------------------------------------------------------------------------
    def _validateXLSData(self) -> bool:
        """
            Validate xls data
        """
        self.logger.info("Validating config file input data...")
        if isValidControllerType(
            self.controllerType, logger = self.logger) and isValidReleaseName(
                self.releaseName, logger = self.logger) and self._validateEmptyConfigInputs():
            self.logger.info("Validation for config file is successful")
            return True

        self.logger.info("[%s] Validation for config file failed", type(self).prefixCls)
        return False

    #-------------------------------------------------------------------------------------------------------------------
    def _validateEmptyConfigInputs(self) -> bool:
        """
            Validate config file for empty values
        """
        return bool(isEmpty('PLC version', self.plcVersion, logger = self.logger))

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
                while True:
                    grpCellVal = worksheet.cell_value(rowIndex,
                                                      ConfigExlParser.TESTCASE_SELECTION_GRP_NAME_COL)
                    if grpCellVal.strip():
                        grpName = grpCellVal
                    tcName = worksheet.cell_value(rowIndex,
                                                  ConfigExlParser.TESTCASE_SELECTION_TC_NAME_COLUMN)
                    spira = worksheet.cell_value(rowIndex,
                                                 ConfigExlParser.TESTCASE_SELECTION_SPIRA_ID_COLUMN)
                    spiraId = str(int(spira))
                    executeCellVal = worksheet.cell_value(rowIndex,
                                                          ConfigExlParser.TESTCASE_SELECTION_EXECUTE_FLAG_COLUMN)
                    executeFlag = bool(executeCellVal == 'Execute')
                    testDesc = worksheet.cell_value(rowIndex,
                                                    ConfigExlParser.TESTCASE_SELECTION_TC_DESC_COLUMN)
                    if testCaseSelectionDict.get(grpName, None) is None:
                        testCaseSelectionDict[grpName] = {}

                    testCaseSelectionDict[grpName][tcName] = {"spira" : spiraId,
                                                              "execute" : executeFlag,
                                                              "testDesc" : testDesc}

                    rowIndex += 1
            except IndexError:
                # Last row reached
                pass
            return testCaseSelectionDict
        except Exception:  # pylint: disable=broad-exception-caught
            self.logger.exception("[%s] Exception occurred in _readTestCaseSelection()", type(self).prefixCls)
            return None
