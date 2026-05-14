"""
Dev seed script — populates the database with realistic fixture data.

Usage (from backend/):
    uv run scripts/seed.py

Guards:
  - Refuses to run when ENVIRONMENT=production.
  - Fully idempotent: safe to run multiple times; existing rows are skipped.

Seeded entities (all linked to test@test.com):
  - 1 User  (test@test.com / test1234)
  - 5 Chats, each with 2 Messages (user turn + AI turn)
  - 5 PressReviews
"""

from __future__ import annotations

import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Ensure src/ is on the import path regardless of working directory
# ---------------------------------------------------------------------------
BACKEND_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = BACKEND_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

# ---------------------------------------------------------------------------
# Now import project modules
# ---------------------------------------------------------------------------
from dotenv import load_dotenv  # noqa: E402

load_dotenv(BACKEND_ROOT / ".env")

from core.config import ENVIRONMENT  # noqa: E402
from core.security import hash_password  # noqa: E402
from database.database import engine  # noqa: E402
from database.models import Chat, Message, MessageType, PressReview, User, UserRole  # noqa: E402
from sqlmodel import Session, select  # noqa: E402

# ---------------------------------------------------------------------------
# Guard: production safety
# ---------------------------------------------------------------------------
if ENVIRONMENT == "production":
    print("✗ Refusing to seed: ENVIRONMENT=production", file=sys.stderr)
    sys.exit(1)

# ---------------------------------------------------------------------------
# Fixture data
# ---------------------------------------------------------------------------
SEED_EMAIL = "test@test.com"
SEED_PASSWORD = "test1234"

CHATS: list[dict] = [
    {
        "date": "10/12/2026",
        "messages": [
            {
                "type": MessageType.USER,
                "content": "Peux-tu me donner les dernières actualités politiques ?",
                "timestamp": "2026-12-10T10:30:00",
            },
            {
                "type": MessageType.AI,
                "content": (
                    "Voici un **résumé des dernières nouvelles politiques** :\n\n"
                    "- Le gouvernement a annoncé de nouvelles **mesures économiques**\n"
                    "- Débat sur la _réforme des retraites_ au Parlement\n"
                    "- Visite diplomatique prévue la semaine prochaine\n\n"
                    "> Ces informations sont issues de sources vérifiées au **10 décembre 2026**.\n\n"
                    "Souhaitez-vous que je génère une revue de presse détaillée sur l'un de ces sujets ?"
                ),
                "timestamp": "2026-12-10T10:31:00",
            },
        ],
    },
    {
        "date": "11/12/2026",
        "messages": [
            {
                "type": MessageType.USER,
                "content": "Quelles sont les nouvelles économiques du jour ?",
                "timestamp": "2026-12-11T09:00:00",
            },
            {
                "type": MessageType.AI,
                "content": (
                    "Voici les **principales nouvelles économiques** :\n\n"
                    "- **Inflation** : recul à 2,1 % sur un an\n"
                    "- **CAC 40** : en hausse de 0,8 % à l'ouverture\n"
                    "- **Emploi** : baisse du taux de chômage à 7,2 %\n\n"
                    "> Source : données consolidées au **11 décembre 2026**.\n\n"
                    "Voulez-vous une analyse approfondie ou une revue de presse sur ce thème ?"
                ),
                "timestamp": "2026-12-11T09:01:00",
            },
        ],
    },
    {
        "date": "12/12/2026",
        "messages": [
            {
                "type": MessageType.USER,
                "content": "Résume-moi l'actualité internationale de cette semaine.",
                "timestamp": "2026-12-12T14:00:00",
            },
            {
                "type": MessageType.AI,
                "content": (
                    "**Actualité internationale — semaine du 8 au 12 décembre 2026** :\n\n"
                    "1. **Europe** : sommet européen sur la défense à Bruxelles\n"
                    "2. **États-Unis** : débat au Congrès sur le budget fédéral 2027\n"
                    "3. **Asie** : tensions commerciales entre Pékin et Washington\n"
                    "4. **Afrique** : accord de paix signé au Soudan\n\n"
                    "> Données issues des grandes agences de presse au **12 décembre 2026**."
                ),
                "timestamp": "2026-12-12T14:01:00",
            },
        ],
    },
    {
        "date": "13/12/2026",
        "messages": [
            {
                "type": MessageType.USER,
                "content": "Y a-t-il des développements technologiques notables cette semaine ?",
                "timestamp": "2026-12-13T11:00:00",
            },
            {
                "type": MessageType.AI,
                "content": (
                    "**Technologie — faits marquants du 13 décembre 2026** :\n\n"
                    "- **IA générative** : nouvelle mise à jour majeure des modèles de langage\n"
                    "- **Semi-conducteurs** : annonce d'un investissement européen de 10 Md€\n"
                    "- **Spatial** : lancement réussi d'un satellite d'observation climatique\n\n"
                    "> Souhaitez-vous une revue de presse approfondie sur l'un de ces sujets ?"
                ),
                "timestamp": "2026-12-13T11:01:00",
            },
        ],
    },
    {
        "date": "14/12/2026",
        "messages": [
            {
                "type": MessageType.USER,
                "content": "Génère une revue de presse sur le climat.",
                "timestamp": "2026-12-14T08:30:00",
            },
            {
                "type": MessageType.AI,
                "content": (
                    "## Revue de presse — **Climat & Environnement** (14 déc. 2026)\n\n"
                    "### Faits saillants\n"
                    "- **COP32** : les négociations achoppent sur les financements des pays en développement\n"
                    "- **Températures** : novembre 2026 classé mois le plus chaud jamais enregistré\n"
                    "- **Énergies renouvelables** : la part du solaire dépasse 20 % du mix européen\n\n"
                    "### Analyse\n"
                    "> _Les engagements actuels restent insuffisants pour limiter le réchauffement "
                    "à 1,5 °C selon le dernier rapport du GIEC._\n\n"
                    "Voulez-vous que j'approfondisse un point particulier ?"
                ),
                "timestamp": "2026-12-14T08:31:00",
            },
        ],
    },
]

