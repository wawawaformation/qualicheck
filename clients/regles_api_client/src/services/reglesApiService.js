import { API_REGLES_URL } from '../apiServer.js'

// Tolère un slash final dans API_REGLES_URL (ex. valeur d'un environnement
// donnée avec ou sans "/" de fin) : sinon "https://x.fr/" + "/regles"
// produirait "https://x.fr//regles".
const BASE_URL = API_REGLES_URL.replace(/\/+$/, '')

export class ErreurAuthentification extends Error {}

export async function listerRegles() {
  const reponse = await fetch(`${BASE_URL}/regles`)
  if (!reponse.ok) {
    throw new Error(`Échec du chargement des règles (${reponse.status})`)
  }
  return reponse.json()
}

export async function annoterRegle(numero, { reviewStatus, reviewNote }, cle) {
  const reponse = await fetch(`${BASE_URL}/regles/${numero}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${cle}`,
    },
    body: JSON.stringify({ review_status: reviewStatus, review_note: reviewNote ?? null }),
  })

  if (reponse.status === 401) {
    throw new ErreurAuthentification('Clé API absente ou invalide')
  }
  if (!reponse.ok) {
    const corps = await reponse.json().catch(() => ({}))
    throw new Error(corps.detail ?? `Échec de l'annotation (${reponse.status})`)
  }
  return reponse.json()
}
