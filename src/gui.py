import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import queue
from datetime import datetime
from typing import Callable, Optional
import sys
from pathlib import Path

class VideoGeneratorGUI:
    def __init__(self, process_func: Callable):
        self.process_func = process_func
        self.window = tk.Tk()
        self.window.title("Video Generator")
        self.window.geometry("800x600")

        # Crea una coda per la comunicazione thread-safe
        self.message_queue = queue.Queue()
        self.progress_queue = queue.Queue()

        self._setup_ui()
        self._setup_queue_processing()

    def _setup_ui(self):
        """Configura l'interfaccia utente"""
        # Frame principale
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Titolo
        title_label = ttk.Label(
            main_frame,
            text="Video Generator",
            font=("Helvetica", 16, "bold")
        )
        title_label.grid(row=0, column=0, pady=10, columnspan=2)

        # Progress bar principale
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            main_frame,
            length=600,
            mode='determinate',
            variable=self.progress_var
        )
        self.progress_bar.grid(row=1, column=0, pady=10, columnspan=2)

        # Label per lo stato corrente
        self.status_label = ttk.Label(
            main_frame,
            text="In attesa di avvio...",
            font=("Helvetica", 10)
        )
        self.status_label.grid(row=2, column=0, pady=5, columnspan=2)

        # Area di log
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="5")
        log_frame.grid(row=3, column=0, pady=10, columnspan=2, sticky=(tk.W, tk.E))

        self.log_area = scrolledtext.ScrolledText(
            log_frame,
            width=70,
            height=20,
            font=("Courier", 9)
        )
        self.log_area.grid(row=0, column=0, pady=5)

        # Pulsanti
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, pady=10, columnspan=2)

        self.start_button = ttk.Button(
            button_frame,
            text="Avvia Conversione",
            command=self._start_processing
        )
        self.start_button.grid(row=0, column=0, padx=5)

        self.cancel_button = ttk.Button(
            button_frame,
            text="Annulla",
            command=self._cancel_processing,
            state=tk.DISABLED
        )
        self.cancel_button.grid(row=0, column=1, padx=5)

    def _setup_queue_processing(self):
        """Configura il processamento della coda dei messaggi"""
        def check_queue():
            try:
                while True:
                    message = self.message_queue.get_nowait()
                    self._append_log(message)
            except queue.Empty:
                pass

            try:
                while True:
                    progress = self.progress_queue.get_nowait()
                    self._update_progress(progress)
            except queue.Empty:
                pass

            self.window.after(100, check_queue)

        self.window.after(100, check_queue)

    def _append_log(self, message: str):
        """Aggiunge un messaggio all'area di log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_area.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_area.see(tk.END)

    def _update_progress(self, progress_info: dict):
        """Aggiorna la progress bar e lo stato"""
        if 'value' in progress_info:
            self.progress_var.set(progress_info['value'])
        if 'status' in progress_info:
            self.status_label.config(text=progress_info['status'])

    def _start_processing(self):
        """Avvia il processo di conversione in un thread separato"""
        self.start_button.config(state=tk.DISABLED)
        self.cancel_button.config(state=tk.NORMAL)
        self.progress_var.set(0)

        def run_process():
            try:
                self.process_func(
                    message_callback=lambda msg: self.message_queue.put(msg),
                    progress_callback=lambda prog: self.progress_queue.put(prog)
                )
                self.message_queue.put("Processo completato con successo!")
                self.window.after(0, self._processing_completed)
            except Exception as e:
                self.message_queue.put(f"Errore durante l'elaborazione: {str(e)}")
                self.window.after(0, self._processing_failed)

        self.processing_thread = threading.Thread(target=run_process)
        self.processing_thread.start()

    def _cancel_processing(self):
        """Gestisce l'annullamento del processo"""
        self.message_queue.put("Annullamento in corso...")
        # Implementa qui la logica di annullamento

    def _processing_completed(self):
        """Gestisce il completamento del processo"""
        self.start_button.config(state=tk.NORMAL)
        self.cancel_button.config(state=tk.DISABLED)
        self.progress_var.set(100)
        self.status_label.config(text="Processo completato")

    def _processing_failed(self):
        """Gestisce il fallimento del processo"""
        self.start_button.config(state=tk.NORMAL)
        self.cancel_button.config(state=tk.DISABLED)
        self.status_label.config(text="Processo fallito")

    def run(self):
        """Avvia l'interfaccia grafica"""
        self.window.mainloop()

class CustomLogger(logging.Logger):
    """Logger personalizzato che supporta il callback per la GUI"""
    def __init__(self, name: str, callback: Optional[Callable] = None):
        super().__init__(name)
        self.callback = callback

    def _log(self, level, msg, args, **kwargs):
        super()._log(level, msg, args, **kwargs)
        if self.callback:
            self.callback(msg % args if args else msg)