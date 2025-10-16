import { pixelsPerRem } from "../app";
import { ComponentBase, ComponentState, DeltaState } from "./componentBase";
import { DragHandler } from "../eventHandling";
import { ComponentId } from "../dataModels";
import { findComponentUnderMouse } from "../utils";
import { ComponentStatesUpdateContext } from "../componentManagement";

function eventMouseButtonToString(event: MouseEvent): object {
    return {
        button: ["left", "middle", "right"][event.button],
    };
}

function eventMousePositionToString(event: MouseEvent): object {
    return {
        x: event.clientX / pixelsPerRem,
        y: event.clientY / pixelsPerRem,
    };
}

export type MouseEventListenerState = ComponentState & {
    _type_: "MouseEventListener-builtin";
    content: ComponentId;
    reportPress: boolean;
    reportMouseDown: boolean;
    reportMouseUp: boolean;
    reportMouseMove: boolean;
    reportMouseEnter: boolean;
    reportMouseLeave: boolean;
    reportDragStart: boolean;
    reportDragMove: boolean;
    reportDragEnd: boolean;
};

export class MouseEventListenerComponent extends ComponentBase<MouseEventListenerState> {
    private _dragHandler: DragHandler | null = null;

    createElement(context: ComponentStatesUpdateContext): HTMLElement {
        let element = document.createElement("div");
        element.classList.add("rio-pointer-event-listener");
        return element;
    }

    updateElement(
        deltaState: DeltaState<MouseEventListenerState>,
        context: ComponentStatesUpdateContext
    ): void {
        super.updateElement(deltaState, context);

        this.replaceOnlyChild(context, deltaState.content);

        if (deltaState.reportPress) {
            this.element.onclick = (e) => {
                this.sendMessageToBackend({
                    type: "press",
                    ...eventMouseButtonToString(e),
                    ...eventMousePositionToString(e),
                });
            };
        } else {
            this.element.onclick = null;
        }

        if (deltaState.reportMouseDown) {
            this.element.onmousedown = (e) => {
                this.sendMessageToBackend({
                    type: "mouseDown",
                    ...eventMouseButtonToString(e),
                    ...eventMousePositionToString(e),
                });
            };
        } else {
            this.element.onmousedown = null;
        }

        if (deltaState.reportMouseUp) {
            this.element.onmouseup = (e) => {
                this.sendMessageToBackend({
                    type: "mouseUp",
                    ...eventMouseButtonToString(e),
                    ...eventMousePositionToString(e),
                });
            };
        } else {
            this.element.onmouseup = null;
        }

        if (deltaState.reportMouseMove) {
            this.element.onmousemove = (e) => {
                this.sendMessageToBackend({
                    type: "mouseMove",
                    ...eventMousePositionToString(e),
                });
            };
        } else {
            this.element.onmousemove = null;
        }

        if (deltaState.reportMouseEnter) {
            this.element.onmouseenter = (e) => {
                this.sendMessageToBackend({
                    type: "mouseEnter",
                    ...eventMousePositionToString(e),
                });
            };
        } else {
            this.element.onmouseenter = null;
        }

        if (deltaState.reportMouseLeave) {
            this.element.onmouseleave = (e) => {
                this.sendMessageToBackend({
                    type: "mouseLeave",
                    ...eventMousePositionToString(e),
                });
            };
        } else {
            this.element.onmouseleave = null;
        }

        if (
            deltaState.reportDragStart ||
            deltaState.reportDragMove ||
            deltaState.reportDragEnd
        ) {
            if (this._dragHandler === null) {
                this._dragHandler = this.addDragHandler({
                    element: this.element,
                    onStart: this._onDragStart.bind(this),
                    onMove: this._onDragMove.bind(this),
                    onEnd: this._onDragEnd.bind(this),
                });
            }
        } else {
            if (this._dragHandler !== null) {
                this._dragHandler.disconnect();
                this._dragHandler = null;
            }
        }
    }

    private _onDragStart(event: MouseEvent): boolean {
        if (this.state.reportDragStart) {
            this._sendDragEvent("dragStart", event);
        }
        return true;
    }

    private _onDragMove(event: MouseEvent): void {
        if (this.state.reportDragMove) {
            this._sendDragEvent("dragMove", event);
        }
    }

    private _onDragEnd(event: MouseEvent): void {
        if (this.state.reportDragEnd) {
            this._sendDragEvent("dragEnd", event);
        }
    }

    private _sendDragEvent(eventType: string, event: MouseEvent): void {
        this.sendMessageToBackend({
            type: eventType,
            ...eventMouseButtonToString(event),
            x: event.clientX / pixelsPerRem,
            y: event.clientY / pixelsPerRem,
            component: findComponentUnderMouse(event),
        });
    }
}
