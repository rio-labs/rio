import { ComponentStatesUpdateContext } from "../componentManagement";
import { fillToCss } from "../cssUtils";
import { AnyFill } from "../dataModels";
import { getAllocatedHeightInPx, getAllocatedWidthInPx } from "../utils";
import { ComponentBase, ComponentState, DeltaState } from "./componentBase";

type PlotlyType = any;

type PlotlyPlot = {
    type: "plotly";
    json: string;
};

type MatplotlibPlot = {
    type: "matplotlib";
    svg: string;
};

type PlotState = ComponentState & {
    _type_: "Plot-builtin";
    plot: PlotlyPlot | MatplotlibPlot;
    background: AnyFill | null;
    corner_radius: [number, number, number, number];
};

export class PlotComponent extends ComponentBase<PlotState> {
    // I know this abstraction looks like overkill, but plotly does so much
    // stuff with a time delay (loading plotly, setTimeout, resizeObserver, ...)
    // that it's just a giant mess of race conditions if it's not all
    // represented as a single object that we can easily swap out.
    private plotManager: PlotManager | null = null;

    createElement(context: ComponentStatesUpdateContext): HTMLElement {
        let element = document.createElement("div");
        element.classList.add("rio-plot");
        return element;
    }

    updateElement(
        deltaState: DeltaState<PlotState>,
        context: ComponentStatesUpdateContext
    ): void {
        super.updateElement(deltaState, context);

        if (deltaState.plot !== undefined) {
            if (this.plotManager !== null) {
                this.plotManager.element.remove();
                this.plotManager.destroy();
            }

            if (deltaState.plot.type === "plotly") {
                this.plotManager = new PlotlyManager(deltaState.plot);
            } else {
                this.plotManager = new MatplotlibManager(deltaState.plot);
            }

            this.element.appendChild(this.plotManager.element);
        }

        if (deltaState.background === null) {
            this.element.style.background = "var(--rio-local-bg-variant)";
        } else if (deltaState.background !== undefined) {
            Object.assign(this.element.style, fillToCss(deltaState.background));
        }

        if (deltaState.corner_radius !== undefined) {
            let [topLeft, topRight, bottomRight, bottomLeft] =
                deltaState.corner_radius;

            this.element.style.borderRadius = `${topLeft}rem ${topRight}rem ${bottomRight}rem ${bottomLeft}rem`;
        }
    }

    onDestruction(): void {
        super.onDestruction();

        if (this.plotManager !== null) {
            this.plotManager.destroy();
        }
    }
}

interface PlotManager {
    get element(): HTMLElement;

    destroy(): void;
}

class MatplotlibManager implements PlotManager {
    element: HTMLElement;

    constructor(plot: MatplotlibPlot) {
        this.element = document.createElement("div");
        this.element.innerHTML = plot.svg;

        let svgElement = this.element.querySelector("svg") as SVGElement;

        svgElement.style.width = "100%";
        svgElement.style.height = "100%";
    }

    destroy(): void {}
}

class PlotlyManager implements PlotManager {
    element: HTMLElement;

    private plotDiv: HTMLDivElement;
    private resizeObserver: ResizeObserver | null = null;

    constructor(plot: PlotlyPlot) {
        this.element = document.createElement("div");
        this.element.classList.add("rio-plotly-plot");

        this.plotDiv = document.createElement("div");
        this.element.appendChild(this.plotDiv);

        this.makePlot(plot);
    }

    destroy(): void {
        if (this.resizeObserver !== null) {
            this.resizeObserver.disconnect();
        }
    }

    private async makePlot(plot: PlotlyPlot): Promise<void> {
        let plotJson = JSON.parse(plot.json);

        // Make the plot transparent so the component's background
        // can shine through
        plotJson.layout.paper_bgcolor = "rgba(0,0,0,0)";
        plotJson.layout.plot_bgcolor = "rgba(0,0,0,0)";

        let Plotly = await getPlotly();
        Plotly.newPlot(this.plotDiv, plotJson.data, plotJson.layout);

        // Wait until all components have been created (and
        // `updateElement` called), then tell plotly how much space we
        // have
        setTimeout(() => {
            // Plotly is too stupid to layout itself. Help out.
            this.resizeObserver = new ResizeObserver(() => {
                // Inform plotly of the new size
                Plotly.relayout(this.plotDiv, {
                    width: getAllocatedWidthInPx(this.element),
                    height: getAllocatedHeightInPx(this.element),
                });
            });
            this.resizeObserver.observe(this.element);
        }, 0);
    }
}

let fetchPlotlyPromise: Promise<void> | null = null;

function getPlotly(): Promise<PlotlyType> {
    if (fetchPlotlyPromise === null) {
        console.debug("Fetching plotly.js");

        fetchPlotlyPromise = new Promise<PlotlyType>((resolve) => {
            let script = document.createElement("script");

            script.onload = () => {
                resolve(window["Plotly"]);
            };

            script.src = `${globalThis.RIO_BASE_URL}rio/assets/special/plotly.min.js`;
            document.head.appendChild(script);
        });
    }

    return fetchPlotlyPromise;
}
