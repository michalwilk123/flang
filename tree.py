from abc import ABC, abstractmethod
import re
from typing import TypeVar

BUILTIN_PATTERNS = {
    "vname": r"[A-Za-z]\w+",
    "number": r"-?(([1-9]+\d*)|0)(\.\d*)?",
    "string": r"((?:\\)\"[^\"]*(?:\\)\")|((?:\\)'[^\']*(?:\\)')",
}

T = TypeVar("T")


class FlangAbstractMatcher(ABC):
    @abstractmethod
    def match(self, text: str, pos: int) -> tuple[dict, int] | None:
        ...

    @abstractmethod
    def generate(self, config: dict[T]) -> tuple[str, dict[T]]:
        ...


from dataclasses import dataclass


@dataclass
class IntermediateFlangTreeElement:
    name: str
    value: list["IntermediateFlangTreeElement"] | str
    attributes: dict[str, str] | None = None


class FlangStringMatcher(FlangAbstractMatcher):
    def __init__(self, pattern) -> None:
        self.value = pattern

    def match(self, text, pos):
        if text.startswith(self.value, pos):
            return {}, len(self.value) + pos

    def generate(self, config):
        return self.value, config

    def __str__(self) -> str:
        return f"FlangStringMatcher(value={self.value})"


class FlangComponent(FlangAbstractMatcher):
    def __init__(
        self,
        name="",
        children=None,
        cardinality="..",
        ordering=True,
        is_root=False,
    ) -> None:
        self.children = children or []
        self.predicates = {}
        self.matchers: list[FlangAbstractMatcher] = []
        self.samples = []
        self.name = name
        self.spec = {}
        self.is_root = is_root

        for idx, child in enumerate(children):
            if isinstance(child, str):
                if idx == 0:
                    child = child.removeprefix("\n")
                elif idx == len(children) - 1:
                    child = child.removesuffix("\n")

                child = child and FlangStringMatcher(child)

            if isinstance(child, (FlangStringMatcher, FlangPredicate, FlangComponent)):
                self.matchers.append(child)

    def generate(self, config: dict[str, str]) -> str:
        generated_component = ""

        new_config = {**config}

        for key, value in config.items():
            if key.startswith(self.name):  # todo: should be a better way to do this...
                del new_config[key]
                new_config[key.removeprefix(self.name)] = value

        config = new_config  # cannot iterate through changing dictionary..

        for matcher in self.matchers:
            chunk, config = matcher.generate(config)
            generated_component += chunk

        return generated_component, config

    def match(self, text):
        sample = {}
        start = 0

        for matcher in self.matchers:
            match = matcher.match(text, start)

            if not match:
                return None

            sample_chunk, pos = match

            assert all(
                isinstance(key, str) and isinstance(value, str)
                for key, value in sample_chunk.items()
            )

            if not self.is_root:
                sample_chunk = {f"{self.name}.{key}": value for key, value in sample_chunk.items()}

            sample.update(sample_chunk)

            start = pos

        return sample, start

    def __str__(self) -> str:
        TAB = "  "
        message = f"Component(name={self.name})["
        children_message = "\nPredicates:" if self.predicates else ""

        for predicate in self.predicates.values():
            children_message += "\n" + str(predicate)

        children_message = children_message.replace("\n", f"\n{TAB}")
        message = f"{message}{children_message}\n]"

        return message


class FlangPredicate(FlangAbstractMatcher):
    def __init__(self, pattern, name="", multi=False) -> None:
        self.raw_pattern = pattern
        self.pattern = re.compile(pattern.format(**BUILTIN_PATTERNS))
        self.name = name

    def __str__(self) -> str:
        return f"FlangPredicate(name={self.name}, pattern={self.pattern})"

    def to_pattern(self):
        return re.compile(self.pattern)

    def match(self, text, pos=0):
        match = self.pattern.match(text, pos)
        return match and ({self.name: match.group()}, match.end())

    def generate(self, config):
        value = config.pop(self.name)
        return value, config


from constructs import FlangConstructs, BaseFlangConstruct, AccessibleConstruct


class FlangASTBuilder:
    FlangConstructsMapping = {constr.name: constr for constr in FlangConstructs}

    def __init__(self, root, path) -> None:
        self.symbols = {}
        self.start_path = path
        self.loaded_files = []
        self.root = self.consume_single_tree(root)

    def consume(
        self,
        intermediate_trees: list[IntermediateFlangTreeElement],
        paths: list[str],
    ) -> list[str]:
        assert len(intermediate_trees) == len(paths)

        all_files_to_load = []
        for tree, path in zip(intermediate_trees, paths):
            all_files_to_load += self.consume_single_tree(tree, path)

        return list(set(all_files_to_load))

    def consume_single_tree(
        self,
        intermediate_tree: IntermediateFlangTreeElement,
        path: str | None = None,
    ) -> list[str]:
        # construct_class = self.FlangConstructsMapping[intermediate_tree.name]
        # construct_obj =
        paths_to_load = []
        symbols = {}
        path = path or self.start_path
        path += ":"
        self._consume_tree(intermediate_tree, paths_to_load, symbols, path)

    def _consume_tree(
        self,
        intermediate_tree: IntermediateFlangTreeElement,
        parent: IntermediateFlangTreeElement,
        paths_to_load: list[str],
        path: str,
    ) -> BaseFlangConstruct:
        construct_class = self.FlangConstructsMapping[intermediate_tree.name]

        construct_obj = construct_class(
            intermediate_tree.value,
            intermediate_tree.attributes,
            paths_to_load,
            parent,
            path,
        )

        if isinstance(intermediate_tree.value, list):
            location, source = path.split(":")
            path = location + ":" + (source + "." + construct_obj.symbol).removeprefix(".")
            construct_obj.children = [
                self._consume_tree(child, construct_obj, paths_to_load, path)
                for child in intermediate_tree.value
            ]

        if isinstance(construct_obj, AccessibleConstruct):
            self.symbols[construct_obj.path] = construct_obj

        return construct_obj

    def link(self):
        """
        traverse tree and link what is necessary
        """
        ...

    def evaluate(self):
        ...
