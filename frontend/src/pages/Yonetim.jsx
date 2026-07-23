import { useEffect, useRef, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import PageHead from "../components/PageHead";
import { api } from "../api/client";
import { tl, sayi, kompaktTl } from "../utils/format";

const RENK = "#d62828"; // marka kirmizisi (grafik ana rengi)
const IZGARA = "#e6e2d9";
const EKSEN = "#8a938e";

const BOS_SCRAPER = { durum: "bosta", yeni_ilan: 0, ingest_ozeti: null, hata: null };

export default function Yonetim() {
  const [ozet, setOzet] = useState(null);
  const [ilceler, setIlceler] = useState([]);
  const [trend, setTrend] = useState([]);
  const [hata, setHata] = useState("");
  const [yukleniyor, setYukleniyor] = useState(true);
  const [scraper, setScraper] = useState(BOS_SCRAPER); // /scraper/status yaniti
  const [eylemHata, setEylemHata] = useState(null); // baslat/durdur hatasi
  const pollRef = useRef(null);

  const cekiliyor = scraper.durum === "cekiliyor";
  const kaydediliyor = scraper.durum === "kaydediliyor";
  const egitiliyor = scraper.durum === "egitiliyor";
  const aktif = cekiliyor || kaydediliyor || egitiliyor;

  const istatistikleriYukle = () => {
    setYukleniyor(true);
    Promise.all([api.ozetIstatistik(), api.ilceIstatistik(), api.fiyatTrendi()])
      .then(([o, il, tr]) => {
        setOzet(o);
        setIlceler(il);
        setTrend(tr);
        setHata("");
      })
      .catch((e) => setHata("Veriler yüklenemedi: " + e.message))
      .finally(() => setYukleniyor(false));
  };

  const durumCek = async () => {
    try {
      const d = await api.veriDurum();
      setScraper(d);
      return d;
    } catch {
      return null;
    }
  };

  const pollDurdur = () => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  };

  const pollBaslat = () => {
    if (pollRef.current) return;
    pollRef.current = setInterval(async () => {
      const d = await durumCek();
      // Is bittiyse (bitti/durduruldu/hata/bosta) poll'u durdur, istatistikleri tazele
      if (
        d &&
        d.durum !== "cekiliyor" &&
        d.durum !== "kaydediliyor" &&
        d.durum !== "egitiliyor"
      ) {
        pollDurdur();
        istatistikleriYukle();
      }
    }, 2000);
  };

  useEffect(() => {
    istatistikleriYukle();
    // Sayfa acildiginda devam eden bir cekme var mi kontrol et
    durumCek().then((d) => {
      if (
        d &&
        (d.durum === "cekiliyor" ||
          d.durum === "kaydediliyor" ||
          d.durum === "egitiliyor")
      ) {
        pollBaslat();
      }
    });
    return () => pollDurdur();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const veriCek = async () => {
    setEylemHata(null);
    try {
      const r = await api.veriCek();
      if (r && r.baslatildi === false) {
        setEylemHata(r.mesaj || "Zaten çalışıyor.");
      }
      await durumCek();
      pollBaslat();
    } catch (e) {
      setEylemHata("Başlatılamadı: " + e.message);
    }
  };

  const veriDurdur = async () => {
    setEylemHata(null);
    try {
      await api.veriDurdur();
      await durumCek(); // "kaydediliyor" asamasina gecer
    } catch (e) {
      setEylemHata("Durdurulamadı: " + e.message);
    }
  };

  // m2 fiyatina gore en pahali 12 ilce (grafik icin anlamli siralama)
  const enPahaliIlceler = [...ilceler]
    .sort((a, b) => b.ortalama_m2_fiyat - a.ortalama_m2_fiyat)
    .slice(0, 12);

  return (
    <>
      <PageHead
        eyebrow="Yönetim"
        baslik="Genel bakış"
        aciklama="Sistemdeki İstanbul ilanlarının özeti: toplam ilan, ilçelere göre ortalama metrekare fiyatı ve zaman içindeki fiyat değişimi."
      />

      <div className="yonetim-eylem">
        <div>
          <strong>Veri toplama</strong>
          <div className="alt">
            Hepsiemlak'tan güncel İstanbul ilanlarını çeker. İstediğin an
            durdurabilirsin; o ana kadar çekilenler veritabanına kaydedilir.
          </div>
        </div>
        <div className="row" style={{ gap: 8 }}>
          <button className="btn btn-primary" onClick={veriCek} disabled={aktif}>
            {cekiliyor
              ? "Çekiliyor…"
              : kaydediliyor
              ? "Kaydediliyor…"
              : egitiliyor
              ? "Model güncelleniyor…"
              : "Verileri şimdi çek"}
          </button>
          {cekiliyor && (
            <button className="btn btn-ghost" onClick={veriDurdur}>
              Durdur
            </button>
          )}
        </div>
      </div>

      {eylemHata && <p className="form-error">{eylemHata}</p>}
      <ScraperKutu s={scraper} />

      {hata && <p className="form-error">{hata}</p>}
      {yukleniyor ? (
        <p className="muted">Yükleniyor…</p>
      ) : (
        <>
          {ozet && (
            <div className="stat-grid">
              <StatCard k="Toplam ilan" v={sayi(ozet.toplam_ilan)} />
              <StatCard k="İlçe sayısı" v={sayi(ozet.toplam_ilce)} />
              <StatCard k="Ortalama fiyat" v={tl(ozet.ortalama_fiyat)} />
              <StatCard k="Ortalama m² fiyatı" v={tl(ozet.ortalama_m2_fiyat)} />
              <StatCard
                k="Fiyat aralığı"
                v={kompaktTl(ozet.en_dusuk_fiyat)}
                alt={`en yüksek ${kompaktTl(ozet.en_yuksek_fiyat)}`}
              />
            </div>
          )}

          <div className="chart-card">
            <h2>İlçelere göre ortalama m² fiyatı</h2>
            <div className="alt">En pahalı 12 ilçe (₺/m²)</div>
            <div className="chart-wrap">
              <ResponsiveContainer>
                <BarChart
                  data={enPahaliIlceler}
                  margin={{ top: 8, right: 12, left: 8, bottom: 60 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke={IZGARA} vertical={false} />
                  <XAxis
                    dataKey="ilce"
                    angle={-45}
                    textAnchor="end"
                    height={70}
                    tick={{ fill: EKSEN, fontSize: 12 }}
                    interval={0}
                  />
                  <YAxis
                    tickFormatter={kompaktTl}
                    tick={{ fill: EKSEN, fontSize: 12 }}
                    width={64}
                  />
                  <Tooltip
                    formatter={(v) => [tl(v), "Ort. m² fiyatı"]}
                    labelStyle={{ fontWeight: 700 }}
                  />
                  <Bar dataKey="ortalama_m2_fiyat" fill={RENK} radius={[5, 5, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="chart-card">
            <h2>Zaman içinde fiyat değişimi</h2>
            <div className="alt">Aylık ortalama ilan fiyatı</div>
            <div className="chart-wrap">
              <ResponsiveContainer>
                <LineChart
                  data={trend}
                  margin={{ top: 8, right: 16, left: 8, bottom: 8 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke={IZGARA} vertical={false} />
                  <XAxis
                    dataKey="donem"
                    tick={{ fill: EKSEN, fontSize: 12 }}
                  />
                  <YAxis
                    tickFormatter={kompaktTl}
                    tick={{ fill: EKSEN, fontSize: 12 }}
                    width={64}
                  />
                  <Tooltip
                    formatter={(v) => [tl(v), "Ort. fiyat"]}
                    labelStyle={{ fontWeight: 700 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="ortalama_fiyat"
                    stroke={RENK}
                    strokeWidth={2.5}
                    dot={{ r: 4, fill: RENK }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </>
      )}
    </>
  );
}

function StatCard({ k, v, alt }) {
  return (
    <div className="stat-card">
      <div className="k">{k}</div>
      <div className="v">{v}</div>
      {alt && <div className="alt">{alt}</div>}
    </div>
  );
}

// Veri cekme durumunu canli gosteren bilgi kutusu.
function ScraperKutu({ s }) {
  if (s.durum === "bosta") return null;

  if (s.durum === "hata") {
    return (
      <div className="scraper-kutu err">
        <strong>Bir hata oluştu.</strong>
        <div className="alt">{s.hata}</div>
      </div>
    );
  }

  if (s.durum === "cekiliyor") {
    return (
      <div className="scraper-kutu calisiyor">
        <span className="nabiz" />
        <div className="scraper-metin">
          <div className="scraper-baslik">Veri çekiliyor…</div>
          <div className="alt">
            Şu ana kadar <strong>{sayi(s.yeni_ilan)}</strong> yeni ilan bulundu.
            Yeterince topladığını düşününce “Durdur”a basabilirsin.
          </div>
        </div>
      </div>
    );
  }

  if (s.durum === "kaydediliyor") {
    return (
      <div className="scraper-kutu calisiyor">
        <span className="nabiz" />
        <div className="scraper-metin">
          <div className="scraper-baslik">Veritabanına kaydediliyor…</div>
          <div className="alt">
            Çekme durdu; bu koşuda bulunan <strong>{sayi(s.yeni_ilan)}</strong>{" "}
            ilan veritabanına işleniyor.
          </div>
        </div>
      </div>
    );
  }

  if (s.durum === "egitiliyor") {
    return (
      <div className="scraper-kutu calisiyor">
        <span className="nabiz" />
        <div className="scraper-metin">
          <div className="scraper-baslik">Model güncelleniyor…</div>
          <div className="alt">
            Yeni ilanlar kaydedildi; tahmin modeli güncel veriyle yeniden
            eğitiliyor. Birkaç saniye sürebilir.
          </div>
        </div>
      </div>
    );
  }

  // bitti | durduruldu
  const oz = s.ingest_ozeti || {};
  return (
    <div className="scraper-kutu bitti">
      <div className="scraper-metin">
        <div className="scraper-baslik">
          {s.durum === "durduruldu" ? "Durduruldu ✓" : "Tamamlandı ✓"}
        </div>
        <div className="alt">
          Bu koşuda <strong>{sayi(s.yeni_ilan)}</strong> ilan çekildi.
          Veritabanına <strong>{sayi(oz.eklenen || 0)}</strong> yeni ilan
          eklendi{oz.zaten_var ? `, ${sayi(oz.zaten_var)} tanesi zaten kayıtlıydı` : ""}.
          Tahmin modeli güncel veriyle yeniden eğitildi.
        </div>
      </div>
    </div>
  );
}
