/// A connection that is only connected to a single port, with the other end

import { componentsByElement } from "../../componentManagement";
import { ComponentId } from "../../dataModels";
import { GraphEditorComponent } from "./graphEditor";
import { NodeInputComponent } from "../nodeInput";
import { NodeOutputComponent } from "../nodeOutput";

export class DraggingSelectionStrategy {
    startPointX: number;
    startPointY: number;

    constructor(startPointX: number, startPointY: number) {
        this.startPointX = startPointX;
        this.startPointY = startPointY;
    }

    onDragMove(this_: GraphEditorComponent, event: PointerEvent): void {}
    onDragEnd(this_: GraphEditorComponent, event: PointerEvent): void {}
}
