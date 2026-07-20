# -*- coding: utf-8 -*-
#
# © 2007-2008 Lenze Drive Systems GmbH. All rights reserved.
# © 2008-2021 Lenze Automation GmbH. All rights reserved.
#
#-----------------------------------------------------------------------------------------------------------------------
# PyTeF file header (for PyTeF Internal Code) V1.4-01
#-----------------------------------------------------------------------------------------------------------------------
# Disable linter warnings -> ONLY for PyTeF internal code!
# pylint: disable=protected-access,relative-import
#
#-----------------------------------------------------------------------------------------------------------------------
# PyTeF Internal Code docstring (must be first definition in file)
#-----------------------------------------------------------------------------------------------------------------------
"""
This file is derived from ProjectObjectBase and will hold functions specific to VirtualAxes object
"""
#-----------------------------------------------------------------------------------------------------------------------
# PyTeF Internal Code imports (must be defined before code)
#-----------------------------------------------------------------------------------------------------------------------
from collections import OrderedDict
from pywinauto.keyboard import send_keys
from tests.testlib.utils.CommonLib import userSleep, takeScreenshot
from tests.cysec.cysec_testsuites.offline_user_management.core.ProjectObjects.ProjectObjectBase import ProjectObjectBase
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
class VirtualAxes(ProjectObjectBase):
    '''
    Class for VirtualAxes object of plc project
    '''
    prefixCls = 'VirtualAxes'
    OBJ_NAME_IN_DEV_WINDOW = "VirtualAxis"
    OBJ_NAME_IN_ADD_DEV_WINDOW = "VirtualAxis"
    OBJ_MODIFY_NAME = "VirtualAxisModified"
    CHILD_OBJ_NAME = "VirtualAxesChild"
    IS_OBJ_MODIFIED_FLAG = False

    PROPERTIES_DOWN_KEYS_ON_RGT_CLK_MENU = 6
    ADD_DEVICE_DOWN_KEYS_ON_RGT_CLK_MENU = 9

    ACTION_SEQ = OrderedDict()
    ACTION_SEQ['addOrRemoveChildren'] = {"nameInPermissionWin" : OBJ_NAME_IN_DEV_WINDOW}
    ACTION_SEQ['modify'] = {"nameInPermissionWin" : OBJ_NAME_IN_DEV_WINDOW}
    ACTION_SEQ['view'] = {"nameInPermissionWin" : OBJ_NAME_IN_DEV_WINDOW}
    ACTION_SEQ['remove'] = {"nameInPermissionWin" : OBJ_NAME_IN_DEV_WINDOW}

    #-------------------------------------------------------------------------------------------------------------------
    def preReq(self):
        '''
        This method is used to execute pre-required steps for VirtualAxes Object
        '''
        self.logger.info(f"[{type(self).prefixCls}] Creating VirtualAxes Object to begin with")
        if self.create():
            self.logger.info(f"[{type(self).prefixCls}] VirtualAxes Object created")
            return self.post_create()
        self.logger.error(f"[{type(self).prefixCls}] VirtualAxes Object not created")
        return False

    #-------------------------------------------------------------------------------------------------------------------
    def create(self):
        '''
        This method is used to create VirtualAxes object in Plc project
        1. Select Functions Object from devices window
        2. Right click on Functions node and in right click menu select Add device..
        3. On Add Device Window select virtual axes and add it
        '''
        try:
            # Select Functions object from Devices window
            self.logger.info(f"[{type(self).prefixCls}] Selecting Functions from Devices window and adding "
                             "Virtual Axes to it")
            uiaWindow = self.plcObj.getWpfAppHandle()
            functions = self.plcObj.getObjFromDevicesWindowWpf(objectName = "Functions")

            if functions is None:
                functions = self.plcObj.getObjFromDevicesWindowWpf(objectName = "VirtualAxes")

            # Right clicking on the Functions object and select 'Add Device' option
            functions.click_input(button = "right")

            self.logger.info(f"[{type(self).prefixCls}] Selecting 'Add device' option from right click menu")
            userSleep(2)
            self.plcObj.clickContextMenuItem(mainAppWindow = uiaWindow, menuItemStr = "Add Device...")

            deviceaddWindow = self.plcObj.app['Add Device']
            takeScreenshot()
            deviceaddWindow.wait('exists', timeout = 3)
            self.logger.info(f'[{type(self).prefixCls}] Add Devices window opened')

            # Selecting Lenze as vendor on Add Device window
            self.logger.info(f"[{type(self).prefixCls}] selecting vendor: Lenze")
            vendorSelection = deviceaddWindow['Vendor:ComboBox']
            vendorSelection.select('Lenze')

            # Unchecking Group by Device checkbox
            self.plcObj.uncheckGroupByDev(deviceaddWindow = deviceaddWindow)

            # Adding random device from devices list
            if not self.plcObj.selectAndAddDevices(deviceaddWindow = deviceaddWindow,
                                                   devicesToAddList = [type(self).OBJ_NAME_IN_ADD_DEV_WINDOW],
                                                   displayAllVersionFlg = True):
                self.logger.error(f"[{type(self).prefixCls}] Failed to add VirtualAxes")
                return False
            return True
        except Exception:
            self.logger.exception(f"[{type(self).prefixCls}] Exception occurred in create ")
            return False

    #-------------------------------------------------------------------------------------------------------------------
    def post_create(self):
        '''
        No post create action is needed as creation of VirtualAxes object is not possible
        '''
        try:
            # Close Add device window if it is open
            self.logger.info(f"[{type(self).prefixCls}] Performing post action function for create()")
            return self._closeAddDeviceWin()
        except Exception:
            self.logger.exception(f"[{type(self).prefixCls}] Exception occurred in post_addChildren() ")
            return False
    #
    # #-------------------------------------------------------------------------------------------------------------------
    # def addChildren(self):
    #     '''
    #     This method is used to add child element for VirtualAxes object
    #     1. Right click on VirtualAxes object from devices window
    #     2. Select add device option on the right click menu
    #     3. From Add Device window select random device and add
    #     '''
    #     try:
    #         # Getting VirtualAxes element object from Devices window
    #         virtAxes = self.plcObj.getObjFromDevicesWindowWpf(objectName = type(self).OBJ_NAME_IN_DEV_WINDOW)
    #         self.logger.info(f"[{type(self).prefixCls}] Right clicking on VirtualAxes in Devices window")
    #
    #         # Right clicking on the VirtualAxes object and select 'Add Device' option
    #         virtAxes.click_input(button = "right")
    #         self.logger.info(f"[{type(self).prefixCls}] Selecting 'Add device' option from right click menu")
    #         userSleep(2)
    #         keysToOpenAddDevice = f"{{DOWN {type(self).ADD_DEVICE_DOWN_KEYS_ON_RGT_CLK_MENU}}} {{ENTER}}"
    #         send_keys(keysToOpenAddDevice, pause = 0.3)
    #
    #         deviceaddWindow = self.plcObj.app['Add Device']
    #         deviceaddWindow.wait('exists', timeout = 3)
    #         self.logger.info(f'[{type(self).prefixCls}] Add Devices window opened')
    #
    #         # Selecting Lenze as vendor on Add Device window
    #         self.logger.info(f"[{type(self).prefixCls}] selecting vendor: Lenze")
    #         vendorSelection = deviceaddWindow['Vendor:ComboBox']
    #         vendorSelection.select('Lenze')
    #
    #         # Unchecking Group by Device checkbox
    #         self.plcObj.uncheckGroupByDev(deviceaddWindow = deviceaddWindow)
    #
    #         # Adding random device from devices list
    #         self.plcObj.selectAndAddRandomDevice(deviceaddWindow)
    #         return True
    #     except Exception:
    #         self.logger.exception(f"[{type(self).prefixCls}] Exception occurred in addChildren() ")
    #         return False

    #-------------------------------------------------------------------------------------------------------------------
    def _closeAddDeviceWin(self):
        '''
        Method is used to close Add Device window
        '''
        try:
            # Close Add device window if it is open
            deviceaddWindow = self.plcObj.app['Add Device']
            self.logger.info(f"[{type(self).prefixCls}] Checking if Add Devices window is open")
            if deviceaddWindow.exists(timeout = 3):
                self.logger.info(f"[{type(self).prefixCls}] Add Device window is open")
                self.logger.info(f"[{type(self).prefixCls}] Closing Add Device window")
                deviceaddWindow.close()
            else:
                self.logger.info(f"[{type(self).prefixCls}] Add device window is not open")
            return True
        except Exception:
            self.logger.exception(f"[{type(self).prefixCls}] Exception occurred while closing Add Device window ")
            return False

    #-------------------------------------------------------------------------------------------------------------------
    def post_addChildren(self):
        '''
        This is a post action method for addChildren method
        '''
        try:
            # Close Add device window if it is open
            self.logger.info(f"[{type(self).prefixCls}] Performing post action function for addChildren()")
            return self._closeAddDeviceWin()
        except Exception:
            self.logger.exception(f"[{type(self).prefixCls}] Exception occurred in post_addChildren() ")
            return False

    #-------------------------------------------------------------------------------------------------------------------
    def modify(self):
        '''
        This method is used to modify(rename) VirtualAxes object.
        1. Right click on VirtualAxes object
        2. Select Properties from right click menu
        3. Change VirtualAxes object name in properties window
        4. Click OK button
        '''
        try:
            # Getting VirtualAxes element object from project
            if type(self).IS_OBJ_MODIFIED_FLAG:
                virtualAxesEle = self.plcObj.getObjFromDevicesWindowWpf(objectName = type(self).OBJ_MODIFY_NAME)
                nameToSet = type(self).OBJ_NAME_IN_ADD_DEV_WINDOW
            else:
                virtualAxesEle = self.plcObj.getObjFromDevicesWindowWpf(
                    objectName = type(self).OBJ_NAME_IN_ADD_DEV_WINDOW)
                nameToSet = type(self).OBJ_MODIFY_NAME

            # Right click on Virtual Axes object and select Properties
            self.logger.info(f"[{type(self).prefixCls}] Right clicking on VirtualAxes element on Devices window")
            virtualAxesEle.click_input(button = 'right')
            self.logger.info(f"[{type(self).prefixCls}] Selecting 'Properties' on right click menu")
            userSleep(2)
            keysToOpenProperties = f"{{DOWN {type(self).PROPERTIES_DOWN_KEYS_ON_RGT_CLK_MENU}}} {{ENTER}}"
            send_keys(keysToOpenProperties, pause = 0.3)
            # Change object name on properties window and click Ok
            propertiesWin = self.plcObj.app.window(title_re = "Properties - *")

            self.logger.info(f"[{type(self).prefixCls}] Changing object name in properties tab to {nameToSet}")
            propertiesWin.Edit4.set_edit_text(nameToSet)

            self.logger.info(f"[{type(self).prefixCls}] Selecting OK button by typing ENTER")
            okButton = propertiesWin.OK
            okButton.wait("ready")
            okButton.set_focus()
            userSleep(0.5)
            propertiesWin.type_keys("{ENTER}")

            wpf = self.plcObj.getWpfAppHandle()
            refactorWin = wpf.child_window(auto_id = "QueryAutomaticRenameDialog")
            if refactorWin.exists(timeout = 30, retry_interval = 0.1):
                noBtn = refactorWin.child_window(auto_id = "_noButton")
                noBtn.wait('ready')
                noBtn.set_focus()
                noBtn.click_input()
            propertiesWin.wait_not(wait_for_not = 'enabled')
            self.logger.info(f"[{type(self).prefixCls}] ENTER pressed")
            return True
        except Exception:
            self.logger.exception(f"[{type(self).prefixCls}] Exception occurred in modify ")
            return False

    #-------------------------------------------------------------------------------------------------------------------
    def post_modify(self):
        '''
        This is a post action method for modify method for VirtualAxes
        This method is used to rename VirtualAxes object back to its original name
        '''
        try:
            # Check if properties window is open
            self.logger.info(f"[{type(self).prefixCls}] Performing post action function for modify()")
            propertiesWin = self.plcObj.app.window(title_re = "Properties - *")
            self.logger.info(f"[{type(self).prefixCls}] Checking if Properties window is open")

            if propertiesWin.exists(timeout = 3):
                # If properties window is open then close it
                self.logger.info(f"[{type(self).prefixCls}] Properties window is open")
                self.logger.info(f"[{type(self).prefixCls}] Closing Properties window")
                cancelButton = propertiesWin.Cancel
                cancelButton.click_input()
            else:
                # If properties window is not open that means access to perform modify function was granted, Hence
                type(self).IS_OBJ_MODIFIED_FLAG = True
                self.logger.info(f"[{type(self).prefixCls}] Properties window is not open")
                self.logger.info(
                    f"[{type(self).prefixCls}] Renaming VirtualAxes object back to {type(self).OBJ_NAME_IN_DEV_WINDOW}")

                self.modify()
                type(self).IS_OBJ_MODIFIED_FLAG = False
            return True
        except Exception:
            self.logger.exception(f"[{type(self).prefixCls}] Exception occurred in post_modify ")
            return False

    #-------------------------------------------------------------------------------------------------------------------
    def cleanUp(self):
        '''
        No cleanup is needed for VirtualAxes object
        '''
        self.logger.info(f"[{type(self).prefixCls}] There is no clean up action steps for VirtualAxes")
        return True
