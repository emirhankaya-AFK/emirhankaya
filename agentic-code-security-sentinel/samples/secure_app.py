"""
Benchmark Secure Application.
Demonstrates best-practice secure coding patterns matching the scenarios in vulnerable_app.py.
"""

import ast
import hashlib
import json
import os
import sqlite3
import subprocess

# Safe Secret handling via environment variables
API_KEY = os.environ.get("API_KEY", "")


def get_user_profile(user_id: str):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    # Safe Parameterized SQL Query
    cursor.execute("SELECT id, username, email FROM users WHERE id = ?", (user_id,))
    return cursor.fetchone()


def ping_diagnostics(host: str):
    # Safe Subprocess execution without shell=True
    subprocess.run(["ping", "-c", "1", host], shell=False, check=True)


def read_uploaded_file(filename: str):
    # Safe Path Traversal prevention with boundary check
    base_dir = os.path.abspath("/var/www/uploads")
    resolved_path = os.path.abspath(os.path.join(base_dir, os.path.basename(filename)))
    if not resolved_path.startswith(base_dir):
        raise PermissionError("Access outside upload directory is forbidden.")
    with open(resolved_path, "r") as f:
        return f.read()


def restore_user_session(session_bytes: bytes):
    # Safe JSON deserialization
    return json.loads(session_bytes.decode("utf-8"))


def hash_user_password(password: str):
    # Secure SHA-256 cryptographic hashing
    return hashlib.sha256(password.encode()).hexdigest()


def calculate_dynamic_formula(formula_str: str):
    # Safe AST literal evaluation
    return ast.literal_eval(formula_str)
