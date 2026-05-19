import os
import tempfile
import pytest
from app.utils.hash import compute_file_hash


def test_hash_consistency():
    """Same file should produce same hash"""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
        f.write(b"test content for hashing")
        path = f.name

    try:
        hash1 = compute_file_hash(path)
        hash2 = compute_file_hash(path)
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex length
    finally:
        os.unlink(path)


def test_hash_different_files():
    """Different files should produce different hashes"""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f1:
        f1.write(b"content A")
        path1 = f1.name

    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f2:
        f2.write(b"content B")
        path2 = f2.name

    try:
        assert compute_file_hash(path1) != compute_file_hash(path2)
    finally:
        os.unlink(path1)
        os.unlink(path2)


def test_hash_large_file():
    """Hash should work with chunked reading for large files"""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as f:
        # Write 256KB of data
        f.write(b"x" * 256 * 1024)
        path = f.name

    try:
        h = compute_file_hash(path, chunk_size=65536)
        assert len(h) == 64
    finally:
        os.unlink(path)
