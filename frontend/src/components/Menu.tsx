"use client";

import Link from "next/link";
import { logout } from "@/src/actions/auth.action";
import Chat from "./ui/chat";
import Logo from "./ui/Logo";

interface MenuProps {
	id: string;
	date: string;
}

export default function Menu({ chats }: Readonly<{ chats?: MenuProps[] }>) {
	const logoutSVG = (
		<svg
			width="14"
			height="16"
			viewBox="0 0 14 16"
			fill="none"
			xmlns="http://www.w3.org/2000/svg"
		>
			<title>Se deconnecter</title>
			<path
				d="M10 10.5V14.5C10 15.327 9.327 16 8.5 16H1.5C0.673 16 0 15.327 0 14.5V1.5C0 0.673 0.673 0 1.5 0H8.5C9.327 0 10 0.673 10 1.5V5.5C10 5.776 9.776 6 9.5 6C9.224 6 9 5.776 9 5.5V1.5C9 1.224 8.775 1 8.5 1H1.5C1.225 1 1 1.224 1 1.5V14.5C1 14.776 1.225 15 1.5 15H8.5C8.775 15 9 14.776 9 14.5V10.5C9 10.224 9.224 10 9.5 10C9.776 10 10 10.224 10 10.5ZM13.757 7.346L11.878 5.173C11.697 4.964 11.381 4.942 11.173 5.122C10.964 5.303 10.942 5.619 11.122 5.828L12.569 7.5H5.5C5.224 7.5 5 7.724 5 8C5 8.276 5.224 8.5 5.5 8.5H12.568L11.122 10.173C10.941 10.382 10.964 10.698 11.173 10.879C11.268 10.96 11.384 11 11.5 11C11.64 11 11.779 10.941 11.878 10.827L13.758 8.653C13.914 8.471 14 8.239 14 8C14 7.761 13.914 7.529 13.757 7.346Z"
				fill="#2A2A31"
			/>
		</svg>
	);

	return (
		<aside className="hidden md:flex flex-col w-fit h-full justify-between bg-slate-100">
			{/* Partie Haute*/}
			<div className="w-full h-fit flex flex-col">
				<Link
					href="/"
					className="w-full h-22 flex items-center gap-2.5 pl-6 py-5.5 pr-37.5 bg-slate-100 border-slate-400 border"
				>
					{/* Logo NewFoundry placeholder */}
					<Logo />
				</Link>
				{/* Historique de discussion */}
				<nav className="w-full h-fit">
					<ul className="flex flex-col gap-0.5">
						{/* Card Chat à implementer ici en generation par map, attention a avoir discussion id */}
						{chats ? (
							chats.map((c) => <Chat key={c.id} date={c.date} id={c.id} />)
						) : (
							<li>No chats available.</li>
						)}
					</ul>
				</nav>
			</div>
			{/* Partie basse */}
			<form
				action={logout}
				className="w-full h-fit pl-6 pr-9.25 pt-9.75 pb-9.75 bg-slate-100"
			>
				<button
					type="submit"
					className="w-full h-fit flex py-4 gap-2.75 rounded-[8px] items-center hover:underline hover:cursor-pointer"
				>
					{logoutSVG}
					<span className="text-body-xs text-slate-dark"> Se déconnecter</span>
				</button>
			</form>
		</aside>
	);
}
