# -*- coding: utf-8 -*-
#
# © 2007-2020 Lenze Drive Systems GmbH, Lenze Automation GmbH. All rights reserved.
# © 2020-     Lenze SE. All rights reserved.
#
#-----------------------------------------------------------------------------------------------------------------------
# PyTeF file header (for PyTeF Internal Code) V1.4-01
#-----------------------------------------------------------------------------------------------------------------------
# Disable linter warnings -> ONLY for PyTeF internal code!
#
#-----------------------------------------------------------------------------------------------------------------------
# PyTeF Internal Code docstring (must be first definition in file)
#-----------------------------------------------------------------------------------------------------------------------
"""This file includes constants used in Auditlog Tests
"""
#-----------------------------------------------------------------------------------------------------------------------
# PyTeF Internal Code imports (must be defined before code)
#-----------------------------------------------------------------------------------------------------------------------

import os

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
MANUAL_REQUIREMENT = ['test_c550_tc_Grp_04', 'test_c550_tc_Grp_06', 'test_c550_tc_Grp_07', 'test_c550_tc_Grp_09',
                      'test_c550_tc_Grp_10', 'test_c550_tc_Grp_11']

CMD_PARAM_MANUAL_INTERVENTION = ['tc_20_verifySysLogsCopyWOSDCard']

# Device Config sheet name constants
COMMON_SETTINGS_SHEET = "Common Settings"
HELPER_SHEET = "Test Case Sequence"

JIRA_TESTKEY = 'SYST-{}'

# Report file path
REPORT_FILE_PATH = r"\Results\report\Report_AuditLog_{}.xlsx"   # The report file
REPORT_SHEET_SYSLOG = r"Audit_Log_Sys_Log"
REPORT_SHEET_COMMAND_PARAMETER = r"Command_Parameter"
REPORT_SHEET_TLS = r"TLS"

# Config file path
CONFIG_FILE_PATH_SYS_LOG = r"\config\DeviceConfig_Audit_Sys_Log.xls"   # Config file path
CONFIG_FILE_PATH_CMD_PARAM = r"\config\DeviceConfig_AL_CmdParam.xls"
CONGIF_FILE_PATH_TLS = r"\config\DeviceConfig_TLS.xls"

# AuditLog Cmd Parameter Config file path
CONFIG_CMD_PARAMETER_FILE_PATH = r"\config\DeviceConfig_AL_Cmd_Parameter.xls"   # Config file path

LPK_PATH = r"project\lpk"
TAR_PATH = r"project\firmwareTar"

# Dictionary storing user managements details
USERS_DETAILS_DICT = {
    "administratorUser": {
        "userName": "user1",
        "group": "Administrator",
        "password": "QWRtaW5pc3RyYXRvckAxMjM=",
    }
}

GDS_USER = {
    "userName": "GDS1",
    "password": "R0RTMUAxMjM="
    }

WRONG_USERNAME = "a"
WRONG_PASSWORD = "YWRtaW5AMTIz"
PERMISSION_DENIED_PATH = r"\\zin502.lenze.com\Data\04ODC_Ops"
USER_MGMT_PATH = r"project\userManagement\Users_Groups_export.dum2"
NEW_GROUP_NAME = "newGroup"

DEVICE_RIGHT_MANAGEMENT_FILE_NAME = "accessRights.drm"
DEVICE_RIGHT_MANAGEMENT_FILE_PATH = 'input_files\\'

# --------------------------------------------------- PLCD -------------------------------------------------------------
PLC_HEADER = "PLC Designer"
PLC_PROJ_PATH = r'project\plcd\{}'
COPIED_PLC_PROJECT_PATH = r"project\copied_project"
PLC_PROJ_NAME = r'Audit_Log_{}.project'
PLC_NTP_PROJ_NAME = r'Audit_Log_NTP_{}.project'
PLC_PROJECT_EXTENSION = ".project"
DEVICE_NAME = "Controller"
LOGGING_PROTOCOL_NODEPATH = ["Communication", "System Logging Protocol (SysLog)"]
SYSLOG_SEVERITY_LIST = ['emerg', 'alert', 'crit', 'err', 'warning', 'notice', 'info', 'debug']
TYPE_OF_CERTIFICATES = ['Trusted Certificates', 'Quarantined Certificates']

# --------------------------------------------- Application Loader -----------------------------------------------------
USER_HOME = os.path.expanduser('~')
USER_NAME = os.path.split(USER_HOME)[-1].lower()

