import unittest
from fastapi.testclient import TestClient
from backend.main import app


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.body = {'nodes': [{'id': n} for n in ['A', 'R1', 'R2', 'B']],
                     'links': [{'source': a, 'target': b, 'cost': c} for a,b,c in
                               [('A','R1',1), ('R1','B',1), ('A','R2',3), ('R2','B',2)]],
                     'source': 'A', 'destination': 'B'}

    def test_health_and_route(self):
        self.assertEqual(self.client.get('/api/health').json()['status'], 'ok')
        result = self.client.post('/api/route', json=self.body)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()['path'], ['A', 'R1', 'B'])

    def test_simulation_and_failures(self):
        self.body['links'][0]['enabled'] = False
        result = self.client.post('/api/simulate', json=self.body).json()
        self.assertEqual(result['total_cost'], 5)
        self.assertEqual(result['events'][-1]['type'], 'delivered')
        self.body['links'][2]['enabled'] = False
        result = self.client.post('/api/simulate', json=self.body).json()
        self.assertFalse(result['reachable'])
        self.assertEqual(result['events'][-1]['type'], 'unreachable')

    def test_validation(self):
        self.body['nodes'][0]['ip'] = 'invalid'
        self.assertEqual(self.client.post('/api/route', json=self.body).status_code, 422)
        self.body['nodes'][0].pop('ip')
        self.body['links'][0]['cost'] = -1
        self.assertEqual(self.client.post('/api/route', json=self.body).status_code, 422)
        self.assertEqual(self.client.post('/api/subnet', json={'cidr':'nope'}).status_code, 422)

    def test_subnet(self):
        result = self.client.post('/api/subnet', json={'cidr':'192.168.1.15/26'}).json()
        self.assertEqual(result['network'], '192.168.1.0')
        self.assertEqual(result['last_host'], '192.168.1.62')

    def test_ambiguous_and_invalid_links(self):
        for cost in [True, '2', -0.5]:
            self.body['links'][0]['cost'] = cost
            self.assertEqual(self.client.post('/api/route', json=self.body).status_code, 422)
        self.body['links'][0]['cost'] = 1
        self.body['links'].append({'source':'R1','target':'A','cost':2})
        self.assertEqual(self.client.post('/api/route', json=self.body).status_code, 422)
        self.body['links'] = [{'source':'A','target':'A','cost':0}]
        self.assertEqual(self.client.post('/api/route', json=self.body).status_code, 422)

    def test_id_and_boolean_validation(self):
        self.body['nodes'][0]['id'] = '  '
        self.assertEqual(self.client.post('/api/route', json=self.body).status_code, 422)
        self.body['nodes'][0]['id'] = 'A'
        self.body['links'][0]['enabled'] = 'false'
        self.assertEqual(self.client.post('/api/route', json=self.body).status_code, 422)

    def test_loopback_cors(self):
        for origin in ['http://localhost:5173','http://127.0.0.1:5173']:
            response=self.client.options('/api/route',headers={'Origin':origin,'Access-Control-Request-Method':'POST'})
            self.assertEqual(response.headers['access-control-allow-origin'],origin)

    def test_cost_overflow(self):
        self.body['links']=[{'source':'A','target':'R1','cost':1e308}, {'source':'R1','target':'B','cost':1e308}]
        response=self.client.post('/api/route',json=self.body)
        self.assertEqual(response.status_code,422)
        self.assertIn('numeric range',response.json()['detail'])
