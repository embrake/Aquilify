import copy
import itertools
import operator
from functools import wraps

class cached_property:
    name = None

    @staticmethod
    def func(instance):
        raise TypeError(
            "Cannot use cached_property instance without calling "
            "__set_name__() on it."
        )

    def __init__(self, func):
        self.real_func = func
        self.__doc__ = getattr(func, "__doc__")

    def __set_name__(self, owner, name):
        if self.name is None:
            self.name = name
            self.func = self.real_func
        elif name != self.name:
            raise TypeError(
                "Cannot assign the same cached_property to two different names "
                "(%r and %r)." % (self.name, name)
            )

    def __get__(self, instance, cls=None):
        if instance is None:
            return self
        res = instance.__dict__[self.name] = self.func(instance)
        return res


class classproperty:
    def __init__(self, method=None):
        self.fget = method

    def __get__(self, instance, cls=None):
        return self.fget(cls)

    def getter(self, method):
        self.fget = method
        return self


class Promise:
    pass


def lazy(func, *resultclasses):
    class __proxy__(Promise):
        def __init__(self, args, kw):
            self._args = args
            self._kw = kw

        def __reduce__(self):
            return (
                _lazy_proxy_unpickle,
                (func, self._args, self._kw) + resultclasses,
            )

        def __deepcopy__(self, memo):
            memo[id(self)] = self
            return self

        def __cast(self):
            return func(*self._args, **self._kw)

        def __repr__(self):
            return repr(self.__cast())

        def __str__(self):
            return str(self.__cast())

        def __eq__(self, other):
            if isinstance(other, Promise):
                other = other.__cast()
            return self.__cast() == other

        def __ne__(self, other):
            if isinstance(other, Promise):
                other = other.__cast()
            return self.__cast() != other

        def __lt__(self, other):
            if isinstance(other, Promise):
                other = other.__cast()
            return self.__cast() < other

        def __le__(self, other):
            if isinstance(other, Promise):
                other = other.__cast()
            return self.__cast() <= other

        def __gt__(self, other):
            if isinstance(other, Promise):
                other = other.__cast()
            return self.__cast() > other

        def __ge__(self, other):
            if isinstance(other, Promise):
                other = other.__cast()
            return self.__cast() >= other

        def __hash__(self):
            return hash(self.__cast())

        def __format__(self, format_spec):
            return format(self.__cast(), format_spec)

        def __add__(self, other):
            return self.__cast() + other

        def __radd__(self, other):
            return other + self.__cast()

        def __mod__(self, other):
            return self.__cast() % other

        def __mul__(self, other):
            return self.__cast() * other
        
    for resultclass in resultclasses:
        for type_ in resultclass.mro():
            for method_name in type_.__dict__:
                if hasattr(__proxy__, method_name):
                    continue

                def __wrapper__(self, *args, __method_name=method_name, **kw):
                    result = func(*self._args, **self._kw)
                    return getattr(result, __method_name)(*args, **kw)

                setattr(__proxy__, method_name, __wrapper__)

    @wraps(func)
    def __wrapper__(*args, **kw):
        return __proxy__(args, kw)

    return __wrapper__


def _lazy_proxy_unpickle(func, args, kwargs, *resultclasses):
    return lazy(func, *resultclasses)(*args, **kwargs)


def lazystr(text):
    return lazy(str, str)(text)


def keep_lazy(*resultclasses):
    if not resultclasses:
        raise TypeError("You must pass at least one argument to keep_lazy().")

    def decorator(func):
        lazy_func = lazy(func, *resultclasses)

        @wraps(func)
        def wrapper(*args, **kwargs):
            if any(
                isinstance(arg, Promise)
                for arg in itertools.chain(args, kwargs.values())
            ):
                return lazy_func(*args, **kwargs)
            return func(*args, **kwargs)

        return wrapper

    return decorator


