import { componentsById } from '../componentManagement';
import { ComponentId } from '../dataModels';
import { getNaturalSizeInPixels } from '../utils';
import { ComponentBase, ComponentState } from './componentBase';

export type LinearContainerState = ComponentState & {
    _type_: 'Row-builtin' | 'Column-builtin' | 'ListView-builtin';
    children?: ComponentId[];
    spacing?: number;
    proportions?: 'homogeneous' | number[] | null;
};

export abstract class LinearContainer extends ComponentBase {
    state: Required<LinearContainerState>;

    index = -1; // 0 for Rows, 1 for Columns

    createElement(): HTMLElement {
        let element = document.createElement('div');
        element.classList.add('rio-linear-child-container');

        return element;
    }

    updateElement(
        deltaState: LinearContainerState,
        latentComponents: Set<ComponentBase>
    ): void {
        super.updateElement(deltaState, latentComponents);

        // Children
        if (deltaState.children !== undefined) {
            this.replaceChildren(
                latentComponents,
                deltaState.children,
                this.element,
                true
            );
        }

        // Spacing
        if (deltaState.spacing !== undefined) {
            this.element.style.gap = `${deltaState.spacing}rem`;
        }

        // Update the CSS depending on whether we have proportions or not
        Object.assign(this.state, deltaState);
        this.updateCSS();
    }

    onChildGrowChanged(): void {
        this.updateCSS();
    }

    private updateCSS(): void {
        if (this.state.proportions === null) {
            this.updateChildGrows();
        } else {
            this.updateProportions();
        }
    }

    private updateChildGrows(): void {
        // Set the children's `flex-grow`
        let hasGrowers = false;
        for (let [index, childId] of this.state.children.entries()) {
            let childComponent = componentsById[childId]!;
            let childWrapper = this.element.children[index] as HTMLElement;

            if (childComponent.state._grow_[this.index]) {
                hasGrowers = true;
                childWrapper.style.flexGrow = '1';
            } else {
                childWrapper.style.flexGrow = '0';
            }
        }

        // If nobody wants to grow, all of them do
        if (!hasGrowers) {
            for (let childWrapper of this.element.children) {
                (childWrapper as HTMLElement).style.flexGrow = '1';
            }
        }
    }

    private updateProportions(): void {
        let proportions: number[] =
            this.state.proportions === 'homogeneous'
                ? new Array(this.children.size).fill(1)
                : this.state.proportions!;

        let naturalSizes = this.state.children.map(
            (childId) =>
                getNaturalSizeInPixels(componentsById[childId]!.outerElement)[
                    this.index
                ]
        );
    }
}

export class RowComponent extends LinearContainer {
    index = 0;
}

export class ColumnComponent extends LinearContainer {
    index = 1;

    createElement(): HTMLElement {
        let element = super.createElement();
        element.classList.add('rio-column');
        return element;
    }
}
