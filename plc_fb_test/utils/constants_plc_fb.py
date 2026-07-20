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
"""This file includes constants used in Open PLC FB Test
"""
#-----------------------------------------------------------------------------------------------------------------------
# PyTeF Internal Code imports (must be defined before code)
#-----------------------------------------------------------------------------------------------------------------------
from enum import Enum
#-----------------------------------------------------------------------------------------------------------------------
# SVN keyword section
#-----------------------------------------------------------------------------------------------------------------------
FILE_URL = "$HeadURL: $"[10:-2]
FILE_REV = "$Revision: $"[11:-2]
FILE_DATE = "$LastChangedDate: $"[18:-2]
FILE_AUTHOR = "$LastChangedBy: $"[16:-2]

#-----------------------------------------------------------------------------------------------------------------------
# PyTeF file header end
#-----------------------------------------------------------------------------------------------------------------------
# Relative path for Device configuration file for OPC UA FB test
CONFIG_FILE_FB_PATH: str = r'/config/DeviceConfig_PLC_Open_Client_FB.xls'
CONFIG_FILE_FB_EXT_PATH: str = r'/config/DeviceConfig_PLC_Open_Client_FB_Ext_Feat.xls'
CONFIG_FILE_FB_AUTH_TOKENS_PATH: str = r'/config/DeviceConfig_PLC_Open_Client_Auth_Tokens.xls'

# Relative path for template report file for OPC UA FB test
REPORT_FILE_FB_PATH: str = r'report\PLC_Open_Client_FB_Automated_Test_Report.xlsx'
REPORT_FILE_FB_EXT_PATH: str = r'report\PLC_Open_Client_FB_Ext_Feat_Automated_Test_Report.xlsx'
REPORT_FILE_FB_AUTH_TOKENS_PATH: str = r'report\PLC_Open_Client_FB_Auth_Tokens_Automated_Test_Report.xlsx'

# Name of the Report sheet to update the results
REPORT_SHEET_FB_NAME: str = "PLC_Open_Client_FB_Test_Report"
REPORT_SHEET_FB_EXT_NAME: str = "PLC_Open_Client_FB_Test_Report"
REPORT_SHEET_FB_AUTH_TOKENS_NAME: str = "PLC_Open_Client_AT_Test_Report"

# Header string for the report
# OPC UA FB Test Report - <controllerType> - <releaseName>
REPORT_FB_HEADER: str = "PLC Open Client FB Test Report - {} - {}"

# OPC UA FB Test Report - <controllerType> - <releaseName>
REPORT_FB_EXT_HEADER: str = "PLC Open Client FB Extended Feature Test Report - {} - {}"

# OPC UA FB Test Report - <controllerType> - <releaseName>
REPORT_FB_AUTH_TOKENS_HEADER: str = "PLC Open Client Authorization Tokens Test Report - {} - {}"

MAX_CONTROLLERS: int = 2
SESSION_MAX: dict[str, int] = {"c430": 4, "c520": 6, "c550": 6}
SESSION_WAIT: dict[str, int] = {"Internal": 1, "External": 10, "Multiple": 1}
SESSION_URL_INDEX: str = "session{}"
SESSION_START_INDEX: int = 1
TYPE_OF_CERTIFICATES = ['Trusted Certificates', 'Quarantined Certificates']

PLC_HEADER = "PLC Designer"
PLC_PROJ_PATH = r"\projects\plcd\{}\{}"
# Name of PLCD project for OPC UA LLM test
PLC_PROJ_NAME = "OpSys_PLC Open Client FB_{}_Sys25_v1.0"

# opc.tcp//<controller IP>:4840 "opc.tcp://10.255.184.201:4840"
PLC_OPEN_CLIENT_SERVER_URL: str = "opc.tcp://{}:4840"

PLC_OPEN_APPLICATION_GVL_PYTEF: str = "Application.GVL_pytef."

#---------------------- IN USE ----------------------------------------------------------------------------------------
PLC_OPEN_CLIENT_SERVER_URL_SYMBOL_NAME: str = PLC_OPEN_APPLICATION_GVL_PYTEF + "g_sOutOpcUaMethodCallUrl_Server{}"
PLC_OPEN_CLIENT_EXECUTE_CONNECT_SYMBOL_NAME: str = PLC_OPEN_APPLICATION_GVL_PYTEF + "g_xOutPytefExecuteServer{}"
PLC_OPEN_CLIENT_MODE_SYMBOL_NAME: str = PLC_OPEN_APPLICATION_GVL_PYTEF + "g_iOutPytefMode"

PLC_OPEN_CLIENT_IMPLEMENTATION_SYMBOL_NAME: str = PLC_OPEN_APPLICATION_GVL_PYTEF + \
    "g_iOutPytef_iAuth_ImplimentationServer{}"

#---------------------- SYMBOL NAMES USED FOR VALIDATION --------------------------------------------------------------
PLC_OPEN_CLIENT_CONNECT_STEPNO_SYMBOL_NAME: str = PLC_OPEN_APPLICATION_GVL_PYTEF + "g_iInPytefStepNoServer{}"

PLC_OPEN_CLIENT_CONNECT_STEPFAILED_SYMBOL_NAME: str = PLC_OPEN_APPLICATION_GVL_PYTEF + \
    "g_fInPytef_dwErrorId_StepServer{}"

