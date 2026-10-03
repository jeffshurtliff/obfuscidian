import os
from cryptography.fernet import Fernet


def generate_and_save_key(key_path="secret.key"):
    """Generates a key and saves it to a file. Keep this safe!"""
    key = Fernet.generate_key()
    with open(key_path, "wb") as key_file:
        key_file.write(key)
    print(f"Key saved to {key_path}. Do not lose this file!")
    return key


def load_key(key_path="secret.key"):
    """Loads the key from the current directory."""
    return open(key_path, "rb").read()


def process_directory(root_dir, key, decrypt=False):
    """Recursively encrypts or decrypts .txt and .md files."""
    fernet = Fernet(key)

    # Supported file extensions
    target_extensions = ('.txt', '.md')

    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith(target_extensions):
                file_path = os.path.join(dirpath, filename)

                try:
                    # Read the original file data
                    with open(file_path, "rb") as f:
                        file_data = f.read()

                    # Process data
                    if decrypt:
                        processed_data = fernet.decrypt(file_data)
                        action = "Decrypted"
                    else:
                        processed_data = fernet.encrypt(file_data)
                        action = "Encrypted"

                    # Write the processed data back in-place
                    with open(file_path, "wb") as f:
                        f.write(processed_data)

                    print(f"{action}: {file_path}")

                except Exception as e:
                    print(f"Error processing {file_path}: {e}")


# --- HOW TO USE IT ---
if __name__ == "__main__":
    # 1. Generate a key (Only run this ONCE, then comment it out)
    # my_key = generate_and_save_key()

    # 2. Load your existing key
    my_key = load_key()

    # 3. Define target directory
    target_folder = "./my_notes"

    # 4. Run (Set decrypt=True when you want your text back)
    process_directory(target_folder, my_key, decrypt=False)
