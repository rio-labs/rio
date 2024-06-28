export abstract class BaseTween {
    /// Where the animation started at, is going to and is currently at.
    protected _start: number;
    protected _current: number;
    protected _end: number;

    protected animationStartedAt: number = -1;

    constructor({ initialValue: initialValue = 0 } = {}) {
        this._start = initialValue;
        this._current = initialValue;
        this._end = initialValue;
    }

    /// Starts a smooth transition to the provided target. This will set `start`
    /// to the current value.
    public transitionTo(target: number): void {
        this.animationStartedAt = Date.now() / 1000;

        this._start = this._current;
        this._end = target;
    }

    /// Immediately sets the current position to the provided target. This will
    /// set `start` to the current value.
    public teleportTo(position: number): void {
        this.animationStartedAt = Date.now() / 1000;

        this._start = this._current;
        this._current = position;
        this._end = position;
    }

    public abstract update(): void;

    /// The original value when the animation started.
    public get start(): number {
        return this._start;
    }

    /// The current value of the animation.
    public get current(): number {
        return this._current;
    }

    /// Returns the value the animation will end up at once it has finished.
    public get end(): number {
        return this._end;
    }

    /// How far through the animation the current position is, as a fraction.
    public get progress(): number {
        if (this._start === this._end) {
            return 1;
        }

        return (this._current - this._start) / (this._end - this._start);
    }

    /// Whether the animation is currently running, i.e. it hasn't reached the
    /// target yet.
    get isRunning(): boolean {
        return this._current !== this._end;
    }
}
