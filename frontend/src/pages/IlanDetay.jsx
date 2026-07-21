import { useParams, Link } from "react-router-dom";
import PageHead, { Placeholder } from "../components/PageHead";

export default function IlanDetay() {
  const { id } = useParams();
  return (
    <>
      <Link to="/ilanlar" className="muted" style={{ fontSize: "0.9rem" }}>
        ← İlanlara dön
      </Link>
      <div style={{ height: 12 }} />
      <PageHead eyebrow={`İlan #${id}`} baslik="İlan detayı" />
      <Placeholder>
        İlan bilgileri ve piyasaya göre fiyat değerlendirmesi bu ekrana gelecek.
      </Placeholder>
    </>
  );
}
