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

import { pixelsPerRem } from './app';

/// Will always be on top of everything else.
export class PopupManager {
    private anchor: HTMLElement;
    private content: HTMLElement;

    /// Where the pop-up should be positioned relative to the anchor.
    ///
    /// This is taken as a hint, but can be ignored if there isn't enough space
    /// to fit the pop-up at that location.
    public position:
        | 'auto'
        | 'left'
        | 'top'
        | 'right'
        | 'bottom'
        | 'center'
        | 'fullscreen';

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
        position:
            | 'auto'
            | 'left'
            | 'top'
            | 'right'
            | 'bottom'
            | 'center'
            | 'fullscreen',
        alignment: number,
        gap: number
    ) {
        this.anchor = anchor;
        this.content = content;
        this.position = position;
        this.alignment = alignment;
        this.gap = gap;

        // Prepare the content
        this.content.classList.add('rio-popup-manager-content'); // `rio-popup` is taken by the `Popup` component

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
        return this.content.classList.contains('rio-popup-manager-open');
    }

    set isOpen(open: boolean) {
        // Easy case: Hide the content
        if (!open) {
            this.content.classList.remove('rio-popup-manager-open');
            return;
        }

        // Show the content
        this.content.classList.add('rio-popup-manager-open');

        // If the content is to be displayed fullscreen, handle that separately,
        // since it behaves so differently from the other positions.
        if (this.position === 'fullscreen') {
            this.content.style.left = '1rem';
            this.content.style.top = '1rem';
            this.content.style.width = `calc(100% - 2rem)`;
            this.content.style.height = `calc(100% - 2rem)`;
            return;
        }

        this.content.style.removeProperty('left');
        this.content.style.removeProperty('top');
        this.content.style.removeProperty('width');
        this.content.style.removeProperty('height');

        // If the popup position is set to `auto`, convert it to one of the
        // other values, based on the anchor element's position.
        let position = this.position;

        if (this.position === 'auto') {
            let anchorRect = this.anchor.getBoundingClientRect();
            let screenWidth = window.innerWidth;
            let screenHeight = window.innerHeight;

            let relX = (anchorRect.left + anchorRect.right) / 2 / screenWidth;
            let relY = (anchorRect.top + anchorRect.bottom) / 2 / screenHeight;

            if (relX < 0.2) {
                position = 'right';
            } else if (relX > 0.8) {
                position = 'left';
            } else if (relY < 0.2) {
                position = 'bottom';
            } else {
                position = 'top';
            }
        }

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

        if (position === 'left') {
            anchorRelativeX = 0;
            anchorRelativeY = this.alignment;
            contentRelativeX = 1;
            contentRelativeY = this.alignment;
            fixedOffsetXRem = -this.gap;
            fixedOffsetYRem = 0;
        } else if (position === 'top') {
            anchorRelativeX = this.alignment;
            anchorRelativeY = 0;
            contentRelativeX = this.alignment;
            contentRelativeY = 1;
            fixedOffsetXRem = 0;
            fixedOffsetYRem = -this.gap;
        } else if (position === 'right') {
            anchorRelativeX = 1;
            anchorRelativeY = this.alignment;
            contentRelativeX = 0;
            contentRelativeY = this.alignment;
            fixedOffsetXRem = this.gap;
            fixedOffsetYRem = 0;
        } else if (position === 'bottom') {
            anchorRelativeX = this.alignment;
            anchorRelativeY = 1;
            contentRelativeX = this.alignment;
            contentRelativeY = 0;
            fixedOffsetXRem = 0;
            fixedOffsetYRem = this.gap;
        } else if (position === 'center') {
            anchorRelativeX = 0.5;
            anchorRelativeY = 0.5;
            contentRelativeX = 0.5;
            contentRelativeY = 0.5;
            fixedOffsetXRem = 0;
            fixedOffsetYRem = 0;
        } else {
            throw new Error(`Invalid Popup direction: ${position}`);
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
