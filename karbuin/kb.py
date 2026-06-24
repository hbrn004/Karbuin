"""KnowledgeBase — loads seed JSON files and provides indexed access."""
import json
from pathlib import Path


class KnowledgeBase:
    def __init__(self, data_dir: str | Path):
        self.data_dir = Path(data_dir)
        # Load all seed files
        self.motor = self._load("motor.json")
        self.komponen = self._load("komponen.json")
        self.gejala = self._load("gejala.json")
        self.penyebab = self._load("penyebab.json")
        self.relasi = self._load("relasi_gejala_penyebab.json")
        self.solusi = self._load("solusi.json")
        self.harga = self._load("harga.json")
        self.lokasi_komponen = self._load("lokasi_komponen.json")
        self.image_component = self._load("image_component.json")
        self.sumber_referensi = self._load("sumber_referensi.json")
        # v1.2.2: load synonym groups (was missing — wired in integration sprint)
        self.synonym_groups = self._load("synonym_groups.json")

        # Indexes by id
        self.motor_dict = {m["id"]: m for m in self.motor}
        self.komponen_dict = {k["id"]: k for k in self.komponen}
        self.gejala_dict = {g["id"]: g for g in self.gejala}
        self.penyebab_dict = {p["id"]: p for p in self.penyebab}
        self.sumber_dict = {s["id"]: s for s in self.sumber_referensi}

        # v1.2.2: synonym group indexes
        # phrase_lower -> (canonical_id, group_name, base_conf=0.9)
        self.synonym_phrase_index: dict[str, tuple[str, str, float]] = {}
        for grp in self.synonym_groups.get("groups", []):
            cid = grp["canonical_id"]
            gname = grp["name"]
            for phrase in grp.get("phrases", []):
                p = phrase.lower().strip()
                if p and p not in self.synonym_phrase_index:
                    self.synonym_phrase_index[p] = (cid, gname, 0.9)

    def _load(self, filename: str):
        path = self.data_dir / filename
        return json.loads(path.read_text(encoding="utf-8"))

    # -------- lookups --------
    def get_motor(self, motor_id: str):
        return self.motor_dict.get(motor_id)

    def get_komponen(self, komp_id: str):
        return self.komponen_dict.get(komp_id)

    def get_gejala(self, geja_id: str):
        return self.gejala_dict.get(geja_id)

    def get_penyebab(self, peny_id: str):
        return self.penyebab_dict.get(peny_id)

    def get_source(self, source_id: str):
        return self.sumber_dict.get(source_id)

    def get_solutions_for_cause(self, cause_id: str):
        return [s for s in self.solusi if s["cause_id"] == cause_id]

    def get_prices_for_component(self, komp_id: str):
        return [h for h in self.harga if h["item_id"] == komp_id]

    def get_images_for_component(self, komp_id: str, motor_id: str | None = None):
        """Return images. Prefer motor-specific verified, fallback to generic verified."""
        # Filter for verified + component match
        all_match = [
            i for i in self.image_component
            if i["component_id"] == komp_id and i["verified"]
        ]
        if not all_match:
            return []
        # Motor-specific first
        if motor_id:
            motor_specific = [i for i in all_match if i.get("motor_specific") == motor_id]
            if motor_specific:
                return motor_specific
        # Fallback to generic (no motor_specific)
        generic = [i for i in all_match if not i.get("motor_specific")]
        return generic

    def get_location(self, motor_id: str, komp_id: str):
        """Return verified location for motor×component, or None."""
        for loc in self.lokasi_komponen:
            if (loc["motor_id"] == motor_id
                    and loc["component_id"] == komp_id
                    and loc["verified"]):
                return loc
        return None

    def get_locations_for_motor(self, motor_id: str):
        """Return all verified locations for a motor."""
        return [l for l in self.lokasi_komponen
                if l["motor_id"] == motor_id and l["verified"]]

    # -------- stats --------
    def coverage_stats(self) -> dict:
        """Compute coverage statistics for the knowledge base."""
        relasi_verified = sum(1 for r in self.relasi if r.get("verified"))
        lokasi_verified = sum(1 for l in self.lokasi_komponen if l.get("verified"))
        image_verified = sum(1 for i in self.image_component if i.get("verified"))
        harga_verified = sum(1 for h in self.harga if h.get("verified"))

        # Matrix: for each motor, how many unique causes reachable?
        motor_coverage = {}
        for motor in self.motor:
            mid = motor["id"]
            reachable_causes = set()
            for rel in self.relasi:
                if self._rel_applies(rel, mid):
                    reachable_causes.add(rel["cause_id"])
            motor_coverage[mid] = {
                "model": motor["model"],
                "reachable_causes": len(reachable_causes),
                "verified_lokasi": sum(
                    1 for l in self.lokasi_komponen
                    if l["motor_id"] == mid and l["verified"]
                ),
                "total_lokasi": sum(
                    1 for l in self.lokasi_komponen if l["motor_id"] == mid
                ),
            }

        return {
            "motor": len(self.motor),
            "komponen": len(self.komponen),
            "gejala": len(self.gejala),
            "penyebab": len(self.penyebab),
            "relasi": len(self.relasi),
            "relasi_verified": relasi_verified,
            "solusi": len(self.solusi),
            "harga": len(self.harga),
            "harga_verified": harga_verified,
            "lokasi_total": len(self.lokasi_komponen),
            "lokasi_verified": lokasi_verified,
            "image_total": len(self.image_component),
            "image_verified": image_verified,
            "sumber_referensi": len(self.sumber_referensi),
            "motor_coverage": motor_coverage,
        }

    def _rel_applies(self, rel, motor_id):
        mf = rel.get("motor_filter")
        if mf is None:
            return True
        for pattern in mf:
            if pattern == motor_id:
                return True
            if pattern.endswith("*") and motor_id.startswith(pattern[:-1]):
                return True
            if pattern.startswith("*") and motor_id.endswith(pattern[1:]):
                return True
        return False