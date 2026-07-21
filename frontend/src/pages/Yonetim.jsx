import PageHead, { Placeholder } from "../components/PageHead";

export default function Yonetim() {
  return (
    <>
      <PageHead
        eyebrow="Yönetim"
        baslik="Genel bakış"
        aciklama="Toplam ilan, ilçelere göre ortalama metrekare fiyatı ve zaman içindeki fiyat değişimi gibi özet bilgiler ve grafikler."
      />
      <Placeholder>Özet kartlar ve grafikler bu ekrana gelecek.</Placeholder>
    </>
  );
}
