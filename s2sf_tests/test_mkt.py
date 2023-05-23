import unittest
from solvency2sf.scr_mkt.mkt import f_up


class TestFUpFunction(unittest.TestCase):
    """ Thanks chat GPT for writing this """
    def test_f_up_bonds(self):
        cc_step = 3
        duration = 8.5
        expected_result = 0.68

        result = f_up(cc_step, duration, type='bonds')
        self.assertAlmostEqual(result, expected_result, places=2)

    def test_f_up_ri_no_mcr(self):
        cc_step = 2
        duration = 6.5
        expected_result = 0.635

        result = f_up(cc_step, duration, type='ri_no_mcr')
        self.assertAlmostEqual(result, expected_result, places=2)

    def test_f_up_gov_eea(self):
        cc_step = 4
        duration = 10.0
        expected_result = 0.0

        result = f_up(cc_step, duration, type='gov_eea')
        self.assertAlmostEqual(result, expected_result, places=2)

    def test_f_up_sec_type1(self):
        cc_step = 1
        duration = 7.0
        expected_result = 0.294

        result = f_up(cc_step, duration, type='sec_type1')
        self.assertAlmostEqual(result, expected_result, places=2)

    def test_f_up_resec(self):
        cc_step = 5
        duration = 12.5
        expected_result = 1.0

        result = f_up(cc_step, duration, type='resec')
        self.assertAlmostEqual(result, expected_result, places=2)

if __name__ == '__main__':
    unittest.main()