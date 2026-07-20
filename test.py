# -*- coding: utf-8 -*-
#
# © 2007-2020 Lenze Drive Systems GmbH, Lenze Automation GmbH. All rights reserved.
# © 2020-     Lenze SE. All rights reserved.
#
#-----------------------------------------------------------------------------------------------------------------------
# PyTeF file header (for PyTeF Internal Code) V2.0-00
#-----------------------------------------------------------------------------------------------------------------------
# Disable linter warnings -> ONLY for PyTeF internal code!
# pylint: disable=protected-access
#
#-----------------------------------------------------------------------------------------------------------------------
# Module docstring (must be first definition in file)
#-----------------------------------------------------------------------------------------------------------------------
"""TODO: docstring of PyTeF Internal Code
"""
#-----------------------------------------------------------------------------------------------------------------------
# Module imports (must be defined before code)
#-----------------------------------------------------------------------------------------------------------------------
import typing as ty
import os
import weakref

from inspect import isclass

from PyQt5.QtWidgets import QWidget, QMessageBox, QApplication, QFrame, QTableWidgetItem, QHeaderView, QMainWindow
from PyQt5.QtGui import QIcon, QPixmap, QColor
from PyQt5.QtCore import QTimer, QTimerEvent, Qt, QSize

from pytef.core import Result, timeFunc, aio
from pytef.core.devel import _ThreadContext

from pytef.util import (Boolean, DataType, Float32, Signed16, Signed32, Unsigned08, Unsigned32, VisibleString)

from ..common import EnumInteractResponse

from .UiSimpleFrame import Ui_simpleFrame
from .UiInstructFrame import Ui_instructFrame
from .UiMainWindow import Ui_MainWindow

if ty.TYPE_CHECKING:
    from pytef.core.types import tyOptInt

#-----------------------------------------------------------------------------------------------------------------------
# SVN keyword section
#-----------------------------------------------------------------------------------------------------------------------
FILE_URL = "$HeadURL$"[10:-2]  # noqa: E501
FILE_REV = "$Revision$"[11:-2]
FILE_DATE = "$LastChangedDate$"[18:-2]
FILE_AUTHOR = "$LastChangedBy$"[16:-2]

#-----------------------------------------------------------------------------------------------------------------------
# PyTeF file header end
#-----------------------------------------------------------------------------------------------------------------------

class MyWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._resizeHandlers = []

    def addResizeHandler(self, func):
        self._resizeHandlers.append(func)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        #newSize = event.size()
        for handler in self._resizeHandlers:
            handler(event)

class MyFrame(QFrame):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._resizeHandlers = []

    def addResizeHandler(self, func):
        self._resizeHandlers.append(func)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        #newSize = event.size()
        for handler in self._resizeHandlers:
            handler(event)

#-----------------------------------------------------------------------------------------------------------------------
class _UiSimpleFrame(Ui_simpleFrame):

    def __init__(self, inOutDict, mainWindow):
        super().__init__()

        self.setupUi(mainWindow)
        self.mainWindow = mainWindow

        inOutDict["result"] = None

        title         = inOutDict.get("title",          "NO TITLE")
        text          = inOutDict.get("text",           "<no text given>")
        buttonStyle   = inOutDict.get("buttonStyle",    QMessageBox.StandardButton.Ok)
        buttonDefault = inOutDict.get("buttonDefault",  QMessageBox.StandardButton.Ok)
        timeout       = inOutDict.get("timeout",        None)
        notifyDelay   = inOutDict.get("notifyDelay",    None)

        self._inOutDict = inOutDict
        self._text      = text
        self._isClosed  = False

        #-----------------------------------------------------------------------
        # Icon
        #-----------------------------------------------------------------------
        thisPath = os.path.abspath(os.path.dirname(__file__))
        imgPath  = os.path.abspath(os.path.join(thisPath, '..', 'gui', 'images'))

        if buttonStyle == QMessageBox.StandardButton.Ok:
            imageFilePath = os.path.join(imgPath, 'check_green.png')

        elif buttonStyle == (QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No):
            if buttonDefault == QMessageBox.StandardButton.No:
                imageFilePath = os.path.join(imgPath, 'question_red.png')
            else:
                imageFilePath = os.path.join(imgPath, 'question_green.png')

        else:
            imageFilePath = os.path.join(imgPath, 'question_blue.png')

        self.labelImage.setPixmap(QPixmap(imageFilePath))

        self.mainWindow.setWindowTitle(title)
        self.mainWindow.setWindowIcon(QIcon(imageFilePath))

        #-----------------------------------------------------------------------
        # Text
        #-----------------------------------------------------------------------
        self.labelText.setText(text)

        #-----------------------------------------------------------------------
        # Buttons
        #-----------------------------------------------------------------------
        if buttonStyle == QMessageBox.StandardButton.Ok:
            self.pushButtonLeft.setDefault(True)
            self.pushButtonLeft.setFlat(False)
            self.pushButtonLeft.setText("&OK")
            self.pushButtonLeft.clicked['bool'].connect(self.onButtonOkClicked)

            self.pushButtonRight.close()
            self.buttonLayout.addWidget(self.pushButtonRight)

        elif buttonStyle == (QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No):

            if buttonDefault == QMessageBox.StandardButton.Yes:
                self.pushButtonLeft.setDefault(True)
                self.pushButtonLeft.setFlat(False)
                self.pushButtonLeft.setText("&Yes")
                self.pushButtonLeft.clicked['bool'].connect(self.onButtonYesClicked)

                self.pushButtonRight.setDefault(False)
                self.pushButtonRight.setFlat(False)
                self.pushButtonRight.setText("&No")
                self.pushButtonRight.clicked['bool'].connect(self.onButtonNoClicked)

            else:
                self.pushButtonLeft.setDefault(True)
                self.pushButtonLeft.setFlat(False)
                self.pushButtonLeft.setText("&No")
                self.pushButtonLeft.clicked['bool'].connect(self.onButtonNoClicked)

                self.pushButtonRight.setDefault(False)
                self.pushButtonRight.setFlat(False)
                self.pushButtonRight.setText("&Yes")
                self.pushButtonRight.clicked['bool'].connect(self.onButtonYesClicked)

        #-----------------------------------------------------------------------
        # Progress bars for timeout and notifier call
        #-----------------------------------------------------------------------
        if notifyDelay is None:
            self.progressNotifier.close()
            self.mainLayout.removeWidget(self.progressNotifier)
            self.progressNotifier = None
        else:
            self.progressTimeout.setValue(0)
            self.progressTimeout.setRange(0, int(notifyDelay * 1000))

        if timeout is None:
            self.progressTimeout.close()
            self.mainLayout.removeWidget(self.progressTimeout)
            self.progressTimeout = None
        else:
            self.progressTimeout.setValue(0)
            self.progressTimeout.setRange(0, int(timeout * 1000))

    #---------------------------------------------------------------------------
    def onResize(self, event) -> None:
        newSize = event.size()
        newHeight = newSize.height()
        newWidth  = newSize.width()

        self.verticalLayoutWidget.resize(newSize)

    #-------------------------------------------------------------------------------------------------------------------
    def updateWaitTime(self,
                       waitTimeMs: "tyOptInt" = None,
                       remainTimeMs: "tyOptInt" = None,
                       notifyTimeMs: "tyOptInt" = None) -> None:
        try:
            doUpdate = False

            if self._isClosed:
                return

            if remainTimeMs is not None:
                remainTimeMs = int(max(0, remainTimeMs))
                if self.progressTimeout is not None:
                    self.progressTimeout.setValue(remainTimeMs)
                    doUpdate = True

            if notifyTimeMs is not None:
                notifyTimeMs = int(max(0, notifyTimeMs))
                if self.progressNotifier is not None:
                    doUpdate = True
                    self.progressNotifier.setValue(notifyTimeMs)

            if doUpdate:
                self.mainWindow.update()

        except Exception as exc:
            raise

    #---------------------------------------------------------------------------
    def onButtonOkClicked(self) -> None:
        self._inOutDict["result"] = QMessageBox.StandardButton.Ok
        self._isClosed = True
        self.mainWindow.close()

    #---------------------------------------------------------------------------
    def onButtonYesClicked(self) -> None:
        self._inOutDict["result"] = QMessageBox.StandardButton.Yes
        self._isClosed = True
        self.mainWindow.close()

    #---------------------------------------------------------------------------
    def onButtonNoClicked(self) -> None:
        self._inOutDict["result"] = QMessageBox.StandardButton.No
        self._isClosed = True
        self.mainWindow.close()

