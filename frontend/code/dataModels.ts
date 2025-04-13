export type ComponentId = number & { __brand: "ComponentId" };

export type RioScrollBehavior = "never" | "auto" | "always";

export type Color = [number, number, number, number];

export const COLOR_SET_NAMES = [
    "primary",
    "secondary",
    "background",
    "neutral",
    "hud",
    "disabled",
    "success",
    "warning",
    "danger",
    "keep",
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
    type: "solid";
    color: Color;
};
export type LinearGradientFill = {
    type: "linearGradient";
    angleDegrees: number;
    stops: [Color, number][];
};
export type RadialGradientFill = {
    type: "radialGradient";
    centerX: number;
    centerY: number;
    stops: [Color, number][];
};
export type ImageFill = {
    type: "image";
    imageUrl: string;
    fillMode: "fit" | "stretch" | "zoom" | "tile";
    tileSize: [number, number];
};
export type FrostedGlassFill = {
    type: "frostedGlass";
    color: Color;
    blurSize: number;
};
export type AnyFill =
    | SolidFill
    | LinearGradientFill
    | RadialGradientFill
    | ImageFill
    | FrostedGlassFill;

export type TextCompatibleFill =
    | Color
    | SolidFill
    | LinearGradientFill
    | RadialGradientFill
    | ImageFill;
export type TextStyle = {
    fontName: string | null;
    fill: TextCompatibleFill | null;
    fontSize: number | null;
    italic: boolean | null;
    fontWeight: "normal" | "bold" | null;
    underlined: boolean | null;
    strikethrough: boolean | null;
    allCaps: boolean | null;
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

    variant: "light" | "dark";
};

/// Contains layout information about a single component
export type ComponentLayout = {
    /// The minimum amount of size needed by the component. The width is
    /// calculated first, meaning the height can depend on the width. (i.e. a
    /// text's height depends on the width because it wraps)
    naturalWidth: number;
    naturalHeight: number;

    /// Components can request more space than their natural size if a size was
    /// explicitly provided on the Python-side. This value is the maximum of the
    /// natural size and any explicitly provided size.
    requestedInnerWidth: number;
    requestedInnerHeight: number;

    /// The requested width after scrolling, alignment and margin.
    requestedOuterWidth: number;
    requestedOuterHeight: number;

    /// The amount of space allocated to the component before scrolling,
    /// alignment and margin.
    allocatedOuterWidth: number;
    allocatedOuterHeight: number;

    /// The amount of space allocated to the component after scrolling,
    /// alignment and margin.
    allocatedInnerWidth: number;
    allocatedInnerHeight: number;

    /// The component's position relative to the viewport before scrolling,
    /// alignment and margin.
    leftInViewportOuter: number;
    topInViewportOuter: number;

    /// The component's position relative to the viewport after scrolling,
    /// alignment and margin.
    leftInViewportInner: number;
    topInViewportInner: number;

    /// The id of the parent component, unless this is the root component.
    parentId: ComponentId | null;
};

// Contains layout information about a single component, as used in unittests.
export type UnittestComponentLayout = ComponentLayout & {
    aux: object;
};

export type UnittestClientLayoutInfo = {
    windowWidth: number;
    windowHeight: number;

    componentLayouts: { [componentId: number]: UnittestComponentLayout };
};
