import tenseal as ts
from .key_management import create_and_store_tenseal_context, load_tenseal_context_from_vault, get_vault_instance
import logging # Added

# Configure logger for this module
logger = logging.getLogger(__name__) # Added

# --- Development/Educational Purposes Only ---
# This script demonstrates a simple privacy-preserving sum application
# using Homomorphic Encryption (HE) with TenSEAL.
# It utilizes the simulated SecureKeyVault for context management.
# --- Development/Educational Purposes Only ---

# Application-specific constants
APP_CONTEXT_NAME = "privacy_preserving_sum_app"
VAULT_MASTER_PASSWORD = "app_super_secret_password123" # For this application's vault access

def initialize_he_environment_for_app():
    """
    Initializes the HE context for the application if it doesn't exist in the vault.
    This would typically be done by an administrator or a trusted setup process.
    """
    try:
        # Attempt to load to see if it exists; if not, create it.
        # We need the secret key part to ensure all keys are generated and stored.
        load_tenseal_context_from_vault(
            vault_master_password=VAULT_MASTER_PASSWORD,
            context_name=APP_CONTEXT_NAME,
            load_secret_key=True
        )
        logger.info(f"HE context '{APP_CONTEXT_NAME}' already exists in the vault.") # Changed
    except FileNotFoundError:
        logger.info(f"HE context '{APP_CONTEXT_NAME}' not found. Creating and storing it now.") # Changed
        create_and_store_tenseal_context(
            vault_master_password=VAULT_MASTER_PASSWORD,
            context_name=APP_CONTEXT_NAME,
            scheme=ts.SCHEME_TYPE.BFV, # BFV is suitable for integer sums
            poly_modulus_degree=8192,
            plain_modulus=1032193, # A prime suitable for sums without overflowing easily
            generate_galois=True, # Needed for some vector operations, good to have
            generate_relin=True,  # Needed for reducing noise after multiplications (not strictly for sum, but good practice)
            store_public_separately=True
        )
        logger.info(f"HE context '{APP_CONTEXT_NAME}' created and stored in vault.") # Changed
    except Exception as e:
        logger.exception(f"Error during HE environment initialization for app: {e}") # Changed
        raise

class Client:
    def __init__(self, vault_password: str, context_name: str):
        self.vault_password = vault_password
        self.context_name = context_name
        # Client loads the public context for encryption
        self.public_context = load_tenseal_context_from_vault(
            self.vault_password, self.context_name, load_secret_key=False
        )
        # Client also needs access to the secret key for decryption.
        # In a real scenario, the secret key might be held by the client securely
        # or by a trusted third party. Here, we load the full context for decryption.
        self.secret_context = load_tenseal_context_from_vault(
            self.vault_password, self.context_name, load_secret_key=True
        )
        logger.info("Client initialized with public (for encryption) and secret (for decryption) contexts.") # Changed

    def encrypt_numbers(self, numbers: list) -> ts.BFVVector:
        if not self.public_context:
            logger.error("Client's public HE context not loaded for encryption.") # Changed
            raise ValueError("Client's public HE context not loaded.")
        logger.info(f"Client encrypting numbers: {numbers}") # Changed
        encrypted_vector = ts.bfv_vector(self.public_context, numbers)
        return encrypted_vector

    def decrypt_result(self, encrypted_result: ts.BFVVector) -> list:
        if not self.secret_context:
            logger.error("Client's secret HE context not loaded for decryption.") # Changed
            raise ValueError("Client's secret HE context not loaded for decryption.")
        logger.info("Client decrypting result...") # Changed
        decrypted_vector = encrypted_result.decrypt(self.secret_context)
        return decrypted_vector

class Server: # Or "Computation Service"
    def __init__(self, vault_password: str, context_name: str):
        self.vault_password = vault_password
        self.context_name = context_name
        # Server loads the public context which should contain relin/galois keys
        # if they were generated and stored with the public part.
        # For BFV addition of vectors, only the public key part of the context is strictly needed.
        # Relinearization keys are for multiplications. Galois keys for rotations.
        self.compute_context = load_tenseal_context_from_vault(
            self.vault_password, self.context_name, load_secret_key=False
        )
        # If server needed to generate new keys or decrypt (which it shouldn't for this example),
        # it would need the secret_key=True version, but that violates privacy.
        logger.info("Server (Computation Service) initialized with public HE context for computation.") # Changed

    def homomorphic_sum_vectors(self, encrypted_vectors: list) -> ts.BFVVector:
        if not self.compute_context:
            logger.error("Server's HE context not loaded for computation.") # Changed
            raise ValueError("Server's HE context not loaded for computation.")
        if not encrypted_vectors:
            logger.error("No encrypted vectors provided to sum.") # Changed
            raise ValueError("No encrypted vectors provided to sum.")

        logger.info("Server performing homomorphic sum...") # Changed
        # Ensure all vectors are compatible with the server's context if they came from different clients
        # (though here they come from one client using the same context parameters)

        # Initialize sum with the first encrypted vector
        current_sum_encrypted = encrypted_vectors[0]

        # Add subsequent encrypted vectors
        for i in range(1, len(encrypted_vectors)):
            current_sum_encrypted += encrypted_vectors[i]
            logger.info(f"Server: Added vector {i+1} to sum.") # Changed

        return current_sum_encrypted

