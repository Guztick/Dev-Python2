# -*- coding: utf-8 -*-
import os
import logging
from typing import Optional
from tqdm.auto import tqdm
import time

from config import AppConfig

logger = logging.getLogger(__name__)

_gemini_configured = False


def _configure_gemini(api_key: str) -> bool:
    global _gemini_configured
    if _gemini_configured:
        return True
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        _gemini_configured = True
        return True
    except Exception as e:
        logger.error(f"Error al configurar Gemini API: {e}")
        return False


class TranscriptionService:
    """Servicio de transcripción y procesamiento de video con Gemini."""

    def __init__(self, config: AppConfig):
        self.config = config
        if config.GEMINI_API_KEY:
            _configure_gemini(config.GEMINI_API_KEY)
        else:
            logger.warning("GEMINI_API_KEY no configurada. Procesamiento con Gemini no disponible.")
        logger.info("TranscriptionService inicializado.")

    def process_videos(self, input_path: str) -> None:
        """Procesa un archivo de video o carpeta específica."""
        logger.info(f"Procesando: {input_path}")

        # TODO: implementar extracción de audio con moviepy y transcripción con faster-whisper
        output_path = os.path.join(
            self.config.OUTPUT_FOLDER,
            os.path.splitext(os.path.basename(input_path))[0] + '.txt'
        )

        for _ in tqdm(range(10), desc=f"Procesando {os.path.basename(input_path)}"):
            time.sleep(0.05)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"[Transcripción pendiente para: {input_path}]\n")

        logger.info(f"Salida guardada en: {output_path}")

        if self.config.GEMINI_API_KEY:
            self._process_with_gemini(output_path)

    def process_videos_batch(self) -> None:
        """Busca y procesa todos los videos en INPUT_FOLDER."""
        logger.info(f"Buscando videos en: {self.config.INPUT_FOLDER}")
        video_extensions = ('.mp4', '.avi', '.mov', '.mkv', '.webm', '.m4v')
        videos = [
            os.path.join(self.config.INPUT_FOLDER, f)
            for f in os.listdir(self.config.INPUT_FOLDER)
            if f.lower().endswith(video_extensions)
        ]

        if not videos:
            logger.info("No se encontraron videos para procesar.")
            return

        for video_path in tqdm(videos, desc="Lote de videos"):
            try:
                self.process_videos(video_path)
            except Exception as e:
                logger.error(f"Error procesando {video_path}: {e}")

    def _process_with_gemini(self, text_path: str, template_path: Optional[str] = None) -> None:
        """Procesa texto transcrito con Gemini para mejorar/formatear."""
        # TODO: implementar llamada a Gemini para post-procesamiento
        logger.info(f"Post-procesamiento con Gemini para: {text_path}")
