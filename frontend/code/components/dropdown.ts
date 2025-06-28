import { DeltaState } from "./componentBase";
import { applyIcon } from "../designApplication";
import { InputBox, InputBoxStyle } from "../inputBox";
import { markEventAsHandled } from "../eventHandling";
import { PopupManager } from "../popupManager";
import {
    KeyboardFocusableComponent,
    KeyboardFocusableComponentState,
} from "./keyboardFocusableComponent";
import { DropdownPositioner } from "../popupPositioners";
import { ComponentStatesUpdateContext } from "../componentManagement";

export type DropdownState = KeyboardFocusableComponentState & {
    _type_: "Dropdown-builtin";
    optionNames: string[];
    label: string;
    accessibility_label: string;
    style: InputBoxStyle;
    selectedName: string;
    is_sensitive: boolean;
    is_valid: boolean;
};

export class DropdownComponent extends KeyboardFocusableComponent<DropdownState> {
    private inputBox: InputBox;
    private hiddenOptionsElement: HTMLElement;
    private popupElement: HTMLElement;
    private popupOptionsElement: HTMLElement;
    private mobileLabelElement: HTMLElement;

    private popupManager: PopupManager;
    private useMobilePopup: boolean;

    // The currently highlighted option, if any
    private highlightedOptionElement: HTMLElement | null = null;

    createElement(context: ComponentStatesUpdateContext): HTMLElement {
        // Create root element
        let element = document.createElement("div");
        element.classList.add("rio-dropdown");

        // The dropdown is styled as an input box, so use the InputBox
        // abstraction.
        this.inputBox = new InputBox({
            labelIsAlwaysSmall: true,
            // Don't make any elements clickable because they steal away the
            // focus from the <input> for a short while, which causes the
            // dropdown to close and immediately reopen
            connectClickHandlers: false,
        });
        element.appendChild(this.inputBox.outerElement);
        this.inputBox.outerElement.role = "combobox";

        // In order to ensure the dropdown can actually fit its options, add a
        // hidden element that will contain a copy of all options. This element
        // will have no height, but but its width will push the dropdown to be
        // wide enough to fit all texts.
        this.hiddenOptionsElement = document.createElement("div");
        this.hiddenOptionsElement.classList.add("rio-dropdown-options");
        element.appendChild(this.hiddenOptionsElement);

        // Add an arrow icon
        let arrowElement = document.createElement("div");
        arrowElement.classList.add("rio-dropdown-arrow");
        applyIcon(arrowElement, "material/expand_more");
        this.inputBox.suffixElement = arrowElement;

        // Create the popup content
        this.popupElement = document.createElement("div");
        this.popupElement.classList.add("rio-dropdown-popup");
        this.popupElement.tabIndex = -999; // Required for Chrome, sets `FocusEvent.relatedTarget`
        this.popupElement.id = `rio-dropdown-popup-${this.id}`;
        this.popupElement.role = "listbox";

        let popupScrollerElement = document.createElement("div");
        popupScrollerElement.classList.add("rio-dropdown-popup-scroller");
        this.popupElement.appendChild(popupScrollerElement);

        this.mobileLabelElement = document.createElement("div");
        this.mobileLabelElement.classList.add("rio-dropdown-mobile-label");
        popupScrollerElement.appendChild(this.mobileLabelElement);

        this.popupOptionsElement = document.createElement("div");
        this.popupOptionsElement.classList.add("rio-dropdown-options");
        popupScrollerElement.appendChild(this.popupOptionsElement);

        // Connect events
        element.addEventListener(
            "pointerdown",
            this._onPointerDown.bind(this),
            true
        );
        element.addEventListener("click", markEventAsHandled);

        this.inputBox.inputElement.addEventListener(
            "keydown",
            this._onKeyDown.bind(this)
        );
        this.inputBox.inputElement.addEventListener(
            "input",
            this._onInputValueChange.bind(this)
        );
        this.inputBox.inputElement.addEventListener(
            "focusin",
            this._onFocusIn.bind(this)
        );
        this.inputBox.inputElement.addEventListener(
            "focusout",
            this._onFocusOut.bind(this)
        );

        // Initialize a popup manager
        this.popupManager = new PopupManager({
            anchor: element,
            content: this.popupElement,
            positioner: new DropdownPositioner(),
            modal: false,
            userClosable: true,
            onUserClose: this.hidePopupDontCommit.bind(this),
        });

        return element;
    }

