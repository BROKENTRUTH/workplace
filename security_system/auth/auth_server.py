import ssl
import socket
import os
import threading

# --- Development/Educational Purposes Only ---
# This is a basic SSL/TLS server requiring client certificate authentication.
# Assumes certificates are generated (e.g., using openssl) and placed in 'certs/'
# For production, use robust error handling, logging, and a proper application protocol.
# --- Development/Educational Purposes Only ---

CERT_DIR = os.path.join(os.path.dirname(__file__), 'certs')
SERVER_CERT = os.path.join(CERT_DIR, 'server.crt')
SERVER_KEY = os.path.join(CERT_DIR, 'server.key')
CLIENT_CA_CERT = os.path.join(CERT_DIR, 'ca.crt') # CA that signed the client certs

def handle_client_connection(conn, addr):
    print(f"Accepted connection from {addr}")
    try:
        # Get client certificate information
        client_cert = conn.getpeercert()
        if not client_cert:
            print("Client did not provide a certificate.")
            conn.sendall(b"ERROR: Client certificate required.\n")
            return

        print(f"Client certificate: {client_cert.get('subject', 'N/A')}")

        # Echo server
        conn.sendall(b"Welcome! You are authenticated. Send data to echo.\n")
        while True:
            data = conn.recv(1024)
            if not data:
                print(f"Connection closed by {addr}")
                break
            print(f"Received from {addr}: {data.decode('utf-8').strip()}")
            conn.sendall(b"Server received: " + data)
    except ssl.SSLError as e:
        print(f"SSL Error with {addr}: {e}")
    except Exception as e:
        print(f"Error handling client {addr}: {e}")
    finally:
        conn.close()
        print(f"Closed connection from {addr}")


def run_server(host='localhost', port=8443):
    # Create a placeholder certs directory if it doesn't exist
    # In a real scenario, certs would be provisioned here.
    if not os.path.exists(CERT_DIR):
        os.makedirs(CERT_DIR)
        print(f"Created placeholder directory: {CERT_DIR}")
        print(f"Please generate certificates using openssl (see generate_certs.sh)")
        print(f"and place them in {CERT_DIR} for the server to run correctly.")
        print("Required: server.crt, server.key, ca.crt (for client auth)")
        # Create dummy files to allow server to start, though it won't function for auth
        if not os.path.exists(SERVER_CERT): open(SERVER_CERT, 'a').close()
        if not os.path.exists(SERVER_KEY): open(SERVER_KEY, 'a').close()
        if not os.path.exists(CLIENT_CA_CERT): open(CLIENT_CA_CERT, 'a').close()


    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    try:
        context.load_cert_chain(certfile=SERVER_CERT, keyfile=SERVER_KEY)
        # Require client certificate and verify it against our CA
        context.verify_mode = ssl.CERT_REQUIRED
        context.load_verify_locations(cafile=CLIENT_CA_CERT)
        print("Server SSL context configured to require client certificates.")
    except FileNotFoundError:
        print("ERROR: Certificate files not found. Please generate them (see generate_certs.sh).")
        print(f"Looking for: \n - Server Cert: {SERVER_CERT}\n - Server Key: {SERVER_KEY}\n - Client CA: {CLIENT_CA_CERT}")
        return
    except ssl.SSLError as e:
        print(f"ERROR: SSL configuration error: {e}. Check certificate validity and paths.")
        return


    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, port))
        sock.listen(5)
        print(f"SSL Server listening on {host}:{port}, requiring client certificates.")

        with context.wrap_socket(sock, server_side=True) as ssock:
            while True:
                try:
                    conn, addr = ssock.accept()
                    # You might want to use a thread pool for many clients
                    client_thread = threading.Thread(target=handle_client_connection, args=(conn, addr))
                    client_thread.daemon = True # Allow main program to exit even if threads are running
                    client_thread.start()
                except ssl.SSLError as e:
                    # This can happen if client cert is invalid or not provided during handshake
                    print(f"SSL handshake error: {e}")
                except Exception as e:
                    print(f"Error accepting connection: {e}")
                    break # Or continue, depending on desired robustness
    print("Server shutdown.")

if __name__ == "__main__":
    print("--- Basic SSL/TLS Server with Client Certificate Authentication ---")
    print("This server requires client certificates signed by a CA (ca.crt).")
    print(f"Ensure '{SERVER_CERT}', '{SERVER_KEY}', and '{CLIENT_CA_CERT}' are present.")
    run_server()
