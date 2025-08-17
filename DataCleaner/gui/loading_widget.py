from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget
from PyQt5.QtGui import QMovie
from PyQt5.QtCore import Qt

class LoadingWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        self.setFixedSize(200, 200)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.label = QLabel(self)
        self.movie = QMovie("assets/loading.gif")  # Path to GIF
        self.label.setMovie(self.movie)
        
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)
        self.setStyleSheet("background: rgba(255, 255, 255, 150); border-radius: 10px;")

    def start(self):
        self.movie.start()
        self.show()
        self.raise_()

    def stop(self):
        self.movie.stop()
        self.hide()