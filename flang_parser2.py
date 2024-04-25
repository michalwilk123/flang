from __future__ import annotations
import os
import xml.etree.ElementTree as ET
import warnings
import functools

from utils.dataclasses import (
    BaseFlangConstruct,
    FlangObject,
    IntermediateFlangTreeElement,
    FlangMatchObject,
    Postition,
)
from utils.abstracts import (
    TextToIntermediateTreeParser,
    SingleFileParser,
    FlangProcessor,
)
from utils.helpers import interlace
import utils.constructs as c


class FlangXMLParser(TextToIntermediateTreeParser):
    def _build_tree(
        self,
        element: ET.Element | str,
        index: int = 0,
        last_element: bool = True,
    ):
        if isinstance(element, str):
            if index == 0:
                element = element.removeprefix("\n")
            if last_element:
                element = element.removesuffix("\n")

            return IntermediateFlangTreeElement("text", element) if element else None

        children_list = [item for item in interlace(element.itertext(), element)]

        children: list[IntermediateFlangTreeElement] = (
            self._build_tree(child, index=idx, last_element=idx == len(children_list) - 1)
            for idx, child in enumerate(children_list)
        )
        children = list(filter(None, children))

        return IntermediateFlangTreeElement(
            name=element.tag, value=children, attributes=element.attrib
        )

    def parse(self, text: str) -> IntermediateFlangTreeElement:
        processed_xml = ET.fromstring(text)
        return self._build_tree(processed_xml)


class FlangStandardParser(SingleFileParser):
    CONSTRUCTS = {
        constr.name: constr
        for constr in [
            c.FlangComponent,
            c.FlangPredicate,
            c.FlangRawText,
            c.FlangChoice,
            c.FlangReference,
            c.FlangRule,
        ]
    }

    def get_constructs_classes(self) -> dict[str, BaseFlangConstruct]:
        return super().get_constructs_classes()

    def _build_construct(
        self,
        flang_object: FlangObject,
        intermediate_tree: IntermediateFlangTreeElement,
        location="",
    ):
        construct_class = self.CONSTRUCTS[intermediate_tree.name]

        construct_obj = construct_class(
            children_or_value=intermediate_tree.value if isinstance(intermediate_tree.value, str) else None,
            attributes=intermediate_tree.attributes,
            parent=location,
        )
        assert isinstance(construct_obj, BaseFlangConstruct)

        symbol_full_name = construct_obj.get_full_location()

        if isinstance(intermediate_tree.value, list):
            construct_obj.children_or_value = [
                self._build_construct(flang_object, child, symbol_full_name)
                for child in intermediate_tree.value
            ]

        if not location:
            flang_object.root = symbol_full_name

        flang_object.symbols[symbol_full_name] = construct_obj
        # if isinstance(construct_obj, AccessibleConstruct):
        #     self.symbols[construct_obj.path] = construct_obj

        return construct_obj

    def parse(self, intermediate_tree: IntermediateFlangTreeElement) -> FlangObject:
        flang_object = FlangObject()
        self._build_construct(flang_object, intermediate_tree)
        return flang_object

class FlangInfererProcessor(FlangProcessor):
    ...

