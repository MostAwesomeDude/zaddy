from collections import defaultdict
from rpython.rlib.rfile import create_stdio
from rpython.rlib.objectmodel import specialize, r_dict
from rpython.rlib.unroll import unrolling_iterable
from rpython.rlib.listsort import make_timsort_class
class Result(object):
    pass
class Failed(Result):
    pass
failed = Failed()
def cached(f, cacheCount=[0]):
    attr = "t" + str(cacheCount[0]); cacheCount[0] += 1
    name = f.__name__
    uname = unicode(name)
    class CacheResult(Result):
        def __init__(self, i, rv): setattr(self, attr, (i, rv))
        pass
    cache = {}
    def deco(self, i):
        key = i
        if key in cache and cache[key] is failed: raise ParseError("no reason")
        elif key in cache: return getattr(cache[key], attr)
        cache[key] = failed
        i, rv = f(self, i)
        cache[key] = CacheResult(i, rv)
        self.lastMatch.append((uname, key, i))
        return i, rv
        pass
    deco.__name__ = name
    return deco
    pass
ruleNames = []
letNames = []
def let(f):
    letNames.append(f)
    return f
    pass
triggers = defaultdict(list)
def rewrite(*args):
    def deco(f):
        name = f.__name__
        ruleNames.append((name, f))
        for rel in args: triggers[rel].append(name)
        return f
        pass
    return deco
    pass
@specialize.call_location()
def flatten(xs):
    rv = []
    for x in xs: rv.extend(x)
    return rv
    pass
def intersect(l, r):
    rv = []
    for x in r:
        if x in l: rv.append(x)
        pass
    return rv
    pass
def listEq(l, r): return l == r
def listHash(l):
    rv = 0
    for x in l: rv += x
    return rv
    pass
class UF(object):
    def __init__(self):
        self.uf = [0]
        self.handle2str = {}
        self.str2handle = {}
        self.handle2list = {}
        self.list2handle = r_dict(listEq, listHash)
        pass
    def make(self):
        rv = len(self.uf)
        self.uf.append(rv)
        return rv
        pass
    def find(self, i):
        j = self.uf[i]
        while self.uf[j] != j: self.uf[i], j, i = self.uf[j], self.uf[j], j
        return j
        pass
    def union(self, i, j):
        i = self.find(i); j = self.find(j)
        if i != j: self.uf[i] = j
        return j
        pass
    def makeStr(self, s):
        if s in self.str2handle: return self.str2handle[s]
        rv = self.make()
        self.handle2str[rv] = s
        self.str2handle[s] = rv
        return rv
        pass
    def findStr(self, i):
        try: return self.handle2str[self.find(i)]
        except KeyError: raise NoResults("findStr", i)
        pass
    def makeList(self, l):
        if l in self.list2handle: return self.list2handle[l]
        rv = self.make()
        self.handle2list[rv] = l
        self.list2handle[l] = rv
        return rv
        pass
    def findList(self, i):
        try: return self.handle2list[self.find(i)]
        except KeyError: raise NoResults("findList", i)
        pass
    def rebuild(self):
        for (i, s) in self.handle2str.items():
            self.handle2str[self.find(i)] = s
            pass
        q = [(self.find(i), [self.find(x) for x in l]) for (i, l) in self.handle2list.items()]
        self.handle2list.clear()
        self.list2handle.clear()
        for i, l in q:
            self.handle2list[i] = l
            self.list2handle[l] = i
            pass
        pass
    pass
@specialize.call_location()
def rebuildRel(uf, d):
    q = []
    for r in d:
        if isinstance(r, int): q.append(uf.find(r))
        elif len(r) == 1: q.append((uf.find(r[0]),))
        elif len(r) == 2: q.append((uf.find(r[0]), uf.find(r[1])))
        elif len(r) == 3: q.append((uf.find(r[0]), uf.find(r[1]), uf.find(r[2])))
        elif len(r) == 4: q.append((uf.find(r[0]), uf.find(r[1]), uf.find(r[2]), uf.find(r[3])))
        elif len(r) == 5: q.append((uf.find(r[0]), uf.find(r[1]), uf.find(r[2]), uf.find(r[3]), uf.find(r[4])))
        else: assert False, "bob"
        pass
    d.clear()
    for r in q: d[r] = None
    pass
@specialize.call_location()
def rebuildHash(uf, d):
    for k, v in d.items(): d[k] = uf.find(v)
    pass
class Builtin(object):
    pass
class EmitLine(Builtin):
    def __init__(self, s): self.s = s
    def out(self, m): return [u" " * (m * 4) + self.s]
    pass
class EmitBlock(Builtin):
    def __init__(self, ls): self.ls = ls
    def out(self, m): return flatten([l.out(m + 1) for l in self.ls])
    pass
class Rels(object):
    dirty = False
    pass
allRels = []
class Builder(object):
    def Line(self, s): return EmitLine(s)
    def Block(self, ls): return EmitBlock(ls)
    pass
builtin = Builder()
class builtinRels(Rels):
    def __init__(self, uf):
        self.uf = uf
        self.Line = {}
        self.Block = {}
        self.Flatten = {}
        self.Length = {}
        self.Join = {}
        self.Concat = {}
        self.hashLine = {}
        self.hashBlock = {}
        self.hashFlatten = {}
        self.hashLength = {}
        self.hashJoin = {}
        self.hashConcat = {}
        pass
    def rebuild(self):
        rebuildRel(self.uf, self.Line)
        rebuildRel(self.uf, self.Block)
        rebuildRel(self.uf, self.Flatten)
        rebuildRel(self.uf, self.Length)
        rebuildRel(self.uf, self.Join)
        rebuildRel(self.uf, self.Concat)
        rebuildHash(self.uf, self.hashLine)
        rebuildHash(self.uf, self.hashBlock)
        rebuildHash(self.uf, self.hashFlatten)
        rebuildHash(self.uf, self.hashLength)
        rebuildHash(self.uf, self.hashJoin)
        rebuildHash(self.uf, self.hashConcat)
        pass
    def makeLine(self, s):
        rv = self.uf.make()
        self.Line[rv, s] = None
        return rv
        pass
    def findLine(self, i):
        for (x, s) in self.Line:
            if x != i: continue
            try: return EmitLine(self.uf.findStr(s))
            except NoResults: continue
            pass
        raise NoResults("findLine", i)
        pass
    def makeBlock(self, ls):
        rv = self.uf.make()
        self.Block[rv, ls] = None
        return rv
        pass
    def findBlock(self, i):
        for (x, ls) in self.Block:
            if x != i: continue
            try: return EmitBlock([self.findbuiltin(x) for x in self.uf.findList(ls)])
            except NoResults: continue
            pass
        raise NoResults("findBlock", i)
        pass
    def makeFlatten(self, ls):
        k = ls
        if k in self.hashFlatten: return self.hashFlatten[k]
        self.dirty = True
        rv = self.uf.make()
        self.Flatten[rv, ls] = None
        self.hashFlatten[k] = rv
        return rv
        pass
    def makeLength(self, s):
        k = s
        if k in self.hashLength: return self.hashLength[k]
        self.dirty = True
        rv = self.uf.make()
        self.Length[rv, s] = None
        self.hashLength[k] = rv
        return rv
        pass
    def makeJoin(self, s, ps):
        k = s, ps
        if k in self.hashJoin: return self.hashJoin[k]
        self.dirty = True
        rv = self.uf.make()
        self.Join[rv, s, ps] = None
        self.hashJoin[k] = rv
        return rv
        pass
    def makeConcat(self, p, ps):
        k = p, ps
        if k in self.hashConcat: return self.hashConcat[k]
        self.dirty = True
        rv = self.uf.make()
        self.Concat[rv, p, ps] = None
        self.hashConcat[k] = rv
        return rv
        pass
    def findbuiltin(self, i):
        try:
            return self.findLine(i)
            pass
        except NoResults:
            return self.findBlock(i)
            pass
        pass
    pass
allRels.append(("builtin", builtinRels))
class ParseError(Exception):
    def __init__(self, reason): self.reason = reason
    pass
class NoResults(Exception):
    def __init__(self, message, handle):
        self.message = message; self.handle = handle
        pass
    pass
def lineNumber(s, i):
    assert i >= 0
    return s.count(unichr(10), 0, i)
    pass
SortTraces = make_timsort_class(lt=lambda l, r: l[2] > r[2])
def main(argv):
    stdin, stdout, stderr = create_stdio()
    stderr.write("Registered %d rewrite rules\n" % len(frozenRules))
    stderr.write("Registered %d rewrite triggers\n" % len(frozenTriggers))
    uf = UF()
    parser = MainParser(stdin.read().decode("utf-8"), uf)
    try:
        i, l = parser.parse()
        if i != len(parser.s):
            raise ParseError("Failed to consume all input")
        l = parser.builtin.makeFlatten(l)
        for iteration in range(25):
            rulesToTry = []
            for r in unrolledRels:
                rel = getattr(parser, r)
                rulesToTry.extend(frozenTriggers.get(r, []))
                rel.rebuild()
                rel.dirty = False
                pass
            if not rulesToTry: break
            uf.rebuild()
            stderr.write("Iteration %d: Union/find: %d handles\n" % (iteration, len(uf.uf)))
            count = 0
            stderr.write("Iteration %d: %d rules to try\n" % (iteration, len(rulesToTry)))
            for name in rulesToTry:
                c = frozenRules[name](uf, parser)
                if c: stderr.write("Rule %s: %d transactions\n" % (name, c))
                count += c
                pass
            stderr.write("Iteration %d: %d applications\n" % (iteration, count))
            pass
        buf = []
        ls = uf.findList(l)
        stderr.write("Optimized to %d builtin blocks\n" % len(ls))
        for rule in ls: buf.extend(parser.builtin.findbuiltin(rule).out(0))
        stdout.write(u"\n".join(buf).encode("utf-8"))
        stderr.write("Wrote %d lines to stdout\n" % len(buf))
        return 0
    except ParseError as pe:
        stderr.write("Parse error: %s\n" % pe.reason)
        SortTraces(parser.lastMatch).sort()
        newlines = [0]
        for line in parser.s.split(u"\n"):
            newlines.append(newlines[-1] + len(line) + 1)
            pass
        for k, start, stop in parser.lastMatch[:10]:
            startLine = lineNumber(parser.s, start)
            startCol = start - newlines[startLine]
            stopLine = lineNumber(parser.s, stop)
            stopCol = stop - newlines[stopLine]
            t = k.encode("utf-8"), startLine + 1, startCol, stopLine + 1, stopCol
            stderr.write(("Trail: %s (%d:%d - %d:%d)" % t) + chr(10))
            pass
        return 1
    except NoResults as nr:
        stderr.write("No results: %s\n" % nr.message)
        return 1
        pass
    pass
pyCons = []
class pyRels(Rels):
    cons = pyCons
    def __init__(self, uf):
        self.uf = uf
        for n in unrolledpyCons:
            setattr(self, n, {})
            setattr(self, "hash" + n, {})
            pass
        pass
    def rebuild(self):
        for n in unrolledpyCons:
            rebuildRel(self.uf, getattr(self, n))
            rebuildHash(self.uf, getattr(self, "hash" + n))
            pass
        pass
    cons.append("Statement")
    def makeStatement(self, line):
        self.dirtyStatement = True
        k = (line)
        if k in self.hashStatement: return self.hashStatement[k]
        rv = self.uf.make()
        self.Statement[(rv, line)] = None
        self.hashStatement[k] = rv
        return rv
        pass
    cons.append("Imp")
    def makeImp(self, module, names):
        self.dirtyImp = True
        k = (module, names)
        if k in self.hashImp: return self.hashImp[k]
        rv = self.uf.make()
        self.Imp[(rv, module, names)] = None
        self.hashImp[k] = rv
        return rv
        pass
    cons.append("Ret")
    def makeRet(self, expr):
        self.dirtyRet = True
        k = (expr)
        if k in self.hashRet: return self.hashRet[k]
        rv = self.uf.make()
        self.Ret[(rv, expr)] = None
        self.hashRet[k] = rv
        return rv
        pass
    cons.append("RaiseIf")
    def makeRaiseIf(self, test):
        self.dirtyRaiseIf = True
        k = (test)
        if k in self.hashRaiseIf: return self.hashRaiseIf[k]
        rv = self.uf.make()
        self.RaiseIf[(rv, test)] = None
        self.hashRaiseIf[k] = rv
        return rv
        pass
    cons.append("Compound")
    def makeCompound(self, head, block):
        self.dirtyCompound = True
        k = (head, block)
        if k in self.hashCompound: return self.hashCompound[k]
        rv = self.uf.make()
        self.Compound[(rv, head, block)] = None
        self.hashCompound[k] = rv
        return rv
        pass
    cons.append("Conditional")
    def makeConditional(self, test, block):
        self.dirtyConditional = True
        k = (test, block)
        if k in self.hashConditional: return self.hashConditional[k]
        rv = self.uf.make()
        self.Conditional[(rv, test, block)] = None
        self.hashConditional[k] = rv
        return rv
        pass
    cons.append("Handler")
    def makeHandler(self, block, handler):
        self.dirtyHandler = True
        k = (block, handler)
        if k in self.hashHandler: return self.hashHandler[k]
        rv = self.uf.make()
        self.Handler[(rv, block, handler)] = None
        self.hashHandler[k] = rv
        return rv
        pass
    pass
unrolledpyCons = unrolling_iterable(pyCons[:])
allRels.append(("py", pyRels))
pegCons = []
class pegRels(Rels):
    cons = pegCons
    def __init__(self, uf):
        self.uf = uf
        for n in unrolledpegCons:
            setattr(self, n, {})
            setattr(self, "hash" + n, {})
            pass
        pass
    def rebuild(self):
        for n in unrolledpegCons:
            rebuildRel(self.uf, getattr(self, n))
            rebuildHash(self.uf, getattr(self, "hash" + n))
            pass
        pass
    cons.append("NamePatt")
    def makeNamePatt(self, name):
        self.dirtyNamePatt = True
        k = (name)
        if k in self.hashNamePatt: return self.hashNamePatt[k]
        rv = self.uf.make()
        self.NamePatt[(rv, name)] = None
        self.hashNamePatt[k] = rv
        return rv
        pass
    cons.append("TuplePatt")
    def makeTuplePatt(self, ps):
        self.dirtyTuplePatt = True
        k = (ps)
        if k in self.hashTuplePatt: return self.hashTuplePatt[k]
        rv = self.uf.make()
        self.TuplePatt[(rv, ps)] = None
        self.hashTuplePatt[k] = rv
        return rv
        pass
    cons.append("Null")
    def makeNull(self, ):
        self.dirtyNull = True
        k = ()
        if k in self.hashNull: return self.hashNull[k]
        rv = self.uf.make()
        self.Null[(rv, )] = None
        self.hashNull[k] = rv
        return rv
        pass
    cons.append("Token")
    def makeToken(self, s):
        self.dirtyToken = True
        k = (s)
        if k in self.hashToken: return self.hashToken[k]
        rv = self.uf.make()
        self.Token[(rv, s)] = None
        self.hashToken[k] = rv
        return rv
        pass
    cons.append("Call")
    def makeCall(self, s):
        self.dirtyCall = True
        k = (s)
        if k in self.hashCall: return self.hashCall[k]
        rv = self.uf.make()
        self.Call[(rv, s)] = None
        self.hashCall[k] = rv
        return rv
        pass
    cons.append("Sequence")
    def makeSequence(self, exprs):
        self.dirtySequence = True
        k = (exprs)
        if k in self.hashSequence: return self.hashSequence[k]
        rv = self.uf.make()
        self.Sequence[(rv, exprs)] = None
        self.hashSequence[k] = rv
        return rv
        pass
    cons.append("Choice")
    def makeChoice(self, this, that):
        self.dirtyChoice = True
        k = (this, that)
        if k in self.hashChoice: return self.hashChoice[k]
        rv = self.uf.make()
        self.Choice[(rv, this, that)] = None
        self.hashChoice[k] = rv
        return rv
        pass
    cons.append("Any")
    def makeAny(self, expr):
        self.dirtyAny = True
        k = (expr)
        if k in self.hashAny: return self.hashAny[k]
        rv = self.uf.make()
        self.Any[(rv, expr)] = None
        self.hashAny[k] = rv
        return rv
        pass
    cons.append("Some")
    def makeSome(self, expr):
        self.dirtySome = True
        k = (expr)
        if k in self.hashSome: return self.hashSome[k]
        rv = self.uf.make()
        self.Some[(rv, expr)] = None
        self.hashSome[k] = rv
        return rv
        pass
    cons.append("Maybe")
    def makeMaybe(self, expr):
        self.dirtyMaybe = True
        k = (expr)
        if k in self.hashMaybe: return self.hashMaybe[k]
        rv = self.uf.make()
        self.Maybe[(rv, expr)] = None
        self.hashMaybe[k] = rv
        return rv
        pass
    cons.append("Positive")
    def makePositive(self, expr):
        self.dirtyPositive = True
        k = (expr)
        if k in self.hashPositive: return self.hashPositive[k]
        rv = self.uf.make()
        self.Positive[(rv, expr)] = None
        self.hashPositive[k] = rv
        return rv
        pass
    cons.append("Negative")
    def makeNegative(self, expr):
        self.dirtyNegative = True
        k = (expr)
        if k in self.hashNegative: return self.hashNegative[k]
        rv = self.uf.make()
        self.Negative[(rv, expr)] = None
        self.hashNegative[k] = rv
        return rv
        pass
    cons.append("Capture")
    def makeCapture(self, expr, patt):
        self.dirtyCapture = True
        k = (expr, patt)
        if k in self.hashCapture: return self.hashCapture[k]
        rv = self.uf.make()
        self.Capture[(rv, expr, patt)] = None
        self.hashCapture[k] = rv
        return rv
        pass
    cons.append("Production")
    def makeProduction(self, expr, prod):
        self.dirtyProduction = True
        k = (expr, prod)
        if k in self.hashProduction: return self.hashProduction[k]
        rv = self.uf.make()
        self.Production[(rv, expr, prod)] = None
        self.hashProduction[k] = rv
        return rv
        pass
    pass
unrolledpegCons = unrolling_iterable(pegCons[:])
allRels.append(("peg", pegRels))
zephyrCons = []
class zephyrRels(Rels):
    cons = zephyrCons
    def __init__(self, uf):
        self.uf = uf
        for n in unrolledzephyrCons:
            setattr(self, n, {})
            setattr(self, "hash" + n, {})
            pass
        pass
    def rebuild(self):
        for n in unrolledzephyrCons:
            rebuildRel(self.uf, getattr(self, n))
            rebuildHash(self.uf, getattr(self, "hash" + n))
            pass
        pass
    cons.append("Signature")
    def makeSignature(self, name, tys):
        self.dirtySignature = True
        k = (name, tys)
        if k in self.hashSignature: return self.hashSignature[k]
        rv = self.uf.make()
        self.Signature[(rv, name, tys)] = None
        self.hashSignature[k] = rv
        return rv
        pass
    cons.append("Product")
    def makeProduct(self, name, fs):
        self.dirtyProduct = True
        k = (name, fs)
        if k in self.hashProduct: return self.hashProduct[k]
        rv = self.uf.make()
        self.Product[(rv, name, fs)] = None
        self.hashProduct[k] = rv
        return rv
        pass
    cons.append("Sum")
    def makeSum(self, name, attrs, con, cons):
        self.dirtySum = True
        k = (name, attrs, con, cons)
        if k in self.hashSum: return self.hashSum[k]
        rv = self.uf.make()
        self.Sum[(rv, name, attrs, con, cons)] = None
        self.hashSum[k] = rv
        return rv
        pass
    cons.append("Con")
    def makeCon(self, tag, args):
        self.dirtyCon = True
        k = (tag, args)
        if k in self.hashCon: return self.hashCon[k]
        rv = self.uf.make()
        self.Con[(rv, tag, args)] = None
        self.hashCon[k] = rv
        return rv
        pass
    cons.append("Id")
    def makeId(self, ty, name):
        self.dirtyId = True
        k = (ty, name)
        if k in self.hashId: return self.hashId[k]
        rv = self.uf.make()
        self.Id[(rv, ty, name)] = None
        self.hashId[k] = rv
        return rv
        pass
    cons.append("Option")
    def makeOption(self, ty, name):
        self.dirtyOption = True
        k = (ty, name)
        if k in self.hashOption: return self.hashOption[k]
        rv = self.uf.make()
        self.Option[(rv, ty, name)] = None
        self.hashOption[k] = rv
        return rv
        pass
    cons.append("Sequence")
    def makeSequence(self, ty, name):
        self.dirtySequence = True
        k = (ty, name)
        if k in self.hashSequence: return self.hashSequence[k]
        rv = self.uf.make()
        self.Sequence[(rv, ty, name)] = None
        self.hashSequence[k] = rv
        return rv
        pass
    pass
