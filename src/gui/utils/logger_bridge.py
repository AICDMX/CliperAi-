"""Bridge to capture loguru logs and make them available to GUI."""

from queue import Queue
from loguru import logger


class LoggerBridge:
    """Capture loguru logs via custom sink and provide access via thread-safe queue."""

    def __init__(self):
        """Initialize LoggerBridge with empty queue."""
        self.log_queue = Queue()
        self.handler_id = None

    def setup(self):
        """
        Add custom sink to loguru.

        Must be called once at application startup before any logging happens.
        """
        self.handler_id = logger.add(
            self._queue_sink,
            format="{time:HH:mm:ss} | {level: <8} | {message}",
            level="INFO",
            colorize=False,  # We'll handle colorization in GUI
        )

    def _queue_sink(self, message):
        """
        Custom sink that puts log messages in queue.

        Called by loguru for each log message.
        """
        # message is a str from loguru's sink format
        self.log_queue.put(message.rstrip("\n"))

    def get_logs(self):
        """
        Get all pending logs (non-blocking).

        Returns:
            List of log strings, empty if queue is empty
        """
        logs = []
        while not self.log_queue.empty():
            try:
                logs.append(self.log_queue.get_nowait())
            except Exception:
                break
        return logs

    def shutdown(self):
        """Remove the custom sink from loguru."""
        if self.handler_id is not None:
            logger.remove(self.handler_id)
