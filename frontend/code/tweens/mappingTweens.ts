import { BaseTween } from "./baseTween";

/// A tween whose value is determined by mapping a fraction value to the output
/// range.
export class MappingTween extends BaseTween {
    private mapping: (value: number) => number;
    private duration: number;

    constructor({
        mapping,
        duration,
        initialValue = 0,
    }: {
        mapping: (value: number) => number;
        duration: number;
        initialValue?: number;
    }) {
        // Chain to the parent constructor
        super({
            initialValue: initialValue,
        });

        // Local configuration
        this.mapping = mapping;
        this.duration = duration;
    }

    override update(): void {
        let linearProgress = this.progress;
        let mappedProgress = this.mapping(linearProgress);
        this._current =
            this._start + mappedProgress * (this._end - this._start);
    }

    override get progress(): number {
        let now = Date.now();
        let timeSinceStart = now / 1000 - this.animationStartedAt;

        let progress = timeSinceStart / this.duration;
        return Math.min(progress, 1);
    }
}
