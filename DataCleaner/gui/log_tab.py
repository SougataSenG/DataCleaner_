from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTextEdit, QPushButton, 
                            QHBoxLayout, QGroupBox, QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt 
from PyQt5.QtCore import QDateTime
from PyQt5.QtGui import QColor
from datetime import datetime

class LogTab(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.log_messages = []
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Log display group
        log_group = QGroupBox("Cleaning Operations Log")
        log_layout = QVBoxLayout()
        
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setLineWrapMode(QTextEdit.NoWrap)
        
        # Control buttons
        btn_layout = QHBoxLayout()
        self.clear_btn = QPushButton("Clear Log")
        self.clear_btn.clicked.connect(self.clear_log)
        self.save_btn = QPushButton("Save Log")
        self.save_btn.clicked.connect(self.save_log)
        
        btn_layout.addWidget(self.clear_btn)
        btn_layout.addWidget(self.save_btn)
        
        log_layout.addWidget(self.log_display)
        log_layout.addLayout(btn_layout)
        log_group.setLayout(log_layout)
        
        layout.addWidget(log_group)
        self.setLayout(layout)
    
    def add_log(self, message: str, level: str = 'info'):
        """Add a new log message with timestamp and level"""
        from PyQt5.QtGui import QColor
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        level_prefix = {
            'info': '[INFO]',
            'warning': '[WARNING]',
            'error': '[ERROR]'
        }.get(level.lower(), '[INFO]')
        
        log_entry = f"{timestamp} {level_prefix} {message}"
        self.log_messages.append(log_entry)
        
        # Color coding
        if level.lower() == 'warning':
            self.log_display.setTextColor(QColor(180, 120, 0))  # Dark yellow
        elif level.lower() == 'error':
            self.log_display.setTextColor(Qt.red)
        else:
            self.log_display.setTextColor(Qt.black)
            
        self.log_display.append(log_entry)
        self.log_display.setTextColor(Qt.black)  # Reset color
        
        # Auto-scroll to bottom
        scrollbar = self.log_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_log(self):
        """Clear all log messages"""
        self.log_messages = []
        self.log_display.clear()
    
    def save_log(self):
        """Save the log content to a file"""
        if not self.log_messages:
            self.add_log("No log content to save", level='warning')
            return
            
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Save Log File",
            f"data_cleaning_log_{QDateTime.currentDateTime().toString('yyyyMMdd_hhmmss')}.txt",
            "Text Files (*.txt);;All Files (*)",
            options=options
        )
        
        if file_name:
            try:
                with open(file_name, 'w', encoding='utf-8') as f:
                    f.write("\n".join(self.log_messages))
                self.add_log(f"Log saved successfully to {file_name}")
            except Exception as e:
                self.add_log(f"Failed to save log: {str(e)}", level='error')
                QMessageBox.critical(self, "Error", f"Failed to save log:\n{str(e)}")