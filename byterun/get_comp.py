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
    starting_value = 11
    find_str = 11
    split_str = 12


class GetComparisons(VirtualMachine):

    def functions(self):
        self.functions = [
            "find of str",
            "split of str",
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

            # we also have to consider, that a character is looked for, which is not in the arg, e.g. "'?' in arg"

        return VirtualMachine.byte_COMPARE_OP(self, opnum)


    def line_already_seen(self):
        line = (self.frame.f_lineno, self.frame.f_lasti)
        if line not in self.lines_seen:
            self.new_comp_seen = True
            self.lines_seen.add(line)



    def function_watched(self, function_string):
        counter = 0
        for f in self.functions:
            if f in function_string:
                return counter
            counter += 1
        return -1


    def byte_CALL_FUNCTION(self, arg):
        self.line_already_seen()
        args = self.topn(arg + 1)
        func_watched = self.function_watched(str(args[0]))
        if func_watched != -1:
            self.trace.append((Functions(Functions.starting_value.value + func_watched), [str(self.load_from)] + args))

        return VirtualMachine.byte_CALL_FUNCTION(self, arg)


    def byte_LOAD_ATTR(self, attr):
        self.line_already_seen()
        obj = self.top()
        self.load_from = obj

        return VirtualMachine.byte_LOAD_ATTR(self, attr)


    ######### Trace report #############
    def extract_predicates(self):
        remaining_input = sys.argv[1]
        comparisons = list()

        for t in self.trace:
            if t[0] == Operator.EQ or t[0] == Operator.NE:
                remaining_input = self.eq_comp(t, remaining_input, comparisons)
            elif t[0] == Operator.IN or t[0] == Operator.NOT_IN:
                remaining_input = self.in_comp(t, remaining_input, comparisons)

            # if len(remaining_input) > length_next_inputs:
            #     length_next_inputs = len(next_inputs)
            #     comparisons.append(t)

        return comparisons

    # adds a new comparison to the list of comparisons
    # key is the value from the input which was compared
    # comparisons is the list of comparisons made throughout the exec
    # op is the used operator
    # comp_with is the value with which the input was compared
    # value is the outcome of the comparison
    def add_comparison(self, key, comparisons, op, comp_with, value):
        if comparisons and comparisons[- 1][0] == key:
            comparisons[- 1][1].append((op.name, comp_with, value))
        else:
            comparisons.append((key, [(op.name, comp_with, value)]))



    def eq_comp(self, trace_line, remaining_input, comparisons):
        compare = trace_line[1]
        # verify that both operands are string
        if type(compare[0]) is not str or type(compare[1]) is not str:
            return remaining_input
        cmp0_str = str(compare[0])
        cmp1_str = str(compare[1])
        find0 = remaining_input.find(cmp0_str)
        find1 = remaining_input.find(cmp1_str)
        # if both sides of the equality are not part of the remaining string, the comparison does likely not have to
        # do something with our input
        if find0 == -1 and find1 == -1:
            return remaining_input
        pos = min(i for i in [find0, find1] if i >= 0)
        remaining_input = remaining_input[pos:]
        operator_eq = trace_line[0] == Operator.EQ
        if compare[0] == "" or compare[1] == "":
            return remaining_input
        if compare[0] == compare[1]:
            self.add_comparison(compare[0], comparisons, Operator.EQ, compare[0], True if operator_eq else False)
        else:
            if remaining_input.startswith(compare[0]):
                self.add_comparison(compare[0], comparisons, Operator.EQ, compare[1], False if operator_eq else True)
            else:
                self.add_comparison(compare[1], comparisons, Operator.EQ, compare[0], False if operator_eq else True)
        return remaining_input


    # apply the subsititution for the in statement
    def in_comp(self, trace_line, remaining_input, comparisons):
        compare = trace_line[1]
        # verify that both operands are string
        if type(compare[0]) is not str:
            return remaining_input
        cmp0_str = str(compare[0])
        if cmp0_str == "":
            return remaining_input
        find0 = remaining_input.find(cmp0_str)
        # if the lhs is not part of the remaining string, the comparison does likely not have to
        # do something with our input
        if find0 != -1:
            remaining_input = remaining_input[find0:]
            if trace_line[0] == Operator.IN:
                self.add_comparison(compare[0], comparisons, Operator.IN, str(compare[1]), compare[0] in compare[1])
            else:
                self.add_comparison(compare[0], comparisons, Operator.NOT_IN, compare[1], compare[0] not in compare[1])
            return remaining_input
        else:
            # it might be that something is searched in the input string, we ignore this for the moment
            return remaining_input

