import sys
import time
import threading
import queue
import json
import csv
import os
import socket
import subprocess
import select
import logging
import platform
import asyncio
import datetime
import numpy
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QTabWidget, QTableWidget, QTableWidgetItem, QPushButton,
                            QLineEdit, QComboBox, QCheckBox, QLabel, QGroupBox,
                            QMenuBar, QMenu, QDialog, QFormLayout,
                            QSpinBox, QSystemTrayIcon, QMessageBox, QFileDialog,
                            QInputDialog, QSplitter, QStyleFactory)
from PyQt6.QtCore import Qt, QTimer, QCoreApplication, QSettings, QTranslator, QLocale, QEventLoop
from PyQt6.QtGui import QIcon, QColor, QPalette, QAction, QFont
import pandas as pd
import smtplib
from email.mime.text import MIMEText
import requests
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import dns.resolver
import qdarkstyle
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

# Setup logging
logging.basicConfig(filename='netping.log', level=logging.DEBUG,
                   format='%(asctime)s - %(levelname)s - %(message)s')

class PingResult:
    def __init__(self, host, timestamp, latency=None, jitter=None, packet_loss=None, status="Unknown"):
        self.host = host
        self.timestamp = timestamp
        self.latency = latency
        self.jitter = jitter
        self.packet_loss = packet_loss
        self.status = status

