from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Iterable


NETWORK_DIR = Path(__file__).resolve().parent
DB_PATH = NETWORK_DIR / "network.db"
LEGACY_DB_PATH = NETWORK_DIR / "Agencies.db"


def _slugify(value: str) -> str:
    return "-".join(value.strip().lower().split())


class NetworkDB:
    def __init__(self, db_path: Path | None = None, migrate_legacy: bool = False) -> None:
        self.db_path = Path(db_path) if db_path else DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._ensure_schema()
        if migrate_legacy:
            self._migrate_legacy()

    def close(self) -> None:
        self.conn.close()

    def query(self, sql: str, params: Iterable[Any] = ()) -> list[dict[str, Any]]:
        cursor = self.conn.execute(sql, tuple(params))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def summary(self) -> dict[str, int]:
        counts = {
            "agencies": self._count("agencies"),
            "contacts": self._count("contacts"),
            "people": self._count("people"),
            "sources": self._count("person_sources"),
            "opportunities": self._count("opportunities"),
            "matches": self._count("person_opportunity_matches"),
        }
        print(json.dumps(counts, indent=2))
        return counts

    def reset(self) -> None:
        self.close()
        if self.db_path.exists():
            self.db_path.unlink()
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._ensure_schema()

    def get_person(self, slug: str) -> dict[str, Any] | None:
        rows = self.query("SELECT * FROM people WHERE slug = ?", (slug,))
        return rows[0] if rows else None

    def upsert_person(
        self,
        *,
        full_name: str,
        slug: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        current_role: str | None = None,
        current_company: str | None = None,
        linkedin_url: str | None = None,
        email: str | None = None,
        location: str | None = None,
        profile_summary: str | None = None,
        relationship_type: str | None = None,
        opportunity_signal: str | None = None,
        source_confidence: str = "medium",
        tags_json: str | None = None,
        profile_data_json: str | None = None,
    ) -> int:
        resolved_slug = slug or _slugify(full_name)
        self.conn.execute(
            """
            INSERT INTO people (
                slug, full_name, first_name, last_name, current_role, current_company,
                linkedin_url, email, location, profile_summary, relationship_type,
                opportunity_signal, source_confidence, tags_json, profile_data_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(slug) DO UPDATE SET
                full_name = excluded.full_name,
                first_name = excluded.first_name,
                last_name = excluded.last_name,
                current_role = excluded.current_role,
                current_company = excluded.current_company,
                linkedin_url = excluded.linkedin_url,
                email = excluded.email,
                location = excluded.location,
                profile_summary = excluded.profile_summary,
                relationship_type = excluded.relationship_type,
                opportunity_signal = excluded.opportunity_signal,
                source_confidence = excluded.source_confidence,
                tags_json = excluded.tags_json,
                profile_data_json = excluded.profile_data_json,
                updated_at = datetime('now', 'utc')
            """,
            (
                resolved_slug,
                full_name,
                first_name,
                last_name,
                current_role,
                current_company,
                linkedin_url,
                email,
                location,
                profile_summary,
                relationship_type,
                opportunity_signal,
                source_confidence,
                tags_json,
                profile_data_json,
            ),
        )
        self.conn.commit()
        row = self.conn.execute("SELECT id FROM people WHERE slug = ?", (resolved_slug,)).fetchone()
        return int(row[0])

    def add_person_source(
        self,
        *,
        person_id: int,
        source_type: str,
        source_url: str | None = None,
        source_title: str | None = None,
        source_snippet: str | None = None,
    ) -> int:
        cursor = self.conn.execute(
            """
            INSERT INTO person_sources (person_id, source_type, source_url, source_title, source_snippet)
            VALUES (?, ?, ?, ?, ?)
            """,
            (person_id, source_type, source_url, source_title, source_snippet),
        )
        self.conn.commit()
        return int(cursor.lastrowid)

    def upsert_opportunity(
        self,
        *,
        name: str,
        slug: str | None = None,
        description: str | None = None,
        ideal_profile: str | None = None,
        keywords_json: str | None = None,
        status: str = "active",
    ) -> int:
        resolved_slug = slug or _slugify(name)
        self.conn.execute(
            """
            INSERT INTO opportunities (slug, name, description, ideal_profile, keywords_json, status)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(slug) DO UPDATE SET
                name = excluded.name,
                description = excluded.description,
                ideal_profile = excluded.ideal_profile,
                keywords_json = excluded.keywords_json,
                status = excluded.status,
                updated_at = datetime('now', 'utc')
            """,
            (resolved_slug, name, description, ideal_profile, keywords_json, status),
        )
        self.conn.commit()
        row = self.conn.execute("SELECT id FROM opportunities WHERE slug = ?", (resolved_slug,)).fetchone()
        return int(row[0])

    def upsert_person_opportunity_match(
        self,
        *,
        person_id: int,
        opportunity_id: int,
        match_score: int,
        match_type: str,
        rationale: str,
        next_step: str | None = None,
        status: str = "open",
    ) -> int:
        self.conn.execute(
            """
            INSERT INTO person_opportunity_matches (
                person_id, opportunity_id, match_score, match_type, rationale, next_step, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(person_id, opportunity_id) DO UPDATE SET
                match_score = excluded.match_score,
                match_type = excluded.match_type,
                rationale = excluded.rationale,
                next_step = excluded.next_step,
                status = excluded.status,
                updated_at = datetime('now', 'utc')
            """,
            (person_id, opportunity_id, match_score, match_type, rationale, next_step, status),
        )
        self.conn.commit()
        row = self.conn.execute(
            "SELECT id FROM person_opportunity_matches WHERE person_id = ? AND opportunity_id = ?",
            (person_id, opportunity_id),
        ).fetchone()
        return int(row[0])

    def _count(self, table_name: str) -> int:
        return int(self.conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0])

    def _ensure_schema(self) -> None:
        statements = [
            """
            CREATE TABLE IF NOT EXISTS agencies (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                name             TEXT NOT NULL,
                domain           TEXT UNIQUE NOT NULL,
                apollo_name      TEXT,
                employees        INTEGER,
                industry         TEXT,
                revenue          INTEGER,
                founded          INTEGER,
                linkedin         TEXT,
                city             TEXT,
                country          TEXT,
                keywords         TEXT,
                technologies     TEXT,
                priority         TEXT DEFAULT 'UNKNOWN',
                enrichment_error TEXT,
                enriched_at      TEXT,
                created_at       TEXT NOT NULL DEFAULT (datetime('now','utc')),
                updated_at       TEXT NOT NULL DEFAULT (datetime('now','utc'))
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS contacts (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                agency_id         INTEGER NOT NULL REFERENCES agencies(id) ON DELETE CASCADE,
                first_name        TEXT NOT NULL,
                last_name         TEXT NOT NULL,
                title             TEXT,
                email             TEXT,
                linkedin_url      TEXT,
                apollo_contact_id TEXT,
                notes             TEXT,
                created_at        TEXT NOT NULL DEFAULT (datetime('now','utc')),
                updated_at        TEXT NOT NULL DEFAULT (datetime('now','utc'))
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS discovery_notes (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                agency_id        INTEGER NOT NULL REFERENCES agencies(id) ON DELETE CASCADE,
                contact_id       INTEGER REFERENCES contacts(id) ON DELETE SET NULL,
                date             TEXT NOT NULL,
                pain_intensity   INTEGER CHECK(pain_intensity BETWEEN 1 AND 5),
                current_process  TEXT,
                error_frequency  TEXT,
                cost_signal      TEXT,
                wtp_signal       TEXT,
                best_quote       TEXT,
                follow_up        INTEGER NOT NULL DEFAULT 0,
                notes            TEXT,
                created_at       TEXT NOT NULL DEFAULT (datetime('now','utc'))
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS outreach (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_id       INTEGER NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
                channel          TEXT NOT NULL CHECK(channel IN ('email','linkedin','in_person','phone')),
                sent_at          TEXT NOT NULL,
                response_at      TEXT,
                response_type    TEXT CHECK(response_type IN (
                                     'no_response','interested','not_interested','meeting_booked','unsubscribed'
                                   )),
                notes            TEXT,
                created_at       TEXT NOT NULL DEFAULT (datetime('now','utc'))
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS people (
                id                 INTEGER PRIMARY KEY AUTOINCREMENT,
                slug               TEXT UNIQUE NOT NULL,
                full_name          TEXT NOT NULL,
                first_name         TEXT,
                last_name          TEXT,
                current_role       TEXT,
                current_company    TEXT,
                linkedin_url       TEXT,
                email              TEXT,
                location           TEXT,
                profile_summary    TEXT,
                relationship_type  TEXT,
                opportunity_signal TEXT,
                source_confidence  TEXT DEFAULT 'medium',
                tags_json          TEXT,
                profile_data_json  TEXT,
                created_at         TEXT NOT NULL DEFAULT (datetime('now','utc')),
                updated_at         TEXT NOT NULL DEFAULT (datetime('now','utc'))
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS person_sources (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                person_id      INTEGER NOT NULL REFERENCES people(id) ON DELETE CASCADE,
                source_type    TEXT NOT NULL,
                source_url     TEXT,
                source_title   TEXT,
                source_snippet TEXT,
                captured_at    TEXT NOT NULL DEFAULT (datetime('now','utc'))
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS opportunities (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                slug          TEXT UNIQUE NOT NULL,
                name          TEXT NOT NULL,
                description   TEXT,
                ideal_profile TEXT,
                keywords_json TEXT,
                status        TEXT DEFAULT 'active',
                created_at    TEXT NOT NULL DEFAULT (datetime('now','utc')),
                updated_at    TEXT NOT NULL DEFAULT (datetime('now','utc'))
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS person_opportunity_matches (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                person_id      INTEGER NOT NULL REFERENCES people(id) ON DELETE CASCADE,
                opportunity_id INTEGER NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
                match_score    INTEGER NOT NULL,
                match_type     TEXT NOT NULL,
                rationale      TEXT NOT NULL,
                next_step      TEXT,
                status         TEXT DEFAULT 'open',
                created_at     TEXT NOT NULL DEFAULT (datetime('now','utc')),
                updated_at     TEXT NOT NULL DEFAULT (datetime('now','utc')),
                UNIQUE(person_id, opportunity_id)
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_agencies_domain ON agencies(domain)",
            "CREATE INDEX IF NOT EXISTS idx_agencies_priority ON agencies(priority)",
            "CREATE INDEX IF NOT EXISTS idx_contacts_agency ON contacts(agency_id)",
            "CREATE INDEX IF NOT EXISTS idx_discovery_agency ON discovery_notes(agency_id)",
            "CREATE INDEX IF NOT EXISTS idx_outreach_contact ON outreach(contact_id)",
            "CREATE INDEX IF NOT EXISTS idx_people_company ON people(current_company)",
            "CREATE INDEX IF NOT EXISTS idx_people_relationship_type ON people(relationship_type)",
            "CREATE INDEX IF NOT EXISTS idx_match_score ON person_opportunity_matches(match_score)",
            "DROP VIEW IF EXISTS individual_network",
            """
            CREATE VIEW individual_network AS
            SELECT
                people.id AS network_person_id,
                people.slug AS network_handle,
                people.full_name AS full_name,
                people.first_name AS first_name,
                people.last_name AS last_name,
                people.current_role AS role_title,
                people.current_company AS organization,
                people.relationship_type AS network_role,
                people.email AS primary_email,
                people.linkedin_url AS linkedin_profile,
                people.location AS location,
                people.profile_summary AS profile_summary,
                people.opportunity_signal AS opportunity_signal,
                people.source_confidence AS source_confidence,
                people.tags_json AS tags,
                people.profile_data_json AS profile_data,
                COUNT(person_sources.id) AS source_count,
                MIN(person_sources.source_url) AS first_source_url,
                people.created_at AS created_at,
                people.updated_at AS updated_at
            FROM people
            LEFT JOIN person_sources ON person_sources.person_id = people.id
            GROUP BY
                people.id,
                people.slug,
                people.full_name,
                people.first_name,
                people.last_name,
                people.current_role,
                people.current_company,
                people.relationship_type,
                people.email,
                people.linkedin_url,
                people.location,
                people.profile_summary,
                people.opportunity_signal,
                people.source_confidence,
                people.tags_json,
                people.profile_data_json,
                people.created_at,
                people.updated_at
            """,
        ]
        with self.conn:
            for statement in statements:
                self.conn.execute(statement)

    def _migrate_legacy(self) -> None:
        if not LEGACY_DB_PATH.exists() or LEGACY_DB_PATH.resolve() == self.db_path.resolve():
            return
        if any(self._count(table) for table in ("agencies", "contacts", "discovery_notes", "outreach")):
            return
        self.conn.execute("ATTACH DATABASE ? AS legacy", (str(LEGACY_DB_PATH),))
        try:
            for table in ("agencies", "contacts", "discovery_notes", "outreach"):
                if not self._table_exists("legacy", table):
                    continue
                target_columns = self._table_columns("main", table)
                legacy_columns = self._table_columns("legacy", table)
                common_columns = [column for column in target_columns if column in legacy_columns]
                if not common_columns:
                    continue
                column_sql = ", ".join(common_columns)
                self.conn.execute(
                    f"INSERT INTO {table} ({column_sql}) SELECT {column_sql} FROM legacy.{table}"
                )
            self.conn.commit()
        finally:
            self.conn.execute("DETACH DATABASE legacy")

    def _table_columns(self, schema_name: str, table_name: str) -> list[str]:
        cursor = self.conn.execute(f"PRAGMA {schema_name}.table_info({table_name})")
        return [row[1] for row in cursor.fetchall()]

    def _table_exists(self, schema_name: str, table_name: str) -> bool:
        row = self.conn.execute(
            f"SELECT 1 FROM {schema_name}.sqlite_master WHERE type = 'table' AND name = ?",
            (table_name,),
        ).fetchone()
        return row is not None


if __name__ == "__main__":
    NetworkDB(migrate_legacy=False).summary()