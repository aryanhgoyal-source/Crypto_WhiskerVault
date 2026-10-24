import os
from paths import *
from cyphering import encrypt_file, decrypt_file
from integrity import sign_or_verify, verify_file
from audit_log import show_logs

user = "aryan"
priv = os.path.join(KEYS, f"{user}_private.pem")
pub = os.path.join(KEYS, f"{user}_public.pem")

doc = os.path.join(DOCS, "test.txt")
enc = os.path.join(ENCRYPTED, "test.enc")
dec = os.path.join(DECRYPTED, "test_decrypted.txt")
sig = os.path.join(SIGNATURES, "test.txt.sig")

# 1. Sign (new file) or verify (already signed)
ok = sign_or_verify(doc, priv, pub)

if ok:
    # 2. Encrypt
    encrypt_file(doc, enc, pub)

    # 3. Decrypt
    decrypt_file(enc, dec, priv)

    # 4. Verify the decrypted copy against the original signature
    verify_file(dec, pub, sig)

show_logs()