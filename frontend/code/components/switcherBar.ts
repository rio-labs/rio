import { ComponentBase, ComponentState } from './componentBase';
import { ColorSet } from '../dataModels';
import { applySwitcheroo } from '../designApplication';
import { getTextDimensionsWithCss } from '../layoutHelpers';
import { LayoutContext } from '../layouting';
import { easeInOut } from '../easeFunctions';
import { firstDefined } from '../utils';

const ACCELERATION: number = 350; // rem/s^2

const MARKER_FADE_DURATION: number = 0.18; // s

// Whitespace around each option
const OPTION_MARGIN: number = 0.5;

// Width & height of the SVG in each option
const ICON_HEIGHT: number = 1.8;

// Whitespace between the icon and the text, if both are present
const ICON_MARGIN: number = 0.5;

const TEXT_STYLE_CSS_OPTIONS: object = {
    'font-weight': 'bold',
};

export type SwitcherBarState = ComponentState & {
    _type_: 'SwitcherBar-builtin';
    names?: string[];
    icon_svg_sources?: (string | null)[];
    color?: ColorSet;
    orientation?: 'horizontal' | 'vertical';
    spacing?: number;
    allow_none: boolean;
    selectedName?: string | null;
};

export class SwitcherBarComponent extends ComponentBase {
    state: Required<SwitcherBarState>;

    private innerElement: HTMLElement;
    private markerElement: HTMLElement;
    private backgroundOptionsElement: HTMLElement;
    private markerOptionsElement: HTMLElement;

    // The width and height of each option. Icon, string and all
    private optionWidths: number[];
    private optionHeights: number[];

    // Marker animation state
    private markerCurFade: number;

    private markerCurLeft: number = 0;
    private markerCurTop: number = 0;
    private markerCurWidth: number = 0;
    private markerCurHeight: number = 0;

    private markerCurVelocity: number = 0;

    // -1 if no animation is running
    private lastAnimationTickAt: number = -1;

    // Allows to determine whether this is the first time the element is being
    // updated.
    private isInitialized: boolean = false;

    createElement(): HTMLElement {
        // Create the elements
        let elementOuter = document.createElement('div');
        elementOuter.classList.add('rio-switcher-bar');

        // Centers the bar
        this.innerElement = document.createElement('div');
        elementOuter.appendChild(this.innerElement);

        // Highlights the selected item
        this.markerElement = document.createElement('div');
        this.markerElement.classList.add('rio-switcher-bar-marker');

        return elementOuter;
    }

    /// Instantly move the marker to the position stored in the instance
    placeMarkerToState(): void {
        // Account for the marker's resize animation
        let easedFade = easeInOut(this.markerCurFade);
        let scaledWidth = this.markerCurWidth * easedFade;
        let scaledHeight = this.markerCurHeight * easedFade;

        let left = this.markerCurLeft + (this.markerCurWidth - scaledWidth) / 2;
        let top = this.markerCurTop + (this.markerCurHeight - scaledHeight) / 2;

        // Move the marker
        this.markerElement.style.left = `${left}rem`;
        this.markerElement.style.top = `${top}rem`;
        this.markerElement.style.width = `${scaledWidth}rem`;
        this.markerElement.style.height = `${scaledHeight}rem`;

        // The inner options are positioned relative to the marker. Move them in
        // the opposite direction so they stay put.
        this.markerOptionsElement.style.left = `-${left}rem`;
        this.markerOptionsElement.style.top = `-${top}rem`;
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
        let selectedIndex = this.state.names.indexOf(this.state.selectedName!);
        console.assert(selectedIndex !== -1);

        // Find the location of the selected item. This could be done using
        // `getBoundingClientRect`, but for some reason that seems to yield
        // wrong results occasionally.

        // Horizontal
        if (this.state.orientation == 'horizontal') {
            let additionalWidth = this.allocatedWidth - this.naturalWidth;
            let left = 0;

            // Spacing
            if (this.state.names.length === 1) {
                left = additionalWidth / 2;
            } else {
                let spacing =
                    additionalWidth / (this.state.names.length - 1) +
                    this.state.spacing;
                left = spacing * selectedIndex;
            }

            // Items
            for (let i = 0; i < selectedIndex; i++) {
                left += this.optionWidths[i];
            }

            // Combine everything
            return [
                left,
                0,
                this.optionWidths[selectedIndex],
                this.naturalHeight,
            ];
        }

        // Vertical
        else {
            let additionalHeight = this.allocatedHeight - this.naturalHeight;
            let top = 0;

            // Spacing
            if (this.state.names.length === 1) {
                top = additionalHeight / 2;
            } else {
                let spacing =
                    additionalHeight / (this.state.names.length - 1) +
                    this.state.spacing;
                top = spacing * selectedIndex;
            }

            // Items
            for (let i = 0; i < selectedIndex; i++) {
                top += this.optionHeights[i];
            }

            // Combine everything
            return [
                0,
                top,
                this.naturalWidth,
                this.optionHeights[selectedIndex],
            ];
        }
    }