unrolledzephyrCons = unrolling_iterable(zephyrCons[:])
allRels.append(("zephyr", zephyrRels))
rulesCons = []
class rulesRels(Rels):
    cons = rulesCons
    def __init__(self, uf):
        self.uf = uf
        for n in unrolledrulesCons:
            setattr(self, n, {})
            setattr(self, "hash" + n, {})
            pass
        pass
    def rebuild(self):
        for n in unrolledrulesCons:
            rebuildRel(self.uf, getattr(self, n))
            rebuildHash(self.uf, getattr(self, "hash" + n))
            pass
        pass
    cons.append("IgnorePatt")
    def makeIgnorePatt(self, ):
        self.dirtyIgnorePatt = True
        k = ()
        if k in self.hashIgnorePatt: return self.hashIgnorePatt[k]
        rv = self.uf.make()
        self.IgnorePatt[(rv, )] = None
        self.hashIgnorePatt[k] = rv
        return rv
        pass
    cons.append("VarPatt")
    def makeVarPatt(self, n):
        self.dirtyVarPatt = True
        k = (n)
        if k in self.hashVarPatt: return self.hashVarPatt[k]
        rv = self.uf.make()
        self.VarPatt[(rv, n)] = None
        self.hashVarPatt[k] = rv
        return rv
        pass
    cons.append("StrPatt")
    def makeStrPatt(self, s):
        self.dirtyStrPatt = True
        k = (s)
        if k in self.hashStrPatt: return self.hashStrPatt[k]
        rv = self.uf.make()
        self.StrPatt[(rv, s)] = None
        self.hashStrPatt[k] = rv
        return rv
        pass
    cons.append("StructPatt")
    def makeStructPatt(self, ns, func, vars):
        self.dirtyStructPatt = True
        k = (ns, func, vars)
        if k in self.hashStructPatt: return self.hashStructPatt[k]
        rv = self.uf.make()
        self.StructPatt[(rv, ns, func, vars)] = None
        self.hashStructPatt[k] = rv
        return rv
        pass
    cons.append("EmptyListPatt")
    def makeEmptyListPatt(self, ):
        self.dirtyEmptyListPatt = True
        k = ()
        if k in self.hashEmptyListPatt: return self.hashEmptyListPatt[k]
        rv = self.uf.make()
        self.EmptyListPatt[(rv, )] = None
        self.hashEmptyListPatt[k] = rv
        return rv
        pass
    cons.append("ListPatt")
    def makeListPatt(self, ps):
        self.dirtyListPatt = True
        k = (ps)
        if k in self.hashListPatt: return self.hashListPatt[k]
        rv = self.uf.make()
        self.ListPatt[(rv, ps)] = None
        self.hashListPatt[k] = rv
        return rv
        pass
    cons.append("ListHeadPatt")
    def makeListHeadPatt(self, head, ps):
        self.dirtyListHeadPatt = True
        k = (head, ps)
        if k in self.hashListHeadPatt: return self.hashListHeadPatt[k]
        rv = self.uf.make()
        self.ListHeadPatt[(rv, head, ps)] = None
        self.hashListHeadPatt[k] = rv
        return rv
        pass
    cons.append("ListTailPatt")
    def makeListTailPatt(self, tail, ps):
        self.dirtyListTailPatt = True
        k = (tail, ps)
        if k in self.hashListTailPatt: return self.hashListTailPatt[k]
        rv = self.uf.make()
        self.ListTailPatt[(rv, tail, ps)] = None
        self.hashListTailPatt[k] = rv
        return rv
        pass
    cons.append("ListMidPatt")
    def makeListMidPatt(self, head, tail, ps):
        self.dirtyListMidPatt = True
        k = (head, tail, ps)
        if k in self.hashListMidPatt: return self.hashListMidPatt[k]
        rv = self.uf.make()
        self.ListMidPatt[(rv, head, tail, ps)] = None
        self.hashListMidPatt[k] = rv
        return rv
        pass
    cons.append("VarProd")
    def makeVarProd(self, name):
        self.dirtyVarProd = True
        k = (name)
        if k in self.hashVarProd: return self.hashVarProd[k]
        rv = self.uf.make()
        self.VarProd[(rv, name)] = None
        self.hashVarProd[k] = rv
        return rv
        pass
    cons.append("ConstProd")
    def makeConstProd(self, name):
        self.dirtyConstProd = True
        k = (name)
        if k in self.hashConstProd: return self.hashConstProd[k]
        rv = self.uf.make()
        self.ConstProd[(rv, name)] = None
        self.hashConstProd[k] = rv
        return rv
        pass
    cons.append("StrProd")
    def makeStrProd(self, s):
        self.dirtyStrProd = True
        k = (s)
        if k in self.hashStrProd: return self.hashStrProd[k]
        rv = self.uf.make()
        self.StrProd[(rv, s)] = None
        self.hashStrProd[k] = rv
        return rv
        pass
    cons.append("CharProd")
    def makeCharProd(self, n):
        self.dirtyCharProd = True
        k = (n)
        if k in self.hashCharProd: return self.hashCharProd[k]
        rv = self.uf.make()
        self.CharProd[(rv, n)] = None
        self.hashCharProd[k] = rv
        return rv
        pass
    cons.append("StructProd")
    def makeStructProd(self, ns, func, ps):
        self.dirtyStructProd = True
        k = (ns, func, ps)
        if k in self.hashStructProd: return self.hashStructProd[k]
        rv = self.uf.make()
        self.StructProd[(rv, ns, func, ps)] = None
        self.hashStructProd[k] = rv
        return rv
        pass
    cons.append("ListProd")
    def makeListProd(self, ps):
        self.dirtyListProd = True
        k = (ps)
        if k in self.hashListProd: return self.hashListProd[k]
        rv = self.uf.make()
        self.ListProd[(rv, ps)] = None
        self.hashListProd[k] = rv
        return rv
        pass
    cons.append("ListHeadProd")
    def makeListHeadProd(self, head, ps):
        self.dirtyListHeadProd = True
        k = (head, ps)
        if k in self.hashListHeadProd: return self.hashListHeadProd[k]
        rv = self.uf.make()
        self.ListHeadProd[(rv, head, ps)] = None
        self.hashListHeadProd[k] = rv
        return rv
        pass
    cons.append("ListTailProd")
    def makeListTailProd(self, tail, ps):
        self.dirtyListTailProd = True
        k = (tail, ps)
        if k in self.hashListTailProd: return self.hashListTailProd[k]
        rv = self.uf.make()
        self.ListTailProd[(rv, tail, ps)] = None
        self.hashListTailProd[k] = rv
        return rv
        pass
    cons.append("ListMidProd")
    def makeListMidProd(self, head, tail, ps):
        self.dirtyListMidProd = True
        k = (head, tail, ps)
        if k in self.hashListMidProd: return self.hashListMidProd[k]
        rv = self.uf.make()
        self.ListMidProd[(rv, head, tail, ps)] = None
        self.hashListMidProd[k] = rv
        return rv
        pass
    cons.append("FlattenOp")
    def makeFlattenOp(self, p):
        self.dirtyFlattenOp = True
        k = (p)
        if k in self.hashFlattenOp: return self.hashFlattenOp[k]
        rv = self.uf.make()
        self.FlattenOp[(rv, p)] = None
        self.hashFlattenOp[k] = rv
        return rv
        pass
    cons.append("LengthOp")
    def makeLengthOp(self, p):
        self.dirtyLengthOp = True
        k = (p)
        if k in self.hashLengthOp: return self.hashLengthOp[k]
        rv = self.uf.make()
        self.LengthOp[(rv, p)] = None
        self.hashLengthOp[k] = rv
        return rv
        pass
    cons.append("JoinOp")
    def makeJoinOp(self, s, p):
        self.dirtyJoinOp = True
        k = (s, p)
        if k in self.hashJoinOp: return self.hashJoinOp[k]
        rv = self.uf.make()
        self.JoinOp[(rv, s, p)] = None
        self.hashJoinOp[k] = rv
        return rv
        pass
    cons.append("ConcatOp")
    def makeConcatOp(self, p, ps):
        self.dirtyConcatOp = True
        k = (p, ps)
        if k in self.hashConcatOp: return self.hashConcatOp[k]
        rv = self.uf.make()
        self.ConcatOp[(rv, p, ps)] = None
        self.hashConcatOp[k] = rv
        return rv
        pass
    cons.append("Rewrite")
    def makeRewrite(self, name, root, prods):
        self.dirtyRewrite = True
        k = (name, root, prods)
        if k in self.hashRewrite: return self.hashRewrite[k]
        rv = self.uf.make()
        self.Rewrite[(rv, name, root, prods)] = None
        self.hashRewrite[k] = rv
        return rv
        pass
    cons.append("Let")
    def makeLet(self, name, p):
        self.dirtyLet = True
        k = (name, p)
        if k in self.hashLet: return self.hashLet[k]
        rv = self.uf.make()
        self.Let[(rv, name, p)] = None
        self.hashLet[k] = rv
        return rv
        pass
    pass
unrolledrulesCons = unrolling_iterable(rulesCons[:])
allRels.append(("rules", rulesRels))
charCons = []
class charRels(Rels):
    cons = charCons
    def __init__(self, uf):
        self.uf = uf
        for n in unrolledcharCons:
            setattr(self, n, {})
            setattr(self, "hash" + n, {})
            pass
        pass
    def rebuild(self):
        for n in unrolledcharCons:
            rebuildRel(self.uf, getattr(self, n))
            rebuildHash(self.uf, getattr(self, "hash" + n))
            pass
        pass
    cons.append("Any")
    def makeAny(self, ):
        self.dirtyAny = True
        k = ()
        if k in self.hashAny: return self.hashAny[k]
        rv = self.uf.make()
        self.Any[(rv, )] = None
        self.hashAny[k] = rv
        return rv
        pass
    cons.append("Exactly")
    def makeExactly(self, c):
        self.dirtyExactly = True
        k = (c)
        if k in self.hashExactly: return self.hashExactly[k]
        rv = self.uf.make()
        self.Exactly[(rv, c)] = None
        self.hashExactly[k] = rv
        return rv
        pass
    cons.append("Range")
    def makeRange(self, l, u):
        self.dirtyRange = True
        k = (l, u)
        if k in self.hashRange: return self.hashRange[k]
        rv = self.uf.make()
        self.Range[(rv, l, u)] = None
        self.hashRange[k] = rv
        return rv
        pass
    cons.append("Call")
    def makeCall(self, n):
        self.dirtyCall = True
        k = (n)
        if k in self.hashCall: return self.hashCall[k]
        rv = self.uf.make()
        self.Call[(rv, n)] = None
        self.hashCall[k] = rv
        return rv
        pass
    cons.append("Complement")
    def makeComplement(self, s):
        self.dirtyComplement = True
        k = (s)
        if k in self.hashComplement: return self.hashComplement[k]
        rv = self.uf.make()
        self.Complement[(rv, s)] = None
        self.hashComplement[k] = rv
        return rv
        pass
    cons.append("Either")
    def makeEither(self, l, r):
        self.dirtyEither = True
        k = (l, r)
        if k in self.hashEither: return self.hashEither[k]
        rv = self.uf.make()
        self.Either[(rv, l, r)] = None
        self.hashEither[k] = rv
        return rv
        pass
    pass
unrolledcharCons = unrolling_iterable(charCons[:])
allRels.append(("char", charRels))
@rewrite("builtin", "py", "rules", "peg", "char", "zephyr")
def pyStatement(uf, rel):
    q = []
    beEmpty = uf.makeList([])
    for (vRoot, vL) in rel.py.Statement:
        try:
            if len(uf.findList(beEmpty)): continue
            uf.union(vRoot, uf.makeList([rel.builtin.makeLine(vL)]))
            q.append(vRoot)
            pass
        except NoResults: continue
        pass
    return len(q)
    pass
@rewrite("builtin", "py", "rules", "peg", "char", "zephyr")
def pyImp(uf, rel):
    q = []
    beEmpty = uf.makeList([])
    for (vRoot, vM, vNs) in rel.py.Imp:
        try:
            if len(uf.findList(beEmpty)): continue
            uf.union(vRoot, uf.makeList([rel.builtin.makeLine(rel.builtin.makeConcat(uf.makeStr(u'from '), uf.makeList([vM, uf.makeStr(u' import '), vNs])))]))
            q.append(vRoot)
            pass
        except NoResults: continue
        pass
    return len(q)
    pass
@rewrite("builtin", "py", "rules", "peg", "char", "zephyr")
def pyRet(uf, rel):
    q = []
    beEmpty = uf.makeList([])
    for (vRoot, vE) in rel.py.Ret:
        try:
            if len(uf.findList(beEmpty)): continue
            uf.union(vRoot, uf.makeList([rel.builtin.makeLine(rel.builtin.makeConcat(uf.makeStr(u'return '), uf.makeList([vE])))]))
            q.append(vRoot)
            pass
        except NoResults: continue
        pass
    return len(q)
    pass
@rewrite("builtin", "py", "rules", "peg", "char", "zephyr")
def pyRaiseIf(uf, rel):
    q = []
    beEmpty = uf.makeList([])
    for (vRoot, vT) in rel.py.RaiseIf:
        try:
            if len(uf.findList(beEmpty)): continue
            uf.union(vRoot, uf.makeList([rel.builtin.makeLine(rel.builtin.makeConcat(uf.makeStr(u'if '), uf.makeList([vT, uf.makeStr(u': raise ParseError("no reason")')])))]))
            q.append(vRoot)
            pass
        except NoResults: continue
        pass
    return len(q)
    pass
@rewrite("builtin", "py", "rules", "peg", "char", "zephyr")
def pyCompPass(uf, rel):
    q = []
    beEmpty = uf.makeList([])
    for (vRoot, vH, beEmpty) in rel.py.Compound:
        try:
            if len(uf.findList(beEmpty)): continue
            uf.union(vRoot, uf.makeList([rel.builtin.makeLine(rel.builtin.makeConcat(vH, uf.makeList([uf.makeStr(u': pass')])))]))
            q.append(vRoot)
            pass
        except NoResults: continue
        pass
    return len(q)
    pass
@rewrite("builtin", "py", "rules", "peg", "char", "zephyr")
def pyCompBlock(uf, rel):
    q = []
    beEmpty = uf.makeList([])
    for (vRoot, vH, vB) in rel.py.Compound:
        try:
            if len(uf.findList(beEmpty)): continue
            uf.union(vRoot, uf.makeList([rel.builtin.makeLine(rel.builtin.makeConcat(vH, uf.makeList([uf.makeStr(u':')]))), rel.builtin.makeBlock(rel.builtin.makeFlatten(uf.makeList([rel.builtin.makeFlatten(vB), uf.makeList([rel.builtin.makeLine(uf.makeStr(u'pass'))])])))]))
            q.append(vRoot)
            pass
        except NoResults: continue
        pass
    return len(q)
    pass
@rewrite("builtin", "py", "rules", "peg", "char", "zephyr")
def pyCondEmpty(uf, rel):
    q = []
    beEmpty = uf.makeList([])
    for (vRoot, vT, beEmpty) in rel.py.Conditional:
        try:
            if len(uf.findList(beEmpty)): continue
            uf.union(vRoot, uf.makeList([]))
            q.append(vRoot)
            pass
        except NoResults: continue
        pass
    return len(q)
    pass
@rewrite("builtin", "py", "rules", "peg", "char", "zephyr")
def pyCondBlock(uf, rel):
    q = []
    beEmpty = uf.makeList([])
    for (vRoot, vT, vB) in rel.py.Conditional:
        try:
            if len(uf.findList(beEmpty)): continue
            uf.union(vRoot, uf.makeList([rel.builtin.makeLine(rel.builtin.makeConcat(uf.makeStr(u'if '), uf.makeList([vT, uf.makeStr(u':')]))), rel.builtin.makeBlock(rel.builtin.makeFlatten(vB))]))
            q.append(vRoot)
            pass
        except NoResults: continue
        pass
    return len(q)
    pass
@rewrite("builtin", "py", "rules", "peg", "char", "zephyr")
def pyHandEmpty(uf, rel):
    q = []
    beEmpty = uf.makeList([])
    for (vRoot, vB, beEmpty) in rel.py.Handler:
        try:
            if len(uf.findList(beEmpty)): continue
            uf.union(vRoot, uf.makeList([]))
            q.append(vRoot)
            pass
        except NoResults: continue
        pass
    return len(q)
    pass
@rewrite("builtin", "py", "rules", "peg", "char", "zephyr")
def pyHandBlock(uf, rel):
    q = []
    beEmpty = uf.makeList([])
    for (vRoot, vB, vH) in rel.py.Handler:
        try:
            if len(uf.findList(beEmpty)): continue
            uf.union(vRoot, uf.makeList([rel.builtin.makeLine(uf.makeStr(u'try:')), rel.builtin.makeBlock(rel.builtin.makeFlatten(vB)), rel.builtin.makeLine(uf.makeStr(u'except ParseError as pe:')), rel.builtin.makeBlock(rel.builtin.makeFlatten(vH))]))
            q.append(vRoot)
            pass
        except NoResults: continue
        pass
    return len(q)
    pass
@rewrite("builtin", "py", "rules", "peg", "char", "zephyr")
def pegNamePatt(uf, rel):
    q = []
    beEmpty = uf.makeList([])
    for (vRoot, vName) in rel.peg.NamePatt:
        try:
            if len(uf.findList(beEmpty)): continue
            uf.union(vRoot, rel.builtin.makeConcat(uf.makeStr(u'v'), uf.makeList([vName])))
            q.append(vRoot)
            pass
        except NoResults: continue
        pass
    return len(q)
    pass
@rewrite("builtin", "py", "rules", "peg", "char", "zephyr")
def pegTuplePatt(uf, rel):
    q = []
    beEmpty = uf.makeList([])
    for (vRoot, vPs) in rel.peg.TuplePatt:
        try:
            if len(uf.findList(beEmpty)): continue
            uf.union(vRoot, rel.builtin.makeConcat(uf.makeStr(u'('), uf.makeList([rel.builtin.makeJoin(uf.makeStr(u", "), vPs), uf.makeStr(u')')])))
            q.append(vRoot)
            pass
        except NoResults: continue
        pass
    return len(q)
    pass
@let
def letsave(uf, rel): rel.constsave = rel.py.makeStatement(uf.makeStr(u'st.append(i)'))
@let
def letbackup(uf, rel): rel.constbackup = rel.py.makeStatement(uf.makeStr(u'i = st.pop()'))
@let
def letboundcheck(uf, rel): rel.constboundcheck = rel.py.makeRaiseIf(uf.makeStr(u'i >= len(self.s)'))
@let
def letskipws(uf, rel): rel.constskipws = rel.py.makeStatement(uf.makeStr(u'while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1'))
@rewrite("builtin", "py", "rules", "peg", "char", "zephyr")
def pegSeq(uf, rel):
    q = []
    beEmpty = uf.makeList([])
    for (vRoot, vEs) in rel.peg.Sequence:
        try:
            if len(uf.findList(beEmpty)): continue
            uf.union(vRoot, rel.builtin.makeFlatten(vEs))
            q.append(vRoot)
            pass
        except NoResults: continue
        pass
    return len(q)
    pass
@rewrite("builtin", "py", "rules", "peg", "char", "zephyr")
def pegCap(uf, rel):
    q = []
    beEmpty = uf.makeList([])
    for (vRoot, vE, vP) in rel.peg.Capture:
        try:
            if len(uf.findList(beEmpty)): continue
            uf.union(vRoot, uf.makeList(uf.findList(vE) + [rel.py.makeStatement(rel.builtin.makeConcat(vP, uf.makeList([uf.makeStr(u' = rv')])))]))
            q.append(vRoot)
            pass
        except NoResults: continue
        pass
    return len(q)
    pass
@rewrite("builtin", "py", "rules", "peg", "char", "zephyr")
def pegProd(uf, rel):
    q = []
    beEmpty = uf.makeList([])
    for (vRoot, vE, vP) in rel.peg.Production:
        try:
            if len(uf.findList(beEmpty)): continue
            uf.union(vRoot, uf.makeList(uf.findList(vE) + [rel.py.makeStatement(rel.builtin.makeConcat(uf.makeStr(u'rv = '), uf.makeList([vP])))]))
            q.append(vRoot)
            pass
        except NoResults: continue
        pass
    return len(q)
    pass
@rewrite("builtin", "py", "rules", "peg", "char", "zephyr")
def pegCall(uf, rel):
    q = []
    beEmpty = uf.makeList([])
    for (vRoot, vS) in rel.peg.Call:
        try:
            if len(uf.findList(beEmpty)): continue
            uf.union(vRoot, uf.makeList([rel.py.makeStatement(rel.builtin.makeConcat(uf.makeStr(u'i, rv = self.parse'), uf.makeList([vS, uf.makeStr(u'(i)')])))]))
            q.append(vRoot)
            pass
        except NoResults: continue
        pass
    return len(q)
    pass
@rewrite("builtin", "py", "rules", "peg", "char", "zephyr")
def pegChoice(uf, rel):
    q = []
    beEmpty = uf.makeList([])
    for (vRoot, vL, vR) in rel.peg.Choice:
        try:
            if len(uf.findList(beEmpty)): continue
            uf.union(vRoot, uf.makeList([rel.constsave, rel.py.makeHandler(vL, uf.makeList([rel.constbackup] + uf.findList(vR)))]))
            q.append(vRoot)
            pass
        except NoResults: continue
        pass
    return len(q)
    pass
