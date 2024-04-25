from __future__ import annotations
import dataclasses
from utils.constructs import BaseFlangConstruct, FlangComponent
import collections

RecursiveDict = dict[str, str | dict]  # cannot do recursive types till python 3.12


@dataclasses.dataclass
class IntermediateFlangTreeElement:
    name: str
    value: list[IntermediateFlangTreeElement] | str
    attributes: dict[str, str] | None = None


@dataclasses.dataclass
class FlangObject:
    root: str = ""
    rules: list = dataclasses.field(default_factory=list)
    symbols: dict[str, BaseFlangConstruct] = dataclasses.field(default_factory=dict)
    external_dependencies: list[str] = dataclasses.field(default_factory=list)

    @property
    def root_component(self) -> FlangComponent:
        assert self.root, "Root must be initialized!"
        root = self.symbols[self.root]
        assert isinstance(root, FlangComponent), "The root construct should be a component!"

        return root

    def find_refrenced_object(self, location: str) -> BaseFlangConstruct:
        if ":" in location:
            ...


Postition = collections.namedtuple("Postition", ["start", "end"])


@dataclasses.dataclass
class FlangMatchObject:
    position: Postition
    spec_or_matched: dict[str, FlangMatchObject] | str

    def to_dict(self) -> RecursiveDict:
        if isinstance(self.spec_or_matched, str):
            return self.spec_or_matched

        assert False, "TODO: TUTAJ SKONCZYŁESSSSS AAA"
        return {
            key: value.to_dict() for key, value in self.spec_or_matched.items()
        }
        
        return {
            key: value.to_dict() for key, value in self.spec_or_matched.items()
        }


    def to_flat_dict(self) -> dict[str, str]:
        regular_dict = self.to_dict()

        flat_dict = {}

        for key, value in regular_dict.items():
            if isinstance(value, str):
                flat_dict[key] = value
            else:
                value = self.to_flat_dict(value)
                for internal_key, internal_value in value.items():
                    flat_dict[f"{key}.{internal_key}"] = internal_value

        return flat_dict

    @classmethod
    def from_flat(cls) -> dict[str, str]:
        ...

