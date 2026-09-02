import { hasErrors, validateSignUpForm, type SignUpFormValues } from '../signUpValidation';

const today = new Date('2026-09-02T12:00:00Z');

function values(overrides: Partial<SignUpFormValues> = {}): SignUpFormValues {
  return {
    email: 'person@example.com',
    password: 'longenoughpassword',
    birthdate: '2000-01-01',
    termsAccepted: true,
    city: '',
    locationPermission: false,
    ...overrides,
  };
}

describe('validateSignUpForm', () => {
  it('accepts a fully valid, adult submission', () => {
    expect(hasErrors(validateSignUpForm(values(), today))).toBe(false);
  });

  it('rejects an invalid email', () => {
    const errors = validateSignUpForm(values({ email: 'not-an-email' }), today);
    expect(errors.email).toBeDefined();
  });

  it('rejects a short password', () => {
    const errors = validateSignUpForm(values({ password: 'short' }), today);
    expect(errors.password).toBeDefined();
  });

  it('rejects someone under eighteen', () => {
    const errors = validateSignUpForm(values({ birthdate: '2015-01-01' }), today);
    expect(errors.birthdate).toMatch(/18/);
  });

  it('rejects a malformed birthdate', () => {
    const errors = validateSignUpForm(values({ birthdate: '01/01/2000' }), today);
    expect(errors.birthdate).toBeDefined();
  });

  it('requires terms acceptance', () => {
    const errors = validateSignUpForm(values({ termsAccepted: false }), today);
    expect(errors.termsAccepted).toBeDefined();
  });

  it('does not require a phone number or identity document field to be present to pass (there is no such field in the form values at all)', () => {
    const formValues = values();
    expect('phoneNumber' in formValues).toBe(false);
    expect('identityDocument' in formValues).toBe(false);
  });
});