    /// Instantly move the marker to the currently selected item
    moveMarkerInstantlyIfAnimationIsntRunning(): void {
        // Already transitioning?
        if (this.lastAnimationTickAt !== -1) {
            return;
        }

        // Where to move to?
        let target = this.getMarkerTarget();

        // No target
        if (target === null) {
            return;
        }

        // Teleport
        this.markerCurLeft = target[0];
        this.markerCurTop = target[1];
        this.markerCurWidth = target[2];
        this.markerCurHeight = target[3];
        this.placeMarkerToState();
    }

    moveAnimationWorker(deltaTime: number): boolean {
        // Where to move to?
        let target = this.getMarkerTarget();

        // The target may disappear while the animation is running. Handle that
        // gracefully.
        if (target === null) {
            return false;
        }

        // Calculate the distance to the target
        let curPos: number, targetPos: number;
        if (this.state.orientation == 'horizontal') {
            curPos = this.markerCurLeft;
            targetPos = target[0];
        } else {
            curPos = this.markerCurTop;
            targetPos = target[1];
        }

        let signedRemainingDistance = targetPos - curPos;

        // Which direction to accelerate towards?
        let accelerationFactor; // + means towards the target
        let brakingDistance =
            Math.pow(this.markerCurVelocity, 2) / (2 * ACCELERATION);

        // Case: Moving away from the target
        if (
            Math.sign(signedRemainingDistance) !=
            Math.sign(this.markerCurVelocity)
        ) {
            accelerationFactor = 3;
        }
        // Case: Don't run over the target quite so hard
        else if (Math.abs(signedRemainingDistance) < brakingDistance) {
            accelerationFactor = -1;
        }
        // Case: Accelerate towards the target
        else {
            accelerationFactor = 1;
        }

        let currentAcceleration =
            ACCELERATION *
            accelerationFactor *
            Math.sign(signedRemainingDistance);

        // Update the velocity
        this.markerCurVelocity += currentAcceleration * deltaTime;
        let deltaDistance = this.markerCurVelocity * deltaTime;

        // Arrived?
        let t;
        if (Math.abs(deltaDistance) >= Math.abs(signedRemainingDistance)) {
            t = 1;
        } else {
            t = deltaDistance / signedRemainingDistance;
        }

        // Update the marker
        this.markerCurLeft += t * (target[0] - this.markerCurLeft);
        this.markerCurTop += t * (target[1] - this.markerCurTop);
        this.markerCurWidth += t * (target[2] - this.markerCurWidth);
        this.markerCurHeight += t * (target[3] - this.markerCurHeight);

        // Done?
        return t !== 1;
    }

    fadeAnimationWorker(deltaTime: number): boolean {
        // Fade in or out?
        let target = this.state.selectedName === null ? 0 : 1;

        // Update state
        let amount =
            (Math.sign(target - this.markerCurFade) * deltaTime) /
            MARKER_FADE_DURATION;
        this.markerCurFade += amount;
        this.markerCurFade = Math.min(Math.max(this.markerCurFade, 0), 1);

        // Keep going?
        return this.markerCurFade !== target;
    }

