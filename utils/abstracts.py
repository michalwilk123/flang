import abc
from .dataclasses import (
    IntermediateFlangTreeElement,
    FlangObject,
    BaseFlangConstruct,
)
from typing import TypeVar
import dataclasses

T = TypeVar("T")


class TextToIntermediateTreeParser(abc.ABC):
    @abc.abstractmethod
    def parse(self, text: str) -> IntermediateFlangTreeElement:
        ...


class SingleFileParser(abc.ABC):
    @abc.abstractmethod
    def parse(self, intermediate_tree: IntermediateFlangTreeElement) -> FlangObject:
        ...

    @abc.abstractmethod
    def get_constructs_classes(self) -> dict[str, BaseFlangConstruct]:
        ...


class FlangProcessor(abc.ABC):
    @abc.abstractmethod
    def __init__(self, flang_object: FlangObject):
        ...

    @abc.abstractmethod
    def run(self, *args: any, **kwargs: any) -> any:
        ...

    # food for thought..
    # @abc.abstractmethod
    # def forward(self, *args: any, **kwargs: any) -> any:
    #     ...

    # @abc.abstractmethod
    # def backward(self, *args: any, **kwargs: any) -> any:
    #     ...
    
    @property
    @abc.abstractmethod
    def input_type(self) -> type:
        ...

    @property
    @abc.abstractmethod
    def output_type(self) -> type:
        ...
