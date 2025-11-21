import socket
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, simpledialog, Toplevel, Label
import json
import base64
import io
from PIL import Image, ImageTk

class Servidor:
    def __init__(self):
        self.host = self.obtener_ip_local()
        self.port = 5000
        self.clientes = {}  # {cliente_id: {'socket': socket, 'direccion': addr, 'info': info}}
        self.socket_servidor = None
        self.ventanas_pantalla = {} # {cliente_id: window_object}
        
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
        self.ventana.title("Servidor de Control Remoto - Maestro")
        self.ventana.geometry("900x600")
        
        # Información
        frame_info = ttk.LabelFrame(self.ventana, text="Estado del Servidor")
        frame_info.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(frame_info, text=f"IP: {self.host} | Puerto: {self.port}").pack(side=tk.LEFT, padx=10)
        self.estado_label = ttk.Label(frame_info, text="DETENIDO", foreground="red")
        self.estado_label.pack(side=tk.RIGHT, padx=10)
        
        # Botones principales
        frame_main_btns = ttk.Frame(self.ventana)
        frame_main_btns.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(frame_main_btns, text="Iniciar Servidor", command=self.iniciar_servidor).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_main_btns, text="Detener", command=self.detener_servidor).pack(side=tk.LEFT, padx=5)
        
        # Área principal dividida
        paned = ttk.PanedWindow(self.ventana, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Panel Izquierdo: Clientes y Log
        frame_left = ttk.Frame(paned)
        paned.add(frame_left, weight=1)
        
        # Lista de clientes
        ttk.Label(frame_left, text="Clientes Conectados").pack(anchor=tk.W)
        self.lista_clientes = tk.Listbox(frame_left, height=10)
        self.lista_clientes.pack(fill=tk.X, padx=5, pady=2)
        
        # Log
        ttk.Label(frame_left, text="Log de Eventos").pack(anchor=tk.W, pady=(10,0))
        self.log_area = scrolledtext.ScrolledText(frame_left, height=10)
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=2)
        
        # Panel Derecho: Controles
        frame_right = ttk.LabelFrame(paned, text="Panel de Control")
        paned.add(frame_right, weight=1)
        
        # Grupo 1: Visualización
        lbl_vis = ttk.LabelFrame(frame_right, text="Visualización (3.1, 3.4, 3.5)")
        lbl_vis.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(lbl_vis, text="Ver Pantalla Cliente (3.1)", command=self.ver_pantalla_cliente).pack(fill=tk.X, padx=2, pady=2)
        ttk.Button(lbl_vis, text="Exhibir Cliente a Cliente (3.4)", command=self.exhibir_cliente).pack(fill=tk.X, padx=2, pady=2)
        ttk.Button(lbl_vis, text="Mostrar Servidor a Cliente (3.5)", command=self.mostrar_servidor).pack(fill=tk.X, padx=2, pady=2)
        ttk.Button(lbl_vis, text="Detener Transmisión", command=self.detener_transmision).pack(fill=tk.X, padx=2, pady=2)
        
        # Grupo 2: Control
        lbl_ctrl = ttk.LabelFrame(frame_right, text="Control Remoto (3.6 - 3.8)")
        lbl_ctrl.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(lbl_ctrl, text="Bloquear Input (3.6)", command=lambda: self.enviar_comando_simple("bloquear_input")).pack(fill=tk.X, padx=2, pady=2)
        ttk.Button(lbl_ctrl, text="Desbloquear Input (3.7)", command=lambda: self.enviar_comando_simple("desbloquear_input")).pack(fill=tk.X, padx=2, pady=2)
        ttk.Button(lbl_ctrl, text="Apagar Remoto (3.8)", command=self.confirmar_apagado).pack(fill=tk.X, padx=2, pady=2)
        
        # Grupo 3: Red y Sistema
        lbl_net = ttk.LabelFrame(frame_right, text="Red y Restricciones (3.9, 3.10)")
        lbl_net.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(lbl_net, text="Bloquear Web (3.9)", command=self.bloquear_web_dialogo).pack(fill=tk.X, padx=2, pady=2)
        ttk.Button(lbl_net, text="Bloquear Ping (3.10)", command=lambda: self.control_ping("bloquear")).pack(fill=tk.X, padx=2, pady=2)
        ttk.Button(lbl_net, text="Permitir Ping (3.10)", command=lambda: self.control_ping("permitir")).pack(fill=tk.X, padx=2, pady=2)
        
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
            self.log("✅ Servidor iniciado")
            threading.Thread(target=self.aceptar_conexiones, daemon=True).start()
        except Exception as e:
            self.log(f"❌ Error: {e}")
            
    def aceptar_conexiones(self):
        while True:
            try:
                if not self.socket_servidor: break
                client_sock, addr = self.socket_servidor.accept()
                
                # Recibir ID
                data = client_sock.recv(1024).decode()
                info = json.loads(data)
                cid = info['id']
                
                self.clientes[cid] = {'socket': client_sock, 'direccion': addr, 'info': info}
                self.actualizar_lista()
                self.log(f"🔗 Conectado: {cid} ({addr[0]})")
                
                threading.Thread(target=self.manejar_cliente, args=(client_sock, cid), daemon=True).start()
            except:
                break
                
    def manejar_cliente(self, sock, cid):
        buffer = ""
        while True:
            try:
                # Buffer grande para imágenes
                data = sock.recv(1024*1024)
                if not data: break
                
                mensaje = data.decode('utf-8', errors='ignore')
                
                try:
                    # Intento simple de parseo
                    # En producción se requiere mejor framing
                    if mensaje.startswith('{') and mensaje.endswith('}'):
                        datos = json.loads(mensaje)
                        self.procesar_mensaje(datos, cid)
                    else:
                        # Podría ser parte de un stream o múltiples mensajes
                        pass
                except:
                    pass
                    
            except:
                break
                
        if cid in self.clientes:
            del self.clientes[cid]
            self.actualizar_lista()
            self.log(f"❌ Desconectado: {cid}")
            
    def procesar_mensaje(self, datos, origen):
        tipo = datos.get('tipo')
        
        if tipo == 'chat':
            self.log(f"💬 {origen}: {datos['contenido']}")
            # Broadcast
            for cid, info in self.clientes.items():
                if cid != origen:
                    self.enviar_json(cid, {'tipo': 'chat_remoto', 'de': origen, 'contenido': datos['contenido']})
                    
        elif tipo == 'imagen_pantalla':
            destino = datos.get('destino')
            if destino == 'servidor':
                self.actualizar_ventana_pantalla(origen, datos['contenido'])
            elif destino in self.clientes:
                # Reenviar a otro cliente
                self.enviar_json(destino, datos)
                
        elif tipo == 'archivo':
            # Reenviar a todos los demás (broadcast simple para 3.2)
            for cid, info in self.clientes.items():
                if cid != origen:
                    self.enviar_json(cid, datos)
                    
    def enviar_json(self, cid, datos):
        try:
            if cid in self.clientes:
                msg = json.dumps(datos)
                self.clientes[cid]['socket'].send(msg.encode())
        except Exception as e:
            self.log(f"❌ Error enviando a {cid}: {e}")

    # --- Comandos de Control ---
    def get_cliente_seleccionado(self):
        sel = self.lista_clientes.curselection()
        if not sel:
            self.log("⚠️ Selecciona un cliente primero")
            return None
        return self.lista_clientes.get(sel[0])

    def enviar_comando_simple(self, tipo_comando, extra_data=None):
        cid = self.get_cliente_seleccionado()
        if cid:
            payload = {'tipo': tipo_comando}
            if extra_data:
                payload.update(extra_data)
            self.enviar_json(cid, payload)
            self.log(f"📤 Comando {tipo_comando} enviado a {cid}")

    def ver_pantalla_cliente(self):
        cid = self.get_cliente_seleccionado()
        if cid:
            self.enviar_json(cid, {'tipo': 'solicitar_pantalla', 'destino': 'servidor'})
            self.abrir_ventana_pantalla(cid)

    def exhibir_cliente(self):
        origen = self.get_cliente_seleccionado()
        if not origen: return
        
        destino = simpledialog.askstring("Exhibir", f"Escribe el nombre del cliente que verá a {origen}:")
        if destino and destino in self.clientes:
            self.enviar_json(origen, {'tipo': 'solicitar_pantalla', 'destino': destino})
            self.log(f"📺 Solicitando a {origen} que transmita a {destino}")
        else:
            self.log("❌ Cliente destino no encontrado")

    def mostrar_servidor(self):
        # 3.5 Mostrar lo que hace el servidor
        # Esto requeriría que el servidor también capture su pantalla
        # Por simplicidad, enviamos un mensaje de que no implementado o implementamos captura local
        self.log("⚠️ Funcionalidad Servidor -> Cliente pendiente de implementación completa (requiere mss en servidor)")
        # Se puede implementar igual que en el cliente

    def detener_transmision(self):
        cid = self.get_cliente_seleccionado()
        if cid:
            self.enviar_json(cid, {'tipo': 'detener_pantalla'})

    def confirmar_apagado(self):
        if tk.messagebox.askyesno("Confirmar", "¿Seguro que quieres apagar el equipo remoto?"):
            self.enviar_comando_simple("apagar_pc")

    def bloquear_web_dialogo(self):
        url = simpledialog.askstring("Bloquear Web", "URL a bloquear (ej: www.facebook.com):")
        if url:
            self.enviar_comando_simple("bloquear_web", {'url': url})

    def control_ping(self, accion):
        self.enviar_comando_simple("control_ping", {'accion': accion})

    # --- Manejo de Ventanas de Pantalla ---
    def abrir_ventana_pantalla(self, cid):
        if cid in self.ventanas_pantalla:
            return # Ya abierta
            
        top = Toplevel(self.ventana)
        top.title(f"Pantalla de {cid}")
        top.geometry("800x600")
        
        lbl = Label(top)
        lbl.pack(fill=tk.BOTH, expand=True)
        
        self.ventanas_pantalla[cid] = {'window': top, 'label': lbl}
        
        def on_close():
            self.enviar_json(cid, {'tipo': 'detener_pantalla'})
            del self.ventanas_pantalla[cid]
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
                lbl.image = photo # Mantener referencia
            except Exception as e:
                print(f"Error imagen: {e}")

    def actualizar_lista(self):
        self.lista_clientes.delete(0, tk.END)
        for cid in self.clientes:
            self.lista_clientes.insert(tk.END, cid)
            
    def detener_servidor(self):
        if self.socket_servidor:
            self.socket_servidor.close()
            self.socket_servidor = None
        self.estado_label.config(text="DETENIDO", foreground="red")
        self.log("🛑 Servidor detenido")

    def ejecutar(self):
        self.ventana.mainloop()

if __name__ == "__main__":
    servidor = Servidor()
    servidor.ejecutar()