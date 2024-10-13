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

import { pixelsPerRem } from "./app";

// Given the anchor and content, return where to position the content.
type PopupPositioner = (anchor: HTMLElement, content: HTMLElement) => void;

export function positionFullscreen(
    anchor: HTMLElement,
    content: HTMLElement
): void {
    content.style.left = "0";
    content.style.top = "0";
    content.style.width = "100%";
    content.style.height = "100%";
    content.style.borderRadius = "0";
}

export function positionDropdown(
    anchor: HTMLElement,
    content: HTMLElement
): void {
    // Position & Animate
    let anchorRect = anchor.getBoundingClientRect();
    let contentHeight = content.scrollHeight;
    let windowWidth = window.innerWidth - 1; // innerWidth is rounded
    let windowHeight = window.innerHeight - 1; // innerHeight is rounded

    const DESKTOP_WINDOW_MARGIN = 0.5 * pixelsPerRem;
    const MOBILE_WINDOW_MARGIN = 2 * pixelsPerRem;
    const GAP_IF_ENTIRELY_ABOVE = 0.5 * pixelsPerRem;

    // On small screens, such as phones, go fullscreen
    //
    // TODO: Adjust these thresholds. Maybe have a global variable which
    // keeps track of whether we're on mobile?
    if (windowWidth < 60 * pixelsPerRem || windowHeight < 40 * pixelsPerRem) {
        // Make sure mobile browsers don't display a keyboard
        //
        // TODO
        // this.inputBox.inputElement.readOnly = true;

        content.style.left = "0";
        content.style.top = "0";
        content.style.width = "100vw";
        content.style.height = "100vh";

        content.classList.add("rio-dropdown-popup-mobile-fullscreen");
        return;
    }

    content.classList.remove("rio-dropdown-popup-mobile-fullscreen");

    // TODO
    //
    // this.inputBox.inputElement.readOnly = false;

    // Popup is larger than the window. Give it all the space that's
    // available.
    if (contentHeight >= windowHeight - 2 * DESKTOP_WINDOW_MARGIN) {
        content.style.left = `${anchorRect.left}px`;
        content.style.top = `${DESKTOP_WINDOW_MARGIN}px`;
        content.style.width = `${anchorRect.width}px`;
        content.style.height = `calc(100vh - ${2 * DESKTOP_WINDOW_MARGIN}px)`;
        return;
    }

    // Popup fits below the dropdown
    if (
        anchorRect.bottom + contentHeight + DESKTOP_WINDOW_MARGIN <=
        windowHeight
    ) {
        content.style.left = `${anchorRect.left}px`;
        content.style.top = `${anchorRect.bottom}px`;
        content.style.width = `max(min-content, ${anchorRect.width}px)`;
        content.style.height = `min-content`;
        content.style.maxHeight = `${contentHeight}px`;
        return;
    }
    // Popup fits above the dropdown
    else if (
        anchorRect.top - contentHeight >=
        GAP_IF_ENTIRELY_ABOVE + DESKTOP_WINDOW_MARGIN
    ) {
        content.style.left = `${anchorRect.left}px`;
        content.style.top = `${
            anchorRect.top - contentHeight - GAP_IF_ENTIRELY_ABOVE
        }px`;
        content.style.width = `${anchorRect.width}px`;
        content.style.height = `${contentHeight}px`;
        content.style.maxHeight = `${contentHeight}px`;
    }
    // Popup doesn't fit above or below the dropdown. Center it as much
    // as possible
    else {
        let top = anchorRect.top + anchorRect.height / 2 - contentHeight / 2;
        if (top < DESKTOP_WINDOW_MARGIN) {
            top = DESKTOP_WINDOW_MARGIN;
        } else if (top + contentHeight + DESKTOP_WINDOW_MARGIN > windowHeight) {
            top = windowHeight - contentHeight - DESKTOP_WINDOW_MARGIN;
        }

        content.style.left = `${anchorRect.left}px`;
        content.style.top = `${top}px`;
        content.style.width = `${anchorRect.width}px`;
        content.style.height = `${contentHeight}px`;
        content.style.maxHeight = `${contentHeight}px`;
        content.style.overflowY = "auto";
        return;
    }

    // Unreachable
    console.error("Unreachable");
}

