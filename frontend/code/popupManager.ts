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
///
/// Note: I have experimented with using <dialog> elements, but the last opened
/// dialog is always on top, which is a deal breaker for us.

import { RioAnimation, RioAnimationPlayback } from "./animations";
import {
    componentsById,
    getComponentByElement,
    getRootComponent,
} from "./componentManagement";
import { DialogContainerComponent } from "./components/dialogContainer";
import { markEventAsHandled } from "./eventHandling";
import { PopupPositioner } from "./popupPositioners";
import {
    camelToKebab,
    commitCss,
    getAllocatedHeightInPx,
    getAllocatedWidthInPx,
    OnlyResizeObserver,
    reprElement,
} from "./utils";

import ally from "ally.js";

const enableSafariScrollingWorkaround = /^((?!chrome|android).)*safari/i.test(
    navigator.userAgent
);

/// Will always be on top of everything else.
export class PopupManager {
    private _anchor: HTMLElement;
    private content: HTMLElement;
    private _userClosable: boolean;
    public dialog: boolean;
    public moveKeyboardFocusInside: boolean;

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

    private focusTrap: any | null = null;

    /// Listen for interactions with the outside world, so they can close the
    /// popup if user-closable.
    private clickHandler: ((event: MouseEvent) => void) | null = null;
    private keydownHandler: ((event: KeyboardEvent) => void) | null = null;

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
        dialog,
        moveKeyboardFocusInside,
        onUserClose,
    }: {
        anchor: HTMLElement;
        content: HTMLElement;
        positioner: PopupPositioner;
        modal: boolean;
        userClosable: boolean;
        dialog?: boolean;
        moveKeyboardFocusInside?: boolean;
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
        this.dialog = dialog ?? false;
        this.moveKeyboardFocusInside = moveKeyboardFocusInside ?? true;
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
        if (this.keydownHandler !== null) {
            window.removeEventListener("keydown", this.keydownHandler);
        }

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

    private _onKeydown(event: KeyboardEvent): void {
        // If the popup isn't user-closable or not even open, there's nothing
        // to do
        if (!this.userClosable || !this.isOpen) {
            return;
        }

        // We only care about the "Escape" key
        if (event.key !== "Escape") {
            return;
        }

        markEventAsHandled(event);

        // Close the popup
        this.isOpen = false;

        // Tell the outside world
        if (this.onUserClose !== undefined) {
            this.onUserClose();
        }
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

        let keydownHandler = this._onKeydown.bind(this);
        this.keydownHandler = keydownHandler; // Shuts up the type checker
        window.addEventListener("keydown", keydownHandler);

        // Position the popup
        let animation = this._positionContent();

        // Cancel the close animation, if it's still playing
        if (this.currentAnimationPlayback !== null) {
            this.currentAnimationPlayback.cancel();
        }

        // Set dialog metadata
        if (this.dialog) {
            this.content.role = "dialog";
            this.content.ariaModal = this.modal ? "true" : "false";
        } else {
            this.content.removeAttribute("role");
            this.content.removeAttribute("aria-modal");
        }

        // Move the keyboard focus inside the popup, if desired
        if (this.moveKeyboardFocusInside) {
            ensureFocusIsInside(this.content);
        }

        // If modal, trap the keyboard focus inside
        if (this.modal) {
            this.focusTrap = ally.maintain.tabFocus({
                context: this.shadeElement,
            });
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

        // Disengage the focus trap, if any
        if (this.focusTrap !== null) {
            this.focusTrap.disengage();
            this.focusTrap = null;
        }

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

    get modal(): boolean {
        return this.shadeElement.classList.contains("rio-popup-manager-modal");
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

function ensureFocusIsInside(element: HTMLElement): void {
    // If the focus is already inside, do nothing
    let focusedElement = document.activeElement;
    if (focusedElement !== null && element.contains(focusedElement)) {
        return;
    }

    // Find something to focus
    let focusableElement = element.querySelector("[autofocus]");

    if (focusableElement instanceof HTMLElement) {
        focusableElement.focus();
    }
}
