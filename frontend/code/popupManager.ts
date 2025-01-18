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
    getAllocatedHeightInPx,
    getAllocatedWidthInPx,
    reprElement,
} from "./utils";

/// `PopupPositioner`s are responsible for setting the size and position of a
/// popup. They can also decide which animation should be played when the popup
/// is opened or closed.
///
/// TODO: This class should probably be replaced by a function that positions
/// the element and returns the `[initialCss, openAnimation, closeAnimation]`. I
/// can't be bothered to rewrite all the code right now though.
export abstract class PopupPositioner {
    /// If a popup is quickly opened and closed (or the other way round), the
    /// animation may be interrupted partway. If that happens, we don't want the
    /// popup to "snap" to its final state and then start playing the new
    /// animation, we want to seamlessly switch from one animation to the other.
    /// That's why `PopupManagerAnimation`s should not hard-code a specific
    /// starting keyframe, but rather start from the element's current state.
    /// The `initialState` is stored separately and is only applied to the
    /// element once, when the PopupManager is created.
    abstract getInitialCss(content: HTMLElement): Keyframe;

    /// Positions the `content` in the `overlaysContainer` by updating its CSS
    /// *AND* returns the animation for opening the popup
    abstract positionContent(
        anchor: HTMLElement,
        content: HTMLElement,
        overlaysContainer: HTMLElement
    ): RioAnimation;

    abstract getCloseAnimation(content: HTMLElement): RioAnimation;
}

/// Most `PopupPositioner`s always use the same open/close animation, so this
/// class exists to make that more convenient.
abstract class PopupPositionerWithStaticAnimation extends PopupPositioner {
    private initialCss: Keyframe;
    private openAnimation: RioAnimation;
    private closeAnimation: RioAnimation;

    constructor(
        initialCss: Keyframe,
        finalCss: Keyframe,
        options: KeyframeAnimationOptions
    ) {
        super();

        this.initialCss = initialCss;
        this.openAnimation = new RioKeyframeAnimation([finalCss], options);
        this.closeAnimation = new RioKeyframeAnimation([initialCss], options);
    }

    getInitialCss(content: HTMLElement): Keyframe {
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

    getCloseAnimation(content: HTMLElement): RioAnimation {
        return this.closeAnimation;
    }
}

export class FullscreenPositioner extends PopupPositionerWithStaticAnimation {
    constructor() {
        super(
            { transform: "translateY(-1rem)", opacity: 0 },
            { transform: "translateY(0)", opacity: 1 },
            {
                duration: 200, // 0.2s
                easing: "ease-in-out",
            }
        );
    }

    _positionContent(
        anchor: HTMLElement,
        content: HTMLElement,
        overlaysContainer: HTMLElement
    ): void {
        content.style.left = "0";
        content.style.top = "0";
        content.style.width = "100%";
        content.style.height = "100%";
        content.style.borderRadius = "0";
    }
}

export class DropdownPositioner extends PopupPositioner {
    positionContent(
        anchor: HTMLElement,
        content: HTMLElement,
        overlaysContainer: HTMLElement
    ): RioAnimation {
        // Get some information about achor & content
        let anchorRect = getAnchorRectInContainer(anchor, overlaysContainer);

        // For some reason, the `max-height: 0` causes the `scrollHeight` to be
        // wrong. Temporarily remove it.
        let maxHeight = content.style.maxHeight;
        content.style.maxHeight = "unset";
        let contentHeight = content.scrollHeight;
        content.style.maxHeight = maxHeight;

        let availableWidth = getAllocatedWidthInPx(overlaysContainer);
        let availableHeight = getAllocatedHeightInPx(overlaysContainer);

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

        // On small screens, such as phones, go fullscreen
        //
        // TODO: Adjust these thresholds. Maybe have a global variable which
        // keeps track of whether we're on mobile?
        if (
            availableWidth < 60 * pixelsPerRem ||
            availableHeight < 40 * pixelsPerRem
        ) {
            content.style.left = "0";
            content.style.top = "0";
            content.style.width = "100%";
            content.style.height = "100%";
            content.style.maxHeight = "unset";
            content.style.overflowY = "auto";

            content.classList.add("rio-dropdown-popup-mobile-fullscreen");
            return new RioKeyframeAnimation([], {});
        }

        // Popup is larger than the window. Give it all the space that's available.
        if (contentHeight >= availableHeight - 2 * DESKTOP_WINDOW_MARGIN) {
            let heightCss = `calc(100vh - ${2 * DESKTOP_WINDOW_MARGIN}px)`;

            content.style.left = `${anchorRect.left}px`;
            content.style.top = `${DESKTOP_WINDOW_MARGIN}px`;
            content.style.width = `${anchorRect.width}px`;
            content.style.height = heightCss;
            content.style.maxHeight = heightCss;
            content.style.overflowY = "auto";

            content.classList.add("rio-dropdown-popup-above-and-below");
            return this.makeOpenAnimation(contentHeight);
        }

        // Popup fits below the dropdown
        if (
            anchorRect.bottom + contentHeight + DESKTOP_WINDOW_MARGIN <=
            availableHeight
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
            let top =
                anchorRect.top + anchorRect.height / 2 - contentHeight / 2;

            // It looks ugly if the dropdown touches the border of the window, so
            // enforce a small margin on the top and the bottom
            if (top < DESKTOP_WINDOW_MARGIN) {
                top = DESKTOP_WINDOW_MARGIN;
            } else if (
                top + contentHeight + DESKTOP_WINDOW_MARGIN >
                availableHeight
            ) {
                top = availableHeight - contentHeight - DESKTOP_WINDOW_MARGIN;
            }

            content.style.left = `${anchorRect.left}px`;
            content.style.top = `${top}px`;
            content.style.width = `${anchorRect.width}px`;
            content.style.height = `${contentHeight}px`;
            content.style.maxHeight = `${contentHeight}px`;

            content.classList.add("rio-dropdown-popup-above-and-below");
        }

        return this.makeOpenAnimation(contentHeight);
    }

