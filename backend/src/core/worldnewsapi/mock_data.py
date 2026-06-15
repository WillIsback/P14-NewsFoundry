"""Données de mock pour WorldNewsAPI.

Retournées à la place des vrais appels HTTP quand ``WORLDNEWS_MOCK=True``
(i.e. hors production). Cela évite d'atteindre le rate-limit de 50 points/jour
pendant le développement local.

Les structures Pydantic sont construites directement à partir des modèles
``worldnewsapi`` — la mock est donc typée et identique à la vraie réponse API.
"""

from worldnewsapi.models import (
    SearchNews200Response,
    SearchNews200ResponseNewsInner,
    TopNews200Response,
    TopNews200ResponseTopNewsInner,
    TopNews200ResponseTopNewsInnerNewsInner,
)


def make_top_news_mock(date: str = "2026-06-05") -> TopNews200Response:
    """Retourne une réponse top-news fictive avec 4 clusters."""

    def _article(
        id: int,
        title: str,
        url: str,
        summary: str,
        text: str = "",
        publish_date: str = date,
        authors: list | None = None,
    ) -> TopNews200ResponseTopNewsInnerNewsInner:
        return TopNews200ResponseTopNewsInnerNewsInner(
            id=id,
            title=title,
            url=url,
            summary=summary,
            publish_date=publish_date,
            text=text,
            author=None,
            authors=authors or [],
            image=None,
        )

    clusters = [
        TopNews200ResponseTopNewsInner(
            news=[
                _article(
                    1,
                    "Sommet du G7 : Emmanuel Macron reçoit les leaders mondiaux à Évian",
                    "https://www.lemonde.fr/politique/g7-evian-2026",
                    summary="Le sommet du G7 s'ouvre à Évian avec l'IA, la défense et le climat à l'ordre du jour.",
                    text=(
                        "Le sommet du G7 s'est ouvert ce jeudi à Évian-les-Bains, sous la présidence française d'Emmanuel Macron. "
                        "Réunissant les chefs d'État et de gouvernement des sept plus grandes économies mondiales — États-Unis, Royaume-Uni, "
                        "Allemagne, France, Italie, Canada et Japon —, cette édition 2026 se tient dans un contexte géopolitique particulièrement "
                        "tendu, marqué par la poursuite du conflit en Ukraine et les tensions croissantes en mer de Chine méridionale.\n\n"
                        "L'ordre du jour prioritaire porte sur trois axes : la gouvernance mondiale de l'intelligence artificielle, le renforcement "
                        "de la défense collective face aux menaces hybrides, et l'accélération des engagements climatiques après les résultats "
                        "décevants de la COP31. Emmanuel Macron a annoncé en ouverture un « pacte de responsabilité technologique » visant à "
                        "harmoniser les régulations nationales sur l'IA avant fin 2027.\n\n"
                        "Parmi les invités notables figure Sam Altman, PDG d'OpenAI, dont la présence symbolise la place désormais centrale "
                        "des grandes firmes technologiques dans les négociations diplomatiques. Des représentants de l'Union africaine et de "
                        "l'ASEAN ont également été conviés pour la session élargie du vendredi, signe d'une volonté d'élargir le dialogue "
                        "au-delà du cercle traditionnel des pays industrialisés."
                    ),
                    authors=["Marie Dupont", "Jean-Pierre Lefebvre"],
                ),
                _article(
                    2,
                    "G7 à Évian : Sam Altman (OpenAI) parmi les invités de Macron",
                    "https://www.bfmtv.com/tech/g7-sam-altman-macron",
                    summary="Sam Altman participera aux discussions sur la régulation de l'intelligence artificielle.",
                    text=(
                        "La présence de Sam Altman, patron d'OpenAI, au G7 d'Évian marque une rupture avec les usages diplomatiques "
                        "traditionnels. Pour la première fois, un dirigeant d'entreprise technologique est formellement intégré aux travaux "
                        "du sommet, non pas en marge mais au cœur des discussions sur la gouvernance de l'IA.\n\n"
                        "Altman doit présenter devant les chefs d'État un cadre en cinq points pour une « IA sûre et bénéfique », incluant "
                        "des mécanismes d'audit international, un registre des modèles les plus puissants, et des seuils de sécurité "
                        "contraignants. Ce document, élaboré conjointement avec Anthropic et DeepMind, est perçu comme une tentative "
                        "du secteur privé d'influencer la législation avant qu'elle ne lui soit imposée unilatéralement.\n\n"
                        "Les ONG présentes à Évian dénoncent ce qu'elles appellent une « capture réglementaire », rappelant que les mêmes "
                        "entreprises ayant créé les risques sont invitées à en définir les garde-fous. Altman, de son côté, a défendu "
                        "l'approche lors d'une conférence de presse : « Personne ne comprend mieux les risques réels que ceux qui "
                        "construisent ces systèmes. »"
                    ),
                    authors=["Sophie Martin"],
                ),
            ]
        ),
        TopNews200ResponseTopNewsInner(
            news=[
                _article(
                    3,
                    "Ukraine : Zelensky propose une rencontre directe avec Poutine",
                    "https://www.rfi.fr/europe/ukraine-zelensky-poutine",
                    summary="Dans une lettre ouverte, le président ukrainien appelle à un cessez-le-feu immédiat.",
                    text=(
                        "Dans une lettre ouverte adressée à Vladimir Poutine et rendue publique mercredi soir, Volodymyr Zelensky "
                        "a proposé une rencontre directe « sans conditions préalables » dans un pays neutre, citant la Suisse ou "
                        "la Turquie comme cadres possibles. C'est la première fois depuis le début de la guerre, en février 2022, "
                        "que le président ukrainien formule publiquement une telle invitation.\n\n"
                        "Zelensky conditionne toutefois la reprise des négociations à la libération immédiate de tous les prisonniers "
                        "de guerre ukrainiens et au retrait des troupes russes des zones civiles. « Je suis prêt à regarder Poutine "
                        "dans les yeux et à lui dire : assez de sang », a-t-il déclaré dans un message vidéo diffusé depuis Kiev. "
                        "Le Kremlin n'avait pas encore répondu officiellement au moment où ces lignes sont écrites.\n\n"
                        "Cette démarche intervient dans un contexte de fatigue des opinions occidentales face à la durée du conflit, "
                        "et à quelques semaines des élections de mi-mandat aux États-Unis qui pourraient modifier le soutien financier "
                        "et militaire américain à l'Ukraine. Plusieurs analystes y voient une manœuvre diplomatique destinée à "
                        "repositionner Kiev comme acteur de bonne volonté dans les négociations, quelle que soit la réponse de Moscou."
                    ),
                    authors=["Olena Kovalenko", "François Dubois"],
                ),
                _article(
                    4,
                    "Guerre en Ukraine : trois morts dans des frappes russes sur Kherson",
                    "https://www.lemonde.fr/international/ukraine-frappes-kherson",
                    summary="L'armée russe a visé des infrastructures civiles dans le sud du pays.",
                    text=(
                        "Des frappes de missiles russes ont tué trois civils et blessé onze autres jeudi matin dans la ville de Kherson, "
                        "selon le gouvernorat régional ukrainien. Les tirs ont visé un marché couvert et un immeuble résidentiel de cinq étages "
                        "dans le centre-ville, selon les premières reconstitutions des faits par les équipes de secours locales.\n\n"
                        "Ces attaques interviennent deux jours après l'annonce par Zelensky d'une initiative diplomatique, ce que certains "
                        "commentateurs interprètent comme une réponse délibérée de Moscou. L'armée ukrainienne a indiqué avoir abattu "
                        "quatre des huit missiles lancés, mais reconnait que les systèmes de défense antiaérienne dans cette région "
                        "restent insuffisants face à des tirs en saturation.\n\n"
                        "Le maire de Kherson, Ihor Kolykhaiev, a appelé la communauté internationale à accélérer la livraison "
                        "de systèmes Patriot supplémentaires. « Chaque heure de délai coûte des vies », a-t-il déclaré sur Telegram. "
                        "Depuis la contre-offensive ukrainienne de 2022 qui a libéré la ville, Kherson est régulièrement la cible "
                        "de bombardements en raison de sa position sur la rive droite du Dniepr, face aux positions russes."
                    ),
                    authors=["Pierre Morel"],
                ),
                _article(
                    5,
                    "Ukraine : la France intensifie sa formation de soldats",
                    "https://www.lavoixdunord.fr/ukraine-formation-france",
                    summary="Des centaines de militaires ukrainiens sont formés en France chaque mois.",
                    text=(
                        "Le ministère des Armées français a annoncé jeudi l'extension du programme de formation des soldats ukrainiens "
                        "sur le territoire national. Depuis janvier 2026, ce sont désormais 600 militaires ukrainiens par mois qui "
                        "reçoivent une formation aux centres spécialisés de Saumur, Draguignan et Canjuers, contre 400 auparavant.\n\n"
                        "La formation couvre le maniement des véhicules blindés Caesar récemment livrés, les techniques de déminage, "
                        "et depuis mars 2026, les opérations de guerre électronique. Le général Thierry Burkhard, chef d'état-major "
                        "des armées, a précisé que la France avait formé au total plus de 8 000 soldats ukrainiens depuis le début "
                        "du programme en 2022.\n\n"
                        "Ce renforcement s'inscrit dans le cadre de l'accord de sécurité bilatéral signé en février dernier à Paris, "
                        "qui engage la France sur dix ans à soutenir militairement l'Ukraine. L'opposition française, notamment le "
                        "Rassemblement national, a critiqué cette intensification, estimant qu'elle rapprochait la France d'une "
                        "co-belligérance avec la Russie — accusation rejetée par l'Élysée."
                    ),
                    authors=["Camille Bernard"],
                ),
            ]
        ),
        TopNews200ResponseTopNewsInner(
            news=[
                _article(
                    6,
                    "Disparition de Lyhanna : un corps retrouvé dans le Gers, suspect interpellé",
                    "https://www.bfmtv.com/faits-divers/lyhanna-gers",
                    summary="Le ministre de l'Intérieur a convoqué une cellule de crise après la découverte.",
                    text=(
                        "Les recherches entreprises depuis six jours pour retrouver Lyhanna, une fillette de 9 ans disparue dans "
                        "le village de Fleurance (Gers), ont pris un tour tragique jeudi matin. Les gendarmes ont découvert un corps "
                        "dans un étang à la périphérie du village. L'identification formelle est en cours, mais les autorités "
                        "ont confirmé l'interpellation d'un suspect dans les heures qui ont suivi.\n\n"
                        "Selon des sources proches de l'enquête, le suspect est un homme de 43 ans, résidant dans la même commune "
                        "que la famille. Il aurait été repéré grâce aux images de vidéosurveillance d'un commerce situé sur le "
                        "trajet habituel de la fillette. Le procureur de la République d'Auch a ouvert une information judiciaire "
                        "pour enlèvement et séquestration suivis de mort.\n\n"
                        "La ministre de la Justice a annoncé l'envoi d'une équipe de l'Office central pour la répression des "
                        "violences aux personnes (OCRVP) en renfort des gendarmes locaux. Cette affaire suscite une vive émotion "
                        "nationale et relance le débat sur les dispositifs d'alerte enlèvement, dont l'activation avait été "
                        "retardée de quarante-huit heures dans ce dossier."
                    ),
                    authors=["Élodie Rousseau", "Marc Tantin"],
                ),
            ]
        ),
        TopNews200ResponseTopNewsInner(
            news=[
                _article(
                    7,
                    "Égalité salariale : la France rate l'échéance européenne du 7 juin",
                    "https://www.lanouvellerepublique.fr/egalite-salariale-france",
                    summary="La directive sur la transparence des salaires ne sera pas appliquée à temps.",
                    text=(
                        "La France ne respectera pas l'échéance du 7 juin 2026 fixée par la directive européenne sur la "
                        "transparence des rémunérations. Cette directive impose aux entreprises de plus de 100 salariés de "
                        "publier leurs écarts de salaire entre femmes et hommes, et d'ouvrir des négociations correctives "
                        "lorsque cet écart dépasse 5 %. Bruxelles avait accordé un délai supplémentaire à Paris après une "
                        "première alerte en 2025.\n\n"
                        "Le gouvernement français invoque des difficultés techniques liées à la mise en place du système "
                        "d'information centralisé requis par la directive, ainsi que des oppositions patronales persistantes. "
                        "Selon le ministère du Travail, une loi de transposition sera soumise au Parlement à l'automne 2026 "
                        "— soit avec neuf mois de retard. La Commission européenne pourrait ouvrir une procédure en manquement, "
                        "exposant la France à une astreinte journalière.\n\n"
                        "Les associations féministes dénoncent ce qu'elles qualifient de « manque de volonté politique ». "
                        "« L'écart de salaire moyen en France est de 16,8 %, l'un des plus élevés d'Europe occidentale. "
                        "Chaque mois de retard, c'est des millions d'euros de manque à gagner pour les femmes », a déclaré "
                        "la présidente de l'association À Égalité. Le patronat, lui, réclame des délais supplémentaires "
                        "pour adapter ses systèmes de paie."
                    ),
                    authors=["Nathalie Girard"],
                ),
                _article(
                    8,
                    "Économie française : légère hausse du chômage au premier trimestre",
                    "https://www.lesechos.fr/economie/chomage-t1-2026",
                    summary="Le taux de chômage s'établit à 7,3 % selon les derniers chiffres de l'INSEE.",
                    text=(
                        "Le taux de chômage en France a progressé de 0,2 point au premier trimestre 2026 pour s'établir "
                        "à 7,3 % de la population active, selon les données publiées jeudi par l'Institut national de la "
                        "statistique et des études économiques (INSEE). Cette hausse met fin à une période de deux ans de "
                        "baisse continue qui avait vu le chômage atteindre un plancher historique de 6,8 % au second "
                        "trimestre 2025.\n\n"
                        "L'INSEE pointe plusieurs facteurs explicatifs : le ralentissement de l'activité dans le secteur "
                        "de la construction, touché par la remontée des taux d'intérêt, ainsi qu'une vague de restructurations "
                        "dans l'industrie automobile liée à la transition vers le véhicule électrique. Le chômage des jeunes "
                        "(15-24 ans) a connu la hausse la plus marquée, atteignant 18,2 % contre 17,1 % au trimestre précédent.\n\n"
                        "Le ministre de l'Économie, Bruno Lemaire, a minimisé ces chiffres en les qualifiant de « rebond "
                        "technique temporaire » et a maintenu l'objectif gouvernemental de ramener le chômage sous les 5 % "
                        "d'ici 2028. Les économistes de la Banque de France sont plus prudents, tablant sur un taux de "
                        "7,5 % en fin d'année en cas de poursuite du ralentissement de la zone euro."
                    ),
                    authors=["Laurent Forestier"],
                ),
            ]
        ),
    ]

    return TopNews200Response(
        top_news=clusters,
        language="fr",
        country="fr",
    )


