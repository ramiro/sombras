# coding: utf-8
from datetime import datetime, timedelta
from math import tan

import ephem
import pytz

USAR_FUERZA_BRUTA = False

ANIO = 2018

DIAS_MARGEN_ALREDEDOR_SOLSTICIO = 2

PUNTOS = [
    {
        "descr": "Faro del Bicentenario, Córdoba, Argentina",
        "lat": "-31.42841",  # -31.428167
        "long": "-64.18202",  # 64.182172
        "huso": "America/Argentina/Cordoba",
        "altitud": 424.50,
        "altura": 60,
    },
    {
        "descr": "Reloj de Sol Trópico de Capricornio, Huacalera, Jujuy, Argentina",
        "lat": "-23.447783",
        "long": "-65.351664",
        "huso": "America/Argentina/Jujuy",
        "altitud": 2741.75,
    },
    {
        "descr": "Intersección de Latitud real Trópico de Capricornio en 2018 según Wikipedia c/Ruta Nacional 9, Huacalera, Jujuy, Argentina",
        "lat": "-23.43686",
        "long": "-65.351020",
        "huso": "America/Argentina/Jujuy",
        "altitud": 2741.75,
    },
    {
        "descr": "Intersección de Latitud en la que PyEphem computa que el Sol se encontrará a 90 grados c/Ruta Nacional 9, Huacalera, Jujuy, Argentina",
        "lat": "-23.43518",
        "long": "-65.351325",
        "huso": "America/Argentina/Jujuy",
        "altitud": 2741.75,
    },
    {
        "descr": "Obelisco, CABA, Argentina",
        "lat": "-34.603611",
        "long": "-58.381667",
        "huso": "America/Argentina/Buenos_Aires",
        "altitud": 37.75,
        "altura": 67.5,
    },
]


def mostrar_resultados(punto, salida):
    print(punto["descr"])
    print("\tMomento de sombra mas corta: %s" % ephem.localtime(salida["momento_sombra_mas_corta"]))
    print("\tAltitud del Sol en ese momento: %s" % salida["max_alt"])
    altura = punto.get("altura")
    if altura is not None:
        longitud_sombra = altura / tan(salida["max_alt"])
        print("\tLargo de la sombra en ese momento: %.03fm" % longitud_sombra)


def datetime2utc(dt, tzdata):
    dt_con_tz = tzdata.localize(dt)
    return dt_con_tz.astimezone(pytz.utc)


def datetime2PyEphemDate(dt, tzdata):
    return ephem.Date(datetime2utc(dt, tzdata))


def solsticio_pyephem(lat, anio, huso):
    inicio_utc = datetime2utc(datetime(anio, 1, 1), huso)
    if float(lat) < 0:
        return ephem.next_winter_solstice(inicio_utc)  # Hemisferio Sur
    elif float(lat) > 0:
        return ephem.next_summer_solstice(inicio_utc)  # Hemisferio Norte
    raise Exception("Por ahora no soporto ubicaciones sobre el Ecuador :(")


def estrategia_rapida_usando_transit(punto, anio):
    """Estrategia usando método Observer.next_transit()"""
    sol = ephem.Sun()
    solsticio = solsticio_pyephem(punto["lat"], anio, punto["huso_horario"])
    salida = {"max_alt": -90.0}
    dt = solsticio.datetime() - timedelta(days=DIAS_MARGEN_ALREDEDOR_SOLSTICIO)
    while dt - solsticio.datetime() <= timedelta(days=DIAS_MARGEN_ALREDEDOR_SOLSTICIO):
        momento_inicial = datetime2PyEphemDate(dt, punto["huso_horario"])
        punto["ubicacion"].date = momento_inicial
        momento = punto["ubicacion"].next_transit(sol)
        if sol.alt > salida["max_alt"]:
            salida["max_alt"] = sol.alt
            salida["momento_sombra_mas_corta"] = momento

        dt += timedelta(days=1)

    mostrar_resultados(punto, salida)


def estrategia_fuerza_bruta(punto, anio):
    """Obtiene máxima altitud iterando en saltos de un segundo"""
    if USAR_FUERZA_BRUTA:
        sol = ephem.Sun()
        solsticio = solsticio_pyephem(punto["lat"], anio, punto["huso_horario"])
        salida = {"max_alt": -90.0}
        dt = solsticio.datetime() - timedelta(days=DIAS_MARGEN_ALREDEDOR_SOLSTICIO)
        while dt - solsticio.datetime() <= timedelta(days=DIAS_MARGEN_ALREDEDOR_SOLSTICIO):
            momento = datetime2PyEphemDate(dt, punto["huso_horario"])
            punto["ubicacion"].date = momento
            sol.compute(punto["ubicacion"])
            if sol.alt > salida["max_alt"]:
                salida["max_alt"] = sol.alt
                salida["momento_sombra_mas_corta"] = momento

            dt += timedelta(seconds=1)

        mostrar_resultados(punto, salida)


if __name__ == "__main__":
    for punto in PUNTOS:
        ubicacion = ephem.Observer()
        ubicacion.lat = punto["lat"]
        ubicacion.long = punto["long"]
        altitud = punto.get("altitud")
        if altitud is not None:
            ubicacion.elevation = altitud

        punto["ubicacion"] = ubicacion
        punto["huso_horario"] = pytz.timezone(punto["huso"])

        estrategia_rapida_usando_transit(punto, ANIO)
        estrategia_fuerza_bruta(punto, ANIO)
