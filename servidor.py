import socket
import threading
import os  # Necesario para manejar archivos y tamaños

# --- Constantes ---
HOST = '0.0.0.0'
PORT = 65432
BUFFER_SIZE = 4096  # Aumentamos el buffer para archivos (4KB)

def recibir_archivo(conn, filename, filesize):
    """ Función dedicada a recibir un archivo """
    print(f"Recibiendo {filename} de {filesize} bytes...")
    
    # Creamos un nombre de archivo seguro para evitar sobreescribir
    # (ej. "recibido_mi_archivo.txt")
    safe_filename = f"recibido_{os.path.basename(filename)}"
    
    bytes_recibidos = 0
    try:
        # Abrimos el archivo en modo "Write Binary" (wb)
        with open(safe_filename, 'wb') as f:
            while bytes_recibidos < filesize:
                # Calculamos cuánto falta, para no recibir de más
                bytes_por_leer = min(BUFFER_SIZE, filesize - bytes_recibidos)
                
                data = conn.recv(bytes_por_leer)
                if not data:
                    print("Error: El cliente se desconectó antes de terminar.")
                    break
                
                f.write(data)
                bytes_recibidos += len(data)

        if bytes_recibidos == filesize:
            print(f"✅ Archivo {safe_filename} recibido con éxito.")
            conn.send("OK: Archivo recibido".encode('utf-8'))
        else:
            print("Error: No se recibió el archivo completo.")
            
    except Exception as e:
        print(f"Error al recibir archivo: {e}")
        conn.send(f"ERROR: {e}".encode('utf-8'))


def manejar_cliente(conn, addr):
    print(f"✅ [NUEVA CONEXIÓN] {addr} conectado.")
    
    try:
        conn.send("¡Bienvenido al servidor! Escribe 'adios' para salir.".encode('utf-8'))

        while True:
            # Recibimos datos (ahora 4096 bytes)
            data = conn.recv(BUFFER_SIZE)
            if not data:
                break
                
            mensaje = data.decode('utf-8')
            
            # --- NUEVA LÓGICA DE COMANDOS ---
            if mensaje.startswith('enviar_archivo'):
                try:
                    # El comando debe ser: "enviar_archivo::nombre.txt::12345"
                    partes = mensaje.split('::')
                    filename = partes[1]
                    filesize = int(partes[2])
                    
                    # Avisamos al cliente que estamos listos
                    conn.send("OK_LISTO".encode('utf-Tf-8'))
                    
                    # Llamamos a la función que recibe el archivo
                    recibir_archivo(conn, filename, filesize)
                    
                except Exception as e:
                    print(f"Error al procesar comando de archivo: {e}")
                    conn.send("ERROR: Comando inválido".encode('utf-8'))

            # --- LÓGICA DE CHAT (como antes) ---
            elif mensaje.strip().lower() == 'adios':
                break
            else:
                print(f"[{addr}] dice: {mensaje}")
                conn.send(f"Eco: {mensaje}".encode('utf-8'))
            
    except ConnectionResetError:
        print(f"⚠️ [CONEXIÓN PERDIDA] {addr} se desconectó abruptamente.")
    except UnicodeDecodeError:
        # Esto pasará si recibimos datos que no son texto (como un archivo)
        # por error. Lo ignoramos para que no se caiga el servidor.
        print(f"[{addr}] envió datos binarios (no texto).")
    finally:
        print(f"🛑 [CONEXIÓN CERRADA] {addr}.")
        conn.close()

# --- Configuración Principal del Servidor (Sin cambios) ---
servidor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
servidor_socket.bind((HOST, PORT))
servidor_socket.listen()
print(f"🚀 Servidor escuchando en {HOST}:{PORT}")

while True:
    conn, addr = servidor_socket.accept()
    thread = threading.Thread(target=manejar_cliente, args=(conn, addr))
    thread.start()