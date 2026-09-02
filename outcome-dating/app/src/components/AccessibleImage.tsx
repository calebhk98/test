import React from 'react';
import { Image, ImageStyle, StyleProp, View } from 'react-native';
import { colors } from '../theme/tokens';

interface AccessibleImageProps {
  uri: string | null;
  /** Server-provided alt text. Required, not optional: a screen that has no alt text for an image (e.g. it hasn't loaded yet) must pass a real fallback string describing what the image is FOR, never leave this out. */
  alt: string;
  style?: StyleProp<ImageStyle>;
  fallback?: React.ReactNode;
}

/** The one image component every screen uses, so "does this image have accessible alt text" is answerable by grepping for raw `<Image` instead of auditing every screen. */
export function AccessibleImage({ uri, alt, style, fallback }: AccessibleImageProps): React.ReactElement {
  if (!uri) {
    return (
      <View style={[{ backgroundColor: colors.surface }, style]} accessible accessibilityLabel={alt} accessibilityRole="image">
        {fallback}
      </View>
    );
  }
  return <Image source={{ uri }} style={style} accessible accessibilityLabel={alt} accessibilityRole="image" />;
}
