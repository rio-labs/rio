import { ComponentBase, ComponentState, DeltaState } from "./componentBase";
import { applyTextStyleCss, textStyleToCss } from "../cssUtils";
import { ComponentStatesUpdateContext } from "../componentManagement";
import { ComponentId } from "../dataModels";
import { ListViewComponent } from "./listView";
import { RippleEffect } from "../rippleEffect";
import { PressableElement } from "../elements/pressableElement";
import { markEventAsHandled } from "../eventHandling";

/// ListItems must keep track which ListView they belong to, in order to manage
/// the selection. Depending on whether selection is enabled ListItems must
/// behave differently (e.g. change color on hover), and destroyed ListItems
/// must be removed from the selection.
///
/// Subclasses must include a `PressableElement` somewhere in the DOM and assign
/// it to `this.pressToSelectButton`. Pressing this element will add/remove this
/// ListItem from the selection. Alternatively, you may set
/// `this.pressToSelectButton` to `null` but then it's your responsibility to
/// call `this.onPress()` whenever the list item is pressed.
export abstract class SelectableListItemComponent<
    S extends ComponentState,
> extends ComponentBase<S> {
    protected abstract pressToSelectButton: PressableElement | null;
    protected listView: ListViewComponent | null = null;

    constructor(
        id: ComponentId,
        state: S,
        context: ComponentStatesUpdateContext
    ) {
        super(id, state, context);

        // Find the ListView we belong to
        context.addEventListener("all states updated", () => {
            let parent = this.parent;

            while (parent !== null) {
                if (parent instanceof ListViewComponent) {
                    this.listView = parent;
                    parent.registerItem(this);
                    break;
                }
                parent = parent.parent;
            }
        });
    }

    onDestruction(): void {
        super.onDestruction();

        if (this.listView !== null) {
            this.listView.unregisterItem(this);
        }
    }

    onPress(event: PointerEvent | KeyboardEvent): void {
        if (this.isSelectable && this.listView !== null) {
            this.listView.onItemPress(this, event);
            markEventAsHandled(event);
        }
    }
    get isSelectable(): boolean {
        return this.element.classList.contains("rio-selectable-item");
    }
    set isSelectable(isSelectable: boolean) {
        if (isSelectable) {
            this.element.classList.add("rio-selectable-item");

            if (this.pressToSelectButton !== null) {
                this.pressToSelectButton.onPress = this.onPress.bind(this);
            }
        } else {
            this.element.classList.remove("rio-selectable-item");

            if (this.pressToSelectButton !== null) {
                this.pressToSelectButton.onPress = null;
            }
        }
    }

    set isSelected(isSelected: boolean) {
        this.element.classList.toggle("selected", isSelected);
    }
}

// === HEADING LIST ITEM =======================================================
export type HeadingListItemState = ComponentState & {
    _type_: "HeadingListItem-builtin";
    text: string;
};

export class HeadingListItemComponent extends ComponentBase<HeadingListItemState> {
    createElement(context: ComponentStatesUpdateContext): HTMLElement {
        // Create the element
        let element = document.createElement("div");
        element.classList.add("rio-heading-list-item");

        // Apply a style. This could be done with CSS, instead of doing it
        // individually for each component, but these are rare and this preempts
        // duplicate code.
        applyTextStyleCss(element, textStyleToCss("heading3"));

        return element;
    }

    updateElement(
        deltaState: DeltaState<HeadingListItemState>,
        context: ComponentStatesUpdateContext
    ): void {
        super.updateElement(deltaState, context);

        if (deltaState.text !== undefined) {
            this.element.textContent = deltaState.text;
        }
    }
}

// === SEPARATOR LIST ITEM =====================================================
export type SeparatorListItemState = ComponentState & {
    _type_: "SeparatorListItem-builtin";
};

export class SeparatorListItemComponent extends ComponentBase<SeparatorListItemState> {
    createElement(context: ComponentStatesUpdateContext): HTMLElement {
        let element = document.createElement("div");
        element.classList.add("rio-separator-list-item");
        return element;
    }
}

// === CUSTOM LIST ITEM ========================================================
export type CustomListItemState = ComponentState & {
    _type_: "CustomListItem-builtin";
    content: ComponentId;
    pressable: boolean;
};

export class CustomListItemComponent extends SelectableListItemComponent<CustomListItemState> {
    declare element: PressableElement;

    // The `SelectableListItemComponent` parent class will connect/disconnect
    // the onPress handler depending on whether the list item is selectable, but
    // that's a problem for us because we must also be clickable if `pressable`
    // is true. So we'll handle it manually.
    protected pressToSelectButton = null;

    // If this item has a ripple effect, this is the ripple instance. `null`
    // otherwise.
    private rippleInstance: RippleEffect | null = null;

    createElement(context: ComponentStatesUpdateContext): HTMLElement {
        let element = new PressableElement();
        element.classList.add("rio-custom-list-item");

        return element;
    }

    updateElement(
        deltaState: DeltaState<CustomListItemState>,
        context: ComponentStatesUpdateContext
    ): void {
        super.updateElement(deltaState, context);

        // Update the child
        this.replaceOnlyChild(context, deltaState.content);

        // Style the surface depending on whether it is pressable
        if (deltaState.pressable === true) {
            if (this.rippleInstance === null) {
                this.rippleInstance = new RippleEffect(this.element);

                this.element.style.cursor = "pointer";
                this.element.style.setProperty(
                    "--hover-color",
                    "var(--rio-local-bg-active)"
                );

                this.updateOnPressHandler();
            }
        } else if (deltaState.pressable === false) {
            if (this.rippleInstance !== null) {
                this.rippleInstance.destroy();
                this.rippleInstance = null;

                this.element.style.removeProperty("cursor");
                this.element.style.setProperty("--hover-color", "transparent");

                this.updateOnPressHandler();
            }
        }
    }

    // Override the setter so that we can update the onPress handler. (Note: In
    // order for the getter to remain functional, we must override it as well.)
    override set isSelectable(isSelectable: boolean) {
        super.isSelectable = isSelectable;

        this.updateOnPressHandler();
    }
    override get isSelectable(): boolean {
        return super.isSelectable;
    }

    private updateOnPressHandler() {
        if (this.state.pressable || this.isSelectable) {
            this.element.onPress = this._onCustomListItemPress.bind(this);
        } else {
            this.element.onPress = null;
        }
    }

    // Important: The parent class `SelectableListItemComponent` already
    // implements a `onPress` method, but that gets connected/disconnected
    // depending on whether the item is selectable or not (which also depends on
    // the selection mode of the list view). So we should avoid overriding it.
    _onCustomListItemPress(event: PointerEvent | KeyboardEvent): void {
        super.onPress(event);

        if (this.state.pressable) {
            this.sendMessageToBackend({
                type: "press",
            });
            markEventAsHandled(event);
        }
    }
}
