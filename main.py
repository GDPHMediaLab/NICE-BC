#!/usr/bin/env python3
import sys
import signal
import os
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
    QGridLayout, QLabel, QLineEdit, QDoubleSpinBox, QPushButton, 
    QFileDialog, QFrame, QSplitter, QTextEdit, QMessageBox, 
    QProgressBar, QGroupBox, QFormLayout, QSpinBox, QComboBox,
    QDialog, QDialogButtonBox, QCheckBox, QSizePolicy
)
from PySide6.QtCore import Qt, QThread, Signal, QMimeData, QUrl, QProcess, QObject, QTimer
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QFont, QPalette, QTextCursor

# Import MultiFileSelector component
from multi_file_selector import MultiFileSelector

# System monitoring imports
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("Warning: psutil not available. CPU monitoring will be disabled.")

try:
    import GPUtil
    GPUTIL_AVAILABLE = True
except ImportError:
    GPUTIL_AVAILABLE = False

try:
    import nvidia_ml_py3 as pynvml
    PYNVML_AVAILABLE = True
except ImportError:
    try:
        import pynvml
        PYNVML_AVAILABLE = True
    except ImportError:
        PYNVML_AVAILABLE = False

if not GPUTIL_AVAILABLE and not PYNVML_AVAILABLE:
    print("Warning: Neither GPUtil nor nvidia-ml-py3 available. GPU monitoring will be disabled.")

# Import viewer component - from same directory
try:
    from multiviewer import MultiViewer, ViewerConfig, MultiviewerConfig, create_multiviewer
except ImportError as e:
    print(f"Warning: Could not import MultiViewer: {e}")
    MultiViewer = None

# Import core module - no longer directly imported, using process method
# try:
#     from core import run as run_core
# except ImportError as e:
#     print(f"Warning: Could not import core module: {e}")
#     run_core = None

