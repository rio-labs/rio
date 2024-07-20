import { ComponentBase, ComponentState } from './componentBase';
import { applyIcon } from '../designApplication';
import { pixelsPerRem } from '../app';
import { InputBox } from '../inputBox';
import { markEventAsHandled } from '../eventHandling';

export type DropdownState = ComponentState & {
    _type_: 'Dropdown-builtin';
    optionNames?: string[];
    label?: string;
    accessibility_label?: string;
    selectedName?: string;
    is_sensitive?: boolean;
    is_valid?: boolean;
};

export class DropdownComponent extends ComponentBase {
    state: Required<DropdownState>;

    private inputBox: InputBox;
    private hiddenOptionsElement: HTMLElement;
    private popupElement: HTMLElement;
    private popupPptionsElement: HTMLElement;
    private isOpen: boolean = false;

    // The currently highlighted option, if any
    private highlightedOptionElement: HTMLElement | null = null;

    createElement(): HTMLElement {
        // Create root element
        let element = document.createElement('div');
        element.classList.add('rio-dropdown');

        // The dropdown is styled as an input box. Use the InputBox abstraction.
        this.inputBox = new InputBox({
            labelIsAlwaysSmall: true,
            // Don't make any elements clickable because they steal away the
            // focus from the <input> for a short while, which causes the
            // dropdown to close and immediately reopen
            connectClickHandlers: false,
        });
        element.appendChild(this.inputBox.outerElement);

        // In order to ensure the dropdown can actually fit its options, add a
        // hidden element that will contain a copy of all options. This element
        // will have no height, but but its width will impact the dropdown.
        this.hiddenOptionsElement = document.createElement('div');
        this.hiddenOptionsElement.classList.add('rio-dropdown-options');
        element.appendChild(this.hiddenOptionsElement);

        // Add an arrow icon
        let arrowElement = document.createElement('div');
        arrowElement.classList.add('rio-dropdown-arrow');
        applyIcon(arrowElement, 'material/expand_more');
        this.inputBox.suffixElement = arrowElement;

        // Create the popup
        this.popupElement = document.createElement('div');
        this.popupElement.tabIndex = -999; // Required for Chrome, sets `FocusEvent.relatedTarget`
        this.popupElement.classList.add('rio-dropdown-popup');

        this.popupPptionsElement = document.createElement('div');
        this.popupPptionsElement.classList.add('rio-dropdown-options');
        this.popupElement.appendChild(this.popupPptionsElement);

        document.body.appendChild(this.popupElement);

        // Connect events
        element.addEventListener(
            'mousedown',
            this._onMouseDown.bind(this),
            true
        );

        this.inputBox.inputElement.addEventListener(
            'keydown',
            this._onKeyDown.bind(this)
        );
        this.inputBox.inputElement.addEventListener(
            'input',
            this._onInputValueChange.bind(this)
        );
        this.inputBox.inputElement.addEventListener(
            'focusin',
            this._onFocusIn.bind(this)
        );
        this.inputBox.inputElement.addEventListener(
            'focusout',
            this._onFocusOut.bind(this)
        );

        return element;
    }

    private _onFocusIn(): void {
        // Clear the input text so that all options are shown in the dropdown
        this.inputBox.value = '';

        this.showPopup();
    }

    private _onFocusOut(event: FocusEvent): void {
        // When the input element loses focus, that means the user is done
        // entering input. Depending on whether they inputted a valid option,
        // either save it or reset.
        //
        // Careful: Clicking on a dropdown option with the mouse also causes us
        // to lose focus. If we close the popup too early, the click won't hit
        // anything.
        //
        // In Firefox the click is triggered before the focusout, so
        // that's no problem. But in Chrome, we have to check whether the focus
        // went to our popup element.
        if (
            event.relatedTarget instanceof HTMLElement &&
            event.relatedTarget.classList.contains('rio-dropdown-popup')
        ) {
            return;
        }

        this.trySubmitInput();
    }

    private trySubmitInput(): void {
        this.inputBox.unfocus();
        this.hidePopup();

        // Check if the inputted text corresponds to a valid option
        let inputText = this.inputBox.value;

        if (inputText === this.state.selectedName) {
            return;
        }

        if (this.state.optionNames.includes(inputText)) {
            this.state.selectedName = inputText;
            this.sendMessageToBackend({
                name: inputText,
            });
        } else {
            this.inputBox.value = this.state.selectedName;
        }
    }

    private cancelInput(): void {
        this.inputBox.value = this.state.selectedName;
        this.trySubmitInput();
    }

    private submitInput(optionName: string): void {
        this.inputBox.value = optionName;
        this.trySubmitInput();
    }

