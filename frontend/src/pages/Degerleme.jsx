import { useEffect, useMemo, useState } from "react";
import PageHead from "../components/PageHead";
import { api } from "../api/client";
import { tl, sayi, YORUM_ETIKET } from "../utils/format";

const BASLANGIC = {
  ilce: "",
  mahalle: "",
  brut_m2: "",
  net_m2: "",
  oda_sayisi: "",
  banyo_sayisi: "1",
  bina_yasi: "",
  bulundugu_kat: "",
  kat_sayisi: "",
  isinma: "",
  cephe: "",
  esya_durumu: "",
  aidat: "",
  beklenen_fiyat: "",
};

// Modele gonderilirken sayisal alanlar int'e cevrilir, bos kategorikler atlanir.
const SAYISAL = [
  "brut_m2",
  "net_m2",
  "banyo_sayisi",
  "bina_yasi",
  "kat_sayisi",
  "aidat",
  "beklenen_fiyat",
];

function istegeCevir(form) {
  const govde = {};
  for (const [k, v] of Object.entries(form)) {
    if (v === "" || v == null) continue;
    govde[k] = SAYISAL.includes(k) ? Number(v) : v;
  }
  return govde;
}

export default function Degerleme() {
  const [secenekler, setSecenekler] = useState(null);
  const [form, setForm] = useState(BASLANGIC);
  const [sonuc, setSonuc] = useState(null);
  const [yukleniyor, setYukleniyor] = useState(false);
  const [hata, setHata] = useState("");

  useEffect(() => {
    api
      .degerlemeSecenekleri()
      .then(setSecenekler)
      .catch((e) => setHata("Seçenekler yüklenemedi: " + e.message));
  }, []);

  // Secili ilceye gore mahalle listesi
  const mahalleler = useMemo(() => {
    if (!secenekler || !form.ilce) return [];
    return secenekler.mahalle_by_ilce?.[form.ilce] || [];
  }, [secenekler, form.ilce]);

  const guncelle = (alan) => (e) => {
    const deger = e.target.value;
    setForm((o) => {
      const yeni = { ...o, [alan]: deger };
      if (alan === "ilce") yeni.mahalle = ""; // ilce degisince mahalle sifirla
      return yeni;
    });
  };

  const gonder = async (e) => {
    e.preventDefault();
    setHata("");
    setYukleniyor(true);
    setSonuc(null);
    try {
      const yanit = await api.degerlemeYap(istegeCevir(form));
      setSonuc(yanit);
    } catch (err) {
      setHata("Tahmin alınamadı: " + err.message);
    } finally {
      setYukleniyor(false);
    }
  };

  if (!secenekler && !hata) {
    return (
      <>
        <PageHead eyebrow="Piyasa Değerleme" baslik="Evinin değerini öğren" />
        <p className="muted">Yükleniyor…</p>
      </>
    );
  }

  return (
    <>
      <PageHead
        eyebrow="Piyasa Değerleme"
        baslik="Evinin değerini öğren"
        aciklama="Evin özelliklerini gir; model benzer İstanbul ilanlarına göre tahmini piyasa değerini üretsin."
      />

      <div className="two-col">
        <form className="card" onSubmit={gonder}>
          <div className="form-grid">
            <Alan label="İlçe *">
              <select value={form.ilce} onChange={guncelle("ilce")} required>
                <option value="">Seçin</option>
                {secenekler?.ilce.map((v) => (
                  <option key={v} value={v}>
                    {v}
                  </option>
                ))}
              </select>
            </Alan>

            <Alan label="Mahalle">
              <select
                value={form.mahalle}
                onChange={guncelle("mahalle")}
                disabled={!form.ilce}
              >
                <option value="">{form.ilce ? "Seçin" : "Önce ilçe"}</option>
                {mahalleler.map((v) => (
                  <option key={v} value={v}>
                    {v}
                  </option>
                ))}
              </select>
            </Alan>

            <Alan label="Oda sayısı">
              <select value={form.oda_sayisi} onChange={guncelle("oda_sayisi")}>
                <option value="">Seçin</option>
                {secenekler?.oda_sayisi.map((v) => (
                  <option key={v} value={v}>
                    {v}
                  </option>
                ))}
              </select>
            </Alan>

            <Alan label="Brüt m² *">
              <input
                type="number"
                min="1"
                value={form.brut_m2}
                onChange={guncelle("brut_m2")}
                required
                placeholder="120"
              />
            </Alan>

            <Alan label="Net m²">
              <input
                type="number"
                min="0"
                value={form.net_m2}
                onChange={guncelle("net_m2")}
                placeholder="100"
              />
            </Alan>

            <Alan label="Bina yaşı">
              <input
                type="number"
                min="0"
                value={form.bina_yasi}
                onChange={guncelle("bina_yasi")}
                placeholder="10"
              />
            </Alan>

            <Alan label="Banyo sayısı">
              <input
                type="number"
                min="0"
                value={form.banyo_sayisi}
                onChange={guncelle("banyo_sayisi")}
              />
            </Alan>

            <Alan label="Kat sayısı">
              <input
                type="number"
                min="0"
                value={form.kat_sayisi}
                onChange={guncelle("kat_sayisi")}
                placeholder="5"
              />
            </Alan>

            <Alan label="Bulunduğu kat">
              <select
                value={form.bulundugu_kat}
                onChange={guncelle("bulundugu_kat")}
              >
                <option value="">Seçin</option>
                {secenekler?.bulundugu_kat.map((v) => (
                  <option key={v} value={v}>
                    {v}
                  </option>
                ))}
              </select>
            </Alan>

            <Alan label="Isıtma">
              <select value={form.isinma} onChange={guncelle("isinma")}>
                <option value="">Seçin</option>
                {secenekler?.isinma.map((v) => (
                  <option key={v} value={v}>
                    {v}
                  </option>
                ))}
              </select>
            </Alan>

            <Alan label="Cephe">
              <select value={form.cephe} onChange={guncelle("cephe")}>
                <option value="">Seçin</option>
                {secenekler?.cephe.map((v) => (
                  <option key={v} value={v}>
                    {v}
                  </option>
                ))}
              </select>
            </Alan>

            <Alan label="Eşya durumu">
              <select
                value={form.esya_durumu}
                onChange={guncelle("esya_durumu")}
              >
                <option value="">Seçin</option>
                {secenekler?.esya_durumu.map((v) => (
                  <option key={v} value={v}>
                    {v}
                  </option>
                ))}
              </select>
            </Alan>

            <Alan label="Aidat (TL)">
              <input
                type="number"
                min="0"
                value={form.aidat}
                onChange={guncelle("aidat")}
                placeholder="1500"
              />
            </Alan>

            <Alan label="Beklenen fiyat (TL)" hint="Girersen piyasayla karşılaştırırız">
              <input
                type="number"
                min="1"
                value={form.beklenen_fiyat}
                onChange={guncelle("beklenen_fiyat")}
                placeholder="opsiyonel"
              />
            </Alan>
          </div>

          <div className="form-actions">
            <button className="btn btn-primary" disabled={yukleniyor}>
              {yukleniyor ? "Hesaplanıyor…" : "Değerle"}
            </button>
            {hata && <span className="form-error">{hata}</span>}
          </div>
        </form>

        <div>
          {sonuc ? (
            <Sonuc sonuc={sonuc} />
          ) : (
            <div className="placeholder" style={{ padding: "40px 20px" }}>
              <strong>Sonuç burada</strong>
              Formu doldurup “Değerle”ye bas.
            </div>
          )}
        </div>
      </div>
    </>
  );
}

