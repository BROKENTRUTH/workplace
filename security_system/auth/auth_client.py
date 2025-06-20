import ssl
import socket
import os

# --- Development/Educational Purposes Only ---
# This is a basic SSL/TLS client that presents a client certificate.
# Assumes certificates are generated and placed in 'certs/'
# For production, use robust error handling and proper application logic.
# --- Development/Educational Purposes Only ---

CERT_DIR = os.path.join(os.path.dirname(__file__), 'certs')
CLIENT_CERT = os.path.join(CERT_DIR, 'client.crt')
CLIENT_KEY = os.path.join(CERT_DIR, 'client.key')
SERVER_CA_CERT = os.path.join(CERT_DIR, 'ca.crt') # CA that signed the server cert

def run_client(host='localhost', port=8443):
    # Create a placeholder certs directory if it doesn't exist
    if not os.path.exists(CERT_DIR):
        os.makedirs(CERT_DIR)
        print(f"Created placeholder directory: {CERT_DIR}")
        print(f"Please generate certificates using openssl (see generate_certs.sh)")
        print(f"and place them in {CERT_DIR} for the client to run correctly.")
        print("Required: client.crt, client.key, ca.crt (to verify server)")
        # Create dummy files to allow client to start, though it won't function for auth
        if not os.path.exists(CLIENT_CERT): open(CLIENT_CERT, 'a').close()
        if not os.path.exists(CLIENT_KEY): open(CLIENT_KEY, 'a').close()
        if not os.path.exists(SERVER_CA_CERT): open(SERVER_CA_CERT, 'a').close()

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    try:
        # Load client's certificate and private key
        context.load_cert_chain(certfile=CLIENT_CERT, keyfile=CLIENT_KEY)
        # Load CA certificate to verify the server
        context.load_verify_locations(cafile=SERVER_CA_CERT)
        context.check_hostname = True # Recommended for server cert validation
        context.verify_mode = ssl.CERT_REQUIRED
        print("Client SSL context configured to present client certificate and verify server.")
    except FileNotFoundError:
        print("ERROR: Certificate files not found. Please generate them (see generate_certs.sh).")
        print(f"Looking for: \n - Client Cert: {CLIENT_CERT}\n - Client Key: {CLIENT_KEY}\n - Server CA: {SERVER_CA_CERT}")
        return
    except ssl.SSLError as e:
        print(f"ERROR: SSL configuration error: {e}. Check certificate validity and paths.")
        return

    # For testing with self-signed server cert where hostname might be 'localhost'
    # but CN in cert might be different, or if not using DNS resolvable names for server.
    # In production, ensure server_hostname matches the CN or SAN in server's certificate.
    # context.check_hostname = False
    # context.verify_mode = ssl.CERT_NONE # DANGEROUS: Disables server cert validation

    try:
        with socket.create_connection((host, port)) as sock:
            with context.wrap_socket(sock, server_side=False, server_hostname=host) as ssock:
                print(f"Connected securely to {host}:{port}")
                server_cert = ssock.getpeercert()
                print(f"Server certificate: {server_cert.get('subject', 'N/A')}")

                # Receive welcome message
                welcome_msg = ssock.recv(1024)
                print(f"Server says: {welcome_msg.decode('utf-8').strip()}")

                # Send some data
                for i in range(3):
                    message = f"Hello from client, message {i+1}"
                    print(f"Sending: {message}")
                    ssock.sendall(message.encode('utf-8'))
                    response = ssock.recv(1024)
                    print(f"Server echoed: {response.decode('utf-8').strip()}\n")
                    # socket.timeout(1) # Dummy delay - corrected from original, timeout is a method on socket object, not socket module

        except ConnectionRefusedError:
            print(f"ERROR: Connection refused. Is the server running at {host}:{port}?")
        except ssl.SSLCertVerificationError as e:
            print(f"ERROR: Server certificate verification failed: {e}")
            print("Ensure the server's certificate is signed by the CA specified in ca.crt (for client) or that you trust the self-signed server cert.")
        except ssl.SSLError as e:
            # This can happen if server rejects client cert, or other TLS issues
            print(f"ERROR: SSL communication error: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
        finally:
            print("Client finished.")


if __name__ == "__main__":
    print("--- Basic SSL/TLS Client with Client Certificate Authentication ---")
    print(f"This client presents '{CLIENT_CERT}' and '{CLIENT_KEY}'.")
    print(f"It verifies the server against '{SERVER_CA_CERT}'.")
    run_client()