# LDA Folder and CUSTOMER RSA PATH constants
LDA_FOLDER_PATH = r"input_files\LDA_Files"
CUSTOMER_RSA_PATH = r"\\zin502\Data2\SV Team\DO_NOT_DELETE\.ssh\customer.rsa"

ROOT_RSA_PATH = None

# ---------------------------------------------- Firmware Loader -------------------------------------------------------
DEVICE = {
    "c520": "c500",
    "c550": "c500",
    "c430": "c400",
    "i950 (BS-STO)": "i950 (BS-STO)"
    }
DEVICE_AND_VERSION = {
    "c520": "c5xx V{}",
    "c550": "c5xx V{}",
    "c430": "c4xx V{}",
    "i950 (BS-STO)": "i950 (BS-STO) V{}"
    }

CUSTOMER_SSH_CONFIG = {
    "port": 22,
    "username": "customer",
    "privKeyFile": CUSTOMER_RSA_PATH
    }

#Update the privKeyFile at runtime as the key differs for different controller Ips
ROOT_SSH_CONFIG = {
    "port": 22,
    "username": "root",
    "privKeyFile": None
    }


#----------------------------------------------- Easy Ui Designer ------------------------------------------------------
# Easy UI designer project path constants
SLN_FOLDER_PATH = r"project\easyUi\{}"
SLN_FILE_NAME = "c5xx_IPC0404_UI_V1.3_June2021_IT5.sln"

#----------------------------------------------- Pytef Client ----------------------------------------------------------
SERVER_URL = "opc.tcp://{}:4840/freeopcua/server"
PRODUCT_URI = "urn:SDC:testclient"
SERVER_NAMESPACE = "urn:Lenze:PLCOpen"

#------------------------------------------------UAGDS TOOL-------------------------------------------------------------
UAGDS_PASSWORD = r"admin"
UAGDS_CERTIFICATE_NAME = "UaGDS@{}.lenze.com"
UAGDS_PLC_CERTIFICATE = "LenzeSDC{}"
SERVER_URL = "opc.tcp://{}:4840"

#----------------------------------------------- Key Details -----------------------------------------------------------
# ROOT_KEY_FILEPATH = r"PKK_Files\{}\root.pem"
ROOT_KEY_FILEPATH = r"C:\Users\Pytef03\.ssh\pytef\root.pem"
CUSTOMER_KEY_FILEPATH = r"PKK_Files\General c5xx_c4xx\customer.pkk"
ROOT_USERNAME = "root"
ROOT_PORT = 22

CONTROLLER_TYPE = {"c430" : "c4xx", "c550" : "c5xx", "c520" : "c5xx"}

# Types of Logs
LOCAL_LOG_0 = "local_log_0"
LOCAL_LOG_1 = "local_log_1"
LOCAL_LOG_2 = "local_log_2"
DAEMON_LOG = "daemon_log"
AUTH_LOG = "auth_log"
USER_LOG = "user_log"
NTP_LOG = "ntp_log"
KERN_LOG = "kern_log"
AUTHPRIVILEAGE_LOG = "authprivileage_log"
SERVER_LOG = "server_log"

# Name of log files
LOG_FILES = {LOCAL_LOG_0: "local0.log", LOCAL_LOG_1: "local1.log", LOCAL_LOG_2: "local2.log",
             DAEMON_LOG : "daemon.log", AUTH_LOG : "auth.log", USER_LOG : "user.log",
             NTP_LOG : "ntp.log", KERN_LOG : "kern.log", AUTHPRIVILEAGE_LOG : "authpriv.log",
             SERVER_LOG : "{}"}

LOG_FILES = {LOCAL_LOG_0: "current"}

# CRONY_ACTIONS
CRONY_CMDS = {"start" : r'systemctl start chrony',
              "stop" : r'systemctl stop chrony',
              "restart" : r'systemctl restart chrony'}

#---------------------------------------------------Controller Log Paths------------------------------------------------
CONTROLLER_LOG_PATH = r"/log_data/log/"
CONTROLLER_LOG_PATH_i950 = r"/var/log/local0/"
COPIED_LOG_PATH = r"/tmp/lsyslog/"
SDCARD_PATH = r"/sdcard"
SYSTEM_LOG_PATH = r'controllerLogs'
COPIED_LOG_PATH = r"/tmp/lsyslog/"

WAIT_CONTROLLER_TO_REFRESH = 5

