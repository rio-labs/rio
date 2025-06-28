import { pixelsPerRem } from "../app";
import { commitCss } from "../utils";
import { ComponentBase, ComponentState, DeltaState } from "./componentBase";
import { ColorSet, ComponentId } from "../dataModels";
import { applySwitcheroo } from "../designApplication";
import { markEventAsHandled } from "../eventHandling";
import { ComponentStatesUpdateContext } from "../componentManagement";

export type DrawerState = ComponentState & {
    _type_: "Drawer-builtin";
    anchor: ComponentId;
    content: ComponentId;
    side: "left" | "right" | "top" | "bottom";
    is_modal: boolean;
    is_open: boolean;
    is_user_openable: boolean;
    color: ColorSet;
};

export class DrawerComponent extends ComponentBase<DrawerState> {
    private anchorContainer: HTMLElement;
    private contentOuterContainer: HTMLElement;
    private contentInnerContainer: HTMLElement;
    private shadeElement: HTMLElement;

    private dragStartedAt: number = 0;
    private openFractionAtDragStart: number = 0;
    private openFraction: number = 1;

    private isFirstUpdate: boolean = true;

    createElement(context: ComponentStatesUpdateContext): HTMLElement {
        // Create the HTML
        let element = document.createElement("div");
        element.classList.add("rio-drawer");

        element.innerHTML = `
            <div class="rio-drawer-anchor"></div>
            <div class="rio-drawer-shade"></div>
            <div class="rio-drawer-content-outer">
                <div class="rio-drawer-content-inner"></div>
                <div class="rio-drawer-knob"></div>
            </div>
        `;

        this.anchorContainer = element.querySelector(
            ".rio-drawer-anchor"
        ) as HTMLElement;

        this.shadeElement = element.querySelector(
            ".rio-drawer-shade"
        ) as HTMLElement;

        this.contentOuterContainer = element.querySelector(
            ".rio-drawer-content-outer"
        ) as HTMLElement;

        this.contentInnerContainer = element.querySelector(
            ".rio-drawer-content-inner"
        ) as HTMLElement;

        // Connect to events
        this.addDragHandler({
            element: element,
            onStart: this.beginDrag.bind(this),
            onMove: this.dragMove.bind(this),
            onEnd: this.endDrag.bind(this),
            // Let things like Buttons and TextInputs consume pointer events
            capturing: false,
        });

        return element;
    }

    updateElement(
        deltaState: DeltaState<DrawerState>,
        context: ComponentStatesUpdateContext
    ): void {
        super.updateElement(deltaState, context);

        // Update the children
        this.replaceOnlyChild(context, deltaState.anchor, this.anchorContainer);
        this.replaceOnlyChild(
            context,
            deltaState.content,
            this.contentInnerContainer
        );

        // Assign the correct class for the side
        if (deltaState.side !== undefined) {
            this.element.classList.remove(
                "rio-drawer-left",
                "rio-drawer-right",
                "rio-drawer-top",
                "rio-drawer-bottom"
            );
            this.element.classList.add(`rio-drawer-${deltaState.side}`);
        }

        // Colorize
        if (deltaState.color !== undefined) {
            applySwitcheroo(this.contentOuterContainer, deltaState.color);
        }

        // Open?
        //
        // Assign the changes directly to the state. This is necessary, because
        // the subsequent call to `_updateCss` uses the state to derive what the
        // CSS should be. Having values stored in the delta state rather than
        // actual state would ignore them.
        if (deltaState.is_open === true) {
            this.openFraction = 1;
            this.state.is_open = true;
        } else if (deltaState.is_open === false) {
            this.openFraction = 0;
            this.state.is_open = false;
        }

        // Make sure the CSS matches the state
        if (this.isFirstUpdate) {
            this._disableTransition();
        } else {
            this._enableTransition();
        }
        this._updateCss();

        // Not the first update anymore
        this.isFirstUpdate = false;
    }

    _updateCss() {
        // Account for the side of the drawer
        let axis =
            this.state.side === "left" || this.state.side === "right"
                ? "X"
                : "Y";

        let negate =
            this.state.side === "right" || this.state.side === "bottom"
                ? "+"
                : "-";

        // Move the drawer far enough to hide the shadow
        let closedFraction = 1 - this.openFraction;
        this.contentOuterContainer.style.transform = `translate${axis}(calc(0rem ${negate} ${
            closedFraction * 100
        }% ${negate} ${closedFraction}rem))`;

        // Throw some shade, if modal
        if (this.state.is_modal) {
            let shadeFraction = this.openFraction * 0.5;
            this.shadeElement.style.backgroundColor = `rgba(0, 0, 0, ${shadeFraction})`;
            this.shadeElement.style.pointerEvents = this.state.is_open
                ? "auto"
                : "none";
        } else {
            this.shadeElement.style.backgroundColor = "rgba(0, 0, 0, 0)";
            this.shadeElement.style.pointerEvents = "none";
        }

        // Update the class
        let element = this.element;
        if (this.openFraction > 0.5) {
            element.classList.add("rio-drawer-open");
        } else {
            element.classList.remove("rio-drawer-open");
        }
    }