@rewrite("builtin", "py", "rules", "peg", "char", "zephyr")
def pegToken(uf, rel):
    q = []
    beEmpty = uf.makeList([])
    for (vRoot, vS) in rel.peg.Token:
        try:
            if len(uf.findList(beEmpty)): continue
            uf.union(vRoot, uf.makeList([rel.constskipws, rel.constboundcheck, rel.py.makeStatement(uf.makeStr(u'assert i >= 0')), rel.py.makeRaiseIf(rel.builtin.makeConcat(uf.makeStr(u'self.s[i:i + '), uf.makeList([rel.builtin.makeLength(vS), uf.makeStr(u'] != u"'), vS, uf.makeStr(u'"')]))), rel.py.makeStatement(rel.builtin.makeConcat(uf.makeStr(u'self.lastMatch.append((u"TOKEN '), uf.makeList([vS, uf.makeStr(u'", i, i + '), rel.builtin.makeLength(vS), uf.makeStr(u'))')]))), rel.py.makeStatement(rel.builtin.makeConcat(uf.makeStr(u'rv = self.uf.makeStr(u"'), uf.makeList([vS, uf.makeStr(u'"); i += '), rel.builtin.makeLength(vS)])))]))
            q.append(vRoot)
            pass
        except NoResults: continue
        pass
    return len(q)
    pass
@rewrite("builtin", "py", "rules", "peg", "char", "zephyr")
def pegAny(uf, rel):
    q = []
    beEmpty = uf.makeList([])
    for (vRoot, vE) in rel.peg.Any:
        try:
            if len(uf.findList(beEmpty)): continue
            uf.union(vRoot, uf.makeList([rel.py.makeStatement(uf.makeStr(u'rvs = []')), rel.py.makeCompound(uf.makeStr(u'while True'), uf.makeList([rel.constsave, rel.py.makeHandler(uf.makeList(uf.findList(vE) + [rel.py.makeStatement(uf.makeStr(u'rvs.append(rv)'))]), uf.makeList([rel.constbackup, rel.py.makeStatement(uf.makeStr(u'break'))]))])), rel.py.makeStatement(uf.makeStr(u'rv = rel.uf.makeList(rvs)'))]))
            q.append(vRoot)
            pass
        except NoResults: continue
        pass
    return len(q)
    pass
@rewrite("builtin", "py", "rules", "peg", "char", "zephyr")
def pegSome(uf, rel):
    q = []
    beEmpty = uf.makeList([])
    for (vRoot, vE) in rel.peg.Some:
        try:
            if len(uf.findList(beEmpty)): continue
            uf.union(vRoot, rel.builtin.makeFlatten(uf.makeList([rel.peg.makeAny(vE), uf.makeList([rel.py.makeRaiseIf(uf.makeStr(u'not len(rvs)'))])])))
            q.append(vRoot)
            pass
        except NoResults: continue
        pass
    return len(q)
    pass
@rewrite("builtin", "py", "rules", "peg", "char", "zephyr")
def pegMaybe(uf, rel):
    q = []
    beEmpty = uf.makeList([])
    for (vRoot, vE) in rel.peg.Maybe:
        try:
            if len(uf.findList(beEmpty)): continue
            uf.union(vRoot, uf.makeList([rel.constsave, rel.py.makeHandler(vE, uf.makeList([rel.py.makeStatement(uf.makeStr(u'rv = 0')), rel.constbackup]))]))
            q.append(vRoot)
            pass
        except NoResults: continue
        pass
    return len(q)
    pass
@rewrite("builtin", "py", "rules", "peg", "char", "zephyr")
def pegPos(uf, rel):
    q = []
    beEmpty = uf.makeList([])
    for (vRoot, vE) in rel.peg.Positive:
        try:
            if len(uf.findList(beEmpty)): continue
            uf.union(vRoot, uf.makeList([rel.constsave, rel.py.makeHandler(uf.makeList(uf.findList(vE) + [rel.py.makeStatement(uf.makeStr(u'rv = True'))]), uf.makeList([rel.py.makeStatement(uf.makeStr(u'rv = False'))])), rel.constbackup, rel.py.makeRaiseIf(uf.makeStr(u'not rv'))]))
            q.append(vRoot)
            pass
        except NoResults: continue
        pass
    return len(q)
    pass
@rewrite("builtin", "py", "rules", "peg", "char", "zephyr")
def pegNeg(uf, rel):
    q = []
    beEmpty = uf.makeList([])
    for (vRoot, vE) in rel.peg.Negative:
        try:
            if len(uf.findList(beEmpty)): continue
            uf.union(vRoot, uf.makeList([rel.constsave, rel.py.makeHandler(uf.makeList(uf.findList(vE) + [rel.py.makeStatement(uf.makeStr(u'rv = True'))]), uf.makeList([rel.py.makeStatement(uf.makeStr(u'rv = False'))])), rel.constbackup, rel.py.makeRaiseIf(uf.makeStr(u'rv'))]))
            q.append(vRoot)
            pass
        except NoResults: continue
        pass
    return len(q)
    pass
@rewrite("builtin", "py", "rules", "peg", "char", "zephyr")
def zSig(uf, rel):
    q = []
    beEmpty = uf.makeList([])
    for (vRoot, vN, vT) in rel.zephyr.Signature:
        try:
            if len(uf.findList(beEmpty)): continue
            uf.union(vRoot, uf.makeList([rel.py.makeStatement(rel.builtin.makeConcat(vN, uf.makeList([uf.makeStr(u'Cons = []')]))), rel.py.makeCompound(rel.builtin.makeConcat(uf.makeStr(u'class '), uf.makeList([vN, uf.makeStr(u'Rels(Rels)')])), rel.builtin.makeFlatten(uf.makeList([uf.makeList([rel.py.makeStatement(rel.builtin.makeConcat(uf.makeStr(u'cons = '), uf.makeList([vN, uf.makeStr(u'Cons')]))), rel.py.makeCompound(uf.makeStr(u'def __init__(self, uf)'), uf.makeList([rel.py.makeStatement(uf.makeStr(u'self.uf = uf')), rel.py.makeCompound(rel.builtin.makeConcat(uf.makeStr(u'for n in unrolled'), uf.makeList([vN, uf.makeStr(u'Cons')])), uf.makeList([rel.py.makeStatement(uf.makeStr(u'setattr(self, n, {})')), rel.py.makeStatement(uf.makeStr(u'setattr(self, "hash" + n, {})'))]))])), rel.py.makeCompound(uf.makeStr(u'def rebuild(self)'), uf.makeList([rel.py.makeCompound(rel.builtin.makeConcat(uf.makeStr(u'for n in unrolled'), uf.makeList([vN, uf.makeStr(u'Cons')])), uf.makeList([rel.py.makeStatement(uf.makeStr(u'rebuildRel(self.uf, getattr(self, n))')), rel.py.makeStatement(uf.makeStr(u'rebuildHash(self.uf, getattr(self, "hash" + n))'))]))]))]), rel.builtin.makeFlatten(vT)]))), rel.py.makeStatement(rel.builtin.makeConcat(uf.makeStr(u'unrolled'), uf.makeList([vN, uf.makeStr(u'Cons = unrolling_iterable('), vN, uf.makeStr(u'Cons[:])')]))), rel.py.makeStatement(rel.builtin.makeConcat(uf.makeStr(u'allRels.append(("'), uf.makeList([vN, uf.makeStr(u'", '), vN, uf.makeStr(u'Rels))')])))]))
            q.append(vRoot)
            pass
        except NoResults: continue
        pass
    return len(q)
    pass
@rewrite("builtin", "py", "rules", "peg", "char", "zephyr")
def zProd(uf, rel):
    q = []
    beEmpty = uf.makeList([])
    for (vRoot, vN, vFs) in rel.zephyr.Product:
        try:
            if len(uf.findList(beEmpty)): continue
            uf.union(vRoot, uf.makeList([rel.py.makeStatement(rel.builtin.makeConcat(uf.makeStr(u'# product '), uf.makeList([vN])))]))
            q.append(vRoot)
            pass
        except NoResults: continue
        pass
    return len(q)
    pass
@rewrite("builtin", "py", "rules", "peg", "char", "zephyr")
def zSum(uf, rel):
    q = []
    beEmpty = uf.makeList([])
    for (vRoot, vN, vA, vC, vCs) in rel.zephyr.Sum:
        try:
            if len(uf.findList(beEmpty)): continue
            uf.union(vRoot, rel.builtin.makeFlatten(uf.makeList([vC, rel.builtin.makeFlatten(vCs)])))
            q.append(vRoot)
            pass
        except NoResults: continue
        pass
    return len(q)
    pass
@rewrite("builtin", "py", "rules", "peg", "char", "zephyr")
def zConF(uf, rel):
    q = []
    beEmpty = uf.makeList([])
    for (vRoot, vT, vA) in rel.zephyr.Con:
        try:
            if len(uf.findList(beEmpty)): continue
            uf.union(vRoot, uf.makeList([rel.py.makeStatement(rel.builtin.makeConcat(uf.makeStr(u'cons.append("'), uf.makeList([vT, uf.makeStr(u'")')]))), rel.py.makeCompound(rel.builtin.makeConcat(uf.makeStr(u'def make'), uf.makeList([vT, uf.makeStr(u'(self, '), rel.builtin.makeJoin(uf.makeStr(u", "), vA), uf.makeStr(u')')])), uf.makeList([rel.py.makeStatement(rel.builtin.makeConcat(uf.makeStr(u'self.dirty'), uf.makeList([vT, uf.makeStr(u' = True')]))), rel.py.makeStatement(rel.builtin.makeConcat(uf.makeStr(u'k = ('), uf.makeList([rel.builtin.makeJoin(uf.makeStr(u", "), vA), uf.makeStr(u')')]))), rel.py.makeStatement(rel.builtin.makeConcat(uf.makeStr(u'if k in self.hash'), uf.makeList([vT, uf.makeStr(u': return self.hash'), vT, uf.makeStr(u'[k]')]))), rel.py.makeStatement(uf.makeStr(u'rv = self.uf.make()')), rel.py.makeStatement(rel.builtin.makeConcat(uf.makeStr(u'self.'), uf.makeList([vT, uf.makeStr(u'[(rv, '), rel.builtin.makeJoin(uf.makeStr(u", "), vA), uf.makeStr(u')] = None')]))), rel.py.makeStatement(rel.builtin.makeConcat(uf.makeStr(u'self.hash'), uf.makeList([vT, uf.makeStr(u'[k] = rv')]))), rel.py.makeRet(uf.makeStr(u'rv'))]))]))
            q.append(vRoot)
            pass
        except NoResults: continue
        pass
    return len(q)
    pass
@rewrite("builtin", "py", "rules", "peg", "char", "zephyr")
def zOpt(uf, rel):
    q = []
    beEmpty = uf.makeList([])
    for (vRoot, vT, vN) in rel.zephyr.Option:
        try:
            if len(uf.findList(beEmpty)): continue
            uf.union(vRoot, vN)
            q.append(vRoot)
            pass
        except NoResults: continue
        pass
    return len(q)
    pass
@rewrite("builtin", "py", "rules", "peg", "char", "zephyr")
def zSeq(uf, rel):
    q = []
    beEmpty = uf.makeList([])
    for (vRoot, vT, vN) in rel.zephyr.Sequence:
        try:
            if len(uf.findList(beEmpty)): continue
            uf.union(vRoot, vN)
            q.append(vRoot)
            pass
        except NoResults: continue
        pass
    return len(q)
    pass
@rewrite("builtin", "py", "rules", "peg", "char", "zephyr")
def zId(uf, rel):
    q = []
    beEmpty = uf.makeList([])
    for (vRoot, vT, vN) in rel.zephyr.Id:
        try:
            if len(uf.findList(beEmpty)): continue
            uf.union(vRoot, vN)
            q.append(vRoot)
            pass
        except NoResults: continue
        pass
    return len(q)
    pass
@rewrite("builtin", "py", "rules", "peg", "char", "zephyr")
def charAny(uf, rel):
    q = []
    beEmpty = uf.makeList([])
    for (vRoot, ) in rel.char.Any:
        try:
            if len(uf.findList(beEmpty)): continue
            uf.union(vRoot, uf.makeStr(u'True'))
            q.append(vRoot)
            pass
        except NoResults: continue
        pass
    return len(q)
    pass
@rewrite("builtin", "py", "rules", "peg", "char", "zephyr")
def charExactly(uf, rel):
    q = []
    beEmpty = uf.makeList([])
    for (vRoot, vC) in rel.char.Exactly:
        try:
            if len(uf.findList(beEmpty)): continue
            uf.union(vRoot, rel.builtin.makeConcat(uf.makeStr(u'c == '), uf.makeList([vC])))
            q.append(vRoot)
            pass
        except NoResults: continue
        pass
    return len(q)
    pass
@rewrite("builtin", "py", "rules", "peg", "char", "zephyr")
def charRange(uf, rel):
    q = []
    beEmpty = uf.makeList([])
    for (vRoot, vL, vU) in rel.char.Range:
        try:
            if len(uf.findList(beEmpty)): continue
            uf.union(vRoot, rel.builtin.makeConcat(vL, uf.makeList([uf.makeStr(u' <= c <= '), vU])))
            q.append(vRoot)
            pass
        except NoResults: continue
        pass
    return len(q)
    pass
@rewrite("builtin", "py", "rules", "peg", "char", "zephyr")
def charCall(uf, rel):
    q = []
    beEmpty = uf.makeList([])
    for (vRoot, vN) in rel.char.Call:
        try:
            if len(uf.findList(beEmpty)): continue
            uf.union(vRoot, rel.builtin.makeConcat(uf.makeStr(u'self.cls'), uf.makeList([vN, uf.makeStr(u'(c)')])))
            q.append(vRoot)
            pass
        except NoResults: continue
        pass
    return len(q)
    pass
@rewrite("builtin", "py", "rules", "peg", "char", "zephyr")
def charComp(uf, rel):
    q = []
    beEmpty = uf.makeList([])
    for (vRoot, vS) in rel.char.Complement:
        try:
            if len(uf.findList(beEmpty)): continue
            uf.union(vRoot, rel.builtin.makeConcat(uf.makeStr(u'not ('), uf.makeList([vS, uf.makeStr(u')')])))
            q.append(vRoot)
            pass
        except NoResults: continue
        pass
    return len(q)
    pass
@rewrite("builtin", "py", "rules", "peg", "char", "zephyr")
def charEither(uf, rel):
    q = []
    beEmpty = uf.makeList([])
    for (vRoot, vL, vR) in rel.char.Either:
        try:
            if len(uf.findList(beEmpty)): continue
            uf.union(vRoot, rel.builtin.makeConcat(uf.makeStr(u'('), uf.makeList([vL, uf.makeStr(u') or ('), vR, uf.makeStr(u')')])))
            q.append(vRoot)
            pass
        except NoResults: continue
        pass
    return len(q)
    pass
@rewrite("builtin", "py", "rules", "peg", "char", "zephyr")
def rPattIg(uf, rel):
    q = []
    beEmpty = uf.makeList([])
    for (vRoot, ) in rel.rules.IgnorePatt:
        try:
            if len(uf.findList(beEmpty)): continue
            uf.union(vRoot, uf.makeStr(u'_'))
            q.append(vRoot)
            pass
        except NoResults: continue
        pass
    return len(q)
    pass
@rewrite("builtin", "py", "rules", "peg", "char", "zephyr")
def rPattV(uf, rel):
    q = []
    beEmpty = uf.makeList([])
    for (vRoot, vN) in rel.rules.VarPatt:
        try:
            if len(uf.findList(beEmpty)): continue
            uf.union(vRoot, rel.builtin.makeConcat(uf.makeStr(u'v'), uf.makeList([vN])))
            q.append(vRoot)
            pass
        except NoResults: continue
        pass
    return len(q)
    pass
@rewrite("builtin", "py", "rules", "peg", "char", "zephyr")
def rPattS(uf, rel):
    q = []
    beEmpty = uf.makeList([])
    for (vRoot, vS) in rel.rules.StrPatt:
        try:
            if len(uf.findList(beEmpty)): continue
            uf.union(vRoot, rel.builtin.makeConcat(uf.makeStr(u'u'), uf.makeList([uf.makeStr(unichr(39)), vS, uf.makeStr(unichr(39))])))
            q.append(vRoot)
            pass
        except NoResults: continue
        pass
    return len(q)
    pass
@rewrite("builtin", "py", "rules", "peg", "char", "zephyr")
def rPattSt(uf, rel):
    q = []
    beEmpty = uf.makeList([])
    for (vRoot, vNs, vF, vVs) in rel.rules.StructPatt:
        try:
            if len(uf.findList(beEmpty)): continue
            uf.union(vRoot, rel.builtin.makeConcat(uf.makeStr(u'for (vRoot, '), uf.makeList([rel.builtin.makeJoin(uf.makeStr(u", "), vVs), uf.makeStr(u') in rel.'), vNs, uf.makeStr(u'.'), vF])))
            q.append(vRoot)
            pass
        except NoResults: continue
        pass
    return len(q)
    pass
@rewrite("builtin", "py", "rules", "peg", "char", "zephyr")
def rPattLE(uf, rel):
    q = []
    beEmpty = uf.makeList([])
    for (vRoot, ) in rel.rules.EmptyListPatt:
        try:
            if len(uf.findList(beEmpty)): continue
            uf.union(vRoot, uf.makeStr(u'beEmpty'))
            q.append(vRoot)
            pass
        except NoResults: continue
        pass
    return len(q)
    pass
@rewrite("builtin", "py", "rules", "peg", "char", "zephyr")
def rPattLL(uf, rel):
    q = []
    beEmpty = uf.makeList([])
    for (vRoot, vPs) in rel.rules.ListPatt:
        try:
            if len(uf.findList(beEmpty)): continue
            uf.union(vRoot, rel.builtin.makeJoin(uf.makeStr(u", "), vPs))
            q.append(vRoot)
            pass
        except NoResults: continue
        pass
    return len(q)
    pass
@rewrite("builtin", "py", "rules", "peg", "char", "zephyr")
def rPattLH(uf, rel):
    q = []
    beEmpty = uf.makeList([])
    for (vRoot, vH, vPs) in rel.rules.ListHeadPatt:
        try:
            if len(uf.findList(beEmpty)): continue
            uf.union(vRoot, rel.builtin.makeConcat(uf.makeStr(u'listhead'), uf.makeList([vH, rel.builtin.makeJoin(uf.makeStr(u", "), vPs)])))
            q.append(vRoot)
            pass
        except NoResults: continue
        pass
    return len(q)
    pass
@rewrite("builtin", "py", "rules", "peg", "char", "zephyr")
def rPattLT(uf, rel):
    q = []
    beEmpty = uf.makeList([])
    for (vRoot, vT, vPs) in rel.rules.ListTailPatt:
        try:
            if len(uf.findList(beEmpty)): continue
            uf.union(vRoot, rel.builtin.makeConcat(uf.makeStr(u'listtail'), uf.makeList([vT, rel.builtin.makeJoin(uf.makeStr(u", "), vPs)])))
            q.append(vRoot)
            pass
        except NoResults: continue
        pass
    return len(q)
    pass
@rewrite("builtin", "py", "rules", "peg", "char", "zephyr")
def rPattLM(uf, rel):
    q = []
    beEmpty = uf.makeList([])
    for (vRoot, vH, vT, vPs) in rel.rules.ListMidPatt:
        try:
            if len(uf.findList(beEmpty)): continue
            uf.union(vRoot, rel.builtin.makeConcat(uf.makeStr(u'listmid'), uf.makeList([vH, vT, rel.builtin.makeJoin(uf.makeStr(u", "), vPs)])))
            q.append(vRoot)
            pass
        except NoResults: continue
        pass
    return len(q)
    pass
@rewrite("builtin", "py", "rules", "peg", "char", "zephyr")
def rProdV(uf, rel):
    q = []
    beEmpty = uf.makeList([])
    for (vRoot, vName) in rel.rules.VarProd:
        try:
            if len(uf.findList(beEmpty)): continue
            uf.union(vRoot, rel.builtin.makeConcat(uf.makeStr(u'v'), uf.makeList([vName])))
            q.append(vRoot)
            pass
        except NoResults: continue
        pass
    return len(q)
    pass
@rewrite("builtin", "py", "rules", "peg", "char", "zephyr")
def rProdC(uf, rel):
    q = []
    beEmpty = uf.makeList([])
    for (vRoot, vName) in rel.rules.ConstProd:
        try:
            if len(uf.findList(beEmpty)): continue
            uf.union(vRoot, rel.builtin.makeConcat(uf.makeStr(u'rel.const'), uf.makeList([vName])))
            q.append(vRoot)
            pass
        except NoResults: continue
        pass
    return len(q)
    pass
