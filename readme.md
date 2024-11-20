# MD2Video

Questo tool converte post markdown in video narrati automaticamente.

## Installazione

```bash
# Clona il repository
git clone https://github.com/yourusername/md2video.git
cd md2video

# Crea e avvia il container Docker
docker-compose build
docker-compose up -d
```

## Uso

Il tool può essere eseguito in modalità CLI con i seguenti comandi:

```bash
# Avvia app con CLI
docker-compose run --rm md2video

# Genera solo gli script XML
docker-compose run --rm md2video script

# Genera video da uno script esistente
docker-compose run --rm md2video video

# Genera sia script che video in un unico comando
docker-compose run --rm md2video genera
```

## Struttura delle Directory

```
md2video/
├── content/posts/          # Directory contenente i post markdown
├── video_output/           # Directory output per i video
│   ├── assets/             # Directory per gli sfondi personalizzati
│   ├── temp/               # Directory temporanea (auto-generata)
│   └── videos/             # Video generati
└── scripts/                # Script XML generati
```

## Personalizzazione degli Script XML

Gli script XML generati possono essere personalizzati per utilizzare sfondi e animazioni diverse per ogni sezione.

### Esempio Base
```xml
<?xml version="1.0" encoding="UTF-8"?>
<script version="1.0">
  <metadata>
    <title>Titolo del Video</title>
    <url>https://example.com/post</url>
    <date>2024-11-20</date>
  </metadata>
  <content>
    <section level="1" type="intro">
      <heading>Introduzione</heading>
      <speech pause="0.5">Testo dell'introduzione</speech>
    </section>
  </content>
</script>
```

### Esempio con Sfondo Personalizzato
```xml
<section level="1" type="intro" background="intro_bg.png">
  <heading>Introduzione</heading>
  <speech pause="0.5">Testo con sfondo personalizzato</speech>
</section>
```

### Esempio con Animazione
```xml
<section level="2" type="content" animation="slide_left">
  <heading>Sezione con Animazione</heading>
  <speech pause="0.3">Questo testo apparirà con un'animazione</speech>
</section>
```

### Esempio Completo con Sfondo e Animazione
```xml
<section level="1" type="intro" background="custom_bg.png" animation="zoom">
  <heading>Sezione Personalizzata</heading>
  <speech pause="0.5">Prima frase con pausa lunga</speech>
  <speech pause="0.3">Seconda frase con pausa breve</speech>
</section>
```

## Sfondi Personalizzati

Gli sfondi personalizzati devono essere posizionati nella directory `video_output/assets/` e possono essere referenziati negli script XML usando l'attributo `background`.

## Transizioni Disponibili

### Base
- `fade`: Dissolvenza in entrata e uscita
- `slide_left`: Scorrimento da destra a sinistra
- `slide_right`: Scorrimento da sinistra a destra
- `slide_up`: Scorrimento dal basso all'alto
- `slide_down`: Scorrimento dall'alto al basso

### Zoom
- `zoom_in`: Ingrandimento progressivo
- `zoom_out`: Rimpicciolimento progressivo
- `zoom_pulse`: Effetto pulsante leggero

### Rotazioni
- `rotate_cw`: Rotazione oraria
- `rotate_ccw`: Rotazione antioraria

### Combinazioni
- `zoom_fade`: Dissolvenza con zoom
- `rotate_fade`: Dissolvenza con rotazione

## Dimensioni Raccomandate
- Larghezza: 1920px
- Altezza: 1080px
- Formato: PNG o JPG

## Note
- Gli sfondi personalizzati verranno automaticamente ridimensionati alla risoluzione del video
- Se uno sfondo specificato non viene trovato, verrà utilizzato lo sfondo gradiente di default
- Le pause tra i speech possono essere personalizzate con l'attributo `pause` (in secondi)

## Requisiti degli Sfondi
- Usare immagini con contrasto sufficiente per il testo in overlay
- Evitare pattern troppo complessi che potrebbero rendere il testo illeggibile
- Preferire immagini con aree libere al centro per il posizionamento del testo