import { defineConfig } from "vite";
import { compression } from "vite-plugin-compression2";

export default defineConfig({
    build: {
        rollupOptions: {
            external: [/^\/rio\/asset\/.*/],
        },
    },
    plugins: [
        compression({
            exclude: /.*index\.html$/,
            deleteOriginalAssets: true,
        }),
    ],
});
