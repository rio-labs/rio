import { ComponentBase, ComponentState } from './componentBase';
import { ColorSet, TextStyle } from '../dataModels';
import { applySwitcheroo } from '../designApplication';
import { textStyleToCss } from '../cssUtils';
import { firstDefined } from '../utils';
import { MappingTween } from '../tweens/mappingTweens';
import { BaseTween } from '../tweens/baseTween';
import { KineticTween } from '../tweens/kineticTween';
import { pixelsPerRem } from '../app';

// Whitespace around each option
const OPTION_MARGIN: number = 0.5;

// Width & height of the SVG in each option
const ICON_HEIGHT: number = 1.8;

// Whitespace between the icon and the text, if both are present
const ICON_MARGIN: number = 0.5;

const TEXT_STYLE: TextStyle = {
    fontName: 'Roboto',
    fill: [0, 0, 0, 1],
    fontSize: 1,
    italic: false,
    fontWeight: 'bold',
    underlined: false,
    allCaps: false,
};

const TEXT_STYLE_CSS_OPTIONS: object = textStyleToCss(TEXT_STYLE);

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

    // Animation state
    private fadeTween: BaseTween;
    private moveTween: BaseTween;

    private animationIsRunning: boolean = false;

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

        // Prepare animations
        this.fadeTween = new MappingTween({
            mapping: (value: number) => value,
            duration: 0.18,
        });

        this.moveTween = new KineticTween({
            acceleration: 150 * pixelsPerRem,
        });

        return elementOuter;
    }

    /// Update the HTML & CSS to match the current state
    updateCssToMatchState(): void {
        // Where should the marker be at?
        let markerCurLeft, markerCurTop;

        if (this.state.orientation === 'horizontal') {
            markerCurLeft = this.moveTween.current;
            markerCurTop = 0;
        } else {
            markerCurLeft = 0;
            markerCurTop = this.moveTween.current;
        }

        // What size should the marker be?
        let targetWidth, targetHeight;
        let targetRect = this.getMarkerTarget();

        if (targetRect === null) {
            // targetWidth = this.targetWidthAtAnimationStart;
            // targetHeight = this.targetHeightAtAnimationStart;
            targetWidth = 30;
            targetHeight = 20;
        } else {
            targetWidth = targetRect[2];
            targetHeight = targetRect[3];
        }

        // How large should the marker be?
        // Account for the marker's fade-in animation
        let fade = this.fadeTween.current;
        let markerCurWidth = targetWidth * fade;
        let markerCurHeight = targetHeight * fade;
        markerCurLeft += (targetWidth - markerCurWidth) / 2;
        markerCurTop += (targetHeight - markerCurHeight) / 2;

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
            requestAnimationFrame(this.ensureAnimationIsRunning.bind(this));
        }
    }

    ensureAnimationIsRunning(): void {
        if (this.animationIsRunning) {
            return;
        }

        requestAnimationFrame(this.animationWorker.bind(this));
    }

    /// Start moving the marker to match the current state, taking care of
    /// animations and everything
    animateTo(targetName: string | null): void {
        // Move the marker
        if (targetName !== null) {
            let markerTarget = this.getMarkerTarget()!;
            let targetPosition =
                this.state.orientation == 'horizontal'
                    ? markerTarget[0]
                    : markerTarget[1];

            // If the marker is currently completely invisible, teleport.
            if (this.fadeTween.current === 0) {
                this.moveTween.teleportTo(targetPosition);
            } else {
                this.moveTween.transitionTo(targetPosition);
            }
        }

        // Fade the marker in/out
        if (targetName === null) {
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
        let selectedIndex = this.state.names.indexOf(this.state.selectedName!);
        console.assert(selectedIndex !== -1);

        // Find the location of the selected item.
        let optionElement =
            this.backgroundOptionsElement.children[selectedIndex];
        let optionRect = optionElement.getBoundingClientRect();
        let parentRect = this.innerElement.getBoundingClientRect();

        return [
            optionRect.left - parentRect.left,
            optionRect.top - parentRect.top,
            optionRect.width,
            optionRect.height,
        ];
    }

    onItemClick(event: MouseEvent, name: string): void {
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
        this.animateTo(this.state.selectedName);

        // Notify the backend
        this.sendMessageToBackend({
            name: this.state.selectedName,
        });

        // Eat the event
        event.stopPropagation();
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
            optionElement.addEventListener('click', (event) =>
                this.onItemClick(event, name)
            );
        }

        return result;
    }

    updateElement(
        deltaState: SwitcherBarState,
        latentComponents: Set<ComponentBase>
    ): void {
        // Have the options changed?
        if (
            deltaState.names !== undefined ||
            deltaState.icon_svg_sources !== undefined
        ) {
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
        }

        // Spacing
        if (deltaState.spacing !== undefined) {
            this.element.style.gap = `${deltaState.spacing}rem`;
        }

        // If the selection has changed make sure to move the marker
        if (deltaState.selectedName !== undefined) {
            if (this.isInitialized) {
                this.animateTo(deltaState.selectedName);
                this.state.selectedName = deltaState.selectedName;
            } else {
                // TODO: Parent the marker to the correct element
            }
        }

        // Any future updates are not the first
        this.isInitialized = true;
    }
}
