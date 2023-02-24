
expect.py
=======

Expect.py is an expect testing framework fashioned after the [expect-test](https://github.com/janestreet/ppx_expect) ocaml framework (ppx_expect). Under this framework tests are functions that return a value that can be represented as a string (or something where calling `repr` on it is meaningful). These tests contain an expect decorator with the expected output of the function call. When the file is run, the expect framework will check the output of each function against the value passed to the decorator. The test can be "promoted", meaning the expected value will be automatically replaced with real output value.

There are two primary benefits to this style of testing:

1. Standard string diffs are used to compare outputs to expected values, freeing the programmer from manually writing in-depth comparisons

2. The auto-promotion mechanic saves time when first writing tests for functions that have correct behaviour


It is easier to show with an example, suppose you have a file `test.py` with the following contents.
```python
from expect.expect import expect

@expect("Some")
def silly_test():
    return "None"
```

Running `python test.py` will produce the below output ([with colour](./media/example_colours.png)).
```
silly_test at line no. 3 failed
@expect(Some)
@actual(None)
def silly_test():
    return "None"
```

Instead of manually updated the expected value, line 3 of `test.py` can be edited to enabled auto-promotion. Here, promoting means that the expected value will be replaced with the real value right in the source file! A copy of the original file before promotion will be saved 

```python
@expect("Some", promote=True)
# or using another decorator
from expect.expect import promote
@promote
@expect("Some")
```

Both promotion syntaxes are the same, it's just personal preference. After the promotion takes place the promotion parameter (or decorator) will be removed. This means there is always manual intervention required for each test to be auto-changed.

That's it! Those two simple decorators enable an alternative testing workflow that is much lighter weight (for the programmer). I made heavy use of expect.py while working on my master's thesis as a sort of REPL that stores and validates changes. I don't currently use it in any projects, so use at your own risk.


# Gotchas
## Multi-line strings
Multi-line strings don't work properly. They must be wrapped in a `repr` call before return from the test function. For example

```python
@expect('\n    some\n    multiline\n    string\n    ')
def less_silly_test():
    return repr("""
    some
    multiline
    string
    """)
```

## Backups
Every time a test is promoted, a backup file is created (just in case something goes horribly wrong, in practice we don't expect anything to go wrong but this provides a safety net for those who are nervous about machine edited code). The backup will be overridden if multiple tests are promoted at the same time. If you're nervous about the framework editing your code files, consider only promoting a single test at a time.

