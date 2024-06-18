import { ComponentBase, ComponentState } from './componentBase';
import { applyIcon } from '../designApplication';
import { pixelsPerRem } from '../app';
import { InputBox } from '../inputBox';
import { PopupManager } from '../popupManager';

export type DropdownState = ComponentState & {
    _type_: 'Dropdown-builtin';
    optionNames?: string[];
    label?: string;
    selectedName?: string;
    is_sensitive?: boolean;
    is_valid?: boolean;
};

export class DropdownComponent extends ComponentBase {
    state: Required<DropdownState>;

    private inputBox: InputBox;
    private popupManager: PopupManager;
    private popupElement: HTMLElement;
    private optionsElement: HTMLElement;

    // The currently highlighted option, if any
    private highlightedOptionElement: HTMLElement | null = null;

    createElement(): HTMLElement {
        // Create the elements
        let element = document.createElement('div');
        element.classList.add('rio-dropdown');

        this.inputBox = new InputBox(element);

        // Add an arrow icon
        let arrowElement = document.createElement('div');
        arrowElement.classList.add('rio-dropdown-arrow');
        applyIcon(
            arrowElement,
            'material/expand-more',
            'var(--rio-local-text-color)'
        );
        this.inputBox.suffixElement = arrowElement;

        // Create the popup
        this.popupElement = document.createElement('div');
        this.popupElement.tabIndex = -999; // Required for Chrome, sets `FocusEvent.relatedTarget`
        this.popupElement.classList.add('rio-dropdown-popup');

        this.optionsElement = document.createElement('div');
        this.optionsElement.classList.add('rio-dropdown-options');
        this.popupElement.appendChild(this.optionsElement);

        this.popupManager = new PopupManager(
            element,
            this.popupElement,
            'bottom',
            0.5,
            0
        );

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
        event.stopPropagation();
        event.preventDefault();

        // Already open?
        if (this.popupManager.isOpen) {
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
                this.highlightedOptionElement.click();
            }
        }

        // Move highlight up
        else if (event.key === 'ArrowDown') {
            let nextOption;

            if (this.highlightedOptionElement === null) {
                nextOption = this.optionsElement.firstElementChild;
            } else {
                nextOption = this.highlightedOptionElement.nextElementSibling;

                if (nextOption === null) {
                    nextOption = this.optionsElement.firstElementChild;
                }
            }

            this._highlightOption(nextOption as HTMLElement);
        }

        // Move highlight down
        else if (event.key === 'ArrowUp') {
            let nextOption: Element | null;

            if (this.highlightedOptionElement === null) {
                nextOption = this.optionsElement.lastElementChild;
            } else {
                nextOption =
                    this.highlightedOptionElement.previousElementSibling;

                if (nextOption === null) {
                    nextOption = this.optionsElement.lastElementChild;
                }
            }

            this._highlightOption(nextOption as HTMLElement);
        }
        // Any other key -> let the event propagate
        else {
            return;
        }

