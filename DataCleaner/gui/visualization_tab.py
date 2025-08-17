from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QComboBox, QGroupBox, QSplitter, QTabWidget, QDoubleSpinBox)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
import base64
import matplotlib.pyplot as plt
from io import BytesIO
from core.outlier_handler import detect_outliers, generate_outlier_plots


class VisualizationTab(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.init_ui()
        self.update_columns()
        
    def init_ui(self):
        main_layout = QVBoxLayout()
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Missing Data Tab
        self.missing_data_tab = QWidget()
        self.setup_missing_data_tab()
        self.tab_widget.addTab(self.missing_data_tab, "Missing Data")
        
        # Outliers Tab
        self.outliers_tab = QWidget()
        self.setup_outliers_tab()
        self.tab_widget.addTab(self.outliers_tab, "Outliers")
        
        main_layout.addWidget(self.tab_widget)
        self.setLayout(main_layout)
    
    def setup_missing_data_tab(self):
        layout = QVBoxLayout()
        
        # Control Panel
        control_group = QGroupBox("Visualization Controls")
        control_layout = QHBoxLayout()
        
        # Visualization Type
        control_layout.addWidget(QLabel("View:"))
        self.missing_view_combo = QComboBox()
        self.missing_view_combo.addItems(["Column Wise", "Row Wise"])
        control_layout.addWidget(self.missing_view_combo)
        
        # Plot Type
        control_layout.addWidget(QLabel("Plot Type:"))
        self.missing_plot_combo = QComboBox()
        self.missing_plot_combo.addItems(["Bar Plot", "Heatmap", "Matrix"])
        control_layout.addWidget(self.missing_plot_combo)
        
        # Generate Button
        self.missing_generate_btn = QPushButton("Generate Visualization")
        self.missing_generate_btn.clicked.connect(self.generate_missing_visualization)
        control_layout.addWidget(self.missing_generate_btn)
        
        control_group.setLayout(control_layout)
        
        # Visualization Area
        self.missing_plot_label = QLabel()
        self.missing_plot_label.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(control_group)
        layout.addWidget(self.missing_plot_label)
        self.missing_data_tab.setLayout(layout)
        
    def setup_outliers_tab(self):
        layout = QVBoxLayout()
        
        # Control Panel
        control_group = QGroupBox("Outlier Visualization Controls")
        control_layout = QVBoxLayout()
        
        # First row - column and method selection
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Column:"))
        self.outlier_column_combo = QComboBox()
        row1.addWidget(self.outlier_column_combo)
        
        row1.addWidget(QLabel("Method:"))
        self.outlier_method_combo = QComboBox()
        self.outlier_method_combo.addItems(["iqr", "zscore"])
        row1.addWidget(self.outlier_method_combo)
        
        row1.addWidget(QLabel("Threshold:"))
        self.outlier_threshold = QDoubleSpinBox()
        self.outlier_threshold.setRange(1.0, 5.0)
        self.outlier_threshold.setValue(1.5)
        row1.addWidget(self.outlier_threshold)
        control_layout.addLayout(row1)
        
        # Second row - plot type selection
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Plot Type:"))
        self.outlier_plot_combo = QComboBox()
        self.outlier_plot_combo.addItems(["Box Plot", "Scatter Plot"])
        row2.addWidget(self.outlier_plot_combo)
        
        # Generate Button
        self.outlier_generate_btn = QPushButton("Generate Outlier Visualization")
        self.outlier_generate_btn.clicked.connect(self.generate_outlier_visualization)
        row2.addWidget(self.outlier_generate_btn)
        control_layout.addLayout(row2)
        
        control_group.setLayout(control_layout)
        
        # Visualization Area
        self.outlier_plot_label = QLabel()
        self.outlier_plot_label.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(control_group)
        layout.addWidget(self.outlier_plot_label)
        self.outliers_tab.setLayout(layout)
    
    def update_columns(self):
        """Update column combobox when new data is loaded"""
        try:
            if hasattr(self.parent, 'df') and self.parent.df is not None:
                self.outlier_column_combo.clear()
                numeric_cols = self.parent.df.select_dtypes(
                    include=['number', 'float', 'int', 'int64', 'float64']
                ).columns.tolist()
                
                if numeric_cols:
                    self.outlier_column_combo.addItems(numeric_cols)
                    self.outlier_generate_btn.setEnabled(True)
                else:
                    self.outlier_plot_label.setText("No numeric columns found in data")
                    self.outlier_generate_btn.setEnabled(False)
            else:
                self.outlier_column_combo.clear()
                self.outlier_plot_label.setText("No data loaded")
                self.outlier_generate_btn.setEnabled(False)

            # Force UI update
            self.outlier_column_combo.update()

        except Exception as e:
            print(f"Error updating columns: {e}")
            self.parent.log_tab.add_log(f"Error updating visualiation columns: {str(e)}", level='error')
    
    def generate_missing_visualization(self):
        if self.parent.df is None:
            return
            
        view_type = self.missing_view_combo.currentText()
        plot_type = self.missing_plot_combo.currentText()
        
        fig = self.create_missing_plot(view_type, plot_type)
        self.display_plot(fig, self.missing_plot_label)
    
    def generate_outlier_visualization(self):
        if self.parent.df is None:
            return
            
        column = self.outlier_column_combo.currentText()
        plot_type = self.outlier_plot_combo.currentText().lower().replace(" ", "")
        method = self.outlier_method_combo.currentText()
        threshold = self.outlier_threshold.value()
        
        # Use detect_outliers to get the outlier mask and bounds
        analysis = detect_outliers(
            self.parent.df,
            columns=[column],
            method=method,
            threshold=threshold,
            generate_plots=False
        )
        
        if not analysis or column not in analysis:
            return
            
        stats = analysis[column]
        outlier_mask = self.parent.df.index.isin(stats['indices'])
        
        # Generate the plot using your existing function
        plots = generate_outlier_plots(
            self.parent.df,
            column,
            outlier_mask,
            stats['bounds']
        )
        
        # Display the selected plot
        if plot_type == "boxplot":
            plot_data = plots['boxplot']
        else:  # scatterplot
            plot_data = plots['scatterplot']
        
        # Convert base64 to QPixmap
        self.display_base64_plot(plot_data, self.outlier_plot_label)
     
    def create_missing_plot(self, view_type, plot_type):
        df = self.parent.df
        
        if view_type == "Column Wise":
            missing = df.isnull().sum()
            title = "Missing Values (Column Wise)"
        else:  # Row Wise
            missing = df.isnull().sum(axis=1)
            title = "Missing Values (Row Wise)"
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        if plot_type == "Bar Plot":
            missing.plot(kind='bar', ax=ax)
            ax.set_ylabel("Missing Count")
        elif plot_type == "Heatmap":
            import seaborn as sns
            sns.heatmap(df.isnull(), cbar=False, ax=ax)
        else:  # Matrix
            from missingno import matrix
            matrix(df, ax=ax)
        
        ax.set_title(title)
        plt.tight_layout()
        return fig
    
    def display_plot(self, fig, label):
        """Convert matplotlib figure to QPixmap and display in label"""
        buf = BytesIO()
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        pixmap = QPixmap()
        pixmap.loadFromData(buf.getvalue())
        label.setPixmap(pixmap.scaledToWidth(600))
        plt.close(fig)
    
    def display_base64_plot(self, base64_data, label):
        """Display a base64 encoded plot in a QLabel"""
        try:
            image_data = base64.b64decode(base64_data)
            pixmap = QPixmap()
            pixmap.loadFromData(image_data)
            label.setPixmap(pixmap.scaledToWidth(600, Qt.SmoothTransformation))
        except Exception as e:
            print(f"Error displaying plot: {e}")