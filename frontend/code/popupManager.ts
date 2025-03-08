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

import {
    RioAnimation,
    RioAnimationGroup,
    RioAnimationPlayback,
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
    commitCss,
    getAllocatedHeightInPx,
    getAllocatedWidthInPx,
    OnlyResizeObserver,
    reprElement,
} from "./utils";

const enableSafariScrollingWorkaround = /^((?!chrome|android).)*safari/i.test(
    navigator.userAgent
);

/// `PopupPositioner`s are responsible for setting the size and position of a
/// popup. They can also decide which animation should be played when the popup
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

    throw new Error(`Invalid position: ${position}`);
}

/// Will always be on top of everything else.
export class PopupManager {
    private _anchor: HTMLElement;
    private content: HTMLElement;
    private _userClosable: boolean;

    /// Inform the outside world when the popup was closed by the user, rather
    /// than programmatically.
    public onUserClose?: () => void;

    private _isOpen: boolean = false;

    /// Used to darken the screen if the popup is modal.
    private shadeElement: HTMLElement;

    /// A container for nested overlays. This ensures that nested overlays
    /// disappear if the popup is closed.
    private nestedOverlaysContainer: HTMLElement;

    private scrollerElement: HTMLElement;

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

    private currentAnimationPlayback: RioAnimationPlayback | null = null;

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

        this.nestedOverlaysContainer = document.createElement("div");
        this.nestedOverlaysContainer.classList.add(
            "rio-popup-manager-nested-overlays-container"
        );
        this.shadeElement.appendChild(this.nestedOverlaysContainer);

        this.scrollerElement = document.createElement("div");
        this.scrollerElement.classList.add("rio-popup-manager-scroller");
        this.nestedOverlaysContainer.appendChild(this.scrollerElement);
        this.scrollerElement.appendChild(content);

        // Set the initial CSS required for the animation to work
        Object.assign(this.content.style, positioner.getInitialCss());

