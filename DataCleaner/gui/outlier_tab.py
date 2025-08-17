import base64
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QComboBox, QTableWidget, QTableWidgetItem,
                            QHeaderView, QGroupBox, QSplitter, QDoubleSpinBox, QMessageBox)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QThread
from core import detect_outliers, handle_outliers
from PyQt5.QtCore import QObject, pyqtSignal

class OutlierAnalysisWorker(QObject):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, df, method, threshold):
        super().__init__()
        self.df = df
        self.method = method
        self.threshold = threshold
        
    def run(self):
        try:
            results = detect_outliers(
                self.df,
                method=self.method,
                threshold=self.threshold,
                generate_plots=True
            )
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))

class OutlierTab(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.current_analysis = None #new
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
                
        # Analysis group
        analysis_group = QGroupBox("Outlier Analysis")
        analysis_layout = QVBoxLayout()
        
        self.analysis_table = QTableWidget()
        self.analysis_table.setColumnCount(4)
        self.analysis_table.setHorizontalHeaderLabels(["Column", "Outliers", "Percentage", "Method"])
        self.analysis_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        analysis_layout.addWidget(self.analysis_table)
        analysis_group.setLayout(analysis_layout)
        
        # Handling group
        handling_group = QGroupBox("Outlier Handling")
        handling_layout = QVBoxLayout()
        
        # Detection settings
        detect_layout = QHBoxLayout()
        detect_layout.addWidget(QLabel("Method:"))
        
        self.method_combo = QComboBox()
        self.method_combo.addItems(["iqr", "zscore"])
        detect_layout.addWidget(self.method_combo)
        
        detect_layout.addWidget(QLabel("Threshold:"))
        self.threshold_input = QDoubleSpinBox()
        self.threshold_input.setRange(1.0, 5.0)
        self.threshold_input.setValue(1.5)
        detect_layout.addWidget(self.threshold_input)
        
        # Handling settings
        handle_layout = QHBoxLayout()
        handle_layout.addWidget(QLabel("Strategy:"))
        
        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems(["cap", "remove", "log"])
        handle_layout.addWidget(self.strategy_combo)
        
        # Buttons
        self.analyze_btn = QPushButton("Analyze Outliers")
        self.analyze_btn.clicked.connect(self.analyze)
        
        self.handle_btn = QPushButton("Handle Outliers")
        self.handle_btn.clicked.connect(self.handle_outliers)
        
        handling_layout.addLayout(detect_layout)
        handling_layout.addLayout(handle_layout)
        handling_layout.addWidget(self.analyze_btn)
        handling_layout.addWidget(self.handle_btn)
        handling_group.setLayout(handling_layout)
        
        layout.addWidget(analysis_group)
        layout.addWidget(handling_group)
       
        self.setLayout(layout)
        
   
    # def analyze(self):
    #     if self.parent.df is None:
    #         self.parent.log_tab.add_log("Cannot analyze outliers - no data loaded", level='warning')
    #         return
            
    #     method = self.method_combo.currentText()
    #     threshold = self.threshold_input.value()
        
    #     try:
    #         self.parent.log_tab.add_log(
    #             f"Starting outlier analysis using {method} method (threshold={threshold})..."
    #         )
            
    #         # Call the imported detect_outliers function
    #         self.current_analysis = detect_outliers(
    #             self.parent.df,
    #             method=method,
    #             threshold=threshold,
    #             generate_plots=True
    #         )

    #         # Update analysis table and log results
    #         self.analysis_table.setRowCount(len(self.current_analysis))
    #         total_outliers = 0
    #         columns_with_outliers = 0
            
    #         for i, (col, stats) in enumerate(self.current_analysis.items()):
    #             self.analysis_table.setItem(i, 0, QTableWidgetItem(col))
    #             self.analysis_table.setItem(i, 1, QTableWidgetItem(str(stats['count'])))
    #             self.analysis_table.setItem(i, 2, QTableWidgetItem(f"{stats['percentage']:.2f}%"))
    #             self.analysis_table.setItem(i, 3, QTableWidgetItem(stats['method']))
                
    #             if stats['count'] > 0:
    #                 total_outliers += stats['count']
    #                 columns_with_outliers += 1
    #                 self.parent.log_tab.add_log(
    #                     f"Column '{col}': {stats['count']} outliers detected "
    #                     f"({stats['percentage']:.2f}%) using {stats['method']}"
    #                 )

    #         # Log summary
    #         self.parent.log_tab.add_log(
    #             f"Outlier analysis complete. Found {total_outliers} outliers "
    #             f"across {columns_with_outliers} columns"
    #         )
            
                
    #     except Exception as e:
    #         self.parent.log_tab.add_log(f"Outlier analysis failed: {str(e)}", level='error')
    #         QMessageBox.critical(self, "Error", f"Analysis failed: {str(e)}")

    def analyze(self):
        if self.parent.df is None:
            self.parent.log_tab.add_log("Cannot analyze outliers - no data loaded", level='warning')
            return
            
        # Show loading state
        self.parent.loading_widget.start()
        self.parent.log_tab.add_log(
                f"Starting outlier analysis using {self.method_combo.currentText()} method (threshold={self.threshold_input.value()})..."
            )
        
        # Run analysis in thread
        self.analysis_thread = QThread()
        self.worker = OutlierAnalysisWorker(
            self.parent.df,
            self.method_combo.currentText(),
            self.threshold_input.value()
        )
        
        self.worker.moveToThread(self.analysis_thread)
        self.analysis_thread.started.connect(self.worker.run)
        self.worker.finished.connect(self._on_analysis_complete)
        self.worker.error.connect(self._on_analysis_error)
        self.analysis_thread.start()

    def _on_analysis_complete(self, results):
        self.analysis_thread.quit()
        self.analysis_thread.wait()
        self.parent.loading_widget.stop()
        
        self.current_analysis = results
        # Update GUI with results...
        self.analysis_table.setRowCount(len(self.current_analysis))
        total_outliers = 0
        columns_with_outliers = 0
        
        for i, (col, stats) in enumerate(self.current_analysis.items()):
            self.analysis_table.setItem(i, 0, QTableWidgetItem(col))
            self.analysis_table.setItem(i, 1, QTableWidgetItem(str(stats['count'])))
            self.analysis_table.setItem(i, 2, QTableWidgetItem(f"{stats['percentage']:.2f}%"))
            self.analysis_table.setItem(i, 3, QTableWidgetItem(stats['method']))
            
            if stats['count'] > 0:
                total_outliers += stats['count']
                columns_with_outliers += 1
                self.parent.log_tab.add_log(
                    f"Column '{col}': {stats['count']} outliers detected "
                    f"({stats['percentage']:.2f}%) using {stats['method']}"
                )

        # Log summary
        self.parent.log_tab.add_log(
            f"Outlier analysis complete. Found {total_outliers} outliers "
            f"across {columns_with_outliers} columns"
        )
        
    def _on_analysis_error(self, error_msg):
        self.analysis_thread.quit()
        self.parent.loading_widget.stop()
        self.parent.log_tab.add_log(f"Outlier analysis failed: {error_msg}", level='error')


    def handle_outliers(self):
        if self.parent.df is None:
            self.parent.log_tab.add_log("Cannot handle outliers - no data loaded", level='warning')
            return
            
        method = self.method_combo.currentText()
        threshold = self.threshold_input.value()
        strategy = self.strategy_combo.currentText()
        
        try:
            self.parent.log_tab.add_log(
                f"Starting outlier handling using {strategy} strategy "
                f"(detection method: {method}, threshold: {threshold})..."
            )
            
            new_df, report = handle_outliers(
                self.parent.df,
                strategy=strategy,
                method=method,
                threshold=threshold,
                generate_plots=True
            )
            
            self.parent.df = new_df
            self.parent.data_tab.update_data(new_df)
            
            # Log handling results
            processed_cols = report.get('processed_columns', [])
            self.parent.log_tab.add_log(
                f"Outlier handling complete. Modified {len(processed_cols)} columns: "
                f"{', '.join(processed_cols)}"
            )
                        
            # Log details for each column
            for col, details in report.get('details', {}).items():
                self.parent.log_tab.add_log(
                    f"Column '{col}': {details.get('outliers_processed', 0)} outliers "
                    f"handled using {details.get('method', 'unknown')}"
                )
                
            # Refresh Analysis
            self.analyze()

            # Show summary
            msg = QMessageBox()
            msg.setWindowTitle("Outliers Handled")
            msg.setText(f"Modified {len(processed_cols)} columns: {', '.join(processed_cols)}")
            msg.exec_()
            
            self.parent.status_bar.showMessage(
                f"Handled outliers using {strategy} strategy. "
                f"Modified {len(processed_cols)} columns."
            )
            
        except Exception as e:
            self.parent.log_tab.add_log(f"Outlier handling failed: {str(e)}", level='error')
            QMessageBox.critical(self, "Error", f"Handling failed: {str(e)}")