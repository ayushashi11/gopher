from antlr4 import *
from GopherLexer import GopherLexer
from GopherParser import GopherParser
from Gophisitor import Gophisitor
lexer = GopherLexer(FileStream("oop.gopr"))
stream = CommonTokenStream(lexer)
parser = GopherParser(stream)
tree = parser.program()
gophisitor = Gophisitor()
gophisitor.visit(tree)
