/// `PopupPositioner`s are responsible for setting the size and position of a
/// popup. They can also decide which animation should be played when the popup

import {
    RioAnimation,
    RioAnimationGroup,
    RioKeyframe,
    RioKeyframeAnimation,
} from "./animations";
import { pixelsPerRem } from "./app";
import { getAllocatedHeightInPx, getAllocatedWidthInPx } from "./utils";

/// is opened or closed.
export abstract class PopupPositioner {
    /// If a popup is quickly opened and closed (or the other way round), the
    /// animation may be interrupted partway. If that happens, we don't want the
    /// popup to "snap" to its final state and then start playing the new
    /// animation, we want to seamlessly switch from one animation to the other.
    /// That's why animations should not hard-code a specific starting keyframe,
    /// but rather start from the element's current state. The `initialCss` is
    /// stored separately and is only applied to the element once, when the
    /// PopupManager is created.
    abstract getInitialCss(): RioKeyframe;

    /// Positions the `content` in the `overlaysContainer` by updating its CSS
    /// *AND* returns the animation for opening the popup
    abstract positionContent(
        anchor: HTMLElement,
        content: HTMLElement,
        overlaysContainer: HTMLElement
    ): RioAnimation;

    abstract getCloseAnimation(
        anchor: HTMLElement,
        content: HTMLElement,
        overlaysContainer: HTMLElement
    ): RioAnimation;

    /// Called when the positioner is replaced with a different one
    cleanup(content: HTMLElement): void {}
}

/// Most `PopupPositioner`s always use the same open/close animation, so this
/// class exists to make that more convenient.
abstract class PopupPositionerWithStaticAnimation extends PopupPositioner {
    private initialCss: RioKeyframe;
    private openAnimation: RioAnimation;
    private closeAnimation: RioAnimation;

    constructor(
        initialCss: RioKeyframe,
        finalCss: RioKeyframe,
        options: KeyframeAnimationOptions
    ) {
        super();

        this.initialCss = initialCss;
        this.openAnimation = new RioKeyframeAnimation([finalCss], options);
        this.closeAnimation = new RioKeyframeAnimation([initialCss], options);
    }

    getInitialCss(): RioKeyframe {
        return this.initialCss;
    }

    positionContent(
        anchor: HTMLElement,
        content: HTMLElement,
        overlaysContainer: HTMLElement
    ): RioAnimation {
        this._positionContent(anchor, content, overlaysContainer);
        return this.openAnimation;
    }

    abstract _positionContent(
        anchor: HTMLElement,
        content: HTMLElement,
        overlaysContainer: HTMLElement
    ): void;

    getCloseAnimation(
        anchor: HTMLElement,
        content: HTMLElement,
        overlaysContainer: HTMLElement
    ): RioAnimation {
        return this.closeAnimation;
    }
}

export class FullscreenPositioner extends PopupPositionerWithStaticAnimation {
    constructor() {
        super(
            { transform: "translateY(-1rem)", opacity: "0" },
            { transform: "translateY(0)", opacity: "1" },
            {
                duration: 200,
                easing: "ease-in-out",
            }
        );
    }

    _positionContent(
        anchor: HTMLElement,
        content: HTMLElement,
        overlaysContainer: HTMLElement
    ): void {
        content.style.minWidth = "100%";
        content.style.minHeight = "100%";
    }
}

export class DropdownPositioner extends PopupPositioner {
    private readonly positioner: PopupPositioner;

    // I have absolutely no clue why this is standard, but on mobile devices
    // dropdowns open up centered on the screen. I guess we'll decide based
    // on whether it's a touchscreen device?
    public static useMobileMode(): boolean {
        if (!window.matchMedia("(pointer: coarse)").matches) {
            return false;
        }

        // Laptops with a touchscreen will also reach this point, but mobile
        // dropdowns look silly on a laptop. So we'll additionally check the
        // screen size.
        let screenSize =
            Math.min(window.screen.width, window.screen.height) / pixelsPerRem;

        return screenSize < 40;
    }

    constructor() {
        super();

        // Since mobile mode and desktop mode use completely different
        // animations and CSS attributes, things would definitely go wrong if a
        // popup were to switch from one mode to the other. So we'll select the
        // mode *once* and stick to it.
        if (DropdownPositioner.useMobileMode()) {
            this.positioner = new MobileDropdownPositioner();
        } else {
            this.positioner = new DesktopDropdownPositioner();
        }
    }

