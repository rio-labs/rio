import {
    componentsByElement,
    componentsById,
    ComponentStatesUpdateContext,
    getComponentByElement,
} from "../componentManagement";
import { callRemoteMethodDiscardResponse } from "../rpc";
import {
    EventHandler,
    DragHandler,
    DragHandlerArguments,
    ClickHandlerArguments,
    ClickHandler,
} from "../eventHandling";
import { ComponentId } from "../dataModels";
import { insertWrapperElement, replaceElement } from "../utils";
import { devToolsConnector } from "../app";

export type Key = string | number;

/// Base for all component states. Updates received from the backend are
/// partial, hence most properties may be undefined.
export type ComponentState = {
    // The component type's unique id. Crucial so the client knows what kind of
    // component to spawn.
    readonly _type_: string;
    // Debugging information. Useful both for developing rio itself, and also
    // displayed to developers in Rio's dev tools
    _python_type_: string;
    // Debugging information
    key: Key | null;
    // How much space to leave on the left, top, right, bottom
    _margin_: [number, number, number, number];
    // Explicit size request, if any
    _min_size_: [number, number];
    // Maximum size, if any
    // MAX-SIZE-BRANCH _max_size_?: [number | null, number | null];
    // Alignment of the component within its parent, if any
    _align_: [number | null, number | null];
    // Scrolling behavior
    // SCROLLING-REWORK _scroll_?: [RioScrollBehavior, RioScrollBehavior];
    // Whether the component would like to receive additional space if there is
    // any left over
    _grow_: [boolean, boolean];
    accessibility_role: string | null;
    // Debugging information: The dev tools may not display components to the
    // developer if they're considered internal
    _rio_internal_: boolean;
};

export type DeltaState<S extends ComponentState> = Omit<Partial<S>, "_type_">;
export type DeltaStateFromBackend = DeltaState<ComponentState> &
    Pick<ComponentState, "_type_">;

/// Base class for all components
export abstract class ComponentBase<S extends ComponentState = ComponentState> {
    readonly id: ComponentId;
    readonly element: HTMLElement;

    readonly state: S;

    // Reference to the parent component. If the component is about to be
    // removed from the component tree (i.e. it's in `latent-components`), this
    // still references the *last* parent component. `null` is only for newly
    // created components and the root component.
    parent: ComponentBase | null = null;
    children = new Set<ComponentBase>();

    _eventHandlers = new Set<EventHandler>();

    private marginElement: HTMLElement | null = null;

    private outerAlignElement: HTMLElement | null = null;
    private innerAlignElement: HTMLElement | null = null;

    private outerScrollElement: HTMLElement | null = null;
    private centerScrollElement: HTMLElement | null = null;
    private innerScrollElement: HTMLElement | null = null;

    constructor(
        id: ComponentId,
        state: S,
        context: ComponentStatesUpdateContext
    ) {
        this.id = id;
        this.state = state;

        this.element = this.createElement(context);
        this.element.classList.add("rio-component");
    }

    // Layouting (alignment, scrolling, etc) may require extra HTML elements,
    // which will be created on demand. This property always points to the
    // current outermost element. So when a component is moved around in the
    // DOM, make sure to use `outerElement` instead of `element`.
    get outerElement(): HTMLElement {
        if (this.marginElement !== null) {
            return this.marginElement;
        }

        if (this.outerScrollElement !== null) {
            return this.outerScrollElement;
        }

        if (this.outerAlignElement !== null) {
            return this.outerAlignElement;
        }

        return this.element;
    }

    get alignmentElement(): HTMLElement | null {
        return this.outerAlignElement;
    }

    /// Given a partial state update, this function updates the component's HTML
    /// element to reflect the new state.
    ///
    /// The `element` parameter is identical to `this.element`. It's passed as
    /// an argument because it's more efficient than calling `this.element`.
    updateElement(
        deltaState: DeltaState<S>,
        context: ComponentStatesUpdateContext
    ): void {
        if (deltaState._min_size_ !== undefined) {
            this.element.style.minWidth = `${deltaState._min_size_[0]}rem`;
            this.element.style.minHeight = `${deltaState._min_size_[1]}rem`;
        }

        // MAX-SIZE-BRANCH if (deltaState._max_size_ !== undefined) {
        // MAX-SIZE-BRANCH     this._updateMaxSize(deltaState._max_size_);
        // MAX-SIZE-BRANCH }

        if (deltaState._align_ !== undefined) {
            this._updateAlign(deltaState._align_);
        }

        // SCROLLING-REWORK
        // if (deltaState._scroll_ !== undefined) {
        //     this._updateScroll(deltaState._scroll_);
        // }

        if (deltaState._margin_ !== undefined) {
            this._updateMargin(deltaState._margin_);
        }

        if (deltaState.accessibility_role !== undefined) {
            if (deltaState.accessibility_role === null) {
                this.element.removeAttribute("role");
            } else {
                this.element.role = deltaState.accessibility_role;
            }
        }
    }

