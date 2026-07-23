import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import PageHead from "../components/PageHead";
import { api } from "../api/client";
import { tl, sayi } from "../utils/format";

const BOS_FILTRE = {
  ilce: "",
  mahalle: "",
  oda_sayisi: "",
  min_fiyat: "",
  max_fiyat: "",
  min_m2: "",
  max_m2: "",
  min_banyo: "",
  max_bina_yasi: "",
  isitma_tipi: "",
  kullanim_durumu: "",
  esyali: "",
  cephe: "",
};
const SAYFA_BOYUTU = 24;

// Piyasa durumu -> kart uzerindeki onizleme rozeti (simge + etiket + renk sinifi)
const PIYASA = {
  uygun: { simge: "▼", etiket: "Piyasa altı" },
  normal: { simge: "≈", etiket: "Piyasa değerinde" },
  pahali: { simge: "▲", etiket: "Piyasa üstü" },
};

// Piyasa durumu filtresi secenekleri (siralamanin yaninda)
const PIYASA_FILTRE = [
  { deger: "", etiket: "Tümü" },
  { deger: "uygun", etiket: "Piyasa altı" },
  { deger: "normal", etiket: "Piyasa değerinde" },
  { deger: "pahali", etiket: "Piyasa üstü" },
];

function sorgu(filtre, sirala, piyasa, skip) {
  const p = new URLSearchParams();
  for (const [k, v] of Object.entries(filtre)) {
    if (v !== "" && v != null) p.set(k, v);
  }
  if (sirala) p.set("sirala", sirala);
  if (piyasa) p.set("piyasa", piyasa);
  p.set("skip", skip);
  p.set("limit", SAYFA_BOYUTU);
  return "?" + p.toString();
}

