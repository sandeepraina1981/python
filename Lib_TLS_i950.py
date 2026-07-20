# -*- coding: utf-8 -*-
#
# © 2007-2020 Lenze Drive Systems GmbH, Lenze Automation GmbH. All rights reserved.
# © 2020-     Lenze SE. All rights reserved.
#
#-----------------------------------------------------------------------------------------------------------------------
# PyTeF file header (for Test Library) V2.0-00
#-----------------------------------------------------------------------------------------------------------------------
# Disable linter warnings -> OTHER DISABLES ARE NOT RECOMMENDED, CHANGES ARE AT YOUR OWN RISK!
# pylint: disable=wildcard-import,unused-wildcard-import
#
#-----------------------------------------------------------------------------------------------------------------------
# Module docstring (must be first definition in file)
#-----------------------------------------------------------------------------------------------------------------------
"""Audit Log Test Library for holdig all the common featues of Audit Log Tests
"""
#-----------------------------------------------------------------------------------------------------------------------
# Module imports (must be defined before code)
#-----------------------------------------------------------------------------------------------------------------------

#pytef utilities
from pytef.namespace.testlib import (Version)

from tests.cysec.auditlog_testsuites.audit_log_test.lib.Lib_i950 import Lib_i950
from tests.cysec.auditlog_testsuites.audit_log_test.lib.Lib_TLS import Lib_TLS

#-----------------------------------------------------------------------------------------------------------------------
# SVN keyword section
#-----------------------------------------------------------------------------------------------------------------------
FILE_URL     = "$HeadURL: http://repository.lenze.com/test/pytef/Source/branches/V02.00/src/templates/Lib_Template.py $"[10:-2]  # noqa: E501
FILE_REV     = "$Revision: 9489 $"[11:-2]
FILE_DATE    = "$LastChangedDate: 2024-09-19 08:37:00 +0200 (Thu, 19 Sep 2024) $"[18:-2]
FILE_AUTHOR  = "$LastChangedBy: Langenberg $"[16:-2]

