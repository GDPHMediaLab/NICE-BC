#!/usr/bin/env python3
import os
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFileDialog, QFrame, QGroupBox, QSizePolicy, QApplication
)
from PySide6.QtCore import Qt, QMimeData, QUrl
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QFont, QPalette


class FileDropArea(QFrame):
    """File drop area component"""
    
    def __init__(self, label_text="", file_type="", required=False, parent=None):
        super().__init__(parent)
        self.label_text = label_text
        self.file_type = file_type
        self.required = required
        self.file_path = ""
        self.init_ui()
        
    def init_ui(self):
        """Initialize interface"""
        self.setAcceptDrops(True)
        self.setMinimumHeight(45)
        self.setMaximumHeight(45)
        
        # Main layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)
        
        # Get system palette for adaptive colors
        palette = QApplication.palette()
        text_color = palette.color(QPalette.WindowText).name()
        
        # Label
        label_text = f"{self.label_text} {'(Required)' if self.required else '(Optional)'}"
        self.type_label = QLabel(label_text)
        self.type_label.setFont(QFont("Arial", 9, QFont.Bold))
        self.type_label.setFixedWidth(120)
        if self.required:
            self.type_label.setStyleSheet("color: #d32f2f;")
        else:
            # Use system text color instead of hardcoded #666
            self.type_label.setStyleSheet(f"color: {text_color}; opacity: 0.7;")
        layout.addWidget(self.type_label)
        
        # File path display
        self.path_label = QLabel("No file selected")
        self.path_label.setWordWrap(True)
        layout.addWidget(self.path_label, 1)
        
        # Browse button
        self.browse_btn = QPushButton("Browse")
        self.browse_btn.setFixedWidth(70)
        self.browse_btn.setFixedHeight(30)
        self.browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
            QPushButton:pressed {
                background-color: #4e555b;
            }
        """)
        self.browse_btn.clicked.connect(self.browse_file)
        layout.addWidget(self.browse_btn)
        
        # Clear button
        self.clear_btn = QPushButton("×")
        self.clear_btn.setFixedSize(30, 30)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:pressed {
                background-color: #bd2130;
            }
        """)
        self.clear_btn.clicked.connect(self.clear_file)
        self.clear_btn.setVisible(False)
        layout.addWidget(self.clear_btn)
        
        # Set initial style
        self.update_style()
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Drag enter event"""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if len(urls) == 1:
                file_path = urls[0].toLocalFile()
                if self.is_valid_file(file_path):
                    event.acceptProposedAction()
                    self.setStyleSheet("""
                        QFrame {
                            border: 2px dashed #0078d4;
                            background-color: #f0f8ff;
                            border-radius: 6px;
                        }
                    """)
                    return
        event.ignore()
    
    def dragLeaveEvent(self, event):
        """Drag leave event"""
        self.update_style()
    
    def dropEvent(self, event: QDropEvent):
        """Drop event"""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if len(urls) == 1:
                file_path = urls[0].toLocalFile()
                if self.is_valid_file(file_path):
                    self.set_file_path(file_path)
                    event.acceptProposedAction()
        self.update_style()
    
    def is_valid_file(self, file_path):
        """Validate file"""
        if not os.path.exists(file_path):
            return False
        
        # Check file extension
        valid_extensions = ['.nii', '.nii.gz', '.dcm', '.mha', '.mhd', '.nrrd']
        file_ext = ''.join(Path(file_path).suffixes).lower()
        
        return any(file_ext.endswith(ext) for ext in valid_extensions)
    
    def browse_file(self):
        """Browse file"""
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter(
            "Medical Images (*.nii *.nii.gz *.dcm *.mha *.mhd *.nrrd);;All Files (*)"
        )
        
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                self.set_file_path(selected_files[0])
    
    def set_file_path(self, file_path):
        """Set file path"""
        if file_path and os.path.exists(file_path):
            self.file_path = file_path
            # Display only filename for better readability
            filename = os.path.basename(file_path)
            self.path_label.setText(filename)
            self.path_label.setToolTip(file_path)  # Show full path in tooltip
            self.clear_btn.setVisible(True)
            self.update_style()
    
    def clear_file(self):
        """Clear file"""
        self.file_path = ""
        self.path_label.setText("No file selected")
        self.path_label.setToolTip("")
        self.clear_btn.setVisible(False)
        self.update_style()
    
    def get_file_path(self):
        """Get file path"""
        return self.file_path
    
    def update_style(self):
        """Update style with system-adaptive colors"""
        # Get system palette for adaptive colors
        palette = QApplication.palette()
        base_color = palette.color(QPalette.Base).name()
        window_color = palette.color(QPalette.Window).name()
        text_color = palette.color(QPalette.WindowText).name()
        
        if self.file_path:
            # File selected style
            self.setStyleSheet("""
                QFrame {
                    border: 2px solid #28a745;
                    background-color: #f8fff8;
                    border-radius: 6px;
                }
            """)
            self.path_label.setStyleSheet("""
                QLabel {
                    background-color: #e8f5e8;
                    border: 1px solid #28a745;
                    border-radius: 4px;
                    padding: 4px 4px;
                    color: #155724;
                    font-size: 10px;
                }
            """)
        elif self.required:
            # Required but no file selected
            self.setStyleSheet("""
                QFrame {
                    border: 2px solid #dc3545;
                    background-color: #fff5f5;
                    border-radius: 6px;
                }
            """)
            self.path_label.setStyleSheet("""
                QLabel {
                    background-color: #ffeaea;
                    border: 1px solid #dc3545;
                    border-radius: 4px;
                    padding: 4px 4px;
                    color: #721c24;
                    font-size: 10px;
                }
            """)
        else:
            # Optional, no file selected (normal state) - use system colors
            self.setStyleSheet(f"""
                QFrame {{
                    border: 2px solid #dee2e6;
                    background-color: {window_color};
                    border-radius: 6px;
                }}
            """)
            self.path_label.setStyleSheet(f"""
                QLabel {{
                    background-color: {base_color};
                    border: 1px solid #dee2e6;
                    border-radius: 4px;
                    padding: 6px 8px;
                    color: {text_color};
                    font-size: 10px;
                    opacity: 0.7;
                }}
            """)


class MultiFileSelector(QGroupBox):
    """Multi-file selector component"""
    
    def __init__(self, title="Files", parent=None):
        super().__init__(f"{title} Scan", parent)
        self.title = title
        self.init_ui()
    
    def init_ui(self):
        """Initialize interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 12, 8, 8)
        layout.setSpacing(6)
        
        # Get system palette for adaptive colors
        palette = QApplication.palette()
        text_color = palette.color(QPalette.WindowText).name()
        
        # Instructions
        instruction_label = QLabel("Drag & drop files or click Browse to select:")
        instruction_label.setStyleSheet(f"""
            QLabel {{
                color: {text_color};
                font-size: 10px;
                font-style: italic;
                margin-bottom: 4px;
                opacity: 0.7;
            }}
        """)
        layout.addWidget(instruction_label)
        
        # Image file selector (required)
        self.image_selector = FileDropArea("Image", "image", required=True)
        layout.addWidget(self.image_selector)
        
        # BC file selector (now required)
        self.bc_selector = FileDropArea("BC", "bc", required=True)
        layout.addWidget(self.bc_selector)
        
        # Bone file selector (now required)
        self.bone_selector = FileDropArea("Spine", "bone", required=True)
        layout.addWidget(self.bone_selector)
        
        # Add stretch to push content to top
        layout.addStretch()
        
        # Set group box style with system-adaptive colors
        self.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                font-size: 11px;
                color: {text_color};
                border: 2px solid #dee2e6;
                border-radius: 8px;
                margin-top: 6px;
                padding-top: 6px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: {text_color};
            }}
        """)
    
    def get_file_paths(self):
        """Get all file paths"""
        return {
            'image': self.image_selector.get_file_path(),
            'bc': self.bc_selector.get_file_path(),
            'bone': self.bone_selector.get_file_path()
        }
    
    def set_file_paths(self, paths_dict):
        """Set file paths"""
        if 'image' in paths_dict and paths_dict['image']:
            self.image_selector.set_file_path(paths_dict['image'])
        
        if 'bc' in paths_dict and paths_dict['bc']:
            self.bc_selector.set_file_path(paths_dict['bc'])
        
        if 'bone' in paths_dict and paths_dict['bone']:
            self.bone_selector.set_file_path(paths_dict['bone'])
    
    def clear_all_files(self):
        """Clear all files"""
        self.image_selector.clear_file()
        self.bc_selector.clear_file()
        self.bone_selector.clear_file()
    
    def validate_required_files(self):
        """Validate required files"""
        if not self.image_selector.get_file_path():
            return False, f"{self.title} Image file is required"
        
        if not os.path.exists(self.image_selector.get_file_path()):
            return False, f"{self.title} Image file does not exist"
        
        # Validate BC file (now required)
        if not self.bc_selector.get_file_path():
            return False, f"{self.title} BC file is required"
        
        if not os.path.exists(self.bc_selector.get_file_path()):
            return False, f"{self.title} BC file does not exist"
        
        # Validate Bone file (now required)
        if not self.bone_selector.get_file_path():
            return False, f"{self.title} Bone file is required"
        
        if not os.path.exists(self.bone_selector.get_file_path()):
            return False, f"{self.title} Bone file does not exist"
        
        return True, "Validation passed"