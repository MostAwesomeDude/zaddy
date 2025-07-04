from collections import defaultdict
from rpython.rlib.rfile import create_stdio
from rpython.rlib.objectmodel import specialize, r_dict
from rpython.rlib.signature import finishsigs, signature, types
from rpython.annotator.model import SomeList, SomeTuple
from rpython.annotator.listdef import ListDef
from rpython.rlib.unroll import unrolling_iterable
from rpython.rlib.listsort import make_timsort_class
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
    @signature(types.self(), types.int(),
               returns=SomeTuple((types.int(), types.int())))
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
letNames = []
def let(f):
    letNames.append(f)
    return f
triggers = defaultdict(list)
def rewrite(*args):
    def deco(f):
        name = f.__name__
        ruleNames.append((name, f))
        for rel in args: triggers[rel].append(name)
        return f
    return deco
@specialize.call_location()
def flatten(xs):
    rv = []
    for x in xs: rv.extend(x)
    return rv
def intersect(l, r):
    rv = []
    for x in r:
        if x in l: rv.append(x)
    return rv
def listEq(l, r): return l == r
def listHash(l):
    rv = 0
    for x in l: rv += x
    return rv
@finishsigs
class UF(object):
    def __init__(self):
        self.uf = [0]
        self.handle2str = {}
        self.str2handle = {}
        self.handle2list = {}
        self.list2handle = r_dict(listEq, listHash)

    @signature(types.self(), returns=types.int())
    def make(self):
        rv = len(self.uf)
        self.uf.append(rv)
        return rv
    @signature(types.self(), types.int(), returns=types.int())
    def find(self, i):
        j = self.uf[i]
        while self.uf[j] != j:
            self.uf[i], j, i = self.uf[j], self.uf[j], j
        return j
    @signature(types.self(), types.int(), types.int(), returns=types.int())
    def union(self, i, j):
        i = self.find(i); j = self.find(j)
        if i != j: self.uf[i] = j
        return j
    @signature(types.self(), types.unicode(), returns=types.int())
    def makeStr(self, s):
        if s in self.str2handle: return self.str2handle[s]
        rv = self.make()
        self.handle2str[rv] = s
        self.str2handle[s] = rv
        return rv
    @signature(types.self(), types.int(), returns=types.unicode())
    def findStr(self, i):
        try: return self.handle2str[self.find(i)]
        except KeyError: raise NoResults("findStr", i)
    def makeList(self, l):
        if l in self.list2handle: return self.list2handle[l]
        rv = self.make()
        self.handle2list[rv] = l
        self.list2handle[l] = rv
        return rv
    def findList(self, i):
        try: return self.handle2list[self.find(i)]
        except KeyError: raise NoResults("findList", i)
    def rebuild(self):
        # NB: saturate handle -> str map, don't unify distinct strings!
        for (i, s) in self.handle2str.items():
            self.handle2str[self.find(i)] = s
        # NB: rebuild both list maps with a single find, equivalent cost
        q = [(self.find(i), [self.find(x) for x in l])
             for (i, l) in self.handle2list.items()]
        self.handle2list.clear()
        self.list2handle.clear()
        for i, l in q:
            self.handle2list[i] = l
            self.list2handle[l] = i

@specialize.call_location()
def rebuildRel(uf, d):
    q = []
    for r in d:
        if isinstance(r, int): q.append(uf.find(r))
        elif len(r) == 2: q.append((uf.find(r[0]), uf.find(r[1])))
        elif len(r) == 3: q.append((uf.find(r[0]), uf.find(r[1]), uf.find(r[2])))
        elif len(r) == 4: q.append((uf.find(r[0]), uf.find(r[1]), uf.find(r[2]), uf.find(r[3])))
        elif len(r) == 5: q.append((uf.find(r[0]), uf.find(r[1]), uf.find(r[2]), uf.find(r[3]), uf.find(r[4])))
        else: assert False, "bob"
    d.clear()
    for r in q: d[r] = None
@specialize.call_location()
def rebuildHash(uf, d):
    for k, v in d.items(): d[k] = uf.find(v)
allRels = []
class Builtin(object): pass
class EmitLine(Builtin):
    def __init__(self, s): self.s = s
    def out(self, m): return [u" " * (m * 4) + self.s]
class EmitBlock(Builtin):
    def __init__(self, ls): self.ls = ls
    def out(self, m): return flatten([b.out(m + 1) for b in self.ls])
class Rels(object): dirty = False
class builtinRels(Rels):
    def __init__(self, uf):
        self.uf = uf
        self.Line = {}; self.Block = {}
        self.Flatten = {}; self.Length = {}
        self.Join = {}; self.hashJoin = {}
        self.Concat = {}; self.hashConcat = {}
        self.hashLine = {}
        self.hashBlock = {}
        self.hashFlatten = {}; self.hashLength = {}
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
        rebuildHash(self.uf, self.hashConcat)
        rebuildHash(self.uf, self.hashJoin)
    def makeLine(self, s):
        k = s
        if k in self.hashLine: return self.hashLine[k]
        self.dirty = True
        rv = self.uf.make()
        self.Line[rv, s] = None
        self.hashLine[k] = rv
        return rv
    def findLine(self, i):
        for (x, s) in self.Line:
            if x != i: continue
            try: return EmitLine(self.uf.findStr(s))
            except NoResults: continue
        raise NoResults("findLine", i)
    def makeBlock(self, ls):
        k = ls
        if k in self.hashBlock: return self.hashBlock[k]
        self.dirty = True
        rv = self.uf.make()
        self.Block[rv, ls] = None
        self.hashBlock[k] = rv
        return rv
    def findBlock(self, i):
        for (x, ls) in self.Block:
            if x != i: continue
            try:
                return EmitBlock([self.findbuiltin(x) for x in self.uf.findList(ls)])
            except NoResults: continue
        raise NoResults("findBlock", i)
    def makeFlatten(self, ls):
        k = ls
        if k in self.hashFlatten: return self.hashFlatten[k]
        self.dirty = True
        rv = self.uf.make()
        self.Flatten[rv, ls] = None
        self.hashFlatten[k] = rv
        return rv
    def makeLength(self, ls):
        k = ls
        if k in self.hashLength: return self.hashLength[k]
        self.dirty = True
        rv = self.uf.make()
        self.Length[rv, ls] = None
        self.hashLength[k] = rv
        return rv
    def makeConcat(self, s, ps):
        k = s, ps
        if k in self.hashConcat: return self.hashConcat[k]
        self.dirty = True
        rv = self.uf.make()
        self.Concat[rv, s, ps] = None
        self.hashConcat[k] = rv
        return rv
    def makeJoin(self, s, ps):
        k = s, ps
        if k in self.hashJoin: return self.hashJoin[k]
        self.dirty = True
        rv = self.uf.make()
        self.Join[rv, s, ps] = None
        self.hashJoin[k] = rv
        return rv
    def findbuiltin(self, i):
        try:
            return self.findLine(i)
        except NoResults:
            return self.findBlock(i)
allRels.append(("builtin", builtinRels))
@rewrite("builtin")
def builtinFlattenList(uf, rel):
    q = []
    for (vRoot, vLs) in rel.builtin.Flatten:
        try:
            ls = uf.findList(vLs)
            # if len(ls) == 1: target = ls[0]
            target = uf.makeList(flatten([uf.findList(l) for l in ls]))
            uf.union(vRoot, target)
            q.append((vRoot, vLs))
        except NoResults: continue
    for k in q: del rel.builtin.Flatten[k]
    return len(q)
@rewrite("builtin")
def builtinLength(uf, rel):
    q = []
    for (vRoot, vS) in rel.builtin.Length:
        try:
            s = uf.findStr(vS)
            target = uf.makeStr(str(len(s)).decode("utf-8"))
            uf.union(vRoot, target)
            q.append((vRoot, vS))
        except NoResults: continue
    for k in q: del rel.builtin.Length[k]
    return len(q)
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
        except NoResults: continue
    for k in q: del rel.builtin.Join[k]
    return len(q)
@rewrite("builtin")
def builtinConcat(uf, rel):
    q = []
    for (vRoot, vP, vPs) in rel.builtin.Concat:
        try:
            ps = [uf.findStr(i) for i in uf.findList(vPs)]
            if len(ps):
                s = uf.findStr(vP)
                target = uf.makeStr(s + u"".join(ps))
            else: target = vP
            uf.union(vRoot, target)
            q.append((vRoot, vP, vPs))
        except NoResults: continue
    for k in q: del rel.builtin.Concat[k]
    return len(q)
class ParseError(Exception): pass
class NoResults(Exception):
    def __init__(self, message, handle):
        self.message = message
        self.handle = handle
def lineNumber(s, i):
    assert i >= 0
    return s.count(unichr(10), 0, i)
def debugHandle(uf, rel, i, m=0):
    stdin, stdout, stderr = create_stdio()
    j = uf.find(i)
    margin = ' ' * m
    stderr.write("Debug: %sHandle %d -> %d\n" % (margin, i, j))
    if j in uf.handle2str:
        s = uf.handle2str[j].encode("utf-8")
        if len(s) < 25:
            stderr.write("Debug: %sHandle %d: string '%s'\n" % (margin, j, s))
        else:
            stderr.write("Debug: %sHandle %d: string of %d bytes\n" %
                         (margin, j, len(s)))
    if j in uf.handle2list:
        l = uf.handle2list[j]
        stderr.write("Debug: %sHandle %d: list of %d items:\n" % (margin, j, len(l)))
        for i, x in enumerate(l):
            stderr.write("      : %s[%d]:\n" % (margin, i))
            debugHandle(uf, rel, x, m=m+1)
    for row in rel.builtin.Line:
        if row[0] == j:
            stderr.write("Debug: %sHandle %d: builtin.Line of:\n" %
                         (margin, j))
            debugHandle(uf, rel, row[1], m=m+1)
    for row in rel.builtin.Block:
        if row[0] == j:
            stderr.write("Debug: %sHandle %d: builtin.Block of:\n" %
                         (margin, j))
            debugHandle(uf, rel, row[1], m=m+1)
    for row in rel.builtin.Join:
        if row[0] == j:
            stderr.write("Debug: %sHandle %d: builtin.Join of:\n" %
                         (margin, j))
            debugHandle(uf, rel, row[1], m=m+1)
            debugHandle(uf, rel, row[2], m=m+1)
    for row in rel.builtin.Concat:
        if row[0] == j:
            stderr.write("Debug: %sHandle %d: builtin.Concat of:\n" %
                         (margin, j))
            debugHandle(uf, rel, row[1], m=m+1)
            debugHandle(uf, rel, row[2], m=m+1)
    for row in rel.builtin.Flatten:
        if row[0] == j:
            stderr.write("Debug: %sHandle %d: builtin.Flatten of:\n" %
                         (margin, j))
            debugHandle(uf, rel, row[1], m=m+1)
    for row in rel.py.Statement:
        if row[0] == j:
            stderr.write("Debug: %sHandle %d: py.Statement of:\n" %
                         (margin, j))
            debugHandle(uf, rel, row[1], m=m+1)
    for row in rel.py.Ret:
        if row[0] == j:
            stderr.write("Debug: %sHandle %d: py.Ret of:\n" %
                         (margin, j))
            debugHandle(uf, rel, row[1], m=m+1)
    for row in rel.py.RaiseIf:
        if row[0] == j:
            stderr.write("Debug: %sHandle %d: py.RaiseIf of:\n" %
                         (margin, j))
            debugHandle(uf, rel, row[1], m=m+1)
    for row in rel.py.Compound:
        if row[0] == j:
            stderr.write("Debug: %sHandle %d: py.Compound of:\n" %
                         (margin, j))
            debugHandle(uf, rel, row[1], m=m+1)
            debugHandle(uf, rel, row[2], m=m+1)
    for row in rel.py.Conditional:
        if row[0] == j:
            stderr.write("Debug: %sHandle %d: py.Conditional of:\n" %
                         (margin, j))
            debugHandle(uf, rel, row[1], m=m+1)
            debugHandle(uf, rel, row[2], m=m+1)
    for row in rel.py.Handler:
        if row[0] == j:
            stderr.write("Debug: %sHandle %d: py.Handler of:\n" %
                         (margin, j))
            debugHandle(uf, rel, row[1], m=m+1)
            debugHandle(uf, rel, row[2], m=m+1)
    for row in rel.zephyr.Con:
        if row[0] == j:
            stderr.write("Debug: %sHandle %d: zephyr.Con of:\n" %
                         (margin, j))
            debugHandle(uf, rel, row[1], m=m+1)
            debugHandle(uf, rel, row[2], m=m+1)
    for row in rel.peg.Some:
        if row[0] == j:
            stderr.write("Debug: %sHandle %d: peg.Some of:\n" %
                         (margin, j))
            debugHandle(uf, rel, row[1], m=m+1)
    for row in rel.peg.Any:
        if row[0] == j:
            stderr.write("Debug: %sHandle %d: peg.Any of:\n" %
                         (margin, j))
            debugHandle(uf, rel, row[1], m=m+1)
SortTraces = make_timsort_class(lt=lambda l, r: l[2] > r[2])
def main(argv):
    stdin, stdout, stderr = create_stdio()
    stderr.write("Registered %d rewrite rules\n" % len(frozenRules))
    stderr.write("Registered %d rewrite triggers\n" % len(frozenTriggers))
    uf = UF()
    parser = MainParser(stdin.read().decode("utf-8"), uf)
    l = 0
    try:
        i, l = parser.parse()
        if i < len(parser.s):
            stderr.write("Error: Failed to consume all input\n")
            raise ParseError()
        l = parser.builtin.makeFlatten(l)
        for iteration in range(25):
            rulesToTry = []
            for r in unrolledRels:
                rel = getattr(parser, r)
                # if rel.dirty:
                rulesToTry.extend(frozenTriggers.get(r, []))
                rel.rebuild()
                rel.dirty = False
            if not rulesToTry: break
            uf.rebuild()
            stderr.write("Iteration %d: Union/find: %d handles\n" %
                         (iteration, len(uf.uf)))
            count = 0
            stderr.write("Iteration %d: %d rules to try\n" %
                         (iteration, len(rulesToTry)))
            for name in rulesToTry:
                c = frozenRules[name](uf, parser)
                if c: stderr.write("Rule %s: %d transactions\n" % (name, c))
                count += c
            stderr.write("Iteration %d: %d applications\n" % (iteration, count))
        buf = []
        ls = uf.findList(l)
    except ParseError:
        SortTraces(parser.lastMatch).sort()
        newlines = [0]
        for line in parser.s.split(u"\n"):
            newlines.append(newlines[-1] + len(line) + 1)
        for k, start, stop in parser.lastMatch[:10]:
            startLine = lineNumber(parser.s, start)
            startCol = start - newlines[startLine]
            stopLine = lineNumber(parser.s, stop)
            stopCol = stop - newlines[stopLine]
            t = k.encode("utf-8"), startLine + 1, startCol, stopLine + 1, stopCol
            stderr.write(("Trail: %s (%d:%d - %d:%d)" % t) + chr(10))
        return 1
    except NoResults as nr:
        stderr.write("No rewrite results during parse: %s\n" % nr.message)
        stderr.write("Trace of offending root:\n")
        debugHandle(uf, parser, nr.handle)
        return 1
    else:
        stderr.write("Optimized to %d builtin blocks\n" % len(ls))
        for i, rule in enumerate(ls):
            stderr.write("Emitting block %d\n" % i)
            try: buf.extend(parser.builtin.findbuiltin(rule).out(0))
            except NoResults as nr:
                stderr.write("No rewrite results: %s\n" % nr.message)
                stderr.write("Trace of block:\n")
                debugHandle(uf, parser, nr.handle)
                return 1
        stdout.write(u"\n".join(buf).encode("utf-8"))
        stderr.write("Wrote %d lines to stdout\n" % len(buf))
        return 0
selfSrc = open(__file__).read().decode("utf-8").split(u"\n")[:460]

# XXX






















