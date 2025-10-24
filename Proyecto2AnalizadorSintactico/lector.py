from tkinter import filedialog

class Lector:
    @staticmethod
    def cargar_archivo():
        #Abre el buscador para seleccionar un archivo de texto
        path = filedialog.askopenfilename(filetypes=[("Text files","*.txt"),("All files","*.*")])
        if path:
            # Lee el contenido completo del archivo
            with open(path,"r",encoding="utf-8") as f:
                return f.read()
        return None

    @staticmethod
    def guardar_archivo(contenido, extension=".txt"):
        #Muestra el buscador para elegir dónde guardar
        path = filedialog.asksaveasfilename(defaultextension=extension)
        if path:
            #Escribe el contenido en el archivo seleccionado
            with open(path,"w",encoding="utf-8") as f:
                f.write(contenido)
            return True
        return False

    @staticmethod
    def guardar_imagen_pillow(img, extension=".png"):
        #Específico para guardar imágenes PNG
        path = filedialog.asksaveasfilename(defaultextension=extension, filetypes=[("PNG image","*.png"), ("All files","*.*")])
        if not path:
            return False
        try:
            #Guarda la imagen usando PIL/Pillow
            img.save(path, "PNG")
            return True
        except Exception:
            return False

    @staticmethod
    def obtener_ejemplo():
        #Retorna un código de ejemplo por defecto para pruebas
        return """class Demo {
    int sum(int a, int b) { return a + b; }
}"""