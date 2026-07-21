import PageHead, { Placeholder } from "../components/PageHead";

export default function Ilanlar() {
  return (
    <>
      <PageHead
        eyebrow="İlanlar"
        baslik="İstanbul konut ilanları"
        aciklama="İlçe, fiyat ve oda sayısına göre filtrele; bir ilana tıklayıp piyasaya göre pahalı mı, normal mi, uygun mu incele."
      />
      <Placeholder>Filtreli ilan listesi bu ekrana gelecek.</Placeholder>
    </>
  );
}
