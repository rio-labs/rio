import { applyIcon } from '../designApplication';
import { ComponentBase, ComponentState } from './componentBase';

const FILL_MODE_TO_OBJECT_FIT = {
    fit: 'contain',
    stretch: 'fill',
    zoom: 'cover',
} as const;

export type ImageState = ComponentState & {
    _type_: 'Image-builtin';
    fill_mode?: keyof typeof FILL_MODE_TO_OBJECT_FIT;
    imageUrl?: string;
    reportError?: boolean;
    corner_radius?: [number, number, number, number];
    accessibility_description?: string;
};

export class ImageComponent extends ComponentBase {
    state: Required<ImageState>;

    private imageElement: HTMLImageElement;

    createElement(): HTMLElement {
        let element = document.createElement('div');
        element.classList.add('rio-image');
        element.role = 'img';

        // Dragging prevents mouseups and is annoying in general, so we'll
        // disable it
        element.draggable = false;

        this.imageElement = document.createElement('img');
        element.appendChild(this.imageElement);

        this.imageElement.onload = () => {
            this.imageElement.classList.remove('rio-content-loading');
        };
        this.imageElement.onerror = this._onError.bind(this);

        return element;
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
            // imgElement.classList.add('rio-content-loading');
            imgElement.src = deltaState.imageUrl;

            // If we're currently displaying an error icon, remove it
            if (this.element.firstElementChild !== imgElement) {
                this.element.firstElementChild!.remove();
                this.element.appendChild(imgElement);
            }
        }

        if (deltaState.fill_mode !== undefined) {
            imgElement.style.objectFit =
                FILL_MODE_TO_OBJECT_FIT[deltaState.fill_mode];
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

    private _onError(event: string | Event): void {
        this.imageElement.classList.remove('rio-content-loading');

        applyIcon(this.element, 'material/broken_image');

        this.sendMessageToBackend({
            type: 'onError',
        });
    }
}
