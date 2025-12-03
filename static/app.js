// static/app.js
document.addEventListener("DOMContentLoaded", () => {
  /* Menu + overlay */
  const menuBtn = document.getElementById("menu-btn");
  const sideMenu = document.getElementById("side-menu");
  let overlay = document.getElementById("menu-overlay");
  if (!overlay) {
    overlay = document.createElement("div");
    overlay.id = "menu-overlay";
    document.body.appendChild(overlay);
  }

  function openMenu() {
    if (sideMenu) sideMenu.classList.add("open");
    overlay.classList.add("visible");
    document.body.style.overflow = "hidden";
  }
  function closeMenu() {
    if (sideMenu) sideMenu.classList.remove("open");
    overlay.classList.remove("visible");
    document.body.style.overflow = "";
  }

  if (menuBtn) {
    menuBtn.addEventListener("click", () => {
      if (!sideMenu) return;
      if (sideMenu.classList.contains("open")) closeMenu();
      else openMenu();
    });
  }
  overlay.addEventListener("click", closeMenu);
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") closeMenu(); });

  /* Flash auto-hide after 2.5s */
  setTimeout(() => {
    const flashes = document.querySelectorAll('.flash');
    flashes.forEach(f => { f.style.opacity = '0'; setTimeout(()=>f.remove(), 400); });
  }, 2500);

  /* Home search */
  const homeSearchInput = document.getElementById("home-search");
  const homeSearchBtn = document.getElementById("home-search-btn");
  if (homeSearchBtn && homeSearchInput) {
    homeSearchBtn.addEventListener("click", () => {
      const q = homeSearchInput.value.trim();
      const url = q ? `/hotels?q=${encodeURIComponent(q)}` : '/hotels';
      window.location.href = url;
    });
    homeSearchInput.addEventListener("keydown", (ev) => {
      if (ev.key === "Enter") {
        ev.preventDefault();
        homeSearchBtn.click();
      }
    });
  }

  /* List hotels filter */
  const hotelGrid = document.getElementById("hotel-grid");
  if (hotelGrid) {
    const hotelCards = hotelGrid.querySelectorAll(".hotel-card");
    const searchInput = document.getElementById("hotel-search");
    const locationInput = document.getElementById("filter-location");
    const maxPriceInput = document.getElementById("filter-maxprice");
    const resetBtn = document.getElementById("filter-reset");
    const sortSelect = document.getElementById("sort-select");
    const searchBtn = document.getElementById("filter-search");

    const priceOf = el => {
      const raw = el.dataset.minprice;
      const n = Number(raw);
      if (Number.isFinite(n)) return n;
      return Infinity;
    };

    function applyFiltersAndSort() {
      const search = searchInput ? searchInput.value.trim().toLowerCase() : "";
      const location = locationInput ? locationInput.value.trim().toLowerCase() : "";
      const maxPrice = maxPriceInput ? Number(maxPriceInput.value) : 0;
      const sortBy = sortSelect ? sortSelect.value : "";

      hotelCards.forEach(card => {
        const name = (card.dataset.name || "").toLowerCase();
        const loc = (card.dataset.location || "").toLowerCase();
        const price = priceOf(card);

        let visible = true;
        if (search && !name.includes(search)) visible = false;
        if (location && !loc.includes(location)) visible = false;
        if (maxPrice && Number.isFinite(price) && price > maxPrice) visible = false;

        card.style.display = visible ? "block" : "none";
      });

      if (sortBy) {
        const arr = Array.from(hotelGrid.querySelectorAll(".hotel-card")).filter(c => c.style.display !== "none");
        arr.sort((a, b) => {
          if (sortBy === "price_low") return priceOf(a) - priceOf(b);
          if (sortBy === "price_high") return priceOf(b) - priceOf(a);
          if (sortBy === "name_az") return (a.dataset.name || "").localeCompare(b.dataset.name || "");
          if (sortBy === "name_za") return (b.dataset.name || "").localeCompare(a.dataset.name || "");
          return 0;
        });
        arr.forEach(node => hotelGrid.appendChild(node));
      }
    }

    if (searchInput) searchInput.addEventListener("input", applyFiltersAndSort);
    if (locationInput) locationInput.addEventListener("input", applyFiltersAndSort);
    if (maxPriceInput) maxPriceInput.addEventListener("input", applyFiltersAndSort);
    if (sortSelect) sortSelect.addEventListener("change", applyFiltersAndSort);
    if (resetBtn) resetBtn.addEventListener("click", () => {
      if (searchInput) searchInput.value = "";
      if (locationInput) locationInput.value = "";
      if (maxPriceInput) maxPriceInput.value = "";
      if (sortSelect) sortSelect.value = "";
      applyFiltersAndSort();
    });
    if (searchBtn) searchBtn.addEventListener("click", applyFiltersAndSort);

    // small fade-in for cards
    try {
      const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) entry.target.classList.add("visible");
        });
      }, { threshold: 0.12 });
      hotelCards.forEach(c => observer.observe(c));
    } catch (e) {}
  }

});