    /// With a `click` handler, the <input> element loses focus for a little
    /// while, which is noticeable because the floating label will quickly move
    /// down and then back up. To avoid this, we use `pointerdown` instead. But
    /// on mobile this prevents scrolling, so mobile uses `click`.
    private getOptionSelectEvent(): string {
        return this.useMobilePopup ? "click" : "pointerdown";
    }

    /// Open the dropdown and show all options
    private _onPointerDown(event: PointerEvent): void {
        // Do we care?
        if (!this.state.is_sensitive || event.button !== 0) {
            return;
        }

        // Eat the event
        markEventAsHandled(event);

        // If the popup was already open, close it
        if (this.popupManager.isOpen) {
            this.hidePopupDontCommit();
            return;
        }

        // Otherwise focus it. The focus handler will do the remaining work.
        this.inputBox.focus();
    }

    private _onFocusIn(): void {
        // Clear the input text so that all options are shown in the dropdown
        this.inputBox.value = "";

        // Show the popup
        this.showPopup();
    }

    private _onFocusOut(event: FocusEvent): void {
        // Careful: Clicking on a dropdown option also causes us to lose focus.
        // If we close the popup too early, the click won't hit anything.
        //
        // In Firefox the click is triggered before the focusout, so
        // that's no problem. But in Chrome, we have to check whether the focus
        // went to our popup element.
        if (
            event.relatedTarget instanceof HTMLElement &&
            event.relatedTarget.classList.contains("rio-dropdown-popup")
        ) {
            return;
        }

        // When the input element loses focus, that means the user is done
        // entering input. Depending on whether they have put in a valid option,
        // either save it or reset.
        this.hidePopupAndCommit(this.inputBox.value);
    }

    _onKeyDown(event: KeyboardEvent): void {
        // Escape: close the popup without committing
        if (event.key === "Escape") {
            this.hidePopupDontCommit();
        }

        // Enter: select the highlighted option
        else if (event.key === "Enter") {
            if (this.highlightedOptionElement !== null) {
                let pointerDownEvent = new PointerEvent(
                    this.getOptionSelectEvent(),
                    {
                        bubbles: true,
                        cancelable: true,
                        view: window,
                    }
                );

                this.highlightedOptionElement.dispatchEvent(pointerDownEvent);
            }
        }

        // Move highlight down
        else if (event.key === "ArrowDown") {
            let nextOption: Element | null;

            if (this.highlightedOptionElement === null) {
                nextOption = this.popupOptionsElement.firstElementChild;
            } else {
                nextOption = this.highlightedOptionElement.nextElementSibling;

                if (nextOption === null) {
                    nextOption = this.popupOptionsElement.firstElementChild;
                }
            }

            this._highlightOption(nextOption as HTMLElement | null);
        }

        // Move highlight up
        else if (event.key === "ArrowUp") {
            let nextOption: Element | null;

            if (this.highlightedOptionElement === null) {
                nextOption = this.popupOptionsElement.lastElementChild;
            } else {
                nextOption =
                    this.highlightedOptionElement.previousElementSibling;

                if (nextOption === null) {
                    nextOption = this.popupOptionsElement.lastElementChild;
                }
            }

            this._highlightOption(nextOption as HTMLElement);
        }

        // Any other key: let the event propagate
        else {
            return;
        }

        markEventAsHandled(event);
    }

    private _onInputValueChange(): void {
        this._updatePopupOptionsElement();
    }

    private _highlightOption(optionElement: HTMLElement | null): void {
        // Remove the highlight from the previous option
        if (this.highlightedOptionElement !== null) {
            this.highlightedOptionElement.classList.remove(
                "rio-dropdown-option-highlighted"
            );
        }

        // Remember the new option and highlight it
        this.highlightedOptionElement = optionElement;

        if (optionElement !== null) {
            optionElement.classList.add("rio-dropdown-option-highlighted");
        }
    }