#-----------------------------------------------------------------------------------------------------------------------
# PyTeF file header end
#-----------------------------------------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------------------------------------
class Lib_TLS_i950(Lib_i950, Lib_TLS):

    __LIB_DICT = {}

    LIB_NAME    = "Lib_TLS_i950"
    LIB_VERSION = Version(1, 0, 0)

    #-------------------------------------------------------------------------------------------------------------------
    def __init__(self) -> None:
        """
            Initializes the test case with necessary parameters and resources.

            This method performs the following steps:
            1. Calls the superclass initializer with specific constants.
            2. Filters IPC objects based on specified classes and retrieves one IPC object.
            3. Appends the IP address and controller type of the IPC object to respective lists.
            4. Logs the controller details including IP address and type.
            5. Initializes an SSH client for the IPC object.
            6. Sets the relative path for the PLC project based on the controller type.
            7. Initializes the PLC project with the specified relative path.

            Args:
                self: Instance of the class containing this method.

            Returns:
                None

            Example:
                >>> test_instance = YourTestClass()
                >>> test_instance.__init__()
                None
        """
        super().__init__()

    #-------------------------------------------------------------------------------------------------------------------
    @property
    def startSyslog(self):
        paramDict = self.readParamUsingIPC(param = self.constants.IEC_FB["SYSLOG_TLS_STARTLOG"]["id"],
                                           ipcObj = self.ipcObjs[0])

        return int(paramDict[self.constants.IEC_FB["SYSLOG_TLS_STARTLOG"]["id"]]["value"])

    #-------------------------------------------------------------------------------------------------------------------
    @startSyslog.setter
    def startSyslog(self, value):
        self.executeFBParamsUsingIPC(param = self.constants.IEC_FB["SYSLOG_TLS_STARTLOG"]["id"],
                                     valueToBeSet = int(value), ipcObj = self.ipcObjs[0])

    #-------------------------------------------------------------------------------------------------------------------
    @property
    def strMessage(self):
        paramDict = self.readParamUsingIPC(param = self.constants.IEC_FB["MESSAGE"]["id"],
                                           ipcObj = self.ipcObjs[0])

        return paramDict[self.constants.IEC_FB["MESSAGE"]["id"]]["value"]

    #-------------------------------------------------------------------------------------------------------------------
    @strMessage.setter
    def strMessage(self, value):
        self.setStringParamsUsingIPC(param = self.constants.IEC_FB["MESSAGE"]["id"], valueToBeSet = value,
                                     ipcObj = self.ipcObjs[0])

    #-------------------------------------------------------------------------------------------------------------------
    @property
    def strUser(self):
        paramDict = self.readParamUsingIPC(param = self.constants.IEC_FB["USER"]["id"],
                                           ipcObj = self.ipcObjs[0])

        return paramDict[self.constants.IEC_FB["USER"]["id"]]["value"]

    #-------------------------------------------------------------------------------------------------------------------
    @strUser.setter
    def strUser(self, value):
        self.setStringParamsUsingIPC(param = self.constants.IEC_FB["USER"]["id"], valueToBeSet = value,
                                     ipcObj = self.ipcObjs[0])

    #-------------------------------------------------------------------------------------------------------------------
    @property
    def iMessage_Count(self):
        paramDict = self.readParamUsingIPC(param = self.constants.IEC_FB["MESSAGE_COUNT"]["id"],
                                           ipcObj = self.ipcObjs[0])

        return int(paramDict[self.constants.IEC_FB["MESSAGE_COUNT"]["id"]]["value"])

    #-------------------------------------------------------------------------------------------------------------------
    @iMessage_Count.setter
    def iMessage_Count(self, value):
        self.setParamsUsingIPC(param = self.constants.IEC_FB["MESSAGE_COUNT"]["id"], valueToBeSet = value,
                               ipcObj = self.ipcObjs[0])

    #-------------------------------------------------------------------------------------------------------------------
    @property
    def ui_Log_Data_Transfer_Rate(self):
        paramDict = self.readParamUsingIPC(param = self.constants.IEC_FB["LOG_DATA_TRANSFER_RATE"]["id"],
                                           ipcObj = self.ipcObjs[0])

        return int(paramDict[self.constants.IEC_FB["LOG_DATA_TRANSFER_RATE"]["id"]]["value"])

    #-------------------------------------------------------------------------------------------------------------------
    @ui_Log_Data_Transfer_Rate.setter
    def ui_Log_Data_Transfer_Rate(self, value):
        self.setParamsUsingIPC(param = self.constants.IEC_FB["LOG_DATA_TRANSFER_RATE"]["id"], valueToBeSet = value,
                               ipcObj = self.ipcObjs[0])

    #-------------------------------------------------------------------------------------------------------------------
    @property
    def iFacility(self):
        paramDict = self.readParamUsingIPC(param = self.constants.IEC_FB["FACILITY"]["id"],
                                           ipcObj = self.ipcObjs[0])

        return int(paramDict[self.constants.IEC_FB["FACILITY"]["id"]]["value"])

    #-------------------------------------------------------------------------------------------------------------------
    @iFacility.setter
    def iFacility(self, value):
        self.setParamsUsingIPC(param = self.constants.IEC_FB["FACILITY"]["id"], valueToBeSet = value,
                               ipcObj = self.ipcObjs[0])

    #-------------------------------------------------------------------------------------------------------------------
    @property
    def iAuthentication(self):
        paramDict = self.readParamUsingIPC(param = self.constants.IEC_FB["AUTHENTICATION"]["id"],
                                           ipcObj = self.ipcObjs[0])

        return int(paramDict[self.constants.IEC_FB["AUTHENTICATION"]["id"]]["value"])

    #-------------------------------------------------------------------------------------------------------------------
    @iAuthentication.setter
    def iAuthentication(self, value):
        self.setParamsUsingIPC(param = self.constants.IEC_FB["AUTHENTICATION"]["id"], valueToBeSet = value,
                               ipcObj = self.ipcObjs[0])

    #-------------------------------------------------------------------------------------------------------------------
    @property
    def iSeverity(self):
        paramDict = self.readParamUsingIPC(param = self.constants.IEC_FB["SEVERITY"]["id"],
                                           ipcObj = self.ipcObjs[0])

        return int(paramDict[self.constants.IEC_FB["SEVERITY"]["id"]]["value"])

    #-------------------------------------------------------------------------------------------------------------------
    @iSeverity.setter
    def iSeverity(self, value):
        self.setParamsUsingIPC(param = self.constants.IEC_FB["SEVERITY"]["id"], valueToBeSet = value,
                               ipcObj = self.ipcObjs[0])

    #-------------------------------------------------------------------------------------------------------------------
    @property
    def bTrigger_Log_Msg(self):
        paramDict = self.readParamUsingIPC(param = self.constants.IEC_FB["TRIGGER_LOG_MSG"]["id"],
                                           ipcObj = self.ipcObjs[0])

        return int(paramDict[self.constants.IEC_FB["TRIGGER_LOG_MSG"]["id"]]["value"])

    #-------------------------------------------------------------------------------------------------------------------
    @bTrigger_Log_Msg.setter
    def bTrigger_Log_Msg(self, value):
        self.executeFBParamsUsingIPC(param = self.constants.IEC_FB["TRIGGER_LOG_MSG"]["id"], valueToBeSet = int(value),
                                     ipcObj = self.ipcObjs[0])

    #-------------------------------------------------------------------------------------------------------------------
    @property
    def bTrigger_Log_MsgIdx_1(self):
        paramDict = self.readParamUsingIPC(param = self.constants.IEC_FB["TRIGGER_LOG_MSGIDX1"]["id"],
                                           ipcObj = self.ipcObjs[0])

        return int(paramDict[self.constants.IEC_FB["TRIGGER_LOG_MSGIDX1"]["id"]]["value"])

    #-------------------------------------------------------------------------------------------------------------------
    @bTrigger_Log_MsgIdx_1.setter
    def bTrigger_Log_MsgIdx_1(self, value):
        self.executeFBParamsUsingIPC(param = self.constants.IEC_FB["TRIGGER_LOG_MSGIDX1"]["id"],
                                     valueToBeSet = int(value), ipcObj = self.ipcObjs[0])

    #-------------------------------------------------------------------------------------------------------------------
    @property
    def bTrigger_Log_MsgIdx_2(self):
        paramDict = self.readParamUsingIPC(param = self.constants.IEC_FB["TRIGGER_LOG_MSGIDX2"]["id"],
                                           ipcObj = self.ipcObjs[0])

        return int(paramDict[self.constants.IEC_FB["TRIGGER_LOG_MSGIDX2"]["id"]]["value"])

    #-------------------------------------------------------------------------------------------------------------------
    @bTrigger_Log_MsgIdx_2.setter
    def bTrigger_Log_MsgIdx_2(self, value):
        self.executeFBParamsUsingIPC(param = self.constants.IEC_FB["TRIGGER_LOG_MSGIDX2"]["id"],
                                     valueToBeSet = int(value), ipcObj = self.ipcObjs[0])

    #-------------------------------------------------------------------------------------------------------------------
    @property
    def bTrigger_Interval(self):
        paramDict = self.readParamUsingIPC(param = self.constants.IEC_FB["TRIGGER_INTERVAL"]["id"],
                                           ipcObj = self.ipcObjs[0])

        return int(paramDict[self.constants.IEC_FB["TRIGGER_INTERVAL"]["id"]]["value"])

    #-------------------------------------------------------------------------------------------------------------------
    @bTrigger_Interval.setter
    def bTrigger_Interval(self, value):
        self.executeFBParamsUsingIPC(param = self.constants.IEC_FB["TRIGGER_INTERVAL"]["id"],
                                     valueToBeSet = int(value), ipcObj = self.ipcObjs[0])

    #-------------------------------------------------------------------------------------------------------------------
    def setSyslogParams(self, protocol : str, port : str, encryption : str = None) -> None:
        """
        This method is used to set the syslog parameters value
        """
        try:
            self.logger.newStep("Setting Syslog Parameters")

            # step 1 : setting port
            self.logger.newStep("Setting Port", level = 3)
            self.setParamsUsingIPC(param = self.constants.SYSLOG_PARAMS["PORT"][0],
                                   valueToBeSet = port,
                                   ipcObj = self.ipcObjs[0])

            # step 2 : setting protocol
            self.logger.newStep("Setting Protocol", level = 3)
            self.setParamsUsingIPC(param = self.constants.SYSLOG_PARAMS["PROTOCOL"][0],
                                   valueToBeSet = protocol,
                                   ipcObj = self.ipcObjs[0])

        except Exception:
            # Log any unexpected exceptions in the outer try block
            self.logger.error("Exception Occurred in setSyslogParams")

    #-------------------------------------------------------------------------------------------------------------------
    def verifySyslogParams(self, expectedProtocol : str, expectedPort : str, expectedEncryption : str = None) -> bool:
        """
        This method is used to verify if the syslog parameter values are entered successfully
        """
        try:
            self.logger.newStep("Verifying Syslog Parameters")

            # step 1 : checking port
            self.logger.newStep("Verifying Port", level = 3)
            portReadValue = self.readParamUsingIPC(param = self.constants.SYSLOG_PARAMS["PORT"][0],
                                                   ipcObj = self.ipcObjs[0])
            portReadValue = portReadValue[self.constants.SYSLOG_PARAMS["PORT"][0]]['value']
            if portReadValue == expectedPort:
                self.logger.info(f"{[type(self).prefixCls]} Port Value is set successfully :- {expectedPort}")
            else:
                self.logger.error(f"{[type(self).prefixCls]} Port Value is NOT set successfully")
                self.logger.error(f"{[type(self).prefixCls]} Expected :- {expectedPort} Found :- {portReadValue}")
                return False

            # step 2 : checking protocol
            self.logger.newStep("Verifying Protocol", level = 3)
            protocolReadValue = self.readParamUsingIPC(param = self.constants.SYSLOG_PARAMS["PROTOCOL"][0],
                                                       ipcObj = self.ipcObjs[0])
            protocolReadValue = protocolReadValue[self.constants.SYSLOG_PARAMS["PROTOCOL"][0]]['message']
            if expectedProtocol in protocolReadValue:
                self.logger.info(f"{[type(self).prefixCls]} Protocol Value is set successfully :- {expectedProtocol}")
            else:
                self.logger.error(f"{[type(self).prefixCls]} Protocol Value is NOT set successfully")
                self.logger.error(
                    f"{[type(self).prefixCls]} Expected :- {expectedProtocol} Found :- {protocolReadValue}")
                return False

            return True
        except Exception:
            # Log any unexpected exceptions in the outer try block
            self.logger.error("Exception Occurred in verifySyslogParams")
            return False

    #-------------------------------------------------------------------------------------------------------------------
    def verifyLogs(self, logType, validationType, detailsToCheck, logsNotPresent = None, extSSHClient = None) -> bool:
        """
        Verifies log files based on provided details to check.
        """

        return Lib_TLS.verifyLogs(self,
                                  logType = logType,
                                  validationType = validationType,
                                  detailsToCheck = detailsToCheck,
                                  logsNotPresent = logsNotPresent,
                                  extSSHClient = extSSHClient)
