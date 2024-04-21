import { Color } from '../dataModels';
import { ComponentBase, ComponentState } from './componentBase';
import { hsvToRgb, rgbToHsv, rgbToHex, rgbaToHex } from '../colorConversion';
import { LayoutContext } from '../layouting';
import { getElementDimensions } from '../layoutHelpers';

export type ColorPickerState = ComponentState & {
    _type_: 'ColorPicker-builtin';
    color?: Color;
    pick_opacity?: boolean;
};

export class ColorPickerComponent extends ComponentBase {
    state: Required<ColorPickerState>;

    private colorSquare: HTMLElement;
    private squareKnob: HTMLElement;

    private hueBarOuter: HTMLElement;
    private hueBarInner: HTMLElement;
    private hueIndicator: HTMLElement;

    private opacityBarOuter: HTMLElement;
    private opacityBarInner: HTMLElement;
    private opacityIndicator: HTMLElement;

    private selectedColorLabel: HTMLInputElement;

    private selectedHsv: [number, number, number] = [0, 0, 0];

    private latentEventHandlers: any[] = [];

    private isInitialized = false;

    createElement(): HTMLElement {
        // Create the elements
        let containerElement = document.createElement('div');
        containerElement.classList.add('rio-color-picker');

        containerElement.innerHTML = `
        <div class="rio-color-picker-color-square">
            <div class="rio-color-picker-knob"></div>
        </div>

        <div class="rio-color-picker-hue-bar rio-color-picker-slider-outer">
            <div class="rio-color-slider-inner"></div>
            <div class="rio-color-picker-knob"></div>
        </div>

        <div class="rio-color-picker-opacity-bar rio-color-picker-slider-outer">
            <div class="rio-color-slider-inner"></div>
            <div class="rio-color-slider-inner rio-checkered"></div>
            <div class="rio-color-picker-knob"></div>
        </div>

        <div class="rio-color-picker-result-container">
            <div class="rio-color-picker-selected-color-circle">
                <div></div>
                <div class="rio-checkered"></div>
            </div>
            <input type='text' class="rio-color-picker-selected-color-label" value="dummy" />
        </div>`;

        // Expose them as properties
        this.colorSquare = containerElement.querySelector(
            '.rio-color-picker-color-square'
        )!;
        this.squareKnob = this.colorSquare.querySelector(
            '.rio-color-picker-knob'
        )!;

        this.hueBarOuter = containerElement.querySelector(
            '.rio-color-picker-hue-bar'
        )!;
        this.hueBarInner = this.hueBarOuter.querySelector(
            '.rio-color-slider-inner'
        )!;
        this.hueIndicator = this.hueBarOuter.querySelector(
            '.rio-color-picker-knob'
        )!;

        this.opacityBarOuter = containerElement.querySelector(
            '.rio-color-picker-opacity-bar'
        )!;
        this.opacityBarInner = this.opacityBarOuter.querySelector(
            '.rio-color-slider-inner'
        )!;
        this.opacityIndicator = this.opacityBarOuter.querySelector(
            '.rio-color-picker-knob'
        )!;

        this.selectedColorLabel = containerElement.querySelector(
            '.rio-color-picker-selected-color-label'
        )!;

        // Subscribe to mouse down events. The other events will be subscribed
        // to only once needed.
        this.colorSquare.addEventListener(
            'mousedown',
            this.onSquareMouseDown.bind(this)
        );
        this.hueBarOuter.addEventListener(
            'mousedown',
            this.onHueBarMouseDown.bind(this)
        );
        this.opacityBarOuter.addEventListener(
            'mousedown',
            this.onOpacityBarMouseDown.bind(this)
        );
        this.selectedColorLabel.addEventListener(
            'change',
            this.setFromUserHex.bind(this)
        );

        // TODO: This component probably doesn't unsubscribe from events if it
        // gets removed from the DOM. This is a memory leak.

        return containerElement;
    }

