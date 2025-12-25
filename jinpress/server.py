"""
Development server for JinPress.

Provides live reload functionality during development with BuildEngine integration.
Implements Requirements 6.1, 6.2, 6.3, 6.4, 6.5, 6.6.
"""

from __future__ import annotations

import http.server
import json
import logging
import socket
import socketserver
import threading
import time
import webbrowser
from collections.abc import Callable
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from .builder import BuildEngine, Builder, BuildResult
from .config import ConfigManager, JinPressConfig

logger = logging.getLogger(__name__)


# Livereload script to inject into HTML pages
LIVERELOAD_SCRIPT = """
<script>
(function() {
    var lastCheck = Date.now();
    var checkInterval = 1000;
    var reloadPending = false;

    function checkForReload() {
        if (reloadPending) return;

        fetch('/__livereload__/check?t=' + lastCheck)
            .then(function(response) {
                return response.json();
            })
            .then(function(data) {
                if (data.reload) {
                    reloadPending = true;
                    console.log('[JinPress] Reloading...');
                    location.reload();
                }
                lastCheck = data.timestamp;
            })
            .catch(function(err) {
                // Server might be restarting, retry
            });
    }

    setInterval(checkForReload, checkInterval);
    console.log('[JinPress] Live reload enabled');
})();
</script>
"""


class LiveReloadHandler(FileSystemEventHandler):
    """File system event handler for live reload."""

    def __init__(
        self,
        builder: BuildEngine,
        debounce_delay: float = 1.0,
        on_rebuild: Callable[[], None] | None = None,
    ):
        """
        Initialize live reload handler.

        Args:
            builder: BuildEngine instance
            debounce_delay: Delay in seconds to debounce file changes
            on_rebuild: Optional callback to invoke after rebuild
        """
        super().__init__()
        self.builder = builder
        self.debounce_delay = debounce_delay
        self.on_rebuild = on_rebuild
        self.last_rebuild_time = 0
        self.rebuild_timer: threading.Timer | None = None
        self._lock = threading.Lock()

    def on_modified(self, event):
        """Handle file modification events."""
        if event.is_directory:
            return

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
        if any(part.startswith(".") for part in file_path.parts):
            return False

        # Skip output directory
        if self.builder.output_dir in file_path.parents:
            return False

        # Include relevant file types
        relevant_extensions = {".md", ".yml", ".yaml", ".html", ".css", ".js"}
        return file_path.suffix.lower() in relevant_extensions

    def _schedule_rebuild(self):
        """Schedule a rebuild with debouncing."""
        with self._lock:
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
            result = self.builder.build(clean=False)
            elapsed = time.time() - start_time

            if result.success:
                logger.info(
                    f"Site rebuilt in {elapsed:.2f}s ({result.pages_built} pages)"
                )
            else:
                for error in result.errors:
                    logger.error(f"Build error: {error}")

            # Update rebuild timestamp
            self.last_rebuild_time = time.time()

            # Invoke callback if provided
            if self.on_rebuild:
                self.on_rebuild()

        except Exception as e:
            logger.error(f"Build error: {e}")


class DevServerHTTPHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP handler for development server with livereload support."""

    # Class-level attributes set by DevServer
    output_dir: Path = Path(".")
    last_rebuild_time: float = 0
    inject_livereload: bool = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(self.output_dir), **kwargs)

    def do_GET(self):
        """Handle GET requests with livereload check endpoint."""
        if self.path.startswith("/__livereload__/check"):
            self._handle_livereload_check()
        else:
            super().do_GET()

    def _handle_livereload_check(self):
        """Handle livereload check requests."""
        # Parse timestamp from query string
        client_time = 0
        if "?" in self.path:
            query = self.path.split("?")[1]
            for param in query.split("&"):
                if param.startswith("t="):
                    try:
                        client_time = float(param[2:])
                    except ValueError:
                        pass

        # Check if rebuild happened after client's last check
        should_reload = self.last_rebuild_time > client_time / 1000

        response = json.dumps(
            {"reload": should_reload, "timestamp": int(time.time() * 1000)}
        )

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(response.encode())

    def send_head(self):
        """Send response headers and potentially inject livereload script."""
        # Get the file to serve
        path = self.translate_path(self.path)

        # Handle directory requests
        if Path(path).is_dir():
            index_path = Path(path) / "index.html"
            if index_path.exists():
                path = str(index_path)

        # Check if this is an HTML file
        if path.endswith(".html") and self.inject_livereload:
            return self._send_html_with_livereload(path)

        return super().send_head()

    def _send_html_with_livereload(self, path: str):
        """Send HTML file with livereload script injected."""
        try:
            with open(path, "rb") as f:
                content = f.read()

            # Inject livereload script before </body>
            content_str = content.decode("utf-8")
            if "</body>" in content_str:
                content_str = content_str.replace(
                    "</body>", LIVERELOAD_SCRIPT + "</body>"
                )
            elif "</html>" in content_str:
                content_str = content_str.replace(
                    "</html>", LIVERELOAD_SCRIPT + "</html>"
                )
            else:
                content_str += LIVERELOAD_SCRIPT

            content = content_str.encode("utf-8")

            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", len(content))
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
            self.end_headers()

            self.wfile.write(content)
            return None

        except Exception as e:
            logger.error(f"Error serving HTML: {e}")
            return super().send_head()

    def end_headers(self):
        """Add headers to prevent caching during development."""
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def log_message(self, format, *args):
        """Custom logging for HTTP requests."""
        # Only log non-livereload requests
        if not args[0].startswith("GET /__livereload__"):
            logger.debug("%s - %s", self.address_string(), format % args)


class DevServer:
    """
    Development server with live reload.

    Integrates BuildEngine for site building and provides HTTP serving
    with automatic file watching and hot reload capabilities.

    Requirements:
    - 6.1: Start local development server with `jinpress serve`
    - 6.2: Default to localhost:3000
    - 6.3: Auto-rebuild and notify browser on file changes
    - 6.4: Auto-reload config on changes
    - 6.5: Display server status and access URL in terminal
    - 6.6: Auto-select next available port if occupied
    """

    DEFAULT_PORT = 3000
    MAX_PORT_ATTEMPTS = 10

    def __init__(
        self,
        project_root: Path,
        config: JinPressConfig | None = None,
        host: str = "localhost",
        port: int = DEFAULT_PORT,
    ):
        """
        Initialize development server.

        Args:
            project_root: Root directory of the JinPress project
            config: Site configuration (will load from project_root if None)
            host: Server host (default: localhost)
            port: Server port (default: 3000)
        """
        self.project_root = Path(project_root)
        self.host = host
        self.port = port

        # Load configuration
        if config is None:
            config_manager = ConfigManager()
            self.config = config_manager.load(self.project_root)
        else:
            self.config = config

        # Initialize build engine
        self.builder = BuildEngine(self.project_root, self.config)

        # Server components
        self.observer: Observer | None = None
        self.server: socketserver.TCPServer | None = None
        self._server_thread: threading.Thread | None = None
        self._running = False
        self._last_rebuild_time = time.time()

    def start(self, open_browser: bool = True) -> None:
        """
        Start the development server.

        Args:
            open_browser: Whether to open browser automatically
        """
        self._running = True

        # Initial build
        self._display_startup_message()
        logger.info("Building site...")
        result = self.builder.build()

        if not result.success:
            for error in result.errors:
                logger.error(f"Build error: {error}")
            raise RuntimeError("Initial build failed")

        logger.info(f"Built {result.pages_built} pages in {result.duration_ms:.0f}ms")

        # Find available port (Requirement 6.6)
        self.port = self._find_available_port(self.port)

        # Start file watcher (Requirements 6.3, 6.4)
        self._start_file_watcher()

        # Display server info (Requirement 6.5)
        self._display_server_info()

        # Open browser if requested
        if open_browser:
            url = f"http://{self.host}:{self.port}"
            webbrowser.open(url)

        # Start HTTP server (blocking)
        self._start_http_server()

    def stop(self) -> None:
        """Stop the development server."""
        self._running = False

        if self.observer:
            self.observer.stop()
            self.observer.join(timeout=2)
            self.observer = None

        if self.server:
            self.server.shutdown()
            self.server = None

        logger.info("Server stopped")

    def _display_startup_message(self) -> None:
        """Display startup message."""
        print("\n" + "=" * 50)
        print("  JinPress Development Server")
        print("=" * 50)

    def _display_server_info(self) -> None:
        """Display server status and access URL (Requirement 6.5)."""
        url = f"http://{self.host}:{self.port}"

        print(f"\n  ➜  Local:   {url}")
        print(f"  ➜  Project: {self.project_root}")
        print("\n  Press Ctrl+C to stop\n")
        print("-" * 50)

    def _find_available_port(self, preferred: int) -> int:
        """
        Find an available port, starting from preferred port.

        Implements Requirement 6.6: Auto-select next available port.

        Args:
            preferred: Preferred port number

        Returns:
            Available port number

        Raises:
            RuntimeError: If no available port found after MAX_PORT_ATTEMPTS
        """
        for attempt in range(self.MAX_PORT_ATTEMPTS):
            port = preferred + attempt
            if self._is_port_available(port):
                if attempt > 0:
                    logger.info(f"Port {preferred} in use, using port {port}")
                return port

        raise RuntimeError(
            f"Could not find available port after {self.MAX_PORT_ATTEMPTS} attempts "
            f"(tried {preferred}-{preferred + self.MAX_PORT_ATTEMPTS - 1})"
        )

    def _is_port_available(self, port: int) -> bool:
        """Check if a port is available."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((self.host, port))
                return True
        except OSError:
            return False

    def _start_file_watcher(self) -> None:
        """
        Start the file system watcher.

        Implements Requirements 6.3 and 6.4:
        - Auto-rebuild on Markdown file changes
        - Auto-reload config on changes
        """

        def on_rebuild():
            self._last_rebuild_time = time.time()
            # Update handler's timestamp
            DevServerHTTPHandler.last_rebuild_time = self._last_rebuild_time

        event_handler = LiveReloadHandler(
            self.builder, debounce_delay=0.5, on_rebuild=on_rebuild
        )

        self.observer = Observer()

        # Watch directories
        watch_paths = [
            self.project_root / "docs",
            self.project_root / "static",
            self.project_root / "templates",
        ]

        for watch_path in watch_paths:
            if watch_path.exists():
                self.observer.schedule(event_handler, str(watch_path), recursive=True)
                logger.debug(f"Watching: {watch_path}")

        # Watch config files (Requirement 6.4)
        config_files = [
            self.project_root / "jinpress.yml",
            self.project_root / "config.yml",
        ]

        for config_file in config_files:
            if config_file.exists():
                self.observer.schedule(
                    event_handler, str(config_file.parent), recursive=False
                )

        self.observer.start()
        logger.debug("File watcher started")

    def _start_http_server(self) -> None:
        """
        Start the HTTP server.

        Implements Requirements 6.1 and 6.2:
        - Start local development server
        - Default to localhost:3000
        """
        output_dir = self.builder.output_dir
        if not output_dir.exists():
            raise RuntimeError("Output directory does not exist. Build failed.")

        # Configure handler class
        DevServerHTTPHandler.output_dir = output_dir
        DevServerHTTPHandler.last_rebuild_time = self._last_rebuild_time
        DevServerHTTPHandler.inject_livereload = True

        # Allow socket reuse
        socketserver.TCPServer.allow_reuse_address = True

        try:
            with socketserver.TCPServer(
                (self.host, self.port), DevServerHTTPHandler
            ) as httpd:
                self.server = httpd
                logger.info(f"Server running at http://{self.host}:{self.port}")

                try:
                    httpd.serve_forever()
                except KeyboardInterrupt:
                    print("\n")
                    logger.info("Shutting down server...")
                    self.stop()

        except OSError as e:
            # Address already in use (Unix: 48, Windows: 10048)
            if e.errno in (48, 10048):
                logger.error(f"Port {self.port} is already in use")
            else:
                logger.error(f"Error starting server: {e}")
            raise


