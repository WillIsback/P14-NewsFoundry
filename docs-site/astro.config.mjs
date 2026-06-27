// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

export default defineConfig({
  site: 'https://willisback.github.io',
  base: '/P14-NewsFoundry',
  integrations: [
    starlight({
      title: 'NewsFoundry Docs',
      description: 'Documentation technique de NewsFoundry — revue de presse IA',
      defaultLocale: 'fr',
      locales: {
        root: { label: 'Français', lang: 'fr' },
      },
      social: [
        { icon: 'github', label: 'GitHub', href: 'https://github.com/WillIsback/P14-NewsFoundry' },
      ],
      sidebar: [
        {
          label: 'Guides',
          items: [
            { label: 'Introduction', link: '/' },
            { label: 'Architecture', link: '/guides/architecture/' },
            { label: 'Authentification', link: '/guides/authentication/' },
            { label: 'Gestion des erreurs', link: '/guides/error-handling/' },
            { label: 'Tests', link: '/guides/testing/' },
            { label: 'Déploiement', link: '/guides/deployment/' },
            { label: 'Performance', link: '/guides/performance/' },
          ],
        },
        {
          label: 'Référence API',
          items: [
            { label: 'Vue d\'ensemble', link: '/api/' },
            { label: 'Actions', link: '/api/actions/' },
            { label: 'Composants', link: '/api/components/' },
            { label: 'Lib', link: '/api/lib/' },
            { label: 'Service (DAL)', link: '/api/service/' },
          ],
        },
      ],
      customCss: [],
    }),
  ],
  outDir: './dist',
});
