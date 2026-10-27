"""Reportes calculados, agrupados y filtrados (devuelven datos, no imprimen)."""
from collections import Counter, defaultdict


def ranking(jugadores, top: int = 5) -> list:
    return sorted(jugadores, key=lambda j: (-j.mejor_puntaje, j.nombre.lower()))[:top]


def resumen_por_dificultad(partidas) -> dict:
    grupos = defaultdict(list)
    for p in partidas:
        grupos[p.dificultad].append(p.puntaje)
    return {
        d: {"partidas": len(ps), "promedio": round(sum(ps) / len(ps), 2), "maximo": max(ps)}
        for d, ps in grupos.items()
    }


def conteo_medallas(partidas) -> dict:
    return dict(Counter(p.medalla for p in partidas))


def jugadores_sin_partidas(repo) -> list:
    """Diferencia de conjuntos: todos los ids MENOS los que ya jugaron."""
    con_partidas = {p.jugador_id for p in repo.partidas}
    sin_partidas = set(repo.jugadores) - con_partidas
    return sorted((repo.jugadores[i] for i in sin_partidas), key=lambda j: j.nombre.lower())


def resumen_general(repo) -> dict:
    ps = repo.partidas
    return {
        "jugadores": len(repo.jugadores),
        "activos": sum(j.activo for j in repo.jugadores.values()),
        "partidas": len(ps),
        "promedio_puntaje": round(sum(p.puntaje for p in ps) / len(ps), 2) if ps else 0,
        "monedas_en_circulacion": sum(j.monedas for j in repo.jugadores.values()),
    }
