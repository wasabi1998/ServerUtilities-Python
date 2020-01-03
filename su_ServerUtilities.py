#!/usr/bin/env python
# _*_ coding: utf-8 _*_
import cx_Oracle
import re, os, sys
# import time
# import pandas as pd
# import win32api, win32con

import sqlite3
#
import paramiko
# from pkg_resources import NotADirectoryError, PermissionError
import xlsxwriter

import su_connection_index
import su_connection_add
import su_connection_addhost
import su_connection_modify
import su_connection_client
import su_connection_export

import su_module_index

#
from PyQt4 import QtCore, QtGui, Qt

global appName
appName = r'ServerUtilities'
global installDir
installDir = os.path.expandvars('$APPDATA') + r'/' + appName
global configDir
configDir = os.path.expandvars('$APPDATA') + r'/' + appName
global sqlitedb
sqlitedb = configDir + r'/' + appName + r'.db'
global sessionfile
sessionfile = configDir + r'/' + r'session.ini'
global tbRegistryDB
tbRegistryDB = r'registryDB'
# global tbRegistryDBSummary
# tbRegistryDBSummary = r'registryDBSummary'
global tbRegistryServer
tbRegistryServer = r'registryServer'
# global tbRegistry
# tbRegistry = r'registry'
# global tbLoginDetail
# tbLoginDetail = r'loginDetail'
global pathExportDir
pathExportDir = r'E:\servers\inspection'

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s
try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class MainWindow(QtGui.QMainWindow):
    def __init__(self,parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.main = su_connection_index.Ui_MainWindow()
        self.main.setupUi(self)

        try:
            if not os.path.exists(installDir):
                os.makedirs(installDir)
            if not os.path.exists(configDir):
                os.makedirs(configDir)
        except Exception, error:
            msg = 'installation failed\n' + format(error)
            QtGui.QMessageBox.warning(self, 'Error', msg)
            sys.exit(1)
        # database varchar(128),
        tbRegistryDBSQL = '''CREATE TABLE ''' + tbRegistryDB + ''' (
                id integer PRIMARY KEY AUTOINCREMENT,
                alias varchar(128),
                hostname varchar(128),
                host varchar(128),
                port varchar(128),
                user varchar(128),
                password varchar(128),
                serviceName varchar(128),
                instanceName varchar(128),
                defaultRole varchar(128),
                clientName varchar(128),
                UNIQUE([host], [user], [instanceName]))'''
        # tbRegistryDBSummarySQL = '''create table ''' + tbRegistryDBSummary + ''' (
        #                         id integer primary key autoincrement,
        #                         alias varchar(128),
        #                         database varchar(128),
        #                         host varchar(128),
        #                         user varchar(128),
        #                         defaultRole varchar(128),
        #                         instanceName varchar(128),
        #                         instanceName varchar(128),
        #                         clientHome varchar(128))'''
        tbRegistryServerSQL = '''create table ''' + tbRegistryServer + ''' (
                id integer primary key autoincrement,
                hostname varchar(128),
                host varchar(128),
                port varchar(128),
                user varchar(128),
                password varchar(128),
                privatekey varchar(128),
                UNIQUE([host], [user]))'''
        # tbLoginDetailSQL = '''create table ''' + tbLoginDetail + ''' (
        #         id integer primary key autoincrement,
        #         alias varchar(128),
        #         database varchar(128),
        #         host varchar(128),
        #         port varchar(128),
        #         user varchar(128),
        #         password varchar(128),
        #         instanceName varchar(128),
        #         instanceName varchar(128),
        #         defaultRole varchar(128))'''
        conn = sqlite3.connect(sqlitedb)
        cursor01 = conn.cursor()
        # cursor02 = conn.cursor()
        cursor03 = conn.cursor()
        cursor04 = conn.cursor()
        cursor01.execute(
            """select name from sqlite_master
            where type='table' and name=?""", (tbRegistryDB,))
        # cursor02.execute(
        #     """select name from sqlite_master
        #     where type='table' and name=?""", (tbRegistryDBSummary,))
        cursor03.execute(
            """select name from sqlite_master
            where type='table' and name=?""", (tbRegistryServer,))
        # cursor04.execute("""select name from sqlite_master
        #     where type='table' and name=?""", (tbLoginDetail,))
        tbRegistryDBInfo = cursor01.fetchall()
        # tbRegistryDBSummaryInfo = cursor02.fetchall()
        tbRegistryServerInfo = cursor03.fetchall()
        tbLoginDetailInfo = cursor04.fetchall()

        if len(tbRegistryDBInfo) == 0:
            cursor01.execute(tbRegistryDBSQL)
        # if len(tbRegistryDBSummaryInfo) == 0:
        #     cursor02.execute(tbRegistryDBSummarySQL)
        if len(tbRegistryServerInfo) == 0:
            cursor03.execute(tbRegistryServerSQL)
        # if len(tbLoginDetailInfo) == 0:
        #     cursor04.execute(tbLoginDetailSQL)
        cursor01.close()
        # cursor02.close()
        cursor03.close()
        # cursor04.close()
        conn.close()

        self.toolBar()
        self.connectionDisplay()
        self.statusBar().showMessage('Ready')
        # self.connectionmodifywidget = WidgetConnectionRescan()
        self.connectionaddwidget = WidgetConnectionAdd()
        # self.connectionmodifywidget = WidgetConnectionDelete()
        self.connectionmodifywidget = WidgetConnectionModify()
        self.connectionclientwidget = WidgetConnecionClient()
        self.connectionexportwidget = WidgetConnecionExport()

        self.module_index_mainwindow = MainWindowModuleIndex()

        self.connect(self.main.tableWidget, QtCore.SIGNAL("itemClicked (QTableWidgetItem*)"), self.outSelect)

        self.main.toolButton.clicked.connect(self.connectionDisplay)
        self.main.toolButton_2.clicked.connect(self.connectionAddWidget)
        self.main.toolButton_3.clicked.connect(self.connectionModifyWidget)
        self.main.toolButton_4.clicked.connect(self.connectionExportWidget)
        self.main.toolButton_5.clicked.connect(self.connectionFilter)
        self.main.toolButton_6.clicked.connect(self.connectionClientWidget)

        # self.main.lineEdit.returnPressed.connect(self.oraLogin)
        self.main.pushButton.clicked.connect(self.connectLogin)
        self.main.pushButton_2.clicked.connect(self.serverUltililtyClose)
    def toolBar(self):
        toolbar = self.addToolBar(u'ToolBar')
        # 建立export动作
        actionExport = QtGui.QAction(QtGui.QIcon(r'picturePath'), r'Export', self)
        # actionExport.setCheckable(True)
        actionExport.setShortcut("Ctrl+Alt+E")
        actionExport.setObjectName(_fromUtf8("actionExport"))
        actionExport.setText(_translate("MainWindow", "Export", None))
        actionExport.setToolTip(_translate("MainWindow", "Export", None))
        actionExport.setStatusTip(u'Exporting...')
        actionExport.connect(actionExport, QtCore.SIGNAL('triggered()'), self.connectionExportWidget)
        toolbar.addAction(actionExport)
        # 建立action动作，
        login = QtGui.QAction(QtGui.QIcon(r'picturePath'), r'Login', self)
        login.setShortcut('Ctrl+L')
        login.setStatusTip(u'Connecting...')
        login.connect(login, QtCore.SIGNAL('triggered()'), QtGui.qApp, QtCore.SLOT('quit()'))
        toolbar.addAction(login)
        # self.statusBar()

        quit = QtGui.QAction(QtGui.QIcon(r'picturePath'), r'Quit', self)
        quit.setShortcut('Ctrl+Q')
        quit.setStatusTip(u'Quit Appliaction.')
        quit.connect(quit, QtCore.SIGNAL('triggered()'), QtGui.qApp, QtCore.SLOT('quit()'))
        toolbar.addAction(quit)
    def outSelect(self, Item=None):
        # if Item==None:
        #     return
        #
        # print(Item.text())
        contextRowSelected = []
        curRowIdx = self.main.tableWidget.currentIndex().row()
        items = self.main.tableWidget.selectedItems()
        colsNum = len(items)
        for col in range(0, colsNum):
            content = unicode(self.main.tableWidget.item(curRowIdx, col).text()).encode('utf-8').strip()
            contextRowSelected.append(content)
        # for col in range(0, colsNum):
            # index = QtCore.QModelIndex.li
            # item = QtGui.QTableWidgetItem(curRowNum, col)
            # itemContext = unicode(item.text()).encode('utf-8').strip()
            # contextRowSelected = contextRowSelected.append(itemContext)

        # count = items.count()
        # for col in range(0, colsNum):
        #     item = QtGui.QTableWidgetItem(curRowNum, col)
        #     itemContext = unicode(item.text()).encode('utf-8').strip()
        #     contextRowSelected = contextRowSelected.append(itemContext)
    def check_ip(self, ipAddr):
        compileip = re.compile(
            '^(1\d{2}|2[0-4]\d|25[0-5]|[1-9]\d|[1-9])\.(1\d{2}|2[0-4]\d|25[0-5]|[1-9]\d|\d)\.(1\d{2}|2[0-4]\d|25[0-5]|[1-9]\d|\d)\.(1\d{2}|2[0-4]\d|25[0-5]|[1-9]\d|\d)$')
        if compileip.match(ipAddr):
            return True
        else:
            return False
    def check_port(self, port):
        compileport = re.compile(
            '^([0-9]|[1-9]\d{1,3}|[1-5]\d{4}|6[0-4]\d{4}|65[0-4]\d{2}|655[0-2]\d|6553[0-5])$')
        if compileport.match(port):
            return True
        else:
            return False
    def check_strings(self, str):
        if len(str) != 0:
            return True
        else:
            return False
    def connectionTableWidget(self):
        pass
    def connectionAddWidget(self):
        try:
            self.connectionaddwidget.close()
            self.connectionaddwidget.show()
        except Exception, error:
            msg = 'Error, ' + unicode(error)
            QtGui.QMessageBox.about(self, 'About', msg)
    def connectionModifyWidget(self):
        try:
            self.connectionmodifywidget.close()
            self.connectionmodifywidget.show()
        except Exception, error:
            msg = 'Error, ' + unicode(error)
            QtGui.QMessageBox.about(self, 'About', msg)
    def connectionExportWidget(self):
        try:
            conn = sqlite3.connect(sqlitedb)
            cursor = conn.cursor()
            cursor.execute(
                """SELECT HOST FROM """ + tbRegistryServer)
            availHostList = cursor.fetchall()
            conn.close()
            self.connectionexportwidget.ui.listWidget.clearFocus()
            self.connectionexportwidget.ui.listWidget.clear()
            for availHost in availHostList:
                self.connectionexportwidget.ui.listWidget.addItem(''.join(availHost))

        except sqlite3.IntegrityError as error:
            msg = 'Error. Initial available host failed.\n' + format(error)
            QtGui.QMessageBox.about(self, 'About', msg)
        # else:
            # msg = 'OK, Initial available host succeeded.'
            # QtGui.QMessageBox.about(self, 'About', msg)
        try:
            self.connectionexportwidget.close()
            self.connectionexportwidget.show()
        except Exception, error:
            msg = 'Error, Display Export Widget Failed' + unicode(error)
            QtGui.QMessageBox.about(self, 'About', msg)
    def connectionDelete(self):
        pass
    def connectionDisplay(self):
        conn = sqlite3.connect(sqlitedb)
        cursor1 = conn.cursor()
        # cursor2 = conn.cursor()
        # allRowsDataSQL = """select alias,user||'@' ||host||':'||port||'/'||instanceName as database,host,user,password,instanceName,instanceName,connectas from """ + tbRegistryDB
        allRowsDataSQL = """select id,alias,user||'@' ||host||':'||port||'/'||instanceName,host,port,user,defaultRole,serviceName,instanceName,clientName from """ + tbRegistryDB

        # allColNameSQL = """PRAGMA table_info([""" + tbRegistryDB + """])"""
        cursor1.execute(allRowsDataSQL)
        # cursor2.execute(allColNameSQL)
        # cursor2.execute(execCountSQL)
        allRowsDataresult = cursor1.fetchall()
        # allColNameresult = cursor2.fetchall()
        cursor1.close()
        # cursor2.close()
        conn.close()
        # colNum = len(allRowsDataresult[0])
        # colNameList = []
        # for column in allColNameresult:
        #     colNameList.append(column[1])
        # colNameList.insert(2,'database')
        # 清理数据
        self.main.tableWidget.clearFocus()
        self.main.tableWidget.clearContents()
        clearRowNum = self.main.tableWidget.rowCount()
        for i in range(0, clearRowNum)[::-1]:
            self.main.tableWidget.removeRow(i)
        colNameList = ['id', 'alias', 'database', 'host', 'port', 'user', 'defaultRole','serviceName','instanceNmae', 'clientName']
        # 设置表头
        self.main.tableWidget.setColumnCount(len(colNameList))
        # self.main.tableWidget.setRowCount(len(allRowsDataresult))
        textFont = QtGui.QFont("song", 10, QtGui.QFont.Bold)
        for i in range(0, len(colNameList)):
            item = QtGui.QTableWidgetItem()
            self.main.tableWidget.setHorizontalHeaderItem(i, item)
            item = self.main.tableWidget.horizontalHeaderItem(i)
            item.setText(_translate("MainWindow", colNameList[i].capitalize(), None))
            item.setFont(textFont)  # 设置字体
            item.setBackgroundColor(QtGui.QColor(0, 128, 0))  # 设置单元格背景颜色
            item.setTextColor(QtGui.QColor(0, 0, 0))  # 设置文字颜色
        # 写入数据
        for row in allRowsDataresult:
            i = allRowsDataresult.index(row)
            rowcount = self.main.tableWidget.rowCount()
            self.main.tableWidget.insertRow(rowcount)
            for j in range(0, len(row)):
                # item = QtGui.QTableWidgetItem()
                text = str(unicode(row[j]).encode('utf-8')).strip()
                self.main.tableWidget.setItem(i, j, QtGui.QTableWidgetItem(text))
                self.main.tableWidget.resizeColumnsToContents()  # 将列调整到跟内容大小相匹配
                self.main.tableWidget.resizeRowsToContents()  # 将行大小调整到跟内容的大学相匹配
                self.main.tableWidget.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
                self.main.tableWidget.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
    def connectionFilter(self):
        try:
            text = unicode(self.main.lineEdit.text()).encode('utf-8').strip()
            # 遍历表查找对应的item
            item = self.main.tableWidget.findItems(text, QtCore.Qt.MatchRegExp)
            # 获取其行号
            row = item[0].row()
            # 滚轮定位过去
            self.main.tableWidget.verticalScrollBar().setSliderPosition(row)
            self.main.tableWidget.setStyleSheet("selection-background-color:rgb(0,255,128)")
            self.main.tableWidget.selectRow(row)
        except Exception, error:
            msg = 'Warn, No items match your search'
            QtGui.QMessageBox.about(self, 'About', msg)
    def connectionClientWidget(self):
        try:
            self.connectionclientwidget.close()
            self.connectionclientwidget.show()
        except Exception, error:
            msg = 'Error, ' + unicode(error)
            QtGui.QMessageBox.about(self, 'About', msg)
    def connectLogin(self):
        rowClicked = []
        curRowIdx = self.main.tableWidget.currentIndex().row()
        items = self.main.tableWidget.selectedItems()
        for col in range(0, len(items)):
            content = unicode(self.main.tableWidget.item(curRowIdx, col).text()).encode('utf-8').strip()
            rowClicked.append(content)
        if len(rowClicked) != 0:
            connStatus = r'True'
            try:
                oraHostTmp = rowClicked[3]
                oraUserTmp = rowClicked[5]
                oraSIDTmp = rowClicked[8]
                conn = sqlite3.connect(sqlitedb)
                cursor = conn.cursor()
                cursor.execute(
                    """select port,password from """ + tbRegistryDB + """ where host=? and user=? and instanceName=?""",
                    (oraHostTmp,oraUserTmp,oraSIDTmp,))
                resultList = cursor.fetchall()
                conn.close()
                if len(resultList) == 1:
                    curOraHost = oraHostTmp
                    curOraPort = resultList[0][0]
                    curOraUser = oraUserTmp
                    curOraPassword = resultList[0][1]
                    curOraSID = oraSIDTmp
                    curOraDSN = cx_Oracle.makedsn(curOraHost, curOraPort, curOraSID, region=None, sharding_key=None, super_sharding_key=None)
            except Exception, error:
                msg = 'Error, Account verification failed.\n' + unicode(error)
                QtGui.QMessageBox.about(self, 'About', msg)

            try:
                connection = cx_Oracle.connect(curOraUser, curOraPassword, curOraDSN, cx_Oracle.SYSDBA)
                cursor1 = connection.cursor()
                cursor2 = connection.cursor()
                cursor1.execute(
                    r"select name as dbName, db_unique_name as dbUName, open_mode, platform_name from v$database")
                cursor2.execute(r"select host_name, version, instance_name from v$instance")
                dbresultList = cursor1.fetchall()
                instresultList = cursor2.fetchall()
                cursor1.close()
                cursor2.close()
                connection.close()
                summaryList = []
                if len(dbresultList) != 0 and len(dbresultList) != 0:
                    summaryList = instresultList + dbresultList
                    self.module_index_mainwindow.ui.label_3.setText(summaryList[0][0])
                    self.module_index_mainwindow.ui.label_4.setText(summaryList[0][1])
                    self.module_index_mainwindow.ui.label_5.setText(summaryList[0][2])
                    self.module_index_mainwindow.ui.label_6.setText(summaryList[1][0])
                    self.module_index_mainwindow.ui.label_7.setText(summaryList[1][1])
                    self.module_index_mainwindow.ui.label_8.setText(summaryList[1][2])
                    self.module_index_mainwindow.ui.label_9.setText(summaryList[1][3])
                else:
                    self.module_index_mainwindow.ui.label_3.clear()
                    self.module_index_mainwindow.ui.label_4.clear()
                    self.module_index_mainwindow.ui.label_5.clear()
                    self.module_index_mainwindow.ui.label_6.clear()
                    self.module_index_mainwindow.ui.label_7.clear()
                    self.module_index_mainwindow.ui.label_8.clear()
                    self.module_index_mainwindow.ui.label_9.clear()
            except Exception, error:
                msg = 'Error, Login failed(can not connect to oracle).\n' + unicode(error)
                QtGui.QMessageBox.about(self, 'About', msg)
            else:
                connectionas = curOraUser + r'@' + curOraHost + r':' + curOraPort + r'/' + curOraSID
                conn = sqlite3.connect(sqlitedb)
                cursor = conn.cursor()
                cursor.execute("""select host,port,user,instanceName from """ + tbRegistryDB)
                dbStrList = cursor.fetchall()
                conn.close()
                if dbStrList:
                    self.module_index_mainwindow.ui.comboBox.clearFocus()
                    self.module_index_mainwindow.ui.comboBox.clear()
                    for n in range(0, len(dbStrList)):
                        dbStr = dbStrList[n][2] + r'@' + dbStrList[n][0] + r':' + dbStrList[n][1] + r'/' + dbStrList[n][3]
                        self.module_index_mainwindow.ui.comboBox.addItem(dbStr)
                idx = self.module_index_mainwindow.ui.comboBox.findText(connectionas)
                self.module_index_mainwindow.ui.comboBox.setCurrentIndex(idx)

                self.module_index_mainwindow.close()
                self.module_index_mainwindow.show()
        else:
            connStatus = r'False'
            conn = sqlite3.connect(sqlitedb)
            cursor = conn.cursor()
            cursor.execute("""select host,port,user,instanceName from """ + tbRegistryDB)
            dbStrList = cursor.fetchall()
            conn.close()
            if dbStrList:
                self.module_index_mainwindow.ui.comboBox.clearFocus()
                self.module_index_mainwindow.ui.comboBox.clear()
                for n in range(0, len(dbStrList)):
                    dbStr = dbStrList[n][2] + r'@' + dbStrList[n][0] + r':' + dbStrList[n][1] + r'/' + dbStrList[n][3]
                    self.module_index_mainwindow.ui.comboBox.addItem(dbStr)
            self.module_index_mainwindow.ui.comboBox.setCurrentIndex(-1)
            self.module_index_mainwindow.ui.groupBox.setTitle('No Connection(IDLE)')
            summaryList = []
            if len(summaryList) == 0:
                self.module_index_mainwindow.ui.label_3.clear()
                self.module_index_mainwindow.ui.label_4.clear()
                self.module_index_mainwindow.ui.label_5.clear()
                self.module_index_mainwindow.ui.label_6.clear()
                self.module_index_mainwindow.ui.label_7.clear()
                self.module_index_mainwindow.ui.label_8.clear()
                self.module_index_mainwindow.ui.label_9.clear()
            self.module_index_mainwindow.close()
            self.module_index_mainwindow.show()
        #     msg = 'Error, Unable to find database server.'
        #     QtGui.QMessageBox.about(self, 'About', msg)

    def serverUltililtyClose(self):
        sys.exit(1)

class WidgetConnectionAdd(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.ui = su_connection_add.Ui_Form()
        self.ui.setupUi(self)

        self.connServerAddWidget = WidgetConnectionAddServer()

        self.ui.toolButton.clicked.connect(self.oraConnClient)
        self.ui.toolButton_2.clicked.connect(self.oraConnstoreVault)
        self.ui.toolButton_3.clicked.connect(self.oraConnVaultClear)
        self.ui.pushButton.clicked.connect(self.connAddServerWidget)
        self.ui.pushButton_2.clicked.connect(self.oraConnTest)
        self.ui.pushButton_3.clicked.connect(self.oraConnRegistry)
        self.ui.pushButton_4.clicked.connect(self.oraConnCancel)

        # self.ui.comboBox.activated[str].connect(self.connMethod)
    def oraConnMethod(self):
        string = unicode(self.ui.comboBox.currentText()).encode('utf-8').strip()
        if string == r'Standard(TCP/IP)':
            self.oraProtocal = r'TCPIP'
        elif string == r'Standard(TCP/IP) over SSH':
            self.oraProtocal = r'TCPIPOVERSSH'
        elif string == r'Local Socket/Pipe':
            self.oraProtocal = r'LOCALSOCKETPIPE'
        else:
            self.oraProtocal = r''
            msg = 'Failed. Illegal communication protocol.\n'
            QtGui.QMessageBox.about(self, 'About', msg)
    def oraConnConfingure(self):
        self.oraConnMethod()
        self.oraAlias = unicode(self.ui.lineEdit.text()).encode('utf-8').strip()
        if self.oraProtocal == r'TCPIP':
            # connMethod = unicode(self.ui.comboBox.currentText()).encode('utf-8').strip()
            self.oraHost = unicode(self.ui.lineEdit_2.text()).encode('utf-8').strip()
            self.oraPort = str(unicode(self.ui.lineEdit_3.text()).encode('utf-8').strip())
            self.oraUsername = unicode(self.ui.lineEdit_4.text()).encode('utf-8').strip()
            self.oraPassword = unicode(self.ui.lineEdit_5.text()).encode('utf-8').strip()
            self.oraService = unicode(self.ui.lineEdit_6.text()).encode('utf-8').strip()
            self.oraInstance = unicode(self.ui.lineEdit_7.text()).encode('utf-8').strip()
            self.oraDSNSID = cx_Oracle.makedsn(self.oraHost, self.oraPort, sid=self.oraInstance, region=None,
                                                sharding_key=None,
                                                super_sharding_key=None)
            self.oraDSNService = cx_Oracle.makedsn(self.oraHost, self.oraPort, service_name=self.oraService,
                                                region=None,
                                                sharding_key=None, super_sharding_key=None)
            if unicode(self.ui.lineEdit_4.text()).encode('utf-8').strip().upper() == r'SYS':
                idx = self.ui.comboBox_3.findText('SYSDBA')
                self.ui.comboBox_3.setCurrentIndex(idx)
            elif unicode(self.ui.lineEdit_4.text()).encode('utf-8').strip().upper() == r'SYSTEM':
                idx = self.ui.comboBox_3.findText('NORMAL')
                self.ui.comboBox_3.setCurrentIndex(idx)
            elif unicode(self.ui.lineEdit_4.text()).encode('utf-8').strip().upper() == r'PUBLIC':
                idx = self.ui.comboBox_3.findText('SYSOPER')
                self.ui.comboBox_3.setCurrentIndex(idx)
            else:
                idx = self.ui.comboBox_3.findText('NORMAL')
                self.ui.comboBox_3.setCurrentIndex(idx)

            if len(self.ui.comboBox_3.currentText()) == 0:
                self.oraDefaultRole = 'NORMAL'
            else:
                self.oraDefaultRole = unicode(self.ui.comboBox_3.currentText()).encode('utf-8').strip()
        elif self.oraProtocal == r'TCPIPOVERSSH':
            msg = 'Failed. Temporarily not supported Standard (TCP/IP) over SSH .\n'
            QtGui.QMessageBox.about(self, 'About', msg)
        elif self.oraProtocal == r'LOCALSOCKETPIPE':
            msg = 'Failed, Temporarily not supported Local Socket/Pipe.\n'
            QtGui.QMessageBox.about(self, 'About', msg)
        else:
            msg = 'Failed. Please specify a supported communication protocol.\n'
            QtGui.QMessageBox.about(self, 'About', msg)
    def oraConnClient(self):
        pass
    def oraConnstoreVault(self):
        pass
    def oraConnVaultClear(self):
        pass
    def oraConnTest(self):
        self.oraConnConfingure()
        if self.oraProtocal == r'TCPIP':
            # self.cx_OracleMode = r'cx_Oracle.' + self.oraDefaultRole.upper()
            try:
                if self.oraDefaultRole == r'SYSDBA':
                    connection = cx_Oracle.connect(self.oraUsername, self.oraPassword, self.oraDSNService,
                                                   mode=cx_Oracle.SYSDBA)
                elif self.oraDefaultRole == r'SYSOPER':
                    connection = cx_Oracle.connect(self.oraUsername, self.oraPassword, self.oraDSNService,
                                                   mode=cx_Oracle.SYSOPER)
                elif self.oraDefaultRole == r'NORMAL':
                    connection = cx_Oracle.connect(self.oraUsername, self.oraPassword, self.oraDSNService)
                elif self.oraDefaultRole == r'SYSASM':
                    connection = cx_Oracle.connect(self.oraUsername, self.oraPassword, self.oraDSNService,
                                                   mode=cx_Oracle.SYSASM)
                else:
                    connection = cx_Oracle.connect(self.oraUsername, self.oraPassword, self.oraDSNService)
            except cx_Oracle.DatabaseError as error:
                msg = 'Error. Test connection Service failed.\n' + format(error)
                QtGui.QMessageBox.about(self, 'About', msg)
            else:
                self.dbConnService = True
                msg = 'OK. Test connection Service successfully.\n'
                QtGui.QMessageBox.about(self, 'About', msg)
            try:
                if self.oraDefaultRole == r'SYSDBA':
                    connection = cx_Oracle.connect(self.oraUsername, self.oraPassword, self.oraDSNSID,
                                                   mode=cx_Oracle.SYSDBA)
                elif self.oraDefaultRole == r'SYSOPER':
                    connection = cx_Oracle.connect(self.oraUsername, self.oraPassword, self.oraDSNSID,
                                                   mode=cx_Oracle.SYSOPER)
                elif self.oraDefaultRole == r'NORMAL':
                    connection = cx_Oracle.connect(self.oraUsername, self.oraPassword, self.oraDSNSID)
                elif self.oraDefaultRole == r'SYSASM':
                    connection = cx_Oracle.connect(self.oraUsername, self.oraPassword, self.oraDSNSID,
                                                   mode=cx_Oracle.SYSASM)
                else:
                    connection = cx_Oracle.connect(self.oraUsername, self.oraPassword, self.oraDSNSID)
            except cx_Oracle.DatabaseError as error:
                msg = 'Error. Test connection SID failed.\n' + format(error)
                QtGui.QMessageBox.about(self, 'About', msg)
            else:
                self.dbConnSID = True
                msg = 'OK. Test connection SID successfully.\n'
                QtGui.QMessageBox.about(self, 'About', msg)
        elif self.connProtocal == r'TCPIPOVERSSH':
            msg = 'Error. Test connection failed.\n'
            QtGui.QMessageBox.about(self, 'About', msg)
        elif self.connProtocal == r'LOCALSOCKETPIPE':
            msg = 'Error. Test connection failed.\n'
            QtGui.QMessageBox.about(self, 'About', msg)
        else:
            msg = 'Error. Test connection failed.\n' + 'Temporarily not supported Local Socket/Pipe.'
            QtGui.QMessageBox.about(self, 'About', msg)
    def oraConnRegistry(self):
        self.oraConnConfingure()
        if self.oraProtocal == r'TCPIP':
            # self.cx_OracleMode = r'cx_Oracle.' + self.oraDefaultRole.upper()
            try:
                if self.oraDefaultRole == r'SYSDBA':
                    connection = cx_Oracle.connect(self.oraUsername, self.oraPassword, self.oraDSNService,
                                                   mode=cx_Oracle.SYSDBA)
                elif self.oraDefaultRole == r'SYSOPER':
                    connection = cx_Oracle.connect(self.oraUsername, self.oraPassword, self.oraDSNService,
                                                   mode=cx_Oracle.SYSOPER)
                elif self.oraDefaultRole == r'NORMAL':
                    connection = cx_Oracle.connect(self.oraUsername, self.oraPassword, self.oraDSNService)
                elif self.oraDefaultRole == r'SYSASM':
                    connection = cx_Oracle.connect(self.oraUsername, self.oraPassword, self.oraDSNService,
                                                   mode=cx_Oracle.SYSASM)
                else:
                    connection = cx_Oracle.connect(self.oraUsername, self.oraPassword, self.oraDSNService)
            except cx_Oracle.DatabaseError as error:
                self.dbConnService = False
                # msg = 'Error. Test connection Service failed.\n' + format(error)
                # QtGui.QMessageBox.about(self, 'About', msg)
            else:
                self.dbConnService = True
            #     msg = 'OK. Test connection Service successfully.\n'
            #     QtGui.QMessageBox.about(self, 'About', msg)
            try:
                if self.oraDefaultRole == r'SYSDBA':
                    connection = cx_Oracle.connect(self.oraUsername, self.oraPassword, self.oraDSNSID,
                                                   mode=cx_Oracle.SYSDBA)
                elif self.oraDefaultRole == r'SYSOPER':
                    connection = cx_Oracle.connect(self.oraUsername, self.oraPassword, self.oraDSNSID,
                                                   mode=cx_Oracle.SYSOPER)
                elif self.oraDefaultRole == r'NORMAL':
                    connection = cx_Oracle.connect(self.oraUsername, self.oraPassword, self.oraDSNSID)
                elif self.oraDefaultRole == r'SYSASM':
                    connection = cx_Oracle.connect(self.oraUsername, self.oraPassword, self.oraDSNSID,
                                                   mode=cx_Oracle.SYSASM)
                else:
                    connection = cx_Oracle.connect(self.oraUsername, self.oraPassword, self.oraDSNSID)
            except cx_Oracle.DatabaseError as error:
                self.dbConnSID = False
                # msg = 'Error. Test connection SID failed.\n' + format(error)
                # QtGui.QMessageBox.about(self, 'About', msg)
            else:
                self.dbConnSID = True
            #     msg = 'OK. Test connection SID successfully.\n'
            #     QtGui.QMessageBox.about(self, 'About', msg)
        if self.dbConnService == True and self.dbConnSID == True:
            hostnamesql = r"select host_name from v$instance"
            connection = cx_Oracle.connect(self.oraUsername, self.oraPassword, self.oraDSNSID,mode=cx_Oracle.SYSDBA)
            cursor = connection.cursor()
            cursor.execute(hostnamesql)
            hostnamesqlList = cursor.fetchall()
            cursor.close()
            connection.close()
            if hostnamesqlList:
                self.oraHostname = hostnamesqlList[0][0]
            self.database = self.oraUsername + r'@' + self.oraHost + r':' + self.oraPort + r'/' + self.oraInstance
            self.clientHome = 'OraHome1'
            # addDBinfo = (self.oraAlias, self.oraHost, self.oraUsername, self.oraPassword, self.oraPort, self.oraService, self.oraInstance, self.oraDefaultRole)
            # addDBSummary = (self.oraAlias, self.database, self.oraHost, self.oraUsername, self.oraDefaultRole, self.oraService, self.oraInstance, self.clientHome)
            addDBinfo = (self.oraAlias, self.oraHostname, self.oraHost, self.oraPort, self.oraUsername, self.oraPassword,
                         self.oraService, self.oraInstance, self.oraDefaultRole, self.clientHome)
            try:
                conn = sqlite3.connect(sqlitedb)
                cursor1 = conn.cursor()
                # cursor2 = conn.cursor()
                cursor1.execute(
                    """INSERT INTO """ + tbRegistryDB + """(alias, hostname, host, port, user, password, serviceName, instanceName, defaultRole, clientName) VALUES (?,?,?,?,?,?,?,?,?,?)""", addDBinfo)
                cursor1.close()
                # cursor2.execute(
                #     """INSERT INTO """ + tbRegistryDBSummary + """(alias, database, host, user, defaultRole, instanceName, instanceName, clientHome) VALUES (?,?,?,?,?,?,?,?)""",
                #     addDBSummary)
                # cursor2.close()
                conn.commit()
                conn.close()
            except Exception, error:
                msg = 'Error. Registry database Failed.\n' + format(error)
                QtGui.QMessageBox.about(self, 'About', msg)
            else:
                msg = 'OK.Registry database successfully.'
                QtGui.QMessageBox.about(self, 'About', msg)
        else:
            msg = 'Failed, Registry database failed.\n(Test connection failed)'
            QtGui.QMessageBox.about(self, 'About', msg)

    def oraConnSSL(self):
        pass
    def oraConnAdvanced(self):
        pass
    def connAddServerWidget(self):
        content = unicode(self.ui.lineEdit_2.text()).encode('utf-8').strip()
        self.connServerAddWidget.ui.lineEdit.setText(content)
        self.connServerAddWidget.close()
        self.connServerAddWidget.show()
    def oraConnCancel(self):
        pass
class WidgetConnectionAddServer(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.ui = su_connection_addhost.Ui_Form()
        self.ui.setupUi(self)

        self.sshPrivKeyAvail()
        self.connect(self.ui.checkBox, QtCore.SIGNAL('stateChanged(int)'), self.sshPrivKeyAvail)

        self.ui.toolButton.clicked.connect(self.searchPrivKey)
        self.ui.pushButton.clicked.connect(self.hostConnTest)
        self.ui.pushButton_2.clicked.connect(self.oraConnRegistry)
        self.ui.pushButton_3.clicked.connect(self.connHostCancel)

    def sshPrivKeyAvail(self):
        if self.ui.checkBox.isChecked():
            self.ui.label_6.setEnabled(True)
            self.ui.lineEdit_5.setEnabled(True)
            self.ui.toolButton.setEnabled(True)
        else:
            self.ui.label_6.setEnabled(False)
            self.ui.lineEdit_5.setEnabled(False)
            self.ui.toolButton.setEnabled(False)
    def searchPrivKey(self):
        if self.ui.toolButton.isEnabled():
            SSHPrikeyTmp = unicode(QtGui.QFileDialog.getOpenFileName(self, 'Select the file', os.getcwd())).encode(
                'urf-8').strip()
            self.ui.lineEdit_5.setText(SSHPrikeyTmp)
    def hostConnConfingure(self):
        self.hostTmp = unicode(self.ui.lineEdit.text()).encode('utf-8').strip()
        self.portTmp = unicode(self.ui.lineEdit_2.text()).encode('utf-8').strip()
        self.userTmp = unicode(self.ui.lineEdit_3.text()).encode('utf-8').strip()
        self.pwdTmp = unicode(self.ui.lineEdit_4.text()).encode('utf-8').strip()
        if self.ui.checkBox.isEnabled():
            self.privKeyTmp = unicode(self.ui.lineEdit_5.text()).encode('utf-8').strip()
        else:
            self.privKeyTmp = ''
    def hostConnTest(self):
        self.hostConnConfingure()
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(self.hostTmp, self.portTmp, self.userTmp, self.pwdTmp)
            ssh.close()
        except Exception, error:
            self.hostConnStatus = False
            msg = 'Error. Host connection test failed.\n' + format(error)
            QtGui.QMessageBox.about(self, 'About', msg)
        else:
            self.hostConnStatus = True
            msg = 'OK. Host connection test successfully.\n'
            QtGui.QMessageBox.about(self, 'About', msg)
    def oraConnRegistry(self):
        self.hostConnConfingure()
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(self.hostTmp, self.portTmp, self.userTmp, self.pwdTmp)
            stdin, stdout, stderr = ssh.exec_command(r"hostname")
            hostnameList = stdout.readlines()
            hostnameError = stderr.readlines()
            ssh.close()
        except Exception, error:
            self.hostConnStatus = False
            msg = 'Error. Host connection test failed.\n' + format(error)
            QtGui.QMessageBox.about(self, 'About', msg)
        else:
            self.hostConnStatus = True
            if len(hostnameError) == 0:
                self.hostnameTmp = hostnameList[0]
            # msg = 'OK. Host connection test successfully.\n'
            # QtGui.QMessageBox.about(self, 'About', msg)
        if self.hostConnStatus == True:

            try:
                conn = sqlite3.connect(sqlitedb)
                cursor = conn.cursor()
                cursor.execute(
                    """INSERT INTO """ + tbRegistryServer + """(hostname,host,port,user,password,privatekey) VALUES (?,?,?,?,?,?)""",
                    (self.hostnameTmp,self.hostTmp, self.portTmp, self.userTmp, self.pwdTmp, self.privKeyTmp,))
                cursor.close()
                conn.commit()
                conn.close()
            except sqlite3.IntegrityError as error:
                msg = 'Error. Host registration failed.\n' + format(error)
                QtGui.QMessageBox.about(self, 'About', msg)
            else:
                msg = 'OK, Host registration succeeded.'
                QtGui.QMessageBox.about(self, 'About', msg)
    def connHostCancel(self):
        pass
class WidgetConnectionModify(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.ui = su_connection_modify.Ui_Form()
        self.ui.setupUi(self)

        # self.scanSummary()
        # self.scanRegistedDB()
        # self.scanRegistedServer()

        # self.connect(self.ui.tableWidget, QtCore.SIGNAL("itemClicked (QTableWidgetItem*)"), self.rowSelectedDB)
        # self.connect(self.ui.tableWidget, QtCore.SIGNAL(_fromUtf8("itemDoubleClicked(QTableWidgetItem*)")),
        #                        self.updataDataDB)
        # QtCore.QObject.connect(self.ui.tableWidget, QtCore.SIGNAL(_fromUtf8("itemEntered(QTableWidgetItem*)")), self.updataDataDB)
        # self.connect(self.ui.tableWidget_2, QtCore.SIGNAL("itemClicked (QTableWidgetItem*)"), self.rowSelectedServer)
        # self.connect(self.tableWidget, QtCore.SIGNAL(_fromUtf8("itemDoubleClicked(QTableWidgetItem*)")),
        #                        Form.lower)
        self.ui.toolButton.clicked.connect(self.scanRegistedDB)
        self.ui.toolButton_2.clicked.connect(self.deleteDataDB)
        # self.ui.toolButton_2.clicked.connect(self.scanRegistedDB)
        self.ui.toolButton_3.clicked.connect(self.updataDataDB)
        self.ui.toolButton_4.clicked.connect(self.insertDataDB)
        self.ui.toolButton_5.clicked.connect(self.dataCommitDB)

        self.ui.toolButton_6.clicked.connect(self.scanRegistedServer)
        self.ui.toolButton_7.clicked.connect(self.deleteDataServer)
        # self.ui.toolButton_7.clicked.connect(self.scanRegistedServer)
        self.ui.toolButton_8.clicked.connect(self.updateDataServer)
        self.ui.toolButton_9.clicked.connect(self.insertDataServer)
        self.ui.toolButton_10.clicked.connect(self.dataCommitServer)


    # def scanSummary(self):
    #     conn = sqlite3.connect(sqlitedb)
    #     cursor1 = conn.cursor()
    #     cursor2 = conn.cursor()
    #     # allRowsDataSQL = """select alias,user||'@' ||host||':'||port||'/'||instanceName as database,host,user,password,instanceName,instanceName,connectas from """ + tbRegistryDB
    #     allRowsDataSQL = """select id,alias,database,host,user,defaultRole,instanceName,instanceName,clientHome from """ + tbRegistryDB
    #     allColNameSQL = """PRAGMA table_info([""" + tbRegistryDB + """])"""
    #     cursor1.execute(allRowsDataSQL)
    #     cursor2.execute(allColNameSQL)
    #     # cursor2.execute(execCountSQL)
    #     allRowsDataresult = cursor1.fetchall()
    #     allColNameresult = cursor2.fetchall()
    #     cursor1.close()
    #     cursor2.close()
    #     conn.close()
    #     # colNum = len(allRowsDataresult[0])
    #     colNameList = []
    #     for column in allColNameresult[::-1]:
    #         colNameList.append(column[1])
    #     # 清理数据
    #     self.ui.tableWidget.clearFocus()
    #     self.ui.tableWidget.clearContents()
    #     clearRowNum = self.ui.tableWidget.rowCount()
    #     for i in range(0, clearRowNum):
    #         self.ui.tableWidget.removeRow(i)
    #     # 设置表头
    #     self.ui.tableWidget.setColumnCount(len(colNameList))
    #     # self.main.tableWidget.setRowCount(len(allRowsDataresult))
    #     textFont = QtGui.QFont("song", 10, QtGui.QFont.Bold)
    #     for i in range(0, len(colNameList)):
    #         item = QtGui.QTableWidgetItem()
    #         self.ui.tableWidget.setHorizontalHeaderItem(i, item)
    #         item = self.ui.tableWidget.horizontalHeaderItem(i)
    #         item.setText(_translate("MainWindow", colNameList[i].capitalize(), None))
    #         item.setFont(textFont)  # 设置字体
    #         item.setBackgroundColor(QtGui.QColor(0, 128, 0))  # 设置单元格背景颜色
    #         item.setTextColor(QtGui.QColor(0, 0, 0))  # 设置文字颜色
    #     # 写入数据
    #     for row in allRowsDataresult:
    #         i = allRowsDataresult.index(row)
    #         rowcount = self.ui.tableWidget.rowCount()
    #         self.ui.tableWidget.insertRow(rowcount)
    #         for j in range(0, len(row)):
    #             # item = QtGui.QTableWidgetItem()
    #             text = str(unicode(row[j]).encode('utf-8')).strip()
    #             self.ui.tableWidget.setItem(i, j, QtGui.QTableWidgetItem(text))
    #             self.ui.tableWidget.resizeColumnsToContents()  # 将列调整到跟内容大小相匹配
    #             self.ui.tableWidget.resizeRowsToContents()  # 将行大小调整到跟内容的大学相匹配
    #             # self.ui.tableWidget.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
    #             # self.ui.tableWidget.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
    def scanRegistedDB(self):
        conn = sqlite3.connect(sqlitedb)
        cursor1 = conn.cursor()
        cursor2 = conn.cursor()
        # allRowsDataSQL = """select alias,user||'@' ||host||':'||port||'/'||instanceName as database,host,user,password,instanceName,instanceName,connectas from """ + tbRegistryDB
        allRowsDataSQL = """select id,alias,hostname,host,port,user,password,serviceName,instanceName,defaultRole,clientName from """ + tbRegistryDB
        allColNameSQL = """PRAGMA table_info([""" + tbRegistryDB + """])"""
        cursor1.execute(allRowsDataSQL)
        cursor2.execute(allColNameSQL)
        # cursor2.execute(execCountSQL)
        allRowsDataresult = cursor1.fetchall()
        allColNameresult = cursor2.fetchall()
        cursor1.close()
        cursor2.close()
        conn.close()
        # colNum = len(allRowsDataresult[0])
        colNameList = []
        for column in allColNameresult:
            colNameList.append(column[1])
        # 清理数据
        self.ui.tableWidget.clearFocus()
        self.ui.tableWidget.clearContents()
        clearRowNum = self.ui.tableWidget.rowCount()
        for i in range(0, clearRowNum)[::-1]:
            self.ui.tableWidget.removeRow(i)
        # 设置表头
        self.ui.tableWidget.setColumnCount(len(colNameList))
        # self.ui.tableWidget.setRowCount(len(allRowsDataresult))
        textFont = QtGui.QFont("song", 10, QtGui.QFont.Bold)
        for i in range(0, len(colNameList)):
            item = QtGui.QTableWidgetItem()
            self.ui.tableWidget.setHorizontalHeaderItem(i, item)
            item = self.ui.tableWidget.horizontalHeaderItem(i)
            item.setText(_translate("MainWindow", colNameList[i].capitalize(), None))
            item.setFont(textFont)  # 设置字体
            item.setBackgroundColor(QtGui.QColor(0, 128, 0))  # 设置单元格背景颜色
            item.setTextColor(QtGui.QColor(0, 0, 0))  # 设置文字颜色
        # 写入数据
        for row in allRowsDataresult:
            j = allRowsDataresult.index(row)
            rowcount = self.ui.tableWidget.rowCount()
            self.ui.tableWidget.insertRow(rowcount)
            for k in range(0, len(row)):
                # item = QtGui.QTableWidgetItem()
                text = str(unicode(row[k]).encode('utf-8')).strip()
                self.ui.tableWidget.setItem(j, k, QtGui.QTableWidgetItem(text))
                self.ui.tableWidget.resizeColumnsToContents()  # 将列调整到跟内容大小相匹配
                self.ui.tableWidget.resizeRowsToContents()  # 将行大小调整到跟内容的大学相匹配
                # self.ui.tableWidget.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
                # self.ui.tableWidget.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
    def scanRegistedServer(self):
        conn = sqlite3.connect(sqlitedb)
        cursor1 = conn.cursor()
        cursor2 = conn.cursor()
        # allRowsDataSQL = """select alias,user||'@' ||host||':'||port||'/'||instanceName as database,host,user,password,instanceName,instanceName,connectas from """ + tbRegistryDB
        allRowsDataSQL = """select id,hostname,host,port,user,password from """ + tbRegistryServer
        allColNameSQL = """PRAGMA table_info([""" + tbRegistryServer + """])"""
        cursor1.execute(allRowsDataSQL)
        cursor2.execute(allColNameSQL)
        # cursor2.execute(execCountSQL)
        allRowsDataresult = cursor1.fetchall()
        allColNameresult = cursor2.fetchall()
        cursor1.close()
        cursor2.close()
        conn.close()
        # colNum = len(allRowsDataresult[0])
        colNameList = []
        for column in allColNameresult:
            colNameList.append(column[1])
        # 清理数据
        self.ui.tableWidget_2.clearFocus()
        self.ui.tableWidget_2.clearContents()
        clearRowNum = self.ui.tableWidget_2.rowCount()
        for i in range(0, clearRowNum)[::-1]:
            self.ui.tableWidget_2.removeRow(i)
        # 设置表头
        self.ui.tableWidget_2.setColumnCount(len(colNameList))
        # self.main.tableWidget.setRowCount(len(allRowsDataresult))
        textFont = QtGui.QFont("song", 10, QtGui.QFont.Bold)
        for i in range(0, len(colNameList)):
            item = QtGui.QTableWidgetItem()
            self.ui.tableWidget_2.setHorizontalHeaderItem(i, item)
            item = self.ui.tableWidget_2.horizontalHeaderItem(i)
            item.setText(_translate("MainWindow", colNameList[i].capitalize(), None))
            item.setFont(textFont)  # 设置字体
            item.setBackgroundColor(QtGui.QColor(0, 128, 0))  # 设置单元格背景颜色
            item.setTextColor(QtGui.QColor(0, 0, 0))  # 设置文字颜色
        # 写入数据
        for row in allRowsDataresult:
            i = allRowsDataresult.index(row)
            rowcount = self.ui.tableWidget_2.rowCount()
            self.ui.tableWidget_2.insertRow(rowcount)
            for j in range(0, len(row)):
                # item = QtGui.QTableWidgetItem()
                text = str(unicode(row[j]).encode('utf-8')).strip()
                self.ui.tableWidget_2.setItem(i, j, QtGui.QTableWidgetItem(text))
                self.ui.tableWidget_2.resizeColumnsToContents()  # 将列调整到跟内容大小相匹配
                self.ui.tableWidget_2.resizeRowsToContents()  # 将行大小调整到跟内容的大学相匹配
                # self.ui.tableWidget_2.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
                # self.ui.tableWidget_2.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
    def deleteDataDB(self):
        curRowIdx = self.ui.tableWidget.currentIndex().row()
        try:
            items = self.ui.tableWidget.selectedItems()
            rowID = unicode(items[0].text()).encode('utf-8').strip()
        except Exception, error:
            msg = 'Warn, No data row is selected.'
            QtGui.QMessageBox.about(self, 'Warn', msg)
        self.ui.tableWidget.clearFocus()
        # self.ui.tableWidget.clearContents()
        self.ui.tableWidget.removeRow(curRowIdx)
        try:
            conn = sqlite3.connect(sqlitedb)
            cursor = conn.cursor()
            delDBSQL = "DELETE FROM " + tbRegistryDB + " WHERE ID = ?"
            cursor.execute(delDBSQL,(rowID,))
            cursor.close()
            conn.commit()
            conn.close()
        except Exception, error:
            msg = 'Error, Delete DB data filed ' + unicode(error)
            QtGui.QMessageBox.about(self, 'About', msg)
        else:
            msg = 'OK, Delete DB data successfully.'
            QtGui.QMessageBox.about(self, 'About', msg)

    def deleteDataServer(self):
        curRowIdx = self.ui.tableWidget_2.currentIndex().row()
        try:
            items = self.ui.tableWidget_2.selectedItems()
            rowID = unicode(items[0].text()).encode('utf-8').strip()
        except Exception, error:
            msg = 'Warn, No data row is selected.'
            QtGui.QMessageBox.about(self, 'Warn', msg)
        self.ui.tableWidget_2.clearFocus()
        # self.ui.tableWidget.clearContents()
        self.ui.tableWidget_2.removeRow(curRowIdx)
        try:
            conn = sqlite3.connect(sqlitedb)
            cursor = conn.cursor()
            delDBSQL = "DELETE FROM " + tbRegistryServer + " WHERE ID = ?"
            cursor.execute(delDBSQL, (rowID,))
            cursor.close()
            conn.commit()
            conn.close()
        except Exception, error:
            msg = 'Error, Delete Server data failed ' + unicode(error)
            QtGui.QMessageBox.about(self, 'About', msg)
        else:
            msg = 'OK, Delete Server data successfully.'
            QtGui.QMessageBox.about(self, 'About', msg)
    def updataDataDB(self):
        titleList = []
        curRowIdxRow = int(self.ui.tableWidget.currentIndex().row())
        try:
            items = self.ui.tableWidget.selectedItems()
            rowID = unicode(items[0].text()).encode('utf-8').strip()
        except Exception, error:
            msg = 'Warn, No data row is selected.'
            QtGui.QMessageBox.about(self, 'Warn', msg)
        # self.ui.tableWidget.currentRow()
        curRowIdxCol = int(self.ui.tableWidget.currentIndex().column())
        # self.ui.tableWidget.currentColumn()
        for x in range(self.ui.tableWidget.columnCount()):
            headItem = self.ui.tableWidget.horizontalHeaderItem(x)
            titleList.append(unicode(headItem.text()).encode('utf-8').strip())
        curItemText = unicode(self.ui.tableWidget.item(curRowIdxRow, curRowIdxCol).text()).encode('utf-8').strip()
        try:
            updateSQL = "update " + tbRegistryDB + " set " + titleList[
                curRowIdxCol] + "=" + "'" + curItemText + "'" + "where ID = " + str(rowID)
            conn = sqlite3.connect(sqlitedb)
            cursor = conn.cursor()
            cursor.execute(updateSQL)
            cursor.close()
            conn.commit()
            conn.close()
        except Exception, error:
            msg = 'Error, Update DB data failed ' + unicode(error)
            QtGui.QMessageBox.about(self, 'About', msg)
        else:
            msg = 'OK, Update DB data successfully.'
            QtGui.QMessageBox.about(self, 'About', msg)
    def updateDataServer(self):
        titleList = []
        curRowIdxRow = int(self.ui.tableWidget_2.currentIndex().row())
        try:
            items = self.ui.tableWidget_2.selectedItems()
            rowID = unicode(items[0].text()).encode('utf-8').strip()
        except Exception, error:
            msg = 'Warn, No data row is selected.'
            QtGui.QMessageBox.about(self, 'Warn', msg)
        # self.ui.tableWidget.currentRow()
        curRowIdxCol = int(self.ui.tableWidget_2.currentIndex().column())
        # self.ui.tableWidget.currentColumn()
        for x in range(self.ui.tableWidget_2.columnCount()):
            headItem = self.ui.tableWidget_2.horizontalHeaderItem(x)
            titleList.append(unicode(headItem.text()).encode('utf-8').strip())
        curItemText = unicode(self.ui.tableWidget_2.item(curRowIdxRow, curRowIdxCol).text()).encode('utf-8').strip()
        updateSQL = "update " + tbRegistryServer + " set " + titleList[curRowIdxCol] + "=" + "'" + curItemText + "'" + "where ID = " + str(rowID)
        try:
            conn = sqlite3.connect(sqlitedb)
            cursor = conn.cursor()
            cursor.execute(updateSQL)
            cursor.close()
            conn.commit()
            conn.close()
        except Exception, error:
            msg = 'Error, Update Server data failed ' + unicode(error)
            QtGui.QMessageBox.about(self, 'About', msg)
        else:
            msg = 'OK, Update Server data successfully.'
            QtGui.QMessageBox.about(self, 'About', msg)

    def insertDataDB(self):
        rowcount = self.ui.tableWidget.rowCount()
        self.ui.tableWidget.insertRow(rowcount)
        seqSQL = "select seq from sqlite_sequence where name = ?"
        conn = sqlite3.connect(sqlitedb)
        cursor = conn.cursor()
        cursor.execute(seqSQL, (tbRegistryDB,))
        seqResult = cursor.fetchone()
        cursor.close()
        conn.close()
        if seqResult != None:
            seqRow = str(int(seqResult[0]) + 1)
        self.ui.tableWidget.setItem(rowcount, 0, QtGui.QTableWidgetItem(seqRow))
        columnCount = self.ui.tableWidget.columnCount()
        for r in range(1, columnCount):
            # item = QtGui.QTableWidgetItem()
            self.ui.tableWidget.setItem(rowcount, r, QtGui.QTableWidgetItem('None'))
        sql_insert = "insert into " + tbRegistryDB + " values "
        sql_values = ""
        for i in range(0, columnCount):
            # sql_values += '('
            sql_values += 'None,'
            # sql_values += '),'
        sql_values = sql_values.strip(',')
        insertSQL = sql_insert + r'(' + sql_values + r')'
        conn = sqlite3.connect(sqlitedb)
        cursor = conn.cursor()
        cursor.execute(insertSQL)
        cursor.close()
        conn.commit()
        conn.close()
    def insertDataServer(self):
        rowcount = self.ui.tableWidget_2.rowCount()
        self.ui.tableWidget_2.insertRow(rowcount)
        seqSQL = "select seq from sqlite_sequence where name = ?"
        conn = sqlite3.connect(sqlitedb)
        cursor = conn.cursor()
        cursor.execute(seqSQL, (tbRegistryServer,))
        seqResult = cursor.fetchone()
        cursor.close()
        conn.close()
        if seqResult != None:
            seqRow = str(int(seqResult[0]) + 1)
        self.ui.tableWidget_2.setItem(rowcount, 0, QtGui.QTableWidgetItem(seqRow))
        columnCount = self.ui.tableWidget_2.columnCount()
        for r in range(1, columnCount):
            # item = QtGui.QTableWidgetItem()
            self.ui.tableWidget_2.setItem(rowcount, r, QtGui.QTableWidgetItem('None'))
        sql_insert = "insert into " + tbRegistryServer + " values "
        sql_values = ""
        for i in range(0, columnCount):
            # sql_values += '('
            sql_values += 'None,'
            # sql_values += '),'
        sql_values = sql_values.strip(',')
        insertSQL = sql_insert + r'(' + sql_values + r')'
        conn = sqlite3.connect(sqlitedb)
        cursor = conn.cursor()
        cursor.execute(insertSQL)
        cursor.close()
        conn.commit()
        conn.close()
    def dataCommitDB(self):
        titleList = []
        curRowIdxRow = int(self.ui.tableWidget.currentIndex().row())
        try:
            items = self.ui.tableWidget.selectedItems()
            rowID = unicode(items[0].text()).encode('utf-8').strip()
        except Exception, error:
            msg = 'Warn, No data row is selected.'
            QtGui.QMessageBox.about(self, 'Warn', msg)
        # self.ui.tableWidget.currentRow()
        curRowIdxCol = int(self.ui.tableWidget.currentIndex().column())
        # self.ui.tableWidget.currentColumn()
        for x in range(self.ui.tableWidget.columnCount()):
            headItem = self.ui.tableWidget.horizontalHeaderItem(x)
            titleList.append(unicode(headItem.text()).encode('utf-8').strip())

        curSelectedList = []
        for col in range(0, len(items)):
            content = unicode(self.ui.tableWidget.item(curRowIdxRow, col).text()).encode('utf-8').strip()
            curSelectedList.append(content)
        # updateValue = (curSelected[0],curSelected[1],curSelected[2],curSelected[3],curSelected[4],curSelected[5],curSelected[6],curSelected[7],curSelected[8],curSelected[9],curSelected[10],)
        try:
            conn = sqlite3.connect(sqlitedb)
            cursor = conn.cursor()
            for i in range(0, len(curSelectedList)):
                value = curSelectedList[i]
                updateSQL = "update " + tbRegistryDB + " set " + titleList[i] + "=" + "'" + value + "'" + "where ID = " + str(rowID)
                cursor.execute(updateSQL)
            cursor.close()
            conn.commit()
            conn.close()
        except Exception, error:
            msg = 'Error, Commit DB data failed ' + unicode(error)
            QtGui.QMessageBox.about(self, 'About', msg)
        else:
            msg = 'OK, Commit DB data successfully.'
            QtGui.QMessageBox.about(self, 'About', msg)
    def dataCommitServer(self):
        titleList = []
        curRowIdxRow = int(self.ui.tableWidget_2.currentIndex().row())
        try:
            items = self.ui.tableWidget_2.selectedItems()
            rowID = unicode(items[0].text()).encode('utf-8').strip()
        except Exception, error:
            msg = 'Warn, No data row is selected.'
            QtGui.QMessageBox.about(self, 'Warn', msg)
        # self.ui.tableWidget.currentRow()
        curRowIdxCol = int(self.ui.tableWidget_2.currentIndex().column())
        # self.ui.tableWidget.currentColumn()
        for x in range(self.ui.tableWidget_2.columnCount()):
            headItem = self.ui.tableWidget_2.horizontalHeaderItem(x)
            titleList.append(unicode(headItem.text()).encode('utf-8').strip())

        curSelectedList = []
        for col in range(0, len(items)):
            content = unicode(self.ui.tableWidget_2.item(curRowIdxRow, col).text()).encode('utf-8').strip()
            curSelectedList.append(content)
        # updateValue = (curSelected[0],curSelected[1],curSelected[2],curSelected[3],curSelected[4],curSelected[5],curSelected[6],curSelected[7],curSelected[8],curSelected[9],curSelected[10],)
        try:
            conn = sqlite3.connect(sqlitedb)
            cursor = conn.cursor()
            for i in range(0, len(curSelectedList)):
                value = curSelectedList[i]
                updateSQL = "update " + tbRegistryServer + " set " + titleList[i] + "=" + "'" + value + "'" + "where ID = " + str(rowID)
                cursor.execute(updateSQL)
            cursor.close()
            conn.commit()
            conn.close()
        except Exception, error:
            msg = 'Error, Commit Server data failed ' + unicode(error)
            QtGui.QMessageBox.about(self, 'About', msg)
        else:
            msg = 'OK, Commit Server data successfully.'
            QtGui.QMessageBox.about(self, 'About', msg)
class WidgetConnecionClient(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.ui = su_connection_client.Ui_Form()
        self.ui.setupUi(self)
class WidgetConnecionExport(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.ui = su_connection_export.Ui_Form()
        self.ui.setupUi(self)

        # self.ui.radioButton_4.isChecked()
        self.ui.radioButton_4.setChecked(True)
        uniqueStr = Qt.QDateTime.currentDateTime().toString('yyyyMMddHHmmss')
        defaultName = pathExportDir + r'/' + unicode(self.ui.radioButton_4.text()).encode('utf-8').strip() + r'-' + uniqueStr + r'.xls'
        self.ui.lineEdit.setText(defaultName)

        # self.rowaddList = []
        self.rowdelList = []
        self.is_add_double_clicked = False
        self.is_double_clicked = False
        self.ui.listWidget.itemClicked.connect(self.itemAddClicked)
        self.ui.listWidget.itemDoubleClicked.connect(self.itemAddDoubleClicked)
        self.ui.listWidget_2.itemClicked.connect(self.itemDelClicked)
        self.ui.listWidget_2.itemDoubleClicked.connect(self.itemDelDoubleClicked)

        # QtCore.QObject.connect(self.radioButton, QtCore.SIGNAL(_fromUtf8("clicked()")), self.lineEdit.copy)
        self.connect(self.ui.radioButton, QtCore.SIGNAL('clicked()'), self.checkRadioButtons)
        self.connect(self.ui.radioButton_2, QtCore.SIGNAL('clicked()'), self.checkRadioButtons)
        self.connect(self.ui.radioButton_3, QtCore.SIGNAL('clicked()'), self.checkRadioButtons)
        self.connect(self.ui.radioButton_4, QtCore.SIGNAL('clicked()'), self.checkRadioButtons)

        self.ui.toolButton.clicked.connect(self.addItemSelected)
        self.ui.toolButton_2.clicked.connect(self.addMulItemSelected)
        self.ui.toolButton_3.clicked.connect(self.addAllItemSelected)
        self.ui.toolButton_4.clicked.connect(self.delItemSelected)
        self.ui.toolButton_5.clicked.connect(self.delMulItemSelected)
        self.ui.toolButton_6.clicked.connect(self.delAllItemSelected)
        self.ui.toolButton_7.clicked.connect(self.exportSaveDirectory)

        self.ui.pushButton.clicked.connect(self.saveExportFile)
        self.ui.pushButton_2.clicked.connect(self.cancelExportFile)

    def checkRadioButtons(self):
        if self.ui.radioButton.isChecked():
            uniqueStr = Qt.QDateTime.currentDateTime().toString('yyyyMMddHHmmss')
            defaultName = os.getcwd() + r'/' + unicode(self.ui.radioButton.text()).encode(
                'utf-8').strip() + r'-' + uniqueStr + r'.xlsx'
            self.ui.lineEdit.setText(defaultName)
        elif self.ui.radioButton_2.isChecked():
            uniqueStr = Qt.QDateTime.currentDateTime().toString('yyyyMMddHHmmss')
            defaultName = os.getcwd() + r'/' + unicode(self.ui.radioButton_2.text()).encode(
                'utf-8').strip() + r'-' + uniqueStr + r'.xlsx'
            self.ui.lineEdit.setText(defaultName)
        elif self.ui.radioButton_3.isChecked():
            uniqueStr = Qt.QDateTime.currentDateTime().toString('yyyyMMddHHmmss')
            defaultName = os.getcwd() + r'/' + unicode(self.ui.radioButton_3.text()).encode(
                'utf-8').strip() + r'-' + uniqueStr + r'.xlsx'
            self.ui.lineEdit.setText(defaultName)
        elif self.ui.radioButton_4.isChecked():
            uniqueStr = Qt.QDateTime.currentDateTime().toString('yyyyMMddHHmmss')
            defaultName = os.getcwd() + r'/' + unicode(self.ui.radioButton_4.text()).encode(
                'utf-8').strip() + r'-' + uniqueStr + r'.xlsx'
            self.ui.lineEdit.setText(defaultName)
        else:
            msg = 'Please, Specify the category of export statistic.'
            QtGui.QMessageBox.about(self, 'About', msg)
    def itemAddClicked(self):
        if not self.is_add_double_clicked:
            QtCore.QTimer.singleShot(100, self.itemAddClickedTimeout)
    def itemAddClickedTimeout(self):
        if not self.is_add_double_clicked:
            # do something when item clicked
            try:
                content = self.ui.listWidget_2.currentRow()
            except Exception, error:
                msg = 'Error.' + format(error)
                QtGui.QMessageBox.about(self, 'Error', msg)
            # self.rowaddList.append(content)
        else:
            self.is_add_double_clicked = False
    def itemAddDoubleClicked(self):
        self.is_add_double_clicked = True
        # do something when item double clicked
        try:
            rowadd = self.ui.listWidget.currentItem().text()
        except Exception, error:
            msg = 'Error.' + format(error)
            QtGui.QMessageBox.about(self, 'Error', msg)
        self.ui.listWidget_2.addItem(rowadd)
    def addItemSelected(self):
        try:
            content = self.ui.listWidget.currentItem().text()
            selectedItem = unicode(content).encode('utf-8').strip()

            self.ui.listWidget_2.clearFocus()
            # self.ui.listWidget_2.clear()
            self.ui.listWidget_2.addItem(selectedItem)
        except Exception, error:
            # selectedItem = ''
            msg = 'Error.Please specify the available host.\n' + format(error)
            QtGui.QMessageBox.about(self, 'Error', msg)
    def addMulItemSelected(self):
        selectedItemsList = []
        try:
            content = self.ui.listWidget.selectedItems()
            selectedItemsList = [i.text() for i in list(content)]
        except Exception, error:
            selectedItemsList = []
            msg = 'Error. Multiple selection(add) are Null.\n' + format(error)
            QtGui.QMessageBox.about(self, 'Error', msg)
        self.ui.listWidget_2.clearFocus()
        # self.ui.listWidget_2.clear()
        for selectedItems in selectedItemsList:
            self.ui.listWidget_2.addItem(selectedItems)
    def addAllItemSelected(self):
        selectedItemsList = []
        count = self.ui.listWidget.count()
        for i in range(count):
            try:
                content = unicode(self.ui.listWidget.item(i).text()).encode('utf-8').strip()
                selectedItemsList.append(content)
            except Exception, error:
                selectedItemsList = []
                msg = 'Error. All selection are Null.\n' + format(error)
                QtGui.QMessageBox.about(self, 'Error', msg)
        self.ui.listWidget_2.clearFocus()
        self.ui.listWidget_2.clear()
        for selectedItems in selectedItemsList:
            self.ui.listWidget_2.addItem(selectedItems)
    def itemDelClicked(self):
        if not self.is_double_clicked:
            QtCore.QTimer.singleShot(100, self.itemDelClickedTimeout)
    def itemDelClickedTimeout(self):
        if not self.is_double_clicked:
            # do something when item clicked
            try:
                content = self.ui.listWidget_2.currentRow()
                self.rowdelList.append(content)
            except Exception, error:
                msg = 'Error.\n' + format(error)
                QtGui.QMessageBox.about(self, 'Error', msg)
        else:
            self.is_double_clicked = False
    def itemDelDoubleClicked(self):
        self.is_double_clicked = True
        # do something when item double clicked
        try:
            rowdel = self.ui.listWidget_2.currentRow()
        except Exception, error:
            msg = 'Error.\n' + format(error)
            QtGui.QMessageBox.about(self, 'Error', msg)
        self.ui.listWidget_2.takeItem(rowdel)
    def delItemSelected(self):
        try:
            rowdel = self.ui.listWidget_2.currentRow()
        except Exception, error:
            msg = 'Error.\n' + format(error)
            QtGui.QMessageBox.about(self, 'Error', msg)
        self.ui.listWidget_2.takeItem(rowdel)
    def delMulItemSelected(self):
        for selectedItem in self.ui.listWidget_2.selectedItems():
            self.ui.listWidget_2.takeItem(self.ui.listWidget_2.row(selectedItem))
        # selectedItemsList = []
        # try:
        #     content = self.ui.listWidget_2.selectedItems()
        # except Exception, error:
        #     selectedItemsList = []
        #     msg = 'Error. Multiple selection(delete) are Null.\n' + format(error)
        #     QtGui.QMessageBox.about(self, 'Error', msg)
        # else:
        #     selectedItemsList = [i.text() for i in list(content)]
        #     print('selectedItemsList')
        #     print(selectedItemsList)
        #     print('')
        #     print()
        # for selectedItems in selectedItemsList:
        #     idx = self.ui.listWidget_2.find(selectedItems)
        #     self.ui.listWidget_2.clearFocus()
        #     # self.ui.listWidget_2.takeItem(idx)
        #     print('selectedItems')
        #     print(selectedItems)
        #     print('idx')
        #     print(idx)

    def delAllItemSelected(self):
        count = self.ui.listWidget_2.count()
        for rowdel in range(0, count):
            self.ui.listWidget_2.takeItem(0)
    def exportSaveDirectory(self):

        datetime = Qt.QDateTime.currentDateTime()
        uniqueStr = datetime.toString('yyyyMMddHHmmss')
        if self.ui.radioButton.isChecked():
            fileClass = unicode(self.ui.radioButton.text()).encode('utf-8').strip()
        elif self.ui.radioButton_2.isChecked():
            fileClass = unicode(self.ui.radioButton_2.text()).encode('utf-8').strip()
        elif self.ui.radioButton_3.isChecked():
            fileClass = unicode(self.ui.radioButton_3.text()).encode('utf-8').strip()
        else:
            fileClass = r'ExportFile'
        defaultName = pathExportDir + r'/' + fileClass + r'-' + uniqueStr + r'.xls'
        # filename = QtGui.QFileDialog.getSaveFileNameAndFilter(self, 'Export Save as File.', default_dir,
        #                                                       filter=self.tr("CSV files (*.csv)", options=QtGui.QFileDialog.DontUseNativeDialog))
        filename, extension = QtGui.QFileDialog.getSaveFileNameAndFilter(self, 'Export Save as File.', defaultName,
                                                                         filter=self.tr("Excel files (*.xlsx)"))
        if filename:
            self.ui.lineEdit.setText(filename)
    def saveExportFile(self):
        dataServerList = []
        dataStorageDiskList = []
        dataStorageInodeList = []
        dataTBSList = []
        cmd000 = r"res=`hostname -i`;if [ -z '$res' ];  then  res='None'; echo $res; else echo $res; fi"
        cmd001 = r"res=`cat /etc/redhat-release`;if [ -z '$res' ];  then  res='None'; echo $res; else echo $res; fi"
        cmd002 = r"res=`uname -r`;if [ -z '$res' ];  then  res='None'; echo $res; else echo $res; fi"
        cmd003 = r"res=`stat / | grep Change | awk -F' ' '{print$2}'`;if [ -z '$res' ];  then  res='None'; echo $res; else echo $res; fi"
        cmd004 = r"res=`dmidecode | grep -A9 'System Information' | grep 'Product Name' | cut -d':' -f2`;if [ -z '$res' ];  then  res='None'; echo $res; else echo $res; fi"
        cmd005 = r"res=`dmidecode | grep -A9 'System Information' | grep 'Serial Number' | cut -d':' -f2`;if [ -z '$res' ];  then  res='None'; echo $res; else echo $res; fi"
        cmd006 = r"res=`dmidecode | grep -A9 'System Information' | grep 'SKU Number' | cut -d':' -f2`;if [ -z '$res' ];  then  res='None'; echo $res; else echo $res; fi"
        # cmd007 = r"res=`dmidecode | grep -A10 'BIOS ' | grep 'BIOS Revision'"
        cmd008 = r"res=`dmidecode | grep 'Firmware Revision'`;if [ -z '$res' ];  then  res='None'; echo $res; else echo $res; fi"
        cmd009 = r"res=`dmidecode | grep CPU | grep Version | sort -u | cut -d':' -f2`;if [ -z '$res' ];  then  res='None'; echo $res; else echo $res; fi"
        cmd010 = r"res=`dmidecode  | grep -A2 'Handle'| grep 'Processor Information' | wc -l`;if [ -z '$res' ];  then  res='None'; echo $res; else echo $res; fi"
        cmd011 = r"res=`dmidecode | grep 'Core Count' | sort -u | cut -d':' -f2`;if [ -z '$res' ];  then  res='None'; echo $res; else echo $res; fi"
        cmd012 = r"res=`cat /proc/cpuinfo| grep 'processor' | wc -l`;if [ -z '$res' ];  then  res='None'; echo $res; else echo $res; fi"
        cmd013 = r"res=`top -d 1 -n 1 -b | grep Cpu | awk -F' ' '{print$2}' | awk -F'%' '{print$1}'`;if [ -z '$res' ];  then  res='None'; echo $res; else echo $res; fi"
        cmd014 = r"res=`dmidecode | grep -A10 'Memory Device' | grep 'Type' | grep -v 'Other' | sort -u | cut -d':' -f 2`;if [ -z '$res' ];  then  res='None'; echo $res; else echo $res; fi"
        cmd015 = r"res=`dmidecode | grep -A10 'Memory Device' | grep Size | grep -v 'No Module Installed' | wc -l`;if [ -z '$res' ];  then  res='None'; echo $res; else echo $res; fi"
        cmd016 = r"res=`dmidecode | grep -A10 'Memory Device' | grep Size | grep -v 'No Module Installed' | sort -u | cut -d':' -f2`;if [ -z '$res' ];  then  res='None'; echo $res; else echo $res; fi"
        cmd017 = r"res=`free -m | grep -w Mem | awk -F' ' '{print$2}'`;if [ -z '$res' ];  then  res='None'; echo $res; else echo $res; fi"
        cmd018 = r"res=`free -m | grep -w Mem | awk -F' ' '{print$3}'`;if [ -z '$res' ];  then  res='None'; echo $res; else echo $res; fi"
        cmd019 = r"res=`free -m | grep -w Mem | awk -F' ' '{print$4}'`;if [ -z '$res' ];  then  res='None'; echo $res; else echo $res; fi"
        cmd020 = r"res=`free -m | grep -w Mem | awk -F' ' '{print$5}'`;if [ -z '$res' ];  then  res='None'; echo $res; else echo $res; fi"
        cmd021 = r"res=`free -m | grep -w Mem | awk -F' ' '{print$6}'`;if [ -z '$res' ];  then  res='None'; echo $res; else echo $res; fi"
        cmd022 = r"res=`free -m | grep -w Mem | awk -F' ' '{print$7}'`;if [ -z '$res' ];  then  res='None'; echo $res; else echo $res; fi"
        cmd023 = r"""awk 'BEGIN{printf "%.2f%\n",('`free -m | grep -w Mem | awk '{print$3}'`'/'`free -m | grep -w Mem | awk '{print$2}'`')*100}'"""
        cmd024 = r"res=`free -m | grep -w Swap | awk -F' ' '{print$2}'`;if [ -z '$res' ];  then  res='None'; echo $res; else echo $res; fi"
        cmd025 = r"res=`free -m | grep -w Swap | awk -F' ' '{print$3}'`;if [ -z '$res' ];  then  res='None'; echo $res; else echo $res; fi"
        cmd026 = r"res=`free -m | grep -w Swap | awk -F' ' '{print$4}'`;if [ -z '$res' ];  then  res='None'; echo $res; else echo $res; fi"
        cmd027 = r"""awk 'BEGIN{printf "%.2f%\n",('`free -m | grep -w Swap | awk '{print$3}'`'/'`free -m | grep -w Swap | awk '{print$2}'`')*100}'"""
        cmddisks = r"res=`df -Phl`;if [ -z '$res' ];  then  res='None'; echo $res; else df -Phl; fi"
        cmdinodes = r"res=`df -Phi`;if [ -z '$res' ];  then  res='None'; echo $res; else df -Phi; fi"
        commanddisks = cmd000 + r';' + cmddisks
        commandinodes = cmd000 + r';' + cmdinodes
        commandserver = cmd000 + r';' + cmd001 + r';' + cmd002 + r';' + cmd003 + r';' + cmd004 + r';' + cmd005 + r';' + cmd006 + r';' + cmd008 + r';' + cmd009 + r';' + cmd010 + r';' + cmd011 + r';' + cmd012 + r';' + cmd013 + r';' + cmd014 + r';' + cmd015 + r';' + cmd016 + r';' + cmd017 + r';' + cmd018 + r';' + cmd019 + r';' + cmd020 + r';' + cmd021 + r';' + cmd022 + r';' + cmd023 + r';' + cmd024 + r';' + cmd025 + r';' + cmd026 + r';' + cmd027

        tbsSQL = """SELECT d.tablespace_name AS tablespace_name,
       d.allocated_space AS allocated_space_gb,
                       e.free_space AS free_space_gb,
                       d.allocated_space - NVL (e.free_space, 0) used_space_gb,
                          CASE
                             WHEN d.allocated_space = 0
                             THEN
                                0
                             ELSE
                                ROUND (
                                     (  (d.allocated_space - NVL (e.free_space, 0))
                                      / d.allocated_space)
                                   * 100,
                                   2)
                          END
                       || '%'
                          used_rate,
                       d.max_space AS max_space_gb,
                          CASE
                             WHEN d.max_space = 0
                             THEN
                                0
                             ELSE
                                ROUND (
                                     (  (d.allocated_space - NVL (e.free_space, 0))
                                      / d.max_space)
                                   * 100,
                                   2)
                          END
                       || '%'
                          max_used_rate,
                       f.value as db_file_param,
                       g.data_file_count as data_file_count,
                       CASE
                             WHEN f.value = 0
                             THEN
                                0
                             ELSE
                                ROUND((g.data_file_count / f.value) * 100, 2)
                       END
                       || '%'
                          dbfiles_rate,
                       SYSDATE chktime
                  FROM (  SELECT tablespace_name,
                                 ROUND (SUM (bytes) / (1024 * 1024 * 1024), 2) allocated_space,
                                 ROUND (
                                      SUM (
                                         DECODE (maxbytes,
                                                 0, bytes,
                                                 GREATEST (maxbytes, bytes)))
                                    / (1024 * 1024 * 1024),
                                    2)
                                    max_space
                            FROM dba_data_files
                        GROUP BY tablespace_name) d,
                       (  SELECT tablespace_name,
                                 ROUND (SUM (bytes) / (1024 * 1024 * 1024), 2) free_space
                            FROM dba_free_space
                        GROUP BY tablespace_name) e,
                        (select value from v$parameter where name = 'db_files') f,
                        (select ROUND((select count(file_name) from dba_data_files) + (select count(file_name) from dba_temp_files),2) as data_file_count from dual) g
                 WHERE d.tablespace_name = e.tablespace_name(+)
                UNION ALL
                SELECT s.tablespace_name AS tablespace_name,
                       s.allocated_space AS allocated_space_gb,
                       s.allocated_space - NVL (t.used_space, 0) AS free_space_gb,
                       t.used_space AS used_space_gb,
                          CASE
                             WHEN s.allocated_space = 0 THEN 0
                             ELSE ROUND (NVL (t.used_space, 0) * 100 / s.allocated_space, 2)
                          END
                       || '%'
                          used_rate,
                       s.max_space AS max_space_gb,
                          CASE
                             WHEN s.max_space = 0 THEN 0
                             ELSE ROUND (NVL (t.used_space, 0) * 100 / s.max_space, 2)
                          END
                       || '%'
                          max_used_rate,
                       u.value as db_file_param,
                       v.data_file_count as data_file_count,
                       CASE
                             WHEN u.value = 0
                             THEN
                                0
                             ELSE
                                ROUND((v.data_file_count / u.value) * 100, 2)
                       END
                       || '%'
                          dbfiles_rate,
                       SYSDATE chktime
                  FROM (  SELECT tablespace_name,
                                 ROUND (SUM (bytes) / (1024 * 1024 * 1024), 2) allocated_space,
                                 ROUND (
                                      SUM (
                                         DECODE (maxbytes,
                                                 0, bytes,
                                                 GREATEST (maxbytes, bytes)))
                                    / (1024 * 1024 * 1024),
                                    2)
                                    max_space
                            FROM dba_temp_files
                        GROUP BY tablespace_name) s,
                       (  SELECT tablespace_name,
                                 ROUND (SUM (bytes_used) / (1024 * 1024 * 1024), 2) used_space
                            FROM v$temp_extent_pool
                        GROUP BY tablespace_name) t,
                        (select value from v$parameter where name = 'db_files') u,
                        (select ROUND((select count(file_name) from dba_data_files) + (select count(file_name) from dba_temp_files),2) as data_file_count from dual) v
                 WHERE s.tablespace_name = t.tablespace_name(+)
                """
        if len(self.ui.lineEdit.text()) != 0:
            saveExpfile = unicode(self.ui.lineEdit.text()).encode('utf-8').strip()
            selectedHostList = []
            for i in range(self.ui.listWidget_2.count()):
                selectedHostList.append(unicode(self.ui.listWidget_2.item(i).text()).encode('utf-8').strip())
            # Server
            if self.ui.radioButton.isChecked():
                for selectedHost in selectedHostList:
                    try:
                        conn = sqlite3.connect(sqlitedb)
                        cursor = conn.cursor()
                        cursor.execute(
                            """select host,port,user,password from """ + tbRegistryServer + """ where user='root' and host=?""",
                            (selectedHost,))
                        resultList = cursor.fetchall()
                        cursor.close()
                        conn.close()
                    except Exception, error:
                        msg = 'Error. Query account failed.\n' + unicode(error).encode('utf-8')
                        QtGui.QMessageBox.about(self, 'About', msg)
                    if len(resultList) == 1:
                        selectedHost = resultList[0][0]
                        selectedPort = int(resultList[0][1])
                        selectedUser = resultList[0][2]
                        selectedPassword = resultList[0][3]
                    elif len(resultList) == 0:
                        msg = 'Failed to get server account(Not Found).'
                        QtGui.QMessageBox.about(self, 'About', msg)
                    else:
                        msg = 'Failed to get server account(multiple).'
                        QtGui.QMessageBox.about(self, 'About', msg)

                    try:
                        ssh = paramiko.SSHClient()
                        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                        ssh.connect(selectedHost, selectedPort, selectedUser, selectedPassword)
                        stdin, stdout, stderr = ssh.exec_command(commandserver)
                        cmdServerList = stdout.readlines()
                        cmdServerError = stderr.readlines()
                        ssh.close()
                    except Exception, error:
                        msg = 'Server Information query failed!\n' + format(error)
                        QtGui.QMessageBox.about(self, 'About', msg)
                    if len(cmdServerError) == 0:
                        dataServerList.append(cmdServerList)
                try:
                    titleServerList = ['Host', 'OSVersion', 'Kernel', 'InstDate', 'ProductName', 'SerialNumber', 'SKUNumber', 'FirmwareRevision',
                                 'CPUVersion', 'CPUCount', 'CPUCorePer', 'CPULogical', 'CPUUsage',
                                 'MemType', 'MemCount', 'MemSizePer', 'MemTotal', 'MemUsed', 'MemFree', 'MemShared', 'MemBuffers', 'MemCached', 'MemUsage',
                                 'SwapTotal', 'SwapUsed', 'SwapFree', 'SwapUsage']
                    # titleList = ['Host', 'OSVersion', 'Kernel', 'InstDate', 'ProductName', 'SerialNumber', 'SKUNumber',
                    #              'BIOSRevision', 'FirmwareRevision',
                    #              'CPUVersion', 'CPUCount', 'CPUCorePer', 'CPULogical', 'CPUUsage', 'MemType', 'MemCount',
                    #              'MemSizePer', 'MemTotal', 'MemUsed',
                    #              'MemFree', 'MemShared', 'MemBuffers', 'MemCached', 'MemUsage', 'SwapTotal', 'SwapUsed',
                    #              'SwapFree', 'SwapUsage']
                    workbook = xlsxwriter.Workbook(saveExpfile)
                    worksheetServer = workbook.add_worksheet('Server')
                    bold = workbook.add_format({'bold': True})
                    worksheetServer.write_row('A1', titleServerList, bold)
                    for i in range(0, len(dataServerList)):
                        rowdataServer = dataServerList[i]
                        for j in range(0, len(rowdataServer)):
                            worksheetServer.write(i + 1, j, rowdataServer[j].strip())
                    workbook.close()
                except Exception, error:
                    msg = 'Error. Export Statistic to excel Failed\n.' + format(error)
                    QtGui.QMessageBox.about(self, 'Error', msg)
                else:
                    msg = 'OK. Export Statistic to excel successfully.'
                    QtGui.QMessageBox.about(self, 'about', msg)
            elif self.ui.radioButton_2.isChecked():
                # Storage
                dataStorageDiskList = []
                dataStorageInodeList = []
                for selectedHost in selectedHostList:
                    try:
                        conn = sqlite3.connect(sqlitedb)
                        cursor = conn.cursor()
                        cursor.execute(
                            """select host,port,user,password from """ + tbRegistryServer + """ where user='root' and host=?""",
                            (selectedHost,))
                        resultList = cursor.fetchall()
                        conn.close()
                    except Exception, error:
                        msg = 'Error. Query account failed.\n' + unicode(error).encode('utf-8')
                        QtGui.QMessageBox.about(self, 'About', msg)
                    if len(resultList) == 1:
                        selectedHost = resultList[0][0]
                        selectedPort = int(resultList[0][1])
                        selectedUser = resultList[0][2]
                        selectedPassword = resultList[0][3]
                    elif len(resultList) == 0:
                        msg = 'Failed to get server account(Not Found).'
                        QtGui.QMessageBox.about(self, 'About', msg)
                    else:
                        msg = 'Failed to get server account(multiple).'
                        QtGui.QMessageBox.about(self, 'About', msg)
                    try:
                        ssh = paramiko.SSHClient()
                        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                        ssh.connect(selectedHost, selectedPort, selectedUser, selectedPassword)
                        stdin, stdout, stderr = ssh.exec_command(commanddisks)
                        cmdDisksList = stdout.readlines()
                        cmdDisksError = stderr.readlines()
                        stdin, stdout, stderr = ssh.exec_command(commandinodes)
                        cmdInodesList = stdout.readlines()
                        cmdInodesError = stderr.readlines()
                        ssh.close()
                    except Exception, error:
                        msg = 'Server Information query failed!\n' + format(error)
                        QtGui.QMessageBox.about(self, 'About', msg)
                    if len(cmdDisksError) == 0:
                        dataStorageDiskList.append(cmdDisksList)
                    if len(cmdInodesError) == 0:
                        dataStorageInodeList.append(cmdInodesList)
                try:
                    titleStorageDiskList = dataStorageDiskList[0][1].split()
                    titleStorageDiskList.remove('Mounted')
                    titleStorageDiskList.remove('on')
                    titleStorageInodeList = dataStorageInodeList[0][1].split()
                    titleStorageInodeList.remove('Mounted')
                    titleStorageInodeList.remove('on')
                    titleStorage = titleStorageDiskList + titleStorageInodeList
                    titleStorage.insert(0, 'Host')
                    # subTitleList = [' ','Filesystem','Size','Used','Avail','Use%','Mounted']
                    workbook = xlsxwriter.Workbook(saveExpfile)
                    worksheetStorage = workbook.add_worksheet('Storage')
                    bold = workbook.add_format({'bold': True})
                    worksheetStorage.write_row('A1', titleStorage, bold)
                    rowCountStorage = []
                    for i in range(0, len(dataStorageDiskList)):
                        dataStorageDisk = dataStorageDiskList[i][2:]
                        dataStorageInode = dataStorageInodeList[i][2:]
                        # worksheetStorage.write(1 + sum(rowCountStorage), 0, dataStorageDiskList[i][0])
                        for n in range(0, len(dataStorageDisk)):
                            worksheetStorage.write(1 + sum(rowCountStorage) + n, 0, dataStorageDiskList[i][0])
                        for j in range(0, len(dataStorageDisk)):
                            rowdatastorage = ''.join(dataStorageDisk[j]).split() + ''.join(dataStorageInode[j]).split()
                            del rowdatastorage[6]
                            del rowdatastorage[10]
                            for k in range(0, len(rowdatastorage)):
                                worksheetStorage.write(j + 1 + sum(rowCountStorage), k + 1, rowdatastorage[k].strip())
                        rowCountStorage.append(int(len(dataStorageDisk)))
                    workbook.close()
                except Exception, error:
                    msg = 'Error. Export Statistic to excel Failed\n.' + format(error)
                    QtGui.QMessageBox.about(self, 'Error', msg)
                else:
                    msg = 'OK. Export Statistic to excel successfully.'
                    QtGui.QMessageBox.about(self, 'about', msg)
            elif self.ui.radioButton_3.isChecked():
                # Tablespace
                for selectedHost in selectedHostList:

                    try:
                        conn = sqlite3.connect(sqlitedb)
                        cursor = conn.cursor()
                        cursor.execute(
                            """select host,port,user,password,instanceName,defaultRole from """ + tbRegistryDB + """ where user='sys' and host=?""",
                            (selectedHost,))
                        resultList = cursor.fetchall()
                        conn.close()
                    except Exception, error:
                        msg = 'Error. Query account failed.\n' + format(error)
                        QtGui.QMessageBox.about(self, 'About', msg)
                    if len(resultList) == 1:
                        selectedOraHost = resultList[0][0]
                        selectedOraPort = int(resultList[0][1])
                        selectedOraUser = resultList[0][2]
                        selectedOraPassword = resultList[0][3]
                        selectedOrainstanceName = resultList[0][4]
                        selectedOradefaultRole = resultList[0][5]
                        selectedOraDSN = cx_Oracle.makedsn(selectedOraHost, selectedOraPort, selectedOrainstanceName,
                                                           region=None,
                                                           sharding_key=None,
                                                           super_sharding_key=None)
                    elif len(resultList) == 0:
                        msg = 'Failed, Oracle(' + selectedHost + r') account(Not Found).'
                        QtGui.QMessageBox.about(self, 'About', msg)
                    else:
                        msg = 'Failed, (Oracle(' + selectedHost + r') account(Multiple).'
                        QtGui.QMessageBox.about(self, 'About', msg)
                    try:
                        connection = cx_Oracle.connect(selectedOraUser, selectedOraPassword, selectedOraDSN,
                                                       cx_Oracle.SYSDBA)
                        cursor = connection.cursor()
                        cursor.execute(tbsSQL)
                        tbsDetailList = cursor.fetchall()
                        cursor.close()
                        connection.close()
                    except Exception, error:
                        msg = 'Error, Oracle(' + selectedHost + r') Tablepsce statistics query failed!\n' + unicode(error)
                        QtGui.QMessageBox.about(self, 'About', msg)
                    if tbsDetailList:
                        tbsDetailList.insert(0, selectedHost)
                        dataTBSList.append(tbsDetailList)
                try:
                    titleTBSList = ['Host', 'Tablespace_name', 'Allocated_space', 'Free_space', 'Used_space',
                                    'Used_rate', 'Max_space', 'Max_used_rate', 'Db_files', 'Data_files_count', 'Data_files_rate', 'Chk_time']
                    workbook = xlsxwriter.Workbook(saveExpfile)
                    worksheetTBS = workbook.add_worksheet('Tablespace')
                    dateFormat = workbook.add_format({'num_format': 'mm/dd/yyyy'})
                    # worksheet.set_column('I:I', dateFormat)
                    bold = workbook.add_format({'bold': True})
                    worksheetTBS.write_row('A1', titleTBSList, bold)
                    rowCountTBS = []
                    for i in range(0, len(dataTBSList)):
                        dataTBS = dataTBSList[i][1:]
                        # worksheetTBS.write(1 + sum(rowCountTBS), 0, dataTBSList[i][0])
                        for n in range(0, len(dataTBS)):
                            worksheetTBS.write(1 + sum(rowCountTBS) + n, 0, dataTBSList[i][0])
                        for j in range(0, len(dataTBS)):
                            rowdataTBS = list(dataTBS[j])[:-1]
                            for k in range(0, len(rowdataTBS)):
                                worksheetTBS.write(j + 1 + sum(rowCountTBS), k + 1, rowdataTBS[k])
                            worksheetTBS.write(j + 1 + sum(rowCountTBS), k + 2, list(dataTBS[j])[-1], dateFormat)
                        rowCountTBS.append(int(len(dataTBS)))
                    workbook.close()
                except Exception, error:
                    msg = 'Error. Export tablespace statistic to excel Failed\n.' + format(error)
                    QtGui.QMessageBox.about(self, 'Error', msg)
                else:
                    msg = 'OK. Export tablespace statistic to excel successfully.'
                    QtGui.QMessageBox.about(self, 'about', msg)
            elif self.ui.radioButton_4.isChecked():
                for selectedHost in selectedHostList:
                    try:
                        conn = sqlite3.connect(sqlitedb)
                        cursor = conn.cursor()
                        cursor.execute(
                            """select host,port,user,password from """ + tbRegistryServer + """ where user='root' and host=?""",
                            (selectedHost,))
                        hostConnList = cursor.fetchall()
                        cursor.close()
                        conn.close()
                    except Exception, error:
                        msg = 'Error. Query account failed.\n' + unicode(error).encode('utf-8')
                        QtGui.QMessageBox.about(self, 'About', msg)
                    try:
                        conn = sqlite3.connect(sqlitedb)
                        cursor = conn.cursor()
                        cursor.execute(
                            """select host,port,user,password,instanceName,defaultRole from """ + tbRegistryDB + """ where user='sys' and host=?""",
                            (selectedHost,))
                        oraConnList = cursor.fetchall()
                        cursor.close()
                        conn.close()
                    except Exception, error:
                        msg = 'Error. Query account failed.\n' + unicode(error).encode('utf-8')
                        QtGui.QMessageBox.about(self, 'About', msg)
                    if len(oraConnList) == 1:
                        selectedOraHost = oraConnList[0][0]
                        selectedOraPort = int(oraConnList[0][1])
                        selectedOraUser = oraConnList[0][2]
                        selectedOraPassword = oraConnList[0][3]
                        selectedOrainstanceName = oraConnList[0][4]
                        selectedOradefaultRole = oraConnList[0][5]
                        selectedOraDSN = cx_Oracle.makedsn(selectedOraHost, selectedOraPort, selectedOrainstanceName,
                                                           region=None,
                                                           sharding_key=None,
                                                           super_sharding_key=None)
                    elif len(oraConnList) == 0:
                        msg = 'Failed, Oracle(' + selectedHost + r') account(Not Found).'
                        QtGui.QMessageBox.about(self, 'About', msg)
                    else:
                        msg = 'Failed, Oracle(' + selectedHost + r') account(Multiple)'
                        QtGui.QMessageBox.about(self, 'About', msg)
                    if len(hostConnList) == 1:
                        selectedHost = hostConnList[0][0]
                        selectedPort = int(hostConnList[0][1])
                        selectedUser = hostConnList[0][2]
                        selectedPassword = hostConnList[0][3]
                    elif len(hostConnList) == 0:
                        msg = 'Failed, Server(' + selectedHost + r') account(Not Found).'
                        QtGui.QMessageBox.about(self, 'About', msg)
                    else:
                        msg = 'Failed, Server(' + selectedHost + r') account(Multiple).'
                        QtGui.QMessageBox.about(self, 'About', msg)
                    try:
                        ssh = paramiko.SSHClient()
                        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                        ssh.connect(selectedHost, selectedPort, selectedUser, selectedPassword)
                        stdin, stdout, stderr = ssh.exec_command(commandserver)
                        commandserverList = stdout.readlines()
                        commandserverError = stderr.readlines()
                        stdin, stdout, stderr = ssh.exec_command(commanddisks)
                        commanddisksList = stdout.readlines()
                        commanddisksError = stderr.readlines()
                        stdin, stdout, stderr = ssh.exec_command(commandinodes)
                        commandinodesList = stdout.readlines()
                        commandinodesError = stderr.readlines()
                        ssh.close()
                    except Exception, error:
                        msg = 'Server Information query failed!\n' + format(error)
                        QtGui.QMessageBox.about(self, 'About', msg)
                    if len(commandserverError) == 0:
                        dataServerList.append(commandserverList)
                    if len(commanddisksError) == 0:
                        dataStorageDiskList.append(commanddisksList)
                    if len(commandinodesError) == 0:
                        dataStorageInodeList.append(commandinodesList)

                    try:
                        connection = cx_Oracle.connect(selectedOraUser, selectedOraPassword, selectedOraDSN,
                                                       cx_Oracle.SYSDBA)
                        cursor = connection.cursor()
                        cursor.execute(tbsSQL)
                        tbsDetailList = cursor.fetchall()
                        cursor.close()
                        connection.close()
                    except Exception, error:
                        msg = 'Error, Tablepsce statistics query failed!\n' + unicode(error)
                        QtGui.QMessageBox.about(self, 'About', msg)
                    if tbsDetailList:
                        tbsDetailList.insert(0, selectedHost)
                        dataTBSList.append(tbsDetailList)

                try:
                    titleServerList = ['Host', 'OSVersion', 'Kernel', 'InstDate', 'ProductName', 'SerialNumber',
                                       'SKUNumber',
                                       'FirmwareRevision',
                                       'CPUVersion', 'CPUCount', 'CPUCorePer', 'CPULogical', 'CPUUsage',
                                       'MemType', 'MemCount', 'MemSizePer', 'MemTotal', 'MemUsed', 'MemFree', 'MemShared',
                                       'MemBuffers', 'MemCached', 'MemUsage',
                                       'SwapTotal', 'SwapUsed', 'SwapFree', 'SwapUsage']
                    titleStorageDiskList = dataStorageDiskList[0][1].split()
                    titleStorageDiskList.remove('Mounted')
                    titleStorageDiskList.remove('on')
                    titleStorageInodeList = dataStorageInodeList[0][1].split()
                    titleStorageInodeList.remove('Mounted')
                    titleStorageInodeList.remove('on')
                    titleStorage = titleStorageDiskList + titleStorageInodeList
                    titleStorage.insert(0, 'Host')
                    titleTBSList = ['Host', 'Tablespace_name', 'Allocated_space', 'Free_space', 'Used_space',
                                    'Used_rate', 'Max_space', 'Max_used_rate', 'Db_files', 'Data_files_count', 'Data_files_rate', 'Chk_time']
                    workbook = xlsxwriter.Workbook(saveExpfile)
                    worksheetServer = workbook.add_worksheet('Server')
                    worksheetStorage = workbook.add_worksheet('Storage')
                    worksheetTBS = workbook.add_worksheet('Tablespace')
                    dateFormat = workbook.add_format({'num_format': 'mm/dd/yyyy'})
                    bold = workbook.add_format({'bold': True})
                    worksheetServer.write_row('A1', titleServerList, bold)
                    worksheetStorage.write_row('A1', titleStorage, bold)
                    worksheetTBS.write_row('A1', titleTBSList, bold)
                    # Server
                    for i in range(0, len(dataServerList)):
                        data = dataServerList[i]
                        for j in range(0, len(data)):
                            worksheetServer.write(i + 1, j, data[j].strip())
                    # Storage
                    rowCountStorage = []
                    for i in range(0, len(dataStorageDiskList)):
                        dataStorageDisk = dataStorageDiskList[i][2:]
                        dataStorageInode = dataStorageInodeList[i][2:]
                        # worksheetStorage.write(1 + sum(rowCountStorage), 0, dataStorageDiskList[i][0])
                        for n in range(0, len(dataStorageDisk)):
                            worksheetStorage.write(1 + sum(rowCountStorage) + n, 0, dataStorageDiskList[i][0])
                        for j in range(0, len(dataStorageDisk)):
                            rowdatastorage = ''.join(dataStorageDisk[j]).split() + ''.join(dataStorageInode[j]).split()
                            del rowdatastorage[6]
                            del rowdatastorage[10]
                            for k in range(0, len(rowdatastorage)):
                                worksheetStorage.write(j + 1 + sum(rowCountStorage), k + 1, rowdatastorage[k].strip())
                        rowCountStorage.append(int(len(dataStorageDisk)))
                    # tablespace
                    rowCountTBS = []
                    for i in range(0, len(dataTBSList)):
                        dataTBS = dataTBSList[i][1:]
                        # worksheetTBS.write(1 + sum(rowCountTBS), 0, dataTBSList[i][0])
                        for n in range(0, len(dataTBS)):
                            worksheetTBS.write(1 + sum(rowCountTBS) + n, 0, dataTBSList[i][0])
                        for j in range(0, len(dataTBS)):
                            rowdataTBS = list(dataTBS[j])[:-1]
                            for k in range(0, len(rowdataTBS)):
                                worksheetTBS.write(j + 1 + sum(rowCountTBS), k + 1, rowdataTBS[k])
                                worksheetTBS.write(j + 1 + sum(rowCountTBS), k + 2, list(dataTBS[j])[-1], dateFormat)
                        rowCountTBS.append(int(len(dataTBS)))
                    workbook.close()
                except Exception, error:
                    msg = 'Error. Export tablespace statistic to excel Failed\n.' + format(error)
                    QtGui.QMessageBox.about(self, 'Error', msg)
                else:
                    msg = 'OK. Export tablespace statistic to excel successfully.'
                    QtGui.QMessageBox.about(self, 'about', msg)
            else:
                msg = 'Error. Please specify the export category.'
                QtGui.QMessageBox.about(self, 'Error', msg)
        else:
            # saveExpfile = os.getcwd() + r'/' + appName + r'-' + uniqueStr + r'.xlsx'
            msg = 'Error. Please specify the Export Destination'
            QtGui.QMessageBox.about(self, 'Error', msg)
    def cancelExportFile(self):
        self.ui.listWidget_2.clearFocus()
        self.ui.listWidget_2.clear()
        count = self.ui.listWidget_2.count()
        for rowdel in range(0, count):
            self.ui.listWidget_2.takeItem(0)
        QtGui.QWidget.close(self)

class MainWindowModuleIndex(QtGui.QMainWindow):
    def __init__(self,parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.ui = su_module_index.Ui_MainWindow()
        self.ui.setupUi(self)

        QtCore.QObject.connect(self.ui.treeWidget, QtCore.SIGNAL(_fromUtf8("itemClicked(QTreeWidgetItem*,int)")),
                               self.stackWidgetSwitch)
        self.ui.comboBox.activated.connect(lambda: self.selectPrimary(self.ui.comboBox.currentText()))
        self.ui.pushButton.clicked.connect(self.stackedWidgetIndex09)
        self.ui.pushButton_2.clicked.connect(self.stackedWidgetIndex10)
        # self.curAccount()
    def selectPrimary(self, param):
        content = unicode(param).encode('utf-8').strip().split('@')[1].split(':')[0]
        idx = self.ui.comboBox_2.findText(content)
        self.ui.comboBox_2.setCurrentIndex(idx)
        self.ui.comboBox_2.setEnabled(False)
        try:
            curOraHost = unicode(param).encode('utf-8').strip().split('@')[1].split(':')[0]
            curOraPort = unicode(param).encode('utf-8').strip().split('/')[0].split(':')[1]
            curOraUser = unicode(param).encode('utf-8').strip().split('@')[0]
            curOraSID = unicode(param).encode('utf-8').strip().split('/')[1]
            curOraDSN = cx_Oracle.makedsn(curOraHost, curOraPort, curOraSID, region=None,
                                               sharding_key=None,
                                               super_sharding_key=None)
            conn = sqlite3.connect(sqlitedb)
            cursor = conn.cursor()
            cursor.execute(
                """select password from """ + tbRegistryDB + """ where host=? and user=? and instanceName=?""",
                (curOraHost,curOraUser,curOraSID,))
            resultList = cursor.fetchall()
            cursor.close()
            conn.close()
            if len(resultList) == 1:
                curOraPassword = resultList[0][0]
        except Exception, error:
            msg = 'Error, Account verification failed.\n' + unicode(error)
            QtGui.QMessageBox.about(self, 'About', msg)
        else:
            connection = cx_Oracle.connect(curOraUser, curOraPassword, curOraDSN, cx_Oracle.SYSDBA)
            cursor1 = connection.cursor()
            cursor2 = connection.cursor()
            cursor1.execute(r"select name as dbName, db_unique_name as dbUName, open_mode, platform_name from v$database")
            cursor2.execute(r"select host_name, version, instance_name from v$instance")
            dbresultList = cursor1.fetchall()
            instresultList = cursor2.fetchall()
            cursor1.close()
            cursor2.close()
            connection.close()
            summaryList = []
            if len(dbresultList) != 0 and len(dbresultList) != 0:
                summaryList = instresultList + dbresultList
            self.ui.label_3.setText(summaryList[0][0])
            self.ui.label_4.setText(summaryList[0][1])
            self.ui.label_5.setText(summaryList[0][2])
            self.ui.label_6.setText(summaryList[1][0])
            self.ui.label_7.setText(summaryList[1][1])
            self.ui.label_8.setText(summaryList[1][2])
            self.ui.label_9.setText(summaryList[1][3])
    def curAccount(self):
        qtStrings = unicode(self.ui.comboBox.currentText()).encode('utf-8').strip()
        if len(qtStrings) != 0:
            self.connStatus = r'True'
            try:
                self.curOraHost = qtStrings.split('@')[1].split(':')[0]
                self.curOraPort = qtStrings.split('/')[0].split(':')[1]
                self.curOraUser = qtStrings.split('@')[0]
                self.curOraSID = qtStrings.split('/')[1]
                self.curOraDSN = cx_Oracle.makedsn(self.curOraHost, self.curOraPort, self.curOraSID, region=None, sharding_key=None,
                                      super_sharding_key=None)
                conn = sqlite3.connect(sqlitedb)
                cursor = conn.cursor()
                cursor.execute(
                    """select hostname,password from """ + tbRegistryDB + """ where host=? and user=? and instanceName=?""",
                    (self.curOraHost, self.curOraUser, self.curOraSID,))
                resultList = cursor.fetchall()
                conn.close()
                if len(resultList) == 1:
                    self.curHostname = resultList[0][0]
                    self.curOraPassword = resultList[0][1]
            except Exception, error:
                msg = 'Error, Account verification failed.\n' + unicode(error)
                QtGui.QMessageBox.about(self, 'About', msg)
        else:
            self.connStatus = r'False'
            msg = 'Error, Please connect to the database before performing the operation.\n'
            QtGui.QMessageBox.about(self, 'About', msg)
    def stackWidgetSwitch(self):
        try:
            curItem = self.ui.treeWidget.currentItem()
            curCol = self.ui.treeWidget.currentColumn()
            curItemText = self.ui.treeWidget.currentItem().text(0)
            curIndexRow = self.ui.treeWidget.currentIndex().row()
            curIndexCol = self.ui.treeWidget.currentIndex().column()
            indexFromItem = self.ui.treeWidget.indexFromItem(curItem).row()

            if curItemText == r'Monitor' or curItemText == r'Installation' or curItemText == r'Maintenance' or curItemText == r'Inspection':
                pass
            elif curItemText == r'Server Status':
                self.ui.stackedWidget.setCurrentIndex(0)
            elif curItemText == r'Users and Privileges':
                self.ui.stackedWidget.setCurrentIndex(1)
            elif curItemText == r'System Variables':
                self.ui.stackedWidget.setCurrentIndex(2)
            elif curItemText == r'Report Export':
                self.ui.stackedWidget.setCurrentIndex(3)
            elif curItemText == r'Oracle Installation':
                self.ui.stackedWidget.setCurrentIndex(4)
            elif curItemText == r'MySQL Installation':
                self.ui.stackedWidget.setCurrentIndex(5)
            elif curItemText == r'PostgreSQL Installation':
                self.ui.stackedWidget.setCurrentIndex(6)
            elif curItemText == r'Oracle DDL Authorization':
                self.ui.stackedWidget.setCurrentIndex(7)
            elif curItemText == r'Database Increment':
                self.ui.stackedWidget.setCurrentIndex(8)
            elif curItemText == r'Oracle DataGuard':

                try:
                    conn = sqlite3.connect(sqlitedb)
                    cursor = conn.cursor()
                    cursor.execute(
                        """select distinct host from """ + tbRegistryDB)
                    hostList = cursor.fetchall()
                    cursor.close()
                    conn.close()
                except Exception, error:
                    msg = 'Error, Account verification failed.\n' + unicode(error)
                    QtGui.QMessageBox.about(self, 'About', msg)
                else:
                    if hostList:
                        self.ui.comboBox_2.clearFocus()
                        self.ui.comboBox_2.clear()
                        self.ui.comboBox_3.clearFocus()
                        self.ui.comboBox_3.clear()

                        for i in range(0, len(hostList)):
                            host = hostList[i][0]
                            self.ui.comboBox_2.addItem(host)
                            self.ui.comboBox_3.addItem(host)
                    if self.ui.comboBox.currentText():
                        curOraHost = unicode(self.ui.comboBox.currentText()).encode('utf-8').split(':')[0].split('@')[1]
                        idx = self.ui.comboBox_2.findText(curOraHost)
                        self.ui.comboBox_2.setCurrentIndex(idx)
                        self.ui.comboBox_2.setEnabled(False)
                        self.ui.comboBox_3.setCurrentIndex(-1)

                    else:
                        self.ui.comboBox_2.setCurrentIndex(-1)
                        self.ui.comboBox_3.setCurrentIndex(-1)

                    self.ui.stackedWidget.setCurrentIndex(9)
            elif curItemText == r'ASM DiskGroup':
                try:
                    conn = sqlite3.connect(sqlitedb)
                    cursor = conn.cursor()
                    cursor.execute(
                        """select distinct host from """ + tbRegistryDB)
                    hostList = cursor.fetchall()
                    cursor.close()
                    conn.close()
                except Exception, error:
                    msg = 'Error, Account verification failed.\n' + unicode(error)
                    QtGui.QMessageBox.about(self, 'About', msg)
                self.ui.stackedWidget.setCurrentIndex(10)
            else:
                msg = 'Error, Stack widget items out of range.'
                QtGui.QMessageBox.about(self, 'About', msg)
        except Exception, error:
            msg = 'Error, Stack widget switch failed.\n' + format(error)
            QtGui.QMessageBox.about(self, 'About', msg)

    def stackedWidgetIndex09(self):
        self.curAccount()
        if self.connStatus == 'True':
            nodesList = []
            nodesSTYList = []
            pridataList = []
            stadataList = []
            datalist = []
            dataguardSQL = r"""/* Formatted on 2019/11/2 下午 05:05:07 (QP5 v5.256.13226.35538) */
            SELECT distinct
                   i.inst_id,
                   i.instance_name,
                   i.host_name,
                   i.version,
                   i.status,
                   i.thread#,
                   i.archiver,
                   d.name,
                   d.db_unique_name,
                   d.log_mode,
                   d.open_mode,
                   d.protection_mode,
                   d.protection_level,
                   d.remote_archive,
                   d.database_role,
                   d.archivelog_compression,
                   d.switchover_status,
                   d.dataguard_broker,
                   d.force_logging,
                   d.platform_name,
                   DECODE (m.lns_sequence#, NULL, 'None', m.lns_sequence#) lns_sequence#,
                   DECODE (n.mrp_sequence#, NULL, 'None', n.mrp_sequence#) mrp_sequence#,
                   o.max_archived_seq#,
                   p.max_applied_seq#,
                   q.recovery_mode,
                   DECODE (r.log_archive_dest_1, NULL, 'None', r.log_archive_dest_1) log_archive_dest_1,
                   DECODE (s.log_archive_dest_2, NULL, 'None', s.log_archive_dest_2) log_archive_dest_2,
                   DECODE (t.log_archive_dest_3, NULL, 'None', t.log_archive_dest_3) log_archive_dest_3,
                   DECODE (u.gap_seq#, NULL, 'None', u.gap_seq#) gap_seq#,
                   DECODE (v.transport_lag, NULL, 'None', v.transport_lag) transport_lag,
                   DECODE (w.apply_lag, NULL, 'None', w.apply_lag) apply_lag
              FROM gv$database d
                   LEFT JOIN gv$instance i ON d.inst_id = i.inst_id
                   LEFT JOIN (SELECT inst_id, sequence# AS lns_sequence#
                                FROM gv$managed_standby
                               WHERE process = 'LNS') m
                      ON d.inst_id = m.inst_id
                   LEFT JOIN (SELECT inst_id, sequence# AS mrp_sequence#
                                FROM gv$managed_standby
                               WHERE process LIKE '%MRP%') n
                      ON d.inst_id = n.inst_id
                   LEFT JOIN
                   (SELECT UNIQUE
                           THREAD#,
                           MAX (SEQUENCE#) OVER (PARTITION BY THREAD#)
                              AS max_archived_seq#
                      FROM gv$archived_log) o
                      ON i.thread# = o.THREAD#
                   LEFT JOIN
                   (SELECT UNIQUE
                           THREAD#,
                           MAX (SEQUENCE#) OVER (PARTITION BY THREAD#)
                              AS max_applied_seq#
                      FROM gv$archived_log
                     WHERE applied = 'YES') p
                      ON i.thread# = p.THREAD#
                   LEFT JOIN (SELECT inst_id, recovery_mode
                                FROM gv$archive_dest_status
                               WHERE status = 'VALID' AND TYPE = 'LOCAL') q
                      ON d.inst_id = q.inst_id
                   LEFT JOIN
                   (SELECT inst_id,
                              destination
                           || '('
                           || target
                           || '-'
                           || archiver
                           || ''
                           || error
                           || ')'
                              AS log_archive_dest_1
                      FROM gv$archive_dest
                     WHERE status = 'VALID' AND dest_name = 'LOG_ARCHIVE_DEST_1') r
                      ON d.inst_id = r.inst_id
                   LEFT JOIN
                   (SELECT inst_id,
                              destination
                           || '('
                           || target
                           || '-'
                           || archiver
                           || ''
                           || error
                           || ')'
                              AS log_archive_dest_2
                      FROM gv$archive_dest
                     WHERE status = 'VALID' AND dest_name = 'LOG_ARCHIVE_DEST_2') s
                      ON d.inst_id = s.inst_id
                   LEFT JOIN
                   (SELECT inst_id,
                              destination
                           || '('
                           || target
                           || '-'
                           || archiver
                           || ''
                           || error
                           || ')'
                              AS log_archive_dest_3
                      FROM gv$archive_dest
                     WHERE status = 'VALID' AND dest_name = 'LOG_ARCHIVE_DEST_3') t
                      ON d.inst_id = t.inst_id
                   LEFT JOIN
                   (SELECT inst_id, low_sequence# || '-' || high_sequence# AS gap_seq#
                      FROM gv$archive_gap) u
                      ON d.inst_id = u.inst_id
                   LEFT JOIN (SELECT inst_id, VALUE AS transport_lag
                                FROM gv$dataguard_stats
                               WHERE name = 'transport lag') v
                      ON d.inst_id = v.inst_id
                   LEFT JOIN (SELECT inst_id, VALUE AS apply_lag
                                FROM gv$dataguard_stats
                               WHERE name = 'apply lag') w
                      ON d.inst_id = w.inst_id
                   order by i.inst_id"""
            try:
                connection = cx_Oracle.connect(self.curOraUser, self.curOraPassword, self.curOraDSN,
                                               cx_Oracle.SYSDBA)
                cursor1 = connection.cursor()
                cursor2 = connection.cursor()
                cursor1.execute(r"select distinct inst_id, host_name from gv$instance order by 1")
                cursor2.execute(dataguardSQL)
                nodesList = cursor1.fetchall()
                pridataList = cursor2.fetchall()
                # print('nodesList')
                # print(nodesList)
                # print('pridataList')
                # print(pridataList)
                cursor1.close()
                cursor2.close()
                connection.close()
            except Exception, error:
                msg = 'Error, Login failed(can not connect to oracle).\n' + unicode(error)
                QtGui.QMessageBox.about(self, 'About', msg)
            # Standby
            ipsty = unicode(self.ui.comboBox_3.currentText()).encode('utf-8').strip()
            # ipsty = unicode(self.ui.comboBox_2.currentText()).encode('utf-8').strip()
            try:
                conn = sqlite3.connect(sqlitedb)
                cursor = conn.cursor()
                cursor.execute(
                    """select distinct hostname,host,port,user,password,instanceName,defaultRole from """ + tbRegistryDB + """ where user='sys' and host=?""",
                    (ipsty,))
                resultList = cursor.fetchall()
                conn.close()
            except Exception, error:
                msg = 'Error, Login failed(can not connect to oracle).\n' + unicode(error)
                QtGui.QMessageBox.about(self, 'About', msg)
            else:
                self.hostnamesty = resultList[0][0]
                self.hoststy = resultList[0][1]
                self.portsty = resultList[0][2]
                self.usersty = resultList[0][3]
                self.passwordsty = resultList[0][4]
                self.sidsty = resultList[0][5]
                self.rolesty = resultList[0][6]
                self.dsnsty = cx_Oracle.makedsn(self.hoststy, self.portsty, self.sidsty, region=None, sharding_key=None,
                                                super_sharding_key=None)
            try:
                connection = cx_Oracle.connect(self.usersty, self.passwordsty, self.dsnsty,
                                               cx_Oracle.SYSDBA)
                cursor1 = connection.cursor()
                cursor2 = connection.cursor()
                cursor1.execute(r"select distinct inst_id, host_name from gv$instance order by 1")
                cursor2.execute(dataguardSQL)
                nodesSTYList = cursor1.fetchall()
                stadataList = cursor2.fetchall()
                # print('nodesSTYList')
                # print(nodesSTYList)
                # print('stadataList')
                # print(stadataList)
                cursor1.close()
                cursor2.close()
                connection.close()
            except Exception, error:
                msg = 'Error, Login failed(can not connect to oracle).\n' + unicode(error)
                QtGui.QMessageBox.about(self, 'About', msg)

            HHeaderList = []
            for p in nodesList + nodesSTYList:
                HHeaderList.append(p[1])
            VHeaderList = ['inst_id','instance_name','host_name','version','status','thread#','archiver','name','db_unique_name','log_mode','open_mode','protection_mode','protection_level','remote_archive','database_role','archivelog_compression','switchover_status','dataguard_broker','force_logging','platform_name','lns_sequence#','mrp_sequence#','max_archived_seq#','max_applied_seq#','recovery_mode','log_archive_dest_1','log_archive_dest_2','log_archive_dest_3','gap_seq#','transport_lag','apply_lag']

            # 设置表头 VHeaderList[i].capitalize()
            self.ui.tableWidget.setColumnCount(len(HHeaderList))
            self.ui.tableWidget.setRowCount(len(VHeaderList))
            textFont = QtGui.QFont("song", 10, QtGui.QFont.Bold)
            for h in range(0, len(HHeaderList)):
                hitem = QtGui.QTableWidgetItem()
                self.ui.tableWidget.setHorizontalHeaderItem(h, hitem)
                hitem = self.ui.tableWidget.horizontalHeaderItem(h)
                hitem.setText(_translate("MainWindow", HHeaderList[h].upper(), None))
                hitem.setFont(textFont)  # 设置字体
                hitem.setBackgroundColor(QtGui.QColor(0, 128, 0))  # 设置单元格背景颜色
                hitem.setTextColor(QtGui.QColor(0, 0, 0))  # 设置文字颜色
            for v in range(0, len(VHeaderList)):
                vitem = QtGui.QTableWidgetItem()
                self.ui.tableWidget.setVerticalHeaderItem(v, vitem)
                vitem = self.ui.tableWidget.verticalHeaderItem(v)
                vitem.setText(_translate("MainWindow", VHeaderList[v].upper(), None))
                # vitem.setFont(textFont)  # 设置字体
                vitem.setBackgroundColor(QtGui.QColor(0, 128, 0))  # 设置单元格背景颜色
                vitem.setTextColor(QtGui.QColor(0, 0, 0))  # 设置文字颜色

            # 获取数据
            dataList = pridataList + stadataList
            print('dataList')
            print(dataList)
            for col in dataList:
                j = dataList.index(col)
                #(1, 'newsfc', 'jc-tt-db-b1', '11.2.0.4.0', 'OPEN', 1, 'STARTED', 'NEWSFC')
                for i in range(0, len(col)):
                    text = str(unicode(col[i]).encode('utf-8')).strip()
                    self.ui.tableWidget.setItem(i, j, QtGui.QTableWidgetItem(text))
                    self.ui.tableWidget.resizeColumnsToContents()  # 将列调整到跟内容大小相匹配
                    self.ui.tableWidget.resizeRowsToContents()  # 将行大小调整到跟内容的大学相匹配
                    self.ui.tableWidget.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
                    self.ui.tableWidget.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
            try:
                connection = cx_Oracle.connect(self.curOraUser, self.curOraPassword, self.curOraDSN, cx_Oracle.SYSDBA)
                cursor = connection.cursor()
                # cursor.execute(r"select process,status,client_process,thread#,sequence# from gv$managed_standby where process = 'LNS'")
                cursor.execute(
                    r"select sequence# from gv$managed_standby where process = 'LNS'")
                pryLNSList = cursor.fetchall()
                cursor.close()
                connection.close()
            except Exception, error:
                msg = 'Error, Login failed(can not connect to oracle).\n' + unicode(error)
                QtGui.QMessageBox.about(self, 'About', msg)
            try:
                connection = cx_Oracle.connect(self.usersty, self.passwordsty, self.dsnsty, cx_Oracle.SYSDBA)
                cursor = connection.cursor()
                cursor.execute( r"select sequence# from gv$managed_standby where process like 'MRP%'")
                styMRPList = cursor.fetchall()
                cursor.close()
                connection.close()
            except Exception, error:
                msg = 'Error, Login failed(can not connect to oracle).\n' + unicode(error)
                QtGui.QMessageBox.about(self, 'About', msg)
            DGsyncStatusList = []
            for pryLNS in pryLNSList:
                pryLNSSEQ = pryLNS[0]
                for styMRP in styMRPList:
                    styMRPSEQ = styMRP[0]
                    if styMRPSEQ == pryLNSSEQ:
                        DGsyncStatusList.append(r'True')
                    else:
                        DGsyncStatusList.append(r'False')
            if r'True' in DGsyncStatusList:
                msg = 'OK, Data synchronization status is successful.\n'
                QtGui.QMessageBox.about(self, 'About', msg)
            else:
                msg = 'ERROR, Data synchronization status is failed.\n'
                QtGui.QMessageBox.about(self, 'About', msg)
        else:
            msg = 'Error, No connection to the database.\n'
            QtGui.QMessageBox.about(self, 'About', msg)
    def stackedWidgetIndex10(self):
        self.curAccount()
        ASMStatusSQL = """select inst_id, group_number, name, round(total_mb / 1024,2) as total_gb, round((total_mb - free_mb) / 1024) as used_gb, round(free_mb / 1024,2) as free_gb,round((total_mb - free_mb) * 100 / total_mb) || '%' as used_rate, state, type,offline_disks,voting_files from gv$asm_diskgroup order by inst_id"""
        if self.connStatus == 'True':
            try:
                connection = cx_Oracle.connect(self.curOraUser, self.curOraPassword, self.curOraDSN,
                                               cx_Oracle.SYSDBA)
                cursor = connection.cursor()
                cursor.execute(ASMStatusSQL)
                ASMStatusList = cursor.fetchall()
                cursor.close()
                connection.close()
            except Exception, error:
                msg = 'Error, Login failed(can not connect to oracle).\n' + unicode(error)
                QtGui.QMessageBox.about(self, 'About', msg)
            else:
                Htitle = ['inst_id','group_number','name','total_gb','used_gb','free_gb','used_rate','state','type','offline_disks','voting_files']
                # 设置表头 VHeaderList[i].capitalize()
                self.ui.tableWidget_2.setColumnCount(len(Htitle))
                self.ui.tableWidget_2.setRowCount(len(ASMStatusList))
                textFont = QtGui.QFont("song", 10, QtGui.QFont.Bold)
                for h in range(0, len(Htitle)):
                    hitem = QtGui.QTableWidgetItem()
                    self.ui.tableWidget_2.setHorizontalHeaderItem(h, hitem)
                    hitem = self.ui.tableWidget_2.horizontalHeaderItem(h)
                    hitem.setText(_translate("MainWindow", Htitle[h].upper(), None))
                    hitem.setFont(textFont)  # 设置字体
                    hitem.setBackgroundColor(QtGui.QColor(0, 128, 0))  # 设置单元格背景颜色
                    hitem.setTextColor(QtGui.QColor(0, 0, 0))  # 设置文字颜色
                # 获取数据
                dataList = ASMStatusList
                for row in dataList:
                    i = dataList.index(row)
                    # (1, 'newsfc', 'jc-tt-db-b1', '11.2.0.4.0', 'OPEN', 1, 'STARTED', 'NEWSFC')
                    for j in range(0, len(row)):
                        text = str(unicode(row[j]).encode('utf-8')).strip()
                        self.ui.tableWidget_2.setItem(i, j, QtGui.QTableWidgetItem(text))
                        self.ui.tableWidget_2.resizeColumnsToContents()  # 将列调整到跟内容大小相匹配
                        self.ui.tableWidget_2.resizeRowsToContents()  # 将行大小调整到跟内容的大学相匹配
                        self.ui.tableWidget_2.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
                        self.ui.tableWidget_2.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.ui.stackedWidget.setCurrentIndex(10)


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    main = MainWindow()


    # depHostsDialog = DialogDepHosts()
    # depUsersDialog = DialogDepUsers()
    # depDeployDialog = DialogDepDeploy()

    main.show()
    sys.exit(app.exec_())
