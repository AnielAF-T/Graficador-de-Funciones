"""Graficador universal de funciones

by: Aniel AF"""

import re
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np
import pandas as pd
from sympy import (Symbol, lambdify, sin, cos, tan, asin, acos, atan,
                   sinh, cosh, tanh, exp, sqrt, log, Abs, pi, E)
from sympy.parsing.sympy_parser import parse_expr, standard_transformations
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.widgets import Cursor
from matplotlib.ticker import FuncFormatter, AutoMinorLocator
import matplotlib.pyplot as plt

# El programa intenta aplicar un estilo visual moderno a todas las
# figuras de Matplotlib; si el estilo preferido no existe en el
# entorno, se recurre a una alternativa equivalente.
try:
    plt.style.use("seaborn-v0_8-darkgrid")
except Exception:
    plt.style.use("ggplot")


# El diccionario reúne únicamente los nombres que deben interpretarse
# como funciones matemáticas o constantes conocidas. Cualquier otro
# identificador que aparezca en una expresión se trata como variable.
PERMITIDOS = {
    'sin': sin, 'cos': cos, 'tan': tan,
    'asin': asin, 'acos': acos, 'atan': atan,
    'sinh': sinh, 'cosh': cosh, 'tanh': tanh,
    'exp': exp, 'sqrt': sqrt, 'log': log, 'ln': log,
    'abs': Abs, 'pi': pi, 'E': E,
}


def construir_local(texto):
    """La función arma el diccionario de símbolos locales que sympy
    utilizará para interpretar una expresión. Todo nombre detectado
    que no pertenezca a PERMITIDOS se registra como un Symbol nuevo."""
    nombres = set(re.findall(r'[A-Za-z_][A-Za-z0-9_]*', texto))
    local = dict(PERMITIDOS)
    for n in nombres:
        if n not in PERMITIDOS:
            local[n] = Symbol(n)
    return local


def parsear(texto):
    """La función traduce una cadena de texto a una expresión simbólica
    de sympy, apoyándose en el diccionario construido dinámicamente."""
    return parse_expr(texto, local_dict=construir_local(texto),
                      transformations=standard_transformations)


def limpiar_expresion(texto):
    """La función elimina la parte "nombre(args) =" o "nombre =" que el
    usuario pudiera anteponer, dejando solo la expresión matemática."""
    texto = texto.strip()
    if "=" in texto:
        texto = texto.split("=", 1)[1].strip()
    return texto


def separar_funciones(texto):
    """La función separa varias expresiones escritas en una sola línea,
    respetando los paréntesis para no cortar comas internas de una
    función. Por ejemplo, 'f(a,b), g(c)' se convierte en ['f(a,b)', 'g(c)']."""
    partes = []
    actual = ""
    nivel = 0
    for ch in texto:
        if ch in "([{":
            nivel += 1
        elif ch in ")]}":
            nivel -= 1
        if ch == "," and nivel == 0:
            partes.append(actual)
            actual = ""
        else:
            actual += ch
    partes.append(actual)
    return [limpiar_expresion(p) for p in partes if p.strip()]


def _formato_origen(valor, _pos):
    """La función formatea las etiquetas del eje Y, ocultando el cero
    para evitar que se superponga con el cero del eje X, y presentando
    los números enteros sin decimales innecesarios."""
    if abs(valor) < 1e-9:
        return ""
    if float(valor).is_integer():
        return f"{int(valor)}"
    return f"{valor:g}"


def formatear_numero(valor, decimales=2):
    """La función redondea un valor numérico a un máximo de dos
    decimales y elimina los ceros sobrantes al final, de modo que un
    número entero se muestre sin punto decimal y uno fraccionario
    nunca exceda la cantidad de decimales indicada."""
    texto = f"{valor:.{decimales}f}"
    if "." in texto:
        texto = texto.rstrip("0").rstrip(".")
    return texto if texto not in ("", "-0") else "0"