    private _onMouseDown(event: MouseEvent): void {
        if (!this.state.is_sensitive) {
            return;
        }

        // Not left click?
        if (event.button !== 0) {
            return;
        }

        // Eat the event
        markEventAsHandled(event);

        // Already open?
        if (this.isOpen) {
            this.cancelInput();
            return;
        }

        // Make the text input appear as active
        this.inputBox.focus();
    }

    _onKeyDown(event: KeyboardEvent): void {
        // Close the dropdown on escape
        if (event.key === 'Escape') {
            this.cancelInput();
        }

        // Enter -> select the highlighted option
        else if (event.key === 'Enter') {
            if (this.highlightedOptionElement !== null) {
                let mouseDownEvent = new MouseEvent('mousedown', {
                    bubbles: true,
                    cancelable: true,
                    view: window,
                });

                this.highlightedOptionElement.dispatchEvent(mouseDownEvent);
            }
        }

        // Move highlight up
        else if (event.key === 'ArrowDown') {
            let nextOption;

            if (this.highlightedOptionElement === null) {
                nextOption = this.popupPptionsElement.firstElementChild;
            } else {
                nextOption = this.highlightedOptionElement.nextElementSibling;

                if (nextOption === null) {
                    nextOption = this.popupPptionsElement.firstElementChild;
                }
            }

            this._highlightOption(nextOption as HTMLElement);
        }

        // Move highlight down
        else if (event.key === 'ArrowUp') {
            let nextOption: Element | null;

            if (this.highlightedOptionElement === null) {
                nextOption = this.popupPptionsElement.lastElementChild;
            } else {
                nextOption =
                    this.highlightedOptionElement.previousElementSibling;

                if (nextOption === null) {
                    nextOption = this.popupPptionsElement.lastElementChild;
                }
            }

            this._highlightOption(nextOption as HTMLElement);
        }
        // Any other key -> let the event propagate
        else {
            return;
        }

        markEventAsHandled(event);
    }

    private _onInputValueChange(): void {
        this._updateOptionsElement('popup');
    }

    private _highlightOption(optionElement: HTMLElement | null): void {
        // Remove the highlight from the previous option
        if (this.highlightedOptionElement !== null) {
            this.highlightedOptionElement.classList.remove(
                'rio-dropdown-option-highlighted'
            );
        }

        // Remember the new option and highlight it
        this.highlightedOptionElement = optionElement;

        if (optionElement !== null) {
            optionElement.classList.add('rio-dropdown-option-highlighted');
        }
    }

    private showPopup(): void {
        if (this.isOpen) {
            return;
        }

        this.isOpen = true;
        this._updateOptionsElement('popup');

        // Position & Animate
        let dropdownRect = this.element.getBoundingClientRect();
        let popupHeight = this.popupElement.scrollHeight;
        let windowHeight = window.innerHeight - 1; // innerHeight is rounded

        this.popupElement.style.removeProperty('top');
        this.popupElement.style.removeProperty('bottom');

        this.popupElement.style.width = `${dropdownRect.width}px`;

        const MARGIN_IF_ENTIRELY_ABOVE = 0.5 * pixelsPerRem;

        // Popup is larger than the window. Give it all the space that's
        // available.
        if (popupHeight >= windowHeight) {
            this.popupElement.style.overflowY = 'scroll';
            this.popupElement.style.top = '0';
            this.popupElement.classList.add('rio-dropdown-popup-above');
        }
        // Popup fits below the dropdown
        else if (dropdownRect.bottom + popupHeight <= windowHeight) {
            this.popupElement.style.overflowY = 'hidden';
            this.popupElement.style.top = `${dropdownRect.bottom}px`;
            this.popupElement.classList.remove('rio-dropdown-popup-above');
        }
        // Popup fits above the dropdown
        else if (dropdownRect.top - popupHeight >= MARGIN_IF_ENTIRELY_ABOVE) {
            this.popupElement.style.overflowY = 'hidden';
            this.popupElement.style.bottom = `${
                windowHeight - dropdownRect.top + MARGIN_IF_ENTIRELY_ABOVE
            }px`;
            this.popupElement.classList.add('rio-dropdown-popup-above');
        }
        // Popup doesn't fit above or below the dropdown. Center it as much
        // as possible
        else {
            this.popupElement.style.overflowY = 'hidden';
            let top =
                dropdownRect.top + dropdownRect.height / 2 - popupHeight / 2;
            if (top < 0) {
                top = 0;
            } else if (top + popupHeight > windowHeight) {
                top = windowHeight - popupHeight;
            }

            this.popupElement.style.top = `${top}px`;
            this.popupElement.classList.add('rio-dropdown-popup-above');
        }

        this.popupElement.style.left = dropdownRect.left + 'px';
    }

