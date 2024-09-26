import { getComponentLayout } from "./utils";
import { pixelsPerRem } from "./app";
import {
    componentsById,
    getRootComponent,
    recursivelyDeleteComponent,
} from "./componentManagement";
import { ComponentBase } from "./components/componentBase";
import {
    ComponentLayout,
    UnittestClientLayoutInfo,
    UnittestComponentLayout,
} from "./dataModels";

export async function registerFont(
    name: string,
    urls: (string | null)[]
): Promise<void> {
    const VARIATIONS = [
        { weight: "normal", style: "normal" },
        { weight: "bold", style: "normal" },
        { weight: "normal", style: "italic" },
        { weight: "bold", style: "italic" },
    ];

    let fontFaces = new Map<string, FontFace>();

    for (let [i, url] of urls.entries()) {
        if (url === null) {
            continue;
        }

        // There is/was a bug in Firefox where `FontFace.load()` hangs
        // indefinitely if the FontFace is garbage collected. So make sure to
        // keep a reference to the FontFace at all times.
        let fontFace = new FontFace(name, `url(${url})`, VARIATIONS[i]);
        fontFace.load();

        fontFaces.set(url, fontFace);
    }

    let numSuccesses = 0;
    let numFailures = 0;

    for (let [url, fontFace] of fontFaces.entries()) {
        try {
            await fontFace.loaded;
        } catch (error) {
            numFailures++;
            console.warn(`Failed to load font file ${url}: ${error}`);
            continue;
        }

        numSuccesses++;
        document.fonts.add(fontFace);
    }

    if (numFailures === 0) {
        console.debug(
            `Successfully registered all ${numSuccesses} variations of font ${name}`
        );
    } else if (numSuccesses === 0) {
        console.warn(
            `Failed to register all ${numFailures} variations of font ${name}`
        );
    } else {
        console.warn(
            `Successfully registered ${numSuccesses} variations of font ${name}, but failed to register ${numFailures} variations`
        );
    }
}

export function requestFileUpload(message: any): void {
    // Create a file upload input element
    let input = document.createElement("input");
    input.type = "file";
    input.multiple = message.multiple;

    if (message.fileTypes !== null) {
        input.accept = message.fileTypes.map((x) => `.${x}`).join(",");
    }

    input.style.display = "none";

    function finish() {
        // Don't run twice
        if (input.parentElement === null) {
            return;
        }

        // Build a `FormData` object containing the files
        const data = new FormData();

        let ii = 0;
        for (const file of input.files || []) {
            ii += 1;
            data.append("file_names", file.name);
            data.append("file_types", file.type);
            data.append("file_sizes", file.size.toString());
            data.append("file_streams", file, file.name);
        }

        // FastAPI has trouble parsing empty form data. Append a dummy value so
        // it's never empty
        data.append("dummy", "dummy");

        // Upload the files
        fetch(message.uploadUrl, {
            method: "PUT",
            body: data,
        });

        // Remove the input element from the DOM. Removing this too early causes
        // weird behavior in some browsers
        input.remove();
    }

    // Listen for changes to the input
    input.addEventListener("change", finish);

    // Detect if the window gains focus. This means the file upload dialog was
    // closed without selecting a file
    window.addEventListener(
        "focus",
        function () {
            // In some browsers `focus` fires before `change`. Give `change`
            // time to run first.
            this.window.setTimeout(finish, 500);
        },
        { once: true }
    );

    // Add the input element to the DOM
    document.body.appendChild(input);

    // Trigger the file upload
    input.click();
}

export function setTitle(title: string): void {
    document.title = title;
}

export function closeSession(): void {
    console.trace("closeSession was called somehow! This shouldn't happen!");
    // window.close(); // TODO: What if the browser doesn't allow this?
}

/// Gathers layout information for the given components.
export function getComponentLayouts(
    componentIds: number[]
): (ComponentLayout | null)[] {
    let result: (ComponentLayout | null)[] = [];

    for (let componentId of componentIds) {
        {
            // Find the component
            let component: ComponentBase = componentsById[componentId];

            if (component === undefined) {
                result.push(null);
                continue;
            }

            // Fetch layout information
            result.push(getComponentLayout(component));
        }
    }

    return result;
}

function dumpComponentRecursively(
    component: ComponentBase,
    componentLayouts: { [componentId: number]: UnittestComponentLayout }
) {
    // Prepare the layout
    let subresult = getComponentLayout(component) as UnittestComponentLayout;

    // Add properties specific to unittests
    subresult.aux = {};

    // Save the layout
    componentLayouts[component.id] = subresult;

    // Recurse to children
    for (let child of component.children) {
        dumpComponentRecursively(child, componentLayouts);
    }
}

export function getUnittestClientLayoutInfo(): UnittestClientLayoutInfo {
    // Prepare the result
    const result = {} as UnittestClientLayoutInfo;

    result.windowWidth = window.innerWidth / pixelsPerRem;
    result.windowHeight = window.innerHeight / pixelsPerRem;

    result.componentLayouts = {};

    // Dump recursively, starting with the root component
    let rootComponent = getRootComponent();
    dumpComponentRecursively(rootComponent, result.componentLayouts);

    // Done!
    return result;
}

export function removeDialog(rootComponentId: number): void {
    // Get the dialog's root component
    let rootComponent = componentsById[rootComponentId];

    // Because of network latency, the component might have been removed already
    if (rootComponent === undefined) {
        return;
    }

    // Let the dialog handle the removal
    recursivelyDeleteComponent(rootComponent);
}
