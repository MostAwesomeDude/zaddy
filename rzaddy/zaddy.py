from rpython.rlib.rfile import create_stdio
class Status(object): pass
class Failed(Status): pass
# i, ms[-1], tb, ob, lb
class Succeeded(Status):
    def __init__(self, t): self.t = t
failed = Failed()
class Py(object):
    m = 0
    def indent(self): self.m += 1
    def dedent(self): self.m -= 1
    def line(self, s): return " " * self.m + s
class Compound(Py):
    def __init__(self, head, block): self.head = head; self.block = block
    def out(self, buf):
        if self.block:
            buf.append(self.line(self.head + ":"))
            self.indent()
            for b in self.block: b.out(buf)
            self.dedent()
        else: buf.append(self.line(self.head + ": pass"))
class Conditional(Py):
    def __init__(self, test, block): self.test = test; self.block = block
    def out(self, buf):
        if not self.block: return
        buf.append(self.line("if " + self.test + ":"))
        self.indent()
        for b in self.block: b.out(buf)
        self.dedent()
class Statement(Py):
    def __init__(self, s): self.s = s
    def out(self, buf): buf.append(self.line(self.s))
class Builder(object):
    def Compound(self, head, block): return Compound(head, block)
    def Conditional(self, test, block): return Conditional(test, block)
    def Statement(self, line): return Statement(line)
py = Builder()
save = Statement("saved.append((i, rv))")
backup = Statement("i, rv = saved[-1]")
commit = Conditional("pf", [Statement("saved.pop()")])
class PEG(object):
    def Con(self, ty, con, prods): return "self." + ty + "." + con + "(" + ", ".join(prods) + ")"
    def Plus(self, left, right): return left + " + " + right
    def Name(self, s): return s
    def String(self, s): return chr(34) + s + chr(34)
    def List(self, prods): return "[" + ", ".join(prods) + "]"
    def Null(self): return []
    def AnyChar(self): return [py.Statement("rv = self.s[i]; i += 1")]
    def Char(self, i): return [py.Statement("if ord(self.s[i]) == " + str(i) + ": rv = self.s[i]; i += 1")]
    def Range(self, l, u): return [py.Statement("if " + str(l) + " <= ord(self.s[i]) <= " + str(u) + ": rv = self.s[i]; i += 1")]
    def Call(self, s): return [py.Statement("st = self.parse" + s + "(i); if st is not failed: i, rv = st.t")]
    def Sequence(self, exprs):
        rv = []
        for expr in reversed(exprs): rv = [py.Conditional("rv", rv)]
        return rv
    def Choice(self, this, that): return [this, py.Conditional("not rv", [that])]
    def Any(self, expr):
        return [py.Statement("pf = True; rvs = []"), py.Compound("while pf", [expr, py.Statement("if rv: rvs.append(rv)"), py.Statement("pf = bool(rv)")])]
    Some = Any
    def Maybe(self, expr): return [save, expr, py.Conditional("not rv", [backup]), commit]
    def Positive(self, expr): return [save, expr, backup]
    Negative = Positive
    def Capture(self, expr, name): return [expr, py.Conditional("rv", [py.Statement(name + " = rv")])]
    def Production(self, expr, prod): return [expr, py.Statement("rv = " + prod)]
def main(argv):
    stdin, stdout, stderr = create_stdio()
    parser = ZADDYParser(stdin.read())
    status = parser.parse()
    if status is failed:
        start = max(len(parser.lastMatch) - 5, 0)
        for k, i in parser.lastMatch[start:]:
            lineNumber = parser.s.count(chr(10), 0, i) + 1
            t = k, i, lineNumber
            stderr.write(("Last successful match:'%s, %d (line %d)'" % t) + chr(10))
        return 1
    else:
        _, _, _, _, lb = status.t
        stdout.write(lb)
        return 0
def target(driver, *args):
    driver.exe_name = "ZADDY".lower() + "c"
    return main, None
