import { ComponentStatesUpdateContext } from "../componentManagement";
import { applyIcon } from "../designApplication";
import { getAllocatedHeightInPx, getAllocatedWidthInPx } from "../utils";
import { ComponentBase, ComponentState, DeltaState } from "./componentBase";

const FILL_MODE_TO_OBJECT_FIT = {
    fit: "contain",
    stretch: "fill",
    zoom: "cover",
} as const;

export type ImageState = ComponentState & {
    _type_: "Image-builtin";
    fill_mode: keyof typeof FILL_MODE_TO_OBJECT_FIT;
    imageUrl: string;
    reportError: boolean;
    corner_radius: [number, number, number, number];
    accessibility_description: string;
};

export class ImageComponent extends ComponentBase<ImageState> {
    private imageElement: HTMLImageElement;
    private resizeObserver: ResizeObserver;

    createElement(context: ComponentStatesUpdateContext): HTMLElement {
        let element = document.createElement("div");
        element.classList.add("rio-image");

        this.imageElement = document.createElement("img");
        this.imageElement.role = "img";
        // Dragging prevents pointer events and is annoying in general, so
        // we'll disable that.
        this.imageElement.draggable = false;
        element.appendChild(this.imageElement);

        this.imageElement.onload = this._onLoad.bind(this);
        this.imageElement.onerror = this._onError.bind(this);

        this.resizeObserver = new ResizeObserver(this._updateSize.bind(this));
        this.resizeObserver.observe(element);

        return element;
    }

    onDestruction(): void {
        this.resizeObserver.disconnect();
    }

    updateElement(
        deltaState: DeltaState<ImageState>,
        context: ComponentStatesUpdateContext
    ): void {
        super.updateElement(deltaState, context);

        if (
            deltaState.imageUrl !== undefined &&
            this.imageElement.src !== deltaState.imageUrl
        ) {
            this.element.classList.add("rio-loading");

            this.imageElement.src = deltaState.imageUrl;

            // If we're currently displaying an error icon, remove it
            if (this.element.firstElementChild !== this.imageElement) {
                this.element.firstElementChild!.remove();
                this.element.appendChild(this.imageElement);
            }
        }

        if (deltaState.fill_mode !== undefined) {
            this.imageElement.style.objectFit =
                FILL_MODE_TO_OBJECT_FIT[deltaState.fill_mode];

            this._updateSize();
        }

        if (deltaState.corner_radius !== undefined) {
            let [topLeft, topRight, bottomRight, bottomLeft] =
                deltaState.corner_radius;

            this.imageElement.style.borderRadius = `${topLeft}rem ${topRight}rem ${bottomRight}rem ${bottomLeft}rem`;
        }

        if (deltaState.accessibility_description !== undefined) {
            this.imageElement.alt = deltaState.accessibility_description;
        }
    }

    private _onLoad(): void {
        this.element.classList.remove("rio-loading");
        this._updateSize();
    }

    private _updateSize(): void {
        if (this.element.classList.contains("rio-loading")) {
            // While loading a new image, the size is set to 100%
            this.imageElement.style.removeProperty("width");
            this.imageElement.style.removeProperty("height");
            return;
        }

        // We need to resize the `<img>` element to the size of the image,
        // because:
        // 1. It ensures that `corner_radius` is always visible, even if too
        //    much space has been allocated
        // 2. Browsers are dumb and render content outside of the SVG viewbox if
        //    the <img> element is too large
        if (this.state.fill_mode === "fit") {
            let allocatedWidth = getAllocatedWidthInPx(this.element);
            let allocatedHeight = getAllocatedHeightInPx(this.element);

            let aspectRatioAvailable = allocatedWidth / allocatedHeight;
            let aspectRatioImage =
                this.imageElement.naturalWidth /
                this.imageElement.naturalHeight;

            let scaleFactor =
                aspectRatioAvailable > aspectRatioImage
                    ? allocatedHeight / this.imageElement.naturalHeight
                    : allocatedWidth / this.imageElement.naturalWidth;

            let imgWidth = Math.round(
                this.imageElement.naturalWidth * scaleFactor
            );
            let imgHeight = Math.round(
                this.imageElement.naturalHeight * scaleFactor
            );

            this.imageElement.style.width = `${imgWidth}px`;
            this.imageElement.style.height = `${imgHeight}px`;
        } else {
            this.imageElement.style.width = "100%";
            this.imageElement.style.height = "100%";
        }
    }

    private _onError(event: string | Event): void {
        applyIcon(this.element, "material/broken_image");

        this.sendMessageToBackend({
            type: "onError",
        });
    }
}
