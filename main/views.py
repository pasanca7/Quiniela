from django.shortcuts import render, redirect
from main.models import Partido, Pleno, Quiniela, NoticiaPrimera
from bs4 import BeautifulSoup
import urllib.request
import lxml
import os, os.path
from whoosh import index
from whoosh.fields import Schema, TEXT, NUMERIC
from whoosh.qparser import QueryParser, MultifieldParser
from whoosh.index import create_in,open_dir

#encoding:utf-8
def get_schema():
    return Schema(titular=TEXT(stored=True),
                        link=TEXT(stored=True),
                        resumen = TEXT(stored=True),
                        division = TEXT(stored=True))
    
def crear_indice():
    if not os.path.exists("indexdir"):
        os.mkdir('indexdir')    
    
    schema = get_schema()
    
    index.create_in("indexdir", schema)
    
def add_doc(noticias):
    try:
        ix = index.open_dir("indexdir")
        writer = ix.writer()
        i = 0
        for noticia in noticias:
            writer.add_document(titular = str(noticia[0]), 
                                link = str(noticia[1]), 
                                resumen = str(noticia[2]),
                                division = str(noticia[3]))        
            i += 1
        print("Se han indexado " + str(i) + " documentos" )
        writer.commit()
    except Exception as e:
        print(e)

def extraerNoticias():    
    res = []
    f = urllib.request.urlopen("https://cadenaser.com/tag/primera_division/a/")
    s = BeautifulSoup(f, "lxml")
    principal = s.find("main", class_="main")
    noticias = principal.findAll("li", class_="item")
    
    i = 0
    for noticia in noticias:
        titulo = noticia.find("h2", class_="module-title")
        if(titulo == None):
            noticias.pop(i)
        i = i + 1

    for n in noticias:
        noticia = []
        titulo = n.find("h2", class_="module-title").find("a")["title"]
        link = n.find("h2", class_="module-title").find("a")["href"]
        resumen = n.find("p", class_="module-text").text
        
        noticia.append(titulo)
        noticia.append(link)
        noticia.append(resumen)
        noticia.append("1")

        res.append(noticia)
    
    f = urllib.request.urlopen("https://cadenaser.com/tag/segunda_division_a/a/")
    s = BeautifulSoup(f, "lxml")
    principal = s.find("main", class_="main")
    noticias = principal.findAll("li", class_="item")
    
    i = 0
    for noticia in noticias:
        titulo = noticia.find("h2", class_="module-title")
        if(titulo == None):
            noticias.pop(i)
        i = i + 1

    for n in noticias:
        noticia = []
        titulo = n.find("h2", class_="module-title").find("a")["title"]
        link = n.find("h2", class_="module-title").find("a")["href"]
        resumen = n.find("p", class_="module-text").text
        
        noticia.append(titulo)
        noticia.append(link)
        noticia.append(resumen)
        noticia.append("2")

        res.append(noticia)
    return add_doc(res)

def obtnerTodasNoticias():
    ix=open_dir("indexdir")
    return ix.searcher().documents() 


def buscarPorTexto(texto):
    ix=open_dir("indexdir")
    with ix.searcher() as searcher:
        myquery = MultifieldParser(["titular","resumen"], ix.schema).parse(texto)
        results = searcher.search(myquery)
        noticias = []
        for r in results:
            noticia = []
            noticia = {'titular': r['titular'], 'resumen':r['resumen'], 'link':r['link'], 'division':r['division']}
            noticias.append(noticia)
        return noticias
    
def buscaNoticias(request):
    mensajeError = ""
    texto = request.POST.get('texto')
    noticias = buscarPorTexto(texto)
    if len(noticias) == 0:
        mensajeError = "No se han encontrado resultados, prueba de nuevo"
    return render(request, 'noticias.html', {'noticias': noticias, 'mensajeError': mensajeError})
    
def cargaNoticias(request):
    if request.method == 'POST':
        if 'Aceptar' in request.POST:
            crear_indice()
            extraerNoticias()
            mensaje = "Se han actualizado las noticias satisfactoriamente"
            return render(request, 'cargaQuinielaBD.html', {'mensaje':mensaje})
        else:
            return redirect("/")
    return render(request, 'confirmacion.html')    

def noticias(request):
    noticias = obtnerTodasNoticias()
    noticiasPrimera = []
    noticiasSegunda = []
    for n in noticias:
        if n.get('division') == '1':
            noticiasPrimera.append(n)
        else :
            noticiasSegunda.append(n)
    return render(request, 'noticias.html', {'noticiasPrimera': noticiasPrimera, 'noticiasSegunda': noticiasSegunda})

    #return render(request, 'noticias.html', {'noticias': noticias})

