import base64

# OBFUSCATION
# Convert Markdown file name to obfuscated file name
original_bytes = b"team meeting - 2026-10-01.md"

# See example-encrypt-base64-to-base64.py for encrypting either the original file name or base64 string

# Encode to urlsafe base64 and strip trailing '=' padding bytes
encoded_bytes = base64.urlsafe_b64encode(original_bytes).rstrip(b'=')
filename = encoded_bytes.decode('utf-8') + ".obf"

print(filename)
# Output: dGVhbSBtZWV0aW5nIC0gMjAyNi0xMC0wMS5tZA.obf


# DE-OBFUSCATION
# Extract the base64 portion from the filename
filename = "dGVhbSBtZWV0aW5nIC0gMjAyNi0xMC0wMS5tZA.obf"
b64_string = filename.split('.')[0]

# Add back the correct amount of padding dynamically
padded_string = b64_string + "=" * ((4 - len(b64_string) % 4) % 4)

# Safely decode
decoded_bytes = base64.urlsafe_b64decode(padded_string)
print(decoded_bytes.decode('utf-8'))
# Output: team meeting - 2026-10-01.md
