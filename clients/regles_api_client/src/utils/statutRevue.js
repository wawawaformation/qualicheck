const LIBELLES = {
  null: { classe: 'badge-statut--neutre', texte: 'Non revue' },
  a_revoir: { classe: 'badge-statut--danger', texte: 'À revoir' },
  valide: { classe: 'badge-statut--succes', texte: 'Validée' },
}

export function libelleStatut(reviewStatus) {
  return LIBELLES[reviewStatus] ?? LIBELLES[null]
}
