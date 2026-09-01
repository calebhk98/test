-- 009_units_attributes.sql
-- Units + physical-attributes build (this build; no § reference, a
-- product decision on top of the completed spec implementation, same
-- category as 007_decisions.sql's additions). Owned by this build only;
-- does not alter or drop anything from any earlier migration, and no
-- earlier migration is edited.
--
-- Three additions, all to `profiles` (001_init.sql) plus one to
-- `hard_filters` (001_init.sql):
--
--   1. height_cm / weight_g / weight_visible / body_type, new OPTIONAL
--      profile fields the product owner asked for (height, weight, body
--      type, none of the three existed anywhere before this build, not
--      as a profile field nor as a filter). See src/services/
--      profile.service.ts and src/domain/units/ for the canonical-unit
--      discipline these columns exist to support: height_cm/weight_g are
--      ALWAYS the canonical stored value (whole centimetres / whole
--      grams, integer, never a display unit, never a float that could
--      drift a filter comparison across reads).
--   2. unit_preference, per-user 'metric'/'imperial' DISPLAY preference
--      (src/domain/units/preference.ts). Presentation-only: nothing in
--      this schema or profile.service.ts ever lets changing this column
--      rewrite height_cm/weight_g.
--   3. hard_filters.exclude_if_unset, product-owner correction (see this
--      build's report): whether a hard filter EXCLUDES a candidate whose
--      value for that filter's key cannot be resolved (true) or still
--      lets them through (false). See src/services/filter.service.ts's
--      file-level "MISSING/UNRESOLVED VALUES" note for the full policy.
--      Column-level default is `false`, matching the application-level
--      default exactly (there is no exception for any filter key,
--      including deal-breaker-derived ones, a brand-new account that
--      hasn't filled a field in yet must not silently vanish from
--      results). A user, or a deal-breaker derivation acting on that
--      user's explicit request, opts INTO strict exclusion per filter.

-- =========================================================================
-- profiles: height / weight / body type / unit preference
-- =========================================================================
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS height_cm integer
  CHECK (height_cm BETWEEN 100 AND 250); -- generous adult range; nullable (optional field)

ALTER TABLE profiles ADD COLUMN IF NOT EXISTS weight_g integer
  CHECK (weight_g BETWEEN 20000 AND 300000); -- 20kg-300kg in grams; nullable (optional field)

-- Whether weight_g appears on this user's PublicProfileView at all, see
-- profile.service.ts's PublicProfileView doc: hidden means structurally
-- ABSENT from the returned object, not merely masked. Defaults to visible
-- (true), matching every other optional profile field's "shown once set"
-- default; the user opts INTO hiding, not into showing.
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS weight_visible boolean NOT NULL DEFAULT true;

ALTER TABLE profiles ADD COLUMN IF NOT EXISTS body_type text
  CHECK (body_type IN ('slim', 'athletic', 'average', 'curvy', 'muscular', 'plus_size', 'other')); -- src/domain/units/bodyType.ts BODY_TYPES, keep in sync

-- Presentation-only display-unit preference (src/domain/units/preference.ts).
-- Defaults to 'metric', profiles carries no country/locale column to
-- infer from (see that file's resolveDefaultUnitPreference doc).
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS unit_preference text NOT NULL DEFAULT 'metric'
  CHECK (unit_preference IN ('metric', 'imperial'));

-- =========================================================================
-- hard_filters: excludeIfUnset toggle
-- =========================================================================
ALTER TABLE hard_filters ADD COLUMN IF NOT EXISTS exclude_if_unset boolean NOT NULL DEFAULT false;
