import { pixelsPerRem } from "../app";
import { ComponentBase, ComponentState, DeltaState } from "./componentBase";
import { DragHandler, markEventAsHandled } from "../eventHandling";
import { ComponentId } from "../dataModels";
import { ComponentStatesUpdateContext } from "../componentManagement";

type MouseButton = "left" | "middle" | "right";

export type PointerEventListenerState = ComponentState & {
    _type_: "PointerEventListener-builtin";
    content: ComponentId;
    reportPress: boolean;
    reportDoublePress: boolean;
    reportPointerDown: MouseButton[];
    reportPointerUp: MouseButton[];
    reportPointerMove: boolean;
    reportPointerEnter: boolean;
    reportPointerLeave: boolean;
    reportDragStart: boolean;
    reportDragMove: boolean;
    reportDragEnd: boolean;
};

const DOUBLE_CLICK_TIMEOUT = 300;

export class PointerEventListenerComponent extends ComponentBase<PointerEventListenerState> {
    private _dragHandler: DragHandler | null = null;
    private _doubleClickTimeoutByButton: {
        [button: number]: number | undefined;
    } = {};

    createElement(context: ComponentStatesUpdateContext): HTMLElement {
        let element = document.createElement("div");
        element.classList.add("rio-pointer-event-listener");
        return element;
    }

    updateElement(
        deltaState: DeltaState<PointerEventListenerState>,
        context: ComponentStatesUpdateContext
    ): void {
        super.updateElement(deltaState, context);

        this.replaceOnlyChild(context, deltaState.content);

        if (
            deltaState.reportPress !== undefined ||
            deltaState.reportDoublePress !== undefined
        ) {
            let reportPress = deltaState.reportPress ?? this.state.reportPress;
            let reportDoublePress =
                deltaState.reportDoublePress ?? this.state.reportDoublePress;

            if (reportPress || reportDoublePress) {
                this.element.onclick = this._onClick.bind(this);
            } else {
                this.element.onclick = null;
            }
        }

        if (deltaState.reportPointerDown !== undefined) {
            if (deltaState.reportPointerDown.length > 0) {
                this.element.onpointerdown = (e) => {
                    if (eventMatchesButton(e, deltaState.reportPointerDown!)) {
                        this._sendEventToBackend("pointerDown", e, false);
                    }
                };
            } else {
                this.element.onpointerdown = null;
            }
        }

        if (deltaState.reportPointerUp !== undefined) {
            if (deltaState.reportPointerUp.length > 0) {
                this.element.onpointerup = (e) => {
                    if (eventMatchesButton(e, deltaState.reportPointerUp!)) {
                        this._sendEventToBackend("pointerUp", e, false);
                    }
                };
            } else {
                this.element.onpointerup = null;
            }
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

    private _onClick(event: MouseEvent): void {
        // This handler is responsible for both single clicks and double clicks

        // If it's not a left-click, ignore it
        if (event.button !== 0) {
            return;
        }

        // Double click
        if (this.state.reportDoublePress) {
            let timeout = this._doubleClickTimeoutByButton[event.button];

            if (timeout === undefined) {
                // If no timeout is registered, this is the first click.
                // Register a timeout.
                this._doubleClickTimeoutByButton[event.button] =
                    window.setTimeout(() => {
                        // Send a "press" event and clear the timeout so that
                        // the next press starts a new timeout
                        if (this.state.reportPress) {
                            this._sendEventToBackend("press", event, false);
                        }

                        this._doubleClickTimeoutByButton[event.button] =
                            undefined;
                    }, DOUBLE_CLICK_TIMEOUT);
            } else {
                // If a timeout is registered, this is the 2nd click. Cancel
                // the timeout so it doesn't send a "press" event, and send
                // a "doublePress" event.
                clearTimeout(timeout);
                this._doubleClickTimeoutByButton[event.button] = undefined;
                this._sendEventToBackend("doublePress", event, false);
            }

            // We've taken care of both double clicks and single clicks, so
            // don't run the rest of the function.
            return;
        }

        // Single click

        // We know that there's no double click handler for this button, so we
        // can just send a "press" event without worrying about anything else
        if (this.state.reportPress) {
            this._sendEventToBackend("press", event, false);
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
    /// Not all types of events are supported on the Python side. For example,
    /// pen input isn't currently handled. If this particular event isn't
    /// supported, returns `null`.
    serializePointerEvent(event: PointerEvent | MouseEvent): object | null {
        // Convert the pointer type
        //
        // Some browsers (e.g. Safari) sometimes have `undefined` as the pointer
        // type. This can lead to important events being dropped. In this case,
        // we guess the pointer type from whether the device is using a
        // touchscreen as the primary input device.
        let pointerType =
            event instanceof PointerEvent ? event.pointerType : undefined;

        if (pointerType === undefined) {
            let hasTouchscreen = window.matchMedia("(pointer: coarse)").matches;
            pointerType = hasTouchscreen ? "touch" : "mouse";
        } else if (pointerType !== "mouse" && pointerType !== "touch") {
            return null;
        }

        // Convert the button
        if (event.button < -1 || event.button > 2) {
            return null;
        }
        let button = buttonIntToButtonName(event.button);

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
    serializePointerMoveEvent(event: PointerEvent | MouseEvent): object | null {
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
        event: PointerEvent | MouseEvent,
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

        // Mark the event as handled
        markEventAsHandled(event);

        // Send the event
        this.sendMessageToBackend({
            type: eventType,
            ...serialized,
        });
    }
}

function buttonIntToButtonName(button: number): MouseButton | null {
    let buttonName = {
        0: "left",
        1: "middle",
        2: "right",
    }[button] as MouseButton | undefined;

    if (buttonName === undefined) {
        return null;
    }

    return buttonName;
}

function eventMatchesButton(
    event: PointerEvent | MouseEvent,
    buttons: MouseButton[]
): boolean {
    let buttonName = buttonIntToButtonName(event.button);
    if (buttonName === null) {
        return false;
    }

    return buttons.includes(buttonName);
}
