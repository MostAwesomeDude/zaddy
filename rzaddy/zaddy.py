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
ruleNames = []
def rewrite(f):
    ruleNames.append((f, f.__name__))
    return f
@specialize.call_location()
def flatten(xs):
    rv = []
    for x in xs: rv.extend(x)
    return rv
def flattenList(i):
    rv = []
    for x in findList(i): rv.extend(findList(x))
    return makeList(rv)
def intersect(l, r):
    rv = []
    for x in r:
        if x in l: rv.append(x)
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
interned = {}
def makeStr(s):
    rv = make()
    interned[rv] = s
    return rv
def findStr(i): return interned[find(i)]
allLists = []
def makeList(l):
    rv = make()
    allLists.append([rv] + l)
    return rv
emptyList = makeList([])
def findList(i):
    i = find(i)
    return next([l[1:] for l in allLists if l[0] == i])
class Builtin(object): pass
class EmitLine(Builtin):
    def __init__(self, s): self.s = s
    def out(self, m): return [u" " * (m * 4) + self.s]
class EmitBlock(Builtin):
    def __init__(self, ls): self.ls = ls
    def out(self, m): return flatten([l.out(m + 1) for l in flatten(self.ls)])
class Builder(object):
    def Line(self, s): return EmitLine(s)
    def Block(self, ls): return EmitBlock(ls)
builtin = Builder()
class builtinRels:
    Line = {}; Block = {}
    def makeLine(self, s):
        rv = make()
        self.Line[rv, s] = None
        return rv
    def findLine(self, i):
        ss = [s for (x, s) in self.Line if x == i]
        return EmitLine(findStr(next(ss)))
    def makeBlock(self, ls):
        rv = make()
        self.Block[rv, ls] = None
        return rv
    def findBlock(self, i):
        lss = [ls for (x, ls) in self.Block if x == i]
        return EmitBlock([self.findbuiltin(x) for x in findList(next(lss))])
    def findbuiltin(self, i):
        try:
            return self.findLine(i)
        except StopIteration:
            return self.findBlock(i)
class ParseError(Exception): pass
def lineNumber(s, i):
    return s.count(unichr(10), 0, i)
def main(argv):
    stdin, stdout, stderr = create_stdio()
    stderr.write("Registered %d rewrite rules\n" % len(ruleNames))
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
    def makeStatement(self, line):
        rv = make()
        self.Statement[rv, line] = None
        return rv
    Ret = {}
    def makeRet(self, expr):
        rv = make()
        self.Ret[rv, expr] = None
        return rv
    RaiseIf = {}
    def makeRaiseIf(self, test):
        rv = make()
        self.RaiseIf[rv, test] = None
        return rv
    Compound = {}
    def makeCompound(self, head, block):
        rv = make()
        self.Compound[rv, head, block] = None
        return rv
    Conditional = {}
    def makeConditional(self, test, block):
        rv = make()
        self.Conditional[rv, test, block] = None
        return rv
    Handler = {}
    def makeHandler(self, block, handler):
        rv = make()
        self.Handler[rv, block, handler] = None
        return rv
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
    def makeCon(self, ty, con, prods):
        rv = make()
        self.Con[rv, ty, con, prods] = None
        return rv
    PlusMany = {}
    def makePlusMany(self, ps):
        rv = make()
        self.PlusMany[rv, ps] = None
        return rv
    Mod = {}
    def makeMod(self, left, right):
        rv = make()
        self.Mod[rv, left, right] = None
        return rv
    Flatten = {}
    def makeFlatten(self, l):
        rv = make()
        self.Flatten[rv, l] = None
        return rv
    Name = {}
    def makeName(self, s):
        rv = make()
        self.Name[rv, s] = None
        return rv
    String = {}
    def makeString(self, s):
        rv = make()
        self.String[rv, s] = None
        return rv
    List = {}
    def makeList(self, prods):
        rv = make()
        self.List[rv, prods] = None
        return rv
    Length = {}
    def makeLength(self, s):
        rv = make()
        self.Length[rv, s] = None
        return rv
    Chr = {}
    def makeChr(self, n):
        rv = make()
        self.Chr[rv, n] = None
        return rv
    Cond = {}
    def makeCond(self, t, c, o):
        rv = make()
        self.Cond[rv, t, c, o] = None
        return rv
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
    def Length(self, s):
        return u'str(len(' + s + u')).decode("utf-8")'
    def Chr(self, n):
        return u'unichr(' + n + u')'
    def Cond(self, t, c, o):
        return u'(' + c + u') if ' + t + u' else (' + o + u')'
production = productionFunctor()
class pegRels(object):
    NamePatt = {}
    def makeNamePatt(self, name):
        rv = make()
        self.NamePatt[rv, name] = None
        return rv
    TuplePatt = {}
    def makeTuplePatt(self, ps):
        rv = make()
        self.TuplePatt[rv, ps] = None
        return rv
    Null = make()
    Token = {}
    def makeToken(self, s):
        rv = make()
        self.Token[rv, s] = None
        return rv
    Call = {}
    def makeCall(self, s):
        rv = make()
        self.Call[rv, s] = None
        return rv
    Sequence = {}
    def makeSequence(self, exprs):
        rv = make()
        self.Sequence[rv, exprs] = None
        return rv
    Choice = {}
    def makeChoice(self, this, that):
        rv = make()
        self.Choice[rv, this, that] = None
        return rv
    Any = {}
    def makeAny(self, expr):
        rv = make()
        self.Any[rv, expr] = None
        return rv
    Some = {}
    def makeSome(self, expr):
        rv = make()
        self.Some[rv, expr] = None
        return rv
    Maybe = {}
    def makeMaybe(self, expr):
        rv = make()
        self.Maybe[rv, expr] = None
        return rv
    Positive = {}
    def makePositive(self, expr):
        rv = make()
        self.Positive[rv, expr] = None
        return rv
    Negative = {}
    def makeNegative(self, expr):
        rv = make()
        self.Negative[rv, expr] = None
        return rv
    Capture = {}
    def makeCapture(self, expr, patt):
        rv = make()
        self.Capture[rv, expr, patt] = None
        return rv
    Production = {}
    def makeProduction(self, expr, prod):
        rv = make()
        self.Production[rv, expr, prod] = None
        return rv
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
        return [save, py.Handler(this, flatten([[backup], that]))]
    def Any(self, expr):
        return [py.Statement(u'rvs = []'), py.Compound(u'while True', [save, py.Handler(flatten([expr, [py.Statement(u'rvs.append(rv)')]]), [backup, py.Statement(u'break')])]), py.Statement(u'rv = rvs')]
    def Some(self, expr):
        return [py.Statement(u'rvs = []'), py.Compound(u'while True', [save, py.Handler(flatten([expr, [py.Statement(u'rvs.append(rv)')]]), [backup, py.Statement(u'break')])]), py.Statement(u'rv = rvs'), py.RaiseIf(u'not rv')]
    def Maybe(self, expr):
        return [save, py.Handler(expr, [py.Statement(u'rv = peg.Null()'), backup])]
    def Positive(self, expr):
        return [save, py.Handler(flatten([expr, [py.Statement(u'rv = True')]]), [py.Statement(u'rv = False')]), backup, py.RaiseIf(u'not rv')]
    def Negative(self, expr):
        return [save, py.Handler(flatten([expr, [py.Statement(u'rv = True')]]), [py.Statement(u'rv = False')]), backup, py.RaiseIf(u'rv')]
    def Capture(self, expr, patt):
        return expr + [py.Statement(patt + u' = rv')]
    def Production(self, expr, prod):
        return expr + [py.Statement(u'rv = ' + prod)]