    getInitialCss(): RioKeyframe {
        return this.positioner.getInitialCss();
    }

    positionContent(
        anchor: HTMLElement,
        content: HTMLElement,
        overlaysContainer: HTMLElement
    ): RioAnimation {
        return this.positioner.positionContent(
            anchor,
            content,
            overlaysContainer
        );
    }

    getCloseAnimation(
        anchor: HTMLElement,
        content: HTMLElement,
        overlaysContainer: HTMLElement
    ): RioAnimation {
        return this.positioner.getCloseAnimation(
            anchor,
            content,
            overlaysContainer
        );
    }
}

export class MobileDropdownPositioner extends PopupPositioner {
    private static OPEN_ANIMATION = new RioAnimationGroup([
        new RioKeyframeAnimation(
            [
                {
                    transform: "scale(1)",
                },
            ],
            {
                duration: 200,
                easing: "ease-in-out",
            }
        ),
        new RioKeyframeAnimation(
            [
                {
                    opacity: "1",
                },
            ],
            {
                duration: 100,
                easing: "cubic-bezier(0.5, 0.5, 0.2, 1.14)",
            }
        ),
    ]);
    private static CLOSE_ANIMATION = new RioAnimationGroup([
        new RioKeyframeAnimation(
            [
                {
                    transform: "scale(0)",
                },
            ],
            {
                duration: 200,
                easing: "ease-in-out",
            }
        ),
        new RioKeyframeAnimation(
            [
                {
                    opacity: "0",
                },
            ],
            {
                duration: 200,
                easing: "cubic-bezier(0.5, 0.5, 0.2, 1.14)",
            }
        ),
    ]);

    getInitialCss(): RioKeyframe {
        return {
            transform: "scale(0)",
            opacity: "0",
        };
    }

    positionContent(
        anchor: HTMLElement,
        content: HTMLElement,
        overlaysContainer: HTMLElement
    ): RioAnimation {
        content.classList.add("rio-dropdown-popup-mobile-fullscreen");

        let availableWidth = getAllocatedWidthInPx(overlaysContainer);
        let availableHeight = getAllocatedHeightInPx(overlaysContainer);

        let contentWidth = getAllocatedWidthInPx(content);
        let contentHeight = getAllocatedHeightInPx(content);

        let left = (availableWidth - contentWidth) / 2;
        left = Math.max(left, 0);

        let top = (availableHeight - contentHeight) / 2;
        top = Math.max(top, 0);

        content.style.left = `${left}px`;
        content.style.top = `${top}px`;

        // Assign a minimum width, otherwise it's easy to misclick on a
        // touchscreen
        content.style.minWidth = "10rem";

        return MobileDropdownPositioner.OPEN_ANIMATION;
    }

    getCloseAnimation(
        anchor: HTMLElement,
        content: HTMLElement,
        overlaysContainer: HTMLElement
    ): RioAnimation {
        return MobileDropdownPositioner.CLOSE_ANIMATION;
    }
}

