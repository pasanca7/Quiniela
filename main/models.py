from django.db import models
from django.contrib.auth.models import User
from numpy.f2py.crackfortran import verbose

class Quiniela(models.Model):
    temporada = models.CharField(max_length=9, verbose_name='Temporada')
    jornada = models.CharField(max_length=2, verbose_name='Jornada')
    
class Partido(models.Model):
    local = models.CharField(max_length=30, verbose_name='Local')
    visitante = models.CharField(max_length=30, verbose_name='Visitante')
    uno = models.IntegerField(blank = True, null = True, verbose_name='Uno')
    x = models.IntegerField(blank = True, null = True, verbose_name='X')
    dos = models.IntegerField(blank = True, null = True, verbose_name='Dos')
    quiniela = models.ForeignKey(Quiniela, on_delete=models.SET_NULL, null=True)
    votantes = models.ManyToManyField(User)

class Pleno(models.Model):
    local = models.CharField(max_length=30, verbose_name='Local')
    visitante = models.CharField(max_length=30, verbose_name='Visitante')
    ceroL = models.IntegerField(blank = True, null = True, verbose_name='CeroL')
    unoL = models.IntegerField(blank = True, null = True, verbose_name='UnoL')
    dosL = models.IntegerField(blank = True, null = True, verbose_name='DosL')
    masL = models.IntegerField(blank = True, null = True, verbose_name='MasL')
    ceroV = models.IntegerField(blank = True, null = True, verbose_name='CeroV')
    unoV = models.IntegerField(blank = True, null = True, verbose_name='UnoV')
    dosV = models.IntegerField(blank = True, null = True, verbose_name='DosV')
    masV = models.IntegerField(blank = True, null = True, verbose_name='MasV')
    quiniela = models.OneToOneField(Quiniela, on_delete=models.CASCADE, primary_key=True,)
    votantes = models.ManyToManyField(User)

class NoticiaPrimera(models.Model):
    titular = models.TextField(verbose_name='Titular')
    resumen = models.TextField(verbose_name='Resumen')
    link = models.TextField(verbose_name='Link')
    division = models.CharField(max_length=30, verbose_name="Division")