.syntax PROGRAM

OUT1 = '*'     .out('self.ob += self.tb' .nl)
     / STRING  .out('self.ob += ' 39 * 39 .nl)
     / NUMBER  .out('self.ob += chr(' * ')' .nl)
     / '#'     .out('self.ob += self.unique()' .nl)
     / '.lm+'  .out('self.m += 1' .nl)
     / '.lm-'  .out('if self.m: self.m -= 1' .nl)
     / '.nl'   .out(
       'print " " * (self.m * 2) + self.ob' .nl
       'self.ob = ""' .nl
     ) ;
OUTPUT = '.out' '(' $OUT1 ')' ;

CX3 = NUMBER / SQUOTE .litchr ;
CX2 = CX3 ( ':' .out(* ' <= ord(s.get()) <= ') CX3 .out(*)
          / .empty .out('ord(s.get()) == ' *) ) ;
CX1 = .out('self.pf = ') CX2 $( '!' .out(' or ') CX2 ) .out(.nl) ;

SCAN = .out(
         'if self.pf:' .nl .lm+
         'if self.tf: self.tb += s.get()' .nl
         's.advance(1)' .nl .lm-
       ) ;
SUB = ID .out(
        'self.stack.append(("' * '", self.l1))' .nl
        'self.l1 = ""' .nl
        'self.parse' * '(s)' .nl
        'self.stack.pop()' .nl
      ) ;

TX3 = ( '.token' .out('self.tf = True' .nl 'self.tb = ""' .nl)
      / '.tokout' .out('self.tf = False' .nl)
      / '$' .out('self.pf = True' .nl 'while self.pf:' .nl .lm+) TX3 .out(.lm-) )
        .out('self.pf = True' .nl)
    / '.not(' CX1 ')' .out('self.pf = not self.pf' .nl) SCAN
    / '.any(' CX1 ')' SCAN
    / SUB
    / '(' TX1 ')' ;
TX2 = TX3 .out('if self.pf:' .nl .lm+ 'pass' .nl)
      $( TX3 .out('if not self.pf: return' .nl) )
      .out(.lm-) ;
TX1 = TX2 $( '/' .out('if not self.pf:' .nl .lm+) TX2 .out(.lm-) ) ;
TR = ID .out('def parse' * '(self, s):' .nl .lm+) ':' TX1 ';' .out(.lm-) ;

EX3 = SUB
    / STRING .out(
      's.eatWhitespace()' .nl
      'self.pf = s.matches("' * '")' .nl
      'if self.pf: s.advance(len("' * '"))' .nl
    )
    / '(' EX1 ')'
    / '.empty' .out('self.pf = True' .nl)
    / '.litchr' .out(
      'self.pf = True' .nl
      'self.tb = str(ord(s.get()))' .nl
      's.advance(1)' .nl
    )
    / '.pass' .out('s.i = 0' .nl)
    / '$' .out('self.pf = True' .nl 'while self.pf:' .nl .lm+)
      EX3 .out(.lm- 'self.pf = True' .nl) ;
EX2 = ( EX3 .out('if self.pf:') / OUTPUT .out('if True:') )
      .out(.nl .lm+ 'pass' .nl)
      $( EX3 .out('if not self.pf: self.error(s.i)' .nl) / OUTPUT )
      .out(.lm-) ;
EX1 = EX2 $( '/' .out('if not self.pf:' .nl .lm+) EX2 .out(.lm-) ) ;

PR = ID .out('def parse' * '(self, s):' .nl .lm+) '=' EX1 ';' .out(.lm-) ;

PROGRAM = '.syntax' ID .out(
            'class ' * 'Parser(object):' .nl .lm+
            'u = 0' .nl
            'pf = tf = False' .nl
            'l1 = tb = ""' .nl
            'm = 0' .nl
            'ob = ""' .nl
            'def __init__(self): self.stack = []' .nl
            'def parse(self, s): return self.parse' * '(s)' .nl
            'def unique(self):' .nl .lm+
            'if not self.l1: self.l1 = str(self.u); self.u += 1' .nl
            'return self.l1' .nl .lm-
            'def error(self, i): raise ValueError("meh")' .nl
          )
          $PR '.tokens' $TR
          ( '.domain' / .empty )
          '.end' ;

.tokens

WS     : $.any(9!10!13!32) ;
DIGIT  : .any('0:'9) ;
ALPHA  : .any('A:'Z!'a:'z) ;
SQUOTE : WS .any(39) ;
STRING : WS .any(39) .token $.not(10!13!39) .tokout .any(39) ;
NUMBER : WS .token DIGIT $DIGIT .tokout ;
ID     : WS .token ALPHA $( ALPHA / DIGIT ) .tokout ;

.end
