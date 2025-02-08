/// Helper class for creating pop-up elements.
///
/// Many components need to only display an element on occasion, and have it
/// hover over the rest of the page. This is surprisingly difficult to do,
/// because adding elements right in the HTML tree can cause them to be cut off
/// by `overflow: hidden`, or other elements with a higher index. A simple
/// `z-index` doesn't fix this either.
///
/// This class instead functions by adding the content close to the HTML root,
/// and programmatically moves it to the right place.
///
/// While open, the content is assigned the CSS class `rio-popup-manager-open`.
///
/// The popup manager may assign classes or CSS to both `content` and `anchor`.
/// This means you can't pass in a rio component directly (since they could move
/// outside of the manager in the future, leaving them tainted). If you need to
/// pass a rio component, wrap it in a div.

// FIXME: This thing is a mess. Some of the problems we currently have:
// - Shadows and corner radius. The `DropdownPositioner`s need `overflow-hidden`
//   for their animation, which prevents the content from creating a shadow.
//   `DropdownPositioner`s "solved" this issue by adding `box-shadow` to their
//   "initalCss". `Popup`s needed more control, so now we additionally have
//   properties for controlling the shadow in the `PopupManager`.
// - The "look" of the popup and how it interacts with scrolling. In particular,
//   `Popup`s want to wrap their content in a `Card`-like container, but it
//   looks ugly if a scroll bar appears outside of the card and its rounded
//   borders. (And we can't just let take the responsibility of scrolling away
//   from the `PopupPositioner`s because the `DropdownPositioner` has to
//   allocate extra space for the scroll bar.)

import {
    RioAnimation,
    RioAnimationGroup,
    RioKeyframe,
    RioKeyframeAnimation,
} from "./animations";
import { pixelsPerRem } from "./app";
import {
    componentsById,
    getComponentByElement,
    getRootComponent,
} from "./componentManagement";
import { DialogContainerComponent } from "./components/dialogContainer";
import {
    camelToKebab,
    getAllocatedHeightInPx,
    getAllocatedWidthInPx,
    getNaturalSizeInPixelsAndPreserveScrollPosition,
    getScrollBarSizeInPixels,
    OnlyResizeObserver,
    reprElement,
} from "./utils";

export class Popup {
    public readonly style: CSSStyleDeclaration;
    public readonly scrollBarWidth = getScrollBarSizeInPixels();
    public readonly scrollBarHeight = getScrollBarSizeInPixels();
    private readonly scroller: HTMLElement;

    constructor(
        public readonly anchor: HTMLElement,
        public readonly content: HTMLElement,
        public readonly overlaysContainer: HTMLElement,
        public readonly element: HTMLElement
    ) {
        this.style = element.style;
        this.scroller = element.firstChild as HTMLElement;
    }

    set scrollX(scroll: "auto" | "always" | "never") {
        this.element.dataset.scrollX = scroll;
    }

    set scrollY(scroll: "auto" | "always" | "never") {
        this.element.dataset.scrollY = scroll;
    }

    getNaturalSize(): [number, number] {
        return getNaturalSizeInPixelsAndPreserveScrollPosition(
            this.content,
            this.scroller
        );
    }
}

/// `PopupPositioner`s are responsible for setting the size and position of a
/// popup. They can also decide which animation should be played when the popup
/// is opened or closed.
export abstract class PopupPositioner {
    /// If a popup is quickly opened and closed (or the other way round), the
    /// animation may be interrupted partway. If that happens, we don't want the
    /// popup to "snap" to its final state and then start playing the new
    /// animation, we want to seamlessly switch from one animation to the other.
    /// That's why `PopupManagerAnimation`s should not hard-code a specific
    /// starting keyframe, but rather start from the element's current state.
    /// The `initialState` is stored separately and is only applied to the
    /// element once, when the PopupManager is created.
    abstract getInitialCss(): RioKeyframe;

    /// Positions the `content` in the `overlaysContainer` by updating its CSS
    /// *AND* returns the animation for opening the popup
    abstract positionContent(popup: Popup): RioAnimation;

    abstract getCloseAnimation(popup: Popup): RioAnimation;
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

