import os

BASE = os.path.dirname(os.path.abspath(__file__))
KEYS = os.path.join(BASE, "keys")
DOCS = os.path.join(BASE, "documents")
ENCRYPTED = os.path.join(BASE, "encrypted")
DECRYPTED = os.path.join(BASE, "decrypted")
SIGNATURES = os.path.join(BASE, "signatures")
LOGS = os.path.join(BASE, "logs")

for folder in (KEYS, DOCS, ENCRYPTED, DECRYPTED, SIGNATURES, LOGS):
    os.makedirs(folder, exist_ok=True)