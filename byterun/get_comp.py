"""A pure-Python Python bytecode interpreter."""
# Based on:
# pyvm2 by Paul Swartz (z3p), from http://www.twistedmatrix.com/users/z3p/

from __future__ import print_function, division
import sys

import pyvm2


class VirtualMachineError(Exception):
    """For raising errors in the operation of the VM."""
    pass


class GetComparisons(pyvm2.VirtualMachine):


    def __init__(self):
        # The call stack of frames.
        self.frames = []
        # The current frame.
        self.frame = None
        self.return_value = None
        self.last_exception = None
        self.args = sys.argv[1:]


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
        # for arg in self.args:
            
        print(str(self.COMPARE_OPERATORS[opnum]), self.topn(2))
        pyvm2.VirtualMachine.byte_COMPARE_OP(self, opnum)
        # x, y = self.popn(2)
        # self.push(self.COMPARE_OPERATORS[opnum](x, y))