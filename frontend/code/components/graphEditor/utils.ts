import { pixelsPerRem } from "../../app";
import { componentsByElement, componentsById } from "../../componentManagement";
import { ComponentBase } from "../componentBase";
import { NodeInputComponent } from "../nodeInput";
import { NodeOutputComponent } from "../nodeOutput";
import { GraphEditorComponent } from "./graphEditor";
import { AugmentedConnectionState } from "./graphStore";

/// Temporary function to get a component by its key
///
/// TODO / FIXME / REMOVEME
export function devel_getComponentByKey(key: string): ComponentBase {
    for (let component of Object.values(componentsById)) {
        if (component === undefined) {
            continue;
        }

        // @ts-ignore
        if (component.state.key === key) {
            return component;
        }
    }

    throw new Error(`Could not find component with key ${key}`);
}

/// Given the circle HTML element of a port, walk up the DOM to find the port
/// component that contains it.
export function getPortFromCircle(
    circleElement: HTMLElement
): NodeInputComponent | NodeOutputComponent {
    let portElement = circleElement.parentElement as HTMLElement;
    console.assert(
        portElement.classList.contains("rio-graph-editor-port"),
        "Port element does not have the expected class"
    );

    let portComponent = componentsByElement.get(portElement) as ComponentBase;
    console.assert(
        portComponent !== undefined,
        "Port element does not have a corresponding component"
    );

    console.assert(
        portComponent instanceof NodeInputComponent ||
            portComponent instanceof NodeOutputComponent,
        "Port component is not of the expected type"
    );

    // @ts-ignore
    return portComponent;
}

/// Given a port component, walk up the DOM to find the node component that
/// contains it.
export function getNodeFromPort(
    port: NodeInputComponent | NodeOutputComponent
): ComponentBase {
    // Walk up to find the node's body element
    let bodyElement = port.element.closest(
        ".rio-graph-editor-node-body"
    ) as HTMLElement;

    // Then walk back down to find the Rio component. Take care - there may ba
    // alignments and margins inbetween
    let nodeElement = bodyElement.querySelector(
        ".rio-component"
    ) as HTMLElement;

    // Now use the Rio component to find the actual component
    return componentsByElement.get(nodeElement) as ComponentBase;
}

/// Given the HTML element of a node, return the node's component by walking
/// the DOM.
export function getNodeComponentFromElement(
    nodeElement: HTMLElement
): ComponentBase {
    console.assert(
        nodeElement.classList.contains("rio-graph-editor-node"),
        "Node element does not have the expected class"
    );

    // The node body contains a Rio component. That component's ID is also the
    // node's ID.
    let componentElement = nodeElement.querySelector(
        ".rio-component"
    ) as HTMLElement;

    return componentsByElement.get(componentElement) as ComponentBase;
}

/// Creates a SVG path element representing a connection. Does not add it to
/// the DOM.
export function makeConnectionElement(): SVGPathElement {
    const svgPath = document.createElementNS(
        "http://www.w3.org/2000/svg",
        "path"
    ) as SVGPathElement;

    svgPath.setAttribute("stroke", "var(--rio-local-text-color)");
    svgPath.setAttribute("stroke-opacity", "0.5");
    svgPath.setAttribute("stroke-width", "0.2rem");
    svgPath.setAttribute("fill", "none");

    return svgPath;
}

/// Given a port component, return the coordinates of the port's socket relative
/// to the viewport.
export function getPortViewportPosition(
    portComponent: NodeInputComponent | NodeOutputComponent
): [number, number] {
    // Find the circle's HTML element
    let circleElement = portComponent.element.querySelector(
        ".rio-graph-editor-port-circle"
    ) as HTMLElement;

    // Get the circle's bounding box
    let circleBox = circleElement.getBoundingClientRect();

    // Return the center of the circle
    return [
        circleBox.left + circleBox.width * 0.5,
        circleBox.top + circleBox.height * 0.5,
    ];
}

/// Updates the SVG path of a connection based on the state of the
/// connection. This is a convenience function which determines the start
/// and end points and delegates to the more general function.
export function updateConnectionFromObject(
    ge: GraphEditorComponent,
    connectionState: AugmentedConnectionState
): void {
    // From Port
    let fromPortComponent = componentsById[
        connectionState.fromPort
    ] as NodeOutputComponent;

    let [x1, y1] = getPortViewportPosition(fromPortComponent);

    // To Port
    let toPortComponent = componentsById[
        connectionState.toPort
    ] as NodeInputComponent;

    let [x4, y4] = getPortViewportPosition(toPortComponent);

    // Convert the coordinates to the editor's coordinate system
    const editorRect = ge.element.getBoundingClientRect();
    x1 = x1 - editorRect.left;
    y1 = y1 - editorRect.top;
    x4 = x4 - editorRect.left;
    y4 = y4 - editorRect.top;

    // Update the SVG path
    updateConnectionFromCoordinates(connectionState.element, x1, y1, x4, y4);
}

/// Updates the SVG path of a connection based on the coordinates of the
/// start and end points.
///
/// All coordinates are relative to the editor.
export function updateConnectionFromCoordinates(
    connectionElement: SVGPathElement,
    x1: number,
    y1: number,
    x4: number,
    y4: number
): void {
    // Control the curve's bend
    let signedDistance = Math.abs(x4 - x1);

    let velocity = Math.pow(signedDistance * 10, 0.6);
    velocity = Math.max(velocity, 3 * pixelsPerRem);

    // Calculate the intermediate points
    const x2 = x1 + velocity;
    const y2 = y1;

    const x3 = x4 - velocity;
    const y3 = y4;

    // Update the SVG path
    connectionElement.setAttribute(
        "d",
        `M${x1} ${y1} C ${x2} ${y2}, ${x3} ${y3}, ${x4} ${y4}`
    );
}

/// Returns `true` if the two lines intersect, `false` otherwise.
///
/// ChatGPT generated black magic.
export function linesIntersect(
    l1x1: number,
    l1y1: number,
    l1x2: number,
    l1y2: number,
    l2x1: number,
    l2y1: number,
    l2x2: number,
    l2y2: number
): boolean {
    const denominator =
        (l1x1 - l1x2) * (l2y1 - l2y2) - (l1y1 - l1y2) * (l2x1 - l2x2);

    if (denominator === 0) {
        return false;
    }

    const t =
        ((l1x1 - l2x1) * (l2y1 - l2y2) - (l1y1 - l2y1) * (l2x1 - l2x2)) /
        denominator;

    const u =
        -((l1x1 - l1x2) * (l1y1 - l2y1) - (l1y1 - l1y2) * (l1x1 - l2x1)) /
        denominator;

    return t >= 0 && t <= 1 && u >= 0 && u <= 1;
}
