import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("build", Path(__file__).resolve().parents[1] / "scripts/build.py")
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


class Validation(unittest.TestCase):
    def test_subnet_location_and_optional_fields(self):
        result = build.validate_locations({"165.217.165.0/25": {"country": "de", "region": "DE-HE", "city": "Frankfurt am Main"}}, ["165.217.165.0/24"])
        self.assertEqual(result[0], ["165.217.165.0/25", "DE", "DE-HE", "Frankfurt am Main", ""])

    def test_unrelated_or_invalid_data_rejected(self):
        for mapping in [{"8.8.8.0/24": {"country": "DE"}}, {"165.217.165.1/24": {"country": "DE"}}, {"165.217.165.0/24": {"country": "EU"}}, {"165.217.165.0/24": {"country": "DE", "region": "NL-LI"}}, {"165.217.165.0/24": {"country": "DE", "city": "Bad\nRow"}}]:
            with self.subTest(mapping=mapping), self.assertRaises(ValueError):
                build.validate_locations(mapping, ["165.217.165.0/24"])

    def test_ipv6_and_empty_feed(self):
        self.assertEqual(build.validate_locations({}, ["2a14:7582:d000::/36"]), [])
        self.assertEqual(len(build.validate_locations({"2a14:7582:d001::/48": {"country": "NL"}}, ["2a14:7582:d000::/36"])), 1)


if __name__ == "__main__":
    unittest.main()
