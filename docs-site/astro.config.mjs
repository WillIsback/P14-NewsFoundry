// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import starlightTypeDoc, { typeDocSidebarGroup } from 'starlight-typedoc';

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
      plugins: [
        starlightTypeDoc({
          entryPoints: [
            '../frontend/src/components',
            '../frontend/src/actions',
            '../frontend/src/service',
            '../frontend/src/lib',
          ],
          tsconfig: './typedoc.tsconfig.json',
          output: 'api',
          typeDoc: {
            entryPointStrategy: 'expand',
            excludePrivate: true,
            excludeInternal: false,
            excludeExternals: true,
            skipErrorChecking: true,
            readme: 'none',
          },
          sidebar: {
            label: 'Référence API',
            collapsed: false,
          },
        }),
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
        typeDocSidebarGroup,
      ],
      customCss: [],
    }),
  ],
  outDir: './dist',
});
