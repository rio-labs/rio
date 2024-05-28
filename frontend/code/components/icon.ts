import {
    Color,
    ColorSet,
    ImageFill,
    LinearGradientFill,
    SolidFill,
} from '../dataModels';
import { ComponentBase, ComponentState } from './componentBase';
import { applyFillToSVG } from '../designApplication';
import { pixelsPerRem } from '../app';
import { LayoutContext } from '../layouting';

export type IconState = ComponentState & {
    _type_: 'Icon-builtin';
    svgSource: string;
    fill: SolidFill | LinearGradientFill | ImageFill | Color | ColorSet | 'dim';
};

export class IconComponent extends ComponentBase {
    state: Required<IconState>;

    private svgElement: SVGSVGElement;

    createElement(): HTMLElement {
        let element = document.createElement('div');
        element.classList.add('rio-icon');
        return element;
    }

    updateElement(
        deltaState: IconState,
        latentComponents: Set<ComponentBase>
    ): void {
        if (deltaState.svgSource !== undefined) {
            // Replace the SVG element
            this.element.innerHTML = deltaState.svgSource;
            this.svgElement = this.element.querySelector(
                'svg'
            ) as SVGSVGElement;

            // If the fill has changed, it'll be applied by the code below. But
            // if it hasn't, then it's our responsibility to apply the current
            // fill.
            if (deltaState.fill === undefined) {
                applyFillToSVG(this.svgElement, this.state.fill);
            }
        }

        if (deltaState.fill !== undefined) {
            applyFillToSVG(this.svgElement, deltaState.fill);
        }
    }

    updateAllocatedHeight(ctx: LayoutContext): void {
        // The SVG has no size on its own. This is so it scales up, rather than
        // staying a fixed size. However, this removes its "size request". If a
        // size was provided by the backend, apply that explicitly.

        // SVG can't handle `rem`, but needs `px`. Convert.
        this.svgElement.setAttribute(
            'width',
            `${this.allocatedWidth * pixelsPerRem}px`
        );
        this.svgElement.setAttribute(
            'height',
            `${this.allocatedHeight * pixelsPerRem}px`
        );
    }
}
