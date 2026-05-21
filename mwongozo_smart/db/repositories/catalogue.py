from __future__ import annotations

import json
import logging
from typing import Any

from mwongozo_smart.core.models import AdmissionRequirement, Institution, Programme
from mwongozo_smart.data import institution_classify
from mwongozo_smart.data import sqlite_store
from mwongozo_smart.db.catalogue_merge import merge_institutions, merge_programmes
from mwongozo_smart.db.config import CatalogueReadMode, CatalogueWriteMode, catalogue_read_mode, catalogue_write_mode
from mwongozo_smart.db.session import apply_catalogue_schema, mysql_connection, mysql_ping, mysql_table_exists

logger = logging.getLogger(__name__)

_REPOSITORY: CatalogueRepository | None = None


def _unique_by_code(items: list[Institution] | list[Programme]) -> list:
    unique: dict[str, object] = {}
    for item in items:
        unique[item.code] = item
    return list(unique.values())


def _institution_to_row(institution: Institution) -> dict[str, Any]:
    classified = institution_classify.classify_institution(institution)
    kind = classified.get("kind", "other")
    if kind not in ("university", "college", "institute", "other"):
        kind = "other"
    ownership = classified.get("ownership", "unknown")
    if ownership not in ("public", "private", "unknown"):
        ownership = "unknown"
    return {
        "code": institution.code,
        "name": institution.name,
        "city": institution.city,
        "region": institution.region,
        "website": institution.website,
        "apply_url": institution.apply_url,
        "cta_label": institution.cta_label,
        "ownership": ownership,
        "kind": kind,
    }


def _programme_to_rows(programme: Programme, institution_id: int) -> tuple[dict[str, Any], dict[str, Any]]:
    req = programme.admission_requirement
    programme_row = {
        "code": programme.code,
        "name": programme.name,
        "institution_id": institution_id,
        "city": programme.city,
        "region": programme.region,
        "category": programme.category.value,
        "award_level": programme.award_level.value,
        "duration_years": programme.duration_years,
        "capacity": programme.capacity,
        "competition_tier": programme.competition_tier,
        "tags": json.dumps(programme.tags, ensure_ascii=False),
        "source_reference": programme.source_reference,
        "guidebook_year": _guidebook_year_from_reference(programme.source_reference),
    }
    requirement_row = _requirement_to_row(req)
    return programme_row, requirement_row


def _guidebook_year_from_reference(source_reference: str) -> str | None:
    if "2025/2026" in source_reference:
        return "2025/2026"
    if "2024/2025" in source_reference:
        return "2024/2025"
    if "2023/2024" in source_reference:
        return "2023/2024"
    return None


def _requirement_to_row(req: AdmissionRequirement) -> dict[str, Any]:
    return {
        "minimum_principal_passes": req.minimum_principal_passes,
        "minimum_total_points": req.minimum_total_points,
        "minimum_o_level_passes": req.minimum_o_level_passes,
        "principal_pool_min_count": req.principal_pool_min_count,
        "strict": int(req.strict),
        "principal_subject_pool": json.dumps(req.principal_subject_pool, ensure_ascii=False),
        "required_principal_subjects": json.dumps(req.required_principal_subjects, ensure_ascii=False),
        "minimum_a_level_subject_grades": json.dumps(req.minimum_a_level_subject_grades, ensure_ascii=False),
        "minimum_o_level_subject_grades": json.dumps(req.minimum_o_level_subject_grades, ensure_ascii=False),
        "preferred_o_level_subjects": json.dumps(req.preferred_o_level_subjects, ensure_ascii=False),
        "conditional_requirements": json.dumps(
            [item.model_dump(mode="json") for item in req.conditional_requirements],
            ensure_ascii=False,
        ),
        "notes": json.dumps(req.notes, ensure_ascii=False),
    }


def _row_to_institution(row: dict[str, Any]) -> Institution:
    return Institution(
        code=row["code"],
        name=row["name"],
        city=row["city"],
        region=row["region"],
        website=row.get("website"),
        apply_url=row.get("apply_url"),
        cta_label=row.get("cta_label") or "Apply Now",
    )


def _json_list(value: Any) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        return json.loads(value)
    return list(value)


def _json_dict(value: Any) -> dict:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        return json.loads(value)
    return dict(value)


