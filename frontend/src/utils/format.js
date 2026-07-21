const _tl = new Intl.NumberFormat("tr-TR", {
  style: "currency",
  currency: "TRY",
  maximumFractionDigits: 0,
});

export const tl = (deger) => _tl.format(deger || 0);

export const sayi = (deger) =>
  new Intl.NumberFormat("tr-TR").format(deger || 0);

// Grafik eksenleri icin kisa TL: 112000 -> "₺112B", 2400000 -> "₺2,4M"
export const kompaktTl = (deger) => {
  const n = deger || 0;
  if (n >= 1_000_000) return "₺" + (n / 1_000_000).toFixed(1).replace(".", ",") + "M";
  if (n >= 1_000) return "₺" + Math.round(n / 1_000) + "B";
  return "₺" + n;
};

export const YORUM_ETIKET = {
  uygun: "Uygun fiyatlı",
  normal: "Piyasa değerinde",
  pahali: "Piyasa üstü",
};