PRESS_REVIEWS: list[dict] = [
    {
        "title": "Revue de presse — Économie (30 sept. 2026)",
        "description": "2026-09-30T09:00:00",
        "content": (
            "## **Points clés**\n\n"
            "### Économie\n"
            "- **Marchés** : le CAC 40 termine le trimestre en hausse de 4,2 %\n"
            "- **Politique budgétaire** : présentation du projet de loi de finances 2027 au Parlement\n\n"
            "### Politique\n"
            "- _Remaniement ministériel_ attendu après les résultats des régionales\n"
            "- **Réforme des retraites** : nouvelles concertations syndicales prévues en octobre\n\n"
            "### Analyse\n"
            "> La conjoncture économique reste fragile malgré des signaux encourageants sur l'emploi. "
            "Les prochaines semaines seront décisives pour le budget 2027."
        ),
    },
    {
        "title": "Revue de presse — International (15 mai 2026)",
        "description": "2026-05-15T14:00:00",
        "content": (
            "## **Développements récents**\n\n"
            "### À la une\n"
            "1. **Diplomatie** : sommet G7 au Japon, focus sur la sécurité alimentaire mondiale\n"
            "2. **Conflit** : cessez-le-feu négocié sous égide ONU dans la région du Sahel\n"
            "3. **Commerce** : accord commercial UE–Mercosur ratifié après dix ans de négociations\n\n"
            "### Experts\n"
            "- **Analyse géopolitique** : reconfiguration des alliances en Asie du Sud-Est\n"
            "- **Économie mondiale** : le FMI revoit à la hausse ses prévisions de croissance\n\n"
            "> **À retenir** : la stabilité des marchés émergents reste conditionnée à la maîtrise "
            "de l'inflation dans les grandes économies."
        ),
    },
    {
        "title": "Revue de presse — Science & Tech (1er juin 2026)",
        "description": "2026-06-01T10:00:00",
        "content": (
            "## **Rapport approfondi**\n\n"
            "### Synthèse\n"
            "**Vue d'ensemble** : la semaine a été marquée par plusieurs annonces majeures "
            "dans le domaine de l'intelligence artificielle et de la biotechnologie.\n\n"
            "### Analyse détaillée\n"
            "- _IA_ : publication d'un nouveau benchmark multimodal dépassant les capacités humaines\n"
            "- **Santé** : essai clinique de phase III concluant pour un vaccin contre la dengue\n"
            "- **Espace** : la mission Europa Clipper transmet ses premières images de la lune jovienne\n\n"
            "### Points à retenir\n"
            "1. L'IA générative transforme désormais la recherche académique\n"
            "2. Les biotech européennes attirent un niveau record d'investissements\n"
            "3. La course spatiale privée s'intensifie\n\n"
            "> **Conclusion** : l'innovation technologique accélère à un rythme sans précédent, "
            "soulevant des questions éthiques et réglementaires croissantes."
        ),
    },
    {
        "title": "Revue de presse — Environnement (20 juin 2026)",
        "description": "2026-06-20T08:00:00",
        "content": (
            "## **Couverture complète**\n\n"
            "### Thèmes principaux\n"
            "**Canicule européenne** : vague de chaleur record dans le bassin méditerranéen, "
            "températures dépassant 45 °C en Espagne et en Italie.\n\n"
            "**Biodiversité** : publication du rapport annuel du WWF, perte de 38 % des populations "
            "sauvages depuis 2000.\n\n"
            "### Détail par section\n"
            "- **Politique climatique** : la Commission européenne propose un durcissement du marché carbone\n"
            "- **Énergie** : le nucléaire revient au cœur du débat énergétique en France et en Pologne\n"
            "- **Agriculture** : sécheresse persistante en Occitanie, déclaration de catastrophe naturelle\n\n"
            "### Conclusion\n"
            "> L'urgence climatique n'est plus une projection : elle s'impose comme une réalité "
            "quotidienne pour des millions de citoyens européens."
        ),
    },
    {
        "title": "Revue de presse — Culture & Société (5 juil. 2026)",
        "description": "2026-07-05T16:00:00",
        "content": (
            "## **Éclairage culture & société**\n\n"
            "### Résumé\n"
            "**En bref** : retour sur une semaine riche en événements culturels et débats de société.\n\n"
            "### Faits marquants\n"
            "- _Festival d'Avignon_ : affluence record, 150 000 spectateurs en dix jours\n"
            "- **Éducation** : rapport sur le décrochage scolaire post-Covid, +12 % par rapport à 2019\n"
            "- **Numérique** : adoption de la loi sur l'identité numérique au Sénat\n\n"
            "### Points à retenir\n"
            "1. La culture reste un vecteur de cohésion sociale malgré les contraintes budgétaires\n"
            "2. Le numérique transforme profondément les modes d'apprentissage\n"
            "3. Le débat sur la place des écrans à l'école s'intensifie\n\n"
            "> **Synthèse finale** : la société française navigue entre volonté de modernisation "
            "et attachement aux repères culturels traditionnels."
        ),
    },
]


