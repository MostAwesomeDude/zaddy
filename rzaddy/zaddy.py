from rpython.rlib.rfile import create_stdio
def target(driver, *args):
    driver.exe_name = "ZADDY".lower() + "c"
    return main, None
class ParseError(Exception):
    def __init__(self, i): self.i = i
def main(argv):
    stdin, stdout, stderr = create_stdio()
    parser = ZADDYParser(stdin.read())
    try:
        _, _, _, _, _, _, lb = parser.parse()
        stdout.write(lb)
        return 0
    except ParseError as pe:
        line = parser.s.count(chr(10), 0, pe.i) + 1
        stderr.write(("Error at input location: %d (line %d)" % (pe.i, line)) + chr(10))
        stderr.write(("Backtrace: %s" % " ".join(parser.stack)) + chr(10))
        stderr.write(("Last matching token: '%s'" % parser.lastMatch) + chr(10))
        return 1
class ZADDYParser(object):
    lastMatch = ""
    def __init__(self, s): self.s = s; self.stack = []; self.top()
    def parse(self):
        self.top()
        # i, pf, tf, ms, tb, ob, lb
        return self.parseZADDY(0, False, False, [0], "", "", "")
    def parseOUT1(self, i, pf, tf, ms, tb, ob, lb):
        while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
        stop = i + len("*")
        if stop > len(self.s): pf = False
        else: pf = self.s[i:stop] == "*"
        if pf: self.lastMatch = "*"; i = stop
        if pf:
            pass
            ob += 'ob += tb'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
        if not pf:
            self.stack.append("STRING")
            i, pf, tf, ms, tb, ob, lb = self.parseSTRING(i, pf, tf, ms[:], tb, ob, lb)
            self.stack.pop()
            if pf:
                pass
                ob += 'ob += '
                ob += chr(39)
                ob += tb
                ob += chr(39)
                lb += " " * (ms[-1] * 4) + ob + chr(10)
                ob = ""
        if not pf:
            self.stack.append("NUMBER")
            i, pf, tf, ms, tb, ob, lb = self.parseNUMBER(i, pf, tf, ms[:], tb, ob, lb)
            self.stack.pop()
            if pf:
                pass
                ob += 'ob += chr('
                ob += tb
                ob += ')'
                lb += " " * (ms[-1] * 4) + ob + chr(10)
                ob = ""
        if not pf:
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + len(".lm+")
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == ".lm+"
            if pf: self.lastMatch = ".lm+"; i = stop
            if pf:
                pass
                ob += 'ms[-1] += 1'
                lb += " " * (ms[-1] * 4) + ob + chr(10)
                ob = ""
        if not pf:
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + len(".lm-")
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == ".lm-"
            if pf: self.lastMatch = ".lm-"; i = stop
            if pf:
                pass
                ob += 'if ms[-1]: ms[-1] -= 1'
                lb += " " * (ms[-1] * 4) + ob + chr(10)
                ob = ""
        if not pf:
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + len(".lm?")
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == ".lm?"
            if pf: self.lastMatch = ".lm?"; i = stop
            if pf:
                pass
                ob += 'ms.append(ms[-1])'
                lb += " " * (ms[-1] * 4) + ob + chr(10)
                ob = ""
        if not pf:
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + len(".lm!")
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == ".lm!"
            if pf: self.lastMatch = ".lm!"; i = stop
            if pf:
                pass
                ob += 'ms.pop()'
                lb += " " * (ms[-1] * 4) + ob + chr(10)
                ob = ""
        if not pf:
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + len(".nl")
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == ".nl"
            if pf: self.lastMatch = ".nl"; i = stop
            if pf:
                pass
                ob += 'lb += " " * (ms[-1] * 4) + ob + chr(10)'
                lb += " " * (ms[-1] * 4) + ob + chr(10)
                ob = ""
                ob += 'ob = ""'
                lb += " " * (ms[-1] * 4) + ob + chr(10)
                ob = ""
        return i, pf, tf, ms, tb, ob, lb
    def parseOUTPUT(self, i, pf, tf, ms, tb, ob, lb):
        while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
        stop = i + len(".out")
        if stop > len(self.s): pf = False
        else: pf = self.s[i:stop] == ".out"
        if pf: self.lastMatch = ".out"; i = stop
        if pf:
            pass
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + len("(")
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == "("
            if pf: self.lastMatch = "("; i = stop
            if not pf: raise ParseError(i)
            while pf:
                self.stack.append("OUT1")
                i, pf, tf, ms, tb, ob, lb = self.parseOUT1(i, pf, tf, ms[:], tb, ob, lb)
                self.stack.pop()
            pf = True
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + len(")")
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == ")"
            if pf: self.lastMatch = ")"; i = stop
            if not pf: raise ParseError(i)
        return i, pf, tf, ms, tb, ob, lb
    def parseCX3(self, i, pf, tf, ms, tb, ob, lb):
        self.stack.append("NUMBER")
        i, pf, tf, ms, tb, ob, lb = self.parseNUMBER(i, pf, tf, ms[:], tb, ob, lb)
        self.stack.pop()
        if pf:
            pass
        if not pf:
            self.stack.append("SQUOTE")
            i, pf, tf, ms, tb, ob, lb = self.parseSQUOTE(i, pf, tf, ms[:], tb, ob, lb)
            self.stack.pop()
            if pf:
                pass
                tb = str(ord(self.s[i]))
                i += 1
        return i, pf, tf, ms, tb, ob, lb
    def parseCX2(self, i, pf, tf, ms, tb, ob, lb):
        self.stack.append("CX3")
        i, pf, tf, ms, tb, ob, lb = self.parseCX3(i, pf, tf, ms[:], tb, ob, lb)
        self.stack.pop()
        if pf:
            pass
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + len(":")
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == ":"
            if pf: self.lastMatch = ":"; i = stop
            if pf:
                pass
                ob += tb
                ob += ' <= ord(self.s[i]) <= '
                self.stack.append("CX3")
                i, pf, tf, ms, tb, ob, lb = self.parseCX3(i, pf, tf, ms[:], tb, ob, lb)
                self.stack.pop()
                if not pf: raise ParseError(i)
                ob += tb
            if not pf:
                pf = True
                if pf:
                    pass
                    ob += 'ord(self.s[i]) == '
                    ob += tb
            if not pf: raise ParseError(i)
        return i, pf, tf, ms, tb, ob, lb
    def parseCX1(self, i, pf, tf, ms, tb, ob, lb):
        ob += 'pf = (i < len(self.s)) and '
        self.stack.append("CX2")
        i, pf, tf, ms, tb, ob, lb = self.parseCX2(i, pf, tf, ms[:], tb, ob, lb)
        self.stack.pop()
        if not pf: raise ParseError(i)
        while pf:
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + len("!")
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == "!"
            if pf: self.lastMatch = "!"; i = stop
            if pf:
                pass
                ob += ' or '
                self.stack.append("CX2")
                i, pf, tf, ms, tb, ob, lb = self.parseCX2(i, pf, tf, ms[:], tb, ob, lb)
                self.stack.pop()
                if not pf: raise ParseError(i)
        pf = True
        lb += " " * (ms[-1] * 4) + ob + chr(10)
        ob = ""
        self.apf = 0
        return i, pf, tf, ms, tb, ob, lb
    def parseSCAN(self, i, pf, tf, ms, tb, ob, lb):
        if (self.apf == 1):
            pass
            if (self.atf == 1):
                pass
                ob += 'tb += self.s[i]'
                lb += " " * (ms[-1] * 4) + ob + chr(10)
                ob = ""
            if pf:
                pass
                if (self.atf == 0):
                    pass
                    ob += 'if tf: tb += self.s[i]'
                    lb += " " * (ms[-1] * 4) + ob + chr(10)
                    ob = ""
                if not pf: raise ParseError(i)
                ob += 'i += 1'
                lb += " " * (ms[-1] * 4) + ob + chr(10)
                ob = ""
        if pf:
            pass
            if (self.apf == 0):
                pass
                ob += 'if pf:'
                lb += " " * (ms[-1] * 4) + ob + chr(10)
                ob = ""
                ms[-1] += 1
                if (self.atf == 1):
                    pass
                    ob += 'tb += self.s[i]'
                    lb += " " * (ms[-1] * 4) + ob + chr(10)
                    ob = ""
                if not pf: raise ParseError(i)
                if (self.atf == 0):
                    pass
                    ob += 'if tf: tb += self.s[i]'
                    lb += " " * (ms[-1] * 4) + ob + chr(10)
                    ob = ""
                if not pf: raise ParseError(i)
                ob += 'i += 1'
                lb += " " * (ms[-1] * 4) + ob + chr(10)
                ob = ""
                if ms[-1]: ms[-1] -= 1
            if not pf: raise ParseError(i)
        return i, pf, tf, ms, tb, ob, lb
    def parseSUB(self, i, pf, tf, ms, tb, ob, lb):
        self.stack.append("ID")
        i, pf, tf, ms, tb, ob, lb = self.parseID(i, pf, tf, ms[:], tb, ob, lb)
        self.stack.pop()
        if pf:
            pass
            ob += 'self.stack.append("'
            ob += tb
            ob += '")'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
            ob += 'i, pf, tf, ms, tb, ob, lb = self.parse'
            ob += tb
            ob += '(i, pf, tf, ms[:], tb, ob, lb)'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
            ob += 'self.stack.pop()'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
            self.top()
        return i, pf, tf, ms, tb, ob, lb
    def parseSET(self, i, pf, tf, ms, tb, ob, lb):
        if (not (self.apf == 1)):
            pass
            ob += 'pf = True'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
        if pf:
            pass
            self.apf = 1
        return i, pf, tf, ms, tb, ob, lb
    def parseTX3(self, i, pf, tf, ms, tb, ob, lb):
        while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
        stop = i + len(".token")
        if stop > len(self.s): pf = False
        else: pf = self.s[i:stop] == ".token"
        if pf: self.lastMatch = ".token"; i = stop
        if pf:
            pass
            ob += 'tb = ""'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
            if (not (self.atf == 1)):
                pass
                ob += 'tf = True'
                lb += " " * (ms[-1] * 4) + ob + chr(10)
                ob = ""
            if not pf: raise ParseError(i)
            self.atf = 1
        if not pf:
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + len(".tokout")
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == ".tokout"
            if pf: self.lastMatch = ".tokout"; i = stop
            if pf:
                pass
                if (not (self.atf == 2)):
                    pass
                    ob += 'tf = False'
                    lb += " " * (ms[-1] * 4) + ob + chr(10)
                    ob = ""
                if not pf: raise ParseError(i)
                self.atf = 2
        if not pf:
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + len("$")
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == "$"
            if pf: self.lastMatch = "$"; i = stop
            if pf:
                pass
                self.stack.append("SET")
                i, pf, tf, ms, tb, ob, lb = self.parseSET(i, pf, tf, ms[:], tb, ob, lb)
                self.stack.pop()
                if not pf: raise ParseError(i)
                ob += 'while pf:'
                lb += " " * (ms[-1] * 4) + ob + chr(10)
                ob = ""
                ms[-1] += 1
                self.apf = 1
                self.stack.append("TX3")
                i, pf, tf, ms, tb, ob, lb = self.parseTX3(i, pf, tf, ms[:], tb, ob, lb)
                self.stack.pop()
                if not pf: raise ParseError(i)
                if ms[-1]: ms[-1] -= 1
                self.apf = 2
        if pf:
            pass
            self.stack.append("SET")
            i, pf, tf, ms, tb, ob, lb = self.parseSET(i, pf, tf, ms[:], tb, ob, lb)
            self.stack.pop()
            if not pf: raise ParseError(i)
        if not pf:
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + len(".empty")
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == ".empty"
            if pf: self.lastMatch = ".empty"; i = stop
            if pf:
                pass
                self.stack.append("SET")
                i, pf, tf, ms, tb, ob, lb = self.parseSET(i, pf, tf, ms[:], tb, ob, lb)
                self.stack.pop()
                if not pf: raise ParseError(i)
        if not pf:
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + len(".not(")
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == ".not("
            if pf: self.lastMatch = ".not("; i = stop
            if pf:
                pass
                self.stack.append("CX1")
                i, pf, tf, ms, tb, ob, lb = self.parseCX1(i, pf, tf, ms[:], tb, ob, lb)
                self.stack.pop()
                if not pf: raise ParseError(i)
                while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
                stop = i + len(")")
                if stop > len(self.s): pf = False
                else: pf = self.s[i:stop] == ")"
                if pf: self.lastMatch = ")"; i = stop
                if not pf: raise ParseError(i)
                ob += 'pf = (i < len(self.s)) and not pf'
                lb += " " * (ms[-1] * 4) + ob + chr(10)
                ob = ""
                self.apf = 0
                self.stack.append("SCAN")
                i, pf, tf, ms, tb, ob, lb = self.parseSCAN(i, pf, tf, ms[:], tb, ob, lb)
                self.stack.pop()
                if not pf: raise ParseError(i)
        if not pf:
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + len(".any(")
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == ".any("
            if pf: self.lastMatch = ".any("; i = stop
            if pf:
                pass
                self.stack.append("CX1")
                i, pf, tf, ms, tb, ob, lb = self.parseCX1(i, pf, tf, ms[:], tb, ob, lb)
                self.stack.pop()
                if not pf: raise ParseError(i)
                while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
                stop = i + len(")")
                if stop > len(self.s): pf = False
                else: pf = self.s[i:stop] == ")"
                if pf: self.lastMatch = ")"; i = stop
                if not pf: raise ParseError(i)
                self.stack.append("SCAN")
                i, pf, tf, ms, tb, ob, lb = self.parseSCAN(i, pf, tf, ms[:], tb, ob, lb)
                self.stack.pop()
                if not pf: raise ParseError(i)
        if not pf:
            self.stack.append("SUB")
            i, pf, tf, ms, tb, ob, lb = self.parseSUB(i, pf, tf, ms[:], tb, ob, lb)
            self.stack.pop()
            if pf:
                pass
        if not pf:
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + len("(")
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == "("
            if pf: self.lastMatch = "("; i = stop
            if pf:
                pass
                self.stack.append("TX1")
                i, pf, tf, ms, tb, ob, lb = self.parseTX1(i, pf, tf, ms[:], tb, ob, lb)
                self.stack.pop()
                if not pf: raise ParseError(i)
                while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
                stop = i + len(")")
                if stop > len(self.s): pf = False
                else: pf = self.s[i:stop] == ")"
                if pf: self.lastMatch = ")"; i = stop
                if not pf: raise ParseError(i)
        return i, pf, tf, ms, tb, ob, lb
    def parseTX2(self, i, pf, tf, ms, tb, ob, lb):
        self.stack.append("TX3")
        i, pf, tf, ms, tb, ob, lb = self.parseTX3(i, pf, tf, ms[:], tb, ob, lb)
        self.stack.pop()
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
            while pf:
                self.stack.append("TX3")
                i, pf, tf, ms, tb, ob, lb = self.parseTX3(i, pf, tf, ms[:], tb, ob, lb)
                self.stack.pop()
                if pf:
                    pass
                    if (self.apf == 0):
                        pass
                        ob += 'if not pf: return i, pf, tf, ms, tb, ob, lb'
                        lb += " " * (ms[-1] * 4) + ob + chr(10)
                        ob = ""
                    if not pf: raise ParseError(i)
                    if (self.apf == 2):
                        pass
                        ob += 'return i, pf, tf, ms, tb, ob, lb'
                        lb += " " * (ms[-1] * 4) + ob + chr(10)
                        ob = ""
                    if not pf: raise ParseError(i)
                    self.apf = 1
            pf = True
            if ms[-1]: ms[-1] -= 1
        return i, pf, tf, ms, tb, ob, lb
    def parseTX1(self, i, pf, tf, ms, tb, ob, lb):
        self.stack.append("TX2")
        i, pf, tf, ms, tb, ob, lb = self.parseTX2(i, pf, tf, ms[:], tb, ob, lb)
        self.stack.pop()
        if pf:
            pass
            while pf:
                while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
                stop = i + len("/")
                if stop > len(self.s): pf = False
                else: pf = self.s[i:stop] == "/"
                if pf: self.lastMatch = "/"; i = stop
                if pf:
                    pass
                    ob += 'if not pf:'
                    lb += " " * (ms[-1] * 4) + ob + chr(10)
                    ob = ""
                    ms[-1] += 1
                    self.apf = 2
                    self.stack.append("TX2")
                    i, pf, tf, ms, tb, ob, lb = self.parseTX2(i, pf, tf, ms[:], tb, ob, lb)
                    self.stack.pop()
                    if not pf: raise ParseError(i)
                    self.apf = 0
                    if ms[-1]: ms[-1] -= 1
            pf = True
        return i, pf, tf, ms, tb, ob, lb
    def parseTR(self, i, pf, tf, ms, tb, ob, lb):
        self.stack.append("ID")
        i, pf, tf, ms, tb, ob, lb = self.parseID(i, pf, tf, ms[:], tb, ob, lb)
        self.stack.pop()
        if pf:
            pass
            ob += 'def parse'
            ob += tb
            ob += '(self, i, pf, tf, ms, tb, ob, lb):'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
            ms[-1] += 1
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + len(":")
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == ":"
            if pf: self.lastMatch = ":"; i = stop
            if not pf: raise ParseError(i)
            self.top()
            self.stack.append("TX1")
            i, pf, tf, ms, tb, ob, lb = self.parseTX1(i, pf, tf, ms[:], tb, ob, lb)
            self.stack.pop()
            if not pf: raise ParseError(i)
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + len(";")
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == ";"
            if pf: self.lastMatch = ";"; i = stop
            if not pf: raise ParseError(i)
            ob += 'return i, pf, tf, ms, tb, ob, lb'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
            if ms[-1]: ms[-1] -= 1
        return i, pf, tf, ms, tb, ob, lb
    def parseTVAR(self, i, pf, tf, ms, tb, ob, lb):
        while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
        stop = i + len("~")
        if stop > len(self.s): pf = False
        else: pf = self.s[i:stop] == "~"
        if pf: self.lastMatch = "~"; i = stop
        if pf:
            pass
            ob += '(not '
            self.stack.append("TVAR")
            i, pf, tf, ms, tb, ob, lb = self.parseTVAR(i, pf, tf, ms[:], tb, ob, lb)
            self.stack.pop()
            if not pf: raise ParseError(i)
            ob += ')'
        if not pf:
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + len("?")
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == "?"
            if pf: self.lastMatch = "?"; i = stop
            if pf:
                pass
                self.stack.append("ID")
                i, pf, tf, ms, tb, ob, lb = self.parseID(i, pf, tf, ms[:], tb, ob, lb)
                self.stack.pop()
                if not pf: raise ParseError(i)
                ob += '(self.a'
                ob += tb
                ob += ' == 0)'
        if not pf:
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + len("+")
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == "+"
            if pf: self.lastMatch = "+"; i = stop
            if pf:
                pass
                self.stack.append("ID")
                i, pf, tf, ms, tb, ob, lb = self.parseID(i, pf, tf, ms[:], tb, ob, lb)
                self.stack.pop()
                if not pf: raise ParseError(i)
                ob += '(self.a'
                ob += tb
                ob += ' == 1)'
        if not pf:
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + len("-")
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == "-"
            if pf: self.lastMatch = "-"; i = stop
            if pf:
                pass
                self.stack.append("ID")
                i, pf, tf, ms, tb, ob, lb = self.parseID(i, pf, tf, ms[:], tb, ob, lb)
                self.stack.pop()
                if not pf: raise ParseError(i)
                ob += '(self.a'
                ob += tb
                ob += ' == 2)'
        return i, pf, tf, ms, tb, ob, lb
    def parseAVAR(self, i, pf, tf, ms, tb, ob, lb):
        while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
        stop = i + len("?")
        if stop > len(self.s): pf = False
        else: pf = self.s[i:stop] == "?"
        if pf: self.lastMatch = "?"; i = stop
        if pf:
            pass
            self.stack.append("ID")
            i, pf, tf, ms, tb, ob, lb = self.parseID(i, pf, tf, ms[:], tb, ob, lb)
            self.stack.pop()
            if not pf: raise ParseError(i)
            ob += 'self.a'
            ob += tb
            ob += ' = 0'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
        if not pf:
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + len("+")
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == "+"
            if pf: self.lastMatch = "+"; i = stop
            if pf:
                pass
                self.stack.append("ID")
                i, pf, tf, ms, tb, ob, lb = self.parseID(i, pf, tf, ms[:], tb, ob, lb)
                self.stack.pop()
                if not pf: raise ParseError(i)
                ob += 'self.a'
                ob += tb
                ob += ' = 1'
                lb += " " * (ms[-1] * 4) + ob + chr(10)
                ob = ""
        if not pf:
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + len("-")
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == "-"
            if pf: self.lastMatch = "-"; i = stop
            if pf:
                pass
                self.stack.append("ID")
                i, pf, tf, ms, tb, ob, lb = self.parseID(i, pf, tf, ms[:], tb, ob, lb)
                self.stack.pop()
                if not pf: raise ParseError(i)
                ob += 'self.a'
                ob += tb
                ob += ' = 2'
                lb += " " * (ms[-1] * 4) + ob + chr(10)
                ob = ""
        return i, pf, tf, ms, tb, ob, lb
    def parseEX3(self, i, pf, tf, ms, tb, ob, lb):
        self.stack.append("SUB")
        i, pf, tf, ms, tb, ob, lb = self.parseSUB(i, pf, tf, ms[:], tb, ob, lb)
        self.stack.pop()
        if pf:
            pass
        if not pf:
            self.stack.append("STRING")
            i, pf, tf, ms, tb, ob, lb = self.parseSTRING(i, pf, tf, ms[:], tb, ob, lb)
            self.stack.pop()
            if pf:
                pass
                ob += 'while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1'
                lb += " " * (ms[-1] * 4) + ob + chr(10)
                ob = ""
                ob += 'stop = i + len("'
                ob += tb
                ob += '")'
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
                ob += 'if pf: self.lastMatch = "'
                ob += tb
                ob += '"; i = stop'
                lb += " " * (ms[-1] * 4) + ob + chr(10)
                ob = ""
                self.apf = 0
        if not pf:
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + len("(")
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == "("
            if pf: self.lastMatch = "("; i = stop
            if pf:
                pass
                self.stack.append("EX1")
                i, pf, tf, ms, tb, ob, lb = self.parseEX1(i, pf, tf, ms[:], tb, ob, lb)
                self.stack.pop()
                if not pf: raise ParseError(i)
                while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
                stop = i + len(")")
                if stop > len(self.s): pf = False
                else: pf = self.s[i:stop] == ")"
                if pf: self.lastMatch = ")"; i = stop
                if not pf: raise ParseError(i)
        if not pf:
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + len(".pre")
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == ".pre"
            if pf: self.lastMatch = ".pre"; i = stop
            if pf:
                pass
                while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
                stop = i + len("{")
                if stop > len(self.s): pf = False
                else: pf = self.s[i:stop] == "{"
                if pf: self.lastMatch = "{"; i = stop
                if not pf: raise ParseError(i)
                ob += 'if '
                self.stack.append("TVAR")
                i, pf, tf, ms, tb, ob, lb = self.parseTVAR(i, pf, tf, ms[:], tb, ob, lb)
                self.stack.pop()
                if not pf: raise ParseError(i)
                while pf:
                    while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
                    stop = i + len(",")
                    if stop > len(self.s): pf = False
                    else: pf = self.s[i:stop] == ","
                    if pf: self.lastMatch = ","; i = stop
                    if pf:
                        pass
                        ob += ' and '
                        self.stack.append("TVAR")
                        i, pf, tf, ms, tb, ob, lb = self.parseTVAR(i, pf, tf, ms[:], tb, ob, lb)
                        self.stack.pop()
                        if not pf: raise ParseError(i)
                pf = True
                ob += ':'
                lb += " " * (ms[-1] * 4) + ob + chr(10)
                ob = ""
                ms[-1] += 1
                ob += 'pass'
                lb += " " * (ms[-1] * 4) + ob + chr(10)
                ob = ""
                while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
                stop = i + len("}")
                if stop > len(self.s): pf = False
                else: pf = self.s[i:stop] == "}"
                if pf: self.lastMatch = "}"; i = stop
                if not pf: raise ParseError(i)
                while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
                stop = i + len("{")
                if stop > len(self.s): pf = False
                else: pf = self.s[i:stop] == "{"
                if pf: self.lastMatch = "{"; i = stop
                if not pf: raise ParseError(i)
                self.stack.append("EX1")
                i, pf, tf, ms, tb, ob, lb = self.parseEX1(i, pf, tf, ms[:], tb, ob, lb)
                self.stack.pop()
                if not pf: raise ParseError(i)
                while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
                stop = i + len("}")
                if stop > len(self.s): pf = False
                else: pf = self.s[i:stop] == "}"
                if pf: self.lastMatch = "}"; i = stop
                if not pf: raise ParseError(i)
                if ms[-1]: ms[-1] -= 1
        if not pf:
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + len(".post")
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == ".post"
            if pf: self.lastMatch = ".post"; i = stop
            if pf:
                pass
                while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
                stop = i + len("{")
                if stop > len(self.s): pf = False
                else: pf = self.s[i:stop] == "{"
                if pf: self.lastMatch = "{"; i = stop
                if not pf: raise ParseError(i)
                self.stack.append("AVAR")
                i, pf, tf, ms, tb, ob, lb = self.parseAVAR(i, pf, tf, ms[:], tb, ob, lb)
                self.stack.pop()
                if not pf: raise ParseError(i)
                while pf:
                    while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
                    stop = i + len(",")
                    if stop > len(self.s): pf = False
                    else: pf = self.s[i:stop] == ","
                    if pf: self.lastMatch = ","; i = stop
                    if pf:
                        pass
                        self.stack.append("AVAR")
                        i, pf, tf, ms, tb, ob, lb = self.parseAVAR(i, pf, tf, ms[:], tb, ob, lb)
                        self.stack.pop()
                        if not pf: raise ParseError(i)
                pf = True
                while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
                stop = i + len("}")
                if stop > len(self.s): pf = False
                else: pf = self.s[i:stop] == "}"
                if pf: self.lastMatch = "}"; i = stop
                if not pf: raise ParseError(i)
        if not pf:
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + len(".fork")
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == ".fork"
            if pf: self.lastMatch = ".fork"; i = stop
            if pf:
                pass
        if not pf:
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + len(".join")
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == ".join"
            if pf: self.lastMatch = ".join"; i = stop
            if pf:
                pass
        if not pf:
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + len(".top")
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == ".top"
            if pf: self.lastMatch = ".top"; i = stop
            if pf:
                pass
                ob += 'self.top()'
                lb += " " * (ms[-1] * 4) + ob + chr(10)
                ob = ""
        if not pf:
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + len(".empty")
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == ".empty"
            if pf: self.lastMatch = ".empty"; i = stop
            if pf:
                pass
                self.stack.append("SET")
                i, pf, tf, ms, tb, ob, lb = self.parseSET(i, pf, tf, ms[:], tb, ob, lb)
                self.stack.pop()
                if not pf: raise ParseError(i)
        if not pf:
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + len(".litchr")
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == ".litchr"
            if pf: self.lastMatch = ".litchr"; i = stop
            if pf:
                pass
                self.stack.append("SET")
                i, pf, tf, ms, tb, ob, lb = self.parseSET(i, pf, tf, ms[:], tb, ob, lb)
                self.stack.pop()
                if not pf: raise ParseError(i)
                ob += 'tb = str(ord(self.s[i]))'
                lb += " " * (ms[-1] * 4) + ob + chr(10)
                ob = ""
                ob += 'i += 1'
                lb += " " * (ms[-1] * 4) + ob + chr(10)
                ob = ""
        if not pf:
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + len(".pass")
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == ".pass"
            if pf: self.lastMatch = ".pass"; i = stop
            if pf:
                pass
                ob += 'i = 0'
                lb += " " * (ms[-1] * 4) + ob + chr(10)
                ob = ""
        if not pf:
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + len("$")
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == "$"
            if pf: self.lastMatch = "$"; i = stop
            if pf:
                pass
                self.stack.append("SET")
                i, pf, tf, ms, tb, ob, lb = self.parseSET(i, pf, tf, ms[:], tb, ob, lb)
                self.stack.pop()
                if not pf: raise ParseError(i)
                ob += 'while pf:'
                lb += " " * (ms[-1] * 4) + ob + chr(10)
                ob = ""
                ms[-1] += 1
                self.apf = 1
                self.stack.append("EX3")
                i, pf, tf, ms, tb, ob, lb = self.parseEX3(i, pf, tf, ms[:], tb, ob, lb)
                self.stack.pop()
                if not pf: raise ParseError(i)
                if ms[-1]: ms[-1] -= 1
                self.apf = 2
                self.stack.append("SET")
                i, pf, tf, ms, tb, ob, lb = self.parseSET(i, pf, tf, ms[:], tb, ob, lb)
                self.stack.pop()
                if not pf: raise ParseError(i)
        return i, pf, tf, ms, tb, ob, lb
    def parseEX2(self, i, pf, tf, ms, tb, ob, lb):
        self.stack.append("EX3")
        i, pf, tf, ms, tb, ob, lb = self.parseEX3(i, pf, tf, ms[:], tb, ob, lb)
        self.stack.pop()
        if pf:
            pass
            ms.append(ms[-1])
            ob += 'if pf:'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
            ms[-1] += 1
            ob += 'pass'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
            self.apf = 1
        if not pf:
            self.stack.append("OUTPUT")
            i, pf, tf, ms, tb, ob, lb = self.parseOUTPUT(i, pf, tf, ms[:], tb, ob, lb)
            self.stack.pop()
            if pf:
                pass
                ms.append(ms[-1])
        if pf:
            pass
            while pf:
                self.stack.append("EX3")
                i, pf, tf, ms, tb, ob, lb = self.parseEX3(i, pf, tf, ms[:], tb, ob, lb)
                self.stack.pop()
                if pf:
                    pass
                    if (self.apf == 2):
                        pass
                        ob += 'raise ParseError(i)'
                        lb += " " * (ms[-1] * 4) + ob + chr(10)
                        ob = ""
                    if not pf: raise ParseError(i)
                    if (self.apf == 0):
                        pass
                        ob += 'if not pf: raise ParseError(i)'
                        lb += " " * (ms[-1] * 4) + ob + chr(10)
                        ob = ""
                    if not pf: raise ParseError(i)
                    self.apf = 1
                if not pf:
                    self.stack.append("OUTPUT")
                    i, pf, tf, ms, tb, ob, lb = self.parseOUTPUT(i, pf, tf, ms[:], tb, ob, lb)
                    self.stack.pop()
                    if pf:
                        pass
            pf = True
            ms.pop()
            self.apf = 0
        return i, pf, tf, ms, tb, ob, lb
    def parseEX1(self, i, pf, tf, ms, tb, ob, lb):
        self.stack.append("EX2")
        i, pf, tf, ms, tb, ob, lb = self.parseEX2(i, pf, tf, ms[:], tb, ob, lb)
        self.stack.pop()
        if pf:
            pass
            while pf:
                while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
                stop = i + len("/")
                if stop > len(self.s): pf = False
                else: pf = self.s[i:stop] == "/"
                if pf: self.lastMatch = "/"; i = stop
                if pf:
                    pass
                    ob += 'if not pf:'
                    lb += " " * (ms[-1] * 4) + ob + chr(10)
                    ob = ""
                    ms[-1] += 1
                    self.apf = 2
                    self.stack.append("EX2")
                    i, pf, tf, ms, tb, ob, lb = self.parseEX2(i, pf, tf, ms[:], tb, ob, lb)
                    self.stack.pop()
                    if not pf: raise ParseError(i)
                    self.apf = 0
                    if ms[-1]: ms[-1] -= 1
            pf = True
        return i, pf, tf, ms, tb, ob, lb
    def parsePR(self, i, pf, tf, ms, tb, ob, lb):
        self.stack.append("ID")
        i, pf, tf, ms, tb, ob, lb = self.parseID(i, pf, tf, ms[:], tb, ob, lb)
        self.stack.pop()
        if pf:
            pass
            ob += 'def parse'
            ob += tb
            ob += '(self, i, pf, tf, ms, tb, ob, lb):'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
            ms[-1] += 1
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + len("=")
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == "="
            if pf: self.lastMatch = "="; i = stop
            if not pf: raise ParseError(i)
            self.top()
            self.stack.append("EX1")
            i, pf, tf, ms, tb, ob, lb = self.parseEX1(i, pf, tf, ms[:], tb, ob, lb)
            self.stack.pop()
            if not pf: raise ParseError(i)
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + len(";")
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == ";"
            if pf: self.lastMatch = ";"; i = stop
            if not pf: raise ParseError(i)
            ob += 'return i, pf, tf, ms, tb, ob, lb'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
            if ms[-1]: ms[-1] -= 1
        return i, pf, tf, ms, tb, ob, lb
    def parseTY(self, i, pf, tf, ms, tb, ob, lb):
        while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
        stop = i + len("bool")
        if stop > len(self.s): pf = False
        else: pf = self.s[i:stop] == "bool"
        if pf: self.lastMatch = "bool"; i = stop
        if pf:
            pass
            ob += '0'
        return i, pf, tf, ms, tb, ob, lb
    def parseDR(self, i, pf, tf, ms, tb, ob, lb):
        self.stack.append("ID")
        i, pf, tf, ms, tb, ob, lb = self.parseID(i, pf, tf, ms[:], tb, ob, lb)
        self.stack.pop()
        if pf:
            pass
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + len(":")
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == ":"
            if pf: self.lastMatch = ":"; i = stop
            if not pf: raise ParseError(i)
            ob += 'self.a'
            ob += tb
            ob += ' = '
            self.stack.append("TY")
            i, pf, tf, ms, tb, ob, lb = self.parseTY(i, pf, tf, ms[:], tb, ob, lb)
            self.stack.pop()
            if not pf: raise ParseError(i)
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + len(";")
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == ";"
            if pf: self.lastMatch = ";"; i = stop
            if not pf: raise ParseError(i)
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
        return i, pf, tf, ms, tb, ob, lb
    def parseZADDY(self, i, pf, tf, ms, tb, ob, lb):
        while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
        stop = i + len(".syntax")
        if stop > len(self.s): pf = False
        else: pf = self.s[i:stop] == ".syntax"
        if pf: self.lastMatch = ".syntax"; i = stop
        if pf:
            pass
            self.stack.append("ID")
            i, pf, tf, ms, tb, ob, lb = self.parseID(i, pf, tf, ms[:], tb, ob, lb)
            self.stack.pop()
            if not pf: raise ParseError(i)
            ob += 'from rpython.rlib.rfile import create_stdio'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
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
            ob += 'class ParseError(Exception):'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
            ms[-1] += 1
            ob += 'def __init__(self, i): self.i = i'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
            if ms[-1]: ms[-1] -= 1
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
            ob += 'try:'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
            ms[-1] += 1
            ob += '_, _, _, _, _, _, lb = parser.parse()'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
            ob += 'stdout.write(lb)'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
            ob += 'return 0'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
            if ms[-1]: ms[-1] -= 1
            ob += 'except ParseError as pe:'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
            ms[-1] += 1
            ob += 'line = parser.s.count(chr(10), 0, pe.i) + 1'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
            ob += 'stderr.write(("Error at input location: %d (line %d)" % (pe.i, line)) + chr(10))'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
            ob += 'stderr.write(("Backtrace: %s" % " ".join(parser.stack)) + chr(10))'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
            ob += 'stderr.write(("Last matching token: '
            ob += chr(39)
            ob += '%s'
            ob += chr(39)
            ob += '" % parser.lastMatch) + chr(10))'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
            ob += 'return 1'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
            if ms[-1]: ms[-1] -= 1
            if ms[-1]: ms[-1] -= 1
            ob += 'class '
            ob += tb
            ob += 'Parser(object):'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
            ms[-1] += 1
            ob += 'lastMatch = ""'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
            ob += 'def __init__(self, s): self.s = s; self.stack = []; self.top()'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
            ob += 'def parse(self):'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
            ms[-1] += 1
            ob += 'self.top()'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
            ob += '# i, pf, tf, ms, tb, ob, lb'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
            ob += 'return self.parse'
            ob += tb
            ob += '(0, False, False, [0], "", "", "")'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
            if ms[-1]: ms[-1] -= 1
            while pf:
                self.stack.append("PR")
                i, pf, tf, ms, tb, ob, lb = self.parsePR(i, pf, tf, ms[:], tb, ob, lb)
                self.stack.pop()
            pf = True
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + len(".tokens")
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == ".tokens"
            if pf: self.lastMatch = ".tokens"; i = stop
            if not pf: raise ParseError(i)
            while pf:
                self.stack.append("TR")
                i, pf, tf, ms, tb, ob, lb = self.parseTR(i, pf, tf, ms[:], tb, ob, lb)
                self.stack.pop()
            pf = True
            ob += 'def top(self):'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
            ms[-1] += 1
            ob += 'pass'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + len(".domain")
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == ".domain"
            if pf: self.lastMatch = ".domain"; i = stop
            if not pf: raise ParseError(i)
            while pf:
                self.stack.append("DR")
                i, pf, tf, ms, tb, ob, lb = self.parseDR(i, pf, tf, ms[:], tb, ob, lb)
                self.stack.pop()
            pf = True
            if ms[-1]: ms[-1] -= 1
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + len(".end")
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == ".end"
            if pf: self.lastMatch = ".end"; i = stop
            if not pf: raise ParseError(i)
        return i, pf, tf, ms, tb, ob, lb
    def parseWS(self, i, pf, tf, ms, tb, ob, lb):
        pf = True
        while pf:
            pf = (i < len(self.s)) and ord(self.s[i]) == 9 or ord(self.s[i]) == 10 or ord(self.s[i]) == 13 or ord(self.s[i]) == 32
            if pf:
                if tf: tb += self.s[i]
                i += 1
        pf = True
        if pf:
            pass
        return i, pf, tf, ms, tb, ob, lb
    def parseDIGIT(self, i, pf, tf, ms, tb, ob, lb):
        pf = (i < len(self.s)) and 48 <= ord(self.s[i]) <= 57
        if pf:
            if tf: tb += self.s[i]
            i += 1
        if pf:
            pass
        return i, pf, tf, ms, tb, ob, lb
    def parseALPHA(self, i, pf, tf, ms, tb, ob, lb):
        pf = (i < len(self.s)) and 65 <= ord(self.s[i]) <= 90 or 97 <= ord(self.s[i]) <= 122
        if pf:
            if tf: tb += self.s[i]
            i += 1
        if pf:
            pass
        return i, pf, tf, ms, tb, ob, lb
    def parseSQUOTE(self, i, pf, tf, ms, tb, ob, lb):
        self.stack.append("WS")
        i, pf, tf, ms, tb, ob, lb = self.parseWS(i, pf, tf, ms[:], tb, ob, lb)
        self.stack.pop()
        if pf:
            pass
            pf = (i < len(self.s)) and ord(self.s[i]) == 39
            if pf:
                if tf: tb += self.s[i]
                i += 1
            if not pf: return i, pf, tf, ms, tb, ob, lb
        return i, pf, tf, ms, tb, ob, lb
    def parseSTRING(self, i, pf, tf, ms, tb, ob, lb):
        self.stack.append("WS")
        i, pf, tf, ms, tb, ob, lb = self.parseWS(i, pf, tf, ms[:], tb, ob, lb)
        self.stack.pop()
        if pf:
            pass
            pf = (i < len(self.s)) and ord(self.s[i]) == 39
            if pf:
                if tf: tb += self.s[i]
                i += 1
            if not pf: return i, pf, tf, ms, tb, ob, lb
            tb = ""
            tf = True
            while pf:
                pf = (i < len(self.s)) and ord(self.s[i]) == 10 or ord(self.s[i]) == 13 or ord(self.s[i]) == 39
                pf = (i < len(self.s)) and not pf
                if pf:
                    tb += self.s[i]
                    i += 1
            pf = True
            tf = False
            pf = (i < len(self.s)) and ord(self.s[i]) == 39
            if pf:
                i += 1
            if not pf: return i, pf, tf, ms, tb, ob, lb
        return i, pf, tf, ms, tb, ob, lb
    def parseNUMBER(self, i, pf, tf, ms, tb, ob, lb):
        self.stack.append("WS")
        i, pf, tf, ms, tb, ob, lb = self.parseWS(i, pf, tf, ms[:], tb, ob, lb)
        self.stack.pop()
        if pf:
            pass
            tb = ""
            tf = True
            self.stack.append("DIGIT")
            i, pf, tf, ms, tb, ob, lb = self.parseDIGIT(i, pf, tf, ms[:], tb, ob, lb)
            self.stack.pop()
            if not pf: return i, pf, tf, ms, tb, ob, lb
            while pf:
                self.stack.append("DIGIT")
                i, pf, tf, ms, tb, ob, lb = self.parseDIGIT(i, pf, tf, ms[:], tb, ob, lb)
                self.stack.pop()
            pf = True
            tf = False
        return i, pf, tf, ms, tb, ob, lb
    def parseID(self, i, pf, tf, ms, tb, ob, lb):
        self.stack.append("WS")
        i, pf, tf, ms, tb, ob, lb = self.parseWS(i, pf, tf, ms[:], tb, ob, lb)
        self.stack.pop()
        if pf:
            pass
            tb = ""
            tf = True
            self.stack.append("ALPHA")
            i, pf, tf, ms, tb, ob, lb = self.parseALPHA(i, pf, tf, ms[:], tb, ob, lb)
            self.stack.pop()
            if not pf: return i, pf, tf, ms, tb, ob, lb
            while pf:
                self.stack.append("ALPHA")
                i, pf, tf, ms, tb, ob, lb = self.parseALPHA(i, pf, tf, ms[:], tb, ob, lb)
                self.stack.pop()
                if pf:
                    pass
                if not pf:
                    self.stack.append("DIGIT")
                    i, pf, tf, ms, tb, ob, lb = self.parseDIGIT(i, pf, tf, ms[:], tb, ob, lb)
                    self.stack.pop()
                    if pf:
                        pass
            pf = True
            tf = False
        return i, pf, tf, ms, tb, ob, lb
    def top(self):
        pass
        self.apf = 0
        self.atf = 0
