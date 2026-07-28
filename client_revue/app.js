const API_BASE_URL = "http://localhost:8880";
let REGLES = [];

const state = { outil: new Set(), review_status: new Set(), theme: new Set(), phase: new Set(), selected: null, query: "" };

function normalise(texte) {
  return texte.normalize("NFD").replace(/\p{M}/gu, "").toLowerCase();
}

function statusLabel(s) {
  return { valide: "Validée", a_revoir: "À revoir", invalide: "Invalide", aucun: "Non revue" }[s || "aucun"];
}

function formatDate(iso) {
  if (!iso) return null;
  const d = new Date(iso);
  return d.toLocaleString("fr-FR", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" });
}

function matches(regle) {
  const okOutil = state.outil.size === 0 || regle.outils.some(o => state.outil.has(o));
  const status = regle.review_status || "aucun";
  const okStatus = state.review_status.size === 0 || state.review_status.has(status);
  const okTheme = state.theme.size === 0 || state.theme.has(regle.theme);
  const okPhase = state.phase.size === 0 || regle.phases.some(p => state.phase.has(p));

  const okQuery = !state.query || normalise(regle.intitule).includes(state.query);

  return okOutil && okStatus && okTheme && okPhase && okQuery;
}

function renderList() {
  const list = document.getElementById("list");
  const visibles = REGLES.filter(matches);
  document.getElementById("result-count").textContent = visibles.length;

  if (visibles.length === 0) {
    list.innerHTML = '<div class="list-empty">Aucune règle ne correspond aux filtres sélectionnés.</div>';
    return;
  }

  list.innerHTML = visibles.map(r => {
    const status = r.review_status || "aucun";
    const selected = state.selected === r.numero ? " is-selected" : "";
    return `
      <div class="list-row${selected}" data-numero="${r.numero}" role="button" tabindex="0">
        <div class="numero mono">n°${r.numero}</div>
        <div>
          <div class="intitule">${r.intitule}</div>
          <div class="meta">
            ${r.outils.map(o => `<span class="outil-tag">${o}</span>`).join("")}
          </div>
        </div>
        <span class="status-pill ${status}">${statusLabel(status)}</span>
      </div>`;
  }).join("");

  list.querySelectorAll(".list-row").forEach(row => {
    row.addEventListener("click", () => selectRegle(Number(row.dataset.numero)));
    row.addEventListener("keydown", e => {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); selectRegle(Number(row.dataset.numero)); }
    });
  });
}

function selectRegle(numero) {
  state.selected = numero;
  renderList();
  renderDetail(REGLES.find(r => r.numero === numero));
}

