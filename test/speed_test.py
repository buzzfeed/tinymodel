import cProfile, pstats, StringIO

from unittest import TestCase
from nose.tools import assert_raises, eq_

from model_internals_test import MyValidTestModel

class SpeedTest(TestCase):
    def test_speed(self):
        iterations = 100
        pr = cProfile.Profile()
        pr.enable()
        for x in range(iterations):
            m = MyValidTestModel(random=True)
        pr.disable()
        s = StringIO.StringIO()
        sortby = 'cumulative'
        ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
        ps.print_stats()
        #print s.getvalue()