export class DesktopDropdownPositioner extends PopupPositioner {
    positionContent(
        anchor: HTMLElement,
        content: HTMLElement,
        overlaysContainer: HTMLElement
    ): RioAnimation {
        const WINDOW_MARGIN = 0.5 * pixelsPerRem;
        const GAP_IF_ENTIRELY_ABOVE = 0.5 * pixelsPerRem;

        // Get some information about achor & content
        let anchorRect = getAnchorRectInContainer(anchor, overlaysContainer);
        let availableHeight =
            getAllocatedHeightInPx(overlaysContainer) - 2 * WINDOW_MARGIN;

        // Remove the previously assigned dimensions before querying the content
        // size. But since we need the `max-height` for our animation, we need
        // to remember the current `max-height`.
        let startHeight = content.style.maxHeight;
        content.style.minWidth = "unset";
        content.style.maxHeight = `${availableHeight}px`;
        content.style.height = "unset";

        let contentWidth = getAllocatedWidthInPx(content);
        let contentHeight = getAllocatedHeightInPx(content);

        // CSS classes are used to communicate which of the different layouts is
        // used. Remove them all first.
        this.removeCssClasses(content);

        // Make sure the popup is at least as wide as the anchor, while still
        // being able to resize itself in case its content changes
        if (contentWidth < anchorRect.width) {
            content.style.minWidth = `${anchorRect.width}px`;
        }

        let popupWidth = Math.max(contentWidth, anchorRect.width);
        let left = anchorRect.left - (popupWidth - anchorRect.width) / 2;
        content.style.left = `${left}px`;

        // Popup is larger than the window. Give it all the space that's available.
        if (contentHeight >= availableHeight - 2 * WINDOW_MARGIN) {
            content.style.top = `${WINDOW_MARGIN}px`;

            content.classList.add(
                "rio-dropdown-popup-above-and-below",
                "rio-dropdown-popup-scroll-y"
            );
            return this.makeOpenAnimation(startHeight, availableHeight);
        }

        // Popup fits below the dropdown
        if (
            anchorRect.bottom + contentHeight + WINDOW_MARGIN <=
            availableHeight
        ) {
            content.style.top = `${anchorRect.bottom}px`;

            content.classList.add("rio-dropdown-popup-below");
        }
        // Popup fits above the dropdown
        else if (
            anchorRect.top - contentHeight >=
            GAP_IF_ENTIRELY_ABOVE + WINDOW_MARGIN
        ) {
            content.style.top = `${
                anchorRect.top - contentHeight - GAP_IF_ENTIRELY_ABOVE
            }px`;

            content.classList.add("rio-dropdown-popup-above");
        }
        // Popup doesn't fit above or below the dropdown. Center it as much
        // as possible
        else {
            let top =
                anchorRect.top + anchorRect.height / 2 - contentHeight / 2;

            // It looks ugly if the dropdown touches the border of the window, so
            // enforce a small margin on the top and the bottom
            if (top < WINDOW_MARGIN) {
                top = WINDOW_MARGIN;
            } else if (top + contentHeight + WINDOW_MARGIN > availableHeight) {
                top = availableHeight - contentHeight - WINDOW_MARGIN;
            }

            content.style.top = `${top}px`;

            content.classList.add("rio-dropdown-popup-above-and-below");
        }

        return this.makeOpenAnimation(startHeight, contentHeight);
    }

    getInitialCss(): RioKeyframe {
        return {
            maxHeight: "0",
            overflow: "hidden",
        };
    }

    private makeOpenAnimation(
        startHeight: string,
        endHeight: number
    ): RioAnimation {
        return new RioKeyframeAnimation(
            [
                {
                    maxHeight: startHeight,
                },
                // A fixed max-height would prevent the content from resizing
                // itself, so we must remove the max-height at the end.
                {
                    offset: 0.99999,
                    maxHeight: `${endHeight}px`,
                },
                {
                    maxHeight: "unset",
                },
            ],
            { duration: 400, easing: "ease-in-out" }
        );
    }

    getCloseAnimation(
        anchor: HTMLElement,
        content: HTMLElement,
        overlaysContainer: HTMLElement
    ): RioAnimation {
        let currentHeight = getAllocatedHeightInPx(content);

        return new RioKeyframeAnimation(
            [{ maxHeight: `${currentHeight}px` }, { maxHeight: "0" }],
            {
                duration: 400,
                easing: "ease-in-out",
            }
        );
    }

    cleanup(content: HTMLElement): void {
        this.removeCssClasses(content);
    }

    private removeCssClasses(content: HTMLElement): void {
        content.classList.remove(
            "rio-dropdown-popup-above",
            "rio-dropdown-popup-below",
            "rio-dropdown-popup-above-and-below",
            "rio-dropdown-popup-scroll-y"
        );
    }
}

class SidePositioner extends PopupPositioner {
    public gap: number;
    public alignment: number;
    public anchorRelativeX: number;
    public anchorRelativeY: number;
    public contentRelativeX: number;
    public contentRelativeY: number;
    public fixedOffsetXRem: number;
    public fixedOffsetYRem: number;

