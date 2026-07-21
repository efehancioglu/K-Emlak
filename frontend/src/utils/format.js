const _tl = new Intl.NumberFormat("tr-TR", {
  style: "currency",
  currency: "TRY",
  maximumFractionDigits: 0,
});

export const tl = (deger) => _tl.format(deger || 0);

export const sayi = (deger) =>
  new Intl.NumberFormat("tr-TR").format(deger || 0);

export const YORUM_ETIKET = {
  uygun: "Uygun fiyatlı",
  normal: "Piyasa değerinde",
  pahali: "Piyasa üstü",
};
