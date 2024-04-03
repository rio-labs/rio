import { ComponentBase } from './components/componentBase';

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
    onClick: (event: MouseEvent) => boolean;
    target?: EventTarget;
    capturing?: boolean;
};

export class ClickHandler extends EventHandler {
    private onClick: (event: MouseEvent) => void;
    private target: EventTarget;
    private capturing: boolean;

    constructor(component: ComponentBase, args: ClickHandlerArguments) {
        super(component);

        this.onClick = args.onClick;
        this.target = args.target ?? component.element;
        this.capturing = args.capturing ?? false;

        // @ts-ignore
        this.target.addEventListener('click', this.onClick, this.capturing);
    }

    override disconnect(): void {
        super.disconnect();

        // @ts-ignore
        this.target.removeEventListener('click', this.onClick, this.capturing);
    }
}

export type DragHandlerArguments = {
    element: HTMLElement;
    onStart?: (event: MouseEvent) => boolean;
    onMove?: (event: MouseEvent) => void;
    onEnd?: (event: MouseEvent) => void;
    capturing?: boolean;
};

export class DragHandler extends EventHandler {
    private element: HTMLElement;
    private onStart: (event: MouseEvent) => boolean;
    private onMove: (event: MouseEvent) => void;
    private onEnd: (event: MouseEvent) => void;
    private capturing: boolean;

    private onMouseDown = this._onMouseDown.bind(this);
    private onMouseMove = this._onMouseMove.bind(this);
    private onMouseUp = this._onMouseUp.bind(this);
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
            'mousedown',
            this.onMouseDown,
            this.capturing
        );
    }

    private _onMouseDown(event: MouseEvent): void {
        console.debug('Drag: mouse down');
        let onStartResult = this.onStart(event);
        console.debug('Drag: onStart result', onStartResult);

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

        console.debug('Drag: mouse down stop propagation');
        event.stopPropagation();

        window.addEventListener('mousemove', this.onMouseMove, true);
        window.addEventListener('mouseup', this.onMouseUp, true);
        window.addEventListener('click', this.onClick, true);
    }

    private _onMouseMove(event: MouseEvent): void {
        console.debug('Drag: mouse move');
        this.hasDragged = true;

        event.stopPropagation();
        this.onMove(event);
    }

    private _onMouseUp(event: MouseEvent): void {
        console.debug('Drag: mouse up');
        if (this.hasDragged) {
            console.debug('Preventing default due to drag');
            event.stopPropagation();
        }

        this._disconnectDragListeners();
        this.onEnd(event);
    }

    private _onClick(event: MouseEvent): void {
        // This event isn't using by the drag event handler, but it should
        // nonetheless be stopped to prevent the click from being handled by
        // other handlers.

        console.debug('Drag: click');

        if (this.hasDragged) {
            console.debug('Preventing default due to drag');
            event.stopPropagation();
            event.stopImmediatePropagation();
            event.preventDefault();
        }
    }

    private _disconnectDragListeners(): void {
        window.removeEventListener('mousemove', this.onMouseMove, true);
        window.removeEventListener('mouseup', this.onMouseUp, true);
        window.removeEventListener('click', this.onClick, true);
    }

    override disconnect(): void {
        super.disconnect();

        this.element.removeEventListener(
            'mousedown',
            this.onMouseDown,
            this.capturing
        );
        this._disconnectDragListeners();
    }
}