DEVICE_COMMAND_MSG_STRINGS = {
    "loadLenzeSettingsCmd" : ["Device command 'Load Lenze settings' is executed. [Parameter: 0x2022_001]"],
    "saveParamSettingsCmd" : ["Device command 'Save Parameter settings' is executed. [Parameter: 0x2022_003]"],
    "startAppCmd" : ["Device command 'Start Application' is executed. [Parameter: 0x2022_044]"],
    "stopAppCmd" : ["Device command 'Stop Application' is executed. [Parameter: 0x2022_045]"],
    "deleteLogbookCmd" : ["Device command 'Delete Logbook' is executed. [Parameter: 0x2022_015]"],
    "exportLogbookCmd" : ["Device command 'Export Complete Logbook' is executed. [Parameter: 0x2022_036]"],
    "deleteLogfilesCmd" : ["Device command 'Delete Logfiles' is executed. [Parameter: 0x2022_037]"],
    "loadTADefaultCmd" : ["Device command 'Load TA Defaults' is executed. [Parameter: 0x2022_039]"],
    "backupCmd" : ["Device command 'Backup' is executed. [Parameter: 0x2022_040]"],
    "restoreCmd" : ["Device command 'Restore' is executed. [Parameter: 0x2022_043]"],
    "reloadBootProjectCmd" : ["Device command 'Reload Bootproject' is executed. [Parameter: 0x2022_046]"],
    "resetColdCmd" : ["Device command 'Reset Cold' is executed. [Parameter: 0x2022_048]"],
    "resetOrigin" : ["Device command 'Reset Origin' is executed. [Parameter: 0x2022_049]"],
    "exportFastCmd" : ["Device command 'Export FAST Framework data' is executed. [Parameter: 0x2022_050]"],
    "activeLoadedAppCmd" : ["Device command 'Activate loaded Application' is executed. [Parameter: 0x2022_038]"],
    "upDownCmd" : ["Device command 'Start Up/Downgrade' is executed. [Parameter: 0x2022_047]"],
    "deviceRestartCmd" : ["Device command 'Restart Device' is executed. [Parameter: 0x2022_035]"],
    "copySyslogCmd" : ["Device command 'Copy SysLog data' is executed. [Parameter: 0x2022_051]"]
    }

LOG_DICTIONARY_DEV_CMD = {
    'c550' : DEVICE_COMMAND_MSG_STRINGS,
    'c520' : DEVICE_COMMAND_MSG_STRINGS,
    'c430' : DEVICE_COMMAND_MSG_STRINGS,
    'i950 (BS-STO)' : {
        "loadLenzeSettingsCmd" : ["Device command 'Load default settings' is executed.. [Parameter: 0x2022_001]"],
        "saveParamSettingsCmd" : ["Device command 'Save user data' is executed.. [Parameter: 0x2022_003]"],
        "startAppCmd" : ["Device command 'Start Application' is executed.. [Parameter: 0x2022_044]"],
        "stopAppCmd" : ["Device command 'Stop Application' is executed.. [Parameter: 0x2022_045]"],
        "deleteLogbookCmd" : ["Device command 'Delete Logbook' is executed.. [Parameter: 0x2022_015]"],
        "exportLogbookCmd" : ["Device command 'Export Complete Logbook' is executed.. [Parameter: 0x2022_036]"],
        "deleteLogfilesCmd" : ["Device command 'Delete Logfiles' is executed.. [Parameter: 0x2022_037]"],
        "loadTADefaultCmd" : ["Device command 'Load TA Defaults' is executed.. [Parameter: 0x2022_039]"],
        "backupCmd" : ["Device command 'Backup' is executed.. [Parameter: 0x2022_040]"],
        "restoreCmd" : ["Device command 'Restore' is executed.. [Parameter: 0x2022_043]"],
        "reloadBootProjectCmd" : ["Device command 'Reload Bootproject' is executed.. [Parameter: 0x2022_046]"],
        "resetColdCmd" : ["Device command 'Reset Cold' is executed.. [Parameter: 0x2022_048]"],
        "resetOrigin" : ["Device command 'Reset Origin' is executed.. [Parameter: 0x2022_049]"],
        "exportFastCmd" : ["Device command 'Export FAST Framework data' is executed.. [Parameter: 0x2022_050]"],
        "activeLoadedAppCmd" : ["Device command 'Activate loaded Application' is executed.. [Parameter: 0x2022_038]"],
        "upDownCmd" : ["Device command 'Start Up/Downgrade' is executed.. [Parameter: 0x2022_047]"],
        "deviceRestartCmd" : ["Device command 'Restart Device' is executed.. [Parameter: 0x2022_035]"],
        "copySyslogCmd" : ["Device command 'Copy SysLog data' is executed.. [Parameter: 0x2022_051]"]
        }
    }

