"""
The Five language

The language for specifying the frames and examples defining code.
Using this application you would be able to
ask the program: "Create me component like XYZ with red color"
and it would be able to create the proper code

Maybe the language for the user would be different but the
idea is exact same.

It would be possible by using the Minsky idea of frames and examples.
We here will define some useful frames and some examples.
Users will be able to put here their own either custom frames or examples

We will be asking the system for some functionality and using 
reverse matching it will look for most appropriate example and
fill out the details that the user will propose
"""

from flang_parser2 import FlangParser, FlangTextProcessor


def main(filename):
    with open(filename) as f:
        ...


DUMMY_TEST_TEMPLATE = """
<component name="import">
from <predicate name="module" pattern="{vname}"/> import <predicate name="object" pattern="{vname}"/>
</component>
"""

DUMMY_TEST_SAMPLE_1 = "from json import dumps"
DUMMY_TEST_SAMPLE_2 = "from itertools import chain"


def dummy_main():
    interpreter = FlangParser()
    flang_ast = interpreter.parse_text(DUMMY_TEST_TEMPLATE)
    match_processor = FlangTextProcessor(flang_ast)
    ret = match_processor.run(DUMMY_TEST_SAMPLE_1)

    print(ret)
    print(ret.to_dict())
    print(ret.to_flat_dict())
    # interpreter.feed(DUMMY_TEST_SAMPLE_1)
    # interpreter.feed(DUMMY_TEST_SAMPLE_2)
    # generator = parse_text(DUMMY_TEST_TEMPLATE)
    # generator.feed(DUMMY_TEST_SAMPLE_1)
    # generator.feed(DUMMY_TEST_SAMPLE_2)
    # print(generator.samples)

    # generated = interpreter.generate({"object": "chain"})
    # print(generated)


if __name__ == "__main__":
    dummy_main()