def _row_to_programme(row: dict[str, Any], req_row: dict[str, Any] | None) -> Programme:
    admission_requirement = AdmissionRequirement()
    if req_row:
        admission_requirement = AdmissionRequirement.model_validate(
            {
                "minimum_principal_passes": req_row["minimum_principal_passes"],
                "minimum_total_points": float(req_row["minimum_total_points"]),
                "minimum_o_level_passes": req_row["minimum_o_level_passes"],
                "principal_pool_min_count": req_row["principal_pool_min_count"],
                "strict": bool(req_row["strict"]),
                "principal_subject_pool": _json_list(req_row["principal_subject_pool"]),
                "required_principal_subjects": _json_list(req_row["required_principal_subjects"]),
                "minimum_a_level_subject_grades": _json_dict(req_row["minimum_a_level_subject_grades"]),
                "minimum_o_level_subject_grades": _json_dict(req_row["minimum_o_level_subject_grades"]),
                "preferred_o_level_subjects": _json_dict(req_row["preferred_o_level_subjects"]),
                "conditional_requirements": _json_list(req_row["conditional_requirements"]),
                "notes": _json_list(req_row["notes"]),
            }
        )
    return Programme(
        code=row["code"],
        name=row["name"],
        institution_code=row["institution_code"],
        institution_name=row["institution_name"],
        city=row["city"],
        region=row["region"],
        category=row["category"],
        award_level=row["award_level"],
        duration_years=row.get("duration_years"),
        capacity=row.get("capacity"),
        competition_tier=row["competition_tier"],
        admission_requirement=admission_requirement,
        tags=_json_list(row.get("tags")),
        source_reference=row.get("source_reference") or "",
    )


