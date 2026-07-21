import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import PageHead from "../components/PageHead";
import { api } from "../api/client";
import { tl } from "../utils/format";

const BOS_FILTRE = { ilce: "", oda_sayisi: "", min_fiyat: "", max_fiyat: "" };

function sorgu(filtre) {
  const p = new URLSearchParams();
  for (const [k, v] of Object.entries(filtre)) {
    if (v !== "" && v != null) p.set(k, v);
  }
  const s = p.toString();
  return s ? "?" + s : "";
}

export default function Ilanlar() {
  const [secenekler, setSecenekler] = useState(null);
  const [filtre, setFiltre] = useState(BOS_FILTRE);
  const [ilanlar, setIlanlar] = useState([]);
  const [yukleniyor, setYukleniyor] = useState(true);
  const [hata, setHata] = useState("");

  useEffect(() => {
    api.degerlemeSecenekleri().then(setSecenekler).catch(() => {});
    yukle(BOS_FILTRE);
  }, []);

  const yukle = async (f) => {
    setYukleniyor(true);
    setHata("");
    try {
      const veri = await api.ilanlar(sorgu(f));
      setIlanlar(veri);
    } catch (e) {
      setHata("İlanlar yüklenemedi: " + e.message);
    } finally {
      setYukleniyor(false);
    }
  };

  const guncelle = (alan) => (e) =>
    setFiltre((o) => ({ ...o, [alan]: e.target.value }));

  const filtrele = (e) => {
    e.preventDefault();
    yukle(filtre);
  };

  const temizle = () => {
    setFiltre(BOS_FILTRE);
    yukle(BOS_FILTRE);
  };

  return (
    <>
      <PageHead
        eyebrow="İlanlar"
        baslik="İstanbul konut ilanları"
        aciklama="İlçe, fiyat ve oda sayısına göre filtrele; bir ilana tıklayıp piyasaya göre değerlendirmesini incele."
      />

      <form className="filters" onSubmit={filtrele}>
        <div className="field">
          <label>İlçe</label>
          <select value={filtre.ilce} onChange={guncelle("ilce")}>
            <option value="">Tümü</option>
            {secenekler?.ilce.map((v) => (
              <option key={v} value={v}>
                {v}
              </option>
            ))}
          </select>
        </div>
        <div className="field">
          <label>Oda sayısı</label>
          <select value={filtre.oda_sayisi} onChange={guncelle("oda_sayisi")}>
            <option value="">Tümü</option>
            {secenekler?.oda_sayisi.map((v) => (
              <option key={v} value={v}>
                {v}
              </option>
            ))}
          </select>
        </div>
        <div className="field">
          <label>Min. fiyat</label>
          <input
            type="number"
            min="0"
            value={filtre.min_fiyat}
            onChange={guncelle("min_fiyat")}
            placeholder="₺"
          />
        </div>
        <div className="field">
          <label>Maks. fiyat</label>
          <input
            type="number"
            min="0"
            value={filtre.max_fiyat}
            onChange={guncelle("max_fiyat")}
            placeholder="₺"
          />
        </div>
        <div className="field apply">
          <label>&nbsp;</label>
          <div className="row" style={{ gap: 8 }}>
            <button className="btn btn-primary" style={{ flex: 1 }}>
              Filtrele
            </button>
            <button type="button" className="btn btn-ghost" onClick={temizle}>
              Temizle
            </button>
          </div>
        </div>
      </form>

      {hata && <p className="form-error">{hata}</p>}

      {yukleniyor ? (
        <p className="muted">Yükleniyor…</p>
      ) : ilanlar.length === 0 ? (
        <div className="placeholder">
          <strong>Sonuç yok</strong>
          Bu filtrelere uyan ilan bulunamadı.
        </div>
      ) : (
        <>
          <div className="list-info">{ilanlar.length} ilan listeleniyor</div>
          <div className="listing-grid">
            {ilanlar.map((il) => (
              <Link key={il.id} to={`/ilanlar/${il.id}`} className="listing-card">
                <div className="konum">
                  {il.ilce}
                  {il.mahalle ? ` · ${il.mahalle}` : ""}
                </div>
                <div className="fiyat">{tl(il.fiyat)}</div>
                <div className="ozet">
                  <span className="chip">{il.oda_sayisi}</span>
                  <span className="chip">{il.brut_metrekare} m²</span>
                  <span className="chip">{il.bina_yasi} yaş</span>
                </div>
              </Link>
            ))}
          </div>
        </>
      )}
    </>
  );
}
