import { componentsById } from '../componentManagement';
import { ComponentId } from '../dataModels';
import { ComponentBase, ComponentState } from './componentBase';

export type FlowState = ComponentState & {
    _type_: 'FlowContainer-builtin';
    children?: ComponentId[];
    row_spacing?: number;
    column_spacing?: number;
    justify?: 'left' | 'center' | 'right' | 'justified' | 'grow';
};

export class FlowComponent extends ComponentBase {
    state: Required<FlowState>;

    createElement(): HTMLElement {
        let element = document.createElement('div');
        element.classList.add('rio-flow-container');
        return element;
    }

    updateElement(
        deltaState: FlowState,
        latentComponents: Set<ComponentBase>
    ): void {
        super.updateElement(deltaState, latentComponents);

        if (deltaState.row_spacing !== undefined) {
            this.element.style.rowGap = `${deltaState.row_spacing}rem`;
        }

        if (deltaState.column_spacing !== undefined) {
            this.element.style.columnGap = `${deltaState.column_spacing}rem`;
        }

        if (deltaState.justify !== undefined) {
            this.element.style.justifyContent = {
                left: 'start',
                right: 'end',
                center: 'center',
                justified: 'space-between',
                grow: 'stretch',
            }[deltaState.justify];
        }

        if (deltaState.children !== undefined) {
            this.replaceChildren(
                latentComponents,
                deltaState.children,
                this.element,
                true
            );
            this.updateChildGrows(
                deltaState.children,
                deltaState.justify ?? this.state.justify
            );
        }
    }

    onChildGrowChanged(): void {
        this.updateChildGrows(this.state.children, this.state.justify);
    }

    private updateChildGrows(children: ComponentId[], justify: string): void {
        // Set the children's `flex-grow`
        let hasGrowers = false;
        for (let [index, childId] of children.entries()) {
            let childComponent = componentsById[childId]!;
            let childWrapper = this.element.children[index] as HTMLElement;

            if (childComponent.state._grow_[0]) {
                hasGrowers = true;
                childWrapper.style.flexGrow = '1';
            } else {
                childWrapper.style.flexGrow = '0';
            }
        }

        // If nobody wants to grow, all of them do
        if (justify === 'grow' && !hasGrowers) {
            for (let childWrapper of this.element.children) {
                (childWrapper as HTMLElement).style.flexGrow = '1';
            }
        }
    }
}