class ZADDYParser(object):
    peg = PEG()
    py = py
    def __init__(self, s): self.s = s; self.lastMatch = []; self.cache = {}; self.top()
    def parse(self):
        self.top()
        # i, tf, ms, tb, ob, lb
        return self.parseZADDY(0, False, [0], "", "", "")
    def parseOUT1(self, i, tf, ms, tb, ob, lb):
        k = "OUT1", i, tf, ms[-1], tb, ob, lb
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        pf = True
        saved.append((i, tf, ms[-1], tb, ob, lb))
        while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
        stop = i + 1
        if stop > len(self.s): pf = False
        else: pf = self.s[i:stop] == "*"
        if pf: i = stop
        if pf:
            pass
            ob += 'ob += tb'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
        if not pf:
            i, tf, ms[-1], tb, ob, lb = saved[-1]
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + 1
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == "#"
            if pf: i = stop
            if pf:
                pass
                ob += 'ob += str(len(tb))'
                lb += " " * (ms[-1] * 4) + ob + chr(10)
                ob = ""
        if not pf:
            i, tf, ms[-1], tb, ob, lb = saved[-1]
            rv = self.parseSTRING(i, tf, ms[:], tb, ob, lb)
            pf = rv is not failed
            if pf: i, ms[-1], tb, ob, lb = rv.t
            if pf:
                pass
                ob += 'ob += '
                ob += chr(39)
                ob += tb
                ob += chr(39)
                lb += " " * (ms[-1] * 4) + ob + chr(10)
                ob = ""
        if not pf:
            i, tf, ms[-1], tb, ob, lb = saved[-1]
            rv = self.parseNUMBER(i, tf, ms[:], tb, ob, lb)
            pf = rv is not failed
            if pf: i, ms[-1], tb, ob, lb = rv.t
            if pf:
                pass
                ob += 'ob += chr('
                ob += tb
                ob += ')'
                lb += " " * (ms[-1] * 4) + ob + chr(10)
                ob = ""
        if not pf:
            i, tf, ms[-1], tb, ob, lb = saved[-1]
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + 4
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == ".lm+"
            if pf: i = stop
            if pf:
                pass
                ob += 'ms[-1] += 1'
                lb += " " * (ms[-1] * 4) + ob + chr(10)
                ob = ""
        if not pf:
            i, tf, ms[-1], tb, ob, lb = saved[-1]
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + 4
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == ".lm-"
            if pf: i = stop
            if pf:
                pass
                ob += 'if ms[-1]: ms[-1] -= 1'
                lb += " " * (ms[-1] * 4) + ob + chr(10)
                ob = ""
        if not pf:
            i, tf, ms[-1], tb, ob, lb = saved[-1]
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + 4
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == ".lm?"
            if pf: i = stop
            if pf:
                pass
                ob += 'ms.append(ms[-1])'
                lb += " " * (ms[-1] * 4) + ob + chr(10)
                ob = ""
        if not pf:
            i, tf, ms[-1], tb, ob, lb = saved[-1]
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + 4
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == ".lm!"
            if pf: i = stop
            if pf:
                pass
                ob += 'ms.pop()'
                lb += " " * (ms[-1] * 4) + ob + chr(10)
                ob = ""
        if not pf:
            i, tf, ms[-1], tb, ob, lb = saved[-1]
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + 3
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == ".nl"
            if pf: i = stop
            if pf:
                pass
                ob += 'lb += " " * (ms[-1] * 4) + ob + chr(10)'
                lb += " " * (ms[-1] * 4) + ob + chr(10)
                ob = ""
                ob += 'ob = ""'
                lb += " " * (ms[-1] * 4) + ob + chr(10)
                ob = ""
        saved.pop()
        if pf:
            self.cache[k] = Succeeded((i, ms[-1], tb, ob, lb))
            self.lastMatch.append((k[0], k[1]))
        return self.cache[k]
    def parseOUTPUT(self, i, tf, ms, tb, ob, lb):
        k = "OUTPUT", i, tf, ms[-1], tb, ob, lb
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        pf = True
        saved.append((i, tf, ms[-1], tb, ob, lb))
        while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
        stop = i + 4
        if stop > len(self.s): pf = False
        else: pf = self.s[i:stop] == ".out"
        if pf: i = stop
        if pf:
            pass
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + 1
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == "("
            if pf: i = stop
            if pf:
                pass
                while pf:
                    rv = self.parseOUT1(i, tf, ms[:], tb, ob, lb)
                    pf = rv is not failed
                    if pf: i, ms[-1], tb, ob, lb = rv.t
                pf = True
                if pf:
                    pass
                    while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
                    stop = i + 1
                    if stop > len(self.s): pf = False
                    else: pf = self.s[i:stop] == ")"
                    if pf: i = stop
                    if pf:
                        pass
        saved.pop()
        if pf:
            self.cache[k] = Succeeded((i, ms[-1], tb, ob, lb))
            self.lastMatch.append((k[0], k[1]))
        return self.cache[k]
    def parseCX3(self, i, tf, ms, tb, ob, lb):
        k = "CX3", i, tf, ms[-1], tb, ob, lb
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        pf = True
        saved.append((i, tf, ms[-1], tb, ob, lb))
        rv = self.parseNUMBER(i, tf, ms[:], tb, ob, lb)
        pf = rv is not failed
        if pf: i, ms[-1], tb, ob, lb = rv.t
        if pf:
            pass
        if not pf:
            i, tf, ms[-1], tb, ob, lb = saved[-1]
            rv = self.parseSQUOTE(i, tf, ms[:], tb, ob, lb)
            pf = rv is not failed
            if pf: i, ms[-1], tb, ob, lb = rv.t
            if pf:
                pass
                tb = str(ord(self.s[i]))
                i += 1
                if pf:
                    pass
        saved.pop()
        if pf:
            self.cache[k] = Succeeded((i, ms[-1], tb, ob, lb))
            self.lastMatch.append((k[0], k[1]))
        return self.cache[k]
    def parseCX2(self, i, tf, ms, tb, ob, lb):
        k = "CX2", i, tf, ms[-1], tb, ob, lb
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        pf = True
        saved.append((i, tf, ms[-1], tb, ob, lb))
        rv = self.parseCX3(i, tf, ms[:], tb, ob, lb)
        pf = rv is not failed
        if pf: i, ms[-1], tb, ob, lb = rv.t
        if pf:
            pass
            saved.append((i, tf, ms[-1], tb, ob, lb))
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + 1
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == ":"
            if pf: i = stop
            if pf:
                pass
                ob += tb
                ob += ' <= ord(self.s[i]) <= '
                rv = self.parseCX3(i, tf, ms[:], tb, ob, lb)
                pf = rv is not failed
                if pf: i, ms[-1], tb, ob, lb = rv.t
                if pf:
                    pass
                    ob += tb
            if not pf:
                i, tf, ms[-1], tb, ob, lb = saved[-1]
                pf = True
                if pf:
                    pass
                    ob += 'ord(self.s[i]) == '
                    ob += tb
            saved.pop()
            if pf:
                pass
        saved.pop()
        if pf:
            self.cache[k] = Succeeded((i, ms[-1], tb, ob, lb))
            self.lastMatch.append((k[0], k[1]))
        return self.cache[k]
    def parseCX1(self, i, tf, ms, tb, ob, lb):
        k = "CX1", i, tf, ms[-1], tb, ob, lb
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        pf = True
        saved.append((i, tf, ms[-1], tb, ob, lb))
        ob += 'pf = (i < len(self.s)) and '
        rv = self.parseCX2(i, tf, ms[:], tb, ob, lb)
        pf = rv is not failed
        if pf: i, ms[-1], tb, ob, lb = rv.t
        if pf:
            pass
            while pf:
                saved.append((i, tf, ms[-1], tb, ob, lb))
                while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
                stop = i + 1
                if stop > len(self.s): pf = False
                else: pf = self.s[i:stop] == "!"
                if pf: i = stop
                if pf:
                    pass
                    ob += ' or '
                    rv = self.parseCX2(i, tf, ms[:], tb, ob, lb)
                    pf = rv is not failed
                    if pf: i, ms[-1], tb, ob, lb = rv.t
                    if pf:
                        pass
                saved.pop()
            pf = True
            if pf:
                pass
                lb += " " * (ms[-1] * 4) + ob + chr(10)
                ob = ""
                self.apf = 0
                if pf:
                    pass
        saved.pop()
        if pf:
            self.cache[k] = Succeeded((i, ms[-1], tb, ob, lb))
            self.lastMatch.append((k[0], k[1]))
        return self.cache[k]
    def parseSCAN(self, i, tf, ms, tb, ob, lb):
        k = "SCAN", i, tf, ms[-1], tb, ob, lb
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        pf = True
        saved.append((i, tf, ms[-1], tb, ob, lb))
        if (self.apf == 1):
            pass
            saved.append((i, tf, ms[-1], tb, ob, lb))
            ob += 'if tf: tb += self.s[i]'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
            ob += 'i += 1'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
            saved.pop()
        if pf:
            pass
            if (self.apf == 0):
                pass
                saved.append((i, tf, ms[-1], tb, ob, lb))
                ob += 'if pf:'
                lb += " " * (ms[-1] * 4) + ob + chr(10)
                ob = ""
                ms[-1] += 1
                ob += 'if tf: tb += self.s[i]'
                lb += " " * (ms[-1] * 4) + ob + chr(10)
                ob = ""
                ob += 'i += 1'
                lb += " " * (ms[-1] * 4) + ob + chr(10)
                ob = ""
                if ms[-1]: ms[-1] -= 1
                saved.pop()
            if pf:
                pass
        saved.pop()
        if pf:
            self.cache[k] = Succeeded((i, ms[-1], tb, ob, lb))
            self.lastMatch.append((k[0], k[1]))
        return self.cache[k]
    def parseSUB(self, i, tf, ms, tb, ob, lb):
        k = "SUB", i, tf, ms[-1], tb, ob, lb
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        pf = True
        saved.append((i, tf, ms[-1], tb, ob, lb))
        rv = self.parseID(i, tf, ms[:], tb, ob, lb)
        pf = rv is not failed
        if pf: i, ms[-1], tb, ob, lb = rv.t
        if pf:
            pass
            ob += 'rv = self.parse'
            ob += tb
            ob += '(i, tf, ms[:], tb, ob, lb)'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
            ob += 'pf = rv is not failed'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
            ob += 'if pf: i, ms[-1], tb, ob, lb = rv.t'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
            self.top()
            if pf:
                pass
        saved.pop()
        if pf:
            self.cache[k] = Succeeded((i, ms[-1], tb, ob, lb))
            self.lastMatch.append((k[0], k[1]))
        return self.cache[k]
    def parseSET(self, i, tf, ms, tb, ob, lb):
        k = "SET", i, tf, ms[-1], tb, ob, lb
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        pf = True
        saved.append((i, tf, ms[-1], tb, ob, lb))
        if (not (self.apf == 1)):
            pass
            saved.append((i, tf, ms[-1], tb, ob, lb))
            ob += 'pf = True'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
            saved.pop()
        if pf:
            pass
            self.apf = 1
            if pf:
                pass
        saved.pop()
        if pf:
            self.cache[k] = Succeeded((i, ms[-1], tb, ob, lb))
            self.lastMatch.append((k[0], k[1]))
        return self.cache[k]
    def parseSAVE(self, i, tf, ms, tb, ob, lb):
        k = "SAVE", i, tf, ms[-1], tb, ob, lb
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        pf = True
        saved.append((i, tf, ms[-1], tb, ob, lb))
        ob += 'saved.append((i, tf, ms[-1], tb, ob, lb))'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        saved.pop()
        if pf:
            self.cache[k] = Succeeded((i, ms[-1], tb, ob, lb))
            self.lastMatch.append((k[0], k[1]))
        return self.cache[k]
    def parseBACKUP(self, i, tf, ms, tb, ob, lb):
        k = "BACKUP", i, tf, ms[-1], tb, ob, lb
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        pf = True
        saved.append((i, tf, ms[-1], tb, ob, lb))
        ob += 'i, tf, ms[-1], tb, ob, lb = saved[-1]'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        saved.pop()
        if pf:
            self.cache[k] = Succeeded((i, ms[-1], tb, ob, lb))
            self.lastMatch.append((k[0], k[1]))
        return self.cache[k]
    def parseCOMMIT(self, i, tf, ms, tb, ob, lb):
        k = "COMMIT", i, tf, ms[-1], tb, ob, lb
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        pf = True
        saved.append((i, tf, ms[-1], tb, ob, lb))
        ob += 'saved.pop()'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        saved.pop()
        if pf:
            self.cache[k] = Succeeded((i, ms[-1], tb, ob, lb))
            self.lastMatch.append((k[0], k[1]))
        return self.cache[k]
    def parseTX3(self, i, tf, ms, tb, ob, lb):
        k = "TX3", i, tf, ms[-1], tb, ob, lb
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        pf = True
        saved.append((i, tf, ms[-1], tb, ob, lb))
        saved.append((i, tf, ms[-1], tb, ob, lb))
        while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
        stop = i + 6
        if stop > len(self.s): pf = False
        else: pf = self.s[i:stop] == ".token"
        if pf: i = stop
        if pf:
            pass
            ob += 'tb = ""'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
            ob += 'tf = True'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
        if not pf:
            i, tf, ms[-1], tb, ob, lb = saved[-1]
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + 7
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == ".tokout"
            if pf: i = stop
            if pf:
                pass
                ob += 'tf = False'
                lb += " " * (ms[-1] * 4) + ob + chr(10)
                ob = ""
        if not pf:
            i, tf, ms[-1], tb, ob, lb = saved[-1]
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + 1
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == "$"
            if pf: i = stop
            if pf:
                pass
                rv = self.parseSET(i, tf, ms[:], tb, ob, lb)
                pf = rv is not failed
                if pf: i, ms[-1], tb, ob, lb = rv.t
                if pf:
                    pass
                    ob += 'while pf:'
                    lb += " " * (ms[-1] * 4) + ob + chr(10)
                    ob = ""
                    ms[-1] += 1
                    self.apf = 1
                    if pf:
                        pass
                        rv = self.parseTX3(i, tf, ms[:], tb, ob, lb)
                        pf = rv is not failed
                        if pf: i, ms[-1], tb, ob, lb = rv.t
                        if pf:
                            pass
                            if ms[-1]: ms[-1] -= 1
                            self.apf = 2
                            if pf:
                                pass
        saved.pop()
        if pf:
            pass
            rv = self.parseSET(i, tf, ms[:], tb, ob, lb)
            pf = rv is not failed
            if pf: i, ms[-1], tb, ob, lb = rv.t
            if pf:
                pass
        if not pf:
            i, tf, ms[-1], tb, ob, lb = saved[-1]
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + 6
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == ".empty"
            if pf: i = stop
            if pf:
                pass
                rv = self.parseSET(i, tf, ms[:], tb, ob, lb)
                pf = rv is not failed
                if pf: i, ms[-1], tb, ob, lb = rv.t
                if pf:
                    pass
        if not pf:
            i, tf, ms[-1], tb, ob, lb = saved[-1]
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + 5
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == ".not("
            if pf: i = stop
            if pf:
                pass
                rv = self.parseCX1(i, tf, ms[:], tb, ob, lb)
                pf = rv is not failed
                if pf: i, ms[-1], tb, ob, lb = rv.t
                if pf:
                    pass
                    while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
                    stop = i + 1
                    if stop > len(self.s): pf = False
                    else: pf = self.s[i:stop] == ")"
                    if pf: i = stop
                    if pf:
                        pass
                        ob += 'pf = (i < len(self.s)) and not pf'
                        lb += " " * (ms[-1] * 4) + ob + chr(10)
                        ob = ""
                        self.apf = 0
                        if pf:
                            pass
                            rv = self.parseSCAN(i, tf, ms[:], tb, ob, lb)
                            pf = rv is not failed
                            if pf: i, ms[-1], tb, ob, lb = rv.t
                            if pf:
                                pass
        if not pf:
            i, tf, ms[-1], tb, ob, lb = saved[-1]
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + 5
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == ".any("
            if pf: i = stop
            if pf:
                pass
                rv = self.parseCX1(i, tf, ms[:], tb, ob, lb)
                pf = rv is not failed
                if pf: i, ms[-1], tb, ob, lb = rv.t
                if pf:
                    pass
                    while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
                    stop = i + 1
                    if stop > len(self.s): pf = False
                    else: pf = self.s[i:stop] == ")"
                    if pf: i = stop
                    if pf:
                        pass
                        rv = self.parseSCAN(i, tf, ms[:], tb, ob, lb)
                        pf = rv is not failed
                        if pf: i, ms[-1], tb, ob, lb = rv.t
                        if pf:
                            pass
        if not pf:
            i, tf, ms[-1], tb, ob, lb = saved[-1]
            rv = self.parseSUB(i, tf, ms[:], tb, ob, lb)
            pf = rv is not failed
            if pf: i, ms[-1], tb, ob, lb = rv.t
            if pf:
                pass
        if not pf:
            i, tf, ms[-1], tb, ob, lb = saved[-1]
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + 1
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == "("
            if pf: i = stop
            if pf:
                pass
                rv = self.parseTX1(i, tf, ms[:], tb, ob, lb)
                pf = rv is not failed
                if pf: i, ms[-1], tb, ob, lb = rv.t
                if pf:
                    pass
                    while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
                    stop = i + 1
                    if stop > len(self.s): pf = False
                    else: pf = self.s[i:stop] == ")"
                    if pf: i = stop
                    if pf:
                        pass
        saved.pop()
        if pf:
            self.cache[k] = Succeeded((i, ms[-1], tb, ob, lb))
            self.lastMatch.append((k[0], k[1]))
        return self.cache[k]
    def parseTX2(self, i, tf, ms, tb, ob, lb):
        k = "TX2", i, tf, ms[-1], tb, ob, lb
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        pf = True
        saved.append((i, tf, ms[-1], tb, ob, lb))
        ms.append(ms[-1])
        rv = self.parseTX3(i, tf, ms[:], tb, ob, lb)
        pf = rv is not failed
        if pf: i, ms[-1], tb, ob, lb = rv.t
        if pf:
            pass
            ob += 'if pf:'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
            ms[-1] += 1
            ob += 'pass'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
            self.apf = 1
            if pf:
                pass
                while pf:
                    saved.append((i, tf, ms[-1], tb, ob, lb))
                    rv = self.parseTX3(i, tf, ms[:], tb, ob, lb)
                    pf = rv is not failed
                    if pf: i, ms[-1], tb, ob, lb = rv.t
                    if pf:
                        pass
                        ob += 'if pf:'
                        lb += " " * (ms[-1] * 4) + ob + chr(10)
                        ob = ""
                        ms[-1] += 1
                        ob += 'pass'
                        lb += " " * (ms[-1] * 4) + ob + chr(10)
                        ob = ""
                        self.apf = 1
                        if pf:
                            pass
                    saved.pop()
                pf = True
                if pf:
                    pass
                    ms.pop()
        saved.pop()
        if pf:
            self.cache[k] = Succeeded((i, ms[-1], tb, ob, lb))
            self.lastMatch.append((k[0], k[1]))
        return self.cache[k]
    def parseTX1(self, i, tf, ms, tb, ob, lb):
        k = "TX1", i, tf, ms[-1], tb, ob, lb
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        pf = True
        saved.append((i, tf, ms[-1], tb, ob, lb))
        rv = self.parseSAVE(i, tf, ms[:], tb, ob, lb)
        pf = rv is not failed
        if pf: i, ms[-1], tb, ob, lb = rv.t
        if pf:
            pass
            rv = self.parseTX2(i, tf, ms[:], tb, ob, lb)
            pf = rv is not failed
            if pf: i, ms[-1], tb, ob, lb = rv.t
            if pf:
                pass
                while pf:
                    saved.append((i, tf, ms[-1], tb, ob, lb))
                    while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
                    stop = i + 1
                    if stop > len(self.s): pf = False
                    else: pf = self.s[i:stop] == "/"
                    if pf: i = stop
                    if pf:
                        pass
                        ob += 'if not pf:'
                        lb += " " * (ms[-1] * 4) + ob + chr(10)
                        ob = ""
                        ms[-1] += 1
                        self.apf = 2
                        if pf:
                            pass
                            rv = self.parseBACKUP(i, tf, ms[:], tb, ob, lb)
                            pf = rv is not failed
                            if pf: i, ms[-1], tb, ob, lb = rv.t
                            if pf:
                                pass
                                rv = self.parseTX2(i, tf, ms[:], tb, ob, lb)
                                pf = rv is not failed
                                if pf: i, ms[-1], tb, ob, lb = rv.t
                                if pf:
                                    pass
                                    self.apf = 0
                                    if pf:
                                        pass
                                        if ms[-1]: ms[-1] -= 1
                    saved.pop()
                pf = True
                if pf:
                    pass
                    rv = self.parseCOMMIT(i, tf, ms[:], tb, ob, lb)
                    pf = rv is not failed
                    if pf: i, ms[-1], tb, ob, lb = rv.t
                    if pf:
                        pass
        saved.pop()
        if pf:
            self.cache[k] = Succeeded((i, ms[-1], tb, ob, lb))
            self.lastMatch.append((k[0], k[1]))
        return self.cache[k]
    def parseTR(self, i, tf, ms, tb, ob, lb):
        k = "TR", i, tf, ms[-1], tb, ob, lb
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        pf = True
        saved.append((i, tf, ms[-1], tb, ob, lb))
        rv = self.parseID(i, tf, ms[:], tb, ob, lb)
        pf = rv is not failed
        if pf: i, ms[-1], tb, ob, lb = rv.t
        if pf:
            pass
            ob += 'def parse'
            ob += tb
            ob += '(self, i, tf, ms, tb, ob, lb):'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
            ms[-1] += 1
            ob += 'k = "'
            ob += tb
            ob += '", i, tf, ms[-1], tb, ob, lb'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
            ob += 'if k in self.cache: return self.cache[k]'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
            ob += 'self.cache[k] = failed'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
            ob += 'saved = []'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + 1
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == ":"
            if pf: i = stop
            if pf:
                pass
                self.top()
                if pf:
                    pass
                    rv = self.parseSET(i, tf, ms[:], tb, ob, lb)
                    pf = rv is not failed
                    if pf: i, ms[-1], tb, ob, lb = rv.t
                    if pf:
                        pass
                        rv = self.parseTX1(i, tf, ms[:], tb, ob, lb)
                        pf = rv is not failed
                        if pf: i, ms[-1], tb, ob, lb = rv.t
                        if pf:
                            pass
                            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
                            stop = i + 1
                            if stop > len(self.s): pf = False
                            else: pf = self.s[i:stop] == ";"
                            if pf: i = stop
                            if pf:
                                pass
                                ob += 'if pf:'
                                lb += " " * (ms[-1] * 4) + ob + chr(10)
                                ob = ""
                                ms[-1] += 1
                                ob += 'self.cache[k] = Succeeded((i, ms[-1], tb, ob, lb))'
                                lb += " " * (ms[-1] * 4) + ob + chr(10)
                                ob = ""
                                ob += 'self.lastMatch.append((k[0], k[1]))'
                                lb += " " * (ms[-1] * 4) + ob + chr(10)
                                ob = ""
                                if ms[-1]: ms[-1] -= 1
                                ob += 'return self.cache[k]'
                                lb += " " * (ms[-1] * 4) + ob + chr(10)
                                ob = ""
                                if ms[-1]: ms[-1] -= 1
        saved.pop()
        if pf:
            self.cache[k] = Succeeded((i, ms[-1], tb, ob, lb))
            self.lastMatch.append((k[0], k[1]))
        return self.cache[k]
    def parseTVAR(self, i, tf, ms, tb, ob, lb):
        k = "TVAR", i, tf, ms[-1], tb, ob, lb
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        pf = True
        saved.append((i, tf, ms[-1], tb, ob, lb))
        while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
        stop = i + 1
        if stop > len(self.s): pf = False
        else: pf = self.s[i:stop] == "~"
        if pf: i = stop
        if pf:
            pass
            ob += '(not '
            rv = self.parseTVAR(i, tf, ms[:], tb, ob, lb)
            pf = rv is not failed
            if pf: i, ms[-1], tb, ob, lb = rv.t
            if pf:
                pass
                ob += ')'
        if not pf:
            i, tf, ms[-1], tb, ob, lb = saved[-1]
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + 1
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == "?"
            if pf: i = stop
            if pf:
                pass
                rv = self.parseID(i, tf, ms[:], tb, ob, lb)
                pf = rv is not failed
                if pf: i, ms[-1], tb, ob, lb = rv.t
                if pf:
                    pass
                    ob += '(self.a'
                    ob += tb
                    ob += ' == 0)'
        if not pf:
            i, tf, ms[-1], tb, ob, lb = saved[-1]
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + 1
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == "+"
            if pf: i = stop
            if pf:
                pass
                rv = self.parseID(i, tf, ms[:], tb, ob, lb)
                pf = rv is not failed
                if pf: i, ms[-1], tb, ob, lb = rv.t
                if pf:
                    pass
                    ob += '(self.a'
                    ob += tb
                    ob += ' == 1)'
        if not pf:
            i, tf, ms[-1], tb, ob, lb = saved[-1]
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + 1
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == "-"
            if pf: i = stop
            if pf:
                pass
                rv = self.parseID(i, tf, ms[:], tb, ob, lb)
                pf = rv is not failed
                if pf: i, ms[-1], tb, ob, lb = rv.t
                if pf:
                    pass
                    ob += '(self.a'
                    ob += tb
                    ob += ' == 2)'
        saved.pop()
        if pf:
            self.cache[k] = Succeeded((i, ms[-1], tb, ob, lb))
            self.lastMatch.append((k[0], k[1]))
        return self.cache[k]
    def parseAVAR(self, i, tf, ms, tb, ob, lb):
        k = "AVAR", i, tf, ms[-1], tb, ob, lb
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        pf = True
        saved.append((i, tf, ms[-1], tb, ob, lb))
        while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
        stop = i + 1
        if stop > len(self.s): pf = False
        else: pf = self.s[i:stop] == "?"
        if pf: i = stop
        if pf:
            pass
            rv = self.parseID(i, tf, ms[:], tb, ob, lb)
            pf = rv is not failed
            if pf: i, ms[-1], tb, ob, lb = rv.t
            if pf:
                pass
                ob += 'self.a'
                ob += tb
                ob += ' = 0'
                lb += " " * (ms[-1] * 4) + ob + chr(10)
                ob = ""
        if not pf:
            i, tf, ms[-1], tb, ob, lb = saved[-1]
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + 1
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == "+"
            if pf: i = stop
            if pf:
                pass
                rv = self.parseID(i, tf, ms[:], tb, ob, lb)
                pf = rv is not failed
                if pf: i, ms[-1], tb, ob, lb = rv.t
                if pf:
                    pass
                    ob += 'self.a'
                    ob += tb
                    ob += ' = 1'
                    lb += " " * (ms[-1] * 4) + ob + chr(10)
                    ob = ""
        if not pf:
            i, tf, ms[-1], tb, ob, lb = saved[-1]
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + 1
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == "-"
            if pf: i = stop
            if pf:
                pass
                rv = self.parseID(i, tf, ms[:], tb, ob, lb)
                pf = rv is not failed
                if pf: i, ms[-1], tb, ob, lb = rv.t
                if pf:
                    pass
                    ob += 'self.a'
                    ob += tb
                    ob += ' = 2'
                    lb += " " * (ms[-1] * 4) + ob + chr(10)
                    ob = ""
        saved.pop()
        if pf:
            self.cache[k] = Succeeded((i, ms[-1], tb, ob, lb))
            self.lastMatch.append((k[0], k[1]))
        return self.cache[k]
    def parseEX3(self, i, tf, ms, tb, ob, lb):
        k = "EX3", i, tf, ms[-1], tb, ob, lb
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        pf = True
        saved.append((i, tf, ms[-1], tb, ob, lb))
        rv = self.parseSUB(i, tf, ms[:], tb, ob, lb)
        pf = rv is not failed
        if pf: i, ms[-1], tb, ob, lb = rv.t
        if pf:
            pass
        if not pf:
            i, tf, ms[-1], tb, ob, lb = saved[-1]
            rv = self.parseSTRING(i, tf, ms[:], tb, ob, lb)
            pf = rv is not failed
            if pf: i, ms[-1], tb, ob, lb = rv.t
            if pf:
                pass
                ob += 'while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1'
                lb += " " * (ms[-1] * 4) + ob + chr(10)
                ob = ""
                ob += 'stop = i + '
                ob += str(len(tb))
                lb += " " * (ms[-1] * 4) + ob + chr(10)
                ob = ""
                ob += 'if stop > len(self.s): pf = False'
                lb += " " * (ms[-1] * 4) + ob + chr(10)
                ob = ""
                ob += 'else: pf = self.s[i:stop] == "'
                ob += tb
                ob += '"'
                lb += " " * (ms[-1] * 4) + ob + chr(10)
                ob = ""
                ob += 'if pf: i = stop'
                lb += " " * (ms[-1] * 4) + ob + chr(10)
                ob = ""
                self.apf = 0
                if pf:
                    pass
        if not pf:
            i, tf, ms[-1], tb, ob, lb = saved[-1]
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + 1
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == "("
            if pf: i = stop
            if pf:
                pass
                rv = self.parseEX1(i, tf, ms[:], tb, ob, lb)
                pf = rv is not failed
                if pf: i, ms[-1], tb, ob, lb = rv.t
                if pf:
                    pass
                    while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
                    stop = i + 1
                    if stop > len(self.s): pf = False
                    else: pf = self.s[i:stop] == ")"
                    if pf: i = stop
                    if pf:
                        pass
        if not pf:
            i, tf, ms[-1], tb, ob, lb = saved[-1]
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + 4
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == ".pre"
            if pf: i = stop
            if pf:
                pass
                while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
                stop = i + 1
                if stop > len(self.s): pf = False
                else: pf = self.s[i:stop] == "{"
                if pf: i = stop
                if pf:
                    pass
                    ob += 'if '
                    rv = self.parseTVAR(i, tf, ms[:], tb, ob, lb)
                    pf = rv is not failed
                    if pf: i, ms[-1], tb, ob, lb = rv.t
                    if pf:
                        pass
                        while pf:
                            saved.append((i, tf, ms[-1], tb, ob, lb))
                            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
                            stop = i + 1
                            if stop > len(self.s): pf = False
                            else: pf = self.s[i:stop] == ","
                            if pf: i = stop
                            if pf:
                                pass
                                ob += ' and '
                                rv = self.parseTVAR(i, tf, ms[:], tb, ob, lb)
                                pf = rv is not failed
                                if pf: i, ms[-1], tb, ob, lb = rv.t
                                if pf:
                                    pass
                            saved.pop()
                        pf = True
                        if pf:
                            pass
                            ob += ':'
                            lb += " " * (ms[-1] * 4) + ob + chr(10)
                            ob = ""
                            ms[-1] += 1
                            ob += 'pass'
                            lb += " " * (ms[-1] * 4) + ob + chr(10)
                            ob = ""
                            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
                            stop = i + 1
                            if stop > len(self.s): pf = False
                            else: pf = self.s[i:stop] == "}"
                            if pf: i = stop
                            if pf:
                                pass
                                while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
                                stop = i + 1
                                if stop > len(self.s): pf = False
                                else: pf = self.s[i:stop] == "{"
                                if pf: i = stop
                                if pf:
                                    pass
                                    rv = self.parseEX1(i, tf, ms[:], tb, ob, lb)
                                    pf = rv is not failed
                                    if pf: i, ms[-1], tb, ob, lb = rv.t
                                    if pf:
                                        pass
                                        while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
                                        stop = i + 1
                                        if stop > len(self.s): pf = False
                                        else: pf = self.s[i:stop] == "}"
                                        if pf: i = stop
                                        if pf:
                                            pass
                                            if ms[-1]: ms[-1] -= 1
        if not pf:
            i, tf, ms[-1], tb, ob, lb = saved[-1]
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + 5
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == ".post"
            if pf: i = stop
            if pf:
                pass
                while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
                stop = i + 1
                if stop > len(self.s): pf = False
                else: pf = self.s[i:stop] == "{"
                if pf: i = stop
                if pf:
                    pass
                    rv = self.parseAVAR(i, tf, ms[:], tb, ob, lb)
                    pf = rv is not failed
                    if pf: i, ms[-1], tb, ob, lb = rv.t
                    if pf:
                        pass
                        while pf:
                            saved.append((i, tf, ms[-1], tb, ob, lb))
                            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
                            stop = i + 1
                            if stop > len(self.s): pf = False
                            else: pf = self.s[i:stop] == ","
                            if pf: i = stop
                            if pf:
                                pass
                                rv = self.parseAVAR(i, tf, ms[:], tb, ob, lb)
                                pf = rv is not failed
                                if pf: i, ms[-1], tb, ob, lb = rv.t
                                if pf:
                                    pass
                            saved.pop()
                        pf = True
                        if pf:
                            pass
                            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
                            stop = i + 1
                            if stop > len(self.s): pf = False
                            else: pf = self.s[i:stop] == "}"
                            if pf: i = stop
                            if pf:
                                pass
        if not pf:
            i, tf, ms[-1], tb, ob, lb = saved[-1]
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + 4
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == ".top"
            if pf: i = stop
            if pf:
                pass
                ob += 'self.top()'
                lb += " " * (ms[-1] * 4) + ob + chr(10)
                ob = ""
        if not pf:
            i, tf, ms[-1], tb, ob, lb = saved[-1]
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + 6
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == ".empty"
            if pf: i = stop
            if pf:
                pass
                rv = self.parseSET(i, tf, ms[:], tb, ob, lb)
                pf = rv is not failed
                if pf: i, ms[-1], tb, ob, lb = rv.t
                if pf:
                    pass
        if not pf:
            i, tf, ms[-1], tb, ob, lb = saved[-1]
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + 7
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == ".litchr"
            if pf: i = stop
            if pf:
                pass
                rv = self.parseSET(i, tf, ms[:], tb, ob, lb)
                pf = rv is not failed
                if pf: i, ms[-1], tb, ob, lb = rv.t
                if pf:
                    pass
                    ob += 'tb = str(ord(self.s[i]))'
                    lb += " " * (ms[-1] * 4) + ob + chr(10)
                    ob = ""
                    ob += 'i += 1'
                    lb += " " * (ms[-1] * 4) + ob + chr(10)
                    ob = ""
        if not pf:
            i, tf, ms[-1], tb, ob, lb = saved[-1]
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + 5
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == ".pass"
            if pf: i = stop
            if pf:
                pass
                ob += 'i = 0'
                lb += " " * (ms[-1] * 4) + ob + chr(10)
                ob = ""
        if not pf:
            i, tf, ms[-1], tb, ob, lb = saved[-1]
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + 1
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == "$"
            if pf: i = stop
            if pf:
                pass
                rv = self.parseSET(i, tf, ms[:], tb, ob, lb)
                pf = rv is not failed
                if pf: i, ms[-1], tb, ob, lb = rv.t
                if pf:
                    pass
                    ob += 'while pf:'
                    lb += " " * (ms[-1] * 4) + ob + chr(10)
                    ob = ""
                    ms[-1] += 1
                    self.apf = 1
                    if pf:
                        pass
                        rv = self.parseEX3(i, tf, ms[:], tb, ob, lb)
                        pf = rv is not failed
                        if pf: i, ms[-1], tb, ob, lb = rv.t
                        if pf:
                            pass
                            if ms[-1]: ms[-1] -= 1
                            self.apf = 2
                            if pf:
                                pass
                                rv = self.parseSET(i, tf, ms[:], tb, ob, lb)
                                pf = rv is not failed
                                if pf: i, ms[-1], tb, ob, lb = rv.t
                                if pf:
                                    pass
        saved.pop()
        if pf:
            self.cache[k] = Succeeded((i, ms[-1], tb, ob, lb))
            self.lastMatch.append((k[0], k[1]))
        return self.cache[k]
    def parseEX2(self, i, tf, ms, tb, ob, lb):
        k = "EX2", i, tf, ms[-1], tb, ob, lb
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        pf = True
        saved.append((i, tf, ms[-1], tb, ob, lb))
        ms.append(ms[-1])
        saved.append((i, tf, ms[-1], tb, ob, lb))
        rv = self.parseEX3(i, tf, ms[:], tb, ob, lb)
        pf = rv is not failed
        if pf: i, ms[-1], tb, ob, lb = rv.t
        if pf:
            pass
            ob += 'if pf:'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
            ms[-1] += 1
            ob += 'pass'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
            self.apf = 1
            if pf:
                pass
        if not pf:
            i, tf, ms[-1], tb, ob, lb = saved[-1]
            rv = self.parseOUTPUT(i, tf, ms[:], tb, ob, lb)
            pf = rv is not failed
            if pf: i, ms[-1], tb, ob, lb = rv.t
            if pf:
                pass
        saved.pop()
        if pf:
            pass
            while pf:
                saved.append((i, tf, ms[-1], tb, ob, lb))
                rv = self.parseEX3(i, tf, ms[:], tb, ob, lb)
                pf = rv is not failed
                if pf: i, ms[-1], tb, ob, lb = rv.t
                if pf:
                    pass
                    ob += 'if pf:'
                    lb += " " * (ms[-1] * 4) + ob + chr(10)
                    ob = ""
                    ms[-1] += 1
                    ob += 'pass'
                    lb += " " * (ms[-1] * 4) + ob + chr(10)
                    ob = ""
                    self.apf = 1
                    if pf:
                        pass
                if not pf:
                    i, tf, ms[-1], tb, ob, lb = saved[-1]
                    rv = self.parseOUTPUT(i, tf, ms[:], tb, ob, lb)
                    pf = rv is not failed
                    if pf: i, ms[-1], tb, ob, lb = rv.t
                    if pf:
                        pass
                saved.pop()
            pf = True
            if pf:
                pass
                ms.pop()
                self.apf = 0
                if pf:
                    pass
        saved.pop()
        if pf:
            self.cache[k] = Succeeded((i, ms[-1], tb, ob, lb))
            self.lastMatch.append((k[0], k[1]))
        return self.cache[k]
    def parseEX1(self, i, tf, ms, tb, ob, lb):
        k = "EX1", i, tf, ms[-1], tb, ob, lb
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        pf = True
        saved.append((i, tf, ms[-1], tb, ob, lb))
        rv = self.parseSAVE(i, tf, ms[:], tb, ob, lb)
        pf = rv is not failed
        if pf: i, ms[-1], tb, ob, lb = rv.t
        if pf:
            pass
            rv = self.parseEX2(i, tf, ms[:], tb, ob, lb)
            pf = rv is not failed
            if pf: i, ms[-1], tb, ob, lb = rv.t
            if pf:
                pass
                while pf:
                    saved.append((i, tf, ms[-1], tb, ob, lb))
                    while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
                    stop = i + 1
                    if stop > len(self.s): pf = False
                    else: pf = self.s[i:stop] == "/"
                    if pf: i = stop
                    if pf:
                        pass
                        ob += 'if not pf:'
                        lb += " " * (ms[-1] * 4) + ob + chr(10)
                        ob = ""
                        ms[-1] += 1
                        self.apf = 2
                        if pf:
                            pass
                            rv = self.parseBACKUP(i, tf, ms[:], tb, ob, lb)
                            pf = rv is not failed
                            if pf: i, ms[-1], tb, ob, lb = rv.t
                            if pf:
                                pass
                                rv = self.parseEX2(i, tf, ms[:], tb, ob, lb)
                                pf = rv is not failed
                                if pf: i, ms[-1], tb, ob, lb = rv.t
                                if pf:
                                    pass
                                    self.apf = 0
                                    if pf:
                                        pass
                                        if ms[-1]: ms[-1] -= 1
                    saved.pop()
                pf = True
                if pf:
                    pass
                    rv = self.parseCOMMIT(i, tf, ms[:], tb, ob, lb)
                    pf = rv is not failed
                    if pf: i, ms[-1], tb, ob, lb = rv.t
                    if pf:
                        pass
        saved.pop()
        if pf:
            self.cache[k] = Succeeded((i, ms[-1], tb, ob, lb))
            self.lastMatch.append((k[0], k[1]))
        return self.cache[k]
    def parsePR(self, i, tf, ms, tb, ob, lb):
        k = "PR", i, tf, ms[-1], tb, ob, lb
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        pf = True
        saved.append((i, tf, ms[-1], tb, ob, lb))
        rv = self.parseID(i, tf, ms[:], tb, ob, lb)
        pf = rv is not failed
        if pf: i, ms[-1], tb, ob, lb = rv.t
        if pf:
            pass
            ob += 'def parse'
            ob += tb
            ob += '(self, i, tf, ms, tb, ob, lb):'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
            ms[-1] += 1
            ob += 'k = "'
            ob += tb
            ob += '", i, tf, ms[-1], tb, ob, lb'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
            ob += 'if k in self.cache: return self.cache[k]'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
            ob += 'self.cache[k] = failed'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
            ob += 'saved = []'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + 1
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == "="
            if pf: i = stop
            if pf:
                pass
                self.top()
                if pf:
                    pass
                    rv = self.parseSET(i, tf, ms[:], tb, ob, lb)
                    pf = rv is not failed
                    if pf: i, ms[-1], tb, ob, lb = rv.t
                    if pf:
                        pass
                        rv = self.parseEX1(i, tf, ms[:], tb, ob, lb)
                        pf = rv is not failed
                        if pf: i, ms[-1], tb, ob, lb = rv.t
                        if pf:
                            pass
                            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
                            stop = i + 1
                            if stop > len(self.s): pf = False
                            else: pf = self.s[i:stop] == ";"
                            if pf: i = stop
                            if pf:
                                pass
                                ob += 'if pf:'
                                lb += " " * (ms[-1] * 4) + ob + chr(10)
                                ob = ""
                                ms[-1] += 1
                                ob += 'self.cache[k] = Succeeded((i, ms[-1], tb, ob, lb))'
                                lb += " " * (ms[-1] * 4) + ob + chr(10)
                                ob = ""
                                ob += 'self.lastMatch.append((k[0], k[1]))'
                                lb += " " * (ms[-1] * 4) + ob + chr(10)
                                ob = ""
                                if ms[-1]: ms[-1] -= 1
                                ob += 'return self.cache[k]'
                                lb += " " * (ms[-1] * 4) + ob + chr(10)
                                ob = ""
                                if ms[-1]: ms[-1] -= 1
        saved.pop()
        if pf:
            self.cache[k] = Succeeded((i, ms[-1], tb, ob, lb))
            self.lastMatch.append((k[0], k[1]))
        return self.cache[k]
    def parseTY(self, i, tf, ms, tb, ob, lb):
        k = "TY", i, tf, ms[-1], tb, ob, lb
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        pf = True
        saved.append((i, tf, ms[-1], tb, ob, lb))
        while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
        stop = i + 4
        if stop > len(self.s): pf = False
        else: pf = self.s[i:stop] == "bool"
        if pf: i = stop
        if pf:
            pass
            ob += '0'
        saved.pop()
        if pf:
            self.cache[k] = Succeeded((i, ms[-1], tb, ob, lb))
            self.lastMatch.append((k[0], k[1]))
        return self.cache[k]
    def parseDR(self, i, tf, ms, tb, ob, lb):
        k = "DR", i, tf, ms[-1], tb, ob, lb
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        pf = True
        saved.append((i, tf, ms[-1], tb, ob, lb))
        rv = self.parseID(i, tf, ms[:], tb, ob, lb)
        pf = rv is not failed
        if pf: i, ms[-1], tb, ob, lb = rv.t
        if pf:
            pass
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + 1
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == ":"
            if pf: i = stop
            if pf:
                pass
                ob += 'self.a'
                ob += tb
                ob += ' = '
                rv = self.parseTY(i, tf, ms[:], tb, ob, lb)
                pf = rv is not failed
                if pf: i, ms[-1], tb, ob, lb = rv.t
                if pf:
                    pass
                    while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
                    stop = i + 1
                    if stop > len(self.s): pf = False
                    else: pf = self.s[i:stop] == ";"
                    if pf: i = stop
                    if pf:
                        pass
                        lb += " " * (ms[-1] * 4) + ob + chr(10)
                        ob = ""
        saved.pop()
        if pf:
            self.cache[k] = Succeeded((i, ms[-1], tb, ob, lb))
            self.lastMatch.append((k[0], k[1]))
        return self.cache[k]
    def parsePROLOGUE(self, i, tf, ms, tb, ob, lb):
        k = "PROLOGUE", i, tf, ms[-1], tb, ob, lb
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        pf = True
        saved.append((i, tf, ms[-1], tb, ob, lb))
        ob += 'from rpython.rlib.rfile import create_stdio'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        ob += 'class Status(object): pass'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        ob += 'class Failed(Status): pass'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        ob += '# i, ms[-1], tb, ob, lb'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        ob += 'class Succeeded(Status):'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        ms[-1] += 1
        ob += 'def __init__(self, t): self.t = t'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        if ms[-1]: ms[-1] -= 1
        ob += 'failed = Failed()'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        ob += 'class Py(object):'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        ms[-1] += 1
        ob += 'm = 0'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        ob += 'def indent(self): self.m += 1'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        ob += 'def dedent(self): self.m -= 1'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        ob += 'def line(self, s): return " " * self.m + s'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        if ms[-1]: ms[-1] -= 1
        ob += 'class Compound(Py):'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        ms[-1] += 1
        ob += 'def __init__(self, head, block): self.head = head; self.block = block'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        ob += 'def out(self, buf):'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        ms[-1] += 1
        ob += 'if self.block:'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        ms[-1] += 1
        ob += 'buf.append(self.line(self.head + ":"))'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        ob += 'self.indent()'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        ob += 'for b in self.block: b.out(buf)'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        ob += 'self.dedent()'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        if ms[-1]: ms[-1] -= 1
        ob += 'else: buf.append(self.line(self.head + ": pass"))'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        if ms[-1]: ms[-1] -= 1
        if ms[-1]: ms[-1] -= 1
        ob += 'class Conditional(Py):'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        ms[-1] += 1
        ob += 'def __init__(self, test, block): self.test = test; self.block = block'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        ob += 'def out(self, buf):'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        ms[-1] += 1
        ob += 'if not self.block: return'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        ob += 'buf.append(self.line("if " + self.test + ":"))'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        ob += 'self.indent()'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        ob += 'for b in self.block: b.out(buf)'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        ob += 'self.dedent()'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        if ms[-1]: ms[-1] -= 1
        if ms[-1]: ms[-1] -= 1
        ob += 'class Statement(Py):'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        ms[-1] += 1
        ob += 'def __init__(self, s): self.s = s'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        ob += 'def out(self, buf): buf.append(self.line(self.s))'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        if ms[-1]: ms[-1] -= 1
        ob += 'class Builder(object):'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        ms[-1] += 1
        ob += 'def Compound(self, head, block): return Compound(head, block)'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        ob += 'def Conditional(self, test, block): return Conditional(test, block)'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        ob += 'def Statement(self, line): return Statement(line)'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        if ms[-1]: ms[-1] -= 1
        ob += 'py = Builder()'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        ob += 'save = Statement("saved.append((i, rv))")'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        ob += 'backup = Statement("i, rv = saved[-1]")'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        ob += 'commit = Conditional("pf", [Statement("saved.pop()")])'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        ob += 'class PEG(object):'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        ms[-1] += 1
        ob += 'def Con(self, ty, con, prods): return "self." + ty + "." + con + "(" + ", ".join(prods) + ")"'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        ob += 'def Plus(self, left, right): return left + " + " + right'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        ob += 'def Name(self, s): return s'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        ob += 'def String(self, s): return chr(34) + s + chr(34)'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        ob += 'def List(self, prods): return "[" + ", ".join(prods) + "]"'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        ob += 'def Null(self): return []'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        ob += 'def AnyChar(self): return [py.Statement("rv = self.s[i]; i += 1")]'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        ob += 'def Char(self, i): return [py.Statement("if ord(self.s[i]) == " + str(i) + ": rv = self.s[i]; i += 1")]'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        ob += 'def Range(self, l, u): return [py.Statement("if " + str(l) + " <= ord(self.s[i]) <= " + str(u) + ": rv = self.s[i]; i += 1")]'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        ob += 'def Call(self, s): return [py.Statement("st = self.parse" + s + "(i); if st is not failed: i, rv = st.t")]'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        ob += 'def Sequence(self, exprs):'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        ms[-1] += 1
        ob += 'rv = []'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        ob += 'for expr in reversed(exprs): rv = [py.Conditional("rv", rv)]'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        ob += 'return rv'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        if ms[-1]: ms[-1] -= 1
        ob += 'def Choice(self, this, that): return [this, py.Conditional("not rv", [that])]'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        ob += 'def Any(self, expr):'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        ms[-1] += 1
        ob += 'return [py.Statement("pf = True; rvs = []"), py.Compound("while pf", [expr, py.Statement("if rv: rvs.append(rv)"), py.Statement("pf = bool(rv)")])]'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        if ms[-1]: ms[-1] -= 1
        ob += 'Some = Any'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        ob += 'def Maybe(self, expr): return [save, expr, py.Conditional("not rv", [backup]), commit]'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        ob += 'def Positive(self, expr): return [save, expr, backup]'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        ob += 'Negative = Positive'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        ob += 'def Capture(self, expr, name): return [expr, py.Conditional("rv", [py.Statement(name + " = rv")])]'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        ob += 'def Production(self, expr, prod): return [expr, py.Statement("rv = " + prod)]'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        if ms[-1]: ms[-1] -= 1
        saved.pop()
        if pf:
            self.cache[k] = Succeeded((i, ms[-1], tb, ob, lb))
            self.lastMatch.append((k[0], k[1]))
        return self.cache[k]
    def parseZADDY(self, i, tf, ms, tb, ob, lb):
        k = "ZADDY", i, tf, ms[-1], tb, ob, lb
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        pf = True
        saved.append((i, tf, ms[-1], tb, ob, lb))
        rv = self.parsePROLOGUE(i, tf, ms[:], tb, ob, lb)
        pf = rv is not failed
        if pf: i, ms[-1], tb, ob, lb = rv.t
        if pf:
            pass
            while pf:
                saved.append((i, tf, ms[-1], tb, ob, lb))
                saved.append((i, tf, ms[-1], tb, ob, lb))
                while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
                stop = i + 8
                if stop > len(self.s): pf = False
                else: pf = self.s[i:stop] == ".grammar"
                if pf: i = stop
                if pf:
                    pass
                if not pf:
                    i, tf, ms[-1], tb, ob, lb = saved[-1]
                    while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
                    stop = i + 7
                    if stop > len(self.s): pf = False
                    else: pf = self.s[i:stop] == ".syntax"
                    if pf: i = stop
                    if pf:
                        pass
                saved.pop()
                if pf:
                    pass
                    rv = self.parseID(i, tf, ms[:], tb, ob, lb)
                    pf = rv is not failed
                    if pf: i, ms[-1], tb, ob, lb = rv.t
                    if pf:
                        pass
                        ob += 'def main(argv):'
                        lb += " " * (ms[-1] * 4) + ob + chr(10)
                        ob = ""
                        ms[-1] += 1
                        ob += 'stdin, stdout, stderr = create_stdio()'
                        lb += " " * (ms[-1] * 4) + ob + chr(10)
                        ob = ""
                        ob += 'parser = '
                        ob += tb
                        ob += 'Parser(stdin.read())'
                        lb += " " * (ms[-1] * 4) + ob + chr(10)
                        ob = ""
                        ob += 'status = parser.parse()'
                        lb += " " * (ms[-1] * 4) + ob + chr(10)
                        ob = ""
                        ob += 'if status is failed:'
                        lb += " " * (ms[-1] * 4) + ob + chr(10)
                        ob = ""
                        ms[-1] += 1
                        ob += 'start = max(len(parser.lastMatch) - 5, 0)'
                        lb += " " * (ms[-1] * 4) + ob + chr(10)
                        ob = ""
                        ob += 'for k, i in parser.lastMatch[start:]:'
                        lb += " " * (ms[-1] * 4) + ob + chr(10)
                        ob = ""
                        ms[-1] += 1
                        ob += 'lineNumber = parser.s.count(chr(10), 0, i) + 1'
                        lb += " " * (ms[-1] * 4) + ob + chr(10)
                        ob = ""
                        ob += 't = k, i, lineNumber'
                        lb += " " * (ms[-1] * 4) + ob + chr(10)
                        ob = ""
                        ob += 'stderr.write(("Last successful match:'
                        ob += chr(39)
                        ob += '%s, %d (line %d)'
                        ob += chr(39)
                        ob += '" % t) + chr(10))'
                        lb += " " * (ms[-1] * 4) + ob + chr(10)
                        ob = ""
                        if ms[-1]: ms[-1] -= 1
                        ob += 'return 1'
                        lb += " " * (ms[-1] * 4) + ob + chr(10)
                        ob = ""
                        if ms[-1]: ms[-1] -= 1
                        ob += 'else:'
                        lb += " " * (ms[-1] * 4) + ob + chr(10)
                        ob = ""
                        ms[-1] += 1
                        ob += '_, _, _, _, lb = status.t'
                        lb += " " * (ms[-1] * 4) + ob + chr(10)
                        ob = ""
                        ob += 'stdout.write(lb)'
                        lb += " " * (ms[-1] * 4) + ob + chr(10)
                        ob = ""
                        ob += 'return 0'
                        lb += " " * (ms[-1] * 4) + ob + chr(10)
                        ob = ""
                        if ms[-1]: ms[-1] -= 1
                        if ms[-1]: ms[-1] -= 1
                        ob += 'def target(driver, *args):'
                        lb += " " * (ms[-1] * 4) + ob + chr(10)
                        ob = ""
                        ms[-1] += 1
                        ob += 'driver.exe_name = "'
                        ob += tb
                        ob += '".lower() + "c"'
                        lb += " " * (ms[-1] * 4) + ob + chr(10)
                        ob = ""
                        ob += 'return main, None'
                        lb += " " * (ms[-1] * 4) + ob + chr(10)
                        ob = ""
                        if ms[-1]: ms[-1] -= 1
                        ob += 'class '
                        ob += tb
                        ob += 'Parser(object):'
                        lb += " " * (ms[-1] * 4) + ob + chr(10)
                        ob = ""
                        ms[-1] += 1
                        ob += 'peg = PEG()'
                        lb += " " * (ms[-1] * 4) + ob + chr(10)
                        ob = ""
                        ob += 'py = py'
                        lb += " " * (ms[-1] * 4) + ob + chr(10)
                        ob = ""
                        ob += 'def __init__(self, s): self.s = s; self.lastMatch = []; self.cache = {}; self.top()'
                        lb += " " * (ms[-1] * 4) + ob + chr(10)
                        ob = ""
                        ob += 'def parse(self):'
                        lb += " " * (ms[-1] * 4) + ob + chr(10)
                        ob = ""
                        ms[-1] += 1
                        ob += 'self.top()'
                        lb += " " * (ms[-1] * 4) + ob + chr(10)
                        ob = ""
                        ob += '# i, tf, ms, tb, ob, lb'
                        lb += " " * (ms[-1] * 4) + ob + chr(10)
                        ob = ""
                        ob += 'return self.parse'
                        ob += tb
                        ob += '(0, False, [0], "", "", "")'
                        lb += " " * (ms[-1] * 4) + ob + chr(10)
                        ob = ""
                        if ms[-1]: ms[-1] -= 1
                        while pf:
                            saved.append((i, tf, ms[-1], tb, ob, lb))
                            rv = self.parsePRULE(i, tf, ms[:], tb, ob, lb)
                            pf = rv is not failed
                            if pf: i, ms[-1], tb, ob, lb = rv.t
                            if pf:
                                pass
                            if not pf:
                                i, tf, ms[-1], tb, ob, lb = saved[-1]
                                rv = self.parsePR(i, tf, ms[:], tb, ob, lb)
                                pf = rv is not failed
                                if pf: i, ms[-1], tb, ob, lb = rv.t
                                if pf:
                                    pass
                            saved.pop()
                        pf = True
                        if pf:
                            pass
                            saved.append((i, tf, ms[-1], tb, ob, lb))
                            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
                            stop = i + 7
                            if stop > len(self.s): pf = False
                            else: pf = self.s[i:stop] == ".tokens"
                            if pf: i = stop
                            if pf:
                                pass
                                while pf:
                                    rv = self.parseTR(i, tf, ms[:], tb, ob, lb)
                                    pf = rv is not failed
                                    if pf: i, ms[-1], tb, ob, lb = rv.t
                                pf = True
                                if pf:
                                    pass
                            if not pf:
                                i, tf, ms[-1], tb, ob, lb = saved[-1]
                                pf = True
                                if pf:
                                    pass
                            saved.pop()
                            if pf:
                                pass
                                ob += 'def top(self):'
                                lb += " " * (ms[-1] * 4) + ob + chr(10)
                                ob = ""
                                ms[-1] += 1
                                ob += 'pass'
                                lb += " " * (ms[-1] * 4) + ob + chr(10)
                                ob = ""
                                saved.append((i, tf, ms[-1], tb, ob, lb))
                                while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
                                stop = i + 7
                                if stop > len(self.s): pf = False
                                else: pf = self.s[i:stop] == ".domain"
                                if pf: i = stop
                                if pf:
                                    pass
                                    while pf:
                                        rv = self.parseDR(i, tf, ms[:], tb, ob, lb)
                                        pf = rv is not failed
                                        if pf: i, ms[-1], tb, ob, lb = rv.t
                                    pf = True
                                    if pf:
                                        pass
                                if not pf:
                                    i, tf, ms[-1], tb, ob, lb = saved[-1]
                                    pf = True
                                    if pf:
                                        pass
                                saved.pop()
                                if pf:
                                    pass
                                    if ms[-1]: ms[-1] -= 1
                                    if ms[-1]: ms[-1] -= 1
                saved.pop()
            pf = True
            if pf:
                pass
                while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
                stop = i + 4
                if stop > len(self.s): pf = False
                else: pf = self.s[i:stop] == ".end"
                if pf: i = stop
                if pf:
                    pass
        saved.pop()
        if pf:
            self.cache[k] = Succeeded((i, ms[-1], tb, ob, lb))
            self.lastMatch.append((k[0], k[1]))
        return self.cache[k]
    def parseZSAVE(self, i, tf, ms, tb, ob, lb):
        k = "ZSAVE", i, tf, ms[-1], tb, ob, lb
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        pf = True
        saved.append((i, tf, ms[-1], tb, ob, lb))
        ob += 'saved.append((i, rv))'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        saved.pop()
        if pf:
            self.cache[k] = Succeeded((i, ms[-1], tb, ob, lb))
            self.lastMatch.append((k[0], k[1]))
        return self.cache[k]
    def parseZBACKUP(self, i, tf, ms, tb, ob, lb):
        k = "ZBACKUP", i, tf, ms[-1], tb, ob, lb
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        pf = True
        saved.append((i, tf, ms[-1], tb, ob, lb))
        ob += 'i, rv = saved[-1]'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        saved.pop()
        if pf:
            self.cache[k] = Succeeded((i, ms[-1], tb, ob, lb))
            self.lastMatch.append((k[0], k[1]))
        return self.cache[k]
    def parseZCOMMIT(self, i, tf, ms, tb, ob, lb):
        k = "ZCOMMIT", i, tf, ms[-1], tb, ob, lb
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        pf = True
        saved.append((i, tf, ms[-1], tb, ob, lb))
        ob += 'if pf: saved.pop()'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        saved.pop()
        if pf:
            self.cache[k] = Succeeded((i, ms[-1], tb, ob, lb))
            self.lastMatch.append((k[0], k[1]))
        return self.cache[k]
    def parsePRULE(self, i, tf, ms, tb, ob, lb):
        k = "PRULE", i, tf, ms[-1], tb, ob, lb
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        pf = True
        saved.append((i, tf, ms[-1], tb, ob, lb))
        rv = self.parseID(i, tf, ms[:], tb, ob, lb)
        pf = rv is not failed
        if pf: i, ms[-1], tb, ob, lb = rv.t
        if pf:
            pass
            ob += 'def parse'
            ob += tb
            ob += '(self, i):'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
            ms[-1] += 1
            ob += 'k = "'
            ob += tb
            ob += '", i'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
            ob += 'if k in self.cache: return self.cache[k]'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
            ob += 'self.cache[k] = failed'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
            ob += 'saved = []'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
            saved.append((i, tf, ms[-1], tb, ob, lb))
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + 4
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == ":str"
            if pf: i = stop
            if pf:
                pass
                ob += 'rv = ""'
                lb += " " * (ms[-1] * 4) + ob + chr(10)
                ob = ""
            if not pf:
                i, tf, ms[-1], tb, ob, lb = saved[-1]
                pf = True
                if pf:
                    pass
                    ob += 'rv = self.peg.Null()'
                    lb += " " * (ms[-1] * 4) + ob + chr(10)
                    ob = ""
            saved.pop()
            if pf:
                pass
                while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
                stop = i + 2
                if stop > len(self.s): pf = False
                else: pf = self.s[i:stop] == ":="
                if pf: i = stop
                if pf:
                    pass
                    rv = self.parsePEXPR1(i, tf, ms[:], tb, ob, lb)
                    pf = rv is not failed
                    if pf: i, ms[-1], tb, ob, lb = rv.t
                    if pf:
                        pass
                        while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
                        stop = i + 1
                        if stop > len(self.s): pf = False
                        else: pf = self.s[i:stop] == ";"
                        if pf: i = stop
                        if pf:
                            pass
                            ob += 'if rv:'
                            lb += " " * (ms[-1] * 4) + ob + chr(10)
                            ob = ""
                            ms[-1] += 1
                            ob += 'self.cache[k] = Succeeded((i, rv))'
                            lb += " " * (ms[-1] * 4) + ob + chr(10)
                            ob = ""
                            ob += 'self.lastMatch.append(k)'
                            lb += " " * (ms[-1] * 4) + ob + chr(10)
                            ob = ""
                            if ms[-1]: ms[-1] -= 1
                            ob += 'return self.cache[k]'
                            lb += " " * (ms[-1] * 4) + ob + chr(10)
                            ob = ""
                            if ms[-1]: ms[-1] -= 1
        saved.pop()
        if pf:
            self.cache[k] = Succeeded((i, ms[-1], tb, ob, lb))
            self.lastMatch.append((k[0], k[1]))
        return self.cache[k]
    def parsePEXPR1(self, i, tf, ms, tb, ob, lb):
        k = "PEXPR1", i, tf, ms[-1], tb, ob, lb
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        pf = True
        saved.append((i, tf, ms[-1], tb, ob, lb))
        rv = self.parseZSAVE(i, tf, ms[:], tb, ob, lb)
        pf = rv is not failed
        if pf: i, ms[-1], tb, ob, lb = rv.t
        if pf:
            pass
            rv = self.parsePEXPR2(i, tf, ms[:], tb, ob, lb)
            pf = rv is not failed
            if pf: i, ms[-1], tb, ob, lb = rv.t
            if pf:
                pass
                while pf:
                    saved.append((i, tf, ms[-1], tb, ob, lb))
                    while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
                    stop = i + 1
                    if stop > len(self.s): pf = False
                    else: pf = self.s[i:stop] == "/"
                    if pf: i = stop
                    if pf:
                        pass
                        ob += 'if not rv:'
                        lb += " " * (ms[-1] * 4) + ob + chr(10)
                        ob = ""
                        ms[-1] += 1
                        rv = self.parseZBACKUP(i, tf, ms[:], tb, ob, lb)
                        pf = rv is not failed
                        if pf: i, ms[-1], tb, ob, lb = rv.t
                        if pf:
                            pass
                            rv = self.parsePEXPR2(i, tf, ms[:], tb, ob, lb)
                            pf = rv is not failed
                            if pf: i, ms[-1], tb, ob, lb = rv.t
                            if pf:
                                pass
                                rv = self.parseZCOMMIT(i, tf, ms[:], tb, ob, lb)
                                pf = rv is not failed
                                if pf: i, ms[-1], tb, ob, lb = rv.t
                                if pf:
                                    pass
                                    if ms[-1]: ms[-1] -= 1
                    saved.pop()
                pf = True
                if pf:
                    pass
        saved.pop()
        if pf:
            self.cache[k] = Succeeded((i, ms[-1], tb, ob, lb))
            self.lastMatch.append((k[0], k[1]))
        return self.cache[k]
    def parsePEXPR2(self, i, tf, ms, tb, ob, lb):
        k = "PEXPR2", i, tf, ms[-1], tb, ob, lb
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        pf = True
        saved.append((i, tf, ms[-1], tb, ob, lb))
        ms.append(ms[-1])
        while pf:
            saved.append((i, tf, ms[-1], tb, ob, lb))
            ob += 'if rv:'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
            ms[-1] += 1
            ob += 'pass'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
            rv = self.parsePEXPR3(i, tf, ms[:], tb, ob, lb)
            pf = rv is not failed
            if pf: i, ms[-1], tb, ob, lb = rv.t
            if pf:
                pass
                saved.append((i, tf, ms[-1], tb, ob, lb))
                while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
                stop = i + 1
                if stop > len(self.s): pf = False
                else: pf = self.s[i:stop] == ":"
                if pf: i = stop
                if pf:
                    pass
                    rv = self.parseID(i, tf, ms[:], tb, ob, lb)
                    pf = rv is not failed
                    if pf: i, ms[-1], tb, ob, lb = rv.t
                    if pf:
                        pass
                        ob += tb
                        ob += ' = rv'
                        lb += " " * (ms[-1] * 4) + ob + chr(10)
                        ob = ""
                if not pf:
                    i, tf, ms[-1], tb, ob, lb = saved[-1]
                    pf = True
                    if pf:
                        pass
                saved.pop()
                if pf:
                    pass
            saved.pop()
        pf = True
        if pf:
            pass
            saved.append((i, tf, ms[-1], tb, ob, lb))
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + 2
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == "->"
            if pf: i = stop
            if pf:
                pass
                ob += 'rv = '
                rv = self.parsePPROD1(i, tf, ms[:], tb, ob, lb)
                pf = rv is not failed
                if pf: i, ms[-1], tb, ob, lb = rv.t
                if pf:
                    pass
                    lb += " " * (ms[-1] * 4) + ob + chr(10)
                    ob = ""
            if not pf:
                i, tf, ms[-1], tb, ob, lb = saved[-1]
                pf = True
                if pf:
                    pass
            saved.pop()
            if pf:
                pass
                ms.pop()
        saved.pop()
        if pf:
            self.cache[k] = Succeeded((i, ms[-1], tb, ob, lb))
            self.lastMatch.append((k[0], k[1]))
        return self.cache[k]
    def parsePPROD1(self, i, tf, ms, tb, ob, lb):
        k = "PPROD1", i, tf, ms[-1], tb, ob, lb
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        pf = True
        saved.append((i, tf, ms[-1], tb, ob, lb))
        rv = self.parsePPROD2(i, tf, ms[:], tb, ob, lb)
        pf = rv is not failed
        if pf: i, ms[-1], tb, ob, lb = rv.t
        if pf:
            pass
            while pf:
                saved.append((i, tf, ms[-1], tb, ob, lb))
                while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
                stop = i + 1
                if stop > len(self.s): pf = False
                else: pf = self.s[i:stop] == "+"
                if pf: i = stop
                if pf:
                    pass
                    ob += ' + '
                    rv = self.parsePPROD1(i, tf, ms[:], tb, ob, lb)
                    pf = rv is not failed
                    if pf: i, ms[-1], tb, ob, lb = rv.t
                    if pf:
                        pass
                saved.pop()
            pf = True
            if pf:
                pass
        saved.pop()
        if pf:
            self.cache[k] = Succeeded((i, ms[-1], tb, ob, lb))
            self.lastMatch.append((k[0], k[1]))
        return self.cache[k]
    def parsePPROD2(self, i, tf, ms, tb, ob, lb):
        k = "PPROD2", i, tf, ms[-1], tb, ob, lb
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        pf = True
        saved.append((i, tf, ms[-1], tb, ob, lb))
        while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
        stop = i + 2
        if stop > len(self.s): pf = False
        else: pf = self.s[i:stop] == "[]"
        if pf: i = stop
        if pf:
            pass
            ob += '[]'
        if not pf:
            i, tf, ms[-1], tb, ob, lb = saved[-1]
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + 1
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == "["
            if pf: i = stop
            if pf:
                pass
                ob += '['
                rv = self.parsePPROD1(i, tf, ms[:], tb, ob, lb)
                pf = rv is not failed
                if pf: i, ms[-1], tb, ob, lb = rv.t
                if pf:
                    pass
                    while pf:
                        saved.append((i, tf, ms[-1], tb, ob, lb))
                        while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
                        stop = i + 1
                        if stop > len(self.s): pf = False
                        else: pf = self.s[i:stop] == ","
                        if pf: i = stop
                        if pf:
                            pass
                            ob += ', '
                            rv = self.parsePPROD1(i, tf, ms[:], tb, ob, lb)
                            pf = rv is not failed
                            if pf: i, ms[-1], tb, ob, lb = rv.t
                            if pf:
                                pass
                        saved.pop()
                    pf = True
                    if pf:
                        pass
                        while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
                        stop = i + 1
                        if stop > len(self.s): pf = False
                        else: pf = self.s[i:stop] == "]"
                        if pf: i = stop
                        if pf:
                            pass
                            ob += ']'
        if not pf:
            i, tf, ms[-1], tb, ob, lb = saved[-1]
            rv = self.parseSTRING(i, tf, ms[:], tb, ob, lb)
            pf = rv is not failed
            if pf: i, ms[-1], tb, ob, lb = rv.t
            if pf:
                pass
                ob += '"'
                ob += tb
                ob += '"'
        if not pf:
            i, tf, ms[-1], tb, ob, lb = saved[-1]
            rv = self.parseID(i, tf, ms[:], tb, ob, lb)
            pf = rv is not failed
            if pf: i, ms[-1], tb, ob, lb = rv.t
            if pf:
                pass
                while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
                stop = i + 1
                if stop > len(self.s): pf = False
                else: pf = self.s[i:stop] == "."
                if pf: i = stop
                if pf:
                    pass
                    ob += 'self.'
                    ob += tb
                    ob += '.'
                    rv = self.parseID(i, tf, ms[:], tb, ob, lb)
                    pf = rv is not failed
                    if pf: i, ms[-1], tb, ob, lb = rv.t
                    if pf:
                        pass
                        ob += tb
                        saved.append((i, tf, ms[-1], tb, ob, lb))
                        while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
                        stop = i + 1
                        if stop > len(self.s): pf = False
                        else: pf = self.s[i:stop] == "("
                        if pf: i = stop
                        if pf:
                            pass
                            ob += '('
                            rv = self.parsePPROD1(i, tf, ms[:], tb, ob, lb)
                            pf = rv is not failed
                            if pf: i, ms[-1], tb, ob, lb = rv.t
                            if pf:
                                pass
                                while pf:
                                    saved.append((i, tf, ms[-1], tb, ob, lb))
                                    while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
                                    stop = i + 1
                                    if stop > len(self.s): pf = False
                                    else: pf = self.s[i:stop] == ","
                                    if pf: i = stop
                                    if pf:
                                        pass
                                        ob += ', '
                                        rv = self.parsePPROD1(i, tf, ms[:], tb, ob, lb)
                                        pf = rv is not failed
                                        if pf: i, ms[-1], tb, ob, lb = rv.t
                                        if pf:
                                            pass
                                    saved.pop()
                                pf = True
                                if pf:
                                    pass
                                    while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
                                    stop = i + 1
                                    if stop > len(self.s): pf = False
                                    else: pf = self.s[i:stop] == ")"
                                    if pf: i = stop
                                    if pf:
                                        pass
                                        ob += ')'
                        if not pf:
                            i, tf, ms[-1], tb, ob, lb = saved[-1]
                            pf = True
                            if pf:
                                pass
                                ob += '()'
                        saved.pop()
                        if pf:
                            pass
        if not pf:
            i, tf, ms[-1], tb, ob, lb = saved[-1]
            rv = self.parseID(i, tf, ms[:], tb, ob, lb)
            pf = rv is not failed
            if pf: i, ms[-1], tb, ob, lb = rv.t
            if pf:
                pass
                ob += tb
        saved.pop()
        if pf:
            self.cache[k] = Succeeded((i, ms[-1], tb, ob, lb))
            self.lastMatch.append((k[0], k[1]))
        return self.cache[k]
    def parsePEXPR3(self, i, tf, ms, tb, ob, lb):
        k = "PEXPR3", i, tf, ms[-1], tb, ob, lb
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        pf = True
        saved.append((i, tf, ms[-1], tb, ob, lb))
        while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
        stop = i + 1
        if stop > len(self.s): pf = False
        else: pf = self.s[i:stop] == "&"
        if pf: i = stop
        if pf:
            pass
            rv = self.parseZSAVE(i, tf, ms[:], tb, ob, lb)
            pf = rv is not failed
            if pf: i, ms[-1], tb, ob, lb = rv.t
            if pf:
                pass
                rv = self.parsePEXPR4(i, tf, ms[:], tb, ob, lb)
                pf = rv is not failed
                if pf: i, ms[-1], tb, ob, lb = rv.t
                if pf:
                    pass
                    rv = self.parseZBACKUP(i, tf, ms[:], tb, ob, lb)
                    pf = rv is not failed
                    if pf: i, ms[-1], tb, ob, lb = rv.t
                    if pf:
                        pass
        if not pf:
            i, tf, ms[-1], tb, ob, lb = saved[-1]
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + 1
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == "!"
            if pf: i = stop
            if pf:
                pass
                rv = self.parseZSAVE(i, tf, ms[:], tb, ob, lb)
                pf = rv is not failed
                if pf: i, ms[-1], tb, ob, lb = rv.t
                if pf:
                    pass
                    rv = self.parsePEXPR4(i, tf, ms[:], tb, ob, lb)
                    pf = rv is not failed
                    if pf: i, ms[-1], tb, ob, lb = rv.t
                    if pf:
                        pass
                        rv = self.parseZBACKUP(i, tf, ms[:], tb, ob, lb)
                        pf = rv is not failed
                        if pf: i, ms[-1], tb, ob, lb = rv.t
                        if pf:
                            pass
        if not pf:
            i, tf, ms[-1], tb, ob, lb = saved[-1]
            rv = self.parsePEXPR4(i, tf, ms[:], tb, ob, lb)
            pf = rv is not failed
            if pf: i, ms[-1], tb, ob, lb = rv.t
            if pf:
                pass
        saved.pop()
        if pf:
            self.cache[k] = Succeeded((i, ms[-1], tb, ob, lb))
            self.lastMatch.append((k[0], k[1]))
        return self.cache[k]
    def parsePEXPR4(self, i, tf, ms, tb, ob, lb):
        k = "PEXPR4", i, tf, ms[-1], tb, ob, lb
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        pf = True
        saved.append((i, tf, ms[-1], tb, ob, lb))
        ob += 'pf = first = True'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        ob += 'rvs = []'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        ob += 'while pf:'
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        ms[-1] += 1
        rv = self.parsePEXPR5(i, tf, ms[:], tb, ob, lb)
        pf = rv is not failed
        if pf: i, ms[-1], tb, ob, lb = rv.t
        if pf:
            pass
            ob += 'if rv: rvs.append(rv)'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
            ob += 'pf = bool(rv)'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
            saved.append((i, tf, ms[-1], tb, ob, lb))
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + 1
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == "+"
            if pf: i = stop
            if pf:
                pass
                ob += 'pf = pf or not first'
                lb += " " * (ms[-1] * 4) + ob + chr(10)
                ob = ""
            if not pf:
                i, tf, ms[-1], tb, ob, lb = saved[-1]
                while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
                stop = i + 1
                if stop > len(self.s): pf = False
                else: pf = self.s[i:stop] == "*"
                if pf: i = stop
                if pf:
                    pass
            saved.pop()
            if pf:
                pass
                ob += 'first = False'
                lb += " " * (ms[-1] * 4) + ob + chr(10)
                ob = ""
                if ms[-1]: ms[-1] -= 1
        if not pf:
            i, tf, ms[-1], tb, ob, lb = saved[-1]
            rv = self.parseZSAVE(i, tf, ms[:], tb, ob, lb)
            pf = rv is not failed
            if pf: i, ms[-1], tb, ob, lb = rv.t
            if pf:
                pass
                rv = self.parsePEXPR5(i, tf, ms[:], tb, ob, lb)
                pf = rv is not failed
                if pf: i, ms[-1], tb, ob, lb = rv.t
                if pf:
                    pass
                    while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
                    stop = i + 1
                    if stop > len(self.s): pf = False
                    else: pf = self.s[i:stop] == "?"
                    if pf: i = stop
                    if pf:
                        pass
                        ob += 'if not rv:'
                        lb += " " * (ms[-1] * 4) + ob + chr(10)
                        ob = ""
                        ms[-1] += 1
                        rv = self.parseZBACKUP(i, tf, ms[:], tb, ob, lb)
                        pf = rv is not failed
                        if pf: i, ms[-1], tb, ob, lb = rv.t
                        if pf:
                            pass
                            if ms[-1]: ms[-1] -= 1
                            rv = self.parseZCOMMIT(i, tf, ms[:], tb, ob, lb)
                            pf = rv is not failed
                            if pf: i, ms[-1], tb, ob, lb = rv.t
                            if pf:
                                pass
        if not pf:
            i, tf, ms[-1], tb, ob, lb = saved[-1]
            rv = self.parsePEXPR5(i, tf, ms[:], tb, ob, lb)
            pf = rv is not failed
            if pf: i, ms[-1], tb, ob, lb = rv.t
            if pf:
                pass
        saved.pop()
        if pf:
            self.cache[k] = Succeeded((i, ms[-1], tb, ob, lb))
            self.lastMatch.append((k[0], k[1]))
        return self.cache[k]
    def parsePEXPR5(self, i, tf, ms, tb, ob, lb):
        k = "PEXPR5", i, tf, ms[-1], tb, ob, lb
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        pf = True
        saved.append((i, tf, ms[-1], tb, ob, lb))
        while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
        stop = i + 7
        if stop > len(self.s): pf = False
        else: pf = self.s[i:stop] == ".range("
        if pf: i = stop
        if pf:
            pass
            rv = self.parseNUMBER(i, tf, ms[:], tb, ob, lb)
            pf = rv is not failed
            if pf: i, ms[-1], tb, ob, lb = rv.t
            if pf:
                pass
                ob += 'if '
                ob += tb
                ob += ' <= ord(self.s[i]) <= '
                while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
                stop = i + 1
                if stop > len(self.s): pf = False
                else: pf = self.s[i:stop] == ":"
                if pf: i = stop
                if pf:
                    pass
                    rv = self.parseNUMBER(i, tf, ms[:], tb, ob, lb)
                    pf = rv is not failed
                    if pf: i, ms[-1], tb, ob, lb = rv.t
                    if pf:
                        pass
                        while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
                        stop = i + 1
                        if stop > len(self.s): pf = False
                        else: pf = self.s[i:stop] == ")"
                        if pf: i = stop
                        if pf:
                            pass
                            ob += tb
                            ob += ': rv = self.s[i]; i += 1'
                            lb += " " * (ms[-1] * 4) + ob + chr(10)
                            ob = ""
        if not pf:
            i, tf, ms[-1], tb, ob, lb = saved[-1]
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + 4
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == ".any"
            if pf: i = stop
            if pf:
                pass
                ob += 'rv = self.s[i]; i += 1'
                lb += " " * (ms[-1] * 4) + ob + chr(10)
                ob = ""
        if not pf:
            i, tf, ms[-1], tb, ob, lb = saved[-1]
            rv = self.parseNUMBER(i, tf, ms[:], tb, ob, lb)
            pf = rv is not failed
            if pf: i, ms[-1], tb, ob, lb = rv.t
            if pf:
                pass
                ob += 'if ord(self.s[i]) == '
                ob += tb
                ob += ': rv = chr('
                ob += tb
                ob += '); i += 1'
                lb += " " * (ms[-1] * 4) + ob + chr(10)
                ob = ""
        if not pf:
            i, tf, ms[-1], tb, ob, lb = saved[-1]
            rv = self.parseID(i, tf, ms[:], tb, ob, lb)
            pf = rv is not failed
            if pf: i, ms[-1], tb, ob, lb = rv.t
            if pf:
                pass
                ob += 'st = self.parse'
                ob += tb
                ob += '(i)'
                lb += " " * (ms[-1] * 4) + ob + chr(10)
                ob = ""
                ob += 'if st is not failed: i, rv = st.t'
                lb += " " * (ms[-1] * 4) + ob + chr(10)
                ob = ""
        if not pf:
            i, tf, ms[-1], tb, ob, lb = saved[-1]
            rv = self.parseSTRING(i, tf, ms[:], tb, ob, lb)
            pf = rv is not failed
            if pf: i, ms[-1], tb, ob, lb = rv.t
            if pf:
                pass
                ob += 'l = '
                ob += str(len(tb))
                lb += " " * (ms[-1] * 4) + ob + chr(10)
                ob = ""
                ob += 'if self.s[i:i + l] == "'
                ob += tb
                ob += '": rv = "'
                ob += tb
                ob += '"; i += l'
                lb += " " * (ms[-1] * 4) + ob + chr(10)
                ob = ""
        if not pf:
            i, tf, ms[-1], tb, ob, lb = saved[-1]
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + 1
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == "("
            if pf: i = stop
            if pf:
                pass
                rv = self.parsePEXPR1(i, tf, ms[:], tb, ob, lb)
                pf = rv is not failed
                if pf: i, ms[-1], tb, ob, lb = rv.t
                if pf:
                    pass
                    while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
                    stop = i + 1
                    if stop > len(self.s): pf = False
                    else: pf = self.s[i:stop] == ")"
                    if pf: i = stop
                    if pf:
                        pass
        saved.pop()
        if pf:
            self.cache[k] = Succeeded((i, ms[-1], tb, ob, lb))
            self.lastMatch.append((k[0], k[1]))
        return self.cache[k]
    def parseZZADDY(self, i):
        k = "ZZADDY", i
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        rv = self.peg.Null()
        saved.append((i, rv))
        if rv:
            pass
            saved.append((i, rv))
            if rv:
                pass
                l = 7
                if self.s[i:i + l] == ".syntax": rv = ".syntax"; i += l
                if rv:
                    pass
            if not rv:
                i, rv = saved[-1]
                if rv:
                    pass
                    l = 8
                    if self.s[i:i + l] == ".grammar": rv = ".grammar"; i += l
                    if rv:
                        pass
                if pf: saved.pop()
            if rv:
                pass
                st = self.parseID(i)
                if st is not failed: i, rv = st.t
                name = rv
                if rv:
                    pass
                    pf = first = True
                    rvs = []
                    while pf:
                        st = self.parsePRULE(i)
                        if st is not failed: i, rv = st.t
                        if rv: rvs.append(rv)
                        pf = bool(rv)
                        first = False
                    rules = rv
                    if rv:
                        pass
                        rv = self.py.Compound("class " + name + "Parser(object):", [self.py.Statement("def __init__(self, s): self.s = s; self.lastMatch = []; self.cache = {}"), self.py.Statement("def parse(self): return self.parse" + name + "(0)")] + rules)
        if rv:
            self.cache[k] = Succeeded((i, rv))
            self.lastMatch.append(k)
        return self.cache[k]
    def parseZZR(self, i):
        k = "ZZR", i
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        rv = self.peg.Null()
        saved.append((i, rv))
        if rv:
            pass
            st = self.parseID(i)
            if st is not failed: i, rv = st.t
            name = rv
            if rv:
                pass
                l = 1
                if self.s[i:i + l] == "=": rv = "="; i += l
                if rv:
                    pass
                    saved.append((i, rv))
                    if rv:
                        pass
                        st = self.parseFIELDS(i)
                        if st is not failed: i, rv = st.t
                        fs = rv
                        if rv:
                            pass
                            rv = self.zephyr.Product(name, fs)
                    if not rv:
                        i, rv = saved[-1]
                        if rv:
                            pass
                            st = self.parseCONSTRUCTOR(i)
                            if st is not failed: i, rv = st.t
                            con = rv
                            if rv:
                                pass
                                pf = first = True
                                rvs = []
                                while pf:
                                    saved.append((i, rv))
                                    if rv:
                                        pass
                                        l = 1
                                        if self.s[i:i + l] == "|": rv = "|"; i += l
                                        if rv:
                                            pass
                                            st = self.parseCONSTRUCTOR(i)
                                            if st is not failed: i, rv = st.t
                                            if rv:
                                                pass
                                    if rv: rvs.append(rv)
                                    pf = bool(rv)
                                    first = False
                                cons = rv
                                if rv:
                                    pass
                                    saved.append((i, rv))
                                    saved.append((i, rv))
                                    if rv:
                                        pass
                                        l = 10
                                        if self.s[i:i + l] == "attributes": rv = "attributes"; i += l
                                        if rv:
                                            pass
                                            st = self.parseFIELDS(i)
                                            if st is not failed: i, rv = st.t
                                            if rv:
                                                pass
                                    if not rv:
                                        i, rv = saved[-1]
                                    if pf: saved.pop()
                                    attrs = rv
                                    if rv:
                                        pass
                                        rv = self.zephyr.Sum(name, attrs, con, cons)
                        if pf: saved.pop()
                    if rv:
                        pass
        if rv:
            self.cache[k] = Succeeded((i, rv))
            self.lastMatch.append(k)
        return self.cache[k]
    def parseZCONSTRUCTOR(self, i):
        k = "ZCONSTRUCTOR", i
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        rv = self.peg.Null()
        saved.append((i, rv))
        if rv:
            pass
            st = self.parseID(i)
            if st is not failed: i, rv = st.t
            tag = rv
            if rv:
                pass
                saved.append((i, rv))
                st = self.parseFIELDS(i)
                if st is not failed: i, rv = st.t
                if not rv:
                    i, rv = saved[-1]
                if pf: saved.pop()
                args = rv
                if rv:
                    pass
                    rv = self.zephyr.Con(tag, args)
        if rv:
            self.cache[k] = Succeeded((i, rv))
            self.lastMatch.append(k)
        return self.cache[k]
    def parseZFIELDS(self, i):
        k = "ZFIELDS", i
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        rv = self.peg.Null()
        saved.append((i, rv))
        if rv:
            pass
            l = 1
            if self.s[i:i + l] == "(": rv = "("; i += l
            if rv:
                pass
                st = self.parseFIELD(i)
                if st is not failed: i, rv = st.t
                f = rv
                if rv:
                    pass
                    pf = first = True
                    rvs = []
                    while pf:
                        saved.append((i, rv))
                        if rv:
                            pass
                            l = 1
                            if self.s[i:i + l] == ",": rv = ","; i += l
                            if rv:
                                pass
                                st = self.parseFIELD(i)
                                if st is not failed: i, rv = st.t
                                if rv:
                                    pass
                        if rv: rvs.append(rv)
                        pf = bool(rv)
                        first = False
                    fs = rv
                    if rv:
                        pass
                        l = 1
                        if self.s[i:i + l] == ")": rv = ")"; i += l
                        if rv:
                            pass
                            rv = f + fs
        if rv:
            self.cache[k] = Succeeded((i, rv))
            self.lastMatch.append(k)
        return self.cache[k]
    def parseZFIELD(self, i):
        k = "ZFIELD", i
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        rv = self.peg.Null()
        saved.append((i, rv))
        if rv:
            pass
            st = self.parseID(i)
            if st is not failed: i, rv = st.t
            ty = rv
            if rv:
                pass
                saved.append((i, rv))
                st = self.parseID(i)
                if st is not failed: i, rv = st.t
                if not rv:
                    i, rv = saved[-1]
                if pf: saved.pop()
                name = rv
                if rv:
                    pass
                    l = 1
                    if self.s[i:i + l] == "?": rv = "?"; i += l
                    if rv:
                        pass
                        rv = self.zephyr.Option(ty, name)
        if not rv:
            i, rv = saved[-1]
            if rv:
                pass
                st = self.parseID(i)
                if st is not failed: i, rv = st.t
                ty = rv
                if rv:
                    pass
                    saved.append((i, rv))
                    st = self.parseID(i)
                    if st is not failed: i, rv = st.t
                    if not rv:
                        i, rv = saved[-1]
                    if pf: saved.pop()
                    name = rv
                    if rv:
                        pass
                        l = 1
                        if self.s[i:i + l] == "*": rv = "*"; i += l
                        if rv:
                            pass
                            rv = self.zephyr.Sequence(ty, name)
            if pf: saved.pop()
        if not rv:
            i, rv = saved[-1]
            if rv:
                pass
                st = self.parseID(i)
                if st is not failed: i, rv = st.t
                ty = rv
                if rv:
                    pass
                    saved.append((i, rv))
                    st = self.parseID(i)
                    if st is not failed: i, rv = st.t
                    if not rv:
                        i, rv = saved[-1]
                    if pf: saved.pop()
                    name = rv
                    if rv:
                        pass
                        rv = self.zephyr.Id(ty, name)
            if pf: saved.pop()
        if rv:
            self.cache[k] = Succeeded((i, rv))
            self.lastMatch.append(k)
        return self.cache[k]
    def parseZPRULE(self, i):
        k = "ZPRULE", i
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        rv = self.peg.Null()
        saved.append((i, rv))
        if rv:
            pass
            st = self.parseID(i)
            if st is not failed: i, rv = st.t
            name = rv
            if rv:
                pass
                l = 2
                if self.s[i:i + l] == ":=": rv = ":="; i += l
                if rv:
                    pass
                    st = self.parsePEXPR1(i)
                    if st is not failed: i, rv = st.t
                    expr = rv
                    if rv:
                        pass
                        l = 1
                        if self.s[i:i + l] == ";": rv = ";"; i += l
                        if rv:
                            pass
                            rv = self.py.Compound("def parse" + name + "(self, i):", expr)
        if rv:
            self.cache[k] = Succeeded((i, rv))
            self.lastMatch.append(k)
        return self.cache[k]
    def parseZPEXPR1(self, i):
        k = "ZPEXPR1", i
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        rv = self.peg.Null()
        saved.append((i, rv))
        if rv:
            pass
            st = self.parsePEXPR2(i)
            if st is not failed: i, rv = st.t
            this = rv
            if rv:
                pass
                l = 1
                if self.s[i:i + l] == "/": rv = "/"; i += l
                if rv:
                    pass
                    st = self.parsePEXPR2(i)
                    if st is not failed: i, rv = st.t
                    that = rv
                    if rv:
                        pass
                        rv = self.peg.Choice(this, that)
        if not rv:
            i, rv = saved[-1]
            if rv:
                pass
                st = self.parsePEXPR2(i)
                if st is not failed: i, rv = st.t
                if rv:
                    pass
            if pf: saved.pop()
        if rv:
            self.cache[k] = Succeeded((i, rv))
            self.lastMatch.append(k)
        return self.cache[k]
    def parseZPEXPR2(self, i):
        k = "ZPEXPR2", i
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        rv = self.peg.Null()
        saved.append((i, rv))
        if rv:
            pass
            pf = first = True
            rvs = []
            while pf:
                st = self.parsePEXPR3(i)
                if st is not failed: i, rv = st.t
                if rv: rvs.append(rv)
                pf = bool(rv)
                first = False
            exprs = rv
            if rv:
                pass
                l = 2
                if self.s[i:i + l] == "->": rv = "->"; i += l
                if rv:
                    pass
                    st = self.parsePPROD1(i)
                    if st is not failed: i, rv = st.t
                    prod = rv
                    if rv:
                        pass
                        rv = self.peg.Production(self.peg.Sequence(exprs), prod)
        if not rv:
            i, rv = saved[-1]
            if rv:
                pass
                pf = first = True
                rvs = []
                while pf:
                    st = self.parsePEXPR3(i)
                    if st is not failed: i, rv = st.t
                    if rv: rvs.append(rv)
                    pf = bool(rv)
                    first = False
                exprs = rv
                if rv:
                    pass
                    rv = self.peg.Sequence(exprs)
            if pf: saved.pop()
        if rv:
            self.cache[k] = Succeeded((i, rv))
            self.lastMatch.append(k)
        return self.cache[k]
    def parseZPEXPR3(self, i):
        k = "ZPEXPR3", i
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        rv = self.peg.Null()
        saved.append((i, rv))
        if rv:
            pass
            st = self.parsePEXPR4(i)
            if st is not failed: i, rv = st.t
            expr = rv
            if rv:
                pass
                l = 1
                if self.s[i:i + l] == ":": rv = ":"; i += l
                if rv:
                    pass
                    st = self.parseID(i)
                    if st is not failed: i, rv = st.t
                    name = rv
                    if rv:
                        pass
                        rv = self.peg.Capture(expr, name)
        if not rv:
            i, rv = saved[-1]
            if rv:
                pass
                st = self.parsePEXPR4(i)
                if st is not failed: i, rv = st.t
                if rv:
                    pass
            if pf: saved.pop()
        if rv:
            self.cache[k] = Succeeded((i, rv))
            self.lastMatch.append(k)
        return self.cache[k]
    def parseZPEXPR4(self, i):
        k = "ZPEXPR4", i
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        rv = self.peg.Null()
        saved.append((i, rv))
        if rv:
            pass
            l = 1
            if self.s[i:i + l] == "&": rv = "&"; i += l
            if rv:
                pass
                st = self.parsePEXPR5(i)
                if st is not failed: i, rv = st.t
                expr = rv
                if rv:
                    pass
                    rv = self.peg.Positive(expr)
        if not rv:
            i, rv = saved[-1]
            if rv:
                pass
                l = 1
                if self.s[i:i + l] == "!": rv = "!"; i += l
                if rv:
                    pass
                    st = self.parsePEXPR5(i)
                    if st is not failed: i, rv = st.t
                    expr = rv
                    if rv:
                        pass
                        rv = self.peg.Negative(expr)
            if pf: saved.pop()
        if not rv:
            i, rv = saved[-1]
            if rv:
                pass
                st = self.parsePEXPR5(i)
                if st is not failed: i, rv = st.t
                if rv:
                    pass
            if pf: saved.pop()
        if rv:
            self.cache[k] = Succeeded((i, rv))
            self.lastMatch.append(k)
        return self.cache[k]
    def parseZPEXPR5(self, i):
        k = "ZPEXPR5", i
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        rv = self.peg.Null()
        saved.append((i, rv))
        if rv:
            pass
            st = self.parsePEXPR6(i)
            if st is not failed: i, rv = st.t
            expr = rv
            if rv:
                pass
                l = 1
                if self.s[i:i + l] == "*": rv = "*"; i += l
                if rv:
                    pass
                    rv = self.peg.Any(expr)
        if not rv:
            i, rv = saved[-1]
            if rv:
                pass
                st = self.parsePEXPR6(i)
                if st is not failed: i, rv = st.t
                expr = rv
                if rv:
                    pass
                    l = 1
                    if self.s[i:i + l] == "?": rv = "?"; i += l
                    if rv:
                        pass
                        rv = self.peg.Maybe(expr)
            if pf: saved.pop()
        if not rv:
            i, rv = saved[-1]
            if rv:
                pass
                st = self.parsePEXPR6(i)
                if st is not failed: i, rv = st.t
                if rv:
                    pass
            if pf: saved.pop()
        if rv:
            self.cache[k] = Succeeded((i, rv))
            self.lastMatch.append(k)
        return self.cache[k]
    def parseZPEXPR6(self, i):
        k = "ZPEXPR6", i
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        rv = self.peg.Null()
        saved.append((i, rv))
        if rv:
            pass
            l = 7
            if self.s[i:i + l] == ".range(": rv = ".range("; i += l
            if rv:
                pass
                st = self.parseNUMBER(i)
                if st is not failed: i, rv = st.t
                l = rv
                if rv:
                    pass
                    l = 1
                    if self.s[i:i + l] == ":": rv = ":"; i += l
                    if rv:
                        pass
                        st = self.parseNUMBER(i)
                        if st is not failed: i, rv = st.t
                        u = rv
                        if rv:
                            pass
                            l = 1
                            if self.s[i:i + l] == ")": rv = ")"; i += l
                            if rv:
                                pass
                                rv = self.peg.Range(l, u)
        if not rv:
            i, rv = saved[-1]
            if rv:
                pass
                l = 4
                if self.s[i:i + l] == ".any": rv = ".any"; i += l
                if rv:
                    pass
                    rv = self.peg.AnyChar()
            if pf: saved.pop()
        if not rv:
            i, rv = saved[-1]
            if rv:
                pass
                st = self.parseNUMBER(i)
                if st is not failed: i, rv = st.t
                c = rv
                if rv:
                    pass
                    rv = self.peg.Char(c)
            if pf: saved.pop()
        if not rv:
            i, rv = saved[-1]
            if rv:
                pass
                st = self.parseID(i)
                if st is not failed: i, rv = st.t
                name = rv
                if rv:
                    pass
                    rv = self.peg.Call(name)
            if pf: saved.pop()
        if not rv:
            i, rv = saved[-1]
            if rv:
                pass
                st = self.parseSTRING(i)
                if st is not failed: i, rv = st.t
                s = rv
                if rv:
                    pass
                    rv = self.peg.String(s)
            if pf: saved.pop()
        if not rv:
            i, rv = saved[-1]
            if rv:
                pass
                l = 1
                if self.s[i:i + l] == "(": rv = "("; i += l
                if rv:
                    pass
                    st = self.parsePEXPR1(i)
                    if st is not failed: i, rv = st.t
                    if rv:
                        pass
                        l = 1
                        if self.s[i:i + l] == ")": rv = ")"; i += l
                        if rv:
                            pass
            if pf: saved.pop()
        if rv:
            self.cache[k] = Succeeded((i, rv))
            self.lastMatch.append(k)
        return self.cache[k]
    def parseZPPROD1(self, i):
        k = "ZPPROD1", i
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        rv = self.peg.Null()
        saved.append((i, rv))
        if rv:
            pass
            st = self.parsePPROD1(i)
            if st is not failed: i, rv = st.t
            this = rv
            if rv:
                pass
                l = 1
                if self.s[i:i + l] == "+": rv = "+"; i += l
                if rv:
                    pass
                    st = self.parsePPROD2(i)
                    if st is not failed: i, rv = st.t
                    that = rv
                    if rv:
                        pass
                        rv = self.peg.Plus(this, that)
        if not rv:
            i, rv = saved[-1]
            if rv:
                pass
                st = self.parsePPROD2(i)
                if st is not failed: i, rv = st.t
                if rv:
                    pass
            if pf: saved.pop()
        if rv:
            self.cache[k] = Succeeded((i, rv))
            self.lastMatch.append(k)
        return self.cache[k]
    def parseZPPROD2(self, i):
        k = "ZPPROD2", i
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        rv = self.peg.Null()
        saved.append((i, rv))
        if rv:
            pass
            st = self.parseID(i)
            if st is not failed: i, rv = st.t
            ty = rv
            if rv:
                pass
                l = 1
                if self.s[i:i + l] == ".": rv = "."; i += l
                if rv:
                    pass
                    st = self.parseID(i)
                    if st is not failed: i, rv = st.t
                    con = rv
                    if rv:
                        pass
                        l = 1
                        if self.s[i:i + l] == "(": rv = "("; i += l
                        if rv:
                            pass
                            st = self.parsePPROD1(i)
                            if st is not failed: i, rv = st.t
                            prod = rv
                            if rv:
                                pass
                                pf = first = True
                                rvs = []
                                while pf:
                                    saved.append((i, rv))
                                    if rv:
                                        pass
                                        l = 1
                                        if self.s[i:i + l] == ",": rv = ","; i += l
                                        if rv:
                                            pass
                                            st = self.parsePPROD1(i)
                                            if st is not failed: i, rv = st.t
                                            if rv:
                                                pass
                                    if rv: rvs.append(rv)
                                    pf = bool(rv)
                                    first = False
                                prods = rv
                                if rv:
                                    pass
                                    l = 1
                                    if self.s[i:i + l] == ")": rv = ")"; i += l
                                    if rv:
                                        pass
                                        rv = self.peg.Con(ty, con, [prod] + prods)
        if not rv:
            i, rv = saved[-1]
            if rv:
                pass
                l = 2
                if self.s[i:i + l] == "[]": rv = "[]"; i += l
                if rv:
                    pass
                    rv = self.peg.List([])
            if pf: saved.pop()
        if not rv:
            i, rv = saved[-1]
            if rv:
                pass
                l = 1
                if self.s[i:i + l] == "[": rv = "["; i += l
                if rv:
                    pass
                    st = self.parsePPROD1(i)
                    if st is not failed: i, rv = st.t
                    expr = rv
                    if rv:
                        pass
                        pf = first = True
                        rvs = []
                        while pf:
                            saved.append((i, rv))
                            if rv:
                                pass
                                l = 1
                                if self.s[i:i + l] == ",": rv = ","; i += l
                                if rv:
                                    pass
                                    st = self.parsePPROD1(i)
                                    if st is not failed: i, rv = st.t
                                    if rv:
                                        pass
                            if rv: rvs.append(rv)
                            pf = bool(rv)
                            first = False
                        exprs = rv
                        if rv:
                            pass
                            l = 1
                            if self.s[i:i + l] == "]": rv = "]"; i += l
                            if rv:
                                pass
                                rv = self.peg.List([expr] + exprs)
            if pf: saved.pop()
        if not rv:
            i, rv = saved[-1]
            if rv:
                pass
                st = self.parseID(i)
                if st is not failed: i, rv = st.t
                s = rv
                if rv:
                    pass
                    rv = self.peg.Name(s)
            if pf: saved.pop()
        if not rv:
            i, rv = saved[-1]
            if rv:
                pass
                st = self.parseSTRING(i)
                if st is not failed: i, rv = st.t
                s = rv
                if rv:
                    pass
                    rv = self.peg.String(s)
            if pf: saved.pop()
        if rv:
            self.cache[k] = Succeeded((i, rv))
            self.lastMatch.append(k)
        return self.cache[k]
    def parseZWS(self, i):
        k = "ZWS", i
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        rv = self.peg.Null()
        saved.append((i, rv))
        if rv:
            pass
            pf = first = True
            rvs = []
            while pf:
                saved.append((i, rv))
                if rv:
                    pass
                    if ord(self.s[i]) == 9: rv = chr(9); i += 1
                    if rv:
                        pass
                if not rv:
                    i, rv = saved[-1]
                    if rv:
                        pass
                        if ord(self.s[i]) == 10: rv = chr(10); i += 1
                        if rv:
                            pass
                    if pf: saved.pop()
                if not rv:
                    i, rv = saved[-1]
                    if rv:
                        pass
                        if ord(self.s[i]) == 13: rv = chr(13); i += 1
                        if rv:
                            pass
                    if pf: saved.pop()
                if not rv:
                    i, rv = saved[-1]
                    if rv:
                        pass
                        if ord(self.s[i]) == 32: rv = chr(32); i += 1
                        if rv:
                            pass
                    if pf: saved.pop()
                if rv: rvs.append(rv)
                pf = bool(rv)
                first = False
            if rv:
                pass
        if rv:
            self.cache[k] = Succeeded((i, rv))
            self.lastMatch.append(k)
        return self.cache[k]
    def parseZDIGIT(self, i):
        k = "ZDIGIT", i
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        rv = self.peg.Null()
        saved.append((i, rv))
        if rv:
            pass
            if 48 <= ord(self.s[i]) <= 57: rv = self.s[i]; i += 1
            if rv:
                pass
        if rv:
            self.cache[k] = Succeeded((i, rv))
            self.lastMatch.append(k)
        return self.cache[k]
    def parseZALPHA(self, i):
        k = "ZALPHA", i
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        rv = self.peg.Null()
        saved.append((i, rv))
        if rv:
            pass
            if 65 <= ord(self.s[i]) <= 90: rv = self.s[i]; i += 1
            if rv:
                pass
        if not rv:
            i, rv = saved[-1]
            if rv:
                pass
                if 97 <= ord(self.s[i]) <= 122: rv = self.s[i]; i += 1
                if rv:
                    pass
            if pf: saved.pop()
        if rv:
            self.cache[k] = Succeeded((i, rv))
            self.lastMatch.append(k)
        return self.cache[k]
    def parseZSQUOTE(self, i):
        k = "ZSQUOTE", i
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        rv = self.peg.Null()
        saved.append((i, rv))
        if rv:
            pass
            st = self.parseWS(i)
            if st is not failed: i, rv = st.t
            if rv:
                pass
                if ord(self.s[i]) == 39: rv = chr(39); i += 1
                if rv:
                    pass
        if rv:
            self.cache[k] = Succeeded((i, rv))
            self.lastMatch.append(k)
        return self.cache[k]
    def parseZSTRING(self, i):
        k = "ZSTRING", i
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        rv = self.peg.Null()
        saved.append((i, rv))
        if rv:
            pass
            st = self.parseWS(i)
            if st is not failed: i, rv = st.t
            if rv:
                pass
                if ord(self.s[i]) == 39: rv = chr(39); i += 1
                if rv:
                    pass
                    pf = first = True
                    rvs = []
                    while pf:
                        saved.append((i, rv))
                        if rv:
                            pass
                            saved.append((i, rv))
                            saved.append((i, rv))
                            if rv:
                                pass
                                if ord(self.s[i]) == 10: rv = chr(10); i += 1
                                if rv:
                                    pass
                            if not rv:
                                i, rv = saved[-1]
                                if rv:
                                    pass
                                    if ord(self.s[i]) == 13: rv = chr(13); i += 1
                                    if rv:
                                        pass
                                if pf: saved.pop()
                            if not rv:
                                i, rv = saved[-1]
                                if rv:
                                    pass
                                    if ord(self.s[i]) == 39: rv = chr(39); i += 1
                                    if rv:
                                        pass
                                if pf: saved.pop()
                            i, rv = saved[-1]
                            if rv:
                                pass
                                rv = self.s[i]; i += 1
                                if rv:
                                    pass
                        if rv: rvs.append(rv)
                        pf = bool(rv)
                        first = False
                    cs = rv
                    if rv:
                        pass
                        if ord(self.s[i]) == 39: rv = chr(39); i += 1
                        if rv:
                            pass
                            rv = cs
        if rv:
            self.cache[k] = Succeeded((i, rv))
            self.lastMatch.append(k)
        return self.cache[k]
    def parseZNUMBER(self, i):
        k = "ZNUMBER", i
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        rv = self.peg.Null()
        saved.append((i, rv))
        if rv:
            pass
            st = self.parseWS(i)
            if st is not failed: i, rv = st.t
            if rv:
                pass
                st = self.parseZDIGIT(i)
                if st is not failed: i, rv = st.t
                d = rv
                if rv:
                    pass
                    pf = first = True
                    rvs = []
                    while pf:
                        st = self.parseZDIGIT(i)
                        if st is not failed: i, rv = st.t
                        if rv: rvs.append(rv)
                        pf = bool(rv)
                        first = False
                    ds = rv
                    if rv:
                        pass
                        rv = d + ds
        if rv:
            self.cache[k] = Succeeded((i, rv))
            self.lastMatch.append(k)
        return self.cache[k]
    def parseZID(self, i):
        k = "ZID", i
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        rv = self.peg.Null()
        saved.append((i, rv))
        if rv:
            pass
            st = self.parseWS(i)
            if st is not failed: i, rv = st.t
            if rv:
                pass
                st = self.parseALPHA(i)
                if st is not failed: i, rv = st.t
                c = rv
                if rv:
                    pass
                    pf = first = True
                    rvs = []
                    while pf:
                        saved.append((i, rv))
                        if rv:
                            pass
                            st = self.parseALPHA(i)
                            if st is not failed: i, rv = st.t
                            if rv:
                                pass
                        if not rv:
                            i, rv = saved[-1]
                            if rv:
                                pass
                                st = self.parseDIGIT(i)
                                if st is not failed: i, rv = st.t
                                if rv:
                                    pass
                            if pf: saved.pop()
                        if rv: rvs.append(rv)
                        pf = bool(rv)
                        first = False
                    cs = rv
                    if rv:
                        pass
                        rv = c + cs
        if rv:
            self.cache[k] = Succeeded((i, rv))
            self.lastMatch.append(k)
        return self.cache[k]
    def parseWS(self, i, tf, ms, tb, ob, lb):
        k = "WS", i, tf, ms[-1], tb, ob, lb
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        pf = True
        saved.append((i, tf, ms[-1], tb, ob, lb))
        while pf:
            pf = (i < len(self.s)) and ord(self.s[i]) == 9 or ord(self.s[i]) == 10 or ord(self.s[i]) == 13 or ord(self.s[i]) == 32
            if pf:
                if tf: tb += self.s[i]
                i += 1
        pf = True
        if pf:
            pass
        saved.pop()
        if pf:
            self.cache[k] = Succeeded((i, ms[-1], tb, ob, lb))
            self.lastMatch.append((k[0], k[1]))
        return self.cache[k]
    def parseDIGIT(self, i, tf, ms, tb, ob, lb):
        k = "DIGIT", i, tf, ms[-1], tb, ob, lb
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        pf = True
        saved.append((i, tf, ms[-1], tb, ob, lb))
        pf = (i < len(self.s)) and 48 <= ord(self.s[i]) <= 57
        if pf:
            if tf: tb += self.s[i]
            i += 1
        if pf:
            pass
        saved.pop()
        if pf:
            self.cache[k] = Succeeded((i, ms[-1], tb, ob, lb))
            self.lastMatch.append((k[0], k[1]))
        return self.cache[k]
    def parseALPHA(self, i, tf, ms, tb, ob, lb):
        k = "ALPHA", i, tf, ms[-1], tb, ob, lb
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        pf = True
        saved.append((i, tf, ms[-1], tb, ob, lb))
        pf = (i < len(self.s)) and 65 <= ord(self.s[i]) <= 90 or 97 <= ord(self.s[i]) <= 122
        if pf:
            if tf: tb += self.s[i]
            i += 1
        if pf:
            pass
        saved.pop()
        if pf:
            self.cache[k] = Succeeded((i, ms[-1], tb, ob, lb))
            self.lastMatch.append((k[0], k[1]))
        return self.cache[k]
    def parseSQUOTE(self, i, tf, ms, tb, ob, lb):
        k = "SQUOTE", i, tf, ms[-1], tb, ob, lb
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        pf = True
        saved.append((i, tf, ms[-1], tb, ob, lb))
        rv = self.parseWS(i, tf, ms[:], tb, ob, lb)
        pf = rv is not failed
        if pf: i, ms[-1], tb, ob, lb = rv.t
        if pf:
            pass
            pf = (i < len(self.s)) and ord(self.s[i]) == 39
            if pf:
                if tf: tb += self.s[i]
                i += 1
            if pf:
                pass
        saved.pop()
        if pf:
            self.cache[k] = Succeeded((i, ms[-1], tb, ob, lb))
            self.lastMatch.append((k[0], k[1]))
        return self.cache[k]
    def parseSTRING(self, i, tf, ms, tb, ob, lb):
        k = "STRING", i, tf, ms[-1], tb, ob, lb
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        pf = True
        saved.append((i, tf, ms[-1], tb, ob, lb))
        rv = self.parseWS(i, tf, ms[:], tb, ob, lb)
        pf = rv is not failed
        if pf: i, ms[-1], tb, ob, lb = rv.t
        if pf:
            pass
            pf = (i < len(self.s)) and ord(self.s[i]) == 39
            if pf:
                if tf: tb += self.s[i]
                i += 1
            if pf:
                pass
                tb = ""
                tf = True
                if pf:
                    pass
                    while pf:
                        pf = (i < len(self.s)) and ord(self.s[i]) == 10 or ord(self.s[i]) == 13 or ord(self.s[i]) == 39
                        pf = (i < len(self.s)) and not pf
                        if pf:
                            if tf: tb += self.s[i]
                            i += 1
                    pf = True
                    if pf:
                        pass
                        tf = False
                        if pf:
                            pass
                            pf = (i < len(self.s)) and ord(self.s[i]) == 39
                            if pf:
                                if tf: tb += self.s[i]
                                i += 1
                            if pf:
                                pass
        saved.pop()
        if pf:
            self.cache[k] = Succeeded((i, ms[-1], tb, ob, lb))
            self.lastMatch.append((k[0], k[1]))
        return self.cache[k]
    def parseNUMBER(self, i, tf, ms, tb, ob, lb):
        k = "NUMBER", i, tf, ms[-1], tb, ob, lb
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        pf = True
        saved.append((i, tf, ms[-1], tb, ob, lb))
        rv = self.parseWS(i, tf, ms[:], tb, ob, lb)
        pf = rv is not failed
        if pf: i, ms[-1], tb, ob, lb = rv.t
        if pf:
            pass
            tb = ""
            tf = True
            if pf:
                pass
                rv = self.parseDIGIT(i, tf, ms[:], tb, ob, lb)
                pf = rv is not failed
                if pf: i, ms[-1], tb, ob, lb = rv.t
                if pf:
                    pass
                    while pf:
                        rv = self.parseDIGIT(i, tf, ms[:], tb, ob, lb)
                        pf = rv is not failed
                        if pf: i, ms[-1], tb, ob, lb = rv.t
                    pf = True
                    if pf:
                        pass
                        tf = False
                        if pf:
                            pass
        saved.pop()
        if pf:
            self.cache[k] = Succeeded((i, ms[-1], tb, ob, lb))
            self.lastMatch.append((k[0], k[1]))
        return self.cache[k]
    def parseID(self, i, tf, ms, tb, ob, lb):
        k = "ID", i, tf, ms[-1], tb, ob, lb
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        pf = True
        saved.append((i, tf, ms[-1], tb, ob, lb))
        rv = self.parseWS(i, tf, ms[:], tb, ob, lb)
        pf = rv is not failed
        if pf: i, ms[-1], tb, ob, lb = rv.t
        if pf:
            pass
            tb = ""
            tf = True
            if pf:
                pass
                rv = self.parseALPHA(i, tf, ms[:], tb, ob, lb)
                pf = rv is not failed
                if pf: i, ms[-1], tb, ob, lb = rv.t
                if pf:
                    pass
                    while pf:
                        saved.append((i, tf, ms[-1], tb, ob, lb))
                        rv = self.parseALPHA(i, tf, ms[:], tb, ob, lb)
                        pf = rv is not failed
                        if pf: i, ms[-1], tb, ob, lb = rv.t
                        if pf:
                            pass
                        if not pf:
                            i, tf, ms[-1], tb, ob, lb = saved[-1]
                            rv = self.parseDIGIT(i, tf, ms[:], tb, ob, lb)
                            pf = rv is not failed
                            if pf: i, ms[-1], tb, ob, lb = rv.t
                            if pf:
                                pass
                        saved.pop()
                    pf = True
                    if pf:
                        pass
                        tf = False
                        if pf:
                            pass
        saved.pop()
        if pf:
            self.cache[k] = Succeeded((i, ms[-1], tb, ob, lb))
            self.lastMatch.append((k[0], k[1]))
        return self.cache[k]
    def top(self):
        pass
        self.apf = 0
