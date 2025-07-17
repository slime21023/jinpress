"""
Development server for JinPress.

Provides live reload functionality during development.
"""

import http.server
import logging
import socketserver
import threading
import time
from pathlib import Path
from typing import Optional

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from .builder import Builder

logger = logging.getLogger(__name__)


class LiveReloadHandler(FileSystemEventHandler):
    """File system event handler for live reload."""
    
    def __init__(self, builder: Builder, debounce_delay: float = 1.0):
        """
        Initialize live reload handler.
        
        Args:
            builder: Site builder instance
            debounce_delay: Delay in seconds to debounce file changes
        """
        super().__init__()
        self.builder = builder
        self.debounce_delay = debounce_delay
        self.last_rebuild_time = 0
        self.rebuild_timer = None
    
    def on_modified(self, event):
        """Handle file modification events."""
        if event.is_directory:
            return
        
        # Filter relevant file types
        file_path = Path(event.src_path)
        if not self._should_rebuild(file_path):
            return
        
        logger.info(f"File changed: {file_path}")
        self._schedule_rebuild()
    
    def on_created(self, event):
        """Handle file creation events."""
        self.on_modified(event)
    
    def on_deleted(self, event):
        """Handle file deletion events."""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        if self._should_rebuild(file_path):
            logger.info(f"File deleted: {file_path}")
            self._schedule_rebuild()
    
    def _should_rebuild(self, file_path: Path) -> bool:
        """Check if file change should trigger a rebuild."""
        # Skip hidden files and cache directories
        if any(part.startswith('.') for part in file_path.parts):
            return False
        
        # Skip output directory
        if self.builder.output_dir in file_path.parents:
            return False
        
        # Include relevant file types
        relevant_extensions = {'.md', '.yml', '.yaml', '.html', '.css', '.js'}
        return file_path.suffix.lower() in relevant_extensions
    
    def _schedule_rebuild(self):
        """Schedule a rebuild with debouncing."""
        current_time = time.time()
        
        # Cancel existing timer
        if self.rebuild_timer:
            self.rebuild_timer.cancel()
        
        # Schedule new rebuild
        self.rebuild_timer = threading.Timer(self.debounce_delay, self._rebuild)
        self.rebuild_timer.start()
    
    def _rebuild(self):
        """Perform the actual rebuild."""
        try:
            logger.info("Rebuilding site...")
            start_time = time.time()
            self.builder.build(clean=False)  # Don't clean to speed up rebuilds
            elapsed = time.time() - start_time
            logger.info(f"Site rebuilt in {elapsed:.2f}s")
        except Exception as e:
            logger.error(f"Build error: {e}")


class DevServer:
    """Development server with live reload."""
    
    def __init__(self, builder: Builder, host: str = "localhost", port: int = 8000):
        """
        Initialize development server.
        
        Args:
            builder: Site builder instance
            host: Server host
            port: Server port
        """
        self.builder = builder
        self.host = host
        self.port = port
        self.observer = None
        self.server = None
    
    def start(self) -> None:
        """Start the development server."""
        # Initial build
        logger.info("Building site...")
        self.builder.build()
        
        # Start file watcher
        self._start_file_watcher()
        
        # Start HTTP server
        self._start_http_server()
    
    def stop(self) -> None:
        """Stop the development server."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
        
        if self.server:
            self.server.shutdown()
    
    def _start_file_watcher(self) -> None:
        """Start the file system watcher."""
        event_handler = LiveReloadHandler(self.builder)
        self.observer = Observer()
        
        # Watch project directories
        watch_dirs = [
            self.builder.project_root / "docs",
            self.builder.project_root / "static",
            self.builder.project_root / "templates",
        ]
        
        # Add config file
        config_file = self.builder.project_root / "config.yml"
        if config_file.exists():
            self.observer.schedule(event_handler, str(config_file.parent), recursive=False)
        
        # Watch directories that exist
        for watch_dir in watch_dirs:
            if watch_dir.exists():
                self.observer.schedule(event_handler, str(watch_dir), recursive=True)
        
        self.observer.start()
        logger.debug("File watcher started")
    
    def _start_http_server(self) -> None:
        """Start the HTTP server."""
        # Change to output directory
        output_dir = self.builder.output_dir
        if not output_dir.exists():
            raise RuntimeError("Output directory does not exist. Run build first.")
        
        # Create custom handler that serves from output directory
        class CustomHandler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=str(output_dir), **kwargs)
            
            def end_headers(self):
                # Add headers to prevent caching during development
                self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                self.send_header('Pragma', 'no-cache')
                self.send_header('Expires', '0')
                super().end_headers()
            
            def log_message(self, format, *args):
                # Suppress default logging
                pass
        
        # Start server
        try:
            with socketserver.TCPServer((self.host, self.port), CustomHandler) as httpd:
                self.server = httpd
                logger.info(f"Development server running at http://{self.host}:{self.port}")
                logger.info("Press Ctrl+C to stop")
                
                try:
                    httpd.serve_forever()
                except KeyboardInterrupt:
                    logger.info("\nShutting down server...")
                    self.stop()
        
        except OSError as e:
            if e.errno == 48:  # Address already in use
                logger.error(f"Error: Port {self.port} is already in use")
                logger.error(f"Try using a different port: jinpress serve --port {self.port + 1}")
            else:
                logger.error(f"Error starting server: {e}")
            raise


def serve_site(project_root: Path, host: str = "localhost", port: int = 8000) -> None:
    """
    Serve a JinPress site with live reload.
    
    Args:
        project_root: Root directory of the JinPress project
        host: Server host
        port: Server port
    """
    try:
        builder = Builder(project_root)
        server = DevServer(builder, host, port)
        server.start()
    except KeyboardInterrupt:
        logger.info("\nServer stopped")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise
