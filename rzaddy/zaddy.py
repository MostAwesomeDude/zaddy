from rpython.rlib.rfile import create_stdio
from rpython.rlib.objectmodel import specialize
class Result(object): pass
class Failed(Result): pass
failed = Failed()
def cached(f, cacheCount=[0]):
    attr = "t" + str(cacheCount[0]); cacheCount[0] += 1
    name = f.__name__
    uname = unicode(name)
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
        self.lastMatch.append((uname, key, i))
        return i, rv
    deco.__name__ = name
    return deco
@specialize.call_location()
def flatten(xs):
    rv = []
    for x in xs: rv.extend(x)
    return rv
uf = []
def make():
    rv = len(uf)
    uf.append(rv)
    return rv
def find(i):
    j = uf[i]
    while uf[j] != j:
        uf[i], j, i = uf[j], uf[j], j
    return j
def union(i, j):
    i = find(i); j = find(j)
    if i != j:
        uf[i] = j
    return j
regNone = make()
class Builtin(object): pass
class Line(Builtin):
    def __init__(self, s): self.s = s
    def out(self, m): return [u" " * (m * 4) + self.s]
class Block(Builtin):
    def __init__(self, ls): self.ls = ls
    def out(self, m): return flatten([l.out(m + 1) for l in flatten(self.ls)])
class Builder(object):
    def Line(self, s): return Line(s)
    def Block(self, ls): return Block(ls)
builtin = Builder()
class ParseError(Exception): pass
def lineNumber(s, i):
    return s.count(unichr(10), 0, i)
def main(argv):
    stdin, stdout, stderr = create_stdio()
    parser = MainParser(stdin.read().decode("utf-8"))
    try:
        i, rules = parser.parse()
        if i != len(parser.s):
            stderr.write("Failed to consume all input\n")
            raise ParseError()
        buf = []
        for rule in flatten(rules): buf.extend(rule.out(0))
        stdout.write(u"\n".join(buf).encode("utf-8"))
        stderr.write("Wrote %d lines to stdout\n" % len(buf))
        return 0
    except ParseError:
        start = max(len(parser.lastMatch) - 25, 0)
        newlines = [0]
        for line in parser.s.split(u"\n"):
            newlines.append(newlines[-1] + len(line) + 1)
        for k, start, stop in parser.lastMatch[start:]:
            startLine = lineNumber(parser.s, start)
            startCol = start - newlines[startLine]
            stopLine = lineNumber(parser.s, stop)
            stopCol = stop - newlines[stopLine]
            t = k.encode("utf-8"), startLine + 1, startCol, stopLine + 1, stopCol
            stderr.write(("Trail: %s (%d:%d - %d:%d)" % t) + chr(10))
        return 1
class pyRels(object):
    Statement = {}
    Ret = {}
    RaiseIf = {}
    Compound = {}
    Conditional = {}
    Handler = {}
class pyFunctor(object):
    def Statement(self, line):
        return [builtin.Line(line)]
    def Ret(self, expr):
        return [builtin.Line(u'return ' + expr)]
    def RaiseIf(self, test):
        return [builtin.Line(u'if ' + test + u': raise ParseError()')]
    def Compound(self, head, block):
        return ([builtin.Line(head + u':'), builtin.Block(block)]) if block else ([builtin.Line(head + u': pass')])
    def Conditional(self, test, block):
        return ([builtin.Line(u'if ' + test + u':'), builtin.Block(block)]) if block else ([])
    def Handler(self, block, handler):
        return (([builtin.Line(u'try:'), builtin.Block(block), builtin.Line(u'except ParseError:'), builtin.Block(handler)]) if handler else (flatten(block))) if block else ([])
py = pyFunctor()
class productionRels(object):
    Con = {}
    PlusMany = {}
    Mod = {}
    Flatten = {}
    Name = {}
    String = {}
    List = {}
    Tuple = {}
    Length = {}
    Chr = {}
    Cond = {}
class productionFunctor(object):
    def Con(self, ty, con, prods):
        return ty + u'.' + con + u'(' + u', '.join(prods) + u')'
    def PlusMany(self, ps):
        return u' + '.join(ps)
    def Mod(self, left, right):
        return right + u'.join(' + left + u')'
    def Flatten(self, l):
        return u'flatten(' + l + u')'
    def Name(self, s):
        return s
    def String(self, s):
        return u'u' + unichr(39) + s + unichr(39)
    def List(self, prods):
        return u'[' + u', '.join(prods) + u']'
    def Tuple(self, prods):
        return u'(' + u', '.join(prods) + u')'
    def Length(self, s):
        return u'str(len(' + s + u')).decode("utf-8")'
    def Chr(self, n):
        return u'unichr(' + n + u')'
    def Cond(self, t, c, o):
        return u'(' + c + u') if ' + t + u' else (' + o + u')'
production = productionFunctor()
class pegRels(object):
    NamePatt = {}
    TuplePatt = {}
    Null = make()
    Token = {}
    Call = {}
    Sequence = {}
    Choice = {}
    Any = {}
    Some = {}
    Maybe = {}
    Positive = {}
    Negative = {}
    Capture = {}
    Production = {}
save = py.Statement(u'st.append(i)')
backup = py.Statement(u'i = st.pop()')
boundcheck = py.RaiseIf(u'i >= len(self.s)')
class pegFunctor(object):
    def NamePatt(self, name):
        return name
    def TuplePatt(self, ps):
        return u'(' + u', '.join(ps) + u')'
    def Null(self):
        return []
    def Token(self, s):
        return [boundcheck, py.Statement(u'while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1'), boundcheck, py.RaiseIf(u'self.s[i:i + ' + str(len(s)).decode("utf-8") + u'] != u"' + s + u'"'), py.Statement(u'self.lastMatch.append((u"TOKEN ' + s + u'", i, i + ' + str(len(s)).decode("utf-8") + u'))'), py.Statement(u'rv = u"' + s + u'"; i += ' + str(len(s)).decode("utf-8"))]
    def Call(self, s):
        return [py.Statement(u'i, rv = self.parse' + s + u'(i)')]
    def Sequence(self, exprs):
        return flatten(exprs)
    def Choice(self, this, that):
        return [save, py.Handler(this, [backup] + that)]
    def Any(self, expr):
        return [py.Statement(u'rvs = []'), py.Compound(u'while True', [save, py.Handler(expr + [py.Statement(u'rvs.append(rv)')], [backup, py.Statement(u'break')])]), py.Statement(u'rv = rvs')]
    def Some(self, expr):
        return [py.Statement(u'rvs = []'), py.Compound(u'while True', [save, py.Handler(expr + [py.Statement(u'rvs.append(rv)')], [backup, py.Statement(u'break')])]), py.Statement(u'rv = rvs'), py.RaiseIf(u'not rv')]
    def Maybe(self, expr):
        return [save, py.Handler(expr, [py.Statement(u'rv = peg.Null()'), backup])]
    def Positive(self, expr):
        return [save, py.Handler(expr + [py.Statement(u'rv = True')], [py.Statement(u'rv = False')]), backup, py.RaiseIf(u'not rv')]
    def Negative(self, expr):
        return [save, py.Handler(expr + [py.Statement(u'rv = True')], [py.Statement(u'rv = False')]), backup, py.RaiseIf(u'rv')]
    def Capture(self, expr, patt):
        return expr + [py.Statement(patt + u' = rv')]
    def Production(self, expr, prod):
        return expr + [py.Statement(u'rv = ' + prod)]