class ConsoleWindow(QDialog):
    """Console window for displaying background running status"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Console Output")
        self.setMinimumSize(600, 400)
        self.resize(800, 500)
        
        # Layout
        layout = QVBoxLayout(self)
        
        # Control button area
        button_layout = QHBoxLayout()
        
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear_console)
        button_layout.addWidget(self.clear_btn)
        
        self.auto_scroll_checkbox = QCheckBox("Auto Scroll")
        self.auto_scroll_checkbox.setChecked(True)
        button_layout.addWidget(self.auto_scroll_checkbox)
        
        button_layout.addStretch()
        
        # Close button
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.close)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
        
        # Console text area
        self.console_text = QTextEdit()
        self.console_text.setReadOnly(True)
        self.console_text.setFont(QFont("Consolas", 10))
        self.console_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #555;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.console_text)
        
        # Set window properties
        self.setModal(False)  # Non-modal window, can operate with main window simultaneously
    
    def append_text(self, text):
        """Add text to console"""
        self.console_text.append(f"[{self.get_timestamp()}] {text}")
        
        # Auto scroll to bottom
        if self.auto_scroll_checkbox.isChecked():
            scrollbar = self.console_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
    
    def clear_console(self):
        """Clear console"""
        self.console_text.clear()
    
    def get_timestamp(self):
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")
    
    def closeEvent(self, event):
        """Override close event, hide window instead of destroying"""
        self.hide()
        event.ignore()




class ParameterInputWidget(QGroupBox):
    """Parameter input component"""
    
    def __init__(self, parent=None):
        super().__init__("Clinical Variables", parent)
        self.init_ui()
    
    def init_ui(self):
        """Initialize interface"""
        layout = QFormLayout(self)
        
        # Sex selection
        self.sex_combo = QComboBox()
        self.sex_combo.addItem("Female", 0)
        self.sex_combo.addItem("Male", 1)
        self.sex_combo.setCurrentIndex(1)  # Set default to "Male" (value=1)
        layout.addRow("Sex:", self.sex_combo)
        
        # Smoking status selection
        self.smoking_combo = QComboBox()
        self.smoking_combo.addItem("Never Smoked", 0)
        self.smoking_combo.addItem("Current Smoker", 1)
        self.smoking_combo.addItem("Former Smoker", 2)
        self.smoking_combo.setCurrentIndex(2)  # Set default to "Never Smoked" (value=0)
        layout.addRow("Smoking Status:", self.smoking_combo)
        
        # Types selection
        self.types_combo = QComboBox()
        self.types_combo.addItem("Adenocarcinoma", 1)
        self.types_combo.addItem("Squamous carcinoma", 2)
        self.types_combo.addItem("Other", 3)
        self.types_combo.setCurrentIndex(1)  # Set default to "Squamous carcinoma" (value=2)
        layout.addRow("Hist_type:", self.types_combo)
        
        # TPS selection
        self.tps_combo = QComboBox()
        self.tps_combo.addItem("TPS = 0", 0)
        self.tps_combo.addItem("TPS = 1", 1)
        layout.addRow("TPS:", self.tps_combo)
        
        # Height input (in meters)
        self.height_spinbox = QDoubleSpinBox()
        self.height_spinbox.setRange(0.0, 3.0)
        self.height_spinbox.setValue(1.66)
        self.height_spinbox.setSuffix(" m")
        self.height_spinbox.setDecimals(2)
        self.height_spinbox.setSingleStep(0.01)
        layout.addRow("Height:", self.height_spinbox)
        
        # 连接信号，监听参数变化
        self.sex_combo.currentIndexChanged.connect(self.print_current_values)
        self.smoking_combo.currentIndexChanged.connect(self.print_current_values)
        self.types_combo.currentIndexChanged.connect(self.print_current_values)
        self.tps_combo.currentIndexChanged.connect(self.print_current_values)
        self.height_spinbox.valueChanged.connect(self.print_current_values)
        
        # 打印初始值
        self.print_current_values()
    
    def print_current_values(self):
        """Print current parameter values to console"""
        params = self.get_parameters()
        print("=" * 50)
        print("Current parameter values:")
        print(f"  Sex: {params['sex']} ({'Male' if params['sex'] == 1 else 'Female'})")
        print(f"  Smoking Status: {params['smoking']} ({'Never' if params['smoking'] == 0 else 'Current' if params['smoking'] == 1 else 'Former'})")
        print(f"  Type: {params['types']} ({'Adenocarcinoma' if params['types'] == 1 else 'Squamous carcinoma' if params['types'] == 2 else 'Other'})")
        print(f"  TPS: {params['tps']}")
        print(f"  Height: {params['height']:.2f} m")
        print("=" * 50)
    
    def get_parameters(self):
        """Get parameter values"""
        return {
            'sex': self.sex_combo.currentData(),          # Return associated data value (0 or 1)
            'smoking': self.smoking_combo.currentData(),  # Return associated data value (0,1,2)
            'types': self.types_combo.currentData(),      # Return associated data value (1,2,3)
            'tps': self.tps_combo.currentData(),          # Return associated data value (0 or 1)
            'height': self.height_spinbox.value()
        }
    
    def set_parameters(self, sex=None, smoking=None, types=None, tps=None, height=None):
        """Set parameter values"""
        if sex is not None:
            # Find corresponding index based on data value
            for i in range(self.sex_combo.count()):
                if self.sex_combo.itemData(i) == sex:
                    self.sex_combo.setCurrentIndex(i)
                    break
        if smoking is not None:
            for i in range(self.smoking_combo.count()):
                if self.smoking_combo.itemData(i) == smoking:
                    self.smoking_combo.setCurrentIndex(i)
                    break
        if types is not None:
            for i in range(self.types_combo.count()):
                if self.types_combo.itemData(i) == types:
                    self.types_combo.setCurrentIndex(i)
                    break
        if tps is not None:
            for i in range(self.tps_combo.count()):
                if self.tps_combo.itemData(i) == tps:
                    self.tps_combo.setCurrentIndex(i)
                    break
        if height is not None:
            self.height_spinbox.setValue(height)


class ProcessRunner(QThread):
    """Class for running processing using QThread (replacing QProcess for Nuitka compatibility)"""
    progress_updated = Signal(int)
    status_updated = Signal(str)
    console_output = Signal(str)
    finished_signal = Signal(bool, str)
    result_path_generated = Signal(str, str)  # New signal: type, path
    y_value_generated = Signal(str)  # New signal: Y value
    
    def __init__(self, image_path1, image_path2, parameters, preprocessed_files, parent=None):
        super().__init__(parent)
        self.image_path1 = image_path1
        self.image_path2 = image_path2
        self.parameters = parameters
        self.preprocessed_files = preprocessed_files  # Now required, not optional
        self._stop_requested = False
        
        # Store generated paths
        self.generated_paths = {
            'pre_bc_path': None,
            'pre_bone_path': None,
            'post_bc_path': None,
            'post_bone_path': None,
            'pre_results_path': None,
            'post_results_path': None
        }
    
    def start_processing(self):
        """Start processing"""
        if self.isRunning():
            return  # Thread already running
        
        self.status_updated.emit("Preparing to start processing...")
        self.console_output.emit("=== Preparing to start processing ===")
        self.progress_updated.emit(5)
        
        # Check if image files exist
        if not os.path.exists(self.image_path1):
            error_msg = f"Pre image file not found: {self.image_path1}"
            self.console_output.emit(error_msg)
            self.finished_signal.emit(False, error_msg)
            return
            
        if not os.path.exists(self.image_path2):
            error_msg = f"Post image file not found: {self.image_path2}"
            self.console_output.emit(error_msg)
            self.finished_signal.emit(False, error_msg)
            return
        
        # Check preprocessed files
        if self.preprocessed_files:
            if 'pre_bc' in self.preprocessed_files and self.preprocessed_files['pre_bc']:
                self.console_output.emit(f"Using pre BC file: {self.preprocessed_files['pre_bc']}")
            else:
                self.console_output.emit("Error: Pre BC file is required but not provided")
                self.finished_signal.emit(False, "Pre BC file is required but not provided")
                return
                
            if 'pre_bone' in self.preprocessed_files and self.preprocessed_files['pre_bone']:
                self.console_output.emit(f"Using pre bone file: {self.preprocessed_files['pre_bone']}")
            else:
                self.console_output.emit("Error: Pre bone file is required but not provided")
                self.finished_signal.emit(False, "Pre bone file is required but not provided")
                return
                
            if 'post_bc' in self.preprocessed_files and self.preprocessed_files['post_bc']:
                self.console_output.emit(f"Using post BC file: {self.preprocessed_files['post_bc']}")
            else:
                self.console_output.emit("Error: Post BC file is required but not provided")
                self.finished_signal.emit(False, "Post BC file is required but not provided")
                return
                
            if 'post_bone' in self.preprocessed_files and self.preprocessed_files['post_bone']:
                self.console_output.emit(f"Using post bone file: {self.preprocessed_files['post_bone']}")
            else:
                self.console_output.emit("Error: Post bone file is required but not provided")
                self.finished_signal.emit(False, "Post bone file is required but not provided")
                return
        else:
            self.console_output.emit("Error: No preprocessed files provided")
            self.finished_signal.emit(False, "BC and Bone files are required")
            return
        
        self.console_output.emit(f"Required preprocessed files: {self.preprocessed_files}")
        self.status_updated.emit("Starting processing...")
        self.progress_updated.emit(10)
        
        # Start the thread
        self.start()
    
    def run(self):
        """Thread run method"""
        try:
            self.console_output.emit("Starting processing...")
            
            # Import core module
            try:
                from core import run
                self.console_output.emit("Successfully imported core module")
            except ImportError as e:
                error_msg = f"Failed to import core module: {e}"
                self.console_output.emit(error_msg)
                self.finished_signal.emit(False, error_msg)
                return
            
            # Redirect print output to our signal
            import sys
            from io import StringIO
            
            class SignalStream:
                def __init__(self, signal, thread_instance):
                    self.signal = signal
                    self.thread_instance = thread_instance
                    self.buffer = ""
                
                def write(self, text):
                    if text and text.strip():
                        # Handle callback messages
                        if "callback@" in text:
                            parts = text.strip().split("@")
                            if len(parts) == 3:
                                path_type = parts[1]
                                path_value = parts[2]
                                self.signal.emit(f"Detected path generation: {path_type} -> {path_value}")
                                self.thread_instance.result_path_generated.emit(path_type, path_value)
                                if path_type == "y":
                                    self.thread_instance.y_value_generated.emit(path_value)
                            return
                        
                        self.signal.emit(text.strip())
                        
                        # Update progress based on output
                        self._update_progress_from_output(text.strip())
                
                def flush(self):
                    pass
                
                def _update_progress_from_output(self, line):
                    """Update progress based on output"""
                    line_lower = line.lower()
                    
                    if "starting processing task" in line_lower:
                        self.thread_instance.progress_updated.emit(15)
                    elif "calculating file md5" in line_lower:
                        self.thread_instance.progress_updated.emit(25)
                    elif "checking segmentation files" in line_lower:
                        self.thread_instance.progress_updated.emit(35)
                    elif "calculating pre phase metrics" in line_lower:
                        self.thread_instance.progress_updated.emit(45)
                    elif "calculating post phase metrics" in line_lower:
                        self.thread_instance.progress_updated.emit(75)
                    elif "calculating final result" in line_lower:
                        self.thread_instance.progress_updated.emit(90)
                    elif "processing task complete" in line_lower:
                        self.thread_instance.progress_updated.emit(100)
            
            # Temporarily redirect stdout
            original_stdout = sys.stdout
            signal_stream = SignalStream(self.console_output, self)
            sys.stdout = signal_stream
            
            try:
                # Execute processing
                self.console_output.emit("Starting core processing...")
                result = run(self.image_path1, self.image_path2, self.parameters, self.preprocessed_files)
                self.console_output.emit(f"Processing result: {result}")
                self.console_output.emit("Processing completed successfully")
                
                # Emit the final result
                self.y_value_generated.emit(str(result))
                
                self.finished_signal.emit(True, "Processing completed successfully")
                
            finally:
                # Restore stdout
                sys.stdout = original_stdout
                
        except Exception as e:
            import traceback
            error_msg = f"Error during processing: {str(e)}"
            self.console_output.emit(error_msg)
            self.console_output.emit(traceback.format_exc())
            self.finished_signal.emit(False, error_msg)
    
    def stop_processing(self):
        """Stop processing thread"""
        if self.isRunning():
            self.console_output.emit("Stopping processing...")
            self._stop_requested = True
            self.quit()
            if self.wait(3000):
                self.console_output.emit("Process stopped")
            else:
                self.console_output.emit("Forcefully stopping process")
                self.terminate()
                self.wait()


class ResultDisplayWidget(QGroupBox):
    """Result display component"""
    
    def __init__(self, parent=None):
        super().__init__("Processing Results", parent)
        # 设置一致的字体大小，与Visualization面板保持一致
        self.setStyleSheet("QGroupBox { font-size: 12px; }")
        self.init_ui()
    
    def init_ui(self):
        """Initialize interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)  # Reduce top and bottom margins
        layout.setSpacing(8)  # Reduce spacing
        
        # Result value display area
        result_layout = QHBoxLayout()
        
        # Y value display
        self.y_label = QLabel("pCR Probability:")
        self.y_label.setFont(QFont("Arial", 10, QFont.Bold))
        result_layout.addWidget(self.y_label)
        
        self.y_value_label = QLabel("Calculating...")
        self.y_value_label.setStyleSheet("""
            QLabel {
                background-color: #f0f8ff;
                border: 1px solid #0078d4;
                border-radius: 4px;
                padding: 5px 10px;
                font-size: 12px;
                font-weight: bold;
                color: #0078d4;
            }
        """)
        result_layout.addWidget(self.y_value_label)
        
        # Clinical Cut-off display
        self.cutoff_label = QLabel("Clinical Cut-off: 0.463")
        self.cutoff_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.cutoff_label.setStyleSheet("""
            QLabel {
                background-color: #fff3e0;
                border: 1px solid #ff9800;
                border-radius: 4px;
                padding: 5px 10px;
                font-size: 12px;
                font-weight: bold;
                color: #e65100;
                margin-left: 10px;
            }
        """)
        result_layout.addWidget(self.cutoff_label)
        
        result_layout.addStretch()
        layout.addLayout(result_layout)
        
        # Compact color label description area
        color_layout = QHBoxLayout()
        color_layout.setSpacing(3)  # Reduce spacing
        
        # Title
        color_title = QLabel("Labels:")
        color_title.setFont(QFont("Arial", 9, QFont.Bold))
        color_layout.addWidget(color_title)
        
        # Predefined color labels (based on BC segmentation actual labels and label2rgb default color scheme)
        self.color_info = [
            {"label": 1, "name": "Muscle", "color": "#ff0000"},      # Red
            {"label": 2, "name": "IMAT (Inter-muscular Adipose Tissue)", "color": "#0000ff"},    # Green
            {"label": 3, "name": "VAT (Visceral Adipose Tissue)", "color": "#ffff00"},     # Blue
            {"label": 4, "name": "SAT (Subcutaneous Adipose Tissue)", "color": "#ff00ff"},     # Yellow
            {"label": 5, "name": "Bone", "color": "#008000"}         # Cyan
        ]
        
        # 创建紧凑的圆形颜色标签
        for info in self.color_info:
            # 创建圆形颜色标签
            color_circle = QLabel()
            color_circle.setFixedSize(18, 18)  # 小圆形
            color_circle.setStyleSheet(f"""
                QLabel {{
                    background-color: {info['color']};
                    border: 1px solid #333;
                    border-radius: 9px;  /* 圆形 */
                    font-size: 8px;
                    color: white;
                    font-weight: bold;
                }}
            """)
            color_circle.setAlignment(Qt.AlignCenter)
            # 移除数字显示，只显示纯色圆形
            # color_circle.setText(str(info['label']))  # 注释掉数字显示
            
            # 设置tooltip显示详细信息
            color_circle.setToolTip(f"Label {info['label']}: {info['name']}")
            
            color_layout.addWidget(color_circle)
        
        # 添加鼠标悬停提示说明
        hint_label = QLabel("(Hover for details)")
        hint_label.setStyleSheet("QLabel { color: #999; font-size: 8px; font-style: italic; }")
        color_layout.addWidget(hint_label)
        
        color_layout.addStretch()  # 右侧弹性空间
        layout.addLayout(color_layout)
        
        # 设置整个组件的最大高度 - 大幅减小
        self.setMaximumHeight(85)  # 从220减少到85
    
    def update_y_value(self, y_value):
        """Update Y value display"""
        try:
            # Try to convert y_value to float and format for display
            if isinstance(y_value, (int, float)):
                formatted_value = f"{float(y_value):.6f}"
            else:
                # If it's a string, try to convert
                formatted_value = f"{float(y_value):.6f}"
            
            self.y_value_label.setText(formatted_value)
            self.y_value_label.setStyleSheet("""
                QLabel {
                    background-color: #e8f5e8;
                    border: 1px solid #28a745;
                    border-radius: 4px;
                    padding: 5px 10px;
                    font-size: 12px;
                    font-weight: bold;
                    color: #28a745;
                }
            """)
        except (ValueError, TypeError) as e:
            # If conversion fails, just display the original value
            self.y_value_label.setText(str(y_value))
            self.y_value_label.setStyleSheet("""
                QLabel {
                    background-color: #fff3cd;
                    border: 1px solid #ffc107;
                    border-radius: 4px;
                    padding: 5px 10px;
                    font-size: 12px;
                    font-weight: bold;
                    color: #856404;
                }
            """)
    
    def reset_display(self):
        """Reset display"""
        self.y_value_label.setText("Calculating...")
        self.y_value_label.setStyleSheet("""
            QLabel {
                background-color: #f0f8ff;
                border: 1px solid #0078d4;
                border-radius: 4px;
                padding: 5px 10px;
                font-size: 12px;
                font-weight: bold;
                color: #0078d4;
            }
        """)