        // Call the setters last, as they might expect the instance to be
        // initialized
        this.modal = modal;
        this.userClosable = userClosable;
    }

    public get anchor(): HTMLElement {
        return this._anchor;
    }

    public set anchor(anchor: HTMLElement) {
        this._anchor = anchor;

        // *Technically* we should update the `overlaysContainer` as well, but I
        // don't think it can actually be different than before. And we could
        // run into problems if the new anchor isn't attached to the DOM yet.

        if (this.isOpen) {
            this._positionContent();
        }
    }

    public get positioner(): PopupPositioner {
        return this._positioner;
    }

    public set positioner(positioner: PopupPositioner) {
        this.positioner.cleanup(this.content);

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
            this.content.style.removeProperty(prop);
        }

        let oldInitialCss = this.positioner.getInitialCss();
        let newInitialCss = positioner.getInitialCss();

        for (let key of Object.keys(oldInitialCss)) {
            this.content.style.removeProperty(camelToKebab(key));
        }

        Object.assign(this.content.style, newInitialCss);

        this._positioner = positioner;

        // If the popup is currently open, we just messed up its layout.
        // Reposition it.
        if (this.isOpen) {
            // Repositioning alone isn't enough. Because we never played the
            // open animation, the popup is almost certainly invisible right
            // now. We need to style it as if the open animation had played.
            let animation = this._positionContent();
            animation.applyFinalCss(this.content);
        }
    }

    private get overlaysContainer(): HTMLElement {
        if (this._overlaysContainer === null) {
            this._overlaysContainer = findOverlaysContainer(this._anchor);
        }

        return this._overlaysContainer;
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
        let animation = this._positioner.positionContent(
            this._anchor,
            this.content,
            this.overlaysContainer
        );

        // In Safari, popups that are too large for the screen are not
        // scrollable. Safari doesn't like it that pointer-events are disabled
        // for the scrolling element. (In other browsers scrolling is possible
        // as long as the cursor is above the popup content.) We can't *always*
        // enable pointer events for the scrolling element because this would
        // prevent users from clicking other stuff. So we'll enable pointer
        // events only when scrolling is needed.
        if (enableSafariScrollingWorkaround) {
            if (
                getAllocatedHeightInPx(this.content) >
                    getAllocatedHeightInPx(this.overlaysContainer) ||
                getAllocatedWidthInPx(this.content) >
                    getAllocatedWidthInPx(this.overlaysContainer)
            ) {
                this.scrollerElement.style.pointerEvents = "auto";
            } else {
                this.scrollerElement.style.pointerEvents = "none";
            }
        }

        return animation;
    }

    private _onPointerDown(event: MouseEvent): void {
        // If the popup isn't user-closable or not even open, there's nothing
        // to do
        if (!this.userClosable || !this.isOpen) {
            return;
        }

        // Depending on where the user clicked, the popup will either close or
        // stay open. It'll stay open if the click was in any of these places:
        // - The popup.
        // - The anchor. This allows the anchor to decide its own behavior.
        // - Another popup that's located inside our nested-overlays-container.
        let acceptableTargets = [
            ...this.nestedOverlaysContainer.children,
        ].filter(
            (elem) => !elem.classList.contains("rio-popup-manager-scroller")
        );
        acceptableTargets.push(this.anchor);
        acceptableTargets.push(this.content);

        let target = event.target as Element | null;
        while (target !== null) {
            if (acceptableTargets.includes(target)) {
                return;
            }
            target = target.parentElement;
        }

        // Close the popup
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

        // Fade in the shade
        this.shadeElement.style.backgroundColor = "transparent";
        commitCss(this.shadeElement);
        this.shadeElement.style.removeProperty("background-color");

        // Attach event handlers that don't mess with the popup animation. (i.e.
        // those that don't reposition/resize the content)
        let clickHandler = this._onPointerDown.bind(this);
        this.clickHandler = clickHandler; // Shuts up the type checker
        window.addEventListener("pointerdown", clickHandler, true);

        // Position the popup
        let animation = this._positionContent();

        // Cancel the close animation, if it's still playing
        if (this.currentAnimationPlayback !== null) {
            this.currentAnimationPlayback.cancel();
        }

        // Start playing the popup animation. This may temporarily override the
        // position/size of the popup.
        //
        // Once the animation is complete, we'll attach a bunch of event
        // listeners that reposition the popup in case the user scrolls or the
        // anchor changes size or whatever. These can mess with the animation,
        // which is why we don't attach them right away.
        this.currentAnimationPlayback = animation.animate(this.content);

        this.currentAnimationPlayback.addEventListener("finish", () => {
            this.currentAnimationPlayback = null;

            let repositionContent = this._positionContent.bind(this);
            let repositionContentIfPositionChanged =
                this._repositionContentIfPositionChanged.bind(this);

            // The 'scroll' event is triggered when *any* element scrolls. We
            // should only reposition the popup if scroll-y actually caused it
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

        // Fade out the shade
        this.shadeElement.style.backgroundColor = "transparent";

        // Cancel the open animation, if it's still playing
        if (this.currentAnimationPlayback !== null) {
            this.currentAnimationPlayback.cancel();
        }

        // Play the close animation and remove the popup when the animation
        // is complete.
        let animation = this._positioner.getCloseAnimation(
            this._anchor,
            this.content,
            this.overlaysContainer
        );
        this.currentAnimationPlayback = animation.animate(this.content);

        this.currentAnimationPlayback.addEventListener("finish", () => {
            this.currentAnimationPlayback = null;
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
///
/// Also, each PopupManager creates its own overlays container.
function findOverlaysContainer(anchor: HTMLElement): HTMLElement {
    let element: HTMLElement | null = anchor;

    while (element !== null) {
        if (element.classList.contains("rio-user-root-container-inner")) {
            return getRootComponent().userOverlaysContainer;
        }

        if (element.classList.contains("rio-connection-lost-popup-container")) {
            return getRootComponent().connectionLostPopupOverlaysContainer;
        }

        if (element.classList.contains("rio-dev-tools-container")) {
            return getRootComponent().devToolsOverlaysContainer;
        }

        // PopupManagers function as nested overlays containers
        if (
            element.classList.contains(
                "rio-popup-manager-nested-overlays-container"
            )
        ) {
            return element;
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