peg = pegFunctor()
class zephyrRels(object):
    Signature = {}
    Product = {}
    Sum = {}
    Con = {}
    Id = {}
    Option = {}
    Sequence = {}
class zephyrFunctor(object):
    def Signature(self, name, tys):
        return [py.Compound(u'class ' + name + u'Rels(object)', flatten(tys))]
    def Product(self, name, fs):
        return [py.Statement(u'# product ' + name)]
    def Sum(self, name, attrs, con, cons):
        return [con] + cons
    def Con(self, tag, args):
        return (py.Statement(tag + u' = {}')) if args else (py.Statement(tag + u' = make()'))
    def Option(self, ty, name):
        return u'option ' + name
    def Sequence(self, ty, name):
        return u'sequence ' + name
    def Id(self, ty, name):
        return u'id ' + name
zephyr = zephyrFunctor()
class rulesRels(object):
    IgnorePatt = make()
    Var = {}
    Const = {}
    Literal = {}
    StarPatt = {}
    PlusPatt = {}
    Compound = {}
    Rewrite = {}
class rulesFunctor(object):
    def IgnorePatt(self):
        return u'_'
    def Var(self, n):
        return n
    def Const(self, n):
        return n
    def Literal(self, s):
        return unichr(39) + s + unichr(39)
    def StarPatt(self, p):
        return p + u'*'
    def PlusPatt(self, p):
        return p + u'+'
    def Compound(self, ns, func, vars):
        return u'-'.join([ns + func] + vars)
    def Rewrite(self, name, ps, prod):
        return [py.Compound(u'def ' + name + u'()', [py.Statement(u'pass')])]
rules = rulesFunctor()
class charRels(object):
    Any = make()
    Exactly = {}
    Range = {}
    Call = {}
    Complement = {}
    Either = {}
class charFunctor(object):
    def Any(self):
        return u'True'
    def Exactly(self, c):
        return u'c == ' + c
    def Range(self, l, u):
        return l + u' <= c <= ' + u
    def Call(self, n):
        return u'self.cls' + n + u'(c)'
    def Complement(self, s):
        return u'not (' + s + u')'
    def Either(self, l, r):
        return u'(' + l + u') or (' + r + u')'
char = charFunctor()
def target(driver, *args):
    driver.exe_name = "ZADDY".lower() + "c"
    return main, None
