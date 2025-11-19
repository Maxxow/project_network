import socket
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext
import json
import platform

class Cliente:
    def __init__(self, nombre_cliente):
        self.nombre_cliente = nombre_cliente
        self.host_servidor = ''  # Se ingresará manualmente
        self.port_servidor = 5000
        self.socket_cliente = None
        self.conectado = False
        
        self.crear_interfaz()
        
    def crear_interfaz(self):
        self.ventana = tk.Tk()
        self.ventana.title(f"Cliente - {self.nombre_cliente}")
        self.ventana.geometry("600x450")
        
        # Información del cliente
        frame_info = ttk.LabelFrame(self.ventana, text="Información del Cliente")
        frame_info.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(frame_info, text=f"Nombre: {self.nombre_cliente}").pack(anchor=tk.W, padx=5, pady=2)
        ttk.Label(frame_info, text=f"Sistema: {platform.system()} {platform.release()}").pack(anchor=tk.W, padx=5, pady=2)
        
        # Frame de conexión
        frame_conexion = ttk.Frame(self.ventana)
        frame_conexion.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(frame_conexion, text="IP del Servidor:").pack(side=tk.LEFT)
        self.servidor_entry = ttk.Entry(frame_conexion, width=15)
        self.servidor_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(frame_conexion, text="Conectar", 
                  command=self.conectar_servidor).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(frame_conexion, text="Desconectar", 
                  command=self.desconectar_servidor).pack(side=tk.LEFT, padx=5)
        
        # Estado
        self.estado_label = ttk.Label(self.ventana, text="Desconectado", foreground="red")
        self.estado_label.pack(pady=5)
        
        # Frame principal
        frame_principal = ttk.Frame(self.ventana)
        frame_principal.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Log de mensajes
        frame_log = ttk.LabelFrame(frame_principal, text="Mensajes")
        frame_log.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        self.log_area = scrolledtext.ScrolledText(frame_log, height=15)
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Frame de controles
        frame_controles = ttk.LabelFrame(frame_principal, text="Controles")
        frame_controles.pack(fill=tk.Y, side=tk.RIGHT, padx=(5,0))
        
        ttk.Button(frame_controles, text="Enviar Pantalla", 
                  command=self.enviar_pantalla, width=15).pack(padx=5, pady=2)
        
        ttk.Button(frame_controles, text="Chat Grupal", 
                  command=self.abrir_chat_grupal, width=15).pack(padx=5, pady=2)
        
        ttk.Button(frame_controles, text="Info Sistema", 
                  command=self.enviar_info_sistema, width=15).pack(padx=5, pady=2)
        
        # Entrada de mensajes
        frame_mensaje = ttk.Frame(self.ventana)
        frame_mensaje.pack(fill=tk.X, padx=10, pady=5)
        
        self.mensaje_entry = ttk.Entry(frame_mensaje)
        self.mensaje_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.mensaje_entry.bind('<Return>', self.enviar_mensaje_chat)
        
        ttk.Button(frame_mensaje, text="Enviar", 
                  command=self.enviar_mensaje_chat).pack(side=tk.RIGHT, padx=5)
        
    def log(self, mensaje):
        self.log_area.insert(tk.END, f"{mensaje}\n")
        self.log_area.see(tk.END)
        
    def conectar_servidor(self):
        if self.conectado:
            return
            
        try:
            self.host_servidor = self.servidor_entry.get().strip()
            if not self.host_servidor:
                self.log("❌ Ingresa la IP del servidor")
                return
                
            self.socket_cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket_cliente.settimeout(5)  # Timeout de 5 segundos
            self.socket_cliente.connect((self.host_servidor, self.port_servidor))
            
            # Enviar información de identificación
            info_cliente = {
                'id': self.nombre_cliente,
                'sistema': platform.system(),
                'version': platform.release()
            }
            self.socket_cliente.send(json.dumps(info_cliente).encode())
            
            self.conectado = True
            self.estado_label.config(text=f"Conectado a {self.host_servidor}:{self.port_servidor}", foreground="green")
            self.log("✅ Conectado al servidor exitosamente")
            
            # Hilo para recibir mensajes
            threading.Thread(target=self.recibir_mensajes, daemon=True).start()
            
        except socket.timeout:
            self.log("❌ Timeout: No se pudo conectar al servidor")
        except Exception as e:
            self.log(f"❌ Error al conectar: {e}")
            
    def recibir_mensajes(self):
        while self.conectado:
            try:
                mensaje = self.socket_cliente.recv(1024).decode()
                if not mensaje:
                    break
                    
                try:
                    # Intentar parsear como JSON
                    datos = json.loads(mensaje)
                    self.procesar_mensaje_json(datos)
                except json.JSONDecodeError:
                    # Mensaje plano
                    self.log(f"📨 Servidor: {mensaje}")
                    
            except Exception as e:
                if self.conectado:  # Solo logear si aún debería estar conectado
                    self.log(f"❌ Error en recibir_mensajes: {e}")
                break
                
        if self.conectado:
            self.desconectar_servidor()
                
    def procesar_mensaje_json(self, datos):
        tipo = datos.get('tipo')
        
        if tipo == 'chat_remoto':
            self.log(f"💬 {datos['de']}: {datos['contenido']}")
        elif tipo == 'solicitar_pantalla':
            self.log(f"📺 El servidor solicita ver tu pantalla")
            # Aquí implementaremos la captura de pantalla después
            
    def enviar_mensaje_chat(self, event=None):
        if not self.conectado:
            self.log("❌ No estás conectado al servidor")
            return
            
        mensaje = self.mensaje_entry.get().strip()
        if mensaje:
            try:
                mensaje_json = json.dumps({
                    'tipo': 'chat',
                    'contenido': mensaje
                })
                self.socket_cliente.send(mensaje_json.encode())
                self.log(f"💬 Tú: {mensaje}")
                self.mensaje_entry.delete(0, tk.END)
            except Exception as e:
                self.log(f"❌ Error al enviar mensaje: {e}")
                
    def enviar_pantalla(self):
        if self.conectado:
            self.log("🖥️ Funcionalidad de pantalla - Próximamente...")
            
    def abrir_chat_grupal(self):
        self.log("💬 Chat grupal activo - Escribe en la barra de mensajes")
            
    def enviar_info_sistema(self):
        info = f"Sistema: {platform.system()} {platform.release()}"
        self.log(f"🖥️ {info}")
        if self.conectado:
            try:
                self.socket_cliente.send(info.encode())
            except:
                pass
                
    def desconectar_servidor(self):
        if self.socket_cliente:
            self.socket_cliente.close()
            self.socket_cliente = None
        self.conectado = False
        self.estado_label.config(text="Desconectado", foreground="red")
        self.log("❌ Desconectado del servidor")
            
    def ejecutar(self):
        self.ventana.mainloop()

if __name__ == "__main__":
    # Para usar: cambiar por "Equipo1" o "Equipo2"
    import sys
    nombre = sys.argv[1] if len(sys.argv) > 1 else "Cliente"
    cliente = Cliente(nombre)
    cliente.ejecutar()