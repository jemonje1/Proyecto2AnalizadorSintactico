import csv
import io
from lexico import Lexico

class Tabla:
    @staticmethod
    def build_table(FIRST, FOLLOW):
        #Construye la tabla de parsing LL(1)
        table = {A:{} for A in Lexico.NONTERMINALS}
        conflicts = []
        for A in Lexico.NONTERMINALS:
            for prod in Lexico.GRAMMAR[A]:
                #Calcula FIRST de la producción
                firstAlpha = Lexico.first_of_sequence(prod, FIRST)
                
                #Para cada terminal en FIRST, agrega la producción a la tabla
                for a in firstAlpha:
                    if a == Lexico.EPS:
                        continue
                    if a in table[A]:
                        #Detecta conflictos (múltiples producciones para la misma celda)
                        conflicts.append((A,a,table[A][a],prod))
                    else:
                        table[A][a] = prod
                
                #Si la producción es anulable, usa FOLLOW
                if Lexico.EPS in firstAlpha:
                    for b in FOLLOW[A]:
                        if b in table[A]:
                            conflicts.append((A,b,table[A][b],prod))
                        else:
                            table[A][b] = prod

        return table, conflicts

    @staticmethod
    def format_table(table):
        #Formatea la tabla como texto legible
        result = []
        for nt, row in table.items():
            result.append(f'{nt}: {row}\n')
        return ''.join(result)

    @staticmethod
    def terminals_for_table():
        return [t for t in Lexico.all_terminals()]

    @staticmethod
    def as_matrix(table):
        #Convierte la tabla a formato de matriz (filas y columnas)
        terms = Tabla.terminals_for_table()
        headers = ["No Terminal"] + terms
        rows = []
        
        for nt in Lexico.NONTERMINALS:
            row = [nt]
            for t in terms:
                prod = table.get(nt, {}).get(t, None)
                if prod:
                    #Convierte la producción a string
                    right = " ".join(prod) if prod != [Lexico.EPS] else "ε"
                    row.append(right)
                else:
                    row.append("")
            rows.append(row)
        
        return headers, rows

    @staticmethod
    def to_csv_string(table):
        #Exporta la tabla a formato CSV
        headers, rows = Tabla.as_matrix(table)
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(headers)
        writer.writerows(rows)
        return buf.getvalue()