// The popup location is defined in developer-friendly this function takes
// a couple floats instead:
//
// - Anchor point X & Y (relative)
// - Content point X & Y (relative)
// - Offset X & Y (absolute)
//
// The popup will appear, uch that the popup point is placed exactly at the
// anchor point. (But never off the screen.)
export function positionOnSide({
    anchor,
    content,
    anchorRelativeX,
    anchorRelativeY,
    contentRelativeX,
    contentRelativeY,
    fixedOffsetXRem,
    fixedOffsetYRem,
}: {
    anchor: HTMLElement;
    content: HTMLElement;
    anchorRelativeX: number;
    anchorRelativeY: number;
    contentRelativeX: number;
    contentRelativeY: number;
    fixedOffsetXRem: number;
    fixedOffsetYRem: number;
}): void {
    // Where would we like the content to be?
    let anchorRect = anchor.getBoundingClientRect();
    let contentWidth = content.scrollWidth;
    let contentHeight = content.scrollHeight;

    let anchorPointX = anchorRect.left + anchorRect.width * anchorRelativeX;
    let anchorPointY = anchorRect.top + anchorRect.height * anchorRelativeY;

    let contentPointX = contentWidth * contentRelativeX;
    let contentPointY = contentHeight * contentRelativeY;

    let contentLeft =
        anchorPointX - contentPointX + fixedOffsetXRem * pixelsPerRem;
    let contentTop =
        anchorPointY - contentPointY + fixedOffsetYRem * pixelsPerRem;

    // Establish limits, so the popup doesn't go off the screen. This is
    // relative to the popup's top left corner.
    let screenWidth = window.innerWidth;
    let screenHeight = window.innerHeight;
    let margin = 1 * pixelsPerRem;

    let minX = margin;
    let maxX = screenWidth - contentWidth - margin;

    let minY = margin;
    let maxY = screenHeight - contentHeight - margin;

    // Enforce the limits
    contentLeft = Math.min(Math.max(contentLeft, minX), maxX);
    contentTop = Math.min(Math.max(contentTop, minY), maxY);

    // Position & size the popup
    content.style.left = `${contentLeft}px`;
    content.style.top = `${contentTop}px`;
    content.style.width = `${contentWidth}px`;
    content.style.height = `${contentHeight}px`;
}

export function makePositionLeft(
    gap: number,
    alignment: number
): (anchor: HTMLElement, content: HTMLElement) => void {
    function result(anchor: HTMLElement, content: HTMLElement): void {
        return positionOnSide({
            anchor: anchor,
            content: content,
            anchorRelativeX: 0,
            anchorRelativeY: alignment,
            contentRelativeX: 1,
            contentRelativeY: 1 - alignment,
            fixedOffsetXRem: -gap,
            fixedOffsetYRem: 0,
        });
    }

    return result;
}

export function makePositionTop(
    gap: number,
    alignment: number
): (anchor: HTMLElement, content: HTMLElement) => void {
    function result(anchor: HTMLElement, content: HTMLElement): void {
        return positionOnSide({
            anchor: anchor,
            content: content,
            anchorRelativeX: alignment,
            anchorRelativeY: 0,
            contentRelativeX: 1 - alignment,
            contentRelativeY: 1,
            fixedOffsetXRem: 0,
            fixedOffsetYRem: -gap,
        });
    }

    return result;
}

export function makePositionRight(
    gap: number,
    alignment: number
): (anchor: HTMLElement, content: HTMLElement) => void {
    function result(anchor: HTMLElement, content: HTMLElement): void {
        return positionOnSide({
            anchor: anchor,
            content: content,
            anchorRelativeX: 1,
            anchorRelativeY: alignment,
            contentRelativeX: 0,
            contentRelativeY: 1 - alignment,
            fixedOffsetXRem: gap,
            fixedOffsetYRem: 0,
        });
    }

    return result;
}

export function makePositionBottom(
    gap: number,
    alignment: number
): (anchor: HTMLElement, content: HTMLElement) => void {
    function result(anchor: HTMLElement, content: HTMLElement): void {
        return positionOnSide({
            anchor: anchor,
            content: content,
            anchorRelativeX: alignment,
            anchorRelativeY: 1,
            contentRelativeX: 1 - alignment,
            contentRelativeY: 0,
            fixedOffsetXRem: 0,
            fixedOffsetYRem: gap,
        });
    }

    return result;
}

export function positionCenter(
    anchor: HTMLElement,
    content: HTMLElement
): void {
    positionOnSide({
        anchor: anchor,
        content: content,
        anchorRelativeX: 0.5,
        anchorRelativeY: 0.5,
        contentRelativeX: 0.5,
        contentRelativeY: 0.5,
        fixedOffsetXRem: 0,
        fixedOffsetYRem: 0,
    });
}

