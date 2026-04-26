import sys
from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                             QPushButton, QStackedWidget, QFrame, QLabel)
from PySide6.QtCore import Qt
from views.dashboard import DashboardView
from views.face_management import FaceManagementView

class SidebarButton(QPushButton):
    def __init__(self, text, icon_path=None):
        super().__init__(text)
        self.setCheckable(True)
        self.setFixedHeight(45)
        self.setStyleSheet("""
            QPushButton {
                text-align: left; padding-left: 15px; border: none;
                border-radius: 8px; color: #4b5563; font-weight: 500;
            }
            QPushButton:hover { background-color: #f3f4f6; }
            QPushButton:checked { background-color: #4f46e5; color: white; }
        """)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Photo Organizer")
        self.resize(1200, 850)
        self.setStyleSheet("QMainWindow { background-color: #f9fafb; }")

        # Main Layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Sidebar
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(240)
        self.sidebar.setStyleSheet("background-color: white; border-right: 1px solid #e5e7eb;")
        side_layout = QVBoxLayout(self.sidebar)
        side_layout.setContentsMargins(15, 30, 15, 15)

        self.btn_dash = SidebarButton(" Dashboard")
        self.btn_faces = SidebarButton(" Face Management")
        
        side_layout.addWidget(self.btn_dash)
        side_layout.addWidget(self.btn_faces)
        side_layout.addStretch()

        # Content Area
        self.content_stack = QStackedWidget()
        self.dashboard = DashboardView()
        self.face_mgmt = FaceManagementView()
        
        self.content_stack.addWidget(self.dashboard)
        self.content_stack.addWidget(self.face_mgmt)

        layout.addWidget(self.sidebar)
        layout.addWidget(self.content_stack)

        # Navigation logic
        self.btn_dash.clicked.connect(lambda: self.switch_view(0))
        self.btn_faces.clicked.connect(lambda: self.switch_view(1))
        self.btn_dash.setChecked(True)

    def switch_view(self, index):
        self.content_stack.setCurrentIndex(index)
        self.btn_dash.setChecked(index == 0)
        self.btn_faces.setChecked(index == 1)

if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())