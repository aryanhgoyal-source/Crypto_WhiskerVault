from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
import os
from paths import SIGNATURES
from audit_log import log_event, user_from_key


def compute_hash(file_path):
    hasher = hashes.Hash(hashes.SHA256())
    with open(file_path, "rb") as f:
        while chunk := f.read(4096):
            hasher.update(chunk)
    return hasher.finalize()


def sign_file(file_path, private_key_path, signature_path):
    file_hash = compute_hash(file_path)

    with open(private_key_path, "rb") as f:
        private_key = serialization.load_pem_private_key(f.read(), password=None)

    signature = private_key.sign(
        file_hash,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()  # note: signs a pre-hash, so this labels the hash algo used
    )

    with open(signature_path, "wb") as f:
        f.write(signature)

    print(f"Signature saved to {signature_path}")
    log_event(user_from_key(private_key_path), "SIGN", os.path.basename(file_path), "SUCCESS")


def verify_file(file_path, public_key_path, signature_path):
    file_hash = compute_hash(file_path)

    with open(public_key_path, "rb") as f:
        public_key = serialization.load_pem_public_key(f.read())

    with open(signature_path, "rb") as f:
        signature = f.read()

    try:
        public_key.verify(
            signature,
            file_hash,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        print("✅ Verification PASSED — file is authentic and untampered.")
        log_event(user_from_key(public_key_path), "VERIFY", os.path.basename(file_path), "SUCCESS")
        return True
    except Exception:
        print("❌ Verification FAILED — file may be tampered or signature invalid.")
        log_event(user_from_key(public_key_path), "VERIFY", os.path.basename(file_path), "FAILED")
        return False

def sign_or_verify(file_path, private_key_path, public_key_path):
    name = os.path.basename(file_path)
    sig_path = os.path.join(SIGNATURES, name + ".sig")

    if os.path.exists(sig_path):
        print(f"Signature found for {name}, verifying...")
        return verify_file(file_path, public_key_path, sig_path)
    else:
        print(f"New file {name}, signing it...")
        sign_file(file_path, private_key_path, sig_path)
        return True