# ai-customer-support

Agent d'e-mails clients pour une banque belge fictive (Sambre Bank). Il lit une boîte Gmail, écarte les robots, classe chaque message, rédige une réponse avec un agent LLM qui lit une base de connaissances, et confie tout cas douteux à un humain. Voir README.md pour le détail du flux.

Principe : le modèle propose, le code décide. Les règles métier et le choix final répondre ou escalader sont en Python, pas dans les prompts.

## Stack et commandes

Python 3.13, uv, FastAPI, Pydantic AI avec Groq (`gpt-oss-20b`), Postgres sur Supabase, Gmail API, pydantic-evals, Docker Compose.

```bash
uv run python -m app.poller                 # la boucle
uv run python playground/try_pipeline.py    # pipeline IA sans Gmail, sans envoi
uv run python -m evals.run_evals            # 24 e-mails de référence, lancer deux fois après un changement de prompt
docker compose up -d --build                # api + poller
```

## Règles de travail

- Rester sur `main`, la branche d'origine. Pas de nouvelle branche sans demande.
- Code au minimum de lignes. Le README ne cite pas le cours d'origine.
- Messages de commit sans mention de Claude.
- Aucun secret dans les fichiers suivis : `.env` et `credentials.json` sont ignorés. Ne jamais écrire un mot de passe, une clé ou une IP ici.
- Le dépôt est public : pas de donnée personnelle dans ce fichier ni dans le README.

## État (mis à jour le 14-11-2026)

Fait :
- Setup, accès Gmail, base de données et poller, classifieur, agent, règles, decide.
- Évaluations : 24 cas, 100 % au dernier passage (13-11, un seul passage, les sorties varient).
- Déploiement sur un VPS le 13-11 : Docker Compose avec les services api et poller, utilisateur `deploy`, accès par `ssh support-vps`, dossier `~/ai-customer-support`. Poller toutes les 10 minutes. Vérifié de bout en bout : un e-mail de test a été traité et a reçu une réponse.

Reste à faire :
- Cocher le déploiement dans le README.
- Check de l'API sur le serveur : `ssh support-vps 'curl -s http://127.0.0.1:8080/health'`.
- Supprimer l'ancien clone sous root sur le VPS (son `.env` est périmé).
- Dashboard admin.
- Branche `fix/pipeline-fragilites` (ae4a6c5, trois corrections du pipeline) : pas encore fusionnée dans `main`.
- Limite connue : l'évaluation ne juge pas le texte des réponses.

## Pièges connus

- Depuis le VPS, la connexion directe à Supabase échoue depuis le réseau Docker (IPv6 seulement). Utiliser l'adresse du Session pooler dans `DATABASE_URL`.
- Une variable `DATABASE_URL` déjà présente dans un vieux terminal passe avant le `.env` (`load_dotenv` ne l'écrase pas). Hypothèse cohérente avec les journaux, non prouvée. Fermer les anciens terminaux en cas de doute.
- Erreur de connexion à la base : lire d'abord les journaux Supabase avant de supposer un blocage d'IP.

## Contexte hors dépôt

Le journal des sessions et le wiki de tous les projets sont dans `/Users/proftg/DataScience` : `memory/wiki/ai-customer-support.md` et `memory/sessions/`. En fin de session, utiliser `/fin`.
