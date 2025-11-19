import socket
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext

class Cliente:
    def __init__(self, nombre_cliente):
        self.nombre_cliente = nombre_cliente
        self.host_servidor = 'localhost'  # Cambiar por IP del servidor
        self.port_servidor = 5000
        self.socket_cliente = None
        
        self.crear_interfaz()
        
    def crear_interfaz(self):
        self.ventana = tk.Tk()
        self.ventana.title(f"Cliente - {self.nombre_cliente}")
        self.ventana.geometry("500x400")
        
        # Frame de conexión
        frame_conexion = ttk.Frame(self.ventana)
        frame_conexion.pack(pady=10)
        
        ttk.Label(frame_conexion, text="Servidor:").pack(side=tk.LEFT)
        self.servidor_entry = ttk.Entry(frame_conexion, width=15)
        self.servidor_entry.insert(0, self.host_servidor)
        self.servidor_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(frame_conexion, text="Conectar", 
                  command=self.conectar_servidor).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(frame_conexion, text="Desconectar", 
                  command=self.desconectar_servidor).pack(side=tk.LEFT, padx=5)
        
        # Estado
        self.estado_label = ttk.Label(self.ventana, text="Desconectado")
        self.estado_label.pack(pady=5)
        
        # Log
        ttk.Label(self.ventana, text="Mensajes:").pack(pady=5)
        self.log_area = scrolledtext.ScrolledText(self.ventana, height=15)
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Entrada de mensajes
        frame_mensaje = ttk.Frame(self.ventana)
        frame_mensaje.pack(fill=tk.X, padx=10, pady=5)
        
        self.mensaje_entry = ttk.Entry(frame_mensaje)
        self.mensaje_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.mensaje_entry.bind('<Return>', self.enviar_mensaje)
        
        ttk.Button(frame_mensaje, text="Enviar", 
                  command=self.enviar_mensaje).pack(side=tk.RIGHT, padx=5)
        
    def log(self, mensaje):
        self.log_area.insert(tk.END, f"{mensaje}\n")
        self.log_area.see(tk.END)
        
    def conectar_servidor(self):
        try:
            self.host_servidor = self.servidor_entry.get()
            self.socket_cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket_cliente.connect((self.host_servidor, self.port_servidor))
            
            # Enviar identificación
            self.socket_cliente.send(self.nombre_cliente.encode())
            
            self.estado_label.config(text=f"Conectado a {self.host_servidor}:{self.port_servidor}")
            self.log("Conectado al servidor")
            
            # Hilo para recibir mensajes
            threading.Thread(target=self.recibir_mensajes, daemon=True).start()
            
        except Exception as e:
            self.log(f"Error al conectar: {e}")
            
    def recibir_mensajes(self):
        while True:
            try:
                mensaje = self.socket_cliente.recv(1024).decode()
                if not mensaje:
                    break
                self.log(f"Servidor: {mensaje}")
            except:
                break
                
    def enviar_mensaje(self, event=None):
        mensaje = self.mensaje_entry.get()
        if mensaje and self.socket_cliente:
            try:
                self.socket_cliente.send(mensaje.encode())
                self.log(f"Tú: {mensaje}")
                self.mensaje_entry.delete(0, tk.END)
            except Exception as e:
                self.log(f"Error al enviar: {e}")
                
    def desconectar_servidor(self):
        if self.socket_cliente:
            self.socket_cliente.close()
            self.estado_label.config(text="Desconectado")
            self.log("Desconectado del servidor")
            
    def ejecutar(self):
        self.ventana.mainloop()

if __name__ == "__main__":
    # Para probar, puedes cambiar el nombre: Cliente("Equipo1") o Cliente("Equipo2")
    cliente = Cliente("Equipo1")
    cliente.ejecutar()