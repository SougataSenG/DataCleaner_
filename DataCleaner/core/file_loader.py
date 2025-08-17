from PyQt5.QtCore import QThread, pyqtSignal, QObject
import pandas as pd
import os

class FileLoaderSignals(QObject):
    progress = pyqtSignal(int)
    chunk_loaded = pyqtSignal(pd.DataFrame)
    finished = pyqtSignal()
    error = pyqtSignal(str)

class FileLoaderThread(QThread):
    def __init__(self, file_path, max_size_mb=50, chunk_size=10000):
        super().__init__()
        self.signals = FileLoaderSignals()
        self.file_path = file_path
        self.max_size_mb = max_size_mb  # This was missing
        self.chunk_size = chunk_size    # This was missing
        self._is_running = True

    def run(self):
        try:
            # 1. Check file size
            file_size = os.path.getsize(self.file_path) / (1024*1024)
            if file_size > self.max_size_mb:
                self.signals.error.emit(f"File too large ({file_size:.1f}MB > {self.max_size_mb}MB limit)")
                return

            # 2. Get total rows for progress calculation (CSV specific)
            if self.file_path.endswith('.csv'):
                with open(self.file_path, 'r') as f:
                    total_rows = sum(1 for _ in f) - 1  # Subtract header
            else:
                # For Excel, we'll estimate
                total_rows = 100000  # Default estimate

            # 3. Chunked loading
            processed_rows = 0
            if self.file_path.endswith('.csv'):
                reader = pd.read_csv(
                    self.file_path,
                    chunksize=self.chunk_size,
                    engine='c'
                )
            else:  # Excel
                reader = pd.read_excel(
                    self.file_path,
                    chunksize=self.chunk_size,
                    engine='openpyxl'
                )

            for chunk in reader:
                if not self._is_running:
                    break

                processed_rows += len(chunk)
                progress = int((processed_rows / total_rows) * 100)
                self.signals.progress.emit(progress)
                self.signals.chunk_loaded.emit(chunk.copy())

            self.signals.finished.emit()

        except Exception as e:
            self.signals.error.emit(str(e))

    def stop(self):
        self._is_running = False