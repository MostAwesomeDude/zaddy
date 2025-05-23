from rpython.rlib.rfile import create_stdio
from rpython.rlib.unroll import unrolling_iterable
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
        self.lastMatch.append((name, i))
        return i, rv
    deco.__name__ = name
    return deco
@specialize.call_location()
def flatten(xs):
    rv = []
    for x in xs: rv.extend(x)
    return rv
def line(m, s): return " " * (m * 4) + s
class Py(object): pass
class Compound(Py):
    def __init__(self, head, block): self.head = head; self.block = block
    def out(self, buf, m):
        if self.block:
            buf.append(line(m, self.head + ":"))
            for b in self.block: b.out(buf, m + 1)
        else: buf.append(line(m, self.head + ": pass"))
class Conditional(Py):
    def __init__(self, test, block): self.test = test; self.block = block
    def out(self, buf, m):
        if not self.block: return
        buf.append(line(m, "if " + self.test + ":"))
        for b in self.block: b.out(buf, m + 1)
class Handler(Py):
    def __init__(self, block, handler): self.block = block; self.handler = handler
    def out(self, buf, m):
        if not self.block: return
        if self.handler:
            buf.append(line(m, "try:"))
            for b in self.block: b.out(buf, m + 1)
            buf.append(line(m, "except ParseError:"))
            for b in self.handler: b.out(buf, m + 1)
        else:
            for b in self.block: b.out(buf, m)
class Statement(Py):
    def __init__(self, s): self.s = s
    def out(self, buf, m): buf.append(line(m, self.s))
class Builder(object):
    def Compound(self, head, block): return Compound(head, block)
    def Conditional(self, test, block): return Conditional(test, block)
    def Handler(self, block, handler): return Handler(block, handler)
    def Statement(self, line): return Statement(line)
py = Builder()
save = Statement("st.append(i)")
backup = Statement("i = st.pop()")
boundcheck = Statement("if i >= len(self.s): raise ParseError()")
class PEG(object):
    def Con(self, ty, con, prods): return ty + "." + con + "(" + ", ".join(prods) + ")"
    def Plus(self, left, right): return left + " + " + right
    def Mod(self, left, right): return right + ".join(" + left + ")"
    def Flatten(self, l): return "flatten(" + l + ")"
    def Name(self, s): return s
    def String(self, s): return "'" + s + "'"
    def List(self, prods): return "[" + ", ".join(prods) + "]"

    def Null(self): return []
    def AnyChar(self): return [boundcheck, py.Statement("rv = self.s[i]; i += 1")]
    def Char(self, i):
        return [boundcheck, py.Statement("if ord(self.s[i]) != " + str(i) + ": raise ParseError()"),
                py.Statement("rv = self.s[i]; i += 1")]
    def Range(self, l, u):
        return [boundcheck, py.Statement("if not (" + str(l) + " <= ord(self.s[i]) <= " + str(u) + "): raise ParseError()"),
                py.Statement("rv = self.s[i]; i += 1")]
    def Token(self, s):
        return [boundcheck, py.Statement("while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1"),
                boundcheck, py.Statement("if self.s[i:i + %d] != \"%s\": raise ParseError()" % (len(s), s)),
                py.Statement("rv = \"%s\"; i += %d" % (s, len(s)))]
    def Call(self, s): return [py.Statement("i, rv = self.parse" + s + "(i)")]
    def Sequence(self, exprs): return flatten(exprs)
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
    def Maybe(self, expr):
        return [save, py.Handler(expr, [py.Statement("rv = peg.Null()"), backup])]
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
selfSrc = open(__file__, "rb").read().split("\n")[:145]
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
        newlines = [0]
        for line in parser.s.split("\n"):
            newlines.append(newlines[-1] + len(line) + 1)
        for k, i in parser.lastMatch[start:]:
            lineNumber = parser.s.count(chr(10), 0, i)
            t = k, i, lineNumber + 1, i - newlines[lineNumber]
            stderr.write(("Trail: %s %d (line %d, char %d)" % t) + chr(10))
        return 1
