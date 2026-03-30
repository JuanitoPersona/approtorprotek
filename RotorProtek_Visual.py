import sys
import math
import csv
import warnings
import numpy as np
import pandas as pd
import os
import json
from datetime import datetime

from matplotlib.ticker import MaxNLocator, MultipleLocator
from matplotlib.ticker import FuncFormatter
from matplotlib import dates as mdates
from PyQt5.QtWidgets import (
    QSpinBox, QCheckBox, QApplication, QMainWindow, QWidget, QFileDialog, QDoubleSpinBox,
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QStackedWidget, QSizePolicy,
    QComboBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QTabWidget, QListWidget, QListWidgetItem, QMenu, QDialog, QSplitter, QFrame,
    QToolButton, QAction, QActionGroup,
    QMessageBox, QDateEdit, QDialogButtonBox, QFormLayout, QColorDialog
)
from PyQt5.QtCore import Qt, QStandardPaths, QObject, QThread, pyqtSignal, QDate, QTimer, QSize
from PyQt5.QtGui import QPixmap, QFont, QIcon, QColor
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavToolbar
)
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle

from app.csv_loader import (
    parse_csv_records_to_legacy,
    parse_multi_start_csv as core_parse_multi_start_csv,
    parse_numeric as core_parse_numeric,
    parse_scalars_from_multi_row as core_parse_scalars_from_multi_row,
    parse_single_start_csv as core_parse_single_start_csv,
    read_csv_rows as core_read_csv_rows,
    to_float_or_nan as core_to_float_or_nan,
    try_parse_datetime_text as core_try_parse_datetime_text,
)
from app.historical import (
    compute_history_metrics as core_compute_history_metrics,
    estimated_nominal_current as core_estimated_nominal_current,
    linearity_pairs as core_linearity_pairs,
    successful_current_analysis_pairs as core_successful_current_analysis_pairs,
    successful_speed_resistance_ratio_pairs as core_successful_speed_resistance_ratio_pairs,
)
from app.metrics import (
    estimate_mill_load_pct as core_estimate_mill_load_pct,
    is_externally_aborted_start as core_is_externally_aborted_start,
    is_successful_start as core_is_successful_start,
    scalar_value as core_scalar_value,
)
from app.startup_detection import (
    decode_datetime as core_decode_datetime,
    detect_csv_type as core_detect_csv_type,
    extract_multi_start_rows as core_extract_multi_start_rows,
    format_datetime as core_format_datetime,
    is_valid_datetime as core_is_valid_datetime,
    normalize_header as core_normalize_header,
)

LIGHT_STYLE = """
QMainWindow { background-color: #F2F2F2; }
QPushButton { background-color: #EC6E00; color: white; padding: 8px 16px; border-radius: 8px; font-size: 15px; font-weight: 600; }
QPushButton:hover { background-color: #c75d00; }
QToolButton { background-color: #3A4F66; color: white; padding: 8px 14px; border-radius: 8px; font-size: 15px; font-weight: 600; }
QToolButton:hover { background-color: #2F4359; }
QComboBox { padding: 4px; border: 1px solid #ccc; border-radius: 4px; }
QTableWidget { gridline-color: #ddd; }
QTableWidget::item { padding: 6px; }
QTabWidget::pane { border: 1px solid #D8D8D8; top: -1px; background: white; }
QTabBar::tab {
    background: #E6E6E6;
    color: #303030;
    padding: 10px 22px;
    min-width: 180px;
    font-size: 13px;
    font-weight: 600;
}
QTabBar::tab:selected { background: #EC6E00; color: white; }
"""
STYLE = LIGHT_STYLE

UI_TEXTS = {
    'es': {
        'window_title': 'Arranque Visualizer',
        'status_no_csv': 'Sin CSV cargado',
        'viewer_title': 'Visualización de Arranque',
        'load_csv': 'Cargar CSV',
        'filters': 'Filtros',
        'export_csv': 'Exportar CSV',
        'export_png': 'Exportar PNG',
        'config': 'Configuración',
        'language_menu': 'Idioma',
        'language_es': 'Español',
        'language_en': 'Inglés',
        'select_start': 'Seleccionar arranque:',
        'show_harmonics': 'Mostrar armónicos',
        'hide_harmonics': 'Ocultar armónicos',
        'prev': '<< Anterior',
        'next': 'Siguiente >>',
        'show_frequency_hz': 'Mostrar frecuencia en Hz',
        'viewer_tab': 'Visualización de Arranque',
        'cm_tab': 'Condition Monitoring',
        'history_tab': 'Histórico',
        'history_nominal_speed': 'Velocidad nominal [r.p.m.]',
        'history_nominal_current': 'Corriente nominal estimada [A]: --',
        'history_nominal_current_value': 'Corriente nominal estimada [A]: {value:.2f}',
        'analysis_linearity': 'Análisis de linealidad',
        'hide_analysis_linearity': 'Ocultar análisis de linealidad',
        'analysis_current': 'Análisis de corrientes',
        'hide_analysis_current': 'Ocultar análisis de corrientes',
        'history_load_title': 'Evolución histórica del % de carga',
        'cm_subtitle': 'Comparativa avanzada entre arranques con filtros, doble gráfica y navegación asistida.',
        'cm_config_title': 'Configura las gráficas comparativas:',
        'cm_div_left': 'Divisiones Y izq:',
        'cm_div_right': 'Divisiones Y der:',
        'cm_gridx': 'Rejilla vertical X',
        'cm_second_graph': 'Segunda gráfica',
        'cm_restore': 'Restaurar gráficas',
        'cm_filter_success': 'Filtrar arranques',
        'cm_show_all_starts': 'Mostrar todos',
        'cm_params1': 'Parámetros Gráfica 1',
        'cm_params2': 'Parámetros Gráfica 2',
        'cm_starts': 'Arranques (marca para incluir):',
        'cm_all': 'Seleccionar todos',
        'cm_none': 'Limpiar selección',
        'cm_invert': 'Invertir selección',
        'cm_cursor1_default': 'Cursor G1: mueve el ratón sobre la gráfica para inspeccionar el arranque.',
        'cm_cursor2_default': 'Cursor G2: mueve el ratón sobre la gráfica para inspeccionar el arranque.',
        'cm_cursor1_prefix': 'Cursor G1: {text}',
        'cm_cursor2_prefix': 'Cursor G2: {text}',
        'cm_settings': 'Ajustes CM',
        'cm_toggle_dates': 'Mostrar fechas completas',
        'cm_click_date': 'Mostrar fecha con un click',
        'cm_double_delete': 'Borrar con doble click',
        'cm_area_selection': 'Selección por área',
        'cm_show_selector': 'Mostrar selector de arranques',
        'cm_show_params': 'Mostrar selector de parámetros',
        'cm_starts_from': 'Desde',
        'cm_starts_to': 'Hasta',
        'cm_apply_range': 'Aplicar rango',
        'cm_clear_range': 'Limpiar rango',
        'cm_close_panel': '×',
        'cm_selected_date': 'Fecha seleccionada: {date}',
        'loading_csv': 'Cargando {name}...',
        'load_error': 'Error al cargar CSV',
        'status_loaded': '{name} | {count} arranques visibles | modo: {mode}',
        'status_visible': '{name} | {count} arranques visibles',
        'dataset': 'Dataset',
        'csv_exported': 'CSV exportado: {name}',
        'png_exported': 'PNG exportado: {name}',
    },
    'en': {
        'window_title': 'Start Visualizer',
        'status_no_csv': 'No CSV loaded',
        'viewer_title': 'Startup Visualization',
        'load_csv': 'Load CSV',
        'filters': 'Filters',
        'export_csv': 'Export CSV',
        'export_png': 'Export PNG',
        'config': 'Settings',
        'language_menu': 'Language',
        'language_es': 'Spanish',
        'language_en': 'English',
        'select_start': 'Select startup:',
        'show_harmonics': 'Show harmonics',
        'hide_harmonics': 'Hide harmonics',
        'prev': '<< Previous',
        'next': 'Next >>',
        'show_frequency_hz': 'Show frequency in Hz',
        'viewer_tab': 'Startup Visualization',
        'cm_tab': 'Condition Monitoring',
        'history_tab': 'History',
        'history_nominal_speed': 'Nominal speed [r.p.m.]',
        'history_nominal_current': 'Estimated nominal current [A]: --',
        'history_nominal_current_value': 'Estimated nominal current [A]: {value:.2f}',
        'analysis_linearity': 'Linearity analysis',
        'hide_analysis_linearity': 'Hide linearity analysis',
        'analysis_current': 'Current analysis',
        'hide_analysis_current': 'Hide current analysis',
        'history_load_title': 'Historical load evolution [%]',
        'cm_subtitle': 'Advanced startup comparison with filters, dual chart and assisted navigation.',
        'cm_config_title': 'Configure the comparison charts:',
        'cm_div_left': 'Left Y divisions:',
        'cm_div_right': 'Right Y divisions:',
        'cm_gridx': 'Vertical X grid',
        'cm_second_graph': 'Second chart',
        'cm_restore': 'Restore charts',
        'cm_filter_success': 'Filter startups',
        'cm_show_all_starts': 'Show all',
        'cm_params1': 'Chart 1 parameters',
        'cm_params2': 'Chart 2 parameters',
        'cm_starts': 'Startups (check to include):',
        'cm_all': 'Select all',
        'cm_none': 'Clear selection',
        'cm_invert': 'Invert selection',
        'cm_cursor1_default': 'Cursor G1: move the mouse over the chart to inspect the startup.',
        'cm_cursor2_default': 'Cursor G2: move the mouse over the chart to inspect the startup.',
        'cm_cursor1_prefix': 'Cursor G1: {text}',
        'cm_cursor2_prefix': 'Cursor G2: {text}',
        'cm_settings': 'CM Settings',
        'cm_toggle_dates': 'Show full dates',
        'cm_click_date': 'Show date with single click',
        'cm_double_delete': 'Delete with double click',
        'cm_area_selection': 'Area selection',
        'cm_show_selector': 'Show startup selector',
        'cm_show_params': 'Show parameter selector',
        'cm_starts_from': 'From',
        'cm_starts_to': 'To',
        'cm_apply_range': 'Apply range',
        'cm_clear_range': 'Clear range',
        'cm_close_panel': '×',
        'cm_selected_date': 'Selected date: {date}',
        'loading_csv': 'Loading {name}...',
        'load_error': 'Error loading CSV',
        'status_loaded': '{name} | {count} visible startups | mode: {mode}',
        'status_visible': '{name} | {count} visible startups',
        'dataset': 'Dataset',
        'csv_exported': 'CSV exported: {name}',
        'png_exported': 'PNG exported: {name}',
    }
}

START_TYPES = {
    1: "Successful start",
    2: "Successful start with alarm",
    3: "RotorProtek tripped start",
    4: "Externally aborted start",
    5: "Start longer than two minutes"
}
PROTECTIONS = {
    0: "Not protected",
    1: "Factory acceptance tests",
    2: "Cold commissioning start",
    3: "Hot commissioning start",
    4: "Start previous to maintenance",
    5: "Start after maintenance"
}
SCALAR_FIELDS = [
    'Duración (s)','I máx (Arms)','Tiempo I máx (s)','I inicial','I final',
    'Vel ini','Vel fin','Sampling rate (ms)','% desequ. fases','% d motores',
    'Temp ini (K)','Temp fin (K)','Par máx (%)','Par mín (%)',
    'Par cort (%)','Tiempo cort(s)','R ini (Ω)','R fin (Ω)',
    'Ratio R','E dis(MJ)','Amp frz(%)','Inercia','I cortoc (A)','Ángulo (°)'
]

SINGLE_START_REQUIRED_HEADERS = {
    'speedvstime(%syncspd)',
    'rotcurrentvstime(%in)',
    'mottorquevst(%flt)',
    'starttime(s)',
    'protection',
    'typeofstart',
    'time'
}
SINGLE_START_COLUMN_MAP = {
    'speedvstime(%syncspd)': 'speed',
    'rotcurrentvstime(%in)': 'current',
    'mottorquevst(%flt)': 'torque',
    'secondmotcurrvst(%in)': 'dual_current',
    'starttime(s)': 'time',
    'loadtvsmillang(%flt)': 'load_torque',
    'motortvsmillang(%flt)': 'motor_torque',
    'frequency(hz)': 'harmonic_freq',
    'harmonicamp(arms)': 'harmonic_amp_arms',
    'harmonicamp(%irms)': 'harmonic_amp_irms',
    'harmonicamp(%in)': 'harmonic_amp_pct_nominal',
}
SINGLE_START_SCALAR_MAP = {
    'totalstrtngtime(s)': ('Duración (s)', 1.0, 0.0),
    'maxcurrent(arms)': ('I máx (Arms)', 1.0, 0.0),
    'tofmaxcurrent(s)': ('Tiempo I máx (s)', 1.0, 0.0),
    'initcurrent(arms)': ('I inicial', 1.0, 0.0),
    'finalcurrent(arms)': ('I final', 1.0, 0.0),
    'shortingspeed(rpm)': ('Vel ini', 1.0, 0.0),
    'finalspeed(rpm)': ('Vel fin', 1.0, 0.0),
    'samplerate(ms)': ('Sampling rate (ms)', 1.0, 0.0),
    'phasecurrunbalance(%in)': ('% desequ. fases', 1.0, 0.0),
    'motorscurrunbalance(%in)': ('% d motores', 1.0, 0.0),
    'initelecttemp(degc)': ('Temp ini (K)', 1.0, 273.15),
    'finalelecttemp(degc)': ('Temp fin (K)', 1.0, 273.15),
    'maxtorque(%flt)': ('Par máx (%)', 1.0, 0.0),
    'mintorque(%flt)': ('Par mín (%)', 1.0, 0.0),
    'torqueatshort(%flt)': ('Par cort (%)', 1.0, 0.0),
    'timeofshort(s)': ('Tiempo cort(s)', 1.0, 0.0),
    'initres(ohm)': ('R ini (Ω)', 1.0, 0.0),
    'finalres(ohm)': ('R fin (Ω)', 1.0, 0.0),
    'resratio': ('Ratio R', 1.0, 0.0),
    'energy(mj)': ('E dis(MJ)', 1.0, 0.0),
    'frzchrgamp(%flt)': ('Amp frz(%)', 1.0, 0.0),
    'inertia(kgm2)': ('Inercia', 1.0, 0.0),
    'maxshortcurr(a)': ('I cortoc (A)', 1.0, 0.0),
    'tumblingangle(deg)': ('Ángulo (°)', 1.0, 0.0),
}

def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, relative_path)

def parse_numeric(val, factor=1.0, default=0.0):
    return core_parse_numeric(val, factor=factor, default=default)

def decode_datetime(a, b, c):
    return core_decode_datetime(a, b, c)

def format_datetime(dt):
    return core_format_datetime(dt)

def is_valid_datetime(dt):
    return core_is_valid_datetime(dt)

def clear_layout(layout):
    while layout.count():
        item = layout.takeAt(0)
        if w := item.widget():
            w.deleteLater()
        elif sub := item.layout():
            clear_layout(sub)

def normalize_header(value):
    return core_normalize_header(value)

def try_parse_datetime_text(value):
    return core_try_parse_datetime_text(value)

def to_float_or_nan(value):
    return core_to_float_or_nan(value)

class CsvLoadWorker(QObject):
    finished = pyqtSignal(str, str, list, str, str)

    def __init__(self, owner, file_path):
        super().__init__()
        self.owner = owner
        self.file_path = file_path

    def run(self):
        try:
            rows = self.owner._read_csv_rows(self.file_path)
            csv_mode, view_mode, records = self.owner.parse_csv_records(rows)
            if not records:
                self.finished.emit('', '', [], self.file_path, 'No se detectaron arranques válidos en el CSV.')
                return
            self.finished.emit(csv_mode or '', view_mode or '', records, self.file_path, '')
        except Exception as exc:
            self.finished.emit('', '', [], self.file_path, str(exc))

class FilterDialog(QDialog):
    def __init__(self, parent, protections, start_types, current_filter):
        super().__init__(parent)
        self.setWindowTitle('Filtros de arranques')
        self.resize(420, 260)
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.success_combo = QComboBox()
        self.success_combo.addItems(['Todos', 'Solo exitosos', 'Solo fallidos'])
        self.success_combo.setCurrentText(current_filter.get('success_mode', 'Todos'))
        form.addRow('Resultado', self.success_combo)

        self.protection_combo = QComboBox()
        self.protection_combo.addItems(['Todas'] + protections)
        self.protection_combo.setCurrentText(current_filter.get('protection', 'Todas'))
        form.addRow('Protección', self.protection_combo)

        self.type_combo = QComboBox()
        self.type_combo.addItems(['Todos'] + start_types)
        self.type_combo.setCurrentText(current_filter.get('start_type', 'Todos'))
        form.addRow('Tipo arranque', self.type_combo)

        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDisplayFormat('yyyy/MM/dd')
        self.start_date.setSpecialValueText('Sin mínimo')
        self.start_date.setDate(QDate(2000, 1, 1))
        self.start_date.setMinimumDate(QDate(2000, 1, 1))
        self.start_date.setCurrentSection(QDateEdit.YearSection)
        if current_filter.get('date_from'):
            d = current_filter['date_from']
            self.start_date.setDate(QDate(d.year, d.month, d.day))
        form.addRow('Fecha desde', self.start_date)

        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDisplayFormat('yyyy/MM/dd')
        self.end_date.setSpecialValueText('Sin máximo')
        self.end_date.setDate(QDate(2000, 1, 1))
        self.end_date.setMinimumDate(QDate(2000, 1, 1))
        if current_filter.get('date_to'):
            d = current_filter['date_to']
            self.end_date.setDate(QDate(d.year, d.month, d.day))
        form.addRow('Fecha hasta', self.end_date)

        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Reset)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.Reset).clicked.connect(self._reset)
        layout.addWidget(buttons)

    def _reset(self):
        self.success_combo.setCurrentText('Todos')
        self.protection_combo.setCurrentText('Todas')
        self.type_combo.setCurrentText('Todos')
        self.start_date.setDate(QDate(2000, 1, 1))
        self.end_date.setDate(QDate(2000, 1, 1))

    def get_filter(self):
        return {
            'success_mode': self.success_combo.currentText(),
            'protection': self.protection_combo.currentText(),
            'start_type': self.type_combo.currentText(),
            'date_from': None if self.start_date.date() == QDate(2000, 1, 1) else self.start_date.date().toPyDate(),
            'date_to': None if self.end_date.date() == QDate(2000, 1, 1) else self.end_date.date().toPyDate(),
        }

def infer_axis_label(param_names):
    raw = [str(name).lower() for name in param_names]
    normalized = [normalize_header(name) for name in param_names]
    if raw and all('%' in n for n in raw):
        return '%'
    if raw and all(('r ini' in n) or ('r fin' in n) or ('ratio r' in n) or ('res' in n) for n in raw):
        return 'Resistencia'
    if raw and all(('i ' in n) or ('corr' in n) or ('current' in n) or ('cortoc' in n) for n in raw):
        return 'Corriente [A]'
    if raw and all(('vel' in n) or ('speed' in n) or ('rpm' in n) for n in raw):
        return 'Velocidad [r.p.m]'
    if raw and all(('tiempo cort' in n) or ('timeofshort' in n) for n in raw):
        return 'Tiempo [s]'
    if normalized and all(('ang' in n) or ('ngulo' in n) or ('tumblingangle' in n) for n in normalized):
        return 'Ángulo [º]'
    if normalized and all('r' in n for n in normalized):
        return 'Resistencia'
    return 'Eje izquierdo'

def summarize_plot_title(param_names):
    if not param_names:
        return 'Sin variables seleccionadas'
    if len(param_names) == 1:
        return param_names[0]
    if len(param_names) == 2:
        return f"{param_names[0]} y {param_names[1]}"
    shown = ', '.join(param_names[:3])
    extra = len(param_names) - 3
    return f"{shown} (+{extra})"

