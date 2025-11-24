import socket
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, simpledialog, Toplevel, Label, filedialog, messagebox
import json
import base64
import io
import time
from PIL import Image, ImageTk
# Importamos mss para el punto 3.5 (Mostrar Servidor)
import mss

class Servidor:
    def __init__(self):
        self.host = self.obtener_ip_local()
        self.port = 5000
        self.clientes = {} 
        self.socket_servidor = None
        self.ventanas_pantalla = {} 
        
        # Control de transmisión del servidor (3.5)
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
        self.ventana = tk.Tk()
        self.ventana.title("Servidor Maestro - Control Escolar")
        self.ventana.geometry("950x650")
        
        # Info Header
        frame_info = ttk.LabelFrame(self.ventana, text="Estado del Servidor")
        frame_info.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(frame_info, text=f"IP Local: {self.host} | Puerto: {self.port}").pack(side=tk.LEFT, padx=10)
        self.estado_label = ttk.Label(frame_info, text="DETENIDO", foreground="red")
        self.estado_label.pack(side=tk.RIGHT, padx=10)
        
        # Botones ON/OFF
        frame_main_btns = ttk.Frame(self.ventana)
        frame_main_btns.pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(frame_main_btns, text="▶ INICIAR SERVIDOR", command=self.iniciar_servidor).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_main_btns, text="⏹ DETENER", command=self.detener_servidor).pack(side=tk.LEFT, padx=5)
        
        # Panel dividido
        paned = ttk.PanedWindow(self.ventana, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Izquierda: Lista y Log
        frame_left = ttk.Frame(paned)
        paned.add(frame_left, weight=1)
        
        ttk.Label(frame_left, text="Alumnos Conectados").pack(anchor=tk.W)
        self.lista_clientes = tk.Listbox(frame_left, height=12)
        self.lista_clientes.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(frame_left, text="Log de Eventos").pack(anchor=tk.W, pady=(10,0))
        self.log_area = scrolledtext.ScrolledText(frame_left, height=12)
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=2)

        # Chat (3.3)
        frame_chat = ttk.LabelFrame(frame_left, text="Chat General (3.3)")
        frame_chat.pack(fill=tk.X, padx=5, pady=5)
        self.chat_entry = ttk.Entry(frame_chat)
        self.chat_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)
        self.chat_entry.bind('<Return>', self.enviar_mensaje_chat_servidor)
        ttk.Button(frame_chat, text="Enviar", command=self.enviar_mensaje_chat_servidor).pack(side=tk.RIGHT, padx=5)
        
        # Derecha: Panel de Control por Puntos
        frame_right = ttk.LabelFrame(paned, text="Comandos")
        paned.add(frame_right, weight=1)
        
        # Visualización
        lbl_vis = ttk.LabelFrame(frame_right, text="Visualización y Pantalla")
        lbl_vis.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(lbl_vis, text="3.1 Ver Pantalla de Alumno", command=self.ver_pantalla_cliente).pack(fill=tk.X, padx=2, pady=2)
        ttk.Button(lbl_vis, text="3.4 Exhibir Alumno a Alumno", command=self.exhibir_cliente).pack(fill=tk.X, padx=2, pady=2)
        ttk.Button(lbl_vis, text="3.5 Mostrar SERVIDOR a Alumno", command=self.mostrar_servidor_a_cliente).pack(fill=tk.X, padx=2, pady=2)
        ttk.Button(lbl_vis, text="⏹ Detener Transmisiones", command=self.detener_transmision).pack(fill=tk.X, padx=2, pady=2)
        
        # Control Hard
        lbl_ctrl = ttk.LabelFrame(frame_right, text="Control Hardware")
        lbl_ctrl.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(lbl_ctrl, text="3.6 Bloquear Input", command=lambda: self.enviar_comando_simple("bloquear_input")).pack(fill=tk.X, padx=2, pady=2)
        ttk.Button(lbl_ctrl, text="3.7 Desbloquear Input", command=lambda: self.enviar_comando_simple("desbloquear_input")).pack(fill=tk.X, padx=2, pady=2)
        ttk.Button(lbl_ctrl, text="3.8 Apagar Remoto", command=self.confirmar_apagado).pack(fill=tk.X, padx=2, pady=2)
        
        # Red
        lbl_net = ttk.LabelFrame(frame_right, text="Red y Restricciones")
        lbl_net.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(lbl_net, text="3.9 Bloquear Web", command=self.bloquear_web_dialogo).pack(fill=tk.X, padx=2, pady=2)
        ttk.Button(lbl_net, text="3.9 Desbloquear Web", command=self.desbloquear_web_dialogo).pack(fill=tk.X, padx=2, pady=2)
        ttk.Button(lbl_net, text="3.10 Bloquear Ping", command=lambda: self.control_ping("bloquear")).pack(fill=tk.X, padx=2, pady=2)
        ttk.Button(lbl_net, text="3.10 Permitir Ping", command=lambda: self.control_ping("permitir")).pack(fill=tk.X, padx=2, pady=2)

        # Archivos
        lbl_trans = ttk.LabelFrame(frame_right, text="Archivos (3.2)")
        lbl_trans.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(lbl_trans, text="Enviar Archivo a Todos", command=self.enviar_archivo_dialogo).pack(fill=tk.X, padx=2, pady=2)
        
    def log(self, mensaje):
        self.log_area.insert(tk.END, f"{mensaje}\n")
        self.log_area.see(tk.END)
        
    def iniciar_servidor(self):
        try:
            self.socket_servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket_servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket_servidor.bind((self.host, self.port))
            self.socket_servidor.listen(5)
            
            self.estado_label.config(text="EJECUTANDO", foreground="green")
            self.log("✅ Servidor iniciado esperando conexiones...")
            threading.Thread(target=self.aceptar_conexiones, daemon=True).start()
        except Exception as e:
            self.log(f"❌ Error iniciando: {e}")
            
    def aceptar_conexiones(self):
        while True:
            try:
                if not self.socket_servidor: break
                client_sock, addr = self.socket_servidor.accept()
                
                # Recibir ID inicial
                data = client_sock.recv(4096).decode()
                info = json.loads(data)
                cid = info['id']
                
                # Guardar cliente
                self.clientes[cid] = {'socket': client_sock, 'direccion': addr, 'info': info}
                
                # Actualizar UI en hilo principal (simplificado aquí, Tk es thread-sensitive)
                self.actualizar_lista()
                self.log(f"🔗 Nuevo alumno: {cid} desde {addr[0]}")
                
                threading.Thread(target=self.manejar_cliente, args=(client_sock, cid), daemon=True).start()
            except:
                break
                
    def manejar_cliente(self, sock, cid):
        while True:
            try:
                data = sock.recv(1024*2048) # Buffer grande
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
        
        if tipo == 'chat': # 3.3
            self.log(f"💬 {origen}: {datos['contenido']}")
            # Reenviar a todos para chat grupal
            for cid in self.clientes:
                if cid != origen:
                    self.enviar_json(cid, {'tipo': 'chat_remoto', 'de': origen, 'contenido': datos['contenido']})
                    
        elif tipo == 'imagen_pantalla': # 3.1 y 3.4
            destino = datos.get('destino')
            if destino == 'servidor':
                self.actualizar_ventana_pantalla(origen, datos['contenido'])
            elif destino in self.clientes:
                self.enviar_json(destino, datos) # Reenviar imagen al alumno destino
                
        elif tipo == 'archivo': # 3.2
            # Reenviar archivo a todos los demás alumnos
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

    # --- Chat Servidor ---
    def enviar_mensaje_chat_servidor(self, event=None): # 3.3
        mensaje = self.chat_entry.get().strip()
        if mensaje:
            self.log(f"💬 Servidor: {mensaje}")
            for cid in self.clientes:
                self.enviar_json(cid, {'tipo': 'chat_remoto', 'de': 'Profesor', 'contenido': mensaje})
            self.chat_entry.delete(0, tk.END)

    # --- Lógica de Control ---
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

    # --- 3.1 Ver Pantalla ---
    def ver_pantalla_cliente(self):
        cid = self.get_cliente_seleccionado()
        if cid:
            self.enviar_json(cid, {'tipo': 'solicitar_pantalla', 'destino': 'servidor'})
            self.abrir_ventana_pantalla(cid)

    # --- 3.4 Exhibir ---
    def exhibir_cliente(self):
        origen = self.get_cliente_seleccionado()
        if not origen: return
        
        destino = simpledialog.askstring("Exhibir", f"¿A qué alumno mostrar la pantalla de {origen}?\n(Escribe el nombre exacto del otro alumno)")
        if destino and destino in self.clientes:
            self.enviar_json(origen, {'tipo': 'solicitar_pantalla', 'destino': destino})
            self.log(f"📺 Ordenando a {origen} transmitir a {destino}")
        else:
            self.log("❌ Alumno destino no encontrado")

    # --- 3.5 Mostrar Servidor a Alumno (IMPLEMENTADO) ---
    def mostrar_servidor_a_cliente(self):
        cid = self.get_cliente_seleccionado()
        if cid:
            self.compartiendo_servidor = True
            threading.Thread(target=self.hilo_transmitir_servidor, args=(cid,), daemon=True).start()
            self.log(f"📺 Transmitiendo MI pantalla a {cid}")

    def hilo_transmitir_servidor(self, destino):
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            while self.compartiendo_servidor and (destino in self.clientes):
                try:
                    sct_img = sct.grab(monitor)
                    img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                    img.thumbnail((800, 600))
                    
                    buffer = io.BytesIO()
                    img.save(buffer, format="JPEG", quality=40)
                    img_str = base64.b64encode(buffer.getvalue()).decode()
                    
                    self.enviar_json(destino, {
                        'tipo': 'imagen_pantalla',
                        'destino': 'cliente', # Indicamos que es para el cliente
                        'contenido': img_str
                    })
                    time.sleep(0.15)
                except Exception as e:
                    print(f"Error transmision servidor: {e}")
                    break
        self.log("Fin transmisión servidor")

    def detener_transmision(self):
        self.compartiendo_servidor = False
        cid = self.get_cliente_seleccionado()
        if cid:
            self.enviar_json(cid, {'tipo': 'detener_pantalla'})

    # --- 3.8, 3.9, 3.10 Comandos ---
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

    # --- 3.2 Archivos ---
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
            
            # Broadcast a todos
            for cid in self.clientes:
                self.enviar_json(cid, {'tipo': 'archivo', 'nombre': nombre, 'contenido': contenido})
            self.log(f"📂 Archivo enviado a todos: {nombre}")
        except Exception as e:
            self.log(f"Error archivo: {e}")

    # --- Gestión de Ventanas de Pantalla ---
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
        self.estado_label.config(text="DETENIDO", foreground="red")
        self.compartiendo_servidor = False
        sys.exit()

    def ejecutar(self):
        self.ventana.mainloop()

if __name__ == "__main__":
    servidor = Servidor()
    servidor.ejecutar()