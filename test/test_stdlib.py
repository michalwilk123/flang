from unittest import TestCase
import lang.builtins.core as core


class StdLibTestCase(TestCase):
    def test_defr(self):
        core.defr("component", "proc")
