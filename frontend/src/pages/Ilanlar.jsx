import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import PageHead from "../components/PageHead";
import { api } from "../api/client";
import { tl, sayi } from "../utils/format";

const BOS_FILTRE = { ilce: "", oda_sayisi: "", min_fiyat: "", max_fiyat: "" };
const SAYFA_BOYUTU = 24;

// Piyasa durumu -> kart uzerindeki onizleme rozeti (simge + etiket + renk sinifi)
const PIYASA = {
  uygun: { simge: "▼", etiket: "Piyasa altı" },
  normal: { simge: "≈", etiket: "Piyasa değerinde" },
  pahali: { simge: "▲", etiket: "Piyasa üstü" },
};

function sorgu(filtre, skip) {
  const p = new URLSearchParams();
  for (const [k, v] of Object.entries(filtre)) {
    if (v !== "" && v != null) p.set(k, v);
  }
  p.set("skip", skip);
  p.set("limit", SAYFA_BOYUTU);
  return "?" + p.toString();
}

export default function Ilanlar() {
  const [secenekler, setSecenekler] = useState(null);
  const [filtre, setFiltre] = useState(BOS_FILTRE);
  const [ilanlar, setIlanlar] = useState([]);
  const [toplam, setToplam] = useState(0);
  const [skip, setSkip] = useState(0);
  const [yukleniyor, setYukleniyor] = useState(true);
  const [hata, setHata] = useState("");

  useEffect(() => {
    api.degerlemeSecenekleri().then(setSecenekler).catch(() => {});
    yukle(BOS_FILTRE, 0);
  }, []);

  const yukle = async (f, yeniSkip) => {
    setYukleniyor(true);
    setHata("");
    try {
      const veri = await api.ilanlar(sorgu(f, yeniSkip));
      setIlanlar(veri.items);
      setToplam(veri.toplam);
      setSkip(veri.skip);
      window.scrollTo({ top: 0, behavior: "smooth" });
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
    yukle(filtre, 0); // filtre degisince ilk sayfaya don
  };

  const temizle = () => {
    setFiltre(BOS_FILTRE);
    yukle(BOS_FILTRE, 0);
  };

  const sayfa = Math.floor(skip / SAYFA_BOYUTU) + 1;
  const toplamSayfa = Math.max(1, Math.ceil(toplam / SAYFA_BOYUTU));
  const ilk = toplam === 0 ? 0 : skip + 1;
  const son = Math.min(skip + ilanlar.length, toplam);

  return (
    <>
      <PageHead
        eyebrow="İlanlar"
        baslik="İstanbul konut ilanları"
        aciklama="İlçe, fiyat ve oda sayısına göre filtrele. Her kartta, ilanın piyasaya göre durumu daha tıklamadan önizlenir."
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
          <div className="list-info">
            <strong>{sayi(toplam)}</strong> ilandan{" "}
            <strong>
              {ilk}–{son}
            </strong>{" "}
            arası gösteriliyor
          </div>

          <div className="listing-grid">
            {ilanlar.map((il) => {
              const p = il.piyasa ? PIYASA[il.piyasa.durum] : null;
              return (
                <Link
                  key={il.id}
                  to={`/ilanlar/${il.id}`}
                  className={`listing-card${
                    il.piyasa ? " durum-" + il.piyasa.durum : ""
                  }`}
                >
                  {p && (
                    <span
                      className={`piyasa-rozet ${il.piyasa.durum}`}
                      title={`Tahmini piyasa değeri: ${tl(
                        il.piyasa.tahmini_fiyat
                      )}`}
                    >
                      <span className="simge">{p.simge}</span>
                      {p.etiket}
                    </span>
                  )}
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
              );
            })}
          </div>

          <div className="pagination">
            <button
              className="btn btn-ghost"
              disabled={skip === 0}
              onClick={() => yukle(filtre, Math.max(0, skip - SAYFA_BOYUTU))}
            >
              ‹ Önceki
            </button>
            <span className="sayfa-bilgi">
              Sayfa {sayfa} / {toplamSayfa}
            </span>
            <button
              className="btn btn-ghost"
              disabled={sayfa >= toplamSayfa}
              onClick={() => yukle(filtre, skip + SAYFA_BOYUTU)}
            >
              Sonraki ›
            </button>
          </div>
        </>
      )}
    </>
  );
}
