export type ComponentId = number & { __brand: 'ComponentId' };

export type Color = [number, number, number, number];

export type ColorSet =
    | 'primary'
    | 'secondary'
    | 'background'
    | 'neutral'
    | 'hud'
    | 'disabled'
    | 'success'
    | 'warning'
    | 'danger'
    | 'keep'
    | {
          localBg: Color;
          localBgVariant: Color;
          localBgActive: Color;
          localFg: Color;
      };

export type Fill =
    | {
          type: 'solid';
          color: Color;
      }
    | {
          type: 'linearGradient';
          angleDegrees: number;
          stops: [Color, number][];
      }
    | {
          type: 'image';
          imageUrl: string;
          fillMode: 'fit' | 'stretch' | 'tile' | 'zoom';
      };

export type TextStyle = {
    fontName: string | null;
    fill: Color | Fill | null;
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
