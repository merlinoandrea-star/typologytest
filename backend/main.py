from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import anthropic
import os
import traceback
import httpx
import asyncio
import uuid
from threading import Thread

app = FastAPI(title="Typology API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

@app.options("/{rest_of_path:path}")
async def preflight_handler(rest_of_path: str):
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )

api_key = os.environ.get("ANTHROPIC_API_KEY")
client = anthropic.Anthropic(api_key=api_key) if api_key else None

# ── Job store (in-memory) ──────────────────────────────────────────────────
JOBS: dict = {}  # job_id -> {"status": "pending"|"done", "sections": {...}}

# ── HumanTypology RAG ────────────────────────────────────────────────────────
HUMTYPO_URL = "https://humantypology-api.onrender.com"
HUMTYPO_TOKEN = os.environ.get("HUMTYPO_API_TOKEN", "")

FUNCTION_NAMES_IT = {
    "E": "Estroverso", "I": "Introverso",
    "T": "Pensiero",   "F": "Sentimento",
    "S": "Sensazione", "N": "Intuizione"
}

async def rag_ask_async(question: str, top_k: int = 5) -> str:
    """Interroga il RAG in modo asincrono e sintetizza con Claude."""
    try:
        async with httpx.AsyncClient(timeout=25.0) as ac:
            resp = await ac.post(
                f"{HUMTYPO_URL}/ask",
                json={"question": question, "top_k": top_k},
                headers={"x-admin-token": HUMTYPO_TOKEN},
            )
            resp.raise_for_status()
            data = resp.json()

        if data.get("answer"):
            return data["answer"]

        chunks = data.get("chunks", [])
        if not chunks:
            return ""

        context = "\n\n---\n\n".join(c["text"] for c in chunks if c.get("text"))
        if not context.strip() or not client:
            return context[:500] if context else ""

        synthesis = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=600,
            system=(
                "Sei un esperto di psicologia junghiana. "
                "Rispondi in italiano in modo chiaro e professionale. "
                "Usa solo le informazioni del contesto fornito."
            ),
            messages=[{
                "role": "user",
                "content": f"Contesto:\n\n{context}\n\nDomanda: {question}\n\nRispondi in modo discorsivo."
            }]
        )
        return synthesis.content[0].text

    except Exception as e:
        return ""

def rag_ask(question: str, top_k: int = 5) -> str:
    """Wrapper sincrono per compatibilità."""
    try:
        return asyncio.get_event_loop().run_until_complete(rag_ask_async(question, top_k))
    except Exception:
        return ""

