import { useEffect, useState } from "react";
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

export default function Yonetim() {
  const [ozet, setOzet] = useState(null);
  const [ilceler, setIlceler] = useState([]);
  const [trend, setTrend] = useState([]);
  const [hata, setHata] = useState("");
  const [yukleniyor, setYukleniyor] = useState(true);

  useEffect(() => {
    Promise.all([
      api.ozetIstatistik(),
      api.ilceIstatistik(),
      api.fiyatTrendi(),
    ])
      .then(([o, il, tr]) => {
        setOzet(o);
        setIlceler(il);
        setTrend(tr);
      })
      .catch((e) => setHata("Veriler yüklenemedi: " + e.message))
      .finally(() => setYukleniyor(false));
  }, []);

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
