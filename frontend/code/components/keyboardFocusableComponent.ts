import { ComponentId } from "../dataModels";
import { ComponentBase, ComponentState } from "./componentBase";

export type KeyboardFocusableComponentState = ComponentState & {
    auto_focus: boolean;
};

/// Base class for components that can receive keyboard focus. What this class
/// does:
/// - Enforces the presence of `auto_focus` in the component state
/// - Focuses the component on mount if `auto_focus` is true
///
/// There are also some other places where this class is used:
/// - In `updateComponentStates`, the keyboard focus is automatically moved to a
///   `KeyboardFocusableComponent` if the focused component dies
/// - The `setKeyboardFocus` RPC function only works with these components
export abstract class KeyboardFocusableComponent<
    S extends KeyboardFocusableComponentState = KeyboardFocusableComponentState,
> extends ComponentBase<S> {
    constructor(id: ComponentId, state: S) {
        super(id, state);

        if (state.auto_focus) {
            // `.focus()` may not work on the initial page load (it's probably
            // blocked unless there's user interaction like a click), so we'll
            // use the `autofocus` attribute.
            let element = this.getElementForKeyboardFocus();
            element.autofocus = true;

            // `autofocus` only works if the element is newly inserted into the
            // document, so as an extra precaution, we'll also try to focus it
            // with JS.
            setTimeout(() => {
                this.grabKeyboardFocus();
            }, 50);

            // Note about dialogs/popups: The `PopupManager` takes care of
            // moving the keyboard focus to the dialog when it is opened.
        }
    }

    public grabKeyboardFocus(): void {
        this.getElementForKeyboardFocus().focus();
    }

    protected getElementForKeyboardFocus(): HTMLElement {
        return this.element;
    }
}
