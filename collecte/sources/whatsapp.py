"""WhatsApp : l'application WhatsApp du PC, la discussion « Échange entre adhérents » de la communauté
Nouvelle Énergie 34, et elle seule.

L'application (5319275A.WhatsAppDesktop) affiche WhatsApp Web dans une page intégrée (WebView2).
À chaque lancement, le script :
1. ferme WhatsApp s'il est ouvert, puis le relance avec un port de lecture local (variable
   WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS posée une seconde, le temps du démarrage, puis retirée) ;
2. met la fenêtre en plein écran ;
3. si l'application n'est pas liée au téléphone, affiche le QR code et attend qu'on le scanne ;
4. ouvre la discussion, remonte jusqu'au dernier message déjà enregistré (la première fois : jusqu'au début),
   lit auteur, date, texte et le message cité (« en réponse à ») ;
5. referme WhatsApp et le relance normalement, sans le port.

Le script ne fait que lire : il n'écrit rien et n'envoie rien.
"""
import ctypes
import re
import shutil
import subprocess
import time
import urllib.request
import winreg
import zipfile
from datetime import datetime

import psutil

from collecte.depot import PRINCIPAL, REPONSE, SourceImpossible
from commun.config import DONNEES, SESSIONS, perimetre
from commun.fichiers import lire_csv
from commun.textes import PARIS, empreinte, sans_accents

AUMID = r"5319275A.WhatsAppDesktop_cv1g1gvanyjgm!App"
EXE = "WhatsApp.Root.exe"
PORT = 9333
VARIABLE = "WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS"
ATTENTE_QR_S = 600
DEBUG = SESSIONS / "debug"


# --- Démarrage de l'application -------------------------------------------------

def _diffuser_environnement():
    ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x001A, 0, "Environment", 0x0002, 3000,
                                             ctypes.byref(ctypes.c_ulong()))


def _variable(valeur: str | None):
    k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_SET_VALUE)
    try:
        if valeur is None:
            try:
                winreg.DeleteValue(k, VARIABLE)
            except FileNotFoundError:
                pass
        else:
            winreg.SetValueEx(k, VARIABLE, 0, winreg.REG_SZ, valeur)
    finally:
        winreg.CloseKey(k)
    _diffuser_environnement()


def _port_ouvert() -> bool:
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/version", timeout=2)
        return True
    except Exception:
        return False


def fermer_whatsapp():
    procs = [p for p in psutil.process_iter(["name"]) if (p.info["name"] or "").lower() == EXE.lower()]
    for p in procs:
        try:
            p.kill()
        except psutil.Error:
            pass
    psutil.wait_procs(procs, timeout=10)
    for _ in range(20):
        if not _port_ouvert():
            break
        time.sleep(0.5)


def lancer_whatsapp(avec_port: bool):
    if avec_port:
        _variable(f"--remote-debugging-port={PORT}")
    try:
        subprocess.Popen(["explorer.exe", rf"shell:AppsFolder\{AUMID}"])
        if avec_port:
            for _ in range(60):
                if _port_ouvert():
                    return
                time.sleep(1)
            raise SourceImpossible("WhatsApp s'est ouvert sans le port de lecture.")
    finally:
        if avec_port:
            time.sleep(1)
            _variable(None)  # les autres applications ne doivent jamais en hériter


def retablir():
    """Remet WhatsApp dans son état normal, sans port de lecture (après un arrêt forcé de la collecte)."""
    _variable(None)
    fermer_whatsapp()
    lancer_whatsapp(avec_port=False)


def plein_ecran():
    import win32con
    import win32gui
    import win32process
    pids = {p.pid for p in psutil.process_iter(["name"]) if (p.info["name"] or "").lower() == EXE.lower()}
    fenetres = []

    def voir(hwnd, _):
        if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
            if win32process.GetWindowThreadProcessId(hwnd)[1] in pids:
                fenetres.append(hwnd)
    for _ in range(20):
        win32gui.EnumWindows(voir, None)
        if fenetres:
            break
        time.sleep(0.5)
    for hwnd in fenetres:
        win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
        try:
            win32gui.SetForegroundWindow(hwnd)
        except Exception:
            pass


# --- Lecture de la page -----------------------------------------------------------

