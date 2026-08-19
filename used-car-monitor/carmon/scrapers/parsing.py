"""Shared parsing/coercion toolkit for the scraper adapters in this package.

Every adapter in `carmon/scrapers/` (`cars_com.py`, `carmax.py`, `carvana.py`,
`cargurus.py`, `autotrader.py`, `truecar.py`, and to a lesser extent `repairpal.py`) was
written independently against the same category of problem: turn an unpredictable mix of
schema.org JSON-LD, a framework's embedded-JSON hydration blob, and loosely-conventioned
HTML listing-card markup into this project's normalized listing fields, without ever
raising on a page that does not look the way its author expected. That produced the same
handful of small, careful functions rewritten with tiny variations seven times over. This
module is the single copy.

What stays here is genuinely site-*agnostic*: type coercion ("$18,995" -> 18995), the
mechanics of walking a JSON-LD or hydration-JSON tree, case-insensitive field lookup, and
a couple of small `html.parser` helpers for walking card-shaped markup. What deliberately
stays OUT of this module -- and lives in each adapter instead -- is anything that encodes a
judgment call about one specific site: CarMax's manufacturer-CPO-vs-"CarMax Quality
Certified" distinction, Carvana always being the seller of record, CarGurus'/TrueCar's deal-
rating extraction, which CSS class names identify a listing card on which site, and so on.
Where this module offers a *parametrized* helper (`ClassCardParser`, `looks_vehicle_shaped`)
the parameters are exactly that kind of per-site configuration -- container class names,
which key names count as "vehicle-ish" -- never a flag standing in for different business
logic.

A note on two coexisting int coercions, `to_int` and `to_signed_int`: they read as
near-duplicates but encode a real difference. `to_int` strips every non-digit character
(including a leading '-'), which is correct for a price or an odometer reading -- those are
never legitimately negative in this project's data, and if a source page ever rendered one
with a stray hyphen (a bullet, a phone-style dash) that character should be discarded, not
misread as a sign. `to_signed_int` instead extracts the *first* number token and keeps a
leading '-' if present, because it is used exactly where a negative value is meaningful:
CarGurus' "$1,200 below market" delta, and Autotrader/TrueCar's free-text field scraping
where preserving whatever sign the source text actually had is the safer default. Passing
the wrong one to the wrong field would corrupt data quietly, so adapters must keep using
whichever one their own tests were written against rather than switching for style.
"""

from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple

# =============================================================================
# Coercion: turning whatever a page/JSON blob handed us into a clean scalar.
# =============================================================================


def to_int(value: Any) -> Optional[int]:
    """Best-effort *unsigned* int coercion for strings like '$18,995', '37,412 mi.', or
    '37K mi' (-> 37000). Digit-stripping: any sign, currency symbol, comma, or unit text is
    simply discarded rather than causing a parse failure. Never raises -- returns None for
    anything that yields no digits at all (e.g. "Call for price").

    Use `to_signed_int` instead when a negative value is meaningful for the field being
    parsed (see the module docstring).
    """
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    text = str(value)
    lowered = text.lower()
    k_match = re.match(r"\s*([\d,.]+)\s*k\b", lowered)
    if k_match:
        try:
            return int(round(float(k_match.group(1).replace(",", "")) * 1000))
        except ValueError:
            pass
    digits = re.sub(r"[^0-9]", "", text)
    if not digits:
        return None
    try:
        return int(digits)
    except ValueError:
        return None


def to_signed_int(value: Any) -> Optional[int]:
    """Int coercion that keeps a leading '-' and the *first* number found in the text,
    rather than stripping to digits-only. See the module docstring for why this is a
    separate function from `to_int` rather than a flag on it.
    """
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(value)
    match = re.search(r"-?\d[\d,]*", str(value))
    if not match:
        return None
    try:
        return int(match.group().replace(",", ""))
    except ValueError:
        return None


