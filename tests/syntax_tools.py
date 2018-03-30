import unittest

from cozy.common import OrderedSet
from cozy.target_syntax import *
from cozy.syntax_tools import *
from cozy.typecheck import retypecheck
from cozy.solver import valid
from cozy.evaluation import eval

class TestSyntaxTools(unittest.TestCase):

    def test_eall(self):
        assert eval(EAll(()), {})
        for l in range(5):
            print(pprint(EAll([EVar("v{}".format(i)).with_type(BOOL) for i in range(l)])))

    def test_enumerate_fragments_strange_binder_behavior(self):
        xs = EVar("xs").with_type(TBag(INT))
        x = EVar("x").with_type(INT)
        xs_eq_zero = EFilter(xs, ELambda(x, equal(x, ZERO)))
        e = EFilter(xs_eq_zero, ELambda(x,
            equal(
                EFilter(xs, ELambda(x, T)),
                EEmptyList().with_type(xs.type))))
        assert retypecheck(e)
        for ctx in enumerate_fragments(e):
            e = ctx.e
            a = ctx.facts
            if e == T:
                assert not valid(implies(EAll(a), equal(x, ZERO)), validate_model=True), "assumptions at {}: {}".format(pprint(e), "; ".join(pprint(aa) for aa in a))

    def test_enumerate_fragments_bound(self):
        b = EVar("b").with_type(BOOL)
        e = ELet(ZERO, mk_lambda(INT, lambda x: b))
        assert retypecheck(e)
        for ctx in enumerate_fragments(e):
            x = ctx.e
            bound = ctx.bound_vars
            if x == b:
                assert bound == { e.f.arg }, "got {}".format(bound)
            elif x == ZERO:
                assert bound == set(), "got {}".format(bound)

    def test_enumerate_fragments_estatevar(self):
        b = EVar("b").with_type(BOOL)
        e = ELet(ZERO, mk_lambda(INT, lambda x: EStateVar(b)))
        assert retypecheck(e)
        for ctx in enumerate_fragments(e):
            if ctx.e == b:
                bound = ctx.bound_vars
                assert not bound, "EStateVar should reset bound variables, but got {}".format(bound)

    def test_enumerate_fragments_regression_1(self):
        e = EFilter(ESingleton(EVar('e').with_type(THandle('Entry', TRecord((('key', TNative('uint64_t')), ('pixmap', TNative('QPixmap *')), ('indexData', TNative('QByteArray')), ('memSize', TInt()), ('diskSize', TInt()), ('st', TEnum(('Disk', 'Loading', 'DiskAndMemory', 'MemoryOnly', 'Saving', 'NetworkPending', 'IndexPending', 'Invalid'))), ('inUse', TBool())))))).with_type(TBag(THandle('Entry', TRecord((('key', TNative('uint64_t')), ('pixmap', TNative('QPixmap *')), ('indexData', TNative('QByteArray')), ('memSize', TInt()), ('diskSize', TInt()), ('st', TEnum(('Disk', 'Loading', 'DiskAndMemory', 'MemoryOnly', 'Saving', 'NetworkPending', 'IndexPending', 'Invalid'))), ('inUse', TBool())))))), ELambda(EVar('_var380').with_type(THandle('Entry', TRecord((('key', TNative('uint64_t')), ('pixmap', TNative('QPixmap *')), ('indexData', TNative('QByteArray')), ('memSize', TInt()), ('diskSize', TInt()), ('st', TEnum(('Disk', 'Loading', 'DiskAndMemory', 'MemoryOnly', 'Saving', 'NetworkPending', 'IndexPending', 'Invalid'))), ('inUse', TBool()))))), EBinOp(EVar('e').with_type(THandle('Entry', TRecord((('key', TNative('uint64_t')), ('pixmap', TNative('QPixmap *')), ('indexData', TNative('QByteArray')), ('memSize', TInt()), ('diskSize', TInt()), ('st', TEnum(('Disk', 'Loading', 'DiskAndMemory', 'MemoryOnly', 'Saving', 'NetworkPending', 'IndexPending', 'Invalid'))), ('inUse', TBool()))))), 'in', EStateVar(EVar('entries').with_type(TBag(THandle('Entry', TRecord((('key', TNative('uint64_t')), ('pixmap', TNative('QPixmap *')), ('indexData', TNative('QByteArray')), ('memSize', TInt()), ('diskSize', TInt()), ('st', TEnum(('Disk', 'Loading', 'DiskAndMemory', 'MemoryOnly', 'Saving', 'NetworkPending', 'IndexPending', 'Invalid'))), ('inUse', TBool()))))))).with_type(TBag(THandle('Entry', TRecord((('key', TNative('uint64_t')), ('pixmap', TNative('QPixmap *')), ('indexData', TNative('QByteArray')), ('memSize', TInt()), ('diskSize', TInt()), ('st', TEnum(('Disk', 'Loading', 'DiskAndMemory', 'MemoryOnly', 'Saving', 'NetworkPending', 'IndexPending', 'Invalid'))), ('inUse', TBool()))))))).with_type(TBool()))).with_type(TBag(THandle('Entry', TRecord((('key', TNative('uint64_t')), ('pixmap', TNative('QPixmap *')), ('indexData', TNative('QByteArray')), ('memSize', TInt()), ('diskSize', TInt()), ('st', TEnum(('Disk', 'Loading', 'DiskAndMemory', 'MemoryOnly', 'Saving', 'NetworkPending', 'IndexPending', 'Invalid'))), ('inUse', TBool()))))))
        for _ in enumerate_fragments(e):
            pass

    def _do_cse_check(self, e):
        for x in sorted(set(all_exps(e)), key=Exp.size):
            if isinstance(x, ELambda):
                continue
            print("checking {}...".format(pprint(x)))
            y = cse(x)
            if not valid(EBinOp(x, "===", y).with_type(BOOL)):
                print("Bad behavior!")
                print(pprint(x))
                print(pprint(y))
                return False
        return True

    def test_cse(self):
        x = EVar("x").with_type(INT)
        a = EBinOp(x, "+", ONE).with_type(INT)
        e = EBinOp(a, "+", a).with_type(INT)
        e = EBinOp(e, "+", ELet(ONE, ELambda(x, EBinOp(x, "+", x).with_type(INT))).with_type(INT)).with_type(INT)
        assert self._do_cse_check(e)

    def __test_cse_2(self):
        op = Op('addElement', [('x', TInt())], [], SSeq(SSeq(SSeq(SDecl('_name5771', ECond(EBinOp(EBinOp(EBinOp(EUnaryOp('len', EVar('_var2027').with_type(TBag(TInt()))).with_type(TInt()), '+', EUnaryOp('len', EVar('_var2027').with_type(TBag(TInt()))).with_type(TInt())).with_type(TInt()), '<', ENum(5).with_type(TInt())).with_type(TBool()), 'or', EBinOp(EBinOp(EUnaryOp('len', EVar('_var2027').with_type(TBag(TInt()))).with_type(TInt()), '+', EUnaryOp('len', EVar('_var2027').with_type(TBag(TInt()))).with_type(TInt())).with_type(TInt()), '>', ENum(7).with_type(TInt())).with_type(TBool())).with_type(TBool()), EBinOp(EVar('_var2027').with_type(TBag(TInt())), '-', EBinOp(EVar('_var2027').with_type(TBag(TInt())), '+', ESingleton(EVar('x').with_type(TInt())).with_type(TBag(TInt()))).with_type(TBag(TInt()))).with_type(TBag(TInt())), EBinOp(EVar('_var2027').with_type(TBag(TInt())), '-', EVar('_var2027').with_type(TBag(TInt()))).with_type(TBag(TInt()))).with_type(TBag(TInt()))), SDecl('_name5772', ECond(EBinOp(EBinOp(EBinOp(EUnaryOp('len', EVar('_var2027').with_type(TBag(TInt()))).with_type(TInt()), '+', EUnaryOp('len', EVar('_var2027').with_type(TBag(TInt()))).with_type(TInt())).with_type(TInt()),'<', ENum(5).with_type(TInt())).with_type(TBool()), 'or', EBinOp(EBinOp(EUnaryOp('len', EVar('_var2027').with_type(TBag(TInt()))).with_type(TInt()), '+', EUnaryOp('len', EVar('_var2027').with_type(TBag(TInt()))).with_type(TInt())).with_type(TInt()), '>', ENum(7).with_type(TInt())).with_type(TBool())).with_type(TBool()), EBinOp(EBinOp(EVar('_var2027').with_type(TBag(TInt())), '+', ESingleton(EVar('x').with_type(TInt())).with_type(TBag(TInt()))).with_type(TBag(TInt())), '-', EVar('_var2027').with_type(TBag(TInt()))).with_type(TBag(TInt())), EBinOp(EVar('_var2027').with_type(TBag(TInt())), '-', EVar('_var2027').with_type(TBag(TInt()))).with_type(TBag(TInt()))).with_type(TBag(TInt())))), SAssign(EVar('_var507').with_type(TInt()), ECond(EBinOp(EBinOp(EBinOp(EUnaryOp('len', EEmptyList().with_type(TBag(TInt()))).with_type(TInt()), '+', EUnaryOp('len', EEmptyList().with_type(TBag(TInt()))).with_type(TInt())).with_type(TInt()), '<', ENum(5).with_type(TInt())).with_type(TBool()), 'or', EBinOp(ENum(5).with_type(TInt()), '>', ENum(7).with_type(TInt())).with_type(TBool())).with_type(TBool()), EBinOp(EUnaryOp('len', EVar('_var2027').with_type(TBag(TInt()))).with_type(TInt()), '+', ENum(1).with_type(TInt())).with_type(TInt()), EUnaryOp('len', EEmptyList().with_type(TBag(TInt()))).with_type(TInt())).with_type(TInt()))), SSeq(SForEach(EVar('_var2988').with_type(TInt()), EVar('_name5771').with_type(TBag(TInt())), SCall(EVar('_var2027').with_type(TBag(TInt())), 'remove', [EVar('_var2988').with_type(TInt())])), SForEach(EVar('_var2988').with_type(TInt()), EVar('_name5772').with_type(TBag(TInt())), SCall(EVar('_var2027').with_type(TBag(TInt())), 'add', [EVar('_var2988').with_type(TInt())])))), '')
        spec = Spec("foo", (), (), (), (), [op], "", "", "")

        assert retypecheck(op)

        print(pprint(spec))
        print(pprint(eliminate_common_subexpressions(spec)))
        assert False

    def test_cse_2_stm_if(self):
        """
        if (foo)
            x = y + 2
        else
            z = y + 2
        =>
        tmp = y + 2;
        if (foo)
            x = tmp
        else
            z = tmp
        """
        yp2 = EBinOp(EVar("y").with_type(INT), "+", ENum(2).with_type(INT))

        s = SIf(
                EVar("foo").with_type(BOOL),
                SAssign(EVar("x").with_type(INT), yp2),
                SAssign(EVar("z").with_type(INT), yp2),
        )

        assert retypecheck(s)

        print(pprint(s))
        s2 = eliminate_common_subexpressions_stm(s)
        print(pprint(s2))

        assert isinstance(s2, SSeq) and isinstance(s2.s1, SDecl)

    def test_cse_2_stm_seq_assign_kill_deep(self):
        """
        Seq(
            SAssign(q = y + 2),
            Seq(
                Seq(
                    Seq(
                        SNoOp,
                        SAssign(y = 5),
                        ),
                    SNoOp,
                ),
                Seq(
                    SAssign(x = y + 2),
                    SAssign(z = y + 2)
                    )
            )
        )
        """

        yp2 = EBinOp(EVar("y").with_type(INT), "+", ENum(2).with_type(INT))
        zp4 = EBinOp(EVar("z").with_type(INT), "+", ENum(4).with_type(INT))

        s = SSeq(
                SAssign(EVar("q").with_type(INT), yp2),
                SSeq(
                    SSeq(
                        SSeq(
                            SNoOp(),
                            SAssign(EVar("y").with_type(INT), ONE)
                        ),
                        SNoOp()
                    ),
                    SSeq(
                        SAssign(EVar("x").with_type(INT), yp2),
                        SAssign(EVar("z").with_type(INT), yp2)
                    )
                )
            )

        assert retypecheck(s)
        print(pprint(s))

        s2 = eliminate_common_subexpressions_stm(s)
        newForm = pprint(s2)
        print("========")
        print(newForm)

        assert newForm.count("y + 2") == 2

    def test_cse_2_stm_newscope(self):
        """
        x = y + 2

        for (y in [1,2]) {
            z = y + 2
        }

        q = y + 2

        The for-loop body scope should not get CSE'd. The outer two *should*.
        """

        yp2 = EBinOp(EVar("y").with_type(INT), "+", ENum(2).with_type(INT)).with_type(INT)

        s = seq((
            SAssign(EVar("x").with_type(INT), yp2),
            SForEach(EVar("y"), ESingleton(ONE),
                SAssign(EVar("z").with_type(INT), yp2),
                ),
            SAssign(EVar("q").with_type(INT), yp2),
        ))

        assert retypecheck(s)

        print(pprint(s))
        s2 = eliminate_common_subexpressions_stm(s)
        print(pprint(s2))
        print(s2)

        new_form = pprint(s2)

        assert new_form.count("y + 2") == 2


    def test_cse_regression1(self):
        e = EBinOp(EBinOp(EUnaryOp('unique', EVar('conns').with_type(TList(THandle('Connection', TRecord((('conn_state', TEnum(('READY', 'PROCESSING', 'CHECKED_OUT'))), ('conn_host', TNative('HostAndPort')), ('conn_iface', TNative('ConnectionPool::ConnectionInterface*')), ('conn_next_refresh', TNative('Date_t')), ('conn_returned', TNative('Date_t')), ('conn_dropped', TBool()))))))).with_type(TBool()), 'and', EBinOp(EUnaryOp('unique', EMap(EVar('conns').with_type(TList(THandle('Connection', TRecord((('conn_state', TEnum(('READY', 'PROCESSING', 'CHECKED_OUT'))), ('conn_host', TNative('HostAndPort')), ('conn_iface', TNative('ConnectionPool::ConnectionInterface*')), ('conn_next_refresh', TNative('Date_t')), ('conn_returned', TNative('Date_t')), ('conn_dropped', TBool())))))), ELambda(EVar('_var810294').with_type(THandle('Connection', TRecord((('conn_state', TEnum(('READY', 'PROCESSING', 'CHECKED_OUT'))), ('conn_host', TNative('HostAndPort')), ('conn_iface', TNative('ConnectionPool::ConnectionInterface*')), ('conn_next_refresh', TNative('Date_t')), ('conn_returned', TNative('Date_t')), ('conn_dropped', TBool()))))), EGetField(EGetField(EVar('_var810294').with_type(THandle('Connection', TRecord((('conn_state', TEnum(('READY', 'PROCESSING', 'CHECKED_OUT'))), ('conn_host', TNative('HostAndPort')), ('conn_iface', TNative('ConnectionPool::ConnectionInterface*')), ('conn_next_refresh', TNative('Date_t')), ('conn_returned', TNative('Date_t')), ('conn_dropped', TBool()))))), 'val').with_type(TRecord((('conn_state', TEnum(('READY', 'PROCESSING', 'CHECKED_OUT'))), ('conn_host', TNative('HostAndPort')), ('conn_iface', TNative('ConnectionPool::ConnectionInterface*')), ('conn_next_refresh', TNative('Date_t')), ('conn_returned', TNative('Date_t')), ('conn_dropped', TBool())))), 'conn_iface').with_type(TNative('ConnectionPool::ConnectionInterface*')))).with_type(TList(TNative('ConnectionPool::ConnectionInterface*')))).with_type(TBool()), 'and', EUnaryOp('unique', EVar('reqs').with_type(TBag(THandle('Request', TRecord((('rq_expiration', TNative('Date_t')), ('rq_host', TNative('HostAndPort')), ('rq_callback', TNative('std::unique_ptr<ConnectionPool::GetConnectionCallback>')))))))).with_type(TBool())).with_type(TBool())).with_type(TBool()), 'and', EBinOp(EBinOp(EBinOp(EVar('rt').with_type(TNative('Milliseconds')), '==', EVar('refreshRequirement').with_type(TNative('Milliseconds'))).with_type(TBool()), 'and', EBinOp(EVar('c').with_type(THandle('Connection', TRecord((('conn_state', TEnum(('READY', 'PROCESSING', 'CHECKED_OUT'))), ('conn_host', TNative('HostAndPort')), ('conn_iface', TNative('ConnectionPool::ConnectionInterface*')), ('conn_next_refresh', TNative('Date_t')), ('conn_returned', TNative('Date_t')), ('conn_dropped', TBool()))))), 'in', EVar('conns').with_type(TList(THandle('Connection', TRecord((('conn_state', TEnum(('READY', 'PROCESSING', 'CHECKED_OUT'))), ('conn_host', TNative('HostAndPort')), ('conn_iface', TNative('ConnectionPool::ConnectionInterface*')), ('conn_next_refresh', TNative('Date_t')), ('conn_returned', TNative('Date_t')), ('conn_dropped', TBool()))))))).with_type(TBool())).with_type(TBool()), 'and', EBinOp(EUnaryOp('all', EMap(EBinOp(EFlatMap(EVar('conns').with_type(TList(THandle('Connection', TRecord((('conn_state', TEnum(('READY', 'PROCESSING', 'CHECKED_OUT'))), ('conn_host', TNative('HostAndPort')), ('conn_iface', TNative('ConnectionPool::ConnectionInterface*')), ('conn_next_refresh', TNative('Date_t')), ('conn_returned', TNative('Date_t')), ('conn_dropped', TBool())))))), ELambda(EVar('_var810294').with_type(THandle('Connection', TRecord((('conn_state', TEnum(('READY', 'PROCESSING', 'CHECKED_OUT'))), ('conn_host', TNative('HostAndPort')), ('conn_iface', TNative('ConnectionPool::ConnectionInterface*')), ('conn_next_refresh', TNative('Date_t')), ('conn_returned', TNative('Date_t')), ('conn_dropped', TBool()))))), ESingleton(EVar('_var810294').with_type(THandle('Connection', TRecord((('conn_state', TEnum(('READY', 'PROCESSING', 'CHECKED_OUT'))), ('conn_host', TNative('HostAndPort')), ('conn_iface', TNative('ConnectionPool::ConnectionInterface*')), ('conn_next_refresh', TNative('Date_t')), ('conn_returned', TNative('Date_t')), ('conn_dropped', TBool())))))).with_type(TBag(THandle('Connection', TRecord((('conn_state', TEnum(('READY', 'PROCESSING', 'CHECKED_OUT'))), ('conn_host', TNative('HostAndPort')), ('conn_iface', TNative('ConnectionPool::ConnectionInterface*')), ('conn_next_refresh', TNative('Date_t')), ('conn_returned', TNative('Date_t')), ('conn_dropped', TBool())))))))).with_type(TBag(THandle('Connection', TRecord((('conn_state', TEnum(('READY', 'PROCESSING', 'CHECKED_OUT'))), ('conn_host', TNative('HostAndPort')), ('conn_iface', TNative('ConnectionPool::ConnectionInterface*')), ('conn_next_refresh', TNative('Date_t')), ('conn_returned', TNative('Date_t')), ('conn_dropped', TBool())))))), '+', ESingleton(EVar('c').with_type(THandle('Connection', TRecord((('conn_state', TEnum(('READY', 'PROCESSING', 'CHECKED_OUT'))), ('conn_host', TNative('HostAndPort')), ('conn_iface', TNative('ConnectionPool::ConnectionInterface*')), ('conn_next_refresh', TNative('Date_t')), ('conn_returned', TNative('Date_t')), ('conn_dropped', TBool())))))).with_type(TBag(THandle('Connection', TRecord((('conn_state', TEnum(('READY', 'PROCESSING', 'CHECKED_OUT'))), ('conn_host', TNative('HostAndPort')), ('conn_iface', TNative('ConnectionPool::ConnectionInterface*')), ('conn_next_refresh', TNative('Date_t')), ('conn_returned', TNative('Date_t')), ('conn_dropped', TBool()))))))).with_type(TBag(THandle('Connection', TRecord((('conn_state', TEnum(('READY', 'PROCESSING', 'CHECKED_OUT'))), ('conn_host', TNative('HostAndPort')), ('conn_iface', TNative('ConnectionPool::ConnectionInterface*')), ('conn_next_refresh', TNative('Date_t')), ('conn_returned', TNative('Date_t')), ('conn_dropped', TBool())))))), ELambda(EVar('_var810294').with_type(THandle('Connection', TRecord((('conn_state', TEnum(('READY', 'PROCESSING', 'CHECKED_OUT'))), ('conn_host', TNative('HostAndPort')), ('conn_iface', TNative('ConnectionPool::ConnectionInterface*')), ('conn_next_refresh', TNative('Date_t')), ('conn_returned', TNative('Date_t')), ('conn_dropped', TBool()))))), EUnaryOp('all', EMap(EBinOp(EFlatMap(EVar('conns').with_type(TList(THandle('Connection', TRecord((('conn_state', TEnum(('READY', 'PROCESSING', 'CHECKED_OUT'))), ('conn_host', TNative('HostAndPort')), ('conn_iface', TNative('ConnectionPool::ConnectionInterface*')), ('conn_next_refresh', TNative('Date_t')), ('conn_returned', TNative('Date_t')), ('conn_dropped', TBool())))))), ELambda(EVar('_var810294').with_type(THandle('Connection', TRecord((('conn_state', TEnum(('READY', 'PROCESSING', 'CHECKED_OUT'))), ('conn_host', TNative('HostAndPort')), ('conn_iface', TNative('ConnectionPool::ConnectionInterface*')), ('conn_next_refresh', TNative('Date_t')), ('conn_returned', TNative('Date_t')), ('conn_dropped', TBool()))))), ESingleton(EVar('_var810294').with_type(THandle('Connection', TRecord((('conn_state', TEnum(('READY', 'PROCESSING', 'CHECKED_OUT'))), ('conn_host', TNative('HostAndPort')), ('conn_iface', TNative('ConnectionPool::ConnectionInterface*')), ('conn_next_refresh', TNative('Date_t')), ('conn_returned', TNative('Date_t')), ('conn_dropped', TBool())))))).with_type(TBag(THandle('Connection', TRecord((('conn_state', TEnum(('READY', 'PROCESSING', 'CHECKED_OUT'))), ('conn_host', TNative('HostAndPort')), ('conn_iface', TNative('ConnectionPool::ConnectionInterface*')), ('conn_next_refresh', TNative('Date_t')), ('conn_returned', TNative('Date_t')), ('conn_dropped', TBool())))))))).with_type(TBag(THandle('Connection', TRecord((('conn_state', TEnum(('READY', 'PROCESSING', 'CHECKED_OUT'))), ('conn_host', TNative('HostAndPort')), ('conn_iface', TNative('ConnectionPool::ConnectionInterface*')), ('conn_next_refresh', TNative('Date_t')), ('conn_returned', TNative('Date_t')), ('conn_dropped', TBool())))))), '+', ESingleton(EVar('c').with_type(THandle('Connection', TRecord((('conn_state', TEnum(('READY', 'PROCESSING', 'CHECKED_OUT'))), ('conn_host', TNative('HostAndPort')), ('conn_iface', TNative('ConnectionPool::ConnectionInterface*')), ('conn_next_refresh', TNative('Date_t')), ('conn_returned', TNative('Date_t')), ('conn_dropped', TBool())))))).with_type(TBag(THandle('Connection', TRecord((('conn_state', TEnum(('READY', 'PROCESSING', 'CHECKED_OUT'))), ('conn_host', TNative('HostAndPort')), ('conn_iface', TNative('ConnectionPool::ConnectionInterface*')), ('conn_next_refresh', TNative('Date_t')), ('conn_returned', TNative('Date_t')), ('conn_dropped', TBool()))))))).with_type(TBag(THandle('Connection', TRecord((('conn_state', TEnum(('READY', 'PROCESSING', 'CHECKED_OUT'))), ('conn_host', TNative('HostAndPort')), ('conn_iface', TNative('ConnectionPool::ConnectionInterface*')), ('conn_next_refresh', TNative('Date_t')), ('conn_returned', TNative('Date_t')), ('conn_dropped', TBool())))))), ELambda(EVar('_var810295').with_type(THandle('Connection', TRecord((('conn_state', TEnum(('READY', 'PROCESSING', 'CHECKED_OUT'))), ('conn_host', TNative('HostAndPort')), ('conn_iface', TNative('ConnectionPool::ConnectionInterface*')), ('conn_next_refresh', TNative('Date_t')), ('conn_returned', TNative('Date_t')), ('conn_dropped', TBool()))))), EBinOp(EUnaryOp('not', EBinOp(EVar('_var810294').with_type(THandle('Connection', TRecord((('conn_state', TEnum(('READY', 'PROCESSING', 'CHECKED_OUT'))), ('conn_host', TNative('HostAndPort')), ('conn_iface', TNative('ConnectionPool::ConnectionInterface*')), ('conn_next_refresh', TNative('Date_t')), ('conn_returned', TNative('Date_t')), ('conn_dropped', TBool()))))), '==', EVar('_var810295').with_type(THandle('Connection', TRecord((('conn_state', TEnum(('READY', 'PROCESSING', 'CHECKED_OUT'))), ('conn_host', TNative('HostAndPort')), ('conn_iface', TNative('ConnectionPool::ConnectionInterface*')), ('conn_next_refresh', TNative('Date_t')), ('conn_returned', TNative('Date_t')), ('conn_dropped', TBool())))))).with_type(TBool())).with_type(TBool()), 'or', EBinOp(EGetField(EVar('_var810294').with_type(THandle('Connection', TRecord((('conn_state', TEnum(('READY', 'PROCESSING', 'CHECKED_OUT'))), ('conn_host', TNative('HostAndPort')), ('conn_iface', TNative('ConnectionPool::ConnectionInterface*')), ('conn_next_refresh', TNative('Date_t')), ('conn_returned', TNative('Date_t')), ('conn_dropped', TBool()))))), 'val').with_type(TRecord((('conn_state', TEnum(('READY', 'PROCESSING', 'CHECKED_OUT'))), ('conn_host', TNative('HostAndPort')), ('conn_iface', TNative('ConnectionPool::ConnectionInterface*')), ('conn_next_refresh', TNative('Date_t')), ('conn_returned', TNative('Date_t')), ('conn_dropped', TBool())))), '==', EGetField(EVar('_var810295').with_type(THandle('Connection', TRecord((('conn_state', TEnum(('READY', 'PROCESSING', 'CHECKED_OUT'))), ('conn_host', TNative('HostAndPort')), ('conn_iface', TNative('ConnectionPool::ConnectionInterface*')), ('conn_next_refresh', TNative('Date_t')), ('conn_returned', TNative('Date_t')), ('conn_dropped', TBool()))))), 'val').with_type(TRecord((('conn_state', TEnum(('READY', 'PROCESSING', 'CHECKED_OUT'))), ('conn_host', TNative('HostAndPort')), ('conn_iface', TNative('ConnectionPool::ConnectionInterface*')), ('conn_next_refresh', TNative('Date_t')), ('conn_returned', TNative('Date_t')), ('conn_dropped', TBool()))))).with_type(TBool())).with_type(TBool()))).with_type(TBag(TBool()))).with_type(TBool()))).with_type(TBag(TBool()))).with_type(TBool()), 'and', EUnaryOp('all', EMap(EFlatMap(EVar('reqs').with_type(TBag(THandle('Request', TRecord((('rq_expiration', TNative('Date_t')), ('rq_host', TNative('HostAndPort')), ('rq_callback', TNative('std::unique_ptr<ConnectionPool::GetConnectionCallback>'))))))), ELambda(EVar('_var810300').with_type(THandle('Request', TRecord((('rq_expiration', TNative('Date_t')), ('rq_host', TNative('HostAndPort')), ('rq_callback', TNative('std::unique_ptr<ConnectionPool::GetConnectionCallback>')))))), ESingleton(EVar('_var810300').with_type(THandle('Request', TRecord((('rq_expiration', TNative('Date_t')), ('rq_host', TNative('HostAndPort')), ('rq_callback', TNative('std::unique_ptr<ConnectionPool::GetConnectionCallback>'))))))).with_type(TBag(THandle('Request', TRecord((('rq_expiration', TNative('Date_t')), ('rq_host', TNative('HostAndPort')), ('rq_callback', TNative('std::unique_ptr<ConnectionPool::GetConnectionCallback>'))))))))).with_type(TBag(THandle('Request', TRecord((('rq_expiration', TNative('Date_t')), ('rq_host', TNative('HostAndPort')), ('rq_callback', TNative('std::unique_ptr<ConnectionPool::GetConnectionCallback>'))))))), ELambda(EVar('_var810300').with_type(THandle('Request', TRecord((('rq_expiration', TNative('Date_t')), ('rq_host', TNative('HostAndPort')), ('rq_callback', TNative('std::unique_ptr<ConnectionPool::GetConnectionCallback>')))))), EUnaryOp('all', EMap(EFlatMap(EVar('reqs').with_type(TBag(THandle('Request', TRecord((('rq_expiration', TNative('Date_t')), ('rq_host', TNative('HostAndPort')), ('rq_callback', TNative('std::unique_ptr<ConnectionPool::GetConnectionCallback>'))))))), ELambda(EVar('_var810300').with_type(THandle('Request', TRecord((('rq_expiration', TNative('Date_t')), ('rq_host', TNative('HostAndPort')), ('rq_callback', TNative('std::unique_ptr<ConnectionPool::GetConnectionCallback>')))))), ESingleton(EVar('_var810300').with_type(THandle('Request', TRecord((('rq_expiration', TNative('Date_t')), ('rq_host', TNative('HostAndPort')), ('rq_callback', TNative('std::unique_ptr<ConnectionPool::GetConnectionCallback>'))))))).with_type(TBag(THandle('Request', TRecord((('rq_expiration', TNative('Date_t')), ('rq_host', TNative('HostAndPort')), ('rq_callback', TNative('std::unique_ptr<ConnectionPool::GetConnectionCallback>'))))))))).with_type(TBag(THandle('Request', TRecord((('rq_expiration', TNative('Date_t')), ('rq_host', TNative('HostAndPort')), ('rq_callback', TNative('std::unique_ptr<ConnectionPool::GetConnectionCallback>'))))))), ELambda(EVar('_var810301').with_type(THandle('Request', TRecord((('rq_expiration', TNative('Date_t')), ('rq_host', TNative('HostAndPort')), ('rq_callback', TNative('std::unique_ptr<ConnectionPool::GetConnectionCallback>')))))), EBinOp(EUnaryOp('not', EBinOp(EVar('_var810300').with_type(THandle('Request', TRecord((('rq_expiration', TNative('Date_t')), ('rq_host', TNative('HostAndPort')), ('rq_callback', TNative('std::unique_ptr<ConnectionPool::GetConnectionCallback>')))))), '==', EVar('_var810301').with_type(THandle('Request', TRecord((('rq_expiration', TNative('Date_t')), ('rq_host', TNative('HostAndPort')), ('rq_callback', TNative('std::unique_ptr<ConnectionPool::GetConnectionCallback>'))))))).with_type(TBool())).with_type(TBool()), 'or', EBinOp(EGetField(EVar('_var810300').with_type(THandle('Request', TRecord((('rq_expiration', TNative('Date_t')), ('rq_host', TNative('HostAndPort')), ('rq_callback', TNative('std::unique_ptr<ConnectionPool::GetConnectionCallback>')))))), 'val').with_type(TRecord((('rq_expiration', TNative('Date_t')), ('rq_host', TNative('HostAndPort')), ('rq_callback', TNative('std::unique_ptr<ConnectionPool::GetConnectionCallback>'))))), '==', EGetField(EVar('_var810301').with_type(THandle('Request', TRecord((('rq_expiration', TNative('Date_t')), ('rq_host', TNative('HostAndPort')), ('rq_callback', TNative('std::unique_ptr<ConnectionPool::GetConnectionCallback>')))))), 'val').with_type(TRecord((('rq_expiration', TNative('Date_t')), ('rq_host', TNative('HostAndPort')), ('rq_callback', TNative('std::unique_ptr<ConnectionPool::GetConnectionCallback>')))))).with_type(TBool())).with_type(TBool()))).with_type(TBag(TBool()))).with_type(TBool()))).with_type(TBag(TBool()))).with_type(TBool())).with_type(TBool())).with_type(TBool())).with_type(TBool())
        assert self._do_cse_check(e)

    def test_fvs_depth(self):
        e = ZERO
        for i in range(500):
            e = ECond(EBinOp(e, "<=", ONE), ONE, ZERO).with_type(INT)
        res = free_vars(e)

    def test_fvs(self):
        e = EBinOp(EMapGet(EStateVar(EMakeMap2(EVar('l').with_type(TBag(INT)), ELambda(EVar('_var111').with_type(INT), EBinOp(EVar('_var111').with_type(INT), 'in', EVar('l').with_type(TBag(INT))).with_type(BOOL))).with_type(TMap(INT, BOOL))).with_type(TMap(INT, BOOL)), EVar('n').with_type(INT)).with_type(BOOL), '==', EBinOp(EVar('_var111').with_type(INT), 'in', EVar('l').with_type(TBag(INT))).with_type(BOOL)).with_type(BOOL)
        print(pprint(e))
        print(free_vars(e))
        assert free_vars(e) == OrderedSet([EVar('l').with_type(TBag(INT)), EVar('n').with_type(INT), EVar('_var111').with_type(INT)])

    def test_recursive_adt_repr(self):
        e = EStateVar(None)
        e.e = e
        print(repr(e))
        assert repr(e) == "EStateVar(<<recursive>>)"

    def test_var_under_estatevar(self):
        # wow, very tricky!
        # EStateVar(...) needs to be "separable" from the parent, so bound vars
        # get cleared.  Thus, if EStateVar(x) appears somewhere, then `x` is
        # is free, even if it appears in e.g. \x -> EStateVar(x).
        x = EVar("x").with_type(INT)
        e = EUnaryOp(UOp.Exists, EFilter(ESingleton(ONE), ELambda(x, EStateVar(EEq(x, ZERO)))))
        print(pprint(e))
        assert retypecheck(e)
        assert x in free_vars(e), free_vars(e)
        sub = subst(e, {"x":ZERO})
        assert sub == EUnaryOp(UOp.Exists, EFilter(ESingleton(ONE), ELambda(x, EStateVar(EEq(ZERO, ZERO))))), pprint(sub)

    def test_query_fvs(self):
        fvs = free_vars(Query('__isDistinct', 'public', [('startOffset', TInt())], [], EBinOp(EVar('startOffset').with_type(TInt()), '>=', EArgMax(EMap(EMap(EFilter(EVar('tokens').with_type(TBag(TTuple((TInt(), TRecord((('score', TFloat()), ('startOffset', TInt()), ('endOffset', TInt()), ('important', TBool()))))))), ELambda(EVar('t').with_type(TTuple((TInt(), TRecord((('score', TFloat()), ('startOffset', TInt()), ('endOffset', TInt()), ('important', TBool())))))), EGetField(ETupleGet(EVar('t').with_type(TTuple((TInt(), TRecord((('score', TFloat()), ('startOffset', TInt()), ('endOffset', TInt()), ('important', TBool())))))), 1).with_type(TRecord((('score', TFloat()), ('startOffset', TInt()), ('endOffset', TInt()), ('important', TBool())))), 'important').with_type(TBool()))).with_type(TBag(TTuple((TInt(), TRecord((('score', TFloat()), ('startOffset', TInt()), ('endOffset', TInt()), ('important', TBool()))))))), ELambda(EVar('t').with_type(TTuple((TInt(), TRecord((('score', TFloat()), ('startOffset', TInt()), ('endOffset', TInt()), ('important', TBool())))))), EVar('t').with_type(TTuple((TInt(), TRecord((('score', TFloat()), ('startOffset', TInt()), ('endOffset', TInt()), ('important', TBool())))))))).with_type(TBag(TTuple((TInt(), TRecord((('score', TFloat()), ('startOffset', TInt()), ('endOffset', TInt()), ('important', TBool()))))))), ELambda(EVar('tok').with_type(TTuple((TInt(), TRecord((('score', TFloat()), ('startOffset', TInt()), ('endOffset', TInt()), ('important', TBool())))))), EGetField(ETupleGet(EVar('tok').with_type(TTuple((TInt(), TRecord((('score', TFloat()), ('startOffset', TInt()), ('endOffset', TInt()), ('important', TBool())))))), 1).with_type(TRecord((('score', TFloat()), ('startOffset', TInt()), ('endOffset', TInt()), ('important', TBool())))), 'endOffset').with_type(TInt()))).with_type(TBag(TInt())), ELambda(EVar('x').with_type(TInt()), EVar('x').with_type(TInt()))).with_type(TInt())).with_type(TBool()), ""))
        assert EVar("startOffset") not in fvs

    def test_pickling(self):
        import pickle
        e = EVar("foo").with_type(INT)
        orig_hash = hash(e)
        ee = pickle.loads(pickle.dumps(e))
        assert not hasattr(ee, "_hash") # hash code should not be saved, since it is different each time Python is invoked
        assert e == ee
        assert orig_hash == hash(ee)
        assert e.type == ee.type

    def test_stm_fvs(self):
        use_x = SCall(ONE, "f", (EVar("x"),))
        assert list(free_vars(SDecl("x", EVar("x")))) == [EVar("x")]
        assert list(free_vars(SSeq(
            SDecl("x", ONE),
            use_x))) == []
        assert list(free_vars(SIf(T, SDecl("x", ONE), SNoOp()))) == []
        assert list(free_vars(SSeq(
            SIf(T, SDecl("x", ONE), SNoOp()),
            use_x))) == [EVar("x")]
        assert list(free_vars(SForEach(EVar("x"), EEmptyList(), use_x))) == []
        assert list(free_vars(SSeq(SForEach(EVar("x"), EEmptyList(), use_x), use_x))) == [EVar("x")]
        assert list(free_vars(SEscapableBlock("label", SDecl("x", ONE)))) == []
        assert list(free_vars(SWhile(T, SDecl("x", ONE)))) == []
        assert list(free_vars(SMapUpdate(T, T, EVar("x"), SSeq(SDecl("y", ONE), use_x)))) == []

    def test_deep_copy(self):
        e1 = ETuple((EVar("x"), EBinOp(EVar("x"), "+", EVar("y"))))
        e2 = deep_copy(e1)
        assert e1 == e2
        assert e1 is not e2
        assert e1.es is not e2.es
        assert e1.es[0] is not e2.es[0]
        assert e1.es[1] is not e2.es[1]
        assert e1.es[1].e1 is not e2.es[1].e1
        assert e1.es[1].e2 is not e2.es[1].e2

    def test_shallow_copy(self):
        e1 = ETuple((EVar("x"), EBinOp(EVar("x"), "+", EVar("y"))))
        e2 = shallow_copy(e1)
        assert e1 == e2
        assert e1 is not e2
        assert e1.es is e2.es

    def test_double_bound(self):
        xs = EVar("xs").with_type(INT_BAG)
        ys = EVar("ys").with_type(INT_BAG)
        x = EVar("x").with_type(INT)
        e = EMap(xs, ELambda(x, EMap(ys, ELambda(x, x))))
        assert retypecheck(e)
        found = False
        for ctx in enumerate_fragments(e):
            facts = EAll(ctx.facts)
            print("{} | {}".format(pprint(ctx.e), pprint(facts)))
            if ctx.e == x:
                found = True
                assert valid(EImplies(facts, EIn(x, ys)))
                assert not valid(EImplies(facts, EIn(x, xs)))
        assert found

    def test_self_bound(self):
        xs1 = EVar("xs").with_type(INT_BAG)
        xs2 = EVar("xs").with_type(INT)
        e = EMap(xs1, ELambda(xs2, xs2))
        assert retypecheck(e)
        found = False
        for ctx in enumerate_fragments(e):
            found = found or ctx.e == xs2
            assert not ctx.facts
        assert found

    def test_break_conj(self):
        x, y, z = [fresh_var(BOOL) for i in range(3)]
        e = EBinOp(
            EBinOp(EBinOp(EBinOp(x, BOp.And, y), BOp.Or, z), BOp.And, x), BOp.And,
            EBinOp(x, BOp.And, y))
        assert list(break_conj(e)) == [EBinOp(EBinOp(x, BOp.And, y), BOp.Or, z), x, x, y]

    def test_break_seq(self):
        x, y, z = [SNoOp() for i in range(3)]
        e = SSeq(SSeq(x, y), SSeq(y, z))
        l = list(break_seq(e))
        assert len(l) == 4
        assert l[0] is x
        assert l[1] is y
        assert l[2] is y
        assert l[3] is z
