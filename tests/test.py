from expect.expect import expect #, promote

@expect('Some')
def test1():
    return 'None'

# promoting will make this a string "5"
@expect((lambda x: repr(x))(5))
def test_function():
    return "4"


@expect('None')
def test_cast():
    return None

def multiline():
    return repr("""Fail
    Malti
    Line""")

@expect("'Fail\\n    Malti\\n    Line'")
def test_multiline():
    return multiline()