    updateElement(
        deltaState: ColorPickerState,
        latentComponents: Set<ComponentBase>
    ): void {
        // Color
        //
        // Many combination of HSV values correspond to the same RGB color.
        // For example, every HSV value with V=0 is black.
        //
        // This needs consideration, because even if the backend sets the
        // color to the same one as before, the knobs might jump around.
        // Avoid this, by only updating the selected color if the color
        // actually changed.

        if (deltaState.color !== undefined) {
            let rgbChanged =
                deltaState.color[0] !== this.state.color[0] ||
                deltaState.color[1] !== this.state.color[1] ||
                deltaState.color[2] !== this.state.color[2];

            if (rgbChanged || !this.isInitialized) {
                this.selectedHsv = rgbToHsv(
                    deltaState.color[0],
                    deltaState.color[1],
                    deltaState.color[2]
                );
            }
        }

        // Pick Opacity
        if (deltaState.pick_opacity === true) {
            this.opacityBarOuter.style.display = 'block';
        } else if (deltaState.pick_opacity === false) {
            this.opacityBarOuter.style.display = 'none';

            if (this.state.color !== undefined) {
                this.state.color[3] = 1.0;
            }
        }

        // Apply the modified state
        this.matchComponentToSelectedHsv();

        // The component has been initialized
        this.isInitialized = true;
    }

    matchComponentToSelectedHsv(): void {
        // Precompute the color in RGB
        let [r, g, b] = hsvToRgb(
            this.selectedHsv[0],
            this.selectedHsv[1],
            this.selectedHsv[2]
        );

        this.state.color[0] = r;
        this.state.color[1] = g;
        this.state.color[2] = b;

        let rgbHex = rgbToHex(r, g, b);
        let rgbaHex = rgbaToHex(r, g, b, this.state.color[3]);

        // Update the colors
        let element = this.element;
        element.style.setProperty('--chosen-color-opaque', `#${rgbHex}`);
        element.style.setProperty('--chosen-color-transparent', `#${rgbaHex}`);

        let onlyHueRgb = hsvToRgb(this.selectedHsv[0], 1, 1);
        let hueHex = rgbToHex(onlyHueRgb[0], onlyHueRgb[1], onlyHueRgb[2]);

        this.colorSquare.style.background = `
            linear-gradient(
                to top,
                black,
                transparent
            ),
            linear-gradient(
                to right,
                white,
                #${hueHex}
            )`;

        this.hueIndicator.style.background = `#${hueHex}`;

        // Place the saturation/brightness indicator
        const saturationX = this.selectedHsv[1];
        const brightnessY = 1 - this.selectedHsv[2];

        this.squareKnob.style.left = `${saturationX * 100}%`;
        this.squareKnob.style.top = `${brightnessY * 100}%`;

        // Place the hue indicator
        const hueX = this.selectedHsv[0] / 360;
        this.hueIndicator.style.left = `${hueX * 100}%`;

        // Place the opacity indicator
        const opacityX = this.state.color[3];
        this.opacityIndicator.style.left = `${opacityX * 100}%`;

        // Update the output label
        this.selectedColorLabel.value = this.state.pick_opacity
            ? rgbaHex
            : rgbHex;
    }

    updateSaturationBrightness(x: number, y: number): void {
        const boundingBox = this.colorSquare.getBoundingClientRect();
        this.selectedHsv[1] = (x - boundingBox.left) / boundingBox.width;
        this.selectedHsv[1] = Math.max(0, Math.min(1, this.selectedHsv[1]));

        this.selectedHsv[2] = 1 - (y - boundingBox.top) / boundingBox.height;
        this.selectedHsv[2] = Math.max(0, Math.min(1, this.selectedHsv[2]));

        this.matchComponentToSelectedHsv();
    }

    updateHue(x: number): void {
        const boundingBox = this.hueBarOuter.getBoundingClientRect();
        this.selectedHsv[0] =
            (360 * (x - boundingBox.left)) / boundingBox.width;
        this.selectedHsv[0] = Math.max(0, Math.min(360, this.selectedHsv[0]));

        this.matchComponentToSelectedHsv();
    }

    updateOpacity(x: number): void {
        const boundingBox = this.opacityBarOuter.getBoundingClientRect();
        this.state.color[3] = (x - boundingBox.left) / boundingBox.width;
        this.state.color[3] = Math.max(0, Math.min(1, this.state.color[3]));

        this.matchComponentToSelectedHsv();
    }

    bindHandler(eventName: string, handler: any) {
        let boundHandler = handler.bind(this);
        document.addEventListener(eventName, boundHandler);
        this.latentEventHandlers.push([eventName, boundHandler]);
    }

    onSquareMouseDown(event) {
        this.updateSaturationBrightness(event.clientX, event.clientY);

        // Subscribe to other events and keep track of them
        this.bindHandler('mousemove', this.onSquareMouseMove);
        this.bindHandler('click', this.onSelectionFinished);

        // Eat the event
        event.stopPropagation();
        event.preventDefault();
    }

