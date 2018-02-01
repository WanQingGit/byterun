"""Execute files of Python code."""

import imp
import os
import sys
import tokenize
import queue
import string

# from pyvm2 import VirtualMachine
from get_comp import GetComparisons

# This code is ripped off from coverage.py.  Define things it expects.
try:
    open_source = tokenize.open     # pylint: disable=E1101
except:
    def open_source(fname):
        """Open a source file the best way."""
        return open(fname, "rU")

NoSource = Exception


def exec_code_object(code, env):
    # vm = VirtualMachine()
    vm = GetComparisons()
    # TODO: a fast hack to get the loop running, some sophisticated run loop will be added later
    last_input = "qiaup98bsdf"
    next_input = ""
    expansion_list = queue.PriorityQueue()
    explored = set()
    expansion_counter = 0
    with open("outputs.txt","w") as outputs:
        for i in range(0,3000000):
            expansion_counter += 1
            print("#############")
            # we might run into exceptions since we produce invalid inputs
            # we catch those exceptions and produce a new input based on the gained knowledge through the
            # execution
            print(repr(next_input))
            try:
                vm.run_code(code, f_globals=env)
            except Exception:
                pass
            # for t in vm.trace:
            #     print(t)
            next_inputs = vm.get_next_inputs()
            for next_input in next_inputs:
                next_input = ''.join(filter(lambda x: x in string.printable, next_input))
                # do not reevaluate inputs that we have already seen
                if next_input not in explored:
                    new_node = (calc_heuristic(expansion_counter, vm, next_input), last_input, next_input)
                    expansion_list.put(new_node)
            if expansion_list.empty():
                return
            (_, last_input, next_input) = expansion_list.get_nowait()
            # print(next_inputs)
            # print(expansion_list)
            outputs.write(next_input + "\n")
            explored.add(next_input)
            vm.clean([next_input])
            sys.argv[1] = next_input


def calc_heuristic(expansion_counter, vm, input_string):
    result = sys.maxsize // 2

    # earlier expansions should be prioritized
    # inputs that are created based on later comparisons might be deeper down in the program and should therefore
    # be preferred
    result += expansion_counter
    # longer traces indicate more execution, so likely the input was more correct
    # result -= len(vm.trace)
    # inputs that do not produce an exception might be correct, so we prefer it by some constant
    # if vm.last_exception is None:
    #     result -= 20
    # shorter inputs are preferred at the moment
    # result += len(input_string)

    # a higher levensthein distance is better
    # result -= len(set("qiaup98bsdf") & set(input_string)) * 4

    # prefer inputs with many control characters (non-alpha nums)
    # result -= sum((not c.isalnum() and c not in {"\n", "\t", "\r", "\f"}) for c in input_string)

    return result



# TODO: we need a more sophisicated restart function in future
def restart():
    return "qiaup98bsdf"


# from coverage.py:

try:
    # In Py 2.x, the builtins were in __builtin__
    BUILTINS = sys.modules['__builtin__']
except KeyError:
    # In Py 3.x, they're in builtins
    BUILTINS = sys.modules['builtins']


def rsplit1(s, sep):
    """The same as s.rsplit(sep, 1), but works in 2.3"""
    parts = s.split(sep)
    return sep.join(parts[:-1]), parts[-1]


def run_python_module(modulename, args):
    """Run a python module, as though with ``python -m name args...``.

    `modulename` is the name of the module, possibly a dot-separated name.
    `args` is the argument array to present as sys.argv, including the first
    element naming the module being executed.

    """
    openfile = None
    glo, loc = globals(), locals()
    try:
        try:
            # Search for the module - inside its parent package, if any - using
            # standard import mechanics.
            if '.' in modulename:
                packagename, name = rsplit1(modulename, '.')
                package = __import__(packagename, glo, loc, ['__path__'])
                searchpath = package.__path__
            else:
                packagename, name = None, modulename
                searchpath = None  # "top-level search" in imp.find_module()
            openfile, pathname, _ = imp.find_module(name, searchpath)

            # Complain if this is a magic non-file module.
            if openfile is None and pathname is None:
                raise NoSource(
                    "module does not live in a file: %r" % modulename
                    )

            # If `modulename` is actually a package, not a mere module, then we
            # pretend to be Python 2.7 and try running its __main__.py script.
            if openfile is None:
                packagename = modulename
                name = '__main__'
                package = __import__(packagename, glo, loc, ['__path__'])
                searchpath = package.__path__
                openfile, pathname, _ = imp.find_module(name, searchpath)
        except ImportError:
            _, err, _ = sys.exc_info()
            raise NoSource(str(err))
    finally:
        if openfile:
            openfile.close()

    # Finally, hand the file off to run_python_file for execution.
    args[0] = pathname
    run_python_file(pathname, args, package=packagename)


def run_python_file(filename, args, package=None):
    """Run a python file as if it were the main program on the command line.

    `filename` is the path to the file to execute, it need not be a .py file.
    `args` is the argument array to present as sys.argv, including the first
    element naming the file being executed.  `package` is the name of the
    enclosing package, if any.

    """
    # Create a module to serve as __main__
    old_main_mod = sys.modules['__main__']
    main_mod = imp.new_module('__main__')
    sys.modules['__main__'] = main_mod
    main_mod.__file__ = filename
    if package:
        main_mod.__package__ = package
    main_mod.__builtins__ = BUILTINS

    # Set sys.argv and the first path element properly.
    old_argv = sys.argv
    old_path0 = sys.path[0]
    sys.argv = args
    if package:
        sys.path[0] = ''
    else:
        sys.path[0] = os.path.abspath(os.path.dirname(filename))

    try:
        # Open the source file.
        try:
            source_file = open_source(filename)
        except IOError:
            raise NoSource("No file to run: %r" % filename)

        try:
            source = source_file.read()
        finally:
            source_file.close()

        # We have the source.  `compile` still needs the last line to be clean,
        # so make sure it is, then compile a code object from it.
        if not source or source[-1] != '\n':
            source += '\n'
        code = compile(source, filename, "exec")

        # Execute the source file.
        exec_code_object(code, main_mod.__dict__)
    finally:
        # Restore the old __main__
        sys.modules['__main__'] = old_main_mod

        # Restore the old argv and path
        sys.argv = old_argv
        sys.path[0] = old_path0
