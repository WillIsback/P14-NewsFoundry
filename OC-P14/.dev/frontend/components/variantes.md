# Gestion des variantes dans le Button shadcn/ui

Le composant utilise **CVA (class-variance-authority)**, une librairie qui permet de gérer les variantes de composants de manière déclarative. Voici comment ça fonctionne :

## 1. **Structure du CVA**

```tsx
const buttonVariants = cva(
  "classes de base...",  // Classes appliquées TOUJOURS
  {
    variants: { ... },
    defaultVariants: { ... }
  }
)
```

**Classes de base** : `inline-flex shrink-0 items-center justify-center...` — ces classes s'appliquent systématiquement à tous les buttons.

## 2. **Les variantes**

Le button définit 2 axes de variation :

### **`variant`** (le style visuel)
- `default` : fond primaire
- `outline` : bordure + fond transparent
- `secondary`, `ghost`, `destructive`, `link` : autres styles

### **`size`** (la taille)
- `default` : h-9, px-2.5
- `xs`, `sm`, `lg`, `icon`, `icon-xs`, etc.

**Point clé** : chaque variante ajoute ses propres classes, qui se combinent avec les classes de base.

## 3. **Utilisation dans le composant**

```tsx
function Button({
  variant = "default",
  size = "default",
  asChild = false,
  ...props
}: ...) {
  return (
    <Comp
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    />
  )
}
```

- Les props `variant` et `size` sont extraites
- `buttonVariants()` génère les classes finales basées sur ces props
- `cn()` (util de fusion de classes) les fusionne avec le `className` passé manuellement

## 4. **Avantages pour tes composants**

✅ **Type-safe** : TypeScript validera les valeurs de `variant` et `size`  
✅ **Composable** : tu peux créer plusieurs axes de variation  
✅ **Maintenable** : toute la logique des classes est centralisée  
✅ **Flexible** : facile d'ajouter nouvelles variantes

## Exemple pour tes autres composants

```tsx
const cardVariants = cva(
  "rounded-lg border p-4",
  {
    variants: {
      elevation: {
        none: "shadow-none",
        sm: "shadow-sm",
        md: "shadow-md",
      },
      padding: {
        sm: "p-2",
        md: "p-4",
        lg: "p-6",
      },
    },
    defaultVariants: {
      elevation: "md",
      padding: "md",
    },
  }
)
```

Puis l'utiliser exactement comme le button. **CVA** reste la meilleure approche pour scalable tes composants ! 🎯