def to_float(value: Any) -> Optional[float]:
    """Best-effort float coercion. Only None/bool/int/float/str are handled on purpose --
    an unexpected dict or list is left as None rather than stringified and regex-scanned,
    which could otherwise "find" a number inside a JSON repr that was never meant as data.
    """
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        match = re.search(r"-?\d+(?:\.\d+)?", value.replace(",", ""))
        if match:
            try:
                return float(match.group())
            except ValueError:
                return None
    return None


def to_bool(value: Any) -> bool:
    """Loose truthiness for certification-ish fields: 'true'/'1'/'yes'/'certified'/'cpo'
    (any casing) are True, everything else (including None) is False."""
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    text = str(value).strip().lower()
    return text in ("true", "1", "yes", "certified", "cpo")


def clean_str(value: Any) -> Optional[str]:
    """Stringify and strip; empty (or all-whitespace) becomes None rather than ''."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def name_of(value: Any) -> Optional[str]:
    """A schema.org-ish field is sometimes a plain string, sometimes `{'name': '...'}`.
    Used for make/model/dealer-name style fields that come from either flavor."""
    if isinstance(value, dict):
        return clean_str(value.get("name"))
    return clean_str(value)


def scalar(value: Any) -> Optional[str]:
    """Like `name_of`, but also unwraps a list (first usable item wins) and accepts a
    dict's `@id` as a fallback name -- the shape schema.org `brand`/`model` values from
    Autotrader/TrueCar-style pages can take, where `name_of`'s narrower dict-only handling
    is not enough."""
    if isinstance(value, dict):
        return clean_str(value.get("name") or value.get("@id"))
    if isinstance(value, list):
        for item in value:
            found = scalar(item)
            if found:
                return found
        return None
    return clean_str(value)


# =============================================================================
# Field normalization: shapes every adapter's field-mapping normalizer needs.
# =============================================================================

# 17-character VIN pattern (excludes I/O/Q per the VIN standard). Used as a last-resort
# fallback when a field mapping has no clearly-named VIN key but a string field happens to
# contain one -- e.g. buried in a listing URL or a title attribute.
# "Nashville, TN" as it appears on its own inside a listing card — used to recognise which
# text chunk is the dealer's location when a card gives no explicit field for it.
CITY_STATE_RE = re.compile(r"^[A-Za-z][A-Za-z .'\-]*,\s*[A-Z]{2}$")

VIN_RE = re.compile(r"\b[A-HJ-NPR-Z0-9]{17}\b")

# A plausible model year, generous on both ends (1950-2049) so it isn't broken by whichever
# year this code happens to run in.
YEAR_RE = re.compile(r"\b(19[5-9]\d|20[0-4]\d)\b")


def find_ci(d: Any, *names: str) -> Any:
    """Case-insensitive, first-match lookup across several candidate key names. Skips a key
    whose value is None or ''  so a later, populated candidate can still win."""
    if not isinstance(d, dict):
        return None
    lower_map = {str(k).lower(): k for k in d.keys()}
    for name in names:
        key = lower_map.get(name.lower())
        if key is not None:
            value = d.get(key)
            if value not in (None, ""):
                return value
    return None


def split_dealer_location(location: Any) -> Tuple[Optional[str], Optional[str]]:
    """'Nashville, TN' -> ('Nashville', 'TN'). Anything else -> (None, None). A "state" of
    more than 3 characters is treated as unparseable rather than trusted (it is more likely
    the whole string had no comma-separated state at all) and left unset."""
    text = clean_str(location)
    if not text or "," not in text:
        return None, None
    city, _, state = text.rpartition(",")
    city = city.strip() or None
    state = state.strip() or None
    if state and len(state) > 3:
        state = None
    return city, state


def parse_vehicle_title(title: Any, known_trim: Any = None) -> Dict[str, Any]:
    """Best-effort 'YEAR MAKE MODEL [TRIM...]' split of a listing title, e.g.
    '2019 Honda Accord EX-L' -> {'year': 2019, 'make': 'Honda', 'model': 'Accord',
    'trim': 'EX-L'}.

    `known_trim`: pass the trim value already recovered from a separate structured field
    (e.g. `vehicleConfiguration`), if any. When it is truthy, the whole remainder after MAKE
    is treated as MODEL rather than re-guessing a trim split -- a structured trim field is a
    more reliable source than blindly splitting the title text again. Returns only the keys
    it actually found: a title with no leading year yields `{}`.
    """
    result: Dict[str, Any] = {}
    if not title:
        return result
    match = re.match(r"\s*(\d{4})\s+([A-Za-z0-9\-]+)\s+(.+)", str(title))
    if not match:
        return result
    result["year"] = int(match.group(1))
    result["make"] = match.group(2)
    rest = match.group(3).strip()
    if known_trim:
        result["model"] = rest
    else:
        parts = rest.split(None, 1)
        if parts:
            result["model"] = parts[0]
        if len(parts) > 1:
            result["trim"] = parts[1]
    return result


def parse_title_free_text(text: Any, year_re: "re.Pattern[str]" = YEAR_RE) -> Dict[str, Any]:
    """Best-effort 'YEAR MAKE MODEL [TRIM...]' split of unstructured title text, used by
    Autotrader and TrueCar when a structured year/make/model field is absent.

    Deliberately a different algorithm from `parse_vehicle_title` above, not a
    parametrized variant of it: this one strips a leading "Certified [Pre-Owned]" prefix
    first (both sites' plain-text titles have been observed to carry that), finds the year
    anywhere in the remaining text via `year_re` rather than requiring it to lead, and -- if
    a year is found at all -- always treats every token after MAKE beyond MODEL as TRIM
    (joined back together), rather than `parse_vehicle_title`'s "trim is only the single
    next token, and only when no trim was already known" rule. Both quirks were deliberate
    choices for these two sites' expected free-text card/title conventions and would be
    wrong for the other four adapters' more structured field maps.
    """
    result: Dict[str, Any] = {}
    if not text:
        return result
    cleaned = re.sub(r"(?i)^certified\s+(pre-owned\s+)?", "", str(text).strip())
    match = year_re.search(cleaned)
    if not match:
        return result
    result["year"] = int(match.group(1))
    tokens = cleaned[match.end():].split()
    if tokens:
        result["make"] = tokens[0]
    if len(tokens) > 1:
        result["model"] = tokens[1]
    if len(tokens) > 2:
        result["trim"] = " ".join(tokens[2:])
    return result


def extract_year(value: Any) -> Optional[int]:
    """A model year from an int/float, or scraped out of free text via `YEAR_RE`."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        match = YEAR_RE.search(value)
        if match:
            return int(match.group(1))
    return None


def extract_mileage(value: Any) -> Optional[int]:
    """Mileage from a plain scalar, or from a schema.org QuantitativeValue-shaped
    `{'value': ...}` dict."""
    if isinstance(value, dict):
        value = value.get("value")
    return to_int(value)


def find_vin_in_strings(fields: Dict[str, Any]) -> Optional[str]:
    """Fallback VIN recovery: scan every string value in a field mapping for a bare 17-
    character VIN pattern. This is the last resort in every adapter's listing normalizer --
    a field map with a properly-named vin/sku/vehicleIdentificationNumber key never reaches
    this, since that is checked first."""
    for value in fields.values():
        if isinstance(value, str):
            found = VIN_RE.search(value.upper())
            if found:
                return found.group(0)
    return None


def absolute_url(base_url: str, href: Optional[str]) -> Optional[str]:
    """Resolve a (possibly relative) href against the page URL it was found on."""
    if not href:
        return None
    from urllib.parse import urljoin

    try:
        return urljoin(base_url, href)
    except Exception:
        return None


# =============================================================================
# JSON-LD: <script type="application/ld+json"> schema.org blocks.
# =============================================================================

JSON_LD_SCRIPT_RE = re.compile(
    r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.IGNORECASE | re.DOTALL,
)

# The schema.org @types that plausibly describe a used-vehicle listing on the sites this
# package scrapes. Product is included because some sites describe a vehicle listing as a
# generic Product with automotive-flavored additionalProperty/offers rather than Car/Vehicle.
VEHICLE_LD_TYPES = {"car", "vehicle", "product"}


def extract_json_ld_blocks(body: str) -> List[str]:
    """Return the raw (not-yet-parsed) text of every application/ld+json script in `body`."""
    return JSON_LD_SCRIPT_RE.findall(body)


def walk_dicts(node: Any) -> Iterator[Dict[str, Any]]:
    """Yield every dict anywhere in a nested JSON structure, depth-first.

    This is the one tree-walk every adapter needs, for two different jobs: finding
    schema.org nodes inside a JSON-LD payload (where a top-level `@graph` array, or a bare
    array of nodes, is common) and finding vehicle-shaped objects inside a framework's
    hydration-JSON state blob (where the real listing objects are nested arbitrarily deep
    under page-props/component-state keys nobody outside that site's build tooling can
    predict). A plain recursive walk with no special-casing of any particular key (such as
    `@graph`) is sufficient for both: `@graph`'s value is itself a list, which this walk
    already descends into like any other dict value.
    """
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from walk_dicts(value)
    elif isinstance(node, list):
        for item in node:
            yield from walk_dicts(item)


def iter_ld_vehicle_nodes(
    body: str, vehicle_types: Iterable[str] = VEHICLE_LD_TYPES
) -> Iterator[Dict[str, Any]]:
    """Yield every schema.org node, from every JSON-LD block in `body`, whose `@type`
    intersects `vehicle_types`. Malformed JSON in a block is skipped, not raised."""
    types_wanted = {t.lower() for t in vehicle_types}
    for block in extract_json_ld_blocks(body):
        raw = block.strip()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            continue
        for node in walk_dicts(data):
            node_type = node.get("@type")
            if isinstance(node_type, list):
                types = {str(t).lower() for t in node_type}
            else:
                types = {str(node_type).lower()} if node_type else set()
            if types & types_wanted:
                yield node


def ld_offer_price_and_seller(
    node: Dict[str, Any], *, case_insensitive: bool = False
) -> Tuple[Any, Optional[Dict[str, Any]]]:
    """Pull `price` and `seller` out of a schema.org node's `offers` sub-object, when
    `offers` is present and shaped as a dict. `case_insensitive=True` (CarGurus) looks the
    two keys up via `find_ci` instead of a plain `.get`, since that site's hydration-JSON
    fixtures are not consistently cased the way schema.org markup normally is.
    """
    offers = node.get("offers")
    if not isinstance(offers, dict):
        return None, None
    if case_insensitive:
        price = find_ci(offers, "price")
        seller = find_ci(offers, "seller")
    else:
        price = offers.get("price")
        seller = offers.get("seller")
    return price, (seller if isinstance(seller, dict) else None)


# =============================================================================
# Embedded JSON: __NEXT_DATA__ / application/json scripts / window.X = {...} hydration.
# =============================================================================

NEXT_DATA_SCRIPT_RE = re.compile(
    r'<script[^>]+id=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>',
    re.IGNORECASE | re.DOTALL,
)

# A node is "vehicle-shaped" if it carries at least this many of these keys together --
# avoids treating an arbitrary app-state object (nav menus, feature flags, ...) as a
# listing just because it happens to have one vehicle-ish-sounding key.
VEHICLE_KEY_HINTS = (
    "vin", "vehicleIdentificationNumber", "stockNumber", "stock_number",
    "mileage", "mileageFromOdometer", "price", "make", "model",
)


def looks_vehicle_shaped(
    node: Dict[str, Any], hints: Iterable[str] = VEHICLE_KEY_HINTS, min_hits: int = 3
) -> bool:
    """True when `node` carries at least `min_hits` of `hints` as keys. Deliberately a
    "several keys together" heuristic rather than "any one key" -- a single `price` or
    `make` key is common on all sorts of unrelated app-state objects; several of them
    together is a much stronger signal that this dict actually describes one vehicle.

    Use this (rather than the simpler "carries a VIN" anchor `iter_ld_vehicle_nodes`'s
    sibling functions rely on) for a hydration blob where the listing objects are not
    guaranteed to carry an explicit VIN key at all -- only where that is a deliberate,
    site-specific choice, since it is more permissive about *which* dicts count as a
    listing candidate and a site with lots of vehicle-key-shaped non-listing objects could
    produce false positives a stricter VIN-anchored walk would not.
    """
    hits = sum(1 for key in hints if key in node)
    return hits >= min_hits


# =============================================================================
# HTML cards: small html.parser helpers for walking listing-card-shaped markup.
# =============================================================================


class ClassCardParser(HTMLParser):
    """Generic "container identified by CSS class, fields identified by CSS class" listing-
    card walker, configured per-site by its caller (cars.com, CarMax, Carvana, and CarGurus
    each use this for their plain-HTML-fallback parse strategy, each with its own class
    names -- see WHAT MUST STAY PER-ADAPTER in each adapter's own module docstring).

    Only the tree-walking mechanics are shared: tracking element depth so a card's end is
    detected even when its markup nests other elements sharing the same tag names, buffering
    text for whichever field-class is currently open, and capturing the container's own
    data-* attributes plus the first `<a href>` found. Two knobs capture real per-site
    markup differences rather than business logic:

      * `capture_data_attrs`: which data-* suffixes (e.g. "vin") to copy off the container
        tag itself, or True to copy all of them. Carvana's markup convention puts more of a
        listing's data directly into data-* attributes than the other three sites' do,
        hence the "copy everything" option.
      * `overwrite`: whether a later element matching an already-seen field class replaces
        the earlier value (True -- cars.com/CarMax/CarGurus' documented convention: last
        element in the card wins) or is ignored in favor of the first one seen (False --
        Carvana's). Getting this backwards would silently swap which of two same-class
        elements' text a listing ends up with.
    """

    def __init__(
        self,
        container_classes: Any,
        field_classes: Dict[str, str],
        capture_data_attrs: Any = False,
        overwrite: bool = True,
    ) -> None:
        super().__init__(convert_charrefs=True)
        self.container_classes = (
            {container_classes} if isinstance(container_classes, str) else set(container_classes)
        )
        self.field_classes = field_classes
        self.capture_data_attrs = capture_data_attrs
        self.overwrite = overwrite
        self.cards: List[Dict[str, Any]] = []
        self._depth: List[str] = []
        self._card: Optional[Dict[str, Any]] = None
        self._card_depth = 0
        self._text_target: Optional[str] = None
        self._buffer = ""

    def handle_starttag(self, tag: str, attrs: List[tuple]) -> None:
        attr_map = dict(attrs)
        classes = (attr_map.get("class") or "").split()
        self._depth.append(tag)

        if self._card is None and any(c in classes for c in self.container_classes):
            self._card = {}
            self._card_depth = len(self._depth)
            if self.capture_data_attrs:
                for key, value in attrs:
                    if not value or not key.startswith("data-"):
                        continue
                    suffix = key[len("data-"):]
                    if self.capture_data_attrs is True or suffix in self.capture_data_attrs:
                        self._card[suffix.replace("-", "_")] = value
            if tag == "a" and attr_map.get("href"):
                self._card.setdefault("listing_url", attr_map["href"])
            return

        if self._card is None:
            return

        if tag == "a" and attr_map.get("href"):
            self._card.setdefault("listing_url", attr_map["href"])

        for css_class, field_name in self.field_classes.items():
            if css_class in classes:
                self._text_target = field_name
                self._buffer = ""
                break

    def handle_data(self, data: str) -> None:
        if self._text_target is not None:
            self._buffer += data

    def handle_endtag(self, tag: str) -> None:
        if self._text_target is not None:
            value = self._buffer.strip()
            if value and self._card is not None:
                if self.overwrite:
                    self._card[self._text_target] = value
                else:
                    self._card.setdefault(self._text_target, value)
            self._text_target = None
            self._buffer = ""

        if self._depth:
            self._depth.pop()

        if self._card is not None and len(self._depth) < self._card_depth:
            self.cards.append(self._card)
            self._card = None
            self._card_depth = 0


def run_class_card_parser(
    body: str,
    container_classes: Any,
    field_classes: Dict[str, str],
    capture_data_attrs: Any = False,
    overwrite: bool = True,
) -> List[Dict[str, Any]]:
    """Feed `body` through a `ClassCardParser` and return its collected cards, or `[]` on
    any parse failure (malformed markup must never take an adapter down)."""
    parser = ClassCardParser(container_classes, field_classes, capture_data_attrs, overwrite)
    try:
        parser.feed(body)
    except Exception:
        return []
    return parser.cards


class DataAttributeCardScanner(HTMLParser):
    """Simpler cousin of `ClassCardParser`: collects every data-* attribute off an element
    whose class carries a given marker, with no text-content or nesting-depth tracking at
    all (cars.com's search-results markup has historically carried each card's full data as
    data-* attributes on one element, needing nothing more than this).

    The marker check accepts either a class-list token match or a raw substring match
    (`"vehicle-card" in classes.split()` or `"vehicle-card" in classes`), since a marker
    class is sometimes seen compounded with a modifier (e.g. `vehicle-card--featured`) and
    both forms have been observed in the wild for this kind of listing markup.
    """

    def __init__(self, container_marker: str) -> None:
        super().__init__(convert_charrefs=True)
        self.container_marker = container_marker
        self.cards: List[Dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: List[tuple]) -> None:
        attr_map = dict(attrs)
        classes = attr_map.get("class", "") or ""
        if self.container_marker not in classes.split() and self.container_marker not in classes:
            return
        fields: Dict[str, str] = {}
        for key, value in attrs:
            if value is None:
                continue
            if key.startswith("data-"):
                fields[key[len("data-"):].replace("-", "_")] = value
        if fields:
            self.cards.append(fields)


def run_data_attribute_card_scanner(body: str, container_marker: str) -> List[Dict[str, str]]:
    """Feed `body` through a `DataAttributeCardScanner` and return its collected cards, or
    `[]` on any parse failure."""
    scanner = DataAttributeCardScanner(container_marker)
    try:
        scanner.feed(body)
    except Exception:
        return []
    return scanner.cards


class VinAnchoredCardParser(HTMLParser):
    """Collects text within any element carrying a `data-vin`/`data-listing-vin` attribute.

    Deliberately simple, with no assumption about class names: Autotrader and TrueCar (the
    two adapters that use this) were both written without ever having seen live HTML from
    their target site (see each adapter's module docstring), so a class-name convention
    would be a guess with nothing to validate it against. A VIN attribute is the one anchor
    both adapters trust -- if the source markup ever attaches `data-vin`/`data-listing-vin`
    to a listing's container element, that is enough to find it; if it does not, this
    strategy correctly finds nothing rather than guessing at a class name.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.cards: List[Dict[str, Any]] = []
        self._depth = 0
        self._card: Optional[Dict[str, Any]] = None
        self._card_depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        self._depth += 1
        attrs_d = dict(attrs)
        if self._card is None:
            vin = attrs_d.get("data-vin") or attrs_d.get("data-listing-vin")
            if vin and vin.strip():
                self._card = {"vin": vin.strip(), "parts": [], "href": None}
                self._card_depth = self._depth
        if self._card is not None and tag == "a" and self._card.get("href") is None:
            href = attrs_d.get("href")
            if href:
                self._card["href"] = href

    def handle_startendtag(self, tag: str, attrs) -> None:
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        if self._card is not None and self._depth == self._card_depth:
            self.cards.append(self._card)
            self._card = None
        self._depth = max(0, self._depth - 1)

    def handle_data(self, data: str) -> None:
        if self._card is not None:
            text = data.strip()
            if text:
                self._card["parts"].append(text)


def run_vin_anchored_card_parser(body: str) -> List[Dict[str, Any]]:
    """Feed `body` through a `VinAnchoredCardParser` and return its collected cards, or
    `[]` on any parse failure."""
    parser = VinAnchoredCardParser()
    try:
        parser.feed(body)
    except Exception:
        return []
    return parser.cards
