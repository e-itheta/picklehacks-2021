# Author: Kevin Lai <kevinlai31@gmail.com> 2021


class _InterfaceType(type):
    # Create Interface types from class annotations. The purpose of this metaclass
    # is to create types that merge static type hinting and dynamic member access
    # Do not use this class directly. Use the base class "Interface" instead

    def __init__(self, *args, **kwargs):

        annot = {} # Store annotation definition of bases
        for base in self.__mro__[::1]:
            annot.update(getattr(base, "__annotations__", {}))

        self.anotations = annot

        def create_getset(name):
            # Inject getter and setter definition

            def getter(obj):
                if name in obj:
                    return obj[name]
                return None

            
            def setter(obj, value):
                assert value is None or isinstance(value, (
                    str, float, list, dict, bool, int
                )), "Value is not json serializable"
                obj[name] = value

            return getter, setter

        for name in annot.keys():
            setattr(self, name, property(*create_getset(name)))
    
    

class Interface(dict, metaclass=_InterfaceType):
    pass


