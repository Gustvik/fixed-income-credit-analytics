"""Learning page — the finance behind every metric in the toolkit (Norwegian).

Each concept is presented as: intuition → formula → worked example (with the
app's own numbers) → CFA Level II link → an interview-ready one-liner. The goal
is that the author can explain every number the dashboard produces.
"""

from __future__ import annotations

import streamlit as st

st.set_page_config(page_title="Læring & metodikk", page_icon="📖", layout="wide")

st.title("📖 Læring & metodikk")
st.caption(
    "Detaljene bak hver metrikk i verktøyet — intuisjon, formel, eksempel, CFA-kobling "
    "og en setning du kan si i et intervju. Målet: du skal kunne forklare hvert tall appen viser."
)


def concept(title, intuition, formulas, example, cfa, interview):
    with st.expander(title):
        st.markdown(f"**Intuisjon.** {intuition}")
        if formulas:
            st.markdown("**Formel.**")
            for f in formulas:
                st.latex(f)
        st.markdown(f"**Eksempel (fra appen).** {example}")
        st.markdown(f"**CFA Level II.** {cfa}")
        st.success(f"🗣️ *Intervju-svar:* {interview}")


# ─────────────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "1 · Rentekurven", "2 · Yield & spread", "3 · Rentefølsomhet",
    "4 · Kreditt & portefølje", "5 · Opsjoner (OAS)", "6 · Scenario & overvåking",
])

# ── 1 · Rentekurven ─────────────────────────────────────────────────────────
with tab1:
    st.markdown("### Å bygge det risikofrie fundamentet")
    concept(
        "Nullkupongkurve & bootstrapping",
        "En nullkupongrente (spot) er renten for én enkelt utbetaling på et gitt tidspunkt. "
        "Vanlige statsobligasjoner betaler kuponger underveis, så vi kan ikke lese spot-rentene "
        "rett av. *Bootstrapping* løser dem ut sekvensielt: kjenner du de korte spot-rentene, "
        "kan du isolere den neste fra en obligasjon med lengre løpetid.",
        [r"P = \sum_{i=1}^{n} c\,DF(t_i) + 100\,DF(t_n)",
         r"DF(t_n) = \frac{P - c\sum_{i<n} DF(t_i)}{c + 100}"],
        "På Yield Curve-siden bootstrappes kurven slik at den **repriser hver input-obligasjon "
        "eksakt** (feil ~1e-11). Det er beviset på at kurven er riktig kalibrert.",
        "Dekkes i *Term Structure of Interest Rates* — spot- vs. par- vs. forwardkurver.",
        "«Jeg bygger den risikofrie kurven ved bootstrapping, og validerer den ved at den "
        "repriser instrumentene den ble bygget fra.»",
    )
    concept(
        "Diskonteringsfaktor & kontinuerlig rente",
        "En diskonteringsfaktor DF(t) er dagens verdi av 1 krone på tid t. Modellen jobber "
        "internt med *kontinuerlig* rente fordi den gjør matematikken ren (addisjon i "
        "eksponenten), og konverterer til årlig/halvårlig ved visning.",
        [r"DF(t) = e^{-z\,t}", r"r_m = m\left(e^{z/m}-1\right)"],
        "Alle priser i verktøyet er summer av kontantstrøm × DF(t). Diskonteringsfaktoren er "
        "konvensjonsfri — den bryr seg ikke om hvilken rentekonvensjon du viser.",
        "*Fixed Income* — sammenhengen rente ↔ diskonteringsfaktor og ulike renteconvensjoner.",
        "«Kontinuerlig rente internt, konvertert til markedskonvensjon ved visning — da er "
        "diskonteringen konsistent uansett instrument.»",
    )
    concept(
        "Par- og forwardrenter",
        "Par-renten er kupongen som gjør at en obligasjon prises til pari (100). Forwardrenten "
        "er renten markedet i dag priser inn for en fremtidig periode. Begge utledes av samme "
        "diskonteringsfaktorer.",
        [r"\text{par}(T) = f\,\frac{1 - DF(T)}{\sum_i DF(t_i)}",
         r"f(t_1,t_2) = \frac{z_2 t_2 - z_1 t_1}{t_2 - t_1}"],
        "Yield Curve-siden viser par-, spot- og forwardkurven samtidig, så du ser om markedet "
        "priser inn stigende eller fallende renter (forward over/under spot).",
        "*Term Structure* — forwardrater som markedets forventning + terminpremie.",
        "«Forwardkurven er markedets pris på fremtidige renter — den forteller om markedet "
        "venter kutt eller hevinger.»",
    )

