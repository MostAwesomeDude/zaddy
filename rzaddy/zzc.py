from rpython.rlib.rfile import create_stdio
def target(driver, *args):
    driver.exe_name = "ZADDY".lower() + "c"
    return main, None
def main(argv):
    stdin, stdout, stderr = create_stdio()
    parser = ZADDYParser(stdin.read())
    try:
        parser.parse()
        return 0
    except ValueError:
        line = parser.s.count(chr(10), 0, parser.i) + 1
        stderr.write(("Error at input location: %d (line %d)" % (parser.i, line)) + chr(10))
        stderr.write(("Backtrace: %s" % " ".join([frame[0] for frame in parser.stack])) + chr(10))
        stderr.write(("Last matching token: '%s'" % parser.lastMatch) + chr(10))
        return 1
class ZADDYParser(object):
    u = 0
    pf = tf = False
    of = True
    l1 = tb = ""
    m = 0
    ob = ""
    i = 0
    lastMatch = ""
    def __init__(self, s): self.s = s; self.stack = []; self.top()
    def parse(self): self.top(); return self.parseZADDY()
    def unique(self):
        if not self.l1: self.l1 = str(self.u); self.u += 1
        return self.l1
    def error(self): raise ValueError("meh")
    def eatWhitespace(self):
        while self.i < len(self.s) and self.s[self.i] in (" " + chr(10)): self.i += 1
    def matches(self, token):
        stop = self.i + len(token)
        if stop > len(self.s): self.pf = False
        else: self.pf = self.s[self.i:stop] == token
        if self.pf: self.lastMatch = token
    def parseOUT1(self):
        self.eatWhitespace()
        self.matches("*")
        if self.pf: self.i += len("*")
        if self.pf:
            pass
            if self.of:
                self.ob += 'self.ob += self.tb'
                print " " * (self.m * 4) + self.ob
                self.ob = ""
        if not self.pf:
            self.stack.append(("STRING", self.l1))
            self.l1 = ""
            self.parseSTRING()
            self.stack.pop()
            if self.pf:
                pass
                if self.of:
                    self.ob += 'self.ob += '
                    self.ob += chr(39)
                    self.ob += self.tb
                    self.ob += chr(39)
                    print " " * (self.m * 4) + self.ob
                    self.ob = ""
        if not self.pf:
            self.stack.append(("NUMBER", self.l1))
            self.l1 = ""
            self.parseNUMBER()
            self.stack.pop()
            if self.pf:
                pass
                if self.of:
                    self.ob += 'self.ob += chr('
                    self.ob += self.tb
                    self.ob += ')'
                    print " " * (self.m * 4) + self.ob
                    self.ob = ""
        if not self.pf:
            self.eatWhitespace()
            self.matches("#")
            if self.pf: self.i += len("#")
            if self.pf:
                pass
                if self.of:
                    self.ob += 'self.ob += self.unique()'
                    print " " * (self.m * 4) + self.ob
                    self.ob = ""
        if not self.pf:
            self.eatWhitespace()
            self.matches(".lm+")
            if self.pf: self.i += len(".lm+")
            if self.pf:
                pass
                if self.of:
                    self.ob += 'self.m += 1'
                    print " " * (self.m * 4) + self.ob
                    self.ob = ""
        if not self.pf:
            self.eatWhitespace()
            self.matches(".lm-")
            if self.pf: self.i += len(".lm-")
            if self.pf:
                pass
                if self.of:
                    self.ob += 'if self.m: self.m -= 1'
                    print " " * (self.m * 4) + self.ob
                    self.ob = ""
        if not self.pf:
            self.eatWhitespace()
            self.matches(".nl")
            if self.pf: self.i += len(".nl")
            if self.pf:
                pass
                if self.of:
                    self.ob += 'print " " * (self.m * 4) + self.ob'
                    print " " * (self.m * 4) + self.ob
                    self.ob = ""
                    self.ob += 'self.ob = ""'
                    print " " * (self.m * 4) + self.ob
                    self.ob = ""
    def parseOUTPUT(self):
        self.eatWhitespace()
        self.matches(".out")
        if self.pf: self.i += len(".out")
        if self.pf:
            pass
            self.eatWhitespace()
            self.matches("(")
            if self.pf: self.i += len("(")
            if not self.pf: self.error()
            if (self.aof == 0):
                pass
                if self.of:
                    self.ob += 'if self.of:'
                    print " " * (self.m * 4) + self.ob
                    self.ob = ""
                    self.m += 1
                if True:
                    pass
                    while self.pf:
                        self.stack.append(("OUT1", self.l1))
                        self.l1 = ""
                        self.parseOUT1()
                        self.stack.pop()
                    self.pf = True
                    if self.of:
                        if self.m: self.m -= 1
            if not self.pf: self.error()
            if (self.aof == 2):
                pass
                self.of = False
                if self.pf:
                    pass
                    while self.pf:
                        self.stack.append(("OUT1", self.l1))
                        self.l1 = ""
                        self.parseOUT1()
                        self.stack.pop()
                    self.pf = True
                    self.of = True
            if not self.pf: self.error()
            self.eatWhitespace()
            self.matches(")")
            if self.pf: self.i += len(")")
            if not self.pf: self.error()
    def parseCX3(self):
        self.stack.append(("NUMBER", self.l1))
        self.l1 = ""
        self.parseNUMBER()
        self.stack.pop()
        if self.pf:
            pass
        if not self.pf:
            self.stack.append(("SQUOTE", self.l1))
            self.l1 = ""
            self.parseSQUOTE()
            self.stack.pop()
            if self.pf:
                pass
                self.tb = str(ord(self.s[self.i]))
                self.i += 1
    def parseCX2(self):
        self.stack.append(("CX3", self.l1))
        self.l1 = ""
        self.parseCX3()
        self.stack.pop()
        if self.pf:
            pass
            self.eatWhitespace()
            self.matches(":")
            if self.pf: self.i += len(":")
            if self.pf:
                pass
                if self.of:
                    self.ob += self.tb
                    self.ob += ' <= ord(self.s[self.i]) <= '
                self.stack.append(("CX3", self.l1))
                self.l1 = ""
                self.parseCX3()
                self.stack.pop()
                if not self.pf: self.error()
                if self.of:
                    self.ob += self.tb
            if not self.pf:
                self.pf = True
                if self.pf:
                    pass
                    if self.of:
                        self.ob += 'ord(self.s[self.i]) == '
                        self.ob += self.tb
            if not self.pf: self.error()
    def parseCX1(self):
        if self.of:
            self.ob += 'self.pf = '
        if True:
            pass
            self.stack.append(("CX2", self.l1))
            self.l1 = ""
            self.parseCX2()
            self.stack.pop()
            if not self.pf: self.error()
            while self.pf:
                self.eatWhitespace()
                self.matches("!")
                if self.pf: self.i += len("!")
                if self.pf:
                    pass
                    if self.of:
                        self.ob += ' or '
                    self.stack.append(("CX2", self.l1))
                    self.l1 = ""
                    self.parseCX2()
                    self.stack.pop()
                    if not self.pf: self.error()
            self.pf = True
            if self.of:
                print " " * (self.m * 4) + self.ob
                self.ob = ""
            self.apf = 0
    def parseSCAN(self):
        if (self.apf == 1):
            pass
            if (self.atf == 1):
                pass
                if self.of:
                    self.ob += 'self.tb += self.s[self.i]'
                    print " " * (self.m * 4) + self.ob
                    self.ob = ""
                if True:
                    pass
            if self.pf:
                pass
                if (self.atf == 0):
                    pass
                    if self.of:
                        self.ob += 'if self.tf: self.tb += self.s[self.i]'
                        print " " * (self.m * 4) + self.ob
                        self.ob = ""
                    if True:
                        pass
                if not self.pf: self.error()
                if self.of:
                    self.ob += 'self.i += 1'
                    print " " * (self.m * 4) + self.ob
                    self.ob = ""
        if self.pf:
            pass
            if (self.apf == 0):
                pass
                if self.of:
                    self.ob += 'if self.pf:'
                    print " " * (self.m * 4) + self.ob
                    self.ob = ""
                    self.m += 1
                if True:
                    pass
                    if (self.atf == 1):
                        pass
                        if self.of:
                            self.ob += 'self.tb += self.s[self.i]'
                            print " " * (self.m * 4) + self.ob
                            self.ob = ""
                        if True:
                            pass
                    if not self.pf: self.error()
                    if (self.atf == 0):
                        pass
                        if self.of:
                            self.ob += 'if self.tf: self.tb += self.s[self.i]'
                            print " " * (self.m * 4) + self.ob
                            self.ob = ""
                        if True:
                            pass
                    if not self.pf: self.error()
                    if self.of:
                        self.ob += 'self.i += 1'
                        print " " * (self.m * 4) + self.ob
                        self.ob = ""
                        if self.m: self.m -= 1
            if not self.pf: self.error()
    def parseSUB(self):
        self.stack.append(("ID", self.l1))
        self.l1 = ""
        self.parseID()
        self.stack.pop()
        if self.pf:
            pass
            if self.of:
                self.ob += 'self.stack.append(("'
                self.ob += self.tb
                self.ob += '", self.l1))'
                print " " * (self.m * 4) + self.ob
                self.ob = ""
                self.ob += 'self.l1 = ""'
                print " " * (self.m * 4) + self.ob
                self.ob = ""
                self.ob += 'self.parse'
                self.ob += self.tb
                self.ob += '()'
                print " " * (self.m * 4) + self.ob
                self.ob = ""
                self.ob += 'self.stack.pop()'
                print " " * (self.m * 4) + self.ob
                self.ob = ""
            self.top()
    def parseSET(self):
        if (not (self.apf == 1)):
            pass
            if self.of:
                self.ob += 'self.pf = True'
                print " " * (self.m * 4) + self.ob
                self.ob = ""
            if True:
                pass
        if self.pf:
            pass
            self.apf = 1
    def parseTX3(self):
        self.eatWhitespace()
        self.matches(".token")
        if self.pf: self.i += len(".token")
        if self.pf:
            pass
            if self.of:
                self.ob += 'self.tb = ""'
                print " " * (self.m * 4) + self.ob
                self.ob = ""
            if (not (self.atf == 1)):
                pass
                if self.of:
                    self.ob += 'self.tf = True'
                    print " " * (self.m * 4) + self.ob
                    self.ob = ""
                if True:
                    pass
            if not self.pf: self.error()
            self.atf = 1
        if not self.pf:
            self.eatWhitespace()
            self.matches(".tokout")
            if self.pf: self.i += len(".tokout")
            if self.pf:
                pass
                if (not (self.atf == 2)):
                    pass
                    if self.of:
                        self.ob += 'self.tf = False'
                        print " " * (self.m * 4) + self.ob
                        self.ob = ""
                    if True:
                        pass
                if not self.pf: self.error()
                self.atf = 2
        if not self.pf:
            self.eatWhitespace()
            self.matches("$")
            if self.pf: self.i += len("$")
            if self.pf:
                pass
                self.stack.append(("SET", self.l1))
                self.l1 = ""
                self.parseSET()
                self.stack.pop()
                if not self.pf: self.error()
                if self.of:
                    self.ob += 'while self.pf:'
                    print " " * (self.m * 4) + self.ob
                    self.ob = ""
                    self.m += 1
                self.apf = 1
                self.stack.append(("TX3", self.l1))
                self.l1 = ""
                self.parseTX3()
                self.stack.pop()
                if not self.pf: self.error()
                if self.of:
                    if self.m: self.m -= 1
                self.apf = 2
        if self.pf:
            pass
            self.stack.append(("SET", self.l1))
            self.l1 = ""
            self.parseSET()
            self.stack.pop()
            if not self.pf: self.error()
        if not self.pf:
            self.eatWhitespace()
            self.matches(".empty")
            if self.pf: self.i += len(".empty")
            if self.pf:
                pass
                self.stack.append(("SET", self.l1))
                self.l1 = ""
                self.parseSET()
                self.stack.pop()
                if not self.pf: self.error()
        if not self.pf:
            self.eatWhitespace()
            self.matches(".not(")
            if self.pf: self.i += len(".not(")
            if self.pf:
                pass
                self.stack.append(("CX1", self.l1))
                self.l1 = ""
                self.parseCX1()
                self.stack.pop()
                if not self.pf: self.error()
                self.eatWhitespace()
                self.matches(")")
                if self.pf: self.i += len(")")
                if not self.pf: self.error()
                if self.of:
                    self.ob += 'self.pf = not self.pf'
                    print " " * (self.m * 4) + self.ob
                    self.ob = ""
                self.apf = 0
                self.stack.append(("SCAN", self.l1))
                self.l1 = ""
                self.parseSCAN()
                self.stack.pop()
                if not self.pf: self.error()
        if not self.pf:
            self.eatWhitespace()
            self.matches(".any(")
            if self.pf: self.i += len(".any(")
            if self.pf:
                pass
                self.stack.append(("CX1", self.l1))
                self.l1 = ""
                self.parseCX1()
                self.stack.pop()
                if not self.pf: self.error()
                self.eatWhitespace()
                self.matches(")")
                if self.pf: self.i += len(")")
                if not self.pf: self.error()
                self.stack.append(("SCAN", self.l1))
                self.l1 = ""
                self.parseSCAN()
                self.stack.pop()
                if not self.pf: self.error()
        if not self.pf:
            self.stack.append(("SUB", self.l1))
            self.l1 = ""
            self.parseSUB()
            self.stack.pop()
            if self.pf:
                pass
        if not self.pf:
            self.eatWhitespace()
            self.matches("(")
            if self.pf: self.i += len("(")
            if self.pf:
                pass
                self.stack.append(("TX1", self.l1))
                self.l1 = ""
                self.parseTX1()
                self.stack.pop()
                if not self.pf: self.error()
                self.eatWhitespace()
                self.matches(")")
                if self.pf: self.i += len(")")
                if not self.pf: self.error()
    def parseTX2(self):
        self.stack.append(("TX3", self.l1))
        self.l1 = ""
        self.parseTX3()
        self.stack.pop()
        if self.pf:
            pass
            if self.of:
                self.ob += 'if self.pf:'
                print " " * (self.m * 4) + self.ob
                self.ob = ""
                self.m += 1
                self.ob += 'pass'
                print " " * (self.m * 4) + self.ob
                self.ob = ""
            self.apf = 1
            while self.pf:
                self.stack.append(("TX3", self.l1))
                self.l1 = ""
                self.parseTX3()
                self.stack.pop()
                if self.pf:
                    pass
                    if (not (self.apf == 1)):
                        pass
                        if self.of:
                            self.ob += 'if not self.pf: return'
                            print " " * (self.m * 4) + self.ob
                            self.ob = ""
                        if True:
                            pass
                    if not self.pf: self.error()
                    self.apf = 1
            self.pf = True
            if self.of:
                if self.m: self.m -= 1
    def parseTX1(self):
        self.stack.append(("TX2", self.l1))
        self.l1 = ""
        self.parseTX2()
        self.stack.pop()
        if self.pf:
            pass
            while self.pf:
                self.eatWhitespace()
                self.matches("/")
                if self.pf: self.i += len("/")
                if self.pf:
                    pass
                    if self.of:
                        self.ob += 'if not self.pf:'
                        print " " * (self.m * 4) + self.ob
                        self.ob = ""
                        self.m += 1
                    self.apf = 2
                    self.stack.append(("TX2", self.l1))
                    self.l1 = ""
                    self.parseTX2()
                    self.stack.pop()
                    if not self.pf: self.error()
                    if self.of:
                        if self.m: self.m -= 1
                    self.apf = 0
            self.pf = True
    def parseTR(self):
        self.stack.append(("ID", self.l1))
        self.l1 = ""
        self.parseID()
        self.stack.pop()
        if self.pf:
            pass
            if self.of:
                self.ob += 'def parse'
                self.ob += self.tb
                self.ob += '(self):'
                print " " * (self.m * 4) + self.ob
                self.ob = ""
                self.m += 1
            self.eatWhitespace()
            self.matches(":")
            if self.pf: self.i += len(":")
            if not self.pf: self.error()
            self.top()
            self.stack.append(("TX1", self.l1))
            self.l1 = ""
            self.parseTX1()
            self.stack.pop()
            if not self.pf: self.error()
            self.eatWhitespace()
            self.matches(";")
            if self.pf: self.i += len(";")
            if not self.pf: self.error()
            if self.of:
                if self.m: self.m -= 1
    def parseTVAR(self):
        self.eatWhitespace()
        self.matches("~")
        if self.pf: self.i += len("~")
        if self.pf:
            pass
            if self.of:
                self.ob += '(not '
            self.stack.append(("TVAR", self.l1))
            self.l1 = ""
            self.parseTVAR()
            self.stack.pop()
            if not self.pf: self.error()
            if self.of:
                self.ob += ')'
        if not self.pf:
            self.eatWhitespace()
            self.matches("?")
            if self.pf: self.i += len("?")
            if self.pf:
                pass
                self.stack.append(("ID", self.l1))
                self.l1 = ""
                self.parseID()
                self.stack.pop()
                if not self.pf: self.error()
                if self.of:
                    self.ob += '(self.a'
                    self.ob += self.tb
                    self.ob += ' == 0)'
        if not self.pf:
            self.eatWhitespace()
            self.matches("+")
            if self.pf: self.i += len("+")
            if self.pf:
                pass
                self.stack.append(("ID", self.l1))
                self.l1 = ""
                self.parseID()
                self.stack.pop()
                if not self.pf: self.error()
                if self.of:
                    self.ob += '(self.a'
                    self.ob += self.tb
                    self.ob += ' == 1)'
        if not self.pf:
            self.eatWhitespace()
            self.matches("-")
            if self.pf: self.i += len("-")
            if self.pf:
                pass
                self.stack.append(("ID", self.l1))
                self.l1 = ""
                self.parseID()
                self.stack.pop()
                if not self.pf: self.error()
                if self.of:
                    self.ob += '(self.a'
                    self.ob += self.tb
                    self.ob += ' == 2)'
    def parseAVAR(self):
        self.eatWhitespace()
        self.matches("?")
        if self.pf: self.i += len("?")
        if self.pf:
            pass
            self.stack.append(("ID", self.l1))
            self.l1 = ""
            self.parseID()
            self.stack.pop()
            if not self.pf: self.error()
            if self.of:
                self.ob += 'self.a'
                self.ob += self.tb
                self.ob += ' = 0'
                print " " * (self.m * 4) + self.ob
                self.ob = ""
        if not self.pf:
            self.eatWhitespace()
            self.matches("+")
            if self.pf: self.i += len("+")
            if self.pf:
                pass
                self.stack.append(("ID", self.l1))
                self.l1 = ""
                self.parseID()
                self.stack.pop()
                if not self.pf: self.error()
                if self.of:
                    self.ob += 'self.a'
                    self.ob += self.tb
                    self.ob += ' = 1'
                    print " " * (self.m * 4) + self.ob
                    self.ob = ""
        if not self.pf:
            self.eatWhitespace()
            self.matches("-")
            if self.pf: self.i += len("-")
            if self.pf:
                pass
                self.stack.append(("ID", self.l1))
                self.l1 = ""
                self.parseID()
                self.stack.pop()
                if not self.pf: self.error()
                if self.of:
                    self.ob += 'self.a'
                    self.ob += self.tb
                    self.ob += ' = 2'
                    print " " * (self.m * 4) + self.ob
                    self.ob = ""
    def parseEX3(self):
        self.stack.append(("SUB", self.l1))
        self.l1 = ""
        self.parseSUB()
        self.stack.pop()
        if self.pf:
            pass
        if not self.pf:
            self.stack.append(("STRING", self.l1))
            self.l1 = ""
            self.parseSTRING()
            self.stack.pop()
            if self.pf:
                pass
                if self.of:
                    self.ob += 'self.eatWhitespace()'
                    print " " * (self.m * 4) + self.ob
                    self.ob = ""
                    self.ob += 'self.matches("'
                    self.ob += self.tb
                    self.ob += '")'
                    print " " * (self.m * 4) + self.ob
                    self.ob = ""
                    self.ob += 'if self.pf: self.i += len("'
                    self.ob += self.tb
                    self.ob += '")'
                    print " " * (self.m * 4) + self.ob
                    self.ob = ""
                self.apf = 0
        if not self.pf:
            self.eatWhitespace()
            self.matches("(")
            if self.pf: self.i += len("(")
            if self.pf:
                pass
                self.stack.append(("EX1", self.l1))
                self.l1 = ""
                self.parseEX1()
                self.stack.pop()
                if not self.pf: self.error()
                self.eatWhitespace()
                self.matches(")")
                if self.pf: self.i += len(")")
                if not self.pf: self.error()
        if not self.pf:
            self.eatWhitespace()
            self.matches(".pre")
            if self.pf: self.i += len(".pre")
            if self.pf:
                pass
                self.eatWhitespace()
                self.matches("{")
                if self.pf: self.i += len("{")
                if not self.pf: self.error()
                if self.of:
                    self.ob += 'if '
                self.stack.append(("TVAR", self.l1))
                self.l1 = ""
                self.parseTVAR()
                self.stack.pop()
                if not self.pf: self.error()
                while self.pf:
                    self.eatWhitespace()
                    self.matches(",")
                    if self.pf: self.i += len(",")
                    if self.pf:
                        pass
                        if self.of:
                            self.ob += ' and '
                        self.stack.append(("TVAR", self.l1))
                        self.l1 = ""
                        self.parseTVAR()
                        self.stack.pop()
                        if not self.pf: self.error()
                self.pf = True
                if self.of:
                    self.ob += ':'
                    print " " * (self.m * 4) + self.ob
                    self.ob = ""
                    self.m += 1
                    self.ob += 'pass'
                    print " " * (self.m * 4) + self.ob
                    self.ob = ""
                self.eatWhitespace()
                self.matches("}")
                if self.pf: self.i += len("}")
                if not self.pf: self.error()
                self.eatWhitespace()
                self.matches("{")
                if self.pf: self.i += len("{")
                if not self.pf: self.error()
                self.stack.append(("EX1", self.l1))
                self.l1 = ""
                self.parseEX1()
                self.stack.pop()
                if not self.pf: self.error()
                self.eatWhitespace()
                self.matches("}")
                if self.pf: self.i += len("}")
                if not self.pf: self.error()
                if self.of:
                    if self.m: self.m -= 1
        if not self.pf:
            self.eatWhitespace()
            self.matches(".post")
            if self.pf: self.i += len(".post")
            if self.pf:
                pass
                self.eatWhitespace()
                self.matches("{")
                if self.pf: self.i += len("{")
                if not self.pf: self.error()
                self.stack.append(("AVAR", self.l1))
                self.l1 = ""
                self.parseAVAR()
                self.stack.pop()
                if not self.pf: self.error()
                while self.pf:
                    self.eatWhitespace()
                    self.matches(",")
                    if self.pf: self.i += len(",")
                    if self.pf:
                        pass
                        self.stack.append(("AVAR", self.l1))
                        self.l1 = ""
                        self.parseAVAR()
                        self.stack.pop()
                        if not self.pf: self.error()
                self.pf = True
                self.eatWhitespace()
                self.matches("}")
                if self.pf: self.i += len("}")
                if not self.pf: self.error()
        if not self.pf:
            self.eatWhitespace()
            self.matches(".fork")
            if self.pf: self.i += len(".fork")
            if self.pf:
                pass
        if not self.pf:
            self.eatWhitespace()
            self.matches(".join")
            if self.pf: self.i += len(".join")
            if self.pf:
                pass
        if not self.pf:
            self.eatWhitespace()
            self.matches(".top")
            if self.pf: self.i += len(".top")
            if self.pf:
                pass
                if self.of:
                    self.ob += 'self.top()'
                    print " " * (self.m * 4) + self.ob
                    self.ob = ""
        if not self.pf:
            self.eatWhitespace()
            self.matches(".empty")
            if self.pf: self.i += len(".empty")
            if self.pf:
                pass
                self.stack.append(("SET", self.l1))
                self.l1 = ""
                self.parseSET()
                self.stack.pop()
                if not self.pf: self.error()
        if not self.pf:
            self.eatWhitespace()
            self.matches(".litchr")
            if self.pf: self.i += len(".litchr")
            if self.pf:
                pass
                self.stack.append(("SET", self.l1))
                self.l1 = ""
                self.parseSET()
                self.stack.pop()
                if not self.pf: self.error()
                if self.of:
                    self.ob += 'self.tb = str(ord(self.s[self.i]))'
                    print " " * (self.m * 4) + self.ob
                    self.ob = ""
                    self.ob += 'self.i += 1'
                    print " " * (self.m * 4) + self.ob
                    self.ob = ""
        if not self.pf:
            self.eatWhitespace()
            self.matches(".o+")
            if self.pf: self.i += len(".o+")
            if self.pf:
                pass
                if (not (self.aof == 1)):
                    pass
                    if self.of:
                        self.ob += 'self.of = True'
                        print " " * (self.m * 4) + self.ob
                        self.ob = ""
                    if True:
                        pass
                if not self.pf: self.error()
                self.aof = 1
        if not self.pf:
            self.eatWhitespace()
            self.matches(".o-")
            if self.pf: self.i += len(".o-")
            if self.pf:
                pass
                if (not (self.aof == 2)):
                    pass
                    if self.of:
                        self.ob += 'self.of = False'
                        print " " * (self.m * 4) + self.ob
                        self.ob = ""
                    if True:
                        pass
                if not self.pf: self.error()
                self.aof = 2
        if not self.pf:
            self.eatWhitespace()
            self.matches(".pass")
            if self.pf: self.i += len(".pass")
            if self.pf:
                pass
                if self.of:
                    self.ob += 'self.i = 0'
                    print " " * (self.m * 4) + self.ob
                    self.ob = ""
        if not self.pf:
            self.eatWhitespace()
            self.matches("$")
            if self.pf: self.i += len("$")
            if self.pf:
                pass
                self.stack.append(("SET", self.l1))
                self.l1 = ""
                self.parseSET()
                self.stack.pop()
                if not self.pf: self.error()
                if self.of:
                    self.ob += 'while self.pf:'
                    print " " * (self.m * 4) + self.ob
                    self.ob = ""
                    self.m += 1
                self.apf = 1
                self.stack.append(("EX3", self.l1))
                self.l1 = ""
                self.parseEX3()
                self.stack.pop()
                if not self.pf: self.error()
                if self.of:
                    if self.m: self.m -= 1
                self.apf = 2
                self.stack.append(("SET", self.l1))
                self.l1 = ""
                self.parseSET()
                self.stack.pop()
                if not self.pf: self.error()
    def parseEX2(self):
        self.stack.append(("EX3", self.l1))
        self.l1 = ""
        self.parseEX3()
        self.stack.pop()
        if self.pf:
            pass
            if self.of:
                self.ob += 'if self.pf:'
            self.apf = 1
        if not self.pf:
            self.stack.append(("OUTPUT", self.l1))
            self.l1 = ""
            self.parseOUTPUT()
            self.stack.pop()
            if self.pf:
                pass
                if self.of:
                    self.ob += 'if True:'
        if self.pf:
            pass
            if self.of:
                print " " * (self.m * 4) + self.ob
                self.ob = ""
                self.m += 1
                self.ob += 'pass'
                print " " * (self.m * 4) + self.ob
                self.ob = ""
            while self.pf:
                self.stack.append(("EX3", self.l1))
                self.l1 = ""
                self.parseEX3()
                self.stack.pop()
                if self.pf:
                    pass
                    if (not (self.apf == 1)):
                        pass
                        if self.of:
                            self.ob += 'if not self.pf: self.error()'
                            print " " * (self.m * 4) + self.ob
                            self.ob = ""
                        if True:
                            pass
                    if not self.pf: self.error()
                    self.apf = 1
                if not self.pf:
                    self.stack.append(("OUTPUT", self.l1))
                    self.l1 = ""
                    self.parseOUTPUT()
                    self.stack.pop()
                    if self.pf:
                        pass
            self.pf = True
            if self.of:
                if self.m: self.m -= 1
            self.apf = 0
    def parseEX1(self):
        self.stack.append(("EX2", self.l1))
        self.l1 = ""
        self.parseEX2()
        self.stack.pop()
        if self.pf:
            pass
            while self.pf:
                self.eatWhitespace()
                self.matches("/")
                if self.pf: self.i += len("/")
                if self.pf:
                    pass
                    if self.of:
                        self.ob += 'if not self.pf:'
                        print " " * (self.m * 4) + self.ob
                        self.ob = ""
                        self.m += 1
                    self.stack.append(("EX2", self.l1))
                    self.l1 = ""
                    self.parseEX2()
                    self.stack.pop()
                    if not self.pf: self.error()
                    if self.of:
                        if self.m: self.m -= 1
            self.pf = True
    def parsePR(self):
        self.stack.append(("ID", self.l1))
        self.l1 = ""
        self.parseID()
        self.stack.pop()
        if self.pf:
            pass
            if self.of:
                self.ob += 'def parse'
                self.ob += self.tb
                self.ob += '(self):'
                print " " * (self.m * 4) + self.ob
                self.ob = ""
                self.m += 1
            self.eatWhitespace()
            self.matches("=")
            if self.pf: self.i += len("=")
            if not self.pf: self.error()
            self.top()
            self.stack.append(("EX1", self.l1))
            self.l1 = ""
            self.parseEX1()
            self.stack.pop()
            if not self.pf: self.error()
            self.eatWhitespace()
            self.matches(";")
            if self.pf: self.i += len(";")
            if not self.pf: self.error()
            if self.of:
                if self.m: self.m -= 1
    def parseTY(self):
        self.eatWhitespace()
        self.matches("bool")
        if self.pf: self.i += len("bool")
        if self.pf:
            pass
            if self.of:
                self.ob += '0'
    def parseDR(self):
        self.stack.append(("ID", self.l1))
        self.l1 = ""
        self.parseID()
        self.stack.pop()
        if self.pf:
            pass
            self.eatWhitespace()
            self.matches(":")
            if self.pf: self.i += len(":")
            if not self.pf: self.error()
            if self.of:
                self.ob += 'self.a'
                self.ob += self.tb
                self.ob += ' = '
            self.stack.append(("TY", self.l1))
            self.l1 = ""
            self.parseTY()
            self.stack.pop()
            if not self.pf: self.error()
            self.eatWhitespace()
            self.matches(";")
            if self.pf: self.i += len(";")
            if not self.pf: self.error()
            if self.of:
                print " " * (self.m * 4) + self.ob
                self.ob = ""
    def parseZADDY(self):
        self.eatWhitespace()
        self.matches(".syntax")
        if self.pf: self.i += len(".syntax")
        if self.pf:
            pass
            self.stack.append(("ID", self.l1))
            self.l1 = ""
            self.parseID()
            self.stack.pop()
            if not self.pf: self.error()
            if self.of:
                self.ob += 'from rpython.rlib.rfile import create_stdio'
                print " " * (self.m * 4) + self.ob
                self.ob = ""
                self.ob += 'def target(driver, *args):'
                print " " * (self.m * 4) + self.ob
                self.ob = ""
                self.m += 1
                self.ob += 'driver.exe_name = "'
                self.ob += self.tb
                self.ob += '".lower() + "c"'
                print " " * (self.m * 4) + self.ob
                self.ob = ""
                self.ob += 'return main, None'
                print " " * (self.m * 4) + self.ob
                self.ob = ""
                if self.m: self.m -= 1
                self.ob += 'def main(argv):'
                print " " * (self.m * 4) + self.ob
                self.ob = ""
                self.m += 1
                self.ob += 'stdin, stdout, stderr = create_stdio()'
                print " " * (self.m * 4) + self.ob
                self.ob = ""
                self.ob += 'parser = '
                self.ob += self.tb
                self.ob += 'Parser(stdin.read())'
                print " " * (self.m * 4) + self.ob
                self.ob = ""
                self.ob += 'try:'
                print " " * (self.m * 4) + self.ob
                self.ob = ""
                self.m += 1
                self.ob += 'parser.parse()'
                print " " * (self.m * 4) + self.ob
                self.ob = ""
                self.ob += 'return 0'
                print " " * (self.m * 4) + self.ob
                self.ob = ""
                if self.m: self.m -= 1
                self.ob += 'except ValueError:'
                print " " * (self.m * 4) + self.ob
                self.ob = ""
                self.m += 1
                self.ob += 'line = parser.s.count(chr(10), 0, parser.i) + 1'
                print " " * (self.m * 4) + self.ob
                self.ob = ""
                self.ob += 'stderr.write(("Error at input location: %d (line %d)" % (parser.i, line)) + chr(10))'
                print " " * (self.m * 4) + self.ob
                self.ob = ""
                self.ob += 'stderr.write(("Backtrace: %s" % " ".join([frame[0] for frame in parser.stack])) + chr(10))'
                print " " * (self.m * 4) + self.ob
                self.ob = ""
                self.ob += 'stderr.write(("Last matching token: '
                self.ob += chr(39)
                self.ob += '%s'
                self.ob += chr(39)
                self.ob += '" % parser.lastMatch) + chr(10))'
                print " " * (self.m * 4) + self.ob
                self.ob = ""
                self.ob += 'return 1'
                print " " * (self.m * 4) + self.ob
                self.ob = ""
                if self.m: self.m -= 1
                if self.m: self.m -= 1
                self.ob += 'class '
                self.ob += self.tb
                self.ob += 'Parser(object):'
                print " " * (self.m * 4) + self.ob
                self.ob = ""
                self.m += 1
                self.ob += 'u = 0'
                print " " * (self.m * 4) + self.ob
                self.ob = ""
                self.ob += 'pf = tf = False'
                print " " * (self.m * 4) + self.ob
                self.ob = ""
                self.ob += 'of = True'
                print " " * (self.m * 4) + self.ob
                self.ob = ""
                self.ob += 'l1 = tb = ""'
                print " " * (self.m * 4) + self.ob
                self.ob = ""
                self.ob += 'm = 0'
                print " " * (self.m * 4) + self.ob
                self.ob = ""
                self.ob += 'ob = ""'
                print " " * (self.m * 4) + self.ob
                self.ob = ""
                self.ob += 'i = 0'
                print " " * (self.m * 4) + self.ob
                self.ob = ""
                self.ob += 'lastMatch = ""'
                print " " * (self.m * 4) + self.ob
                self.ob = ""
                self.ob += 'def __init__(self, s): self.s = s; self.stack = []; self.top()'
                print " " * (self.m * 4) + self.ob
                self.ob = ""
                self.ob += 'def parse(self): self.top(); return self.parse'
                self.ob += self.tb
                self.ob += '()'
                print " " * (self.m * 4) + self.ob
                self.ob = ""
                self.ob += 'def unique(self):'
                print " " * (self.m * 4) + self.ob
                self.ob = ""
                self.m += 1
                self.ob += 'if not self.l1: self.l1 = str(self.u); self.u += 1'
                print " " * (self.m * 4) + self.ob
                self.ob = ""
                self.ob += 'return self.l1'
                print " " * (self.m * 4) + self.ob
                self.ob = ""
                if self.m: self.m -= 1
                self.ob += 'def error(self): raise ValueError("meh")'
                print " " * (self.m * 4) + self.ob
                self.ob = ""
                self.ob += 'def eatWhitespace(self):'
                print " " * (self.m * 4) + self.ob
                self.ob = ""
                self.m += 1
                self.ob += 'while self.i < len(self.s) and self.s[self.i] in (" " + chr(10)): self.i += 1'
                print " " * (self.m * 4) + self.ob
                self.ob = ""
                if self.m: self.m -= 1
                self.ob += 'def matches(self, token):'
                print " " * (self.m * 4) + self.ob
                self.ob = ""
                self.m += 1
                self.ob += 'stop = self.i + len(token)'
                print " " * (self.m * 4) + self.ob
                self.ob = ""
                self.ob += 'if stop > len(self.s): self.pf = False'
                print " " * (self.m * 4) + self.ob
                self.ob = ""
                self.ob += 'else: self.pf = self.s[self.i:stop] == token'
                print " " * (self.m * 4) + self.ob
                self.ob = ""
                self.ob += 'if self.pf: self.lastMatch = token'
                print " " * (self.m * 4) + self.ob
                self.ob = ""
                if self.m: self.m -= 1
            while self.pf:
                self.stack.append(("PR", self.l1))
                self.l1 = ""
                self.parsePR()
                self.stack.pop()
            self.pf = True
            self.eatWhitespace()
            self.matches(".tokens")
            if self.pf: self.i += len(".tokens")
            if not self.pf: self.error()
            while self.pf:
                self.stack.append(("TR", self.l1))
                self.l1 = ""
                self.parseTR()
                self.stack.pop()
            self.pf = True
            if self.of:
                self.ob += 'def top(self):'
                print " " * (self.m * 4) + self.ob
                self.ob = ""
                self.m += 1
                self.ob += 'pass'
                print " " * (self.m * 4) + self.ob
                self.ob = ""
            self.eatWhitespace()
            self.matches(".domain")
            if self.pf: self.i += len(".domain")
            if not self.pf: self.error()
            while self.pf:
                self.stack.append(("DR", self.l1))
                self.l1 = ""
                self.parseDR()
                self.stack.pop()
            self.pf = True
            if self.of:
                if self.m: self.m -= 1
            self.eatWhitespace()
            self.matches(".end")
            if self.pf: self.i += len(".end")
            if not self.pf: self.error()
    def parseWS(self):
        self.pf = True
        while self.pf:
            self.pf = ord(self.s[self.i]) == 9 or ord(self.s[self.i]) == 10 or ord(self.s[self.i]) == 13 or ord(self.s[self.i]) == 32
            if self.pf:
                if self.tf: self.tb += self.s[self.i]
                self.i += 1
        self.pf = True
        if self.pf:
            pass
    def parseDIGIT(self):
        self.pf = 48 <= ord(self.s[self.i]) <= 57
        if self.pf:
            if self.tf: self.tb += self.s[self.i]
            self.i += 1
        if self.pf:
            pass
    def parseALPHA(self):
        self.pf = 65 <= ord(self.s[self.i]) <= 90 or 97 <= ord(self.s[self.i]) <= 122
        if self.pf:
            if self.tf: self.tb += self.s[self.i]
            self.i += 1
        if self.pf:
            pass
    def parseSQUOTE(self):
        self.stack.append(("WS", self.l1))
        self.l1 = ""
        self.parseWS()
        self.stack.pop()
        if self.pf:
            pass
            self.pf = ord(self.s[self.i]) == 39
            if self.pf:
                if self.tf: self.tb += self.s[self.i]
                self.i += 1
            if not self.pf: return
    def parseSTRING(self):
        self.stack.append(("WS", self.l1))
        self.l1 = ""
        self.parseWS()
        self.stack.pop()
        if self.pf:
            pass
            self.pf = ord(self.s[self.i]) == 39
            if self.pf:
                if self.tf: self.tb += self.s[self.i]
                self.i += 1
            if not self.pf: return
            self.tb = ""
            self.tf = True
            while self.pf:
                self.pf = ord(self.s[self.i]) == 10 or ord(self.s[self.i]) == 13 or ord(self.s[self.i]) == 39
                self.pf = not self.pf
                if self.pf:
                    self.tb += self.s[self.i]
                    self.i += 1
            self.pf = True
            self.tf = False
            self.pf = ord(self.s[self.i]) == 39
            if self.pf:
                self.i += 1
            if not self.pf: return
    def parseNUMBER(self):
        self.stack.append(("WS", self.l1))
        self.l1 = ""
        self.parseWS()
        self.stack.pop()
        if self.pf:
            pass
            self.tb = ""
            self.tf = True
            self.stack.append(("DIGIT", self.l1))
            self.l1 = ""
            self.parseDIGIT()
            self.stack.pop()
            if not self.pf: return
            while self.pf:
                self.stack.append(("DIGIT", self.l1))
                self.l1 = ""
                self.parseDIGIT()
                self.stack.pop()
            self.pf = True
            self.tf = False
    def parseID(self):
        self.stack.append(("WS", self.l1))
        self.l1 = ""
        self.parseWS()
        self.stack.pop()
        if self.pf:
            pass
            self.tb = ""
            self.tf = True
            self.stack.append(("ALPHA", self.l1))
            self.l1 = ""
            self.parseALPHA()
            self.stack.pop()
            if not self.pf: return
            while self.pf:
                self.stack.append(("ALPHA", self.l1))
                self.l1 = ""
                self.parseALPHA()
                self.stack.pop()
                if self.pf:
                    pass
                if not self.pf:
                    self.stack.append(("DIGIT", self.l1))
                    self.l1 = ""
                    self.parseDIGIT()
                    self.stack.pop()
                    if self.pf:
                        pass
            self.pf = True
            self.tf = False
    def top(self):
        pass
        self.apf = 0
        self.atf = 0
        self.aof = 0
