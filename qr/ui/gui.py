import tkinter as tk

ventana = tk.Tk()
ventana.title("Mi Primera Ventana")
ventana.geometry("400x300")
etiqueta = tk.Label(ventana, text="¡Hola, Mundo!")
etiqueta.pack()
ventana.mainloop()