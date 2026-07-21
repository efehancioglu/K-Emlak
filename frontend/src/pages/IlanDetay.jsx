import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import PageHead from "../components/PageHead";
import { api } from "../api/client";
import { tl, YORUM_ETIKET } from "../utils/format";

function cepheMetni(il) {
  const yon = [];
  if (il.cephe_kuzey) yon.push("Kuzey");
  if (il.cephe_guney) yon.push("Güney");
  if (il.cephe_dogu) yon.push("Doğu");
  if (il.cephe_bati) yon.push("Batı");
  return yon.join(", ") || "—";
}

export default function IlanDetay() {
  const { id } = useParams();
  const [ilan, setIlan] = useState(null);
  const [hata, setHata] = useState("");

  useEffect(() => {
    setIlan(null);
    setHata("");
    api
      .ilanDetay(id)
      .then(setIlan)
      .catch((e) => setHata(e.message));
  }, [id]);

  return (
    <>
      <Link to="/ilanlar" className="muted" style={{ fontSize: "0.9rem" }}>
        ← İlanlara dön
      </Link>
      <div style={{ height: 12 }} />

      {hata ? (
        <div className="placeholder">
          <strong>İlan bulunamadı</strong>
          {hata}
        </div>
      ) : !ilan ? (
        <p className="muted">Yükleniyor…</p>
      ) : (
        <>
          <PageHead
            eyebrow={`İlan #${ilan.id}`}
            baslik={`${ilan.ilce}${ilan.mahalle ? " · " + ilan.mahalle : ""}`}
          />

          <div className="two-col">
            <div className="card">
              <h2 style={{ marginBottom: 16 }}>İlan bilgileri</h2>
              <div className="detail-grid">
                <Satir k="İlan fiyatı" v={tl(ilan.fiyat)} />
                <Satir k="Oda sayısı" v={ilan.oda_sayisi} />
                <Satir k="Brüt / Net m²" v={`${ilan.brut_metrekare} / ${ilan.net_metrekare}`} />
                <Satir k="Bina yaşı" v={`${ilan.bina_yasi}`} />
                <Satir k="Bulunduğu kat" v={ilan.bulundugu_kat || "—"} />
                <Satir k="Kat sayısı" v={`${ilan.kat_sayisi}`} />
                <Satir k="Banyo sayısı" v={`${ilan.banyo_sayisi}`} />
                <Satir k="Isıtma" v={ilan.isitma_tipi} />
                <Satir k="Cephe" v={cepheMetni(ilan)} />
                <Satir k="Eşya durumu" v={ilan.esyali ? "Eşyalı" : "Eşyalı Değil"} />
                <Satir k="Kullanım" v={ilan.kullanim_durumu} />
                <Satir k="Aidat" v={ilan.aidat ? tl(ilan.aidat) : "—"} />
              </div>
              {ilan.kaynak_url && (
                <div style={{ marginTop: 16 }}>
                  <a
                    href={ilan.kaynak_url}
                    target="_blank"
                    rel="noreferrer"
                    className="btn btn-ghost"
                  >
                    İlan kaynağına git ↗
                  </a>
                </div>
              )}
            </div>

            <Degerlendirme d={ilan.fiyat_degerlendirmesi} ilanFiyat={ilan.fiyat} />
          </div>
        </>
      )}
    </>
  );
}

function Satir({ k, v }) {
  return (
    <div className="detail-row">
      <span className="k">{k}</span>
      <span className="v">{v}</span>
    </div>
  );
}

function Degerlendirme({ d, ilanFiyat }) {
  if (!d) return null;
  const fark = d.fark_yuzdesi;
  const farkMetni =
    fark > 0 ? `%${fark} üzerinde` : fark < 0 ? `%${Math.abs(fark)} altında` : "piyasa değerinde";
  return (
    <div className="result">
      <div className="etiket">Piyasa değerlendirmesi</div>
      <div style={{ margin: "8px 0 12px" }}>
        <span className={`badge ${d.durum}`}>{YORUM_ETIKET[d.durum]}</span>
      </div>
      <p className="yorum-box" style={{ marginTop: 0 }}>
        {d.mesaj}
      </p>

      <div className="result-meta">
        <div className="metric">
          <div className="k">Tahmini piyasa değeri</div>
          <div className="v">{tl(d.tahmini_fiyat)}</div>
        </div>
        <div className="metric">
          <div className="k">İlan fiyatı</div>
          <div className="v">{tl(ilanFiyat)}</div>
        </div>
        <div className="metric">
          <div className="k">Fark</div>
          <div className="v">{farkMetni}</div>
        </div>
      </div>
      <div className="aralik" style={{ marginTop: 12 }}>
        Tahmin aralığı: {tl(d.fiyat_araligi.alt)} – {tl(d.fiyat_araligi.ust)}
      </div>
    </div>
  );
}
