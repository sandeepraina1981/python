# -*- coding: utf-8 -*-
#
# © 2007-2008 Lenze Drive Systems GmbH. All rights reserved.
# © 2008-2021 Lenze Automation GmbH. All rights reserved.
#
#-----------------------------------------------------------------------------------------------------------------------
# PyTeF file header (for PyTeF Internal Code) V1.4-01
#-----------------------------------------------------------------------------------------------------------------------
# Disable linter warnings -> ONLY for PyTeF internal code!
#
#-----------------------------------------------------------------------------------------------------------------------
# PyTeF Internal Code docstring (must be first definition in file)
#-----------------------------------------------------------------------------------------------------------------------
"""This file is derived from testlibs PLC and will hold features/specific to Offline User Management
"""
#-----------------------------------------------------------------------------------------------------------------------
# PyTeF Internal Code imports (must be defined before code)
#-----------------------------------------------------------------------------------------------------------------------
import os
import time
import random
import xml.etree.ElementTree as ET
from tests.testlib.lib_pywinauto.plcd.PLC import PLC
from tests.testlib.utils.CommonLib import userSleep, getDecodedPassword, takeScreenshot, clsLogger
from tests.cysec.cysec_testsuites.offline_user_management.utils import constants_offline_usermanagement
from tests.testlib.interface.patterns.Singleton import Singleton
#-----------------------------------------------------------------------------------------------------------------------
# SVN keyword section
#-----------------------------------------------------------------------------------------------------------------------
FILE_URL = "$HeadURL: $"[10:-2]
FILE_REV = "$Revision: 9179 $"[11:-2]
FILE_DATE = "$LastChangedDate: 2022-06-24 12:40:36 +0530 (Fri, 24 Jun 2022) $"[18:-2]
FILE_AUTHOR = "$LastChangedBy: patole@lenze.com $"[16:-2]

