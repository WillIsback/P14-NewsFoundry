"use client";
import { LoaderCircle } from "lucide-react";
import { useActionState } from "react";
import { useFormStatus } from "react-dom";
import type { LoginActionState } from "@/src/actions/auth.action";
import { loginUser } from "@/src/actions/auth.action";
import { Button } from "@/src/components/ui/button";
import Input from "@/src/components/ui/Input";
import Logo from "@/src/components/ui/Logo";

const initialState: LoginActionState = {
	error: null,
	errors: null,
};

function SubmitButton() {
	const { pending } = useFormStatus();

	return (
		<Button type="submit" disabled={pending} className="w-full">
			{pending ? (
				<LoaderCircle className="h-4 w-4 animate-spin" aria-hidden="true" />
			) : null}
			{pending ? "Connexion en cours..." : "Se connecter"}
		</Button>
	);
}

export default function LoginPage() {
	const [state, formAction] = useActionState(loginUser, initialState);

	return (
		<form
			action={formAction}
			className="min-w-58 w-[31%] h-fit flex flex-col gap-6 px-8 py-8 justify-center items-center rounded-[14px] bg-white border border-slate-300"
		>
			<Logo width={200} />
			<p className="text-slate-800 text-center">
				Connectez-vous pour accéder à votre assistant d&apos;actualités IA
			</p>
			<Input
				name="email"
				type="email"
				label="Adresse email"
				placeholder="votre.email@example.com"
				required
			/>
			<Input
				name="password"
				type="password"
				label="Mot de passe"
				placeholder="Votre mot de passe"
				required
			/>
			{state?.error ? (
				<p role="status" aria-live="polite" className="text-sm text-red-600">
					{state.error}
				</p>
			) : null}
			<SubmitButton />
		</form>
	);
}
