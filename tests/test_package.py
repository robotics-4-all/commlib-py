import unittest
import importlib

class TestPackaging(unittest.TestCase):
    def test_imports(self):
        """Test that all core modules and subpackages are importable."""
        modules = [
            'commlib',
            'commlib.transports',
            'commlib.transports.amqp',
            'commlib.transports.mqtt',
            'commlib.transports.redis',
            'commlib.transports.kafka',
            'commlib.node',
            'commlib.pubsub',
            'commlib.rpc',
            'commlib.endpoints',
            'commlib.msg',
            'commlib.serializer',
            'commlib.utils'
        ]
        for module_name in modules:
            with self.subTest(module=module_name):
                try:
                    importlib.import_module(module_name)
                except ImportError as e:
                    self.fail(f"Failed to import {module_name}: {e}")

    def test_version_exists(self):
        """Test that the package has a version string."""
        import commlib
        self.assertTrue(hasattr(commlib, '__version__'))
        self.assertIsInstance(commlib.__version__, str)
