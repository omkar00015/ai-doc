/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE: string;
  // add other project env vars here as needed, e.g.
  // readonly VITE_OTHER_FLAG?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
