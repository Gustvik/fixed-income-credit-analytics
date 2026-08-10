"""Learning page — the finance behind every metric in the toolkit (Norwegian).

Each concept: intuition → formula → **worked calculation with real numbers** →
CFA Level II link → an interview-ready one-liner. A single running bond
(3-year, 4% coupon, price 98, semi-annual) threads through YTM → duration →
convexity → DV01; model figures are used for spread/DTS/OAS. All numbers are
verified against the library in tests and the sample data.
"""

from __future__ import annotations

import streamlit as st

st.set_page_config(page_title="Læring & metodikk", page_icon="📖", layout="wide")

st.title("📖 Læring & metodikk")
st.caption(
    "Detaljene bak hver metrikk — intuisjon, formel, et regneeksempel du kan følge steg for "
    "steg, CFA-kobling og en setning du kan si i et intervju. Gjennomgående eksempel: en "
    "3-årig obligasjon med 4 % kupong til pris 98 (halvårlige kuponger)."
)


def concept(title, intuition, formulas, steps, example, cfa, interview):
    with st.expander(title):
        st.markdown(f"**Intuisjon.** {intuition}")
        if formulas:
            st.markdown("**Formel.**")
            for f in formulas:
                st.latex(f)
        if steps:
            st.markdown("**📝 Regneeksempel.**")
            for s in steps:
                st.latex(s)
        if example:
            st.markdown(f"**Kobling til appen.** {example}")
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
        "En nullkupongrente (spot) er renten for én enkelt utbetaling. Vanlige obligasjoner "
        "betaler kuponger underveis, så spot-rentene løses ut sekvensielt: kjenner du de korte, "
        "kan du isolere den neste fra en obligasjon med lengre løpetid.",
        [r"DF(t_n) = \frac{P - c\sum_{i<n} DF(t_i)}{c + 100}"],
        [r"\text{1-årig nullkupong, pris 96:}\quad DF(1) = \tfrac{96}{100} = 0.960",
         r"\text{2-årig, kupong 5, pris 101:}\quad DF(2) = \frac{101 - 5\cdot 0.960}{5 + 100} = \frac{96.2}{105} = 0.9162",
         r"z_2 = -\frac{\ln(0.9162)}{2} = 4.38\%"],
        "På Yield Curve-siden bootstrappes kurven slik at den **repriser hver input-obligasjon "
        "eksakt** (feil ~1e-11) — beviset på riktig kalibrering.",
        "*Term Structure of Interest Rates* — spot- vs. par- vs. forwardkurver.",
        "«Jeg bygger den risikofrie kurven ved bootstrapping og validerer at den repriser "
        "instrumentene den ble bygget fra.»",
    )
    concept(
        "Diskonteringsfaktor & kontinuerlig rente",
        "DF(t) er dagens verdi av 1 krone på tid t. Modellen bruker kontinuerlig rente internt "
        "(ren addisjon i eksponenten) og konverterer til årlig/halvårlig ved visning.",
        [r"DF(t) = e^{-z\,t}", r"r_m = m\left(e^{z/m}-1\right)"],
        [r"z = 4\%,\ t = 3:\quad DF = e^{-0.04\cdot 3} = e^{-0.12} = 0.8869",
         r"\text{Årlig ekvivalent:}\quad r_1 = e^{0.04}-1 = 4.08\%"],
        "Alle priser i verktøyet er summer av kontantstrøm × DF(t).",
        "*Fixed Income* — rente ↔ diskonteringsfaktor og rentekonvensjoner.",
        "«Kontinuerlig rente internt, konvertert til markedskonvensjon ved visning — da er "
        "diskonteringen konsistent uansett instrument.»",
    )
    concept(
        "Forwardrente",
        "Forwardrenten er renten markedet i dag priser inn for en fremtidig periode, utledet av "
        "spot-rentene på hver ende av perioden.",
        [r"f(t_1,t_2) = \frac{z_2 t_2 - z_1 t_1}{t_2 - t_1}"],
        [r"z_1 = 3.0\%\,(1\text{ år}),\ z_2 = 3.5\%\,(2\text{ år}):",
         r"f(1,2) = \frac{0.035\cdot 2 - 0.030\cdot 1}{2 - 1} = \frac{0.040}{1} = 4.00\%"],
        "Yield Curve-siden viser spot-, par- og forwardkurven samtidig, så du ser om markedet "
        "priser inn stigende eller fallende renter.",
        "*Term Structure* — forwardrater som markedets forventning + terminpremie.",
        "«Forwardkurven er markedets pris på fremtidige renter — den forteller om markedet "
        "venter kutt eller hevinger.»",
    )
    concept(
        "Realrente & nøytral realrente (r\\*)",
        "Realrenten er nominell rente minus inflasjon. Men om pengepolitikken faktisk strammer "
        "eller stimulerer, avgjøres ikke av fortegnet — det avgjøres av realrenten *relativt til "
        "den nøytrale realrenten* r\\*, nivået som verken gir gass eller bremser. En moderat "
        "positiv realrente er normalt og sunt; det er en realrente godt over r\\* som strammer til.",
        [r"r \approx i - \pi \quad(\text{Fisher, approksimasjon})",
         r"r < r^{*}\ \Rightarrow\ \text{ekspansiv},\qquad r > r^{*}\ \Rightarrow\ \text{kontraktiv}"],
        [r"\text{Styringsrente } i = 4.0\%,\ \text{inflasjon } \pi = 3.2\%",
         r"r = 4.0\% - 3.2\% = 0.8\%",
         r"\text{Anta } r^{*}\approx 0.5\%:\quad 0.8\% > 0.5\%\ \Rightarrow\ \text{svakt kontraktiv}"],
        "Makro-siden viser nominell styringsrente vs. realrente over tid — sweet spot er en "
        "moderat positiv realrente nær r\\*.",
        "*Economics* — nøytral rente, pengepolitisk innstilling og (beslektet) Taylor-regelen.",
        "«Restriktiv pengepolitikk handler om realrenten relativt til r\\*, ikke om den er "
        "positiv — det er nyansen mange bommer på.»",
    )

