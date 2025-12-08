"""Threading helper for running long-running operations without freezing GUI."""

from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from typing import Callable, Any


class TaskRunner:
    """Run functions in background thread with thread-safe result callback."""

    def __init__(self, root):
        """
        Initialize TaskRunner.

        Args:
            root: Tkinter root window for scheduling callbacks
        """
        self.root = root
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.result_queue = Queue()

    def run_task(self, func: Callable, callback: Callable, *args, **kwargs):
        """
        Run function in background thread.

        Args:
            func: Function to run in background
            callback: Function to call with result: callback(status, result)
                      status is 'success' or 'error'
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func
        """

        def wrapper():
            try:
                result = func(*args, **kwargs)
                self.result_queue.put(("success", result))
            except Exception as e:
                self.result_queue.put(("error", e))

        self.executor.submit(wrapper)
        self._poll_queue(callback)

    def _poll_queue(self, callback: Callable):
        """
        Poll queue for results (thread-safe).

        Checks queue every 100ms for result, calls callback when available.
        """
        try:
            status, result = self.result_queue.get_nowait()
            callback(status, result)
        except Exception:
            # Queue empty, check again in 100ms
            self.root.after(100, lambda: self._poll_queue(callback))

    def shutdown(self):
        """Shutdown thread pool gracefully."""
        self.executor.shutdown(wait=True)
