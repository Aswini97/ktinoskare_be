#!/usr/bin/env python
"""
Seed pet Species and PetBreed records through the Django ORM.

Run from the project root, usually inside the web container:
    python scripts/seed_species_breeds.py
    python scripts/seed_species_breeds.py --file scripts/species_breeds.sample.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ktinoscare.settings")

Species = None
PetBreed = None
transaction = None
timezone = None


DEFAULT_DATA: dict[str, list[dict[str, Any]]] = {
    "species": [
        {"name": "Dog"},
        {"name": "Cat"},
        {"name": "Cattle"},
        {"name": "Goat"},
        {"name": "Sheep"},
    ],
    "breeds": [
        {"name": "Labrador Retriever", "species": "Dog"},
        {"name": "German Shepherd", "species": "Dog"},
        {"name": "Golden Retriever", "species": "Dog"},
        {"name": "Persian", "species": "Cat"},
        {"name": "Siamese", "species": "Cat"},
        {"name": "Holstein Friesian", "species": "Cattle"},
        {"name": "Gir", "species": "Cattle"},
        {"name": "Boer", "species": "Goat"},
        {"name": "Jamunapari", "species": "Goat"},
        {"name": "Merino", "species": "Sheep"},
    ],
}


def clean_name(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string.")
    return value.strip()


def load_seed_data(path: Path | None, include_defaults: bool) -> dict[str, list[dict[str, Any]]]:
    data = {"species": [], "breeds": []}

    if include_defaults:
        data["species"].extend(DEFAULT_DATA["species"])
        data["breeds"].extend(DEFAULT_DATA["breeds"])

    if path:
        with path.open("r", encoding="utf-8") as seed_file:
            file_data = json.load(seed_file)
        data["species"].extend(file_data.get("species", []))
        data["breeds"].extend(file_data.get("breeds", []))

    return data


def resolve_species(breed_payload: dict[str, Any]) -> Species:
    dto_species_id = breed_payload.get("species_id")
    species_name = breed_payload.get("species") or breed_payload.get("species_name")

    if dto_species_id:
        return Species.objects.get(id=dto_species_id)

    if species_name:
        return Species.objects.get(name=clean_name(species_name, "breed.species"))

    raise ValueError(
        "Each breed needs a species reference. Use species, species_name, or species_id."
    )


def initialize_django() -> None:
    global PetBreed, Species, timezone, transaction

    import django
    from django.db import transaction as django_transaction
    from django.utils import timezone as django_timezone

    django.setup()

    from pets.models import PetBreed as PetBreedModel
    from pets.models import Species as SpeciesModel

    Species = SpeciesModel
    PetBreed = PetBreedModel
    transaction = django_transaction
    timezone = django_timezone


def revive_if_deleted(instance: Any) -> bool:
    if not instance.is_deleted:
        return False

    instance.is_deleted = False
    instance.deleted_at = None
    instance.save(update_fields=["is_deleted", "deleted_at"])
    return True


def seed(data: dict[str, list[dict[str, Any]]], dry_run: bool = False) -> dict[str, int]:
    stats = {
        "species_created": 0,
        "species_existing": 0,
        "species_revived": 0,
        "breeds_created": 0,
        "breeds_existing": 0,
        "breeds_revived": 0,
        "breeds_reassigned": 0,
    }

    with transaction.atomic():
        for species_payload in data["species"]:
            name = clean_name(species_payload.get("name"), "species.name")
            species, created = Species.objects.get_or_create(name=name)

            if created:
                stats["species_created"] += 1
            else:
                stats["species_existing"] += 1
                if revive_if_deleted(species):
                    stats["species_revived"] += 1

        for breed_payload in data["breeds"]:
            name = clean_name(breed_payload.get("name"), "breed.name")
            species = resolve_species(breed_payload)
            breed, created = PetBreed.objects.get_or_create(
                name=name,
                defaults={"species": species},
            )

            if created:
                stats["breeds_created"] += 1
                continue

            stats["breeds_existing"] += 1
            changed_fields = []

            if revive_if_deleted(breed):
                stats["breeds_revived"] += 1

            if breed.species_id != species.id:
                breed.species = species
                changed_fields.append("species")
                stats["breeds_reassigned"] += 1

            if changed_fields:
                breed.save(update_fields=changed_fields)

        if dry_run:
            transaction.set_rollback(True)

    return stats


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Insert Species and PetBreed records into the configured Django database."
    )
    parser.add_argument(
        "--file",
        type=Path,
        help="Optional JSON seed file with species and breeds arrays.",
    )
    parser.add_argument(
        "--no-defaults",
        action="store_true",
        help="Only insert records from --file, skipping built-in sample records.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and report changes without committing them.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.no_defaults and not args.file:
        print("--no-defaults requires --file.", file=sys.stderr)
        return 2

    try:
        initialize_django()
        data = load_seed_data(args.file, include_defaults=not args.no_defaults)
        stats = seed(data, dry_run=args.dry_run)
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"Seed failed: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        missing_species = (
            Species is not None
            and hasattr(Species, "DoesNotExist")
            and isinstance(exc, Species.DoesNotExist)
        )
        if missing_species:
            print(f"Missing species for a breed row: {exc}", file=sys.stderr)
            return 1

        print(f"Seed failed: {exc}", file=sys.stderr)
        return 1

    mode = "DRY RUN" if args.dry_run else "COMMITTED"
    print(f"{mode} at {timezone.now().isoformat()}")
    for key, value in stats.items():
        print(f"{key}: {value}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
