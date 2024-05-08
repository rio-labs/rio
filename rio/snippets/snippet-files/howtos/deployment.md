# I have created a web-app using Rio. How do I deploy it?

## One-click deployment

We're currently working on a one-click deployment solution for Rio apps. This
will allow you to deploy your app to the internet with just a single command.

This will be announced in our discord server once it's ready.

## Manual  deployment

Most Python web servers aren't meant to be directly visible to the internet.
Because of this we recommend the following setup:

**Run your Rio app on a local port**, such as 8000. Make sure that Rio is
running in release mode. This will make it run faster, use less memory and
enable additional safety checks. To do this, run your app with the `--release`
flag:

```bash
rio run --port 8000 --release
```

Make sure **not** to pass the `--public` flag. We want to make sure Rio is only
available on your local machine.

**Alternatively**, you can run your app via a server such as `uvicorn`. At its
core, Rio is a `fastapi` app, which means you can follow [FastAPI's deployment
guide](https://fastapi.tiangolo.com/deployment/).

**Use Nginx as a reverse proxy**. Nginx is a powerful web server that is
hardened against attacks and safe to run on the internet. This will be what your
users connect to, and it will forward requests to your Rio app. The excellent
`nginx` documentation [has a guide on how to set this
up](https://docs.nginx.com/nginx/admin-guide/web-server/reverse-proxy/).