def build_profile_sections(type_code: str, orientation: str, dominant: str,
                            auxiliary: str, inferior: str, otroversion: str) -> dict:
    """Costruisce le 8 sezioni del profilo interrogando il RAG."""

    dom_name  = FUNCTION_NAMES_IT.get(dominant, dominant)
    aux_name  = FUNCTION_NAMES_IT.get(auxiliary, auxiliary)
    inf_name  = FUNCTION_NAMES_IT.get(inferior, inferior)
    ori_name  = FUNCTION_NAMES_IT.get(orientation, orientation)
    sigla     = f"{orientation}-{dominant}-{auxiliary}-{inferior}"

    queries = {
        "panoramica": (
            f"Descrivi in modo completo e discorsivo il profilo tipologico {sigla} "
            f"({ori_name}, funzione dominante {dom_name}, ausiliaria {aux_name}). "
            f"Includi caratteristiche principali, comportamenti tipici e figure storiche rappresentative."
        ),
        "punti_forza": (
            f"Quali sono i punti di forza del tipo {sigla} con funzione dominante {dom_name}?"
        ),
        "aree_miglioramento": (
            f"Quali sono le aree di miglioramento e i rischi del tipo {sigla} "
            f"con funzione dominante {dom_name} e funzione inferiore {inf_name}?"
        ),
        "funzione_dominante": (
            f"Descrivi la funzione dominante {dom_name} nella tipologia junghiana: "
            f"come si manifesta, cosa caratterizza chi la ha come funzione principale."
        ),
        "funzione_ausiliaria": (
            f"Descrivi la funzione ausiliaria {aux_name} e come collabora con la funzione "
            f"dominante {dom_name} nel profilo {sigla}."
        ),
        "funzione_mediatrice": (
            f"Descrivi il ruolo della funzione mediatrice (terziaria) nella tipologia junghiana "
            f"per il profilo {sigla}."
        ),
        "funzione_inferiore": (
            f"Descrivi la funzione inferiore {inf_name} nel profilo {sigla}: "
            f"come si manifesta, quali rischi comporta e come integrarla nel percorso di crescita."
        ),
        "dinamica_evoluzione": (
            f"Descrivi la dinamica di evoluzione tra la funzione dominante {dom_name} "
            f"e la funzione inferiore {inf_name} nel tipo {sigla}: eccessi, ombra e integrazione."
        ),
        "prevalente_collaborante": (
            f"Descrivi come funzionano insieme la funzione prevalente {dom_name} "
            f"e la funzione collaborante {aux_name} nel profilo {sigla}."
        ),
        "tipi_affini": (
            f"Quali sono i tipi psicologici affini al profilo {sigla} "
            f"e quali caratteristiche li accomunano?"
        ),
        "tipo_opposto": (
            f"Qual è il tipo psicologico opposto/difficile per il profilo {sigla} "
            f"e come si manifesta la difficoltà relazionale?"
        ),
        "otroversione": (
            f"Descrivi l'otroversione '{otroversion}' nella tipologia junghiana: "
            f"cosa significa, come si manifesta nel profilo {sigla}."
        ),
        "sviluppo": (
            f"Descrivi il percorso di sviluppo e integrazione consigliato per il profilo {sigla}, "
            f"con particolare attenzione alla funzione inferiore {inf_name}."
        ),
        "altri_profili": (
            f"Come può il profilo {sigla} comunicare e lavorare efficacemente "
            f"con gli altri tipi psicologici diversi da sé? Suggerimenti pratici."
        ),
    }

    async def fetch_all():
        tasks = {key: rag_ask_async(query) for key, query in queries.items()}
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        return {k: (v if isinstance(v, str) else "") for k, v in zip(tasks.keys(), results)}

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, fetch_all())
                sections = future.result(timeout=55)
        else:
            sections = loop.run_until_complete(fetch_all())
    except Exception as e:
        sections = {key: "" for key in queries.keys()}

    return sections