PLC_OPEN_CLIENT_CONNECT_STEPERRORID_SYMBOL_NAME: str = PLC_OPEN_APPLICATION_GVL_PYTEF + "g_dwInPytef_dwErrorIdServer{}"
PLC_OPEN_CLIENT_CONNECT_CONNECTDONE_SYMBOL_NAME: str = PLC_OPEN_APPLICATION_GVL_PYTEF + "g_xInPytefConnectDoneServer{}"
PLC_OPEN_CLIENT_CONNECT_BROWSEDONE_SYMBOL_NAME: str = PLC_OPEN_APPLICATION_GVL_PYTEF + "g_xInPytefBrowseDoneServer{}"
PLC_OPEN_CLIENT_CONNECT_WRITEDONE_SYMBOL_NAME: str = PLC_OPEN_APPLICATION_GVL_PYTEF + "g_xInPytefWriteDoneServer{}"
PLC_OPEN_CLIENT_CONNECT_READDONE_SYMBOL_NAME: str = PLC_OPEN_APPLICATION_GVL_PYTEF + "g_xInPytefReadDoneServer{}"
PLC_OPEN_CLIENT_CONNECT_WRITEREADDONE_SYMBOL_NAME: str = PLC_OPEN_APPLICATION_GVL_PYTEF + \
    "g_xInPytefWriteReadDoneServer{}"

PLC_OPEN_CLIENT_CONNECT_METHODDONE_SYMBOL_NAME: str = PLC_OPEN_APPLICATION_GVL_PYTEF + \
    "g_axInPytefMethodDoneListServer{}"

PLC_OPEN_CLIENT_CONNECT_WRITE_ERRORLIST_SYMBOL_NAME: str = PLC_OPEN_APPLICATION_GVL_PYTEF + \
    "g_adwInPytefWriteNodeErrorListServer{}"

PLC_OPEN_CLIENT_CONNECT_READ_ERRORLIST_SYMBOL_NAME: str = PLC_OPEN_APPLICATION_GVL_PYTEF + \
    "g_adwInPytefReadNodeErrorListServer{}"

PLC_OPEN_CLIENT_CONNECT_WRITEREAD_ERRORLIST_SYMBOL_NAME: str = PLC_OPEN_APPLICATION_GVL_PYTEF + \
    "g_aiInPytefWriteReadNodeErrorListServer{}"

PLC_OPEN_CLIENT_CONNECT_METHOD_ERRORLIST_SYMBOL_NAME: str = PLC_OPEN_APPLICATION_GVL_PYTEF + \
    "g_adwInPytefMethodErrorListServer{}"

#INT PROVIDE CYCLE COUNT KEEP CHECKING TO SEE IF CYCLE COUNT UPDATING ELSE MARK TEST AS FAIL
PLC_OPEN_CLIENT_CONNECT_COUNTCYCLES_SYMBOL_NAME: str = PLC_OPEN_APPLICATION_GVL_PYTEF + \
    "g_diInPytefCountCyclesServer{}"

# Security Tokens
# Auth_UserIdentity_TokenType:=0; "Anonymous"; (Client Authentication from Anonymous User for Username and Password)
# Auth_UserIdentity_TokenType:=1; "Username"; (Client Authentication from Code for Username and Password )
# Auth_UserIdentity_TokenType:=100; "UserTokenID"; (Client Authentication from Parameters for Username and Password)
PLC_OPEN_CLIENT_CONNECT_TOKEN_TYPE_SERVER: str = PLC_OPEN_APPLICATION_GVL_PYTEF + \
    "g_iOutPytef_iAuth_UserIdentity_TokenTypeServer{}"

# Useranme
PLC_OPEN_CLIENT_CONNECT_TOKEN_PRAM_USERNAME_SERVER: str = PLC_OPEN_APPLICATION_GVL_PYTEF + \
    "g_sOutPytefUserIdentityToken_TokenParam1Server{}"

# Password
PLC_OPEN_CLIENT_CONNECT_TOKEN_PRAM_PASSWORD_SERVER: str = PLC_OPEN_APPLICATION_GVL_PYTEF + \
    "g_sOutPytefUserIdentityToken_TokenParam2Server{}"

PLC_OPEN_CLIENT_UA_CLIENT_UI: str = "UAClientUT_{}"

# Dictionary storing user managements details
USERS_DETAILS_DICT = {
    "administratorUser": {
        "userName": "user1",
        "group": "Administrator",
        "password": "QWRtaW5pc3RyYXRvcg==",
    }
}

#----------------------------------------------------------------------------------------------------------------------
class TestType(str, Enum):
    """Enum for test types."""

    INTERNAL = "Internal"
    EXTERNAL = "External"
    MULTIPLE = "Multiple"

#----------------------------------------------------------------------------------------------------------------------
class PolicyNames(str, Enum):
    """Enum for PLCD communication policy names."""

    NO_ENCRYPTION = "No encryption"
    OPTIONAL_ENCRYPTION = "Optional encryption"
    ENFORCED_ENCRYPTION = "Enforced encryption"

#----------------------------------------------------------------------------------------------------------------------
class FBMode(Enum):
    """
    Enum representing different Function Block program modes.
    """

    BROWSE = 1
    TRANSLATE_PATH = 2
    FIXED_NODE = 3
    B_T_PASSING = 4
    B_T_F_PASSING = 5

#----------------------------------------------------------------------------------------------------------------------
class FBTokenType(Enum):
    """
    Enum representing different Function Block program modes.
    """

    ANONYMOUS = 0
    USERNAME = 1
    USERTOKENID = 100

#----------------------------------------------------------------------------------------------------------------------
class FBImplementation(Enum):
    """
    Enum representing different Function Block program implementations.
    """

    VARIABLE_RW_METHOD_CONNECT = 0
    VARIABLE_RW_CONNECT = 1
    CONNECT = 2
