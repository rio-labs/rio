import { ComponentBase, ComponentState, DeltaState } from "./componentBase";
import { applyTextStyleCss, textStyleToCss } from "../cssUtils";
import { ComponentStatesUpdateContext } from "../componentManagement";
import { ComponentId } from "../dataModels";
import { ListViewComponent } from "./listView";
import { RippleEffect } from "../rippleEffect";
import { PressableElement } from "../elements/pressableElement";

/// ListItems must keep track which ListView they belong to, in order to manage
/// the selection. Depending on whether selection is enabled ListItems must
/// behave differently (e.g. change color on hover), and destroyed ListItems
/// must be removed from the selection.
///
/// Subclasses must include a `PressableElement` somewhere in the DOM and assign
/// it to `this.pressToSelectButton`. Pressing this element will add/remove this
/// ListItem from the selection.
export abstract class SelectableListItemComponent<
    S extends ComponentState,
> extends ComponentBase<S> {
    protected pressToSelectButton: PressableElement;
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

    set isSelectable(isSelectable: boolean) {
        if (isSelectable) {
            this.element.classList.add("rio-selectable-item");

            this.pressToSelectButton.onPress = (
                event: PointerEvent | KeyboardEvent
            ) => {
                if (this.listView !== null) {
                    this.listView.onItemPress(this, event);
                }
            };
        } else {
            this.element.classList.remove("rio-selectable-item");
            this.pressToSelectButton.onPress = null;
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
    // If this item has a ripple effect, this is the ripple instance. `null`
    // otherwise.
    private rippleInstance: RippleEffect | null = null;

    createElement(context: ComponentStatesUpdateContext): HTMLElement {
        let element = new PressableElement();
        element.classList.add("rio-custom-list-item");

        this.pressToSelectButton = element;

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

                this.element.onclick = this.onPress.bind(this);
            }
        } else if (deltaState.pressable === false) {
            if (this.rippleInstance !== null) {
                this.rippleInstance.destroy();
                this.rippleInstance = null;

                this.element.style.removeProperty("cursor");
                this.element.style.setProperty("--hover-color", "transparent");

                this.element.onclick = null;
            }
        }
    }

    private onPress(): void {
        this.sendMessageToBackend({
            type: "press",
        });
    }
}