# ── Questions & scoring ──────────────────────────────────────────────────────
QUESTIONS = [
  {"id":1,"scala":"TF","latoA":"T","testoA":"Quando ho bisogno di recuperare energie, preferisco stare da solo.","testoB":"Quando ho bisogno di recuperare energie, mi fa bene parlare o stare con qualcuno."},
  {"id":2,"scala":"TF","latoA":"T","testoA":"Preferisco un linguaggio diretto e ordinato.","testoB":"Preferisco un linguaggio accogliente e che metta a proprio agio."},
  {"id":3,"scala":"TF","latoA":"T","testoA":"Mi piace rendere le cose pratiche quando parlo.","testoB":"Mi piace proporre idee e possibilità."},
  {"id":4,"scala":"TF","latoA":"T","testoA":"Quando mi sento molto emozionato, mi aiuta tornare a qualcosa di concreto.","testoB":"Quando mi sento molto emozionato, mi aiuta immaginare come cambieranno le cose."},
  {"id":5,"scala":"TF","latoA":"T","testoA":"Preferisco soluzioni pratiche e già testate.","testoB":"Preferisco soluzioni creative anche se nuove."},
  {"id":6,"scala":"TF","latoA":"T","testoA":"A volte sono troppo diretto e rischio di sembrare freddo.","testoB":"A volte sono troppo accomodante e rischio di non essere chiaro."},
  {"id":7,"scala":"TF","latoA":"T","testoA":"A volte mi irrigidisco su principi troppo fissi.","testoB":"A volte evito scelte importanti per non creare disagi."},
  {"id":8,"scala":"TF","latoA":"T","testoA":"A volte evito cambiamenti che potrebbero aiutarmi.","testoB":"A volte sogno soluzioni senza metterle in pratica."},
  {"id":9,"scala":"TF","latoA":"T","testoA":"A volte evito cambiamenti per prudenza.","testoB":"A volte inseguo novità poco realistiche."},
  {"id":10,"scala":"TF","latoA":"T","testoA":"A volte metto troppa distanza tra me e i miei sentimenti.","testoB":"A volte mi lascio coinvolgere troppo dai sentimenti altrui."},
  {"id":11,"scala":"TF","latoA":"T","testoA":"In situazioni complesse, uso criteri chiari per orientarmi.","testoB":"In situazioni complesse, cerco di far sì che tutti si sentano considerati."},
  {"id":12,"scala":"TF","latoA":"T","testoA":"Tendo a valutare le situazioni in modo oggettivo.","testoB":"Tendo a valutare le situazioni considerando come si sentono le persone coinvolte."},
  {"id":13,"scala":"TF","latoA":"T","testoA":"Mi fido di più dei dati e dei fatti.","testoB":"Mi fido di più delle sensazioni e dell'atmosfera."},
  {"id":14,"scala":"TF","latoA":"T","testoA":"Preferisco decisioni coerenti con una logica precisa.","testoB":"Preferisco decisioni che tengano conto delle persone coinvolte."},
  {"id":15,"scala":"TF","latoA":"T","testoA":"Quando giudico una situazione, cerco di essere imparziale.","testoB":"Quando giudico una situazione, considero prima di tutto l'impatto sulle persone."},
  {"id":16,"scala":"TF","latoA":"T","testoA":"Sono più a mio agio con problemi tecnici che con problemi relazionali.","testoB":"Sono più a mio agio con problemi relazionali che con problemi tecnici."},
  {"id":17,"scala":"TF","latoA":"T","testoA":"Valuto le idee principalmente per la loro utilità pratica.","testoB":"Valuto le idee principalmente per il loro impatto sulle persone."},
  {"id":18,"scala":"TF","latoA":"T","testoA":"In un conflitto, cerco la soluzione più logica.","testoB":"In un conflitto, cerco la soluzione che preservi le relazioni."},
  {"id":19,"scala":"TF","latoA":"T","testoA":"Preferisco essere preciso anche a costo di sembrare rigido.","testoB":"Preferisco essere flessibile anche a costo di essere meno preciso."},
  {"id":20,"scala":"TF","latoA":"T","testoA":"Nelle decisioni importanti mi affido alla ragione.","testoB":"Nelle decisioni importanti mi affido ai valori e alle emozioni."},
  {"id":21,"scala":"TF","latoA":"T","testoA":"Trovo più facile criticare un'idea che sostenerla emotivamente.","testoB":"Trovo più facile sostenere le persone che analizzare le loro idee."},
  {"id":22,"scala":"TF","latoA":"T","testoA":"La coerenza logica è per me una priorità.","testoB":"L'armonia relazionale è per me una priorità."},
  {"id":23,"scala":"TF","latoA":"T","testoA":"Mi disturba l'incoerenza più del conflitto emotivo.","testoB":"Mi disturba il conflitto emotivo più dell'incoerenza logica."},
  {"id":24,"scala":"TF","latoA":"T","testoA":"Preferisco che le regole siano chiare e rispettate da tutti.","testoB":"Preferisco che le regole si adattino alle situazioni e alle persone."},
  {"id":25,"scala":"SN","latoA":"S","testoA":"Mi fido di ciò che posso osservare direttamente.","testoB":"Mi fido delle connessioni e dei pattern che percepisco."},
  {"id":26,"scala":"SN","latoA":"S","testoA":"Preferisco lavorare con dati concreti e verificabili.","testoB":"Preferisco lavorare con idee e possibilità future."},
  {"id":27,"scala":"SN","latoA":"S","testoA":"Amo i dettagli e la precisione.","testoB":"Amo le visioni d'insieme e i concetti."},
  {"id":28,"scala":"SN","latoA":"S","testoA":"Imparo meglio facendo esperienza diretta.","testoB":"Imparo meglio capendo i principi sottostanti."},
  {"id":29,"scala":"SN","latoA":"S","testoA":"Preferisco istruzioni chiare e passo-per-passo.","testoB":"Preferisco capire il senso generale e trovare la mia strada."},
  {"id":30,"scala":"SN","latoA":"S","testoA":"Mi concentro su ciò che è reale e presente.","testoB":"Mi concentro su ciò che potrebbe essere o diventare."},
  {"id":31,"scala":"SN","latoA":"S","testoA":"Tendo a essere pratico e concreto.","testoB":"Tendo a essere immaginativo e speculativo."},
  {"id":32,"scala":"SN","latoA":"S","testoA":"Preferisco soluzioni già testate.","testoB":"Preferisco soluzioni innovative anche se incerte."},
  {"id":33,"scala":"SN","latoA":"S","testoA":"Mi annoio quando le discussioni diventano troppo astratte.","testoB":"Mi annoio quando le discussioni restano troppo in superficie."},
  {"id":34,"scala":"SN","latoA":"S","testoA":"Tendo a ricordare i fatti con precisione.","testoB":"Tendo a ricordare le impressioni e i significati."},
  {"id":35,"scala":"SN","latoA":"S","testoA":"Mi piace la routine e la continuità.","testoB":"Mi piace la varietà e il cambiamento."},
  {"id":36,"scala":"SN","latoA":"S","testoA":"Sono attento ai dettagli pratici.","testoB":"Sono attento alle possibilità nascoste."},
  {"id":37,"scala":"SN","latoA":"S","testoA":"Preferisco lavorare con cose concrete.","testoB":"Preferisco lavorare con idee e concetti."},
  {"id":38,"scala":"SN","latoA":"S","testoA":"Mi fido di ciò che è stato provato nel tempo.","testoB":"Mi fido di ciò che l'intuizione mi suggerisce."},
  {"id":39,"scala":"SN","latoA":"S","testoA":"Descrivo le cose in modo letterale e preciso.","testoB":"Descrivo le cose usando metafore e analogie."},
  {"id":40,"scala":"SN","latoA":"S","testoA":"Preferisco un approccio graduale e sistematico.","testoB":"Preferisco fare salti intuitivi e poi verificare."},
  {"id":41,"scala":"SN","latoA":"S","testoA":"Sono più convincente quando uso esempi concreti.","testoB":"Sono più convincente quando uso visioni e idee ispiranti."},
  {"id":42,"scala":"SN","latoA":"S","testoA":"Mi piace perfezionare ciò che esiste già.","testoB":"Mi piace inventare qualcosa di completamente nuovo."},
  {"id":43,"scala":"SN","latoA":"S","testoA":"Noto prima i dettagli specifici.","testoB":"Noto prima il quadro generale."},
  {"id":44,"scala":"SN","latoA":"S","testoA":"Preferisco che le istruzioni siano esplicite.","testoB":"Preferisco capire l'intenzione e poi agire autonomamente."},
  {"id":45,"scala":"SN","latoA":"S","testoA":"Mi piace applicare metodi consolidati.","testoB":"Mi piace sperimentare approcci originali."},
  {"id":46,"scala":"SN","latoA":"S","testoA":"Sono attratto dalla concretezza e dalla solidità.","testoB":"Sono attratto dall'originalità e dalla complessità."},
  {"id":47,"scala":"SN","latoA":"S","testoA":"Preferisco obiettivi chiari e misurabili.","testoB":"Preferisco obiettivi ispiranti anche se vaghi."},
  {"id":48,"scala":"SN","latoA":"S","testoA":"Tendo a essere preciso nelle parole che uso.","testoB":"Tendo a essere evocativo nelle parole che uso."},
  {"id":49,"scala":"IE","latoA":"I","testoA":"Preferisco ambienti tranquilli dove posso concentrarmi.","testoB":"Preferisco ambienti vivaci dove c'è interazione continua."},
  {"id":50,"scala":"IE","latoA":"I","testoA":"Dopo una lunga giornata sociale, ho bisogno di tempo da solo.","testoB":"Dopo una lunga giornata da solo, ho bisogno di stare con le persone."},
  {"id":51,"scala":"IE","latoA":"I","testoA":"Penso meglio quando sono solo e in silenzio.","testoB":"Penso meglio quando ne parlo con qualcuno."},
  {"id":52,"scala":"IE","latoA":"I","testoA":"Preferisco avere poche relazioni profonde.","testoB":"Preferisco avere molte relazioni variegate."},
  {"id":53,"scala":"IE","latoA":"I","testoA":"Nelle riunioni, preferisco ascoltare prima di parlare.","testoB":"Nelle riunioni, mi viene naturale prendere la parola."},
  {"id":54,"scala":"IE","latoA":"I","testoA":"Mi piace lavorare in modo indipendente.","testoB":"Mi piace lavorare in team."},
  {"id":55,"scala":"IE","latoA":"I","testoA":"Preferisco comunicare per iscritto piuttosto che di persona.","testoB":"Preferisco comunicare di persona piuttosto che per iscritto."},
  {"id":56,"scala":"IE","latoA":"I","testoA":"Mi sento a disagio se devo parlare senza aver riflettuto.","testoB":"Mi viene naturale parlare mentre sto ancora elaborando."},
  {"id":57,"scala":"IE","latoA":"I","testoA":"Preferisco approfondire pochi argomenti.","testoB":"Preferisco esplorare molti argomenti diversi."},
  {"id":58,"scala":"IE","latoA":"I","testoA":"Le interruzioni frequenti mi disturbano molto.","testoB":"Le interruzioni frequenti non mi disturbano particolarmente."},
  {"id":59,"scala":"IE","latoA":"I","testoA":"Mi ricarico stando solo con i miei pensieri.","testoB":"Mi ricarico stando con le persone e l'energia del gruppo."},
  {"id":60,"scala":"IE","latoA":"I","testoA":"Quando lavoro da solo sto bene, ma rischio di isolarmi troppo.","testoB":"Quando lavoro con gli altri mi carico, ma rischio di perdermi in troppe cose."},
  {"id":61,"scala":"OT","latoA":"B","testoA":"Quando entro a far parte di un nuovo gruppo, cerco subito punti in comune con gli altri.","testoB":"Quando entro a far parte di un nuovo gruppo, osservo prima di decidere se appartenervi davvero."},
  {"id":62,"scala":"OT","latoA":"B","testoA":"Mi sento più me stesso quando faccio parte di qualcosa di più grande di me.","testoB":"Mi sento più me stesso quando agisco in modo indipendente dal gruppo."},
  {"id":63,"scala":"OT","latoA":"B","testoA":"Le tradizioni e i rituali collettivi mi danno un senso di sicurezza e continuità.","testoB":"Le tradizioni e i rituali collettivi mi sembrano spesso sovrastrutture che non mi appartengono."},
  {"id":64,"scala":"OT","latoA":"B","testoA":"Quando un gruppo prende una decisione condivisa, mi adeguo volentieri anche se ho un'opinione diversa.","testoB":"Quando un gruppo prende una decisione condivisa, faccio fatica ad accettarla se non la sento mia."},
  {"id":65,"scala":"OT","latoA":"B","testoA":"Ho un forte senso di lealtà verso le comunità a cui appartengo (famiglia, lavoro, associazioni).","testoB":"La mia lealtà è verso singole persone, non verso gruppi o istituzioni."},
  {"id":66,"scala":"OT","latoA":"B","testoA":"Mi riconosco nell'identità del gruppo di cui faccio parte e ne sono orgoglioso.","testoB":"Mi riconosco come individuo prima ancora che come membro di qualsiasi gruppo."},
  {"id":67,"scala":"OT","latoA":"B","testoA":"In una situazione sociale nuova, cerco naturalmente di integrarmi e di essere accettato.","testoB":"In una situazione sociale nuova, mi basta essere rispettato — non ho bisogno di essere pienamente accettato."},
  {"id":68,"scala":"OT","latoA":"B","testoA":"Condividere valori, abitudini o simboli con altri mi fa sentire connesso e motivato.","testoB":"Posso collaborare bene con gli altri anche senza condividerne i valori o le abitudini."},
  {"id":69,"scala":"OT","latoA":"B","testoA":"Quando il gruppo a cui appartengo viene criticato, lo sento come una critica anche a me.","testoB":"Quando il gruppo a cui appartengo viene criticato, lo valuto in modo distaccato come se fossi esterno."},
  {"id":70,"scala":"OT","latoA":"B","testoA":"Ho bisogno di sentirmi parte di una comunità per stare bene.","testoB":"Sto bene anche senza appartenere a nessuna comunità in particolare."},
  {"id":71,"scala":"OT","latoA":"B","testoA":"Le opinioni degli altri su di me, specialmente di chi stimo, influenzano le mie scelte.","testoB":"Le opinioni degli altri su di me mi interessano poco rispetto a ciò che penso di me stesso."},
  {"id":72,"scala":"OT","latoA":"B","testoA":"Quando devo prendere una decisione importante, mi confronto naturalmente con gli altri prima di scegliere.","testoB":"Quando devo prendere una decisione importante, arrivo alla scelta da solo e poi eventualmente la comunico."}
]

