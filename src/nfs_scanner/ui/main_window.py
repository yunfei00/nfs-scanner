from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel

class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("NFS Scanner")
        self.resize(1200, 800)

        root = QWidget()
        layout = QVBoxLayout(root)
        layout.addWidget(QLabel("Near-Field Scanning System (Commercial Skeleton)"))
        self.setCentralWidget(root)
