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
    consume_events: boolean;
};

const DOUBLE_CLICK_TIMEOUT = 300;

export class PointerEventListenerComponent extends ComponentBase<PointerEventListenerState> {
    private _dragHandler: DragHandler | null = null;
    private _doubleClickTimeoutByButton: {
        [button: number]: number | undefined;
    } = {};
    // Handler references created on-demand where installed
    private _onClickBound: (e: MouseEvent) => void | null = null;
    private _onPointerDownBound: ((e: PointerEvent) => void) | null = null;
    private _onPointerUpBound: ((e: PointerEvent) => void) | null = null;
    private _onPointerMoveBound: ((e: PointerEvent) => void) | null = null;
    private _onPointerEnterBound: ((e: PointerEvent) => void) | null = null;
    private _onPointerLeaveBound: ((e: PointerEvent) => void) | null = null;

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
                if (this._onClickBound === null) {
                    this._onClickBound = this._onClick.bind(this);
                    this.element.addEventListener("click", this._onClickBound, {
                        capture: true,
                    });
                }
            } else {
                if (this._onClickBound !== null) {
                    this.element.removeEventListener(
                        "click",
                        this._onClickBound,
                        { capture: true } as AddEventListenerOptions
                    );
                    this._onClickBound = null;
                }
            }
        }

        if (deltaState.reportPointerDown !== undefined) {
            if ((this.state.reportPointerDown?.length ?? 0) > 0) {
                if (this._onPointerDownBound === null) {
                    this._onPointerDownBound = (e: PointerEvent) => {
                        if (
                            eventMatchesButton(e, this.state.reportPointerDown)
                        ) {
                            this._sendEventToBackend("pointerDown", e, false);
                        }
                    };
                    this.element.addEventListener(
                        "pointerdown",
                        this._onPointerDownBound,
                        { capture: true }
                    );
                }
            } else {
                if (this._onPointerDownBound !== null) {
                    this.element.removeEventListener(
                        "pointerdown",
                        this._onPointerDownBound,
                        { capture: true } as AddEventListenerOptions
                    );
                    this._onPointerDownBound = null;
                }
            }
        }

        if (deltaState.reportPointerUp !== undefined) {
            if ((this.state.reportPointerUp?.length ?? 0) > 0) {
                if (this._onPointerUpBound === null) {
                    this._onPointerUpBound = (e: PointerEvent) => {
                        if (eventMatchesButton(e, this.state.reportPointerUp)) {
                            this._sendEventToBackend("pointerUp", e, false);
                        }
                    };
                    this.element.addEventListener(
                        "pointerup",
                        this._onPointerUpBound,
                        { capture: true }
                    );
                }
            } else {
                if (this._onPointerUpBound !== null) {
                    this.element.removeEventListener(
                        "pointerup",
                        this._onPointerUpBound,
                        { capture: true } as AddEventListenerOptions
                    );
                    this._onPointerUpBound = null;
                }
            }
        }

        if (deltaState.reportPointerMove !== undefined) {
            if (this.state.reportPointerMove) {
                if (this._onPointerMoveBound === null) {
                    this._onPointerMoveBound = (e: PointerEvent) => {
                        this._sendEventToBackend("pointerMove", e, true);
                    };
                    this.element.addEventListener(
                        "pointermove",
                        this._onPointerMoveBound,
                        { capture: true }
                    );
                }
            } else {
                if (this._onPointerMoveBound !== null) {
                    this.element.removeEventListener(
                        "pointermove",
                        this._onPointerMoveBound,
                        { capture: true } as AddEventListenerOptions
                    );
                    this._onPointerMoveBound = null;
                }
            }
        }

        if (deltaState.reportPointerEnter !== undefined) {
            if (this.state.reportPointerEnter) {
                if (this._onPointerEnterBound === null) {
                    this._onPointerEnterBound = (e: PointerEvent) => {
                        this._sendEventToBackend("pointerEnter", e, false);
                    };
                    this.element.addEventListener(
                        "pointerenter",
                        this._onPointerEnterBound,
                        { capture: true }
                    );
                }
            } else {
                if (this._onPointerEnterBound !== null) {
                    this.element.removeEventListener(
                        "pointerenter",
                        this._onPointerEnterBound,
                        { capture: true } as AddEventListenerOptions
                    );
                    this._onPointerEnterBound = null;
                }
            }
        }

        if (deltaState.reportPointerLeave !== undefined) {
            if (this.state.reportPointerLeave) {
                if (this._onPointerLeaveBound === null) {
                    this._onPointerLeaveBound = (e: PointerEvent) => {
                        this._sendEventToBackend("pointerLeave", e, false);
                    };
                    this.element.addEventListener(
                        "pointerleave",
                        this._onPointerLeaveBound,
                        { capture: true }
                    );
                }
            } else {
                if (this._onPointerLeaveBound !== null) {
                    this.element.removeEventListener(
                        "pointerleave",
                        this._onPointerLeaveBound,
                        { capture: true } as AddEventListenerOptions
                    );
                    this._onPointerLeaveBound = null;
                }
            }
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

        // Mark the event as handled if needed
        if (this.state.consume_events) markEventAsHandled(event);

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
