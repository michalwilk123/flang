import itertools
import random

BUILTIN_PATTERNS = {
    "vname": r"[A-Za-z]\w+",
    "number": r"-?(([1-9]+\d*)|0)(\.\d*)?",
    "string": r"((?:\\)\"[^\"]*(?:\\)\")|((?:\\)'[^\']*(?:\\)')",
}

global_anonymous_name_counter = 0

def interlace(*iterables):
    for items_to_yield in itertools.zip_longest(*iterables):
        for item in items_to_yield:
            if item is not None:
                yield item

def create_unique_symbol(obj) -> str:
    global global_anonymous_name_counter
    symbol = f"{type(obj).__name__}@{global_anonymous_name_counter}"
    global_anonymous_name_counter += 1

    return symbol

