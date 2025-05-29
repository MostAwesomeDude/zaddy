from rpython.rlib.rfile import create_stdio
from rpython.rlib.objectmodel import specialize
class Result(object): pass
class Failed(Result): pass
failed = Failed()
def cached(f, cacheCount=[0]):
    attr = "t" + str(cacheCount[0]); cacheCount[0] += 1
    name = f.__name__
    class CacheResult(Result):
        def __init__(self, i, rv): setattr(self, attr, (i, rv))
    cache = {}
    def deco(self, i):
        key = i
        if key in cache and cache[key] is failed: raise ParseError()
        elif key in cache: return getattr(cache[key], attr)
        cache[key] = failed
        i, rv = f(self, i)
        cache[key] = CacheResult(i, rv)
        self.lastMatch.append((name, key, i))
        return i, rv
    deco.__name__ = name
    return deco
@specialize.call_location()
def flatten(xs):
    rv = []
    for x in xs: rv.extend(x)
    return rv
class Builtin(object): pass
class Line(Builtin):
    def __init__(self, s): self.s = s
    def out(self, m): return [" " * (m * 4) + self.s]
class Block(Builtin):
    def __init__(self, ls): self.ls = ls
    def out(self, m): return flatten([l.out(m + 1) for l in flatten(self.ls)])
class Builder(object):
    def Line(self, s): return Line(s)
    def Block(self, ls): return Block(ls)
builtin = Builder()
class ParseError(Exception): pass
def lineNumber(s, i): return s.count(chr(10), 0, i)
def main(argv):
    stdin, stdout, stderr = create_stdio()
    parser = MainParser(stdin.read())
    try:
        i, rules = parser.parse()
        if i != len(parser.s):
            stderr.write("Failed to consume all input\n")
            raise ParseError()
        buf = []
        for rule in flatten(rules): buf.extend(rule.out(0))
        stdout.write("\n".join(buf))
        stderr.write("Wrote %d lines to stdout\n" % len(buf))
        return 0
    except ParseError:
        start = max(len(parser.lastMatch) - 25, 0)
        newlines = [0]
        for line in parser.s.split("\n"):
            newlines.append(newlines[-1] + len(line) + 1)
        for k, start, stop in parser.lastMatch[start:]:
            startLine = lineNumber(parser.s, start)
            startCol = start - newlines[startLine]
            stopLine = lineNumber(parser.s, stop)
            stopCol = stop - newlines[stopLine]
            t = k, startLine + 1, startCol, stopLine + 1, stopCol
            stderr.write(("Trail: %s (%d:%d - %d:%d)" % t) + chr(10))
        return 1
class pyFunctor(object):
    def Statement(self, line):
        return [builtin.Line(line)]
    def Ret(self, expr):
        return [builtin.Line('return ' + expr)]
    def RaiseIf(self, test):
        return [builtin.Line('if ' + test + ': raise ParseError()')]
    def Compound(self, head, block):
        return ([builtin.Line(head + ':'), builtin.Block(block)]) if block else ([builtin.Line(head + ': pass')])
    def Conditional(self, test, block):
        return ([builtin.Line('if ' + test + ':'), builtin.Block(block)]) if block else ([])
    def Handler(self, block, handler):
        return (([builtin.Line('try:'), builtin.Block(block), builtin.Line('except ParseError:'), builtin.Block(handler)]) if handler else (flatten(block))) if block else ([])
py = pyFunctor()
class productionFunctor(object):
    def Con(self, ty, con, prods):
        return ty + '.' + con + '(' + ', '.join(prods) + ')'
    def PlusMany(self, ps):
        return ' + '.join(ps)
    def Mod(self, left, right):
        return right + '.join(' + left + ')'
    def Flatten(self, l):
        return 'flatten(' + l + ')'
    def Name(self, s):
        return s
    def String(self, s):
        return chr(39) + s + chr(39)
    def List(self, prods):
        return '[' + ', '.join(prods) + ']'
    def Length(self, s):
        return 'str(len(' + s + '))'
    def Chr(self, n):
        return 'chr(' + n + ')'
    def Cond(self, t, c, o):
        return '(' + c + ') if ' + t + ' else (' + o + ')'
production = productionFunctor()
save = py.Statement('st.append(i)')
backup = py.Statement('i = st.pop()')
boundcheck = py.RaiseIf('i >= len(self.s)')
class pegFunctor(object):
    def Null(self):
        return []
    def AnyChar(self):
        return [boundcheck, py.Statement('rv = self.s[i]; i += 1')]
    def Char(self, i):
        return [boundcheck, py.RaiseIf('ord(self.s[i]) != ' + i), py.Statement('rv = self.s[i]; i += 1')]
    def Range(self, l, u):
        return [boundcheck, py.RaiseIf('not (' + l + ' <= ord(self.s[i]) <= ' + u + ')'), py.Statement('rv = self.s[i]; i += 1')]
    def Token(self, s):
        return [boundcheck, py.Statement('while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1'), boundcheck, py.RaiseIf('self.s[i:i + ' + str(len(s)) + '] != "' + s + '"'), py.Statement('self.lastMatch.append(("TOKEN ' + s + '", i, i + ' + str(len(s)) + '))'), py.Statement('rv = "' + s + '"; i += ' + str(len(s)))]
    def Call(self, s):
        return [py.Statement('i, rv = self.parse' + s + '(i)')]
    def Sequence(self, exprs):
        return flatten(exprs)
    def Choice(self, this, that):
        return [save, py.Handler(this, [backup] + that)]
    def Any(self, expr):
        return [py.Statement('rvs = []'), py.Compound('while True', [save, py.Handler(expr + [py.Statement('rvs.append(rv)')], [backup, py.Statement('break')])]), py.Statement('rv = rvs')]
    def Some(self, expr):
        return [py.Statement('rvs = []'), py.Compound('while True', [save, py.Handler(expr + [py.Statement('rvs.append(rv)')], [backup, py.Statement('break')])]), py.Statement('rv = rvs'), py.RaiseIf('not rv')]
    def Maybe(self, expr):
        return [save, py.Handler(expr, [py.Statement('rv = peg.Null()'), backup])]
    def Positive(self, expr):
        return [save, py.Handler(expr + [py.Statement('rv = True')], [py.Statement('rv = False')]), backup, py.RaiseIf('not rv')]
    def Negative(self, expr):
        return [save, py.Handler(expr + [py.Statement('rv = True')], [py.Statement('rv = False')]), backup, py.RaiseIf('rv')]
    def Capture(self, expr, name):
        return expr + [py.Statement(name + ' = rv')]
    def Production(self, expr, prod):
        return expr + [py.Statement('rv = ' + prod)]
