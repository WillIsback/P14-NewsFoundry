# Home Chat Pending State Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Afficher un état de transition visuel (WandSparkles + Loader2 + message) sur la page `/home` pendant que `sendNewMessage` s'exécute, en remplaçant le welcome card statique.

**Architecture:** Un nouveau composant client `HomeChatWrapper` encapsule la section de contenu ET la barre de formulaire pour le mode chat. Il gère `isPending` via `useActionState(sendNewMessage)` et bascule `AssistantCard` entre `"welcome"` et `"pending"`. `NewChatFormWrapper` est supprimé (absorbé). `AssistantCard` reçoit un troisième variant `"pending"` rendu par le nouveau `AssistantPendingContent`.

**Tech Stack:** Next.js 16 App Router, React 19 (`useActionState`), Lucide React (`WandSparkles`, `Loader2`), Vitest + @testing-library/react, Tailwind CSS, Biome

---

## Fichiers impactés

| Fichier | Action |
|---|---|
| `src/components/ui/AssistantPendingContent.tsx` | Créer |
| `src/components/ui/__tests__/AssistantPendingContent.test.tsx` | Créer |
| `src/components/AssistantCard.tsx` | Modifier (+ variant `"pending"`) |
| `src/components/HomeChatWrapper.tsx` | Créer |
| `src/components/__tests__/HomeChatWrapper.test.tsx` | Créer |
| `src/app/(private)/home/page.tsx` | Modifier |
| `src/components/NewChatFormWrapper.tsx` | Supprimer |
| `src/components/__tests__/NewChatFormWrapper.test.tsx` | Supprimer |

---

## Task 1 : AssistantPendingContent

**Fichiers :**
- Créer : `frontend/src/components/ui/AssistantPendingContent.tsx`
- Créer : `frontend/src/components/ui/__tests__/AssistantPendingContent.test.tsx`

### Contexte

`AssistantWelcome` (référence de structure) se trouve dans `src/components/ui/AssistantWelcome.tsx`. Le conteneur extérieur du welcome card est dans `AssistantCard` (`flex flex-col w-full h-fit items-center gap-10 px-10 py-14 rounded-[14px] bg-slate-white border border-slate-300`). `AssistantPendingContent` est le contenu interne du nouveau variant pending — pas le conteneur.

- [ ] **Écrire le test qui échoue**

```tsx
// frontend/src/components/ui/__tests__/AssistantPendingContent.test.tsx
import { render, screen } from "@testing-library/react";
import AssistantPendingContent from "../AssistantPendingContent";

describe("AssistantPendingContent", () => {
  it("affiche le spinner animé", () => {
    render(<AssistantPendingContent />);
    expect(document.querySelector(".animate-spin")).toBeInTheDocument();
  });

  it("affiche le message de statut", () => {
    render(<AssistantPendingContent />);
    expect(
      screen.getByText(
        "Création de votre chat et recherche des actualités en cours…",
      ),
    ).toBeInTheDocument();
  });

  it("est accessible avec role status", () => {
    render(<AssistantPendingContent />);
    expect(screen.getByRole("status")).toBeInTheDocument();
  });
});
```

- [ ] **Lancer le test pour vérifier qu'il échoue**

```bash
cd frontend && npx vitest run src/components/ui/__tests__/AssistantPendingContent.test.tsx
```

Résultat attendu : FAIL — `Cannot find module '../AssistantPendingContent'`

- [ ] **Créer le composant**

```tsx
// frontend/src/components/ui/AssistantPendingContent.tsx
import { Loader2, WandSparkles } from "lucide-react";

export default function AssistantPendingContent() {
  return (
    <>
      <WandSparkles size={48} className="text-brand-velvet" />
      <div
        role="status"
        aria-label="Chargement en cours"
        className="flex items-center gap-3"
      >
        <Loader2 size={24} className="animate-spin text-brand-velvet" />
      </div>
      <p className="text-center text-slate-700">
        Création de votre chat et recherche des actualités en cours…
      </p>
    </>
  );
}
```

- [ ] **Lancer les tests pour vérifier qu'ils passent**

```bash
cd frontend && npx vitest run src/components/ui/__tests__/AssistantPendingContent.test.tsx
```

Résultat attendu : 3 PASS

- [ ] **Commit**

```bash
git add frontend/src/components/ui/AssistantPendingContent.tsx \
        frontend/src/components/ui/__tests__/AssistantPendingContent.test.tsx
git commit -m "feat(ux): ajouter AssistantPendingContent (WandSparkles + Loader2)"
```

---

## Task 2 : Variant "pending" dans AssistantCard

**Fichiers :**
- Modifier : `frontend/src/components/AssistantCard.tsx`

