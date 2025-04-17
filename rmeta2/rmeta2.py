from string import ascii_letters, digits
import sys

from rpython.rlib.rfile import create_stdio

class Slicer(object):
    i = 0
    def __init__(self, s): self.s = s
    def get(self): return self.s[self.i]
    def eatWhitespace(self):
        while self.i < len(self.s) and self.s[self.i] in " \n": self.i += 1
    def matches(self, token):
        stop = self.i + len(token)
        if stop > len(self.s): return False
        rv = self.s[self.i:stop] == token
        return rv
    def advance(self, i): self.i += i

def parse(program):
    labels = {}
    instructions = []
    adr = ""
    for line in program.split("\n"):
        if not line: continue
        elif line.startswith(" "):
            instruction = line.strip()
            if instruction.lower() == "end": break
            elif instruction.lower().startswith("adr "): adr = instruction[4:].strip()
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
    parseFlag = tokenFlag = False
    l1 = tokenBuffer = ""
    margin = 1
    outBuffer = ""
    while i < len(instructions):
        inst = instructions[i]
        if " " in inst:
            op, params = inst.split(" ", 1)
            op = op.lower()
            params = params.strip()
        else:
            op = inst.strip().lower()
            params = ""

        if op == "tft":
            tokenFlag = True
            tokenBuffer = ""
            i += 1
        elif op == "tff":
            tokenFlag = False
            i += 1
        elif op == "not":
            parseFlag = not parseFlag
            i += 1
        elif op == "scn":
            if parseFlag:
                if tokenFlag: tokenBuffer += slicer.get()
                slicer.advance(1)
            i += 1
        elif op == "cge":
            parseFlag = ord(slicer.get()) >= int(params)
            i += 1
        elif op == "cle":
            parseFlag = ord(slicer.get()) <= int(params)
            i += 1
        elif op == "ce":
            parseFlag = ord(slicer.get()) == int(params)
            i += 1
        elif op == "lch":
            parseFlag = True
            tokenBuffer = str(ord(slicer.get()))
            slicer.advance(1)
            i += 1
        elif op == "tst":
            slicer.eatWhitespace()
            stop = len(params) - 1
            assert stop >= 0, "magnolia"
            token = params[1:stop]
            parseFlag = slicer.matches(token)
            if parseFlag: slicer.advance(len(token))
            i += 1
        elif op == "cll":
            stack.append((params, l1, i + 1))
            l1 = ""
            i = labels[params]
        elif op == "r":
            if not stack: return 0
            _, l1, i = stack.pop()
        elif op == "rf":
            if not parseFlag:
                if not stack: return 0
                _, l1, i = stack.pop()
            else: i += 1
        elif op == "set":
            parseFlag = True
            i += 1
        elif op == "bt": i = labels[params] if parseFlag else i + 1
        elif op == "bf": i = i + 1 if parseFlag else labels[params]
        elif op == "be":
            i += 1
            if not parseFlag:
                print "Error!"
                print "Input location:", slicer.i
                print "Backtrace:", " ".join([frame[0] for frame in stack])
                return 1
        elif op == "cc":
            outBuffer += chr(int(params))
            i += 1
        elif op == "cl":
            stop = len(params) - 1
            assert stop >= 0, "magnolia"
            outBuffer += params[1:stop]
            i += 1
        elif op == "ci":
            outBuffer += tokenBuffer
            i += 1
        elif op == "gn":
            if not l1:
                l1 = str(unique)
                unique += 1
            outBuffer += l1
            i += 1
        elif op == "lb":
            outBuffer = ""
            margin = 0
            i += 1
        elif op in ("tb", "lmi"):
            margin += 1
            i += 1
        elif op == "lmd":
            if margin: margin -= 1
            i += 1
        elif op in ("nl", "out"):
            print " " * margin + outBuffer
            outBuffer = ""
            margin = 1
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
