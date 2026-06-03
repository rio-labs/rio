interface NotificationData {
    id: number;
    element: HTMLElement;
    height: number;
}

export class NotificationManager {
    private container: HTMLElement;
    private nextId: number = 0;
    private notifications: NotificationData[] = [];
    private readonly spacing = 0.8; // rem

    constructor() {
        // Create the container that will hold all notifications
        this.container = document.createElement("div");
        this.container.classList.add("rio-notification-container");
        document.body.appendChild(this.container);
    }

    createNotification(title: string, body: string): void {
        const id = this.nextId++;

        // Create notification element
        const notification = document.createElement("div");
        notification.classList.add("rio-notification");

        // Create progress overlay
        const progressOverlay = document.createElement("div");
        progressOverlay.classList.add("rio-notification-progress-overlay");
        notification.appendChild(progressOverlay);

        // Create title element
        const titleElement = document.createElement("div");
        titleElement.classList.add("rio-notification-title");
        titleElement.textContent = title;
        notification.appendChild(titleElement);

        // Create body element
        const bodyElement = document.createElement("div");
        bodyElement.classList.add("rio-notification-body");
        bodyElement.textContent = body;
        notification.appendChild(bodyElement);

        // Add to container
        this.container.appendChild(notification);

        // Measure height after adding to DOM
        const height = notification.getBoundingClientRect().height;

        // Add to list
        this.notifications.push({ id, element: notification, height });

        // Update all positions
        this.updatePositions();

        // Trigger slide-in animation
        requestAnimationFrame(() => {
            notification.classList.add("rio-notification-show");
            // Start progress animation (fade out)
            requestAnimationFrame(() => {
                progressOverlay.style.opacity = "0";
            });
        });

        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            this.removeNotification(id);
        }, 5000);
    }

    private removeNotification(id: number): void {
        const index = this.notifications.findIndex((n) => n.id === id);
        if (index === -1) {
            return;
        }

        const notification = this.notifications[index].element;

        // Trigger fade-out animation
        notification.classList.remove("rio-notification-show");
        notification.classList.add("rio-notification-hide");

        // Remove from list
        this.notifications.splice(index, 1);

        // Update positions of remaining notifications with stagger
        this.updatePositions();

        // Remove from DOM after animation
        setTimeout(() => {
            notification.remove();
        }, 250);
    }

    private updatePositions(): void {
        const remInPixels = parseFloat(
            getComputedStyle(document.documentElement).fontSize
        );
        const spacingInPixels = this.spacing * remInPixels;

        let currentTop = 0;

        this.notifications.forEach((notification, index) => {
            // Add a staggered delay for a wave effect
            const delay = index * 0.03; // 30ms between each
            notification.element.style.transitionDelay = `${delay}s`;
            notification.element.style.top = `${currentTop}px`;

            currentTop += notification.height + spacingInPixels;
        });
    }
}
