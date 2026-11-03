import json
import unittest
from decimal import Decimal
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from profile_projection import PURPOSE_FIELDS, project_profile, project_synthetic_full_for_benchmark


HERE = Path(__file__).resolve().parent


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"), parse_float=Decimal)


class ProjectionSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.remote_schema = read_json(HERE / "profile-projection.schema.json")
        cls.consent_schema = read_json(HERE / "projection-consent.schema.json")
        cls.benchmark_schema = read_json(HERE / "synthetic-benchmark-projection.schema.json")
        cls.local_schema = read_json(
            HERE / "../../planificacion-03/05-perfil-conversacion/perfil.schema.json"
        )
        cls.remote_validator = Draft202012Validator(cls.remote_schema)
        cls.consent_validator = Draft202012Validator(cls.consent_schema)
        registry = Registry().with_resource(
            cls.remote_schema["$id"], Resource.from_contents(cls.remote_schema)
        )
        cls.benchmark_validator = Draft202012Validator(cls.benchmark_schema, registry=registry)

    def test_all_schemas_are_valid_without_network_resolution(self):
        for schema in (
            self.remote_schema,
            self.consent_schema,
            self.benchmark_schema,
            self.local_schema,
        ):
            with self.subTest(title=schema.get("title")):
                Draft202012Validator.check_schema(schema)

    def test_remote_projection_schema_rejects_extra_properties_and_wrong_purpose(self):
        projection = {
            "contract_version": "0.1",
            "purpose": "learn_basics",
            "fields": {"objective": {"state": "known", "value": "learn_concepts"}},
        }
        self.assertTrue(self.remote_validator.is_valid(projection))

        extra_top = {**projection, "profile_context": {"monthly_income_eur": "5000"}}
        extra_field = {**projection, "fields": {**projection["fields"], "email": {"state": "unknown"}}}
        extra_answer = {
            **projection,
            "fields": {"objective": {"state": "known", "value": "learn_concepts", "comment": "extra"}},
        }
        wrong_purpose = {
            "contract_version": "0.1",
            "purpose": "learn_basics",
            "fields": {"debt": {"state": "unknown"}},
        }
        for invalid in (extra_top, extra_field, extra_answer, wrong_purpose):
            with self.subTest(instance=invalid):
                self.assertFalse(self.remote_validator.is_valid(invalid))

    def test_consent_schema_is_closed_and_keeps_rejection_representable(self):
        refusal = {
            "notice_version": "notice-v1",
            "accepted_chat_processing": False,
            "purpose": "learn_basics",
            "approved_fields": [],
        }
        self.assertTrue(self.consent_validator.is_valid(refusal))
        self.assertFalse(
            self.consent_validator.is_valid({**refusal, "approved_fields": ["objective"]})
        )
        accepted = {**refusal, "accepted_chat_processing": True, "approved_fields": ["objective"]}
        self.assertTrue(self.consent_validator.is_valid(accepted))
        self.assertFalse(self.consent_validator.is_valid({**refusal, "share_all": True}))
        self.assertFalse(
            self.consent_validator.is_valid(
                {**accepted, "approved_fields": ["objective", "debt"]}
            )
        )

    def test_each_purpose_projection_conforms_to_closed_remote_schema(self):
        fixture = read_json(HERE / "fixtures/synthetic-full-profile.json")
        profile = fixture["profile"]
        for purpose, allowed in PURPOSE_FIELDS.items():
            selected = sorted(allowed)
            consent = {
                "notice_version": "notice-v1",
                "accepted_chat_processing": True,
                "purpose": purpose,
                "approved_fields": selected,
            }
            with self.subTest(purpose=purpose):
                projection = project_profile(
                    profile,
                    purpose=purpose,
                    selected_fields=selected,
                    consent=consent,
                )
                self.remote_validator.validate(projection)

    def test_full_fixture_is_valid_local_but_benchmark_dto_is_not_production_dto(self):
        fixture = read_json(HERE / "fixtures/synthetic-full-profile.json")
        local_profile = fixture["profile"]
        Draft202012Validator(self.local_schema).validate(local_profile)

        benchmark = project_synthetic_full_for_benchmark(fixture)
        self.benchmark_validator.validate(benchmark)
        self.assertFalse(self.remote_validator.is_valid(benchmark))
        self.assertEqual(benchmark["fields"]["monthly_income_eur"]["value"]["amount"]["min_eur"], "2800.00")


if __name__ == "__main__":
    unittest.main()
