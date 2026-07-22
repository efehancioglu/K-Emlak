// Backend'e tek giris noktasi. Vite dev proxy'si /api -> localhost:8000.
const BASE = "/api";

async function istek(yol, secenekler = {}) {
  const yanit = await fetch(BASE + yol, {
    headers: { "Content-Type": "application/json" },
    ...secenekler,
  });
  if (!yanit.ok) {
    let detay = yanit.statusText;
    try {
      const govde = await yanit.json();
      detay = govde.detail || detay;
    } catch {
      /* json degilse statusText kalir */
    }
    throw new Error(detay);
  }
  return yanit.json();
}

export const api = {
  get: (yol) => istek(yol),
  post: (yol, govde) =>
    istek(yol, { method: "POST", body: JSON.stringify(govde) }),

  // Kisayollar (ekranlar bunlari kullanacak)
  degerlemeYap: (ozellikler) => api.post("/valuation/predict", ozellikler),
  degerlemeSecenekleri: () => api.get("/valuation/options"),
  degerlemeGecmisi: (params = "") => api.get("/valuation/history" + params),
  ilanlar: (params = "") => api.get("/listings/" + params),
  ilanFiltreSecenekleri: () => api.get("/listings/filtre-secenekleri"),
  ilanDetay: (id) => api.get("/listings/" + id),
  ozetIstatistik: () => api.get("/stats/summary"),
  ilceIstatistik: () => api.get("/stats/by-ilce"),
  fiyatTrendi: () => api.get("/stats/price-trend"),
  // Veri cekme kontrolu: baslat / durdur (o ana dek cekileni DB'ye kaydeder) / durum
  veriCek: () => api.post("/scraper/run"),
  veriDurdur: () => api.post("/scraper/stop"),
  veriDurum: () => api.get("/scraper/status"),
};
