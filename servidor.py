import socket
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext

class Servidor:
    def __init__(self):
        self.host = '0.0.0.0'
        self.port = 5000
        self.clientes = {}
        self.socket_servidor = None
        
        # Crear interfaz gráfica
        self.crear_interfaz()
        
    def crear_interfaz(self):
        self.ventana = tk.Tk()
        self.ventana.title("Servidor de Control Remoto")
        self.ventana.geometry("600x400")
        
        # Frame de controles
        frame_controles = ttk.Frame(self.ventana)
        frame_controles.pack(pady=10)
        
        ttk.Button(frame_controles, text="Iniciar Servidor", 
                  command=self.iniciar_servidor).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(frame_controles, text="Detener Servidor", 
                  command=self.detener_servidor).pack(side=tk.LEFT, padx=5)
        
        # Estado del servidor
        self.estado_label = ttk.Label(self.ventana, text="Servidor detenido")
        self.estado_label.pack(pady=5)
        
        # Lista de clientes conectados
        ttk.Label(self.ventana, text="Clientes Conectados:").pack(pady=5)
        self.lista_clientes = tk.Listbox(self.ventana, height=8)
        self.lista_clientes.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Log de actividad
        ttk.Label(self.ventana, text="Log de Actividad:").pack(pady=5)
        self.log_area = scrolledtext.ScrolledText(self.ventana, height=10)
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
    def log(self, mensaje):
        self.log_area.insert(tk.END, f"{mensaje}\n")
        self.log_area.see(tk.END)
        
    def iniciar_servidor(self):
        try:
            self.socket_servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket_servidor.bind((self.host, self.port))
            self.socket_servidor.listen(5)
            
            self.estado_label.config(text=f"Servidor ejecutándose en {self.host}:{self.port}")
            self.log("Servidor iniciado - Esperando conexiones...")
            
            # Hilo para aceptar conexiones
            threading.Thread(target=self.aceptar_conexiones, daemon=True).start()
            
        except Exception as e:
            self.log(f"Error al iniciar servidor: {e}")
            
    def aceptar_conexiones(self):
        while True:
            try:
                cliente_socket, direccion = self.socket_servidor.accept()
                self.log(f"Conexión aceptada desde {direccion}")
                
                # Recibir identificación del cliente
                cliente_id = cliente_socket.recv(1024).decode()
                self.clientes[cliente_id] = {
                    'socket': cliente_socket,
                    'direccion': direccion
                }
                
                # Actualizar lista en interfaz
                self.actualizar_lista_clientes()
                
                # Hilo para manejar este cliente
                threading.Thread(target=self.manejar_cliente, 
                               args=(cliente_socket, cliente_id), daemon=True).start()
                
            except Exception as e:
                self.log(f"Error en aceptar_conexiones: {e}")
                break
                
    def manejar_cliente(self, cliente_socket, cliente_id):
        try:
            while True:
                data = cliente_socket.recv(1024).decode()
                if not data:
                    break
                    
                self.log(f"Mensaje de {cliente_id}: {data}")
                
        except Exception as e:
            self.log(f"Cliente {cliente_id} desconectado: {e}")
        finally:
            if cliente_id in self.clientes:
                del self.clientes[cliente_id]
                self.actualizar_lista_clientes()
                
    def actualizar_lista_clientes(self):
        self.lista_clientes.delete(0, tk.END)
        for cliente_id in self.clientes:
            self.lista_clientes.insert(tk.END, f"{cliente_id} - {self.clientes[cliente_id]['direccion']}")
            
    def detener_servidor(self):
        if self.socket_servidor:
            self.socket_servidor.close()
            self.estado_label.config(text="Servidor detenido")
            self.log("Servidor detenido")
            
    def ejecutar(self):
        self.ventana.mainloop()

if __name__ == "__main__":
    servidor = Servidor()
    servidor.ejecutar()