class GraficadorUniversal:
    """La clase encapsula toda la interfaz gráfica y la lógica de
    trazado del programa, incluyendo el manejo de funciones, variables,
    etiquetas interactivas, zoom estilo MATLAB y exportación de datos."""

    def __init__(self, ventana):
        self.ventana = ventana
        self.ventana.title("Graficador Universal by: Aniel AF")

        # La ventana intenta abrirse maximizada; si el sistema operativo
        # no soporta el método correspondiente, se aplica una alternativa.
        try:
            self.ventana.state("zoomed")
        except Exception:
            try:
                self.ventana.attributes("-zoomed", True)
            except Exception:
                self.ventana.geometry("1400x800")
        self.ventana.geometry("1400x800")

        self.entradas_variables = {}
        self.datos_graficados = {}
        self.variables_detectadas = []
        self.texto_info = ""

        # La lista guarda cada etiqueta colocada sobre la gráfica como
        # un diccionario con el punto, la anotación y sus coordenadas.
        self.etiquetas = []

        # La referencia permite borrar el texto de estadísticas anterior
        # antes de dibujar uno nuevo, evitando que se acumulen textos.
        self.texto_stats = None

        self.crear_interfaz()

    def crear_interfaz(self):

        # El panel izquierdo agrupa todos los controles dentro de un
        # área con desplazamiento vertical, para que quepan aunque la
        # ventana se reduzca de tamaño.
        contenedor_izq = ttk.Frame(self.ventana)
        contenedor_izq.pack(side="left", fill="y", padx=5, pady=5)

        canvas_scroll = tk.Canvas(contenedor_izq, width=260, highlightthickness=0)
        scrollbar = ttk.Scrollbar(contenedor_izq, orient="vertical",
                                  command=canvas_scroll.yview)
        canvas_scroll.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas_scroll.pack(side="left", fill="both", expand=True)

        panel = ttk.Frame(canvas_scroll)
        ventana_interna = canvas_scroll.create_window((0, 0), window=panel, anchor="nw")

        def ajustar_scroll(event):
            canvas_scroll.configure(scrollregion=canvas_scroll.bbox("all"))
        panel.bind("<Configure>", ajustar_scroll)

        def ajustar_ancho(event):
            canvas_scroll.itemconfig(ventana_interna, width=event.width)
        canvas_scroll.bind("<Configure>", ajustar_ancho)

        # El desplazamiento con la rueda del mouse se limita al panel
        # izquierdo, para no interferir con el zoom de la gráfica.
        def rueda(event):
            canvas_scroll.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def rueda_linux(event):
            canvas_scroll.yview_scroll(-1 if event.num == 4 else 1, "units")

        canvas_scroll.bind("<MouseWheel>", rueda)
        canvas_scroll.bind("<Button-4>", rueda_linux)
        canvas_scroll.bind("<Button-5>", rueda_linux)

        ttk.Label(panel, text="Funciones").pack()

        self.lista = tk.Listbox(panel, selectmode=tk.MULTIPLE, width=36, height=10)
        self.lista.pack(fill="x")

        fila_funcs = ttk.Frame(panel)
        fila_funcs.pack(fill="x", pady=2)

        ttk.Button(fila_funcs, text="Agregar",
                   command=self.agregar_funcion).pack(side="left", expand=True,
                                                      fill="x", padx=1)
        ttk.Button(fila_funcs, text="Editar",
                   command=self.editar_funcion).pack(side="left", expand=True,
                                                     fill="x", padx=1)
        ttk.Button(fila_funcs, text="Eliminar",
                   command=self.eliminar_funcion).pack(side="left", expand=True,
                                                       fill="x", padx=1)

        ttk.Separator(panel).pack(fill="x", pady=5)

        ttk.Button(panel, text="Detectar variables",
                   command=self.detectar_variables).pack(fill="x", pady=2)

        self.marco_variables = ttk.LabelFrame(panel, text="Variables y parametros")
        self.marco_variables.pack(fill="both", expand=False)

        ttk.Separator(panel).pack(fill="x", pady=5)

        fila_rango = ttk.Frame(panel)
        fila_rango.pack(fill="x", pady=2)

        col_ini = ttk.Frame(fila_rango)
        col_ini.pack(side="left", expand=True, fill="x", padx=2)
        ttk.Label(col_ini, text="Inicio").pack()
        self.inicio = ttk.Entry(col_ini, width=8)
        self.inicio.insert(0, "0")
        self.inicio.pack(fill="x")

        col_fin = ttk.Frame(fila_rango)
        col_fin.pack(side="left", expand=True, fill="x", padx=2)
        ttk.Label(col_fin, text="Fin").pack()
        self.fin = ttk.Entry(col_fin, width=8)
        self.fin.insert(0, "10")
        self.fin.pack(fill="x")

        col_pts = ttk.Frame(fila_rango)
        col_pts.pack(side="left", expand=True, fill="x", padx=2)
        ttk.Label(col_pts, text="Puntos").pack()
        self.puntos = ttk.Entry(col_pts, width=8)
        self.puntos.insert(0, "2000")
        self.puntos.pack(fill="x")

        ttk.Button(panel, text="Graficar ",
                   command=self.graficar).pack(fill="x", pady=4)

        marco_export = ttk.LabelFrame(panel, text="Exportar")
        marco_export.pack(fill="x", pady=4)

        fila = ttk.Frame(marco_export)
        fila.pack(fill="x", padx=4, pady=4)

        ttk.Button(fila, text="Excel", width=10,
                   command=self.exportar_excel).pack(side="left", expand=True, padx=2)

        ttk.Button(fila, text="PNG", width=10,
                   command=self.guardar_png).pack(side="left", expand=True, padx=2)

        # El conjunto de casillas controla comportamientos opcionales:
        # visibilidad del cursor, activación de etiquetas por clic y
        # bloqueo de la proporción X:Y al hacer zoom.
        self.usar_cursor = tk.BooleanVar(value=True)
        ttk.Checkbutton(panel, text="Mostrar cursor",
                        variable=self.usar_cursor,
                        command=self.alternar_cursor).pack(anchor="w", pady=2)

        self.activar_etiquetas = tk.BooleanVar(value=False)
        ttk.Checkbutton(panel, text="Activar etiquetas al hacer clic",
                        variable=self.activar_etiquetas).pack(anchor="w", pady=2)

        self.figura, self.ejes = plt.subplots(figsize=(10, 5.5))

        contenedor = ttk.Frame(self.ventana)
        contenedor.pack(side="right", fill="both", expand=True)

        # El listado de etiquetas se ubica en la parte superior, con
        # espacio suficiente para mostrar hasta doce entradas repartidas
        # en cuatro columnas.
        marco_lista_etq = ttk.LabelFrame(contenedor, text="Etiquetas (X, Y)")
        marco_lista_etq.pack(side="top", fill="x", padx=4, pady=4)

        barra_frame = ttk.Frame(contenedor)
        barra_frame.pack(side="bottom", fill="x")

        self.canvas = FigureCanvasTkAgg(self.figura, master=contenedor)
        self.canvas.get_tk_widget().pack(side="top", fill="both", expand=True)

        NavigationToolbar2Tk(self.canvas, barra_frame)

        # Cada celda combina una etiqueta de texto con un botón "X" que
        # solo se hace visible cuando el mouse pasa por encima de ella.
        self.celdas_etiquetas = []
        for col in range(4):
            columna = ttk.Frame(marco_lista_etq)
            columna.pack(side="left", fill="both", expand=True, padx=6)
            for _ in range(3):
                fila = ttk.Frame(columna)
                fila.pack(fill="x")

                texto = ttk.Label(fila, text="", anchor="w",
                                  font=("Consolas", 9))
                texto.pack(side="left", fill="x", expand=True)

                equis = tk.Label(fila, text="", fg="red", cursor="hand2",
                                 font=("Consolas", 9, "bold"))
                equis.pack(side="right")

                celda = {"fila": fila, "texto": texto, "equis": equis}
                self.celdas_etiquetas.append(celda)

                def entrar(_e, c=celda):
                    self._hover_celda(c, True)
                def salir(_e, c=celda):
                    self._hover_celda(c, False)
                for w in (fila, texto, equis):
                    w.bind("<Enter>", entrar)
                    w.bind("<Leave>", salir)

                idx = len(self.celdas_etiquetas) - 1
                equis.bind("<Button-1>", lambda _e, i=idx: self.borrar_etiqueta(i))

        self.ejes.yaxis.set_major_formatter(FuncFormatter(_formato_origen))

        self.cursor = Cursor(self.ejes, useblit=True,
                             color="gray", linewidth=0.8)

        self.canvas.mpl_connect("scroll_event", self.zoom_rueda)
        self.canvas.mpl_connect("button_press_event", self.click_en_grafica)

    # ----------------------------------------------------------------
    #  Cursor
    # ----------------------------------------------------------------
    def alternar_cursor(self):
        """El método muestra u oculta el cursor de referencia según el
        estado actual de la casilla correspondiente."""
        self.cursor.visible = self.usar_cursor.get()
        self.canvas.draw_idle()

    # ----------------------------------------------------------------
    #  Zoom con la rueda del mouse
    # ----------------------------------------------------------------
    def zoom_rueda(self, event):
        """El método acerca o aleja la vista de la gráfica cuando el
        usuario gira la rueda del mouse. Mantiene fijo el punto que se
        encuentra bajo el cursor y aplica siempre el mismo factor de
        escala a los dos ejes, de modo que la relación entre el ancho y
        el alto de la vista nunca cambia y las curvas jamás se ven
        estiradas ni aplastadas al hacer zoom, tal como ocurre en
        MATLAB."""
        if event.inaxes != self.ejes:
            return

        factor = 1.2
        escala = 1 / factor if event.button == "up" else factor

        xmin, xmax = self.ejes.get_xlim()
        ymin, ymax = self.ejes.get_ylim()

        xdata, ydata = event.xdata, event.ydata
        if xdata is None or ydata is None:
            return

        nuevo_ancho = (xmax - xmin) * escala
        nuevo_alto = (ymax - ymin) * escala

        relx = (xdata - xmin) / (xmax - xmin)
        rely = (ydata - ymin) / (ymax - ymin)

        self.ejes.set_xlim(xdata - nuevo_ancho * relx,
                           xdata + nuevo_ancho * (1 - relx))
        self.ejes.set_ylim(ydata - nuevo_alto * rely,
                           ydata + nuevo_alto * (1 - rely))

        self.canvas.draw_idle()

    # ----------------------------------------------------------------
    #  Etiquetas interactivas
    # ----------------------------------------------------------------
    def click_en_grafica(self, event):
        """El método coloca una etiqueta numerada en el punto donde el
        usuario hace clic, pero únicamente cuando la casilla "Activar
        etiquetas al hacer clic" está marcada; de lo contrario el clic
        se ignora por completo."""
        if not self.activar_etiquetas.get():
            return
        if event.inaxes != self.ejes:
            return
        if event.button != 1:
            return
        if event.xdata is None or event.ydata is None:
            return

        if len(self.etiquetas) >= 12:
            messagebox.showinfo("Etiquetas",
                                "Maximo 12 etiquetas. Vuelva a graficar para limpiarlas.")
            return

        x, y = event.xdata, event.ydata
        numero = len(self.etiquetas) + 1

        punto = self.ejes.plot(x, y, "o", color="red", markersize=6)[0]
        anotacion = self.ejes.annotate(
            f"{numero}",
            xy=(x, y),
            xytext=(6, 6), textcoords="offset points",
            fontsize=9, color="black",
            bbox=dict(boxstyle="round,pad=0.2",
                      facecolor="yellow", edgecolor="gray", alpha=0.85)
        )

        self.etiquetas.append({
            "punto": punto,
            "anotacion": anotacion,
            "x": x,
            "y": y,
        })

        self.actualizar_listado_etiquetas()
        self.canvas.draw_idle()

    def _hover_celda(self, celda, dentro):
        """El método muestra el botón "X" únicamente cuando el mouse
        está sobre una celda que efectivamente contiene una etiqueta."""
        i = self.celdas_etiquetas.index(celda)
        tiene_contenido = i < len(self.etiquetas)
        celda["equis"].config(text="X" if (dentro and tiene_contenido) else "")

    def actualizar_listado_etiquetas(self):
        """El método vuelve a llenar las doce celdas del listado inferior
        en el mismo orden en que fueron creadas las etiquetas."""
        for i, celda in enumerate(self.celdas_etiquetas):
            if i < len(self.etiquetas):
                e = self.etiquetas[i]
                celda["texto"].config(
                    text=f"{i+1}: X={formatear_numero(e['x'])}  Y={formatear_numero(e['y'])}")
            else:
                celda["texto"].config(text="")
            celda["equis"].config(text="")

    def borrar_etiqueta(self, indice):
        """El método elimina una etiqueta específica y renumera las
        etiquetas restantes para mantener la secuencia consecutiva."""
        if indice >= len(self.etiquetas):
            return
        e = self.etiquetas.pop(indice)
        try:
            e["punto"].remove()
            e["anotacion"].remove()
        except Exception:
            pass

        for i, et in enumerate(self.etiquetas):
            et["anotacion"].set_text(str(i + 1))

        self.actualizar_listado_etiquetas()
        self.canvas.draw_idle()

    def borrar_todas_etiquetas(self):
        """El método retira todas las etiquetas presentes en la gráfica."""
        for e in self.etiquetas:
            try:
                e["punto"].remove()
                e["anotacion"].remove()
            except Exception:
                pass
        self.etiquetas.clear()
        self.actualizar_listado_etiquetas()
        self.canvas.draw_idle()

    # ----------------------------------------------------------------
    #  Manejo de funciones
    # ----------------------------------------------------------------
    def agregar_funcion(self):
        """El método solicita una o varias expresiones al usuario y las
        agrega a la lista únicamente si logran interpretarse con éxito."""
        texto = self._dialogo_funcion("Agregar funcion")
        if not texto:
            return

        for expresion in separar_funciones(texto):
            if not expresion:
                continue
            try:
                parsear(expresion)
                self.lista.insert(tk.END, expresion)
            except Exception as e:
                messagebox.showerror(
                    "Funcion invalida",
                    f"No se pudo interpretar:\n{expresion}\n\n{e}"
                )

    def editar_funcion(self):
        """El método permite modificar la expresión seleccionada usando
        el mismo cuadro de texto amplio que se emplea para agregar
        funciones nuevas, lo que facilita revisar expresiones largas."""
        seleccion = self.lista.curselection()
        if len(seleccion) != 1:
            messagebox.showwarning(
                "Aviso",
                "Seleccione exactamente una funcion para editar."
            )
            return

        indice = seleccion[0]
        actual = self.lista.get(indice)

        nuevo = self._dialogo_funcion("Editar funcion", texto_inicial=actual)
        if not nuevo:
            return

        nuevo = limpiar_expresion(nuevo)
        try:
            parsear(nuevo)
        except Exception as e:
            messagebox.showerror("Funcion invalida", str(e))
            return

        self.lista.delete(indice)
        self.lista.insert(indice, nuevo)
        self.lista.selection_set(indice)

    def _dialogo_funcion(self, titulo, texto_inicial=""):
        """El método construye un cuadro de diálogo amplio y reutilizable
        para escribir o modificar expresiones matemáticas. El área de
        texto es más grande que la de un cuadro de diálogo estándar,
        lo que permite ver por completo expresiones largas."""
        dialogo = tk.Toplevel(self.ventana)
        dialogo.title(titulo)
        ancho, alto = 560, 280
        self.ventana.update_idletasks()
        x = self.ventana.winfo_x() + (self.ventana.winfo_width()  - ancho) // 2
        y = self.ventana.winfo_y() + (self.ventana.winfo_height() - alto) // 2
        dialogo.geometry(f"{ancho}x{alto}+{x}+{y}")

        dialogo.transient(self.ventana)
        dialogo.grab_set()

        ttk.Label(dialogo,
                  text="Escriba solo la expresion (puede separar varias con comas):"
                  "\n Ejemplo: "
                  "\n       - x(t) = x*exp(zeta*wn*t)   --> X "
                  "\n       - x*exp(zeta*wn*t)    --> OK"
                  ).pack(anchor="w", padx=10, pady=(10, 4))

        caja = tk.Text(dialogo, height=8, font=("Consolas", 12), wrap="word")
        caja.pack(fill="both", expand=True, padx=10, pady=4)
        if texto_inicial:
            caja.insert("1.0", texto_inicial)
        caja.focus_set()

        resultado = {"texto": None}

        def aceptar():
            resultado["texto"] = caja.get("1.0", "end").strip()
            dialogo.destroy()

        def cancelar():
            resultado["texto"] = None
            dialogo.destroy()

        barra = ttk.Frame(dialogo)
        barra.pack(fill="x", padx=10, pady=8)
        ttk.Button(barra, text="Aceptar", command=aceptar).pack(side="right", padx=4)
        ttk.Button(barra, text="Cancelar", command=cancelar).pack(side="right")

        dialogo.bind("<Control-Return>", lambda e: aceptar())

        self.ventana.wait_window(dialogo)
        return resultado["texto"]

    def eliminar_funcion(self):
        """El método borra de la lista todas las funciones seleccionadas."""
        seleccion = list(self.lista.curselection())
        seleccion.reverse()
        for i in seleccion:
            self.lista.delete(i)

    # ----------------------------------------------------------------
    #  Variables
    # ----------------------------------------------------------------
    def detectar_variables(self):
        """El método recorre todas las funciones cargadas, identifica
        los símbolos que contienen y construye los campos de entrada
        correspondientes a cada parámetro detectado."""
        variables = set()

        for funcion in self.lista.get(0, tk.END):
            try:
                expr = parsear(funcion)
                for simbolo in expr.free_symbols:
                    variables.add(str(simbolo))
            except Exception:
                pass

        self.variables_detectadas = sorted(variables)

        if not self.variables_detectadas:
            for widget in self.marco_variables.winfo_children():
                widget.destroy()
            self.entradas_variables.clear()
            messagebox.showwarning(
                "Variables",
                "No se detectaron variables.\n\n"
                "Revise que escribio SOLO la expresion,\n"
                "sin 'x(t)=' al inicio."
            )
            return

        self.construir_caja_variables()

        messagebox.showinfo(
            "Variables",
            f"Detectadas: {', '.join(self.variables_detectadas)}"
        )

    def construir_caja_variables(self):
        """El método reconstruye el panel de variables, conservando los
        valores previamente ingresados por el usuario cuando es posible."""
        valores_previos = {}
        for nombre, entrada in self.entradas_variables.items():
            try:
                valores_previos[nombre] = entrada.get()
            except Exception:
                pass

        for widget in self.marco_variables.winfo_children():
            widget.destroy()
        self.entradas_variables.clear()

        ttk.Label(self.marco_variables,
                  text="Variable independiente:").pack(anchor="w")
        self.combo_x = ttk.Combobox(self.marco_variables, state="readonly",
                                    values=self.variables_detectadas)
        self.combo_x.current(0)
        self.combo_x.pack(fill="x", pady=(0, 6))
        self.combo_x.bind("<<ComboboxSelected>>",
                          lambda e: self.refrescar_parametros(valores_previos))

        ttk.Separator(self.marco_variables).pack(fill="x", pady=2)
        ttk.Label(self.marco_variables,
                  text="Valores de parametros:").pack(anchor="w")

        self.marco_parametros = ttk.Frame(self.marco_variables)
        self.marco_parametros.pack(fill="x")

        self.dibujar_parametros(valores_previos)

    def refrescar_parametros(self, valores_previos):
        """El método actualiza los campos de parámetros cuando el usuario
        cambia la variable independiente seleccionada."""
        for nombre, entrada in self.entradas_variables.items():
            try:
                valores_previos[nombre] = entrada.get()
            except Exception:
                pass
        self.dibujar_parametros(valores_previos)

    def dibujar_parametros(self, valores_previos):
        """El método crea un campo de entrada por cada variable detectada,
        exceptuando la que fue elegida como variable independiente."""
        for widget in self.marco_parametros.winfo_children():
            widget.destroy()
        self.entradas_variables.clear()

        independiente = self.combo_x.get()

        for variable in self.variables_detectadas:
            if variable == independiente:
                continue
            fila = ttk.Frame(self.marco_parametros)
            fila.pack(fill="x")
            ttk.Label(fila, text=variable, width=8).pack(side="left")
            entrada = ttk.Entry(fila)
            entrada.insert(0, valores_previos.get(variable, "1"))
            entrada.pack(side="left", fill="x", expand=True)
            self.entradas_variables[variable] = entrada

    def obtener_valores_variables(self):
        """El método recopila en un diccionario los valores numéricos
        que el usuario asignó a cada parámetro."""
        datos = {}
        for nombre, entrada in self.entradas_variables.items():
            datos[nombre] = float(entrada.get())
        return datos

    # ----------------------------------------------------------------
    #  Graficar
    # ----------------------------------------------------------------
    def graficar(self):
        """El método traza todas las funciones seleccionadas dentro del
        rango indicado, calcula sus estadísticas básicas y actualiza la
        gráfica junto con el panel de información inferior."""
        try:
            seleccionadas = self.lista.curselection()
            if not seleccionadas:
                messagebox.showwarning("Aviso", "Seleccione una o mas funciones")
                return

            if not hasattr(self, "combo_x"):
                messagebox.showwarning("Aviso", "Detecte variables primero")
                return

            variable_x = self.combo_x.get()
            if not variable_x:
                messagebox.showwarning("Aviso", "Seleccione la variable independiente")
                return

            inicio = float(self.inicio.get())
            fin = float(self.fin.get())
            puntos = int(self.puntos.get())

            x = np.linspace(inicio, fin, puntos)
            parametros = self.obtener_valores_variables()

            self.ejes.clear()
            # Al limpiar los ejes se eliminan también los puntos y las
            # anotaciones dibujados previamente, por lo que la lista de
            # etiquetas y su listado inferior se reinician en conjunto.
            self.etiquetas.clear()
            self.actualizar_listado_etiquetas()

            self.datos_graficados = {variable_x: x}
            lineas_info = []
            y_min_global = None
            y_max_global = None

            for indice in seleccionadas:
                expresion = self.lista.get(indice)
                expr = parsear(expresion)

                simbolos = sorted(expr.free_symbols, key=str)
                nombres = [str(s) for s in simbolos]

                funcion = lambdify(simbolos, expr, modules=["numpy"])

                argumentos = []
                for nombre in nombres:
                    if nombre == variable_x:
                        argumentos.append(x)
                    else:
                        argumentos.append(parametros[nombre])

                y = funcion(*argumentos)
                y = np.broadcast_to(np.asarray(y, dtype=float), x.shape)

                self.ejes.plot(x, y, label=expresion, linewidth=2)
                self.datos_graficados[expresion] = y

                try:
                    y_actual_min = float(np.nanmin(y))
                    y_actual_max = float(np.nanmax(y))
                    y_min_global = y_actual_min if y_min_global is None else min(y_min_global, y_actual_min)
                    y_max_global = y_actual_max if y_max_global is None else max(y_max_global, y_actual_max)
                except Exception:
                    pass

                try:
                    lineas_info.append(
                        f"{expresion}  |  Max={formatear_numero(np.nanmax(y))}  "
                        f"Min={formatear_numero(np.nanmin(y))}  "
                        f"RMS={formatear_numero(np.sqrt(np.nanmean(y**2)))}"
                    )
                except Exception:
                    pass

            # La proporción entre los ejes se fija en función del ancho
            # y el alto de la figura y del rango de datos trazado, de
            # modo que la forma de las curvas se conserve sin importar
            # qué herramienta use el usuario para hacer zoom o
            # desplazarse: la rueda del mouse, el recuadro de zoom de la
            # barra de herramientas o el modo de desplazamiento (pan).
            # Con "adjustable='datalim'", Matplotlib recalcula los
            # límites cada vez que cambian para respetar siempre esta
            # misma proporción, igual que "axis equal" en MATLAB.
            rango_x = fin - inicio
            if y_min_global is not None and y_max_global is not None:
                rango_y = y_max_global - y_min_global
            else:
                rango_y = 0
            if rango_x > 0 and rango_y > 0:
                ancho_fig, alto_fig = self.figura.get_size_inches()
                proporcion = (alto_fig / ancho_fig) * (rango_x / rango_y)
                self.ejes.set_aspect(proporcion, adjustable="datalim")
            else:
                self.ejes.set_aspect("auto")

            # La cuadrícula se dibuja en gris, combinando líneas
            # principales y secundarias, para que la gráfica se vea
            # dividida en recuadros como en el papel milimetrado.
            self.ejes.xaxis.set_minor_locator(AutoMinorLocator())
            self.ejes.yaxis.set_minor_locator(AutoMinorLocator())
            self.ejes.grid(True, which="major", color="gray",
                           linestyle="-", linewidth=0.6, alpha=0.6)
            self.ejes.grid(True, which="minor", color="gray",
                           linestyle="-", linewidth=0.3, alpha=0.3)
            self.ejes.legend(loc="best", fontsize=9)
            self.ejes.set_xlabel(variable_x)
            self.ejes.set_ylabel("Amp")
            self.ejes.set_title("Resultados")
            self.ejes.spines["top"].set_visible(False)
            self.ejes.spines["right"].set_visible(False)

            # El formateador del eje Y se pierde cada vez que se limpian
            # los ejes, por lo que se vuelve a asignar tras cada trazado.
            self.ejes.yaxis.set_major_formatter(FuncFormatter(_formato_origen))

            # El texto de estadísticas anterior se elimina antes de crear
            # uno nuevo, ya que figura.text() no se borra junto con los
            # ejes y de lo contrario se iría acumulando.
            if self.texto_stats is not None:
                try:
                    self.texto_stats.remove()
                except Exception:
                    pass
                self.texto_stats = None

            self.texto_info = "\n".join(lineas_info)
            if self.texto_info:
                self.figura.subplots_adjust(left=0.08, right=0.97, top=0.90, bottom=0.20)
                self.texto_stats = self.figura.text(
                    0.01, 0.01, self.texto_info,
                    fontsize=8, family="monospace",
                    verticalalignment="bottom")

            self.cursor = Cursor(self.ejes, useblit=True,
                                 color="gray", linewidth=0.8)
            self.cursor.visible = self.usar_cursor.get()

            self.canvas.draw()

        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ----------------------------------------------------------------
    #  Exportacion
    # ----------------------------------------------------------------
    def exportar_excel(self):
        """El método guarda los datos actualmente graficados en un
        archivo de Excel elegido por el usuario."""
        ruta = filedialog.asksaveasfilename(defaultextension=".xlsx")
        if not ruta:
            return

        if len(self.datos_graficados) > 1:
            df = pd.DataFrame(self.datos_graficados)
        else:
            df = pd.DataFrame({"Informacion": [self.texto_info]})

        df.to_excel(ruta, index=False)
        messagebox.showinfo("Correcto", "Archivo exportado")

    def guardar_png(self):
        """El método exporta la gráfica actual como una imagen PNG."""
        ruta = filedialog.asksaveasfilename(defaultextension=".png")
        if ruta:
            self.figura.savefig(ruta, dpi=300)
            messagebox.showinfo("Correcto", "Imagen guardada")


if __name__ == "__main__":
    raiz = tk.Tk()
    app = GraficadorUniversal(raiz)
    raiz.mainloop()