class MysqlCatalogueStore:
    def ensure_schema(self) -> None:
        with mysql_connection() as connection:
            apply_catalogue_schema(connection)

    def upsert_institutions(self, institutions: list[Institution]) -> int:
        self.ensure_schema()
        count = 0
        with mysql_connection() as connection:
            with connection.cursor() as cursor:
                for institution in institutions:
                    row = _institution_to_row(institution)
                    cursor.execute(
                        """
                        INSERT INTO institutions (
                            code, name, city, region, website, apply_url, cta_label,
                            ownership, kind, is_active, deleted_at
                        ) VALUES (
                            %(code)s, %(name)s, %(city)s, %(region)s, %(website)s, %(apply_url)s, %(cta_label)s,
                            %(ownership)s, %(kind)s, 1, NULL
                        )
                        ON DUPLICATE KEY UPDATE
                            name = VALUES(name),
                            city = VALUES(city),
                            region = VALUES(region),
                            website = VALUES(website),
                            apply_url = VALUES(apply_url),
                            cta_label = VALUES(cta_label),
                            ownership = VALUES(ownership),
                            kind = VALUES(kind),
                            is_active = 1,
                            deleted_at = NULL,
                            updated_at = CURRENT_TIMESTAMP(3)
                        """,
                        row,
                    )
                    count += 1
            connection.commit()
        return count

    def upsert_programmes(self, programmes: list[Programme]) -> int:
        self.ensure_schema()
        count = 0
        with mysql_connection() as connection:
            with connection.cursor() as cursor:
                for programme in programmes:
                    cursor.execute(
                        "SELECT id FROM institutions WHERE code = %s AND deleted_at IS NULL",
                        (programme.institution_code,),
                    )
                    inst_row = cursor.fetchone()
                    if not inst_row:
                        cursor.execute(
                            """
                            INSERT INTO institutions (code, name, city, region, ownership, kind, is_active)
                            VALUES (%s, %s, %s, %s, 'unknown', 'other', 1)
                            """,
                            (
                                programme.institution_code,
                                programme.institution_name,
                                programme.city,
                                programme.region,
                            ),
                        )
                        cursor.execute(
                            "SELECT id FROM institutions WHERE code = %s",
                            (programme.institution_code,),
                        )
                        inst_row = cursor.fetchone()
                    institution_id = int(inst_row["id"])
                    programme_row, requirement_row = _programme_to_rows(programme, institution_id)
                    cursor.execute(
                        """
                        INSERT INTO programmes (
                            code, name, institution_id, city, region, category, award_level,
                            duration_years, capacity, competition_tier, tags, source_reference,
                            guidebook_year, is_active, deleted_at
                        ) VALUES (
                            %(code)s, %(name)s, %(institution_id)s, %(city)s, %(region)s, %(category)s, %(award_level)s,
                            %(duration_years)s, %(capacity)s, %(competition_tier)s, %(tags)s, %(source_reference)s,
                            %(guidebook_year)s, 1, NULL
                        )
                        ON DUPLICATE KEY UPDATE
                            name = VALUES(name),
                            institution_id = VALUES(institution_id),
                            city = VALUES(city),
                            region = VALUES(region),
                            category = VALUES(category),
                            award_level = VALUES(award_level),
                            duration_years = VALUES(duration_years),
                            capacity = VALUES(capacity),
                            competition_tier = VALUES(competition_tier),
                            tags = VALUES(tags),
                            source_reference = VALUES(source_reference),
                            guidebook_year = VALUES(guidebook_year),
                            is_active = 1,
                            deleted_at = NULL,
                            updated_at = CURRENT_TIMESTAMP(3)
                        """,
                        programme_row,
                    )
                    cursor.execute("SELECT id FROM programmes WHERE code = %s", (programme.code,))
                    programme_id = int(cursor.fetchone()["id"])
                    requirement_row["programme_id"] = programme_id
                    cursor.execute(
                        """
                        INSERT INTO programme_requirements (
                            programme_id, minimum_principal_passes, minimum_total_points,
                            minimum_o_level_passes, principal_pool_min_count, strict,
                            principal_subject_pool, required_principal_subjects,
                            minimum_a_level_subject_grades, minimum_o_level_subject_grades,
                            preferred_o_level_subjects, conditional_requirements, notes
                        ) VALUES (
                            %(programme_id)s, %(minimum_principal_passes)s, %(minimum_total_points)s,
                            %(minimum_o_level_passes)s, %(principal_pool_min_count)s, %(strict)s,
                            %(principal_subject_pool)s, %(required_principal_subjects)s,
                            %(minimum_a_level_subject_grades)s, %(minimum_o_level_subject_grades)s,
                            %(preferred_o_level_subjects)s, %(conditional_requirements)s, %(notes)s
                        )
                        ON DUPLICATE KEY UPDATE
                            minimum_principal_passes = VALUES(minimum_principal_passes),
                            minimum_total_points = VALUES(minimum_total_points),
                            minimum_o_level_passes = VALUES(minimum_o_level_passes),
                            principal_pool_min_count = VALUES(principal_pool_min_count),
                            strict = VALUES(strict),
                            principal_subject_pool = VALUES(principal_subject_pool),
                            required_principal_subjects = VALUES(required_principal_subjects),
                            minimum_a_level_subject_grades = VALUES(minimum_a_level_subject_grades),
                            minimum_o_level_subject_grades = VALUES(minimum_o_level_subject_grades),
                            preferred_o_level_subjects = VALUES(preferred_o_level_subjects),
                            conditional_requirements = VALUES(conditional_requirements),
                            notes = VALUES(notes),
                            updated_at = CURRENT_TIMESTAMP(3)
                        """,
                        requirement_row,
                    )
                    count += 1
            connection.commit()
        return count

    def fetch_institutions(self) -> list[Institution]:
        if not mysql_table_exists("institutions"):
            self.ensure_schema()
        with mysql_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT code, name, city, region, website, apply_url, cta_label
                    FROM institutions
                    WHERE deleted_at IS NULL AND is_active = 1
                    ORDER BY code
                    """
                )
                rows = cursor.fetchall()
        return [_row_to_institution(row) for row in rows]

    def fetch_programmes(self) -> list[Programme]:
        if not mysql_table_exists("programmes"):
            self.ensure_schema()
        with mysql_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        p.code, p.name, p.city, p.region, p.category, p.award_level,
                        p.duration_years, p.capacity, p.competition_tier, p.tags, p.source_reference,
                        i.code AS institution_code, i.name AS institution_name
                    FROM programmes p
                    JOIN institutions i ON i.id = p.institution_id
                    WHERE p.deleted_at IS NULL AND p.is_active = 1
                      AND i.deleted_at IS NULL AND i.is_active = 1
                    ORDER BY p.code
                    """
                )
                programme_rows = cursor.fetchall()
                cursor.execute(
                    """
                    SELECT pr.*, p.code AS programme_code
                    FROM programme_requirements pr
                    JOIN programmes p ON p.id = pr.programme_id
                    WHERE p.deleted_at IS NULL AND p.is_active = 1
                    """
                )
                requirement_rows = cursor.fetchall()
        req_by_code = {row["programme_code"]: row for row in requirement_rows}
        programmes: list[Programme] = []
        for row in programme_rows:
            programmes.append(_row_to_programme(row, req_by_code.get(row["code"])))
        return programmes


