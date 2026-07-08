import { useState } from "react";
import Header from "./components/Header";
import AboutPage from "./pages/AboutPage";
import HomePage from "./pages/HomePage";

type Page = "home" | "about";

export default function App() {
  const [page, setPage] = useState<Page>("home");

  return (
    <main>
      <Header page={page} onNavigate={setPage} />
      {page === "home" ? <HomePage /> : <AboutPage />}
    </main>
  );
}
