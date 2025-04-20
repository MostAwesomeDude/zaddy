class PROGRAMParser(object):
  u = 0
  pf = tf = False
  of = True
  l1 = tb = ""
  m = 0
  ob = ""
  def __init__(self): self.top(); self.stack = []
  def parse(self, s): self.top(); return self.parsePROGRAM(s)
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
      if self.of: self.ob += 'if self.of: self.ob += self.tb'
      if self.of:
        print " " * (self.m * 2) + self.ob
        self.ob = ""
    if not self.pf:
      self.stack.append(("STRING", self.l1))
      self.l1 = ""
      self.parseSTRING(s)
      self.stack.pop()
      if self.pf:
        pass
        if self.of: self.ob += 'if self.of: self.ob += '
        if self.of: self.ob += chr(39)
        if self.of: self.ob += self.tb
        if self.of: self.ob += chr(39)
        if self.of:
          print " " * (self.m * 2) + self.ob
          self.ob = ""
    if not self.pf:
      self.stack.append(("NUMBER", self.l1))
      self.l1 = ""
      self.parseNUMBER(s)
      self.stack.pop()
      if self.pf:
        pass
        if self.of: self.ob += 'if self.of: self.ob += chr('
        if self.of: self.ob += self.tb
        if self.of: self.ob += ')'
        if self.of:
          print " " * (self.m * 2) + self.ob
          self.ob = ""
    if not self.pf:
      s.eatWhitespace()
      self.pf = s.matches("#")
      if self.pf: s.advance(len("#"))
      if self.pf:
        pass
        if self.of: self.ob += 'if self.of: self.ob += self.unique()'
        if self.of:
          print " " * (self.m * 2) + self.ob
          self.ob = ""
    if not self.pf:
      s.eatWhitespace()
      self.pf = s.matches(".lm+")
      if self.pf: s.advance(len(".lm+"))
      if self.pf:
        pass
        if self.of: self.ob += 'if self.of: self.m += 1'
        if self.of:
          print " " * (self.m * 2) + self.ob
          self.ob = ""
    if not self.pf:
      s.eatWhitespace()
      self.pf = s.matches(".lm-")
      if self.pf: s.advance(len(".lm-"))
      if self.pf:
        pass
        if self.of: self.ob += 'if self.of and self.m: self.m -= 1'
        if self.of:
          print " " * (self.m * 2) + self.ob
          self.ob = ""
    if not self.pf:
      s.eatWhitespace()
      self.pf = s.matches(".nl")
      if self.pf: s.advance(len(".nl"))
      if self.pf:
        pass
        if self.of: self.ob += 'if self.of:'
        if self.of:
          print " " * (self.m * 2) + self.ob
          self.ob = ""
        if self.of: self.m += 1
        if self.of: self.ob += 'print " " * (self.m * 2) + self.ob'
        if self.of:
          print " " * (self.m * 2) + self.ob
          self.ob = ""
        if self.of: self.ob += 'self.ob = ""'
        if self.of:
          print " " * (self.m * 2) + self.ob
          self.ob = ""
        if self.of and self.m: self.m -= 1
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
      while self.pf:
        self.stack.append(("OUT1", self.l1))
        self.l1 = ""
        self.parseOUT1(s)
        self.stack.pop()
      self.pf = True
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
        self.tb = str(ord(s.get()))
        s.advance(1)
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
        if self.of: self.ob += self.tb
        if self.of: self.ob += ' <= ord(s.get()) <= '
        self.stack.append(("CX3", self.l1))
        self.l1 = ""
        self.parseCX3(s)
        self.stack.pop()
        if not self.pf: self.error(s.i)
        if self.of: self.ob += self.tb
      if not self.pf:
        self.pf = True
        if self.pf:
          pass
          if self.of: self.ob += 'ord(s.get()) == '
          if self.of: self.ob += self.tb
      if not self.pf: self.error(s.i)
  def parseCX1(self, s):
    if self.of: self.ob += 'self.pf = '
    if True:
      pass
      self.stack.append(("CX2", self.l1))
      self.l1 = ""
      self.parseCX2(s)
      self.stack.pop()
      if not self.pf: self.error(s.i)
      while self.pf:
        s.eatWhitespace()
        self.pf = s.matches("!")
        if self.pf: s.advance(len("!"))
        if self.pf:
          pass
          if self.of: self.ob += ' or '
          self.stack.append(("CX2", self.l1))
          self.l1 = ""
          self.parseCX2(s)
          self.stack.pop()
          if not self.pf: self.error(s.i)
      self.pf = True
      if self.of:
        print " " * (self.m * 2) + self.ob
        self.ob = ""
      self.apf = 0
  def parseSCAN(self, s):
    if (self.apf == 1):
      pass
      if (self.atf == 1):
        pass
        if self.of: self.ob += 'self.tb += s.get()'
        if self.of:
          print " " * (self.m * 2) + self.ob
          self.ob = ""
        if True:
          pass
      if self.pf:
        pass
        if (self.atf == 0):
          pass
          if self.of: self.ob += 'if self.tf: self.tb += s.get()'
          if self.of:
            print " " * (self.m * 2) + self.ob
            self.ob = ""
          if True:
            pass
        if not self.pf: self.error(s.i)
        if self.of: self.ob += 's.advance(1)'
        if self.of:
          print " " * (self.m * 2) + self.ob
          self.ob = ""
    if self.pf:
      pass
      if (self.apf == 0):
        pass
        if self.of: self.ob += 'if self.pf:'
        if self.of:
          print " " * (self.m * 2) + self.ob
          self.ob = ""
        if self.of: self.m += 1
        if True:
          pass
          if (self.atf == 1):
            pass
            if self.of: self.ob += 'self.tb += s.get()'
            if self.of:
              print " " * (self.m * 2) + self.ob
              self.ob = ""
            if True:
              pass
          if not self.pf: self.error(s.i)
          if (self.atf == 0):
            pass
            if self.of: self.ob += 'if self.tf: self.tb += s.get()'
            if self.of:
              print " " * (self.m * 2) + self.ob
              self.ob = ""
            if True:
              pass
          if not self.pf: self.error(s.i)
          if self.of: self.ob += 's.advance(1)'
          if self.of:
            print " " * (self.m * 2) + self.ob
            self.ob = ""
          if self.of and self.m: self.m -= 1
      if not self.pf: self.error(s.i)
  def parseSUB(self, s):
    self.stack.append(("ID", self.l1))
    self.l1 = ""
    self.parseID(s)
    self.stack.pop()
    if self.pf:
      pass
      if self.of: self.ob += 'self.stack.append(("'
      if self.of: self.ob += self.tb
      if self.of: self.ob += '", self.l1))'
      if self.of:
        print " " * (self.m * 2) + self.ob
        self.ob = ""
      if self.of: self.ob += 'self.l1 = ""'
      if self.of:
        print " " * (self.m * 2) + self.ob
        self.ob = ""
      if self.of: self.ob += 'self.parse'
      if self.of: self.ob += self.tb
      if self.of: self.ob += '(s)'
      if self.of:
        print " " * (self.m * 2) + self.ob
        self.ob = ""
      if self.of: self.ob += 'self.stack.pop()'
      if self.of:
        print " " * (self.m * 2) + self.ob
        self.ob = ""
      self.top()
  def parseSET(self, s):
    if (not (self.apf == 1)):
      pass
      if self.of: self.ob += 'self.pf = True'
      if self.of:
        print " " * (self.m * 2) + self.ob
        self.ob = ""
      if True:
        pass
    if self.pf:
      pass
      self.apf = 1
  def parseTX3(self, s):
    s.eatWhitespace()
    self.pf = s.matches(".token")
    if self.pf: s.advance(len(".token"))
    if self.pf:
      pass
      if self.of: self.ob += 'self.tb = ""'
      if self.of:
        print " " * (self.m * 2) + self.ob
        self.ob = ""
      if (not (self.atf == 1)):
        pass
        if self.of: self.ob += 'self.tf = True'
        if self.of:
          print " " * (self.m * 2) + self.ob
          self.ob = ""
        if True:
          pass
      if not self.pf: self.error(s.i)
      self.atf = 1
    if not self.pf:
      s.eatWhitespace()
      self.pf = s.matches(".tokout")
      if self.pf: s.advance(len(".tokout"))
      if self.pf:
        pass
        if (not (self.atf == 2)):
          pass
          if self.of: self.ob += 'self.tf = False'
          if self.of:
            print " " * (self.m * 2) + self.ob
            self.ob = ""
          if True:
            pass
        if not self.pf: self.error(s.i)
        self.atf = 2
    if not self.pf:
      s.eatWhitespace()
      self.pf = s.matches("$")
      if self.pf: s.advance(len("$"))
      if self.pf:
        pass
        self.stack.append(("SET", self.l1))
        self.l1 = ""
        self.parseSET(s)
        self.stack.pop()
        if not self.pf: self.error(s.i)
        if self.of: self.ob += 'while self.pf:'
        if self.of:
          print " " * (self.m * 2) + self.ob
          self.ob = ""
        if self.of: self.m += 1
        self.apf = 1
        self.stack.append(("TX3", self.l1))
        self.l1 = ""
        self.parseTX3(s)
        self.stack.pop()
        if not self.pf: self.error(s.i)
        if self.of and self.m: self.m -= 1
        self.apf = 2
    if self.pf:
      pass
      self.stack.append(("SET", self.l1))
      self.l1 = ""
      self.parseSET(s)
      self.stack.pop()
      if not self.pf: self.error(s.i)
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
        if self.of: self.ob += 'self.pf = not self.pf'
        if self.of:
          print " " * (self.m * 2) + self.ob
          self.ob = ""
        self.apf = 0
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
      if self.of: self.ob += 'if self.pf:'
      if self.of:
        print " " * (self.m * 2) + self.ob
        self.ob = ""
      if self.of: self.m += 1
      if self.of: self.ob += 'pass'
      if self.of:
        print " " * (self.m * 2) + self.ob
        self.ob = ""
      self.apf = 1
      while self.pf:
        self.stack.append(("TX3", self.l1))
        self.l1 = ""
        self.parseTX3(s)
        self.stack.pop()
        if self.pf:
          pass
          if (not (self.apf == 1)):
            pass
            if self.of: self.ob += 'if not self.pf: return'
            if self.of:
              print " " * (self.m * 2) + self.ob
              self.ob = ""
            if True:
              pass
          if not self.pf: self.error(s.i)
          self.apf = 1
      self.pf = True
      if self.of and self.m: self.m -= 1
  def parseTX1(self, s):
    self.stack.append(("TX2", self.l1))
    self.l1 = ""
    self.parseTX2(s)
    self.stack.pop()
    if self.pf:
      pass
      while self.pf:
        s.eatWhitespace()
        self.pf = s.matches("/")
        if self.pf: s.advance(len("/"))
        if self.pf:
          pass
          if self.of: self.ob += 'if not self.pf:'
          if self.of:
            print " " * (self.m * 2) + self.ob
            self.ob = ""
          if self.of: self.m += 1
          self.apf = 2
          self.stack.append(("TX2", self.l1))
          self.l1 = ""
          self.parseTX2(s)
          self.stack.pop()
          if not self.pf: self.error(s.i)
          if self.of and self.m: self.m -= 1
          self.apf = 0
      self.pf = True
  def parseTR(self, s):
    self.stack.append(("ID", self.l1))
    self.l1 = ""
    self.parseID(s)
    self.stack.pop()
    if self.pf:
      pass
      if self.of: self.ob += 'def parse'
      if self.of: self.ob += self.tb
      if self.of: self.ob += '(self, s):'
      if self.of:
        print " " * (self.m * 2) + self.ob
        self.ob = ""
      if self.of: self.m += 1
      s.eatWhitespace()
      self.pf = s.matches(":")
      if self.pf: s.advance(len(":"))
      if not self.pf: self.error(s.i)
      self.top()
      self.stack.append(("TX1", self.l1))
      self.l1 = ""
      self.parseTX1(s)
      self.stack.pop()
      if not self.pf: self.error(s.i)
      s.eatWhitespace()
      self.pf = s.matches(";")
      if self.pf: s.advance(len(";"))
      if not self.pf: self.error(s.i)
      if self.of and self.m: self.m -= 1
  def parseTVAR(self, s):
    s.eatWhitespace()
    self.pf = s.matches("~")
    if self.pf: s.advance(len("~"))
    if self.pf:
      pass
      if self.of: self.ob += '(not '
      self.stack.append(("TVAR", self.l1))
      self.l1 = ""
      self.parseTVAR(s)
      self.stack.pop()
      if not self.pf: self.error(s.i)
      if self.of: self.ob += ')'
    if not self.pf:
      s.eatWhitespace()
      self.pf = s.matches("?")
      if self.pf: s.advance(len("?"))
      if self.pf:
        pass
        self.stack.append(("ID", self.l1))
        self.l1 = ""
        self.parseID(s)
        self.stack.pop()
        if not self.pf: self.error(s.i)
        if self.of: self.ob += '(self.a'
        if self.of: self.ob += self.tb
        if self.of: self.ob += ' == 0)'
    if not self.pf:
      s.eatWhitespace()
      self.pf = s.matches("+")
      if self.pf: s.advance(len("+"))
      if self.pf:
        pass
        self.stack.append(("ID", self.l1))
        self.l1 = ""
        self.parseID(s)
        self.stack.pop()
        if not self.pf: self.error(s.i)
        if self.of: self.ob += '(self.a'
        if self.of: self.ob += self.tb
        if self.of: self.ob += ' == 1)'
    if not self.pf:
      s.eatWhitespace()
      self.pf = s.matches("-")
      if self.pf: s.advance(len("-"))
      if self.pf:
        pass
        self.stack.append(("ID", self.l1))
        self.l1 = ""
        self.parseID(s)
        self.stack.pop()
        if not self.pf: self.error(s.i)
        if self.of: self.ob += '(self.a'
        if self.of: self.ob += self.tb
        if self.of: self.ob += ' == 2)'
  def parseAVAR(self, s):
    s.eatWhitespace()
    self.pf = s.matches("?")
    if self.pf: s.advance(len("?"))
    if self.pf:
      pass
      self.stack.append(("ID", self.l1))
      self.l1 = ""
      self.parseID(s)
      self.stack.pop()
      if not self.pf: self.error(s.i)
      if self.of: self.ob += 'self.a'
      if self.of: self.ob += self.tb
      if self.of: self.ob += ' = 0'
      if self.of:
        print " " * (self.m * 2) + self.ob
        self.ob = ""
    if not self.pf:
      s.eatWhitespace()
      self.pf = s.matches("+")
      if self.pf: s.advance(len("+"))
      if self.pf:
        pass
        self.stack.append(("ID", self.l1))
        self.l1 = ""
        self.parseID(s)
        self.stack.pop()
        if not self.pf: self.error(s.i)
        if self.of: self.ob += 'self.a'
        if self.of: self.ob += self.tb
        if self.of: self.ob += ' = 1'
        if self.of:
          print " " * (self.m * 2) + self.ob
          self.ob = ""
    if not self.pf:
      s.eatWhitespace()
      self.pf = s.matches("-")
      if self.pf: s.advance(len("-"))
      if self.pf:
        pass
        self.stack.append(("ID", self.l1))
        self.l1 = ""
        self.parseID(s)
        self.stack.pop()
        if not self.pf: self.error(s.i)
        if self.of: self.ob += 'self.a'
        if self.of: self.ob += self.tb
        if self.of: self.ob += ' = 2'
        if self.of:
          print " " * (self.m * 2) + self.ob
          self.ob = ""
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
        if self.of: self.ob += 's.eatWhitespace()'
        if self.of:
          print " " * (self.m * 2) + self.ob
          self.ob = ""
        if self.of: self.ob += 'self.pf = s.matches("'
        if self.of: self.ob += self.tb
        if self.of: self.ob += '")'
        if self.of:
          print " " * (self.m * 2) + self.ob
          self.ob = ""
        if self.of: self.ob += 'if self.pf: s.advance(len("'
        if self.of: self.ob += self.tb
        if self.of: self.ob += '"))'
        if self.of:
          print " " * (self.m * 2) + self.ob
          self.ob = ""
        self.apf = 0
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
      self.pf = s.matches(".pre")
      if self.pf: s.advance(len(".pre"))
      if self.pf:
        pass
        s.eatWhitespace()
        self.pf = s.matches("{")
        if self.pf: s.advance(len("{"))
        if not self.pf: self.error(s.i)
        if self.of: self.ob += 'if '
        self.stack.append(("TVAR", self.l1))
        self.l1 = ""
        self.parseTVAR(s)
        self.stack.pop()
        if not self.pf: self.error(s.i)
        while self.pf:
          s.eatWhitespace()
          self.pf = s.matches(",")
          if self.pf: s.advance(len(","))
          if self.pf:
            pass
            if self.of: self.ob += ' and '
            self.stack.append(("TVAR", self.l1))
            self.l1 = ""
            self.parseTVAR(s)
            self.stack.pop()
            if not self.pf: self.error(s.i)
        self.pf = True
        if self.of: self.ob += ':'
        if self.of:
          print " " * (self.m * 2) + self.ob
          self.ob = ""
        if self.of: self.m += 1
        if self.of: self.ob += 'pass'
        if self.of:
          print " " * (self.m * 2) + self.ob
          self.ob = ""
        s.eatWhitespace()
        self.pf = s.matches("}")
        if self.pf: s.advance(len("}"))
        if not self.pf: self.error(s.i)
        s.eatWhitespace()
        self.pf = s.matches("{")
        if self.pf: s.advance(len("{"))
        if not self.pf: self.error(s.i)
        self.stack.append(("EX1", self.l1))
        self.l1 = ""
        self.parseEX1(s)
        self.stack.pop()
        if not self.pf: self.error(s.i)
        s.eatWhitespace()
        self.pf = s.matches("}")
        if self.pf: s.advance(len("}"))
        if not self.pf: self.error(s.i)
        if self.of and self.m: self.m -= 1
    if not self.pf:
      s.eatWhitespace()
      self.pf = s.matches(".post")
      if self.pf: s.advance(len(".post"))
      if self.pf:
        pass
        s.eatWhitespace()
        self.pf = s.matches("{")
        if self.pf: s.advance(len("{"))
        if not self.pf: self.error(s.i)
        self.stack.append(("AVAR", self.l1))
        self.l1 = ""
        self.parseAVAR(s)
        self.stack.pop()
        if not self.pf: self.error(s.i)
        while self.pf:
          s.eatWhitespace()
          self.pf = s.matches(",")
          if self.pf: s.advance(len(","))
          if self.pf:
            pass
            self.stack.append(("AVAR", self.l1))
            self.l1 = ""
            self.parseAVAR(s)
            self.stack.pop()
            if not self.pf: self.error(s.i)
        self.pf = True
        s.eatWhitespace()
        self.pf = s.matches("}")
        if self.pf: s.advance(len("}"))
        if not self.pf: self.error(s.i)
    if not self.pf:
      s.eatWhitespace()
      self.pf = s.matches(".fork")
      if self.pf: s.advance(len(".fork"))
      if self.pf:
        pass
    if not self.pf:
      s.eatWhitespace()
      self.pf = s.matches(".join")
      if self.pf: s.advance(len(".join"))
      if self.pf:
        pass
    if not self.pf:
      s.eatWhitespace()
      self.pf = s.matches(".top")
      if self.pf: s.advance(len(".top"))
      if self.pf:
        pass
        if self.of: self.ob += 'self.top()'
        if self.of:
          print " " * (self.m * 2) + self.ob
          self.ob = ""
    if not self.pf:
      s.eatWhitespace()
      self.pf = s.matches(".empty")
      if self.pf: s.advance(len(".empty"))
      if self.pf:
        pass
        self.stack.append(("SET", self.l1))
        self.l1 = ""
        self.parseSET(s)
        self.stack.pop()
        if not self.pf: self.error(s.i)
    if not self.pf:
      s.eatWhitespace()
      self.pf = s.matches(".litchr")
      if self.pf: s.advance(len(".litchr"))
      if self.pf:
        pass
        self.stack.append(("SET", self.l1))
        self.l1 = ""
        self.parseSET(s)
        self.stack.pop()
        if not self.pf: self.error(s.i)
        if self.of: self.ob += 'self.tb = str(ord(s.get()))'
        if self.of:
          print " " * (self.m * 2) + self.ob
          self.ob = ""
        if self.of: self.ob += 's.advance(1)'
        if self.of:
          print " " * (self.m * 2) + self.ob
          self.ob = ""
    if not self.pf:
      s.eatWhitespace()
      self.pf = s.matches(".o+")
      if self.pf: s.advance(len(".o+"))
      if self.pf:
        pass
        if self.of: self.ob += 'self.of = True'
        if self.of:
          print " " * (self.m * 2) + self.ob
          self.ob = ""
    if not self.pf:
      s.eatWhitespace()
      self.pf = s.matches(".o-")
      if self.pf: s.advance(len(".o-"))
      if self.pf:
        pass
        if self.of: self.ob += 'self.of = False'
        if self.of:
          print " " * (self.m * 2) + self.ob
          self.ob = ""
    if not self.pf:
      s.eatWhitespace()
      self.pf = s.matches(".pass")
      if self.pf: s.advance(len(".pass"))
      if self.pf:
        pass
        if self.of: self.ob += 's.i = 0'
        if self.of:
          print " " * (self.m * 2) + self.ob
          self.ob = ""
    if not self.pf:
      s.eatWhitespace()
      self.pf = s.matches("$")
      if self.pf: s.advance(len("$"))
      if self.pf:
        pass
        self.stack.append(("SET", self.l1))
        self.l1 = ""
        self.parseSET(s)
        self.stack.pop()
        if not self.pf: self.error(s.i)
        if self.of: self.ob += 'while self.pf:'
        if self.of:
          print " " * (self.m * 2) + self.ob
          self.ob = ""
        if self.of: self.m += 1
        self.apf = 1
        self.stack.append(("EX3", self.l1))
        self.l1 = ""
        self.parseEX3(s)
        self.stack.pop()
        if not self.pf: self.error(s.i)
        if self.of and self.m: self.m -= 1
        self.apf = 2
        self.stack.append(("SET", self.l1))
        self.l1 = ""
        self.parseSET(s)
        self.stack.pop()
        if not self.pf: self.error(s.i)
  def parseEX2(self, s):
    self.stack.append(("EX3", self.l1))
    self.l1 = ""
    self.parseEX3(s)
    self.stack.pop()
    if self.pf:
      pass
      if self.of: self.ob += 'if self.pf:'
      self.apf = 1
    if not self.pf:
      self.stack.append(("OUTPUT", self.l1))
      self.l1 = ""
      self.parseOUTPUT(s)
      self.stack.pop()
      if self.pf:
        pass
        if self.of: self.ob += 'if True:'
    if self.pf:
      pass
      if self.of:
        print " " * (self.m * 2) + self.ob
        self.ob = ""
      if self.of: self.m += 1
      if self.of: self.ob += 'pass'
      if self.of:
        print " " * (self.m * 2) + self.ob
        self.ob = ""
      while self.pf:
        self.stack.append(("EX3", self.l1))
        self.l1 = ""
        self.parseEX3(s)
        self.stack.pop()
        if self.pf:
          pass
          if (not (self.apf == 1)):
            pass
            if self.of: self.ob += 'if not self.pf: self.error(s.i)'
            if self.of:
              print " " * (self.m * 2) + self.ob
              self.ob = ""
            if True:
              pass
          if not self.pf: self.error(s.i)
          self.apf = 1
        if not self.pf:
          self.stack.append(("OUTPUT", self.l1))
          self.l1 = ""
          self.parseOUTPUT(s)
          self.stack.pop()
          if self.pf:
            pass
      self.pf = True
      if self.of and self.m: self.m -= 1
      self.apf = 0
  def parseEX1(self, s):
    self.stack.append(("EX2", self.l1))
    self.l1 = ""
    self.parseEX2(s)
    self.stack.pop()
    if self.pf:
      pass
      while self.pf:
        s.eatWhitespace()
        self.pf = s.matches("/")
        if self.pf: s.advance(len("/"))
        if self.pf:
          pass
          if self.of: self.ob += 'if not self.pf:'
          if self.of:
            print " " * (self.m * 2) + self.ob
            self.ob = ""
          if self.of: self.m += 1
          self.stack.append(("EX2", self.l1))
          self.l1 = ""
          self.parseEX2(s)
          self.stack.pop()
          if not self.pf: self.error(s.i)
          if self.of and self.m: self.m -= 1
      self.pf = True
  def parsePR(self, s):
    self.stack.append(("ID", self.l1))
    self.l1 = ""
    self.parseID(s)
    self.stack.pop()
    if self.pf:
      pass
      if self.of: self.ob += 'def parse'
      if self.of: self.ob += self.tb
      if self.of: self.ob += '(self, s):'
      if self.of:
        print " " * (self.m * 2) + self.ob
        self.ob = ""
      if self.of: self.m += 1
      s.eatWhitespace()
      self.pf = s.matches("=")
      if self.pf: s.advance(len("="))
      if not self.pf: self.error(s.i)
      self.top()
      self.stack.append(("EX1", self.l1))
      self.l1 = ""
      self.parseEX1(s)
      self.stack.pop()
      if not self.pf: self.error(s.i)
      s.eatWhitespace()
      self.pf = s.matches(";")
      if self.pf: s.advance(len(";"))
      if not self.pf: self.error(s.i)
      if self.of and self.m: self.m -= 1
  def parseTY(self, s):
    s.eatWhitespace()
    self.pf = s.matches("bool")
    if self.pf: s.advance(len("bool"))
    if self.pf:
      pass
      if self.of: self.ob += '0'
  def parseDR(self, s):
    self.stack.append(("ID", self.l1))
    self.l1 = ""
    self.parseID(s)
    self.stack.pop()
    if self.pf:
      pass
      s.eatWhitespace()
      self.pf = s.matches(":")
      if self.pf: s.advance(len(":"))
      if not self.pf: self.error(s.i)
      if self.of: self.ob += 'self.a'
      if self.of: self.ob += self.tb
      if self.of: self.ob += ' = '
      self.stack.append(("TY", self.l1))
      self.l1 = ""
      self.parseTY(s)
      self.stack.pop()
      if not self.pf: self.error(s.i)
      s.eatWhitespace()
      self.pf = s.matches(";")
      if self.pf: s.advance(len(";"))
      if not self.pf: self.error(s.i)
      if self.of:
        print " " * (self.m * 2) + self.ob
        self.ob = ""
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
      if self.of: self.ob += 'class '
      if self.of: self.ob += self.tb
      if self.of: self.ob += 'Parser(object):'
      if self.of:
        print " " * (self.m * 2) + self.ob
        self.ob = ""
      if self.of: self.m += 1
      if self.of: self.ob += 'u = 0'
      if self.of:
        print " " * (self.m * 2) + self.ob
        self.ob = ""
      if self.of: self.ob += 'pf = tf = False'
      if self.of:
        print " " * (self.m * 2) + self.ob
        self.ob = ""
      if self.of: self.ob += 'of = True'
      if self.of:
        print " " * (self.m * 2) + self.ob
        self.ob = ""
      if self.of: self.ob += 'l1 = tb = ""'
      if self.of:
        print " " * (self.m * 2) + self.ob
        self.ob = ""
      if self.of: self.ob += 'm = 0'
      if self.of:
        print " " * (self.m * 2) + self.ob
        self.ob = ""
      if self.of: self.ob += 'ob = ""'
      if self.of:
        print " " * (self.m * 2) + self.ob
        self.ob = ""
      if self.of: self.ob += 'def __init__(self): self.top(); self.stack = []'
      if self.of:
        print " " * (self.m * 2) + self.ob
        self.ob = ""
      if self.of: self.ob += 'def parse(self, s): self.top(); return self.parse'
      if self.of: self.ob += self.tb
      if self.of: self.ob += '(s)'
      if self.of:
        print " " * (self.m * 2) + self.ob
        self.ob = ""
      if self.of: self.ob += 'def unique(self):'
      if self.of:
        print " " * (self.m * 2) + self.ob
        self.ob = ""
      if self.of: self.m += 1
      if self.of: self.ob += 'if not self.l1: self.l1 = str(self.u); self.u += 1'
      if self.of:
        print " " * (self.m * 2) + self.ob
        self.ob = ""
      if self.of: self.ob += 'return self.l1'
      if self.of:
        print " " * (self.m * 2) + self.ob
        self.ob = ""
      if self.of and self.m: self.m -= 1
      if self.of: self.ob += 'def error(self, i): raise ValueError("meh")'
      if self.of:
        print " " * (self.m * 2) + self.ob
        self.ob = ""
      while self.pf:
        self.stack.append(("PR", self.l1))
        self.l1 = ""
        self.parsePR(s)
        self.stack.pop()
      self.pf = True
      s.eatWhitespace()
      self.pf = s.matches(".tokens")
      if self.pf: s.advance(len(".tokens"))
      if not self.pf: self.error(s.i)
      while self.pf:
        self.stack.append(("TR", self.l1))
        self.l1 = ""
        self.parseTR(s)
        self.stack.pop()
      self.pf = True
      if self.of: self.ob += 'def top(self):'
      if self.of:
        print " " * (self.m * 2) + self.ob
        self.ob = ""
      if self.of: self.m += 1
      if self.of: self.ob += 'pass'
      if self.of:
        print " " * (self.m * 2) + self.ob
        self.ob = ""
      s.eatWhitespace()
      self.pf = s.matches(".domain")
      if self.pf: s.advance(len(".domain"))
      if not self.pf: self.error(s.i)
      while self.pf:
        self.stack.append(("DR", self.l1))
        self.l1 = ""
        self.parseDR(s)
        self.stack.pop()
      self.pf = True
      if self.of and self.m: self.m -= 1
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
      self.tb = ""
      self.tf = True
      while self.pf:
        self.pf = ord(s.get()) == 10 or ord(s.get()) == 13 or ord(s.get()) == 39
        self.pf = not self.pf
        if self.pf:
          self.tb += s.get()
          s.advance(1)
      self.pf = True
      self.tf = False
      self.pf = ord(s.get()) == 39
      if self.pf:
        s.advance(1)
      if not self.pf: return
  def parseNUMBER(self, s):
    self.stack.append(("WS", self.l1))
    self.l1 = ""
    self.parseWS(s)
    self.stack.pop()
    if self.pf:
      pass
      self.tb = ""
      self.tf = True
      self.stack.append(("DIGIT", self.l1))
      self.l1 = ""
      self.parseDIGIT(s)
      self.stack.pop()
      if not self.pf: return
      while self.pf:
        self.stack.append(("DIGIT", self.l1))
        self.l1 = ""
        self.parseDIGIT(s)
        self.stack.pop()
      self.pf = True
      self.tf = False
  def parseID(self, s):
    self.stack.append(("WS", self.l1))
    self.l1 = ""
    self.parseWS(s)
    self.stack.pop()
    if self.pf:
      pass
      self.tb = ""
      self.tf = True
      self.stack.append(("ALPHA", self.l1))
      self.l1 = ""
      self.parseALPHA(s)
      self.stack.pop()
      if not self.pf: return
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
      self.tf = False
  def top(self):
    pass
    self.apf = 0
    self.atf = 0
