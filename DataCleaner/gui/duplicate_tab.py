from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QComboBox, QTableWidget, QTableWidgetItem,
                            QHeaderView, QGroupBox)
from PyQt5.QtCore import Qt
from core import analyze_duplicates, handle_duplicates

class DuplicateTab(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Analysis group
        analysis_group = QGroupBox("Duplicate Analysis")
        analysis_layout = QVBoxLayout()
        
        self.analysis_table = QTableWidget()
        self.analysis_table.setColumnCount(3)
        self.analysis_table.setHorizontalHeaderLabels(["Column Group", "Duplicates", "Percentage"])
        self.analysis_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        analysis_layout.addWidget(self.analysis_table)
        analysis_group.setLayout(analysis_layout)
        
        # Handling group
        handling_group = QGroupBox("Duplicate Handling")
        handling_layout = QVBoxLayout()
        
        # Strategy selection
        strategy_layout = QHBoxLayout()
        strategy_layout.addWidget(QLabel("Strategy:"))
        
        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems(["drop", "flag"])
        strategy_layout.addWidget(self.strategy_combo)
        
        strategy_layout.addWidget(QLabel("Keep:"))
        self.keep_combo = QComboBox()
        self.keep_combo.addItems(["first", "last"])
        strategy_layout.addWidget(self.keep_combo)
        
        self.analyze_btn = QPushButton("Analyze Duplicates")
        self.analyze_btn.clicked.connect(self.analyze)
        
        self.handle_btn = QPushButton("Handle Duplicates")
        self.handle_btn.clicked.connect(self.handle_duplicates)
        
        handling_layout.addLayout(strategy_layout)
        handling_layout.addWidget(self.analyze_btn)
        handling_layout.addWidget(self.handle_btn)
        handling_group.setLayout(handling_layout)
        
        layout.addWidget(analysis_group)
        layout.addWidget(handling_group)
        self.setLayout(layout)
        
    def analyze(self):
        if self.parent.df is None:
            return

        self.parent.log_tab.add_log("Starting duplicate values analysis...")    
        analysis = analyze_duplicates(self.parent.df)
        
        # Group duplicates by column sets for display
        duplicate_groups = {}
        for cols, count in analysis['duplicate_groups'].items():
            col_str = ", ".join(str(x) for x in cols) if isinstance(cols, tuple) else str(cols)
            duplicate_groups[col_str] = count
        
        self.analysis_table.setRowCount(len(duplicate_groups))
        
        for i, (cols, count) in enumerate(duplicate_groups.items()):
            self.analysis_table.setItem(i, 0, QTableWidgetItem(cols))
            self.analysis_table.setItem(i, 1, QTableWidgetItem(str(count)))
            self.analysis_table.setItem(i, 2, QTableWidgetItem(f"{count/len(self.parent.df)*100:.2f}%"))
    
        self.parent.log_tab.add_log(
            f"Dupicate row analysis complete."
            f"Found {len(duplicate_groups)} duplicate rows accross {len(self.parent.df)} rows"
        )

    def handle_duplicates(self):
        if self.parent.df is None:
            return
            
        strategy = self.strategy_combo.currentText()
        keep = self.keep_combo.currentText()
        
        new_df, report = handle_duplicates(
            self.parent.df,
            strategy=strategy,
            keep=keep
        )
        
        self.parent.df = new_df
        self.parent.data_tab.update_data(new_df)
        self.analyze()  # Refresh analysis
        
        self.parent.log_tab.add_log(
            f"Handled duplicates using {strategy} strategy. "
            f"{report['rows_removed']} rows removed." if strategy == 'drop' else "Duplicates flagged."
        )

        self.parent.status_bar.showMessage(
            f"Handled duplicates using {strategy} strategy. "
            f"{report['rows_removed']} rows removed." if strategy == 'drop' else "Duplicates flagged."
        )