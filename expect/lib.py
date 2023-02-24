import ast
from difflib import Differ
import inspect
import os

colors = {'red': '\033[31m',
        'green': '\033[32m',
        'bred': '\033[91m',   # bright red
        'bgreen': '\033[92m', # bright green
        'endc': '\033[0m'}

def colored(text, color):
    """Multicolor text!"""
    return '{}{}{}'.format(colors[color], text, colors['endc'])

def diff(expected, result):
    """Performs a diff and walks the piecewise diff result to join them into a coherent string"""
    diff = Differ().compare(expected, result)
    old = ''
    new = ''
    for e in diff:
        if e.startswith("+"):
            new += colored(e[-1], "bgreen")
        elif e.startswith("-"):
            old += colored(e[-1], "bred")
        else:
            new += colored(e[-1], 'green')
            old += colored(e[-1], 'red')
    return "@expect({})\n@actual({})".format(old, new)

# TODO: look into using something better https://github.com/rec/safer
# https://stackoverflow.com/questions/2333872/atomic-writing-to-file-with-python/2333979#2333979
def atomic_write(filepath, code):
    """Writes the code to the file atomically"""
    with open("tmpfile.py", 'w') as f:
        f.write(code)
        f.flush()
        os.fsync(f.fileno())
    os.rename("tmpfile.py", filepath)

class MalformedExpect(Exception):
    docs = """
    The correct way to form an @expect test expression is
    @expect("Expected String")
    def some_function_name():
        return some_code_to_test()

    or if you want to promote a function

    @promote
    @expect("Expected String")
    def some_function_name():
        return some_code_to_test()

    Note that no other decorators are allowed
    and @promote must always come before @expect
    """

    def __init__(self, message, *args, **kwargs):
        message = "{}\n{}".format(message, self.docs)
        super().__init__(message, *args, **kwargs)

class _ExpectResults():
    """
    Helper Class for checking the promote is correctly placed
    Does so by giving us makeshift typing
    This class is returned (with data) by @expect, if @promote is passed any
    type besides this, it will fail
    """

    def __init__(self, lineno, result):
        self.lineno = lineno
        self.result = result

def get_node_firstline(node: ast.FunctionDef) -> int:
    if len(node.decorator_list) > 0:
        return node.decorator_list[0].lineno
    return node.lineno

class Promote(ast.NodeTransformer):
    """
    Walk the ast looking for expect nodes that are in need of promotion,
    note: this returns a copy of the ast with transformations, but does not write anything back
    """

    def __init__(self, target, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target = target
        self.updated_nodes = []

    def visit_FunctionDef(self, node):
        # target lineno grabbed in the @expect function, this allows us to find the right node
        if isinstance(node, ast.FunctionDef) and get_node_firstline(node) == self.target.lineno:
            firstline = get_node_firstline(node)
            for dec in node.decorator_list:
                if isinstance(dec, ast.Name):
                    if dec.id != 'promote':
                        raise MalformedExpect("@expect is not compatible with other decorators")
                elif isinstance(dec, ast.Call):
                    if dec.func.id == 'expect':
                        # once promoted we only want one argument which is a string with
                        # our expected output
                        dec.args = [ast.Str(self.target.result)]
                        # Removes the promote keyword, or does nothing (if there weren't any keywords)
                        dec.keywords = []
                    else:
                        raise MalformedExpect("@expect is not compatible with other decorators")

            # Clear @promote if it exists
            # This line is needed to walk children, aka invoke self.visit_Name
            self.generic_visit(node)

            self.updated_nodes.append((firstline, node))
        return node

    def visit_Name(self, node):
        # removes the @promote associated with the target node (if there is one)
        if node.id == 'promote' and node.lineno == self.target.lineno:
            return None
        return node

def node_bounds(node: ast.FunctionDef):
    """
    Finds the bounds of a function be looking at the first line,
    as well as the line the return statement is on
    """
    for b in node.body:
        if isinstance(b, ast.Return):
            # slice bounds don't include the last element, this means that we need to add +1 to make
            # it inclusive, this +1 cancels out the -1 from the zero start
            return slice(get_node_firstline(node) - 1, b.value.lineno)

def leading_whitespace(s):
    """Helper to that grabs the leading whitespace of a line"""
    return s.split(s.lstrip()[0])[0]

def update_code_from_ast(lines, root, details):
    """
    Performs the promotion transformation directly on the ast, but only
    writes back relevant sections to the code, this means that only the sections
    of code that are explicitely allowed to be manipulated (any function with an @expect decorator)
    will be updated. This can change the formatting 
    """
    promoter = Promote(details)
    promoter.visit(root)
    for firstline, n in promoter.updated_nodes:
        bounds = node_bounds(n)
        # First line is guarenteed to contain a decorator at the correct indent level
        indent = leading_whitespace(lines[bounds.start])
        
        # This removes a @promote if it exists,
        # otherwise it removes @expect (which is quickly replaced)
        # note the -1 becuse lineno's (including firstline) are 1-indexed
        lines[firstline - 1] = ''

        def add_indent(l):
            return indent + l

        lines[bounds] = map(add_indent, ast.unparse(n).splitlines())

    return lines

def _promote(details):
    if not isinstance(details, _ExpectResults):
        raise MalformedExpect("Promote must be called before @expect")

    # 0 is the current frame (_promote)
    # 1 is the caller (expect) or (promote)
    # 2 is the user
    filename = inspect.stack()[2].filename
    filepath = os.path.realpath(filename)

    with open(filepath, 'r') as f:
        code_file = f.read()
        lines = code_file.splitlines()

    with open(os.path.realpath("{}.expect.bak".format(filename)), 'w') as f:
        f.write(code_file)

    # Get an ast representation of the code file
    root = ast.parse(code_file)

    # perform operations on the ast and write to line representation of the source
    lines = update_code_from_ast(lines, root, details)

    atomic_write(filepath, '\n'.join(lines))
    # print(filepath)
    # print('\n'.join(lines))

    print("Promoted succesfully!")

    return details

