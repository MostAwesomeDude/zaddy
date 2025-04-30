from rpython.rlib.rfile import create_stdio
def target(driver, *args):
    driver.exe_name = "ZADDY".lower() + "c"
    return main, None
class Status(object): pass
class Failed(Status): pass
# i, ms[-1], tb, ob, lb
class Succeeded(Status):
    def __init__(self, t): self.t = t
failed = Failed()
def main(argv):
    stdin, stdout, stderr = create_stdio()
    parser = ZADDYParser(stdin.read())
    status = parser.parse()
    if status is failed:
        stderr.write(("Last successful match:'%s, %d'" % parser.lastMatch) + chr(10))
        return 1
    else:
        _, _, _, _, lb = status.t
        stdout.write(lb)
        return 0
class ZADDYParser(object):
    lastMatch = "", 0
    def __init__(self, s): self.s = s; self.cache = {}; self.top()
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
        stop = i + len("*")
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
            stop = i + len(".lm+")
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
            stop = i + len(".lm-")
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
            stop = i + len(".lm?")
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
            stop = i + len(".lm!")
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
            stop = i + len(".nl")
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
            self.lastMatch = k[0], k[1]
        return self.cache[k]
    def parseOUTPUT(self, i, tf, ms, tb, ob, lb):
        k = "OUTPUT", i, tf, ms[-1], tb, ob, lb
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        pf = True
        saved.append((i, tf, ms[-1], tb, ob, lb))
        while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
        stop = i + len(".out")
        if stop > len(self.s): pf = False
        else: pf = self.s[i:stop] == ".out"
        if pf: i = stop
        if pf:
            pass
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + len("(")
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
                    stop = i + len(")")
                    if stop > len(self.s): pf = False
                    else: pf = self.s[i:stop] == ")"
                    if pf: i = stop
                    if pf:
                        pass
        saved.pop()
        if pf:
            self.cache[k] = Succeeded((i, ms[-1], tb, ob, lb))
            self.lastMatch = k[0], k[1]
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
            self.lastMatch = k[0], k[1]
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
            stop = i + len(":")
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
            self.lastMatch = k[0], k[1]
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
                stop = i + len("!")
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
            self.lastMatch = k[0], k[1]
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
            if (self.atf == 1):
                pass
                saved.append((i, tf, ms[-1], tb, ob, lb))
                ob += 'tb += self.s[i]'
                lb += " " * (ms[-1] * 4) + ob + chr(10)
                ob = ""
                saved.pop()
            if pf:
                pass
                if (self.atf == 0):
                    pass
                    saved.append((i, tf, ms[-1], tb, ob, lb))
                    ob += 'if tf: tb += self.s[i]'
                    lb += " " * (ms[-1] * 4) + ob + chr(10)
                    ob = ""
                    saved.pop()
                if pf:
                    pass
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
                if (self.atf == 1):
                    pass
                    saved.append((i, tf, ms[-1], tb, ob, lb))
                    ob += 'tb += self.s[i]'
                    lb += " " * (ms[-1] * 4) + ob + chr(10)
                    ob = ""
                    saved.pop()
                if pf:
                    pass
                    if (self.atf == 0):
                        pass
                        saved.append((i, tf, ms[-1], tb, ob, lb))
                        ob += 'if tf: tb += self.s[i]'
                        lb += " " * (ms[-1] * 4) + ob + chr(10)
                        ob = ""
                        saved.pop()
                    if pf:
                        pass
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
            self.lastMatch = k[0], k[1]
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
            self.lastMatch = k[0], k[1]
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
            self.lastMatch = k[0], k[1]
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
            self.lastMatch = k[0], k[1]
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
            self.lastMatch = k[0], k[1]
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
            self.lastMatch = k[0], k[1]
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
        stop = i + len(".token")
        if stop > len(self.s): pf = False
        else: pf = self.s[i:stop] == ".token"
        if pf: i = stop
        if pf:
            pass
            ob += 'tb = ""'
            lb += " " * (ms[-1] * 4) + ob + chr(10)
            ob = ""
            if (not (self.atf == 1)):
                pass
                saved.append((i, tf, ms[-1], tb, ob, lb))
                ob += 'tf = True'
                lb += " " * (ms[-1] * 4) + ob + chr(10)
                ob = ""
                saved.pop()
            if pf:
                pass
                self.atf = 1
                if pf:
                    pass
        if not pf:
            i, tf, ms[-1], tb, ob, lb = saved[-1]
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + len(".tokout")
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == ".tokout"
            if pf: i = stop
            if pf:
                pass
                if (not (self.atf == 2)):
                    pass
                    saved.append((i, tf, ms[-1], tb, ob, lb))
                    ob += 'tf = False'
                    lb += " " * (ms[-1] * 4) + ob + chr(10)
                    ob = ""
                    saved.pop()
                if pf:
                    pass
                    self.atf = 2
                    if pf:
                        pass
        if not pf:
            i, tf, ms[-1], tb, ob, lb = saved[-1]
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + len("$")
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
            stop = i + len(".empty")
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
            stop = i + len(".not(")
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
                    stop = i + len(")")
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
            stop = i + len(".any(")
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
                    stop = i + len(")")
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
            stop = i + len("(")
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
                    stop = i + len(")")
                    if stop > len(self.s): pf = False
                    else: pf = self.s[i:stop] == ")"
                    if pf: i = stop
                    if pf:
                        pass
        saved.pop()
        if pf:
            self.cache[k] = Succeeded((i, ms[-1], tb, ob, lb))
            self.lastMatch = k[0], k[1]
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
            self.lastMatch = k[0], k[1]
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
                    stop = i + len("/")
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
            self.lastMatch = k[0], k[1]
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
            stop = i + len(":")
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
                            stop = i + len(";")
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
                                ob += 'self.lastMatch = k[0], k[1]'
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
            self.lastMatch = k[0], k[1]
        return self.cache[k]
    def parseTVAR(self, i, tf, ms, tb, ob, lb):
        k = "TVAR", i, tf, ms[-1], tb, ob, lb
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        pf = True
        saved.append((i, tf, ms[-1], tb, ob, lb))
        while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
        stop = i + len("~")
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
            stop = i + len("?")
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
            stop = i + len("+")
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
            stop = i + len("-")
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
            self.lastMatch = k[0], k[1]
        return self.cache[k]
    def parseAVAR(self, i, tf, ms, tb, ob, lb):
        k = "AVAR", i, tf, ms[-1], tb, ob, lb
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        pf = True
        saved.append((i, tf, ms[-1], tb, ob, lb))
        while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
        stop = i + len("?")
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
            stop = i + len("+")
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
            stop = i + len("-")
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
            self.lastMatch = k[0], k[1]
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
                ob += 'if pf: i = stop'
                lb += " " * (ms[-1] * 4) + ob + chr(10)
                ob = ""
                self.apf = 0
                if pf:
                    pass
        if not pf:
            i, tf, ms[-1], tb, ob, lb = saved[-1]
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + len("(")
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
                    stop = i + len(")")
                    if stop > len(self.s): pf = False
                    else: pf = self.s[i:stop] == ")"
                    if pf: i = stop
                    if pf:
                        pass
        if not pf:
            i, tf, ms[-1], tb, ob, lb = saved[-1]
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + len(".pre")
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == ".pre"
            if pf: i = stop
            if pf:
                pass
                while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
                stop = i + len("{")
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
                            stop = i + len(",")
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
                            stop = i + len("}")
                            if stop > len(self.s): pf = False
                            else: pf = self.s[i:stop] == "}"
                            if pf: i = stop
                            if pf:
                                pass
                                while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
                                stop = i + len("{")
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
                                        stop = i + len("}")
                                        if stop > len(self.s): pf = False
                                        else: pf = self.s[i:stop] == "}"
                                        if pf: i = stop
                                        if pf:
                                            pass
                                            if ms[-1]: ms[-1] -= 1
        if not pf:
            i, tf, ms[-1], tb, ob, lb = saved[-1]
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + len(".post")
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == ".post"
            if pf: i = stop
            if pf:
                pass
                while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
                stop = i + len("{")
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
                            stop = i + len(",")
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
                            stop = i + len("}")
                            if stop > len(self.s): pf = False
                            else: pf = self.s[i:stop] == "}"
                            if pf: i = stop
                            if pf:
                                pass
        if not pf:
            i, tf, ms[-1], tb, ob, lb = saved[-1]
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + len(".fork")
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == ".fork"
            if pf: i = stop
            if pf:
                pass
        if not pf:
            i, tf, ms[-1], tb, ob, lb = saved[-1]
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + len(".join")
            if stop > len(self.s): pf = False
            else: pf = self.s[i:stop] == ".join"
            if pf: i = stop
            if pf:
                pass
        if not pf:
            i, tf, ms[-1], tb, ob, lb = saved[-1]
            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
            stop = i + len(".top")
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
            stop = i + len(".empty")
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
            stop = i + len(".litchr")
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
            stop = i + len(".pass")
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
            stop = i + len("$")
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
            self.lastMatch = k[0], k[1]
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
            self.lastMatch = k[0], k[1]
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
                    stop = i + len("/")
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
            self.lastMatch = k[0], k[1]
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
            stop = i + len("=")
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
                            stop = i + len(";")
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
                                ob += 'self.lastMatch = k[0], k[1]'
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
            self.lastMatch = k[0], k[1]
        return self.cache[k]
    def parseTY(self, i, tf, ms, tb, ob, lb):
        k = "TY", i, tf, ms[-1], tb, ob, lb
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        pf = True
        saved.append((i, tf, ms[-1], tb, ob, lb))
        while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
        stop = i + len("bool")
        if stop > len(self.s): pf = False
        else: pf = self.s[i:stop] == "bool"
        if pf: i = stop
        if pf:
            pass
            ob += '0'
        saved.pop()
        if pf:
            self.cache[k] = Succeeded((i, ms[-1], tb, ob, lb))
            self.lastMatch = k[0], k[1]
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
            stop = i + len(":")
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
                    stop = i + len(";")
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
            self.lastMatch = k[0], k[1]
        return self.cache[k]
    def parseZADDY(self, i, tf, ms, tb, ob, lb):
        k = "ZADDY", i, tf, ms[-1], tb, ob, lb
        if k in self.cache: return self.cache[k]
        self.cache[k] = failed
        saved = []
        pf = True
        saved.append((i, tf, ms[-1], tb, ob, lb))
        while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
        stop = i + len(".syntax")
        if stop > len(self.s): pf = False
        else: pf = self.s[i:stop] == ".syntax"
        if pf: i = stop
        if pf:
            pass
            rv = self.parseID(i, tf, ms[:], tb, ob, lb)
            pf = rv is not failed
            if pf: i, ms[-1], tb, ob, lb = rv.t
            if pf:
                pass
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
                ob += 'stderr.write(("Last successful match:'
                ob += chr(39)
                ob += '%s, %d'
                ob += chr(39)
                ob += '" % parser.lastMatch) + chr(10))'
                lb += " " * (ms[-1] * 4) + ob + chr(10)
                ob = ""
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
                ob += 'class '
                ob += tb
                ob += 'Parser(object):'
                lb += " " * (ms[-1] * 4) + ob + chr(10)
                ob = ""
                ms[-1] += 1
                ob += 'lastMatch = "", 0'
                lb += " " * (ms[-1] * 4) + ob + chr(10)
                ob = ""
                ob += 'def __init__(self, s): self.s = s; self.cache = {}; self.top()'
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
                    rv = self.parsePR(i, tf, ms[:], tb, ob, lb)
                    pf = rv is not failed
                    if pf: i, ms[-1], tb, ob, lb = rv.t
                pf = True
                if pf:
                    pass
                    while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
                    stop = i + len(".tokens")
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
                                    if ms[-1]: ms[-1] -= 1
                                    saved.append((i, tf, ms[-1], tb, ob, lb))
                                    while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
                                    stop = i + len(".semantics")
                                    if stop > len(self.s): pf = False
                                    else: pf = self.s[i:stop] == ".semantics"
                                    if pf: i = stop
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
                                        saved.append((i, tf, ms[-1], tb, ob, lb))
                                        while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
                                        stop = i + len(".tiles")
                                        if stop > len(self.s): pf = False
                                        else: pf = self.s[i:stop] == ".tiles"
                                        if pf: i = stop
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
                                            while i < len(self.s) and self.s[i] in (" " + chr(10)): i += 1
                                            stop = i + len(".end")
                                            if stop > len(self.s): pf = False
                                            else: pf = self.s[i:stop] == ".end"
                                            if pf: i = stop
                                            if pf:
                                                pass
        saved.pop()
        if pf:
            self.cache[k] = Succeeded((i, ms[-1], tb, ob, lb))
            self.lastMatch = k[0], k[1]
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
            self.lastMatch = k[0], k[1]
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
            self.lastMatch = k[0], k[1]
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
            self.lastMatch = k[0], k[1]
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
            self.lastMatch = k[0], k[1]
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
                            tb += self.s[i]
                            i += 1
                    pf = True
                    if pf:
                        pass
                        tf = False
                        if pf:
                            pass
                            pf = (i < len(self.s)) and ord(self.s[i]) == 39
                            if pf:
                                i += 1
                            if pf:
                                pass
        saved.pop()
        if pf:
            self.cache[k] = Succeeded((i, ms[-1], tb, ob, lb))
            self.lastMatch = k[0], k[1]
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
            self.lastMatch = k[0], k[1]
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
            self.lastMatch = k[0], k[1]
        return self.cache[k]
    def top(self):
        pass
        self.apf = 0
        self.atf = 0
