// Source de vérité unique de l'URL de app/api_regles pour ce client.
// L'URL vient de l'environnement de build Vite (.env du client), pas d'une
// valeur en dur : VITE_API_REGLES_URL_DEV en local, VITE_API_REGLES_URL_PREPROD
// avant un build de déploiement (voir clients/regles_api_client/.env.example).
export const API_REGLES_URL =
  import.meta.env.VITE_API_REGLES_URL_DEV ??
  import.meta.env.VITE_API_REGLES_URL_PREPROD ??
  'https://regles.qualicheck.koabana.fr/'