def target(driver, *args):
    driver.exe_name = "ZADDY".lower() + "c"
    return main, None
class ParseError(Exception): pass



# XXX



class ZADDYParser(object):
    def __init__(self, s):
        self.s = s; self.lastMatch = []
    def parse(self): return self.parseZADDY(0)
    @cached
    def parseZADDY(self, i):
        st = []
        if i >= len(self.s): raise ParseError()
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError()
        if self.s[i:i + 8] != ".grammar": raise ParseError()
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
        i, rv = self.parseWS(i)
        rv = py.Compound('class ' + name + 'Parser(object)', [py.Compound('def __init__(self, s)', [py.Statement('self.s = s; self.lastMatch = []')]), py.Statement('def parse(self): return self.parse' + name + '(0)')] + flatten(rules))
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
                rv = "attributes"; i += 10
                i, rv = self.parseFIELDS(i)
            except ParseError:
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
        rv = ")"; i += 1
        rv = f + fs
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
                i = st.pop()
            name = rv
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            if self.s[i:i + 1] != "?": raise ParseError()
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
                    i = st.pop()
                name = rv
                if i >= len(self.s): raise ParseError()
                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                if i >= len(self.s): raise ParseError()
                if self.s[i:i + 1] != "*": raise ParseError()
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
                    i = st.pop()
                name = rv
                rv = zephyr.Id(ty, name)
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
        rv = ":="; i += 2
        i, rv = self.parsePEXPR1(i)
        expr = rv
        if i >= len(self.s): raise ParseError()
        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
        if i >= len(self.s): raise ParseError()
        if self.s[i:i + 1] != ";": raise ParseError()
        rv = ";"; i += 1
        rv = [py.Statement('@cached'), py.Compound('def parse' + name + '(self, i)', [py.Statement('st = []')] + expr + [py.Statement('return i, rv')])]
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
            rv = "->"; i += 2
            i, rv = self.parsePPROD1(i)
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
                if self.s[i:i + 1] != "?": raise ParseError()
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
            rv = ".range("; i += 7
            i, rv = self.parseNUMBER(i)
            l = rv
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            if self.s[i:i + 1] != ":": raise ParseError()
            rv = ":"; i += 1
            i, rv = self.parseNUMBER(i)
            u = rv
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            if self.s[i:i + 1] != ")": raise ParseError()
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
                            rv = "("; i += 1
                            i, rv = self.parsePEXPR1(i)
                            expr = rv
                            if i >= len(self.s): raise ParseError()
                            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                            if i >= len(self.s): raise ParseError()
                            if self.s[i:i + 1] != ")": raise ParseError()
                            rv = ")"; i += 1
                            rv = expr
        return i, rv
    @cached
    def parsePPROD1(self, i):
        st = []
        st.append(i)
        try:
            i, rv = self.parsePPROD2(i)
            this = rv
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            if self.s[i:i + 1] != "+": raise ParseError()
            rv = "+"; i += 1
            i, rv = self.parsePPROD1(i)
            that = rv
            rv = peg.Plus(this, that)
        except ParseError:
            i = st.pop()
            st.append(i)
            try:
                i, rv = self.parsePPROD2(i)
                this = rv
                if i >= len(self.s): raise ParseError()
                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                if i >= len(self.s): raise ParseError()
                if self.s[i:i + 1] != "%": raise ParseError()
                rv = "%"; i += 1
                i, rv = self.parsePPROD1(i)
                that = rv
                rv = peg.Mod(this, that)
            except ParseError:
                i = st.pop()
                i, rv = self.parsePPROD2(i)
        return i, rv
    @cached
    def parsePPROD2(self, i):
        st = []
        st.append(i)
        try:
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            if self.s[i:i + 1] != "*": raise ParseError()
            rv = "*"; i += 1
            i, rv = self.parsePPROD3(i)
            prod = rv
            rv = peg.Flatten(prod)
        except ParseError:
            i = st.pop()
            i, rv = self.parsePPROD3(i)
        return i, rv
    @cached
    def parsePPROD3(self, i):
        st = []
        st.append(i)
        try:
            i, rv = self.parseID(i)
            ty = rv
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            if self.s[i:i + 1] != ".": raise ParseError()
            rv = "."; i += 1
            i, rv = self.parseID(i)
            con = rv
            if i >= len(self.s): raise ParseError()
            while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
            if i >= len(self.s): raise ParseError()
            if self.s[i:i + 1] != "(": raise ParseError()
            rv = "("; i += 1
            i, rv = self.parsePPROD1(i)
            prod = rv
            rvs = []
            while True:
                st.append(i)
                try:
                    if i >= len(self.s): raise ParseError()
                    while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                    if i >= len(self.s): raise ParseError()
                    if self.s[i:i + 1] != ",": raise ParseError()
                    rv = ","; i += 1
                    i, rv = self.parsePPROD1(i)
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
            rv = ")"; i += 1
            rv = peg.Con(ty, con, [prod] + prods)
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
                rv = "."; i += 1
                i, rv = self.parseID(i)
                con = rv
                rv = peg.Con(ty, con, [])
            except ParseError:
                i = st.pop()
                st.append(i)
                try:
                    if i >= len(self.s): raise ParseError()
                    while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                    if i >= len(self.s): raise ParseError()
                    if self.s[i:i + 2] != "[]": raise ParseError()
                    rv = "[]"; i += 2
                    rv = peg.List([])
                except ParseError:
                    i = st.pop()
                    st.append(i)
                    try:
                        if i >= len(self.s): raise ParseError()
                        while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                        if i >= len(self.s): raise ParseError()
                        if self.s[i:i + 1] != "[": raise ParseError()
                        rv = "["; i += 1
                        i, rv = self.parsePPROD1(i)
                        expr = rv
                        rvs = []
                        while True:
                            st.append(i)
                            try:
                                if i >= len(self.s): raise ParseError()
                                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                if i >= len(self.s): raise ParseError()
                                if self.s[i:i + 1] != ",": raise ParseError()
                                rv = ","; i += 1
                                i, rv = self.parsePPROD1(i)
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
                        rv = "]"; i += 1
                        rv = peg.List([expr] + exprs)
                    except ParseError:
                        i = st.pop()
                        st.append(i)
                        try:
                            i, rv = self.parseID(i)
                            s = rv
                            rv = peg.Name(s)
                        except ParseError:
                            i = st.pop()
                            st.append(i)
                            try:
                                i, rv = self.parseSTRING(i)
                                s = rv
                                rv = peg.String(s)
                            except ParseError:
                                i = st.pop()
                                if i >= len(self.s): raise ParseError()
                                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                if i >= len(self.s): raise ParseError()
                                if self.s[i:i + 1] != "(": raise ParseError()
                                rv = "("; i += 1
                                i, rv = self.parsePPROD1(i)
                                prod = rv
                                if i >= len(self.s): raise ParseError()
                                while i < len(self.s) and ord(self.s[i]) in [9, 10, 13, 32]: i += 1
                                if i >= len(self.s): raise ParseError()
                                if self.s[i:i + 1] != ")": raise ParseError()
                                rv = ")"; i += 1
                                rv = prod
        return i, rv
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
    def parseALPHA(self, i):
        st = []
        st.append(i)
        try:
            if i >= len(self.s): raise ParseError()
            if not (65 <= ord(self.s[i]) <= 90): raise ParseError()
            rv = self.s[i]; i += 1
        except ParseError:
            i = st.pop()
            if i >= len(self.s): raise ParseError()
            if not (97 <= ord(self.s[i]) <= 122): raise ParseError()
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
                if i >= len(self.s): raise ParseError()
                rv = self.s[i]; i += 1
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
