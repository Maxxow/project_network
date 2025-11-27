import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog, Toplevel, Label
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
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
        # Usar ttkbootstrap con tema Darkly (modo oscuro suave y agradable)
        self.ventana = ttk.Window(themename="darkly")
        self.ventana.title(f"🖥️ Cliente - {self.nombre_cliente}")
        self.ventana.geometry("850x750")
        
        # Información del cliente con mejor padding
        frame_info = ttk.Labelframe(self.ventana, text="📋 Información del Cliente", bootstyle="primary")
        frame_info.pack(fill=tk.X, padx=15, pady=10)
        
        ttk.Label(frame_info, text=f"👤 Nombre: {self.nombre_cliente}", 
                 font=("Segoe UI", 12)).pack(anchor=tk.W, padx=10, pady=6)
        ttk.Label(frame_info, text=f"💻 Sistema: {platform.system()} {platform.release()}", 
                 font=("Segoe UI", 12)).pack(anchor=tk.W, padx=10, pady=6)
        
        # Frame de conexión con mejor espaciado
        frame_conexion = ttk.Frame(self.ventana)
        frame_conexion.pack(fill=tk.X, padx=15, pady=10)
        
        ttk.Label(frame_conexion, text="🌐 IP del Servidor:", 
                 font=("Segoe UI", 12, "bold")).pack(side=tk.LEFT, padx=5)
        self.servidor_entry = ttk.Entry(frame_conexion, width=20, font=("Consolas", 12))
        self.servidor_entry.pack(side=tk.LEFT, padx=8)
        self.servidor_entry.insert(0, "127.0.0.1")
        
        # Botones con colores semánticos
        ttk.Button(frame_conexion, text="✅ Conectar", 
                  command=self.conectar_servidor, 
                  bootstyle="success", width=14).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(frame_conexion, text="❌ Desconectar", 
                  command=self.desconectar_servidor, 
                  bootstyle="danger", width=14).pack(side=tk.LEFT, padx=5)
        
        # Estado con indicador visual
        self.estado_label = ttk.Label(self.ventana, text="⚫ Desconectado", 
                                     font=("Segoe UI", 13, "bold"), bootstyle="danger")
        self.estado_label.pack(pady=8)
        
        # Frame principal con mejor organización
        frame_principal = ttk.Frame(self.ventana)
        frame_principal.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
        
        # Log de mensajes con estilo
        frame_log = ttk.Labelframe(frame_principal, text="💬 Mensajes y Actividad", bootstyle="info")
        frame_log.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        self.log_area = scrolledtext.ScrolledText(frame_log, height=16, 
                                                  font=("Consolas", 11),
                                                  bg="#1a1d23", fg="#00ff41",
                                                  insertbackground="white")
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        
        # Frame de controles con mejor diseño
        frame_controles = ttk.Labelframe(frame_principal, text="🎛️ Controles", bootstyle="secondary")
        frame_controles.pack(fill=tk.Y, side=tk.RIGHT, padx=(10,0))
        
        ttk.Button(frame_controles, text="📁 Enviar Archivo", 
                  command=self.enviar_archivo_dialogo, 
                  bootstyle="primary-outline", width=20).pack(padx=10, pady=10)
        
        # Entrada de mensajes (3.3) con mejor estilo
        frame_mensaje = ttk.Labelframe(self.ventana, text="✉️ Chat", bootstyle="info")
        frame_mensaje.pack(fill=tk.X, padx=15, pady=10)
        
        self.mensaje_entry = ttk.Entry(frame_mensaje, font=("Segoe UI", 12))
        self.mensaje_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, pady=10)
        self.mensaje_entry.bind('<Return>', self.enviar_mensaje_chat)
        
        ttk.Button(frame_mensaje, text="📤 Enviar", 
                  command=self.enviar_mensaje_chat, 
                  bootstyle="primary", width=14).pack(side=tk.RIGHT, padx=10, pady=10)
        
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
            self.estado_label.config(text=f"🟢 Conectado a {self.host_servidor}:{self.port_servidor}", bootstyle="success")
            self.log("✅ Conectado al servidor exitosamente")
            
            threading.Thread(target=self.recibir_mensajes, daemon=True).start()
            
        except Exception as e:
            self.log(f"❌ Error al conectar: {e}")
            
    def recibir_mensajes(self):
        while self.conectado:
            try:
                # Buffer grande para recibir imágenes o archivos
                data = self.socket_cliente.recv(1024*4096) 
                if not data:
                    break
                
                mensaje = data.decode('utf-8', errors='ignore')
                
                try:
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
        
        if tipo == 'chat_remoto':
            self.log(f"💬 {datos['de']}: {datos['contenido']}")
            
        elif tipo == 'solicitar_pantalla':
            destino = datos.get('destino', 'servidor')
            self.log(f"📺 Solicitud de transmisión para: {destino}")
            if not self.compartiendo_pantalla:
                threading.Thread(target=self.iniciar_compartir_pantalla, args=(destino,), daemon=True).start()
            
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
            
        elif tipo == 'imagen_pantalla':
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

    # --- Funcionalidades 3.1, 3.4: Emisor de Pantalla ---
    def iniciar_compartir_pantalla(self, destino):
        self.compartiendo_pantalla = True
        self.log(f"🚀 Compartiendo pantalla con {destino}...")
        
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            
            while self.compartiendo_pantalla and self.conectado:
                try:
                    sct_img = sct.grab(monitor)
                    img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                    img.thumbnail((800, 600))
                    
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
            pass

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

    # --- Funcionalidad 3.6, 3.7: Bloqueo Input MEJORADO ---
    def bloquear_input(self):
        if self.bloqueado: return
        self.bloqueado = True
        self.log("🔒 SISTEMA BLOQUEADO (Teclado y Mouse)")
        
        try:
            # 1. Bloquear eventos (suppress=True hace que los clics no pasen)
            self.mouse_listener = mouse.Listener(suppress=True)
            self.mouse_listener.start()
            self.keyboard_listener = keyboard.Listener(suppress=True)
            self.keyboard_listener.start()
            
            # 2. TRAMPA VISUAL: Hilo que fuerza la posición del mouse a 0,0
            # Esto evita que el usuario mueva el cursor visualmente
            threading.Thread(target=self._trampa_mouse, daemon=True).start()
            
        except Exception as e:
            self.log(f"Error bloqueando inputs: {e}")
        
    def _trampa_mouse(self):
        """Mantiene el mouse atrapado en la esquina 0,0 mientras esté bloqueado"""
        controlador = mouse.Controller()
        # Puedes cambiar 0,0 por coordenadas centrales si prefieres
        x_target, y_target = 0, 0 
        
        while self.bloqueado:
            # Forzar posición constantemente
            controlador.position = (x_target, y_target)
            # Frecuencia muy alta para que no se escape
            time.sleep(0.01)

    def desbloquear_input(self):
        if not self.bloqueado: return
        self.bloqueado = False
        self.log("🔓 Sistema desbloqueado")
        
        # Detener listeners
        if self.mouse_listener: 
            self.mouse_listener.stop()
            self.mouse_listener = None
        if self.keyboard_listener: 
            self.keyboard_listener.stop()
            self.keyboard_listener = None

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
        self.estado_label.config(text="⚫ Desconectado", bootstyle="danger")
        self.desbloquear_input()
            
    def ejecutar(self):
        self.ventana.mainloop()

if __name__ == "__main__":
    nombre = sys.argv[1] if len(sys.argv) > 1 else f"Cliente_{platform.node()}"
    cliente = Cliente(nombre)
    cliente.ejecutar()