#---------------------------------------------------Log Messages Dictionary---------------------------------------------
LOG_DICTIONARY = {
    LOCAL_LOG_0 : {
        "startApp" : ["[Application] Start successful"],
        "stopApp" : ["[Application] Stop successful"],
        "startStopApp" : ["[Application] Start successful", "[Application] Stop successful"],
        "bootOnline" : ["[Application] Create boot project successful"],
        "resetWarm" : ["[Application] Reset Warm successful"],
        "resetCold" : ["[Application] Reset Cold successful"],
        "reseOrigin" : ["[Application] Reset Origin successful"],
        "resetWarmColdOrigin" : ["[Application] Reset Warm successful",
                                 "[Application] Reset Cold successful",
                                 "[Application] Reset Origin successful"],
        "resetOriginDevice" : [r"Reset Origin Device \(\d\)"],
        "startAppUser" : [r"User=([^<>]+), App \[([^<>]+)\] Start successful"],
        "stopAppUser" : [r"User=([^<>]+), App \[([^<>]+)\] Stop successful"],
        "createBootProjUser" : [r"User=[^<>]*, App \[([^<>]+)\] Create boot project successful"],
        "userLoginSuccessful" : [r"User=[^']*, Sessioninfo: client version: '[^']*', CDS version: '[^']*'",
                                 r"User=[^']*, Device Login from [^']* successful",
                                 r"User=[^']*, Sessioninfo: client: '[^']*', host: '[^']*'",
                                 r"User=([^']+), App \[Application\] Login successful", r"User=[^']*, Login \(1\)"],
        "userLoginFailed" : [r"User=[^<>]+, Login failed", r"User=[^<>]*, Device Login from [^<>]+ failed",
                             r"User=[^']*, Sessioninfo: client version: '[^']*', CDS version: '[^']*'",
                             r"User=[^']*, Sessioninfo: client: '[^']*', host: '[^']*'"],
        "addNewUser" : ["User=[^']*, Add user '[^']*' to Group '[^']*' successful",
                        "User=[^']*, Add group '[^']*' successful",
                        "System, Add object '[^']*' successful",
                        "System, Set rights of group '[^']*' on object '[^']*' successful",
                        "System, Set denied rights of group '[^']*' on object '[^']*' successful"],
        "brokenChannel" : ["App [Application] Logout because of broken channel"],
        "logoutSuccessful" : ["App [Application] Logout successful"],
        "exportUserMgmtSuccess" : ["Export UserManagement successful"],
        "exportUserMgmtFailure" : ["Export UserManagement failed"],
        "exportUserMgmtSuccFail" : ["Export UserManagement successful", "Export UserManagement failed"],
        "importUserMgmtSuccess" : ["Import UserManagement successful"],
        "importUserMgmtFailure" : ["Import UserManagement failed"],
        "importUserMgmtSuccFail" : ["Import UserManagement successful", "Import UserManagement failed"],
        "createBootProject" : ["App [Application] Create boot project successful"],
        "easyStarterConnectDisconnect" : ["Lenze:EASYStarter connected", "Lenze:EASYStarter disconnected"],
        "uaExpertConnectDisconnect" : ["UaExpert connected", "UaExpert disconnected"],
        "3rdPartyClientConnectDisconnect" : ["PyTeF:python-opcua connected", "PyTeF:python-opcua disconnected"],
        "easyUiConnectDisconnect" : ["FASTUIRuntime connected", "FASTUIRuntime disconnected"],
        "uagdsConnect" : ["Client urn:UnifiedAutomation:UaGds:Server:{}.lenze.com connected"],
        "uagdsDisconnect" : ["Client urn:UnifiedAutomation:UaGds:Server:{}.lenze.com disconnected"],
        "visiwinConnect" : ["VisiWin7.Server.Manager: AuthClass Auth.CheckAuthToken: OK",
                            "VisiWin7.Server.Manager: Initialize: OK",
                            "VisiWin7.Server.Manager: GetKeys: OK value="],
        "ntpRestart" : ["Server started on opc.tcp://"],
        "loadFactorySettings" : ["Load parameter factory settings successful"],
        "reloadBootProject" : ["Reload boot project"],
        "opcConnection" : ["Server started on opc.tcp://"],
        "loadLenzeSettingsCmd" : ["Device command: 'Load Lenze settings' is executed. [Parameter: 0x2022_001]"],
        "saveParamSettingsCmd" : ["Device command: 'Save Parameter settings' is executed. [Parameter: 0x2022_003]"],
        "startAppCmd" : ["Device command: 'Start Application' is executed. [Parameter: 0x2022_044]"],
        "stopAppCmd" : ["Device command: 'Stop Application' is executed. [Parameter: 0x2022_045]"],
        "deleteLogbookCmd" : ["Device command: 'Delete Logbook' is executed. [Parameter: 0x2022_015]"],
        "exportLogbookCmd" : ["Device command: 'Export Complete Logbook' is executed. [Parameter: 0x2022_036]"],
        "deleteLogfilesCmd" : ["Device command: 'Delete Logfiles' is executed. [Parameter: 0x2022_037]"],
        "loadTADefaultCmd" : ["Device command: 'Load TA Defaults' is executed. [Parameter: 0x2022_039]"],
        "backupCmd" : ["Device command: 'Backup' is executed. [Parameter: 0x2022_040]"],
        "restoreCmd" : ["Device command: 'Restore' is executed. [Parameter: 0x2022_043]"],
        "reloadBootProjectCmd" : ["Device command: 'Reload Bootproject' is executed. [Parameter: 0x2022_046]"],
        "resetColdCmd" : ["Device command: 'Reset Cold' is executed. [Parameter: 0x2022_048]"],
        "resetOrigin" : ["Device command: 'Reset Origin' is executed. [Parameter: 0x2022_049]"],
        "exportFastCmd" : ["Device command: 'Export FAST Framework data' is executed. [Parameter: 0x2022_050]"],
        "activeLoadedAppCmd" : ["Device command: 'Activate loaded Application' is executed. [Parameter: 0x2022_038]"],
        "upDownCmd" : ["Device command: 'Start Up/Downgrade' is executed. [Parameter: 0x2022_047]"],
        "deviceRestartCmd" : ["Device command: 'Restart Device' is executed. [Parameter: 0x2022_035]"],
        "copySyslogCmd" : ["Device command: 'Copy SysLog data' is executed. [Parameter: 0x2022_051]"]
        },
    LOCAL_LOG_1 : {
        "ecat-io-comm" : ["EC-I/O driver - start tracing", "syncOpen: syncMode=3, framegate=1"],
        },
    LOCAL_LOG_2 : {
        },
    AUTH_LOG : {},
    AUTHPRIVILEAGE_LOG : {"agentForwardingDisabled" : ["Agent forwarding disabled."],
                          "authSuccess" : ["Pubkey auth succeeded for 'root'"],
                          "disconnectSSH" : ["Exited normally"],
                          "childConnection" : ["Child connection from"],
                          "sshConnectionSuccess" : ["Agent forwarding disabled.", "Pubkey auth succeeded for 'root'",
                                                    "Exited normally", "Child connection from",
                                                    "X11 forwarding disabled."],
                          "sftpConnectionSuccess" : ["Child connection from", "Port forwarding disabled.",
                                                     "Agent forwarding disabled.", "X11 forwarding disabled.",
                                                     "Pty allocation disabled.", "Pubkey auth succeeded for 'customer'"]
                          },
    USER_LOG : {"deleteFile" : ["{}: DELETE"],
                "changeFileDetails" : ["{}: CLOSE_WRITE"],
                "createFile" : ["{}: CREATE", "{}: CLOSE_WRITE"],
                "deleteDirectory" : ["{}: DELETE_SELF"],
                "createDirectory" : ["{}: CREATE,ISDIR"],
                "changeAccessRights" : ["{}: ATTRIB"],
                "ntpRestart" : ["System time has been changed. Time difference in seconds:",
                                "Start time update via ntp-client", "Time update via ntp-client was successful"],
                "opcConnection" : ["PubSub module is disabled", "GDS Provisioning mode is disabled"],
                "maxLogs" : ["Emergency log message transmitted", "WARNING log message transmitted",
                             "INFORMATION log message transmitted", "NOTICE log message transmitted",
                             "DEBUG log message transmitted", "ALERT log message transmitted",
                             "CRITICAL log message transmitted", "ERROR log message transmitted"],
                "emergencyLogs" : ["Emergency log message transmitted"],
                "warningLogs" : ["WARNING log message transmitted"],
                "infoLogs" : ["INFORMATION log message transmitted"],
                "noticeLogs" : ["NOTICE log message transmitted"],
                "debugLogs" : ["DEBUG log message transmitted"],
                "alertLogs" : ["ALERT log message transmitted"],
                "criticalLogs" : ["CRITICAL log message transmitted"],
                "errorLogs" : ["ERROR log message transmitted"],
                "visiwinConnect" : ["VisiWin7.Server.Manager: AuthClass Auth.CheckAuthToken: OK",
                                    "VisiWin7.Server.Manager: Initialize: OK",
                                    "VisiWin7.Server.Manager: GetKeys: OK value="]
                },
    DAEMON_LOG : {"opcConnection" : ["opc_ua_server_infra ", "Server is up and running.",
                                     r"Listening on opc\.tcp:\/\/([a-zA-Z0-9\-]+:[0-9]+)",
                                     "Listening on opc.tcp://127.0.0.1:4855"],
                  "cronyStartStopRestart" : ["Stopped chrony, an NTP client/server",
                                             "chronyd exiting",
                                             "Starting chrony, an NTP client/server",
                                             "chronyd version 4.0 starting",
                                             "Initial frequency",
                                             "Loaded seccomp filter",
                                             "Started chrony, an NTP client/server"],
                  "ntpRestart" : ["OPC UA Server initialized",
                                  "[OpcUaServer::Initialize] opc_ua_server_infra",
                                  "[OpcUaServer::LoadPlugin]",
                                  "[OpcUaServer::Run] Server is up and running.",
                                  "[OpcUaServer::Run] Listening on opc.tcp://127.0.0.1:4855"],
                  "c5xxUnmountSDCard" : [
                      "Unmounting /sdcard...", "umount: /sdcard: target is busy.",
                      "sdcard.mount: Mount process exited, code=exited, status=32/n/a",
                      "Failed unmounting /sdcard.",
                      "sdcard.mount: Unit is bound to inactive unit dev-mmcblk0p1.device. Stopping, too."],
                  "c4xxUnmountSDCard" : ["umount: /sdcard: target is busy."],
                  "c5xxMountSDCard" : ["Starting check and mount device mmcblk0p1...",
                                       "check-and-mount@mmcblk0p1.service: Succeeded.",
                                       "Finished check and mount device mmcblk0p1."],
                  "c4xxMountSDCard" : [
                      "mmc0:0001: /usr/lib/udev/rules.d/11-sd-cards-auto-mount.rules:2 Failed to write"],
                  "firmwwareUpgrade" : [r"^Extracting /media/update_data/.+_v_\d+\.\d+\.\d+\.\d+_firmware\.tar to /tmp/tmp\.firmware/firmware/in$"],
                  "visiwinConnect" : ["Connecting to Server Manager..",
                                      "Connected to Server Manager"],
                  },
    KERN_LOG : {"c5xxMountSDCard" : [r"mmc0: new high speed SD card at address \(\d+\)",
                                     r"mmcblk0: mmc0:\(\d+\) DDINC \(\d+\) MiB",
                                     "mmcblk0: p1",
                                     "debugfs: Directory 'mmcblk0' with parent 'block' already present!",
                                     r"FAT-fs \(mmcblk0p1\): Directory bread\(block (\d+)\)"],
                "c4xxMountSDCard" : [r"mmc0: new high speed SD card at address \(\d+\)",
                                     r"mmcblk0: mmc0:\(\d+\) L1BN1 \(\d+\) MiB",
                                     "mmcblk0: p1",
                                     "debugfs: Directory 'mmcblk0' with parent 'block' already present!",
                                     r"FAT-fs \(mmcblk0p1\): Directory bread\(block \(\d+\)\) failed"],
                "c5xxUnmountSDCard" : [r"mmc0: card \w+ removed"],
                "c4xxUnmountSDCard" : [r"mmc0: card \w+ removed"]},
    SERVER_LOG : {"startLogging" : ["Starting System Logging Service..."],
                  "restartSyslogging" : ["calling systemctl restart  rsyslog.service"],
                  "keyNotAccessible" : ["defaultnetstreamdriverkeyfile '/data_usr/syslog_proxy/syslog_proxy_key.pem' could not be accessed"]}
    }