### Contexte

`AssistantCard` actuel (voir `src/components/AssistantCard.tsx`) :
- `variant?: "default" | "welcome"` 
- `variant === "welcome"` → conteneur avec `<AssistantWelcome />`
- `variant === "default"` → liste de messages

Le conteneur welcome : `flex flex-col w-full h-fit items-center gap-10 px-10 py-14 rounded-[14px] bg-slate-white border border-slate-300`

- [ ] **Modifier `AssistantCard` pour ajouter le variant pending**

```tsx
// frontend/src/components/AssistantCard.tsx
"use client";

import AssistantPendingContent from "./ui/AssistantPendingContent";
import AssistantWelcome from "./ui/AssistantWelcome";
import Icon from "./ui/Icon";
import Message from "./ui/Message";

interface AssistantCardProps {
  variant?: "default" | "welcome" | "pending";
  messages?: {
    id: number;
    type: string;
    content: string;
    timestamp: string;
  }[];
}

export default function AssistantCard({
  variant,
  messages,
}: Readonly<AssistantCardProps>) {
  if (!messages && variant !== "welcome" && variant !== "pending") return <p></p>;
  return (
    <>
      {variant === "welcome" ? (
        <div className="flex flex-col w-full h-fit items-center gap-10 px-10 py-14 rounded-[14px] bg-slate-white border border-slate-300">
          <AssistantWelcome />
        </div>
      ) : variant === "pending" ? (
        <div className="flex flex-col w-full h-fit items-center gap-10 px-10 py-14 rounded-[14px] bg-slate-white border border-slate-300">
          <AssistantPendingContent />
        </div>
      ) : (
        <div className="flex flex-col w-full h-fit gap-8">
          {messages && messages.length > 0 ? (
            messages?.map((message) => (
              <div
                key={message.id}
                className={`flex gap-2.5 ${message.type === "user" ? "justify-end" : "justify-start"}`}
              >
                {message.type === "ai" && <Icon type="ai" />}
                <Message
                  key={message.id}
                  type={message.type as "user" | "ai"}
                  content={message.content}
                  timestamp={message.timestamp}
                />
                {message.type === "user" && <Icon type="user" />}
              </div>
            ))
          ) : (
            <p className="text-slate-800 text-center">
              Aucun message pour le moment. Commencez la conversation en
              envoyant un message !
            </p>
          )}
        </div>
      )}
    </>
  );
}
```

- [ ] **Vérifier que les tests existants passent encore**

```bash
cd frontend && npx vitest run src/components/__tests__/ChatWindow.test.tsx
```

Résultat attendu : tous PASS (AssistantCard est utilisé dans ChatWindow)

- [ ] **Commit**

```bash
git add frontend/src/components/AssistantCard.tsx
git commit -m "feat(ux): ajouter variant pending à AssistantCard"
```

---

## Task 3 : HomeChatWrapper

**Fichiers :**
- Créer : `frontend/src/components/HomeChatWrapper.tsx`
- Créer : `frontend/src/components/__tests__/HomeChatWrapper.test.tsx`

### Contexte

`NewChatFormWrapper` actuel (référence) :
```tsx
const [state, formAction, isPending] = useActionState<
  ChatActionState & { data?: unknown }, FormData
>(sendNewMessage, initialState);
const [resetKey, setResetKey] = useState(0);
useEffect(() => {
  if (!isPending && !state.error && state.data !== undefined) {
    setResetKey((k) => k + 1);
  }
}, [isPending, state]);
```

`HomeChatWrapper` reprend exactement ce pattern ET ajoute le rendu de la section de contenu.

Classes de la section chat dans `home/page.tsx` (à reprendre identiquement) :
`w-full flex-1 min-h-0 flex flex-col gap-2.5 px-4 py-8 md:px-[25%] md:py-[18%] bg-slate-400`

- [ ] **Écrire les tests qui échouent**

```tsx
// frontend/src/components/__tests__/HomeChatWrapper.test.tsx
import { render, screen } from "@testing-library/react";
import { vi } from "vitest";
import HomeChatWrapper from "../HomeChatWrapper";

vi.mock("@/src/actions/chat.action", () => ({
  sendNewMessage: vi.fn(),
}));

describe("HomeChatWrapper", () => {
  it("affiche la zone de texte", () => {
    render(<HomeChatWrapper />);
    expect(screen.getByLabelText("Message")).toBeInTheDocument();
  });

  it("affiche le bouton d'envoi actif par défaut", () => {
    render(<HomeChatWrapper />);
    expect(screen.getByRole("button", { name: "Envoyer" })).not.toBeDisabled();
  });

  it("n'affiche pas le spinner par défaut", () => {
    render(<HomeChatWrapper />);
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });
});
```

