import { pixelsPerRem } from '../app';
import { SingleContainer } from './singleContainer';
import { ComponentBase, ComponentState } from './componentBase';
import { DragHandler } from '../eventHandling';
import { tryGetComponentByElement } from '../componentManagement';
import { ComponentId } from '../dataModels';

function eventMouseButtonToString(event: MouseEvent): object {
    return {
        button: ['left', 'middle', 'right'][event.button],
    };
}

function eventMousePositionToString(event: MouseEvent): object {
    return {
        x: event.clientX / pixelsPerRem,
        y: event.clientY / pixelsPerRem,
    };
}

function findComponentUnderMouse(event: MouseEvent): ComponentId {
    // The coordinates for `elementFromPoint` are relative to the viewport. This
    // matches `event.clientX` and `event.clientY`.
    let element = document.elementFromPoint(event.clientX, event.clientY)!;

    // It could be an internal element. Go up the tree until we find a Component
    let component: ComponentBase | null;
    while (true) {
        component = tryGetComponentByElement(element);

        if (component !== null) {
            break;
        }

        element = element.parentElement!;
    }

    // Make sure not to return any injected Align or Margin components
    while (component.isInjectedLayoutComponent()) {
        component = component.parent!;
    }

    return component.id;
}

export type MouseEventListenerState = ComponentState & {
    _type_: 'MouseEventListener-builtin';
    content?: ComponentId;
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

export class MouseEventListenerComponent extends SingleContainer {
    state: Required<MouseEventListenerState>;

    private _dragHandler: DragHandler | null = null;

    createElement(): HTMLElement {
        return document.createElement('div');
    }

    updateElement(
        deltaState: MouseEventListenerState,
        latentComponents: Set<ComponentBase>
    ): void {
        this.replaceOnlyChild(latentComponents, deltaState.content);

        if (deltaState.reportPress) {
            this.element.onclick = (e) => {
                this.sendMessageToBackend({
                    type: 'press',
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
                    type: 'mouseDown',
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
                    type: 'mouseUp',
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
                    type: 'mouseMove',
                    ...eventMousePositionToString(e),
                });
            };
        } else {
            this.element.onmousemove = null;
        }

        if (deltaState.reportMouseEnter) {
            this.element.onmouseenter = (e) => {
                this.sendMessageToBackend({
                    type: 'mouseEnter',
                    ...eventMousePositionToString(e),
                });
            };
        } else {
            this.element.onmouseenter = null;
        }

        if (deltaState.reportMouseLeave) {
            this.element.onmouseleave = (e) => {
                this.sendMessageToBackend({
                    type: 'mouseLeave',
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
            this._sendDragEvent('dragStart', event);
        }
        return true;
    }

    private _onDragMove(event: MouseEvent): void {
        if (this.state.reportDragMove) {
            this._sendDragEvent('dragMove', event);
        }
    }

    private _onDragEnd(event: MouseEvent): void {
        if (this.state.reportDragEnd) {
            this._sendDragEvent('dragEnd', event);
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
