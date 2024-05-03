import { pixelsPerRem } from '../app';
import { fillToCss } from '../cssUtils';
import { LayoutContext } from '../layouting';
import { Fill } from '../dataModels';
import { ComponentBase, ComponentState } from './componentBase';

type PlotlyPlot = {
    type: 'plotly';
    json: string;
};

type MatplotlibPlot = {
    type: 'matplotlib';
    svg: string;
};

type PlotState = ComponentState & {
    _type_: 'Plot-builtin';
    plot: PlotlyPlot | MatplotlibPlot;
    background: Fill | null;
    corner_radius?: [number, number, number, number];
};

let fetchPlotlyPromise: Promise<void> | null = null;

function withPlotly(callback: () => void): void {
    // If plotly is already loaded just call the callback
    if (typeof window['Plotly'] !== 'undefined') {
        callback();
        return;
    }

    // If plotly is currently being fetched, wait for it to finish
    if (fetchPlotlyPromise !== null) {
        fetchPlotlyPromise.then(callback);
        return;
    }

    // Otherwise fetch plotly and call the callback when it's done
    console.log('Fetching plotly.js');
    let script = document.createElement('script');
    script.src = '/rio/asset/plotly.min.js';

    fetchPlotlyPromise = new Promise((resolve) => {
        script.onload = () => {
            resolve(null);
        };
        document.head.appendChild(script);
    }).then(callback);
}

export class PlotComponent extends ComponentBase {
    state: Required<PlotState>;

    createElement(): HTMLElement {
        let element = document.createElement('div');
        element.classList.add('rio-plot');
        return element;
    }

    updateElement(
        deltaState: PlotState,
        latentComponents: Set<ComponentBase>
    ): void {
        if (deltaState.plot !== undefined) {
            this.element.innerHTML = '';

            // Plotly
            if (deltaState.plot.type === 'plotly') {
                let plot = deltaState.plot;

                withPlotly(() => {
                    let plotJson = JSON.parse(plot.json);
                    window['Plotly'].newPlot(
                        this.element,
                        plotJson.data,
                        plotJson.layout
                    );

                    this.updatePlotlyLayout();
                });
            }
            // Matplotlib (Just a SVG)
            else {
                this.element.innerHTML = deltaState.plot.svg;

                let svgElement = this.element.querySelector(
                    'svg'
                ) as SVGElement;

                svgElement.style.width = '100%';
                svgElement.style.height = '100%';
            }
        }

        if (deltaState.background === null) {
            this.element.style.background = 'var(--rio-local-bg-variant)';
        } else if (deltaState.background !== undefined) {
            Object.assign(this.element.style, fillToCss(deltaState.background));
        }

        if (deltaState.corner_radius !== undefined) {
            let [topLeft, topRight, bottomRight, bottomLeft] =
                deltaState.corner_radius;

            this.element.style.borderRadius = `${topLeft}rem ${topRight}rem ${bottomRight}rem ${bottomLeft}rem`;
        }
    }

    updatePlotlyLayout(): void {
        window['Plotly'].update(
            this.element,
            {},
            {
                width: this.allocatedWidth * pixelsPerRem,
                height: this.allocatedHeight * pixelsPerRem,
            }
        );
    }

    updateAllocatedHeight(ctx: LayoutContext): void {
        // Plotly is too dumb to layout itself. Help out.
        if (
            this.state.plot.type === 'plotly' &&
            window['Plotly'] !== undefined
        ) {
            this.updatePlotlyLayout();
        }
    }
}
