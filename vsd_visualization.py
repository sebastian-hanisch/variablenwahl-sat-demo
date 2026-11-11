"""Plotly-Figuren: Aktivitätsbalken je Schritt und Streifendiagramme der Messreihen (alle Achsen fest, `fixedrange`)."""

import math
from statistics import median

import plotly.graph_objects as go

import vsd_constants as C

SCHRIFT = dict(size=12)


def _fest(fig, hoehe: int):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    fig.update_layout(height=hoehe, margin=dict(l=50, r=20, t=40, b=50), showlegend=False, font=SCHRIFT)
    return fig


def sortierte_variablen(aktivitaet: dict) -> list[int]:
    """Absteigend nach Aktivität, bei Gleichstand die kleinere Nummer zuerst (wie die Wahl des Lösers)."""
    return sorted(aktivitaet, key=lambda v: (-aktivitaet[v], v))


def build_aktivitaet(aktivitaet: dict, belegt: set, hervorgehoben: tuple, titel: str):
    """Balken der Aktivität je Variable, absteigend sortiert: belegte Variablen grau, die vom Ereignis betroffenen farbig."""
    var = sortierte_variablen(aktivitaet)
    farben = [C.COLOR_WAHL if (v in hervorgehoben and v not in belegt) else C.COLOR_BETEILIGT if v in hervorgehoben
              else C.COLOR_BELEGT if v in belegt else C.COLOR_AKTIV for v in var]
    fig = go.Figure(go.Bar(x=[f"x{v}" for v in var], y=[aktivitaet[v] for v in var], marker_color=farben,
                           text=[f"{aktivitaet[v]:g}" for v in var], textposition="outside", cliponaxis=False,
                           hovertemplate="%{x}: Aktivität %{y:g}<extra></extra>"))
    fig.update_layout(title=titel, yaxis_title="Aktivität")
    fig.update_yaxes(range=[0, max(1.0, max(aktivitaet.values(), default=0.0) * 1.25)])
    return _fest(fig, 330)


def build_streifen(reihen: dict, budget: int, beschriftung: dict, farben: dict, titel: str, key_hoehe: int = 380):
    """Streifendiagramm: ein Punkt je Lauf (Konflikte, logarithmische Achse), Abbrüche als Kreuz am Budget, Median als Strich.

    `reihen`: Verfahren -> {"konflikte": [...], "antwort": [...]}; die Reihenfolge des Wörterbuchs ist die der Achse."""
    fig = go.Figure()
    namen = list(reihen)
    for i, name in enumerate(namen):
        k, ant = reihen[name]["konflikte"], reihen[name]["antwort"]
        n = len(k)
        xs = [i + (j - (n - 1) / 2) * 0.5 / max(n - 1, 1) for j in range(n)]
        ys = [max(c, 0.7) for c in k]
        farbe = farben.get(name, C.COLOR_AKTIV)
        fig.add_trace(go.Scatter(
            x=xs, y=ys, mode="markers", name=beschriftung[name],
            marker=dict(color=farbe, size=9, symbol=["x" if a is None else "circle" for a in ant],
                        line=dict(width=1.5, color=farbe)),
            customdata=[[c, "Abbruch am Budget" if a is None else ("erfüllbar" if a else "unerfüllbar")] for c, a in zip(k, ant)],
            hovertemplate="%{customdata[0]} Konflikte (%{customdata[1]})<extra>" + beschriftung[name] + "</extra>"))
        med = median(k)
        fig.add_shape(type="line", x0=i - 0.32, x1=i + 0.32, y0=max(med, 0.7), y1=max(med, 0.7), line=dict(color=farbe, width=3))
    fig.add_hline(y=budget, line=dict(color="rgba(150,150,150,0.8)", dash="dot"), annotation_text=f"Budget {budget:,}".replace(",", "."),
                  annotation_position="top left")
    fig.update_xaxes(tickmode="array", tickvals=list(range(len(namen))), ticktext=[beschriftung[n].replace(" + ", "<br>+ ") for n in namen],
                     range=[-0.6, len(namen) - 0.4])
    fig.update_yaxes(type="log", range=[-0.2, math.log10(budget * 2)], title="Konflikte (logarithmisch)")
    fig.update_layout(title=titel)
    return _fest(fig, key_hoehe)
