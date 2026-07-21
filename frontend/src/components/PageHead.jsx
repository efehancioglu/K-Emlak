export default function PageHead({ eyebrow, baslik, aciklama }) {
  return (
    <div className="page-head">
      {eyebrow && <div className="eyebrow">{eyebrow}</div>}
      <h1>{baslik}</h1>
      {aciklama && <p>{aciklama}</p>}
    </div>
  );
}

export function Placeholder({ children }) {
  return (
    <div className="placeholder">
      <strong>Bu ekran yakında</strong>
      {children || "İskelet hazır, içerik bir sonraki adımda eklenecek."}
    </div>
  );
}