def keep_lazy_text(func):
    return keep_lazy(str)(func)


empty = object()


def new_method_proxy(func):
    def inner(self, *args):
        if (_wrapped := self._wrapped) is empty:
            self._setup()
            _wrapped = self._wrapped
        return func(_wrapped, *args)

    inner._mask_wrapped = False
    return inner


class LazyObject:
    _wrapped = None

    def __init__(self):
        self._wrapped = empty

    def __getattribute__(self, name):
        if name == "_wrapped":
            return super().__getattribute__(name)
        value = super().__getattribute__(name)
        if not getattr(value, "_mask_wrapped", True):
            raise AttributeError
        return value

    __getattr__ = new_method_proxy(getattr)

    def __setattr__(self, name, value):
        if name == "_wrapped":
            self.__dict__["_wrapped"] = value
        else:
            if self._wrapped is empty:
                self._setup()
            setattr(self._wrapped, name, value)

    def __delattr__(self, name):
        if name == "_wrapped":
            raise TypeError("can't delete _wrapped.")
        if self._wrapped is empty:
            self._setup()
        delattr(self._wrapped, name)

    def _setup(self):
        raise NotImplementedError(
            "subclasses of LazyObject must provide a _setup() method"
        )
    
    def __reduce__(self):
        if self._wrapped is empty:
            self._setup()
        return (unpickle_lazyobject, (self._wrapped,))

    def __copy__(self):
        if self._wrapped is empty:
            return type(self)()
        else:
            return copy.copy(self._wrapped)

    def __deepcopy__(self, memo):
        if self._wrapped is empty:
            result = type(self)()
            memo[id(self)] = result
            return result
        return copy.deepcopy(self._wrapped, memo)

    __bytes__ = new_method_proxy(bytes)
    __str__ = new_method_proxy(str)
    __bool__ = new_method_proxy(bool)
    __dir__ = new_method_proxy(dir)

    __class__ = property(new_method_proxy(operator.attrgetter("__class__")))
    __eq__ = new_method_proxy(operator.eq)
    __lt__ = new_method_proxy(operator.lt)
    __gt__ = new_method_proxy(operator.gt)
    __ne__ = new_method_proxy(operator.ne)
    __hash__ = new_method_proxy(hash)

    # List/Tuple/Dictionary methods support
    __getitem__ = new_method_proxy(operator.getitem)
    __setitem__ = new_method_proxy(operator.setitem)
    __delitem__ = new_method_proxy(operator.delitem)
    __iter__ = new_method_proxy(iter)
    __len__ = new_method_proxy(len)
    __contains__ = new_method_proxy(operator.contains)


def unpickle_lazyobject(wrapped):
    return wrapped


class SimpleLazyObject(LazyObject):

    def __init__(self, func):
        self.__dict__["_setupfunc"] = func
        super().__init__()

    def _setup(self):
        self._wrapped = self._setupfunc()

    def __repr__(self):
        if self._wrapped is empty:
            repr_attr = self._setupfunc
        else:
            repr_attr = self._wrapped
        return "<%s: %r>" % (type(self).__name__, repr_attr)

    def __copy__(self):
        if self._wrapped is empty:
            return SimpleLazyObject(self._setupfunc)
        else:
            return copy.copy(self._wrapped)

    def __deepcopy__(self, memo):
        if self._wrapped is empty:
            result = SimpleLazyObject(self._setupfunc)
            memo[id(self)] = result
            return result
        return copy.deepcopy(self._wrapped, memo)

    __add__ = new_method_proxy(operator.add)

    @new_method_proxy
    def __radd__(self, other):
        return other + self


def partition(predicate, values):
    """
    Split the values into two sets, based on the return value of the function
    (True/False). e.g.:

        >>> partition(lambda x: x > 3, range(5))
        [0, 1, 2, 3], [4]
    """
    results = ([], [])
    for item in values:
        results[predicate(item)].append(item)
    return results