#-------------------------------------------------------------------------------
class _UiInstructWindow(Ui_MainWindow):

    def __init__(self,
                 inOutDict,
                 mainWindow,
                 logger) -> None:

        super().__init__()

        self.setupUi(mainWindow)
        self.mainWindow = mainWindow
        self.menubar.close()
        self.statusbar.close()
        self.__weakLogger = weakref.ref(logger)

        inOutDict["result"]    = None

        title         = inOutDict.get("title",          "NO TITLE")
        instruction   = inOutDict.get("instruction",    "")
        fieldList     = inOutDict.get("fieldList",      [])
        infoText      = inOutDict.get("infoText",       None)
        buttonStyle   = inOutDict.get("buttonStyle",    QMessageBox.StandardButton.Ok)
        buttonDefault = inOutDict.get("buttonDefault",  QMessageBox.StandardButton.Ok)
        imageFilePath = inOutDict.get("imageFilePath",  None)
        timeout       = inOutDict.get("timeout",        None)
        notifyDelay   = inOutDict.get("notifyDelay",    None)

        inOutDict["valueList"] = [tpl[1] for tpl in fieldList]

        self._inOutDict   = inOutDict
        self._instruction = instruction
        self._fieldList   = fieldList
        self._txtCtrlList = []
        self._isClosed    = False

        self._workingTableItem = None

        #-----------------------------------------------------------------------
        # Image
        #-----------------------------------------------------------------------
        thisPath = os.path.abspath(os.path.dirname(__file__))
        imgPath  = os.path.abspath(os.path.join(thisPath, '..', 'gui', 'images'))

        if imageFilePath is None:
            imageFilePath = os.path.join(imgPath, 'exclamation_blue.png')

        if imageFilePath is not None:
            self.labelImage.setPixmap(QPixmap(imageFilePath))

        self.mainWindow.setWindowTitle(title)
        self.mainWindow.setWindowIcon(QIcon(imageFilePath))

        #-----------------------------------------------------------------------
        # Anweisung
        #-----------------------------------------------------------------------
        self.labelInstruct.setText(self._instruction)

        #-----------------------------------------------------------------------
        # Info
        #-----------------------------------------------------------------------
        if infoText is not None and infoText.strip():
            self.labelInfo.setText(infoText)
        else:
            self.groupBoxInfo.close()
            self.mainLayout.removeWidget(self.groupBoxInfo)
            self.groupBoxInfo = None

        #-----------------------------------------------------------------------
        # Statischer Text
        #-----------------------------------------------------------------------
        if not self._fieldList:
            self.groupBoxValues.close()
            self.mainLayout.removeWidget(self.groupBoxValues)
            self.groupBoxValues = None

        else:
            self.tableWidget.setColumnCount(3)
            self.tableWidget.setRowCount(len(self._fieldList))
            self.tableWidget.setHorizontalHeaderLabels(["Variable", "Value", "Data type"])

            # header = self.tableWidget.horizontalHeader()
            # header.setResizeMode(0, QHeaderView.Stretch)
            # header.setResizeMode(1, QHeaderView.ResizeToContents)
            # header.setResizeMode(2, QHeaderView.ResizeToContents)

            for row, field in enumerate(self._fieldList):
                txt     = field[0]
                dtType  = field[1]
                defVal  = field[2]

                txtType = "{} ({} byte)".format(type(dtType).__name__, dtType.byteLength)
                txtVal  = "{}".format(defVal)

                item = QTableWidgetItem(txt)
                item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                self.tableWidget.setItem(row, 0, item)

                item = QTableWidgetItem(txtVal)
                item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEditable)
                self.tableWidget.setItem(row, 1, item)

                item = QTableWidgetItem(txtType)
                item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                self.tableWidget.setItem(row, 2, item)

            self.tableWidget.resizeRowsToContents()
            self.tableWidget.resizeColumnsToContents()
            self.tableWidget.cellChanged.connect(self.onCellChanged)

        #-----------------------------------------------------------------------
        # Buttons
        #-----------------------------------------------------------------------
        objList = []

        if buttonStyle == QMessageBox.StandardButton.Ok:
            self.pushButtonLeft.setDefault(True)
            self.pushButtonLeft.setFlat(False)
            self.pushButtonLeft.setText("&OK")
            self.pushButtonLeft.clicked['bool'].connect(self.onButtonOkClicked)

            self.pushButtonRight.close()
            self.buttonLayout.removeWidget(self.pushButtonRight)

        elif buttonStyle == (QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No):

            if buttonDefault == QMessageBox.StandardButton.Yes:
                self.pushButtonLeft.setDefault(True)
                self.pushButtonLeft.setFlat(False)
                self.pushButtonLeft.setText("&Yes")
                self.pushButtonLeft.clicked['bool'].connect(self.onButtonYesClicked)

                self.pushButtonRight.setDefault(False)
                self.pushButtonRight.setFlat(False)
                self.pushButtonRight.setText("&No")
                self.pushButtonRight.clicked['bool'].connect(self.onButtonNoClicked)

            else:
                self.pushButtonLeft.setDefault(True)
                self.pushButtonLeft.setFlat(False)
                self.pushButtonLeft.setText("&No")
                self.pushButtonLeft.clicked['bool'].connect(self.onButtonNoClicked)

                self.pushButtonRight.setDefault(False)
                self.pushButtonRight.setFlat(False)
                self.pushButtonRight.setText("&Yes")
                self.pushButtonRight.clicked['bool'].connect(self.onButtonYesClicked)

        else:
            self.pushButtonRight.close()
            self.buttonLayout.removeWidget(self.pushButtonRight)
            self.pushButtonLeft.close()
            self.buttonLayout.removeWidget(self.pushButtonLeft)

        #-----------------------------------------------------------------------
        # Progress bars for timeout and notifier call
        #-----------------------------------------------------------------------
        if notifyDelay is None:
            self.progressNotifier.close()
            self.mainLayout.removeWidget(self.progressNotifier)
            self.progressNotifier = None
        else:
            self.progressTimeout.setValue(0)
            self.progressTimeout.setRange(0, int(notifyDelay * 1000))

        if timeout is None:
            self.progressTimeout.close()
            self.mainLayout.removeWidget(self.progressTimeout)
            self.progressTimeout = None
        else:
            self.progressTimeout.setValue(0)
            self.progressTimeout.setRange(0, int(timeout * 1000))

    @property
    def logger(self):
        try:
            # return the logger from the actual message handler
            return self.__weakLogger()
        except AttributeError:
            # get a logger from thread
            return _ThreadContext.loggerGet(childName = "dialog.qt5.window")

    #---------------------------------------------------------------------------
    def onResize(self, event) -> None:
        newSize = event.size()
        # newHeight = newSize.height()
        # newWidth  = newSize.width()

        self.verticalLayoutWidget.resize(newSize)

        if self.groupBoxInfo:
            boxSize = self.groupBoxInfo.size()
            self.labelInfo.resize(boxSize)

        if self.groupBoxValues:
            boxSize = self.groupBoxValues.size()
            self.tableWidget.resize(boxSize)

    #---------------------------------------------------------------------------
    def readValues(self) -> bool:

        fails = 0
        valueList = []
        self._inOutDict["valueList"] = valueList

        for row, tpl in enumerate(self._fieldList):
            dType = tpl[1]
            item = self.tableWidget.item(row, 1)
            valStr = item.text()
            try:
                value = type(dType)(initValue = valStr).value
                valueList.append(value)

                item.setText("")
                item.setBackground(QColor(0, 255, 0))
                item.setText('{}'.format(value))

            except Exception as exc:
                self.logger.printTrace()

                item.setText("")
                item.setBackground(QColor(255, 0, 0))
                item.setText('{}'.format(valStr))

                valueList.append(valStr)
                fails += 1

            self.tableWidget.update()
            self.mainWindow.update()

        return bool(fails == 0)

    #-------------------------------------------------------------------------------------------------------------------
    def updateWaitTime(self,
                       waitTimeMs = None,
                       remainTimeMs = None,
                       notifierTimeMs = None) -> None:
        try:
            doUpdate = False

            if self._isClosed:
                return

            if remainTimeMs is not None:
                remainTimeMs = int(max(0, remainTimeMs))
                if self.progressTimeout is not None:
                    self.progressTimeout.setValue(remainTimeMs)
                    doUpdate = True

            if notifierTimeMs is not None:
                notifierTimeMs = int(max(0, notifierTimeMs))
                if self.progressNotifier is not None:
                    doUpdate = True
                    self.progressNotifier.setValue(notifierTimeMs)

            if doUpdate:
                self.mainWindow.update()

        except Exception as exc:
            raise

    #---------------------------------------------------------------------------
    def onCellChanged(self, **kwargs) -> None:

        # do not call recursive
        if self._workingTableItem is not None:
            return

        item = self.tableWidget.currentItem()
        row = self.tableWidget.currentRow()
        col = self.tableWidget.currentColumn()
        dType = self._fieldList[row][1]

        self._workingTableItem = item

        valStr = item.text()
        try:
            value = type(dType)(initValue = valStr).value
            item.setBackground(QColor(0, 255, 0))
            item.setText('{}'.format(value))

        except Exception as exc:
            item.setBackground(QColor(255, 0, 0))
            item.setText('{}'.format(valStr))

        pass

        self._workingTableItem = None

        self.tableWidget.update()
        #self.mainWindow.update()

    #---------------------------------------------------------------------------
    def onButtonOkClicked(self) -> None:
        self._inOutDict["result"] = QMessageBox.StandardButton.Ok

        if self._fieldList:
            res = self.readValues()
            if res is False:
                self.mainWindow.update()
                return

        self._isClosed = True
        self.mainWindow.close()

    #---------------------------------------------------------------------------
    def onButtonYesClicked(self) -> None:
        self._inOutDict["result"] = QMessageBox.StandardButton.Yes

        if self._fieldList:
            res = self.readValues()
            if res is False:
                self.mainWindow.update()
                return

        self._isClosed = True
        self.mainWindow.close()

    #---------------------------------------------------------------------------
    def onButtonNoClicked(self) -> None:
        self._inOutDict["result"] = QMessageBox.StandardButton.No

        if self._fieldList:
            res = self.readValues()
            if res is False:
                self.mainWindow.update()
                return

        self._isClosed = True
        self.mainWindow.close()