    onChildGrowChanged(): void {}

    private _updateMaxSize(maxSize: [number | null, number | null]): void {
        let transform: string[] = [];

        if (maxSize[0] === null) {
            this.element.style.removeProperty("max-width");
            this.element.style.removeProperty("left");
        } else {
            this.element.style.maxWidth = `${maxSize[0]}rem`;
            this.element.style.left = `50%`;
            transform.push("translateX(-50%)");
        }

        if (maxSize[1] === null) {
            this.element.style.removeProperty("max-height");
            this.element.style.removeProperty("top");
        } else {
            this.element.style.maxHeight = `${maxSize[1]}rem`;
            this.element.style.top = `50%`;
            transform.push("translateY(-50%)");
        }

        this.element.style.transform = transform.join(" ");
    }

    private _updateAlign(align: [number | null, number | null]): void {
        if (align[0] === null && align[1] === null) {
            // Remove the alignElement if we have one
            if (this.outerAlignElement !== null) {
                replaceElement(
                    this.outerAlignElement,
                    this.innerAlignElement!.firstChild!
                );
                this.outerAlignElement = null;
                this.innerAlignElement = null;
            }
        } else {
            // Create the alignElement if we don't have one already
            if (this.outerAlignElement === null) {
                this.innerAlignElement = insertWrapperElement(this.element);
                this.outerAlignElement = insertWrapperElement(
                    this.innerAlignElement
                );

                this.innerAlignElement.classList.add("rio-align-inner");
                this.outerAlignElement.classList.add("rio-align-outer");

                this.outerAlignElement.dataset.ownerId = `${this.id}`;
            }

            let transform = "";

            if (align[0] === null) {
                this.innerAlignElement!.style.removeProperty("left");
                this.innerAlignElement!.style.width = "100%";
                this.innerAlignElement!.classList.add("stretch-child-x");
            } else {
                this.innerAlignElement!.style.left = `${align[0] * 100}%`;
                this.innerAlignElement!.style.width = "min-content";
                this.innerAlignElement!.classList.remove("stretch-child-x");
                transform += `translateX(-${align[0] * 100}%) `;
            }

            if (align[1] === null) {
                this.innerAlignElement!.style.removeProperty("top");
                this.innerAlignElement!.style.height = "100%";
                this.innerAlignElement!.classList.add("stretch-child-y");
            } else {
                this.innerAlignElement!.style.top = `${align[1] * 100}%`;
                this.innerAlignElement!.style.height = "min-content";
                this.innerAlignElement!.classList.remove("stretch-child-y");
                transform += `translateY(-${align[1] * 100}%) `;
            }

            this.innerAlignElement!.style.transform = transform;
        }
    }

    // SCROLLING-REWORK
    // private _updateScroll(
    //     scroll: [RioScrollBehavior, RioScrollBehavior]
    // ): void {
    //     if (scroll[0] === 'never' && scroll[1] === 'never') {
    //         // Remove the scrollElement if we have one
    //         if (this.outerScrollElement !== null) {
    //             replaceElement(
    //                 this.outerScrollElement,
    //                 this.outerScrollElement.firstChild!
    //             );
    //             this.outerScrollElement = null;
    //         }
    //     } else {
    //         // Create the scrollElement if we don't have one already
    //         if (this.outerScrollElement === null) {
    //             this.innerScrollElement = insertWrapperElement(
    //                 this.outerAlignElement ?? this.element
    //             );
    //             this.centerScrollElement = insertWrapperElement(
    //                 this.innerScrollElement
    //             );
    //             this.outerScrollElement = insertWrapperElement(
    //                 this.centerScrollElement
    //             );

    //             this.outerScrollElement.dataset.ownerId = `${this.id}`;
    //             this.outerScrollElement.className =
    //                 'rio-scroll-helper rio-scroll';
    //         }

    //         this.outerScrollElement.dataset.scrollX = scroll[0];
    //         this.outerScrollElement.dataset.scrollY = scroll[1];
    //     }
    // }

    private _updateMargin(margin: [number, number, number, number]): void {
        if (
            margin[0] === 0 &&
            margin[1] === 0 &&
            margin[2] === 0 &&
            margin[3] === 0
        ) {
            // Remove the marginElement if we have one
            if (this.marginElement !== null) {
                replaceElement(
                    this.marginElement,
                    this.marginElement.firstChild!
                );
                this.marginElement = null;
            }
        } else {
            // Create the marginElement if we don't have one already
            if (this.marginElement === null) {
                this.marginElement = insertWrapperElement(
                    this.outerScrollElement ??
                        this.outerAlignElement ??
                        this.element
                );

                this.marginElement.classList.add("rio-margin");

                this.marginElement.dataset.ownerId = `${this.id}`;
            }

            // Margins cause weird problems (for example, they can stick out of
            // the parent element), so we use padding instead
            this.marginElement.style.paddingLeft = `${margin[0]}rem`;
            this.marginElement.style.paddingTop = `${margin[1]}rem`;
            this.marginElement.style.paddingRight = `${margin[2]}rem`;
            this.marginElement.style.paddingBottom = `${margin[3]}rem`;
        }
    }

