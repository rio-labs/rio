/**
 * Creates a rate-limited version of the given function. The function will be
 * called at most once every `delay` milliseconds. It is also guaranteed to be
 * called at least once with the final set of arguments passed to the original
 * function.
 *
 * @param callback - The function to be called when the window resizes.
 * @param delay - The delay in milliseconds between function calls.
 * @returns A function that removes the event listener.
 */
export function eventRateLimiter(
    callback: (...args: any[]) => void,
    delay: number
): (...args: any[]) => void {
    let timeout: number | null = null;
    let lastArgs: any[] = [];

    // Create a closure over the state
    return (...args: any[]) => {
        // Store the arguments, so future calls can use them
        lastArgs = args;

        // If a timeout is already set, do nothing
        if (timeout) {
            console.trace('Eating');
            return;
        }

        // Set a timeout to call the function
        timeout = window.setTimeout(() => {
            timeout = null;
            callback(...lastArgs);
        }, delay);
    };
}
