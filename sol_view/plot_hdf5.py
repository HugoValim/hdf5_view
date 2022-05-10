# from collections import Counter
import os
from os import path, listdir
from os.path import isfile, join
import datetime

import numpy as np
import pandas as pd

from pydm import Display
from PyQt5.QtCore import Qt
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtWidgets import (
    QTableWidgetItem,
    QHeaderView,
    QCheckBox,
    QSplitter,
    QApplication,
)
from PyQt5.QtCore import QTimer
from PyQt5 import QtCore
from PyQt5.QtWidgets import QMenu
import silx.io
from silx.gui import qt
from PyMca5.PyMcaGui.pymca.ScanWindow import ScanWindow

# from PyMca5.PyMcaGui.plotting.PlotWindow import PlotWindow
# from PyMca5.PyMcaGui.plotting.LegendSelector import LegendListView
# from silx.gui.plot import Plot1D

import plot_actions
import fits


class MyDisplay(Display):
    def __init__(self, parent=None, args=None, macros=None):
        super(MyDisplay, self).__init__(parent=parent, args=args, macros=macros)
        self.app = QApplication.instance()
        self.macros = macros
        self.initializa_setup()
        self.hash = ""

    def ui_filename(self):
        return "plot_hdf5.ui"

    def ui_filepath(self):
        return path.join(path.dirname(path.realpath(__file__)), self.ui_filename())

    def loop(self):
        """Loop to check if a curve is selected or not"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.on_dir_change_update)
        self.timer.start(10000)  # trigger every 10 seconds.

    def keyPressEvent(self, event):
        """Connect keys to methods"""
        if event.key() == QtCore.Qt.Key_Return:
            self.check_selected_checkboxes()
        if event.key() == QtCore.Qt.Key_Escape:
            self.uncheck_selected_checkboxes()
        if event.key() == QtCore.Qt.Key_F11:
            if self.app.main_window.isFullScreen():
                self.app.main_window.showNormal()
            else:
                self.app.main_window.showFullScreen()

    def on_dir_change_update(self):
        scroll_pos = self.tableWidget.verticalScrollBar().value()
        self.clear_table_files()
        self.tableWidget.verticalScrollBar().setValue(scroll_pos)

    def initializa_setup(self):
        """Initialize all setup variables and methods"""
        self.plot = ScanWindow(backend="silx")
        self.verticalLayout.addWidget(self.plot)
        self.plot.setMinimumHeight(300)
        self.plot.setMinimumWidth(600)
        self.curve_now = None
        self.checked_now = None
        self.monitor_checked_now = None
        self.store_current_counters = []
        self.store_current_motors = []
        self.store_current_monitors = []
        self.store_highlighted = []
        self.standard_motor = None
        self.standard_counter = None
        self.files = self.macros["FILES"]
        head, tail = os.path.split(self.files[0])
        self.path = head
        self.__plot_tools()
        self.table_files()
        self.table_stats_layout()
        self.new_buttons()
        self.build_splitable_layout()
        self.build_plot()
        self.connections()

    def table_menu(self):
        """
        Build the menu that is shown when a right cick is done in the
        table widget containing the files

        """
        self.table_menu = QMenu(self.tableWidget)
        # Close the file
        open_action = self.table_menu.addAction("Open File")
        open_action.triggered.connect(self.check_selected_checkboxes)
        # Open the file
        close_action = self.table_menu.addAction("Close File")
        close_action.triggered.connect(self.uncheck_selected_checkboxes)
        # Highlight a table row
        highlight_action = self.table_menu.addAction("Highlight")
        highlight_action.triggered.connect(self.highlight_table)
        # Export hdf content to csv
        highlight_action = self.table_menu.addAction("Export as csv")
        highlight_action.triggered.connect(self.export_2_csv)

        self.table_menu.exec_(QtGui.QCursor.pos())

    def connections(self):
        """Do the connections"""
        self.plot.sigPlotSignal.connect(self.plot_signal_handler)
        # self.plot.sigActiveCurveChanged.connect(self.update_stat)
        self.tableWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tableWidget.customContextMenuRequested[QtCore.QPoint].connect(
            self.table_menu
        )

    def build_splitable_layout(self):
        """Build split bars"""
        splitter_frames = QSplitter(QtCore.Qt.Horizontal)
        splitter_frames.addWidget(self.frame_left)
        splitter_frames.addWidget(self.frame_right)
        splitter_frames.setCollapsible(0, False)
        splitter_frames.setCollapsible(1, False)
        splitter_frames.setStretchFactor(0, 1)
        splitter_frames.setStretchFactor(1, 1)
        splitter_frames.setSizes([250, 400])
        self.horizontalLayout.addWidget(splitter_frames)

        splitter_tables = QSplitter(QtCore.Qt.Vertical)
        splitter_tables.addWidget(self.tableWidget)
        splitter_tables.addWidget(self.tableWidget_plot)
        # splitter_tables.addWidget(self.legend_widget)
        splitter_tables.setCollapsible(0, False)
        splitter_tables.setCollapsible(1, False)
        # splitter_tables.setCollapsible(2,False)
        splitter_tables.setStretchFactor(0, 1)
        splitter_tables.setStretchFactor(1, 1)
        # splitter_tables.setStretchFactor(2, 1)
        # splitter_frames.setSizes([450, 200])
        self.verticalLayout_left.addWidget(splitter_tables)

        splitter_plot_stat = QSplitter(QtCore.Qt.Vertical)
        splitter_plot_stat.addWidget(self.plot)
        splitter_plot_stat.addWidget(self.tableWidget_stats)
        splitter_plot_stat.setCollapsible(0, False)
        splitter_plot_stat.setCollapsible(1, False)
        splitter_plot_stat.setStretchFactor(0, 1)
        splitter_plot_stat.setStretchFactor(1, 1)
        splitter_plot_stat.setSizes([900, 100])
        self.verticalLayout.addWidget(splitter_plot_stat)

    def build_plot(self):
        self.get_hdf5_data()
        self.assert_data()
        self.build_plot_table()
        self.set_standard_plot(
            self.store_current_counters,
            self.store_current_motors,
            self.store_current_monitors,
        )
        self.uncheck_other_motors()
        self.uncheck_other_monitors()
        self.loop()

    def __plot_tools(self):
        # self.plot._buildLegendWidget() #Fix me im collapsed
        self.plot.toggleCrosshairCursor()
        # self.plot.legendWidget.setStyleSheet("color: rgb(0, 0, 0);")

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
                instrument = sf["Scan/scan_000/instrument"]
                for i in instrument:
                    # If the data is called 'data' them its a motor, otherwise its a counter
                    if "data" in instrument[i]:
                        if "data" in instrument[i]:
                            attrs = [j for j in instrument[i].attrs]
                            if "shape" in attrs:
                                if len(instrument[i].attrs["shape"].split(",")) >= 2:
                                    continue
                        try:
                            self.motors_data[i + "__data__" + tail] = instrument[i][
                                "data"
                            ][:]
                        except KeyError:
                            pass
                    else:
                        self.counters_data[i + "__data__" + tail] = instrument[i][i][:]
                try:
                    self.standard_motor = instrument.attrs["main_motor"]
                    self.standard_counter = instrument.attrs["main_counter"]
                except KeyError:
                    self.standard_motor = None
                    self.standard_counter = None

    def get_hdf5_data_2_export(self, file):
        """Read Scan data and store into dicts, also creates a dict with simplified data names"""
        export_counters_data = {}
        export_motors_data = {}

        fo = open(file)
        fo.close()
        with silx.io.open(file) as sf:
            head, tail = os.path.split(file)
            instrument = sf["Scan/scan_000/instrument"]
            for i in instrument:
                # If the data is called 'data' them its a motor, otherwise its a counter
                if "data" in instrument[i]:
                    if "data" in instrument[i]:
                        attrs = [j for j in instrument[i].attrs]
                        if "shape" in attrs:
                            if len(instrument[i].attrs["shape"].split(",")) >= 2:
                                continue
                    try:
                        export_motors_data[i] = instrument[i]["data"][:]
                    except KeyError:
                        pass
                else:
                    export_counters_data[i] = instrument[i][i][:]

        return export_motors_data, export_counters_data

    def modification_date(self, filename):
        t = os.path.getmtime(filename)
        mt = str(datetime.datetime.fromtimestamp(t))[:-7]
        return mt

    def highlight_table(self, items=None):
        rm_signal = False
        flag_signal = False
        if not items:
            items = self.tableWidget.selectedItems()
            slice_ = self.tableWidget.columnCount() - 1
            items = items[::slice_]
            flag_signal = True
        for item in items:
            for j in range(self.tableWidget.columnCount() - 1):
                if j == 0:
                    file = self.tableWidget.item(item.row(), j).text()
                    if flag_signal:
                        if file in self.store_highlighted:
                            self.store_highlighted.remove(file)
                            rm_signal = True
                            break
                        else:
                            self.store_highlighted.append(file)
                if file in self.store_highlighted:
                    self.tableWidget.item(item.row(), j).setBackground(
                        QtGui.QColor(0, 125, 0)
                    )
            if file in self.store_highlighted:
                self.table_checkboxes[file].setStyleSheet(
                    "background-color : rgb(0,125,0);"
                )
        if rm_signal:
            self.clear_table_files()

    def export_2_csv(self):

        items = self.tableWidget.selectedItems()
        slice_ = self.tableWidget.columnCount() - 1
        items = items[::slice_]
        for item in items:
            len_data = []
            frame = {}
            file_path = self.path + "/" + item.text()
            motor_data, counter_data = self.get_hdf5_data_2_export(file_path)
            csv_file_name = item.text().split(".hdf")[0] + ".csv"
            csv_full_path = self.path + "/" + csv_file_name
            for k in list(motor_data.values()):
                len_data.append(len(k))
            for z in list(counter_data.values()):
                len_data.append(len(z))
            len_data = np.array(len_data)
            for i in list(motor_data.keys()):
                frame[i] = motor_data[i][: len_data.min()]
            for j in list(counter_data.keys()):
                frame[j] = counter_data[j][: len_data.min()]
            pd.DataFrame(frame).to_csv(csv_full_path, mode="w", header=True)

    def table_files(self):
        row = 0
        self.table_checkboxes = {}
        self.dir_files = [f for f in listdir(self.path) if isfile(join(self.path, f))]
        self.dir_files = [i for i in self.dir_files if i.endswith(".hdf5")]
        self.dir_files.sort()
        for file in self.dir_files:
            date = self.modification_date(os.path.join(self.path, file))
            try:
                with silx.io.open(os.path.join(self.path, file)) as sf:
                    instrument = sf["Scan/scan_000/instrument"]
                    motors = ""
                    len_points = 0
                    for i in instrument:
                        # If the data is called 'data' them its a motor, otherwise its a counter
                        if "data" in instrument[i]:
                            attrs = [j for j in instrument[i].attrs]
                            if "shape" in attrs:
                                if len(instrument[i].attrs["shape"].split(",")) >= 2:
                                    continue
                            motors += i + ", "
                            len_points = str(len(instrument[i]["data"]))
                    motors = motors[:-2]
            except KeyError:
                continue
            self.tableWidget.insertRow(row)
            self.tableWidget.setItem(row, 0, QTableWidgetItem(file))
            self.tableWidget.setItem(row, 1, QTableWidgetItem(motors))
            self.tableWidget.setItem(row, 2, QTableWidgetItem(len_points))
            self.tableWidget.setItem(row, 3, QTableWidgetItem(date))
            self.table_checkboxes[file] = QCheckBox()
            self.table_checkboxes[file].setCheckState(QtCore.Qt.Unchecked)
            self.tableWidget.setCellWidget(row, 4, self.table_checkboxes[file])
            full_file_path = self.path + "/" + file
            if full_file_path in self.files:
                self.table_checkboxes[file].setChecked(True)
            self.table_checkboxes[file].stateChanged.connect(self.on_state_changed)
            # Keep the hightlighted ones
            if file in self.store_highlighted:
                self.highlight_table(items=[self.tableWidget.item(row, 0)])
            row += 1

        header = self.tableWidget.horizontalHeader()
        # # header.setResizeMode(0, QtGui.QHeaderView.Stretch)
        header.setResizeMode(0, QHeaderView.Stretch)
        header.setResizeMode(1, QHeaderView.Stretch)
        header.setResizeMode(2, QHeaderView.Stretch)
        header.setResizeMode(3, QHeaderView.Stretch)
        header.setResizeMode(4, QHeaderView.ResizeToContents)

    def check_selected_checkboxes(self):
        selected_rows = [i.row() for i in self.tableWidget.selectedItems()]
        for row in set(selected_rows):
            file_now = self.tableWidget.item(row, 0).text()
            self.table_checkboxes[file_now].setChecked(True)

    def uncheck_selected_checkboxes(self):
        selected_rows = [i.row() for i in self.tableWidget.selectedItems()]
        for row in set(selected_rows):
            file_now = self.tableWidget.item(row, 0).text()
            self.table_checkboxes[file_now].setChecked(False)

    def on_state_changed(self):
        ch = self.sender()
        ix = self.tableWidget.indexAt(ch.pos())
        file_now = self.tableWidget.item(ix.row(), 0).text()
        full_file_path = self.path + "/" + file_now
        if ch.isChecked():
            self.files.append(full_file_path)
        else:
            self.files.remove(full_file_path)
        self.clear_all()
        self.build_plot()

    def assert_data(self):
        """Check if the files have difference between motor and counters, and also provides simplified data labels for the plot"""
        motor_prefix = [i.split("__data__")[0] for i in self.motors_data.keys()]
        counter_prefix = [i.split("__data__")[0] for i in self.counters_data.keys()]
        # Get only the instrument name without the file associated to it, and also remove all duplicated
        # ones by transforming the list into a set before iterates over it
        self.simplified_motor_data = set(motor_prefix)  # Simplified data label
        self.simplified_counter_data = set(counter_prefix)  # Simplified data label

        # motor_count = Counter(motor_prefix)
        # counters_count = Counter(counter_prefix)
        # flag_diff = (
        #     False  # Flag to tell if a motor or counter is different between files
        # )
        # for key in motor_count.keys():
        #     if motor_count[key] != len(self.files):
        #         flag_diff = True

    def plot_signal_handler(self, dict_):
        if dict_["event"] == "curveClicked":
            if self.plot.getActiveCurve() is not None:
                self.update_stat()
        if str(self.app.style().metaObject().className()) == "QFusionStyle":
            self.plot._xPos.setStyleSheet("color: rgb(0, 0, 0);")
            self.plot._yPos.setStyleSheet("color: rgb(0, 0, 0);")
        elif str(self.app.style().metaObject().className()) == "QStyleSheetStyle":
            self.plot._xPos.setStyleSheet("color: rgb(255, 255, 255);")
            self.plot._yPos.setStyleSheet("color: rgb(255, 255, 255);")

    def build_plot_table(self):
        row_size = max(
            [len(self.simplified_counter_data), len(self.simplified_motor_data)]
        )
        self.tableWidget_plot.setRowCount(row_size)
        self.counter_checkboxes()
        self.motor_checkboxes()
        self.monitor_checkboxes()
        header = self.tableWidget_plot.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)

    def counter_checkboxes(self):
        """Create counter checkboxes in the tab interface"""
        self.dict_counters = {}
        row = 0
        for i in sorted(self.simplified_counter_data):
            self.dict_counters[i] = QtWidgets.QCheckBox(parent=self.tableWidget_plot)
            self.dict_counters[i].clicked.connect(self.set_plot)
            self.tableWidget_plot.setCellWidget(row, 1, self.dict_counters[i])
            self.dict_counters[i].setText(i)
            row += 1

    def motor_checkboxes(self):
        """Create motor checkboxes in the tab interface"""
        self.dict_motors = {}
        row = 0
        for i in sorted(self.simplified_motor_data):
            self.dict_motors[i] = QtWidgets.QCheckBox(parent=self.tableWidget_plot)
            self.dict_motors[i].clicked.connect(self.uncheck_other_motors)
            self.tableWidget_plot.setCellWidget(row, 0, self.dict_motors[i])
            self.dict_motors[i].setText(i)
            row += 1

    def monitor_checkboxes(self):
        """Create counter checkboxes in the tab interface"""
        self.dict_monitors = {}
        row = 0
        for i in sorted(self.simplified_counter_data):
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
                    assert isinstance(
                        self.counters_data[i + "__data__" + tail],
                        (list, tuple, np.ndarray),
                    )
                    if self.monitor_checked_now:
                        assert isinstance(
                            self.counters_data[
                                self.monitor_checked_now + "__data__" + tail
                            ],
                            (list, tuple, np.ndarray),
                        )
                    if self.checked_now:
                        assert isinstance(
                            self.motors_data[self.checked_now + "__data__" + tail],
                            (list, tuple, np.ndarray),
                        )
                except KeyError:
                    pass
                    # print(e)
                else:
                    if self.monitor_checked_now:
                        data = (
                            self.counters_data[i + "__data__" + tail]
                            / self.counters_data[
                                self.monitor_checked_now + "__data__" + tail
                            ]
                        )
                    else:
                        data = self.counters_data[i + "__data__" + tail]
                    if self.checked_now:
                        # self.plot.getXAxis().setLabel(self.checked_now)
                        if self.dict_counters[i].isChecked():
                            self.plot.addCurve(
                                self.motors_data[self.checked_now + "__data__" + tail][
                                    : len(data)
                                ],
                                data,
                                legend=i + "__data__" + tail,
                            )
                    else:
                        # self.plot.getXAxis().setLabel("Points")
                        points = [i for i in range(len(data))]
                        if self.dict_counters[i].isChecked():
                            self.plot.addCurve(
                                points, data, legend=i + "__data__" + tail
                            )

                    if self.dict_counters[i].isChecked():
                        self.plot.getCurve(i + "__data__" + tail)
                    else:
                        self.plot.removeCurve(i + "__data__" + tail + " Y")
                        if i + "__data__" + tail in self.plot.dataObjectsDict:
                            del self.plot.dataObjectsDict[i + "__data__" + tail]
                        # print(self.plot._curveList)

        self.plot.resetZoom()
        self.plot.updateLegends()

    def new_buttons(self):
        """Method to add new buttons with new funcionalities to the plot"""
        # Create a toolbar and add it to the plot widget
        toolbar = qt.QToolBar()
        self.plot.addToolBar(toolbar)

        # Create clear action and add it to the toolbar
        action = plot_actions.Derivative(self.plot, parent=self.plot)
        toolbar.addAction(action)

    def set_standard_plot(self, counters, motors, monitors):
        """
        Defines the standard plot. If the plot doesn't have any previous
        configuration, it takes the motor and counter passed by the attrs in the instrument path.
        If these attributes don't exist as well, it takes the first counter and motor, finally
        it will take the ones that are current selected from previous files.
        """

        if not counters:
            if self.standard_counter is not None:
                counters.append(self.standard_counter)
            else:
                counters.append(list(self.dict_counters.keys())[0])
        if not motors:
            if self.standard_motor is not None:
                motors.append(self.standard_motor)
            else:
                motors.append(list(self.dict_motors.keys())[0])

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

    def table_stats_layout(self):
        header = self.tableWidget_stats.horizontalHeader()
        header.setResizeMode(0, QHeaderView.Stretch)
        header.setResizeMode(1, QHeaderView.Stretch)
        header.setResizeMode(2, QHeaderView.Stretch)
        header.setResizeMode(3, QHeaderView.Stretch)

    @staticmethod
    def format(x):
        """Format a float with 5 decimals"""
        return str("{:.5f}".format(float(x)))

    def update_stat(self):
        """Update the statistics when a curve is selected"""

        if self.plot.getActiveCurve() is not None:
            activeCurve = self.plot.getActiveCurve()
            x0, y0, legend, info = activeCurve[0:4]
            self.stats = fits.fitGauss(x0, y0)
            self.peak = self.stats[0]
            self.peak_pos = self.stats[1]
            self.min = self.stats[2]
            self.min_pos = self.stats[3]
            self.fwhm = self.stats[4]
            self.fwhm_pos = self.stats[5]
            self.com = self.stats[6]
            # Update table
            self.tableWidget_stats.setItem(
                0, 1, QTableWidgetItem(self.format(self.fwhm))
            )
            self.tableWidget_stats.setItem(
                0, 3, QTableWidgetItem(self.format(self.fwhm_pos))
            )
            self.tableWidget_stats.setItem(
                1, 1, QTableWidgetItem(self.format(self.peak))
            )
            self.tableWidget_stats.setItem(
                1, 3, QTableWidgetItem(self.format(self.peak_pos))
            )
            self.tableWidget_stats.setItem(
                2, 1, QTableWidgetItem(self.format(self.min))
            )
            self.tableWidget_stats.setItem(
                2, 3, QTableWidgetItem(self.format(self.min_pos))
            )
            self.tableWidget_stats.setItem(
                3, 1, QTableWidgetItem(self.format(self.com))
            )
        else:
            self.tableWidget_stats.setItem(0, 1, QTableWidgetItem(""))
            self.tableWidget_stats.setItem(0, 3, QTableWidgetItem(""))
            self.tableWidget_stats.setItem(1, 1, QTableWidgetItem(""))
            self.tableWidget_stats.setItem(1, 3, QTableWidgetItem(""))
            self.tableWidget_stats.setItem(2, 1, QTableWidgetItem(""))
            self.tableWidget_stats.setItem(2, 3, QTableWidgetItem(""))
            self.tableWidget_stats.setItem(3, 1, QTableWidgetItem(""))

    def clear_table_files(self):
        self.tableWidget.clearContents()
        self.tableWidget.setRowCount(0)
        self.table_checkboxes = {}
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
