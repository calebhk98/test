import type {
  ChoiceOption,
  FrequencyDefinition,
  MultiChoiceDefinition,
  QuestionType,
  QuestionTypeDefinition,
  ScaleDefinition,
  SingleChoiceDefinition,
} from './types.js';

/**
 * Per-type behavior, registered once here and never switched on again
 * elsewhere. This is the extension point: adding a fifth `QuestionType`
 * means adding one `QuestionTypeHandler` entry to `TYPE_HANDLERS` below —
 * `scoring.ts` and `selector.ts` call `getTypeHandler(type)` and never
 * hardcode a list of types themselves.
 */
export type ValidationResult<T = unknown> = { valid: true; value: T } | { valid: false; reason: string };

export interface QuestionTypeHandler {
  type: QuestionType;
  /** Parses/validates a raw self-value (what the user IS/DOES) against a question's type definition. */
  validateSelfValue(def: QuestionTypeDefinition, raw: unknown): ValidationResult;
  /** Parses/validates a raw preference-value (what the user WANTS) against a question's type definition. Shape differs from selfValue for single_choice (a set, not a scalar — see types.ts). */
  validatePreferenceValue(def: QuestionTypeDefinition, raw: unknown): ValidationResult;
  /**
   * 0..1: how well does `selfValue` (candidate's own answer) satisfy
   * `preferenceValue` (the other user's stated want)? Symmetric inputs
   * are combined by the caller (scoring.ts); this function only scores
   * one direction.
   */
  satisfaction(def: QuestionTypeDefinition, selfValue: unknown, preferenceValue: unknown): number;
  /**
   * Binary, zero-tolerance acceptability check — used only to derive
   * deal-breaker filters (dealBreakers.ts). A deal breaker has no
   * gradation: either `selfValue` is acceptable or the candidate is
   * excluded, so this is intentionally NOT "satisfaction >= threshold".
   */
  isAcceptable(def: QuestionTypeDefinition, selfValue: unknown, preferenceValue: unknown): boolean;
}

function optionKeys(options: ChoiceOption[]): Set<string> {
  return new Set(options.map((o) => o.key));
}

// ---- scale ---------------------------------------------------------

function asScaleDef(def: QuestionTypeDefinition): ScaleDefinition {
  if (def.type !== 'scale') throw new Error(`Expected scale definition, got "${def.type}"`);
  return def;
}

const scaleHandler: QuestionTypeHandler = {
  type: 'scale',
  validateSelfValue(defIn, raw) {
    const def = asScaleDef(defIn);
    if (typeof raw !== 'number' || !Number.isInteger(raw) || raw < def.min || raw > def.max) {
      return { valid: false, reason: `Expected an integer between ${def.min} and ${def.max}` };
    }
    return { valid: true, value: raw };
  },
  validatePreferenceValue(defIn, raw) {
    return scaleHandler.validateSelfValue(defIn, raw);
  },
  satisfaction(defIn, selfValue, preferenceValue) {
    const def = asScaleDef(defIn);
    const range = def.max - def.min;
    if (range <= 0) return 1;
    const self = selfValue as number;
    const pref = preferenceValue as number;
    return 1 - Math.abs(self - pref) / range;
  },
  isAcceptable(_def, selfValue, preferenceValue) {
    // Deal breaker on a scale question: zero tolerance -> exact match only.
    return selfValue === preferenceValue;
  },
};

// ---- frequency (ordinal, like scale, but keyed by anchor) ----------

function asFrequencyDef(def: QuestionTypeDefinition): FrequencyDefinition {
  if (def.type !== 'frequency') throw new Error(`Expected frequency definition, got "${def.type}"`);
  return def;
}

function anchorIndex(def: FrequencyDefinition, key: unknown): number {
  return def.anchors.findIndex((a) => a.key === key);
}

const frequencyHandler: QuestionTypeHandler = {
  type: 'frequency',
  validateSelfValue(defIn, raw) {
    const def = asFrequencyDef(defIn);
    if (typeof raw !== 'string' || anchorIndex(def, raw) === -1) {
      return { valid: false, reason: `Expected one of: ${def.anchors.map((a) => a.key).join(', ')}` };
    }
    return { valid: true, value: raw };
  },
  validatePreferenceValue(defIn, raw) {
    return frequencyHandler.validateSelfValue(defIn, raw);
  },
  satisfaction(defIn, selfValue, preferenceValue) {
    const def = asFrequencyDef(defIn);
    const range = def.anchors.length - 1;
    if (range <= 0) return 1;
    const selfIdx = anchorIndex(def, selfValue);
    const prefIdx = anchorIndex(def, preferenceValue);
    if (selfIdx === -1 || prefIdx === -1) return 0;
    return 1 - Math.abs(selfIdx - prefIdx) / range;
  },
  isAcceptable(_def, selfValue, preferenceValue) {
    return selfValue === preferenceValue;
  },
};