peg = pegFunctor()
class zephyrRels(object):
    Signature = {}
    def makeSignature(self, name, tys):
        rv = make()
        self.Signature[rv, name, tys] = None
        return rv
    Product = {}
    def makeProduct(self, name, fs):
        rv = make()
        self.Product[rv, name, fs] = None
        return rv
    Sum = {}
    def makeSum(self, name, attrs, con, cons):
        rv = make()
        self.Sum[rv, name, attrs, con, cons] = None
        return rv
    Con = {}
    def makeCon(self, tag, args):
        rv = make()
        self.Con[rv, tag, args] = None
        return rv
    Id = {}
    def makeId(self, ty, name):
        rv = make()
        self.Id[rv, ty, name] = None
        return rv
    Option = {}
    def makeOption(self, ty, name):
        rv = make()
        self.Option[rv, ty, name] = None
        return rv
    Sequence = {}
    def makeSequence(self, ty, name):
        rv = make()
        self.Sequence[rv, ty, name] = None
        return rv
class zephyrFunctor(object):
    def Signature(self, name, tys):
        return [py.Compound(u'class ' + name + u'Rels(object)', flatten(tys))]
    def Product(self, name, fs):
        return [py.Statement(u'# product ' + name)]
    def Sum(self, name, attrs, con, cons):
        return flatten([con, flatten(cons)])
    def Con(self, tag, args):
        return ([py.Statement(tag + u' = {}'), py.Compound(u'def make' + tag + u'(self, ' + u', '.join(args) + u')', [py.Statement(u'rv = make()'), py.Statement(u'self.' + tag + u'[rv, ' + u', '.join(args) + u'] = None'), py.Ret(u'rv')])]) if args else ([py.Statement(tag + u' = make()')])
    def Option(self, ty, name):
        return name
    def Sequence(self, ty, name):
        return name
    def Id(self, ty, name):
        return name
zephyr = zephyrFunctor()
class rulesRels(object):
    IgnorePatt = make()
    VarPatt = {}
    def makeVarPatt(self, n):
        rv = make()
        self.VarPatt[rv, n] = None
        return rv
    StrPatt = {}
    def makeStrPatt(self, s):
        rv = make()
        self.StrPatt[rv, s] = None
        return rv
    StructPatt = {}
    def makeStructPatt(self, ns, func, vars):
        rv = make()
        self.StructPatt[rv, ns, func, vars] = None
        return rv
    ListPatt = {}
    def makeListPatt(self, ps):
        rv = make()
        self.ListPatt[rv, ps] = None
        return rv
    ListHeadPatt = {}
    def makeListHeadPatt(self, head, ps):
        rv = make()
        self.ListHeadPatt[rv, head, ps] = None
        return rv
    ListTailPatt = {}
    def makeListTailPatt(self, tail, ps):
        rv = make()
        self.ListTailPatt[rv, tail, ps] = None
        return rv
    ListMidPatt = {}
    def makeListMidPatt(self, head, tail, ps):
        rv = make()
        self.ListMidPatt[rv, head, tail, ps] = None
        return rv
    VarProd = {}
    def makeVarProd(self, name):
        rv = make()
        self.VarProd[rv, name] = None
        return rv
    ConstProd = {}
    def makeConstProd(self, name):
        rv = make()
        self.ConstProd[rv, name] = None
        return rv
    StrProd = {}
    def makeStrProd(self, s):
        rv = make()
        self.StrProd[rv, s] = None
        return rv
    CharProd = {}
    def makeCharProd(self, n):
        rv = make()
        self.CharProd[rv, n] = None
        return rv
    StructProd = {}
    def makeStructProd(self, ns, func, ps):
        rv = make()
        self.StructProd[rv, ns, func, ps] = None
        return rv
    ListProd = {}
    def makeListProd(self, ps):
        rv = make()
        self.ListProd[rv, ps] = None
        return rv
    ListHeadProd = {}
    def makeListHeadProd(self, head, ps):
        rv = make()
        self.ListHeadProd[rv, head, ps] = None
        return rv
    ListTailProd = {}
    def makeListTailProd(self, tail, ps):
        rv = make()
        self.ListTailProd[rv, tail, ps] = None
        return rv
    ListMidProd = {}
    def makeListMidProd(self, head, tail, ps):
        rv = make()
        self.ListMidProd[rv, head, tail, ps] = None
        return rv
    FlattenOp = {}
    def makeFlattenOp(self, p):
        rv = make()
        self.FlattenOp[rv, p] = None
        return rv
    LengthOp = {}
    def makeLengthOp(self, p):
        rv = make()
        self.LengthOp[rv, p] = None
        return rv
    JoinOp = {}
    def makeJoinOp(self, s, p):
        rv = make()
        self.JoinOp[rv, s, p] = None
        return rv
    ConcatOp = {}
    def makeConcatOp(self, ps):
        rv = make()
        self.ConcatOp[rv, ps] = None
        return rv
    Rewrite = {}
    def makeRewrite(self, name, root, prods):
        rv = make()
        self.Rewrite[rv, name, root, prods] = None
        return rv
    Let = {}
    def makeLet(self, name, p):
        rv = make()
        self.Let[rv, name, p] = None
        return rv
class rulesFunctor(object):
    def IgnorePatt(self):
        return u'_'
    def VarPatt(self, n):
        return n
    def StrPatt(self, s):
        return unichr(39) + s + unichr(39)
    def StructPatt(self, ns, func, vars):
        return ns + u'.' + func + u'(' + u', '.join(vars) + u')'
    def ListPatt(self, ps):
        return u', '.join(ps)
    def ListHeadPatt(self, head, ps):
        return u'listhead' + head + u', '.join(ps)
    def ListTailPatt(self, tail, ps):
        return u'listtail' + tail + u', '.join(ps)
    def ListMidPatt(self, head, tail, ps):
        return u'listmid' + head + tail + u', '.join(ps)
    def VarProd(self, name):
        return u'v' + name
    def ConstProd(self, name):
        return u'const' + name
    def StrProd(self, s):
        return u'makeStr(' + unichr(39) + s + unichr(39) + u')'
    def CharProd(self, n):
        return u'makeStr(unichr(' + n + u'))'
    def StructProd(self, ns, func, ps):
        return ns + u'Rels().make' + func + u'(' + u', '.join(ps) + u')'
    def ListProd(self, ps):
        return (u'makeList([' + u', '.join(ps) + u'])') if ps else (u'emptyList')
    def ListHeadProd(self, head, ps):
        return u'makeList(findList(' + head + u') + [' + u', '.join(ps) + u'])'
    def ListTailProd(self, tail, ps):
        return u'listtail' + tail + u', '.join(ps)
    def ListMidProd(self, head, tail, ps):
        return u'listmid' + head + tail + u', '.join(ps)
    def FlattenOp(self, p):
        return u'flattenList(' + p + u')'
    def LengthOp(self, p):
        return u'makeStr(str(len(findStr(' + p + u'))).encode("utf-8"))'
    def JoinOp(self, s, p):
        return u'makeStr("' + s + u'".join([findStr(x) for x in findList(' + p + u')]))'
    def ConcatOp(self, ps):
        return u'makeStr(findStr(' + u') + findStr('.join(ps) + u'))'
    def Rewrite(self, name, root, prods):
        return [py.Statement(u'@rewrite'), py.Compound(u'def ' + name + u'()', [py.Statement(u'count = 0'), py.Statement(u'# ' + root), py.Statement(u'# unify(vRoot, ' + u', '.join(prods) + u')'), py.Statement(u'# count += 1'), py.Ret(u'count')])]
    def Let(self, name, p):
        return [py.Statement(u'const' + name + u' = ' + p)]
rules = rulesFunctor()
class charRels(object):
    Any = make()
    Exactly = {}
    def makeExactly(self, c):
        rv = make()
        self.Exactly[rv, c] = None
        return rv
    Range = {}
    def makeRange(self, l, u):
        rv = make()
        self.Range[rv, l, u] = None
        return rv
    Call = {}
    def makeCall(self, n):
        rv = make()
        self.Call[rv, n] = None
        return rv
    Complement = {}
    def makeComplement(self, s):
        rv = make()
        self.Complement[rv, s] = None
        return rv
    Either = {}
    def makeEither(self, l, r):
        rv = make()
        self.Either[rv, l, r] = None
        return rv
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
@rewrite
def pyStatement():
    count = 0
    # py.Statement(L)
    # unify(vRoot, makeList([builtinRels().makeLine(vL)]))
    # count += 1
    return count
