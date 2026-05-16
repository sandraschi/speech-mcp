import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 10908,
    host: true,
    strictPort: true,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:10909",
        changeOrigin: true,
      },
      "/mcp": {
        target: "http://127.0.0.1:10909",
        changeOrigin: true,
      },
    },
  },
});
