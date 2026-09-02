module.exports = {
  preset: 'jest-expo',
  // Deliberately no transformIgnorePatterns override here: jest-expo's
  // preset already ships the correct one for transforming Expo/RN's
  // ESM-only packages, and overriding it (rather than extending it)
  // replaces that pattern outright and breaks the transform.
  testPathIgnorePatterns: ['/node_modules/', '/.expo/'],
  collectCoverageFrom: ['src/**/*.{ts,tsx}', '!src/**/*.d.ts'],
};