#-----------------------------------------------------------------------------------------------------------------------
class _FwDialog(object):

    def __init__(self,
                 title,
                 text = "",
                 buttonStyle = None,
                 buttonDefault = None,
                 timeout = None,
                 notifyDelay = None,
                 logger = None,
                 parent = None) -> None:
        super().__init__()

        if timeout is not None:
            title = "{} (timeout {:.3f} sec)".format(title, timeout)

        #---------------------------------------------------------------------------------------------------------------
        # check if notifier is available end enabled
        #---------------------------------------------------------------------------------------------------------------
        testRun = _ThreadContext.testRunGet()

        notifyEnabled = (testRun is not None and
                         testRun._notifier is not None and
                         testRun._notifier.isEnabled and
                         testRun._notifier.config.interaction.event.onWaitForAction is True)

        # force disable notifier (notify delay == 0)
        if notifyDelay is not None and notifyDelay <= 0:
            notifyEnabled = False

        #---------------------------------------------------------------------------------------------------------------
        # notifier if available -> check notify delay
        #---------------------------------------------------------------------------------------------------------------
        if notifyEnabled is True:

            if notifyDelay is None:
                notifyDelayMin = testRun._notifier.config.interaction.event.notifyDelayMin
                if notifyDelayMin is None:
                    notifyDelay = 0.0
                elif notifyDelayMin > 0:
                    notifyDelay = 60.0 * notifyDelayMin
                else:
                    notifyDelay = None

        else:
            notifyDelay = None

        #---------------------------------------------------------------------------------------------------------------
        # check default continue delay (timeout)
        #---------------------------------------------------------------------------------------------------------------
        if notifyEnabled and timeout is None:

            # use default timeout
            continueDelayMin = testRun._notifier.config.interaction.event.continueDelayMin
            if continueDelayMin is None:
                timeout = None
            elif continueDelayMin > 0:
                timeout = 60.0 * testRun._notifier.config.interaction.event.continueDelayMin
            else:
                timeout = None

        # force disable timeout (timeout == 0)
        if timeout is not None and timeout <= 0:
            timeout = None

        #---------------------------------------------------------------------------------------------------------------
        # the timeout of the dialog must be greater than the notifyDelay
        #---------------------------------------------------------------------------------------------------------------
        if timeout is not None and notifyDelay is not None:
            if timeout < notifyDelay:
                timeout = notifyDelay + timeout

        self._title = title
        self._text = text
        self._prefix = "{}".format(self.__class__.__name__)

        self._buttonStyle = buttonStyle
        self._buttonDefault = buttonDefault
        self._inOutDict = {}
        self._parent = parent

        # Timer
        self._timerTimeout = None
        self._timerStep = None
        self._timerNotify = None
        self._timeWaitStepMs = 100  # in ms

        self._timeout = timeout
        self._notifyDelay = notifyDelay

        self._timeStart = None
        self._timeStop = None
        self._timeNotify = None

        self._ui = None
        self._mainWindow = None

        self.__weakLogger = None
        if logger:
            self.__weakLogger = weakref.ref(logger)

    #-------------------------------------------------------------------------------------------------------------------
    # properties
    #-------------------------------------------------------------------------------------------------------------------
    @property
    def logger(self):
        try:
            # return the logger from the actual message handler
            return self.__weakLogger()
        except TypeError:
            # get a logger from thread
            return _ThreadContext.loggerGet(childName = "dialog.qt5")

    #-------------------------------------------------------------------------------------------------------------------
    def onTimerStep(self) -> None:
        self._timerStep.start()

        if self._timeStart is None:
            return

        if self._ui is None:
            self._timerStep.stop()
            self._timerStep = None
            return

        ui = self._ui

        if ui._isClosed is True:
            self._timerStep.stop()
            self._timerStep = None
            return

        now = timeFunc()
        waitTimeMs = (now - self._timeStart) * 1000

        if self._timeStop is None:
            remainTimeMs = None
        else:
            remainTimeMs = (self._timeStop - now) * 1000

        if self._timeNotify is None:
            notifyTimeMs = None
        else:
            notifyTimeMs = (self._timeNotify - now) * 1000

        if ui is not None:
            ui.updateWaitTime(waitTimeMs = waitTimeMs,
                              remainTimeMs = remainTimeMs,
                              notifyTimeMs = notifyTimeMs)

    #-------------------------------------------------------------------------------------------------------------------
    def onTimeout(self) -> None:
        self.logger.info("{}: Timeout after {:.3f} sec".format(self._prefix, self._timeout))

        if self._ui is not None:
            self._mainWindow.close()

    #-------------------------------------------------------------------------------------------------------------------
    def onTimeNotify(self) -> None:
        self.logger.info("{}: Notify call after {:.3f} sec".format(self._prefix, self._notifyDelay))

        self._timerNotify.stop()
        self._timeNotify    = None
        self._notifyDelay   = None

        testRun = _ThreadContext.testRunGet()
        if testRun is None or testRun._notifier is None:
            return

        aio(testRun._notifier._onTestInteractionNeeded(title = self._title,
                                                       text = self._text,
                                                       timeout = self._timeout))

    #-------------------------------------------------------------------------------------------------------------------
    def _showPrepare(self,
                     maxChars: int = 120) -> None:

        self._timeStart = timeFunc()

        if self._timeout is not None:
            self._timeStop = self._timeStart + self._timeout

            self._timerTimeout = QTimer()
            self._timerTimeout.timeout.connect(self.onTimeout)
            self._timerTimeout.start(int(self._timeout * 1000))

            self.logger.info("{}: Timer started, timeout in {:.3f} sec".format(self._prefix, self._timeout))

        if self._notifyDelay is not None:
            self._timeNotify = self._timeStart + self._notifyDelay

            self._timerNotify = QTimer()
            self._timerTimeout.timeout.connect(self.onTimeNotify)
            self._timerTimeout.start(int(self._notifyDelay * 1000))

            self.logger.info("{}: Timer started, notify call in {:.3f} sec".format(self._prefix, self._notifyDelay))

        if self._timerTimeout is not None or \
           self._timerNotify is not None:

            self._timerStep = QTimer()
            self._timerStep.timeout.connect(self.onTimerStep)
            self._timerStep.start(self._timeWaitStepMs)

        horLine    = "{}: +{}+".format(self._prefix, "-" * (maxChars - 2))

        self.logger.info(horLine)
        self.logger.info("{}: | {:{:d}} |".format(self._prefix, self._title, maxChars - 4))
        self.logger.info(horLine)
        lines = self._text.split("\n")
        for line in lines:
            self.logger.info("{}: | {:{:d}} |".format(self._prefix, line, maxChars - 4))

        self.logger.info(horLine)

    #-------------------------------------------------------------------------------------------------------------------
    def _showCleanup(self,
                     maxChars: int = 120) -> None:

        if self._timerStep is not None:
            self._timerStep.stop()
            self._timerStep = None

        if self._timerNotify is not None:
            self._timerNotify.stop()
            self._timerNotify = None
            self.logger.info("{}: Timer stopped (notifier)".format(self._prefix))

        if self._timerTimeout is not None:
            self._timerTimeout.stop()
            self._timerTimeout = None
            self.logger.info("{}: Timer stopped (timeout)".format(self._prefix))

    #-------------------------------------------------------------------------------------------------------------------
    def show(self) -> Result:

        try:
            # Diese Liste wird dem Dialog übergeben und von ihm gefüllt!!
            self._inOutDict["title"] = self._title
            self._inOutDict["text"] = self._text
            self._inOutDict["buttonStyle"] = self._buttonStyle
            self._inOutDict["buttonDefault"] = self._buttonDefault
            self._inOutDict["timeout"] = self._timeout
            self._inOutDict["notifyDelay"] = self._notifyDelay

            app = QApplication([])

            self._mainWindow = MyFrame()

            self._showPrepare()

            self._ui = _UiSimpleFrame(inOutDict = self._inOutDict,
                                      mainWindow = self._mainWindow)

            self._mainWindow.addResizeHandler(self._ui.onResize)

            try:
                self._mainWindow.show()
                res = app.exec_()

            except Exception as exc:
                self.logger.warning("{}: Exception while showing dialog: {}".format(self._prefix, exc))

            self._showCleanup()

            #-----------------------------------------------------------------------------------------------------------
            # Result handling
            #-----------------------------------------------------------------------------------------------------------
            res = self._inOutDict.get("result", None)
            if res is None:
                res = QMessageBox.StandardButton.Cancel

            if self._buttonStyle == QMessageBox.StandardButton.Ok:
                if res == QMessageBox.StandardButton.Ok:
                    result = Result(errorCode = Result.NO_ERROR,
                                    errorMessage = "Success",
                                    value = EnumInteractResponse.OK)

                    self.logger.info("{}: [OK] pressed, return value: {}".format(self._prefix, result.value))

                else:
                    result = Result(errorCode = Result.ERROR,
                                    errorMessage = "Success",
                                    value = EnumInteractResponse.CANCEL)

                    self.logger.info("{}: [X] pressed or timeout occurred, return value: {}".format(
                        self._prefix, result.value))

                return result

            elif self._buttonStyle == (QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No):

                if res == QMessageBox.StandardButton.Yes:
                    self.logger.info("{}: [YES] pressed".format(self._prefix))
                    result = Result(errorCode = Result.NO_ERROR,
                                    errorMessage = "Yes pressed",
                                    value = EnumInteractResponse.YES)

                elif res == QMessageBox.StandardButton.No:
                    self.logger.info("{}: [NO]  pressed".format(self._prefix))
                    result = Result(errorCode = Result.ERROR,
                                    errorMessage = "No pressed",
                                    value = EnumInteractResponse.NO)

                else:
                    self.logger.info("{}: [X] or [Cancel] pressed -> using NO as default value".format(self._prefix))
                    result = Result(errorCode = Result.ERROR,
                                    errorMessage = "[X] or [Cancel] pressed",
                                    value = EnumInteractResponse.CANCEL)

                return result

            msg = "{}: Invalid / unhandled buttonStyle".format(self._prefix)
            self.logger.error(msg)
            return Result(errorCode = Result.ERROR,
                          errorMessage = msg)

        except Exception as exc:
            self.logger.printTrace()
            return Result(errorCode = Result.ERROR,
                          errorMessage = "{}".format(exc))

    #---------------------------------------------------------------------------
    @classmethod
    def _test(cls) -> None:

        #---------------------------------------------------------------------------------------------------------------
        dlg = FwDialogOk(title = "FwDialogOk",
                         text  = "Press OK")
        dlg.show()

        #---------------------------------------------------------------------------------------------------------------
        dlg = FwDialogOk(title = "FwDialogOk",
                         text  = "Press [X]")
        dlg.show()

        #---------------------------------------------------------------------------------------------------------------
        dlg = FwDialogOk(title = "FwDialogOk",
                         text  = " ".join(['aaaa'] * 100))
        dlg.show()

        #---------------------------------------------------------------------------------------------------------------
        dlg = FwDialogOk(title   = "FwDialogOk with timeout",
                         text    = "Wait until timeout",
                         timeout = 5.0)
        dlg.show()

        #---------------------------------------------------------------------------------------------------------------
        dlg = FwDialogYesNo(title = "FwDialogYesNo",
                            text  = "Press YES")
        dlg.show()

        #---------------------------------------------------------------------------------------------------------------
        dlg = FwDialogYesNo(title = "FwDialogYesNo",
                            text  = "Press NO")
        dlg.show()

        #---------------------------------------------------------------------------------------------------------------
        dlg = FwDialogYesNo(title = "FwDialogYesNo",
                            text  = "Press [X]")
        dlg.show()

        #---------------------------------------------------------------------------------------------------------------
        dlg = FwDialogYesNo(title   = "FwDialogYesNo with timeout",
                            text    = "Wait until timeout",
                            timeout = 5.0)
        dlg.show()

        #---------------------------------------------------------------------------------------------------------------
        dlg = FwDialogNoYes(title = "FwDialogNoYes",
                            text  = "Press YES")
        dlg.show()

        #---------------------------------------------------------------------------------------------------------------
        dlg = FwDialogNoYes(title = "FwDialogNoYes",
                            text  = "Press NO")
        dlg.show()

        #---------------------------------------------------------------------------------------------------------------
        dlg = FwDialogNoYes(title = "FwDialogNoYes",
                            text  = "Press [X]")
        dlg.show()

        #---------------------------------------------------------------------------------------------------------------
        dlg = FwDialogNoYes(title   = "FwDialogNoYes with timeout",
                            text    = "Wait until timeout",
                            timeout = 5.0)
        dlg.show()

        #---------------------------------------------------------------------------------------------------------------
        dlg = FwDialogNoYes(title         = "FwDialogNoYes with timeout and notifier",
                            text         = "Wait until timeout",
                            timeout     = 20.0,
                            notifyDelay = 5.0)
        dlg.show()


