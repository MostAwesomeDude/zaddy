from rpython.rlib.rfile import create_stdio
from rpython.rlib.unroll import unrolling_iterable
from rpython.rlib.objectmodel import specialize
class Result(object): pass
class Failed(Result): pass
failed = Failed()
@specialize.call_location()
def flatten(xs):
    rv = []
    for x in xs: rv.extend(x)
    return rv
class Py(object):
    def line(self, m, s): return " " * (m * 4) + s
class Compound(Py):
    def __init__(self, head, block): self.head = head; self.block = block
    def out(self, buf, m):
        if self.block:
            buf.append(self.line(m, self.head + ":"))
            for b in self.block: b.out(buf, m + 1)
        else: buf.append(self.line(m, self.head + ": pass"))
class Conditional(Py):
    def __init__(self, test, block): self.test = test; self.block = block
    def out(self, buf, m):
        if not self.block: return
        buf.append(self.line(m, "if " + self.test + ":"))
        for b in self.block: b.out(buf, m + 1)
class Handler(Py):
    def __init__(self, block, handler): self.block = block; self.handler = handler
    def out(self, buf, m):
        if not self.block: return
        if self.handler:
            buf.append(self.line(m, "try:"))
            for b in self.block: b.out(buf, m + 1)
            buf.append(self.line(m, "except ParseError:"))
            for b in self.handler: b.out(buf, m + 1)
        else:
            for b in self.block: b.out(buf, m)
class Statement(Py):
    def __init__(self, s): self.s = s
    def out(self, buf, m): buf.append(self.line(m, self.s))
class Builder(object):
    def Compound(self, head, block): return Compound(head, block)
    def Conditional(self, test, block): return Conditional(test, block)
    def Handler(self, block, handler): return Handler(block, handler)
    def Statement(self, line): return Statement(line)
py = Builder()
save = Statement("st.append(i)")
backup = Statement("i = st.pop()")
class PEG(object):
    def Con(self, ty, con, prods): return ty + "." + con + "(" + ", ".join(prods) + ")"
    def Plus(self, left, right): return left + " + " + right
    def Mod(self, left, right): return right + ".join(" + left + ")"
    def Flatten(self, l): return "flatten(" + l + ")"
    def Name(self, s): return s
    def String(self, s): return "'" + s + "'"
    def List(self, prods): return "[" + ", ".join(prods) + "]"

    def Null(self): return []
    def AnyChar(self): return [py.Statement("rv = self.s[i]; i += 1")]
    def Char(self, i):
        return [py.Statement("if ord(self.s[i]) != " + str(i) + ": raise ParseError()"),
                py.Statement("rv = self.s[i]; i += 1")]
    def Range(self, l, u):
        return [py.Statement("if not (" + str(l) + " <= ord(self.s[i]) <= " + str(u) + "): raise ParseError()"),
                py.Statement("rv = self.s[i]; i += 1")]
    def Token(self, s):
        return [py.Statement("while ord(self.s[i]) in [9, 10, 13, 32]: i += 1"),
                py.Statement("if self.s[i:i + %d] != \"%s\": raise ParseError()" % (len(s), s)),
                py.Statement("rv = \"%s\"; i += %d" % (s, len(s)))]
    def Call(self, s): return [py.Statement("i, rv = self.parse" + s + "(i)")]
    def Sequence(self, exprs):
        rv = []
        for expr in exprs: rv.extend(expr)
        return rv
    def Choice(self, this, that): return [save] + [py.Handler(this, [backup] + that)]
    def Any(self, expr):
        return [py.Statement("rvs = []"),
                py.Compound("while True",
                            [save, py.Handler(expr +
                                        [py.Statement("rvs.append(rv)")],
                                        [backup, py.Statement("break")])]),
                py.Statement("rv = rvs")]
    def Some(self, expr):
        return self.Any(expr) + [py.Statement("if not rv: raise ParseError()")]
    def Maybe(self, expr): return [save, py.Handler(expr, [backup])]
    def Positive(self, expr):
        return [save, py.Handler(expr + [py.Statement("rv = True")],
                                 [py.Statement("rv = False")]),
                backup, py.Statement("if not rv: raise ParseError()")]
    def Negative(self, expr):
        return [save, py.Handler(expr + [py.Statement("rv = True")],
                                 [py.Statement("rv = False")]),
                backup, py.Statement("if rv: raise ParseError()")]
    def Capture(self, expr, name): return expr + [py.Statement(name + " = rv")]
    def Production(self, expr, prod): return expr + [py.Statement("rv = " + prod)]