peg = pegFunctor()
class rulesFunctor(object):
    def Fact(self, t):
        return '# ' + t
    def Clause(self, t, goal):
        return '# ' + t + ''.join(goal)
    def Rule(self, name, r):
        return '# ' + name + '@' + r
    def True(self):
        return 'true'
    def Eq(self, l, r):
        return l + '=' + r
    def Ignore(self):
        return '_'
    def Var(self, n):
        return n
    def Const(self, n):
        return n
    def Compound(self, func, vars):
        return ''.join([func] + vars)
    def Propagate(self, head, guard, goal):
        return ''.join(['Propagate('] + head + [', ' + guard + ', '] + goal + [')'])
    def Simplify(self, head, guard, goal):
        return ''.join(['Simplify('] + head + [', ' + guard + ', '] + goal + [')'])
    def Simpagate(self, keep, discard, guard, goal):
        return ''.join(['Simpagate('] + keep + discard + [', ' + guard + ', '] + goal + [')'])
rules = rulesFunctor()
# declare zero0
# declare succ2
# declare gte2
# declare max3
# declare root2
# declare link2
# declare branch2
# declare make1
# declare union2
# declare find2
# gteNzero
# gteNMsuccXNsuccYMgteXY
# maxLeft@Simplify(maxNzeroM, true, N=M)
# maxRight@Simplify(maxNMzero, true, N=M)
# maxSucc@Simpagate(succXLsuccYNsuccZMmaxLNM, true, maxXYZ)
# make@Simplify(makeA, true, rootAzero)
# union@Simplify(unionAB, true, findAXfindBYlinkXY)
# findNode@Simplify(branchABfindAX, true, findBXbranchAX)
# findRoot@Simpagate(rootA_findAX, true, X=A)
# linkEq@Simplify(linkAA, true, true)
# linkLeft@Simplify(linkABrootANrootBM, gteNM, branchBAsuccMM1maxRNM1rootAR)
# linkRight@Simplify(linkBArootANrootBM, gteNM, branchBAsuccMM1maxRNM1rootAR)
def target(driver, *args):
    driver.exe_name = "ZADDY".lower() + "c"
    return main, None