        event.stopPropagation();
        event.preventDefault();
    }

    private _onInputValueChange(): void {
        this._updateOptionEntries();
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
        if (this.popupManager.isOpen) {
            return;
        }

        this._updateOptionEntries();

        // Resize & Animate
        let dropdownRect = this.element.getBoundingClientRect();

        this.popupElement.style.minWidth = dropdownRect.width + 'px';

        let popupHeight = this.popupElement.scrollHeight;
        let windowHeight = window.innerHeight - 1; // innerHeight is rounded

        const MARGIN_IF_ENTIRELY_ABOVE = 0.5 * pixelsPerRem;

        // Popup is larger than the window. Give it all the space that's
        // available.
        if (popupHeight >= windowHeight) {
            this.popupElement.style.overflowY = 'scroll';
            this.popupElement.classList.add('rio-dropdown-popup-above');
        }
        // Popup fits below the dropdown
        else if (dropdownRect.bottom + popupHeight <= windowHeight) {
            this.popupElement.style.overflowY = 'hidden';
            this.popupElement.classList.remove('rio-dropdown-popup-above');
        }
        // Popup fits above the dropdown
        else if (dropdownRect.top - popupHeight >= MARGIN_IF_ENTIRELY_ABOVE) {
            this.popupElement.style.overflowY = 'hidden';
            this.popupElement.classList.add('rio-dropdown-popup-above');
        }
        // Popup doesn't fit above or below the dropdown. Center it as much
        // as possible
        else {
            this.popupElement.style.overflowY = 'hidden';
            this.popupElement.classList.add('rio-dropdown-popup-above');
        }

        this.popupManager.isOpen = true;
    }

    private hidePopup(): void {
        if (!this.popupManager.isOpen) {
            return;
        }

        this.popupManager.isOpen = false;

        // Animate the disappearance
        this.popupElement.style.height = '0';

        // Remove the element once the animation is done
        setTimeout(() => {
            if (!this.popupManager.isOpen) {
                this.popupElement.remove();
            }
        }, 300);
    }

    onDestruction(): void {
        super.onDestruction();
        this.popupManager.destroy();
    }

    /// Find needle in haystack, returning a HTMLElement with the matched
    /// sections highlighted. If no match is found, return null. Needle must be
    /// lowercase.
    _highlightMatches(
        haystack: string,
        needleLower: string
    ): HTMLElement | null {
        // Special case: Empty needle matches everything, and would cause a hang
        // in the while loop below
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
            span.className = 'rio-dropdown-option-highlight';
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
    _updateOptionEntries(): void {
        this.optionsElement.innerHTML = '';
        let needleLower = this.inputBox.value.toLowerCase();

        // Find matching options
        for (let optionName of this.state.optionNames) {
            let match = this._highlightMatches(optionName, needleLower);

            if (match === null) {
                continue;
            }

            match.classList.add('rio-dropdown-option');
            this.optionsElement.appendChild(match);

            match.addEventListener('mouseenter', () => {
                this._highlightOption(match);
            });

            match.addEventListener('click', (event) => {
                this.submitInput(optionName);
                event.stopPropagation();
            });
        }

        // If only one option was found, highlight it
        if (this.optionsElement.children.length === 1) {
            this._highlightOption(
                this.optionsElement.firstElementChild as HTMLElement
            );
        }

        // Was anything found?
        if (this.optionsElement.children.length === 0) {
            applyIcon(
                this.optionsElement,
                'material/error',
                'var(--rio-local-text-color)'
            );

            // The icon is loaded asynchronously, so make sure to give the
            // element some space
            this.popupElement.style.height = '7rem';
        } else {
            // Resize the popup to fit the new content
            this.popupElement.style.height = `${this.optionsElement.scrollHeight}px`;
        }
    }

    updateElement(
        deltaState: DropdownState,
        latentComponents: Set<ComponentBase>
    ): void {
        super.updateElement(deltaState, latentComponents);

        let element = this.element;

        if (deltaState.optionNames !== undefined) {
            this.state.optionNames = deltaState.optionNames;

            if (this.popupManager.isOpen) {
                this._updateOptionEntries();
            }
        }

        if (deltaState.label !== undefined) {
            let labelElement = element.querySelector(
                '.rio-input-box-label'
            ) as HTMLElement;
            labelElement.textContent = deltaState.label;
        }

        if (deltaState.selectedName !== undefined) {
            this.inputBox.value = deltaState.selectedName;
        }

        if (deltaState.is_sensitive === true) {
            this.inputBox.isSensitive = true;
            element.classList.remove(
                'rio-disabled-input',
                'rio-switcheroo-disabled'
            );
        } else if (deltaState.is_sensitive === false) {
            this.inputBox.isSensitive = false;
            element.classList.add(
                'rio-disabled-input',
                'rio-switcheroo-disabled'
            );
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
