import PageHead, { Placeholder } from "../components/PageHead";

export default function Gecmis() {
  return (
    <>
      <PageHead
        eyebrow="Geçmiş"
        baslik="Yapılan değerlemeler"
        aciklama="Daha önce yaptığın tüm değerlemeler burada; ne zaman, hangi ev için ne tahmin çıkmış görebilirsin."
      />
      <Placeholder>Geçmiş değerleme kayıtları bu ekrana gelecek.</Placeholder>
    </>
  );
}
