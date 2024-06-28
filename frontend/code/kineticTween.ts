export class KineticTween {
    /// How quickly the animation accelerates. The unit is units/s^2.
    private acceleration: number;

    /// The current progression of the animation. The range is arbitrary.
    private currentPosition: number;

    /// The target position of the animation. The range is arbitrary.
    private targetPosition: number;

    /// The current speed of the animation. The unit is units/s.
    private velocity: number;

    /// When the function was last ticked. This is a UNIX timestamp in
    /// seconds.
    private lastTickAt: number = -1;

    constructor({ acceleration = 350, position = 0 } = {}) {
        this.acceleration = acceleration;
        this.currentPosition = position;
        this.velocity = 0;
    }

    transitionTo(position: number): void {
        // Update the target position
        this.targetPosition = position;
    }

    teleportTo(position: number): void {
        // Update state
        this.currentPosition = position;
        this.targetPosition = position;
        this.velocity = 0;
    }

    /// Ensures that the
    update(): void {
        let now = Date.now();
        let deltaTime = (now - this.lastTickAt) / 1000;
        this.lastTickAt = now;

        // Calculate the distance to the target
        let signedRemainingDistance =
            this.targetPosition - this.currentPosition;

        // Which direction to accelerate towards?
        let accelerationFactor; // + means towards the target
        let brakingDistance =
            Math.pow(this.velocity, 2) / (2 * this.acceleration);

        // Case: Moving away from the target
        if (Math.sign(signedRemainingDistance) != Math.sign(this.velocity)) {
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
            this.currentPosition = this.targetPosition;
            this.velocity = 0;
        } else {
            this.currentPosition += deltaDistance / signedRemainingDistance;
        }
    }

    /// Returns the current position of the animation.
    ///
    /// This value is cached and will only be refreshed when the `update` method
    /// is called.
    get position(): number {
        return this.currentPosition;
    }

    /// Whether the animation is currently animating towards a target. `False`
    /// if the animation is at the target.
    get isRunning(): boolean {
        return this.currentPosition !== this.targetPosition;
    }
}