def make_search_news_mock(query: str = "") -> SearchNews200Response:
    """Retourne des articles thématiques selon les mots-clés de la query.

    Permet de valider que l'agent sert bien les données du tool plutôt que ses
    connaissances paramétriques.  Chaque thème est détectable via des mots-clés
    connus dans les assertions des tests.
    """

    q = query.lower()

    def _article(
        id: int,
        title: str,
        url: str,
        summary: str,
        text: str = "",
        publish_date: str = "2026-06-05 08:00:00",
        category: str = "world",
        authors: list | None = None,
    ) -> SearchNews200ResponseNewsInner:
        return SearchNews200ResponseNewsInner(
            id=id,
            title=title,
            url=url,
            summary=summary,
            publish_date=publish_date,
            source_country="fr",
            language="fr",
            sentiment=0.0,
            category=category,
            authors=authors or [],
            text=text,
            image=None,
            video=None,
        )

    # ── Thème Ukraine ────────────────────────────────────────────────────────
    if any(
        kw in q
        for kw in ["ukraine", "ukrainien", "kiev", "donbass", "zelensky", "poutine"]
    ):
        articles = [
            _article(
                201,
                "Ukraine : Zelensky exige un cessez-le-feu immédiat dans une lettre ouverte",
                "https://www.rfi.fr/europe/ukraine-zelensky-cessez-le-feu-2026",
                summary="Le président ukrainien propose une rencontre directe avec Poutine à Genève.",
                text=(
                    "Dans une lettre ouverte publiée mercredi sur le site officiel de la présidence ukrainienne, "
                    "Volodymyr Zelensky a lancé un appel solennel à Vladimir Poutine pour une rencontre directe à Genève, "
                    "sans conditions préalables. C'est la première initiative diplomatique publique du dirigeant ukrainien "
                    "depuis l'échec des pourparlers d'Istanbul en mars 2022.\n\n"
                    "« Je suis prêt à me rendre à Genève demain si Poutine accepte. La paix ne viendra pas des bombes, "
                    "elle viendra des mots », a écrit Zelensky. La lettre exige également la libération de tous les "
                    "prisonniers de guerre ukrainiens comme geste de bonne foi préalable, et le retrait des troupes russes "
                    "des zones résidentielles occupées.\n\n"
                    "Le Kremlin, par la voix du porte-parole Dmitri Peskov, a qualifié la démarche de « coup de communication » "
                    "sans substance, réitérant les conditions russes habituelles : reconnaissance des territoires annexés et "
                    "neutralité militaire de l'Ukraine. Plusieurs capitales occidentales — Washington, Paris, Berlin — ont "
                    "salué l'initiative tout en se montrant sceptiques quant à la réceptivité de Moscou.\n\n"
                    "Cette démarche intervient à six semaines des élections de mi-mandat américaines, dans un contexte "
                    "de pressions croissantes des alliés européens pour relancer un processus diplomatique. Les sondages "
                    "montrent une fatigue des opinions publiques occidentales face à la durée du conflit, désormais dans "
                    "sa cinquième année."
                ),
                authors=["Olena Kovalenko", "Pierre Sautreau"],
            ),
            _article(
                202,
                "Donbass : les frappes russes s'intensifient sur trois oblasts",
                "https://www.lemonde.fr/international/donbass-frappes-russes-juin-2026",
                summary="L'armée russe a visé des infrastructures civiles dans le Donbass, causant 14 victimes.",
                text=(
                    "L'armée russe a intensifié ses frappes sur les oblasts de Donetsk, Zaporizhzhia et Kharkiv au cours "
                    "des 48 dernières heures, faisant selon le bilan provisoire des autorités ukrainiennes 14 morts et "
                    "37 blessés parmi les civils. Les attaques ont ciblé des marchés, des établissements scolaires et "
                    "des stations de pompage d'eau, selon les rapports des gouverneurs régionaux.\n\n"
                    "À Kramatorsk, un immeuble résidentiel de sept étages a été partiellement détruit par un missile "
                    "balistique Iskander dans la nuit de mardi à mercredi. Les secouristes ont extrait douze survivants "
                    "des décombres ; trois corps ont également été retrouvés. Le maire de la ville a déclaré l'état "
                    "d'urgence local et demandé l'évacuation des quartiers les plus exposés.\n\n"
                    "Les experts militaires de l'Institute for the Study of War (ISW) notent que cette intensification "
                    "correspond à un schéma observé chaque fois que les négociations diplomatiques progressent : Moscou "
                    "chercherait à démontrer sa supériorité militaire pour peser sur les éventuels pourparlers. "
                    "Le général Syrsky, commandant en chef des forces armées ukrainiennes, a annoncé le renforcement "
                    "de la défense antiaérienne dans les trois oblasts visés."
                ),
                authors=["François-Xavier Morin"],
            ),
            _article(
                203,
                "Aide militaire à l'Ukraine : le Parlement européen vote un nouveau paquet de 10 Mrd €",
                "https://www.euronews.com/europe/aide-ukraine-parlement-europeen-2026",
                summary="La décision intervient lors du sommet de Bruxelles consacré à la défense collective.",
                text=(
                    "Le Parlement européen a adopté jeudi, à 412 voix pour et 134 contre, un nouveau paquet d'aide "
                    "militaire à l'Ukraine d'un montant de 10 milliards d'euros. Ce vote historique, le plus important "
                    "jamais consacré à la défense dans l'histoire de l'Union, s'est tenu lors d'une session extraordinaire "
                    "convoquée en marge du sommet de Bruxelles sur la défense collective.\n\n"
                    "Le paquet comprend des systèmes de défense antiaérienne — notamment des batteries Patriot supplémentaires "
                    "fournies par l'Allemagne et les Pays-Bas —, des munitions d'artillerie de 155 mm, et pour la première "
                    "fois des missiles de croisière à longue portée dont l'utilisation sera toutefois limitée au territoire "
                    "ukrainien. La présidente de la Commission, Ursula von der Leyen, a qualifié ce vote de « moment "
                    "fondateur pour la défense européenne ».\n\n"
                    "L'opposition au vote est venue principalement des groupes de la gauche radicale (La Gauche) et de "
                    "l'extrême droite (Identité et Démocratie), qui ont tous deux appelé à des négociations immédiates. "
                    "Viktor Orbán, Premier ministre hongrois, a annoncé que son pays bloquerait le décaissement des fonds "
                    "via les mécanismes de l'UE, forçant les autres États membres à recourir à un financement intergouvernemental."
                ),
                authors=["Isabelle Leclercq", "Marco Bianchi"],
            ),
            _article(
                204,
                "Négociations de paix : les pourparlers Ukraine-Russie repoussés à une date indéterminée",
                "https://www.francetvinfo.fr/monde/ukraine-russie-negociations-2026",
                summary="Les médiateurs turcs et américains peinent à fixer un cadre acceptable pour les deux parties.",
                text=(
                    "Les tentatives de médiation turco-américaines pour organiser une rencontre entre des représentants "
                    "ukrainiens et russes se heurtent à un blocage persistant sur les conditions de cessez-le-feu, ont "
                    "confié plusieurs sources diplomatiques à France Télévisions. Le secrétaire d'État américain a reporté "
                    "pour la troisième fois sa tournée régionale, prévue initialement pour cette semaine à Ankara.\n\n"
                    "Le principal point de friction demeure la question des frontières : l'Ukraine refuse catégoriquement "
                    "de négocier sur la base du statu quo territorial actuel, tandis que la Russie refuse tout retrait "
                    "préalable comme condition aux pourparlers. Les propositions turques d'un « gel humanitaire » — "
                    "une trêve temporaire permettant l'évacuation des civils sans préjuger des frontières — n'ont pas "
                    "obtenu d'adhésion des deux parties.\n\n"
                    "Plusieurs diplomates européens évoquent en privé la possibilité d'une médiation directe du Saint-Siège, "
                    "le Vatican ayant des canaux de communication avec Moscou que la plupart des capitales occidentales "
                    "n'ont plus. Le pape François a réitéré son appel à « un cessez-le-feu courageux » lors de l'Angélus "
                    "de dimanche dernier, sans être suivi d'effets concrets."
                ),
                authors=["Anne-Laure Dupont"],
            ),
            _article(
                205,
                "Ukraine : plus de 6 millions de réfugiés en Europe selon le HCR",
                "https://www.afp.com/fr/monde/ukraine-refugies-bilan-2026",
                summary="Le Haut-Commissariat aux réfugiés appelle à renforcer les programmes d'accueil.",
                text=(
                    "Le Haut-Commissariat des Nations Unies pour les réfugiés (HCR) a publié jeudi son bilan trimestriel "
                    "sur les déplacements liés au conflit en Ukraine : 6,2 millions de personnes sont désormais réfugiées "
                    "dans les pays européens, avec une stabilisation observée depuis le début de l'année par rapport au "
                    "pic de 7,8 millions atteint en 2023.\n\n"
                    "L'Allemagne accueille le plus grand contingent (1,4 million), suivie de la Pologne (940 000) et de "
                    "la France (380 000). Le HCR note cependant des tensions croissantes dans plusieurs pays d'accueil, "
                    "notamment en Tchéquie et en Slovaquie, où des partis nationalistes ont obtenu des succès électoraux "
                    "en exploitant les questions migratoires liées à l'afflux ukrainien.\n\n"
                    "Filippo Grandi, Haut-Commissaire de l'ONU pour les réfugiés, a appelé les gouvernements à pérenniser "
                    "leurs programmes d'intégration professionnelle, soulignant que 58 % des réfugiés ukrainiens en âge "
                    "de travailler sont désormais insérés dans le marché du travail local — un taux « remarquable » comparé "
                    "aux autres crises de déplacement. Il a également alerté sur le risque d'une « fatigue de la solidarité » "
                    "si le conflit devait se prolonger au-delà de 2027."
                ),
                authors=["Rachid Amara"],
            ),
        ]

    # ── Thème Iran ───────────────────────────────────────────────────────────
    elif any(
        kw in q
        for kw in ["iran", "iranien", "tehran", "téhéran", "nucleaire", "nucléaire"]
    ):
        articles = [
            _article(
                301,
                "Iran : les négociations nucléaires reprennent à Vienne sous médiation européenne",
                "https://www.lemonde.fr/international/iran-nucleaire-vienne-2026",
                summary="L'Union européenne espère relancer l'accord de 2015 après deux ans de blocage.",
                text=(
                    "Les délégations iranienne et américaine se sont retrouvées lundi à Vienne pour une nouvelle série "
                    "de pourparlers indirects sous l'égide de l'Union européenne, dans l'espoir de relancer l'accord sur "
                    "le nucléaire iranien (JCPOA) suspendu depuis le retrait américain de 2018. C'est la première fois "
                    "en huit mois que les deux parties acceptent de siéger dans la même ville, même si les contacts "
                    "restent indirects via l'intermédiaire européen.\n\n"
                    "Selon des sources proches des négociations, les discussions achoppent toujours sur deux points : "
                    "les garanties demandées par Téhéran contre un nouveau retrait américain unilatéral, et les exigences "
                    "de Washington concernant le programme iranien de missiles balistiques. L'Iran conditionne tout accord "
                    "à la levée immédiate et totale des sanctions économiques, tandis que les États-Unis préfèrent une "
                    "approche progressive liée aux avancées sur la vérification.\n\n"
                    "L'Agence internationale de l'énergie atomique (AIEA) a publié la semaine dernière un rapport indiquant "
                    "que l'Iran dispose désormais d'assez de matière fissile enrichie à 60 % pour fabriquer théoriquement "
                    "plusieurs engins nucléaires, bien qu'aucune intention de le faire n'ait été démontrée. Ce rapport a "
                    "considérablement durci le ton des négociateurs occidentaux, qui exigent un retour immédiat aux "
                    "niveaux d'enrichissement prévus par le JCPOA originel (3,67 %).\n\n"
                    "Les analystes du think tank Chatham House estiment que la fenêtre diplomatique se réduit : si aucun "
                    "accord n'est trouvé avant les élections présidentielles américaines de novembre 2026, un nouveau "
                    "gel des négociations est quasi certain, quelle que soit l'issue du scrutin."
                ),
                authors=["Thomas Wieder", "Negar Mortazavi"],
            ),
            _article(
                302,
                "Sanctions contre l'Iran : Washington maintient la pression économique",
                "https://www.lefigaro.fr/international/iran-sanctions-usa-2026",
                summary="Le département du Trésor américain annonce de nouvelles restrictions sur le pétrole iranien.",
                text=(
                    "Le département du Trésor américain a annoncé mercredi l'extension de ses sanctions secondaires "
                    "visant les acheteurs de pétrole iranien, ciblant notamment trois raffineries chinoises et une "
                    "compagnie maritime turque accusées de contourner les restrictions en vigueur. Ces mesures entrent "
                    "en vigueur à compter du 15 juin, laissant un délai de grâce de dix jours pour les contrats en cours.\n\n"
                    "L'annonce est perçue comme délibérément mal timée par rapport à la reprise des négociations à Vienne, "
                    "et plusieurs diplomates européens ont exprimé leur agacement en privé. « On ne peut pas négocier d'une "
                    "main et appuyer sur l'étrangleur de l'autre », a déclaré un haut responsable de la diplomatie "
                    "européenne sous couvert d'anonymat. L'administration américaine, elle, défend une politique de "
                    "« pression maximale combinée à l'ouverture diplomatique ».\n\n"
                    "Côté iranien, le président Massoud Pezeshkian a convoqué une réunion d'urgence du Conseil suprême "
                    "de sécurité nationale. Des sources à Téhéran évoquent la possibilité d'une suspension des pourparlers "
                    "à Vienne si de nouvelles sanctions sont imposées avant la fin des négociations. L'économie iranienne "
                    "reste sous forte pression : le rial a perdu 40 % de sa valeur depuis janvier, et l'inflation frôle "
                    "les 45 % selon les statistiques officielles iraniennes, jugées sous-évaluées par les économistes indépendants."
                ),
                authors=["Michel Bôle-Richard"],
            ),
            _article(
                303,
                "Iran : manifestations à Téhéran après la mort d'une étudiante en garde à vue",
                "https://www.liberation.fr/international/iran-manifestations-2026",
                summary="Des milliers de personnes ont défié le couvre-feu malgré une répression intense.",
                text=(
                    "Des milliers de manifestants ont bravé le couvre-feu instauré à Téhéran mardi soir, après la mort "
                    "d'une étudiante de 22 ans en garde à vue à la prison d'Evin. Selon des sources militantes contactées "
                    "par Libération, la jeune femme, Narges Hosseini — aucun lien de parenté avec la militante Narges "
                    "Mohammadi, prix Nobel de la paix 2023 —, avait été arrêtée trois jours plus tôt lors d'un rassemblement "
                    "commémorant le deuxième anniversaire du mouvement « Femme, Vie, Liberté ».\n\n"
                    "Les autorités iraniennes ont présenté sa mort comme un « suicide », version contestée par sa famille "
                    "et par les médecins légistes indépendants qui réclament une autopsie internationale. Des images diffusées "
                    "sur les réseaux sociaux montrent des blessures incompatibles avec une pendaison, selon des experts "
                    "médico-légaux contactés par plusieurs ONG.\n\n"
                    "La répression a été immédiate : les forces paramilitaires Bassidjis ont dispersé les rassemblements "
                    "à coups de matraques et de gaz lacrymogènes, faisant selon Amnesty International au moins 45 blessés "
                    "et 120 arrestations en une seule nuit. Le Haut-Commissariat aux droits de l'homme de l'ONU a demandé "
                    "l'ouverture d'une enquête indépendante. Ces événements risquent de peser lourdement sur les négociations "
                    "nucléaires en cours à Vienne, plusieurs délégations européennes ayant conditionné toute normalisation "
                    "des relations à des améliorations tangibles en matière de droits humains."
                ),
                authors=["Delphine Minoui"],
            ),
            _article(
                304,
                "Drones iraniens en Ukraine : l'UE prépare des contre-mesures",
                "https://www.rfi.fr/monde/iran-drones-ukraine-ue-2026",
                summary="Bruxelles envisage des sanctions ciblées contre les responsables du programme de drones.",
                text=(
                    "La Commission européenne prépare un nouveau paquet de sanctions visant spécifiquement le programme "
                    "iranien de drones, après la confirmation par les services de renseignement de plusieurs États membres "
                    "que des Shahed-136 de fabrication iranienne ont été utilisés dans les récentes frappes sur Kharkiv "
                    "et Kherson. Ce serait le sixième paquet de sanctions européennes visant l'Iran depuis le début du "
                    "transfert de drones à la Russie, révélé en septembre 2022.\n\n"
                    "Les mesures envisagées cibleraient des entités liées au Corps des Gardiens de la révolution islamique "
                    "(CGRI) impliquées dans la production et l'exportation de drones, ainsi que des intermédiaires en Géorgie "
                    "et aux Émirats arabes unis soupçonnés de faciliter les livraisons. L'Iran dément catégoriquement fournir "
                    "des armes à la Russie, malgré les preuves matérielles accumulées par les enquêteurs ukrainiens et les "
                    "experts de l'ONU.\n\n"
                    "Cette décision complique encore davantage les négociations nucléaires à Vienne. Des diplomates iraniens "
                    "ont d'ores et déjà averti que de nouvelles sanctions « torpilleraient » toute chance d'accord. "
                    "Le chef de la diplomatie européenne, Josep Borrell, tente de maintenir les deux dossiers séparés, "
                    "mais la position est de plus en plus difficile à tenir politiquement, notamment face aux pressions "
                    "des États baltes et de la Pologne qui réclament des mesures plus dures."
                ),
                authors=["Ghazal Golshiri"],
            ),
            _article(
                305,
                "Iran-Israël : escalade verbale après l'opération « Bouclier de Sion »",
                "https://www.france24.com/fr/moyen-orient/iran-israel-escalade-2026",
                summary="Le chef des Gardiens de la révolution menace de frappes préventives sur le territoire israélien.",
                text=(
                    "La tension entre Israël et l'Iran a atteint un nouveau pic cette semaine après que l'armée israélienne "
                    "a conduit l'opération « Bouclier de Sion », une série de frappes préventives contre des dépôts "
                    "d'armes du Hezbollah au Liban-Sud que Jérusalem attribue à un financement et un approvisionnement "
                    "iraniens. C'est la troisième opération militaire israélienne de grande envergure au Liban en moins "
                    "de six mois.\n\n"
                    "En réponse, le général Hussein Salami, commandant du Corps des Gardiens de la révolution islamique, "
                    "a déclaré lors d'une cérémonie militaire à Téhéran que l'Iran se réservait le droit de « frappes "
                    "préventives directes sur le territoire sioniste » si ses intérêts vitaux étaient menacés. C'est "
                    "la déclaration la plus explicite jamais faite par un officiel iranien de haut rang concernant des "
                    "frappes directes sur Israël.\n\n"
                    "Washington a immédiatement convoqué l'ambassadeur iranien aux Nations Unies pour exprimer sa "
                    "« préoccupation extrême ». Le président Biden a activé une cellule de crise à la Maison Blanche "
                    "et le Pentagone a annoncé le déploiement d'un deuxième groupe aéronaval en Méditerranée orientale. "
                    "Les marchés financiers ont réagi à cette escalade : le cours du Brent a bondi de 4,7 % en une "
                    "journée, atteignant 98 dollars le baril, son niveau le plus élevé depuis janvier."
                ),
                authors=["Benjamin Barthe", "Sami Boubaker"],
            ),
        ]

    # ── Thème IA / technologie ───────────────────────────────────────────────
    elif any(
        kw in q
        for kw in ["ia", "intelligence artificielle", "openai", "gpt", "llm", "tech"]
    ):
        articles = [
            _article(
                101,
                "Intelligence artificielle en France : l'Europe veut rattraper son retard",
                "https://www.lesechos.fr/ia-europe-retard-2026",
                summary="Selon un rapport parlementaire, la France doit doubler ses investissements en IA d'ici 2028.",
                text=(
                    "Un rapport de la commission parlementaire sur la souveraineté numérique, rendu public mercredi, "
                    "dresse un bilan sévère du positionnement français dans la course à l'intelligence artificielle. "
                    "Selon ce document de 240 pages co-rédigé par les députés Marc Ferracci (Renaissance) et Arthur "
                    "Delaporte (PS), la France ne consacre que 0,3 % de son PIB à la recherche publique en IA, contre "
                    "0,6 % pour le Royaume-Uni et 0,8 % pour les États-Unis.\n\n"
                    "Le rapport préconise un doublement des investissements publics d'ici 2028, soit 4,2 milliards "
                    "d'euros supplémentaires, dont la moitié destinés à former 15 000 ingénieurs spécialisés par an. "
                    "Il recommande également la création d'un « CERN de l'IA » européen — un laboratoire commun "
                    "associant les grandes universités et les entreprises — pour mutualiser les infrastructures "
                    "de calcul, aujourd'hui essentiellement américaines ou chinoises.\n\n"
                    "Le ministre de l'Industrie et du Numérique a accueilli favorablement le rapport tout en "
                    "rappelant les contraintes budgétaires actuelles. L'investissement public net dans l'IA reste "
                    "fortement dépendant du prochain projet de loi de finances, dont les arbitrages sont attendus "
                    "pour septembre. Les entreprises françaises du secteur — Mistral AI, Kyutai, Nabla — ont de "
                    "leur côté publié une tribune appelant à un « choc de simplification réglementaire » pour ne "
                    "pas être asphyxiées par l'AI Act européen avant même d'avoir atteint une taille critique."
                ),
                category="technology",
                authors=["Sandrine Cassini"],
            ),
            _article(
                102,
                "Doctolib et la protection des données de santé face aux géants de l'IA",
                "https://www.bfmtv.com/tech/doctolib-donnees-sante-ia",
                summary="Des questions persistent sur la capacité de Doctolib à protéger les données médicales des patients.",
                text=(
                    "La Commission nationale de l'informatique et des libertés (CNIL) a ouvert une enquête formelle sur "
                    "les pratiques de Doctolib en matière de traitement des données de santé, après plusieurs signalements "
                    "de chercheurs en cybersécurité concernant des transferts de métadonnées vers des serveurs américains. "
                    "L'entreprise, qui gère les rendez-vous médicaux de plus de 80 millions de patients en France, "
                    "héberge ses données sur des infrastructures AWS en Europe, mais des chercheurs contestent l'étanchéité "
                    "de cette séparation.\n\n"
                    "Doctolib réfute catégoriquement tout manquement réglementaire, affirmant se conformer strictement au "
                    "RGPD et aux exigences de l'hébergement de données de santé (HDS). La société a publié un audit "
                    "indépendant réalisé par le cabinet EY, concluant à l'absence de fuite vers des tiers non autorisés. "
                    "Mais plusieurs experts consultés par BFM Tech estiment que cet audit ne couvre pas les flux de "
                    "métadonnées comportementales — temps de connexion, fréquence des rendez-vous — qui peuvent révéler "
                    "des informations médicales sensibles sans contenir de données nominatives.\n\n"
                    "L'enjeu dépasse Doctolib : la question de la souveraineté des données de santé est centrale dans "
                    "les débats sur l'IA médicale. Plusieurs startups françaises développent des algorithmes de diagnostic "
                    "assisté qui s'appuient précisément sur ces données agrégées. La CNIL devrait rendre ses premières "
                    "conclusions d'ici trois mois."
                ),
                category="technology",
                authors=["Hugo Septier"],
            ),
            _article(
                103,
                "Sam Altman au G7 : OpenAI veut une régulation internationale de l'IA",
                "https://www.leparisien.fr/tech/sam-altman-g7-regulation-ia",
                summary="Le PDG d'OpenAI plaide pour un traité mondial sur la sécurité de l'intelligence artificielle.",
                text=(
                    "Sam Altman, président-directeur général d'OpenAI, a présenté devant les chefs d'État du G7 réunis "
                    "à Évian un projet de traité international sur la sécurité de l'intelligence artificielle, qu'il appelle "
                    "le « Cadre de Genève pour l'IA ». Ce texte en cinq chapitres propose la création d'un organisme "
                    "intergouvernemental de surveillance des systèmes d'IA dits « de haute capacité », définis par un seuil "
                    "de puissance de calcul équivalent à celui de GPT-5.\n\n"
                    "Le cadre préconise un régime d'audit obligatoire pour tout modèle dépassant ce seuil, ainsi qu'un "
                    "mécanisme de signalement des incidents de sécurité similaire à celui qui existe dans l'aviation civile. "
                    "Altman a insisté sur l'urgence : « Nous avons peut-être deux à trois ans avant que des systèmes "
                    "capables d'actions autonomes à grande échelle ne soient déployés. Sans cadre international, chaque "
                    "nation régulera à sa façon — ou ne régulera pas. »\n\n"
                    "La proposition a reçu un accueil contrasté. Macron et Scholz l'ont qualifiée de « base de travail "
                    "sérieuse » ; Biden s'est montré plus réservé, craignant qu'un organisme international ne ralentisse "
                    "l'innovation américaine. Le Premier ministre japonais a soutenu le principe mais demandé des garanties "
                    "sur la gouvernance pour éviter une domination américaine ou européenne de l'organe de contrôle. "
                    "Aucune décision formelle n'a été prise à ce stade, mais plusieurs délégations ont accepté de mandater "
                    "leurs représentants pour des négociations préliminaires avant la fin de l'année."
                ),
                category="technology",
                authors=["Morgane Tual"],
            ),
            _article(
                104,
                "L'IA et le chômage des jeunes : le télétravail plus responsable que l'automatisation",
                "https://www.ouest-france.fr/ia-chomage-jeunes-teletravail",
                summary="Une étude de Sciences Po suggère que le télétravail post-Covid explique davantage la baisse d'embauche des juniors.",
                text=(
                    "Contrairement à la narrative dominante qui attribue la difficulté d'insertion professionnelle des "
                    "jeunes à l'automatisation par l'IA, une nouvelle étude du Laboratoire interdisciplinaire d'évaluation "
                    "des politiques publiques (LIEPP) de Sciences Po conteste cette corrélation. Selon les chercheurs, "
                    "la généralisation du télétravail après la pandémie de Covid-19 expliquerait 60 à 70 % de la baisse "
                    "des embauches de candidats juniors observée depuis 2021.\n\n"
                    "La logique est la suivante : en travaillant à distance, les managers peinent à encadrer des profils "
                    "inexpérimentés qui nécessitent du tutorat quotidien. Les entreprises ont donc massivement favorisé "
                    "les profils seniors, immédiatement opérationnels en autonomie. « L'IA automatise des tâches "
                    "répétitives, mais les jeunes diplômés ne font pas que des tâches répétitives — ils apprennent »,"
                    "explique Lucas Chancel, co-auteur de l'étude.\n\n"
                    "Ces conclusions sont contestées par plusieurs économistes qui pointent que la corrélation télétravail-"
                    "exclusion des juniors ne prouve pas la causalité. Le débat a des implications pratiques importantes : "
                    "si le télétravail est la cause principale, les entreprises pourraient corriger la situation en "
                    "organisant du mentoring hybride. Si c'est l'IA, la solution est structurellement différente et "
                    "nécessite des politiques de formation de plus grande ampleur."
                ),
                category="economy",
                authors=["Manon Paulic"],
            ),
            _article(
                105,
                "Campus IA en Seine-et-Marne : un projet à 50 milliards qui divise",
                "https://www.lagazettefrance.fr/campus-ia-seine-et-marne",
                summary="Le mégaprojet de datacenter annoncé lors du sommet Choose France suscite des inquiétudes environnementales.",
                text=(
                    "Le projet de campus dédié à l'intelligence artificielle annoncé en grande pompe lors du sommet "
                    "Choose France par le consortium américano-émirati BlackRock-MGX est au cœur d'une controverse "
                    "croissante en Seine-et-Marne. Ce campus de 400 hectares, comprenant des datacenters, des laboratoires "
                    "de recherche et des espaces de formation, représente un investissement annoncé de 50 milliards d'euros "
                    "sur dix ans — le plus grand investissement étranger jamais réalisé en France.\n\n"
                    "Les opposants, regroupés dans le collectif « IA pas en nos champs », contestent l'impact "
                    "environnemental d'une infrastructure aussi énergivore. Selon leurs calculs, les datacenters prévus "
                    "consommeraient l'équivalent de la consommation électrique annuelle de la ville de Rennes, et "
                    "nécessiteraient 15 millions de litres d'eau par jour pour le refroidissement — dans une région "
                    "déjà touchée par des épisodes de sécheresse croissants.\n\n"
                    "La préfecture de Seine-et-Marne a lancé une enquête publique dont les résultats sont attendus "
                    "pour septembre. Le gouvernement, de son côté, a accordé une dérogation aux règles de construction "
                    "en zone agricole, décision contestée devant le Conseil d'État par plusieurs associations "
                    "environnementales. Macron défend le projet comme un « investissement stratégique pour la "
                    "souveraineté numérique française », tandis que les Verts réclament un moratoire sur les "
                    "datacenters de grande taille jusqu'à la publication d'un bilan carbone indépendant."
                ),
                category="technology",
                authors=["Perrine Signoret"],
            ),
        ]

    # ── Fallback générique ───────────────────────────────────────────────────
    else:
        articles = [
            _article(
                401,
                f"Actualités : résultats de recherche pour « {query} »",
                "https://www.lefigaro.fr/actualites/recherche-2026",
                summary=f"Résultats agrégés pour la requête : {query}.",
                text=(
                    f"Les actualités relatives à « {query} » sont en cours de traitement par nos équipes éditoriales. "
                    "Plusieurs sources primaires convergent sur ce sujet, indiquant une actualité dynamique qui mérite "
                    "un suivi attentif. Les développements les plus récents datent de moins de 24 heures et n'ont pas "
                    "encore fait l'objet d'une synthèse complète.\n\n"
                    "Les observateurs spécialisés soulignent que cette thématique s'inscrit dans un contexte plus large "
                    "d'évolutions structurelles qui touchent plusieurs secteurs simultanément. Une analyse approfondie "
                    "nécessite de croiser les sources institutionnelles, les témoignages de terrain et les données "
                    "statistiques disponibles."
                ),
            ),
            _article(
                402,
                "France : actualités de la semaine en bref",
                "https://www.francetvinfo.fr/france/bref-semaine-2026",
                summary="Revue des principaux événements de la semaine en France.",
                text=(
                    "Cette semaine en France a été marquée par plusieurs développements significatifs sur les plans "
                    "politique, économique et social. Sur le front politique, les débats parlementaires sur la réforme "
                    "des retraites complémentaires ont repris après une suspension technique liée à un amendement "
                    "gouvernemental controversé.\n\n"
                    "Sur le plan économique, les chiffres de l'inflation de mai ont légèrement dépassé les attentes "
                    "des économistes, s'établissant à 2,4 % en glissement annuel selon l'INSEE. La Banque de France "
                    "maintient ses prévisions de croissance à 1,1 % pour l'année, tout en avertissant des risques "
                    "liés à un affaiblissement de la demande européenne."
                ),
            ),
        ]

    return SearchNews200Response(
        news=articles,
        available=len(articles),
        number=len(articles),
        offset=0,
    )