    getInitialCss(content: HTMLElement): Keyframe {
        return { maxHeight: "0", overflow: "hidden" };
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

    getCloseAnimation(content: HTMLElement): RioAnimation {
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

    private openAnimation: RioAnimation;
    private closeAnimation: RioAnimation;

    // The popup location is defined in developer-friendly this function takes
    // a couple floats instead:
    //
    // - Anchor point X & Y (relative)
    // - Content point X & Y (relative)
    // - Offset X & Y (absolute)
    //
    // The popup will appear, such that the popup point is placed exactly at the
    // anchor point. (But never off the screen.)
    protected constructor({
        gap,
        alignment,
        anchorRelativeX,
        anchorRelativeY,
        contentRelativeX,
        contentRelativeY,
        fixedOffsetXRem,
        fixedOffsetYRem,
    }: {
        gap: number;
        alignment: number;
        anchorRelativeX: number;
        anchorRelativeY: number;
        contentRelativeX: number;
        contentRelativeY: number;
        fixedOffsetXRem: number;
        fixedOffsetYRem: number;
    }) {
        super();

        this.openAnimation = new RioAnimationGroup([
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
                        opacity: 1,
                    },
                ],
                {
                    duration: 100,
                    easing: "cubic-bezier(0.5, 0.5, 0.2, 1.14)",
                }
            ),
        ]);
        this.closeAnimation = new RioAnimationGroup([
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
                        opacity: 0,
                    },
                ],
                {
                    duration: 100,
                    easing: "cubic-bezier(0.5, 0.5, 0.2, 1.14)",
                }
            ),
        ]);

        this.gap = gap;
        this.alignment = alignment;
        this.anchorRelativeX = anchorRelativeX;
        this.anchorRelativeY = anchorRelativeY;
        this.contentRelativeX = contentRelativeX;
        this.contentRelativeY = contentRelativeY;
        this.fixedOffsetXRem = fixedOffsetXRem;
        this.fixedOffsetYRem = fixedOffsetYRem;
    }

    getInitialCss(content: HTMLElement): Keyframe {
        return { transform: "scale(0)", opacity: 0 };
    }

    positionContent(
        anchor: HTMLElement,
        content: HTMLElement,
        overlaysContainer: HTMLElement
    ): RioAnimation {
        // Where would we like the content to be?
        let anchorRect = getAnchorRectInContainer(anchor, overlaysContainer);
        let contentWidth = content.scrollWidth;
        let contentHeight = content.scrollHeight;

        let anchorPointX =
            anchorRect.left + anchorRect.width * this.anchorRelativeX;
        let anchorPointY =
            anchorRect.top + anchorRect.height * this.anchorRelativeY;

        let contentPointX = contentWidth * this.contentRelativeX;
        let contentPointY = contentHeight * this.contentRelativeY;

        let contentLeft =
            anchorPointX - contentPointX + this.fixedOffsetXRem * pixelsPerRem;
        let contentTop =
            anchorPointY - contentPointY + this.fixedOffsetYRem * pixelsPerRem;

        // Establish limits, so the popup doesn't go off the screen. This is
        // relative to the popup's top left corner.
        let availableWidth = getAllocatedWidthInPx(overlaysContainer);
        let availableHeight = getAllocatedHeightInPx(overlaysContainer);
        let margin = 1 * pixelsPerRem;

        let minX = margin;
        let maxX = availableWidth - contentWidth - margin;

        let minY = margin;
        let maxY = availableHeight - contentHeight - margin;

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

        return this.openAnimation;
    }

    getCloseAnimation(content: HTMLElement): RioAnimation {
        return this.closeAnimation;
    }
}