# ---------------------------------------------------------------------------
# Seed logic
# ---------------------------------------------------------------------------


def seed() -> None:
    with Session(engine) as session:
        # -- User ----------------------------------------------------------
        user = session.exec(select(User).where(User.email == SEED_EMAIL)).first()
        if not user:
            user = User(
                email=SEED_EMAIL,
                hashed_password=hash_password(SEED_PASSWORD),
                role=UserRole.USER,
            )
            session.add(user)
            session.flush()  # populate user.id before referencing it
            print(f"  + User created: {SEED_EMAIL}")
        else:
            print(f"  ~ User already exists: {SEED_EMAIL} (id={user.id})")

        # -- Chats & Messages ----------------------------------------------
        existing_chat_count = len(
            list(session.exec(select(Chat).where(Chat.user_id == user.id)).all())
        )
        if existing_chat_count >= len(CHATS):
            print(f"  ~ Chats already seeded ({existing_chat_count} found), skipping.")
        else:
            for chat_data in CHATS:
                chat = Chat(user_id=user.id, date=chat_data["date"])
                session.add(chat)
                session.flush()  # populate chat.id
                for msg_data in chat_data["messages"]:
                    session.add(
                        Message(
                            chat_id=chat.id,
                            type=msg_data["type"],
                            content=msg_data["content"],
                            timestamp=msg_data["timestamp"],
                        )
                    )
            print(f"  + {len(CHATS)} chats seeded with 2 messages each.")

        # -- Press Reviews -------------------------------------------------
        existing_review_count = len(
            list(
                session.exec(
                    select(PressReview).where(PressReview.user_id == user.id)
                ).all()
            )
        )
        if existing_review_count >= len(PRESS_REVIEWS):
            print(
                f"  ~ PressReviews already seeded ({existing_review_count} found), skipping."
            )
        else:
            for review_data in PRESS_REVIEWS:
                session.add(
                    PressReview(
                        user_id=user.id,
                        title=review_data["title"],
                        description=review_data["description"],
                        content=review_data["content"],
                    )
                )
            print(f"  + {len(PRESS_REVIEWS)} press reviews seeded.")

        session.commit()


if __name__ == "__main__":
    print(f"Seeding database (ENVIRONMENT={ENVIRONMENT}) …")
    seed()
    print("Done.")
