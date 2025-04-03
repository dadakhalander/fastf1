import os
import sys
import shutil
import threading
import pandas as pd
from random import randint
from PyQt5 import QtGui
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (QComboBox, QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QProgressBar, QMessageBox)

# Ensure necessary directories exist
CWD = os.getcwd()
CACHE_DIR = os.path.join(CWD, 'cache')
PLOT_DIR = os.path.join(CWD, 'plot')
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(PLOT_DIR, exist_ok=True)

# Load race data
events = pd.read_csv(os.path.join(CWD, 'formula/data/events.csv'))
drivers = pd.read_csv(os.path.join(CWD, 'formula/data/drivers.csv'))
race_laps = pd.read_csv(os.path.join(CWD, 'formula/data/laps.csv'))
placeholder_path = os.path.join(CWD, 'formula/img/placeholder.png')

# Dropdown options
year = ['Select Year'] + events.columns[1:].tolist()
location = ['Select Location']
session = ['Race', 'Qualifying', 'FP1', 'FP2', 'FP3']
driver_name = ['Select Driver']
analysis_type = ['Lap Time', 'Fastest Lap', 'Fastest Sectors', 'Full Telemetry']

# Progress Bar StyleSheet
StyleSheet = '''
#RedProgressBar { min-height: 12px; max-height: 12px; border-radius: 2px; border: .5px solid #808080; }
#RedProgressBar::chunk { border-radius: 2px; background-color: #DC0000; opacity: 1; }
.warning-text { color:#DC0000 }
'''

class ProgressBar(QProgressBar):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setValue(0)
        self.timer = QTimer(self, timeout=self.onTimeout)
        self.timer.start(randint(1, 3) * 1000)
    
    def onTimeout(self):
        if self.value() >= 100:
            self.timer.stop()
        else:
            self.setValue(self.value() + 1)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.UIComponents()

    def initUI(self):
        self.setFixedSize(880, 525)
        self.move(200, 100)
        self.setWindowTitle('Formula 1 Telemetry Analytics')
        self.setWindowIcon(QtGui.QIcon(os.path.join(CWD, 'formula/img/f1.png')))

    def UIComponents(self):
        layout = QVBoxLayout()
        controls_layout = QVBoxLayout()
        img_layout = QHBoxLayout()
        img_layout.addLayout(controls_layout)

        self.drop_year, self.drop_grand_prix = QComboBox(), QComboBox()
        self.drop_session, self.drop_driver1 = QComboBox(), QComboBox()
        self.drop_driver2, self.drop_analysis = QComboBox(), QComboBox()
        self.lap_number = QComboBox()
        
        self.run_button = QPushButton('Run Analysis')
        self.save_button = QPushButton('Save Plot to Desktop')
        self.pbar = ProgressBar(self, minimum=0, maximum=0, textVisible=False, objectName="RedProgressBar")
        self.img_plot = QLabel()
        self.img_plot.setPixmap(QPixmap(placeholder_path).scaledToWidth(625))

        # Populate dropdowns
        self.drop_year.addItems(year)
        self.drop_grand_prix.addItems(location)
        self.drop_session.addItems(session)
        self.drop_driver1.addItems(driver_name)
        self.drop_driver2.addItems(driver_name)
        self.drop_analysis.addItems(analysis_type)
        
        labels = ['Year', 'Grand Prix Location', 'Session', 'Driver 1', 'Driver 2', 'Analysis Type']
        dropdowns = [self.drop_year, self.drop_grand_prix, self.drop_session,
                     self.drop_driver1, self.drop_driver2, self.drop_analysis]
        
        for label, dropdown in zip(labels, dropdowns):
            controls_layout.addWidget(QLabel(f'<span style="font-size:8.5pt; font-weight: 500"> {label}: </span>'))
            controls_layout.addWidget(dropdown)
        
        controls_layout.addWidget(self.lap_number)
        self.lap_number.hide()
        controls_layout.addWidget(self.pbar)
        self.pbar.hide()
        controls_layout.addWidget(self.run_button)
        controls_layout.addWidget(self.save_button)
        self.save_button.hide()
        controls_layout.addStretch()
        img_layout.addWidget(self.img_plot)
        
        self.setLayout(img_layout)
        
        # Event Listeners
        self.drop_year.currentTextChanged.connect(self.update_lists)
        self.run_button.clicked.connect(self.thread_script)
        self.save_button.clicked.connect(self.save_plot)
        self.drop_analysis.currentTextChanged.connect(self.add_laps)
        self.drop_grand_prix.currentTextChanged.connect(self.update_laps)

    def current_text(self):
        return [self.drop_year.currentText(), self.drop_grand_prix.currentText(),
                self.drop_session.currentText(), self.drop_driver1.currentText(),
                self.drop_driver2.currentText(), self.drop_analysis.currentText(),
                self.lap_number.currentText()]

    def display_plot(self, plot_path):
        self.img_plot.setPixmap(QPixmap(plot_path).scaledToWidth(625))

    def save_plot(self):
        desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
        shutil.copy(self.plot_path, desktop_path)

    def add_laps(self):
        self.lap_number.setVisible(self.drop_analysis.currentText() == 'Fastest Sectors')

    def update_laps(self):
        if self.drop_grand_prix.currentText():
            self.lap_number.clear()
            self.lap_number.addItems(['Select Lap'] + list(map(str, range(1, race_laps.loc[race_laps.event == self.drop_grand_prix.currentText(), 'laps'].values[0] + 1))))

    def thread_script(self):
        threading.Thread(target=self.button_listen).start()

    def button_listen(self):
        input_data = self.current_text()
        if input_data[0] == 'Select Year':
            self.run_button.setText('Run Analysis (Select Valid Year)')
        else:
            self.run_button.setText('Running . . .')
            self.save_button.hide()
            self.pbar.show()
            script.get_race_data(input_data)
            self.plot_path = os.path.join(CWD, f'formula/plot/{input_data[5]}.png')
            self.display_plot(self.plot_path)
            self.pbar.hide()
            self.run_button.setText('Run New Analysis')
            self.save_button.show()

    def update_lists(self):
        sel_year = self.drop_year.currentText()
        if sel_year != 'Select Year':
            self.drop_grand_prix.clear()
            self.drop_driver1.clear()
            self.drop_driver2.clear()
            self.drop_grand_prix.addItems(events[str(sel_year)].dropna().tolist())
            self.drop_driver1.addItems(drivers[str(sel_year)].dropna().tolist())
            self.drop_driver2.addItems(drivers[str(sel_year)].dropna().tolist())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(StyleSheet)
    mw = MainWindow()
    mw.show()
    sys.exit(app.exec_())