INFERIOR = {"T":"F","F":"T","S":"N","N":"S"}
FUNCTION_NAMES = {"E":"Estroverso","I":"Introverso","T":"Pensiero","F":"Sentimento","S":"Sensazione","N":"Intuizione"}

def calculate_type(responses: dict) -> dict:
    scores = {"T":0,"F":0,"S":0,"N":0,"E":0,"I":0,"B":0,"NB":0}
    for q in QUESTIONS:
        qid = str(q["id"])
        if qid not in responses:
            continue
        choice = responses[qid]
        scala = q["scala"]
        if scala == "TF":
            scores["T" if choice == "A" else "F"] += 1
        elif scala == "SN":
            scores["S" if choice == "A" else "N"] += 1
        elif scala == "IE":
            scores["I" if choice == "A" else "E"] += 1
        elif scala == "OT":
            scores["B" if choice == "A" else "NB"] += 1

    norm_T = round((scores["T"] / 24) * 100, 1)
    norm_F = round((scores["F"] / 24) * 100, 1)
    norm_S = round((scores["S"] / 24) * 100, 1)
    norm_N = round((scores["N"] / 24) * 100, 1)
    norm_E = round((scores["E"] / 12) * 100, 1)
    norm_I = round((scores["I"] / 12) * 100, 1)

    orientation = "E" if norm_E >= norm_I else "I"
    funcs = sorted([("T",norm_T),("F",norm_F),("S",norm_S),("N",norm_N)], key=lambda x: -x[1])
    dominant = funcs[0][0]
    rational = {"T","F"}
    irrational = {"S","N"}
    dominant_category = rational if dominant in rational else irrational
    opposite_category = irrational if dominant_category == rational else rational
    auxiliary = next((f[0] for f in funcs[1:] if f[0] in opposite_category), funcs[1][0])
    tertiary = next((f[0] for f in funcs[1:] if f[0] != auxiliary and f[0] in dominant_category), funcs[2][0])
    inferior = INFERIOR[dominant]
    otroversion = "Belonging" if scores["B"] >= scores["NB"] else "Not Belonging"
    type_code = f"{orientation}-{dominant}{auxiliary}"
    sigla = f"{orientation}-{dominant}-{auxiliary}-{inferior}"
    nome_esteso = (
        f"{FUNCTION_NAMES[orientation]} (Orientamento), "
        f"{FUNCTION_NAMES[dominant]} (Funzione Primaria), "
        f"{FUNCTION_NAMES[auxiliary]} (Funzione Ausiliaria), "
        f"{FUNCTION_NAMES[inferior]} (Funzione Inferiore)"
    )
    nome_titolo = f"{sigla} | {nome_esteso} | {otroversion}"

    return {
        "type_code": type_code,
        "sigla": sigla,
        "nome_esteso": nome_esteso,
        "nome_titolo": nome_titolo,
        "orientation": orientation,
        "dominant": dominant,
        "auxiliary": auxiliary,
        "tertiary": tertiary,
        "inferior": inferior,
        "otroversion": otroversion,
        "scores": {
            "T": norm_T, "F": norm_F,
            "S": norm_S, "N": norm_N,
            "E": norm_E, "I": norm_I,
            "B": scores["B"], "NB": scores["NB"]
        }
    }