#---------------------------------------------------CONTROLLERS PARAMETERS----------------------------------------------
PARAM_DICT = {"SYSLOG_PARAMETER" : ["0x5914:1", '1'], "MOUBT_USB" : ["0x5902:1", '1'] ,
              "BACKUP_PROJECT" : ["0x2022:40", '1', '0'], "RESTORE_PROJECT" : ["0x2022:43", '1', '0'],
              "CURRENT_TIME" : ["0x245C:2", ''], "LOCAL_TIME" : ["0x245C:1", '194', '203'],
              "RESTART_CONTROLLER" : ["0x2022:035" , "1"], "LOAD_LENZE_SETTINGS" : ["0x2022:001", '1'],
              "DELETE_LOGBOOK" : ["0x2022:015", '1'], "ACTIVATE_APPLICATION" : ["0x2022:038", '1'],
              "LOAD_TA_DEFAULT" : ["0x2022:038", '1'], "START_APPLICATION" : ["0x2022:044", '1'],
              "STOP_APPLICATION" : ["0x2022:045", '1'], "RELOAD_BOOTPROJECT" : ["0x2022:046", '1'],
              "START_UPGRADE" : ["0x2022:047", '1'], "RESET_COLD" : ["0x2022:048", '1'],
              "RESET_ORIGIN" : ["0x2022:049", '1'], "SYSTEM_TIME_CURRENT" : ["0x245B:2", '']}