#-----------------------------------------------------------------------------------------------------------------------
class FwInstructDialog(_FwDialog):

    def __init__(self, title, instruction, fieldList = None, dataDict = None, infoText = None, imageFilePath = None,
                 buttonStyle = QMessageBox.StandardButton.Ok, buttonDefault = QMessageBox.StandardButton.Ok,
                 timeout = None, notifyDelay = None, logger = None, parent = None) -> None:

        super().__init__(title = title,
                         text = instruction,
                         buttonStyle = buttonStyle,
                         timeout = timeout,
                         notifyDelay = notifyDelay,
                         parent = parent)

        if fieldList is None:
            fieldList = []
        if dataDict is None:
            dataDict = {}

        _fieldList = []
        for tpl in fieldList:
            txt    = tpl[0]
            dType  = tpl[1]
            defVal = tpl[2]

            if dType == int:
                dType = Unsigned32()
            elif dType == bool:
                dType = Boolean()
            elif dType == str:
                dType = VisibleString()
            elif dType == float:
                dType = Float32()
            elif isclass(dType) and issubclass(dType, DataType):
                dType = dType()
            elif isinstance(dType, DataType):
                pass
            else:
                raise Exception("Unknown data type")

            _fieldList.append((txt, dType, defVal))

        self._fieldList     = _fieldList
        self._infoText      = infoText
        self._imageFilePath = imageFilePath

    #-------------------------------------------------------------------------------------------------------------------
    def show(self) -> Result:

        try:
            # Diese Liste wird dem Dialog übergeben und von ihm gefüllt!!
            self._inOutDict["title"]         = self._title
            self._inOutDict["instruction"]   = self._text
            self._inOutDict["fieldList"]     = self._fieldList
            self._inOutDict["infoText"]      = self._infoText
            self._inOutDict["buttonStyle"]   = self._buttonStyle
            self._inOutDict["buttondefault"] = self._buttonDefault
            self._inOutDict["imageFilePath"] = self._imageFilePath
            self._inOutDict["timeout"]       = self._timeout
            self._inOutDict["notifyDelay"]   = self._notifyDelay

            app = QApplication([])

            self._mainWindow = MyWindow()

            self._showPrepare()

            self._ui = _UiInstructWindow(inOutDict = self._inOutDict,
                                         mainWindow = self._mainWindow,
                                         logger = self.logger)

            self._mainWindow.addResizeHandler(self._ui.onResize)

            try:
                self._mainWindow.show()
                self._mainWindow.resize(800, 600)
                res = app.exec_()

            except Exception as exc:
                self.logger.warning("{}: Exception while showing dialog: {}".format(self._prefix, exc))

            self._showCleanup()

            #-----------------------------------------------------------------------------------------------------------
            # Result handling
            #-----------------------------------------------------------------------------------------------------------
            valueList = self._inOutDict.get("valueList", [])
            if len(valueList) != len(self._fieldList):
                msg = "{}: {:d} value(s) returned - {:d} value(s) required".format(self._prefix, len(valueList),
                                                                                   len(self._fieldList))
                self.logger.error(msg)
                return Result(errorCode = Result.ERROR,
                              errorMessage = msg)

            res = self._inOutDict.get("result", None)
            if res is None:
                res = QMessageBox.StandardButton.Cancel

            if self._buttonStyle == QMessageBox.StandardButton.Ok:
                if res == QMessageBox.StandardButton.Ok:
                    result = Result(errorCode = Result.NO_ERROR,
                                    value = valueList,
                                    errorMessage = "Success")

                    self.logger.info("{}: [OK] pressed, return value: {}".format(self._prefix, result.value))

                else:
                    result = Result(errorCode = Result.ERROR,
                                    value = valueList,
                                    errorMessage = "Success")

                    self.logger.info("{}: [X] pressed or timeout occurred, return value: {}".format(
                        self._prefix, result.value))

                return result

            elif self._buttonStyle == (QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No):

                if res == QMessageBox.StandardButton.Yes:
                    self.logger.info("{}: [YES] pressed".format(self._prefix))
                    result = Result(errorCode = Result.NO_ERROR,
                                    value = valueList,
                                    errorMessage = "Yes pressed")

                elif res == QMessageBox.StandardButton.No:
                    self.logger.info("{}: [NO]  pressed".format(self._prefix))
                    result = Result(errorCode = Result.ERROR,
                                    value = valueList,
                                    errorMessage = "No pressed")

                else:
                    self.logger.info("{}: [X] or [Cancel] pressed -> using NO as default value".format(self._prefix))
                    result = Result(errorCode = Result.ERROR,
                                    value = valueList,
                                    errorMessage = "No pressed")

                return result

            msg = "{}: Invalid / unhandled buttonStyle".format(self._prefix)
            self.logger.error(msg)
            return Result(errorCode = Result.ERROR,
                          errorMessage = msg)

        except Exception as exc:
            self.logger.printTrace()
            return Result(errorCode = Result.ERROR,
                          errorMessage = "{}".format(exc))

    #-------------------------------------------------------------------------------------------------------------------
    def _showPrepare(self) -> None:
        maxChars = 120
        super()._showPrepare(maxChars = maxChars)

        horLine = "{}: +{}+".format(self._prefix, "-" * (maxChars - 2))

        if not self._fieldList:
            return

        maxNameLen  = max([len(s) for s in [tpl[0] for tpl in self._fieldList]])
        maxValueLen = max([len("{}".format(v)) for v in [tpl[2] for tpl in self._fieldList]])

        self.logger.info("{}: | {:{:d}} |".format(self._prefix, "Default values:", maxChars - 4))
        for tpl in self._fieldList:
            txt = "{:{:d}}: {:{:d}} ({})".format(tpl[0], maxNameLen, tpl[2], maxValueLen, tpl[1])
            fillChars = maxChars - len(txt) - 3
            self.logger.info("{}: | {}{}|".format(self._prefix, txt, " " * fillChars))

        self.logger.info(horLine)

    #---------------------------------------------------------------------------
    def _showCleanup(self) -> None:

        maxChars = 120
        super()._showCleanup(maxChars = maxChars)

        if not self._fieldList:
            return

        valueList = self._inOutDict.get('valueList', [])

        horLine = "{}: +{}+".format(self._prefix, "-" * (maxChars - 2))

        maxNameLen  = max([len(s) for s in [tpl[0] for tpl in self._fieldList]])
        maxValueLen = max([len("{}".format(v)) for v in valueList])

        self.logger.info("{}: | {:{:d}} |".format(self._prefix, "Return values:", maxChars - 4))
        for tpl, val in zip(self._fieldList, valueList):
            txt = "{:{:d}}: {:{:d}} ({})".format(tpl[0], maxNameLen, val, maxValueLen, tpl[1])
            fillChars = maxChars - len(txt) - 3
            self.logger.info("{}: | {}{}|".format(self._prefix, txt, " " * fillChars))

        self.logger.info(horLine)

    #-------------------------------------------------------------------------------------------------------------------
    @classmethod
    def _test(cls) -> None:

        fieldList = [("Wert 1", Unsigned08, 132),
                     ("Wert 2", Signed16,   255),
                     ("Wert 3", VisibleString(byteLength = 10),  "ABC"),
                     ("Wert 4", Float32,    1.3232),
                     ("Wert 5", Signed32,   -132)]

        #---------------------------------------------------------------------------------------------------------------
        dlg = cls(title       = "Field Dialog",
                  instruction = "Test, Test, Test",
                  fieldList   = fieldList,
                  infoText    = "Some info for this dialog\n test test ")
        dlg.show()

        #---------------------------------------------------------------------------------------------------------------
        dlg = cls(title       = "Field Dialog with timeout",
                  instruction = "Test, Test, Test",
                  fieldList   = fieldList,
                  infoText    = "Some info for this dialog",
                  timeout     = 3.0)
        dlg.show()

        #---------------------------------------------------------------------------------------------------------------
        dlg = cls(title       = "Field Dialog without fields",
                  instruction = "Test, Test, Test",
                  #fieldList  = [],
                  infoText    = "Some info for this dialog",
                  notifyDelay = 10.0)
        dlg.show()

        #---------------------------------------------------------------------------------------------------------------
        dlg = cls(title       = "Field Dialog without fields with timeout",
                  instruction = "Test, Test, Test",
                  #fieldList  = [],
                  infoText    = "Some info for this dialog",
                  timeout     = 3.0)
        dlg.show()

        #---------------------------------------------------------------------------------------------------------------
        dlg = cls(title       = "Field Dialog without fields and info",
                  instruction = "Test, Test, Test"
                  # fieldList  = [],
                  # infoText   = "Some info for this dialog")
                  )

        dlg.show()

        #---------------------------------------------------------------------------------------------------------------
        dlg = cls(title         = "Field Dialog with No-Yes Button",
                  instruction   = "Press YES",
                  buttonStyle   = (QMessageBox.StandardButton.Yes  | QMessageBox.StandardButton.No),
                  buttonDefault = QMessageBox.StandardButton.No)
        dlg.show()

        #---------------------------------------------------------------------------------------------------------------
        dlg = cls(title         = "Field Dialog with Yes-No Button",
                  instruction   = "Press NO",
                  buttonStyle   = (QMessageBox.StandardButton.Yes  | QMessageBox.StandardButton.No),
                  buttonDefault = QMessageBox.StandardButton.Yes)
        dlg.show()

        #---------------------------------------------------------------------------------------------------------------
        dlg = cls(title         = "Field Dialog with Yes-No Button",
                  instruction   = "Press [X]",
                  buttonStyle   = (QMessageBox.StandardButton.Yes  | QMessageBox.StandardButton.No),
                  buttonDefault = QMessageBox.StandardButton.Yes)
        dlg.show()

        #---------------------------------------------------------------------------------------------------------------
        dlg = cls(title         = "Field Dialog with Yes-No Button with timeout",
                  instruction   = "Press NO",
                  buttonStyle   = (QMessageBox.StandardButton.Yes  | QMessageBox.StandardButton.No),
                  buttonDefault = QMessageBox.StandardButton.Yes,
                  timeout       = 3.0)
        dlg.show()