class DataVisualizer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Arranque Visualizer")
        self.resize(1200, 900)
        self.language = 'es'
        self._cm_redraw_timer = QTimer(self)
        self._cm_redraw_timer.setSingleShot(True)
        self._cm_redraw_timer.timeout.connect(self.cm_redraw)
        self._cm_state_save_timer = QTimer(self)
        self._cm_state_save_timer.setSingleShot(True)
        self._cm_state_save_timer.timeout.connect(self._flush_cm_state_save)
        self._cm_single_click_timer = QTimer(self)
        self._cm_single_click_timer.setSingleShot(True)
        self._cm_single_click_timer.timeout.connect(self._commit_cm_single_click)

        self.starts = []
        self.all_starts = []
        self.start_labels = []
        self.starts_scalars = []
        self.csv_mode = None
        self.current_file = ''
        self.current_view_mode = 'single_startup_view'
        self.current_filter = {
            'success_mode': 'Todos',
            'protection': 'Todas',
            'start_type': 'Todos',
            'date_from': None,
            'date_to': None,
        }
        self.cm_hidden_indices = set()
        self.history_hidden_indices = set()
        self.cm_success_filter_active = False
        self.current = 0
        self.show_hz = True
        self.nominal_speed_rpm = 1000.0
        self._load_thread = None
        self._load_worker = None

        # ---- Estado persistente de CM ----
        self.cm_state = {
            "selected_params": [],
            "selected_params_secondary": [],
            "axis_map": {},
            "label_map": {},
            "transforms": {},            # {param: {'op':'none'|'mul'|'div','k':float}}
            "checked_starts": {},        # {label_fecha: bool}
            "div_left": 6,
            "div_right": 6,
            "gridx": True,
            "show_second_graph": False,
            "show_full_dates": True,
            "show_click_date": True,
            "enable_double_click_delete": True,
            "enable_area_selection": True,
            "show_start_selector": True,
            "show_param_selector": True,
        }
        conf_dir = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
        if not conf_dir:
            conf_dir = os.path.join(os.path.expanduser("~"), ".rotorprotek")
        os.makedirs(conf_dir, exist_ok=True)
        self._cm_settings_path = os.path.join(conf_dir, "cm_settings.json")
        self._ui_settings_path = os.path.join(conf_dir, "ui_settings.json")
        self._cm_load_from_disk()
        self.cm_state["show_param_selector"] = True
        self._load_ui_settings()
        self.setStyleSheet(LIGHT_STYLE)

        self.cm_axis_map = {}
        self.cm_label_map = {}
        self.cm_transform = {}  # {'op','k'}
        self._cm_fullscreen_dialogs = []

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.tabs_container = None
        self.tabs_widget = None
        self.historical_canvas = None
        self.historical_axes = []
        self.history_analysis_mode = 'none'

        self._build_viewer()
        self.stack.setCurrentWidget(self.viewer_scroll)
        self.setWindowIcon(QIcon(resource_path("logo_app.ico")))
        self.setWindowTitle(self.tr_text('window_title'))
        self.statusBar().showMessage(self.tr_text('status_no_csv'))
        self.showMaximized()

        # Controles CM (se construyen en _build_cm_page)
        self.cm_second_graph_toggle = None
        self.cm_restore_btn = None
        self.cm_list = None
        self.cm_param_list = None
        self.cm_param_list_secondary = None
        self.cm_param_label_secondary = None
        self.cm_cursor_info_main = None
        self.cm_cursor_info_secondary = None
        self.cm_div_left = None
        self.cm_div_right = None
        self.cm_gridx = None
        self.cm_canvas = None
        self.cm_ax2 = None
        self.cm_canvas_secondary = None
        self.cm_ax_secondary = None
        self.cm_ax_secondary_right = None
        self.viewer_body_splitter = None
        self.cm_main_splitter = None
        self.cm_right_splitter = None
        self.cm_secondary_panel = None
        self.cm_selector_panel = None
        self.cm_params_panel = None
        self.cm_selected_point_main = None
        self.cm_selected_point_secondary = None
        self.cm_area_selected_main = set()
        self.cm_area_selected_secondary = set()
        self.cm_area_bounds_main = None
        self.cm_area_bounds_secondary = None
        self.cm_drag_state = None
        self.cm_pending_selection = None
        self.cm_skip_release_canvas = None
        self._cm_layout_signature = None
        self.cm_trendline_enabled_main = False
        self.cm_trendline_enabled_secondary = False
        self.cm_line_mode_main = False
        self.cm_line_mode_secondary = False
        self.cm_draw_mode_main = False
        self.cm_draw_mode_secondary = False
        self.cm_line_anchor_main = None
        self.cm_line_anchor_secondary = None
        self.cm_manual_lines_main = []
        self.cm_manual_lines_secondary = []
        self.cm_freehand_paths_main = []
        self.cm_freehand_paths_secondary = []
        self.history_area_delete_enabled = False
        self.history_area_selection_bounds = None
        self.history_area_selection_indices = set()
        self.history_drag_state = None
        self.history_load_color = '#EC6E00'

    # ---------- VIEWER ----------
    def tr_text(self, key, **kwargs):
        text = UI_TEXTS.get(self.language, UI_TEXTS['es']).get(key, key)
        return text.format(**kwargs) if kwargs else text

    def _panel_style(self):
        return "background: white; border: 1px solid #DDDDDD; border-radius: 12px;"

    def _list_style(self):
        return (
            "QListWidget { background: white; border: 1px solid #DCDCDC; border-radius: 10px; padding: 6px; }"
            "QListWidget::item { padding: 7px 8px; border-bottom: 1px solid #F1F1F1; }"
            "QListWidget::item:selected { background: #FCE6D1; color: #2F2F2F; }"
        )

    def _table_style(self):
        return (
            "QTableWidget { background: white; alternate-background-color: #F7F7F7; border: 1px solid #E2E2E2; border-radius: 8px; }"
            "QTableWidget::item { padding: 8px; border-bottom: 1px solid #EFEFEF; }"
        )

    def _table_header_style(self):
        return "QHeaderView::section { background-color: #EC6E00; color: white; font-weight: bold; border: none; padding: 10px; }"

    def _build_config_button(self):
        btn = QToolButton()
        btn.setText(self.tr_text('config'))
        btn.setPopupMode(QToolButton.InstantPopup)
        menu = QMenu(btn)

        language_menu = menu.addMenu(self.tr_text('language_menu'))
        language_group = QActionGroup(language_menu)
        language_group.setExclusive(True)
        act_es = QAction(self.tr_text('language_es'), language_menu, checkable=True)
        act_en = QAction(self.tr_text('language_en'), language_menu, checkable=True)
        act_es.setChecked(self.language == 'es')
        act_en.setChecked(self.language == 'en')
        act_es.triggered.connect(lambda checked: checked and self._set_language('es'))
        act_en.triggered.connect(lambda checked: checked and self._set_language('en'))
        language_group.addAction(act_es)
        language_group.addAction(act_en)
        language_menu.addActions(language_group.actions())

        btn.setMenu(menu)
        self._fit_toolbutton_to_text(btn, extra=30, min_width=96)
        return btn

    def _save_ui_settings(self):
        try:
            with open(self._ui_settings_path, "w", encoding="utf-8") as f:
                json.dump({"language": self.language}, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _load_ui_settings(self):
        try:
            if os.path.exists(self._ui_settings_path):
                with open(self._ui_settings_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.language = data.get("language", "es") if data.get("language") in ("es", "en") else "es"
        except Exception:
            pass

    def _rebuild_interface(self):
        current_index = self.current
        current_view_mode = self.current_view_mode
        if self.tabs_container is not None:
            self.stack.removeWidget(self.tabs_container)
            self.tabs_container.deleteLater()
            self.tabs_container = None
            self.tabs_widget = None
        if getattr(self, 'viewer_scroll', None) is not None:
            self.stack.removeWidget(self.viewer_scroll)
            self.viewer_scroll.deleteLater()
        self._build_viewer()
        if self.starts:
            self.combo.blockSignals(True)
            self.combo.clear()
            self.combo.addItems(self.start_labels)
            self.combo.blockSignals(False)
            self._rebuild_tabs(current_view_mode)
            if len(self.starts) > 1:
                self._cm_fill_list()
                self._cm_autosize_list()
                self._cm_params_autosize()
                self._cm_restore_state()
                self.cm_redraw()
            if self.combo is not None and 0 <= current_index < self.combo.count():
                self.combo.setCurrentIndex(current_index)
            self.display_item()
        else:
            self.stack.setCurrentWidget(self.viewer_scroll)
        self.setWindowTitle(self.tr_text('window_title'))
        self.statusBar().showMessage(self.tr_text('status_no_csv') if not self.starts else self.statusBar().currentMessage())

    def _set_language(self, language):
        if language == self.language:
            return
        self.language = language
        self._save_ui_settings()
        self._rebuild_interface()

    def _schedule_cm_redraw(self, delay_ms=30):
        if self._cm_redraw_timer.isActive():
            self._cm_redraw_timer.stop()
        self._cm_redraw_timer.start(delay_ms)

    def _schedule_cm_state_save(self, delay_ms=180):
        self._cm_save_state(write_to_disk=False)
        if self._cm_state_save_timer.isActive():
            self._cm_state_save_timer.stop()
        self._cm_state_save_timer.start(delay_ms)

    def _flush_cm_state_save(self):
        self._cm_save_state(write_to_disk=True)

    def _build_cm_settings_button(self):
        btn = QToolButton()
        btn.setText(self.tr_text('cm_settings'))
        btn.setPopupMode(QToolButton.InstantPopup)
        menu = QMenu(btn)
        self.cm_settings_dates_action = QAction(self.tr_text('cm_toggle_dates'), menu, checkable=True)
        self.cm_settings_dates_action.setChecked(bool(self.cm_state.get("show_full_dates", True)))
        self.cm_settings_dates_action.triggered.connect(lambda checked: self._cm_toggle_setting("show_full_dates", checked))
        menu.addAction(self.cm_settings_dates_action)
        menu.addSeparator()

        self.cm_settings_click_action = QAction(self.tr_text('cm_click_date'), menu, checkable=True)
        self.cm_settings_click_action.setChecked(bool(self.cm_state.get("show_click_date", True)))
        self.cm_settings_click_action.triggered.connect(lambda checked: self._cm_toggle_setting("show_click_date", checked))
        menu.addAction(self.cm_settings_click_action)

        self.cm_settings_delete_action = QAction(self.tr_text('cm_double_delete'), menu, checkable=True)
        self.cm_settings_delete_action.setChecked(bool(self.cm_state.get("enable_double_click_delete", True)))
        self.cm_settings_delete_action.triggered.connect(lambda checked: self._cm_toggle_setting("enable_double_click_delete", checked))
        menu.addAction(self.cm_settings_delete_action)

        self.cm_settings_area_action = QAction(self.tr_text('cm_area_selection'), menu, checkable=True)
        self.cm_settings_area_action.setChecked(bool(self.cm_state.get("enable_area_selection", True)))
        self.cm_settings_area_action.triggered.connect(lambda checked: self._cm_toggle_setting("enable_area_selection", checked))
        menu.addAction(self.cm_settings_area_action)

        self.cm_settings_selector_action = QAction(self.tr_text('cm_show_selector'), menu, checkable=True)
        self.cm_settings_selector_action.setChecked(bool(self.cm_state.get("show_start_selector", True)))
        self.cm_settings_selector_action.triggered.connect(lambda checked: self._cm_toggle_setting("show_start_selector", checked))
        menu.addAction(self.cm_settings_selector_action)

        self.cm_settings_params_action = QAction(self.tr_text('cm_show_params'), menu, checkable=True)
        self.cm_settings_params_action.setChecked(bool(self.cm_state.get("show_param_selector", True)))
        self.cm_settings_params_action.triggered.connect(lambda checked: self._cm_toggle_setting("show_param_selector", checked))
        menu.addAction(self.cm_settings_params_action)

        btn.setMenu(menu)
        self._fit_toolbutton_to_text(btn, extra=30, min_width=118)
        return btn

    def _cm_toggle_setting(self, key, checked):
        self.cm_state[key] = bool(checked)
        if key == "enable_area_selection" and not checked:
            self.cm_area_selected_main.clear()
            self.cm_area_selected_secondary.clear()
            self.cm_area_bounds_main = None
            self.cm_area_bounds_secondary = None
        self._schedule_cm_state_save()
        self._schedule_cm_redraw()

    def _cm_hide_param_selector(self):
        self.cm_state["show_param_selector"] = False
        if getattr(self, 'cm_settings_params_action', None):
            self.cm_settings_params_action.blockSignals(True)
            self.cm_settings_params_action.setChecked(False)
            self.cm_settings_params_action.blockSignals(False)
        self._schedule_cm_state_save()
        self.cm_redraw()

    def _cm_hide_start_selector(self):
        self.cm_state["show_start_selector"] = False
        if getattr(self, 'cm_settings_selector_action', None):
            self.cm_settings_selector_action.blockSignals(True)
            self.cm_settings_selector_action.setChecked(False)
            self.cm_settings_selector_action.blockSignals(False)
        self._schedule_cm_state_save()
        self.cm_redraw()

    def _cm_apply_date_range_filter(self):
        if not self.cm_list:
            return
        start_qdate = self.cm_range_start.date() if hasattr(self, 'cm_range_start') else QDate(2000, 1, 1)
        end_qdate = self.cm_range_end.date() if hasattr(self, 'cm_range_end') else QDate(2000, 1, 1)
        start_date = None if start_qdate == QDate(2000, 1, 1) else start_qdate.toPyDate()
        end_date = None if end_qdate == QDate(2000, 1, 1) else end_qdate.toPyDate()
        self.cm_list.blockSignals(True)
        for i in range(self.cm_list.count()):
            dt = self.starts[i].get('timestamp_dt')
            keep = True
            if start_date and (dt is None or dt.date() < start_date):
                keep = False
            if end_date and (dt is None or dt.date() > end_date):
                keep = False
            self.cm_list.item(i).setCheckState(Qt.Checked if keep else Qt.Unchecked)
        self.cm_list.blockSignals(False)
        self._schedule_cm_state_save()
        self.cm_redraw()

    def _cm_clear_date_range_filter(self):
        self._cm_sync_date_range_controls(reset_to_full_range=True)
        self._cm_bulk_check(True)

    def _cm_sync_date_range_controls(self, reset_to_full_range=False):
        if not hasattr(self, 'cm_range_start') or not hasattr(self, 'cm_range_end'):
            return
        valid_dates = [
            start.get('timestamp_dt').date()
            for start in getattr(self, 'starts', [])
            if start.get('timestamp_dt') is not None
        ]
        if not valid_dates:
            return
        min_date = min(valid_dates)
        max_date = max(valid_dates)
        qmin = QDate(min_date.year, min_date.month, min_date.day)
        qmax = QDate(max_date.year, max_date.month, max_date.day)
        for editor in (self.cm_range_start, self.cm_range_end):
            editor.blockSignals(True)
            editor.setMinimumDate(qmin)
            editor.setMaximumDate(qmax)
            editor.blockSignals(False)
        if reset_to_full_range:
            self.cm_range_start.setDate(qmin)
            self.cm_range_end.setDate(qmax)

    def _build_viewer(self):
        page = QWidget()
        main_layout = QVBoxLayout(page)
        main_layout.setSpacing(18)
        main_layout.setContentsMargins(20, 18, 20, 20)

        controls_block = QVBoxLayout()
        controls_block.setSpacing(10)

        hdr = QHBoxLayout()
        hdr.setSpacing(10)
        self.btn_load_csv = QPushButton(self.tr_text('load_csv'))
        self._style_compact_action_button(self.btn_load_csv)
        self._fit_button_to_text(self.btn_load_csv, extra=10, min_width=70)
        self.btn_load_csv.clicked.connect(self.load_csv)
        hdr.addWidget(self.btn_load_csv)
        self.btn_filters = QPushButton(self.tr_text('filters'))
        self._style_compact_action_button(self.btn_filters)
        self._fit_button_to_text(self.btn_filters, extra=10, min_width=58)
        self.btn_filters.clicked.connect(self.open_filter_dialog)
        hdr.addWidget(self.btn_filters)
        self.btn_export_csv = QPushButton(self.tr_text('export_csv'))
        self._style_compact_action_button(self.btn_export_csv)
        self._fit_button_to_text(self.btn_export_csv, extra=10, min_width=78)
        self.btn_export_csv.clicked.connect(self.export_filtered_csv)
        hdr.addWidget(self.btn_export_csv)
        self.btn_export_png = QPushButton(self.tr_text('export_png'))
        self._style_compact_action_button(self.btn_export_png)
        self._fit_button_to_text(self.btn_export_png, extra=10, min_width=78)
        self.btn_export_png.clicked.connect(self.export_current_view_png)
        hdr.addWidget(self.btn_export_png)
        hdr.addStretch()
        controls_block.addLayout(hdr)

        sub_hdr = QHBoxLayout()
        sub_hdr.setSpacing(10)
        arranque_label = QLabel(self.tr_text('select_start'))
        arranque_label.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        sub_hdr.addWidget(arranque_label)
        self.combo = QComboBox()
        self.combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.combo.currentIndexChanged.connect(self.on_select)
        sub_hdr.addWidget(self.combo, 1)
        self.btn_toggle_harmonics = QPushButton(self.tr_text('show_harmonics'))
        self._style_compact_action_button(self.btn_toggle_harmonics)
        self._fit_button_to_text(self.btn_toggle_harmonics, extra=16, min_width=138)
        self.btn_toggle_harmonics.clicked.connect(self.toggle_harmonics_panel)
        sub_hdr.addWidget(self.btn_toggle_harmonics)
        sub_hdr.addWidget(self._build_config_button())
        controls_block.addLayout(sub_hdr)
        main_layout.addLayout(controls_block)

        graphs_widget = QWidget()
        graphs_col = QVBoxLayout(graphs_widget)
        graphs_col.setSpacing(20)
        graphs_col.setContentsMargins(0, 0, 0, 0)
        self._add_graph('SCT', graphs_col, 'Time (s)', '% nominal', title_text='')
        self._add_graph('MLF', graphs_col, 'Mill angle (°)', '% nominal', title_text='')
        graphs_col.setStretch(0, 1)
        graphs_col.setStretch(1, 1)

        params_widget = QWidget()
        params_col = QVBoxLayout(params_widget)
        params_col.setContentsMargins(0, 0, 0, 0)
        params_col.setSpacing(20)
        self._add_params(params_col, title_text='')
        self._add_graph('HAR', params_col, 'Frequency', '% Imax', toggle_units=True, title_text='')
        params_col.setStretch(0, 3)
        params_col.setStretch(1, 2)

        self.viewer_body_splitter = QSplitter(Qt.Horizontal)
        self.viewer_body_splitter.setChildrenCollapsible(False)
        self.viewer_body_splitter.addWidget(graphs_widget)
        self.viewer_body_splitter.addWidget(params_widget)
        self.viewer_body_splitter.setStretchFactor(0, 3)
        self.viewer_body_splitter.setStretchFactor(1, 2)
        self.viewer_body_splitter.setSizes([1080, 840])
        main_layout.addWidget(self.viewer_body_splitter, 1)
        if hasattr(self, 'wrap_HAR'):
            self.wrap_HAR.setVisible(False)

        nav = QHBoxLayout()
        self.btn_prev = QPushButton(self.tr_text('prev')); self.btn_prev.clicked.connect(self.prev_item)
        self._style_compact_action_button(self.btn_prev)
        self._fit_button_to_text(self.btn_prev, extra=18, min_width=104)
        self.btn_next = QPushButton(self.tr_text('next')); self.btn_next.clicked.connect(self.next_item)
        self._style_compact_action_button(self.btn_next)
        self._fit_button_to_text(self.btn_next, extra=18, min_width=112)
        nav.addWidget(self.btn_prev); nav.addStretch(); nav.addWidget(self.btn_next)
        main_layout.addLayout(nav)

        self.viewer_scroll = QScrollArea()
        self.viewer_scroll.setWidgetResizable(True)
        self.viewer_scroll.setFrameShape(QFrame.NoFrame)
        self.viewer_scroll.setWidget(page)
        self.stack.addWidget(self.viewer_scroll)

    def _add_graph(self, key, parent, xlabel, ylabel, toggle_units=False, title_text=None):
        container = QWidget()
        container.setMinimumHeight(320 if key in ('SCT', 'MLF') else 240)
        container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        container.setStyleSheet(self._panel_style())
        vbox = QVBoxLayout(container)
        vbox.setContentsMargins(14, 14, 14, 14)
        vbox.setSpacing(10)

        shown_title = key if title_text is None else title_text
        if shown_title:
            section_title = QLabel(shown_title)
            section_title.setAlignment(Qt.AlignCenter)
            section_title.setStyleSheet("font-size: 18px; font-weight: 700; color: #2F2F2F; padding-bottom: 4px;")
            vbox.addWidget(section_title)

        canvas = FigureCanvas(Figure())
        setattr(self, f'cv_{key}', canvas)
        ax = canvas.figure.add_subplot(111)
        setattr(self, f'ax_{key}', ax)
        navtb = NavToolbar(canvas, self)
        self._style_nav_toolbar(navtb)
        toolbar_row = QHBoxLayout()
        toolbar_row.setContentsMargins(0, 0, 0, 0)
        toolbar_row.setSpacing(6)
        toolbar_row.addWidget(navtb)
        toolbar_row.addStretch()
        if key in ('SCT', 'MLF'):
            expand_btn = QPushButton('Ampliar')
            self._style_cm_expand_button(expand_btn)
            self._fit_button_to_text(expand_btn, extra=14, min_width=76)
            expand_btn.clicked.connect(lambda _=False, graph_key=key: self._open_viewer_graph_fullscreen(graph_key))
            toolbar_row.addWidget(expand_btn)
        vbox.addLayout(toolbar_row)

        canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        vbox.addWidget(canvas)

        if toggle_units:
            btn = QPushButton(self.tr_text('show_frequency_hz'))
            btn.clicked.connect(self.toggle_units)
            vbox.addWidget(btn, alignment=Qt.AlignLeft)

        wrap = QWidget(); h = QHBoxLayout(wrap)
        h.setContentsMargins(0, 0, 0, 0)
        h.addWidget(container,stretch=1)
        wrap.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        setattr(self, f'wrap_{key}', wrap)
        parent.addWidget(wrap)

    def _add_params(self, parent, title_text=''):
        container = QWidget()
        container.setMinimumHeight(420)
        container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        container.setStyleSheet(self._panel_style())
        vbox = QVBoxLayout(container)
        vbox.setContentsMargins(16, 16, 16, 16)
        vbox.setSpacing(12)

        if title_text:
            section_title = QLabel(title_text)
            section_title.setAlignment(Qt.AlignCenter)
            section_title.setStyleSheet("font-size: 18px; font-weight: 700; color: #2F2F2F; padding-bottom: 6px;")
            vbox.addWidget(section_title)

        self.params_table = QTableWidget()
        self.params_table.setColumnCount(2)
        self.params_table.setHorizontalHeaderLabels(['Parámetro', 'Valor'])
        header = self.params_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.params_table.verticalHeader().setVisible(False)
        self.params_table.setAlternatingRowColors(True)
        self.params_table.setShowGrid(False)
        self.params_table.setWordWrap(True)
        self.params_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.params_table.setStyleSheet(self._table_style())
        self.params_table.horizontalHeader().setStyleSheet(self._table_header_style())
        font = QFont(); font.setPointSize(13)
        self.params_table.setFont(font)
        self.params_table.horizontalHeader().setFont(font)
        vbox.addWidget(self.params_table)

        parent.addWidget(container)

    def _wrap_in_scroll_area(self, widget):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidget(widget)
        return scroll

    def _polish_canvas_layout(self, canvas, full_layout=True):
        try:
            self._style_figure(canvas.figure)
            if full_layout:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", UserWarning)
                    canvas.figure.tight_layout(pad=1.1)
        except Exception:
            pass
        if full_layout:
            canvas.draw()
        else:
            canvas.draw_idle()

    def _style_nav_toolbar(self, toolbar):
        toolbar.setIconSize(QSize(16, 16))
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        toolbar.setMaximumHeight(28)
        toolbar.setStyleSheet(
            "QToolBar { background: transparent; border: none; spacing: 0px; padding: 0px; }"
            "QToolButton { background: transparent; border: none; padding: 2px 4px; margin: 0px; min-width: 20px; min-height: 20px; }"
            "QToolButton:hover { background: #E9EEF4; border-radius: 4px; }"
            "QToolButton:pressed { background: #DDE5EE; border-radius: 4px; }"
        )

    def _style_close_toolbutton(self, button):
        button.setText(self.tr_text('cm_close_panel'))
        button.setCursor(Qt.PointingHandCursor)
        button.setToolTip('Cerrar panel')
        button.setStyleSheet(
            "QToolButton { color: #C62828; font-size: 16px; font-weight: 700; background: transparent; border: none; padding: 0px 4px; }"
            "QToolButton:hover { color: white; background: #C62828; border-radius: 8px; }"
        )

    def _style_cm_selector_button(self, button, variant='primary'):
        palette = {
            'primary': ('#EC6E00', '#C85F00'),
            'secondary': ('#F19A3E', '#D78124'),
        }
        base, hover = palette.get(variant, palette['primary'])
        button.setCursor(Qt.PointingHandCursor)
        button.setMinimumHeight(34)
        button.setStyleSheet(
            "QPushButton {"
            f"background-color: {base}; color: white; border: 1px solid {hover};"
            "padding: 7px 12px; border-radius: 8px; font-size: 14px; font-weight: 700; text-align: center; }"
            "QPushButton:hover {"
            f"background-color: {hover};"
            " }"
            "QPushButton:pressed { background-color: #A84E00; }"
        )

    def _style_cm_expand_button(self, button):
        button.setCursor(Qt.PointingHandCursor)
        button.setMinimumHeight(26)
        button.setStyleSheet(
            "QPushButton { background: #F7F7F7; color: #34495E; border: 1px solid #C7D0D9; "
            "padding: 4px 10px; border-radius: 7px; font-size: 14px; font-weight: 700; }"
            "QPushButton:hover { background: #E9EEF4; border-color: #AAB7C4; }"
            "QPushButton:pressed { background: #DCE4EC; }"
        )

    def _style_cm_toolbar_toggle_button(self, button):
        button.setCursor(Qt.PointingHandCursor)
        button.setCheckable(True)
        button.setMinimumHeight(26)
        button.setStyleSheet(
            "QPushButton { background: #F7F7F7; color: #34495E; border: 1px solid #C7D0D9; "
            "padding: 4px 10px; border-radius: 7px; font-size: 14px; font-weight: 700; }"
            "QPushButton:hover { background: #E9EEF4; border-color: #AAB7C4; }"
            "QPushButton:checked { background: #EC6E00; color: white; border-color: #C85F00; }"
            "QPushButton:pressed { background: #DCE4EC; }"
            "QPushButton:checked:pressed { background: #C85F00; }"
        )

    def _style_compact_action_button(self, button):
        button.setMinimumHeight(30)
        button.setStyleSheet(
            "QPushButton { padding: 4px 6px; font-size: 15px; font-weight: 600; }"
        )

    def _fit_button_to_text(self, button, extra=12, min_width=0):
        button.ensurePolished()
        hint_width = button.sizeHint().width()
        fm_width = button.fontMetrics().horizontalAdvance(button.text())
        width = max(hint_width, fm_width + extra + 20)
        final_width = max(min_width, width)
        button.setMinimumWidth(final_width)
        button.setMaximumWidth(final_width)
        button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    def _fit_toolbutton_to_text(self, button, extra=18, min_width=0):
        button.ensurePolished()
        hint_width = button.sizeHint().width()
        fm_width = button.fontMetrics().horizontalAdvance(button.text())
        width = max(hint_width, fm_width + extra + 24)
        final_width = max(min_width, width)
        button.setMinimumWidth(final_width)
        button.setMaximumWidth(final_width)
        button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    def _adjust_cm_figure_layout(self, canvas, has_right_axis=False):
        try:
            show_full_dates = bool(self.cm_state.get("show_full_dates", True))
            show_second_graph = bool(self.cm_second_graph_toggle.isChecked()) if getattr(self, 'cm_second_graph_toggle', None) else False
            if show_full_dates:
                bottom = 0.16 if not show_second_graph else 0.18
            else:
                bottom = 0.08 if not show_second_graph else 0.10
            right = 0.86 if has_right_axis else 0.97
            canvas.figure.subplots_adjust(left=0.10, right=right, top=0.94, bottom=bottom)
        except Exception:
            pass

    def _style_cm_date_edit(self, editor):
        editor.setStyleSheet(
            "QDateEdit { background: white; border: 1px solid #D7D7D7; border-radius: 8px; padding: 4px 8px; }"
            "QDateEdit::drop-down { subcontrol-origin: padding; subcontrol-position: top right; width: 22px; "
            "background: #EC6E00; border-left: 1px solid #C85F00; border-top-right-radius: 8px; border-bottom-right-radius: 8px; }"
            "QCalendarWidget QWidget#qt_calendar_navigationbar { background: #EC6E00; }"
            "QCalendarWidget QToolButton { color: white; background: transparent; font-weight: 700; }"
            "QCalendarWidget QMenu { background: white; }"
            "QCalendarWidget QSpinBox { background: white; border-radius: 4px; padding: 2px; }"
            "QCalendarWidget QAbstractItemView:enabled { selection-background-color: #EC6E00; selection-color: white; }"
            "QCalendarWidget QWidget { alternate-background-color: #FFF6ED; }"
        )

    def _style_figure(self, figure):
        figure.patch.set_facecolor('white')
        for ax in figure.axes:
            ax.set_facecolor('white')
            tick_color = '#303030'
            spine_color = '#B8B8B8'
            title_color = '#303030'
            ax.tick_params(colors=tick_color)
            ax.xaxis.label.set_color(tick_color)
            ax.yaxis.label.set_color(tick_color)
            ax.title.set_color(title_color)
            for spine in ax.spines.values():
                spine.set_color(spine_color)
            legend = ax.get_legend()
            if legend is not None:
                frame = legend.get_frame()
                frame.set_facecolor('white')
                frame.set_edgecolor(spine_color)
                for text in legend.get_texts():
                    text.set_color(tick_color)

    def _make_section_title(self, text):
        lbl = QLabel(text)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setWordWrap(True)
        lbl.setStyleSheet("font-size: 22px; font-weight: 700; color: #303030; padding: 8px 12px;")
        return lbl

    def _read_csv_rows(self, file_path):
        return core_read_csv_rows(file_path)

    def detect_csv_type(self, rows):
        return core_detect_csv_type(rows)

    def _extract_multi_start_rows(self, rows):
        return core_extract_multi_start_rows(rows)

    def _empty_series(self):
        return {
            'speed': np.array([]),
            'current': np.array([]),
            'torque': np.array([]),
            'time': np.array([]),
            'load_torque': np.array([]),
            'motor_torque': np.array([]),
            'dual_current': np.array([]),
            'harmonic_amp': np.array([]),
            'harmonic_freq_raw': np.array([]),
            'harmonic_freq_hz': np.array([]),
        }

    def _create_record(self, *, label, timestamp_text, timestamp_dt, protection, start_type,
                       description, scalars, series, source_kind):
        return {
            'label': label,
            'timestamp_text': timestamp_text,
            'timestamp_dt': timestamp_dt,
            'protection': protection,
            'start_type': start_type,
            'description': description or 'Sin descripción',
            'scalars': scalars,
            'series': series,
            'source_kind': source_kind,
        }

    def _scalar_value(self, record, *names):
        return core_scalar_value(record, *names)

    def _parse_multi_start_record(self, row, label, dt_tuple):
        prot = PROTECTIONS.get(int(parse_numeric(row[0])), 'Unknown')
        st = START_TYPES.get(int(parse_numeric(row[1])), 'Unknown')
        dtstr = format_datetime(dt_tuple)
        desc = 'Sin descripción' if '15163' in row[5:21] else ' '.join(x for x in row[5:21] if x)

        scalars = {
            'Fecha completa': dtstr,
            'Descripción': desc,
            'Protección': prot,
            'Tipo arranque': st
        }
        scalars.update(self._parse_scalars_from_row(row))

        idx = 21 + 24 + 5

        def read_block(n, factor):
            nonlocal idx
            block = [parse_numeric(row[idx + i], factor) for i in range(n)]
            idx += n
            return np.array(block, dtype=float)

        speed = read_block(300, 0.1)
        current = read_block(300, 0.1)
        torque = read_block(300, 0.1)
        load_torque = read_block(180, 0.1)
        motor_torque = read_block(180, 0.1)
        raw_dual = row[idx:idx + 300]
        dual_current = np.array([], dtype=float)
        if any(int(x) != 16383 for x in raw_dual[1:] if x):
            dual_current = np.array([parse_numeric(x, 0.1) for x in raw_dual], dtype=float)
        idx += 300

        amps = []
        raw_freqs = []
        for _ in range(10):
            amps.append(parse_numeric(row[idx])); idx += 1
            raw_freqs.append(parse_numeric(row[idx])); idx += 1
        amps = np.array(amps, dtype=float) / math.sqrt(2)
        raw_freqs = np.array(raw_freqs, dtype=float)
        hz_freqs = raw_freqs / 0.5632

        sample_rate = scalars.get('Sampling rate (ms)', 0)
        time_axis = np.arange(len(speed)) * (sample_rate / 1000 if sample_rate else 0)

        return self._create_record(
            label=label,
            timestamp_text=dtstr,
            timestamp_dt=datetime(*dt_tuple),
            protection=prot,
            start_type=st,
            description=desc,
            scalars=scalars,
            series={
                'speed': speed,
                'current': current,
                'torque': torque,
                'time': time_axis,
                'load_torque': load_torque,
                'motor_torque': motor_torque,
                'dual_current': dual_current,
                'harmonic_amp': amps,
                'harmonic_freq_raw': raw_freqs,
                'harmonic_freq_hz': hz_freqs,
            },
            source_kind='multi_file'
        )

    def parse_multi_start_csv(self, rows):
        return [record.to_legacy() for record in core_parse_multi_start_csv(rows)]

    def _convert_single_scalar(self, raw_value, factor=1.0, offset=0.0):
        base = to_float_or_nan(raw_value)
        if np.isnan(base):
            return np.nan
        return base * factor + offset

    def parse_single_start_csv(self, rows):
        return [record.to_legacy() for record in core_parse_single_start_csv(rows)]

    def parse_csv_records(self, rows):
        csv_type, view_mode, records, _issues = parse_csv_records_to_legacy(rows)
        return csv_type, view_mode, records

    def _rebuild_tabs(self, view_mode):
        if self.tabs_container is not None:
            self.stack.removeWidget(self.tabs_container)
            self.tabs_container.deleteLater()
            self.tabs_container = None
            self.tabs_widget = None

        self.cm_list = None
        self.cm_param_list = None
        self.cm_param_list_secondary = None
        self.cm_param_label_secondary = None
        self.cm_canvas = None
        self.cm_second_graph_toggle = None
        self.cm_restore_btn = None
        self.cm_cursor_info_main = None
        self.cm_cursor_info_secondary = None
        self.cm_ax = None
        self.cm_ax2 = None
        self.cm_div_left = None
        self.cm_div_right = None
        self.cm_gridx = None
        self.historical_canvas = None
        self.historical_axes = []
        self.cm_hidden_indices = set()
        self.history_hidden_indices = set()

        self.tabs_widget = QTabWidget()
        self.tabs_widget.addTab(self.viewer_scroll, self.tr_text('viewer_tab'))

        if view_mode == 'multi_startup_view':
            self.tabs_widget.addTab(self._wrap_in_scroll_area(self._build_cm_page()), self.tr_text('cm_tab'))
            self.tabs_widget.addTab(self._wrap_in_scroll_area(self._build_history_page()), self.tr_text('history_tab'))

        self.tabs_container = QWidget()
        lay = QVBoxLayout(self.tabs_container)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.addWidget(self.tabs_widget)
        self.stack.addWidget(self.tabs_container)

    def _build_history_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(12)

        controls = QHBoxLayout()
        controls.setSpacing(10)
        history_speed_label = QLabel(self.tr_text('history_nominal_speed'))
        history_speed_label.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        controls.addWidget(history_speed_label)
        self.history_nominal_speed = QDoubleSpinBox()
        self.history_nominal_speed.setRange(1.0, 10000.0)
        self.history_nominal_speed.setDecimals(1)
        self.history_nominal_speed.setMinimumWidth(110)
        self.history_nominal_speed.setValue(self.nominal_speed_rpm)
        self.history_nominal_speed.valueChanged.connect(self._on_nominal_speed_changed)
        controls.addWidget(self.history_nominal_speed)
        self.history_nominal_current_label = QLabel(self.tr_text('history_nominal_current'))
        self.history_nominal_current_label.setStyleSheet("font-size: 12px; color: #4F4F4F; padding-left: 10px;")
        controls.addWidget(self.history_nominal_current_label)
        self.btn_linearity = QPushButton(self.tr_text('analysis_linearity'))
        self._style_compact_action_button(self.btn_linearity)
        self._fit_button_to_text(self.btn_linearity, extra=10, min_width=94)
        self.btn_linearity.clicked.connect(self.toggle_linearity_analysis)
        self.btn_current_analysis = QPushButton(self.tr_text('analysis_current'))
        self._style_compact_action_button(self.btn_current_analysis)
        self._fit_button_to_text(self.btn_current_analysis, extra=10, min_width=88)
        self.btn_current_analysis.clicked.connect(self.toggle_current_analysis)
        controls.addStretch()
        controls.addWidget(self.btn_linearity)
        controls.addWidget(self.btn_current_analysis)
        layout.addLayout(controls)
        layout.addSpacing(10)

        load_info_row = QHBoxLayout()
        load_info_row.setSpacing(8)
        self.history_load_info_title = QLabel(self.tr_text('history_load_title'))
        self.history_load_info_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #303030;")
        load_info_row.addWidget(self.history_load_info_title)
        self.btn_history_load_info = QPushButton('i')
        self.btn_history_load_info.setFixedSize(28, 28)
        self.btn_history_load_info.setCheckable(True)
        self.btn_history_load_info.setStyleSheet(
            "QPushButton { background-color: #2F5D8A; color: white; border-radius: 14px; font-weight: 700; padding: 0px; }"
            "QPushButton:hover { background-color: #244A6D; }"
            "QPushButton:checked { background-color: #244A6D; }"
        )
        self.btn_history_load_info.clicked.connect(self._toggle_history_load_info)
        load_info_row.addWidget(self.btn_history_load_info)
        load_info_row.addStretch()
        layout.addLayout(load_info_row)

        self.history_load_info_panel = QLabel(
            "Modelo usado:\n"
            "1. Se toma la curva de par resistente `load_torque`.\n"
            "2. Se analiza la parte estacionaria a partir de 150°.\n"
            "3. Se calcula la mediana de ese tramo para obtener un par resistente representativo.\n"
            "4. Se normaliza con `Amp frz(%)` usando: Carga[%] = 100 * Par resistente estacionario / Amp frz(%).\n"
            "5. `Amp frz(%)` se usa como referencia de calibración del esfuerzo resistente congelado del arranque.\n"
            "6. El resultado final se limita al rango físico 0-100%."
        )
        self.history_load_info_panel.setWordWrap(True)
        self.history_load_info_panel.setVisible(False)
        self.history_load_info_panel.setStyleSheet(
            "background: #F7F9FC; color: #36414A; border: 1px solid #D8E0E8; "
            "border-radius: 10px; padding: 10px 12px; font-size: 11px;"
        )
        layout.addWidget(self.history_load_info_panel)

        self.historical_canvas = FigureCanvas(Figure(figsize=(10, 8)))
        self.historical_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.historical_canvas.setStyleSheet(self._panel_style())
        page.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        historical_toolbar = NavToolbar(self.historical_canvas, self)
        self._style_nav_toolbar(historical_toolbar)
        historical_toolbar_row = QHBoxLayout()
        historical_toolbar_row.setContentsMargins(0, 0, 0, 0)
        historical_toolbar_row.setSpacing(6)
        historical_toolbar_row.addWidget(historical_toolbar)
        historical_toolbar_row.addStretch()
        self.history_area_delete_btn = QPushButton('Borrado área')
        self._style_cm_toolbar_toggle_button(self.history_area_delete_btn)
        self._fit_button_to_text(self.history_area_delete_btn, extra=12, min_width=90)
        self.history_area_delete_btn.setToolTip('Activa o desactiva el borrado por área en la gráfica de carga.')
        self.history_area_delete_btn.toggled.connect(self._toggle_history_area_delete)
        historical_toolbar_row.addWidget(self.history_area_delete_btn)
        self.history_color_btn = QPushButton('Color')
        self._style_cm_expand_button(self.history_color_btn)
        self._fit_button_to_text(self.history_color_btn, extra=12, min_width=64)
        self.history_color_btn.setToolTip('Cambia el color de la curva de evolución histórica de carga.')
        self.history_color_btn.clicked.connect(self._pick_history_load_color)
        historical_toolbar_row.addWidget(self.history_color_btn)
        self.history_expand_btn = QPushButton('Ampliar')
        self._style_cm_expand_button(self.history_expand_btn)
        self._fit_button_to_text(self.history_expand_btn, extra=12, min_width=74)
        self.history_expand_btn.setToolTip('Abre la gráfica histórica de carga en una ventana maximizada.')
        self.history_expand_btn.clicked.connect(self._open_history_load_fullscreen)
        historical_toolbar_row.addWidget(self.history_expand_btn)
        self.history_restore_btn = QPushButton('Restaurar')
        self._style_cm_expand_button(self.history_restore_btn)
        self._fit_button_to_text(self.history_restore_btn, extra=12, min_width=80)
        self.history_restore_btn.setToolTip('Recupera todos los puntos borrados del histórico y limpia la selección por área.')
        self.history_restore_btn.clicked.connect(self._restore_history_hidden_points)
        historical_toolbar_row.addWidget(self.history_restore_btn)
        layout.addLayout(historical_toolbar_row)
        layout.addWidget(self.historical_canvas, 1)
        self.historical_canvas.mpl_connect('button_press_event', self._on_history_click)
        self.historical_canvas.mpl_connect('motion_notify_event', self._on_history_motion)
        self.historical_canvas.mpl_connect('button_release_event', self._on_history_release)
        self.redraw_history()
        return page

    def _valid_metric_pairs(self, values):
        pairs = []
        for idx, value in enumerate(values):
            try:
                numeric = float(value)
            except Exception:
                continue
            if np.isnan(numeric):
                continue
            pairs.append((idx, numeric))
        return pairs

    def _draw_no_data(self, ax, title):
        ax.clear()
        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.text(0.5, 0.5, 'No disponible', ha='center', va='center', fontsize=12, color='#666666')
        ax.set_xticks([])
        ax.set_yticks([])

    def _build_pie_counts(self, values, classifiers):
        counts = []
        labels = []
        colors = []
        for label, color, predicate in classifiers:
            count = sum(1 for value in values if predicate(value))
            if count > 0:
                counts.append(count)
                labels.append(label)
                colors.append(color)
        return counts, labels, colors

    def _is_successful_start(self, record):
        return core_is_successful_start(record)

    def _is_externally_aborted_start(self, record):
        return core_is_externally_aborted_start(record)

    def _estimate_mill_load_pct(self, record):
        series = record.get('series', {})
        load_torque = np.asarray(series.get('load_torque', []), dtype=float)
        load_torque = load_torque[np.isfinite(load_torque)]

        amp_frozen = self._scalar_value(record, 'Amp frz(%)', 'frzChrgAmp(%FLT)')
        try:
            amp_frozen = float(amp_frozen)
        except Exception:
            amp_frozen = np.nan

        if load_torque.size == 0:
            if np.isnan(amp_frozen):
                return np.nan
            return float(np.clip(amp_frozen, 0.0, 100.0))

        angles = np.linspace(0.0, 180.0, load_torque.size)
        stationary_mask = angles >= 150.0
        stationary_torque = load_torque[stationary_mask]
        stationary_torque = stationary_torque[np.isfinite(stationary_torque)]

        # If there are too few samples beyond 150°, use the tail of the curve as a fallback.
        if stationary_torque.size < 5:
            tail_count = max(5, int(round(load_torque.size * 0.15)))
            stationary_torque = load_torque[-tail_count:]
            stationary_torque = stationary_torque[np.isfinite(stationary_torque)]

        if stationary_torque.size == 0:
            if np.isnan(amp_frozen):
                return np.nan
            return float(np.clip(amp_frozen, 0.0, 100.0))

        # The stationary resistant torque is the best proxy for the real mill load.
        steady_resistant_torque = float(np.nanmedian(stationary_torque))
        if np.isnan(steady_resistant_torque):
            return np.nan

        if np.isnan(amp_frozen) or amp_frozen <= 0:
            return float(np.clip(steady_resistant_torque, 0.0, 100.0))

        estimated_load_pct = 100.0 * steady_resistant_torque / amp_frozen
        return float(np.clip(estimated_load_pct, 0.0, 100.0))

    def _compute_history_metrics(self):
        metrics = {
            'load_pct': [],
            'success_flags': [],
            'cascadeo': [],
            'current_pct_nominal': [],
        }
        for record in self.starts:
            metrics['load_pct'].append(self._estimate_mill_load_pct(record))
            metrics['cascadeo'].append(self._scalar_value(record, 'Ángulo (°)', 'Ãngulo (Â°)', 'tumblingAngle(deg)'))

            current_series = np.asarray(record.get('series', {}).get('current', []), dtype=float)
            current_series = current_series[np.isfinite(current_series)]
            metrics['current_pct_nominal'].append(np.nanmax(current_series) if current_series.size else np.nan)
            metrics['success_flags'].append(self._is_successful_start(record))
        return metrics

    def _estimated_nominal_current(self):
        estimates = []
        for idx, record in enumerate(self.starts):
            if idx in self.history_hidden_indices:
                continue
            imax = self._scalar_value(record, 'I máx (Arms)', 'maxCurrent(Arms)')
            current_series = np.asarray(record.get('series', {}).get('current', []), dtype=float)
            current_series = current_series[np.isfinite(current_series)]
            if current_series.size == 0:
                continue
            peak_pct = float(np.nanmax(current_series))
            try:
                imax = float(imax)
            except Exception:
                continue
            if np.isnan(imax) or peak_pct <= 0:
                continue
            estimates.append(imax / (peak_pct / 100.0))
        if not estimates:
            return np.nan
        return float(np.median(estimates))

    def _linearity_pairs(self, x_name, y_name):
        pairs = []
        x_names = x_name if isinstance(x_name, (list, tuple)) else [x_name]
        y_names = y_name if isinstance(y_name, (list, tuple)) else [y_name]
        for idx, record in enumerate(self.starts):
            if idx in self.history_hidden_indices:
                continue
            if not self._is_successful_start(record):
                continue
            x = self._scalar_value(record, *x_names)
            y = self._scalar_value(record, *y_names)
            try:
                x = float(x)
                y = float(y)
            except Exception:
                continue
            if np.isnan(x) or np.isnan(y):
                continue
            pairs.append((x, y, record.get('label', f'Arranque {idx + 1}')))
        return pairs

    def _successful_speed_resistance_ratio_pairs(self):
        pairs = []
        for idx, record in enumerate(self.starts):
            if idx in self.history_hidden_indices:
                continue
            if not self._is_successful_start(record):
                continue
            final_speed = self._scalar_value(record, 'Vel fin', 'finalSpeed(rpm)')
            ratio_r = self._scalar_value(record, 'Ratio R', 'resRatio')
            try:
                final_speed = float(final_speed)
                ratio_r = float(ratio_r)
            except Exception:
                continue
            if np.isnan(final_speed) or np.isnan(ratio_r):
                continue
            speed_ratio = final_speed / self.nominal_speed_rpm if self.nominal_speed_rpm else np.nan
            if np.isnan(speed_ratio):
                continue
            pairs.append((ratio_r, speed_ratio, record.get('label', f'Arranque {idx + 1}')))
        return pairs

    def _successful_current_analysis_pairs(self, nominal_current):
        pairs = []
        if np.isnan(nominal_current) or nominal_current <= 0:
            return pairs
        for idx, record in enumerate(self.starts):
            if idx in self.history_hidden_indices:
                continue
            if not self._is_successful_start(record):
                continue
            init_current = self._scalar_value(record, 'I inicial', 'initCurrent(Arms)')
            short_current = self._scalar_value(record, 'I cortoc (A)', 'I cortoc', 'maxShortCurr(A)')
            try:
                init_current = float(init_current)
                short_current = float(short_current)
            except Exception:
                continue
            if np.isnan(init_current) or np.isnan(short_current):
                continue
            init_pct = 100.0 * init_current / nominal_current
            short_pct = 100.0 * short_current / nominal_current
            if np.isnan(init_pct) or np.isnan(short_pct):
                continue
            pairs.append((init_pct, short_pct, record.get('label', f'Arranque {idx + 1}'), idx))
        return pairs

    def _on_nominal_speed_changed(self, value):
        self.nominal_speed_rpm = float(value)
        if self.history_analysis_mode != 'none':
            self.redraw_history()

    def _toggle_history_load_info(self):
        if hasattr(self, 'history_load_info_panel') and self.history_load_info_panel:
            visible = bool(self.btn_history_load_info.isChecked()) if hasattr(self, 'btn_history_load_info') else False
            self.history_load_info_panel.setVisible(visible)

    def _draw_linearity_subplot(self, ax, pairs, x_label, y_label, title):
        ax.clear()
        ax.set_title(title, fontsize=12, fontweight='bold')
        if len(pairs) < 2:
            ax.text(0.5, 0.5, 'Datos insuficientes', ha='center', va='center', fontsize=12, color='#666666')
            ax.set_xticks([])
            ax.set_yticks([])
            return

        x = np.array([p[0] for p in pairs], dtype=float)
        y = np.array([p[1] for p in pairs], dtype=float)
        ax.scatter(x, y, s=46, color='#EC6E00', edgecolors='white', linewidth=0.8, alpha=0.92)

        coeffs = np.polyfit(x, y, 1)
        trend = np.poly1d(coeffs)
        x_fit = np.linspace(np.min(x), np.max(x), 100)
        y_fit = trend(x_fit)
        ax.plot(x_fit, y_fit, color='#2F5D8A', linewidth=2.0)

        y_pred = trend(x)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else np.nan
        ax.text(
            0.03, 0.94,
            f"y = {coeffs[0]:.3f}x + {coeffs[1]:.3f}\nR² = {r2:.3f}" if not np.isnan(r2) else f"y = {coeffs[0]:.3f}x + {coeffs[1]:.3f}",
            transform=ax.transAxes,
            va='top',
            fontsize=10,
            bbox=dict(boxstyle='round,pad=0.35', facecolor='white', edgecolor='#D6D6D6')
        )
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.grid(True, alpha=0.25)

    def toggle_linearity_analysis(self):
        self.history_analysis_mode = 'none' if self.history_analysis_mode == 'linearity' else 'linearity'
        self._refresh_history_analysis_buttons()
        self.redraw_history()

    def toggle_current_analysis(self):
        self.history_analysis_mode = 'none' if self.history_analysis_mode == 'current' else 'current'
        self._refresh_history_analysis_buttons()
        self.redraw_history()

    def _refresh_history_analysis_buttons(self):
        if hasattr(self, 'btn_linearity') and self.btn_linearity:
            self.btn_linearity.setText(
                self.tr_text('hide_analysis_linearity') if self.history_analysis_mode == 'linearity' else self.tr_text('analysis_linearity')
            )
            self._fit_button_to_text(self.btn_linearity, extra=10, min_width=94)
        if hasattr(self, 'btn_current_analysis') and self.btn_current_analysis:
            self.btn_current_analysis.setText(
                self.tr_text('hide_analysis_current') if self.history_analysis_mode == 'current' else self.tr_text('analysis_current')
            )
            self._fit_button_to_text(self.btn_current_analysis, extra=10, min_width=88)

    def _draw_current_analysis_subplot(self, ax, pairs, nominal_current):
        ax.clear()
        ax.set_title('I cortocircuito vs I inicial', fontsize=12, fontweight='bold')
        if len(pairs) < 2:
            ax._history_point_indices = []
            ax._history_plot_xy = np.empty((0, 2))
            ax.text(0.5, 0.5, 'Datos insuficientes', ha='center', va='center', fontsize=12, color='#666666')
            ax.set_xticks([])
            ax.set_yticks([])
            return

        x = np.array([p[0] for p in pairs], dtype=float)
        y = np.array([p[1] for p in pairs], dtype=float)
        point_indices = [p[3] for p in pairs]
        x_max = max(145.0, float(np.nanmax(x)) * 1.08)
        y_max = max(255.0, float(np.nanmax(y)) * 1.08)

        ax.axvspan(140.0, x_max, color='#D64545', alpha=0.12)
        ax.axhspan(250.0, y_max, color='#D64545', alpha=0.12)
        ax.axvline(140.0, color='#C94A4A', linestyle='--', linewidth=1.2)
        ax.axhline(250.0, color='#C94A4A', linestyle='--', linewidth=1.2)
        ax.scatter(x, y, s=52, color='#EC6E00', edgecolors='white', linewidth=0.8, alpha=0.92)

        coeffs = np.polyfit(x, y, 1)
        trend = np.poly1d(coeffs)
        x_fit = np.linspace(np.min(x), np.max(x), 100)
        y_fit = trend(x_fit)
        ax.plot(x_fit, y_fit, color='#2F5D8A', linewidth=2.0)

        y_pred = trend(x)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else np.nan
        nominal_text = f'Nominal usada: {nominal_current:.2f} A'
        fit_text = f"y = {coeffs[0]:.3f}x + {coeffs[1]:.3f}\nR² = {r2:.3f}" if not np.isnan(r2) else f"y = {coeffs[0]:.3f}x + {coeffs[1]:.3f}"
        ax.text(
            0.03, 0.97,
            f'{fit_text}\n{nominal_text}',
            transform=ax.transAxes,
            va='top',
            fontsize=10,
            bbox=dict(boxstyle='round,pad=0.35', facecolor='white', edgecolor='#D6D6D6')
        )
        ax.text(141.5, y_max * 0.98, '> 140% nominal', color='#A93A3A', fontsize=9, va='top')
        ax.text(x_max * 0.68, 251.5, '> 250% nominal', color='#A93A3A', fontsize=9, va='bottom')
        ax.set_xlim(0, x_max)
        ax.set_ylim(0, y_max)
        ax.set_xlabel('Corriente inicial [% nominal]')
        ax.set_ylabel('Corriente de cortocircuito [% nominal]')
        ax.grid(True, alpha=0.25)
        ax._history_point_indices = point_indices
        ax._history_plot_xy = np.column_stack([x, y])

    def _history_x_labels(self, indices):
        labels = []
        use_dates = all(self.starts[idx].get('timestamp_dt') is not None for idx in indices)
        for idx in indices:
            if use_dates:
                dt = self.starts[idx]['timestamp_dt']
                quarter = ((dt.month - 1) // 3) + 1
                labels.append(f"{dt.year} T{quarter}")
            else:
                labels.append(f"Arranque {idx + 1}")
        return labels

    def _configure_history_time_axis(self, ax, indices):
        dated = [(idx, self.starts[idx].get('timestamp_dt')) for idx in indices]
        dated = [(idx, dt) for idx, dt in dated if dt is not None]
        if len(dated) != len(indices):
            x = np.arange(len(indices))
            ax.set_xticks(x)
            ax.set_xticklabels([f"Arranque {idx + 1}" for idx in indices], rotation=25, ha='right')
            return x, False

        x_dates = [dt for _, dt in dated]
        x = mdates.date2num(x_dates)
        start_dt = min(x_dates)
        end_dt = max(x_dates)
        span_months = max(1, (end_dt.year - start_dt.year) * 12 + (end_dt.month - start_dt.month) + 1)
        if span_months <= 12:
            interval = 1
        elif span_months <= 24:
            interval = 2
        elif span_months <= 48:
            interval = 3
        else:
            interval = 6
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=interval))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
        ax.tick_params(axis='x', which='major', labelrotation=0, pad=8)
        return x, True

    def _toggle_history_area_delete(self, checked):
        self.history_area_delete_enabled = bool(checked)
        if not checked:
            self.history_area_selection_bounds = None
            self.history_area_selection_indices.clear()
        self.redraw_history()

    def _restore_history_hidden_points(self):
        self.history_hidden_indices.clear()
        self.history_area_selection_bounds = None
        self.history_area_selection_indices.clear()
        if getattr(self, 'history_area_delete_btn', None):
            self.history_area_delete_btn.blockSignals(True)
            self.history_area_delete_btn.setChecked(False)
            self.history_area_delete_btn.blockSignals(False)
        self.history_area_delete_enabled = False
        self.redraw_history()

    def _delete_history_area_selection(self):
        if not self.history_area_selection_indices:
            return False
        self.history_hidden_indices.update(self.history_area_selection_indices)
        self.history_area_selection_bounds = None
        self.history_area_selection_indices.clear()
        self.redraw_history()
        return True

    def _pick_history_load_color(self):
        color = QColorDialog.getColor(QColor(self.history_load_color), self, 'Seleccionar color de la curva')
        if not color.isValid():
            return
        self.history_load_color = color.name()
        self.redraw_history()

    def _open_viewer_graph_fullscreen(self, key):
        canvas = getattr(self, f'cv_{key}', None)
        ax_src = getattr(self, f'ax_{key}', None)
        if canvas is None or ax_src is None:
            return
        dialog = QDialog(self)
        dialog.setAttribute(Qt.WA_DeleteOnClose, True)
        dialog.setWindowTitle(f'{key} - Pantalla completa')
        dialog.resize(1440, 900)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)
        full_canvas = FigureCanvas(Figure())
        full_ax = full_canvas.figure.add_subplot(111)
        toolbar = NavToolbar(full_canvas, dialog)
        self._style_nav_toolbar(toolbar)
        toolbar_row = QHBoxLayout()
        toolbar_row.setContentsMargins(0, 0, 0, 0)
        toolbar_row.addWidget(toolbar)
        toolbar_row.addStretch()
        layout.addLayout(toolbar_row)
        layout.addWidget(full_canvas, 1)

        for line in ax_src.get_lines():
            x = np.asarray(line.get_xdata())
            y = np.asarray(line.get_ydata())
            full_ax.plot(
                x, y,
                color=line.get_color(),
                linestyle=line.get_linestyle(),
                linewidth=line.get_linewidth(),
                marker=line.get_marker(),
                markersize=line.get_markersize(),
                label=line.get_label()
            )
        for collection in ax_src.collections:
            try:
                offsets = collection.get_offsets()
                if len(offsets):
                    full_ax.scatter(offsets[:, 0], offsets[:, 1], s=collection.get_sizes(), color=collection.get_facecolor(), edgecolors=collection.get_edgecolor())
            except Exception:
                pass
        full_ax.set_title(ax_src.get_title())
        full_ax.set_xlabel(ax_src.get_xlabel())
        full_ax.set_ylabel(ax_src.get_ylabel())
        full_ax.grid(True, alpha=0.25)
        handles, labels = full_ax.get_legend_handles_labels()
        if handles:
            full_ax.legend()
        self._polish_canvas_layout(full_canvas, full_layout=False)
        dialog.showMaximized()

    def _open_history_load_fullscreen(self):
        if not getattr(self, 'starts', None):
            return
        dialog = QDialog(self)
        dialog.setAttribute(Qt.WA_DeleteOnClose, True)
        dialog.setWindowTitle('Histórico - Evolución histórica de carga')
        dialog.resize(1440, 900)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)
        canvas = FigureCanvas(Figure())
        ax = canvas.figure.add_subplot(111)
        toolbar = NavToolbar(canvas, dialog)
        self._style_nav_toolbar(toolbar)
        toolbar_row = QHBoxLayout()
        toolbar_row.setContentsMargins(0, 0, 0, 0)
        toolbar_row.addWidget(toolbar)
        toolbar_row.addStretch()
        layout.addLayout(toolbar_row)
        layout.addWidget(canvas, 1)

        metrics = self._compute_history_metrics()
        visible_history = [i for i in range(len(self.starts)) if i not in self.history_hidden_indices]
        valid_load = [(idx, val) for idx, val in self._valid_metric_pairs(metrics['load_pct']) if idx in visible_history]
        if valid_load:
            x_idx = [idx for idx, _ in valid_load]
            y_values = [value for _, value in valid_load]
            x_values, uses_dates = self._configure_history_time_axis(ax, x_idx)
            ax.plot(x_values, y_values, color=self.history_load_color, linewidth=2.2, marker='o')
            ax.fill_between(x_values, y_values, color=self.history_load_color, alpha=0.15)
            if self.history_area_selection_indices:
                selected_points = [(xv, yv) for xv, yv, idx in zip(x_values, y_values, x_idx) if idx in self.history_area_selection_indices]
                if selected_points:
                    ax.scatter(
                        [pt[0] for pt in selected_points],
                        [pt[1] for pt in selected_points],
                        s=76,
                        color='#C62828',
                        edgecolors='white',
                        linewidths=1.1,
                        zorder=6
                    )
            if self.history_area_selection_bounds is not None:
                xmin, xmax, ymin, ymax = self.history_area_selection_bounds
                rect = Rectangle((xmin, ymin), xmax - xmin, ymax - ymin, facecolor='#C62828', edgecolor='#C62828', linewidth=1.4, alpha=0.16, zorder=5)
                ax.add_patch(rect)
            ax.set_title('Evolución histórica del % de carga', fontsize=12, fontweight='bold')
            ax.set_xlabel('Perspectiva temporal')
            ax.set_ylabel('% de carga')
            ax.grid(True, axis='y', alpha=0.25)
            if uses_dates:
                ax.set_xlim(min(x_values), max(x_values))
        else:
            self._draw_no_data(ax, 'Evolución histórica del % de carga')
        self._polish_canvas_layout(canvas, full_layout=False)
        dialog.showMaximized()

    def redraw_history(self):
        if self.historical_canvas is None:
            return

        nominal_current = self._estimated_nominal_current()
        if hasattr(self, 'history_nominal_current_label') and self.history_nominal_current_label:
            if np.isnan(nominal_current):
                self.history_nominal_current_label.setText(self.tr_text('history_nominal_current'))
            else:
                self.history_nominal_current_label.setText(self.tr_text('history_nominal_current_value', value=nominal_current))

        fig = self.historical_canvas.figure
        fig.clear()
        if self.history_analysis_mode == 'linearity':
            gs = fig.add_gridspec(3, 4, width_ratios=[1.18, 1.18, 1.18, 1.15], height_ratios=[1.0, 1.0, 1.28], hspace=0.56, wspace=0.62)
            ax_load = fig.add_subplot(gs[0:2, 0:3])
            ax_result = fig.add_subplot(gs[2, 0])
            ax_cascadeo = fig.add_subplot(gs[2, 1])
            ax_current = fig.add_subplot(gs[2, 2])
            ax_line_1 = fig.add_subplot(gs[0, 3])
            ax_line_2 = fig.add_subplot(gs[1, 3])
            ax_line_3 = fig.add_subplot(gs[2, 3])
            self.historical_axes = [ax_load, ax_result, ax_cascadeo, ax_current, ax_line_1, ax_line_2, ax_line_3]
        elif self.history_analysis_mode == 'current':
            gs = fig.add_gridspec(3, 4, width_ratios=[1.18, 1.18, 1.18, 1.15], height_ratios=[1.0, 1.0, 1.28], hspace=0.56, wspace=0.62)
            ax_load = fig.add_subplot(gs[0:2, 0:3])
            ax_result = fig.add_subplot(gs[2, 0])
            ax_cascadeo = fig.add_subplot(gs[2, 1])
            ax_current = fig.add_subplot(gs[2, 2])
            ax_line_1 = fig.add_subplot(gs[:, 3])
            ax_line_2 = ax_line_3 = None
            self.historical_axes = [ax_load, ax_result, ax_cascadeo, ax_current, ax_line_1]
        else:
            gs = fig.add_gridspec(2, 3, height_ratios=[1.5, 1.22], hspace=0.42, wspace=0.64)
            ax_load = fig.add_subplot(gs[0, :])
            ax_result = fig.add_subplot(gs[1, 0])
            ax_cascadeo = fig.add_subplot(gs[1, 1])
            ax_current = fig.add_subplot(gs[1, 2])
            ax_line_1 = ax_line_2 = ax_line_3 = None
            self.historical_axes = [ax_load, ax_result, ax_cascadeo, ax_current]
            fig.subplots_adjust(top=0.93, bottom=0.08)

        metrics = self._compute_history_metrics()
        visible_history = [i for i in range(len(self.starts)) if i not in self.history_hidden_indices]

        valid_load = [(idx, val) for idx, val in self._valid_metric_pairs(metrics['load_pct']) if idx in visible_history]
        if valid_load:
            x_idx = [idx for idx, _ in valid_load]
            y_values = [value for _, value in valid_load]
            x_values, uses_dates = self._configure_history_time_axis(ax_load, x_idx)
            ax_load.plot(x_values, y_values, color=self.history_load_color, linewidth=2.2, marker='o')
            ax_load.fill_between(x_values, y_values, color=self.history_load_color, alpha=0.15)
            ax_load._history_point_indices = x_idx
            ax_load._history_plot_xy = np.column_stack([x_values, y_values])
            if self.history_area_selection_indices:
                selected_points = [(xv, yv) for xv, yv, idx in zip(x_values, y_values, x_idx) if idx in self.history_area_selection_indices]
                if selected_points:
                    ax_load.scatter(
                        [pt[0] for pt in selected_points],
                        [pt[1] for pt in selected_points],
                        s=76,
                        color='#C62828',
                        edgecolors='white',
                        linewidths=1.1,
                        zorder=6
                    )
            if self.history_area_selection_bounds is not None:
                xmin, xmax, ymin, ymax = self.history_area_selection_bounds
                rect = Rectangle(
                    (xmin, ymin),
                    xmax - xmin,
                    ymax - ymin,
                    facecolor='#C62828',
                    edgecolor='#C62828',
                    linewidth=1.4,
                    alpha=0.16,
                    zorder=5
                )
                ax_load.add_patch(rect)
            ax_load.set_title('Evolución histórica del % de carga', fontsize=12, fontweight='bold')
            ax_load.set_xlabel('Perspectiva temporal')
            ax_load.set_ylabel('% de carga')
            ax_load.grid(True, axis='y', alpha=0.25)
            if uses_dates:
                ax_load.set_xlim(min(x_values), max(x_values))
        else:
            self._draw_no_data(ax_load, 'Evolución histórica del % de carga')
            ax_load._history_point_indices = []
            ax_load._history_plot_xy = np.empty((0, 2))

        success_count = sum(1 for idx, record in enumerate(self.starts) if idx in visible_history and self._is_successful_start(record))
        external_abort_count = sum(1 for idx, record in enumerate(self.starts) if idx in visible_history and self._is_externally_aborted_start(record))
        other_fail_count = sum(
            1 for idx, record in enumerate(self.starts)
            if idx in visible_history and not self._is_successful_start(record) and not self._is_externally_aborted_start(record)
        )
        result_counts = [count for count in (success_count, external_abort_count, other_fail_count) if count > 0]
        result_labels = []
        result_colors = []
        if success_count > 0:
            result_labels.append('Exitosos')
            result_colors.append('#2EAD59')
        if external_abort_count > 0:
            result_labels.append('Abortados externamente')
            result_colors.append('#C94A4A')
        if other_fail_count > 0:
            result_labels.append('Otros fallidos')
            result_colors.append('#D64545')
        if result_counts:
            wedges, _, _ = ax_result.pie(
                result_counts,
                labels=None,
                colors=result_colors,
                autopct='%1.0f%%',
                startangle=90,
                pctdistance=0.72,
                radius=1.08,
                wedgeprops=dict(width=0.48, edgecolor='white')
            )
            ax_result.set_title('Arranques exitosos vs fallidos', fontsize=12, fontweight='bold')
            ax_result.legend(
                wedges,
                result_labels,
                loc='center left',
                bbox_to_anchor=(1.02, 0.5),
                frameon=False,
                fontsize=9,
                labelspacing=1.05,
                handletextpad=0.8,
                borderaxespad=0.5
            )
        else:
            self._draw_no_data(ax_result, 'Arranques exitosos vs fallidos')

        cascade_counts, cascade_labels, cascade_colors = self._build_pie_counts(
            [value for idx, value in self._valid_metric_pairs(metrics['cascadeo']) if idx in visible_history],
            [
                ('< 60º', '#2EAD59', lambda v: v < 60),
                ('60º a 70º', '#F1C40F', lambda v: 60 <= v <= 70),
                ('70º a 80º', '#F39C12', lambda v: 70 < v <= 80),
                ('> 80º', '#D64545', lambda v: v > 80),
            ]
        )
        if cascade_counts:
            wedges, _, _ = ax_cascadeo.pie(
                cascade_counts,
                labels=None,
                colors=cascade_colors,
                autopct='%1.0f%%',
                startangle=90,
                pctdistance=0.72,
                radius=1.08,
                wedgeprops=dict(width=0.48, edgecolor='white')
            )
            ax_cascadeo.set_title('Clasificación de cascadeo', fontsize=12, fontweight='bold')
            ax_cascadeo.legend(
                wedges,
                cascade_labels,
                loc='center left',
                bbox_to_anchor=(1.02, 0.5),
                frameon=False,
                fontsize=9,
                labelspacing=1.05,
                handletextpad=0.8,
                borderaxespad=0.5
            )
        else:
            self._draw_no_data(ax_cascadeo, 'Clasificación de cascadeo')

        current_counts, current_labels, current_colors = self._build_pie_counts(
            [value for idx, value in self._valid_metric_pairs(metrics['current_pct_nominal']) if idx in visible_history],
            [
                ('90% a 120%', '#2EAD59', lambda v: 90 <= v <= 120),
                ('80%-90%\n120%-130%', '#F1C40F', lambda v: (80 <= v < 90) or (120 < v <= 130)),
                ('75%-80%\n130%-140%', '#F39C12', lambda v: (75 <= v < 80) or (130 < v <= 140)),
                ('< 75% / > 140%', '#D64545', lambda v: v < 75 or v > 140),
            ]
        )
        if current_counts:
            wedges, _, _ = ax_current.pie(
                current_counts,
                labels=None,
                colors=current_colors,
                autopct='%1.0f%%',
                startangle=90,
                pctdistance=0.72,
                radius=1.08,
                wedgeprops=dict(width=0.48, edgecolor='white')
            )
            ax_current.set_title('% de corriente nominal en el arranque', fontsize=12, fontweight='bold')
            ax_current.legend(
                wedges,
                current_labels,
                loc='center left',
                bbox_to_anchor=(1.02, 0.5),
                frameon=False,
                fontsize=9,
                labelspacing=1.12,
                handletextpad=0.8,
                borderaxespad=0.6
            )
        else:
            self._draw_no_data(ax_current, '% de corriente nominal en el arranque')

        if self.history_analysis_mode == 'linearity':
            pairs_1 = self._linearity_pairs(('R ini (Ω)', 'R ini'), ('I inicial',))
            pairs_2 = self._linearity_pairs(('R fin (Ω)', 'R fin'), ('I cortoc (A)', 'I cortoc'))
            pairs_3 = self._successful_speed_resistance_ratio_pairs()
            self._draw_linearity_subplot(ax_line_1, pairs_1, 'R inicial [Ω]', 'I inicial [A]', 'I inicial vs R inicial')
            self._draw_linearity_subplot(ax_line_2, pairs_2, 'R final [Ω]', 'I cortoc [A]', 'I cortocircuito vs R final')
            self._draw_linearity_subplot(ax_line_3, pairs_3, 'Ratio R', 'Vel final / Vel nominal', 'Ratio velocidad final vs ratio R')

        if self.history_analysis_mode == 'current':
            current_pairs = self._successful_current_analysis_pairs(nominal_current)
            self._draw_current_analysis_subplot(ax_line_1, current_pairs, nominal_current)

        self._polish_canvas_layout(self.historical_canvas, full_layout=False)

    def _on_history_click(self, event):
        if event.inaxes is None:
            return
        if self.history_area_delete_enabled and getattr(event, 'button', None) in (1, None):
            if event.xdata is not None and event.ydata is not None:
                bounds = self.history_area_selection_bounds
                if bounds is not None:
                    xmin, xmax, ymin, ymax = bounds
                    if xmin <= event.xdata <= xmax and ymin <= event.ydata <= ymax:
                        self.history_hidden_indices.update(self.history_area_selection_indices)
                        self.history_area_selection_bounds = None
                        self.history_area_selection_indices.clear()
                        self.redraw_history()
                        return
                self.history_drag_state = {
                    'inaxes': event.inaxes,
                    'x0': float(event.xdata),
                    'y0': float(event.ydata),
                    'rect': None,
                    'dragging': False,
                }
            return
        if event.dblclick is not True:
            return
        if not hasattr(event.inaxes, '_history_point_indices'):
            return
        if event.xdata is None or event.ydata is None:
            return
        indices = getattr(event.inaxes, '_history_point_indices', [])
        xy = getattr(event.inaxes, '_history_plot_xy', np.empty((0, 2)))
        if not indices:
            return
        if len(xy) != len(indices):
            nearest = int(round(event.xdata))
            nearest = max(0, min(nearest, len(indices) - 1))
        else:
            click_px = np.array([event.x, event.y], dtype=float)
            pts_px = event.inaxes.transData.transform(xy)
            distances = np.linalg.norm(pts_px - click_px, axis=1)
            nearest = int(np.argmin(distances))
            if distances[nearest] > 24:
                return
        self.history_hidden_indices.add(indices[nearest])
        self.redraw_history()

    def _on_history_motion(self, event):
        if not self.history_area_delete_enabled or not self.history_drag_state:
            return
        if event.inaxes is not self.history_drag_state.get('inaxes') or event.xdata is None or event.ydata is None:
            return
        dx = abs(event.xdata - self.history_drag_state['x0'])
        dy = abs(event.ydata - self.history_drag_state['y0'])
        if dx <= 0.12 and dy <= 0.12:
            return
        self.history_drag_state['dragging'] = True
        rect = self.history_drag_state.get('rect')
        if rect is None:
            rect = Rectangle(
                (self.history_drag_state['x0'], self.history_drag_state['y0']),
                0,
                0,
                facecolor='#C62828',
                edgecolor='#C62828',
                linewidth=1.2,
                alpha=0.16,
                zorder=9
            )
            event.inaxes.add_patch(rect)
            self.history_drag_state['rect'] = rect
        rect.set_x(min(self.history_drag_state['x0'], event.xdata))
        rect.set_y(min(self.history_drag_state['y0'], event.ydata))
        rect.set_width(abs(event.xdata - self.history_drag_state['x0']))
        rect.set_height(abs(event.ydata - self.history_drag_state['y0']))
        event.canvas.draw_idle()

    def _on_history_release(self, event):
        drag_state = self.history_drag_state
        self.history_drag_state = None
        if not self.history_area_delete_enabled or not drag_state:
            return
        rect = drag_state.get('rect')
        if rect is not None:
            try:
                rect.remove()
            except Exception:
                pass
        if not drag_state.get('dragging') or event.inaxes is not drag_state.get('inaxes') or event.xdata is None or event.ydata is None:
            return
        xmin = min(drag_state['x0'], float(event.xdata))
        xmax = max(drag_state['x0'], float(event.xdata))
        ymin = min(drag_state['y0'], float(event.ydata))
        ymax = max(drag_state['y0'], float(event.ydata))
        indices = getattr(event.inaxes, '_history_point_indices', [])
        xy = getattr(event.inaxes, '_history_plot_xy', np.empty((0, 2)))
        selected = {
            idx for idx, (x_val, y_val) in zip(indices, xy)
            if xmin <= x_val <= xmax and ymin <= y_val <= ymax
        }
        self.history_area_selection_indices = selected
        self.history_area_selection_bounds = (xmin, xmax, ymin, ymax) if selected else None
        self.redraw_history()

    # ---------- CONDITION MONITORING ----------
    def _build_cm_page(self):
        cm = QWidget()
        self._cm_layout_signature = None
        v = QVBoxLayout(cm)
        v.setContentsMargins(18, 18, 18, 18)
        v.setSpacing(12)

        top = QHBoxLayout()
        top.addWidget(QLabel(self.tr_text('cm_div_left')))
        self.cm_div_left = QSpinBox(); self.cm_div_left.setRange(2, 20); self.cm_div_left.setValue(self.cm_state.get("div_left",6))
        self.cm_div_left.valueChanged.connect(self._cm_on_axes_control_changed)
        top.addWidget(self.cm_div_left)

        top.addWidget(QLabel(self.tr_text('cm_div_right')))
        self.cm_div_right = QSpinBox(); self.cm_div_right.setRange(2, 20); self.cm_div_right.setValue(self.cm_state.get("div_right",6))
        self.cm_div_right.valueChanged.connect(self._cm_on_axes_control_changed)
        top.addWidget(self.cm_div_right)

        self.cm_gridx = QCheckBox(self.tr_text('cm_gridx')); self.cm_gridx.setChecked(self.cm_state.get("gridx", True))
        self.cm_gridx.stateChanged.connect(self._cm_on_axes_control_changed)
        top.addWidget(self.cm_gridx)

        self.cm_second_graph_toggle = QCheckBox(self.tr_text('cm_second_graph'))
        self.cm_second_graph_toggle.setChecked(self.cm_state.get("show_second_graph", False))
        self.cm_second_graph_toggle.stateChanged.connect(self._cm_on_axes_control_changed)
        top.addWidget(self.cm_second_graph_toggle)

        self.cm_restore_btn = QPushButton(self.tr_text('cm_restore'))
        self._style_compact_action_button(self.cm_restore_btn)
        self._fit_button_to_text(self.cm_restore_btn, extra=10, min_width=90)
        self.cm_restore_btn.clicked.connect(self._cm_restore_hidden_points)
        top.addWidget(self.cm_restore_btn)

        self.cm_filter_success_btn = QPushButton(self.tr_text('cm_filter_success'))
        self._style_compact_action_button(self.cm_filter_success_btn)
        self._fit_button_to_text(self.cm_filter_success_btn, extra=10, min_width=90)
        self.cm_filter_success_btn.clicked.connect(self._cm_filter_success_starts)
        top.addWidget(self.cm_filter_success_btn)
        self._cm_update_filter_success_button()
        top.addWidget(self._build_cm_settings_button())

        top.addStretch()
        v.addLayout(top)

        self.cm_main_splitter = QSplitter(Qt.Horizontal)
        self.cm_main_splitter.setChildrenCollapsible(False)

        # Lista de parámetros
        left_panel = QVBoxLayout()
        params_header = QHBoxLayout()
        params_header.addWidget(QLabel(self.tr_text('cm_params1')))
        close_params_btn = QToolButton()
        close_params_btn.setAutoRaise(True)
        self._style_close_toolbutton(close_params_btn)
        close_params_btn.clicked.connect(self._cm_hide_param_selector)
        params_header.addStretch()
        params_header.addWidget(close_params_btn)
        left_panel.addLayout(params_header)
        self.cm_param_list = QListWidget()
        self.cm_param_list.setSelectionMode(QListWidget.MultiSelection)
        self.cm_param_list.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.cm_param_list.setStyleSheet(self._list_style())
        for name in SCALAR_FIELDS:
            it = QListWidgetItem(name)
            it.setFlags(it.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsSelectable)
            it.setCheckState(Qt.Unchecked)
            self.cm_param_list.addItem(it)
            self.cm_axis_map.setdefault(name, 'left')
        self.cm_param_list.itemChanged.connect(self._cm_on_param_item_changed)
        self.cm_param_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.cm_param_list.customContextMenuRequested.connect(self._cm_param_context_menu)
        left_panel.addWidget(self.cm_param_list)

        secondary_header = QHBoxLayout()
        self.cm_param_label_secondary = QLabel(self.tr_text('cm_params2'))
        secondary_header.addWidget(self.cm_param_label_secondary)
        close_params_btn_secondary = QToolButton()
        close_params_btn_secondary.setAutoRaise(True)
        self._style_close_toolbutton(close_params_btn_secondary)
        close_params_btn_secondary.clicked.connect(self._cm_hide_param_selector)
        secondary_header.addStretch()
        secondary_header.addWidget(close_params_btn_secondary)
        left_panel.addLayout(secondary_header)
        self.cm_param_list_secondary = QListWidget()
        self.cm_param_list_secondary.setSelectionMode(QListWidget.MultiSelection)
        self.cm_param_list_secondary.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.cm_param_list_secondary.setStyleSheet(self._list_style())
        for name in SCALAR_FIELDS:
            it = QListWidgetItem(name)
            it.setFlags(it.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsSelectable)
            it.setCheckState(Qt.Unchecked)
            self.cm_param_list_secondary.addItem(it)
        self.cm_param_list_secondary.itemChanged.connect(self._cm_on_param_item_changed)
        self.cm_param_list_secondary.setContextMenuPolicy(Qt.CustomContextMenu)
        self.cm_param_list_secondary.customContextMenuRequested.connect(self._cm_param_context_menu)
        left_panel.addWidget(self.cm_param_list_secondary)
        self.cm_param_label_secondary.setVisible(self.cm_second_graph_toggle.isChecked())
        self.cm_param_list_secondary.setVisible(self.cm_second_graph_toggle.isChecked())

        self.cm_params_panel = QWidget(); self.cm_params_panel.setLayout(left_panel)
        self.cm_params_panel.setStyleSheet(self._panel_style())
        self.cm_params_panel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.cm_main_splitter.addWidget(self.cm_params_panel)

        # Lista de fechas
        mid_panel = QVBoxLayout()
        starts_header = QHBoxLayout()
        starts_header.addWidget(QLabel(self.tr_text('cm_starts')))
        close_starts_btn = QToolButton()
        close_starts_btn.setAutoRaise(True)
        self._style_close_toolbutton(close_starts_btn)
        close_starts_btn.clicked.connect(self._cm_hide_start_selector)
        starts_header.addStretch()
        starts_header.addWidget(close_starts_btn)
        mid_panel.addLayout(starts_header)

        range_row = QHBoxLayout()
        range_row.setSpacing(6)
        range_row.addWidget(QLabel(self.tr_text('cm_starts_from')))
        self.cm_range_start = QDateEdit()
        self.cm_range_start.setCalendarPopup(True)
        self.cm_range_start.setDisplayFormat('yyyy/MM/dd')
        self.cm_range_start.setDate(QDate(2000, 1, 1))
        self.cm_range_start.setMinimumDate(QDate(2000, 1, 1))
        self._style_cm_date_edit(self.cm_range_start)
        range_row.addWidget(self.cm_range_start)
        range_row.addWidget(QLabel(self.tr_text('cm_starts_to')))
        self.cm_range_end = QDateEdit()
        self.cm_range_end.setCalendarPopup(True)
        self.cm_range_end.setDisplayFormat('yyyy/MM/dd')
        self.cm_range_end.setDate(QDate(2000, 1, 1))
        self.cm_range_end.setMinimumDate(QDate(2000, 1, 1))
        self._style_cm_date_edit(self.cm_range_end)
        range_row.addWidget(self.cm_range_end)
        mid_panel.addLayout(range_row)

        range_buttons = QHBoxLayout()
        range_buttons.setSpacing(6)
        btn_apply_range = QPushButton(self.tr_text('cm_apply_range'))
        self._style_cm_selector_button(btn_apply_range, 'secondary')
        self._fit_button_to_text(btn_apply_range, extra=20, min_width=126)
        btn_apply_range.setToolTip('Aplica un filtro por fecha dentro del rango detectado en el CSV.')
        btn_apply_range.clicked.connect(self._cm_apply_date_range_filter)
        btn_clear_range = QPushButton(self.tr_text('cm_clear_range'))
        self._style_cm_selector_button(btn_clear_range, 'secondary')
        self._fit_button_to_text(btn_clear_range, extra=20, min_width=126)
        btn_clear_range.setToolTip('Vuelve a mostrar todos los arranques disponibles del CSV.')
        btn_clear_range.clicked.connect(self._cm_clear_date_range_filter)
        range_buttons.addWidget(btn_apply_range)
        range_buttons.addWidget(btn_clear_range)
        range_buttons.addStretch()
        mid_panel.addLayout(range_buttons)

        self.cm_list = QListWidget()
        self.cm_list.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.cm_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.cm_list.setStyleSheet(self._list_style())
        self._cm_fill_list()
        self._cm_autosize_list()
        self.cm_list.itemChanged.connect(self._cm_on_date_item_changed)
        mid_panel.addWidget(self.cm_list)

        fbtns = QHBoxLayout()
        b_all = QPushButton(self.tr_text('cm_all')); b_none = QPushButton(self.tr_text('cm_none')); b_inv = QPushButton(self.tr_text('cm_invert'))
        b_all.clicked.connect(lambda: self._cm_bulk_check(True))
        b_none.clicked.connect(lambda: self._cm_bulk_check(False))
        b_inv.clicked.connect(self._cm_invert_check)
        button_meta = (
            (b_all, 'Marca todos los arranques visibles del selector.'),
            (b_none, 'Desmarca todos los arranques visibles del selector.'),
            (b_inv, 'Invierte la selecciÃ³n actual del selector de arranques.'),
        )
        for b, tooltip in button_meta:
            self._style_cm_selector_button(b)
            self._fit_button_to_text(b, extra=20, min_width=126)
            b.setToolTip(tooltip)
            fbtns.addWidget(b)
        mid_panel.addLayout(fbtns)

        self.cm_selector_panel = QWidget(); self.cm_selector_panel.setLayout(mid_panel)
        self.cm_selector_panel.setStyleSheet(self._panel_style())
        self.cm_selector_panel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.cm_main_splitter.addWidget(self.cm_selector_panel)

        # Gr?fico
        right_wrap = QWidget()
        right_wrap.setStyleSheet(self._panel_style())
        right = QVBoxLayout(right_wrap)
        right.setContentsMargins(12, 12, 12, 12)
        right.setSpacing(10)
        self.cm_right_splitter = QSplitter(Qt.Vertical)
        self.cm_right_splitter.setChildrenCollapsible(False)

        main_plot_panel = QWidget()
        main_plot_panel.setMinimumHeight(280)
        main_plot_layout = QVBoxLayout(main_plot_panel)
        main_plot_layout.setContentsMargins(0, 0, 0, 0)
        main_plot_layout.setSpacing(8)
        self.cm_canvas = FigureCanvas(Figure())
        self.cm_ax = self.cm_canvas.figure.add_subplot(111)
        self.cm_ax2 = None
        cm_toolbar_main = NavToolbar(self.cm_canvas, self)
        self._style_nav_toolbar(cm_toolbar_main)
        cm_toolbar_main_row = QHBoxLayout()
        cm_toolbar_main_row.setContentsMargins(0, 0, 0, 0)
        cm_toolbar_main_row.setSpacing(6)
        cm_toolbar_main_row.addWidget(cm_toolbar_main)
        self.cm_cursor_info_main = QLabel(self.tr_text('cm_cursor1_default'))
        self.cm_cursor_info_main.setWordWrap(False)
        self.cm_cursor_info_main.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.cm_cursor_info_main.setStyleSheet("font-size: 11px; color: #555555; padding: 0px 8px 0px 4px;")
        cm_toolbar_main_row.addWidget(self.cm_cursor_info_main, 1)
        self.cm_trend_main_btn = QPushButton('Línea de tendencia')
        self._style_cm_toolbar_toggle_button(self.cm_trend_main_btn)
        self._fit_button_to_text(self.cm_trend_main_btn, extra=18, min_width=166)
        self.cm_trend_main_btn.setToolTip('Muestra u oculta una tendencia lineal sobre cada serie visible.')
        self.cm_trend_main_btn.toggled.connect(lambda checked: self._cm_toggle_trendline(self.cm_canvas, checked))
        cm_toolbar_main_row.addWidget(self.cm_trend_main_btn)
        self.cm_line_main_btn = QPushButton('Línea')
        self._style_cm_toolbar_toggle_button(self.cm_line_main_btn)
        self._fit_button_to_text(self.cm_line_main_btn, extra=18, min_width=92)
        self.cm_line_main_btn.setToolTip('Permite marcar dos puntos de la gráfica para unirlos con una recta.')
        self.cm_line_main_btn.toggled.connect(lambda checked: self._cm_toggle_line_mode(self.cm_canvas, checked))
        cm_toolbar_main_row.addWidget(self.cm_line_main_btn)
        self.cm_draw_main_btn = QPushButton('Dibujar')
        self._style_cm_toolbar_toggle_button(self.cm_draw_main_btn)
        self._fit_button_to_text(self.cm_draw_main_btn, extra=18, min_width=100)
        self.cm_draw_main_btn.setToolTip('Permite dibujar libremente sobre la gráfica mientras esté activado.')
        self.cm_draw_main_btn.toggled.connect(lambda checked: self._cm_toggle_draw_mode(self.cm_canvas, checked))
        cm_toolbar_main_row.addWidget(self.cm_draw_main_btn)
        self.cm_expand_main_btn = QPushButton('Ampliar')
        self._style_cm_expand_button(self.cm_expand_main_btn)
        self._fit_button_to_text(self.cm_expand_main_btn, extra=18, min_width=106)
        self.cm_expand_main_btn.setToolTip('Abre la grÃ¡fica principal de Condition Monitoring en pantalla completa.')
        self.cm_expand_main_btn.clicked.connect(lambda: self._open_cm_fullscreen('main'))
        cm_toolbar_main_row.addWidget(self.cm_expand_main_btn)
        main_plot_layout.addLayout(cm_toolbar_main_row)
        self.cm_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_plot_layout.addWidget(self.cm_canvas, 1)
        self.cm_canvas.mpl_connect('button_press_event', self._on_cm_click)
        self.cm_canvas.mpl_connect('motion_notify_event', self._on_cm_motion)
        self.cm_canvas.mpl_connect('button_release_event', self._on_cm_release)
        self.cm_right_splitter.addWidget(main_plot_panel)

        self.cm_secondary_panel = QWidget()
        self.cm_secondary_panel.setMinimumHeight(240)
        secondary_plot_layout = QVBoxLayout(self.cm_secondary_panel)
        secondary_plot_layout.setContentsMargins(0, 0, 0, 0)
        secondary_plot_layout.setSpacing(8)
        self.cm_canvas_secondary = FigureCanvas(Figure())
        self.cm_ax_secondary = self.cm_canvas_secondary.figure.add_subplot(111)
        self.cm_ax_secondary_right = None
        cm_toolbar_secondary = NavToolbar(self.cm_canvas_secondary, self)
        self._style_nav_toolbar(cm_toolbar_secondary)
        cm_toolbar_secondary_row = QHBoxLayout()
        cm_toolbar_secondary_row.setContentsMargins(0, 0, 0, 0)
        cm_toolbar_secondary_row.setSpacing(6)
        cm_toolbar_secondary_row.addWidget(cm_toolbar_secondary)
        self.cm_cursor_info_secondary = QLabel(self.tr_text('cm_cursor2_default'))
        self.cm_cursor_info_secondary.setWordWrap(False)
        self.cm_cursor_info_secondary.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.cm_cursor_info_secondary.setStyleSheet("font-size: 11px; color: #555555; padding: 0px 8px 0px 4px;")
        cm_toolbar_secondary_row.addWidget(self.cm_cursor_info_secondary, 1)
        self.cm_trend_secondary_btn = QPushButton('Línea de tendencia')
        self._style_cm_toolbar_toggle_button(self.cm_trend_secondary_btn)
        self._fit_button_to_text(self.cm_trend_secondary_btn, extra=18, min_width=166)
        self.cm_trend_secondary_btn.setToolTip('Muestra u oculta una tendencia lineal sobre cada serie visible.')
        self.cm_trend_secondary_btn.toggled.connect(lambda checked: self._cm_toggle_trendline(self.cm_canvas_secondary, checked))
        cm_toolbar_secondary_row.addWidget(self.cm_trend_secondary_btn)
        self.cm_line_secondary_btn = QPushButton('Línea')
        self._style_cm_toolbar_toggle_button(self.cm_line_secondary_btn)
        self._fit_button_to_text(self.cm_line_secondary_btn, extra=18, min_width=92)
        self.cm_line_secondary_btn.setToolTip('Permite marcar dos puntos de la gráfica para unirlos con una recta.')
        self.cm_line_secondary_btn.toggled.connect(lambda checked: self._cm_toggle_line_mode(self.cm_canvas_secondary, checked))
        cm_toolbar_secondary_row.addWidget(self.cm_line_secondary_btn)
        self.cm_draw_secondary_btn = QPushButton('Dibujar')
        self._style_cm_toolbar_toggle_button(self.cm_draw_secondary_btn)
        self._fit_button_to_text(self.cm_draw_secondary_btn, extra=18, min_width=100)
        self.cm_draw_secondary_btn.setToolTip('Permite dibujar libremente sobre la gráfica mientras esté activado.')
        self.cm_draw_secondary_btn.toggled.connect(lambda checked: self._cm_toggle_draw_mode(self.cm_canvas_secondary, checked))
        cm_toolbar_secondary_row.addWidget(self.cm_draw_secondary_btn)
        self.cm_expand_secondary_btn = QPushButton('Ampliar')
        self._style_cm_expand_button(self.cm_expand_secondary_btn)
        self._fit_button_to_text(self.cm_expand_secondary_btn, extra=18, min_width=106)
        self.cm_expand_secondary_btn.setToolTip('Abre la grÃ¡fica secundaria de Condition Monitoring en pantalla completa.')
        self.cm_expand_secondary_btn.clicked.connect(lambda: self._open_cm_fullscreen('secondary'))
        cm_toolbar_secondary_row.addWidget(self.cm_expand_secondary_btn)
        secondary_plot_layout.addLayout(cm_toolbar_secondary_row)
        self.cm_canvas_secondary.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        secondary_plot_layout.addWidget(self.cm_canvas_secondary, 1)
        self.cm_canvas_secondary.mpl_connect('button_press_event', self._on_cm_click)
        self.cm_canvas_secondary.mpl_connect('motion_notify_event', self._on_cm_motion)
        self.cm_canvas_secondary.mpl_connect('button_release_event', self._on_cm_release)
        self.cm_right_splitter.addWidget(self.cm_secondary_panel)
        self.cm_right_splitter.setStretchFactor(0, 3)
        self.cm_right_splitter.setStretchFactor(1, 2)
        self.cm_right_splitter.setSizes([520, 320])
        right.addWidget(self.cm_right_splitter, 1)
        self.cm_canvas_secondary.setVisible(self.cm_second_graph_toggle.isChecked())
        self.cm_cursor_info_secondary.setVisible(self.cm_second_graph_toggle.isChecked())
        self.cm_secondary_panel.setVisible(self.cm_second_graph_toggle.isChecked())
        self.cm_main_splitter.addWidget(right_wrap)
        self.cm_main_splitter.setStretchFactor(0, 0)
        self.cm_main_splitter.setStretchFactor(1, 0)
        self.cm_main_splitter.setStretchFactor(2, 1)

        v.addWidget(self.cm_main_splitter, 1)

        self._cm_params_autosize()
        return cm

    def _cm_param_context_menu(self, pos):
        source_list = self.sender()
        if source_list is None:
            return
        item = source_list.itemAt(pos)
        if not item: return

        selected = source_list.selectedItems()
        targets = selected if selected else [item]

        menu = QMenu(source_list)
        act_left  = menu.addAction("Eje izquierdo")
        act_right = menu.addAction("Eje derecho")
        menu.addSeparator()
        act_rename = menu.addAction("Renombrar…")
        menu.addSeparator()
        act_reset = menu.addAction("Valores originales")
        act_mult  = menu.addAction("Multiplicar por…")
        act_div   = menu.addAction("Dividir por…")

        action = menu.exec_(source_list.mapToGlobal(pos))
        if not action: return

        if action == act_left:
            for it in targets:
                self.cm_axis_map[it.text()] = 'left'
            self._schedule_cm_state_save(); self.cm_redraw()

        elif action == act_right:
            for it in targets:
                self.cm_axis_map[it.text()] = 'right'
            self._schedule_cm_state_save(); self.cm_redraw()

        elif action == act_rename:
            from PyQt5.QtWidgets import QInputDialog
            base_item = targets[0]
            current_label = self.cm_label_map.get(base_item.text(), base_item.text())
            new_label, ok = QInputDialog.getText(self, "Renombrar serie", "Nombre:", text=current_label)
            if ok and new_label.strip():
                self.cm_label_map[base_item.text()] = new_label.strip()
                self._schedule_cm_state_save(); self.cm_redraw()

        elif action == act_reset:
            for it in targets:
                self.cm_transform[it.text()] = {'op':'none','k':1.0}
            self._schedule_cm_state_save(); self.cm_redraw()

        elif action in (act_mult, act_div):
            from PyQt5.QtWidgets import QInputDialog
            factor, ok = QInputDialog.getDouble(self, "Factor", "Introduce el valor:",
                                                1.0, -1e12, 1e12, 6)
            if ok:
                for it in targets:
                    name = it.text()
                    if action == act_mult:
                        self.cm_transform[name] = {'op':'mul','k':float(factor)}
                    else:
                        self.cm_transform[name] = {'op':'div','k':float(factor)}
                self._schedule_cm_state_save(); self.cm_redraw()

    def _cm_autosize_list(self):
        if not hasattr(self, 'cm_list') or not self.cm_list: return
        labels = getattr(self, 'start_labels', [])
        fm = self.cm_list.fontMetrics()
        max_text = max((fm.horizontalAdvance(lbl) for lbl in labels), default=150)
        w = min(max(220, max_text + 50), 500)
        self.cm_list.setMinimumWidth(min(w, 320))
        self.cm_list.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

    def _cm_fill_list(self):
        if not hasattr(self, 'cm_list') or self.cm_list is None: return
        self.cm_list.blockSignals(True)
        self.cm_list.clear()
        for label in self.start_labels:
            it = QListWidgetItem(label)
            it.setFlags(it.flags() | Qt.ItemIsUserCheckable)
            # Aplica estado guardado si existe
            checked_default = self.cm_state.get("checked_starts", {}).get(label, True)
            it.setCheckState(Qt.Checked if checked_default else Qt.Unchecked)
            self.cm_list.addItem(it)
        self.cm_list.blockSignals(False)
        self._cm_sync_date_range_controls(reset_to_full_range=True)
        self._cm_autosize_list()

    def _cm_bulk_check(self, checked: bool):
        self.cm_list.blockSignals(True)
        state = Qt.Checked if checked else Qt.Unchecked
        for i in range(self.cm_list.count()):
            self.cm_list.item(i).setCheckState(state)
        self.cm_list.blockSignals(False)
        self._schedule_cm_state_save()
        self.cm_redraw()

    def _cm_invert_check(self):
        self.cm_list.blockSignals(True)
        for i in range(self.cm_list.count()):
            it = self.cm_list.item(i)
            it.setCheckState(Qt.Unchecked if it.checkState()==Qt.Checked else Qt.Checked)
        self.cm_list.blockSignals(False)
        self._schedule_cm_state_save()
        self.cm_redraw()

    def _cm_params_autosize(self):
        if not hasattr(self, 'cm_param_list') or not self.cm_param_list: return
        fm = self.cm_param_list.fontMetrics()
        names = SCALAR_FIELDS
        max_text = max((fm.horizontalAdvance(lbl) for lbl in names), default=140)
        w = min(max(200, max_text + 50), 420)
        self.cm_param_list.setMinimumWidth(min(w, 300))
        self.cm_param_list.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        if getattr(self, 'cm_param_list_secondary', None):
            self.cm_param_list_secondary.setMinimumWidth(min(w, 300))
            self.cm_param_list_secondary.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

    def _cm_on_param_item_changed(self, *args):
        self._schedule_cm_state_save()
        self._schedule_cm_redraw()

    def _cm_on_date_item_changed(self, *args):
        self.cm_success_filter_active = False
        self._cm_update_filter_success_button()
        self._schedule_cm_state_save()
        self._schedule_cm_redraw()

    def _cm_update_filter_success_button(self):
        if getattr(self, 'cm_filter_success_btn', None):
            label_key = 'cm_show_all_starts' if self.cm_success_filter_active else 'cm_filter_success'
            self.cm_filter_success_btn.setText(self.tr_text(label_key))
            self._fit_button_to_text(self.cm_filter_success_btn, extra=10, min_width=108)

    def _cm_on_axes_control_changed(self, *args):
        self._schedule_cm_state_save()
        self._schedule_cm_redraw()

    def _cm_get_area_selection(self, canvas):
        if canvas is self.cm_canvas:
            return self.cm_area_selected_main, self.cm_area_bounds_main
        return self.cm_area_selected_secondary, self.cm_area_bounds_secondary

    def _cm_set_area_selection(self, canvas, indices, bounds):
        if canvas is self.cm_canvas:
            self.cm_area_selected_main = set(indices)
            self.cm_area_bounds_main = bounds
            self.cm_selected_point_main = None
        else:
            self.cm_area_selected_secondary = set(indices)
            self.cm_area_bounds_secondary = bounds
            self.cm_selected_point_secondary = None

    def _cm_clear_area_selection(self, canvas, redraw=False):
        if canvas is self.cm_canvas:
            self.cm_area_selected_main.clear()
            self.cm_area_bounds_main = None
        else:
            self.cm_area_selected_secondary.clear()
            self.cm_area_bounds_secondary = None
        if redraw:
            self.cm_redraw()

    def _cm_canvas_info_label(self, canvas):
        return self.cm_cursor_info_main if canvas is self.cm_canvas else self.cm_cursor_info_secondary

    def _cm_reset_cursor_info(self, canvas):
        label = self._cm_canvas_info_label(canvas)
        if label is not None:
            default_key = 'cm_cursor1_default' if canvas is self.cm_canvas else 'cm_cursor2_default'
            label.setText(self.tr_text(default_key))

    def _cm_trendline_enabled(self, canvas):
        return self.cm_trendline_enabled_main if canvas is self.cm_canvas else self.cm_trendline_enabled_secondary

    def _cm_line_mode_enabled(self, canvas):
        return self.cm_line_mode_main if canvas is self.cm_canvas else self.cm_line_mode_secondary

    def _cm_draw_mode_enabled(self, canvas):
        return self.cm_draw_mode_main if canvas is self.cm_canvas else self.cm_draw_mode_secondary

    def _cm_get_manual_line_store(self, canvas):
        if canvas is self.cm_canvas:
            return self.cm_manual_lines_main, self.cm_line_anchor_main
        return self.cm_manual_lines_secondary, self.cm_line_anchor_secondary

    def _cm_get_freehand_paths(self, canvas):
        return self.cm_freehand_paths_main if canvas is self.cm_canvas else self.cm_freehand_paths_secondary

    def _cm_set_manual_line_anchor(self, canvas, anchor):
        if canvas is self.cm_canvas:
            self.cm_line_anchor_main = anchor
        else:
            self.cm_line_anchor_secondary = anchor

    def _cm_toggle_trendline(self, canvas, checked):
        if canvas is self.cm_canvas:
            self.cm_trendline_enabled_main = bool(checked)
        else:
            self.cm_trendline_enabled_secondary = bool(checked)
        self.cm_redraw()

    def _cm_toggle_line_mode(self, canvas, checked):
        enabled = bool(checked)
        if canvas is self.cm_canvas:
            self.cm_line_mode_main = enabled
            if not enabled:
                self.cm_line_anchor_main = None
        else:
            self.cm_line_mode_secondary = enabled
            if not enabled:
                self.cm_line_anchor_secondary = None
        self.cm_redraw()

    def _cm_toggle_draw_mode(self, canvas, checked):
        enabled = bool(checked)
        if canvas is self.cm_canvas:
            self.cm_draw_mode_main = enabled
        else:
            self.cm_draw_mode_secondary = enabled
        self.cm_redraw()

    def _apply_cm_layout(self, show_second):
        show_params = bool(self.cm_state.get("show_param_selector", True))
        show_selector = bool(self.cm_state.get("show_start_selector", True))
        signature = (show_second, show_params, show_selector)
        if self._cm_layout_signature == signature:
            return
        self._cm_layout_signature = signature
        if self.cm_canvas_secondary:
            self.cm_canvas_secondary.setVisible(show_second)
        if self.cm_cursor_info_secondary:
            self.cm_cursor_info_secondary.setVisible(show_second)
        if self.cm_secondary_panel:
            self.cm_secondary_panel.setVisible(show_second)
        if self.cm_param_label_secondary:
            self.cm_param_label_secondary.setVisible(show_second)
        if self.cm_param_list_secondary:
            self.cm_param_list_secondary.setVisible(show_second)
        if self.cm_params_panel:
            self.cm_params_panel.setVisible(show_params)
        if self.cm_selector_panel:
            self.cm_selector_panel.setVisible(show_selector)
        if self.cm_right_splitter:
            if show_second:
                self.cm_right_splitter.setSizes([520, 320])
            else:
                self.cm_right_splitter.setSizes([1, 0])
        if self.cm_main_splitter:
            if show_params and show_selector:
                self.cm_main_splitter.setSizes([280, 300, 940])
            elif show_params and not show_selector:
                self.cm_main_splitter.setSizes([320, 0, 1200])
            elif not show_params and show_selector:
                self.cm_main_splitter.setSizes([0, 320, 1200])
            else:
                self.cm_main_splitter.setSizes([0, 0, 1520])

    def _cm_find_nearest_candidate(self, event):
        hover_candidates = getattr(event.inaxes, '_cm_hover_candidates', [])
        if not hover_candidates or event.x is None or event.y is None:
            return None, None
        click_px = np.array([event.x, event.y], dtype=float)
        candidate_xy = np.array([[pt[0], pt[1]] for pt in hover_candidates], dtype=float)
        pts_px = event.inaxes.transData.transform(candidate_xy)
        distances = np.linalg.norm(pts_px - click_px, axis=1)
        nearest = int(np.argmin(distances))
        return hover_candidates, (nearest, distances[nearest])

    def _cm_area_contains_event(self, canvas, event):
        _, bounds = self._cm_get_area_selection(canvas)
        if bounds is None or event.xdata is None or event.ydata is None:
            return False
        xmin, xmax, ymin, ymax = bounds
        return xmin <= event.xdata <= xmax and ymin <= event.ydata <= ymax

    def _cm_delete_area_selection(self, canvas):
        self._cm_cancel_pending_selection()
        selected_indices, _ = self._cm_get_area_selection(canvas)
        if not selected_indices:
            return
        self.cm_hidden_indices.update(selected_indices)
        self._cm_clear_area_selection(canvas, redraw=False)
        if canvas is self.cm_canvas:
            self.cm_selected_point_main = None
        else:
            self.cm_selected_point_secondary = None
        self._cm_reset_cursor_info(canvas)
        self.cm_redraw()

    def _cm_delete_selected_point(self, canvas):
        self._cm_cancel_pending_selection()
        selected_point = self.cm_selected_point_main if canvas is self.cm_canvas else self.cm_selected_point_secondary
        if selected_point is None:
            return False
        start_idx, _ = selected_point
        self.cm_hidden_indices.add(start_idx)
        if canvas is self.cm_canvas:
            self.cm_selected_point_main = None
        else:
            self.cm_selected_point_secondary = None
        self._cm_reset_cursor_info(canvas)
        self.cm_redraw()
        return True

    def _cm_cancel_pending_selection(self):
        if self._cm_single_click_timer.isActive():
            self._cm_single_click_timer.stop()
        self.cm_pending_selection = None

    def _commit_cm_single_click(self):
        pending = self.cm_pending_selection
        self.cm_pending_selection = None
        if not pending:
            return
        canvas = pending.get('canvas')
        start_idx = pending.get('start_idx')
        selected_payload = pending.get('selected_payload')
        if canvas is self.cm_canvas:
            self.cm_selected_point_main = selected_payload
        elif canvas is self.cm_canvas_secondary:
            self.cm_selected_point_secondary = selected_payload
        if self.cm_state.get("show_click_date", True):
            text = f"<b>{self.tr_text('cm_selected_date', date=self._cm_point_label(start_idx))}</b>"
            label = self._cm_canvas_info_label(canvas)
            if label is not None:
                label.setText(text)
        self.cm_redraw()

    def _open_cm_fullscreen(self, which='main'):
        show_secondary = bool(self.cm_second_graph_toggle and self.cm_second_graph_toggle.isChecked())
        if which == 'secondary' and not show_secondary:
            return
        sel_idx = self._cm_selected_indices()
        if which == 'main':
            params = self._cm_selected_params(self.cm_param_list)
            title = summarize_plot_title(params)
            selected_point = self.cm_selected_point_main
            trend_enabled = self.cm_trendline_enabled_main
            manual_lines = list(self.cm_manual_lines_main)
            line_anchor = self.cm_line_anchor_main
            freehand_paths = [list(path) for path in self.cm_freehand_paths_main]
            area_selected = set(self.cm_area_selected_main)
            area_bounds = self.cm_area_bounds_main
            dialog_title = 'Condition Monitoring - Gráfica principal'
        else:
            params = self._cm_selected_params(self.cm_param_list_secondary)
            title = summarize_plot_title(params)
            selected_point = self.cm_selected_point_secondary
            trend_enabled = self.cm_trendline_enabled_secondary
            manual_lines = list(self.cm_manual_lines_secondary)
            line_anchor = self.cm_line_anchor_secondary
            freehand_paths = [list(path) for path in self.cm_freehand_paths_secondary]
            area_selected = set(self.cm_area_selected_secondary)
            area_bounds = self.cm_area_bounds_secondary
            dialog_title = 'Condition Monitoring - Gráfica secundaria'

        dialog = QDialog(self)
        dialog.setAttribute(Qt.WA_DeleteOnClose, True)
        dialog.setWindowTitle(dialog_title)
        dialog.resize(1440, 900)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        canvas = FigureCanvas(Figure())
        ax = canvas.figure.add_subplot(111)
        toolbar = NavToolbar(canvas, dialog)
        self._style_nav_toolbar(toolbar)
        toolbar_row = QHBoxLayout()
        toolbar_row.setContentsMargins(0, 0, 0, 0)
        toolbar_row.addWidget(toolbar)
        toolbar_row.addStretch()
        layout.addLayout(toolbar_row)
        layout.addWidget(canvas, 1)

        twin_attr = '_cm_fullscreen_main_right' if which == 'main' else '_cm_fullscreen_secondary_right'
        marker_name = '_cm_fullscreen_main_points' if which == 'main' else '_cm_fullscreen_secondary_points'
        self._cm_draw_group(
            ax, twin_attr, canvas, sel_idx, params, title, marker_name,
            selected_point=selected_point,
            trend_enabled=trend_enabled,
            manual_lines=manual_lines,
            line_anchor=line_anchor,
            area_selected=area_selected,
            area_bounds=area_bounds,
            freehand_paths=freehand_paths,
        )
        self._cm_fullscreen_dialogs.append(dialog)
        dialog.destroyed.connect(lambda *_: self._cm_fullscreen_dialogs.remove(dialog) if dialog in self._cm_fullscreen_dialogs else None)
        dialog.showMaximized()

    def _cm_restore_hidden_points(self):
        self.cm_hidden_indices.clear()
        self.cm_success_filter_active = False
        if self.cm_list:
            self.cm_list.blockSignals(True)
            for i in range(self.cm_list.count()):
                self.cm_list.item(i).setCheckState(Qt.Checked)
            self.cm_list.blockSignals(False)
        self._cm_cancel_pending_selection()
        self.cm_selected_point_main = None
        self.cm_selected_point_secondary = None
        self.cm_area_selected_main.clear()
        self.cm_area_selected_secondary.clear()
        self.cm_area_bounds_main = None
        self.cm_area_bounds_secondary = None
        self.cm_line_anchor_main = None
        self.cm_line_anchor_secondary = None
        self.cm_manual_lines_main.clear()
        self.cm_manual_lines_secondary.clear()
        self.cm_freehand_paths_main.clear()
        self.cm_freehand_paths_secondary.clear()
        self.cm_trendline_enabled_main = False
        self.cm_trendline_enabled_secondary = False
        self.cm_line_mode_main = False
        self.cm_line_mode_secondary = False
        self.cm_draw_mode_main = False
        self.cm_draw_mode_secondary = False
        if getattr(self, 'cm_trend_main_btn', None):
            self.cm_trend_main_btn.blockSignals(True)
            self.cm_trend_main_btn.setChecked(False)
            self.cm_trend_main_btn.blockSignals(False)
        if getattr(self, 'cm_trend_secondary_btn', None):
            self.cm_trend_secondary_btn.blockSignals(True)
            self.cm_trend_secondary_btn.setChecked(False)
            self.cm_trend_secondary_btn.blockSignals(False)
        if getattr(self, 'cm_line_main_btn', None):
            self.cm_line_main_btn.blockSignals(True)
            self.cm_line_main_btn.setChecked(False)
            self.cm_line_main_btn.blockSignals(False)
        if getattr(self, 'cm_line_secondary_btn', None):
            self.cm_line_secondary_btn.blockSignals(True)
            self.cm_line_secondary_btn.setChecked(False)
            self.cm_line_secondary_btn.blockSignals(False)
        if getattr(self, 'cm_draw_main_btn', None):
            self.cm_draw_main_btn.blockSignals(True)
            self.cm_draw_main_btn.setChecked(False)
            self.cm_draw_main_btn.blockSignals(False)
        if getattr(self, 'cm_draw_secondary_btn', None):
            self.cm_draw_secondary_btn.blockSignals(True)
            self.cm_draw_secondary_btn.setChecked(False)
            self.cm_draw_secondary_btn.blockSignals(False)
        self._cm_reset_cursor_info(self.cm_canvas)
        if getattr(self, 'cm_canvas_secondary', None):
            self._cm_reset_cursor_info(self.cm_canvas_secondary)
        self._cm_update_filter_success_button()
        self._schedule_cm_state_save()
        self.cm_redraw()

    def _cm_filter_success_starts(self):
        if not self.cm_list:
            return
        self.cm_list.blockSignals(True)
        if self.cm_success_filter_active:
            for i in range(self.cm_list.count()):
                self.cm_list.item(i).setCheckState(Qt.Checked)
            self.cm_success_filter_active = False
        else:
            for i in range(self.cm_list.count()):
                keep = self._is_successful_start(self.starts[i])
                self.cm_list.item(i).setCheckState(Qt.Checked if keep else Qt.Unchecked)
            self.cm_success_filter_active = True
        self.cm_list.blockSignals(False)
        self._cm_update_filter_success_button()
        self._schedule_cm_state_save()
        self.cm_redraw()

    def cm_transform_to_dict(self):
        # Ya está en formato serializable
        return self.cm_transform if hasattr(self, 'cm_transform') else {}

    def cm_transform_from_dict(self, dct):
        self.cm_transform = {}
        for p, t in (dct or {}).items():
            op = t.get('op','none'); k = float(t.get('k', 1.0))
            if op not in ('none','mul','div'): op = 'none'
            self.cm_transform[p] = {'op': op, 'k': k}

    def _cm_apply_transform(self, param_name, value):
        try:
            v = float(value)
        except Exception:
            return np.nan
        t = (self.cm_transform or {}).get(param_name, {'op':'none','k':1.0})
        op = t.get('op','none'); k = float(t.get('k',1.0))
        try:
            if op == 'mul':
                return v * k
            elif op == 'div':
                return v / k if k != 0 else float('nan')
            else:
                return v
        except Exception:
            return np.nan

    def _cm_selected_indices(self):
        selected = [i for i in range(self.cm_list.count()) if self.cm_list.item(i).checkState()==Qt.Checked]
        return [i for i in selected if i not in self.cm_hidden_indices]

    def _cm_point_label(self, start_idx):
        dt = self.starts[start_idx].get('timestamp_dt')
        if dt is not None:
            return dt.strftime('%Y/%m/%d %H:%M:%S')
        return self.start_labels[start_idx]

    def _cm_axis_labels(self, sel_idx):
        show_full_dates = bool(self.cm_state.get("show_full_dates", True))
        month_names = {
            'es': ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'],
            'en': ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'],
        }
        labels = []
        last_month_key = None
        last_year = None
        for idx in sel_idx:
            dt = self.starts[idx].get('timestamp_dt')
            if dt is None:
                labels.append(self.start_labels[idx])
                continue
            if show_full_dates:
                labels.append(dt.strftime('%Y/%m/%d'))
            else:
                month_key = (dt.year, dt.month)
                if month_key != last_month_key:
                    month_label = month_names.get(self.language, month_names['es'])[dt.month - 1]
                    if last_year is None or dt.year != last_year:
                        month_label = f"{month_label}\n{dt.year}"
                    labels.append(month_label)
                    last_month_key = month_key
                    last_year = dt.year
                else:
                    labels.append('')
        return labels

    def _cm_selected_params(self, list_widget):
        selected = []
        if not list_widget:
            return selected
        for i in range(list_widget.count()):
            it = list_widget.item(i)
            if it.checkState() == Qt.Checked:
                selected.append(it.text())
        return selected

    def _cm_prepare_axis(self, ax, twin_attr):
        ax.clear()
        for attr in ('_cm_point_indices', '_cm_series_values', '_cm_hover_xy', '_cm_hover_line', '_cm_hover_artist', '_cm_hover_candidates'):
            setattr(ax, attr, [] if attr.endswith('indices') or attr.endswith('candidates') else None)
        twin = getattr(self, twin_attr, None)
        if twin is not None:
            try:
                twin.remove()
            except Exception:
                pass
            setattr(self, twin_attr, None)

    def _cm_draw_group(self, ax, twin_attr, canvas, sel_idx, params, title, marker_store_name, selected_point=None, trend_enabled=None, manual_lines=None, line_anchor=None, area_selected=None, area_bounds=None, freehand_paths=None):
        self._cm_prepare_axis(ax, twin_attr)
        if not sel_idx or not params:
            ax._cm_point_indices = []
            ax._cm_series_values = {}
            ax._cm_hover_xy = np.empty((0, 2))
            ax._cm_hover_line = None
            ax._cm_hover_artist = None
            ax.set_title(title, fontsize=12, fontweight='bold')
            self._adjust_cm_figure_layout(canvas, has_right_axis=False)
            self._polish_canvas_layout(canvas)
            return

        use_right = any(self.cm_axis_map.get(p, 'left') == 'right' for p in params)
        if use_right:
            setattr(self, twin_attr, ax.twinx())
        ax2 = getattr(self, twin_attr, None)

        x = np.arange(len(sel_idx))
        ax.set_xticks(x)
        show_full_dates = bool(self.cm_state.get("show_full_dates", True))
        ax.set_xticklabels(
            self._cm_axis_labels(sel_idx),
            rotation=45 if show_full_dates else 36,
            ha='right' if show_full_dates else 'right'
        )
        ax.tick_params(axis='x', labelsize=8 if (show_full_dates or len(sel_idx) > 10) else 8, pad=6 if show_full_dates else 1)
        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.grid(True, axis='y')
        ax.grid(bool(self.cm_gridx.isChecked()), axis='x')
        ax._cm_point_indices = sel_idx
        ax._cm_cursor_line = None
        can_add_hover = canvas.width() > 10 and canvas.height() > 10
        if can_add_hover:
            try:
                ax._cm_cursor_line = ax.axvline(0, color='#444444', linestyle='--', alpha=0.18, visible=False)
            except Exception:
                ax._cm_cursor_line = None

        try:
            ax.yaxis.set_major_locator(MaxNLocator(nbins=self.cm_div_left.value() if self.cm_div_left else 6, prune=None))
        except Exception:
            pass
        if ax2 is not None:
            try:
                ax2.yaxis.set_major_locator(MaxNLocator(nbins=self.cm_div_right.value() if self.cm_div_right else 6, prune=None))
            except Exception:
                pass

        import itertools
        colors = itertools.cycle(['#1f77b4','#ff7f0e','#2ca02c','#d62728','#9467bd','#8c564b','#e377c2','#7f7f7f','#bcbd22','#17becf'])
        handles = []
        labels = []
        point_map = {}
        series_values = {}
        left_values = []
        right_values = []
        hover_candidates = []
        line_records = []
        if trend_enabled is None:
            trend_enabled = self._cm_trendline_enabled(canvas) if canvas in (self.cm_canvas, self.cm_canvas_secondary) else False

        for p in params:
            y = [self._cm_apply_transform(p, self.starts_scalars[i].get(p, np.nan)) for i in sel_idx]
            c = next(colors)
            axis_name = self.cm_axis_map.get(p, 'left')
            lbl = self.cm_label_map.get(p, p)
            target_ax = ax2 if axis_name == 'right' and ax2 is not None else ax
            line, = target_ax.plot(x, y, marker='o', linestyle='-', color=c, label=lbl, picker=6)
            handles.append(line)
            labels.append(lbl)
            point_map[line] = sel_idx
            series_values[lbl] = y
            line_records.append((target_ax, np.asarray(x, dtype=float), np.asarray(y, dtype=float), c))
            finite_values = [v for v in y if not np.isnan(v)]
            for x_val, y_val, start_idx in zip(x, y, sel_idx):
                if not np.isnan(y_val):
                    hover_candidates.append((x_val, y_val, start_idx))
            if target_ax is ax2:
                right_values.extend(finite_values)
            else:
                left_values.extend(finite_values)

        if trend_enabled:
            for target_ax, x_vals, y_vals, color in line_records:
                finite_mask = np.isfinite(x_vals) & np.isfinite(y_vals)
                if np.count_nonzero(finite_mask) < 2:
                    continue
                coeffs = np.polyfit(x_vals[finite_mask], y_vals[finite_mask], 1)
                y_fit = np.polyval(coeffs, x_vals[finite_mask])
                target_ax.plot(
                    x_vals[finite_mask],
                    y_fit,
                    linestyle='--',
                    linewidth=1.5,
                    color=color,
                    alpha=0.72,
                    zorder=4
                )

        legend_ax = ax2 if ax2 is not None else ax
        legend_ax.legend(handles, labels, loc='upper left', fontsize=8, frameon=True)
        shared_axes = [ax] + ([ax2] if ax2 is not None else [])
        hover_line = None
        hover_artist = None
        if can_add_hover:
            try:
                hover_line = ax.axvline(0, color='#444444', linestyle='--', alpha=0.18, visible=False)
                hover_artist = ax.scatter([], [], s=90, facecolors='none', edgecolors='#2F5D8A', linewidths=1.3, zorder=6, visible=False)
            except Exception:
                hover_line = None
                hover_artist = None
        for shared_ax in shared_axes:
            shared_ax._cm_line_indices = point_map
            shared_ax._cm_series_values = series_values
            shared_ax._cm_hover_candidates = hover_candidates
            shared_ax._cm_point_indices = sel_idx
            shared_ax._cm_hover_line = hover_line
            shared_ax._cm_hover_artist = hover_artist

        if selected_point is None:
            selected_point = self.cm_selected_point_main if canvas is self.cm_canvas else self.cm_selected_point_secondary
        if area_selected is None and area_bounds is None:
            area_selected, area_bounds = self._cm_get_area_selection(canvas) if canvas in (self.cm_canvas, self.cm_canvas_secondary) else (set(), None)
        if area_selected:
            selected_candidates = [pt for pt in hover_candidates if pt[2] in area_selected]
            if selected_candidates:
                ax.scatter(
                    [pt[0] for pt in selected_candidates],
                    [pt[1] for pt in selected_candidates],
                    s=88,
                    color='#C62828',
                    edgecolors='white',
                    linewidths=1.1,
                    zorder=7
                )
        if selected_point is not None:
            selected_idx, selected_y = selected_point
            matching_candidates = [pt for pt in hover_candidates if pt[2] == selected_idx]
            if matching_candidates:
                best_match = min(matching_candidates, key=lambda pt: abs(pt[1] - selected_y))
                ax.scatter([best_match[0]], [best_match[1]], s=92, color='#C62828', edgecolors='white', linewidths=1.3, zorder=8)
        if area_bounds is not None:
            xmin, xmax, ymin, ymax = area_bounds
            rect = Rectangle(
                (xmin, ymin),
                xmax - xmin,
                ymax - ymin,
                facecolor='#C62828',
                edgecolor='#C62828',
                linewidth=1.4,
                alpha=0.16,
                zorder=5
            )
            ax.add_patch(rect)
        if manual_lines is None and line_anchor is None:
            manual_lines, line_anchor = self._cm_get_manual_line_store(canvas) if canvas in (self.cm_canvas, self.cm_canvas_secondary) else ([], None)
        if freehand_paths is None:
            freehand_paths = self._cm_get_freehand_paths(canvas) if canvas in (self.cm_canvas, self.cm_canvas_secondary) else []
        if manual_lines:
            for (x0, y0), (x1, y1) in manual_lines:
                ax.plot([x0, x1], [y0, y1], color='#C62828', linewidth=1.6, alpha=0.9, zorder=6)
        if freehand_paths:
            for path in freehand_paths:
                if len(path) < 2:
                    continue
                xs = [pt[0] for pt in path]
                ys = [pt[1] for pt in path]
                ax.plot(xs, ys, color='#C62828', linewidth=1.4, alpha=0.85, zorder=6)
        if line_anchor is not None:
            x0, y0 = line_anchor
            ax.scatter([x0], [y0], s=95, facecolors='#EC6E00', edgecolors='white', linewidths=1.2, zorder=8)

        setattr(self, marker_store_name, point_map)

        left_params = [p for p in params if self.cm_axis_map.get(p, 'left') != 'right']
        ax.set_ylabel(infer_axis_label(left_params) if left_params else 'Eje izquierdo')
        if ax2 is not None:
            ax2.set_ylabel('Eje derecho')

        if left_values:
            ymin = min(left_values)
            ymax = max(left_values)
            if ymin == ymax:
                margin = max(abs(ymin) * 0.1, 1.0)
            else:
                margin = (ymax - ymin) * 0.12
            ax.set_ylim(ymin - margin, ymax + margin)
        else:
            ax.autoscale(enable=True, axis='y', tight=False)

        if ax2 is not None and right_values:
            ymin = min(right_values)
            ymax = max(right_values)
            if ymin == ymax:
                margin = max(abs(ymin) * 0.1, 1.0)
            else:
                margin = (ymax - ymin) * 0.12
            ax2.set_ylim(ymin - margin, ymax + margin)
        elif ax2 is not None:
            ax2.autoscale(enable=True, axis='y', tight=False)

        try:
            ax.xaxis.set_minor_locator(MultipleLocator(0.5))
            ax.grid(True, which='minor', axis='x', alpha=0.25)
        except Exception:
            pass
        self._adjust_cm_figure_layout(canvas, has_right_axis=ax2 is not None)
        self._polish_canvas_layout(canvas, full_layout=False)

    def cm_redraw(self):
        if not self.starts or not self.starts_scalars or not getattr(self, 'cm_list', None) or not getattr(self, 'cm_param_list', None):
            return

        sel_idx = self._cm_selected_indices()
        main_params = self._cm_selected_params(self.cm_param_list)
        secondary_params = self._cm_selected_params(self.cm_param_list_secondary)
        show_second = self.cm_second_graph_toggle.isChecked() if self.cm_second_graph_toggle else False
        self._apply_cm_layout(show_second)
        if not show_second:
            secondary_params = []

        main_title = summarize_plot_title(main_params)
        self._cm_draw_group(self.cm_ax, 'cm_ax2', self.cm_canvas, sel_idx, main_params, main_title, '_cm_main_points')

        if self.cm_canvas_secondary:
            secondary_title = summarize_plot_title(secondary_params)
            self._cm_draw_group(self.cm_ax_secondary, 'cm_ax_secondary_right', self.cm_canvas_secondary, sel_idx, secondary_params, secondary_title, '_cm_secondary_points')
            if not show_second:
                self.cm_ax_secondary.clear()
                self._polish_canvas_layout(self.cm_canvas_secondary, full_layout=False)

    def _on_cm_click(self, event):
        if event.inaxes is None or event.xdata is None or event.ydata is None:
            return
        if getattr(event, 'button', None) not in (1, None):
            return
        self._cm_cancel_pending_selection()
        if self._cm_draw_mode_enabled(event.canvas):
            self.cm_drag_state = {
                'canvas': event.canvas,
                'inaxes': event.inaxes,
                'mode': 'draw',
                'path': [(float(event.xdata), float(event.ydata))],
                'artist': None,
            }
            return
        if self.cm_state.get("enable_area_selection", True) and self._cm_area_contains_event(event.canvas, event):
            self.cm_skip_release_canvas = event.canvas
            self._cm_delete_area_selection(event.canvas)
            return
        hover_candidates, nearest_info = self._cm_find_nearest_candidate(event)
        if hover_candidates is None:
            return
        nearest, nearest_distance = nearest_info
        start_idx = hover_candidates[nearest][2]
        selected_payload = (start_idx, hover_candidates[nearest][1])
        if event.dblclick is True:
            if nearest_distance > 24:
                return
            if not self.cm_state.get("enable_double_click_delete", True):
                return
            self.cm_skip_release_canvas = event.canvas
            self.cm_hidden_indices.add(start_idx)
            if event.canvas is self.cm_canvas:
                self.cm_selected_point_main = None
            elif event.canvas is self.cm_canvas_secondary:
                self.cm_selected_point_secondary = None
            self.cm_redraw()
            return
        self.cm_drag_state = {
            'canvas': event.canvas,
            'inaxes': event.inaxes,
            'mode': 'area',
            'x0': float(event.xdata),
            'y0': float(event.ydata),
            'dragging': False,
            'rect': None,
            'selected_payload': selected_payload,
            'nearest_distance': nearest_distance,
        }

    def _on_cm_motion(self, event):
        if self.cm_drag_state and event.canvas is self.cm_drag_state.get('canvas') and event.inaxes is self.cm_drag_state.get('inaxes'):
            if self.cm_drag_state.get('mode') == 'draw':
                if event.xdata is not None and event.ydata is not None:
                    new_point = (float(event.xdata), float(event.ydata))
                    last_point = self.cm_drag_state['path'][-1]
                    if abs(new_point[0] - last_point[0]) < 0.08 and abs(new_point[1] - last_point[1]) < 0.08:
                        return
                    self.cm_drag_state['path'].append(new_point)
                    artist = self.cm_drag_state.get('artist')
                    xs = [pt[0] for pt in self.cm_drag_state['path']]
                    ys = [pt[1] for pt in self.cm_drag_state['path']]
                    if artist is None:
                        artist, = event.inaxes.plot(xs, ys, color='#C62828', linewidth=1.4, alpha=0.85, zorder=9)
                        self.cm_drag_state['artist'] = artist
                    else:
                        artist.set_data(xs, ys)
                    event.canvas.draw_idle()
                return
            if self.cm_state.get("enable_area_selection", True) and event.xdata is not None and event.ydata is not None:
                dx = abs(event.xdata - self.cm_drag_state['x0'])
                dy = abs(event.ydata - self.cm_drag_state['y0'])
                if dx > 0.12 or dy > 0.12:
                    self.cm_drag_state['dragging'] = True
                    rect = self.cm_drag_state.get('rect')
                    if rect is None:
                        rect = Rectangle(
                            (self.cm_drag_state['x0'], self.cm_drag_state['y0']),
                            0,
                            0,
                            facecolor='#C62828',
                            edgecolor='#C62828',
                            linewidth=1.2,
                            alpha=0.16,
                            zorder=9
                        )
                        event.inaxes.add_patch(rect)
                        self.cm_drag_state['rect'] = rect
                    rect.set_x(min(self.cm_drag_state['x0'], event.xdata))
                    rect.set_y(min(self.cm_drag_state['y0'], event.ydata))
                    rect.set_width(abs(event.xdata - self.cm_drag_state['x0']))
                    rect.set_height(abs(event.ydata - self.cm_drag_state['y0']))
                    event.canvas.draw_idle()
                    return
        if event.inaxes is None or event.xdata is None or event.ydata is None:
            return
        hover_candidates, nearest_info = self._cm_find_nearest_candidate(event)
        if hover_candidates is None:
            return
        nearest, nearest_distance = nearest_info
        hover_line = getattr(event.inaxes, '_cm_hover_line', None)
        hover_artist = getattr(event.inaxes, '_cm_hover_artist', None)
        if nearest_distance > 24:
            if hover_line is not None:
                hover_line.set_visible(False)
            if hover_artist is not None:
                hover_artist.set_visible(False)
            if event.canvas is self.cm_canvas:
                self.cm_canvas.draw_idle()
            elif event.canvas is self.cm_canvas_secondary:
                self.cm_canvas_secondary.draw_idle()
            return

        x_val, y_val, start_idx = hover_candidates[nearest]
        selected_point = self.cm_selected_point_main if event.canvas is self.cm_canvas else self.cm_selected_point_secondary
        area_selected, _ = self._cm_get_area_selection(event.canvas)
        if selected_point is not None or area_selected:
            return
        label = self.start_labels[start_idx]
        series_values = getattr(event.inaxes, '_cm_series_values', {})
        parts = [f"Arranque: {label}"]
        for name, values in list(series_values.items())[:4]:
            line_indices = getattr(event.inaxes, '_cm_point_indices', [])
            if start_idx in line_indices:
                value_idx = line_indices.index(start_idx)
                if value_idx < len(values):
                    value = values[value_idx]
                    if not np.isnan(value):
                        parts.append(f"{name}: {value:.2f}")
        text = " | ".join(parts)
        if hover_line is not None:
            hover_line.set_xdata([x_val, x_val])
            hover_line.set_visible(True)
        if hover_artist is not None:
            hover_artist.set_offsets([[x_val, y_val]])
            hover_artist.set_visible(True)
        if event.canvas is self.cm_canvas and self.cm_cursor_info_main:
            self.cm_cursor_info_main.setText(self.tr_text('cm_cursor1_prefix', text=text))
            self.cm_canvas.draw_idle()
        elif event.canvas is self.cm_canvas_secondary and self.cm_cursor_info_secondary:
            self.cm_cursor_info_secondary.setText(self.tr_text('cm_cursor2_prefix', text=text))
            self.cm_canvas_secondary.draw_idle()

    def _on_cm_release(self, event):
        drag_state = self.cm_drag_state
        self.cm_drag_state = None
        if self.cm_skip_release_canvas is not None and event.canvas is self.cm_skip_release_canvas:
            self.cm_skip_release_canvas = None
            return
        if not drag_state or event.canvas is not drag_state.get('canvas'):
            return
        if drag_state.get('mode') == 'draw':
            artist = drag_state.get('artist')
            if artist is not None:
                try:
                    artist.remove()
                except Exception:
                    pass
            path = list(drag_state.get('path', []))
            if len(path) > 1:
                self._cm_get_freehand_paths(event.canvas).append(path)
                self.cm_redraw()
            return
        rect = drag_state.get('rect')
        if rect is not None:
            try:
                rect.remove()
            except Exception:
                pass
        if drag_state.get('dragging') and event.inaxes is drag_state.get('inaxes') and event.xdata is not None and event.ydata is not None:
            xmin = min(drag_state['x0'], float(event.xdata))
            xmax = max(drag_state['x0'], float(event.xdata))
            ymin = min(drag_state['y0'], float(event.ydata))
            ymax = max(drag_state['y0'], float(event.ydata))
            selected_indices = {
                start_idx for x_val, y_val, start_idx in getattr(event.inaxes, '_cm_hover_candidates', [])
                if xmin <= x_val <= xmax and ymin <= y_val <= ymax
            }
            self._cm_set_area_selection(event.canvas, selected_indices, (xmin, xmax, ymin, ymax) if selected_indices else None)
            self._cm_reset_cursor_info(event.canvas)
            self.cm_redraw()
            return
        if event.inaxes is None or event.xdata is None or event.ydata is None:
            return
        if self.cm_state.get("enable_area_selection", True):
            selected_indices, bounds = self._cm_get_area_selection(event.canvas)
            if selected_indices and bounds is not None and not self._cm_area_contains_event(event.canvas, event):
                self._cm_clear_area_selection(event.canvas, redraw=True)
                self._cm_reset_cursor_info(event.canvas)
                return
        if self._cm_line_mode_enabled(event.canvas):
            manual_lines, line_anchor = self._cm_get_manual_line_store(event.canvas)
            if line_anchor is None:
                self._cm_set_manual_line_anchor(event.canvas, (float(event.xdata), float(event.ydata)))
            else:
                x0, y0 = line_anchor
                x1, y1 = float(event.xdata), float(event.ydata)
                if (abs(x0 - x1) > 1e-9) or (abs(y0 - y1) > 1e-9):
                    manual_lines.append(((x0, y0), (x1, y1)))
                self._cm_set_manual_line_anchor(event.canvas, None)
            self._cm_clear_area_selection(event.canvas, redraw=False)
            self.cm_redraw()
            return
        hover_candidates, nearest_info = self._cm_find_nearest_candidate(event)
        if hover_candidates is None:
            return
        nearest, nearest_distance = nearest_info
        if nearest_distance > 24:
            return
        start_idx = hover_candidates[nearest][2]
        selected_payload = drag_state.get('selected_payload', (start_idx, hover_candidates[nearest][1]))
        self._cm_clear_area_selection(event.canvas, redraw=False)
        self.cm_pending_selection = {
            'canvas': event.canvas,
            'start_idx': start_idx,
            'selected_payload': selected_payload,
        }
        self._cm_single_click_timer.start(220)

    # ---------- CSV LOADING & TABS ----------
    def load_csv(self):
        file,_ = QFileDialog.getOpenFileName(self, 'Seleccionar CSV', '', 'CSV Files (*.csv)')
        if not file:
            return
        self.begin_csv_load(file)

    def begin_csv_load(self, file_path):
        if self._load_thread is not None and self._load_thread.isRunning():
            return
        self._cm_save_state()
        self.statusBar().showMessage(self.tr_text('loading_csv', name=os.path.basename(file_path)))
        self.btn_load_csv.setEnabled(False)
        self._load_thread = QThread(self)
        self._load_worker = CsvLoadWorker(self, file_path)
        self._load_worker.moveToThread(self._load_thread)
        self._load_thread.started.connect(self._load_worker.run)
        self._load_worker.finished.connect(self._on_csv_loaded)
        self._load_worker.finished.connect(self._load_thread.quit)
        self._load_worker.finished.connect(self._load_worker.deleteLater)
        self._load_thread.finished.connect(self._load_thread.deleteLater)
        self._load_thread.start()

    def _on_csv_loaded(self, csv_mode, view_mode, records, file_path, error_text):
        self.btn_load_csv.setEnabled(True)
        self._load_thread = None
        self._load_worker = None
        if error_text:
            self.statusBar().showMessage(self.tr_text('load_error'))
            QMessageBox.warning(self, 'Error de carga', error_text)
            return
        self.csv_mode = csv_mode
        self.current_view_mode = view_mode
        self.current_file = file_path
        self.all_starts = records
        self.history_hidden_indices.clear()
        self.cm_hidden_indices.clear()
        self.apply_current_filters(reset_selection=True)
        self.statusBar().showMessage(self.tr_text('status_loaded', name=os.path.basename(file_path), count=len(self.starts), mode=view_mode))

    def _record_matches_filter(self, record):
        success_mode = self.current_filter.get('success_mode', 'Todos')
        if success_mode == 'Solo exitosos' and not self._is_successful_start(record):
            return False
        if success_mode == 'Solo fallidos' and self._is_successful_start(record):
            return False

        protection = self.current_filter.get('protection', 'Todas')
        if protection != 'Todas' and str(record.get('protection', '')) != protection:
            return False

        start_type = self.current_filter.get('start_type', 'Todos')
        if start_type != 'Todos' and str(record.get('start_type', '')) != start_type:
            return False

        dt = record.get('timestamp_dt')
        date_from = self.current_filter.get('date_from')
        date_to = self.current_filter.get('date_to')
        if date_from and (dt is None or dt.date() < date_from):
            return False
        if date_to and (dt is None or dt.date() > date_to):
            return False
        return True

    def apply_current_filters(self, reset_selection=False):
        filtered = [record for record in self.all_starts if self._record_matches_filter(record)]
        if not filtered:
            QMessageBox.information(self, 'Sin datos', 'Los filtros actuales no dejan arranques visibles.')
            return
        self.starts = filtered
        self.start_labels = [record['label'] for record in filtered]
        self.starts_scalars = [record['scalars'] for record in filtered]
        self.current = 0 if reset_selection else min(self.current, len(self.starts) - 1)

        self.combo.blockSignals(True)
        self.combo.clear()
        self.combo.addItems(self.start_labels)
        self.combo.blockSignals(False)
        self.combo.setCurrentIndex(self.current)

        self._rebuild_tabs('multi_startup_view' if len(self.starts) > 1 else 'single_startup_view')
        if len(self.starts) > 1:
            self._cm_fill_list()
            self._cm_autosize_list()
            self._cm_params_autosize()
            self._cm_restore_state()
            self.cm_redraw()
            self.redraw_history()
        self.stack.setCurrentWidget(self.tabs_container)
        self.display_item()
        self.statusBar().showMessage(self.tr_text('status_visible', name=os.path.basename(self.current_file) if self.current_file else self.tr_text('dataset'), count=len(self.starts)))

    def open_filter_dialog(self):
        if not self.all_starts:
            QMessageBox.information(self, 'Filtros', 'Primero carga un CSV.')
            return
        protections = sorted({str(record.get('protection', 'Unknown')) for record in self.all_starts})
        start_types = sorted({str(record.get('start_type', 'Unknown')) for record in self.all_starts})
        dlg = FilterDialog(self, protections, start_types, self.current_filter)
        if dlg.exec_():
            self.current_filter = dlg.get_filter()
            self.apply_current_filters(reset_selection=True)

    def export_filtered_csv(self):
        if not self.starts:
            QMessageBox.information(self, 'Exportar CSV', 'No hay arranques visibles para exportar.')
            return
        file_path, _ = QFileDialog.getSaveFileName(self, 'Guardar CSV filtrado', 'arranques_filtrados.csv', 'CSV Files (*.csv)')
        if not file_path:
            return
        rows = []
        for record in self.starts:
            row = {'label': record.get('label', '')}
            for key, value in record.get('scalars', {}).items():
                row[key] = value
            rows.append(row)
        pd.DataFrame(rows).to_csv(file_path, index=False, encoding='utf-8-sig')
        self.statusBar().showMessage(self.tr_text('csv_exported', name=os.path.basename(file_path)))

    def export_current_view_png(self):
        if self.tabs_widget is None:
            QMessageBox.information(self, 'Exportar PNG', 'No hay vista activa para exportar.')
            return
        tab_name = self.tabs_widget.tabText(self.tabs_widget.currentIndex()).replace(' ', '_').lower()
        file_path, _ = QFileDialog.getSaveFileName(self, 'Guardar PNG', f'{tab_name}.png', 'PNG Files (*.png)')
        if not file_path:
            return
        current_widget = self.tabs_widget.currentWidget()
        if current_widget is None:
            QMessageBox.information(self, 'Exportar PNG', 'No se pudo obtener la vista activa.')
            return
        pixmap = current_widget.grab()
        pixmap.save(file_path, 'PNG')
        self.statusBar().showMessage(self.tr_text('png_exported', name=os.path.basename(file_path)))

    def _parse_scalars_from_row(self, r):
        scalars = {}
        idx = 21
        fields=[
            ('Duración (s)',0.1),('I máx (Arms)',1),('Tiempo I máx (s)',0.1),('I inicial',1),('I final',1),
            ('Vel ini',1),('Vel fin',1),('Sampling rate (ms)',1),('% desequ. fases',0.1),('% d motores',0.1),
            ('Temp ini (K)',1),('Temp fin (K)',1),('Par máx (%)',0.1),('Par mín (%)',0.1),
            ('Par cort (%)',0.1),('Tiempo cort(s)',0.1),('R ini (Ω)',0.001),('R fin (Ω)',0.001),
            ('Ratio R',0.1),('E dis(MJ)',0.1),('Amp frz(%)',0.1),('Inercia',1),('I cortoc (A)',1),('Ángulo (°)',1)
        ]
        for name, fac in fields:
            scalars[name] = parse_numeric(r[idx], fac)
            idx += 1
        return scalars

    # ---------- VIEWER BEHAVIOUR ----------
    def on_select(self,i):
        if 0<=i<len(self.starts): self.current=i; self.display_item()

    def display_item(self):
        if not self.starts:
            return

        record = self.starts[self.current]
        scalars = dict(record['scalars'])
        series = record['series']

        self.params_table.setRowCount(len(scalars))
        for row,(k,v) in enumerate(scalars.items()):
            self.params_table.setItem(row,0,QTableWidgetItem(str(k)))
            shown = 'No disponible' if isinstance(v, float) and np.isnan(v) else str(v)
            self.params_table.setItem(row,1,QTableWidgetItem(shown))
        self.params_table.resizeRowsToContents()

        ax,cv=self.ax_SCT,self.cv_SCT; ax.clear()
        t=np.asarray(series.get('time', []), dtype=float)
        sp=np.asarray(series.get('speed', []), dtype=float)
        cu=np.asarray(series.get('current', []), dtype=float)
        tq=np.asarray(series.get('torque', []), dtype=float)
        dual=np.asarray(series.get('dual_current', []), dtype=float)
        if t.size == 0:
            t=np.arange(len(sp), dtype=float)
        ax.plot(t,sp,'k',label='Speed'); ax.plot(t,cu,'#ff6600',label='Current')
        if dual.size: ax.plot(t[:len(dual)],dual,'b',label='Current 2º motor')
        ax.plot(t,tq,'#33cc33',label='Torque'); ax.set_xlabel('Time (s)'); ax.set_ylabel('% nominal'); ax.legend(); ax.grid(True); self._polish_canvas_layout(cv)

        ax,cv=self.ax_MLF,self.cv_MLF; ax.clear()
        load_tq=np.asarray(series.get('load_torque', []), dtype=float)
        mot_tq=np.asarray(series.get('motor_torque', []), dtype=float)
        ang=np.linspace(0,180,len(load_tq)) if len(load_tq) else np.array([])
        frz_pct=scalars.get('Amp frz(%)', np.nan)
        frzn=frz_pct*np.sin(np.radians(ang)) if len(ang) and not np.isnan(frz_pct) else np.array([])
        ax.plot(ang,mot_tq,'#ff6600',label='Motor'); ax.plot(ang,load_tq,'k',label='Load')
        if len(frzn): ax.plot(ang,frzn,'--',label='Frozen')
        ax.set_xlabel('Mill angle (°)'); ax.set_ylabel('% nominal'); ax.legend(); ax.grid(True); self._polish_canvas_layout(cv)

        ax,cv=self.ax_HAR,self.cv_HAR; ax.clear()
        raw_fr=np.asarray(series.get('harmonic_freq_raw', []), dtype=float)
        hz_fr=np.asarray(series.get('harmonic_freq_hz', []), dtype=float)
        amps=np.asarray(series.get('harmonic_amp', []), dtype=float)
        data=hz_fr if self.show_hz else raw_fr
        max_current=scalars.get('I máx (Arms)', np.nan)
        y=amps/max_current*100 if not np.isnan(max_current) and max_current>0 else amps
        mask = y > 0
        data = data[mask]; y = y[mask]
        pos=np.arange(len(data))
        ax.bar(pos,y,color='#33cc33')
        unit='Hz' if self.show_hz else 'Raw'
        ax.set_xticks(pos); ax.set_xticklabels([f"{v:.0f} {unit}" for v in data],rotation=45,ha='right')
        ax.set_xlabel(f'Freq ({unit})'); ax.set_ylabel('% Imax'); ax.grid(True,axis='y'); self._polish_canvas_layout(cv)

        self.btn_prev.setEnabled(self.current>0); self.btn_next.setEnabled(self.current<len(self.starts)-1)

    def toggle_harmonics_panel(self):
        if not hasattr(self, 'wrap_HAR') or self.wrap_HAR is None:
            return
        visible = not self.wrap_HAR.isVisible()
        self.wrap_HAR.setVisible(visible)
        self.btn_toggle_harmonics.setText(self.tr_text('hide_harmonics') if visible else self.tr_text('show_harmonics'))

    def toggle_units(self):
        self.show_hz=not self.show_hz; self.display_item(); self.cm_redraw()

    def prev_item(self):
        if self.current>0: self.current-=1; self.combo.setCurrentIndex(self.current)

    def next_item(self):
        if self.current<len(self.starts)-1: self.current+=1; self.combo.setCurrentIndex(self.current)

    # ---------- Persistencia CM ----------
    def _cm_save_state(self, write_to_disk=True):
        sel_params = self._cm_selected_params(self.cm_param_list) if getattr(self, 'cm_param_list', None) else []
        sel_params_secondary = self._cm_selected_params(self.cm_param_list_secondary) if getattr(self, 'cm_param_list_secondary', None) else []

        checked_starts = {}
        if hasattr(self, 'cm_list') and self.cm_list:
            for i in range(self.cm_list.count()):
                it = self.cm_list.item(i)
                checked_starts[it.text()] = (it.checkState() == Qt.Checked)

        div_left  = self.cm_div_left.value()  if getattr(self, 'cm_div_left', None)  else 6
        div_right = self.cm_div_right.value() if getattr(self, 'cm_div_right', None) else 6
        gridx     = self.cm_gridx.isChecked() if getattr(self, 'cm_gridx', None) else True
        show_second_graph = self.cm_second_graph_toggle.isChecked() if getattr(self, 'cm_second_graph_toggle', None) else False

        axis_map  = dict(self.cm_axis_map)   if hasattr(self, 'cm_axis_map')  else {}
        label_map = dict(self.cm_label_map)  if hasattr(self, 'cm_label_map') else {}
        transforms= dict(self.cm_transform_to_dict())

        self.cm_state.update({
            "selected_params": sel_params,
            "selected_params_secondary": sel_params_secondary,
            "axis_map": axis_map,
            "label_map": label_map,
            "transforms": transforms,
            "checked_starts": checked_starts,
            "div_left": div_left,
            "div_right": div_right,
            "gridx": gridx,
            "show_second_graph": show_second_graph,
            "show_full_dates": bool(self.cm_state.get("show_full_dates", True)),
            "show_click_date": bool(self.cm_state.get("show_click_date", True)),
            "enable_double_click_delete": bool(self.cm_state.get("enable_double_click_delete", True)),
            "enable_area_selection": bool(self.cm_state.get("enable_area_selection", True)),
            "show_start_selector": bool(self.cm_state.get("show_start_selector", True)),
            "show_param_selector": bool(self.cm_state.get("show_param_selector", True)),
        })
        if write_to_disk:
            self._cm_save_to_disk()

    def _cm_restore_state(self):
        st = self.cm_state
        if hasattr(self, 'cm_param_list') and self.cm_param_list:
            self.cm_param_list.blockSignals(True)
            present = set()
            for i in range(self.cm_param_list.count()):
                it = self.cm_param_list.item(i)
                present.add(it.text())
                it.setCheckState(Qt.Checked if it.text() in st.get("selected_params", []) else Qt.Unchecked)
            self.cm_axis_map.update({p:side for p,side in st.get("axis_map", {}).items() if p in present})
            self.cm_label_map.update({p:lbl  for p,lbl  in st.get("label_map", {}).items() if p in present})
            self.cm_param_list.blockSignals(False)
            self.cm_transform_from_dict({p:t for p,t in st.get("transforms", {}).items() if p in present})

        if hasattr(self, 'cm_param_list_secondary') and self.cm_param_list_secondary:
            self.cm_param_list_secondary.blockSignals(True)
            for i in range(self.cm_param_list_secondary.count()):
                it = self.cm_param_list_secondary.item(i)
                it.setCheckState(Qt.Checked if it.text() in st.get("selected_params_secondary", []) else Qt.Unchecked)
            self.cm_param_list_secondary.blockSignals(False)

        if hasattr(self, 'cm_list') and self.cm_list:
            self.cm_list.blockSignals(True)
            for i in range(self.cm_list.count()):
                it = self.cm_list.item(i)
                checked = st.get("checked_starts", {}).get(it.text(), True)
                it.setCheckState(Qt.Checked if checked else Qt.Unchecked)
            self.cm_list.blockSignals(False)

        if self.cm_div_left:  self.cm_div_left.setValue(st.get("div_left", 6))
        if self.cm_div_right: self.cm_div_right.setValue(st.get("div_right", 6))
        if self.cm_gridx:     self.cm_gridx.setChecked(st.get("gridx", True))
        if self.cm_second_graph_toggle: self.cm_second_graph_toggle.setChecked(st.get("show_second_graph", False))

    def _cm_settings_dir(self):
        return os.path.dirname(self._cm_settings_path)

    def _cm_save_to_disk(self):
        try:
            os.makedirs(self._cm_settings_dir(), exist_ok=True)
            with open(self._cm_settings_path, "w", encoding="utf-8") as f:
                json.dump(self.cm_state, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _cm_load_from_disk(self):
        try:
            if os.path.exists(self._cm_settings_path):
                with open(self._cm_settings_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.cm_state.update(data)
        except Exception:
            pass

    def closeEvent(self, event):
        try:
            if self._load_thread is not None and self._load_thread.isRunning():
                self.statusBar().showMessage('Esperando a que termine la carga del CSV...')
                self._load_thread.quit()
                self._load_thread.wait(15000)
            if self._cm_state_save_timer.isActive():
                self._cm_state_save_timer.stop()
            self._cm_save_state()
            self._save_ui_settings()
        finally:
            super().closeEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            current_tab = self.tabs_widget.tabText(self.tabs_widget.currentIndex()) if self.tabs_widget is not None else ''
            if current_tab == self.tr_text('cm_tab'):
                self._cm_cancel_pending_selection()
                if self.cm_area_selected_main:
                    self._cm_delete_area_selection(self.cm_canvas)
                    event.accept()
                    return
                if self.cm_area_selected_secondary:
                    self._cm_delete_area_selection(self.cm_canvas_secondary)
                    event.accept()
                    return
                if self._cm_delete_selected_point(self.cm_canvas):
                    event.accept()
                    return
                if self._cm_delete_selected_point(self.cm_canvas_secondary):
                    event.accept()
                    return
            if current_tab == self.tr_text('history_tab'):
                if self._delete_history_area_selection():
                    event.accept()
                    return
        super().keyPressEvent(event)


def _core_parse_scalars_from_row(self, row):
    return core_parse_scalars_from_multi_row(row)


def _core_parse_single_start_csv(self, rows):
    return [record.to_legacy() for record in core_parse_single_start_csv(rows)]


def _core_parse_csv_records(self, rows):
    csv_type, view_mode, records, _issues = parse_csv_records_to_legacy(rows)
    return csv_type, view_mode, records


def _core_estimate_mill_load_pct(self, record):
    return core_estimate_mill_load_pct(record)


def _core_compute_history_metrics(self):
    return core_compute_history_metrics(self.starts)


def _core_estimated_nominal_current(self):
    return core_estimated_nominal_current(self.starts, hidden_indices=self.history_hidden_indices)


def _core_linearity_pairs(self, x_name, y_name):
    return core_linearity_pairs(self.starts, x_name, y_name, hidden_indices=self.history_hidden_indices)


def _core_successful_speed_resistance_ratio_pairs(self):
    return core_successful_speed_resistance_ratio_pairs(
        self.starts,
        self.nominal_speed_rpm,
        hidden_indices=self.history_hidden_indices,
    )


def _core_successful_current_analysis_pairs(self, nominal_current):
    return core_successful_current_analysis_pairs(
        self.starts,
        nominal_current,
        hidden_indices=self.history_hidden_indices,
    )


DataVisualizer._parse_scalars_from_row = _core_parse_scalars_from_row
DataVisualizer.parse_single_start_csv = _core_parse_single_start_csv
DataVisualizer.parse_csv_records = _core_parse_csv_records
DataVisualizer._estimate_mill_load_pct = _core_estimate_mill_load_pct
DataVisualizer._compute_history_metrics = _core_compute_history_metrics
DataVisualizer._estimated_nominal_current = _core_estimated_nominal_current
DataVisualizer._linearity_pairs = _core_linearity_pairs
DataVisualizer._successful_speed_resistance_ratio_pairs = _core_successful_speed_resistance_ratio_pairs
DataVisualizer._successful_current_analysis_pairs = _core_successful_current_analysis_pairs

if __name__=='__main__':
    if sys.platform.startswith("win"):
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("RotorProtek.Visualizer")
        except Exception:
            pass
    app=QApplication(sys.argv)
    icon_path = resource_path("logo_app.ico")
    app.setWindowIcon(QIcon(icon_path))
    win=DataVisualizer()
    win.show()
    sys.exit(app.exec_())