# ── 2 · Yield & spread ──────────────────────────────────────────────────────
with tab2:
    st.markdown("### Yield delt i risikofri rente + kredittpremie")
    concept(
        "Yield to maturity (YTM)",
        "YTM er den ene konstante renten som gjør nåverdien av alle kontantstrømmer lik prisen. "
        "Det er obligasjonens interne avkastning *hvis* du holder til forfall og reinvesterer "
        "kupongene til samme rente.",
        [r"P = \sum_{i=1}^{n} \frac{CF_i}{(1+y/f)^{i}}"],
        "Løses med et rotsøk (biseksjon). En obligasjon priset til 100 får YTM ≈ kupong — "
        "en nyttig sanity-sjekk du finner igjen i testene.",
        "*Fixed Income* — YTM og dens forutsetninger (reinvesteringsrisiko).",
        "«YTM forutsetter reinvestering til samme rente — derfor er den et utgangspunkt, ikke "
        "en garantert avkastning.»",
    )
    concept(
        "Z-spread (kredittpremien)",
        "Z-spreaden er det konstante påslaget du legger på *hele* den risikofrie kurven for at "
        "de diskonterte kontantstrømmene skal treffe markedsprisen. Den er den reneste "
        "spread-målingen fordi den bruker hele kurven, ikke ett enkelt punkt.",
        [r"P = \sum_i CF_i\, e^{-(z(t_i) + s)\,t_i}"],
        "For Equinor 5y i eksempeluniverset gir modellen ~69 bp. Spread-dekomponeringen viser "
        "yield = risikofri rente + Z-spread, per obligasjon.",
        "*Credit Analysis* — Z-spread vs. nominell spread; hvorfor kurven betyr noe.",
        "«Z-spread er kredittpremien målt mot hele kurven — det er slik jeg skiller renterisiko "
        "fra kredittrisiko i avkastningen.»",
    )
    concept(
        "G-spread & I-spread",
        "G-spread er en enklere måling: obligasjonens YTM minus statsrenten ved samme løpetid. "
        "Rask å regne, men mindre presis enn Z-spread fordi den bruker ett kurvepunkt.",
        [r"\text{G-spread} = y_{\text{bond}} - y_{\text{stat}}(T)"],
        "Verktøyet viser G-spread ved siden av Z-spread — de ligger tett når kurven er flat, og "
        "spriker mer når kurven er bratt.",
        "*Credit Analysis* — ulike spread-mål og når de brukes.",
        "«G-spread er kjapp og intuitiv; Z-spread er den jeg stoler på når kurven er bratt.»",
    )

