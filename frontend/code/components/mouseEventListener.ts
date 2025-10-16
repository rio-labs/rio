import { pixelsPerRem } from "../app";
import { ComponentBase, ComponentState, DeltaState } from "./componentBase";
import { DragHandler } from "../eventHandling";
import { ComponentId } from "../dataModels";
import { findComponentUnderMouse } from "../utils";
import { ComponentStatesUpdateContext } from "../componentManagement";
import { markEventAsHandled } from "../eventHandling";

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
    consume_events: boolean;
    capture_events: boolean;
};

export class MouseEventListenerComponent extends ComponentBase<MouseEventListenerState> {
    private _dragHandler: DragHandler | null = null;
    // Handler refs created on install to keep structure minimal
    private _onClickBound: ((e: MouseEvent) => void) | null = null;
    private _onMouseDownBound: ((e: MouseEvent) => void) | null = null;
    private _onMouseUpBound: ((e: MouseEvent) => void) | null = null;
    private _onMouseMoveBound: ((e: MouseEvent) => void) | null = null;
    private _onMouseEnterBound: ((e: MouseEvent) => void) | null = null;
    private _onMouseLeaveBound: ((e: MouseEvent) => void) | null = null;

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

        if (
            deltaState.reportPress !== undefined ||
            deltaState.capture_events !== undefined
        ) {
            const reportPress =
                deltaState.reportPress ?? this.state.reportPress;
            const captureEvents =
                deltaState.capture_events ?? this.state.capture_events;

            // Remove existing listener if it exists
            if (this._onClickBound !== null) {
                const oldOptions = this.state.capture_events
                    ? { capture: true }
                    : {};
                this.element.removeEventListener(
                    "click",
                    this._onClickBound,
                    oldOptions as AddEventListenerOptions
                );
            }

            if (reportPress) {
                // Install new listener with current capture setting
                this._onClickBound = (e: MouseEvent) => {
                    this._sendMessageToBackend(e, {
                        type: "press",
                        ...eventMouseButtonToString(e),
                        ...eventMousePositionToString(e),
                    });
                };
                const options = captureEvents ? { capture: true } : {};
                this.element.addEventListener(
                    "click",
                    this._onClickBound,
                    options
                );
            } else {
                this._onClickBound = null;
            }
        }

        if (
            deltaState.reportMouseDown !== undefined ||
            deltaState.capture_events !== undefined
        ) {
            const reportMouseDown =
                deltaState.reportMouseDown ?? this.state.reportMouseDown;
            const captureEvents =
                deltaState.capture_events ?? this.state.capture_events;

            // Remove existing listener if it exists
            if (this._onMouseDownBound !== null) {
                const oldOptions = this.state.capture_events
                    ? { capture: true }
                    : {};
                this.element.removeEventListener(
                    "mousedown",
                    this._onMouseDownBound,
                    oldOptions as AddEventListenerOptions
                );
            }

            if (reportMouseDown) {
                // Install new listener with current capture setting
                this._onMouseDownBound = (e: MouseEvent) => {
                    this._sendMessageToBackend(e, {
                        type: "mouseDown",
                        ...eventMouseButtonToString(e),
                        ...eventMousePositionToString(e),
                    });
                };
                const options = captureEvents ? { capture: true } : {};
                this.element.addEventListener(
                    "mousedown",
                    this._onMouseDownBound,
                    options
                );
            } else {
                this._onMouseDownBound = null;
            }
        }

        if (
            deltaState.reportMouseUp !== undefined ||
            deltaState.capture_events !== undefined
        ) {
            const reportMouseUp =
                deltaState.reportMouseUp ?? this.state.reportMouseUp;
            const captureEvents =
                deltaState.capture_events ?? this.state.capture_events;

            // Remove existing listener if it exists
            if (this._onMouseUpBound !== null) {
                const oldOptions = this.state.capture_events
                    ? { capture: true }
                    : {};
                this.element.removeEventListener(
                    "mouseup",
                    this._onMouseUpBound,
                    oldOptions as AddEventListenerOptions
                );
            }

            if (reportMouseUp) {
                // Install new listener with current capture setting
                this._onMouseUpBound = (e: MouseEvent) => {
                    this._sendMessageToBackend(e, {
                        type: "mouseUp",
                        ...eventMouseButtonToString(e),
                        ...eventMousePositionToString(e),
                    });
                };
                const options = captureEvents ? { capture: true } : {};
                this.element.addEventListener(
                    "mouseup",
                    this._onMouseUpBound,
                    options
                );
            } else {
                this._onMouseUpBound = null;
            }
        }

