import { pixelsPerRem } from "../app";
import { ComponentBase, ComponentState, DeltaState } from "./componentBase";
import { DragHandler } from "../eventHandling";
import { tryGetComponentByElement } from "../componentManagement";
import { ComponentId } from "../dataModels";
import { findComponentUnderMouse } from "../utils";

export type PointerEventListenerState = ComponentState & {
    _type_: "PointerEventListener-builtin";
    content: ComponentId;
    reportPress: boolean;
    reportPointerDown: boolean;
    reportPointerUp: boolean;
    reportPointerMove: boolean;
    reportPointerEnter: boolean;
    reportPointerLeave: boolean;
    reportDragStart: boolean;
    reportDragMove: boolean;
    reportDragEnd: boolean;
};

export class PointerEventListenerComponent extends ComponentBase<PointerEventListenerState> {
    private _dragHandler: DragHandler | null = null;

    createElement(): HTMLElement {
        let element = document.createElement("div");
        element.classList.add("rio-pointer-event-listener");
        return element;
    }

    updateElement(
        deltaState: DeltaState<PointerEventListenerState>,
        latentComponents: Set<ComponentBase>
    ): void {
        super.updateElement(deltaState, latentComponents);

        this.replaceOnlyChild(latentComponents, deltaState.content);

        if (deltaState.reportPress) {
            this.element.onclick = (e) => {
                this._sendEventToBackend("press", e as PointerEvent, false);
            };
        } else {
            this.element.onclick = null;
        }

        if (deltaState.reportPointerDown) {
            this.element.onpointerdown = (e) => {
                this._sendEventToBackend("pointerDown", e, false);
            };
        } else {
            this.element.onpointerdown = null;
        }

        if (deltaState.reportPointerUp) {
            this.element.onpointerup = (e) => {
                this._sendEventToBackend("pointerUp", e, false);
            };
        } else {
            this.element.onpointerup = null;
        }

        if (deltaState.reportPointerMove) {
            this.element.onpointermove = (e) => {
                this._sendEventToBackend("pointerMove", e, true);
            };
        } else {
            this.element.onpointermove = null;
        }

        if (deltaState.reportPointerEnter) {
            this.element.onpointerenter = (e) => {
                this._sendEventToBackend("pointerEnter", e, false);
            };
        } else {
            this.element.onpointerenter = null;
        }

        if (deltaState.reportPointerLeave) {
            this.element.onpointerleave = (e) => {
                this._sendEventToBackend("pointerLeave", e, false);
            };
        } else {
            this.element.onpointerleave = null;
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

    private _onDragStart(event: PointerEvent): boolean {
        // Drag handlers prevent pointer downs from being detected. Manually
        // report them here
        if (this.state.reportPointerDown) {
            this._sendEventToBackend("pointerDown", event, false);
        }

        // Report the drag start event
        if (this.state.reportDragStart) {
            this._sendEventToBackend("dragStart", event, false);
        }
        return true;
    }

    private _onDragMove(event: PointerEvent): void {
        if (this.state.reportDragMove) {
            this._sendEventToBackend("dragMove", event, true);
        }
    }

    private _onDragEnd(event: PointerEvent): void {
        if (this.state.reportDragEnd) {
            this._sendEventToBackend("dragEnd", event, false);
        }
    }

    /// Serializes a pointer event to the format expected by Python.
    ///
    /// Not all types of events are supported on the Python side. For example, pen
    /// input isn't currently handled. If this particular event isn't supported,
    /// returns `null`.
    serializePointerEvent(event: PointerEvent): object | null {
        // Convert the pointer type
        //
        // Some browsers (e.g. Safari) sometimes have `undefined` as the pointer
        // type. This can lead to important events being dropped. In this case,
        // we guess the pointer type from whether the device is using a
        // touchscreen as the primary input device.
        let pointerType = event.pointerType;

        if (pointerType === undefined) {
            let hasTouchscreen = window.matchMedia("(pointer: coarse)").matches;
            pointerType = hasTouchscreen ? "touch" : "mouse";
        } else if (
            event.pointerType !== "mouse" &&
            event.pointerType !== "touch"
        ) {
            return null;
        }

        // Convert the button
        if (event.button < -1 || event.button > 2) {
            return null;
        }
        let button = [null, "left", "middle", "right"][event.button + 1];

        // Get the event positions
        let elementRect = this.element.getBoundingClientRect();

        let windowX = event.clientX / pixelsPerRem;
        let windowY = event.clientY / pixelsPerRem;

        let componentX = windowX - elementRect.left / pixelsPerRem;
        let componentY = windowY - elementRect.top / pixelsPerRem;

        // Build the result
        return {
            pointerType: pointerType,
            button: button,
            windowX: windowX,
            windowY: windowY,
            componentX: componentX,
            componentY: componentY,
        };
    }

    /// Serializes a pointer event to the format expected by Python. Follows the
    /// same semantics as `serializePointerEvent`.
    serializePointerMoveEvent(event: PointerEvent): object | null {
        // Serialize this as a pointer event
        let result = this.serializePointerEvent(event);

        // Did the serialization succeed?
        if (result === null) {
            return null;
        }

        // Add the relative position
        result["relativeX"] = event.movementX / pixelsPerRem;
        result["relativeY"] = event.movementY / pixelsPerRem;

        // Done
        return result;
    }

    /// Serializes the given event and sends it to the backend. If this type of
    /// event isn't supported by the backend (e.g. pen inputs), does nothing.
    private _sendEventToBackend(
        eventType: string,
        event: PointerEvent,
        asMoveEvent: boolean
    ): void {
        // Serialize the event
        let serialized: object | null;

        if (asMoveEvent) {
            serialized = this.serializePointerMoveEvent(event);
        } else {
            serialized = this.serializePointerEvent(event);
        }

        // Did the serialization succeed?
        if (serialized === null) {
            return;
        }

        // Send the event
        this.sendMessageToBackend({
            type: eventType,
            ...serialized,
        });
    }
}