    onSquareMouseMove(event) {
        this.updateSaturationBrightness(event.clientX, event.clientY);

        // Eat the event
        event.stopPropagation();
        event.preventDefault();
    }

    onHueBarMouseDown(event) {
        this.updateHue(event.clientX);

        // Subscribe to other events and keep track of them
        this.bindHandler('mousemove', this.onHueBarMouseMove);
        this.bindHandler('click', this.onSelectionFinished);

        // Eat the event
        event.stopPropagation();
    }

    onHueBarMouseMove(event) {
        this.updateHue(event.clientX);

        // Eat the event
        event.stopPropagation();
        event.preventDefault();
    }

    onOpacityBarMouseDown(event) {
        this.updateOpacity(event.clientX);

        // Subscribe to other events and keep track of them
        this.bindHandler('mousemove', this.onOpacityBarMouseMove);
        this.bindHandler('click', this.onSelectionFinished);

        // Eat the event
        event.stopPropagation();
    }

    onOpacityBarMouseMove(event) {
        this.updateOpacity(event.clientX);

        // Eat the event
        event.stopPropagation();
        event.preventDefault();
    }

    onSelectionFinished(event) {
        // Send the final color to the frontend
        this.sendMessageToBackend({
            color: this.state.color,
        });

        // Unsubscribe from all events
        for (let handler of this.latentEventHandlers) {
            let [eventName, boundHandler] = handler;
            document.removeEventListener(eventName, boundHandler);
        }

        this.latentEventHandlers = [];

        // Eat the event
        event.stopPropagation();
    }

    lenientlyParseColorHex(hex) {
        // Try to very leniently parse the user-provided hex string
        hex = hex.trim();

        // Drop the leading # if it exists
        hex = hex.startsWith('#') ? hex.slice(1).trim() : hex;

        // Make sure the input consists only of valid characters
        if (!/^[0-9a-fA-F]+$/.test(hex)) {
            return null;
        }

        // rgb
        if (hex.length == 3) {
            let [r, g, b] = hex;
            return [
                parseInt(r + r, 16) / 255,
                parseInt(g + g, 16) / 255,
                parseInt(b + b, 16) / 255,
                1.0,
            ];
        }

        // rgba
        if (hex.length == 4) {
            let [r, g, b, a] = hex;
            return [
                parseInt(r + r, 16) / 255,
                parseInt(g + g, 16) / 255,
                parseInt(b + b, 16) / 255,
                parseInt(a + a, 16) / 255,
            ];
        }

        // rrggbb
        if (hex.length == 6) {
            let [r, g, b] = hex.match(/.{2}/g);
            return [
                parseInt(r, 16) / 255,
                parseInt(g, 16) / 255,
                parseInt(b, 16) / 255,
                1.0,
            ];
        }

        // rrggbbaa
        if (hex.length == 8) {
            let [r, g, b, a] = hex.match(/.{2}/g);
            return [
                parseInt(r, 16) / 255,
                parseInt(g, 16) / 255,
                parseInt(b, 16) / 255,
                parseInt(a, 16) / 255,
            ];
        }

        // Invalid format
        return null;
    }

    setFromUserHex(event) {
        // Try to parse the value
        let color = this.lenientlyParseColorHex(event.target.value);

        // Invalid color
        if (color === null) {
            return;
        }

        // If a color could be parsed, update the component
        let [h, s, l] = rgbToHsv(color[0], color[1], color[2]);
        this.selectedHsv[0] = h;
        this.selectedHsv[1] = s;
        this.selectedHsv[2] = l;
        this.state.color[3] = this.state.pick_opacity ? color[3] : 1.0;

        // Update the component
        this.matchComponentToSelectedHsv();

        // Deselect the text input
        event.target.blur();

        // Send the final color to the frontend
        this.sendMessageToBackend({
            color: this.state.color,
        });
    }

    updateNaturalWidth(ctx: LayoutContext): void {
        this.naturalWidth = 12;
    }

    updateAllocatedWidth(ctx: LayoutContext): void {}

    updateNaturalHeight(ctx: LayoutContext): void {
        this.naturalHeight = this.state.pick_opacity ? 16 : 12;
    }

    updateAllocatedHeight(ctx: LayoutContext): void {
        // The knobs are positioned based on the component's size. Update them.
        this.matchComponentToSelectedHsv();
    }
}
