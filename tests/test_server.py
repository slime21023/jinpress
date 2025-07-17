#!/usr/bin/env python3
"""
Test development server and live reload functionality.
"""

import unittest
import tempfile
import shutil
import time
import threading
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from jinpress.server import LiveReloadHandler, DevServer, serve_site
from jinpress.builder import Builder

class TestLiveReloadHandler(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_root = Path(self.test_dir) / "project"
        self.project_root.mkdir()
        
        # Create a mock builder
        self.mock_builder = Mock(spec=Builder)
        self.mock_builder.project_root = self.project_root
        self.mock_builder.output_dir = self.project_root / "dist"
        
        self.handler = LiveReloadHandler(self.mock_builder, debounce_delay=0.1)

    def tearDown(self):
        # Cancel any pending timers
        if self.handler.rebuild_timer:
            self.handler.rebuild_timer.cancel()
        shutil.rmtree(self.test_dir)

    def test_handler_initialization(self):
        """Test that LiveReloadHandler initializes correctly."""
        self.assertEqual(self.handler.builder, self.mock_builder)
        self.assertEqual(self.handler.debounce_delay, 0.1)
        self.assertIsNone(self.handler.rebuild_timer)

    def test_should_rebuild_relevant_files(self):
        """Test that relevant file types trigger rebuilds."""
        relevant_files = [
            self.project_root / "test.md",
            self.project_root / "config.yml",
            self.project_root / "config.yaml",
            self.project_root / "template.html",
            self.project_root / "style.css",
            self.project_root / "script.js",
        ]
        
        for file_path in relevant_files:
            with self.subTest(file=file_path):
                self.assertTrue(self.handler._should_rebuild(file_path))

    def test_should_not_rebuild_irrelevant_files(self):
        """Test that irrelevant file types don't trigger rebuilds."""
        irrelevant_files = [
            self.project_root / "test.txt",
            self.project_root / "image.png",
            self.project_root / "data.json",
            self.project_root / ".hidden",
            self.project_root / ".git" / "config",
            self.mock_builder.output_dir / "index.html",  # Output directory
        ]
        
        for file_path in irrelevant_files:
            with self.subTest(file=file_path):
                self.assertFalse(self.handler._should_rebuild(file_path))

    def test_schedule_rebuild_debouncing(self):
        """Test that rebuild scheduling includes debouncing."""
        # Schedule first rebuild
        self.handler._schedule_rebuild()
        first_timer = self.handler.rebuild_timer
        self.assertIsNotNone(first_timer)
        
        # Schedule second rebuild (should cancel first)
        self.handler._schedule_rebuild()
        second_timer = self.handler.rebuild_timer
        self.assertIsNotNone(second_timer)
        self.assertNotEqual(first_timer, second_timer)
        
        # Clean up
        if second_timer:
            second_timer.cancel()

    def test_rebuild_calls_builder(self):
        """Test that rebuild calls the builder."""
        self.handler._rebuild()
        self.mock_builder.build.assert_called_once_with(clean=False)

    def test_rebuild_handles_exceptions(self):
        """Test that rebuild handles builder exceptions gracefully."""
        self.mock_builder.build.side_effect = Exception("Build failed")
        
        # Should not raise exception
        try:
            self.handler._rebuild()
        except Exception:
            self.fail("_rebuild should handle exceptions gracefully")
        
        self.mock_builder.build.assert_called_once()

    def test_file_modification_event(self):
        """Test handling of file modification events."""
        # Create a mock event
        mock_event = Mock()
        mock_event.is_directory = False
        mock_event.src_path = str(self.project_root / "test.md")
        
        with patch.object(self.handler, '_schedule_rebuild') as mock_schedule:
            self.handler.on_modified(mock_event)
            mock_schedule.assert_called_once()

    def test_directory_modification_ignored(self):
        """Test that directory modifications are ignored."""
        mock_event = Mock()
        mock_event.is_directory = True
        mock_event.src_path = str(self.project_root / "some_dir")
        
        with patch.object(self.handler, '_schedule_rebuild') as mock_schedule:
            self.handler.on_modified(mock_event)
            mock_schedule.assert_not_called()

    def test_file_creation_event(self):
        """Test handling of file creation events."""
        mock_event = Mock()
        mock_event.is_directory = False
        mock_event.src_path = str(self.project_root / "new.md")
        
        with patch.object(self.handler, '_schedule_rebuild') as mock_schedule:
            self.handler.on_created(mock_event)
            mock_schedule.assert_called_once()

    def test_file_deletion_event(self):
        """Test handling of file deletion events."""
        mock_event = Mock()
        mock_event.is_directory = False
        mock_event.src_path = str(self.project_root / "deleted.md")
        
        with patch.object(self.handler, '_schedule_rebuild') as mock_schedule:
            self.handler.on_deleted(mock_event)
            mock_schedule.assert_called_once()


class TestDevServer(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_root = Path(self.test_dir) / "project"
        self.project_root.mkdir()
        
        # Create output directory
        self.output_dir = self.project_root / "dist"
        self.output_dir.mkdir()
        
        # Create a mock builder
        self.mock_builder = Mock(spec=Builder)
        self.mock_builder.project_root = self.project_root
        self.mock_builder.output_dir = self.output_dir
        
        self.server = DevServer(self.mock_builder, host="localhost", port=8001)

    def tearDown(self):
        if self.server.observer:
            self.server.observer.stop()
            self.server.observer.join()
        shutil.rmtree(self.test_dir)

    def test_server_initialization(self):
        """Test that DevServer initializes correctly."""
        self.assertEqual(self.server.builder, self.mock_builder)
        self.assertEqual(self.server.host, "localhost")
        self.assertEqual(self.server.port, 8001)
        self.assertIsNone(self.server.observer)
        self.assertIsNone(self.server.server)

    def test_file_watcher_setup(self):
        """Test that file watcher is set up correctly."""
        # Create some directories to watch
        docs_dir = self.project_root / "docs"
        docs_dir.mkdir()
        templates_dir = self.project_root / "templates"
        templates_dir.mkdir()
        config_file = self.project_root / "config.yml"
        config_file.touch()
        
        self.server._start_file_watcher()
        
        self.assertIsNotNone(self.server.observer)
        self.assertTrue(self.server.observer.is_alive())
        
        # Clean up
        self.server.observer.stop()
        self.server.observer.join()

    def test_file_watcher_handles_missing_directories(self):
        """Test that file watcher handles missing directories gracefully."""
        # Don't create any directories
        
        try:
            self.server._start_file_watcher()
            self.assertIsNotNone(self.server.observer)
            
            # Clean up
            self.server.observer.stop()
            self.server.observer.join()
        except Exception as e:
            self.fail(f"File watcher should handle missing directories: {e}")

    @patch('jinpress.server.socketserver.TCPServer')
    def test_http_server_setup(self, mock_tcp_server):
        """Test that HTTP server is set up correctly."""
        # Create a mock server instance
        mock_server_instance = Mock()
        mock_tcp_server.return_value.__enter__.return_value = mock_server_instance
        
        # Mock the serve_forever to avoid blocking
        def mock_serve_forever():
            raise KeyboardInterrupt()  # Simulate Ctrl+C
        
        mock_server_instance.serve_forever = mock_serve_forever
        
        try:
            self.server._start_http_server()
        except KeyboardInterrupt:
            pass  # Expected
        
        # Verify server was created with correct parameters
        mock_tcp_server.assert_called_once()
        args, kwargs = mock_tcp_server.call_args
        self.assertEqual(args[0], ("localhost", 8001))

    def test_http_server_missing_output_dir(self):
        """Test that HTTP server handles missing output directory."""
        # Remove output directory
        shutil.rmtree(self.output_dir)
        
        with self.assertRaises(RuntimeError) as context:
            self.server._start_http_server()
        
        self.assertIn("Output directory does not exist", str(context.exception))

    @patch('jinpress.server.socketserver.TCPServer')
    def test_http_server_port_in_use(self, mock_tcp_server):
        """Test that HTTP server handles port already in use."""
        # Mock OSError with errno 48 (Address already in use)
        error = OSError("Address already in use")
        error.errno = 48
        mock_tcp_server.side_effect = error
        
        with self.assertRaises(OSError):
            self.server._start_http_server()


class TestServeFunction(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_root = Path(self.test_dir) / "project"
        self.project_root.mkdir()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch('jinpress.server.Builder')
    @patch('jinpress.server.DevServer')
    def test_serve_site_function(self, mock_dev_server_class, mock_builder_class):
        """Test the serve_site function."""
        # Create mock instances
        mock_builder = Mock()
        mock_server = Mock()
        mock_builder_class.return_value = mock_builder
        mock_dev_server_class.return_value = mock_server
        
        # Mock server.start() to raise KeyboardInterrupt (simulate Ctrl+C)
        mock_server.start.side_effect = KeyboardInterrupt()
        
        try:
            serve_site(self.project_root, "localhost", 8002)
        except KeyboardInterrupt:
            pass  # Expected
        
        # Verify builder and server were created correctly
        mock_builder_class.assert_called_once_with(self.project_root)
        mock_dev_server_class.assert_called_once_with(mock_builder, "localhost", 8002)
        mock_server.start.assert_called_once()

    @patch('jinpress.server.Builder')
    @patch('jinpress.server.DevServer')
    def test_serve_site_handles_exceptions(self, mock_dev_server_class, mock_builder_class):
        """Test that serve_site handles exceptions properly."""
        # Create mock instances
        mock_builder = Mock()
        mock_server = Mock()
        mock_builder_class.return_value = mock_builder
        mock_dev_server_class.return_value = mock_server
        
        # Mock server.start() to raise a general exception
        mock_server.start.side_effect = Exception("Server error")
        
        with self.assertRaises(Exception) as context:
            serve_site(self.project_root)
        
        self.assertEqual(str(context.exception), "Server error")


if __name__ == "__main__":
    unittest.main()