@rewrite("builtin", "py", "rules", "peg", "char", "zephyr")
def rProdS(uf, rel):
    q = []
    beEmpty = uf.makeList([])
    for (vRoot, vS) in rel.rules.StrProd:
        try:
            if len(uf.findList(beEmpty)): continue
            uf.union(vRoot, rel.builtin.makeConcat(uf.makeStr(u'uf.makeStr(u'), uf.makeList([uf.makeStr(unichr(39)), vS, uf.makeStr(unichr(39)), uf.makeStr(u')')])))
            q.append(vRoot)
            pass
        except NoResults: continue
        pass
    return len(q)
    pass
@rewrite("builtin", "py", "rules", "peg", "char", "zephyr")
def rProdCh(uf, rel):
    q = []
    beEmpty = uf.makeList([])
    for (vRoot, vN) in rel.rules.CharProd:
        try:
            if len(uf.findList(beEmpty)): continue
            uf.union(vRoot, rel.builtin.makeConcat(uf.makeStr(u'uf.makeStr(unichr('), uf.makeList([vN, uf.makeStr(u'))')])))
            q.append(vRoot)
            pass
        except NoResults: continue
        pass
    return len(q)
    pass
@rewrite("builtin", "py", "rules", "peg", "char", "zephyr")
def rProdSt(uf, rel):
    q = []
    beEmpty = uf.makeList([])
    for (vRoot, vNs, vF, vPs) in rel.rules.StructProd:
        try:
            if len(uf.findList(beEmpty)): continue
            uf.union(vRoot, rel.builtin.makeConcat(uf.makeStr(u'rel.'), uf.makeList([vNs, uf.makeStr(u'.make'), vF, uf.makeStr(u'('), rel.builtin.makeJoin(uf.makeStr(u", "), vPs), uf.makeStr(u')')])))
            q.append(vRoot)
            pass
        except NoResults: continue
        pass
    return len(q)
    pass
@rewrite("builtin", "py", "rules", "peg", "char", "zephyr")
def rProdL(uf, rel):
    q = []
    beEmpty = uf.makeList([])
    for (vRoot, vPs) in rel.rules.ListProd:
        try:
            if len(uf.findList(beEmpty)): continue
            uf.union(vRoot, rel.builtin.makeConcat(uf.makeStr(u'uf.makeList(['), uf.makeList([rel.builtin.makeJoin(uf.makeStr(u", "), vPs), uf.makeStr(u'])')])))
            q.append(vRoot)
            pass
        except NoResults: continue
        pass
    return len(q)
    pass
@rewrite("builtin", "py", "rules", "peg", "char", "zephyr")
def rProdLH(uf, rel):
    q = []
    beEmpty = uf.makeList([])
    for (vRoot, vH, vPs) in rel.rules.ListHeadProd:
        try:
            if len(uf.findList(beEmpty)): continue
            uf.union(vRoot, rel.builtin.makeConcat(uf.makeStr(u'uf.makeList(uf.findList('), uf.makeList([vH, uf.makeStr(u') + ['), rel.builtin.makeJoin(uf.makeStr(u", "), vPs), uf.makeStr(u'])')])))
            q.append(vRoot)
            pass
        except NoResults: continue
        pass
    return len(q)
    pass
@rewrite("builtin", "py", "rules", "peg", "char", "zephyr")
def rProdLT(uf, rel):
    q = []
    beEmpty = uf.makeList([])
    for (vRoot, vT, vPs) in rel.rules.ListTailProd:
        try:
            if len(uf.findList(beEmpty)): continue
            uf.union(vRoot, rel.builtin.makeConcat(uf.makeStr(u'uf.makeList(['), uf.makeList([rel.builtin.makeJoin(uf.makeStr(u", "), vPs), uf.makeStr(u'] + uf.findList('), vT, uf.makeStr(u'))')])))
            q.append(vRoot)
            pass
        except NoResults: continue
        pass
    return len(q)
    pass
@rewrite("builtin", "py", "rules", "peg", "char", "zephyr")
def rProdLM(uf, rel):
    q = []
    beEmpty = uf.makeList([])
    for (vRoot, vH, vT, vPs) in rel.rules.ListMidProd:
        try:
            if len(uf.findList(beEmpty)): continue
            uf.union(vRoot, rel.builtin.makeConcat(uf.makeStr(u'uf.makeList(uf.findList('), uf.makeList([vH, uf.makeStr(u') + ['), rel.builtin.makeJoin(uf.makeStr(u", "), vPs), uf.makeStr(u'] + uf.findList('), vT, uf.makeStr(u'))')])))
            q.append(vRoot)
            pass
        except NoResults: continue
        pass
    return len(q)
    pass
@rewrite("builtin", "py", "rules", "peg", "char", "zephyr")
def rProdOF(uf, rel):
    q = []
    beEmpty = uf.makeList([])
    for (vRoot, vP) in rel.rules.FlattenOp:
        try:
            if len(uf.findList(beEmpty)): continue
            uf.union(vRoot, rel.builtin.makeConcat(uf.makeStr(u'rel.builtin.makeFlatten('), uf.makeList([vP, uf.makeStr(u')')])))
            q.append(vRoot)
            pass
        except NoResults: continue
        pass
    return len(q)
    pass
@rewrite("builtin", "py", "rules", "peg", "char", "zephyr")
def rProdOL(uf, rel):
    q = []
    beEmpty = uf.makeList([])
    for (vRoot, vP) in rel.rules.LengthOp:
        try:
            if len(uf.findList(beEmpty)): continue
            uf.union(vRoot, rel.builtin.makeConcat(uf.makeStr(u'rel.builtin.makeLength('), uf.makeList([vP, uf.makeStr(u')')])))
            q.append(vRoot)
            pass
        except NoResults: continue
        pass
    return len(q)
    pass
@rewrite("builtin", "py", "rules", "peg", "char", "zephyr")
def rProdOJ(uf, rel):
    q = []
    beEmpty = uf.makeList([])
    for (vRoot, vS, vP) in rel.rules.JoinOp:
        try:
            if len(uf.findList(beEmpty)): continue
            uf.union(vRoot, rel.builtin.makeConcat(uf.makeStr(u'rel.builtin.makeJoin(uf.makeStr(u"'), uf.makeList([vS, uf.makeStr(u'"), '), vP, uf.makeStr(u')')])))
            q.append(vRoot)
            pass
        except NoResults: continue
        pass
    return len(q)
    pass
@rewrite("builtin", "py", "rules", "peg", "char", "zephyr")
def rProdOE(uf, rel):
    q = []
    beEmpty = uf.makeList([])
    for (vRoot, vP, beEmpty) in rel.rules.ConcatOp:
        try:
            if len(uf.findList(beEmpty)): continue
            uf.union(vRoot, vP)
            q.append(vRoot)
            pass
        except NoResults: continue
        pass
    return len(q)
    pass
@rewrite("builtin", "py", "rules", "peg", "char", "zephyr")
def rProdOC(uf, rel):
    q = []
    beEmpty = uf.makeList([])
    for (vRoot, vP, vPs) in rel.rules.ConcatOp:
        try:
            if len(uf.findList(beEmpty)): continue
            uf.union(vRoot, rel.builtin.makeConcat(uf.makeStr(u'rel.builtin.makeConcat('), uf.makeList([vP, uf.makeStr(u', uf.makeList(['), rel.builtin.makeJoin(uf.makeStr(u", "), vPs), uf.makeStr(u']))')])))
            q.append(vRoot)
            pass
        except NoResults: continue
        pass
    return len(q)
    pass
@rewrite("builtin", "py", "rules", "peg", "char", "zephyr")
def rRule(uf, rel):
    q = []
    beEmpty = uf.makeList([])
    for (vRoot, vName, vRootFor, vPs) in rel.rules.Rewrite:
        try:
            if len(uf.findList(beEmpty)): continue
            uf.union(vRoot, uf.makeList([rel.py.makeStatement(uf.makeStr(u'@rewrite("builtin", "py", "rules", "peg", "char", "zephyr")')), rel.py.makeCompound(rel.builtin.makeConcat(uf.makeStr(u'def '), uf.makeList([vName, uf.makeStr(u'(uf, rel)')])), uf.makeList([rel.py.makeStatement(uf.makeStr(u'q = []')), rel.py.makeStatement(uf.makeStr(u'beEmpty = uf.makeList([])')), rel.py.makeCompound(vRootFor, uf.makeList([rel.py.makeCompound(uf.makeStr(u'try'), uf.makeList([rel.py.makeStatement(uf.makeStr(u'if len(uf.findList(beEmpty)): continue')), rel.py.makeStatement(rel.builtin.makeConcat(uf.makeStr(u'uf.union(vRoot, '), uf.makeList([rel.builtin.makeJoin(uf.makeStr(u", "), vPs), uf.makeStr(u')')]))), rel.py.makeStatement(uf.makeStr(u'q.append(vRoot)'))])), rel.py.makeStatement(uf.makeStr(u'except NoResults: continue'))])), rel.py.makeRet(uf.makeStr(u'len(q)'))]))]))
            q.append(vRoot)
            pass
        except NoResults: continue
        pass
    return len(q)
    pass
@rewrite("builtin", "py", "rules", "peg", "char", "zephyr")
def rLet(uf, rel):
    q = []
    beEmpty = uf.makeList([])
    for (vRoot, vName, vP) in rel.rules.Let:
        try:
            if len(uf.findList(beEmpty)): continue
            uf.union(vRoot, uf.makeList([rel.py.makeStatement(uf.makeStr(u'@let')), rel.py.makeStatement(rel.builtin.makeConcat(uf.makeStr(u'def let'), uf.makeList([vName, uf.makeStr(u'(uf, rel): rel.const'), vName, uf.makeStr(u' = '), vP])))]))
            q.append(vRoot)
            pass
        except NoResults: continue
        pass
    return len(q)
    pass
def target(driver, *args):
    driver.exe_name = "ZADDY".lower() + "c"
    return main, None
    pass
