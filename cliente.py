import socket
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog, Toplevel, Label
import json
import platform
import os
import sys
import subprocess
import time
import base64
import io
from PIL import Image, ImageTk
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
        self.ventana_remota = None # Para ver al servidor (3.5) o a otro cliente
        
        self.crear_interfaz()
        
    def crear_interfaz(self):
        self.ventana = tk.Tk()
        self.ventana.title(f"Cliente - {self.nombre_cliente}")
        self.ventana.geometry("600x550")
        
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
        self.servidor_entry.insert(0, "127.0.0.1") # Default localhost para pruebas
        
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
        
        # Frame de controles (Envío archivos 3.2)
        frame_controles = ttk.LabelFrame(frame_principal, text="Controles")
        frame_controles.pack(fill=tk.Y, side=tk.RIGHT, padx=(5,0))
        
        ttk.Button(frame_controles, text="Enviar Archivo (3.2)", 
                  command=self.enviar_archivo_dialogo, width=20).pack(padx=5, pady=2)
        
        # Entrada de mensajes (3.3)
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
            self.socket_cliente.settimeout(None)
            
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
            
            threading.Thread(target=self.recibir_mensajes, daemon=True).start()
            
        except Exception as e:
            self.log(f"❌ Error al conectar: {e}")
            
    def recibir_mensajes(self):
        while self.conectado:
            try:
                # Buffer grande para recibir imágenes o archivos
                data = self.socket_cliente.recv(1024*2048) 
                if not data:
                    break
                
                mensaje = data.decode('utf-8', errors='ignore')
                
                try:
                    # En un entorno real se necesita un delimitador.
                    # Aquí intentamos parsear lo que llega.
                    if mensaje.strip().startswith('{') and mensaje.strip().endswith('}'):
                        datos = json.loads(mensaje)
                        self.procesar_mensaje_json(datos)
                except json.JSONDecodeError:
                    pass
                    
            except Exception as e:
                if self.conectado:
                    self.log(f"❌ Error en conexión: {e}")
                break
                
        if self.conectado:
            self.desconectar_servidor()
            
    def procesar_mensaje_json(self, datos):
        tipo = datos.get('tipo')
        
        if tipo == 'chat_remoto': # 3.3
            self.log(f"💬 {datos['de']}: {datos['contenido']}")
            
        elif tipo == 'solicitar_pantalla': # 3.1 y 3.4 (Emisor)
            destino = datos.get('destino', 'servidor')
            self.log(f"📺 Solicitud de transmisión para: {destino}")
            if not self.compartiendo_pantalla:
                threading.Thread(target=self.iniciar_compartir_pantalla, args=(destino,), daemon=True).start()
            
        elif tipo == 'detener_pantalla':
            self.compartiendo_pantalla = False
            self.log("📺 Transmisión de pantalla detenida")
            
        elif tipo == 'bloquear_input': # 3.6
            self.bloquear_input()
            
        elif tipo == 'desbloquear_input': # 3.7
            self.desbloquear_input()
            
        elif tipo == 'apagar_pc': # 3.8
            self.apagar_pc()
            
        elif tipo == 'bloquear_web': # 3.9
            self.bloquear_web(datos.get('url'))

        elif tipo == 'desbloquear_web': # 3.9
            self.desbloquear_web(datos.get('url'))
            
        elif tipo == 'control_ping': # 3.10
            self.controlar_ping(datos.get('accion'))
            
        elif tipo == 'archivo': # 3.2
            self.recibir_archivo(datos)
            
        elif tipo == 'imagen_pantalla': # 3.4 (Receptor) y 3.5 (Receptor del Servidor)
            self.mostrar_imagen_remota(datos)

    def enviar_mensaje_chat(self, event=None): # 3.3
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

    # --- Funcionalidades 3.1, 3.4: Emisor de Pantalla ---
    def iniciar_compartir_pantalla(self, destino):
        self.compartiendo_pantalla = True
        self.log(f"🚀 Compartiendo pantalla con {destino}...")
        
        with mss.mss() as sct:
            # Detectar monitor. Linux a veces requiere ajustes específicos
            monitor = sct.monitors[1]
            
            while self.compartiendo_pantalla and self.conectado:
                try:
                    sct_img = sct.grab(monitor)
                    img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                    img.thumbnail((800, 600)) # Reducir calidad para velocidad
                    
                    buffer = io.BytesIO()
                    img.save(buffer, format="JPEG", quality=40)
                    img_str = base64.b64encode(buffer.getvalue()).decode()
                    
                    self.enviar_json({
                        'tipo': 'imagen_pantalla',
                        'destino': destino,
                        'contenido': img_str
                    })
                    
                    time.sleep(0.15)
                except Exception as e:
                    self.log(f"❌ Error compartiendo: {e}")
                    break
        self.compartiendo_pantalla = False

    # --- Funcionalidad 3.4 y 3.5: Receptor de Pantalla ---
    def mostrar_imagen_remota(self, datos):
        # Esta función faltaba implementar en el código original
        try:
            contenido = datos['contenido']
            img_data = base64.b64decode(contenido)
            img = Image.open(io.BytesIO(img_data))
            photo = ImageTk.PhotoImage(img)

            if self.ventana_remota is None or not tk.Toplevel.winfo_exists(self.ventana_remota):
                self.ventana_remota = Toplevel(self.ventana)
                self.ventana_remota.title("Visualización Remota")
                self.lbl_remoto = Label(self.ventana_remota)
                self.lbl_remoto.pack()
                
                def on_close():
                    self.ventana_remota.destroy()
                    self.ventana_remota = None
                self.ventana_remota.protocol("WM_DELETE_WINDOW", on_close)

            self.lbl_remoto.config(image=photo)
            self.lbl_remoto.image = photo
        except Exception as e:
            print(f"Error renderizando imagen remota: {e}")

    # --- Funcionalidad 3.2: Archivos ---
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
            self.log(f"📤 Archivo enviado: {nombre_archivo}")
        except Exception as e:
            self.log(f"❌ Error enviando archivo: {e}")
            
    def recibir_archivo(self, datos):
        try:
            nombre = datos['nombre']
            contenido = base64.b64decode(datos['contenido'])
            
            with open(f"recibido_{nombre}", 'wb') as f:
                f.write(contenido)
            self.log(f"📥 Archivo recibido: recibido_{nombre}")
            messagebox.showinfo("Archivo", f"Se recibió el archivo: {nombre}")
        except Exception as e:
            self.log(f"❌ Error guardando archivo: {e}")

    # --- Funcionalidad 3.6, 3.7: Bloqueo Input ---
    def bloquear_input(self):
        if self.bloqueado: return
        self.bloqueado = True
        self.log("🔒 SISTEMA BLOQUEADO POR SERVIDOR")
        
        try:
            self.mouse_listener = mouse.Listener(suppress=True)
            self.mouse_listener.start()
            self.keyboard_listener = keyboard.Listener(suppress=True)
            self.keyboard_listener.start()
        except Exception as e:
            self.log(f"Error bloqueando inputs (¿Linux sin sudo?): {e}")
        
    def desbloquear_input(self):
        if not self.bloqueado: return
        self.bloqueado = False
        self.log("🔓 Sistema desbloqueado")
        
        if self.mouse_listener: self.mouse_listener.stop()
        if self.keyboard_listener: self.keyboard_listener.stop()

    # --- Funcionalidad 3.8: Apagar PC ---
    def apagar_pc(self):
        self.log("⚠️ RECIBIDO COMANDO DE APAGADO")
        time.sleep(2)
        if platform.system() == "Windows":
            os.system("shutdown /s /t 0")
        else: # Linux
            os.system("shutdown -h now")

    # --- Funcionalidad 3.9: Bloquear Web ---
    def bloquear_web(self, url):
        if not url: return
        self.log(f"🚫 Intentando bloquear {url}...")
        
        # Rutas según SO
        hosts_path = r"C:\Windows\System32\drivers\etc\hosts" if platform.system() == "Windows" else "/etc/hosts"
        redirect = "127.0.0.1"
        
        try:
            with open(hosts_path, 'r+') as file:
                content = file.read()
                if url not in content:
                    file.write(f"\n{redirect} {url}")
                    self.log(f"✅ {url} bloqueado.")
                else:
                    self.log(f"⚠️ {url} ya estaba bloqueado.")
        except PermissionError:
            self.log("❌ ERROR: Se requieren permisos de ADMIN/ROOT para bloquear webs.")

    def desbloquear_web(self, url):
        if not url: return
        self.log(f"🔓 Desbloqueando {url}...")
        
        hosts_path = r"C:\Windows\System32\drivers\etc\hosts" if platform.system() == "Windows" else "/etc/hosts"
        
        try:
            with open(hosts_path, 'r') as file:
                lines = file.readlines()
            
            with open(hosts_path, 'w') as file:
                for line in lines:
                    if url not in line:
                        file.write(line)
            self.log(f"✅ {url} desbloqueado.")
        except PermissionError:
            self.log("❌ ERROR: Se requieren permisos de ADMIN/ROOT.")

    # --- Funcionalidad 3.10: Ping ---
    def controlar_ping(self, accion):
        sistema = platform.system()
        try:
            if accion == "bloquear":
                self.log("🚫 Bloqueando Ping entrante...")
                if sistema == "Windows":
                    # Requiere correr como Admin
                    os.system("netsh advfirewall firewall add rule name=\"BlockPing\" protocol=icmpv4:8,any dir=in action=block")
                else:
                    # Requiere sudo
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
        self.desbloquear_input()
            
    def ejecutar(self):
        self.ventana.mainloop()

if __name__ == "__main__":
    nombre = sys.argv[1] if len(sys.argv) > 1 else f"Cliente_{platform.node()}"
    cliente = Cliente(nombre)
    cliente.ejecutar()