// ---- single_choice ---------------------------------------------------

function asSingleChoiceDef(def: QuestionTypeDefinition): SingleChoiceDefinition {
  if (def.type !== 'single_choice') throw new Error(`Expected single_choice definition, got "${def.type}"`);
  return def;
}

const singleChoiceHandler: QuestionTypeHandler = {
  type: 'single_choice',
  validateSelfValue(defIn, raw) {
    const def = asSingleChoiceDef(defIn);
    const keys = optionKeys(def.options);
    if (typeof raw !== 'string' || !keys.has(raw)) {
      return { valid: false, reason: `Expected one of: ${[...keys].join(', ')}` };
    }
    return { valid: true, value: raw };
  },
  validatePreferenceValue(defIn, raw) {
    const def = asSingleChoiceDef(defIn);
    const keys = optionKeys(def.options);
    if (!Array.isArray(raw) || raw.length === 0 || !raw.every((v) => typeof v === 'string' && keys.has(v))) {
      return { valid: false, reason: `Expected a non-empty array of acceptable options from: ${[...keys].join(', ')}` };
    }
    // De-dupe defensively so a caller passing duplicates doesn't skew set-size-based logic elsewhere.
    return { valid: true, value: [...new Set(raw as string[])] };
  },
  satisfaction(_def, selfValue, preferenceValue) {
    const acceptable = preferenceValue as string[];
    return acceptable.includes(selfValue as string) ? 1 : 0;
  },
  isAcceptable(_def, selfValue, preferenceValue) {
    const acceptable = preferenceValue as string[];
    return acceptable.includes(selfValue as string);
  },
};

// ---- multi_choice ------------------------------------------------------

function asMultiChoiceDef(def: QuestionTypeDefinition): MultiChoiceDefinition {
  if (def.type !== 'multi_choice') throw new Error(`Expected multi_choice definition, got "${def.type}"`);
  return def;
}

function validateOptionSet(def: MultiChoiceDefinition, raw: unknown, allowEmpty: boolean): ValidationResult {
  const keys = optionKeys(def.options);
  if (!Array.isArray(raw) || (!allowEmpty && raw.length === 0) || !raw.every((v) => typeof v === 'string' && keys.has(v))) {
    return { valid: false, reason: `Expected an array of options from: ${[...keys].join(', ')}` };
  }
  return { valid: true, value: [...new Set(raw as string[])] };
}

const multiChoiceHandler: QuestionTypeHandler = {
  type: 'multi_choice',
  validateSelfValue(defIn, raw) {
    // A user may legitimately select zero of the options ("none of these apply to me").
    return validateOptionSet(asMultiChoiceDef(defIn), raw, true);
  },
  validatePreferenceValue(defIn, raw) {
    return validateOptionSet(asMultiChoiceDef(defIn), raw, true);
  },
  satisfaction(_def, selfValue, preferenceValue) {
    const self = new Set(selfValue as string[]);
    const pref = preferenceValue as string[];
    // Nothing was requested -> trivially satisfied (no basis to penalize).
    if (pref.length === 0) return 1;
    const overlap = pref.filter((k) => self.has(k)).length;
    const union = new Set([...self, ...pref]).size;
    // Jaccard-style overlap: symmetric, 1 only when the sets match exactly,
    // 0 when disjoint. Chosen over "overlap / preference-size-only" so a
    // candidate who selects everything doesn't trivially max out every
    // multi_choice preference.
    return union === 0 ? 1 : overlap / union;
  },
  isAcceptable(_def, selfValue, preferenceValue) {
    const self = new Set(selfValue as string[]);
    const pref = preferenceValue as string[];
    if (pref.length === 0) return true;
    // Deal breaker on multi_choice: candidate must include AT LEAST ONE of
    // the desired options (e.g. "must speak at least one of: Spanish,
    // French"). See dealBreakers.ts for the documented limitation this
    // implies for filter-row derivation.
    return pref.some((k) => self.has(k));
  },
};

const TYPE_HANDLERS: Record<QuestionType, QuestionTypeHandler> = {
  scale: scaleHandler,
  single_choice: singleChoiceHandler,
  multi_choice: multiChoiceHandler,
  frequency: frequencyHandler,
};

export function getTypeHandler(type: QuestionType): QuestionTypeHandler {
  const handler = TYPE_HANDLERS[type];
  if (!handler) throw new Error(`No handler registered for question type "${type}"`);
  return handler;
}

export function allRegisteredTypes(): QuestionType[] {
  return Object.keys(TYPE_HANDLERS) as QuestionType[];
}