ETAT_PAGE = """() => {
  if (document.querySelector('#pane-side')) return 'connecte';
  if (document.querySelector('canvas[aria-label], div[data-ref] canvas')) return 'qr';
  const t = document.body ? document.body.innerText : '';
  if (/Bienvenue sur WhatsApp|Connexion|Se connecter|Log in/.test(t) && t.length < 600) return 'accueil';
  return 'chargement';
}"""

CLIQUER_CONNEXION = """() => {
  for (const el of document.querySelectorAll('button, [role=button], a')) {
    const t = (el.innerText || '').trim();
    if (/^(Connexion|Se connecter|Log in)$/i.test(t)) { el.click(); return true; }
  }
  return false;
}"""

# Messages visibles de la discussion ouverte.
# Structure de novembre 2026 : data-id = identifiant seul ; data-testid="author" (nom affiché puis numéro) ;
# data-testid="selectable-text" (texte) ; data-testid="quoted-message" (message cité). Les messages hors écran
# sont « virtualisés » (vides) : on ne garde que ceux qui ont leur data-pre-plain-text.
MESSAGES = """() => {
  const sortie = [];
  const hors_cite = el => !el.closest('[data-testid=quoted-message]');
  for (const bloc of document.querySelectorAll('#main [data-id]')) {
    const id = bloc.getAttribute('data-id') || '';
    if (!id || bloc.parentElement.closest('[data-id]')) continue;
    const pre = bloc.querySelector('[data-pre-plain-text]');
    if (!pre) continue;
    const auteurs = [...bloc.querySelectorAll('[data-testid=author]')].filter(hors_cite).map(a => a.innerText.trim());
    let cite = null;
    const q = bloc.querySelector('[data-testid=quoted-message]');
    if (q) {
      const qa = [...q.querySelectorAll('[data-testid=author]')].map(a => a.innerText.trim());
      const qt = q.querySelector('[data-testid=selectable-text], .quoted-mention');
      cite = { auteur: qa[0] || '', tel: qa[1] || '', texte: (qt ? qt.innerText : '').trim() };
    }
    const corps = [...pre.querySelectorAll('[data-testid=selectable-text], span.selectable-text')].filter(hors_cite);
    const texte = corps.length ? corps[0].innerText.trim() : '';
    sortie.push({ id, pre: pre.getAttribute('data-pre-plain-text'), nom: auteurs[0] || '', tel: auteurs[1] || '',
                  texte, cite });
  }
  return sortie;
}"""

# Remonte d'un peu moins d'un écran (lecture pas à pas : les messages sautés ne seraient jamais affichés).
# Renvoie [scrollTop avant, scrollHeight].
DEFILER_HAUT = """() => {
  let meilleur = null;
  for (const el of document.querySelectorAll('#main div')) {
    if (el.scrollHeight > el.clientHeight + 100 && /auto|scroll/.test(getComputedStyle(el).overflowY))
      if (!meilleur || el.scrollHeight > meilleur.scrollHeight) meilleur = el;
  }
  if (!meilleur) return [-1, -1];
  const avant = meilleur.scrollTop;
  meilleur.scrollTop = Math.max(0, avant - meilleur.clientHeight * 0.6);
  return [avant, meilleur.scrollHeight];
}"""

DEFILER_BAS = """() => {
  let meilleur = null;
  for (const el of document.querySelectorAll('#main div')) {
    if (el.scrollHeight > el.clientHeight + 100 && /auto|scroll/.test(getComputedStyle(el).overflowY))
      if (!meilleur || el.scrollHeight > meilleur.scrollHeight) meilleur = el;
  }
  if (!meilleur) return -1;
  meilleur.scrollTop = meilleur.scrollHeight;
  return meilleur.scrollHeight;
}"""


def _mid(data_id: str) -> str:
    """Identifiant du message. Ancien format « false_1203…@g.us_3EB0A1B2…_336…@c.us » → « 3EB0A1B2… » ;
    format de novembre 2026 : l'identifiant seul."""
    morceaux = data_id.split("_")
    if len(morceaux) > 2:
        return morceaux[2]
    return data_id if re.fullmatch(r"[0-9A-Fa-f]{10,64}", data_id) else empreinte(data_id)


ANCIENS_DU_TELEPHONE = """() => {
  for (const el of document.querySelectorAll('#main button, #main [role=button], #main div')) {
    const t = (el.innerText || '').trim();
    if (el.children.length <= 2 && /messages plus anciens|older messages/i.test(t) && t.length < 200) { el.click(); return true; }
  }
  return false;
}"""