# ── 2 · Yield & spread ──────────────────────────────────────────────────────
with tab2:
    st.markdown("### Yield delt i risikofri rente + kredittpremie")
    concept(
        "Yield to maturity (YTM)",
        "YTM er den ene konstante renten som gjør nåverdien av alle kontantstrømmer lik prisen — "
        "obligasjonens interne avkastning hvis du holder til forfall og reinvesterer kupongene "
        "til samme rente.",
        [r"P = \sum_{i=1}^{n} \frac{CF_i}{(1+y/f)^{i}}"],
        [r"\text{3-årig, 4\% kupong, pris 98, halvårlig } (f=2):",
         r"98 = \frac{2}{(1+y/2)}+\frac{2}{(1+y/2)^2}+\dots+\frac{102}{(1+y/2)^6}",
         r"\Rightarrow\ y = 4.72\%\quad(\text{perioderente } y/2 = 2.36\%)"],
        "Løses med biseksjon. En obligasjon priset til 100 får YTM ≈ kupong — en sanity-sjekk "
        "i testene.",
        "*Fixed Income* — YTM og reinvesteringsforutsetningen.",
        "«YTM forutsetter reinvestering til samme rente — derfor er den et utgangspunkt, ikke "
        "en garantert avkastning.»",
    )
    concept(
        "Z-spread (kredittpremien)",
        "Z-spreaden er det konstante påslaget på hele den risikofrie kurven som gjør at de "
        "diskonterte kontantstrømmene treffer markedsprisen. Den reneste spread-målingen fordi "
        "den bruker hele kurven.",
        [r"P = \sum_i CF_i\, e^{-(z(t_i) + s)\,t_i}"],
        [r"\text{Equinor 5y, pris } 99.80,\ \text{løs for } s:",
         r"99.80 = \sum_i CF_i\, e^{-(z(t_i)+s)\,t_i}\ \Rightarrow\ s = 0.00686",
         r"s = 0.00686 \times 10^4 = 68.6\ \text{bp}"],
        "Spread-dekomponeringen viser yield = risikofri rente + Z-spread, per obligasjon "
        "(Equinor: 3,74 % + 0,69 % ≈ 4,45 %).",
        "*Credit Analysis* — Z-spread vs. nominell spread; hvorfor kurven betyr noe.",
        "«Z-spread er kredittpremien målt mot hele kurven — slik skiller jeg renterisiko fra "
        "kredittrisiko i avkastningen.»",
    )
    concept(
        "G-spread",
        "G-spread er en enklere måling: obligasjonens YTM minus statsrenten ved samme løpetid. "
        "Rask, men mindre presis fordi den bruker ett kurvepunkt.",
        [r"\text{G-spread} = y_{\text{bond}} - y_{\text{stat}}(T)"],
        [r"\text{Equinor: } y_{\text{bond}} = 4.45\%,\ y_{\text{stat}}(5) = 3.74\%",
         r"\text{G-spread} = 4.45\% - 3.74\% = 0.71\% = 71\ \text{bp}"],
        "Verktøyet viser G-spread ved siden av Z-spread — de ligger tett når kurven er flat "
        "(her 71 vs. 69 bp).",
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
        [r"\text{Vår 3-årige: } D_{mac} = 2.855,\ y = 4.72\%,\ f = 2",
         r"D_{mod} = \frac{2.855}{1 + 0.0472/2} = \frac{2.855}{1.0236} = 2.789",
         r"\text{+100 bp renter}\ \Rightarrow\ \tfrac{\Delta P}{P} \approx -2.789 \times 0.01 = -2.79\%"],
        "Porteføljens durasjon (~3,34 år i eksempelet) er den markedsverdivektede summen av "
        "obligasjonenes.",
        "*Interest Rate Risk* — durasjon som førsteordens følsomhet.",
        "«Modifisert durasjon er mitt førsteordens mål på renterisiko — porteføljens er bare "
        "det vektede snittet.»",
    )
    concept(
        "Konveksitet",
        "Durasjon er en rett linje; den ekte pris/rente-sammenhengen er en kurve. Konveksitet er "
        "andreordens-korreksjonen. Positiv konveksitet er bra for eieren.",
        [r"\frac{\Delta P}{P} \approx -D_{mod}\,\Delta y + \tfrac{1}{2}\,C\,(\Delta y)^2"],
        [r"\text{Vår 3-årige: } C = 9.378,\ \Delta y = +1\%",
         r"\tfrac{1}{2}\,C\,(\Delta y)^2 = 0.5 \times 9.378 \times (0.01)^2 = +0.047\%",
         r"\text{Total} \approx -2.79\% + 0.05\% = -2.74\%\ (\text{konveksiteten demper tapet})"],
        "I scenariofanen ser du gapet mellom eksakt reprising og durasjons­approksimasjonen — "
        "det gapet *er* konveksiteten.",
        "*Interest Rate Risk* — konveksitet og hvorfor approksimasjonen svikter ved store skift.",
        "«Konveksitet er andreordensleddet — den forklarer hvorfor durasjon alene undervurderer "
        "gevinsten ved store rentefall.»",
    )
    concept(
        "DV01 (pengefølsomhet)",
        "DV01 er kroneendringen i verdi per 1 basispunkt. Der durasjon er i prosent, er DV01 i "
        "kroner — praktisk for å dimensjonere sikring.",
        [r"DV01 = D_{mod}\times P \times 10^{-4}"],
        [r"\text{Vår 3-årige: } D_{mod} = 2.789,\ P = 98",
         r"DV01 = 2.789 \times 98 \times 10^{-4} = 0.0273\ \text{(kr per 100 pålydende per bp)}"],
        "Vises per obligasjon i analysetabellen. Summér over porteføljen for kroner per bp.",
        "*Interest Rate Risk* — money duration / PVBP.",
        "«DV01 oversetter durasjon til kroner per basispunkt — språket sikring foregår i.»",
    )
    concept(
        "Key-rate (partiell) durasjon",
        "Én durasjon antar parallelt kurveskift. Key-rate durasjoner måler følsomheten til hvert "
        "løpetidspunkt hver for seg — så du ser om risikoen ligger i 2-års- eller 10-årspunktet.",
        [r"KRD_k = -\frac{1}{P}\frac{\partial P}{\partial z_k}",
         r"\sum_k KRD_k \approx D_{\text{eff}}"],
        [r"\text{Equinor 5y, KRD per punkt:}",
         r"KRD_{0.5}{=}0.01,\ KRD_{1}{=}0.04,\ KRD_{2}{=}0.08,\ KRD_{3}{=}0.19,\ KRD_{5}{=}4.23",
         r"\textstyle\sum_k KRD_k = 4.54 \approx D_{mod}\ (\text{konsentrert i 5-årspunktet})"],
        "Curve Risk-fanen viser porteføljens KRD per punkt — avslører bullet vs. barbell og "
        "steepener/flattener.",
        "*Interest Rate Risk* — key rate durations og ikke-parallelle kurveskift.",
        "«Én durasjon skjuler kurverisiko. Key-rate durasjoner viser hvor på kurven risikoen "
        "sitter — avgjørende for steepener/flattener-syn.»",
    )

