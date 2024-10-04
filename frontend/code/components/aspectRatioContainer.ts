import { ComponentBase, ComponentState } from "./componentBase";
import { ComponentId } from "../dataModels";
import { getNaturalSizeInPixels } from "../utils";

export type AspectRatioContainerState = ComponentState & {
    _type_: "AspectRatioContainer-builtin";
    content?: ComponentId;
    aspect_ratio: number;
};

export class AspectRatioContainerComponent extends ComponentBase {
    declare state: Required<AspectRatioContainerState>;

    private innerElement: HTMLElement;
    private childContainer: HTMLElement;

    private parentResizeObserver: ResizeObserver;
    private childResizeObserver: ResizeObserver;

    createElement(): HTMLElement {
        let element = document.createElement("div");
        element.classList.add("rio-aspect-ratio-container");

        // Add a second element to apply the child's size to
        this.innerElement = document.createElement("div");
        element.appendChild(this.innerElement);

        // Add a child container
        this.childContainer = document.createElement("div");
        this.childContainer.classList.add(
            "rio-aspect-ratio-container-child-container"
        );
        this.innerElement.appendChild(this.childContainer);

        // Listen for changes
        this.parentResizeObserver = new ResizeObserver(
            this.onParentResize.bind(this)
        );
        this.parentResizeObserver.observe(element);

        this.childResizeObserver = new ResizeObserver(
            this.onParentResize.bind(this)
        );
        this.childResizeObserver.observe(this.childContainer);

        return element;
    }

    onDestruction(): void {
        super.onDestruction();

        this.parentResizeObserver.disconnect();
        this.childResizeObserver.disconnect();
    }

    updateElement(
        deltaState: AspectRatioContainerState,
        latentComponents: Set<ComponentBase>
    ): void {
        super.updateElement(deltaState, latentComponents);

        if (deltaState.content !== undefined) {
            this.replaceOnlyChild(
                latentComponents,
                deltaState.content,
                this.childContainer
            );
        }

        if (deltaState.aspect_ratio !== undefined) {
            this.childContainer.style.aspectRatio =
                deltaState.aspect_ratio.toString();
        }
    }

    onParentResize(): void {
        // Get the parent's and child's dimensions
        let parentRect = this.element.getBoundingClientRect();
        let parentAspectRatio = parentRect.width / parentRect.height;

        // Update the child's dimensions
        if (parentAspectRatio > this.state.aspect_ratio) {
            this.childContainer.style.width = "auto";
            this.childContainer.style.height = "100%";

            this.childContainer.style.left = "50%";
            this.childContainer.style.top = "0";
            this.childContainer.style.transform = "translateX(-50%)";
        } else {
            this.childContainer.style.width = "100%";
            this.childContainer.style.height = "auto";

            this.childContainer.style.left = "0";
            this.childContainer.style.top = "50%";
            this.childContainer.style.transform = "translateY(-50%)";
        }
    }

    onChildResize(): void {
        let childElement = this.innerElement.firstElementChild as HTMLElement;
        let childNaturalSize = getNaturalSizeInPixels(childElement);
        this.innerElement.style.minWidth = `${childNaturalSize[0]}px`;
        this.innerElement.style.minHeight = `${childNaturalSize[1]}px`;
    }
}
