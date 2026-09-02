import { isAtLeastMinimumAge, MINIMUM_AGE } from '../../domain/age';

export interface SignUpFormValues {
  email: string;
  password: string;
  birthdate: string; // YYYY-MM-DD
  termsAccepted: boolean;
  city: string;
  locationPermission: boolean;
}

export interface SignUpFormErrors {
  email?: string;
  password?: string;
  birthdate?: string;
  termsAccepted?: string;
}

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

/**
 * Pure, no I/O, so it is unit-testable without mounting the screen. The
 * server is still the real authority (it re-checks email uniqueness,
 * password strength, and age), this only catches the obvious cases
 * before a round trip, and it's the one place the "age enforced at
 * eighteen" and "no phone number, no identity document" rules are
 * visible in the form itself.
 */
export function validateSignUpForm(values: SignUpFormValues, today: Date = new Date()): SignUpFormErrors {
  const errors: SignUpFormErrors = {};

  if (!EMAIL_PATTERN.test(values.email.trim())) {
    errors.email = 'Enter a valid email address.';
  }

  if (values.password.length < 8) {
    errors.password = 'Use at least 8 characters.';
  }

  if (!/^\d{4}-\d{2}-\d{2}$/.test(values.birthdate)) {
    errors.birthdate = 'Enter your birthdate as YYYY-MM-DD.';
  } else if (!isAtLeastMinimumAge(values.birthdate, today)) {
    errors.birthdate = `You must be at least ${MINIMUM_AGE} to use Outcome Dating.`;
  }

  if (!values.termsAccepted) {
    errors.termsAccepted = 'You need to accept the terms to continue.';
  }

  return errors;
}

export function hasErrors(errors: SignUpFormErrors): boolean {
  return Object.keys(errors).length > 0;
}