@rewrite
def pyRet():
    count = 0
    # py.Ret(E)
    # unify(vRoot, makeList([builtinRels().makeLine(makeStr(findStr(makeStr('return ')) + findStr(vE)))]))
    # count += 1
    return count
@rewrite
def pyRaiseIf():
    count = 0
    # py.RaiseIf(T)
    # unify(vRoot, makeList([builtinRels().makeLine(makeStr(findStr(makeStr('if ')) + findStr(vT) + findStr(makeStr(': raise ParseError()'))))]))
    # count += 1
    return count
@rewrite
def pyCompPass():
    count = 0
    # py.Compound(H, )
    # unify(vRoot, makeList([builtinRels().makeLine(makeStr(findStr(vH) + findStr(makeStr(': pass'))))]))
    # count += 1
    return count
@rewrite
def pyCompBlock():
    count = 0
    # py.Compound(H, B)
    # unify(vRoot, makeList([builtinRels().makeLine(makeStr(findStr(vH) + findStr(makeStr(':')))), builtinRels().makeBlock(vB)]))
    # count += 1
    return count
@rewrite
def pyCondEmpty():
    count = 0
    # py.Conditional(T, )
    # unify(vRoot, emptyList)
    # count += 1
    return count
@rewrite
def pyCondBlock():
    count = 0
    # py.Conditional(T, B)
    # unify(vRoot, makeList([builtinRels().makeLine(makeStr(findStr(makeStr('if ')) + findStr(vT) + findStr(makeStr(':')))), builtinRels().makeBlock(vB)]))
    # count += 1
    return count
@rewrite
def pyHandEmpty():
    count = 0
    # py.Handler(B, )
    # unify(vRoot, emptyList)
    # count += 1
    return count
@rewrite
def pyHandBlock():
    count = 0
    # py.Handler(B, H)
    # unify(vRoot, makeList([builtinRels().makeLine(makeStr('try:')), builtinRels().makeBlock(vB), builtinRels().makeLine(makeStr('except ParseError:')), builtinRels().makeBlock(vH)]))
    # count += 1
    return count
@rewrite
def prodCon():
    count = 0
    # production.Con(T, C, Ps)
    # unify(vRoot, makeStr(findStr(vT) + findStr(makeStr('.')) + findStr(vC) + findStr(makeStr('(')) + findStr(makeStr(", ".join([findStr(x) for x in findList(vPs)]))) + findStr(makeStr(')'))))
    # count += 1
    return count
@rewrite
def prodPlus():
    count = 0
    # production.PlusMany(Ps)
    # unify(vRoot, makeStr(" + ".join([findStr(x) for x in findList(vPs)])))
    # count += 1
    return count
@rewrite
def prodMod():
    count = 0
    # production.Mod(L, R)
    # unify(vRoot, makeStr(findStr(vR) + findStr(makeStr('.join(')) + findStr(vL) + findStr(makeStr(')'))))
    # count += 1
    return count
@rewrite
def prodFlat():
    count = 0
    # production.Flatten(L)
    # unify(vRoot, makeStr(findStr(makeStr('flatten(')) + findStr(vL) + findStr(makeStr(')'))))
    # count += 1
    return count
@rewrite
def prodName():
    count = 0
    # production.Name(S)
    # unify(vRoot, vS)
    # count += 1
    return count
@rewrite
def prodStr():
    count = 0
    # production.String(S)
    # unify(vRoot, makeStr(findStr(makeStr('u')) + findStr(makeStr(unichr(39))) + findStr(vS) + findStr(makeStr(unichr(39)))))
    # count += 1
    return count
@rewrite
def prodList():
    count = 0
    # production.List(Ps)
    # unify(vRoot, makeStr(findStr(makeStr('[')) + findStr(makeStr(", ".join([findStr(x) for x in findList(vPs)]))) + findStr(makeStr(']'))))
    # count += 1
    return count
@rewrite
def prodLen():
    count = 0
    # production.Length(S)
    # unify(vRoot, makeStr(findStr(makeStr('str(len(')) + findStr(vS) + findStr(makeStr(')).decode("utf-8")'))))
    # count += 1
    return count
@rewrite
def prodChr():
    count = 0
    # production.Chr(N)
    # unify(vRoot, makeStr(findStr(makeStr('unichr(')) + findStr(vN) + findStr(makeStr(')'))))
    # count += 1
    return count
@rewrite
def prodCond():
    count = 0
    # production.Cond(T, C, O)
    # unify(vRoot, makeStr(findStr(makeStr('(')) + findStr(vC) + findStr(makeStr(') if ')) + findStr(vT) + findStr(makeStr(' else (')) + findStr(vO) + findStr(makeStr(')'))))
    # count += 1
    return count
@rewrite
def pegNamePatt():
    count = 0
    # peg.NamePatt(Name)
    # unify(vRoot, vName)
    # count += 1
    return count
@rewrite
def pegNamePatt():
    count = 0
    # peg.TuplePatt(Ps)
    # unify(vRoot, makeStr(findStr(makeStr('(')) + findStr(makeStr(", ".join([findStr(x) for x in findList(vPs)]))) + findStr(makeStr(')'))))
    # count += 1
    return count
constsave = pyRels().makeStatement(makeStr('st.append(i)'))
constbackup = pyRels().makeStatement(makeStr('i = st.pop()'))
constboundcheck = pyRels().makeRaiseIf(makeStr('i >= len(self.s)'))
constskipws = pyRels().makeStatement(makeStr('while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1'))
@rewrite
def pegSeq():
    count = 0
    # peg.Sequence(Es)
    # unify(vRoot, flattenList(vEs))
    # count += 1
    return count
@rewrite
def pegCap():
    count = 0
    # peg.Capture(E, P)
    # unify(vRoot, makeList(findList(E) + [pyRels().makeStatement(makeStr(findStr(vP) + findStr(makeStr(' = rv'))))]))
    # count += 1
    return count
@rewrite
def pegProd():
    count = 0
    # peg.Production(E, P)
    # unify(vRoot, makeList(findList(E) + [pyRels().makeStatement(makeStr(findStr(makeStr('rv = ')) + findStr(vP)))]))
    # count += 1
    return count
@rewrite
def pegCall():
    count = 0
    # peg.Call(S)
    # unify(vRoot, makeList([pyRels().makeStatement(makeStr(findStr(makeStr('i, rv = self.parse')) + findStr(vS) + findStr(makeStr('(i)'))))]))
    # count += 1
    return count
@rewrite
def pegChoice():
    count = 0
    # peg.Choice(L, R)
    # unify(vRoot, makeList([constsave, pyRels().makeHandler(vL, listtailRconstbackup)]))
    # count += 1
    return count
@rewrite
def pegToken():
    count = 0
    # peg.Token(S)
    # unify(vRoot, makeList([constskipws, constboundcheck, pyRels().makeRaiseIf(makeStr(findStr(makeStr('self.s[i:i + ')) + findStr(makeStr(str(len(findStr(vS))).encode("utf-8"))) + findStr(makeStr('] != u"')) + findStr(vS) + findStr(makeStr('"')))), pyRels().makeStatement(makeStr(findStr(makeStr('self.lastMatch.append((u"TOKEN ')) + findStr(vS) + findStr(makeStr('", i, i + ')) + findStr(makeStr(str(len(findStr(vS))).encode("utf-8"))) + findStr(makeStr('))')))), pyRels().makeStatement(makeStr(findStr(makeStr('rv = u"')) + findStr(vS) + findStr(makeStr('"; i += ')) + findStr(makeStr(str(len(findStr(vS))).encode("utf-8")))))]))
    # count += 1
    return count
@rewrite
def pegAny():
    count = 0
    # peg.Any(E)
    # unify(vRoot, makeList([pyRels().makeStatement(makeStr('rvs = []')), pyRels().makeCompound(makeStr('while True'), makeList([constsave, pyRels().makeHandler(makeList(findList(E) + [pyRels().makeStatement(makeStr('rvs.append(rv)'))]), makeList([constbackup, pyRels().makeStatement(makeStr('break'))]))])), pyRels().makeStatement(makeStr('rv = rvs'))]))
    # count += 1
    return count
