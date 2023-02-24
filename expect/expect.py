from expect.lib import (_promote, _ExpectResults, diff, MalformedExpect, colored)

import inspect


def promote(details):
    """
    Alternate promotion syntax
    example:
        @promote
        @expect("Foo")
        def test():
            return "Bar"
    """
    _promote(details)

def expect(expected, promote=False):
    """
    Decoration for @expect syntax

    Parameters
    ----------
    expected : callable
        A function that returns the expected output

    promote : bool
        An option to allow the function to be autopromoted.
        Should be used carefully.

    e.g
    @expect("Some result")
    def some_test_function():
        return some_function_that_returns_some_result()

    e.g of promotion

    @expect("", promote=True) # this line would be replaced with @expect("Some result")
    def some_test_function():
        return some_function_that_returns_some_result()

    or
    @promote
    @expect("") # this line would be replaced with @expect("Some result")
    def some_test_function():
        return some_function_that_returns_some_result()
    """
    def inner(func):
        if func.__name__ != func.__code__.co_name:
            raise MalformedExpect("@expect is not compatible with other decorators")

        res = func()
        exp = expected

        first_lineno = func.__code__.co_firstlineno

        # Warnings are initially stored in a list, only to be printed if there is a mismatch
        warnings = []

        if not isinstance(exp, str):
            warnings.append(colored(("Warning at line no. {}\n"
                "@expect functions on strings, some other types may work but are unsupported and will be cast to string").format(first_lineno), 'red'))
            exp = repr(exp)
        if not isinstance(res, str):
            warnings.append(colored(("Warning at line no. {}\n"
                "@expect functions on strings, some other types may work but are unsupported and will be cast to string").format(first_lineno), 'red'))
            res = repr(res)

        if res != exp:
            print(colored("\n{} at line no. {} failed".format(func.__name__, first_lineno), 'bred'))

            for w in warnings:
                print(w)

            print(diff(exp, res))

            # Print source
            def_start = False
            for l in inspect.getsource(func).splitlines():
                if not def_start:
                    def_start = l.strip().startswith('def')
                if def_start:
                    print(l)


        results = _ExpectResults(first_lineno, res)

        if promote:
            _promote(results)

        return results

    return inner


if __name__ == "__main__":
    import functools
    def new_dec(f):
        @functools.wraps(f)
        def inner():
            print("Wrapper!!!")
            return f()
        return inner

    @expect('Failed')
    def fun():
        return 'Failed'

    @expect('Non')
    def something():
        return None

    def multiline():
        return repr("""Fai
        Malti
        Line""")

    @expect("'Fai\\n        Malti\\n        Line'")
    def test():
        return multiline()