class pyRels(Rels):
    def __init__(self, uf):
        self.uf = uf
        self.Statement = {}
        self.hashStatement = {}
        self.Ret = {}
        self.hashRet = {}
        self.RaiseIf = {}
        self.hashRaiseIf = {}
        self.Compound = {}
        self.hashCompound = {}
        self.Conditional = {}
        self.hashConditional = {}
        self.Handler = {}
        self.hashHandler = {}
    def rebuild(self):
        rebuildRel(self.uf, self.Statement)
        rebuildRel(self.uf, self.Ret)
        rebuildRel(self.uf, self.RaiseIf)
        rebuildRel(self.uf, self.Compound)
        rebuildRel(self.uf, self.Conditional)
        rebuildRel(self.uf, self.Handler)
        rebuildHash(self.uf, self.hashStatement)
        rebuildHash(self.uf, self.hashRet)
        rebuildHash(self.uf, self.hashRaiseIf)
        rebuildHash(self.uf, self.hashCompound)
        rebuildHash(self.uf, self.hashConditional)
        rebuildHash(self.uf, self.hashHandler)
    def makeStatement(self, line):
        self.dirty = True
        k = line
        if k in self.hashStatement:
            return self.hashStatement[k]
        rv = self.uf.make()
        self.Statement[rv, line] = None
        self.hashStatement[k] = rv
        return rv
    def makeRet(self, expr):
        self.dirty = True
        k = expr
        if k in self.hashRet:
            return self.hashRet[k]
        rv = self.uf.make()
        self.Ret[rv, expr] = None
        self.hashRet[k] = rv
        return rv
    def makeRaiseIf(self, test):
        self.dirty = True
        k = test
        if k in self.hashRaiseIf:
            return self.hashRaiseIf[k]
        rv = self.uf.make()
        self.RaiseIf[rv, test] = None
        self.hashRaiseIf[k] = rv
        return rv
    def makeCompound(self, head, block):
        self.dirty = True
        k = head, block
        if k in self.hashCompound:
            return self.hashCompound[k]
        rv = self.uf.make()
        self.Compound[rv, head, block] = None
        self.hashCompound[k] = rv
        return rv
    def makeConditional(self, test, block):
        self.dirty = True
        k = test, block
        if k in self.hashConditional:
            return self.hashConditional[k]
        rv = self.uf.make()
        self.Conditional[rv, test, block] = None
        self.hashConditional[k] = rv
        return rv
    def makeHandler(self, block, handler):
        self.dirty = True
        k = block, handler
        if k in self.hashHandler:
            return self.hashHandler[k]
        rv = self.uf.make()
        self.Handler[rv, block, handler] = None
        self.hashHandler[k] = rv
        return rv
allRels.append(("py", pyRels))
class pegRels(Rels):
    def __init__(self, uf):
        self.uf = uf
        self.Null = self.uf.make()
        self.Token = {}
        self.hashToken = {}
        self.Call = {}
        self.hashCall = {}
        self.Sequence = {}
        self.hashSequence = {}
        self.Choice = {}
        self.hashChoice = {}
        self.Any = {}
        self.hashAny = {}
        self.Some = {}
        self.hashSome = {}
        self.Maybe = {}
        self.hashMaybe = {}
        self.Positive = {}
        self.hashPositive = {}
        self.Negative = {}
        self.hashNegative = {}
        self.Capture = {}
        self.hashCapture = {}
        self.Production = {}
        self.hashProduction = {}
        self.NamePatt = {}
        self.hashNamePatt = {}
        self.TuplePatt = {}
        self.hashTuplePatt = {}
    def rebuild(self):
        rebuildRel(self.uf, self.NamePatt)
        rebuildRel(self.uf, self.Any)
        rebuildRel(self.uf, self.Call)
        rebuildRel(self.uf, self.Capture)
        rebuildRel(self.uf, self.Choice)
        rebuildRel(self.uf, self.Maybe)
        rebuildRel(self.uf, self.NamePatt)
        rebuildRel(self.uf, self.Negative)
        rebuildRel(self.uf, self.Positive)
        rebuildRel(self.uf, self.Production)
        rebuildRel(self.uf, self.Sequence)
        rebuildRel(self.uf, self.Some)
        rebuildRel(self.uf, self.Token)
        rebuildRel(self.uf, self.TuplePatt)
        rebuildHash(self.uf, self.hashAny)
        rebuildHash(self.uf, self.hashCall)
        rebuildHash(self.uf, self.hashCapture)
        rebuildHash(self.uf, self.hashChoice)
        rebuildHash(self.uf, self.hashMaybe)
        rebuildHash(self.uf, self.hashNamePatt)
        rebuildHash(self.uf, self.hashNegative)
        rebuildHash(self.uf, self.hashPositive)
        rebuildHash(self.uf, self.hashProduction)
        rebuildHash(self.uf, self.hashSequence)
        rebuildHash(self.uf, self.hashSome)
        rebuildHash(self.uf, self.hashToken)
        rebuildHash(self.uf, self.hashTuplePatt)
    def makeNamePatt(self, name):
        self.dirty = True
        k = name
        if k in self.hashNamePatt:
            return self.hashNamePatt[k]
        rv = self.uf.make()
        self.NamePatt[rv, name] = None
        self.hashNamePatt[k] = rv
        return rv
    def makeTuplePatt(self, ps):
        self.dirty = True
        k = ps
        if k in self.hashTuplePatt:
            return self.hashTuplePatt[k]
        rv = self.uf.make()
        self.TuplePatt[rv, ps] = None
        self.hashTuplePatt[k] = rv
        return rv
    def makeToken(self, s):
        self.dirty = True
        k = s
        if k in self.hashToken:
            return self.hashToken[k]
        rv = self.uf.make()
        self.Token[rv, s] = None
        self.hashToken[k] = rv
        return rv
    def makeCall(self, s):
        self.dirty = True
        k = s
        if k in self.hashCall:
            return self.hashCall[k]
        rv = self.uf.make()
        self.Call[rv, s] = None
        self.hashCall[k] = rv
        return rv
    def makeSequence(self, exprs):
        self.dirty = True
        k = exprs
        if k in self.hashSequence:
            return self.hashSequence[k]
        rv = self.uf.make()
        self.Sequence[rv, exprs] = None
        self.hashSequence[k] = rv
        return rv
    def makeChoice(self, this, that):
        self.dirty = True
        k = this, that
        if k in self.hashChoice:
            return self.hashChoice[k]
        rv = self.uf.make()
        self.Choice[rv, this, that] = None
        self.hashChoice[k] = rv
        return rv
    def makeAny(self, expr):
        self.dirty = True
        k = expr
        if k in self.hashAny:
            return self.hashAny[k]
        rv = self.uf.make()
        self.Any[rv, expr] = None
        self.hashAny[k] = rv
        return rv
    def makeSome(self, expr):
        self.dirty = True
        k = expr
        if k in self.hashSome:
            return self.hashSome[k]
        rv = self.uf.make()
        self.Some[rv, expr] = None
        self.hashSome[k] = rv
        return rv
    def makeMaybe(self, expr):
        self.dirty = True
        k = expr
        if k in self.hashMaybe:
            return self.hashMaybe[k]
        rv = self.uf.make()
        self.Maybe[rv, expr] = None
        self.hashMaybe[k] = rv
        return rv
    def makePositive(self, expr):
        self.dirty = True
        k = expr
        if k in self.hashPositive:
            return self.hashPositive[k]
        rv = self.uf.make()
        self.Positive[rv, expr] = None
        self.hashPositive[k] = rv
        return rv
    def makeNegative(self, expr):
        self.dirty = True
        k = expr
        if k in self.hashNegative:
            return self.hashNegative[k]
        rv = self.uf.make()
        self.Negative[rv, expr] = None
        self.hashNegative[k] = rv
        return rv
    def makeCapture(self, expr, patt):
        self.dirty = True
        k = expr, patt
        if k in self.hashCapture:
            return self.hashCapture[k]
        rv = self.uf.make()
        self.Capture[rv, expr, patt] = None
        self.hashCapture[k] = rv
        return rv
    def makeProduction(self, expr, prod):
        self.dirty = True
        k = expr, prod
        if k in self.hashProduction:
            return self.hashProduction[k]
        rv = self.uf.make()
        self.Production[rv, expr, prod] = None
        self.hashProduction[k] = rv
        return rv
allRels.append(("peg", pegRels))
class zephyrRels(Rels):
    def __init__(self, uf):
        self.uf = uf
        self.Signature = {}
        self.hashSignature = {}
        self.Product = {}
        self.hashProduct = {}
        self.Sum = {}
        self.hashSum = {}
        self.Con = {}
        self.hashCon = {}
        self.Id = {}
        self.hashId = {}
        self.Option = {}
        self.hashOption = {}
        self.Sequence = {}
        self.hashSequence = {}
    def rebuild(self):
        rebuildRel(self.uf, self.Con)
        rebuildRel(self.uf, self.Id)
        rebuildRel(self.uf, self.Option)
        rebuildRel(self.uf, self.Product)
        rebuildRel(self.uf, self.Sequence)
        rebuildRel(self.uf, self.Signature)
        rebuildRel(self.uf, self.Sum)
        rebuildHash(self.uf, self.hashCon)
        rebuildHash(self.uf, self.hashId)
        rebuildHash(self.uf, self.hashOption)
        rebuildHash(self.uf, self.hashProduct)
        rebuildHash(self.uf, self.hashSequence)
        rebuildHash(self.uf, self.hashSignature)
        rebuildHash(self.uf, self.hashSum)
    def makeSignature(self, name, tys):
        self.dirty = True
        k = name, tys
        if k in self.hashSignature:
            return self.hashSignature[k]
        rv = self.uf.make()
        self.Signature[rv, name, tys] = None
        self.hashSignature[k] = rv
        return rv
    def makeProduct(self, name, fs):
        self.dirty = True
        k = name, fs
        if k in self.hashProduct:
            return self.hashProduct[k]
        rv = self.uf.make()
        self.Product[rv, name, fs] = None
        self.hashProduct[k] = rv
        return rv
    def makeSum(self, name, attrs, con, cons):
        self.dirty = True
        k = name, attrs, con, cons
        if k in self.hashSum:
            return self.hashSum[k]
        rv = self.uf.make()
        self.Sum[rv, name, attrs, con, cons] = None
        self.hashSum[k] = rv
        return rv
    def makeCon(self, tag, args):
        self.dirty = True
        k = tag, args
        if k in self.hashCon:
            return self.hashCon[k]
        rv = self.uf.make()
        self.Con[rv, tag, args] = None
        self.hashCon[k] = rv
        return rv
    def makeId(self, ty, name):
        self.dirty = True
        k = ty, name
        if k in self.hashId:
            return self.hashId[k]
        rv = self.uf.make()
        self.Id[rv, ty, name] = None
        self.hashId[k] = rv
        return rv
    def makeOption(self, ty, name):
        self.dirty = True
        k = ty, name
        if k in self.hashOption:
            return self.hashOption[k]
        rv = self.uf.make()
        self.Option[rv, ty, name] = None
        self.hashOption[k] = rv
        return rv
    def makeSequence(self, ty, name):
        self.dirty = True
        k = ty, name
        if k in self.hashSequence:
            return self.hashSequence[k]
        rv = self.uf.make()
        self.Sequence[rv, ty, name] = None
        self.hashSequence[k] = rv
        return rv
