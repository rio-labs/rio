import { ComponentBase } from "./components/componentBase";

export function markEventAsHandled(event: Event): void {
    event.stopPropagation();
    event.stopImmediatePropagation();
    event.preventDefault();
}

export function stopPropagation(event: Event): void {
    event.stopPropagation();
}

export abstract class EventHandler {
    component: ComponentBase;

    constructor(component: ComponentBase) {
        this.component = component;

        component._eventHandlers.add(this);
    }

    disconnect(): void {
        this.component._eventHandlers.delete(this);
    }
}

function _no_op(): boolean {
    return true;
}

export type ClickHandlerArguments = {
    onClick: (event: PointerEvent) => boolean;
    target?: EventTarget;
    capturing?: boolean;
};

export class ClickHandler extends EventHandler {
    private onClick: (event: PointerEvent) => void;
    private target: EventTarget;
    private capturing: boolean;

    constructor(component: ComponentBase, args: ClickHandlerArguments) {
        super(component);

        this.onClick = args.onClick;
        this.target = args.target ?? component.element;
        this.capturing = args.capturing ?? false;

        // @ts-ignore
        this.target.addEventListener("click", this.onClick, this.capturing);
    }

    override disconnect(): void {
        super.disconnect();

        // @ts-ignore
        this.target.removeEventListener("click", this.onClick, this.capturing);
    }
}

export type DragHandlerArguments = {
    element: HTMLElement;
    onStart?: (event: PointerEvent) => boolean;
    onMove?: (event: PointerEvent) => void;
    onEnd?: (event: PointerEvent) => void;
    capturing?: boolean;
};

export class DragHandler extends EventHandler {
    private element: HTMLElement;
    private onStart: (event: PointerEvent) => boolean;
    private onMove: (event: PointerEvent) => void;
    private onEnd: (event: PointerEvent) => void;
    private capturing: boolean;

    private onPointerDown = this._onPointerDown.bind(this);
    private onPointerMove = this._onPointerMove.bind(this);
    private onPointerUp = this._onPointerUp.bind(this);
    private onClick = this._onClick.bind(this);

    private hasDragged = false;

    constructor(component: ComponentBase, args: DragHandlerArguments) {
        super(component);

        this.element = args.element;

        this.onStart = args.onStart ?? _no_op;
        this.onMove = args.onMove ?? _no_op;
        this.onEnd = args.onEnd ?? _no_op;

        this.capturing = args.capturing ?? true;
        this.element.addEventListener(
            "pointerdown",
            this.onPointerDown,
            this.capturing
        );
    }

    private _onPointerDown(event: PointerEvent): void {
        // On mice we only care about the left mouse button
        if (event.pointerType === "mouse" && event.button !== 0) {
            return;
        }

        let onStartResult = this.onStart(event);

        // It's easy to forget to return a boolean. Make sure to catch this
        // mistake.
        if (onStartResult !== true && onStartResult !== false) {
            throw new Error(
                `Drag event onStart must return a boolean, but it returned ${onStartResult}`
            );
        }

        // Don't continue if the handler isn't interested in the event.
        if (!onStartResult) {
            return;
        }

        markEventAsHandled(event);
        this.hasDragged = false;

        window.addEventListener("pointermove", this.onPointerMove, true);
        window.addEventListener("pointerup", this.onPointerUp, true);
        window.addEventListener("click", this.onClick, true);
    }

    private _onPointerMove(event: PointerEvent): void {
        this.hasDragged = true;

        markEventAsHandled(event);

        this.onMove(event);
    }

    private _onPointerUp(event: PointerEvent): void {
        if (this.hasDragged) {
            markEventAsHandled(event);
        }

        // Disconnect all the drag listeners. The problem here is that if we do
        // it right now, the event handler that's supposed to block the `click`
        // event will be gone before the click event is even triggered. But
        // there's also no guarantee that a click will be triggered at all, so
        // we can't make the `click` handler disconnect itself. ("click" is only
        // triggered if mousedown and mouseup happened on the same element.)
        //
        // Workaround: Delay the disconnect a little bit.
        window.removeEventListener("pointermove", this.onPointerMove, true);
        window.removeEventListener("pointerup", this.onPointerUp, true);
        requestAnimationFrame(() =>
            window.removeEventListener("click", this.onClick, true)
        );

        this.onEnd(event);
    }

    private _onClick(event: PointerEvent): void {
        // This event isn't using by the drag event handler, but it should
        // nonetheless be stopped to prevent the click from being handled by
        // other handlers.

        if (this.hasDragged) {
            markEventAsHandled(event);
        }
    }

    private _disconnectDragListeners(): void {
        window.removeEventListener("pointermove", this.onPointerMove, true);
        window.removeEventListener("pointerup", this.onPointerUp, true);
        window.removeEventListener("click", this.onClick, true);
    }

    override disconnect(): void {
        super.disconnect();

        this.element.removeEventListener(
            "pointerdown",
            this.onPointerDown,
            this.capturing
        );
        this._disconnectDragListeners();
    }
}
