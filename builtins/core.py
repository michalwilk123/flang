### Component related


def defc(body, **params):
    """
    Define the component object. Core of the entire language
    """
    ...


def defoc(body, **params):
    ...


def defpc():
    """
    Modify the property of the current filename.
    Takes function in body and returns
    """
    ...


def defr(component, procedure, **params):
    """
    Create a rule for some component. The position of this function is irrelevant as
    it will be called
    """
    exec("print('hello from flang!')")
    return component


def defa():
    """
    Associate some component with other component
    """
    ...
