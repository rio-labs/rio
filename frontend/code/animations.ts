/// Javascript's animation API is pretty basic (and annoying in some ways), so
/// we made our own.

import { reprElement } from "./utils";

/// Represents an animation. Animations are immutable and can be applied to
/// HTMLElements via the `.animate(element)` method.
///
/// The final state of the animation is copied into the Element's CSS,
/// regardless of whether the animation finishes or is canceled.
export abstract class RioAnimation {
    abstract animate(element: HTMLElement): RioAnimationPlayback;
    abstract applyFinalCss(element: HTMLElement): void;
    abstract reversed(): RioAnimation;

    toString(): string {
        return `<${this.constructor.name}>`;
    }
}

/// This is a object mapping CSS attributes to values. The attributes use
/// `camelCase`, which is the ONLY case that works with the animation API. It
/// also works with:
/// - `Object.assign(element.style, ...)`
/// - `element.style[attrName] = value`
///
/// It does NOT work with:
/// - `element.style.setProperty(attrName, value)`
/// - `element.style.removeProperty(attrName)`
export type RioKeyframe = Partial<CSSStyleDeclaration> | { offset?: number };

export class RioKeyframeAnimation extends RioAnimation {
    public readonly keyframes: RioKeyframe[];
    public readonly options: KeyframeEffectOptions;

    constructor(
        keyframes: RioKeyframe[],
        options: Omit<KeyframeEffectOptions, "fill">
    ) {
        super();

        this.keyframes = keyframes;
        this.options = {
            ...options,
            // This is important even though we explicitly `commitStyles()`
            fill: "forwards",
        };
    }

    animate(element: HTMLElement): RioAnimationPlayback {
        return new RioKeyframeAnimationPlayback(element, this);
    }

    applyFinalCss(element: HTMLElement): void {
        Object.assign(element.style, this.keyframes[this.keyframes.length - 1]);
    }

    reversed(): RioKeyframeAnimation {
        let keyframes = Array.from(this.keyframes).reverse();
        return new RioKeyframeAnimation(keyframes, this.options);
    }

    toString(): string {
        return `<${this.constructor.name} ${this.keyframes} ${this.options}>`;
    }
}

export class RioAnimationGroup extends RioAnimation {
    private animations: RioAnimation[];

    constructor(animations: RioAnimation[]) {
        super();

        this.animations = animations;
    }

    animate(element: HTMLElement): RioAnimationPlayback {
        let playbacks = this.animations.map((animation) =>
            animation.animate(element)
        );
        return new RioAnimationGroupPlayback(playbacks, element, this);
    }

    applyFinalCss(element: HTMLElement): void {
        for (let animation of this.animations) {
            animation.applyFinalCss(element);
        }
    }

    reversed(): RioAnimationGroup {
        return new RioAnimationGroup(
            this.animations.map((animation) => animation.reversed())
        );
    }

    toString(): string {
        return `<${this.constructor.name} ${this.animations}>`;
    }
}

/// Represents a playing animation, i.e. an animation that is currently being
/// applied to an HTMLElement.
export abstract class RioAnimationPlayback extends EventTarget {
    public readonly element: HTMLElement;
    public readonly animation: RioAnimation;

    private _state: "unfinished" | "finished" | "canceled" = "unfinished";

    constructor(animation: RioAnimation, element: HTMLElement) {
        super();

        this.animation = animation;
        this.element = element;
    }

    get state(): "unfinished" | "finished" | "canceled" {
        return this._state;
    }

    addEventListener(
        event: "finish" | "cancel" | "end",
        callback: () => void
    ): void {
        super.addEventListener(event, callback);
    }

    protected endWithState(state: "finished" | "canceled"): void {
        if (this._state !== "unfinished") {
            return;
        }
        this._state = state;

        // When the animation ends, whether successfully or canceled, update the
        // element's CSS so that it maintains its current layout/look.
        this._persistCss();

        this.dispatchEvent(new Event(state.substring(0, state.length - 2)));
        this.dispatchEvent(new Event("end"));
    }

    cancel(): void {
        // If it's already in the 'finished' or 'canceled' state, it can't be
        // canceled any more
        if (this._state !== "unfinished") {
            return;
        }

        this._cancel();

        this.endWithState("canceled");
    }

    toString(): string {
        return `<${this.constructor.name} ${this._state} ${reprElement(
            this.element
        )} ${this.animation.toString()}>`;
    }

    /// Writes the current state of the animation into the element's CSS, so
    /// that it still looks the same even after the animation ends.
    protected abstract _persistCss(): void;

    /// Cancels the playback
    protected abstract _cancel(): void;
}

class RioKeyframeAnimationPlayback extends RioAnimationPlayback {
    private jsAnimation: Animation;
    private keyframeAnimation: RioKeyframeAnimation;

    constructor(element: HTMLElement, keyframeAnimation: RioKeyframeAnimation) {
        super(keyframeAnimation, element);

        this.jsAnimation = element.animate(
            keyframeAnimation.keyframes as any,
            keyframeAnimation.options
        );
        this.keyframeAnimation = keyframeAnimation;

        // When the animation finishes, update our state and the element's CSS
        this.jsAnimation.addEventListener("finish", () => {
            this.endWithState("finished");

            // Apparently you're supposed to cancel a finished animation to
            // ensure it's properly cleaned up. Sigh.
            this.jsAnimation.cancel();
        });

        this.jsAnimation.addEventListener("cancel", this.cancel.bind(this));
    }

    protected _persistCss(): void {
        // This idiotic function throws an error if the animated element isn't
        // visible. We somehow have to work around that.
        try {
            this.jsAnimation.commitStyles();
        } catch (error) {
            // For now, just copy the last Keyframe
            // TODO: Find better solution
            Object.assign(
                this.element.style,
                this.keyframeAnimation.keyframes[
                    this.keyframeAnimation.keyframes.length - 1
                ]
            );
        }
    }

    protected _cancel(): void {
        this.jsAnimation.cancel();
    }
}

class RioAnimationGroupPlayback extends RioAnimationPlayback {
    private playbacks: RioAnimationPlayback[];
    private finished: number = 0;

    constructor(
        playbacks: RioAnimationPlayback[],
        element: HTMLElement,
        animation: RioAnimationGroup
    ) {
        super(animation, element);

        this.playbacks = playbacks;

        // Make sure that cancelling one animation cancels them all, and keep
        // track of whether all animations ended successfully as well
        let cancel = this.cancel.bind(this);
        let onOnePlaybackFinished = this.onOnePlaybackFinished.bind(this);

        for (let playback of playbacks) {
            playback.addEventListener("cancel", cancel);
            playback.addEventListener("finish", onOnePlaybackFinished);
        }
    }

    private onOnePlaybackFinished(): void {
        this.finished++;

        // If all playbacks have finished, emit our own 'finish' event
        if (this.finished === this.playbacks.length) {
            this.endWithState("finished");
        }
    }

    protected _persistCss(): void {}

    protected _cancel(): void {
        for (let playback of this.playbacks) {
            playback.cancel();
        }
    }
}