@rewrite
def pegSome():
    count = 0
    # peg.Some(E)
    # unify(vRoot, flattenList(makeList([pegRels().makeAny(vE), makeList([pyRels().makeRaiseIf(makeStr('not rv'))])])))
    # count += 1
    return count
@rewrite
def pegMaybe():
    count = 0
    # peg.Maybe(E)
    # unify(vRoot, makeList([constsave, pyRels().makeHandler(vE, makeList([pyRels().makeStatement(makeStr('rv = peg.Null()')), constbackup]))]))
    # count += 1
    return count
@rewrite
def pegPos():
    count = 0
    # peg.Positive(E)
    # unify(vRoot, makeList([constsave, pyRels().makeHandler(makeList(findList(E) + [pyRels().makeStatement(makeStr('rv = True'))]), makeList([pyRels().makeStatement(makeStr('rv = False'))])), constbackup, pyRels().makeRaiseIf(makeStr('not rv'))]))
    # count += 1
    return count
@rewrite
def pegNeg():
    count = 0
    # peg.Negative(E)
    # unify(vRoot, makeList([constsave, pyRels().makeHandler(makeList(findList(E) + [pyRels().makeStatement(makeStr('rv = True'))]), makeList([pyRels().makeStatement(makeStr('rv = False'))])), constbackup, pyRels().makeRaiseIf(makeStr('rv'))]))
    # count += 1
    return count
@rewrite
def zSig():
    count = 0
    # zephyr.Signature(N, T)
    # unify(vRoot, makeList([pyRels().makeCompound(makeStr(findStr(makeStr('class ')) + findStr(vN) + findStr(makeStr('Rels(object)'))), flattenList(vT))]))
    # count += 1
    return count
@rewrite
def zProd():
    count = 0
    # zephyr.Product(N, Fs)
    # unify(vRoot, makeList([pyRels().makeStatement(makeStr(findStr(makeStr('# product ')) + findStr(vN)))]))
    # count += 1
    return count
@rewrite
def zSum():
    count = 0
    # zephyr.Sum(N, A, C, Cs)
    # unify(vRoot, flattenList(makeList([constcon, flattenList(constcons)])))
    # count += 1
    return count
@rewrite
def zConT():
    count = 0
    # zephyr.Con(T, )
    # unify(vRoot, makeList([pyRels().makeStatement(makeStr(findStr(vT) + findStr(makeStr(' = make()'))))]))
    # count += 1
    return count
@rewrite
def zConF():
    count = 0
    # zephyr.Con(T, A)
    # unify(vRoot, makeList([pyRels().makeStatement(makeStr(findStr(vT) + findStr(makeStr(' = {}')))), pyRels().makeCompound(makeStr(findStr(makeStr('def make')) + findStr(vT) + findStr(makeStr('(self, ')) + findStr(makeStr(", ".join([findStr(x) for x in findList(vA)]))) + findStr(makeStr(')'))), makeList([pyRels().makeStatement(makeStr('rv = make()')), pyRels().makeStatement(makeStr(findStr(makeStr('self.')) + findStr(vT) + findStr(makeStr('[rv, ')) + findStr(makeStr(", ".join([findStr(x) for x in findList(vA)]))) + findStr(makeStr('] = None')))), pyRels().makeRet(makeStr('rv'))]))]))
    # count += 1
    return count
@rewrite
def zOpt():
    count = 0
    # zephyr.Option(T, N)
    # unify(vRoot, vN)
    # count += 1
    return count
@rewrite
def zSeq():
    count = 0
    # zephyr.Sequence(T, N)
    # unify(vRoot, vN)
    # count += 1
    return count
@rewrite
def zId():
    count = 0
    # zephyr.Id(T, N)
    # unify(vRoot, vN)
    # count += 1
    return count
@rewrite
def charAny():
    count = 0
    # char.Any()
    # unify(vRoot, makeStr('True'))
    # count += 1
    return count
@rewrite
def charExactly():
    count = 0
    # char.Exactly(C)
    # unify(vRoot, makeStr(findStr(makeStr('c == ')) + findStr(vC)))
    # count += 1
    return count
@rewrite
def charRange():
    count = 0
    # char.Range(L, U)
    # unify(vRoot, makeStr(findStr(vL) + findStr(makeStr(' <= c <= ')) + findStr(vU)))
    # count += 1
    return count
@rewrite
def charCall():
    count = 0
    # char.Call(N)
    # unify(vRoot, makeStr(findStr(makeStr('self.cls')) + findStr(vN) + findStr(makeStr('(c)'))))
    # count += 1
    return count
@rewrite
def charComp():
    count = 0
    # char.Complement(S)
    # unify(vRoot, makeStr(findStr(makeStr('not (')) + findStr(vS) + findStr(makeStr(')'))))
    # count += 1
    return count
@rewrite
def charEither():
    count = 0
    # char.Either(L, R)
    # unify(vRoot, makeStr(findStr(makeStr('(')) + findStr(vL) + findStr(makeStr(') or (')) + findStr(vR) + findStr(makeStr(')'))))
    # count += 1
    return count
@rewrite
def rPattIg():
    count = 0
    # rules.IgnorePatt()
    # unify(vRoot, makeStr('_'))
    # count += 1
    return count
@rewrite
def rPattV():
    count = 0
    # rules.VarPatt(N)
    # unify(vRoot, vN)
    # count += 1
    return count
@rewrite
def rPattS():
    count = 0
    # rules.StrPatt(S)
    # unify(vRoot, makeStr(findStr(makeStr(unichr(39))) + findStr(vS) + findStr(makeStr(unichr(39)))))
    # count += 1
    return count
@rewrite
def rPattSt():
    count = 0
    # rules.StructPatt(Ns, F, Vs)
    # unify(vRoot, makeStr(findStr(vNs) + findStr(makeStr('.')) + findStr(vF) + findStr(makeStr('(')) + findStr(makeStr(", ".join([findStr(x) for x in findList(vVs)]))) + findStr(makeStr(')'))))
    # count += 1
    return count
@rewrite
def rPattL():
    count = 0
    # rules.ListPatt(Ps)
    # unify(vRoot, makeStr(", ".join([findStr(x) for x in findList(vPs)])))
    # count += 1
    return count
@rewrite
def rPattLH():
    count = 0
    # rules.ListHeadPatt(H, Ps)
    # unify(vRoot, makeStr(findStr(makeStr('listhead')) + findStr(vH) + findStr(makeStr(", ".join([findStr(x) for x in findList(vPs)])))))
    # count += 1
    return count
@rewrite
def rPattLT():
    count = 0
    # rules.ListTailPatt(T, Ps)
    # unify(vRoot, makeStr(findStr(makeStr('listtail')) + findStr(vT) + findStr(makeStr(", ".join([findStr(x) for x in findList(vPs)])))))
    # count += 1
    return count
@rewrite
def rPattLM():
    count = 0
    # rules.ListMidPatt(H, T, Ps)
    # unify(vRoot, makeStr(findStr(makeStr('listmid')) + findStr(vH) + findStr(vT) + findStr(makeStr(", ".join([findStr(x) for x in findList(vPs)])))))
    # count += 1
    return count
@rewrite
def rProdV():
    count = 0
    # rules.VarProd(Name)
    # unify(vRoot, makeStr(findStr(makeStr('v')) + findStr(vName)))
    # count += 1
    return count
@rewrite
def rProdC():
    count = 0
    # rules.ConstProd(Name)
    # unify(vRoot, makeStr(findStr(makeStr('const')) + findStr(vName)))
    # count += 1
    return count
@rewrite
def rProdS():
    count = 0
    # rules.StrProd(S)
    # unify(vRoot, makeStr(findStr(makeStr('makeStr(')) + findStr(makeStr(unichr(39))) + findStr(vS) + findStr(makeStr(unichr(39))) + findStr(makeStr(')'))))
    # count += 1
    return count