allRels.append(("zephyr", zephyrRels))
class rulesRels(Rels):
    def __init__(self, uf):
        self.uf = uf
        self.StructProd = {}
        self.hashStructProd = {}
        self.ListProd = {}
        self.hashListProd = {}
        self.hashListHeadProd = {}
        self.ListTailProd = {}
        self.hashListTailProd = {}
        self.ListMidProd = {}
        self.hashListMidProd = {}
        self.hashFlattenOp = {}
        self.hashLengthOp = {}
        self.JoinOp = {}
        self.hashJoinOp = {}
        self.ConcatOp = {}
        self.hashConcatOp = {}
        self.Rewrite = {}
        self.hashRewrite = {}
        self.Let = {}
        self.hashLet = {}
        self.FlattenOp = {}
        self.LengthOp = {}
        self.ListHeadProd = {}
        self.IgnorePatt = self.uf.make()
        self.VarPatt = {}
        self.hashVarPatt = {}
        self.StrPatt = {}
        self.hashStrPatt = {}
        self.StructPatt = {}
        self.hashStructPatt = {}
        self.ListPatt = {}
        self.hashListPatt = {}
        self.CharProd = {}
        self.hashCharProd = {}
        self.StrProd = {}
        self.ListHeadPatt = {}
        self.hashListHeadPatt = {}
        self.ListTailPatt = {}
        self.hashListTailPatt = {}
        self.ListMidPatt = {}
        self.ConstProd = {}
        self.hashConstProd = {}
        self.VarProd = {}
        self.hashVarProd = {}
        self.hashListMidPatt = {}
        self.hashStrProd = {}
    def rebuild(self):
        rebuildRel(self.uf, self.CharProd)
        rebuildRel(self.uf, self.ConcatOp)
        rebuildRel(self.uf, self.ConstProd)
        rebuildRel(self.uf, self.FlattenOp)
        rebuildRel(self.uf, self.JoinOp)
        rebuildRel(self.uf, self.LengthOp)
        rebuildRel(self.uf, self.Let)
        rebuildRel(self.uf, self.ListHeadPatt)
        rebuildRel(self.uf, self.ListHeadProd)
        rebuildRel(self.uf, self.ListMidPatt)
        rebuildRel(self.uf, self.ListMidProd)
        rebuildRel(self.uf, self.ListPatt)
        rebuildRel(self.uf, self.ListProd)
        rebuildRel(self.uf, self.ListTailPatt)
        rebuildRel(self.uf, self.ListTailProd)
        rebuildRel(self.uf, self.Rewrite)
        rebuildRel(self.uf, self.StrPatt)
        rebuildRel(self.uf, self.StrProd)
        rebuildRel(self.uf, self.StructPatt)
        rebuildRel(self.uf, self.StructProd)
        rebuildRel(self.uf, self.VarPatt)
        rebuildRel(self.uf, self.VarProd)
        rebuildHash(self.uf, self.hashCharProd)
        rebuildHash(self.uf, self.hashConcatOp)
        rebuildHash(self.uf, self.hashConstProd)
        rebuildHash(self.uf, self.hashFlattenOp)
        rebuildHash(self.uf, self.hashJoinOp)
        rebuildHash(self.uf, self.hashLengthOp)
        rebuildHash(self.uf, self.hashLet)
        rebuildHash(self.uf, self.hashListHeadPatt)
        rebuildHash(self.uf, self.hashListHeadProd)
        rebuildHash(self.uf, self.hashListMidPatt)
        rebuildHash(self.uf, self.hashListMidProd)
        rebuildHash(self.uf, self.hashListPatt)
        rebuildHash(self.uf, self.hashListProd)
        rebuildHash(self.uf, self.hashListTailPatt)
        rebuildHash(self.uf, self.hashListTailProd)
        rebuildHash(self.uf, self.hashRewrite)
        rebuildHash(self.uf, self.hashStrPatt)
        rebuildHash(self.uf, self.hashStrProd)
        rebuildHash(self.uf, self.hashStructPatt)
        rebuildHash(self.uf, self.hashStructProd)
        rebuildHash(self.uf, self.hashVarPatt)
        rebuildHash(self.uf, self.hashVarProd)
    def makeVarPatt(self, n):
        self.dirty = True
        k = n
        if k in self.hashVarPatt:
            return self.hashVarPatt[k]
        rv = self.uf.make()
        self.VarPatt[rv, n] = None
        self.hashVarPatt[k] = rv
        return rv
    def makeStrPatt(self, s):
        self.dirty = True
        k = s
        if k in self.hashStrPatt:
            return self.hashStrPatt[k]
        rv = self.uf.make()
        self.StrPatt[rv, s] = None
        self.hashStrPatt[k] = rv
        return rv
    def makeStructPatt(self, ns, func, vars):
        self.dirty = True
        k = ns, func, vars
        if k in self.hashStructPatt:
            return self.hashStructPatt[k]
        rv = self.uf.make()
        self.StructPatt[rv, ns, func, vars] = None
        self.hashStructPatt[k] = rv
        return rv
    def makeListPatt(self, ps):
        self.dirty = True
        k = ps
        if k in self.hashListPatt:
            return self.hashListPatt[k]
        rv = self.uf.make()
        self.ListPatt[rv, ps] = None
        self.hashListPatt[k] = rv
        return rv
    def makeListHeadPatt(self, head, ps):
        self.dirty = True
        k = head, ps
        if k in self.hashListHeadPatt:
            return self.hashListHeadPatt[k]
        rv = self.uf.make()
        self.ListHeadPatt[rv, head, ps] = None
        self.hashListHeadPatt[k] = rv
        return rv
    def makeListTailPatt(self, tail, ps):
        self.dirty = True
        k = tail, ps
        if k in self.hashListTailPatt:
            return self.hashListTailPatt[k]
        rv = self.uf.make()
        self.ListTailPatt[rv, tail, ps] = None
        self.hashListTailPatt[k] = rv
        return rv
    def makeListMidPatt(self, head, tail, ps):
        self.dirty = True
        k = head, tail, ps
        if k in self.hashListMidPatt:
            return self.hashListMidPatt[k]
        rv = self.uf.make()
        self.ListMidPatt[rv, head, tail, ps] = None
        self.hashListMidPatt[k] = rv
        return rv
    def makeVarProd(self, name):
        self.dirty = True
        k = name
        if k in self.hashVarProd:
            return self.hashVarProd[k]
        rv = self.uf.make()
        self.VarProd[rv, name] = None
        self.hashVarProd[k] = rv
        return rv
    def makeConstProd(self, name):
        self.dirty = True
        k = name
        if k in self.hashConstProd:
            return self.hashConstProd[k]
        rv = self.uf.make()
        self.ConstProd[rv, name] = None
        self.hashConstProd[k] = rv
        return rv
    def makeStrProd(self, s):
        self.dirty = True
        k = s
        if k in self.hashStrProd:
            return self.hashStrProd[k]
        rv = self.uf.make()
        self.StrProd[rv, s] = None
        self.hashStrProd[k] = rv
        return rv
    def makeCharProd(self, n):
        self.dirty = True
        k = n
        if k in self.hashCharProd:
            return self.hashCharProd[k]
        rv = self.uf.make()
        self.CharProd[rv, n] = None
        self.hashCharProd[k] = rv
        return rv
    def makeStructProd(self, ns, func, ps):
        self.dirty = True
        k = ns, func, ps
        if k in self.hashStructProd:
            return self.hashStructProd[k]
        rv = self.uf.make()
        self.StructProd[rv, ns, func, ps] = None
        self.hashStructProd[k] = rv
        return rv
    def makeListProd(self, ps):
        self.dirty = True
        k = ps
        if k in self.hashListProd:
            return self.hashListProd[k]
        rv = self.uf.make()
        self.ListProd[rv, ps] = None
        self.hashListProd[k] = rv
        return rv
    def makeListHeadProd(self, head, ps):
        self.dirty = True
        k = head, ps
        if k in self.hashListHeadProd:
            return self.hashListHeadProd[k]
        rv = self.uf.make()
        self.ListHeadProd[rv, head, ps] = None
        self.hashListHeadProd[k] = rv
        return rv
    def makeListTailProd(self, tail, ps):
        self.dirty = True
        k = tail, ps
        if k in self.hashListTailProd:
            return self.hashListTailProd[k]
        rv = self.uf.make()
        self.ListTailProd[rv, tail, ps] = None
        self.hashListTailProd[k] = rv
        return rv
    def makeListMidProd(self, head, tail, ps):
        self.dirty = True
        k = head, tail, ps
        if k in self.hashListMidProd:
            return self.hashListMidProd[k]
        rv = self.uf.make()
        self.ListMidProd[rv, head, tail, ps] = None
        self.hashListMidProd[k] = rv
        return rv
    def makeFlattenOp(self, p):
        self.dirty = True
        k = p
        if k in self.hashFlattenOp:
            return self.hashFlattenOp[k]
        rv = self.uf.make()
        self.FlattenOp[rv, p] = None
        self.hashFlattenOp[k] = rv
        return rv
    def makeLengthOp(self, p):
        self.dirty = True
        k = p
        if k in self.hashLengthOp:
            return self.hashLengthOp[k]
        rv = self.uf.make()
        self.LengthOp[rv, p] = None
        self.hashLengthOp[k] = rv
        return rv
    def makeJoinOp(self, s, p):
        self.dirty = True
        k = s, p
        if k in self.hashJoinOp:
            return self.hashJoinOp[k]
        rv = self.uf.make()
        self.JoinOp[rv, s, p] = None
        self.hashJoinOp[k] = rv
        return rv
    def makeConcatOp(self, p, ps):
        self.dirty = True
        k = p, ps
        if k in self.hashConcatOp:
            return self.hashConcatOp[k]
        rv = self.uf.make()
        self.ConcatOp[rv, p, ps] = None
        self.hashConcatOp[k] = rv
        return rv
    def makeRewrite(self, name, root, prods):
        self.dirty = True
        k = name, root, prods
        if k in self.hashRewrite:
            return self.hashRewrite[k]
        rv = self.uf.make()
        self.Rewrite[rv, name, root, prods] = None
        self.hashRewrite[k] = rv
        return rv
    def makeLet(self, name, p):
        self.dirty = True
        k = name, p
        if k in self.hashLet:
            return self.hashLet[k]
        rv = self.uf.make()
        self.Let[rv, name, p] = None
        self.hashLet[k] = rv
        return rv
allRels.append(("rules", rulesRels))
class charRels(Rels):
    def __init__(self, uf):
        self.uf = uf
        self.Any = self.uf.make()
        self.Exactly = {}
        self.hashExactly = {}
        self.Either = {}
        self.hashEither = {}
        self.Complement = {}
        self.hashComplement = {}
        self.Range = {}
        self.hashRange = {}
        self.Call = {}
        self.hashCall = {}
    def rebuild(self):
        rebuildRel(self.uf, self.Exactly)
        rebuildRel(self.uf, self.Call)
        rebuildRel(self.uf, self.Complement)
        rebuildRel(self.uf, self.Either)
        rebuildRel(self.uf, self.Exactly)
        rebuildRel(self.uf, self.Range)
        rebuildHash(self.uf, self.hashCall)
        rebuildHash(self.uf, self.hashComplement)
        rebuildHash(self.uf, self.hashEither)
        rebuildHash(self.uf, self.hashExactly)
        rebuildHash(self.uf, self.hashRange)
    def makeExactly(self, c):
        self.dirty = True
        k = c
        if k in self.hashExactly:
            return self.hashExactly[k]
        rv = self.uf.make()
        self.Exactly[rv, c] = None
        self.hashExactly[k] = rv
        return rv
    def makeRange(self, l, u):
        self.dirty = True
        k = l, u
        if k in self.hashRange:
            return self.hashRange[k]
        rv = self.uf.make()
        self.Range[rv, l, u] = None
        self.hashRange[k] = rv
        return rv
    def makeCall(self, n):
        self.dirty = True
        k = n
        if k in self.hashCall:
            return self.hashCall[k]
        rv = self.uf.make()
        self.Call[rv, n] = None
        self.hashCall[k] = rv
        return rv
    def makeComplement(self, s):
        self.dirty = True
        k = s
        if k in self.hashComplement:
            return self.hashComplement[k]
        rv = self.uf.make()
        self.Complement[rv, s] = None
        self.hashComplement[k] = rv
        return rv
    def makeEither(self, l, r):
        self.dirty = True
        k = l, r
        if k in self.hashEither:
            return self.hashEither[k]
        rv = self.uf.make()
        self.Either[rv, l, r] = None
        self.hashEither[k] = rv
        return rv
allRels.append(("char", charRels))
@rewrite("py")
def pyStatement(uf, rel):
    count = 0
    q = []
    for (vRoot, vL) in rel.py.Statement:
        try:
            target = rel.uf.makeList([rel.builtin.makeLine(vL)])
            uf.union(vRoot, target)
            q.append((vRoot, vL))
            count += 1
        except NoResults: continue
    for k in q: del rel.py.Statement[k]
    return count
@rewrite("py")
def pyRet(uf, rel):
    count = 0
    q = []
    for (vRoot, vE) in rel.py.Ret:
        try:
            target = (uf.makeList([rel.builtin.makeLine(uf.makeStr(u'return ' + uf.findStr(vE)))]))
            uf.union(vRoot, target)
            q.append((vRoot, vE))
            count += 1
        except NoResults: continue
    for k in q: del rel.py.Ret[k]
    return count
@rewrite("py")
def pyRaiseIf(uf, rel):
    count = 0
    q = []
    for (vRoot, vT) in rel.py.RaiseIf:
        try:
            target = (uf.makeList([rel.builtin.makeLine(uf.makeStr(u'if ' + uf.findStr(vT) + u': raise ParseError()'))]))
            uf.union(vRoot, target)
            q.append((vRoot, vT))
            count += 1
        except NoResults: continue
    for k in q: del rel.py.RaiseIf[k]
    return count
@rewrite("py")
def pyCompPass(uf, rel):
    count = 0
    q = []
    for (vRoot, vH, beEmpty) in rel.py.Compound:
        try:
            if len(uf.findList(beEmpty)): continue
            target = (uf.makeList([rel.builtin.makeLine(uf.makeStr(uf.findStr(vH) + u': pass'))]))
            uf.union(vRoot, target)
            q.append((vRoot, vH, beEmpty))
            count += 1
        except NoResults: continue
    for k in q: del rel.py.Compound[k]
    return count
@rewrite("py")
def pyCompBlock(uf, rel):
    count = 0
    q = []
    for (vRoot, vH, vB) in rel.py.Compound:
        try:
            if not len(uf.findList(vB)): continue
            target = uf.makeList([rel.builtin.makeLine(uf.makeStr(uf.findStr(vH) +
                                                          u':')),
                          rel.builtin.makeBlock(rel.builtin.makeFlatten(vB))])
            uf.union(vRoot, target)
            q.append((vRoot, vH, vB))
            count += 1
        except NoResults: continue
    for k in q: del rel.py.Compound[k]
    return count
@rewrite("py")
def pyCondEmpty(uf, rel):
    count = 0
    q = []
    for (vRoot, vT, beEmpty) in rel.py.Conditional:
        try:
            if len(uf.findList(beEmpty)): continue
            target = uf.makeList([])
            uf.union(vRoot, target)
            count += 1
            q.append((vRoot, vT, beEmpty))
        except NoResults: continue
    for k in q: del rel.py.Conditional[k]
    return count
@rewrite("py")
def pyCondBlock(uf, rel):
    count = 0
    q = []
    for (vRoot, vT, vB) in rel.py.Conditional:
        try:
            if not len(uf.findList(vB)): continue
            target = (uf.makeList([rel.builtin.makeLine(uf.makeStr(u'if ' +
                                                                   uf.findStr(vT)
                                                                   + u':')),
                                   rel.builtin.makeBlock(rel.builtin.makeFlatten(vB))]))
            uf.union(vRoot, target)
            q.append((vRoot, vT, vB))
            count += 1
        except NoResults: continue
    for k in q: del rel.py.Conditional[k]
    return count
@rewrite("py")
def pyHandEmpty(uf, rel):
    count = 0
    for (vRoot, vB, beEmpty) in rel.py.Handler:
        try:
            if len(uf.findList(beEmpty)): continue
            target = uf.makeList([])
            uf.union(vRoot, target)
            count += 1
        except NoResults: continue
    return count
@rewrite("py")
def pyHandBlock(uf, rel):
    count = 0
    q = []
    for (vRoot, vB, vH) in rel.py.Handler:
        try:
            if not uf.findList(vH): continue
            target = (uf.makeList([rel.builtin.makeLine(uf.makeStr(u'try:')),
                                   rel.builtin.makeBlock(rel.builtin.makeFlatten(vB)),
                                   rel.builtin.makeLine(uf.makeStr(u'except ParseError:')),
                                                                   rel.builtin.makeBlock(rel.builtin.makeFlatten(vH))]))
            uf.union(vRoot, target)
            q.append((vRoot, vB, vH))
            count += 1
        except NoResults: continue
    for k in q: del rel.py.Handler[k]
    return count
@rewrite("peg")
def pegNamePatt(uf, rel):
    count = 0
    q = []
    for (vRoot, vName) in rel.peg.NamePatt:
        try:
            target = (uf.makeStr(u'v' + uf.findStr(vName)))
            uf.union(vRoot, target)
            q.append((vRoot, vName))
            count += 1
        except NoResults:
            continue
    for k in q: del rel.peg.NamePatt[k]
    return count
@rewrite("peg")
def pegTuplePatt(uf, rel):
    count = 0
    for (vRoot, vPs) in rel.peg.TuplePatt:
        try:
            target = (uf.makeStr(u'(' + u",".join([uf.findStr(x) for x in uf.findList(vPs)]) + u')'))
            uf.union(vRoot, target)
            count += 1
        except NoResults:
            continue
    return count
@rewrite("peg")
def pegSeq(uf, rel):
    count = 0
    q = []
    for (vRoot, vEs) in rel.peg.Sequence:
        try:
            target = (rel.builtin.makeFlatten(vEs))
            uf.union(vRoot, target)
            q.append((vRoot, vEs))
            count += 1
        except NoResults:
            continue
    for k in q: del rel.peg.Sequence[k]
    return count
@rewrite("peg")
def pegCap(uf, rel):
    count = 0
    q = []
    for (vRoot, vE, vP) in rel.peg.Capture:
        try:
            target = (uf.makeList(uf.findList(vE) + [rel.py.makeStatement(uf.makeStr(uf.findStr(vP) + u' = rv'))]))
            uf.union(vRoot, target)
            q.append((vRoot, vE, vP))
            count += 1
        except NoResults:
            continue
    for k in q: del rel.peg.Capture[k]
    return count
@rewrite("peg")
def pegProd(uf, rel):
    count = 0
    q = []
    for (vRoot, vE, vP) in rel.peg.Production:
        try:
            target = (uf.makeList(uf.findList(vE) + [rel.py.makeStatement(uf.makeStr(u'rv = ' + uf.findStr(vP)))]))
            uf.union(vRoot, target)
            count += 1
            q.append((vRoot, vE, vP))
        except NoResults:
            continue
    for k in q: del rel.peg.Production[k]
    return count
@rewrite("peg")
def pegCall(uf, rel):
    count = 0
    q = []
    for (vRoot, vS) in rel.peg.Call:
        try:
            target = (uf.makeList([rel.py.makeStatement(uf.makeStr(u'i, rv = self.parse' + uf.findStr(vS) + u'(i)'))]))
            uf.union(vRoot, target)
            q.append((vRoot, vS))
            count += 1
        except NoResults:
            continue
    for k in q: del rel.peg.Call[k]
    return count
@rewrite("peg")
def pegChoice(uf, rel):
    count = 0
    q = []
    for (vRoot, vL, vR) in rel.peg.Choice:
        try:
            target = (uf.makeList([rel.constsave, rel.py.makeHandler(vL,
                                                                uf.makeList([rel.constbackup]
                                                                         +
                                                                         uf.findList(vR)))]))
            uf.union(vRoot, target)
            q.append((vRoot, vL, vR))
            count += 1
        except NoResults:
            continue
    for k in q: del rel.peg.Choice[k]
    return count
@rewrite("peg")
def pegToken(uf, rel):
    count = 0
    q = []
    for (vRoot, vS) in rel.peg.Token:
        try:
            target = uf.makeList([
                rel.constskipws,
                rel.constboundcheck,
                rel.py.makeStatement(uf.makeStr(u'assert i >= 0')),
                rel.py.makeRaiseIf(uf.makeStr(u'self.s[i:i + ' + uf.findStr(uf.makeStr(str(len(uf.findStr(vS))).decode("utf-8"))) + u'] != u"' + uf.findStr(vS) + u'"')), rel.py.makeStatement(uf.makeStr(u'self.lastMatch.append((u"TOKEN ' + uf.findStr(vS) + u'", i, i + ' + uf.findStr(uf.makeStr(str(len(uf.findStr(vS))).decode("utf-8"))) + u'))')), rel.py.makeStatement(uf.makeStr(u'rv = uf.makeStr(u"' + uf.findStr(vS) + u'");i += ' + uf.findStr(uf.makeStr(str(len(uf.findStr(vS))).decode("utf-8")))))])
            uf.union(vRoot, target)
            count += 1
            q.append((vRoot, vS))
        except NoResults:
            continue
    for k in q: del rel.peg.Token[k]
    return count
