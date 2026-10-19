"""核查转换语义和安全边界，不模拟 Quantumult X 的实际命中。"""
import unittest
from build import Resolver, normalize


class ConversionTests(unittest.TestCase):
    def test_selective_include_requires_positive_and_negative_attributes(self):
        r=Resolver({'base':'a.example @cn\nb.example @cn @ads\nc.example\n',
                    'target':'include:base @cn @-ads'})
        self.assertEqual([e[1] for e in r.resolve('target')],['a.example'])

    def test_affiliation_adds_to_virtual_list(self):
        r=Resolver({'base':'a.example &virtual'})
        self.assertEqual(r.resolve('virtual')[0][1],'a.example')

    def test_cycle_fails(self):
        with self.assertRaises(ValueError):
            Resolver({'a':'include:b','b':'include:a'}).resolve('a')

    def test_missing_include_fails(self):
        with self.assertRaises(ValueError):
            Resolver({'a':'include:missing'}).resolve('a')

    def test_exact_and_suffix_keep_their_meaning(self):
        self.assertEqual(normalize(('full','A.Example',frozenset(),'source',1))[0],('host','a.example'))
        self.assertEqual(normalize(('domain','a.example',frozenset(),'source',1))[0],('host-suffix','a.example'))

    def test_shared_roots_ads_regex_and_ips_are_quarantined(self):
        entries=[('domain','cloudfront.net',frozenset(),'s',1),
                 ('full','a.example',frozenset({'ads'}),'s',1),
                 ('regexp','.*example',frozenset(),'s',1),
                 ('domain','127.0.0.1',frozenset(),'s',1)]
        for entry in entries:
            with self.subTest(entry=entry):
                self.assertIsNone(normalize(entry)[0])

    def test_dedicated_host_under_shared_cdn_is_retained(self):
        self.assertEqual(normalize(('full','product.cloudfront.net',frozenset(),'s',1))[0],('host','product.cloudfront.net'))


if __name__=='__main__':
    unittest.main()
