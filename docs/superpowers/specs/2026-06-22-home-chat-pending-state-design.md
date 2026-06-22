# Design : état de transition sur la page Home (mode chat)

**Date :** 2026-06-22  
**Scope :** `frontend/src`

---

## Problème

Quand l'utilisateur envoie son premier message depuis `/home` (mode chat), il n'y a aucun retour visuel pendant la server action `sendNewMessage` — le welcome card reste statique jusqu'à la redirection vers `/chat/[slug]`. L'UX est silencieuse alors que l'opération peut prendre plusieurs secondes (création du chat + appel LLM initial).

---

## Architecture

### Situation actuelle

```
home/page.tsx (server)
  ├── <section>
  │     └── <AssistantCard variant="welcome" />   ← server, ignorant isPending
  └── <NewChatFormWrapper />                       ← client, sait isPending
```

`isPending` est confiné dans `NewChatFormWrapper` et ne peut pas remonter vers la section de contenu sans refactoring.

### Cible

```
home/page.tsx (server)
  ├── mode review → <section> + <DisplayReviews /> (inchangé)
  └── mode chat   → <HomeChatWrapper />            ← client, possède les deux zones
```

`HomeChatWrapper` encapsule la section de contenu ET la barre de formulaire. Il gère `useActionState(sendNewMessage)` et expose `isPending` aux deux zones. `NewChatFormWrapper` est supprimé (absorbé).

---

## Composants

### Nouveau : `HomeChatWrapper`

**Fichier :** `src/components/HomeChatWrapper.tsx`  
**Type :** `"use client"`

Responsabilités :
- Gère `useActionState(sendNewMessage, { error: null })` → `[state, formAction, isPending]`
- Gère `resetKey` via `useEffect` (réinitialisation du formulaire après succès, même pattern que `NewChatFormWrapper`)
- Rend `<AssistantCard variant={isPending ? "pending" : "welcome"} />` dans sa section
- Rend `<ChatForm key={resetKey} formAction={formAction} isPending={isPending} error={state.error} />`

Classes de la section : `w-full flex-1 min-h-0 flex flex-col gap-2.5 px-4 py-8 md:px-[25%] md:py-[18%] bg-slate-400`

### Nouveau : `AssistantPendingContent`

**Fichier :** `src/components/ui/AssistantPendingContent.tsx`  
**Type :** composant pur (pas de `"use client"` requis)

Contenu (ordre vertical, `items-center`, `gap-10`) :
1. `<WandSparkles size={48} className="text-brand-velvet" />` (Lucide)
2. `<Loader2 size={24} className="animate-spin text-brand-velvet" />` (Lucide)
3. `<p>` : *"Création de votre chat et recherche des actualités en cours…"*

### Modifié : `AssistantCard`

**Fichier :** `src/components/AssistantCard.tsx`

- Ajouter `"pending"` au type union : `variant?: "default" | "welcome" | "pending"`
- Ajouter une branche dans le rendu pour `variant === "pending"` :  
  Même conteneur extérieur que `"welcome"` (`flex flex-col w-full h-fit items-center gap-10 px-10 py-14 rounded-[14px] bg-slate-white border border-slate-300`) + `<AssistantPendingContent />`

### Supprimé : `NewChatFormWrapper`

- `src/components/NewChatFormWrapper.tsx` → supprimé
- `src/components/__tests__/NewChatFormWrapper.test.tsx` → supprimé
- Import dans `home/page.tsx` → supprimé

### Modifié : `home/page.tsx`

Remplacer :
```tsx
<section className={`... ${defaultMode === "review" ? "..." : "..."}`}>
  {defaultMode === "review" ? <DisplayReviews /> : <AssistantCard variant="welcome" />}
</section>
{defaultMode === "chat" && <NewChatFormWrapper />}
```

Par :
```tsx
{defaultMode === "review" ? (
  <section className="... review classes ...">
    <ErrorBoundary>
      <Suspense><DisplayReviews /></Suspense>
    </ErrorBoundary>
  </section>
) : (
  <HomeChatWrapper />
)}
```

---

## Tests

### `HomeChatWrapper.test.tsx`
- Affiche `AssistantCard variant="welcome"` par défaut (pas de soumission)
- Affiche le bouton d'envoi
- Affiche la zone de texte

### `AssistantPendingContent.test.tsx`
- Rend le spinner (`role="img"` ou classe `animate-spin`)
- Affiche le texte de statut
- Rend l'icône `WandSparkles`

### `AssistantCard.test.tsx` (existant — vérifier s'il existe)
- Ajouter un test : variant `"pending"` rend `AssistantPendingContent`

---

## Flux de données

```
user soumet formulaire
  → HomeChatWrapper: isPending = true
    → AssistantCard variant="pending" (WandSparkles + Loader2 + message)
    → ChatForm: disabled=true, aria-busy=true
  → sendNewMessage complète
    → redirect('/chat/[chatId]')  ← navigation, isPending revient false
```

---

## Fichiers impactés

| Fichier | Action |
|---|---|
| `src/components/HomeChatWrapper.tsx` | Créer |
| `src/components/ui/AssistantPendingContent.tsx` | Créer |
| `src/components/__tests__/HomeChatWrapper.test.tsx` | Créer |
| `src/components/ui/__tests__/AssistantPendingContent.test.tsx` | Créer |
| `src/components/AssistantCard.tsx` | Modifier (+ variant pending) |
| `src/app/(private)/home/page.tsx` | Modifier (HomeChatWrapper) |
| `src/components/NewChatFormWrapper.tsx` | Supprimer |
| `src/components/__tests__/NewChatFormWrapper.test.tsx` | Supprimer |