    private unparent(context: ComponentStatesUpdateContext): void {
        // Remove this component from its parent
        console.assert(
            this.parent !== null,
            `.unparent() was called on ${this}, which doesn't have a parent`
        );

        this.parent!.children.delete(this);
        context.latentComponents.add(this);
    }

    registerChild(
        context: ComponentStatesUpdateContext,
        child: ComponentBase
    ): void {
        // Remove the child from its previous parent
        if (child.parent !== null) {
            child.parent.children.delete(child);
        }

        // Add it to this component
        child.parent = this;
        this.children.add(child);
        context.latentComponents.delete(child);
    }

    /// Appends the given child component at the end of the given HTML element.
    /// Does not remove or modify any existing children. If `childId` is
    /// `undefined`, does nothing.
    appendChild(
        context: ComponentStatesUpdateContext,
        childId: ComponentId | undefined,
        parentElement: HTMLElement = this.element
    ): void {
        // If undefined, do nothing
        if (childId === undefined) {
            return;
        }

        // Add the child
        let child = componentsById[childId]!;
        parentElement.appendChild(child.outerElement);

        this.registerChild(context, child);
    }

    /// Replaces the child of the given HTML element with the given child. The
    /// element must have zero or one children. If `childId` is `null`, removes
    /// the current child. If `childId` is `undefined`, does nothing.
    replaceOnlyChild(
        context: ComponentStatesUpdateContext,
        childId: null | undefined | ComponentId,
        parentElement: HTMLElement = this.element
    ): void {
        // If undefined, do nothing
        if (childId === undefined) {
            return;
        }

        // If null, remove the current child
        let currentChildElement: Element | null = null;
        for (let child of iterChildElements(parentElement)) {
            currentChildElement = child;
            break;
        }

        if (childId === null) {
            if (currentChildElement !== null) {
                let child = getComponentByElement(currentChildElement);

                currentChildElement.remove();
                child.unparent(context);
            }

            console.assert(
                parentElement.firstElementChild === null,
                `Parent element ${parentElement} still has a child after replaceOnlyChild(null)`
            );
            return;
        }

        // If a child already exists, either move it to the latent container or
        // leave it alone if it's already the correct element
        if (currentChildElement !== null) {
            let child = getComponentByElement(currentChildElement);

            // Don't reparent the child if not necessary. This way things like
            // keyboard focus are preserved
            if (child.id === childId) {
                return;
            }

            currentChildElement.remove();
            child.unparent(context);
        }

        // Add the replacement component
        let child = componentsById[childId]!;
        parentElement.appendChild(child.outerElement);

        this.registerChild(context, child);
    }

    /// Replaces all children of the given HTML element with the given children.
    /// If `childIds` is `undefined`, does nothing.
    ///
    /// If `wrapInDivs` is true, each child is wrapped in a `<div>` element.
    /// This also requires any existing children to be wrapped in `<div>`s.
    replaceChildren(
        context: ComponentStatesUpdateContext,
        childIds: undefined | ComponentId[],
        parentElement: HTMLElement = this.element,
        wrapInDivs: boolean = false
    ): void {
        // If undefined, do nothing
        if (childIds === undefined) {
            return;
        }

        let childElementIter = iterChildElements(parentElement);
        let curElement = childElementIter.next().value;
        let children = childIds.map((id) => componentsById[id]!);
        let curIndex = 0;

        // Since children are being moved between parents, it's possible for
        // some empty wrappers to persist. In that case `unwrap` will return
        // `null`.
        let wrap: (element: HTMLElement) => Element;
        let unwrap: (element: Element) => HTMLElement | null;
        if (wrapInDivs) {
            wrap = (element: HTMLElement) => {
                let wrapper = document.createElement("div");
                wrapper.classList.add("rio-child-wrapper");
                wrapper.appendChild(element);
                return wrapper;
            };
            unwrap = (element: Element) =>
                element.firstElementChild as HTMLElement | null;
        } else {
            wrap = (element: HTMLElement) => element;
            unwrap = (element: Element) => element as HTMLElement;
        }

        while (true) {
            // If there are no more children in the DOM element, add the
            // remaining children
            if (curElement === null) {
                while (curIndex < children.length) {
                    let child = children[curIndex];

                    parentElement.appendChild(wrap(child.outerElement));
                    this.registerChild(context, child);

                    curIndex++;
                }
                break;
            }

            // If there are no more children in the message, remove the
            // remaining DOM children
            if (curIndex >= children.length) {
                while (curElement !== null) {
                    curElement.remove();

                    let childElement = unwrap(curElement);
                    if (childElement !== null) {
                        let child = getComponentByElement(childElement);
                        child.unparent(context);
                    }

                    curElement = childElementIter.next().value;
                }
                break;
            }

            // If this was just an empty wrapper element, remove it and move on
            // to the next element
            let childElement = unwrap(curElement);

            if (childElement === null) {
                curElement.remove();
                curElement = childElementIter.next().value;
                continue;
            }

            // If this element is the correct element, move on
            let curChild = getComponentByElement(childElement);
            let expectedChild = children[curIndex];
            if (curChild === expectedChild) {
                curElement = childElementIter.next().value;
                curIndex++;
                continue;
            }

            // This element is not the correct element, insert the correct one
            // instead
            parentElement.insertBefore(
                wrap(expectedChild.outerElement),
                curElement
            );
            this.registerChild(context, expectedChild);

            curIndex++;
        }
    }

