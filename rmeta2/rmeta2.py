from string import ascii_letters, digits
import sys

from rpython.rlib.rfile import create_stdio

class Slicer(object):
    i = 0
    def __init__(self, s): self.s = s
    def eatWhitespace(self):
        while self.i < len(self.s) and self.s[self.i] in " \n": self.i += 1
    def matches(self, token):
        stop = self.i + len(token)
        if stop > len(self.s): return False
        rv = self.s[self.i:stop] == token
        return rv
    def matchToken(self):
        if self.s[self.i] not in ascii_letters: return ""
        stop = self.i + 1
        while stop < len(self.s) and (
                self.s[stop] in (ascii_letters + digits)): stop += 1
        token = self.s[self.i:stop]
        self.i = stop
        return token
    def matchNum(self):
        if self.s[self.i] not in digits: return ""
        stop = self.i + 1
        while stop < len(self.s) and self.s[stop] in digits: stop += 1
        token = self.s[self.i:stop]
        self.i = stop
        return token
    def matchString(self):
        if self.s[self.i] != "'": return ""
        stop = self.i + 1
        while stop < len(self.s) and self.s[stop] != "'": stop += 1
        stop += 1
        token = self.s[self.i:stop]
        self.i = stop
        return token
    def advance(self, i): self.i += i

def parse(program):
    labels = {}
    instructions = []
    adr = ""
    for line in program.split("\n"):
        if not line: continue
        elif line.startswith(" "):
            instruction = line.strip()
            if instruction == "END": break
            elif instruction.startswith("ADR "): adr = instruction[4:].strip()
            else: instructions.append(instruction)
        else:
            label = line.strip()
            labels[label] = len(instructions)
    if adr not in labels:
        print "Starting address %s not in labels!" % adr
        raise ValueError("No starting address!")
    return labels[adr], labels, instructions

def go(i, labels, instructions, slicer):
    unique = 0
    stack = []
    switch = False
    l1 = l2 = tokenBuffer = ""
    outBuffer = " " * 8
    while i < len(instructions):
        inst = instructions[i]
        if " " in inst:
            op, params = inst.split(" ", 1)
            params = params.strip()
        else:
            op = inst.strip()
            params = ""
        if op == "TST":
            slicer.eatWhitespace()
            stop = len(params) - 1
            assert stop >= 0, "magnolia"
            token = params[1:stop]
            switch = slicer.matches(token)
            if switch: slicer.advance(len(token))
            i += 1
        elif op == "ID":
            slicer.eatWhitespace()
            token = slicer.matchToken()
            switch = bool(token)
            if switch: tokenBuffer = token
            i += 1
        elif op == "NUM":
            slicer.eatWhitespace()
            token = slicer.matchNum()
            switch = bool(token)
            if switch: tokenBuffer = token
            i += 1
        elif op == "SR":
            slicer.eatWhitespace()
            token = slicer.matchString()
            switch = bool(token)
            if switch: tokenBuffer = token
            i += 1
        elif op == "CLL":
            stack.append((l1, l2, i + 1))
            l1 = l2 = ""
            i = labels[params]
        elif op == "R":
            if not stack: return 0
            l1, l2, i = stack.pop()
        elif op == "SET":
            switch = True
            i += 1
        elif op == "B": i = labels[params]
        elif op == "BT": i = labels[params] if switch else i + 1
        elif op == "BF": i = i + 1 if switch else labels[params]
        elif op == "BE":
            i += 1
            if not switch:
                print "Error!"
                return 1
        elif op == "CL":
            stop = len(params) - 1
            assert stop >= 0, "magnolia"
            outBuffer += params[1:stop]
            i += 1
        elif op == "CI":
            outBuffer += tokenBuffer
            i += 1
        elif op == "GN1":
            if not l1:
                l1 = "l%d" % unique
                unique += 1
            outBuffer += l1
            i += 1
        elif op == "GN2":
            if not l2:
                l2 = "l%d" % unique
                unique += 1
            outBuffer += l2
            i += 1
        elif op == "LB":
            outBuffer = ""
            i += 1
        elif op == "OUT":
            print outBuffer
            outBuffer = " " * 8
            i += 1
        else:
            print "Unknown opcode %s" % op
            return 1
    return 0

def main(argv):
    if len(argv) != 2:
        print "Usage:", argv[0], "<program.o>"
        return 1
    with open(argv[1], "rb") as handle: program = handle.read()
    adr, labels, instructions = parse(program)
    stdin, stdout, stderr = create_stdio()
    return go(adr, labels, instructions, Slicer(stdin.read()))

def target(driver, *args):
    driver.exe_name = "rmeta2"
    return main, None

if __name__ == "__main__":
    sys.exit(main(sys.argv))