class NetPing(QMainWindow):
    def __init__(self):
        super().__init__()
        logging.debug("Initializing NetPing")
        print("Initializing NetPing")
        self.setWindowTitle("NetPing - Network Monitoring Tool")
        self.setGeometry(100, 100, 1200, 800)
        self.servers = []
        self.results = {}
        self.ping_thread = None
        self.running = False
        self.settings = QSettings("xAI", "NetPing")
        self.translator = QTranslator()
        self.current_language = "Persian"  # Set default to Persian
        self.translations = {}
        self.theme_label = None
        self.language_label = None
        self.setup_translations()
        self.setup_ui()
        self.load_settings()
        self.setup_system_tray()

    def setup_translations(self):
        logging.debug("Setting up translations")
        print("Setting up translations")
        self.translations = {
            "English": {
                "left_to_right": True,
                "add_server": "Add Server",
                "remove_server": "Remove Server",
                "start_monitoring": "Start Monitoring",
                "stop_monitoring": "Stop Monitoring",
                "settings": "Settings",
                "export_report": "Export Report",
                "language": "Language",
                "theme": "Theme",
                "interval": "Ping Interval (ms)",
                "timeout": "Timeout (ms)",
                "email_alerts": "Enable Email Alerts",
                "email_server": "Email Server",
                "email_port": "Email Port",
                "email_user": "Email User",
                "email_pass": "Email Password",
                "recipient": "Recipient Email",
                "save": "Save",
                "cancel": "Cancel",
                "dashboard": "Dashboard",
                "charts": "Charts",
                "logs": "Logs",
                "status": "Status",
                "latency": "Latency (ms)",
                "jitter": "Jitter (ms)",
                "packet_loss": "Packet Loss (%)",
                "host": "Host",
                "time": "Time",
                "export_csv": "Export to CSV",
                "export_pdf": "Export to PDF",
                "group_servers": "Group Servers",
                "discover_network": "Discover Network",
                "api_settings": "API Settings",
                "enable_api": "Enable API",
                "api_key": "API Key"
            },
            "Persian": {
                "left_to_right": False,
                "add_server": "اضافه کردن سرور",
                "remove_server": "حذف سرور",
                "start_monitoring": "شروع نظارت",
                "stop_monitoring": "توقف نظارت",
                "settings": "تنظیمات",
                "export_report": "صدور گزارش",
                "language": "زبان",
                "theme": "تم",
                "interval": "فاصله پینگ (میلی‌ثانیه)",
                "timeout": "تایم‌اوت (میلی‌ثانیه)",
                "email_alerts": "فعال کردن هشدارهای ایمیل",
                "email_server": "سرور ایمیل",
                "email_port": "پورت ایمیل",
                "email_user": "کاربر ایمیل",
                "email_pass": "رمز ایمیل",
                "recipient": "ایمیل گیرنده",
                "save": "ذخیره",
                "cancel": "لغو",
                "dashboard": "داشبورد",
                "charts": "نمودارها",
                "logs": "لاگ‌ها",
                "status": "وضعیت",
                "latency": "تأخیر (میلی‌ثانیه)",
                "jitter": "نوسان (میلی‌ثانیه)",
                "packet_loss": "از دست رفتن بسته (%)",
                "host": "هاست",
                "time": "زمان",
                "export_csv": "صدور به CSV",
                "export_pdf": "صدور به PDF",
                "group_servers": "گروه‌بندی سرورها",
                "discover_network": "کشف شبکه",
                "api_settings": "تنظیمات API",
                "enable_api": "فعال کردن API",
                "api_key": "کلید API"
            },
            "Chinese": {
                "left_to_right": True,
                "add_server": "添加服务器",
                "remove_server": "删除服务器",
                "start_monitoring": "开始监控",
                "stop_monitoring": "停止监控",
                "settings": "设置",
                "export_report": "导出报告",
                "language": "语言",
                "theme": "主题",
                "interval": "Ping间隔（毫秒）",
                "timeout": "超时（毫秒）",
                "email_alerts": "启用电子邮件警报",
                "email_server": "电子邮件服务器",
                "email_port": "电子邮件端口",
                "email_user": "电子邮件用户",
                "email_pass": "电子邮件密码",
                "recipient": "收件人电子邮件",
                "save": "保存",
                "cancel": "取消",
                "dashboard": "仪表板",
                "charts": "图表",
                "logs": "日志",
                "status": "状态",
                "latency": "延迟（毫秒）",
                "jitter": "抖动（毫秒）",
                "packet_loss": "丢包率（%）",
                "host": "主机",
                "time": "时间",
                "export_csv": "导出到CSV",
                "export_pdf": "导出到PDF",
                "group_servers": "分组服务器",
                "discover_network": "发现网络",
                "api_settings": "API设置",
                "enable_api": "启用API",
                "api_key": "API密钥"
            }
        }

    def setup_ui(self):
        logging.debug("Setting up UI")
        print("Setting up UI")
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Set window icon as logo
        self.setWindowIcon(QIcon("NetPing.jpg"))

        # Menu Bar
        menubar = self.menuBar()
        file_menu = menubar.addMenu(self.tr("File"))
        settings_action = QAction(self.tr("Settings"), self)
        settings_action.triggered.connect(self.show_settings_dialog)
        file_menu.addAction(settings_action)
        export_menu = QMenu(self.tr("Export"), self)
        export_csv = QAction(self.tr("Export to CSV"), self)
        export_csv.triggered.connect(self.export_to_csv)
        export_pdf = QAction(self.tr("Export to PDF"), self)
        export_pdf.triggered.connect(self.export_to_pdf)
        export_menu.addAction(export_csv)
        export_menu.addAction(export_pdf)
        file_menu.addMenu(export_menu)

        # Toolbar
        toolbar = QHBoxLayout()
        self.add_server_btn = QPushButton(self.tr("Add Server"))
        self.add_server_btn.clicked.connect(self.add_server)
        self.remove_server_btn = QPushButton(self.tr("Remove Server"))
        self.remove_server_btn.clicked.connect(self.remove_server)
        self.start_btn = QPushButton(self.tr("Start Monitoring"))
        self.start_btn.clicked.connect(self.start_monitoring)
        self.stop_btn = QPushButton(self.tr("Stop Monitoring"))
        self.stop_btn.clicked.connect(self.stop_monitoring)
        self.stop_btn.setEnabled(False)
        toolbar.addWidget(self.add_server_btn)
        toolbar.addWidget(self.remove_server_btn)
        toolbar.addWidget(self.start_btn)
        toolbar.addWidget(self.stop_btn)
        main_layout.addLayout(toolbar)

        # Tabs
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Dashboard Tab
        dashboard_widget = QWidget()
        dashboard_layout = QVBoxLayout(dashboard_widget)
        self.server_table = QTableWidget()
        self.server_table.setColumnCount(5)
        self.server_table.setHorizontalHeaderLabels([
            self.tr("Host"), self.tr("Status"), self.tr("Latency (ms)"),
            self.tr("Jitter (ms)"), self.tr("Packet Loss (%)")
        ])
        self.server_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.server_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        dashboard_layout.addWidget(self.server_table)
        self.tabs.addTab(dashboard_widget, self.tr("Dashboard"))

        # Charts Tab
        charts_widget = QWidget()
        charts_layout = QVBoxLayout(charts_widget)
        self.figure = plt.Figure()
        self.canvas = FigureCanvas(self.figure)
        charts_layout.addWidget(self.canvas)
        self.chart_selector = QComboBox()
        self.chart_selector.addItems([self.tr("Latency"), self.tr("Jitter"), self.tr("Packet Loss")])
        self.chart_selector.currentTextChanged.connect(self.update_chart)
        charts_layout.addWidget(self.chart_selector)
        self.tabs.addTab(charts_widget, self.tr("Charts"))

        # Logs Tab
        logs_widget = QWidget()
        logs_layout = QVBoxLayout(logs_widget)
        self.log_table = QTableWidget()
        self.log_table.setColumnCount(5)
        self.log_table.setHorizontalHeaderLabels([
            self.tr("Time"), self.tr("Host"), self.tr("Status"),
            self.tr("Latency (ms)"), self.tr("Packet Loss (%)")
        ])
        self.log_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        logs_layout.addWidget(self.log_table)
        self.tabs.addTab(logs_widget, self.tr("Logs"))

        # Theme selector
        theme_layout = QHBoxLayout()
        self.theme_label = QLabel(self.tr("Theme"))
        self.theme_selector = QComboBox()
        self.theme_selector.addItems(["Default", "Dark", "Light", "Red", "Blue"])
        self.theme_selector.currentTextChanged.connect(self.change_theme)
        theme_layout.addWidget(self.theme_label)
        theme_layout.addWidget(self.theme_selector)
        main_layout.addLayout(theme_layout)

        # Language selector
        language_layout = QHBoxLayout()
        self.language_label = QLabel(self.tr("Language"))
        self.language_selector = QComboBox()
        self.language_selector.addItems(["English", "Persian", "Chinese"])
        self.language_selector.setCurrentText(self.current_language)
        self.language_selector.currentTextChanged.connect(self.change_language)
        language_layout.addWidget(self.language_label)
        language_layout.addWidget(self.language_selector)
        main_layout.addLayout(language_layout)

        # Apply font for better readability
        font = QFont("Arial", 10)
        self.setFont(font)

        # Initialize UI elements
        self.update_server_table()
        self.update_chart()

    def setup_system_tray(self):
        logging.debug("Setting up system tray")
        print("Setting up system tray")
        self.tray_icon = QSystemTrayIcon(self)
        try:
            self.tray_icon.setIcon(QIcon("NetPing.jpg"))
        except:
            logging.warning("System tray icon not found, using default")
            print("System tray icon not found, using default")
            self.tray_icon.setIcon(QIcon())
        tray_menu = QMenu()
        show_action = QAction(self.tr("Show"), self)
        show_action.triggered.connect(self.show)
        quit_action = QAction(self.tr("Quit"), self)
        quit_action.triggered.connect(QCoreApplication.quit)
        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def change_theme(self, theme):
        logging.debug(f"Changing theme to {theme}")
        print(f"Changing theme to {theme}")
        if theme == "Dark":
            app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
        elif theme == "Light":
            app.setStyleSheet("")
            palette = QPalette()
            palette.setColor(QPalette.ColorRole.Window, QColor(245, 245, 245))
            palette.setColor(QPalette.ColorRole.Text, QColor(0, 0, 0))
            palette.setColor(QPalette.ColorRole.Button, QColor(200, 200, 200))
            palette.setColor(QPalette.ColorRole.ButtonText, QColor(0, 0, 0))
            app.setPalette(palette)
        elif theme == "Red":
            app.setStyleSheet("""
                QWidget { background-color: #ffe6e6; color: #000000; }
                QPushButton { background-color: #ff3333; color: #ffffff; border: 1px solid #cc0000; }
                QTableWidget { background-color: #fff0f0; color: #000000; }
                QComboBox { background-color: #ffffff; color: #000000; }
                QLabel { color: #000000; }
            """)
        elif theme == "Blue":
            app.setStyleSheet("""
                QWidget { background-color: #e6f3ff; color: #000000; }
                QPushButton { background-color: #3399ff; color: #ffffff; border: 1px solid #0066cc; }
                QTableWidget { background-color: #f0f8ff; color: #000000; }
                QComboBox { background-color: #ffffff; color: #000000; }
                QLabel { color: #000000; }
            """)
        else:  # Default
            app.setStyleSheet("")
            palette = QStyleFactory.create("Windows").standardPalette()
            palette.setColor(QPalette.ColorRole.Text, QColor(0, 0, 0))
            palette.setColor(QPalette.ColorRole.ButtonText, QColor(0, 0, 0))
            app.setPalette(palette)
        self.settings.setValue("theme", theme)

    def change_language(self, language):
        logging.debug(f"Changing language to {language}")
        print(f"Changing language to {language}")
        self.current_language = language
        direction = Qt.LayoutDirection.LeftToRight if self.translations[language]["left_to_right"] else Qt.LayoutDirection.RightToLeft
        app.setLayoutDirection(direction)
        self.translator = QTranslator()
        if language == "Persian":
            font = QFont("Noto Serif", 10)
            app.setFont(font)
        elif language == "Chinese":
            font = QFont("Noto Serif CJK SC", 10)
            app.setFont(font)
        else:
            font = QFont("Arial", 10)
            app.setFont(font)
        self.update_ui_texts()
        self.settings.setValue("language", language)

    def update_ui_texts(self):
        logging.debug("Updating UI texts")
        print("Updating UI texts")
        self.setWindowTitle(self.tr("NetPing - Network Monitoring Tool"))
        self.add_server_btn.setText(self.tr("Add Server"))
        self.remove_server_btn.setText(self.tr("Remove Server"))
        self.start_btn.setText(self.tr("Start Monitoring"))
        self.stop_btn.setText(self.tr("Stop Monitoring"))
        self.tabs.setTabText(0, self.tr("Dashboard"))
        self.tabs.setTabText(1, self.tr("Charts"))
        self.tabs.setTabText(2, self.tr("Logs"))
        self.server_table.setHorizontalHeaderLabels([
            self.tr("Host"), self.tr("Status"), self.tr("Latency (ms)"),
            self.tr("Jitter (ms)"), self.tr("Packet Loss (%)")
        ])
        self.log_table.setHorizontalHeaderLabels([
            self.tr("Time"), self.tr("Host"), self.tr("Status"),
            self.tr("Latency (ms)"), self.tr("Packet Loss (%)")
        ])
        self.chart_selector.clear()
        self.chart_selector.addItems([self.tr("Latency"), self.tr("Jitter"), self.tr("Packet Loss")])
        if self.theme_label:
            self.theme_label.setText(self.tr("Theme"))
        if self.language_label:
            self.language_label.setText(self.tr("Language"))
        self.menuBar().clear()
        file_menu = self.menuBar().addMenu(self.tr("File"))
        settings_action = QAction(self.tr("Settings"), self)
        settings_action.triggered.connect(self.show_settings_dialog)
        file_menu.addAction(settings_action)
        export_menu = QMenu(self.tr("Export"), self)
        export_csv = QAction(self.tr("Export to CSV"), self)
        export_csv.triggered.connect(self.export_to_csv)
        export_pdf = QAction(self.tr("Export to PDF"), self)
        export_pdf.triggered.connect(self.export_to_pdf)
        export_menu.addAction(export_csv)
        export_menu.addAction(export_pdf)
        file_menu.addMenu(export_menu)

    def tr(self, text):
        return self.translations[self.current_language].get(text, text)

    def add_server(self):
        logging.debug("Adding server")
        print("Adding server")
        host, ok = QInputDialog.getText(self, self.tr("Add Server"), self.tr("Enter IP or hostname:"))
        if ok and host:
            try:
                socket.gethostbyname(host)
                if host not in self.servers:
                    self.servers.append(host)
                    self.results[host] = [PingResult(host, datetime.now())]
                    self.update_server_table()
                    self.settings.setValue("servers", self.servers)
                    logging.info(f"Server {host} added successfully")
                    print(f"Server {host} added successfully")
                else:
                    logging.warning(f"Server {host} already exists")
                    print(f"Server {host} already exists")
            except socket.gaierror:
                QMessageBox.warning(self, self.tr("Error"), self.tr("Invalid IP or hostname"))
                logging.error(f"Failed to add server {host}: Invalid IP or hostname")
                print(f"Failed to add server {host}: Invalid IP or hostname")

    def remove_server(self):
        logging.debug("Removing server")
        print("Removing server")
        selected = self.server_table.currentRow()
        if selected >= 0:
            host = self.server_table.item(selected, 0).text()
            if host in self.servers:
                self.servers.remove(host)
                if host in self.results:
                    del self.results[host]
                self.update_server_table()
                self.settings.setValue("servers", self.servers)
                logging.info(f"Server {host} removed successfully")
                print(f"Server {host} removed successfully")
            else:
                logging.error(f"Failed to remove server {host}: Not found in servers list")
                print(f"Failed to remove server {host}: Not found in servers list")

    def update_server_table(self):
        logging.debug("Updating server table")
        print("Updating server table")
        self.server_table.setRowCount(len(self.servers))
        for i, host in enumerate(self.servers):
            self.server_table.setItem(i, 0, QTableWidgetItem(host))
            if host in self.results and self.results[host]:
                result = self.results[host][-1]
            else:
                result = PingResult(host, datetime.now())
            status_item = QTableWidgetItem(self.tr(result.status))
            latency_item = QTableWidgetItem(str(round(result.latency, 2)) if result.latency else "-")
            jitter_item = QTableWidgetItem(str(round(result.jitter, 2)) if result.jitter else "-")
            packet_loss_item = QTableWidgetItem(str(round(result.packet_loss, 2)) if result.packet_loss else "-")
            
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            latency_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            jitter_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            packet_loss_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            self.server_table.setItem(i, 1, status_item)
            self.server_table.setItem(i, 2, latency_item)
            self.server_table.setItem(i, 3, jitter_item)
            self.server_table.setItem(i, 4, packet_loss_item)
        
        self.server_table.resizeColumnsToContents()
        self.server_table.resizeRowsToContents()

    def start_monitoring(self):
        logging.debug("start_monitoring called")
        print("start_monitoring called")
        if not self.servers:
            logging.warning("Start monitoring failed: No servers added")
            print("Start monitoring failed: No servers added")
            QMessageBox.warning(self, self.tr("Warning"), self.tr("No servers added!"))
            return
        if self.running:
            logging.warning("Start monitoring called while already running")
            print("Start monitoring called while already running")
            return
        try:
            self.servers = list(dict.fromkeys(self.servers))
            self.settings.setValue("servers", self.servers)
            logging.debug("Removed duplicate servers")
            print("Removed duplicate servers")
            logging.debug("Setting running flag to True")
            print("Setting running flag to True")
            self.running = True
            logging.debug("Disabling start button, enabling stop button")
            print("Disabling start button, enabling stop button")
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            logging.debug("Creating ping thread")
            print("Creating ping thread")
            self.ping_thread = threading.Thread(target=self.ping_loop, daemon=True)
            logging.debug("Starting ping thread")
            print("Starting ping thread")
            self.ping_thread.start()
            logging.info("Monitoring started successfully")
            print("Monitoring started successfully")
            self.update_status_bar(self.tr("Monitoring started"))
        except Exception as e:
            logging.error(f"Failed to start monitoring: {str(e)}")
            print(f"Failed to start monitoring: {str(e)}")
            self.running = False
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            QMessageBox.critical(self, self.tr("Error"), f"{self.tr('Failed to start monitoring')}: {str(e)}")
            self.update_status_bar(f"Failed to start monitoring: {str(e)}")

    def stop_monitoring(self):
        logging.debug("stop_monitoring called")
        print("stop_monitoring called")
        self.running = False
        self.start_btn.setText(self.tr("Start Monitoring"))
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        if self.ping_thread and self.ping_thread.is_alive():
            logging.debug("Joining ping thread")
            print("Joining ping thread")
            self.ping_thread.join(timeout=1.0)
        self.ping_thread = None
        logging.info("Monitoring stopped")
        print("Monitoring stopped")
        self.update_status_bar(self.tr("Monitoring stopped"))

    def ping_loop(self):
        logging.debug("ping_loop started")
        print("ping_loop started")
        while self.running:
            logging.debug(f"ping_loop running, servers: {self.servers}")
            print(f"ping_loop running, servers: {self.servers}")
            for host in self.servers:
                try:
                    logging.debug(f"Pinging host: {host}")
                    print(f"Pinging host: {host}")
                    result = self.ping(host)
                    self.results.setdefault(host, []).append(result)
                    self.update_ui(result)
                    if self.settings.value("email_alerts", False, bool) and result.status != "Up":
                        self.send_alert_email(host, result)
                except Exception as e:
                    logging.error(f"Error pinging {host}: {str(e)}")
                    print(f"Error pinging {host}: {str(e)}")
                    result = PingResult(host, datetime.now(), None, None, 100.0, "Error")
                    self.results.setdefault(host, []).append(result)
                    self.update_ui(result)
            time.sleep(self.settings.value("interval", 1000, int) / 1000.0)
        logging.debug("ping_loop stopped")
        print("ping_loop stopped")

    def ping(self, host):
        logging.debug(f"Starting ping for {host}")
        print(f"Starting ping for {host}")
        try:
            timeout = self.settings.value("timeout", 1000, int) / 1000.0
            cmd = ["ping", "-n", "1", "-w", str(int(timeout * 1000)), host]
            if platform.system() != "Windows":
                cmd = ["ping", "-c", "1", "-W", str(int(timeout)), host]
            
            start_time = time.time()
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
            end_time = time.time()
            
            latency = None
            status = "Timeout"
            for line in output.splitlines():
                if "time=" in line or "time<" in line:
                    try:
                        time_str = line.split("time=")[1].split()[0]
                        if time_str.startswith("<"):
                            latency = 0.0
                        else:
                            latency = float(time_str.replace("ms", ""))
                        status = "Up"
                    except:
                        pass
            
            jitter = self.calculate_jitter(host, latency) if latency is not None else 0.0
            packet_loss = self.calculate_packet_loss(host)
            
            logging.debug(f"Ping successful for {host}: latency={latency}, jitter={jitter}, packet_loss={packet_loss}")
            print(f"Ping successful for {host}: latency={latency}, jitter={jitter}, packet_loss={packet_loss}")
            return PingResult(host, datetime.now(), latency, jitter, packet_loss, status)
        except subprocess.CalledProcessError:
            logging.debug(f"Ping timeout for {host}")
            print(f"Ping timeout for {host}")
            return PingResult(host, datetime.now(), None, None, 100.0, "Timeout")
        except Exception as e:
            logging.error(f"Ping error for {host}: {str(e)}")
            print(f"Ping error for {host}: {str(e)}")
            return PingResult(host, datetime.now(), None, None, 100.0, "Error")

    def calculate_jitter(self, host, current_latency):
        logging.debug(f"Calculating jitter for {host}")
        print(f"Calculating jitter for {host}")
        if len(self.results.get(host, [])) < 2:
            return 0.0
        previous_latency = self.results[host][-2].latency
        if previous_latency is None or current_latency is None:
            return 0.0
        return abs(current_latency - previous_latency)

    def calculate_packet_loss(self, host):
        logging.debug(f"Calculating packet loss for {host}")
        print(f"Calculating packet loss for {host}")
        if len(self.results.get(host, [])) < 10:
            return 0.0
        recent_results = self.results[host][-10:]
        failed = sum(1 for r in recent_results if r.status != "Up")
        return (failed / 10) * 100

    def update_ui(self, result):
        logging.debug(f"Updating UI for result: {result.host}, status: {result.status}")
        print(f"Updating UI for result: {result.host}, status: {result.status}")
        self.update_server_table()
        self.update_log_table(result)
        self.update_chart()

    def update_log_table(self, result):
        logging.debug(f"Updating log table for {result.host}")
        print(f"Updating log table for {result.host}")
        row = self.log_table.rowCount()
        self.log_table.insertRow(row)
        time_item = QTableWidgetItem(str(result.timestamp))
        host_item = QTableWidgetItem(result.host)
        status_item = QTableWidgetItem(self.tr(result.status))
        latency_item = QTableWidgetItem(str(round(result.latency, 2)) if result.latency else "-")
        packet_loss_item = QTableWidgetItem(str(round(result.packet_loss, 2)) if result.packet_loss else "-")
        
        time_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        host_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        latency_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        packet_loss_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.log_table.setItem(row, 0, time_item)
        self.log_table.setItem(row, 1, host_item)
        self.log_table.setItem(row, 2, status_item)
        self.log_table.setItem(row, 3, latency_item)
        self.log_table.setItem(row, 4, packet_loss_item)
        
        self.log_table.resizeColumnsToContents()
        self.log_table.resizeRowsToContents()

    def update_chart(self):
        logging.debug("Updating chart")
        print("Updating chart")
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        metric = self.chart_selector.currentText()
        logging.debug(f"Selected chart metric: {metric}")
        print(f"Selected chart metric: {metric}")
        has_data = False
        for host in self.servers:
            timestamps = []
            values = []
            for result in self.results.get(host, [])[-100:]:
                timestamps.append(result.timestamp)
                value = None
                try:
                    if metric == self.tr("Latency"):
                        value = result.latency
                    elif metric == self.tr("Jitter"):
                        value = result.jitter
                    elif metric == self.tr("Packet Loss"):
                        value = result.packet_loss
                    else:
                        logging.warning(f"Unknown chart metric: {metric}")
                        print(f"Unknown chart metric: {metric}")
                except Exception as e:
                    logging.error(f"Error selecting metric {metric} for host {host}: {str(e)}")
                    print(f"Error selecting metric {metric} for host {host}: {str(e)}")
                if value is not None:
                    values.append(value)
                    has_data = True
                else:
                    values.append(0)
            if values:
                ax.plot(timestamps, values, label=host)
        if has_data:
            ax.legend()
        ax.set_xlabel(self.tr("Time"))
        ax.set_ylabel(metric)
        ax.grid(True)
        self.figure.autofmt_xdate()
        self.canvas.draw()
        self.canvas.flush_events()
        logging.debug("Chart updated successfully")
        print("Chart updated successfully")

    def send_alert_email(self, host, result):
        logging.debug(f"Sending alert email for {host}")
        print(f"Sending alert email for {host}")
        if not self.settings.value("email_alerts", False, bool):
            logging.debug("Email alerts disabled")
            print("Email alerts disabled")
            return
        try:
            msg = MIMEText(f"Alert: {host} is {self.tr(result.status)}\n"
                          f"Latency: {result.latency or 'N/A'} ms\n"
                          f"Packet Loss: {result.packet_loss or 'N/A'}%")
            msg['Subject'] = f"NetPing Alert: {host}"
            msg['From'] = self.settings.value("email_user", "")
            msg['To'] = self.settings.value("recipient", "")

            server = smtplib.SMTP(self.settings.value("email_server", ""), 
                                self.settings.value("email_port", 587, int))
            server.starttls()
            server.login(self.settings.value("email_user", ""), 
                        self.settings.value("email_pass", ""))
            server.send_message(msg)
            server.quit()
            logging.info(f"Alert email sent for {host}")
            print(f"Alert email sent for {host}")
        except Exception as e:
            logging.error(f"Failed to send email alert for {host}: {str(e)}")
            print(f"Failed to send email alert for {host}: {str(e)}")

    def show_settings_dialog(self):
        logging.debug("Showing settings dialog")
        print("Showing settings dialog")
        dialog = QDialog(self)
        dialog.setWindowTitle(self.tr("Settings"))
        layout = QFormLayout(dialog)

        interval_spin = QSpinBox()
        interval_spin.setRange(100, 10000)
        interval_spin.setValue(self.settings.value("interval", 1000, int))
        layout.addRow(self.tr("Ping Interval (ms)"), interval_spin)

        timeout_spin = QSpinBox()
        timeout_spin.setRange(100, 10000)
        timeout_spin.setValue(self.settings.value("timeout", 1000, int))
        layout.addRow(self.tr("Timeout (ms)"), timeout_spin)

        email_alerts = QCheckBox()
        email_alerts.setChecked(self.settings.value("email_alerts", False, bool))
        layout.addRow(self.tr("Enable Email Alerts"), email_alerts)

        email_server = QLineEdit(self.settings.value("email_server", ""))
        layout.addRow(self.tr("Email Server"), email_server)

        email_port = QSpinBox()
        email_port.setRange(1, 65535)
        email_port.setValue(self.settings.value("email_port", 587, int))
        layout.addRow(self.tr("Email Port"), email_port)

        email_user = QLineEdit(self.settings.value("email_user", ""))
        layout.addRow(self.tr("Email User"), email_user)

        email_pass = QLineEdit(self.settings.value("email_pass", ""))
        email_pass.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addRow(self.tr("Email Password"), email_pass)

        recipient = QLineEdit(self.settings.value("recipient", ""))
        layout.addRow(self.tr("Recipient Email"), recipient)

        api_enabled = QCheckBox()
        api_enabled.setChecked(self.settings.value("api_enabled", False, bool))
        layout.addRow(self.tr("Enable API"), api_enabled)

        api_key = QLineEdit(self.settings.value("api_key", ""))
        layout.addRow(self.tr("API Key"), api_key)

        buttons = QHBoxLayout()
        save_btn = QPushButton(self.tr("Save"))
        save_btn.clicked.connect(lambda: self.save_settings(dialog, {
            "interval": interval_spin.value(),
            "timeout": timeout_spin.value(),
            "email_alerts": email_alerts.isChecked(),
            "email_server": email_server.text(),
            "email_port": email_port.value(),
            "email_user": email_user.text(),
            "email_pass": email_pass.text(),
            "recipient": recipient.text(),
            "api_enabled": api_enabled.isChecked(),
            "api_key": api_key.text()
        }))
        cancel_btn = QPushButton(self.tr("Cancel"))
        cancel_btn.clicked.connect(dialog.reject)
        buttons.addWidget(save_btn)
        buttons.addWidget(cancel_btn)
        layout.addRow(buttons)

        dialog.exec()

    def save_settings(self, dialog, settings):
        logging.debug("Saving settings")
        print("Saving settings")
        for key, value in settings.items():
            self.settings.setValue(key, value)
        dialog.accept()
        logging.info("Settings saved")
        print("Settings saved")
        self.update_ui_texts()

    def load_settings(self):
        logging.debug("Loading settings")
        print("Loading settings")
        self.servers = list(dict.fromkeys(self.settings.value("servers", [], list)))
        self.current_language = self.settings.value("language", "Persian")
        self.language_selector.setCurrentText(self.current_language)
        self.theme_selector.setCurrentText(self.settings.value("theme", "Default"))
        self.change_language(self.current_language)
        self.update_server_table()

    def export_to_csv(self):
        logging.debug("Exporting to CSV")
        print("Exporting to CSV")
        filename, _ = QFileDialog.getSaveFileName(self, self.tr("Save CSV"), "", "CSV Files (*.csv)")
        if filename:
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([self.tr("Time"), self.tr("Host"), self.tr("Status"), 
                                self.tr("Latency (ms)"), self.tr("Jitter (ms)"), self.tr("Packet Loss (%)")])
                for host in self.servers:
                    for result in self.results.get(host, []):
                        writer.writerow([
                            result.timestamp,
                            result.host,
                            self.tr(result.status),
                            round(result.latency, 2) if result.latency else "",
                            round(result.jitter, 2) if result.jitter else "",
                            round(result.packet_loss, 2) if result.packet_loss else ""
                        ])
            logging.info(f"Exported data to CSV: {filename}")
            print(f"Exported data to CSV: {filename}")

    def export_to_pdf(self):
        logging.debug("Exporting to PDF")
        print("Exporting to PDF")
        filename, _ = QFileDialog.getSaveFileName(self, self.tr("Save PDF"), "", "PDF Files (*.pdf)")
        if filename:
            c = canvas.Canvas(filename, pagesize=letter)
            c.setFont("Helvetica", 12)
            c.drawString(100, 750, self.tr("NetPing Report"))
            y = 700
            for host in self.servers:
                c.drawString(100, y, f"{self.tr('Host')}: {host}")
                y -= 20
                for result in self.results.get(host, [])[-10:]:
                    c.drawString(120, y, f"{result.timestamp}: {self.tr(result.status)}, "
                                       f"{self.tr('Latency')}: {round(result.latency, 2) if result.latency else 'N/A'} ms, "
                                       f"{self.tr('Packet Loss')}: {round(result.packet_loss, 2) if result.packet_loss else 'N/A'}%")
                    y -= 20
                y -= 10
            c.save()
            logging.info(f"Exported data to PDF: {filename}")
            print(f"Exported data to PDF: {filename}")

    def discover_network(self):
        logging.debug("Starting network discovery")
        print("Starting network discovery")
        def arp_scan():
            import subprocess
            try:
                output = subprocess.check_output(["arp", "-a"])
                lines = output.decode().split('\n')
                for line in lines:
                    if line.strip():
                        parts = line.split()
                        if len(parts) > 1:
                            ip = parts[0]
                            if ip not in self.servers:
                                self.servers.append(ip)
                                self.results[ip] = [PingResult(ip, datetime.now())]
                self.update_server_table()
                self.settings.setValue("servers", self.servers)
                logging.info("Network discovery completed")
                print("Network discovery completed")
            except Exception as e:
                logging.error(f"Network discovery failed: {str(e)}")
                print(f"Network discovery failed: {str(e)}")
        
        threading.Thread(target=arp_scan, daemon=True).start()

    def group_servers(self):
        logging.debug("Grouping servers")
        print("Grouping servers")
        group_name, ok = QInputDialog.getText(self, self.tr("Group Servers"), self.tr("Enter group name:"))
        if ok and group_name:
            selected = [self.server_table.item(row, 0).text() for row in range(self.server_table.rowCount())
                       if self.server_table.item(row, 0).isSelected()]
            if selected:
                self.settings.setValue(f"groups/{group_name}", selected)
                QMessageBox.information(self, self.tr("Success"), 
                                      f"{self.tr('Group')} {group_name} {self.tr('created with')} {len(selected)} {self.tr('servers')}.")
                logging.info(f"Server group {group_name} created with {len(selected)} servers")
                print(f"Server group {group_name} created with {len(selected)} servers")
            else:
                logging.warning("No servers selected for grouping")
                print("No servers selected for grouping")

    def start_api_server(self):
        logging.debug("Starting API server")
        print("Starting API server")
        if not self.settings.value("api_enabled", False, bool):
            logging.debug("API server disabled")
            print("API server disabled")
            return
        from http.server import HTTPServer, BaseHTTPRequestHandler
        class APIHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == "/api/ping_results":
                    self.send_response(200)
                    self.send_header("Content-type", "application/json")
                    self.end_headers()
                    data = {host: [r.__dict__ for r in results] for host, results in self.results.items()}
                    self.wfile.write(json.dumps(data).encode())
                else:
                    self.send_response(404)
                    self.end_headers()
        
        try:
            server = HTTPServer(('localhost', 8000), APIHandler)
            threading.Thread(target=server.serve_forever, daemon=True).start()
            logging.info("API server started")
            print("API server started")
        except Exception as e:
            logging.error(f"Failed to start API server: {str(e)}")
            print(f"Failed to start API server: {str(e)}")

    def closeEvent(self, event):
        logging.debug("Closing window, minimizing to tray")
        print("Closing window, minimizing to tray")
        self.tray_icon.showMessage(self.tr("NetPing"), self.tr("Application minimized to system tray"),
                                 QSystemTrayIcon.MessageIcon.Information)
        self.hide()
        event.ignore()

    def validate_ip(self, ip):
        logging.debug(f"Validating IP: {ip}")
        print(f"Validating IP: {ip}")
        try:
            socket.inet_aton(ip)
            return True
        except socket.error:
            return False

    def validate_hostname(self, hostname):
        logging.debug(f"Validating hostname: {hostname}")
        print(f"Validating hostname: {hostname}")
        try:
            socket.gethostbyname(hostname)
            return True
        except socket.gaierror:
            return False

    def clear_logs(self):
        logging.debug("Clearing logs")
        print("Clearing logs")
        self.log_table.setRowCount(0)
        for host in self.results:
            self.results[host] = []
        self.update_server_table()
        self.update_chart()
        logging.info("Logs cleared")
        print("Logs cleared")

    def export_log_to_json(self):
        logging.debug("Exporting logs to JSON")
        print("Exporting logs to JSON")
        filename, _ = QFileDialog.getSaveFileName(self, self.tr("Save JSON"), "", "JSON Files (*.json)")
        if filename:
            data = {host: [r.__dict__ for r in results] for host, results in self.results.items()}
            with open(filename, 'w') as f:
                json.dump(data, f, default=str)
            logging.info(f"Exported logs to JSON: {filename}")
            print(f"Exported logs to JSON: {filename}")

    def import_servers_from_file(self):
        logging.debug("Importing servers from file")
        print("Importing servers from file")
        filename, _ = QFileDialog.getOpenFileName(self, self.tr("Import Servers"), "", "Text Files (*.txt)")
        if filename:
            with open(filename, 'r') as f:
                for line in f:
                    host = line.strip()
                    if host and host not in self.servers and (self.validate_ip(host) or self.validate_hostname(host)):
                        self.servers.append(host)
                        self.results[host] = [PingResult(host, datetime.now())]
            self.update_server_table()
            self.settings.setValue("servers", self.servers)
            logging.info(f"Imported servers from file: {filename}")
            print(f"Imported servers from file: {filename}")

    def save_current_state(self):
        logging.debug("Saving current state")
        print("Saving current state")
        state = {
            "servers": self.servers,
            "results": {host: [r.__dict__ for r in results] for host, results in self.results.items()}
        }
        with open("netping_state.json", "w") as f:
            json.dump(state, f, default=str)
        logging.info("Current state saved to netping_state.json")
        print("Current state saved to netping_state.json")

    def load_state(self):
        logging.debug("Loading state")
        print("Loading state")
        try:
            with open("netping_state.json", "r") as f:
                state = json.load(f)
                self.servers = list(dict.fromkeys(state.get("servers", [])))
                self.results = {host: [PingResult(**r) for r in results] for host, results in state.get("results", {}).items()}
            self.update_server_table()
            self.settings.setValue("servers", self.servers)
            logging.info("State loaded from netping_state.json")
            print("State loaded from netping_state.json")
        except FileNotFoundError:
            logging.info("No saved state found")
            print("No saved state found")

    def check_server_status(self, host):
        logging.debug(f"Checking server status for {host}")
        print(f"Checking server status for {host}")
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((host, 80))
            sock.close()
            return result == 0
        except:
            return False

    def update_status_bar(self, message):
        logging.debug(f"Updating status bar: {message}")
        print(f"Updating status bar: {message}")
        self.statusBar().showMessage(self.tr(message), 5000)

    def schedule_monitoring(self):
        logging.debug("Scheduling monitoring")
        print("Scheduling monitoring")
        interval = self.settings.value("interval", 1000, int)
        QTimer.singleShot(interval, self.start_monitoring)

    def backup_settings(self):
        logging.debug("Backing up settings")
        print("Backing up settings")
        settings_data = {}
        for key in self.settings.allKeys():
            settings_data[key] = self.settings.value(key)
        with open("netping_settings_backup.json", "w") as f:
            json.dump(settings_data, f)
        logging.info("Settings backed up to netping_settings_backup.json")
        print("Settings backed up to netping_settings_backup.json")

    def restore_settings(self):
        logging.debug("Restoring settings")
        print("Restoring settings")
        try:
            with open("netping_settings_backup.json", "r") as f:
                settings_data = json.load(f)
                for key, value in settings_data.items():
                    self.settings.setValue(key, value)
            self.load_settings()
            logging.info("Settings restored from netping_settings_backup.json")
            print("Settings restored from netping_settings_backup.json")
        except FileNotFoundError:
            logging.info("No settings backup found")
            print("No settings backup found")

    def add_server_group(self):
        logging.debug("Adding server group")
        print("Adding server group")
        group_name, ok = QInputDialog.getText(self, self.tr("Add Server Group"), self.tr("Enter group name:"))
        if ok and group_name:
            self.settings.setValue(f"groups/{group_name}", [])
            QMessageBox.information(self, self.tr("Success"), f"{self.tr('Group')} {group_name} {self.tr('created')}.")
            logging.info(f"Server group {group_name} created")
            print(f"Server group {group_name} created")

    def remove_server_group(self):
        logging.debug("Removing server group")
        print("Removing server group")
        groups = [key.split('/')[-1] for key in self.settings.allKeys() if key.startswith("groups/")]
        group_name, ok = QInputDialog.getItem(self, self.tr("Remove Server Group"), 
                                            self.tr("Select group to remove:"), groups, 0, False)
        if ok and group_name:
            self.settings.remove(f"groups/{group_name}")
            QMessageBox.information(self, self.tr("Success"), f"{self.tr('Group')} {group_name} {self.tr('removed')}.")
            logging.info(f"Server group {group_name} removed")
            print(f"Server group {group_name} removed")

    def export_chart(self):
        logging.debug("Exporting chart")
        print("Exporting chart")
        filename, _ = QFileDialog.getSaveFileName(self, self.tr("Save Chart"), "", "PNG Files (*.png)")
        if filename:
            self.figure.savefig(filename)
            logging.info(f"Chart exported to {filename}")
            print(f"Chart exported to {filename}")

    def toggle_fullscreen(self):
        logging.debug("Toggling fullscreen")
        print("Toggling fullscreen")
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def reset_ui(self):
        logging.debug("Resetting UI")
        print("Resetting UI")
        self.servers = []
        self.results = {}
        self.update_server_table()
        self.log_table.setRowCount(0)
        self.figure.clear()
        self.canvas.draw()
        self.canvas.flush_events()
        self.settings.setValue("servers", self.servers)
        logging.info("UI reset")
        print("UI reset")

    def check_for_updates(self):
        logging.debug("Checking for updates")
        print("Checking for updates")
        try:
            response = requests.get("https://api.example.com/netping/version")
            latest_version = response.json().get("version")
            current_version = "1.0.0"
            if latest_version != current_version:
                QMessageBox.information(self, self.tr("Update Available"), 
                                      f"{self.tr('New version')} {latest_version} {self.tr('is available.')}")
            logging.info(f"Checked for updates: Current version {current_version}, Latest version {latest_version}")
            print(f"Checked for updates: Current version {current_version}, Latest version {latest_version}")
        except:
            logging.error("Failed to check for updates")
            print("Failed to check for updates")

    def log_event(self, event):
        logging.debug(f"Logging event: {event}")
        print(f"Logging event: {event}")
        logging.info(event)
        self.update_status_bar(event)

    def validate_email_settings(self):
        logging.debug("Validating email settings")
        print("Validating email settings")
        email_server = self.settings.value("email_server", "")
        email_port = self.settings.value("email_port", 587, int)
        email_user = self.settings.value("email_user", "")
        email_pass = self.settings.value("email_pass", "")
        recipient = self.settings.value("recipient", "")
        return all([email_server, email_port, email_user, email_pass, recipient])

    def test_email_settings(self):
        logging.debug("Testing email settings")
        print("Testing email settings")
        if not self.validate_email_settings():
            QMessageBox.warning(self, self.tr("Error"), self.tr("Email settings incomplete"))
            logging.warning("Email settings test failed: Incomplete settings")
            print("Email settings test failed: Incomplete settings")
            return
        try:
            msg = MIMEText("Test email from NetPing")
            msg['Subject'] = "Test Email"
            msg['From'] = self.settings.value("email_user", "")
            msg['To'] = self.settings.value("recipient", "")
            server = smtplib.SMTP(self.settings.value("email_server", ""), 
                                self.settings.value("email_port", 587, int))
            server.starttls()
            server.login(self.settings.value("email_user", ""), 
                        self.settings.value("email_pass", ""))
            server.send_message(msg)
            server.quit()
            QMessageBox.information(self, self.tr("Success"), self.tr("Test email sent successfully"))
            logging.info("Test email sent successfully")
            print("Test email sent successfully")
        except Exception as e:
            QMessageBox.warning(self, self.tr("Error"), f"{self.tr('Failed to send test email')}: {str(e)}")
            logging.error(f"Test email failed: {str(e)}")
            print(f"Test email failed: {str(e)}")

    def schedule_backup(self):
        logging.debug("Scheduling backup")
        print("Scheduling backup")
        QTimer.singleShot(3600000, self.backup_settings)

    def monitor_network_changes(self):
        logging.debug("Monitoring network changes")
        print("Monitoring network changes")
        def check_network():
            while self.running:
                for host in self.servers:
                    status = self.check_server_status(host)
                    self.log_event(f"Network check: {host} is {'up' if status else 'down'}")
                time.sleep(60)
        threading.Thread(target=check_network, daemon=True).start()

    def export_all_data(self):
        logging.debug("Exporting all data")
        print("Exporting all data")
        filename, _ = QFileDialog.getSaveFileName(self, self.tr("Export All Data"), "", "JSON Files (*.json)")
        if filename:
            data = {
                "servers": self.servers,
                "results": {host: [r.__dict__ for r in results] for host, results in self.results.items()},
                "settings": {key: self.settings.value(key) for key in self.settings.allKeys()}
            }
            with open(filename, 'w') as f:
                json.dump(data, f, default=str)
            logging.info(f"Exported all data to {filename}")
            print(f"Exported all data to {filename}")

    def import_all_data(self):
        logging.debug("Importing all data")
        print("Importing all data")
        filename, _ = QFileDialog.getOpenFileName(self, self.tr("Import All Data"), "", "JSON Files (*.json)")
        if filename:
            try:
                with open(filename, 'r') as f:
                    data = json.load(f)
                    self.servers = list(dict.fromkeys(data.get("servers", [])))
                    self.results = {host: [PingResult(**r) for r in results] for host, results in data.get("results", {}).items()}
                    for key, value in data.get("settings", {}).items():
                        self.settings.setValue(key, value)
                self.update_server_table()
                self.change_language(self.current_language)
                logging.info(f"Imported all data from {filename}")
                print(f"Imported all data from {filename}")
            except Exception as e:
                QMessageBox.warning(self, self.tr("Error"), f"{self.tr('Failed to import data')}: {str(e)}")
                logging.error(f"Failed to import data from {filename}: {str(e)}")
                print(f"Failed to import data from {filename}: {str(e)}")

    def add_context_menu(self):
        logging.debug("Adding context menu")
        print("Adding context menu")
        context_menu = QMenu(self)
        clear_logs_action = QAction(self.tr("Clear Logs"), self)
        clear_logs_action.triggered.connect(self.clear_logs)
        export_json_action = QAction(self.tr("Export to JSON"), self)
        export_json_action.triggered.connect(self.export_log_to_json)
        import_servers_action = QAction(self.tr("Import Servers"), self)
        import_servers_action.triggered.connect(self.import_servers_from_file)
        context_menu.addAction(clear_logs_action)
        context_menu.addAction(export_json_action)
        context_menu.addAction(import_servers_action)
        self.server_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.server_table.customContextMenuRequested.connect(lambda pos: context_menu.exec(self.server_table.mapToGlobal(pos)))

    def initialize_ui(self):
        logging.debug("Initializing UI")
        print("Initializing UI")
        self.add_context_menu()
        self.load_state()
        self.schedule_backup()
        self.check_for_updates()

    def get_favicon_html(self):
        logging.debug("Generating favicon HTML")
        print("Generating favicon HTML")
        return """
<!DOCTYPE html>
<html>
<head>
    <link rel="icon" type="image/jpg" href="NetPing.jpg">
</head>
<body>
    <!-- NetPing application content would go here -->
</body>
</html>
"""

if __name__ == '__main__':
    logging.debug("Starting application")
    print("Starting application")
    app = QApplication(sys.argv)
    app.setStyle("Windows")
    window = NetPing()
    window.initialize_ui()
    window.show()
    logging.debug("Application started")
    print("Application started")
    sys.exit(app.exec())