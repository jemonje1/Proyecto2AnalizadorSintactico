import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
from lector import Lector
from lexico import Lexico
from tabla import Tabla
from arbol import Arbol

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

class AnalyzerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Analizador Funciones Java - LL(1)")
        self.geometry("1200x750")
        self.minsize(1100, 700)
        self.lexico = Lexico()
        
        #Crea el sistema de tabs principal
        self.tabs = ctk.CTkTabview(self)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=10)
        self.tabs.add("Editor / Tokens")
        self.tabs.add("Árbol de Derivación")
        
        #Editor / Tokens
        tab1 = self.tabs.tab("Editor / Tokens")
        
        #Panel izquierdo: editor de código
        self.left = ctk.CTkFrame(tab1, width=350)
        self.left.pack(side="left", fill="y", padx=10, pady=10)
        self.center = ctk.CTkFrame(tab1)
        self.center.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(self.left, text="Código Java", font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", pady=(5,8))
        self.text_input = ctk.CTkTextbox(self.left, width=330, height=320, font=("Consolas", 11))
        self.text_input.pack(padx=5)
        
        #Botones principales de acción
        btns = ctk.CTkFrame(self.left)
        btns.pack(pady=10, fill="x")
        ctk.CTkButton(btns, text="📁 Cargar", command=self.load_file, width=100).pack(side="left", padx=4)
        ctk.CTkButton(btns, text="📝 Ejemplo", command=self.load_example, width=100).pack(side="left", padx=4)
        ctk.CTkButton(btns, text="▶ Analizar", fg_color="#1f6aa5", command=self.run, width=100).pack(side="left", padx=4)
        
        #Panel central: resultados del análisis
        ctk.CTkLabel(self.center, text="Tokens", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w")
        self.tokens_box = ctk.CTkTextbox(self.center, height=140, font=("Consolas", 10))
        self.tokens_box.pack(fill="x", pady=(4,10), padx=5)
        
        ctk.CTkLabel(self.center, text="Errores", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w")
        self.errors_box = ctk.CTkTextbox(self.center, height=110, font=("Consolas", 10))
        self.errors_box.pack(fill="x", pady=(4,10), padx=5)
        
        #Tabla LL(1) con scrollbars
        ctk.CTkLabel(self.center, text="Tabla LL(1)", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w")
        self.table_frame = ctk.CTkFrame(self.center)
        self.table_frame.pack(fill="both", expand=True, pady=(4,10), padx=5)
        
        self.table_xscroll = tk.Scrollbar(self.table_frame, orient="horizontal")
        self.table_yscroll = tk.Scrollbar(self.table_frame, orient="vertical")
        self.table_view = ttk.Treeview(
            self.table_frame,
            columns=[],
            show="headings",
            xscrollcommand=self.table_xscroll.set,
            yscrollcommand=self.table_yscroll.set,
            height=8
        )
        self.table_xscroll.config(command=self.table_view.xview)
        self.table_yscroll.config(command=self.table_view.yview)
        self.table_view.grid(row=0, column=0, sticky="nsew")
        self.table_yscroll.grid(row=0, column=1, sticky="ns")
        self.table_xscroll.grid(row=1, column=0, sticky="ew")
        self.table_frame.grid_rowconfigure(0, weight=1)
        self.table_frame.grid_columnconfigure(0, weight=1)
        
        #Estilo oscuro para la tabla
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except:
            pass
        style.configure("Treeview", background="#0b1220", fieldbackground="#0b1220", foreground="#e5e7eb", rowheight=26, bordercolor="#1f2937", borderwidth=0)
        style.configure("Treeview.Heading", background="#111827", foreground="#f3f4f6", relief="flat")
        style.map("Treeview.Heading", background=[("active", "#1f2937")])
        
        #Árbol de Derivación =====
        tab2 = self.tabs.tab("Árbol de Derivación")
        
        ctk.CTkLabel(tab2, text="Árbol de Derivación", font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", pady=(5,8))
        self.canvas_frame = ctk.CTkFrame(tab2)
        self.canvas_frame.pack(fill="both", expand=True, padx=8, pady=8)
        self.canvas = Arbol.crear_canvas_scroll(self.canvas_frame)
        
        #Controles de animación
        ctrls = ctk.CTkFrame(tab2)
        ctrls.pack(pady=6)
        ctk.CTkButton(ctrls, text="⏮", command=self.reset_anim, width=60).pack(side="left", padx=3)
        ctk.CTkButton(ctrls, text="⏭", command=self.next_step, width=60).pack(side="left", padx=3)
        ctk.CTkButton(ctrls, text="▶", command=self.play, width=60).pack(side="left", padx=3)
        ctk.CTkButton(ctrls, text="⏸", command=self.pause, width=60).pack(side="left", padx=3)
        
        #Botones de exportación
        ex = ctk.CTkFrame(tab2)
        ex.pack(pady=6, fill="x", padx=5)
        ctk.CTkButton(ex, text="💾 Exportar .DOT", command=self.export_dots).pack(fill="x", pady=2)
        ctk.CTkButton(ex, text="🖼️ Exportar PNG", command=self.export_png).pack(fill="x", pady=2)
        ctk.CTkButton(ex, text="💾 Exportar AST .DOT", command=self.export_ast).pack(fill="x", pady=2)
        ctk.CTkButton(ex, text="📤 Exportar tabla_transicion.txt", command=self.export_table).pack(fill="x", pady=2)
        
        #Estado interno de la animación
        self.steps = []
        self.current = 0
        self.animating = False
        self.last_analysis = {}
        self._last_table_dict = None

    def load_file(self):
        contenido = Lector.cargar_archivo()
        if contenido:
            self.text_input.delete("1.0", tk.END)
            self.text_input.insert(tk.END, contenido)

    def load_example(self):
        ex = Lector.obtener_ejemplo()
        self.text_input.delete("1.0", tk.END)
        self.text_input.insert(tk.END, ex)

    def run(self):
        #Ejecuta el análisis léxico y sintáctico completo
        code = self.text_input.get("1.0", tk.END)
        lex = self.lexico.lexer(code)
        
        #Muestra tokens encontrados
        self.tokens_box.delete("1.0", tk.END)
        self.errors_box.delete("1.0", tk.END)
        for t in lex["tokens"]:
            self.tokens_box.insert(tk.END, f'{t["lexeme"]} : {t["type"]} (L{t["line"]})\n')
        
        #Muestra errores léxicos
        for e in lex["errors"]:
            self.errors_box.insert(tk.END, f'Error: {e["msg"]} L{e["line"]} C{e["col"]}\n')
        
        #Calcula FIRST, FOLLOW y construye la tabla LL(1)
        FIRST = Lexico.compute_first()
        FOLLOW = Lexico.compute_follow(FIRST)
        table, conflicts = Tabla.build_table(FIRST, FOLLOW)
        
        #Ejecuta el parser
        parse_res = Lexico.parse(lex["tokens"], FIRST, FOLLOW, table)
        
        #Muestra errores sintácticos
        for e in parse_res["errors"]:
            self.errors_box.insert(tk.END, f'Parser: {e["msg"]} L{e["line"]}\n')
        
        #Guarda resultados para visualización
        self.last_analysis = parse_res
        self.steps = parse_res["steps"]
        self.current = 0
        used = parse_res.get("used_cells", [])
        self._last_table_dict = table
        
        #Renderiza la tabla marcando celdas usadas
        self.render_ll1_table(table, used_cells=used)
        
        #Reporta conflictos de la gramática
        if conflicts:
            self.errors_box.insert(tk.END, "Conflictos LL(1):\n")
            for c in conflicts:
                self.errors_box.insert(tk.END, f'No determinismo: {c}\n')
        
        self.draw_current()
        
        #Genera resumen estadístico
        summary = self.summarize_counts(lex["tokens"])
        self.tokens_box.insert(tk.END, "\n--- RESUMEN ---\n")
        self.tokens_box.insert(tk.END, f"Variables declaradas: {summary['vars']}\n")
        self.tokens_box.insert(tk.END, f"Métodos declarados: {summary['methods']}\n")
        self.tokens_box.insert(tk.END, f"Operadores: {summary['ops']}\n")
        self.tokens_box.insert(tk.END, f"Símbolos: {summary['symbols']}\n")
        self.tokens_box.insert(tk.END, f"Líneas procesadas: {lex['lines']}\n")
        
        #Exporta errores a archivo de texto
        errores_lines = []
        for e in lex["errors"]:
            errores_lines.append(f"[LEX] L{e['line']} C{e['col']}: {e['msg']}")
        for e in parse_res["errors"]:
            errores_lines.append(f"[SINTAX] L{e['line']} C{e['col']}: {e['msg']}")
        if errores_lines:
            try:
                with open("errores.txt", "w", encoding="utf-8") as f:
                    f.write("\n".join(errores_lines))
            except Exception as ex:
                self.errors_box.insert(tk.END, f"Error al escribir errores.txt: {ex}\n")

    def draw_current(self):
        #Dibuja el paso actual de la derivación
        if self.steps:
            Arbol.draw_snapshot(self.canvas, self.steps[self.current], self.current, len(self.steps))
        else:
            Arbol.draw_snapshot(self.canvas, None, 0, 0)

    def next_step(self):
        #Avanza al siguiente paso de la animación
        if not self.steps:
            return
        self.current = min(self.current+1, len(self.steps)-1)
        self.draw_current()

    def play(self):
        #Inicia la animación automática
        self.animating = True
        self.animate()

    def pause(self):
        self.animating = False

    def animate(self):
        #Loop de animación recursivo
        if self.animating and self.current < len(self.steps)-1:
            self.current += 1
            self.draw_current()
            self.after(800, self.animate)

    def reset_anim(self):
        #Regresa al inicio de la derivación
        self.current = 0
        self.draw_current()

    def export_dots(self):
        if not self.last_analysis.get("tree"):
            return
        dot = Arbol.tree_to_dot(self.last_analysis["tree"])
        Lector.guardar_archivo(dot, ".dot")

    def export_png(self):
        img = Arbol.render_to_image(self.canvas)
        if img is None:
            self.errors_box.insert(tk.END, "Export PNG: No fue posible generar la imagen.\n")
            return
        ok = Lector.guardar_imagen_pillow(img, ".png")
        if not ok:
            self.errors_box.insert(tk.END, "Export PNG: cancelado o error al guardar.\n")

    def export_ast(self):
        if not self.last_analysis.get("tree"):
            return
        dot = Arbol.export_ast_dot(self.last_analysis["tree"])
        ok = Lector.guardar_archivo(dot, ".dot")
        if not ok:
            self.errors_box.insert(tk.END, "Export AST: cancelado o error.\n")

    def export_table(self):
        #Exporta la tabla de parsing a archivo de texto
        if not self._last_table_dict:
            self.errors_box.insert(tk.END, "No hay tabla generada aún.\n")
            return
        csv_text = Tabla.to_csv_string(self._last_table_dict)
        ok = Lector.guardar_archivo(csv_text, ".txt")
        if not ok:
            self.errors_box.insert(tk.END, "Export tabla: cancelado o error.\n")

    def clear_table_widget(self):
        #Limpia el widget Treeview antes de renderizar nueva tabla
        for col in self.table_view["columns"]:
            self.table_view.heading(col, text="")
            self.table_view.column(col, width=0)
        self.table_view["columns"] = ()
        for item in self.table_view.get_children():
            self.table_view.delete(item)

    def render_ll1_table(self, table_dict, used_cells=None):
        #Renderiza la tabla LL(1) en el Treeview marcando celdas usadas
        headers, rows = Tabla.as_matrix(table_dict)
        used = set(used_cells or [])
        
        self.clear_table_widget()
        self.table_view["columns"] = headers
        
        #Configura columnas
        for h in headers:
            w = 160 if h == "No Terminal" else max(90, min(180, 12 * len(h)))
            self.table_view.heading(h, text=h)
            self.table_view.column(h, width=w, anchor="center", stretch=True)
        
        #Inserta filas y marca celdas usadas con "▶"
        terms = headers[1:]
        for idx, r in enumerate(rows):
            nt = r[0]
            new_row = [nt]
            for j, cell in enumerate(r[1:], start=1):
                t = terms[j-1]
                if cell and (nt, t) in used:
                    new_row.append("▶ " + cell)
                else:
                    new_row.append(cell)
            self.table_view.insert("", "end", values=new_row)

    def summarize_counts(self, tokens):
        #Cuenta variables, métodos, operadores y símbolos del código
        ops = {"+","-","*","/","<",">","=="}
        syms = {"{","}","(",")",",",";"}
        n_ops = sum(1 for t in tokens if t["type"] in ops)
        n_syms = sum(1 for t in tokens if t["type"] in syms)
        
        #Detecta declaraciones por el patrón: tipo + id + ";" o "("
        var_decl = 0
        meth_decl = 0
        for i in range(len(tokens)-2):
            a,b,c = tokens[i], tokens[i+1], tokens[i+2]
            if a["type"] in {"int","void"} and b["type"]=="id":
                if c["type"] == ";":
                    var_decl += 1
                elif c["type"] == "(":
                    meth_decl += 1
        
        return {"vars": var_decl, "methods": meth_decl, "ops": n_ops, "symbols": n_syms}