#-----------------------------------------------------------------------------------------------------------------------
# PyTeF file header end
#-----------------------------------------------------------------------------------------------------------------------
class UserManagement_PLC(PLC, metaclass=Singleton):
    '''
    Class for offline user management tests for PLCD
    '''
    prefixCls = 'UserManagement_PLC'

    #-------------------------------------------------------------------------------------------------------------------
    def __init__(self, logger):
        '''
            Constructor
        '''
        super().__init__(logger)
        self.currentTestObj = None

    #-------------------------------------------------------------------------------------------------------------------
    def _openUsersAndGroupSettings(self, projName):
        '''
        This method is used to open Users and Groups Settings
        1. Open project settings by typing keys ALT + P + R
        2. On Project Settings window, select Users and Groups from listview

              .. image:: images/selectUsersAndGroups.png

        '''
        try:
            # Open Project Settings
            self.logger.info(f"[{type(self).prefixCls}] Opening project settings..")
            mainWin = self.getMainWindow(header = projName)
            mainWin.wait('ready')
            mainWin.type_keys("% P J", pause = 0.3)

            # Select Users and Groups from list view on Project Settings window
            projSettingsWin = self.app.window(title_re = constants_offline_usermanagement.PROJECT_SETTINGS_WIN_TITLE)
            projSettingsWin.wait('ready', timeout = 10)
            self.logger.info(f"[{type(self).prefixCls}] Project Settings window opened..")
            self.logger.info(f"[{type(self).prefixCls}] Selecting 'Users and Groups' tab from List view")
            handle = self.getWpfAppHandle()
            projSettingLeftView = handle.child_window(auto_id = "_categoryList")
            self.logger.info(
                f"[{type(self).prefixCls}] Searching for 'Users and Groups' tab on Project settings window")
            for tab in projSettingLeftView.children():
                if tab.legacy_properties()['Name'].strip() == "Users and Groups":
                    self.logger.info(
                        f"[{type(self).prefixCls}] Clicking on 'Users and Groups' tab on Project settings window")
                    tab.set_focus()
                    tab.click_input()
                    self.logger.info(f"[{type(self).prefixCls}] 'Users and Groups' tab selected")
                    return True

            self.logger.error(f"[{type(self).prefixCls}] 'Users and Groups' tab not found on 'Project settings' window")
            return False
        except Exception:
            self.logger.exception(f"[{type(self).prefixCls}] Exception occurred in _openUsersAndGroupSettings() ")
            return False

    #-------------------------------------------------------------------------------------------------------------------
    def createGroup(self, groupName, projName):
        '''
        This method is used to create new Group for offline user management
        1. Open Users and Groups Settings
        2. Go to Groups tab and click Add button

              .. image:: images/groupsTabAddButton.png

        3. Enter group name in Add Group window

              .. image:: images/enterGroupName.png

        4. CLick OK button and check if no error popup appears
        '''
        try:
            # Open Users and Groups Settings
            usersAndGrpsSettingOpenStatus = self._openUsersAndGroupSettings(projName = projName)
            if not usersAndGrpsSettingOpenStatus:
                self.logger.error(f"[{type(self).prefixCls}] Users and Groups Settings is not open")
                return False

            # Select Groups tab
            projSettingsWin = self.app.window(title_re = constants_offline_usermanagement.PROJECT_SETTINGS_WIN_TITLE)
            projSettingsWin.wait('ready')
            projSettingsWin.set_focus()
            self.logger.info(f"[{type(self).prefixCls}] Selecting Groups tab")
            tabControl = projSettingsWin.TabControl
            tabControl.wait('ready')
            tabControl.select('Groups')
            self.logger.info(f"[{type(self).prefixCls}] 'Groups' tab selected")

            # Click add button
            self.logger.info(f"[{type(self).prefixCls}] Clicking on 'Add' Button")
            addButton = projSettingsWin['&Add...']
            addButton.wait('enabled', timeout = 5)
            addButton.set_focus()
            addButton.click_input()
            self.logger.info(f"[{type(self).prefixCls}] 'Add' Button clicked")

            # Enter group name in Add Group window
            addGroupWin = self.app['Add Group']
            addGroupWin.wait('ready')
            addGroupWin.set_focus()
            self.logger.info(f"[{type(self).prefixCls}] Add Group Window opened..")
            groupNameEditBox = addGroupWin.Edit2
            self.logger.info(f"[{type(self).prefixCls}] Entering {groupName} in group name edit box")
            groupNameEditBox.set_edit_text(groupName)

            # Click Ok button on Add Group window
            self.logger.info(f"[{type(self).prefixCls}] Clicking Ok Button on 'Add Group' window")
            okButton = addGroupWin.OK
            okButton.wait('enabled', timeout = 5)
            okButton.click_input()
            self.logger.info(f"[{type(self).prefixCls}] Ok Button Clicked")

            # Click Ok button on Project settings window
            self.logger.info(f"[{type(self).prefixCls}] Clicking Ok Button on Project Settings window")
            okButton = projSettingsWin.OK
            okButton.wait('enabled', timeout = 5)
            okButton.set_focus()
            okButton.click_input()
            self.logger.info(f"[{type(self).prefixCls}] OK Button Clicked")

            # Check if no error pop up appears
            popUp = self.app.Dialog
            if popUp.exists(timeout = 2):
                # If error popup appears, close pop up, Add Group window and Project Settings window
                self.logger.error(f"[{type(self).prefixCls}] Error popup with message : "
                                  f"{popUp.Static2.texts()[0]} appeared")

                self.logger.error(f"[{type(self).prefixCls}] Failed to create Group...")
                self.logger.info(f"[{type(self).prefixCls}] Closing error pop-up and Project Settings window")
                popUp.close()
                addGroupWin.close()
                projSettingsWin.close()
                return False
            return True
        except Exception:
            self.logger.exception(f"[{type(self).prefixCls}] Exception occurred in createGroup() ")
            return False

    #-------------------------------------------------------------------------------------------------------------------
    def openLoginWindow(self, projName):
        '''
        This method is used to open login window by typing keys ALT + P + U + U
        '''
        try:
            self.logger.info(f"[{type(self).prefixCls}] Opening login window")
            if not self.app['Log In'].exists(timeout = 15):
                mainWin = self.getMainWindow(header = projName)
                mainWin.wait('ready', timeout = 15)
                mainWin.set_focus()

                mainWin.type_keys("% P U U", pause = 0.3)

            loginWin = self.app['Log In']
            loginWin.wait('ready', timeout = 15)
            loginWin.set_focus()
            self.logger.info(f"[{type(self).prefixCls}] Login window opened")
            return loginWin
        except Exception:
            self.logger.exception(f"[{type(self).prefixCls}] Exception occurred in openLoginWindow() ")
            return None

    #-------------------------------------------------------------------------------------------------------------------
    def enterLoginCredentials(self, userName, base64Password = None):
        '''
        This method is used to enter username, password and click ok on login window

              .. image:: images/enterLoginCredentials.png
        '''
        try:
            # Enter username
            loginWin = self.app['Log In']
            loginWin.wait("ready", timeout = 15)

            userNameEditBox = loginWin.child_window(auto_id = "_userNameTextBox")
            userNameEditBox.wait("exists visible", timeout = 5)
            self.logger.info(f"[{type(self).prefixCls}] Entering username : {userName}")
            userNameEditBox.set_edit_text(userName)

            # Enter password
            if base64Password:
                self.logger.info(f"[{type(self).prefixCls}] Entering password")
                pwd = getDecodedPassword(logger = self.logger,
                                         base64EncryptedPassword = base64Password)
                pwdEditBox = loginWin.child_window(auto_id = "_passwordTextBox")
                pwdEditBox.wait("exists visible", timeout = 5)
                pwdEditBox.set_edit_text(pwd)

            # Click OK button
            self.logger.info(f"[{type(self).prefixCls}] Clicking Ok button")
            okButton = loginWin.OK
            okButton.wait('enabled', timeout = 5)
            okButton.set_focus()
            time.sleep(1)
            okButton.click_input()
            self.logger.info(f"[{type(self).prefixCls}] Ok button clicked")
            return True
        except Exception:
            self.logger.exception(f"[{type(self).prefixCls}] Exception occurred in enterLoginCredentials() ")
            return False

    #-------------------------------------------------------------------------------------------------------------------
    def loginUser(self, projName, userName, base64Password = None):
        '''
        This method is used to login user for offline user management
        '''
        try:
            # Open Login window
            loginWin = self.openLoginWindow(projName = projName)

            # Enter login credentials
            self.enterLoginCredentials(userName, base64Password)

            # Check if not error popup appears
            popUp = self.app.Dialog
            if popUp.exists(timeout = 5):
                self.logger.error(f"[{type(self).prefixCls}] Error popup with message : "
                                  f"{popUp.Static2.texts()[0]} appeared")

                self.logger.error(f"[{type(self).prefixCls}] Failed to Login...")
                popUp.close()
                loginWin.close()
                return False

            self.logger.info(f"[{type(self).prefixCls}] {userName} logged in successfully")
            return True
        except Exception:
            self.logger.exception(f"[{type(self).prefixCls}] Exception occurred in loginUser() ")
            return False

    #-------------------------------------------------------------------------------------------------------------------
    def createUser(self, projName, userName, password, memberShipList):
        '''
        This method is used to create new user for offline user management
        1. Open Users and Groups Settings
        2. Go to Users tab and click add button

              .. image:: images/selectUsersTab.png

        3. Enter username, password and confirm password on Add User window

              .. image:: images/enterAddUserDetails.png

        4. Select required membership and click Ok button on Add User window

              .. image:: images/selectMembership.png
        '''
        try:
            # Open Users and Groups Settings
            usersAndGrpsSettingOpenStatus = self._openUsersAndGroupSettings(projName = projName)
            if not usersAndGrpsSettingOpenStatus:
                self.logger.error(f"[{type(self).prefixCls}] Users and Groups Settings is not open")
                return False

            # Select Users tab
            projSettingsWin = self.app.window(title_re = constants_offline_usermanagement.PROJECT_SETTINGS_WIN_TITLE)
            self.logger.info(f"[{type(self).prefixCls}] Selecting Users tab")
            tabControl = projSettingsWin.TabControl
            tabControl.select('Users')

            # Click Add button
            self.logger.info(f"[{type(self).prefixCls}] Clicking on 'Add' Button")
            addButton = projSettingsWin['&Add...']
            addButton.wait('enabled', timeout = 5)
            addButton.set_focus()
            addButton.click_input()

            # Enter user name
            addUserWin = self.app['Add User']
            addUserWin.wait('ready')
            self.logger.info(f"[{type(self).prefixCls}] Add User Window opened..")
            loginNameEditBox = addUserWin.Edit6
            self.logger.info(f"[{type(self).prefixCls}] Entering {userName} in login name edit box")
            loginNameEditBox.set_edit_text(userName)

            # Enter password and confirm password
            self.logger.info(f"[{type(self).prefixCls}] Entering password")
            pwd = getDecodedPassword(logger = self.logger,
                                     base64EncryptedPassword = password)
            pwdEditBox = addUserWin.Edit3
            pwdEditBox.set_edit_text(pwd)
            confirmPwdEditBox = addUserWin.Edit2
            confirmPwdEditBox.set_edit_text(pwd)

            # Select required memberships
            wpfApp = self.connectToPLCWPFWindow()
            wind = wpfApp.windows()
            title = wind[0].get_properties()['texts'][0]
            handle = wpfApp.window(title = title)

            child = handle.child_window(auto_id = "_groupsListBox")
            groupsListBox = child.wrapper_object()
            for group in memberShipList:
                groupFoundFlag = False
                for grp in groupsListBox.children():
                    if grp.legacy_properties()['Name'] == group:
                        self.logger.info(f"[{type(self).prefixCls}] Checking {group} group in membership list")
                        groupFoundFlag = True
                        grp.double_click_input()
                if not groupFoundFlag:
                    self.logger.error(f"[{type(self).prefixCls}] Could not find {group} in membership list... "
                                      "cannot add it's membership")

                    addUserWin.type_keys("{ESC}")
                    projSettingsWin.type_keys("{ESC}")
                    return False

            # Click OK button on Add User window
            self.logger.info(f"[{type(self).prefixCls}] Clicking on Ok Button on Add User window")
            okButton = addUserWin.OK
            okButton.wait('enabled', timeout = 5)
            okButton.click_input()
            self.logger.info(f"[{type(self).prefixCls}] Ok Button Clicked")

            # Click Ok button on Project Settings window
            self.logger.info(f"[{type(self).prefixCls}] Clicking on Ok Button on Project Setting window")
            okButton = projSettingsWin.OK
            okButton.wait('enabled', timeout = 5)
            okButton.click_input()
            self.logger.info(f"[{type(self).prefixCls}] Ok Button Clicked")

            # Check if not error popup appears
            popUp = self.app.Dialog
            if popUp.exists(timeout = 2):
                # If error popup appears, close pop up, Add User window and project settings window
                self.logger.error(f"[{type(self).prefixCls}] Error popup with message : "
                                  f"{popUp.Static2.texts()[0]} appeared")

                self.logger.error(f"[{type(self).prefixCls}] Failed to create User...")
                popUp.close()
                addUserWin.close()
                projSettingsWin.close()
                return False
            return True
        except Exception:
            self.logger.exception(f"[{type(self).prefixCls}] Exception occurred in createUser() ")
            return False

    #-------------------------------------------------------------------------------------------------------------------
    def expandAndReturnChildrenListOfElementInDevices(self, projName, elementName):
        '''
        This method is used to expand an element in Devices window and
        return the list of names of its children elements if exists
        '''
        try:
            childrenNameList = []
            self.getDevicesWindow(header = projName).type_keys("{HOME}")
            self.logger.info(f"[{type(self).prefixCls}] Searching for {elementName} in devices window")
            element = self.getObjFromDevicesWindowWpf(objectName = elementName)
            if element:
                self.logger.info(f"[{type(self).prefixCls}] Element {elementName} found in devices window... "
                                 "clicking on it")
                elementNameInDevices = element.legacy_properties()['Name'].strip()
                # element.click_input()
                element.invoke()
                element.select()
            else:
                self.logger.error(f"[{type(self).prefixCls}] Element {elementName} not found in Devices window")
                return None

            handle = self.getWpfAppHandle()
            for win in handle.children():
                if "Devices" in win.children()[0].legacy_properties()['Name']:
                    topDev = win.children()[0]
                    break
            else:
                self.logger.error(f"[{type(self).prefixCls}] Failed to get Devices pane")
                return None

            dev = [win for win in topDev.children() if win.automation_id() == "Devices"][0]
            tree = [win for win in dev.children() if win.automation_id() == "_treeTableView"][0]
            listNode = tree.children()[0]

            dev.type_keys("{LEFT}")
            elementsCountWhenCollapsed = len(listNode.children())

            dev.type_keys("{RIGHT}")
            elementsCountWhenExpanded = len(listNode.children())

            devicesList = [node.legacy_properties()[
                'Name'].strip() for node in listNode.children() if node.legacy_properties()['Name']]

            dev.type_keys("{LEFT}")

            childCount = elementsCountWhenExpanded - elementsCountWhenCollapsed
            self.logger.info(f"[{type(self).prefixCls}] Total children founds: {childCount}")

            elementIndex = devicesList.index(elementNameInDevices)

            for childNumber in range(elementIndex, len(devicesList)):
                self.logger.info(f"[{type(self).prefixCls}] {childNumber}:{devicesList[childNumber]}")
                childrenNameList.append(devicesList[childNumber])

            return childrenNameList
        except Exception:
            self.logger.exception(f"[{type(self).prefixCls}] Exception occurred in "
                                  "expandAndReturnChildrenListOfElementInDevices() ")
            return False

    #-------------------------------------------------------------------------------------------------------------------
    def _openPermissionsWindow(self, projName):
        '''
        This method is used to open Permissions Window by typing keys : ALT + P + U + P
        '''
        try:
            self.logger.info(f"[{type(self).prefixCls}] Opening 'Permissions' window")
            mainWin = self.getMainWindow(header = projName)
            mainWin.type_keys("% P U P", pause = 0.3)
            # self.selectMenuItem(itemPathList = ["Project","User Management","Permissions..."], projName = projName)
            permissionsWin = self.app.Permissions
            permissionsWin.wait('ready', timeout = 10)
            self.logger.info(f"[{type(self).prefixCls}] Permissions window opened..")
            return permissionsWin
        except Exception:
            self.logger.exception(f"[{type(self).prefixCls}] Exception occurred in _openPermissionsWindow() ")
            return None

    #-------------------------------------------------------------------------------------------------------------------
    def _goToCommandInPermissionsWindow(self, permissionPath):
        '''
        This method is used to select and get required command from permissions window tree view
        :param permissionPath: Path of the command in the tree view
        '''
        try:
            permWin = self.app.window(title_re = "Permissions")
            permWin.wait('ready')
            permWin.set_focus()
            permWin.ListView.click_input()
            wpfApp = self.connectToPLCWPFWindow()
            wind = wpfApp.windows()
            title = wind[0].get_properties()['texts'][0]
            handle = wpfApp.window(title = title)
            child = handle.child_window(auto_id = "_actionsTreeTableView")
            treeView = child.wrapper_object()
            for node in permissionPath:
                self.logger.info(f"[{type(self).prefixCls}] Selecting and expanding {node} in from treeview")
                for element in treeView.children():
                    if node == element.legacy_properties()['Name']:
                        element.click_input()
                        permWin.type_keys("{RIGHT}")
                        userSleep(0.5)
                        treeView = element
            return treeView
        except Exception:
            self.logger.exception(f"[{type(self).prefixCls}] Exception occurred in _goToCommandInPermissionsWindow() ")
            return None

    #-------------------------------------------------------------------------------------------------------------------
    def _selectObjectInPermissionTreeView(self, node, objectName):
        '''
        This method is used to recursively search and select required object from the tree view
        :param node: Parent node object
        :param objectName: Name of the object to select
        '''
        try:
            permWin  = self.app.window(title_re = "Permissions")
            if node.legacy_properties()['Name'] == objectName:
                node.click_input()
                return node
            permWin.type_keys("{DOWN} {RIGHT}")
            if node.children():
                for child in node.children():
                    res = self._selectObjectInPermissionTreeView(child, objectName)
                    if res:
                        return res
            return None
        except Exception:
            self.logger.exception(
                f"[{type(self).prefixCls}] Exception occurred in _selectObjectInPermissionTreeView()")
            return None

    #-------------------------------------------------------------------------------------------------------------------
    def _checkIfPermissionsSetProperly(self, permissionPath, groupPermissionsDict):
        '''
        This method is uses exported permissions xml file to verify if required permissions are set correctly
        :param permissionPath: Path of the object in permissions tree view
        :param groupPermissionDict: Dictionary which contains required permissions for groups
        '''
        try:
            # Export Permissions XML file
            permWin = self.app.Permissions
            self.logger.info(f"[{type(self).prefixCls}] Clicking on 'Export Permissions' button")
            exportPermButton = permWin.Button
            exportPermButton.set_focus()
            exportPermButton.click()

            self.logger.info(f"[{type(self).prefixCls}] Selecting 'Export selected permissions'...")
            self.app.top_window().type_keys("{DOWN 2} {ENTER}")

            saveWin = self.app.window(title_re = 'Export Permissions')
            if saveWin.exists(timeout = 10, retry_interval=0.1):
                xmlFilePath = os.getcwd() + constants_offline_usermanagement.EXPORTED_PERMISSIONS_XML_FILE_PATH
                self.logger.info(f"[{type(self).prefixCls}] Entering export permissions file path :{xmlFilePath}")
                saveWin.Edit.set_edit_text(xmlFilePath)
                saveWin.type_keys("{ENTER}")
            else:
                self.logger.error(f"[{type(self).prefixCls}] Timeout: Export permissions window did not open")

            self.logger.info(f"[{type(self).prefixCls}] Clicking 'Yes' on Confirm Save As window")
            confirmRep = self.app.window(title_re = 'Confirm Save As')
            if confirmRep.exists(timeout = 3):
                self.logger.info(f"[{type(self).prefixCls}] Confirm Save As popup appeared... Clicking 'Yes'..")
                confirmRep['&Yes'].click_input()
                confirmRep.wait_not(wait_for_not = 'exists', timeout = 3, retry_interval = 0.1)

            time.sleep(2)
            if self.app.Dialog.exists(timeout = 10):
                self.app.Dialog.OK.click_input()
                self.app.Dialog.wait_not(wait_for_not = 'exists', timeout = 3, retry_interval = 0.1)

            self.logger.info(f"[{type(self).prefixCls}] Closing permissions window")
            permWin.close(wait_time = 5)

            # Get permission data from XML file
            permObj = PermissionXMLParser(constants_offline_usermanagement.EXPORTED_PERMISSIONS_XML_FILE_PATH,
                                          logger = self.logger)
            permData = permObj.permData
            res = True
            # Compare required permission with XML permission data
            for group, permission in list(groupPermissionsDict.items()):
                if permission == 'Clear':
                    if group not in permData.get(permissionPath[0]).get(permissionPath[1]).get('Grant') and \
                     group not in permData.get(permissionPath[0]).get(permissionPath[1]).get('Deny'):
                        self.logger.info(f"[{type(self).prefixCls}] Permission for {group} is set properly...")
                    else:
                        self.logger.info(f"[{type(self).prefixCls}] Permission for {group} not set properly")
                        res = False
                        break
                else:
                    if group in permData.get(permissionPath[0]).get(permissionPath[1]).get(permission):
                        self.logger.info(f"[{type(self).prefixCls}] Permission for {group} is set properly...")
                    else:
                        self.logger.info(f"[{type(self).prefixCls}] Permission for {group} not set properly")
                        res = False
                        break
            return res
        except Exception:
            self.logger.exception(f"[{type(self).prefixCls}] Exception occurred in _checkIfPermissionsSetProperly() ")
            takeScreenshot()
            return False

    #-------------------------------------------------------------------------------------------------------------------
    def setPermission(self, projName, permissionPath, objectName, groupPermissionsDict):
        '''
        This method is used to set permissions for required object for different groups
        :param permissionPath: Path of the object in permissions tree view
        :param objectName: Name of the object whose permissions are to be set
        :param groupPermissionDict: Dictionary which contains required permissions for groups
        '''
        try:
            # open and get permission window object
            permWin = self._openPermissionsWindow(projName = projName)
            permissionNode = self._goToCommandInPermissionsWindow(permissionPath)
            self._selectObjectInPermissionTreeView(node = permissionNode, objectName = objectName)

            wpfApp = self.connectToPLCWPFWindow()
            wind = wpfApp.windows()
            title = wind[0].get_properties()['texts'][0]
            handle = wpfApp.window(title = title)
            child0 = handle.child_window(auto_id = "toolStrip1")
            permButtons = child0.wrapper_object()

            for group, permission in list(groupPermissionsDict.items()):
                self.logger.info(f"[{type(self).prefixCls}] Selecting {group} group on Permissions window..")
                permWin.ListView2.wait("visible enabled ready", timeout=10)
                grp = permWin.ListView2.get_item(
                    f'{group}                                                                          ')

                grp.click_input()

                self.logger.info(f"[{type(self).prefixCls}] Clicking on '{permission}' permission button")
                userSleep(1)

                for permissionButton in permButtons.children():
                    if permissionButton.legacy_properties()['Name'] == permission:
                        # permissionButton.set_focus()
                        permissionButton.click_input()
                        self.logger.info(f"[{type(self).prefixCls}] Clicked on '{permission}' permission button")

            res = self._checkIfPermissionsSetProperly(permissionPath, groupPermissionsDict)
            return res
        except Exception:
            self.logger.exception(f"[{type(self).prefixCls}] Exception occurred in setPermission() ")
            return False

    #-------------------------------------------------------------------------------------------------------------------
    def _checkIfLoginPopUpAppeared(self):
        '''
        This method is used to check if login popup appears
        '''
        try:
            self.logger.info(f"[{type(self).prefixCls}] Checking if login pop up appeared")
            loginWin = self.app['Log In']
            if loginWin.exists(timeout = 5):
                self.logger.info(f"[{type(self).prefixCls}] Login Pop up appeared")
                loginWin.close()
                if self.app.Dialog.exists():
                    self.app.Dialog.close()
                return True
            self.logger.info(f"[{type(self).prefixCls}] Login Pop up did not appear")
            return False
        except Exception:
            self.logger.exception(f"[{type(self).prefixCls}] Exception occurred in _checkIfLoginPopUpAppeared() ")
            return False

    #-------------------------------------------------------------------------------------------------------------------
    def logoutCurrentUser(self, projName):
        '''
        This method is used to logout current user by typing keys ALT + P + U + L
        '''
        try:
            self.logger.info(f"[{type(self).prefixCls}] Logging out current user")
            mainWin = self.getMainWindow(header = projName)
            mainWin.type_keys("% P U L", pause = 0.3)
            return True
        except Exception:
            self.logger.exception(f"[{type(self).prefixCls}] Exception occurred in logoutCurrentUser() ")
            return False

    #-------------------------------------------------------------------------------------------------------------------
    def checkIfGroupsAreCreated(self, projName, groupNameList):
        '''
        This method is used to check if required groups are created
        1. Open Users and Groups Settings
        2. Go to Groups tab
        3. Check if required groups are present
        :param groupNameList: List of names of required groups
        '''
        try:
            # Open Users and Groups Settings
            usersAndGrpsSettingOpenStatus = self._openUsersAndGroupSettings(projName)
            if not usersAndGrpsSettingOpenStatus:
                self.logger.error(f"[{type(self).prefixCls}] Users and Groups Settings is not open")
                return False

            # Select Groups tab
            projSettingsWin = self.app.window(title_re = constants_offline_usermanagement.PROJECT_SETTINGS_WIN_TITLE)
            projSettingsWin.set_focus()
            self.logger.info(f"[{type(self).prefixCls}] Selecting Groups tab")
            tabControl = projSettingsWin.TabControl
            tabControl.select('Groups')
            self.logger.info(f"[{type(self).prefixCls}] 'Groups' tab selected")

            # Check if required Groups are present
            groupListView = projSettingsWin.ListView
            groupsPresentLi = [grp.strip() for grp in groupListView.texts()]

            for groupName in groupNameList:
                self.logger.info(f"[{type(self).prefixCls}] Checking if group '{groupName}' is created")
                if groupName in groupsPresentLi:
                    self.logger.info(f"[{type(self).prefixCls}] Group '{groupName}' is created..")
                else:
                    self.logger.error(f"[{type(self).prefixCls}] Group '{groupName}' is not created..")
                    return False
            return True
        except Exception:
            self.logger.exception(f"[{type(self).prefixCls}] Exception occurred in checkIfGroupsAreCreated() ")
            return False

        finally:
            if projSettingsWin.exists():
                self.logger.info(f"[{type(self).prefixCls}] Closing 'Project Settings' window")
                projSettingsWin.close()

    #-------------------------------------------------------------------------------------------------------------------
    def checkIfUserIsCreated(self, projName, userName, memberShipList):
        '''
        This method is used to check if required user is created with required membership
        1. Open Users and Groups Settings
        2. Go to Users tab
        3. Check if required user is present with required membership
        :param userName: Name of required user
        :param memberShipList: List of names of required memberships
        '''
        try:
            # Open Users and Groups Settings
            usersAndGrpsSettingOpenStatus = self._openUsersAndGroupSettings(projName = projName)
            if not usersAndGrpsSettingOpenStatus:
                self.logger.error(f"[{type(self).prefixCls}] Users and Groups Settings is not open")
                return False

            # Select Users tab
            projSettingsWin = self.app.window(title_re = constants_offline_usermanagement.PROJECT_SETTINGS_WIN_TITLE)
            projSettingsWin.set_focus()
            self.logger.info(f"[{type(self).prefixCls}] Selecting Groups tab")
            tabControl = projSettingsWin.TabControl
            tabControl.select('Users')
            self.logger.info(f"[{type(self).prefixCls}] 'Users' tab selected")

            wpfApp = self.connectToPLCWPFWindow()
            wind = wpfApp.windows()
            title = wind[0].get_properties()['texts'][0]
            handle = wpfApp.window(title = title)

            child = handle.child_window(auto_id = "_userTreeTableView")
            usersTreeView = child.wrapper_object()
            usersPresent = usersTreeView.children()

            self.logger.info(f"[{type(self).prefixCls}] Checking if user : '{userName}' is created")
            for user in usersPresent:
                # check if user is present
                if userName == user.legacy_properties()['Name']:
                    self.logger.info(f"[{type(self).prefixCls}] User : '{userName}' is created")

                    # expand user and check if required membership is present in expanded list
                    user.expand()
                    memberShipAvailableList = [
                        memberShip.legacy_properties()['Name'].split("'")[1] for memberShip in user.children()]

                    for memberShip in memberShipList:
                        self.logger.info(
                            f"[{type(self).prefixCls}] Checking if {userName} has membership to {memberShip}")

                        if memberShip in memberShipAvailableList:
                            self.logger.info(f"[{type(self).prefixCls}] {userName} has membership to {memberShip}")
                        else:
                            self.logger.error(
                                f"[{type(self).prefixCls}] {userName} does not have membership to {memberShip}")

                            return False
                    return True
            self.logger.error(f"[{type(self).prefixCls}] User : '{userName}' is not created")
            return False
        except Exception:
            self.logger.exception(f"[{type(self).prefixCls}] Exception occurred in checkIfUserIsCreated() ")
            return False
        finally:
            # Close project settings window if open
            if projSettingsWin.exists():
                self.logger.info(f"[{type(self).prefixCls}] Closing 'Project Settings' window")
                projSettingsWin.close()

    #-------------------------------------------------------------------------------------------------------------------
    def setMaxAuthenticationTrials(self, projName, authenticationTrialValue):
        '''
        This method is used to set maximum authentication trial value for plc project
        1. Open Users and Groups settings
        2. Open settings tab
        3. Check "Maximum number of authentication trials" Check box
        4. Enter authentication trial value in "Maximum number of authentication trials " edit box

              .. image:: images/setMaxAuthenticationTrial.png

        :param authenticationTrialValue: Value of Maximum number of authentication trials to be set
        '''
        try:
            # Open Users and Groups Settings
            usersAndGrpsSettingOpenStatus = self._openUsersAndGroupSettings(projName = projName)
            if not usersAndGrpsSettingOpenStatus:
                self.logger.error(f"[{type(self).prefixCls}] Users and Groups Settings is not open")
                return False

            # Select Settings tab
            projSettingsWin = self.app.window(title_re = constants_offline_usermanagement.PROJECT_SETTINGS_WIN_TITLE)
            projSettingsWin.set_focus()
            self.logger.info(f"[{type(self).prefixCls}] Selecting Settings tab")
            tabControl = projSettingsWin.TabControl
            tabControl.select('Settings')
            self.logger.info(f"[{type(self).prefixCls}] 'Settings' tab selected")

            # Check "Maximum number of authentication trials" Check box if it is not already checked
            maxTrialSettingCheckBox = projSettingsWin.CheckBox2
            if not maxTrialSettingCheckBox.get_check_state():
                self.logger.info(
                    f"[{type(self).prefixCls}] Checking 'Maximum number of authentication trials' check box")
                maxTrialSettingCheckBox.click()

            # Enter new Maximum number of authentication trials value
            self.logger.info(f"[{type(self).prefixCls}] Setting Maximum number of authentication trials to "
                             f"{authenticationTrialValue}")

            projSettingsWin.Edit2.set_edit_text(authenticationTrialValue)
            projSettingsWin.type_keys("{ENTER}")
            self.logger.info(f"[{type(self).prefixCls}] Successfully set Maximum number of authentication trials to "
                             f"{authenticationTrialValue}")

            return True
        except Exception:
            self.logger.exception(f"[{type(self).prefixCls}] Exception occurred in setMaxAuthenticationTrials() ")
            if projSettingsWin.exists():
                self.logger.info(f"[{type(self).prefixCls}] Closing Project Settings window")
                projSettingsWin.close()
            return False

    #-------------------------------------------------------------------------------------------------------------------
    def setInactivityLogoutTime(self, projName, inactivityLogoutTimeInMins):
        '''
        This method is used to set automatic inactivity logout time for plc project
        1. Open Users and Groups settings
        2. Open settings tab
        3. Check "Automatically logout after time of inactivity" Check box if not already checked
        4. Enter new value in "Automatically logout after time of inactivity" edit box

              .. image:: images/setInactivityLogoutTime.png

        :param inactivityLogoutTimeInMins: Value of automatic inactivity logout time to be set
        '''
        try:
            # Open Users and Groups Settings
            usersAndGrpsSettingOpenStatus = self._openUsersAndGroupSettings(projName = projName)
            if not usersAndGrpsSettingOpenStatus:
                self.logger.error(f"[{type(self).prefixCls}] Users and Groups Settings is not open")
                return False

            # Select Settings tab
            projSettingsWin = self.app.window(title_re = constants_offline_usermanagement.PROJECT_SETTINGS_WIN_TITLE)
            projSettingsWin.set_focus()
            self.logger.info(f"[{type(self).prefixCls}] Selecting Groups tab")
            tabControl = projSettingsWin.TabControl
            tabControl.select('Settings')
            self.logger.info(f"[{type(self).prefixCls}] 'Settings' tab selected")

            # Check "Automatically logout after time of inactivity." Check box if it is not already checked
            inactivityLogoutTimeCheckBox = projSettingsWin.CheckBox
            if not inactivityLogoutTimeCheckBox.get_check_state():
                self.logger.info(
                    f"[{type(self).prefixCls}] Checking 'Automatically logout after time of inactivity.' check box")

                inactivityLogoutTimeCheckBox.click()

            # Enter new automatic logout time value
            self.logger.info(f"[{type(self).prefixCls}] Setting Inactivity logout time to {inactivityLogoutTimeInMins}")
            projSettingsWin.Edit.set_edit_text(inactivityLogoutTimeInMins)
            projSettingsWin.type_keys("{ENTER}")
            self.logger.info(f"[{type(self).prefixCls}] Successfully set Inactivity logout time to "
                             f"{inactivityLogoutTimeInMins}")

            return True
        except Exception:
            self.logger.exception(f"[{type(self).prefixCls}] Exception occurred in setInactivityLogoutTime() ")
            if projSettingsWin.exists():
                self.logger.info(f"[{type(self).prefixCls}] Closing Project Settings window")
                projSettingsWin.close()
            return False

    #-------------------------------------------------------------------------------------------------------------------
    def setUserToActive(self, projName, userName):
        '''
        This method is used to make required user active
        1. Open Users and Groups Settings
        2. Double click on required user
        3. Check Active User checkbox if not already checked
        :param userName: Name of the user to be set to active
        '''
        try:
            # Open Users and Groups Settings
            usersAndGrpsSettingOpenStatus = self._openUsersAndGroupSettings(projName = projName)
            if not usersAndGrpsSettingOpenStatus:
                self.logger.error(f"[{type(self).prefixCls}] Users and Groups Settings is not open")
                return False

            # Go to users tab
            projSettingsWin = self.app.window(title_re = constants_offline_usermanagement.PROJECT_SETTINGS_WIN_TITLE)
            projSettingsWin.set_focus()
            self.logger.info(f"[{type(self).prefixCls}] Selecting Groups tab")
            tabControl = projSettingsWin.TabControl
            tabControl.select('Users')
            self.logger.info(f"[{type(self).prefixCls}] 'Users' tab selected")

            # Double click on required user to open Edit User window
            self.logger.info(f"[{type(self).prefixCls}] Opening Edit User window for {userName}")
            usersList = projSettingsWin.ListView
            user = usersList.get_item(
                f'{userName}                                                                          ')
            user.click_input(double = True)

            editUserWin = self.app['Edit User']
            editUserWin.wait('ready')
            editUserWin.set_focus()

            # Check Active checkbox if not already checked
            if editUserWin.CheckBox.get_check_state():
                self.logger.info(f"[{type(self).prefixCls}] {userName} is already set as active")
            else:
                editUserWin.CheckBox.click()
                self.logger.info(f"[{type(self).prefixCls}] Successfully set {userName} as active")

            editUserWin.type_keys("{ENTER}")
            projSettingsWin.type_keys("{ENTER}")
            return True
        except Exception:
            self.logger.exception(f"[{type(self).prefixCls}] Exception occurred in setUserToActive() ")
            if projSettingsWin.exists():
                self.logger.info(f"[{type(self).prefixCls}] Closing Project Settings window")
                projSettingsWin.close()
            return False

    #-------------------------------------------------------------------------------------------------------------------
    def checkUserInactiveAfterMaxTrail(self, projName, userName, maxAuthenticationTrailValue):
        '''
        This method is used to verify if user becomes inactive after maximum authentication trials without password
        '''
        try:
            retryLoginCount = 0

            # Opening Login window
            logWin = self.openLoginWindow(projName = projName)

            # Trying to login with wrong password until user is set to inactive
            while logWin.exists(timeout = 2):
                self.logger.info(f"[{type(self).prefixCls}] Trying to login {userName} with wrong credentials")
                self.enterLoginCredentials(userName)
                popUp = self.app.Dialog
                if popUp.exists(timeout = 2):
                    popUpMsg = popUp.Static2.texts()[0]
                    self.logger.error(f"[{type(self).prefixCls}] Failed to Login...")
                    popUp.close()

                    if popUpMsg == constants_offline_usermanagement.AUTHENTICATION_TRIAL_USER_INACTIVE_POPUP_MSG:
                        # If user is inactive popup is found, closing the login window and breaking from the loop
                        self.logger.info(f"[{type(self).prefixCls}] Error popup with message : {popUpMsg} appeared")
                        self.logger.info(f"[{type(self).prefixCls}] User: {userName} has become inactive")
                        logWin.close()
                        break

                    if retryLoginCount > maxAuthenticationTrailValue:
                        logWin.close()
                        self.logger.error(
                            f"[{type(self).prefixCls}] Authentication trial value is set to : "
                            f"{maxAuthenticationTrailValue} and Inactive user popup did not"
                            f"appear after retry count {retryLoginCount}")

                        return False

                retryLoginCount += 1

            self.logger.info(f"[{type(self).prefixCls}] Setting {userName} to active")
            self.setUserToActive(projName = projName,
                                 userName = userName)

            if retryLoginCount == maxAuthenticationTrailValue:
                self.logger.newStep(
                    f"Authentication trail value is set to : {maxAuthenticationTrailValue} and User : {userName} "
                    f"became inactive after retry count {retryLoginCount}")
                return True

            self.logger.error(
                f"[{type(self).prefixCls}] Authentication trial value is set to : {maxAuthenticationTrailValue} and "
                f"User : {userName} became inactive after retry count {retryLoginCount}")

            return False
        except Exception:
            self.logger.exception(f"[{type(self).prefixCls}] Exception occurred in checkUserInactiveAfterMaxTrail() ")
            return False

    #-------------------------------------------------------------------------------------------------------------------
    def checkNobodyIsLoggedIn(self, projName):
        '''
        This method is used to check if nobody is logged in
        '''
        self.logoutCurrentUser(projName = projName)

        try:
            popUp = self.app.window(best_match="Dialog")
            popUp.wait("exists visible", timeout=15)

            if popUp.exists():
                popUpMsg = popUp.Static2.texts()[0]
                popUp.close()
                if popUpMsg == constants_offline_usermanagement.NOBODY_LOGOUT_POPUP_MSG:
                    self.logger.info(f"[{type(self).prefixCls}] No user is logged in")
                    return True
            self.logger.info(f"[{type(self).prefixCls}] Some user was logged in")
            return False

        except Exception:
            return False

    #------------------------------------------------------------------------------------------------------------------
    def selectAndAddRandomDevice(self, deviceaddWindow):
        """
        :param deviceaddWindow: Add Device window object.

        Add random device from Add Device window into PLCD project.
        """
        try:
            listViewObj = deviceaddWindow['ListView']
            valList = listViewObj.texts()
            valueslst = [elem for elem in valList if elem]
            listViewObj.type_keys("{HOME}")

            randomIdx = random.randint(0, len(valueslst)-1)
            self.logger.info(f"[{type(self).prefixCls}] Adding random device : "
                             f"{valueslst[randomIdx].strip()} from list")

            listViewObj.type_keys("{HOME}")
            listViewObj.type_keys("{HOME}")
            downTimes = "{DOWN " + str(randomIdx) + "}"
            listViewObj.type_keys(downTimes)

            self.logger.info(f"[{type(self).prefixCls}] Clicking Add Device button")
            okBtn = deviceaddWindow['&Add Device']
            okBtn.click()
            userSleep(5)
            self.logger.info(f"[{type(self).prefixCls}] Successfully added device")
            return True
        except Exception:
            self.logger.exception(f"[{type(self).prefixCls}] Exception occurred in selectAndAddRandomDevice() ")
            return False

    #-------------------------------------------------------------------------------------------------------------------
    def verifyAccess(self, projObj, accessStr, accessExpectedFlag, addorDeleteAfterFlag = False):
        '''
        This method is used to verify access for required operations on required inner class objects
        '''
        try:
            self.logger.info(f"[{type(self).prefixCls}] Verifying access to perform {accessStr} operation")
            self.logger.info(f"[{type(self).prefixCls}] ACCESS EXPECTED = {accessExpectedFlag}")
            operationExecStatus = getattr(projObj, accessStr)()
            if not operationExecStatus:
                self.logger.error(f"[{type(self).prefixCls}] Some error occurred while performing {accessStr} command")
                return False

            loginPopUpAppearedFlag = self._checkIfLoginPopUpAppeared()
            if accessStr == 'create' and addorDeleteAfterFlag:
                self.moveMousePtrToTitleBar(projName = self.projName)
                projObj.remove()
            if accessStr == 'remove' and addorDeleteAfterFlag:
                self.moveMousePtrToTitleBar(projName = self.projName)
                projObj.create()
                userSleep(1)
                projObj.post_create()

            self.moveMousePtrToTitleBar(projName = self.projName)
            try:
                getattr(projObj, 'post_'+accessStr)()
            except Exception:
                pass

            accessResultStr = "DENIED" if loginPopUpAppearedFlag else "GRANTED"
            if loginPopUpAppearedFlag == accessExpectedFlag:
                self.logger.error(f"[{type(self).prefixCls}] ACCESS EXPECTED = {accessExpectedFlag} but ACCESS TO "
                                  f"PERFORM {accessStr} OPERATION WAS {accessResultStr}")

                return False
            self.logger.newStep(f"ACCESS EXPECTED = {accessExpectedFlag} and ACCESS TO PERFORM {accessStr} "
                                f"OPERATION WAS {accessResultStr}", level = 3)
            return True
        except Exception:
            self.logger.exception(f"[{type(self).prefixCls}] Exception occurred in verifyAccess() ")
            return False

    #-------------------------------------------------------------------------------------------------------------------
    def verifyExecuteCmdAccess(self, objName, accessExpectedFlag):
        '''
        This method is used to verify access for execute command operations on required objects
        '''
        try:
            self.logger.newStep(f"Verifying access to execute {objName} command", level = 3)
            self.logger.info(f"[{type(self).prefixCls}] ACCESS EXPECTED = {accessExpectedFlag}")

            operationExecStatus = getattr(self, "execute" + objName)()
            if not operationExecStatus:
                self.logger.error(f"[{type(self).prefixCls}] Some error occurred while performing executing "
                                  f"{objName} command")

                return False

            loginPopUpAppearedFlag = self._checkIfLoginPopUpAppeared()

            self.logger.newStep(f"Performing post action operation for execute {objName} command", level = 3)
            try:
                postExecStatus = getattr(self, "post" + objName)()
                if not postExecStatus:
                    self.logger.error(f"[{type(self).prefixCls}] Some error occurred while performing post action "
                                      f"for executing {objName} command")

                    return False
                self.logger.newStep(f"Post action operation for execute {objName} command completed..", level = 3)
            except Exception:
                self.logger.info(f"[{type(self).prefixCls}] {objName} does not have any post action operations..")

            accessResultStr = "DENIED" if loginPopUpAppearedFlag else "GRANTED"
            if loginPopUpAppearedFlag == accessExpectedFlag:
                self.logger.error(f"[{type(self).prefixCls}] ACCESS EXPECTED = {accessExpectedFlag} but "
                                  f"ACCESS TO EXECUTE {objName} COMMAND WAS {accessResultStr}")

                return False
            self.logger.newStep(f"ACCESS EXPECTED = {accessExpectedFlag} and ACCESS TO EXECUTE {objName} "
                                f"COMMAND WAS {accessResultStr}")
            return True
        except Exception:
            self.logger.exception(f"[{type(self).prefixCls}] Exception occurred in verifyExecuteCmdAccess() ")
            return False

    #------------------------------------------------------------------------------------------------------------------
    def addIOModule(self, projName, devicesToAddList, displayAllVersionFlg = False):
        """
        :param projName: Name of the PLC project.

        :param devicesToAddList: List of devices to add in the project.

        Add Devices.

        1.    Go to EtherCAT Master in Devices window then open the Update Window.

        2.    Choose the 'Append device' option, which changes the 'Update Device' into 'Add Device'. Select the vendor:
              'Lenze' and uncheck the GroupByDevice option checkbox.

        3.    Add devices from the devicesToAddList into the PLCD project and close the Add Device window.

        .. image:: images/addDeviceWindow.png
        """
        self.logger.info(f"[{type(self).prefixCls}] Adding IO Module devices - {devicesToAddList}")
        try:
            userSleep(3)
            mainWindow = self.getMainWindow(header = projName)
            if mainWindow.exists(timeout = 60, retry_interval = 0.5):
                mainWindow.set_focus()
            else:
                self.logger.error(f"[{type(self).prefixCls}] Could not find main window")
                return False

            devwin = mainWindow.Devices
            userSleep(3)

            # Go to Couple IO modul
            self.logger.info(f"[{type(self).prefixCls}] Go to Coupler IO Moduls object")
            ioModulObj = self.getObjFromDevicesWindowWpf(objectName = "Coupler_I_O_moduls")
            ioModulObj.click_input()

            self.moveMousePtrToTitleBar(projName = constants_offline_usermanagement.OFFLINE_USR_MGMT_PLC_PROJ_NAME)
            self.logger.info(f"[{type(self).prefixCls}] Open Update Device Window using Alt+PD..")
            userSleep(2)
            devwin.type_keys("%")
            userSleep(0.5)
            devwin.type_keys("PD")

            userSleep(2)
            updateWindow = self.app['Update Device']
            self.logger.info(f"[{type(self).prefixCls}] Update Device window opened successfully...")
            adddev = updateWindow['&Append device']
            adddev.type_keys("{SPACE}")
            self.logger.info(f"[{type(self).prefixCls}] Clicked Append Device checkbox...")
            userSleep(3)

            self.logger.info(f"[{type(self).prefixCls}] Add Device window now available for adding device...")
            deviceaddWindow = self.app['Add Device']
            vendorSelection = deviceaddWindow['Vendor:ComboBox']
            vendorSelection.select('Lenze')
            userSleep(2)

            # SPS2018 : Change in Listview (add device folder structure)
            self.uncheckGroupByDev(deviceaddWindow = deviceaddWindow)

            # Display all versions for firmwarehandling scenario.
            if displayAllVersionFlg:
                self.checkDisplayAllVersions(deviceaddWindow = deviceaddWindow)
            userSleep(2)

            addDeviceStatus = self.selectAndAddDevices(deviceaddWindow = deviceaddWindow,
                                                       devicesToAddList = devicesToAddList,
                                                       displayAllVersionFlg = displayAllVersionFlg)
            userSleep(2)
            for key, value in list(addDeviceStatus.items()):
                if not value:
                    deviceNotAddedList = []
                    for i, _ in enumerate(devicesToAddList):
                        if devicesToAddList[i][0] == key:
                            deviceNotAddedList.append(devicesToAddList[i])
                    self.uncheckGroupByDev(deviceaddWindow = deviceaddWindow)
                    if displayAllVersionFlg:
                        self.checkDisplayAllVersions(deviceaddWindow = deviceaddWindow)
                    userSleep(1)
                    addDeviceStatus = self.selectAndAddDevices(deviceaddWindow = deviceaddWindow,
                                                               devicesToAddList = deviceNotAddedList,
                                                               displayAllVersionFlg = displayAllVersionFlg)
                    userSleep(2)

            userSleep(5)
            self.logger.info(f"[{type(self).prefixCls}] Closing Add device Window...")
            try:
                closeBtn = deviceaddWindow['&Close']
                closeBtn.click()
                userSleep(2)
                self.logger.info(f"[{type(self).prefixCls}] Successfully Closed Add device Window...")
            except Exception:
                try:
                    self.logger.info(f"[{type(self).prefixCls}] Retrying closing Add device Window...")
                    closeBtn = deviceaddWindow['Close']
                    closeBtn.click()
                    userSleep(2)
                    self.logger.info(f"[{type(self).prefixCls}] Successfully Closed Add device Window...")
                except Exception:
                    self.logger.info(f"[{type(self).prefixCls}] Retrying closing Add device Window...")
                    mainWindow.type_keys("{ESC ESC ESC}")
                    self.logger.info(f"[{type(self).prefixCls}] Successfully Closed Add device Window...")
        except Exception:
            self.logger.exception(f"[{type(self).prefixCls}] Exception occurred in addIOModule() ")
            return False

        for key, value in list(addDeviceStatus.items()):
            if value:
                self.logger.info(f"[{type(self).prefixCls}] Successfully added {key} device")
            else:
                self.logger.error(f"[{type(self).prefixCls}] Could not add {key} device")
                return False
        return True

    #-------------------------------------------------------------------------------------------------------------------
    def addRemoveDUTfromPRG(self, removeFlag = False):
        '''
        1.    Go to PLC_PRG in Devices tab and open DUT window.

        2.    Declare DUT instance in PLC_PRG.

        3.    Code to add DUT declaration is stored at :
        "C:\\Workspace-SV-devel\\SDC-Tests\\tests\\common\\offline_user_management\\utils\\DUTdeclarationInPRG.txt"

        4.   Code to remove DUT declaration is stored at :
        "C:\\Workspace-SV-devel\\SDC-Tests\\tests\\common\\offline_user_management\\utils\\removeDUTdeclarationPRG.txt"

        5.    Copy the code from above locations and paste into PLC_PRG.

        6.    Save the project.

        '''
        try:
            mainWindow = self.getMainWindow(header = self.projName)
            mainWindow.set_focus()
            userSleep(1)

            self.logger.info(f"[{type(self).prefixCls}] Go to DUT in Devices tab and open DUT window")
            devicesWindow = mainWindow['Devices']
            self.gotoDevicesListElement(devicesWindow = devicesWindow, elementName = 'PLC_PRG (PRG)')
            plcPrgWin = mainWindow['PLC_PRG']
            plcPrgWin.set_focus()

            self.logger.info(f"[{type(self).prefixCls}] PLC program window opened")
            wpfApp = self.connectToPLCWPFWindow()
            wind = wpfApp.windows()
            title = wind[0].get_properties()['texts'][0]
            handle = wpfApp.window(title = title)
            child = handle.child_window(auto_id = "PLC_PRG")
            child0 = child.wrapper_object()
            child1 = child0.children()
            child2 = child1[0].children()
            plcPrgFrame = child2[0].children()[0]

            self.logger.info(f"[{type(self).prefixCls}] Declare DUT instance in PLC_PRG")
            varDeclFrame = plcPrgFrame.children()[0]
            varDeclFrame.click_input()
            userSleep(1)
            child0.type_keys("^A")
            userSleep(1)
            child0.type_keys("^A")
            userSleep(1)
            child0.type_keys("{DELETE}")
            userSleep(1)
            if removeFlag:
                codeFile = constants_offline_usermanagement.REM_DUT_DECLARATION_PRG_FILE
            else:
                codeFile = constants_offline_usermanagement.DUT_DECLARATION_IN_PRG_FILE
            command = 'type ' + os.path.abspath(codeFile) + '| clip'
            os.system(command)
            child0.type_keys("^V")
            userSleep(2)

            # self.saveProject(projName = self.projName)
        except Exception:
            self.logger.exception(f"[{type(self).prefixCls}] Exception occurred in addRemoveDUTfromPRG() ")

    #-------------------------------------------------------------------------------------------------------------------
    def addVariablesToDUT(self):
        '''
        1.    Go to DUT in Devices tab and open DUT window.

        2.    Declare required variables in DUT file.

        3.    Variable declaration is stored at :
        "C:\\Workspace-SV-devel\\SDC-Tests\\tests\\common\\offline_user_management\\utils\\variableDeclaration.txt"

        5.    Copy the code from above locations and paste into DUT.

        6.    Save the project.

        '''
        try:
            mainWindow = self.getMainWindow(header = self.projName)
            mainWindow.set_focus()
            userSleep(1)

            self.logger.info(f"[{type(self).prefixCls}] Go to DUT in Devices tab and open DUT window")
            devicesWindow = mainWindow['Devices']
            self.gotoDevicesListElement(devicesWindow = devicesWindow, elementName = 'DUT')
            dutWin = mainWindow['DUT']
            dutWin.set_focus()

            self.logger.info(f"[{type(self).prefixCls}] DUT window opened")
            wpfApp = self.connectToPLCWPFWindow()
            wind = wpfApp.windows()
            title = wind[0].get_properties()['texts'][0]
            handle = wpfApp.window(title = title)
            child = handle.child_window(auto_id = "DUT")
            child0 = child.wrapper_object()

            self.logger.info(f"[{type(self).prefixCls}] Declare variables in DUT")
            child0.click_input()
            userSleep(1)
            child0.type_keys("^A")
            userSleep(1)
            child0.type_keys("^A")
            userSleep(1)
            child0.type_keys("{DELETE}")
            userSleep(1)
            command = 'type ' + os.path.abspath(constants_offline_usermanagement.VAR_DECLARATION_IN_DUT_FILE) + '| clip'
            os.system(command)
            child0.type_keys("^V")
            userSleep(2)

            # self.saveProject(projName = self.projName)
        except Exception:
            self.logger.exception(f"[{type(self).prefixCls}] Exception occurred in addVariablesToDUT() ")

    #-------------------------------------------------------------------------------------------------------------------
    def addFolderToObjOnDevicesWindow(self, objectName, folderName, projName):
        '''
        This method is used to add folder to a required object on Devices window
        1. Select Object from Devices window
        2. In main menu go to Project -> Add Folder..
        3. On Add Folder window enter new folder name and click Ok button
        :param objectName: Name of the object on devices window to which folder is to be added
        :param folderName: Name of the new folder to be added
        '''
        try:
            self.logger.info(f"[{type(self).prefixCls}] Selecting {objectName} element object on Devices window")
            devWin = self.getDevicesWindow(header = projName)

            self.gotoDevicesListElement(devicesWindow = devWin, elementName = objectName, performDoubleClick = False)

            self.moveMousePtrToTitleBar(projName = projName)
            # In Main menu go to Project -> Add Folder...
            self.logger.info(f"[{type(self).prefixCls}] Selecting 'Add Folder' option from main menu")
            self.selectMenuItem(itemPathList = ["Project", "Add Folder..."],
                                projName = projName)

            # Enter child object name in Add Folder window and click OK
            addFolderWin = self.app['Add Folder']
            addFolderWin.wait('ready')
            self.logger.info(f"[{type(self).prefixCls}] Add Folder window opened")
            folderNameEditBox = addFolderWin.Edit

            self.logger.info(f"[{type(self).prefixCls}] Entering name of folder as {folderName}")
            folderNameEditBox.set_edit_text(folderName)

            self.logger.info(f"[{type(self).prefixCls}] Clicking 'Ok' button to add the Folder")
            okButton = addFolderWin.OK
            okButton.wait('enabled', timeout = 5)
            okButton.click_input()
            return True
        except Exception:
            self.logger.exception(f"[{type(self).prefixCls}] Exception occurred in addFolderToObjOnDevicesWindow() ")
            return False

    #-------------------------------------------------------------------------------------------------------------------
    def buildProjAndGoOnline(self, ipAddress, projName):
        '''
        1. Build project
        2. Check if build completed with 0 errors
        3. Select controller
        4. Go online
        '''
        try:
            self.logger.info(f"[{type(self).prefixCls}] Building project..")
            buildStatus = self.buildProject(projName = projName)
            if not buildStatus:
                self.logger.error(f"[{type(self).prefixCls}] Project build failed ... cannot proceed further..")
                return False

            self.logger.info(f"[{type(self).prefixCls}] Checking if build completed with 0 errors...")
            zeroErrStatus = self.checkBuildMessages(projName = projName)
            if not zeroErrStatus:
                self.logger.error(
                    f"[{type(self).prefixCls}] Project did not compile with 0 errors .. cannot proceed further")

            # Select controller in communication settings tab
            controllerSelectStatus = self.selectController(ipAddress = ipAddress, projName = projName)
            if not controllerSelectStatus:
                self.logger.error(f"[{type(self).prefixCls}] Controller not selected.. Cannot proceed")
                return False

            # Going online
            onlineStatus = self.goOnline()
            if not onlineStatus:
                self.logger.error(f"[{type(self).prefixCls}] Controller is not online... cannot proceed further..")
                return False
        except Exception:
            self.logger.exception(f"[{type(self).prefixCls}] Exception occurred in buildProjAndGoOnline() ")
            return False
        return True

    #-------------------------------------------------------------------------------------------------------------------
    def deleteAllUsersAndGroups(self, projName):
        '''
        This method is used to remove all existing non-default users and groups
        1. Open Users and Groups Settings
        2. Go to Groups tab and delete all the groups other than default groups
        3. Go to Users tab and delete all the users other than default users
        4. Close Project settings window
        '''
        try:
            # Open Users and Groups Settings
            usersAndGrpsSettingOpenStatus = self._openUsersAndGroupSettings(projName = projName)
            if not usersAndGrpsSettingOpenStatus:
                self.logger.error(f"[{type(self).prefixCls}] Users and Groups Settings is not open")
                return False

            # Select Groups tab
            projSettingsWin = self.app.window(title_re = constants_offline_usermanagement.PROJECT_SETTINGS_WIN_TITLE)
            projSettingsWin.wait('ready')
            projSettingsWin.set_focus()
            self.logger.info(f"[{type(self).prefixCls}] Selecting Groups tab")
            tabControl = projSettingsWin.TabControl
            tabControl.wait('ready')
            tabControl.select('Groups')
            self.logger.info(f"[{type(self).prefixCls}] 'Groups' tab selected")

            handle = self.getWpfAppHandle()
            # Start deleting Groups
            groupsTreeTableView = handle.child_window(auto_id = "_groupsTreeTableView")
            allGrps = groupsTreeTableView.children()
            allGrpNamesToDel = [grp.legacy_properties()['Name'] for grp in allGrps if grp.legacy_properties()[
                'Name'] and grp.legacy_properties()[
                'Name'] not in constants_offline_usermanagement.GRPS_AND_USERS_NOT_TO_DELETE]

            for grpName in allGrpNamesToDel:
                self.logger.info(f"[{type(self).prefixCls}] Deleting group {grpName}")
                for grp in groupsTreeTableView.children():
                    if grp.legacy_properties()['Name'] == grpName:
                        self.logger.info(f"[{type(self).prefixCls}] Clicking on {grpName}")
                        grp.click_input()
                        self.logger.info(f"[{type(self).prefixCls}] Clicking Remove button")
                        removeGrpBtn = handle.child_window(auto_id = "_removeGroupButton")
                        removeGrpBtn.set_focus()
                        removeGrpBtn.click_input()
                        self.logger.info(f"[{type(self).prefixCls}] {grpName} Removed")
                        userSleep(0.5)
                        break

            projSettingsWin.wait('ready')
            projSettingsWin.set_focus()
            self.logger.info(f"[{type(self).prefixCls}] Selecting Users tab")
            tabControl = projSettingsWin.TabControl
            tabControl.wait('ready')
            tabControl.select('Users')
            self.logger.info(f"[{type(self).prefixCls}] 'Users' tab selected")

            handle = self.getWpfAppHandle()
            # Start deleting Users
            usersTreeTableView = handle.child_window(auto_id = "_userTreeTableView")
            allUsers = usersTreeTableView.children()
            allNamesToDel = [user.legacy_properties()['Name'] for user in allUsers if user.legacy_properties()[
                'Name'] and user.legacy_properties()[
                'Name'] not in constants_offline_usermanagement.GRPS_AND_USERS_NOT_TO_DELETE]

            for usrName in allNamesToDel:
                self.logger.info(f"[{type(self).prefixCls}] Deleting user {usrName}")
                for user in usersTreeTableView.children():
                    if user.legacy_properties()['Name'] == usrName:
                        self.logger.info(f"[{type(self).prefixCls}] Clicking on {usrName}")
                        user.click_input()
                        self.logger.info(f"[{type(self).prefixCls}] Clicking Remove button")
                        removeBtn = handle.child_window(auto_id = "_removeUserButton")
                        removeBtn.set_focus()
                        removeBtn.click_input()
                        self.logger.info(f"[{type(self).prefixCls}] {usrName} Removed")
                        userSleep(0.5)
                        break

            self.logger.info(f"[{type(self).prefixCls}] Clicking on 'OK' Button")
            okButton = handle.child_window(auto_id = "_okButton")
            okButton.set_focus()
            okButton.click()
            self.logger.info(f"[{type(self).prefixCls}] 'OK' Button clicked")

            # Waiting for Project settings window to close
            projSettingsWin.wait_not(wait_for_not = "exists", timeout = 5, retry_interval = 0.1)
            return True
        except Exception:
            self.logger.exception(f"[{type(self).prefixCls}] Exception occurred in deleteAllUsersAndGroups() ")
            return False

