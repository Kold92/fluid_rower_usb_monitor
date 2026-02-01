// See https://kit.svelte.dev/docs/types#app for information about these interfaces
// and what to do when importing types

declare namespace App {
  // interface Error {}
  // interface Locals {}
  // interface PageData {}
  // interface Platform {}
}

// Ensure TS knows about the Vite import.meta env values
interface ImportMetaEnv {
  readonly PUBLIC_API_BASE?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
