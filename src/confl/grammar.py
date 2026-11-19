"""Lark grammar of the educational configuration language (variant 26)."""

GRAMMAR = r"""
start: definition* value

definition: _DEF NAME _EQ value _SEMI

?value: NUMBER -> number
      | dict
      | const_expr

dict: _TABLE _LPAR (entry (_COMMA entry)* _COMMA?)? _RPAR

entry: NAME _ARROW value

const_expr: _LSQB atom+ _RSQB

?atom: NUMBER
     | NAME
     | PLUS
     | POW
     | SQRT

_DEF: "def"
_TABLE: "table"
_EQ: "="
_ARROW: "=>"
_SEMI: ";"
_COMMA: ","
_LPAR: "("
_RPAR: ")"
_LSQB: "["
_RSQB: "]"
PLUS: "+"
POW: /pow(\(\))?/
SQRT: /sqrt(\(\))?/
NAME: /[_A-Z][_a-zA-Z0-9]*/
NUMBER: /[0-9]+/

LINE_COMMENT: /"[^\n]*/
BLOCK_COMMENT: /\|#[\s\S]*?#\|/
WS: /[ \t\r\n]+/

%ignore WS
%ignore LINE_COMMENT
%ignore BLOCK_COMMENT
"""