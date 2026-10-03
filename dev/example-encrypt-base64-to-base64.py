from cryptography.fernet import Fernet

# 1. Generate a Fernet key (this is already a URL-safe base64 encoded byte string)
key = Fernet.generate_key()
cipher_suite = Fernet(key)

# 2. Your starting Base64 string (e.g., "SGVsbG8gV29ybGQ=" is "Hello World")
input_base64_str = "SGVsbG8gV29ybGQ="

# 3. Convert the input string into bytes (Fernet requires byte inputs)
data_bytes = input_base64_str.encode("utf-8")

# 4. Encrypt the data
# Fernet outputs a token that is inherently a URL-safe base64-encoded byte string
encrypted_bytes = cipher_suite.encrypt(data_bytes)

# 5. Decode the bytes back to a standard string
output_base64_str = encrypted_bytes.decode("utf-8")

print(f"Original Base64 String:  {input_base64_str}")
print(f"Encrypted Base64 String: {output_base64_str}")


# --- Optional: Decryption to verify ---
# Convert the encrypted string back to bytes to decrypt it
decrypted_bytes = cipher_suite.decrypt(output_base64_str.encode("utf-8"))
decrypted_base64_str = decrypted_bytes.decode("utf-8")

print(f"Decrypted Base64 String: {decrypted_base64_str}")