    positionContent(popup: Popup): RioAnimation {
        this._positionContent(popup);
        return this.openAnimation;
    }

    abstract _positionContent(popup: Popup): void;

    getCloseAnimation(popup: Popup): RioAnimation {
        return this.closeAnimation;
    }
}

export class FullscreenPositioner extends PopupPositionerWithStaticAnimation {
    constructor() {
        super(
            { transform: "translateY(-1rem)", opacity: "0" },
            { transform: "translateY(0)", opacity: "1" },
            {
                duration: 200, // 0.2s
                easing: "ease-in-out",
            }
        );
    }

    _positionContent(popup: Popup): void {
        popup.style.left = "0";
        popup.style.top = "0";
        popup.style.width = "100%";
        popup.style.height = "100%";

        popup.scrollX = "auto";
        popup.scrollY = "auto";
    }
}

export class DropdownPositioner extends PopupPositioner {
    private readonly positioner: PopupPositioner;

    // I have absolutely no clue why this is standard, but on mobile devices
    // dropdowns open up centered on the screen. I guess we'll decide based
    // on whether it's a touchscreen device?
    //
    // Note: Since mobile mode and desktop mode use completely different
    // animations and CSS attributes, things would definitely go wrong if a
    // popup were to switch from one mode to the other. So we'll select the
    // mode *once* and stick to it.
    public static readonly USE_MOBILE_MODE =
        window.matchMedia("(pointer: coarse)").matches;

    constructor() {
        super();

        if (DropdownPositioner.USE_MOBILE_MODE) {
            this.positioner = new MobileDropdownPositioner();
        } else {
            this.positioner = new DesktopDropdownPositioner();
        }
    }

    getInitialCss(): RioKeyframe {
        return this.positioner.getInitialCss();
    }

    positionContent(popup: Popup): RioAnimation {
        return this.positioner.positionContent(popup);
    }

    getCloseAnimation(popup: Popup): RioAnimation {
        return this.positioner.getCloseAnimation(popup);
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
                duration: 100,
                easing: "cubic-bezier(0.5, 0.5, 0.2, 1.14)",
            }
        ),
    ]);

    getInitialCss(): RioKeyframe {
        return {
            transform: "scale(0)",
            opacity: "0",
            boxShadow: "0 0 1rem var(--rio-global-shadow-color)",
        };
    }

    positionContent(popup: Popup): RioAnimation {
        let WINDOW_MARGIN = 0.5 * pixelsPerRem;

        // Apply the CSS class *before* we query the size of the content
        popup.content.classList.add("rio-dropdown-popup-mobile-fullscreen");

        let availableWidth =
            getAllocatedWidthInPx(popup.overlaysContainer) - 2 * WINDOW_MARGIN;
        let availableHeight =
            getAllocatedHeightInPx(popup.overlaysContainer) - 2 * WINDOW_MARGIN;
        let [popupWidth, popupHeight] = popup.getNaturalSize();

        if (popupHeight > availableHeight) {
            popupWidth += popup.scrollBarWidth;
        }

        popupWidth = Math.min(popupWidth, availableWidth);
        popupHeight = Math.min(popupHeight, availableHeight);

        popup.style.width = `${popupWidth}px`;
        popup.style.height = `${popupHeight}px`;
        popup.style.left = `${
            WINDOW_MARGIN + (availableWidth - popupWidth) / 2
        }px`;
        popup.style.top = `${
            WINDOW_MARGIN + (availableHeight - popupHeight) / 2
        }px`;

        return MobileDropdownPositioner.OPEN_ANIMATION;
    }

    getCloseAnimation(popup: Popup): RioAnimation {
        return MobileDropdownPositioner.CLOSE_ANIMATION;
    }
}

