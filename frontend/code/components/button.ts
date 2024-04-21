import { applyColorSet } from '../designApplication';
import { ColorSet, ComponentId } from '../dataModels';
import { ComponentBase, ComponentState } from './componentBase';
import { MDCRipple } from '@material/ripple';
import { LayoutContext } from '../layouting';
import { SingleContainer } from './singleContainer';
import { firstDefined } from '../utils';

export type ButtonState = ComponentState & {
    _type_: 'Button-builtin';
    shape?: 'pill' | 'rounded' | 'rectangle';
    style?: 'major' | 'minor' | 'plain';
    color?: ColorSet;
    content?: ComponentId;
    is_sensitive?: boolean;
    initially_disabled_for?: number;
};

export class ButtonComponent extends SingleContainer {
    state: Required<ButtonState>;
    private mdcRipple: MDCRipple;

    private innerElement: HTMLElement;

    // In order to prevent a newly created button from being clicked on
    // accident, it starts out disabled and enables itself after a short delay.
    private isStillInitiallyDisabled: boolean = true;

    createElement(): HTMLElement {
        // Create the element
        let element = document.createElement('div');
        element.classList.add('rio-button', 'mdc-ripple-surface');

        this.innerElement = document.createElement('div');
        element.appendChild(this.innerElement);

        // Add a material ripple effect
        this.mdcRipple = new MDCRipple(this.innerElement);

        // Detect button presses
        this.innerElement.onclick = (event) => {
            event.stopPropagation();

            // Do nothing if the button isn't sensitive
            if (!this.state['is_sensitive'] || this.isStillInitiallyDisabled) {
                return;
            }

            // Otherwise notify the backend
            this.sendMessageToBackend({
                type: 'press',
            });
        };

        setTimeout(() => {
            this.isStillInitiallyDisabled = false;
        }, this.state.initially_disabled_for * 1000);

        return element;
    }

    updateElement(
        deltaState: ButtonState,
        latentComponents: Set<ComponentBase>
    ): void {
        // Update the child
        this.replaceOnlyChild(
            latentComponents,
            deltaState.content,
            this.innerElement
        );

        // Set the shape
        if (deltaState.shape !== undefined) {
            this.innerElement.classList.remove(
                'rio-shape-pill',
                'rio-shape-rounded',
                'rio-shape-rectangle',
                'rio-shape-circle'
            );

            let className = 'rio-shape-' + deltaState.shape;
            this.innerElement.classList.add(className);
        }

        // Set the style
        if (deltaState.style !== undefined) {
            this.innerElement.classList.remove(
                'rio-buttonstyle-major',
                'rio-buttonstyle-minor',
                'rio-buttonstyle-plain'
            );

            let className = 'rio-buttonstyle-' + deltaState.style;
            this.innerElement.classList.add(className);
        }

        // Apply the color
        if (
            deltaState.color !== undefined ||
            deltaState.is_sensitive !== undefined ||
            deltaState.style !== undefined
        ) {
            // It looks ugly if every new button is initially greyed out, so for
            // the styling ignore `self.isStillInitiallyDisabled`.
            let is_sensitive: boolean = firstDefined(
                deltaState.is_sensitive,
                this.state['is_sensitive']
            );

            let colorSet = is_sensitive
                ? firstDefined(deltaState.color, this.state['color'])
                : 'disabled';

            // If no new colorset is specified, turn the accent color into the
            // plain color. This allows all styles to just assume that the color
            // they should use is the plain color.
            //
            // The exception to this is the plain style, which obviously isn't
            // trying to stand out.
            if (colorSet === 'keep') {
                colorSet = 'accent-to-plain';
            }

            applyColorSet(this.innerElement, colorSet);
        }
    }

    updateAllocatedHeight(ctx: LayoutContext): void {
        super.updateAllocatedHeight(ctx);

        // The ripple stores the coordinates of its rectangle. Since Rio likes
        // to resize and move around components, the rectangle must be updated
        // appropriately.
        this.mdcRipple.layout();
    }
}
