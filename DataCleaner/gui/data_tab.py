from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, 
                            QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import pandas as pd

class FileLoaderThread(QThread):
    finished = pyqtSignal(object)  # Will emit either DataFrame or Exception
    
    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path
        
    def run(self):
        try:
            if self.file_path.endswith('.csv'):
                df = pd.read_csv(self.file_path)
            elif self.file_path.endswith('.xlsx'):
                df = pd.read_excel(self.file_path)
            self.finished.emit(df)
        except Exception as e:
            self.finished.emit(e)

class DataTab(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.init_ui()
        self._partial_update_threshold = 100000 #update Ui only below this row count
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Create table widget
        self.table = QTableWidget()
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        
        layout.addWidget(self.table)
        self.setLayout(layout)
        
    # def update_data(self, df):
    #     if df is None:
    #         self.parent.log_tab.add_log("Attempted to update data view with None dataframe", level='warning')
    #         return
            
    #     self.table.setRowCount(df.shape[0])
    #     self.table.setColumnCount(df.shape[1])
    #     self.table.setHorizontalHeaderLabels(df.columns)
        
    #     # Populate table
    #     for i in range(df.shape[0]):
    #         for j in range(df.shape[1]):
    #             item = QTableWidgetItem(str(df.iloc[i, j]))
    #             item.setFlags(item.flags() ^ Qt.ItemIsEditable)
    #             self.table.setItem(i, j, item)
        
    #     # Resize columns
    #     self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
    #     self.table.horizontalHeader().setStretchLastSection(True)

    def partial_update(self, df):
        """Fast partial update for chunked loading"""
        if len(df) > self._partial_update_threshold:
            return
            
        self.table.setRowCount(len(df))
        # Only update visible portion
        for i in range(min(100, len(df))):  # First 100 rows
            for j, value in enumerate(df.iloc[i]):
                self.table.setItem(i, j, QTableWidgetItem(str(value)))

    def final_update(self, df):
        """Complete update after all chunks loaded"""
        self.table.setRowCount(0)  # Clear first
        self.table.setColumnCount(len(df.columns))
        self.table.setHorizontalHeaderLabels(df.columns)
        
        # Only load visible portion for large files
        display_rows = min(1000, len(df))
        self.table.setRowCount(display_rows)
        
        for i in range(display_rows):
            for j, value in enumerate(df.iloc[i]):
                self.table.setItem(i, j, QTableWidgetItem(str(value)))

    def update_data(self, df):
        if df is None:
            self.parent.log_tab.add_log("Attempted to update data view with None dataframe", level='warning')
            return
            
        try:
            self.parent.log_tab.add_log("Updating data table view...")
            
            self.table.setRowCount(df.shape[0])
            self.table.setColumnCount(df.shape[1])
            self.table.setHorizontalHeaderLabels(df.columns)
            
            # Populate table
            for i in range(df.shape[0]):
                for j in range(df.shape[1]):
                    item = QTableWidgetItem(str(df.iloc[i, j]))
                    item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                    self.table.setItem(i, j, item)
            
            # Resize columns
            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
            self.table.horizontalHeader().setStretchLastSection(True)
            
            self.parent.log_tab.add_log(
                f"Data view updated with {df.shape[0]} rows and {df.shape[1]} columns"
            )
            
        except Exception as e:
            self.parent.log_tab.add_log(
                f"Failed to update data view: {str(e)}", 
                level='error'
            )
            raise