#-----------------------------------------------------------------------------------------------------------------------
class FwDialogOk(_FwDialog):

    def __init__(self, title, text, timeout = None, notifyDelay = None, logger = None, parent = None) -> None:

        super().__init__(title = title,
                         text = text,
                         buttonStyle = QMessageBox.StandardButton.Ok,
                         buttonDefault = QMessageBox.StandardButton.Ok,
                         timeout = timeout,
                         notifyDelay = notifyDelay,
                         logger = logger,
                         parent = parent)


#-----------------------------------------------------------------------------------------------------------------------
class FwDialogYesNo(_FwDialog):

    def __init__(self, title, text,  timeout = None, notifyDelay = None, logger = None, parent = None) -> None:

        super().__init__(title = title,
                         text = text,
                         buttonStyle = (QMessageBox.StandardButton.Yes |
                                        QMessageBox.StandardButton.No),
                         buttonDefault = QMessageBox.StandardButton.Yes,
                         timeout = timeout,
                         notifyDelay   = notifyDelay,
                         logger = logger,
                         parent = parent)

#-----------------------------------------------------------------------------------------------------------------------
class FwDialogNoYes(_FwDialog):

    def __init__(self, title, text,  timeout = None, notifyDelay = None, logger = None, parent = None) -> None:

        super().__init__(title = title,
                         text = text,
                         buttonStyle = (QMessageBox.StandardButton.Yes |
                                        QMessageBox.StandardButton.No),
                         buttonDefault = QMessageBox.StandardButton.No,
                         timeout = timeout,
                         notifyDelay = notifyDelay,
                         logger = logger,
                         parent = parent)

