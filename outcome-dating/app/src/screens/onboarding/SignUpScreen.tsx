import React, { useState } from 'react';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { StyleSheet, Switch, View, Text } from 'react-native';
import { Screen } from '../../components/Screen';
import { Title, Body, Caption } from '../../components/Typography';
import { FormField } from '../../components/FormField';
import { Checkbox } from '../../components/Checkbox';
import { Button } from '../../components/Button';
import { colors, spacing } from '../../theme/tokens';
import { useAuth } from '../../state/AuthContext';
import { messageForError } from '../../api/errors';
import { calculateAge } from '../../domain/age';
import { hasErrors, validateSignUpForm, type SignUpFormValues } from './signUpValidation';
import type { AuthStackParamList } from '../../navigation/types';

type Props = NativeStackScreenProps<AuthStackParamList, 'SignUp'>;

const INITIAL_VALUES: SignUpFormValues = {
  email: '',
  password: '',
  birthdate: '',
  termsAccepted: false,
  city: '',
  locationPermission: false,
};

export function SignUpScreen(_props: Props): React.ReactElement {
  const { register } = useAuth();
  const [values, setValues] = useState<SignUpFormValues>(INITIAL_VALUES);
  const [touched, setTouched] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const errors = validateSignUpForm(values);
  const age = calculateAge(values.birthdate);

  async function handleSubmit(): Promise<void> {
    setTouched(true);
    setSubmitError(null);
    if (hasErrors(errors)) return;
    setSubmitting(true);
    try {
      await register({
        email: values.email.trim(),
        password: values.password,
        birthdate: values.birthdate,
        termsAccepted: values.termsAccepted,
        city: values.city.trim() || undefined,
        locationPermission: values.locationPermission,
      });
    } catch (error) {
      setSubmitError(messageForError(error));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Screen>
      <Title style={styles.title}>Create your account</Title>
      <Body style={styles.intro}>We only ever ask for what we need to run the app: your email, a password, and your birthdate to confirm you're eighteen or older. No phone number, no ID photo.</Body>

      <FormField
        label="Email"
        value={values.email}
        onChangeText={(email) => setValues((v) => ({ ...v, email }))}
        keyboardType="email-address"
        autoCapitalize="none"
        autoComplete="email"
        textContentType="emailAddress"
        error={touched ? errors.email : undefined}
      />

      <FormField
        label="Password"
        value={values.password}
        onChangeText={(password) => setValues((v) => ({ ...v, password }))}
        secureTextEntry
        autoCapitalize="none"
        autoComplete="new-password"
        textContentType="newPassword"
        hint="At least 8 characters."
        error={touched ? errors.password : undefined}
      />

      <FormField
        label="Birthdate"
        value={values.birthdate}
        onChangeText={(birthdate) => setValues((v) => ({ ...v, birthdate }))}
        placeholder="YYYY-MM-DD"
        keyboardType="number-pad"
        hint={age !== null ? `That makes you ${age}.` : 'You must be 18 or older to use Outcome Dating.'}
        error={touched ? errors.birthdate : undefined}
      />

      <FormField
        label="City (optional)"
        value={values.city}
        onChangeText={(city) => setValues((v) => ({ ...v, city }))}
        autoCapitalize="words"
      />

      <View style={styles.switchRow}>
        <View style={styles.switchText}>
          <Text style={styles.switchLabel}>Share my location</Text>
          <Caption>Used to show approximate distance to other people. You can turn this off anytime in Settings.</Caption>
        </View>
        <Switch
          value={values.locationPermission}
          onValueChange={(locationPermission) => setValues((v) => ({ ...v, locationPermission }))}
          accessibilityLabel="Share my location"
          accessibilityRole="switch"
          trackColor={{ true: colors.accent, false: colors.border }}
        />
      </View>

      <View style={styles.terms}>
        <Checkbox
          checked={values.termsAccepted}
          onChange={(termsAccepted) => setValues((v) => ({ ...v, termsAccepted }))}
          label="I agree to the Terms of Service and Privacy Policy."
          testID="terms-checkbox"
        />
        {touched && errors.termsAccepted ? (
          <Text style={styles.termsError} accessibilityRole="alert">
            {errors.termsAccepted}
          </Text>
        ) : null}
      </View>

      {submitError ? (
        <Text style={styles.submitError} accessibilityRole="alert">
          {submitError}
        </Text>
      ) : null}

      <Button label="Create account" onPress={handleSubmit} loading={submitting} testID="submit-signup" />
    </Screen>
  );
}

const styles = StyleSheet.create({
  title: { marginBottom: spacing.sm },
  intro: { color: colors.textSecondary, marginBottom: spacing.lg },
  switchRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.md, marginBottom: spacing.md },
  switchText: { flex: 1 },
  switchLabel: { fontSize: 16, fontWeight: '600', color: colors.textPrimary, marginBottom: 2 },
  terms: { marginBottom: spacing.lg },
  termsError: { color: colors.critical, fontSize: 13, fontWeight: '600', marginTop: spacing.xs },
  submitError: { color: colors.critical, fontSize: 14, fontWeight: '600', marginBottom: spacing.md, textAlign: 'center' },
});