# ── 3 · Rentefølsomhet ──────────────────────────────────────────────────────
with tab3:
    st.markdown("### Hvor mye taper/tjener porteføljen når renten beveger seg")
    concept(
        "Macaulay- & modifisert durasjon",
        "Macaulay-durasjon er kontantstrømmenes vektede gjennomsnittlige løpetid. Modifisert "
        "durasjon gjør den om til en følsomhet: omtrent hvor mange prosent prisen faller når "
        "renten stiger 1 prosentpoeng.",
        [r"D_{mod} = \frac{D_{mac}}{1 + y/f}",
         r"\frac{\Delta P}{P} \approx -D_{mod}\,\Delta y"],
        "Porteføljen i eksempelet har modifisert durasjon ~3,34 år → +100 bp renter ≈ −3,3 %. "
        "Porteføljens durasjon er den markedsverdivektede summen av obligasjonenes.",
        "*Interest Rate Risk* — durasjon som førsteordens følsomhet.",
        "«Modifisert durasjon er mitt førsteordens mål på renterisiko — porteføljens er bare "
        "det vektede snittet av posisjonenes.»",
    )
    concept(
        "Konveksitet",
        "Durasjon er en rett linje; den ekte pris/rente-sammenhengen er en kurve. Konveksitet er "
        "andreordens-korreksjonen. Positiv konveksitet er bra for eieren: du taper litt mindre "
        "når renten stiger, og tjener litt mer når den faller.",
        [r"\frac{\Delta P}{P} \approx -D_{mod}\,\Delta y + \tfrac{1}{2}\,C\,(\Delta y)^2"],
        "I scenariofanen ser du gapet mellom eksakt reprising og durasjons­approksimasjonen — "
        "det gapet *er* konveksiteten (og kryssleddet mot spread).",
        "*Interest Rate Risk* — konveksitet og hvorfor approksimasjonen svikter ved store skift.",
        "«Konveksitet er andreordensleddet — den forklarer hvorfor durasjon alene undervurderer "
        "gevinsten ved store rentefall.»",
    )
    concept(
        "DV01 (pengefølsomhet)",
        "DV01 er kroneendringen i verdi per 1 basispunkt renteendring. Der durasjon er i prosent, "
        "er DV01 i kroner — praktisk for å dimensjonere sikring (hvor mye må jeg hedge?).",
        [r"DV01 = D_{mod}\,\times P \times 10^{-4}"],
        "Vises per obligasjon i analysetabellen. Summér DV01 over porteføljen for å vite hvor "
        "mange kroner ett basispunkt er verdt.",
        "*Interest Rate Risk* — money duration / PVBP.",
        "«DV01 oversetter durasjon til kroner per basispunkt — det er språket sikring foregår i.»",
    )
    concept(
        "Key-rate (partiell) durasjon",
        "Én durasjon antar at hele kurven beveger seg parallelt. Key-rate durasjoner måler "
        "følsomheten til *hvert* løpetidspunkt hver for seg — så du ser om risikoen ligger i "
        "2-års- eller 10-årspunktet, og om du er eksponert for at kurven bratter/flater.",
        [r"KRD_k = -\frac{1}{P}\frac{\partial P}{\partial z_k}",
         r"\sum_k KRD_k \approx D_{\text{eff}}"],
        "Curve Risk-fanen viser porteføljens KRD per punkt. Summen ≈ effektiv durasjon — men "
        "fordelingen avslører bullet vs. barbell og steepener/flattener-posisjoner.",
        "*Interest Rate Risk* — key rate durations og ikke-parallelle kurveskift.",
        "«Én durasjon skjuler kurverisiko. Key-rate durasjoner viser *hvor* på kurven risikoen "
        "sitter — avgjørende for steepener/flattener-syn.»",
    )

