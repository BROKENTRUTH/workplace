import re

# --- Development/Educational Purposes Only ---
# This is a very basic signature-based IDS component.
# Signatures are hardcoded for demonstration.
# In a real system, signatures would be managed in a database or external files,
# and matching would need to be much more performant for high traffic volumes.
# --- Development/Educational Purposes Only ---

# Define a list of simple signatures.
# Each signature is a dictionary with 'id', 'name', 'type' (string/regex), and 'pattern'.
SIGNATURES = [
    {
        "id": "STR001",
        "name": "SQL Injection Attempt (SELECT * FROM)",
        "type": "regex", # Case-insensitive regex
        "pattern": r"select\s+\*\s+from"
    },
    {
        "id": "STR002",
        "name": "Common Web Shell Upload (cmd.php)",
        "type": "string", # Simple string containment
        "pattern": "cmd.php"
    },
    {
        "id": "REG001",
        "name": "Potential XSS Attempt (script tag)",
        "type": "regex", # Case-insensitive regex
        "pattern": r"<script.*?>.*?</script.*?>"
    },
    {
        "id": "STR003",
        "name": "Known Malicious User Agent (BadBot)",
        "type": "string",
        "pattern": "BadBot/1.0"
    },
    {
        "id": "REG002",
        "name": "Nikto Scan Attempt (Nikto User Agent)",
        "type": "regex",
        "pattern": r"Nikto/"
    }
]

def check_signatures(data_input: str) -> list:
    """
    Checks the input data against a predefined set of signatures.

    Args:
        data_input (str): The data to check (e.g., log line, packet payload snippet).

    Returns:
        list: A list of signature names that matched the input data.
              Returns an empty list if no signatures match.
    """
    matched_signatures = []
    if not isinstance(data_input, str):
        # print("Error: Input data must be a string.")
        return matched_signatures # Or raise TypeError

    for sig in SIGNATURES:
        try:
            if sig["type"] == "string":
                if sig["pattern"] in data_input:
                    matched_signatures.append(sig["name"])
            elif sig["type"] == "regex":
                # re.IGNORECASE can be added if patterns are not already case-insensitive
                if re.search(sig["pattern"], data_input, re.IGNORECASE):
                    matched_signatures.append(sig["name"])
        except re.error as e:
            # print(f"Regex error in signature {sig['id']} ('{sig['name']}'): {e}")
            # This signature will be skipped in case of error.
            # In a real system, invalid regexes should be caught during signature loading.
            pass
        except Exception as e:
            # print(f"Error processing signature {sig['id']} ('{sig['name']}'): {e}")
            pass # Skip this signature

    return matched_signatures

def example_usage():
    print("### Running Basic Signature-Based IDS Example ###")

    test_data_benign = [
        "GET /index.html HTTP/1.1 User-Agent: GoodBot/2.0",
        "This is a normal log entry.",
        "SELECT id, name FROM users WHERE id = 1" # Not matching "SELECT * FROM"
    ]

    test_data_suspicious = [
        "GET /admin.php?query=SELECT%20*%20FROM%20users HTTP/1.1 User-Agent: Mozilla/5.0", # Decoded: SELECT * FROM users
        "POST /upload.aspx HTTP/1.1 User-Agent: BadBot/1.0 attempting to upload cmd.php",
        "GET /page.html?name=<script>alert('XSS')</script> HTTP/1.1",
        "User tried to access /etc/passwd", # No specific signature for this
        "GET / HTTP/1.1 User-Agent: Nikto/2.1.6 (Evasions:None) (Test:001)",
        "Another alert with <ScRiPt>alert(1)</ScRiPt> somewhere." # Case variation for XSS
    ]

    print("\n--- Checking Benign Data ---")
    for i, data in enumerate(test_data_benign):
        matches = check_signatures(data)
        print(f"Data {i+1}: '{data[:50]}...' -> Matches: {matches if matches else 'None'}")

    print("\n--- Checking Suspicious Data ---")
    for i, data in enumerate(test_data_suspicious):
        matches = check_signatures(data)
        print(f"Data {i+1}: '{data[:70]}...' -> Matches: {matches if matches else 'None'}")

    print("\n--- Testing Invalid Input ---")
    matches_invalid = check_signatures(12345) # Non-string input
    print(f"Data (invalid type): {12345} -> Matches: {matches_invalid if matches_invalid else 'None'}")


if __name__ == "__main__":
    example_usage()
