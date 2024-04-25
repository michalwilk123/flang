from unittest import TestCase
from lang.parser import parse


class ParserTestCase(TestCase):
    def test_parser(self):
        parse("lang/lib/samples/test/variables.flang.xml")
        print("DNSJKA")