    /// Removes all children of the given HTML element. Children that are
    /// components are removed properly, while simple HTML are simply removed
    /// from the DOM.
    ///
    /// This is **not recursive**. It only looks through the direct children of
    /// an element and removes them.
    removeHtmlOrComponentChildren(
        context: ComponentStatesUpdateContext,
        parentElement: HTMLElement
    ) {
        while (true) {
            let childElement =
                parentElement.firstElementChild! as HTMLElement | null;

            // Done?
            if (childElement === null) {
                break;
            }

            // Is this a component?
            let childComponent = componentsByElement.get(childElement);

            if (childComponent === undefined) {
                // Nope, it's just HTML
                childElement.remove();
            } else {
                // Yes, take extra special tender loving care
                childComponent.unparent(context);
                childElement.remove();
            }
        }
    }

    /// Creates the HTML element associated with this component. This function does
    /// not attach the element to the DOM, but merely returns it.
    protected abstract createElement(
        context: ComponentStatesUpdateContext
    ): HTMLElement;

    /// This method is called when a component is about to be removed from the
    /// component tree. It can be used for cleaning up event handlers and helper
    /// HTML elements (like popups).
    onDestruction(): void {
        for (let handler of this._eventHandlers) {
            handler.disconnect();
        }
    }

    /// Send a message to the python instance corresponding to this component. The
    /// message is an arbitrary JSON object and will be passed to the instance's
    /// `_on_message` method.
    sendMessageToBackend(message: object): void {
        callRemoteMethodDiscardResponse("componentMessage", {
            component_id: this.id,
            payload: message,
        });
    }

    _setStateDontNotifyBackend(deltaState: DeltaState<S>): void {
        // Trigger an update
        this.updateElement(
            deltaState,
            null as any as ComponentStatesUpdateContext
        );

        // Set the state
        Object.assign(this.state, deltaState);

        // Notify the dev tools, if any
        if (devToolsConnector !== null) {
            devToolsConnector.afterComponentStateChange({
                [this.id]: deltaState,
            });
        }
    }

    setStateAndNotifyBackend(deltaState: DeltaState<S>): void {
        // Set the state. This also updates the component
        this._setStateDontNotifyBackend(deltaState);

        // Notify the backend
        callRemoteMethodDiscardResponse("componentStateUpdate", {
            component_id: this.id,
            delta_state: deltaState,
        });
    }

    addClickHandler(args: ClickHandlerArguments): ClickHandler {
        return new ClickHandler(this, args);
    }

    addDragHandler(args: DragHandlerArguments): DragHandler {
        return new DragHandler(this, args);
    }

    toString(): string {
        let class_name = this.constructor.name;
        return `<${class_name} id:${this.id}>`;
    }
}

globalThis.RIO_COMPONENT_BASE = ComponentBase;

/// Iterates over an element's children, but ignores elements that have the
/// `rio-not-a-child-component` class. This is used by e.g. the RippleEffect.
function* iterChildElements(parentElement: Element) {
    // Since `replaceChildren` removes elements from the DOM, it messes up the
    // iteration for us. So we'll first store the elements in an array, and then
    // yield them.
    //
    // Yes, I know this function is pretty weird, but the upside is that
    // `replaceChildren` is neater in exchange.
    let children: Element[] = [];

    let element = parentElement.firstElementChild;

    while (element !== null) {
        if (!element.classList.contains("rio-not-a-child-component")) {
            children.push(element);
        }

        element = element.nextElementSibling;
    }

    for (let element of children) {
        yield element;
    }
    return null; // Return instead of yield to shut up the type checker
}
