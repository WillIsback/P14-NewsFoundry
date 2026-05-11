import { defineConfig } from '@kubb/core';
import { pluginOas } from '@kubb/plugin-oas';
import { pluginZod } from '@kubb/plugin-zod';

export default defineConfig({
  root: '.',
  input: {
    path: 'http://127.0.0.1:8000/openapi.json',
  },
  output: {
    // On garde un dossier "gen" dédié pour ne pas polluer tes autres fichiers
    path: './src/models/gen',
    clean: true, // IMPORTANT : Ça va supprimer tes 16 anciens fichiers
  },
  plugins: [
    pluginOas({}),
    pluginZod({
      output: {
        // En mettant un nom de FICHIER (avec .ts) au lieu d'un dossier,
        // Kubb comprend qu'il doit tout compiler sur une seule page !
        path: './backend.zod.ts',
      },
    }),
  ],
});