    _enableTransition(): void {
        // Remove the class and flush the style changes
        let element = this.element;
        element.classList.remove("rio-drawer-no-transition");
        commitCss(element);
    }

    _disableTransition(): void {
        // Add the class and flush the style changes
        let element = this.element;
        element.classList.add("rio-drawer-no-transition");
        commitCss(element);
    }

    openDrawer(): void {
        this.openFraction = 1;
        this._enableTransition();
        this._updateCss();

        // Notify the backend
        if (!this.state.is_open) {
            this.setStateAndNotifyBackend({
                is_open: true,
            });
        }
    }

    closeDrawer(): void {
        this.openFraction = 0;
        this._enableTransition();
        this._updateCss();

        // Notify the backend
        if (this.state.is_open) {
            this.setStateAndNotifyBackend({
                is_open: false,
            });
        }
    }

    beginDrag(event: PointerEvent): boolean {
        // If the drawer isn't user-openable, ignore the click
        if (!this.state.is_user_openable) {
            return false;
        }

        // Find the location of the drawer
        //
        // If the click was outside of the anchor element, ignore it
        let drawerRect = this.element.getBoundingClientRect();

        // Account for the side of the drawer
        const handleSizeIfClosed = 2.0 * pixelsPerRem;
        let relevantClickCoordinate, thresholdMin, thresholdMax;

        if (this.state.side === "left") {
            relevantClickCoordinate = event.clientX;
            thresholdMin = drawerRect.left;
            thresholdMax = Math.max(
                drawerRect.left + handleSizeIfClosed,
                drawerRect.left +
                    this.contentOuterContainer.scrollWidth * this.openFraction
            );
        } else if (this.state.side === "right") {
            relevantClickCoordinate = event.clientX;
            thresholdMin = Math.min(
                drawerRect.right - handleSizeIfClosed,
                drawerRect.right -
                    this.contentOuterContainer.scrollWidth * this.openFraction
            );
            thresholdMax = drawerRect.right;
        } else if (this.state.side === "top") {
            relevantClickCoordinate = event.clientY;
            thresholdMin = drawerRect.top;
            thresholdMax = Math.max(
                drawerRect.top + handleSizeIfClosed,
                drawerRect.top +
                    this.contentOuterContainer.scrollHeight * this.openFraction
            );
        } else if (this.state.side === "bottom") {
            relevantClickCoordinate = event.clientY;
            thresholdMin = Math.min(
                drawerRect.bottom - handleSizeIfClosed,
                drawerRect.bottom -
                    this.contentOuterContainer.scrollHeight * this.openFraction
            );
            thresholdMax = drawerRect.bottom;
        }

        // The drawer was clicked. It is being dragged now
        if (
            thresholdMin < relevantClickCoordinate &&
            relevantClickCoordinate < thresholdMax
        ) {
            this.openFractionAtDragStart = this.openFraction;
            this.dragStartedAt = relevantClickCoordinate;
            return true;
        }

        // The anchor was clicked. Collapse the drawer if modal
        else if (this.state.is_modal) {
            this.closeDrawer();
            markEventAsHandled(event);
            return false;
        }

        return false;
    }

    dragMove(event: PointerEvent) {
        // Account for the side of the drawer
        let relevantCoordinate, drawerSize;

        if (this.state.side === "left" || this.state.side === "right") {
            relevantCoordinate = event.clientX;
            drawerSize = this.contentOuterContainer.scrollWidth;
        } else {
            relevantCoordinate = event.clientY;
            drawerSize = this.contentOuterContainer.scrollHeight;
        }

        let negate =
            this.state.side === "right" || this.state.side === "bottom"
                ? -1
                : 1;

        // Calculate the fraction the drawer is open
        this.openFraction =
            this.openFractionAtDragStart +
            ((relevantCoordinate - this.dragStartedAt) / drawerSize) * negate;

        this.openFraction = Math.max(0, Math.min(1, this.openFraction));

        // Update the drawer
        this._disableTransition();
        this._updateCss();
    }

    endDrag(event: PointerEvent): void {
        // Snap to fully open or fully closed
        let threshold = this.openFractionAtDragStart > 0.5 ? 0.75 : 0.25;

        if (this.openFraction > threshold) {
            this.openDrawer();
        } else {
            this.closeDrawer();
        }
    }
}