TYPE_PROFILES = {
    "E-TN": "Profilo estroverso con Pensiero come funzione guida e Intuizione a supporto. Strategico e visionario, unisce logica e capacità di proiettarsi nel futuro.",
    "E-TS": "Profilo estroverso con Pensiero come funzione guida e Sensazione a supporto. Pratico, concreto e orientato ai fatti, ama costruire processi affidabili.",
    "E-FN": "Profilo estroverso con Sentimento come funzione guida e Intuizione a supporto. Empatico, creativo e motivatore, ispira gli altri con visione e calore umano.",
    "E-FS": "Profilo estroverso con Sentimento come funzione guida e Sensazione a supporto. Caloroso, pratico e accogliente, crea armonia concreta attorno a sé.",
    "E-ST": "Profilo estroverso con Sensazione come funzione guida e Pensiero a supporto. Dinamico e orientato all'azione, coglie opportunità concrete e decide rapidamente.",
    "E-SF": "Profilo estroverso con Sensazione come funzione guida e Sentimento a supporto. Vive il presente con intensità, condivide emozioni e cura concretamente il gruppo.",
    "E-NT": "Profilo estroverso con Intuizione come funzione guida e Pensiero a supporto. Visionario pragmatico, combina creatività e logica per generare idee e realizzarle.",
    "E-NF": "Profilo estroverso con Intuizione come funzione guida e Sentimento a supporto. Ispiratore naturale, vede il potenziale nelle persone e nelle situazioni.",
    "I-TN": "Profilo introverso con Pensiero come funzione guida e Intuizione a supporto. Analitico e visionario, coglie pattern nascosti e costruisce modelli teorici profondi.",
    "I-TS": "Profilo introverso con Pensiero come funzione guida e Sensazione a supporto. Meticoloso e tradizionalista, coniuga analisi logica e memoria sensoriale eccellente.",
    "I-FN": "Profilo introverso con Sentimento come funzione guida e Intuizione a supporto. Profondo e immaginativo, vive guidato da valori personali e intuizioni simboliche.",
    "I-FS": "Profilo introverso con Sentimento come funzione guida e Sensazione a supporto. Stabile, sensibile e radicato, custodisce valori e tradizioni con cura emotiva.",
    "I-ST": "Profilo introverso con Sensazione come funzione guida e Pensiero a supporto. Metodico, preciso e tradizionalista, conserva procedure collaudate con grande affidabilità.",
    "I-SF": "Profilo introverso con Sensazione come funzione guida e Sentimento a supporto. Custode di valori e tradizioni, unisce sensibilità emotiva e cura concreta del dettaglio.",
    "I-NT": "Profilo introverso con Intuizione come funzione guida e Pensiero a supporto. Analista visionario, ama le idee astratte e sistematizza visioni profonde con rigore logico.",
    "I-NF": "Profilo introverso con Intuizione come funzione guida e Sentimento a supporto. Profondo e spirituale, percepisce significati archetipici e guida gli altri con visione ed empatia.",
}

