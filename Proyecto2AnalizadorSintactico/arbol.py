import tkinter as tk
from lexico import Lexico
from io import BytesIO
try:
    from PIL import Image, ImageGrab
    PIL_OK = True
except Exception:
    PIL_OK = False


class Arbol:
    @staticmethod
    def width_of(node):
        # Calcula el ancho total del árbol sumando el ancho de todos los hijos
        if not node.get("children"):
            return 1
        return sum(Arbol.width_of(c) for c in node.get("children", []))

    @staticmethod
    def layout_tree(root, x0, x1, y0=20, y_step=60):
        # Calcula las posiciones (x, y) de cada nodo para dibujar el árbol
        nodespos = {}
        def assign(n, left, right, depth):
            w = Arbol.width_of(n)
            if not n.get("children"):
                # Hoja: centrar en el espacio asignado
                x = (left + right) / 2
                nodespos[id(n)] = (n, x, y0 + depth * y_step)
            else:
                # Nodo interno: posicionar hijos primero
                cur = left
                for c in n.get("children", []):
                    cw = Arbol.width_of(c)
                    cleft = cur
                    cright = cur + cw
                    assign(c, cleft, cright, depth + 1)
                    cur += cw
                # Posicionar este nodo entre el primer y último hijo
                first = n["children"][0]
                last = n["children"][-1]
                x_first = nodespos[id(first)][1]
                x_last = nodespos[id(last)][1]
                nodespos[id(n)] = (n, (x_first + x_last) / 2, y0 + depth * y_step)
        total = Arbol.width_of(root)
        assign(root, 0, total, 0)
        return nodespos

    @staticmethod
    def tree_to_dot(tree, name="arbol"):
        # Genera código DOT de Graphviz para visualizar el árbol
        if not tree or not tree.get("sym"):
            return (
                f"digraph {name} {{\n"
                f"  node [shape=box];\n"
                f"  empty [label=\"Árbol vacío\"];\n"
                f"}}"
            )
        lines = [
            f"digraph {name} {{",
            '  node [shape=box, style=rounded, fontname="Consolas"];'
        ]
        node_counter = [0]
        def visit(n, parent_id=None):
            node_counter[0] += 1
            nid = f"n{node_counter[0]}"
            lab = n.get("sym", "?").replace('"', '\\"')
            # Colorea nodos según su tipo
            if lab == "ε":
                lines.append(f'  {nid} [label="{lab}", fillcolor="#f0f0f0", style=filled];')
            elif lab in Lexico.NONTERMINALS:
                lines.append(f'  {nid} [label="{lab}", fillcolor="#e3f2fd", style=filled];')
            else:
                lines.append(f'  {nid} [label="{lab}", fillcolor="#fff3e0", style=filled];')
            if parent_id:
                lines.append(f'  {parent_id} -> {nid};')
            for c in n.get("children", []):
                visit(c, nid)
            return nid
        visit(tree)
        lines.append("}")
        return "\n".join(lines)

    @staticmethod
    def crear_canvas_scroll(parent):
        # Crea un canvas con scroll y zoom para visualizar el árbol
        frame = tk.Frame(parent)
        frame.pack(fill="both", expand=True)
        x_scroll = tk.Scrollbar(frame, orient="horizontal")
        y_scroll = tk.Scrollbar(frame, orient="vertical")
        canvas = tk.Canvas(frame, bg="#0f172a", xscrollcommand=x_scroll.set, yscrollcommand=y_scroll.set)
        x_scroll.config(command=canvas.xview)
        y_scroll.config(command=canvas.yview)
        x_scroll.pack(side="bottom", fill="x")
        y_scroll.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        canvas.scale_factor = 1.0
        
        # Zoom con Ctrl + Scroll
        def zoom(event):
            if event.state & 0x0004:
                factor = 1.1 if event.delta > 0 else 0.9
                canvas.scale_factor *= factor
                canvas.scale("all", canvas.canvasx(event.x), canvas.canvasy(event.y), factor, factor)
                canvas.configure(scrollregion=canvas.bbox("all"))
        
        # Pan con clic medio o derecho
        def start_pan(event):
            canvas.scan_mark(event.x, event.y)
        def do_pan(event):
            canvas.scan_dragto(event.x, event.y, gain=1)
        
        # Manejo de scroll del mouse
        def on_wheel(event):
            if event.state & 0x0004:
                zoom(event)
                return
            if event.state & 0x0001:
                canvas.xview_scroll(-1 if event.delta > 0 else 1, "units")
            else:
                canvas.yview_scroll(-1 if event.delta > 0 else 1, "units")
        
        # Bind de eventos
        canvas.bind("<MouseWheel>", on_wheel)
        canvas.bind("<Button-4>",  lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind("<Button-5>",  lambda e: canvas.yview_scroll(1, "units"))
        canvas.bind("<ButtonPress-2>", start_pan)
        canvas.bind("<B2-Motion>", do_pan)
        canvas.bind("<ButtonPress-3>", start_pan)
        canvas.bind("<B3-Motion>", do_pan)
        return canvas

    @staticmethod
    def draw_snapshot(canvas, step, current, total_steps):
        # Dibuja un paso específico del árbol de derivación
        canvas.delete("all")
        if not step or not step.get("tree"):
            canvas.create_text(200, 150, text="Ejecuta 'Analizar' primero", fill="#888", font=("Arial", 13))
            return
        tree = step["tree"]
        canvas.update_idletasks()
        
        # Calcula posiciones y normaliza a píxeles
        nodespos = Arbol.layout_tree(tree, 0, 1, y0=30, y_step=70)
        if not nodespos:
            return
        xs = [p[1] for p in nodespos.values()]
        minx, maxx = min(xs), max(xs)
        margin_x = 60
        margin_y = 40
        y_step_extra = 0
        px_per_unit = 100
        norm = {}
        for k, (n, x, y) in nodespos.items():
            nx = margin_x + (x - minx) * px_per_unit
            ny = margin_y + y + y_step_extra
            norm[k] = (n, nx, ny)
        
        # Dibuja las líneas entre padres e hijos
        for _, (n, x, y) in norm.items():
            for c in n.get("children", []):
                for _, (cn, cx, cy) in norm.items():
                    if cn.get("id") == c.get("id"):
                        canvas.create_line(x, y + 16, cx, cy - 16, width=2, fill="#5599ff", smooth=True)
                        break
        
        # Dibuja los nodos como óvalos con texto
        for _, (n, x, y) in norm.items():
            lab = n.get("sym", "?")
            w = max(40, len(lab) * 10)
            h = 28
            fill = "#1e3a5f" if lab not in Lexico.NONTERMINALS else "#e3f2fd"
            outline = "#3b82f6" if lab not in Lexico.NONTERMINALS else "#1e40af"
            text_color = "#fff3e0" if lab not in Lexico.NONTERMINALS else "#000"
            canvas.create_oval(x - w / 2, y - h / 2, x + w / 2, y + h / 2, fill=fill, outline=outline, width=2)
            canvas.create_text(x, y, text=lab, font=("Consolas", 11, "bold"), fill=text_color)
        
        # Muestra información del paso actual
        ch = max(canvas.winfo_height(), 400)
        action = step.get("action", "")
        cap = f"Paso {current + 1}/{total_steps} | {action}"
        canvas.create_text(10, ch - 15, text=cap, anchor="w", fill="#94a3b8", font=("Arial", 10))
        bbox = canvas.bbox("all")
        if bbox:
            pad = 60
            canvas.configure(scrollregion=(bbox[0]-pad, bbox[1]-pad, bbox[2]+pad, bbox[3]+pad))

    @staticmethod
    def render_to_image(canvas):
        # Exporta el canvas actual como imagen PIL
        if not PIL_OK:
            return None
        bbox = canvas.bbox("all")
        if not bbox:
            return None
        x0, y0, x1, y1 = bbox
        width = int(x1 - x0)
        height = int(y1 - y0)
        if width <= 0 or height <= 0:
            return None
        try:
            # Intenta con postscript primero
            ps = canvas.postscript(colormode='color', x=x0, y=y0, width=width, height=height, pagewidth=width)
            bio = BytesIO(ps.encode("utf-8"))
            img = Image.open(bio)
            return img.convert("RGBA")
        except Exception:
            try:
                # Fallback: captura de pantalla
                rx = canvas.winfo_rootx()
                ry = canvas.winfo_rooty()
                rw = rx + canvas.winfo_width()
                rh = ry + canvas.winfo_height()
                img = ImageGrab.grab(bbox=(rx, ry, rw, rh))
                return img.convert("RGBA")
            except Exception:
                return None

    @staticmethod
    def derivation_to_ast(node):
        # Convierte el árbol de derivación completo a un AST simplificado
        if not node:
            return None
        sym = node.get("sym", "")
        childs = node.get("children", [])
        # Filtra nodos epsilon
        filt = [c for c in childs if c.get("sym") != "ε"]
        new_children = [Arbol.derivation_to_ast(c) for c in filt]
        new_children = [c for c in new_children if c]
        
        # Solo mantiene terminales y símbolos de interés
        terminal_interes = {"id", "number", "+", "-", "*", "/", "==", "<", ">", "=", "return", "class", "int", "void", "(", ")", "{", "}", ",", ";"}
        if sym in terminal_interes:
            return {"id": node.get("id"), "sym": sym, "children": new_children}
        
        # Simplifica nodos con un solo hijo
        if len(new_children) == 1:
            return new_children[0]
        if new_children:
            return {"id": node.get("id"), "sym": sym, "children": new_children}
        return None

    @staticmethod
    def export_ast_dot(derivation_root):
        # Genera código DOT del AST simplificado
        ast = Arbol.derivation_to_ast(derivation_root)
        if not ast:
            return "digraph ast { node [shape=box]; empty [label=\"AST vacío\"]; }"
        return Arbol.tree_to_dot(ast, name="ast")