# ── 4 · Kreditt & portefølje ────────────────────────────────────────────────
with tab4:
    st.markdown("### Kredittrisiko og aktiv forvaltning mot indeks")
    concept(
        "Spread-durasjon",
        "Som modifisert durasjon, men følsomheten er mot *spread*-bevegelser, ikke rente. For en "
        "vanlig obligasjon ligger de tett; forskjellen betyr noe når rente og spread beveger seg "
        "ulikt (typisk i risk-off).",
        [r"\frac{\Delta P}{P} \approx -D_{spread}\,\Delta s"],
        "Brukes i scenariofanen: spread-utgang på 50 bp × spread-durasjon gir spread-bidraget til "
        "tapet, adskilt fra rentebidraget.",
        "*Credit Analysis* — spread duration som kredittrisiko-følsomhet.",
        "«Spread-durasjon isolerer kredittrisikoen — den lar meg stress-teste spread og rente "
        "hver for seg.»",
    )
    concept(
        "DTS — Duration Times Spread",
        "DTS = spread-durasjon × spread. Innsikten: en obligasjon med dobbelt så høy spread er "
        "omtrent dobbelt så volatil i spread-termer. DTS er derfor det beste *ex-ante*-målet på "
        "en posisjons kredittrisiko, og grunnlaget for risikobudsjettering.",
        [r"DTS = D_{spread}\times s"],
        "Portfolio & Risk-fanen fordeler porteføljens DTS på hver posisjon — så du ser hvem som "
        "faktisk bruker av risikobudsjettet (ofte få BBB-navn, ikke de med størst vekt).",
        "*Credit Analysis / Portfolio Management* — DTS som kredittrisiko-metrikk (Ben Dor et al.).",
        "«Jeg budsjetterer kredittrisiko i DTS, ikke i vekt — for risikoen sitter i spread × "
        "spread-durasjon, ikke i hvor mye jeg eier.»",
    )
    concept(
        "Aktiv risiko vs. benchmark",
        "Aktiv forvaltning handler om *avvik* fra indeks. Aktiv durasjon, aktiv spread-durasjon "
        "og aktiv DTS = porteføljens minus benchmarkens. De forteller hvilke veddemål du faktisk "
        "tar: mer rente­risiko? mer kredittrisiko? i hvilke sektorer?",
        [r"\text{Aktiv}_x = x_{\text{portefølje}} - x_{\text{benchmark}}"],
        "Portfolio & Risk-fanen viser aktiv durasjon/DTS/yield og aktive sektorvekter mot valgt "
        "benchmark (lik vekt eller markedsverdi).",
        "*Portfolio Management* — benchmark-relativ posisjonering.",
        "«Jeg tenker i aktive posisjoner: hvert avvik fra indeks er et bevisst veddemål jeg må "
        "kunne begrunne.»",
    )
    concept(
        "Tracking error (kovariansbasert)",
        "Tracking error er forventet standardavvik i *meravkastningen* mot indeks. Vi bygger en "
        "kovariansmatrise fra en faktormodell (rentefaktor + felles/sektor/idiosynkratisk "
        "spreadfaktor) og regner TE på de aktive vektene. Bidragene summerer til TE, så du ser "
        "hvem som driver den aktive risikoen.",
        [r"TE = \sqrt{w_a^{\top}\,\Sigma\,w_a}",
         r"\Sigma_{ij} = D_iD_j\sigma_r^2 + SD_i SD_j\,\text{cov}(s_i,s_j) + \dots"],
        "Tracking Error-fanen lar deg justere volatilitetsantakelsene og se hvordan TE og "
        "risikobidragene endrer seg. Med lik-vekt-benchmark ligger eksempelet ~0,2 %/år.",
        "*Portfolio Management* — aktiv risiko, informasjonsrate, risikodekomponering.",
        "«Tracking error er ex-ante aktiv risiko fra en kovariansmodell — og jeg kan peke på "
        "nøyaktig hvilke posisjoner som bidrar mest.»",
    )

