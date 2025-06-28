import { ComponentBase, ComponentState, DeltaState } from "./componentBase";
import { applyIcon } from "../designApplication";
import { markEventAsHandled } from "../eventHandling";
import { ComponentStatesUpdateContext } from "../componentManagement";

const CALENDAR_WIDTH = 15.7;
const CALENDAR_HEIGHT = 17.8;

export type CalendarState = ComponentState & {
    _type_: "Calendar-builtin";
    selectedYear: number;
    selectedMonth: number; // [1, 12]
    selectedDay: number; // [1, ...]
    monthNamesLong: Array<string>;
    dayNamesLong: Array<string>;
    firstDayOfWeek: number;
    is_sensitive: boolean;
};

export class CalendarComponent extends ComponentBase<CalendarState> {
    // Internal HTML Elements
    private prevYearButton: HTMLElement;
    private prevMonthButton: HTMLElement;

    private yearMonthDisplay: HTMLElement;

    private nextMonthButton: HTMLElement;
    private nextYearButton: HTMLElement;

    private grid: HTMLElement;

    // These store the displayed year and month. This is in contrast to the
    // *selected* year and month, which are stored in the state.
    private displayedYear: number;
    private displayedMonth: number; // 1 to 12

    createElement(context: ComponentStatesUpdateContext): HTMLElement {
        // Create the HTML structure
        let element = document.createElement("div");
        element.classList.add("rio-calendar");

        element.innerHTML = `
            <div class="rio-calendar-inner" style="width: ${CALENDAR_WIDTH}rem; height: ${CALENDAR_HEIGHT}rem;">
                <div class="rio-calendar-header">
                    <div class="rio-calendar-button rio-calendar-prev-year-button"></div>
                    <div class="rio-calendar-button rio-calendar-prev-month-button"></div>
                    <div class="rio-calendar-year-month-display"></div>
                    <div class="rio-calendar-button rio-calendar-next-month-button"></div>
                    <div class="rio-calendar-button rio-calendar-next-year-button"></div>
                </div>
                <div class="rio-calendar-grid"></div>
            </div>
        `;

        // Expose the elements
        let innerElement = element.firstElementChild as HTMLElement;

        let headerElement: HTMLElement;
        [headerElement, this.grid] = Array.from(
            innerElement.children
        ) as HTMLElement[];

        [
            this.prevYearButton,
            this.prevMonthButton,
            this.yearMonthDisplay,
            this.nextMonthButton,
            this.nextYearButton,
        ] = Array.from(headerElement.children) as HTMLElement[];

        // Initialize icons
        applyIcon(this.prevYearButton, "material/keyboard_double_arrow_left");
        applyIcon(this.prevMonthButton, "material/keyboard_arrow_left");
        applyIcon(this.nextMonthButton, "material/keyboard_arrow_right");
        applyIcon(this.nextYearButton, "material/keyboard_double_arrow_right");

        // Initialize the state
        this.displayedYear = this.state.selectedYear;
        this.displayedMonth = this.state.selectedMonth;

        // Initialize the content
        this.displayedValuesChanged();

        // Connect to events
        this.prevMonthButton.addEventListener(
            "click",
            this.onPressPrevMonth.bind(this)
        );
        this.nextMonthButton.addEventListener(
            "click",
            this.onPressNextMonth.bind(this)
        );

        this.prevYearButton.addEventListener(
            "click",
            this.onPressPrevYear.bind(this)
        );
        this.nextYearButton.addEventListener(
            "click",
            this.onPressNextYear.bind(this)
        );

        return element;
    }

    updateElement(
        deltaState: DeltaState<CalendarState>,
        context: ComponentStatesUpdateContext
    ): void {
        super.updateElement(deltaState, context);

        if (deltaState.is_sensitive !== undefined) {
            if (deltaState.is_sensitive) {
                this.element.classList.remove(
                    "rio-disabled-input",
                    "rio-switcheroo-disabled"
                );
            } else {
                this.element.classList.add(
                    "rio-disabled-input",
                    "rio-switcheroo-disabled"
                );
            }
        }

        // Apply latent changes to the state
        let dateChanged: boolean = false;

        if (deltaState.selectedYear !== undefined) {
            this.state.selectedYear = deltaState.selectedYear;
            this.displayedYear = this.state.selectedYear;

            dateChanged = true;
        }

        if (deltaState.selectedMonth !== undefined) {
            this.state.selectedMonth = deltaState.selectedMonth;
            this.displayedMonth = this.state.selectedMonth;

            dateChanged = true;
        }

        if (deltaState.selectedDay !== undefined) {
            this.state.selectedDay = deltaState.selectedDay;

            dateChanged = true;
        }

        // Then update the UI
        if (dateChanged) {
            this.displayedValuesChanged();
        }
    }

    displayedValuesChanged(): void {
        // Update the year and month display
        let monthName = this.state.monthNamesLong[this.displayedMonth - 1];
        this.yearMonthDisplay.textContent = `${monthName} ${this.displayedYear}`;

        // Update the grid
        this.updateGrid();
    }