    private hidePopup(): void {
        if (!this.isOpen) {
            return;
        }

        this.isOpen = false;

        // Animate the disappearance
        this.popupElement.style.height = '0';
    }

    onDestruction(): void {
        super.onDestruction();
        this.popupElement.remove();
    }

    /// Find needle in haystack, returning a HTMLElement with the matched
    /// sections highlighted. If no match is found, return null. Needle must be
    /// lowercase.
    _highlightMatches(
        haystack: string,
        needleLower: string
    ): HTMLElement | null {
        // Special case: Empty needle matches everything, and would cause a hang
        // in the `while` loop below
        if (needleLower.length === 0) {
            const container = document.createElement('div');
            container.textContent = haystack;
            return container;
        }

        // Create a div element to hold the highlighted content
        const container = document.createElement('div');

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
            const span = document.createElement('span');
            span.className = 'rio-dropdown-option-highlighted';
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

    /// Update the visible options based on everything matching the search
    /// filter
    _updateOptionsElement(which: 'hidden' | 'popup'): void {
        // Prepare
        let element: HTMLElement;
        let needleLower: string;

        if (which == 'hidden') {
            element = this.hiddenOptionsElement;
            needleLower = '';
        } else {
            element = this.popupPptionsElement;
            needleLower = this.inputBox.value.toLowerCase();
        }

        // Clean up
        element.innerHTML = '';

        // Find matching options
        for (let optionName of this.state.optionNames) {
            let match = this._highlightMatches(optionName, needleLower);

            if (match === null) {
                continue;
            }

            match.classList.add('rio-dropdown-option');
            element.appendChild(match);

            match.addEventListener('mouseenter', () => {
                this._highlightOption(match);
            });

            // With a `click` handler, the <input> element loses focus for a
            // little while, which is noticeable because the floating label will
            // quickly move down and then back up. To avoid this, we use
            // `mousedown` instead.
            match.addEventListener('mousedown', (event) => {
                this.submitInput(optionName);
                markEventAsHandled(event);
            });
        }

        // If this is the hidden element, we're done
        if (which == 'hidden') {
            return;
        }

        // If only one option was found, highlight it
        if (element.children.length === 1) {
            this._highlightOption(element.firstElementChild as HTMLElement);
        }

        // Display an icon and resize the element
        //
        // For some reason the SVG has an explicit opacity set. Because of that,
        // using CSS isn't possible. Overwrite the opacity here.
        if (element.children.length === 0) {
            applyIcon(element, 'material/error').then(() => {
                (element.firstElementChild as SVGElement).style.opacity = '0.2';
            });

            this.popupElement.style.height = '7rem';
        } else {
            this.popupElement.style.height = `${element.scrollHeight}px`;
        }
    }

    updateElement(
        deltaState: DropdownState,
        latentComponents: Set<ComponentBase>
    ): void {
        super.updateElement(deltaState, latentComponents);

        // If the options have changed update the options element, and also
        // store its width
        if (deltaState.optionNames !== undefined) {
            // Store the new value, because it is about to be accessed
            this.state.optionNames = deltaState.optionNames;

            // Update the hidden options element
            this._updateOptionsElement('hidden');
            this.hiddenOptionsElement.style.height = '0';

            // Update the visible options element
            if (this.isOpen) {
                this._updateOptionsElement('popup');
            }
        }

        if (deltaState.label !== undefined) {
            this.inputBox.label = deltaState.label;
        }

        if (deltaState.accessibility_label !== undefined) {
            this.inputBox.accessibilityLabel = deltaState.accessibility_label;
        }

        if (deltaState.selectedName !== undefined) {
            this.inputBox.value = deltaState.selectedName;
        }

        if (deltaState.is_sensitive === true) {
            this.inputBox.isSensitive = true;
            this.element.classList.remove(
                'rio-disabled-input',
                'rio-switcheroo-disabled'
            );
        } else if (deltaState.is_sensitive === false) {
            this.inputBox.isSensitive = false;
            this.element.classList.add(
                'rio-disabled-input',
                'rio-switcheroo-disabled'
            );
            this.hidePopup();
        }

        if (deltaState.is_valid === false) {
            this.element.style.setProperty(
                '--rio-local-text-color',
                'var(--rio-global-danger-bg)'
            );
        } else if (deltaState.is_valid === true) {
            this.element.style.removeProperty('--rio-local-text-color');
        }
    }
}