DEBUT_DISCUSSION = """() => /a créé (le groupe|cette communauté)|created (group|this community)|chiffrés de bout en bout/i
  .test(((document.querySelector('#main [role=application]') || document.querySelector('#main')).innerText || '').slice(0, 4000))"""

ALERTES = """() => {
  const t = (document.querySelector('#main') || document.body).innerText || '';
  return { pause: /synchronisation est en pause|sync(ing)? is paused/i.test(t),
           ephemere: !!document.querySelector('#main [aria-label*="éphémère"], #main [aria-label*="isappearing"]') };
}"""

PRE = re.compile(r"\[(\d{1,2}):(\d{2})(?::(\d{2}))?, (\d{1,2})/(\d{1,2})/(\d{4})\] (.*?): ?$")


def _date(pre: str):
    m = PRE.match(pre or "")
    if not m:
        return None, ""
    h, mi, s, j, mo, a, auteur = m.groups()
    d = datetime(int(a), int(mo), int(j), int(h), int(mi), int(s or 0), tzinfo=PARIS)
    return d, auteur.strip()


def _diagnostic(page, nom: str):
    """Garde la structure de la page en local (sessions/debug, hors partage) quand quelque chose ne va pas."""
    DEBUG.mkdir(parents=True, exist_ok=True)
    try:
        html = page.evaluate("() => (document.querySelector('#app') || document.body).outerHTML")
        (DEBUG / f"whatsapp_{nom}.html").write_text(html[:3_000_000], encoding="utf-8")
    except Exception:
        pass


def attendre_connexion(page, journal):
    debut, qr_annonce = time.time(), False
    while time.time() - debut < ATTENTE_QR_S + 120:
        etat = page.evaluate(ETAT_PAGE)
        if etat == "connecte":
            return
        if etat == "accueil":
            page.evaluate(CLIQUER_CONNEXION)
        if etat in ("qr", "accueil") and not qr_annonce:
            journal("  WhatsApp n'est pas lié à ton téléphone : sur le téléphone, WhatsApp → Appareils connectés → "
                    "Connecter un appareil, puis scanne le QR code affiché dans la fenêtre WhatsApp du PC "
                    f"(j'attends {ATTENTE_QR_S // 60} minutes).")
            qr_annonce = True
        page.wait_for_timeout(3000)
    _diagnostic(page, "connexion")
    raise SourceImpossible("WhatsApp n'est pas connecté sur le PC (QR code non scanné à temps). "
                           "Relance la collecte quand tu as ton téléphone sous la main.")


def _mots(texte: str) -> set[str]:
    return {m.rstrip("s") for m in re.findall(r"\w+", sans_accents(texte).lower())}


def ouvrir_discussion(page, communaute: str, discussion: str, journal):
    page.wait_for_timeout(3000)
    recherche = page.query_selector("#side div[contenteditable='true'], #side input[type='text'], "
                                    "#side [role='textbox']")
    if not recherche:
        _diagnostic(page, "recherche")
        raise SourceImpossible("Zone de recherche de WhatsApp introuvable (sessions/debug/whatsapp_recherche.html).")
    recherche.click()
    page.keyboard.press("Control+A")
    page.keyboard.press("Backspace")
    page.keyboard.type(discussion, delay=60)
    page.wait_for_timeout(4000)
    # Le nom tapé et le titre affiché peuvent différer d'un accent, d'un pluriel ou d'un préfixe : on compare
    # les mots sans accents ni « s » final.
    voulu = _mots(discussion)
    candidats = [c for c in page.query_selector_all("#side span[title], #pane-side span[title]")
                 if voulu <= _mots(c.get_attribute("title") or "")]
    if not candidats:
        _diagnostic(page, "resultats")
        raise SourceImpossible(f"Discussion « {discussion} » introuvable dans WhatsApp.")
    for c in candidats:
        ligne = c.evaluate_handle("e => e.closest('[role=listitem], [role=row], [role=gridcell], [tabindex]') || e")
        texte_ligne = ligne.evaluate("e => e.innerText")
        if len(candidats) > 1 and not _mots(communaute) <= _mots(texte_ligne):
            continue
        ligne.as_element().click()
        break
    else:
        candidats[0].click()
        journal(f"  attention : plusieurs « {discussion} », la communauté n'a pas pu être vérifiée dans la liste")
    page.wait_for_selector("#main header", timeout=20000)
    page.wait_for_timeout(3000)
    entete = page.inner_text("#main header")
    if not voulu <= _mots(entete):
        raise SourceImpossible(f"La discussion ouverte n'est pas « {discussion} » (en-tête : {entete[:80]!r}).")


