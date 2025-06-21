import ssl
import socket
import os
import threading
import logging # Added

# Configure logger for this module
logger = logging.getLogger(__name__) # Added

# --- Development/Educational Purposes Only ---
# This is a basic SSL/TLS server requiring client certificate authentication.
# Assumes certificates are generated (e.g., using openssl) and placed in 'certs/'
# For production, use robust error handling, logging, and a proper application protocol.
# --- Development/Educational Purposes Only ---

CERT_DIR = os.path.join(os.path.dirname(__file__), 'certs')
SERVER_CERT = os.path.join(CERT_DIR, 'server.crt')
SERVER_KEY = os.path.join(CERT_DIR, 'server.key')
CLIENT_CA_CERT = os.path.join(CERT_DIR, 'ca.crt') # CA that signed the client certs
# CRL_FILE = os.path.join(CERT_DIR, 'ca.crl') # Placeholder for CRL file path

# --- Placeholder for Certificate Revocation Check ---
def is_certificate_revoked(client_cert: dict) -> bool:
    """
    Placeholder for checking if a client certificate has been revoked.
    In a real system, this would involve checking a Certificate Revocation List (CRL)
    or using Online Certificate Status Protocol (OCSP).

    Args:
        client_cert (dict): The client certificate dictionary (from conn.getpeercert()).

    Returns:
        bool: True if the certificate is considered revoked, False otherwise.
    """
    # For demonstration, we'll extract a serial number if available.
    # A real implementation would use the serial number to check against a CRL.
    serial_number = None
    if client_cert and 'serialNumber' in client_cert:
        serial_number = client_cert['serialNumber']

    logger.debug(f"Checking revocation status for cert (SN: {serial_number})... (Placeholder: always returns False)") # Changed

    # --- Actual Revocation Check Logic Would Go Here ---
    # Example with CRL (conceptual):
    # 1. Load the CRL file (e.g., using OpenSSL.crypto or cryptography.x509).
    #    crl = OpenSSL.crypto.load_crl(OpenSSL.crypto.FILETYPE_PEM, open(CRL_FILE).read())
    # 2. Get the list of revoked serial numbers.
    #    revoked_serials = [rev.get_serial() for rev in crl.get_revoked()]
    # 3. Check if client_cert's serial number is in revoked_serials.
    #    if serial_number and serial_number.lower() in [s.decode('ascii').lower() for s in revoked_serials]:
    #        logger.warning(f"Certificate with SN {serial_number} IS REVOKED.")
    #        return True
    # --- End Example ---

    # Placeholder: For this prototype, no certificates are considered revoked.
    return False
# --- End Placeholder ---

def handle_client_connection(conn, addr):
    logger.info(f"Accepted connection from {addr}") # Changed
    client_cert_subject = "N/A"
    try:
        client_cert = conn.getpeercert()
        if not client_cert:
            logger.warning(f"Client from {addr} did not provide a certificate.") # Changed
            conn.sendall(b"ERROR: Client certificate required.\n")
            return

        client_cert_subject = client_cert.get('subject', ((('commonName', 'N/A'),),))[0][0][1]
        logger.info(f"Client certificate subject: CN={client_cert_subject} from {addr}") # Changed
        logger.debug(f"Full client certificate details from {addr}: {client_cert}") # Changed


        # --- Perform Revocation Check ---
        if is_certificate_revoked(client_cert):
            logger.warning(f"Client certificate for CN={client_cert_subject} from {addr} is REVOKED. Closing connection.") # Changed
            conn.sendall(b"ERROR: Your certificate has been revoked.\n")
            return
        # --- End Revocation Check ---

        conn.sendall(b"Welcome! You are authenticated. Send data to echo.\n")
        while True:
            data = conn.recv(1024)
            if not data:
                logger.info(f"Connection closed by {addr} (CN={client_cert_subject})") # Changed
                break
            logger.info(f"Received from {addr} (CN={client_cert_subject}): {data.decode('utf-8').strip()}") # Changed
            conn.sendall(b"Server received: " + data)
    except ssl.SSLError as e:
        logger.error(f"SSL Error with {addr} (CN={client_cert_subject}): {e}", exc_info=True) # Changed
    except Exception as e:
        logger.exception(f"Error handling client {addr} (CN={client_cert_subject}): {e}") # Changed
    finally:
        conn.close()
        logger.info(f"Closed connection from {addr} (CN={client_cert_subject})") # Changed


