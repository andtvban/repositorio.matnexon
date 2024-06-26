# -*- coding: utf-8 -*-

import sys

if sys.version_info[0] < 3:
    PY3 = False

    import htmlentitydefs
    from htmlentitydefs import name2codepoint as n2cp

    import urllib
    import urlparse
else:
    PY3 = True

    unicode = str
    unichr = chr

    import html.entities as htmlentitydefs
    from html.entities import name2codepoint as n2cp

    import urllib.parse as urlparse

import re, time

from core import httptools
from platformcode import logger


# ~ Expresiones regulares

def find_single_match(data, patron, index=0):
    try:
        matches = re.findall(patron, data, flags=re.DOTALL)
        return matches[index]
    except:
        return ""

def find_multiple_matches(text, pattern):
    return re.findall(pattern, text, re.DOTALL)


def get_match(data, patron, index=0):
    matches = re.findall(patron, data, flags=re.DOTALL)
    return matches[index]


def printMatches(matches):
    for i, match in enumerate(matches):
        logger.info("%d %s" % (i, match))


def es_genero_xxx(texto):
    # ~ Devuelve True si es algún género erótico / xxx
    # ~ ['Erótica', 'Erótico', 'Erotico', 'Erotica', 'Xxx, erotico', 'Adultos +18', 'Eróticas +18', 'Eroticas +18', 'Animación para adultos', 'Abusos sexuales']

    txt = texto.lower().replace('ó', 'o')
    if 'erotic' in txt or '+18' in txt or 'adulto' in txt or 'sexual' in txt:
        return True
    return False


def clean_cfemail(texto):
   # ~ Si hay alguna @ en el texto, cloudflare lo considera como un email y lo protege en un link (Ej: Tod@s)

    matches = find_multiple_matches(texto, ' data-cfemail="([^"]+)"')
    for cfemail in matches:
        r = int(cfemail[:2],16)
        email = ''.join([chr(int(cfemail[i:i+2], 16) ^ r) for i in range(2, len(cfemail), 2)])
        texto = re.sub('<a href="/cdn-cgi/l/email-protection" class="__cf_email__" data-cfemail="%s">.*?</a>' % cfemail, email, texto)

    return texto


def entityunescape(cadena):
    return unescape(cadena)


def unescape(text):
    """Removes HTML or XML character references
       and entities from a text string.
       keep &amp;, &gt;, &lt; in the source code.
    from Fredrik Lundh
    http://effbot.org/zone/re-sub.htm#unescape-html
    """

    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # ~ character reference
            try:
                if text[:3] == "&#x":
                    text = unichr(int(text[3:-1], 16)).encode("utf-8")
                else:
                    text = unichr(int(text[2:-1])).encode("utf-8")
                if PY3 and isinstance(text, bytes):
                    text = text.decode("utf-8")
                return text

            except ValueError:
                logger.error("error de valor")
                pass
        else:
            # ~ named entity
            try:
                text = unichr(n2cp[text[1:-1]]).encode("utf-8")
                if PY3 and isinstance(text, bytes):
                    text = text.decode("utf-8")
            except KeyError:
                logger.error("keyerror")
                pass
            except:
                pass
        return text  # ~ leave as is

    return re.sub("&#?\w+;", fixup, text)


def decodeHtmlentities(string):
    # ~ Convierte los codigos html "&ntilde;" y lo reemplaza por "ñ" caracter unicode utf-8

    string = entitiesfix(string)
    entity_re = re.compile("&(#?)(\d{1,5}|\w{1,8});")

    def substitute_entity(match):
        ent = match.group(2)
        if match.group(1) == "#":
            ent = unichr(int(ent)).encode('utf-8')
            if PY3 and isinstance(ent, bytes):
                ent = ent.decode("utf-8")
            return ent
        else:
            cp = n2cp.get(ent)

            if cp:
                cp = unichr(cp).encode('utf-8')
                if PY3 and isinstance(cp, bytes):
                    cp = cp.decode("utf-8")
                return cp
            else:
                return match.group()

    return entity_re.subn(substitute_entity, string)[0]


