import unittest
import lancet

LANCET_RESULT = """-s 10.90.44.220:8000 -p 1234 -t 8 -c 128 -g exp -a synthetic:fixed:10 -l open
Load rate = 10000
#ReqCount	QPS	RxBw	TxBw
69583	13916.007178094213	143101.10389297415	143097.90402928836
#Avg Lat	50th	90th	95th	99th
23	22	26	30	37

Load rate = 15000
#ReqCount	QPS	RxBw	TxBw
94768	18952.891161870546	183500.33708739295	183501.93702755516
#Avg Lat	50th	90th	95th	99th
23	22	28	31	41
"""

class LancetParsing(unittest.TestCase):
    def test_group_measurements(self):
        grp1 = [
            'Load rate = 10000',
            '#ReqCount	QPS	RxBw	TxBw',
            '69583	13916.007178094213	143101.10389297415	143097.90402928836',
            '#Avg Lat	50th	90th	95th	99th',
            '23	22	26	30	37'
        ]

        _, groups = lancet.group_results(LANCET_RESULT)
        self.assertEqual(len(groups), 2)
        self.assertEqual(groups[0], grp1)

    def test_find_options(self):
        expected = "-s 10.90.44.220:8000 -p 1234 -t 8 -c 128 -g exp -a synthetic:fixed:10 -l open"
        opt, _ = lancet.group_results(LANCET_RESULT)
        self.assertEqual(expected, opt)

    def test_parse_group(self):
        grp = lancet.group_results(LANCET_RESULT)[1][0]
        grp = lancet.parse_group(grp)

        self.assertEqual(grp.target_rate, 10000)
        self.assertAlmostEqual(grp.rate, 13916, places=0)
        self.assertAlmostEqual(grp.latency_avg, 23, places=0)
        self.assertAlmostEqual(grp.latency_percentiles[50], 22, places=0)

    def test_wrapper(self):
        data = lancet.parse_results(LANCET_RESULT)
        self.assertAlmostEqual(data[1].rate, 18953, places=0)