#-----------------------------------------------------------------------------------------------------------------------
class PermissionXMLParser():
    '''
    This is a class for Permission xml File parsing
    '''
    prefixCls = 'PermissionXMLParser'
    prefixCls = "PermissionXMLParser"

    #-------------------------------------------------------------------------------------------------------------------
    def __init__(self, xmlFile, logger):
        xmlFilePath = os.getcwd() + xmlFile
        tree = ET.parse(xmlFilePath)
        self.rootNode = tree.getroot()
        self.permData = self._loadPermissionData()
        self.logger = logger

    #-------------------------------------------------------------------------------------------------------------------
    def _loadPermissionData(self):
        '''
        This method load permission data in dictionary format
        '''
        try:
            permData = {}
            for permission in self.rootNode:
                grantedList = []
                deniedList = []
                accessType = None
                for ele in permission:
                    if str(ele.tag) == "Name":
                        permName = ele.text
                        print(permName)
                    if str(ele.tag) == "Permissions":
                        for permiss in ele:
                            for node in permiss:
                                if str(node.tag) == "ActionName":
                                    accessType = node.text
                                if str(node.tag) == "Granted":
                                    for group in node:
                                        grantedList.append(group.text)
                                if str(node.tag) == "Denied":
                                    for group in node:
                                        deniedList.append(group.text)
                if accessType:
                    permData[permName] = {accessType : {"Grant": grantedList, "Deny": deniedList}}
                    #print(ele.text)
            return permData
        except Exception:
            self.logger.exception(f"[{type(self).prefixCls}] Exception occurred in _loadPermissionData() ")
            return None


if __name__ == '__main__':
    plc = UserManagement_PLC(logger = clsLogger())
    plc.connectToRunningPLC(version='4.0.0.37716')

    devWin = plc.getDevicesWindow(header = constants_offline_usermanagement.OFFLINE_USR_MGMT_PLC_PROJ_NAME)

    plc.gotoDevicesListElement(devicesWindow = devWin, elementName = "User_Model", performDoubleClick = False)

    plc.selectMenuItem(itemPathList = ["View", "Properties..."],
                       projName = constants_offline_usermanagement.OFFLINE_USR_MGMT_PLC_PROJ_NAME)
    pass