class ZADDYParser(object):
    def __init__(self, s):
        self.s = s; self.lastMatch = []
    def parse(self): return self.parseZADDY(0)
    @cached
    def parseWS(self, i):
        st = []
        rvs = []
        while True:
            st.append(i)
            try:
                st.append(i)
                try:
                    if i >= len(self.s): raise ParseError()
                    if ord(self.s[i]) != 9: raise ParseError()
                    rv = self.s[i]; i += 1
                except ParseError:
                    i = st.pop()
                    st.append(i)
                    try:
                        if i >= len(self.s): raise ParseError()
                        if ord(self.s[i]) != 10: raise ParseError()
                        rv = self.s[i]; i += 1
                    except ParseError:
                        i = st.pop()
                        st.append(i)
                        try:
                            if i >= len(self.s): raise ParseError()
                            if ord(self.s[i]) != 13: raise ParseError()
                            rv = self.s[i]; i += 1
                        except ParseError:
                            i = st.pop()
                            if i >= len(self.s): raise ParseError()
                            if ord(self.s[i]) != 32: raise ParseError()
                            rv = self.s[i]; i += 1
                rvs.append(rv)
            except ParseError:
                i = st.pop()
                break
        rv = rvs
        return i, rv
    @cached
    def parseDIGIT(self, i):
        st = []
        if i >= len(self.s): raise ParseError()
        if not (48 <= ord(self.s[i]) <= 57): raise ParseError()
        rv = self.s[i]; i += 1
        return i, rv
    @cached
    def parseUPPER(self, i):
        st = []
        if i >= len(self.s): raise ParseError()
        if not (65 <= ord(self.s[i]) <= 90): raise ParseError()
        rv = self.s[i]; i += 1
        return i, rv
    @cached
    def parseLOWER(self, i):
        st = []
        if i >= len(self.s): raise ParseError()
        if not (97 <= ord(self.s[i]) <= 122): raise ParseError()
        rv = self.s[i]; i += 1
        return i, rv
    @cached
    def parseALPHA(self, i):
        st = []
        st.append(i)
        try:
            i, rv = self.parseUPPER(i)
        except ParseError:
            i = st.pop()
            i, rv = self.parseLOWER(i)
        return i, rv
    @cached
    def parseESCAPE(self, i):
        st = []
        st.append(i)
        try:
            if i >= len(self.s): raise ParseError()
            if ord(self.s[i]) != 92: raise ParseError()
            rv = self.s[i]; i += 1
            if i >= len(self.s): raise ParseError()
            if ord(self.s[i]) != 92: raise ParseError()
            rv = self.s[i]; i += 1
            rv = chr(92) + chr(92)
        except ParseError:
            i = st.pop()
            if i >= len(self.s): raise ParseError()
            rv = self.s[i]; i += 1
        return i, rv
    @cached
    def parseSTRING(self, i):
        st = []
        i, rv = self.parseWS(i)
        if i >= len(self.s): raise ParseError()
        if ord(self.s[i]) != 39: raise ParseError()
        rv = self.s[i]; i += 1
        rvs = []
        while True:
            st.append(i)
            try:
                st.append(i)
                try:
                    st.append(i)
                    try:
                        if i >= len(self.s): raise ParseError()
                        if ord(self.s[i]) != 10: raise ParseError()
                        rv = self.s[i]; i += 1
                    except ParseError:
                        i = st.pop()
                        st.append(i)
                        try:
                            if i >= len(self.s): raise ParseError()
                            if ord(self.s[i]) != 13: raise ParseError()
                            rv = self.s[i]; i += 1
                        except ParseError:
                            i = st.pop()
                            if i >= len(self.s): raise ParseError()
                            if ord(self.s[i]) != 39: raise ParseError()
                            rv = self.s[i]; i += 1
                    rv = True
                except ParseError:
                    rv = False
                i = st.pop()
                if rv: raise ParseError()
                i, rv = self.parseESCAPE(i)
                rvs.append(rv)
            except ParseError:
                i = st.pop()
                break
        rv = rvs
        cs = rv
        if i >= len(self.s): raise ParseError()
        if ord(self.s[i]) != 39: raise ParseError()
        rv = self.s[i]; i += 1
        rv = ''.join(cs)
        return i, rv
    @cached
    def parseNUMBER(self, i):
        st = []
        i, rv = self.parseWS(i)
        i, rv = self.parseDIGIT(i)
        d = rv
        rvs = []
        while True:
            st.append(i)
            try:
                i, rv = self.parseDIGIT(i)
                rvs.append(rv)
            except ParseError:
                i = st.pop()
                break
        rv = rvs
        ds = rv
        rv = ''.join([d] + ds)
        return i, rv
    @cached
    def parseID(self, i):
        st = []
        i, rv = self.parseWS(i)
        i, rv = self.parseALPHA(i)
        c = rv
        rvs = []
        while True:
            st.append(i)
            try:
                st.append(i)
                try:
                    i, rv = self.parseALPHA(i)
                except ParseError:
                    i = st.pop()
                    i, rv = self.parseDIGIT(i)
                rvs.append(rv)
            except ParseError:
                i = st.pop()
                break
        rv = rvs
        cs = rv
        rv = ''.join([c] + cs)
        return i, rv
    @cached
    def parsePVAR(self, i):
        st = []
        i, rv = self.parseWS(i)
        i, rv = self.parseUPPER(i)
        x = rv
        rvs = []
        while True:
            st.append(i)
            try:
                st.append(i)
                try:
                    i, rv = self.parseALPHA(i)
                except ParseError:
                    i = st.pop()
                    i, rv = self.parseDIGIT(i)
                rvs.append(rv)
            except ParseError:
                i = st.pop()
                break
        rv = rvs
        xs = rv
        rv = ''.join([x] + xs)
        return i, rv
    @cached
    def parsePCONST(self, i):
        st = []
        i, rv = self.parseWS(i)
        rvs = []
        while True:
            st.append(i)
            try:
                i, rv = self.parseLOWER(i)
                rvs.append(rv)
            except ParseError:
                i = st.pop()
                break
        rv = rvs
        if not rv: raise ParseError()
        xs = rv
        rv = ''.join(xs)
        return i, rv
    @cached
    def parseZR(self, i):
        st = []
        i, rv = self.parseID(i)
        name = rv
        if i >= len(self.s): raise ParseError()
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError()
        if self.s[i:i + 1] != "=": raise ParseError()
        self.lastMatch.append(("TOKEN =", i, i + 1))
        rv = "="; i += 1
        st.append(i)
        try:
            i, rv = self.parseFIELDS(i)
            fs = rv
            rv = zephyr.Product(name, fs)
        except ParseError:
            i = st.pop()
            i, rv = self.parseCONSTRUCTOR(i)
            con = rv
            rvs = []
            while True:
                st.append(i)
                try:
                    if i >= len(self.s): raise ParseError()
                    while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                    if i >= len(self.s): raise ParseError()
                    if self.s[i:i + 1] != "|": raise ParseError()
                    self.lastMatch.append(("TOKEN |", i, i + 1))
                    rv = "|"; i += 1
                    i, rv = self.parseCONSTRUCTOR(i)
                    rvs.append(rv)
                except ParseError:
                    i = st.pop()
                    break
            rv = rvs
            cons = rv
            st.append(i)
            try:
                if i >= len(self.s): raise ParseError()
                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                if i >= len(self.s): raise ParseError()
                if self.s[i:i + 10] != "attributes": raise ParseError()
                self.lastMatch.append(("TOKEN attributes", i, i + 10))
                rv = "attributes"; i += 10
                i, rv = self.parseFIELDS(i)
            except ParseError:
                rv = peg.Null()
                i = st.pop()
            attrs = rv
            rv = zephyr.Sum(name, attrs, con, cons)
        return i, rv
    @cached
    def parseCONSTRUCTOR(self, i):
        st = []
        i, rv = self.parseID(i)
        tag = rv
        st.append(i)
        try:
            i, rv = self.parseFIELDS(i)
        except ParseError:
            rv = peg.Null()
            i = st.pop()
        args = rv
        rv = zephyr.Con(tag, args)
        return i, rv
    @cached
    def parseFIELDS(self, i):
        st = []
        if i >= len(self.s): raise ParseError()
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError()
        if self.s[i:i + 1] != "(": raise ParseError()
        self.lastMatch.append(("TOKEN (", i, i + 1))
        rv = "("; i += 1
        i, rv = self.parseFIELD(i)
        f = rv
        rvs = []
        while True:
            st.append(i)
            try:
                if i >= len(self.s): raise ParseError()
                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                if i >= len(self.s): raise ParseError()
                if self.s[i:i + 1] != ",": raise ParseError()
                self.lastMatch.append(("TOKEN ,", i, i + 1))
                rv = ","; i += 1
                i, rv = self.parseFIELD(i)
                rvs.append(rv)
            except ParseError:
                i = st.pop()
                break
        rv = rvs
        fs = rv
        if i >= len(self.s): raise ParseError()
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError()
        if self.s[i:i + 1] != ")": raise ParseError()
        self.lastMatch.append(("TOKEN )", i, i + 1))
        rv = ")"; i += 1
        rv = [f] + fs
        return i, rv
    @cached
    def parseFIELD(self, i):
        st = []
        st.append(i)
        try:
            i, rv = self.parseID(i)
            ty = rv
            st.append(i)
            try:
                i, rv = self.parseID(i)
            except ParseError:
                rv = peg.Null()
                i = st.pop()
            name = rv
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            if self.s[i:i + 1] != "?": raise ParseError()
            self.lastMatch.append(("TOKEN ?", i, i + 1))
            rv = "?"; i += 1
            rv = zephyr.Option(ty, name)
        except ParseError:
            i = st.pop()
            st.append(i)
            try:
                i, rv = self.parseID(i)
                ty = rv
                st.append(i)
                try:
                    i, rv = self.parseID(i)
                except ParseError:
                    rv = peg.Null()
                    i = st.pop()
                name = rv
                if i >= len(self.s): raise ParseError()
                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                if i >= len(self.s): raise ParseError()
                if self.s[i:i + 1] != "*": raise ParseError()
                self.lastMatch.append(("TOKEN *", i, i + 1))
                rv = "*"; i += 1
                rv = zephyr.Sequence(ty, name)
            except ParseError:
                i = st.pop()
                i, rv = self.parseID(i)
                ty = rv
                st.append(i)
                try:
                    i, rv = self.parseID(i)
                except ParseError:
                    rv = peg.Null()
                    i = st.pop()
                name = rv
                rv = zephyr.Id(ty, name)
        return i, rv
    @cached
    def parseRULES(self, i):
        st = []
        if i >= len(self.s): raise ParseError()
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError()
        if self.s[i:i + 6] != ".rules": raise ParseError()
        self.lastMatch.append(("TOKEN .rules", i, i + 6))
        rv = ".rules"; i += 6
        i, rv = self.parseCONSTRAINT(i)
        cs = rv
        rvs = []
        while True:
            st.append(i)
            try:
                i, rv = self.parseCHORN(i)
                rvs.append(rv)
            except ParseError:
                i = st.pop()
                break
        rv = rvs
        hs = rv
        rvs = []
        while True:
            st.append(i)
            try:
                i, rv = self.parseCHANDLER(i)
                rvs.append(rv)
            except ParseError:
                i = st.pop()
                break
        rv = rvs
        rs = rv
        rv = cs + hs + rs
        return i, rv
    @cached
    def parseCONSTRAINT(self, i):
        st = []
        st.append(i)
        try:
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            if self.s[i:i + 12] != ".constraints": raise ParseError()
            self.lastMatch.append(("TOKEN .constraints", i, i + 12))
            rv = ".constraints"; i += 12
            i, rv = self.parseCFUNCTOR(i)
            f = rv
            rvs = []
            while True:
                st.append(i)
                try:
                    if i >= len(self.s): raise ParseError()
                    while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                    if i >= len(self.s): raise ParseError()
                    if self.s[i:i + 1] != ",": raise ParseError()
                    self.lastMatch.append(("TOKEN ,", i, i + 1))
                    rv = ","; i += 1
                    i, rv = self.parseCFUNCTOR(i)
                    rvs.append(rv)
                except ParseError:
                    i = st.pop()
                    break
            rv = rvs
            fs = rv
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            if self.s[i:i + 1] != ".": raise ParseError()
            self.lastMatch.append(("TOKEN .", i, i + 1))
            rv = "."; i += 1
            rv = [f] + fs
        except ParseError:
            i = st.pop()
            rv = []
        return i, rv
    @cached
    def parseCFUNCTOR(self, i):
        st = []
        i, rv = self.parseID(i)
        name = rv
        if i >= len(self.s): raise ParseError()
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError()
        if self.s[i:i + 1] != "/": raise ParseError()
        self.lastMatch.append(("TOKEN /", i, i + 1))
        rv = "/"; i += 1
        i, rv = self.parseNUMBER(i)
        arity = rv
        rv = py.Statement('# declare ' + name + arity)
        return i, rv
    @cached
    def parseCHORN(self, i):
        st = []
        st.append(i)
        try:
            i, rv = self.parseCCOMPOUND(i)
            t = rv
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            if self.s[i:i + 1] != ".": raise ParseError()
            self.lastMatch.append(("TOKEN .", i, i + 1))
            rv = "."; i += 1
            rv = py.Statement(rules.Fact(t))
        except ParseError:
            i = st.pop()
            i, rv = self.parseCCOMPOUND(i)
            t = rv
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            if self.s[i:i + 2] != ":-": raise ParseError()
            self.lastMatch.append(("TOKEN :-", i, i + 2))
            rv = ":-"; i += 2
            i, rv = self.parseCGOALS(i)
            goal = rv
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            if self.s[i:i + 1] != ".": raise ParseError()
            self.lastMatch.append(("TOKEN .", i, i + 1))
            rv = "."; i += 1
            rv = py.Statement(rules.Clause(t, goal))
        return i, rv
    @cached
    def parseCHANDLER(self, i):
        st = []
        i, rv = self.parseID(i)
        name = rv
        if i >= len(self.s): raise ParseError()
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError()
        if self.s[i:i + 1] != "@": raise ParseError()
        self.lastMatch.append(("TOKEN @", i, i + 1))
        rv = "@"; i += 1
        i, rv = self.parseCHRULE(i)
        r = rv
        rv = py.Statement(rules.Rule(name, r))
        return i, rv
    @cached
    def parseCHRULE(self, i):
        st = []
        st.append(i)
        try:
            i, rv = self.parseCHEAD(i)
            head = rv
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            if self.s[i:i + 3] != "==>": raise ParseError()
            self.lastMatch.append(("TOKEN ==>", i, i + 3))
            rv = "==>"; i += 3
            i, rv = self.parseCGUARD(i)
            guard = rv
            i, rv = self.parseCGOALS(i)
            goal = rv
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            if self.s[i:i + 1] != ".": raise ParseError()
            self.lastMatch.append(("TOKEN .", i, i + 1))
            rv = "."; i += 1
            rv = rules.Propagate(head, guard, goal)
        except ParseError:
            i = st.pop()
            st.append(i)
            try:
                i, rv = self.parseCHEAD(i)
                head = rv
                if i >= len(self.s): raise ParseError()
                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                if i >= len(self.s): raise ParseError()
                if self.s[i:i + 3] != "<=>": raise ParseError()
                self.lastMatch.append(("TOKEN <=>", i, i + 3))
                rv = "<=>"; i += 3
                i, rv = self.parseCGUARD(i)
                guard = rv
                i, rv = self.parseCGOALS(i)
                goal = rv
                if i >= len(self.s): raise ParseError()
                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                if i >= len(self.s): raise ParseError()
                if self.s[i:i + 1] != ".": raise ParseError()
                self.lastMatch.append(("TOKEN .", i, i + 1))
                rv = "."; i += 1
                rv = rules.Simplify(head, guard, goal)
            except ParseError:
                i = st.pop()
                i, rv = self.parseCHEAD(i)
                keep = rv
                i, rv = self.parseWS(i)
                if i >= len(self.s): raise ParseError()
                if ord(self.s[i]) != 92: raise ParseError()
                rv = self.s[i]; i += 1
                i, rv = self.parseCHEAD(i)
                discard = rv
                if i >= len(self.s): raise ParseError()
                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                if i >= len(self.s): raise ParseError()
                if self.s[i:i + 3] != "<=>": raise ParseError()
                self.lastMatch.append(("TOKEN <=>", i, i + 3))
                rv = "<=>"; i += 3
                i, rv = self.parseCGUARD(i)
                guard = rv
                i, rv = self.parseCGOALS(i)
                goal = rv
                if i >= len(self.s): raise ParseError()
                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                if i >= len(self.s): raise ParseError()
                if self.s[i:i + 1] != ".": raise ParseError()
                self.lastMatch.append(("TOKEN .", i, i + 1))
                rv = "."; i += 1
                rv = rules.Simpagate(keep, discard, guard, goal)
        return i, rv
    @cached
    def parseCHEAD(self, i):
        st = []
        i, rv = self.parseCTERM(i)
        t = rv
        rvs = []
        while True:
            st.append(i)
            try:
                if i >= len(self.s): raise ParseError()
                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                if i >= len(self.s): raise ParseError()
                if self.s[i:i + 1] != ",": raise ParseError()
                self.lastMatch.append(("TOKEN ,", i, i + 1))
                rv = ","; i += 1
                i, rv = self.parseCTERM(i)
                rvs.append(rv)
            except ParseError:
                i = st.pop()
                break
        rv = rvs
        ts = rv
        rv = [t] + ts
        return i, rv
    @cached
    def parseCTERM(self, i):
        st = []
        st.append(i)
        try:
            i, rv = self.parseCCOMPOUND(i)
        except ParseError:
            i = st.pop()
            i, rv = self.parseCVAR(i)
        return i, rv
    @cached
    def parseCCOMPOUND(self, i):
        st = []
        i, rv = self.parseID(i)
        func = rv
        if i >= len(self.s): raise ParseError()
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError()
        if self.s[i:i + 1] != "(": raise ParseError()
        self.lastMatch.append(("TOKEN (", i, i + 1))
        rv = "("; i += 1
        i, rv = self.parseCHEAD(i)
        vars = rv
        if i >= len(self.s): raise ParseError()
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError()
        if self.s[i:i + 1] != ")": raise ParseError()
        self.lastMatch.append(("TOKEN )", i, i + 1))
        rv = ")"; i += 1
        rv = rules.Compound(func, vars)
        return i, rv
    @cached
    def parseCVAR(self, i):
        st = []
        st.append(i)
        try:
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            if self.s[i:i + 1] != "_": raise ParseError()
            self.lastMatch.append(("TOKEN _", i, i + 1))
            rv = "_"; i += 1
            rv = rules.Ignore()
        except ParseError:
            i = st.pop()
            st.append(i)
            try:
                i, rv = self.parsePVAR(i)
                name = rv
                rv = rules.Var(name)
            except ParseError:
                i = st.pop()
                i, rv = self.parsePCONST(i)
                name = rv
                rv = rules.Const(name)
        return i, rv
    @cached
    def parseCGUARD(self, i):
        st = []
        st.append(i)
        try:
            i, rv = self.parseCGOAL(i)
            g = rv
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            if self.s[i:i + 1] != "|": raise ParseError()
            self.lastMatch.append(("TOKEN |", i, i + 1))
            rv = "|"; i += 1
            rv = g
        except ParseError:
            i = st.pop()
            rv = rules.True()
        return i, rv
    @cached
    def parseCGOALS(self, i):
        st = []
        i, rv = self.parseCGOAL(i)
        g = rv
        rvs = []
        while True:
            st.append(i)
            try:
                if i >= len(self.s): raise ParseError()
                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                if i >= len(self.s): raise ParseError()
                if self.s[i:i + 1] != ",": raise ParseError()
                self.lastMatch.append(("TOKEN ,", i, i + 1))
                rv = ","; i += 1
                i, rv = self.parseCGOAL(i)
                rvs.append(rv)
            except ParseError:
                i = st.pop()
                break
        rv = rvs
        gs = rv
        rv = [g] + gs
        return i, rv
    @cached
    def parseCGOAL(self, i):
        st = []
        st.append(i)
        try:
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            if self.s[i:i + 4] != "true": raise ParseError()
            self.lastMatch.append(("TOKEN true", i, i + 4))
            rv = "true"; i += 4
            rv = rules.True()
        except ParseError:
            i = st.pop()
            st.append(i)
            try:
                i, rv = self.parseCVAR(i)
                l = rv
                if i >= len(self.s): raise ParseError()
                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                if i >= len(self.s): raise ParseError()
                if self.s[i:i + 1] != "=": raise ParseError()
                self.lastMatch.append(("TOKEN =", i, i + 1))
                rv = "="; i += 1
                i, rv = self.parseCVAR(i)
                r = rv
                rv = rules.Eq(l, r)
            except ParseError:
                i = st.pop()
                i, rv = self.parseCTERM(i)
        return i, rv
    @cached
    def parsePROD1(self, i):
        st = []
        st.append(i)
        try:
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            if self.s[i:i + 3] != ".if": raise ParseError()
            self.lastMatch.append(("TOKEN .if", i, i + 3))
            rv = ".if"; i += 3
            i, rv = self.parsePROD1(i)
            test = rv
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            if self.s[i:i + 5] != ".then": raise ParseError()
            self.lastMatch.append(("TOKEN .then", i, i + 5))
            rv = ".then"; i += 5
            i, rv = self.parsePROD1(i)
            cons = rv
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            if self.s[i:i + 5] != ".else": raise ParseError()
            self.lastMatch.append(("TOKEN .else", i, i + 5))
            rv = ".else"; i += 5
            i, rv = self.parsePROD1(i)
            other = rv
            rv = production.Cond(test, cons, other)
        except ParseError:
            i = st.pop()
            i, rv = self.parsePROD2(i)
        return i, rv
    @cached
    def parsePROD2(self, i):
        st = []
        st.append(i)
        try:
            i, rv = self.parsePROD3(i)
            this = rv
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            if self.s[i:i + 1] != "%": raise ParseError()
            self.lastMatch.append(("TOKEN %", i, i + 1))
            rv = "%"; i += 1
            i, rv = self.parsePROD2(i)
            that = rv
            rv = production.Mod(this, that)
        except ParseError:
            i = st.pop()
            i, rv = self.parsePROD3(i)
        return i, rv
    @cached
    def parsePROD3(self, i):
        st = []
        rvs = []
        while True:
            st.append(i)
            try:
                i, rv = self.parsePROD4(i)
                rvs.append(rv)
            except ParseError:
                i = st.pop()
                break
        rv = rvs
        if not rv: raise ParseError()
        ps = rv
        rv = production.PlusMany(ps)
        return i, rv
    @cached
    def parsePROD4(self, i):
        st = []
        st.append(i)
        try:
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            if self.s[i:i + 1] != "*": raise ParseError()
            self.lastMatch.append(("TOKEN *", i, i + 1))
            rv = "*"; i += 1
            i, rv = self.parsePROD5(i)
            prod = rv
            rv = production.Flatten(prod)
        except ParseError:
            i = st.pop()
            st.append(i)
            try:
                if i >= len(self.s): raise ParseError()
                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                if i >= len(self.s): raise ParseError()
                if self.s[i:i + 1] != "#": raise ParseError()
                self.lastMatch.append(("TOKEN #", i, i + 1))
                rv = "#"; i += 1
                i, rv = self.parsePROD5(i)
                prod = rv
                rv = production.Length(prod)
            except ParseError:
                i = st.pop()
                i, rv = self.parsePROD5(i)
        return i, rv
    @cached
    def parsePROD5(self, i):
        st = []
        st.append(i)
        try:
            i, rv = self.parseID(i)
            ty = rv
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            if self.s[i:i + 1] != ".": raise ParseError()
            self.lastMatch.append(("TOKEN .", i, i + 1))
            rv = "."; i += 1
            i, rv = self.parseID(i)
            con = rv
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            if self.s[i:i + 1] != "(": raise ParseError()
            self.lastMatch.append(("TOKEN (", i, i + 1))
            rv = "("; i += 1
            i, rv = self.parsePROD1(i)
            prod = rv
            rvs = []
            while True:
                st.append(i)
                try:
                    if i >= len(self.s): raise ParseError()
                    while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                    if i >= len(self.s): raise ParseError()
                    if self.s[i:i + 1] != ",": raise ParseError()
                    self.lastMatch.append(("TOKEN ,", i, i + 1))
                    rv = ","; i += 1
                    i, rv = self.parsePROD1(i)
                    rvs.append(rv)
                except ParseError:
                    i = st.pop()
                    break
            rv = rvs
            prods = rv
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            if self.s[i:i + 1] != ")": raise ParseError()
            self.lastMatch.append(("TOKEN )", i, i + 1))
            rv = ")"; i += 1
            rv = production.Con(ty, con, [prod] + prods)
        except ParseError:
            i = st.pop()
            st.append(i)
            try:
                i, rv = self.parseID(i)
                ty = rv
                if i >= len(self.s): raise ParseError()
                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                if i >= len(self.s): raise ParseError()
                if self.s[i:i + 1] != ".": raise ParseError()
                self.lastMatch.append(("TOKEN .", i, i + 1))
                rv = "."; i += 1
                i, rv = self.parseID(i)
                con = rv
                rv = production.Con(ty, con, [])
            except ParseError:
                i = st.pop()
                st.append(i)
                try:
                    if i >= len(self.s): raise ParseError()
                    while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                    if i >= len(self.s): raise ParseError()
                    if self.s[i:i + 2] != "[]": raise ParseError()
                    self.lastMatch.append(("TOKEN []", i, i + 2))
                    rv = "[]"; i += 2
                    rv = production.List([])
                except ParseError:
                    i = st.pop()
                    st.append(i)
                    try:
                        if i >= len(self.s): raise ParseError()
                        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                        if i >= len(self.s): raise ParseError()
                        if self.s[i:i + 6] != ".line(": raise ParseError()
                        self.lastMatch.append(("TOKEN .line(", i, i + 6))
                        rv = ".line("; i += 6
                        i, rv = self.parsePROD1(i)
                        l = rv
                        if i >= len(self.s): raise ParseError()
                        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                        if i >= len(self.s): raise ParseError()
                        if self.s[i:i + 1] != ")": raise ParseError()
                        self.lastMatch.append(("TOKEN )", i, i + 1))
                        rv = ")"; i += 1
                        rv = production.Con('builtin', 'Line', [l])
                    except ParseError:
                        i = st.pop()
                        st.append(i)
                        try:
                            if i >= len(self.s): raise ParseError()
                            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                            if i >= len(self.s): raise ParseError()
                            if self.s[i:i + 7] != ".block(": raise ParseError()
                            self.lastMatch.append(("TOKEN .block(", i, i + 7))
                            rv = ".block("; i += 7
                            i, rv = self.parsePROD1(i)
                            expr = rv
                            if i >= len(self.s): raise ParseError()
                            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                            if i >= len(self.s): raise ParseError()
                            if self.s[i:i + 1] != ")": raise ParseError()
                            self.lastMatch.append(("TOKEN )", i, i + 1))
                            rv = ")"; i += 1
                            rv = production.Con('builtin', 'Block', [expr])
                        except ParseError:
                            i = st.pop()
                            st.append(i)
                            try:
                                if i >= len(self.s): raise ParseError()
                                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                if i >= len(self.s): raise ParseError()
                                if self.s[i:i + 1] != "[": raise ParseError()
                                self.lastMatch.append(("TOKEN [", i, i + 1))
                                rv = "["; i += 1
                                i, rv = self.parsePROD1(i)
                                expr = rv
                                rvs = []
                                while True:
                                    st.append(i)
                                    try:
                                        if i >= len(self.s): raise ParseError()
                                        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                        if i >= len(self.s): raise ParseError()
                                        if self.s[i:i + 1] != ",": raise ParseError()
                                        self.lastMatch.append(("TOKEN ,", i, i + 1))
                                        rv = ","; i += 1
                                        i, rv = self.parsePROD1(i)
                                        rvs.append(rv)
                                    except ParseError:
                                        i = st.pop()
                                        break
                                rv = rvs
                                exprs = rv
                                if i >= len(self.s): raise ParseError()
                                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                if i >= len(self.s): raise ParseError()
                                if self.s[i:i + 1] != "]": raise ParseError()
                                self.lastMatch.append(("TOKEN ]", i, i + 1))
                                rv = "]"; i += 1
                                rv = production.List([expr] + exprs)
                            except ParseError:
                                i = st.pop()
                                st.append(i)
                                try:
                                    i, rv = self.parseID(i)
                                    s = rv
                                    rv = production.Name(s)
                                except ParseError:
                                    i = st.pop()
                                    st.append(i)
                                    try:
                                        i, rv = self.parseSTRING(i)
                                        s = rv
                                        rv = production.String(s)
                                    except ParseError:
                                        i = st.pop()
                                        st.append(i)
                                        try:
                                            i, rv = self.parseNUMBER(i)
                                            n = rv
                                            rv = production.Chr(n)
                                        except ParseError:
                                            i = st.pop()
                                            if i >= len(self.s): raise ParseError()
                                            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                            if i >= len(self.s): raise ParseError()
                                            if self.s[i:i + 1] != "(": raise ParseError()
                                            self.lastMatch.append(("TOKEN (", i, i + 1))
                                            rv = "("; i += 1
                                            i, rv = self.parsePROD1(i)
                                            prod = rv
                                            if i >= len(self.s): raise ParseError()
                                            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                            if i >= len(self.s): raise ParseError()
                                            if self.s[i:i + 1] != ")": raise ParseError()
                                            self.lastMatch.append(("TOKEN )", i, i + 1))
                                            rv = ")"; i += 1
                                            rv = prod
        return i, rv
    @cached
    def parseFUNCTOR(self, i):
        st = []
        if i >= len(self.s): raise ParseError()
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError()
        if self.s[i:i + 8] != ".functor": raise ParseError()
        self.lastMatch.append(("TOKEN .functor", i, i + 8))
        rv = ".functor"; i += 8
        i, rv = self.parseID(i)
        name = rv
        rvs = []
        while True:
            st.append(i)
            try:
                i, rv = self.parseFLET(i)
                rvs.append(rv)
            except ParseError:
                i = st.pop()
                break
        rv = rvs
        lets = rv
        rvs = []
        while True:
            st.append(i)
            try:
                i, rv = self.parseFRULE(i)
                rvs.append(rv)
            except ParseError:
                i = st.pop()
                break
        rv = rvs
        rules = rv
        rv = lets + [py.Compound('class ' + name + 'Functor(object)', rules), py.Statement(name + ' = ' + name + 'Functor()')]
        return i, rv
    @cached
    def parseFLET(self, i):
        st = []
        if i >= len(self.s): raise ParseError()
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError()
        if self.s[i:i + 3] != "let": raise ParseError()
        self.lastMatch.append(("TOKEN let", i, i + 3))
        rv = "let"; i += 3
        i, rv = self.parseID(i)
        name = rv
        if i >= len(self.s): raise ParseError()
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError()
        if self.s[i:i + 2] != ":=": raise ParseError()
        self.lastMatch.append(("TOKEN :=", i, i + 2))
        rv = ":="; i += 2
        i, rv = self.parsePROD1(i)
        prod = rv
        if i >= len(self.s): raise ParseError()
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError()
        if self.s[i:i + 1] != ";": raise ParseError()
        self.lastMatch.append(("TOKEN ;", i, i + 1))
        rv = ";"; i += 1
        rv = py.Statement(name + ' = ' + prod)
        return i, rv
    @cached
    def parseFRULE(self, i):
        st = []
        st.append(i)
        try:
            i, rv = self.parseID(i)
            tag = rv
            i, rv = self.parseFPATTS(i)
            patts = rv
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            if self.s[i:i + 2] != "->": raise ParseError()
            self.lastMatch.append(("TOKEN ->", i, i + 2))
            rv = "->"; i += 2
            i, rv = self.parsePROD1(i)
            prod = rv
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            if self.s[i:i + 1] != ";": raise ParseError()
            self.lastMatch.append(("TOKEN ;", i, i + 1))
            rv = ";"; i += 1
            rv = py.Compound('def ' + tag + '(self, ' + ', '.join(patts) + ')', [py.Ret(prod)])
        except ParseError:
            i = st.pop()
            i, rv = self.parseID(i)
            tag = rv
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            if self.s[i:i + 2] != "->": raise ParseError()
            self.lastMatch.append(("TOKEN ->", i, i + 2))
            rv = "->"; i += 2
            i, rv = self.parsePROD1(i)
            prod = rv
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            if self.s[i:i + 1] != ";": raise ParseError()
            self.lastMatch.append(("TOKEN ;", i, i + 1))
            rv = ";"; i += 1
            rv = py.Compound('def ' + tag + '(self)', [py.Ret(prod)])
        return i, rv
    @cached
    def parseFPATTS(self, i):
        st = []
        if i >= len(self.s): raise ParseError()
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError()
        if self.s[i:i + 1] != "(": raise ParseError()
        self.lastMatch.append(("TOKEN (", i, i + 1))
        rv = "("; i += 1
        i, rv = self.parseFPATT(i)
        p = rv
        rvs = []
        while True:
            st.append(i)
            try:
                if i >= len(self.s): raise ParseError()
                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                if i >= len(self.s): raise ParseError()
                if self.s[i:i + 1] != ",": raise ParseError()
                self.lastMatch.append(("TOKEN ,", i, i + 1))
                rv = ","; i += 1
                i, rv = self.parseFPATT(i)
                rvs.append(rv)
            except ParseError:
                i = st.pop()
                break
        rv = rvs
        ps = rv
        if i >= len(self.s): raise ParseError()
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError()
        if self.s[i:i + 1] != ")": raise ParseError()
        self.lastMatch.append(("TOKEN )", i, i + 1))
        rv = ")"; i += 1
        rv = [p] + ps
        return i, rv
    @cached
    def parseFPATT(self, i):
        st = []
        i, rv = self.parseID(i)
        return i, rv
    @cached
    def parseGRAMMAR(self, i):
        st = []
        if i >= len(self.s): raise ParseError()
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError()
        if self.s[i:i + 8] != ".grammar": raise ParseError()
        self.lastMatch.append(("TOKEN .grammar", i, i + 8))
        rv = ".grammar"; i += 8
        i, rv = self.parseID(i)
        name = rv
        rvs = []
        while True:
            st.append(i)
            try:
                i, rv = self.parsePRULE(i)
                rvs.append(rv)
            except ParseError:
                i = st.pop()
                break
        rv = rvs
        rules = rv
        rv = [py.Compound('def target(driver, *args)', [py.Statement('driver.exe_name = "' + name + '".lower() + "c"'), py.Ret('main, None')]), py.Compound('class ' + name + 'Parser(object)', [py.Compound('def __init__(self, s)', [py.Statement('self.s = s; self.lastMatch = []')]), py.Compound('def parse(self)', [py.Ret('self.parse' + name + '(0)')])] + flatten(rules)), py.Statement('MainParser = ' + name + 'Parser')]
        return i, rv
    @cached
    def parsePRULE(self, i):
        st = []
        i, rv = self.parseID(i)
        name = rv
        if i >= len(self.s): raise ParseError()
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError()
        if self.s[i:i + 2] != ":=": raise ParseError()
        self.lastMatch.append(("TOKEN :=", i, i + 2))
        rv = ":="; i += 2
        i, rv = self.parsePEXPR1(i)
        expr = rv
        if i >= len(self.s): raise ParseError()
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError()
        if self.s[i:i + 1] != ";": raise ParseError()
        self.lastMatch.append(("TOKEN ;", i, i + 1))
        rv = ";"; i += 1
        rv = [py.Statement('@cached'), py.Compound('def parse' + name + '(self, i)', [py.Statement('st = []')] + expr + [py.Ret('i, rv')])]
        return i, rv
    @cached
    def parsePEXPR1(self, i):
        st = []
        st.append(i)
        try:
            i, rv = self.parsePEXPR2(i)
            this = rv
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            if self.s[i:i + 1] != "/": raise ParseError()
            self.lastMatch.append(("TOKEN /", i, i + 1))
            rv = "/"; i += 1
            i, rv = self.parsePEXPR1(i)
            that = rv
            rv = peg.Choice(this, that)
        except ParseError:
            i = st.pop()
            i, rv = self.parsePEXPR2(i)
        return i, rv
    @cached
    def parsePEXPR2(self, i):
        st = []
        st.append(i)
        try:
            i, rv = self.parsePEXPR3(i)
            exprs = rv
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            if self.s[i:i + 2] != "->": raise ParseError()
            self.lastMatch.append(("TOKEN ->", i, i + 2))
            rv = "->"; i += 2
            i, rv = self.parsePROD1(i)
            prod = rv
            rv = peg.Production(exprs, prod)
        except ParseError:
            i = st.pop()
            i, rv = self.parsePEXPR3(i)
        return i, rv
    @cached
    def parsePEXPR3(self, i):
        st = []
        rvs = []
        while True:
            st.append(i)
            try:
                i, rv = self.parsePEXPR4(i)
                rvs.append(rv)
            except ParseError:
                i = st.pop()
                break
        rv = rvs
        exprs = rv
        rv = peg.Sequence(exprs)
        return i, rv
    @cached
    def parsePEXPR4(self, i):
        st = []
        st.append(i)
        try:
            i, rv = self.parsePEXPR5(i)
            expr = rv
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            if self.s[i:i + 1] != ":": raise ParseError()
            self.lastMatch.append(("TOKEN :", i, i + 1))
            rv = ":"; i += 1
            i, rv = self.parseID(i)
            name = rv
            rv = peg.Capture(expr, name)
        except ParseError:
            i = st.pop()
            i, rv = self.parsePEXPR5(i)
        return i, rv
    @cached
    def parsePEXPR5(self, i):
        st = []
        st.append(i)
        try:
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            if self.s[i:i + 1] != "&": raise ParseError()
            self.lastMatch.append(("TOKEN &", i, i + 1))
            rv = "&"; i += 1
            i, rv = self.parsePEXPR6(i)
            expr = rv
            rv = peg.Positive(expr)
        except ParseError:
            i = st.pop()
            st.append(i)
            try:
                if i >= len(self.s): raise ParseError()
                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                if i >= len(self.s): raise ParseError()
                if self.s[i:i + 1] != "!": raise ParseError()
                self.lastMatch.append(("TOKEN !", i, i + 1))
                rv = "!"; i += 1
                i, rv = self.parsePEXPR6(i)
                expr = rv
                rv = peg.Negative(expr)
            except ParseError:
                i = st.pop()
                i, rv = self.parsePEXPR6(i)
        return i, rv
    @cached
    def parsePEXPR6(self, i):
        st = []
        st.append(i)
        try:
            i, rv = self.parsePEXPR7(i)
            expr = rv
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            if self.s[i:i + 1] != "*": raise ParseError()
            self.lastMatch.append(("TOKEN *", i, i + 1))
            rv = "*"; i += 1
            rv = peg.Any(expr)
        except ParseError:
            i = st.pop()
            st.append(i)
            try:
                i, rv = self.parsePEXPR7(i)
                expr = rv
                if i >= len(self.s): raise ParseError()
                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                if i >= len(self.s): raise ParseError()
                if self.s[i:i + 1] != "+": raise ParseError()
                self.lastMatch.append(("TOKEN +", i, i + 1))
                rv = "+"; i += 1
                rv = peg.Some(expr)
            except ParseError:
                i = st.pop()
                st.append(i)
                try:
                    i, rv = self.parsePEXPR7(i)
                    expr = rv
                    if i >= len(self.s): raise ParseError()
                    while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                    if i >= len(self.s): raise ParseError()
                    if self.s[i:i + 1] != "?": raise ParseError()
                    self.lastMatch.append(("TOKEN ?", i, i + 1))
                    rv = "?"; i += 1
                    rv = peg.Maybe(expr)
                except ParseError:
                    i = st.pop()
                    i, rv = self.parsePEXPR7(i)
        return i, rv
    @cached
    def parsePEXPR7(self, i):
        st = []
        st.append(i)
        try:
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            if self.s[i:i + 7] != ".range(": raise ParseError()
            self.lastMatch.append(("TOKEN .range(", i, i + 7))
            rv = ".range("; i += 7
            i, rv = self.parseNUMBER(i)
            l = rv
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            if self.s[i:i + 1] != ":": raise ParseError()
            self.lastMatch.append(("TOKEN :", i, i + 1))
            rv = ":"; i += 1
            i, rv = self.parseNUMBER(i)
            u = rv
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            if self.s[i:i + 1] != ")": raise ParseError()
            self.lastMatch.append(("TOKEN )", i, i + 1))
            rv = ")"; i += 1
            rv = peg.Range(l, u)
        except ParseError:
            i = st.pop()
            st.append(i)
            try:
                if i >= len(self.s): raise ParseError()
                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                if i >= len(self.s): raise ParseError()
                if self.s[i:i + 4] != ".any": raise ParseError()
                self.lastMatch.append(("TOKEN .any", i, i + 4))
                rv = ".any"; i += 4
                rv = peg.AnyChar()
            except ParseError:
                i = st.pop()
                st.append(i)
                try:
                    i, rv = self.parseNUMBER(i)
                    c = rv
                    rv = peg.Char(c)
                except ParseError:
                    i = st.pop()
                    st.append(i)
                    try:
                        i, rv = self.parseID(i)
                        name = rv
                        rv = peg.Call(name)
                    except ParseError:
                        i = st.pop()
                        st.append(i)
                        try:
                            i, rv = self.parseSTRING(i)
                            s = rv
                            rv = peg.Token(s)
                        except ParseError:
                            i = st.pop()
                            if i >= len(self.s): raise ParseError()
                            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                            if i >= len(self.s): raise ParseError()
                            if self.s[i:i + 1] != "(": raise ParseError()
                            self.lastMatch.append(("TOKEN (", i, i + 1))
                            rv = "("; i += 1
                            i, rv = self.parsePEXPR1(i)
                            expr = rv
                            if i >= len(self.s): raise ParseError()
                            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                            if i >= len(self.s): raise ParseError()
                            if self.s[i:i + 1] != ")": raise ParseError()
                            self.lastMatch.append(("TOKEN )", i, i + 1))
                            rv = ")"; i += 1
                            rv = expr
        return i, rv
    @cached
    def parseZADDY(self, i):
        st = []
        i, rv = self.parseWS(i)
        rvs = []
        while True:
            st.append(i)
            try:
                st.append(i)
                try:
                    i, rv = self.parseRULES(i)
                except ParseError:
                    i = st.pop()
                    st.append(i)
                    try:
                        i, rv = self.parseFUNCTOR(i)
                    except ParseError:
                        i = st.pop()
                        i, rv = self.parseGRAMMAR(i)
                rvs.append(rv)
            except ParseError:
                i = st.pop()
                break
        rv = rvs
        clss = rv
        i, rv = self.parseWS(i)
        rv = [py.Statement('from rpython.rlib.rfile import create_stdio'), py.Statement('from rpython.rlib.objectmodel import specialize'), py.Compound('class Result(object)', []), py.Compound('class Failed(Result)', []), py.Statement('failed = Failed()'), py.Compound('def cached(f, cacheCount=[0])', [py.Statement('attr = "t" + str(cacheCount[0]); cacheCount[0] += 1'), py.Statement('name = f.__name__'), py.Statement('class CacheResult(Result):'), py.Statement('    def __init__(self, i, rv): setattr(self, attr, (i, rv))'), py.Statement('cache = {}'), py.Compound('def deco(self, i)', [py.Statement('key = i'), py.RaiseIf('key in cache and cache[key] is failed'), py.Statement('elif key in cache: return getattr(cache[key], attr)'), py.Statement('cache[key] = failed'), py.Statement('i, rv = f(self, i)'), py.Statement('cache[key] = CacheResult(i, rv)'), py.Statement('self.lastMatch.append((name, key, i))'), py.Ret('i, rv')]), py.Statement('deco.__name__ = name'), py.Ret('deco')]), py.Statement('@specialize.call_location()'), py.Compound('def flatten(xs)', [py.Statement('rv = []'), py.Statement('for x in xs: rv.extend(x)'), py.Ret('rv')]), py.Compound('class Builtin(object)', []), py.Statement('class Line(Builtin):'), py.Statement('    def __init__(self, s): self.s = s'), py.Statement('    def out(self, m): return [" " * (m * 4) + self.s]'), py.Statement('class Block(Builtin):'), py.Statement('    def __init__(self, ls): self.ls = ls'), py.Statement('    def out(self, m): return flatten([l.out(m + 1) for l in flatten(self.ls)])'), py.Statement('class Builder(object):'), py.Statement('    def Line(self, s): return Line(s)'), py.Statement('    def Block(self, ls): return Block(ls)'), py.Statement('builtin = Builder()'), py.Compound('class ParseError(Exception)', []), py.Compound('def lineNumber(s, i)', [py.Ret('s.count(chr(10), 0, i)')]), py.Compound('def main(argv)', [py.Statement('stdin, stdout, stderr = create_stdio()'), py.Statement('parser = MainParser(stdin.read())'), py.Handler([py.Statement('i, rules = parser.parse()'), py.Statement('if i != len(parser.s):'), py.Statement('    stderr.write("Failed to consume all input\\n")'), py.Statement('    raise ParseError()'), py.Statement('buf = []'), py.Statement('for rule in flatten(rules): buf.extend(rule.out(0))'), py.Statement('stdout.write("\\n".join(buf))'), py.Statement('stderr.write("Wrote %d lines to stdout\\n" % len(buf))'), py.Ret('0')], [py.Statement('start = max(len(parser.lastMatch) - 25, 0)'), py.Statement('newlines = [0]'), py.Statement('for line in parser.s.split("\\n"):'), py.Statement('    newlines.append(newlines[-1] + len(line) + 1)'), py.Statement('for k, start, stop in parser.lastMatch[start:]:'), py.Statement('    startLine = lineNumber(parser.s, start)'), py.Statement('    startCol = start - newlines[startLine]'), py.Statement('    stopLine = lineNumber(parser.s, stop)'), py.Statement('    stopCol = stop - newlines[stopLine]'), py.Statement('    t = k, startLine + 1, startCol, stopLine + 1, stopCol'), py.Statement('    stderr.write(("Trail: %s (%d:%d - %d:%d)" % t) + chr(10))'), py.Ret('1')])])] + flatten(clss)
        return i, rv
MainParser = ZADDYParser