class ChatMessage(BaseModel):
    message: str
    conversation_history: list
    responses: dict
    current_question_index: int

class SubmitTest(BaseModel):
    responses: dict

@app.get("/")
def root():
    return {"status": "ok", "message": "Typology API v2", "api_key_set": bool(api_key)}

@app.get("/api/questions")
def get_questions():
    return {"questions": QUESTIONS, "total": len(QUESTIONS)}

@app.post("/api/chat")
def chat(data: ChatMessage):
    if not client:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY non configurata")

    q_index = data.current_question_index
    responses = data.responses

    if q_index < len(QUESTIONS):
        current_q = QUESTIONS[q_index]
        system_prompt = f"""Sei Sofia, una guida professionale che conduce un test psicologico basato sulla tipologia junghiana.

Il tuo unico compito è presentare la domanda in modo diretto e neutro.
NON commentare la risposta precedente dell'utente.
NON fare osservazioni, complimenti o considerazioni di alcun tipo.
NON usare frasi come "Ottima scelta", "Interessante", "Capisco", "Grazie".
Presenta esclusivamente la domanda successiva, nient'altro.

Domanda {current_q['id']} di 72:
Opzione A: {current_q['testoA']}
Opzione B: {current_q['testoB']}

Formato: scrivi solo "Domanda {current_q['id']}." poi su righe separate "A: [testo]" e "B: [testo]". Nessun altro testo."""

    else:
        result = calculate_type(responses)
        profile = TYPE_PROFILES.get(result["type_code"], "Profilo in elaborazione.")
        system_prompt = f"""Sei Sofia. Il test è completato.
Presenta il profilo in modo professionale e diretto.

Profilo:
- Sigla: {result['sigla']}
- Nome: {result['nome_esteso']}
- Descrizione: {profile}
- Otroversione: {result['otroversion']}

Scrivi 3-4 frasi descrittive, chiare e autorevoli.
Inizia con: "Il tuo profilo è {result['sigla']}."
Niente frasi motivazionali. Sii preciso e concreto."""

    clean_history = [
        m for m in data.conversation_history
        if isinstance(m, dict)
        and m.get("role") in ("user", "assistant")
        and m.get("content")
        and str(m.get("content")).strip()
    ]
    messages = clean_history + [{"role": "user", "content": data.message}]

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=400,
            system=system_prompt,
            messages=messages
        )
        return {
            "response": response.content[0].text,
            "question_index": q_index,
            "total_questions": len(QUESTIONS),
            "completed": q_index >= len(QUESTIONS)
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

def _generate_sections_bg(job_id: str, result: dict):
    """Genera le sezioni in background e salva nel job store."""
    try:
        sections = build_profile_sections(
            type_code=result["type_code"],
            orientation=result["orientation"],
            dominant=result["dominant"],
            auxiliary=result["auxiliary"],
            inferior=result["inferior"],
            otroversion=result["otroversion"]
        )
        JOBS[job_id] = {"status": "done", "sections": sections}
    except Exception as e:
        JOBS[job_id] = {"status": "error", "sections": {}, "error": str(e)}

@app.post("/api/submit")
def submit_test(data: SubmitTest):
    if not client:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY non configurata")
    if len(data.responses) < 72:
        raise HTTPException(status_code=400, detail=f"Risposte incomplete: {len(data.responses)}/72")
    try:
        result = calculate_type(data.responses)
        profile = TYPE_PROFILES.get(result["type_code"], "")

        # Avvia generazione sezioni in background
        job_id = str(uuid.uuid4())
        JOBS[job_id] = {"status": "pending", "sections": {}}
        Thread(target=_generate_sections_bg, args=(job_id, result), daemon=True).start()

        # Risponde subito con i dati base + job_id
        return {
            **result,
            "profile_description": profile,
            "sections": {},
            "job_id": job_id
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sections/{job_id}")
def get_sections(job_id: str):
    """Polling endpoint: restituisce le sezioni quando sono pronte."""
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job non trovato")
    return job

@app.get("/api/profile/{type_code}")
def get_profile(type_code: str, otroversion: str = "Not Belonging"):
    """Endpoint diretto per ottenere il profilo completo dal RAG dato un type_code."""
    parts = type_code.upper().split("-")
    if len(parts) < 3:
        raise HTTPException(status_code=400, detail="type_code non valido. Formato atteso: E-TN o E-T-N-F")
    orientation = parts[0]
    dominant    = parts[1][0] if len(parts) == 2 else parts[1]
    auxiliary   = parts[1][1] if len(parts) == 2 else parts[2]
    inferior    = INFERIOR.get(dominant, "?")
    sections = build_profile_sections(
        type_code=type_code,
        orientation=orientation,
        dominant=dominant,
        auxiliary=auxiliary,
        inferior=inferior,
        otroversion=otroversion
    )
    return {"type_code": type_code, "sections": sections}
