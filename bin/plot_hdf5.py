from collections import Counter
import os
from os import path
import time
import datetime
import numpy as np
from pydm import Display
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMessageBox, QTableWidgetItem, QHeaderView, QWidget, QCheckBox, QHBoxLayout
import silx.io
from silx.gui import qt
from silx.gui.plot import LegendSelector
from PyQt5.QtCore import QObject, QThread, pyqtSignal, QCoreApplication, QTimer
from PyQt5 import QtCore
import fits
import plot_actions

class MyDisplay(Display):

    def __init__(self, parent=None, args=None, macros=None):
        super(MyDisplay, self).__init__(parent=parent, args=args, macros=macros)
        self.macros = macros
        self.initializa_setup()

    def ui_filename(self):
        return 'plot_hdf5.ui'

    def ui_filepath(self):
        return path.join(path.dirname(path.realpath(__file__)), self.ui_filename())

    def loop(self):
        """Loop to check if a curve is selected or not"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.custom_signals)
        self.timer.start(250) #trigger every .25 seconds.

    def custom_signals(self):
        """If there is an active curve, do the stats for that"""

        self.legend_widget.updateLegends()
        dir_files = os.listdir(self.path)
        dir_files = [i for i in dir_files if i.endswith('.hdf5')]
        dir_files.sort() 
        if dir_files != self.dir_files:
            self.clear_table_files()           

    def initializa_setup(self):
        """Initialize all setup variables"""
        self.plot = self.ui.plotwindow
        self.curve_now = None
        self.checked_now = None
        self.monitor_checked_now = None
        self.store_current_counters = []
        self.store_current_motors= []
        self.store_current_monitors = []
        self.files = self.macros['FILES']
        head, tail = os.path.split(self.files[0])
        self.path = head
        self.table_files()
        self.new_buttons()
        self.build_plot()
        self.legend_widget()

    def build_plot(self):
        self.get_hdf5_data()
        self.assert_data()
        self.build_plot_table()
        # self.connect_check_boxes()
        self.set_standard_plot(self.store_current_counters, self.store_current_motors, self.store_current_monitors)
        self.connections()
        self.loop()

    def legend_widget(self):
        self.legend_widget = LegendSelector.LegendsDockWidget(parent=self, plot = self.plot)
        self.verticalLayout_left.addWidget(self.legend_widget)

    def get_hdf5_data(self):
        """Read Scan data and store into dicts, also creates a dict with simplified data names"""
        self.counters_data = {}
        self.motors_data = {}
        for file in self.files:
            fo = open(file)
            fo.close()
            with silx.io.open(file) as sf:
                self.data = sf
                head, tail = os.path.split(file)
                instrument = sf['Scan/scan_000/instrument']
                for i in instrument:
                    # If the data is called 'data' them its a motor, otherwise its a counter
                    if 'data' in instrument[i]:
                        self.motors_data[i + '__data__' + tail] = instrument[i]['data'][:]
                    else:
                        self.counters_data[i + '__data__' + tail] = instrument[i][i][:]

    def modification_date(self, filename):
        t = os.path.getmtime(filename)
        mt = str(datetime.datetime.fromtimestamp(t))[:-7]
        return mt

    def table_files(self):
        row = 0
        self.dir_files = os.listdir(self.path)
        self.dir_files = [i for i in self.dir_files if i.endswith('.hdf5')]
        self.dir_files.sort()  
        for file in self.dir_files:
            date = self.modification_date(os.path.join(self.path,file))
            with silx.io.open(os.path.join(self.path,file)) as sf:
                instrument = sf['Scan/scan_000/instrument']
                motors = ''
                len_points = 0
                for i in instrument:
                    # If the data is called 'data' them its a motor, otherwise its a counter
                    if 'data' in instrument[i]:
                        motors += i + ', '
                        len_points = str(len(instrument[i]['data']))
                motors = motors[:-2]
            self.tableWidget.insertRow(row)
            self.tableWidget.setItem(row, 0, QTableWidgetItem(file))
            self.tableWidget.setItem(row, 1, QTableWidgetItem(motors))
            self.tableWidget.setItem(row, 2, QTableWidgetItem(len_points))
            self.tableWidget.setItem(row, 3, QTableWidgetItem(date))
            # self.tableWidget.setItem(row, 3, QTableWidgetItem(date))
            # widget   = QWidget(parent=self.tableWidget)
            # checkbox = QCheckBox()
            # checkbox.setCheckState(QtCore.Qt.Unchecked)
            # layoutH = QHBoxLayout(widget)
            # layoutH.addWidget(checkbox)
            # layoutH.setAlignment(QtCore.Qt.AlignCenter)
            # layoutH.setContentsMargins(0, 0, 0, 0)           
            # self.tableWidget.setCellWidget(row, 2, widget)                  # <----
            # self.tableWidget.setItem(row, 2, QTableWidgetItem(str(row)))
            checkbox = QtWidgets.QCheckBox(parent=self.tableWidget)
            checkbox.clicked.connect(self.on_state_changed)
            self.tableWidget.setCellWidget(row, 4, checkbox)
            full_file_path = self.path + '/' + file
            if full_file_path in self.files: 
                checkbox.setChecked(True)
            row += 1

        header = self.tableWidget.horizontalHeader()
        # # header.setResizeMode(0, QtGui.QHeaderView.Stretch)
        header.setResizeMode(0, QHeaderView.ResizeToContents)
        header.setResizeMode(1, QHeaderView.ResizeToContents)
        header.setResizeMode(2, QHeaderView.ResizeToContents)
        header.setResizeMode(3, QHeaderView.ResizeToContents)
        header.setResizeMode(4, QHeaderView.ResizeToContents)

    def on_state_changed(self):
        ch = self.sender()
        ix = self.tableWidget.indexAt(ch.pos())
        file_now = self.tableWidget.item(ix.row(), 0).text()
        full_file_path = self.path + '/' + file_now
        if ch.isChecked():
            self.files.append(full_file_path)
        else:
            self.files.remove(full_file_path)
        self.clear_all()
        self.build_plot()


    def assert_data(self):
        """Check if the files have difference between motor and counters, and also provides simplified data labels for the plot"""
        motor_prefix = [i.split('__data__')[0] for i in self.motors_data.keys()]
        counter_prefix = [i.split('__data__')[0] for i in self.counters_data.keys()]
        # Get only the instrument name without the file associated to it, and also remove all duplicated
        # ones by transforming the list into a set before iterates over it
        self.simplified_motor_data = set(motor_prefix) # Simplified data label
        self.simplified_counter_data = set(counter_prefix) # Simplified data label
        
        motor_count = Counter(motor_prefix)
        counters_count = Counter(counter_prefix)
        flag_diff = False # Flag to tell if a motor or counter is different between files
        for key in motor_count.keys():
            if motor_count[key] != len(self.files):
                flag_diff = True
        # for key in counters_count.keys():
        #     if counters_count[key] != len(self.files):
        #         flag_diff = True
        # if flag_diff:
        #        msg = QMessageBox()
        #        msg.setIcon(QMessageBox.Information)
        #        msg.setText("There is a difference between counters/motors in the selected files")
        #        msg.setInformativeText("Some counters and/or motors are not present in all the files")
        #        msg.setWindowTitle("Warning")
        #        # msg.setDetailedText("The details are as follows:")
        #        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        #        # msg.buttonClicked.connect(msgbtn)
        #        retval = msg.exec_()

    def connections(self):
        """Do the connections"""
        self.plot.sigPlotSignal.connect(self.plot_signal_handler)
        self.plot.sigActiveCurveChanged.connect(self.update_stat)

    def plot_signal_handler(self, dict_):
        # if dict_['event'] == 'curveClicked':
        #     print(dict_['label'])
        #     print(self.plot.getActiveCurve())
        #     if self.plot.getActiveCurve() is not None:
        #         self.update_stat()
        # print(dict_)
        pass

    def build_plot_table(self):
        row_size = max([len(self.simplified_counter_data), len(self.simplified_motor_data)])
        self.tableWidget_plot.setRowCount(row_size)
        self.counter_checkboxes()
        self.motor_checkboxes()
        self.monitor_checkboxes()
        header = self.tableWidget_plot.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)

    def counter_checkboxes(self):
        """Create counter checkboxes in ther tab interface"""
        self.dict_counters = {}
        row = 0
        for i in self.simplified_counter_data:
            self.dict_counters[i] = QtWidgets.QCheckBox(parent=self.tableWidget_plot)
            self.dict_counters[i].clicked.connect(self.set_plot)
            self.tableWidget_plot.setCellWidget(row, 1, self.dict_counters[i])
            self.dict_counters[i].setText(i)
            row += 1
    def motor_checkboxes(self):
        """Create motor checkboxes in ther tab interface"""
        self.dict_motors = {}
        row = 0
        for i in self.simplified_motor_data:
            self.dict_motors[i] = QtWidgets.QCheckBox(parent=self.tableWidget_plot)
            self.dict_motors[i].clicked.connect(self.uncheck_other_motors)
            self.tableWidget_plot.setCellWidget(row, 0, self.dict_motors[i])
            self.dict_motors[i].setText(i)
            row += 1
        
    def monitor_checkboxes(self):
        """Create counter checkboxes in ther tab interface"""
        self.dict_monitors = {}
        row = 0
        for i in self.simplified_counter_data:
            self.dict_monitors[i] = QtWidgets.QCheckBox(parent=self.tableWidget_plot)
            self.dict_monitors[i].clicked.connect(self.uncheck_other_monitors)
            self.tableWidget_plot.setCellWidget(row, 2, self.dict_monitors[i])
            self.dict_monitors[i].setText(i)
            row += 1

    def uncheck_other_motors(self):
        """Logic to permit only one check box to be checked"""
        for motor in self.simplified_motor_data:
            if self.dict_motors[motor].isChecked():
                if not self.checked_now == str(motor):
                    self.checked_now = motor
                    break
        for motor in self.dict_motors.keys():
            if motor != self.checked_now:
                self.dict_motors[motor].setChecked(False)
        
        motor_false_flag = len(self.dict_motors.keys())
        for motor in self.dict_motors.keys():
            if not self.dict_motors[motor].isChecked():
                motor_false_flag -= 1
        if motor_false_flag == 0:
            self.checked_now = None
        self.set_plot()

    def uncheck_other_monitors(self):
        """Logic to permit only one check box to be checked"""
        for monitor in self.simplified_counter_data:
            if self.dict_monitors[monitor].isChecked():
                if not self.monitor_checked_now == str(monitor):
                    self.monitor_checked_now = monitor
                    break
        for monitor in self.dict_monitors.keys():
            if monitor != self.monitor_checked_now:
                self.dict_monitors[monitor].setChecked(False)
        
        monitor_false_flag = len(self.dict_monitors.keys())
        for monitor in self.dict_monitors.keys():
            if not self.dict_monitors[monitor].isChecked():
                monitor_false_flag -= 1
        if monitor_false_flag == 0:
            self.monitor_checked_now = None
        self.set_plot()

    def set_plot(self):
        """Plot the data"""
        for i in self.simplified_counter_data:
            for file in self.files:
                head, tail = os.path.split(file)
                try:
                    assert isinstance(self.counters_data[i + '__data__' + tail], (list, tuple, np.ndarray))
                    if self.monitor_checked_now:
                        assert isinstance(self.counters_data[self.monitor_checked_now + '__data__' + tail], (list, tuple, np.ndarray))
                    if self.checked_now:
                        assert isinstance(self.motors_data[self.checked_now + '__data__' + tail], (list, tuple, np.ndarray))
                except KeyError as e:
                    pass
                    # print(e)
                else:
                    if self.monitor_checked_now:
                        data = self.counters_data[i + '__data__' + tail]/self.counters_data[self.monitor_checked_now + '__data__' + tail]
                    else:
                        data = self.counters_data[i + '__data__' + tail]
                    if self.checked_now:
                        self.plot.getXAxis().setLabel(self.checked_now)
                        self.plot.addCurve(self.motors_data[self.checked_now + '__data__' + tail], data, legend = i + '__data__' + tail)
                    else:
                        self.plot.getXAxis().setLabel("Points")
                        points = [i for i in range(len(data))]
                        self.plot.addCurve(points, data, legend = i + '__data__' + tail)
                
                    if self.dict_counters[i].isChecked():
                        self.plot.getCurve(i + '__data__' + tail)
                    else:
                        self.plot.remove(i + '__data__' + tail)

        self.plot.resetZoom()

    def new_buttons(self):
        """Method to add new buttons with new funcionalities to the plot"""
        # Create a toolbar and add it to the plot widget
        toolbar = qt.QToolBar()
        self.plot.addToolBar(toolbar)

        # Create clear action and add it to the toolbar
        action = plot_actions.Derivative(self.plot, parent=self.plot)
        toolbar.addAction(action)

    def set_standard_plot(self,counters, motors, monitors):
        for counter in self.dict_counters.keys():
            if counter in counters:
                self.dict_counters[counter].setChecked(True)
        for motor in self.dict_motors.keys():
            if motor in motors:
                self.dict_motors[motor].setChecked(True)
        for monitor in self.dict_monitors.keys():
            if monitor in monitors:
                self.dict_monitors[monitor].setChecked(True)
        self.set_plot()

    def update_stat(self):

        if self.plot.getActiveCurve() is not None:
            activeCurve = self.plot.getActiveCurve()
            x0 = activeCurve.getXData()
            y0 = activeCurve.getYData()
            self.stats = fits.fitGauss(x0,y0)
            self.peak = self.stats[0]
            self.peak_pos = self.stats[1]
            self.fwhm = self.stats[4]
            self.fwhm_pos = self.stats[5]
            self.com = self.stats[6]
            # Update labels
            self.ui.label_fwhm.setText(str(self.fwhm))
            self.ui.label_fwhm_pos.setText(str(self.fwhm_pos))
            self.ui.label_peak.setText(str(self.peak))
            self.ui.label_peak_pos.setText(str(self.peak_pos))
            self.ui.label_com.setText(str(self.com))
        else:
            self.ui.label_fwhm.setText(str(''))
            self.ui.label_fwhm_pos.setText(str(''))
            self.ui.label_peak.setText(str(''))
            self.ui.label_peak_pos.setText(str(''))
            self.ui.label_com.setText(str(''))


    def clear_table_files(self):
        self.tableWidget.clearContents()
        self.tableWidget.setRowCount(0)
        self.table_files()

    def clear_all(self):
        self.store_current_counters = []
        self.store_current_motors = []
        self.store_current_monitors = []
        for i in self.dict_counters.keys():
            if self.dict_counters[i].isChecked():
                self.store_current_counters.append(i)
        for i in self.dict_motors.keys():
            if self.dict_motors[i].isChecked():
                self.store_current_motors.append(i)
        for i in self.dict_monitors.keys():
            if self.dict_monitors[i].isChecked():
                self.store_current_monitors.append(i)
        self.tableWidget_plot.clearContents()
        self.tableWidget_plot.setRowCount(0)
        self.plot.clear()