def lire_messages(page, connus: set, journal, verifier_arret=lambda: None) -> dict[str, dict]:
    """Remonte la discussion jusqu'à un message déjà connu (ou jusqu'au début) et renvoie les messages vus."""
    vus: dict[str, dict] = {}
    # WhatsApp peut ouvrir la discussion au premier message non lu : on descend d'abord tout en bas.
    hauteur = None
    for _ in range(30):
        for m in page.evaluate(MESSAGES):
            vus.setdefault(m["id"], m)
        h = page.evaluate(DEFILER_BAS)
        page.wait_for_timeout(1500)
        if h == hauteur:
            break
        hauteur = h
    # Puis on remonte d'un peu moins d'un écran à la fois, en lisant à chaque pas. Arrivé en haut, WhatsApp charge
    # les messages plus anciens (la hauteur grandit) ; s'il ne charge plus rien pendant ~25 s, c'est le début.
    calme, tours, hauteur = 0, 0, None
    while calme < 10:
        tours += 1
        verifier_arret()
        for m in page.evaluate(MESSAGES):
            vus.setdefault(m["id"], m)
        if connus and any(_mid(i) in connus for i in vus):
            break
        if page.evaluate(DEBUT_DISCUSSION):
            break
        page.evaluate(ANCIENS_DU_TELEPHONE)
        position, h = page.evaluate(DEFILER_HAUT)
        page.wait_for_timeout(1200 if position > 0 else 2500)
        calme = calme + 1 if position == 0 and h == hauteur else 0
        hauteur = h
        if tours % 50 == 0:
            journal(f"    {len(vus)} messages vus en remontant…")
    for m in page.evaluate(MESSAGES):
        vus.setdefault(m["id"], m)
    return vus


# --- Export intégré (menu ⋮ → Exporter la discussion → Tous les messages) ---------------------------------------
# Il donne l'heure à la seconde et rattrape ce que la lecture de l'écran aurait manqué, mais il omet les messages
# éphémères (constaté le 2026-11-08 : aucun des 13 messages du 2026-11-07 n'y figurait). Les deux sont donc combinés.

EXPORTS = DONNEES / "whatsapp" / "exports"
LIGNE_EXPORT = re.compile(r"^‎?\[(\d{1,2})/(\d{1,2})/(\d{2,4}),? (\d{1,2}):(\d{2})(?::(\d{2}))?\s?([AaPp]\.?[Mm]\.?)?\] (.*)$")
IGNORES_EXPORT = re.compile(r"^(\[Notification système\]|Ce message a été supprimé|Vous avez supprimé ce message|"
                            r"<Médias omis>|<.*(omis|absent|joint).*>|.*\(fichier joint\)$|null$)", re.I)


def exporter_discussion(nav, page, journal):
    """Exporte la discussion ouverte (sans les médias) dans donnees/whatsapp/exports/ et renvoie le .zip."""
    tmp = EXPORTS / "_en_cours"
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    s = nav.new_browser_cdp_session()
    s.send("Browser.setDownloadBehavior", {"behavior": "allowAndName", "downloadPath": str(tmp), "eventsEnabled": True})
    # (pas de touche Échap ici : elle fermerait la discussion)
    page.click("#main header [aria-label='Menu']", timeout=15000)
    page.wait_for_timeout(1200)
    page.get_by_text("Exporter la discussion", exact=True).click()
    dialogue = page.locator("[role=dialog]").filter(has_text="Tous les messages").last
    dialogue.wait_for(timeout=15000)
    radios = dialogue.locator("input[type=radio]")
    if radios.count():
        radios.first.check()  # « Tous les messages »
    dialogue.get_by_role("button", name="Exporter").click()
    debut = time.time()
    while time.time() - debut < 300:
        prets = [f for f in tmp.iterdir() if f.stat().st_size and zipfile.is_zipfile(f)]
        if prets:
            time.sleep(2)
            fichier = EXPORTS / f"export_{datetime.now(PARIS):%Y-%m-%d_%H%M%S}.zip"
            shutil.move(prets[0], fichier)
            shutil.rmtree(tmp, ignore_errors=True)
            for vieux in sorted(EXPORTS.glob("export_*.zip"))[:-10]:  # on garde les 10 derniers
                vieux.unlink()
            return fichier
        time.sleep(2)
    shutil.rmtree(tmp, ignore_errors=True)
    raise SourceImpossible("l'export de WhatsApp n'a produit aucun fichier en 5 minutes")