export class LeftPositioner extends SidePositioner {
    constructor(gap: number, alignment: number) {
        super({
            gap: gap,
            alignment: alignment,
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
            gap: gap,
            alignment: alignment,
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
            gap: gap,
            alignment: alignment,
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
            gap: gap,
            alignment: alignment,
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
    constructor(gap: number, alignment: number) {
        super({
            gap: gap,
            alignment: alignment,
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

    getInitialCss(content: HTMLElement): Keyframe {
        return new TopPositioner(0, 0).getInitialCss(content);
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

    getCloseAnimation(content: HTMLElement): RioAnimation {
        return new TopPositioner(0, 0).getCloseAnimation(content);
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
            return new CenterPositioner(gap, alignment);
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
    private anchor: HTMLElement;
    private content: HTMLElement;
    private _userClosable: boolean;

    /// Inform the outside world when the popup was closed by the user, rather
    /// than programmatically.
    public onUserClose?: () => void;

    private _isOpen: boolean = false;

    /// Used to darken the screen if the popup is modal.
    private shadeElement: HTMLElement;

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
        this._positioner = positioner;
        this.onUserClose = onUserClose;

        // Prepare the HTML
        this.shadeElement = document.createElement("div");
        this.shadeElement.classList.add("rio-popup-manager-shade");
        this.shadeElement.appendChild(this.content);

        Object.assign(content.style, positioner.getInitialCss(content));

        // Call the setters last, as they might expect the instance to be
        // initialized
        this.modal = modal;
        this.userClosable = userClosable;
    }

    public get positioner(): PopupPositioner {
        return this._positioner;
    }

    public set positioner(positioner: PopupPositioner) {
        // Clear the CSS that the current positioner needed, but the new one
        // doesn't
        let oldInitialCss = this.positioner.getInitialCss(this.content);
        let newInitialCss = positioner.getInitialCss(this.content);

        for (let key of Object.keys(oldInitialCss)) {
            if (!(key in newInitialCss)) {
                this.content.style.removeProperty(key);
            }
        }

        // Apply the CSS that the new positioner needs and the old one didn't
        // already set
        for (let [key, value] of Object.entries(newInitialCss)) {
            if (!(key in oldInitialCss)) {
                this.content.style.setProperty(key, `${value}`);
            }
        }

        this._positioner = positioner;

        // If the popup is currently open, we just messed up its layout.
        // Reposition it.
        if (this.isOpen) {
            this._positionContent();
        }
    }

    private get overlaysContainer(): HTMLElement {
        if (this._overlaysContainer === null) {
            this._overlaysContainer = findOverlaysContainer(this.anchor);
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
        return this._positioner.positionContent(
            this.anchor,
            this.content,
            this.overlaysContainer
        );
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
        let playback = animation.animate(this.content);

        playback.addEventListener("finish", () => {
            let repositionContent = this._positionContent.bind(this);

            this.scrollHandler = repositionContent;
            window.addEventListener("scroll", repositionContent, true);

            this.resizeObserver = new ResizeObserver(repositionContent);
            this.resizeObserver.observe(this.anchor);
            this.resizeObserver.observe(this.content);

            this.anchorPositionPoller = window.setInterval(
                this._pollAnchorPosition.bind(this),
                100
            );
        });
    }

    private _closePopup(): void {
        this.removeEventHandlers();

        // Play the close animation and remove the popup when the animation
        // is complete.
        let animation = this._positioner.getCloseAnimation(this.content);
        let playback = animation.animate(this.content);

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
