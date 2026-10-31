/* Skyline Weather — progressive enhancement only */
(function () {
  "use strict";

  const $ = (selector, scope = document) => scope.querySelector(selector);
  const $$ = (selector, scope = document) => Array.from(scope.querySelectorAll(selector));

  // ---------------------------------------------------------------------
  // Mobile navigation
  // ---------------------------------------------------------------------
  const navToggle = $("[data-nav-toggle]");
  const siteNav = $("#site-nav");
  if (navToggle && siteNav) {
    navToggle.addEventListener("click", () => {
      const open = siteNav.classList.toggle("is-open");
      navToggle.setAttribute("aria-expanded", String(open));
    });
    $$(".nav-link", siteNav).forEach((link) => {
      link.addEventListener("click", () => {
        siteNav.classList.remove("is-open");
        navToggle.setAttribute("aria-expanded", "false");
      });
    });
  }

  // ---------------------------------------------------------------------
  // Dismissible alerts / flashes
  // ---------------------------------------------------------------------
  $$("[data-dismiss]").forEach((button) => {
    button.addEventListener("click", () => {
      const flash = button.closest(".flash");
      if (flash) flash.remove();
    });
  });

  $$("[data-dismiss-alert]").forEach((button) => {
    const strip = button.closest(".alert-strip");
    const id = button.getAttribute("data-alert-id") || "alert";
    if (!strip) return;
    try {
      if (localStorage.getItem("skyline-dismissed-" + id) === "1") {
        strip.remove();
        return;
      }
    } catch (error) {
      /* private mode */
    }
    button.addEventListener("click", () => {
      strip.remove();
      try {
        localStorage.setItem("skyline-dismissed-" + id, "1");
      } catch (error) {
        /* private mode */
      }
    });
  });

  // ---------------------------------------------------------------------
  // Header search with city suggestions
  // ---------------------------------------------------------------------
  const searchForm = $("[data-search-form]");
  const searchInput = $("[data-search-input]");
  const suggestPanel = $("[data-search-suggest]");
  if (searchForm && searchInput && suggestPanel) {
    const endpoint = searchForm.getAttribute("data-search-url");
    let controller = null;
    let timer = null;
    let activeIndex = -1;
    let items = [];

    const icon = (name) =>
      '<svg class="icon" width="15" height="15" aria-hidden="true"><use href="#i-' +
      name +
      '"></use></svg>';

    const close = () => {
      suggestPanel.hidden = true;
      suggestPanel.innerHTML = "";
      activeIndex = -1;
      items = [];
    };

    const setActive = (index) => {
      items.forEach((item, i) => item.classList.toggle("is-active", i === index));
      activeIndex = index;
      if (items[index]) items[index].scrollIntoView({ block: "nearest" });
    };

    const render = (results) => {
      suggestPanel.innerHTML = "";
      if (!results.length) {
        const empty = document.createElement("div");
        empty.className = "suggest-empty";
        empty.textContent = "找不到符合的城市，試試城市名、州別或 ZIP。";
        suggestPanel.appendChild(empty);
        suggestPanel.hidden = false;
        return;
      }

      const head = document.createElement("div");
      head.className = "suggest-head";
      head.textContent = "城市建議";
      suggestPanel.appendChild(head);

      items = results.map((result) => {
        const link = document.createElement("a");
        link.className = "suggest-item";
        link.href = result.url;
        link.innerHTML = icon("pin");

        const copy = document.createElement("div");
        const name = document.createElement("div");
        name.className = "suggest-name";
        name.textContent = result.label;
        const meta = document.createElement("div");
        meta.className = "suggest-meta";
        meta.textContent = [result.county, result.condition].filter(Boolean).join(" · ");
        copy.appendChild(name);
        copy.appendChild(meta);

        const temp = document.createElement("span");
        temp.className = "suggest-temp";
        temp.textContent = result.temp === null ? "" : result.temp + result.unit;

        link.appendChild(copy);
        link.appendChild(temp);
        return link;
      });

      items.forEach((item, index) => {
        item.addEventListener("mouseenter", () => setActive(index));
      });

      items.forEach((item) => suggestPanel.appendChild(item));
      suggestPanel.hidden = false;
    };

    const search = async () => {
      const q = searchInput.value.trim();
      if (!q) {
        close();
        return;
      }
      if (!endpoint) return;
      if (controller) controller.abort();
      controller = new AbortController();
      try {
        const response = await fetch(
          endpoint + "?q=" + encodeURIComponent(q),
          { signal: controller.signal, headers: { Accept: "application/json" } }
        );
        if (!response.ok) throw new Error("search failed");
        const data = await response.json();
        render(data.results || []);
      } catch (error) {
        if (error.name !== "AbortError") close();
      }
    };

    searchInput.addEventListener("input", () => {
      window.clearTimeout(timer);
      timer = window.setTimeout(search, 180);
    });

    searchInput.addEventListener("keydown", (event) => {
      if (suggestPanel.hidden) return;
      if (event.key === "ArrowDown") {
        event.preventDefault();
        setActive(Math.min(activeIndex + 1, items.length - 1));
      } else if (event.key === "ArrowUp") {
        event.preventDefault();
        setActive(Math.max(activeIndex - 1, 0));
      } else if (event.key === "Enter" && activeIndex >= 0 && items[activeIndex]) {
        event.preventDefault();
        window.location.href = items[activeIndex].href;
      } else if (event.key === "Escape") {
        close();
      }
    });

    document.addEventListener("click", (event) => {
      if (!searchForm.contains(event.target)) close();
    });

    document.addEventListener("keydown", (event) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        searchInput.focus();
        searchInput.select();
      }
      if (event.key === "Escape") close();
    });
  }

  // ---------------------------------------------------------------------
  // User menu: close when clicking outside or pressing Escape
  // ---------------------------------------------------------------------
  $$("details.user-menu").forEach((menu) => {
    document.addEventListener("click", (event) => {
      if (menu.open && !menu.contains(event.target)) menu.open = false;
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") menu.open = false;
    });
  });

  // ---------------------------------------------------------------------
  // Auto-submit filter selects
  // ---------------------------------------------------------------------
  $$("[data-auto-submit]").forEach((select) => {
    select.addEventListener("change", () => {
      const form = select.form;
      if (form) form.submit();
    });
  });

  // ---------------------------------------------------------------------
  // Confirm destructive actions
  // ---------------------------------------------------------------------
  $$("[data-confirm]").forEach((element) => {
    element.addEventListener("click", (event) => {
      if (!window.confirm(element.getAttribute("data-confirm"))) {
        event.preventDefault();
      }
    });
  });
})();