# ── 5 · Opsjoner (OAS) ──────────────────────────────────────────────────────
with tab5:
    st.markdown("### Obligasjoner med innebygde opsjoner")
    concept(
        "Callable bonds & opsjonskostnad",
        "En callable obligasjon lar utsteder innfri tidlig — typisk når rentene faller. Det er "
        "en opsjon *du som eier har skrevet*, så du får betalt for den i form av høyere spread. "
        "Opsjonskostnaden er den delen av spreaden som bare kompenserer for opsjonen.",
        [r"\text{Opsjonskostnad} = \text{statisk spread} - OAS"],
        "OAS-fanen: en 5y 5%-obligasjon callable fra år 3 gir statisk spread 99 bp, OAS 70 bp → "
        "opsjonskostnad 29 bp ved 15 % rentevolatilitet.",
        "*Valuation of Bonds with Embedded Options* — callable/putable og effekten på spread.",
        "«Den rå spreaden på en callable lyver — jeg ser på OAS, som er det jeg faktisk sitter "
        "igjen med etter å ha betalt for opsjonen jeg har skrevet.»",
    )
    concept(
        "OAS via binomisk rentetre",
        "OAS finnes ved å bygge et binomisk rentetre kalibrert til den risikofrie kurven (så det "
        "repriser statskurven), la renten sprike opp/ned med en volatilitetsantakelse, verdsette "
        "obligasjonen med utsteders call-regel bakover gjennom treet, og løse ut det konstante "
        "påslaget (OAS) som treffer markedsprisen.",
        [r"V_{node} = \min\!\Big(\text{call},\ \tfrac{0.5(V_u+V_d)}{1+r+OAS}\Big) + \text{kupong}"],
        "Høyere volatilitet → mer verdifull call for utsteder → høyere opsjonskostnad → lavere "
        "OAS. Grafen i fanen viser nettopp dette: gapet mellom statisk spread og OAS vokser med "
        "volatiliteten.",
        "*Valuation of Bonds with Embedded Options* — binomiske trær, kalibrering, OAS.",
        "«OAS er opsjonsjustert fordi den kommer fra et volatilitets-kalibrert tre — derfor kan "
        "jeg sammenligne callable og ikke-callable på like vilkår.»",
    )

# ── 6 · Scenario & overvåking ───────────────────────────────────────────────
with tab6:
    st.markdown("### Stresstesting og tidlig varsling")
    concept(
        "Scenario: full reprising vs. approksimasjon",
        "To måter å måle et sjokk på: (1) *eksakt* — skift kurven med Δr og spreaden med Δs og "
        "reprising hver kontantstrøm på nytt; (2) *approksimasjon* — bruk durasjon og konveksitet. "
        "Eksakt er alltid riktig; approksimasjonen er rask men svikter ved store sjokk.",
        [r"\Delta V \approx \big(-D_{mod}\Delta r + \tfrac12 C\,\Delta r^2 - D_{spread}\Delta s\big)V"],
        "Scenariofanen viser begge side om side + et Δr×Δs-varmekart. Ved +100 bp / +50 bp ligger "
        "eksempelet ~−5 %, og eksakt vs. approksimasjon er nær hverandre (gapet = konveksitet).",
        "*Interest Rate Risk / Fixed Income* — scenarioanalyse og grensene for durasjon.",
        "«Jeg reprisererer fullt ut i scenarioer — durasjon/konveksitet er en kontroll, ikke "
        "fasiten, når sjokkene blir store.»",
    )
    concept(
        "Early warning — spread-z-score",
        "Kredittforverring viser seg først i spread. Vi sammenligner dagens spread mot navnets "
        "egen nylige historikk med en z-score; brudd på terskler gir WATCH/ALERT. Poenget er å "
        "fange *unormal* utgang tidlig, justert for hvor volatil hvert navn normalt er.",
        [r"z = \frac{s_{\text{i dag}} - \bar{s}}{\sigma_s}"],
        "Early Warning-fanen flagger navn hvis z overstiger tersklene du setter. (Historikken i "
        "demoen er syntetisk og reproduserbar — bytt inn en ekte daglig spread-serie i drift.)",
        "*Credit Analysis* — spread som ledende indikator på kredittkvalitet.",
        "«Spread er den ledende indikatoren på kredittforverring — z-score fanger unormal utgang "
        "justert for navnets egen volatilitet.»",
    )

st.divider()
st.info(
    "Denne siden er også intervjuforberedelse: klarer du å forklare hver boks med egne ord — "
    "intuisjon, formel og et konkret tall fra appen — kan du forsvare hele modellen i et møte.",
    icon="🎓",
)