def run_privacy_preserving_sum_example():
    logger.info("### Running Privacy-Preserving Sum Application Example ###") # Changed

    # 0. Ensure HE environment (keys/context in vault) is set up
    try:
        initialize_he_environment_for_app()
    except Exception as e:
        logger.exception(f"Failed to initialize HE environment: {e}. Aborting example.") # Changed
        return

    # 1. Client Side: Prepare and encrypt data
    logger.info("\n--- Client Operations ---") # Changed
    client = Client(vault_password=VAULT_MASTER_PASSWORD, context_name=APP_CONTEXT_NAME)

    data_set1 = [10, 20, 30, 40, 50]
    data_set2 = [5, 15, 25, 35, 45]
    # (For BFV, vectors should be of the same size for element-wise operations like sum here)

    encrypted_data1 = client.encrypt_numbers(data_set1)
    encrypted_data2 = client.encrypt_numbers(data_set2)

    logger.info(f"Client: Data Set 1 ({data_set1}) encrypted.") # Changed
    logger.info(f"Client: Data Set 2 ({data_set2}) encrypted.") # Changed

    # Data is now sent to the server (conceptually)
    # For this example, we'll just pass the encrypted objects.

    # 2. Server Side: Perform homomorphic computation
    logger.info("\n--- Server Operations ---") # Changed
    server = Server(vault_password=VAULT_MASTER_PASSWORD, context_name=APP_CONTEXT_NAME)

    # Server receives a list of encrypted vectors
    received_encrypted_vectors = [encrypted_data1, encrypted_data2]

    homomorphic_result = server.homomorphic_sum_vectors(received_encrypted_vectors)
    logger.info("Server: Homomorphic summation completed.") # Changed

    # Result is now sent back to the client (conceptually)

    # 3. Client Side: Decrypt the result
    logger.info("\n--- Client Operations (Decryption) ---") # Changed
    decrypted_sum_result = client.decrypt_result(homomorphic_result)
    logger.info(f"Client: Decrypted sum result: {decrypted_sum_result}") # Changed

    # 4. Verification (non-HE, for correctness check)
    expected_sum = [d1 + d2 for d1, d2 in zip(data_set1, data_set2)]
    logger.info(f"Expected sum (plaintext): {expected_sum}") # Changed

    if decrypted_sum_result == expected_sum:
        logger.info("SUCCESS: The decrypted homomorphic sum matches the expected plaintext sum!") # Changed
    else:
        logger.error("FAILURE: Decrypted sum does NOT match expected sum.") # Changed
        logger.error(f"Got: {decrypted_sum_result}, Expected: {expected_sum}") # Changed

    logger.info("\nPrivacy-preserving sum application example finished.") # Changed


if __name__ == "__main__":
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            handlers=[logging.StreamHandler()])
    logger.info("Starting he_application.py example...") # Changed
    # Ensure the vault is clean for this specific app context if run multiple times in one session
    # This is a bit of a hack for example purity; real vault wouldn't be cleared like this.
    try:
        vault = get_vault_instance(VAULT_MASTER_PASSWORD)
        if vault.context_exists(f"{APP_CONTEXT_NAME}_secret", VAULT_MASTER_PASSWORD):
            del vault._keys_storage[f"{APP_CONTEXT_NAME}_secret"]
            logger.debug(f"Cleared {APP_CONTEXT_NAME}_secret from vault for example run.") # Changed
        if vault.context_exists(f"{APP_CONTEXT_NAME}_public", VAULT_MASTER_PASSWORD):
            del vault._keys_storage[f"{APP_CONTEXT_NAME}_public"]
            logger.debug(f"Cleared {APP_CONTEXT_NAME}_public from vault for example run.") # Changed
    except Exception as e:
        logger.debug(f"Vault not yet initialized or other issue during pre-example cleanup: {e}", exc_info=True) # Changed
        pass

    run_privacy_preserving_sum_example()
