import { ComponentBase, ComponentState, DeltaState } from "./componentBase";
import { ColorSet } from "../dataModels";
import { applyIcon, applySwitcheroo } from "../designApplication";
import { MappingTween } from "../tweens/mappingTweens";
import { BaseTween } from "../tweens/baseTween";
import { KineticTween } from "../tweens/kineticTween";
import { pixelsPerRem } from "../app";
import {
    firstDefined,
    getAllocatedHeightInPx,
    getAllocatedWidthInPx,
} from "../utils";
import { ComponentStatesUpdateContext } from "../componentManagement";
import { PressableElement } from "../elements/pressableElement";

type SwitcherBarItem = {
    name: string;
    icon: string | null;
};

export type SwitcherBarState = ComponentState & {
    _type_: "SwitcherBar-builtin";
    items: SwitcherBarItem[];
    color: ColorSet;
    orientation: "horizontal" | "vertical";
    spacing: number;
    allow_none: boolean;
    selectedName: string | null;
};

export class SwitcherBarComponent extends ComponentBase<SwitcherBarState> {
    private innerElement: HTMLElement; // Used for alignment
    private markerElement: HTMLElement; // Highlights the selected item
    private backgroundOptionsElement: HTMLElement; // Displays all options
    private markerOptionsElement: HTMLElement; // Options, but different color

    // Animation state
    private animationIsRunning: boolean = false;

    private fadeTween: BaseTween;
    private moveTween: BaseTween;

    private markerAtAnimationStart: [number, number, number, number] = [
        0, 0, 0, 0,
    ];

    private markerAtAnimationEnd: [number, number, number, number] = [
        0, 0, 0, 0,
    ];

    private markerCurrent: [number, number, number, number] = [0, 0, 0, 0];

    // Allows to determine whether this is the first time the element is being
    // updated.
    private isInitialized: boolean = false;

    // Used to update the marker should the element be resized
    private resizeObserver: ResizeObserver;

    createElement(context: ComponentStatesUpdateContext): HTMLElement {
        // Create the elements
        let outerElement = document.createElement("div");
        outerElement.classList.add("rio-switcher-bar");

        // Centers the bar
        this.innerElement = document.createElement("div");
        outerElement.appendChild(this.innerElement);

        // Highlights the selected item
        this.markerElement = document.createElement("div");
        this.markerElement.classList.add("rio-switcher-bar-marker");

        // Prepare animations
        this.fadeTween = new MappingTween({
            mapping: (value: number) => value,
            duration: 0.18,
        });

        this.moveTween = new KineticTween({
            acceleration: 350 * pixelsPerRem,
        });

        // The marker needs updating when the element is resized
        this.resizeObserver = new ResizeObserver(this.onResize.bind(this));
        this.resizeObserver.observe(this.innerElement);

        return outerElement;
    }

    onDestruction(): void {
        super.onDestruction();
        this.resizeObserver.disconnect();
    }

    onResize(): void {
        // Update the marker position
        if (this.state.selectedName !== null) {
            this.markerAtAnimationEnd = this.getMarkerTarget()!;
            this.updateCssToMatchState();
        }

        // Pass on all of the allocated size to the marker options
        this.markerOptionsElement.style.width = `${getAllocatedWidthInPx(
            this.backgroundOptionsElement
        )}px`;
        this.markerOptionsElement.style.height = `${getAllocatedHeightInPx(
            this.backgroundOptionsElement
        )}px`;
    }

    /// Update the HTML & CSS to match the current state
    updateCssToMatchState(): void {
        // Position the marker
        let t = this.moveTween.progress;

        for (let i = 0; i < 4; i++) {
            let start = this.markerAtAnimationStart[i];
            let delta = this.markerAtAnimationEnd[i] - start;
            this.markerCurrent[i] = start + delta * t;
        }

        // Account for the fade animation
        let fade = this.fadeTween.current;
        let markerCurWidth = this.markerCurrent[2] * fade;
        let markerCurHeight = this.markerCurrent[3] * fade;
        let markerCurLeft =
            this.markerCurrent[0] +
            (this.markerCurrent[2] - markerCurWidth) / 2;
        let markerCurTop =
            this.markerCurrent[1] +
            (this.markerCurrent[3] - markerCurHeight) / 2;

        // Move the marker
        this.markerElement.style.left = `${markerCurLeft}px`;
        this.markerElement.style.top = `${markerCurTop}px`;
        this.markerElement.style.width = `${markerCurWidth}px`;
        this.markerElement.style.height = `${markerCurHeight}px`;

        // The inner options are positioned relative to the marker. Move them in
        // the opposite direction so they stay put.
        this.markerOptionsElement.style.left = `-${markerCurLeft}px`;
        this.markerOptionsElement.style.top = `-${markerCurTop}px`;
    }

