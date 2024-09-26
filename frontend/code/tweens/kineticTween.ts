import { BaseTween } from "./baseTween";

export class KineticTween extends BaseTween {
    /// How quickly the animation accelerates. The unit is units/s^2.
    private acceleration: number;

    /// The current speed of the animation. The unit is units/s.
    private velocity: number;

    /// When the function was last ticked. This is a UNIX timestamp in
    /// seconds.
    private lastTickAt: number = 0;

    constructor({ acceleration = 1, initialValue = 0 } = {}) {
        // Chain to the parent constructor
        super({
            initialValue: initialValue,
        });

        // Local configuration
        this.acceleration = acceleration;
        this.velocity = 0;
    }

    public transitionTo(target: number): void {
        this.lastTickAt = Date.now() / 1000;
        super.transitionTo(target);
    }

    public teleportTo(position: number): void {
        this.lastTickAt = Date.now() / 1000;
        super.teleportTo(position);
    }

    override update(): void {
        let now = Date.now() / 1000;
        let deltaTime = now - this.lastTickAt;
        this.lastTickAt = now;

        // Calculate the distance to the target
        let signedRemainingDistance = this._end - this._current;

        // Which direction to accelerate towards?
        let accelerationFactor; // + means towards the target
        let brakingDistance =
            Math.pow(this.velocity, 2) / (2 * this.acceleration);

        // Case: Moving away from the target
        if (
            Math.sign(signedRemainingDistance) != Math.sign(this.velocity) &&
            this.velocity != 0
        ) {
            accelerationFactor = 3;
        }
        // Case: Brake
        else if (Math.abs(signedRemainingDistance) < brakingDistance) {
            accelerationFactor = -1;
        }
        // Case: Accelerate towards the target
        else {
            accelerationFactor = 1;
        }

        let currentAcceleration =
            this.acceleration *
            accelerationFactor *
            Math.sign(signedRemainingDistance);

        // Update the velocity
        this.velocity += currentAcceleration * deltaTime;
        let deltaDistance = this.velocity * deltaTime;

        // Arrived?
        if (Math.abs(deltaDistance) >= Math.abs(signedRemainingDistance)) {
            this._current = this._end;
            this.velocity = 0;
        } else {
            this._current += deltaDistance;
        }
    }
}
