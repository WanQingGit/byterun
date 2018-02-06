"""A pure-Python Python bytecode interpreter."""
# Based on:
# pyvm2 by Paul Swartz (z3p), from http://www.twistedmatrix.com/users/z3p/

from __future__ import print_function, division
import sys

from .pyvm2 import VirtualMachine
from enum import Enum
from random import shuffle
import string

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


class GetComparisons(VirtualMachine):

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
        # stores the lines seen throughout all executions, is not cleared after one execution
        self.lines_seen = set()
        # TODO it might also be worth storing the new comps and exploring inputs based on those new comps first
        self.new_comp_seen = False

        #some constants that may be configured in the future
        self.expand_in = 2 # sets how many values are taken from the right hand side at most when a call to in or not in happens

    def clean(self, new_args):
        self.args = new_args
        self.trace = list()
        self.load_from = None
        self.frame = None
        self.return_value = None
        self.last_exception = None
        self.frames = []

        self.new_comp_seen = False


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
        self.line_already_seen()
        operands = self.topn(2)
        for arg in self.args:
            if ((str(operands[0]) != '') and str(operands[0]) in arg) \
                    or ((str(operands[1]) != '') and str(operands[1]) in arg):
                self.trace.append((Operator(opnum), operands))
                break

        return VirtualMachine.byte_COMPARE_OP(self, opnum)


    def line_already_seen(self):
        line = (self.frame.f_lineno, self.frame.f_lasti)
        if line not in self.lines_seen:
            self.new_comp_seen = True
            self.lines_seen.add(line)



    def function_watched(self, function_string):
        for f in self.functions:
            if f in function_string:
                return True
        return False


    def byte_CALL_FUNCTION(self, arg):
        self.line_already_seen()
        args = self.topn(arg + 1)
        if self.function_watched(str(args[0])):
            self.trace.append((Functions(11), [str(self.load_from)] + args))

        return VirtualMachine.byte_CALL_FUNCTION(self, arg)


    def byte_LOAD_ATTR(self, attr):
        self.line_already_seen()
        obj = self.top()
        self.load_from = obj

        return VirtualMachine.byte_LOAD_ATTR(self, attr)


    #################    Next input generation     ############################

    # lets first use a simple approach where strong equality is used for replacement in the first input
    # also we use parts of the rhs of the in statement as substitution
    def get_next_inputs(self, pos):
        next_inputs = list()
        current = self.args[0]
        for t in self.trace:
            if t[0] == Operator.EQ or t[0] == Operator.NE:
                next_inputs += self.eq_next_inputs(t, current, pos)
            elif t[0] == Operator.IN or t[0] == Operator.NOT_IN:
                next_inputs += self.in_next_inputs(t, current, pos)

        # add some letter as substitution as well
        next_inputs += [(0, pos, "B")]
        return next_inputs


    # apply the substitution for equality comparisons
    # TODO find all occ. in near future
    def eq_next_inputs(self, trace_line, current, pos):
        compare = trace_line[1]
        # verify that both operands are string
        if type(compare[0]) is not str or type(compare[1]) is not str:
            return []
        next_inputs = list()
        cmp0_str = str(compare[0])
        cmp1_str = str(compare[1])
        if compare[0] == compare[1]:
            return []

        # self.changed.add(str(trace_line))
        find0 = current.find(cmp0_str)
        find1 = current.find(cmp1_str)
        # check if actually the char at the pos we are currently checking was checked in the comparison
        if find0 == pos:
            next_inputs.append((0, pos, cmp1_str))
        elif find1 == pos:
            next_inputs.append((0, pos, cmp0_str))

        return next_inputs


    # apply the subsititution for the in statement
    def in_next_inputs(self, trace_line, current, pos):
        compare = trace_line[1]
        # the lhs must be a string
        if type(compare[0]) is not str:
            return []
        next_inputs = list()
        cmp0_str = str(compare[0])
        counter = 0
        # take some samples from the collection in is applied on
        for cmp in compare[1]:
            # only take a subset of the rhs (the collection in is applied on)
            if counter >= self.expand_in:
                break
            counter += 1
            cmp1_str = str(cmp)
            if compare[0] == cmp:
                continue
            # self.changed.add(str(trace_line))
            find0 = current.find(cmp0_str)
            if find0 == pos:
                next_inputs.append((1, pos, cmp1_str))

        return next_inputs
