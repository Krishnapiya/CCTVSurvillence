/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_BACKEND_HOST?: string
  readonly VITE_BACKEND_PORT?: string
  readonly VITE_STATION_CODE?: string
  readonly VITE_STATION_NAME?: string
  readonly VITE_INSTALLATION_ID?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
