from os import path
from pydm import Display
import os
import subprocess
from PyQt5 import QtWidgets
import silx.io

class MyDisplay(Display):


    def __init__(self, parent=None, args=None, macros=None):
        super(MyDisplay, self).__init__(parent=parent, args=args, macros=macros)
        self.macros = macros

        self.initializa_setup()
        self.get_hdf5_data()
        self.plot_counters()
        self.select_x_axis()
        self.connect_check_boxes()

    def ui_filename(self):
        return 'plot_hdf5.ui'

    def ui_filepath(self):
        return path.join(path.dirname(path.realpath(__file__)), self.ui_filename())

    def initializa_setup(self):
        self.checked_now = None

    def get_hdf5_data(self):
        self.counters_data = {}
        self.motors_data = {}

        with silx.io.open(self.macros['FILE']) as sf:
            self.data = sf
            instrument = sf['Scan/scan_000/instrument']
            for i in instrument:
                # If the data is called 'data' them its a motor, otherwise its a counter
                if 'data' in instrument[i]:
                    self.motors_data[i] = instrument[i]['data'][:]
                else:
                    self.counters_data[i] = instrument[i][i][:]

    def set_plot(self):
        for i in self.counters_data.keys():
            if self.checked_now:
                self.plot.addCurve(self.motors_data[self.checked_now], self.counters_data[i], legend = i)
            else:
                points = [i for i in range(len(self.counters_data[i]))]
                self.plot.addCurve(points, self.counters_data[i], legend = i)
            if self.dict_counters[i].isChecked():
                self.plot.getCurve(i)
            else:
                self.plot.remove(i)

    def connect_check_boxes(self):
        for i in self.counters_data.keys():
            self.dict_counters[i].clicked.connect(self.set_plot)
        for i in self.motors_data.keys():
            self.dict_motors[i].clicked.connect(self.uncheck_other_motors)

    def plot_counters(self):
        self.plot = self.ui.plot1d  # Create the plot widget
        self.dict_counters = {}
        for i in self.counters_data.keys():
            self.dict_counters[i] = QtWidgets.QCheckBox()
            self.ui.verticalLayout_counter.addWidget(self.dict_counters[i])
            self.dict_counters[i].setText(i)

    def select_x_axis(self):
        self.dict_motors = {}
        for i in self.motors_data.keys():
            self.dict_motors[i] = QtWidgets.QCheckBox()
            self.ui.verticalLayout_motors.addWidget(self.dict_motors[i])
            self.dict_motors[i].setText(i)

    def uncheck_other_motors(self):
        for motor in self.dict_motors.keys():
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