#-----------------------------------------------------------------------------------------------------------------------
class FwInstructDialogOk(FwInstructDialog):

    def __init__(self, title, instruction, fieldList = None, dataDict = None, infoText = None, imageFilePath = None,
                 timeout = None, notifyDelay = None, logger = None, parent = None) -> None:

        super().__init__(title = title,
                         instruction = instruction,
                         fieldList = fieldList,
                         dataDict = dataDict,
                         infoText = infoText,
                         imageFilePath = imageFilePath,
                         buttonStyle = QMessageBox.StandardButton.Ok,
                         buttonDefault = QMessageBox.StandardButton.Ok,
                         timeout = timeout,
                         notifyDelay = notifyDelay,
                         logger = logger,
                         parent = parent)

#-------------------------------------------------------------------------------
class FwInstructDialogYesNo(FwInstructDialog):

    def __init__(self, title, instruction, fieldList = None, dataDict = None, infoText = None, imageFilePath = None,
                 timeout = None, notifyDelay = None, logger = None, parent = None) -> None:

        super().__init__(title = title,
                         instruction = instruction,
                         fieldList = fieldList,
                         dataDict = dataDict,
                         infoText = infoText,
                         imageFilePath = imageFilePath,
                         buttonStyle = (QMessageBox.StandardButton.Yes |
                                        QMessageBox.StandardButton.No),
                         buttonDefault = QMessageBox.StandardButton.Yes,
                         timeout = timeout,
                         notifyDelay = notifyDelay,
                         logger = logger,
                         parent = parent)

#-------------------------------------------------------------------------------
class FwInstructDialogNoYes(FwInstructDialog):

    def __init__(self, title, instruction, fieldList = None, dataDict = None, infoText = None, imageFilePath = None,
                 timeout = None, notifyDelay = None, logger = None, parent = None) -> None:

        super().__init__(title = title,
                         instruction = instruction,
                         fieldList = fieldList,
                         dataDict = dataDict,
                         infoText = infoText,
                         imageFilePath = imageFilePath,
                         buttonStyle = (QMessageBox.StandardButton.Yes |
                                        QMessageBox.StandardButton.No),
                         buttonDefault = QMessageBox.StandardButton.No,
                         timeout = timeout,
                         notifyDelay = notifyDelay,
                         logger = logger,
                         parent = parent)


if __name__ == '__main__':
    _FwDialog._test()
    FwInstructDialog._test()
