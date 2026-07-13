# DownTube

Self-hosted music downloader & library manager. Download audio from YouTube, YouTube Music, and Spotify with rich metadata tagging.

## Fitur

- **Smart Search** — Cari lagu, album, artis dari YouTube Music. Paste URL (YouTube/Spotify) untuk preview sebelum download.
- **Download & Tagging** — Audio di-download via yt-dlp, di-transcode ke format pilihan (mp3/opus/m4a/flac), lalu di-tag dengan metadata lengkap (judul, artis, album, cover art, lirik).
- **Spotify Integration** — Metadata dari Spotify (album, cover, tahun, nomor trek) digabung dengan audio dari YouTube Music.
- **Playlist Management** — Buat playlist, tambah lagu, sinkronisasi dari YouTube Music.
- **Real-time Progress** — Progress download ditampilkan via Server-Sent Events (SSE).
- **Dark/Light Mode** — Toggle tema di halaman Pengaturan.
- **Responsive** — Desktop sidebar, mobile hamburger menu.

## Tech Stack

| Layer | Tech |
|---|---|
| Backend | Python 3.11, FastAPI, SQLAlchemy + SQLite, yt-dlp, mutagen |
| Frontend | Vue 3, Vite 5, Tailwind CSS 3, TypeScript |
| Audio | yt-dlp (download), ffmpeg (transcode), mutagen (tagging) |
| Metadata | YouTube Music API, Spotify API (Client Credentials) |
| Deploy | Docker, CasaOS |

## Quick Start

### Docker (Recommended)

```bash
docker build -f docker/Dockerfile -t downtube .
docker run -p 9876:9876 \
  -e MUSIC_ROOT=/app/music \
  -e DATA_DIR=/app/data \
  -e DATABASE_URL=sqlite+aiosqlite:////app/data/downtube.db \
  downtube
```

Buka `http://localhost:9876`

### Docker Compose

```bash
docker compose up -d
```

### CasaOS

1. Buka CasaOS → Custom Install
2. Image: `ghcr.io/haanzx/downtube:latest`
3. Port: `9876`
4. Volumes:
   - `/DATA/AppData/downtube` → `/app/data`
   - `/DATA/Music/downtube` → `/app/music`
5. Install

### Local Development

**Backend:**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn downtube.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Environment Variables

| Variable | Default | Deskripsi |
|---|---|---|
| `MUSIC_ROOT` | `./music` | Direktori penyimpanan audio |
| `DATA_DIR` | `./data` | Direktori database & config |
| `DATABASE_URL` | `sqlite+aiosqlite:///./data/downtube.db` | Database connection string |
| `DOWNLOAD_CONCURRENCY` | `2` | Max download bersamaan |
| `YTDLP_PATH` | `yt-dlp` | Path ke yt-dlp |
| `FFMPEG_PATH` | `ffmpeg` | Path ke ffmpeg |
| `SPOTIFY_CLIENT_ID` | _(kosong)_ | Spotify Client ID (opsional) |
| `SPOTIFY_CLIENT_SECRET` | _(kosong)_ | Spotify Client Secret (opsional) |

## screenshots

<!-- TODO: tambahkan screenshot -->
<!-- ![Search](screenshots/search.png) -->
<!-- ![Downloads](screenshots/downloads.png) -->
<!-- ![Settings](screenshots/settings.png) -->

## License

GPL-3.0
