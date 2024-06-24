import { applySwitcheroo } from '../designApplication';
import { ColorSet, ComponentId } from '../dataModels';
import { ComponentBase, ComponentState } from './componentBase';
import { RippleEffect } from '../rippleEffect';
import { firstDefined } from '../utils';
import { markEventAsHandled } from '../eventHandling';

type AbstractButtonState = ComponentState & {
    shape?: 'pill' | 'rounded' | 'rectangle' | 'circle';
    style?: 'major' | 'minor' | 'plain';
    color?: ColorSet;
    content?: ComponentId;
    is_sensitive?: boolean;
};

abstract class AbstractButtonComponent extends ComponentBase {
    state: Required<AbstractButtonState>;

    protected buttonElement: HTMLElement;

    private rippleInstance: RippleEffect;

    // In order to prevent a newly created button from being clicked on
    // accident, it starts out disabled and enables itself after a short delay.
    private isStillInitiallyDisabled: boolean = true;

    protected createButtonElement(): HTMLElement {
        // Create the element
        let element = document.createElement('div');
        element.classList.add('rio-button');

        // Add a material ripple effect
        this.rippleInstance = new RippleEffect(element, {
            triggerOnPress: false,
        });

        // Detect button presses
        element.onclick = (event) => {
            markEventAsHandled(event);

            // Do nothing if the button isn't sensitive
            if (!this.state['is_sensitive'] || this.isStillInitiallyDisabled) {
                return;
            }

            this.rippleInstance.trigger(event);

            // Otherwise notify the backend
            this.sendMessageToBackend({
                type: 'press',
            });
        };

        setTimeout(() => {
            this.isStillInitiallyDisabled = false;
        }, 350);

        return element;
    }

    updateElement(
        deltaState: AbstractButtonState,
        latentComponents: Set<ComponentBase>
    ): void {
        super.updateElement(deltaState, latentComponents);

        // Update the child
        this.replaceOnlyChild(
            latentComponents,
            deltaState.content,
            this.buttonElement
        );

        // Set the shape
        if (deltaState.shape !== undefined) {
            this.buttonElement.classList.remove(
                'rio-shape-pill',
                'rio-shape-rounded',
                'rio-shape-rectangle',
                'rio-shape-circle'
            );

            let className = 'rio-shape-' + deltaState.shape;
            this.buttonElement.classList.add(className);
        }

        // Set the style
        if (deltaState.style !== undefined) {
            this.buttonElement.classList.remove(
                'rio-buttonstyle-major',
                'rio-buttonstyle-minor',
                'rio-buttonstyle-plain'
            );

            let className = 'rio-buttonstyle-' + deltaState.style;
            this.buttonElement.classList.add(className);
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

            // If no new colorset is specified, bump to the next palette. This
            // allows all styles to just assume that the palette they should use
            // is the current one.
            applySwitcheroo(
                this.buttonElement,
                colorSet === 'keep' ? 'bump' : colorSet
            );
        }
    }
}

export type ButtonState = AbstractButtonState & {
    _type_: 'Button-builtin';
};

export class ButtonComponent extends AbstractButtonComponent {
    state: Required<ButtonState>;

    createElement(): HTMLElement {
        this.buttonElement = this.createButtonElement();
        return this.buttonElement;
    }
}

export type IconButtonState = AbstractButtonState & {
    _type_: 'IconButton-builtin';
    icon: string;
};

export class IconButtonComponent extends AbstractButtonComponent {
    state: Required<IconButtonState>;

    protected createElement(): HTMLElement {
        let element = document.createElement('div');
        element.classList.add('rio-icon-button');

        let helperElement1 = document.createElement('div');
        element.appendChild(helperElement1);

        let helperElement2 = document.createElement('div');
        helperElement1.appendChild(helperElement2);

        let helperElement3 = document.createElement('div');
        helperElement2.appendChild(helperElement3);

        this.buttonElement = this.createButtonElement();
        helperElement3.appendChild(this.buttonElement);

        return element;
    }
}