class ZADDYParser(object):
    def __init__(self, s, uf):
        self.s = s; self.uf = uf
        self.lastMatch = []
        for name in unrolledRels: setattr(self, name, frozenRels[name](uf))
        for l in unrolledLets: l(uf, self)
        pass
    def parse(self):
        return self.parseZADDY(0)
        pass
    def clsWhitespace(self, c):
        return (c == 9) or ((c == 10) or ((c == 13) or (c == 32)))
        pass
    def clsDigit(self, c):
        return 48 <= c <= 57
        pass
    def clsUpper(self, c):
        return 65 <= c <= 90
        pass
    def clsLower(self, c):
        return 97 <= c <= 122
        pass
    def clsAlpha(self, c):
        return (self.clsUpper(c)) or (self.clsLower(c))
        pass
    def clsAlphanumeric(self, c):
        return (self.clsAlpha(c)) or (self.clsDigit(c))
        pass
    def clsQuote(self, c):
        return c == 39
        pass
    def clsQuoted(self, c):
        return not ((c == 10) or ((c == 13) or (c == 39)))
        pass
    def clsEllipsis(self, c):
        return c == 8230
        pass
    def parseWS(self, i):
        if i >= len(self.s): raise ParseError("no reason")
        start = i; assert start >= 0
        while i < len(self.s) and self.clsWhitespace(ord(self.s[i])): i += 1
        rv = self.uf.makeStr(self.s[start:i])
        self.lastMatch.append((u"TOKEN WS", start, i))
        return i, rv
        pass
    def parseNumber(self, i):
        if i >= len(self.s): raise ParseError("no reason")
        start = i; assert start >= 0
        if i >= len(self.s) or not self.clsDigit(ord(self.s[i])): raise ParseError("no reason")
        while i < len(self.s) and self.clsDigit(ord(self.s[i])): i += 1
        rv = self.uf.makeStr(self.s[start:i])
        self.lastMatch.append((u"TOKEN Number", start, i))
        return i, rv
        pass
    def parseId(self, i):
        if i >= len(self.s): raise ParseError("no reason")
        start = i; assert start >= 0
        if i >= len(self.s) or not self.clsAlpha(ord(self.s[i])): raise ParseError("no reason")
        i += 1
        while i < len(self.s) and self.clsAlphanumeric(ord(self.s[i])): i += 1
        rv = self.uf.makeStr(self.s[start:i])
        self.lastMatch.append((u"TOKEN Id", start, i))
        return i, rv
        pass
    def parsePVar(self, i):
        if i >= len(self.s): raise ParseError("no reason")
        start = i; assert start >= 0
        if i >= len(self.s) or not self.clsUpper(ord(self.s[i])): raise ParseError("no reason")
        i += 1
        while i < len(self.s) and self.clsAlphanumeric(ord(self.s[i])): i += 1
        rv = self.uf.makeStr(self.s[start:i])
        self.lastMatch.append((u"TOKEN PVar", start, i))
        return i, rv
        pass
    def parsePConst(self, i):
        if i >= len(self.s): raise ParseError("no reason")
        start = i; assert start >= 0
        if i >= len(self.s) or not self.clsLower(ord(self.s[i])): raise ParseError("no reason")
        while i < len(self.s) and self.clsLower(ord(self.s[i])): i += 1
        rv = self.uf.makeStr(self.s[start:i])
        self.lastMatch.append((u"TOKEN PConst", start, i))
        return i, rv
        pass
    def parseZTId(self, i):
        if i >= len(self.s): raise ParseError("no reason")
        start = i; assert start >= 0
        if i >= len(self.s) or not self.clsLower(ord(self.s[i])): raise ParseError("no reason")
        i += 1
        while i < len(self.s) and self.clsAlphanumeric(ord(self.s[i])): i += 1
        rv = self.uf.makeStr(self.s[start:i])
        self.lastMatch.append((u"TOKEN ZTId", start, i))
        return i, rv
        pass
    def parseZCId(self, i):
        if i >= len(self.s): raise ParseError("no reason")
        start = i; assert start >= 0
        if i >= len(self.s) or not self.clsUpper(ord(self.s[i])): raise ParseError("no reason")
        i += 1
        while i < len(self.s) and self.clsAlphanumeric(ord(self.s[i])): i += 1
        rv = self.uf.makeStr(self.s[start:i])
        self.lastMatch.append((u"TOKEN ZCId", start, i))
        return i, rv
        pass
    def parseQuote(self, i):
        if i >= len(self.s): raise ParseError("no reason")
        start = i; assert start >= 0
        if i >= len(self.s) or not self.clsQuote(ord(self.s[i])): raise ParseError("no reason")
        i += 1
        rv = self.uf.makeStr(self.s[start:i])
        self.lastMatch.append((u"TOKEN Quote", start, i))
        return i, rv
        pass
    def parseQuoted(self, i):
        if i >= len(self.s): raise ParseError("no reason")
        start = i; assert start >= 0
        while i < len(self.s) and self.clsQuoted(ord(self.s[i])): i += 1
        rv = self.uf.makeStr(self.s[start:i])
        self.lastMatch.append((u"TOKEN Quoted", start, i))
        return i, rv
        pass
    def parseEllipsis(self, i):
        if i >= len(self.s): raise ParseError("no reason")
        start = i; assert start >= 0
        if i >= len(self.s) or not self.clsEllipsis(ord(self.s[i])): raise ParseError("no reason")
        i += 1
        rv = self.uf.makeStr(self.s[start:i])
        self.lastMatch.append((u"TOKEN Ellipsis", start, i))
        return i, rv
        pass
    @cached
    def parseSTRING(self, i):
        rel = self; uf = self.uf; st = []
        i, rv = self.parseWS(i)
        i, rv = self.parseQuote(i)
        i, rv = self.parseQuoted(i)
        vQ = rv
        i, rv = self.parseQuote(i)
        rv = vQ
        return i, rv
        pass
    @cached
    def parseID(self, i):
        rel = self; uf = self.uf; st = []
        i, rv = self.parseWS(i)
        i, rv = self.parseId(i)
        return i, rv
        pass
    @cached
    def parseSIGNATURE(self, i):
        rel = self; uf = self.uf; st = []
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError("no reason")
        assert i >= 0
        if self.s[i:i + 10] != u".signature": raise ParseError("no reason")
        self.lastMatch.append((u"TOKEN .signature", i, i + 10))
        rv = self.uf.makeStr(u".signature"); i += 10
        i, rv = self.parseID(i)
        vName = rv
        rvs = []
        while True:
            st.append(i)
            try:
                i, rv = self.parseZTY(i)
                rvs.append(rv)
            except ParseError as pe:
                i = st.pop()
                break
            pass
        rv = rel.uf.makeList(rvs)
        vTys = rv
        rv = rel.zephyr.makeSignature(vName, rel.builtin.makeFlatten(vTys))
        return i, rv
        pass
    @cached
    def parseZTY(self, i):
        rel = self; uf = self.uf; st = []
        i, rv = self.parseID(i)
        vName = rv
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError("no reason")
        assert i >= 0
        if self.s[i:i + 1] != u"=": raise ParseError("no reason")
        self.lastMatch.append((u"TOKEN =", i, i + 1))
        rv = self.uf.makeStr(u"="); i += 1
        st.append(i)
        try:
            i, rv = self.parseFIELDS(i)
            vFs = rv
            rv = uf.makeList([rel.zephyr.makeProduct(vName, vFs)])
        except ParseError as pe:
            i = st.pop()
            i, rv = self.parseZCON(i)
            vCon = rv
            rvs = []
            while True:
                st.append(i)
                try:
                    while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                    if i >= len(self.s): raise ParseError("no reason")
                    assert i >= 0
                    if self.s[i:i + 1] != u"|": raise ParseError("no reason")
                    self.lastMatch.append((u"TOKEN |", i, i + 1))
                    rv = self.uf.makeStr(u"|"); i += 1
                    i, rv = self.parseZCON(i)
                    rvs.append(rv)
                except ParseError as pe:
                    i = st.pop()
                    break
                pass
            rv = rel.uf.makeList(rvs)
            vCons = rv
            st.append(i)
            try:
                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                if i >= len(self.s): raise ParseError("no reason")
                assert i >= 0
                if self.s[i:i + 10] != u"attributes": raise ParseError("no reason")
                self.lastMatch.append((u"TOKEN attributes", i, i + 10))
                rv = self.uf.makeStr(u"attributes"); i += 10
                i, rv = self.parseFIELDS(i)
                vAttrs = rv
                rv = uf.makeList([rel.zephyr.makeSum(vName, vAttrs, vCon, vCons)])
            except ParseError as pe:
                i = st.pop()
                rv = uf.makeList([rel.zephyr.makeSum(vName, uf.makeList([]), vCon, vCons)])
        return i, rv
        pass
    @cached
    def parseZCON(self, i):
        rel = self; uf = self.uf; st = []
        i, rv = self.parseWS(i)
        st.append(i)
        try:
            i, rv = self.parseZCId(i)
            vTag = rv
            i, rv = self.parseFIELDS(i)
            vArgs = rv
            rv = rel.zephyr.makeCon(vTag, vArgs)
        except ParseError as pe:
            i = st.pop()
            i, rv = self.parseZCId(i)
            vTag = rv
            rv = rel.zephyr.makeCon(vTag, uf.makeList([]))
        return i, rv
        pass
    @cached
    def parseFIELDS(self, i):
        rel = self; uf = self.uf; st = []
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError("no reason")
        assert i >= 0
        if self.s[i:i + 1] != u"(": raise ParseError("no reason")
        self.lastMatch.append((u"TOKEN (", i, i + 1))
        rv = self.uf.makeStr(u"("); i += 1
        i, rv = self.parseFIELD(i)
        vF = rv
        rvs = []
        while True:
            st.append(i)
            try:
                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                if i >= len(self.s): raise ParseError("no reason")
                assert i >= 0
                if self.s[i:i + 1] != u",": raise ParseError("no reason")
                self.lastMatch.append((u"TOKEN ,", i, i + 1))
                rv = self.uf.makeStr(u","); i += 1
                i, rv = self.parseFIELD(i)
                rvs.append(rv)
            except ParseError as pe:
                i = st.pop()
                break
            pass
        rv = rel.uf.makeList(rvs)
        vFs = rv
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError("no reason")
        assert i >= 0
        if self.s[i:i + 1] != u")": raise ParseError("no reason")
        self.lastMatch.append((u"TOKEN )", i, i + 1))
        rv = self.uf.makeStr(u")"); i += 1
        rv = rel.builtin.makeFlatten(uf.makeList([uf.makeList([vF]), vFs]))
        return i, rv
        pass
    @cached
    def parseFIELD(self, i):
        rel = self; uf = self.uf; st = []
        i, rv = self.parseWS(i)
        st.append(i)
        try:
            i, rv = self.parseZTId(i)
            vTy = rv
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError("no reason")
            assert i >= 0
            if self.s[i:i + 1] != u"?": raise ParseError("no reason")
            self.lastMatch.append((u"TOKEN ?", i, i + 1))
            rv = self.uf.makeStr(u"?"); i += 1
            i, rv = self.parseID(i)
            vName = rv
            rv = rel.zephyr.makeOption(vTy, vName)
        except ParseError as pe:
            i = st.pop()
            st.append(i)
            try:
                i, rv = self.parseZTId(i)
                vTy = rv
                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                if i >= len(self.s): raise ParseError("no reason")
                assert i >= 0
                if self.s[i:i + 1] != u"*": raise ParseError("no reason")
                self.lastMatch.append((u"TOKEN *", i, i + 1))
                rv = self.uf.makeStr(u"*"); i += 1
                i, rv = self.parseID(i)
                vName = rv
                rv = rel.zephyr.makeSequence(vTy, vName)
            except ParseError as pe:
                i = st.pop()
                i, rv = self.parseZTId(i)
                vTy = rv
                i, rv = self.parseID(i)
                vName = rv
                rv = rel.zephyr.makeId(vTy, vName)
        return i, rv
        pass
    @cached
    def parseRULES(self, i):
        rel = self; uf = self.uf; st = []
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError("no reason")
        assert i >= 0
        if self.s[i:i + 6] != u".rules": raise ParseError("no reason")
        self.lastMatch.append((u"TOKEN .rules", i, i + 6))
        rv = self.uf.makeStr(u".rules"); i += 6
        rvs = []
        while True:
            st.append(i)
            try:
                st.append(i)
                try:
                    i, rv = self.parseCHRULE(i)
                except ParseError as pe:
                    i = st.pop()
                    i, rv = self.parseCHLET(i)
                rvs.append(rv)
            except ParseError as pe:
                i = st.pop()
                break
            pass
        rv = rel.uf.makeList(rvs)
        vHs = rv
        rv = rel.builtin.makeFlatten(vHs)
        return i, rv
        pass
    @cached
    def parseCHRULE(self, i):
        rel = self; uf = self.uf; st = []
        i, rv = self.parseID(i)
        vName = rv
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError("no reason")
        assert i >= 0
        if self.s[i:i + 1] != u"@": raise ParseError("no reason")
        self.lastMatch.append((u"TOKEN @", i, i + 1))
        rv = self.uf.makeStr(u"@"); i += 1
        i, rv = self.parseWS(i)
        i, rv = self.parseCPATT(i)
        vRoot = rv
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError("no reason")
        assert i >= 0
        if self.s[i:i + 3] != u"==>": raise ParseError("no reason")
        self.lastMatch.append((u"TOKEN ==>", i, i + 3))
        rv = self.uf.makeStr(u"==>"); i += 3
        i, rv = self.parseCPRODS(i)
        vProds = rv
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError("no reason")
        assert i >= 0
        if self.s[i:i + 1] != u";": raise ParseError("no reason")
        self.lastMatch.append((u"TOKEN ;", i, i + 1))
        rv = self.uf.makeStr(u";"); i += 1
        rv = rel.rules.makeRewrite(vName, vRoot, vProds)
        return i, rv
        pass
    @cached
    def parseCHLET(self, i):
        rel = self; uf = self.uf; st = []
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError("no reason")
        assert i >= 0
        if self.s[i:i + 3] != u"let": raise ParseError("no reason")
        self.lastMatch.append((u"TOKEN let", i, i + 3))
        rv = self.uf.makeStr(u"let"); i += 3
        i, rv = self.parseID(i)
        vName = rv
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError("no reason")
        assert i >= 0
        if self.s[i:i + 2] != u":=": raise ParseError("no reason")
        self.lastMatch.append((u"TOKEN :=", i, i + 2))
        rv = self.uf.makeStr(u":="); i += 2
        i, rv = self.parseCPROD1(i)
        vP = rv
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError("no reason")
        assert i >= 0
        if self.s[i:i + 1] != u";": raise ParseError("no reason")
        self.lastMatch.append((u"TOKEN ;", i, i + 1))
        rv = self.uf.makeStr(u";"); i += 1
        rv = rel.rules.makeLet(vName, vP)
        return i, rv
        pass
    @cached
    def parseCPATTS(self, i):
        rel = self; uf = self.uf; st = []
        i, rv = self.parseWS(i)
        i, rv = self.parseCPATT(i)
        vP = rv
        rvs = []
        while True:
            st.append(i)
            try:
                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                if i >= len(self.s): raise ParseError("no reason")
                assert i >= 0
                if self.s[i:i + 1] != u",": raise ParseError("no reason")
                self.lastMatch.append((u"TOKEN ,", i, i + 1))
                rv = self.uf.makeStr(u","); i += 1
                i, rv = self.parseWS(i)
                i, rv = self.parseCPATT(i)
                rvs.append(rv)
            except ParseError as pe:
                i = st.pop()
                break
            pass
        rv = rel.uf.makeList(rvs)
        vPs = rv
        rv = rel.builtin.makeFlatten(uf.makeList([uf.makeList([vP]), vPs]))
        return i, rv
        pass
    @cached
    def parsePATTDOTS(self, i):
        rel = self; uf = self.uf; st = []
        i, rv = self.parseWS(i)
        i, rv = self.parsePVar(i)
        vN = rv
        i, rv = self.parseEllipsis(i)
        rv = rel.rules.makeVarPatt(vN)
        return i, rv
        pass
    @cached
    def parseCPATT(self, i):
        rel = self; uf = self.uf; st = []
        st.append(i)
        try:
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError("no reason")
            assert i >= 0
            if self.s[i:i + 1] != u"_": raise ParseError("no reason")
            self.lastMatch.append((u"TOKEN _", i, i + 1))
            rv = self.uf.makeStr(u"_"); i += 1
            rv = rel.rules.makeIgnorePatt()
        except ParseError as pe:
            i = st.pop()
            st.append(i)
            try:
                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                if i >= len(self.s): raise ParseError("no reason")
                assert i >= 0
                if self.s[i:i + 2] != u"[]": raise ParseError("no reason")
                self.lastMatch.append((u"TOKEN []", i, i + 2))
                rv = self.uf.makeStr(u"[]"); i += 2
                rv = rel.rules.makeEmptyListPatt()
            except ParseError as pe:
                i = st.pop()
                st.append(i)
                try:
                    while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                    if i >= len(self.s): raise ParseError("no reason")
                    assert i >= 0
                    if self.s[i:i + 1] != u"[": raise ParseError("no reason")
                    self.lastMatch.append((u"TOKEN [", i, i + 1))
                    rv = self.uf.makeStr(u"["); i += 1
                    i, rv = self.parsePATTDOTS(i)
                    vHead = rv
                    while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                    if i >= len(self.s): raise ParseError("no reason")
                    assert i >= 0
                    if self.s[i:i + 1] != u",": raise ParseError("no reason")
                    self.lastMatch.append((u"TOKEN ,", i, i + 1))
                    rv = self.uf.makeStr(u","); i += 1
                    i, rv = self.parseCPATTS(i)
                    vPs = rv
                    while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                    if i >= len(self.s): raise ParseError("no reason")
                    assert i >= 0
                    if self.s[i:i + 1] != u",": raise ParseError("no reason")
                    self.lastMatch.append((u"TOKEN ,", i, i + 1))
                    rv = self.uf.makeStr(u","); i += 1
                    i, rv = self.parsePATTDOTS(i)
                    vTail = rv
                    while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                    if i >= len(self.s): raise ParseError("no reason")
                    assert i >= 0
                    if self.s[i:i + 1] != u"]": raise ParseError("no reason")
                    self.lastMatch.append((u"TOKEN ]", i, i + 1))
                    rv = self.uf.makeStr(u"]"); i += 1
                    rv = rel.rules.makeListMidPatt(vHead, vTail, vPs)
                except ParseError as pe:
                    i = st.pop()
                    st.append(i)
                    try:
                        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                        if i >= len(self.s): raise ParseError("no reason")
                        assert i >= 0
                        if self.s[i:i + 1] != u"[": raise ParseError("no reason")
                        self.lastMatch.append((u"TOKEN [", i, i + 1))
                        rv = self.uf.makeStr(u"["); i += 1
                        i, rv = self.parsePATTDOTS(i)
                        vHead = rv
                        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                        if i >= len(self.s): raise ParseError("no reason")
                        assert i >= 0
                        if self.s[i:i + 1] != u",": raise ParseError("no reason")
                        self.lastMatch.append((u"TOKEN ,", i, i + 1))
                        rv = self.uf.makeStr(u","); i += 1
                        i, rv = self.parseCPATTS(i)
                        vPs = rv
                        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                        if i >= len(self.s): raise ParseError("no reason")
                        assert i >= 0
                        if self.s[i:i + 1] != u"]": raise ParseError("no reason")
                        self.lastMatch.append((u"TOKEN ]", i, i + 1))
                        rv = self.uf.makeStr(u"]"); i += 1
                        rv = rel.rules.makeListHeadPatt(vHead, vPs)
                    except ParseError as pe:
                        i = st.pop()
                        st.append(i)
                        try:
                            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                            if i >= len(self.s): raise ParseError("no reason")
                            assert i >= 0
                            if self.s[i:i + 1] != u"[": raise ParseError("no reason")
                            self.lastMatch.append((u"TOKEN [", i, i + 1))
                            rv = self.uf.makeStr(u"["); i += 1
                            i, rv = self.parseCPATTS(i)
                            vPs = rv
                            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                            if i >= len(self.s): raise ParseError("no reason")
                            assert i >= 0
                            if self.s[i:i + 1] != u",": raise ParseError("no reason")
                            self.lastMatch.append((u"TOKEN ,", i, i + 1))
                            rv = self.uf.makeStr(u","); i += 1
                            i, rv = self.parsePATTDOTS(i)
                            vTail = rv
                            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                            if i >= len(self.s): raise ParseError("no reason")
                            assert i >= 0
                            if self.s[i:i + 1] != u"]": raise ParseError("no reason")
                            self.lastMatch.append((u"TOKEN ]", i, i + 1))
                            rv = self.uf.makeStr(u"]"); i += 1
                            rv = rel.rules.makeListTailPatt(vTail, vPs)
                        except ParseError as pe:
                            i = st.pop()
                            st.append(i)
                            try:
                                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                if i >= len(self.s): raise ParseError("no reason")
                                assert i >= 0
                                if self.s[i:i + 1] != u"[": raise ParseError("no reason")
                                self.lastMatch.append((u"TOKEN [", i, i + 1))
                                rv = self.uf.makeStr(u"["); i += 1
                                i, rv = self.parseCPATTS(i)
                                vPs = rv
                                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                if i >= len(self.s): raise ParseError("no reason")
                                assert i >= 0
                                if self.s[i:i + 1] != u"]": raise ParseError("no reason")
                                self.lastMatch.append((u"TOKEN ]", i, i + 1))
                                rv = self.uf.makeStr(u"]"); i += 1
                                rv = rel.rules.makeListPatt(vPs)
                            except ParseError as pe:
                                i = st.pop()
                                st.append(i)
                                try:
                                    i, rv = self.parseSTRING(i)
                                    vS = rv
                                    rv = rel.rules.makeStrPatt(vS)
                                except ParseError as pe:
                                    i = st.pop()
                                    st.append(i)
                                    try:
                                        i, rv = self.parseID(i)
                                        vNs = rv
                                        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                        if i >= len(self.s): raise ParseError("no reason")
                                        assert i >= 0
                                        if self.s[i:i + 1] != u".": raise ParseError("no reason")
                                        self.lastMatch.append((u"TOKEN .", i, i + 1))
                                        rv = self.uf.makeStr(u"."); i += 1
                                        i, rv = self.parseID(i)
                                        vFunc = rv
                                        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                        if i >= len(self.s): raise ParseError("no reason")
                                        assert i >= 0
                                        if self.s[i:i + 1] != u"(": raise ParseError("no reason")
                                        self.lastMatch.append((u"TOKEN (", i, i + 1))
                                        rv = self.uf.makeStr(u"("); i += 1
                                        i, rv = self.parseCPATTS(i)
                                        vPs = rv
                                        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                        if i >= len(self.s): raise ParseError("no reason")
                                        assert i >= 0
                                        if self.s[i:i + 1] != u")": raise ParseError("no reason")
                                        self.lastMatch.append((u"TOKEN )", i, i + 1))
                                        rv = self.uf.makeStr(u")"); i += 1
                                        rv = rel.rules.makeStructPatt(vNs, vFunc, vPs)
                                    except ParseError as pe:
                                        i = st.pop()
                                        st.append(i)
                                        try:
                                            i, rv = self.parseID(i)
                                            vNs = rv
                                            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                            if i >= len(self.s): raise ParseError("no reason")
                                            assert i >= 0
                                            if self.s[i:i + 1] != u".": raise ParseError("no reason")
                                            self.lastMatch.append((u"TOKEN .", i, i + 1))
                                            rv = self.uf.makeStr(u"."); i += 1
                                            i, rv = self.parseID(i)
                                            vFunc = rv
                                            rv = rel.rules.makeStructPatt(vNs, vFunc, uf.makeList([]))
                                        except ParseError as pe:
                                            i = st.pop()
                                            i, rv = self.parsePVar(i)
                                            vName = rv
                                            st.append(i)
                                            try:
                                                i, rv = self.parseEllipsis(i)
                                                rv = True
                                            except ParseError as pe:
                                                rv = False
                                            i = st.pop()
                                            if rv: raise ParseError("no reason")
                                            rv = rel.rules.makeVarPatt(vName)
        return i, rv
        pass
    @cached
    def parseCPRODS(self, i):
        rel = self; uf = self.uf; st = []
        i, rv = self.parseCPROD1(i)
        vP = rv
        rvs = []
        while True:
            st.append(i)
            try:
                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                if i >= len(self.s): raise ParseError("no reason")
                assert i >= 0
                if self.s[i:i + 1] != u",": raise ParseError("no reason")
                self.lastMatch.append((u"TOKEN ,", i, i + 1))
                rv = self.uf.makeStr(u","); i += 1
                i, rv = self.parseCPROD1(i)
                rvs.append(rv)
            except ParseError as pe:
                i = st.pop()
                break
            pass
        rv = rel.uf.makeList(rvs)
        vPs = rv
        rv = rel.builtin.makeFlatten(uf.makeList([uf.makeList([vP]), vPs]))
        return i, rv
        pass
    @cached
    def parseCPROD1(self, i):
        rel = self; uf = self.uf; st = []
        st.append(i)
        try:
            i, rv = self.parseWS(i)
            i, rv = self.parseCPROD2(i)
            vP = rv
            rvs = []
            while True:
                st.append(i)
                try:
                    i, rv = self.parseWS(i)
                    i, rv = self.parseCPROD2(i)
                    rvs.append(rv)
                except ParseError as pe:
                    i = st.pop()
                    break
                pass
            rv = rel.uf.makeList(rvs)
            if not len(rvs): raise ParseError("no reason")
            vPs = rv
            rv = rel.rules.makeConcatOp(vP, vPs)
        except ParseError as pe:
            i = st.pop()
            i, rv = self.parseWS(i)
            i, rv = self.parseCPROD2(i)
        return i, rv
        pass
    @cached
    def parseCPROD2(self, i):
        rel = self; uf = self.uf; st = []
        st.append(i)
        try:
            i, rv = self.parseSTRING(i)
            vS = rv
            rv = rel.rules.makeStrProd(vS)
        except ParseError as pe:
            i = st.pop()
            st.append(i)
            try:
                i, rv = self.parseNumber(i)
                vN = rv
                rv = rel.rules.makeCharProd(vN)
            except ParseError as pe:
                i = st.pop()
                st.append(i)
                try:
                    while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                    if i >= len(self.s): raise ParseError("no reason")
                    assert i >= 0
                    if self.s[i:i + 1] != u"#": raise ParseError("no reason")
                    self.lastMatch.append((u"TOKEN #", i, i + 1))
                    rv = self.uf.makeStr(u"#"); i += 1
                    i, rv = self.parseCPROD2(i)
                    vP = rv
                    rv = rel.rules.makeLengthOp(vP)
                except ParseError as pe:
                    i = st.pop()
                    st.append(i)
                    try:
                        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                        if i >= len(self.s): raise ParseError("no reason")
                        assert i >= 0
                        if self.s[i:i + 1] != u"*": raise ParseError("no reason")
                        self.lastMatch.append((u"TOKEN *", i, i + 1))
                        rv = self.uf.makeStr(u"*"); i += 1
                        i, rv = self.parseCPROD2(i)
                        vP = rv
                        rv = rel.rules.makeFlattenOp(vP)
                    except ParseError as pe:
                        i = st.pop()
                        st.append(i)
                        try:
                            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                            if i >= len(self.s): raise ParseError("no reason")
                            assert i >= 0
                            if self.s[i:i + 2] != u"*(": raise ParseError("no reason")
                            self.lastMatch.append((u"TOKEN *(", i, i + 2))
                            rv = self.uf.makeStr(u"*("); i += 2
                            i, rv = self.parseCPROD1(i)
                            vP = rv
                            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                            if i >= len(self.s): raise ParseError("no reason")
                            assert i >= 0
                            if self.s[i:i + 1] != u")": raise ParseError("no reason")
                            self.lastMatch.append((u"TOKEN )", i, i + 1))
                            rv = self.uf.makeStr(u")"); i += 1
                            rv = rel.rules.makeFlattenOp(vP)
                        except ParseError as pe:
                            i = st.pop()
                            st.append(i)
                            try:
                                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                if i >= len(self.s): raise ParseError("no reason")
                                assert i >= 0
                                if self.s[i:i + 6] != u".line(": raise ParseError("no reason")
                                self.lastMatch.append((u"TOKEN .line(", i, i + 6))
                                rv = self.uf.makeStr(u".line("); i += 6
                                i, rv = self.parseCPROD1(i)
                                vP = rv
                                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                if i >= len(self.s): raise ParseError("no reason")
                                assert i >= 0
                                if self.s[i:i + 1] != u")": raise ParseError("no reason")
                                self.lastMatch.append((u"TOKEN )", i, i + 1))
                                rv = self.uf.makeStr(u")"); i += 1
                                rv = rel.rules.makeStructProd(uf.makeStr(u'builtin'), uf.makeStr(u'Line'), uf.makeList([vP]))
                            except ParseError as pe:
                                i = st.pop()
                                st.append(i)
                                try:
                                    while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                    if i >= len(self.s): raise ParseError("no reason")
                                    assert i >= 0
                                    if self.s[i:i + 7] != u".block(": raise ParseError("no reason")
                                    self.lastMatch.append((u"TOKEN .block(", i, i + 7))
                                    rv = self.uf.makeStr(u".block("); i += 7
                                    i, rv = self.parseCPROD1(i)
                                    vP = rv
                                    while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                    if i >= len(self.s): raise ParseError("no reason")
                                    assert i >= 0
                                    if self.s[i:i + 1] != u")": raise ParseError("no reason")
                                    self.lastMatch.append((u"TOKEN )", i, i + 1))
                                    rv = self.uf.makeStr(u")"); i += 1
                                    rv = rel.rules.makeStructProd(uf.makeStr(u'builtin'), uf.makeStr(u'Block'), uf.makeList([vP]))
                                except ParseError as pe:
                                    i = st.pop()
                                    st.append(i)
                                    try:
                                        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                        if i >= len(self.s): raise ParseError("no reason")
                                        assert i >= 0
                                        if self.s[i:i + 6] != u".join(": raise ParseError("no reason")
                                        self.lastMatch.append((u"TOKEN .join(", i, i + 6))
                                        rv = self.uf.makeStr(u".join("); i += 6
                                        i, rv = self.parseCPROD1(i)
                                        vP = rv
                                        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                        if i >= len(self.s): raise ParseError("no reason")
                                        assert i >= 0
                                        if self.s[i:i + 1] != u",": raise ParseError("no reason")
                                        self.lastMatch.append((u"TOKEN ,", i, i + 1))
                                        rv = self.uf.makeStr(u","); i += 1
                                        i, rv = self.parseSTRING(i)
                                        vS = rv
                                        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                        if i >= len(self.s): raise ParseError("no reason")
                                        assert i >= 0
                                        if self.s[i:i + 1] != u")": raise ParseError("no reason")
                                        self.lastMatch.append((u"TOKEN )", i, i + 1))
                                        rv = self.uf.makeStr(u")"); i += 1
                                        rv = rel.rules.makeJoinOp(vS, vP)
                                    except ParseError as pe:
                                        i = st.pop()
                                        st.append(i)
                                        try:
                                            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                            if i >= len(self.s): raise ParseError("no reason")
                                            assert i >= 0
                                            if self.s[i:i + 2] != u"[]": raise ParseError("no reason")
                                            self.lastMatch.append((u"TOKEN []", i, i + 2))
                                            rv = self.uf.makeStr(u"[]"); i += 2
                                            rv = rel.rules.makeListProd(uf.makeList([]))
                                        except ParseError as pe:
                                            i = st.pop()
                                            st.append(i)
                                            try:
                                                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                                if i >= len(self.s): raise ParseError("no reason")
                                                assert i >= 0
                                                if self.s[i:i + 1] != u"[": raise ParseError("no reason")
                                                self.lastMatch.append((u"TOKEN [", i, i + 1))
                                                rv = self.uf.makeStr(u"["); i += 1
                                                i, rv = self.parsePATTDOTS(i)
                                                vHead = rv
                                                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                                if i >= len(self.s): raise ParseError("no reason")
                                                assert i >= 0
                                                if self.s[i:i + 1] != u",": raise ParseError("no reason")
                                                self.lastMatch.append((u"TOKEN ,", i, i + 1))
                                                rv = self.uf.makeStr(u","); i += 1
                                                i, rv = self.parseCPRODS(i)
                                                vPs = rv
                                                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                                if i >= len(self.s): raise ParseError("no reason")
                                                assert i >= 0
                                                if self.s[i:i + 1] != u",": raise ParseError("no reason")
                                                self.lastMatch.append((u"TOKEN ,", i, i + 1))
                                                rv = self.uf.makeStr(u","); i += 1
                                                i, rv = self.parsePATTDOTS(i)
                                                vTail = rv
                                                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                                if i >= len(self.s): raise ParseError("no reason")
                                                assert i >= 0
                                                if self.s[i:i + 1] != u"]": raise ParseError("no reason")
                                                self.lastMatch.append((u"TOKEN ]", i, i + 1))
                                                rv = self.uf.makeStr(u"]"); i += 1
                                                rv = rel.rules.makeListMidProd(vHead, vTail, vPs)
                                            except ParseError as pe:
                                                i = st.pop()
                                                st.append(i)
                                                try:
                                                    while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                                    if i >= len(self.s): raise ParseError("no reason")
                                                    assert i >= 0
                                                    if self.s[i:i + 1] != u"[": raise ParseError("no reason")
                                                    self.lastMatch.append((u"TOKEN [", i, i + 1))
                                                    rv = self.uf.makeStr(u"["); i += 1
                                                    i, rv = self.parsePATTDOTS(i)
                                                    vHead = rv
                                                    while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                                    if i >= len(self.s): raise ParseError("no reason")
                                                    assert i >= 0
                                                    if self.s[i:i + 1] != u",": raise ParseError("no reason")
                                                    self.lastMatch.append((u"TOKEN ,", i, i + 1))
                                                    rv = self.uf.makeStr(u","); i += 1
                                                    i, rv = self.parseCPRODS(i)
                                                    vPs = rv
                                                    while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                                    if i >= len(self.s): raise ParseError("no reason")
                                                    assert i >= 0
                                                    if self.s[i:i + 1] != u"]": raise ParseError("no reason")
                                                    self.lastMatch.append((u"TOKEN ]", i, i + 1))
                                                    rv = self.uf.makeStr(u"]"); i += 1
                                                    rv = rel.rules.makeListHeadProd(vHead, vPs)
                                                except ParseError as pe:
                                                    i = st.pop()
                                                    st.append(i)
                                                    try:
                                                        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                                        if i >= len(self.s): raise ParseError("no reason")
                                                        assert i >= 0
                                                        if self.s[i:i + 1] != u"[": raise ParseError("no reason")
                                                        self.lastMatch.append((u"TOKEN [", i, i + 1))
                                                        rv = self.uf.makeStr(u"["); i += 1
                                                        i, rv = self.parseCPRODS(i)
                                                        vPs = rv
                                                        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                                        if i >= len(self.s): raise ParseError("no reason")
                                                        assert i >= 0
                                                        if self.s[i:i + 1] != u",": raise ParseError("no reason")
                                                        self.lastMatch.append((u"TOKEN ,", i, i + 1))
                                                        rv = self.uf.makeStr(u","); i += 1
                                                        i, rv = self.parsePATTDOTS(i)
                                                        vTail = rv
                                                        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                                        if i >= len(self.s): raise ParseError("no reason")
                                                        assert i >= 0
                                                        if self.s[i:i + 1] != u"]": raise ParseError("no reason")
                                                        self.lastMatch.append((u"TOKEN ]", i, i + 1))
                                                        rv = self.uf.makeStr(u"]"); i += 1
                                                        rv = rel.rules.makeListTailProd(vTail, vPs)
                                                    except ParseError as pe:
                                                        i = st.pop()
                                                        st.append(i)
                                                        try:
                                                            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                                            if i >= len(self.s): raise ParseError("no reason")
                                                            assert i >= 0
                                                            if self.s[i:i + 1] != u"[": raise ParseError("no reason")
                                                            self.lastMatch.append((u"TOKEN [", i, i + 1))
                                                            rv = self.uf.makeStr(u"["); i += 1
                                                            i, rv = self.parseCPRODS(i)
                                                            vPs = rv
                                                            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                                            if i >= len(self.s): raise ParseError("no reason")
                                                            assert i >= 0
                                                            if self.s[i:i + 1] != u"]": raise ParseError("no reason")
                                                            self.lastMatch.append((u"TOKEN ]", i, i + 1))
                                                            rv = self.uf.makeStr(u"]"); i += 1
                                                            rv = rel.rules.makeListProd(vPs)
                                                        except ParseError as pe:
                                                            i = st.pop()
                                                            st.append(i)
                                                            try:
                                                                i, rv = self.parsePVar(i)
                                                                vName = rv
                                                                st.append(i)
                                                                try:
                                                                    i, rv = self.parseEllipsis(i)
                                                                    rv = True
                                                                except ParseError as pe:
                                                                    rv = False
                                                                i = st.pop()
                                                                if rv: raise ParseError("no reason")
                                                                rv = rel.rules.makeVarProd(vName)
                                                            except ParseError as pe:
                                                                i = st.pop()
                                                                st.append(i)
                                                                try:
                                                                    i, rv = self.parsePConst(i)
                                                                    vName = rv
                                                                    st.append(i)
                                                                    try:
                                                                        i, rv = self.parseEllipsis(i)
                                                                        rv = True
                                                                    except ParseError as pe:
                                                                        rv = False
                                                                    i = st.pop()
                                                                    if rv: raise ParseError("no reason")
                                                                    st.append(i)
                                                                    try:
                                                                        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                                                        if i >= len(self.s): raise ParseError("no reason")
                                                                        assert i >= 0
                                                                        if self.s[i:i + 1] != u".": raise ParseError("no reason")
                                                                        self.lastMatch.append((u"TOKEN .", i, i + 1))
                                                                        rv = self.uf.makeStr(u"."); i += 1
                                                                        rv = True
                                                                    except ParseError as pe:
                                                                        rv = False
                                                                    i = st.pop()
                                                                    if rv: raise ParseError("no reason")
                                                                    rv = rel.rules.makeConstProd(vName)
                                                                except ParseError as pe:
                                                                    i = st.pop()
                                                                    st.append(i)
                                                                    try:
                                                                        i, rv = self.parseID(i)
                                                                        vNs = rv
                                                                        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                                                        if i >= len(self.s): raise ParseError("no reason")
                                                                        assert i >= 0
                                                                        if self.s[i:i + 1] != u".": raise ParseError("no reason")
                                                                        self.lastMatch.append((u"TOKEN .", i, i + 1))
                                                                        rv = self.uf.makeStr(u"."); i += 1
                                                                        i, rv = self.parseID(i)
                                                                        vFunc = rv
                                                                        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                                                        if i >= len(self.s): raise ParseError("no reason")
                                                                        assert i >= 0
                                                                        if self.s[i:i + 1] != u"(": raise ParseError("no reason")
                                                                        self.lastMatch.append((u"TOKEN (", i, i + 1))
                                                                        rv = self.uf.makeStr(u"("); i += 1
                                                                        i, rv = self.parseCPRODS(i)
                                                                        vPs = rv
                                                                        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                                                        if i >= len(self.s): raise ParseError("no reason")
                                                                        assert i >= 0
                                                                        if self.s[i:i + 1] != u")": raise ParseError("no reason")
                                                                        self.lastMatch.append((u"TOKEN )", i, i + 1))
                                                                        rv = self.uf.makeStr(u")"); i += 1
                                                                        rv = rel.rules.makeStructProd(vNs, vFunc, vPs)
                                                                    except ParseError as pe:
                                                                        i = st.pop()
                                                                        i, rv = self.parseID(i)
                                                                        vNs = rv
                                                                        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                                                        if i >= len(self.s): raise ParseError("no reason")
                                                                        assert i >= 0
                                                                        if self.s[i:i + 1] != u".": raise ParseError("no reason")
                                                                        self.lastMatch.append((u"TOKEN .", i, i + 1))
                                                                        rv = self.uf.makeStr(u"."); i += 1
                                                                        i, rv = self.parseID(i)
                                                                        vFunc = rv
                                                                        rv = rel.rules.makeStructProd(vNs, vFunc, uf.makeList([]))
        return i, rv
        pass
    @cached
    def parseGRAMMAR(self, i):
        rel = self; uf = self.uf; st = []
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError("no reason")
        assert i >= 0
        if self.s[i:i + 8] != u".grammar": raise ParseError("no reason")
        self.lastMatch.append((u"TOKEN .grammar", i, i + 8))
        rv = self.uf.makeStr(u".grammar"); i += 8
        i, rv = self.parseID(i)
        vName = rv
        rvs = []
        while True:
            st.append(i)
            try:
                st.append(i)
                try:
                    i, rv = self.parsePCLASS(i)
                except ParseError as pe:
                    i = st.pop()
                    st.append(i)
                    try:
                        i, rv = self.parsePTOKEN(i)
                    except ParseError as pe:
                        i = st.pop()
                        i, rv = self.parsePRULE(i)
                rvs.append(rv)
            except ParseError as pe:
                i = st.pop()
                break
            pass
        rv = rel.uf.makeList(rvs)
        vRules = rv
        rv = uf.makeList([rel.py.makeCompound(uf.makeStr(u'def target(driver, *args)'), uf.makeList([rel.py.makeStatement(rel.builtin.makeConcat(uf.makeStr(u'driver.exe_name = "'), uf.makeList([vName, uf.makeStr(u'".lower() + "c"')]))), rel.py.makeRet(uf.makeStr(u'main, None'))])), rel.py.makeCompound(rel.builtin.makeConcat(uf.makeStr(u'class '), uf.makeList([vName, uf.makeStr(u'Parser(object)')])), rel.builtin.makeFlatten(uf.makeList([uf.makeList([rel.py.makeCompound(uf.makeStr(u'def __init__(self, s, uf)'), uf.makeList([rel.py.makeStatement(uf.makeStr(u'self.s = s; self.uf = uf')), rel.py.makeStatement(uf.makeStr(u'self.lastMatch = []')), rel.py.makeStatement(uf.makeStr(u'for name in unrolledRels: setattr(self, name, frozenRels[name](uf))')), rel.py.makeStatement(uf.makeStr(u'for l in unrolledLets: l(uf, self)'))])), rel.py.makeCompound(uf.makeStr(u'def parse(self)'), uf.makeList([rel.py.makeRet(rel.builtin.makeConcat(uf.makeStr(u'self.parse'), uf.makeList([vName, uf.makeStr(u'(0)')])))]))]), rel.builtin.makeFlatten(vRules)]))), rel.py.makeStatement(rel.builtin.makeConcat(uf.makeStr(u'MainParser = '), uf.makeList([vName, uf.makeStr(u'Parser')])))])
        return i, rv
        pass
    @cached
    def parsePCLASS(self, i):
        rel = self; uf = self.uf; st = []
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError("no reason")
        assert i >= 0
        if self.s[i:i + 5] != u"class": raise ParseError("no reason")
        self.lastMatch.append((u"TOKEN class", i, i + 5))
        rv = self.uf.makeStr(u"class"); i += 5
        i, rv = self.parseID(i)
        vName = rv
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError("no reason")
        assert i >= 0
        if self.s[i:i + 1] != u"=": raise ParseError("no reason")
        self.lastMatch.append((u"TOKEN =", i, i + 1))
        rv = self.uf.makeStr(u"="); i += 1
        i, rv = self.parseCLASSEXPR1(i)
        vC = rv
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError("no reason")
        assert i >= 0
        if self.s[i:i + 1] != u";": raise ParseError("no reason")
        self.lastMatch.append((u"TOKEN ;", i, i + 1))
        rv = self.uf.makeStr(u";"); i += 1
        rv = uf.makeList([rel.py.makeCompound(rel.builtin.makeConcat(uf.makeStr(u'def cls'), uf.makeList([vName, uf.makeStr(u'(self, c)')])), uf.makeList([rel.py.makeRet(vC)]))])
        return i, rv
        pass
    @cached
    def parseCLASSEXPR1(self, i):
        rel = self; uf = self.uf; st = []
        st.append(i)
        try:
            i, rv = self.parseCLASSEXPR2(i)
            vL = rv
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError("no reason")
            assert i >= 0
            if self.s[i:i + 1] != u"|": raise ParseError("no reason")
            self.lastMatch.append((u"TOKEN |", i, i + 1))
            rv = self.uf.makeStr(u"|"); i += 1
            i, rv = self.parseCLASSEXPR1(i)
            vR = rv
            rv = rel.char.makeEither(vL, vR)
        except ParseError as pe:
            i = st.pop()
            i, rv = self.parseCLASSEXPR2(i)
        return i, rv
        pass
    @cached
    def parseCLASSEXPR2(self, i):
        rel = self; uf = self.uf; st = []
        st.append(i)
        try:
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError("no reason")
            assert i >= 0
            if self.s[i:i + 4] != u".any": raise ParseError("no reason")
            self.lastMatch.append((u"TOKEN .any", i, i + 4))
            rv = self.uf.makeStr(u".any"); i += 4
            rv = rel.char.makeAny()
        except ParseError as pe:
            i = st.pop()
            st.append(i)
            try:
                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                if i >= len(self.s): raise ParseError("no reason")
                assert i >= 0
                if self.s[i:i + 7] != u".range(": raise ParseError("no reason")
                self.lastMatch.append((u"TOKEN .range(", i, i + 7))
                rv = self.uf.makeStr(u".range("); i += 7
                i, rv = self.parseWS(i)
                i, rv = self.parseNumber(i)
                vL = rv
                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                if i >= len(self.s): raise ParseError("no reason")
                assert i >= 0
                if self.s[i:i + 1] != u":": raise ParseError("no reason")
                self.lastMatch.append((u"TOKEN :", i, i + 1))
                rv = self.uf.makeStr(u":"); i += 1
                i, rv = self.parseWS(i)
                i, rv = self.parseNumber(i)
                vU = rv
                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                if i >= len(self.s): raise ParseError("no reason")
                assert i >= 0
                if self.s[i:i + 1] != u")": raise ParseError("no reason")
                self.lastMatch.append((u"TOKEN )", i, i + 1))
                rv = self.uf.makeStr(u")"); i += 1
                rv = rel.char.makeRange(vL, vU)
            except ParseError as pe:
                i = st.pop()
                st.append(i)
                try:
                    while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                    if i >= len(self.s): raise ParseError("no reason")
                    assert i >= 0
                    if self.s[i:i + 1] != u"~": raise ParseError("no reason")
                    self.lastMatch.append((u"TOKEN ~", i, i + 1))
                    rv = self.uf.makeStr(u"~"); i += 1
                    i, rv = self.parseCLASSEXPR2(i)
                    vS = rv
                    rv = rel.char.makeComplement(vS)
                except ParseError as pe:
                    i = st.pop()
                    st.append(i)
                    try:
                        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                        if i >= len(self.s): raise ParseError("no reason")
                        assert i >= 0
                        if self.s[i:i + 1] != u"(": raise ParseError("no reason")
                        self.lastMatch.append((u"TOKEN (", i, i + 1))
                        rv = self.uf.makeStr(u"("); i += 1
                        i, rv = self.parseCLASSEXPR1(i)
                        vS = rv
                        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                        if i >= len(self.s): raise ParseError("no reason")
                        assert i >= 0
                        if self.s[i:i + 1] != u")": raise ParseError("no reason")
                        self.lastMatch.append((u"TOKEN )", i, i + 1))
                        rv = self.uf.makeStr(u")"); i += 1
                        rv = vS
                    except ParseError as pe:
                        i = st.pop()
                        st.append(i)
                        try:
                            i, rv = self.parseWS(i)
                            i, rv = self.parseNumber(i)
                            vC = rv
                            rv = rel.char.makeExactly(vC)
                        except ParseError as pe:
                            i = st.pop()
                            i, rv = self.parseID(i)
                            vN = rv
                            rv = rel.char.makeCall(vN)
        return i, rv
        pass
    @cached
    def parsePTOKEN(self, i):
        rel = self; uf = self.uf; st = []
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError("no reason")
        assert i >= 0
        if self.s[i:i + 5] != u"token": raise ParseError("no reason")
        self.lastMatch.append((u"TOKEN token", i, i + 5))
        rv = self.uf.makeStr(u"token"); i += 5
        i, rv = self.parseID(i)
        vName = rv
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError("no reason")
        assert i >= 0
        if self.s[i:i + 1] != u"=": raise ParseError("no reason")
        self.lastMatch.append((u"TOKEN =", i, i + 1))
        rv = self.uf.makeStr(u"="); i += 1
        rvs = []
        while True:
            st.append(i)
            try:
                i, rv = self.parsePSCAN(i)
                rvs.append(rv)
            except ParseError as pe:
                i = st.pop()
                break
            pass
        rv = rel.uf.makeList(rvs)
        if not len(rvs): raise ParseError("no reason")
        vScans = rv
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError("no reason")
        assert i >= 0
        if self.s[i:i + 1] != u";": raise ParseError("no reason")
        self.lastMatch.append((u"TOKEN ;", i, i + 1))
        rv = self.uf.makeStr(u";"); i += 1
        rv = uf.makeList([rel.py.makeCompound(rel.builtin.makeConcat(uf.makeStr(u'def parse'), uf.makeList([vName, uf.makeStr(u'(self, i)')])), rel.builtin.makeFlatten(uf.makeList([uf.makeList([rel.constboundcheck, rel.py.makeStatement(uf.makeStr(u'start = i; assert start >= 0'))]), rel.builtin.makeFlatten(vScans), uf.makeList([rel.py.makeStatement(uf.makeStr(u'rv = self.uf.makeStr(self.s[start:i])')), rel.py.makeStatement(rel.builtin.makeConcat(uf.makeStr(u'self.lastMatch.append((u"TOKEN '), uf.makeList([vName, uf.makeStr(u'", start, i))')]))), rel.py.makeRet(uf.makeStr(u'i, rv'))])])))])
        return i, rv
        pass
    @cached
    def parsePSCAN(self, i):
        rel = self; uf = self.uf; st = []
        st.append(i)
        try:
            i, rv = self.parseID(i)
            vCls = rv
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError("no reason")
            assert i >= 0
            if self.s[i:i + 1] != u"*": raise ParseError("no reason")
            self.lastMatch.append((u"TOKEN *", i, i + 1))
            rv = self.uf.makeStr(u"*"); i += 1
            rv = uf.makeList([rel.py.makeStatement(rel.builtin.makeConcat(uf.makeStr(u'while i < len(self.s) and self.cls'), uf.makeList([vCls, uf.makeStr(u'(ord(self.s[i])): i += 1')])))])
        except ParseError as pe:
            i = st.pop()
            st.append(i)
            try:
                i, rv = self.parseID(i)
                vCls = rv
                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                if i >= len(self.s): raise ParseError("no reason")
                assert i >= 0
                if self.s[i:i + 1] != u"+": raise ParseError("no reason")
                self.lastMatch.append((u"TOKEN +", i, i + 1))
                rv = self.uf.makeStr(u"+"); i += 1
                rv = uf.makeList([rel.py.makeRaiseIf(rel.builtin.makeConcat(uf.makeStr(u'i >= len(self.s) or not self.cls'), uf.makeList([vCls, uf.makeStr(u'(ord(self.s[i]))')]))), rel.py.makeStatement(rel.builtin.makeConcat(uf.makeStr(u'while i < len(self.s) and self.cls'), uf.makeList([vCls, uf.makeStr(u'(ord(self.s[i])): i += 1')])))])
            except ParseError as pe:
                i = st.pop()
                i, rv = self.parseID(i)
                vCls = rv
                rv = uf.makeList([rel.py.makeRaiseIf(rel.builtin.makeConcat(uf.makeStr(u'i >= len(self.s) or not self.cls'), uf.makeList([vCls, uf.makeStr(u'(ord(self.s[i]))')]))), rel.py.makeStatement(uf.makeStr(u'i += 1'))])
        return i, rv
        pass
    @cached
    def parsePRULE(self, i):
        rel = self; uf = self.uf; st = []
        i, rv = self.parseID(i)
        vName = rv
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError("no reason")
        assert i >= 0
        if self.s[i:i + 2] != u":=": raise ParseError("no reason")
        self.lastMatch.append((u"TOKEN :=", i, i + 2))
        rv = self.uf.makeStr(u":="); i += 2
        i, rv = self.parsePEXPR1(i)
        vExpr = rv
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError("no reason")
        assert i >= 0
        if self.s[i:i + 1] != u";": raise ParseError("no reason")
        self.lastMatch.append((u"TOKEN ;", i, i + 1))
        rv = self.uf.makeStr(u";"); i += 1
        rv = uf.makeList([rel.py.makeStatement(uf.makeStr(u'@cached')), rel.py.makeCompound(rel.builtin.makeConcat(uf.makeStr(u'def parse'), uf.makeList([vName, uf.makeStr(u'(self, i)')])), rel.builtin.makeFlatten(uf.makeList([uf.makeList([rel.py.makeStatement(uf.makeStr(u'rel = self; uf = self.uf; st = []'))]), vExpr, uf.makeList([rel.py.makeRet(uf.makeStr(u'i, rv'))])])))])
        return i, rv
        pass
    @cached
    def parsePEXPR1(self, i):
        rel = self; uf = self.uf; st = []
        st.append(i)
        try:
            i, rv = self.parsePEXPR2(i)
            vThis = rv
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError("no reason")
            assert i >= 0
            if self.s[i:i + 1] != u"/": raise ParseError("no reason")
            self.lastMatch.append((u"TOKEN /", i, i + 1))
            rv = self.uf.makeStr(u"/"); i += 1
            i, rv = self.parsePEXPR1(i)
            vThat = rv
            rv = rel.peg.makeChoice(vThis, vThat)
        except ParseError as pe:
            i = st.pop()
            i, rv = self.parsePEXPR2(i)
        return i, rv
        pass
    @cached
    def parsePEXPR2(self, i):
        rel = self; uf = self.uf; st = []
        st.append(i)
        try:
            i, rv = self.parsePEXPR3(i)
            vExprs = rv
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError("no reason")
            assert i >= 0
            if self.s[i:i + 2] != u"->": raise ParseError("no reason")
            self.lastMatch.append((u"TOKEN ->", i, i + 2))
            rv = self.uf.makeStr(u"->"); i += 2
            i, rv = self.parseCPROD1(i)
            vProd = rv
            rv = rel.peg.makeProduction(vExprs, vProd)
        except ParseError as pe:
            i = st.pop()
            i, rv = self.parsePEXPR3(i)
        return i, rv
        pass
    @cached
    def parsePEXPR3(self, i):
        rel = self; uf = self.uf; st = []
        rvs = []
        while True:
            st.append(i)
            try:
                i, rv = self.parsePEXPR4(i)
                rvs.append(rv)
            except ParseError as pe:
                i = st.pop()
                break
            pass
        rv = rel.uf.makeList(rvs)
        vExprs = rv
        rv = rel.peg.makeSequence(vExprs)
        return i, rv
        pass
    @cached
    def parsePEXPR4(self, i):
        rel = self; uf = self.uf; st = []
        st.append(i)
        try:
            i, rv = self.parsePEXPR5(i)
            vExpr = rv
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError("no reason")
            assert i >= 0
            if self.s[i:i + 1] != u":": raise ParseError("no reason")
            self.lastMatch.append((u"TOKEN :", i, i + 1))
            rv = self.uf.makeStr(u":"); i += 1
            i, rv = self.parsePPATT(i)
            vP = rv
            rv = rel.peg.makeCapture(vExpr, vP)
        except ParseError as pe:
            i = st.pop()
            i, rv = self.parsePEXPR5(i)
        return i, rv
        pass
    @cached
    def parsePPATT(self, i):
        rel = self; uf = self.uf; st = []
        st.append(i)
        try:
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError("no reason")
            assert i >= 0
            if self.s[i:i + 1] != u"(": raise ParseError("no reason")
            self.lastMatch.append((u"TOKEN (", i, i + 1))
            rv = self.uf.makeStr(u"("); i += 1
            i, rv = self.parsePPATT(i)
            vP = rv
            rvs = []
            while True:
                st.append(i)
                try:
                    while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                    if i >= len(self.s): raise ParseError("no reason")
                    assert i >= 0
                    if self.s[i:i + 1] != u",": raise ParseError("no reason")
                    self.lastMatch.append((u"TOKEN ,", i, i + 1))
                    rv = self.uf.makeStr(u","); i += 1
                    i, rv = self.parsePPATT(i)
                    rvs.append(rv)
                except ParseError as pe:
                    i = st.pop()
                    break
                pass
            rv = rel.uf.makeList(rvs)
            vPs = rv
            rv = rel.peg.makeTuplePatt(rel.builtin.makeFlatten(uf.makeList([uf.makeList([vP]), vPs])))
        except ParseError as pe:
            i = st.pop()
            i, rv = self.parseID(i)
            vName = rv
            rv = rel.peg.makeNamePatt(vName)
        return i, rv
        pass
    @cached
    def parsePEXPR5(self, i):
        rel = self; uf = self.uf; st = []
        st.append(i)
        try:
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError("no reason")
            assert i >= 0
            if self.s[i:i + 1] != u"&": raise ParseError("no reason")
            self.lastMatch.append((u"TOKEN &", i, i + 1))
            rv = self.uf.makeStr(u"&"); i += 1
            i, rv = self.parsePEXPR6(i)
            vExpr = rv
            rv = rel.peg.makePositive(vExpr)
        except ParseError as pe:
            i = st.pop()
            st.append(i)
            try:
                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                if i >= len(self.s): raise ParseError("no reason")
                assert i >= 0
                if self.s[i:i + 1] != u"!": raise ParseError("no reason")
                self.lastMatch.append((u"TOKEN !", i, i + 1))
                rv = self.uf.makeStr(u"!"); i += 1
                i, rv = self.parsePEXPR6(i)
                vExpr = rv
                rv = rel.peg.makeNegative(vExpr)
            except ParseError as pe:
                i = st.pop()
                i, rv = self.parsePEXPR6(i)
        return i, rv
        pass
    @cached
    def parsePEXPR6(self, i):
        rel = self; uf = self.uf; st = []
        st.append(i)
        try:
            i, rv = self.parsePEXPR7(i)
            vExpr = rv
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError("no reason")
            assert i >= 0
            if self.s[i:i + 1] != u"*": raise ParseError("no reason")
            self.lastMatch.append((u"TOKEN *", i, i + 1))
            rv = self.uf.makeStr(u"*"); i += 1
            rv = rel.peg.makeAny(vExpr)
        except ParseError as pe:
            i = st.pop()
            st.append(i)
            try:
                i, rv = self.parsePEXPR7(i)
                vExpr = rv
                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                if i >= len(self.s): raise ParseError("no reason")
                assert i >= 0
                if self.s[i:i + 1] != u"+": raise ParseError("no reason")
                self.lastMatch.append((u"TOKEN +", i, i + 1))
                rv = self.uf.makeStr(u"+"); i += 1
                rv = rel.peg.makeSome(vExpr)
            except ParseError as pe:
                i = st.pop()
                st.append(i)
                try:
                    i, rv = self.parsePEXPR7(i)
                    vExpr = rv
                    while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                    if i >= len(self.s): raise ParseError("no reason")
                    assert i >= 0
                    if self.s[i:i + 1] != u"?": raise ParseError("no reason")
                    self.lastMatch.append((u"TOKEN ?", i, i + 1))
                    rv = self.uf.makeStr(u"?"); i += 1
                    rv = rel.peg.makeMaybe(vExpr)
                except ParseError as pe:
                    i = st.pop()
                    i, rv = self.parsePEXPR7(i)
        return i, rv
        pass
    @cached
    def parsePEXPR7(self, i):
        rel = self; uf = self.uf; st = []
        st.append(i)
        try:
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError("no reason")
            assert i >= 0
            if self.s[i:i + 1] != u"(": raise ParseError("no reason")
            self.lastMatch.append((u"TOKEN (", i, i + 1))
            rv = self.uf.makeStr(u"("); i += 1
            i, rv = self.parsePEXPR1(i)
            vExpr = rv
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError("no reason")
            assert i >= 0
            if self.s[i:i + 1] != u")": raise ParseError("no reason")
            self.lastMatch.append((u"TOKEN )", i, i + 1))
            rv = self.uf.makeStr(u")"); i += 1
            rv = vExpr
        except ParseError as pe:
            i = st.pop()
            st.append(i)
            try:
                i, rv = self.parseSTRING(i)
                vS = rv
                rv = rel.peg.makeToken(vS)
            except ParseError as pe:
                i = st.pop()
                i, rv = self.parseID(i)
                vName = rv
                rv = rel.peg.makeCall(vName)
        return i, rv
        pass
    @cached
    def parseZADDY(self, i):
        rel = self; uf = self.uf; st = []
        i, rv = self.parseWS(i)
        rvs = []
        while True:
            st.append(i)
            try:
                st.append(i)
                try:
                    i, rv = self.parseRULES(i)
                except ParseError as pe:
                    i = st.pop()
                    st.append(i)
                    try:
                        i, rv = self.parseSIGNATURE(i)
                    except ParseError as pe:
                        i = st.pop()
                        i, rv = self.parseGRAMMAR(i)
                rvs.append(rv)
            except ParseError as pe:
                i = st.pop()
                break
            pass
        rv = rel.uf.makeList(rvs)
        vClss = rv
        i, rv = self.parseWS(i)
        rv = rel.builtin.makeFlatten(uf.makeList([uf.makeList([rel.py.makeImp(uf.makeStr(u'collections'), uf.makeStr(u'defaultdict')), rel.py.makeImp(uf.makeStr(u'rpython.rlib.rfile'), uf.makeStr(u'create_stdio')), rel.py.makeImp(uf.makeStr(u'rpython.rlib.objectmodel'), uf.makeStr(u'specialize, r_dict')), rel.py.makeImp(uf.makeStr(u'rpython.rlib.unroll'), uf.makeStr(u'unrolling_iterable')), rel.py.makeImp(uf.makeStr(u'rpython.rlib.listsort'), uf.makeStr(u'make_timsort_class')), rel.py.makeCompound(uf.makeStr(u'class Result(object)'), uf.makeList([])), rel.py.makeCompound(uf.makeStr(u'class Failed(Result)'), uf.makeList([])), rel.py.makeStatement(uf.makeStr(u'failed = Failed()')), rel.py.makeCompound(uf.makeStr(u'def cached(f, cacheCount=[0])'), uf.makeList([rel.py.makeStatement(uf.makeStr(u'attr = "t" + str(cacheCount[0]); cacheCount[0] += 1')), rel.py.makeStatement(uf.makeStr(u'name = f.__name__')), rel.py.makeStatement(uf.makeStr(u'uname = unicode(name)')), rel.py.makeCompound(uf.makeStr(u'class CacheResult(Result)'), uf.makeList([rel.py.makeStatement(uf.makeStr(u'def __init__(self, i, rv): setattr(self, attr, (i, rv))'))])), rel.py.makeStatement(uf.makeStr(u'cache = {}')), rel.py.makeCompound(uf.makeStr(u'def deco(self, i)'), uf.makeList([rel.py.makeStatement(uf.makeStr(u'key = i')), rel.py.makeRaiseIf(uf.makeStr(u'key in cache and cache[key] is failed')), rel.py.makeStatement(uf.makeStr(u'elif key in cache: return getattr(cache[key], attr)')), rel.py.makeStatement(uf.makeStr(u'cache[key] = failed')), rel.py.makeStatement(uf.makeStr(u'i, rv = f(self, i)')), rel.py.makeStatement(uf.makeStr(u'cache[key] = CacheResult(i, rv)')), rel.py.makeStatement(uf.makeStr(u'self.lastMatch.append((uname, key, i))')), rel.py.makeRet(uf.makeStr(u'i, rv'))])), rel.py.makeStatement(uf.makeStr(u'deco.__name__ = name')), rel.py.makeRet(uf.makeStr(u'deco'))])), rel.py.makeStatement(uf.makeStr(u'ruleNames = []')), rel.py.makeStatement(uf.makeStr(u'letNames = []')), rel.py.makeCompound(uf.makeStr(u'def let(f)'), uf.makeList([rel.py.makeStatement(uf.makeStr(u'letNames.append(f)')), rel.py.makeRet(uf.makeStr(u'f'))])), rel.py.makeStatement(uf.makeStr(u'triggers = defaultdict(list)')), rel.py.makeCompound(uf.makeStr(u'def rewrite(*args)'), uf.makeList([rel.py.makeCompound(uf.makeStr(u'def deco(f)'), uf.makeList([rel.py.makeStatement(uf.makeStr(u'name = f.__name__')), rel.py.makeStatement(uf.makeStr(u'ruleNames.append((name, f))')), rel.py.makeStatement(uf.makeStr(u'for rel in args: triggers[rel].append(name)')), rel.py.makeRet(uf.makeStr(u'f'))])), rel.py.makeRet(uf.makeStr(u'deco'))])), rel.py.makeStatement(uf.makeStr(u'@specialize.call_location()')), rel.py.makeCompound(uf.makeStr(u'def flatten(xs)'), uf.makeList([rel.py.makeStatement(uf.makeStr(u'rv = []')), rel.py.makeStatement(uf.makeStr(u'for x in xs: rv.extend(x)')), rel.py.makeRet(uf.makeStr(u'rv'))])), rel.py.makeCompound(uf.makeStr(u'def intersect(l, r)'), uf.makeList([rel.py.makeStatement(uf.makeStr(u'rv = []')), rel.py.makeCompound(uf.makeStr(u'for x in r'), uf.makeList([rel.py.makeStatement(uf.makeStr(u'if x in l: rv.append(x)'))])), rel.py.makeRet(uf.makeStr(u'rv'))])), rel.py.makeStatement(uf.makeStr(u'def listEq(l, r): return l == r')), rel.py.makeCompound(uf.makeStr(u'def listHash(l)'), uf.makeList([rel.py.makeStatement(uf.makeStr(u'rv = 0')), rel.py.makeStatement(uf.makeStr(u'for x in l: rv += x')), rel.py.makeRet(uf.makeStr(u'rv'))])), rel.py.makeCompound(uf.makeStr(u'class UF(object)'), uf.makeList([rel.py.makeCompound(uf.makeStr(u'def __init__(self)'), uf.makeList([rel.py.makeStatement(uf.makeStr(u'self.uf = [0]')), rel.py.makeStatement(uf.makeStr(u'self.handle2str = {}')), rel.py.makeStatement(uf.makeStr(u'self.str2handle = {}')), rel.py.makeStatement(uf.makeStr(u'self.handle2list = {}')), rel.py.makeStatement(uf.makeStr(u'self.list2handle = r_dict(listEq, listHash)'))])), rel.py.makeCompound(uf.makeStr(u'def make(self)'), uf.makeList([rel.py.makeStatement(uf.makeStr(u'rv = len(self.uf)')), rel.py.makeStatement(uf.makeStr(u'self.uf.append(rv)')), rel.py.makeRet(uf.makeStr(u'rv'))])), rel.py.makeCompound(uf.makeStr(u'def find(self, i)'), uf.makeList([rel.py.makeStatement(uf.makeStr(u'j = self.uf[i]')), rel.py.makeStatement(uf.makeStr(u'while self.uf[j] != j: self.uf[i], j, i = self.uf[j], self.uf[j], j')), rel.py.makeRet(uf.makeStr(u'j'))])), rel.py.makeCompound(uf.makeStr(u'def union(self, i, j)'), uf.makeList([rel.py.makeStatement(uf.makeStr(u'i = self.find(i); j = self.find(j)')), rel.py.makeStatement(uf.makeStr(u'if i != j: self.uf[i] = j')), rel.py.makeRet(uf.makeStr(u'j'))])), rel.py.makeCompound(uf.makeStr(u'def makeStr(self, s)'), uf.makeList([rel.py.makeStatement(uf.makeStr(u'if s in self.str2handle: return self.str2handle[s]')), rel.py.makeStatement(uf.makeStr(u'rv = self.make()')), rel.py.makeStatement(uf.makeStr(u'self.handle2str[rv] = s')), rel.py.makeStatement(uf.makeStr(u'self.str2handle[s] = rv')), rel.py.makeRet(uf.makeStr(u'rv'))])), rel.py.makeCompound(uf.makeStr(u'def findStr(self, i)'), uf.makeList([rel.py.makeStatement(uf.makeStr(u'try: return self.handle2str[self.find(i)]')), rel.py.makeStatement(uf.makeStr(u'except KeyError: raise NoResults("findStr", i)'))])), rel.py.makeCompound(uf.makeStr(u'def makeList(self, l)'), uf.makeList([rel.py.makeStatement(uf.makeStr(u'if l in self.list2handle: return self.list2handle[l]')), rel.py.makeStatement(uf.makeStr(u'rv = self.make()')), rel.py.makeStatement(uf.makeStr(u'self.handle2list[rv] = l')), rel.py.makeStatement(uf.makeStr(u'self.list2handle[l] = rv')), rel.py.makeRet(uf.makeStr(u'rv'))])), rel.py.makeCompound(uf.makeStr(u'def findList(self, i)'), uf.makeList([rel.py.makeStatement(uf.makeStr(u'try: return self.handle2list[self.find(i)]')), rel.py.makeStatement(uf.makeStr(u'except KeyError: raise NoResults("findList", i)'))])), rel.py.makeCompound(uf.makeStr(u'def rebuild(self)'), uf.makeList([rel.py.makeCompound(uf.makeStr(u'for (i, s) in self.handle2str.items()'), uf.makeList([rel.py.makeStatement(uf.makeStr(u'self.handle2str[self.find(i)] = s'))])), rel.py.makeStatement(uf.makeStr(u'q = [(self.find(i), [self.find(x) for x in l]) for (i, l) in self.handle2list.items()]')), rel.py.makeStatement(uf.makeStr(u'self.handle2list.clear()')), rel.py.makeStatement(uf.makeStr(u'self.list2handle.clear()')), rel.py.makeCompound(uf.makeStr(u'for i, l in q'), uf.makeList([rel.py.makeStatement(uf.makeStr(u'self.handle2list[i] = l')), rel.py.makeStatement(uf.makeStr(u'self.list2handle[l] = i'))]))]))])), rel.py.makeStatement(uf.makeStr(u'@specialize.call_location()')), rel.py.makeCompound(uf.makeStr(u'def rebuildRel(uf, d)'), uf.makeList([rel.py.makeStatement(uf.makeStr(u'q = []')), rel.py.makeCompound(uf.makeStr(u'for r in d'), uf.makeList([rel.py.makeStatement(uf.makeStr(u'if isinstance(r, int): q.append(uf.find(r))')), rel.py.makeStatement(uf.makeStr(u'elif len(r) == 1: q.append((uf.find(r[0]),))')), rel.py.makeStatement(uf.makeStr(u'elif len(r) == 2: q.append((uf.find(r[0]), uf.find(r[1])))')), rel.py.makeStatement(uf.makeStr(u'elif len(r) == 3: q.append((uf.find(r[0]), uf.find(r[1]), uf.find(r[2])))')), rel.py.makeStatement(uf.makeStr(u'elif len(r) == 4: q.append((uf.find(r[0]), uf.find(r[1]), uf.find(r[2]), uf.find(r[3])))')), rel.py.makeStatement(uf.makeStr(u'elif len(r) == 5: q.append((uf.find(r[0]), uf.find(r[1]), uf.find(r[2]), uf.find(r[3]), uf.find(r[4])))')), rel.py.makeStatement(uf.makeStr(u'else: assert False, "bob"'))])), rel.py.makeStatement(uf.makeStr(u'd.clear()')), rel.py.makeStatement(uf.makeStr(u'for r in q: d[r] = None'))])), rel.py.makeStatement(uf.makeStr(u'@specialize.call_location()')), rel.py.makeCompound(uf.makeStr(u'def rebuildHash(uf, d)'), uf.makeList([rel.py.makeStatement(uf.makeStr(u'for k, v in d.items(): d[k] = uf.find(v)'))])), rel.py.makeCompound(uf.makeStr(u'class Builtin(object)'), uf.makeList([])), rel.py.makeCompound(uf.makeStr(u'class EmitLine(Builtin)'), uf.makeList([rel.py.makeStatement(uf.makeStr(u'def __init__(self, s): self.s = s')), rel.py.makeStatement(uf.makeStr(u'def out(self, m): return [u" " * (m * 4) + self.s]'))])), rel.py.makeCompound(uf.makeStr(u'class EmitBlock(Builtin)'), uf.makeList([rel.py.makeStatement(uf.makeStr(u'def __init__(self, ls): self.ls = ls')), rel.py.makeStatement(uf.makeStr(u'def out(self, m): return flatten([l.out(m + 1) for l in self.ls])'))])), rel.py.makeCompound(uf.makeStr(u'class Rels(object)'), uf.makeList([rel.py.makeStatement(uf.makeStr(u'dirty = False'))])), rel.py.makeStatement(uf.makeStr(u'allRels = []')), rel.py.makeCompound(uf.makeStr(u'class Builder(object)'), uf.makeList([rel.py.makeStatement(uf.makeStr(u'def Line(self, s): return EmitLine(s)')), rel.py.makeStatement(uf.makeStr(u'def Block(self, ls): return EmitBlock(ls)'))])), rel.py.makeStatement(uf.makeStr(u'builtin = Builder()')), rel.py.makeCompound(uf.makeStr(u'class builtinRels(Rels)'), uf.makeList([rel.py.makeCompound(uf.makeStr(u'def __init__(self, uf)'), uf.makeList([rel.py.makeStatement(uf.makeStr(u'self.uf = uf')), rel.py.makeStatement(uf.makeStr(u'self.Line = {}')), rel.py.makeStatement(uf.makeStr(u'self.Block = {}')), rel.py.makeStatement(uf.makeStr(u'self.Flatten = {}')), rel.py.makeStatement(uf.makeStr(u'self.Length = {}')), rel.py.makeStatement(uf.makeStr(u'self.Join = {}')), rel.py.makeStatement(uf.makeStr(u'self.Concat = {}')), rel.py.makeStatement(uf.makeStr(u'self.hashLine = {}')), rel.py.makeStatement(uf.makeStr(u'self.hashBlock = {}')), rel.py.makeStatement(uf.makeStr(u'self.hashFlatten = {}')), rel.py.makeStatement(uf.makeStr(u'self.hashLength = {}')), rel.py.makeStatement(uf.makeStr(u'self.hashJoin = {}')), rel.py.makeStatement(uf.makeStr(u'self.hashConcat = {}'))])), rel.py.makeCompound(uf.makeStr(u'def rebuild(self)'), uf.makeList([rel.py.makeStatement(uf.makeStr(u'rebuildRel(self.uf, self.Line)')), rel.py.makeStatement(uf.makeStr(u'rebuildRel(self.uf, self.Block)')), rel.py.makeStatement(uf.makeStr(u'rebuildRel(self.uf, self.Flatten)')), rel.py.makeStatement(uf.makeStr(u'rebuildRel(self.uf, self.Length)')), rel.py.makeStatement(uf.makeStr(u'rebuildRel(self.uf, self.Join)')), rel.py.makeStatement(uf.makeStr(u'rebuildRel(self.uf, self.Concat)')), rel.py.makeStatement(uf.makeStr(u'rebuildHash(self.uf, self.hashLine)')), rel.py.makeStatement(uf.makeStr(u'rebuildHash(self.uf, self.hashBlock)')), rel.py.makeStatement(uf.makeStr(u'rebuildHash(self.uf, self.hashFlatten)')), rel.py.makeStatement(uf.makeStr(u'rebuildHash(self.uf, self.hashLength)')), rel.py.makeStatement(uf.makeStr(u'rebuildHash(self.uf, self.hashJoin)')), rel.py.makeStatement(uf.makeStr(u'rebuildHash(self.uf, self.hashConcat)'))])), rel.py.makeCompound(uf.makeStr(u'def makeLine(self, s)'), uf.makeList([rel.py.makeStatement(uf.makeStr(u'rv = self.uf.make()')), rel.py.makeStatement(uf.makeStr(u'self.Line[rv, s] = None')), rel.py.makeRet(uf.makeStr(u'rv'))])), rel.py.makeCompound(uf.makeStr(u'def findLine(self, i)'), uf.makeList([rel.py.makeCompound(uf.makeStr(u'for (x, s) in self.Line'), uf.makeList([rel.py.makeStatement(uf.makeStr(u'if x != i: continue')), rel.py.makeStatement(uf.makeStr(u'try: return EmitLine(self.uf.findStr(s))')), rel.py.makeStatement(uf.makeStr(u'except NoResults: continue'))])), rel.py.makeStatement(uf.makeStr(u'raise NoResults("findLine", i)'))])), rel.py.makeCompound(uf.makeStr(u'def makeBlock(self, ls)'), uf.makeList([rel.py.makeStatement(uf.makeStr(u'rv = self.uf.make()')), rel.py.makeStatement(uf.makeStr(u'self.Block[rv, ls] = None')), rel.py.makeRet(uf.makeStr(u'rv'))])), rel.py.makeCompound(uf.makeStr(u'def findBlock(self, i)'), uf.makeList([rel.py.makeCompound(uf.makeStr(u'for (x, ls) in self.Block'), uf.makeList([rel.py.makeStatement(uf.makeStr(u'if x != i: continue')), rel.py.makeStatement(uf.makeStr(u'try: return EmitBlock([self.findbuiltin(x) for x in self.uf.findList(ls)])')), rel.py.makeStatement(uf.makeStr(u'except NoResults: continue'))])), rel.py.makeStatement(uf.makeStr(u'raise NoResults("findBlock", i)'))])), rel.py.makeCompound(uf.makeStr(u'def makeFlatten(self, ls)'), uf.makeList([rel.py.makeStatement(uf.makeStr(u'k = ls')), rel.py.makeStatement(uf.makeStr(u'if k in self.hashFlatten: return self.hashFlatten[k]')), rel.py.makeStatement(uf.makeStr(u'self.dirty = True')), rel.py.makeStatement(uf.makeStr(u'rv = self.uf.make()')), rel.py.makeStatement(uf.makeStr(u'self.Flatten[rv, ls] = None')), rel.py.makeStatement(uf.makeStr(u'self.hashFlatten[k] = rv')), rel.py.makeRet(uf.makeStr(u'rv'))])), rel.py.makeCompound(uf.makeStr(u'def makeLength(self, s)'), uf.makeList([rel.py.makeStatement(uf.makeStr(u'k = s')), rel.py.makeStatement(uf.makeStr(u'if k in self.hashLength: return self.hashLength[k]')), rel.py.makeStatement(uf.makeStr(u'self.dirty = True')), rel.py.makeStatement(uf.makeStr(u'rv = self.uf.make()')), rel.py.makeStatement(uf.makeStr(u'self.Length[rv, s] = None')), rel.py.makeStatement(uf.makeStr(u'self.hashLength[k] = rv')), rel.py.makeRet(uf.makeStr(u'rv'))])), rel.py.makeCompound(uf.makeStr(u'def makeJoin(self, s, ps)'), uf.makeList([rel.py.makeStatement(uf.makeStr(u'k = s, ps')), rel.py.makeStatement(uf.makeStr(u'if k in self.hashJoin: return self.hashJoin[k]')), rel.py.makeStatement(uf.makeStr(u'self.dirty = True')), rel.py.makeStatement(uf.makeStr(u'rv = self.uf.make()')), rel.py.makeStatement(uf.makeStr(u'self.Join[rv, s, ps] = None')), rel.py.makeStatement(uf.makeStr(u'self.hashJoin[k] = rv')), rel.py.makeRet(uf.makeStr(u'rv'))])), rel.py.makeCompound(uf.makeStr(u'def makeConcat(self, p, ps)'), uf.makeList([rel.py.makeStatement(uf.makeStr(u'k = p, ps')), rel.py.makeStatement(uf.makeStr(u'if k in self.hashConcat: return self.hashConcat[k]')), rel.py.makeStatement(uf.makeStr(u'self.dirty = True')), rel.py.makeStatement(uf.makeStr(u'rv = self.uf.make()')), rel.py.makeStatement(uf.makeStr(u'self.Concat[rv, p, ps] = None')), rel.py.makeStatement(uf.makeStr(u'self.hashConcat[k] = rv')), rel.py.makeRet(uf.makeStr(u'rv'))])), rel.py.makeCompound(uf.makeStr(u'def findbuiltin(self, i)'), uf.makeList([rel.py.makeCompound(uf.makeStr(u'try'), uf.makeList([rel.py.makeRet(uf.makeStr(u'self.findLine(i)'))])), rel.py.makeCompound(uf.makeStr(u'except NoResults'), uf.makeList([rel.py.makeRet(uf.makeStr(u'self.findBlock(i)'))]))]))])), rel.py.makeStatement(uf.makeStr(u'allRels.append(("builtin", builtinRels))')), rel.py.makeCompound(uf.makeStr(u'class ParseError(Exception)'), uf.makeList([rel.py.makeStatement(uf.makeStr(u'def __init__(self, reason): self.reason = reason'))])), rel.py.makeCompound(uf.makeStr(u'class NoResults(Exception)'), uf.makeList([rel.py.makeCompound(uf.makeStr(u'def __init__(self, message, handle)'), uf.makeList([rel.py.makeStatement(uf.makeStr(u'self.message = message; self.handle = handle'))]))])), rel.py.makeCompound(uf.makeStr(u'def lineNumber(s, i)'), uf.makeList([rel.py.makeStatement(uf.makeStr(u'assert i >= 0')), rel.py.makeRet(uf.makeStr(u's.count(unichr(10), 0, i)'))])), rel.py.makeStatement(uf.makeStr(u'SortTraces = make_timsort_class(lt=lambda l, r: l[2] > r[2])')), rel.py.makeCompound(uf.makeStr(u'def main(argv)'), uf.makeList([rel.py.makeStatement(uf.makeStr(u'stdin, stdout, stderr = create_stdio()')), rel.py.makeStatement(uf.makeStr(u'stderr.write("Registered %d rewrite rules\\n" % len(frozenRules))')), rel.py.makeStatement(uf.makeStr(u'stderr.write("Registered %d rewrite triggers\\n" % len(frozenTriggers))')), rel.py.makeStatement(uf.makeStr(u'uf = UF()')), rel.py.makeStatement(uf.makeStr(u'parser = MainParser(stdin.read().decode("utf-8"), uf)')), rel.py.makeHandler(uf.makeList([rel.py.makeStatement(uf.makeStr(u'i, l = parser.parse()')), rel.py.makeConditional(uf.makeStr(u'i != len(parser.s)'), uf.makeList([rel.py.makeStatement(uf.makeStr(u'raise ParseError("Failed to consume all input")'))])), rel.py.makeStatement(uf.makeStr(u'l = parser.builtin.makeFlatten(l)')), rel.py.makeCompound(uf.makeStr(u'for iteration in range(25)'), uf.makeList([rel.py.makeStatement(uf.makeStr(u'rulesToTry = []')), rel.py.makeCompound(uf.makeStr(u'for r in unrolledRels'), uf.makeList([rel.py.makeStatement(uf.makeStr(u'rel = getattr(parser, r)')), rel.py.makeStatement(uf.makeStr(u'rulesToTry.extend(frozenTriggers.get(r, []))')), rel.py.makeStatement(uf.makeStr(u'rel.rebuild()')), rel.py.makeStatement(uf.makeStr(u'rel.dirty = False'))])), rel.py.makeStatement(uf.makeStr(u'if not rulesToTry: break')), rel.py.makeStatement(uf.makeStr(u'uf.rebuild()')), rel.py.makeStatement(uf.makeStr(u'stderr.write("Iteration %d: Union/find: %d handles\\n" % (iteration, len(uf.uf)))')), rel.py.makeStatement(uf.makeStr(u'count = 0')), rel.py.makeStatement(uf.makeStr(u'stderr.write("Iteration %d: %d rules to try\\n" % (iteration, len(rulesToTry)))')), rel.py.makeCompound(uf.makeStr(u'for name in rulesToTry'), uf.makeList([rel.py.makeStatement(uf.makeStr(u'c = frozenRules[name](uf, parser)')), rel.py.makeStatement(uf.makeStr(u'if c: stderr.write("Rule %s: %d transactions\\n" % (name, c))')), rel.py.makeStatement(uf.makeStr(u'count += c'))])), rel.py.makeStatement(uf.makeStr(u'stderr.write("Iteration %d: %d applications\\n" % (iteration, count))'))])), rel.py.makeStatement(uf.makeStr(u'buf = []')), rel.py.makeStatement(uf.makeStr(u'ls = uf.findList(l)')), rel.py.makeStatement(uf.makeStr(u'stderr.write("Optimized to %d builtin blocks\\n" % len(ls))')), rel.py.makeStatement(uf.makeStr(u'for rule in ls: buf.extend(parser.builtin.findbuiltin(rule).out(0))')), rel.py.makeStatement(uf.makeStr(u'stdout.write(u"\\n".join(buf).encode("utf-8"))')), rel.py.makeStatement(uf.makeStr(u'stderr.write("Wrote %d lines to stdout\\n" % len(buf))')), rel.py.makeRet(uf.makeStr(u'0'))]), uf.makeList([rel.py.makeStatement(uf.makeStr(u'stderr.write("Parse error: %s\\n" % pe.reason)')), rel.py.makeStatement(uf.makeStr(u'SortTraces(parser.lastMatch).sort()')), rel.py.makeStatement(uf.makeStr(u'newlines = [0]')), rel.py.makeCompound(uf.makeStr(u'for line in parser.s.split(u"\\n")'), uf.makeList([rel.py.makeStatement(uf.makeStr(u'newlines.append(newlines[-1] + len(line) + 1)'))])), rel.py.makeCompound(uf.makeStr(u'for k, start, stop in parser.lastMatch[:10]'), uf.makeList([rel.py.makeStatement(uf.makeStr(u'startLine = lineNumber(parser.s, start)')), rel.py.makeStatement(uf.makeStr(u'startCol = start - newlines[startLine]')), rel.py.makeStatement(uf.makeStr(u'stopLine = lineNumber(parser.s, stop)')), rel.py.makeStatement(uf.makeStr(u'stopCol = stop - newlines[stopLine]')), rel.py.makeStatement(uf.makeStr(u't = k.encode("utf-8"), startLine + 1, startCol, stopLine + 1, stopCol')), rel.py.makeStatement(uf.makeStr(u'stderr.write(("Trail: %s (%d:%d - %d:%d)" % t) + chr(10))'))])), rel.py.makeRet(uf.makeStr(u'1'))])), rel.py.makeCompound(uf.makeStr(u'except NoResults as nr'), uf.makeList([rel.py.makeStatement(uf.makeStr(u'stderr.write("No results: %s\\n" % nr.message)')), rel.py.makeRet(uf.makeStr(u'1'))]))]))]), rel.builtin.makeFlatten(vClss), uf.makeList([rel.py.makeStatement(uf.makeStr(u'@rewrite("builtin")')), rel.py.makeCompound(uf.makeStr(u'def builtinFlatten(uf, rel)'), uf.makeList([rel.py.makeStatement(uf.makeStr(u'q = []')), rel.py.makeCompound(uf.makeStr(u'for (vRoot, vLs) in rel.builtin.Flatten'), uf.makeList([rel.py.makeCompound(uf.makeStr(u'try'), uf.makeList([rel.py.makeStatement(uf.makeStr(u'ls = uf.findList(vLs)')), rel.py.makeStatement(uf.makeStr(u'if len(ls) == 1: target = ls[0]')), rel.py.makeStatement(uf.makeStr(u'else: target = uf.makeList(flatten([uf.findList(l) for l in ls]))')), rel.py.makeStatement(uf.makeStr(u'uf.union(vRoot, target)')), rel.py.makeStatement(uf.makeStr(u'q.append((vRoot, vLs))'))])), rel.py.makeStatement(uf.makeStr(u'except NoResults: continue'))])), rel.py.makeStatement(uf.makeStr(u'for k in q: del rel.builtin.Flatten[k]')), rel.py.makeRet(uf.makeStr(u'len(q)'))])), rel.py.makeStatement(uf.makeStr(u'@rewrite("builtin")')), rel.py.makeCompound(uf.makeStr(u'def builtinLength(uf, rel)'), uf.makeList([rel.py.makeStatement(uf.makeStr(u'q = []')), rel.py.makeCompound(uf.makeStr(u'for (vRoot, vS) in rel.builtin.Length'), uf.makeList([rel.py.makeCompound(uf.makeStr(u'try'), uf.makeList([rel.py.makeStatement(uf.makeStr(u's = uf.findStr(vS)')), rel.py.makeStatement(uf.makeStr(u'target = uf.makeStr(str(len(s)).decode("utf-8"))')), rel.py.makeStatement(uf.makeStr(u'uf.union(vRoot, target)')), rel.py.makeStatement(uf.makeStr(u'q.append((vRoot, vS))'))])), rel.py.makeStatement(uf.makeStr(u'except NoResults: continue'))])), rel.py.makeStatement(uf.makeStr(u'for k in q: del rel.builtin.Length[k]')), rel.py.makeRet(uf.makeStr(u'len(q)'))])), rel.py.makeStatement(uf.makeStr(u'@rewrite("builtin")')), rel.py.makeCompound(uf.makeStr(u'def builtinJoin(uf, rel)'), uf.makeList([rel.py.makeStatement(uf.makeStr(u'q = []')), rel.py.makeCompound(uf.makeStr(u'for (vRoot, vS, vPs) in rel.builtin.Join'), uf.makeList([rel.py.makeCompound(uf.makeStr(u'try'), uf.makeList([rel.py.makeStatement(uf.makeStr(u's = uf.findStr(vS)')), rel.py.makeStatement(uf.makeStr(u'ps = [uf.findStr(i) for i in uf.findList(vPs)]')), rel.py.makeStatement(uf.makeStr(u'target = uf.makeStr(s.join(ps))')), rel.py.makeStatement(uf.makeStr(u'uf.union(vRoot, target)')), rel.py.makeStatement(uf.makeStr(u'q.append((vRoot, vS, vPs))'))])), rel.py.makeStatement(uf.makeStr(u'except NoResults: continue'))])), rel.py.makeStatement(uf.makeStr(u'for k in q: del rel.builtin.Join[k]')), rel.py.makeRet(uf.makeStr(u'len(q)'))])), rel.py.makeStatement(uf.makeStr(u'@rewrite("builtin")')), rel.py.makeCompound(uf.makeStr(u'def builtinConcat(uf, rel)'), uf.makeList([rel.py.makeStatement(uf.makeStr(u'q = []')), rel.py.makeCompound(uf.makeStr(u'for (vRoot, vS, vPs) in rel.builtin.Concat'), uf.makeList([rel.py.makeCompound(uf.makeStr(u'try'), uf.makeList([rel.py.makeStatement(uf.makeStr(u'ps = [uf.findStr(i) for i in uf.findList(vPs)]')), rel.py.makeConditional(uf.makeStr(u'len(ps)'), uf.makeList([rel.py.makeStatement(uf.makeStr(u's = uf.findStr(vS)')), rel.py.makeStatement(uf.makeStr(u'target = uf.makeStr(s + u"".join(ps))'))])), rel.py.makeStatement(uf.makeStr(u'else: target = vS')), rel.py.makeStatement(uf.makeStr(u'uf.union(vRoot, target)')), rel.py.makeStatement(uf.makeStr(u'q.append((vRoot, vS, vPs))'))])), rel.py.makeStatement(uf.makeStr(u'except NoResults: continue'))])), rel.py.makeStatement(uf.makeStr(u'for k in q: del rel.builtin.Concat[k]')), rel.py.makeRet(uf.makeStr(u'len(q)'))])), rel.py.makeStatement(uf.makeStr(u'frozenRels = dict(allRels)')), rel.py.makeStatement(uf.makeStr(u'unrolledRels = unrolling_iterable(frozenRels)')), rel.py.makeStatement(uf.makeStr(u'frozenRules = dict(ruleNames)')), rel.py.makeStatement(uf.makeStr(u'unrolledRules = unrolling_iterable(frozenRules)')), rel.py.makeStatement(uf.makeStr(u'frozenLets = letNames[:]')), rel.py.makeStatement(uf.makeStr(u'unrolledLets = unrolling_iterable(frozenLets)')), rel.py.makeStatement(uf.makeStr(u'frozenTriggers = dict(triggers)'))])]))
        return i, rv
        pass
    pass
