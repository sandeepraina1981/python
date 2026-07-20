# -*- coding: utf-8 -*-
#
# © 2007-2008 Lenze Drive Systems GmbH. All rights reserved.
# © 2008-2021 Lenze Automation GmbH. All rights reserved.
#
#-----------------------------------------------------------------------------------------------------------------------
# PyTeF file header (for PyTeF Internal Code) V1.4-01
#-----------------------------------------------------------------------------------------------------------------------
# Disable linter warnings -> OTHER DISABLES ARE NOT RECOMMENDED, CHANGES ARE AT YOUR OWN RISK!
# pylint: disable=wildcard-import,unused-wildcard-import
#
#-----------------------------------------------------------------------------------------------------------------------
# PyTeF Internal Code docstring (must be first definition in file)
#-----------------------------------------------------------------------------------------------------------------------
"""
    Excel Report updater, which will update report with the test results
"""
#-----------------------------------------------------------------------------------------------------------------------
# PyTeF Internal Code imports (must be defined before code)
#-----------------------------------------------------------------------------------------------------------------------
import os
from typing import Tuple, Union
import openpyxl
from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet
from tests.testlib.interface.patterns.Singleton import Singleton
#-----------------------------------------------------------------------------------------------------------------------
# SVN keyword section
#-----------------------------------------------------------------------------------------------------------------------
FILE_URL = "$HeadURL: http://repository.lenze.com/ssv/TestRepository/branches/sdc/tests/common/opc_ua/utils/excelReportUpdater.py $"[10:-2]  # noqa: E501
FILE_REV = "$Revision: 9245 $"[11:-2]
FILE_DATE = "$LastChangedDate: 2022-08-23 10:19:00 +0530 (Tue, 23 Aug 2022) $"[18:-2]
FILE_AUTHOR = "$LastChangedBy: saklechas $"[16:-2]

#-----------------------------------------------------------------------------------------------------------------------
# PyTeF file header end
#-----------------------------------------------------------------------------------------------------------------------
class ReportExlParser(metaclass=Singleton):
    '''
    Class for reading and updating report data
    '''
    prefixCls = "[ReportExlParser]"
    SPIRA_COL = 1
    TEST_DESCRIPTION_COL = 3
    START_ROW = 2
    RESULT_COL = 4
    REMARK_COL = 5
    REPORT_HEADER_CELL = 'A1'

    PASS_TEXT = "Pass"
    FAIL_TEXT = "Fail"
    NOT_EXECUTED_TEXT = "Not Executed"

    #-------------------------------------------------------------------------------------------------------------------
    def __init__(self, reportFile: str, sheetName: str, logger) -> None:
        '''
        Constructor for XLSX Report Reader
        '''
        # Opening workbook for reading xls file
        fullPath = os.path.join(os.getcwd(), reportFile)
        self.logger = logger
        self.reportFilePath = fullPath
        self.workbook = openpyxl.load_workbook(self.reportFilePath)
        self.sheetName = sheetName

        self.validateReportFile()
        self._reportData = {}
        self._loadReportData()

    #-------------------------------------------------------------------------------------------------------------------
    def loadWorkbook(self) -> Tuple[Workbook, Worksheet]:
        '''
        Load workbook and worksheet and return both
        '''
        workbook = openpyxl.load_workbook(self.reportFilePath)
        worksheet = workbook[self.sheetName]
        return workbook, worksheet

    #-------------------------------------------------------------------------------------------------------------------
    def saveAndCloseWorkbook(self, workbook: Workbook) -> None:
        '''
            Save and close workbook
        '''
        workbook.save(self.reportFilePath)
        workbook.close()

    #-------------------------------------------------------------------------------------------------------------------
    def _loadReportData(self) -> None:
        """
            Load Report Data from Report xlsx file
        """
        try:
            _, worksheet = self.loadWorkbook()
            for row in worksheet.iter_rows(min_row = ReportExlParser.START_ROW + 1,
                                           min_col = ReportExlParser.SPIRA_COL,
                                           max_col = ReportExlParser.SPIRA_COL + 3):
                spiraId = str(row[ReportExlParser.SPIRA_COL].value)
                testDesc = row[ReportExlParser.TEST_DESCRIPTION_COL].value
                resultRow = row[2].row
                remarkRow = row[3].row

                self._reportData[spiraId] = {}
                self._reportData[spiraId]['testDesc'] = testDesc
                self._reportData[spiraId]['resultRow'] = resultRow
                self._reportData[spiraId]['remarkRow'] = remarkRow
        except Exception:  # pylint: disable=broad-exception-caught
            self.logger.exception("[%s] Exception occurred while loading report data..!", type(self).prefixCls)

    #-------------------------------------------------------------------------------------------------------------------
    def getReportData(self) -> dict:
        '''
        Returns report data stored in a dictionary
        '''
        return self._reportData

    #-------------------------------------------------------------------------------------------------------------------
    def updateResult(self, spiraId: Union[int, str], result: bool, remark: str = None) -> bool:
        '''
        Update result in report file for respective spira ids
        '''
        try:
            workbook, worksheet = self.loadWorkbook()
            if isinstance(spiraId, int):
                spiraId = str(spiraId)
            resCol = ReportExlParser.RESULT_COL
            resRow = self._reportData[spiraId]['resultRow']
            if result:
                result = ReportExlParser.PASS_TEXT
            else:
                result = ReportExlParser.FAIL_TEXT
            worksheet[chr(resCol + 65) + str(resRow)] = result

            remCol = ReportExlParser.REMARK_COL
            remRow = self._reportData[spiraId]['remarkRow']
            worksheet[chr(remCol + 65) + str(remRow)] = remark
            self.saveAndCloseWorkbook(workbook = workbook)

        except IndexError:
            self.logger.warning("%s Spira id not found in helper sheet", type(self).prefixCls)
            self.logger.warning("%s Could not update result in report", type(self).prefixCls)

        except Exception:  # pylint: disable=broad-exception-caught
            self.logger.exception("[%s] Exception occurred while updating report excel", type(self).prefixCls)

    #-------------------------------------------------------------------------------------------------------------------
    def validateReportFile(self) -> bool:
        """
        Validate if report is present or not
        """
        try:
            self.logger.info("%s Validating Report File - %s", type(self).prefixCls, self.reportFilePath)
            if os.path.exists(self.reportFilePath) and os.path.isfile(self.reportFilePath):
                self.logger.info("%s Report file exists at location - %s", type(self).prefixCls, self.reportFilePath)
                return True

            self.logger.error("%s Report not found at location : %s", type(self).prefixCls, self.reportFilePath)
            return False
        except Exception:  # pylint: disable=broad-exception-caught
            self.logger.exception("[%s] Exception Occurred while validation of Report", type(self).prefixCls)
            return False

    #-------------------------------------------------------------------------------------------------------------------
    def getTestDescription(self, spira: Union[int, str]) -> str:
        """
        return TC description which was read from report
        """
        if isinstance(spira, int):
            spira = str(spira)
        return self.getReportData().get(spira).get('testDesc')

    #-------------------------------------------------------------------------------------------------------------------
    def updateReportHeader(self, header: str) -> bool:
        """
        This method is used to update the header of the report file
        """
        try:
            workbook, worksheet = self.loadWorkbook()
            worksheet[ReportExlParser.REPORT_HEADER_CELL] = header
            self.saveAndCloseWorkbook(workbook = workbook)
            return True
        except Exception:  # pylint: disable=broad-exception-caught
            self.logger.exception("[%s] Exception occurred in _updateReportHeader()", type(self).prefixCls)
            return False
