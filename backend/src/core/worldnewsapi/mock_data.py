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
        publish_date: str = date,
    ) -> TopNews200ResponseTopNewsInnerNewsInner:
        return TopNews200ResponseTopNewsInnerNewsInner(
            id=id,
            title=title,
            url=url,
            summary=summary,
            publish_date=publish_date,
            text="",
            author=None,
            authors=[],
            image=None,
        )

    clusters = [
        TopNews200ResponseTopNewsInner(
            news=[
                _article(
                    1,
                    "Sommet du G7 : Emmanuel Macron reçoit les leaders mondiaux à Évian",
                    "https://www.lemonde.fr/politique/g7-evian-2026",
                    "Le sommet du G7 s'ouvre à Évian avec l'IA, la défense et le climat à l'ordre du jour.",
                ),
                _article(
                    2,
                    "G7 à Évian : Sam Altman (OpenAI) parmi les invités de Macron",
                    "https://www.bfmtv.com/tech/g7-sam-altman-macron",
                    "Sam Altman participera aux discussions sur la régulation de l'intelligence artificielle.",
                ),
            ]
        ),
        TopNews200ResponseTopNewsInner(
            news=[
                _article(
                    3,
                    "Ukraine : Zelensky propose une rencontre directe avec Poutine",
                    "https://www.rfi.fr/europe/ukraine-zelensky-poutine",
                    "Dans une lettre ouverte, le président ukrainien appelle à un cessez-le-feu immédiat.",
                ),
                _article(
                    4,
                    "Guerre en Ukraine : trois morts dans des frappes russes sur Kherson",
                    "https://www.lemonde.fr/international/ukraine-frappes-kherson",
                    "L'armée russe a visé des infrastructures civiles dans le sud du pays.",
                ),
                _article(
                    5,
                    "Ukraine : la France intensifie sa formation de soldats",
                    "https://www.lavoixdunord.fr/ukraine-formation-france",
                    "Des centaines de militaires ukrainiens sont formés en France chaque mois.",
                ),
            ]
        ),
        TopNews200ResponseTopNewsInner(
            news=[
                _article(
                    6,
                    "Disparition de Lyhanna : un corps retrouvé dans le Gers, suspect interpellé",
                    "https://www.bfmtv.com/faits-divers/lyhanna-gers",
                    "Le ministre de l'Intérieur a convoqué une cellule de crise après la découverte.",
                ),
            ]
        ),
        TopNews200ResponseTopNewsInner(
            news=[
                _article(
                    7,
                    "Égalité salariale : la France rate l'échéance européenne du 7 juin",
                    "https://www.lanouvellerepublique.fr/egalite-salariale-france",
                    "La directive sur la transparence des salaires ne sera pas appliquée à temps.",
                ),
                _article(
                    8,
                    "Économie française : légère hausse du chômage au premier trimestre",
                    "https://www.lesechos.fr/economie/chomage-t1-2026",
                    "Le taux de chômage s'établit à 7,3 % selon les derniers chiffres de l'INSEE.",
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
        publish_date: str = "2026-06-05 08:00:00",
        category: str = "world",
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
            authors=[],
            text="",
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
                "Le président ukrainien propose une rencontre directe avec Poutine à Genève.",
            ),
            _article(
                202,
                "Donbass : les frappes russes s'intensifient sur trois oblasts",
                "https://www.lemonde.fr/international/donbass-frappes-russes-juin-2026",
                "L'armée russe a visé des infrastructures civiles dans le Donbass, causant 14 victimes.",
            ),
            _article(
                203,
                "Aide militaire à l'Ukraine : le Parlement européen vote un nouveau paquet de 10 Mrd €",
                "https://www.euronews.com/europe/aide-ukraine-parlement-europeen-2026",
                "La décision intervient lors du sommet de Bruxelles consacré à la défense collective.",
            ),
            _article(
                204,
                "Négociations de paix : les pourparlers Ukraine-Russie repoussés à une date indéterminée",
                "https://www.francetvinfo.fr/monde/ukraine-russie-negociations-2026",
                "Les médiateurs turcs et américains peinent à fixer un cadre acceptable pour les deux parties.",
            ),
            _article(
                205,
                "Ukraine : plus de 6 millions de réfugiés en Europe selon le HCR",
                "https://www.afp.com/fr/monde/ukraine-refugies-bilan-2026",
                "Le Haut-Commissariat aux réfugiés appelle à renforcer les programmes d'accueil.",
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
                "L'Union européenne espère relancer l'accord de 2015 après deux ans de blocage.",
            ),
            _article(
                302,
                "Sanctions contre l'Iran : Washington maintient la pression économique",
                "https://www.lefigaro.fr/international/iran-sanctions-usa-2026",
                "Le département du Trésor américain annonce de nouvelles restrictions sur le pétrole iranien.",
            ),
            _article(
                303,
                "Iran : manifestations à Téhéran après la mort d'une étudiante en garde à vue",
                "https://www.liberation.fr/international/iran-manifestations-2026",
                "Des milliers de personnes ont défié le couvre-feu malgré une répression intense.",
            ),
            _article(
                304,
                "Drones iraniens en Ukraine : l'UE prépare des contre-mesures",
                "https://www.rfi.fr/monde/iran-drones-ukraine-ue-2026",
                "Bruxelles envisage des sanctions ciblées contre les responsables du programme de drones.",
            ),
            _article(
                305,
                "Iran-Israël : escalade verbale après l'opération « Bouclier de Sion »",
                "https://www.france24.com/fr/moyen-orient/iran-israel-escalade-2026",
                "Le chef des Gardiens de la révolution menace de frappes préventives sur le territoire israélien.",
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
                "Selon un rapport parlementaire, la France doit doubler ses investissements en IA d'ici 2028.",
                category="technology",
            ),
            _article(
                102,
                "Doctolib et la protection des données de santé face aux géants de l'IA",
                "https://www.bfmtv.com/tech/doctolib-donnees-sante-ia",
                "Des questions persistent sur la capacité de Doctolib à protéger les données médicales des patients.",
                category="technology",
            ),
            _article(
                103,
                "Sam Altman au G7 : OpenAI veut une régulation internationale de l'IA",
                "https://www.leparisien.fr/tech/sam-altman-g7-regulation-ia",
                "Le PDG d'OpenAI plaide pour un traité mondial sur la sécurité de l'intelligence artificielle.",
                category="technology",
            ),
            _article(
                104,
                "L'IA et le chômage des jeunes : le télétravail plus responsable que l'automatisation",
                "https://www.ouest-france.fr/ia-chomage-jeunes-teletravail",
                "Une étude de Sciences Po suggère que le télétravail post-Covid explique davantage la baisse d'embauche des juniors.",
                category="economy",
            ),
            _article(
                105,
                "Campus IA en Seine-et-Marne : un projet à 50 milliards qui divise",
                "https://www.lagazettefrance.fr/campus-ia-seine-et-marne",
                "Le mégaprojet de datacenter annoncé lors du sommet Choose France suscite des inquiétudes environnementales.",
                category="technology",
            ),
        ]

    # ── Fallback générique ───────────────────────────────────────────────────
    else:
        articles = [
            _article(
                401,
                f"Actualités : résultats de recherche pour « {query} »",
                "https://www.lefigaro.fr/actualites/recherche-2026",
                f"Résultats agrégés pour la requête : {query}.",
            ),
            _article(
                402,
                "France : actualités de la semaine en bref",
                "https://www.francetvinfo.fr/france/bref-semaine-2026",
                "Revue des principaux événements de la semaine en France.",
            ),
        ]

    return SearchNews200Response(
        news=articles,
        available=len(articles),
        number=len(articles),
        offset=0,
    )