    updateGrid(): void {
        // Clear the grid
        this.grid.innerHTML = "";

        // Add the day names
        for (let i = 0; i < 7; ++i) {
            let nameIndex = (i + this.state.firstDayOfWeek) % 7;
            let longName = this.state.dayNamesLong[nameIndex];
            let shortName = longName.slice(0, 1); // Don't crash if the name is too short

            let cell = document.createElement("div");
            cell.classList.add("rio-calendar-day-name");
            cell.textContent = shortName;
            this.grid.appendChild(cell);
        }

        // The first day of the month isn't placed in the first cell, because
        // it must line up with the correct day of the week. Prepare a shift
        // value to account for this.
        //
        // Since this is modular arithmetic and modulus is weird with negative
        // numbers, subtraction is done by _adding_.
        let firstThisMonth = new Date(
            this.displayedYear,
            this.displayedMonth - 1,
            1
        );
        let dayShift =
            (firstThisMonth.getDay() - this.state.firstDayOfWeek + 6) % 7;

        // Prepare a list of all days to display
        //
        // Each day has the following values:
        //
        // - year
        // - month
        // - day
        // - CSS classes to apply
        let days: Array<[number, number, number, Array<string>]> = [];

        // Subtract one, to account for the fact that the first day is 1 instead
        // of zero. Note that this is a real subtraction. This is so that (day
        // shift + 1) never ever becomes 7, as that would lead to an empty first
        // row.
        dayShift -= 1;

        // Add the final days from the previous month
        let numDaysPrevMonth = new Date(
            this.displayedYear,
            this.displayedMonth - 1,
            0
        ).getDate();

        let numEmptyCells = dayShift + 1;
        let prevYear =
            this.displayedMonth === 1
                ? this.displayedYear - 1
                : this.displayedYear;
        let prevMonth =
            this.displayedMonth === 1 ? 12 : this.displayedMonth - 1;

        for (
            let i = numDaysPrevMonth - numEmptyCells + 1;
            i <= numDaysPrevMonth;
            ++i
        ) {
            days.push([
                prevYear,
                prevMonth,
                i,
                ["rio-calendar-day", "rio-calendar-day-other-month"],
            ]);
        }

        // Add the days of this month
        let daysThisMonth = new Date(
            this.displayedYear,
            this.displayedMonth, // This will correctly overflow to the next year
            0
        ).getDate();

        let selectedDayIndex =
            this.state.selectedYear === this.displayedYear &&
            this.state.selectedMonth === this.displayedMonth
                ? this.state.selectedDay
                : -1;

        for (let i = 1; i <= daysThisMonth; ++i) {
            let classes = ["rio-calendar-day"];

            if (i === selectedDayIndex) {
                classes.push("rio-calendar-selected-day");
            }

            days.push([this.displayedYear, this.displayedMonth, i, classes]);
        }

        // Add the first few days from the next month
        let numEmptyCellsEnd = 7 - ((daysThisMonth + dayShift + 1) % 7);
        numEmptyCellsEnd = numEmptyCellsEnd === 7 ? 0 : numEmptyCellsEnd;

        let nextYear =
            this.displayedMonth === 12
                ? this.displayedYear + 1
                : this.displayedYear;

        let nextMonth =
            this.displayedMonth === 12 ? 1 : this.displayedMonth + 1;

        for (let i = 1; i <= numEmptyCellsEnd; ++i) {
            days.push([
                nextYear,
                nextMonth,
                i,
                ["rio-calendar-day", "rio-calendar-day-other-month"],
            ]);
        }

        // Populate the grid
        for (let i = 0; i < days.length; ++i) {
            let [year, month, day, classes] = days[i];

            // Spawn the element
            let cell = document.createElement("div");
            this.grid.appendChild(cell);
            cell.classList.add(...classes);
            cell.textContent = day.toString();

            // Detect clicks
            cell.addEventListener("click", () =>
                this.onSelectDay(year, month, day)
            );
        }
    }

    onPressPrevMonth(event: MouseEvent): void {
        if (!this.state.is_sensitive) {
            return;
        }

        if (this.displayedMonth === 1) {
            this.displayedMonth = 12;
            --this.displayedYear;
        } else {
            --this.displayedMonth;
        }

        this.displayedValuesChanged();
        markEventAsHandled(event);
    }

    onPressNextMonth(event: MouseEvent): void {
        if (!this.state.is_sensitive) {
            return;
        }

        if (this.displayedMonth === 12) {
            this.displayedMonth = 1;
            ++this.displayedYear;
        } else {
            ++this.displayedMonth;
        }

        this.displayedValuesChanged();
        markEventAsHandled(event);
    }

    onPressPrevYear(event: MouseEvent): void {
        if (!this.state.is_sensitive) {
            return;
        }

        --this.displayedYear;
        this.displayedValuesChanged();

        markEventAsHandled(event);
    }

    onPressNextYear(event: MouseEvent): void {
        if (!this.state.is_sensitive) {
            return;
        }

        ++this.displayedYear;
        this.displayedValuesChanged();

        markEventAsHandled(event);
    }

    onSelectDay(year: number, month: number, day: number): void {
        if (!this.state.is_sensitive) {
            return;
        }

        // Switch to the selected day
        this.state.selectedYear = year;
        this.state.selectedMonth = month;
        this.state.selectedDay = day;

        // Notify the backend
        this.sendMessageToBackend({
            year: this.state.selectedYear,
            month: this.state.selectedMonth,
            day: this.state.selectedDay,
        });

        // Update the grid
        this.updateGrid();
    }
}
