import socket
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext
import json

class Servidor:
    def __init__(self):
        # Obtener IP automáticamente para conexión inalámbrica
        self.host = self.obtener_ip_local()
        self.port = 5000
        self.clientes = {}  # {cliente_id: socket}
        self.socket_servidor = None
        
        self.crear_interfaz()
        
    def obtener_ip_local(self):
        """Obtiene la IP local para conexión inalámbrica"""
        try:
            # Conectar a un servidor externo para obtener la IP local
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except:
            return "127.0.0.1"  # Fallback a localhost
        
    def crear_interfaz(self):
        self.ventana = tk.Tk()
        self.ventana.title("Servidor de Control Remoto - Conexión Inalámbrica")
        self.ventana.geometry("700x500")
        
        # Información de conexión
        frame_info = ttk.LabelFrame(self.ventana, text="Información del Servidor")
        frame_info.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(frame_info, text=f"IP del Servidor: {self.host}").pack(anchor=tk.W, padx=5, pady=2)
        ttk.Label(frame_info, text=f"Puerto: {self.port}").pack(anchor=tk.W, padx=5, pady=2)
        ttk.Label(frame_info, text="Los clientes deben conectarse a esta IP").pack(anchor=tk.W, padx=5, pady=2)
        
        # Frame de controles
        frame_controles = ttk.Frame(self.ventana)
        frame_controles.pack(pady=10)
        
        ttk.Button(frame_controles, text="Iniciar Servidor", 
                  command=self.iniciar_servidor).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(frame_controles, text="Detener Servidor", 
                  command=self.detener_servidor).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(frame_controles, text="Enviar a Todos", 
                  command=self.enviar_a_todos).pack(side=tk.LEFT, padx=5)
        
        # Estado del servidor
        self.estado_label = ttk.Label(self.ventana, text="Servidor detenido", foreground="red")
        self.estado_label.pack(pady=5)
        
        # Lista de clientes conectados
        frame_clientes = ttk.LabelFrame(self.ventana, text="Clientes Conectados (0/2)")
        frame_clientes.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.lista_clientes = tk.Listbox(frame_clientes, height=6)
        self.lista_clientes.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Frame para controles de clientes
        frame_acciones = ttk.Frame(frame_clientes)
        frame_acciones.pack(fill=tk.X, pady=5)
        
        ttk.Button(frame_acciones, text="Solicitar Pantalla", 
                  command=self.solicitar_pantalla).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(frame_acciones, text="Enviar Mensaje", 
                  command=self.enviar_mensaje_cliente).pack(side=tk.LEFT, padx=2)
        
        # Log de actividad
        frame_log = ttk.LabelFrame(self.ventana, text="Log de Actividad")
        frame_log.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.log_area = scrolledtext.ScrolledText(frame_log, height=12)
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
    def log(self, mensaje):
        self.log_area.insert(tk.END, f"{mensaje}\n")
        self.log_area.see(tk.END)
        
    def iniciar_servidor(self):
        try:
            self.socket_servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket_servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket_servidor.bind((self.host, self.port))
            self.socket_servidor.listen(5)
            
            self.estado_label.config(text=f"Servidor ejecutándose en {self.host}:{self.port}", foreground="green")
            self.log("✅ Servidor iniciado - Esperando conexiones inalámbricas...")
            self.log(f"📡 Los clientes deben conectarse a: {self.host}:{self.port}")
            
            # Hilo para aceptar conexiones
            threading.Thread(target=self.aceptar_conexiones, daemon=True).start()
            
        except Exception as e:
            self.log(f"❌ Error al iniciar servidor: {e}")
            
    def aceptar_conexiones(self):
        while True:
            try:
                if not self.socket_servidor:
                    break
                    
                cliente_socket, direccion = self.socket_servidor.accept()
                self.log(f"🔗 Nueva conexión desde {direccion}")
                
                # Recibir identificación del cliente
                datos_cliente = cliente_socket.recv(1024).decode()
                info_cliente = json.loads(datos_cliente)
                cliente_id = info_cliente['id']
                
                self.clientes[cliente_id] = {
                    'socket': cliente_socket,
                    'direccion': direccion,
                    'info': info_cliente
                }
                
                self.log(f"✅ Cliente {cliente_id} conectado desde {direccion}")
                
                # Actualizar lista en interfaz
                self.actualizar_lista_clientes()
                
                # Hilo para manejar este cliente
                threading.Thread(target=self.manejar_cliente, 
                               args=(cliente_socket, cliente_id), daemon=True).start()
                
            except Exception as e:
                self.log(f"❌ Error en aceptar_conexiones: {e}")
                break
                
    def manejar_cliente(self, cliente_socket, cliente_id):
        try:
            while True:
                data = cliente_socket.recv(1024).decode()
                if not data:
                    break
                    
                try:
                    mensaje = json.loads(data)
                    self.procesar_mensaje(mensaje, cliente_id)
                except json.JSONDecodeError:
                    self.log(f"📨 Mensaje de {cliente_id}: {data}")
                    
        except Exception as e:
            self.log(f"⚠️ Cliente {cliente_id} desconectado: {e}")
        finally:
            if cliente_id in self.clientes:
                del self.clientes[cliente_id]
                self.actualizar_lista_clientes()
                self.log(f"❌ Cliente {cliente_id} desconectado")
                
    def procesar_mensaje(self, mensaje, cliente_id):
        tipo = mensaje.get('tipo')
        
        if tipo == 'chat':
            self.log(f"💬 {cliente_id}: {mensaje['contenido']}")
            # Reenviar a otros clientes
            self.reenviar_mensaje(mensaje, cliente_id)
            
    def reenviar_mensaje(self, mensaje, cliente_origen):
        for cliente_id, info in self.clientes.items():
            if cliente_id != cliente_origen:
                try:
                    mensaje_reenvio = json.dumps({
                        'tipo': 'chat_remoto',
                        'de': cliente_origen,
                        'contenido': mensaje['contenido']
                    })
                    info['socket'].send(mensaje_reenvio.encode())
                except Exception as e:
                    self.log(f"❌ Error al reenviar a {cliente_id}: {e}")
                    
    def solicitar_pantalla(self):
        seleccionado = self.lista_clientes.curselection()
        if seleccionado:
            cliente_id = self.lista_clientes.get(seleccionado[0]).split(" - ")[0]
            
            mensaje = json.dumps({
                'tipo': 'solicitar_pantalla',
                'destino': cliente_id
            })
            
            try:
                self.clientes[cliente_id]['socket'].send(mensaje.encode())
                self.log(f"📺 Solicitando pantalla de {cliente_id}")
            except Exception as e:
                self.log(f"❌ Error al solicitar pantalla: {e}")
                
    def enviar_mensaje_cliente(self):
        seleccionado = self.lista_clientes.curselection()
        if seleccionado:
            cliente_id = self.lista_clientes.get(seleccionado[0]).split(" - ")[0]
            mensaje = tk.simpledialog.askstring("Enviar mensaje", f"Mensaje para {cliente_id}:")
            
            if mensaje:
                try:
                    self.clientes[cliente_id]['socket'].send(mensaje.encode())
                    self.log(f"📤 Mensaje enviado a {cliente_id}: {mensaje}")
                except Exception as e:
                    self.log(f"❌ Error al enviar mensaje: {e}")
                    
    def enviar_a_todos(self):
        mensaje = tk.simpledialog.askstring("Enviar a todos", "Mensaje para todos los clientes:")
        if mensaje:
            for cliente_id, info in self.clientes.items():
                try:
                    info['socket'].send(mensaje.encode())
                except Exception as e:
                    self.log(f"❌ Error al enviar a {cliente_id}: {e}")
            self.log(f"📤 Mensaje enviado a todos: {mensaje}")
                
    def actualizar_lista_clientes(self):
        self.lista_clientes.delete(0, tk.END)
        for cliente_id, info in self.clientes.items():
            self.lista_clientes.insert(tk.END, f"{cliente_id} - {info['direccion'][0]}")
            
        # Actualizar título del frame
        for widget in self.ventana.winfo_children():
            if isinstance(widget, ttk.LabelFrame) and "Clientes Conectados" in widget.cget('text'):
                widget.config(text=f"Clientes Conectados ({len(self.clientes)}/2)")
            
    def detener_servidor(self):
        if self.socket_servidor:
            self.socket_servidor.close()
            self.socket_servidor = None
            self.estado_label.config(text="Servidor detenido", foreground="red")
            self.log("🛑 Servidor detenido")
            
    def ejecutar(self):
        self.ventana.mainloop()

if __name__ == "__main__":
    servidor = Servidor()
    servidor.ejecutar()