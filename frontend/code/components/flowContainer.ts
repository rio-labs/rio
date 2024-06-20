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

        // Update the children
        this.replaceChildren(latentComponents, deltaState.children);
    }

    private processRow(row: ComponentBase[], rowWidth: number): void {
        // Determine how to use the additional space
        let spaceToTheLeft, spaceToGrow, spaceForGap;
        let additionalWidth = this.allocatedWidth - rowWidth;

        if (this.state.justify === 'left') {
            spaceToTheLeft = 0;
            spaceToGrow = 0;
            spaceForGap = 0;
        } else if (this.state.justify === 'center') {
            spaceToTheLeft = additionalWidth * 0.5;
            spaceToGrow = 0;
            spaceForGap = 0;
        } else if (this.state.justify === 'right') {
            spaceToTheLeft = additionalWidth;
            spaceToGrow = 0;
            spaceForGap = 0;
        } else if (this.state.justify === 'justified') {
            if (row.length === 1) {
                spaceToTheLeft = additionalWidth * 0.5;
                spaceToGrow = 0;
                spaceForGap = 0;
            } else {
                spaceToTheLeft = 0;
                spaceToGrow = 0;
                spaceForGap = additionalWidth / (row.length - 1);
            }
        } else {
            // 'grow'
            spaceToTheLeft = 0;
            spaceToGrow = additionalWidth / row.length;
            spaceForGap = spaceToGrow;
        }

        // Assign the positions
        for (let ii = 0; ii < row.length; ii++) {
            let child = row[ii];

            // Assign the position
            let left =
                (child as any)._flowContainer_posX +
                spaceToTheLeft +
                ii * spaceForGap;
            child.element.style.left = `${left}rem`;

            // Assign the width
            child.allocatedWidth = child.requestedWidth + spaceToGrow;
        }
    }
}
