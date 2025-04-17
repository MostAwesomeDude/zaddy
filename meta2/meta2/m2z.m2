.syntax PROGRAM

OUT1 = '*'     .out(.tb 'ci' .nl)
     / STRING  .out(.tb 'cl ' 39 * 39 .nl)
     / NUMBER  .out(.tb 'cc ' * .nl)
     / '#'     .out(.tb 'gn' .nl)
     / '.nl'   .out(.tb 'nl' .nl)
     / '.lb'   .out(.tb 'lb' .nl)
     / '.tb'   .out(.tb 'tb' .nl)
     / '.lm+'  .out(.tb 'lmi' .nl)
     / '.lm-'  .out(.tb 'lmd' .nl) ;
OUTPUT = '.out' '(' $OUT1 ')' ;

CX3 = NUMBER / SQUOTE .litchr ;
CX2 = CX3 ( ':' .out(.tb 'cge ' * .nl .tb 'bf d'# .nl)
            CX3 .out(.tb 'cle ' * .nl .lb 'd'# .nl)
          / .empty .out(.tb 'ce ' * .nl) ) ;
CX1 = CX2 $( '!' .out(.tb 'bt c'# .nl) CX2 ) .out(.lb 'c'# .nl) ;

TX3 = ( '.token' .out(.tb 'tft' .nl)
      / '.tokout' .out(.tb 'tff' .nl)
      / '$' .out(.lb 't'# .nl) TX3 .out(.tb 'bt t'# .nl) ) .out(.tb 'set' .nl)
    / '.not(' CX1 ')' .out(.tb 'not' .nl .tb 'scn' .nl)
    / '.any(' CX1 ')' .out(.tb 'scn' .nl)
    / ID .out(.tb 'cll ' * .nl)
    / '(' TX1 ')' ;
TX2 = TX3 .out(.tb 'bf t'# .nl)
      $( TX3 .out(.tb 'rf' .nl) )
      .out(.lb 't'# .nl) ;
TX1 = TX2 $( '/' .out(.tb 'bt t'# .nl) TX2 ) .out(.lb 't'# .nl) ;
TR = ID .out(.lb * .nl) ':' TX1 ';' .out(.tb 'r' .nl) ;

EX3 = ID .out(.tb 'cll ' * .nl)
    / STRING .out(.tb 'tst ' 39 * 39 .nl)
    / '(' EX1 ')'
    / '.empty' .out(.tb 'set' .nl)
    / '.litchr' .out(.tb 'lch' .nl)
    / '$' .out(.lb 'l'# .nl) EX3 .out(.tb 'bt l'# .nl .tb 'set' .nl) ;
EX2 = ( EX3 .out(.tb 'bf l'# .nl) / OUTPUT ) $( EX3 .out(.tb 'be' .nl) / OUTPUT ) .out(.lb 'l'# .nl) ;
EX1 = EX2 $( '/' .out(.tb 'bt l'# .nl) EX2 ) .out(.lb 'l'# .nl) ;

PR = ID .out(.lb * .nl) '=' EX1 ';' .out(.tb 'r' .nl) ;

PROGRAM = '.syntax' ID .out(.tb 'adr ' * .nl) $PR
          '.tokens' $TR
          '.end' .out(.tb 'end' .nl) ;

.tokens

WS     : $.any(9!10!13!32) ;
DIGIT  : .any('0:'9) ;
ALPHA  : .any('A:'Z!'a:'z) ;
SQUOTE : WS .any(39) ;
STRING : WS .any(39) .token $.not(10!13!39) .tokout .any(39) ;
NUMBER : WS .token DIGIT $DIGIT .tokout ;
ID     : WS .token ALPHA $( ALPHA / DIGIT ) .tokout ;

.end
