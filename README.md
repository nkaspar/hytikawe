# RecipeDB

## Sovelluksen toiminnot

- Käyttäjä pystyy luomaan tunnuksen ja kirjautumaan sisään sovellukseen.
- Käyttäjä pystyy lisäämään, muokkaamaan ja poistamaan reseptejä.
- Reseptiin voi lisätä tarvittavat ainekset ja valmistusohjeen.
- Käyttäjä näkee sovellukseen lisätyt reseptit.
- Käyttäjä pystyy etsimään reseptejä hakusanalla.
- Hakusanaa voi etsiä reseptin otsikosta, aineksista tai valmistusohjeesta.
- Käyttäjä pystyy valitsemaan reseptille yhden tai useamman luokittelun. Mahdolliset luokat ovat tietokannassa.
- Käyttäjä pystyy lisäämään toisen käyttäjän reseptiin muistiinpanon, joka näkyy reseptisivulla.
- Sovelluksessa on käyttäjäsivut, jotka näyttävät käyttäjän lisäämät reseptit ja reseptien määrän.

## Sovelluksen asennus

1. Asenna flask

```
$ pip install flask
```

2. Luo tietokanta

```
$ sqlite3 database.db < schema.sql
$ sqlite3 database.db < init.sql
```

3. Käynnistä sovellus

```
$ flask run
```
