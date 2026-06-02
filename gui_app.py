# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTextEdit, QFileDialog,
)

from config import AppConfig
from services.transcription_service import TranscriptionService


class TranscriptionApp(QMainWindow):
    """Ventana principal de la aplicación de transcripción."""

    def __init__(self, config: AppConfig, service: TranscriptionService):
        super().__init__()
        self.config = config
        self.service = service
        self.setWindowTitle('Transcriptor de Videos')
        self.setMinimumSize(600, 400)
        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Fila de selección de archivo
        file_row = QHBoxLayout()
        self.input_path = QLineEdit()
        self.input_path.setPlaceholderText('Ruta de video o carpeta...')
        browse_btn = QPushButton('Explorar')
        browse_btn.clicked.connect(self._browse)
        file_row.addWidget(self.input_path)
        file_row.addWidget(browse_btn)
        layout.addLayout(file_row)

        # Botón principal
        self.start_btn = QPushButton('Iniciar Transcripción')
        self.start_btn.clicked.connect(self._start)
        layout.addWidget(self.start_btn)

        # Área de log
        layout.addWidget(QLabel('Log:'))
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        layout.addWidget(self.log_area)

    def _browse(self):
        path = QFileDialog.getOpenFileName(self, 'Seleccionar video', '',
                                           'Videos (*.mp4 *.avi *.mov *.mkv *.webm)')[0]
        if path:
            self.input_path.setText(path)

    def _start(self):
        path = self.input_path.text().strip()
        if not path:
            self.log_area.append('⚠️ Selecciona un archivo o carpeta primero.')
            return
        self.log_area.append(f'▶️ Procesando: {path}')
        self.start_btn.setEnabled(False)
        try:
            self.service.process_videos(path)
            self.log_area.append('✅ Completado.')
        except Exception as e:
            self.log_area.append(f'❌ Error: {e}')
        finally:
            self.start_btn.setEnabled(True)