class CatalogueRepository:
    def __init__(
        self,
        read_mode: CatalogueReadMode | None = None,
        write_mode: CatalogueWriteMode | None = None,
        mysql_store: MysqlCatalogueStore | None = None,
    ) -> None:
        self._read_mode = read_mode or catalogue_read_mode()
        self._write_mode = write_mode or catalogue_write_mode()
        self._mysql = mysql_store or MysqlCatalogueStore()

    def load_institutions(self, defaults: list[Institution] | None = None) -> list[Institution]:
        defaults = list(_unique_by_code(list(defaults or [])))
        if self._read_mode == CatalogueReadMode.MYSQL:
            loaded = self._mysql.fetch_institutions()
            return merge_institutions(defaults, loaded) if defaults else loaded

        sqlite_result = sqlite_store.load_institutions(defaults, seed_defaults=False)

        if self._read_mode == CatalogueReadMode.SQLITE_WITH_MYSQL_VERIFY and mysql_ping():
            try:
                mysql_loaded = self._mysql.fetch_institutions()
                mysql_merged = merge_institutions(defaults, mysql_loaded) if defaults else mysql_loaded
                _log_catalogue_diff("institutions", sqlite_result, mysql_merged)
            except Exception:
                logger.exception("MySQL catalogue verify failed for institutions")

        return sqlite_result

    def load_programmes(self, defaults: list[Programme] | None = None) -> list[Programme]:
        defaults = list(_unique_by_code(list(defaults or [])))
        if self._read_mode == CatalogueReadMode.MYSQL:
            loaded = self._mysql.fetch_programmes()
            return merge_programmes(defaults, loaded) if defaults else loaded

        sqlite_result = sqlite_store.load_programmes(defaults, seed_defaults=False)

        if self._read_mode == CatalogueReadMode.SQLITE_WITH_MYSQL_VERIFY and mysql_ping():
            try:
                mysql_loaded = self._mysql.fetch_programmes()
                mysql_merged = merge_programmes(defaults, mysql_loaded) if defaults else mysql_loaded
                _log_catalogue_diff("programmes", sqlite_result, mysql_merged)
            except Exception:
                logger.exception("MySQL catalogue verify failed for programmes")

        return sqlite_result

    def seed_institutions(self, items: list[Institution]) -> None:
        items = list(_unique_by_code(items))
        if self._write_mode in (CatalogueWriteMode.SQLITE, CatalogueWriteMode.DUAL):
            sqlite_store.seed_institutions(items)
        if self._write_mode in (CatalogueWriteMode.MYSQL, CatalogueWriteMode.DUAL):
            self._mysql.upsert_institutions(items)

    def seed_programmes(self, items: list[Programme]) -> None:
        items = list(_unique_by_code(items))
        if self._write_mode in (CatalogueWriteMode.SQLITE, CatalogueWriteMode.DUAL):
            sqlite_store.seed_programmes(items)
        if self._write_mode in (CatalogueWriteMode.MYSQL, CatalogueWriteMode.DUAL):
            self._mysql.upsert_programmes(items)


def _log_catalogue_diff(kind: str, sqlite_items: list, mysql_items: list) -> None:
    sqlite_codes = {item.code for item in sqlite_items}
    mysql_codes = {item.code for item in mysql_items}
    missing_in_mysql = sqlite_codes - mysql_codes
    extra_in_mysql = mysql_codes - sqlite_codes
    if missing_in_mysql or extra_in_mysql:
        logger.warning(
            "Catalogue parity mismatch (%s): missing_in_mysql=%s extra_in_mysql=%s",
            kind,
            sorted(missing_in_mysql)[:10],
            sorted(extra_in_mysql)[:10],
        )


def get_catalogue_repository() -> CatalogueRepository:
    global _REPOSITORY
    if _REPOSITORY is None:
        _REPOSITORY = CatalogueRepository()
    return _REPOSITORY