export default function Ilanlar() {
  const [secenekler, setSecenekler] = useState(null); // degerleme secenekleri (ilce/mahalle/oda)
  const [filtreSec, setFiltreSec] = useState(null); // ilan filtre secenekleri (isitma/kullanim/cephe/sirala)
  const [filtre, setFiltre] = useState(BOS_FILTRE);
  const [sirala, setSirala] = useState("en_yeni");
  const [piyasa, setPiyasa] = useState(""); // piyasa durumu filtresi (uygun/normal/pahali)
  const [ilanlar, setIlanlar] = useState([]);
  const [toplam, setToplam] = useState(0);
  const [skip, setSkip] = useState(0);
  const [yukleniyor, setYukleniyor] = useState(true);
  const [hata, setHata] = useState("");

  useEffect(() => {
    api.degerlemeSecenekleri().then(setSecenekler).catch(() => {});
    api.ilanFiltreSecenekleri().then(setFiltreSec).catch(() => {});
    yukle(BOS_FILTRE, "en_yeni", "", 0);
  }, []);

  const yukle = async (f, s, pi, yeniSkip) => {
    setYukleniyor(true);
    setHata("");
    try {
      const veri = await api.ilanlar(sorgu(f, s, pi, yeniSkip));
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

  // Ilce degisince o ilceye ait olmayan mahalle secimini sifirla.
  const ilceGuncelle = (e) =>
    setFiltre((o) => ({ ...o, ilce: e.target.value, mahalle: "" }));

  const siralaGuncelle = (e) => {
    const s = e.target.value;
    setSirala(s);
    yukle(filtre, s, piyasa, 0); // siralama degisince ilk sayfadan yeniden yukle
  };

  const piyasaGuncelle = (e) => {
    const pi = e.target.value;
    setPiyasa(pi);
    yukle(filtre, sirala, pi, 0); // piyasa filtresi degisince ilk sayfaya don
  };

  const filtrele = (e) => {
    e.preventDefault();
    yukle(filtre, sirala, piyasa, 0); // filtre degisince ilk sayfaya don
  };

  const temizle = () => {
    setFiltre(BOS_FILTRE);
    setSirala("en_yeni");
    setPiyasa("");
    yukle(BOS_FILTRE, "en_yeni", "", 0);
  };

  const mahalleler =
    (secenekler?.mahalle_by_ilce && filtre.ilce
      ? secenekler.mahalle_by_ilce[filtre.ilce]
      : null) || [];

  const sayfa = Math.floor(skip / SAYFA_BOYUTU) + 1;
  const toplamSayfa = Math.max(1, Math.ceil(toplam / SAYFA_BOYUTU));
  const ilk = toplam === 0 ? 0 : skip + 1;
  const son = Math.min(skip + ilanlar.length, toplam);

  return (
    <>
      <PageHead
        eyebrow="İlanlar"
        baslik="İstanbul konut ilanları"
        aciklama="Konum, fiyat, metrekare, oda, ısınma ve daha fazlasına göre filtrele; sonuçları fiyata veya tarihe göre sırala. Her kartta ilanın piyasaya göre durumu daha tıklamadan önizlenir."
      />

      <form className="filters filters-genis" onSubmit={filtrele}>
        <div className="field">
          <label>İlçe</label>
          <select value={filtre.ilce} onChange={ilceGuncelle}>
            <option value="">Tümü</option>
            {secenekler?.ilce.map((v) => (
              <option key={v} value={v}>
                {v}
              </option>
            ))}
          </select>
        </div>
        <div className="field">
          <label>Mahalle</label>
          <select
            value={filtre.mahalle}
            onChange={guncelle("mahalle")}
            disabled={!filtre.ilce}
          >
            <option value="">Tümü</option>
            {mahalleler.map((v) => (
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
          <label>Isınma</label>
          <select value={filtre.isitma_tipi} onChange={guncelle("isitma_tipi")}>
            <option value="">Tümü</option>
            {filtreSec?.isitma_tipi.map((o) => (
              <option key={o.deger} value={o.deger}>
                {o.etiket}
              </option>
            ))}
          </select>
        </div>
        <div className="field">
          <label>Kullanım durumu</label>
          <select
            value={filtre.kullanim_durumu}
            onChange={guncelle("kullanim_durumu")}
          >
            <option value="">Tümü</option>
            {filtreSec?.kullanim_durumu.map((o) => (
              <option key={o.deger} value={o.deger}>
                {o.etiket}
              </option>
            ))}
          </select>
        </div>
        <div className="field">
          <label>Eşya durumu</label>
          <select value={filtre.esyali} onChange={guncelle("esyali")}>
            <option value="">Tümü</option>
            <option value="true">Eşyalı</option>
            <option value="false">Eşyasız</option>
          </select>
        </div>
        <div className="field">
          <label>Cephe</label>
          <select value={filtre.cephe} onChange={guncelle("cephe")}>
            <option value="">Farketmez</option>
            {filtreSec?.cephe.map((o) => (
              <option key={o.deger} value={o.deger}>
                {o.etiket}
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
        <div className="field">
          <label>Min. m²</label>
          <input
            type="number"
            min="0"
            value={filtre.min_m2}
            onChange={guncelle("min_m2")}
            placeholder="m²"
          />
        </div>
        <div className="field">
          <label>Maks. m²</label>
          <input
            type="number"
            min="0"
            value={filtre.max_m2}
            onChange={guncelle("max_m2")}
            placeholder="m²"
          />
        </div>
        <div className="field">
          <label>Min. banyo</label>
          <input
            type="number"
            min="0"
            value={filtre.min_banyo}
            onChange={guncelle("min_banyo")}
            placeholder="adet"
          />
        </div>
        <div className="field">
          <label>Maks. bina yaşı</label>
          <input
            type="number"
            min="0"
            value={filtre.max_bina_yasi}
            onChange={guncelle("max_bina_yasi")}
            placeholder="yaş"
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

      {/* Siralama + piyasa durumu filtresi: her zaman gorunur (piyasa filtresi
          0 sonuc dondururse kullanici filtreyi geri alabilsin) */}
      <div className="liste-kontrol">
        <div className="field sirala">
          <label>Piyasa durumu</label>
          <select value={piyasa} onChange={piyasaGuncelle}>
            {PIYASA_FILTRE.map((o) => (
              <option key={o.deger} value={o.deger}>
                {o.etiket}
              </option>
            ))}
          </select>
        </div>
        <div className="field sirala">
          <label>Sırala</label>
          <select value={sirala} onChange={siralaGuncelle}>
            {(filtreSec?.sirala || [{ deger: "en_yeni", etiket: "En yeni" }]).map(
              (o) => (
                <option key={o.deger} value={o.deger}>
                  {o.etiket}
                </option>
              )
            )}
          </select>
        </div>
      </div>

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
              onClick={() =>
                yukle(filtre, sirala, piyasa, Math.max(0, skip - SAYFA_BOYUTU))
              }
            >
              ‹ Önceki
            </button>
            <span className="sayfa-bilgi">
              Sayfa {sayfa} / {toplamSayfa}
            </span>
            <button
              className="btn btn-ghost"
              disabled={sayfa >= toplamSayfa}
              onClick={() => yukle(filtre, sirala, piyasa, skip + SAYFA_BOYUTU)}
            >
              Sonraki ›
            </button>
          </div>
        </>
      )}
    </>
  );
}
