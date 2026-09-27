"""
Benchmark Vulnerable Microservice.
Contains intentional security flaws across OWASP Top 10 / CWE for audit evaluation.
"""

import hashlib
import os
import pickle
import sqlite3

# CWE-798: Hardcoded high-entropy secret API token
API_KEY = "sk-live-99a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4"


def get_user_profile(user_id: str):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    # CWE-89: SQL Injection via direct f-string interpolation
    cursor.execute(f"SELECT id, username, email FROM users WHERE id = '{user_id}'")
    return cursor.fetchone()


def ping_diagnostics(host: str):
    # CWE-78: OS Command Injection via shell command formatting
    os.system(f"ping -c 1 {host}")


def read_uploaded_file(filename: str):
    # CWE-22: Path Traversal without boundary verification
    with open(f"/var/www/uploads/{filename}", "r") as f:
        return f.read()


def restore_user_session(session_bytes: bytes):
    # CWE-502: Insecure Deserialization of untrusted stream
    return pickle.loads(session_bytes)


def hash_user_password(password: str):
    # CWE-327: Use of broken and deprecated MD5 algorithm
    return hashlib.md5(password.encode()).hexdigest()


def calculate_dynamic_formula(formula_str: str):
    # CWE-94: Code Injection via dynamic eval
    return eval(formula_str)
