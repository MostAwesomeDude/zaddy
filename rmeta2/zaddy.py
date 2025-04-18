class PROGRAMParser(object):
  u = 0
  pf = tf = False
  l1 = tb = ""
  m = 0
  ob = ""
  def __init__(self): self.stack = []
  def parse(self, s): return self.parsePROGRAM(s)
  def unique(self):
    if not self.l1: self.l1 = str(self.u); self.u += 1
    return self.l1
  def error(self, i): raise ValueError("meh")
  def parseOUT1(self, s):
    s.eatWhitespace()
    self.pf = s.matches("*")
    if self.pf: s.advance(len("*"))
    if self.pf:
      pass
      self.ob += 'self.ob += self.tb'
      print " " * (self.m * 2) + self.ob
      self.ob = ""
    if not self.pf:
      self.stack.append(("STRING", self.l1))
      self.l1 = ""
      self.parseSTRING(s)
      self.stack.pop()
      if self.pf:
        pass
        self.ob += 'self.ob += '
        self.ob += chr(39)
        self.ob += self.tb
        self.ob += chr(39)
        print " " * (self.m * 2) + self.ob
        self.ob = ""
    if not self.pf:
      self.stack.append(("NUMBER", self.l1))
      self.l1 = ""
      self.parseNUMBER(s)
      self.stack.pop()
      if self.pf:
        pass
        self.ob += 'self.ob += chr('
        self.ob += self.tb
        self.ob += ')'
        print " " * (self.m * 2) + self.ob
        self.ob = ""
    if not self.pf:
      s.eatWhitespace()
      self.pf = s.matches("#")
      if self.pf: s.advance(len("#"))
      if self.pf:
        pass
        self.ob += 'self.ob += self.unique()'
        print " " * (self.m * 2) + self.ob
        self.ob = ""
    if not self.pf:
      s.eatWhitespace()
      self.pf = s.matches(".lm+")
      if self.pf: s.advance(len(".lm+"))
      if self.pf:
        pass
        self.ob += 'self.m += 1'
        print " " * (self.m * 2) + self.ob
        self.ob = ""
    if not self.pf:
      s.eatWhitespace()
      self.pf = s.matches(".lm-")
      if self.pf: s.advance(len(".lm-"))
      if self.pf:
        pass
        self.ob += 'if self.m: self.m -= 1'
        print " " * (self.m * 2) + self.ob
        self.ob = ""
    if not self.pf:
      s.eatWhitespace()
      self.pf = s.matches(".nl")
      if self.pf: s.advance(len(".nl"))
      if self.pf:
        pass
        self.ob += 'print " " * (self.m * 2) + self.ob'
        print " " * (self.m * 2) + self.ob
        self.ob = ""
        self.ob += 'self.ob = ""'
        print " " * (self.m * 2) + self.ob
        self.ob = ""
  def parseOUTPUT(self, s):
    s.eatWhitespace()
    self.pf = s.matches(".out")
    if self.pf: s.advance(len(".out"))
    if self.pf:
      pass
      s.eatWhitespace()
      self.pf = s.matches("(")
      if self.pf: s.advance(len("("))
      if not self.pf: self.error(s.i)
      self.pf = True
      while self.pf:
        self.stack.append(("OUT1", self.l1))
        self.l1 = ""
        self.parseOUT1(s)
        self.stack.pop()
      self.pf = True
      if not self.pf: self.error(s.i)
      s.eatWhitespace()
      self.pf = s.matches(")")
      if self.pf: s.advance(len(")"))
      if not self.pf: self.error(s.i)
  def parseCX3(self, s):
    self.stack.append(("NUMBER", self.l1))
    self.l1 = ""
    self.parseNUMBER(s)
    self.stack.pop()
    if self.pf:
      pass
    if not self.pf:
      self.stack.append(("SQUOTE", self.l1))
      self.l1 = ""
      self.parseSQUOTE(s)
      self.stack.pop()
      if self.pf:
        pass
        self.pf = True
        self.tb = str(ord(s.get()))
        s.advance(1)
        if not self.pf: self.error(s.i)
  def parseCX2(self, s):
    self.stack.append(("CX3", self.l1))
    self.l1 = ""
    self.parseCX3(s)
    self.stack.pop()
    if self.pf:
      pass
      s.eatWhitespace()
      self.pf = s.matches(":")
      if self.pf: s.advance(len(":"))
      if self.pf:
        pass
        self.ob += self.tb
        self.ob += ' <= ord(s.get()) <= '
        self.stack.append(("CX3", self.l1))
        self.l1 = ""
        self.parseCX3(s)
        self.stack.pop()
        if not self.pf: self.error(s.i)
        self.ob += self.tb
      if not self.pf:
        self.pf = True
        if self.pf:
          pass
          self.ob += 'ord(s.get()) == '
          self.ob += self.tb
      if not self.pf: self.error(s.i)
  def parseCX1(self, s):
    self.ob += 'self.pf = '
    if True:
      pass
      self.stack.append(("CX2", self.l1))
      self.l1 = ""
      self.parseCX2(s)
      self.stack.pop()
      if not self.pf: self.error(s.i)
      self.pf = True
      while self.pf:
        s.eatWhitespace()
        self.pf = s.matches("!")
        if self.pf: s.advance(len("!"))
        if self.pf:
          pass
          self.ob += ' or '
          self.stack.append(("CX2", self.l1))
          self.l1 = ""
          self.parseCX2(s)
          self.stack.pop()
          if not self.pf: self.error(s.i)
      self.pf = True
      if not self.pf: self.error(s.i)
      print " " * (self.m * 2) + self.ob
      self.ob = ""
  def parseSCAN(self, s):
    self.ob += 'if self.pf:'
    print " " * (self.m * 2) + self.ob
    self.ob = ""
    self.m += 1
    self.ob += 'if self.tf: self.tb += s.get()'
    print " " * (self.m * 2) + self.ob
    self.ob = ""
    self.ob += 's.advance(1)'
    print " " * (self.m * 2) + self.ob
    self.ob = ""
    if self.m: self.m -= 1
    if True:
      pass
  def parseSUB(self, s):
    self.stack.append(("ID", self.l1))
    self.l1 = ""
    self.parseID(s)
    self.stack.pop()
    if self.pf:
      pass
      self.ob += 'self.stack.append(("'
      self.ob += self.tb
      self.ob += '", self.l1))'
      print " " * (self.m * 2) + self.ob
      self.ob = ""
      self.ob += 'self.l1 = ""'
      print " " * (self.m * 2) + self.ob
      self.ob = ""
      self.ob += 'self.parse'
      self.ob += self.tb
      self.ob += '(s)'
      print " " * (self.m * 2) + self.ob
      self.ob = ""
      self.ob += 'self.stack.pop()'
      print " " * (self.m * 2) + self.ob
      self.ob = ""
  def parseTX3(self, s):
    s.eatWhitespace()
    self.pf = s.matches(".token")
    if self.pf: s.advance(len(".token"))
    if self.pf:
      pass
      self.ob += 'self.tf = True'
      print " " * (self.m * 2) + self.ob
      self.ob = ""
      self.ob += 'self.tb = ""'
      print " " * (self.m * 2) + self.ob
      self.ob = ""
    if not self.pf:
      s.eatWhitespace()
      self.pf = s.matches(".tokout")
      if self.pf: s.advance(len(".tokout"))
      if self.pf:
        pass
        self.ob += 'self.tf = False'
        print " " * (self.m * 2) + self.ob
        self.ob = ""
    if not self.pf:
      s.eatWhitespace()
      self.pf = s.matches("$")
      if self.pf: s.advance(len("$"))
      if self.pf:
        pass
        self.ob += 'self.pf = True'
        print " " * (self.m * 2) + self.ob
        self.ob = ""
        self.ob += 'while self.pf:'
        print " " * (self.m * 2) + self.ob
        self.ob = ""
        self.m += 1
        self.stack.append(("TX3", self.l1))
        self.l1 = ""
        self.parseTX3(s)
        self.stack.pop()
        if not self.pf: self.error(s.i)
        if self.m: self.m -= 1
    if self.pf:
      pass
      self.ob += 'self.pf = True'
      print " " * (self.m * 2) + self.ob
      self.ob = ""
    if not self.pf:
      s.eatWhitespace()
      self.pf = s.matches(".not(")
      if self.pf: s.advance(len(".not("))
      if self.pf:
        pass
        self.stack.append(("CX1", self.l1))
        self.l1 = ""
        self.parseCX1(s)
        self.stack.pop()
        if not self.pf: self.error(s.i)
        s.eatWhitespace()
        self.pf = s.matches(")")
        if self.pf: s.advance(len(")"))
        if not self.pf: self.error(s.i)
        self.ob += 'self.pf = not self.pf'
        print " " * (self.m * 2) + self.ob
        self.ob = ""
        self.stack.append(("SCAN", self.l1))
        self.l1 = ""
        self.parseSCAN(s)
        self.stack.pop()
        if not self.pf: self.error(s.i)
    if not self.pf:
      s.eatWhitespace()
      self.pf = s.matches(".any(")
      if self.pf: s.advance(len(".any("))
      if self.pf:
        pass
        self.stack.append(("CX1", self.l1))
        self.l1 = ""
        self.parseCX1(s)
        self.stack.pop()
        if not self.pf: self.error(s.i)
        s.eatWhitespace()
        self.pf = s.matches(")")
        if self.pf: s.advance(len(")"))
        if not self.pf: self.error(s.i)
        self.stack.append(("SCAN", self.l1))
        self.l1 = ""
        self.parseSCAN(s)
        self.stack.pop()
        if not self.pf: self.error(s.i)
    if not self.pf:
      self.stack.append(("SUB", self.l1))
      self.l1 = ""
      self.parseSUB(s)
      self.stack.pop()
      if self.pf:
        pass
    if not self.pf:
      s.eatWhitespace()
      self.pf = s.matches("(")
      if self.pf: s.advance(len("("))
      if self.pf:
        pass
        self.stack.append(("TX1", self.l1))
        self.l1 = ""
        self.parseTX1(s)
        self.stack.pop()
        if not self.pf: self.error(s.i)
        s.eatWhitespace()
        self.pf = s.matches(")")
        if self.pf: s.advance(len(")"))
        if not self.pf: self.error(s.i)
  def parseTX2(self, s):
    self.stack.append(("TX3", self.l1))
    self.l1 = ""
    self.parseTX3(s)
    self.stack.pop()
    if self.pf:
      pass
      self.ob += 'if self.pf:'
      print " " * (self.m * 2) + self.ob
      self.ob = ""
      self.m += 1
      self.ob += 'pass'
      print " " * (self.m * 2) + self.ob
      self.ob = ""
      self.pf = True
      while self.pf:
        self.stack.append(("TX3", self.l1))
        self.l1 = ""
        self.parseTX3(s)
        self.stack.pop()
        if self.pf:
          pass
          self.ob += 'if not self.pf: return'
          print " " * (self.m * 2) + self.ob
          self.ob = ""
      self.pf = True
      if not self.pf: self.error(s.i)
      if self.m: self.m -= 1
  def parseTX1(self, s):
    self.stack.append(("TX2", self.l1))
    self.l1 = ""
    self.parseTX2(s)
    self.stack.pop()
    if self.pf:
      pass
      self.pf = True
      while self.pf:
        s.eatWhitespace()
        self.pf = s.matches("/")
        if self.pf: s.advance(len("/"))
        if self.pf:
          pass
          self.ob += 'if not self.pf:'
          print " " * (self.m * 2) + self.ob
          self.ob = ""
          self.m += 1
          self.stack.append(("TX2", self.l1))
          self.l1 = ""
          self.parseTX2(s)
          self.stack.pop()
          if not self.pf: self.error(s.i)
          if self.m: self.m -= 1
      self.pf = True
      if not self.pf: self.error(s.i)
  def parseTR(self, s):
    self.stack.append(("ID", self.l1))
    self.l1 = ""
    self.parseID(s)
    self.stack.pop()
    if self.pf:
      pass
      self.ob += 'def parse'
      self.ob += self.tb
      self.ob += '(self, s):'
      print " " * (self.m * 2) + self.ob
      self.ob = ""
      self.m += 1
      s.eatWhitespace()
      self.pf = s.matches(":")
      if self.pf: s.advance(len(":"))
      if not self.pf: self.error(s.i)
      self.stack.append(("TX1", self.l1))
      self.l1 = ""
      self.parseTX1(s)
      self.stack.pop()
      if not self.pf: self.error(s.i)
      s.eatWhitespace()
      self.pf = s.matches(";")
      if self.pf: s.advance(len(";"))
      if not self.pf: self.error(s.i)
      if self.m: self.m -= 1
  def parseEX3(self, s):
    self.stack.append(("SUB", self.l1))
    self.l1 = ""
    self.parseSUB(s)
    self.stack.pop()
    if self.pf:
      pass
    if not self.pf:
      self.stack.append(("STRING", self.l1))
      self.l1 = ""
      self.parseSTRING(s)
      self.stack.pop()
      if self.pf:
        pass
        self.ob += 's.eatWhitespace()'
        print " " * (self.m * 2) + self.ob
        self.ob = ""
        self.ob += 'self.pf = s.matches("'
        self.ob += self.tb
        self.ob += '")'
        print " " * (self.m * 2) + self.ob
        self.ob = ""
        self.ob += 'if self.pf: s.advance(len("'
        self.ob += self.tb
        self.ob += '"))'
        print " " * (self.m * 2) + self.ob
        self.ob = ""
    if not self.pf:
      s.eatWhitespace()
      self.pf = s.matches("(")
      if self.pf: s.advance(len("("))
      if self.pf:
        pass
        self.stack.append(("EX1", self.l1))
        self.l1 = ""
        self.parseEX1(s)
        self.stack.pop()
        if not self.pf: self.error(s.i)
        s.eatWhitespace()
        self.pf = s.matches(")")
        if self.pf: s.advance(len(")"))
        if not self.pf: self.error(s.i)
    if not self.pf:
      s.eatWhitespace()
      self.pf = s.matches(".empty")
      if self.pf: s.advance(len(".empty"))
      if self.pf:
        pass
        self.ob += 'self.pf = True'
        print " " * (self.m * 2) + self.ob
        self.ob = ""
    if not self.pf:
      s.eatWhitespace()
      self.pf = s.matches(".litchr")
      if self.pf: s.advance(len(".litchr"))
      if self.pf:
        pass
        self.ob += 'self.pf = True'
        print " " * (self.m * 2) + self.ob
        self.ob = ""
        self.ob += 'self.tb = str(ord(s.get()))'
        print " " * (self.m * 2) + self.ob
        self.ob = ""
        self.ob += 's.advance(1)'
        print " " * (self.m * 2) + self.ob
        self.ob = ""
    if not self.pf:
      s.eatWhitespace()
      self.pf = s.matches("$")
      if self.pf: s.advance(len("$"))
      if self.pf:
        pass
        self.ob += 'self.pf = True'
        print " " * (self.m * 2) + self.ob
        self.ob = ""
        self.ob += 'while self.pf:'
        print " " * (self.m * 2) + self.ob
        self.ob = ""
        self.m += 1
        self.stack.append(("EX3", self.l1))
        self.l1 = ""
        self.parseEX3(s)
        self.stack.pop()
        if not self.pf: self.error(s.i)
        if self.m: self.m -= 1
        self.ob += 'self.pf = True'
        print " " * (self.m * 2) + self.ob
        self.ob = ""
  def parseEX2(self, s):
    self.stack.append(("EX3", self.l1))
    self.l1 = ""
    self.parseEX3(s)
    self.stack.pop()
    if self.pf:
      pass
      self.ob += 'if self.pf:'
    if not self.pf:
      self.stack.append(("OUTPUT", self.l1))
      self.l1 = ""
      self.parseOUTPUT(s)
      self.stack.pop()
      if self.pf:
        pass
        self.ob += 'if True:'
    if self.pf:
      pass
      print " " * (self.m * 2) + self.ob
      self.ob = ""
      self.m += 1
      self.ob += 'pass'
      print " " * (self.m * 2) + self.ob
      self.ob = ""
      self.pf = True
      while self.pf:
        self.stack.append(("EX3", self.l1))
        self.l1 = ""
        self.parseEX3(s)
        self.stack.pop()
        if self.pf:
          pass
          self.ob += 'if not self.pf: self.error(s.i)'
          print " " * (self.m * 2) + self.ob
          self.ob = ""
        if not self.pf:
          self.stack.append(("OUTPUT", self.l1))
          self.l1 = ""
          self.parseOUTPUT(s)
          self.stack.pop()
          if self.pf:
            pass
      self.pf = True
      if not self.pf: self.error(s.i)
      if self.m: self.m -= 1
  def parseEX1(self, s):
    self.stack.append(("EX2", self.l1))
    self.l1 = ""
    self.parseEX2(s)
    self.stack.pop()
    if self.pf:
      pass
      self.pf = True
      while self.pf:
        s.eatWhitespace()
        self.pf = s.matches("/")
        if self.pf: s.advance(len("/"))
        if self.pf:
          pass
          self.ob += 'if not self.pf:'
          print " " * (self.m * 2) + self.ob
          self.ob = ""
          self.m += 1
          self.stack.append(("EX2", self.l1))
          self.l1 = ""
          self.parseEX2(s)
          self.stack.pop()
          if not self.pf: self.error(s.i)
          if self.m: self.m -= 1
      self.pf = True
      if not self.pf: self.error(s.i)
  def parsePR(self, s):
    self.stack.append(("ID", self.l1))
    self.l1 = ""
    self.parseID(s)
    self.stack.pop()
    if self.pf:
      pass
      self.ob += 'def parse'
      self.ob += self.tb
      self.ob += '(self, s):'
      print " " * (self.m * 2) + self.ob
      self.ob = ""
      self.m += 1
      s.eatWhitespace()
      self.pf = s.matches("=")
      if self.pf: s.advance(len("="))
      if not self.pf: self.error(s.i)
      self.stack.append(("EX1", self.l1))
      self.l1 = ""
      self.parseEX1(s)
      self.stack.pop()
      if not self.pf: self.error(s.i)
      s.eatWhitespace()
      self.pf = s.matches(";")
      if self.pf: s.advance(len(";"))
      if not self.pf: self.error(s.i)
      if self.m: self.m -= 1
  def parsePROGRAM(self, s):
    s.eatWhitespace()
    self.pf = s.matches(".syntax")
    if self.pf: s.advance(len(".syntax"))
    if self.pf:
      pass
      self.stack.append(("ID", self.l1))
      self.l1 = ""
      self.parseID(s)
      self.stack.pop()
      if not self.pf: self.error(s.i)
      self.ob += 'class '
      self.ob += self.tb
      self.ob += 'Parser(object):'
      print " " * (self.m * 2) + self.ob
      self.ob = ""
      self.m += 1
      self.ob += 'u = 0'
      print " " * (self.m * 2) + self.ob
      self.ob = ""
      self.ob += 'pf = tf = False'
      print " " * (self.m * 2) + self.ob
      self.ob = ""
      self.ob += 'l1 = tb = ""'
      print " " * (self.m * 2) + self.ob
      self.ob = ""
      self.ob += 'm = 0'
      print " " * (self.m * 2) + self.ob
      self.ob = ""
      self.ob += 'ob = ""'
      print " " * (self.m * 2) + self.ob
      self.ob = ""
      self.ob += 'def __init__(self): self.stack = []'
      print " " * (self.m * 2) + self.ob
      self.ob = ""
      self.ob += 'def parse(self, s): return self.parse'
      self.ob += self.tb
      self.ob += '(s)'
      print " " * (self.m * 2) + self.ob
      self.ob = ""
      self.ob += 'def unique(self):'
      print " " * (self.m * 2) + self.ob
      self.ob = ""
      self.m += 1
      self.ob += 'if not self.l1: self.l1 = str(self.u); self.u += 1'
      print " " * (self.m * 2) + self.ob
      self.ob = ""
      self.ob += 'return self.l1'
      print " " * (self.m * 2) + self.ob
      self.ob = ""
      if self.m: self.m -= 1
      self.ob += 'def error(self, i): raise ValueError("meh")'
      print " " * (self.m * 2) + self.ob
      self.ob = ""
      self.pf = True
      while self.pf:
        self.stack.append(("PR", self.l1))
        self.l1 = ""
        self.parsePR(s)
        self.stack.pop()
      self.pf = True
      if not self.pf: self.error(s.i)
      s.eatWhitespace()
      self.pf = s.matches(".tokens")
      if self.pf: s.advance(len(".tokens"))
      if not self.pf: self.error(s.i)
      self.pf = True
      while self.pf:
        self.stack.append(("TR", self.l1))
        self.l1 = ""
        self.parseTR(s)
        self.stack.pop()
      self.pf = True
      if not self.pf: self.error(s.i)
      s.eatWhitespace()
      self.pf = s.matches(".end")
      if self.pf: s.advance(len(".end"))
      if not self.pf: self.error(s.i)
  def parseWS(self, s):
    self.pf = True
    while self.pf:
      self.pf = ord(s.get()) == 9 or ord(s.get()) == 10 or ord(s.get()) == 13 or ord(s.get()) == 32
      if self.pf:
        if self.tf: self.tb += s.get()
        s.advance(1)
    self.pf = True
    if self.pf:
      pass
  def parseDIGIT(self, s):
    self.pf = 48 <= ord(s.get()) <= 57
    if self.pf:
      if self.tf: self.tb += s.get()
      s.advance(1)
    if self.pf:
      pass
  def parseALPHA(self, s):
    self.pf = 65 <= ord(s.get()) <= 90 or 97 <= ord(s.get()) <= 122
    if self.pf:
      if self.tf: self.tb += s.get()
      s.advance(1)
    if self.pf:
      pass
  def parseSQUOTE(self, s):
    self.stack.append(("WS", self.l1))
    self.l1 = ""
    self.parseWS(s)
    self.stack.pop()
    if self.pf:
      pass
      self.pf = ord(s.get()) == 39
      if self.pf:
        if self.tf: self.tb += s.get()
        s.advance(1)
      if not self.pf: return
  def parseSTRING(self, s):
    self.stack.append(("WS", self.l1))
    self.l1 = ""
    self.parseWS(s)
    self.stack.pop()
    if self.pf:
      pass
      self.pf = ord(s.get()) == 39
      if self.pf:
        if self.tf: self.tb += s.get()
        s.advance(1)
      if not self.pf: return
      self.tf = True
      self.tb = ""
      self.pf = True
      if not self.pf: return
      self.pf = True
      while self.pf:
        self.pf = ord(s.get()) == 10 or ord(s.get()) == 13 or ord(s.get()) == 39
        self.pf = not self.pf
        if self.pf:
          if self.tf: self.tb += s.get()
          s.advance(1)
      self.pf = True
      if not self.pf: return
      self.tf = False
      self.pf = True
      if not self.pf: return
      self.pf = ord(s.get()) == 39
      if self.pf:
        if self.tf: self.tb += s.get()
        s.advance(1)
      if not self.pf: return
  def parseNUMBER(self, s):
    self.stack.append(("WS", self.l1))
    self.l1 = ""
    self.parseWS(s)
    self.stack.pop()
    if self.pf:
      pass
      self.tf = True
      self.tb = ""
      self.pf = True
      if not self.pf: return
      self.stack.append(("DIGIT", self.l1))
      self.l1 = ""
      self.parseDIGIT(s)
      self.stack.pop()
      if not self.pf: return
      self.pf = True
      while self.pf:
        self.stack.append(("DIGIT", self.l1))
        self.l1 = ""
        self.parseDIGIT(s)
        self.stack.pop()
      self.pf = True
      if not self.pf: return
      self.tf = False
      self.pf = True
      if not self.pf: return
  def parseID(self, s):
    self.stack.append(("WS", self.l1))
    self.l1 = ""
    self.parseWS(s)
    self.stack.pop()
    if self.pf:
      pass
      self.tf = True
      self.tb = ""
      self.pf = True
      if not self.pf: return
      self.stack.append(("ALPHA", self.l1))
      self.l1 = ""
      self.parseALPHA(s)
      self.stack.pop()
      if not self.pf: return
      self.pf = True
      while self.pf:
        self.stack.append(("ALPHA", self.l1))
        self.l1 = ""
        self.parseALPHA(s)
        self.stack.pop()
        if self.pf:
          pass
        if not self.pf:
          self.stack.append(("DIGIT", self.l1))
          self.l1 = ""
          self.parseDIGIT(s)
          self.stack.pop()
          if self.pf:
            pass
      self.pf = True
      if not self.pf: return
      self.tf = False
      self.pf = True
      if not self.pf: return
