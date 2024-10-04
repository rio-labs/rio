import { applyIcon } from "../designApplication";
import { ComponentBase, ComponentState } from "./componentBase";

const FILL_MODE_TO_OBJECT_FIT = {
    fit: "contain",
    stretch: "fill",
    zoom: "cover",
} as const;

export type ImageState = ComponentState & {
    _type_: "Image-builtin";
    fill_mode?: keyof typeof FILL_MODE_TO_OBJECT_FIT;
    imageUrl?: string;
    reportError?: boolean;
    corner_radius?: [number, number, number, number];
    accessibility_description?: string;
};

export class ImageComponent extends ComponentBase {
    declare state: Required<ImageState>;

    private imageElement: HTMLImageElement;
    private resizeObserver: ResizeObserver;

    createElement(): HTMLElement {
        let element = document.createElement("div");
        element.classList.add("rio-image");

        this.imageElement = document.createElement("img");
        this.imageElement.role = "img";
        // Dragging prevents pointerups and is annoying in general, so we'll
        // disable it
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
        deltaState: ImageState,
        latentComponents: Set<ComponentBase>
    ): void {
        super.updateElement(deltaState, latentComponents);

        let imgElement = this.imageElement;

        if (
            deltaState.imageUrl !== undefined &&
            imgElement.src !== deltaState.imageUrl
        ) {
            // this.element.classList.add('rio-content-loading');
            imgElement.src = deltaState.imageUrl;

            // Until the image is loaded and we get access to its resolution,
            // let it fill the entire space. This is the correct size for all
            // `fill_mode`s except `"fit"` anyway, so there's no harm in setting
            // it now rather than later. (SVGs might temporarily render content
            // outside of the viewbox, but the only way to prevent that would be
            // to make the image invisible until loaded.)
            this.imageElement.style.width = "100%";
            this.imageElement.style.height = "100%";

            // If we're currently displaying an error icon, remove it
            if (this.element.firstElementChild !== imgElement) {
                this.element.firstElementChild!.remove();
                this.element.appendChild(imgElement);
            }
        }

        if (deltaState.fill_mode !== undefined) {
            imgElement.style.objectFit =
                FILL_MODE_TO_OBJECT_FIT[deltaState.fill_mode];

            this._updateSize();
        }

        if (deltaState.corner_radius !== undefined) {
            let [topLeft, topRight, bottomRight, bottomLeft] =
                deltaState.corner_radius;

            imgElement.style.borderRadius = `${topLeft}rem ${topRight}rem ${bottomRight}rem ${bottomLeft}rem`;
        }

        if (deltaState.accessibility_description !== undefined) {
            imgElement.alt = deltaState.accessibility_description;
        }
    }

    private _onLoad(): void {
        // this.element.classList.remove('rio-content-loading');
        this._updateSize();
    }

    private _updateSize(): void {
        // We need to resize the `<img>` element to the size of the image,
        // because:
        // 1. It ensures that `corner_radius` is always visible, even if too
        //    much space has been allocated
        // 2. Browsers are dumb and render content outside of the SVG viewbox if
        //    the <img> element is too large
        if (this.state.fill_mode === "fit") {
            let rect = this.element.getBoundingClientRect();
            let aspectRatioAvailable = rect.width / rect.height;
            let aspectRatioImage =
                this.imageElement.naturalWidth /
                this.imageElement.naturalHeight;

            let scaleFactor =
                aspectRatioAvailable > aspectRatioImage
                    ? rect.height / this.imageElement.naturalHeight
                    : rect.width / this.imageElement.naturalWidth;

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
        this.element.classList.remove("rio-content-loading");

        applyIcon(this.element, "material/broken_image");

        this.sendMessageToBackend({
            type: "onError",
        });
    }
}
