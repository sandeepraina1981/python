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
"""This file includes constants used in Opc Ua LLM Test
"""
#-----------------------------------------------------------------------------------------------------------------------
# PyTeF Internal Code imports (must be defined before code)
#-----------------------------------------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------------------------------------
# SVN keyword section
#-----------------------------------------------------------------------------------------------------------------------
FILE_URL = "$HeadURL: http://repository.lenze.com/ssv/TestRepository/branches/sdc/tests/common/opc_ua/utils/constants_opc_ua.py $"[10:-2]  # noqa:E501
FILE_REV = "$Revision: 9362 $"[11:-2]
FILE_DATE = "$LastChangedDate: 2022-12-06 12:29:26 +0530 (Tue, 06 Dec 2022) $"[18:-2]
FILE_AUTHOR = "$LastChangedBy: saklechas $"[16:-2]

#-----------------------------------------------------------------------------------------------------------------------
# PyTeF file header end
#-----------------------------------------------------------------------------------------------------------------------
# Relative path for Device configuration file for OPC UA LLM test
CONFIG_FILE_PATH = r'/config/DeviceConfig_LLM.xls'

# Relative path for template report file for LLM test
REPORT_FILE_PATH = r'report\OPC_UA_LLM_Automated_Test_Report.xlsx'

# Name of the Report sheet to update the results
REPORT_SHEET_NAME = "LLM_Test_Report"

# Header string for the report
REPORT_HEADER = "OPC UA LLM Test Report - {} - {}"   # OPC UA LLM Test Report - <controllerType> - <releaseName>

# Path for UA Expert project
UA_EXPERT_PROJ_PATH = r"projects\uaExpert"

# Name of UA Expert project for OPC UA LLM test
UA_EXPERT_PROJ_NAME = "PUB_SUB_Config.uap"

# Config name in UA Expert project
UA_EXPERT_CONFIG_NAME = "LLM_Pub_Sub_Config"

# Document name of the PUB SUB COnfig View
UA_EXPERT_PUB_SUB_CFG_DOC_NAME = "PubSub Config View"

# Path for OPC UA LLM PLC project
PLC_PROJ_PATH = r"projects\plcd\{}"

# Name of PLCD project for OPC UA LLM test
PLC_PROJ_NAME = "OPC_UA_LLM_PROJECT.project"

# Below is the count of maximum number of Third party connections available via OPC UA, this count may change in future
MAX_NUM_OF_EXT_SESSIONS_POSSIBLE = {'c430' : 4, 'c550' : 6, 'c520': 6}

# Below is the list of different Application credit values for which the testing is done
APP_CRED_VALUES_TO_TEST_LIST = [0, 100, 150]

# Below is the count of minimum third party client connection needed in order to activate extended packages
MIN_EXT_CLIENT_REQ_TO_ACTIVATE_EXT_PKG = 2

# String used as name to create third party python object
THIRD_PARTY_PYTHON_CLIENT_NAME = "Third-party-client-{}"

# Below values are required to occupy third party python client connection
THIRD_PARTY_PYTHON_SERVER_URL = "opc.tcp://{}:4840/freeopcua/server/"
THIRD_PARTY_PYTHON_SERVER_NAMESPACE = "urn:Lenze:PLCOpen"
THIRD_PARTY_CLIENT_APP_URI = "urn:{}:PyTeF:python-opcua"

# Legacy name for External client name edit box that on Ua Server page (PLCD tool)
EXT_CLNT_NAME_EDITBOX_LEGACY_NAME = "Client of external session {}"

# Parameter to check Connected External client names
EXTERNAL_CLIENT_NAME_PLC_PARAM_INDEX = "0x2473"
EXTERNAL_CLIENT_NAME_PLC_PARAM_SUB_INDEX = 130

# Matching strings for possible Configuration mode value in combobox on License Manager page
CONFIG_MODE_STATIC_AC_STR = "Static AC Configuration"
CONFIG_MODE_ALL_AC_TO_FAST_STR = "All AC to FAST Toolbox"
FAST_SYS_CONFIG_NAME = "FAST System Configuration"

