import { defineConfig } from 'vite';
import { viteSingleFile } from 'vite-plugin-singlefile';

export default defineConfig({
    build: {
        rollupOptions: {
            external: [/^\/rio\/asset\/.*/],
        },
    },
    plugins: [viteSingleFile()],
});
