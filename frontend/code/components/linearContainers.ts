import { componentsById } from '../componentManagement';
import { LayoutContext } from '../layouting';
import { ComponentId } from '../dataModels';
import { ComponentBase, ComponentState } from './componentBase';

export type LinearContainerState = ComponentState & {
    _type_: 'Row-builtin' | 'Column-builtin' | 'ListView-builtin';
    children?: ComponentId[];
    spacing?: number;
    proportions?: 'homogeneous' | number[] | null;
};

class LinearContainer extends ComponentBase {
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
        // Children
        if (deltaState.children !== undefined) {
            this.replaceChildren(
                latentComponents,
                deltaState.children,
                this.element
            );

            // Clear everybody's position
            for (let childElement of this.element
                .children as Iterable<HTMLElement>) {
                childElement.style.left = '0';
                childElement.style.top = '0';
            }
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
            this.totalProportions = this.children.size;
        } else {
            this.totalProportions = deltaState.proportions.reduce(
                (a, b) => a + b
            );
        }

        // Re-layout
        this.makeLayoutDirty();
    }
}

export class RowComponent extends LinearContainer {
    updateNaturalWidth(ctx: LayoutContext): void {
        if (this.state.proportions === null) {
            this.naturalWidth = 0;
            this.nGrowers = 0;

            // Add up all children's requested widths
            for (let child of this.children) {
                this.naturalWidth += child.requestedWidth;
                this.nGrowers += child.state._grow_[0] as any as number;
            }
        } else {
            // When proportions are set, growers are ignored. Extra space is
            // distributed among all children.

            // Each child has a requested width and a proportion number, which
            // essentially "cuts" the child into a certain number of equally
            // sized pieces. In order to find our natural width, we need to
            // determine the width of the largest piece, then multiply that by
            // the number of total pieces.
            let proportions =
                this.state.proportions === 'homogeneous'
                    ? Array(this.children.size).fill(1)
                    : this.state.proportions;
            let maxProportionSize = 0;

            for (let i = 0; i < proportions.length; i++) {
                let child = componentsById[this.state.children[i]]!;
                let proportion = proportions[i];

                if (proportion !== 0) {
                    let proportionSize = child.requestedWidth / proportion;

                    maxProportionSize = Math.max(
                        maxProportionSize,
                        proportionSize
                    );
                }
            }

            this.naturalWidth = maxProportionSize * this.totalProportions;
        }

        // Account for spacing
        this.naturalWidth +=
            Math.max(this.children.size - 1, 0) * this.state.spacing;
    }

    updateAllocatedWidth(ctx: LayoutContext): void {
        if (this.state.proportions === null) {
            // If no child wants to grow, we pretend that all of them do.
            let forceGrow = this.nGrowers === 0;
            let nGrowers = forceGrow
                ? this.state.children.length
                : this.nGrowers;

            let additionalSpace = this.allocatedWidth - this.naturalWidth;
            let additionalSpacePerGrower = additionalSpace / nGrowers;

            for (let child of this.children) {
                child.allocatedWidth = child.requestedWidth;

                if (child.state._grow_[0] || forceGrow) {
                    child.allocatedWidth += additionalSpacePerGrower;
                }
            }
        } else {
            let proportions =
                this.state.proportions === 'homogeneous'
                    ? Array(this.children.size).fill(1)
                    : this.state.proportions;

            let spacing =
                Math.max(this.children.size - 1, 0) * this.state.spacing;
            let proportionSize =
                (this.allocatedWidth - spacing) / this.totalProportions;

            for (let i = 0; i < proportions.length; i++) {
                let child = componentsById[this.state.children[i]]!;
                child.allocatedWidth = proportionSize * proportions[i];
            }
        }
    }

    updateNaturalHeight(ctx: LayoutContext): void {
        this.naturalHeight = 0;

        for (let child of this.children) {
            this.naturalHeight = Math.max(
                this.naturalHeight,
                child.requestedHeight
            );
        }
    }

    updateAllocatedHeight(ctx: LayoutContext): void {
        // Assign the allocated height to the children
        for (let child of this.children) {
            child.allocatedHeight = this.allocatedHeight;
        }
    }
}

export class ColumnComponent extends LinearContainer {
    createElement(): HTMLElement {
        let element = super.createElement();
        element.classList.add('rio-column');
        return element;
    }

    updateNaturalWidth(ctx: LayoutContext): void {
        this.naturalWidth = 0;

        for (let child of this.children) {
            this.naturalWidth = Math.max(
                this.naturalWidth,
                child.requestedWidth
            );
        }
    }

    updateAllocatedWidth(ctx: LayoutContext): void {
        // Assign the allocated width to the children
        for (let child of this.children) {
            child.allocatedWidth = this.allocatedWidth;
        }
    }

    updateNaturalHeight(ctx: LayoutContext): void {
        if (this.state.proportions === null) {
            this.naturalHeight = 0;
            this.nGrowers = 0;

            // Add up all children's requested heights
            for (let child of this.children) {
                this.naturalHeight += child.requestedHeight;
                this.nGrowers += child.state._grow_[1] as any as number;
            }
        } else {
            // When proportions are set, growers are ignored. Extra space is
            // distributed among all children.

            // Each child has a requested width and a proportion number, which
            // essentially "cuts" the child into a certain number of equally
            // sized pieces. In order to find our natural width, we need to
            // determine the width of the largest piece, then multiply that by
            // the number of total pieces.
            let proportions =
                this.state.proportions === 'homogeneous'
                    ? Array(this.children.size).fill(1)
                    : this.state.proportions;
            let maxProportionSize = 0;

            for (let i = 0; i < proportions.length; i++) {
                let child = componentsById[this.state.children[i]]!;
                let proportion = proportions[i];

                if (proportion !== 0) {
                    let proportionSize = child.requestedHeight / proportion;

                    maxProportionSize = Math.max(
                        maxProportionSize,
                        proportionSize
                    );
                }
            }

            this.naturalHeight = maxProportionSize * this.totalProportions;
        }

        // Account for spacing
        this.naturalHeight +=
            Math.max(this.children.size - 1, 0) * this.state.spacing;
    }

    updateAllocatedHeight(ctx: LayoutContext): void {
        // Assign the allocated height to the children
        if (this.state.proportions === null) {
            // If no child wants to grow, we pretend that all of them do.
            let forceGrow = this.nGrowers === 0;
            let nGrowers = forceGrow
                ? this.state.children.length
                : this.nGrowers;

            let additionalSpace = this.allocatedHeight - this.naturalHeight;
            let additionalSpacePerGrower = additionalSpace / nGrowers;

            for (let child of this.children) {
                child.allocatedHeight = child.requestedHeight;

                if (child.state._grow_[1] || forceGrow) {
                    child.allocatedHeight += additionalSpacePerGrower;
                }
            }
        } else {
            let proportions =
                this.state.proportions === 'homogeneous'
                    ? Array(this.children.size).fill(1)
                    : this.state.proportions;

            let spacing =
                Math.max(this.children.size - 1, 0) * this.state.spacing;
            let proportionSize =
                (this.allocatedHeight - spacing) / this.totalProportions;

            for (let i = 0; i < proportions.length; i++) {
                let child = componentsById[this.state.children[i]]!;
                child.allocatedHeight = proportionSize * proportions[i];
            }
        }
    }
}
