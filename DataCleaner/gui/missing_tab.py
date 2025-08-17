import numpy as np
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QComboBox, QTableWidget, QTableWidgetItem,
                            QHeaderView, QGroupBox, QMessageBox)
from PyQt5.QtCore import Qt
from core.missing_handler import analyze_missing, handle_missing_values, get_missing_value_suggestion
from core.analyzer import get_cleaning_recommendations, generate_quality_report

class MissingTab(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Analysis group
        analysis_group = QGroupBox("Missing Value Analysis")
        analysis_layout = QVBoxLayout()
        
        self.analysis_table = QTableWidget()
        self.analysis_table.setColumnCount(5)
        headers = ["Column", "Type", "Missing Count", "Percentage", "Recommended Action"]
        self.analysis_table.setHorizontalHeaderLabels(headers)
        self.analysis_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        analysis_layout.addWidget(self.analysis_table)
        analysis_group.setLayout(analysis_layout)
        
        # Handling group
        handling_group = QGroupBox("Missing Value Handling")
        handling_layout = QVBoxLayout()
        
        # Strategy selection
        strategy_layout = QHBoxLayout()
        strategy_layout.addWidget(QLabel("Strategy:"))
        
        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems([
            "auto (use recommendations)", 
            "mean", 
            "median", 
            "mode", 
            "interpolate", 
            "drop"
        ])
        strategy_layout.addWidget(self.strategy_combo)
        
        self.analyze_btn = QPushButton("Analyze Missing Values")
        self.analyze_btn.clicked.connect(self.analyze)
        
        self.recommend_btn = QPushButton("Show Recommendations")
        self.recommend_btn.clicked.connect(self.show_recommendations)
        
        self.handle_btn = QPushButton("Handle Missing Values")
        self.handle_btn.clicked.connect(self.handle_missing)
        
        handling_layout.addLayout(strategy_layout)
        handling_layout.addWidget(self.analyze_btn)
        handling_layout.addWidget(self.recommend_btn)
        handling_layout.addWidget(self.handle_btn)
        handling_group.setLayout(handling_layout)
        
        layout.addWidget(analysis_group)
        layout.addWidget(handling_group)
        self.setLayout(layout)
        
    def analyze(self):
        if self.parent.df is None:
            QMessageBox.warning(self, "Warning", "No data loaded!")
            return
        
        try:
            # Log start of analysis
            self.parent.log_tab.add_log("Starting missing value analysis...")
            
            self.analysis = analyze_missing(self.parent.df)
            self.analysis_table.setRowCount(len(self.analysis['counts']))
            
            total_missing = 0
            columns_with_missing = 0
            
            for i, col in enumerate(self.analysis['counts'].keys()):
                dtype = str(self.parent.df[col].dtype)
                count = self.analysis['counts'][col]
                percent = self.analysis['percentages'][col]
                
                # Update summary counts
                if count > 0:
                    total_missing += count
                    columns_with_missing += 1
                    self.parent.log_tab.add_log(
                        f"Column '{col}' ({dtype}): {count} missing values ({percent:.2f}%)"
                    )
                
                # Update table
                self.analysis_table.setItem(i, 0, QTableWidgetItem(col))
                self.analysis_table.setItem(i, 1, QTableWidgetItem(dtype))
                self.analysis_table.setItem(i, 2, QTableWidgetItem(str(count)))
                self.analysis_table.setItem(i, 3, QTableWidgetItem(f"{percent:.2f}%"))
                self.analysis_table.setItem(i, 4, QTableWidgetItem(""))  # Empty for now
            
            # Log summary
            self.parent.log_tab.add_log(
                f"Missing value analysis complete. "
                f"Found {total_missing} missing values across {columns_with_missing} columns"
            )
            
            if total_missing > 0:
                self.parent.log_tab.add_log(
                    "Click 'Show Recommendations' to see suggested handling methods",
                    level='info'
                )
                
        except Exception as e:
            self.parent.log_tab.add_log(
                f"Failed to analyze missing values: {str(e)}",
                level='error'
            )
            QMessageBox.critical(self, "Error", f"Analysis failed: {str(e)}")
                
   
    def show_recommendations(self):
        if not hasattr(self, 'analysis') or self.parent.df is None:
            QMessageBox.warning(self, "Warning", "Please analyze data first!")
            return
                
        try:
            self.parent.log_tab.add_log("Generating missing value recommendations...")
            
            quality_report = generate_quality_report(self.parent.df)
            recommendations = get_cleaning_recommendations(quality_report, self.parent.df)
            
            for i, col in enumerate(self.analysis['counts'].keys()):
                if col in recommendations['missing_values']:
                    action = recommendations['missing_values'][col]
                    self.analysis_table.setItem(i, 4, QTableWidgetItem(action))
                    
                    # Log each recommendation
                    if self.analysis['counts'][col] > 0:
                        self.parent.log_tab.add_log(
                            f"Recommendation for '{col}': {action} "
                            f"(has {self.analysis['counts'][col]} missing values)"
                        )
            
            self.parent.log_tab.add_log("Recommendations generated successfully")
            
        except Exception as e:
            self.parent.log_tab.add_log(
                f"Failed to generate recommendations: {str(e)}",
                level='error'
            )
            QMessageBox.critical(self, "Error", f"Failed to generate recommendations: {str(e)}")
                
    def handle_missing(self):
        if self.parent.df is None:
            QMessageBox.warning(self, "Warning", "No data loaded!")
            return
            
        strategy = self.strategy_combo.currentText().split(" ")[0]
        
        if strategy == "auto":
            new_df, report = handle_missing_values(
                self.parent.df,
                auto_apply_suggestions=True,
                log_callback=self.parent.log_tab.add_log
            )
        else:
            new_df, report = handle_missing_values(
                self.parent.df,
                numeric_strategy=strategy,
                categorical_strategy=strategy,
                datetime_strategy=strategy,
                log_callback=self.parent.log_tab.add_log
            )
        
        self.parent.df = new_df
        self.parent.data_tab.update_data(new_df)
        self.analyze()  # Refresh analysis
        
        # Show summary
        msg = QMessageBox()
        msg.setWindowTitle("Processing Complete")
        msg.setText(f"Handled missing values using {strategy} strategy")
        
        if report['columns_dropped']:
            msg.setInformativeText(f"Dropped columns: {', '.join(report['columns_dropped'])}")
        if report['columns_filled']:
            filled = [f"{col} ({method})" for col, method, _ in report['columns_filled']]
            msg.setDetailedText("\n".join(filled))
        
        msg.exec_()