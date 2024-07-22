
import sys, os, json
from PyQt6 import uic, QtCore, QtSvg
from PyQt6 import QtWidgets
from PyQt6.QtCore import Qt, QCoreApplication
from PyQt6 import QtGui

import gazu



class ReadOnlyDelegate(QtWidgets.QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        return
    
class EditedDelegate(QtWidgets.QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = super().createEditor(parent, option, index)
        # Access the QTableWidget by traversing up the widget hierarchy
        table_widget = parent
        while not isinstance(table_widget, QtWidgets.QTableWidget):
            table_widget = table_widget.parent()
        row = index.row()
        column = index.column()
        item = table_widget.item(row, column)
        
        if item:
            # Do something with the QTableWidgetItem
            item.setEdited(True)  # Assuming you want to mark it as edited
        
        return editor
    
class TableItem(QtWidgets.QTableWidgetItem):
    def __init__(self, text=''):
        super().__init__(text)
        self.isEdited = False

    def setEdited(self, edited):
        self.isEdited = edited
       #print(self.parent())

class project_settings(QtWidgets.QWidget):
    def __init__(self, main_app):
        super(project_settings, self).__init__()

        self.project = main_app.project_box.currentText()
        uic.loadUi(os.path.join(main_app.root_folder, 'ui', 'project_settings.ui'), self)
        self.setWindowTitle("Kitsu Connect Project Settings - "+ self.project)
        self.setWindowFlags(Qt.WindowType.WindowCloseButtonHint)

        self.save_button.pressed.connect(self.save)
        self.load_button.pressed.connect(self.getInfos)

        self.edited_selection = False
        self.project_data = {}

    def getInfos(self):
        self.table.setRowCount(0)
        project = gazu.project.get_project_by_name(self.project)
        delegate = ReadOnlyDelegate(self)
        self.table.setItemDelegateForColumn(0, delegate)
        self.table.setItemDelegateForColumn(1, EditedDelegate(self))

        self.project_data = project['data']
        if not project['data'] or project['data'] == 'None':
            self.project_data = {'project_root':None}

        if not 'project_root' in self.project_data.keys():
            self.project_data['project_root'] = None
            
        row_count = 0

        for i in self.project_data:
            self.table.insertRow(row_count)
            self.table.setItem(row_count, 0, QtWidgets.QTableWidgetItem(i))
            item = TableItem(str(self.project_data[i]))
            self.table.setItem(row_count, 1, item)
            row_count+1
            item.setEdited(False)

        for i in reversed(list(project.keys())):
            if i != 'data':
                self.table.insertRow(row_count)
                self.table.setItem(row_count, 0, QtWidgets.QTableWidgetItem(i))
            
                if type(project[i]) is bool:
                    item = TableItem(project[i])
                    item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
                    if project[i]:
                        item.setCheckState(Qt.CheckState.Checked)
                    else:
                        item.setCheckState(Qt.CheckState.Unchecked)
                elif project[i] is None:
                    item = TableItem(None)       
                else:
                    item = TableItem(str(project[i]))

                self.table.setItem(row_count, 1, item)
                row_count+1
                item.setEdited(False)
    
        self.table.resizeColumnToContents(0)
        self.table.resizeColumnToContents(1)
        self.adjustSize()
        return True
        
    def save(self):
        
        project = gazu.project.get_project_by_name(self.project)
        rows = self.table.rowCount()

        for row in range(rows):
            element = [self.table.item(row, 0).text() , self.table.item(row, 1).text()]
            if self.table.item(row, 1).isEdited:
                if element[0] in project.keys():
                    try:
                        if type(project[element[0]]) is bool:
                            if self.table.item(row, 1).checkState() == Qt.CheckState.Checked:
                                element[1] = True
                            else:
                                element[1] = False
                    except:
                        pass
                    project[element[0]] = element[1]
                if element[0] in self.project_data.keys():
                    self.project_data[element[0]] = element[1] 
                print('Updated', element[0])

        print(project)
        project['data'] = self.project_data
        gazu.project.update_project(project)
        self.edited_selection = False


