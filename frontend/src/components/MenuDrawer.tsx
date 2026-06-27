"use client";

import { Menu as MenuIcon } from "lucide-react";
import Menu from "@/src/components/Menu";
import {
	Sheet,
	SheetContent,
	SheetTitle,
	SheetTrigger,
} from "@/src/components/ui/sheet";

/**
 * Props for the MenuDrawer component.
 *
 * @property chatsPromise - A promise that resolves to the user's chat history.
 */
interface MenuDrawerProps {
	chatsPromise: Promise<{ id: number; date: string }[]>;
}

/**
 * A slide-out drawer menu for mobile devices containing the navigation menu.
 *
 * Hidden on tablet and above, shows a hamburger menu icon on mobile.
 */
export function MenuDrawer({ chatsPromise }: Readonly<MenuDrawerProps>) {
	return (
		<Sheet>
			<SheetTrigger
				className="flex tablet:hidden items-center justify-center w-10 h-10 rounded-[8px] hover:bg-slate-200 hover:cursor-pointer transition-colors"
				aria-label="Ouvrir le menu"
			>
				<MenuIcon size={20} />
			</SheetTrigger>
			<SheetContent side="left" showCloseButton={false} className="p-0 w-fit">
				<SheetTitle className="sr-only">Menu de navigation</SheetTitle>
				<Menu chatsPromise={chatsPromise} inDrawer />
			</SheetContent>
		</Sheet>
	);
}
