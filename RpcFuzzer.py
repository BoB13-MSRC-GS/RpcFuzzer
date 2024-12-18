import sys
import os
import shutil
import configparser
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox
from PyQt5 import uic
from generate import Generate
import time, subprocess

class MyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        if getattr(sys, 'frozen', False):
            self.program_temp_directory = os.path.dirname(os.path.abspath(__file__))
        else:
            self.program_temp_directory = os.path.dirname(os.path.abspath(__file__)) + "\sfiles"
        self.program_directory = os.path.dirname(os.path.abspath(sys.executable))
        
        uic.loadUi(self.program_temp_directory + '\Main.ui', self)
        self.setFixedSize(self.size())
        
        self.DEV_PATH = None
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        self.loadConfigPaths()

        self.IDL_Button.clicked.connect(self.openFileDialogForIDL)
        self.input_checkBox.stateChanged.connect(self.inputCheckboxSwitch)
        self.output_checkBox.stateChanged.connect(self.outputCheckboxSwitch)
        self.methods_listWidget.itemDoubleClicked.connect(self.generate_method)
        self.retry_pushButton.clicked.connect(self.generate_retry)
        self.all_compile_pushButton.clicked.connect(self.generate_all_compile)
        self.all_run_pushButton.clicked.connect(self.all_run)
        
    def loadConfigPaths(self):
        if 'Path' in self.config:
            if 'dev_path' in self.config['Path']:
                self.DEV_PATH = self.config['Path']['dev_path']
    
    def inputCheckboxSwitch(self):
        self.input_lineEdit.setEnabled(not self.input_checkBox.isChecked())

    def outputCheckboxSwitch(self):
        self.output_lineEdit.setEnabled(not self.output_checkBox.isChecked())

    def openFileDialogForIDL(self):
        fname = QFileDialog.getOpenFileName(self, 'IDL 파일 선택', 'test.idl', 'IDL Files (*.idl)')[0]
        if fname:
            self.IDL_Path = fname
            self.copyIdlFile()

    def copyIdlFile(self):
        idl_directory = os.path.join(self.program_directory, 'idl')
        cpp_directory = os.path.join(self.program_directory, 'cpp')
        
        if not self.input_checkBox.isChecked():
            file_basename = self.input_lineEdit.text()
            if file_basename == '':
                return
            filename = file_basename + ".idl"
        else:
            filename = os.path.basename(self.IDL_Path)
            if filename.count('_') == 2:
                filename = filename.split('_')[1]
                filename = filename.split('.')[0]
                filename = filename + ".idl"
            file_basename, _ = os.path.splitext(filename)

        self.idl_target_directory = os.path.join(idl_directory, file_basename)
        self.cpp_target_directory = os.path.join(cpp_directory, file_basename)
        idl_path = os.path.join(self.idl_target_directory, filename)
        print(idl_path)
        if not os.path.exists(self.idl_target_directory):
            os.makedirs(self.idl_target_directory)
        if not os.path.exists(self.cpp_target_directory):
            os.makedirs(self.cpp_target_directory)
        
        self.generate = Generate(self.idl_target_directory, self.cpp_target_directory, file_basename)
        self.generate.clear_file()
        self.generate.clear_file2()
        shutil.copy(self.IDL_Path, idl_path)
        self.generate.reproduce_idl()
        if self.generate.midl_compile():
            self.method_data = self.generate.parse_idl()
            # print(self.method_data)
            self.methods_listWidget.clear()
            for i in range(len(self.method_data)):
                self.methods_listWidget.insertItem(i, self.method_data[i]['method_name'])
            self.all_compile_pushButton.setEnabled(True)
            self.all_run_pushButton.setEnabled(True)
        else:
            QMessageBox.critical(self, '실패', 'Failed MIDL Compile !!')
    
    def generate_method(self):
        item = (self.methods_listWidget.selectedItems()[0]).text()
        print(item)
        self.generate.generate_c_code(item, self.handle_checkBox.isChecked(), self.nulldere_checkBox.isChecked())
        output = ''
        if not self.output_checkBox.isChecked():
            output = self.output_lineEdit.text()
        self.generate.generate_cpp(self.prot_comboBox.currentText(), self.EndPoint_lineEdit.text(), output)
        if not self.generate.cpp_compile(output, self.DEV_PATH):
            QMessageBox.critical(self, '실패', 'Failed Cpp Compile !!')
        self.generate.clear_file2()
        self.retry_pushButton.setEnabled(True)
    
    def generate_retry(self):
        output = ''
        if not self.output_checkBox.isChecked():
            output = self.output_lineEdit.text()
        if not self.generate.cpp_compile(output, self.DEV_PATH):
            QMessageBox.critical(self, '실패', 'Failed Cpp Compile !!')
        self.generate.clear_file2()
    
    def generate_all_compile(self):
        for x in range(self.methods_listWidget.count()):
            item = self.methods_listWidget.item(x).text()
            print(item)
            self.generate.generate_c_code(item, self.handle_checkBox.isChecked(), self.nulldere_checkBox.isChecked())
            output = item
            self.generate.generate_cpp(self.prot_comboBox.currentText(), self.EndPoint_lineEdit.text(), output)
            if not self.generate.cpp_compile(output, self.DEV_PATH):
                QMessageBox.critical(self, '실패', f'Failed Cpp Compile - {item}!!')
            self.generate.clear_file2()
            time.sleep(0.25)
    
    def all_run(self):
        for x in range(self.methods_listWidget.count()):
            item = self.methods_listWidget.item(x).text()
            program_path = os.path.join(self.cpp_target_directory, item + ".exe")
            print(program_path)
            if os.path.isfile(program_path):
                # subprocess.Popen([program_path], shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE)
                # subprocess.Popen(
                #     ["cmd.exe", "/c", f"start {program_path}"],
                #     shell=True
                # )
                subprocess.Popen(
                    [self.program_temp_directory + '\PsExec64.exe', "-s", "-i", f"{program_path}"],
                    shell=True
                )
                time.sleep(0.05)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    myApp = MyApp()
    myApp.show()
    sys.exit(app.exec_())

# pyinstaller -F --add-data="sfiles/*;./" RpcFuzzer.py