# ── 4 · Kreditt & portefølje ────────────────────────────────────────────────
with tab4:
    st.markdown("### Kredittrisiko og aktiv forvaltning mot indeks")
    concept(
        "Spread-durasjon",
        "Som modifisert durasjon, men følsomheten er mot spread-bevegelser, ikke rente. Betyr "
        "mest når rente og spread beveger seg ulikt (typisk i risk-off).",
        [r"\frac{\Delta P}{P} \approx -D_{spread}\,\Delta s"],
        [r"\text{Equinor: } D_{spread} = 4.54",
         r"\text{spread ut } +50\text{ bp}\ \Rightarrow\ \tfrac{\Delta P}{P} \approx -4.54 \times 0.005 = -2.27\%"],
        "Brukes i scenariofanen for å skille spread-bidraget fra rentebidraget til tapet.",
        "*Credit Analysis* — spread duration som kredittrisiko-følsomhet.",
        "«Spread-durasjon isolerer kredittrisikoen — den lar meg stress-teste spread og rente "
        "hver for seg.»",
    )
    concept(
        "DTS — Duration Times Spread",
        "DTS = spread-durasjon × spread. En obligasjon med dobbelt så høy spread er omtrent "
        "dobbelt så volatil i spread-termer. Det beste ex-ante-målet på kredittrisiko, og "
        "grunnlaget for risikobudsjettering.",
        [r"DTS = D_{spread}\times s"],
        [r"\text{Equinor: } D_{spread} = 4.54,\ s = 0.686\%",
         r"DTS = 4.54 \times 0.686 = 3.11"],
        "Portfolio & Risk-fanen fordeler porteføljens DTS på hver posisjon — så du ser hvem som "
        "faktisk bruker risikobudsjettet (ofte få BBB-navn, ikke de med størst vekt).",
        "*Credit Analysis / Portfolio Management* — DTS (Ben Dor et al.).",
        "«Jeg budsjetterer kredittrisiko i DTS, ikke i vekt — risikoen sitter i spread × "
        "spread-durasjon, ikke i hvor mye jeg eier.»",
    )
    concept(
        "Aktiv risiko vs. benchmark",
        "Aktiv forvaltning handler om avvik fra indeks. Aktiv durasjon/DTS = porteføljens minus "
        "benchmarkens — hvilke veddemål du faktisk tar.",
        [r"\text{Aktiv}_x = x_{\text{portefølje}} - x_{\text{benchmark}}"],
        [r"\text{Aktiv durasjon} = 3.34 - 3.47 = -0.13\ \text{år}",
         r"(\text{porteføljen har litt lavere renterisiko enn indeks})"],
        "Portfolio & Risk-fanen viser aktiv durasjon/DTS/yield og aktive sektorvekter mot valgt "
        "benchmark.",
        "*Portfolio Management* — benchmark-relativ posisjonering.",
        "«Hvert avvik fra indeks er et bevisst veddemål jeg må kunne begrunne.»",
    )
    concept(
        "Tracking error (kovariansbasert)",
        "Forventet standardavvik i meravkastningen mot indeks. Bygges fra en kovariansmatrise "
        "(rentefaktor + spreadfaktor) på de aktive vektene. Bidragene summerer til TE.",
        [r"TE = \sqrt{w_a^{\top}\,\Sigma\,w_a}",
         r"TE \approx \sqrt{D_a^2\sigma_r^2 + SD_a^2\sigma_s^2 + 2\rho\,D_a SD_a\,\sigma_r\sigma_s}"],
        [r"D_a{=}{-}0.13,\ SD_a{=}{-}0.20,\ \sigma_r{=}1.0\%,\ \sigma_s{=}0.8\%,\ \rho{=}{-}0.2",
         r"TE = \sqrt{(0.13)^2(0.01)^2 + (0.20)^2(0.008)^2 + 2(-0.2)(-0.13)(-0.20)(0.01)(0.008)}",
         r"TE = \sqrt{1.69{+}2.56{-}0.83}\times 10^{-6} = 0.18\%\ \text{per år}"],
        "Tracking Error-fanen lar deg justere volatilitetsantakelsene og se risikobidragene "
        "(fullversjonen bruker hele kovariansmatrisen, ~0,2 %/år i eksempelet).",
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
        "en opsjon du som eier har skrevet, så du får betalt via høyere spread. Opsjonskostnaden "
        "er den delen av spreaden som bare kompenserer for opsjonen.",
        [r"\text{Opsjonskostnad} = \text{statisk spread} - OAS"],
        [r"\text{5y 5\%, callable fra år 3, pris 101, } \sigma = 15\%:",
         r"\text{Statisk spread} = 98.9\ \text{bp},\quad OAS = 70.0\ \text{bp}",
         r"\text{Opsjonskostnad} = 98.9 - 70.0 = 28.9\ \text{bp}"],
        "OAS-fanen viser nettopp dette — og at opsjonskostnaden vokser med volatiliteten.",
        "*Valuation of Bonds with Embedded Options* — callable/putable og effekten på spread.",
        "«Den rå spreaden på en callable lyver — jeg ser på OAS, det jeg faktisk sitter igjen "
        "med etter å ha betalt for opsjonen jeg har skrevet.»",
    )
    concept(
        "OAS via binomisk rentetre",
        "OAS finnes ved å bygge et binomisk rentetre kalibrert til den risikofrie kurven, la "
        "renten sprike med en volatilitetsantakelse, verdsette obligasjonen med utsteders "
        "call-regel bakover gjennom treet, og løse ut påslaget (OAS) som treffer markedsprisen.",
        [r"V_{node} = \min\!\Big(\text{call},\ \tfrac{0.5(V_u+V_d)}{1+r+OAS}\Big) + \text{kupong}"],
        [r"\sigma:\ 10\% \to 15\% \to 25\%\ (\text{alt annet likt}):",
         r"\text{Opsjonskostnad}:\ \approx 19 \to 29 \to 43\ \text{bp}",
         r"\text{Høyere } \sigma \Rightarrow \text{dyrere call} \Rightarrow \text{lavere } OAS"],
        "Grafen i OAS-fanen viser gapet mellom statisk spread og OAS vokse med volatiliteten.",
        "*Valuation of Bonds with Embedded Options* — binomiske trær, kalibrering, OAS.",
        "«OAS er opsjonsjustert fordi den kommer fra et volatilitets-kalibrert tre — derfor kan "
        "jeg sammenligne callable og ikke-callable på like vilkår.»",
    )

