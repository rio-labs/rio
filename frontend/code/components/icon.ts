import {
    Color,
    ColorSet,
    ImageFill,
    LinearGradientFill,
    RadialGradientFill,
    SolidFill,
} from "../dataModels";
import { ComponentBase, ComponentState, DeltaState } from "./componentBase";
import { applyIcon, applyFillToSVG } from "../designApplication";

export type IconState = ComponentState & {
    _type_: "Icon-builtin";
    icon: string;
    fill:
        | SolidFill
        | LinearGradientFill
        | RadialGradientFill
        | ImageFill
        | Color
        | ColorSet
        | "dim";
};

export class IconComponent extends ComponentBase<IconState> {
    private svgElement: SVGSVGElement;

    createElement(): HTMLElement {
        let element = document.createElement("div");
        element.classList.add("rio-icon");
        return element;
    }

    updateElement(
        deltaState: DeltaState<IconState>,
        latentComponents: Set<ComponentBase>
    ): void {
        super.updateElement(deltaState, latentComponents);

        if (deltaState.icon !== undefined) {
            // Loading the icon may take a while and applying the fill actually
            // alters the icon's SVG source, so if the icon has changed, we
            // have to wait until the SVG source is loaded and then re-apply the
            // fill.
            let fill = deltaState.fill ?? this.state.fill;

            applyIcon(this.element, deltaState.icon, fill);
            return;
        }

        if (deltaState.fill !== undefined) {
            applyFillToSVG(this.svgElement, deltaState.fill);
        }
    }
}