    private static OPEN_ANIMATION = new RioAnimationGroup([
        new RioKeyframeAnimation(
            [
                {
                    transform: "scale(1)",
                },
            ],
            {
                duration: 200,
                easing: "ease-in-out",
            }
        ),
        new RioKeyframeAnimation(
            [
                {
                    opacity: "1",
                },
            ],
            {
                duration: 100,
                easing: "cubic-bezier(0.5, 0.5, 0.2, 1.14)",
            }
        ),
    ]);
    private static CLOSE_ANIMATION = new RioAnimationGroup([
        new RioKeyframeAnimation(
            [
                {
                    transform: "scale(0)",
                },
            ],
            {
                duration: 200,
                easing: "ease-in-out",
            }
        ),
        new RioKeyframeAnimation(
            [
                {
                    opacity: "0",
                },
            ],
            {
                duration: 200,
                easing: "cubic-bezier(0.5, 0.5, 0.2, 1.14)",
            }
        ),
    ]);

    // The popup location is defined in developer-friendly this function takes
    // a couple floats instead:
    //
    // - Anchor point X & Y (relative)
    // - Content point X & Y (relative)
    // - Offset X & Y (absolute)
    //
    // The popup will be positioned such that the popup point is placed exactly
    // at the anchor point. (But never off the screen.)
    protected constructor({
        anchorRelativeX,
        anchorRelativeY,
        contentRelativeX,
        contentRelativeY,
        fixedOffsetXRem,
        fixedOffsetYRem,
    }: {
        anchorRelativeX: number;
        anchorRelativeY: number;
        contentRelativeX: number;
        contentRelativeY: number;
        fixedOffsetXRem: number;
        fixedOffsetYRem: number;
    }) {
        super();

        this.anchorRelativeX = anchorRelativeX;
        this.anchorRelativeY = anchorRelativeY;
        this.contentRelativeX = contentRelativeX;
        this.contentRelativeY = contentRelativeY;
        this.fixedOffsetXRem = fixedOffsetXRem;
        this.fixedOffsetYRem = fixedOffsetYRem;
    }

    getInitialCss(): RioKeyframe {
        return { transform: "scale(0)", opacity: "0" };
    }

    positionContent(
        anchor: HTMLElement,
        content: HTMLElement,
        overlaysContainer: HTMLElement
    ): RioAnimation {
        let margin = 0.5 * pixelsPerRem;

        let availableWidth =
            getAllocatedWidthInPx(overlaysContainer) - 2 * margin;
        let availableHeight =
            getAllocatedHeightInPx(overlaysContainer) - 2 * margin;

        // Where would we like the content to be?
        let anchorRect = getAnchorRectInContainer(anchor, overlaysContainer);
        let contentWidth = getAllocatedWidthInPx(content);
        let contentHeight = getAllocatedHeightInPx(content);

        let anchorPointX =
            anchorRect.left + anchorRect.width * this.anchorRelativeX;
        let anchorPointY =
            anchorRect.top + anchorRect.height * this.anchorRelativeY;

        let popupPointX = contentWidth * this.contentRelativeX;
        let popupPointY = contentHeight * this.contentRelativeY;

        let popupLeft: number, popupTop: number;

        if (contentWidth >= availableWidth) {
            popupLeft = margin;
        } else {
            popupLeft =
                anchorPointX -
                popupPointX +
                this.fixedOffsetXRem * pixelsPerRem;

            let minX = margin;
            let maxX = minX + availableWidth - contentWidth;
            popupLeft = Math.min(Math.max(popupLeft, minX), maxX);
        }

        if (contentHeight >= availableHeight) {
            popupTop = margin;
        } else {
            popupTop =
                anchorPointY -
                popupPointY +
                this.fixedOffsetYRem * pixelsPerRem;

            let minY = margin;
            let maxY = minY + availableHeight - contentHeight;
            popupTop = Math.min(Math.max(popupTop, minY), maxY);
        }

        // Position & size the popup
        content.style.left = `${popupLeft}px`;
        content.style.top = `${popupTop}px`;

        return SidePositioner.OPEN_ANIMATION;
    }

    getCloseAnimation(
        anchor: HTMLElement,
        content: HTMLElement,
        overlaysContainer: HTMLElement
    ): RioAnimation {
        return SidePositioner.CLOSE_ANIMATION;
    }
}

export class LeftPositioner extends SidePositioner {
    constructor(gap: number, alignment: number) {
        super({
            anchorRelativeX: 0,
            anchorRelativeY: alignment,
            contentRelativeX: 1,
            contentRelativeY: 1 - alignment,
            fixedOffsetXRem: -gap,
            fixedOffsetYRem: 0,
        });
    }
}

