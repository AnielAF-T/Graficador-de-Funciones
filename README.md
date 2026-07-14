# Graficador Universal AF

Aplicación de escritorio en Python para graficar y comparar múltiples funciones matemáticas de forma interactiva. Permite escribir expresiones simbólicas, detectar automáticamente sus variables, ajustar parámetros en tiempo real y explorar la gráfica.
![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Tkinter](https://img.shields.io/badge/GUI-Tkinter-informational)
![License](https://img.shields.io/badge/license-MIT-green)

## ✨ Características

- **Parser simbólico con SymPy**: escribe expresiones matemáticas como `sin(x)*exp(-t)` o `x(t) = A*cos(w*t + phi)`; el programa reconoce automáticamente qué nombres son funciones (`sin`, `cos`, `exp`, `sqrt`, `log`, etc.) y cuáles son variables.
- **Múltiples funciones a la vez**: agrega, edita y elimina expresiones desde una lista, y selecciona cuáles se grafican simultáneamente para compararlas.
- **Detección automática de variables**: identifica los símbolos usados en las funciones y genera campos de entrada para cada parámetro, conservando los valores ya ingresados al cambiar la variable independiente.
- **Zoom sin distorsión**: la proporción real entre los ejes X e Y queda fija automáticamente después de cada trazado. No importa qué herramienta se use para acercar, alejar o desplazar la vista —la rueda del mouse, el recuadro de zoom o el modo de desplazamiento (pan) de la barra de herramientas—: Matplotlib siempre corrige los límites para conservar la forma real de las curvas, igual que `axis equal` en MATLAB.
- **Etiquetas interactivas opcionales**: al marcar la casilla **"Activar etiquetas al hacer clic"**, cada clic sobre la gráfica coloca un punto numerado con sus coordenadas (X, Y); si la casilla está desmarcada, los clics no generan etiquetas. Hasta 12 etiquetas simultáneas, listadas debajo de la gráfica y eliminables individualmente.
- **Estadísticas automáticas**: máximo, mínimo y RMS de cada función graficada, mostrados al pie de la gráfica con un máximo de 2 decimales (sin ceros sobrantes).
- **Cuadrícula tipo papel milimetrado**: líneas de división principales y secundarias en gris, para ubicar valores con más precisión visual.
- **Exportación**:
  - A **Excel (.xlsx)** con los datos numéricos de cada curva.
  - A **PNG** en alta resolución (300 dpi).
- **Barra de herramientas de Matplotlib** integrada (pan, zoom por recuadro, guardar, etc.).

## 📦 Requisitos

- Python 3.9 o superior
- Bibliotecas:
  - `numpy`
  - `pandas`
  - `sympy`
  - `matplotlib`
  - `openpyxl` (usada internamente por `pandas` para exportar a `.xlsx`)
  - `tkinter` (incluida en la mayoría de las distribuciones de Python; en Linux puede requerir instalación aparte, por ejemplo `sudo apt install python3-tk`)

## 🚀 Instalación

```bash
git clone https://github.com/tu-usuario/graficador-universal.git
cd graficador-universal
pip install numpy pandas sympy matplotlib openpyxl
```

## ▶️ Uso

```bash
python graficador_universal.py
```

1. Haz clic en **Agregar** y escribe una o varias expresiones separadas por comas (por ejemplo `sin(x), cos(x)*exp(-x/5)`).
2. Presiona **Detectar variables** para que el programa identifique las variables y genere sus campos de valor.
3. Elige la **variable independiente** y asigna valores a los demás parámetros.
4. Define **Inicio**, **Fin** y **Puntos** del rango de graficado.
5. Presiona **Graficar**.
6. Opcionalmente:
   - Activa **"Activar etiquetas al hacer clic"** para marcar puntos de interés sobre la curva.
   - Activa **"Proporcion X:Y fija (estilo MATLAB)"** para conservar la forma real de las curvas al hacer zoom.
   - Usa la rueda del mouse sobre la gráfica para acercar o alejar la vista.
7. Exporta los resultados con los botones **Excel** o **PNG**.

## 🖱️ Controles de la gráfica

| Acción | Resultado |
|---|---|
| Rueda del mouse sobre la gráfica | Zoom centrado en el cursor |
| Clic izquierdo (con etiquetas activadas) | Agrega una etiqueta numerada con sus coordenadas |
| Botón "X" en el listado de etiquetas | Elimina esa etiqueta específica |
| Barra de herramientas inferior | Pan, zoom por recuadro, guardar imagen, restablecer vista |

## 📁 Estructura del proyecto

```
graficador_universal.py   # Código fuente principal
README.md                 # Este archivo
```

## 🤝 Contribuciones

Las sugerencias, reportes de errores y pull requests son bienvenidos. Abre un *issue* describiendo el cambio propuesto antes de enviar un PR grande.

## 📄 Licencia

Este proyecto se distribuye bajo la licencia MIT. Consulta el archivo `LICENSE` para más detalles.
