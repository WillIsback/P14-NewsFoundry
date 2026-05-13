# Text design token - Body typography

## Contexte
La maquette Figma utilisait initialement un Body S ambigu (12px) alors qu'un autre usage "S" existait en 16px.
Pour clarifier l'échelle typographique, le plus petit style Body a été renommé:

- Body 12px: renommé en Body 2XS
- Body 14px: Body XS
- Body 16px: Body S

## Décision
Le token de texte pour les dates (ex: jj/mm/aaaa) repose désormais sur Body 2XS.
Le token pour les labels de formulaire repose sur Body S.
Le token pour les textes inline courts (ex: span générique) repose sur Body XS.

## Impact Figma -> JSON
L'export Figma doit contenir les 3 entrées suivantes dans la hiérarchie Body:

- body.2xs (12px)
- body.xs (14px)
- body.s (16px)

Sans ces trois entrées, la génération CSS ne peut pas produire les variables correspondantes.

## Impact script de génération
Le mapping HTML dans [frontend/scripts/generate-tokens-css.mjs](frontend/scripts/generate-tokens-css.mjs) doit rester aligné avec ces tokens:

- time -> body-2xs
- label -> body-s
- span -> body-xs (ou éviter le global span si trop large selon les composants)

Rappel: [frontend/src/app/tokens.css](frontend/src/app/tokens.css) est auto-généré, il ne faut pas l'éditer à la main.

## Recommandation d'usage
Éviter de dépendre uniquement de balises globales pour la typo (surtout span).
Privilégier des classes utilitaires locales quand le composant a une contrainte métier spécifique.