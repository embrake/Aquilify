import re

from aquilify.utils.functional import SimpleLazyObject

ESCAPE_MAPPINGS = {
    "A": None,
    "b": None,
    "B": None,
    "d": "0",
    "D": "x",
    "s": " ",
    "S": "x",
    "w": "x",
    "W": "!",
    "Z": None,
}


class Choice(list):
    """Represent multiple possibilities at this point in a pattern string."""


class Group(list):
    """Represent a capturing group in the pattern string."""


class NonCapture(list):
    """Represent a non-capturing group in the pattern string."""


def normalize(pattern):
    result = []
    non_capturing_groups = []
    consume_next = True
    pattern_iter = next_char(iter(pattern))
    num_args = 0
    
    try:
        ch, escaped = next(pattern_iter)
    except StopIteration:
        return [("", [])]

    try:
        while True:
            if escaped:
                result.append(ch)
            elif ch == ".":
                result.append(".")
            elif ch == "|":
                # FIXME: One day we'll should do this, but not in 1.0.
                raise NotImplementedError("Awaiting Implementation")
            elif ch == "^":
                pass
            elif ch == "$":
                break
            elif ch == ")":
                start = non_capturing_groups.pop()
                inner = NonCapture(result[start:])
                result = result[:start] + [inner]
            elif ch == "[":
                ch, escaped = next(pattern_iter)
                result.append(ch)
                ch, escaped = next(pattern_iter)
                while escaped or ch != "]":
                    ch, escaped = next(pattern_iter)
            elif ch == "(":
                ch, escaped = next(pattern_iter)
                if ch != "?" or escaped:
                    name = "_%d" % num_args
                    num_args += 1
                    result.append(Group((("%%(%s)s" % name), name)))
                    walk_to_end(ch, pattern_iter)
                else:
                    ch, escaped = next(pattern_iter)
                    if ch in "!=<":
                        walk_to_end(ch, pattern_iter)
                    elif ch == ":":
                        non_capturing_groups.append(len(result))
                    elif ch != "P":
                        raise ValueError("Non-reversible reg-exp portion: '(?%s'" % ch)
                    else:
                        ch, escaped = next(pattern_iter)
                        if ch not in ("<", "="):
                            raise ValueError(
                                "Non-reversible reg-exp portion: '(?P%s'" % ch
                            )
                        if ch == "<":
                            terminal_char = ">"
                        else:
                            terminal_char = ")"
                        name = []
                        ch, escaped = next(pattern_iter)
                        while ch != terminal_char:
                            name.append(ch)
                            ch, escaped = next(pattern_iter)
                        param = "".join(name)
                        if terminal_char != ")":
                            result.append(Group((("%%(%s)s" % param), param)))
                            walk_to_end(ch, pattern_iter)
                        else:
                            result.append(Group((("%%(%s)s" % param), None)))
            elif ch in "*?+{":
                count, ch = get_quantifier(ch, pattern_iter)
                if ch:
                    consume_next = False

                if count == 0:
                    if contains(result[-1], Group):
                        result[-1] = Choice([None, result[-1]])
                    else:
                        result.pop()
                elif count > 1:
                    result.extend([result[-1]] * (count - 1))
            else:
                result.append(ch)

            if consume_next:
                ch, escaped = next(pattern_iter)
            consume_next = True
    except StopIteration:
        pass
    except NotImplementedError:
        return [("", [])]

    return list(zip(*flatten_result(result)))


def next_char(input_iter):
    for ch in input_iter:
        if ch != "\\":
            yield ch, False
            continue
        ch = next(input_iter)
        representative = ESCAPE_MAPPINGS.get(ch, ch)
        if representative is None:
            continue
        yield representative, True


def walk_to_end(ch, input_iter):
    if ch == "(":
        nesting = 1
    else:
        nesting = 0
    for ch, escaped in input_iter:
        if escaped:
            continue
        elif ch == "(":
            nesting += 1
        elif ch == ")":
            if not nesting:
                return
            nesting -= 1


def get_quantifier(ch, input_iter):
    if ch in "*?+":
        try:
            ch2, escaped = next(input_iter)
        except StopIteration:
            ch2 = None
        if ch2 == "?":
            ch2 = None
        if ch == "+":
            return 1, ch2
        return 0, ch2

    quant = []
    while ch != "}":
        ch, escaped = next(input_iter)
        quant.append(ch)
    quant = quant[:-1]
    values = "".join(quant).split(",")

    try:
        ch, escaped = next(input_iter)
    except StopIteration:
        ch = None
    if ch == "?":
        ch = None
    return int(values[0]), ch


def contains(source, inst):
    if isinstance(source, inst):
        return True
    if isinstance(source, NonCapture):
        for elt in source:
            if contains(elt, inst):
                return True
    return False


def flatten_result(source):
    if source is None:
        return [""], [[]]
    if isinstance(source, Group):
        if source[1] is None:
            params = []
        else:
            params = [source[1]]
        return [source[0]], [params]
    result = [""]
    result_args = [[]]
    pos = last = 0
    for pos, elt in enumerate(source):
        if isinstance(elt, str):
            continue
        piece = "".join(source[last:pos])
        if isinstance(elt, Group):
            piece += elt[0]
            param = elt[1]
        else:
            param = None
        last = pos + 1
        for i in range(len(result)):
            result[i] += piece
            if param:
                result_args[i].append(param)
        if isinstance(elt, (Choice, NonCapture)):
            if isinstance(elt, NonCapture):
                elt = [elt]
            inner_result, inner_args = [], []
            for item in elt:
                res, args = flatten_result(item)
                inner_result.extend(res)
                inner_args.extend(args)
            new_result = []
            new_args = []
            for item, args in zip(result, result_args):
                for i_item, i_args in zip(inner_result, inner_args):
                    new_result.append(item + i_item)
                    new_args.append(args[:] + i_args)
            result = new_result
            result_args = new_args
    if pos >= last:
        piece = "".join(source[last:])
        for i in range(len(result)):
            result[i] += piece
    return result, result_args


def _lazy_re_compile(regex, flags=0):

    def _compile():
        # Compile the regex if it was not passed pre-compiled.
        if isinstance(regex, (str, bytes)):
            return re.compile(regex, flags)
        else:
            assert not flags, "flags must be empty if regex is passed pre-compiled"
            return regex

    return SimpleLazyObject(_compile)