export class RightPositioner extends SidePositioner {
    constructor(gap: number, alignment: number) {
        super({
            anchorRelativeX: 1,
            anchorRelativeY: alignment,
            contentRelativeX: 0,
            contentRelativeY: 1 - alignment,
            fixedOffsetXRem: gap,
            fixedOffsetYRem: 0,
        });
    }
}

export class TopPositioner extends SidePositioner {
    constructor(gap: number, alignment: number) {
        super({
            anchorRelativeX: alignment,
            anchorRelativeY: 0,
            contentRelativeX: 1 - alignment,
            contentRelativeY: 1,
            fixedOffsetXRem: 0,
            fixedOffsetYRem: -gap,
        });
    }
}

export class BottomPositioner extends SidePositioner {
    constructor(gap: number, alignment: number) {
        super({
            anchorRelativeX: alignment,
            anchorRelativeY: 1,
            contentRelativeX: 1 - alignment,
            contentRelativeY: 0,
            fixedOffsetXRem: 0,
            fixedOffsetYRem: gap,
        });
    }
}

export class CenterPositioner extends SidePositioner {
    constructor() {
        super({
            anchorRelativeX: 0.5,
            anchorRelativeY: 0.5,
            contentRelativeX: 0.5,
            contentRelativeY: 0.5,
            fixedOffsetXRem: 0,
            fixedOffsetYRem: 0,
        });
    }
}

export class AutoSidePositioner extends PopupPositioner {
    gap: number;
    alignment: number;

    constructor(gap: number, alignment: number) {
        super();

        this.gap = gap;
        this.alignment = alignment;
    }

    getInitialCss(): RioKeyframe {
        return new TopPositioner(0, 0).getInitialCss();
    }

    positionContent(
        anchor: HTMLElement,
        content: HTMLElement,
        overlaysContainer: HTMLElement
    ): RioAnimation {
        let availableWidth = getAllocatedWidthInPx(overlaysContainer);
        let availableHeight = getAllocatedHeightInPx(overlaysContainer);

        let anchorRect = getAnchorRectInContainer(anchor, overlaysContainer);
        let relX = (anchorRect.left + anchor.scrollWidth) / 2 / availableWidth;
        let relY = (anchorRect.top + anchor.scrollHeight) / 2 / availableHeight;

        let positioner: SidePositioner;

        if (relX < 0.2) {
            positioner = new RightPositioner(this.gap, this.alignment);
        } else if (relX > 0.8) {
            positioner = new LeftPositioner(this.gap, this.alignment);
        } else if (relY < 0.2) {
            positioner = new BottomPositioner(this.gap, this.alignment);
        } else {
            positioner = new TopPositioner(this.gap, this.alignment);
        }

        return positioner.positionContent(anchor, content, overlaysContainer);
    }

    getCloseAnimation(
        anchor: HTMLElement,
        content: HTMLElement,
        overlaysContainer: HTMLElement
    ): RioAnimation {
        return new TopPositioner(0, 0).getCloseAnimation(
            anchor,
            content,
            overlaysContainer
        );
    }
}

export function getPositionerByName(
    position:
        | "left"
        | "top"
        | "right"
        | "bottom"
        | "center"
        | "auto"
        | "fullscreen"
        | "dropdown",
    gap: number,
    alignment: number
): PopupPositioner {
    switch (position) {
        case "left":
            return new LeftPositioner(gap, alignment);
        case "top":
            return new TopPositioner(gap, alignment);
        case "right":
            return new RightPositioner(gap, alignment);
        case "bottom":
            return new BottomPositioner(gap, alignment);
        case "center":
            return new CenterPositioner();
        case "auto":
            return new AutoSidePositioner(gap, alignment);
        case "fullscreen":
            return new FullscreenPositioner();
        case "dropdown":
            return new DropdownPositioner();
    }
}

function getAnchorRectInContainer(
    anchor: HTMLElement,
    overlaysContainer: HTMLElement
): DOMRect {
    // Assumptions made here:
    // 1. The overlaysContainer is positioned at (0, 0) in the viewport
    // 2. Neither element is affected by `filter: scale` (which would distort
    //    the relation between "CSS pixels" and "visible pixels")
    return anchor.getBoundingClientRect();
}