class FlangTextProcessor(FlangProcessor):
    """
    How matcher works
    f(x) = matcher(schema).forward
    f'(x) = matcher(schema).backward

    f(a) -> b
    f'(b) -> a'
    a is equivalent to a'

    Forward pass through processor generates source code from provided schema based on the flang object
    Backward pass through processor generates schema with parameters based on source code
    """
    def __init__(self, flang_object: FlangObject, stop_on_error: bool = False) -> any:
        self.root = flang_object.root_component
        self.object = flang_object
        self.stop_on_error = stop_on_error

    def return_without_match(self, reason=""):
        if self.stop_on_error:
            raise RuntimeError(f"Could not match component. Reason: {reason}")

    @functools.singledispatchmethod
    def _match(self, construct, *args, **kwargs) -> FlangMatchObject | None:
        raise NotImplementedError

    @_match.register
    def __dispatched_match(
        self, construct: c.FlangComponent, text: str, start_position: int = 0
    ) -> FlangMatchObject | None:
        """
        Component can only match based on its children
        """
        spec = {}
        end_position = start_position

        for child in construct.children:
            match_object = self.match(child, text, end_position)

            if match_object is not None:
                if child.symbol:
                    spec[child.symbol] = match_object

                end_position = match_object.position.end

        return FlangMatchObject(position=Postition(start_position, end_position), spec_or_matched=spec)

    @_match.register
    def __dispatched_match(
        self, construct: c.FlangRawText, text: str, start_position: int = 0
    ) -> FlangMatchObject | None:
        if text.startswith(construct.value, start_position):
            return FlangMatchObject(
                position=Postition(start_position, len(construct.value) + start_position),
                spec_or_matched=construct.value,
            )

    @_match.register
    def __dispatched_match(
        self, construct: c.FlangPredicate, text: str, start_position: int = 0
    ) -> FlangMatchObject | None:
        if match := construct.pattern.match(text, start_position):
            return FlangMatchObject(
                position=Postition(start_position, match.end()),
                spec_or_matched=match.group(),
            )

    @_match.register
    def __dispatched_match(
        self, construct: c.FlangReference, *args, **kwargs
    ) -> FlangMatchObject | None:
        referenced_object = self.object.find_refrenced_object(symbol := construct.attributes["ref"])
        assert referenced_object, f"Cannot find object {symbol}"

        return self._match(referenced_object, *args, **kwargs)

    def match(self, construct: c.FlangReference, *args, **kwargs):
        if not self.can_construct_match(construct):
            return None

        result = self._match(construct, *args, **kwargs)
        return self.return_without_match() if result is None else result

    def run(self, sample: str) -> FlangMatchObject | None:
        return self.match(self.root, sample)

    @staticmethod
    def can_construct_match(construct: c.BaseFlangConstruct):
        if isinstance(construct, c.FlangComponent):
            return construct.attributes.get("name") != "definition"
        if isinstance(construct, (c.FlangRawText, c.FlangPredicate)):
            return True
        return False


class FlangParser:
    def __init__(self) -> None:
        self.intermediate_parser: TextToIntermediateTreeParser = FlangXMLParser()
        self.single_file_parser_class: SingleFileParser = FlangStandardParser
        self.single_file_parsers: dict = {}
        self.symbol_table = {}

    def parse_text(self, text: str, path: str | None = None, evaluate: bool = True):
        path = path or os.getcwd()
        intermediate_tree = self.intermediate_parser.parse(text)
        assert intermediate_tree.name == "component"  # sanity check

        # self._evaluate_intermediate_tree(intermediate_tree)

        subparser = FlangStandardParser()
        self.single_file_parsers[path] = subparser
        flang_object = subparser.parse(intermediate_tree)
        global_symbols = self.translate_local_symbol_table_to_global(flang_object.symbols, path)

        assert (
            not self.symbol_table.keys() & global_symbols.keys()
        ), "Symbols are repeating! Possible recursive import"
        self.symbol_table.update(global_symbols)

        for dependency in flang_object.external_dependencies:
            if dependency not in self.symbol_table:
                source, _ = dependency.split(":")
                self.parse_file(source, evaluate=False)

        if evaluate:
            # This is the file we return to user.
            # We should perform optimizations and stuff
            self.perform_optimizations(flang_object)

        return flang_object

    def parse_file(self, filepath: str, evaluate: bool = True):
        with open(filepath) as f:
            return self.parse_text(f.read(), filepath, evaluate)

    def translate_local_symbol_table_to_global(self, symbol_table: dict, path: str) -> dict:
        return {f"{path}:{symbol}": value for symbol, value in symbol_table.items()}

    def _evaluate_intermediate_tree(self, intermediate: IntermediateFlangTreeElement):
        ...

    def perform_optimizations(self, root: FlangObject):
        warnings.warn("Optimizations not implemented!")