MainParser = ZADDYParser
@rewrite("builtin")
def builtinFlatten(uf, rel):
    q = []
    for (vRoot, vLs) in rel.builtin.Flatten:
        try:
            ls = uf.findList(vLs)
            if len(ls) == 1: target = ls[0]
            else: target = uf.makeList(flatten([uf.findList(l) for l in ls]))
            uf.union(vRoot, target)
            q.append((vRoot, vLs))
            pass
        except NoResults: continue
        pass
    for k in q: del rel.builtin.Flatten[k]
    return len(q)
    pass
@rewrite("builtin")
def builtinLength(uf, rel):
    q = []
    for (vRoot, vS) in rel.builtin.Length:
        try:
            s = uf.findStr(vS)
            target = uf.makeStr(str(len(s)).decode("utf-8"))
            uf.union(vRoot, target)
            q.append((vRoot, vS))
            pass
        except NoResults: continue
        pass
    for k in q: del rel.builtin.Length[k]
    return len(q)
    pass
@rewrite("builtin")
def builtinJoin(uf, rel):
    q = []
    for (vRoot, vS, vPs) in rel.builtin.Join:
        try:
            s = uf.findStr(vS)
            ps = [uf.findStr(i) for i in uf.findList(vPs)]
            target = uf.makeStr(s.join(ps))
            uf.union(vRoot, target)
            q.append((vRoot, vS, vPs))
            pass
        except NoResults: continue
        pass
    for k in q: del rel.builtin.Join[k]
    return len(q)
    pass
@rewrite("builtin")
def builtinConcat(uf, rel):
    q = []
    for (vRoot, vS, vPs) in rel.builtin.Concat:
        try:
            ps = [uf.findStr(i) for i in uf.findList(vPs)]
            if len(ps):
                s = uf.findStr(vS)
                target = uf.makeStr(s + u"".join(ps))
            else: target = vS
            uf.union(vRoot, target)
            q.append((vRoot, vS, vPs))
            pass
        except NoResults: continue
        pass
    for k in q: del rel.builtin.Concat[k]
    return len(q)
    pass
frozenRels = dict(allRels)
unrolledRels = unrolling_iterable(frozenRels)
frozenRules = dict(ruleNames)
unrolledRules = unrolling_iterable(frozenRules)
frozenLets = letNames[:]
unrolledLets = unrolling_iterable(frozenLets)
frozenTriggers = dict(triggers)