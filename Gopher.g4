grammar Gopher;
program: block EOF;
block:(stmt)*;
stmt:incl_stmt ';'
|load_stmt ';'
|var ';'
|decl ';'
|class_stmt
|impl_stmt
|print_stmt ';'
|key ';'
|if_stmt
|while_stmt
|until_stmt
|for_stmt
|match_stmt
|label_def
|def_func_stmt
|id_call';'
|ext_call ';'
|goto_stmt';'
|return_stmt ';'
|expr ';';
key: 'key';
var: (VAR ID (':' DT)? CONSTASSIGN expr)|(ID (':' DT)? '=' expr)|(expr ASSIGN (DT':')?ID);
decl: recID '=' expr;
print_stmt: PRINT expr #print0
|PRINTLN expr #println
|OUTS expr expr expr  #fileouts;
label_def:LABEL ID stmt_block;
goto_stmt:GOTO ID;
class_stmt:CLASS ID (UNDER (EID=ID)+)? OBRACE var* CBRACE;
impl_stmt:'impl' ID OBRACE def_func_stmt* CBRACE;
class_inst:(ID|recID) OBRACE (expr(','expr)*) CBRACE;
def_func_stmt:FUNCTION FUNCID=ID OPAR (ID(','ID)*)?((','NID=ID '=' value)*)? CPAR stmt_block;
def_func_expr: '|' (ID(','ID)*)?((','NID=ID '=' value)*)? '|' '=>' stmt_block;
id_call: (ID|recID) REF_OP OPAR (expr(','expr)*)? CPAR;
ext_call: EXTCALL OPAR (expr(','expr)*)? CPAR (ID|recID);
recID: ID (REF_OP ID)+;
value:OPAR expr CPAR #parExpr
|DECIMAL #numberAtom
|EXPDECIMAL #expnumberAtom
|BOOL #boolAtom
|(ID|recID) #idAtom
|STRING #stringAtom
|list_var #listAtom
|linspace #listspaceAtom
|NULL #nullAtom
;
expr:INPUT expr #inputExpr
|ext_call #ext_callExpr
|id_call #id_callExpr 
|class_inst #class_instExpr
|def_func_expr #def_funcExpr
|<assoc=right>expr POW expr #powExpr
|MINUS expr #uminusExpr
|NOT expr #unotExpr
|expr op=(MULT|DIV|MOD) expr #multExpr
|expr op=(PLUS|MINUS) expr #addExpr
|expr op=(LTEQ|GTEQ|LT|GT) expr #relatExpr
|expr op=(EQ|NEQ) expr #eqExpr
|expr AND expr #andExpr
|expr OR expr #orExpr
|condexpr=expr '?' truexpr=expr ':' falsexpr=expr #tern_opExpr
|value #valueExpr
;
incl_stmt:INCLUDE (ID|recID);
load_stmt:LOAD (ID|recID);
for_stmt:FOR ID COL expr stmt_block;
match_stmt: MATCH expr OBRACE condition_block CBRACE (ELSE stmt_block)?;
until_stmt:UNTIL expr stmt_block;
while_stmt:WHILE expr stmt_block;
if_stmt:IF condition_block ((ELSE IF|ELSIF) condition_block)* (ELSE stmt_block)?;
condition_block:expr stmt_block;
stmt_block: OBRACE block CBRACE
|'\t'stmt
;
return_stmt:RET expr ;
DT: 'float'|'str'|'bool'|'list'|'any';
COL:':';
PRINT: 'print';
OUTS:'outs';
INCLUDE: 'incl';
LOAD: 'load';
EXTCALL: 'extcall';
PRINTLN: 'println';
INPUT: 'gets'|'input';
FUNCTION: 'function';
RET: 'ret';
LABEL: 'label';
CLASS: 'type';
UNDER: 'under';
GOTO: 'goto';
VAR: 'var';
IF: 'if';
ELSE:'else';
ELSIF: 'elsif';
UNTIL: 'until';
WHILE: 'while';
FOR: 'for';
MATCH:'match';
list_var: '['expr(','expr)*']';
linspace: 'l['expr','expr':'expr']';
BOOL:(TRUE|FALSE);
DECIMAL: [0-9]+('.'[0-9]*)?
|'.' [0-9]+;
EXPDECIMAL:DECIMAL'e'('+'|'-')[0-9]+;
TRUE:'true';
FALSE:'false';
NULL:'null';
REF_OP:'::';
OR:'or';
AND:'and';
EQ:'==';
NEQ:'!=';
GT:'>';
LT:'<';
GTEQ:'>=';
LTEQ:'<=';
POW: '**';
PLUS:'+';
MINUS:'-';
MULT:'*';
DIV:'/';
MOD:'%'|'rem';
NOT:'not';
ASSIGN:'->';
CONSTASSIGN:'is';
OPAR:'(';
CPAR:')';
OBRACE:'{';
CBRACE:'}';
STRING:'"'(~['"\n\r]|(OBRACE [a-zA-Z] CBRACE))*'"';
ID: [a-zA-Z_][a-zA-Z0-9_]*;
COMMENT:('#' ~[\r\n]* | '#*' .* '*#')->skip;
WS: [ \t\n\r]+ -> skip;