from __future__ import annotations
from dataclasses import dataclass
import re
import abc
from typing import TypeVar

BUILTIN_PATTERNS = {
    "vname": r"[A-Za-z]\w+",
    "number": r"-?(([1-9]+\d*)|0)(\.\d*)?",
    "string": r"((?:\\)\"[^\"]*(?:\\)\")|((?:\\)'[^\']*(?:\\)')",
}

T = TypeVar("T")


@dataclass
class BaseFlangConstruct:
    children_or_values: list[BaseFlangConstruct] | str
    attributes: dict[str, str] | None
    external_dependencies: list[str]
    parent: None | BaseFlangConstruct = None
    path: None | str = None


class MatchingConstruct(abc.ABC):
    """
    Implementing this makes the construct able to match strings from text
    """

    @abc.abstractmethod
    def match(self, text: str, pos: int) -> tuple[dict, int] | None:
        ...

    @abc.abstractmethod
    def generate(self, config: dict[T]) -> tuple[str, dict[T]]:
        ...

    @property
    def can_match(self) -> bool:
        return True


class AccessibleConstruct(abc.ABC):
    """
    Implementing this makes the construct able to being imported from outside
    """

    @property
    @abc.abstractmethod
    def symbol(self) -> str:
        raise NotImplementedError


class LinkableConstruct:
    """
    Implementing this makes the construct take a part in link step
    """

    def link(self, symbol_table: dict[str, AccessibleConstruct]) -> bool:
        """
        Return True if some additional linking is necessary
        """
        raise NotImplementedError


class FlangComponent(BaseFlangConstruct, MatchingConstruct, AccessibleConstruct):
    name = "component"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.component_type = self.attributes.get("type", "matcher")

    @property
    def symbol(self):
        return self.attributes.get("name", "anonymous")

    def can_match(self) -> bool:
        return self.component_type != "definition"

    @property
    def matchers(self):
        return [child for child in self.children if child.can_match()]

    def match(self, text):
        sample = {}
        start = 0

        for matcher in self.matchers:
            match = matcher.match(text, start)

            if not match:
                assert False, "Could not match the text!"

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


class FlangPredicate(BaseFlangConstruct, MatchingConstruct):
    name = "predicate"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._raw_pattern = self.attributes["pattern"]
        self.pattern = re.compile(self._raw_pattern.format(**BUILTIN_PATTERNS))

    def generate(self, config):
        value = config.pop(self.name)
        return value, config

    def match(self, text, pos=0):
        match = self.pattern.match(text, pos)
        return match and ({self.name: match.group()}, match.end())

    @property
    def symbol(self):
        return self.attributes["name"]


class FlangRawText(BaseFlangConstruct, MatchingConstruct):
    name = "text"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.value = self.children_or_values

    def match(self, text, pos):
        if text.startswith(self.value, pos):
            return {}, len(self.value) + pos

    def generate(self, config):
        return self.value, config

    @property
    def symbol(self):
        return f'"{self.value}"'


class FlangRule(BaseFlangConstruct):
    name = "rule"


class FlangChoice(BaseFlangConstruct, AccessibleConstruct):
    name = "choice"


class FlangReference(BaseFlangConstruct, LinkableConstruct):
    name = "use"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        if "/" in self.attributes["ref"]:
            self.external_dependencies.append(self.attributes["ref"])

    def link(self, symbol_table: dict[str, AccessibleConstruct], path):
        component = self.find_component_from_path(self.attributes["ref"])


FlangConstructs = [
    FlangComponent,
    FlangPredicate,
    FlangRawText,
    FlangChoice,
    FlangReference,
]

FlangConstructsMapping = {constr.name: constr for constr in FlangConstructs}
