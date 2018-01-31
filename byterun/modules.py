import os.path
import types
NoSource = Exception

def find_module_absolute(name, searchpath, isfile):
    # search path should really be appeneded to a list of paths
    # that the interpreter knows about. For now, we only look in '.'
    myname = name if not searchpath else "%s/%s" % (searchpath, name)
    if isfile:
        fname = "%s.py" % myname
        return os.path.abspath(fname) if os.path.isfile(fname) else None
    else:
        return os.path.abspath(myname) if os.path.isdir(myname) else None

def find_module_relative(name, searchpath): return None

def find_module(name, searchpath, level, isfile=True):
    """
    `level` specifies whether to use absolute and/or relative.
        The default is -1 which is both absolute and relative
        0 means only absolute and positive values indicate number
        parent directories to search relative to the directory of module
        calling `__import__`
    """
    assert level <= 0 # we dont implement relative yet
    if level == 0:
        return find_module_absolute(name, searchpath, isfile)
    elif level > 0:
        return find_module_relative(name, searchpath, isfile)
    else:
        res = find_module_absolute(name, searchpath, isfile)
        return find_module_relative(name, searchpath, isfile) if not res \
                else res

def import_python_dir(name, search, glo, loc, level):
    mymod = types.ModuleType(name)
    path = find_module(name, search, level, isfile=False)
    if path == None: raise NoSource("<%s> not a directory" % path)
    mymod.__file__ = path
    mymod.__path__ = path
    mymod.__builtins__ = glo['__builtins__']
    return mymod


def import_python_module(modulename, glo, loc, fromlist, level, search=None):
    """Import a python module.
    `modulename` is the name of the module, possibly a dot-separated name.
    `fromlist` is the list of things to imported from the module.
    """
    try:
        if '.' not in modulename:
            pkg, name = None, modulename
            path = find_module(name, search, level, isfile=True)
            mymod = types.ModuleType(name)
            mymod.__file__ = path
            mymod.__builtins__ = glo['__builtins__']
            # Open the source file.
            try:
                with open(path, "rU") as source_file:
                    source = source_file.read()
                    if not source or source[-1] != '\n': source += '\n'
                    code = compile(source, path, "exec")
                    # Execute the source file.
                    vm = VirtualMachine()
                    vm.run_code(code, f_globals=mymod.__dict__, f_locals=mymod.__dict__)
                    # strip it with fromlist
                    # get the defined module
                    return mymod
            except IOError:
                raise NoSource("module does not live in a file: %r" % modulename)
        else:
            pkgn, name = modulename.rsplit('.', 1)
            pkg = import_python_dir(pkgn, search, glo, loc, level)
            mod = import_python_module(name, glo, loc, fromlist, level, pkg.__path__)
            # mod is an attribute of pkg
            setattr(pkg, mod.__name__, mod)
            return pkg
    except NoSource as e:
        return __import__(modulename, glo, loc, fromlist, level)