def entitiesfix(string):
    # ~ Las entidades comienzan siempre con el símbolo & , y terminan con un punto y coma ( ; ).

    string = string.replace("&aacute", "&aacute;")
    string = string.replace("&eacute", "&eacute;")
    string = string.replace("&iacute", "&iacute;")
    string = string.replace("&oacute", "&oacute;")
    string = string.replace("&uacute", "&uacute;")
    string = string.replace("&Aacute", "&Aacute;")
    string = string.replace("&Eacute", "&Eacute;")
    string = string.replace("&Iacute", "&Iacute;")
    string = string.replace("&Oacute", "&Oacute;")
    string = string.replace("&Uacute", "&Uacute;")
    string = string.replace("&uuml", "&uuml;")
    string = string.replace("&Uuml", "&Uuml;")
    string = string.replace("&ntilde", "&ntilde;")
    string = string.replace("&#191", "&#191;")
    string = string.replace("&#161", "&#161;")
    string = string.replace(";;", ";")
    string = string.replace("&#x27;", "")
    return string


def htmlclean(cadena):
    cadena = re.compile("<!--.*?-->", re.DOTALL).sub("", cadena)

    cadena = cadena.replace("<center>", "")
    cadena = cadena.replace("</center>", "")
    cadena = cadena.replace("<cite>", "")
    cadena = cadena.replace("</cite>", "")
    cadena = cadena.replace("<em>", "")
    cadena = cadena.replace("</em>", "")
    cadena = cadena.replace("<u>", "")
    cadena = cadena.replace("</u>", "")
    cadena = cadena.replace("<li>", "")
    cadena = cadena.replace("</li>", "")
    cadena = cadena.replace("<turl>", "")
    cadena = cadena.replace("</tbody>", "")
    cadena = cadena.replace("<tr>", "")
    cadena = cadena.replace("</tr>", "")
    cadena = cadena.replace("<![CDATA[", "")
    cadena = cadena.replace("<wbr>", "")
    cadena = cadena.replace("<Br />", " ")
    cadena = cadena.replace("<BR />", " ")
    cadena = cadena.replace("<Br>", " ")
    cadena = re.compile("<br[^>]*>", re.DOTALL).sub(" ", cadena)

    cadena = re.compile("<script.*?</script>", re.DOTALL).sub("", cadena)

    cadena = re.compile("<option[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</option>", "")

    cadena = re.compile("<button[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</button>", "")

    cadena = re.compile("<i[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</iframe>", "")
    cadena = cadena.replace("</i>", "")

    cadena = re.compile("<table[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</table>", "")

    cadena = re.compile("<td[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</td>", "")

    cadena = re.compile("<div[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</div>", "")

    cadena = re.compile("<dd[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</dd>", "")

    cadena = re.compile("<b[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</b>", "")

    cadena = re.compile("<font[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</font>", "")

    cadena = re.compile("<strong[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</strong>", "")

    cadena = re.compile("<small[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</small>", "")

    cadena = re.compile("<span[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</span>", "")

    cadena = re.compile("<a[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</a>", "")

    cadena = re.compile("<p[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</p>", "")

    cadena = re.compile("<ul[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</ul>", "")

    cadena = re.compile("<h1[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</h1>", "")

    cadena = re.compile("<h2[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</h2>", "")

    cadena = re.compile("<h3[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</h3>", "")

    cadena = re.compile("<h4[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</h4>", "")

    cadena = re.compile("<!--[^-]+-->", re.DOTALL).sub("", cadena)

    cadena = re.compile("<img[^>]*>", re.DOTALL).sub("", cadena)

    cadena = re.compile("<object[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</object>", "")
    cadena = re.compile("<param[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</param>", "")
    cadena = re.compile("<embed[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</embed>", "")

    cadena = re.compile("<title[^>]*>", re.DOTALL).sub("", cadena)
    cadena = cadena.replace("</title>", "")

    cadena = re.compile("<link[^>]*>", re.DOTALL).sub("", cadena)

    cadena = cadena.replace("\t", "")
    cadena = entityunescape(cadena)
    return cadena


