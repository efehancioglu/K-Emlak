import PageHead, { Placeholder } from "../components/PageHead";

export default function Degerleme() {
  return (
    <>
      <PageHead
        eyebrow="Piyasa Değerleme"
        baslik="Evinin değerini öğren"
        aciklama="Evin özelliklerini gir; yapay zeka modeli benzer İstanbul ilanlarına göre tahmini piyasa değerini ve fiyat yorumunu üretsin."
      />
      <Placeholder>
        Değerleme formu ve tahmin sonucu bu ekrana gelecek.
      </Placeholder>
    </>
  );
}