export class DesktopDropdownPositioner extends PopupPositioner {
    // TODO: If the dropdown is too large for the screen, it seems to sometimes
    // open up scrolled all the way to the bottom. No idea why and I can't
    // reproduce it now.
    positionContent(popup: Popup): RioAnimation {
        // Get some information about achor & content
        let anchorRect = getAnchorRectInContainer(popup);
        let availableHeight = getAllocatedHeightInPx(popup.overlaysContainer);
        let [contentWidth, contentHeight] = popup.getNaturalSize();

        const WINDOW_MARGIN = 0.5 * pixelsPerRem;
        const GAP_IF_ENTIRELY_ABOVE = 0.5 * pixelsPerRem;

        // CSS classes are used to communicate which of the different layouts is
        // used. Remove them all first.
        popup.content.classList.remove(
            "rio-dropdown-popup-above",
            "rio-dropdown-popup-below",
            "rio-dropdown-popup-above-and-below"
        );

        // Make sure the popup is at least as wide as the anchor, while still
        // being able to resize itself in case its content changes
        if (contentWidth < anchorRect.width) {
            popup.style.minWidth = `${anchorRect.width}px`;
        } else {
            popup.style.minWidth = "unset";
        }

        let popupWidth = Math.max(contentWidth, anchorRect.width);
        let left = anchorRect.left - (popupWidth - anchorRect.width) / 2;
        popup.style.left = `${left}px`;

        // Popup is larger than the window. Give it all the space that's available.
        if (contentHeight >= availableHeight - 2 * WINDOW_MARGIN) {
            // Make sure there's enough space for the vertical scroll bar
            if (contentWidth + popup.scrollBarWidth > anchorRect.width) {
                popupWidth = contentWidth + popup.scrollBarWidth;
                left = anchorRect.left - (popupWidth - anchorRect.width) / 2;
                popup.style.left = `${left}px`;
            }

            popup.style.top = `${WINDOW_MARGIN}px`;
            popup.style.height = `${availableHeight - 2 * WINDOW_MARGIN}px`;

            popup.scrollY = "always";

            popup.content.classList.add("rio-dropdown-popup-above-and-below");
            return this.makeOpenAnimation(contentHeight);
        }

        // We know the popup fits on the screen, so disable the vertical scroll
        // bar. Since we're animating the max-height, the scroll bar would be
        // visible during the animation. Not only is it ugly, but it messes up
        // the layout as well.
        popup.scrollY = "never";

        // Set the height. This may(?) prevent the popup from resizing itself,
        // but the `max-height` is used by the animation, so we don't really
        // have a choice.
        popup.style.height = `${contentHeight}px`;

        // Popup fits below the dropdown
        if (
            anchorRect.bottom + contentHeight + WINDOW_MARGIN <=
            availableHeight
        ) {
            popup.style.top = `${anchorRect.bottom}px`;

            popup.content.classList.add("rio-dropdown-popup-below");
        }
        // Popup fits above the dropdown
        else if (
            anchorRect.top - contentHeight >=
            GAP_IF_ENTIRELY_ABOVE + WINDOW_MARGIN
        ) {
            popup.style.top = `${
                anchorRect.top - contentHeight - GAP_IF_ENTIRELY_ABOVE
            }px`;

            popup.content.classList.add("rio-dropdown-popup-above");
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

            popup.style.top = `${top}px`;

            popup.content.classList.add("rio-dropdown-popup-above-and-below");
        }

        return this.makeOpenAnimation(contentHeight);
    }

    getInitialCss(): RioKeyframe {
        return {
            maxHeight: "0",
            overflow: "hidden",
            boxShadow: "0 0 1rem var(--rio-global-shadow-color)",
        };
    }

    private makeOpenAnimation(contentHeight: number): RioAnimation {
        return new RioKeyframeAnimation(
            [
                {
                    maxHeight: `${contentHeight}px`,
                },
            ],
            { duration: 400, easing: "ease-in-out" }
        );
    }

