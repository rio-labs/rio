export async function registerFont(
    name: string,
    urls: (string | null)[]
): Promise<void> {
    const VARIATIONS = [
        { weight: 'normal', style: 'normal' },
        { weight: 'bold', style: 'normal' },
        { weight: 'normal', style: 'italic' },
        { weight: 'bold', style: 'italic' },
    ];

    let promises = new Map<string, Promise<FontFace>>();

    for (let [i, url] of urls.entries()) {
        if (url === null) {
            continue;
        }

        let fontFace = new FontFace(name, `url(${url})`, VARIATIONS[i]);
        promises.set(url, fontFace.load());
    }

    let numSuccesses = 0;
    let numFailures = 0;

    for (let [url, promise] of promises.entries()) {
        let fontFace: FontFace;
        try {
            fontFace = await promise;
        } catch (error) {
            numFailures++;
            console.warn(`Failed to load font file ${url}: ${error}`);
            continue;
        }

        numSuccesses++;
        document.fonts.add(fontFace);
    }

    if (numFailures === 0) {
        console.log(
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
    let input = document.createElement('input');
    input.type = 'file';
    input.multiple = message.multiple;

    if (message.fileExtensions !== null) {
        input.accept = message.fileExtensions.join(',');
    }

    input.style.display = 'none';

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
            data.append('file_names', file.name);
            data.append('file_types', file.type);
            data.append('file_sizes', file.size.toString());
            data.append('file_streams', file, file.name);
        }

        // FastAPI has trouble parsing empty form data. Append a dummy value so
        // it's never empty
        data.append('dummy', 'dummy');

        // Upload the files
        fetch(message.uploadUrl, {
            method: 'PUT',
            body: data,
        });

        // Remove the input element from the DOM. Removing this too early causes
        // weird behavior in some browsers
        input.remove();
    }

    // Listen for changes to the input
    input.addEventListener('change', finish);

    // Detect if the window gains focus. This means the file upload dialog was
    // closed without selecting a file
    window.addEventListener(
        'focus',
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
    window.close(); // TODO: What if the browser doesn't allow this?
}