class SystemMonitorWidget(QGroupBox):
    """System monitor component showing CPU and GPU usage"""
    
    def __init__(self, parent=None):
        super().__init__("System Monitor", parent)
        self.init_ui()
        self.init_monitoring()
    
    def init_ui(self):
        """Initialize interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        
        # CPU usage display
        cpu_layout = QHBoxLayout()
        cpu_layout.setContentsMargins(0, 0, 0, 0)
        
        cpu_label = QLabel("CPU:")
        cpu_label.setFont(QFont("Arial", 9, QFont.Bold))
        cpu_label.setFixedWidth(35)
        cpu_layout.addWidget(cpu_label)
        
        self.cpu_value = QLabel("---%")
        self.cpu_value.setStyleSheet("""
            QLabel {
                background-color: #f0f8ff;
                border: 1px solid #0078d4;
                border-radius: 3px;
                padding: 2px 8px;
                font-size: 10px;
                font-weight: bold;
                color: #0078d4;
                min-width: 50px;
            }
        """)
        cpu_layout.addWidget(self.cpu_value)
        
        # CPU progress bar
        self.cpu_progress = QProgressBar()
        self.cpu_progress.setRange(0, 100)
        self.cpu_progress.setFixedHeight(12)
        self.cpu_progress.setTextVisible(False)
        self.cpu_progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ccc;
                border-radius: 3px;
                background-color: #f0f0f0;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4CAF50, stop:0.7 #FFC107, stop:1 #F44336);
                border-radius: 2px;
            }
        """)
        cpu_layout.addWidget(self.cpu_progress)
        
        layout.addLayout(cpu_layout)
        
        # GPU memory display
        gpu_layout = QHBoxLayout()
        gpu_layout.setContentsMargins(0, 0, 0, 0)
        
        gpu_label = QLabel("GPU:")
        gpu_label.setFont(QFont("Arial", 9, QFont.Bold))
        gpu_label.setFixedWidth(35)
        gpu_layout.addWidget(gpu_label)
        
        self.gpu_value = QLabel("--- MB")
        self.gpu_value.setStyleSheet("""
            QLabel {
                background-color: #f0f8ff;
                border: 1px solid #0078d4;
                border-radius: 3px;
                padding: 2px 8px;
                font-size: 10px;
                font-weight: bold;
                color: #0078d4;
                min-width: 50px;
            }
        """)
        gpu_layout.addWidget(self.gpu_value)
        
        # GPU progress bar
        self.gpu_progress = QProgressBar()
        self.gpu_progress.setRange(0, 100)
        self.gpu_progress.setFixedHeight(12)
        self.gpu_progress.setTextVisible(False)
        self.gpu_progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ccc;
                border-radius: 3px;
                background-color: #f0f0f0;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2196F3, stop:0.7 #FF9800, stop:1 #F44336);
                border-radius: 2px;
            }
        """)
        gpu_layout.addWidget(self.gpu_progress)
        
        layout.addLayout(gpu_layout)
        
        # Set fixed height for compact display
        self.setMaximumHeight(85)
        
        # Initialize GPU monitoring if available
        self.gpu_available = False
        self.gpu_count = 0
        
        if PYNVML_AVAILABLE:
            try:
                if 'nvidia_ml_py3' in sys.modules:
                    import nvidia_ml_py3 as pynvml
                else:
                    import pynvml
                pynvml.nvmlInit()
                self.pynvml = pynvml
                self.gpu_available = True
                self.gpu_count = pynvml.nvmlDeviceGetCount()
                print(f"NVIDIA-ML initialized successfully. Found {self.gpu_count} GPU(s)")
            except Exception as e:
                print(f"NVIDIA-ML initialization failed: {e}")
                self.gpu_available = False
        
        if not self.gpu_available and GPUTIL_AVAILABLE:
            try:
                import GPUtil
                gpus = GPUtil.getGPUs()
                if gpus:
                    self.gpu_available = True
                    self.gpu_count = len(gpus)
                    print(f"GPUtil initialized successfully. Found {self.gpu_count} GPU(s)")
                else:
                    print("GPUtil: No GPUs found")
            except Exception as e:
                print(f"GPUtil initialization failed: {e}")
                self.gpu_available = False
        
        if not self.gpu_available:
            print("No GPU monitoring available")
    
    def init_monitoring(self):
        """Initialize monitoring timer"""
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.update_system_info)
        self.monitor_timer.start(2000)  # Update every 2 seconds
    
    def update_system_info(self):
        """Update system information"""
        # Update CPU usage
        if PSUTIL_AVAILABLE:
            try:
                cpu_percent = psutil.cpu_percent(interval=0.1)
                self.cpu_value.setText(f"{cpu_percent:.1f}%")
                self.cpu_progress.setValue(int(cpu_percent))
                
                # Update CPU label color based on usage
                if cpu_percent < 50:
                    color = "#4CAF50"  # Green
                elif cpu_percent < 80:
                    color = "#FFC107"  # Yellow
                else:
                    color = "#F44336"  # Red
                
                self.cpu_value.setStyleSheet(f"""
                    QLabel {{
                        background-color: {color}20;
                        border: 1px solid {color};
                        border-radius: 3px;
                        padding: 2px 8px;
                        font-size: 10px;
                        font-weight: bold;
                        color: {color};
                        min-width: 50px;
                    }}
                """)
            except Exception as e:
                self.cpu_value.setText("Error")
                print(f"CPU monitoring error: {e}")
        
        # Update GPU memory usage
        if self.gpu_available:
            try:
                if GPUTIL_AVAILABLE:
                    gpus = GPUtil.getGPUs()
                    if gpus:
                        gpu = gpus[0]  # Use first GPU
                        used_mb = gpu.memoryUsed
                        total_mb = gpu.memoryTotal
                        usage_percent = (used_mb / total_mb) * 100
                        
                        self.gpu_value.setText(f"{used_mb:.0f}/{total_mb:.0f} MB")
                        self.gpu_progress.setValue(int(usage_percent))
                elif PYNVML_AVAILABLE:
                    handle = self.pynvml.nvmlDeviceGetHandleByIndex(0)  # Use first GPU
                    info = self.pynvml.nvmlDeviceGetMemoryInfo(handle)
                    used_mb = info.used // 1024 // 1024
                    total_mb = info.total // 1024 // 1024
                    usage_percent = (info.used / info.total) * 100
                    
                    self.gpu_value.setText(f"{used_mb}/{total_mb} MB")
                    self.gpu_progress.setValue(int(usage_percent))
                
                # Update GPU label color based on usage
                if usage_percent < 50:
                    color = "#2196F3"  # Blue
                elif usage_percent < 80:
                    color = "#FF9800"  # Orange
                else:
                    color = "#F44336"  # Red
                
                self.gpu_value.setStyleSheet(f"""
                    QLabel {{
                        background-color: {color}20;
                        border: 1px solid {color};
                        border-radius: 3px;
                        padding: 2px 8px;
                        font-size: 10px;
                        font-weight: bold;
                        color: {color};
                        min-width: 50px;
                    }}
                """)
                
            except Exception as e:
                self.gpu_value.setText("No GPU")
                self.gpu_progress.setValue(0)
        else:
            self.gpu_value.setText("N/A")
            self.gpu_progress.setValue(0)


class LeftPanel(QWidget):
    """Left control panel"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.timer = QTimer()  # Add timer for elapsed time tracking
        self.start_time = 0  # Record start time
        self.timer.timeout.connect(self.update_elapsed_time)  # Connect timer signal
        self.init_ui()
    
    def init_ui(self):
        """Initialize interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Parameter input area
        self.param_widget = ParameterInputWidget()
        layout.addWidget(self.param_widget)
        
        # File selection area
        file_group = QGroupBox("Image Upload")
        file_group.setMaximumHeight(420)  # Increased from 280 to 420 to accommodate proper display
        file_layout = QVBoxLayout(file_group)
        file_layout.setContentsMargins(8, 8, 8, 8)  # Increased margins
        file_layout.setSpacing(12)  # Increased spacing for better visibility
        
        # First file selector - Pre
        self.file_selector1 = MultiFileSelector("Pre-treatment")
        self.file_selector1.setMinimumHeight(180)  # Increased from 120 to 180 for proper display
        file_layout.addWidget(self.file_selector1)
        
        # Second file selector - Post
        self.file_selector2 = MultiFileSelector("Post-treatment")
        self.file_selector2.setMinimumHeight(180)  # Increased from 120 to 180 for proper display
        file_layout.addWidget(self.file_selector2)
        
        layout.addWidget(file_group)
        
        # Control button area
        control_group = QGroupBox("Processing")
        control_group.setMaximumHeight(120)  # Set maximum height to make it more compact
        control_layout = QVBoxLayout(control_group)
        control_layout.setContentsMargins(6, 6, 6, 6)  # Reduced margins
        control_layout.setSpacing(6)  # Reduced spacing
        
        # Button layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(6)  # Reduced spacing
        
        self.run_btn = QPushButton("Run")
        self.run_btn.setMinimumHeight(35)  # Reduced from 40 to 35
        self.run_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
            QPushButton:disabled {
                background-color: #ccc;
                color: #666;
            }
        """)
        button_layout.addWidget(self.run_btn)
        
        self.console_btn = QPushButton("Console")
        self.console_btn.setMinimumHeight(35)  # Reduced from 40 to 35
        self.console_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        button_layout.addWidget(self.console_btn)
        
        control_layout.addLayout(button_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedHeight(8)  # Make progress bar thinner
        control_layout.addWidget(self.progress_bar)
        
        # Status and timer layout
        status_timer_layout = QHBoxLayout()
        status_timer_layout.setContentsMargins(0, 0, 0, 0)
        status_timer_layout.setSpacing(6)
        
        # Status display
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.status_label.setStyleSheet("color: #666; font-style: italic; font-size: 10px;")  # Smaller font
        status_timer_layout.addWidget(self.status_label)
        
        # Spacer
        status_timer_layout.addStretch()
        
        # Timer display
        self.timer_label = QLabel("00:00:00")
        self.timer_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.timer_label.setStyleSheet("""
            QLabel {
                color: #0078d4;
                font-family: 'Courier New', monospace;
                font-size: 10px;
                font-weight: bold;
                background-color: #f0f8ff;
                border: 1px solid #0078d4;
                border-radius: 3px;
                padding: 1px 4px;
            }
        """)
        self.timer_label.setVisible(False)  # Initially hidden
        status_timer_layout.addWidget(self.timer_label)
        
        control_layout.addLayout(status_timer_layout)
        
        layout.addWidget(control_group)
        
        # System monitor area
        self.system_monitor = SystemMonitorWidget()
        layout.addWidget(self.system_monitor)
        
        # Spring to push content to top
        layout.addStretch()
    
    def start_timer(self):
        """Start timer"""
        from time import time
        self.start_time = time()
        self.timer_label.setVisible(True)
        self.timer_label.setText("00:00:00")
        # Set running style
        self.timer_label.setStyleSheet("""
            QLabel {
                color: #0078d4;
                font-family: 'Courier New', monospace;
                font-size: 10px;
                font-weight: bold;
                background-color: #f0f8ff;
                border: 1px solid #0078d4;
                border-radius: 3px;
                padding: 1px 4px;
            }
        """)
        self.timer.start(1000)  # Update every second
    
    def stop_timer(self, success=True):
        """Stop timer"""
        self.timer.stop()
        # Don't hide the timer, just update its style to show it's completed
        if success:
            # Green style for successful completion
            self.timer_label.setStyleSheet("""
                QLabel {
                    color: #28a745;
                    font-family: 'Courier New', monospace;
                    font-size: 10px;
                    font-weight: bold;
                    background-color: #e8f5e8;
                    border: 1px solid #28a745;
                    border-radius: 3px;
                    padding: 1px 4px;
                }
            """)
        else:
            # Red style for failed completion
            self.timer_label.setStyleSheet("""
                QLabel {
                    color: #dc3545;
                    font-family: 'Courier New', monospace;
                    font-size: 10px;
                    font-weight: bold;
                    background-color: #ffeaea;
                    border: 1px solid #dc3545;
                    border-radius: 3px;
                    padding: 1px 4px;
                }
            """)
    
    def update_elapsed_time(self):
        """Update elapsed time display"""
        from time import time
        if self.start_time > 0:
            elapsed = int(time() - self.start_time)
            hours = elapsed // 3600
            minutes = (elapsed % 3600) // 60
            seconds = elapsed % 60
            time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            self.timer_label.setText(time_str)
    
    def get_input_data(self):
        """Get all input data"""
        return {
            'parameters': self.param_widget.get_parameters(),
            'file1': self.file_selector1.get_file_paths(),
            'file2': self.file_selector2.get_file_paths()
        }
    
    def validate_inputs(self):
        """Validate inputs"""
        data = self.get_input_data()
        
        if not data['file1']['image']:
            return False, "Please select Pre image file"
        
        if not data['file2']['image']:
            return False, "Please select Post image file"
        
        # Make BC and Bone files required
        if not data['file1']['bc']:
            return False, "Please select Pre BC segmentation file (Required)"
        
        if not data['file1']['bone']:
            return False, "Please select Pre Bone segmentation file (Required)"
        
        if not data['file2']['bc']:
            return False, "Please select Post BC segmentation file (Required)"
        
        if not data['file2']['bone']:
            return False, "Please select Post Bone segmentation file (Required)"
        
        if not os.path.exists(data['file1']['image']):
            return False, f"Pre image file does not exist: {data['file1']['image']}"
        
        if not os.path.exists(data['file2']['image']):
            return False, f"Post image file does not exist: {data['file2']['image']}"
        
        # Validate BC and Bone files exist
        if not os.path.exists(data['file1']['bc']):
            return False, f"Pre BC file does not exist: {data['file1']['bc']}"
        
        if not os.path.exists(data['file1']['bone']):
            return False, f"Pre Bone file does not exist: {data['file1']['bone']}"
        
        if not os.path.exists(data['file2']['bc']):
            return False, f"Post BC file does not exist: {data['file2']['bc']}"
        
        if not os.path.exists(data['file2']['bone']):
            return False, f"Post Bone file does not exist: {data['file2']['bone']}"
        
        return True, "Validation passed"


class RightPanel(QWidget):
    """Right display panel"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_widget = None
        self.result_display = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize interface"""
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(5)  # Reduce spacing from 10 to 5
        
        # Result display component
        self.result_display = ResultDisplayWidget()
        self.result_display.setVisible(False)  # Initially hidden
        self.layout.addWidget(self.result_display)
        
        # Default display placeholder
        self.placeholder_label = QLabel("Processing results will be displayed here")
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        self.placeholder_label.setStyleSheet("""
            QLabel {
                color: #999;
                font-size: 16px;
                font-style: italic;
                border: 2px dashed #ddd;
                border-radius: 8px;
                padding: 50px;
            }
        """)
        self.layout.addWidget(self.placeholder_label)
    
    def set_widget(self, widget):
        """Set widget to display"""
        # Clear current widget
        if self.current_widget:
            self.layout.removeWidget(self.current_widget)
            self.current_widget.setParent(None)
        
        # Hide placeholder
        self.placeholder_label.setVisible(False)
        
        # Show result display component
        self.result_display.setVisible(True)
        
        # Add new widget
        self.current_widget = widget
        self.layout.addWidget(widget)
        widget.show()
    
    def clear_widget(self):
        """Clear current widget, show placeholder"""
        if self.current_widget:
            self.layout.removeWidget(self.current_widget)
            self.current_widget.setParent(None)
            self.current_widget = None
        
        # Hide result display component and reset
        if self.result_display:
            self.result_display.setVisible(False)
            self.result_display.reset_display()
        
        self.placeholder_label.setVisible(True)
    
    def update_result_display(self, y_value):
        """Update result display"""
        if self.result_display:
            self.result_display.update_y_value(y_value)


class MedicalImageApp(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.process_runner = None  # Changed to process_runner
        self.console_window = None  # Console window
        self.viewer = None  # Store viewer reference
        self.init_ui()
    
    def init_ui(self):
        """Initialize interface"""
        self.setWindowTitle("NICE-BC")
        self.setMinimumSize(1200, 800)
        
        # Create console window
        self.console_window = ConsoleWindow(self)
        
        # Central component
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout - horizontal splitter
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel
        self.left_panel = LeftPanel()
        self.left_panel.setMaximumWidth(350)
        self.left_panel.setMinimumWidth(300)
        splitter.addWidget(self.left_panel)
        
        # Right panel
        self.right_panel = RightPanel()
        splitter.addWidget(self.right_panel)
        
        # Set splitter proportions
        splitter.setStretchFactor(0, 0)  # Left side does not stretch
        splitter.setStretchFactor(1, 1)  # Right side can stretch
        
        # Connect signals
        self.left_panel.run_btn.clicked.connect(self.start_processing)
        self.left_panel.console_btn.clicked.connect(self.show_console)
    
    def start_processing(self):
        """Start processing"""
        # Validate input
        is_valid, message = self.left_panel.validate_inputs()
        if not is_valid:
            QMessageBox.warning(self, "Input Error", message)
            return
        
        # Get input data
        data = self.left_panel.get_input_data()
        
        # Disable run button and start timer
        self.left_panel.run_btn.setEnabled(False)
        self.left_panel.progress_bar.setVisible(True)
        self.left_panel.progress_bar.setValue(0)
        self.left_panel.start_timer()  # Start timing
        
        # Clear previous viewer
        self.right_panel.clear_widget()
        
        # Extract preprocessed files from file selectors
        preprocessed_files = {}
        
        # Get Pre BC and Bone files if selected
        if data['file1']['bc']:  # Pre BC file
            preprocessed_files['pre_bc'] = data['file1']['bc']
            self.console_window.append_text(f"Using Pre BC file: {data['file1']['bc']}")
        
        if data['file1']['bone']:  # Pre Bone file
            preprocessed_files['pre_bone'] = data['file1']['bone']
            self.console_window.append_text(f"Using Pre Bone file: {data['file1']['bone']}")
        
        # Get Post BC and Bone files if selected
        if data['file2']['bc']:  # Post BC file
            preprocessed_files['post_bc'] = data['file2']['bc']
            self.console_window.append_text(f"Using Post BC file: {data['file2']['bc']}")
        
        if data['file2']['bone']:  # Post Bone file
            preprocessed_files['post_bone'] = data['file2']['bone']
            self.console_window.append_text(f"Using Post Bone file: {data['file2']['bone']}")
        
        # Log the preprocessed files being used
        if preprocessed_files:
            self.console_window.append_text(f"Required preprocessed files: {preprocessed_files}")
        else:
            self.console_window.append_text("Error: All BC and Bone files are required")
        
        # Create processing thread
        self.process_runner = ProcessRunner(
            data['file1']['image'], 
            data['file2']['image'], 
            data['parameters'],
            preprocessed_files  # Pass the required preprocessed files
        )
        
        # Connect signals
        self.process_runner.progress_updated.connect(
            self.left_panel.progress_bar.setValue
        )
        self.process_runner.status_updated.connect(
            self.left_panel.status_label.setText
        )
        self.process_runner.console_output.connect(
            self.console_window.append_text
        )
        self.process_runner.finished_signal.connect(
            self.on_processing_finished
        )
        self.process_runner.result_path_generated.connect(
            self.on_result_path_generated
        )
        self.process_runner.y_value_generated.connect(
            self.on_y_value_generated
        )
        
        # Initialize viewer
        self.init_viewer_component()
        
        # Start thread
        self.process_runner.start_processing()
    
    def on_result_path_generated(self, path_type, path_value):
        """Callback when result path is generated"""
        if self.viewer is None:
            return
        
        # Check if the file really exists
        if not os.path.exists(path_value):
            return
        
        # Get input data
        data = self.left_panel.get_input_data()
        
        try:
            # Update corresponding viewer based on path type
            if path_type == 'pre_bc_path':
                # Update pre bc result (first row)
                self.update_viewer_for_pre_bc(data['file1']['image'], path_value)
            elif path_type == 'post_bc_path':
                # Update post bc result (second row)
                self.update_viewer_for_post_bc(data['file2']['image'], path_value)
        except Exception as e:
            self.console_window.append_text(f"Error updating viewer: {str(e)}")
    
    def init_viewer_component(self):
        """Initialize viewer component"""
        if MultiViewer is None:
            placeholder = QLabel("MultiViewer component not available\nPlease check multiviewer.py file path")
            placeholder.setAlignment(Qt.AlignCenter)
            placeholder.setStyleSheet("""
                QLabel {
                    color: #d32f2f;
                    font-size: 14px;
                    border: 2px solid #d32f2f;
                    border-radius: 8px;
                    padding: 20px;
                    background-color: #ffeaea;
                }
            """)
            self.right_panel.set_widget(placeholder)
            return

        try:
            # Create empty viewer configuration list (2 rows 3 columns = 6 positions)
            viewers = [None] * 6  # Initialize all to None, will be dynamically loaded later
            
            # Create MultiViewer configuration
            config = MultiviewerConfig(
                row=2,
                col=3,
                width=800,
                height=600,
                viewers=viewers,
                mask_alpha=0.5
            )
            
            # Create MultiViewer component
            self.viewer = create_multiviewer(config)
            
            # Set viewer minimum size
            self.viewer.setMinimumSize(800, 600)
            
            # Set to right panel
            self.right_panel.set_widget(self.viewer)
            
            # Ensure correct initial layout
            from PySide6.QtWidgets import QApplication
            QApplication.processEvents()
            QTimer.singleShot(100, lambda: self._initial_viewer_setup())
            
        except Exception as e:
            error_label = QLabel(f"Error initializing viewer:\n{str(e)}")
            error_label.setAlignment(Qt.AlignCenter)
            error_label.setStyleSheet("""
                QLabel {
                    color: #d32f2f;
                    font-size: 12px;
                    border: 1px solid #d32f2f;
                    border-radius: 4px;
                    padding: 15px;
                    background-color: #ffeaea;
                }
            """)
            self.right_panel.set_widget(error_label)
    
    def _initial_viewer_setup(self):
        """Initial viewer setup"""
        if self.viewer is None:
            return
        
        try:
            # Ensure viewer layout is correct
            self.viewer.update()
            
        except Exception as e:
            self.console_window.append_text(f"Error in initial viewer setup: {str(e)}")
    
    def update_viewer_for_pre_bc(self, original_image_path, bc_mask_path):
        """Update Pre bc result display"""
        if self.viewer is None:
            return
        
        try:
            # Update first row (Pre) three viewers, each displaying different axial directions
            
            # Position 0: Axial (first row first column)
            axial_config = ViewerConfig(
                image_path=original_image_path,
                mask_path=bc_mask_path,
                direction="axial",
                title="Pre - Body Composition (Axial)"
            )
            self.viewer.update_viewer(0, axial_config)
            
            # Position 1: Coronal (first row second column)
            coronal_config = ViewerConfig(
                image_path=original_image_path,
                mask_path=bc_mask_path,
                direction="coronal",
                title="Pre - Body Composition (Coronal)"
            )
            self.viewer.update_viewer(1, coronal_config)
            
            # Position 2: Sagittal (first row third column)
            sagittal_config = ViewerConfig(
                image_path=original_image_path,
                mask_path=bc_mask_path,
                direction="sagittal",
                title="Pre - Body Composition (Sagittal)"
            )
            self.viewer.update_viewer(2, sagittal_config)
            
            self.console_window.append_text("Pre BC result updated to viewer")
            
        except Exception as e:
            self.console_window.append_text(f"Error updating Pre BC viewer: {str(e)}")
    
    def update_viewer_for_post_bc(self, original_image_path, bc_mask_path):
        """Update Post bc result display"""
        if self.viewer is None:
            return
        
        try:
            # Update second row (Post) three viewers, each displaying different axial directions
            
            # Position 3: Axial (second row first column)
            axial_config = ViewerConfig(
                image_path=original_image_path,
                mask_path=bc_mask_path,
                direction="axial",
                title="Post - Body Composition (Axial)"
            )
            self.viewer.update_viewer(3, axial_config)
            
            # Position 4: Coronal (second row second column)
            coronal_config = ViewerConfig(
                image_path=original_image_path,
                mask_path=bc_mask_path,
                direction="coronal",
                title="Post - Body Composition (Coronal)"
            )
            self.viewer.update_viewer(4, coronal_config)
            
            # Position 5: Sagittal (second row third column)
            sagittal_config = ViewerConfig(
                image_path=original_image_path,
                mask_path=bc_mask_path,
                direction="sagittal",
                title="Post - Body Composition (Sagittal)"
            )
            self.viewer.update_viewer(5, sagittal_config)
            
            self.console_window.append_text("Post BC result updated to viewer")
            
        except Exception as e:
            self.console_window.append_text(f"Error updating Post BC viewer: {str(e)}")
    
    def _force_viewer_refresh(self):
        """Force refresh viewer display"""
        if self.viewer is None:
            return
        
        try:
            # Force update MultiViewer display
            self.viewer.update()
            
        except Exception as e:
            self.console_window.append_text(f"Error forcing viewer refresh: {str(e)}")

    def on_processing_finished(self, success, message):
        """Processing completion callback"""
        # Stop timer and restore interface state
        self.left_panel.stop_timer(success)  # Stop timing
        self.left_panel.run_btn.setEnabled(True)
        self.left_panel.progress_bar.setVisible(False)
        
        if success:
            self.left_panel.status_label.setText("Processing Complete")
            QMessageBox.information(self, "Success", message)
        else:
            self.left_panel.status_label.setText("Processing Failed")
            QMessageBox.critical(self, "Error", message)
    
    def load_viewer_component(self):
        """Load viewer component to right panel - Replaced by init_viewer_component, kept as backup"""
        # This method is now replaced by init_viewer_component, kept as backup
        pass

    def show_console(self):
        """Show console"""
        self.console_window.show()

    def on_y_value_generated(self, y_value):
        """Callback after y value generation"""
        try:
            self.console_window.append_text(f"Y value generated: {y_value}")
            
            # Update right panel result display
            self.right_panel.update_result_display(y_value)
            
        except Exception as e:
            self.console_window.append_text(f"Error updating Y value display: {str(e)}")
    
    def closeEvent(self, event):
        """Handle application close event"""
        print("Closing application...")
        
        # Stop any running processes
        if self.process_runner:
            try:
                self.process_runner.stop_processing()
            except Exception as e:
                print(f"Error stopping process: {e}")
        
        # Stop system monitoring timer if exists
        if hasattr(self.left_panel, 'system_monitor') and self.left_panel.system_monitor:
            try:
                self.left_panel.system_monitor.monitor_timer.stop()
            except Exception as e:
                print(f"Error stopping monitor timer: {e}")
        
        # Stop any other timers
        if hasattr(self.left_panel, 'timer'):
            try:
                self.left_panel.timer.stop()
            except Exception as e:
                print(f"Error stopping left panel timer: {e}")
        
        # Close console window
        if self.console_window:
            self.console_window.close()
        
        # Accept the close event
        event.accept()
        print("Application closed successfully.")


def main():
    """Main function"""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Set up signal handling for Ctrl+C
    def signal_handler(sig, frame):
        """Handle interrupt signals (Ctrl+C)"""
        print("\nReceived interrupt signal, closing application...")
        app.quit()
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, signal_handler)
    
    # Enable processing of keyboard interrupts
    # Create a timer to allow the Python interpreter to process signals
    timer = QTimer()
    timer.timeout.connect(lambda: None)  # Empty lambda to allow signal processing
    timer.start(100)  # Check every 100ms
    
    # Create main window
    window = MedicalImageApp()
    window.show()
    
    # Print usage information
    print("Application started. Press Ctrl+C to exit.")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
