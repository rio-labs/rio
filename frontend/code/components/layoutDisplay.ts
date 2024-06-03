import { ComponentBase, ComponentState } from './componentBase';
import { LayoutContext } from '../layouting';
import { componentsById } from '../componentManagement';
import { pixelsPerRem } from '../app';

export type LayoutDisplayState = ComponentState & {
    _type_: 'LayoutDisplay-builtin';
    component_id: number;
};

export class LayoutDisplayComponent extends ComponentBase {
    state: Required<LayoutDisplayState>;

    // Just quick references for convenience
    targetComponent: ComponentBase;

    // Represents the target component's parent. It matches the aspect ratio of
    // the parent and is centered within this component.
    parentElement: HTMLElement;

    // Represents the target component's margin.
    marginElement: HTMLElement;

    // Represents the target component itself.
    targetElement: HTMLElement;

    createElement(): HTMLElement {
        let element = document.createElement('div');
        element.classList.add('rio-layout-display');

        this.parentElement = document.createElement('div');
        this.parentElement.classList.add('rio-layout-display-parent');
        element.appendChild(this.parentElement);

        this.marginElement = document.createElement('div');
        this.marginElement.classList.add('rio-layout-display-margin');
        this.parentElement.appendChild(this.marginElement);

        this.targetElement = document.createElement('div');
        this.targetElement.classList.add('rio-layout-display-target');
        this.parentElement.appendChild(this.targetElement);

        return element;
    }

    updateElement(
        deltaState: LayoutDisplayState,
        latentComponents: Set<ComponentBase>
    ): void {
        // Has the target component changed?
        if (deltaState.component_id !== undefined) {
            // Store a reference to the component and its parent
            this.targetComponent = componentsById[deltaState.component_id];

            // Label the target
            this.targetElement.innerText =
                this.targetComponent.state._python_type_;

            // Trigger a re-layout
            this.makeLayoutDirty();
        }
    }

    updateNaturalHeight(ctx: LayoutContext): void {
        // This component doesn't particularly care about its size. However, it
        // would be nice to have the correct aspect ratio.
        //
        // It's probably not remotely legal to access the natural width of
        // another component during layouting, but what the heck. This doesn't
        // do anything other than _attempting_ to get the correct aspect ratio.
        // Without this we're guaranteed to get a wrong one.
        let parentComponent =
            this.targetComponent.getParentExcludingInjected()!;

        if (parentComponent.allocatedWidth === 0) {
            this.naturalHeight = 0;
        } else {
            this.naturalHeight =
                (this.allocatedWidth * parentComponent.allocatedHeight) /
                parentComponent.allocatedWidth;
        }
    }

    updateAllocatedHeight(ctx: LayoutContext): void {
        // Let the code below assume that we have a reasonable size
        if (this.allocatedWidth === 0 || this.allocatedHeight === 0) {
            return;
        }

        setTimeout(() => {
            this.updateContent();
        }, 0);
    }

    updateContent(): void {
        // Decide on a scale. Display everything as large as possible, while
        // fitting it into the allocated space and without distorting the aspect
        // ratio.
        let parentComponent =
            this.targetComponent.getParentExcludingInjected()!;

        let scaleX = this.allocatedWidth / parentComponent.allocatedWidth;
        let scaleY = this.allocatedHeight / parentComponent.allocatedHeight;
        let scaleRem: number, scalePer: number;

        if (scaleX < scaleY) {
            scaleRem = scaleX;
            scalePer = (scaleX / this.allocatedWidth) * 100;
        } else {
            scaleRem = scaleY;
            scalePer = (scaleY / this.allocatedHeight) * 100;
        }

        // Resize the parent representation
        this.parentElement.style.width = `${
            parentComponent.allocatedWidth * scaleRem
        }rem`;
        this.parentElement.style.height = `${
            parentComponent.allocatedHeight * scaleRem
        }rem`;

        // Position the target
        let parentRect = parentComponent.element.getBoundingClientRect();
        let targetRect = this.targetComponent.element.getBoundingClientRect();

        let targetLeft = (targetRect.left - parentRect.left) / pixelsPerRem;
        let targetTop = (targetRect.top - parentRect.top) / pixelsPerRem;

        this.targetElement.style.left = `${targetLeft * scalePer}%`;
        this.targetElement.style.top = `${targetTop * scalePer}%`;

        // Size the target
        this.targetElement.style.width = `${
            this.targetComponent.allocatedWidth * scalePer
        }%`;
        this.targetElement.style.height = `${
            this.targetComponent.allocatedHeight * scalePer
        }%`;

        // Position the margin
        let margins = this.targetComponent.state._margin_;

        let marginLeft = targetLeft - margins[0];
        let marginTop = targetTop - margins[1];

        this.marginElement.style.left = `${marginLeft * scalePer}%`;
        this.marginElement.style.top = `${marginTop * scalePer}%`;

        // Size the margin
        this.marginElement.style.width = `${
            (this.targetComponent.allocatedWidth + margins[0] + margins[2]) *
            scalePer
        }%`;

        this.marginElement.style.height = `${
            (this.targetComponent.allocatedHeight + margins[1] + margins[3]) *
            scalePer
        }%`;
    }
}
