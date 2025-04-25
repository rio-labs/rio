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
import { ComponentStatesUpdateContext } from "../componentManagement";

type IconCompatibleFill =
    | SolidFill
    | LinearGradientFill
    | RadialGradientFill
    | ImageFill
    | Color
    | ColorSet
    | "dim";

export type IconState = ComponentState & {
    _type_: "Icon-builtin";
    icon: string;
    fill: IconCompatibleFill;
};

export class IconComponent extends ComponentBase<IconState> {
    createElement(context: ComponentStatesUpdateContext): HTMLElement {
        let element = document.createElement("div");
        element.classList.add("rio-icon");
        return element;
    }

    updateElement(
        deltaState: DeltaState<IconState>,
        context: ComponentStatesUpdateContext
    ): void {
        super.updateElement(deltaState, context);

        if (deltaState.icon !== undefined) {
            // Loading the icon may take a while and applying the fill actually
            // alters the icon's SVG source, so if the icon has changed, we
            // have to wait until the SVG source is loaded and then re-apply the
            // fill.
            let fill = deltaState.fill ?? this.state.fill;

            applyIcon(this.element, deltaState.icon, fill).then(() => {
                // The fill may have changed while the icon was loading, so
                // we'll re-apply it
                this.applyFillIfSvgElementExists(this.state.fill);
            });
            return;
        }

        if (deltaState.fill !== undefined) {
            this.applyFillIfSvgElementExists(deltaState.fill);
        }
    }

    private applyFillIfSvgElementExists(fill: IconCompatibleFill): void {
        let svgRoot = this.element.querySelector("svg");
        if (svgRoot === null) {
            return;
        }

        applyFillToSVG(svgRoot, fill);
    }
}