    animationWorker() {
        // Update the tweens
        let keepGoing = false;

        if (this.fadeTween.isRunning) {
            this.fadeTween.update();
            keepGoing = true;
        }

        if (this.moveTween.isRunning) {
            this.moveTween.update();
            keepGoing = true;
        }

        // Update the CSS
        this.updateCssToMatchState();

        // Keep going?
        if (keepGoing) {
            requestAnimationFrame(this.animationWorker.bind(this));
        } else {
            this.animationIsRunning = false;
        }
    }

    ensureAnimationIsRunning(): void {
        if (this.animationIsRunning) {
            return;
        }

        this.animationIsRunning = true;
        requestAnimationFrame(this.animationWorker.bind(this));
    }

    /// Start moving the marker to match the current state, taking care of
    /// animations and everything
    animateToCurrentTarget(): void {
        // Move the marker
        if (this.state.selectedName !== null) {
            this.markerAtAnimationStart = [...this.markerCurrent];
            this.markerAtAnimationEnd = this.getMarkerTarget()!;

            let animatedPosition =
                this.state.orientation == "horizontal"
                    ? this.markerAtAnimationEnd[0]
                    : this.markerAtAnimationEnd[1];

            // If the marker is currently completely invisible, teleport.
            if (this.fadeTween.current === 0) {
                this.moveTween.teleportTo(animatedPosition);
            } else {
                this.moveTween.transitionTo(animatedPosition);
            }
        }

        // Fade the marker in/out
        if (this.state.selectedName === null) {
            this.fadeTween.transitionTo(0);
        } else {
            this.fadeTween.transitionTo(1);
        }

        // Make sure there's somebody tending to the tweens
        this.ensureAnimationIsRunning();
    }

    /// If an item is selected, returns the position and size the marker should
    /// be in order to highlight the selected item. Returns `null` if no item is
    /// currently selected.
    getMarkerTarget(): [number, number, number, number] | null {
        // Nothing selected
        if (this.state.selectedName === null) {
            return null;
        }

        // Find the selected item
        let selectedIndex = this.getSelectedIndex();
        console.assert(
            selectedIndex !== null,
            `Invalid name selected: ${
                this.state.selectedName
            } is not in ${this.state.items.map((item) => item.name)}`
        );

        // Find the location of the selected item.
        let optionElement = this.backgroundOptionsElement.children[
            selectedIndex
        ] as HTMLElement;
        let optionRect = optionElement.getBoundingClientRect();
        let parentRect = this.innerElement.getBoundingClientRect();

        return [
            optionRect.left - parentRect.left,
            optionRect.top - parentRect.top,
            getAllocatedWidthInPx(optionElement),
            getAllocatedHeightInPx(optionElement),
        ];
    }

    onItemClick(event: Event, name: string): void {
        // If this item was already selected, the new value may be `None`
        if (this.state.selectedName === name) {
            if (this.state.allow_none) {
                this.state.selectedName = null;
            } else {
                return;
            }
        } else {
            this.state.selectedName = name;
        }

        // Update the marker
        this.animateToCurrentTarget();

        // Notify the backend
        this.sendMessageToBackend({
            name: this.state.selectedName,
        });

        // Eat the event
        event.stopPropagation();
    }

