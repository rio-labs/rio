import { componentsById } from '../componentManagement';
import { ComponentId } from '../dataModels';
import { ComponentBase, ComponentState } from './componentBase';

export type LinearContainerState = ComponentState & {
    _type_: 'Row-builtin' | 'Column-builtin' | 'ListView-builtin';
    children?: ComponentId[];
    spacing?: number;
    proportions?: 'homogeneous' | number[] | null;
};

abstract class LinearContainer extends ComponentBase {
    state: Required<LinearContainerState>;

    protected nGrowers: number; // Number of children that grow in the major axis
    protected totalProportions: number; // Sum of all proportions, if there are proportions

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

            this.updateChildFlexes(deltaState.children);
        }

        // Spacing
        if (deltaState.spacing !== undefined) {
            this.element.style.gap = `${deltaState.spacing}rem`;
        }

        // Proportions
        if (
            deltaState.proportions === undefined ||
            deltaState.proportions === null
        ) {
        } else if (deltaState.proportions === 'homogeneous') {
            throw new Error('not implemented yet');
        } else {
            throw new Error('not implemented yet');
        }
    }

    onChildGrowChanged(): void {
        this.updateChildFlexes(this.state.children);
    }

    private updateChildFlexes(children: ComponentId[]): void {
        // Set the children's `flex-grow`
        let hasGrowers = false;
        for (let [index, childId] of children.entries()) {
            let childComponent = componentsById[childId]!;
            let childWrapper = this.element.children[index] as HTMLElement;

            if (this.getGrow(childComponent)) {
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

    /// Returns whether the given component grows in the direction of the
    /// container
    abstract getGrow(childComponent: ComponentBase): boolean;
}

export class RowComponent extends LinearContainer {
    getGrow(childComponent: ComponentBase): boolean {
        return childComponent.state._grow_[0];
    }
}

export class ColumnComponent extends LinearContainer {
    createElement(): HTMLElement {
        let element = super.createElement();
        element.classList.add('rio-column');
        return element;
    }

    getGrow(childComponent: ComponentBase): boolean {
        return childComponent.state._grow_[1];
    }
}
