import tkinter as tk

ventana = tk.Tk()
ventana.title("Mi Primera Ventana")
ventana.geometry("400x300")
etiqueta = tk.Label(ventana, text="¡Hola, Mundo!")
etiqueta.pack()

def crear_qr_canvas():
    canvas = tk.Canvas(ventana, width=600, height=400, bg='white')
    canvas.pack(anchor=tk.CENTER, expand=True)

    return canvas

ventana.mainloop()