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
  // Search inputs with city and ZIP completion suggestions
  // ---------------------------------------------------------------------
  const initSearchForm = (searchForm) => {
    const searchInput = $("[data-search-input]", searchForm);
    const suggestPanel = $("[data-search-suggest]", searchForm);
    if (!searchInput || !suggestPanel) return;

    const endpoint = searchForm.getAttribute("data-search-url") || "/api/search/";
    let controller = null;
    let timer = null;
    let activeIndex = -1;
    let items = [];
    let currentResults = [];
    let currentIsZip = false;

    const icon = (name) =>
      '<svg class="icon" width="15" height="15" aria-hidden="true"><use href="#i-' +
      name +
      '"></use></svg>';

    const close = () => {
      suggestPanel.hidden = true;
      suggestPanel.innerHTML = "";
      activeIndex = -1;
      items = [];
      currentResults = [];
      currentIsZip = false;
    };

    const setActive = (index) => {
      items.forEach((item, i) => item.classList.toggle("is-active", i === index));
      activeIndex = index;
      if (items[index]) items[index].scrollIntoView({ block: "nearest" });
    };

    const fillZip = (zip) => {
      if (!zip) return;
      searchInput.value = zip;
      searchInput.focus();
      search();
    };

    const render = (results, isZipSearch) => {
      suggestPanel.innerHTML = "";
      currentResults = results || [];
      currentIsZip = Boolean(isZipSearch);

      if (!currentResults.length) {
        const empty = document.createElement("div");
        empty.className = "suggest-empty";
        empty.textContent = currentIsZip
          ? "找不到符合此 ZIP 郵遞區號的城市，請嘗試其他 5 位數 ZIP。"
          : "找不到符合的城市，試試城市名、州別或 ZIP。";
        suggestPanel.appendChild(empty);
        suggestPanel.hidden = false;
        return;
      }

      const head = document.createElement("div");
      head.className = "suggest-head" + (currentIsZip ? " is-zip-head" : "");
      if (currentIsZip) {
        head.innerHTML =
          '<span>' + icon("pin") + ' ZIP 快速補全建議</span>' +
          '<span class="suggest-head-tip">按 Tab 或點擊「帶入」快速補全</span>';
      } else {
        head.textContent = "城市建議";
      }
      suggestPanel.appendChild(head);

      items = currentResults.map((result) => {
        const link = document.createElement("a");
        link.className = "suggest-item" + (currentIsZip ? " is-zip-item" : "");
        link.href = result.url;
        link.innerHTML = icon("pin");

        const copy = document.createElement("div");
        copy.className = "suggest-copy";

        const name = document.createElement("div");
        name.className = "suggest-name";
        name.textContent = result.label;

        // 僅在 zip code 搜尋時顯示 zip code 標籤
        if (currentIsZip && result.zip_code) {
          const zipBadge = document.createElement("span");
          zipBadge.className = "suggest-zip-pill";
          zipBadge.textContent = "ZIP " + result.zip_code;
          name.appendChild(zipBadge);
        }

        const meta = document.createElement("div");
        meta.className = "suggest-meta";
        const metaParts = [];
        if (result.county) metaParts.push(result.county);
        if (result.condition) metaParts.push(result.condition);
        meta.textContent = metaParts.join(" · ");

        copy.appendChild(name);
        copy.appendChild(meta);
        link.appendChild(copy);

        // 僅在 zip code 搜尋時提供補全帶入按鈕
        if (currentIsZip && result.zip_code) {
          const fillBtn = document.createElement("button");
          fillBtn.type = "button";
          fillBtn.className = "suggest-fill-btn";
          fillBtn.title = "帶入 ZIP " + result.zip_code + " 到搜尋框";
          fillBtn.setAttribute("aria-label", "帶入 ZIP " + result.zip_code);
          fillBtn.innerHTML = '帶入 ' + icon("arrow-right");
          fillBtn.addEventListener("click", (event) => {
            event.preventDefault();
            event.stopPropagation();
            fillZip(result.zip_code);
          });
          link.appendChild(fillBtn);
        }

        const temp = document.createElement("span");
        temp.className = "suggest-temp";
        temp.textContent = result.temp === null ? "" : result.temp + result.unit;
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
        render(data.results || [], data.is_zip_search);
      } catch (error) {
        if (error.name !== "AbortError") close();
      }
    };

    searchInput.addEventListener("input", () => {
      window.clearTimeout(timer);
      timer = window.setTimeout(search, 160);
    });

    searchInput.addEventListener("keydown", (event) => {
      if (suggestPanel.hidden) return;

      if (event.key === "ArrowDown") {
        event.preventDefault();
        setActive(Math.min(activeIndex + 1, items.length - 1));
      } else if (event.key === "ArrowUp") {
        event.preventDefault();
        setActive(Math.max(activeIndex - 1, 0));
      } else if (event.key === "Tab") {
        // Tab 補全：在 zip 搜尋下若有匹配結果，按 Tab 帶入選中或第一筆 ZIP
        if (currentIsZip && currentResults.length > 0) {
          const target = activeIndex >= 0 ? currentResults[activeIndex] : currentResults[0];
          if (target && target.zip_code) {
            event.preventDefault();
            fillZip(target.zip_code);
          }
        }
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
  };

  $$("[data-search-form]").forEach(initSearchForm);

  document.addEventListener("keydown", (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
      const globalInput = $("#global-search-input");
      if (globalInput) {
        event.preventDefault();
        globalInput.focus();
        globalInput.select();
      }
    }
  });

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