def populateDB():
    #borramos todas las tablas de la BD
    Partido.objects.all().delete()
    Pleno.objects.all().delete()
    Quiniela.objects.all().delete()
    
    #extraemos los datos de la web con BS
    f = urllib.request.urlopen("https://resultados.as.com/quiniela/")
    s = BeautifulSoup(f, "lxml")
    urlNuevaJornada = "https:" + s.find("span", class_="siguiente").find("a")["href"]
    temporada = urlNuevaJornada[35:44].replace("_", "-")

    if(urlNuevaJornada == "https:#"):
        urlNuevaJornada = "https://resultados.as.com/quiniela/"
        
    if(temporada == ""):
        url = "https:" + s.find("span", class_="anterior").find("a")["href"]
        temporada = url[35:44].replace("_", "-")
        
    jornada = s.find("h2", class_="tit-modulo").find("a").text
    jornada = jornada.split(" ")[1]
    quiniela = Quiniela.objects.create(temporada = temporada, jornada = jornada)
    
    p = urllib.request.urlopen(urlNuevaJornada)
    s = BeautifulSoup(p, "lxml")
    
    partidos = s.find("div", class_="resultados-quiniela cf").findAll("div", class_="cont-partido")
    partidos = partidos[0:14]
    
    for x in partidos:
        local = x.find("a", class_="local").find("span", class_="nombre-equipo").string
        visitante = x.find("a", class_="visitante").find("span", class_="nombre-equipo").string
        partidos = Partido.objects.create(local=local, visitante=visitante, uno=0, x=0, dos=0, quiniela=quiniela)
    
    pleno = s.find("div", class_="cont-partido pleno-15")
    local = pleno.findAll("span", class_="partido")[0].find("a", class_="visitante").find("span", class_="nombre-equipo").string
    visitante = pleno.findAll("span", class_="partido")[1].find("a", class_="visitante").find("span", class_="nombre-equipo").string
    pleno = Pleno.objects.create(local=local, visitante=visitante, ceroL=0, unoL=0, dosL=0, masL=0, ceroV=0,unoV=0, dosV=0, masV=0, quiniela=quiniela)
    
    return quiniela

def inicio(request):
    quiniela = Quiniela.objects.get()
    jornada = quiniela.jornada
    temporada = quiniela.temporada
    noticias = obtnerTodasNoticias()
    noticiasPrimera = 0
    noticiasSegunda = 0
    for n in noticias:
        if n.get('division') == '1':
            noticiasPrimera = noticiasPrimera + 1
        else :
            noticiasSegunda = noticiasSegunda + 1
    return render(request,'inicio.html', {'jornada': jornada, 'temporada': temporada, 'noticiasSegunda':noticiasSegunda, 'noticiasPrimera':noticiasPrimera})

def quiniela(request):
    quiniela = Quiniela.objects.get()
    partidos = Partido.objects.all()
    return render(request,'quiniela.html', {'quiniela':quiniela, 'partidos':partidos, })

def cargaQuiniela(request):
    
    if request.method == 'POST':
        if 'Aceptar' in request.POST:
            
            f = urllib.request.urlopen("https://resultados.as.com/quiniela/")
            s = BeautifulSoup(f, "lxml")
            urlNuevaJornada = "https:" + s.find("span", class_="siguiente").find("a")["href"]
            nuevaTemporada = urlNuevaJornada[35:44].replace("_", "-")
        
            if(urlNuevaJornada == "https:#"):
                urlNuevaJornada = "https://resultados.as.com/quiniela/"
                
            if(nuevaTemporada == ""):
                url = "https:" + s.find("span", class_="anterior").find("a")["href"]
                nuevaTemporada = url[35:44].replace("_", "-")
                
            nuevaJornada = s.find("h2", class_="tit-modulo").find("a").text
            nuevaJornada = nuevaJornada.split(" ")[1]
            
            quiniela = Quiniela.objects.get()
            jornada = quiniela.jornada
            temporada = quiniela.temporada
            
            if jornada == nuevaJornada and temporada == nuevaTemporada:
                mensaje = "Error: la quiniela registrada sigue vigente"
                return render(request, 'cargaQuinielaBD.html', {'mensaje':mensaje})
            else:            
                nuevaQuiniela = populateDB()
                mensaje = "Se ha actualizado la quiniela a la de la jornada "+ nuevaQuiniela.jornada
                return render(request, 'cargaQuinielaBD.html', {'mensaje':mensaje})
        else:
            return redirect("/")
    return render(request, 'confirmacion.html')

def gaurdaResultado(request):
    idPartido = request.POST.get("id")
    resultado = request.POST.get("resultado")

    quiniela = Quiniela.objects.get()
    partido = Partido.objects.get(id=idPartido)
    
    if(resultado == "1"):
        n1 = partido.uno
        partido.uno = n1 + 1;
    if(resultado == "X"):
        nx = partido.x
        partido.x = nx + 1
    if(resultado == "2"):
        n2 = partido.dos
        partido.dos = n2 + 1
    
    partido.votantes.add(request.user)
    partido.save()
    
    partidos = Partido.objects.all()
    return render(request,'quiniela.html', {'quiniela':quiniela, 'partidos':partidos})

def guardaPleno(request):
    marcadorL = request.POST.get("plenoL")
    marcadorV = request.POST.get("plenoV")

    quiniela = Quiniela.objects.get()
    pleno = quiniela.pleno
    
    if(marcadorL == "0"):
        l0 = pleno.ceroL
        pleno.ceroL = l0 + 1;
    if(marcadorL == "1"):
        l1 = pleno.unoL
        pleno.unoL = l1 + 1;
    if(marcadorL == "2"):
        l2 = pleno.dosL
        pleno.dosL = l2 + 1
    if(marcadorL == "M"):
        lm = pleno.masL
        pleno.masL = lm + 1
    
    if(marcadorV == "0"):
        v0 = pleno.ceroV
        pleno.ceroV = v0 + 1;
    if(marcadorV == "1"):
        v1 = pleno.unoV
        pleno.unoV = v1 + 1;
    if(marcadorV == "2"):
        v2 = pleno.dosV
        pleno.dosV = v2 + 1
    if(marcadorV == "M"):
        vm = pleno.masV
        pleno.masV = vm + 1
    
    pleno.votantes.add(request.user)
    pleno.save()
    
    partidos = Partido.objects.all()
    return render(request,'quiniela.html', {'quiniela':quiniela, 'partidos':partidos})
