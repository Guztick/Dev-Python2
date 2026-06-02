# -*- coding: utf-8 -*-
import os
import logging
import argparse
import sys
import threading
import signal
from typing import Optional

from bootstrap import run_bootstrap
from config import AppConfig
from services.transcription_service import TranscriptionService

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def setup_logging(log_folder: str) -> None:
    log_file_path = os.path.join(log_folder, 'transcriptor.log')
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file_path, encoding='utf-8'),
        ],
    )


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Transcriptor automático de videos")
    parser.add_argument('--watch', dest='watch', action='store_true',
                        help="Modo observador continuo")
    parser.add_argument('--no-watch', dest='watch', action='store_false',
                        help="Ejecutar solo una vez")
    parser.add_argument('--interval', type=int, default=10,
                        help="Segundos entre comprobaciones en modo --watch (default: 10)")
    parser.add_argument('--input', type=str,
                        help="Ruta de video o carpeta para procesar")
    parser.add_argument('--cli', action='store_true',
                        help="Forzar modo consola (CLI)")
    parser.set_defaults(watch=True)
    args, unknown = parser.parse_known_args()
    if unknown:
        logger.warning(f"Argumentos desconocidos ignorados: {unknown}")
    return args


def run_cli_mode(config: AppConfig, service: TranscriptionService, args: argparse.Namespace) -> None:
    stop_event = threading.Event()

    def _signal_handler(signum: int, frame: Optional[object]) -> None:
        logger.info(f"Señal recibida ({signum}). Cerrando...")
        stop_event.set()

    signal.signal(signal.SIGINT, _signal_handler)
    try:
        signal.signal(signal.SIGTERM, _signal_handler)
    except Exception:
        pass

    try:
        if args.input:
            logger.info(f"Procesando: {args.input}")
            service.process_videos(args.input)
        elif args.watch:
            logger.info(f"Modo observador activo. Intervalo: {args.interval}s")
            while not stop_event.is_set():
                try:
                    service.process_videos_batch()
                except Exception as e:
                    logger.error(f"Error en lote: {e}")
                if not stop_event.is_set():
                    stop_event.wait(args.interval)
        else:
            logger.info("Procesando una vez...")
            service.process_videos_batch()
    except KeyboardInterrupt:
        logger.info("Interrumpido por el usuario.")
    except Exception as e:
        logger.error(f"Error fatal en CLI: {e}", exc_info=True)
    finally:
        logger.info("Programa finalizado.")


def main() -> None:
    run_bootstrap()

    config = AppConfig()

    try:
        config.setup_folders()
    except Exception as e:
        logger.critical(f"Error al crear carpetas: {e}")
        sys.exit(1)

    setup_logging(config.LOGS_FOLDER)

    args = parse_arguments()

    service = TranscriptionService(config)

    is_cli_mode = args.input is not None or args.cli or not sys.stdin.isatty()

    if is_cli_mode:
        logger.info("Modo Consola (CLI).")
        run_cli_mode(config, service, args)
    else:
        logger.info("Modo Gráfico (GUI).")
        try:
            from PyQt5.QtWidgets import QApplication
            from gui_app import TranscriptionApp
            app = QApplication(sys.argv)
            window = TranscriptionApp(config, service)
            window.show()
            sys.exit(app.exec_())
        except ImportError as e:
            logger.error(f"PyQt5 no disponible ({e}). Iniciando en modo CLI.")
            run_cli_mode(config, service, args)


if __name__ == '__main__':
    main()
