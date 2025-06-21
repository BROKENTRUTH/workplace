import tenseal as ts
import os # Keep for potential future path operations if needed, but not for direct key saving
import logging # Added

# Configure logger for this module
logger = logging.getLogger(__name__) # Added

# --- Development/Educational Purposes Only ---
# WARNING: The SecureKeyVault below is a SIMULATION.
# It stores keys in memory and uses a conceptual master password.
# This is NOT a substitute for a real Hardware Security Module (HSM)
# or a dedicated Key Management System (KMS) like HashiCorp Vault,
# AWS KMS, Azure Key Vault, or Google Cloud KMS.
# Real KMS solutions provide robust hardware/software security, access control,
# audit logging, and key lifecycle management.
# --- Development/Educational Purposes Only ---

_vault_instance = None # Singleton pattern for the vault

class SecureKeyVault:
    def __init__(self, master_password: str):
        # In a real system, this password would be handled very carefully,
        # possibly derived, and used to unlock access to a protected store.
        # Here, it's just a conceptual barrier.
        if not master_password: # Simplified check
            logger.error("Master password cannot be empty for the vault.") # Changed
            raise ValueError("Master password cannot be empty for the vault.")
        self._master_password_hash = hash(master_password) # Simulate storing a hash
        self._keys_storage = {} # In-memory dictionary to store serialized context data
        self._is_unlocked = True # Simplified: unlocked upon instantiation with password
        logger.info("SecureKeyVault initialized (SIMULATED).") # Changed

    def _authenticate(self, master_password_attempt: str):
        # Conceptual authentication
        if not self._is_unlocked: # Or if it were locked due to inactivity
            logger.warning("Vault access attempted while locked.") # Changed
            raise PermissionError("Vault is locked.")
        if hash(master_password_attempt) != self._master_password_hash:
            logger.warning("Invalid master password for vault access.") # Changed
            raise PermissionError("Invalid master password for vault access.")
        return True

    def store_context_data(self, context_name: str, context_data: bytes, master_password_attempt: str):
        self._authenticate(master_password_attempt)
        if not isinstance(context_data, bytes):
            logger.error(f"Context data for '{context_name}' must be bytes, got {type(context_data)}.") # Changed
            raise TypeError("Context data must be bytes.")
        self._keys_storage[context_name] = context_data
        logger.info(f"Context '{context_name}' stored in SecureKeyVault (SIMULATED).") # Changed

    def retrieve_context_data(self, context_name: str, master_password_attempt: str) -> bytes:
        self._authenticate(master_password_attempt)
        if context_name not in self._keys_storage:
            logger.warning(f"Context '{context_name}' not found in SecureKeyVault.") # Changed
            raise FileNotFoundError(f"Context '{context_name}' not found in SecureKeyVault.")
        logger.info(f"Context '{context_name}' retrieved from SecureKeyVault (SIMULATED).") # Changed
        return self._keys_storage[context_name]

    def context_exists(self, context_name: str, master_password_attempt: str) -> bool:
        self._authenticate(master_password_attempt)
        return context_name in self._keys_storage

    def lock_vault(self):
        # Conceptual lock, would require re-auth
        self._is_unlocked = False
        logger.info("SecureKeyVault locked (SIMULATED).") # Changed

    def unlock_vault(self, master_password_attempt: str):
        if hash(master_password_attempt) == self._master_password_hash:
            self._is_unlocked = True
            logger.info("SecureKeyVault unlocked (SIMULATED).") # Changed
        else:
            logger.warning("Invalid master password for unlocking vault.") # Changed
            raise PermissionError("Invalid master password for unlocking vault.")


def get_vault_instance(master_password: str) -> SecureKeyVault:
    global _vault_instance
    if _vault_instance is None:
        _vault_instance = SecureKeyVault(master_password)
    return _vault_instance


def create_and_store_tenseal_context(
    vault_master_password: str,
    context_name: str,
    scheme: ts.SCHEME_TYPE = ts.SCHEME_TYPE.BFV,
    poly_modulus_degree: int = 8192,
    plain_modulus: int = 1032193,
    generate_galois: bool = True,
    generate_relin: bool = True,
    store_public_separately: bool = True
) -> ts.Context:
    vault = get_vault_instance(vault_master_password)
    context = ts.context(
        scheme,
        poly_modulus_degree=poly_modulus_degree,
        plain_modulus=plain_modulus
    )
    if generate_galois:
        context.generate_galois_keys()
    if generate_relin:
        context.generate_relin_keys()
    try:
        full_context_data = context.serialize(save_secret_key=True)
        vault.store_context_data(f"{context_name}_secret", full_context_data, vault_master_password)
        logger.info(f"Full context (with secret key) for '{context_name}' stored in vault.")

        if store_public_separately:
            public_context = ts.context_from(full_context_data)
            public_context.make_context_public()
            public_context_data = public_context.serialize(save_secret_key=False)
            vault.store_context_data(f"{context_name}_public", public_context_data, vault_master_password)
            logger.info(f"Public-only context for '{context_name}' stored in vault.")
    except Exception as e:
        logger.exception(f"Error storing TenSEAL context '{context_name}' in vault: {e}")
        raise
    return context

def load_tenseal_context_from_vault(
    vault_master_password: str,
    context_name: str,
    load_secret_key: bool = True
) -> ts.Context:
    vault = get_vault_instance(vault_master_password)
    effective_context_name = f"{context_name}_secret" if load_secret_key else f"{context_name}_public"
    if not vault.context_exists(effective_context_name, vault_master_password):
        if load_secret_key and vault.context_exists(context_name, vault_master_password):
            effective_context_name = context_name
        else:
             logger.error(f"TenSEAL context '{effective_context_name}' not found in vault.")
             raise FileNotFoundError(f"TenSEAL context '{effective_context_name}' not found in vault.")
    try:
        context_data = vault.retrieve_context_data(effective_context_name, vault_master_password)
        context = ts.context_from(context_data)
        logger.info(f"TenSEAL context '{effective_context_name}' loaded successfully from vault.")
        return context
    except Exception as e:
        logger.exception(f"Error loading TenSEAL context '{effective_context_name}' from vault: {e}")
        raise

def example_usage():
    # BasicConfig for logging if this script is run directly.
    # Placed here so it's configured before any other logging calls in this function.
    if not logger.handlers and not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            handlers=[logging.StreamHandler()])

    logger.info("\n### Running Enhanced Key Management Example (SecureKeyVault SIMULATION) ###")
    logger.warning("WARNING: This example uses a SIMULATED SecureKeyVault and is NOT for production key security.")

    demo_master_password = "supersecretpassword123"
    context_id = "my_bfv_app_context"

    logger.info("\n--- Creating and Storing Context (with secret key) in Vault ---")
    admin_context = create_and_store_tenseal_context(
        vault_master_password=demo_master_password,
        context_name=context_id,
        store_public_separately=True
    )

    data_to_encrypt = [10, 20, 30]
    encrypted_data = ts.bfv_vector(admin_context, data_to_encrypt)
    logger.info(f"Encrypted {data_to_encrypt} with admin_context -> {type(encrypted_data)}")

    decrypted_data = encrypted_data.decrypt()
    logger.info(f"Decrypted by admin_context: {decrypted_data}")
    assert decrypted_data == data_to_encrypt, "Decryption failed with admin context!"

    logger.info("\n--- Loading Public Context from Vault (for encryption/HE operations) ---")
    public_context = load_tenseal_context_from_vault(
        vault_master_password=demo_master_password,
        context_name=context_id,
        load_secret_key=False
    )

    data_to_encrypt_public = [40, 50, 60]
    encrypted_data_public = ts.bfv_vector(public_context, data_to_encrypt_public)
    logger.info(f"Encrypted {data_to_encrypt_public} with public_context -> {type(encrypted_data_public)}")

    try:
        encrypted_data_public.decrypt()
    except RuntimeError as e:
        logger.info(f"As expected, decryption with public_context failed: {e}")

    logger.info("\n--- Loading Context with Secret Key from Vault (for decryption) ---")
    decryption_context = load_tenseal_context_from_vault(
        vault_master_password=demo_master_password,
        context_name=context_id,
        load_secret_key=True
    )

    decrypted_data_from_public_encryption = encrypted_data_public.decrypt(decryption_context)
    logger.info(f"Decrypted data (originated from public_context encryption) by decryption_context: {decrypted_data_from_public_encryption}")
    assert decrypted_data_from_public_encryption == data_to_encrypt_public, "Decryption failed!"

    logger.info("\nEnhanced key management example completed.")
    logger.info("Note: Keys are stored in memory in the SecureKeyVault instance for this session.")
    logger.info("If the script restarts, the vault will be empty unless persisted (which this simulation does not do).")


if __name__ == "__main__":
    # Configure basicConfig for logging when script is run directly
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            handlers=[logging.StreamHandler()])

    logger.info("Starting key_management.py example usage from __main__...")

    old_keys_dir = "dev_keys"
    old_temp_dir = os.path.join(os.getcwd(), "temp_tenseal_keys")
    for dir_path in [old_keys_dir, old_temp_dir]:
        if os.path.exists(dir_path):
            logger.debug(f"Attempting to clean up old key directory: {dir_path}")
            try:
                for f_name in os.listdir(dir_path):
                    if f_name.endswith(".tenseal"):
                        os.remove(os.path.join(dir_path, f_name))
            except Exception as e:
                logger.warning(f"Could not fully clean up {dir_path}: {e}", exc_info=True)

    example_usage()
