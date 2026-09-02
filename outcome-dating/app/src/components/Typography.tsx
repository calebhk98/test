import React from 'react';
import { Text, TextProps } from 'react-native';
import { colors, fontSizes } from '../theme/tokens';

/**
 * `allowFontScaling` stays at its RN default (true) throughout this
 * file deliberately: the task requires the layout to survive a large
 * system text setting, so nothing here opts out of scaling.
 */

export function Headline(props: TextProps): React.ReactElement {
  return <Text accessibilityRole="header" {...props} style={[{ fontSize: fontSizes.headline, fontWeight: '700', color: colors.textPrimary }, props.style]} />;
}

export function Title(props: TextProps): React.ReactElement {
  return <Text accessibilityRole="header" {...props} style={[{ fontSize: fontSizes.title, fontWeight: '700', color: colors.textPrimary }, props.style]} />;
}

export function Body(props: TextProps): React.ReactElement {
  return <Text {...props} style={[{ fontSize: fontSizes.body, color: colors.textPrimary, lineHeight: 22 }, props.style]} />;
}

export function BodyLarge(props: TextProps): React.ReactElement {
  return <Text {...props} style={[{ fontSize: fontSizes.bodyLarge, color: colors.textPrimary, lineHeight: 24 }, props.style]} />;
}

export function Caption(props: TextProps): React.ReactElement {
  return <Text {...props} style={[{ fontSize: fontSizes.caption, color: colors.textSecondary, lineHeight: 18 }, props.style]} />;
}
