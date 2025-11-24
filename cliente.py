import socket
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import json
import platform
import os
import sys
import subprocess
import time
import base64
import io
from PIL import Image
import mss
from pynput import keyboard, mouse

class Cliente:
    def __init__(self, nombre_cliente):
        self.nombre_cliente = nombre_cliente
        self.host_servidor = ''
        self.port_servidor = 5000
        self.socket_cliente = None
        self.conectado = False
        self.bloqueado = False
        self.keyboard_listener = None
        self.mouse_listener = None
        self.compartiendo_pantalla = False
        
        self.crear_interfaz()
        
    def crear_interfaz(self):
        self.ventana = tk.Tk()
        self.ventana.title(f"Cliente - {self.nombre_cliente}")
        self.ventana.geometry("600x500")
        
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
        
        ttk.Button(frame_controles, text="Enviar Archivo", 
                  command=self.enviar_archivo_dialogo, width=15).pack(padx=5, pady=2)
        
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
            self.socket_cliente.settimeout(5)
            self.socket_cliente.connect((self.host_servidor, self.port_servidor))
            self.socket_cliente.settimeout(None) # Quitar timeout para operación normal
            
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
            
        except Exception as e:
            self.log(f"❌ Error al conectar: {e}")
            
    def recibir_mensajes(self):
        buffer = ""
        while self.conectado:
            try:
                # Leer longitud del mensaje primero (protocolo simple: 10 bytes para longitud)
                # Pero para mantener compatibilidad con el código anterior que usaba json directo,
                # vamos a usar un delimitador o intentar leer json.
                # Para simplificar y soportar imágenes base64 grandes, aumentamos el buffer
                # y usamos un protocolo de líneas o delimitadores si fuera necesario.
                # Por ahora, asumiremos que los mensajes JSON caben en el buffer o llegan completos.
                # Una mejor implementación usaría un prefijo de longitud.
                
                # Implementación robusta: Leer hasta encontrar un JSON válido o usar prefijo.
                # Vamos a usar un tamaño grande de buffer.
                data = self.socket_cliente.recv(1024*1024) # 1MB buffer
                if not data:
                    break
                
                mensaje = data.decode('utf-8', errors='ignore')
                
                # Intentar procesar múltiples mensajes si llegan pegados
                # Esto es una simplificación. En producción se necesita un protocolo de framing.
                try:
                    datos = json.loads(mensaje)
                    self.procesar_mensaje_json(datos)
                except json.JSONDecodeError:
                    # Si falla, podría ser que llegaron varios mensajes o está incompleto
                    # Para este ejercicio escolar, asumiremos mensajes atómicos o simples
                    self.log(f"📨 Servidor: {mensaje[:50]}...")
                    
            except Exception as e:
                if self.conectado:
                    self.log(f"❌ Error en conexión: {e}")
                break
                
        if self.conectado:
            self.desconectar_servidor()
            
    def procesar_mensaje_json(self, datos):
        tipo = datos.get('tipo')
        
        if tipo == 'chat_remoto':
            self.log(f"💬 {datos['de']}: {datos['contenido']}")
            
        elif tipo == 'solicitar_pantalla':
            self.log(f"📺 El servidor solicita ver tu pantalla")
            threading.Thread(target=self.iniciar_compartir_pantalla, args=(datos.get('destino', 'servidor'),), daemon=True).start()
            
        elif tipo == 'detener_pantalla':
            self.compartiendo_pantalla = False
            self.log("📺 Transmisión de pantalla detenida")
            
        elif tipo == 'bloquear_input':
            self.bloquear_input()
            
        elif tipo == 'desbloquear_input':
            self.desbloquear_input()
            
        elif tipo == 'apagar_pc':
            self.apagar_pc()
            
        elif tipo == 'bloquear_web':
            self.bloquear_web(datos.get('url'))

        elif tipo == 'desbloquear_web':
            self.desbloquear_web(datos.get('url'))
            
        elif tipo == 'control_ping':
            self.controlar_ping(datos.get('accion'))
            
        elif tipo == 'archivo':
            self.recibir_archivo(datos)
            
        elif tipo == 'mostrar_imagen':
            self.mostrar_imagen_remota(datos)

    def enviar_mensaje_chat(self, event=None):
        if not self.conectado:
            return
        mensaje = self.mensaje_entry.get().strip()
        if mensaje:
            self.enviar_json({'tipo': 'chat', 'contenido': mensaje})
            self.log(f"💬 Tú: {mensaje}")
            self.mensaje_entry.delete(0, tk.END)

    def enviar_json(self, datos):
        try:
            mensaje = json.dumps(datos)
            self.socket_cliente.send(mensaje.encode())
        except Exception as e:
            self.log(f"❌ Error al enviar: {e}")

    # --- Funcionalidades 3.1, 3.4, 3.5: Pantalla ---
    def iniciar_compartir_pantalla(self, destino):
        self.compartiendo_pantalla = True
        self.log(f"🚀 Iniciando transmisión de pantalla a {destino}...")
        
        with mss.mss() as sct:
            monitor = sct.monitors[1] # Monitor principal
            
            while self.compartiendo_pantalla and self.conectado:
                try:
                    # Capturar pantalla
                    sct_img = sct.grab(monitor)
                    img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                    
                    # Redimensionar para rendimiento
                    img.thumbnail((800, 600))
                    
                    # Convertir a bytes JPEG
                    buffer = io.BytesIO()
                    img.save(buffer, format="JPEG", quality=50)
                    img_str = base64.b64encode(buffer.getvalue()).decode()
                    
                    # Enviar
                    self.enviar_json({
                        'tipo': 'imagen_pantalla',
                        'destino': destino,
                        'contenido': img_str
                    })
                    
                    time.sleep(0.1) # ~10 FPS
                except Exception as e:
                    self.log(f"❌ Error compartiendo pantalla: {e}")
                    break
        self.compartiendo_pantalla = False

    def mostrar_imagen_remota(self, datos):
        # Esta función mostraría la imagen recibida en una ventana aparte
        # Por simplicidad, solo logueamos que llegó
        # En una implementación real, actualizaríamos un Label con la imagen
        pass

    # --- Funcionalidad 3.2: Transferencia de Archivos ---
    def enviar_archivo_dialogo(self):
        filename = filedialog.askopenfilename()
        if filename and self.conectado:
            threading.Thread(target=self.enviar_archivo, args=(filename,), daemon=True).start()
            
    def enviar_archivo(self, filepath):
        try:
            nombre_archivo = os.path.basename(filepath)
            with open(filepath, 'rb') as f:
                contenido = base64.b64encode(f.read()).decode()
                
            self.enviar_json({
                'tipo': 'archivo',
                'nombre': nombre_archivo,
                'contenido': contenido
            })
            self.log(f"📂 Archivo enviado: {nombre_archivo}")
        except Exception as e:
            self.log(f"❌ Error enviando archivo: {e}")
            
    def recibir_archivo(self, datos):
        try:
            nombre = datos['nombre']
            contenido = base64.b64decode(datos['contenido'])
            
            # Guardar en descargas o carpeta actual
            with open(f"recibido_{nombre}", 'wb') as f:
                f.write(contenido)
            self.log(f"📂 Archivo recibido y guardado: recibido_{nombre}")
        except Exception as e:
            self.log(f"❌ Error guardando archivo: {e}")

    # --- Funcionalidad 3.6, 3.7: Bloqueo Input ---
    def bloquear_input(self):
        if self.bloqueado: return
        self.bloqueado = True
        self.log("🔒 TECLADO Y MOUSE BLOQUEADOS")
        
        # Bloquear mouse
        self.mouse_listener = mouse.Listener(suppress=True)
        self.mouse_listener.start()
        
        # Bloquear teclado
        self.keyboard_listener = keyboard.Listener(suppress=True)
        self.keyboard_listener.start()
        
    def desbloquear_input(self):
        if not self.bloqueado: return
        self.bloqueado = False
        self.log("🔓 Teclado y mouse desbloqueados")
        
        if self.mouse_listener:
            self.mouse_listener.stop()
        if self.keyboard_listener:
            self.keyboard_listener.stop()

    # --- Funcionalidad 3.8: Apagar PC ---
    def apagar_pc(self):
        self.log("⚠️ APAGANDO EL EQUIPO...")
        if platform.system() == "Windows":
            os.system("shutdown /s /t 5")
        else:
            os.system("shutdown -h now")

    # --- Funcionalidad 3.9: Bloquear Web ---
    def bloquear_web(self, url):
        if not url: return
        self.log(f"🚫 Bloqueando acceso a {url}")
        
        hosts_path = r"C:\Windows\System32\drivers\etc\hosts" if platform.system() == "Windows" else "/etc/hosts"
        redirect = "127.0.0.1"
        
        try:
            with open(hosts_path, 'r+') as file:
                content = file.read()
                if url not in content:
                    file.write(f"\n{redirect} {url}")
                    self.log("✅ Sitio bloqueado (requiere admin)")
                else:
                    self.log("⚠️ El sitio ya estaba bloqueado")
        except PermissionError:
            self.log("❌ Error: Se requieren permisos de administrador para bloquear webs")

    def desbloquear_web(self, url):
        if not url: return
        self.log(f"🔓 Desbloqueando acceso a {url}")
        
        hosts_path = r"C:\Windows\System32\drivers\etc\hosts" if platform.system() == "Windows" else "/etc/hosts"
        redirect = "127.0.0.1"
        
        try:
            lines = []
            with open(hosts_path, 'r') as file:
                lines = file.readlines()
            
            with open(hosts_path, 'w') as file:
                for line in lines:
                    if url not in line:
                        file.write(line)
            
            self.log("✅ Sitio desbloqueado (requiere admin)")
        except PermissionError:
            self.log("❌ Error: Se requieren permisos de administrador para desbloquear webs")
        except Exception as e:
            self.log(f"❌ Error al desbloquear: {e}")

    # --- Funcionalidad 3.10: Ping ---
    def controlar_ping(self, accion):
        sistema = platform.system()
        try:
            if accion == "bloquear":
                self.log("🚫 Bloqueando Ping...")
                if sistema == "Windows":
                    os.system("netsh advfirewall firewall add rule name=\"BlockPing\" protocol=icmpv4:8,any dir=in action=block")
                else:
                    os.system("iptables -A INPUT -p icmp --icmp-type echo-request -j DROP")
            else:
                self.log("✅ Permitiendo Ping...")
                if sistema == "Windows":
                    os.system("netsh advfirewall firewall delete rule name=\"BlockPing\"")
                else:
                    os.system("iptables -D INPUT -p icmp --icmp-type echo-request -j DROP")
        except Exception as e:
            self.log(f"❌ Error configurando firewall: {e}")

    def desconectar_servidor(self):
        if self.socket_cliente:
            self.socket_cliente.close()
            self.socket_cliente = None
        self.conectado = False
        self.estado_label.config(text="Desconectado", foreground="red")
        self.log("❌ Desconectado del servidor")
        self.desbloquear_input() # Asegurar desbloqueo al desconectar
            
    def ejecutar(self):
        self.ventana.mainloop()

if __name__ == "__main__":
    import sys
    nombre = sys.argv[1] if len(sys.argv) > 1 else "Cliente"
    cliente = Cliente(nombre)
    cliente.ejecutar()