@rewrite
def rProdCh():
    count = 0
    # rules.CharProd(N)
    # unify(vRoot, makeStr(findStr(makeStr('makeStr(unichr(')) + findStr(vN) + findStr(makeStr('))'))))
    # count += 1
    return count
@rewrite
def rProdSt():
    count = 0
    # rules.StructProd(Ns, F, Ps)
    # unify(vRoot, makeStr(findStr(vNs) + findStr(makeStr('Rels().make')) + findStr(vF) + findStr(makeStr('(')) + findStr(makeStr(", ".join([findStr(x) for x in findList(constps)]))) + findStr(makeStr(')'))))
    # count += 1
    return count
@rewrite
def rProdL():
    count = 0
    # rules.ListProd(Ps)
    # unify(vRoot, makeStr(", ".join([findStr(x) for x in findList(constps)])))
    # count += 1
    return count
@rewrite
def rProdLH():
    count = 0
    # rules.ListHeadProd(H, Ps)
    # unify(vRoot, makeStr(findStr(makeStr('makeList(findList(')) + findStr(vH) + findStr(makeStr(') + [')) + findStr(makeStr(", ".join([findStr(x) for x in findList(vPs)]))) + findStr(makeStr('])'))))
    # count += 1
    return count
@rewrite
def rProdLT():
    count = 0
    # rules.ListTailProd(T, Ps)
    # unify(vRoot, makeStr(findStr(makeStr('listtail')) + findStr(vT) + findStr(makeStr(", ".join([findStr(x) for x in findList(vPs)])))))
    # count += 1
    return count
@rewrite
def rProdLM():
    count = 0
    # rules.ListMidProd(H, T, Ps)
    # unify(vRoot, makeStr(findStr(makeStr('listmid')) + findStr(vH) + findStr(vT) + findStr(makeStr(", ".join([findStr(x) for x in findList(vPs)])))))
    # count += 1
    return count
@rewrite
def rProdOF():
    count = 0
    # rules.FlattenOp(P)
    # unify(vRoot, makeStr(findStr(makeStr('flattenList(')) + findStr(vP) + findStr(makeStr(')'))))
    # count += 1
    return count
@rewrite
def rProdOL():
    count = 0
    # rules.LengthOp(P)
    # unify(vRoot, makeStr(findStr(makeStr('makeStr(str(len(findStr(')) + findStr(vP) + findStr(makeStr('))).encode("utf-8"))'))))
    # count += 1
    return count
@rewrite
def rProdOJ():
    count = 0
    # rules.JoinOp(S, P)
    # unify(vRoot, makeStr(findStr(makeStr('makeStr("')) + findStr(vS) + findStr(makeStr('".join([findStr(x) for x in findList(')) + findStr(vP) + findStr(makeStr(')]))'))))
    # count += 1
    return count
@rewrite
def rProdOC():
    count = 0
    # rules.ConcatOp(Ps)
    # unify(vRoot, makeStr(findStr(makeStr('makeStr(findStr(')) + findStr(makeStr(") + findStr(".join([findStr(x) for x in findList(vPs)]))) + findStr(makeStr('))'))))
    # count += 1
    return count
@rewrite
def rRule():
    count = 0
    # rules.Rewrite(Name, Root, Ps)
    # unify(vRoot, makeList([pyRels().makeCompound(makeStr(findStr(makeStr('def ')) + findStr(vName) + findStr(makeStr('(vRoot)'))), makeList([pyRels().makeStatement(makeStr('count = 0')), pyRels().makeStatement(makeStr(findStr(makeStr('# ')) + findStr(vRoot))), pyRels().makeStatement(makeStr(findStr(makeStr('# unify(vRoot, ')) + findStr(makeStr(", ".join([findStr(x) for x in findList(vPs)]))) + findStr(makeStr(')')))), pyRels().makeStatement(makeStr('# count += 1')), pyRels().makeRet(makeStr('count'))]))]))
    # count += 1
    return count
