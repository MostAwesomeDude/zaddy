" Vim syntax file
" Language: Zaddy
" Maintainer: Corbin
" Latest Revision: 13 July 2025

if exists("b:current_syntax")
    finish
endif

syn iskeyword .,48-57,65-90,97-122

syn keyword zHeader .signature .rules
syn keyword zForm .range .join .any
syn keyword zBuiltin .line .block .gensym
syn keyword zDecl let class token

syn region zStr start='\'' end='\''

syn match zNum '[0-9]\+'
syn match zVar '[A-Z][a-z0-9]*…\='
syn match zName '[a-z0-9]\+'
syn match zRule '[A-Za-z0-9]\+'
syn match zSplat '\*'
syn match zHash '#'
syn match zFlip '\~'
syn match zBang '!'
syn match zMark '?'
syn match zPlus '+'
syn match zAnd '&'

let b:current_syntax = "zaddy"

hi def link zHeader     Label
hi def link zStr        String
hi def link zVar        Identifier
hi def link zName       Type
hi def link zRule       Function
hi def link zSplat      Operator
hi def link zHash       Operator
hi def link zFlip       Operator
hi def link zBang       Operator
hi def link zMark       Operator
hi def link zPlus       Operator
hi def link zAnd        Operator
hi def link zDecl       Define
hi def link zForm       Operator
hi def link zBuiltin    Operator
hi def link zNum        Number