    /// Opens the popup if it isn't open already. Does nothing otherwise.
    private showPopup(): void {
        // Already open?
        if (this.popupManager.isOpen) {
            return;
        }

        // Unfortunately there's a bunch of code that needs to know this
        // information *later*, so we have to store it
        this.useMobilePopup = DropdownPositioner.useMobileMode();

        // Reset the highlighted option
        this._updatePopupOptionsElement();

        // Configure the popup for desktop/mobile
        if (this.useMobilePopup) {
            this.inputBox.inputElement.readOnly = true;
            this.popupManager.modal = true;
        } else {
            this.inputBox.inputElement.readOnly = false;
            this.popupManager.modal = false;
        }

        // Tell the popup manager to show the popup
        //
        // This must happen after the options are updated, because the popup
        // manager needs knowledge about the size of the options.
        this.popupManager.isOpen = true;

        // Update ARIA attributes
        this.inputBox.outerElement.ariaExpanded = "true";
        this.inputBox.outerElement.ariaHasPopup = "listbox";
        this.inputBox.outerElement.setAttribute(
            "aria-owns",
            this.popupElement.id
        );
        this.inputBox.outerElement.setAttribute(
            "aria-activedescendant",
            this.popupElement.id
        );
    }

    private closePopup(): void {
        // Close the popup
        this.popupManager.isOpen = false;

        // Update ARIA attributes
        this.inputBox.outerElement.ariaExpanded = "false";
        this.inputBox.outerElement.ariaHasPopup = "false";
        this.inputBox.outerElement.removeAttribute("aria-owns");
        this.inputBox.outerElement.removeAttribute("aria-activedescendant");
    }

    /// Close the popup and apply the selected option. Does nothing if the popup
    /// isn't open, or the given option is invalid.
    private hidePopupAndCommit(newOptionName: string): void {
        // Already closed?
        if (!this.popupManager.isOpen) {
            return;
        }

        this.closePopup();

        // No longer focus the input box
        this.inputBox.unfocus();

        // If the chosen text hasn't changed, we only need to reset the text in
        // the text box
        if (newOptionName === this.state.selectedName) {
            this.inputBox.value = newOptionName;
            return;
        }

        // If the given option is valid, tell python about the new value
        if (this.state.optionNames.includes(newOptionName)) {
            this.inputBox.value = newOptionName;
            this.state.selectedName = newOptionName;
            this.sendMessageToBackend({
                name: newOptionName,
            });
        }

        // Nope, revert
        else {
            this.inputBox.value = this.state.selectedName;
        }
    }

    /// Closes the popup without applying the selected option. Does nothing if
    /// the popup isn't open.
    private hidePopupDontCommit(): void {
        // Note that there is no check here for whether the dropdown is already
        // closed. That's because this function is called by the popup manager
        // when closed by the user (e.g. clicking outside the popup), at which
        // point the manager may already consider itself closed. That's fine,
        // because this function doesn't do anything fancy and can be called
        // as often as you like.

        // Make sure the popup isn't visible
        this.closePopup();

        // Revert the text input to what was already selected
        this.inputBox.value = this.state.selectedName;

        // Make sure to defocus the input box, so that clicking on it again
        // re-opens the popup.
        this.inputBox.unfocus();

        // There is no need to tell Python, since nothing has changed.
    }

    onDestruction(): void {
        super.onDestruction();
        this.popupManager.destroy();
    }

    /// Find `needleLower` in `haystack`, returning a HTMLElement with the
    /// matched sections highlighted. If no match is found, return null. The
    /// needle must be lowercase.
    _highlightMatches(
        haystack: string,
        needleLower: string
    ): HTMLElement | null {
        // Special case: Empty needles matches everything, and would cause a
        // hang in the `while` loop below
        if (needleLower.length === 0) {
            const container = document.createElement("div");
            container.textContent = haystack;
            return container;
        }

        // Create a div element to hold the highlighted content
        const container = document.createElement("div");

        // Start searching
        let startIndex = 0;
        let haystackLower = haystack.toLowerCase();
        let index = haystackLower.indexOf(needleLower, startIndex);

        while (index !== -1) {
            // Add the text before the match as a text node
            container.appendChild(
                document.createTextNode(haystack.substring(startIndex, index))
            );

            // Add the matched portion as a highlighted span
            const span = document.createElement("span");
            span.className = "rio-dropdown-option-highlighted";
            span.textContent = haystack.substring(
                index,
                index + needleLower.length
            );
            container.appendChild(span);

            // Update the start index for the next search
            startIndex = index + needleLower.length;

            // Find the next occurrence of needle in haystack
            index = haystackLower.indexOf(needleLower, startIndex);
        }

        // Add any remaining text after the last match
        container.appendChild(
            document.createTextNode(haystack.substring(startIndex))
        );

        // Was anything found?
        return container.children.length === 0 ? null : container;
    }

