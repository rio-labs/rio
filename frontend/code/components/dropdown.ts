import { ComponentBase, ComponentState } from './componentBase';
import { applyIcon } from '../designApplication';
import {
    updateInputBoxNaturalHeight,
    updateInputBoxNaturalWidth,
} from '../inputBoxTools';
import { LayoutContext } from '../layouting';
import { pixelsPerRem, scrollBarSize } from '../app';
import { getTextDimensions } from '../layoutHelpers';
import { ClickHandler } from '../eventHandling';

// Make sure this is in sync with the CSS
const RESERVED_WIDTH_FOR_ARROW = 1.3;
const DROPDOWN_LIST_HORIZONTAL_PADDING = 1;

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

    private popupElement: HTMLElement;
    private optionsElement: HTMLElement;
    private inputElement: HTMLInputElement;

    private isOpen: boolean = false;

    // The currently highlighted option, if any
    private highlightedOptionElement: HTMLElement | null = null;

    private longestOptionWidth: number = 0;

    createElement(): HTMLElement {
        // Create the elements
        let element = document.createElement('div');
        element.classList.add('rio-dropdown', 'rio-input-box');

        element.innerHTML = `
            <input type="text" placeholder="">
            <div class="rio-input-box-label"></div>
            <div class="rio-dropdown-arrow"></div>
            <div class="rio-input-box-plain-bar"></div>
            <div class="rio-input-box-color-bar"></div>
        `;

        // Expose them as properties
        this.inputElement = element.querySelector('input') as HTMLInputElement;

        this.popupElement = document.createElement('div');
        this.popupElement.tabIndex = -999; // Required for Chrome, sets `FocusEvent.relatedTarget`
        this.popupElement.classList.add('rio-dropdown-popup');

        this.optionsElement = document.createElement('div');
        this.optionsElement.classList.add('rio-dropdown-options');
        this.popupElement.appendChild(this.optionsElement);

        // Add an arrow icon
        let arrowElement = element.querySelector(
            '.rio-dropdown-arrow'
        ) as HTMLElement;
        applyIcon(
            arrowElement,
            'material/expand-more',
            'var(--rio-local-text-color)'
        );

        // Connect events
        element.addEventListener(
            'mousedown',
            this._onMouseDown.bind(this),
            true
        );

        this.inputElement.addEventListener(
            'keydown',
            this._onKeyDown.bind(this)
        );
        this.inputElement.addEventListener(
            'input',
            this._onInputValueChange.bind(this)
        );
        this.inputElement.addEventListener(
            'focusin',
            this._onFocusIn.bind(this)
        );
        this.inputElement.addEventListener(
            'focusout',
            this._onFocusOut.bind(this)
        );

        return element;
    }

    private _onFocusIn(): void {
        // Clear the input text so that all options are shown in the dropdown
        this.inputElement.value = '';

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
        this.inputElement.blur();
        this.hidePopup();

        // Check if the inputted text corresponds to a valid option
        let inputText = this.inputElement.value;

        if (inputText === this.state.selectedName) {
            return;
        }

        if (this.state.optionNames.includes(inputText)) {
            this.state.selectedName = inputText;
            this.sendMessageToBackend({
                name: inputText,
            });
        } else {
            this.inputElement.value = this.state.selectedName;
        }
    }

    private cancelInput(): void {
        this.inputElement.value = this.state.selectedName;
        this.trySubmitInput();
    }

    private submitInput(optionName: string): void {
        this.inputElement.value = optionName;
        this.trySubmitInput();
    }

    private _onMouseDown(event: MouseEvent): void {
        // Not left click?
        if (event.button !== 0) {
            return;
        }

        // Eat the event
        event.stopPropagation();
        event.preventDefault();

        // Already open?
        if (this.isOpen) {
            this.cancelInput();
            return;
        }

        // Make the text input appear as active
        this.inputElement.focus();
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
            let nextOption;

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
        if (this.isOpen) {
            return;
        }

        this.isOpen = true;

        // In order to guarantee that the popup is on top of all components, it
        // must be added to the `body`. `z-index` alone isn't enough because it
        // only affects the "local stacking context".
        document.body.appendChild(this.popupElement);

        // Make sure to do this after the popup has been added to the DOM, so
        // that the scrollHeight is correct.
        this._updateOptionEntries();

        // Position & Animate
        let dropdownRect = this.element.getBoundingClientRect();
        let popupHeight = this.popupElement.scrollHeight;
        let windowHeight = window.innerHeight - 1; // innerHeight is rounded

        this.popupElement.style.removeProperty('top');
        this.popupElement.style.removeProperty('bottom');

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

        // Remove the element once the animation is done
        setTimeout(() => {
            if (!this.isOpen) {
                this.popupElement.remove();
            }
        }, 300);
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
        let needleLower = this.inputElement.value.toLowerCase();

        // Find matching options
        for (let optionName of this.state.optionNames) {
            let match = this._highlightMatches(optionName, needleLower);

            if (match === null) {
                continue;
            }

            match.classList.add('rio-dropdown-option');
            match.style.padding = `0.6rem ${DROPDOWN_LIST_HORIZONTAL_PADDING}rem`;
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
        let element = this.element;

        if (deltaState.optionNames !== undefined) {
            this.state.optionNames = deltaState.optionNames;

            this.longestOptionWidth = Math.max(
                0,
                ...this.state.optionNames.map(
                    (option) => getTextDimensions(option, 'text')[0]
                )
            );

            if (this.isOpen) {
                this._updateOptionEntries();
            }
        }

        if (deltaState.label !== undefined) {
            let labelElement = element.querySelector(
                '.rio-input-box-label'
            ) as HTMLElement;
            labelElement.textContent = deltaState.label;

            // Update the layout
            updateInputBoxNaturalHeight(this, deltaState.label, 0);
        }

        if (deltaState.selectedName !== undefined) {
            this.inputElement.value = deltaState.selectedName;
        }

        if (deltaState.is_sensitive === true) {
            element.classList.remove('rio-input-box-disabled');
        } else if (deltaState.is_sensitive === false) {
            element.classList.add('rio-input-box-disabled');
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

    updateNaturalWidth(ctx: LayoutContext): void {
        updateInputBoxNaturalWidth(
            this,
            this.longestOptionWidth +
                scrollBarSize +
                RESERVED_WIDTH_FOR_ARROW +
                2 * DROPDOWN_LIST_HORIZONTAL_PADDING
        );
    }

    updateAllocatedWidth(ctx: LayoutContext): void {
        this.popupElement.style.width = `${this.allocatedWidth}rem`;
    }

    updateNaturalHeight(ctx: LayoutContext): void {
        // This is set during the updateElement() call, so there is nothing to
        // do here.
    }
}
