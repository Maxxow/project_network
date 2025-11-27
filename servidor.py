import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, simpledialog, Toplevel, Label, filedialog, messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import json
import base64
import io
import time
from PIL import Image, ImageTk
import mss

class Servidor:
    def __init__(self):
        self.host = self.obtener_ip_local()
        self.port = 5000
        self.clientes = {} 
        self.socket_servidor = None
        self.ventanas_pantalla = {} 
        self.compartiendo_servidor = False
        
        self.crear_interfaz()
        
    def obtener_ip_local(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except:
            return "127.0.0.1"
        
    def crear_interfaz(self):
        # Usar ttkbootstrap con tema Darkly (modo oscuro suave y agradable)
        self.ventana = ttk.Window(themename="darkly")
        self.ventana.title("🎓 Servidor Maestro - Control Escolar")
        self.ventana.geometry("1200x850")
        
        # Estado del servidor con mejor diseño
        frame_info = ttk.Labelframe(self.ventana, text="🖥️ Estado del Servidor", bootstyle="primary")
        frame_info.pack(fill=tk.X, padx=15, pady=10)
        
        ttk.Label(frame_info, text=f"🌐 IP Local: {self.host} | Puerto: {self.port}", 
                 font=("Segoe UI", 13, "bold")).pack(side=tk.LEFT, padx=15, pady=10)
        self.estado_label = ttk.Label(frame_info, text="⚫ DETENIDO", 
                                     font=("Segoe UI", 13, "bold"), bootstyle="danger")
        self.estado_label.pack(side=tk.RIGHT, padx=15, pady=8)
        
        # Botones principales con colores semánticos
        frame_main_btns = ttk.Frame(self.ventana)
        frame_main_btns.pack(fill=tk.X, padx=15, pady=8)
        
        btn_iniciar = ttk.Button(frame_main_btns, text="▶ INICIAR SERVIDOR", 
                  command=self.iniciar_servidor, 
                  bootstyle="success", width=22)
        btn_iniciar.pack(side=tk.LEFT, padx=8)
        btn_iniciar.configure(style="big.TButton")
        
        btn_detener = ttk.Button(frame_main_btns, text="⏹ DETENER", 
                  command=self.detener_servidor, 
                  bootstyle="danger", width=22)
        btn_detener.pack(side=tk.LEFT, padx=8)
        btn_detener.configure(style="big.TButton")
        
        # Panel dividido con mejor espaciado
        paned = ttk.Panedwindow(self.ventana, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
        
        # Panel izquierdo
        frame_left = ttk.Frame(paned)
        paned.add(frame_left, weight=1)
        
        # Lista de alumnos con estilo
        ttk.Label(frame_left, text="👥 Alumnos Conectados", 
                 font=("Segoe UI", 12, "bold")).pack(anchor=tk.W, padx=5, pady=5)
        self.lista_clientes = tk.Listbox(frame_left, height=8, 
                                        font=("Consolas", 12),
                                        bg="#1a1d23", fg="#00d4ff",
                                        selectbackground="#0d6efd",
                                        selectforeground="white")
        self.lista_clientes.pack(fill=tk.X, padx=5, pady=5)
        
        # Log de eventos con estilo hacker
        ttk.Label(frame_left, text="📋 Log de Eventos", 
                 font=("Segoe UI", 12, "bold")).pack(anchor=tk.W, padx=5, pady=(10,5))
        self.log_area = scrolledtext.ScrolledText(frame_left, height=12,
                                                  font=("Consolas", 11),
                                                  bg="#1a1d23", fg="#00ff41",
                                                  insertbackground="white")
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Chat general con mejor diseño
        frame_chat = ttk.Labelframe(frame_left, text="💬 Chat General", bootstyle="info")
        frame_chat.pack(fill=tk.X, padx=5, pady=8)
        
        self.chat_entry = ttk.Entry(frame_chat, font=("Segoe UI", 12))
        self.chat_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8, pady=10)
        self.chat_entry.bind('<Return>', self.enviar_mensaje_chat_servidor)
        
        ttk.Button(frame_chat, text="📤 Enviar", 
                  command=self.enviar_mensaje_chat_servidor, 
                  bootstyle="primary", width=14).pack(side=tk.RIGHT, padx=8, pady=10)
        
        # Panel derecho - Comandos organizados
        frame_right = ttk.Labelframe(paned, text="🎛️ Panel de Control", bootstyle="secondary")
        paned.add(frame_right, weight=1)
        
        # Sección Visualización
        lbl_vis = ttk.Labelframe(frame_right, text="📺 Visualización y Pantalla", bootstyle="info")
        lbl_vis.pack(fill=tk.X, padx=8, pady=8)
        
        ttk.Button(lbl_vis, text="👁️ Ver Pantalla de Alumno", 
                  command=self.ver_pantalla_cliente, 
                  bootstyle="primary", width=32).pack(fill=tk.X, padx=6, pady=5)
        ttk.Button(lbl_vis, text="📡 Exhibir Alumno a Alumno", 
                  command=self.exhibir_cliente, 
                  bootstyle="primary", width=32).pack(fill=tk.X, padx=6, pady=5)
        ttk.Button(lbl_vis, text="🖥️ Mostrar SERVIDOR a Alumno", 
                  command=self.mostrar_servidor_a_cliente, 
                  bootstyle="primary", width=32).pack(fill=tk.X, padx=6, pady=5)
        ttk.Button(lbl_vis, text="⏹ Detener Transmisiones", 
                  command=self.detener_transmision, 
                  bootstyle="warning", width=32).pack(fill=tk.X, padx=6, pady=5)
        
        # Sección Control Hardware
        lbl_ctrl = ttk.Labelframe(frame_right, text="🔧 Control Hardware", bootstyle="warning")
        lbl_ctrl.pack(fill=tk.X, padx=8, pady=8)
        
        ttk.Button(lbl_ctrl, text="🔒 Bloquear Input", 
                  command=lambda: self.enviar_comando_simple("bloquear_input"), 
                  bootstyle="danger", width=32).pack(fill=tk.X, padx=6, pady=5)
        ttk.Button(lbl_ctrl, text="🔓 Desbloquear Input", 
                  command=lambda: self.enviar_comando_simple("desbloquear_input"), 
                  bootstyle="success", width=32).pack(fill=tk.X, padx=6, pady=5)
        ttk.Button(lbl_ctrl, text="⚡ Apagar Remoto", 
                  command=self.confirmar_apagado, 
                  bootstyle="danger", width=32).pack(fill=tk.X, padx=6, pady=5)
        
        # Sección Red y Restricciones
        lbl_net = ttk.Labelframe(frame_right, text="🌐 Red y Restricciones", bootstyle="secondary")
        lbl_net.pack(fill=tk.X, padx=8, pady=8)
        
        ttk.Button(lbl_net, text="🚫 Bloquear Web", 
                  command=self.bloquear_web_dialogo, 
                  bootstyle="danger-outline", width=32).pack(fill=tk.X, padx=6, pady=5)
        ttk.Button(lbl_net, text="✅ Desbloquear Web", 
                  command=self.desbloquear_web_dialogo, 
                  bootstyle="success-outline", width=32).pack(fill=tk.X, padx=6, pady=5)
        ttk.Button(lbl_net, text="🛡️ Bloquear Ping", 
                  command=lambda: self.control_ping("bloquear"), 
                  bootstyle="danger-outline", width=32).pack(fill=tk.X, padx=6, pady=5)
        ttk.Button(lbl_net, text="✅ Permitir Ping", 
                  command=lambda: self.control_ping("permitir"), 
                  bootstyle="success-outline", width=32).pack(fill=tk.X, padx=6, pady=5)

        # Sección Archivos
        lbl_trans = ttk.Labelframe(frame_right, text="📁 Transferencia de Archivos", bootstyle="info")
        lbl_trans.pack(fill=tk.X, padx=8, pady=8)
        
        ttk.Button(lbl_trans, text="📤 Enviar Archivo a Todos", 
                  command=self.enviar_archivo_dialogo, 
                  bootstyle="primary-outline", width=32).pack(fill=tk.X, padx=6, pady=5)
        
    def log(self, mensaje):
        self.log_area.insert(tk.END, f"{mensaje}\n")
        self.log_area.see(tk.END)
        
    def iniciar_servidor(self):
        try:
            self.socket_servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket_servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket_servidor.bind((self.host, self.port))
            self.socket_servidor.listen(5)
            
            self.estado_label.config(text="🟢 EJECUTANDO", bootstyle="success")
            self.log("✅ Servidor iniciado esperando conexiones...")
            threading.Thread(target=self.aceptar_conexiones, daemon=True).start()
        except Exception as e:
            self.log(f"❌ Error iniciando: {e}")
            
    def aceptar_conexiones(self):
        while True:
            try:
                if not self.socket_servidor: break
                client_sock, addr = self.socket_servidor.accept()
                
                data = client_sock.recv(4096).decode()
                info = json.loads(data)
                cid = info['id']
                
                self.clientes[cid] = {'socket': client_sock, 'direccion': addr, 'info': info}
                
                self.actualizar_lista()
                self.log(f"🔗 Nuevo alumno: {cid} desde {addr[0]}")
                
                threading.Thread(target=self.manejar_cliente, args=(client_sock, cid), daemon=True).start()
            except:
                break
                
    def manejar_cliente(self, sock, cid):
        while True:
            try:
                data = sock.recv(1024*4096)
                if not data: break
                
                mensaje = data.decode('utf-8', errors='ignore')
                
                try:
                    if mensaje.strip().startswith('{') and mensaje.strip().endswith('}'):
                        datos = json.loads(mensaje)
                        self.procesar_mensaje(datos, cid)
                except:
                    pass     
            except:
                break
                
        if cid in self.clientes:
            del self.clientes[cid]
            self.actualizar_lista()
            self.log(f"❌ Alumno desconectado: {cid}")
            
    def procesar_mensaje(self, datos, origen):
        tipo = datos.get('tipo')
        
        if tipo == 'chat':
            self.log(f"💬 {origen}: {datos['contenido']}")
            for cid in self.clientes:
                if cid != origen:
                    self.enviar_json(cid, {'tipo': 'chat_remoto', 'de': origen, 'contenido': datos['contenido']})
                    
        elif tipo == 'imagen_pantalla':
            destino = datos.get('destino')
            if destino == 'servidor':
                self.actualizar_ventana_pantalla(origen, datos['contenido'])
            elif destino in self.clientes:
                self.enviar_json(destino, datos)
                
        elif tipo == 'archivo':
            self.log(f"📂 Archivo recibido de {origen}, retransmitiendo...")
            for cid in self.clientes:
                if cid != origen:
                    self.enviar_json(cid, datos)
                    
    def enviar_json(self, cid, datos):
        try:
            if cid in self.clientes:
                msg = json.dumps(datos)
                self.clientes[cid]['socket'].send(msg.encode())
        except Exception as e:
            self.log(f"❌ Error enviando a {cid}: {e}")

    def enviar_mensaje_chat_servidor(self, event=None):
        mensaje = self.chat_entry.get().strip()
        if mensaje:
            self.log(f"💬 Servidor: {mensaje}")
            for cid in self.clientes:
                self.enviar_json(cid, {'tipo': 'chat_remoto', 'de': 'Profesor', 'contenido': mensaje})
            self.chat_entry.delete(0, tk.END)

    def get_cliente_seleccionado(self):
        sel = self.lista_clientes.curselection()
        if not sel:
            messagebox.showwarning("Selección", "Selecciona un alumno de la lista")
            return None
        return self.lista_clientes.get(sel[0])

    def enviar_comando_simple(self, tipo_comando, extra_data=None):
        cid = self.get_cliente_seleccionado()
        if cid:
            payload = {'tipo': tipo_comando}
            if extra_data: payload.update(extra_data)
            self.enviar_json(cid, payload)
            self.log(f"Comando {tipo_comando} -> {cid}")

    def ver_pantalla_cliente(self):
        cid = self.get_cliente_seleccionado()
        if cid:
            self.enviar_json(cid, {'tipo': 'solicitar_pantalla', 'destino': 'servidor'})
            self.abrir_ventana_pantalla(cid)

    def exhibir_cliente(self):
        origen = self.get_cliente_seleccionado()
        if not origen: return
        
        destino = simpledialog.askstring("Exhibir", f"¿A qué alumno mostrar la pantalla de {origen}?\n(Escribe el nombre exacto del otro alumno)")
        if destino and destino in self.clientes:
            self.enviar_json(origen, {'tipo': 'solicitar_pantalla', 'destino': destino})
            self.log(f"📺 Ordenando a {origen} transmitir a {destino}")
        else:
            self.log("❌ Alumno destino no encontrado")

    # --- 3.5 Mostrar Servidor a Alumno CORREGIDO ---
    def mostrar_servidor_a_cliente(self):
        cid = self.get_cliente_seleccionado()
        if cid:
            self.compartiendo_servidor = True
            
            # Chequeo preventivo de mss
            try:
                with mss.mss() as sct: pass
            except Exception as e:
                self.log(f"❌ Error de captura en servidor: {e}")
                if "Wayland" in str(e):
                    self.log("💡 Sugerencia: Ejecuta con 'GDK_BACKEND=x11 python servidor.py'")
                return
                
            threading.Thread(target=self.hilo_transmitir_servidor, args=(cid,), daemon=True).start()
            self.log(f"📺 Transmitiendo MI pantalla a {cid}")

    def hilo_transmitir_servidor(self, destino):
        try:
            with mss.mss() as sct:
                # Seleccionar monitor con seguridad
                if len(sct.monitors) > 1:
                    monitor = sct.monitors[1]
                else:
                    monitor = sct.monitors[0]
                    
                while self.compartiendo_servidor and (destino in self.clientes):
                    start_time = time.time()
                    try:
                        sct_img = sct.grab(monitor)
                        img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                        img.thumbnail((800, 600))
                        
                        buffer = io.BytesIO()
                        img.save(buffer, format="JPEG", quality=40)
                        img_str = base64.b64encode(buffer.getvalue()).decode()
                        
                        self.enviar_json(destino, {
                            'tipo': 'imagen_pantalla',
                            'destino': 'cliente',
                            'contenido': img_str
                        })
                        
                        elapsed = time.time() - start_time
                        if elapsed < 0.15:
                            time.sleep(0.15 - elapsed)
                    except Exception as e:
                        print(f"Error transmisión loop: {e}")
                        break
        except Exception as e:
            self.log(f"❌ Error en hilo de servidor: {e}")
            
        self.compartiendo_servidor = False
        self.log("⏹ Fin transmisión servidor")

    def detener_transmision(self):
        self.compartiendo_servidor = False
        cid = self.get_cliente_seleccionado()
        if cid:
            self.enviar_json(cid, {'tipo': 'detener_pantalla'})

    def confirmar_apagado(self):
        if messagebox.askyesno("PELIGRO", "¿Apagar equipo remoto?"):
            self.enviar_comando_simple("apagar_pc")

    def bloquear_web_dialogo(self):
        url = simpledialog.askstring("Bloqueo Web", "URL a bloquear (ej: www.youtube.com):")
        if url: self.enviar_comando_simple("bloquear_web", {'url': url})

    def desbloquear_web_dialogo(self):
        url = simpledialog.askstring("Desbloqueo Web", "URL a liberar:")
        if url: self.enviar_comando_simple("desbloquear_web", {'url': url})

    def control_ping(self, accion):
        self.enviar_comando_simple("control_ping", {'accion': accion})

    def enviar_archivo_dialogo(self):
        filepath = filedialog.askopenfilename()
        if filepath:
            threading.Thread(target=self.enviar_archivo, args=(filepath,), daemon=True).start()

    def enviar_archivo(self, filepath):
        try:
            import os
            nombre = os.path.basename(filepath)
            with open(filepath, 'rb') as f:
                contenido = base64.b64encode(f.read()).decode()
            
            for cid in self.clientes:
                self.enviar_json(cid, {'tipo': 'archivo', 'nombre': nombre, 'contenido': contenido})
            self.log(f"📂 Archivo enviado a todos: {nombre}")
        except Exception as e:
            self.log(f"Error archivo: {e}")

    def abrir_ventana_pantalla(self, cid):
        if cid in self.ventanas_pantalla: return
        top = Toplevel(self.ventana)
        top.title(f"Viendo a: {cid}")
        top.geometry("800x600")
        lbl = Label(top)
        lbl.pack(fill=tk.BOTH, expand=True)
        self.ventanas_pantalla[cid] = {'window': top, 'label': lbl}
        
        def on_close():
            self.enviar_json(cid, {'tipo': 'detener_pantalla'})
            if cid in self.ventanas_pantalla: del self.ventanas_pantalla[cid]
            top.destroy()
        top.protocol("WM_DELETE_WINDOW", on_close)

    def actualizar_ventana_pantalla(self, cid, b64_data):
        if cid in self.ventanas_pantalla:
            try:
                img_data = base64.b64decode(b64_data)
                img = Image.open(io.BytesIO(img_data))
                photo = ImageTk.PhotoImage(img)
                lbl = self.ventanas_pantalla[cid]['label']
                lbl.config(image=photo)
                lbl.image = photo
            except: pass

    def actualizar_lista(self):
        self.lista_clientes.delete(0, tk.END)
        for cid in self.clientes:
            self.lista_clientes.insert(tk.END, cid)
            
    def detener_servidor(self):
        if self.socket_servidor:
            self.socket_servidor.close()
            self.socket_servidor = None
        self.estado_label.config(text="⚫ DETENIDO", bootstyle="danger")
        self.compartiendo_servidor = False
        sys.exit()

    def ejecutar(self):
        self.ventana.mainloop()

if __name__ == "__main__":
    servidor = Servidor()
    servidor.ejecutar()