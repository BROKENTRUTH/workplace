import tenseal as ts
from . import key_management # Relative import

def run_tenseal_example():
    try:
        # Setup TenSEAL context
        context = ts.context(
            ts.SCHEME_TYPE.BFV,
        poly_modulus_degree=8192,
        plain_modulus=1032193
        )
        context.generate_galois_keys()
        context.generate_relin_keys()
        # Set the scale for CKKS if it were used (BFV doesn't need it for integers)
        # context.global_scale = 2**40

        print("TenSEAL context created successfully.")

        # Encrypt some numbers
        plain_v1 = [10, 20, 30]
        plain_v2 = [5, 10, 15]

        print(f"Plain V1: {plain_v1}")
        print(f"Plain V2: {plain_v2}")

        encrypted_v1 = ts.bfv_vector(context, plain_v1)
        encrypted_v2 = ts.bfv_vector(context, plain_v2)
        print("Vectors encrypted successfully.")

        # Perform homomorphic addition
        encrypted_sum = encrypted_v1 + encrypted_v2
        print("Homomorphic addition performed.")

        # Decrypt the result
        decrypted_sum = encrypted_sum.decrypt()
        print(f"Decrypted Sum: {decrypted_sum}")

        # Perform homomorphic multiplication (BFV supports this)
        # Note: Multiplication depth is limited in BFV.
        # For more complex computations, CKKS might be preferred for approximate numbers
        # or deeper BFV parameters might be needed.
        encrypted_prod = encrypted_v1 * encrypted_v2 # Element-wise
        print("Homomorphic multiplication performed.")
        decrypted_prod = encrypted_prod.decrypt()
        print(f"Decrypted Product: {decrypted_prod}")

        # Example with a scalar
        encrypted_v1_plus_5 = encrypted_v1 + 5
        decrypted_v1_plus_5 = encrypted_v1_plus_5.decrypt()
        print(f"Decrypted (V1 + 5): {decrypted_v1_plus_5}")


    except Exception as e:
        print(f"An error occurred during TenSEAL example: {e}")
        print("Please ensure TenSEAL is installed correctly (pip install tenseal).")
        print("If you are in an environment without C++ build tools, installing from source or using a pre-built wheel might be necessary.")
        return False

    return True

if __name__ == "__main__":
    if run_tenseal_example():
        print("TenSEAL example ran successfully!")
    else:
        print("TenSEAL example failed.")

    print("\nRunning key management example from tenseal_example.py:")
    key_management.example_usage()