@rewrite
def rLet():
    count = 0
    # rules.Let(Name, P)
    # unify(vRoot, makeList([pyRels().makeStatement(makeStr(findStr(makeStr('const')) + findStr(vName) + findStr(makeStr(' = ')) + findStr(vP)))]))
    # count += 1
    return count
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
    def clsEllipsis(self, c):
        return c == 8230
    def parseWS(self, i):
        if i >= len(self.s): raise ParseError()
        start = i
        while i < len(self.s) and self.clsWhitespace(ord(self.s[i])): i += 1
        rv = self.s[start:i]
        self.lastMatch.append((u"TOKEN WS", start, i))
        return i, rv
    def parseNumber(self, i):
        if i >= len(self.s): raise ParseError()
        start = i
        if i >= len(self.s) or not self.clsDigit(ord(self.s[i])): raise ParseError()
        while i < len(self.s) and self.clsDigit(ord(self.s[i])): i += 1
        rv = self.s[start:i]
        self.lastMatch.append((u"TOKEN Number", start, i))
        return i, rv
    def parseId(self, i):
        if i >= len(self.s): raise ParseError()
        start = i
        if i >= len(self.s) or not self.clsAlpha(ord(self.s[i])): raise ParseError()
        i += 1
        while i < len(self.s) and self.clsAlphanumeric(ord(self.s[i])): i += 1
        rv = self.s[start:i]
        self.lastMatch.append((u"TOKEN Id", start, i))
        return i, rv
    def parsePVar(self, i):
        if i >= len(self.s): raise ParseError()
        start = i
        if i >= len(self.s) or not self.clsUpper(ord(self.s[i])): raise ParseError()
        i += 1
        while i < len(self.s) and self.clsAlphanumeric(ord(self.s[i])): i += 1
        rv = self.s[start:i]
        self.lastMatch.append((u"TOKEN PVar", start, i))
        return i, rv
    def parsePConst(self, i):
        if i >= len(self.s): raise ParseError()
        start = i
        if i >= len(self.s) or not self.clsLower(ord(self.s[i])): raise ParseError()
        while i < len(self.s) and self.clsLower(ord(self.s[i])): i += 1
        rv = self.s[start:i]
        self.lastMatch.append((u"TOKEN PConst", start, i))
        return i, rv
    def parseZTId(self, i):
        if i >= len(self.s): raise ParseError()
        start = i
        if i >= len(self.s) or not self.clsLower(ord(self.s[i])): raise ParseError()
        i += 1
        while i < len(self.s) and self.clsAlphanumeric(ord(self.s[i])): i += 1
        rv = self.s[start:i]
        self.lastMatch.append((u"TOKEN ZTId", start, i))
        return i, rv
    def parseZCId(self, i):
        if i >= len(self.s): raise ParseError()
        start = i
        if i >= len(self.s) or not self.clsUpper(ord(self.s[i])): raise ParseError()
        i += 1
        while i < len(self.s) and self.clsAlphanumeric(ord(self.s[i])): i += 1
        rv = self.s[start:i]
        self.lastMatch.append((u"TOKEN ZCId", start, i))
        return i, rv
    def parseQuote(self, i):
        if i >= len(self.s): raise ParseError()
        start = i
        if i >= len(self.s) or not self.clsQuote(ord(self.s[i])): raise ParseError()
        i += 1
        rv = self.s[start:i]
        self.lastMatch.append((u"TOKEN Quote", start, i))
        return i, rv
    def parseQuoted(self, i):
        if i >= len(self.s): raise ParseError()
        start = i
        while i < len(self.s) and self.clsQuoted(ord(self.s[i])): i += 1
        rv = self.s[start:i]
        self.lastMatch.append((u"TOKEN Quoted", start, i))
        return i, rv
    def parseEllipsis(self, i):
        if i >= len(self.s): raise ParseError()
        start = i
        if i >= len(self.s) or not self.clsEllipsis(ord(self.s[i])): raise ParseError()
        i += 1
        rv = self.s[start:i]
        self.lastMatch.append((u"TOKEN Ellipsis", start, i))
        return i, rv
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
        rv = zephyr.Signature(name, flatten(tys))
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
            rv = [zephyr.Product(name, fs)]
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
                rv = [zephyr.Sum(name, attrs, con, cons)]
            except ParseError:
                i = st.pop()
                rv = [zephyr.Sum(name, [], con, cons)]
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
        rv = flatten([[f], fs])
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
                st.append(i)
                try:
                    i, rv = self.parseCHRULE(i)
                except ParseError:
                    i = st.pop()
                    i, rv = self.parseCHLET(i)
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
        i, rv = self.parseWS(i)
        i, rv = self.parseCPATT(i)
        root = rv
        if i >= len(self.s): raise ParseError()
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError()
        if self.s[i:i + 3] != u"==>": raise ParseError()
        self.lastMatch.append((u"TOKEN ==>", i, i + 3))
        rv = u"==>"; i += 3
        i, rv = self.parseCPRODS(i)
        prods = rv
        if i >= len(self.s): raise ParseError()
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError()
        if self.s[i:i + 1] != u";": raise ParseError()
        self.lastMatch.append((u"TOKEN ;", i, i + 1))
        rv = u";"; i += 1
        rv = rules.Rewrite(name, root, prods)
        return i, rv
    @cached
    def parseCHLET(self, i):
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
        i, rv = self.parseCPROD1(i)
        p = rv
        if i >= len(self.s): raise ParseError()
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError()
        if self.s[i:i + 1] != u";": raise ParseError()
        self.lastMatch.append((u"TOKEN ;", i, i + 1))
        rv = u";"; i += 1
        rv = rules.Let(name, p)
        return i, rv
    @cached
    def parseCPATTS(self, i):
        st = []
        i, rv = self.parseWS(i)
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
                i, rv = self.parseWS(i)
                i, rv = self.parseCPATT(i)
                rvs.append(rv)
            except ParseError:
                i = st.pop()
                break
        rv = rvs
        ps = rv
        rv = flatten([[p], ps])
        return i, rv
    @cached
    def parsePATTDOTS(self, i):
        st = []
        i, rv = self.parseWS(i)
        i, rv = self.parsePVar(i)
        n = rv
        i, rv = self.parseEllipsis(i)
        rv = n
        return i, rv
    @cached
    def parseCPATT(self, i):
        st = []
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
                if i >= len(self.s): raise ParseError()
                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                if i >= len(self.s): raise ParseError()
                if self.s[i:i + 2] != u"[]": raise ParseError()
                self.lastMatch.append((u"TOKEN []", i, i + 2))
                rv = u"[]"; i += 2
                rv = rules.ListPatt([])
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
                    i, rv = self.parsePATTDOTS(i)
                    head = rv
                    if i >= len(self.s): raise ParseError()
                    while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                    if i >= len(self.s): raise ParseError()
                    if self.s[i:i + 1] != u",": raise ParseError()
                    self.lastMatch.append((u"TOKEN ,", i, i + 1))
                    rv = u","; i += 1
                    i, rv = self.parseCPATTS(i)
                    ps = rv
                    if i >= len(self.s): raise ParseError()
                    while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                    if i >= len(self.s): raise ParseError()
                    if self.s[i:i + 1] != u",": raise ParseError()
                    self.lastMatch.append((u"TOKEN ,", i, i + 1))
                    rv = u","; i += 1
                    i, rv = self.parsePATTDOTS(i)
                    tail = rv
                    if i >= len(self.s): raise ParseError()
                    while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                    if i >= len(self.s): raise ParseError()
                    if self.s[i:i + 1] != u"]": raise ParseError()
                    self.lastMatch.append((u"TOKEN ]", i, i + 1))
                    rv = u"]"; i += 1
                    rv = rules.ListMidPatt(head, tail, ps)
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
                        i, rv = self.parsePATTDOTS(i)
                        head = rv
                        if i >= len(self.s): raise ParseError()
                        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                        if i >= len(self.s): raise ParseError()
                        if self.s[i:i + 1] != u",": raise ParseError()
                        self.lastMatch.append((u"TOKEN ,", i, i + 1))
                        rv = u","; i += 1
                        i, rv = self.parseCPATTS(i)
                        ps = rv
                        if i >= len(self.s): raise ParseError()
                        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                        if i >= len(self.s): raise ParseError()
                        if self.s[i:i + 1] != u"]": raise ParseError()
                        self.lastMatch.append((u"TOKEN ]", i, i + 1))
                        rv = u"]"; i += 1
                        rv = rules.ListHeadPatt(head, ps)
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
                            i, rv = self.parseCPATTS(i)
                            ps = rv
                            if i >= len(self.s): raise ParseError()
                            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                            if i >= len(self.s): raise ParseError()
                            if self.s[i:i + 1] != u",": raise ParseError()
                            self.lastMatch.append((u"TOKEN ,", i, i + 1))
                            rv = u","; i += 1
                            i, rv = self.parsePATTDOTS(i)
                            tail = rv
                            if i >= len(self.s): raise ParseError()
                            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                            if i >= len(self.s): raise ParseError()
                            if self.s[i:i + 1] != u"]": raise ParseError()
                            self.lastMatch.append((u"TOKEN ]", i, i + 1))
                            rv = u"]"; i += 1
                            rv = rules.ListTailPatt(tail, ps)
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
                                i, rv = self.parseCPATTS(i)
                                ps = rv
                                if i >= len(self.s): raise ParseError()
                                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                if i >= len(self.s): raise ParseError()
                                if self.s[i:i + 1] != u"]": raise ParseError()
                                self.lastMatch.append((u"TOKEN ]", i, i + 1))
                                rv = u"]"; i += 1
                                rv = rules.ListPatt(ps)
                            except ParseError:
                                i = st.pop()
                                st.append(i)
                                try:
                                    i, rv = self.parseSTRING(i)
                                    s = rv
                                    rv = rules.StrPatt(s)
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
                                        rv = rules.StructPatt(ns, func, ps)
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
                                            rv = rules.StructPatt(ns, func, [])
                                        except ParseError:
                                            i = st.pop()
                                            i, rv = self.parsePVar(i)
                                            name = rv
                                            st.append(i)
                                            try:
                                                i, rv = self.parseEllipsis(i)
                                                rv = True
                                            except ParseError:
                                                rv = False
                                            i = st.pop()
                                            if rv: raise ParseError()
                                            rv = rules.VarPatt(name)
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
        rv = flatten([[p], ps])
        return i, rv
    @cached
    def parseCPROD1(self, i):
        st = []
        i, rv = self.parseWS(i)
        i, rv = self.parseCPROD2(i)
        p = rv
        rvs = []
        while True:
            st.append(i)
            try:
                i, rv = self.parseWS(i)
                i, rv = self.parseCPROD2(i)
                rvs.append(rv)
            except ParseError:
                i = st.pop()
                break
        rv = rvs
        ps = rv
        rv = (rules.ConcatOp(flatten([[p], ps]))) if ps else (p)
        return i, rv
    @cached
    def parseCPROD2(self, i):
        st = []
        st.append(i)
        try:
            i, rv = self.parseSTRING(i)
            s = rv
            rv = rules.StrProd(s)
        except ParseError:
            i = st.pop()
            st.append(i)
            try:
                i, rv = self.parseNumber(i)
                n = rv
                rv = rules.CharProd(n)
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
                    i, rv = self.parseCPROD2(i)
                    p = rv
                    rv = rules.LengthOp(p)
                except ParseError:
                    i = st.pop()
                    st.append(i)
                    try:
                        if i >= len(self.s): raise ParseError()
                        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                        if i >= len(self.s): raise ParseError()
                        if self.s[i:i + 1] != u"*": raise ParseError()
                        self.lastMatch.append((u"TOKEN *", i, i + 1))
                        rv = u"*"; i += 1
                        i, rv = self.parseCPROD2(i)
                        p = rv
                        rv = rules.FlattenOp(p)
                    except ParseError:
                        i = st.pop()
                        st.append(i)
                        try:
                            if i >= len(self.s): raise ParseError()
                            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                            if i >= len(self.s): raise ParseError()
                            if self.s[i:i + 2] != u"*(": raise ParseError()
                            self.lastMatch.append((u"TOKEN *(", i, i + 2))
                            rv = u"*("; i += 2
                            i, rv = self.parseCPROD1(i)
                            p = rv
                            if i >= len(self.s): raise ParseError()
                            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                            if i >= len(self.s): raise ParseError()
                            if self.s[i:i + 1] != u")": raise ParseError()
                            self.lastMatch.append((u"TOKEN )", i, i + 1))
                            rv = u")"; i += 1
                            rv = rules.FlattenOp(p)
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
                                i, rv = self.parseCPROD1(i)
                                p = rv
                                if i >= len(self.s): raise ParseError()
                                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                if i >= len(self.s): raise ParseError()
                                if self.s[i:i + 1] != u")": raise ParseError()
                                self.lastMatch.append((u"TOKEN )", i, i + 1))
                                rv = u")"; i += 1
                                rv = rules.StructProd(u'builtin', u'Line', [p])
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
                                    i, rv = self.parseCPROD1(i)
                                    p = rv
                                    if i >= len(self.s): raise ParseError()
                                    while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                    if i >= len(self.s): raise ParseError()
                                    if self.s[i:i + 1] != u")": raise ParseError()
                                    self.lastMatch.append((u"TOKEN )", i, i + 1))
                                    rv = u")"; i += 1
                                    rv = rules.StructProd(u'builtin', u'Block', [p])
                                except ParseError:
                                    i = st.pop()
                                    st.append(i)
                                    try:
                                        if i >= len(self.s): raise ParseError()
                                        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                        if i >= len(self.s): raise ParseError()
                                        if self.s[i:i + 6] != u".join(": raise ParseError()
                                        self.lastMatch.append((u"TOKEN .join(", i, i + 6))
                                        rv = u".join("; i += 6
                                        i, rv = self.parseCPROD1(i)
                                        p = rv
                                        if i >= len(self.s): raise ParseError()
                                        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                        if i >= len(self.s): raise ParseError()
                                        if self.s[i:i + 1] != u",": raise ParseError()
                                        self.lastMatch.append((u"TOKEN ,", i, i + 1))
                                        rv = u","; i += 1
                                        i, rv = self.parseSTRING(i)
                                        s = rv
                                        if i >= len(self.s): raise ParseError()
                                        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                        if i >= len(self.s): raise ParseError()
                                        if self.s[i:i + 1] != u")": raise ParseError()
                                        self.lastMatch.append((u"TOKEN )", i, i + 1))
                                        rv = u")"; i += 1
                                        rv = rules.JoinOp(s, p)
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
                                            rv = rules.ListProd([])
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
                                                i, rv = self.parsePATTDOTS(i)
                                                head = rv
                                                if i >= len(self.s): raise ParseError()
                                                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                                if i >= len(self.s): raise ParseError()
                                                if self.s[i:i + 1] != u",": raise ParseError()
                                                self.lastMatch.append((u"TOKEN ,", i, i + 1))
                                                rv = u","; i += 1
                                                i, rv = self.parseCPRODS(i)
                                                ps = rv
                                                if i >= len(self.s): raise ParseError()
                                                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                                if i >= len(self.s): raise ParseError()
                                                if self.s[i:i + 1] != u",": raise ParseError()
                                                self.lastMatch.append((u"TOKEN ,", i, i + 1))
                                                rv = u","; i += 1
                                                i, rv = self.parsePATTDOTS(i)
                                                tail = rv
                                                if i >= len(self.s): raise ParseError()
                                                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                                if i >= len(self.s): raise ParseError()
                                                if self.s[i:i + 1] != u"]": raise ParseError()
                                                self.lastMatch.append((u"TOKEN ]", i, i + 1))
                                                rv = u"]"; i += 1
                                                rv = rules.ListMidProd(head, tail, ps)
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
                                                    i, rv = self.parsePATTDOTS(i)
                                                    head = rv
                                                    if i >= len(self.s): raise ParseError()
                                                    while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                                    if i >= len(self.s): raise ParseError()
                                                    if self.s[i:i + 1] != u",": raise ParseError()
                                                    self.lastMatch.append((u"TOKEN ,", i, i + 1))
                                                    rv = u","; i += 1
                                                    i, rv = self.parseCPRODS(i)
                                                    ps = rv
                                                    if i >= len(self.s): raise ParseError()
                                                    while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                                    if i >= len(self.s): raise ParseError()
                                                    if self.s[i:i + 1] != u"]": raise ParseError()
                                                    self.lastMatch.append((u"TOKEN ]", i, i + 1))
                                                    rv = u"]"; i += 1
                                                    rv = rules.ListHeadProd(head, ps)
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
                                                        i, rv = self.parseCPRODS(i)
                                                        ps = rv
                                                        if i >= len(self.s): raise ParseError()
                                                        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                                        if i >= len(self.s): raise ParseError()
                                                        if self.s[i:i + 1] != u",": raise ParseError()
                                                        self.lastMatch.append((u"TOKEN ,", i, i + 1))
                                                        rv = u","; i += 1
                                                        i, rv = self.parsePATTDOTS(i)
                                                        tail = rv
                                                        if i >= len(self.s): raise ParseError()
                                                        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                                        if i >= len(self.s): raise ParseError()
                                                        if self.s[i:i + 1] != u"]": raise ParseError()
                                                        self.lastMatch.append((u"TOKEN ]", i, i + 1))
                                                        rv = u"]"; i += 1
                                                        rv = rules.ListTailProd(tail, ps)
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
                                                            i, rv = self.parseCPRODS(i)
                                                            ps = rv
                                                            if i >= len(self.s): raise ParseError()
                                                            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                                            if i >= len(self.s): raise ParseError()
                                                            if self.s[i:i + 1] != u"]": raise ParseError()
                                                            self.lastMatch.append((u"TOKEN ]", i, i + 1))
                                                            rv = u"]"; i += 1
                                                            rv = rules.ListProd(ps)
                                                        except ParseError:
                                                            i = st.pop()
                                                            st.append(i)
                                                            try:
                                                                i, rv = self.parsePVar(i)
                                                                name = rv
                                                                st.append(i)
                                                                try:
                                                                    i, rv = self.parseEllipsis(i)
                                                                    rv = True
                                                                except ParseError:
                                                                    rv = False
                                                                i = st.pop()
                                                                if rv: raise ParseError()
                                                                rv = rules.VarProd(name)
                                                            except ParseError:
                                                                i = st.pop()
                                                                st.append(i)
                                                                try:
                                                                    i, rv = self.parsePConst(i)
                                                                    name = rv
                                                                    st.append(i)
                                                                    try:
                                                                        i, rv = self.parseEllipsis(i)
                                                                        rv = True
                                                                    except ParseError:
                                                                        rv = False
                                                                    i = st.pop()
                                                                    if rv: raise ParseError()
                                                                    st.append(i)
                                                                    try:
                                                                        if i >= len(self.s): raise ParseError()
                                                                        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                                                        if i >= len(self.s): raise ParseError()
                                                                        if self.s[i:i + 1] != u".": raise ParseError()
                                                                        self.lastMatch.append((u"TOKEN .", i, i + 1))
                                                                        rv = u"."; i += 1
                                                                        rv = True
                                                                    except ParseError:
                                                                        rv = False
                                                                    i = st.pop()
                                                                    if rv: raise ParseError()
                                                                    rv = rules.ConstProd(name)
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
                                                                        rv = rules.StructProd(ns, func, ps)
                                                                    except ParseError:
                                                                        i = st.pop()
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
                                                                        rv = rules.StructProd(ns, func, [])
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
                                rv = production.List(flatten([[expr], exprs]))
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
        rv = flatten([lets, [py.Compound(u'class ' + name + u'Functor(object)', rules), py.Statement(name + u' = ' + name + u'Functor()')]])
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
        rv = flatten([[p], ps])
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
        rv = [py.Compound(u'def target(driver, *args)', [py.Statement(u'driver.exe_name = "' + name + u'".lower() + "c"'), py.Ret(u'main, None')]), py.Compound(u'class ' + name + u'Parser(object)', flatten([[py.Compound(u'def __init__(self, s)', [py.Statement(u'self.s = s; self.lastMatch = []')]), py.Compound(u'def parse(self)', [py.Ret(u'self.parse' + name + u'(0)')])], flatten(rules)])), py.Statement(u'MainParser = ' + name + u'Parser')]
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
        rv = [py.Compound(u'def parse' + name + u'(self, i)', flatten([[boundcheck, py.Statement(u'start = i')], flatten(scans), [py.Statement(u'rv = self.s[start:i]'), py.Statement(u'self.lastMatch.append((u"TOKEN ' + name + u'", start, i))'), py.Ret(u'i, rv')]]))]
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
        rv = [py.Statement(u'@cached'), py.Compound(u'def parse' + name + u'(self, i)', flatten([[py.Statement(u'st = []')], expr, [py.Ret(u'i, rv')]]))]
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
            rv = peg.TuplePatt(flatten([[p], ps]))
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
        rv = flatten([[py.Statement(u'from rpython.rlib.rfile import create_stdio'), py.Statement(u'from rpython.rlib.objectmodel import specialize'), py.Compound(u'class Result(object)', []), py.Compound(u'class Failed(Result)', []), py.Statement(u'failed = Failed()'), py.Compound(u'def cached(f, cacheCount=[0])', [py.Statement(u'attr = "t" + str(cacheCount[0]); cacheCount[0] += 1'), py.Statement(u'name = f.__name__'), py.Statement(u'uname = unicode(name)'), py.Compound(u'class CacheResult(Result)', [py.Statement(u'def __init__(self, i, rv): setattr(self, attr, (i, rv))')]), py.Statement(u'cache = {}'), py.Compound(u'def deco(self, i)', [py.Statement(u'key = i'), py.RaiseIf(u'key in cache and cache[key] is failed'), py.Statement(u'elif key in cache: return getattr(cache[key], attr)'), py.Statement(u'cache[key] = failed'), py.Statement(u'i, rv = f(self, i)'), py.Statement(u'cache[key] = CacheResult(i, rv)'), py.Statement(u'self.lastMatch.append((uname, key, i))'), py.Ret(u'i, rv')]), py.Statement(u'deco.__name__ = name'), py.Ret(u'deco')]), py.Statement(u'ruleNames = []'), py.Compound(u'def rewrite(f)', [py.Statement(u'ruleNames.append((f, f.__name__))'), py.Ret(u'f')]), py.Statement(u'@specialize.call_location()'), py.Compound(u'def flatten(xs)', [py.Statement(u'rv = []'), py.Statement(u'for x in xs: rv.extend(x)'), py.Ret(u'rv')]), py.Compound(u'def flattenList(i)', [py.Statement(u'rv = []'), py.Statement(u'for x in findList(i): rv.extend(findList(x))'), py.Ret(u'makeList(rv)')]), py.Compound(u'def intersect(l, r)', [py.Statement(u'rv = []'), py.Compound(u'for x in r', [py.Statement(u'if x in l: rv.append(x)')]), py.Ret(u'rv')]), py.Statement(u'uf = []'), py.Compound(u'def make()', [py.Statement(u'rv = len(uf)'), py.Statement(u'uf.append(rv)'), py.Ret(u'rv')]), py.Compound(u'def find(i)', [py.Statement(u'j = uf[i]'), py.Compound(u'while uf[j] != j', [py.Statement(u'uf[i], j, i = uf[j], uf[j], j')]), py.Ret(u'j')]), py.Compound(u'def union(i, j)', [py.Statement(u'i = find(i); j = find(j)'), py.Conditional(u'i != j', [py.Statement(u'uf[i] = j')]), py.Ret(u'j')]), py.Statement(u'regNone = make()'), py.Statement(u'interned = {}'), py.Compound(u'def makeStr(s)', [py.Statement(u'rv = make()'), py.Statement(u'interned[rv] = s'), py.Ret(u'rv')]), py.Statement(u'def findStr(i): return interned[find(i)]'), py.Statement(u'allLists = []'), py.Compound(u'def makeList(l)', [py.Statement(u'rv = make()'), py.Statement(u'allLists.append([rv] + l)'), py.Ret(u'rv')]), py.Statement(u'emptyList = makeList([])'), py.Compound(u'def findList(i)', [py.Statement(u'i = find(i)'), py.Ret(u'next([l[1:] for l in allLists if l[0] == i])')]), py.Compound(u'class Builtin(object)', []), py.Compound(u'class EmitLine(Builtin)', [py.Statement(u'def __init__(self, s): self.s = s'), py.Statement(u'def out(self, m): return [u" " * (m * 4) + self.s]')]), py.Compound(u'class EmitBlock(Builtin)', [py.Statement(u'def __init__(self, ls): self.ls = ls'), py.Statement(u'def out(self, m): return flatten([l.out(m + 1) for l in flatten(self.ls)])')]), py.Compound(u'class Builder(object)', [py.Statement(u'def Line(self, s): return EmitLine(s)'), py.Statement(u'def Block(self, ls): return EmitBlock(ls)')]), py.Statement(u'builtin = Builder()'), py.Compound(u'class builtinRels', [py.Statement(u'Line = {}; Block = {}'), py.Compound(u'def makeLine(self, s)', [py.Statement(u'rv = make()'), py.Statement(u'self.Line[rv, s] = None'), py.Ret(u'rv')]), py.Compound(u'def findLine(self, i)', [py.Statement(u'ss = [s for (x, s) in self.Line if x == i]'), py.Ret(u'EmitLine(findStr(next(ss)))')]), py.Compound(u'def makeBlock(self, ls)', [py.Statement(u'rv = make()'), py.Statement(u'self.Block[rv, ls] = None'), py.Ret(u'rv')]), py.Compound(u'def findBlock(self, i)', [py.Statement(u'lss = [ls for (x, ls) in self.Block if x == i]'), py.Ret(u'EmitBlock([self.findbuiltin(x) for x in findList(next(lss))])')]), py.Compound(u'def findbuiltin(self, i)', [py.Compound(u'try', [py.Ret(u'self.findLine(i)')]), py.Compound(u'except StopIteration', [py.Ret(u'self.findBlock(i)')])])]), py.Compound(u'class ParseError(Exception)', []), py.Compound(u'def lineNumber(s, i)', [py.Ret(u's.count(unichr(10), 0, i)')]), py.Compound(u'def main(argv)', [py.Statement(u'stdin, stdout, stderr = create_stdio()'), py.Statement(u'stderr.write("Registered %d rewrite rules\\n" % len(ruleNames))'), py.Statement(u'parser = MainParser(stdin.read().decode("utf-8"))'), py.Handler([py.Statement(u'i, rules = parser.parse()'), py.Conditional(u'i != len(parser.s)', [py.Statement(u'stderr.write("Failed to consume all input\\n")'), py.Statement(u'raise ParseError()')]), py.Statement(u'buf = []'), py.Statement(u'for rule in flatten(rules): buf.extend(rule.out(0))'), py.Statement(u'stdout.write(u"\\n".join(buf).encode("utf-8"))'), py.Statement(u'stderr.write("Wrote %d lines to stdout\\n" % len(buf))'), py.Ret(u'0')], [py.Statement(u'start = max(len(parser.lastMatch) - 25, 0)'), py.Statement(u'newlines = [0]'), py.Compound(u'for line in parser.s.split(u"\\n")', [py.Statement(u'newlines.append(newlines[-1] + len(line) + 1)')]), py.Compound(u'for k, start, stop in parser.lastMatch[start:]', [py.Statement(u'startLine = lineNumber(parser.s, start)'), py.Statement(u'startCol = start - newlines[startLine]'), py.Statement(u'stopLine = lineNumber(parser.s, stop)'), py.Statement(u'stopCol = stop - newlines[stopLine]'), py.Statement(u't = k.encode("utf-8"), startLine + 1, startCol, stopLine + 1, stopCol'), py.Statement(u'stderr.write(("Trail: %s (%d:%d - %d:%d)" % t) + chr(10))')]), py.Ret(u'1')])])], flatten(clss)])
        return i, rv
MainParser = ZADDYParser