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

        if (deltaState.reportPress !== undefined) {
            if (this.state.reportPress) {
                if (this._onClickBound === null) {
                    this._onClickBound = (e: MouseEvent) => {
                        this._sendMessageToBackend(e, {
                            type: "press",
                            ...eventMouseButtonToString(e),
                            ...eventMousePositionToString(e),
                        });
                    };
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

        if (deltaState.reportMouseDown !== undefined) {
            if (this.state.reportMouseDown) {
                if (this._onMouseDownBound === null) {
                    this._onMouseDownBound = (e: MouseEvent) => {
                        this._sendMessageToBackend(e, {
                            type: "mouseDown",
                            ...eventMouseButtonToString(e),
                            ...eventMousePositionToString(e),
                        });
                    };
                    this.element.addEventListener(
                        "mousedown",
                        this._onMouseDownBound,
                        { capture: true }
                    );
                }
            } else {
                if (this._onMouseDownBound !== null) {
                    this.element.removeEventListener(
                        "mousedown",
                        this._onMouseDownBound,
                        { capture: true } as AddEventListenerOptions
                    );
                    this._onMouseDownBound = null;
                }
            }
        }

        if (deltaState.reportMouseUp !== undefined) {
            if (this.state.reportMouseUp) {
                if (this._onMouseUpBound === null) {
                    this._onMouseUpBound = (e: MouseEvent) => {
                        this._sendMessageToBackend(e, {
                            type: "mouseUp",
                            ...eventMouseButtonToString(e),
                            ...eventMousePositionToString(e),
                        });
                    };
                    this.element.addEventListener(
                        "mouseup",
                        this._onMouseUpBound,
                        { capture: true }
                    );
                }
            } else {
                if (this._onMouseUpBound !== null) {
                    this.element.removeEventListener(
                        "mouseup",
                        this._onMouseUpBound,
                        { capture: true } as AddEventListenerOptions
                    );
                    this._onMouseUpBound = null;
                }
            }
        }

        if (deltaState.reportMouseMove !== undefined) {
            if (this.state.reportMouseMove) {
                if (this._onMouseMoveBound === null) {
                    this._onMouseMoveBound = (e: MouseEvent) => {
                        this._sendMessageToBackend(e, {
                            type: "mouseMove",
                            ...eventMousePositionToString(e),
                        });
                    };
                    this.element.addEventListener(
                        "mousemove",
                        this._onMouseMoveBound,
                        { capture: true }
                    );
                }
            } else {
                if (this._onMouseMoveBound !== null) {
                    this.element.removeEventListener(
                        "mousemove",
                        this._onMouseMoveBound,
                        { capture: true } as AddEventListenerOptions
                    );
                    this._onMouseMoveBound = null;
                }
            }
        }

        if (deltaState.reportMouseEnter !== undefined) {
            if (this.state.reportMouseEnter) {
                if (this._onMouseEnterBound === null) {
                    this._onMouseEnterBound = (e: MouseEvent) => {
                        this._sendMessageToBackend(e, {
                            type: "mouseEnter",
                            ...eventMousePositionToString(e),
                        });
                    };
                    this.element.addEventListener(
                        "mouseenter",
                        this._onMouseEnterBound,
                        { capture: true }
                    );
                }
            } else {
                if (this._onMouseEnterBound !== null) {
                    this.element.removeEventListener(
                        "mouseenter",
                        this._onMouseEnterBound,
                        { capture: true } as AddEventListenerOptions
                    );
                    this._onMouseEnterBound = null;
                }
            }
        }

        if (deltaState.reportMouseLeave !== undefined) {
            if (this.state.reportMouseLeave) {
                if (this._onMouseLeaveBound === null) {
                    this._onMouseLeaveBound = (e: MouseEvent) => {
                        this._sendMessageToBackend(e, {
                            type: "mouseLeave",
                            ...eventMousePositionToString(e),
                        });
                    };
                    this.element.addEventListener(
                        "mouseleave",
                        this._onMouseLeaveBound,
                        { capture: true }
                    );
                }
            } else {
                if (this._onMouseLeaveBound !== null) {
                    this.element.removeEventListener(
                        "mouseleave",
                        this._onMouseLeaveBound,
                        { capture: true } as AddEventListenerOptions
                    );
                    this._onMouseLeaveBound = null;
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
