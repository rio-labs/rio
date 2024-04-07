export function easeIn(t: number): number {
    return Math.pow(t, 3);
}

export function easeOut(t: number): number {
    return 1 - easeIn(1 - t);
}

export function easeInOut(t: number): number {
    return t < 0.5 ? easeIn(t * 2) / 2 : easeOut(t * 2 - 1) / 2 + 0.5;
}

function cubicBezier(
    t: number,
    p2: [number, number],
    p3: [number, number]
): number {
    // FIXME: I have about zero confidence that this function is correct. It is
    //        not at all tested. The results look okay though.

    // Define all control points
    const p1 = [0, 0];
    const p4 = [1, 1];

    // Project the given t value onto the curve
    let tCurve = t;
    for (let i = 0; i < 5; i++) {
        let current =
            Math.pow(1 - tCurve, 3) * p1[0] +
            3 * Math.pow(1 - tCurve, 2) * tCurve * p2[0] +
            3 * (1 - tCurve) * Math.pow(tCurve, 2) * p3[0] +
            Math.pow(tCurve, 3) * p4[0];
        let derivative =
            3 * Math.pow(1 - tCurve, 2) * p2[0] +
            6 * (1 - tCurve) * tCurve * (p3[0] - p2[0]) +
            3 * Math.pow(tCurve, 2) * (p4[0] - p3[0]);
        tCurve -= (current - t) / derivative;
    }

    // Calculate the y value corresponding to t' on the curve
    return (
        Math.pow(1 - tCurve, 3) * p1[1] +
        3 * Math.pow(1 - tCurve, 2) * tCurve * p2[1] +
        3 * (1 - tCurve) * Math.pow(tCurve, 2) * p3[1] +
        Math.pow(tCurve, 3) * p4[1]
    );
}

export function overshoot(t: number): number {
    return cubicBezier(t, [0.5, 0.5], [0.2, 1.14]);
}