# Matching string for Fast system diagnosis node on devices window of PLCD tool
FAST_SYS_DIAGNOSIS_NAME = "FAST System Diagnosis"

# Matching string for OPC UA Server node on devices window of PLCD tool
OPC_UA_SERVER_NAME = "OPC UA Server"

# Below are the credentials for the Diagnosis tool, these should be updated with credentials for diagnosis in the
# controller being used for the test
DIAGNOSIS_USERNAME = "Advanced"
DIAGNOSIS_BASE64_PWD = "YWRtaW4="

# Message string that appears in Diagnosis tool if Extended package is activated
EXTENDED_PACKAGE_STR = {"c430" : "OPC UA Extended Package2",
                        "c550" : "OPC UA Extended Package3",
                        "c520" : "OPC UA Extended Package3"}

CONTROLLER_FAMILY_MAP = {
    "c550" : "c500",
    "c520" : "c500",
    "c430" : "c400"
    }

PUB_VAR_NODESTRING = "ns=4;s=|var|{}.Application.Pub_PRG.iPUB_Variable"
SUB_VAR_NODESTRING = "ns=4;s=|var|{}.Application.Sub_PRG.iSUB_Variable"

SUB_VAR_AUTO_CHANGE_NODESTRINGS = ["ns=4;s=|var|{}.Application.Sub_PRG.Sub_Var1",
                                   "ns=4;s=|var|{}.Application.Sub_PRG.Sub_Var2",
                                   "ns=4;s=|var|{}.Application.Sub_PRG.Sub_Var3"]

PUB_SUB_CONFIG_FAILED_LOGBOOK_MSG = "The PubSub module activation failed because of missing credit points."
PUB_SUB_ACTIVATION_PARAM_STR = "0x247b:001"
PUB_SUB_ACTIVATION_DISABLE_VALUE = 0
PUB_SUB_ACTIVATION_ENABLED_VALUE = 1

OPC_UA_PUB_SUB_STATE_PARAM_STR = "0x247e:001"
OPC_UA_PUB_SUB_STATE_DISABLE_VALUE = 0
OPC_UA_PUB_SUB_STATE_ENABLED_VALUE = 1
OPC_UA_PUB_SUB_STATE_RUNNING_VALUE = 2

PLC_OPEN_CLIENT_SERVER_URL = "opc.tcp://{}:4840"  # opc.tcp//<controller IP>:4840 "opc.tcp://10.255.184.201:4840"
PLC_OPEN_CLIENT_SERVER_URL_SYMBOL_NAME = "Application.GlobalSettings.sOpcUaMethodCallServerUrl_{}"
PLC_OPEN_CLIENT_EXECUTE_CONNECT_SYMBOL_NAME = "Application.MainTaskPLCOpenClientFB.xExecutePLCOpenClientFB"
PLC_OPEN_CLIENT_CONNECT_EXTRA_SYMBOL_NAME = "Application.MainTaskPLCOpenClientFB.xEnableNextServer"
PLC_OPEN_CLIENT_DISABLE_ONE_CLIENT_SYMBOL_NAME = "Application.GlobalSettings.xClientDisable"
PLC_OPEN_CLIENT_CONNECT_ERROR_SYMBOL_NAME = "Application.GVL_Pytef.Server{}_ErrorID"
PLC_OPEN_CLIENT_FAILED_CONNECT_ERROR_ID = 2952798017
USED_EXTERNAL_SESSION_COUNT_PARAM = "0x2473:103"
MAX_EXTERNAL_SESSION_COUNT_PARAM = "0x2471:103"

OPC_AC_REJECTED_LOGBOOK_MSG = "OpcUAC Rejected"
# CUSTOMER_SSH_PORT = 47877
# SSH_CUSTOMER_USERNAME = "customer"
# CUSTOMER_PRIV_KEY_FILE = "customer.rsa"
UA_BIN_FILE_PATH_IN_CTRL = r"/sdcard/plc/prg/pta1/OpcUaData"
PUBSUB_CONFIG_BIN_FILE_NAME = "pubsubconfig.uabinary"
PUB_SUB_CONFIG_FOLDER_PATH = r"projects/uabinaryfiles/{}/"
