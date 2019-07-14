from importlib import __import__ as load
from antlr4 import *
import numpy as np
from GopherLexer import GopherLexer
from GopherParser import GopherParser
from GopherVisitor import GopherVisitor
tid = id
ftype = {'float': float,
         'str': str,
         'bool': bool,
         'list': list,
         'any': (lambda x: x)}


class DeclVisitor(GopherVisitor):

    memory = {'': 0}

    def visitPreproc(self, ctx: GopherParser.PreprocContext):
        print(ctx.getText())

    def visitLabel_def(self, ctx: GopherParser.Label_defContext):
        lblid = str(ctx.ID())
        self.memory[lblid] = ctx.stmt_block()
    
    def visitDef_func_stmt(self, ctx: GopherParser.Def_func_stmtContext):
        funcdata = ctx.ID()
        funcid = str(funcdata[0])
        varlist = []
        for varid in funcdata[1:]:
            varlist.append(str(varid))
        namedvarlist = dict()
        for nid, val in zip(ctx.ID(), ctx.value()):
            namedvarlist[str(nid)] = self.visit(val)
        self.memory[funcid] = {'call':
                               {'varlist':
                                varlist,
                                'block':
                                ctx.stmt_block(),
                                'namedvarlist':
                                namedvarlist},
                               'type': 'function'}
        return self.memory[funcid]
    
    def visitClass_stmt(self, ctx: GopherParser.Class_stmtContext):
        cid = str(ctx.ID(0))
        extendeds = []
        if ctx.EID is not None:
            extendeds = ctx.EID()
        varbls = ctx.var()
        temp = self.memory
        self.memory = dict()
        for var in varbls:
            self.visit(var)
        temp[cid], temp[cid]["vars"] = 2*(self.memory,)
        self.memory = temp
    
    def visitImpl_stmt(self, ctx: GopherParser.Impl_stmtContext):
        cid = str(ctx.ID())
        varbls = ctx.def_func_stmt()
        temp = self.memory
        self.memory = dict()
        for var in varbls:
            self.visit(var)
        try:
            self.memory['call'] = self.memory['__init']['call']
        except KeyError:
            pass
        temp[cid].update(self.memory)
        self.memory = temp