@rewrite("peg")
def pegAny(uf, rel):
    count = 0
    q = []
    for (vRoot, vE) in rel.peg.Any:
        try:
            target = (uf.makeList([rel.py.makeStatement(uf.makeStr(u'rvs = []')),
                                rel.py.makeCompound(uf.makeStr(u'while True'),
                                                      uf.makeList([rel.constsave,
                                                                rel.py.makeHandler(uf.makeList(uf.findList(vE)
                                                                                               +
                                                                                               [rel.py.makeStatement(uf.makeStr(u'rvs.append(rv)'))]),
                                                                                   uf.makeList([rel.constbackup, rel.py.makeStatement(uf.makeStr(u'break'))]))])), rel.py.makeStatement(uf.makeStr(u'rv = uf.makeList(rvs)'))]))
            uf.union(vRoot, target)
            count += 1
            q.append((vRoot, vE))
        except NoResults:
            continue
    for k in q: del rel.peg.Any[k]
    return count
@rewrite("peg")
def pegSome(uf, rel):
    count = 0
    q = []
    for (vRoot, vE) in rel.peg.Some:
        try:
            target = (rel.builtin.makeFlatten(uf.makeList([rel.peg.makeAny(vE),
                                                  uf.makeList([rel.py.makeRaiseIf(uf.makeStr(u'not len(rvs)'))])])))
            uf.union(vRoot, target)
            count += 1
            q.append((vRoot, vE))
        except NoResults:
            continue
    for k in q: del rel.peg.Some[k]
    return count
@rewrite("peg")
def pegMaybe(uf, rel):
    count = 0
    for (vRoot, vE) in rel.peg.Maybe:
        try:
            target = (uf.makeList([rel.constsave, rel.py.makeHandler(vE,
                                                                     uf.makeList([rel.py.makeStatement(
                                                                     uf.makeStr(u'rv = 0')),
                                                                                                                     rel.constbackup]))]))
            uf.union(vRoot, target)
            count += 1
        except NoResults:
            continue
    return count
@rewrite("peg")
def pegPos(uf, rel):
    count = 0
    for (vRoot, vE) in rel.peg.Positive:
        try:
            target = (uf.makeList([rel.constsave,
                                rel.py.makeHandler(uf.makeList(uf.findList(vE) + [rel.py.makeStatement(uf.makeStr(u'rv = True'))]), uf.makeList([rel.py.makeStatement(uf.makeStr(u'rv = False'))])), rel.constbackup, rel.py.makeRaiseIf(uf.makeStr(u'not rv'))]))
            uf.union(vRoot, target)
            count += 1
        except NoResults:
            continue
    return count
@rewrite("peg")
def pegNeg(uf, rel):
    count = 0
    for (vRoot, vE) in rel.peg.Negative:
        try:
            target = (uf.makeList([rel.constsave,
                                rel.py.makeHandler(uf.makeList(uf.findList(vE) + [rel.py.makeStatement(uf.makeStr(u'rv = True'))]), uf.makeList([rel.py.makeStatement(uf.makeStr(u'rv = False'))])), rel.constbackup, rel.py.makeRaiseIf(uf.makeStr(u'rv'))]))
            uf.union(vRoot, target)
            count += 1
        except NoResults:
            continue
    return count
@rewrite("zephyr")
def zSig(uf, rel):
    count = 0
    for (vRoot, vN, vT) in rel.zephyr.Signature:
        try:
            N = uf.findStr(vN)
            target = uf.makeList([
                rel.py.makeStatement(uf.makeStr(N + u'Cons = []')),
                rel.py.makeCompound(uf.makeStr(u'class ' + N +
                                               u'Rels(Rels)'),
                                    rel.builtin.makeFlatten(uf.makeList([uf.makeList([
                                        rel.py.makeStatement(uf.makeStr(u'cons=' +
                                                                        N + u'Cons')),
                                        rel.py.makeCompound(uf.makeStr(u'def __init__(self, uf)'), uf.makeList([
                                            rel.py.makeStatement(uf.makeStr(u'self.uf=uf')),
rel.py.makeCompound(uf.makeStr(u'for n in unrolled'
                                                                           + N
                                                                           +
                                                                           u'Cons'),
                                                                uf.makeList([
rel.py.makeStatement(uf.makeStr(u'setattr(self, n, {})')),
rel.py.makeStatement(uf.makeStr(u'setattr(self, "hash" + n, {})'))
                                                ]))])
                                    ),
rel.py.makeCompound(uf.makeStr(u'def rebuild(self)'), uf.makeList([
rel.py.makeCompound(uf.makeStr(u'for n in unrolled'
                                                                           + N
                                                                           +
                                                                           u'Cons'),
                                                                uf.makeList([
rel.py.makeStatement(uf.makeStr(u'rebuildRel(self.uf, getattr(self, n))')),
rel.py.makeStatement(uf.makeStr(u'rebuildHash(self.uf, getattr(self, "hash" + n))'))
                                                ]))])
                                    )]), rel.builtin.makeFlatten(vT)]))),
                rel.py.makeStatement(uf.makeStr(u'unrolled' + N + u'Cons = unrolling_iterable(' + N +
                                                                   u'Cons[:])')),
                rel.py.makeStatement(uf.makeStr(u'allRels.append(("' + N + u'", '
                                                + N + u'Rels))'))
                ])
            uf.union(vRoot, target)
            count += 1
        except NoResults: continue
    return count
@rewrite("zephyr")
def zProd(uf, rel):
    count = 0
    for (vRoot, vN, vFs) in rel.zephyr.Product:
        try:
            target = (uf.makeList([rel.py.makeStatement(uf.makeStr(u'# product ' + uf.findStr(vN)))]))
            uf.union(vRoot, target)
            count += 1
        except NoResults: continue
    return count
@rewrite("zephyr")
def zSum(uf, rel):
    count = 0
    for (vRoot, vN, vA, vC, vCs) in rel.zephyr.Sum:
        try:
            target = (rel.builtin.makeFlatten(uf.makeList([vC, rel.builtin.makeFlatten(vCs)])))
            uf.union(vRoot, target)
            count += 1
        except NoResults: continue
    return count
# @rewrite("zephyr")
def zConT(uf, rel):
    count = 0
    q = []
    for (vRoot, vT, beEmpty) in rel.zephyr.Con:
        try:
            if len(uf.findList(beEmpty)): continue
            target = (uf.makeList([rel.py.makeStatement(uf.makeStr(uf.findStr(vT) + u' = make()'))]))
            uf.union(vRoot, target)
            q.append((vRoot, vT, beEmpty))
            count += 1
        except NoResults: continue
    for k in q: del rel.zephyr.Con[k]
    return count
@rewrite("zephyr")
def zConF(uf, rel):
    count = 0
    q = []
    for (vRoot, vT, vA) in rel.zephyr.Con:
        try:
            # if not len(uf.findList(vA)): continue
            T = uf.findStr(vT)
            A = uf.findStr(uf.makeStr(u",".join([uf.findStr(x) for x in uf.findList(vA)])))
            target = uf.makeList([
                rel.py.makeStatement(uf.makeStr(u'cons.append("' + T + u'")')),
                rel.py.makeCompound(uf.makeStr(u'def make' + T + u'(self, ' +
                                               A + u')'), uf.makeList([
                    rel.py.makeStatement(uf.makeStr(u'self.dirty' + T + u' = True')),
                    rel.py.makeStatement(uf.makeStr(u'k = (' + A + u')')),
                    rel.py.makeStatement(uf.makeStr(u'if k in self.hash' + T +
                                                    u': return self.hash' + T
                                                    + u'[k]')),
                    rel.py.makeStatement(uf.makeStr(u'rv = self.uf.make()')),
                    rel.py.makeStatement(uf.makeStr(u'self.' + T + u'[rv, ' +
                                                    A + u'] = None')),
                    rel.py.makeStatement(uf.makeStr(u'self.hash' + T + u'[k] = rv')),
                    rel.py.makeRet(uf.makeStr(u'rv'))]))])
            uf.union(vRoot, target)
            q.append((vRoot, vT, vA))
            count += 1
        except NoResults: continue
    for k in q: del rel.zephyr.Con[k]
    return count
@rewrite("zephyr")
def zOpt(uf, rel):
    count = 0
    for (vRoot, vT, vN) in rel.zephyr.Option:
        try:
            target = (vN)
            uf.union(vRoot, target)
            count += 1
        except NoResults: continue
    return count
@rewrite("zephyr")
def zSeq(uf, rel):
    count = 0
    for (vRoot, vT, vN) in rel.zephyr.Sequence:
        try:
            target = (vN)
            uf.union(vRoot, target)
            count += 1
        except NoResults: continue
    return count
@rewrite("zephyr")
def zId(uf, rel):
    count = 0
    for (vRoot, vT, vN) in rel.zephyr.Id:
        try:
            target = (vN)
            uf.union(vRoot, target)
            count += 1
        except NoResults: continue
    return count
@rewrite("char")
def charExactly(uf, rel):
    count = 0
    for (vRoot, vC) in rel.char.Exactly:
        try:
            target = (uf.makeStr(u'c == ' + uf.findStr(vC)))
            uf.union(vRoot, target)
            count += 1
        except NoResults: continue
    return count
@rewrite("char")
def charRange(uf, rel):
    count = 0
    for (vRoot, vL, vU) in rel.char.Range:
        try:
            target = (uf.makeStr(uf.findStr(vL) + u' <= c <= ' + uf.findStr(vU)))
            uf.union(vRoot, target)
            count += 1
        except NoResults: continue
    return count
@rewrite("char")
def charCall(uf, rel):
    count = 0
    for (vRoot, vN) in rel.char.Call:
        try:
            target = (uf.makeStr(u'self.cls' + uf.findStr(vN) + u'(c)'))
            uf.union(vRoot, target)
            count += 1
        except NoResults: continue
    return count
@rewrite("char")
def charComp(uf, rel):
    count = 0
    for (vRoot, vS) in rel.char.Complement:
        try:
            target = (uf.makeStr(u'not (' + uf.findStr(vS) + u')'))
            uf.union(vRoot, target)
            count += 1
        except NoResults: continue
    return count
@rewrite("char")
def charEither(uf, rel):
    count = 0
    for (vRoot, vL, vR) in rel.char.Either:
        try:
            target = (uf.makeStr(u'(' + uf.findStr(vL) + u') or (' + uf.findStr(vR) + u')'))
            uf.union(vRoot, target)
            count += 1
        except NoResults: continue
    return count
@rewrite("rules")
def rPattV(uf, rel):
    count = 0
    for (vRoot, vN) in rel.rules.VarPatt:
        try:
            target = (uf.makeStr(u'v' + uf.findStr(vN)))
            uf.union(vRoot, target)
            count += 1
        except NoResults: continue
    return count
@rewrite("rules")
def rPattS(uf, rel):
    count = 0
    for (vRoot, vS) in rel.rules.StrPatt:
        try:
            target = (uf.makeStr(u'u' + unichr(39) + uf.findStr(vS) + unichr(39)))
            uf.union(vRoot, target)
            count += 1
        except NoResults: continue
    return count
@rewrite("rules")
def rPattSt(uf, rel):
    count = 0
    q = []
    for (vRoot, vNs, vF, vVs) in rel.rules.StructPatt:
        try:
            target = (uf.makeStr(u'for (vRoot, ' +
                                 uf.findStr(uf.makeStr(u",".join([uf.findStr(x)
                                                                  for x in
                                                                  uf.findList(vVs)])))
                                 + u') in rel.' + uf.findStr(vNs) + u'.' + uf.findStr(vF)))
            uf.union(vRoot, target)
            count += 1
            q.append((vRoot, vNs, vF, vVs))
        except NoResults: continue
    for k in q: del rel.rules.StructPatt[k]
    return count
@rewrite("rules")
def rPattLE(uf, rel):
    count = 0
    beEmpty = uf.makeList([])
    for (vRoot, beEmpty) in rel.rules.ListPatt:
        if len(uf.findList(beEmpty)): continue
        try:
            uf.union(vRoot, uf.makeStr(u'beEmpty'))
            count += 1
        except NoResults: continue
    return count
@rewrite("rules")
def rPattLL(uf, rel):
    count = 0
    for (vRoot, vPs) in rel.rules.ListPatt:
        if not len(uf.findList(vPs)): continue
        try:
            target = (uf.makeStr(u",".join([uf.findStr(x) for x in uf.findList(vPs)])))
            uf.union(vRoot, target)
            count += 1
        except NoResults: continue
    return count
@rewrite("rules")
def rPattLH(uf, rel):
    count = 0
    for (vRoot, vH, vPs) in rel.rules.ListHeadPatt:
        try:
            target = (uf.makeStr(u'listhead' + uf.findStr(vH) + uf.findStr(uf.makeStr(u",".join([uf.findStr(x) for x in uf.findList(vPs)])))))
            uf.union(vRoot, target)
            count += 1
        except NoResults: continue
    return count
@rewrite("rules")
def rPattLT(uf, rel):
    count = 0
    for (vRoot, vT, vPs) in rel.rules.ListTailPatt:
        try:
            target = (uf.makeStr(u'listtail' + uf.findStr(vT) + uf.findStr(uf.makeStr(u",".join([uf.findStr(x) for x in uf.findList(vPs)])))))
            uf.union(vRoot, target)
            count += 1
        except NoResults: continue
    return count
@rewrite("rules")
def rPattLM(uf, rel):
    count = 0
    for (vRoot, vH, vT, vPs) in rel.rules.ListMidPatt:
        try:
            target = (uf.makeStr(u'listmid' + uf.findStr(vH) + uf.findStr(vT) + uf.findStr(uf.makeStr(u",".join([uf.findStr(x) for x in uf.findList(vPs)])))))
            uf.union(vRoot, target)
            count += 1
        except NoResults: continue
    return count
@rewrite("rules")
def rProdV(uf, rel):
    count = 0
    for (vRoot, vName) in rel.rules.VarProd:
        try:
            target = (uf.makeStr(u'v' + uf.findStr(vName)))
            uf.union(vRoot, target)
            count += 1
        except NoResults: continue
    return count
@rewrite("rules")
def rProdC(uf, rel):
    count = 0
    for (vRoot, vName) in rel.rules.ConstProd:
        try:
            target = (uf.makeStr(u'rel.const' + uf.findStr(vName)))
            uf.union(vRoot, target)
            count += 1
        except NoResults: continue
    return count
@rewrite("rules")
def rProdS(uf, rel):
    count = 0
    q = []
    for (vRoot, vS) in rel.rules.StrProd:
        try:
            target = (uf.makeStr(u'uf.makeStr(u' + unichr(39) + uf.findStr(vS) + unichr(39) + u')'))
            uf.union(vRoot, target)
            count += 1
            q.append((vRoot, vS))
        except NoResults: continue
    for k in q: del rel.rules.StrProd[k]
    return count
@rewrite("rules")
def rProdCh(uf, rel):
    count = 0
    for (vRoot, vN) in rel.rules.CharProd:
        try:
            target = (uf.makeStr(u'uf.makeStr(unichr(' + uf.findStr(vN) + u'))'))
            uf.union(vRoot, target)
            count += 1
        except NoResults: continue
    return count
@rewrite("rules")
def rProdSt(uf, rel):
    count = 0
    q = []
    for (vRoot, vNs, vF, vPs) in rel.rules.StructProd:
        try:
            target = (uf.makeStr(u'rel.' + uf.findStr(vNs) + u'.make' + uf.findStr(vF) + u'(' + uf.findStr(uf.makeStr(u",".join([uf.findStr(x) for x in uf.findList(vPs)]))) + u')'))
            uf.union(vRoot, target)
            count += 1
            q.append((vRoot, vNs, vF, vPs))
        except NoResults: continue
    for k in q: del rel.rules.StructProd[k]
    return count
