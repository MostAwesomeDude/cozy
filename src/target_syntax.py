"""
While the syntax module declares the core _input_ language, this module declares
additional syntax extensions that can appear in the _target_ language: the
primitives the tool can output during synthesis.
"""

from syntax import *
from common import declare_case, typechecked

# Lambdas
EApp = declare_case(Exp, "EApp", ["f", "arg"])
class ELambda(Exp):
    @typechecked
    def __init__(self, arg : EVar, body : Exp):
        self.arg = arg
        self.body = body
    def apply_to(self, arg):
        from syntax_tools import subst
        return subst(self.body, { self.arg.id : arg })
    def children(self):
        return (self.arg, self.body)

# Bag transformations
EMap     = declare_case(Exp, "EMap", ["e", "f"])

# Maps
EMakeMap = declare_case(Exp, "EMakeMap", ["e", "key", "value"])
EMapGet  = declare_case(Exp, "EMapGet", ["map", "key"])