NTP_PARAMS = {"TIME_BASE_SERVER_MANUALLY" : ["0x245B:1", '2'], "TIME_BASE_SERVER_NTP" : ["0x245B:1", '0'],
              "NTP_SERVER" : ["0x245B:3" , '1'], "NTP_CLIENT" : ["0x245A:2" , ''],
              "TIME_BASE_CLIENT" : ["0x245B:1" , '0']}

SYSLOG_PARAMS = {"ACTIVATION" : ["0x5914:1", '1'], "SERVER_IP" : ["0x5914:2", ''], "PORT" : ["0x5914:3", ''],
                 "PROTOCOL" : ["0x5914:4", ''], "ENCRYPTION" : ["0x5914:5", '']}

PARAM_LIST = ["RESET_ORIGIN", "RESET_COLD", "START_UPGRADE", "RELOAD_BOOTPROJECT", "STOP_APPLICATION",
              "START_APPLICATION", "LOAD_TA_DEFAULT", "ACTIVATE_APPLICATION", "DELETE_LOGBOOK", "LOAD_LENZE_SETTINGS"]

BACKUP_RESTORE_PROJECT_CORRECT_STATES = [1, 2, 20, 40, 60, 80, 100, 110]
BACKUP_RESTORE_COMPLETE_STATE = 110

