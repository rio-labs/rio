/// A helper class to rate-limit function calls. After creating a `Debouncer`
/// object, you can invoke its `call` method as quickly or as often as you like.
/// The debouncer will ensure that the function is called at a reasonable rate.
export class Debouncer {
    private callback: (...args: any[]) => void;

    // Keep track of when the most recent call was requested
    private mostRecentCallRequest: number = 0;

    // Keep track when the most recent call was actually made
    private mostRecentPerformedCall: number = 0;

    // Keep track of how much time has passed between calls
    private recentIntervals: number[] = [];

    // Pending arguments, if any
    private pendingArguments: any[] | null = null;

    // If a call is pending, this is set to the `setTimeout` object
    private timeout: number | null = null;

    // Updated to reflect how frequently requests to call the function are made
    private medianInterval: number = 10;

    constructor(options: { callback: (...args: any[]) => void }) {
        const { callback } = options;

        this.callback = callback;
    }

    /// Requests that a call is made. The debouncer will decide when to actually
    /// make the call.
    public call(...args: any[]): void {
        // Keep track of how long it has been since the last call was requested
        let now = Date.now();
        let timeSinceLastCallRequest = now - this.mostRecentCallRequest;
        this.recentIntervals.push(timeSinceLastCallRequest);

        // Don't let the recent intervals list get too long
        if (this.recentIntervals.length > 10) {
            this.recentIntervals.shift();
        }

        // Update the median interval
        if (this.recentIntervals.length >= 1) {
            let sorted = this.recentIntervals.slice().sort();
            this.medianInterval = sorted[Math.floor(sorted.length / 2)];
        }

        // Update the arguments the next call should be made with
        this.pendingArguments = args;

        // Consider making the call
        this.considerCalling();

        // Record this call request, now that all logic has run
        this.mostRecentCallRequest = now;
    }

    considerCalling(): void {
        // If no arguments are pending, there is nothing to do
        if (this.pendingArguments === null) {
            return;
        }

        // Determine thresholds. If the time is past at least one of these
        // the call will be made.
        let pauseThreshold =
            this.mostRecentCallRequest + 5 * this.medianInterval;
        let timeoutThreshold = this.mostRecentPerformedCall + 800;
        let combinedThreshold = Math.min(pauseThreshold, timeoutThreshold);

        // Call?
        let now = Date.now();
        let shouldCallNow: boolean = now > combinedThreshold;

        // Yes!
        if (shouldCallNow) {
            this.flush();
            return;
        }

        // This isn't the right time to make a call. Schedule a call for later,
        // if there isn't already one scheduled.
        if (this.timeout !== null) {
            return;
        }

        // Schedule a call
        let waitTime = Math.max(combinedThreshold - now, 20);

        this.timeout = setTimeout(() => {
            this.timeout = null;
            this.considerCalling();
        }, waitTime);
    }

    /// Inform the debouncer that the user has finished interacting with the
    /// interface, indicating to the debouncer that it should call the function
    /// as soon as possible, if there are any pending arguments.
    ///
    /// This can be useful if the caller has additional information, such as
    /// knowing that the user has finished typing in a text field due to a blur
    /// event.
    public flush(): void {
        // If no call is pending there is nothing to do
        if (this.pendingArguments === null) {
            return;
        }

        // Perform the call, taking care not to crash
        try {
            this.callback(...this.pendingArguments);
        } catch (e) {
            console.error(`Failed to call debounced function: ${e}`);
        }

        // Housekeeping
        this.mostRecentPerformedCall = Date.now();
        this.pendingArguments = null;
    }

    /// Clears any pending calls, ensuring that the debouncer will not call the
    /// function in the future unless `call` is invoked again.
    public clear(): void {
        this.pendingArguments = null;

        if (this.timeout !== null) {
            clearTimeout(this.timeout);
            this.timeout = null;
        }
    }
}
