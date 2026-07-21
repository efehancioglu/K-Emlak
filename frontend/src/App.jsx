import { createBrowserRouter, RouterProvider } from "react-router-dom";
import Layout from "./components/Layout";
import Degerleme from "./pages/Degerleme";
import Ilanlar from "./pages/Ilanlar";
import IlanDetay from "./pages/IlanDetay";
import Gecmis from "./pages/Gecmis";
import Yonetim from "./pages/Yonetim";

const router = createBrowserRouter([
  {
    path: "/",
    element: <Layout />,
    children: [
      { index: true, element: <Degerleme /> },
      { path: "ilanlar", element: <Ilanlar /> },
      { path: "ilanlar/:id", element: <IlanDetay /> },
      { path: "gecmis", element: <Gecmis /> },
      { path: "yonetim", element: <Yonetim /> },
    ],
  },
]);

export default function App() {
  return <RouterProvider router={router} />;
}