# ── 6 · Scenario & overvåking ───────────────────────────────────────────────
with tab6:
    st.markdown("### Stresstesting og tidlig varsling")
    concept(
        "Scenario: full reprising vs. approksimasjon",
        "To måter å måle et sjokk: (1) eksakt — skift kurven med Δr og spreaden med Δs og "
        "reprising alt på nytt; (2) approksimasjon — bruk durasjon, konveksitet og spread-durasjon. "
        "Eksakt er alltid riktig; approksimasjonen er rask men svikter ved store sjokk.",
        [r"\tfrac{\Delta V}{V} \approx -D_{mod}\Delta r + \tfrac12 C\,\Delta r^2 - D_{spread}\Delta s"],
        [r"\text{Portefølje: } D_{mod}{=}3.34,\ C{=}14.36,\ D_{spread}{=}3.42;\ \Delta r{=}{+}1\%,\ \Delta s{=}{+}0.5\%",
         r"= -3.34(0.01) + \tfrac12(14.36)(0.01)^2 - 3.42(0.005)",
         r"= -3.34\% + 0.07\% - 1.71\% = -4.98\%"],
        "Scenariofanen viser eksakt og approksimasjon side om side + et Δr×Δs-varmekart "
        "(her ~−5 %; gapet mot eksakt = konveksitet/kryssledd).",
        "*Interest Rate Risk / Fixed Income* — scenarioanalyse og grensene for durasjon.",
        "«Jeg reprisererer fullt ut i scenarioer — durasjon/konveksitet er en kontroll, ikke "
        "fasiten, når sjokkene blir store.»",
    )
    concept(
        "Early warning — spread-z-score",
        "Kredittforverring viser seg først i spread. Vi sammenligner dagens spread mot navnets "
        "egen nylige historikk med en z-score; brudd på terskler gir WATCH/ALERT.",
        [r"z = \frac{s_{\text{i dag}} - \bar{s}}{\sigma_s}"],
        [r"\text{Dagens spread } 160\text{ bp},\ \text{snitt } \bar{s}=120\text{ bp},\ \sigma_s=15\text{ bp}",
         r"z = \frac{160 - 120}{15} = 2.67\ \Rightarrow\ \textbf{ALERT}\ (z \geq 2.5)"],
        "Early Warning-fanen flagger navn hvis z overstiger tersklene du setter.",
        "*Credit Analysis* — spread som ledende indikator på kredittkvalitet.",
        "«Spread er den ledende indikatoren på kredittforverring — z-score fanger unormal utgang "
        "justert for navnets egen volatilitet.»",
    )

st.divider()
st.info(
    "Klarer du å forklare hver boks med egne ord — intuisjon, regneeksempel og et konkret tall "
    "fra appen — kan du forsvare hele modellen i et intervju.",
    icon="🎓",
)