@rewrite("rules")
def rProdLC(uf, rel):
    count = 0
    q = []
    for (vRoot, vPs) in rel.rules.ListProd:
        try:
            target = (uf.makeStr(u'uf.makeList([' + uf.findStr(uf.makeStr(u",".join([uf.findStr(x) for x in uf.findList(vPs)]))) + u'])'))
            uf.union(vRoot, target)
            q.append((vRoot, vPs))
            count += 1
        except NoResults: continue
    for k in q: del rel.rules.ListProd[k]
    return count
@rewrite("rules")
def rProdLH(uf, rel):
    count = 0
    for (vRoot, vH, vPs) in rel.rules.ListHeadProd:
        try:
            target = (uf.makeStr(u'uf.makeList(uf.findList(' + uf.findStr(vH) + u') + [' + uf.findStr(uf.makeStr(u",".join([uf.findStr(x) for x in uf.findList(vPs)]))) + u'])'))
            uf.union(vRoot, target)
            count += 1
        except NoResults: continue
    return count
@rewrite("rules")
def rProdLT(uf, rel):
    count = 0
    for (vRoot, vT, vPs) in rel.rules.ListTailProd:
        try:
            target = (uf.makeStr(u'uf.makeList([' + uf.findStr(uf.makeStr(u",".join([uf.findStr(x) for x in uf.findList(vPs)]))) + u'] + uf.findList(' + uf.findStr(vT) + u'))'))
            uf.union(vRoot, target)
            count += 1
        except NoResults: continue
    return count
@rewrite("rules")
def rProdLM(uf, rel):
    count = 0
    for (vRoot, vH, vT, vPs) in rel.rules.ListMidProd:
        try:
            target = (uf.makeStr(u'listmid' + uf.findStr(vH) + uf.findStr(vT) + uf.findStr(uf.makeStr(u",".join([uf.findStr(x) for x in uf.findList(vPs)])))))
            uf.union(vRoot, target)
            count += 1
        except NoResults: continue
    return count
@rewrite("rules")
def rProdOF(uf, rel):
    count = 0
    for (vRoot, vP) in rel.rules.FlattenOp:
        try:
            target = (uf.makeStr(u'rel.builtin.makeFlatten(' + uf.findStr(vP) + u')'))
            uf.union(vRoot, target)
            count += 1
        except NoResults: continue
    return count
@rewrite("rules")
def rProdOL(uf, rel):
    count = 0
    for (vRoot, vP) in rel.rules.LengthOp:
        try:
            target = (uf.makeStr(u'rel.builtin.makeLength(' + uf.findStr(vP) + u')'))
            uf.union(vRoot, target)
            count += 1
        except NoResults: continue
    return count
@rewrite("rules")
def rProdOJ(uf, rel):
    count = 0
    for (vRoot, vS, vP) in rel.rules.JoinOp:
        try:
            target = uf.makeStr(u'rel.builtin.makeJoin(uf.makeStr(u"' + uf.findStr(vS) +
            u'"),' + uf.findStr(vP) + u')')
            uf.union(vRoot, target)
            count += 1
        except NoResults: continue
    return count
@rewrite("rules")
def rProdOC(uf, rel):
    count = 0
    q = []
    for (vRoot, vP, vPs) in rel.rules.ConcatOp:
        try:
            ps = [uf.findStr(i) for i in uf.findList(vPs)]
            if len(ps):
                target = uf.makeStr(u'rel.builtin.makeConcat(' + uf.findStr(vP) +
                                    u',uf.makeList([' + u",".join(ps)
                                    + u']))')
            else: target = vP
            uf.union(vRoot, target)
            count += 1
            q.append((vRoot, vP, vPs))
        except NoResults: continue
    for k in q: del rel.rules.ConcatOp[k]
    return count
@rewrite("rules")
def rRule(uf, rel):
    count = 0
    q = []
    for (vRoot, vName, vRootFor, vPs) in rel.rules.Rewrite:
        try:
            ps = [uf.findStr(x) for x in uf.findList(vPs)]
            target = uf.makeList([
                rel.py.makeStatement(uf.makeStr(u'@rewrite("builtin", "py", "rules", "peg", "char", "zephyr")')),
                rel.py.makeCompound(uf.makeStr(u'def ' + uf.findStr(vName) +
                                               u'(uf, rel)'),
                                    uf.makeList([
                                        rel.py.makeStatement(uf.makeStr(u'q = []')),
                                        rel.py.makeStatement(uf.makeStr(u'beEmpty = uf.makeList([])')),
                                        rel.py.makeCompound(vRootFor,
                                                            uf.makeList([
                                            rel.py.makeCompound(uf.makeStr(u'try'),
                                                                uf.makeList([
                                                rel.py.makeStatement(uf.makeStr(u'if len(uf.findList(beEmpty)): continue')),
                                                rel.py.makeStatement(uf.makeStr(u'uf.union(vRoot,'
                                                                                +
                                                                                u",".join(ps)
                                                                                +
                                                                     u')')),
                                                rel.py.makeStatement(uf.makeStr(u'q.append(vRoot)'))])),
                                                rel.py.makeStatement(uf.makeStr(u'except NoResults: continue'))])),
                                                rel.py.makeRet(uf.makeStr(u'len(q)'))]))])
            uf.union(vRoot, target)
            count += 1
            q.append((vRoot, vName, vRootFor, vPs))
        except NoResults: continue
    for k in q: del rel.rules.Rewrite[k]
    return count
@rewrite("rules")
def rLet(uf, rel):
    count = 0
    for (vRoot, vName, vP) in rel.rules.Let:
        try:
            Name = uf.findStr(vName)
            target = uf.makeList([
                rel.py.makeStatement(uf.makeStr(u'@let')),
                rel.py.makeCompound(uf.makeStr(u'def let' + Name +
                u'(uf, rel)'), uf.makeList([
                    rel.py.makeStatement(uf.makeStr(u'rel.const' + Name + u' = ' + uf.findStr(vP)))
                ]))
            ])
            uf.union(vRoot, target)
            count += 1
        except NoResults: continue
    return count
def target(driver, *args):
    driver.exe_name = "ZADDY".lower() + "c"
    return main, None
