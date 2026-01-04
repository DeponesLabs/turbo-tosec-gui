from PySide6.QtCore import QThread, Signal, QObject
# Paket olarak kurduğumuz turbo-tosec'i çağırıyoruz
from turbo_tosec import ImportSession, DatabaseManager

class IngestionWorker(QThread):
    """
    Runs the Turbo-TOSEC ingestion process in a background thread.
    Prevents the GUI from freezing.
    """
    # Signals (for communicating with the GUI)
    progress_changed = Signal(int, int)  # (current, total)
    status_changed = Signal(str)         
    finished = Signal(dict)              # stats
    error_occurred = Signal(str)         

    def __init__(self, db_path, files, mode='staged', parent=None):
        
        super().__init__(parent)
        
        self.db_path = db_path
        self.files = files
        self.mode = mode
        self.is_running = True

    def run(self):
        
        try:
            self.status_changed.emit("Establishing a database connection....")
            
            # Start the database administrator
            # Note: On the GUI side, the number of workers is generally left to the number of CPUs
            with DatabaseManager(self.db_path, read_only=False) as db:
                
                # Start session  (without args, in library mode)
                # Set workers=0 to auto-detect CPU count
                session = ImportSession(db_manager=db, workers=0, batch_size=5000)
                self.status_changed.emit(f"The process is starting... Mode: {self.mode}")

                # *** CRITICAL POINT: CALLBACK CONNECTION ***
                # Instantly convert every progress from the backend into a GUI signal.
                def on_progress(current, total):
                    if self.is_running:
                        self.progress_changed.emit(current, total)

                # Start ingestion
                stats = session.ingest(files=self.files, mode=self.mode, progress_callback=on_progress)
                
                if self.is_running:
                    self.status_changed.emit("Process completed successfully.")
                    self.finished.emit(stats)

        except Exception as e:
            self.error_occurred.emit(str(e))
            
    def stop(self):
        """This is called if the user presses the 'Cancel' button."""
        self.is_running = False
        self.requestInterruption()
        self.wait()