    buildContent(deltaState: DeltaState<SwitcherBarState>): HTMLElement {
        let result = document.createElement("div");
        result.classList.add("rio-switcher-bar-options");
        result.style.gap = `${this.state.spacing}rem`;
        result.role = "listbox";

        let items = deltaState.items ?? this.state.items;

        // Iterate over both
        for (let i = 0; i < items.length; i++) {
            let item = items[i];

            let optionElement = new PressableElement();
            optionElement.classList.add("rio-switcher-bar-option");
            optionElement.ariaPressed = "false";
            result.appendChild(optionElement);

            optionElement.onPress = (event) =>
                this.onItemClick(event, item.name);

            // Icon
            if (item.icon !== null) {
                let iconContainer = document.createElement("div");
                iconContainer.classList.add("rio-switcher-bar-icon");
                optionElement.appendChild(iconContainer);

                applyIcon(iconContainer, item.icon);
            }

            // Text
            let textElement = document.createElement("div");
            optionElement.appendChild(textElement);
            textElement.textContent = item.name;
        }

        return result;
    }

    updateElement(
        deltaState: DeltaState<SwitcherBarState>,
        context: ComponentStatesUpdateContext
    ): void {
        super.updateElement(deltaState, context);

        // Have the options changed?
        if (deltaState.items !== undefined) {
            this.innerElement.innerHTML = "";
            this.markerElement.innerHTML = "";

            // Background options
            this.backgroundOptionsElement = this.buildContent(deltaState);
            this.innerElement.appendChild(this.backgroundOptionsElement);

            // Marker
            this.innerElement.appendChild(this.markerElement);

            // Marker options
            this.markerOptionsElement = this.buildContent(deltaState);
            this.markerElement.appendChild(this.markerOptionsElement);

            // Make sure the orientation is set correctly
            deltaState.orientation =
                deltaState.orientation ?? this.state.orientation;
            deltaState.spacing = deltaState.spacing ?? this.state.spacing;

            // Pass on all available space to the marker options
            requestAnimationFrame(() => {
                this.markerOptionsElement.style.width = `${getAllocatedWidthInPx(
                    this.backgroundOptionsElement
                )}px`;
                this.markerOptionsElement.style.height = `${getAllocatedHeightInPx(
                    this.backgroundOptionsElement
                )}px`;

                // Update the CSS
                this.updateCssToMatchState();
            });
        }

        // Color
        if (deltaState.color !== undefined) {
            applySwitcheroo(
                this.markerElement,
                deltaState.color === "keep" ? "bump" : deltaState.color
            );
        }

        // Orientation
        if (deltaState.orientation !== undefined) {
            let flexDirection =
                deltaState.orientation == "vertical" ? "column" : "row";

            this.element.style.flexDirection = flexDirection;
            this.backgroundOptionsElement.style.flexDirection = flexDirection;
            this.markerOptionsElement.style.flexDirection = flexDirection;
        }

        // Spacing
        if (deltaState.spacing !== undefined) {
            this.backgroundOptionsElement.style.gap = `${deltaState.spacing}rem`;
            this.markerOptionsElement.style.gap = `${deltaState.spacing}rem`;
        }

        // If the selection has changed make sure to move the marker
        if (deltaState.selectedName !== undefined) {
            if (this.isInitialized) {
                if (deltaState.selectedName !== this.state.selectedName) {
                    this.state.selectedName = deltaState.selectedName;
                    this.state.items = deltaState.items ?? this.state.items;
                    this.animateToCurrentTarget();
                }
            } else if (deltaState.selectedName === null) {
                this.fadeTween.teleportTo(0);
            } else {
                this.fadeTween.teleportTo(1);

                requestAnimationFrame(() => {
                    this.markerAtAnimationStart = this.markerAtAnimationEnd =
                        this.getMarkerTarget()!;

                    let animatedPosition =
                        this.state.orientation == "horizontal"
                            ? this.markerAtAnimationEnd[0]
                            : this.markerAtAnimationEnd[1];

                    this.moveTween.teleportTo(animatedPosition);
                    this.moveTween.update();
                    this.updateCssToMatchState();
                });
            }

            // Update the ARIA attributes
            let selectedIndex = this.getSelectedIndex();
            let optionElements = this.innerElement.querySelectorAll(
                ".rio-switcher-bar-option"
            );

            for (let [index, element] of optionElements.entries()) {
                element.ariaPressed =
                    index === selectedIndex ? "true" : "false";
            }
        }

        // Any future updates are not the first
        this.isInitialized = true;
    }

    private getSelectedIndex(): number | null {
        if (this.state.selectedName === null) {
            return null;
        }

        for (let [index, item] of this.state.items.entries()) {
            if (item.name === this.state.selectedName) {
                return index;
            }
        }

        return null;
    }
}
