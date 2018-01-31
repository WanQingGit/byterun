"""A pure-Python Python bytecode interpreter."""
# Based on:
# pyvm2 by Paul Swartz (z3p), from http://www.twistedmatrix.com/users/z3p/

from __future__ import print_function, division
import sys

import pyvm2
from enum import Enum

class Operator(Enum):
    LT = 0
    LE = 1
    EQ = 2
    NE = 3
    GT = 4
    GE = 5
    IN = 6
    NOT_IN = 7
    IS = 8
    IS_NOT = 9
    ISSUBCLASS = 10

class Functions(Enum):
    find_str = 11


class GetComparisons(pyvm2.VirtualMachine):

    def functions(self):
        self.functions = [
            "find of str",
        ]


    def __init__(self):
        # The call stack of frames.
        self.frames = []
        # The current frame.
        self.frame = None
        self.return_value = None
        self.last_exception = None
        self.args = sys.argv[1:]
        self.load_from = None # indicates from which object the last function was loaded
        self.functions()

        self.trace = list()
        self.changed = set()

    def clean(self, new_args):
        self.args = new_args
        self.trace = list()
        self.load_from = None
        self.frame = None
        self.return_value = None
        self.last_exception = None
        self.frames = []


    def topn(self, n):
        """Get a number of values from the value stack.

        A list of `n` values is returned, the deepest value first.

        """
        if n:
            ret = self.frame.stack[-n:]
            return ret
        else:
            return []


    def byte_COMPARE_OP(self, opnum):
        operands = self.topn(2)
        for arg in self.args:
            if ((str(operands[0]) != '') and str(operands[0]) in arg) \
                    or ((str(operands[1]) != '') and str(operands[1]) in arg):
                self.trace.append((Operator(opnum), operands))
                break

        return pyvm2.VirtualMachine.byte_COMPARE_OP(self, opnum)


    def function_watched(self, function_string):
        for f in self.functions:
            if f in function_string:
                return True
        return False


    def byte_CALL_FUNCTION(self, arg):
        args = self.topn(arg + 1)
        if self.function_watched(str(args[0])):
            self.trace.append((Functions(11), [str(self.load_from)] + args))

        return pyvm2.VirtualMachine.byte_CALL_FUNCTION(self, arg)


    def byte_LOAD_ATTR(self, attr):
        obj = self.top()
        self.load_from = obj

        return pyvm2.VirtualMachine.byte_LOAD_ATTR(self, attr)


    #################    Next input generation     ############################

    # lets first use a simple approach where strong equality is replaced in the first input
    def get_next_inputs(self):
        next_inputs = list()
        current = self.args[0]
        for t in self.trace:
            # a currently likely unsound method to avoid changes of the same operator again
            if str(t) in self.changed:
                continue
            if t[0] == Operator.EQ:
                next_inputs += self.eq_next_inputs(t, current)
            elif t[0] == Operator.IN:
                next_inputs += self.in_next_inputs(t, current)
                # if the comparison was successful we do not need to change anything
                # TODO: This does not hold in general, in future we might need to consider succ. comp. as leading into an error

        return next_inputs


    def eq_next_inputs(self, trace_line, current):
        compare = trace_line[1]
        next_inputs = list()
        cmp0_str = str(compare[0])
        cmp1_str = str(compare[1])
        if compare[0] == compare[1]:
            return []
        self.changed.add(str(trace_line))
        if str(compare[0]) in current:
            next_inputs.append(current.replace(cmp0_str, cmp1_str))
        else:
            next_inputs.append(current.replace(cmp1_str, cmp0_str))

        return next_inputs

    def in_next_inputs(self, trace_line, current):
        compare = trace_line[1]
        next_inputs = list()
        cmp0_str = str(compare[0])
        for cmp in compare[1]:
            cmp1_str = str(cmp)
            if compare[0] == cmp:
                return []
            self.changed.add(str(trace_line))
            if str(compare[0]) in current:
                next_inputs.append(current.replace(cmp0_str, cmp1_str))

        return next_inputs
