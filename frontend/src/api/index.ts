const BASE = "/api";

export interface DownloadItem {
  id: number;
  url: string;
  title?: string;
  artist?: string;
  album?: string;
  status: string;
  progress: number;
  phase?: string;
  error?: string;
  format: string;
  output_path?: string;
  cover_url?: string;
  provider?: string;
}

export interface SearchResult {
  id: string;
  title: string;
  artist?: string;
  album?: string;
  duration?: string;
  type: string;
  url: string;
  thumbnail?: string;
  year?: string;
  track_count?: number;
  track_number?: number;
  disc_number?: number;
  spotify_metadata?: boolean;
}

export interface PreviewResult {
  id: string;
  title: string;
  artist?: string;
  album?: string;
  duration?: string;
  type: string;
  url: string;
  thumbnail?: string;
  year?: string;
  track_count?: number;
}

export interface Settings {
  default_format: string;
  default_quality: string;
  default_cover_option: string;
  default_lyrics_option: string;
  download_concurrency: string;
  low_power_mode: boolean;
  ffmpeg_threads: string;
  max_search_results: string;
}

export async function getHealth(): Promise<{ status: string }> {
  const res = await fetch(`${BASE}/health`);
  return res.json();
}

export async function listDownloads(): Promise<DownloadItem[]> {
  const res = await fetch(`${BASE}/downloads`);
  if (!res.ok) return [];
  return res.json();
}

export async function createDownload(
  url: string,
  opts?: { title?: string; artist?: string; album?: string; format?: string; quality?: string; cover_option?: string; lyrics_option?: string },
): Promise<DownloadItem> {
  const res = await fetch(`${BASE}/downloads`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url, ...opts }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export async function deleteDownload(id: number): Promise<void> {
  await fetch(`${BASE}/downloads/${id}`, { method: "DELETE" });
}

export async function retryDownload(id: number): Promise<void> {
  await fetch(`${BASE}/downloads/${id}/retry`, { method: "POST" });
}

export async function searchMusic(
  q: string,
  type: string = "song",
  limit: number = 20,
): Promise<SearchResult[]> {
  const params = new URLSearchParams({ q, type, limit: String(limit) });
  const res = await fetch(`${BASE}/search?${params}`);
  if (!res.ok) return [];
  return res.json();
}

export async function previewUrl(url: string): Promise<PreviewResult | null> {
  const params = new URLSearchParams({ url });
  const res = await fetch(`${BASE}/preview?${params}`);
  if (!res.ok) return null;
  return res.json();
}

export interface LibraryItem {
  path: string;
  size: number;
  title: string;
  artist: string;
  album: string;
  duration: number | null;
  format: string;
}

export async function scanLibrary(): Promise<LibraryItem[]> {
  const res = await fetch(`${BASE}/library`);
  if (!res.ok) return [];
  return res.json();
}

export function streamUrl(path: string): string {
  return `${BASE}/library/stream?path=${encodeURIComponent(path)}`;
}

export interface PlaylistItem {
  id: number;
  video_id: string;
  title: string;
  artist: string;
  output_path: string | null;
  synced_at: string;
}

export interface PlaylistInfo {
  id: number;
  name: string;
  url: string;
  format: string;
  last_sync: string | null;
  created_at: string;
}

export async function listPlaylists(): Promise<PlaylistInfo[]> {
  const res = await fetch(`${BASE}/playlists`);
  if (!res.ok) return [];
  return res.json();
}

export async function createPlaylist(name: string, url: string, format: string = "mp3"): Promise<PlaylistInfo> {
  const res = await fetch(`${BASE}/playlists`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, url, format }),
  });
  return res.json();
}

export async function deletePlaylist(id: number): Promise<void> {
  await fetch(`${BASE}/playlists/${id}`, { method: "DELETE" });
}

export async function getPlaylistItems(id: number): Promise<PlaylistItem[]> {
  const res = await fetch(`${BASE}/playlists/${id}/items`);
  if (!res.ok) return [];
  return res.json();
}

export async function syncPlaylist(id: number): Promise<{ total_remote: number; already_synced: number; new_queued: number }> {
  const res = await fetch(`${BASE}/playlists/${id}/sync`, { method: "POST" });
  return res.json();
}