function Alan({ label, hint, children }) {
  return (
    <div className="field">
      <label>{label}</label>
      {children}
      {hint && <span className="hint">{hint}</span>}
    </div>
  );
}

function Sonuc({ sonuc }) {
  const hataPayi = Math.round((sonuc.tahmin_hata_payi || 0) * 100);
  return (
    <div className="result">
      <div className="etiket">Tahmini piyasa değeri</div>
      <div className="fiyat">{tl(sonuc.tahmini_fiyat)}</div>
      <div className="aralik">
        {tl(sonuc.fiyat_araligi.alt)} – {tl(sonuc.fiyat_araligi.ust)} aralığında
      </div>

      {sonuc.yorum && (
        <div className="yorum-box">
          <span className={`badge ${sonuc.yorum.durum}`}>
            {YORUM_ETIKET[sonuc.yorum.durum]}
          </span>
          <p>{sonuc.yorum.mesaj}</p>
        </div>
      )}

      <div className="result-meta">
        <div className="metric">
          <div className="k">Birim m² fiyatı</div>
          <div className="v">{tl(sonuc.birim_m2_fiyat)}</div>
        </div>
        <div className="metric">
          <div className="k">Tahmin hata payı</div>
          <div className="v">±%{hataPayi}</div>
        </div>
      </div>
    </div>
  );
}
