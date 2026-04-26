import requests
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTabWidget, QGridLayout, 
                             QScrollArea, QPushButton, QLineEdit, QFileDialog, QLabel, QFrame)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap

class FaceManagementView(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)

        # Tabs to match Figma
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #e5e7eb; background: white; border-radius: 8px; }
            QTabBar::tab { padding: 12px 20px; color: #6b7280; font-weight: 500; }
            QTabBar::tab:selected { color: #4f46e5; border-bottom: 2px solid #4f46e5; }
        """)

        # 1. Detected Faces Tab
        self.tab_detected = QWidget()
        self.setup_detected_ui()
        
        # 2. Face Training Tab
        self.tab_train = QWidget()
        self.setup_training_ui()

        self.tabs.addTab(self.tab_detected, "Detected Faces")
        self.tabs.addTab(self.tab_train, "Face Training")
        layout.addWidget(self.tabs)

    def setup_detected_ui(self):
        layout = QVBoxLayout(self.tab_detected)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        
        self.grid_widget = QWidget()
        self.grid = QGridLayout(self.grid_widget)
        self.scroll.setWidget(self.grid_widget)
        
        refresh_btn = QPushButton("Refresh Unlabeled Faces")
        refresh_btn.clicked.connect(self.load_unlabeled)
        
        layout.addWidget(refresh_btn)
        layout.addWidget(self.scroll)

    def setup_training_ui(self):
        layout = QVBoxLayout(self.tab_train)
        layout.setAlignment(Qt.AlignCenter)

        card = QFrame()
        card.setFixedWidth(400)
        card.setStyleSheet("background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 12px; padding: 20px;")
        card_layout = QVBoxLayout(card)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter person's name")
        self.name_input.setFixedHeight(40)

        self.upload_btn = QPushButton("Select Photo")
        self.upload_btn.clicked.connect(self.select_file)
        
        self.submit_btn = QPushButton("Start Training")
        self.submit_btn.setStyleSheet("background: #4f46e5; color: white; font-weight: bold; height: 40px;")
        self.submit_btn.clicked.connect(self.submit_training)

        self.status_label = QLabel("")
        self.selected_file = None

        card_layout.addWidget(QLabel("<b>Train New Face</b>"))
        card_layout.addWidget(self.name_input)
        card_layout.addWidget(self.upload_btn)
        card_layout.addWidget(self.submit_btn)
        card_layout.addWidget(self.status_label)
        layout.addWidget(card)

    def select_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Image Files (*.jpg *.png)")
        if file:
            self.selected_file = file
            self.status_label.setText(f"Selected: {file.split('/')[-1]}")

    def submit_training(self):
        if not self.selected_file or not self.name_input.text():
            return
        
        files = {'file': open(self.selected_file, 'rb')}
        data = {'name': self.name_input.text()}
        try:
            r = requests.post("http://localhost:8000/api/train", files=files, data=data)
            self.status_label.setText(r.json().get("message", "Success!"))
        except Exception as e:
            self.status_label.setText(f"Error: {e}")

    def load_unlabeled(self):
        # Implementation to fetch /api/faces/unlabeled and populate self.grid
        pass