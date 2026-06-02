import os


class AppConfig:
    """
    Configuración de la aplicación de transcripción.
    Rutas adaptadas para entorno local (no Colab).
    """
    def __init__(self):
        self.BASE_PATH = os.environ.get('TRANSCRIPTOR_BASE_PATH', os.path.join(os.getcwd(), 'data'))
        self.INPUT_FOLDER = os.path.join(self.BASE_PATH, 'input')
        self.OUTPUT_FOLDER = os.path.join(self.BASE_PATH, 'output')
        self.PROCESADOS_FOLDER = os.path.join(self.BASE_PATH, 'processed')
        self.LOGS_FOLDER = os.path.join(self.BASE_PATH, 'logs')

        self.GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
        self.GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-1.5-flash')

    def setup_folders(self):
        """Crea las carpetas del proyecto si no existen."""
        for folder in [self.INPUT_FOLDER, self.OUTPUT_FOLDER, self.PROCESADOS_FOLDER, self.LOGS_FOLDER]:
            os.makedirs(folder, exist_ok=True)