def slugify(title):
    # ~ Sustituye acentos y eñes

    title = title.replace("Á", "a")
    title = title.replace("É", "e")
    title = title.replace("Í", "i")
    title = title.replace("Ó", "o")
    title = title.replace("Ú", "u")
    title = title.replace("á", "a")
    title = title.replace("é", "e")
    title = title.replace("í", "i")
    title = title.replace("ó", "o")
    title = title.replace("ú", "u")
    title = title.replace("À", "a")
    title = title.replace("È", "e")
    title = title.replace("Ì", "i")
    title = title.replace("Ò", "o")
    title = title.replace("Ù", "u")
    title = title.replace("à", "a")
    title = title.replace("è", "e")
    title = title.replace("ì", "i")
    title = title.replace("ò", "o")
    title = title.replace("ù", "u")
    title = title.replace("ç", "c")
    title = title.replace("Ç", "C")
    title = title.replace("Ñ", "n")
    title = title.replace("ñ", "n")
    title = title.replace("/", "-")
    title = title.replace("&amp;", "&")

    # ~ Pasa a minúsculas
    title = title.lower().strip()

    # ~ Elimina caracteres no válidos
    validchars = "abcdefghijklmnopqrstuvwxyz1234567890- "
    title = ''.join(c for c in title if c in validchars)

    # ~ Sustituye espacios en blanco duplicados y saltos de línea
    title = re.compile("\s+", re.DOTALL).sub(" ", title)

    # ~ Sustituye espacios en blanco por guiones
    title = re.compile("\s", re.DOTALL).sub("-", title.strip())

    # ~ Sustituye espacios en blanco duplicados y saltos de línea
    title = re.compile("\-+", re.DOTALL).sub("-", title)

    # ~ Arregla casos especiales
    if title.startswith("-"):
        title = title[1:]

    if title == "":
        title = "-" + str(time.time())

    return title


def remove_htmltags(string):
    return re.sub('<[^<]+?>', '', string)


def remove_show_from_title(title, show):
    # ~ Quita el nombre del programa del título

    if slugify(title).startswith(slugify(show)):
        # ~ Convierte a unicode primero, o el encoding se pierde
        if not PY3: title = unicode(title, "utf-8", "replace")
        if not PY3: show = unicode(show, "utf-8", "replace")
        title = title[len(show):].strip()

        if title.startswith("-"):
            title = title[1:].strip()

        if title == "":
            title = str(time.time())

        # ~ Vuelve a utf-8
        title = title.encode("utf-8", "ignore")
        if PY3 and isinstance(title, bytes):
            title = title.decode("utf-8")
        show = show.encode("utf-8", "ignore")
        if PY3 and isinstance(show, bytes):
            show = show.decode("utf-8")

    return title


def get_filename_from_url(url):
    parsed_url = urlparse.urlparse(url)
    try:
        filename = parsed_url.path
    except:
        # ~ Si falla es porque la implementación de parsed_url no reconoce los atributos como "path"
        if len(parsed_url) >= 4:
            filename = parsed_url[2]
        else:
            filename = ""

    if "/" in filename:
        filename = filename.split("/")[-1]

    return filename


def get_domain_from_url(url):
    parsed_url = urlparse.urlparse(url)
    try:
        domain = parsed_url[1]
    except Exception:
        domain = ""

    return domain


def get_season_and_episode(title):
    """
    Retorna el numero de temporada y de episodio en formato "1x01" obtenido del titulo de un episodio
    Ejemplos de diferentes valores para title y su valor devuelto:
        "serie 101x1.strm", "s101e1.avi", "t101e1.avi"  -> '101x01'
        "Name TvShow 1x6.avi" -> '1x06'
        "Temp 3 episodio 2.avi" -> '3x02'
        "Alcantara season 13 episodie 12.avi" -> '13x12'
        "Temp1 capitulo 14" -> '1x14'
        "Temporada 1: El origen Episodio 9" -> '' (entre el numero de temporada y los episodios no puede haber otro texto)
        "Episodio 25: titulo episodio" -> '' (no existe el numero de temporada)
        "Serie X Temporada 1" -> '' (no existe el numero del episodio)
    @type title: str
    @param title: titulo del episodio de una serie
    @rtype: str
    @return: Numero de temporada y episodio en formato "1x01" o cadena vacia si no se han encontrado
    """
    filename = ""

    patrons = ["(\d+)\s*[x-]\s*(\d+)", "(\d+)\s*×\s*(\d+)", "(?:s|t)(\d+)e(\d+)",
               "(?:season|temp\w*)\s*(\d+)\s*(?:capitulo|epi|episode\w*)\s*(\d+)"]

    for patron in patrons:
        try:
            matches = re.compile(patron, re.I).search(title)
            if matches:
                if len(matches.group(1)) == 1:
                    filename = matches.group(1) + "x" + matches.group(2).zfill(2)
                else:
                    filename = matches.group(1).lstrip('0') + "x" + matches.group(2).zfill(2)
                break
        except:
            pass

    logger.info("'" + title + "' -> '" + filename + "'")

    return filename

