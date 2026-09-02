import type { ImportanceLevel } from '../api/types';

export const IMPORTANCE_LEVELS: readonly ImportanceLevel[] = ['irrelevant', 'slight', 'important', 'critical', 'deal_breaker'];

export const IMPORTANCE_LABELS: Record<ImportanceLevel, string> = {
  irrelevant: "Doesn't matter",
  slight: 'Slight preference',
  important: 'Important',
  critical: 'Very important',
  deal_breaker: 'Deal breaker',
};
