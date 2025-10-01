import { defineConfig } from "vite";
import { compression } from "vite-plugin-compression2";
import path from "path";

const PROJECT_ROOT = path.resolve(__dirname);

export default defineConfig({
    root: path.join(PROJECT_ROOT, "frontend"),
    // We don't know the server URL at build time, so this is intentionally an
    // easy-to-replace placeholder
    base: "/rio-base-url-placeholder/rio/frontend/",
    build: {
        outDir: path.join(PROJECT_ROOT, "rio", "frontend files"),
        emptyOutDir: true,
        rollupOptions: {
            external: [/^\/rio\/assets\/.*/],
        },
    },
    plugins: [
        compression({
            exclude: /.*index\.html$/,
            deleteOriginalAssets: true,
            algorithms: ["gzip"],
        }),
    ],
});
