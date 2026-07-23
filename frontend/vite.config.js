import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev'de CORS ile ugrasmamak icin /api istekleri FastAPI backend'e
// (localhost:8000) proxy'lenir. Frontend kodu her zaman "/api/..." cagirir.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
});
