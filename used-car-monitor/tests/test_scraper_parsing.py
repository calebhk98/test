"""Direct tests for the shared scraper parsing/coercion toolkit.

These exercise `carmon/scrapers/parsing.py` on its own, independent of any one adapter.
The seven `tests/test_scraper_*.py` adapter suites are the real proof that refactoring the
adapters to use this module did not change behaviour; this file is the proof that the
shared module itself is correct and robust to malformed input.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from carmon.scrapers import parsing


class ToIntTests(unittest.TestCase):
    def test_money_string(self) -> None:
        self.assertEqual(parsing.to_int("$18,995"), 18995)

    def test_mileage_with_unit_suffix(self) -> None:
        self.assertEqual(parsing.to_int("37,412 mi."), 37412)
        self.assertEqual(parsing.to_int("37,412 miles"), 37412)

    def test_k_suffix_mileage(self) -> None:
        self.assertEqual(parsing.to_int("37K mi"), 37000)
        self.assertEqual(parsing.to_int("12.5k"), 12500)

    def test_plain_numeric_types_pass_through(self) -> None:
        self.assertEqual(parsing.to_int(18995), 18995)
        self.assertEqual(parsing.to_int(18995.0), 18995)

    def test_unparseable_returns_none(self) -> None:
        self.assertIsNone(parsing.to_int("call for price"))
        self.assertIsNone(parsing.to_int(None))
        self.assertIsNone(parsing.to_int(True))  # bool is never a number here

    def test_sign_is_discarded_not_preserved(self) -> None:
        # to_int is the UNSIGNED coercion -- see module docstring. A stray leading '-'
        # (e.g. a bullet or phone-style dash) is stripped like any other non-digit.
        self.assertEqual(parsing.to_int("-1200"), 1200)


class ToSignedIntTests(unittest.TestCase):
    def test_negative_delta(self) -> None:
        self.assertEqual(parsing.to_signed_int("-1200"), -1200)
        self.assertEqual(parsing.to_signed_int("-1,200 below market"), -1200)
        # A '-' not immediately followed by a digit (e.g. before a currency symbol) is not
        # picked up as a sign -- the regex requires '-' directly against the first digit.
        self.assertEqual(parsing.to_signed_int("-$1,200"), 1200)

    def test_positive_first_number_wins(self) -> None:
        self.assertEqual(parsing.to_signed_int("$18,995 (was $20,000)"), 18995)

    def test_unparseable_returns_none(self) -> None:
        self.assertIsNone(parsing.to_signed_int("no numbers here"))
        self.assertIsNone(parsing.to_signed_int(None))
        self.assertIsNone(parsing.to_signed_int(True))


class ToFloatTests(unittest.TestCase):
    def test_comma_separated_decimal(self) -> None:
        self.assertEqual(parsing.to_float("1,234.5"), 1234.5)

    def test_int_and_float_pass_through(self) -> None:
        self.assertEqual(parsing.to_float(12), 12.0)
        self.assertEqual(parsing.to_float(12.5), 12.5)

    def test_unparseable_and_wrong_type_return_none(self) -> None:
        self.assertIsNone(parsing.to_float("no digits"))
        self.assertIsNone(parsing.to_float(None))
        self.assertIsNone(parsing.to_float(True))
        # A dict/list is left alone rather than stringified and regex-scanned.
        self.assertIsNone(parsing.to_float({"value": 12}))
        self.assertIsNone(parsing.to_float([12]))


class ToBoolTests(unittest.TestCase):
    def test_truthy_words(self) -> None:
        for word in ("true", "TRUE", "1", "yes", "certified", "CPO"):
            self.assertTrue(parsing.to_bool(word), word)

    def test_falsy_and_none(self) -> None:
        self.assertFalse(parsing.to_bool("false"))
        self.assertFalse(parsing.to_bool(None))
        self.assertFalse(parsing.to_bool(""))

    def test_bool_passthrough(self) -> None:
        self.assertTrue(parsing.to_bool(True))
        self.assertFalse(parsing.to_bool(False))


class StringCoercionTests(unittest.TestCase):
    def test_clean_str_strips_and_empties_to_none(self) -> None:
        self.assertEqual(parsing.clean_str("  hi  "), "hi")
        self.assertIsNone(parsing.clean_str("   "))
        self.assertIsNone(parsing.clean_str(None))
        self.assertEqual(parsing.clean_str(42), "42")

    def test_name_of_handles_plain_string_and_name_dict(self) -> None:
        self.assertEqual(parsing.name_of("Honda"), "Honda")
        self.assertEqual(parsing.name_of({"name": "Honda"}), "Honda")
        self.assertIsNone(parsing.name_of({"other": "x"}))
        self.assertIsNone(parsing.name_of(None))

    def test_scalar_unwraps_list_and_falls_back_to_id(self) -> None:
        self.assertEqual(parsing.scalar("Honda"), "Honda")
        self.assertEqual(parsing.scalar({"name": "Honda"}), "Honda")
        self.assertEqual(parsing.scalar({"@id": "honda"}), "honda")
        self.assertEqual(parsing.scalar([{"name": ""}, {"name": "Honda"}]), "Honda")
        self.assertIsNone(parsing.scalar([]))
        self.assertIsNone(parsing.scalar({"other": "x"}))


class FindCiTests(unittest.TestCase):
    def test_case_insensitive_first_match(self) -> None:
        d = {"VIN": "1HGCV1F34MA111111"}
        self.assertEqual(parsing.find_ci(d, "vin"), "1HGCV1F34MA111111")

    def test_skips_empty_values_for_later_candidate(self) -> None:
        d = {"dealerName": "", "seller": "Riverside Nissan"}
        self.assertEqual(parsing.find_ci(d, "dealerName", "seller"), "Riverside Nissan")

    def test_non_dict_returns_none(self) -> None:
        self.assertIsNone(parsing.find_ci(["not", "a", "dict"], "vin"))

    def test_no_match_returns_none(self) -> None:
        self.assertIsNone(parsing.find_ci({"a": 1}, "b", "c"))


class SplitDealerLocationTests(unittest.TestCase):
    def test_city_state(self) -> None:
        self.assertEqual(parsing.split_dealer_location("Nashville, TN"), ("Nashville", "TN"))

    def test_no_comma_yields_none_none(self) -> None:
        self.assertEqual(parsing.split_dealer_location("Nashville"), (None, None))

    def test_implausible_state_is_dropped(self) -> None:
        city, state = parsing.split_dealer_location("Somewhere, Not A State Code")
        self.assertEqual(city, "Somewhere")
        self.assertIsNone(state)

    def test_none_input(self) -> None:
        self.assertEqual(parsing.split_dealer_location(None), (None, None))


class ParseVehicleTitleTests(unittest.TestCase):
    def test_full_title_without_known_trim(self) -> None:
        result = parsing.parse_vehicle_title("2019 Honda Accord EX-L")
        self.assertEqual(result, {"year": 2019, "make": "Honda", "model": "Accord", "trim": "EX-L"})

    def test_known_trim_keeps_remainder_as_model(self) -> None:
        result = parsing.parse_vehicle_title("2019 Honda Accord Sport Hybrid", known_trim="Sport Hybrid")
        self.assertEqual(result["model"], "Accord Sport Hybrid")
        self.assertNotIn("trim", result)  # caller already has it; not re-derived

    def test_no_year_yields_empty(self) -> None:
        self.assertEqual(parsing.parse_vehicle_title("Great deal on a car"), {})

    def test_empty_input(self) -> None:
        self.assertEqual(parsing.parse_vehicle_title(""), {})
        self.assertEqual(parsing.parse_vehicle_title(None), {})


class ParseTitleFreeTextTests(unittest.TestCase):
    def test_strips_certified_pre_owned_prefix(self) -> None:
        result = parsing.parse_title_free_text("Certified Pre-Owned 2020 Toyota Camry SE")
        self.assertEqual(result, {"year": 2020, "make": "Toyota", "model": "Camry", "trim": "SE"})

    def test_multi_word_trim_is_joined(self) -> None:
        result = parsing.parse_title_free_text("2021 Ford F-150 XLT SuperCrew 4WD")
        self.assertEqual(result["trim"], "XLT SuperCrew 4WD")

    def test_year_need_not_lead(self) -> None:
        result = parsing.parse_title_free_text("New Listing 2018 Mazda CX-5")
        self.assertEqual(result["year"], 2018)
        self.assertEqual(result["make"], "Mazda")

    def test_no_year_yields_empty(self) -> None:
        self.assertEqual(parsing.parse_title_free_text("no year here"), {})

    def test_empty_input(self) -> None:
        self.assertEqual(parsing.parse_title_free_text(""), {})


class ExtractYearMileageTests(unittest.TestCase):
    def test_extract_year_from_int_float_and_text(self) -> None:
        self.assertEqual(parsing.extract_year(2020), 2020)
        self.assertEqual(parsing.extract_year(2020.0), 2020)
        self.assertEqual(parsing.extract_year("Model year 2020"), 2020)
        self.assertIsNone(parsing.extract_year(True))
        self.assertIsNone(parsing.extract_year("no year"))

    def test_extract_mileage_from_scalar_and_quantitative_value(self) -> None:
        self.assertEqual(parsing.extract_mileage("37,412 mi"), 37412)
        self.assertEqual(parsing.extract_mileage({"value": "37,412"}), 37412)
        self.assertIsNone(parsing.extract_mileage({"value": None}))


class FindVinInStringsTests(unittest.TestCase):
    def test_finds_vin_in_any_string_field(self) -> None:
        fields = {"title": "see VIN 1HGCV1F34MA111111 for details", "price": 18995}
        self.assertEqual(parsing.find_vin_in_strings(fields), "1HGCV1F34MA111111")

    def test_no_vin_anywhere_returns_none(self) -> None:
        self.assertIsNone(parsing.find_vin_in_strings({"title": "no vin here", "price": 100}))


class AbsoluteUrlTests(unittest.TestCase):
    def test_relative_href_resolved_against_base(self) -> None:
        self.assertEqual(
            parsing.absolute_url("https://example.com/search", "/vehicle/123"),
            "https://example.com/vehicle/123",
        )

    def test_none_href_returns_none(self) -> None:
        self.assertIsNone(parsing.absolute_url("https://example.com/search", None))
        self.assertIsNone(parsing.absolute_url("https://example.com/search", ""))


class JsonLdExtractionTests(unittest.TestCase):
    def test_single_object(self) -> None:
        body = """
        <script type="application/ld+json">
        {"@type": "Vehicle", "vehicleIdentificationNumber": "1HGCV1F34MA111111", "name": "2021 Honda Accord"}
        </script>
        """
        nodes = list(parsing.iter_ld_vehicle_nodes(body))
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0]["vehicleIdentificationNumber"], "1HGCV1F34MA111111")

    def test_array_of_objects(self) -> None:
        body = """
        <script type="application/ld+json">
        [{"@type": "Car", "vin": "AAA"}, {"@type": "Car", "vin": "BBB"}]
        </script>
        """
        nodes = list(parsing.iter_ld_vehicle_nodes(body))
        vins = sorted(n["vin"] for n in nodes)
        self.assertEqual(vins, ["AAA", "BBB"])

    def test_graph_wrapped_objects(self) -> None:
        body = """
        <script type="application/ld+json">
        {"@context": "https://schema.org", "@graph": [
            {"@type": "Product", "sku": "CCC"},
            {"@type": "WebPage", "name": "irrelevant"}
        ]}
        </script>
        """
        nodes = list(parsing.iter_ld_vehicle_nodes(body))
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0]["sku"], "CCC")

    def test_non_vehicle_types_are_excluded(self) -> None:
        body = """
        <script type="application/ld+json">
        {"@type": "BreadcrumbList", "vin": "should-not-match"}
        </script>
        """
        self.assertEqual(list(parsing.iter_ld_vehicle_nodes(body)), [])

    def test_malformed_json_does_not_raise_and_yields_nothing(self) -> None:
        body = """
        <script type="application/ld+json">
        { this is not valid json ][
        </script>
        """
        self.assertEqual(list(parsing.iter_ld_vehicle_nodes(body)), [])

    def test_empty_script_block(self) -> None:
        body = '<script type="application/ld+json"></script>'
        self.assertEqual(list(parsing.iter_ld_vehicle_nodes(body)), [])

    def test_no_script_tags_at_all(self) -> None:
        self.assertEqual(list(parsing.iter_ld_vehicle_nodes("<html><body>hi</body></html>")), [])

    def test_extract_json_ld_blocks_returns_raw_text(self) -> None:
        body = '<script type="application/ld+json">{"a": 1}</script>'
        blocks = parsing.extract_json_ld_blocks(body)
        self.assertEqual(len(blocks), 1)
        self.assertIn('"a": 1', blocks[0])


class LdOfferPriceAndSellerTests(unittest.TestCase):
    def test_dict_offers_case_sensitive(self) -> None:
        node = {"offers": {"price": "18995", "seller": {"name": "Riverside Nissan"}}}
        price, seller = parsing.ld_offer_price_and_seller(node)
        self.assertEqual(price, "18995")
        self.assertEqual(seller["name"], "Riverside Nissan")

    def test_case_insensitive_mode(self) -> None:
        # The top-level "offers" key itself must still be lowercase (only find_ci lookups
        # *inside* offers are case-insensitive); this exercises inconsistent casing there.
        node2 = {"offers": {"Price": "18995", "Seller": {"Name": "X"}}}
        price, seller = parsing.ld_offer_price_and_seller(node2, case_insensitive=True)
        self.assertEqual(price, "18995")
        price_ci_off, seller_ci_off = parsing.ld_offer_price_and_seller(node2, case_insensitive=False)
        self.assertIsNone(price_ci_off)  # exact-case "price" key not present

    def test_non_dict_offers_returns_none_none(self) -> None:
        self.assertEqual(parsing.ld_offer_price_and_seller({"offers": "not a dict"}), (None, None))
        self.assertEqual(parsing.ld_offer_price_and_seller({}), (None, None))


class WalkDictsTests(unittest.TestCase):
    def test_walks_nested_dicts_and_lists(self) -> None:
        data = {"a": {"b": [{"c": 1}, {"d": 2}]}}
        found = list(parsing.walk_dicts(data))
        self.assertEqual(len(found), 4)  # outer, {"b": ...}, {"c":1}, {"d":2}

    def test_non_dict_non_list_yields_nothing(self) -> None:
        self.assertEqual(list(parsing.walk_dicts("just a string")), [])
        self.assertEqual(list(parsing.walk_dicts(42)), [])


class LooksVehicleShapedTests(unittest.TestCase):
    def test_three_or_more_hints_is_vehicle_shaped(self) -> None:
        node = {"vin": "X", "price": 100, "make": "Honda", "unrelated": True}
        self.assertTrue(parsing.looks_vehicle_shaped(node))

    def test_fewer_than_min_hits_is_not(self) -> None:
        node = {"price": 100, "unrelated": True}
        self.assertFalse(parsing.looks_vehicle_shaped(node))

    def test_custom_hints_and_threshold(self) -> None:
        node = {"foo": 1, "bar": 2}
        self.assertTrue(parsing.looks_vehicle_shaped(node, hints=("foo", "bar", "baz"), min_hits=2))
        self.assertFalse(parsing.looks_vehicle_shaped(node, hints=("foo", "bar", "baz"), min_hits=3))


class EmbeddedJsonWrapperTests(unittest.TestCase):
    """Discovery of each supported embedded-JSON wrapper shape."""

    def test_next_data_script_regex_extracts_payload(self) -> None:
        body = """
        <script id="__NEXT_DATA__" type="application/json">
        {"props": {"pageProps": {"vin": "1HGCV1F34MA111111"}}}
        </script>
        """
        match = parsing.NEXT_DATA_SCRIPT_RE.search(body)
        self.assertIsNotNone(match)
        import json
        data = json.loads(match.group(1))
        self.assertEqual(data["props"]["pageProps"]["vin"], "1HGCV1F34MA111111")

    def test_walk_dicts_finds_vehicle_shaped_node_anywhere_in_next_data(self) -> None:
        body = """
        <script id="__NEXT_DATA__" type="application/json">
        {"props": {"pageProps": {"initialState": {"inventory": {"vehicles": [
            {"vin": "AAA", "make": "Honda", "model": "Accord", "price": 100}
        ]}}}}}
        </script>
        """
        import json
        match = parsing.NEXT_DATA_SCRIPT_RE.search(body)
        data = json.loads(match.group(1))
        vehicle_nodes = [n for n in parsing.walk_dicts(data) if parsing.looks_vehicle_shaped(n)]
        self.assertEqual(len(vehicle_nodes), 1)
        self.assertEqual(vehicle_nodes[0]["vin"], "AAA")


class ClassCardParserTests(unittest.TestCase):
    def test_container_and_field_classes_basic(self) -> None:
        body = """
        <div class="vehicle-card">
          <h3 class="title">2020 Toyota Camry</h3>
          <span class="price">$19,500</span>
        </div>
        """
        cards = parsing.run_class_card_parser(
            body, "vehicle-card", {"title": "title", "price": "price"}
        )
        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0]["title"], "2020 Toyota Camry")
        self.assertEqual(cards[0]["price"], "$19,500")

    def test_multiple_container_classes(self) -> None:
        body = '<div class="result-tile"><span class="price">$100</span></div>'
        cards = parsing.run_class_card_parser(
            body, ("result-tile", "vehicle-card"), {"price": "price"}
        )
        self.assertEqual(len(cards), 1)

    def test_capture_data_attrs_specific_suffixes(self) -> None:
        body = '<div class="vehicle-card" data-vin="AAA" data-other="ignored"></div>'
        cards = parsing.run_class_card_parser(
            body, "vehicle-card", {}, capture_data_attrs={"vin"}
        )
        self.assertEqual(cards[0].get("vin"), "AAA")
        self.assertNotIn("other", cards[0])

    def test_capture_data_attrs_true_captures_all(self) -> None:
        body = '<div class="vehicle-card" data-vin="AAA" data-stock-number="S1"></div>'
        cards = parsing.run_class_card_parser(
            body, "vehicle-card", {}, capture_data_attrs=True
        )
        self.assertEqual(cards[0].get("vin"), "AAA")
        self.assertEqual(cards[0].get("stock_number"), "S1")

    def test_overwrite_true_last_wins(self) -> None:
        body = """
        <div class="vehicle-card">
          <span class="price">$100</span>
          <span class="price">$200</span>
        </div>
        """
        cards = parsing.run_class_card_parser(body, "vehicle-card", {"price": "price"}, overwrite=True)
        self.assertEqual(cards[0]["price"], "$200")

    def test_overwrite_false_first_wins(self) -> None:
        body = """
        <div class="vehicle-card">
          <span class="price">$100</span>
          <span class="price">$200</span>
        </div>
        """
        cards = parsing.run_class_card_parser(body, "vehicle-card", {"price": "price"}, overwrite=False)
        self.assertEqual(cards[0]["price"], "$100")

    def test_nested_cards_are_each_captured_separately(self) -> None:
        body = """
        <div class="vehicle-card"><span class="price">$100</span></div>
        <div class="vehicle-card"><span class="price">$200</span></div>
        """
        cards = parsing.run_class_card_parser(body, "vehicle-card", {"price": "price"})
        self.assertEqual([c["price"] for c in cards], ["$100", "$200"])

    def test_malformed_markup_returns_empty_list_not_raise(self) -> None:
        # HTMLParser is itself very tolerant, but the wrapper's try/except still guards
        # against any parser edge case; feeding it garbage should never propagate.
        cards = parsing.run_class_card_parser("<<<not html>>>", "vehicle-card", {})
        self.assertEqual(cards, [])


class DataAttributeCardScannerTests(unittest.TestCase):
    def test_collects_data_attrs_off_marker_element(self) -> None:
        body = '<div class="vehicle-card" data-vin="AAA" data-price="18995"></div>'
        cards = parsing.run_data_attribute_card_scanner(body, "vehicle-card")
        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0]["vin"], "AAA")
        self.assertEqual(cards[0]["price"], "18995")

    def test_substring_marker_match(self) -> None:
        body = '<div class="vehicle-card--featured" data-vin="AAA"></div>'
        cards = parsing.run_data_attribute_card_scanner(body, "vehicle-card")
        self.assertEqual(len(cards), 1)

    def test_no_marker_no_cards(self) -> None:
        body = '<div class="something-else" data-vin="AAA"></div>'
        self.assertEqual(parsing.run_data_attribute_card_scanner(body, "vehicle-card"), [])

    def test_marker_without_data_attrs_is_skipped(self) -> None:
        body = '<div class="vehicle-card"></div>'
        self.assertEqual(parsing.run_data_attribute_card_scanner(body, "vehicle-card"), [])


class VinAnchoredCardParserTests(unittest.TestCase):
    def test_collects_text_and_href_within_vin_anchored_element(self) -> None:
        body = """
        <div data-vin="1HGCV1F34MA111111">
          <a href="/vehicle/1HGCV1F34MA111111">
            <h3>2021 Honda Accord</h3>
          </a>
          <span>$21,995</span>
        </div>
        """
        cards = parsing.run_vin_anchored_card_parser(body)
        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0]["vin"], "1HGCV1F34MA111111")
        self.assertEqual(cards[0]["href"], "/vehicle/1HGCV1F34MA111111")
        self.assertIn("2021 Honda Accord", cards[0]["parts"])
        self.assertIn("$21,995", cards[0]["parts"])

    def test_alternate_attribute_name(self) -> None:
        body = '<div data-listing-vin="AAA">text</div>'
        cards = parsing.run_vin_anchored_card_parser(body)
        self.assertEqual(cards[0]["vin"], "AAA")

    def test_no_vin_attribute_no_cards(self) -> None:
        body = "<div>just some text with no vin attribute</div>"
        self.assertEqual(parsing.run_vin_anchored_card_parser(body), [])


if __name__ == "__main__":
    unittest.main()