- [ ] **Lancer les tests pour vérifier qu'ils échouent**

```bash
cd frontend && npx vitest run src/components/__tests__/HomeChatWrapper.test.tsx
```

Résultat attendu : FAIL — `Cannot find module '../HomeChatWrapper'`

- [ ] **Créer `HomeChatWrapper`**

```tsx
// frontend/src/components/HomeChatWrapper.tsx
"use client";

import { useActionState, useEffect, useState } from "react";
import {
  type ChatActionState,
  sendNewMessage,
} from "@/src/actions/chat.action";
import AssistantCard from "./AssistantCard";
import ChatForm from "./ChatForm";

const initialState: ChatActionState = { error: null };

export default function HomeChatWrapper() {
  const [state, formAction, isPending] = useActionState<
    ChatActionState & { data?: unknown },
    FormData
  >(sendNewMessage, initialState);

  const [resetKey, setResetKey] = useState(0);

  useEffect(() => {
    if (!isPending && !state.error && state.data !== undefined) {
      setResetKey((k) => k + 1);
    }
  }, [isPending, state]);

  return (
    <>
      <section className="w-full flex-1 min-h-0 flex flex-col gap-2.5 px-4 py-8 md:px-[25%] md:py-[18%] bg-slate-400">
        <AssistantCard variant={isPending ? "pending" : "welcome"} />
      </section>
      <ChatForm
        key={resetKey}
        formAction={formAction}
        isPending={isPending}
        error={state.error}
      />
    </>
  );
}
```

- [ ] **Lancer les tests pour vérifier qu'ils passent**

```bash
cd frontend && npx vitest run src/components/__tests__/HomeChatWrapper.test.tsx
```

Résultat attendu : 3 PASS

- [ ] **Commit**

```bash
git add frontend/src/components/HomeChatWrapper.tsx \
        frontend/src/components/__tests__/HomeChatWrapper.test.tsx
git commit -m "feat(ux): créer HomeChatWrapper (section + form + isPending)"
```

---

## Task 4 : Mettre à jour home/page.tsx et supprimer NewChatFormWrapper

**Fichiers :**
- Modifier : `frontend/src/app/(private)/home/page.tsx`
- Supprimer : `frontend/src/components/NewChatFormWrapper.tsx`
- Supprimer : `frontend/src/components/__tests__/NewChatFormWrapper.test.tsx`

### Contexte

Structure actuelle de `home/page.tsx` (lignes 75-101) :
```tsx
<section
  className={`w-full flex-1 min-h-0 flex flex-col gap-2.5 bg-slate-400 ${defaultMode === "review" ? "px-4 md:px-22.5 pt-6 md:pt-10" : "px-4 py-8 md:px-[25%] md:py-[18%]"}`}
>
  {defaultMode === "review" ? (
    <ErrorBoundary ...>
      <Suspense ...>
        <DisplayReviews ... />
      </Suspense>
    </ErrorBoundary>
  ) : (
    <AssistantCard variant="welcome" />
  )}
</section>
{defaultMode === "chat" && <NewChatFormWrapper />}
```

- [ ] **Mettre à jour `home/page.tsx`**

Remplacer le bloc `<section>` + `<NewChatFormWrapper />` par un switch review/chat :

