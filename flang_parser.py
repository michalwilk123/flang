import xml.etree.ElementTree as ET
from typing import TypeVar
from collections import defaultdict
from constructs import FlangConstructsMapping
from utils_old import interlace
from tree import FlangComponent, IntermediateFlangTreeElement, FlangASTBuilder
import os
import logging

T = TypeVar("T")
logger = logging.getLogger(__name__)

BUILTIN_PATTERNS = {
    "vname": r"[A-Za-z]\w+",
    "number": r"-?(([1-9]+\d*)|0)(\.\d*)?",
    "string": r"((?:\\)\"[^\"]*(?:\\)\")|((?:\\)'[^\']*(?:\\)')",
}


# class FlangUtilities:
#     def component(self, children=[], is_root=False, **attrs):
#         return FlangComponent(name=attrs["name"], children=children, is_root=is_root)

#     def predicate(self, pattern, name, **attrs):
#         return FlangPredicate(pattern, name)

#     def use(self, **attrs):
#         raise NotImplementedError

#     def rule(self, **attrs):
#         raise NotImplementedError


class FlangCodeGenerator:
    def __init__(self, root_component: FlangComponent) -> None:
        self.root: FlangComponent = root_component
        self.samples: list[defaultdict] = []

    def feed(self, text):
        sample, _ = self.root.match(text)
        self.samples.append(defaultdict(None, sample))

    def fix_incomplete_spec(self, incomplete_spec: dict):
        similarities = []
        for sample in self.samples:
            sim = sum(1 for key, value in sample.items() if incomplete_spec.get(key) == value)
            similarities.append(sim)

        idx_of_most_similar = similarities.index(max(similarities))
        incomplete_spec.update(self.samples[idx_of_most_similar])
        return incomplete_spec  # todo: should be pure!

    def generate(self, incomplete_spec: dict):
        spec = self.fix_incomplete_spec(incomplete_spec)
        generated_text, config = self.root.generate(spec)

        assert len(config) == 0

        return generated_text


class FlangInterpreter:
    def __init__(self) -> None:
        self.externals_to_load = []

    def _build_tree(self, spec: ET.Element, is_root=False):
        tag = spec.tag

        # assert hasattr(FlangUtilities, tag), f"Cannot find class {tag}"

        try:
            FlangConstructsMapping.get(tag)
        except KeyError as error:
            raise NotImplementedError(f"Cannot find class {tag}") from error

        func = getattr(self, tag)
        children = []

        for item in interlace(spec.itertext(), spec):
            if isinstance(item, str):
                children.append(item)
            else:
                children.append(self._build_tree(item, is_root=False))

        # after this step, the tree should be evaluated again
        # because of hoisting and stuff..
        return func(children=children, is_root=is_root, **spec.attrib)

    def build_intermediate_tree_from_xml(
        self,
        element: ET.Element | str,
        index: int = 0,
        last_element: bool = True,
    ) -> IntermediateFlangTreeElement | None:
        if isinstance(element, str):
            if index == 0:
                element = element.removeprefix("\n")
            if last_element:
                element = element.removesuffix("\n")

            return IntermediateFlangTreeElement("text", element) if element else None

        children = list(interlace(element.itertext(), element))

        children: list[IntermediateFlangTreeElement] = [
            self.build_intermediate_tree_from_xml(
                child, index=idx, last_element=idx == len(children) - 1
            )
            for idx, child in enumerate(children)
        ]
        children = list(filter(None, children))

        return IntermediateFlangTreeElement(
            name=element.tag, value=children, attributes=element.attrib
        )

    def parse_xml_tree(self, text: str):
        parsed_spec = ET.fromstring(text)
        return self.build_intermediate_tree_from_xml(parsed_spec)

    def parse_xml_tree_from_path(self, filename: str):
        with open(filename, "w") as f:
            return self.parse_xml_tree(f.read())

    def build_tree_from_text(self, text):
        parsed_spec = ET.fromstring(text)
        return self._build_tree(parsed_spec, is_root=True)

    def perform_evaluation(self, obj) -> ET.Element:
        ...

    def execute(self, text: str, path=None):
        path = path or os.getcwd()
        intermediate_tree = self.parse_xml_tree(text)

        ast_builder = FlangASTBuilder(intermediate_tree, path)

        return intermediate_tree
        files_to_load = ast_builder.initialize(intermediate_tree)

        while files_to_load:
            intermediate_trees = []

            for filename in files_to_load:
                intermediate_trees.append(self.parse_xml_tree_from_path(filename))

            files_to_load = ast_builder.consume(intermediate_trees)
            ## TODO: dodaj jakies logi czy cos..

        ast_builder.link()
        ast_builder.evaluate()

        # tree = self._build_tree(parsed_spec, is_root=True)

        # assert isinstance(tree, FlangComponent)
        # self.perform_evaluation(tree)

        return tree

    def process_from_path(self, path: str):
        ...

    def feed(self, sample: str) -> None:
        ...

    def generate(self, spec: dict) -> str:
        ...


def parse_text(text: str):
    parser = FlangInterpreter()
    # tree = parser.build_tree_from_text(text)
    tree = parser.execute(text)
    sample_generator = FlangCodeGenerator(tree)
    return sample_generator


def parse(filepath):
    """
    1. We match all start expressions and end expressions
    2. We build the stack with all symbols and values
    3. We build new stack with expressions
    4. We reduce new stack till its empty, executing the code inside
    """
    ...
    tree = ET.parse(filepath)
    root = tree.getroot()

    for item in root:
        if attributes := item.attrib:
            print(attributes)

        print(item)
