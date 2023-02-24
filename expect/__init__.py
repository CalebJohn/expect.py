"""@expect

Example Usage:

@expect("Some result")
def some_test_function():
    return some_function_that_returns_some_result()



In circumstances where it can be laborious to type out the result, and it is known
that the function will return the correct result (this is useful when adding @expect
tests to a lib that is already known to work correctly) the value of string inside
@expect can be explicitly promoted using the keyword promote or by adding another decorator
@promote on top.
Promotion happens when the code file is run, and will automatically update the file with
a new expect string
Note that no other decorator is allowed to be used on the test
function as it would lead to unexpected results.


Example of promotion

@expect("", promote=True) # this line would be replaced with @expect("Some result")
def some_test_function():
    return some_function_that_returns_some_result()

or
@promote
@expect("") # this line would be replaced with @expect("Some result")
def some_test_function():
    return some_function_that_returns_some_result()

"""

