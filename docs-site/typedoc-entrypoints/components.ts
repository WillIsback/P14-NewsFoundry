/**
 * @module components
 * @description Composants React — point d'entrée pour la référence API des composants UI.
 *
 * Organisation :
 * - **Composants racine** : pages et layouts de haut niveau (`ChatWindow`, `Menu`, `PressReview`…)
 * - **Composants UI** : atomes réutilisables (`Message`, `Input`, `ButtonSend`, `Icon`…)
 *
 * Tous les composants utilisent `"use client"` ou `"use server"` selon leur contexte d'exécution.
 */

// ── Composants racine ─────────────────────────────────────────────────────────
export { default as AssistantCard } from "@/src/components/AssistantCard";
export { default as ChatBackButton } from "@/src/components/ChatBackButton";
export { default as ChatForm } from "@/src/components/ChatForm";
export { default as ChatHeader } from "@/src/components/ChatHeader";
export { default as ChatWindow } from "@/src/components/ChatWindow";
export { default as DemoAccountBanner } from "@/src/components/DemoAccountBanner";
export { default as DisplayReviews } from "@/src/components/DisplayReviews";
export { ErrorBoundary } from "@/src/components/ErrorBoundary";
export { default as HomeChatWrapper } from "@/src/components/HomeChatWrapper";
export { default as Menu } from "@/src/components/Menu";
export { MenuDrawer } from "@/src/components/MenuDrawer";
export { default as PressReview } from "@/src/components/PressReview";
export { SubMenuNav } from "@/src/components/SubMenuNav";

// ── Composants UI (atomes) ────────────────────────────────────────────────────
export { default as AssistantPendingContent } from "@/src/components/ui/AssistantPendingContent";
export { default as AssistantWelcome } from "@/src/components/ui/AssistantWelcome";
export { Button, buttonVariants } from "@/src/components/ui/button";
export { default as ButtonReview } from "@/src/components/ui/ButtonReview";
export { default as ButtonSend } from "@/src/components/ui/ButtonSend";
export {
	ButtonSubMenu,
	type ButtonSubMenuType,
} from "@/src/components/ui/ButtonSubMenu";
export { default as Chat } from "@/src/components/ui/chat";
export { default as Chips } from "@/src/components/ui/Chips";
export { default as Icon } from "@/src/components/ui/Icon";
export { default as Input } from "@/src/components/ui/Input";
export { default as Logo } from "@/src/components/ui/Logo";
export { default as Message } from "@/src/components/ui/Message";
export { default as PendingSpinner } from "@/src/components/ui/PendingSpinner";
export { default as Robot } from "@/src/components/ui/Robot";
export { Toaster } from "@/src/components/ui/sonner";
export { default as TextArea } from "@/src/components/ui/TextArea";