```tsx
// frontend/src/app/(private)/home/page.tsx
import { Suspense } from "react";
import { fetchChats } from "@/src/actions/chat.action";
import { fetchChatReviews, fetchReviews } from "@/src/actions/review.action";
import DisplayReviews from "@/src/components/DisplayReviews";
import { ErrorBoundary } from "@/src/components/ErrorBoundary";
import HomeChatWrapper from "@/src/components/HomeChatWrapper";
import Menu from "@/src/components/Menu";
import { MenuDrawer } from "@/src/components/MenuDrawer";
import { SubMenuNav } from "@/src/components/SubMenuNav";

export default async function HomePage({
  searchParams,
}: Readonly<{ searchParams: Promise<{ mode?: string }> }>) {
  const { mode } = await searchParams;
  const defaultMode = mode === "review" ? "review" : "chat";

  const chatsPromise = fetchChats().then((r) => {
    if (r.error || !r.data) throw new Error(r.error ?? "Failed to load chats");
    return r.data.data ?? [];
  });
  chatsPromise.catch((err: unknown) => {
    console.error("[chats] Failed to load:", err);
  });

  const reviewsPromise = fetchReviews().then((r) => {
    if (r.error || !r.data)
      throw new Error(r.error ?? "Failed to load reviews");
    return r.data.data ?? [];
  });
  reviewsPromise.catch((err: unknown) => {
    console.error("[reviews] Failed to load:", err);
  });

  const chatReviewsPromise = fetchChatReviews().then((r) => {
    if (r.error || !r.data)
      throw new Error(r.error ?? "Failed to load chat reviews");
    return r.data.data ?? [];
  });
  chatReviewsPromise.catch((err: unknown) => {
    console.error("[chatReviews] Failed to load:", err);
  });

  return (
    <div className="flex w-full h-full">
      <ErrorBoundary
        fallback={
          <aside className="hidden tablet:flex flex-col min-w-45 h-full bg-slate-100 border-r border-slate-400 px-6 py-4">
            <p className="text-body-xs text-red-500">
              Impossible de charger les discussions.
            </p>
          </aside>
        }
      >
        <Suspense
          fallback={
            <aside className="hidden tablet:flex w-fit h-full bg-slate-100" />
          }
        >
          <Menu chatsPromise={chatsPromise} />
        </Suspense>
      </ErrorBoundary>
      {/* Main content area */}
      <div className=" w-full h-full flex flex-col">
        <header className="w-full h-22 flex justify-between items-center px-4.5 py-1.75 bg-slate-100 border-0 border-l border-b border-slate-400">
          <Suspense>
            <SubMenuNav defaultMode={defaultMode} />
          </Suspense>
          <Suspense>
            <MenuDrawer chatsPromise={chatsPromise} />
          </Suspense>
        </header>
        {defaultMode === "review" ? (
          <section className="w-full flex-1 min-h-0 flex flex-col gap-2.5 bg-slate-400 px-4 md:px-22.5 pt-6 md:pt-10">
            <ErrorBoundary
              fallback={
                <p className="text-slate-100">
                  Impossible de charger les revues de presse.
                </p>
              }
            >
              <Suspense
                fallback={
                  <p className="text-slate-100">Chargement des revues...</p>
                }
              >
                <DisplayReviews
                  reviewsPromise={reviewsPromise}
                  chatReviewsPromise={chatReviewsPromise}
                />
              </Suspense>
            </ErrorBoundary>
          </section>
        ) : (
          <HomeChatWrapper />
        )}
      </div>
    </div>
  );
}
```

- [ ] **Supprimer les fichiers NewChatFormWrapper**

```bash
rm frontend/src/components/NewChatFormWrapper.tsx
rm frontend/src/components/__tests__/NewChatFormWrapper.test.tsx
```

- [ ] **Lancer la suite de tests complète**

```bash
cd frontend && npx vitest run --coverage
```

Résultat attendu : tous les tests passent, couverture ≥ 80% sur tous les métriques.

Si des tests échouent sur `NewChatFormWrapper` (import mort), c'est normal — les fichiers ont été supprimés.

- [ ] **Commit**

```bash
git add frontend/src/app/(private)/home/page.tsx
git rm frontend/src/components/NewChatFormWrapper.tsx \
        frontend/src/components/__tests__/NewChatFormWrapper.test.tsx
git commit -m "feat(ux): remplacer AssistantCard+NewChatFormWrapper par HomeChatWrapper dans home/page"
```

---

## Task 5 : PR et vérification finale

- [ ] **Créer une issue GitHub**

```bash
gh issue create \
  --title "feat(ux): état de transition lors du premier envoi de message depuis /home" \
  --body "Quand l'utilisateur envoie son premier message depuis /home, afficher un état de transition (WandSparkles + Loader2 + message) plutôt que de laisser le welcome card statique." \
  --label "enhancement"
```

- [ ] **Créer une branche et pousser**

```bash
git checkout -b feat/home-chat-pending-state
git push -u origin feat/home-chat-pending-state
```

- [ ] **Ouvrir la PR**

```bash
gh pr create \
  --title "feat(ux): état de transition lors du premier envoi depuis /home" \
  --body "$(cat <<'EOF'
## Changements

- `HomeChatWrapper` : nouveau composant client qui encapsule section + formulaire pour le mode chat, gère \`isPending\` via \`useActionState(sendNewMessage)\`
- `AssistantPendingContent` : \`WandSparkles\` + \`Loader2\` + message unique pendant la transition
- `AssistantCard` : nouveau variant \`"pending"\`
- \`home/page.tsx\` : simplifié — switch direct \`review\` / \`<HomeChatWrapper />\`
- \`NewChatFormWrapper\` supprimé (absorbé par \`HomeChatWrapper\`)

Closes #<ISSUE_NUMBER>
EOF
)"
```

Remplacer `#<ISSUE_NUMBER>` par le numéro de l'issue créée à l'étape précédente.