export function makePositionerAuto(
    gap: number,
    alignment: number
): (anchor: HTMLElement, content: HTMLElement) => void {
    function result(anchor: HTMLElement, content: HTMLElement): void {
        let screenWidth = window.innerWidth;
        let screenHeight = window.innerHeight;

        let anchorRect = anchor.getBoundingClientRect();
        let relX = (anchorRect.left + anchor.scrollWidth) / 2 / screenWidth;
        let relY = (anchorRect.top + anchor.scrollHeight) / 2 / screenHeight;

        let positioner;

        if (relX < 0.2) {
            positioner = makePositionRight(gap, alignment);
        } else if (relX > 0.8) {
            positioner = makePositionLeft(gap, alignment);
        } else if (relY < 0.2) {
            positioner = makePositionBottom(gap, alignment);
        } else {
            positioner = makePositionTop(gap, alignment);
        }

        return positioner(anchor, content);
    }

    return result;
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
            return makePositionLeft(gap, alignment);
        case "top":
            return makePositionTop(gap, alignment);
        case "right":
            return makePositionRight(gap, alignment);
        case "bottom":
            return makePositionBottom(gap, alignment);
        case "center":
            return positionCenter;
        case "auto":
            return makePositionerAuto(gap, alignment);
        case "fullscreen":
            return positionFullscreen;
        case "dropdown":
            return positionDropdown;
    }

    throw new Error(`Invalid position: ${position}`);
}

/// Will always be on top of everything else.
export class PopupManager {
    private anchor: HTMLElement;
    private content: HTMLElement;
    private _userCloseable: boolean;

    /// Used to darken the screen if the popup is modal.
    private shadeElement: HTMLElement;

    /// Where the pop-up should be positioned relative to the anchor.
    ///
    /// This is taken as a hint, but can be ignored if there isn't enough space
    /// to fit the pop-up at that location.
    public positioner: PopupPositioner;

    /// Listen for interactions with the outside world, so they can close the
    /// popup if user-closeable.
    private clickHandler: ((event: MouseEvent) => void) | null = null;
    private scrollHandler: ((event: Event) => void) | null = null;

    constructor(
        anchor: HTMLElement,
        content: HTMLElement,
        positioner: PopupPositioner
    ) {
        this.anchor = anchor;
        this.content = content;
        this.positioner = positioner;

        // Prepare the HTML
        this.shadeElement = document.createElement("div");
        this.shadeElement.classList.add("rio-popup-manager-shade");

        this.shadeElement.appendChild(this.content);
        this.content.classList.add("rio-popup-manager-content"); // `rio-popup` is taken by the `Popup` component

        // We can't remove the element from the DOM when the popup is closed
        // because we want to support custom animations and we don't know how
        // long the animations are. So we'll simply leave the element in the DOM
        // permanently.
        document.body.appendChild(this.shadeElement);

        // Default values
        this.modal = false;
        this._userCloseable = true;
    }

    private removeEventHandlers(): void {
        if (this.clickHandler !== null) {
            window.removeEventListener("click", this.clickHandler, true);
        }

        if (this.scrollHandler !== null) {
            window.removeEventListener("scroll", this.scrollHandler, true);
        }
    }

    destroy(): void {
        this.removeEventHandlers();
        this.content.remove();
    }

    private _positionContent(): void {
        // Clear any previously assigned CSS attributes
        this.content.style.cssText = "";

        // Run the positioner
        this.positioner(this.anchor, this.content);
    }

    private _onClick(event: MouseEvent): void {
        // This handler is only attached if user-closeable
        // console.assert(this.userCloseable, "The popup is not user-closeable");

        // And if the popup is open
        // console.assert(this.isOpen, "The popup is not open");

        if (!this.userCloseable || !this.isOpen) {
            return;
        }

        // Check if the interaction was with the popup or its children
        if (this.content.contains(event.target as Node)) {
            return;
        }

        // Otherwise, close the popup
        this.isOpen = false;

        // Don't consider the event to be handled. Any clicks should still do
        // whatever they were going to do. The exception here are modal popups,
        // but the modal shade already takes care of that.
    }

    private _onScroll(event: Event): void {
        // Re-position the content
        this._positionContent();
    }

    get isOpen(): boolean {
        return this.shadeElement.classList.contains("rio-popup-manager-open");
    }

    set isOpen(open: boolean) {
        // Add or remove the CSS class. This can be used by users of the popup
        // manager to trigger animations.
        console.log(this.shadeElement.classList);
        this.shadeElement.classList.toggle("rio-popup-manager-open", open);
        console.log(this.shadeElement.classList);

        // Closing the popup can skip most of the code
        if (!open) {
            this.removeEventHandlers();
            return;
        }

        // Register event handlers, if needed
        if (this.userCloseable) {
            let clickHandler = this._onClick.bind(this);
            this.clickHandler = clickHandler; // Shuts up the type checker
            window.addEventListener("click", clickHandler, true);
        }

        {
            let scrollHandler = this._onScroll.bind(this);
            this.scrollHandler = scrollHandler; // Shuts up the type checker
            window.addEventListener("scroll", scrollHandler, true);
        }

        // Position the content
        this._positionContent();
    }

    set modal(modal: boolean) {
        this.shadeElement.classList.toggle("rio-popup-manager-modal", modal);
    }

    get userCloseable(): boolean {
        return this._userCloseable;
    }

    set userCloseable(userCloseable: boolean) {
        this._userCloseable = userCloseable;
    }
}
