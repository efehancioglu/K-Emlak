import { useEffect, useState } from "react";
import PageHead from "../components/PageHead";
import { api } from "../api/client";
import { tl, sayi, YORUM_ETIKET } from "../utils/format";

const SAYFA_BOYUTU = 50;

// yorum_durum -> rozet sinifi + etiket (Degerleme/Ilanlar ile ayni dil)
const DURUM = {
  uygun: { simge: "▼", etiket: YORUM_ETIKET.uygun },
  normal: { simge: "≈", etiket: YORUM_ETIKET.normal },
  pahali: { simge: "▲", etiket: YORUM_ETIKET.pahali },
};

const tarihBicim = new Intl.DateTimeFormat("tr-TR", {
  day: "2-digit",
  month: "short",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
});

const tarih = (s) => {
  try {
    return tarihBicim.format(new Date(s));
  } catch {
    return s;
  }
};

export default function Gecmis() {
  const [kayitlar, setKayitlar] = useState([]);
  const [skip, setSkip] = useState(0);
  const [yukleniyor, setYukleniyor] = useState(true);
  const [hata, setHata] = useState("");

  const yukle = async (yeniSkip) => {
    setYukleniyor(true);
    setHata("");
    try {
      const p = new URLSearchParams();
      p.set("skip", yeniSkip);
      p.set("limit", SAYFA_BOYUTU);
      const veri = await api.degerlemeGecmisi("?" + p.toString());
      setKayitlar(veri);
      setSkip(yeniSkip);
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (e) {
      setHata("Geçmiş yüklenemedi: " + e.message);
    } finally {
      setYukleniyor(false);
    }
  };

  useEffect(() => {
    yukle(0);
  }, []);

  const sayfa = Math.floor(skip / SAYFA_BOYUTU) + 1;
  // Toplam sayi ucu yok; tam sayfa geldiyse sonraki olabilir varsayimi.
  const sonrakiVar = kayitlar.length === SAYFA_BOYUTU;

  return (
    <>
      <PageHead
        eyebrow="Geçmiş"
        baslik="Yapılan değerlemeler"
        aciklama="Daha önce yaptığın tüm değerlemeler burada; ne zaman, hangi ev için ne tahmin çıkmış ve girdiğin fiyata göre nasıl yorumlandığını görebilirsin."
      />

      {hata && <p className="form-error">{hata}</p>}

      {yukleniyor ? (
        <p className="muted">Yükleniyor…</p>
      ) : kayitlar.length === 0 ? (
        <div className="placeholder">
          <strong>Kayıt yok</strong>
          Henüz bir değerleme yapılmamış. Değerleme ekranından bir tahmin
          oluşturunca burada listelenir.
        </div>
      ) : (
        <>
          <div className="gecmis-liste">
            {kayitlar.map((k) => {
              const d = k.yorum_durum ? DURUM[k.yorum_durum] : null;
              return (
                <div
                  key={k.id}
                  className={`gecmis-kart${
                    k.yorum_durum ? " durum-" + k.yorum_durum : ""
                  }`}
                >
                  <div className="gecmis-ust">
                    <div className="konum">
                      {k.ilce}
                      {k.mahalle ? ` · ${k.mahalle}` : ""}
                    </div>
                    <div className="gecmis-tarih">{tarih(k.olusturulma_tarihi)}</div>
                  </div>

                  <div className="gecmis-orta">
                    <div className="gecmis-tahmin">
                      <span className="etiket">Tahmini değer</span>
                      <span className="deger">{tl(k.tahmini_fiyat)}</span>
                      <span className="aralik">
                        {tl(k.fiyat_alt)} – {tl(k.fiyat_ust)}
                      </span>
                    </div>
                    {d && (
                      <span className={`piyasa-rozet ${k.yorum_durum}`}>
                        <span className="simge">{d.simge}</span>
                        {d.etiket}
                      </span>
                    )}
                  </div>

                  <div className="gecmis-ozet">
                    <span className="chip">{k.oda_sayisi || "—"}</span>
                    <span className="chip">{k.brut_m2} m²</span>
                    <span className="chip">{tl(k.birim_m2_fiyat)}/m²</span>
                    {k.beklenen_fiyat != null && (
                      <span className="chip">
                        Girilen fiyat: {tl(k.beklenen_fiyat)}
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          <div className="pagination">
            <button
              className="btn btn-ghost"
              disabled={skip === 0}
              onClick={() => yukle(Math.max(0, skip - SAYFA_BOYUTU))}
            >
              ‹ Önceki
            </button>
            <span className="sayfa-bilgi">Sayfa {sayfa}</span>
            <button
              className="btn btn-ghost"
              disabled={!sonrakiVar}
              onClick={() => yukle(skip + SAYFA_BOYUTU)}
            >
              Sonraki ›
            </button>
          </div>
        </>
      )}
    </>
  );
}
