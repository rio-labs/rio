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
import { commitCss } from "./utils";

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
    // Get some information about achor & content
    let anchorRect = anchor.getBoundingClientRect();

    let contentHeight = content.scrollHeight;
    let windowWidth = window.innerWidth - 1; // innerWidth is rounded
    let windowHeight = window.innerHeight - 1; // innerHeight is rounded

    const DESKTOP_WINDOW_MARGIN = 0.5 * pixelsPerRem;
    const GAP_IF_ENTIRELY_ABOVE = 0.5 * pixelsPerRem;

    // CSS classes are used to communicate which of the different layouts is
    // used. Remove them all first.
    content.classList.remove(
        "rio-dropdown-popup-mobile-fullscreen",
        "rio-dropdown-popup-above",
        "rio-dropdown-popup-below",
        "rio-dropdown-popup-above-and-below"
    );

    commitCss(content);

    // On small screens, such as phones, go fullscreen
    //
    // TODO: Adjust these thresholds. Maybe have a global variable which
    // keeps track of whether we're on mobile?
    if (windowWidth < 60 * pixelsPerRem || windowHeight < 40 * pixelsPerRem) {
        content.style.left = "0";
        content.style.top = "0";
        content.style.right = "0";
        content.style.bottom = "0";

        content.classList.add("rio-dropdown-popup-mobile-fullscreen");
        return;
    }

    // Popup is larger than the window. Give it all the space that's available.
    if (contentHeight >= windowHeight - 2 * DESKTOP_WINDOW_MARGIN) {
        let heightCss = `calc(100vh - ${2 * DESKTOP_WINDOW_MARGIN}px)`;

        content.style.left = `${anchorRect.left}px`;
        content.style.top = `${DESKTOP_WINDOW_MARGIN}px`;
        content.style.width = `${anchorRect.width}px`;
        content.style.height = heightCss;
        content.style.maxHeight = heightCss;
        content.style.overflowY = "auto";

        content.classList.add("rio-dropdown-popup-above-and-below");
        return;
    }

    // Popup fits below the dropdown
    if (
        anchorRect.bottom + contentHeight + DESKTOP_WINDOW_MARGIN <=
        windowHeight
    ) {
        content.style.left = `${anchorRect.left}px`;
        content.style.top = `${anchorRect.bottom}px`;
        content.style.width = `${anchorRect.width}px`;
        content.style.height = `min-content`;
        content.style.maxHeight = `${contentHeight}px`;

        content.style.borderTopLeftRadius = "0";
        content.style.borderTopRightRadius = "0";

        content.classList.add("rio-dropdown-popup-below");
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

        content.classList.add("rio-dropdown-popup-above");
    }
    // Popup doesn't fit above or below the dropdown. Center it as much
    // as possible
    else {
        let top = anchorRect.top + anchorRect.height / 2 - contentHeight / 2;

        // It looks ugly if the dropdown touches the border of the window, so
        // enforce a small margin on the top and the bottom
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

        content.classList.add("rio-dropdown-popup-above-and-below");
    }
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
function positionOnSide({
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
    content.style.left = `${contentLeft}px`;
    content.style.top = `${contentTop}px`;
    // content.style.width = `${contentWidth}px`;
    // content.style.height = `${contentHeight}px`;
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
    private _userClosable: boolean;

    /// Inform the outside world when the popup was closed by the user, rather
    /// than programmatically.
    public onUserClose?: () => void;

    /// Used to darken the screen if the popup is modal.
    private shadeElement: HTMLElement;

    /// Where the pop-up should be positioned relative to the anchor.
    ///
    /// This is taken as a hint, but can be ignored if there isn't enough space
    /// to fit the pop-up at that location.
    public positioner: PopupPositioner;

    /// Listen for interactions with the outside world, so they can close the
    /// popup if user-closable.
    private clickHandler: ((event: MouseEvent) => void) | null = null;

    // Event handlers for repositioning the popup
    private scrollHandler: ((event: Event) => void) | null = null;
    private resizeObserver: ResizeObserver | null = null;
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
        this.anchor = anchor;
        this.content = content;
        this.positioner = positioner;
        this.onUserClose = onUserClose;

        // Prepare the HTML
        this.shadeElement = document.createElement("div");
        this.shadeElement.classList.add("rio-popup-manager-shade");
        this.shadeElement.appendChild(this.content);

        // Call the setters last, as they might expect the instance to be
        // initialized
        this.modal = modal;
        this.userClosable = userClosable;
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

    private _positionContent(): void {
        // Clear any previously assigned CSS attributes
        this.content.style.cssText = "";

        // Run the positioner
        this.positioner(this.anchor, this.content);
    }

    private _onPointerDown(event: MouseEvent): void {
        // If the popup isn't user-closable or not even open, there's nothing
        // to do
        if (!this.userClosable || !this.isOpen) {
            return;
        }

        // Check if the interaction was with the anchor or its children. This
        // allows the anchor to decide its own behavior.
        if (this.anchor.contains(event.target as Node)) {
            return;
        }

        // Check if the interaction was with the popup or its children
        if (this.content.contains(event.target as Node)) {
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

    private _pollAnchorPosition(): void {
        let anchorRect = this.anchor.getBoundingClientRect();

        // If the anchor has moved, reposition the content
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
        return this.shadeElement.classList.contains("rio-popup-manager-open");
    }

    set isOpen(open: boolean) {
        // Do nothing if the state hasn't changed. This can avoid some
        // unexpected CSS behavior when opening/closing a popup multiple times
        // in a row.
        //
        // For example, say the animation sets a property to `0` when the popup
        // is closed. Opening commits CSS and sets the value larger, thus
        // initiating an animation. If however opening happens twice in a row,
        // the larger value is already set **and committed again**, bypassing
        // the animation.
        if (this.isOpen === open) {
            return;
        }

        // Make sure the popup is in the DOM. We can't rely on it being here or
        // not, because the popup manager could've been rapidly reopened, before
        // the element was removed. Be defensive.
        if (this.shadeElement.parentElement === null) {
            let overlaysContainer = document.querySelector(
                ".rio-overlays-container"
            )!;
            overlaysContainer.appendChild(this.shadeElement);
            commitCss(this.shadeElement);
        }

        // Add or remove the CSS class. This can be used by users of the popup
        // manager to trigger animations.
        this.shadeElement.classList.toggle("rio-popup-manager-open", open);

        // Closing the popup can skip most of the code
        if (!open) {
            this.removeEventHandlers();

            // ... but needs to remove the element after the animation has
            // completed. This makes sure it can't be clicked after it's gone.
            //
            // Since the animation may take any amount of time, go somewhat over
            // the top with the wait time.
            setTimeout(() => this.delayedRemove(), 1000);

            return;
        }

        // Register event handlers, if needed
        if (this.userClosable) {
            let clickHandler = this._onPointerDown.bind(this);
            this.clickHandler = clickHandler; // Shuts up the type checker
            window.addEventListener("pointerdown", clickHandler, true);
        }

        let repositionContent = this._positionContent.bind(this);

        this.scrollHandler = repositionContent;
        window.addEventListener("scroll", repositionContent, true);

        this.resizeObserver = new ResizeObserver(repositionContent);
        this.resizeObserver.observe(this.anchor);

        this.anchorPositionPoller = window.setInterval(
            this._pollAnchorPosition.bind(this),
            100
        );

        // TODO: React to the content's size changing as well

        // Position the content
        this._positionContent();
    }

    /// Entirely removes the element from the DOM. This prevents it from being
    /// clicked after animated out and is intended to be called after some
    /// delay.
    delayedRemove(): void {
        // Make sure the manager hasn't been re-opened while waiting
        if (this.isOpen) {
            return;
        }

        // The door's over there. Don't forget your hat.
        this.shadeElement.remove();
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