def lire_export(fichier) -> list[dict]:
    """chat.txt de l'export → [{date, auteur, texte}] (messages des participants seulement)."""
    with zipfile.ZipFile(fichier) as z:
        nom = next((n for n in z.namelist() if n.endswith(".txt")), None)
        if not nom:
            return []
        lignes = z.read(nom).decode("utf-8-sig", errors="replace").splitlines()
    messages, courant = [], None
    for ligne in lignes:
        m = LIGNE_EXPORT.match(ligne)
        if not m:
            if courant is not None:
                courant["texte"] += "\n" + ligne
            continue
        a, b, annee, h, mi, s, ampm, reste = m.groups()
        annee = int(annee) + (2000 if len(annee) == 2 else 0)
        h = int(h)
        if ampm:  # format américain : mois/jour, 12 h
            mois, jour = int(a), int(b)
            h = h % 12 + (12 if ampm.lower().startswith("p") else 0)
        else:
            jour, mois = int(a), int(b)
        courant = None
        if reste.startswith("- ") or ": " not in reste:
            continue  # message système (création, ajout de membre…)
        auteur, texte = reste.split(": ", 1)
        courant = {"date": datetime(annee, mois, jour, h, int(mi), int(s or 0)), "auteur": auteur.strip("‎ ~"),
                   "texte": texte}
        messages.append(courant)
    for msg in messages:
        msg["texte"] = msg["texte"].replace("‎", "").strip()
    return [msg for msg in messages if msg["texte"] and not IGNORES_EXPORT.match(msg["texte"])]


def _cle(date: str, texte: str) -> tuple:
    """Même message vu à l'écran (à la minute) et dans l'export (à la seconde)."""
    return date[:16], " ".join((texte or "").split())[:40]


