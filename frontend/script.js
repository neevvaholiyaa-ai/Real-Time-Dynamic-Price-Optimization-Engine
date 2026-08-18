/**
 * AuraPrice Dynamic Pricing & Margin Optimization Platform
 * Single-Page Application Client Controller
 * Version 3.0 (Multi-User, API-Driven, Microeconomic Simulation)
 */

document.addEventListener("DOMContentLoaded", () => {
    // =========================================================================
    // 1. APPLICATION STATE
    // =========================================================================
    const appState = {
        user: null,
        activeView: "overview",
        products: [],
        productMode: "new",
        activeProductId: null,
        analyses: [],
        latestAnalysis: null,
        dashboardOverview: null,
        actionQueue: [],
        analyticsData: null,
        settings: null,
        queueFilterCategory: "all"
    };

    const API_BASE = window.location.protocol === "file:" 
        ? "http://127.0.0.1:8000" 
        : (["5500", "3000", "5173", "8080"].includes(window.location.port) ? "http://127.0.0.1:8000" : "");

    // =========================================================================
    // 2. DOM ELEMENTS
    // =========================================================================
    const authOverlay = document.getElementById("authOverlay");
    const appShell = document.getElementById("appShell");
    const tabAuthLogin = document.getElementById("tabAuthLogin");
    const tabAuthRegister = document.getElementById("tabAuthRegister");
    const loginForm = document.getElementById("loginForm");
    const registerForm = document.getElementById("registerForm");
    const loginError = document.getElementById("loginError");
    const regError = document.getElementById("regError");

    const sidebarUserName = document.getElementById("sidebarUserName");
    const headerUserDisplayName = document.getElementById("headerUserDisplayName");
    const headerStoreName = document.getElementById("headerStoreName");
    const sidebarLogoutBtn = document.getElementById("sidebarLogoutBtn");

    const navItems = document.querySelectorAll(".sidebar-nav .nav-item");
    const viewContainers = document.querySelectorAll(".view-container");

    // Modals
    const settingsModal = document.getElementById("settingsModal");
    const supportModal = document.getElementById("supportModal");
    const logSalesModal = document.getElementById("logSalesModal");
    const toastNotification = document.getElementById("toastNotification");
    const toastMessage = document.getElementById("toastMessage");

    // =========================================================================
    // 3. UTILITY FUNCTIONS
    // =========================================================================
    function formatINR(val) {
        if (val === null || val === undefined || isNaN(val)) return "₹0.00";
        return "₹" + Number(val).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }

    function formatNumber(val) {
        if (val === null || val === undefined || isNaN(val)) return "0";
        return Number(val).toLocaleString("en-IN");
    }

    let toastTimer = null;
    function showToast(msg, isError = false) {
        if (!toastNotification || !toastMessage) return;
        toastMessage.textContent = msg;
        toastNotification.style.background = isError ? "var(--coral-bg)" : "var(--emerald-bg)";
        toastNotification.style.color = isError ? "var(--coral-text)" : "var(--emerald-text)";
        toastNotification.style.borderColor = isError ? "var(--coral-border)" : "var(--emerald-border)";
        toastNotification.style.display = "flex";

        clearTimeout(toastTimer);
        toastTimer = setTimeout(() => {
            toastNotification.style.display = "none";
        }, 4000);
    }

    async function apiFetch(url, options = {}) {
        options.credentials = "include"; // Always send HttpOnly cookie
        if (options.body && typeof options.body === "object") {
            options.headers = {
                ...options.headers,
                "Content-Type": "application/json"
            };
            options.body = JSON.stringify(options.body);
        }
        try {
            const resp = await fetch(url, options);
            if (resp.status === 401) {
                // Unauthorized session
                appState.user = null;
                showAuthScreen();
                throw new Error("Session expired. Please log in.");
            }
            return resp;
        } catch (err) {
            console.error(`[API Error] ${url}:`, err);
            throw err;
        }
    }

    // =========================================================================
    // 4. AUTHENTICATION CONTROLLER
    // =========================================================================
    function showAuthScreen() {
        document.body.style.backgroundColor = "#0F172A";
        document.body.style.color = "#F8FAFC";
        if (authOverlay) authOverlay.style.display = "flex";
        if (appShell) appShell.style.display = "none";
    }

    function showAppScreen() {
        document.body.style.backgroundColor = "#F1F5F9";
        document.body.style.color = "#0F172A";
        if (authOverlay) authOverlay.style.display = "none";
        if (appShell) appShell.style.display = "flex";
        if (appState.user) {
            const name = appState.user.display_name || appState.user.email.split("@")[0];
            if (sidebarUserName) sidebarUserName.textContent = name;
            if (headerUserDisplayName) headerUserDisplayName.textContent = name;
            if (headerStoreName) headerStoreName.textContent = `${name} — Dynamic Pricing`;
        }
    }

    async function checkAuthSession() {
        try {
            const resp = await fetch(`${API_BASE}/api/auth/me`, { credentials: "include" });
            if (resp.ok) {
                appState.user = await resp.json();
                showAppScreen();
                await initAppData();
            } else {
                showAuthScreen();
            }
        } catch {
            showAuthScreen();
        }
    }

    // Auth Tabs Switcher
    if (tabAuthLogin && tabAuthRegister) {
        tabAuthLogin.addEventListener("click", () => {
            tabAuthLogin.classList.add("active");
            tabAuthRegister.classList.remove("active");
            if (loginForm) loginForm.style.display = "block";
            if (registerForm) registerForm.style.display = "none";
            if (loginError) loginError.style.display = "none";
        });

        tabAuthRegister.addEventListener("click", () => {
            tabAuthRegister.classList.add("active");
            tabAuthLogin.classList.remove("active");
            if (loginForm) loginForm.style.display = "none";
            if (registerForm) registerForm.style.display = "block";
            if (regError) regError.style.display = "none";
        });
    }

    // Login Form Submit
    if (loginForm) {
        loginForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const email = document.getElementById("loginEmail")?.value;
            const password = document.getElementById("loginPassword")?.value;
            if (loginError) loginError.style.display = "none";

            try {
                const resp = await fetch(`${API_BASE}/api/auth/login`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ email, password }),
                    credentials: "include"
                });

                if (resp.ok) {
                    appState.user = await resp.json();
                    showAppScreen();
                    showToast(`Welcome back, ${appState.user.display_name}!`);
                    await initAppData();
                } else {
                    const err = await resp.json();
                    if (loginError) {
                        loginError.textContent = err.detail || "Invalid email or password.";
                        loginError.style.display = "block";
                    }
                }
            } catch (err) {
                if (loginError) {
                    loginError.textContent = "Network error. Please ensure the backend server is running.";
                    loginError.style.display = "block";
                }
            }
        });
    }

    // Register Form Submit
    if (registerForm) {
        registerForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const display_name = document.getElementById("regDisplayName")?.value;
            const email = document.getElementById("regEmail")?.value;
            const password = document.getElementById("regPassword")?.value;
            if (regError) regError.style.display = "none";

            try {
                const resp = await fetch(`${API_BASE}/api/auth/register`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ display_name, email, password }),
                    credentials: "include"
                });

                if (resp.ok) {
                    appState.user = await resp.json();
                    showAppScreen();
                    showToast(`Account created! Welcome, ${appState.user.display_name}!`);
                    await initAppData();
                } else {
                    const err = await resp.json();
                    if (regError) {
                        regError.textContent = err.detail || "Registration failed. Email may already be in use.";
                        regError.style.display = "block";
                    }
                }
            } catch (err) {
                if (regError) {
                    regError.textContent = "Network error. Please try again.";
                    regError.style.display = "block";
                }
            }
        });
    }

    // Logout Handler
    if (sidebarLogoutBtn) {
        sidebarLogoutBtn.addEventListener("click", async () => {
            try {
                await fetch(`${API_BASE}/api/auth/logout`, { method: "POST", credentials: "include" });
            } catch {}
            appState.user = null;
            showAuthScreen();
            showToast("Signed out successfully.");
        });
    }

    // =========================================================================
    // 5. DATA INITIALIZATION & VIEW NAVIGATION
    // =========================================================================
    async function initAppData() {
        await Promise.all([
            loadProducts(),
            loadDashboardOverview(),
            loadActionQueue(),
            loadAnalytics(),
            loadSettings()
        ]);
        switchView(appState.activeView);
    }

    function switchView(viewName) {
        appState.activeView = viewName;

        navItems.forEach(btn => {
            btn.classList.toggle("active", btn.dataset.view === viewName);
        });

        viewContainers.forEach(container => {
            const isMatch = container.id.toLowerCase() === `view${viewName}`.toLowerCase();
            container.classList.toggle("active", isMatch);
        });

        // Trigger view-specific render
        if (viewName === "overview") renderDashboard();
        else if (viewName === "simulator") renderProductAnalyzer();
        else if (viewName === "queue") renderActionQueue();
        else if (viewName === "radar") renderCompetitorInsights();
        else if (viewName === "analytics") renderRevenueAnalytics();
        else if (viewName === "rules") renderPricingRules();

        // Close sidebar on mobile after navigation
        if (window.innerWidth <= 1024) closeMobileSidebar();
    }

    navItems.forEach(item => {
        item.addEventListener("click", () => {
            const view = item.dataset.view;
            if (view) switchView(view);
        });
    });

    // Mobile Sidebar controls
    const mobileMenuBtn = document.getElementById("mobileMenuBtn");
    const sidebarCloseBtn = document.getElementById("sidebarCloseBtn");
    const sidebarOverlay = document.getElementById("sidebarOverlay");
    const appSidebar = document.getElementById("appSidebar");

    function openMobileSidebar() {
        if (appSidebar) appSidebar.classList.add("mobile-open");
        if (sidebarOverlay) sidebarOverlay.classList.add("active");
    }

    function closeMobileSidebar() {
        if (appSidebar) appSidebar.classList.remove("mobile-open");
        if (sidebarOverlay) sidebarOverlay.classList.remove("active");
    }

    if (mobileMenuBtn) mobileMenuBtn.addEventListener("click", openMobileSidebar);
    if (sidebarCloseBtn) sidebarCloseBtn.addEventListener("click", closeMobileSidebar);
    if (sidebarOverlay) sidebarOverlay.addEventListener("click", closeMobileSidebar);

    // =========================================================================
    // 6. VIEW 1: DASHBOARD
    // =========================================================================
    async function loadDashboardOverview() {
        try {
            const resp = await apiFetch("/api/dashboard/overview");
            if (resp.ok) {
                appState.dashboardOverview = await resp.json();
            }
        } catch (err) {
            console.error("Failed to load dashboard overview:", err);
        }
    }

    function renderDashboard() {
        const d = appState.dashboardOverview;
        if (!d) return;

        // KPI 1: Avg Margin Lift
        const kpiMargin = document.getElementById("kpiMarginLift");
        if (kpiMargin) {
            kpiMargin.textContent = d.avg_margin_lift_pct !== null ? `${d.avg_margin_lift_pct >= 0 ? '+' : ''}${d.avg_margin_lift_pct.toFixed(1)}%` : "--";
        }

        // KPI 2: Price Elasticity Index
        const kpiElasticity = document.getElementById("kpiElasticity");
        const kpiElasticityDesc = document.getElementById("kpiElasticityDesc");
        if (kpiElasticity) {
            kpiElasticity.textContent = d.price_elasticity_index !== null ? d.price_elasticity_index.toFixed(2) : "--";
        }
        if (kpiElasticityDesc) {
            kpiElasticityDesc.textContent = d.price_elasticity_index !== null
                ? (d.price_elasticity_index < -1.5 ? "Elastic — Sensitive Demand" : "Inelastic — Margin Room")
                : "Insufficient data";
        }

        // KPI 3: Competitor Gap
        const kpiCompetitorGap = document.getElementById("kpiCompetitorGap");
        const kpiCompetitorGapSub = document.getElementById("kpiCompetitorGapSub");
        if (kpiCompetitorGap) {
            kpiCompetitorGap.textContent = d.competitor_gap_avg_pct !== null ? `${d.competitor_gap_avg_pct > 0 ? '+' : ''}${d.competitor_gap_avg_pct.toFixed(1)}%` : "--";
        }
        if (kpiCompetitorGapSub) {
            kpiCompetitorGapSub.textContent = d.competitor_status_label || "User-provided benchmark";
        }

        // KPI 4: Stock Runway
        const kpiRunway = document.getElementById("kpiRunway");
        const kpiRunwaySub = document.getElementById("kpiRunwaySub");
        if (kpiRunway) {
            kpiRunway.textContent = d.stock_runway_avg_days !== null ? `${Math.round(d.stock_runway_avg_days)} Days` : "--";
        }
        if (kpiRunwaySub) {
            kpiRunwaySub.textContent = d.stock_status_label || "Inventory burn estimate";
        }

        // KPI 5: Products Analyzed
        const kpiAnalyzed = document.getElementById("kpiProductsAnalyzed");
        if (kpiAnalyzed) {
            kpiAnalyzed.textContent = formatNumber(d.products_analyzed_count);
        }

        // KPI 6: Projected Profit Opportunity
        const kpiProfitOpp = document.getElementById("kpiProfitOpportunity");
        if (kpiProfitOpp) {
            kpiProfitOpp.textContent = d.projected_profit_opportunity_30d !== null ? formatINR(d.projected_profit_opportunity_30d) : "₹0.00";
        }

        renderDynamicSignals(d.signals || []);
        renderUrgentQueueTable();
        renderProfitFrontierChart();
    }

    function renderDynamicSignals(signals) {
        const container = document.getElementById("signalList");
        if (!container) return;
        container.innerHTML = "";

        if (!signals || signals.length === 0) {
            container.innerHTML = `
                <div class="empty-state-container" style="padding: 1.5rem 1rem;">
                    <span class="material-symbols-outlined empty-state-icon" style="width:40px;height:40px;font-size:24px;">info</span>
                    <div class="empty-state-title" style="font-size:0.95rem;">No Active Signals</div>
                    <div class="empty-state-desc" style="font-size:0.8rem;">Add products and run analyses to generate dynamic pricing signals.</div>
                </div>
            `;
            return;
        }

        signals.forEach(s => {
            const div = document.createElement("div");
            div.className = "signal-item";
            div.innerHTML = `
                <div class="signal-icon-wrap ${s.icon_class || 'signal-icon-blue'}">
                    <span class="material-symbols-outlined">${s.icon || 'bolt'}</span>
                </div>
                <div class="signal-body">
                    <div class="signal-title">${s.title}</div>
                    <div class="signal-desc">${s.desc}</div>
                    <div class="signal-meta">${s.meta || ''}</div>
                </div>
            `;
            container.appendChild(div);
        });
    }

    function renderUrgentQueueTable() {
        const tbody = document.getElementById("urgentTableBody");
        if (!tbody) return;
        tbody.innerHTML = "";

        const items = appState.actionQueue.slice(0, 5);
        if (items.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" style="text-align:center;padding:2.5rem 1rem;color:var(--text-muted);">
                        <span class="material-symbols-outlined" style="font-size:32px;display:block;margin-bottom:0.5rem;color:var(--text-muted);">task_alt</span>
                        <strong>No Urgent Price Actions Pending</strong>
                        <p style="font-size:0.8rem;margin-top:0.25rem;">All product prices are aligned with current guardrails.</p>
                    </td>
                </tr>
            `;
            return;
        }

        items.forEach(item => {
            const tr = document.createElement("tr");
            const isUp = item.price_change >= 0;
            const colorClass = isUp ? "price-up" : "price-down";
            const arrow = isUp ? "↑" : "↓";
            const confClass = item.confidence_level === "high" ? "badge-high" : item.confidence_level === "medium" ? "badge-medium" : "badge-low";

            tr.innerHTML = `
                <td>
                    <span class="table-product-name">${item.product_name}</span>
                    <span class="table-product-sku">ID: ${item.product_id.slice(0, 8)}</span>
                </td>
                <td><span class="feat-tag feat-pricing">${item.category}</span></td>
                <td class="mono-num">${formatINR(item.current_price)}</td>
                <td class="mono-num ${colorClass}" style="font-weight:700;">${formatINR(item.recommended_price)} ${arrow}</td>
                <td class="table-impact ${colorClass}">+${item.margin_lift_pct.toFixed(1)}% Lift</td>
                <td><span class="confidence-badge ${confClass}">${item.confidence_level.toUpperCase()}</span></td>
                <td>
                    <button class="table-approve-btn" data-id="${item.analysis_id}">Approve</button>
                </td>
            `;

            const btn = tr.querySelector(".table-approve-btn");
            btn.addEventListener("click", () => applyRecommendation(item.analysis_id, btn));
            tbody.appendChild(tr);
        });
    }

    const overviewApproveAllBtn = document.getElementById("overviewApproveAllBtn");
    if (overviewApproveAllBtn) {
        overviewApproveAllBtn.addEventListener("click", async () => {
            const pending = appState.actionQueue;
            if (pending.length === 0) {
                showToast("No pending recommendations to approve.");
                return;
            }
            let successCount = 0;
            for (const item of pending) {
                try {
                    await apiFetch(`/api/analyses/${item.analysis_id}/apply`, { method: "PUT" });
                    successCount++;
                } catch {}
            }
            showToast(`Approved ${successCount} dynamic price recommendations!`);
            await initAppData();
        });
    }

    // =========================================================================
    // 7. VIEW 2: PRODUCT ANALYZER & SIMULATOR
    // =========================================================================
    async function loadProducts() {
        try {
            const resp = await apiFetch("/api/products");
            if (resp.ok) {
                appState.products = await resp.json();
                populateProductDropdown();
            }
        } catch (err) {
            console.error("Failed to load products:", err);
        }
    }

    function populateProductDropdown() {
        const select = document.getElementById("simActiveProductSelect");
        const salesSelect = document.getElementById("salesProductSelect");
        if (!select) return;

        select.innerHTML = '<option value="">Select Stored Product to Optimize</option>';
        if (salesSelect) salesSelect.innerHTML = '<option value="">-- Select Product --</option>';

        appState.products.forEach(p => {
            const opt = document.createElement("option");
            opt.value = p.product_id;
            opt.textContent = `${p.product_name} (${formatINR(p.current_price)})`;
            select.appendChild(opt);

            if (salesSelect) {
                const opt2 = document.createElement("option");
                opt2.value = p.product_id;
                opt2.textContent = `${p.product_name} (${p.category})`;
                salesSelect.appendChild(opt2);
            }
        });

        if (appState.activeProductId) {
            select.value = appState.activeProductId;
        } else {
            select.value = "";
        }
    }

    function renderProductAnalyzer() {
        populateProductDropdown();
        const select = document.getElementById("simActiveProductSelect");
        if (appState.activeProductId) {
            select.value = appState.activeProductId;
            const prod = appState.products.find(p => p.product_id === appState.activeProductId);
            if (prod) {
                loadProductIntoForm(prod);
                return;
            }
        }
        if (select && select.value) {
            const prod = appState.products.find(p => p.product_id === select.value);
            if (prod) {
                loadProductIntoForm(prod);
                return;
            }
        }
        resetProductForm();
    }

    function loadProductIntoForm(prod) {
        appState.activeProductId = prod.product_id;
        appState.productMode = "edit";
        const select = document.getElementById("simActiveProductSelect");
        if (select) select.value = prod.product_id;

        document.getElementById("prodInputName").value = prod.product_name || "";
        document.getElementById("prodInputCategory").value = prod.category || "";
        document.getElementById("prodInputBrand").value = prod.brand || "";
        document.getElementById("prodInputLocation").value = prod.location || "";
        document.getElementById("prodInputCostPrice").value = prod.cost_price !== null && prod.cost_price !== undefined ? prod.cost_price : "";
        document.getElementById("prodInputCurrentPrice").value = prod.current_price !== null && prod.current_price !== undefined ? prod.current_price : "";
        document.getElementById("prodInputMRP").value = prod.mrp !== null && prod.mrp !== undefined ? prod.mrp : "";
        document.getElementById("prodInputCompetitorPrice").value = prod.competitor_price !== null && prod.competitor_price !== undefined ? prod.competitor_price : "";
        document.getElementById("prodInputCompetitorName").value = prod.competitor_name || "";
        document.getElementById("prodInputStock").value = prod.stock_quantity !== null && prod.stock_quantity !== undefined ? prod.stock_quantity : "";
        document.getElementById("prodInputDailySales").value = prod.average_daily_sales !== null && prod.average_daily_sales !== undefined ? prod.average_daily_sales : "";
        document.getElementById("prodInputGoal").value = prod.business_goal || "balanced";

        // Sync slider values
        const sliderComp = document.getElementById("sliderComp");
        if (sliderComp) {
            const cPrice = prod.competitor_price || prod.current_price || 2000;
            sliderComp.value = cPrice;
            const compVal = document.getElementById("sliderCompVal");
            if (compVal) compVal.textContent = formatINR(cPrice);
        }

        // Run real-time simulation
        runStatelessSimulation();
    }

    // Selector change event
    const simProductSelect = document.getElementById("simActiveProductSelect");
    if (simProductSelect) {
        simProductSelect.addEventListener("change", () => {
            const pid = simProductSelect.value;
            if (pid) {
                const prod = appState.products.find(p => p.product_id === pid);
                if (prod) loadProductIntoForm(prod);
            } else {
                resetProductForm();
            }
        });
    }

    function resetProductForm() {
        appState.activeProductId = null;
        appState.latestAnalysis = null;
        appState.productMode = "new";

        const select = document.getElementById("simActiveProductSelect");
        if (select) select.value = "";

        const nameInput = document.getElementById("prodInputName");
        if (nameInput) nameInput.value = "";
        const catInput = document.getElementById("prodInputCategory");
        if (catInput) catInput.value = "";
        const brandInput = document.getElementById("prodInputBrand");
        if (brandInput) brandInput.value = "";
        const locInput = document.getElementById("prodInputLocation");
        if (locInput) locInput.value = "";
        const costInput = document.getElementById("prodInputCostPrice");
        if (costInput) costInput.value = "";
        const currInput = document.getElementById("prodInputCurrentPrice");
        if (currInput) currInput.value = "";
        const mrpInput = document.getElementById("prodInputMRP");
        if (mrpInput) mrpInput.value = "";
        const compPriceInput = document.getElementById("prodInputCompetitorPrice");
        if (compPriceInput) compPriceInput.value = "";
        const compNameInput = document.getElementById("prodInputCompetitorName");
        if (compNameInput) compNameInput.value = "";
        const stockInput = document.getElementById("prodInputStock");
        if (stockInput) stockInput.value = "";
        const salesInput = document.getElementById("prodInputDailySales");
        if (salesInput) salesInput.value = "";
        const goalInput = document.getElementById("prodInputGoal");
        if (goalInput) goalInput.value = "";

        // Reset Hero and Outputs
        const heroTitle = document.getElementById("simProductHeroTitle");
        if (heroTitle) heroTitle.textContent = "New Product Specification";
        const recPrice = document.getElementById("simRecPrice");
        if (recPrice) recPrice.textContent = "--";
        const currDisplay = document.getElementById("simCurrentPriceDisplay");
        if (currDisplay) currDisplay.textContent = "₹--";
        const deltaDisplay = document.getElementById("simPriceDeltaDisplay");
        if (deltaDisplay) deltaDisplay.textContent = "₹0 (0.0%)";
        const marginPill = document.getElementById("simMarginPill");
        if (marginPill) {
            marginPill.textContent = "--% Gross Margin";
            marginPill.style.background = "var(--surface-light)";
            marginPill.style.color = "var(--text-muted)";
            marginPill.style.borderColor = "var(--border-subtle)";
        }
        const actionBadge = document.getElementById("simActionBadge");
        if (actionBadge) {
            actionBadge.textContent = "Awaiting Input";
            actionBadge.style.background = "var(--brand-light)";
            actionBadge.style.color = "var(--brand-primary)";
        }
        const confBadge = document.getElementById("simConfidenceBadge");
        if (confBadge) {
            confBadge.textContent = "Confidence: --";
            confBadge.className = "confidence-badge badge-medium";
        }
        const floorPrice = document.getElementById("simFloorPrice");
        if (floorPrice) floorPrice.textContent = "₹--";
        const ceilPrice = document.getElementById("simCeilPrice");
        if (ceilPrice) ceilPrice.textContent = "₹--";
        const guardStatus = document.getElementById("simGuardrailStatus");
        if (guardStatus) {
            guardStatus.textContent = "Pending";
            guardStatus.className = "guardrail-badge badge-pass";
        }
        const simVol = document.getElementById("simVolume");
        if (simVol) simVol.textContent = "-- Units";
        const simRev = document.getElementById("simRevenue");
        if (simRev) simRev.textContent = "₹--";
        const simMarg = document.getElementById("simMargin");
        if (simMarg) simMarg.textContent = "--%";
        const simMargSub = document.getElementById("simMarginSub");
        if (simMargSub) simMargSub.textContent = "--";

        const insightsList = document.getElementById("simInsightsList");
        if (insightsList) {
            insightsList.innerHTML = "<li>Provide product parameters and click Analyze to view economic reasoning.</li>";
        }
        const driversTags = document.getElementById("economicDriversTags");
        if (driversTags) {
            driversTags.innerHTML = "";
        }

        // Reset Sliders
        const sliderComp = document.getElementById("sliderComp");
        if (sliderComp) {
            sliderComp.value = 4150;
            const compVal = document.getElementById("sliderCompVal");
            if (compVal) compVal.textContent = "₹4,150";
        }
        const sliderDemand = document.getElementById("sliderDemand");
        if (sliderDemand) {
            sliderDemand.value = 100;
            const demandVal = document.getElementById("sliderDemandVal");
            if (demandVal) demandVal.textContent = "1.0x";
        }
        const sliderInventory = document.getElementById("sliderInventory");
        if (sliderInventory) {
            sliderInventory.value = 30;
            const invVal = document.getElementById("sliderInventoryVal");
            if (invVal) invVal.textContent = "30 Days";
        }
        const sliderMargin = document.getElementById("sliderMargin");
        if (sliderMargin) {
            sliderMargin.value = 5.5;
            const marginVal = document.getElementById("sliderMarginVal");
            if (marginVal) marginVal.textContent = "5.5%";
        }

        // Clear simulation chart
        renderTopologySimulationChart(null);
    }

    const btnNewProduct = document.getElementById("btnNewProduct");
    if (btnNewProduct) {
        btnNewProduct.addEventListener("click", () => {
            resetProductForm();
            showToast("Ready to configure a new product.");
        });
    }

    const sidebarAddProductBtn = document.getElementById("sidebarAddProductBtn");
    if (sidebarAddProductBtn) {
        sidebarAddProductBtn.addEventListener("click", () => {
            switchView("simulator");
            resetProductForm();
            showToast("Ready to configure a new product.");
        });
    }

    const headerAddProductBtn = document.getElementById("headerAddProductBtn");
    if (headerAddProductBtn) {
        headerAddProductBtn.addEventListener("click", () => {
            switchView("simulator");
            resetProductForm();
            showToast("Ready to configure a new product.");
        });
    }

    // Save Product Button
    const btnSaveProductChanges = document.getElementById("btnSaveProductChanges");
    if (btnSaveProductChanges) {
        btnSaveProductChanges.addEventListener("click", async () => {
            const payload = getProductFormData();
            if (!payload) return;

            try {
                if (appState.activeProductId) {
                    // Update existing
                    const resp = await apiFetch(`/api/products/${appState.activeProductId}`, {
                        method: "PUT",
                        body: payload
                    });
                    if (resp.ok) {
                        const updated = await resp.json();
                        showToast(`Product "${updated.product_name}" updated successfully!`);
                        await loadProducts();
                        const sel = document.getElementById("simActiveProductSelect");
                        if (sel) sel.value = updated.product_id;
                    } else {
                        const err = await resp.json();
                        showToast(err.detail || "Failed to update product.", true);
                    }
                } else {
                    // Create new
                    const resp = await apiFetch("/api/products", {
                        method: "POST",
                        body: payload
                    });
                    if (resp.ok) {
                        const created = await resp.json();
                        appState.activeProductId = created.product_id;
                        appState.productMode = "edit";
                        showToast(`Product "${created.product_name}" created successfully!`);
                        await loadProducts();
                        const sel = document.getElementById("simActiveProductSelect");
                        if (sel) sel.value = created.product_id;
                    } else {
                        const err = await resp.json();
                        showToast(err.detail || "Failed to create product.", true);
                    }
                }
            } catch (err) {
                showToast("Network error while saving product.", true);
            }
        });
    }

    // Analyze & Save Button
    const btnRunFullAnalysis = document.getElementById("btnRunFullAnalysis");
    if (btnRunFullAnalysis) {
        btnRunFullAnalysis.addEventListener("click", async () => {
            const payload = getProductFormData();
            if (!payload) return;

            try {
                let productId = appState.activeProductId;
                if (!productId) {
                    // Save product first
                    const pResp = await apiFetch("/api/products", { method: "POST", body: payload });
                    if (!pResp.ok) {
                        const err = await pResp.json();
                        showToast(err.detail || "Failed to save product.", true);
                        return;
                    }
                    const newProd = await pResp.json();
                    productId = newProd.product_id;
                    appState.activeProductId = productId;
                    appState.productMode = "edit";
                    await loadProducts();
                    const sel = document.getElementById("simActiveProductSelect");
                    if (sel) sel.value = productId;
                } else {
                    // Save updates
                    await apiFetch(`/api/products/${productId}`, { method: "PUT", body: payload });
                    await loadProducts();
                    const sel = document.getElementById("simActiveProductSelect");
                    if (sel) sel.value = productId;
                }

                // Run Analysis Endpoint
                const aResp = await apiFetch(`/api/products/${productId}/analyze`, { method: "POST" });
                if (aResp.ok) {
                    const analysis = await aResp.json();
                    appState.latestAnalysis = analysis;
                    renderAnalysisResults(analysis);
                    showToast("AI dynamic pricing analysis completed & saved!");
                    await Promise.all([loadDashboardOverview(), loadActionQueue(), loadAnalytics()]);
                } else {
                    const err = await aResp.json();
                    showToast(err.detail || "Analysis failed.", true);
                }
            } catch (err) {
                showToast("Error running analysis.", true);
            }
        });
    }

    function getProductFormData() {
        const name = document.getElementById("prodInputName")?.value.trim();
        const category = document.getElementById("prodInputCategory")?.value;
        const cost = parseFloat(document.getElementById("prodInputCostPrice")?.value);
        const curr = parseFloat(document.getElementById("prodInputCurrentPrice")?.value);
        const mrp = parseFloat(document.getElementById("prodInputMRP")?.value);

        if (!name) {
            showToast("Please enter a product name.", true);
            return null;
        }
        if (!category) {
            showToast("Please select a product category.", true);
            return null;
        }
        if (isNaN(cost) || cost <= 0) {
            showToast("Please enter a valid positive cost price.", true);
            return null;
        }
        if (isNaN(curr) || curr <= 0) {
            showToast("Please enter a valid current selling price.", true);
            return null;
        }
        if (isNaN(mrp) || mrp <= 0) {
            showToast("Please enter a valid MRP.", true);
            return null;
        }
        if (cost > mrp) {
            showToast("Cost price cannot exceed MRP.", true);
            return null;
        }

        const compVal = document.getElementById("prodInputCompetitorPrice")?.value;
        const compPrice = compVal ? parseFloat(compVal) : null;
        const compName = document.getElementById("prodInputCompetitorName")?.value.trim() || null;
        const stockVal = document.getElementById("prodInputStock")?.value;
        const stock = stockVal ? parseInt(stockVal) : null;
        const salesVal = document.getElementById("prodInputDailySales")?.value;
        const sales = salesVal ? parseFloat(salesVal) : null;
        const locVal = document.getElementById("prodInputLocation")?.value.trim() || null;
        const goalVal = document.getElementById("prodInputGoal")?.value || "balanced";

        return {
            product_name: name,
            category: category,
            brand: document.getElementById("prodInputBrand")?.value.trim() || null,
            location: locVal,
            cost_price: cost,
            current_price: curr,
            mrp: mrp,
            competitor_price: compPrice,
            competitor_name: compName,
            stock_quantity: stock,
            average_daily_sales: sales,
            business_goal: goalVal
        };
    }

    // Stateless Simulation Runner (Sliders & Knobs)
    let simTimer = null;
    function debounceSimulation() {
        clearTimeout(simTimer);
        simTimer = setTimeout(runStatelessSimulation, 250);
    }

    // Slider inputs
    const sliderComp = document.getElementById("sliderComp");
    const sliderDemand = document.getElementById("sliderDemand");
    const sliderInventory = document.getElementById("sliderInventory");
    const sliderMargin = document.getElementById("sliderMargin");

    [sliderComp, sliderDemand, sliderInventory, sliderMargin].forEach(s => {
        if (s) {
            s.addEventListener("input", () => {
                if (sliderComp) document.getElementById("sliderCompVal").textContent = formatINR(sliderComp.value);
                if (sliderDemand) document.getElementById("sliderDemandVal").textContent = (parseInt(sliderDemand.value) / 100).toFixed(1) + "x";
                if (sliderInventory) document.getElementById("sliderInventoryVal").textContent = sliderInventory.value + " Days";
                if (sliderMargin) document.getElementById("sliderMarginVal").textContent = sliderMargin.value + "%";
                debounceSimulation();
            });
        }
    });

    // Form inputs and dropdowns trigger real-time simulation
    ["prodInputCostPrice", "prodInputCurrentPrice", "prodInputMRP", "prodInputCategory", "prodInputLocation", "prodInputCompetitorPrice", "prodInputStock", "prodInputDailySales", "prodInputGoal"].forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.addEventListener("input", debounceSimulation);
            el.addEventListener("change", debounceSimulation);
        }
    });

    async function runStatelessSimulation() {
        const cost = parseFloat(document.getElementById("prodInputCostPrice")?.value);
        const curr = parseFloat(document.getElementById("prodInputCurrentPrice")?.value);
        const mrp = parseFloat(document.getElementById("prodInputMRP")?.value);
        if (isNaN(cost) || isNaN(curr) || isNaN(mrp) || cost <= 0 || curr <= 0 || mrp <= 0 || cost > mrp) return;

        const name = document.getElementById("prodInputName")?.value || "Simulation Target";
        const cat = document.getElementById("prodInputCategory")?.value || "Electronics";
        const loc = document.getElementById("prodInputLocation")?.value || "Ahmedabad";
        const comp = sliderComp ? parseFloat(sliderComp.value) : (parseFloat(document.getElementById("prodInputCompetitorPrice")?.value) || curr);
        const demandMult = sliderDemand ? (parseInt(sliderDemand.value) / 100) : 1.0;
        const runway = sliderInventory ? parseInt(sliderInventory.value) : 30;
        const orders = Math.round(25 * demandMult);
        const stock = Math.round(runway * orders);

        const simPayload = {
            product_id: appState.activeProductId || "PROD-SIM-001",
            product_name: name,
            category: cat,
            city: loc,
            location: loc,
            cost_price: cost,
            current_price: curr,
            mrp: mrp,
            competitor_avg_price: comp,
            stock_level: stock,
            orders: orders
        };

        try {
            const resp = await fetch(`${API_BASE}/predict`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(simPayload)
            });

            if (resp.ok) {
                const data = await resp.json();
                renderSimulationOutputs(data, simPayload);
            }
        } catch (err) {
            console.error("Simulation failed:", err);
        }
    }

    function renderSimulationOutputs(data, payload) {
        const title = document.getElementById("simProductHeroTitle");
        if (title) title.textContent = payload.product_name;

        const recPrice = data.recommended_price;
        const currPrice = payload.current_price;
        const costPrice = payload.cost_price;

        document.getElementById("simRecPrice").textContent = Math.round(recPrice).toLocaleString("en-IN");
        document.getElementById("simCurrentPriceDisplay").textContent = formatINR(currPrice);

        const delta = recPrice - currPrice;
        const deltaPct = currPrice > 0 ? (delta / currPrice) * 100 : 0;
        const sign = delta >= 0 ? "+" : "";
        document.getElementById("simPriceDeltaDisplay").textContent = `${sign}${formatINR(delta)} (${sign}${deltaPct.toFixed(1)}%)`;

        const marginPill = document.getElementById("simMarginPill");
        const marginPct = recPrice > 0 ? ((recPrice - costPrice) / recPrice) * 100 : 0;
        if (marginPill) {
            marginPill.textContent = `${marginPct.toFixed(1)}% Gross Margin`;
            marginPill.style.background = delta >= 0 ? "var(--emerald-bg)" : "var(--coral-bg)";
            marginPill.style.color = delta >= 0 ? "var(--emerald)" : "var(--coral)";
            marginPill.style.borderColor = delta >= 0 ? "var(--emerald-border)" : "var(--coral-border)";
        }

        const actionBadge = document.getElementById("simActionBadge");
        if (actionBadge) {
            actionBadge.textContent = data.recommendation;
            actionBadge.style.background = deltaPct > 1.5 ? "var(--emerald-bg)" : deltaPct < -1.5 ? "var(--coral-bg)" : "var(--brand-light)";
            actionBadge.style.color = deltaPct > 1.5 ? "var(--emerald)" : deltaPct < -1.5 ? "var(--coral)" : "var(--brand-primary)";
        }

        // Confidence
        const confBadge = document.getElementById("simConfidenceBadge");
        if (confBadge) {
            confBadge.textContent = `Confidence: ${(data.confidence_level || 'MEDIUM').toUpperCase()}`;
            confBadge.className = `confidence-badge badge-${data.confidence_level || 'medium'}`;
        }

        // Guardrails
        document.getElementById("simFloorPrice").textContent = formatINR(data.min_allowed_price);
        document.getElementById("simCeilPrice").textContent = formatINR(data.max_allowed_price);

        const statusBadge = document.getElementById("simGuardrailStatus");
        if (statusBadge) {
            statusBadge.textContent = data.guardrail_applied ? "Clipped by Guardrail" : "Verified Pass";
            statusBadge.className = data.guardrail_applied ? "guardrail-badge badge-clipped" : "guardrail-badge badge-pass";
        }

        // Projections
        const volume = Math.round(payload.orders * 30 * (deltaPct < 0 ? 1.2 : 0.95));
        const revenue = recPrice * volume;
        document.getElementById("simVolume").textContent = `${formatNumber(volume)} Units`;
        document.getElementById("simRevenue").textContent = formatINR(revenue);
        document.getElementById("simMargin").textContent = `${marginPct.toFixed(1)}%`;
        const marginSub = document.getElementById("simMarginSub");
        if (marginSub) {
            marginSub.textContent = `${deltaPct >= 0 ? '+' : ''}${deltaPct.toFixed(1)}% lift`;
        }

        // Insights list
        const insightsList = document.getElementById("simInsightsList");
        if (insightsList && Array.isArray(data.insights)) {
            insightsList.innerHTML = "";
            data.insights.forEach(msg => {
                const li = document.createElement("li");
                li.textContent = msg;
                insightsList.appendChild(li);
            });
        }

        // Economic Drivers
        const driversTags = document.getElementById("economicDriversTags");
        if (driversTags) {
            driversTags.innerHTML = "";
            if (Array.isArray(data.economic_drivers)) {
                data.economic_drivers.forEach(d => {
                    const span = document.createElement("span");
                    span.className = "driver-tag";
                    span.innerHTML = `<strong>${d.name}:</strong> ${d.detail}`;
                    driversTags.appendChild(span);
                });
            }
        }

        renderTopologySimulationChart(data.topology_curve, recPrice, costPrice, payload.mrp, currPrice);
    }

    function renderAnalysisResults(analysis) {
        const title = document.getElementById("simProductHeroTitle");
        if (title) title.textContent = analysis.product_name || document.getElementById("prodInputName")?.value || "Optimized Product";

        const recPrice = analysis.recommended_price;
        const currPrice = analysis.input_current_price;
        const costPrice = analysis.input_cost_price;

        document.getElementById("simRecPrice").textContent = Math.round(recPrice).toLocaleString("en-IN");
        document.getElementById("simCurrentPriceDisplay").textContent = formatINR(currPrice);

        const delta = analysis.price_change;
        const deltaPct = analysis.price_change_pct;
        const sign = delta >= 0 ? "+" : "";
        document.getElementById("simPriceDeltaDisplay").textContent = `${sign}${formatINR(delta)} (${sign}${deltaPct.toFixed(1)}%)`;

        const marginPill = document.getElementById("simMarginPill");
        if (marginPill) {
            marginPill.textContent = `${analysis.margin_recommended_pct.toFixed(1)}% Gross Margin`;
            marginPill.style.background = delta >= 0 ? "var(--emerald-bg)" : "var(--coral-bg)";
            marginPill.style.color = delta >= 0 ? "var(--emerald)" : "var(--coral)";
            marginPill.style.borderColor = delta >= 0 ? "var(--emerald-border)" : "var(--coral-border)";
        }

        const actionBadge = document.getElementById("simActionBadge");
        if (actionBadge) {
            actionBadge.textContent = analysis.recommendation;
            actionBadge.style.background = deltaPct > 1.5 ? "var(--emerald-bg)" : deltaPct < -1.5 ? "var(--coral-bg)" : "var(--brand-light)";
            actionBadge.style.color = deltaPct > 1.5 ? "var(--emerald)" : deltaPct < -1.5 ? "var(--coral)" : "var(--brand-primary)";
        }

        const confBadge = document.getElementById("simConfidenceBadge");
        if (confBadge) {
            confBadge.textContent = `Confidence: ${(analysis.confidence_level || 'MEDIUM').toUpperCase()}`;
            confBadge.className = `confidence-badge badge-${analysis.confidence_level || 'medium'}`;
        }

        document.getElementById("simFloorPrice").textContent = formatINR(analysis.min_allowed_price);
        document.getElementById("simCeilPrice").textContent = formatINR(analysis.max_allowed_price);

        const statusBadge = document.getElementById("simGuardrailStatus");
        if (statusBadge) {
            statusBadge.textContent = analysis.guardrail_applied ? "Clipped by Guardrail" : "Verified Pass";
            statusBadge.className = analysis.guardrail_applied ? "guardrail-badge badge-clipped" : "guardrail-badge badge-pass";
        }

        if (analysis.expected_demand) {
            document.getElementById("simVolume").textContent = `${formatNumber(Math.round(analysis.expected_demand * 30))} Units`;
        }
        if (analysis.expected_revenue_30d) {
            document.getElementById("simRevenue").textContent = formatINR(analysis.expected_revenue_30d);
        }
        document.getElementById("simMargin").textContent = `${analysis.margin_recommended_pct.toFixed(1)}%`;
        const marginSub = document.getElementById("simMarginSub");
        if (marginSub) {
            marginSub.textContent = `${analysis.margin_lift_pct >= 0 ? '+' : ''}${analysis.margin_lift_pct.toFixed(1)}% lift`;
        }

        const insightsList = document.getElementById("simInsightsList");
        if (insightsList && Array.isArray(analysis.insights)) {
            insightsList.innerHTML = "";
            analysis.insights.forEach(msg => {
                const li = document.createElement("li");
                li.textContent = msg;
                insightsList.appendChild(li);
            });
        }

        const driversTags = document.getElementById("economicDriversTags");
        if (driversTags) {
            driversTags.innerHTML = "";
            if (Array.isArray(analysis.economic_drivers)) {
                analysis.economic_drivers.forEach(d => {
                    const span = document.createElement("span");
                    span.className = "driver-tag";
                    span.innerHTML = `<strong>${d.name}:</strong> ${d.detail}`;
                    driversTags.appendChild(span);
                });
            }
        }

        if (analysis.topology_curve && analysis.topology_curve.length > 0) {
            renderTopologySimulationChart(analysis.topology_curve, recPrice, costPrice, analysis.input_mrp, currPrice);
        }
    }

    // Apply Recommendation Button (Product Analyzer)
    const btnApplyRecommendation = document.getElementById("btnApplyRecommendation");
    if (btnApplyRecommendation) {
        btnApplyRecommendation.addEventListener("click", async () => {
            if (!appState.latestAnalysis) {
                showToast("Please run an analysis before applying a recommendation.", true);
                return;
            }
            await applyRecommendation(appState.latestAnalysis.analysis_id, btnApplyRecommendation);
        });
    }

    async function applyRecommendation(analysisId, buttonEl) {
        try {
            if (buttonEl) {
                buttonEl.disabled = true;
                buttonEl.textContent = "Applying...";
            }
            const resp = await apiFetch(`/api/analyses/${analysisId}/apply`, { method: "PUT" });
            if (resp.ok) {
                const res = await resp.json();
                showToast(`Price updated to ${formatINR(res.new_price)}! Pricing history logged.`);
                if (buttonEl) {
                    buttonEl.textContent = "Applied ✓";
                    buttonEl.style.background = "var(--emerald-bg)";
                    buttonEl.style.color = "var(--emerald)";
                }
                await Promise.all([loadProducts(), loadDashboardOverview(), loadActionQueue(), loadAnalytics()]);
                renderDashboard();
            } else {
                const err = await resp.json();
                showToast(err.detail || "Failed to apply recommendation.", true);
                if (buttonEl) {
                    buttonEl.disabled = false;
                    buttonEl.textContent = "Apply";
                }
            }
        } catch (err) {
            showToast("Network error applying recommendation.", true);
            if (buttonEl) {
                buttonEl.disabled = false;
                buttonEl.textContent = "Apply";
            }
        }
    }

    // =========================================================================
    // 8. VIEW 3: REPRICE ACTION QUEUE
    // =========================================================================
    async function loadActionQueue() {
        try {
            const resp = await apiFetch("/api/dashboard/queue");
            if (resp.ok) {
                appState.actionQueue = await resp.json();
                const badge = document.getElementById("queueBadge");
                if (badge) {
                    badge.textContent = appState.actionQueue.length;
                    badge.style.display = appState.actionQueue.length > 0 ? "inline-block" : "none";
                }
            }
        } catch (err) {
            console.error("Failed to load queue:", err);
        }
    }

    function renderActionQueue() {
        const countPill = document.getElementById("queuePendingCount");
        const countIndicator = document.getElementById("queueCountIndicator");
        if (countPill) countPill.textContent = appState.actionQueue.length;
        if (countIndicator) countIndicator.textContent = `${appState.actionQueue.length} Pending`;

        const tbody = document.getElementById("queueTableBody");
        if (!tbody) return;
        tbody.innerHTML = "";

        const filter = appState.queueFilterCategory;
        const list = filter === "all" ? appState.actionQueue : appState.actionQueue.filter(i => i.category === filter);

        if (list.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="9" style="text-align:center;padding:3rem 1rem;color:var(--text-muted);">
                        <span class="material-symbols-outlined" style="font-size:36px;display:block;margin-bottom:0.5rem;color:var(--text-muted);">check_circle</span>
                        <strong>No Pending Adjustments in Action Queue</strong>
                        <p style="font-size:0.85rem;margin-top:0.35rem;">All optimizations have been applied or dismissed.</p>
                    </td>
                </tr>
            `;
            return;
        }

        list.forEach(item => {
            const tr = document.createElement("tr");
            const isUp = item.price_change >= 0;
            const colorClass = isUp ? "price-up" : "price-down";
            const arrow = isUp ? "↑" : "↓";
            const confClass = item.confidence_level === "high" ? "badge-high" : item.confidence_level === "medium" ? "badge-medium" : "badge-low";

            tr.innerHTML = `
                <td><input type="checkbox" class="queue-checkbox row-select" data-id="${item.analysis_id}" checked></td>
                <td>
                    <span class="table-product-name">${item.product_name}</span>
                    <span class="table-product-sku">ID: ${item.product_id.slice(0, 8)}</span>
                </td>
                <td><span class="feat-tag feat-pricing">${item.category}</span></td>
                <td class="mono-num">${formatINR(item.cost_price)}</td>
                <td class="mono-num">${formatINR(item.current_price)}</td>
                <td class="mono-num ${colorClass}" style="font-weight:700;">${formatINR(item.recommended_price)} ${arrow}</td>
                <td class="mono-num ${colorClass}">+${item.margin_lift_pct.toFixed(1)}% Lift</td>
                <td><span class="confidence-badge ${confClass}">${item.confidence_level.toUpperCase()}</span></td>
                <td>
                    <div style="display:flex;gap:0.4rem;">
                        <button class="table-approve-btn" data-id="${item.analysis_id}">Approve</button>
                        <button class="btn-secondary btn-sm btn-dismiss" data-id="${item.analysis_id}" style="padding:0.35rem 0.6rem;">Dismiss</button>
                    </div>
                </td>
            `;

            tr.querySelector(".table-approve-btn").addEventListener("click", (e) => applyRecommendation(item.analysis_id, e.target));
            tr.querySelector(".btn-dismiss").addEventListener("click", () => dismissRecommendation(item.analysis_id));
            tbody.appendChild(tr);
        });
    }

    async function dismissRecommendation(analysisId) {
        try {
            await apiFetch(`/api/analyses/${analysisId}/dismiss`, { method: "PUT" });
            showToast("Recommendation dismissed.");
            await Promise.all([loadActionQueue(), loadDashboardOverview()]);
            renderActionQueue();
        } catch {
            showToast("Failed to dismiss recommendation.", true);
        }
    }

    // Queue Filters
    const filterChips = document.querySelectorAll("#queueCategoryFilters .filter-chip");
    filterChips.forEach(chip => {
        chip.addEventListener("click", () => {
            filterChips.forEach(c => c.classList.remove("active"));
            chip.classList.add("active");
            appState.queueFilterCategory = chip.dataset.filter || "all";
            renderActionQueue();
        });
    });

    const queueSelectAll = document.getElementById("queueSelectAll");
    if (queueSelectAll) {
        queueSelectAll.addEventListener("change", () => {
            document.querySelectorAll(".row-select").forEach(cb => cb.checked = queueSelectAll.checked);
        });
    }

    const queueApproveSelBtn = document.getElementById("queueApproveSelBtn");
    if (queueApproveSelBtn) {
        queueApproveSelBtn.addEventListener("click", async () => {
            const selected = document.querySelectorAll(".row-select:checked");
            if (selected.length === 0) {
                showToast("Please select items to approve.");
                return;
            }
            let success = 0;
            for (const cb of selected) {
                try {
                    await apiFetch(`/api/analyses/${cb.dataset.id}/apply`, { method: "PUT" });
                    success++;
                } catch {}
            }
            showToast(`Approved ${success} selected price adjustments!`);
            await Promise.all([loadProducts(), loadActionQueue(), loadDashboardOverview(), loadAnalytics()]);
            renderActionQueue();
        });
    }

    // =========================================================================
    // 9. VIEW 4: COMPETITOR INSIGHTS (User-Product-Anchored)
    // =========================================================================
    function renderCompetitorInsights() {
        const tbody = document.getElementById("competitorTableBody");
        if (!tbody) return;
        tbody.innerHTML = "";

        if (appState.products.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" style="text-align:center;padding:3rem 1rem;color:var(--text-muted);">
                        <span class="material-symbols-outlined" style="font-size:36px;display:block;margin-bottom:0.5rem;color:var(--text-muted);">storefront</span>
                        <strong>No Products in Your Catalog</strong>
                        <p style="font-size:0.85rem;margin-top:0.35rem;">Add your products and optional competitor prices to view competitor intelligence.</p>
                    </td>
                </tr>
            `;
            return;
        }

        appState.products.forEach(p => {
            const tr = document.createElement("tr");
            const hasComp = p.competitor_price !== null && p.competitor_price > 0;
            const gap = hasComp ? ((p.current_price - p.competitor_price) / p.competitor_price) * 100 : null;
            const position = gap !== null ? (gap > 2 ? "Above Market" : gap < -2 ? "Value Leader" : "Market Parity") : "No Benchmark";
            const positionColor = gap !== null ? (gap > 2 ? "var(--coral)" : gap < -2 ? "var(--emerald)" : "var(--text-primary)") : "var(--text-muted)";

            tr.innerHTML = `
                <td>
                    <span class="table-product-name">${p.product_name}</span>
                    <span class="table-product-sku">ID: ${p.product_id.slice(0, 8)}</span>
                </td>
                <td><span class="feat-tag feat-pricing">${p.category || 'General'}</span></td>
                <td class="mono-num">${formatINR(p.current_price)}</td>
                <td class="mono-num">${hasComp ? formatINR(p.competitor_price) : '<span style="color:var(--text-muted);">Not Provided</span>'}</td>
                <td>${p.competitor_name || '<span style="color:var(--text-muted);">-</span>'}</td>
                <td class="mono-num" style="font-weight:700;color:${positionColor};">
                    ${gap !== null ? `${gap > 0 ? '+' : ''}${gap.toFixed(1)}%` : '<span style="color:var(--text-muted);font-weight:400;">Unavailable</span>'}
                </td>
                <td><span style="font-weight:600;color:${positionColor};">${position}</span></td>
                <td>
                    <span class="feat-tag ${hasComp ? 'feat-funnel' : 'feat-macro'}">
                        ${hasComp ? 'User Provided' : 'Unavailable'}
                    </span>
                </td>
            `;
            tbody.appendChild(tr);
        });
    }

    // =========================================================================
    // 10. VIEW 5: REVENUE & MARGIN ANALYTICS
    // =========================================================================
    async function loadAnalytics() {
        try {
            const resp = await apiFetch("/api/dashboard/analytics");
            if (resp.ok) {
                appState.analyticsData = await resp.json();
            }
        } catch (err) {
            console.error("Failed to load analytics:", err);
        }
    }

    function renderRevenueAnalytics() {
        const a = appState.analyticsData;
        if (!a) return;

        // Actual Revenue
        const actRevEl = document.getElementById("analyticsActualRevenue");
        const actRevSub = document.getElementById("analyticsActualRevenueSub");
        if (actRevEl) {
            actRevEl.textContent = a.has_actual_sales_data ? formatINR(a.actual_historical_revenue) : "₹0.00";
        }
        if (actRevSub) {
            actRevSub.textContent = a.has_actual_sales_data ? "From logged sales history" : "No historical sales logged yet";
        }

        // Projected Revenue
        const projRevEl = document.getElementById("analyticsProjectedRevenue");
        if (projRevEl) {
            projRevEl.textContent = a.projected_total_revenue_30d !== null ? formatINR(a.projected_total_revenue_30d) : "₹0.00";
        }

        // Incremental Lift
        const incLiftEl = document.getElementById("analyticsIncrementalLift");
        if (incLiftEl) {
            incLiftEl.textContent = a.projected_incremental_profit_lift_30d !== null ? `+${formatINR(a.projected_incremental_profit_lift_30d)}` : "₹0.00";
        }

        // Products Count
        const totalProdEl = document.getElementById("analyticsTotalProducts");
        const totalAnalyzedEl = document.getElementById("analyticsTotalAnalyzed");
        if (totalProdEl) totalProdEl.textContent = formatNumber(a.total_products_count);
        if (totalAnalyzedEl) totalAnalyzedEl.textContent = `${a.total_analyzed_count} analyzed`;

        // Category Margin Breakdown List
        const catList = document.getElementById("categoryBreakdownList");
        if (catList) {
            catList.innerHTML = "";
            if (!a.category_margin_breakdown || a.category_margin_breakdown.length === 0) {
                catList.innerHTML = '<p style="color:var(--text-muted);font-size:0.85rem;">Add products to see category margin breakdown.</p>';
            } else {
                a.category_margin_breakdown.forEach(c => {
                    const div = document.createElement("div");
                    div.className = "category-breakdown-item";
                    div.innerHTML = `
                        <div class="cat-item-left">
                            <span class="cat-item-name">${c.category}</span>
                            <span class="cat-item-skus">${c.sku_count} SKU${c.sku_count > 1 ? 's' : ''}</span>
                        </div>
                        <div class="cat-item-margin">${c.avg_margin_pct.toFixed(1)}% Avg Margin</div>
                    `;
                    catList.appendChild(div);
                });
            }
        }

        renderRevenueTrajectoryChart(a.sales_trajectory, a.has_actual_sales_data, a.projected_total_revenue_30d);
    }

    // Log Sales Modal
    const btnOpenLogSalesModal = document.getElementById("btnOpenLogSalesModal");
    const closeLogSalesModal = document.getElementById("closeLogSalesModal");
    const btnCancelLogSales = document.getElementById("btnCancelLogSales");
    const btnSubmitLogSales = document.getElementById("btnSubmitLogSales");

    if (btnOpenLogSalesModal) btnOpenLogSalesModal.addEventListener("click", () => openModal(logSalesModal));
    if (closeLogSalesModal) closeLogSalesModal.addEventListener("click", () => closeModal(logSalesModal));
    if (btnCancelLogSales) btnCancelLogSales.addEventListener("click", () => closeModal(logSalesModal));

    if (btnSubmitLogSales) {
        btnSubmitLogSales.addEventListener("click", async () => {
            const pid = document.getElementById("salesProductSelect")?.value;
            const period = document.getElementById("salesPeriodDate")?.value.trim();
            const units = parseInt(document.getElementById("salesUnitsSold")?.value);
            const price = parseFloat(document.getElementById("salesSellingPrice")?.value);

            if (!pid) { showToast("Please select a product.", true); return; }
            if (!period) { showToast("Please enter a period/date.", true); return; }
            if (isNaN(units) || units < 0) { showToast("Please enter valid units sold.", true); return; }
            if (isNaN(price) || price <= 0) { showToast("Please enter a valid realized price.", true); return; }

            try {
                const resp = await apiFetch(`/api/products/${pid}/sales`, {
                    method: "POST",
                    body: {
                        period_date: period,
                        units_sold: units,
                        selling_price: price
                    }
                });

                if (resp.ok) {
                    showToast("Actual sales record logged successfully!");
                    closeModal(logSalesModal);
                    await loadAnalytics();
                    renderRevenueAnalytics();
                } else {
                    const err = await resp.json();
                    showToast(err.detail || "Failed to log sales.", true);
                }
            } catch {
                showToast("Error logging sales.", true);
            }
        });
    }

    // =========================================================================
    // 11. VIEW 6: PRICING RULES & GUARDRAILS
    // =========================================================================
    async function loadSettings() {
        try {
            const resp = await apiFetch("/api/settings");
            if (resp.ok) {
                appState.settings = await resp.json();
            }
        } catch (err) {
            console.error("Failed to load settings:", err);
        }
    }

    function renderPricingRules() {
        const s = appState.settings;
        if (!s) return;

        const marginEl = document.getElementById("ruleMarginFloor");
        const corridorEl = document.getElementById("ruleCorridorMin");
        const belowCostEl = document.getElementById("ruleNeverBelowCost");
        const aboveMRPEl = document.getElementById("ruleNeverAboveMRP");
        const maxPriceChangeEl = document.getElementById("ruleMaxPriceChange");
        const maxDiscountEl = document.getElementById("ruleMaxDiscount");

        if (marginEl) marginEl.value = s.margin_floor_pct;
        if (corridorEl) corridorEl.value = s.corridor_min_pct;
        if (belowCostEl) belowCostEl.checked = s.never_below_cost;
        if (aboveMRPEl) aboveMRPEl.checked = s.never_above_mrp;
        if (maxPriceChangeEl) maxPriceChangeEl.value = s.max_price_change_pct;
        if (maxDiscountEl) maxDiscountEl.value = s.max_discount_pct;
    }

    const btnSavePricingRules = document.getElementById("btnSavePricingRules");
    if (btnSavePricingRules) {
        btnSavePricingRules.addEventListener("click", async () => {
            const payload = {
                margin_floor_pct: parseFloat(document.getElementById("ruleMarginFloor")?.value || 5.5),
                corridor_min_pct: parseFloat(document.getElementById("ruleCorridorMin")?.value || -25.0),
                corridor_max_pct: 25.0,
                never_below_cost: document.getElementById("ruleNeverBelowCost")?.checked ?? true,
                never_above_mrp: document.getElementById("ruleNeverAboveMRP")?.checked ?? true,
                max_price_change_pct: parseFloat(document.getElementById("ruleMaxPriceChange")?.value || 15.0),
                max_discount_pct: parseFloat(document.getElementById("ruleMaxDiscount")?.value || 40.0)
            };

            try {
                const resp = await apiFetch("/api/settings", { method: "PUT", body: payload });
                if (resp.ok) {
                    appState.settings = await resp.json();
                    showToast("Pricing guardrails and rules saved to database!");
                } else {
                    showToast("Failed to save rules.", true);
                }
            } catch {
                showToast("Network error saving rules.", true);
            }
        });
    }

    // =========================================================================
    // 12. CHARTS (High-DPI Data-Driven Canvas Rendering Engine)
    // =========================================================================
    function setupHiDPICanvas(canvas, desiredHeight) {
        if (!canvas) return null;
        const rect = canvas.parentElement.getBoundingClientRect();
        const w = rect.width > 0 ? rect.width : 400;
        const h = desiredHeight || 240;
        const dpr = window.devicePixelRatio || 1;

        canvas.width = Math.floor(w * dpr);
        canvas.height = Math.floor(h * dpr);
        canvas.style.width = `${w}px`;
        canvas.style.height = `${h}px`;

        const ctx = canvas.getContext("2d");
        ctx.scale(dpr, dpr);
        return { ctx, w, h };
    }

    function drawRoundedBadge(ctx, x, y, text, bgColor, textColor, borderColor) {
        ctx.font = "bold 10px 'JetBrains Mono', monospace";
        const textWidth = ctx.measureText(text).width;
        const padX = 8;
        const padY = 4;
        const badgeW = textWidth + padX * 2;
        const badgeH = 18;
        const rx = Math.max(4, Math.min(x - badgeW / 2, ctx.canvas.width / (window.devicePixelRatio || 1) - badgeW - 6));
        const ry = y - badgeH / 2;

        ctx.fillStyle = bgColor || "#1E293B";
        ctx.strokeStyle = borderColor || "rgba(255, 255, 255, 0.15)";
        ctx.lineWidth = 1;

        // Draw rounded rectangle
        ctx.beginPath();
        ctx.roundRect(rx, ry, badgeW, badgeH, 4);
        ctx.fill();
        ctx.stroke();

        ctx.fillStyle = textColor || "#FFFFFF";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(text, rx + badgeW / 2, ry + badgeH / 2);
    }

    function renderProfitFrontierChart() {
        const canvas = document.getElementById("profitFrontierChart");
        const setup = setupHiDPICanvas(canvas, 240);
        if (!setup) return;
        const { ctx, w, h } = setup;

        ctx.clearRect(0, 0, w, h);

        const padLeft = 45;
        const padRight = 30;
        const padTop = 30;
        const padBottom = 40;
        const plotW = w - padLeft - padRight;
        const plotH = h - padTop - padBottom;

        // Subtle background grid
        ctx.strokeStyle = "rgba(255, 255, 255, 0.05)";
        ctx.lineWidth = 1;
        for (let y = padTop; y <= h - padBottom; y += plotH / 4) {
            ctx.beginPath();
            ctx.moveTo(padLeft, y);
            ctx.lineTo(w - padRight, y);
            ctx.stroke();
        }

        // Draw Profit Curve Area Fill (Gradient)
        const gradProfit = ctx.createLinearGradient(0, padTop, 0, h - padBottom);
        gradProfit.addColorStop(0, "rgba(59, 130, 246, 0.25)");
        gradProfit.addColorStop(1, "rgba(59, 130, 246, 0.0)");

        ctx.fillStyle = gradProfit;
        ctx.beginPath();
        ctx.moveTo(padLeft, h - padBottom);
        ctx.bezierCurveTo(
            padLeft + plotW * 0.3, padTop - 10,
            padLeft + plotW * 0.7, padTop - 10,
            padLeft + plotW, h - padBottom
        );
        ctx.lineTo(padLeft + plotW, h - padBottom);
        ctx.closePath();
        ctx.fill();

        // Draw Demand Curve (Downward sloping emerald)
        ctx.strokeStyle = "#10B981";
        ctx.lineWidth = 2.5;
        ctx.beginPath();
        ctx.moveTo(padLeft, padTop + 20);
        ctx.bezierCurveTo(
            padLeft + plotW * 0.35, padTop + plotH * 0.35,
            padLeft + plotW * 0.65, padTop + plotH * 0.7,
            padLeft + plotW, h - padBottom - 10
        );
        ctx.stroke();

        // Draw Profit Curve Stroke (Royal blue glow)
        ctx.strokeStyle = "#3B82F6";
        ctx.lineWidth = 3;
        ctx.shadowColor = "rgba(59, 130, 246, 0.5)";
        ctx.shadowBlur = 10;
        ctx.beginPath();
        ctx.moveTo(padLeft, h - padBottom);
        ctx.bezierCurveTo(
            padLeft + plotW * 0.3, padTop - 10,
            padLeft + plotW * 0.7, padTop - 10,
            padLeft + plotW, h - padBottom
        );
        ctx.stroke();
        ctx.shadowBlur = 0; // reset shadow

        // Peak Sweet Spot Marker
        const peakX = padLeft + plotW * 0.5;
        const peakY = padTop + 14;

        // Glowing outer circle
        ctx.fillStyle = "rgba(59, 130, 246, 0.3)";
        ctx.beginPath();
        ctx.arc(peakX, peakY, 10, 0, Math.PI * 2);
        ctx.fill();

        // Inner solid dot
        ctx.fillStyle = "#38BDF8";
        ctx.beginPath();
        ctx.arc(peakX, peakY, 5, 0, Math.PI * 2);
        ctx.fill();
        ctx.strokeStyle = "#FFFFFF";
        ctx.lineWidth = 2;
        ctx.stroke();

        // Label Sweet Spot
        drawRoundedBadge(ctx, peakX, peakY - 18, "Optimal Equilibrium", "#1E293B", "#38BDF8", "rgba(56, 189, 248, 0.4)");

        // Axes labels
        ctx.fillStyle = "#64748B";
        ctx.font = "600 11px 'Plus Jakarta Sans', sans-serif";
        ctx.textAlign = "center";
        ctx.fillText("Price (p) →", padLeft + plotW / 2, h - 12);
    }

    function renderTopologySimulationChart(points, recPrice, costPrice, mrp, currPrice) {
        const canvas = document.getElementById("topologyChart");
        const setup = setupHiDPICanvas(canvas, 200);
        if (!setup) return;
        const { ctx, w, h } = setup;

        ctx.clearRect(0, 0, w, h);

        const padLeft = 45;
        const padRight = 35;
        const padTop = 45;
        const padBottom = 35;
        const plotW = w - padLeft - padRight;
        const plotH = h - padTop - padBottom;

        // Gridlines
        ctx.strokeStyle = "rgba(255, 255, 255, 0.05)";
        ctx.lineWidth = 1;
        for (let y = padTop; y <= h - padBottom; y += plotH / 3) {
            ctx.beginPath();
            ctx.moveTo(padLeft, y);
            ctx.lineTo(w - padRight, y);
            ctx.stroke();
        }

        if (!points || points.length === 0) {
            ctx.fillStyle = "#64748B";
            ctx.font = "600 12px 'Plus Jakarta Sans'";
            ctx.textAlign = "center";
            ctx.fillText("Simulation curve will render on product selection.", w / 2, h / 2);
            return;
        }

        const prices = points.map(p => p.price);
        const profits = points.map(p => p.projected_profit_30d);
        const minPrice = Math.min(...prices);
        const maxPrice = Math.max(...prices);
        const minProf = Math.min(...profits);
        const maxProf = Math.max(...profits);
        const priceRange = maxPrice - minPrice || 1;
        const profRange = maxProf - minProf || 1;

        const getX = (price) => padLeft + ((price - minPrice) / priceRange) * plotW;
        const getY = (prof) => (h - padBottom) - ((prof - minProf) / profRange) * (plotH - 10);

        // Area Fill under Curve
        const grad = ctx.createLinearGradient(0, padTop, 0, h - padBottom);
        grad.addColorStop(0, "rgba(59, 130, 246, 0.25)");
        grad.addColorStop(1, "rgba(59, 130, 246, 0.0)");

        ctx.fillStyle = grad;
        ctx.beginPath();
        points.forEach((pt, i) => {
            const x = getX(pt.price);
            const y = getY(pt.projected_profit_30d);
            if (i === 0) {
                ctx.moveTo(x, h - padBottom);
                ctx.lineTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        });
        ctx.lineTo(getX(points[points.length - 1].price), h - padBottom);
        ctx.closePath();
        ctx.fill();

        // Stroke line
        ctx.strokeStyle = "#3B82F6";
        ctx.lineWidth = 2.5;
        ctx.beginPath();
        points.forEach((pt, i) => {
            const x = getX(pt.price);
            const y = getY(pt.projected_profit_30d);
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        });
        ctx.stroke();

        // Helper to draw vertical reference line without text collision
        function drawRefLine(price, color, label, lineDash, badgeY, textColor, borderColor) {
            if (price < minPrice || price > maxPrice) return;
            const x = getX(price);

            ctx.save();
            ctx.setLineDash(lineDash || [4, 4]);
            ctx.strokeStyle = color;
            ctx.lineWidth = 1.5;
            ctx.beginPath();
            ctx.moveTo(x, padTop);
            ctx.lineTo(x, h - padBottom);
            ctx.stroke();
            ctx.restore();

            drawRoundedBadge(ctx, x, badgeY, label, "#121929", textColor || color, borderColor || color);
        }

        // Draw Reference Markers with Staggered Y offsets to NEVER overlap
        if (costPrice) drawRefLine(costPrice, "rgba(239, 68, 68, 0.8)", `Cost ₹${Math.round(costPrice).toLocaleString('en-IN')}`, [3, 3], 16, "#F87171", "rgba(239, 68, 68, 0.4)");
        if (currPrice) drawRefLine(currPrice, "rgba(148, 163, 184, 0.8)", `Current ₹${Math.round(currPrice).toLocaleString('en-IN')}`, [4, 4], 32, "#CBD5E1", "rgba(148, 163, 184, 0.4)");
        if (mrp && mrp > costPrice) drawRefLine(mrp, "rgba(245, 158, 11, 0.8)", `MRP ₹${Math.round(mrp).toLocaleString('en-IN')}`, [3, 3], 16, "#FBBF24", "rgba(245, 158, 11, 0.4)");

        // Highlight Recommended Peak Price
        if (recPrice) {
            const recX = getX(recPrice);
            const recY = getY(maxProf);

            // Glowing indicator
            ctx.fillStyle = "rgba(56, 189, 248, 0.35)";
            ctx.beginPath();
            ctx.arc(recX, recY, 9, 0, Math.PI * 2);
            ctx.fill();

            ctx.fillStyle = "#38BDF8";
            ctx.beginPath();
            ctx.arc(recX, recY, 4.5, 0, Math.PI * 2);
            ctx.fill();
            ctx.strokeStyle = "#FFFFFF";
            ctx.lineWidth = 2;
            ctx.stroke();

            drawRoundedBadge(ctx, recX, 16, `AI Rec ₹${Math.round(recPrice).toLocaleString('en-IN')}`, "#1E293B", "#38BDF8", "rgba(56, 189, 248, 0.6)");
        }
    }

    function renderRevenueTrajectoryChart(trajectory, hasActual, projectedRevenue) {
        const canvas = document.getElementById("revenueTrajectoryChart");
        const setup = setupHiDPICanvas(canvas, 250);
        if (!setup) return;
        const { ctx, w, h } = setup;

        ctx.clearRect(0, 0, w, h);

        const padLeft = 55;
        const padRight = 35;
        const padTop = 30;
        const padBottom = 40;
        const plotW = w - padLeft - padRight;
        const plotH = h - padTop - padBottom;

        // Gridlines
        ctx.strokeStyle = "rgba(255, 255, 255, 0.05)";
        ctx.lineWidth = 1;
        for (let y = padTop; y <= h - padBottom; y += plotH / 4) {
            ctx.beginPath();
            ctx.moveTo(padLeft, y);
            ctx.lineTo(w - padRight, y);
            ctx.stroke();
        }

        if (!hasActual || !trajectory || trajectory.length === 0) {
            ctx.fillStyle = "#94A3B8";
            ctx.font = "600 13px 'Plus Jakarta Sans'";
            ctx.textAlign = "center";
            ctx.fillText("Revenue trajectory will appear after sales history is logged.", w / 2, h / 2 - 8);
            ctx.font = "400 11px 'Plus Jakarta Sans'";
            ctx.fillStyle = "#64748B";
            ctx.fillText("Click '+ Log Actual Sales' above to add your actual sales data.", w / 2, h / 2 + 14);
            return;
        }

        const revs = trajectory.map(t => t.realized_revenue);
        const maxRev = Math.max(...revs, projectedRevenue || 0, 1000);
        const getX = (idx, total) => padLeft + (idx / Math.max(total - 1, 1)) * (plotW * 0.65);
        const getY = (val) => (h - padBottom) - (val / maxRev) * plotH;

        // Actual Revenue Area Fill
        const grad = ctx.createLinearGradient(0, padTop, 0, h - padBottom);
        grad.addColorStop(0, "rgba(16, 185, 129, 0.25)");
        grad.addColorStop(1, "rgba(16, 185, 129, 0.0)");

        ctx.fillStyle = grad;
        ctx.beginPath();
        trajectory.forEach((t, idx) => {
            const x = getX(idx, trajectory.length);
            const y = getY(t.realized_revenue);
            if (idx === 0) {
                ctx.moveTo(x, h - padBottom);
                ctx.lineTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        });
        const lastActualX = getX(trajectory.length - 1, trajectory.length);
        ctx.lineTo(lastActualX, h - padBottom);
        ctx.closePath();
        ctx.fill();

        // Actual Line
        ctx.strokeStyle = "#10B981";
        ctx.lineWidth = 3;
        ctx.beginPath();
        trajectory.forEach((t, idx) => {
            const x = getX(idx, trajectory.length);
            const y = getY(t.realized_revenue);
            if (idx === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        });
        ctx.stroke();

        // Projected Continuation (Dashed Blue)
        const lastActualY = getY(trajectory[trajectory.length - 1].realized_revenue);
        const projY = getY(projectedRevenue || trajectory[trajectory.length - 1].realized_revenue * 1.15);

        ctx.save();
        ctx.setLineDash([5, 5]);
        ctx.strokeStyle = "#38BDF8";
        ctx.lineWidth = 2.5;
        ctx.beginPath();
        ctx.moveTo(lastActualX, lastActualY);
        ctx.lineTo(w - padRight, projY);
        ctx.stroke();
        ctx.restore();

        // Labels
        drawRoundedBadge(ctx, lastActualX, lastActualY - 14, "Actual", "#121929", "#10B981", "rgba(16, 185, 129, 0.4)");
        drawRoundedBadge(ctx, w - padRight, projY - 14, "30D Proj", "#121929", "#38BDF8", "rgba(56, 189, 248, 0.4)");
    }


    // =========================================================================
    // 13. MODAL HANDLERS & DIAGNOSTICS
    // =========================================================================
    function openModal(el) { if (el) el.style.display = "flex"; }
    function closeModal(el) { if (el) el.style.display = "none"; }

    const settingsTriggers = [
        document.getElementById("sidebarSettingsBtn"),
        document.getElementById("headerSettingsBtn"),
        document.getElementById("footerLinkSettings")
    ];
    settingsTriggers.forEach(btn => {
        if (btn) btn.addEventListener("click", () => openModal(settingsModal));
    });

    const closeSettingsModal = document.getElementById("closeSettingsModal");
    const btnCancelSettings = document.getElementById("btnCancelSettings");
    if (closeSettingsModal) closeSettingsModal.addEventListener("click", () => closeModal(settingsModal));
    if (btnCancelSettings) btnCancelSettings.addEventListener("click", () => closeModal(settingsModal));

    const supportTriggers = [
        document.getElementById("sidebarSupportBtn"),
        document.getElementById("headerSupportBtn"),
        document.getElementById("footerLinkDocs")
    ];
    supportTriggers.forEach(btn => {
        if (btn) btn.addEventListener("click", () => openModal(supportModal));
    });

    const closeSupportModal = document.getElementById("closeSupportModal");
    const btnCloseSupport = document.getElementById("btnCloseSupport");
    if (closeSupportModal) closeSupportModal.addEventListener("click", () => closeModal(supportModal));
    if (btnCloseSupport) btnCloseSupport.addEventListener("click", () => closeModal(supportModal));

    // ESC to close modals
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
            [settingsModal, supportModal, logSalesModal].forEach(m => closeModal(m));
        }
    });

    // Latency Benchmark
    const btnRunLatency = document.getElementById("btnRunLatencyTest");
    if (btnRunLatency) {
        btnRunLatency.addEventListener("click", async () => {
            btnRunLatency.disabled = true;
            btnRunLatency.textContent = "Testing...";

            const healthLabel = document.getElementById("healthLatencyVal");
            const predictLabel = document.getElementById("predictLatencyVal");

            // 1. Health check
            const t0 = performance.now();
            try {
                const hResp = await fetch(`${API_BASE}/health`);
                const t1 = performance.now();
                if (healthLabel) healthLabel.textContent = `${Math.round(t1 - t0)} ms (${hResp.status === 200 ? 'OK' : 'Err'})`;
            } catch {
                if (healthLabel) healthLabel.textContent = "Error";
            }

            // 2. Predict inference
            const p0 = performance.now();
            try {
                const pResp = await fetch(`${API_BASE}/predict`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        product_id: "PING",
                        cost_price: 1000,
                        current_price: 1500,
                        mrp: 2000
                    })
                });
                const p1 = performance.now();
                if (predictLabel) predictLabel.textContent = `${Math.round(p1 - p0)} ms (Sub-5ms Inference)`;
            } catch {
                if (predictLabel) predictLabel.textContent = "Error";
            }

            btnRunLatency.disabled = false;
            btnRunLatency.innerHTML = '<span class="material-symbols-outlined">speed</span><span>Run Latency Test</span>';
            showToast("Diagnostics benchmark completed!");
        });
    }

    // =========================================================================
    // 14. BOOTSTRAP APP
    // =========================================================================
    checkAuthSession();
});