    _updateHiddenOptionsElement(): void {
        this.hiddenOptionsElement.innerHTML = "";

        for (let optionName of this.state.optionNames) {
            let child = document.createElement("div");
            child.classList.add("rio-dropdown-option");
            child.textContent = optionName;
            this.hiddenOptionsElement.appendChild(child);
        }
    }

    /// Rebuilds the popup options element, filtering the visible options to
    /// those matching the input text. This also updates the matches visually
    /// where appropriate.
    _updatePopupOptionsElement(): void {
        // Prepare
        let needleLower = this.inputBox.value.toLowerCase();

        // Clean up
        this.popupOptionsElement.innerHTML = "";

        // Find matching options
        for (let optionName of this.state.optionNames) {
            let match = this._highlightMatches(optionName, needleLower);

            if (match === null) {
                continue;
            }

            match.classList.add("rio-dropdown-option");
            match.role = "option";
            this.popupOptionsElement.appendChild(match);

            match.addEventListener("pointerenter", () => {
                this._highlightOption(match);
            });

            match.addEventListener(
                this.getOptionSelectEvent(),
                (event: Event) => {
                    this.hidePopupAndCommit(optionName);
                    markEventAsHandled(event);
                }
            );
        }

        // If only one option was found, highlight it
        if (this.popupOptionsElement.children.length === 1) {
            this._highlightOption(
                this.popupOptionsElement.firstElementChild as HTMLElement
            );
        }

        // Display an icon and resize the element
        //
        // For some reason the SVG has an explicit opacity set. Because of that,
        // using CSS isn't possible. Overwrite the opacity here.
        if (this.popupOptionsElement.children.length === 0) {
            applyIcon(this.popupOptionsElement, "material/error").then(() => {
                (
                    this.popupOptionsElement.firstElementChild as SVGElement
                ).style.opacity = "0.2";
            });

            this.popupElement.style.height = "7rem";
        } else {
            this.popupElement.style.height = "unset";
        }
    }

    updateElement(
        deltaState: DeltaState<DropdownState>,
        context: ComponentStatesUpdateContext
    ): void {
        super.updateElement(deltaState, context);

        // If the options have changed update the options element, and also
        // store its width
        if (deltaState.optionNames !== undefined) {
            // Store the new value, because it is about to be accessed
            this.state.optionNames = deltaState.optionNames;

            // Update the hidden options element
            this._updateHiddenOptionsElement();

            // Update the visible options element
            if (this.popupManager.isOpen) {
                this._updatePopupOptionsElement();
            }
        }

        if (deltaState.label !== undefined) {
            this.inputBox.label = deltaState.label;
            this.mobileLabelElement.textContent = deltaState.label;
        }

        if (deltaState.accessibility_label !== undefined) {
            this.inputBox.accessibilityLabel = deltaState.accessibility_label;
        }

        if (deltaState.style !== undefined) {
            this.inputBox.style = deltaState.style;
        }

        if (deltaState.selectedName !== undefined) {
            this.inputBox.value = deltaState.selectedName;
        }

        if (deltaState.is_sensitive === true) {
            this.inputBox.isSensitive = true;
            this.element.classList.remove(
                "rio-disabled-input",
                "rio-switcheroo-disabled"
            );
        } else if (deltaState.is_sensitive === false) {
            this.inputBox.isSensitive = false;
            this.element.classList.add(
                "rio-disabled-input",
                "rio-switcheroo-disabled"
            );
            this.hidePopupDontCommit();
        }

        if (deltaState.is_valid === false) {
            this.element.style.setProperty(
                "--rio-local-text-color",
                "var(--rio-global-danger-bg)"
            );
        } else if (deltaState.is_valid === true) {
            this.element.style.removeProperty("--rio-local-text-color");
        }
    }
}
