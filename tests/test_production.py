import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient

from backend.production import create_app, main


class ProductionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        (self.directory / 'assets').mkdir()
        (self.directory / 'index.html').write_text('<!doctype html><title>NetSim Lite</title>', encoding='utf-8')
        (self.directory / 'assets' / 'test.js').write_text('console.log("ready")', encoding='utf-8')
        self.env = patch.dict(os.environ, {'NETSIM_STATIC_DIR': str(self.directory)})
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_static_and_api_on_same_origin(self):
        client = TestClient(create_app())
        self.assertEqual(client.get('/').status_code, 200)
        self.assertIn('text/html', client.get('/').headers['content-type'])
        self.assertEqual(client.get('/assets/test.js').status_code, 200)
        self.assertEqual(client.get('/api/health').json(), {'status': 'ok'})
        response = client.post('/api/subnet', json={'cidr': '192.168.1.0/26'})
        self.assertEqual(response.json()['usable_hosts'], 62)
        self.assertEqual(client.get('/docs').status_code, 200)

    def test_unknown_files_api_and_path_traversal(self):
        client = TestClient(create_app())
        for path in ['/api/missing', '/assets/missing.js', '/missing', '/%2e%2e/backend/main.py']:
            self.assertEqual(client.get(path).status_code, 404, path)
        self.assertEqual(client.post('/api/subnet', json={'cidr': 'invalid'}).status_code, 422)

    def test_missing_build_fails_at_startup(self):
        (self.directory / 'index.html').unlink()
        with self.assertRaisesRegex(RuntimeError, 'Frontend build missing'):
            create_app()

    def test_runtime_port_and_host(self):
        with patch.dict(os.environ, {'PORT': '8123', 'HOST': '127.0.0.1'}), patch('backend.production.uvicorn.run') as run:
            main()
            self.assertEqual(run.call_args.kwargs, {'host': '127.0.0.1', 'port': 8123})
        for value in ['bad', '0', '65536']:
            with patch.dict(os.environ, {'PORT': value}), self.assertRaisesRegex(ValueError, 'PORT must'):
                main()
