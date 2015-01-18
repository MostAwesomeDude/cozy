
from predicates import *

class Plan(object):
    def toPredicate(self):
        pass
    def isSortedBy(self, fieldName):
        pass
    def isTrivial(self):
        return False
    def wellFormed(self):
        pass
    def size(self):
        pass

class All(Plan):
    def toPredicate(self):
        return Bool(True)
    def isSortedBy(self, fieldName):
        return True
    def isTrivial(self):
        return True
    def wellFormed(self):
        return True
    def size(self):
        return 1
    def __str__(self):
        return "All"

class Empty(Plan):
    def toPredicate(self):
        return Bool(False)
    def isSortedBy(self, fieldName):
        return True
    def isTrivial(self):
        return True
    def wellFormed(self):
        return True
    def size(self):
        return 1
    def __str__(self):
        return "None"

class HashLookup(Plan):
    def __init__(self, plan, fieldName, varName):
        self.plan = plan
        self.fieldName = fieldName
        self.varName = varName
    def toPredicate(self):
        return And(self.plan.toPredicate(), Compare(Var(self.fieldName), Eq, Var(self.varName)))
    def isSortedBy(self, fieldName):
        return self.plan.isSortedBy(fieldName)
    def wellFormed(self):
        return (isinstance(self.plan, HashLookup) or isinstance(self.plan, All)) and self.plan.wellFormed()
    def size(self):
        return 1 + self.plan.size()
    def __str__(self):
        return "HashLookup({}, {} == {})".format(self.plan, self.fieldName, self.varName)

class BinarySearch(Plan):
    def __init__(self, plan, fieldName, op, varName):
        self.plan = plan
        self.fieldName = fieldName
        self.op = op
        self.varName = varName
    def toPredicate(self):
        return And(self.plan.toPredicate(), Compare(Var(self.fieldName), self.op, Var(self.varName)))
    def isSortedBy(self, fieldName):
        return fieldName == self.fieldName
    def wellFormed(self):
        return self.plan.wellFormed() and self.plan.isSortedBy(self.fieldName)
    def size(self):
        return 1 + self.plan.size()
    def __str__(self):
        return "BinarySearch({}, {} {} {})".format(self.plan, self.fieldName, opToStr(self.op), self.varName)

class Filter(Plan):
    def __init__(self, plan, predicate):
        self.plan = plan
        self.predicate = predicate
    def toPredicate(self):
        return And(self.plan.toPredicate(), self.predicate)
    def isSortedBy(self, fieldName):
        return False
    def wellFormed(self):
        return self.plan.wellFormed()
    def size(self):
        return 1 + self.plan.size() + self.predicate.size()
    def __str__(self):
        return "Filter({}, {})".format(self.plan, self.predicate)

class Intersect(Plan):
    def __init__(self, plan1, plan2):
        self.plan1 = plan1
        self.plan2 = plan2
    def toPredicate(self):
        return And(self.plan1.toPredicate(), self.plan2.toPredicate())
    def isSortedBy(self, fieldName):
        return False
    def wellFormed(self):
        return self.plan1.wellFormed() and self.plan2.wellFormed()
    def size(self):
        return 1 + self.plan1.size() + self.plan2.size()
    def __str__(self):
        return "Intersect({}, {})".format(self.plan1, self.plan2)

class Union(Plan):
    def __init__(self, plan1, plan2):
        self.plan1 = plan1
        self.plan2 = plan2
    def toPredicate(self):
        return Or(self.plan1.toPredicate(), self.plan2.toPredicate())
    def isSortedBy(self, fieldName):
        return False
    def wellFormed(self):
        return self.plan1.wellFormed() and self.plan2.wellFormed()
    def size(self):
        return 1 + self.plan1.size() + self.plan2.size()
    def __str__(self):
        return "Union({}, {})".format(self.plan1, self.plan2)