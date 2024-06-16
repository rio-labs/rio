import { ComponentBase, ComponentState } from './componentBase';
import { ColorSet } from '../dataModels';
import { applySwitcheroo } from '../designApplication';

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

    private optionsContainer: HTMLElement;
    private markerElement: HTMLElement;

    createElement(): HTMLElement {
        // Create the elements
        let element = document.createElement('div');
        element.classList.add('rio-switcher-bar');

        // Highlights the selected item
        this.markerElement = document.createElement('div');
        this.markerElement.classList.add('rio-switcher-bar-marker');
        element.appendChild(this.markerElement);

        this.optionsContainer = document.createElement('div');
        this.optionsContainer.classList.add(
            'rio-switcher-bar-options-container'
        );
        element.appendChild(this.optionsContainer);

        return element;
    }

    updateElement(
        deltaState: SwitcherBarState,
        latentComponents: Set<ComponentBase>
    ): void {
        super.updateElement(deltaState, latentComponents);

        // Have the options changed?
        if (
            deltaState.names !== undefined ||
            deltaState.icon_svg_sources !== undefined
        ) {
            this.rebuildOptions(
                deltaState.names ?? this.state.names,
                deltaState.icon_svg_sources ?? this.state.icon_svg_sources
            );
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

            this.optionsContainer.style.flexDirection = flexDirection;
        }

        // Spacing
        if (deltaState.spacing !== undefined) {
            this.optionsContainer.style.gap = `${deltaState.spacing}rem`;
        }

        // If the selection has changed make sure to move the marker
        if (deltaState.selectedName !== undefined) {
            if (deltaState.selectedName === null) {
                this.moveMarkerTo(null);
            } else {
                let i = (deltaState.names ?? this.state.names).indexOf(
                    deltaState.selectedName
                );
                this.moveMarkerTo(i);
            }
        }
    }

    private rebuildOptions(
        names: string[],
        iconSvgSources: (string | null)[]
    ): void {
        this.optionsContainer.innerHTML = '';

        for (let [index, name] of names.entries()) {
            let iconSvg = iconSvgSources[index];

            let optionElement = this.buildOptionElement(index, name, iconSvg);
            this.optionsContainer.appendChild(optionElement);
        }
    }

    private buildOptionElement(
        index: number,
        name: string,
        iconSvg: string | null
    ): HTMLElement {
        let optionElement = document.createElement('div');
        optionElement.classList.add('rio-switcher-bar-option');

        // Icon
        if (iconSvg !== null) {
            optionElement.innerHTML = iconSvg;
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
                    this.moveMarkerTo(null);
                } else {
                    return;
                }
            } else {
                this.state.selectedName = name;
                this.moveMarkerTo(index);
            }

            // Notify the backend
            this.sendMessageToBackend({
                name: this.state.selectedName,
            });

            // Eat the event
            event.stopPropagation();
        });

        return optionElement;
    }

    private moveMarkerTo(index: number | null): void {
        if (index === null) {
            this.markerElement.style.width = '0';
            this.markerElement.style.height = '0';
            return;
        }

        let optionElement = this.optionsContainer.children[index];
        let optionRect = optionElement.getBoundingClientRect();
        let containerRect = this.optionsContainer.getBoundingClientRect();

        this.markerElement.style.left = `${
            optionRect.left - containerRect.left
        }px`;
        this.markerElement.style.top = `${
            optionRect.top - containerRect.top
        }px`;
        this.markerElement.style.width = `${optionRect.width}px`;
        this.markerElement.style.height = `${optionRect.height}px`;
    }
}
