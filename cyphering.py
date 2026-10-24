import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding as sym_padding
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
from cryptography.hazmat.primitives import serialization, hashes
from audit_log import log_event, user_from_key


def encrypt_file(input_path, output_path, public_key_path):
    # Generate a random AES key and IV
    aes_key = os.urandom(32)  # 256-bit key
    iv = os.urandom(16)

    # Read the file to encrypt
    with open(input_path, "rb") as f:
        data = f.read()

    # Pad data to AES block size
    padder = sym_padding.PKCS7(128).padder()
    padded_data = padder.update(data) + padder.finalize()

    # Encrypt with AES-CBC
    cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    encrypted_data = encryptor.update(padded_data) + encryptor.finalize()

    # Load recipient's public key
    with open(public_key_path, "rb") as f:
        public_key = serialization.load_pem_public_key(f.read())

    # Encrypt the AES key with RSA public key
    encrypted_aes_key = public_key.encrypt(
        aes_key,
        asym_padding.OAEP(
            mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    # Save everything needed for decryption: encrypted key + iv + encrypted data
    with open(output_path, "wb") as f:
        f.write(len(encrypted_aes_key).to_bytes(4, "big"))
        f.write(encrypted_aes_key)
        f.write(iv)
        f.write(encrypted_data)

    print(f"Encrypted file saved to {output_path}")
    log_event(user_from_key(public_key_path), "ENCRYPT", os.path.basename(input_path), "SUCCESS")


def _decrypt_file(input_path, output_path, private_key_path):
    with open(input_path, "rb") as f:
        content = f.read()

    # Read encrypted AES key length, then the key, then IV, then data
    key_len = int.from_bytes(content[:4], "big")
    encrypted_aes_key = content[4:4+key_len]
    iv = content[4+key_len:4+key_len+16]
    encrypted_data = content[4+key_len+16:]

    # Load private key
    with open(private_key_path, "rb") as f:
        private_key = serialization.load_pem_private_key(f.read(), password=None)

    # Decrypt AES key with RSA private key
    aes_key = private_key.decrypt(
        encrypted_aes_key,
        asym_padding.OAEP(
            mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    # Decrypt data with AES
    cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv))
    decryptor = cipher.decryptor()
    padded_data = decryptor.update(encrypted_data) + decryptor.finalize()

    # Remove padding
    unpadder = sym_padding.PKCS7(128).unpadder()
    data = unpadder.update(padded_data) + unpadder.finalize()

    with open(output_path, "wb") as f:
        f.write(data)

    print(f"Decrypted file saved to {output_path}")

def decrypt_file(input_path, output_path, private_key_path):
    user = user_from_key(private_key_path)
    name = os.path.basename(input_path)
    try:
        _decrypt_file(input_path, output_path, private_key_path)
        log_event(user, "DECRYPT", name, "SUCCESS")
        return True
    except Exception:
        log_event(user, "DECRYPT", name, "FAILED")
        print("❌ Decryption failed: wrong key or corrupted file.")
        return False