peg = PEG()
selfSrc = open(__file__, "rb").read().split("\n")[:125]
def main(argv):
    stdin, stdout, stderr = create_stdio()
    parser = ZADDYParser(stdin.read())
    try:
        i, rule = parser.parse()
        if i != len(parser.s):
            stderr.write(("Failed to consume all input; ended at %d of %d\n")
                         % (i, len(parser.s)))
            raise ParseError()
        buf = selfSrc[:]
        rule.out(buf, 0)
        stdout.write("\n".join(buf))
        stderr.write("Wrote %d lines to stdout\n" % len(buf))
        return 0
    except ParseError:
        start = max(len(parser.lastMatch) - 10, 0)
        for k, i in parser.lastMatch[start:]:
            lineNumber = parser.s.count(chr(10), 0, i) + 1
            t = k, i, lineNumber
            stderr.write(("Trail: %s %d (line %d)" % t) + chr(10))
        return 1
def target(driver, *args):
    driver.exe_name = "ZADDY".lower() + "c"
    return main, None
class ParseError(Exception): pass



# XXX



def isDigit(c): return 48 <= ord(c) <= 57
def isAlpha(c): return (65 <= ord(c) <= 90) or (97 <= ord(c) <= 122)
class ZADDYParser(object):
    def __init__(self, s):
        self.s = s
        self.lastMatch = []
    def token(self, s, i):
        start = i
        while self.s[start] in (" \n"): start += 1
        stop = start + len(s)
        if self.s[start:stop] != s: raise ParseError()
        self.lastMatch.append(("TOKEN(%s)" % s, i))
        return stop
    def parse(self): return self.parseZADDY(0)
    def parseZADDY(self, i):
        if self.s[i:i + 8] == ".grammar":
            i += 8
            i, rv = self.parseID(i)
            name = rv
            rvs = []
            while True:
                try:
                    i, rv = self.parsePRULE(i)
                    rvs.append(rv)
                except ParseError: break
            rules = rvs
            rv = py.Compound("class " + name + "Parser(object)", [
                py.Statement("def __init__(self, s): self.s = s; self.lastMatch = []; self.cache = {}"),
                py.Statement("def parse(self): return self.parse" + name +
                             "(0)"),
            ] + rules)
            while self.s[i] in (" \n"): i += 1
            return i, rv
        else: raise ParseError()
    def parseNUMBER(self, i):
        start = i
        while self.s[start] in (" \n"): start += 1
        stop = start
        if not isDigit(self.s[stop]): raise ParseError()
        stop += 1
        while isDigit(self.s[stop]): stop += 1
        self.lastMatch.append(("NUMBER", i))
        return stop, int(self.s[start:stop])
    def parseID(self, i):
        start = i
        while self.s[start] in (" \n"): start += 1
        stop = start
        if not isAlpha(self.s[stop]): raise ParseError()
        stop += 1
        while isDigit(self.s[stop]) or isAlpha(self.s[stop]): stop += 1
        self.lastMatch.append(("ID", i))
        return stop, self.s[start:stop]
    def parseSTRING(self, i):
        start = i
        while self.s[start] in (" \n"): start += 1
        if self.s[start] != "'": raise ParseError()
        start += 1
        stop = start
        while self.s[stop] != "'": stop += 1
        self.lastMatch.append(("STRING", i))
        return stop + 1, self.s[start:stop]
    def parsePRULE(self, i):
        k = i
        i, name = self.parseID(i)
        i = self.token(":=", i)
        i, expr = self.parsePEXPR1(i)
        i = self.token(";", i)
        self.lastMatch.append(("PRULE", k))
        return i, py.Compound("def parse" + name + "(self, i)",
              [py.Statement('key = "' + name + '", i'),
               py.Statement('if key in self.cache: raise ParseError()'),
               py.Statement('self.cache[key] = None'),
               py.Statement('st = []; rv = peg.Null()')]
            + expr +
              [py.Statement('self.lastMatch.append(key)'),
               py.Statement('del self.cache[key]'),
               py.Statement('return i, rv')]) ;
    def parsePEXPR1(self, i):
        k = i
        i, rv = self.parsePEXPR2(i)
        while True:
            try:
                i = self.token("/", i)
                i, that = self.parsePEXPR2(i)
                rv = peg.Choice(rv, that)
            except ParseError: break
        self.lastMatch.append(("PEXPR", k))
        return i, rv
    def parsePEXPR2(self, i):
        rvs = []
        while True:
            try:
                i, rv = self.parsePEXPR3(i)
                rvs.append(rv)
            except ParseError: break
        seq = peg.Sequence(rvs)
        try:
            i = self.token("->", i)
            i, prod = self.parsePPROD1(i)
            return i, peg.Production(seq, prod)
        except ParseError: return i, seq
    def parsePEXPR3(self, i):
        i, expr = self.parsePEXPR4(i)
        try:
            i = self.token(":", i)
            i, name = self.parseID(i)
            return i, peg.Capture(expr, name)
        except ParseError: return i, expr
    def parsePEXPR4(self, i):
        k = i
        try:
            i = self.token("!", i)
            i, rv = self.parsePEXPR5(i)
            return i, peg.Negative(rv)
        except ParseError: return self.parsePEXPR5(k)
    def parsePEXPR5(self, i):
        i, rv = self.parsePEXPR6(i)
        if self.s[i] == "*": return i + 1, peg.Any(rv)
        elif self.s[i] == "?": return i + 1, peg.Maybe(rv)
        return i, rv
    def parsePEXPR6(self, i):
        k = i
        try:
            i = self.token("(", i)
            i, rv = self.parsePEXPR1(i)
            i = self.token(")", i)
            return i, rv
        except ParseError:
            i = k
            try:
                i = self.token(".any", i)
                return i, peg.AnyChar()
            except ParseError:
                try:
                    i = self.token(".range(", i)
                    i, l = self.parseNUMBER(i)
                    i = self.token(":", i)
                    i, u = self.parseNUMBER(i)
                    i = self.token(")", i)
                    return i, peg.Range(l, u)
                except ParseError:
                    i = k
                    try:
                        i, c = self.parseNUMBER(i)
                        return i, peg.Char(c)
                    except ParseError:
                        try:
                            i, name = self.parseID(i)
                            return i, peg.Call(name)
                        except ParseError:
                            i, s = self.parseSTRING(i)
                            return i, peg.Token(s)
    def parsePPROD1(self, i):
        k = i
        i, rv = self.parsePPROD2(i)
        while True:
            k = i
            try:
                i = self.token("+", i)
                i, that = self.parsePPROD2(i)
                rv = peg.Plus(rv, that)
            except ParseError:
                i = k
                try:
                    i = self.token("%", i)
                    i, that = self.parsePPROD2(i)
                    rv = peg.Mod(rv, that)
                except ParseError: break
        self.lastMatch.append(("PPROD1", k))
        return i, rv
    def parsePPROD2(self, i):
        try:
            i = self.token("*", i)
            i, rv = self.parsePPROD3(i)
            return i, peg.Flatten(rv)
        except ParseError:
            return self.parsePPROD3(i)
    def parsePPROD3(self, i):
        k = i
        try: return self.token("[]", i), peg.List([])
        except ParseError:
            try:
                i = self.token("(", i)
                i, expr = self.parsePPROD1(i)
                i = self.token(")", i)
                return i, expr
            except ParseError:
                i = k
                try:
                    i = self.token("[", i)
                    i, expr = self.parsePPROD1(i)
                    exprs = [expr]
                    while True:
                        try:
                            i = self.token(",", i)
                            i, expr = self.parsePPROD1(i)
                            exprs.append(expr)
                        except ParseError: break
                    i = self.token("]", i)
                    return i, peg.List(exprs)
                except ParseError:
                    i = k
                    try:
                        i, ty = self.parseID(i)
                        i = self.token(".", i)
                        i, con = self.parseID(i)
                        i = self.token("(", i)
                        i, prod = self.parsePPROD1(i)
                        prods = [prod]
                        while True:
                            try:
                                i = self.token(",", i)
                                i, prod = self.parsePPROD1(i)
                                prods.append(prod)
                            except ParseError: break
                        i = self.token(")", i)
                        return i, peg.Con(ty, con, prods)
                    except ParseError:
                        i = k
                        try:
                            i, ty = self.parseID(i)
                            i = self.token(".", i)
                            i, con = self.parseID(i)
                            return i, peg.Con(ty, con, [])
                        except ParseError:
                            i = k
                            try:
                                i, s = self.parseSTRING(i)
                                return i, peg.String(s)
                            except ParseError:
                                i, s = self.parseID(i)
                                return i, peg.Name(s)
