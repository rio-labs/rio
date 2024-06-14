export type ComponentId = number & { __brand: 'ComponentId' };

export type Color = [number, number, number, number];

export const COLOR_SET_NAMES = [
    'primary',
    'secondary',
    'background',
    'neutral',
    'hud',
    'disabled',
    'success',
    'warning',
    'danger',
    'keep',
] as const;

export type ColorSetName = (typeof COLOR_SET_NAMES)[number];

export type ColorSet =
    | ColorSetName
    | {
          localBg: Color;
          localBgVariant: Color;
          localBgActive: Color;
          localFg: Color;
      };

export type SolidFill = {
    type: 'solid';
    color: Color;
};
export type LinearGradientFill = {
    type: 'linearGradient';
    angleDegrees: number;
    stops: [Color, number][];
};
export type ImageFill = {
    type: 'image';
    imageUrl: string;
    fillMode: 'fit' | 'stretch' | 'zoom';
};
export type FrostedGlassFill = {
    type: 'frostedGlass';
    color: Color;
    blurSize: number;
};
export type AnyFill =
    | SolidFill
    | LinearGradientFill
    | ImageFill
    | FrostedGlassFill;

export type TextStyle = {
    fontName: string | null;
    fill: Color | SolidFill | LinearGradientFill | ImageFill | null;
    fontSize: number;
    italic: boolean;
    fontWeight: 'normal' | 'bold';
    underlined: boolean;
    allCaps: boolean;
};

export type Theme = {
    // The main theme colors
    primaryColor: Color;
    secondaryColor: Color;
    disabledColor: Color;

    primaryColorVariant: Color;
    secondaryColorVariant: Color;
    disabledColorVariant: Color;

    // Surface colors are often used for backgrounds. Most components are placed on
    // top of the surface color.
    backgroundColor: Color;
    surfaceColor: Color;
    surfaceColorVariant: Color;
    surfaceActiveColor: Color;

    // Semantic colors express a meaning, such as positive or negative outcomes
    successColor: Color;
    warningColor: Color;
    dangerColor: Color;

    successColorVariant: Color;
    warningColorVariant: Color;
    dangerColorVariant: Color;

    // Other
    cornerRadiusSmall: number;
    cornerRadiusMedium: number;
    cornerRadiusLarge: number;

    baseSpacing: number;
    shadowRadius: number;
    shadowColor: Color;

    // Text styles
    heading1Style: TextStyle;
    heading2Style: TextStyle;
    heading3Style: TextStyle;
    textStyle: TextStyle;

    headingOnPrimaryColor: Color;
    textOnPrimaryColor: Color;

    headingOnSecondaryColor: Color;
    textOnSecondaryColor: Color;

    textColorOnLight: Color;
    textColorOnDark: Color;

    // Computed (in python) colors
    textOnSuccessColor: Color;
    textOnWarningColor: Color;
    textOnDangerColor: Color;

    variant: 'light' | 'dark';
};