    animationWorker() {
        // How much time has passed?
        let now = Date.now();
        let deltaTime = (now - this.lastAnimationTickAt) / 1000;
        this.lastAnimationTickAt = now;

        // Run the animations
        let moveKeepGoing = this.moveAnimationWorker(deltaTime);
        let fadeKeepGoing = this.fadeAnimationWorker(deltaTime);
        let keepGoing = moveKeepGoing || fadeKeepGoing;

        // Update the marker to match the current state
        this.placeMarkerToState();

        // Keep going?
        if (keepGoing) {
            requestAnimationFrame(this.animationWorker.bind(this));
        } else {
            this.lastAnimationTickAt = -1;
        }
    }

    startAnimationIfNotRunning(): void {
        // Already running?
        if (this.lastAnimationTickAt !== -1) {
            return;
        }

        // Nope, get going
        this.lastAnimationTickAt = Date.now();
        this.markerCurVelocity = 0;
        this.animationWorker();
    }

    /// High level function to update the marker. It will animate the marker as
    /// appropriate.
    switchMarkerToSelectedName(): void {
        // No value selected? Fade out
        let target = this.getMarkerTarget();
        if (target === null) {
            this.startAnimationIfNotRunning();
            return;
        }

        // If the marker is currently invisible, teleport it
        if (this.markerCurFade === 0) {
            this.markerCurLeft = target[0];
            this.markerCurTop = target[1];
            this.markerCurWidth = target[2];
            this.markerCurHeight = target[3];
            this.placeMarkerToState();
        }

        // Start the animation(s)
        this.startAnimationIfNotRunning();
    }

    buildContent(deltaState: SwitcherBarState): HTMLElement {
        let result = document.createElement('div');
        result.classList.add('rio-switcher-bar-options');
        Object.assign(result.style, TEXT_STYLE_CSS_OPTIONS);
        result.style.removeProperty('color');

        let names = firstDefined(deltaState.names, this.state.names);
        let iconSvgSources = firstDefined(
            deltaState.icon_svg_sources,
            this.state.icon_svg_sources
        );

        // Iterate over both
        for (let i = 0; i < names.length; i++) {
            let name = names[i];
            let iconSvg = iconSvgSources[i];

            let optionElement = document.createElement('div');
            optionElement.classList.add('rio-switcher-bar-option');
            optionElement.style.padding = `${OPTION_MARGIN}rem`;
            result.appendChild(optionElement);

            // Icon
            let iconElement;
            if (iconSvg !== null) {
                optionElement.innerHTML = iconSvg;
                iconElement = optionElement.children[0] as HTMLElement;
                iconElement.style.width = `${ICON_HEIGHT}rem`;
                iconElement.style.height = `${ICON_HEIGHT}rem`;
                iconElement.style.marginBottom = `${ICON_MARGIN}rem`;
                iconElement.style.fill = 'currentColor';
            }

            // Text
            let textElement = document.createElement('div');
            optionElement.appendChild(textElement);
            textElement.textContent = name;

            // Detect clicks
            optionElement.addEventListener('click', (event) => {
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
                this.switchMarkerToSelectedName();

                // Notify the backend
                this.sendMessageToBackend({
                    name: this.state.selectedName,
                });

                // Eat the event
                event.stopPropagation();
            });
        }

        // Pass the allocated size on to the content. This can't rely on CSS,
        // because the inner content is necessarily located inside of the
        // marker, which in turn is smaller than the full space.
        if (this.state.orientation == 'horizontal') {
            result.style.width = `${this.allocatedWidth}rem`;
        } else {
            result.style.height = `${this.allocatedHeight}rem`;
        }

        return result;
    }