class ZADDYParser(object):
    def __init__(self, s):
        self.s = s; self.lastMatch = []
    def parse(self):
        return self.parseZADDY(0)
    def clsWhitespace(self, c):
        return (c == 9) or ((c == 10) or ((c == 13) or (c == 32)))
    def clsDigit(self, c):
        return 48 <= c <= 57
    def clsUpper(self, c):
        return 65 <= c <= 90
    def clsLower(self, c):
        return 97 <= c <= 122
    def clsAlpha(self, c):
        return (self.clsUpper(c)) or (self.clsLower(c))
    def clsAlphanumeric(self, c):
        return (self.clsAlpha(c)) or (self.clsDigit(c))
    def clsQuote(self, c):
        return c == 39
    def clsQuoted(self, c):
        return not ((c == 10) or ((c == 13) or (c == 39)))
    def parseWS(self, i):
        if i >= len(self.s): raise ParseError()
        start = i
        while i < len(self.s) and self.clsWhitespace(ord(self.s[i])): i += 1
        return i, self.s[start:i]
    def parseNumber(self, i):
        if i >= len(self.s): raise ParseError()
        start = i
        if i >= len(self.s) or not self.clsDigit(ord(self.s[i])): raise ParseError()
        while i < len(self.s) and self.clsDigit(ord(self.s[i])): i += 1
        return i, self.s[start:i]
    def parseId(self, i):
        if i >= len(self.s): raise ParseError()
        start = i
        if i >= len(self.s) or not self.clsAlpha(ord(self.s[i])): raise ParseError()
        i += 1
        while i < len(self.s) and self.clsAlphanumeric(ord(self.s[i])): i += 1
        return i, self.s[start:i]
    def parsePVar(self, i):
        if i >= len(self.s): raise ParseError()
        start = i
        if i >= len(self.s) or not self.clsUpper(ord(self.s[i])): raise ParseError()
        i += 1
        while i < len(self.s) and self.clsAlphanumeric(ord(self.s[i])): i += 1
        return i, self.s[start:i]
    def parseZTId(self, i):
        if i >= len(self.s): raise ParseError()
        start = i
        if i >= len(self.s) or not self.clsLower(ord(self.s[i])): raise ParseError()
        i += 1
        while i < len(self.s) and self.clsAlphanumeric(ord(self.s[i])): i += 1
        return i, self.s[start:i]
    def parseZCId(self, i):
        if i >= len(self.s): raise ParseError()
        start = i
        if i >= len(self.s) or not self.clsUpper(ord(self.s[i])): raise ParseError()
        i += 1
        while i < len(self.s) and self.clsAlphanumeric(ord(self.s[i])): i += 1
        return i, self.s[start:i]
    def parseQuote(self, i):
        if i >= len(self.s): raise ParseError()
        start = i
        if i >= len(self.s) or not self.clsQuote(ord(self.s[i])): raise ParseError()
        i += 1
        return i, self.s[start:i]
    def parseQuoted(self, i):
        if i >= len(self.s): raise ParseError()
        start = i
        while i < len(self.s) and self.clsQuoted(ord(self.s[i])): i += 1
        return i, self.s[start:i]
    @cached
    def parseSTRING(self, i):
        st = []
        i, rv = self.parseWS(i)
        i, rv = self.parseQuote(i)
        i, rv = self.parseQuoted(i)
        q = rv
        i, rv = self.parseQuote(i)
        rv = q
        return i, rv
    @cached
    def parseID(self, i):
        st = []
        i, rv = self.parseWS(i)
        i, rv = self.parseId(i)
        return i, rv
    @cached
    def parseSIGNATURE(self, i):
        st = []
        if i >= len(self.s): raise ParseError()
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError()
        if self.s[i:i + 10] != u".signature": raise ParseError()
        self.lastMatch.append((u"TOKEN .signature", i, i + 10))
        rv = u".signature"; i += 10
        i, rv = self.parseID(i)
        name = rv
        rvs = []
        while True:
            st.append(i)
            try:
                i, rv = self.parseZTY(i)
                rvs.append(rv)
            except ParseError:
                i = st.pop()
                break
        rv = rvs
        tys = rv
        rv = zephyr.Signature(name, tys)
        return i, rv
    @cached
    def parseZTY(self, i):
        st = []
        i, rv = self.parseID(i)
        name = rv
        if i >= len(self.s): raise ParseError()
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError()
        if self.s[i:i + 1] != u"=": raise ParseError()
        self.lastMatch.append((u"TOKEN =", i, i + 1))
        rv = u"="; i += 1
        st.append(i)
        try:
            i, rv = self.parseFIELDS(i)
            fs = rv
            rv = zephyr.Product(name, fs)
        except ParseError:
            i = st.pop()
            i, rv = self.parseZCON(i)
            con = rv
            rvs = []
            while True:
                st.append(i)
                try:
                    if i >= len(self.s): raise ParseError()
                    while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                    if i >= len(self.s): raise ParseError()
                    if self.s[i:i + 1] != u"|": raise ParseError()
                    self.lastMatch.append((u"TOKEN |", i, i + 1))
                    rv = u"|"; i += 1
                    i, rv = self.parseZCON(i)
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
                if self.s[i:i + 10] != u"attributes": raise ParseError()
                self.lastMatch.append((u"TOKEN attributes", i, i + 10))
                rv = u"attributes"; i += 10
                i, rv = self.parseFIELDS(i)
                attrs = rv
                rv = zephyr.Sum(name, attrs, con, cons)
            except ParseError:
                i = st.pop()
                rv = zephyr.Sum(name, [], con, cons)
        return i, rv
    @cached
    def parseZCON(self, i):
        st = []
        i, rv = self.parseWS(i)
        st.append(i)
        try:
            i, rv = self.parseZCId(i)
            tag = rv
            i, rv = self.parseFIELDS(i)
            args = rv
            rv = zephyr.Con(tag, args)
        except ParseError:
            i = st.pop()
            i, rv = self.parseZCId(i)
            tag = rv
            rv = zephyr.Con(tag, [])
        return i, rv
    @cached
    def parseFIELDS(self, i):
        st = []
        if i >= len(self.s): raise ParseError()
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError()
        if self.s[i:i + 1] != u"(": raise ParseError()
        self.lastMatch.append((u"TOKEN (", i, i + 1))
        rv = u"("; i += 1
        i, rv = self.parseFIELD(i)
        f = rv
        rvs = []
        while True:
            st.append(i)
            try:
                if i >= len(self.s): raise ParseError()
                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                if i >= len(self.s): raise ParseError()
                if self.s[i:i + 1] != u",": raise ParseError()
                self.lastMatch.append((u"TOKEN ,", i, i + 1))
                rv = u","; i += 1
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
        if self.s[i:i + 1] != u")": raise ParseError()
        self.lastMatch.append((u"TOKEN )", i, i + 1))
        rv = u")"; i += 1
        rv = [f] + fs
        return i, rv
    @cached
    def parseFIELD(self, i):
        st = []
        i, rv = self.parseWS(i)
        st.append(i)
        try:
            i, rv = self.parseZTId(i)
            ty = rv
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            if self.s[i:i + 1] != u"?": raise ParseError()
            self.lastMatch.append((u"TOKEN ?", i, i + 1))
            rv = u"?"; i += 1
            i, rv = self.parseID(i)
            name = rv
            rv = zephyr.Option(ty, name)
        except ParseError:
            i = st.pop()
            st.append(i)
            try:
                i, rv = self.parseZTId(i)
                ty = rv
                if i >= len(self.s): raise ParseError()
                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                if i >= len(self.s): raise ParseError()
                if self.s[i:i + 1] != u"*": raise ParseError()
                self.lastMatch.append((u"TOKEN *", i, i + 1))
                rv = u"*"; i += 1
                i, rv = self.parseID(i)
                name = rv
                rv = zephyr.Sequence(ty, name)
            except ParseError:
                i = st.pop()
                i, rv = self.parseZTId(i)
                ty = rv
                i, rv = self.parseID(i)
                name = rv
                rv = zephyr.Id(ty, name)
        return i, rv
    @cached
    def parseRULES(self, i):
        st = []
        if i >= len(self.s): raise ParseError()
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError()
        if self.s[i:i + 6] != u".rules": raise ParseError()
        self.lastMatch.append((u"TOKEN .rules", i, i + 6))
        rv = u".rules"; i += 6
        rvs = []
        while True:
            st.append(i)
            try:
                i, rv = self.parseCHRULE(i)
                rvs.append(rv)
            except ParseError:
                i = st.pop()
                break
        rv = rvs
        hs = rv
        rv = flatten(hs)
        return i, rv
    @cached
    def parseCHRULE(self, i):
        st = []
        i, rv = self.parseID(i)
        name = rv
        if i >= len(self.s): raise ParseError()
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError()
        if self.s[i:i + 1] != u"@": raise ParseError()
        self.lastMatch.append((u"TOKEN @", i, i + 1))
        rv = u"@"; i += 1
        i, rv = self.parseCPATTS(i)
        ps = rv
        if i >= len(self.s): raise ParseError()
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError()
        if self.s[i:i + 3] != u"==>": raise ParseError()
        self.lastMatch.append((u"TOKEN ==>", i, i + 3))
        rv = u"==>"; i += 3
        i, rv = self.parseCPROD1(i)
        prod = rv
        if i >= len(self.s): raise ParseError()
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError()
        if self.s[i:i + 1] != u";": raise ParseError()
        self.lastMatch.append((u"TOKEN ;", i, i + 1))
        rv = u";"; i += 1
        rv = rules.Rewrite(name, ps, prod)
        return i, rv
    @cached
    def parseCLISTPATTS(self, i):
        st = []
        i, rv = self.parseCLISTPATT(i)
        p = rv
        rvs = []
        while True:
            st.append(i)
            try:
                if i >= len(self.s): raise ParseError()
                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                if i >= len(self.s): raise ParseError()
                if self.s[i:i + 1] != u",": raise ParseError()
                self.lastMatch.append((u"TOKEN ,", i, i + 1))
                rv = u","; i += 1
                i, rv = self.parseCLISTPATT(i)
                rvs.append(rv)
            except ParseError:
                i = st.pop()
                break
        rv = rvs
        ps = rv
        rv = [p] + ps
        return i, rv
    @cached
    def parseCLISTPATT(self, i):
        st = []
        st.append(i)
        try:
            i, rv = self.parseWS(i)
            i, rv = self.parsePVar(i)
            p = rv
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            if self.s[i:i + 1] != u"*": raise ParseError()
            self.lastMatch.append((u"TOKEN *", i, i + 1))
            rv = u"*"; i += 1
            rv = rules.StarPatt(p)
        except ParseError:
            i = st.pop()
            st.append(i)
            try:
                i, rv = self.parseWS(i)
                i, rv = self.parsePVar(i)
                p = rv
                if i >= len(self.s): raise ParseError()
                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                if i >= len(self.s): raise ParseError()
                if self.s[i:i + 1] != u"+": raise ParseError()
                self.lastMatch.append((u"TOKEN +", i, i + 1))
                rv = u"+"; i += 1
                rv = rules.PlusPatt(p)
            except ParseError:
                i = st.pop()
                i, rv = self.parseCPATT(i)
        return i, rv
    @cached
    def parseCPATTS(self, i):
        st = []
        i, rv = self.parseCPATT(i)
        p = rv
        rvs = []
        while True:
            st.append(i)
            try:
                if i >= len(self.s): raise ParseError()
                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                if i >= len(self.s): raise ParseError()
                if self.s[i:i + 1] != u",": raise ParseError()
                self.lastMatch.append((u"TOKEN ,", i, i + 1))
                rv = u","; i += 1
                i, rv = self.parseCPATT(i)
                rvs.append(rv)
            except ParseError:
                i = st.pop()
                break
        rv = rvs
        ps = rv
        rv = [p] + ps
        return i, rv
    @cached
    def parseCPATT(self, i):
        st = []
        st.append(i)
        try:
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            if self.s[i:i + 1] != u"[": raise ParseError()
            self.lastMatch.append((u"TOKEN [", i, i + 1))
            rv = u"["; i += 1
            i, rv = self.parseCLISTPATTS(i)
            ps = rv
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            if self.s[i:i + 1] != u"]": raise ParseError()
            self.lastMatch.append((u"TOKEN ]", i, i + 1))
            rv = u"]"; i += 1
            rv = rules.Compound(u'builtin', u'List', ps)
        except ParseError:
            i = st.pop()
            st.append(i)
            try:
                if i >= len(self.s): raise ParseError()
                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                if i >= len(self.s): raise ParseError()
                if self.s[i:i + 1] != u"_": raise ParseError()
                self.lastMatch.append((u"TOKEN _", i, i + 1))
                rv = u"_"; i += 1
                rv = rules.IgnorePatt()
            except ParseError:
                i = st.pop()
                st.append(i)
                try:
                    i, rv = self.parseSTRING(i)
                    s = rv
                    rv = rules.Literal(s)
                except ParseError:
                    i = st.pop()
                    st.append(i)
                    try:
                        i, rv = self.parseID(i)
                        ns = rv
                        if i >= len(self.s): raise ParseError()
                        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                        if i >= len(self.s): raise ParseError()
                        if self.s[i:i + 1] != u".": raise ParseError()
                        self.lastMatch.append((u"TOKEN .", i, i + 1))
                        rv = u"."; i += 1
                        i, rv = self.parseID(i)
                        func = rv
                        if i >= len(self.s): raise ParseError()
                        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                        if i >= len(self.s): raise ParseError()
                        if self.s[i:i + 1] != u"(": raise ParseError()
                        self.lastMatch.append((u"TOKEN (", i, i + 1))
                        rv = u"("; i += 1
                        i, rv = self.parseCPATTS(i)
                        ps = rv
                        if i >= len(self.s): raise ParseError()
                        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                        if i >= len(self.s): raise ParseError()
                        if self.s[i:i + 1] != u")": raise ParseError()
                        self.lastMatch.append((u"TOKEN )", i, i + 1))
                        rv = u")"; i += 1
                        rv = rules.Compound(ns, func, ps)
                    except ParseError:
                        i = st.pop()
                        st.append(i)
                        try:
                            i, rv = self.parseID(i)
                            ns = rv
                            if i >= len(self.s): raise ParseError()
                            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                            if i >= len(self.s): raise ParseError()
                            if self.s[i:i + 1] != u".": raise ParseError()
                            self.lastMatch.append((u"TOKEN .", i, i + 1))
                            rv = u"."; i += 1
                            i, rv = self.parseID(i)
                            func = rv
                            rv = rules.Compound(ns, func, [])
                        except ParseError:
                            i = st.pop()
                            i, rv = self.parseWS(i)
                            i, rv = self.parsePVar(i)
                            name = rv
                            rv = rules.Var(name)
        return i, rv
    @cached
    def parseCPRODS(self, i):
        st = []
        i, rv = self.parseCPROD1(i)
        p = rv
        rvs = []
        while True:
            st.append(i)
            try:
                if i >= len(self.s): raise ParseError()
                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                if i >= len(self.s): raise ParseError()
                if self.s[i:i + 1] != u",": raise ParseError()
                self.lastMatch.append((u"TOKEN ,", i, i + 1))
                rv = u","; i += 1
                i, rv = self.parseCPROD1(i)
                rvs.append(rv)
            except ParseError:
                i = st.pop()
                break
        rv = rvs
        ps = rv
        rv = [p] + ps
        return i, rv
    @cached
    def parseCPROD1(self, i):
        st = []
        rvs = []
        while True:
            st.append(i)
            try:
                i, rv = self.parseCPROD2(i)
                rvs.append(rv)
            except ParseError:
                i = st.pop()
                break
        rv = rvs
        if not rv: raise ParseError()
        ps = rv
        rv = u' '.join(ps)
        return i, rv
    @cached
    def parseCPROD2(self, i):
        st = []
        st.append(i)
        try:
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            if self.s[i:i + 1] != u"[": raise ParseError()
            self.lastMatch.append((u"TOKEN [", i, i + 1))
            rv = u"["; i += 1
            i, rv = self.parseCPRODS(i)
            ps = rv
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            if self.s[i:i + 1] != u"]": raise ParseError()
            self.lastMatch.append((u"TOKEN ]", i, i + 1))
            rv = u"]"; i += 1
            rv = rules.Compound(u'builtin', u'List', ps)
        except ParseError:
            i = st.pop()
            st.append(i)
            try:
                i, rv = self.parseSTRING(i)
                s = rv
                rv = rules.Literal(s)
            except ParseError:
                i = st.pop()
                st.append(i)
                try:
                    i, rv = self.parseID(i)
                    ns = rv
                    if i >= len(self.s): raise ParseError()
                    while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                    if i >= len(self.s): raise ParseError()
                    if self.s[i:i + 1] != u".": raise ParseError()
                    self.lastMatch.append((u"TOKEN .", i, i + 1))
                    rv = u"."; i += 1
                    i, rv = self.parseID(i)
                    func = rv
                    if i >= len(self.s): raise ParseError()
                    while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                    if i >= len(self.s): raise ParseError()
                    if self.s[i:i + 1] != u"(": raise ParseError()
                    self.lastMatch.append((u"TOKEN (", i, i + 1))
                    rv = u"("; i += 1
                    i, rv = self.parseCPRODS(i)
                    ps = rv
                    if i >= len(self.s): raise ParseError()
                    while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                    if i >= len(self.s): raise ParseError()
                    if self.s[i:i + 1] != u")": raise ParseError()
                    self.lastMatch.append((u"TOKEN )", i, i + 1))
                    rv = u")"; i += 1
                    rv = rules.Compound(ns, func, ps)
                except ParseError:
                    i = st.pop()
                    st.append(i)
                    try:
                        i, rv = self.parseID(i)
                        ns = rv
                        if i >= len(self.s): raise ParseError()
                        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                        if i >= len(self.s): raise ParseError()
                        if self.s[i:i + 1] != u".": raise ParseError()
                        self.lastMatch.append((u"TOKEN .", i, i + 1))
                        rv = u"."; i += 1
                        i, rv = self.parseID(i)
                        func = rv
                        rv = rules.Compound(ns, func, [])
                    except ParseError:
                        i = st.pop()
                        i, rv = self.parseWS(i)
                        i, rv = self.parsePVar(i)
                        name = rv
                        rv = rules.Var(name)
        return i, rv
    @cached
    def parsePROD1(self, i):
        st = []
        st.append(i)
        try:
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            if self.s[i:i + 3] != u".if": raise ParseError()
            self.lastMatch.append((u"TOKEN .if", i, i + 3))
            rv = u".if"; i += 3
            i, rv = self.parsePROD1(i)
            test = rv
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            if self.s[i:i + 5] != u".then": raise ParseError()
            self.lastMatch.append((u"TOKEN .then", i, i + 5))
            rv = u".then"; i += 5
            i, rv = self.parsePROD1(i)
            cons = rv
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            if self.s[i:i + 5] != u".else": raise ParseError()
            self.lastMatch.append((u"TOKEN .else", i, i + 5))
            rv = u".else"; i += 5
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
            if self.s[i:i + 1] != u"%": raise ParseError()
            self.lastMatch.append((u"TOKEN %", i, i + 1))
            rv = u"%"; i += 1
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
            if self.s[i:i + 1] != u"*": raise ParseError()
            self.lastMatch.append((u"TOKEN *", i, i + 1))
            rv = u"*"; i += 1
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
                if self.s[i:i + 1] != u"#": raise ParseError()
                self.lastMatch.append((u"TOKEN #", i, i + 1))
                rv = u"#"; i += 1
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
            if self.s[i:i + 1] != u".": raise ParseError()
            self.lastMatch.append((u"TOKEN .", i, i + 1))
            rv = u"."; i += 1
            i, rv = self.parseID(i)
            con = rv
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            if self.s[i:i + 1] != u"(": raise ParseError()
            self.lastMatch.append((u"TOKEN (", i, i + 1))
            rv = u"("; i += 1
            i, rv = self.parsePROD1(i)
            prod = rv
            rvs = []
            while True:
                st.append(i)
                try:
                    if i >= len(self.s): raise ParseError()
                    while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                    if i >= len(self.s): raise ParseError()
                    if self.s[i:i + 1] != u",": raise ParseError()
                    self.lastMatch.append((u"TOKEN ,", i, i + 1))
                    rv = u","; i += 1
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
            if self.s[i:i + 1] != u")": raise ParseError()
            self.lastMatch.append((u"TOKEN )", i, i + 1))
            rv = u")"; i += 1
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
                if self.s[i:i + 1] != u".": raise ParseError()
                self.lastMatch.append((u"TOKEN .", i, i + 1))
                rv = u"."; i += 1
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
                    if self.s[i:i + 2] != u"[]": raise ParseError()
                    self.lastMatch.append((u"TOKEN []", i, i + 2))
                    rv = u"[]"; i += 2
                    rv = production.List([])
                except ParseError:
                    i = st.pop()
                    st.append(i)
                    try:
                        if i >= len(self.s): raise ParseError()
                        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                        if i >= len(self.s): raise ParseError()
                        if self.s[i:i + 6] != u".line(": raise ParseError()
                        self.lastMatch.append((u"TOKEN .line(", i, i + 6))
                        rv = u".line("; i += 6
                        i, rv = self.parsePROD1(i)
                        l = rv
                        if i >= len(self.s): raise ParseError()
                        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                        if i >= len(self.s): raise ParseError()
                        if self.s[i:i + 1] != u")": raise ParseError()
                        self.lastMatch.append((u"TOKEN )", i, i + 1))
                        rv = u")"; i += 1
                        rv = production.Con(u'builtin', u'Line', [l])
                    except ParseError:
                        i = st.pop()
                        st.append(i)
                        try:
                            if i >= len(self.s): raise ParseError()
                            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                            if i >= len(self.s): raise ParseError()
                            if self.s[i:i + 7] != u".block(": raise ParseError()
                            self.lastMatch.append((u"TOKEN .block(", i, i + 7))
                            rv = u".block("; i += 7
                            i, rv = self.parsePROD1(i)
                            expr = rv
                            if i >= len(self.s): raise ParseError()
                            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                            if i >= len(self.s): raise ParseError()
                            if self.s[i:i + 1] != u")": raise ParseError()
                            self.lastMatch.append((u"TOKEN )", i, i + 1))
                            rv = u")"; i += 1
                            rv = production.Con(u'builtin', u'Block', [expr])
                        except ParseError:
                            i = st.pop()
                            st.append(i)
                            try:
                                if i >= len(self.s): raise ParseError()
                                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                if i >= len(self.s): raise ParseError()
                                if self.s[i:i + 1] != u"[": raise ParseError()
                                self.lastMatch.append((u"TOKEN [", i, i + 1))
                                rv = u"["; i += 1
                                i, rv = self.parsePROD1(i)
                                expr = rv
                                rvs = []
                                while True:
                                    st.append(i)
                                    try:
                                        if i >= len(self.s): raise ParseError()
                                        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                        if i >= len(self.s): raise ParseError()
                                        if self.s[i:i + 1] != u",": raise ParseError()
                                        self.lastMatch.append((u"TOKEN ,", i, i + 1))
                                        rv = u","; i += 1
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
                                if self.s[i:i + 1] != u"]": raise ParseError()
                                self.lastMatch.append((u"TOKEN ]", i, i + 1))
                                rv = u"]"; i += 1
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
                                            i, rv = self.parseWS(i)
                                            i, rv = self.parseNumber(i)
                                            n = rv
                                            rv = production.Chr(n)
                                        except ParseError:
                                            i = st.pop()
                                            st.append(i)
                                            try:
                                                if i >= len(self.s): raise ParseError()
                                                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                                if i >= len(self.s): raise ParseError()
                                                if self.s[i:i + 1] != u"(": raise ParseError()
                                                self.lastMatch.append((u"TOKEN (", i, i + 1))
                                                rv = u"("; i += 1
                                                i, rv = self.parsePROD1(i)
                                                p = rv
                                                rvs = []
                                                while True:
                                                    st.append(i)
                                                    try:
                                                        if i >= len(self.s): raise ParseError()
                                                        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                                        if i >= len(self.s): raise ParseError()
                                                        if self.s[i:i + 1] != u",": raise ParseError()
                                                        self.lastMatch.append((u"TOKEN ,", i, i + 1))
                                                        rv = u","; i += 1
                                                        i, rv = self.parsePROD1(i)
                                                        rvs.append(rv)
                                                    except ParseError:
                                                        i = st.pop()
                                                        break
                                                rv = rvs
                                                if not rv: raise ParseError()
                                                ps = rv
                                                if i >= len(self.s): raise ParseError()
                                                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                                if i >= len(self.s): raise ParseError()
                                                if self.s[i:i + 1] != u")": raise ParseError()
                                                self.lastMatch.append((u"TOKEN )", i, i + 1))
                                                rv = u")"; i += 1
                                                rv = production.Tuple([p] + ps)
                                            except ParseError:
                                                i = st.pop()
                                                if i >= len(self.s): raise ParseError()
                                                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                                if i >= len(self.s): raise ParseError()
                                                if self.s[i:i + 1] != u"(": raise ParseError()
                                                self.lastMatch.append((u"TOKEN (", i, i + 1))
                                                rv = u"("; i += 1
                                                i, rv = self.parsePROD1(i)
                                                prod = rv
                                                if i >= len(self.s): raise ParseError()
                                                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                                if i >= len(self.s): raise ParseError()
                                                if self.s[i:i + 1] != u")": raise ParseError()
                                                self.lastMatch.append((u"TOKEN )", i, i + 1))
                                                rv = u")"; i += 1
                                                rv = prod
        return i, rv
    @cached
    def parseFUNCTOR(self, i):
        st = []
        if i >= len(self.s): raise ParseError()
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError()
        if self.s[i:i + 8] != u".functor": raise ParseError()
        self.lastMatch.append((u"TOKEN .functor", i, i + 8))
        rv = u".functor"; i += 8
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
        rv = lets + [py.Compound(u'class ' + name + u'Functor(object)', rules), py.Statement(name + u' = ' + name + u'Functor()')]
        return i, rv
    @cached
    def parseFLET(self, i):
        st = []
        if i >= len(self.s): raise ParseError()
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError()
        if self.s[i:i + 3] != u"let": raise ParseError()
        self.lastMatch.append((u"TOKEN let", i, i + 3))
        rv = u"let"; i += 3
        i, rv = self.parseID(i)
        name = rv
        if i >= len(self.s): raise ParseError()
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError()
        if self.s[i:i + 2] != u":=": raise ParseError()
        self.lastMatch.append((u"TOKEN :=", i, i + 2))
        rv = u":="; i += 2
        i, rv = self.parsePROD1(i)
        prod = rv
        if i >= len(self.s): raise ParseError()
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError()
        if self.s[i:i + 1] != u";": raise ParseError()
        self.lastMatch.append((u"TOKEN ;", i, i + 1))
        rv = u";"; i += 1
        rv = py.Statement(name + u' = ' + prod)
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
            if self.s[i:i + 2] != u"->": raise ParseError()
            self.lastMatch.append((u"TOKEN ->", i, i + 2))
            rv = u"->"; i += 2
            i, rv = self.parsePROD1(i)
            prod = rv
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            if self.s[i:i + 1] != u";": raise ParseError()
            self.lastMatch.append((u"TOKEN ;", i, i + 1))
            rv = u";"; i += 1
            rv = py.Compound(u'def ' + tag + u'(self, ' + u', '.join(patts) + u')', [py.Ret(prod)])
        except ParseError:
            i = st.pop()
            i, rv = self.parseID(i)
            tag = rv
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            if self.s[i:i + 2] != u"->": raise ParseError()
            self.lastMatch.append((u"TOKEN ->", i, i + 2))
            rv = u"->"; i += 2
            i, rv = self.parsePROD1(i)
            prod = rv
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            if self.s[i:i + 1] != u";": raise ParseError()
            self.lastMatch.append((u"TOKEN ;", i, i + 1))
            rv = u";"; i += 1
            rv = py.Compound(u'def ' + tag + u'(self)', [py.Ret(prod)])
        return i, rv
    @cached
    def parseFPATTS(self, i):
        st = []
        if i >= len(self.s): raise ParseError()
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError()
        if self.s[i:i + 1] != u"(": raise ParseError()
        self.lastMatch.append((u"TOKEN (", i, i + 1))
        rv = u"("; i += 1
        i, rv = self.parseFPATT(i)
        p = rv
        rvs = []
        while True:
            st.append(i)
            try:
                if i >= len(self.s): raise ParseError()
                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                if i >= len(self.s): raise ParseError()
                if self.s[i:i + 1] != u",": raise ParseError()
                self.lastMatch.append((u"TOKEN ,", i, i + 1))
                rv = u","; i += 1
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
        if self.s[i:i + 1] != u")": raise ParseError()
        self.lastMatch.append((u"TOKEN )", i, i + 1))
        rv = u")"; i += 1
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
        if self.s[i:i + 8] != u".grammar": raise ParseError()
        self.lastMatch.append((u"TOKEN .grammar", i, i + 8))
        rv = u".grammar"; i += 8
        i, rv = self.parseID(i)
        name = rv
        rvs = []
        while True:
            st.append(i)
            try:
                st.append(i)
                try:
                    i, rv = self.parsePCLASS(i)
                except ParseError:
                    i = st.pop()
                    st.append(i)
                    try:
                        i, rv = self.parsePTOKEN(i)
                    except ParseError:
                        i = st.pop()
                        i, rv = self.parsePRULE(i)
                rvs.append(rv)
            except ParseError:
                i = st.pop()
                break
        rv = rvs
        rules = rv
        rv = [py.Compound(u'def target(driver, *args)', [py.Statement(u'driver.exe_name = "' + name + u'".lower() + "c"'), py.Ret(u'main, None')]), py.Compound(u'class ' + name + u'Parser(object)', [py.Compound(u'def __init__(self, s)', [py.Statement(u'self.s = s; self.lastMatch = []')]), py.Compound(u'def parse(self)', [py.Ret(u'self.parse' + name + u'(0)')])] + flatten(rules)), py.Statement(u'MainParser = ' + name + u'Parser')]
        return i, rv
    @cached
    def parsePCLASS(self, i):
        st = []
        if i >= len(self.s): raise ParseError()
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError()
        if self.s[i:i + 5] != u"class": raise ParseError()
        self.lastMatch.append((u"TOKEN class", i, i + 5))
        rv = u"class"; i += 5
        i, rv = self.parseID(i)
        name = rv
        if i >= len(self.s): raise ParseError()
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError()
        if self.s[i:i + 1] != u"=": raise ParseError()
        self.lastMatch.append((u"TOKEN =", i, i + 1))
        rv = u"="; i += 1
        i, rv = self.parseCLASSEXPR1(i)
        c = rv
        if i >= len(self.s): raise ParseError()
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError()
        if self.s[i:i + 1] != u";": raise ParseError()
        self.lastMatch.append((u"TOKEN ;", i, i + 1))
        rv = u";"; i += 1
        rv = [py.Compound(u'def cls' + name + u'(self, c)', [py.Ret(c)])]
        return i, rv
    @cached
    def parseCLASSEXPR1(self, i):
        st = []
        st.append(i)
        try:
            i, rv = self.parseCLASSEXPR2(i)
            l = rv
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            if self.s[i:i + 1] != u"|": raise ParseError()
            self.lastMatch.append((u"TOKEN |", i, i + 1))
            rv = u"|"; i += 1
            i, rv = self.parseCLASSEXPR1(i)
            r = rv
            rv = char.Either(l, r)
        except ParseError:
            i = st.pop()
            i, rv = self.parseCLASSEXPR2(i)
        return i, rv
    @cached
    def parseCLASSEXPR2(self, i):
        st = []
        st.append(i)
        try:
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            if self.s[i:i + 4] != u".any": raise ParseError()
            self.lastMatch.append((u"TOKEN .any", i, i + 4))
            rv = u".any"; i += 4
            rv = char.Any()
        except ParseError:
            i = st.pop()
            st.append(i)
            try:
                if i >= len(self.s): raise ParseError()
                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                if i >= len(self.s): raise ParseError()
                if self.s[i:i + 7] != u".range(": raise ParseError()
                self.lastMatch.append((u"TOKEN .range(", i, i + 7))
                rv = u".range("; i += 7
                i, rv = self.parseWS(i)
                i, rv = self.parseNumber(i)
                l = rv
                if i >= len(self.s): raise ParseError()
                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                if i >= len(self.s): raise ParseError()
                if self.s[i:i + 1] != u":": raise ParseError()
                self.lastMatch.append((u"TOKEN :", i, i + 1))
                rv = u":"; i += 1
                i, rv = self.parseWS(i)
                i, rv = self.parseNumber(i)
                u = rv
                if i >= len(self.s): raise ParseError()
                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                if i >= len(self.s): raise ParseError()
                if self.s[i:i + 1] != u")": raise ParseError()
                self.lastMatch.append((u"TOKEN )", i, i + 1))
                rv = u")"; i += 1
                rv = char.Range(l, u)
            except ParseError:
                i = st.pop()
                st.append(i)
                try:
                    if i >= len(self.s): raise ParseError()
                    while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                    if i >= len(self.s): raise ParseError()
                    if self.s[i:i + 1] != u"~": raise ParseError()
                    self.lastMatch.append((u"TOKEN ~", i, i + 1))
                    rv = u"~"; i += 1
                    i, rv = self.parseCLASSEXPR2(i)
                    s = rv
                    rv = char.Complement(s)
                except ParseError:
                    i = st.pop()
                    st.append(i)
                    try:
                        if i >= len(self.s): raise ParseError()
                        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                        if i >= len(self.s): raise ParseError()
                        if self.s[i:i + 1] != u"(": raise ParseError()
                        self.lastMatch.append((u"TOKEN (", i, i + 1))
                        rv = u"("; i += 1
                        i, rv = self.parseCLASSEXPR1(i)
                        s = rv
                        if i >= len(self.s): raise ParseError()
                        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                        if i >= len(self.s): raise ParseError()
                        if self.s[i:i + 1] != u")": raise ParseError()
                        self.lastMatch.append((u"TOKEN )", i, i + 1))
                        rv = u")"; i += 1
                        rv = s
                    except ParseError:
                        i = st.pop()
                        st.append(i)
                        try:
                            i, rv = self.parseWS(i)
                            i, rv = self.parseNumber(i)
                            c = rv
                            rv = char.Exactly(c)
                        except ParseError:
                            i = st.pop()
                            i, rv = self.parseID(i)
                            n = rv
                            rv = char.Call(n)
        return i, rv
    @cached
    def parsePTOKEN(self, i):
        st = []
        if i >= len(self.s): raise ParseError()
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError()
        if self.s[i:i + 5] != u"token": raise ParseError()
        self.lastMatch.append((u"TOKEN token", i, i + 5))
        rv = u"token"; i += 5
        i, rv = self.parseID(i)
        name = rv
        if i >= len(self.s): raise ParseError()
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError()
        if self.s[i:i + 1] != u"=": raise ParseError()
        self.lastMatch.append((u"TOKEN =", i, i + 1))
        rv = u"="; i += 1
        rvs = []
        while True:
            st.append(i)
            try:
                i, rv = self.parsePSCAN(i)
                rvs.append(rv)
            except ParseError:
                i = st.pop()
                break
        rv = rvs
        if not rv: raise ParseError()
        scans = rv
        if i >= len(self.s): raise ParseError()
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError()
        if self.s[i:i + 1] != u";": raise ParseError()
        self.lastMatch.append((u"TOKEN ;", i, i + 1))
        rv = u";"; i += 1
        rv = [py.Compound(u'def parse' + name + u'(self, i)', [boundcheck, py.Statement(u'start = i')] + flatten(scans) + [py.Ret(u'i, self.s[start:i]')])]
        return i, rv
    @cached
    def parsePSCAN(self, i):
        st = []
        st.append(i)
        try:
            i, rv = self.parseID(i)
            cls = rv
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            if self.s[i:i + 1] != u"*": raise ParseError()
            self.lastMatch.append((u"TOKEN *", i, i + 1))
            rv = u"*"; i += 1
            rv = [py.Statement(u'while i < len(self.s) and self.cls' + cls + u'(ord(self.s[i])): i += 1')]
        except ParseError:
            i = st.pop()
            st.append(i)
            try:
                i, rv = self.parseID(i)
                cls = rv
                if i >= len(self.s): raise ParseError()
                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                if i >= len(self.s): raise ParseError()
                if self.s[i:i + 1] != u"+": raise ParseError()
                self.lastMatch.append((u"TOKEN +", i, i + 1))
                rv = u"+"; i += 1
                rv = [py.RaiseIf(u'i >= len(self.s) or not self.cls' + cls + u'(ord(self.s[i]))'), py.Statement(u'while i < len(self.s) and self.cls' + cls + u'(ord(self.s[i])): i += 1')]
            except ParseError:
                i = st.pop()
                i, rv = self.parseID(i)
                cls = rv
                rv = [py.RaiseIf(u'i >= len(self.s) or not self.cls' + cls + u'(ord(self.s[i]))'), py.Statement(u'i += 1')]
        return i, rv
    @cached
    def parsePRULE(self, i):
        st = []
        i, rv = self.parseID(i)
        name = rv
        if i >= len(self.s): raise ParseError()
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError()
        if self.s[i:i + 2] != u":=": raise ParseError()
        self.lastMatch.append((u"TOKEN :=", i, i + 2))
        rv = u":="; i += 2
        i, rv = self.parsePEXPR1(i)
        expr = rv
        if i >= len(self.s): raise ParseError()
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError()
        if self.s[i:i + 1] != u";": raise ParseError()
        self.lastMatch.append((u"TOKEN ;", i, i + 1))
        rv = u";"; i += 1
        rv = [py.Statement(u'@cached'), py.Compound(u'def parse' + name + u'(self, i)', [py.Statement(u'st = []')] + expr + [py.Ret(u'i, rv')])]
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
            if self.s[i:i + 1] != u"/": raise ParseError()
            self.lastMatch.append((u"TOKEN /", i, i + 1))
            rv = u"/"; i += 1
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
            if self.s[i:i + 2] != u"->": raise ParseError()
            self.lastMatch.append((u"TOKEN ->", i, i + 2))
            rv = u"->"; i += 2
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
            if self.s[i:i + 1] != u":": raise ParseError()
            self.lastMatch.append((u"TOKEN :", i, i + 1))
            rv = u":"; i += 1
            i, rv = self.parsePPATT(i)
            p = rv
            rv = peg.Capture(expr, p)
        except ParseError:
            i = st.pop()
            i, rv = self.parsePEXPR5(i)
        return i, rv
    @cached
    def parsePPATT(self, i):
        st = []
        st.append(i)
        try:
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            if self.s[i:i + 1] != u"(": raise ParseError()
            self.lastMatch.append((u"TOKEN (", i, i + 1))
            rv = u"("; i += 1
            i, rv = self.parsePPATT(i)
            p = rv
            rvs = []
            while True:
                st.append(i)
                try:
                    if i >= len(self.s): raise ParseError()
                    while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                    if i >= len(self.s): raise ParseError()
                    if self.s[i:i + 1] != u",": raise ParseError()
                    self.lastMatch.append((u"TOKEN ,", i, i + 1))
                    rv = u","; i += 1
                    i, rv = self.parsePPATT(i)
                    rvs.append(rv)
                except ParseError:
                    i = st.pop()
                    break
            rv = rvs
            ps = rv
            rv = peg.TuplePatt([p] + ps)
        except ParseError:
            i = st.pop()
            i, rv = self.parseID(i)
            name = rv
            rv = peg.NamePatt(name)
        return i, rv
    @cached
    def parsePEXPR5(self, i):
        st = []
        st.append(i)
        try:
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            if self.s[i:i + 1] != u"&": raise ParseError()
            self.lastMatch.append((u"TOKEN &", i, i + 1))
            rv = u"&"; i += 1
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
                if self.s[i:i + 1] != u"!": raise ParseError()
                self.lastMatch.append((u"TOKEN !", i, i + 1))
                rv = u"!"; i += 1
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
            if self.s[i:i + 1] != u"*": raise ParseError()
            self.lastMatch.append((u"TOKEN *", i, i + 1))
            rv = u"*"; i += 1
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
                if self.s[i:i + 1] != u"+": raise ParseError()
                self.lastMatch.append((u"TOKEN +", i, i + 1))
                rv = u"+"; i += 1
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
                    if self.s[i:i + 1] != u"?": raise ParseError()
                    self.lastMatch.append((u"TOKEN ?", i, i + 1))
                    rv = u"?"; i += 1
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
            if self.s[i:i + 1] != u"(": raise ParseError()
            self.lastMatch.append((u"TOKEN (", i, i + 1))
            rv = u"("; i += 1
            i, rv = self.parsePEXPR1(i)
            expr = rv
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            if self.s[i:i + 1] != u")": raise ParseError()
            self.lastMatch.append((u"TOKEN )", i, i + 1))
            rv = u")"; i += 1
            rv = expr
        except ParseError:
            i = st.pop()
            st.append(i)
            try:
                i, rv = self.parseSTRING(i)
                s = rv
                rv = peg.Token(s)
            except ParseError:
                i = st.pop()
                i, rv = self.parseID(i)
                name = rv
                rv = peg.Call(name)
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
                        i, rv = self.parseSIGNATURE(i)
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
        rv = [py.Statement(u'from rpython.rlib.rfile import create_stdio'), py.Statement(u'from rpython.rlib.objectmodel import specialize'), py.Compound(u'class Result(object)', []), py.Compound(u'class Failed(Result)', []), py.Statement(u'failed = Failed()'), py.Compound(u'def cached(f, cacheCount=[0])', [py.Statement(u'attr = "t" + str(cacheCount[0]); cacheCount[0] += 1'), py.Statement(u'name = f.__name__'), py.Statement(u'uname = unicode(name)'), py.Compound(u'class CacheResult(Result)', [py.Statement(u'def __init__(self, i, rv): setattr(self, attr, (i, rv))')]), py.Statement(u'cache = {}'), py.Compound(u'def deco(self, i)', [py.Statement(u'key = i'), py.RaiseIf(u'key in cache and cache[key] is failed'), py.Statement(u'elif key in cache: return getattr(cache[key], attr)'), py.Statement(u'cache[key] = failed'), py.Statement(u'i, rv = f(self, i)'), py.Statement(u'cache[key] = CacheResult(i, rv)'), py.Statement(u'self.lastMatch.append((uname, key, i))'), py.Ret(u'i, rv')]), py.Statement(u'deco.__name__ = name'), py.Ret(u'deco')]), py.Statement(u'@specialize.call_location()'), py.Compound(u'def flatten(xs)', [py.Statement(u'rv = []'), py.Statement(u'for x in xs: rv.extend(x)'), py.Ret(u'rv')]), py.Statement(u'uf = []'), py.Compound(u'def make()', [py.Statement(u'rv = len(uf)'), py.Statement(u'uf.append(rv)'), py.Ret(u'rv')]), py.Compound(u'def find(i)', [py.Statement(u'j = uf[i]'), py.Compound(u'while uf[j] != j', [py.Statement(u'uf[i], j, i = uf[j], uf[j], j')]), py.Ret(u'j')]), py.Compound(u'def union(i, j)', [py.Statement(u'i = find(i); j = find(j)'), py.Conditional(u'i != j', [py.Statement(u'uf[i] = j')]), py.Ret(u'j')]), py.Statement(u'regNone = make()'), py.Compound(u'class Builtin(object)', []), py.Compound(u'class Line(Builtin)', [py.Statement(u'def __init__(self, s): self.s = s'), py.Statement(u'def out(self, m): return [u" " * (m * 4) + self.s]')]), py.Compound(u'class Block(Builtin)', [py.Statement(u'def __init__(self, ls): self.ls = ls'), py.Statement(u'def out(self, m): return flatten([l.out(m + 1) for l in flatten(self.ls)])')]), py.Compound(u'class Builder(object)', [py.Statement(u'def Line(self, s): return Line(s)'), py.Statement(u'def Block(self, ls): return Block(ls)')]), py.Statement(u'builtin = Builder()'), py.Compound(u'class ParseError(Exception)', []), py.Compound(u'def lineNumber(s, i)', [py.Ret(u's.count(unichr(10), 0, i)')]), py.Compound(u'def main(argv)', [py.Statement(u'stdin, stdout, stderr = create_stdio()'), py.Statement(u'parser = MainParser(stdin.read().decode("utf-8"))'), py.Handler([py.Statement(u'i, rules = parser.parse()'), py.Conditional(u'i != len(parser.s)', [py.Statement(u'stderr.write("Failed to consume all input\\n")'), py.Statement(u'raise ParseError()')]), py.Statement(u'buf = []'), py.Statement(u'for rule in flatten(rules): buf.extend(rule.out(0))'), py.Statement(u'stdout.write(u"\\n".join(buf).encode("utf-8"))'), py.Statement(u'stderr.write("Wrote %d lines to stdout\\n" % len(buf))'), py.Ret(u'0')], [py.Statement(u'start = max(len(parser.lastMatch) - 25, 0)'), py.Statement(u'newlines = [0]'), py.Compound(u'for line in parser.s.split(u"\\n")', [py.Statement(u'newlines.append(newlines[-1] + len(line) + 1)')]), py.Compound(u'for k, start, stop in parser.lastMatch[start:]', [py.Statement(u'startLine = lineNumber(parser.s, start)'), py.Statement(u'startCol = start - newlines[startLine]'), py.Statement(u'stopLine = lineNumber(parser.s, stop)'), py.Statement(u'stopCol = stop - newlines[stopLine]'), py.Statement(u't = k.encode("utf-8"), startLine + 1, startCol, stopLine + 1, stopCol'), py.Statement(u'stderr.write(("Trail: %s (%d:%d - %d:%d)" % t) + chr(10))')]), py.Ret(u'1')])])] + flatten(clss)
        return i, rv
MainParser = ZADDYParser