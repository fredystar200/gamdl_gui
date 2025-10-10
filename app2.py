import sys
import subprocess
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt

class GamdlDownloader(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Apple Music Downloader (gamdl)")
        self.setFixedSize(400, 150)
        self.setWindowIcon(QIcon())  # You can set a custom icon here

        layout = QVBoxLayout()

        label = QLabel("Enter Apple Music link:")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

        self.entry = QLineEdit()
        self.entry.setPlaceholderText("https://music.apple.com/...")
        layout.addWidget(self.entry)

        self.button = QPushButton("Download")
        self.button.clicked.connect(self.download)
        layout.addWidget(self.button)

        self.setLayout(layout)

    def download(self):
        url = self.entry.text().strip()
        if not url:
            QMessageBox.warning(self, "Input Error", "Please enter an Apple Music link.")
            return

        try:
            subprocess.run(["gamdl", url], check=True)
            QMessageBox.information(self, "Success", "Download completed successfully!")
        except subprocess.CalledProcessError as e:
            QMessageBox.critical(self, "Error", f"gamdl failed:\n{e}")
        except FileNotFoundError:
            QMessageBox.critical(self, "Error", "gamdl not found. Make sure it is installed and in PATH.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GamdlDownloader()
    window.show()
    sys.exit(app.exec())
