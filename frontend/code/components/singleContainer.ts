import { LayoutContext } from '../layouting';
import { ComponentBase } from './componentBase';

export abstract class SingleContainer extends ComponentBase {
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
        for (let child of this.children) {
            child.allocatedWidth = this.allocatedWidth;
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
        for (let child of this.children) {
            child.allocatedHeight = this.allocatedHeight;

            let element = child.element;
            element.style.left = '0';
            element.style.top = '0';
        }
    }
}