frozenRels = dict(allRels)
unrolledRels = unrolling_iterable(frozenRels)
frozenRules = dict(ruleNames)
unrolledRules = unrolling_iterable(frozenRules)
frozenTriggers = dict(triggers)
@finishsigs
class ZADDYParser(object):
    def __init__(self, s, uf):
        self.s = s; self.uf = uf
        self.lastMatch = []
        for name in unrolledRels:
            setattr(self, name, frozenRels[name](uf))
        self.constsave = self.py.makeStatement(uf.makeStr(u'st.append(i)'))
        self.constbackup = self.py.makeStatement(uf.makeStr(u'i = st.pop()'))
        self.constboundcheck = self.py.makeRaiseIf(uf.makeStr(u'i >= len(self.s)'))
        self.constskipws = self.py.makeStatement(uf.makeStr(u'while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1'))
        uf.union(self.rules.IgnorePatt, uf.makeStr(u'_'))
        uf.union(self.char.Any, uf.makeStr(u'True'))
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
    @signature(types.self(), types.int(),
               returns=SomeTuple((types.int(), types.int())))
    def parseWS(self, i):
        if i >= len(self.s): raise ParseError()
        start = i
        assert start >= 0
        while i < len(self.s) and self.clsWhitespace(ord(self.s[i])): i += 1
        rv = self.uf.makeStr(self.s[start:i])
        self.lastMatch.append((u"TOKEN WS", start, i))
        return i, rv
    def parseNumber(self, i):
        if i >= len(self.s): raise ParseError()
        start = i
        assert start >= 0
        if i >= len(self.s) or not self.clsDigit(ord(self.s[i])): raise ParseError()
        while i < len(self.s) and self.clsDigit(ord(self.s[i])): i += 1
        rv = self.uf.makeStr(self.s[start:i])
        self.lastMatch.append((u"TOKEN Number", start, i))
        return i, rv
    def parseId(self, i):
        if i >= len(self.s): raise ParseError()
        start = i
        assert start >= 0
        if i >= len(self.s) or not self.clsAlpha(ord(self.s[i])): raise ParseError()
        i += 1
        while i < len(self.s) and self.clsAlphanumeric(ord(self.s[i])): i += 1
        rv = self.uf.makeStr(self.s[start:i])
        self.lastMatch.append((u"TOKEN Id", start, i))
        return i, rv
    def parsePVar(self, i):
        if i >= len(self.s): raise ParseError()
        start = i
        assert start >= 0
        if i >= len(self.s) or not self.clsUpper(ord(self.s[i])): raise ParseError()
        i += 1
        while i < len(self.s) and self.clsAlphanumeric(ord(self.s[i])): i += 1
        rv = self.uf.makeStr(self.s[start:i])
        self.lastMatch.append((u"TOKEN PVar", start, i))
        return i, rv
    def parsePConst(self, i):
        if i >= len(self.s): raise ParseError()
        start = i
        assert start >= 0
        if i >= len(self.s) or not self.clsLower(ord(self.s[i])): raise ParseError()
        while i < len(self.s) and self.clsLower(ord(self.s[i])): i += 1
        rv = self.uf.makeStr(self.s[start:i])
        self.lastMatch.append((u"TOKEN PConst", start, i))
        return i, rv
    def parseZTId(self, i):
        if i >= len(self.s): raise ParseError()
        start = i
        assert start >= 0
        if i >= len(self.s) or not self.clsLower(ord(self.s[i])): raise ParseError()
        i += 1
        while i < len(self.s) and self.clsAlphanumeric(ord(self.s[i])): i += 1
        rv = self.uf.makeStr(self.s[start:i])
        self.lastMatch.append((u"TOKEN ZTId", start, i))
        return i, rv
    def parseZCId(self, i):
        if i >= len(self.s): raise ParseError()
        start = i
        assert start >= 0
        if i >= len(self.s) or not self.clsUpper(ord(self.s[i])): raise ParseError()
        i += 1
        while i < len(self.s) and self.clsAlphanumeric(ord(self.s[i])): i += 1
        rv = self.uf.makeStr(self.s[start:i])
        self.lastMatch.append((u"TOKEN ZCId", start, i))
        return i, rv
    def parseQuote(self, i):
        if i >= len(self.s): raise ParseError()
        start = i
        assert start >= 0
        if i >= len(self.s) or not self.clsQuote(ord(self.s[i])): raise ParseError()
        i += 1
        rv = self.uf.makeStr(self.s[start:i])
        self.lastMatch.append((u"TOKEN Quote", start, i))
        return i, rv
    def parseQuoted(self, i):
        if i >= len(self.s): raise ParseError()
        start = i
        assert start >= 0
        while i < len(self.s) and self.clsQuoted(ord(self.s[i])): i += 1
        rv = self.uf.makeStr(self.s[start:i])
        self.lastMatch.append((u"TOKEN Quoted", start, i))
        return i, rv
    def parseEllipsis(self, i):
        if i >= len(self.s): raise ParseError()
        start = i
        assert start >= 0
        if i >= len(self.s) or not self.clsEllipsis(ord(self.s[i])): raise ParseError()
        i += 1
        rv = self.uf.makeStr(self.s[start:i])
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
        assert i >= 0
        if self.s[i:i + 10] != u".signature": raise ParseError()
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
            except ParseError:
                i = st.pop()
                break
        rv = self.uf.makeList(rvs)
        vTys = rv
        rv = self.zephyr.makeSignature(vName, self.builtin.makeFlatten(vTys))
        return i, rv
    @cached
    def parseZTY(self, i):
        st = []
        i, rv = self.parseID(i)
        vName = rv
        if i >= len(self.s): raise ParseError()
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError()
        assert i >= 0
        if self.s[i:i + 1] != u"=": raise ParseError()
        self.lastMatch.append((u"TOKEN =", i, i + 1))
        rv = self.uf.makeStr(u"="); i += 1
        st.append(i)
        try:
            i, rv = self.parseFIELDS(i)
            vFs = rv
            rv = self.uf.makeList([self.zephyr.makeProduct(vName, vFs)])
        except ParseError:
            i = st.pop()
            i, rv = self.parseZCON(i)
            vCon = rv
            rvs = []
            while True:
                st.append(i)
                try:
                    if i >= len(self.s): raise ParseError()
                    while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                    if i >= len(self.s): raise ParseError()
                    assert i >= 0
                    if self.s[i:i + 1] != u"|": raise ParseError()
                    self.lastMatch.append((u"TOKEN |", i, i + 1))
                    rv = self.uf.makeStr(u"|"); i += 1
                    i, rv = self.parseZCON(i)
                    rvs.append(rv)
                except ParseError:
                    i = st.pop()
                    break
            rv = self.uf.makeList(rvs)
            vCons = rv
            st.append(i)
            try:
                if i >= len(self.s): raise ParseError()
                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                if i >= len(self.s): raise ParseError()
                assert i >= 0
                if self.s[i:i + 10] != u"attributes": raise ParseError()
                self.lastMatch.append((u"TOKEN attributes", i, i + 10))
                rv = self.uf.makeStr(u"attributes"); i += 10
                i, rv = self.parseFIELDS(i)
                vAttrs = rv
                rv = self.uf.makeList([self.zephyr.makeSum(vName, vAttrs, vCon, vCons)])
            except ParseError:
                i = st.pop()
                rv = self.uf.makeList([self.zephyr.makeSum(vName, self.uf.makeList([]), vCon, vCons)])
        return i, rv
    @cached
    def parseZCON(self, i):
        st = []
        i, rv = self.parseWS(i)
        st.append(i)
        try:
            i, rv = self.parseZCId(i)
            vTag = rv
            i, rv = self.parseFIELDS(i)
            vArgs = rv
            rv = self.zephyr.makeCon(vTag, vArgs)
        except ParseError:
            i = st.pop()
            i, rv = self.parseZCId(i)
            vTag = rv
            rv = self.zephyr.makeCon(vTag, self.uf.makeList([]))
        return i, rv
    @cached
    def parseFIELDS(self, i):
        st = []
        if i >= len(self.s): raise ParseError()
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError()
        assert i >= 0
        if self.s[i:i + 1] != u"(": raise ParseError()
        self.lastMatch.append((u"TOKEN (", i, i + 1))
        rv = self.uf.makeStr(u"("); i += 1
        i, rv = self.parseFIELD(i)
        vF = rv
        rvs = []
        while True:
            st.append(i)
            try:
                if i >= len(self.s): raise ParseError()
                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                if i >= len(self.s): raise ParseError()
                assert i >= 0
                if self.s[i:i + 1] != u",": raise ParseError()
                self.lastMatch.append((u"TOKEN ,", i, i + 1))
                rv = self.uf.makeStr(u","); i += 1
                i, rv = self.parseFIELD(i)
                rvs.append(rv)
            except ParseError:
                i = st.pop()
                break
        rv = self.uf.makeList(rvs)
        vFs = rv
        if i >= len(self.s): raise ParseError()
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError()
        assert i >= 0
        if self.s[i:i + 1] != u")": raise ParseError()
        self.lastMatch.append((u"TOKEN )", i, i + 1))
        rv = self.uf.makeStr(u")"); i += 1
        rv = self.builtin.makeFlatten(self.uf.makeList([self.uf.makeList([vF]), vFs]))
        return i, rv
    @cached
    def parseFIELD(self, i):
        st = []
        i, rv = self.parseWS(i)
        st.append(i)
        try:
            i, rv = self.parseZTId(i)
            vTy = rv
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            assert i >= 0
            if self.s[i:i + 1] != u"?": raise ParseError()
            self.lastMatch.append((u"TOKEN ?", i, i + 1))
            rv = self.uf.makeStr(u"?"); i += 1
            i, rv = self.parseID(i)
            vName = rv
            rv = self.zephyr.makeOption(vTy, vName)
        except ParseError:
            i = st.pop()
            st.append(i)
            try:
                i, rv = self.parseZTId(i)
                vTy = rv
                if i >= len(self.s): raise ParseError()
                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                if i >= len(self.s): raise ParseError()
                assert i >= 0
                if self.s[i:i + 1] != u"*": raise ParseError()
                self.lastMatch.append((u"TOKEN *", i, i + 1))
                rv = self.uf.makeStr(u"*"); i += 1
                i, rv = self.parseID(i)
                vName = rv
                rv = self.zephyr.makeSequence(vTy, vName)
            except ParseError:
                i = st.pop()
                i, rv = self.parseZTId(i)
                vTy = rv
                i, rv = self.parseID(i)
                vName = rv
                rv = self.zephyr.makeId(vTy, vName)
        return i, rv
    @cached
    def parseRULES(self, i):
        st = []
        if i >= len(self.s): raise ParseError()
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError()
        assert i >= 0
        if self.s[i:i + 6] != u".rules": raise ParseError()
        self.lastMatch.append((u"TOKEN .rules", i, i + 6))
        rv = self.uf.makeStr(u".rules"); i += 6
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
        rv = self.uf.makeList(rvs)
        vHs = rv
        rv = self.builtin.makeFlatten(vHs)
        return i, rv
    @cached
    def parseCHRULE(self, i):
        st = []
        i, rv = self.parseID(i)
        vName = rv
        if i >= len(self.s): raise ParseError()
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError()
        assert i >= 0
        if self.s[i:i + 1] != u"@": raise ParseError()
        self.lastMatch.append((u"TOKEN @", i, i + 1))
        rv = self.uf.makeStr(u"@"); i += 1
        i, rv = self.parseWS(i)
        i, rv = self.parseCPATT(i)
        vRoot = rv
        if i >= len(self.s): raise ParseError()
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError()
        assert i >= 0
        if self.s[i:i + 3] != u"==>": raise ParseError()
        self.lastMatch.append((u"TOKEN ==>", i, i + 3))
        rv = self.uf.makeStr(u"==>"); i += 3
        i, rv = self.parseCPRODS(i)
        vProds = rv
        if i >= len(self.s): raise ParseError()
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError()
        assert i >= 0
        if self.s[i:i + 1] != u";": raise ParseError()
        self.lastMatch.append((u"TOKEN ;", i, i + 1))
        rv = self.uf.makeStr(u";"); i += 1
        rv = self.rules.makeRewrite(vName, vRoot, vProds)
        return i, rv
    @cached
    def parseCHLET(self, i):
        st = []
        if i >= len(self.s): raise ParseError()
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError()
        assert i >= 0
        if self.s[i:i + 3] != u"let": raise ParseError()
        self.lastMatch.append((u"TOKEN let", i, i + 3))
        rv = self.uf.makeStr(u"let"); i += 3
        i, rv = self.parseID(i)
        vName = rv
        if i >= len(self.s): raise ParseError()
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError()
        assert i >= 0
        if self.s[i:i + 2] != u":=": raise ParseError()
        self.lastMatch.append((u"TOKEN :=", i, i + 2))
        rv = self.uf.makeStr(u":="); i += 2
        i, rv = self.parseCPROD1(i)
        vP = rv
        if i >= len(self.s): raise ParseError()
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError()
        assert i >= 0
        if self.s[i:i + 1] != u";": raise ParseError()
        self.lastMatch.append((u"TOKEN ;", i, i + 1))
        rv = self.uf.makeStr(u";"); i += 1
        rv = self.rules.makeLet(vName, vP)
        return i, rv
    @cached
    def parseCPATTS(self, i):
        st = []
        i, rv = self.parseWS(i)
        i, rv = self.parseCPATT(i)
        vP = rv
        rvs = []
        while True:
            st.append(i)
            try:
                if i >= len(self.s): raise ParseError()
                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                if i >= len(self.s): raise ParseError()
                assert i >= 0
                if self.s[i:i + 1] != u",": raise ParseError()
                self.lastMatch.append((u"TOKEN ,", i, i + 1))
                rv = self.uf.makeStr(u","); i += 1
                i, rv = self.parseWS(i)
                i, rv = self.parseCPATT(i)
                rvs.append(rv)
            except ParseError:
                i = st.pop()
                break
        rv = self.uf.makeList(rvs)
        vPs = rv
        rv = self.builtin.makeFlatten(self.uf.makeList([self.uf.makeList([vP]), vPs]))
        return i, rv
    @cached
    def parsePATTDOTS(self, i):
        st = []
        i, rv = self.parseWS(i)
        i, rv = self.parsePVar(i)
        vN = rv
        i, rv = self.parseEllipsis(i)
        rv = self.rules.makeVarPatt(vN)
        return i, rv
    @cached
    def parseCPATT(self, i):
        st = []
        st.append(i)
        try:
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            assert i >= 0
            if self.s[i:i + 1] != u"_": raise ParseError()
            self.lastMatch.append((u"TOKEN _", i, i + 1))
            rv = self.uf.makeStr(u"_"); i += 1
            rv = self.rules.IgnorePatt
        except ParseError:
            i = st.pop()
            st.append(i)
            try:
                if i >= len(self.s): raise ParseError()
                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                if i >= len(self.s): raise ParseError()
                assert i >= 0
                if self.s[i:i + 2] != u"[]": raise ParseError()
                self.lastMatch.append((u"TOKEN []", i, i + 2))
                rv = self.uf.makeStr(u"[]"); i += 2
                rv = self.rules.makeListPatt(self.uf.makeList([]))
            except ParseError:
                i = st.pop()
                st.append(i)
                try:
                    if i >= len(self.s): raise ParseError()
                    while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                    if i >= len(self.s): raise ParseError()
                    assert i >= 0
                    if self.s[i:i + 1] != u"[": raise ParseError()
                    self.lastMatch.append((u"TOKEN [", i, i + 1))
                    rv = self.uf.makeStr(u"["); i += 1
                    i, rv = self.parsePATTDOTS(i)
                    vHead = rv
                    if i >= len(self.s): raise ParseError()
                    while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                    if i >= len(self.s): raise ParseError()
                    assert i >= 0
                    if self.s[i:i + 1] != u",": raise ParseError()
                    self.lastMatch.append((u"TOKEN ,", i, i + 1))
                    rv = self.uf.makeStr(u","); i += 1
                    i, rv = self.parseCPATTS(i)
                    vPs = rv
                    if i >= len(self.s): raise ParseError()
                    while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                    if i >= len(self.s): raise ParseError()
                    assert i >= 0
                    if self.s[i:i + 1] != u",": raise ParseError()
                    self.lastMatch.append((u"TOKEN ,", i, i + 1))
                    rv = self.uf.makeStr(u","); i += 1
                    i, rv = self.parsePATTDOTS(i)
                    vTail = rv
                    if i >= len(self.s): raise ParseError()
                    while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                    if i >= len(self.s): raise ParseError()
                    assert i >= 0
                    if self.s[i:i + 1] != u"]": raise ParseError()
                    self.lastMatch.append((u"TOKEN ]", i, i + 1))
                    rv = self.uf.makeStr(u"]"); i += 1
                    rv = self.rules.makeListMidPatt(vHead, vTail, vPs)
                except ParseError:
                    i = st.pop()
                    st.append(i)
                    try:
                        if i >= len(self.s): raise ParseError()
                        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                        if i >= len(self.s): raise ParseError()
                        assert i >= 0
                        if self.s[i:i + 1] != u"[": raise ParseError()
                        self.lastMatch.append((u"TOKEN [", i, i + 1))
                        rv = self.uf.makeStr(u"["); i += 1
                        i, rv = self.parsePATTDOTS(i)
                        vHead = rv
                        if i >= len(self.s): raise ParseError()
                        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                        if i >= len(self.s): raise ParseError()
                        assert i >= 0
                        if self.s[i:i + 1] != u",": raise ParseError()
                        self.lastMatch.append((u"TOKEN ,", i, i + 1))
                        rv = self.uf.makeStr(u","); i += 1
                        i, rv = self.parseCPATTS(i)
                        vPs = rv
                        if i >= len(self.s): raise ParseError()
                        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                        if i >= len(self.s): raise ParseError()
                        assert i >= 0
                        if self.s[i:i + 1] != u"]": raise ParseError()
                        self.lastMatch.append((u"TOKEN ]", i, i + 1))
                        rv = self.uf.makeStr(u"]"); i += 1
                        rv = self.rules.makeListHeadPatt(vHead, vPs)
                    except ParseError:
                        i = st.pop()
                        st.append(i)
                        try:
                            if i >= len(self.s): raise ParseError()
                            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                            if i >= len(self.s): raise ParseError()
                            assert i >= 0
                            if self.s[i:i + 1] != u"[": raise ParseError()
                            self.lastMatch.append((u"TOKEN [", i, i + 1))
                            rv = self.uf.makeStr(u"["); i += 1
                            i, rv = self.parseCPATTS(i)
                            vPs = rv
                            if i >= len(self.s): raise ParseError()
                            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                            if i >= len(self.s): raise ParseError()
                            assert i >= 0
                            if self.s[i:i + 1] != u",": raise ParseError()
                            self.lastMatch.append((u"TOKEN ,", i, i + 1))
                            rv = self.uf.makeStr(u","); i += 1
                            i, rv = self.parsePATTDOTS(i)
                            vTail = rv
                            if i >= len(self.s): raise ParseError()
                            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                            if i >= len(self.s): raise ParseError()
                            assert i >= 0
                            if self.s[i:i + 1] != u"]": raise ParseError()
                            self.lastMatch.append((u"TOKEN ]", i, i + 1))
                            rv = self.uf.makeStr(u"]"); i += 1
                            rv = self.rules.makeListTailPatt(vTail, vPs)
                        except ParseError:
                            i = st.pop()
                            st.append(i)
                            try:
                                if i >= len(self.s): raise ParseError()
                                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                if i >= len(self.s): raise ParseError()
                                assert i >= 0
                                if self.s[i:i + 1] != u"[": raise ParseError()
                                self.lastMatch.append((u"TOKEN [", i, i + 1))
                                rv = self.uf.makeStr(u"["); i += 1
                                i, rv = self.parseCPATTS(i)
                                vPs = rv
                                if i >= len(self.s): raise ParseError()
                                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                if i >= len(self.s): raise ParseError()
                                assert i >= 0
                                if self.s[i:i + 1] != u"]": raise ParseError()
                                self.lastMatch.append((u"TOKEN ]", i, i + 1))
                                rv = self.uf.makeStr(u"]"); i += 1
                                rv = self.rules.makeListPatt(vPs)
                            except ParseError:
                                i = st.pop()
                                st.append(i)
                                try:
                                    i, rv = self.parseSTRING(i)
                                    vS = rv
                                    rv = self.rules.makeStrPatt(vS)
                                except ParseError:
                                    i = st.pop()
                                    st.append(i)
                                    try:
                                        i, rv = self.parseID(i)
                                        vNs = rv
                                        if i >= len(self.s): raise ParseError()
                                        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                        if i >= len(self.s): raise ParseError()
                                        assert i >= 0
                                        if self.s[i:i + 1] != u".": raise ParseError()
                                        self.lastMatch.append((u"TOKEN .", i, i + 1))
                                        rv = self.uf.makeStr(u"."); i += 1
                                        i, rv = self.parseID(i)
                                        vFunc = rv
                                        if i >= len(self.s): raise ParseError()
                                        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                        if i >= len(self.s): raise ParseError()
                                        assert i >= 0
                                        if self.s[i:i + 1] != u"(": raise ParseError()
                                        self.lastMatch.append((u"TOKEN (", i, i + 1))
                                        rv = self.uf.makeStr(u"("); i += 1
                                        i, rv = self.parseCPATTS(i)
                                        vPs = rv
                                        if i >= len(self.s): raise ParseError()
                                        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                        if i >= len(self.s): raise ParseError()
                                        assert i >= 0
                                        assert i >= 0
                                        if self.s[i:i + 1] != u")": raise ParseError()
                                        self.lastMatch.append((u"TOKEN )", i, i + 1))
                                        rv = self.uf.makeStr(u")"); i += 1
                                        rv = self.rules.makeStructPatt(vNs, vFunc, vPs)
                                    except ParseError:
                                        i = st.pop()
                                        st.append(i)
                                        try:
                                            i, rv = self.parseID(i)
                                            vNs = rv
                                            if i >= len(self.s): raise ParseError()
                                            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                            if i >= len(self.s): raise ParseError()
                                            assert i >= 0
                                            if self.s[i:i + 1] != u".": raise ParseError()
                                            self.lastMatch.append((u"TOKEN .", i, i + 1))
                                            rv = self.uf.makeStr(u"."); i += 1
                                            i, rv = self.parseID(i)
                                            vFunc = rv
                                            rv = self.rules.makeStructPatt(vNs,
                                                                          vFunc,
                                                                          self.uf.makeList([]))
                                        except ParseError:
                                            i = st.pop()
                                            i, rv = self.parsePVar(i)
                                            vName = rv
                                            st.append(i)
                                            try:
                                                i, rv = self.parseEllipsis(i)
                                                rv = True
                                            except ParseError:
                                                rv = False
                                            i = st.pop()
                                            if rv: raise ParseError()
                                            rv = self.rules.makeVarPatt(vName)
        return i, rv
    @cached
    def parseCPRODS(self, i):
        st = []
        i, rv = self.parseCPROD1(i)
        vP = rv
        rvs = []
        while True:
            st.append(i)
            try:
                if i >= len(self.s): raise ParseError()
                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                if i >= len(self.s): raise ParseError()
                assert i >= 0
                if self.s[i:i + 1] != u",": raise ParseError()
                self.lastMatch.append((u"TOKEN ,", i, i + 1))
                rv = self.uf.makeStr(u","); i += 1
                i, rv = self.parseCPROD1(i)
                rvs.append(rv)
            except ParseError:
                i = st.pop()
                break
        rv = self.uf.makeList(rvs)
        vPs = rv
        rv = self.builtin.makeFlatten(self.uf.makeList([self.uf.makeList([vP]), vPs]))
        return i, rv
    @cached
    def parseCPROD1(self, i):
        st = []
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
                except ParseError:
                    i = st.pop()
                    break
            rv = self.uf.makeList(rvs)
            if not len(rvs): raise ParseError()
            vPs = rv
            rv = self.rules.makeConcatOp(vP, vPs)
        except ParseError:
            i = st.pop()
            i, rv = self.parseWS(i)
            i, rv = self.parseCPROD2(i)
        return i, rv
    @cached
    def parseCPROD2(self, i):
        st = []
        st.append(i)
        try:
            i, rv = self.parseSTRING(i)
            vS = rv
            rv = self.rules.makeStrProd(vS)
        except ParseError:
            i = st.pop()
            st.append(i)
            try:
                i, rv = self.parseNumber(i)
                vN = rv
                rv = self.rules.makeCharProd(vN)
            except ParseError:
                i = st.pop()
                st.append(i)
                try:
                    if i >= len(self.s): raise ParseError()
                    while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                    if i >= len(self.s): raise ParseError()
                    assert i >= 0
                    if self.s[i:i + 1] != u"#": raise ParseError()
                    self.lastMatch.append((u"TOKEN #", i, i + 1))
                    rv = self.uf.makeStr(u"#"); i += 1
                    i, rv = self.parseCPROD2(i)
                    vP = rv
                    rv = self.rules.makeLengthOp(vP)
                except ParseError:
                    i = st.pop()
                    st.append(i)
                    try:
                        if i >= len(self.s): raise ParseError()
                        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                        if i >= len(self.s): raise ParseError()
                        assert i >= 0
                        if self.s[i:i + 1] != u"*": raise ParseError()
                        self.lastMatch.append((u"TOKEN *", i, i + 1))
                        rv = self.uf.makeStr(u"*"); i += 1
                        i, rv = self.parseCPROD2(i)
                        vP = rv
                        rv = self.rules.makeFlattenOp(vP)
                    except ParseError:
                        i = st.pop()
                        st.append(i)
                        try:
                            if i >= len(self.s): raise ParseError()
                            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                            if i >= len(self.s): raise ParseError()
                            assert i >= 0
                            if self.s[i:i + 2] != u"*(": raise ParseError()
                            self.lastMatch.append((u"TOKEN *(", i, i + 2))
                            rv = self.uf.makeStr(u"*("); i += 2
                            i, rv = self.parseCPROD1(i)
                            vP = rv
                            if i >= len(self.s): raise ParseError()
                            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                            if i >= len(self.s): raise ParseError()
                            assert i >= 0
                            if self.s[i:i + 1] != u")": raise ParseError()
                            self.lastMatch.append((u"TOKEN )", i, i + 1))
                            rv = self.uf.makeStr(u")"); i += 1
                            rv = self.rules.makeFlattenOp(vP)
                        except ParseError:
                            i = st.pop()
                            st.append(i)
                            try:
                                if i >= len(self.s): raise ParseError()
                                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                if i >= len(self.s): raise ParseError()
                                assert i >= 0
                                if self.s[i:i + 6] != u".line(": raise ParseError()
                                self.lastMatch.append((u"TOKEN .line(", i, i + 6))
                                rv = self.uf.makeStr(u".line("); i += 6
                                i, rv = self.parseCPROD1(i)
                                vP = rv
                                if i >= len(self.s): raise ParseError()
                                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                if i >= len(self.s): raise ParseError()
                                assert i >= 0
                                if self.s[i:i + 1] != u")": raise ParseError()
                                self.lastMatch.append((u"TOKEN )", i, i + 1))
                                rv = self.uf.makeStr(u")"); i += 1
                                rv = self.rules.makeStructProd(self.uf.makeStr(u'builtin'), self.uf.makeStr(u'Line'), self.uf.makeList([vP]))
                            except ParseError:
                                i = st.pop()
                                st.append(i)
                                try:
                                    if i >= len(self.s): raise ParseError()
                                    while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                    if i >= len(self.s): raise ParseError()
                                    assert i >= 0
                                    if self.s[i:i + 7] != u".block(": raise ParseError()
                                    self.lastMatch.append((u"TOKEN .block(", i, i + 7))
                                    rv = self.uf.makeStr(u".block("); i += 7
                                    i, rv = self.parseCPROD1(i)
                                    vP = rv
                                    if i >= len(self.s): raise ParseError()
                                    while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                    if i >= len(self.s): raise ParseError()
                                    assert i >= 0
                                    if self.s[i:i + 1] != u")": raise ParseError()
                                    self.lastMatch.append((u"TOKEN )", i, i + 1))
                                    rv = self.uf.makeStr(u")"); i += 1
                                    rv = self.rules.makeStructProd(self.uf.makeStr(u'builtin'), self.uf.makeStr(u'Block'), self.uf.makeList([vP]))
                                except ParseError:
                                    i = st.pop()
                                    st.append(i)
                                    try:
                                        if i >= len(self.s): raise ParseError()
                                        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                        if i >= len(self.s): raise ParseError()
                                        assert i >= 0
                                        if self.s[i:i + 6] != u".join(": raise ParseError()
                                        self.lastMatch.append((u"TOKEN .join(", i, i + 6))
                                        rv = self.uf.makeStr(u".join("); i += 6
                                        i, rv = self.parseCPROD1(i)
                                        vP = rv
                                        if i >= len(self.s): raise ParseError()
                                        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                        if i >= len(self.s): raise ParseError()
                                        assert i >= 0
                                        if self.s[i:i + 1] != u",": raise ParseError()
                                        self.lastMatch.append((u"TOKEN ,", i, i + 1))
                                        rv = self.uf.makeStr(u","); i += 1
                                        i, rv = self.parseSTRING(i)
                                        vS = rv
                                        if i >= len(self.s): raise ParseError()
                                        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                        if i >= len(self.s): raise ParseError()
                                        assert i >= 0
                                        if self.s[i:i + 1] != u")": raise ParseError()
                                        self.lastMatch.append((u"TOKEN )", i, i + 1))
                                        rv = self.uf.makeStr(u")"); i += 1
                                        rv = self.rules.makeJoinOp(vS, vP)
                                    except ParseError:
                                        i = st.pop()
                                        st.append(i)
                                        try:
                                            if i >= len(self.s): raise ParseError()
                                            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                            if i >= len(self.s): raise ParseError()
                                            assert i >= 0
                                            if self.s[i:i + 2] != u"[]": raise ParseError()
                                            self.lastMatch.append((u"TOKEN []", i, i + 2))
                                            rv = self.uf.makeStr(u"[]"); i += 2
                                            rv = self.rules.makeListProd(self.uf.makeList([]))
                                        except ParseError:
                                            i = st.pop()
                                            st.append(i)
                                            try:
                                                if i >= len(self.s): raise ParseError()
                                                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                                if i >= len(self.s): raise ParseError()
                                                assert i >= 0
                                                if self.s[i:i + 1] != u"[": raise ParseError()
                                                self.lastMatch.append((u"TOKEN [", i, i + 1))
                                                rv = self.uf.makeStr(u"["); i += 1
                                                i, rv = self.parsePATTDOTS(i)
                                                vHead = rv
                                                if i >= len(self.s): raise ParseError()
                                                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                                if i >= len(self.s): raise ParseError()
                                                assert i >= 0
                                                if self.s[i:i + 1] != u",": raise ParseError()
                                                self.lastMatch.append((u"TOKEN ,", i, i + 1))
                                                rv = self.uf.makeStr(u","); i += 1
                                                i, rv = self.parseCPRODS(i)
                                                vPs = rv
                                                if i >= len(self.s): raise ParseError()
                                                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                                if i >= len(self.s): raise ParseError()
                                                assert i >= 0
                                                if self.s[i:i + 1] != u",": raise ParseError()
                                                self.lastMatch.append((u"TOKEN ,", i, i + 1))
                                                rv = self.uf.makeStr(u","); i += 1
                                                i, rv = self.parsePATTDOTS(i)
                                                vTail = rv
                                                if i >= len(self.s): raise ParseError()
                                                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                                if i >= len(self.s): raise ParseError()
                                                assert i >= 0
                                                if self.s[i:i + 1] != u"]": raise ParseError()
                                                self.lastMatch.append((u"TOKEN ]", i, i + 1))
                                                rv = self.uf.makeStr(u"]"); i += 1
                                                rv = self.rules.makeListMidProd(vHead, vTail, vPs)
                                            except ParseError:
                                                i = st.pop()
                                                st.append(i)
                                                try:
                                                    if i >= len(self.s): raise ParseError()
                                                    while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                                    if i >= len(self.s): raise ParseError()
                                                    assert i >= 0
                                                    if self.s[i:i + 1] != u"[": raise ParseError()
                                                    self.lastMatch.append((u"TOKEN [", i, i + 1))
                                                    rv = self.uf.makeStr(u"["); i += 1
                                                    i, rv = self.parsePATTDOTS(i)
                                                    vHead = rv
                                                    if i >= len(self.s): raise ParseError()
                                                    while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                                    if i >= len(self.s): raise ParseError()
                                                    assert i >= 0
                                                    if self.s[i:i + 1] != u",": raise ParseError()
                                                    self.lastMatch.append((u"TOKEN ,", i, i + 1))
                                                    rv = self.uf.makeStr(u","); i += 1
                                                    i, rv = self.parseCPRODS(i)
                                                    vPs = rv
                                                    if i >= len(self.s): raise ParseError()
                                                    while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                                    if i >= len(self.s): raise ParseError()
                                                    assert i >= 0
                                                    if self.s[i:i + 1] != u"]": raise ParseError()
                                                    self.lastMatch.append((u"TOKEN ]", i, i + 1))
                                                    rv = self.uf.makeStr(u"]"); i += 1
                                                    rv = self.rules.makeListHeadProd(vHead, vPs)
                                                except ParseError:
                                                    i = st.pop()
                                                    st.append(i)
                                                    try:
                                                        if i >= len(self.s): raise ParseError()
                                                        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                                        if i >= len(self.s): raise ParseError()
                                                        assert i >= 0
                                                        if self.s[i:i + 1] != u"[": raise ParseError()
                                                        self.lastMatch.append((u"TOKEN [", i, i + 1))
                                                        rv = self.uf.makeStr(u"["); i += 1
                                                        i, rv = self.parseCPRODS(i)
                                                        vPs = rv
                                                        if i >= len(self.s): raise ParseError()
                                                        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                                        if i >= len(self.s): raise ParseError()
                                                        assert i >= 0
                                                        if self.s[i:i + 1] != u",": raise ParseError()
                                                        self.lastMatch.append((u"TOKEN ,", i, i + 1))
                                                        rv = self.uf.makeStr(u","); i += 1
                                                        i, rv = self.parsePATTDOTS(i)
                                                        vTail = rv
                                                        if i >= len(self.s): raise ParseError()
                                                        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                                        if i >= len(self.s): raise ParseError()
                                                        assert i >= 0
                                                        if self.s[i:i + 1] != u"]": raise ParseError()
                                                        self.lastMatch.append((u"TOKEN ]", i, i + 1))
                                                        rv = self.uf.makeStr(u"]"); i += 1
                                                        rv = self.rules.makeListTailProd(vTail, vPs)
                                                    except ParseError:
                                                        i = st.pop()
                                                        st.append(i)
                                                        try:
                                                            if i >= len(self.s): raise ParseError()
                                                            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                                            if i >= len(self.s): raise ParseError()
                                                            assert i >= 0
                                                            if self.s[i:i + 1] != u"[": raise ParseError()
                                                            self.lastMatch.append((u"TOKEN [", i, i + 1))
                                                            rv = self.uf.makeStr(u"["); i += 1
                                                            i, rv = self.parseCPRODS(i)
                                                            vPs = rv
                                                            if i >= len(self.s): raise ParseError()
                                                            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                                            if i >= len(self.s): raise ParseError()
                                                            assert i >= 0
                                                            if self.s[i:i + 1] != u"]": raise ParseError()
                                                            self.lastMatch.append((u"TOKEN ]", i, i + 1))
                                                            rv = self.uf.makeStr(u"]"); i += 1
                                                            rv = self.rules.makeListProd(vPs)
                                                        except ParseError:
                                                            i = st.pop()
                                                            st.append(i)
                                                            try:
                                                                i, rv = self.parsePVar(i)
                                                                vName = rv
                                                                st.append(i)
                                                                try:
                                                                    i, rv = self.parseEllipsis(i)
                                                                    rv = True
                                                                except ParseError:
                                                                    rv = False
                                                                i = st.pop()
                                                                if rv: raise ParseError()
                                                                rv = self.rules.makeVarProd(vName)
                                                            except ParseError:
                                                                i = st.pop()
                                                                st.append(i)
                                                                try:
                                                                    i, rv = self.parsePConst(i)
                                                                    vName = rv
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
                                                                        assert i >= 0
                                                                        if self.s[i:i + 1] != u".": raise ParseError()
                                                                        self.lastMatch.append((u"TOKEN .", i, i + 1))
                                                                        rv = self.uf.makeStr(u"."); i += 1
                                                                        rv = True
                                                                    except ParseError:
                                                                        rv = False
                                                                    i = st.pop()
                                                                    if rv: raise ParseError()
                                                                    rv = self.rules.makeConstProd(vName)
                                                                except ParseError:
                                                                    i = st.pop()
                                                                    st.append(i)
                                                                    try:
                                                                        i, rv = self.parseID(i)
                                                                        vNs = rv
                                                                        if i >= len(self.s): raise ParseError()
                                                                        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                                                        if i >= len(self.s): raise ParseError()
                                                                        assert i >= 0
                                                                        if self.s[i:i + 1] != u".": raise ParseError()
                                                                        self.lastMatch.append((u"TOKEN .", i, i + 1))
                                                                        rv = self.uf.makeStr(u"."); i += 1
                                                                        i, rv = self.parseID(i)
                                                                        vFunc = rv
                                                                        if i >= len(self.s): raise ParseError()
                                                                        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                                                        if i >= len(self.s): raise ParseError()
                                                                        assert i >= 0
                                                                        if self.s[i:i + 1] != u"(": raise ParseError()
                                                                        self.lastMatch.append((u"TOKEN (", i, i + 1))
                                                                        rv = self.uf.makeStr(u"("); i += 1
                                                                        i, rv = self.parseCPRODS(i)
                                                                        vPs = rv
                                                                        if i >= len(self.s): raise ParseError()
                                                                        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                                                        if i >= len(self.s): raise ParseError()
                                                                        assert i >= 0
                                                                        if self.s[i:i + 1] != u")": raise ParseError()
                                                                        self.lastMatch.append((u"TOKEN )", i, i + 1))
                                                                        rv = self.uf.makeStr(u")"); i += 1
                                                                        rv = self.rules.makeStructProd(vNs, vFunc, vPs)
                                                                    except ParseError:
                                                                        i = st.pop()
                                                                        i, rv = self.parseID(i)
                                                                        vNs = rv
                                                                        if i >= len(self.s): raise ParseError()
                                                                        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                                                        if i >= len(self.s): raise ParseError()
                                                                        assert i >= 0
                                                                        if self.s[i:i + 1] != u".": raise ParseError()
                                                                        self.lastMatch.append((u"TOKEN .", i, i + 1))
                                                                        rv = self.uf.makeStr(u"."); i += 1
                                                                        i, rv = self.parseID(i)
                                                                        vFunc = rv
                                                                        rv = self.rules.makeStructProd(vNs,
                                                                                                 vFunc,
                                                                                                 self.uf.makeList([]))
        return i, rv
    @cached
    def parseGRAMMAR(self, i):
        st = []
        if i >= len(self.s): raise ParseError()
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError()
        assert i >= 0
        if self.s[i:i + 8] != u".grammar": raise ParseError()
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
        rv = self.uf.makeList(rvs)
        vRules = rv
        rv = self.uf.makeList([
            self.py.makeCompound(self.uf.makeStr(u'def target(driver, *args)'), self.uf.makeList([self.py.makeStatement(self.uf.makeStr(u'driver.exe_name = "' + self.uf.findStr(vName) + u'".lower() + "c"')), self.py.makeRet(self.uf.makeStr(u'main, None'))])),
            self.py.makeStatement(self.uf.makeStr(u'@finishsigs')),
            self.py.makeCompound(self.uf.makeStr(u'class ' + self.uf.findStr(vName) + u'Parser(object)'), self.builtin.makeFlatten(self.uf.makeList([
                self.uf.makeList([
                    self.py.makeCompound(self.uf.makeStr(u'def __init__(self, s, uf)'), self.uf.makeList([
                        self.py.makeStatement(self.uf.makeStr(u'self.s = s; self.uf = uf')),
                        self.py.makeStatement(self.uf.makeStr(u'self.lastMatch = []')),
                        self.py.makeStatement(self.uf.makeStr(u'for name in unrolledRels: setattr(self, name, frozenRels[name](uf))')),
                        self.py.makeStatement(self.uf.makeStr(u'for l in unrolledLets: l(uf, self)')),
                        ])), self.py.makeCompound(self.uf.makeStr(u'def parse(self)'), self.uf.makeList([self.py.makeRet(self.uf.makeStr(u'self.parse' + self.uf.findStr(vName) + u'(0)'))]))]), self.builtin.makeFlatten(vRules)]))),
            self.py.makeStatement(self.uf.makeStr(u'MainParser = ' + self.uf.findStr(vName) + u'Parser'))])
        return i, rv
    @cached
    def parsePCLASS(self, i):
        st = []
        if i >= len(self.s): raise ParseError()
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError()
        assert i >= 0
        if self.s[i:i + 5] != u"class": raise ParseError()
        self.lastMatch.append((u"TOKEN class", i, i + 5))
        rv = self.uf.makeStr(u"class"); i += 5
        i, rv = self.parseID(i)
        vName = rv
        if i >= len(self.s): raise ParseError()
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError()
        assert i >= 0
        if self.s[i:i + 1] != u"=": raise ParseError()
        self.lastMatch.append((u"TOKEN =", i, i + 1))
        rv = self.uf.makeStr(u"="); i += 1
        i, rv = self.parseCLASSEXPR1(i)
        vC = rv
        if i >= len(self.s): raise ParseError()
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError()
        assert i >= 0
        if self.s[i:i + 1] != u";": raise ParseError()
        self.lastMatch.append((u"TOKEN ;", i, i + 1))
        rv = self.uf.makeStr(u";"); i += 1
        rv = self.uf.makeList([self.py.makeCompound(self.uf.makeStr(u'def cls' + self.uf.findStr(vName) + u'(self, c)'), self.uf.makeList([self.py.makeRet(vC)]))])
        return i, rv
    @cached
    def parseCLASSEXPR1(self, i):
        st = []
        st.append(i)
        try:
            i, rv = self.parseCLASSEXPR2(i)
            vL = rv
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            assert i >= 0
            if self.s[i:i + 1] != u"|": raise ParseError()
            self.lastMatch.append((u"TOKEN |", i, i + 1))
            rv = self.uf.makeStr(u"|"); i += 1
            i, rv = self.parseCLASSEXPR1(i)
            vR = rv
            rv = self.char.makeEither(vL, vR)
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
            assert i >= 0
            if self.s[i:i + 4] != u".any": raise ParseError()
            self.lastMatch.append((u"TOKEN .any", i, i + 4))
            rv = self.uf.makeStr(u".any"); i += 4
            rv = self.char.Any
        except ParseError:
            i = st.pop()
            st.append(i)
            try:
                if i >= len(self.s): raise ParseError()
                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                if i >= len(self.s): raise ParseError()
                assert i >= 0
                if self.s[i:i + 7] != u".range(": raise ParseError()
                self.lastMatch.append((u"TOKEN .range(", i, i + 7))
                rv = self.uf.makeStr(u".range("); i += 7
                i, rv = self.parseWS(i)
                i, rv = self.parseNumber(i)
                vL = rv
                if i >= len(self.s): raise ParseError()
                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                if i >= len(self.s): raise ParseError()
                assert i >= 0
                if self.s[i:i + 1] != u":": raise ParseError()
                self.lastMatch.append((u"TOKEN :", i, i + 1))
                rv = self.uf.makeStr(u":"); i += 1
                i, rv = self.parseWS(i)
                i, rv = self.parseNumber(i)
                vU = rv
                if i >= len(self.s): raise ParseError()
                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                if i >= len(self.s): raise ParseError()
                assert i >= 0
                if self.s[i:i + 1] != u")": raise ParseError()
                self.lastMatch.append((u"TOKEN )", i, i + 1))
                rv = self.uf.makeStr(u")"); i += 1
                rv = self.char.makeRange(vL, vU)
            except ParseError:
                i = st.pop()
                st.append(i)
                try:
                    if i >= len(self.s): raise ParseError()
                    while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                    if i >= len(self.s): raise ParseError()
                    assert i >= 0
                    if self.s[i:i + 1] != u"~": raise ParseError()
                    self.lastMatch.append((u"TOKEN ~", i, i + 1))
                    rv = self.uf.makeStr(u"~"); i += 1
                    i, rv = self.parseCLASSEXPR2(i)
                    vS = rv
                    rv = self.char.makeComplement(vS)
                except ParseError:
                    i = st.pop()
                    st.append(i)
                    try:
                        if i >= len(self.s): raise ParseError()
                        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                        if i >= len(self.s): raise ParseError()
                        assert i >= 0
                        if self.s[i:i + 1] != u"(": raise ParseError()
                        self.lastMatch.append((u"TOKEN (", i, i + 1))
                        rv = self.uf.makeStr(u"("); i += 1
                        i, rv = self.parseCLASSEXPR1(i)
                        vS = rv
                        if i >= len(self.s): raise ParseError()
                        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                        if i >= len(self.s): raise ParseError()
                        assert i >= 0
                        if self.s[i:i + 1] != u")": raise ParseError()
                        self.lastMatch.append((u"TOKEN )", i, i + 1))
                        rv = self.uf.makeStr(u")"); i += 1
                        rv = vS
                    except ParseError:
                        i = st.pop()
                        st.append(i)
                        try:
                            i, rv = self.parseWS(i)
                            i, rv = self.parseNumber(i)
                            vC = rv
                            rv = self.char.makeExactly(vC)
                        except ParseError:
                            i = st.pop()
                            i, rv = self.parseID(i)
                            vN = rv
                            rv = self.char.makeCall(vN)
        return i, rv
    @cached
    def parsePTOKEN(self, i):
        st = []
        if i >= len(self.s): raise ParseError()
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError()
        assert i >= 0
        if self.s[i:i + 5] != u"token": raise ParseError()
        self.lastMatch.append((u"TOKEN token", i, i + 5))
        rv = self.uf.makeStr(u"token"); i += 5
        i, rv = self.parseID(i)
        vName = rv
        if i >= len(self.s): raise ParseError()
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError()
        assert i >= 0
        if self.s[i:i + 1] != u"=": raise ParseError()
        self.lastMatch.append((u"TOKEN =", i, i + 1))
        rv = self.uf.makeStr(u"="); i += 1
        rvs = []
        while True:
            st.append(i)
            try:
                i, rv = self.parsePSCAN(i)
                rvs.append(rv)
            except ParseError:
                i = st.pop()
                break
        rv = self.uf.makeList(rvs)
        if not len(rvs): raise ParseError()
        vScans = rv
        if i >= len(self.s): raise ParseError()
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError()
        assert i >= 0
        if self.s[i:i + 1] != u";": raise ParseError()
        self.lastMatch.append((u"TOKEN ;", i, i + 1))
        rv = self.uf.makeStr(u";"); i += 1
        rv = self.uf.makeList([
            self.py.makeCompound(self.uf.makeStr(u'def parse' + self.uf.findStr(vName) + u'(self, i)'), self.builtin.makeFlatten(self.uf.makeList([
                self.uf.makeList([
                    self.constboundcheck,
                    self.py.makeStatement(self.uf.makeStr(u'start = i; assert start >= 0'))]), self.builtin.makeFlatten(vScans), self.uf.makeList([self.py.makeStatement(self.uf.makeStr(u'rv = self.uf.makeStr(self.s[start:i])')), self.py.makeStatement(self.uf.makeStr(u'self.lastMatch.append((u"TOKEN ' + self.uf.findStr(vName) + u'", start, i))')), self.py.makeRet(self.uf.makeStr(u'i, rv'))])])))])
        return i, rv
    @cached
    def parsePSCAN(self, i):
        st = []
        st.append(i)
        try:
            i, rv = self.parseID(i)
            vCls = rv
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            assert i >= 0
            if self.s[i:i + 1] != u"*": raise ParseError()
            self.lastMatch.append((u"TOKEN *", i, i + 1))
            rv = self.uf.makeStr(u"*"); i += 1
            rv = self.uf.makeList([self.py.makeStatement(self.uf.makeStr(u'while i < len(self.s) and self.cls' + self.uf.findStr(vCls) + u'(ord(self.s[i])): i += 1'))])
        except ParseError:
            i = st.pop()
            st.append(i)
            try:
                i, rv = self.parseID(i)
                vCls = rv
                if i >= len(self.s): raise ParseError()
                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                if i >= len(self.s): raise ParseError()
                assert i >= 0
                if self.s[i:i + 1] != u"+": raise ParseError()
                self.lastMatch.append((u"TOKEN +", i, i + 1))
                rv = self.uf.makeStr(u"+"); i += 1
                rv = self.uf.makeList([self.py.makeRaiseIf(self.uf.makeStr(u'i >= len(self.s) or not self.cls' + self.uf.findStr(vCls) + u'(ord(self.s[i]))')), self.py.makeStatement(self.uf.makeStr(u'while i < len(self.s) and self.cls' + self.uf.findStr(vCls) + u'(ord(self.s[i])): i += 1'))])
            except ParseError:
                i = st.pop()
                i, rv = self.parseID(i)
                vCls = rv
                rv = self.uf.makeList([self.py.makeRaiseIf(self.uf.makeStr(u'i >= len(self.s) or not self.cls' + self.uf.findStr(vCls) + u'(ord(self.s[i]))')), self.py.makeStatement(self.uf.makeStr(u'i += 1'))])
        return i, rv
    @cached
    def parsePRULE(self, i):
        st = []
        i, rv = self.parseID(i)
        vName = rv
        if i >= len(self.s): raise ParseError()
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError()
        assert i >= 0
        if self.s[i:i + 2] != u":=": raise ParseError()
        self.lastMatch.append((u"TOKEN :=", i, i + 2))
        rv = self.uf.makeStr(u":="); i += 2
        i, rv = self.parsePEXPR1(i)
        vExpr = rv
        if i >= len(self.s): raise ParseError()
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError()
        assert i >= 0
        if self.s[i:i + 1] != u";": raise ParseError()
        self.lastMatch.append((u"TOKEN ;", i, i + 1))
        rv = self.uf.makeStr(u";"); i += 1
        rv = self.uf.makeList([
            self.py.makeStatement(self.uf.makeStr(u'@cached')),
            self.py.makeCompound(self.uf.makeStr(u'def parse' + self.uf.findStr(vName) + u'(self, i)'), self.builtin.makeFlatten(self.uf.makeList([
                self.uf.makeList([
                    self.py.makeStatement(self.uf.makeStr(u'uf = self.uf; rel = self; st = []'))
                    ]),
                vExpr, self.uf.makeList([self.py.makeRet(self.uf.makeStr(u'i, rv'))])])))])
        return i, rv
    @cached
    def parsePEXPR1(self, i):
        st = []
        st.append(i)
        try:
            i, rv = self.parsePEXPR2(i)
            vThis = rv
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            assert i >= 0
            if self.s[i:i + 1] != u"/": raise ParseError()
            self.lastMatch.append((u"TOKEN /", i, i + 1))
            rv = self.uf.makeStr(u"/"); i += 1
            i, rv = self.parsePEXPR1(i)
            vThat = rv
            rv = self.peg.makeChoice(vThis, vThat)
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
            vExprs = rv
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            assert i >= 0
            if self.s[i:i + 2] != u"->": raise ParseError()
            self.lastMatch.append((u"TOKEN ->", i, i + 2))
            rv = self.uf.makeStr(u"->"); i += 2
            i, rv = self.parseCPROD1(i)
            vProd = rv
            rv = self.peg.makeProduction(vExprs, vProd)
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
        rv = self.uf.makeList(rvs)
        vExprs = rv
        rv = self.peg.makeSequence(vExprs)
        return i, rv
    @cached
    def parsePEXPR4(self, i):
        st = []
        st.append(i)
        try:
            i, rv = self.parsePEXPR5(i)
            vExpr = rv
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            assert i >= 0
            if self.s[i:i + 1] != u":": raise ParseError()
            self.lastMatch.append((u"TOKEN :", i, i + 1))
            rv = self.uf.makeStr(u":"); i += 1
            i, rv = self.parsePPATT(i)
            vP = rv
            rv = self.peg.makeCapture(vExpr, vP)
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
            assert i >= 0
            if self.s[i:i + 1] != u"(": raise ParseError()
            self.lastMatch.append((u"TOKEN (", i, i + 1))
            rv = self.uf.makeStr(u"("); i += 1
            i, rv = self.parsePPATT(i)
            vP = rv
            rvs = []
            while True:
                st.append(i)
                try:
                    if i >= len(self.s): raise ParseError()
                    while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                    if i >= len(self.s): raise ParseError()
                    assert i >= 0
                    if self.s[i:i + 1] != u",": raise ParseError()
                    self.lastMatch.append((u"TOKEN ,", i, i + 1))
                    rv = self.uf.makeStr(u","); i += 1
                    i, rv = self.parsePPATT(i)
                    rvs.append(rv)
                except ParseError:
                    i = st.pop()
                    break
            rv = self.uf.makeList(rvs)
            vPs = rv
            rv = self.peg.makeTuplePatt(self.builtin.makeFlatten(self.uf.makeList([self.uf.makeList([vP]), vPs])))
        except ParseError:
            i = st.pop()
            i, rv = self.parseID(i)
            vName = rv
            rv = self.peg.makeNamePatt(vName)
        return i, rv
    @cached
    def parsePEXPR5(self, i):
        st = []
        st.append(i)
        try:
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            assert i >= 0
            if self.s[i:i + 1] != u"&": raise ParseError()
            self.lastMatch.append((u"TOKEN &", i, i + 1))
            rv = self.uf.makeStr(u"&"); i += 1
            i, rv = self.parsePEXPR6(i)
            vExpr = rv
            rv = self.peg.makePositive(vExpr)
        except ParseError:
            i = st.pop()
            st.append(i)
            try:
                if i >= len(self.s): raise ParseError()
                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                if i >= len(self.s): raise ParseError()
                assert i >= 0
                if self.s[i:i + 1] != u"!": raise ParseError()
                self.lastMatch.append((u"TOKEN !", i, i + 1))
                rv = self.uf.makeStr(u"!"); i += 1
                i, rv = self.parsePEXPR6(i)
                vExpr = rv
                rv = self.peg.makeNegative(vExpr)
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
            vExpr = rv
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            assert i >= 0
            if self.s[i:i + 1] != u"*": raise ParseError()
            self.lastMatch.append((u"TOKEN *", i, i + 1))
            rv = self.uf.makeStr(u"*"); i += 1
            rv = self.peg.makeAny(vExpr)
        except ParseError:
            i = st.pop()
            st.append(i)
            try:
                i, rv = self.parsePEXPR7(i)
                vExpr = rv
                if i >= len(self.s): raise ParseError()
                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                if i >= len(self.s): raise ParseError()
                assert i >= 0
                if self.s[i:i + 1] != u"+": raise ParseError()
                self.lastMatch.append((u"TOKEN +", i, i + 1))
                rv = self.uf.makeStr(u"+"); i += 1
                rv = self.peg.makeSome(vExpr)
            except ParseError:
                i = st.pop()
                st.append(i)
                try:
                    i, rv = self.parsePEXPR7(i)
                    vExpr = rv
                    if i >= len(self.s): raise ParseError()
                    while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                    if i >= len(self.s): raise ParseError()
                    assert i >= 0
                    if self.s[i:i + 1] != u"?": raise ParseError()
                    self.lastMatch.append((u"TOKEN ?", i, i + 1))
                    rv = self.uf.makeStr(u"?"); i += 1
                    rv = self.peg.makeMaybe(vExpr)
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
            assert i >= 0
            if self.s[i:i + 1] != u"(": raise ParseError()
            self.lastMatch.append((u"TOKEN (", i, i + 1))
            rv = self.uf.makeStr(u"("); i += 1
            i, rv = self.parsePEXPR1(i)
            vExpr = rv
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            assert i >= 0
            if self.s[i:i + 1] != u")": raise ParseError()
            self.lastMatch.append((u"TOKEN )", i, i + 1))
            rv = self.uf.makeStr(u")"); i += 1
            rv = vExpr
        except ParseError:
            i = st.pop()
            st.append(i)
            try:
                i, rv = self.parseSTRING(i)
                vS = rv
                rv = self.peg.makeToken(vS)
            except ParseError:
                i = st.pop()
                i, rv = self.parseID(i)
                vName = rv
                rv = self.peg.makeCall(vName)
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
                        i, rv = self.parseGRAMMAR(i)
                rvs.append(rv)
            except ParseError:
                i = st.pop()
                break
        rv = self.uf.makeList(rvs)
        vClss = rv
        i, rv = self.parseWS(i)
        rv = self.builtin.makeFlatten(self.uf.makeList([
                self.uf.makeList([
                    self.uf.makeList([self.builtin.makeLine(self.uf.makeStr(u"\n".join(selfSrc)))])
                ]),
                self.builtin.makeFlatten(vClss),
                self.uf.makeList([
                    self.uf.makeList([
                        self.builtin.makeLine(self.uf.makeStr(u'frozenRels = dict(allRels)')),
                        self.builtin.makeLine(self.uf.makeStr(u'unrolledRels = unrolling_iterable(frozenRels)')),
                        self.builtin.makeLine(self.uf.makeStr(u'frozenRules = dict(ruleNames)')),
                        self.builtin.makeLine(self.uf.makeStr(u'unrolledRules = unrolling_iterable(frozenRules)')),
                        self.builtin.makeLine(self.uf.makeStr(u'frozenLets = letNames[:]')),
                        self.builtin.makeLine(self.uf.makeStr(u'unrolledLets = unrolling_iterable(frozenLets)')),
                        self.builtin.makeLine(self.uf.makeStr(u'frozenTriggers = dict(triggers)')),
                    ]),
                ]),
                ]))
        return i, rv
MainParser = ZADDYParser
