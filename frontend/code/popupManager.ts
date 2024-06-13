/// Helper class for creating pop-up elements.
///
/// Many components need to only display an element on occasion, and have it
/// hover over the rest of the page. This is surprisingly difficult to do,
/// because adding elements right in the HTML tree can cause them to be cut off
/// by `overflow: hidden`, or other elements with a higher index. A simple
/// `z-index` doesn't fix this either.
///
/// This class instead functions by adding the content close to the HTML root,
/// and programmatically moves them to the right place. This way, the pop-up
///
/// While open, the content is assigned the CSS class `rio-popup-manager-open`.

import { pixelsPerRem } from './app';

/// will always be on top of everything else.
export class PopupManager {
    private anchor: HTMLElement;
    private content: HTMLElement;

    /// Where the pop-up should be positioned relative to the anchor.
    ///
    /// This is taken as a hint, but can be ignored if there isn't enough space
    /// to fit the pop-up at that location.
    public position: 'left' | 'top' | 'right' | 'bottom' | 'center';

    /// The alignment of the popup within the anchor. If the popup opens to the
    /// left or right, this is the vertical alignment, with `0` being the top
    /// and `1` being the bottom. If the popup opens to the top or bottom, this
    /// is the horizontal alignment, with `0` being the left and `1` being the
    /// right. Has no effect if the popup opens centered.
    public alignment: number;

    /// The gap between the anchor and the popup, in `rem`.
    public gap: number;

    constructor(
        anchor: HTMLElement,
        content: HTMLElement,
        position: 'left' | 'top' | 'right' | 'bottom' | 'center',
        alignment: number,
        gap: number
    ) {
        this.anchor = anchor;
        this.content = content;
        this.position = position;
        this.alignment = alignment;
        this.gap = gap;

        // Prepare the content
        //
        // Note that the content is always present, even if not visible. This is
        // so it can play CSS animations when it appears/disappears.
        this.content.classList.add('rio-popup-manager-content'); // `rio-popup` is taken by the `Popup` component
        document.body.appendChild(this.content);
    }

    destroy() {
        this.content.remove();
    }

    setOpen(open: boolean) {
        // Easy case: Hide the content
        if (!open) {
            this.content.classList.remove('rio-popup-manager-open');
            return;
        }

        // Show the content
        this.content.classList.add('rio-popup-manager-open');

        // The popup location is defined in developer-friendly terms. Convert
        // this to floats instead:
        //
        // - Anchor point X & Y (relative)
        // - Popup point X & Y (relative)
        // - Offset X & Y (absolute)
        //
        // The popup will appear, uch that the popup point is at the anchor
        // point. (But never off the screen.)
        let anchorRelativeX: number, anchorRelativeY: number;
        let contentRelativeX: number, contentRelativeY: number;
        let fixedOffsetXRem: number, fixedOffsetYRem: number;

        if (this.position === 'left') {
            anchorRelativeX = 0;
            anchorRelativeY = this.alignment;
            contentRelativeX = 1;
            contentRelativeY = this.alignment;
            fixedOffsetXRem = -this.gap;
            fixedOffsetYRem = 0;
        } else if (this.position === 'top') {
            anchorRelativeX = this.alignment;
            anchorRelativeY = 0;
            contentRelativeX = this.alignment;
            contentRelativeY = 1;
            fixedOffsetXRem = 0;
            fixedOffsetYRem = -this.gap;
        } else if (this.position === 'right') {
            anchorRelativeX = 1;
            anchorRelativeY = this.alignment;
            contentRelativeX = 0;
            contentRelativeY = this.alignment;
            fixedOffsetXRem = this.gap;
            fixedOffsetYRem = 0;
        } else if (this.position === 'bottom') {
            anchorRelativeX = this.alignment;
            anchorRelativeY = 1;
            contentRelativeX = this.alignment;
            contentRelativeY = 0;
            fixedOffsetXRem = 0;
            fixedOffsetYRem = this.gap;
        } else if (this.position === 'center') {
            anchorRelativeX = 0.5;
            anchorRelativeY = 0.5;
            contentRelativeX = 0.5;
            contentRelativeY = 0.5;
            fixedOffsetXRem = 0;
            fixedOffsetYRem = 0;
        } else {
            throw new Error(`Invalid Popup direction: ${this.position}`);
        }

        // Determine the size of the screen
        let screenWidth = window.innerWidth;
        let screenHeight = window.innerHeight;

        // Determine the size of the Popup
        let anchorRect = this.anchor.getBoundingClientRect();

        // Location of anchor
        let contentWidth = this.content.scrollWidth;
        let contentHeight = this.content.scrollHeight;

        // Where would the popup be positioned as requested by the user?
        let anchorPointX = anchorRect.left + anchorRect.width * anchorRelativeX;
        let anchorPointY = anchorRect.top + anchorRect.height * anchorRelativeY;

        let contentPointX = contentWidth * contentRelativeX;
        let contentPointY = contentHeight * contentRelativeY;

        let spawnPointX =
            anchorPointX - contentPointX + fixedOffsetXRem * pixelsPerRem;
        let spawnPointY =
            anchorPointY - contentPointY + fixedOffsetYRem * pixelsPerRem;

        // Establish limits, so the popup doesn't go off the screen. This is
        // relative to the popup's top left corner.
        let margin = 1 * pixelsPerRem;

        let minX = margin;
        let maxX = screenWidth - contentWidth - margin;

        let minY = margin;
        let maxY = screenHeight - contentHeight - margin;

        // Enforce limits
        spawnPointX = Math.min(Math.max(spawnPointX, minX), maxX);
        spawnPointY = Math.min(Math.max(spawnPointY, minY), maxY);

        // Set the position of the popup
        this.content.style.left = `${spawnPointX}px`;
        this.content.style.top = `${spawnPointY}px`;
    }
}
