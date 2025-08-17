from PyQt5.QtWidgets import (QMainWindow, QTabWidget, QStatusBar, QVBoxLayout, 
                            QWidget, QMessageBox, QFileDialog, QProgressBar)
from PyQt5.QtCore import Qt
from gui.data_tab import DataTab
from gui.missing_tab import MissingTab
from gui.duplicate_tab import DuplicateTab
from gui.outlier_tab import OutlierTab
from gui.log_tab import LogTab
from core import analyze_missing, handle_missing_values
from core.file_loader import FileLoaderThread, FileLoaderSignals
import pandas as pd
from gui.visualization_tab import VisualizationTab
from gui.loading_widget import LoadingWidget
from PyQt5.QtCore import QThread, pyqtSignal


class AnalysisThread(QThread):
    finished = pyqtSignal()
    
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        
    def run(self):
        # Run all analysis in background
        self.parent.missing_tab.analyze()
        self.parent.duplicate_tab.analyze()
        self.parent.outlier_tab.analyze()
        self.finished.emit()

# class FileLoaderThread(QThread):
#     finished = pyqtSignal(object)
    
#     def __init__(self, file_path):
#         super().__init__()
#         self.file_path = file_path
        
#     def run(self):
#         try:
#             if self.file_path.endswith('.csv'):
#                 df = pd.read_csv(self.file_path)
#             elif self.file_path.endswith('.xlsx'):
#                 df = pd.read_excel(self.file_path)
#             self.finished.emit(df)
#         except Exception as e:
#             self.finished.emit(e)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Data Cleaning Tool")
        self.setGeometry(100, 100, 1200, 800)
        self.df = None
        self.original_df = None
        self.loading_widget = LoadingWidget(self)
        self.loading_widget.hide()
        self.init_ui()

        # Add progress bar to status bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setFixedWidth(200)
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)

    def resizeEvent(self, event):
        """Center loading widget when window resizes"""
        super().resizeEvent(event)
        self.center_loading_widget()
        
    def center_loading_widget(self):
        """Center the loading widget"""
        if hasattr(self, 'loading_widget'):
            self.loading_widget.move(
                self.width() // 2 - self.loading_widget.width() // 2,
                self.height() // 2 - self.loading_widget.height() // 2
            )
    

    def init_ui(self):
        # Central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        self.tab_widget = QTabWidget()

               
        # Initialize tabs
        self.data_tab = DataTab(self)
        self.missing_tab = MissingTab(self)
        self.duplicate_tab = DuplicateTab(self)
        self.outlier_tab = OutlierTab(self)
        self.visualization_tab = VisualizationTab(self)
        self.log_tab = LogTab(self)

        # Add tabs
        self.tab_widget.addTab(self.data_tab, "Data View")
        self.tab_widget.addTab(self.missing_tab, "Missing Values")
        self.tab_widget.addTab(self.duplicate_tab, "Duplicates")
        self.tab_widget.addTab(self.outlier_tab, "Outliers")
        self.tab_widget.addTab(self.visualization_tab, "Visualizations")
        self.tab_widget.addTab(self.log_tab,"Cleaning Log")

        # Connect to data changes
        if hasattr(self, 'data_loaded_signal'):  # If you have a signal for data loading
            self.data_loaded_signal.connect(self.visualization_tab.update_columns)
                
        layout.addWidget(self.tab_widget)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Create menu
        self.create_menu()
        
    def create_menu(self):
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        open_action = file_menu.addAction("Open")
        open_action.triggered.connect(self.open_file)
        
        save_action = file_menu.addAction("Save")
        save_action.triggered.connect(self.save_file)
        
        exit_action = file_menu.addAction("Exit")
        exit_action.triggered.connect(self.close)
        
        # Tools menu
        tools_menu = menubar.addMenu("Tools")
        analyze_action = tools_menu.addAction("Analyze All")
        analyze_action.triggered.connect(self.analyze_all)
        
    # def open_file(self):
    #     options = QFileDialog.Options()
    #     file_path, _ = QFileDialog.getOpenFileName(
    #         self, "Open Data File", "", 
    #         "CSV Files (*.csv);;Excel Files (*.xlsx);;All Files (*)", 
    #         options=options
    #     )
        
    #     if file_path:
            
    #         try:
    #             self.loading_widget.start()

    #             self.log_tab.add_log(f"Attempting to load file: {file_path}")
    #             if file_path.endswith('.csv'):
    #                 self.df = pd.read_csv(file_path)
    #                 self.log_tab.add_log(f"CSV file uploaded successfully")
    #             elif file_path.endswith('.xlsx'):
    #                 self.df = pd.read_excel(file_path)
    #                 self.log_tab.add_log(f"Excel file loaded successfully")
                
    #             self.original_df = self.df.copy()

    #             self.log_tab.add_log(f"Data loaded: {len(self.df)} rows, {len(self.df.columns)} columns"
    #                                  f"{self.df.memory_usage(deep=True).sum()/1024:.2f} KB memory usage")

    #             # Check for duplicate columns
    #             duplicate_cols = self.df.columns[self.df.columns.duplicated()]
    #             if not duplicate_cols.empty:
    #                 self.log_tab.add_log(
    #                 f"Warning: Found duplicate column names: {', '.join(duplicate_cols)}",
    #                 level='warning'
    #             )

    #             self.data_tab.update_data(self.df)
    #             self.status_bar.showMessage(f"Loaded {len(self.df)} rows with {len(self.df.columns)} columns")
    #             self.visualization_tab.update_columns()
                
    #             self.loading_widget.stop()

    #             # Show summary
    #             msg = QMessageBox()
    #             msg.setWindowTitle("File Uploaded")
    #             msg.setText(f"File Name:{file_path}\nRows: {len(self.df)}, Columns: {len(self.df.columns)}")
    #             msg.exec_()
                
    #             # Enable all tabs
    #             for i in range(1, self.tab_widget.count()):
    #                 self.tab_widget.setTabEnabled(i, True)

    #             self.log_tab.add_log("Data successfully loaded into application")
                    
    #         except Exception as e:
    #             self.log_tab.add_log(f"Failed to load file: {str(e)}", level = 'error')
    #             QMessageBox.critical(self, "Error", f"Failed to load file:\n{str(e)}")
    
    def open_file(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Data File", "", 
            "CSV Files (*.csv);;Excel Files (*.xlsx);;All Files (*)", 
            options=options
        )
        
        if file_path:
            # self.loading_widget.start()
            self.log_tab.add_log(f"Attempting to load file: {file_path}")
            
            # Start the file loading in a separate thread
            # self.file_loader_thread = FileLoaderThread(file_path)
            # self.file_loader_thread.finished.connect(self.on_file_loaded)
            # self.file_loader_thread.start()
            self._start_file_loading(file_path)

    def _start_file_loading(self, file_path):
        # Reset UI
        self.df = pd.DataFrame()
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.loading_widget.start()
        
        # Initialize loader
        self.file_loader = FileLoaderThread(
            file_path,
            max_size_mb=50,      # Configurable size limit
            chunk_size=50000     # Rows per chunk
        )
        
        # Connect signals
        self.file_loader.signals.progress.connect(self._update_progress)
        self.file_loader.signals.chunk_loaded.connect(self._process_chunk)
        self.file_loader.signals.finished.connect(self._on_loading_complete)
        self.file_loader.signals.error.connect(self._on_loading_error)
        
        self.file_loader.start()   

    def _update_progress(self, percent):
        self.progress_bar.setValue(percent)
        self.status_bar.showMessage(f"Loading... {percent}%")

    def _process_chunk(self, chunk):
        """Process each chunk as it loads"""
        if self.df.empty:
            self.df = chunk
        else:
            self.df = pd.concat([self.df, chunk])
        
        # Optional: Update table partially
        if len(self.df) <= 100000:  # Only update UI for smaller datasets
            self.data_tab.partial_update(self.df)
         

    # def on_file_loaded(self, result):
    #     """Handles the result of the file loading operation"""
    #     self.loading_widget.stop()
        
    #     if isinstance(result, pd.DataFrame):
    #         # Success case
    #         self.df = result
    #         self.original_df = result.copy()
            
    #         self.log_tab.add_log(
    #             f"Data loaded: {len(self.df)} rows, {len(self.df.columns)} columns, "
    #             f"{self.df.memory_usage(deep=True).sum()/1024:.2f} KB memory usage"
    #         )
            
    #         # Check for duplicate columns
    #         duplicate_cols = self.df.columns[self.df.columns.duplicated()]
    #         if not duplicate_cols.empty:
    #             self.log_tab.add_log(
    #                 f"Warning: Found duplicate column names: {', '.join(duplicate_cols)}",
    #                 level='warning'
    #             )
            
    #         # Update UI
    #         self.data_tab.update_data(self.df)
    #         self.visualization_tab.update_columns()
    #         self.status_bar.showMessage(f"Loaded {len(self.df)} rows with {len(self.df.columns)} columns")
            
    #         # Enable all tabs
    #         for i in range(1, self.tab_widget.count()):
    #             self.tab_widget.setTabEnabled(i, True)
            
    #         # Show summary
    #         QMessageBox.information(
    #             self, 
    #             "File Uploaded", 
    #             f"File Name: {self.file_loader_thread.file_path}\n"
    #             f"Rows: {len(self.df)}, Columns: {len(self.df.columns)}"
    #         )
            
    #         self.log_tab.add_log("Data successfully loaded into application")
            
    #     else:
    #         # Error case
    #         error = result
    #         self.log_tab.add_log(f"Failed to load file: {str(error)}", level='error')
    #         QMessageBox.critical(self, "Error", f"Failed to load file:\n{str(error)}")

    def _on_loading_complete(self):
        self.loading_widget.stop()
        self.progress_bar.setVisible(False)
        
        # Final processing
        self.original_df = self.df.copy()
        self.data_tab.final_update(self.df)
        # self._enable_all_tabs()
        for i in range(1, self.tab_widget.count()):
            self.tab_widget.setTabEnabled(i, True)

        self.visualization_tab.update_columns()
        
        # Log metrics
        mem_usage = self.df.memory_usage(index=True).sum() / 1024**2
        self.log_tab.add_log(
            f"Loaded {len(self.df)} rows ({mem_usage:.1f}MB) | "
            f"{self.df.shape[1]} columns"
        )

    def _on_loading_error(self, error_msg):
        self.loading_widget.stop()
        self.progress_bar.setVisible(False)
        self.log_tab.add_log(f"Load failed: {error_msg}", level='error')
        QMessageBox.critical(self, "Error", error_msg)    

    def save_file(self):
        if self.df is None:
            self.log_tab.add_log("Save attempted with no data loaded", level='warning')
            return
            
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Data", "", 
            "CSV Files (*.csv);;Excel Files (*.xlsx)", 
            options=options
        )
        
        if file_path:
            try:
                if file_path.endswith('.csv'):
                    self.df.to_csv(file_path, index=False)
                    self.log_tab.add_log(f"Data saved as CSV to {file_path}")
                elif file_path.endswith('.xlsx'):
                    self.df.to_excel(file_path, index=False)
                    self.log_tab.add_log(f"Data saved as Excel to {file_path}")
                    
                QMessageBox.information(self, "Success", "Data saved successfully!")
                self.log_tab.add_log(f"Saved {len(self.df)} rows with {len(self.df.columns)} columns")

            except Exception as e:
                self.log_tab.add_log(f"Failed to save file: {str(e)}", level='error')
                QMessageBox.critical(self, "Error", f"Failed to save file:\n{str(e)}")
    
    # def analyze_all(self):
    #     if self.df is None:
    #         return

    #     self.loading_widget.start()
    #     self.center_loading_widget()
    #     self.loading_widget.raise_()
    #     # Analyze missing values
    #     self.missing_tab.analyze()
        
        
    #     # Analyze duplicates
    #     self.duplicate_tab.analyze()
        
    #     # Analyze outliers
    #     self.outlier_tab.analyze()
    #     self.loading_widget.stop()
        
    #     self.status_bar.showMessage("Analysis completed for all data quality aspects")
    
    def analyze_all(self):
        if self.df is None:
            return
            
        self.loading_widget.start()
        self.center_loading_widget()
        self.loading_widget.raise_()  # Bring to front
        
        # Run analysis in background thread
        self.analysis_thread = AnalysisThread(self)
        self.analysis_thread.finished.connect(
            lambda: (
                self.loading_widget.stop(),
                self.status_bar.showMessage("Analysis completed")
            )
        )
        self.analysis_thread.start()    

    def update_data(self, new_df):
        self.df = new_df
        self.loading_widget.start()
        self.data_tab.update_data(self.df)
        self.loading_widget.stop()