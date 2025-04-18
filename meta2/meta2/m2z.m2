.syntax PROGRAM

OUT1 = '*'     .out('ci' .nl)
     / STRING  .out('cl ' 39 * 39 .nl)
     / NUMBER  .out('cc ' * .nl)
     / '#'     .out('gn' .nl)
     / '.nl'   .out('nl' .nl)
     / '.lm+'  .out('lmi' .nl)
     / '.lm-'  .out('lmd' .nl) ;
OUTPUT = '.out' '(' $OUT1 ')' ;

CX3 = NUMBER / SQUOTE .litchr ;
CX2 = CX3 ( ':' .out('cge ' * .nl 'bf d'# .nl)
            CX3 .out('cle ' * .nl .lm- 'd'# .nl .lm+)
          / .empty .out('ce ' * .nl) ) ;
CX1 = CX2 $( '!' .out('bt c'# .nl) CX2 ) .out(.lm- 'c'# .nl .lm+) ;

TX3 = ( '.token' .out('tft' .nl)
      / '.tokout' .out('tff' .nl)
      / '$' .out(.lm- 't'# .nl .lm+) TX3 .out('bt t'# .nl) ) .out('set' .nl)
    / '.not(' CX1 ')' .out('not' .nl 'scn' .nl)
    / '.any(' CX1 ')' .out('scn' .nl)
    / ID .out('cll ' * .nl)
    / '(' TX1 ')' ;
TX2 = TX3 .out('bf t'# .nl)
      $( TX3 .out('rf' .nl) )
      .out(.lm- 't'# .nl .lm+) ;
TX1 = TX2 $( '/' .out('bt t'# .nl) TX2 ) .out(.lm- 't'# .nl .lm+) ;
TR = ID .out(.lm- * .nl .lm+) ':' TX1 ';' .out('r' .nl) ;

EX3 = ID .out('cll ' * .nl)
    / STRING .out('tst ' 39 * 39 .nl)
    / '(' EX1 ')'
    / '.empty' .out('set' .nl)
    / '.litchr' .out('lch' .nl)
    / '$' .out(.lm- 'l'# .nl .lm+) EX3 .out('bt l'# .nl 'set' .nl) ;
EX2 = ( EX3 .out('bf l'# .nl) / OUTPUT )
      $( EX3 .out('be' .nl) / OUTPUT )
      .out(.lm- 'l'# .nl .lm+) ;
EX1 = EX2 $( '/' .out('bt l'# .nl) EX2 ) .out(.lm- 'l'# .nl .lm+) ;

PR = ID .out(.lm- * .nl .lm+) '=' EX1 ';' .out('r' .nl) ;

PROGRAM = '.syntax' ID .out(.lm+ 'adr ' * .nl) $PR
          '.tokens' $TR
          '.end' .out('end' .nl) ;

.tokens

WS     : $.any(9!10!13!32) ;
DIGIT  : .any('0:'9) ;
ALPHA  : .any('A:'Z!'a:'z) ;
SQUOTE : WS .any(39) ;
STRING : WS .any(39) .token $.not(10!13!39) .tokout .any(39) ;
NUMBER : WS .token DIGIT $DIGIT .tokout ;
ID     : WS .token ALPHA $( ALPHA / DIGIT ) .tokout ;

.end
