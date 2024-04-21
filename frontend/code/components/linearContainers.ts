import { pixelsPerRem } from '../app';
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

    protected childContainer: HTMLElement;
    protected undef1: HTMLElement;
    protected undef2: HTMLElement;

    protected nGrowers: number; // Number of children that grow in the major axis
    protected totalProportions: number; // Sum of all proportions, if there are proportions

    createElement(): HTMLElement {
        let element = document.createElement('div');

        this.undef1 = document.createElement('div');
        this.undef1.classList.add('rio-undefined-space');
        element.appendChild(this.undef1);

        this.childContainer = document.createElement('div');
        this.childContainer.classList.add('rio-linear-child-container');
        element.appendChild(this.childContainer);

        this.undef2 = document.createElement('div');
        this.undef2.classList.add('rio-undefined-space');
        element.appendChild(this.undef2);

        if (globalThis.RIO_DEBUG_MODE) {
            let undefinedSpaceMessage =
                `This ${this.state._python_type_} is` +
                ` larger than its content, so it's unclear how the content` +
                ` should be positioned. You can fix this by giving the` +
                ` component an alignment.`;

            for (let elem of [this.undef1, this.undef2]) {
                elem.title = undefinedSpaceMessage;
                elem.style.pointerEvents = 'auto';
            }
        }

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
                this.childContainer
            );

            // Clear everybody's position
            for (let childElement of this.childContainer
                .children as Iterable<HTMLElement>) {
                childElement.style.left = '0';
                childElement.style.top = '0';
            }
        }

        // Spacing
        if (deltaState.spacing !== undefined) {
            this.childContainer.style.gap = `${deltaState.spacing}rem`;
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
    createElement(): HTMLElement {
        let element = super.createElement();
        element.classList.add('rio-row');
        return element;
    }

    updateNaturalWidth(ctx: LayoutContext): void {
        if (this.state.proportions === null) {
            this.naturalWidth = 0;
            this.nGrowers = 0;

            // Add up all children's requested widths
            for (let child of this.children) {
                this.naturalWidth += child.requestedWidth;
                this.nGrowers += child.state['_grow_'][0] as any as number;
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
            let additionalSpace = this.allocatedWidth - this.naturalWidth;
            let additionalSpacePerGrower =
                this.nGrowers === 0 ? 0 : additionalSpace / this.nGrowers;

            for (let child of this.children) {
                child.allocatedWidth = child.requestedWidth;

                if (child.state['_grow_'][0]) {
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
        // Is all allocated space used? Highlight any undefined space
        let additionalSpace = this.allocatedWidth - this.naturalWidth;

        if (this.nGrowers > 0 || Math.abs(additionalSpace) < 1e-6) {
            this.undef1.style.flexGrow = '0';
            this.undef2.style.flexGrow = '0';
            this.undef1.classList.remove('rio-undefined-space');
            this.undef2.classList.remove('rio-undefined-space');
        } else {
            // If there is no child elements make a single undefined space take
            // up everything. This way there is no unsightly disconnect between
            // the two.
            let element = this.element;

            if (element.children.length === 0) {
                this.undef1.style.flexGrow = '1';
                this.undef2.style.flexGrow = '0';
            } else {
                this.undef1.style.flexGrow = '1';
                this.undef2.style.flexGrow = '1';
            }

            console.log(
                `Warning: Component #${this.id} has ${
                    additionalSpace * pixelsPerRem
                }px of unused horizontal space`
            );

            // Since the undefined space is animated, it takes up a fair amount
            // of CPU time - even though it's not visible. Only apply the
            // animation if the component is visible.
            this.undef1.classList.add('rio-undefined-space');
            this.undef2.classList.add('rio-undefined-space');
        }

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
                this.nGrowers += child.state['_grow_'][1] as any as number;
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
        if (this.state.proportions === null) {
            // Is all allocated space used? Highlight any undefined space
            let additionalSpace = this.allocatedHeight - this.naturalHeight;

            if (this.nGrowers > 0 || Math.abs(additionalSpace) < 1e-6) {
                this.undef1.style.flexGrow = '0';
                this.undef2.style.flexGrow = '0';
                this.undef1.classList.remove('rio-undefined-space');
                this.undef2.classList.remove('rio-undefined-space');
            } else {
                // If there is no child elements make a single undefined space take
                // up everything. This way there is no unsightly disconnect between
                // the two.
                let element = this.element;

                if (element.children.length === 0) {
                    this.undef1.style.flexGrow = '1';
                    this.undef2.style.flexGrow = '0';
                } else {
                    this.undef1.style.flexGrow = '1';
                    this.undef2.style.flexGrow = '1';
                }

                console.log(
                    `Warning: Component #${this.id} has ${
                        additionalSpace * pixelsPerRem
                    }px of unused vertical space`
                );

                // Since the undefined space is animated, it takes up a fair amount
                // of CPU time - even though it's not visible. Only apply the
                // animation if the component is visible.
                this.undef1.classList.add('rio-undefined-space');
                this.undef2.classList.add('rio-undefined-space');
            }

            // Assign the allocated height to the children
            let children = this.children;
            let additionalSpacePerGrower =
                this.nGrowers === 0 ? 0 : additionalSpace / this.nGrowers;

            for (let child of children) {
                child.allocatedHeight = child.requestedHeight;

                if (child.state['_grow_'][1]) {
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