# Legacy DevServer wrapper for backward compatibility
class LegacyDevServer:
    """
    Legacy DevServer wrapper for backward compatibility.

    Uses the old Builder class interface.
    """

    def __init__(self, builder: Builder, host: str = "localhost", port: int = 8000):
        """
        Initialize legacy development server.

        Args:
            builder: Legacy Builder instance
            host: Server host
            port: Server port
        """
        self.builder = builder
        self.host = host
        self.port = port
        self.observer: Observer | None = None
        self.server: socketserver.TCPServer | None = None

    def start(self) -> None:
        """Start the development server."""
        logger.info("Building site...")
        self.builder.build()

        self._start_file_watcher()
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

        # Create a wrapper for the legacy builder
        class LegacyBuilderWrapper:
            def __init__(self, builder):
                self._builder = builder
                self.output_dir = builder.output_dir

            def build(self, clean=True):
                self._builder.build(clean=clean)
                return BuildResult(success=True, pages_built=0)

        wrapper = LegacyBuilderWrapper(self.builder)
        event_handler = LiveReloadHandler(wrapper)
        self.observer = Observer()

        watch_dirs = [
            self.builder.project_root / "docs",
            self.builder.project_root / "static",
            self.builder.project_root / "templates",
        ]

        config_file = self.builder.project_root / "config.yml"
        if config_file.exists():
            self.observer.schedule(
                event_handler, str(config_file.parent), recursive=False
            )

        for watch_dir in watch_dirs:
            if watch_dir.exists():
                self.observer.schedule(event_handler, str(watch_dir), recursive=True)

        self.observer.start()
        logger.debug("File watcher started")

    def _start_http_server(self) -> None:
        """Start the HTTP server."""
        output_dir = self.builder.output_dir
        if not output_dir.exists():
            raise RuntimeError("Output directory does not exist. Run build first.")

        class CustomHandler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=str(output_dir), **kwargs)

            def end_headers(self):
                self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
                self.send_header("Pragma", "no-cache")
                self.send_header("Expires", "0")
                super().end_headers()

            def log_message(self, format, *args):
                pass

        try:
            with socketserver.TCPServer((self.host, self.port), CustomHandler) as httpd:
                self.server = httpd
                logger.info(
                    f"Development server running at http://{self.host}:{self.port}"
                )
                logger.info("Press Ctrl+C to stop")

                try:
                    httpd.serve_forever()
                except KeyboardInterrupt:
                    logger.info("\nShutting down server...")
                    self.stop()

        except OSError as e:
            if e.errno == 48:
                logger.error(f"Error: Port {self.port} is already in use")
                logger.error(
                    f"Try using a different port: jinpress serve --port {self.port + 1}"
                )
            else:
                logger.error(f"Error starting server: {e}")
            raise


def serve_site(
    project_root: Path,
    host: str = "localhost",
    port: int = 3000,
    open_browser: bool = True,
) -> None:
    """
    Serve a JinPress site with live reload.

    Args:
        project_root: Root directory of the JinPress project
        host: Server host
        port: Server port
        open_browser: Whether to open browser automatically
    """
    try:
        server = DevServer(project_root, host=host, port=port)
        server.start(open_browser=open_browser)
    except KeyboardInterrupt:
        logger.info("\nServer stopped")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise
