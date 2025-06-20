import tenseal as ts
import os

# --- Development/Educational Purposes Only ---
# WARNING: This key management approach is NOT secure for production.
# It saves cryptographic keys directly to the local filesystem without
# proper access controls, encryption at rest for the keys themselves,
# or audit logging that a true Key Management System (KMS) would provide.
# For production systems, use a dedicated KMS (e.g., HashiCorp Vault,
# AWS KMS, Azure Key Vault, Google Cloud KMS).
# --- Development/Educational Purposes Only ---

DEFAULT_KEYS_DIR = "dev_keys"

def create_and_save_tenseal_context(
    context_name: str,
    scheme: ts.SCHEME_TYPE = ts.SCHEME_TYPE.BFV,
    poly_modulus_degree: int = 8192,
    plain_modulus: int = 1032193,
    generate_galois: bool = True,
    generate_relin: bool = True,
    keys_dir: str = DEFAULT_KEYS_DIR
) -> ts.Context:
    """
    Creates a TenSEAL context, generates keys, and saves them to files.

    Args:
        context_name (str): A unique name for this context (used for filenames).
        scheme (ts.SCHEME_TYPE): The HE scheme to use (BFV or CKKS).
        poly_modulus_degree (int): Degree of the polynomial modulus.
        plain_modulus (int): Plaintext modulus.
        generate_galois (bool): Whether to generate Galois keys.
        generate_relin (bool): Whether to generate Relinearization keys.
        keys_dir (str): Directory to save the key files.

    Returns:
        ts.Context: The created TenSEAL context.
    """
    context = ts.context(
        scheme,
        poly_modulus_degree=poly_modulus_degree,
        plain_modulus=plain_modulus
    )

    # Important: For BFV, secret key is needed for decryption.
    # For CKKS, secret key is also needed.
    # Public key is used for encryption.
    # Galois keys are for rotations.
    # Relinearization keys are for reducing noise after multiplications.

    if generate_galois:
        context.generate_galois_keys() # Requires secret key
    if generate_relin:
        context.generate_relin_keys() # Requires secret key

    # Make the keys directory if it doesn't exist
    os.makedirs(keys_dir, exist_ok=True)

    # Saving the secret key (MOST SENSITIVE)
    try:
        secret_key_path = os.path.join(keys_dir, f"{context_name}_secret.tenseal")
        with open(secret_key_path, "wb") as f:
            f.write(context.serialize(save_secret_key=True))
        print(f"Context (including secret key) saved to {secret_key_path}")

        # For sharing with someone who only encrypts, you'd serialize without the secret key
        # and share that along with Galois/Relin keys if needed for their operations.
        public_context_path = os.path.join(keys_dir, f"{context_name}_public.tenseal")
        with open(public_context_path, "wb") as f:
            # Serialize without secret key for the public part
            context.make_context_public() # Strips secret key for this serialization
            f.write(context.serialize(save_secret_key=False))
        print(f"Public context (without secret key) saved to {public_context_path}")

        # Re-populate context with secret key for current user, as make_context_public is destructive.
        # This is a bit of a workaround for TenSEAL's API design if you want to save both
        # a private and public version from the same context object sequentially.
        # A cleaner way might be to load the secret key back if needed immediately,
        # or create two contexts if you need to operate with both simultaneously.
        # For simplicity here, we'll just re-initialize it for the current user to keep using it.
        # This implies the original context object still holds the secret key in memory
        # *before* make_context_public is called.
        # After make_context_public, the in-memory context loses its secret key.
        # Let's reload from the saved secret key version for the active context.

        # Re-create the context with its secret key for continued use by the 'admin'
        # This ensures the returned context object is fully usable with its secret key.
        context = ts.context(
            scheme,
            poly_modulus_degree=poly_modulus_degree,
            plain_modulus=plain_modulus
        )
        # The keys (secret, public, galois, relin) are part of the context object.
        # We need to re-generate them if we want the admin_context to have them after it was made public for saving.
        # A better approach for production would be to load the saved secret_key_path
        # into a new context object if the admin needs to continue operations.
        # For this example, we re-initialize and re-generate to keep it simple.
        if generate_galois: context.generate_galois_keys()
        if generate_relin: context.generate_relin_keys()
        # Re-save the full context so the _secret.tenseal file is correct if it was overwritten by a public one
        # (it wasn't in the code above, but good to be robust)
        with open(secret_key_path, "wb") as f_full_ser:
            f_full_ser.write(context.serialize(save_secret_key=True))

        print("Admin context re-initialized with secret key for current session.")

    except Exception as e:
        print(f"Error saving TenSEAL context {context_name}: {e}")
        # Consider re-raising or specific error handling
        raise

    return context

def load_tenseal_context(context_name: str, keys_dir: str = DEFAULT_KEYS_DIR, load_secret_key: bool = True) -> ts.Context:
    """
    Loads a TenSEAL context from saved files.

    Args:
        context_name (str): The unique name of the context to load.
        keys_dir (str): Directory where key files are stored.
        load_secret_key (bool): If True, loads the context with the secret key
                                (for decryption/key generation).
                                If False, loads the public context (for encryption/HE ops).

    Returns:
        ts.Context: The loaded TenSEAL context.
    """
    if load_secret_key:
        file_path = os.path.join(keys_dir, f"{context_name}_secret.tenseal")
        print(f"Loading context with secret key from: {file_path}")
    else:
        file_path = os.path.join(keys_dir, f"{context_name}_public.tenseal")
        print(f"Loading public context from: {file_path}")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"TenSEAL context file not found: {file_path}")

    try:
        with open(file_path, "rb") as f:
            context_data = f.read()
        context = ts.context_from(context_data)
        print(f"TenSEAL context '{context_name}' loaded successfully from {file_path}.")
        return context
    except Exception as e:
        print(f"Error loading TenSEAL context {context_name} from {file_path}: {e}")
        # Consider re-raising or specific error handling
        raise

def example_usage():
    # --- Development/Educational Purposes Only ---
    print("### Running Key Management Example ###")
    print("WARNING: This example saves keys to local files and is NOT secure for production.")

    context_id = "my_bfv_context"
    keys_storage_path = os.path.join(os.getcwd(), "temp_tenseal_keys") # Example path

    # Clean up old keys if they exist for the example
    if os.path.exists(keys_storage_path):
        for f_name in os.listdir(keys_storage_path):
            if f_name.startswith(context_id):
                os.remove(os.path.join(keys_storage_path, f_name))

    print(f"Using temporary key storage for example: {keys_storage_path}")

    # Create and save a context (this instance will have the secret key)
    print("\n--- Creating and Saving Context (with secret key) ---")
    admin_context = create_and_save_tenseal_context(context_id, keys_dir=keys_storage_path)

    # Encrypt something with the admin_context (which contains the secret key)
    data_to_encrypt = [1, 2, 3]
    encrypted_data = ts.bfv_vector(admin_context, data_to_encrypt)
    print(f"Encrypted {data_to_encrypt} -> {type(encrypted_data)}")

    # Decrypt with admin_context
    decrypted_data = encrypted_data.decrypt()
    print(f"Decrypted by admin_context: {decrypted_data}")
    assert decrypted_data == data_to_encrypt, "Decryption failed with admin context!"

    # Load the public context (for someone who only encrypts/operates on encrypted data)
    print("\n--- Loading Public Context (for encryption/HE operations) ---")
    public_context = load_tenseal_context(context_id, keys_dir=keys_storage_path, load_secret_key=False)

    # Encrypt with public_context
    data_to_encrypt_public = [4, 5, 6]
    encrypted_data_public = ts.bfv_vector(public_context, data_to_encrypt_public)
    print(f"Encrypted {data_to_encrypt_public} with public_context -> {type(encrypted_data_public)}")

    # Perform an operation requiring relin keys (if context has them)
    # Example: add encrypted_data (from admin) and encrypted_data_public
    # This requires both contexts to be compatible (same parameters)
    # For simplicity, let's assume we're operating on data encrypted with the public_context
    # and the public_context has relin/galois keys (which it would if saved from a full context)

    # encrypted_sum_public = encrypted_data_public + encrypted_data_public # Needs relin keys
    # print(f"Performed addition with public_context.")
    # Attempting to decrypt encrypted_data_public with public_context will fail as it lacks secret key
    try:
        encrypted_data_public.decrypt() # This should fail
    except RuntimeError as e:
        print(f"As expected, decryption with public_context failed: {e}")


    # Load the context WITH the secret key (for decryption)
    print("\n--- Loading Context with Secret Key (for decryption) ---")
    decryption_context = load_tenseal_context(context_id, keys_dir=keys_storage_path, load_secret_key=True)

    # Decrypt data that was encrypted with the public_context, using the decryption_context
    decrypted_data_from_public_encryption = encrypted_data_public.decrypt(decryption_context)
    print(f"Decrypted data (originated from public_context encryption) by decryption_context: {decrypted_data_from_public_encryption}")
    assert decrypted_data_from_public_encryption == data_to_encrypt_public, "Decryption failed for data from public context!"

    print("\nKey management example completed.")
    # Clean up temporary key directory
    # for f_name in os.listdir(keys_storage_path):
    #     os.remove(os.path.join(keys_storage_path, f_name))
    # os.rmdir(keys_storage_path)
    # print(f"Cleaned up {keys_storage_path}")


if __name__ == "__main__":
    example_usage()