    updateElement(
        deltaState: SwitcherBarState,
        latentComponents: Set<ComponentBase>
    ): void {
        let markerPositionNeedsUpdate = false;
        let needsReLayout = false;

        // Have the options changed?
        if (
            deltaState.names !== undefined ||
            deltaState.icon_svg_sources !== undefined
        ) {
            {
                // The option sizes need to be recomputed
                this.optionWidths = [];
                this.optionHeights = [];

                let names = firstDefined(deltaState.names, this.state.names);
                let iconSvgSources = firstDefined(
                    deltaState.icon_svg_sources,
                    this.state.icon_svg_sources
                );

                // Iterate over both
                for (let i = 0; i < names.length; i++) {
                    let name = names[i];
                    let iconSvg = iconSvgSources[i];

                    // Text
                    let [width, height] = getTextDimensionsWithCss(
                        name,
                        TEXT_STYLE_CSS_OPTIONS
                    );

                    // Icon + margin, if present
                    if (iconSvg !== null) {
                        width = Math.max(width, ICON_HEIGHT);
                        height += ICON_HEIGHT + ICON_MARGIN;
                    }

                    // Margin around
                    width += 2 * OPTION_MARGIN;
                    height += 2 * OPTION_MARGIN;

                    // Store the result
                    this.optionWidths.push(width);
                    this.optionHeights.push(height);
                }
            }

            // The HTML needs to be rebuilt
            {
                this.markerElement.innerHTML = '';
                this.innerElement.innerHTML = '';

                // Background options
                this.backgroundOptionsElement = this.buildContent(deltaState);
                this.innerElement.appendChild(this.backgroundOptionsElement);

                // Marker
                this.innerElement.appendChild(this.markerElement);

                // Marker options
                this.markerOptionsElement = this.buildContent(deltaState);
                this.markerElement.appendChild(this.markerOptionsElement);
            }

            // Request updates
            markerPositionNeedsUpdate = true;
            needsReLayout = true;
        }

        // Color
        if (deltaState.color !== undefined) {
            applySwitcheroo(
                this.markerElement,
                deltaState.color === 'keep' ? 'bump' : deltaState.color
            );
        }

        // Orientation
        if (deltaState.orientation !== undefined) {
            let flexDirection =
                deltaState.orientation == 'vertical' ? 'column' : 'row';

            this.element.style.flexDirection = flexDirection;
            this.backgroundOptionsElement.style.flexDirection = flexDirection;
            this.markerOptionsElement.style.flexDirection = flexDirection;

            // Request updates
            markerPositionNeedsUpdate = true;
            needsReLayout = true;
        }

        // Spacing
        if (deltaState.spacing !== undefined) {
            markerPositionNeedsUpdate = true;
            needsReLayout = true;
        }

        // If the selection has changed make sure to move the marker
        if (deltaState.selectedName !== undefined) {
            if (this.isInitialized) {
                this.state.selectedName = deltaState.selectedName;
                this.switchMarkerToSelectedName();
            } else {
                markerPositionNeedsUpdate = true;
                this.markerCurFade = deltaState.selectedName === null ? 0 : 1;
            }
        }

        // Any future updates are not the first
        this.isInitialized = true;

        // Perform any requested updates
        Object.assign(this.state, deltaState);

        if (markerPositionNeedsUpdate) {
            this.moveMarkerInstantlyIfAnimationIsntRunning();
        }

        if (needsReLayout) {
            this.makeLayoutDirty();
        }
    }

    updateNaturalWidth(ctx: LayoutContext): void {
        if (this.state.orientation == 'horizontal') {
            // Spacing
            this.naturalWidth =
                this.state.spacing * (this.state.names.length - 1);

            // Options
            this.optionWidths.forEach((width) => {
                this.naturalWidth += width;
            });
        } else {
            // Options
            this.naturalWidth = 0;

            this.optionWidths.forEach((width) => {
                this.naturalWidth = Math.max(this.naturalWidth, width);
            });
        }
    }

    updateNaturalHeight(ctx: LayoutContext): void {
        if (this.state.orientation == 'horizontal') {
            // Options
            this.naturalHeight = 0;

            this.optionHeights.forEach((height) => {
                this.naturalHeight = Math.max(this.naturalHeight, height);
            });
        } else {
            // Spacing
            this.naturalHeight =
                this.state.spacing * (this.state.names.length - 1);

            // Options
            this.optionHeights.forEach((height) => {
                this.naturalHeight += height;
            });
        }
    }

    updateAllocatedHeight(ctx: LayoutContext): void {
        // Pass on the allocated size to the options
        let width, height;
        if (this.state.orientation == 'horizontal') {
            width = `${this.allocatedWidth}rem`;
            height = '';
        } else {
            width = '';
            height = `${this.allocatedHeight}rem`;
        }

        this.backgroundOptionsElement.style.width = width;
        this.backgroundOptionsElement.style.height = height;

        this.markerOptionsElement.style.width = width;
        this.markerOptionsElement.style.height = height;

        // Reposition the marker
        this.moveMarkerInstantlyIfAnimationIsntRunning();
    }
}