        if (
            deltaState.reportMouseMove !== undefined ||
            deltaState.capture_events !== undefined
        ) {
            const reportMouseMove =
                deltaState.reportMouseMove ?? this.state.reportMouseMove;
            const captureEvents =
                deltaState.capture_events ?? this.state.capture_events;

            // Remove existing listener if it exists
            if (this._onMouseMoveBound !== null) {
                const oldOptions = this.state.capture_events
                    ? { capture: true }
                    : {};
                this.element.removeEventListener(
                    "mousemove",
                    this._onMouseMoveBound,
                    oldOptions as AddEventListenerOptions
                );
            }

            if (reportMouseMove) {
                // Install new listener with current capture setting
                this._onMouseMoveBound = (e: MouseEvent) => {
                    this._sendMessageToBackend(e, {
                        type: "mouseMove",
                        ...eventMousePositionToString(e),
                    });
                };
                const options = captureEvents ? { capture: true } : {};
                this.element.addEventListener(
                    "mousemove",
                    this._onMouseMoveBound,
                    options
                );
            } else {
                this._onMouseMoveBound = null;
            }
        }

        if (
            deltaState.reportMouseEnter !== undefined ||
            deltaState.capture_events !== undefined
        ) {
            const reportMouseEnter =
                deltaState.reportMouseEnter ?? this.state.reportMouseEnter;
            const captureEvents =
                deltaState.capture_events ?? this.state.capture_events;

            // Remove existing listener if it exists
            if (this._onMouseEnterBound !== null) {
                const oldOptions = this.state.capture_events
                    ? { capture: true }
                    : {};
                this.element.removeEventListener(
                    "mouseenter",
                    this._onMouseEnterBound,
                    oldOptions as AddEventListenerOptions
                );
            }

            if (reportMouseEnter) {
                // Install new listener with current capture setting
                this._onMouseEnterBound = (e: MouseEvent) => {
                    this._sendMessageToBackend(e, {
                        type: "mouseEnter",
                        ...eventMousePositionToString(e),
                    });
                };
                const options = captureEvents ? { capture: true } : {};
                this.element.addEventListener(
                    "mouseenter",
                    this._onMouseEnterBound,
                    options
                );
            } else {
                this._onMouseEnterBound = null;
            }
        }

        if (
            deltaState.reportMouseLeave !== undefined ||
            deltaState.capture_events !== undefined
        ) {
            const reportMouseLeave =
                deltaState.reportMouseLeave ?? this.state.reportMouseLeave;
            const captureEvents =
                deltaState.capture_events ?? this.state.capture_events;

            // Remove existing listener if it exists
            if (this._onMouseLeaveBound !== null) {
                const oldOptions = this.state.capture_events
                    ? { capture: true }
                    : {};
                this.element.removeEventListener(
                    "mouseleave",
                    this._onMouseLeaveBound,
                    oldOptions as AddEventListenerOptions
                );
            }

            if (reportMouseLeave) {
                // Install new listener with current capture setting
                this._onMouseLeaveBound = (e: MouseEvent) => {
                    this._sendMessageToBackend(e, {
                        type: "mouseLeave",
                        ...eventMousePositionToString(e),
                    });
                };
                const options = captureEvents ? { capture: true } : {};
                this.element.addEventListener(
                    "mouseleave",
                    this._onMouseLeaveBound,
                    options
                );
            } else {
                this._onMouseLeaveBound = null;
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
        this._sendMessageToBackend(event, {
            type: eventType,
            ...eventMouseButtonToString(event),
            x: event.clientX / pixelsPerRem,
            y: event.clientY / pixelsPerRem,
            component: findComponentUnderMouse(event),
        });
    }

    private _sendMessageToBackend(event: MouseEvent, message: object): void {
        // Mark the event as handled if needed
        if (this.state.consume_events) markEventAsHandled(event);

        this.sendMessageToBackend(message);
    }
}