class Gophisitor(GopherVisitor):

    memory = {'': 0}

    def visitErrorNode(self, *args):
        print(args)

    def visitProgram(self, ctx: GopherParser.ProgramContext):
        declvsr = DeclVisitor()
        declvsr.visit(ctx)
        self.memory.update(declvsr.memory)
        return self.visit(ctx.block())

    def visitIncl_stmt(self, ctx: GopherParser.Incl_stmtContext):
        path = ''
        if ctx.recID() != None:
            mid = None
            ids = ctx.recID().ID()
            path += str(ids[0])
            for pid in ids[1:]:
                mid = str(pid)
                path += '/' + mid
            path += '.gopr'
        else:
            mid = str(ctx.ID())
            path += mid + '.gopr'
        inclexer = GopherLexer(FileStream(path))
        inclstream = CommonTokenStream(inclexer)
        inclparser = GopherParser(inclstream)
        incltree = inclparser.program()
        inclgophisitor = Gophisitor()
        inclgophisitor.visit(incltree)
        self.memory[mid] = inclgophisitor.memory
        self.memory[mid]['type'] = 'module' + mid
    
    def visitLoad_stmt(self, ctx: GopherParser.Load_stmtContext):
        path = ''
        if ctx.recID() != None:
            mid = None
            ids = ctx.recID().ID()
            path += str(ids[0])
            for pid in ids[1:]:
                mid = str(pid)
                path += '.' + mid
            mod = load(path)
            #mod = load(path).__dict__
            #for pid in ids[1:]:
                #mod = mod[str(pid)].__dict__
            self.memory[mid] = {'val': mod, 'type': 'extmod'+mid}
        else:
            mid = str(ctx.ID())
            mod = load(mid)
            #mod = load(mid).__dict__
            self.memory[mid] = {'val': mod, 'type': 'extmod'+mid}
            
    def visitVar(self, ctx: GopherParser.VarContext):
        id = str(ctx.ID())
        value = self.visit(ctx.expr())
        dt = ''
        if ctx.DT() != None:
            dt = str(ctx.DT())
        else:
            try:
                dt = self.memory[id]['type']
            except:
                dt = 'any'
        if (value['type'] != dt) and (dt != 'any'):
            value = {'val': ftype[dt](value['val']), 'type': dt}
        try:
            isconst = self.memory[id]['const']
            if isconst:
                raise Exception('can\'t assign value to const')
            else:
                self.memory[id] = value
                return value
        except:
            self.memory[id] = value
            if ctx.VAR() != None:
                self.memory[id]['const'] = True
            return value

    def visitRecID(self, ctx: GopherParser.RecIDContext):
        ids = ctx.ID()
        val = self.memory[str(ids[0])]
        for vid in ids[1:]:
            self.memory['this'] = val
            val = val[str(vid)]
        return val
    
    def visitIdAtom(self, ctx: GopherParser.IdAtomContext):
        if ctx.recID() != None:
            return self.visit(ctx.recID())
        else:
            id = str(ctx.ID())
            return self.memory[id]
    
    def visitStringAtom(self, ctx: GopherParser.StringAtomContext):
        outstr = str(ctx.STRING())
        return {'val': outstr[1:len(outstr)-1].format(n="\n", r="\r", t="\t"), 'type': 'str'}
    
    def visitNumberAtom(self, ctx: GopherParser.NumberAtomContext):
        outflt = float(str(ctx.DECIMAL()))
        return {'val': outflt, 'type': 'float'}
    
    def visitBoolAtom(self, ctx: GopherParser.BoolAtomContext):
        bltxt = str(ctx.BOOL())
        if bltxt == "false":
            return {'val': False, 'type': 'bool'}
        else: 
            return {'val': True, 'type': 'bool'}
    
    def visitNullAtom(self, ctx: GopherParser.NullAtomContext):
        return {'val': None, 'type': 'null'}
    
    def visitParExpr(self, ctx: GopherParser.ParExprContext):
        return self.visit(ctx.expr())

    def visitPowExpr(self, ctx: GopherParser.PowExprContext):
        left = self.visit(ctx.expr(0))['val']
        right = self.visit(ctx.expr(1))['val']
        return {'val': left**right, 'type': 'float'}

    def visitUminusExpr(self, ctx: GopherParser.UminusExprContext):
        val = self.visit(ctx.expr())['val']
        if isinstance(val, str):
            val = list(val)
            val.reverse()
            return {'val': ''.join(val), 'type': 'str'}
        elif isinstance(val, bool):
            return {'val': not val, 'type': 'bool'}
        else:
            return {'val': -val, 'type': 'float'}
    
    def visitUnotExpr(self, ctx: GopherParser.UnotExprContext):
        return {'val': not (self.visit(ctx.expr()))['val'], 'type': 'bool'}
    
    def visitMultExpr(self, ctx: GopherParser.MultExprContext):
        left = self.visit(ctx.expr(0))['val']
        right = self.visit(ctx.expr(1))['val']
        op = ctx.op.type
        if op == GopherParser.MULT:
            if isinstance(left, (str, list)):
                return {'val': int(right) * left,
                        'type': ('str' if type(left) == str else 'list')}
            elif isinstance(right, (str, list)):
                return {'val': int(left) * right,
                        'type': ('str' if type(right) == str else 'list')}
            else:
                return {'val':  left * right, 'type': 'float'}
        elif op == GopherParser.DIV:
            return {'val':  left / right, 'type': 'float'}
        elif op == GopherParser.MOD:
            return {'val':  left / right, 'type': 'float'}
        else:
            raise SyntaxError(op.getText()+"is not an operator")
 
    def visitAddExpr(self, ctx: GopherParser.AddExprContext):
        left = self.visit(ctx.expr(0))['val']
        right = self.visit(ctx.expr(1))['val']
        op = ctx.op.type
        if op == GopherParser.PLUS:
            if isinstance(left, (str)) or isinstance(right, str):
                return {'val': str(left) + str(right), 'type': 'str'}
            else:
                return {'val': left + right,
                        'type':
                        ('float' if type(left + right) != list else 'list')}
        elif op == GopherParser.MINUS:
            return {'val': float(left)-float(right), 'type': 'float'}
        else:
            raise SyntaxError(op.getText()+"is not a valid operator")
    
    def visitRelatExpr(self, ctx: GopherParser.RelatExprContext):
        left = self.visit(ctx.expr(0))['val']
        right = self.visit(ctx.expr(1))['val']
        op = ctx.op.type
        if (isinstance(left, list) and isinstance(right, list)):
            left, right = left[0]['val'], right[0]['val']
        if op == GopherParser.LT:
            return {'val': left < right, 'type': 'bool'}
        elif op == GopherParser.LTEQ:
            return {'val': left <= right, 'type': 'bool'}
        elif op == GopherParser.GT:
            return {'val': left > right, 'type': 'bool'}
        elif op == GopherParser.GTEQ:
            return {'val': left >= right, 'type': 'bool'}
        else:
            raise SyntaxError(op.getText()+"is not a valid operator")
    
    def visitEqExpr(self, ctx: GopherParser.EqExprContext):
        left = self.visit(ctx.expr(0))['val']
        right = self.visit(ctx.expr(1))['val']
        op = ctx.op.type
        if op == GopherParser.EQ:
            return {'val': left == right, 'type': 'bool'}
        elif op == GopherParser.NEQ:
            return {'val': left != right, 'type': 'bool'}
        else:
            raise SyntaxError(str(op)+"is not a valid operator")
    
    def visitAndExpr(self, ctx: GopherParser.AddExprContext):
        left = self.visit(ctx.expr(0))['val']
        right = self.visit(ctx.expr(1))['val']
        return {'val': left & right}
    
    def visitOrExpr(self, ctx: GopherParser.OrExprContext):
        left = self.visit(ctx.expr(0))['val']
        right = self.visit(ctx.expr(1))['val']
        return {'val': left | right}
    
    def visitPrint0(self, ctx: GopherParser.Print0Context):
        print(self.visit(ctx.expr())['val'], end='')
        return None
    
    def visitPrintln(self, ctx: GopherParser.PrintlnContext):
        print(self.visit(ctx.expr())['val'], end='\n\r')
        return None
    
    def visitValueExpr(self, ctx: GopherParser.ValueExprContext):
        return self.visit(ctx.value())

    def visitKey(self, ctx: GopherParser.KeyContext):
        input()
        return None
    
    def visitInputExpr(self, ctx: GopherParser.InputExprContext):
        return {'val': input(self.visit(ctx.expr())['val']), 'type': 'str'}
    
    def visitIf_stmt(self, ctx: GopherParser.If_stmtContext):
        conditions = ctx.condition_block()
        evalt = False
        retval = "ji"
        for condition in conditions:
            if self.visit(condition.expr())['val']:
                evalt = True
                retval = self.visit(condition.stmt_block())
                if isinstance(retval, tuple):
                    return retval
                break
        if (not evalt) and (ctx.stmt_block() != None):
            retval = self.visit(ctx.stmt_block())
            if isinstance(retval, tuple):
                return retval
        return retval
    
    def visitWhile_stmt(self, ctx: GopherParser.While_stmtContext):
        retval = "ji"
        val = self.visit(ctx.expr())['val']
        while val:
            retval = self.visit(ctx.stmt_block())
            if isinstance(retval, tuple):
                return retval
            val = self.visit(ctx.expr())['val']
        return retval
    
    def visitUntil_stmt(self, ctx: GopherParser.Until_stmtContext):
        retval = "ji"
        val = self.visit(ctx.expr())['val']
        while not val:
            retval = self.visit(ctx.stmt_block())
            if isinstance(retval, tuple):
                return retval
            val = self.visit(ctx.expr())['val']
        return retval
    
    def visitListAtom(self, ctx: GopherParser.ListAtomContext):
        lis = ctx.list_var().expr()
        ret = []
        for expr in lis:
            ret.append(self.visit(expr))
        return {'val': ret, 'type': 'list'}

    def visitListspaceAtom(self, ctx: GopherParser.ListspaceAtomContext):
        exprlis = ctx.linspace().expr()
        val = list(np.linspace(
                                self.visit(exprlis[1])['val'],
                                self.visit(exprlis[2])['val'],
                                self.visit(exprlis[0])['val']))
        return {'val': val, 'type': 'list'}

    def visitFor_stmt(self, ctx: GopherParser.For_stmtContext):
        retval = "ji"
        var = str(ctx.ID())
        lis = self.visit(ctx.expr())
        for val in lis['val']:
            self.memory[var] = val
            retval = self.visit(ctx.stmt_block())
            if isinstance(retval, tuple):
                return retval
        return retval
    
    def visitTern_opExpr(self, ctx: GopherParser.Tern_opExprContext):
        if self.visit(ctx.condexpr):
            return self.visit(ctx.truexpr)
        else:
            return self.visit(ctx.falsexpr)
    
    def visitLabel_def(self, ctx: GopherParser.Label_defContext):
        lblid = str(ctx.ID())
        self.memory[lblid] = ctx.stmt_block()

    def visitGoto_stmt(self, ctx: GopherParser.Goto_stmtContext):
        lblid = str(ctx.ID())
        val = self.visit(self.memory[lblid])
        if isinstance(val, tuple):
            return val
        return val
    
    def visitDef_func_stmt(self, ctx: GopherParser.Def_func_stmtContext):
        funcdata = ctx.ID()
        funcid = str(funcdata[0])
        varlist = []
        for varid in funcdata[1:]:
            varlist.append(str(varid))
        namedvarlist = dict()
        for nid, val in zip(ctx.ID(), ctx.value()):
            namedvarlist[str(nid)] = self.visit(val)
        self.memory[funcid] = {'call':
                               {'varlist':
                                varlist,
                                'block':
                                ctx.stmt_block(),
                                'namedvarlist':
                                namedvarlist},
                               'type': 'function'}
        return self.memory[funcid]
    
    def visitDef_func_expr(self, ctx: GopherParser.Def_func_exprContext):
        funcdata = ctx.ID()
        varlist = []
        for varid in funcdata:
            varlist.append(str(varid))
        namedvarlist = dict()
        for nid, val in zip(ctx.ID(), ctx.value()):
            namedvarlist[str(nid)] = self.visit(val)
        return {'call':
                {'varlist':
                 varlist,
                 'block':
                 ctx.stmt_block(),
                 'namedvarlist':
                 namedvarlist},
                'type': 'function'}
    
    def visitFileouts(self, ctx: GopherParser.FileoutsContext):
        exprlis = ctx.expr()
        val = self.visit(exprlis[0])['val']
        filename = self.visit(exprlis[1])
        mode = self.visit(exprlis[2])['val']
        if mode in ('w', 'a', 'x'):
            fil = open(filename['val'], mode)
            fil.write(str(val))
        else:
            print(f"{mode} is an invalid write mode")
        return filename
    
    def visitId_call(self, ctx: GopherParser.Id_callContext):
        if ctx.recID() != None:
            data = self.visit(ctx.recID())['call']
        else:
            data = self.memory[str(ctx.ID())]['call']
        poplist = data['varlist']+list(data['namedvarlist'].keys())
        exprlis = []
        for expr in ctx.expr():
            exprlis.append(self.visit(expr))
        if (len(data['varlist']) + len(data['namedvarlist'])) < len(exprlis):
            raise TypeError
        self.memory.update(dict(zip(data['varlist'] +
                                    list(data['namedvarlist'].keys())[
                                        :len(exprlis)-len(data['varlist'])
                                        ],
                                    exprlis +
                                    list(data['namedvarlist'].values())[
                                        len(exprlis) - len(data['varlist']):
                                    ])))
        retval = self.visit(data['block'])
        for vid in poplist[:len(poplist)-1]:
            self.memory.pop(vid)
        try:
            self.memory.pop('this')
        except KeyError:
            pass
        if isinstance(retval, tuple):
            return retval[0]
        else:
            return retval
    
    def visitId_callExpr(self, ctx: GopherParser.Id_callExprContext):
        return self.visit(ctx.id_call())
    
    def visitStmt_block(self, ctx: GopherParser.Stmt_blockContext):
        return self.visit(ctx.block())

    def visitExt_call(self, ctx: GopherParser.Ext_callContext):
        func = ''
        if ctx.recID() is not None:
            ids = ctx.recID().ID()
            func = self.memory[str(ids[0])]['val']
            for vid in ids[1:]:
                func = func.__dict__[str(vid)]
        else:
            func = self.visit(ctx.ID())
        evalstr = 'func('
        exprlis = ctx.expr()
        if len(exprlis):
            evalstr += str(self.visit(exprlis[0])['val'])
            for expr in exprlis[1:]:
                evalstr += ',' + str(self.visit(expr)['val'])
        val = eval(evalstr + ')')
        return {'val': val, 'type': 'any'}
        
    def visitBlock(self, ctx: GopherParser.BlockContext):
        retval = "ji"
        for stmt in ctx.stmt():
            if stmt.return_stmt() != None:
                return (self.visit(stmt.return_stmt().expr()),)
            else:
                retval = self.visit(stmt)
                if isinstance(retval, tuple):
                    return retval
        return retval

    def visitDecl(self, ctx: GopherParser.DeclContext):
        vid = self.visit(ctx.recID())
        val = self.visit(ctx.expr())
        if val['const']:
            raise TypeError('can\'t assign to const')
        vid['val'] = val['val']
        vid['type'] = val['type']
        return val

    def visitClass_stmt(self, ctx: GopherParser.Class_stmtContext):
        cid = str(ctx.ID(0))
        extendeds = []
        if ctx.EID is not None:
            extendeds = ctx.EID()
        varbls = ctx.var()
        temp = self.memory
        self.memory = dict()
        for var in varbls:
            self.visit(var)
        temp[cid].update(self.memory)
        temp[cid]["vars"] = self.memory
        self.memory = temp
    
    def visitImpl_stmt(self, ctx: GopherParser.Impl_stmtContext):
        cid = str(ctx.ID())
        varbls = ctx.def_func_stmt()
        temp = self.memory
        self.memory = dict()
        for var in varbls:
            self.visit(var)
        try:
            self.memory['call'] = self.memory['__init']['call']
        except KeyError:
            pass
        temp[cid].update(self.memory)
        self.memory = temp
    
    def visitClass_inst(self, ctx: GopherParser.Class_instContext):
        exprlis = []
        if ctx.recID() is not None:
            dat = self.visit(ctx.recID())
        else:
            dat = self.memory[str(ctx.ID())]
        vardat = dict(dat)
        vardat.pop("vars")
        for expr in ctx.expr():
            exprlis.append(self.visit(expr))
        for k, v in zip(dat['vars'], exprlis):
            if (dat['vars'][k]['type'] == v['type']) or (dat['vars'][k]['type'] == 'any'):
                vardat[k] = v
            else:
                vardat[k] = {
                            'val': ftype[dat['vars'][k]['type']](v['val']),
                            'type': dat['vars'][k]['type']
                }
        vardat["val"] = "object@"+str(tid(vardat))
        vardat["type"] = "inst"
        return vardat
    
    def visitExpnumberAtom(self, ctx: GopherParser.ExpnumberAtomContext):
        num = str(ctx.EXPDECIMAL())
        return {'val': float(num), 'type': 'float'}

    def visitMa
