"""A pure-Python Python bytecode interpreter."""
# Based on:
# pyvm2 by Paul Swartz (z3p), from http://www.twistedmatrix.com/users/z3p/

from __future__ import print_function, division

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

    def byte_COMPARE_OP(self, opnum):
        print('compare_op')
        pyvm2.VirtualMachine.byte_COMPARE_OP(self, opnum)
        # x, y = self.popn(2)
        # self.push(self.COMPARE_OPERATORS[opnum](x, y))