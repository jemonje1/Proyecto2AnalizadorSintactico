import re
import json

class Lexico:
    EPS = "ε"
    # Gramática completa del lenguaje definida como producciones
    GRAMMAR = {
        "Prog": [["ClassDecl"]],
        "ClassDecl": [["class","id","{","MemberList","}"]],
        "MemberList": [["Member","MemberList"], [EPS]],
        "Member": [["Type","id","MemberP"]],
        "MemberP": [[";"], ["(","ParamList",")","Block"]],
        "ParamList": [["Param","ParamRest"], [EPS]],
        "ParamRest": [[",","Param","ParamRest"], [EPS]],
        "Param": [["Type","id"]],
        "Block": [["{","StmtList","}"]],
        "StmtList": [["Stmt","StmtList"], [EPS]],
        "Stmt": [["Type","id",";"], ["Return"], ["id","StmtP"]],
        "StmtP": [["=","Expr",";"], ["(","ArgList",")",";"]],
        "Return": [["return","ReturnP"]],
        "ReturnP": [["Expr",";"], [";"]],
        "ArgList": [["Expr","ArgRest"], [EPS]],
        "ArgRest": [[",","Expr","ArgRest"], [EPS]],
        "Expr": [["Rel"]],
        "Rel": [["Add","RelP"]],
        "RelP": [["==","Add","RelP"], ["<","Add","RelP"], [">","Add","RelP"], [EPS]],
        "Add": [["Term","AddP"]],
        "AddP": [["+","Term","AddP"], ["-","Term","AddP"], [EPS]],
        "Term": [["Factor","TermP"]],
        "TermP": [["*","Factor","TermP"], ["/","Factor","TermP"], [EPS]],
        "Factor": [["number"], ["(", "Expr", ")"], ["id", "FactorP"]],
        "FactorP": [["(","ArgList",")"], [EPS]],
        "Type": [["int"], ["void"]]
    }
    NONTERMINALS = list(GRAMMAR.keys())
    KEYWORDS = {"class","int","void","return"}

    def __init__(self):
        # Define las reglas regex para reconocer tokens en orden de prioridad
        self.token_spec = [
            ("COMMENT_BLOCK", r"/\*[\s\S]*?\*/"),
            ("COMMENT_LINE",  r"//[^\n]*"),
            ("NUMBER",   r"\b\d+\b"),
            ("ID",       r"\b[A-Za-z_][A-Za-z0-9_]*\b"),
            ("OP2",      r"=="),
            ("NEWLINE",  r"\n"),
            ("SKIP",     r"[ \t\r]+"),
            ("SYMBOL",   r"[{}(),;]"),
            ("OP1",      r"[+\-*/=<>]"),
            ("MISMATCH", r"."),
        ]
        # Combina todas las regex en un solo patrón maestro
        self.master_pat = re.compile("|".join("(?P<%s>%s)" % pair for pair in self.token_spec))

    @staticmethod
    def is_nonterminal(x):
        return x in Lexico.NONTERMINALS

    @staticmethod
    def all_terminals():
        # Extrae todos los terminales de la gramática
        terms = set()
        for A in Lexico.NONTERMINALS:
            for prod in Lexico.GRAMMAR[A]:
                for sym in prod:
                    if sym == Lexico.EPS:
                        continue
                    if not Lexico.is_nonterminal(sym):
                        terms.add(sym)
        terms.add("id")
        terms.add("number")
        terms.add("$")
        return sorted(list(terms))

    def lexer(self, text):
        tokens = []
        errors = []
        lineno = 1
        pos = 0
        length = len(text)

        # Itera sobre el texto buscando coincidencias con el patrón maestro
        while pos < length:
            m = self.master_pat.match(text, pos)
            if not m:
                break
            kind = m.lastgroup
            value = m.group()
            
            # Ignora comentarios de línea
            if kind == "COMMENT_LINE":
                pos = m.end()
                continue
            # Ignora comentarios de bloque y cuenta nuevas líneas
            elif kind == "COMMENT_BLOCK":
                lineno += value.count("\n")
                pos = m.end()
                continue

            # Crea tokens según el tipo reconocido
            if kind == "NUMBER":
                tokens.append({"type":"number","lexeme":value,"line":lineno,"col":pos - text.rfind("\n", 0, pos)})
            elif kind == "ID":
                # Distingue entre keywords e identificadores
                if value in self.KEYWORDS:
                    tokens.append({"type":value,"lexeme":value,"line":lineno,"col":pos - text.rfind("\n", 0, pos)})
                else:
                    tokens.append({"type":"id","lexeme":value,"line":lineno,"col":pos - text.rfind("\n", 0, pos)})
            elif kind == "OP2":
                tokens.append({"type":value,"lexeme":value,"line":lineno,"col":pos - text.rfind("\n", 0, pos)})
            elif kind == "OP1":
                tokens.append({"type":value,"lexeme":value,"line":lineno,"col":pos - text.rfind("\n", 0, pos)})
            elif kind == "SYMBOL":
                tokens.append({"type":value,"lexeme":value,"line":lineno,"col":pos - text.rfind("\n", 0, pos)})
            elif kind == "NEWLINE":
                lineno += 1
            elif kind == "SKIP":
                pass
            elif kind == "MISMATCH":
                # Manejo especial para comentarios sin cerrar
                if value == "/" and pos+1 < length and text[pos+1] == "*":
                    end = text.find("*/", pos+2)
                    if end == -1:
                        errors.append({"line":lineno,"col":pos - text.rfind("\n", 0, pos),"msg":"Comentario /* no cerrado"})
                        pos = length
                        break
                    block = text[pos:end+2]
                    lineno += block.count("\n")
                    pos = end + 2
                    continue
                errors.append({"line":lineno,"col":pos - text.rfind("\n", 0, pos),"msg":f"Caracter ilegal '{value}'"})

            pos = m.end()

        return {"tokens":tokens,"errors":errors,"lines": text.count("\n")+1}

    @staticmethod
    def compute_first():
        # Calcula el conjunto FIRST para cada no terminal usando punto fijo
        FIRST = {A:set() for A in Lexico.NONTERMINALS}
        changed = True
        while changed:
            changed = False
            for A in Lexico.NONTERMINALS:
                for prod in Lexico.GRAMMAR[A]:
                    # Si la producción es epsilon
                    if prod[0] == Lexico.EPS:
                        if Lexico.EPS not in FIRST[A]:
                            FIRST[A].add(Lexico.EPS); changed=True
                        continue
                    # Calcula FIRST considerando prefijos anulables
                    nullable_prefix = True
                    for X in prod:
                        if not Lexico.is_nonterminal(X):
                            if X not in FIRST[A]:
                                FIRST[A].add(X); changed=True
                            nullable_prefix = False
                            break
                        else:
                            for t in FIRST[X]:
                                if t != Lexico.EPS and t not in FIRST[A]:
                                    FIRST[A].add(t); changed=True
                            if Lexico.EPS not in FIRST[X]:
                                nullable_prefix = False
                                break
                    if nullable_prefix:
                        if Lexico.EPS not in FIRST[A]:
                            FIRST[A].add(Lexico.EPS); changed=True
        return FIRST

    @staticmethod
    def first_of_sequence(seq, FIRST):
        # Calcula FIRST de una secuencia de símbolos
        res = set()
        nullable_prefix = True
        for X in seq:
            if not Lexico.is_nonterminal(X):
                res.add(X); nullable_prefix = False; break
            else:
                for t in FIRST[X]:
                    if t != Lexico.EPS: res.add(t)
                if Lexico.EPS not in FIRST[X]:
                    nullable_prefix = False; break
        if nullable_prefix: res.add(Lexico.EPS)
        return res

    @staticmethod
    def compute_follow(FIRST):
        # Calcula el conjunto FOLLOW para cada no terminal
        FOLLOW = {A:set() for A in Lexico.NONTERMINALS}
        FOLLOW["Prog"].add("$")
        changed = True
        while changed:
            changed = False
            for A in Lexico.NONTERMINALS:
                for prod in Lexico.GRAMMAR[A]:
                    for i,B in enumerate(prod):
                        if not Lexico.is_nonterminal(B): continue
                        # FIRST del resto de la producción
                        beta = prod[i+1:]
                        FIRSTbeta = Lexico.first_of_sequence(beta,FIRST) if beta else {Lexico.EPS}
                        for t in FIRSTbeta:
                            if t!=Lexico.EPS and t not in FOLLOW[B]:
                                FOLLOW[B].add(t); changed=True
                        # Si beta es anulable, agregar FOLLOW(A) a FOLLOW(B)
                        if Lexico.EPS in FIRSTbeta or not beta:
                            for t in FOLLOW[A]:
                                if t not in FOLLOW[B]:
                                    FOLLOW[B].add(t); changed=True
        return FOLLOW

    @staticmethod
    def parse(tokens, FIRST, FOLLOW, table):
        # Parser predictivo usando tabla LL(1)
        errors = []
        derivation_steps = []
        used_cells = []
        stack = ["$","Prog"]
        root = {"id":"Prog_0","sym":"Prog","children":[],"expanded":False}
        node_stack = [{"sym":"$","node":None},{"sym":"Prog","node":root}]
        # Agrega token EOF al final
        stream = tokens.copy()
        stream.append({"type":"$","lexeme":"$","line": (tokens[-1]["line"] if tokens else 1),"col":1})
        ip = 0
        step_id = 0

        def snapshot(action, info=None):
            # Guarda cada paso del parsing para visualización
            nonlocal step_id
            step_id += 1
            derivation_steps.append({"action":action,"info":info,"tree":json.loads(json.dumps(root))})

        snapshot("start")
        while stack:
            X = stack[-1]
            a = stream[ip]["type"]
            cur = stream[ip]
            
            # Caso de aceptación
            if X == "$" and a == "$":
                snapshot("accept"); break
            
            # Si X es terminal, debe coincidir con el token actual
            if not Lexico.is_nonterminal(X):
                if X == a:
                    snapshot("match", {"token":cur})
                    stack.pop(); node_stack.pop()
                    ip += 1
                    continue
                else:
                    errors.append({"line":cur["line"],"col":cur["col"],"msg":f"Token '{cur['lexeme']}' no coincide con '{X}'"})
                    snapshot("insert", {"expected":X,"found":cur})
                    stack.pop(); node_stack.pop()
                    continue
            else:
                # Busca producción en la tabla para expandir el no terminal
                prod = table.get(X,{}).get(a,None)
                if prod:
                    used_cells.append((X, a))
                    popped = node_stack.pop()
                    node = popped["node"]
                    stack.pop()
                    node["expanded"] = True
                    # Crea nodos hijos para cada símbolo de la producción
                    children = []
                    for s in prod:
                        if s == Lexico.EPS:
                            children.append({"id":f"EPS_{step_id}","sym":"ε","children":[]})
                        elif Lexico.is_nonterminal(s):
                            children.append({"id":f"{s}_{step_id}","sym":s,"children":[]})
                        else:
                            children.append({"id":f"TK_{s}_{step_id}","sym":s,"children":[]})
                    node["children"] = children
                    snapshot("expand", {"nonterminal":X,"production":prod})
                    # Apila los símbolos de la producción en orden inverso
                    if not (len(prod)==1 and prod[0]==Lexico.EPS):
                        for i in range(len(prod)-1,-1,-1):
                            sym = prod[i]
                            stack.append(sym)
                            node_stack.append({"sym":sym,"node":children[i]})
                    continue
                else:
                    # No hay producción válida, reporta error y salta token
                    errors.append({"line":cur["line"],"col":cur["col"],"msg":f"No hay producción para [{X}] con '{cur['lexeme']}'"})
                    snapshot("skip", {"token":cur})
                    ip += 1
                    if ip >= len(stream): break
                    continue
        return {"errors":errors,"steps":derivation_steps,"tree":root, "used_cells": used_cells}