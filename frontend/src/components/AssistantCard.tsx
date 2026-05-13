import Robot from "./ui/Robot"

export default function AssistantCard(){
  return (
    <div className="flex flex-col w-full h-fit items-center gap-10 px-10 py-14 rounded-[14px] bg-slate-white border border-slate-300">
      <header className="flex flex-col w-102.5 h-fit items-center gap-6">
        <Robot variant={"default"} />
        <h1 className="text-brand-velvet">Assistant Revue de Presse IA</h1>
      </header>
      <p className="flex w-full h-fit gap-2.5 px-2 flex-wrap items-center justify-center">Posez-moi des questions sur l&apos;actualité récente ou demandez-moi de générer une revue de presse sur un sujet spécifique.</p>
      <div className="flex w-full h-fit flex-col items-center gap-2.25">
        <p className="font-bold text-[#717182]">Exemples : </p>
        <p className="text-slate-800">• &quot;Quelles sont les dernières nouvelles en politique ?&quot;</p>
        <p className="text-slate-800">• &quot;Génère une revue de presse sur la technologie&quot;</p>
        <p className="text-slate-800">• &quot;Résume l&apos;actualité économique de la semaine&quot;</p>
      </div>

    </div>
  )
}
