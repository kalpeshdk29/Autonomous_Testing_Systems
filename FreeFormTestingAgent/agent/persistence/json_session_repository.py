"""
File: json_session_repository.py

Purpose:
    Persist complete exploration session snapshots as JSON files.

Architecture:

ExplorationSessionSnapshot
        ↓
SessionSerializer
        ↓
JSON-Compatible Dictionary
        ↓
Temporary File
        ↓
Atomic Replace
        ↓
session.json

Storage Layout:

storage/
└── database/
    └── sessions/
        └── <session_id>/
            └── session.json

Important:
    The repository owns filesystem persistence only.

    It does not:
        - calculate coverage
        - modify session timestamps
        - create exploration knowledge
        - manage screenshots
        - manage individual state files
"""

import json
import os

from pathlib import Path

from agent.persistence.session_serializer import (
    SessionSerializer,
)

from agent.persistence.session_snapshot import (
    ExplorationSessionSnapshot,
)


class JsonSessionRepository:
    """
    Filesystem-backed repository for exploration sessions.

    Each session is stored at:

        <storage_root>/
            <session_id>/
                session.json

    Example:

        storage/database/sessions/
            calculator-run-001/
                session.json
    """

    SESSION_FILE_NAME = "session.json"

    TEMP_FILE_NAME = "session.json.tmp"

    def __init__(
        self,
        storage_root=(
            "storage/database/sessions"
        ),
    ) -> None:
        """
        Initialize the repository.

        Parameters
        ----------
        storage_root:
            Directory containing persisted session folders.

            Production default:

                storage/database/sessions

            Tests should provide an isolated temporary directory.
        """

        self.storage_root = Path(
            storage_root
        )

    # =========================================================
    # SAVE
    # =========================================================

    def save(
        self,
        snapshot: ExplorationSessionSnapshot,
    ) -> Path:
        """
        Save a complete session snapshot atomically.

        Flow:

            Serialize
                ↓
            Create session directory
                ↓
            Write session.json.tmp
                ↓
            Flush file contents
                ↓
            Atomic replace
                ↓
            session.json

        Returns
        -------
        Path:
            Final session.json path.
        """

        serialized = (
            SessionSerializer.serialize(
                snapshot
            )
        )

        session_directory = (
            self._get_session_directory(
                snapshot.session_id
            )
        )

        session_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        session_file = (
            session_directory
            /
            self.SESSION_FILE_NAME
        )

        temp_file = (
            session_directory
            /
            self.TEMP_FILE_NAME
        )

        try:

            with temp_file.open(
                "w",
                encoding="utf-8",
            ) as file:

                json.dump(
                    serialized,
                    file,
                    indent=2,
                    sort_keys=True,
                    ensure_ascii=False,
                )

                file.write(
                    "\n"
                )

                file.flush()

                os.fsync(
                    file.fileno()
                )

            os.replace(
                temp_file,
                session_file,
            )

        finally:

            # A failed write before os.replace() may leave a
            # temporary file.
            #
            # Never remove the existing valid session.json.
            if temp_file.exists():

                temp_file.unlink()

        return session_file

    # =========================================================
    # LOAD
    # =========================================================

    def load(
        self,
        session_id: str,
    ) -> ExplorationSessionSnapshot:
        """
        Load and reconstruct one persisted session.

        Raises
        ------
        FileNotFoundError:
            If the session does not exist.

        json.JSONDecodeError:
            If session.json contains invalid JSON.

        ValueError:
            If the serialized session is structurally invalid or
            uses an unsupported schema version.
        """

        session_file = (
            self._get_session_file(
                session_id
            )
        )

        if not session_file.is_file():

            raise FileNotFoundError(
                "Exploration session does not exist: "
                f"{session_id}"
            )

        with session_file.open(
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(
                file
            )

        return SessionSerializer.deserialize(
            data
        )

    # =========================================================
    # EXISTS
    # =========================================================

    def exists(
        self,
        session_id: str,
    ) -> bool:
        """
        Return True when a persisted session file exists.
        """

        return (
            self._get_session_file(
                session_id
            )
            .is_file()
        )

    # =========================================================
    # LIST
    # =========================================================

    def list_sessions(
        self,
    ) -> list[str]:
        """
        Return persisted session IDs in deterministic order.

        A directory is considered a stored session only when it
        contains session.json.

        Unrelated directories and temporary files are ignored.
        """

        if not self.storage_root.is_dir():

            return []

        session_ids = []

        for entry in (
            self.storage_root.iterdir()
        ):

            if not entry.is_dir():
                continue

            session_file = (
                entry
                /
                self.SESSION_FILE_NAME
            )

            if session_file.is_file():

                session_ids.append(
                    entry.name
                )

        return sorted(
            session_ids
        )

    # =========================================================
    # PATH HELPERS
    # =========================================================

    def _get_session_directory(
        self,
        session_id: str,
    ) -> Path:
        """
        Return the directory for one session.
        """

        self._validate_session_id(
            session_id
        )

        return (
            self.storage_root
            /
            session_id
        )

    def _get_session_file(
        self,
        session_id: str,
    ) -> Path:
        """
        Return session.json path for one session.
        """

        return (
            self._get_session_directory(
                session_id
            )
            /
            self.SESSION_FILE_NAME
        )

    # =========================================================
    # VALIDATION
    # =========================================================

    @staticmethod
    def _validate_session_id(
        session_id: str,
    ) -> None:
        """
        Reject invalid or unsafe filesystem session identifiers.

        Session IDs must represent one directory name only.

        Examples rejected:

            ""
            "../other"
            "folder/session"
            "folder\\session"
            "."
            ".."
        """

        if (
            not isinstance(
                session_id,
                str,
            )
            or
            not session_id.strip()
        ):

            raise ValueError(
                "session_id must be a non-empty string."
            )

        if session_id in {
            ".",
            "..",
        }:

            raise ValueError(
                "Invalid session_id."
            )

        if (
            "/"
            in session_id
            or
            "\\"
            in session_id
        ):

            raise ValueError(
                "session_id must not contain "
                "path separators."
            )