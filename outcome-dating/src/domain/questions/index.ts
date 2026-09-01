/**
 * Barrel export for the redesigned compatibility question domain. See
 * each module for detailed docs; this file just re-exports the public
 * surface so callers can `import { ... } from '../domain/questions/index.js'`
 * (or the individual files directly).
 */
export * from './types.js';
export * from './importance.js';
export * from './typeHandlers.js';
export * from './ladder.js';
export * from './scoring.js';
export * from './selector.js';
export * from './dealBreakers.js';
export * from './tags.js';
