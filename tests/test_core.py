import unittest
from backend.core import route, subnet


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.nodes = [{'id': x} for x in ['A', 'R1', 'R2', 'B']]
        self.links = [dict(source=a, target=b, cost=c) for a, b, c in [('A','R1',1), ('R1','B',1), ('A','R2',3), ('R2','B',2)]]

    def test_primary_and_failure(self):
        self.assertEqual(route(self.nodes, self.links, 'A', 'B')['total_cost'], 2)
        self.links[0]['enabled'] = False
        self.assertEqual(route(self.nodes, self.links, 'A', 'B')['path'], ['A','R2','B'])
        self.links[2]['enabled'] = False
        self.assertFalse(route(self.nodes, self.links, 'A', 'B')['reachable'])

    def test_same_node_and_zero_cost(self):
        self.assertEqual(route(self.nodes, self.links, 'A', 'A')['path'], ['A'])
        self.links[0]['cost'] = 0
        self.assertEqual(route(self.nodes, self.links, 'A', 'B')['total_cost'], 1)

    def test_invalid_graph(self):
        for nodes, links in [(self.nodes + [{'id':'A'}], self.links), (self.nodes, [dict(source='A',target='X')]), (self.nodes, [dict(source='A',target='B',cost=-1)])]:
            with self.assertRaises(ValueError):
                route(nodes, links, 'A', 'B')

    def test_subnet(self):
        result = subnet('192.168.1.0/26')
        self.assertEqual(result['broadcast'], '192.168.1.63')
        self.assertEqual(result['mask'], '255.255.255.192')
        self.assertEqual(result['usable_hosts'], 62)
        self.assertEqual(subnet('10.0.0.1/32')['usable_hosts'], 1)
        self.assertEqual(subnet('10.0.0.0/31')['usable_hosts'], 2)
        with self.assertRaises(ValueError):
            subnet('999.0.0.1/24')

    def test_overflowing_detour_does_not_hide_finite_route(self):
        links = [dict(source=a,target=b,cost=c) for a,b,c in
                 [('A','R1',1e308),('R1','R2',1e308),('A','B',1.5e308)]]
        result=route(self.nodes,links,'A','B')
        self.assertTrue(result['reachable'])
        self.assertEqual(result['total_cost'],1.5e308)
        self.assertFalse(route(self.nodes,links[:-1],'A','B')['reachable'])

    def test_equal_cost_paths_and_zero_cycle(self):
        for link in self.links:
            link['cost']=0
        result=route(self.nodes,self.links,'A','B')
        self.assertEqual(result['total_cost'],0)
        self.assertEqual(len(result['path']),len(set(result['path'])))
        self.assertEqual(result['path'][0],'A')
        self.assertEqual(result['path'][-1],'B')


if __name__ == '__main__':
    unittest.main()