    getCloseAnimation(popup: Popup): RioAnimation {
        return new RioKeyframeAnimation([{ maxHeight: "0" }], {
            duration: 400,
            easing: "ease-in-out",
        });
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
                duration: 100,
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

    positionContent(popup: Popup): RioAnimation {
        let margin = 1 * pixelsPerRem;

        let availableWidth =
            getAllocatedWidthInPx(popup.overlaysContainer) - 2 * margin;
        let availableHeight =
            getAllocatedHeightInPx(popup.overlaysContainer) - 2 * margin;

        // Where would we like the content to be?
        let anchorRect = getAnchorRectInContainer(popup);
        let [contentWidth, contentHeight] = popup.getNaturalSize();

        if (contentHeight > availableHeight) {
            contentWidth += popup.scrollBarWidth;
        }

        // Clamp the size of the popup to fit the screen
        let popupWidth = Math.min(contentWidth, availableWidth);
        let popupHeight = Math.min(contentHeight, availableHeight);

        let anchorPointX =
            anchorRect.left + anchorRect.width * this.anchorRelativeX;
        let anchorPointY =
            anchorRect.top + anchorRect.height * this.anchorRelativeY;

        let popupPointX = popupWidth * this.contentRelativeX;
        let popupPointY = popupHeight * this.contentRelativeY;

        let popupLeft =
            anchorPointX - popupPointX + this.fixedOffsetXRem * pixelsPerRem;
        let popupTop =
            anchorPointY - popupPointY + this.fixedOffsetYRem * pixelsPerRem;

        // Establish limits, so the popup doesn't go off the screen. This is
        // relative to the popup's top left corner.
        let minX = margin;
        let maxX = minX + availableWidth - popupWidth;

        let minY = margin;
        let maxY = minY + availableHeight - popupHeight;

        // Enforce the limits
        popupLeft = Math.min(Math.max(popupLeft, minX), maxX);
        popupTop = Math.min(Math.max(popupTop, minY), maxY);

        // Debug display
        // console.log("Anchor:", anchor);
        // console.log(
        //     `Anchor: (${anchorRect.left}, ${anchorRect.top}) ${anchorRect.width}x${anchorRect.height}`
        // );
        // console.log(
        //     `Content: (${contentLeft}, ${contentTop}) ${contentWidth}x${contentHeight}`
        // );

        // let div = document.createElement("div");
        // document.body.appendChild(div);

        // div.style.backgroundColor = "red";
        // div.style.position = "fixed";

        // div.style.left = `${anchorRect.left}px`;
        // div.style.top = `${anchorRect.top}px`;
        // div.style.width = `${anchorRect.width}px`;
        // div.style.height = `${anchorRect.height}px`;

        // div.style.left = `${contentLeft}px`;
        // div.style.top = `${contentTop}px`;
        // div.style.width = `${contentWidth}px`;
        // div.style.height = `${contentHeight}px`;

        // Position & size the popup
        popup.style.left = `${popupLeft}px`;
        popup.style.top = `${popupTop}px`;
        popup.style.width = `${popupWidth}px`;
        popup.style.height = `${popupHeight}px`;

        popup.scrollX = popup.scrollY = "auto";

        return SidePositioner.OPEN_ANIMATION;
    }

    getCloseAnimation(popup: Popup): RioAnimation {
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

    positionContent(popup: Popup): RioAnimation {
        let availableWidth = getAllocatedWidthInPx(popup.overlaysContainer);
        let availableHeight = getAllocatedHeightInPx(popup.overlaysContainer);

        let anchorRect = getAnchorRectInContainer(popup);
        let relX =
            (anchorRect.left + popup.anchor.scrollWidth) / 2 / availableWidth;
        let relY =
            (anchorRect.top + popup.anchor.scrollHeight) / 2 / availableHeight;

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

        return positioner.positionContent(popup);
    }

    getCloseAnimation(popup: Popup): RioAnimation {
        return new TopPositioner(0, 0).getCloseAnimation(popup);
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

    throw new Error(`Invalid position: ${position}`);
}

/// Will always be on top of everything else.
export class PopupManager {
    private _anchor: HTMLElement;
    private content: HTMLElement;
    private _userClosable: boolean;
    private _popup: Popup | null = null;

    /// Inform the outside world when the popup was closed by the user, rather
    /// than programmatically.
    public onUserClose?: () => void;

    private _isOpen: boolean = false;

    /// Used to darken the screen if the popup is modal.
    private shadeElement: HTMLElement;

    /// This is the element that gets positioned by the PopupPositioner. It's
    /// also responsible for scrolling the `content`.
    private popupContainer: HTMLElement;

    /// We have multiple containers for overlays. The correct one is determined
    /// based on the anchor's position in the DOM. Most of the time when a
    /// PopupManager is created, the anchor isn't in the DOM yet, so we must
    /// initialize this variable lazily.
    private _overlaysContainer: HTMLElement | null = null;

    /// Where the pop-up should be positioned relative to the anchor.
    ///
    /// This is taken as a hint, but can be ignored if there isn't enough space
    /// to fit the pop-up at that location.
    private _positioner: PopupPositioner;

    /// Listen for interactions with the outside world, so they can close the
    /// popup if user-closable.
    private clickHandler: ((event: MouseEvent) => void) | null = null;

    // Event handlers for repositioning the popup
    private scrollHandler: ((event: Event) => void) | null = null;
    private resizeObserver: OnlyResizeObserver | null = null;
    private anchorPositionPoller: number | null = null;
    private previousAnchorRect: DOMRect | null = null;

    constructor({
        anchor,
        content,
        positioner,
        modal,
        userClosable,
        onUserClose,
    }: {
        anchor: HTMLElement;
        content: HTMLElement;
        positioner: PopupPositioner;
        modal: boolean;
        userClosable: boolean;
        onUserClose?: () => void;
    }) {
        // Configure the popup
        this._anchor = anchor;
        this.content = content;
        this._positioner = positioner;
        this.onUserClose = onUserClose;

        // Prepare the HTML
        this.shadeElement = document.createElement("div");
        this.shadeElement.classList.add("rio-popup-manager-shade");

        // Create helper elements required for scrolling
        this.popupContainer = document.createElement("div");
        this.popupContainer.classList.add(
            "rio-popup-manager-scroller",
            "rio-scroll-container"
        );
        this.popupContainer.dataset.scrollX = "auto";
        this.popupContainer.dataset.scrollY = "auto";
        Object.assign(this.popupContainer.style, positioner.getInitialCss());
        this.shadeElement.appendChild(this.popupContainer);

        let helperElement1 = document.createElement("div");
        this.popupContainer.appendChild(helperElement1);

        let helperElement2 = document.createElement("div");
        helperElement1.appendChild(helperElement2);
        helperElement2.appendChild(this.content);

        // Call the setters last, as they might expect the instance to be
        // initialized
        this.modal = modal;
        this.userClosable = userClosable;
    }

    // These setters for the shadow style are here because the
    // `DropdownPositioner` uses `overflow: hidden`, which prevents the popup
    // content from creating the shadow.
    public set cornerRadius(
        cornerRadius: number | [number, number, number, number]
    ) {
        if (typeof cornerRadius === "number") {
            this.popupContainer.style.borderRadius = `${cornerRadius}rem`;
        } else {
            this.popupContainer.style.borderRadius = `${cornerRadius[0]}rem ${cornerRadius[1]}rem ${cornerRadius[2]}rem ${cornerRadius[3]}rem`;
        }
    }

    public set shadowRadius(shadowRadius: number) {
        this.popupContainer.style.boxShadow = `0 0 ${shadowRadius}rem var(--rio-global-shadow-color)`;
    }

    public get anchor(): HTMLElement {
        return this._anchor;
    }

    public set anchor(anchor: HTMLElement) {
        this._anchor = anchor;

        // *Technically* we should update the `overlaysContainer` as well, but I
        // don't think it can actually be different than before. And we could
        // run into problems if the new anchor isn't attached to the DOM yet.

        if (this._popup !== null) {
            this._popup = new Popup(
                anchor,
                this.content,
                this.overlaysContainer,
                this.popupContainer
            );
        }

        if (this.isOpen) {
            this._positionContent();
        }
    }

    public get positioner(): PopupPositioner {
        return this._positioner;
    }

    public set positioner(positioner: PopupPositioner) {
        // Not all positioners use the same CSS attributes to position the
        // content (e.g. some might use `width` while others use `min-width`).
        // To prevent issues, we clear all the commonly used layouting.
        for (let prop of [
            "left",
            "right",
            "top",
            "bottom",
            "width",
            "height",
            "min-width",
            "min-height",
            "max-width",
            "max-height",
        ]) {
            this.popupContainer.style.removeProperty(prop);
        }

        let oldInitialCss = this.positioner.getInitialCss();
        let newInitialCss = positioner.getInitialCss();

        for (let key of Object.keys(oldInitialCss)) {
            this.popupContainer.style.removeProperty(camelToKebab(key));
        }

        Object.assign(this.popupContainer.style, newInitialCss);

        this._positioner = positioner;

        // If the popup is currently open, we just messed up its layout.
        // Reposition it.
        if (this.isOpen) {
            // Repositioning alone isn't enough. Because we never played the
            // open animation, the popup is almost certainly invisible right
            // now. We need to style it as if the open animation had played.
            let animation = this._positionContent();
            animation.applyFinalCss(this.popupContainer);
        }
    }

    private get overlaysContainer(): HTMLElement {
        if (this._overlaysContainer === null) {
            this._overlaysContainer = findOverlaysContainer(this._anchor);
        }

        return this._overlaysContainer;
    }

    private get popup(): Popup {
        if (this._popup === null) {
            this._popup = new Popup(
                this._anchor,
                this.content,
                this.overlaysContainer,
                this.popupContainer
            );
        }

        return this._popup;
    }

    private removeEventHandlers(): void {
        if (this.clickHandler !== null) {
            window.removeEventListener("click", this.clickHandler, true);
        }

        if (this.scrollHandler !== null) {
            window.removeEventListener("scroll", this.scrollHandler, true);
        }

        if (this.resizeObserver !== null) {
            this.resizeObserver.disconnect();
            this.resizeObserver = null;
        }

        if (this.anchorPositionPoller !== null) {
            window.clearInterval(this.anchorPositionPoller);
            this.previousAnchorRect = null;
        }
    }

    destroy(): void {
        this.removeEventHandlers();
        this.shadeElement.remove();
    }

    private _positionContent(): RioAnimation {
        // Run the positioner
        return this._positioner.positionContent(this.popup);
    }

    private _onPointerDown(event: MouseEvent): void {
        // If the popup isn't user-closable or not even open, there's nothing
        // to do
        if (!this.userClosable || !this.isOpen) {
            return;
        }

        // Check if the interaction was with the anchor or its children. This
        // allows the anchor to decide its own behavior.
        if (this._anchor.contains(event.target as Node)) {
            return;
        }

        // Check if the interaction was with the popup or its children
        if (this.popupContainer.contains(event.target as Node)) {
            return;
        }

        // Otherwise, close the popup
        this.isOpen = false;

        // Tell the outside world
        if (this.onUserClose !== undefined) {
            this.onUserClose();
        }

        // Don't consider the event to be handled. Any clicks should still do
        // whatever they were going to do. The exception here are modal popups,
        // but the modal shade already takes care of that.
    }

    private _repositionContentIfPositionChanged(): void {
        let anchorRect = this._anchor.getBoundingClientRect();

        if (
            this.previousAnchorRect === null ||
            anchorRect.left !== this.previousAnchorRect.left ||
            anchorRect.top !== this.previousAnchorRect.top
        ) {
            this._positionContent();
        }

        this.previousAnchorRect = anchorRect;
    }

    get isOpen(): boolean {
        return this._isOpen;
    }

    set isOpen(open: boolean) {
        // Do nothing if the state hasn't changed.
        if (open === this.isOpen) {
            return;
        }
        this._isOpen = open;

        if (open) {
            this._openPopup();
        } else {
            this._closePopup();
        }
    }

    private _openPopup(): void {
        // Add the popup to the DOM
        this.overlaysContainer.appendChild(this.shadeElement);

        // Attach event handlers that don't mess with the popup animation. (i.e.
        // those that don't reposition/resize the content)
        let clickHandler = this._onPointerDown.bind(this);
        this.clickHandler = clickHandler; // Shuts up the type checker
        window.addEventListener("pointerdown", clickHandler, true);

        // Position the popup
        let animation = this._positionContent();

        // Start playing the popup animation. This may temporarily override the
        // position/size of the popup.
        //
        // Once the animation is complete, we'll attach a bunch of event
        // listeners that reposition the popup in case the user scrolls or the
        // anchor changes size or whatever. These can mess with the animation,
        // which is why we don't attach them right away.
        let playback = animation.animate(this.popupContainer);

        playback.addEventListener("finish", () => {
            let repositionContent = this._positionContent.bind(this);
            let repositionContentIfPositionChanged =
                this._repositionContentIfPositionChanged.bind(this);

            // The 'scroll' event is triggered when *any* element scrolls. We
            // should only reposition the popup if scrolling actually caused it
            // to move.
            this.scrollHandler = repositionContentIfPositionChanged;
            window.addEventListener(
                "scroll",
                repositionContentIfPositionChanged,
                true
            );

            this.resizeObserver = new OnlyResizeObserver(
                [this._anchor, this.content],
                repositionContent
            );

            this.anchorPositionPoller = window.setInterval(
                repositionContentIfPositionChanged,
                100
            );

            // Reposition right away, just in case something happened during the
            // animation
            //
            // TODO: I don't know why, but for some reason the content is
            // repositioned more than once
            repositionContent();
        });
    }

    private _closePopup(): void {
        this.removeEventHandlers();

        // Play the close animation and remove the popup when the animation
        // is complete.
        let animation = this._positioner.getCloseAnimation(this.popup);
        let playback = animation.animate(this.popupContainer);

        // Note: The popup can be re-opened before the close animation has
        // completed. I believe this will "cancel" the animation and
        // "finish" won't be triggered. But that's fine, we don't need to
        // remove the element from the DOM in that case anyway.

        // Note: Don't worry, the 'finish' event is properly triggered even
        // though nobody is holding a reference to the `playback` object.
        playback.addEventListener("finish", () => {
            this.shadeElement.remove();
        });
    }

    set modal(modal: boolean) {
        this.shadeElement.classList.toggle("rio-popup-manager-modal", modal);
    }

    get userClosable(): boolean {
        return this._userClosable;
    }

    set userClosable(userClosable: boolean) {
        this._userClosable = userClosable;
    }
}

/// Depending on where the anchor is located, the overlay needs to be placed in
/// the corresponding overlays container:
/// - user content: user overlays container
/// - connection lost popup: connection lost popup container
/// - dev tools: dev tools overlays container
function findOverlaysContainer(anchor: HTMLElement): HTMLElement {
    let element: HTMLElement | null = anchor;

    while (element !== null) {
        if (
            element.classList.contains("rio-user-root-container-inner") ||
            element.classList.contains("rio-user-overlays-container")
        ) {
            return getRootComponent().userOverlaysContainer;
        }

        if (
            element.classList.contains("rio-connection-lost-popup-container") ||
            element.classList.contains(
                "rio-connection-lost-popup-overlays-container"
            )
        ) {
            return getRootComponent().connectionLostPopupOverlaysContainer;
        }

        if (
            element.classList.contains("rio-dev-tools-container") ||
            element.classList.contains("rio-dev-tools-overlays-container")
        ) {
            return getRootComponent().devToolsOverlaysContainer;
        }

        // Special case: DialogContainers aren't ever added to the DOM, so it
        // makes no sense to continue with the parent element. Instead, we have
        // to look up the element of the Component that owns the dialog.
        if (element.classList.contains("rio-dialog-container")) {
            let dialogComponent = getComponentByElement(
                element
            ) as DialogContainerComponent;

            let ownerComponent =
                componentsById[dialogComponent.state.owning_component_id]!;

            element = ownerComponent.element;

            // TODO: At least right now, all of the code above is actually
            // unnecessary because the owner of *every* dialog is the
            // fundamental root component. This means we can't determine the
            // "location" of dialogs. Since there are no dialogs in the dev
            // tools as of yet, and only crazy people would spawn dialogs in
            // their connection lost popup, we'll just treat this as user
            // content.
            if (element.classList.contains("rio-fundamental-root-component")) {
                return getRootComponent().userOverlaysContainer;
            }
        } else {
            element = element.parentElement;
        }
    }

    throw new Error(
        `Couldn't find overlays container for anchor ${reprElement(anchor)}`
    );
}

function getAnchorRectInContainer(popup: Popup): DOMRect {
    // Assumptions made here:
    // 1. The overlaysContainer is positioned at (0, 0) in the viewport
    // 2. Neither element is affected by `filter: scale` (which would distort
    //    the relation between "CSS pixels" and "visible pixels")
    return popup.anchor.getBoundingClientRect();
}
