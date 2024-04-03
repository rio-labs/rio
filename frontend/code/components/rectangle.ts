import { BoxStyle, ComponentId } from '../models';
import { colorToCssString, fillToCss } from '../cssUtils';
import { ComponentBase, ComponentState } from './componentBase';
import { MDCRipple } from '@material/ripple';
import { SingleContainer } from './singleContainer';

export type RectangleState = ComponentState & {
    _type_: 'Rectangle-builtin';
    style?: BoxStyle;
    content?: ComponentId | null;
    hover_style?: BoxStyle | null;
    transition_time?: number;
    cursor?: string;
    ripple?: boolean;
};

function setBoxStyleVariables(
    element: HTMLElement,
    style: BoxStyle | undefined,
    prefix: string,
    suffix: string
): void {
    // Do nothing if no style was passed
    if (style === undefined) {
        return;
    }

    // Define a set of CSS variables which should be set. For now without the
    // prefix
    let variables: object = {};

    if (style === null) {
        variables = {
            background: 'transparent',

            'stroke-color': 'transparent',
            'stroke-width': '0',

            'corner-radius-top-left': '0',
            'corner-radius-top-right': '0',
            'corner-radius-bottom-right': '0',
            'corner-radius-bottom-left': '0',

            'shadow-color': 'transparent',
            'shadow-radius': '0',
            'shadow-offset-x': '0',
            'shadow-offset-y': '0',
        };
    } else {
        Object.assign(variables, fillToCss(style.fill));

        variables['stroke-color'] = colorToCssString(style.strokeColor);
        variables['stroke-width'] = `${style.strokeWidth}rem`;

        variables['corner-radius-top-left'] = `${style.cornerRadius[0]}rem`;
        variables['corner-radius-top-right'] = `${style.cornerRadius[1]}rem`;
        variables['corner-radius-bottom-right'] = `${style.cornerRadius[2]}rem`;
        variables['corner-radius-bottom-left'] = `${style.cornerRadius[3]}rem`;

        variables['shadow-color'] = colorToCssString(style.shadowColor);
        variables['shadow-radius'] = `${style.shadowRadius}rem`;
        variables['shadow-offset-x'] = `${style.shadowOffset[0]}rem`;
        variables['shadow-offset-y'] = `${style.shadowOffset[1]}rem`;
    }

    // Set the variables and add the prefix
    for (const [key, value] of Object.entries(variables)) {
        element.style.setProperty(`--${prefix}${key}${suffix}`, value);
    }
}

export class RectangleComponent extends SingleContainer {
    state: Required<RectangleState>;

    // If this rectangle has a ripple effect, this is the ripple instance.
    // `null` otherwise.
    private mdcRipple: MDCRipple | null = null;

    createElement(): HTMLElement {
        let element = document.createElement('div');
        element.classList.add('rio-rectangle');
        return element;
    }

    updateElement(
        deltaState: RectangleState,
        latentComponents: Set<ComponentBase>
    ): void {
        let element = this.element;

        if (deltaState.style !== undefined) {
            setBoxStyleVariables(element, deltaState.style, 'rectangle-', '');
        }

        this.replaceFirstChild(latentComponents, deltaState.content);

        if (deltaState.transition_time !== undefined) {
            element.style.transitionDuration = `${deltaState.transition_time}s`;
        }

        if (deltaState.hover_style === null) {
            element.classList.remove('rio-rectangle-hover');
        } else if (deltaState.hover_style !== undefined) {
            element.classList.add('rio-rectangle-hover');
            setBoxStyleVariables(
                element,
                deltaState.hover_style,
                'rectangle-',
                '-hover'
            );
        }

        if (deltaState.cursor !== undefined) {
            if (deltaState.cursor === 'default') {
                element.style.removeProperty('cursor');
            } else {
                element.style.cursor = deltaState.cursor;
            }
        }

        if (deltaState.ripple === true) {
            if (this.mdcRipple === null) {
                this.mdcRipple = new MDCRipple(element);

                element.classList.add('mdc-ripple-surface');
                element.classList.add('rio-rectangle-ripple');
            }
        } else if (deltaState.ripple === false) {
            if (this.mdcRipple !== null) {
                this.mdcRipple.destroy();
                this.mdcRipple = null;

                element.classList.remove('mdc-ripple-surface');
                element.classList.remove('rio-rectangle-ripple');
            }
        }

        // The ripple effect stores the coordinates of its rectangle. Since
        // rio likes to resize and move around components, the rectangle must be
        // updated appropriately.
        //
        // Really, this should be done when the component is resized or moved, but
        // there is no hook for that. Update seems to work fine.
        if (this.mdcRipple !== null) {
            requestAnimationFrame(() => {
                if (this.mdcRipple !== null) {
                    this.mdcRipple.layout();
                }
            });
        }
    }
}