#-----------------------------------------------Directory Management----------------------------------------------------
IP_TXT_CONTENT = "{}\n255.255.255.0\n10.255.184.1"
FILES_TO_DELETE = ["/ip_old.txt", "/ip.txt"]
FIRMWARE_FILES_LOCATION = r"/sdcard/firmware"
INTERNAL_FIRMWARE_LOCATION = r"/sdcard/firmware"
USERDATABASE_CSV_PATH = r"/plc/prg/pta1/.UserDatabase.csv"
FILES_DIRECTORY = {
    "sdcard": [
        "/slow_data/data_usr/plc/SysFileMap.cfg",
        "/slow_data/data_usr/plc/prg/pta1/.UserDatabase.csv",
        "/slow_data/data_usr/plc/prg/pta1/.GroupDatabase.csv",
        "/slow_data/data_usr/plc/prg/pta1/.UserMgmtRightsDB.lcsv",
        "/slow_data/data_usr/plc/prg/pta1/.UserMgmtExt.csv",
        "/slow_data/data_usr/plc/prg/pta1/.PswDB.csv",
        "/slow_data/data_usr/plc/prg/pta1/Application.app",
        "/slow_data/data_usr/plc/prg/pta1/Application.crc",
        "/slow_data/data_usr/plc/prg/pta1/ecat_master_0.xml",
        "/slow_data/data_usr/plc/prg/pta1/ecat_master_0_boot.xml",
        "/slow_data/data_usr/plc/prg/pta1/ParameterSets/ParSetConfig.cprm",
        "/sdcard/.enable-ssh",
        "/sdcard/ip.txt",
        "/sdcard/update.fw",
        "/sdcard/Licenses_do_not_delete/LicenseFile.lic",
        "/sdcard/Licenses_do_not_delete/VerificationFile.lic",
        "/slow_data/data_usr/plc/CODESYSControl_User.cfg",
        "/slow_data/data_usr/plc/CODESYSControl_UserSec.cfg"
    ],
    "data_usr": [
        "slow_data/data_usr/LicenseFile.lic",
        "slow_data/data_usr/dhcpcd.conf",
        "slow_data/data_usr/dhcpcd.conf.md5sum"
    ],
    "easyui": [
        "/sdcard/easyui/data/ProjectRegistration.xaml",
        r"\/slow_data/data_usr\/easyui\/ServerProjects\/([^\/]+)\/([^\/]+)\.0\.0\.lic",
        "/slow_data/data_usr/easyui/ServerProjects/InternalFallbackTest_Server/InternalFallbackTest_Server.vw7",
        "/slow_data/data_usr/easyui/ServerProjects/InternalFallbackTest_Server/Data/UserManagerRuntimeConfig.urc",
        "/slow_data/data_usr/easyui/ServerProjects/InternalFallbackTest_Server/Data/InternalFallbackTest.rtvw7",
        "/slow_data/data_usr/easyui/ClientProjects/InternalFallbackTest_Client/InternalFallbackTest_Client.vw7",
        "/slow_data/data_usr/easyui/ClientProjects/InternalFallbackTest_Client/index.html",
        "/slow_data/data_usr/easyui/ClientProjects/InternalFallbackTest_Client/service-worker.js",
        "/slow_data/data_usr/easyui/ClientProjects/InternalFallbackTest_Client/manifest.json",
        "/slow_data/data_usr/easyui/ClientProjects/InternalFallbackTest_Client/tsconfig.json",
        "/slow_data/data_usr/easyui/ClientProjects/InternalFallbackTest_Client/web.Release.config",
        "/slow_data/data_usr/easyui/ClientProjects/InternalFallbackTest_Client/web.Debug.config",
        "/slow_data/data_usr/easyui/ClientProjects/InternalFallbackTest_Client/web.config",
        "/slow_data/data_usr/easyui/ClientProjects/InternalFallbackTest_Client/usercontrols",
        "/slow_data/data_usr/easyui/ClientProjects/InternalFallbackTest_Client/actions",
        "/slow_data/data_usr/easyui/ClientProjects/InternalFallbackTest_Client/views",
        "/slow_data/data_usr/easyui/ClientProjects/InternalFallbackTest_Client/pages",
        "/slow_data/data_usr/easyui/ClientProjects/InternalFallbackTest_Client/libs",
        "/slow_data/data_usr/easyui/ClientProjects/InternalFallbackTest_Client/services",
        "/slow_data/data_usr/easyui/ClientProjects/InternalFallbackTest_Client/resources",
        "/slow_data/data_usr/easyui/ClientProjects/InternalFallbackTest_Client/properties",
        "/slow_data/data_usr/easyui/ClientProjects/InternalFallbackTest_Client/images",
        "/slow_data/data_usr/easyui/ClientProjects/InternalFallbackTest_Client/dialogs",
        "/slow_data/data_usr/easyui/ClientProjects/InternalFallbackTest_Client/converters",
        "/slow_data/data_usr/easyui/ClientProjects/InternalFallbackTest_Client/appsettings"
    ]
}

