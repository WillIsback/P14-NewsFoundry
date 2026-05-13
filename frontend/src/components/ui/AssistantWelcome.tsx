import Robot from "./Robot";
export default function AssistantWelcome() {
	return (
		<>
			<div className="flex flex-col w-102.5 h-fit items-center gap-6">
				<Robot variant={"default"} />
				<h1 className="text-brand-velvet">Assistant Revue de Presse IA</h1>
			</div>
			<p className="flex w-full h-fit gap-2.5 px-2 flex-wrap items-center justify-center">
				Posez-moi des questions sur l&apos;actualité récente ou demandez-moi de
				générer une revue de presse sur un sujet spécifique.
			</p>
			<div className="flex w-full h-fit flex-col items-center gap-2.25">
				<p className="font-bold text-slate-500">Exemples :</p>
				<ul className="flex flex-col items-center gap-1 text-slate-800 list-none">
					<li>
						&bull;&nbsp;&quot;Quelles sont les dernières nouvelles en politique
						?&quot;
					</li>
					<li>
						&bull;&nbsp;&quot;Génère une revue de presse sur la
						technologie&quot;
					</li>
					<li>
						&bull;&nbsp;&quot;Résume l&apos;actualité économique de la
						semaine&quot;
					</li>
				</ul>
			</div>
		</>
	);
}
