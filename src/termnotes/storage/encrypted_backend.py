"""
Encrypted storage backend that wraps another backend
"""

import os
import base64
import hashlib
from typing import List, Optional, Union
from chacha20poly1305 import ChaCha20Poly1305
from .base import StorageBackend
from ..note import Note


class EncryptedBackend(StorageBackend):
    """
    Storage backend wrapper that encrypts/decrypts note content.

    Wraps any other storage backend and transparently encrypts content
    before saving and decrypts after loading. Note IDs and timestamps
    remain unencrypted for indexing and sorting.

    Uses ChaCha20-Poly1305 authenticated encryption with PBKDF2 key derivation:
    - Accepts arbitrary-length passwords/passphrases
    - Derives 256-bit keys using PBKDF2-HMAC-SHA256
    - Fast encryption (especially on systems without AES hardware acceleration)
    - Authentication (detects tampering)
    """

    NONCE_SIZE = 12  # ChaCha20-Poly1305 uses 96-bit (12-byte) nonces
    SALT_SIZE = 16   # 128-bit salt for PBKDF2

    def __init__(self, backend: StorageBackend, password: Union[str, bytes], auto_migrate: bool = True):
        """
        Initialize encrypted backend

        Args:
            backend: Underlying storage backend to wrap
            password: Password/passphrase of any length (string or bytes)
                     Will be converted to 32-byte key via PBKDF2
                     Salt is derived from the password itself
            auto_migrate: If True, automatically encrypt unencrypted notes on init

        Raises:
            ValueError: If password is invalid
        """
        self.backend = backend

        # Derive salt from password using a different KDF
        # This allows us to only store the passphrase, not a separate salt
        self.salt = self._derive_salt(password)

        # Derive encryption key from password using the derived salt
        encryption_key = self._derive_key(password, self.salt)

        try:
            self.cipher = ChaCha20Poly1305(encryption_key)
        except Exception as e:
            raise ValueError(f"Invalid encryption key: {e}")

        # Migrate unencrypted notes if requested
        if auto_migrate:
            self._migrate_unencrypted_notes()

    @staticmethod
    def _derive_salt(password: Union[str, bytes]) -> bytes:
        """
        Derive a deterministic salt from password using BLAKE2b

        Uses BLAKE2b with a fixed application-specific personalization string.
        This allows deriving the same salt from the same password consistently.

        Args:
            password: User password (string or bytes)

        Returns:
            16-byte salt
        """
        if isinstance(password, str):
            password_bytes = password.encode('utf-8')
        else:
            password_bytes = password

        # Use BLAKE2b with personalization for domain separation
        # This prevents salt reuse across different applications
        h = hashlib.blake2b(
            password_bytes,
            digest_size=16,
            person=b'termnotes-salt'
        )
        return h.digest()

    @staticmethod
    def _derive_key(password: Union[str, bytes], salt: bytes, iterations: int = 600_000) -> bytes:
        """
        Derive a 32-byte encryption key from password using PBKDF2-HMAC-SHA256

        Args:
            password: User password (string or bytes)
            salt: 16-byte salt
            iterations: Number of PBKDF2 iterations (default: 600,000)

        Returns:
            32-byte encryption key
        """
        if isinstance(password, str):
            password_bytes = password.encode('utf-8')
        else:
            password_bytes = password

        return hashlib.pbkdf2_hmac(
            'sha256',
            password_bytes,
            salt,
            iterations,
            dklen=32
        )

    def _encrypt_content(self, content: str) -> str:
        """
        Encrypt note content

        Args:
            content: Plain text content

        Returns:
            Encrypted content as base64 string with prepended nonce
            Format: base64(nonce + ciphertext)
        """
        if not content:
            return ""

        # Generate random nonce for this encryption
        nonce = os.urandom(self.NONCE_SIZE)

        # Encrypt content
        plaintext_bytes = content.encode('utf-8')
        ciphertext = self.cipher.encrypt(nonce, plaintext_bytes)

        # Prepend nonce to ciphertext (nonce doesn't need to be secret)
        encrypted_bytes = nonce + ciphertext

        # Encode as base64 for storage
        return base64.b64encode(encrypted_bytes).decode('ascii')

    def _decrypt_content(self, encrypted_content: str) -> str:
        """
        Decrypt note content

        Args:
            encrypted_content: Encrypted content as base64 string

        Returns:
            Decrypted plain text content

        Raises:
            Exception: If decryption fails (wrong key, corrupted data, tampered data)
        """
        if not encrypted_content:
            return ""

        # Decode from base64
        encrypted_bytes = base64.b64decode(encrypted_content.encode('ascii'))

        # Extract nonce and ciphertext
        if len(encrypted_bytes) < self.NONCE_SIZE:
            raise ValueError("Encrypted content too short to contain nonce")

        nonce = encrypted_bytes[:self.NONCE_SIZE]
        ciphertext = encrypted_bytes[self.NONCE_SIZE:]

        # Decrypt
        plaintext_bytes = self.cipher.decrypt(nonce, ciphertext)

        return plaintext_bytes.decode('utf-8')

    def get_all_notes(self) -> List[Note]:
        """
        Get all notes with decrypted content

        Returns:
            List of notes with decrypted content
        """
        encrypted_notes = self.backend.get_all_notes()

        decrypted_notes = []
        for note in encrypted_notes:
            try:
                decrypted_content = self._decrypt_content(note.content)

                # Strip encryption metadata from properties when decrypting
                decrypted_properties = note.properties.copy()
                decrypted_properties.pop("encrypted", None)
                decrypted_properties.pop("encryption_method", None)

                decrypted_note = Note(
                    note_id=note.id,
                    content=decrypted_content,
                    created_at=note.created_at,
                    updated_at=note.updated_at,
                    properties=decrypted_properties
                )
                decrypted_notes.append(decrypted_note)
            except Exception as e:
                # Log error but continue with other notes
                # Could add logging here if needed
                print(f"Warning: Failed to decrypt note {note.id}: {e}")
                # Add note with error marker
                error_note = Note(
                    note_id=note.id,
                    content=f"[DECRYPTION FAILED: {str(e)}]",
                    created_at=note.created_at,
                    updated_at=note.updated_at,
                    properties=note.properties
                )
                decrypted_notes.append(error_note)

        return decrypted_notes

    def get_note(self, note_id: str) -> Optional[Note]:
        """
        Get a specific note by ID with decrypted content

        Args:
            note_id: Unique identifier for the note

        Returns:
            Note with decrypted content if found, None otherwise
        """
        encrypted_note = self.backend.get_note(note_id)

        if encrypted_note is None:
            return None

        try:
            decrypted_content = self._decrypt_content(encrypted_note.content)

            # Strip encryption metadata from properties when decrypting
            decrypted_properties = encrypted_note.properties.copy()
            decrypted_properties.pop("encrypted", None)
            decrypted_properties.pop("encryption_method", None)

            return Note(
                note_id=encrypted_note.id,
                content=decrypted_content,
                created_at=encrypted_note.created_at,
                updated_at=encrypted_note.updated_at,
                properties=decrypted_properties
            )
        except Exception as e:
            # Return note with error marker if decryption fails
            print(f"Warning: Failed to decrypt note {note_id}: {e}")
            return Note(
                note_id=encrypted_note.id,
                content=f"[DECRYPTION FAILED: {str(e)}]",
                created_at=encrypted_note.created_at,
                updated_at=encrypted_note.updated_at,
                properties=encrypted_note.properties
            )

    def save_note(self, note: Note):
        """
        Save note with encrypted content

        Args:
            note: Note object with plain text content
        """
        encrypted_content = self._encrypt_content(note.content)

        # Create encrypted note with properties
        # Copy properties and mark as encrypted
        encrypted_properties = note.properties.copy()
        encrypted_properties["encrypted"] = True
        encrypted_properties["encryption_method"] = "chacha20poly1305-pbkdf2"

        encrypted_note = Note(
            note_id=note.id,
            content=encrypted_content,
            created_at=note.created_at,
            updated_at=note.updated_at,
            properties=encrypted_properties
        )

        self.backend.save_note(encrypted_note)

    def delete_note(self, note_id: str):
        """
        Delete a note by ID

        Args:
            note_id: ID of note to delete
        """
        self.backend.delete_note(note_id)

    def close(self):
        """Clean up underlying backend resources"""
        self.backend.close()

    def _migrate_unencrypted_notes(self):
        """
        Migrate unencrypted notes to encrypted format

        Checks all notes in the underlying backend. For any note that doesn't
        have the 'encrypted' property set to True, encrypts it in place.

        This is useful when:
        - Switching from unencrypted to encrypted storage
        - Recovering from partial encryption failures
        """
        try:
            # Get all notes directly from backend (bypassing our encryption layer)
            all_notes = self.backend.get_all_notes()

            unencrypted_count = 0
            migrated_notes = []

            for note in all_notes:
                # Check if note is already encrypted
                if note.get_property("encrypted") == True:
                    continue

                # Note is unencrypted - encrypt it
                unencrypted_count += 1

                # Encrypt the content
                encrypted_content = self._encrypt_content(note.content)

                # Add encryption metadata
                encrypted_properties = note.properties.copy()
                encrypted_properties["encrypted"] = True
                encrypted_properties["encryption_method"] = "chacha20poly1305-pbkdf2"

                # Create encrypted note
                encrypted_note = Note(
                    note_id=note.id,
                    content=encrypted_content,
                    created_at=note.created_at,
                    updated_at=note.updated_at,
                    properties=encrypted_properties
                )

                migrated_notes.append(encrypted_note)

            # Save all encrypted notes
            for encrypted_note in migrated_notes:
                self.backend.save_note(encrypted_note)

            if unencrypted_count > 0:
                print(f"✓ Migrated {unencrypted_count} unencrypted note(s) to encrypted storage")
                print("Press Enter to continue...")
                input()

        except Exception as e:
            print(f"Warning: Failed to migrate notes: {e}")
            print("Press Enter to continue...")
            input()

    @staticmethod
    def generate_passphrase(num_words: int = 6, delimiter: str = "-") -> str:
        """
        Generate a random memorable passphrase using xkcdpass

        Uses cryptographically secure random selection from a large wordlist.
        Each word provides significant entropy for strong security.

        Args:
            num_words: Number of words in passphrase (default: 6 = strong security)
            delimiter: Character to join words (default: "-")

        Returns:
            Passphrase as string (e.g., "correct-horse-battery-staple-random-words")

        Example:
            passphrase = EncryptedBackend.generate_passphrase()
            # Store passphrase securely - it's your only way to decrypt!
            backend = EncryptedBackend(underlying_backend, passphrase)

        Entropy levels:
            4 words = moderate security
            6 words = strong security (recommended)
            8 words = very strong security
        """
        from xkcdpass import xkcd_password as xp

        # Get the wordlist
        wordlist = xp.generate_wordlist(
            wordfile=xp.locate_wordfile(),
            min_length=4,
            max_length=8
        )

        # Generate passphrase with cryptographically secure randomness
        return xp.generate_xkcdpassword(
            wordlist,
            numwords=num_words,
            delimiter=delimiter,
            case="lower"
        )