function renderDetail(r) {
  const detail = document.getElementById("detail");
  const status = r.review_status || "aucun";

  detail.innerHTML = `
    <div class="detail-eyebrow mono">Règle n°${r.numero} · ${r.theme}</div>
    <div class="detail-head">
      <h2>${r.intitule}</h2>
      <span class="status-pill ${status}" style="font-size:12px;padding:5px 12px;">${statusLabel(status)}</span>
    </div>
    <div class="detail-meta-row">
      ${r.outils.map(o => `<span class="meta-tag">Outil : ${o}</span>`).join("")}
      ${r.tags.map(t => `<span class="meta-tag">#${t}</span>`).join("")}
      ${r.phases.map(p => `<span class="meta-tag">Phase : ${p}</span>`).join("")}
    </div>

    ${r.contexte ? `<div class="section"><h3>Contexte</h3><p>${r.contexte}</p></div>` : ""}

    <div class="section"><h3>Solution</h3><p>${r.solution}</p></div>
    <div class="section"><h3>Contrôle</h3><p>${r.controle}</p></div>

    <div class="section">
      <h3>Guide d'analyse (généré par l'agent)</h3>
      <p>${r.guide_analyse}</p>
      <p style="margin-top:10px;color:var(--ink-soft);font-size:12.5px;"><strong>Justification de la stratégie —</strong> ${r.strategie_justification}</p>
    </div>

    <div class="provenance mono">
      <span><b>strategie_analyse</b> ${r.strategie_analyse}</span>
      <span><b>prompt_version</b> ${r.prompt_version}</span>
      <span><b>llm_model</b> ${r.llm_model}</span>
    </div>

    <div class="annotation">
      <h3>Annotation de revue</h3>
      <div class="segmented" id="segmented">
        ${["aucun","valide","a_revoir","invalide"].map(v => `
          <label class="${status === v ? "checked-" + v : ""}" data-value="${v}">
            <input type="radio" name="review_status" value="${v}" ${status === v ? "checked" : ""} />
            ${statusLabel(v)}
          </label>`).join("")}
      </div>

      <div class="note-field">
        <label class="field-label" for="review-note">Note de revue <span id="note-required" class="required-mark" style="display:${(status==='a_revoir'||status==='invalide')?'inline':'none'}">— obligatoire</span></label>
        <textarea id="review-note" placeholder="Expliquez le problème de classification, à l'attention du prochain enrich_again…">${r.review_note || ""}</textarea>
        <div class="field-hint">Cette note est réinjectée telle quelle dans le prompt lors du prochain <span class="mono">make enrich-again</span>.</div>
        <div class="field-error" id="note-error">Une note est obligatoire pour les statuts « À revoir » et « Invalide ».</div>
        <div class="field-error" id="patch-error"></div>
      </div>

      <div class="annotation-footer">
        <span class="reviewed-at mono">${r.reviewed_at ? "Dernière revue : " + formatDate(r.reviewed_at) : "Jamais revue"}</span>
        <button class="btn-save" id="btn-save">Enregistrer l'annotation</button>
      </div>
    </div>
  `;

  const segmented = detail.querySelector("#segmented");
  const noteField = detail.querySelector("#review-note");
  const noteRequired = detail.querySelector("#note-required");

  segmented.querySelectorAll("label").forEach(label => {
    label.addEventListener("click", () => {
      segmented.querySelectorAll("label").forEach(l => l.className = "");
      const v = label.dataset.value;
      label.className = "checked-" + v;
      noteRequired.style.display = (v === "a_revoir" || v === "invalide") ? "inline" : "none";
    });
  });

  detail.querySelector("#btn-save").addEventListener("click", async () => {
    const chosen = segmented.querySelector("input:checked").value;
    const note = noteField.value.trim();
    const errorEl = detail.querySelector("#note-error");
    if ((chosen === "a_revoir" || chosen === "invalide") && !note) {
      errorEl.classList.add("is-visible");
      noteField.focus();
      return;
    }
    errorEl.classList.remove("is-visible");
    const erreurPatch = detail.querySelector("#patch-error");
    erreurPatch.classList.remove("is-visible");

    const corps = {
      review_status: chosen === "aucun" ? null : chosen,
      review_note: chosen === "aucun" ? null : (note || null),
    };

    let reponse;
    try {
      reponse = await fetch(`${API_BASE_URL}/regles/${r.numero}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${champJeton.value}`,
        },
        body: JSON.stringify(corps),
      });
    } catch {
      erreurPatch.textContent = "Impossible de contacter l'API — vérifier qu'elle tourne (make api-regles).";
      erreurPatch.classList.add("is-visible");
      return;
    }

    if (!reponse.ok) {
      const messages = {
        401: "Jeton invalide ou absent.",
        404: "Règle introuvable (a-t-elle été supprimée ?).",
      };
      if (messages[reponse.status]) {
        erreurPatch.textContent = messages[reponse.status];
      } else {
        const corpsErreur = await reponse.json().catch(() => ({}));
        const detail = corpsErreur.detail;
        erreurPatch.textContent = typeof detail === "string"
          ? detail
          : Array.isArray(detail)
            ? detail.map(e => e.msg).join(" ")
            : `Erreur ${reponse.status}.`;
      }
      erreurPatch.classList.add("is-visible");
      return;
    }

    const miseAJour = await reponse.json();
    const index = REGLES.findIndex(regle => regle.numero === miseAJour.numero);
    REGLES[index] = miseAJour;
    renderList();
    renderDetail(miseAJour);
    showToast(chosen === "aucun" ? "Annotation effacée." : "Annotation enregistrée.");
  });
}

function showToast(message) {
  const toast = document.getElementById("toast");
  toast.textContent = message;
  toast.classList.add("is-visible");
  clearTimeout(showToast._t);
  showToast._t = setTimeout(() => toast.classList.remove("is-visible"), 2200);
}

document.getElementById("search").addEventListener("input", e => {
  state.query = normalise(e.target.value.trim());
  renderList();
});

document.querySelectorAll(".filter-group").forEach(group => {
  const key = group.dataset.group;
  group.querySelectorAll(".chip").forEach(chip => {
    const input = chip.querySelector("input");
    chip.addEventListener("click", e => {
      e.preventDefault();
      input.checked = !input.checked;
      chip.classList.toggle("is-active", input.checked);
      if (input.checked) state[key].add(input.value); else state[key].delete(input.value);
      renderList();
    });
  });
});

async function chargerRegles() {
  const reponse = await fetch(`${API_BASE_URL}/regles`);
  if (!reponse.ok) {
    document.getElementById("list").innerHTML =
      '<div class="list-empty">Impossible de charger les règles depuis l\'API — vérifier qu\'elle tourne (make api-regles).</div>';
    return;
  }
  REGLES = await reponse.json();
  renderList();
}

const CLE_JETON = "jetonApiRevue";
const champJeton = document.getElementById("jeton-api");
champJeton.value = localStorage.getItem(CLE_JETON) || "";
champJeton.addEventListener("input", () => {
  localStorage.setItem(CLE_JETON, champJeton.value);
});
document.getElementById("jeton-effacer").addEventListener("click", () => {
  champJeton.value = "";
  localStorage.removeItem(CLE_JETON);
});

chargerRegles();
