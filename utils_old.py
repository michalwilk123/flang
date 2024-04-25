import itertools


def interlace(*iterables):
    for items_to_yield in itertools.zip_longest(*iterables):
        for item in items_to_yield:
            if item is not None:
                yield item
