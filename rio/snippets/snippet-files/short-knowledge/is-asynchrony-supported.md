# Does Rio support async/await?

Absolutely! Rio was written from the ground up to support modern Python
features, including asynchrony. Virtually all functions in your Rio components
can be either synchronous or asynchronous. Rio will automatically detect whether
your event handler is asynchronous and handle it accordingly.
