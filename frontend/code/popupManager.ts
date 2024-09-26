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

// Given the anchor and content, return CSS values to apply to the content
type PopupPositioner = (
    anchor: HTMLElement,
    content: HTMLElement
) => { [key: string]: string };

export function positionFullscreen(
    anchor: HTMLElement,
    content: HTMLElement
): { [key: string]: string } {
    let margin = pixelsPerRem;

    return {
        left: `${margin}px`,
        top: `${margin}px`,
        width: `${window.innerWidth - 2 * margin}px`,
        height: `${window.innerHeight - 2 * margin}px`,
    };
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
}): { [key: string]: string } {
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
    return {
        left: `${contentLeft}px`,
        top: `${contentTop}px`,
    };
}

export function makePositionLeft(
    gap: number,
    alignment: number
): (anchor: HTMLElement, content: HTMLElement) => { [key: string]: string } {
    function result(
        anchor: HTMLElement,
        content: HTMLElement
    ): { [key: string]: string } {
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
): (anchor: HTMLElement, content: HTMLElement) => { [key: string]: string } {
    function result(
        anchor: HTMLElement,
        content: HTMLElement
    ): { [key: string]: string } {
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
): (anchor: HTMLElement, content: HTMLElement) => { [key: string]: string } {
    function result(
        anchor: HTMLElement,
        content: HTMLElement
    ): { [key: string]: string } {
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
): (anchor: HTMLElement, content: HTMLElement) => { [key: string]: string } {
    function result(
        anchor: HTMLElement,
        content: HTMLElement
    ): { [key: string]: string } {
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
): { [key: string]: string } {
    return positionOnSide({
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
): (anchor: HTMLElement, content: HTMLElement) => { [key: string]: string } {
    function result(
        anchor: HTMLElement,
        content: HTMLElement
    ): { [key: string]: string } {
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
        | "fullscreen",
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
    }

    throw new Error(`Invalid position: ${position}`);
}

/// Will always be on top of everything else.
export class PopupManager {
    private anchor: HTMLElement;
    private content: HTMLElement;

    /// Where the pop-up should be positioned relative to the anchor.
    ///
    /// This is taken as a hint, but can be ignored if there isn't enough space
    /// to fit the pop-up at that location.
    public positioner: PopupPositioner;

    constructor(
        anchor: HTMLElement,
        content: HTMLElement,
        positioner: PopupPositioner
    ) {
        this.anchor = anchor;
        this.content = content;
        this.positioner = positioner;

        // Prepare the content
        this.content.classList.add("rio-popup-manager-content"); // `rio-popup` is taken by the `Popup` component

        // We can't remove the element from the DOM when the popup is closed
        // because we want to support custom animations and we don't know how
        // long the animations are. So we'll simply leave the element in the DOM
        // permanently.
        document.body.appendChild(this.content);
    }

    destroy(): void {
        this.content.remove();
    }

    get isOpen(): boolean {
        return this.content.classList.contains("rio-popup-manager-open");
    }

    set isOpen(open: boolean) {
        // Add or remove the CSS class. This can be used by users of the popup
        // manager to trigger animations.
        this.content.classList.toggle("rio-popup-manager-open", open);

        // If just hiding the content, we're done.
        if (!open) {
            return;
        }

        // Determine the size of the screen
        let screenWidth = window.innerWidth;
        let screenHeight = window.innerHeight;

        // Clear any previously assigned CSS attributes
        this.content.style.cssText = "";

        // Have the positioner place the popup
        let cssAttributes = this.positioner(this.anchor, this.content);
        Object.assign(this.content.style, cssAttributes);
    }
}