#---------------------------------------------------COMMANDS------------------------------------------------------------
FACTORY_RESET_COMMAND = "sysupgrade.sh --factory-install /sdcard/{}"

#--------------------------------------------------TLS------------------------------------------------------------------
SERVER_IP = "10.255.184.109"
SERVER_HOMEPATH = r"/home/smart"
PORT = {"UDP" : '514', "TCP" : '1514', "TCP_TLS" : '2514'}
SERVER_CREDENTIALS = {"username" : "smart", "password" : "123"}
PROTOCOL = {"UDP" : '0', "TCP" : '1', "TCP_TLS" : '1'}
SERVER_ENCRYPTION = {"NOT_ENCRYPTED" : '0', "ENCRYPTED" : '1'}
SERVER_LOGPATH = r"/log_data/ log/{}.log"
PROTOCOL_TYPES = ["UDP", "TCP", "TCP_TLS"]
ACCESS_TO_LOG = 'echo "123" | sudo -S chown -R smart /log_data/ log'
SEVERITIES_VALUES = {'emerg' : "1", "alert" : "2", "crit" : "4", "err" : "8",
                     "warning" : "16", "notice" : "32", "info" : "64", "debug" : "128"}
SEVERITIES_MESSAGE_KEYS = {'emerg' : "emergencyLogs", "alert" : "alertLogs",
                           "crit" : "criticalLogs", "err" : "errorLogs", "warning" : "warningLogs",
                           "notice" : "noticeLogs", "info" : "infoLogs", "debug" : "debugLogs"}
TYPE_CERTIFICATE = ['Own Certificates', 'Device']
CERT_NAME = 'Lenze Syslog Proxy'
CERT_NAME_DELETED = 'Lenze Syslog Proxy (not available)'
CERT_VALIDITY = 365
CERT_KEY_LENGTH = '3072'
RETRY_TIMER = 300
