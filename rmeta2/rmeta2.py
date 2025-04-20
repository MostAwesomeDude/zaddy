from string import ascii_letters, digits
import sys

from rpython.rlib.rfile import create_stdio

from zaddy import PROGRAMParser

class Slicer(object):
    i = 0
    lastMatch = ""
    def __init__(self, s): self.s = s
    def get(self): return self.s[self.i]
    def eatWhitespace(self):
        while self.i < len(self.s) and self.s[self.i] in " \n": self.i += 1
    def matches(self, token):
        stop = self.i + len(token)
        if stop > len(self.s): return False
        rv = self.s[self.i:stop] == token
        if rv: self.lastMatch = token
        return rv
    def advance(self, i): self.i += i

def main(argv):
    stdin, stdout, stderr = create_stdio()
    parser = PROGRAMParser()
    slicer = Slicer(stdin.read())
    try:
        parser.parse(slicer)
        return 0
    except ValueError:
        line = slicer.s.count("\n", 0, slicer.i) + 1
        stderr.write("Error at input location: %d (line %d)\n" % (slicer.i, line))
        stderr.write("Backtrace: %s\n" %
                     " ".join([frame[0] for frame in parser.stack]))
        stderr.write("Last matching token: '%s'\n" % slicer.lastMatch)
        return 1

def target(driver, *args):
    driver.exe_name = "rmeta2"
    return main, None

if __name__ == "__main__": sys.exit(main(sys.argv))