def run_server(host='localhost', port=8443):
    # BasicConfig for logging if this script is run directly or if this function is the entry point.
    # Ensuring handler is set up before any logging.
    # Note: In __main__ is better if other module-level code might log before run_server()
    # if not logger.handlers and not logging.getLogger().handlers:
    #     logging.basicConfig(level=logging.INFO,
    #                         format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    #                         handlers=[logging.StreamHandler()])

    if not os.path.exists(CERT_DIR):
        os.makedirs(CERT_DIR)
        logger.info(f"Created placeholder directory: {CERT_DIR}") # Changed
        logger.info(f"Please generate certificates using openssl (see generate_certs.sh)") # Changed
        logger.info(f"and place them in {CERT_DIR} for the server to run correctly.") # Changed
        logger.info("Required: server.crt, server.key, ca.crt (for client auth)") # Changed
        if not os.path.exists(SERVER_CERT): open(SERVER_CERT, 'a').close()
        if not os.path.exists(SERVER_KEY): open(SERVER_KEY, 'a').close()
        if not os.path.exists(CLIENT_CA_CERT): open(CLIENT_CA_CERT, 'a').close()

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    try:
        context.load_cert_chain(certfile=SERVER_CERT, keyfile=SERVER_KEY)
        context.verify_mode = ssl.CERT_REQUIRED
        context.load_verify_locations(cafile=CLIENT_CA_CERT)

            # --- CRL Loading (Conceptual - Python's ssl module doesn't directly load CRLs for you) ---
            # Python's 'ssl' module itself does not have a direct context.load_crl() method.
            # CRL checking needs to be done manually after the handshake using the client_cert,
            # typically with a cryptography library (like PyOpenSSL or cryptography.io).
            # The `is_certificate_revoked` function is the place for such custom logic.
            # logger.info(f"Note: For CRL checking, ensure '{CRL_FILE}' is up-to-date if used by custom logic.")
            # --- End CRL Loading ---
        logger.info("Server SSL context configured to require client certificates.") # Changed

    except FileNotFoundError:
        logger.error(f"Certificate files not found. Please generate them (see generate_certs.sh).") # Changed
        logger.error(f"Looking for: \n - Server Cert: {SERVER_CERT}\n - Server Key: {SERVER_KEY}\n - Client CA: {CLIENT_CA_CERT}") # Changed
        return
    except ssl.SSLError as e:
        logger.error(f"SSL configuration error: {e}. Check certificate validity and paths.", exc_info=True) # Changed
        return

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, port))
        sock.listen(5)
        logger.info(f"SSL Server listening on {host}:{port}, requiring client certificates.") # Changed

        with context.wrap_socket(sock, server_side=True) as ssock:
            while True:
                try:
                    conn, addr = ssock.accept()
                    client_thread = threading.Thread(target=handle_client_connection, args=(conn, addr))
                    client_thread.daemon = True
                    client_thread.start()
                except ssl.SSLError as e:
                    logger.error(f"SSL handshake error: {e}", exc_info=True) # Changed
                except Exception as e:
                    logger.exception(f"Error accepting connection: {e}") # Changed
                    break
    logger.info("Server shutdown.") # Changed

if __name__ == "__main__":
    # Configure basicConfig here ensures it's set when script is run directly.
    if not logging.getLogger().handlers: # Check root logger to avoid duplicate handlers
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            handlers=[logging.StreamHandler()])

    logger.info("--- Basic SSL/TLS Server with Client Certificate Authentication (with Revocation Check Placeholder) ---") # Changed
    logger.info("This server requires client certificates signed by a CA (ca.crt).") # Changed
    logger.info(f"Ensure '{SERVER_CERT}', '{SERVER_KEY}', and '{CLIENT_CA_CERT}' are present.") # Changed
    logger.info("Certificate revocation check is a placeholder and will always pass.") # Changed
    run_server()