def collecter(depot, journal) -> dict:
    from playwright.sync_api import sync_playwright

    conf = perimetre()["whatsapp"]
    communaute, discussion = conf["communaute"], conf["discussion"]
    compte = f"{communaute} — {discussion}"
    connus = set(depot.connus(compte))  # identifiants WhatsApp des messages déjà enregistrés
    # Messages des lancements précédents, pour rattacher une réponse à un vieux message.
    anciens = [{"commentaire_id": l["commentaire_id"], "auteur": l["auteur"], "auteur_id": l["auteur_id"],
                "date": l["date"], "texte": l["texte"].lstrip()} for l in lire_csv(depot.csv_de(compte))]

    journal("  fermeture de WhatsApp et relance avec le port de lecture")
    fermer_whatsapp()
    lancer_whatsapp(avec_port=True)
    try:
        plein_ecran()
        with sync_playwright() as pw:
            nav = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{PORT}")
            page = next((p for c in nav.contexts for p in c.pages if "web.whatsapp.com" in p.url), None)
            if page is None:
                raise SourceImpossible("Page WhatsApp introuvable dans l'application.")
            attendre_connexion(page, journal)
            ouvrir_discussion(page, communaute, discussion, journal)
            journal(f"  discussion « {discussion} » ouverte ; remontée jusqu'au dernier message connu")
            alertes = page.evaluate(ALERTES)
            if alertes.get("pause"):
                journal("  WhatsApp indique « La synchronisation est en pause » : l'historique n'est pas encore "
                        "entièrement arrivé sur le PC (ouvrir WhatsApp sur le téléphone)")
            vus = lire_messages(page, connus, journal, depot.verifier_arret)
            if not vus:
                _diagnostic(page, "messages")
                raise SourceImpossible("Aucun message lu dans la discussion (sessions/debug/whatsapp_messages.html).")
            export, note_export = [], ""
            try:
                fichier = exporter_discussion(nav, page, journal)
                export = lire_export(fichier)
                note_export = f"export intégré : {fichier.name}, {len(export)} messages de participants"
            except Exception as e:  # l'export n'est qu'un complément : la lecture de l'écran suffit
                note_export = f"export intégré impossible ({str(e).splitlines()[0][:150]})"
            journal(f"  {note_export}")
    finally:
        fermer_whatsapp()
        lancer_whatsapp(avec_port=False)

    # Mise en forme, dans l'ordre chronologique, avec rattachement des réponses au message cité.
    # data-pre-plain-text donne le nom du contact, ou le numéro pour un non-contact ; les spans « author » donnent
    # le nom affiché puis le numéro, mais seulement sur le premier message d'une série du même auteur.
    profils = {}
    for m in vus.values():
        _, cle = _date(m["pre"])
        if m.get("nom"):
            profils.setdefault(cle, (m["nom"].lstrip("~ ").strip(), m.get("tel", "")))
    lignes = []
    sans_texte = 0
    for wid, m in vus.items():
        d, cle = _date(m["pre"])
        if d is None or not m["texte"]:
            sans_texte += 1  # médias sans légende, messages système
            continue
        nom, tel = profils.get(cle, ("", ""))
        lignes.append({"_d": d, "_cite": m.get("cite"), "commentaire_id": _mid(wid), "auteur": nom or cle,
                       "auteur_id": tel or cle, "date": d.strftime("%Y-%m-%d %H:%M:%S"),
                       "date_exacte": "à la minute", "texte": m["texte"]})
    # Messages de l'export absents de l'écran (et des lancements précédents) : ajoutés avec l'heure à la seconde.
    deja = {_cle(l["date"], l["texte"]) for l in anciens + lignes}
    du_export = 0
    for msg in export:
        date = msg["date"].strftime("%Y-%m-%d %H:%M:%S")
        if _cle(date, msg["texte"]) in deja:
            continue
        deja.add(_cle(date, msg["texte"]))
        du_export += 1
        tel = msg["auteur"] if re.fullmatch(r"\+?[\d \-()]{6,}", msg["auteur"]) else ""
        lignes.append({"_d": msg["date"], "_cite": None, "commentaire_id": "x" + empreinte(date, msg["auteur"], msg["texte"]),
                       "auteur": msg["auteur"], "auteur_id": tel or msg["auteur"], "date": date, "date_exacte": "oui",
                       "texte": msg["texte"]})
    # Un message déjà enregistré par l'export lors d'un lancement précédent n'est pas réenregistré depuis l'écran.
    vieux = {_cle(l["date"], l["texte"]) for l in anciens}
    lignes = [l for l in lignes if _cle(l["date"], l["texte"]) not in vieux]
    lignes.sort(key=lambda l: l["_d"])
    for l in lignes:
        l.pop("_d")
    candidats = anciens + lignes

    def net(s):
        return " ".join((s or "").split())

    for i, l in enumerate(lignes):
        cite = l.pop("_cite")
        l["type"], l["parent_id"] = PRINCIPAL, ""
        if cite and (cite.get("texte") or cite.get("auteur")):
            l["type"] = REPONSE
            extrait = net(cite.get("texte"))[:60]
            for cand in reversed(candidats[:len(anciens) + i]):
                meme_auteur = (not (cite.get("auteur") or cite.get("tel"))
                               or (cite.get("tel") and cite["tel"] == cand.get("auteur_id"))
                               or cite.get("auteur") in (cand["auteur"], cand.get("auteur_id"), "Vous", "You"))
                if extrait and net(cand["texte"]).startswith(extrait) and meme_auteur:
                    l["parent_id"] = cand["commentaire_id"]
                    break
    ajoutes = depot.ajouter(compte, lignes)
    depot.etat["dernier_lancement"] = datetime.now(PARIS).isoformat(timespec="seconds")
    reponses = sum(1 for l in lignes if l["type"] == REPONSE)
    rattachees = sum(1 for l in lignes if l["type"] == REPONSE and l["parent_id"])
    details = [f"{len(vus)} messages vus, {ajoutes} nouveaux, {sans_texte} sans texte (médias, système) ignorés",
               f"réponses : {reponses}, dont {rattachees} rattachées au message cité",
               f"{note_export} ; {du_export} ajoutés depuis l'export (absents de l'écran)"]
    if alertes.get("pause"):
        details.append("WhatsApp indique « La synchronisation est en pause » : ouvrir WhatsApp sur le téléphone pour "
                       "que l'historique arrive sur le PC")
    if alertes.get("ephemere"):
        details.append("messages éphémères activés dans la discussion : les messages disparaissent au bout d'un "
                       "temps, il faut lancer la collecte assez souvent pour ne rien perdre")
    if lignes:
        details.append(f"du {lignes[0]['date']} au {lignes[-1]['date']}")
    return {"details": details}
